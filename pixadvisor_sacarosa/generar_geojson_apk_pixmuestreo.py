#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — Generador GeoJSON para APK PIX Muestreo (Top 20)
============================================================================
Convierte los datos del muestreo Top 20 a formatos compatibles con la APK
PIX Muestreo (Pixadvisor) para que el técnico navegue a los puntos en
campo y registre samples.

SALIDAS:
  1) pix_muestreo_top20_PROYECTO.json
     → Formato "proyecto consolidado" (importProjectJSON de la APK).
       Crea 1 proyecto + 20 fields (lotes) + 100 puntos en un solo archivo.
       Cada field con boundary (zonas) y points (5 puntos GPS).
       Estructura óptima — la APK los reconoce y abre directo.

  2) geojson_por_lote/<rank>_<lote>.geojson
     → 20 GeoJSON estándar individuales (FeatureCollection).
       Cada uno con: polígono del lote + 5 puntos de muestreo.
       Cargar uno por lote desde APK ("Importar archivo").

  3) pix_muestreo_top20_CONSOLIDADO.geojson
     → 1 GeoJSON único con TODOS los lotes + puntos (FeatureCollection).
       Para visualizar todo de un vistazo en QGIS / Google Earth / APK.

USO:
  python generar_geojson_apk_pixmuestreo.py

CARGA EN APK (técnico):
  - Compartir el .json al teléfono (WhatsApp/email/Drive)
  - Abrir con la APK PIX Muestreo → "Importar archivo"
  - La APK crea proyecto + fields + puntos automáticamente
  - Tap en un lote → muestra mapa con borde + 5 puntos
  - Navegar a cada punto con GPS en vivo
  - Tomar samples (Brix sup/inf) en cada punto
============================================================================
"""
from __future__ import annotations
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
SAMPL_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\05-Muestreo-InSitu-Top20")
CSV_RANK   = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
                   r"\ranking_prioridad_v3_S2_S1_2026-05-15.csv")

OUT_ROOT = SAMPL_ROOT / "APK_PIX_MUESTREO"

CLIENTE = "Hacienda del Señor"
PROYECTO_NAME = f"HDS Muestreo CMI Top 20 - {datetime.now():%Y-%m-%d}"

N_TOP = 20


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


def cargar_zonas_lote(lote_id: str) -> gpd.GeoDataFrame:
    """Carga las 3-4 zonas de manejo internas del lote (sin disolver)."""
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    if not shp.exists():
        raise FileNotFoundError(shp)
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    return gdf.to_crs("EPSG:4326")  # WGS84 para APK


def cargar_puntos_lote(lote_id: str, rank: int) -> gpd.GeoDataFrame:
    """Carga los 5 puntos GPS generados para el lote."""
    shp = SAMPL_ROOT / f"{rank:02d}_{lote_id}" / f"puntos_muestreo_{lote_id}.shp"
    if not shp.exists():
        raise FileNotFoundError(shp)
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    return gdf.to_crs("EPSG:4326")


# ════════════════════════════════════════════════════════════════════════════
# 1) FORMATO 1 — Proyecto JSON consolidado (formato APK óptimo)
# ════════════════════════════════════════════════════════════════════════════
def build_proyecto_consolidado(top20: pd.DataFrame, out_path: Path):
    """Estructura compatible con app.js importProjectJSON()."""
    lotes_arr = []
    total_points = 0

    for _, r in top20.iterrows():
        lote_id = str(r["lote_id"])
        rank = int(r["Rank_v3"])
        try:
            zonas_gdf = cargar_zonas_lote(lote_id)
            puntos_gdf = cargar_puntos_lote(lote_id, rank)
        except FileNotFoundError as e:
            log(f"  ! {lote_id}: {e}"); continue

        # Zonas como FeatureCollection (boundary del field)
        zonas_features = []
        for _, zr in zonas_gdf.iterrows():
            props_zona = {
                "zona": str(zr.get("zona", "")),
                "nombre": str(zr.get("nombre", "")),
                "clase": str(zr.get("nombre", "")),  # APK busca 'clase' como nombre zona
                "color": str(zr.get("color", "#888")),
                "area_ha": float(zr.get("area_ha", 0)),
                "pct": float(zr.get("pct", 0)),
            }
            zonas_features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(zr.geometry),
                "properties": props_zona,
            })
        zonas_fc = {
            "type": "FeatureCollection",
            "features": zonas_features,
        }

        # Puntos (formato esperado por APK)
        puntos_arr = []
        for _, pr in puntos_gdf.iterrows():
            n = int(pr["punto_n"])
            puntos_arr.append({
                "id": f"{lote_id}_P{n}",
                "name": f"P{n}",
                "lat": float(pr.geometry.y),
                "lng": float(pr.geometry.x),
                "zona": "muestreo_CMI",
                "tipo": "principal",
                "status": "pending",
                "properties": {
                    "punto_n": n,
                    "protocolo": "SASRI/CONSECANA — Brix sup/inf 10 tallos",
                    "objetivo": "CMI = (BS/BI)*100 para validar prioridad cosecha",
                },
            })
            total_points += 1

        lote_dict = {
            "id": lote_id,
            "name": f"Lote {lote_id} (Rank #{rank})",
            "area_ha": float(r["area_ha"]),
            "metadata": {
                "rank_v3": rank,
                "priority_score": float(r["Priority_score_v3"]),
                "estado_fenologico": str(r["Estado_fenologico_v3"]),
                "fecha_imagen_s2": str(r["fecha_imagen"]),
                "z_ndwi": float(r.get("NDWI_zscore", 0) or 0),
                "z_cire": float(r.get("CIRE_zscore", 0) or 0),
                "z_vv_s1": float(r.get("VV_zscore", 0) or 0),
                "gdd_acum": float(r.get("GDD_acum", 0) or 0),
            },
            "zonas": zonas_fc,
            "puntos": puntos_arr,
        }
        lotes_arr.append(lote_dict)

    proyecto = {
        "project": {
            "name": PROYECTO_NAME,
            "client": CLIENTE,
            "totalLotes": len(lotes_arr),
            "totalPoints": total_points,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "descripcion": (
                "Top 20 lotes prioridad cosecha según ranking satelital v3 "
                "(Sentinel-2 + Sentinel-1 SAR + ERA5). Validar CMI in-situ "
                "con refractómetro: 5 puntos × 10 tallos = 50 muestras por lote."
            ),
            "metodologia": "Pixadvisor v3 (S2+S1+ERA5) + SASRI/CONSECANA CMI",
            "version_pipeline": "v3_S2_S1",
        },
        "lotes": lotes_arr,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(proyecto, f, ensure_ascii=False, indent=2)
    return len(lotes_arr), total_points


# ════════════════════════════════════════════════════════════════════════════
# 2) FORMATO 2 — GeoJSON estándar individual por lote
# ════════════════════════════════════════════════════════════════════════════
def build_geojson_por_lote(top20: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    for _, r in top20.iterrows():
        lote_id = str(r["lote_id"])
        rank = int(r["Rank_v3"])
        try:
            zonas_gdf = cargar_zonas_lote(lote_id)
            puntos_gdf = cargar_puntos_lote(lote_id, rank)
        except FileNotFoundError: continue

        features = []
        # Cada zona como Feature Polygon (con propiedades zona/clase para
        # que la APK las colorée como management zones)
        for _, zr in zonas_gdf.iterrows():
            features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(zr.geometry),
                "properties": {
                    "lote_id": lote_id,
                    "rank_v3": rank,
                    "area_ha": float(r["area_ha"]),
                    "estado_fenologico": str(r["Estado_fenologico_v3"]),
                    "priority_score": float(r["Priority_score_v3"]),
                    "zona": str(zr.get("zona", "")),
                    "nombre_zona": str(zr.get("nombre", "")),
                    "clase": str(zr.get("nombre", "")),
                    "color": str(zr.get("color", "#888")),
                    "tipo": "boundary_zona",
                },
            })
        # Cada punto como Feature Point
        for _, pr in puntos_gdf.iterrows():
            n = int(pr["punto_n"])
            features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(pr.geometry),
                "properties": {
                    "lote_id": lote_id,
                    "punto_n": n,
                    "name": f"{lote_id}_P{n}",
                    "tipo": "muestreo_CMI",
                    "status": "pending",
                    "protocolo": "Brix superior + Brix inferior · 10 tallos",
                },
            })

        fc = {
            "type": "FeatureCollection",
            "name": f"Lote {lote_id} — Rank #{rank}",
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
            },
            "features": features,
        }
        out_path = out_dir / f"{rank:02d}_{lote_id}.geojson"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fc, f, ensure_ascii=False, indent=2)
        n_ok += 1
    return n_ok


# ════════════════════════════════════════════════════════════════════════════
# 3) FORMATO 3 — GeoJSON consolidado único (TODOS los lotes + puntos)
# ════════════════════════════════════════════════════════════════════════════
def build_geojson_consolidado(top20: pd.DataFrame, out_path: Path):
    features = []
    for _, r in top20.iterrows():
        lote_id = str(r["lote_id"])
        rank = int(r["Rank_v3"])
        try:
            zonas_gdf = cargar_zonas_lote(lote_id)
            puntos_gdf = cargar_puntos_lote(lote_id, rank)
        except FileNotFoundError: continue
        for _, zr in zonas_gdf.iterrows():
            features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(zr.geometry),
                "properties": {
                    "lote_id": lote_id,
                    "rank_v3": rank,
                    "tipo": "boundary",
                    "zona": str(zr.get("zona", "")),
                    "nombre_zona": str(zr.get("nombre", "")),
                    "color": str(zr.get("color", "#888")),
                    "priority_score": float(r["Priority_score_v3"]),
                    "estado": str(r["Estado_fenologico_v3"]),
                },
            })
        for _, pr in puntos_gdf.iterrows():
            n = int(pr["punto_n"])
            features.append({
                "type": "Feature",
                "geometry": shapely.geometry.mapping(pr.geometry),
                "properties": {
                    "lote_id": lote_id,
                    "rank_v3": rank,
                    "tipo": "muestreo_CMI",
                    "name": f"{lote_id}_P{n}",
                    "punto_n": n,
                    "status": "pending",
                },
            })
    fc = {
        "type": "FeatureCollection",
        "name": "Pixadvisor Top 20 Muestreo CMI Hacienda del Señor",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        },
        "metadata": {
            "cliente": CLIENTE,
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "n_lotes": len(top20),
            "metodologia": "Pixadvisor v3 (S2+S1+ERA5) + SASRI/CONSECANA",
        },
        "features": features,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)
    return len(features)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — GeoJSON para APK PIX Muestreo ══")
    if not CSV_RANK.exists():
        log(f"ERROR: falta {CSV_RANK}"); sys.exit(1)

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV_RANK)
    df["lote_id"] = df["lote_id"].astype(str)
    top20 = df.sort_values("Rank_v3").head(N_TOP).reset_index(drop=True)
    log(f"Top {N_TOP} lotes a exportar")

    # 1) Proyecto consolidado APK
    log("\n[1/3] Generando proyecto consolidado para APK...")
    out_proj = OUT_ROOT / "pix_muestreo_top20_PROYECTO.json"
    n_lotes, n_pts = build_proyecto_consolidado(top20, out_proj)
    size_kb = out_proj.stat().st_size / 1024
    log(f"  ✓ {out_proj.name} ({size_kb:.0f} KB)")
    log(f"    {n_lotes} lotes · {n_pts} puntos GPS")

    # 2) GeoJSON por lote
    log("\n[2/3] Generando GeoJSON individual por lote...")
    out_dir_indiv = OUT_ROOT / "geojson_por_lote"
    n_ok = build_geojson_por_lote(top20, out_dir_indiv)
    log(f"  ✓ {n_ok} GeoJSON individuales en {out_dir_indiv.name}/")

    # 3) GeoJSON consolidado universal
    log("\n[3/3] Generando GeoJSON consolidado universal...")
    out_cons = OUT_ROOT / "pix_muestreo_top20_CONSOLIDADO.geojson"
    n_features = build_geojson_consolidado(top20, out_cons)
    size_kb2 = out_cons.stat().st_size / 1024
    log(f"  ✓ {out_cons.name} ({size_kb2:.0f} KB · {n_features} features)")

    # 4) ZIP empaquetado todo
    import zipfile
    zip_out = OUT_ROOT / "Pixadvisor_APKPixMuestreo_Top20.zip"
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_proj, out_proj.name)
        zf.write(out_cons, out_cons.name)
        for f in sorted(out_dir_indiv.glob("*.geojson")):
            zf.write(f, f"geojson_por_lote/{f.name}")
    log(f"\nZIP final: {zip_out.name} ({zip_out.stat().st_size/1024:.0f} KB)")
    log(f"OK — Todas las salidas en {OUT_ROOT}")
    log("\nCómo cargar en APK PIX Muestreo:")
    log("  1. Enviar pix_muestreo_top20_PROYECTO.json al celular")
    log("  2. APK → Importar archivo → seleccionar el JSON")
    log("  3. Se crea proyecto con 20 fields (lotes) + 100 puntos GPS")
    log("  4. Tap en un lote → ver borde + 5 puntos en el mapa")
    log("  5. Navegar a cada punto con GPS, tomar muestra Brix sup/inf")


if __name__ == "__main__":
    main()
