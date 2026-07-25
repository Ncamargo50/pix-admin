# -*- coding: utf-8 -*-
"""Color natural optimizado + realce de Serro Alto (Sentinel-2 SR Harmonized).
Genera PNG de alta resolucion (descarga directa) y lanza export GeoTIFF a Drive."""
import ee, urllib.request, os
ee.Initialize()

# ---------------- Parametros ----------------
DATE   = '2026-06-02'      # fecha objetivo (mas reciente <10% nubes en AOI)
NEXT   = '2026-06-03'      # fin (exclusivo)
GAMMA  = 1.10              # realce de medios tonos (natural)
SHARP  = 0.65             # intensidad unsharp mask
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
PNG_OUT = os.path.join(DESKTOP, 'SerroAlto_S2_%s_natural.png' % DATE.replace('-', ''))

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

# ---------------- Mosaico de la fecha ----------------
col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
       .filterBounds(aoi).filterDate(DATE, NEXT))
print('Imagenes %s:' % DATE, col.size().getInfo(),
      '| plataformas:', col.aggregate_array('SPACECRAFT_NAME').distinct().getInfo())

mosaic = col.mosaic().clip(aoi)
rgb = mosaic.select(['B4', 'B3', 'B2']).toFloat()   # rojo, verde, azul

# ---------------- Estiramiento por percentiles (2-98) en el AOI ----------------
pct = rgb.reduceRegion(ee.Reducer.percentile([2, 98]), aoi, 20,
                       maxPixels=1e9, bestEffort=True).getInfo()
mins = [pct['B4_p2'],  pct['B3_p2'],  pct['B2_p2']]
maxs = [pct['B4_p98'], pct['B3_p98'], pct['B2_p98']]
print('Estiramiento min:', [round(m) for m in mins], ' max:', [round(m) for m in maxs])

minImg = ee.Image.constant(mins).rename(['B4', 'B3', 'B2'])
maxImg = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minImg).divide(maxImg.subtract(minImg)).clamp(0, 1)
scaled = scaled.pow(1.0 / GAMMA)                    # correccion gamma

# ---------------- Realce de nitidez (unsharp mask) ----------------
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
sharp = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1)
final = sharp.multiply(255).toByte()                # 3 bandas 8-bit RGB

# ---------------- PNG alta resolucion (descarga directa) ----------------
url = final.getThumbURL({'region': aoi, 'dimensions': 3000,
                         'format': 'png', 'min': 0, 'max': 255})
print('Descargando PNG...')
urllib.request.urlretrieve(url, PNG_OUT)
print('PNG guardado:', PNG_OUT, '(%.1f KB)' % (os.path.getsize(PNG_OUT) / 1024))

# ---------------- Export GeoTIFF 10m a Google Drive ----------------
task = ee.batch.Export.image.toDrive(
    image=final, description='SerroAlto_S2_%s_natural' % DATE.replace('-', ''),
    folder='Pixadvisor_GEE', fileNamePrefix='SerroAlto_S2_%s_natural' % DATE.replace('-', ''),
    region=aoi, scale=10, crs='EPSG:32720', maxPixels=1e10, fileFormat='GeoTIFF')
task.start()
print('Export GeoTIFF lanzado -> Drive/Pixadvisor_GEE | task id:', task.id, '| estado:', task.status().get('state'))
