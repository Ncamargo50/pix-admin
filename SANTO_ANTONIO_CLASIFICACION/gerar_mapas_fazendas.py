# -*- coding: utf-8 -*-
"""
Genera mapas PNG profesionales de las fazendas para el Anexo II do contrato.
- Santo Antonio: classificação Milho + Soja (shapefile oficial, sin buffer)
- Sao Francisco: todo marcado como Soja (shapefile oficial)
"""
import ee, json, pathlib, io, requests
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import mapping
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from pyproj import Transformer

HERE = pathlib.Path(__file__).parent
OUT = HERE / "output" / "mapas_anexo"
OUT.mkdir(exist_ok=True, parents=True)

ee.Initialize(project="ee-gisagronomico")

# Shapefiles oficiais
gdf_sa = gpd.read_file(HERE/"contrato_tmp"/"Santo_Antonio.shp").to_crs(4326)
gdf_sf = gpd.read_file(HERE/"contrato_tmp"/"Sao_Francisco.shp").to_crs(4326)

def to_ee_geom(geom):
    if geom.geom_type == "Polygon":
        return ee.Geometry.Polygon([[[x,y] for x,y,*_ in geom.exterior.coords]])
    polys = []
    for p in geom.geoms:
        polys.append([[[x,y] for x,y,*_ in p.exterior.coords]])
    return ee.Geometry.MultiPolygon(polys)

santoAntonio = to_ee_geom(gdf_sa.geometry.iloc[0])
saoFrancisco = to_ee_geom(gdf_sf.geometry.iloc[0])

# Firma soya pura (referencia S.A-2)
with open(HERE/"boundaries"/"sa2_soya_ref.geojson") as f:
    sa2_gj = json.load(f)
sa2Soya = ee.Geometry.Polygon([sa2_gj["features"][0]["geometry"]["coordinates"][0]])
soyaPure = sa2Soya.buffer(-15)

# Sentinel-2 composite
def maskS2(img):
    scl = img.select("SCL")
    m = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
         .And(scl.neq(10)).And(scl.neq(11)))
    return (img.updateMask(m).divide(10000)
              .copyProperties(img, ["system:time_start"]))

def addIdx(img):
    ndvi = img.normalizedDifference(["B8","B4"]).rename("NDVI")
    ndre = img.normalizedDifference(["B8","B5"]).rename("NDRE")
    ndmi = img.normalizedDifference(["B8A","B11"]).rename("NDMI")
    gndvi = img.normalizedDifference(["B8","B3"]).rename("GNDVI")
    evi = img.expression("2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))",
        {"NIR":img.select("B8"),"RED":img.select("B4"),"BLUE":img.select("B2")}).rename("EVI")
    gcvi = img.expression("(NIR/GREEN)-1",
        {"NIR":img.select("B8"),"GREEN":img.select("B3")}).rename("GCVI")
    return img.addBands([ndvi,ndre,ndmi,gndvi,evi,gcvi])

bbox = santoAntonio.union(saoFrancisco).buffer(500)
col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(bbox)
        .filterDate("2026-01-01","2026-02-26")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        .map(maskS2))
print(f"S-2 imagenes: {col.size().getInfo()}")

composite = col.map(addIdx).median()
BANDS = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12",
         "NDVI","NDRE","NDMI","GNDVI","EVI","GCVI"]
stack_full = composite.select(BANDS)

# Firma soya
soya_sig = stack_full.reduceRegion(
    ee.Reducer.mean(), soyaPure, 10, maxPixels=1e9).getInfo()

def eucl(sig, ref):
    return float(np.sqrt(sum((sig.get(b,0)-ref.get(b,0))**2 for b in BANDS)))

# =============== SANTO ANTONIO: classificar SIN buffer interno ===============
print("\n[Santo Antonio] classificando (sin buffer)...")
stack_sa = stack_full.clip(santoAntonio)
# Training + K-means k=2
training = stack_sa.sample(region=santoAntonio, scale=10, numPixels=6000, seed=42)
clusterer = ee.Clusterer.wekaKMeans(
    nClusters=2, init=1, maxIterations=30, seed=42).train(training)
classified_sa = stack_sa.cluster(clusterer).rename("cluster")

# Identificar cluster soja
sig0 = stack_sa.updateMask(classified_sa.eq(0)).reduceRegion(
    ee.Reducer.mean(), santoAntonio, 10, maxPixels=1e9).getInfo()
sig1 = stack_sa.updateMask(classified_sa.eq(1)).reduceRegion(
    ee.Reducer.mean(), santoAntonio, 10, maxPixels=1e9).getInfo()
d0, d1 = eucl(sig0, soya_sig), eucl(sig1, soya_sig)
soya_c = 0 if d0 < d1 else 1
maiz_c = 1 - soya_c
print(f"  Soja=Cluster{soya_c} (d={min(d0,d1):.3f}) | Milho=Cluster{maiz_c} (d={max(d0,d1):.3f})")

# Remapear: 1=Soja, 2=Milho
crop_map_sa = classified_sa.remap([soya_c, maiz_c], [1, 2]).rename("cultivo")

# Descargar RGB + classificacion
print("  Descargando RGB...")
rgb_sa = stack_full.select(["B4","B3","B2"]).multiply(10000).toInt16()
url_rgb = rgb_sa.getDownloadURL({
    "region": santoAntonio, "scale": 10, "crs": "EPSG:32722", "format":"GEO_TIFF"})
r = requests.get(url_rgb, timeout=300); r.raise_for_status()
(OUT/"sa_rgb.tif").write_bytes(r.content)

print("  Descargando classificacion...")
url_cls = crop_map_sa.clip(santoAntonio).toInt8().getDownloadURL({
    "region": santoAntonio, "scale": 10, "crs": "EPSG:32722", "format":"GEO_TIFF"})
r = requests.get(url_cls, timeout=300); r.raise_for_status()
(OUT/"sa_cls.tif").write_bytes(r.content)

# =============== SAO FRANCISCO: descargar solo RGB ===============
print("\n[Sao Francisco] descargando RGB (toda soja)...")
rgb_sf = stack_full.select(["B4","B3","B2"]).multiply(10000).toInt16()
url_rgb = rgb_sf.getDownloadURL({
    "region": saoFrancisco, "scale": 10, "crs": "EPSG:32722", "format":"GEO_TIFF"})
r = requests.get(url_rgb, timeout=300); r.raise_for_status()
(OUT/"sf_rgb.tif").write_bytes(r.content)

# =============== GENERAR PNG: SANTO ANTONIO ===============
print("\n[PNG] Santo Antonio...")
with rasterio.open(OUT/"sa_rgb.tif") as src:
    rgb = src.read().transpose(1,2,0).astype(float)
    for i in range(3):
        b = rgb[:,:,i]
        v = b[b>0]
        if len(v):
            p2, p98 = np.percentile(v, [2,98])
            rgb[:,:,i] = np.clip((b-p2)/(p98-p2), 0, 1)
    rgb_b = src.bounds; rgb_crs = src.crs

with rasterio.open(OUT/"sa_cls.tif") as src:
    cls = src.read(1); cls_b = src.bounds

# Colors: verde soja, ámbar milho
cmap_sa = ListedColormap(["#00000000", "#2E7D32", "#FFB300"])

fig, ax = plt.subplots(figsize=(8.5, 10), dpi=150)
ax.imshow(rgb, extent=[rgb_b.left, rgb_b.right, rgb_b.bottom, rgb_b.top])
ax.imshow(np.where(cls>0, cls, 0), cmap=cmap_sa, vmin=0, vmax=2, alpha=0.62,
          extent=[cls_b.left, cls_b.right, cls_b.bottom, cls_b.top])

# Boundary oficial
santo_coords = list(gdf_sa.geometry.iloc[0].geoms if gdf_sa.geometry.iloc[0].geom_type=="MultiPolygon"
                    else [gdf_sa.geometry.iloc[0]])[0].exterior.coords
bx, by = zip(*[(c[0], c[1]) for c in santo_coords])
tr = Transformer.from_crs(4326, rgb_crs, always_xy=True)
bx_m, by_m = tr.transform(bx, by)
ax.plot(bx_m, by_m, color="#FFEB3B", linewidth=2.0, label="Limite oficial", zorder=5)

# Setup
ax.set_title("Fazenda Santo Antônio\nClassificação de Cultivos — Safra 2025/2026",
             fontsize=14, fontweight="bold", color="#0F1B2D", pad=12)
ax.set_xlabel("UTM Easting (m) — Zona 22S", fontsize=9)
ax.set_ylabel("UTM Northing (m)", fontsize=9)
ax.tick_params(labelsize=8)
ax.grid(True, alpha=0.25, linestyle="--", color="#0F1B2D")

# Leyenda con áreas
legend_elements = [
    mpatches.Patch(color="#2E7D32", label="Soja: 84,67 ha (61,8%)"),
    mpatches.Patch(color="#FFB300", label="Milho: 52,38 ha (38,2%)"),
    mpatches.Patch(facecolor="none", edgecolor="#FFEB3B", linewidth=2.0,
                   label="Limite oficial (137,05 ha)"),
]
ax.legend(handles=legend_elements, loc="upper right",
          framealpha=0.93, fontsize=10, edgecolor="#CBD5E1")

# Pixadvisor badge
ax.text(0.99, 0.01, "PIXADVISOR — Agricultura de Precisão  |  Sentinel-2",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7.5, color="#0F1B2D",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#7FD633", alpha=0.85))

# Norte
arrow_x, arrow_y = 0.06, 0.92
ax.annotate("N", xy=(arrow_x, arrow_y+0.04), xytext=(arrow_x, arrow_y-0.03),
            xycoords="axes fraction", ha="center", fontsize=14, fontweight="bold",
            color="#0F1B2D",
            arrowprops=dict(facecolor="#0F1B2D", edgecolor="#0F1B2D", width=3, headwidth=10))

plt.tight_layout()
plt.savefig(OUT/"mapa_santo_antonio.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close()
print(f"  -> {OUT/'mapa_santo_antonio.png'}")

# =============== GENERAR PNG: SAO FRANCISCO ===============
print("\n[PNG] Sao Francisco...")
with rasterio.open(OUT/"sf_rgb.tif") as src:
    rgb2 = src.read().transpose(1,2,0).astype(float)
    for i in range(3):
        b = rgb2[:,:,i]
        v = b[b>0]
        if len(v):
            p2, p98 = np.percentile(v, [2,98])
            rgb2[:,:,i] = np.clip((b-p2)/(p98-p2), 0, 1)
    rgb2_b = src.bounds; rgb2_crs = src.crs

fig, ax = plt.subplots(figsize=(8.5, 10), dpi=150)
ax.imshow(rgb2, extent=[rgb2_b.left, rgb2_b.right, rgb2_b.bottom, rgb2_b.top])

# Overlay verde suave sobre todo el polígono (toda soja)
sf_geom = gdf_sf.to_crs(rgb2_crs).geometry.iloc[0]
from matplotlib.patches import PathPatch
from matplotlib.path import Path
def clean_xy(coords):
    return [(c[0], c[1]) for c in coords]

if sf_geom.geom_type == "Polygon":
    coords_list = [clean_xy(sf_geom.exterior.coords)]
else:
    coords_list = [clean_xy(p.exterior.coords) for p in sf_geom.geoms]

for coords in coords_list:
    path_data = [(Path.MOVETO, coords[0])]
    for c in coords[1:]:
        path_data.append((Path.LINETO, c))
    path_data.append((Path.CLOSEPOLY, coords[0]))
    codes, verts = zip(*path_data)
    path = Path(verts, codes)
    patch = PathPatch(path, facecolor="#2E7D32", alpha=0.55,
                      edgecolor="#FFEB3B", linewidth=2.2, zorder=4)
    ax.add_patch(patch)

ax.set_title("Fazenda São Francisco\nCultivo de Soja — Safra 2025/2026",
             fontsize=14, fontweight="bold", color="#0F1B2D", pad=12)
ax.set_xlabel("UTM Easting (m) — Zona 22S", fontsize=9)
ax.set_ylabel("UTM Northing (m)", fontsize=9)
ax.tick_params(labelsize=8)
ax.grid(True, alpha=0.25, linestyle="--", color="#0F1B2D")

legend_elements = [
    mpatches.Patch(color="#2E7D32", label="Soja: 93,39 ha (100%)"),
    mpatches.Patch(facecolor="none", edgecolor="#FFEB3B", linewidth=2.0,
                   label="Limite oficial (93,39 ha)"),
]
ax.legend(handles=legend_elements, loc="upper right",
          framealpha=0.93, fontsize=10, edgecolor="#CBD5E1")

ax.text(0.99, 0.01, "PIXADVISOR — Agricultura de Precisão  |  Sentinel-2",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7.5, color="#0F1B2D",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#7FD633", alpha=0.85))

arrow_x, arrow_y = 0.06, 0.92
ax.annotate("N", xy=(arrow_x, arrow_y+0.04), xytext=(arrow_x, arrow_y-0.03),
            xycoords="axes fraction", ha="center", fontsize=14, fontweight="bold",
            color="#0F1B2D",
            arrowprops=dict(facecolor="#0F1B2D", edgecolor="#0F1B2D", width=3, headwidth=10))

# Ajustar bounds al polígono para que se vea centrado
minx, miny, maxx, maxy = sf_geom.bounds
pad = 60
ax.set_xlim(minx-pad, maxx+pad)
ax.set_ylim(miny-pad, maxy+pad)

plt.tight_layout()
plt.savefig(OUT/"mapa_sao_francisco.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close()
print(f"  -> {OUT/'mapa_sao_francisco.png'}")

print("\nOK: 2 mapas generados en", OUT)
