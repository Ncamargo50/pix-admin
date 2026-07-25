# -*- coding: utf-8 -*-
"""Serro_Alto-2: tabla de fechas recientes + compuesto SIN NUBES color natural
optimizado (pixel valido mas reciente). Salida PNG + GeoTIFF 10m."""
import ee, urllib.request, os, zipfile, tempfile
import rasterio
from rasterio.merge import merge
ee.Initialize()

TAG    = 'SerroAlto2'
GAMMA  = 1.10
SHARP  = 0.65
NX, NY = 2, 3
WIN0, WIN1 = '2026-05-05', '2026-06-25'      # ventana compuesto (hasta hoy)
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')

coords = [
    [-58.83555739302057, -18.61202609582531],
    [-58.71429052653912, -18.55657971606611],
    [-58.71563995649949, -18.39154797018091],
    [-58.95664619212703, -18.29505258166455],
    [-58.83555739302057, -18.61202609582531],
]
aoi = ee.Geometry.Polygon([coords])
print('AOI area: %.1f ha (%.1f km2)' % (aoi.area(1).divide(1e4).getInfo(),
                                        aoi.area(1).divide(1e6).getInfo()))

# ---------- tabla de fechas (ultimos ~75 dias) DENTRO del AOI ----------
diag = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi)
        .filterDate('2026-04-10', '2026-06-25')
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60))
        .map(lambda im: im.set('date', im.date().format('YYYY-MM-dd'))))
dates = diag.aggregate_array('date').distinct().sort()
def per_date(d):
    d = ee.String(d); day = diag.filter(ee.Filter.eq('date', d)); m = day.mosaic().select('SCL')
    cloud = m.eq(3).Or(m.gte(8)); valid = m.gt(0).rename('v')
    tot = ee.Image.constant(1).rename('c').clip(aoi).reduceRegion(ee.Reducer.count(), aoi, 100, maxPixels=1e9, bestEffort=True).get('c')
    val = valid.reduceRegion(ee.Reducer.sum(), aoi, 100, maxPixels=1e9, bestEffort=True).get('v')
    cld = cloud.rename('cl').reduceRegion(ee.Reducer.sum(), aoi, 100, maxPixels=1e9, bestEffort=True).get('cl')
    return ee.Feature(None, {'date': d, 'tot': tot, 'val': val, 'cld': cld,
                             'plats': day.aggregate_array('SPACECRAFT_NAME').distinct()})
rows = []
for f in ee.FeatureCollection(dates.map(per_date)).getInfo()['features']:
    p = f['properties']; tot = p.get('tot') or 0; val = p.get('val') or 0; cld = p.get('cld') or 0
    cov = val/tot*100 if tot else 0; cpct = cld/val*100 if val else 100
    rows.append((p['date'], cov, cpct, ','.join(p.get('plats', []))))
rows.sort(reverse=True)
print('\n%-12s %8s %7s  %s' % ('FECHA', 'COBERT%', 'NUBE%', 'PLATAFORMA'))
print('-'*52)
for r in rows:
    flag = '  <== CLARA' if (r[1] >= 95 and r[2] < 10) else ''
    print('%-12s %7.1f%% %6.1f%%  %-14s%s' % (r[0], r[1], r[2], r[3], flag))

# ---------- compuesto sin nubes ----------
def mask_s2(img):
    scl = img.select('SCL'); cloud = scl.eq(3).Or(scl.gte(8))
    cloud = cloud.focalMax(radius=2, kernelType='circle', units='pixels')
    return img.updateMask(cloud.Not().And(scl.gt(0)))
recent = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi)
          .filterDate(WIN0, WIN1).map(mask_s2).sort('system:time_start'))
comp = recent.mosaic().clip(aoi)
# fecha mas reciente que aporta pixel valido
dband = recent.map(lambda im: im.metadata('system:time_start').rename('dt')
                   .updateMask(im.select('B4').mask())).max()
fresh = dband.reduceRegion(ee.Reducer.max(), aoi, 60, maxPixels=1e9, bestEffort=True).get('dt')
fresh = ee.Date(fresh).format('YYYY-MM-dd').getInfo()
print('\nFecha mas reciente aportante:', fresh)
PNG_OUT = os.path.join(DESKTOP, '%s_S2_%s_cloudfree.png' % (TAG, fresh.replace('-', '')))
TIF_OUT = os.path.join(DESKTOP, '%s_S2_%s_cloudfree.tif' % (TAG, fresh.replace('-', '')))

sclc = comp.select('SCL'); cloud_c = sclc.eq(3).Or(sclc.gte(8)); valid_c = sclc.gt(0).rename('v')
tot = ee.Image.constant(1).rename('c').clip(aoi).reduceRegion(ee.Reducer.count(), aoi, 100, maxPixels=1e9, bestEffort=True).get('c')
val = valid_c.reduceRegion(ee.Reducer.sum(), aoi, 100, maxPixels=1e9, bestEffort=True).get('v')
cld = cloud_c.rename('cl').reduceRegion(ee.Reducer.sum(), aoi, 100, maxPixels=1e9, bestEffort=True).get('cl')
st = ee.Dictionary({'tot': tot, 'val': val, 'cld': cld}).getInfo()
print('Compuesto -> cobertura: %.2f%% | nube residual: %.2f%%' %
      (st['val']/st['tot']*100, (st['cld'] or 0)/st['val']*100))

rgb = comp.select(['B4', 'B3', 'B2']).toFloat()
pct = rgb.reduceRegion(ee.Reducer.percentile([2, 98]), aoi, 20, maxPixels=1e9, bestEffort=True).getInfo()
mins = [pct['B4_p2'], pct['B3_p2'], pct['B2_p2']]; maxs = [pct['B4_p98'], pct['B3_p98'], pct['B2_p98']]
minImg = ee.Image.constant(mins).rename(['B4', 'B3', 'B2']); maxImg = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minImg).divide(maxImg.subtract(minImg)).clamp(0, 1).pow(1.0/GAMMA)
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
final = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1).multiply(255).toByte()

urllib.request.urlretrieve(final.getThumbURL({'region': aoi, 'dimensions': 3000, 'format': 'png', 'min': 0, 'max': 255}), PNG_OUT)
print('PNG:', PNG_OUT, '(%.1f KB)' % (os.path.getsize(PNG_OUT)/1024))

lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
x0, x1 = min(lons), max(lons); y0, y1 = min(lats), max(lats); dx = (x1-x0)/NX; dy = (y1-y0)/NY
tmp = tempfile.mkdtemp(prefix='sa2_'); tiles = []
for i in range(NX):
    for j in range(NY):
        rect = ee.Geometry.Rectangle([x0+i*dx, y0+j*dy, x0+(i+1)*dx, y0+(j+1)*dy])
        u = final.getDownloadURL({'region': rect, 'scale': 10, 'crs': 'EPSG:32720', 'format': 'GEO_TIFF'})
        d = os.path.join(tmp, 't_%d_%d.tif' % (i, j)); urllib.request.urlretrieve(u, d)
        with open(d, 'rb') as fh:
            isz = fh.read(2) == b'PK'
        if isz:
            with zipfile.ZipFile(d) as zf:
                n = [x for x in zf.namelist() if x.lower().endswith('.tif')][0]; data = zf.read(n)
            with open(d, 'wb') as fo:
                fo.write(data)
        tiles.append(d)
srcs = [rasterio.open(t) for t in tiles]; mos, tr = merge(srcs); meta = srcs[0].meta.copy()
meta.update({'height': mos.shape[1], 'width': mos.shape[2], 'count': mos.shape[0], 'transform': tr,
             'compress': 'LZW', 'photometric': 'RGB', 'nodata': 0})
with rasterio.open(TIF_OUT, 'w', **meta) as o:
    o.write(mos)
for s in srcs:
    s.close()
with rasterio.open(TIF_OUT) as r:
    print('GeoTIFF:', TIF_OUT, '| %.1f MB | %dx%d | %s | 10m' % (os.path.getsize(TIF_OUT)/1e6, r.width, r.height, r.crs))
