# -*- coding: utf-8 -*-
"""Area Cerro Alto (grande): compuesto MEDIANA estacion seca + s2cloudless.
Paso 1: solo PNG quicklook para verificar limpieza antes del GeoTIFF."""
import ee, urllib.request, os
ee.Initialize()

GAMMA = 1.10
SHARP = 0.60
CLD_PRB_THRESH = 35
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
PNG_OUT = os.path.join(DESKTOP, 'AreaSerroAlto_S2_dryseason_clean_PREVIEW.png')

coords = [
    [-59.09980870205587, -18.58884954766944],
    [-58.60695261617405, -18.66991438639186],
    [-58.63656056535330, -18.23813443214794],
    [-59.15746155706938, -18.21358493934918],
    [-59.09980870205587, -18.58884954766944],
]
aoi = ee.Geometry.Polygon([coords])
print('AOI area: %.0f ha (%.0f km2)' % (aoi.area(1).divide(1e4).getInfo(), aoi.area(1).divide(1e6).getInfo()))

# coleccion estacion seca (May-Sep) del ultimo ~ano + s2cloudless
s2sr = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi)
        .filterDate('2025-05-01', '2026-06-25')
        .filter(ee.Filter.calendarRange(5, 9, 'month')))
s2cl = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi)
        .filterDate('2025-05-01', '2026-06-25')
        .filter(ee.Filter.calendarRange(5, 9, 'month')))
joined = ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(
    primary=s2sr, secondary=s2cl,
    condition=ee.Filter.equals(leftField='system:index', rightField='system:index')))
print('Imagenes estacion seca:', joined.size().getInfo())

def mask_img(img):
    prb = ee.Image(img.get('s2cloudless')).select('probability')
    scl = img.select('SCL')
    bad = prb.gt(CLD_PRB_THRESH).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(1)).Or(scl.eq(0))
    return img.updateMask(bad.Not())   # sin focalMax: la mediana limpia residuales

comp = joined.map(mask_img).select(['B4', 'B3', 'B2']).median().clip(aoi)

cov = comp.select('B4').mask().rename('v').reduceRegion(
    ee.Reducer.mean(), aoi, 80, maxPixels=1e10, bestEffort=True).get('v').getInfo() * 100
print('Cobertura compuesto: %.2f%%' % cov)

rgb = comp.toFloat()
pct = rgb.reduceRegion(ee.Reducer.percentile([2, 98]), aoi, 60, maxPixels=1e10, bestEffort=True).getInfo()
mins = [pct['B4_p2'], pct['B3_p2'], pct['B2_p2']]; maxs = [pct['B4_p98'], pct['B3_p98'], pct['B2_p98']]
print('Estiramiento min:', [round(m) for m in mins], 'max:', [round(m) for m in maxs])
minI = ee.Image.constant(mins).rename(['B4', 'B3', 'B2']); maxI = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minI).divide(maxI.subtract(minI)).clamp(0, 1).pow(1.0 / GAMMA)
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
final = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1).multiply(255).toByte()

ok = False
for dim in (1280, 1000, 768):
    try:
        u = final.getThumbURL({'region': aoi, 'dimensions': dim, 'format': 'png', 'min': 0, 'max': 255})
        urllib.request.urlretrieve(u, PNG_OUT)
        print('PNG:', PNG_OUT, '(%.1f KB) @ %dpx' % (os.path.getsize(PNG_OUT) / 1024, dim))
        ok = True
        break
    except Exception as e:
        print('  thumb %dpx fallo: %s' % (dim, repr(e)[:80]))
print('DONE' if ok else 'FALLO_PNG')
