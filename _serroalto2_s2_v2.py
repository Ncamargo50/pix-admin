# -*- coding: utf-8 -*-
"""Serro_Alto-2 v2: compuesto LIMPIO con enmascarado s2cloudless (prob nube +
sombra proyectada + buffer). Mosaico pixel valido mas reciente. PNG + GeoTIFF."""
import ee, urllib.request, os, zipfile, tempfile
import rasterio
from rasterio.merge import merge
ee.Initialize()

TAG    = 'SerroAlto2'
GAMMA  = 1.10
SHARP  = 0.65
NX, NY = 2, 3
START, END = '2026-05-01', '2026-06-25'
CLD_PRB_THRESH = 30      # probabilidad s2cloudless (%) -> nube
NIR_DRK_THRESH = 0.15    # B8 < esto -> pixel oscuro (candidato sombra)
CLD_PRJ_DIST   = 2       # distancia proyeccion sombra
BUFFER_M       = 60      # dilatacion mascara (m)
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')

coords = [
    [-58.83555739302057, -18.61202609582531],
    [-58.71429052653912, -18.55657971606611],
    [-58.71563995649949, -18.39154797018091],
    [-58.95664619212703, -18.29505258166455],
    [-58.83555739302057, -18.61202609582531],
]
aoi = ee.Geometry.Polygon([coords])

s2sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate(START, END)
s2cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate(START, END)
joined = ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(
    primary=s2sr, secondary=s2cl,
    condition=ee.Filter.equals(leftField='system:index', rightField='system:index')))
print('Imagenes en ventana:', joined.size().getInfo())

def add_cld_shdw(img):
    prb = ee.Image(img.get('s2cloudless')).select('probability')
    is_cloud = prb.gt(CLD_PRB_THRESH).rename('clouds')
    not_water = img.select('SCL').neq(6)
    dark = img.select('B8').lt(NIR_DRK_THRESH * 1e4).multiply(not_water)
    saz = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')))
    proj = (is_cloud.directionalDistanceTransform(saz, CLD_PRJ_DIST * 10)
            .reproject(crs=img.select(0).projection(), scale=100)
            .select('distance').mask())
    shadows = proj.multiply(dark).rename('shadows')
    cld_shdw = is_cloud.add(shadows).gt(0)
    cld_shdw = (cld_shdw.focalMin(2).focalMax(int(BUFFER_M * 2 / 20))
                .reproject(crs=img.select(0).projection(), scale=20).rename('cloudmask'))
    return img.addBands(cld_shdw)

def apply_mask(img):
    return img.updateMask(img.select('cloudmask').Not())

coll = joined.map(add_cld_shdw).map(apply_mask).sort('system:time_start')
comp = coll.mosaic().clip(aoi)

# cobertura + fecha mas reciente aportante
valmask = comp.select('B4').mask().rename('v')
cov = valmask.reduceRegion(ee.Reducer.mean(), aoi, 60, maxPixels=1e9, bestEffort=True).get('v').getInfo() * 100
dband = coll.map(lambda im: im.metadata('system:time_start').rename('dt')
                 .updateMask(im.select('B4').mask())).max()
fresh = ee.Date(dband.reduceRegion(ee.Reducer.max(), aoi, 60, maxPixels=1e9, bestEffort=True).get('dt')).format('YYYY-MM-dd').getInfo()
print('Cobertura: %.2f%% | fecha mas reciente aportante: %s' % (cov, fresh))
PNG_OUT = os.path.join(DESKTOP, '%s_S2_%s_clean.png' % (TAG, fresh.replace('-', '')))
TIF_OUT = os.path.join(DESKTOP, '%s_S2_%s_clean.tif' % (TAG, fresh.replace('-', '')))

# color natural optimizado
rgb = comp.select(['B4', 'B3', 'B2']).toFloat()
pct = rgb.reduceRegion(ee.Reducer.percentile([2, 98]), aoi, 20, maxPixels=1e9, bestEffort=True).getInfo()
mins = [pct['B4_p2'], pct['B3_p2'], pct['B2_p2']]; maxs = [pct['B4_p98'], pct['B3_p98'], pct['B2_p98']]
minI = ee.Image.constant(mins).rename(['B4', 'B3', 'B2']); maxI = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minI).divide(maxI.subtract(minI)).clamp(0, 1).pow(1.0 / GAMMA)
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
final = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1).multiply(255).toByte()

urllib.request.urlretrieve(final.getThumbURL({'region': aoi, 'dimensions': 3000, 'format': 'png', 'min': 0, 'max': 255}), PNG_OUT)
print('PNG:', PNG_OUT, '(%.1f KB)' % (os.path.getsize(PNG_OUT) / 1024))

lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
x0, x1 = min(lons), max(lons); y0, y1 = min(lats), max(lats); dx = (x1 - x0) / NX; dy = (y1 - y0) / NY
tmp = tempfile.mkdtemp(prefix='sa2v2_'); tiles = []
for i in range(NX):
    for j in range(NY):
        rect = ee.Geometry.Rectangle([x0 + i * dx, y0 + j * dy, x0 + (i + 1) * dx, y0 + (j + 1) * dy])
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
    print('GeoTIFF:', TIF_OUT, '| %.1f MB | %dx%d | %s | 10m' % (os.path.getsize(TIF_OUT) / 1e6, r.width, r.height, r.crs))
print('DONE')
