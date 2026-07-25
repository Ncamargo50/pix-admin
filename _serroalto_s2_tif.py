# -*- coding: utf-8 -*-
"""Descarga directa del GeoTIFF (color natural optimizado) de Cerro Alto al Desktop."""
import ee, urllib.request, os, zipfile
ee.Initialize()

DATE   = '2026-06-02'
GAMMA  = 1.10
SHARP  = 0.65
# percentiles ya calculados en el render (para que el .tif sea identico al PNG)
mins = [179, 275, 149]
maxs = [1231, 1039, 782]
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
TIF_OUT = os.path.join(DESKTOP, 'SerroAlto_S2_%s_natural.tif' % DATE.replace('-', ''))

coords = [
    [-59.04149483287776, -18.43723058824241], [-59.04011845722908, -18.45517557079797],
    [-59.00326539886977, -18.50928508196885], [-58.96179223512260, -18.51120111104825],
    [-58.94609009832865, -18.56465899879865], [-58.87102796875345, -18.56262666144513],
    [-58.86294304580482, -18.59121509634033], [-58.84382519579287, -18.58752238332183],
    [-58.90961234071023, -18.38671128953329], [-58.92071589843120, -18.38565344568694],
    [-58.94160037845226, -18.33145963719488], [-58.96256446645500, -18.29907257354004],
    [-58.99661478895631, -18.24431724039563], [-59.02188311171686, -18.22257168677444],
    [-59.12269891433242, -18.35152023575153], [-59.12696267158442, -18.40247364203066],
    [-59.04149483287776, -18.43723058824241],
]
aoi = ee.Geometry.Polygon([coords])

col = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate(DATE, '2026-06-03')
rgb = col.mosaic().clip(aoi).select(['B4', 'B3', 'B2']).toFloat()

minImg = ee.Image.constant(mins).rename(['B4', 'B3', 'B2'])
maxImg = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minImg).divide(maxImg.subtract(minImg)).clamp(0, 1).pow(1.0 / GAMMA)
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
final = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1).multiply(255).toByte()

print('Solicitando GeoTIFF 10m (EPSG:32720)...')
try:
    url = final.getDownloadURL({'region': aoi, 'scale': 10, 'crs': 'EPSG:32720', 'format': 'GEO_TIFF'})
    tmp = TIF_OUT + '.part'
    urllib.request.urlretrieve(url, tmp)
    # algunos endpoints devuelven zip; detectar y extraer
    with open(tmp, 'rb') as fh:
        magic = fh.read(4)
    if magic[:2] == b'PK':
        with zipfile.ZipFile(tmp) as z:
            name = [n for n in z.namelist() if n.lower().endswith('.tif')][0]
            with z.open(name) as src, open(TIF_OUT, 'wb') as dst:
                dst.write(src.read())
        os.remove(tmp)
    else:
        os.replace(tmp, TIF_OUT)
    print('OK ->', TIF_OUT, '(%.1f MB)' % (os.path.getsize(TIF_OUT) / 1e6))
except Exception as e:
    print('FALLO descarga directa:', repr(e)[:300])
