#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — RANKING DE PRIORIDAD DE COSECHA v3 (S2 + S1 VV)
============================================================================
Integra Sentinel-1 SAR (banda VV) al composite v2.
Validación empírica sobre 131 lotes Hacienda del Señor:
  Z_VV vs Priority_score_S2: Spearman r = -0.529 (p<0.001) — INCLUIDO
  Z_CR vs Priority_score_S2: signo invertido vs literatura — NO incluido

Score v3 = -0.25·Z_NDWI -0.15·Z_NDMI -0.20·Z_CIRE +0.10·Z_PSRI
            -0.10·Z_VV_S1 +0.20·Z_GDD

Pesos verificados:
  NDWI Gao   0.25 (Leandro 2024 DOI 10.3390/crops4030024)
  NDMI       0.15 (Hajeb 2023 DOI 10.1016/j.jag.2022.103168)
  CIRE       0.20 (Bocca 2024 DOI 10.1007/s12355-024-01468-z)
  PSRI       0.10 (Merzlyak 1999 DOI 10.1034/j.1399-3054.1999.106119.x)
  VV S1      0.10 (validación empírica local 2026-05-15, ver s1_correlacion)
  GDD T18    0.20 (Inman-Bamber 1994 DOI 10.1016/0378-4290(94)90051-5)

S1 specifics: COPERNICUS/S1_GRD, IW DESCENDING rel_orb=10, dual-pol VV+VH
              (consistencia geométrica obligatoria)
============================================================================
"""
from __future__ import annotations
import re, sys, time, warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform
import ee

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
warnings.filterwarnings("ignore")

# Reuso compute_ranking_prioridad como base
sys.path.insert(0, str(Path(__file__).parent))
import compute_ranking_prioridad as cp

# ════════════════════════════════════════════════════════════════════════════
# CONFIG v3
# ════════════════════════════════════════════════════════════════════════════
WEIGHTS_V3 = {
    "NDWI": 0.25,
    "NDMI": 0.15,
    "CIRE": 0.20,
    "PSRI": 0.10,
    "VV":   0.10,   # ← NUEVO Sentinel-1
    "GDD":  0.20,
}
S1_REL_ORBIT = 10
S1_PASS = "DESCENDING"
Z_CAP = 3.0
N_BASELINE_YEARS = 3
DIAS_ATRAS = 21


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


# ════════════════════════════════════════════════════════════════════════════
# S1 features para un lote
# ════════════════════════════════════════════════════════════════════════════
def s1_features(geom_ee, end_date_ee):
    """Z_VV (capeado) sobre baseline 3 años mismo mes."""
    def _col(start, end):
        return (ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(geom_ee)
                .filterDate(start, end)
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VV"))
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation","VH"))
                .filter(ee.Filter.eq("instrumentMode","IW"))
                .filter(ee.Filter.eq("orbitProperties_pass", S1_PASS))
                .filter(ee.Filter.eq("relativeOrbitNumber_start", S1_REL_ORBIT)))

    # Actual
    col_act = _col(end_date_ee.advance(-DIAS_ATRAS, "day"), end_date_ee)
    n_act = col_act.size().getInfo()
    out = {"S1_n_act": n_act}
    if n_act == 0:
        return out

    vv_act = col_act.select("VV").median().reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.count(),"",True),
        geometry=geom_ee, scale=20, maxPixels=int(1e9), bestEffort=True
    ).getInfo()
    vv_a_mean = vv_act.get("VV_mean") if vv_act else None
    vv_a_n    = vv_act.get("VV_count", 0) if vv_act else 0
    out["VV_actual"] = vv_a_mean
    out["VV_actual_n"] = vv_a_n

    # Baseline (server-side por año)
    offsets = ee.List.sequence(1, N_BASELINE_YEARS)
    def per_year(o):
        o = ee.Number(o)
        ty = end_date_ee.get("year").subtract(o)
        m_start = ee.Date.fromYMD(ty, end_date_ee.get("month"), 1)
        m_end = m_start.advance(1, "month")
        col_h = _col(m_start, m_end)
        n_h = col_h.size()
        composite = ee.Image(ee.Algorithms.If(n_h.gt(0), col_h.select("VV").median(), ee.Image(0)))
        m = ee.Algorithms.If(
            n_h.gt(0),
            composite.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geom_ee, scale=20,
                maxPixels=int(1e9), bestEffort=True).get("VV"),
            None)
        return ee.Feature(None, {"y": o, "n_h": n_h, "vv": m})

    feats = ee.FeatureCollection(offsets.map(per_year)).getInfo()
    vvs = []
    for f in feats["features"]:
        p = f["properties"]
        if p.get("n_h", 0) > 0 and p.get("vv") is not None:
            vvs.append(p["vv"])

    out["VV_baseline_n_years"] = len(vvs)
    if len(vvs) >= 2:
        out["VV_baseline_mean"] = float(np.mean(vvs))
        out["VV_baseline_std"]  = float(np.std(vvs, ddof=1))
        if out["VV_baseline_std"] > 1e-6 and vv_a_mean is not None:
            z_raw = (vv_a_mean - out["VV_baseline_mean"]) / out["VV_baseline_std"]
            out["VV_zscore_raw"] = z_raw
            out["VV_zscore"] = max(-Z_CAP, min(Z_CAP, z_raw))
    return out


# ════════════════════════════════════════════════════════════════════════════
# WORKER por lote — extiende compute_ranking_prioridad.procesar_lote con S1
# ════════════════════════════════════════════════════════════════════════════
def procesar_lote_v3(lote: dict, end_date_ee, end_date_dt, idx, total):
    base = cp.procesar_lote(lote, end_date_ee, end_date_dt, idx, total)
    if base is None or "error" in base:
        return base

    # Agregar S1 VV — cp.cargar_geom espera lote_id (string), no path
    try:
        geom_ee, _ = cp.cargar_geom(str(base["lote_id"]))
        s1 = s1_features(geom_ee, end_date_ee)
        base.update(s1)
    except Exception as e:
        log(f"  [{idx}] {base['lote_id']} S1 err: {e}")
    return base


# ════════════════════════════════════════════════════════════════════════════
# COMPOSITE v3 + bootstrap
# ════════════════════════════════════════════════════════════════════════════
def calcular_priority_v3(df: pd.DataFrame) -> pd.DataFrame:
    """Composite v3 con S1 VV. Renormaliza pesos disponibles si falta alguno."""
    # GDD relativo entre lotes
    valid_gdd = df["GDD_acum"].notna()
    if valid_gdd.sum() > 1:
        m = df.loc[valid_gdd, "GDD_acum"].mean()
        s = df.loc[valid_gdd, "GDD_acum"].std()
        df["GDD_zscore"] = (df["GDD_acum"] - m) / s if s > 1e-6 else 0
    else:
        df["GDD_zscore"] = 0

    signs = {"NDWI":-1, "NDMI":-1, "CIRE":-1, "PSRI":+1, "VV":-1, "GDD":+1}

    def score(r):
        sources = {
            "NDWI": r.get("NDWI_zscore"),
            "NDMI": r.get("NDMI_zscore"),
            "CIRE": r.get("CIRE_zscore"),
            "PSRI": r.get("PSRI_zscore"),
            "VV":   r.get("VV_zscore"),
            "GDD":  r.get("GDD_zscore"),
        }
        wts_ok = {}
        for k, v in sources.items():
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            wts_ok[k] = WEIGHTS_V3[k]
        if not wts_ok: return np.nan
        wsum = sum(wts_ok.values())
        wts = {k: w/wsum for k, w in wts_ok.items()}
        s = 0.0
        for k, w in wts.items():
            s += signs[k] * sources[k] * w
        return s

    df["Priority_score_v3"] = df.apply(score, axis=1)
    df["Rank_v3"] = df["Priority_score_v3"].rank(ascending=False, method="min")
    return df


def bootstrap_v3(df, n_iter=200):
    rng = np.random.default_rng(42)
    rank_matrix = np.full((n_iter, len(df)), np.nan)
    for it in range(n_iter):
        df_iter = df.copy()
        for k in ["NDWI","NDMI","CIRE","PSRI","VV"]:
            zcol = f"{k}_zscore"
            ncol = f"{k}_actual_n" if k != "VV" else "VV_actual_n"
            if zcol not in df_iter.columns: continue
            n = df_iter[ncol].fillna(100).clip(lower=10) if ncol in df_iter.columns else 100
            sigma = 1.0 / np.sqrt(n) if isinstance(n, pd.Series) else 1.0/np.sqrt(100)
            noise = rng.normal(0, sigma, size=len(df_iter))
            df_iter[zcol] = df_iter[zcol] + noise
        df_iter = calcular_priority_v3(df_iter)
        rank_matrix[it, :] = df_iter["Rank_v3"].values
    df["Rank_v3_p025"] = np.nanpercentile(rank_matrix, 2.5, axis=0)
    df["Rank_v3_p975"] = np.nanpercentile(rank_matrix, 97.5, axis=0)
    df["Rank_v3_std"]  = np.nanstd(rank_matrix, axis=0)
    return df


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — Compute Priority Ranking v3 (S2+S1) ══")
    cp.init_ee()

    # Cargar lotes HIGH desde clasificador
    df_clas = pd.read_csv(cp.CSV_CLASIFICACION)
    es_high = df_clas["categoria"].isin(cp.CANA_CATS) & (df_clas["confianza"]=="HIGH")
    lotes = df_clas[es_high].copy()
    log(f"Procesando {len(lotes)} lotes CAÑA HIGH (S2 + S1)")

    end_dt = datetime.now(timezone.utc)
    end_ee = ee.Date(int(end_dt.timestamp()*1000))

    t0 = time.time()
    out = []
    with ThreadPoolExecutor(max_workers=cp.N_WORKERS) as ex:
        futs = {ex.submit(procesar_lote_v3, r.to_dict(), end_ee, end_dt, i, len(lotes)): r
                for i, (_, r) in enumerate(lotes.iterrows(), 1)}
        for fu in as_completed(futs):
            try:
                r = fu.result()
                if r: out.append(r)
            except Exception as e:
                log(f"  worker err: {e}")
    log(f"Compute v3 done en {(time.time()-t0)/60:.1f} min")

    df = pd.DataFrame(out)
    df = df[df.get("error").isna() if "error" in df.columns else slice(None)]
    log(f"Lotes con datos: {len(df)}")

    df = calcular_priority_v3(df)
    df = bootstrap_v3(df)

    df = df.sort_values("Priority_score_v3", ascending=False).reset_index(drop=True)

    # Mergear con ranking v2 para comparar
    csv_v2 = cp.OUTPUT_DIR / "ranking_prioridad_cosecha_2026-05-13.csv"
    if csv_v2.exists():
        df_v2 = pd.read_csv(csv_v2)[["lote_id","Rank","Priority_score"]]
        df_v2.columns = ["lote_id","Rank_v2","Priority_score_v2"]
        df["lote_id"] = df["lote_id"].astype(str)
        df_v2["lote_id"] = df_v2["lote_id"].astype(str)
        df = df.merge(df_v2, on="lote_id", how="left")
        df["Rank_change"] = df["Rank_v2"] - df["Rank_v3"]
        log(f"Merged con v2: {df['Rank_v2'].notna().sum()} matches")

    # 4 categorías por cuartil
    p_h = df["Priority_score_v3"].quantile(0.75)
    p_m = df["Priority_score_v3"].quantile(0.50)
    p_l = df["Priority_score_v3"].quantile(0.25)
    def cat(s):
        if pd.isna(s): return "SIN_DATO"
        if s >= p_h: return "MADUREZ_AVANZADA"
        if s >= p_m: return "MADURACION"
        if s >= p_l: return "PRE_MADURACION"
        return "VEGETATIVO"
    df["Estado_fenologico_v3"] = df["Priority_score_v3"].apply(cat)

    # Comparación rank v2 vs v3
    if "Rank" in df.columns:
        df["Rank_change"] = df["Rank"] - df["Rank_v3"]

    fecha = datetime.now().strftime("%Y-%m-%d")

    df_out = df.drop(columns=["zscores"], errors="ignore")
    cols_first = ["lote_id","area_ha",
                  "Rank_v3","Rank_v3_p025","Rank_v3_p975","Rank_v3_std",
                  "Priority_score_v3","Estado_fenologico_v3",
                  "Rank_v2","Priority_score_v2","Rank_change",
                  "fecha_imagen","valid_coverage","cloud_pct",
                  "NDWI_zscore","NDMI_zscore","CIRE_zscore","PSRI_zscore",
                  "VV_actual","VV_baseline_mean","VV_zscore",
                  "GDD_acum","GDD_dias","GDD_zscore"]
    cols_first = [c for c in cols_first if c in df_out.columns]
    cols_rest = [c for c in df_out.columns if c not in cols_first]
    df_out = df_out[cols_first + cols_rest]

    csv = cp.OUTPUT_DIR / f"ranking_prioridad_v3_S2_S1_{fecha}.csv"
    df_out.to_csv(csv, index=False)
    log(f"  → {csv.name}")

    # Comparación v2 vs v3
    print()
    log("══ COMPARACIÓN v2 vs v3 ══")
    if "Rank_change" in df_out.columns:
        cambios = df_out["Rank_change"].abs()
        log(f"Cambios de rank al agregar S1 VV:")
        log(f"  media: {cambios.mean():.1f} posiciones")
        log(f"  máx:   {cambios.max():.0f} posiciones")
        log(f"  >5 pos: {(cambios>5).sum()} lotes")
        log(f"  >10 pos: {(cambios>10).sum()} lotes")

    print()
    log("Top 15 v3:")
    cols_top = [c for c in ["Rank_v3","lote_id","area_ha","Priority_score_v3",
                             "Estado_fenologico_v3","Rank_v2","Rank_change"]
                if c in df_out.columns]
    print(df_out.head(15)[cols_top].to_string(index=False))

    if "Rank_change" in df_out.columns:
        print()
        log("Lotes que SUBIERON más de rank con S1 (v2 → v3):")
        sub_cols = [c for c in ["lote_id","Rank_v2","Rank_v3","Rank_change",
                                 "VV_zscore","Priority_score_v3"]
                    if c in df_out.columns]
        print(df_out.nlargest(10, "Rank_change")[sub_cols].to_string(index=False))
        print()
        log("Lotes que BAJARON más de rank con S1:")
        print(df_out.nsmallest(10, "Rank_change")[sub_cols].to_string(index=False))


if __name__ == "__main__":
    main()
