"""
Refinamiento de un perimetro EXTERNO conocido (contrato, cartografia, dibujo a mano).

Entrada: poligono operador-aportado.
Salida:
  - perimeter_refined: perimetro suavizado y opcionalmente snap a bordes Canny.
  - sub_talhoes: divisiones internas detectadas por Delineate Anything, CLIPEADAS al perimetro.
  - useful_area_ha: area con NDVI > umbral DENTRO del perimetro.
  - useful_pct: % productivo.
  - ndvi_stats: media/std del perimetro.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from shapely import make_valid
from shapely.geometry import Polygon, MultiPolygon, mapping, shape, LineString, Point
from shapely.ops import unary_union


def _to_metric(geom, src_crs="EPSG:4326", dst_crs="EPSG:32722"):
    import geopandas as gpd
    return gpd.GeoSeries([geom], crs=src_crs).to_crs(dst_crs).iloc[0]


def _to_wgs(geom, src_crs="EPSG:32722"):
    import geopandas as gpd
    return gpd.GeoSeries([geom], crs=src_crs).to_crs("EPSG:4326").iloc[0]


def densify_perimeter(poly_metric: Polygon, step_m: float = 5.0) -> Polygon:
    """Inserta vertices intermedios cada step_m metros para que el snap tenga mas anchors."""
    def _densify_ring(ring):
        line = LineString(list(ring.coords))
        L = line.length
        if L <= step_m:
            return list(ring.coords)
        n = int(np.ceil(L / step_m))
        pts = [line.interpolate(i / n, normalized=True) for i in range(n + 1)]
        return [(p.x, p.y) for p in pts]

    if isinstance(poly_metric, MultiPolygon):
        polys = []
        for g in poly_metric.geoms:
            ext = _densify_ring(g.exterior)
            holes = [_densify_ring(h) for h in g.interiors]
            polys.append(Polygon(ext, holes))
        return MultiPolygon(polys)
    ext = _densify_ring(poly_metric.exterior)
    holes = [_densify_ring(h) for h in poly_metric.interiors]
    return Polygon(ext, holes)


def snap_to_edges(poly_metric, edge_raster: np.ndarray, transform,
                  search_m: float = 12.0, min_edge_strength: float = 0.4) -> Polygon:
    """
    Para cada vertice (densificado) busca el pixel-edge mas fuerte dentro de search_m,
    y mueve el vertice a esa posicion. Solo mueve si el edge supera min_edge_strength
    y la nueva posicion no se aleja > search_m.
    """
    inv = ~transform  # mundo -> raster
    h, w = edge_raster.shape

    def _snap_ring(coords):
        out = []
        for x, y in coords:
            try:
                col, row = inv * (x, y)
                col, row = int(round(col)), int(round(row))
            except Exception:
                out.append((x, y)); continue

            # Ventana en pixeles aprox: search_m / pixel_size
            pix_size = abs(transform.a)
            r_pix = max(1, int(search_m / pix_size))
            r0, r1 = max(0, row - r_pix), min(h, row + r_pix + 1)
            c0, c1 = max(0, col - r_pix), min(w, col + r_pix + 1)
            if r1 <= r0 or c1 <= c0:
                out.append((x, y)); continue

            window = edge_raster[r0:r1, c0:c1]
            if window.size == 0 or window.max() < min_edge_strength:
                out.append((x, y)); continue

            # Mejor pixel: max edge strength penalizando distancia
            yy, xx = np.indices(window.shape)
            dist_pix = np.sqrt((yy - (row - r0))**2 + (xx - (col - c0))**2)
            score = window - dist_pix * (min_edge_strength / r_pix)
            best = np.unravel_index(score.argmax(), score.shape)
            new_row, new_col = r0 + best[0], c0 + best[1]
            new_x, new_y = transform * (new_col + 0.5, new_row + 0.5)
            # Validar que el nuevo punto este dentro de search_m del original
            d = np.hypot(new_x - x, new_y - y)
            if d <= search_m:
                out.append((new_x, new_y))
            else:
                out.append((x, y))
        return out

    if isinstance(poly_metric, MultiPolygon):
        return MultiPolygon([
            Polygon(_snap_ring(list(g.exterior.coords)),
                    [_snap_ring(list(h.coords)) for h in g.interiors])
            for g in poly_metric.geoms
        ])
    return Polygon(
        _snap_ring(list(poly_metric.exterior.coords)),
        [_snap_ring(list(h.coords)) for h in poly_metric.interiors]
    )


def chaikin_smooth(poly: Polygon, iterations: int = 1) -> Polygon:
    """Suaviza con Chaikin para eliminar zigzag despues del snap."""
    def _smooth_ring(coords):
        if len(coords) < 4: return coords
        new = []
        for i in range(len(coords) - 1):
            p, q = coords[i], coords[i + 1]
            new.append((0.75*p[0] + 0.25*q[0], 0.75*p[1] + 0.25*q[1]))
            new.append((0.25*p[0] + 0.75*q[0], 0.25*p[1] + 0.75*q[1]))
        new.append(new[0])
        return new

    def _smooth_poly(p):
        ext = list(p.exterior.coords)
        holes = [list(h.coords) for h in p.interiors]
        for _ in range(iterations):
            ext = _smooth_ring(ext)
            holes = [_smooth_ring(h) for h in holes]
        return Polygon(ext, holes)

    if isinstance(poly, MultiPolygon):
        return MultiPolygon([_smooth_poly(g) for g in poly.geoms])
    return _smooth_poly(poly)


def compute_canny_edges(rgb: np.ndarray) -> np.ndarray:
    """Mapa de bordes 0-1 promediando Canny sobre R, G, B."""
    from skimage.feature import canny
    if rgb.dtype != np.uint8:
        rgb = (rgb / max(1, rgb.max()) * 255).astype(np.uint8)
    edges = []
    for c in range(min(3, rgb.shape[2])):
        e = canny(rgb[:, :, c].astype(float) / 255.0, sigma=1.5).astype(float)
        edges.append(e)
    out = np.mean(edges, axis=0)
    # Suavizar con dilatacion ligera para que el snap tenga mas chance
    from scipy.ndimage import maximum_filter
    out = maximum_filter(out, size=3)
    return out


def refine_boundary(perimeter_geojson: dict,
                    rgb: np.ndarray, rgb_transform, rgb_crs,
                    ndvi: np.ndarray, ndvi_transform,
                    sub_polys_wgs: list[dict],
                    snap_m: float = 12.0,
                    densify_m: float = 5.0,
                    smooth_iters: int = 2,
                    ndvi_threshold: float = 0.30,
                    min_inside_pct: float = 0.85,
                    metric_crs: str = "EPSG:32722") -> dict:
    """
    Aplica refinamiento sobre un perimetro externo.

    Args:
        perimeter_geojson: dict GeoJSON Feature/FeatureCollection/geometry.
        rgb, rgb_transform, rgb_crs: array Sentinel-2 RGB del bbox.
        ndvi, ndvi_transform: array NDVI del mismo periodo.
        sub_polys_wgs: lista de dicts {'geometry':Polygon WGS84, 'area_ha':...}
            ya detectados por Delineate Anything en el AOI.
        snap_m: distancia maxima para mover un vertice a un edge.
        densify_m: vertices intermedios cada N metros antes del snap.
        ndvi_threshold: NDVI > umbral cuenta como productivo.
        min_inside_pct: poligono detectado debe estar al menos X% dentro del perimetro.

    Returns:
        dict con perimeter_input, perimeter_refined, sub_talhoes, useful_area, etc.
    """
    from rasterio.features import geometry_mask

    # 1. Parse del perimetro (acepta Feature, FeatureCollection o geometry)
    raw = perimeter_geojson
    if raw.get("type") == "FeatureCollection":
        geoms = [shape(f["geometry"]) for f in raw["features"]]
    elif raw.get("type") == "Feature":
        geoms = [shape(raw["geometry"])]
    else:
        geoms = [shape(raw)]

    perimeter = unary_union([make_valid(g).buffer(0) for g in geoms if not g.is_empty])
    if perimeter.is_empty:
        raise ValueError("Perimetro vacio")

    # 2. Reproyectar a metric
    perim_metric = _to_metric(perimeter)
    if not isinstance(perim_metric, (Polygon, MultiPolygon)):
        raise ValueError(f"Perimetro debe ser Polygon/MultiPolygon, got {type(perim_metric)}")

    area_input_ha = perim_metric.area / 10_000

    # 3. Densificar + snap a edges Canny
    densified = densify_perimeter(perim_metric, step_m=densify_m)
    edge_map = compute_canny_edges(rgb)

    # rgb transform en WGS84 -> hay que reproyectar el edge_map al metric_crs
    # ATAJO: trabajar con perimetro en CRS del raster (WGS84) para el snap, despues volver a metric.
    perim_for_snap = _to_wgs(densified, src_crs=metric_crs)
    if isinstance(perim_for_snap, MultiPolygon):
        snap_input = perim_for_snap
    else:
        snap_input = perim_for_snap

    snapped_wgs = snap_to_edges(snap_input, edge_map, rgb_transform,
                                 search_m=snap_m / 111000,  # grados, aprox
                                 min_edge_strength=0.3)

    # Volver a metric para smoothing y simplify
    snapped_metric = _to_metric(snapped_wgs)
    smoothed = chaikin_smooth(snapped_metric, iterations=smooth_iters)
    refined = make_valid(smoothed).buffer(0)
    if not refined.is_valid or refined.is_empty:
        refined = perim_metric  # fallback al input

    area_refined_ha = refined.area / 10_000
    refined_wgs = _to_wgs(refined)

    # 4. Calcular area util (NDVI > umbral) DENTRO del perimetro refinado
    #    + extraer POLIGONO real de la mancha productiva
    useful_pct = None
    useful_area_ha = None
    mean_ndvi = None
    std_ndvi = None
    productive_polygon = None
    nonproductive_polygon = None
    try:
        from rasterio.features import shapes as rio_shapes
        from scipy.ndimage import binary_closing, binary_opening

        h, w = ndvi.shape
        in_perim = geometry_mask([refined_wgs], out_shape=(h, w),
                                  transform=ndvi_transform, invert=True)
        vals = ndvi[in_perim]
        vals = vals[~np.isnan(vals)]
        if vals.size:
            useful_pct = float((vals > ndvi_threshold).mean())
            useful_area_ha = round(area_refined_ha * useful_pct, 3)
            mean_ndvi = round(float(vals.mean()), 3)
            std_ndvi = round(float(vals.std()), 3)

        # Mascara productiva = (NDVI > umbral) AND (dentro del perimetro)
        prod_mask = (ndvi > ndvi_threshold) & in_perim
        # Limpieza morfologica: cerrar agujeros chicos + abrir para quitar pixeles aislados
        prod_mask = binary_closing(prod_mask, iterations=2)
        prod_mask = binary_opening(prod_mask, iterations=1)

        # Vectorizar mancha productiva
        from shapely.geometry import shape as shp_shape
        from shapely.ops import unary_union as uu
        prod_polys = []
        for geom, val in rio_shapes(prod_mask.astype(np.uint8), transform=ndvi_transform):
            if val == 1:
                g = shp_shape(geom)
                if g.is_valid and g.area > 0:
                    prod_polys.append(g)
        if prod_polys:
            prod_union = uu(prod_polys)
            # Clipping suave al perimetro refinado para que no salga
            prod_clip = prod_union.intersection(refined_wgs)
            prod_clip = make_valid(prod_clip).buffer(0)
            # Filtrar piezas chicas (< 0.1 ha)
            from shapely.geometry import MultiPolygon as MP
            if isinstance(prod_clip, MP):
                pieces = [p for p in prod_clip.geoms if _to_metric(p).area >= 1000]
                if pieces:
                    prod_clip = MP(pieces) if len(pieces) > 1 else pieces[0]
                else:
                    prod_clip = None
            elif _to_metric(prod_clip).area < 1000:
                prod_clip = None
            if prod_clip is not None and not prod_clip.is_empty:
                productive_polygon = mapping(prod_clip)
                # No-productivo = perimetro - productivo
                non = refined_wgs.difference(prod_clip)
                non = make_valid(non).buffer(0)
                if not non.is_empty:
                    nonproductive_polygon = mapping(non)
    except Exception as e:
        useful_pct = None

    # 5. Sub-talhones: filtrar candidatos que esten >= min_inside_pct dentro del perimetro
    sub_talhoes = []
    if sub_polys_wgs:
        for i, p in enumerate(sub_polys_wgs):
            g = p["geometry"]
            try:
                gm = make_valid(g).buffer(0)
                inter = gm.intersection(refined_wgs)
                if inter.is_empty: continue
                inside_pct = inter.area / max(gm.area, 1e-9)
                if inside_pct < min_inside_pct:
                    # Si esta parcialmente dentro, recortar al perimetro pero solo si mas del 50%
                    if inside_pct < 0.50: continue
                    inter_metric = _to_metric(inter)
                    if inter_metric.area < 5000:  # < 0.5 ha post-clip = descartar
                        continue
                    sub_talhoes.append({
                        "geometry": inter,
                        "area_ha": inter_metric.area / 10_000,
                        "inside_pct": round(inside_pct, 3),
                        "clipped": True,
                        "id": len(sub_talhoes),
                    })
                else:
                    g_metric = _to_metric(gm)
                    sub_talhoes.append({
                        "geometry": gm,
                        "area_ha": g_metric.area / 10_000,
                        "inside_pct": round(inside_pct, 3),
                        "clipped": False,
                        "id": len(sub_talhoes),
                    })
            except Exception:
                continue

    return {
        "perimeter_input_ha": round(area_input_ha, 3),
        "perimeter_refined_ha": round(area_refined_ha, 3),
        "perimeter_input_wgs": mapping(perimeter),
        "perimeter_refined_wgs": mapping(refined_wgs),
        "productive_polygon_wgs": productive_polygon,
        "nonproductive_polygon_wgs": nonproductive_polygon,
        "snap_displacement_m": round(abs(area_refined_ha - area_input_ha) / max(area_input_ha,1) * 100, 2),
        "useful_area_ha": useful_area_ha,
        "useful_pct": round(useful_pct * 100, 1) if useful_pct is not None else None,
        "mean_ndvi": mean_ndvi,
        "std_ndvi": std_ndvi,
        "sub_talhoes": [
            {"geometry": mapping(s["geometry"]), "area_ha": round(s["area_ha"], 3),
             "inside_pct": s["inside_pct"], "clipped": s["clipped"], "id": s["id"]}
            for s in sub_talhoes
        ],
        "n_sub_talhoes": len(sub_talhoes),
    }
