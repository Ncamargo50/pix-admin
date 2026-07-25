# -*- coding: utf-8 -*-
"""Area Serro Alto: GeoTIFF 10m del compuesto MEDIANA estacion seca (s2cloudless).
Tiles getDownloadURL + merge rasterio (mosaicos unidos)."""
import ee, urllib.request, os, zipfile, tempfile, sys
import rasterio
from rasterio.merge import merge
ee.Initialize()

GAMMA = 1.10
SHARP = 0.60
CLD_PRB_THRESH = 35
NX = int(sys.argv[1]) if len(sys.argv) > 1 else 6
NY = int(sys.argv[2]) if len(sys.argv) > 2 else 6
mins = [233, 329, 217]            # estiramiento ya calculado (percentil 2-98)
maxs = [1223, 983, 743]
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
TIF_OUT = os.path.join(DESKTOP, 'AreaSerroAlto_S2_dryseason_clean.tif')

coords = [
    [-59.09980870205587, -18.58884954766944],
    [-58.60695261617405, -18.66991438639186],
    [-58.63656056535330, -18.23813443214794],
    [-59.15746155706938, -18.21358493934918],
    [-59.09980870205587, -18.58884954766944],
]
aoi = ee.Geometry.Polygon([coords])

s2sr = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi)
        .filterDate('2025-05-01', '2026-06-25').filter(ee.Filter.calendarRange(5, 9, 'month')))
s2cl = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi)
        .filterDate('2025-05-01', '2026-06-25').filter(ee.Filter.calendarRange(5, 9, 'month')))
joined = ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(
    primary=s2sr, secondary=s2cl,
    condition=ee.Filter.equals(leftField='system:index', rightField='system:index')))

def mask_img(img):
    prb = ee.Image(img.get('s2cloudless')).select('probability')
    scl = img.select('SCL')
    bad = prb.gt(CLD_PRB_THRESH).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(1)).Or(scl.eq(0))
    return img.updateMask(bad.Not())

comp = joined.map(mask_img).select(['B4', 'B3', 'B2']).median().clip(aoi)
rgb = comp.toFloat()
minI = ee.Image.constant(mins).rename(['B4', 'B3', 'B2']); maxI = ee.Image.constant(maxs).rename(['B4', 'B3', 'B2'])
scaled = rgb.subtract(minI).divide(maxI.subtract(minI)).clamp(0, 1).pow(1.0 / GAMMA)
blur = scaled.convolve(ee.Kernel.gaussian(3, 1.5, 'pixels'))
final = scaled.add(scaled.subtract(blur).multiply(SHARP)).clamp(0, 1).multiply(255).toByte()

lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
x0, x1 = min(lons), max(lons); y0, y1 = min(lats), max(lats); dx = (x1 - x0) / NX; dy = (y1 - y0) / NY
print('Grid %dx%d = %d tiles' % (NX, NY, NX * NY)); sys.stdout.flush()
tmp = tempfile.mkdtemp(prefix='area_sa_'); tiles = []
for i in range(NX):
    for j in range(NY):
        rect = ee.Geometry.Rectangle([x0 + i*dx, y0 + j*dy, x0 + (i+1)*dx, y0 + (j+1)*dy])
        d = os.path.join(tmp, 't_%d_%d.tif' % (i, j))
        for attempt in range(4):
            try:
                u = final.getDownloadURL({'region': rect, 'scale': 10, 'crs': 'EPSG:32720', 'format': 'GEO_TIFF'})
                urllib.request.urlretrieve(u, d)
                with open(d, 'rb') as fh:
                    isz = fh.read(2) == b'PK'
                if isz:
                    with zipfile.ZipFile(d) as zf:
                        n = [x for x in zf.namelist() if x.lower().endswith('.tif')][0]; data = zf.read(n)
                    with open(d, 'wb') as fo:
                        fo.write(data)
                tiles.append(d); break
            except Exception as e:
                print('  tile %d,%d intento %d: %s' % (i, j, attempt+1, repr(e)[:70])); sys.stdout.flush()
        else:
            print('  TILE %d,%d FALLIDO definitivo' % (i, j)); sys.stdout.flush()
    print('col %d/%d ok' % (i+1, NX)); sys.stdout.flush()

srcs = [rasterio.open(t) for t in tiles]; mos, tr = merge(srcs); meta = srcs[0].meta.copy()
meta.update({'height': mos.shape[1], 'width': mos.shape[2], 'count': mos.shape[0], 'transform': tr,
             'compress': 'LZW', 'photometric': 'RGB', 'nodata': 0})
with rasterio.open(TIF_OUT, 'w', **meta) as o:
    o.write(mos)
for s in srcs:
    s.close()
with rasterio.open(TIF_OUT) as r:
    print('GeoTIFF:', TIF_OUT, '| %.1f MB | %dx%d | %s | 10m | tiles unidos: %d' %
          (os.path.getsize(TIF_OUT)/1e6, r.width, r.height, r.crs, len(tiles)))
print('DONE')
