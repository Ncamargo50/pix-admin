"""
Detector de lotes basado en imagenes de ALTA RESOLUCION (Esri/Google ~1m).

Pipeline:
  1. Descarga tiles Esri World Imagery del bbox a zoom 17 (~1m/pixel)
  2. Corre Delineate Anything sobre la imagen high-res
  3. Vectoriza, suaviza, simplifica, separa instancias

A 1m de resolucion DA ve los limites visibles (lineas de arboles, caminos)
que a 10m de Sentinel-2 son sub-pixel.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes as rio_shapes
import geopandas as gpd
from shapely import make_valid
from shapely.geometry import shape as shp_shape, mapping
from shapely.ops import unary_union

from highres_tiles import download_highres_bbox, crop_to_exact_bbox
from inference import run_inference

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "output" / "highres_cache"


def _utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    south = lat_mid < 0
    return f"EPSG:{32700 + zone if south else 32600 + zone}"


def _chaikin_smooth(poly, iterations=2):
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
        holes = [list(h.coords) for h in p.interiors]
        for _ in range(iterations):
            ext = _smooth_ring(ext)
            holes = [_smooth_ring(h) for h in holes]
        return Pgon(ext, holes)
    if isinstance(poly, MPgon):
        return MPgon([_one(g) for g in poly.geoms])
    return _one(poly)


def detect_lots_highres(bbox, zoom=17, source="esri",
                        conf=0.05, min_area_ha=1.0,
                        smooth_iters=2, simplify_m=5.0,
                        model_size="small") -> dict:
    """
    Args:
        bbox: [W,S,E,N] WGS84
        zoom: 17 (~1m), 18 (~0.5m), 19 (~0.3m). Mas zoom = mas tiles.
        source: 'esri' (no auth) o 'google'
        conf: confianza minima Delineate Anything
        min_area_ha: filtro area minima
    """
    import time
    t_total = time.time()
    timings = {}

    # 1) Descargar mosaic high-res
    t0 = time.time()
    rgb, transform, crs = download_highres_bbox(
        bbox, zoom=zoom, source=source, cache_dir=CACHE_DIR)
    rgb, transform = crop_to_exact_bbox(rgb, transform, bbox)
    timings["download_tiles"] = round(time.time() - t0, 2)
    timings["image_shape"] = list(rgb.shape)
    timings["m_per_pixel"] = round(abs(transform.a) * 111000, 3)

    # 2) Inferencia Delineate Anything sobre la high-res
    t0 = time.time()
    polys = run_inference(rgb, transform, crs, size=model_size,
                           conf=conf, iou_thr=0.4, min_area_ha=min_area_ha)
    timings["delineate_anything"] = round(time.time() - t0, 2)

    if not polys:
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"timings": timings, "n_polygons": 0,
                             "imagery": {"source": source, "zoom": zoom,
                                         "shape": list(rgb.shape)}}}

    # 3) Refinar bordes en metric crs
    t0 = time.time()
    gdf = gpd.GeoDataFrame(
        geometry=[p["geometry"] for p in polys], crs="EPSG:4326")
    metric = _utm_for_bounds(gdf.total_bounds)
    gdf_m = gdf.to_crs(metric)

    refined = []
    for g in gdf_m.geometry:
        if g.is_empty: continue
        sm = _chaikin_smooth(make_valid(g).buffer(0), iterations=smooth_iters)
        sm = sm.simplify(simplify_m, preserve_topology=True)
        sm = make_valid(sm).buffer(0)
        if sm.is_empty: continue
        if hasattr(sm, "geoms"):
            for sub in sm.geoms:
                if not sub.is_empty: refined.append(sub)
        else:
            refined.append(sm)

    out = gpd.GeoDataFrame(geometry=refined, crs=metric)
    out["area_ha"] = out.area / 10_000
    out = out[out["area_ha"] >= min_area_ha].reset_index(drop=True)
    out_wgs = out.to_crs("EPSG:4326")
    timings["refine"] = round(time.time() - t0, 2)
    timings["total"] = round(time.time() - t_total, 2)

    feats = [{
        "type": "Feature",
        "properties": {
            "id": i, "area_ha": round(float(row.area_ha), 3),
            "model": "highres_da", "zoom": zoom, "source": source,
        },
        "geometry": mapping(row.geometry),
    } for i, row in out_wgs.iterrows()]

    return {
        "type": "FeatureCollection",
        "features": feats,
        "metadata": {
            "n_polygons": len(feats),
            "total_area_ha": round(float(out["area_ha"].sum()), 2),
            "imagery": {
                "source": source, "zoom": zoom,
                "shape": list(rgb.shape),
                "m_per_pixel": timings["m_per_pixel"],
            },
            "timings": timings,
            "bbox": bbox,
        },
    }
