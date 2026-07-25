"""
Clasificacion maiz vs soya en Faz. Santo Antonio usando GEE.
Pipeline completo server-side -> descarga local de raster + vector + reporte.
"""
import ee, json, os, pathlib, io, zipfile, sys
import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape, mapping
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import requests

HERE = pathlib.Path(__file__).parent
OUT  = HERE / "output"
OUT.mkdir(exist_ok=True)

print("[1/9] Inicializando GEE (proyecto ee-gisagronomico)...")
ee.Initialize(project="ee-gisagronomico")

# -----------------------------------------------------------------------------
# 1. CARGAR BOUNDARIES
# -----------------------------------------------------------------------------
print("[2/9] Cargando boundaries desde GeoJSON...")
with open(HERE / "boundaries" / "santo_antonio.geojson") as f:
    santo_gj = json.load(f)
with open(HERE / "boundaries" / "sa2_soya_ref.geojson") as f:
    sa2_gj = json.load(f)

santo_coords = santo_gj["features"][0]["geometry"]["coordinates"][0]
sa2_coords   = sa2_gj["features"][0]["geometry"]["coordinates"][0]

santoAntonio = ee.Geometry.Polygon([santo_coords])
sa2Soya      = ee.Geometry.Polygon([sa2_coords])

aoi      = santoAntonio.buffer(-15)
soyaPure = sa2Soya.buffer(-15)

area_total_ha = aoi.area(1).divide(10000).getInfo()
print(f"       Santo Antonio AOI: {area_total_ha:.2f} ha")
print(f"       S.A-2 (soya ref):  {sa2Soya.area(1).divide(10000).getInfo():.2f} ha")

# -----------------------------------------------------------------------------
# 2. SENTINEL-2 + MASCARA SCL
# -----------------------------------------------------------------------------
START = "2026-01-01"
END   = "2026-02-26"
CLOUD = 30

def maskS2(img):
    scl = img.select("SCL")
    mask = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
               .And(scl.neq(10)).And(scl.neq(11)))
    return (img.updateMask(mask).divide(10000)
               .copyProperties(img, ["system:time_start"]))

col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
         .filterBounds(santoAntonio.buffer(500))
         .filterDate(START, END)
         .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD))
         .map(maskS2))

n_img = col.size().getInfo()
print(f"[3/9] Sentinel-2: {n_img} imagenes (nubes<{CLOUD}%, {START} a {END})")
if n_img < 3:
    print(f"       AVISO: pocas imagenes. Subiendo umbral de nubes a 50%...")
    CLOUD = 50
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
             .filterBounds(santoAntonio.buffer(500))
             .filterDate(START, END)
             .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", CLOUD))
             .map(maskS2))
    n_img = col.size().getInfo()
    print(f"       Ahora: {n_img} imagenes")

dates = col.aggregate_array("system:time_start").getInfo()
import datetime as dt
date_strs = [dt.datetime.utcfromtimestamp(t/1000).strftime("%Y-%m-%d") for t in dates]
print(f"       Fechas: {', '.join(date_strs)}")

# -----------------------------------------------------------------------------
# 3. INDICES + COMPOSITE
# -----------------------------------------------------------------------------
print("[4/9] Calculando indices + compuesto mediana...")

def addIndices(img):
    ndvi = img.normalizedDifference(["B8","B4"]).rename("NDVI")
    ndre = img.normalizedDifference(["B8","B5"]).rename("NDRE")
    ndmi = img.normalizedDifference(["B8A","B11"]).rename("NDMI")
    gndvi = img.normalizedDifference(["B8","B3"]).rename("GNDVI")
    evi = img.expression(
        "2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))",
        {"NIR": img.select("B8"), "RED": img.select("B4"), "BLUE": img.select("B2")}
    ).rename("EVI")
    gcvi = img.expression("(NIR/GREEN)-1",
        {"NIR": img.select("B8"), "GREEN": img.select("B3")}
    ).rename("GCVI")
    return img.addBands([ndvi, ndre, ndmi, gndvi, evi, gcvi])

composite = col.map(addIndices).median()

BANDS = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12",
         "NDVI","NDRE","NDMI","GNDVI","EVI","GCVI"]

# stack SIN clip: S.A-2 esta fuera del poligono Santo Antonio (-2km sur)
stack_full = composite.select(BANDS)
stack      = stack_full.clip(santoAntonio)   # solo para clasif dentro de AOI

# -----------------------------------------------------------------------------
# 4. FIRMA ESPECTRAL DE SOYA (S.A-2)  -- usa stack_full sin clip
# -----------------------------------------------------------------------------
print("[5/9] Extrayendo firma espectral de SOYA pura (S.A-2)...")
soya_sig = stack_full.reduceRegion(
    reducer=ee.Reducer.mean(), geometry=soyaPure, scale=10, maxPixels=1e9
).getInfo()
print(f"       Firma soya NDVI={soya_sig['NDVI']:.3f} NDRE={soya_sig['NDRE']:.3f} "
      f"NDMI={soya_sig['NDMI']:.3f} EVI={soya_sig['EVI']:.3f}")

# -----------------------------------------------------------------------------
# 5. K-MEANS k=2
# -----------------------------------------------------------------------------
print("[6/9] K-means k=2 (5000 samples dentro de Santo Antonio)...")
training = stack.sample(region=aoi, scale=10, numPixels=5000, seed=42)
clusterer = ee.Clusterer.wekaKMeans(nClusters=2, init=1, maxIterations=30, seed=42).train(training)
classified = stack.cluster(clusterer).rename("cluster")

sig0 = stack.updateMask(classified.eq(0)).reduceRegion(
    reducer=ee.Reducer.mean(), geometry=aoi, scale=10, maxPixels=1e9).getInfo()
sig1 = stack.updateMask(classified.eq(1)).reduceRegion(
    reducer=ee.Reducer.mean(), geometry=aoi, scale=10, maxPixels=1e9).getInfo()

# distancia euclidiana a firma de soya
def eucl(sig_cluster, sig_ref):
    return float(np.sqrt(sum(
        (sig_cluster.get(b,0) - sig_ref.get(b,0))**2 for b in BANDS
    )))

d0 = eucl(sig0, soya_sig)
d1 = eucl(sig1, soya_sig)
soya_cluster = 0 if d0 < d1 else 1
maiz_cluster = 1 - soya_cluster
print(f"       Dist Cluster0->Soya: {d0:.4f}")
print(f"       Dist Cluster1->Soya: {d1:.4f}")
print(f"       SOYA = Cluster {soya_cluster}  |  MAIZ = Cluster {maiz_cluster}")
print(f"       Separabilidad: {abs(d0-d1)/max(d0,d1)*100:.1f}%")

# remap: 1=soya, 2=maiz
cropMap = classified.remap([soya_cluster, maiz_cluster], [1, 2]).rename("cultivo")

# -----------------------------------------------------------------------------
# 6. CALCULO DE AREAS
# -----------------------------------------------------------------------------
print("[7/9] Calculando areas por cultivo...")
pixelArea = ee.Image.pixelArea().divide(10000)
areaImg = pixelArea.addBands(cropMap)
stats = areaImg.reduceRegion(
    reducer=ee.Reducer.sum().group(groupField=1, groupName="cultivo"),
    geometry=aoi, scale=10, maxPixels=1e10
).getInfo()

soya_ha, maiz_ha = 0.0, 0.0
for g in stats.get("groups", []):
    if g["cultivo"] == 1: soya_ha = g["sum"]
    if g["cultivo"] == 2: maiz_ha = g["sum"]
sum_ha = soya_ha + maiz_ha

print("       " + "="*50)
print(f"       AREA TOTAL AOI:  {area_total_ha:.2f} ha")
print(f"       SOYA:            {soya_ha:.2f} ha  ({soya_ha/sum_ha*100:.1f}%)")
print(f"       MAIZ:            {maiz_ha:.2f} ha  ({maiz_ha/sum_ha*100:.1f}%)")
print("       " + "="*50)

# -----------------------------------------------------------------------------
# 7. DESCARGA DE RASTER CLASIFICADO
# -----------------------------------------------------------------------------
print("[8/9] Descargando raster clasificado a GeoTIFF...")
classified_clip = cropMap.clip(aoi).toInt8()

url = classified_clip.getDownloadURL({
    "region": aoi,
    "scale": 10,
    "crs": "EPSG:32722",
    "format": "GEO_TIFF"
})
r = requests.get(url, timeout=300)
r.raise_for_status()
tif_path = OUT / "santo_antonio_clasificacion.tif"
with open(tif_path, "wb") as f:
    f.write(r.content)
print(f"       -> {tif_path.name} ({len(r.content)/1024:.1f} KB)")

# Tambien descarga el RGB compuesto para visualizacion
print("       Descargando RGB compuesto...")
rgb = stack.select(["B4","B3","B2"]).multiply(10000).toInt16()
url_rgb = rgb.getDownloadURL({
    "region": santoAntonio,
    "scale": 10,
    "crs": "EPSG:32722",
    "format": "GEO_TIFF"
})
r_rgb = requests.get(url_rgb, timeout=300)
r_rgb.raise_for_status()
rgb_path = OUT / "santo_antonio_rgb.tif"
with open(rgb_path, "wb") as f:
    f.write(r_rgb.content)
print(f"       -> {rgb_path.name} ({len(r_rgb.content)/1024:.1f} KB)")

# -----------------------------------------------------------------------------
# 8. VECTORIZACION local (rasterio -> shapefile)
# -----------------------------------------------------------------------------
print("[9/9] Vectorizando raster -> GeoJSON/Shapefile...")
with rasterio.open(tif_path) as src:
    data = src.read(1)
    mask = data > 0
    transform = src.transform
    crs = src.crs
    feats = []
    for geom, val in shapes(data.astype(np.int16), mask=mask, transform=transform):
        feats.append({
            "type": "Feature",
            "properties": {
                "cultivo_id": int(val),
                "cultivo": "Soya" if int(val) == 1 else "Maiz"
            },
            "geometry": geom
        })

gdf = gpd.GeoDataFrame.from_features(feats, crs=crs)
# area en ha (ya estamos en UTM metros)
gdf["area_ha"] = gdf.geometry.area / 10000.0
# filtrar sliver polygons < 0.03 ha (3 pixels de 10m ~= 300m2)
gdf_clean = gdf[gdf["area_ha"] >= 0.03].copy()

# guardar shapefile y geojson
shp_path = OUT / "santo_antonio_poligonos.shp"
gj_path  = OUT / "santo_antonio_poligonos.geojson"
gdf_clean.to_file(shp_path)
gdf_clean.to_crs(4326).to_file(gj_path, driver="GeoJSON")
print(f"       -> {shp_path.name} + .geojson ({len(gdf_clean)} poligonos, "
      f"descartados {len(gdf)-len(gdf_clean)} sliver)")

# -----------------------------------------------------------------------------
# 9. VISUALIZACION PNG
# -----------------------------------------------------------------------------
print("[+] Generando mapa PNG...")
with rasterio.open(rgb_path) as src:
    rgb_arr = src.read().transpose(1,2,0).astype(float)
    # stretch 2-98%
    for i in range(3):
        b = rgb_arr[:,:,i]
        valid = b[b > 0]
        if len(valid) > 0:
            p2, p98 = np.percentile(valid, [2, 98])
            rgb_arr[:,:,i] = np.clip((b - p2) / (p98 - p2), 0, 1)
    rgb_bounds = src.bounds
    rgb_crs = src.crs

with rasterio.open(tif_path) as src:
    cls_arr = src.read(1)
    cls_bounds = src.bounds

fig, ax = plt.subplots(figsize=(11, 14), dpi=150)
ax.imshow(rgb_arr, extent=[rgb_bounds.left, rgb_bounds.right,
                            rgb_bounds.bottom, rgb_bounds.top])

# overlay clasificacion con transparencia
from matplotlib.colors import ListedColormap
cmap = ListedColormap(["#00000000", "#2E7D32", "#FFB300"])
cls_display = np.where(cls_arr > 0, cls_arr, 0)
ax.imshow(cls_display, cmap=cmap, vmin=0, vmax=2, alpha=0.55,
          extent=[cls_bounds.left, cls_bounds.right,
                  cls_bounds.bottom, cls_bounds.top])

# boundary
bx, by = zip(*santo_coords)
from pyproj import Transformer
tr = Transformer.from_crs(4326, rgb_crs, always_xy=True)
bx_m, by_m = tr.transform(bx, by)
ax.plot(bx_m, by_m, color="yellow", linewidth=1.5, label="Santo Antonio")

ax.set_title("Clasificacion Maiz vs Soya - Faz. Santo Antonio\n"
             f"Sentinel-2 composite {START} a 2026-02-25 ({n_img} imagenes)",
             fontsize=13, fontweight="bold")
ax.set_xlabel("UTM Easting (m) - Zona 22S")
ax.set_ylabel("UTM Northing (m)")

soya_patch = mpatches.Patch(color="#2E7D32",
    label=f"Soya: {soya_ha:.2f} ha ({soya_ha/sum_ha*100:.1f}%)")
maiz_patch = mpatches.Patch(color="#FFB300",
    label=f"Maiz: {maiz_ha:.2f} ha ({maiz_ha/sum_ha*100:.1f}%)")
ax.legend(handles=[soya_patch, maiz_patch], loc="upper right",
          framealpha=0.92, fontsize=11)

ax.grid(True, alpha=0.3, linestyle="--")
plt.tight_layout()
png_path = OUT / "mapa_clasificacion.png"
plt.savefig(png_path, dpi=150, bbox_inches="tight")
print(f"       -> {png_path.name}")

# -----------------------------------------------------------------------------
# REPORTE FINAL
# -----------------------------------------------------------------------------
report = f"""
================================================================
CLASIFICACION MAIZ vs SOYA - Faz. Santo Antonio
================================================================
Periodo analizado : {START} -> 2026-02-25
Imagenes S-2 usadas: {n_img}  (nubes<{CLOUD}%)
Fechas            : {', '.join(date_strs)}
CRS               : EPSG:32722 (WGS84 / UTM 22S)

Metodologia:
  1. Composite mediana Sentinel-2 SR + mascara SCL
  2. Stack 10 bandas + 6 indices (NDVI,NDRE,NDMI,GNDVI,EVI,GCVI)
  3. K-means k=2 (5000 samples)
  4. Asignacion cluster->cultivo por distancia a firma S.A-2

Firma espectral referencia (S.A-2 solo soya):
  NDVI  = {soya_sig['NDVI']:.3f}
  NDRE  = {soya_sig['NDRE']:.3f}
  NDMI  = {soya_sig['NDMI']:.3f}
  EVI   = {soya_sig['EVI']:.3f}

Separabilidad:
  Distancia Cluster0 -> firma soya: {d0:.4f}
  Distancia Cluster1 -> firma soya: {d1:.4f}
  Margen separacion: {abs(d0-d1)/max(d0,d1)*100:.1f}%
  Asignacion:  SOYA=Cluster{soya_cluster}  MAIZ=Cluster{maiz_cluster}

RESULTADOS:
  Area total AOI:  {area_total_ha:>8.2f} ha
  SOYA:            {soya_ha:>8.2f} ha  ({soya_ha/sum_ha*100:>4.1f}%)
  MAIZ:            {maiz_ha:>8.2f} ha  ({maiz_ha/sum_ha*100:>4.1f}%)

Archivos generados:
  output/santo_antonio_clasificacion.tif  (raster 1=Soya, 2=Maiz)
  output/santo_antonio_rgb.tif            (RGB Sentinel-2 compuesto)
  output/santo_antonio_poligonos.shp      (poligonos vectoriales)
  output/santo_antonio_poligonos.geojson  (idem WGS84)
  output/mapa_clasificacion.png           (mapa final)
================================================================
"""
print(report)
with open(OUT / "reporte.txt", "w", encoding="utf-8") as f:
    f.write(report)
print(f"OK -> {OUT}")
