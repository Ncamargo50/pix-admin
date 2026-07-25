"""
POC Field Boundary - Step 1: Prepara AOI Santo Antonio.

Lee el shapefile de verdad (truth), lo convierte a WGS84 (lat/lon),
exporta GeoJSON limpio, BBOX para herramientas externas, y CSV
con vertices simplificados para pegar en GEE Code Editor.

Uso:
    python 01_prepare_aoi.py

Salida:
    output/santo_antonio_truth_wgs84.geojson   <- truth en lat/lon
    output/santo_antonio_truth_utm.geojson     <- truth en UTM 22S
    output/santo_antonio_bbox.txt              <- bbox W S E N para FTW Explorer
    output/santo_antonio_gee_polygon.txt       <- coords simplificadas para pegar en GEE
"""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"
import geopandas as gpd
from shapely.geometry import mapping

ROOT = Path(__file__).parent
TRUTH_SHP = Path("D:/PIXADVISOR_AGENT_WORKSPACE/_orphan_files/shp/Santo_Antonio.shp")
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

# Las coords del shp estan en UTM 22S (false northing 10000000) - Parana/SP, Brasil.
# Coords ejemplo: 534526 E, 7401090 N => lat ~-23.47, lon ~-50.66 (matches GEE script)
ASSUMED_CRS = "EPSG:32722"  # UTM Zone 22S, WGS84

print(f">>> Leyendo {TRUTH_SHP}")
gdf = gpd.read_file(TRUTH_SHP)
if gdf.crs is None:
    print(f"    Sin CRS embebido, asumiendo {ASSUMED_CRS}")
    gdf = gdf.set_crs(ASSUMED_CRS)

# UTM (metros, calcular area precisa)
gdf_utm = gdf.to_crs(ASSUMED_CRS)
total_ha_utm = gdf_utm.area.sum() / 10_000

# WGS84 (lat/lon, para herramientas de delineation)
gdf_wgs = gdf.to_crs("EPSG:4326")
bounds = gdf_wgs.total_bounds  # W, S, E, N

print(f"    Features: {len(gdf)}")
print(f"    Area total: {total_ha_utm:.2f} ha")
print(f"    BBOX WGS84 (W,S,E,N): {bounds[0]:.6f}, {bounds[1]:.6f}, {bounds[2]:.6f}, {bounds[3]:.6f}")

# 1. GeoJSON WGS84
out_wgs = OUT / "santo_antonio_truth_wgs84.geojson"
gdf_wgs.to_file(out_wgs, driver="GeoJSON")
print(f"<<< {out_wgs}")

# 2. GeoJSON UTM (para calculos precisos)
out_utm = OUT / "santo_antonio_truth_utm.geojson"
gdf_utm.to_file(out_utm, driver="GeoJSON")
print(f"<<< {out_utm}")

# 3. BBOX en formato listo para FTW Explorer / Sentinel Hub / EOSDA
buffer = 0.0015  # ~165 m extra para que la deteccion no "corte" en el borde
bbox_padded = (bounds[0] - buffer, bounds[1] - buffer,
               bounds[2] + buffer, bounds[3] + buffer)
bbox_txt = OUT / "santo_antonio_bbox.txt"
bbox_txt.write_text(
    "Santo Antonio AOI - BBOX para herramientas externas\n"
    f"AREA REAL (truth): {total_ha_utm:.2f} ha en {len(gdf)} feature(s)\n\n"
    "FORMATO 1 (WGS84 lat/lon, sin buffer):\n"
    f"  W={bounds[0]:.6f}\n  S={bounds[1]:.6f}\n  E={bounds[2]:.6f}\n  N={bounds[3]:.6f}\n\n"
    "FORMATO 2 (con buffer 165m, recomendado para FTW Explorer):\n"
    f"  W={bbox_padded[0]:.6f}\n  S={bbox_padded[1]:.6f}\n"
    f"  E={bbox_padded[2]:.6f}\n  N={bbox_padded[3]:.6f}\n\n"
    "FORMATO 3 (Sentinel Hub, geojson polygon):\n"
    f"  [[{bbox_padded[0]},{bbox_padded[1]}],[{bbox_padded[2]},{bbox_padded[1]}],"
    f"[{bbox_padded[2]},{bbox_padded[3]}],[{bbox_padded[0]},{bbox_padded[3]}],"
    f"[{bbox_padded[0]},{bbox_padded[1]}]]\n\n"
    "FORMATO 4 (Google Maps URL para inspeccion visual):\n"
    f"  https://www.google.com/maps/@{(bounds[1]+bounds[3])/2:.6f},"
    f"{(bounds[0]+bounds[2])/2:.6f},15z/data=!3m1!1e3\n",
    encoding="utf-8"
)
print(f"<<< {bbox_txt}")

# 4. Polygon coords simplificadas para pegar directo en el GEE Code Editor
gdf_simple = gdf_wgs.copy()
gdf_simple["geometry"] = gdf_simple.geometry.simplify(tolerance=0.00005, preserve_topology=True)
coords_per_feature = []
for geom in gdf_simple.geometry:
    g = mapping(geom)
    if g["type"] == "Polygon":
        coords_per_feature.append(g["coordinates"])
    elif g["type"] == "MultiPolygon":
        for poly in g["coordinates"]:
            coords_per_feature.append(poly)

gee_txt = OUT / "santo_antonio_gee_polygon.txt"
gee_lines = ["// Pegar en GEE Code Editor:\n"]
for i, rings in enumerate(coords_per_feature):
    gee_lines.append(f"var aoi_part_{i+1} = ee.Geometry.Polygon({json.dumps(rings)});\n")
gee_lines.append(f"\nvar aoi = ee.Geometry.MultiPolygon([\n")
for i in range(len(coords_per_feature)):
    gee_lines.append(f"  aoi_part_{i+1}.coordinates(),\n")
gee_lines.append("]);\n")
gee_txt.write_text("".join(gee_lines), encoding="utf-8")
print(f"<<< {gee_txt}")

print("\n=== AOI listo. Pasos siguientes ===")
print("  - Abrir output/santo_antonio_bbox.txt -> usar BBOX en FTW Explorer (https://fieldsofthe.world/ftw-inference-app)")
print("  - Copiar output/santo_antonio_gee_polygon.txt al GEE Code Editor + correr 02_gee_snic_canny.js")
print("  - Correr 03_run_delineate_anything.py para SOTA local")
print("  - Correr 04_compare_iou.py output/<candidate>.geojson para evaluar IoU vs truth")
