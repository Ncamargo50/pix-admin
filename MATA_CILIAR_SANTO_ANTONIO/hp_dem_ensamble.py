# -*- coding: utf-8 -*-
"""Helper de an_11: red de drenaje por DEM (pysheds D8) para VARIOS DEM, calibracion del
umbral de aporte contra FBDS y dispersion posicional entre DEM.

Funciones puras (sin efectos globales): reciben rutas y geometrias, devuelven GeoDataFrames
en EPSG:31982 y diccionarios de metricas. Las cabeceras (inicio de tramo de 1er orden) se
devuelven como puntos para el cruce con las nascentes candidatas.
"""
import numpy as np
import geopandas as gpd
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, unary_union
from shapely.strtree import STRtree
from scipy import ndimage as ndi

from an_00_config import CRS_METRICO, log, verificar_rango

# D8 de pysheds: (E, SE, S, SW, W, NW, N, NE) -> desplazamientos (drow, dcol)
_D8 = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}


def red_por_dem(ruta_dem, nombre, umbrales_ha, rango=(400, 1000)):
    """Corre pysheds sobre un DEM y devuelve dict con acc, fdir, perfil y redes por umbral.

    Devuelve: {'acc', 'fdir', 'dem_cond', 'transform', 'cell_ha', 'redes': {umbral: GeoDataFrame}}
    """
    from pysheds.grid import Grid
    grid = Grid.from_raster(ruta_dem)
    dem = grid.read_raster(ruta_dem)
    verificar_rango('DEM %s' % nombre, np.asarray(dem), *rango)
    pit = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit)
    inflated = grid.resolve_flats(flooded)
    fdir = grid.flowdir(inflated)
    acc = grid.accumulation(fdir)
    tr = grid.affine
    cell_ha = abs(tr.a * tr.e) / 1e4
    acc_a = np.asarray(acc, dtype=np.float64)
    fdir_a = np.asarray(fdir, dtype=np.int32)
    redes = {u: _vectorizar_red(acc_a, fdir_a, tr, u / cell_ha, u) for u in umbrales_ha}
    return {'nombre': nombre, 'acc': acc_a, 'fdir': fdir_a, 'dem_cond': np.asarray(inflated, dtype=np.float32),
            'transform': tr, 'cell_ha': cell_ha, 'redes': redes, 'grid': grid, 'flooded': flooded, 'fdir_obj': fdir}


def _vectorizar_red(acc, fdir, tr, umbral_celdas, umbral_ha):
    """Red D8 como segmentos celda->celda aguas abajo (linemerge despues). Centro de celda."""
    mask = acc > umbral_celdas
    rows, cols = np.where(mask)
    segs = []
    for r, c in zip(rows, cols):
        d = _D8.get(int(fdir[r, c]))
        if d is None:
            continue
        r2, c2 = r + d[0], c + d[1]
        if not (0 <= r2 < acc.shape[0] and 0 <= c2 < acc.shape[1]):
            continue
        x1, y1 = tr * (c + 0.5, r + 0.5)
        x2, y2 = tr * (c2 + 0.5, r2 + 0.5)
        segs.append(LineString([(x1, y1), (x2, y2)]))
    if not segs:
        return gpd.GeoDataFrame({'umbral_ha': []}, geometry=[], crs=CRS_METRICO)
    merged = linemerge(unary_union(segs))
    geoms = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
    return gpd.GeoDataFrame({'umbral_ha': [umbral_ha] * len(geoms)}, geometry=geoms, crs=CRS_METRICO)


def cabeceras(red_gdf, acc=None, transform=None, umbral_celdas=None, tol=1.0):
    """Puntos de inicio de la red (1er orden): extremos que NO tocan ninguna otra linea de la
    red y cuya acumulacion es baja (< 3 x umbral): asi se excluyen confluencias y la salida."""
    if len(red_gdf) == 0:
        return []
    geoms = [g for g in red_gdf.geometry if not g.is_empty]
    tree = STRtree(geoms)
    out = []
    for i, g in enumerate(geoms):
        for p in (Point(g.coords[0]), Point(g.coords[-1])):
            toca = any(j != i and geoms[j].distance(p) < tol for j in tree.query(p.buffer(tol)))
            if toca:
                continue
            if acc is not None:
                c, r = ~transform * (p.x, p.y)
                r, c = int(r), int(c)
                if not (0 <= r < acc.shape[0] and 0 <= c < acc.shape[1]):
                    continue
                if acc[r, c] > 3 * umbral_celdas:
                    continue   # salida de la red, no cabecera
            out.append(p)
    return out


def puntos_a_lo_largo(geoms, paso=10.0):
    pts = []
    for g in geoms:
        if g is None or g.is_empty or g.length == 0:
            continue
        n = max(2, int(g.length // paso) + 1)
        pts.extend([g.interpolate(d) for d in np.linspace(0, g.length, n)])
    return pts


def distancias(pts, geoms_ref):
    geoms_ref = [g for g in geoms_ref if g is not None and not g.is_empty]
    if not geoms_ref or not pts:
        return np.full(len(pts), np.nan)
    tree = STRtree(geoms_ref)
    idx = tree.nearest(pts)
    return np.array([pts[i].distance(geoms_ref[j]) for i, j in zip(range(len(pts)), idx)])


def calibrar_umbral(redes, fbds_geoms, zona):
    """Suma de medianas simetricas FBDS->DEM y DEM->FBDS dentro de `zona`; elige el minimo."""
    fbds_z = [g.intersection(zona) for g in fbds_geoms]
    fbds_z = [g for g in fbds_z if not g.is_empty]
    fpts = puntos_a_lo_largo(fbds_z)
    calib = {}
    for u, red in redes.items():
        rz = [g.intersection(zona) for g in red.geometry]
        rz = [g for g in rz if not g.is_empty]
        d1 = distancias(fpts, rz)
        d2 = distancias(puntos_a_lo_largo(rz), fbds_z)
        calib[u] = {'km_dem': round(sum(g.length for g in rz) / 1e3, 3),
                    'km_fbds': round(sum(g.length for g in fbds_z) / 1e3, 3),
                    'fbds_a_dem_med_m': float(np.nanmedian(d1)) if len(d1) else None,
                    'fbds_a_dem_p90_m': float(np.nanpercentile(d1, 90)) if len(d1) else None,
                    'dem_a_fbds_med_m': float(np.nanmedian(d2)) if len(d2) else None,
                    'dem_a_fbds_p90_m': float(np.nanpercentile(d2, 90)) if len(d2) else None}
    ok = {u: v for u, v in calib.items() if v['fbds_a_dem_med_m'] is not None and v['dem_a_fbds_med_m'] is not None}
    u_opt = min(ok, key=lambda u: ok[u]['fbds_a_dem_med_m'] + ok[u]['dem_a_fbds_med_m']) if ok else None
    return calib, u_opt


def desplazamientos_por_arroio(arroio_geom, redes_opt, paso=10.0, dmax=150.0):
    """Para cada punto del eje FBDS del arroio, el vector al punto mas cercano de cada DEM.

    Devuelve (pts_fbds, {dem: array de distancias}, {dem: array Nx2 de puntos mas cercanos}).
    Distancias > dmax se consideran 'sin correspondencia' (NaN) para no arrastrar otro cauce.
    """
    pts = puntos_a_lo_largo([arroio_geom], paso)
    dist, near = {}, {}
    for nombre, red in redes_opt.items():
        geoms = [g for g in red.geometry if not g.is_empty]
        if not geoms or not pts:
            dist[nombre] = np.full(len(pts), np.nan); near[nombre] = np.full((len(pts), 2), np.nan); continue
        tree = STRtree(geoms)
        idx = tree.nearest(pts)
        d = np.empty(len(pts)); xy = np.empty((len(pts), 2))
        for i, j in zip(range(len(pts)), idx):
            g = geoms[j]
            q = g.interpolate(g.project(pts[i]))
            dd = pts[i].distance(q)
            if dd > dmax:
                d[i] = np.nan; xy[i] = (np.nan, np.nan)
            else:
                d[i] = dd; xy[i] = (q.x, q.y)
        dist[nombre] = d; near[nombre] = xy
    return pts, dist, near


def linea_mediana_ensamble(pts, near, min_dems=3):
    """Linea 'mediana del ensamble': en cada punto FBDS, mediana por componente de los puntos
    mas cercanos de los DEM (solo donde >= min_dems tienen correspondencia)."""
    coords = []
    for i, p in enumerate(pts):
        xs = np.array([near[k][i] for k in near])
        ok = np.isfinite(xs[:, 0])
        if ok.sum() >= min_dems:
            coords.append((float(np.median(xs[ok, 0])), float(np.median(xs[ok, 1]))))
        else:
            coords.append((p.x, p.y))   # sin consenso: se conserva el FBDS
    if len(coords) < 2:
        return None
    ln = LineString(coords)
    # suavizado leve para quitar el zig-zag de celda (30 m) sin mover el trazado
    return ln.simplify(5.0)
