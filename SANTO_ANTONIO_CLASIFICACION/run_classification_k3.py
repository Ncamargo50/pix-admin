"""K-means k=3: detecta si hay clase espuria (barbecho, caminos, 3er cultivo)."""
import ee, json, pathlib, io, datetime as dt
import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import requests
from pyproj import Transformer

HERE = pathlib.Path(__file__).parent
OUT = HERE / "output_k3"
OUT.mkdir(exist_ok=True)

print("[1] GEE init...")
ee.Initialize(project="ee-gisagronomico")

with open(HERE/"boundaries"/"santo_antonio.geojson") as f:
    santo_gj = json.load(f)
with open(HERE/"boundaries"/"sa2_soya_ref.geojson") as f:
    sa2_gj = json.load(f)
santo_coords = santo_gj["features"][0]["geometry"]["coordinates"][0]
sa2_coords   = sa2_gj["features"][0]["geometry"]["coordinates"][0]
santoAntonio = ee.Geometry.Polygon([santo_coords])
sa2Soya      = ee.Geometry.Polygon([sa2_coords])
aoi      = santoAntonio.buffer(-15)
soyaPure = sa2Soya.buffer(-15)

area_total_ha = aoi.area(1).divide(10000).getInfo()

def maskS2(img):
    scl = img.select("SCL")
    m = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
         .And(scl.neq(10)).And(scl.neq(11)))
    return (img.updateMask(m).divide(10000)
              .copyProperties(img, ["system:time_start"]))

col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
         .filterBounds(santoAntonio.buffer(500))
         .filterDate("2026-01-01","2026-02-26")
         .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
         .map(maskS2))

n_img = col.size().getInfo()
print(f"[2] Sentinel-2: {n_img} imagenes")

def addIndices(img):
    ndvi = img.normalizedDifference(["B8","B4"]).rename("NDVI")
    ndre = img.normalizedDifference(["B8","B5"]).rename("NDRE")
    ndmi = img.normalizedDifference(["B8A","B11"]).rename("NDMI")
    gndvi = img.normalizedDifference(["B8","B3"]).rename("GNDVI")
    evi = img.expression("2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))",
        {"NIR":img.select("B8"),"RED":img.select("B4"),"BLUE":img.select("B2")}).rename("EVI")
    gcvi = img.expression("(NIR/GREEN)-1",
        {"NIR":img.select("B8"),"GREEN":img.select("B3")}).rename("GCVI")
    return img.addBands([ndvi,ndre,ndmi,gndvi,evi,gcvi])

composite = col.map(addIndices).median()
BANDS = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12",
         "NDVI","NDRE","NDMI","GNDVI","EVI","GCVI"]
stack_full = composite.select(BANDS)
stack = stack_full.clip(santoAntonio)

print("[3] Firma soya S.A-2...")
soya_sig = stack_full.reduceRegion(
    ee.Reducer.mean(), soyaPure, 10, maxPixels=1e9).getInfo()

print("[4] K-means k=3...")
training = stack.sample(region=aoi, scale=10, numPixels=5000, seed=42)
clusterer = ee.Clusterer.wekaKMeans(
    nClusters=3, init=1, maxIterations=30, seed=42).train(training)
classified = stack.cluster(clusterer).rename("cluster")

print("[5] Firmas por cluster...")
sigs = {}
for c in [0,1,2]:
    sigs[c] = stack.updateMask(classified.eq(c)).reduceRegion(
        ee.Reducer.mean(), aoi, 10, maxPixels=1e9).getInfo()

def eucl(sig_c, sig_r):
    return float(np.sqrt(sum(
        (sig_c.get(b,0) - sig_r.get(b,0))**2 for b in BANDS)))

distances = {c: eucl(sigs[c], soya_sig) for c in [0,1,2]}
print("  Distancias a firma soya:")
for c in [0,1,2]:
    s = sigs[c]
    print(f"    Cluster {c}: dist={distances[c]:.3f}  "
          f"NDVI={s.get('NDVI',0):.3f}  NDRE={s.get('NDRE',0):.3f}  "
          f"NDMI={s.get('NDMI',0):.3f}  EVI={s.get('EVI',0):.3f}  B11={s.get('B11',0):.3f}")

# Asignar: cluster mas cercano a soya = SOYA
# De los otros dos: interpretar por NDVI
sorted_by_dist = sorted(distances.items(), key=lambda x: x[1])
soya_c = sorted_by_dist[0][0]
others = [sorted_by_dist[1][0], sorted_by_dist[2][0]]

# Interpretar "otros" por NDVI/NDMI
def classify_other(c):
    s = sigs[c]
    ndvi = s.get("NDVI", 0)
    ndmi = s.get("NDMI", 0)
    b11  = s.get("B11", 0)
    if ndvi < 0.35:
        return "Suelo/Barbecho"
    elif ndvi < 0.55:
        return "Vegetacion rala/caminos/transicion"
    else:
        return "Maiz"

label_map = {soya_c: "Soya"}
for c in others:
    label_map[c] = classify_other(c)

print(f"\n[6] Asignacion final:")
for c in [0,1,2]:
    print(f"   Cluster {c} -> {label_map[c]}  (dist a soya: {distances[c]:.3f})")

# Calcular areas por cluster
print("\n[7] Areas por cluster...")
pixelArea = ee.Image.pixelArea().divide(10000)
areaImg = pixelArea.addBands(classified)
stats = areaImg.reduceRegion(
    reducer=ee.Reducer.sum().group(groupField=1, groupName="cluster"),
    geometry=aoi, scale=10, maxPixels=1e10).getInfo()

cluster_ha = {0:0.0, 1:0.0, 2:0.0}
for g in stats.get("groups", []):
    cluster_ha[g["cluster"]] = g["sum"]
total_ha = sum(cluster_ha.values())

print(f"   {'Cluster':<10}{'Clase':<30}{'Hectareas':>12}{'Pct':>8}")
print("   " + "-"*60)
for c in [0,1,2]:
    ha = cluster_ha[c]
    pct = ha/total_ha*100 if total_ha else 0
    print(f"   {c:<10}{label_map[c]:<30}{ha:>10.2f} ha{pct:>7.1f}%")

# Agrupar para comparar con k=2: Soya vs "no-soya"
soya_ha_k3 = cluster_ha[soya_c]
maiz_ha_k3 = sum(cluster_ha[c] for c in others if label_map[c] == "Maiz")
otros_ha_k3 = sum(cluster_ha[c] for c in others if label_map[c] != "Maiz")
print("\n   Comparacion con k=2:")
print(f"     SOYA:             {soya_ha_k3:.2f} ha  (vs k=2: 54.62 ha)")
print(f"     MAIZ puro:        {maiz_ha_k3:.2f} ha  (vs k=2: 51.90 ha)")
print(f"     Clase espuria:    {otros_ha_k3:.2f} ha  -> estaba inflando maiz en k=2")

# Decision: hay clase espuria significativa?
espuria_pct = otros_ha_k3/total_ha*100 if total_ha else 0
if espuria_pct < 5:
    veredicto = "OK - no hay clase espuria significativa (<5%). Resultado k=2 es confiable."
elif espuria_pct < 15:
    veredicto = f"ATENCION - clase espuria {espuria_pct:.1f}% detectada. Refinar clasificacion."
else:
    veredicto = f"CRITICO - clase espuria {espuria_pct:.1f}%. k=2 sobreestima maiz."
print(f"\n   VEREDICTO: {veredicto}")

# Descarga raster
print("\n[8] Descargando raster + generando mapa...")
# Raster con 3 clases (valores 0,1,2 del clusterer directamente)
url = classified.clip(aoi).toInt8().getDownloadURL({
    "region": aoi, "scale": 10, "crs": "EPSG:32722", "format": "GEO_TIFF"})
r = requests.get(url, timeout=300); r.raise_for_status()
tif_path = OUT / "clasificacion_k3.tif"
tif_path.write_bytes(r.content)

# RGB (reutilizar del k=2 si existe, sino descargar)
rgb_src = HERE / "output" / "santo_antonio_rgb.tif"
if not rgb_src.exists():
    rgb_url = stack.select(["B4","B3","B2"]).multiply(10000).toInt16().getDownloadURL({
        "region": santoAntonio, "scale": 10, "crs": "EPSG:32722", "format": "GEO_TIFF"})
    r2 = requests.get(rgb_url, timeout=300); r2.raise_for_status()
    rgb_src = OUT / "rgb.tif"
    rgb_src.write_bytes(r2.content)

# Visualizacion
with rasterio.open(rgb_src) as src:
    rgb = src.read().transpose(1,2,0).astype(float)
    for i in range(3):
        b = rgb[:,:,i]
        v = b[b>0]
        if len(v):
            p2, p98 = np.percentile(v, [2,98])
            rgb[:,:,i] = np.clip((b-p2)/(p98-p2), 0, 1)
    rgb_bounds = src.bounds; rgb_crs = src.crs

with rasterio.open(tif_path) as src:
    cls = src.read(1); cls_bounds = src.bounds

# Colores por clase segun label (asignar colores a cada cluster ID)
color_for_label = {
    "Soya": "#2E7D32",
    "Maiz": "#FFB300",
    "Suelo/Barbecho": "#8B4513",
    "Vegetacion rala/caminos/transicion": "#B8860B",
}
# cls contiene 0,1,2 -> necesitamos mapear a color segun cluster
# construir cmap indexado por valor de cluster
cluster_colors = ["#00000000","#00000000","#00000000","#00000000"]  # 0..3
for c in [0,1,2]:
    cluster_colors[c+1] = color_for_label.get(label_map[c], "#888888")
# offset: cls+1 para evitar 0-conflict con mask
cls_vis = np.where(cls >= 0, cls+1, 0).astype(np.int16)

cmap = ListedColormap(cluster_colors)

fig, ax = plt.subplots(figsize=(11,14), dpi=150)
ax.imshow(rgb, extent=[rgb_bounds.left,rgb_bounds.right,
                       rgb_bounds.bottom,rgb_bounds.top])
ax.imshow(cls_vis, cmap=cmap, vmin=0, vmax=3, alpha=0.55,
          extent=[cls_bounds.left,cls_bounds.right,
                  cls_bounds.bottom,cls_bounds.top])

bx, by = zip(*santo_coords)
tr = Transformer.from_crs(4326, rgb_crs, always_xy=True)
bx_m, by_m = tr.transform(bx, by)
ax.plot(bx_m, by_m, color="yellow", linewidth=1.5)

ax.set_title(f"K-means k=3 - Faz. Santo Antonio\n"
             f"Sentinel-2 composite 2026-01-01 a 2026-02-25 ({n_img} imagenes)",
             fontsize=13, fontweight="bold")
ax.set_xlabel("UTM Easting (m) - Zona 22S")
ax.set_ylabel("UTM Northing (m)")

patches = []
for c in [0,1,2]:
    patches.append(mpatches.Patch(
        color=cluster_colors[c+1],
        label=f"C{c} {label_map[c]}: {cluster_ha[c]:.2f} ha "
              f"({cluster_ha[c]/total_ha*100:.1f}%)"))
ax.legend(handles=patches, loc="upper right", framealpha=0.92, fontsize=10)
ax.grid(True, alpha=0.3, linestyle="--")
plt.tight_layout()
png_path = OUT/"mapa_k3.png"
plt.savefig(png_path, dpi=150, bbox_inches="tight")
print(f"   -> {png_path.name}")

# Reporte
report = f"""
================================================================
K-MEANS k=3 - Detectar Clase Espuria
================================================================
Area total AOI:   {area_total_ha:.2f} ha
Imagenes S-2:     {n_img}

Firma SOYA (S.A-2 control):
  NDVI={soya_sig['NDVI']:.3f}  NDRE={soya_sig['NDRE']:.3f}  NDMI={soya_sig['NDMI']:.3f}

RESULTADOS K=3:
"""
for c in [0,1,2]:
    s = sigs[c]
    report += f"""
  Cluster {c}: {label_map[c]}  (dist a soya: {distances[c]:.3f})
    Area     = {cluster_ha[c]:.2f} ha ({cluster_ha[c]/total_ha*100:.1f}%)
    NDVI     = {s.get('NDVI',0):.3f}
    NDRE     = {s.get('NDRE',0):.3f}
    NDMI     = {s.get('NDMI',0):.3f}
    EVI      = {s.get('EVI',0):.3f}
    B11 SWIR = {s.get('B11',0):.3f}
"""
report += f"""
COMPARACION:
  k=2 -> Soya: 54.62 ha  |  Maiz: 51.90 ha
  k=3 -> Soya: {soya_ha_k3:.2f} ha  |  Maiz: {maiz_ha_k3:.2f} ha  |  Otros: {otros_ha_k3:.2f} ha

Clase espuria en k=3: {otros_ha_k3:.2f} ha ({espuria_pct:.1f}%)
VEREDICTO: {veredicto}
================================================================
"""
print(report)
(OUT/"reporte_k3.txt").write_text(report, encoding="utf-8")
print(f"OK -> {OUT}")
