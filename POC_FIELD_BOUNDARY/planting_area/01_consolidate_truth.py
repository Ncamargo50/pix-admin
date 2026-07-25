"""
Consolida los 213 shapefiles de Hacienda Del Senor + Santo Antonio en un
truth master GeoJSON listo para entrenamiento.

Salida:
    output/truth_master.geojson  (Polygons en EPSG:4326 con metadata)
    output/truth_stats.json
"""
from __future__ import annotations

import os
import json
import warnings
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"
warnings.filterwarnings("ignore")

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Polygon

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

# Fuentes de truth
HDS_DIR = Path(r"C:/Users/Usuario/Desktop/PIXADVISOR/01-CLIENTES-PROYECTOS/Hacienda-Del-Senor/02-Lotes/Lotes-Hacienda-Del-Senor")
SANTO_ANTONIO_SHP = Path(r"D:/PIXADVISOR_AGENT_WORKSPACE/_orphan_files/shp/Santo_Antonio.shp")

MIN_AREA_HA = 0.5
MAX_AREA_HA = 500.0


def _utm_for_bounds(bounds):
    """Decide UTM apropiado segun longitud media."""
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    south = lat_mid < 0
    return f"EPSG:{32700 + zone if south else 32600 + zone}"


def load_hds():
    print(f">>> Cargando HDS de {HDS_DIR}")
    shps = sorted(HDS_DIR.glob("*.shp"))
    gdfs = []
    for shp in shps:
        try:
            g = gpd.read_file(shp)
            if g.empty: continue
            if g.crs is None:
                g = g.set_crs("EPSG:4326")
            g = g.to_crs("EPSG:4326")
            g["source"] = "HDS"
            g["lote_name"] = shp.stem
            gdfs.append(g)
        except Exception as e:
            print(f"  WARN {shp.stem}: {e}")
    combined = pd.concat(gdfs, ignore_index=True)
    return gpd.GeoDataFrame(combined, geometry="geometry", crs="EPSG:4326")


def load_santo_antonio():
    print(f">>> Cargando Santo Antonio")
    g = gpd.read_file(SANTO_ANTONIO_SHP)
    if g.crs is None:
        g = g.set_crs("EPSG:32722")  # UTM 22S Brasil Parana
    g = g.to_crs("EPSG:4326")
    g["source"] = "SANTO_ANTONIO"
    g["lote_name"] = "santo_antonio_full"
    return g


def main():
    hds = load_hds()
    sa = load_santo_antonio()

    combined = pd.concat([hds, sa], ignore_index=True)
    combined = gpd.GeoDataFrame(combined, geometry="geometry", crs="EPSG:4326")

    # Filtrar solo Polygons (LineStrings descartados)
    keep = combined.geom_type.isin(["Polygon", "MultiPolygon"])
    print(f"    Filtro tipo: {keep.sum()}/{len(combined)} (descartados {(~keep).sum()} non-Polygon)")
    combined = combined[keep].copy()

    # Convertir MultiPolygon a Polygons individuales (mejor para training)
    explode = combined.explode(index_parts=False).reset_index(drop=True)
    print(f"    Explode multi -> single: {len(combined)} -> {len(explode)}")

    # Calcular area en UTM regional (HDS y SA en zonas distintas)
    explode["area_ha"] = 0.0
    for src in explode["source"].unique():
        mask = explode["source"] == src
        sub = explode[mask]
        utm = _utm_for_bounds(sub.total_bounds)
        sub_utm = sub.to_crs(utm)
        explode.loc[mask, "area_ha"] = sub_utm.area.values / 10_000
        print(f"    {src}: UTM={utm}, n={len(sub)}, area={sub_utm.area.sum()/10000:.1f} ha")

    # Filtrar por area razonable
    before = len(explode)
    explode = explode[(explode["area_ha"] >= MIN_AREA_HA) &
                       (explode["area_ha"] <= MAX_AREA_HA)].copy()
    print(f"    Filtro area [{MIN_AREA_HA}, {MAX_AREA_HA}] ha: {before} -> {len(explode)}")

    # Validar geometrias
    from shapely import make_valid
    explode["geometry"] = explode.geometry.apply(make_valid).buffer(0)
    explode = explode[~explode.geometry.is_empty].copy()
    explode = explode.reset_index(drop=True)

    # Guardar
    out_geo = OUT / "truth_master.geojson"
    cols = ["source", "lote_name", "area_ha", "geometry"]
    explode[cols].to_file(out_geo, driver="GeoJSON")
    print(f"<<< {out_geo}")

    # Stats
    stats = {
        "total_features": len(explode),
        "total_area_ha": float(explode["area_ha"].sum()),
        "by_source": {
            src: {
                "count": int((explode["source"] == src).sum()),
                "total_ha": float(explode[explode["source"] == src]["area_ha"].sum()),
                "min_ha": float(explode[explode["source"] == src]["area_ha"].min()),
                "max_ha": float(explode[explode["source"] == src]["area_ha"].max()),
                "median_ha": float(explode[explode["source"] == src]["area_ha"].median()),
                "bounds": [float(b) for b in explode[explode["source"] == src].total_bounds],
            }
            for src in explode["source"].unique()
        },
    }
    out_stats = OUT / "truth_stats.json"
    out_stats.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"<<< {out_stats}")
    print()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
