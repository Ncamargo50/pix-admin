# -*- coding: utf-8 -*-
"""E1: features de vegetacion 3 años sin nubes para zonas de manejo.
NDVI mediana (vigor), NDRE mediana, NDVI std (estabilidad). Export 10m UTM31981."""
import ee, json, os, urllib.request, zipfile, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import geopandas as gpd
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
OUT = os.path.join(OUTDIR, 'zm_features_veg.tif')

gdf = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(4326)
aoi = ee.FeatureCollection(json.loads(gdf[['lote_id', 'geometry']].to_json())).geometry().buffer(150)

def cm(img):
    p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
    return img.updateMask(p.gt(40).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1)).Not())
sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate('2023-06-01', '2026-06-25')
cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate('2023-06-01', '2026-06-25')
col = ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl,
      condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))).map(cm)
print('imagenes 3 años:', col.size().getInfo())

def idx(img):
    ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndre = img.normalizedDifference(['B8', 'B5']).rename('NDRE')
    return img.addBands([ndvi, ndre])
col = col.map(idx)
ndvi_med = col.select('NDVI').median().rename('ndvi_med')
ndvi_std = col.select('NDVI').reduce(ee.Reducer.stdDev()).rename('ndvi_std')
ndre_med = col.select('NDRE').median().rename('ndre_med')
feat = ndvi_med.addBands(ndvi_std).addBands(ndre_med).clip(aoi).toFloat()

for b in ['ndvi_med', 'ndvi_std', 'ndre_med']:
    s = feat.select(b).reduceRegion(ee.Reducer.percentile([2, 50, 98]), aoi, 10, maxPixels=1e9, bestEffort=True).getInfo()
    print('  %-9s p2/p50/p98:' % b, [round(v, 3) for v in s.values()])

img = feat.reproject('EPSG:31981', None, 10)
url = img.getDownloadURL({'region': aoi, 'scale': 10, 'crs': 'EPSG:31981', 'format': 'GEO_TIFF'})
tmp = OUT + '.part'; urllib.request.urlretrieve(url, tmp)
with open(tmp, 'rb') as fh:
    z = fh.read(2) == b'PK'
if z:
    zf = zipfile.ZipFile(tmp); n = [x for x in zf.namelist() if x.lower().endswith('.tif')][0]; open(OUT, 'wb').write(zf.read(n)); os.remove(tmp)
else:
    os.replace(tmp, OUT)
print('features ->', os.path.basename(OUT), '%.1f MB' % (os.path.getsize(OUT)/1e6))
print('DONE')
