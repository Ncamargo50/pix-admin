# -*- coding: utf-8 -*-
"""Paneles visuales corregidos + capa clave NDVI-p10 (vegetacion permanente)."""
import ee, json, os, urllib.request
import geopandas as gpd
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

LOT = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\Lotes_SerroAlto_Muestreo_Soya_26-27.geojson'
OUTDIR = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\_analisis_canadas'
os.makedirs(OUTDIR, exist_ok=True)

gdf = gpd.read_file(LOT).to_crs(4326); gdf['geometry'] = gdf.simplify(0.00002)
fc = ee.FeatureCollection(json.loads(gdf.to_json()))
aoi = fc.geometry().buffer(200)
outlineViz = ee.Image().byte().paint(fc, 1, 1).selfMask().visualize(palette=['ffff00'])

def cloudmask(img):
    p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
    bad = p.gt(35).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1))
    return img.updateMask(bad.Not())

def join_s2(d0, d1, months=None):
    sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate(d0, d1)
    cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate(d0, d1)
    if months: sr = sr.filter(ee.Filter.calendarRange(*months, 'month')); cl = cl.filter(ee.Filter.calendarRange(*months, 'month'))
    return ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))).map(cloudmask)

dry = join_s2('2025-01-01', '2026-06-25', (5, 9)).median().clip(aoi)
# NDVI percentil 10 sobre 2 anos = verdor permanente (cañada/bosque nunca se pela)
ndvi_p10 = join_s2('2024-06-01', '2026-06-25').map(
    lambda im: im.normalizedDifference(['B8', 'B4']).rename('NDVI')).reduce(ee.Reducer.percentile([10])).clip(aoi).rename('NDVI_p10')
s = ndvi_p10.reduceRegion(ee.Reducer.minMax().combine(ee.Reducer.mean(), sharedInputs=True), aoi, 10, maxPixels=1e9, bestEffort=True).getInfo()
print('NDVI_p10  min=%.3f max=%.3f mean=%.3f' % (s['NDVI_p10_min'], s['NDVI_p10_max'], s['NDVI_p10_mean']))

ndvi_dry = dry.normalizedDifference(['B8', 'B4']).rename('NDVI_dry')
merit = ee.Image('MERIT/Hydro/v1_0_1').clip(aoi)
hnd = merit.select('hnd'); upa = merit.select('upa')
s1 = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(aoi).filter(ee.Filter.eq('instrumentMode', 'IW'))
      .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).select('VV')
      .filter(ee.Filter.calendarRange(5, 9, 'month')).filterDate('2025-01-01', '2026-06-25')).median().clip(aoi).focal_median(30, 'circle', 'meters')

def panel(viz3, fname, dim=1300):
    comp = viz3.blend(outlineViz)
    url = comp.getThumbURL({'region': aoi, 'dimensions': dim, 'format': 'png'})
    p = os.path.join(OUTDIR, fname); urllib.request.urlretrieve(url, p); print('panel ->', fname)

panel(dry.select(['B4', 'B3', 'B2']).visualize(min=200, max=1500, gamma=1.1), '1_truecolor.png')
panel(ndvi_p10.visualize(min=0.1, max=0.7, palette=['ffffff', 'fee08b', '66bd63', '006837']), '2_NDVIp10_permveg.png')
panel(ndvi_dry.visualize(min=0.1, max=0.7, palette=['ffffff', 'fee08b', '66bd63', '006837']), '3_NDVIdry.png')
panel(hnd.visualize(min=0, max=10, palette=['08306b', '4292c6', 'fdae61', 'fee08b']), '4_HAND.png')
panel(upa.log10().visualize(min=-2, max=2, palette=['ffffff', '9ecae1', '2171b5', '08306b']), '5_flowacc_log.png')
panel(s1.visualize(min=-18, max=-6, palette=['000000', 'ffffff']), '6_S1_VV.png')
print('DONE')
