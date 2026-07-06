# -*- coding: utf-8 -*-
"""SERRO ALTO (HACIENDA COMPLETA) — extraccion GEE metodologia v2.1 validada.
veg_summer_full: vigor soya verano Nov-Mar 24/25+25/26 (ndvi, ndvi_std, ndre).
soil_bare_full : suelo desnudo SIN cultivo, ESTACION SECA (may-sep) — B2..B12 + bare_count.
Topografia/hidro/RGB se reusan (ya cubren la hacienda)."""
import os, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ee
ee.Initialize()

OUT = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\_analisis_canadas\AMBIENTES_V2'
os.makedirs(OUT, exist_ok=True)
CRS = 'EPSG:31981'; SCALE = 10
# bbox HACIENDA COMPLETA (B2+B3+B14) + buffer 400 m
roi = ee.Geometry.Rectangle([-59.0434, -18.3178, -58.9715, -18.2311]).buffer(400)

csp = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED'); CS_BAND = 'cs_cdf'; CLEAR = 0.60
def prep(img):
    clear = img.linkCollection(csp, [CS_BAND]).select(CS_BAND).gte(CLEAR)
    sr = img.select(['B2','B3','B4','B5','B8','B8A','B11','B12']).divide(10000)
    return sr.updateMask(clear).copyProperties(img, ['system:time_start'])
def s2(d0, d1):
    return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(roi).filterDate(d0, d1)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 80)).map(prep))

# A) vigor verano
def add_veg(img):
    return img.addBands([img.normalizedDifference(['B8','B4']).rename('ndvi'),
                         img.normalizedDifference(['B8','B5']).rename('ndre')])
summer = (s2('2024-11-01','2025-03-31').merge(s2('2025-11-01','2026-03-31'))).map(add_veg)
veg = (summer.select('ndvi').median().rename('ndvi')
       .addBands(summer.select('ndvi').reduce(ee.Reducer.stdDev()).rename('ndvi_std'))
       .addBands(summer.select('ndre').median().rename('ndre')))

# B) suelo desnudo estacion seca (sin cultivo ni rastrojo)
allc = s2('2022-01-01','2026-07-01').filter(ee.Filter.calendarRange(5, 9, 'month'))
def bare_mask(img):
    bare = img.normalizedDifference(['B8','B4']).lt(0.22).And(img.normalizedDifference(['B11','B12']).lt(0.10))
    return img.updateMask(bare)
bare = allc.map(bare_mask); BB = ['B2','B3','B4','B8','B11','B12']
soil = bare.select(BB).median().rename(BB).addBands(bare.select('B4').count().rename('bare_count'))

def download(image, bands, fname):
    url = image.select(bands).clip(roi).getDownloadURL({'bands': bands, 'region': roi, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'})
    dst = os.path.join(OUT, fname); urllib.request.urlretrieve(url, dst)
    print('  %-22s %.2f MB' % (fname, os.path.getsize(dst)/1e6)); return dst

print('Escenas verano:', summer.size().getInfo(), '| escenas suelo seco:', allc.size().getInfo())
download(veg,  ['ndvi','ndvi_std','ndre'], 'veg_summer_full.tif')
download(soil, BB + ['bare_count'],        'soil_bare_full.tif')
print('DONE extract full')
