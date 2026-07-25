# -*- coding: utf-8 -*-
"""Cerro Alto cañadas v3 (limpio): HAND (drenaje, MERIT) ∩ riparia (NDVI sobre
fondo local). Validacion + vectorizado + area util por lote + export GeoJSON."""
import ee, json, os, urllib.request
import geopandas as gpd, pandas as pd
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
LOT = os.path.join(DIRBASE, 'Lotes_SerroAlto_Muestreo_Soya_26-27.geojson')
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
T_HAND, T_RIP = 3.0, 0.04

gdf = gpd.read_file(LOT).to_crs(4326)
fcs = ee.FeatureCollection(json.loads(gdf[['lote_id', 'geometry']].to_json()))
aoi = fcs.geometry()
outlineViz = ee.Image().byte().paint(fcs, 1, 1).selfMask().visualize(palette=['00e5ff'])

hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').clip(aoi.buffer(200))

def cloudmask(img):
    p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
    return img.updateMask(p.gt(35).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1)).Not())
sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate('2025-01-01', '2026-06-25').filter(ee.Filter.calendarRange(5, 9, 'month'))
cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate('2025-01-01', '2026-06-25').filter(ee.Filter.calendarRange(5, 9, 'month'))
dry = ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl,
      condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))).map(cloudmask).median().clip(aoi.buffer(200))
ndvi = dry.normalizedDifference(['B8', 'B4'])
ripar = ndvi.subtract(ndvi.focal_mean(200, 'circle', 'meters'))

canada = hand.lt(T_HAND).And(ripar.gt(T_RIP))
canada = canada.focal_max(1).focal_min(1).selfMask().rename('c')   # cierre morfologico ligero

# --- validacion visual ---
tc = dry.select(['B4', 'B3', 'B2']).visualize(min=200, max=1500, gamma=1.1)
ov = tc.blend(canada.visualize(palette=['ff0000'])).blend(outlineViz)
p = os.path.join(OUTDIR, '10_VALIDACION_v3.png')
urllib.request.urlretrieve(ov.getThumbURL({'region': aoi, 'dimensions': 1200, 'format': 'png'}), p)
print('validacion ->', os.path.basename(p));
import sys; sys.stdout.flush()

# --- vectorizar cañada ---
vec = canada.int().reduceToVectors(geometry=aoi, scale=10, eightConnected=True,
      geometryType='polygon', maxPixels=1e9, bestEffort=True, tileScale=4)
gj = vec.getInfo()
can = gpd.GeoDataFrame.from_features(gj['features'], crs='EPSG:4326')
print('poligonos cañada:', len(can)); sys.stdout.flush()

# --- area util por lote (vector) ---
gdf_m = gdf.to_crs(31981); gdf['gross_ha'] = (gdf_m.area / 1e4).values
if len(can):
    cu = can.to_crs(31981).buffer(0).unary_union
    gm = gdf.to_crs(31981).copy()
    gm['canada_ha'] = gm.geometry.apply(lambda g: g.intersection(cu).area / 1e4)
    util_geom = gm.geometry.apply(lambda g: g.difference(cu))
else:
    gm = gdf.to_crs(31981).copy(); gm['canada_ha'] = 0.0; util_geom = gm.geometry
gm['util_ha'] = (gm['gross_ha'] - gm['canada_ha']).clip(lower=0)

# export
util_out = gm.copy(); util_out['geometry'] = util_geom
util_out.to_crs(4326)[['lote_id', 'bloque', 'gross_ha', 'canada_ha', 'util_ha', 'geometry']].to_file(
    os.path.join(DIRBASE, 'Area_UTIL_siembra_SerroAlto.geojson'), driver='GeoJSON')
if len(can):
    can.to_crs(4326).to_file(os.path.join(DIRBASE, 'Canadas_drenajes_SerroAlto.geojson'), driver='GeoJSON')

tab = gm.groupby(['lote_id', 'bloque'], as_index=False).agg(gross_ha=('gross_ha', 'sum'), canada_ha=('canada_ha', 'sum'), util_ha=('util_ha', 'sum'))
tab['canada_%'] = (tab['canada_ha'] / tab['gross_ha'] * 100).round(1)
tab.sort_values(['bloque', 'lote_id']).to_csv(os.path.join(OUTDIR, 'area_util_FINAL.csv'), index=False, encoding='utf-8-sig')
t = tab[['gross_ha', 'canada_ha', 'util_ha']].sum()
print('\n===== RESULTADO (HAND<%.1fm ∩ riparia>%.2f) =====' % (T_HAND, T_RIP))
print('  bruta %.1f ha | cañada/drenaje %.1f ha (%.1f%%) | AREA UTIL %.1f ha' % (t['gross_ha'], t['canada_ha'], t['canada_ha']/t['gross_ha']*100, t['util_ha']))
print('  por bloque:')
for b, r in tab.groupby('bloque').agg(g=('gross_ha', 'sum'), c=('canada_ha', 'sum'), u=('util_ha', 'sum')).iterrows():
    print('    B%-3s bruta %6.1f  cañada %5.1f  UTIL %6.1f ha' % (b, r['g'], r['c'], r['u']))
print('  Top 6 con mas cañada:')
for _, r in tab.sort_values('canada_%', ascending=False).head(6).iterrows():
    print('    %-16s B%-3s %5.1f ha  cañada %4.1f (%4.1f%%)  UTIL %5.1f' % (r['lote_id'], r['bloque'], r['gross_ha'], r['canada_ha'], r['canada_%'], r['util_ha']))
print('DONE')
