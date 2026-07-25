# -*- coding: utf-8 -*-
"""Cerro Alto cañadas v2 — terreno-drenaje (TPI GLO-30 + HAND) corroborado con
vegetacion riparia (NDVI sobre fondo local). Validacion + area util por lote."""
import ee, json, os, urllib.request
import geopandas as gpd, pandas as pd
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

LOT = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\Lotes_SerroAlto_Muestreo_Soya_26-27.geojson'
OUTDIR = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\_analisis_canadas'

gdf = gpd.read_file(LOT).to_crs(4326)
fcs = ee.FeatureCollection(json.loads(gdf[['lote_id', 'geometry']].to_json()))
aoi = fcs.geometry().buffer(200)
outlineViz = ee.Image().byte().paint(fcs, 1, 1).selfMask().visualize(palette=['00e5ff'])

# --- TPI desde GLO-30 reproyectado a metrico (evita degeneracion) ---
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().reproject('EPSG:31981', None, 30).clip(aoi)
bg_dem = dem.reduceNeighborhood(ee.Reducer.mean(), ee.Kernel.circle(6, 'pixels'))   # ~180 m
tpi = dem.subtract(bg_dem).rename('tpi')
hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').clip(aoi)
upa = ee.Image('MERIT/Hydro/v1_0_1').select('upa').clip(aoi)

# --- NDVI seca + fondo local (riparia = mas densa que el entorno) ---
def cloudmask(img):
    p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
    return img.updateMask(p.gt(35).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1)).Not())
def join_s2(d0, d1, months=None):
    sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate(d0, d1)
    cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate(d0, d1)
    if months: sr = sr.filter(ee.Filter.calendarRange(*months, 'month')); cl = cl.filter(ee.Filter.calendarRange(*months, 'month'))
    return ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))).map(cloudmask)
dry = join_s2('2025-01-01', '2026-06-25', (5, 9)).median().clip(aoi)
ndvi = dry.normalizedDifference(['B8', 'B4']).rename('ndvi')
bg_ndvi = ndvi.focal_median(250, 'circle', 'meters')
ripar = ndvi.subtract(bg_ndvi).rename('ripar')   # >0 = mas verde que el entorno

for nm, im, sc in [('tpi', tpi, 30), ('hand', hand, 90), ('ripar', ripar, 10)]:
    s = im.reduceRegion(ee.Reducer.percentile([2, 50, 98]), aoi, sc, maxPixels=1e9, bestEffort=True).getInfo()
    print('  %-6s p2=%.3f p50=%.3f p98=%.3f' % (nm, list(s.values())[0], list(s.values())[1], list(s.values())[2]))

# --- mascara cañada: (valle TPI O HAND bajo) Y riparia ---
T_TPI, T_HAND, T_RIP = -0.4, 2.0, 0.06
terr = tpi.lt(T_TPI).Or(hand.lt(T_HAND))
canada = terr.And(ripar.gt(T_RIP)).selfMask()
canada = canada.updateMask(canada.connectedPixelCount(50, True).gte(4))

# --- validacion visual ---
tc = dry.select(['B4', 'B3', 'B2']).visualize(min=200, max=1500, gamma=1.1)
for nm, lay in [('8_TPI', tpi.visualize(min=-2, max=2, palette=['08306b', 'ffffff', '8c510a'])),
                ('9_VALIDACION_v2', tc.blend(canada.visualize(palette=['ff0000'])).blend(outlineViz))]:
    urllib.request.urlretrieve(lay.getThumbURL({'region': aoi, 'dimensions': 1500, 'format': 'png'}),
                               os.path.join(OUTDIR, nm + '.png')); print('panel ->', nm)

# --- area util por lote ---
areaImg = ee.Image.pixelArea()
gdf_m = gdf.to_crs(31981); gdf['gross_ha'] = (gdf_m.area / 1e4).values
rr = areaImg.updateMask(canada).rename('cab').reduceRegions(fcs, ee.Reducer.sum(), 10).getInfo()
rows = {}
for f in rr['features']:
    pr = f['properties']; rows[pr['lote_id']] = rows.get(pr['lote_id'], 0) + (pr.get('cab') or 0) / 1e4
df = pd.DataFrame([(k, v) for k, v in rows.items()], columns=['lote_id', 'canada_ha'])
df = gdf[['lote_id', 'bloque', 'gross_ha']].merge(df, on='lote_id', how='left').fillna(0)
df = df.groupby(['lote_id', 'bloque'], as_index=False).agg(gross_ha=('gross_ha', 'sum'), canada_ha=('canada_ha', 'sum'))
df['util_ha'] = (df['gross_ha'] - df['canada_ha']).clip(lower=0)
df['canada_%'] = (df['canada_ha'] / df['gross_ha'] * 100).round(1)
t = df[['gross_ha', 'canada_ha', 'util_ha']].sum()
print('\nTOTAL: bruta %.1f | cañada %.1f (%.1f%%) | UTIL %.1f ha' % (t['gross_ha'], t['canada_ha'], t['canada_ha']/t['gross_ha']*100, t['util_ha']))
print('Top 6 lotes con mas cañada:')
for _, r in df.sort_values('canada_%', ascending=False).head(6).iterrows():
    print('  %-16s B%-3s bruta %5.1f  cañada %4.1f (%4.1f%%)  UTIL %5.1f' % (r['lote_id'], r['bloque'], r['gross_ha'], r['canada_ha'], r['canada_%'], r['util_ha']))
df.sort_values(['bloque', 'lote_id']).to_csv(os.path.join(OUTDIR, 'area_util_v2.csv'), index=False, encoding='utf-8-sig')
print('DONE')
