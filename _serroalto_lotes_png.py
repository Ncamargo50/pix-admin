# -*- coding: utf-8 -*-
"""Baja fondo S2 RGB seca de los lotes y genera 1 PNG por lote (lote+cañada)."""
import os, sys, json, urllib.request, zipfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import ee, geopandas as gpd, pandas as pd, numpy as np, rasterio
from rasterio.mask import mask as rmask
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
PNGDIR = os.path.join(OUTDIR, 'lotes_png'); os.makedirs(PNGDIR, exist_ok=True)
RGB = os.path.join(OUTDIR, 's2_rgb_lotes.tif')

lot = gpd.read_file(os.path.join(DIRBASE, 'Lotes_SerroAlto_LIMPIOS.geojson')).to_crs(4326)
can = gpd.read_file(os.path.join(DIRBASE, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(4326)
tab = pd.read_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv'))

# --- fondo S2 RGB seca (descarga 1 vez) ---
if not os.path.exists(RGB):
    aoi = ee.FeatureCollection(json.loads(lot[['lote_id', 'geometry']].to_json())).geometry().buffer(300)
    def cm(img):
        p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
        return img.updateMask(p.gt(35).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1)).Not())
    sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate('2025-01-01', '2026-06-25').filter(ee.Filter.calendarRange(5, 9, 'month'))
    cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate('2025-01-01', '2026-06-25').filter(ee.Filter.calendarRange(5, 9, 'month'))
    dry = ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl, condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))).map(cm).median()
    vis = dry.select(['B4', 'B3', 'B2']).clip(aoi).unitScale(200, 1500).clamp(0, 1).pow(1/1.1).multiply(255).toByte()
    url = vis.getDownloadURL({'region': aoi, 'scale': 10, 'crs': 'EPSG:4326', 'format': 'GEO_TIFF'})
    tmp = RGB + '.part'; urllib.request.urlretrieve(url, tmp)
    with open(tmp, 'rb') as fh:
        z = fh.read(2) == b'PK'
    if z:
        zf = zipfile.ZipFile(tmp); n = [x for x in zf.namelist() if x.lower().endswith('.tif')][0]; open(RGB, 'wb').write(zf.read(n)); os.remove(tmp)
    else:
        os.replace(tmp, RGB)
    print('fondo RGB ->', os.path.basename(RGB))

rsrc = rasterio.open(RGB)
print('generando PNG por lote...')
n = 0
for lid, sub in lot.groupby('lote_id'):
    geom = unary_union(sub.geometry.values); b = geom.bounds; mx = (b[2]-b[0])*0.08+0.001; my = (b[3]-b[1])*0.08+0.001
    win = rasterio.windows.from_bounds(b[0]-mx, b[1]-my, b[2]+mx, b[3]+my, rsrc.transform)
    img = rsrc.read(window=win);
    if img.size == 0: continue
    ext = rasterio.windows.bounds(win, rsrc.transform)
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.imshow(np.transpose(img, (1, 2, 0)), extent=[ext[0], ext[2], ext[1], ext[3]])
    gpd.GeoSeries([geom]).boundary.plot(ax=ax, color='yellow', linewidth=2)
    cl_l = can[can.intersects(geom)].clip(geom)
    if len(cl_l): cl_l.plot(ax=ax, color='red', alpha=0.55, edgecolor='red', linewidth=0.5)
    r = tab[tab.lote_id == lid].iloc[0]
    ax.set_title('%s  (Bloque %s)\nBruta %.1f ha | Drenaje %.1f ha (%.1f%%) | UTIL %.1f ha' %
                 (lid, r['bloque'], r['gross_ha'], r['dren_ha'], r['dren_pct'], r['util_ha']), fontsize=11)
    ax.set_xlim(ext[0], ext[2]); ax.set_ylim(ext[1], ext[3]); ax.set_axis_off()
    plt.tight_layout(); plt.savefig(os.path.join(PNGDIR, '%s.png' % lid), dpi=110, bbox_inches='tight'); plt.close()
    n += 1
print('PNG generados:', n, '->', PNGDIR)
print('DONE')
