"""
Deteccion de areas productivas COMO POLIGONOS CANDIDATOS sin perimetro previo.

Caso de uso: el operador NO tiene shapefile/KML del cliente. Solo sabe la zona
geografica aproximada (bbox). El sistema:
  1. Compone NDVI multi-temporal del periodo.
  2. Mascara NDVI > umbral.
  3. Morfologia: closing/opening para limpiar.
  4. Etiqueta componentes conectados.
  5. Vectoriza cada componente como un poligono candidato.
  6. Suaviza + simplifica cada uno.
  7. Devuelve sorted por area DESC.

El operador despues elige cual de los candidatos es el lote de su cliente,
y ese poligono entra al pipeline de refinement como input.
"""
from __future__ import annotations

import numpy as np
from shapely import make_valid
from shapely.geometry import Polygon, MultiPolygon, mapping, shape
from shapely.ops import unary_union


def _to_metric(geom, src_crs="EPSG:4326", dst_crs="EPSG:32722"):
    import geopandas as gpd
    return gpd.GeoSeries([geom], crs=src_crs).to_crs(dst_crs).iloc[0]


def _to_wgs(geom, src_crs="EPSG:32722"):
    import geopandas as gpd
    return gpd.GeoSeries([geom], crs=src_crs).to_crs("EPSG:4326").iloc[0]


def chaikin_smooth(poly: Polygon, iterations: int = 2) -> Polygon:
    def _smooth_ring(coords):
        if len(coords) < 4: return coords
        new = []
        for i in range(len(coords) - 1):
            p, q = coords[i], coords[i + 1]
            new.append((0.75*p[0] + 0.25*q[0], 0.75*p[1] + 0.25*q[1]))
            new.append((0.25*p[0] + 0.75*q[0], 0.25*p[1] + 0.75*q[1]))
        new.append(new[0])
        return new

    if isinstance(poly, MultiPolygon):
        return MultiPolygon([chaikin_smooth(g, iterations) for g in poly.geoms])
    ext = list(poly.exterior.coords)
    holes = [list(h.coords) for h in poly.interiors]
    for _ in range(iterations):
        ext = _smooth_ring(ext)
        holes = [_smooth_ring(h) for h in holes]
    return Polygon(ext, holes)


def detect_productive_perimeters(
    ndvi: np.ndarray, ndvi_transform,
    threshold: float = 0.30,
    min_area_ha: float = 5.0,
    max_area_ha: float = 5000.0,
    smooth_iters: int = 3,
    simplify_m: float = 8.0,
    closing_iters: int = 3,
    opening_iters: int = 1,
    metric_crs: str = "EPSG:32722",
) -> list[dict]:
    """
    Identifica componentes productivos independientes en un NDVI.

    Returns:
        Lista de dicts ordenada por area DESC, con:
        - geometry: shapely.Polygon en EPSG:4326
        - area_ha
        - mean_ndvi, std_ndvi
        - bbox: [W,S,E,N] WGS84
    """
    from rasterio.features import shapes as rio_shapes
    from scipy.ndimage import binary_closing, binary_opening, label as ndi_label

    if ndvi is None or ndvi.size == 0:
        return []

    valid_ndvi = ~np.isnan(ndvi)
    mask = ((ndvi > threshold) & valid_ndvi).astype(np.uint8)

    # Limpieza morfologica
    if closing_iters > 0:
        mask = binary_closing(mask, iterations=closing_iters).astype(np.uint8)
    if opening_iters > 0:
        mask = binary_opening(mask, iterations=opening_iters).astype(np.uint8)

    # Componentes conectados (8-connectivity)
    labeled, n_comp = ndi_label(mask, structure=np.ones((3, 3)))
    if n_comp == 0:
        return []

    candidates = []
    for comp_id in range(1, n_comp + 1):
        comp_mask = (labeled == comp_id).astype(np.uint8)

        # Quick area check via pixel count
        pixel_count = int(comp_mask.sum())
        pixel_area_m2 = abs(ndvi_transform.a) * abs(ndvi_transform.e) * 111000 * 111000  # grados->m
        # Mas preciso: reproyectar despues. Por ahora estimacion para filtro grueso
        if pixel_count * pixel_area_m2 / 10_000 < min_area_ha * 0.3:
            continue

        polys = []
        for geom, val in rio_shapes(comp_mask, transform=ndvi_transform):
            if val == 1:
                g = shape(geom)
                if g.is_valid and not g.is_empty:
                    polys.append(g)
        if not polys:
            continue

        union = unary_union(polys)
        if isinstance(union, MultiPolygon):
            union = max(union.geoms, key=lambda p: p.area)

        # Reproyectar a metric para area precisa + smoothing
        try:
            union_metric = _to_metric(union)
            area_ha_pre = union_metric.area / 10_000
        except Exception:
            continue
        if area_ha_pre < min_area_ha or area_ha_pre > max_area_ha:
            continue

        # Smooth + simplify
        try:
            smooth = chaikin_smooth(union_metric, iterations=smooth_iters)
            simple = smooth.simplify(simplify_m, preserve_topology=True)
            valid = make_valid(simple).buffer(0)
            if isinstance(valid, MultiPolygon):
                valid = max(valid.geoms, key=lambda p: p.area)
            if valid.is_empty:
                continue
        except Exception:
            valid = union_metric

        area_ha = valid.area / 10_000
        if area_ha < min_area_ha:
            continue

        # Estadisticas NDVI dentro del componente original (antes del smoothing)
        comp_ndvi = ndvi[(labeled == comp_id) & valid_ndvi]
        mean_ndvi = float(comp_ndvi.mean()) if comp_ndvi.size else None
        std_ndvi = float(comp_ndvi.std()) if comp_ndvi.size else None

        # Volver a WGS84
        valid_wgs = _to_wgs(valid)
        bx = valid_wgs.bounds  # (minx, miny, maxx, maxy)

        candidates.append({
            "geometry": valid_wgs,
            "area_ha": round(area_ha, 3),
            "mean_ndvi": round(mean_ndvi, 3) if mean_ndvi is not None else None,
            "std_ndvi": round(std_ndvi, 3) if std_ndvi is not None else None,
            "bbox": [round(b, 6) for b in bx],
            "pixel_count": pixel_count,
        })

    candidates.sort(key=lambda c: c["area_ha"], reverse=True)
    for i, c in enumerate(candidates):
        c["id"] = i
    return candidates
