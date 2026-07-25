"""
Consenso multi-temporal: corre detección sobre N periodos y conserva solo
poligonos consistentes. ESTE es el cambio mas importante de fiabilidad.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree


def split_periods(start: str, end: str, n_periods: int = 3) -> list[tuple[str, str]]:
    """Divide rango total en N ventanas iguales."""
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    total = (e - s).days
    if total <= 0 or n_periods < 1:
        return [(start, end)]
    step = max(15, total // n_periods)  # min 15 dias por ventana para tener escenas
    periods = []
    cur = s
    while cur < e:
        nxt = min(e, cur + timedelta(days=step))
        periods.append((cur.isoformat(), nxt.isoformat()))
        cur = nxt
    return periods[:n_periods]


def overlap_iou(a: Polygon, b: Polygon) -> float:
    if a.is_empty or b.is_empty:
        return 0.0
    inter = a.intersection(b).area
    if inter == 0:
        return 0.0
    union = a.union(b).area
    return inter / union if union > 0 else 0.0


def consensus_polygons(detections_per_period: list[list[dict]],
                       min_periods: int = 2,
                       iou_match: float = 0.30) -> list[dict]:
    """
    Cruza detecciones de N periodos y conserva poligonos que aparecen en
    >= min_periods de los periodos.

    Args:
        detections_per_period: lista (un slot por periodo) de listas de polys.
            Cada poly es dict con 'geometry' (Polygon EPSG:4326) y 'area_ha'.
        min_periods: minimo periodos en los que debe aparecer.
        iou_match: IoU minimo para considerar "el mismo poligono" entre periodos.

    Returns: lista de poligonos consenso con campo 'temporal_stability' (frac de periodos).
    """
    n = len(detections_per_period)
    if n == 0: return []
    if n == 1:
        return [d | {"temporal_stability": 1.0, "n_periods_detected": 1}
                for d in detections_per_period[0]]

    # Toma el set base con mas detecciones para indexar mejor
    sizes = [len(d) for d in detections_per_period]
    base_idx = sizes.index(max(sizes))
    base = detections_per_period[base_idx]
    if not base:
        return []

    # STRtree para matching rapido geometria-a-geometria
    base_geoms = [d["geometry"] for d in base]
    tree = STRtree(base_geoms)
    geom_to_idx = {id(g): i for i, g in enumerate(base_geoms)}

    matches = [[False] * n for _ in base]  # matches[i][period] = True si poly i aparece en period
    for i in range(len(base)):
        matches[i][base_idx] = True

    for p_idx, dets in enumerate(detections_per_period):
        if p_idx == base_idx: continue
        for d in dets:
            g = d["geometry"]
            candidates = tree.query(g)
            for cand_idx in candidates:
                cand = base_geoms[cand_idx]
                if overlap_iou(cand, g) >= iou_match:
                    matches[cand_idx][p_idx] = True

    out = []
    for i, m in enumerate(matches):
        n_det = sum(m)
        if n_det >= min_periods:
            out.append(base[i] | {
                "temporal_stability": round(n_det / n, 3),
                "n_periods_detected": n_det,
            })
    return out


def merge_adjacent(polys: list[dict], gap_m: float = 8.0,
                   metric_crs: str = "EPSG:32722") -> list[dict]:
    """
    Fusiona poligonos adyacentes separados por gap pequeno (artifacts del raster).
    Util cuando un mismo lote queda partido en 2-3 piezas.

    Args:
        gap_m: distancia maxima en metros para considerar 'adyacentes'.
    """
    import geopandas as gpd
    if not polys: return polys

    gdf = gpd.GeoDataFrame(
        polys, geometry=[p["geometry"] for p in polys], crs="EPSG:4326"
    ).to_crs(metric_crs)

    # Buffer + dissolve + un-buffer (operación clásica de "merge cercanos")
    buffered = gdf.geometry.buffer(gap_m / 2)
    union = buffered.unary_union if hasattr(buffered, "unary_union") else buffered.union_all()
    from shapely.ops import unary_union
    merged = unary_union(list(buffered)).buffer(-gap_m / 2)

    if merged.is_empty: return []
    if merged.geom_type == "Polygon":
        parts = [merged]
    else:
        parts = list(merged.geoms)

    out_geoms = []
    for part in parts:
        if part.area > 0:
            out_geoms.append(part)

    # Reasignar metadata por interseccion: cada parte hereda max stability de sus inputs
    out = []
    for part in out_geoms:
        contributors = [p for p, g in zip(polys, gdf.geometry)
                       if g.intersects(part) or g.distance(part) < gap_m]
        if not contributors:
            continue
        ts = max((c.get("temporal_stability", 1.0) for c in contributors), default=1.0)
        np_det = max((c.get("n_periods_detected", 1) for c in contributors), default=1)
        # Reproyectar a 4326
        part_wgs = gpd.GeoSeries([part], crs=metric_crs).to_crs(4326).iloc[0]
        out.append({
            "geometry": part_wgs,
            "area_ha": part.area / 10_000,
            "perimeter_m": part.length,
            "temporal_stability": ts,
            "n_periods_detected": np_det,
        })

    return out
