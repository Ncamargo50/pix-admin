# -*- coding: utf-8 -*-
"""BLOQUE 14 — extraccion GEE para RE-HACER AMBIENTES con textura de suelo.

Genera 2 capas nuevas (topografia/hidro se reusan de _analisis_canadas):
  A) veg_summer.tif  -> vigor CULTIVO DE VERANO (Nov-Mar) 2024/25 + 2025/26
                        bandas: ndvi (mediana), ndvi_std (estabilidad), ndre (mediana)
  B) soil_bare.tif   -> compuesto SUELO DESNUDO (SIN cultivo) multi-fecha
                        bandas: B2,B3,B4,B8,B11,B12 (mediana bare) + bare_count
       Bare pixel = NDVI < 0.22  Y  NBR2 < 0.10 (excluye rastrojo/paja)  Y  cloud-free
       -> textura (arcilla), materia organica (brillo) y color (rojo/negro) SOLO de suelo.
"""
import os, sys, time, urllib.request, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ee
ee.Initialize()

OUT = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\_analisis_canadas\AMBIENTES_V2'
os.makedirs(OUT, exist_ok=True)
CRS = 'EPSG:31981'; SCALE = 10

# --- ROI: bbox Bloque 14 (4326) + buffer 330 m ---
b14 = ee.FeatureCollection(ee.Geometry.Rectangle([-59.0434, -18.2809, -59.0092, -18.2311]))
roi = b14.geometry().buffer(330)

# --- Cloud Score+ (estado del arte para mascara de nubes S2) ---
csp = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
CS_BAND = 'cs_cdf'; CLEAR = 0.60

def prep(img):
    img = img.linkCollection(csp, [CS_BAND])
    clear = img.select(CS_BAND).gte(CLEAR)
    sr = img.select(['B2','B3','B4','B5','B8','B8A','B11','B12']).divide(10000)
    return sr.updateMask(clear).copyProperties(img, ['system:time_start'])

def s2(d0, d1):
    return (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(roi).filterDate(d0, d1)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 80))
            .map(prep))

# ============ A) VIGOR CULTIVO DE VERANO (Nov-Mar 24/25 + 25/26) ============
def add_veg(img):
    ndvi = img.normalizedDifference(['B8','B4']).rename('ndvi')
    ndre = img.normalizedDifference(['B8','B5']).rename('ndre')
    return img.addBands([ndvi, ndre])

summer = (s2('2024-11-01','2025-03-31').merge(s2('2025-11-01','2026-03-31'))).map(add_veg)
n_sum = summer.size().getInfo()
veg = (summer.select('ndvi').median().rename('ndvi')
       .addBands(summer.select('ndvi').reduce(ee.Reducer.stdDev()).rename('ndvi_std'))
       .addBands(summer.select('ndre').median().rename('ndre')))

# ============ B) SUELO DESNUDO — SOLO PIXELES SIN CULTIVO, ESTACION SECA ============
# I1 auditoria: se restringe a ESTACION SECA (may-sep) para evitar mezclar humedad
# entre fechas (suelo humedo post-cosecha enrojece/oscurece distinto) -> redness/color
# reflejan mineralogia y no humedad. Solo pixeles bare (sin vegetacion ni rastrojo).
allc = s2('2022-01-01','2026-07-01').filter(ee.Filter.calendarRange(5, 9, 'month'))
def bare_mask(img):
    ndvi = img.normalizedDifference(['B8','B4'])
    nbr2 = img.normalizedDifference(['B11','B12'])           # rastrojo/paja alto
    bare = ndvi.lt(0.22).And(nbr2.lt(0.10))                  # SIN cultivo NI residuo
    return img.updateMask(bare)
bare = allc.map(bare_mask)
BB = ['B2','B3','B4','B8','B11','B12']
soil = bare.select(BB).median().rename(BB)
bare_count = bare.select('B4').count().rename('bare_count')
soil = soil.addBands(bare_count)
n_bare_scenes = allc.size().getInfo()

# ============ DESCARGA ============
def download(image, bands, fname):
    url = image.select(bands).clip(roi).getDownloadURL({
        'bands': bands, 'region': roi, 'scale': SCALE, 'crs': CRS, 'format': 'GEO_TIFF'})
    dst = os.path.join(OUT, fname)
    urllib.request.urlretrieve(url, dst)
    mb = os.path.getsize(dst)/1e6
    print('  %-18s %.2f MB' % (fname, mb))
    return dst

print('Escenas verano (Nov-Mar 24/25+25/26):', n_sum)
print('Escenas archivo p/ suelo desnudo     :', n_bare_scenes)
print('Descargando...')
download(veg,  ['ndvi','ndvi_std','ndre'], 'veg_summer.tif')
download(soil, BB + ['bare_count'],        'soil_bare.tif')

# RGB natural del compuesto de SUELO DESNUDO (validacion visual: sin cultivos)
download(soil, ['B4','B3','B2'], 'soil_bare_rgb.tif')
print('DONE extract')
