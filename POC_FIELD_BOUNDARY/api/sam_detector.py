"""
Detector de lotes usando SAM (Segment Anything Model) de Meta.

SAM es un foundation model de vision que segmenta cualquier objeto visible
en una imagen, sin necesidad de entrenamiento previo. Replica lo que un
humano hace al "ver" lotes en el mapa: identifica regiones cohesivas
delimitadas por bordes visibles.

Pipeline:
  1. Imagen alta resolucion (Esri ~1m) del bbox
  2. SAM AutomaticMaskGenerator -> N mascaras de instancias separadas
  3. Filtrar mascaras: area razonable (1-300 ha tipico), forma compacta
  4. Vectorizar cada mascara -> Polygon
  5. Smooth + simplify -> bordes cadastrables
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import shapes as rio_shapes
from shapely.geometry import shape as shp_shape, Polygon, mapping
from shapely import make_valid

ROOT = Path(__file__).resolve().parent.parent
SAM_MODELS_DIR = ROOT / "output" / "sam_models"
SAM_CHECKPOINTS = {
    "vit_b": SAM_MODELS_DIR / "sam_vit_b_01ec64.pth",
    "vit_l": SAM_MODELS_DIR / "sam_vit_l_0b3195.pth",
    "vit_h": SAM_MODELS_DIR / "sam_vit_h_4b8939.pth",
}

from highres_tiles import download_highres_bbox, crop_to_exact_bbox


def _utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    return f"EPSG:{32700 + zone if lat_mid < 0 else 32600 + zone}"


@lru_cache(maxsize=2)
def _load_sam(model_type="vit_b"):
    """Singleton para SAM (carga solo una vez en memoria)."""
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
    ckpt = SAM_CHECKPOINTS.get(model_type)
    if not ckpt or not ckpt.exists():
        raise FileNotFoundError(f"SAM {model_type} no encontrado en {ckpt}")
    print(f">>> Cargando SAM {model_type} (RAM ~1.5 GB)...")
    import torch
    sam = sam_model_registry[model_type](checkpoint=str(ckpt))
    sam = sam.to("cuda" if torch.cuda.is_available() else "cpu")
    sam.eval()
    print(f"    SAM listo en {sam.device}")
    return sam


def _build_mask_generator(model_type="vit_b",
                           points_per_side=32,
                           pred_iou_thresh=0.88,
                           stability_score_thresh=0.92,
                           min_mask_region_area=2000):
    from segment_anything import SamAutomaticMaskGenerator
    sam = _load_sam(model_type)
    return SamAutomaticMaskGenerator(
        model=sam,
        points_per_side=points_per_side,
        pred_iou_thresh=pred_iou_thresh,
        stability_score_thresh=stability_score_thresh,
        crop_n_layers=0,
        crop_n_points_downscale_factor=1,
        min_mask_region_area=min_mask_region_area,
    )


def _chaikin_smooth_metric(poly, iterations=2):
    from shapely.geometry import Polygon as Pgon, MultiPolygon as MPgon
    def _smooth_ring(coords):
        if len(coords) < 4: return coords
        new = []
        for i in range(len(coords) - 1):
            p, q = coords[i], coords[i + 1]
            new.append((0.75*p[0] + 0.25*q[0], 0.75*p[1] + 0.25*q[1]))
            new.append((0.25*p[0] + 0.75*q[0], 0.25*p[1] + 0.75*q[1]))
        new.append(new[0])
        return new
    def _one(p):
        ext = list(p.exterior.coords)
        for _ in range(iterations): ext = _smooth_ring(ext)
        return Pgon(ext)
    if isinstance(poly, MPgon):
        return MPgon([_one(g) for g in poly.geoms])
    return _one(poly)


def _detect_line_borders(rgb_inf, min_line_length_px=50):
    """
    Detecta lineas oscuras delgadas (arboles en fila, caminos) — RAPIDO.

    Usa morphological tophat con kernels rectangulares orientados:
      - Kernel HORIZONTAL: detecta lineas verticales
      - Kernel VERTICAL: detecta lineas horizontales
      - Si un pixel oscuro NO desaparece con un kernel grande, es una linea fina.

    Filtro final por area: descarta CC < min_line_length_px.
    """
    gray = cv2.cvtColor(rgb_inf, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # Black-hat con kernels lineales: resalta lineas finas oscuras
    k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))  # captura horizontales
    k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))  # captura verticales
    bh_h = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, k_h)
    bh_v = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, k_v)
    bh = cv2.max(bh_h, bh_v)
    _, line_mask = cv2.threshold(bh, 12, 255, cv2.THRESH_BINARY)

    # Filtro por area: descartar manchas chicas (ruido)
    n_cc, labels, stats, _ = cv2.connectedComponentsWithStats(line_mask)
    keep = np.zeros_like(line_mask, dtype=np.uint8)
    for i in range(1, n_cc):
        if stats[i, cv2.CC_STAT_AREA] >= min_line_length_px:
            keep[labels == i] = 255

    # Engrosar 2 px para que sean cortes efectivos
    keep = cv2.dilate(keep, np.ones((3, 3), np.uint8), iterations=2)
    return keep > 0


def detect_lots_with_sam(bbox, zoom=17, source="esri",
                         model_type="vit_b",
                         min_area_ha=1.0, max_area_ha=500.0,
                         points_per_side=32,
                         pred_iou_thresh=0.86,
                         stability_score_thresh=0.90,
                         simplify_m=4.0, smooth_iters=1,
                         max_image_dim=2048,
                         subtract_borders=True,
                         border_min_split_area_ha=2.0) -> dict:
    """
    Detecta lotes con SAM sobre imagen alta resolucion.

    Args:
        bbox: [W, S, E, N] WGS84
        zoom: 17 (~1.2m), 18 (~0.6m)
        max_image_dim: SAM tarda mucho >2048 en CPU. Si la imagen es mas grande,
                        se downscalea para inferencia y luego se reproyecta.
    """
    import time
    timings = {}

    # 1) Descargar mosaic high-res
    t0 = time.time()
    rgb, transform, crs = download_highres_bbox(bbox, zoom=zoom, source=source,
                                                  cache_dir=ROOT/"output"/"highres_cache")
    rgb, transform = crop_to_exact_bbox(rgb, transform, bbox)
    H_orig, W_orig = rgb.shape[:2]
    px_size_m = abs(transform.a) * 111000
    timings["download"] = round(time.time() - t0, 2)
    timings["image_shape_orig"] = [H_orig, W_orig]

    # 2) Si imagen muy grande, downscalear para inferencia SAM
    if max(H_orig, W_orig) > max_image_dim:
        scale = max_image_dim / max(H_orig, W_orig)
        new_w = int(W_orig * scale); new_h = int(H_orig * scale)
        rgb_inf = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
        scale_inv = max(H_orig, W_orig) / max(new_h, new_w)  # px coords back to original
    else:
        rgb_inf = rgb
        scale_inv = 1.0
    H_inf, W_inf = rgb_inf.shape[:2]
    timings["image_shape_inf"] = [H_inf, W_inf]

    # 3) SAM AutomaticMaskGenerator
    t0 = time.time()
    mask_gen = _build_mask_generator(
        model_type=model_type,
        points_per_side=points_per_side,
        pred_iou_thresh=pred_iou_thresh,
        stability_score_thresh=stability_score_thresh,
        min_mask_region_area=int(min_area_ha * 10000 / (px_size_m * scale_inv) ** 2 / 4),
    )
    masks = mask_gen.generate(rgb_inf)
    timings["sam_inference"] = round(time.time() - t0, 2)
    timings["sam_masks_raw"] = len(masks)

    # 4a) Detectar SOLO lineas largas (no sombras ni blobs) para split posterior
    border_mask_full = None
    if subtract_borders:
        t0 = time.time()
        border_mask_full = _detect_line_borders(rgb, min_line_length_px=30)
        timings["border_detect"] = round(time.time() - t0, 2)
        timings["border_pixels"] = int(border_mask_full.sum())

    # 4b) Filtrar, vectorizar y SUBDIVIDIR mascaras SAM con bordes
    t0 = time.time()
    pixel_area_orig_m2 = px_size_m ** 2
    polygons = []
    n_split_total = 0
    for m in masks:
        seg = m["segmentation"]  # bool HxW (en escala de inferencia)
        # Resize mask a tamano original
        if scale_inv != 1.0:
            seg_full = cv2.resize(seg.astype(np.uint8), (W_orig, H_orig),
                                   interpolation=cv2.INTER_NEAREST).astype(bool)
        else:
            seg_full = seg

        # Calcular area precisa post-resize
        area_orig_px = int(seg_full.sum())
        area_ha = area_orig_px * pixel_area_orig_m2 / 10000
        if area_ha < min_area_ha or area_ha > max_area_ha:
            continue

        # *** NUEVO V2: cortar mascara SAM con LINEAS de bordes (no sombras) y rellenar huecos ***
        if subtract_borders and border_mask_full is not None:
            from scipy.ndimage import binary_fill_holes
            # Cortar mascara solo donde hay LINEAS reales
            seg_cut = seg_full & ~border_mask_full
            # Connected components del corte: cada CC es un lote separado
            n_cc, labels = cv2.connectedComponents(seg_cut.astype(np.uint8))
            sub_components = []
            for cc_id in range(1, n_cc):
                cc_mask = (labels == cc_id)
                cc_area_ha = cc_mask.sum() * pixel_area_orig_m2 / 10000
                if cc_area_ha < border_min_split_area_ha: continue
                # CRITICO: rellenar huecos internos para que el lote sea solido
                cc_filled = binary_fill_holes(cc_mask)
                # Dilatar 1 px para recuperar bordes perdidos por la linea de corte
                cc_solid = cv2.dilate(cc_filled.astype(np.uint8),
                                        np.ones((3,3), np.uint8), iterations=2).astype(bool)
                # Clip a SAM original sin restar bordes (queremos cubrir el lote completo
                # excepto las lineas que separan de OTROS lotes)
                cc_solid = cc_solid & seg_full
                # Otra fill final por si la dilatacion creo gaps
                cc_solid = binary_fill_holes(cc_solid)
                sub_components.append((cc_solid.astype(bool), cc_area_ha))
            if len(sub_components) > 1:
                n_split_total += len(sub_components) - 1
            # Vectorizar cada sub-componente
            for cc_mask, cc_area_ha in sub_components:
                cands = []
                for geom_dict, val in rio_shapes(cc_mask.astype(np.uint8), transform=transform):
                    if val == 1:
                        g = shp_shape(geom_dict)
                        if g.is_valid and g.area > 0:
                            cands.append(g)
                if cands:
                    biggest = max(cands, key=lambda p: p.area)
                    polygons.append(biggest)
            continue  # ya procesada esta mascara

        # Vectorizar (modo sin border subtraction)
        cands = []
        for geom_dict, val in rio_shapes(seg_full.astype(np.uint8), transform=transform):
            if val == 1:
                g = shp_shape(geom_dict)
                if g.is_valid and g.area > 0:
                    cands.append(g)
        if not cands: continue
        biggest = max(cands, key=lambda p: p.area)
        polygons.append(biggest)
    timings["vectorize"] = round(time.time() - t0, 2)
    timings["sam_masks_split_into"] = n_split_total + len(masks)

    if not polygons:
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"timings": timings, "n_polygons": 0,
                             "imagery": {"source": source, "zoom": zoom,
                                          "shape": [H_orig, W_orig],
                                          "m_per_pixel": round(px_size_m, 3)}}}

    # 5) Deduplicate (SAM genera mascaras superpuestas): si dos poligonos solapan >85%
    #    del mas chico, quedarse solo con el mas grande
    t0 = time.time()
    if len(polygons) > 1:
        # Ordenar de mas grande a mas chico
        polygons.sort(key=lambda p: -p.area)
        keep = []
        for cand in polygons:
            is_dup = False
            for accepted in keep:
                try:
                    inter = cand.intersection(accepted).area
                    smaller = min(cand.area, accepted.area)
                    if smaller > 0 and inter / smaller > 0.85:
                        is_dup = True; break
                except Exception:
                    continue
            if not is_dup:
                keep.append(cand)
        polygons = keep
    gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")
    metric = _utm_for_bounds(gdf.total_bounds)
    gdf_m = gdf.to_crs(metric)
    refined = []
    for g in gdf_m.geometry:
        g = make_valid(g).buffer(0)
        if hasattr(g, "geoms"):
            g = max(g.geoms, key=lambda p: p.area)
        if g.is_empty: continue
        if smooth_iters > 0:
            g = _chaikin_smooth_metric(g, iterations=smooth_iters)
        if simplify_m > 0:
            g = g.simplify(simplify_m, preserve_topology=True)
        g = make_valid(g).buffer(0)
        if hasattr(g, "geoms"):
            g = max(g.geoms, key=lambda p: p.area)
        if g.is_empty: continue
        refined.append(g)

    out = gpd.GeoDataFrame(geometry=refined, crs=metric)
    out["area_ha"] = out.area / 10_000
    out = out[(out["area_ha"] >= min_area_ha) & (out["area_ha"] <= max_area_ha)]
    out = out.sort_values("area_ha", ascending=False).reset_index(drop=True)
    out_wgs = out.to_crs("EPSG:4326")
    timings["refine"] = round(time.time() - t0, 2)
    timings["total"] = round(sum(v for v in timings.values() if isinstance(v, (int, float))), 2)

    feats = [{
        "type": "Feature",
        "properties": {"id": int(i), "area_ha": round(float(row.area_ha), 3),
                        "model": "sam_" + model_type, "zoom": zoom, "source": source},
        "geometry": mapping(row.geometry),
    } for i, row in out_wgs.iterrows()]

    return {
        "type": "FeatureCollection", "features": feats,
        "metadata": {
            "n_polygons": len(feats),
            "total_area_ha": round(float(out["area_ha"].sum()), 2),
            "imagery": {"source": source, "zoom": zoom,
                         "shape": [H_orig, W_orig],
                         "m_per_pixel": round(px_size_m, 3)},
            "timings": timings, "bbox": bbox, "model": f"sam_{model_type}",
        },
    }
