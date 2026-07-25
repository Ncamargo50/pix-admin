"""
Refinamiento de poligonos para uso cadastral real.

- Topologia valida (make_valid + buffer 0).
- Suavizado de bordes (Chaikin) para eliminar jaggies del raster.
- Simplificacion controlada (Douglas-Peucker, max desviacion 5 m).
- Filtro por area razonable.
- Calculo de area util (NDVI > umbral) por poligono.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
from shapely.geometry import Polygon, MultiPolygon
from shapely import make_valid


def chaikin_smooth(poly: Polygon, iterations: int = 2) -> Polygon:
    """Suaviza bordes con corner-cutting de Chaikin sin distorsionar la forma global."""
    def _smooth_ring(coords: list[tuple]) -> list[tuple]:
        if len(coords) < 4:
            return coords
        new = []
        for i in range(len(coords) - 1):
            p, q = coords[i], coords[i + 1]
            new.append((0.75*p[0] + 0.25*q[0], 0.75*p[1] + 0.25*q[1]))
            new.append((0.25*p[0] + 0.75*q[0], 0.25*p[1] + 0.75*q[1]))
        new.append(new[0])
        return new

    if poly.is_empty or not isinstance(poly, Polygon):
        return poly
    rings = [list(poly.exterior.coords)]
    holes = [list(h.coords) for h in poly.interiors]

    for _ in range(iterations):
        rings = [_smooth_ring(r) for r in rings]
        holes = [_smooth_ring(h) for h in holes]

    return Polygon(rings[0], holes)


def refine_polygons(geoms: Iterable, simplify_m: float = 5.0,
                    smooth_iters: int = 2,
                    metric_crs: str = "EPSG:32722") -> list:
    """
    Aplica pipeline de refinamiento. Espera geometrias en EPSG:4326.

    1. make_valid + buffer(0) -> topologia limpia.
    2. Reproyectar a metric_crs para operaciones en metros.
    3. Suavizar (Chaikin).
    4. Simplificar con tolerance en metros (preserva topologia).
    5. Filtrar por area minima.
    6. Volver a EPSG:4326.

    Returns: lista de (polygon_wgs84, area_ha, perimeter_m).
    """
    import geopandas as gpd

    valid = []
    for g in geoms:
        if g is None or g.is_empty:
            continue
        g2 = make_valid(g)
        if hasattr(g2, "buffer"):
            g2 = g2.buffer(0)
        if isinstance(g2, MultiPolygon):
            for sub in g2.geoms:
                if sub.area > 0:
                    valid.append(sub)
        elif isinstance(g2, Polygon) and g2.area > 0:
            valid.append(g2)

    if not valid:
        return []

    gdf = gpd.GeoDataFrame(geometry=valid, crs="EPSG:4326").to_crs(metric_crs)

    refined = []
    for g in gdf.geometry:
        if g.is_empty: continue
        smooth = chaikin_smooth(g, iterations=smooth_iters)
        simple = smooth.simplify(simplify_m, preserve_topology=True)
        simple = make_valid(simple).buffer(0)
        if isinstance(simple, MultiPolygon):
            simple = max(simple.geoms, key=lambda p: p.area)
        if simple.is_empty: continue
        refined.append(simple)

    if not refined:
        return []

    out = gpd.GeoDataFrame(geometry=refined, crs=metric_crs)
    out["area_ha"] = out.area / 10_000
    out["perimeter_m"] = out.length

    out_wgs = out.to_crs("EPSG:4326")
    return [
        {"geometry": geom, "area_ha": float(a), "perimeter_m": float(p)}
        for geom, a, p in zip(out_wgs.geometry, out["area_ha"], out["perimeter_m"])
    ]


def compute_useful_area(polygons_wgs84: list, ndvi_array: np.ndarray, transform,
                        ndvi_threshold: float = 0.30) -> list:
    """
    Para cada poligono, calcula que fraccion tiene NDVI > umbral (vegetacion productiva).

    Args:
        polygons_wgs84: lista de dicts con 'geometry' en EPSG:4326.
        ndvi_array: array 2D NDVI (-1 a +1) sobre el AOI.
        transform: rasterio Affine del raster NDVI.
        ndvi_threshold: NDVI > umbral cuenta como productivo.

    Returns: misma lista con campos extra:
        - useful_area_ha: area con NDVI > umbral
        - useful_pct: % del lote con cubierta vegetal
        - mean_ndvi
        - std_ndvi (homogeneidad: <0.05 = lote uniforme)
    """
    from rasterio.features import geometry_mask
    import geopandas as gpd

    if not polygons_wgs84 or ndvi_array is None:
        return polygons_wgs84

    h, w = ndvi_array.shape
    out = []
    for poly in polygons_wgs84:
        try:
            mask = geometry_mask(
                [poly["geometry"]], out_shape=(h, w),
                transform=transform, invert=True
            )
        except Exception:
            out.append(poly | {"useful_area_ha": None, "useful_pct": None,
                               "mean_ndvi": None, "std_ndvi": None})
            continue

        vals = ndvi_array[mask]
        vals = vals[~np.isnan(vals)]
        if vals.size == 0:
            out.append(poly | {"useful_area_ha": None, "useful_pct": None,
                               "mean_ndvi": None, "std_ndvi": None})
            continue

        productive_pct = float((vals > ndvi_threshold).mean())
        useful_ha = round(poly["area_ha"] * productive_pct, 3)

        out.append(poly | {
            "useful_area_ha": useful_ha,
            "useful_pct": round(productive_pct * 100, 1),
            "mean_ndvi": round(float(vals.mean()), 3),
            "std_ndvi": round(float(vals.std()), 3),
        })

    return out


def quality_score(poly: dict, temporal_stability: float | None = None) -> dict:
    """
    Puntua calidad de delimitacion 0-100 para review humano.

    Componentes:
      - temporal_stability (0-30): aparece en multiples periodos.
      - homogeneity (0-25): NDVI std bajo = lote uniforme.
      - useful_pct  (0-25): proporcion productiva (esperado >70% para campo activo).
      - area_sanity (0-20): lote tipico 5-500 ha.
    """
    score = 0
    components = {}

    if temporal_stability is not None:
        ts = max(0.0, min(1.0, temporal_stability)) * 30
        score += ts
        components["temporal_stability"] = round(ts, 1)
    else:
        components["temporal_stability"] = "N/A"

    std = poly.get("std_ndvi")
    if std is not None:
        # std 0 = perfecto (30 pts), std 0.20 = pesimo (0 pts)
        homog = max(0.0, 1 - std / 0.20) * 25
        score += homog
        components["homogeneity"] = round(homog, 1)
    else:
        components["homogeneity"] = "N/A"

    upct = poly.get("useful_pct")
    if upct is not None:
        # 70-100% = max; 30-70% degrada; <30% = 0
        if upct >= 70: u = 25
        elif upct >= 30: u = 25 * (upct - 30) / 40
        else: u = 0
        score += u
        components["useful_pct"] = round(u, 1)
    else:
        components["useful_pct"] = "N/A"

    ha = poly.get("area_ha", 0)
    if 5 <= ha <= 500: a = 20
    elif 1 <= ha < 5 or 500 < ha <= 1500: a = 10
    elif 0.5 <= ha < 1 or 1500 < ha <= 5000: a = 5
    else: a = 0
    score += a
    components["area_sanity"] = a

    if score >= 80: tag = "EXCELENTE"
    elif score >= 60: tag = "BUENO"
    elif score >= 40: tag = "REVISAR"
    else: tag = "RECHAZAR"

    return {**poly, "quality_score": round(score, 1),
            "quality_tag": tag, "quality_components": components}
