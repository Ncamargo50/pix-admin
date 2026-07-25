# -*- coding: utf-8 -*-
"""Bloque 14: nueva capa de lotes por DIVISION (renumera +6, explota partes,
letras A/B/C Oeste->Este, fusiona L17C en vecino mas contiguo)."""
import os, sys, math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np, rasterio
import warnings; warnings.filterwarnings('ignore')

D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OFFSET = 6   # bloque 14: L01 -> L07

lot = gpd.read_file(os.path.join(D, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(31981)
b14 = lot[lot.bloque.astype(str) == '14'].copy()
b14['n'] = b14.lote_id.str.extract(r'L0*(\d+)').astype(int)

def parts_we(geom):
    ps = [geom] if geom.geom_type == 'Polygon' else list(geom.geoms)
    return sorted(ps, key=lambda p: p.centroid.x)

recs = []
for _, r in b14.sort_values('n').iterrows():
    newn = int(r['n']) + OFFSET
    ps = parts_we(r.geometry)
    if newn == 17:   # fusionar la division chica (<5ha) en el vecino mas contiguo
        ar = [p.area/1e4 for p in ps]
        si = int(np.argmin(ar))
        small = ps[si]; others = [p for j, p in enumerate(ps) if j != si]
        def contig(o): return small.boundary.intersection(o.buffer(1)).length
        best = max(others, key=contig)
        if contig(best) < 1:   # no toca a nadie -> el mas cercano
            best = min(others, key=lambda o: small.distance(o))
        ps = [unary_union([o, small]) if o is best else o for o in others]
        ps = sorted(ps, key=lambda p: p.centroid.x)
        print('Fusionado L17C (%.1f ha) en la division vecina que ahora mide %.1f ha' % (ar[si], best.area/1e4 + small.area/1e4))
    for i, p in enumerate(ps):
        letter = chr(65+i) if len(ps) > 1 else ''
        recs.append(dict(lote='L%02d%s' % (newn, letter), lote_id='Bloque-14-L%02d%s' % (newn, letter),
                         bloque='14', area_ha=round(p.area/1e4, 2), geometry=p))

gd = gpd.GeoDataFrame(recs, crs=31981)
gd.to_crs(4326).to_file(os.path.join(D, 'Lotes_B14_divisiones.geojson'), driver='GeoJSON')
print('Bloque 14: %d divisiones-lote | área %.1f ha' % (len(gd), gd['area_ha'].sum()))
print('Lotes:', ', '.join(gd['lote'].tolist()))

# mapa
gd4 = gd.to_crs(4326); b = gd4.total_bounds
fig, ax = plt.subplots(figsize=(13, 11))
with rasterio.open(os.path.join(D, '_analisis_canadas', 's2_rgb_lotes.tif')) as r:
    win = rasterio.windows.from_bounds(b[0]-0.002, b[1]-0.002, b[2]+0.002, b[3]+0.002, r.transform)
    img = r.read(window=win); ext = rasterio.windows.bounds(win, r.transform)
ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
cmap = cm.get_cmap('tab20')
for i, (_, rr) in enumerate(gd4.iterrows()):
    gpd.GeoSeries([rr.geometry]).plot(ax=ax, facecolor=cmap(i % 20), alpha=0.45, edgecolor='yellow', linewidth=1.0)
    c = rr.geometry.centroid; ax.annotate(rr['lote'], (c.x, c.y), fontsize=7, weight='bold', color='white', ha='center', va='center')
ax.set_title('BLOQUE 14 — capa de lotes por división (FINAL, L17C fusionada) — %d divisiones' % len(gd), fontsize=12)
ax.set_xlim(ext[0], ext[2]); ax.set_ylim(ext[1], ext[3]); ax.set_axis_off(); plt.tight_layout()
plt.savefig(os.path.join(D, '_analisis_canadas', 'B14_divisiones_FINAL.png'), dpi=140, bbox_inches='tight')
print('mapa -> B14_divisiones_FINAL.png'); print('DONE')
