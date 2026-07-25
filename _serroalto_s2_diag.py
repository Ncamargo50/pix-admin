# -*- coding: utf-8 -*-
"""Diagnostico Sentinel-2 sobre Cerro Alto: lista fechas recientes con
cobertura y nubosidad calculadas DENTRO del poligono (mosaico por dia)."""
import ee
ee.Initialize()

# Poligono Cerro Alto (lon,lat) extraido del KML
coords = [
    [-59.04149483287776, -18.43723058824241],
    [-59.04011845722908, -18.45517557079797],
    [-59.00326539886977, -18.50928508196885],
    [-58.96179223512260, -18.51120111104825],
    [-58.94609009832865, -18.56465899879865],
    [-58.87102796875345, -18.56262666144513],
    [-58.86294304580482, -18.59121509634033],
    [-58.84382519579287, -18.58752238332183],
    [-58.90961234071023, -18.38671128953329],
    [-58.92071589843120, -18.38565344568694],
    [-58.94160037845226, -18.33145963719488],
    [-58.96256446645500, -18.29907257354004],
    [-58.99661478895631, -18.24431724039563],
    [-59.02188311171686, -18.22257168677444],
    [-59.12269891433242, -18.35152023575153],
    [-59.12696267158442, -18.40247364203066],
    [-59.04149483287776, -18.43723058824241],
]
aoi = ee.Geometry.Polygon([coords])
area_ha = aoi.area(1).divide(1e4).getInfo()
print("AOI area: %.1f ha (%.1f km2)" % (area_ha, area_ha/100))

START, END = '2026-02-15', '2026-06-25'

s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(aoi)
      .filterDate(START, END)
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)))

print("Imagenes crudas en ventana:", s2.size().getInfo())

def add_date(img):
    return img.set('date', img.date().format('YYYY-MM-dd'))
s2 = s2.map(add_date)
dates = s2.aggregate_array('date').distinct().sort()

SCALE = 100
def per_date(d):
    d = ee.String(d)
    day = s2.filter(ee.Filter.eq('date', d))
    mosaic = day.mosaic()
    scl = mosaic.select('SCL')
    cloud = scl.eq(3).Or(scl.gte(8))          # 3 sombra, 8/9/10 nube/cirrus, 11 nieve
    valid = scl.gt(0).rename('v')
    total = ee.Image.constant(1).rename('c').clip(aoi)
    tot = total.reduceRegion(ee.Reducer.count(), aoi, SCALE, maxPixels=1e9, bestEffort=True).get('c')
    val = valid.reduceRegion(ee.Reducer.sum(), aoi, SCALE, maxPixels=1e9, bestEffort=True).get('v')
    cld = cloud.rename('cl').reduceRegion(ee.Reducer.sum(), aoi, SCALE, maxPixels=1e9, bestEffort=True).get('cl')
    plats = day.aggregate_array('SPACECRAFT_NAME').distinct()
    return ee.Feature(None, {'date': d, 'tot': tot, 'val': val, 'cld': cld,
                             'n': day.size(), 'plats': plats})

feats = ee.FeatureCollection(dates.map(per_date)).getInfo()

rows = []
for f in feats['features']:
    p = f['properties']
    tot = p.get('tot') or 0
    val = p.get('val') or 0
    cld = p.get('cld') or 0
    cov = (val/tot*100) if tot else 0
    cpct = (cld/val*100) if val else 100
    rows.append((p['date'], cov, cpct, p.get('n'), ','.join(p.get('plats', []))))

rows.sort(reverse=True)  # mas reciente primero
print("\n%-12s %8s %8s %4s  %s" % ("FECHA", "COBERT%", "NUBE%", "N", "PLATAFORMA"))
print("-"*64)
for r in rows:
    flag = "  <== CLARA" if (r[1] >= 95 and r[2] < 10) else ""
    print("%-12s %7.1f%% %7.1f%% %4d  %-22s%s" % (r[0], r[1], r[2], r[3], r[4], flag))
