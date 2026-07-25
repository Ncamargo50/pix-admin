"""Re-clasificacion usando shapefile OFICIAL de Santo Antonio (137 ha).
Detecta tambien no-cultivo (APP, barbecho) con k=3."""
import ee, json, pathlib
import numpy as np
import geopandas as gpd

HERE = pathlib.Path(__file__).parent
ee.Initialize(project="ee-gisagronomico")

# Shapefile OFICIAL Santo Antonio
gdf_sa = gpd.read_file(HERE/"contrato_tmp"/"Santo_Antonio.shp").to_crs(4326)
gdf_sf = gpd.read_file(HERE/"contrato_tmp"/"Sao_Francisco.shp").to_crs(4326)

def to_ee_geom(geom):
    """Convert shapely Polygon/MultiPolygon to ee.Geometry."""
    if geom.geom_type == "Polygon":
        return ee.Geometry.Polygon([[[x,y] for x,y,*_ in geom.exterior.coords]])
    # MultiPolygon: union de poligonos
    polys = []
    for p in geom.geoms:
        polys.append([[[x,y] for x,y,*_ in p.exterior.coords]])
    return ee.Geometry.MultiPolygon(polys)

santoAntonio = to_ee_geom(gdf_sa.geometry.iloc[0])
saoFrancisco = to_ee_geom(gdf_sf.geometry.iloc[0])

# Firma de soya pura (desde S.A-2 original)
with open(HERE/"boundaries"/"sa2_soya_ref.geojson") as f:
    sa2_gj = json.load(f)
sa2Soya = ee.Geometry.Polygon([sa2_gj["features"][0]["geometry"]["coordinates"][0]])

aoi_santo = santoAntonio.buffer(-15)
aoi_sf    = saoFrancisco.buffer(-15)
soyaPure  = sa2Soya.buffer(-15)

ha_santo = aoi_santo.area(1).divide(10000).getInfo()
ha_sf    = aoi_sf.area(1).divide(10000).getInfo()
print(f"Santo Antonio oficial: {ha_santo:.2f} ha (AOI buffer -15m)")
print(f"Sao Francisco oficial: {ha_sf:.2f} ha (AOI buffer -15m)")

def maskS2(img):
    scl = img.select("SCL")
    m = (scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
         .And(scl.neq(10)).And(scl.neq(11)))
    return (img.updateMask(m).divide(10000)
              .copyProperties(img,["system:time_start"]))

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

# Bbox conjunto para filterBounds
bbox_all = santoAntonio.union(saoFrancisco).buffer(500)
col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(bbox_all)
        .filterDate("2026-01-01","2026-02-26")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        .map(maskS2))
n_img = col.size().getInfo()
print(f"S-2 imagenes: {n_img}")

composite = col.map(addIdx).median()
BANDS = ["B2","B3","B4","B5","B6","B7","B8","B8A","B11","B12",
         "NDVI","NDRE","NDMI","GNDVI","EVI","GCVI"]
stack_full = composite.select(BANDS)

# Firma soya pura
soya_sig = stack_full.reduceRegion(
    ee.Reducer.mean(), soyaPure, 10, maxPixels=1e9).getInfo()
print(f"\nFirma soya ref (S.A-2): NDVI={soya_sig['NDVI']:.3f} "
      f"NDRE={soya_sig['NDRE']:.3f} EVI={soya_sig['EVI']:.3f}")

def eucl(sig, ref):
    return float(np.sqrt(sum((sig.get(b,0)-ref.get(b,0))**2 for b in BANDS)))

# ============ SANTO ANTONIO (k=3: soja / milho / no-cultivo) ============
print("\n========== FAZENDA SANTO ANTONIO (k=3) ==========")
stack_sa = stack_full.clip(santoAntonio)
training_sa = stack_sa.sample(region=aoi_santo, scale=10, numPixels=6000, seed=42)
clusterer_sa = ee.Clusterer.wekaKMeans(
    nClusters=3, init=1, maxIterations=30, seed=42).train(training_sa)
cls_sa = stack_sa.cluster(clusterer_sa).rename("cluster")

sigs_sa = {}
for c in [0,1,2]:
    sigs_sa[c] = stack_sa.updateMask(cls_sa.eq(c)).reduceRegion(
        ee.Reducer.mean(), aoi_santo, 10, maxPixels=1e9).getInfo()

print("Firmas de los 3 clusters:")
for c in [0,1,2]:
    s = sigs_sa[c]
    d = eucl(s, soya_sig)
    print(f"  C{c}: NDVI={s.get('NDVI',0):.3f} NDRE={s.get('NDRE',0):.3f} "
          f"EVI={s.get('EVI',0):.3f} B11={s.get('B11',0):.3f} dist-soya={d:.3f}")

# Asignacion:
#  - NDVI < 0.4  -> "no-cultivo" (suelo/APP)
#  - dist < 1.0  -> "soja"
#  - else        -> "milho"
labels_sa = {}
for c in [0,1,2]:
    s = sigs_sa[c]
    ndvi = s.get("NDVI", 0)
    d = eucl(s, soya_sig)
    if ndvi < 0.4:
        labels_sa[c] = "No-cultivo"
    elif d < 1.0:
        labels_sa[c] = "Soja"
    else:
        labels_sa[c] = "Milho"

# Areas
pa = ee.Image.pixelArea().divide(10000)
stats_sa = pa.addBands(cls_sa).reduceRegion(
    reducer=ee.Reducer.sum().group(groupField=1, groupName="cluster"),
    geometry=aoi_santo, scale=10, maxPixels=1e10).getInfo()

ha_cluster_sa = {0:0.0, 1:0.0, 2:0.0}
for g in stats_sa.get("groups", []):
    ha_cluster_sa[g["cluster"]] = g["sum"]

ha_soja_sa = sum(ha_cluster_sa[c] for c in [0,1,2] if labels_sa[c]=="Soja")
ha_milho_sa = sum(ha_cluster_sa[c] for c in [0,1,2] if labels_sa[c]=="Milho")
ha_nc_sa = sum(ha_cluster_sa[c] for c in [0,1,2] if labels_sa[c]=="No-cultivo")
ha_total_sa = sum(ha_cluster_sa.values())

print("\nAreas por cluster (Santo Antonio):")
for c in [0,1,2]:
    print(f"  C{c} {labels_sa[c]:12s}: {ha_cluster_sa[c]:6.2f} ha "
          f"({ha_cluster_sa[c]/ha_total_sa*100:.1f}%)")
print(f"\n  SOJA   plantada: {ha_soja_sa:.2f} ha")
print(f"  MILHO  plantado: {ha_milho_sa:.2f} ha")
print(f"  No-cultivo:      {ha_nc_sa:.2f} ha")

# ============ SAO FRANCISCO (validar que todo es soja con k=2) ============
print("\n========== FAZENDA SAO FRANCISCO (validacion k=2) ==========")
stack_sf = stack_full.clip(saoFrancisco)
training_sf = stack_sf.sample(region=aoi_sf, scale=10, numPixels=5000, seed=42)
clusterer_sf = ee.Clusterer.wekaKMeans(
    nClusters=2, init=1, maxIterations=30, seed=42).train(training_sf)
cls_sf = stack_sf.cluster(clusterer_sf).rename("cluster")

for c in [0,1]:
    s = stack_sf.updateMask(cls_sf.eq(c)).reduceRegion(
        ee.Reducer.mean(), aoi_sf, 10, maxPixels=1e9).getInfo()
    d = eucl(s, soya_sig)
    pa2 = ee.Image.pixelArea().divide(10000)
    cls_mask = cls_sf.eq(c).multiply(pa2)
    ha_c = cls_mask.reduceRegion(
        ee.Reducer.sum(), aoi_sf, 10, maxPixels=1e10).getInfo()["cluster"]
    lbl = ("Soja" if d < 1.0 else
           ("No-cultivo" if s.get("NDVI",0) < 0.4 else "Otro cultivo"))
    print(f"  C{c} {lbl:12s}: {ha_c:6.2f} ha  "
          f"NDVI={s.get('NDVI',0):.3f} dist-soya={d:.3f}")

# Firma media global SF vs firma soya
sig_sf_all = stack_sf.reduceRegion(
    ee.Reducer.mean(), aoi_sf, 10, maxPixels=1e9).getInfo()
d_sf_all = eucl(sig_sf_all, soya_sig)
print(f"\n  Firma promedio SF vs firma soya: dist={d_sf_all:.3f}  "
      f"NDVI={sig_sf_all.get('NDVI',0):.3f}")
print(f"  Area total SF: {ha_sf:.2f} ha (aoi) / shapefile oficial: 93.39 ha")

# ============ RESUMEN FINAL ============
print("\n" + "="*60)
print("RESUMEN PARA CONTRATO SAFRA 2025/2026")
print("="*60)
print(f"Fazenda Santo Antonio:")
print(f"   - Area total shapefile:  137.05 ha")
print(f"   - Area classificada:     {ha_total_sa:.2f} ha (AOI buffer-15m)")
print(f"   - MILHO:                 {ha_milho_sa:.2f} ha")
print(f"   - Soja:                  {ha_soja_sa:.2f} ha")
print(f"   - No-cultivo/APP:        {ha_nc_sa:.2f} ha")
print(f"\nFazenda Sao Francisco:")
print(f"   - Area total shapefile:  93.39 ha")
print(f"   - SOJA total (estimado): ~{ha_sf:.2f} ha")
print(f"\nTOTAL SOJA (para remuneracion):")
print(f"   = {ha_soja_sa:.2f} (SA) + 93.39 (SF) = {ha_soja_sa + 93.39:.2f} ha")
print(f"   = {(ha_soja_sa + 93.39)/2.42:.2f} alqueires paulistas (1 alq = 2.42 ha)")
print(f"\nAREA TOTAL CONTRATADA:")
print(f"   = 137.05 + 93.39 = {137.05 + 93.39:.2f} ha")
print(f"   = {(137.05 + 93.39)/2.42:.2f} alqueires paulistas")

# Guardar resumen json
out = {
    "fazenda_santo_antonio": {
        "area_total_shapefile_ha": 137.05,
        "area_classificada_ha": round(ha_total_sa,2),
        "milho_ha": round(ha_milho_sa,2),
        "soja_ha": round(ha_soja_sa,2),
        "no_cultivo_ha": round(ha_nc_sa,2),
    },
    "fazenda_sao_francisco": {
        "area_total_shapefile_ha": 93.39,
        "soja_ha": 93.39,
    },
    "soja_total_ha": round(ha_soja_sa + 93.39, 2),
    "area_contratada_ha": 230.44,
    "area_contratada_alqueires": round(230.44/2.42, 2),
    "soja_total_alqueires": round((ha_soja_sa+93.39)/2.42, 2),
    "n_imagenes_s2": n_img,
    "periodo": "2026-01-01 a 2026-02-25",
}
import json as _j
with open(HERE/"areas_contrato.json","w") as f:
    _j.dump(out, f, indent=2)
print(f"\n-> areas_contrato.json")
