# -*- coding: utf-8 -*-
"""F (v2): Puntos de muestreo por zona — composite REPRESENTATIVO del ambiente.
Submuestras distribuidas por TODA la zona (FPS) + buffer de borde. Principal =
centro del conjunto. Regla densidad skill 1.4 + nomenclatura."""
import os, sys, math, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd
from shapely.geometry import Point, MultiPoint
from shapely.ops import nearest_points
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
CLASE = {1: 'Baja', 2: 'Media', 3: 'Alta'}
EDGE_BUF = 20.0   # m desde el borde (adaptativo)

def densidad(area_ha):
    if area_ha < 3:    return 1, 5
    elif area_ha < 10: return 1, 7
    elif area_ha < 20: return 1, 10
    else:              return 2, 8

def core_of(poly):
    for b in (EDGE_BUF, 12, 6, 0):
        c = poly.buffer(-b)
        if (not c.is_empty) and c.area >= max(0.1*poly.area, 1500):
            return c
    return poly

def grid_pts(geom, spacing):
    minx, miny, maxx, maxy = geom.bounds; out = []; y = miny
    while y <= maxy:
        x = minx
        while x <= maxx:
            p = Point(x, y)
            if geom.contains(p): out.append(p)
            x += spacing
        y += spacing
    return out

def candidates(geom, n):
    sp = max(math.sqrt(max(geom.area, 1)/(n*6)), 4)
    c = grid_pts(geom, sp)
    while len(c) < n*2 and sp > 2.5:
        sp *= 0.6; c = grid_pts(geom, sp)
    if not c: c = [geom.representative_point()]
    return c

def fps_pts(cands, n, seed=None):
    if not cands: return []
    sel = [seed or cands[0]]; pool = [p for p in cands if p.distance(sel[0]) > 0.1]
    while len(sel) < n and pool:
        d = [min(p.distance(s) for s in sel) for p in pool]
        nxt = pool[int(np.argmax(d))]; sel.append(nxt); pool.remove(nxt)
    return sel[:n]

def snap_in(geom, pt):
    return pt if geom.contains(pt) else nearest_points(geom, pt)[0]

zones = gpd.read_file(os.path.join(DIRBASE, 'ZONAS_MANEJO_GLOBAL_SerroAlto.geojson')).to_crs(31981)
recs = []
for (lid, zona), grp in zones.groupby(['lote_id', 'zona']):
    poly = grp.geometry.union_all() if hasattr(grp.geometry, 'union_all') else grp.unary_union
    bloque = grp['bloque'].iloc[0]; clase = CLASE.get(int(zona), str(zona))
    pref = 'B%s-%s' % (bloque, lid.split('-')[-1])
    nP, nS = densidad(poly.area/1e4)
    core = core_of(poly)
    cands = candidates(core, max(nP*nS, 6))
    # particionar en nP subregiones bien separadas
    seeds = fps_pts(cands, nP, seed=core.representative_point())
    groups = {i: [] for i in range(nP)}
    for c in cands:
        gi = int(np.argmin([c.distance(s) for s in seeds])); groups[gi].append(c)
    for ip in range(nP):
        sub_c = groups[ip] or cands
        subs = fps_pts(sub_c, nS, seed=seeds[ip])               # submuestras distribuidas en la subregion
        cen = snap_in(core, MultiPoint(subs).centroid) if subs else seeds[ip]
        pid = '%s-Z%d-P%d' % (pref, int(zona), ip+1)
        recs.append(dict(punto_id=pid, tipo='PRINCIPAL', lote_id=lid, bloque=bloque, zona=int(zona),
                         clase=clase, principal=pid, n_sub=len(subs), geometry=cen))
        for ms, sp in enumerate(subs, 1):
            recs.append(dict(punto_id='%s-S%d' % (pid, ms), tipo='SUBMUESTRA', lote_id=lid, bloque=bloque,
                             zona=int(zona), clase=clase, principal=pid, n_sub=len(subs), geometry=sp))

g = gpd.GeoDataFrame(recs, crs=31981)
# verificacion: distancia minima al borde de cada punto
zunion = zones.dissolve('lote_id').reset_index()
zbyid = {r['lote_id']: r.geometry.boundary for _, r in zunion.iterrows()}
g['dist_borde_m'] = g.apply(lambda r: round(r.geometry.distance(zbyid[r['lote_id']]), 1), axis=1)
g4 = g.to_crs(4326); g4['lon'] = g4.geometry.x.round(6); g4['lat'] = g4.geometry.y.round(6)
g4.to_file(os.path.join(DIRBASE, 'PUNTOS_MUESTREO_GLOBAL_SerroAlto.geojson'), driver='GeoJSON')
g4.drop(columns='geometry').to_csv(os.path.join(DIRBASE, 'Puntos_muestreo.csv'), index=False, encoding='utf-8-sig')

nP_ = (g.tipo == 'PRINCIPAL').sum(); nS_ = (g.tipo == 'SUBMUESTRA').sum()
print('Puntos: %d principales + %d submuestras = %d' % (nP_, nS_, len(g)))
print('Distancia al borde: min %.1f m | mediana %.1f m | <10m: %d puntos' % (g['dist_borde_m'].min(), g['dist_borde_m'].median(), (g['dist_borde_m'] < 10).sum()))
print('Submuestras por composite (dispersion): mediana spread %.0f m' %
      g[g.tipo == 'SUBMUESTRA'].groupby('principal').apply(lambda d: d.geometry.union_all().convex_hull.length if len(d) > 2 else 0).median())
print('Ejemplo:', list(g4['punto_id'].head(7)))
print('DONE')
