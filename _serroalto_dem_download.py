# -*- coding: utf-8 -*-
"""Baja DEMs (FABDEM bare-earth / ALOS AW3D30 / GLO-30) sobre los lotes en
UTM metrico 30m para ruteo hidrologico (plani-altimetria)."""
import ee, json, os, urllib.request, zipfile
import geopandas as gpd, rasterio, numpy as np
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
LOT = os.path.join(DIRBASE, 'Lotes_SerroAlto_Muestreo_Soya_26-27.geojson')

gdf = gpd.read_file(LOT).to_crs(4326)
aoi = ee.FeatureCollection(json.loads(gdf[['lote_id', 'geometry']].to_json())).geometry().buffer(4000)

dems = {}
try:
    dems['fabdem'] = ee.ImageCollection('projects/sat-io/open-datasets/FABDEM').mosaic().select(0)
    _ = dems['fabdem'].bandNames().getInfo()
except Exception as e:
    print('FABDEM no disponible:', repr(e)[:80]); dems.pop('fabdem', None)
dems['aw3d30'] = ee.ImageCollection('JAXA/ALOS/AW3D30/V3_2').select('DSM').mosaic()
dems['glo30'] = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic()

def dl(img, name):
    img = img.reproject('EPSG:31981', None, 30).clip(aoi)
    url = img.getDownloadURL({'region': aoi, 'scale': 30, 'crs': 'EPSG:31981', 'format': 'GEO_TIFF'})
    out = os.path.join(OUTDIR, 'dem_%s.tif' % name)
    tmp = out + '.part'; urllib.request.urlretrieve(url, tmp)
    with open(tmp, 'rb') as fh:
        z = fh.read(2) == b'PK'
    if z:
        with zipfile.ZipFile(tmp) as zf:
            n = [x for x in zf.namelist() if x.lower().endswith('.tif')][0]
            open(out, 'wb').write(zf.read(n)); os.remove(tmp)
    else:
        os.replace(tmp, out)
    with rasterio.open(out) as r:
        a = r.read(1).astype('float32'); a = a[np.isfinite(a)]
        print('  %-7s %dx%d  elev %.1f..%.1f  relieve %.1f m  std %.2f  -> %s' %
              (name, r.width, r.height, a.min(), a.max(), a.max()-a.min(), a.std(), os.path.basename(out)))

print('Descargando DEMs (UTM 31981, 30m, buffer 4km):')
for nm, im in dems.items():
    try: dl(im, nm)
    except Exception as e: print('  %-7s FALLO %s' % (nm, repr(e)[:90]))
print('DONE')
