# -*- coding: utf-8 -*-
"""Sintesis: vectoriza red de drenaje (flow-acc FABDEM), area util por lote a
varios umbrales, compara con metodo HAND∩riparia, exporta GeoJSON + mapa."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, rasterio
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_Muestreo_Soya_26-27.geojson')).to_crs(31981)
lot['gross_ha'] = lot.area / 1e4
src = rasterio.open(os.path.join(OUTDIR, 'hydro_flowacc.tif')); acc = src.read(1)
lot_u = unary_union(lot.geometry.values)

def network(thr_km2, buf=0):
    thr = thr_km2 * 1e6 / 900.0
    m = (acc > thr).astype('uint8')
    geoms = [shape(g) for g, v in shapes(m, mask=m > 0, transform=src.transform) if v == 1]
    net = unary_union(geoms)
    if buf: net = net.buffer(buf)
    return net.intersection(lot_u)

print('=== Area de drenaje dentro de los lotes segun umbral (cauce ~30m) ===')
res = {}
for thr in (0.27, 0.5, 1.0, 1.8):
    g = network(thr); ha = g.area / 1e4
    res[thr] = g
    print('  acc>%.2f km2 : drenaje %.1f ha (%.1f%% del area)  | util %.1f ha' % (thr, ha, ha/lot['gross_ha'].sum()*100, lot['gross_ha'].sum()-ha))

# primario: acc>0.5 km2 (cauces reales) + buffer +12m (margen riparia no sembrable)
PRIM = 0.5
can_core = res[PRIM]
can_buf = network(PRIM, buf=12)
print('\nPRIMARIO acc>0.5km2: nucleo %.1f ha | con buffer +12m %.1f ha' % (can_core.area/1e4, can_buf.area/1e4))

# comparacion con metodo anterior (HAND∩riparia)
try:
    v3 = gpd.read_file(os.path.join(DIRBASE, 'Canadas_drenajes_SerroAlto.geojson')).to_crs(31981)
    v3u = unary_union(v3.geometry.values).intersection(lot_u)
    inter = can_buf.intersection(v3u).area/1e4
    print('Metodo anterior HAND∩riparia: %.1f ha | solape con red-terreno(buf): %.1f ha' % (v3u.area/1e4, inter))
except Exception as e:
    print('v3 no comparado:', repr(e)[:60])

# --- area util por lote con red-terreno buffer +15m (primario) ---
canu = can_buf
rows = []
for _, r in lot.iterrows():
    cab = r.geometry.intersection(canu).area/1e4
    rows.append((r['lote_id'], r['bloque'], r['gross_ha'], cab, max(r['gross_ha']-cab, 0)))
df = gpd.pd.DataFrame(rows, columns=['lote_id', 'bloque', 'gross_ha', 'canada_ha', 'util_ha'])
df = df.groupby(['lote_id', 'bloque'], as_index=False).sum()
df['canada_%'] = (df['canada_ha']/df['gross_ha']*100).round(1)
df.sort_values(['bloque', 'lote_id']).to_csv(os.path.join(OUTDIR, 'area_util_HIDRO.csv'), index=False, encoding='utf-8-sig')
t = df[['gross_ha', 'canada_ha', 'util_ha']].sum()
print('\n===== AREA UTIL (red terreno acc>1km2 + buffer 15m) =====')
print('  bruta %.1f | drenaje %.1f ha (%.1f%%) | UTIL %.1f ha' % (t['gross_ha'], t['canada_ha'], t['canada_ha']/t['gross_ha']*100, t['util_ha']))

# export GeoJSON red + canada
net_lines = gpd.GeoDataFrame(geometry=[network(0.5)], crs=31981).explode(index_parts=False)
net_lines.to_crs(4326).to_file(os.path.join(DIRBASE, 'Drenaje_red_terreno_SerroAlto.geojson'), driver='GeoJSON')
gpd.GeoDataFrame(geometry=[can_buf], crs=31981).explode(index_parts=False).to_crs(4326).to_file(
    os.path.join(DIRBASE, 'Canadas_HIDRO_SerroAlto.geojson'), driver='GeoJSON')

# --- mapa final ---
fig, ax = plt.subplots(figsize=(11, 11))
lot.plot(ax=ax, color='#a6d96a', edgecolor='#333', linewidth=0.4)
gpd.GeoSeries([can_buf], crs=31981).plot(ax=ax, color='#08519c', alpha=0.85)
ax.set_title('SERRO ALTO - Area util (metodo hidrologico FABDEM)\nbruta %.0f ha | drenaje %.1f ha (%.1f%%) | UTIL %.0f ha'
             % (t['gross_ha'], t['canada_ha'], t['canada_ha']/t['gross_ha']*100, t['util_ha']), fontsize=11)
ax.legend(handles=[mp.Patch(color='#a6d96a', label='Area util %.0f ha' % t['util_ha']),
                   mp.Patch(color='#08519c', label='Drenaje/canada %.1f ha' % t['canada_ha'])], loc='upper right')
ax.set_axis_off(); plt.tight_layout()
plt.savefig(os.path.join(DIRBASE, 'MAPA_Area_UTIL_HIDRO_SerroAlto.png'), dpi=145, bbox_inches='tight')
print('mapa -> MAPA_Area_UTIL_HIDRO_SerroAlto.png')
print('DONE')
