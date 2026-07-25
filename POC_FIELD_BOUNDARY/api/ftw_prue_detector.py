"""
Detector de lotes con FTW PRUE (Fields of The World, Microsoft + Taylor Geospatial).

Modelo: U-Net + EfficientNet-B5 entrenado con 70K samples truth de boundaries
en 24 paises. IoU pixel-level reportado: 0.77.

Pipeline:
  1. Sentinel-2 windows A y B (early + late season para captar variabilidad estacional)
  2. Stack 8 channels: [B4,B3,B2,B8] x 2 windows
  3. Tile-based inference (256x256 patches con overlap)
  4. Output: 3 clases - background / field interior / field boundary
  5. Watershed segmentation usando boundaries como divisores
  6. Vectorizar cada instance separada
  7. Smooth + simplify

Dependencias:
  - segmentation_models_pytorch >= 0.5
  - torch
  - rasterio, geopandas, shapely
  - scipy, scikit-image (para watershed)
"""
from __future__ import annotations

import time
import urllib.request
import warnings
from functools import lru_cache
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import rasterio
from rasterio.features import shapes as rio_shapes
import geopandas as gpd
from shapely.geometry import shape as shp_shape, Polygon, mapping
from shapely import make_valid

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "output" / "ftw_models" / "prue_efnet5_checkpoint.ckpt"
CACHE_DIR = ROOT / "output" / "s2_cache" / "ftw"


@lru_cache(maxsize=1)
def _load_prue_model():
    """Singleton FTW PRUE U-Net + EfficientNet-B5."""
    import torch
    import segmentation_models_pytorch as smp
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"PRUE checkpoint missing: {MODEL_PATH}")
    print(">>> Cargando FTW PRUE EfficientNet-B5 (~120 MB)...")
    model = smp.Unet(encoder_name="efficientnet-b5",
                      in_channels=8, classes=3,
                      encoder_weights=None)
    ckpt = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    sd = {k.removeprefix("model."): v for k, v in ckpt["state_dict"].items()
          if k.startswith("model.")}
    model.load_state_dict(sd, strict=True)
    model.eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    print(f"    PRUE listo en {device}")
    return model, device


def _initialize_ee():
    import ee
    try:
        ee.Number(1).getInfo()
    except Exception:
        ee.Initialize()


def _fetch_s2_window_bgrn(bbox, start, end, scale=10, cloud_pct=30, cache_dir=None):
    """Baja Sentinel-2 RGB+NIR (B2, B3, B4, B8) compuesto mediano del periodo.
    Returns: (HxWx4 uint16, transform, crs, n_scenes)."""
    import ee
    _initialize_ee()
    aoi = ee.Geometry.Rectangle(list(bbox))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct)))
    n = coll.size().getInfo()
    if n == 0:
        raise RuntimeError(f"Sin escenas S2 para {bbox} {start}-{end}")

    def mask_clear(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        # FTW espera valores raw (0-65535) no normalizados
        return img.updateMask(clear).copyProperties(img, ["system:time_start"])

    composite = coll.map(mask_clear).median().clip(aoi)
    bands = composite.select(["B2", "B3", "B4", "B8"]).toUint16()

    url = bands.getDownloadURL({"region": aoi, "scale": scale, "crs": "EPSG:4326",
                                "format": "GEO_TIFF"})

    cache_dir = Path(cache_dir or CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    fn = (f"s2bgrn_{bbox[0]:.4f}_{bbox[1]:.4f}_{bbox[2]:.4f}_{bbox[3]:.4f}_"
          f"{start}_{end}_{scale}m.tif")
    out = cache_dir / fn
    if not out.exists():
        urllib.request.urlretrieve(url, out)
    with rasterio.open(out) as src:
        arr = src.read([1, 2, 3, 4]).transpose(1, 2, 0)  # HxWx4
        return arr, src.transform, str(src.crs), n


def _utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    return f"EPSG:{32700 + zone if lat_mid < 0 else 32600 + zone}"


def _normalize_for_prue(stack_8ch):
    """FTW oficial divide por 3000 (img.astype(float) / 3000).
    No clip - el modelo aprendio con valores raw escalados."""
    return stack_8ch.astype(np.float32) / 3000.0


def _tile_inference(model, device, stack_8ch, tile_size=256, overlap=64):
    """Inference por tiles con overlap, blending con fade en bordes."""
    import torch
    H, W, C = stack_8ch.shape
    stride = tile_size - overlap
    out_logits = np.zeros((3, H, W), dtype=np.float32)
    weights = np.zeros((H, W), dtype=np.float32)

    # Mascara de blending fade en bordes para evitar costuras
    fade = np.ones((tile_size, tile_size), dtype=np.float32)
    if overlap > 0:
        ramp = np.linspace(0, 1, overlap // 2 + 1)[1:]
        fade[:len(ramp), :] *= ramp[:, None]
        fade[-len(ramp):, :] *= ramp[::-1, None]
        fade[:, :len(ramp)] *= ramp[None, :]
        fade[:, -len(ramp):] *= ramp[None, ::-1]

    rows = list(range(0, max(1, H - tile_size + 1), stride))
    cols = list(range(0, max(1, W - tile_size + 1), stride))
    if rows[-1] + tile_size < H: rows.append(H - tile_size)
    if cols[-1] + tile_size < W: cols.append(W - tile_size)

    with torch.no_grad():
        for r in rows:
            for c in cols:
                r1 = min(r + tile_size, H); c1 = min(c + tile_size, W)
                r0 = max(0, r1 - tile_size); c0 = max(0, c1 - tile_size)
                tile = stack_8ch[r0:r1, c0:c1, :]
                # Pad si tile menor que tile_size
                pad_h = tile_size - tile.shape[0]
                pad_w = tile_size - tile.shape[1]
                if pad_h > 0 or pad_w > 0:
                    tile = np.pad(tile, ((0, pad_h), (0, pad_w), (0, 0)))
                x = torch.from_numpy(tile.transpose(2, 0, 1)).unsqueeze(0).to(device)
                logits = model(x).cpu().numpy()[0]  # (3, H, W)
                # Recortar pad
                logits = logits[:, :tile_size - pad_h, :tile_size - pad_w]
                fade_tile = fade[:tile_size - pad_h, :tile_size - pad_w]
                out_logits[:, r0:r1, c0:c1] += logits * fade_tile
                weights[r0:r1, c0:c1] += fade_tile

    weights[weights == 0] = 1
    return out_logits / weights


def _watershed_segment(extent_prob, boundary_prob,
                        extent_thresh=0.30, boundary_thresh=0.50,
                        marker_min_distance_px=15,
                        **kwargs):
    """
    Watershed v3 con DISTANCE TRANSFORM markers:
      - mask del lote = extent FULL (no recortado por boundary) -> lotes COMPLETOS
      - markers = picos locales del distance transform al boundary (1 marker por lote)
      - elevation = boundary_prob (los bordes son altos -> watershed se detiene ahi)

    Resultado: cada lote ocupa TODO el extent disponible hasta llegar a una boundary fuerte.
    """
    from scipy import ndimage as ndi
    from skimage.segmentation import watershed
    from skimage.feature import peak_local_max

    # 1) Field mask: TODO lo que el modelo cree que es campo
    field = extent_prob > extent_thresh
    # Cleanup + fill (lote es solido, sin holes)
    field = ndi.binary_closing(field, iterations=2)
    field = ndi.binary_fill_holes(field)

    # 2) Boundary mask para markers (no para mask del lote)
    boundary = boundary_prob > boundary_thresh

    # 3) Markers seeds = zonas extent-MEDIO Y boundary-bajo
    #    Threshold extent ajustado al threshold pasado, no fijo 0.55
    seed_extent_thr = max(extent_thresh + 0.10, 0.40)
    seed = (extent_prob > seed_extent_thr) & (boundary_prob < boundary_thresh * 0.7)
    seed = ndi.binary_erosion(seed, iterations=1)
    markers, n_markers = ndi.label(seed)
    if n_markers > 0:
        sizes = ndi.sum(seed, markers, range(1, n_markers + 1))
        for i in np.where(sizes < 4)[0]:
            markers[markers == i + 1] = 0

    n_markers = int(markers.max())
    if n_markers == 0:
        # Fallback: usar extent directo sin restar boundary
        seed = (extent_prob > seed_extent_thr)
        seed = ndi.binary_erosion(seed, iterations=1)
        markers, n_markers = ndi.label(seed)
        if int(markers.max()) == 0:
            return np.zeros_like(field, dtype=np.int32)

    # 4) Watershed con elevation = -extent + 2*boundary (bordes son alturas)
    #    Cada marker se expande hasta encontrar pixel con boundary alta o termina mask
    elevation = (boundary_prob - extent_prob * 0.5).astype(np.float32)
    labels = watershed(elevation, markers=markers, mask=field, watershed_line=False)
    return labels


def _tile_inference_tta(model, device, stack_8ch, tile_size=256, overlap=64):
    """Test-Time Augmentation: promediar predicciones sobre 4 rotaciones (0, 90, 180, 270)."""
    import torch
    accum = None
    for k in range(4):
        rotated = np.rot90(stack_8ch, k=k, axes=(0, 1)).copy()
        logits = _tile_inference(model, device, rotated,
                                   tile_size=tile_size, overlap=overlap)
        # Rotar de vuelta para alinear
        unrot = np.rot90(logits, k=-k, axes=(1, 2))
        accum = unrot if accum is None else (accum + unrot)
    return accum / 4.0


def detect_lots_with_ftw(bbox, year=2025,
                          win_a_start="2025-01-01", win_a_end="2025-03-31",
                          win_b_start="2025-07-01", win_b_end="2025-09-30",
                          scale_m=10, cloud_pct=30,
                          extent_thresh=0.3, boundary_thresh=0.4,
                          marker_min_area_px=50, marker_erode_iters=1,
                          min_area_ha=0.5, max_area_ha=500.0,
                          simplify_m=3.0, smooth_iters=2,
                          tile_size=256, overlap=64,
                          use_tta=False) -> dict:
    """Pipeline completo FTW PRUE."""
    import torch

    timings = {}

    # 1) Bajar 2 windows S2
    t0 = time.time()
    win_a, transform_a, crs_a, n_a = _fetch_s2_window_bgrn(
        bbox, win_a_start, win_a_end, scale=scale_m, cloud_pct=cloud_pct)
    win_b, transform_b, crs_b, n_b = _fetch_s2_window_bgrn(
        bbox, win_b_start, win_b_end, scale=scale_m, cloud_pct=cloud_pct)
    timings["s2_download"] = round(time.time() - t0, 2)

    # 2) Validar shapes y stack 8 channels
    if win_a.shape[:2] != win_b.shape[:2]:
        # Reescalar B a A si difieren
        import cv2 as _cv2
        win_b = _cv2.resize(win_b, (win_a.shape[1], win_a.shape[0]),
                              interpolation=_cv2.INTER_LINEAR).astype(np.uint16)
    transform = transform_a; crs = crs_a
    H, W = win_a.shape[:2]
    # FTW PRUE espera orden RGBN por window: B4 (Red), B3 (Green), B2 (Blue), B8 (NIR).
    # Mi fetch baja como [B2,B3,B4,B8] (BGRN) - reordenar a [B4,B3,B2,B8]
    def _to_rgbn(arr):
        return np.stack([arr[:, :, 2], arr[:, :, 1], arr[:, :, 0], arr[:, :, 3]], axis=-1)
    stack_8ch = np.concatenate([_to_rgbn(win_a), _to_rgbn(win_b)], axis=-1)  # HxWx8 (RGBN+RGBN)

    # 3) Normalizar y tile-inference (con TTA opcional)
    t0 = time.time()
    stack_norm = _normalize_for_prue(stack_8ch)
    model, device = _load_prue_model()
    if use_tta:
        logits = _tile_inference_tta(model, device, stack_norm,
                                       tile_size=tile_size, overlap=overlap)
    else:
        logits = _tile_inference(model, device, stack_norm,
                                  tile_size=tile_size, overlap=overlap)
    probs = torch.softmax(torch.from_numpy(logits), dim=0).numpy()
    timings["inference"] = round(time.time() - t0, 2)
    timings["tta"] = use_tta

    # 4) Extraer extent + boundary maps
    background_prob = probs[0]
    extent_prob = probs[1]      # field interior
    boundary_prob = probs[2]    # field boundary

    # 5) Watershed segmentation
    t0 = time.time()
    labels = _watershed_segment(extent_prob, boundary_prob,
                                  extent_thresh=extent_thresh,
                                  boundary_thresh=boundary_thresh,
                                  marker_min_area_px=marker_min_area_px,
                                  marker_erode_iters=marker_erode_iters)
    n_inst = int(labels.max())
    timings["watershed"] = round(time.time() - t0, 2)
    timings["n_instances_raw"] = n_inst

    if n_inst == 0:
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"timings": timings, "n_polygons": 0,
                             "imagery": {"shape": [H, W], "scale_m": scale_m,
                                          "n_scenes": [n_a, n_b]}}}

    # 6) Vectorizar cada instance (watershed v3 ya garantiza lote COMPLETO)
    t0 = time.time()
    from scipy import ndimage as ndi
    pixel_area_m2 = scale_m * scale_m
    polygons = []
    for inst_id in range(1, n_inst + 1):
        mask = (labels == inst_id)
        if not mask.any(): continue
        # Cleanup post-watershed: cerrar gaps + fill holes
        mask = ndi.binary_closing(mask, iterations=1)
        mask = ndi.binary_fill_holes(mask)

        area_px = int(mask.sum())
        area_ha_approx = area_px * pixel_area_m2 / 10000
        if area_ha_approx < min_area_ha or area_ha_approx > max_area_ha: continue

        # Vectorizar - solo componente mas grande
        cands = []
        for geom_dict, val in rio_shapes(mask.astype(np.uint8), transform=transform):
            if val == 1:
                g = shp_shape(geom_dict)
                if g.is_valid and g.area > 0: cands.append(g)
        if cands:
            polygons.append(max(cands, key=lambda p: p.area))
    timings["vectorize"] = round(time.time() - t0, 2)

    if not polygons:
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"timings": timings, "n_polygons": 0}}

    # 7) Refine: simplify ADAPTATIVO (cap a max_vertices) para edicion manual practica
    t0 = time.time()
    gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")
    metric = _utm_for_bounds(gdf.total_bounds)
    gdf_m = gdf.to_crs(metric)
    refined = []
    target_max_vertices = 30  # < 30 vertices = practico para editar a mano
    for g in gdf_m.geometry:
        g = make_valid(g).buffer(0)
        if g.is_empty: continue
        # Simplify adaptativo: empezar con simplify_m, ir aumentando hasta vertices <= target
        tol = max(simplify_m, 6.0)
        for _ in range(8):
            simp = g.simplify(tol, preserve_topology=True)
            simp = make_valid(simp).buffer(0)
            if hasattr(simp, "geoms"): simp = max(simp.geoms, key=lambda p: p.area)
            if simp.is_empty: break
            n_vert = len(list(simp.exterior.coords))
            if n_vert <= target_max_vertices: g = simp; break
            tol *= 1.4  # subir tolerancia y reintentar
        else:
            g = simp
        # Smooth Chaikin SOLO si pocas vertices (no agregar de mas)
        if smooth_iters > 0 and len(list(g.exterior.coords)) <= 50:
            from shapely.geometry import Polygon as Pgon
            for _ in range(min(smooth_iters, 1)):  # max 1 iter para no doblar vertices
                ext = list(g.exterior.coords)
                if len(ext) < 4: break
                new = []
                for i in range(len(ext) - 1):
                    p, q = ext[i], ext[i+1]
                    new.append((0.75*p[0]+0.25*q[0], 0.75*p[1]+0.25*q[1]))
                    new.append((0.25*p[0]+0.75*q[0], 0.25*p[1]+0.75*q[1]))
                new.append(new[0])
                g = Pgon(new)
            # Re-simplify post-smooth
            g = g.simplify(simplify_m * 0.8, preserve_topology=True)
        g = make_valid(g).buffer(0)
        if g.is_empty: continue
        if hasattr(g, "geoms"): g = max(g.geoms, key=lambda p: p.area)
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
                        "model": "ftw_prue_efnet5"},
        "geometry": mapping(row.geometry),
    } for i, row in out_wgs.iterrows()]

    return {
        "type": "FeatureCollection", "features": feats,
        "metadata": {
            "n_polygons": len(feats),
            "total_area_ha": round(float(out["area_ha"].sum()), 2),
            "imagery": {"shape": [H, W], "scale_m": scale_m,
                         "n_scenes": [n_a, n_b],
                         "win_a": [win_a_start, win_a_end],
                         "win_b": [win_b_start, win_b_end]},
            "timings": timings, "model": "ftw_prue_efnet5_v3", "bbox": bbox,
        },
    }
