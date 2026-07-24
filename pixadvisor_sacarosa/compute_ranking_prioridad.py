#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — RANKING DE PRIORIDAD DE COSECHA (científicamente defendible)
============================================================================
NO estima Pol absoluto. Construye un score relativo de prioridad de cosecha
basado en proxies espectrales validados peer-reviewed:

  Score = -wNDWI·Z_NDWI -wNDMI·Z_NDMI -wCIRE·Z_CIRE +wPSRI·Z_PSRI +wGDD·Z_GDD

donde Z = (valor_actual − baseline_histórico_lote) / SD_baseline_lote
(Z-score temporal, anomalía respecto al propio histórico de cada lote).

Pesos defendibles (sin calibración local todavía):
  NDWI Gao       0.30  Leandro 2024  DOI 10.3390/crops4030024  (r=-0.73 vs Pol)
  NDMI           0.20  Hajeb 2023    DOI 10.1016/j.jag.2022.103168
  CIRE           0.20  Bocca 2024    DOI 10.1007/s12355-024-01468-z (top yield S2)
  PSRI           0.10  Merzlyak 1999 DOI 10.1034/j.1399-3054.1999.106119.x
  GDD T_base 18  0.20  Inman-Bamber  DOI 10.1016/0378-4290(94)90051-5

Z-score temporal: método JRC ASAP (Meroni 2019 DOI 10.1016/j.agsy.2018.07.002)
                  + DeVries 2021 DOI 10.3390/rs13081448

Bootstrap del ranking: 200 iteraciones, IC95% del rank por lote.

INPUT:
  clasificacion_lotes_2026-05-13.csv (filtra CAÑA HIGH = 131 lotes)
  Shapefiles en 03-Zonas-Manejo/<lote>/PRO/

OUTPUT:
  ranking_prioridad_cosecha_<fecha>.csv (score, rank, IC95%, Z-scores)
  ranking_features_<fecha>.csv (todos los features intermedios para auditoría)
============================================================================
"""
from __future__ import annotations
import re
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform
import ee

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                  r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUTPUT_DIR = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                  r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2")

CSV_CLASIFICACION = OUTPUT_DIR / "clasificacion_lotes_2026-05-13.csv"

CANA_CATS = {"CAÑA_ACTIVA","CAÑA_SOCA","CAÑA_PRE_COSECHA_RECIENTE","CAÑA_INMADURA_NUEVA"}

# Búsqueda de imagen actual
DIAS_ATRAS_ACTUAL = 21    # ventana imagen actual (3 semanas)
NUBES_MAX         = 60
COBERTURA_MIN     = 0.60  # más permisivo que pipeline anterior

# Baseline histórico
N_BASELINE_YEARS = 3      # 2023, 2024, 2025 → baseline 2026

# GDD
T_BASE_GDD = 18.0         # °C - Inman-Bamber 1994 entrenudo / sucrosa
GDD_DEFAULT_DAYS = 365    # si no hay drop detectado, 12m

# Pesos del composite (suman 1.0)
WEIGHTS = {
    "NDWI": 0.30,
    "NDMI": 0.20,
    "CIRE": 0.20,
    "PSRI": 0.10,
    "GDD":  0.20,
}

# Bootstrap
N_BOOTSTRAP = 200
RANDOM_SEED = 42

# Z-score cap (JRC ASAP estándar) para evitar outliers extremos
Z_CAP = 3.0

# Threading
N_WORKERS = 6
MAX_RETRIES = 2


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def init_ee():
    try: ee.Initialize()
    except Exception:
        ee.Authenticate(); ee.Initialize()
    log("EE OK")


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


# ════════════════════════════════════════════════════════════════════════════
# GEOMETRÍA
# ════════════════════════════════════════════════════════════════════════════
def cargar_geom(lote_id: str):
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    if not shp.exists(): raise FileNotFoundError(str(shp))
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    area = gdf.geometry.area.sum() / 10000.0
    diss = gdf.dissolve().to_crs("EPSG:4326")
    geom = ee.Geometry(diss.geometry.iloc[0].__geo_interface__)
    return geom, area


# ════════════════════════════════════════════════════════════════════════════
# EARTH ENGINE — helpers compartidos
# ════════════════════════════════════════════════════════════════════════════
def mask_scl(img):
    scl = img.select("SCL")
    return img.updateMask(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)))


def add_indices_s2(img):
    """Agrega NDWI, NDMI, CIRE, PSRI sobre imagen SR escalada (0-1)."""
    b2  = img.select("B2").divide(10000)
    b3  = img.select("B3").divide(10000)
    b4  = img.select("B4").divide(10000)
    b5  = img.select("B5").divide(10000)
    b6  = img.select("B6").divide(10000)
    b7  = img.select("B7").divide(10000)
    b8  = img.select("B8").divide(10000)
    b8a = img.select("B8A").divide(10000)
    b11 = img.select("B11").divide(10000)

    ndwi = b8a.subtract(b11).divide(b8a.add(b11).max(1e-6)).rename("NDWI")
    ndmi = b8.subtract(b11).divide(b8.add(b11).max(1e-6)).rename("NDMI")
    cire = b7.divide(b5.max(1e-6)).subtract(1).rename("CIRE")
    psri = b4.subtract(b2).divide(b6.max(1e-6)).rename("PSRI")
    return img.addBands([ndwi, ndmi, cire, psri])


def s2_collection(geom_ee, start_date_ee, end_date_ee, max_cloud=NUBES_MAX):
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom_ee)
            .filterDate(start_date_ee, end_date_ee)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
            .map(mask_scl)
            .map(add_indices_s2))


def reduce_indices(img_or_coll, geom_ee, scale=20):
    """Mean + std de NDWI, NDMI, CIRE, PSRI sobre la región."""
    if isinstance(img_or_coll, ee.ImageCollection):
        img = img_or_coll.select(["NDWI","NDMI","CIRE","PSRI"]).median()
    else:
        img = img_or_coll.select(["NDWI","NDMI","CIRE","PSRI"])
    reducers = ee.Reducer.mean().combine(ee.Reducer.stdDev(), "", True) \
                              .combine(ee.Reducer.count(), "", True)
    return img.reduceRegion(
        reducer=reducers, geometry=geom_ee, scale=scale,
        maxPixels=int(1e9), bestEffort=True
    )


# ════════════════════════════════════════════════════════════════════════════
# 1) ÍNDICES ACTUALES
# ════════════════════════════════════════════════════════════════════════════
def imagen_actual(geom_ee, end_date_ee):
    start = end_date_ee.advance(-DIAS_ATRAS_ACTUAL, "day")
    col = s2_collection(geom_ee, start, end_date_ee)

    def add_cov(img):
        cov = img.select("B4").mask().reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom_ee, scale=20,
            maxPixels=int(1e9), bestEffort=True).get("B4")
        return img.set("VALID_COVERAGE", ee.Number(cov))

    col = (col.map(add_cov)
              .filter(ee.Filter.gte("VALID_COVERAGE", COBERTURA_MIN))
              .sort("system:time_start", False))

    n = col.size().getInfo()
    if n == 0:
        return None, None
    img = ee.Image(col.first())
    info = img.toDictionary([
        "system:index", "system:time_start",
        "CLOUDY_PIXEL_PERCENTAGE", "VALID_COVERAGE"]).getInfo()
    stats = reduce_indices(img, geom_ee, 20).getInfo()
    return stats, info


# ════════════════════════════════════════════════════════════════════════════
# 2) BASELINE HISTÓRICO (mismo mes calendario, últimos N años)
# ════════════════════════════════════════════════════════════════════════════
def baseline_historico(geom_ee, end_date_ee, n_years=N_BASELINE_YEARS):
    """
    Para el mes calendario de end_date, calcula media+std del índice
    sobre los últimos n_years años (mismo mes).
    """
    end_date = ee.Date(end_date_ee)
    month = end_date.get("month")

    # Por cada año offset 1..n_years atrás
    offsets = ee.List.sequence(1, n_years)

    def per_year(y_off):
        y_off = ee.Number(y_off)
        # Fecha inicial: end_date - y_off años, primer día del mes
        target_year = end_date.get("year").subtract(y_off)
        m_start = ee.Date.fromYMD(target_year, month, 1)
        m_end = m_start.advance(1, "month")
        col = s2_collection(geom_ee, m_start, m_end, max_cloud=70)
        n = col.size()
        # Si no hay imágenes ese mes/año, devolver None
        composite = ee.Image(ee.Algorithms.If(n.gt(0), col.median(), ee.Image(0)))
        st = ee.Algorithms.If(
            n.gt(0),
            reduce_indices(composite, geom_ee, 20),
            ee.Dictionary({})
        )
        return ee.Feature(None, ee.Dictionary({
            "year_offset": y_off,
            "n_imgs": n,
        }).combine(ee.Dictionary(st)))

    feats = ee.FeatureCollection(offsets.map(per_year))
    info = feats.getInfo()
    return info


def baseline_stats(baseline_info: dict) -> dict:
    """Procesa la lista de baselines (mismo mes en N años) → media y SD por índice."""
    out = {}
    for idx in ["NDWI", "NDMI", "CIRE", "PSRI"]:
        means = []
        stds = []
        for f in baseline_info["features"]:
            p = f["properties"]
            if p.get("n_imgs", 0) > 0 and (idx + "_mean") in p:
                means.append(p[idx + "_mean"])
                stds.append(p.get(idx + "_stdDev", 0))
        if len(means) >= 2:
            out[idx + "_baseline_mean"] = float(np.mean(means))
            out[idx + "_baseline_std"]  = float(np.std(means, ddof=1))
            out[idx + "_baseline_n_years"] = len(means)
            out[idx + "_intra_std_mean"] = float(np.mean(stds))
        else:
            out[idx + "_baseline_mean"] = None
            out[idx + "_baseline_std"]  = None
            out[idx + "_baseline_n_years"] = len(means)
            out[idx + "_intra_std_mean"] = None
    return out


# ════════════════════════════════════════════════════════════════════════════
# 3) GDD ACUMULADO (ERA5-Land, T_base 18°C)
# ════════════════════════════════════════════════════════════════════════════
def gdd_acumulado(geom_ee, end_date_ee, days_back: int):
    """
    GDD acumulado con T_base 18°C (Inman-Bamber 1994).
    ERA5-Land píxel ~11km — usamos centroid del lote para muestrear,
    válido para variable climática regional.
    """
    start = end_date_ee.advance(-days_back, "day")
    era5 = (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
            .filterDate(start, end_date_ee)
            .select(["temperature_2m"]))

    def gdd_day(img):
        t = img.select("temperature_2m").subtract(273.15)
        return t.subtract(T_BASE_GDD).max(0).rename("GDD_day")

    centroid = geom_ee.centroid(maxError=1)
    gdd_img = era5.map(gdd_day).sum()
    val = gdd_img.reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=centroid, scale=11000,
        maxPixels=int(1e9), bestEffort=True
    ).get("GDD_day").getInfo()
    return val


# ════════════════════════════════════════════════════════════════════════════
# 4) PROCESAR UN LOTE
# ════════════════════════════════════════════════════════════════════════════
def procesar_lote(lote: dict, end_date_ee, end_date_dt: datetime,
                   idx: int, total: int) -> dict:
    lid = str(lote["lote_id"])
    base = {"lote_id": lid, "area_ha": float(lote["area_ha"])}

    for attempt in range(MAX_RETRIES + 1):
        try:
            geom, _ = cargar_geom(lid)

            # Imagen actual
            stats_act, info_act = imagen_actual(geom, end_date_ee)
            if stats_act is None:
                base["error"] = "sin imagen actual válida"
                return base

            # Baseline histórico
            bl_info = baseline_historico(geom, end_date_ee)
            bl = baseline_stats(bl_info)

            # GDD desde último drop (months_since_drop) o default
            msd = lote.get("months_since_drop")
            if pd.isna(msd) or msd is None or msd == "":
                gdd_days = GDD_DEFAULT_DAYS
            else:
                gdd_days = int(float(msd) * 30)
            gdd = gdd_acumulado(geom, end_date_ee, gdd_days)

            # Z-scores
            zscores = {}
            for k in ["NDWI", "NDMI", "CIRE", "PSRI"]:
                cur = stats_act.get(k + "_mean")
                bm = bl.get(k + "_baseline_mean")
                bs = bl.get(k + "_baseline_std")
                cur_std = stats_act.get(k + "_stdDev")
                cur_n = stats_act.get(k + "_count", 0) or 0
                base[f"{k}_actual"]     = cur
                base[f"{k}_actual_std"] = cur_std
                base[f"{k}_actual_n"]   = cur_n
                base[f"{k}_baseline_mean"] = bm
                base[f"{k}_baseline_std"]  = bs
                if cur is None or bm is None or bs is None or bs < 1e-6:
                    zscores[k] = None
                    base[f"{k}_zscore"] = None
                else:
                    z_raw = (cur - bm) / bs
                    z = max(-Z_CAP, min(Z_CAP, z_raw))   # cap a ±3
                    zscores[k] = z
                    base[f"{k}_zscore"] = z
                    base[f"{k}_zscore_raw"] = z_raw

            base["GDD_acum"] = gdd
            base["GDD_dias"] = gdd_days
            base["fecha_imagen"] = datetime.fromtimestamp(
                info_act["system:time_start"] / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%d")
            base["cloud_pct"] = info_act.get("CLOUDY_PIXEL_PERCENTAGE")
            base["valid_coverage"] = info_act.get("VALID_COVERAGE")
            base["zscores"] = zscores

            gdd_str = f"{gdd:.0f}" if gdd is not None else "n/a"
            log(f"[{idx}/{total}] {lid:18s} "
                f"NDWI_z={fmt(zscores.get('NDWI'))} "
                f"CIRE_z={fmt(zscores.get('CIRE'))} "
                f"GDD={gdd_str:>5s} "
                f"img={base['fecha_imagen']}")
            return base

        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2 + attempt * 2)
                continue
            log(f"[{idx}/{total}] {lid} × {e}")
            base["error"] = str(e)[:200]
            return base


def fmt(v):
    return f"{v:+.2f}" if v is not None else " n/a "


# ════════════════════════════════════════════════════════════════════════════
# 5) PRIORITY SCORE + BOOTSTRAP
# ════════════════════════════════════════════════════════════════════════════
def calcular_priority_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Composite ponderado + Z_GDD relativo entre lotes."""
    # GDD relativo: percentile entre lotes
    valid = df["GDD_acum"].notna()
    if valid.sum() > 1:
        gdd_mean = df.loc[valid, "GDD_acum"].mean()
        gdd_std  = df.loc[valid, "GDD_acum"].std()
        df["GDD_zscore"] = (df["GDD_acum"] - gdd_mean) / gdd_std \
                           if gdd_std > 1e-6 else 0
    else:
        df["GDD_zscore"] = 0

    # Composite: signo según dirección de maduración
    # NDWI/NDMI/CIRE bajan al madurar → invertir
    # PSRI sube al madurar → mantener
    # GDD sube con tiempo → mantener
    def score(r):
        z_ndwi = r.get("NDWI_zscore", np.nan)
        z_ndmi = r.get("NDMI_zscore", np.nan)
        z_cire = r.get("CIRE_zscore", np.nan)
        z_psri = r.get("PSRI_zscore", np.nan)
        z_gdd  = r.get("GDD_zscore",  np.nan)

        # Pesos disponibles (excluir NaN, renormalizar)
        weights = {}
        sources = {"NDWI": z_ndwi, "NDMI": z_ndmi, "CIRE": z_cire,
                    "PSRI": z_psri, "GDD": z_gdd}
        # Signos: + significa "más maduro"
        signs = {"NDWI": -1, "NDMI": -1, "CIRE": -1, "PSRI": +1, "GDD": +1}
        for k, v in sources.items():
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                weights[k] = WEIGHTS[k]
        if not weights: return np.nan
        wsum = sum(weights.values())
        weights = {k: w / wsum for k, w in weights.items()}
        s = 0.0
        for k, w in weights.items():
            s += signs[k] * sources[k] * w
        return s

    df["Priority_score"] = df.apply(score, axis=1)
    df["Rank"] = df["Priority_score"].rank(ascending=False, method="min")
    return df


def bootstrap_ranking(df: pd.DataFrame, n_iter=N_BOOTSTRAP) -> pd.DataFrame:
    """
    Para cada lote, genera ruido gaussiano sobre Z-scores con SD = 1/sqrt(n_pixeles)
    y recalcula ranking. Reporta IC95% del rank.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    n_lotes = len(df)
    rank_matrix = np.full((n_iter, n_lotes), np.nan)

    for it in range(n_iter):
        df_iter = df.copy()
        for k in ["NDWI", "NDMI", "CIRE", "PSRI"]:
            zcol = f"{k}_zscore"
            ncol = f"{k}_actual_n"
            if zcol not in df_iter.columns: continue
            # Ruido = 1 / sqrt(n_pixeles válidos)
            n = df_iter[ncol].fillna(100).clip(lower=10)
            sigma = 1.0 / np.sqrt(n)
            noise = rng.normal(0, sigma, size=len(df_iter))
            df_iter[zcol] = df_iter[zcol] + noise

        df_iter = calcular_priority_scores(df_iter)
        rank_matrix[it, :] = df_iter["Rank"].values

    df["Rank_p025"] = np.nanpercentile(rank_matrix, 2.5, axis=0)
    df["Rank_p975"] = np.nanpercentile(rank_matrix, 97.5, axis=0)
    df["Rank_std"]  = np.nanstd(rank_matrix, axis=0)
    return df


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — Compute Priority Ranking ══")
    init_ee()

    if not CSV_CLASIFICACION.exists():
        log(f"ERROR: falta {CSV_CLASIFICACION}"); sys.exit(1)

    df_clas = pd.read_csv(CSV_CLASIFICACION)
    es_high = df_clas["categoria"].isin(CANA_CATS) & (df_clas["confianza"]=="HIGH")
    lotes = df_clas[es_high].copy()
    log(f"Procesando {len(lotes)} lotes CAÑA HIGH")

    end_date_dt = datetime.now(timezone.utc)
    end_date_ee = ee.Date(int(end_date_dt.timestamp() * 1000))

    t0 = time.time()
    resultados = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {
            ex.submit(procesar_lote, row.to_dict(), end_date_ee, end_date_dt,
                      i, len(lotes)): row
            for i, (_, row) in enumerate(lotes.iterrows(), 1)
        }
        for fu in as_completed(futs):
            try:
                r = fu.result()
                if r: resultados.append(r)
            except Exception as e:
                log(f"  worker error: {e}")
    log(f"Compute features done en {(time.time()-t0)/60:.1f} min")

    df = pd.DataFrame(resultados)
    df = df[df.get("error").isna() if "error" in df.columns else slice(None)]
    log(f"Lotes con datos válidos: {len(df)}")

    # Calcular Priority + ranking + bootstrap
    log("Calculando Priority_score y bootstrap...")
    df = calcular_priority_scores(df)
    df = bootstrap_ranking(df)

    df = df.sort_values("Priority_score", ascending=False).reset_index(drop=True)

    # Categoría fenológica (4 clases) basada en Priority_score
    p_high = df["Priority_score"].quantile(0.75)
    p_mid  = df["Priority_score"].quantile(0.50)
    p_low  = df["Priority_score"].quantile(0.25)
    def cat(s):
        if pd.isna(s): return "SIN_DATO"
        if s >= p_high: return "MADUREZ_AVANZADA"
        if s >= p_mid:  return "MADURACION"
        if s >= p_low:  return "PRE_MADURACION"
        return "VEGETATIVO"
    df["Estado_fenologico"] = df["Priority_score"].apply(cat)

    fecha = datetime.now().strftime("%Y-%m-%d")

    # CSV principal (sin la columna nested zscores)
    df_out = df.drop(columns=["zscores"], errors="ignore")
    cols_first = ["lote_id", "area_ha", "Rank", "Rank_p025", "Rank_p975",
                  "Rank_std", "Priority_score", "Estado_fenologico",
                  "fecha_imagen", "valid_coverage", "cloud_pct",
                  "NDWI_actual", "NDWI_baseline_mean", "NDWI_zscore",
                  "NDMI_actual", "NDMI_baseline_mean", "NDMI_zscore",
                  "CIRE_actual", "CIRE_baseline_mean", "CIRE_zscore",
                  "PSRI_actual", "PSRI_baseline_mean", "PSRI_zscore",
                  "GDD_acum", "GDD_dias", "GDD_zscore"]
    cols_first = [c for c in cols_first if c in df_out.columns]
    cols_rest = [c for c in df_out.columns if c not in cols_first]
    df_out = df_out[cols_first + cols_rest]

    csv = OUTPUT_DIR / f"ranking_prioridad_cosecha_{fecha}.csv"
    df_out.to_csv(csv, index=False)
    log(f"  → {csv.name}")

    # Resumen print
    print()
    log("═══ RESUMEN ═══")
    print(df_out["Estado_fenologico"].value_counts().to_string())
    print()
    log("Top 15 prioridad de cosecha:")
    print(df_out.head(15)[["Rank", "lote_id", "area_ha", "Priority_score",
                            "Estado_fenologico", "Rank_p025", "Rank_p975"]
                          ].to_string(index=False))
    log(f"Tiempo total: {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
