# -*- coding: utf-8 -*-
"""Bloque 14 — re-genera PUNTOS con nomenclatura nueva: 1 principal por ambiente
P{zona} (P1=Baja, P2=Media, P3=Alta), submuestra {lote}-B14-P{zona}-{NN}.
Principal en el centro del ambiente. Reusa ZONAS_B14_GLOBAL. + APK + PNG."""
import os, sys, math, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, numpy as np, rasterio
from shapely.geometry import Point, mapping
from shapely.ops import unary_union
from shapely import ops as shops
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings('ignore')

D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUT = os.path.join(D, '_analisis_canadas'); PNGD = os.path.join(OUT, 'B14_muestreo_png'); os.makedirs(PNGD, exist_ok=True)
APKD = os.path.join(D, 'APK_muestreo_por_lote')
CLASE = {1: 'Baja', 2: 'Media', 3: 'Alta'}; COLOR = {'Baja': '#F44336', 'Media': '#FFEB3B', 'Alta': '#4CAF50'}
CLZ = {'Baja': 1, 'Media': 2, 'Alta': 3}; EDGE_BUF = 20.0

def dens(a):  # submuestras por ambiente segun area
    return 5 if a < 3 else 7 if a < 10 else 10 if a < 20 else 12

def center(poly):
    p = poly if poly.geom_type == 'Polygon' else max(poly.geoms, key=lambda g: g.area)
    try: return shops.polylabel(p, tolerance=2)
    except Exception: return p.representative_point()

def core_of(poly):
    for b in (EDGE_BUF, 12, 6, 0):
        c = poly.buffer(-b)
        if (not c.is_empty) and c.area >= max(0.1*poly.area, 1200): return c
    return poly

def grid_pts(g, sp):
    mnx, mny, mxx, mxy = g.bounds; o = []; y = mny
    while y <= mxy:
        x = mnx
        while x <= mxx:
            if g.contains(Point(x, y)): o.append(Point(x, y))
            x += sp
        y += sp
    return o

def fps(g, n, seed):
    sp = max(math.sqrt(max(g.area, 1)/(n*6)), 4); cs = grid_pts(g, sp)
    while len(cs) < n*2 and sp > 2.5: sp *= .6; cs = grid_pts(g, sp)
    if not cs: cs = [g.representative_point()]
    sel = [seed]; pool = [p for p in cs if p.distance(seed) > .1]
    while len(sel) < n+1 and pool:
        d = [min(p.distance(s) for s in sel) for p in pool]; nx = pool[int(np.argmax(d))]; sel.append(nx); pool.remove(nx)
    return sel[1:n+1]

zg = gpd.read_file(os.path.join(D, 'ZONAS_B14_GLOBAL.geojson')).to_crs(31981)
div = gpd.read_file(os.path.join(D, 'Lotes_B14_divisiones.geojson')).to_crs(31981)
precs = []
for (lote, zona), grp in zg.groupby(['lote', 'zona']):
    geom = unary_union(grp.geometry.values); clase = grp['clase'].iloc[0]; z = int(zona)
    area = geom.area/1e4; core = core_of(geom)
    prin = center(core)
    pid = '%s-B14-P%d' % (lote, z)
    precs.append(dict(punto_id=pid, tipo='PRINCIPAL', lote=lote, bloque='14', zona=z, clase=clase, principal=pid, geometry=prin))
    for ms, sp in enumerate(fps(core, dens(area), prin), 1):
        precs.append(dict(punto_id='%s-%02d' % (pid, ms), tipo='SUBMUESTRA', lote=lote, bloque='14', zona=z, clase=clase, principal=pid, geometry=sp))

pg = gpd.GeoDataFrame(precs, crs=31981)
pg4 = pg.to_crs(4326); pg4['lon'] = pg4.geometry.x.round(6); pg4['lat'] = pg4.geometry.y.round(6)
pg4.to_file(os.path.join(D, 'PUNTOS_B14.geojson'), driver='GeoJSON')
pg4.drop(columns='geometry').to_csv(os.path.join(OUT, 'B14_puntos.csv'), index=False, encoding='utf-8-sig')

# APK geojson por lote (zonas con zona/clase/color + puntos coloreados, sin boundary)
zg4 = zg.to_crs(4326)
for lote in div['lote']:
    feats = []
    for _, zr in zg4[zg4.lote == lote].iterrows():
        feats.append({'type': 'Feature', 'properties': {'name': 'Zona %d' % int(zr['zona']), 'zona': int(zr['zona']),
                      'clase': zr['clase'], 'color': COLOR[zr['clase']], 'area_ha': round(zr.geometry.area, 1), 'type': 'zona'},
                      'geometry': mapping(zr.geometry)})
    for _, pr in pg4[pg4.lote == lote].iterrows():
        feats.append({'type': 'Feature', 'properties': {'id': pr['punto_id'], 'name': pr['punto_id'], 'tipo': pr['tipo'].lower(),
                      'zona': int(pr['zona']), 'clase': pr['clase'], 'principal': pr['principal'], 'status': 'pendiente',
                      'marker-color': COLOR[pr['clase']], 'type': 'point'}, 'geometry': mapping(pr.geometry)})
    with open(os.path.join(APKD, 'Bloque-14-%s_muestreo.geojson' % lote), 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'name': 'B14-%s' % lote, 'features': feats}, f, ensure_ascii=False)

# PNG por division
rs = rasterio.open(os.path.join(OUT, 's2_rgb_lotes.tif')); divv = div.to_crs(4326)
for _, lr in divv.iterrows():
    lote = lr['lote']; geom = lr.geometry; b = geom.bounds
    mx = (b[2]-b[0])*0.08+6e-4; my = (b[3]-b[1])*0.08+6e-4
    win = rasterio.windows.from_bounds(b[0]-mx, b[1]-my, b[2]+mx, b[3]+my, rs.transform)
    img = rs.read(window=win); ext = rasterio.windows.bounds(win, rs.transform)
    fig, ax = plt.subplots(figsize=(8, 6.5)); ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
    for cl in ['Baja', 'Media', 'Alta']:
        s = zg4[(zg4.lote == lote) & (zg4.clase == cl)]
        if len(s): s.plot(ax=ax, color=COLOR[cl], alpha=0.45, edgecolor='white', linewidth=0.4)
    gpd.GeoSeries([geom]).boundary.plot(ax=ax, color='cyan', linewidth=1.3)
    pl = pg4[pg4.lote == lote]; sub = pl[pl.tipo == 'SUBMUESTRA']; pri = pl[pl.tipo == 'PRINCIPAL']
    ax.scatter(sub.geometry.x, sub.geometry.y, s=10, c='black', alpha=0.6, zorder=4)
    ax.scatter(pri.geometry.x, pri.geometry.y, s=110, c=[COLOR[c] for c in pri.clase], edgecolor='white', linewidth=1.3, zorder=5)
    for _, r in pri.iterrows():
        ax.annotate('P%d' % r['zona'], (r.geometry.x, r.geometry.y), fontsize=7, color='white', weight='bold', ha='center', va='center', zorder=6)
    ar = div[div.lote == lote]['area_ha'].iloc[0]
    ax.set_title('Bloque 14 — %s (%.1f ha)\nP1=Baja  P2=Media  P3=Alta  ·  %d principales + %d submuestras' % (lote, ar, len(pri), len(sub)), fontsize=10)
    ax.set_xlim(ext[0], ext[2]); ax.set_ylim(ext[1], ext[3]); ax.set_axis_off(); plt.tight_layout()
    plt.savefig(os.path.join(PNGD, '%s.png' % lote), dpi=110, bbox_inches='tight'); plt.close()

nP = (pg.tipo == 'PRINCIPAL').sum(); nS = (pg.tipo == 'SUBMUESTRA').sum()
print('Bloque 14 puntos v2: %d principales (P1/P2/P3 = Baja/Media/Alta) + %d submuestras' % (nP, nS))
print('Ejemplo:', list(pg4[pg4.lote == 'L13B']['punto_id']))
print('DONE')
