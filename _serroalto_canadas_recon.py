# -*- coding: utf-8 -*-
"""Serro Alto lotes: deteccion multi-fuente de canales/canadas.
PASO 1 = recon: rango real de cada capa (DEM/MERIT/S1/S2) + paneles visuales
sobre los lotes para ver que senal capta las canadas."""
import ee, json, os, urllib.request
import geopandas as gpd
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

LOT = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\Lotes_SerroAlto_Muestreo_Soya_26-27.geojson'
OUTDIR = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\_analisis_canadas'
os.makedirs(OUTDIR, exist_ok=True)

# lotes -> ee.FeatureCollection (simplificado)
gdf = gpd.read_file(LOT).to_crs(4326)
gdf['geometry'] = gdf.simplify(0.00002)
fc = ee.FeatureCollection(json.loads(gdf.to_json()))
aoi = fc.geometry().buffer(200)
outline = ee.Image().byte().paint(fc, 1, 1)
yellow = ee.Image([255, 255, 0]).updateMask(outline)

def rng(img, name, scale=30):
    s = img.reduceRegion(ee.Reducer.minMax().combine(ee.Reducer.mean(), sharedInputs=True),
                         aoi, scale, maxPixels=1e9, bestEffort=True).getInfo()
    ks = [k for k in s if k.endswith('_mean')]
    for k in ks:
        b = k[:-5]
        print('  %-14s min=%.3f  max=%.3f  mean=%.3f' % (b, s.get(b+'_min',0) or 0, s.get(b+'_max',0) or 0, s.get(b+'_mean',0) or 0))

# ---------- DEM GLO-30 ----------
dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic().clip(aoi)
slope = ee.Terrain.slope(dem)
print('=== DEM GLO-30 (elevacion m / pendiente grados) ==='); rng(dem.rename('elev_m'), 'dem'); rng(slope.rename('slope_deg'), 'slope')

# ---------- MERIT Hydro (HAND + flow accum) ----------
merit = ee.Image('MERIT/Hydro/v1_0_1').clip(aoi)
hnd = merit.select('hnd').rename('HAND_m')       # altura sobre drenaje mas cercano
upa = merit.select('upa').rename('flowacc_km2')  # area de drenaje acumulada
print('=== MERIT Hydro ==='); rng(hnd, 'hnd', 90); rng(upa, 'upa', 90)

# ---------- Sentinel-1 SAR ----------
s1 = (ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(aoi)
      .filter(ee.Filter.eq('instrumentMode', 'IW'))
      .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
      .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')).select(['VV', 'VH']))
def s1stat(months, lbl):
    sub = s1.filter(ee.Filter.calendarRange(months[0], months[1], 'month')).filterDate('2025-01-01', '2026-06-25')
    m = sub.median().clip(aoi)
    m = m.focal_median(30, 'circle', 'meters')   # despeckle
    print('  S1 %s (n=%d):' % (lbl, sub.size().getInfo())); rng(m.rename(['VV_'+lbl, 'VH_'+lbl]), 's1', 20)
    return m
print('=== Sentinel-1 (dB) ===')
s1_dry = s1stat((5, 9), 'dry')
s1_wet = s1stat((12, 3), 'wet')

# ---------- Sentinel-2 ----------
def s2_median(months):
    sr = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi)
          .filterDate('2025-01-01', '2026-06-25').filter(ee.Filter.calendarRange(months[0], months[1], 'month')))
    cl = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi)
          .filterDate('2025-01-01', '2026-06-25').filter(ee.Filter.calendarRange(months[0], months[1], 'month')))
    j = ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index')))
    def m(img):
        p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
        bad = p.gt(35).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1))
        return img.updateMask(bad.Not())
    return j.map(m).median().clip(aoi)
dry = s2_median((5, 9)); wet = s2_median((12, 3))
ndvi = dry.normalizedDifference(['B8', 'B4']).rename('NDVI_dry')
mndwi = dry.normalizedDifference(['B3', 'B11']).rename('MNDWI_dry')
ndwi = dry.normalizedDifference(['B3', 'B8']).rename('NDWI_dry')
mndwi_wet = wet.normalizedDifference(['B3', 'B11']).rename('MNDWI_wet')
print('=== Sentinel-2 indices ==='); rng(ndvi, 'ndvi', 10); rng(mndwi, 'mndwi', 10); rng(mndwi_wet, 'mndwi_wet', 10)

# ---------- paneles visuales ----------
def panel(viz_img, fname, dim=1400):
    comp = ee.ImageCollection([viz_img.visualize() if viz_img.bandNames().size().getInfo() == 1 else viz_img, yellow]).mosaic()
    url = comp.getThumbURL({'region': aoi, 'dimensions': dim, 'format': 'png'})
    p = os.path.join(OUTDIR, fname); urllib.request.urlretrieve(url, p)
    print('  panel ->', fname)

print('=== generando paneles ===')
tc = dry.select(['B4', 'B3', 'B2']).visualize(min=200, max=1400, gamma=1.1)
panel(ee.ImageCollection([tc, yellow]).mosaic(), '1_truecolor_dry.png')
panel(ndvi.visualize(min=0.1, max=0.7, palette=['e0d9b8', 'b8a04b', 'adff2f', '006400']), '2_NDVI_dry.png')
panel(mndwi.visualize(min=-0.3, max=0.3, palette=['8c510a', 'f5f5f5', '2166ac']), '3_MNDWI_dry.png')
panel(s1_dry.select('VV').visualize(min=-20, max=-5, palette=['000000', 'ffffff']), '4_S1_VV_dry.png')
panel(s1_wet.select('VV').visualize(min=-20, max=-5, palette=['000000', 'ffffff']), '5_S1_VV_wet.png')
panel(hnd.visualize(min=0, max=12, palette=['08306b', '4292c6', 'fdae61', 'd73027']), '6_HAND.png')
print('DONE OUTDIR=' + OUTDIR)
