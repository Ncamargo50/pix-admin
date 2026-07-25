# -*- coding: utf-8 -*-
"""Compuesto SIN NUBES color natural optimizado de Serro Alto.
Mosaico 'pixel valido mas reciente' (1-may..2-jun) + estiramiento + unsharp.
Salida: PNG quicklook + GeoTIFF 10m (tiles + merge rasterio)."""
import ee, urllib.request, os, zipfile, tempfile
import rasterio
from rasterio.merge import merge
ee.Initialize()

BASE   = '20260602'
GAMMA  = 1.10
SHARP  = 0.65
NX, NY = 2, 3
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
PNG_OUT = os.path.join(DESKTOP, 'SerroAlto_S2_%s_cloudfree.png' % BASE)
TIF_OUT = os.path.join(DESKTOP, 'SerroAlto_S2_%s_cloudfree.tif' % BASE)

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

def mask_s2(img):
    scl = img.select('SCL')
    cloud = scl.eq(3).Or(scl.gte(8))                 # sombra + nube + cirrus
    cloud = cloud.focalMax(radius=2, kernelType='circle', units='pixels')  # come bordes
    good = cloud.Not().And(scl.gt(0))
    return img.updateMask(good)

recent = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterBounds(aoi).filterDate('2026-05-01', '2026-06-03')
          .map(mask_s2).sort('system:time_start'))       # ascendente: ultima = mas reciente
print('Pasadas usadas:', recent.size().getInfo(),
      '| fechas:', recent.aggregate_array('system:time_start')
      .map(lambda t: ee.Date(t).format('YYYY-MM-dd')).distinct().getInfo())

comp = recent.mosaic().clip(aoi)

# --- validacion: cobertura y nube residual del compuesto ---
sclc = comp.select('SCL')
cloud_c = sclc.eq(3).Or(sclc.gte(8))
valid_c = sclc.gt(0).rename('v')
tot = ee.Image.constant(1).rename('c').clip(aoi).reduceRegion(ee.Reducer.count(), aoi, 100, maxPixels=1e9, bestEffort=True).get('c')
val = valid_c.reduceRegion(ee.Reducer.sum(), aoi, 100, maxPixels=1e9, bestEffort=True).get('v')
cld = cloud_c.rename('cl').reduceRegion(ee.Reducer.sum(), aoi, 100, maxPixels=1e9, bestEffort=True).get('cl')
stats = ee.Dictionary({'tot': tot, 'val': val, 'cld': cld}).getInfo()
cov = stats['val']/stats['tot']*100; cpct = (stats['cld'] or 0)/stats['val']*100
print('Compuesto -> cobertura: %.2f%% | nube residual: %.2f%%' % (cov, cpct))

# --- color natural optimizado ---
rgb = comp.select(['B4', 'B3', 'B2']).toFloat()
pct = rgb.reduceRegion(ee.Reducer.percentile([2, 98]), aoi, 20, maxPixels=1e9, bestEffort=True).getInfo()
mins = [pct['B4_p2'],  pct['B3_p2'],  pct['B2_p2']]
maxs = [pct['B4_p98'], pct['B3_p98'], pct['B2_p98']]
print('Estiramiento min:', [round(m) for m in mins], 'max:', [round(m) for m in maxs])
minImg = ee.Image.constant(mins).rename(['B4', 'B3', 'B2'])
maxImg = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minImg).divide(maxImg.subtract(minImg)).clamp(0, 1).pow(1.0/GAMMA)
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
final = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1).multiply(255).toByte()

# --- PNG quicklook ---
url = final.getThumbURL({'region': aoi, 'dimensions': 3000, 'format': 'png', 'min': 0, 'max': 255})
urllib.request.urlretrieve(url, PNG_OUT)
print('PNG:', PNG_OUT, '(%.1f KB)' % (os.path.getsize(PNG_OUT)/1024))

# --- GeoTIFF por tiles + merge ---
lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
x0, x1 = min(lons), max(lons); y0, y1 = min(lats), max(lats)
dx = (x1-x0)/NX; dy = (y1-y0)/NY
tmp = tempfile.mkdtemp(prefix='sacf_'); tiles = []
for i in range(NX):
    for j in range(NY):
        rect = ee.Geometry.Rectangle([x0+i*dx, y0+j*dy, x0+(i+1)*dx, y0+(j+1)*dy])
        u = final.getDownloadURL({'region': rect, 'scale': 10, 'crs': 'EPSG:32720', 'format': 'GEO_TIFF'})
        d = os.path.join(tmp, 't_%d_%d.tif' % (i, j)); urllib.request.urlretrieve(u, d)
        with open(d, 'rb') as fh:
            z = fh.read(2) == b'PK'
        if z:
            with zipfile.ZipFile(d) as zf:
                n = [x for x in zf.namelist() if x.lower().endswith('.tif')][0]; data = zf.read(n)
            with open(d, 'wb') as fo:
                fo.write(data)
        tiles.append(d)
srcs = [rasterio.open(t) for t in tiles]
mos, tr = merge(srcs)
meta = srcs[0].meta.copy()
meta.update({'height': mos.shape[1], 'width': mos.shape[2], 'count': mos.shape[0],
             'transform': tr, 'compress': 'LZW', 'photometric': 'RGB', 'nodata': 0})
with rasterio.open(TIF_OUT, 'w', **meta) as o:
    o.write(mos)
for s in srcs:
    s.close()
with rasterio.open(TIF_OUT) as r:
    print('GeoTIFF:', TIF_OUT, '| %.1f MB | %dx%d | %s | 10m' %
          (os.path.getsize(TIF_OUT)/1e6, r.width, r.height, r.crs))
