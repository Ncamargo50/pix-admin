"""Debug: ver cobertura y valores en S.A-2."""
import ee, json, pathlib
ee.Initialize(project="ee-gisagronomico")
HERE = pathlib.Path(__file__).parent

with open(HERE / "boundaries" / "sa2_soya_ref.geojson") as f:
    sa2_gj = json.load(f)
sa2 = ee.Geometry.Polygon([sa2_gj["features"][0]["geometry"]["coordinates"][0]])
sa2_buf = sa2.buffer(-15)
print("SA2 area con buffer-15:", sa2_buf.area(1).divide(10000).getInfo(), "ha")

# SIN mascara
col_raw = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(sa2)
    .filterDate("2026-01-01", "2026-02-26")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))
print("Sin mascara - N imagenes:", col_raw.size().getInfo())

# SCL value counts para la primera imagen sobre S.A-2
first = ee.Image(col_raw.first())
print("Primera imagen:", first.date().format("YYYY-MM-dd").getInfo())

scl_hist = first.select("SCL").reduceRegion(
    reducer=ee.Reducer.frequencyHistogram(),
    geometry=sa2_buf, scale=10, maxPixels=1e9).getInfo()
print("SCL histogram primera imagen:", scl_hist)

# Con mascara relajada (solo 8,9,10): permite shadow (3) y cirrus-light
def mask_relaxed(img):
    scl = img.select("SCL")
    m = scl.neq(8).And(scl.neq(9)).And(scl.neq(10))
    return img.updateMask(m).divide(10000).copyProperties(img, ["system:time_start"])

col_rx = col_raw.map(mask_relaxed)
comp_rx = col_rx.median()
sig = comp_rx.select(["B4","B8"]).reduceRegion(
    ee.Reducer.mean(), sa2_buf, 10, maxPixels=1e9).getInfo()
print("Firma mascara relajada:", sig)

# Con NO mascara
def no_mask(img):
    return img.divide(10000).copyProperties(img, ["system:time_start"])
col_nm = col_raw.map(no_mask)
comp_nm = col_nm.median()
sig2 = comp_nm.select(["B4","B8"]).reduceRegion(
    ee.Reducer.mean(), sa2_buf, 10, maxPixels=1e9).getInfo()
print("Firma SIN mascara:", sig2)

# Check cada imagen individualmente con mascara original
for i in range(col_raw.size().getInfo()):
    img = ee.Image(col_raw.toList(10).get(i))
    date = img.date().format("YYYY-MM-dd").getInfo()
    scl = img.select("SCL")
    mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
    masked_count = mask.reduceRegion(
        ee.Reducer.sum(), sa2_buf, 10, maxPixels=1e9).getInfo()["SCL"]
    total_count = scl.reduceRegion(
        ee.Reducer.count(), sa2_buf, 10, maxPixels=1e9).getInfo()["SCL"]
    pct = masked_count/total_count*100 if total_count else 0
    print(f"  {date}: pixels validos tras SCL = {masked_count}/{total_count} ({pct:.0f}%)")
