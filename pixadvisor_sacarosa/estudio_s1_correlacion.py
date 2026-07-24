#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — ESTUDIO de correlación Sentinel-1 CR vs ranking S2
============================================================================
Antes de integrar S1 al composite, validamos empíricamente sobre los
131 lotes HIGH-caña si el Z-score de Cross-Ratio S1 correlaciona como
espera la teoría (den Besten 2021: r=-0.47 con sucrosa).

Si correlación negativa fuerte → incluir S1 al composite con peso 0.10
Si ambigua o positiva → NO incluir, usar S1 solo para detección de cosecha

Output:
  s1_correlacion_<fecha>.csv (todos los Z_CR + comparación con Priority_score)
  s1_correlacion_scatter.png (visualización con r de Pearson + Spearman)
============================================================================
"""
from __future__ import annotations
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, spearmanr

import ee

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

LOTES_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUTPUT_DIR  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2")
CSV_RANK    = OUTPUT_DIR / "ranking_prioridad_cosecha_2026-05-13.csv"

DIAS_ATRAS = 21
N_BASELINE_YEARS = 3
N_WORKERS = 6
Z_CAP = 3.0


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


def cargar_geom(lote_id):
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    diss = gdf.dissolve().to_crs("EPSG:4326")
    return ee.Geometry(diss.geometry.iloc[0].__geo_interface__)


def s1_indices(geom_ee, end_date_ee):
    """Devuelve dict con CR_actual, CR_baseline_mean, CR_baseline_std,
    Z_CR + VV equivalentes. Usa solo DESCENDING rel_orb=10
    (consistencia geométrica)."""
    def _col(start, end):
        return (ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(geom_ee)
                .filterDate(start, end)
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VV"))
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VH"))
                .filter(ee.Filter.eq("instrumentMode","IW"))
                .filter(ee.Filter.eq("orbitProperties_pass","DESCENDING"))
                .filter(ee.Filter.eq("relativeOrbitNumber_start", 10)))

    def _stats(col):
        n = col.size()
        med = ee.Image(ee.Algorithms.If(n.gt(0), col.median(), ee.Image(0)))
        cr = med.select("VH").subtract(med.select("VV")).rename("CR")
        img = med.addBands(cr).select(["VV","VH","CR"])
        return ee.Algorithms.If(
            n.gt(0),
            img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geom_ee, scale=20,
                maxPixels=int(1e9), bestEffort=True),
            ee.Dictionary({}))

    # Actual
    start_act = end_date_ee.advance(-DIAS_ATRAS, "day")
    col_act = _col(start_act, end_date_ee)
    n_act = col_act.size().getInfo()
    if n_act == 0:
        return {"n_act": 0}
    s_act = _stats(col_act).getInfo()

    # Baseline: mismo mes, N años atrás (server-side por lote)
    offsets = ee.List.sequence(1, N_BASELINE_YEARS)
    def per_year(o):
        o = ee.Number(o)
        ty = end_date_ee.get("year").subtract(o)
        m_start = ee.Date.fromYMD(ty, end_date_ee.get("month"), 1)
        m_end = m_start.advance(1, "month")
        col_h = _col(m_start, m_end)
        return ee.Feature(None, ee.Dictionary({"y": o, "n_h": col_h.size()})
                          .combine(ee.Dictionary(_stats(col_h))))
    feats = ee.FeatureCollection(offsets.map(per_year)).getInfo()

    crs, vvs, vhs = [], [], []
    for f in feats["features"]:
        p = f["properties"]
        if p.get("n_h", 0) > 0 and "CR" in p:
            crs.append(p["CR"]); vvs.append(p["VV"]); vhs.append(p["VH"])

    out = {
        "n_act": n_act,
        "VV_act": s_act.get("VV"),
        "VH_act": s_act.get("VH"),
        "CR_act": s_act.get("CR"),
        "n_baseline_years": len(crs),
    }
    if len(crs) >= 2:
        out["CR_baseline_mean"] = float(np.mean(crs))
        out["CR_baseline_std"]  = float(np.std(crs, ddof=1))
        out["VV_baseline_mean"] = float(np.mean(vvs))
        out["VV_baseline_std"]  = float(np.std(vvs, ddof=1))
        if out["CR_baseline_std"] > 1e-6:
            z_raw = (out["CR_act"] - out["CR_baseline_mean"]) / out["CR_baseline_std"]
            out["Z_CR_raw"] = z_raw
            out["Z_CR"] = max(-Z_CAP, min(Z_CAP, z_raw))
        if out["VV_baseline_std"] > 1e-6:
            z_raw = (out["VV_act"] - out["VV_baseline_mean"]) / out["VV_baseline_std"]
            out["Z_VV_raw"] = z_raw
            out["Z_VV"] = max(-Z_CAP, min(Z_CAP, z_raw))
    return out


def procesar_lote(row, end_date_ee, idx, total):
    lid = str(row["lote_id"])
    base = {"lote_id": lid,
            "Priority_score_S2": row["Priority_score"],
            "Rank_S2": row["Rank"],
            "Estado_S2": row["Estado_fenologico"],
            "area_ha": row["area_ha"]}
    try:
        geom = cargar_geom(lid)
        s1 = s1_indices(geom, end_date_ee)
        base.update(s1)
        log(f"[{idx}/{total}] {lid:14s} "
            f"Z_CR={base.get('Z_CR', float('nan')):+.2f} "
            f"S2_score={base['Priority_score_S2']:+.2f}")
    except Exception as e:
        log(f"[{idx}/{total}] {lid} × {e}")
        base["error"] = str(e)[:200]
    return base


def main():
    log("══ Estudio correlación S1 CR vs ranking S2 ══")
    try: ee.Initialize()
    except Exception: ee.Authenticate(); ee.Initialize()

    df_rank = pd.read_csv(CSV_RANK)
    log(f"Lotes a evaluar: {len(df_rank)}")

    end_dt = datetime.now(timezone.utc)
    end_ee = ee.Date(int(end_dt.timestamp()*1000))

    t0 = time.time()
    out = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(procesar_lote, r, end_ee, i, len(df_rank)): r
                for i, (_, r) in enumerate(df_rank.iterrows(), 1)}
        for fu in as_completed(futs):
            try: out.append(fu.result())
            except Exception as e: log(f"  err: {e}")

    df = pd.DataFrame(out).sort_values("Rank_S2")
    fecha = datetime.now().strftime("%Y-%m-%d")
    csv = OUTPUT_DIR / f"s1_correlacion_{fecha}.csv"
    df.to_csv(csv, index=False)
    log(f"  → {csv.name}")

    # Análisis estadístico
    print()
    log("══ ANÁLISIS DE CORRELACIÓN ══")
    valid = df.dropna(subset=["Z_CR","Priority_score_S2"])
    log(f"Lotes válidos: {len(valid)}/{len(df)}")

    if len(valid) >= 10:
        for col, signo_esperado in [("Z_CR","negativo"), ("Z_VV","negativo")]:
            v = valid.dropna(subset=[col])
            if len(v) < 10: continue
            r_p, p_p = pearsonr(v[col], v["Priority_score_S2"])
            r_s, p_s = spearmanr(v[col], v["Priority_score_S2"])
            log(f"\\n{col} vs Priority_score_S2 (signo esperado: {signo_esperado})")
            log(f"  Pearson  r = {r_p:+.3f}  (p={p_p:.4f})  n={len(v)}")
            log(f"  Spearman r = {r_s:+.3f}  (p={p_s:.4f})")
            if abs(r_p) < 0.20:
                log(f"  → CORRELACIÓN MUY DÉBIL — no incluir en composite")
            elif r_p < -0.30:
                log(f"  → correlación negativa fuerte (esperada) — INCLUIR")
            elif r_p > 0.30:
                log(f"  → correlación positiva (INESPERADA) — investigar antes de usar")
            else:
                log(f"  → correlación moderada — incluir con peso bajo (0.05)")

        # Plot
        fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=140)
        for i, col in enumerate(["Z_CR","Z_VV"]):
            v = valid.dropna(subset=[col])
            if len(v) < 5: continue
            r_p, _ = pearsonr(v[col], v["Priority_score_S2"])
            r_s, _ = spearmanr(v[col], v["Priority_score_S2"])
            ax = axes[i]
            ax.scatter(v[col], v["Priority_score_S2"], s=20, alpha=0.6,
                       c="#1B5E20", edgecolor="black", linewidth=0.3)
            ax.set_xlabel(f"{col} (S1)", fontsize=11)
            ax.set_ylabel("Priority_score (S2)", fontsize=11)
            ax.set_title(f"{col} vs Priority_score\\n"
                         f"Pearson r={r_p:+.3f} · Spearman r={r_s:+.3f} · n={len(v)}",
                         fontsize=11, fontweight="bold", color="#1B5E20")
            ax.axhline(0, color="gray", linestyle="--", alpha=0.5, linewidth=0.5)
            ax.axvline(0, color="gray", linestyle="--", alpha=0.5, linewidth=0.5)
            ax.grid(alpha=0.3)
        plt.suptitle("Correlación Sentinel-1 SAR vs Sentinel-2 Priority — Hacienda del Señor",
                     fontsize=12, fontweight="bold", color="#1B5E20")
        plt.tight_layout()
        png = OUTPUT_DIR / f"s1_correlacion_scatter_{fecha}.png"
        plt.savefig(png, dpi=140, bbox_inches="tight", facecolor="white")
        log(f"  → {png.name}")

    log(f"Done en {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
