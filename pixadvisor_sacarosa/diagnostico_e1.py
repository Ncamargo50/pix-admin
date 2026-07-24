#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnóstico exploratorio: serie NDVI mensual últimos 14 meses
Compara E1 (cliente: pasto) vs M1, M2 (Pol más alto) vs MONTE (forest).
Genera gráfico comparativo para inspección visual de firmas.
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime, timezone

import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import ee

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ee.Initialize()

ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
            r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUT_PNG = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2\diagnostico_E1_firma.png")
OUT_CSV = OUT_PNG.with_suffix(".csv")

# Lotes a comparar (cliente confirmó E1 = pasto)
LOTES_TEST = ["E1", "M1", "M2", "1", "MONTE", "4A9", "PISTA"]
MESES_ATRAS = 14


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


def cargar_geom(lote_id: str):
    shp = ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    if not shp.exists():
        print(f"  ! sin shapefile: {shp}")
        return None
    gdf = gpd.read_file(shp).dissolve()
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    gdf_w = gdf.to_crs("EPSG:4326")
    return ee.Geometry(gdf_w.geometry.iloc[0].__geo_interface__)


def serie_ndvi_mensual(geom_ee, end_date: datetime, n_meses: int):
    """Devuelve list de (fecha, ndvi_mean, ndvi_min, ndvi_max, n_imgs)."""
    end_ee = ee.Date(int(end_date.timestamp() * 1000))
    out = []
    for offset in range(n_meses, 0, -1):
        m_end = end_ee.advance(-(offset - 1), "month")
        m_start = end_ee.advance(-offset, "month")
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
               .filterBounds(geom_ee)
               .filterDate(m_start, m_end)
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
               .map(lambda im: im.updateMask(
                   im.select("SCL").eq(4).Or(im.select("SCL").eq(5))
                                          .Or(im.select("SCL").eq(6)))))
        n = col.size().getInfo()
        if n == 0:
            out.append({"fecha": m_start.format("YYYY-MM").getInfo(),
                        "ndvi_mean": None, "n_imgs": 0})
            continue
        mosaic = col.median()
        nir = mosaic.select("B8").divide(10000)
        red = mosaic.select("B4").divide(10000)
        ndvi = nir.subtract(red).divide(nir.add(red).max(1e-6)).rename("NDVI")
        st = ndvi.reduceRegion(
            reducer=ee.Reducer.mean()
                .combine(ee.Reducer.minMax(), "", True)
                .combine(ee.Reducer.stdDev(), "", True),
            geometry=geom_ee, scale=20, maxPixels=int(1e9), bestEffort=True
        ).getInfo()
        out.append({
            "fecha": m_start.format("YYYY-MM").getInfo(),
            "ndvi_mean": st.get("NDVI_mean"),
            "ndvi_min": st.get("NDVI_min"),
            "ndvi_max": st.get("NDVI_max"),
            "ndvi_std": st.get("NDVI_stdDev"),
            "n_imgs": n,
        })
    return out


def main():
    end_date = datetime.now(timezone.utc)
    print(f"Serie NDVI {MESES_ATRAS} meses hasta {end_date:%Y-%m-%d}")
    print(f"Lotes test: {LOTES_TEST}\n")

    todas = {}
    for lid in LOTES_TEST:
        print(f"[{lid}]")
        g = cargar_geom(lid)
        if g is None: continue
        s = serie_ndvi_mensual(g, end_date, MESES_ATRAS)
        todas[lid] = s
        for r in s:
            v = r["ndvi_mean"]
            v_str = f"{v:.3f}" if v is not None else "  —  "
            print(f"  {r['fecha']}  NDVI={v_str}  n={r['n_imgs']}")
        print()

    # Tabla
    rows = []
    for lid, s in todas.items():
        for r in s:
            rows.append({"lote": lid, **r})
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print(f"CSV → {OUT_CSV}")

    # Gráfico comparativo
    fig, ax = plt.subplots(figsize=(13, 7), dpi=150)
    colores = {"E1": "tab:red", "M1": "tab:green", "M2": "darkgreen",
               "1": "tab:blue", "MONTE": "saddlebrown",
               "4A9": "tab:orange", "PISTA": "gray"}
    for lid, s in todas.items():
        fechas = [r["fecha"] for r in s]
        vals = [r["ndvi_mean"] if r["ndvi_mean"] is not None else np.nan for r in s]
        ax.plot(fechas, vals, marker="o", label=lid,
                color=colores.get(lid, "black"), linewidth=2, markersize=6)

    ax.set_title("Firma fenológica NDVI — comparación lote por lote\n"
                 "Sentinel-2 últimos 14 meses · Hacienda del Señor",
                 fontsize=13, fontweight="bold", color="#1B5E20")
    ax.set_ylabel("NDVI medio mensual", fontsize=11)
    ax.set_xlabel("Mes")
    ax.set_ylim(0, 1)
    ax.axhline(0.3, color="brown", linestyle="--", alpha=0.4,
               label="0.30 = suelo desnudo / reforma")
    ax.axhline(0.6, color="green", linestyle="--", alpha=0.4,
               label="0.60 = vegetación activa")
    ax.legend(loc="lower left", ncol=2, fontsize=9)
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"PNG → {OUT_PNG}")


if __name__ == "__main__":
    main()
