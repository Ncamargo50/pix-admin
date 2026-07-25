# -*- coding: utf-8 -*-
"""GeoTIFF color natural optimizado de Serro Alto via tiles + merge rasterio."""
import ee, urllib.request, os, zipfile, tempfile
import rasterio
from rasterio.merge import merge
ee.Initialize()

DATE  = '2026-06-02'
GAMMA = 1.10
SHARP = 0.65
mins  = [179, 275, 149]
maxs  = [1231, 1039, 782]
NX, NY = 2, 3                       # 6 tiles (~12 MB c/u, bajo el limite de 48 MB)
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

lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
x0, x1 = min(lons), max(lons); y0, y1 = min(lats), max(lats)
dx = (x1 - x0) / NX; dy = (y1 - y0) / NY

tmpdir = tempfile.mkdtemp(prefix='sa_tiles_')
tiles = []
for i in range(NX):
    for j in range(NY):
        rect = ee.Geometry.Rectangle([x0 + i*dx, y0 + j*dy, x0 + (i+1)*dx, y0 + (j+1)*dy])
        url = final.getDownloadURL({'region': rect, 'scale': 10, 'crs': 'EPSG:32720', 'format': 'GEO_TIFF'})
        dst = os.path.join(tmpdir, 'tile_%d_%d.tif' % (i, j))
        urllib.request.urlretrieve(url, dst)
        # algunos vienen zip
        with open(dst, 'rb') as fh:
            if fh.read(2) == b'PK':
                with zipfile.ZipFile(dst) as z:
                    n = [x for x in z.namelist() if x.lower().endswith('.tif')][0]
                    data = z.read(n)
                with open(dst, 'wb') as fo:
                    fo.write(data)
        tiles.append(dst)
        print('tile %d,%d -> %.1f MB' % (i, j, os.path.getsize(dst)/1e6))

srcs = [rasterio.open(t) for t in tiles]
mosaic, transform = merge(srcs)
meta = srcs[0].meta.copy()
meta.update({'height': mosaic.shape[1], 'width': mosaic.shape[2], 'count': mosaic.shape[0],
             'transform': transform, 'compress': 'LZW', 'photometric': 'RGB', 'nodata': 0})
with rasterio.open(TIF_OUT, 'w', **meta) as out:
    out.write(mosaic)
for s in srcs:
    s.close()

with rasterio.open(TIF_OUT) as r:
    print('\nGeoTIFF FINAL:', TIF_OUT)
    print('  tamano   : %.1f MB' % (os.path.getsize(TIF_OUT)/1e6))
    print('  dimension: %d x %d px, %d bandas, %s' % (r.width, r.height, r.count, r.dtypes[0]))
    print('  CRS      :', r.crs, '| res:', tuple(round(v, 2) for v in r.res), 'm')
