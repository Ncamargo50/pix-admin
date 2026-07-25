# -*- coding: utf-8 -*-
"""Cerro Alto: mascara cañadas (NDVI-p10 veg permanente + corroboracion HAND),
validacion visual sobre color real, y AREA UTIL por lote (3 umbrales)."""
import ee, json, os, urllib.request
import geopandas as gpd, pandas as pd
import warnings; warnings.filterwarnings('ignore')
ee.Initialize()

LOT = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\Lotes_SerroAlto_Muestreo_Soya_26-27.geojson'
OUTDIR = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27\_analisis_canadas'

gdf = gpd.read_file(LOT).to_crs(4326)
fcs = ee.FeatureCollection(json.loads(gdf[['lote_id', 'geometry']].to_json()))
aoi = fcs.geometry().buffer(200)
outlineViz = ee.Image().byte().paint(fcs, 1, 1).selfMask().visualize(palette=['00e5ff'])

def cloudmask(img):
    p = ee.Image(img.get('cl')).select('probability'); scl = img.select('SCL')
    return img.updateMask(p.gt(35).Or(scl.eq(3)).Or(scl.gte(8)).Or(scl.eq(0)).Or(scl.eq(1)).Not())
def join_s2(d0, d1, months=None):
    sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(aoi).filterDate(d0, d1)
    cl = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY').filterBounds(aoi).filterDate(d0, d1)
    if months: sr = sr.filter(ee.Filter.calendarRange(*months, 'month')); cl = cl.filter(ee.Filter.calendarRange(*months, 'month'))
    return ee.ImageCollection(ee.Join.saveFirst('cl').apply(primary=sr, secondary=cl,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index'))).map(cloudmask)

ndvi_p10 = join_s2('2024-06-01', '2026-06-25').map(
    lambda im: im.normalizedDifference(['B8', 'B4']).rename('NDVI')).reduce(ee.Reducer.percentile([10])).clip(aoi).rename('p10')
dry = join_s2('2025-01-01', '2026-06-25', (5, 9)).median().clip(aoi)
hand = ee.Image('MERIT/Hydro/v1_0_1').select('hnd').clip(aoi)

def veg_mask(thr):
    m = ndvi_p10.gt(thr).selfMask()
    m = m.updateMask(m.connectedPixelCount(50, True).gte(3))   # quita ruido <3px
    return m

# ---- validacion visual (umbral 0.40) ----
THR = 0.40
veg = veg_mask(THR)
tc = dry.select(['B4', 'B3', 'B2']).visualize(min=200, max=1500, gamma=1.1)
ov = tc.blend(veg.visualize(palette=['ff0000'])).blend(outlineViz)
p = os.path.join(OUTDIR, '7_VALIDACION_canadas_thr040.png')
urllib.request.urlretrieve(ov.getThumbURL({'region': aoi, 'dimensions': 1500, 'format': 'png'}), p)
print('validacion ->', os.path.basename(p))

# corroboracion HAND: % de la veg permanente que cae sobre drenaje (HAND<3m)
# ---- AREA UTIL por lote, 3 umbrales ----
areaImg = ee.Image.pixelArea()
gdf_m = gdf.to_crs(31981); gdf['gross_ha'] = (gdf_m.area / 1e4).values

for THR in (0.35, 0.40, 0.45):
    veg = veg_mask(THR)
    vegA = areaImg.updateMask(veg).rename('veg')
    drainCorr = areaImg.updateMask(veg.And(hand.lt(3))).rename('drn')
    stack = vegA.addBands(drainCorr)
    rr = stack.reduceRegions(fcs, ee.Reducer.sum(), 10).getInfo()
    rows = {}
    for f in rr['features']:
        pr = f['properties']; lid = pr['lote_id']
        rows.setdefault(lid, [0, 0])
        rows[lid][0] += (pr.get('veg') or 0) / 1e4
        rows[lid][1] += (pr.get('drn') or 0) / 1e4
    df = pd.DataFrame([(k, v[0], v[1]) for k, v in rows.items()], columns=['lote_id', 'veg_ha', 'drn_ha'])
    df = gdf[['lote_id', 'bloque', 'gross_ha']].merge(df, on='lote_id', how='left').fillna(0)
    df = df.groupby(['lote_id', 'bloque'], as_index=False).agg(gross_ha=('gross_ha', 'sum'), veg_ha=('veg_ha', 'sum'), drn_ha=('drn_ha', 'sum'))
    df['util_ha'] = (df['gross_ha'] - df['veg_ha']).clip(lower=0)
    df['no_util_%'] = (df['veg_ha'] / df['gross_ha'] * 100).round(1)
    tot = df[['gross_ha', 'veg_ha', 'util_ha']].sum()
    print('\n===== UMBRAL NDVI_p10 > %.2f =====' % THR)
    print('  TOTAL: bruta %.1f ha | no-util(veg) %.1f ha | UTIL %.1f ha | descuento %.1f%% | corrob.drenaje %.1f ha'
          % (tot['gross_ha'], tot['veg_ha'], tot['util_ha'], tot['veg_ha']/tot['gross_ha']*100, df['drn_ha'].sum()))
    if THR == 0.40:
        df.sort_values(['bloque', 'lote_id']).to_csv(os.path.join(OUTDIR, 'area_util_por_lote_thr040.csv'), index=False, encoding='utf-8-sig')
        print('  CSV por lote guardado. Ejemplo (primeros 6):')
        for _, r in df.sort_values('no_util_%', ascending=False).head(6).iterrows():
            print('    %-16s B%-3s bruta %5.1f  no-util %4.1f (%4.1f%%)  UTIL %5.1f ha' % (r['lote_id'], r['bloque'], r['gross_ha'], r['veg_ha'], r['no_util_%'], r['util_ha']))
print('\nDONE')
