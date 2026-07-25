# -*- coding: utf-8 -*-
"""Consolida cañada (terreno flow-acc + riparia), calcula area util por lote,
genera 1 GeoJSON por lote + global + CSV."""
import os, sys, numpy as np
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd, pandas as pd, rasterio
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely.validation import make_valid
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
INDIV = os.path.join(DIRBASE, 'Lotes_individuales_area_util')
os.makedirs(INDIV, exist_ok=True)

lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_Muestreo_Soya_26-27.geojson')).to_crs(31981)
lot_u = unary_union(lot.geometry.values)

# 1) red terreno (flow-acc > 0.5 km2) buffer +10m
src = rasterio.open(os.path.join(OUTDIR, 'hydro_flowacc.tif')); acc = src.read(1)
thr = 0.5 * 1e6 / 900.0
m = (acc > thr).astype('uint8')
terr = unary_union([shape(g) for g, v in shapes(m, mask=m > 0, transform=src.transform) if v == 1]).buffer(10)
# 2) riparia (HAND ∩ NDVI)
rip = unary_union(gpd.read_file(os.path.join(DIRBASE, 'Canadas_drenajes_SerroAlto.geojson')).to_crs(31981).geometry.values)
# consolidado
canada = make_valid(unary_union([terr, rip])).intersection(lot_u)
print('Cañada consolidada: terreno %.1f ha | riparia %.1f ha | UNION %.1f ha (%.1f%%)' %
      (terr.intersection(lot_u).area/1e4, rip.intersection(lot_u).area/1e4, canada.area/1e4, canada.area/lot_u.area*100))

# 3) por lote: util = lote - canada ; export individual
recs = []
for lid, sub in lot.groupby('lote_id'):
    geom = unary_union(sub.geometry.values)
    bloque = sub['bloque'].iloc[0]
    can_l = make_valid(geom.intersection(canada))
    util_l = make_valid(geom.difference(canada))
    gha, cha, uha = geom.area/1e4, can_l.area/1e4, util_l.area/1e4
    recs.append(dict(lote_id=lid, bloque=bloque, gross_ha=round(gha, 2), canada_ha=round(cha, 2),
                     util_ha=round(uha, 2), canada_pct=round(cha/gha*100, 1)))
    # GeoJSON individual: features util + canada
    feats = []
    gu = gpd.GeoDataFrame([{'lote_id': lid, 'bloque': bloque, 'tipo': 'AREA_UTIL', 'ha': round(uha, 2)}],
                          geometry=[util_l], crs=31981)
    if not can_l.is_empty:
        gc = gpd.GeoDataFrame([{'lote_id': lid, 'bloque': bloque, 'tipo': 'CANADA_DRENAJE', 'ha': round(cha, 2)}],
                              geometry=[can_l], crs=31981)
        gi = pd.concat([gu, gc])
    else:
        gi = gu
    gi.to_crs(4326).to_file(os.path.join(INDIV, '%s_area_util.geojson' % lid), driver='GeoJSON')

df = pd.DataFrame(recs).sort_values(['bloque', 'lote_id'])
df.to_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv'), index=False, encoding='utf-8-sig')

# global consolidado (util por lote, todos)
glob = []
for lid, sub in lot.groupby('lote_id'):
    geom = unary_union(sub.geometry.values); bloque = sub['bloque'].iloc[0]
    util_l = make_valid(geom.difference(canada))
    r = df[df.lote_id == lid].iloc[0]
    glob.append({'lote_id': lid, 'bloque': bloque, 'gross_ha': r['gross_ha'], 'canada_ha': r['canada_ha'],
                 'util_ha': r['util_ha'], 'canada_pct': r['canada_pct'], 'geometry': util_l})
gglob = gpd.GeoDataFrame(glob, crs=31981).to_crs(4326)
gglob.to_file(os.path.join(DIRBASE, 'AREA_UTIL_GLOBAL_SerroAlto.geojson'), driver='GeoJSON')
gpd.GeoDataFrame(geometry=[canada], crs=31981).explode(index_parts=False).to_crs(4326).to_file(
    os.path.join(DIRBASE, 'CANADAS_consolidado_SerroAlto.geojson'), driver='GeoJSON')

print('\nArchivos individuales:', len(df), '-> ', INDIV)
print('Global -> AREA_UTIL_GLOBAL_SerroAlto.geojson')
print('\n=== RESUMEN POR BLOQUE ===')
bl = df.groupby('bloque').agg(lotes=('lote_id', 'nunique'), gross=('gross_ha', 'sum'), canada=('canada_ha', 'sum'), util=('util_ha', 'sum'))
for b, r in bl.iterrows():
    print('  Bloque %-3s: %2d lotes | bruta %7.1f | cañada %5.1f (%.1f%%) | UTIL %7.1f ha' % (b, r['lotes'], r['gross'], r['canada'], r['canada']/r['gross']*100, r['util']))
t = df[['gross_ha', 'canada_ha', 'util_ha']].sum()
print('  TOTAL    : %2d lotes | bruta %7.1f | cañada %5.1f (%.1f%%) | UTIL %7.1f ha' % (len(df), t['gross_ha'], t['canada_ha'], t['canada_ha']/t['gross_ha']*100, t['util_ha']))
print('DONE')
