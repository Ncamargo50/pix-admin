#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — CLASIFICADOR DE COBERTURA POR LOTE
============================================================================
Determina qué lotes tienen CAÑA ACTIVA antes de aplicar el modelo Pol/Brix.
Usa serie temporal NDVI Sentinel-2 últimos 14 meses + reglas heurísticas
de firma fenológica.

CATEGORÍAS:
  CAÑA_ACTIVA          : NDVI alto, sin cosecha reciente, posible pre-cosecha
  CAÑA_SOCA            : un drop por cosecha + recuperación posterior
  CAÑA_PRE_COSECHA     : un drop reciente, aún sin recuperación
  CAÑA_INMADURA_NUEVA  : recientemente plantada, NDVI creciendo desde bajo
  REFORMA_SIN_REPLANTAR: cosechado >4 meses sin replantar (E1 case)
  CULTIVO_CORTO_SOYA   : 2+ ciclos en 14 meses (rotación soya/maíz)
  PASTO_O_COBERTURA    : NDVI moderado constante sin cosecha
  MONTE_FOREST         : NDVI alto constante todo el año
  SUELO_DESNUDO        : NDVI muy bajo persistente
  OTRO_REVISAR         : no matchea regla — revisión manual

CONFIANZA: HIGH / MEDIUM / LOW

SALIDAS:
  clasificacion_lotes_<fecha>.csv     : clasificación + features + notas
  serie_ndvi_lotes_<fecha>.csv        : serie completa (auditoría)
  resumen_clasificacion.png           : barras por categoría
  lotes_NO_cana.csv                   : subset para revisión con cliente
  lotes_CANA_confirmada.csv           : input para re-correr pipeline Pol
============================================================================
"""
from __future__ import annotations

import re
import sys
import time
import warnings
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

import ee

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT = Path(
    r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
    r"\Hacienda-Del-Senor\03-Zonas-Manejo"
)
OUTPUT_DIR = Path(
    r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
    r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
)

SHP_PATTERN  = "zonas_manejo_*_PRO.shp"
N_MESES      = 14         # ventana de análisis
N_WORKERS    = 6          # threads paralelos (cuidado con cuota EE)
DROP_THRESH  = 0.30       # caída mes-a-mes para considerarse "cosecha"
MAX_RETRIES  = 2

# Discoverar TODOS los lotes (incluso los previamente excluidos)
EXCLUIR_DEL_DESCUBRIMIENTO: set[str] = set()


def log(m: str):
    print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def init_ee():
    try: ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()
    log("EE OK")


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


# ════════════════════════════════════════════════════════════════════════════
# DISCOVERY + GEOMETRÍA
# ════════════════════════════════════════════════════════════════════════════
def descubrir_lotes(root: Path) -> list[dict]:
    out = []
    for shp in root.rglob(SHP_PATTERN):
        m = re.match(r"zonas_manejo_(.+)_PRO\.shp$", shp.name)
        if not m: continue
        lid = m.group(1)
        if lid in EXCLUIR_DEL_DESCUBRIMIENTO: continue
        out.append({"lote_id": lid, "shp": shp})
    out.sort(key=lambda x: x["lote_id"])
    return out


def cargar_geom(shp_path: Path):
    gdf = gpd.read_file(shp_path)
    if gdf.empty: raise ValueError("shp vacío")
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    area_ha = gdf.geometry.area.sum() / 10000.0
    diss = gdf.dissolve().to_crs("EPSG:4326")
    geom = ee.Geometry(diss.geometry.iloc[0].__geo_interface__)
    return geom, area_ha


# ════════════════════════════════════════════════════════════════════════════
# SERIE NDVI MENSUAL — server-side, una sola llamada EE por lote
# ════════════════════════════════════════════════════════════════════════════
def mask_scl(img):
    scl = img.select("SCL")
    return img.updateMask(scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)))


def serie_ndvi(geom_ee, end_date_ee, n_meses: int):
    offsets = ee.List.sequence(1, n_meses)

    def make(o):
        o = ee.Number(o)
        m_end   = end_date_ee.advance(o.subtract(1).multiply(-1), "month")
        m_start = end_date_ee.advance(o.multiply(-1), "month")
        col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
               .filterBounds(geom_ee)
               .filterDate(m_start, m_end)
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
               .map(mask_scl))
        n = col.size()
        # Si no hay imágenes, devolver feature con ndvi None
        composite = ee.Image(ee.Algorithms.If(n.gt(0), col.median(), ee.Image(0)))
        ndvi = composite.normalizedDifference(["B8", "B4"]).rename("NDVI")
        mean = ee.Algorithms.If(
            n.gt(0),
            ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geom_ee, scale=20,
                maxPixels=int(1e9), bestEffort=True).get("NDVI"),
            None)
        return ee.Feature(None, {
            "offset": o, "ndvi": mean, "n_imgs": n,
            "month": m_start.format("YYYY-MM"),
        })

    feats = ee.FeatureCollection(offsets.map(make))
    info = feats.getInfo()
    rows = []
    for f in info["features"]:
        p = f["properties"]
        rows.append({
            "offset": int(p["offset"]),
            "month":  p.get("month"),
            "ndvi":   p.get("ndvi"),
            "n_imgs": int(p.get("n_imgs") or 0),
        })
    rows.sort(key=lambda x: -x["offset"])  # más viejo primero
    return rows


# ════════════════════════════════════════════════════════════════════════════
# FEATURES + CLASIFICACIÓN
# ════════════════════════════════════════════════════════════════════════════
def calcular_features(serie: list[dict]) -> dict:
    vals = [r["ndvi"] for r in serie if r["ndvi"] is not None]
    if len(vals) < 6:
        return {"_insuficiente": True}

    v = np.array(vals, dtype=float)
    # Series sin huecos para drops (interpola por adyacentes)
    full = []
    last_val = None
    for r in serie:
        if r["ndvi"] is not None:
            full.append(r["ndvi"]); last_val = r["ndvi"]
        else:
            full.append(last_val if last_val is not None else np.nan)
    full = np.array(full, dtype=float)
    full = full[~np.isnan(full)]

    diffs = np.diff(full)
    n_drops = int((diffs <= -DROP_THRESH).sum())
    n_rises = int((diffs >= +DROP_THRESH).sum())

    last3 = vals[-3:] if len(vals) >= 3 else vals
    first3 = vals[:3] if len(vals) >= 3 else vals

    # tiempo desde último drop (en meses al final de la serie)
    drop_idxs = np.where(diffs <= -DROP_THRESH)[0]
    months_since_drop = (len(diffs) - drop_idxs[-1]) if len(drop_idxs) > 0 else None

    n_low  = int((v < 0.30).sum())
    n_high = int((v > 0.70).sum())
    n_mid  = int(((v >= 0.30) & (v <= 0.70)).sum())

    # Recuperación post-drop
    if len(drop_idxs) > 0:
        i = drop_idxs[-1]  # índice del drop (en diffs)
        # ndvi en momento del drop, comparar con últimos meses
        v_post = full[i+1:]
        recovery = float(v_post.max() - full[i+1]) if len(v_post) > 1 else 0
    else:
        recovery = 0.0

    return {
        "_insuficiente": False,
        "n_valid":       len(vals),
        "ndvi_mean":     float(v.mean()),
        "ndvi_min":      float(v.min()),
        "ndvi_max":      float(v.max()),
        "ndvi_range":    float(v.max() - v.min()),
        "ndvi_std":      float(v.std()),
        "ndvi_actual":   float(v[-1]),
        "ndvi_p10":      float(np.percentile(v, 10)),
        "ndvi_p90":      float(np.percentile(v, 90)),
        "n_drops":       n_drops,
        "n_rises":       n_rises,
        "n_low":         n_low,
        "n_high":        n_high,
        "n_mid":         n_mid,
        "last3_mean":    float(np.mean(last3)),
        "first3_mean":   float(np.mean(first3)),
        "months_since_drop": int(months_since_drop) if months_since_drop is not None else None,
        "recovery_post_drop": float(recovery),
    }


def clasificar(f: dict) -> tuple[str, str, str]:
    """Devuelve (categoría, confianza, nota). Reglas conservadoras: ante duda
    flagear como OTRO_REVISAR para no contaminar el output con falsos positivos."""
    if f.get("_insuficiente"):
        return ("DATOS_INSUFICIENTES", "LOW",
                "Pocos meses con observación válida")

    # 1) Forest / monte: NDVI alto constante todo el año
    if f["ndvi_min"] > 0.65 and f["ndvi_range"] < 0.25 and f["n_drops"] == 0:
        return ("MONTE_FOREST", "HIGH",
                "NDVI alto y constante todo el año — vegetación permanente")

    # 2) Suelo desnudo: NDVI muy bajo persistente
    if f["ndvi_max"] < 0.35:
        return ("SUELO_DESNUDO", "HIGH",
                "NDVI muy bajo persistente — sin cobertura significativa")

    # 3) Reforma sin replantar (E1): tuvo NDVI alto, ahora >4m bajo
    if (f["n_low"] >= 4 and f["last3_mean"] < 0.50
            and f["ndvi_max"] > 0.55 and f["months_since_drop"] is not None
            and f["months_since_drop"] >= 4):
        return ("REFORMA_SIN_REPLANTAR", "HIGH",
                f"Cosechado hace {f['months_since_drop']}m — sin replantar caña")

    # 4) Multi-ciclo: soya / rotación corta (>=2 cosechas en 14m)
    if f["n_drops"] >= 2:
        return ("CULTIVO_CORTO_SOYA", "HIGH",
                f"{f['n_drops']} cosechas detectadas en {N_MESES}m — "
                "rotación soya/maíz, no es caña")

    # 5) Pasto / cobertura permanente: NDVI moderado constante, range chico
    # IMPORTANTE: ANTES de cualquier regla de caña sin drop, para evitar
    # falsos positivos sobre pistas, pasturas, áreas verdes manejadas.
    if (f["n_drops"] == 0 and f["ndvi_range"] < 0.30
            and 0.40 < f["ndvi_min"] and f["ndvi_max"] < 0.85):
        return ("PASTO_O_COBERTURA", "HIGH",
                f"NDVI {f['ndvi_min']:.2f}–{f['ndvi_max']:.2f} constante "
                "sin patrón de cosecha — no es caña")

    # 6) Caña con cosecha visible (1 drop)
    if f["n_drops"] == 1 and f["ndvi_max"] > 0.55:
        if f["months_since_drop"] is not None and f["months_since_drop"] <= 3:
            return ("CAÑA_PRE_COSECHA_RECIENTE", "MEDIUM",
                    f"Cosecha hace {f['months_since_drop']}m, "
                    f"recuperación parcial ({f['recovery_post_drop']:.2f})")
        if f["recovery_post_drop"] > 0.30:
            return ("CAÑA_SOCA", "HIGH",
                    f"Cosecha + recuperación {f['recovery_post_drop']:.2f} "
                    "— caña soca creciendo")
        return ("CAÑA_SOCA", "MEDIUM",
                "Un ciclo de cosecha sin recuperación clara visible")

    # 7) Caña con declive lento estacional (sin drop abrupto pero range alto)
    # Lote 1 case: NDVI baja gradualmente y se recupera lento, típico ciclo caña
    if (f["n_drops"] == 0 and f["ndvi_max"] > 0.65
            and f["ndvi_range"] > 0.35
            and f["last3_mean"] < f["first3_mean"] - 0.10):
        return ("CAÑA_ACTIVA", "MEDIUM",
                f"Declive estacional NDVI {f['first3_mean']:.2f}→"
                f"{f['last3_mean']:.2f} — posible caña madurando")

    # 8) Caña inmadura nueva (NDVI creciendo desde bajo, plantación reciente)
    if (f["first3_mean"] < 0.40 and f["last3_mean"] > 0.55
            and f["ndvi_actual"] > f["first3_mean"] + 0.25):
        return ("CAÑA_INMADURA_NUEVA", "MEDIUM",
                f"NDVI creciendo: {f['first3_mean']:.2f} → "
                f"{f['last3_mean']:.2f} — plantación nueva probable")

    # 9) Caña activa estable: NDVI alto + variabilidad moderada + sin cosecha
    if (f["n_drops"] == 0 and f["ndvi_mean"] > 0.55
            and f["ndvi_max"] > 0.70 and f["ndvi_range"] >= 0.30):
        return ("CAÑA_ACTIVA", "LOW",
                "NDVI alto sin cosecha visible — caña en crecimiento "
                "(sin drop confirmado, baja confianza)")

    # 10) Resto — flag para revisión manual
    return ("OTRO_REVISAR", "LOW",
            f"Patrón ambiguo: drops={f['n_drops']}, "
            f"min={f['ndvi_min']:.2f}, max={f['ndvi_max']:.2f}, "
            f"range={f['ndvi_range']:.2f}, last3={f['last3_mean']:.2f}")


# ════════════════════════════════════════════════════════════════════════════
# WORKER POR LOTE
# ════════════════════════════════════════════════════════════════════════════
ee_lock = None  # threading lock no necesario (EE es thread-safe en Py)


def procesar_lote(lote: dict, end_date_ee, idx: int, total: int) -> dict:
    lid = lote["lote_id"]
    base = {"lote_id": lid}
    for attempt in range(MAX_RETRIES + 1):
        try:
            geom, area_ha = cargar_geom(lote["shp"])
            base["area_ha"] = area_ha
            serie = serie_ndvi(geom, end_date_ee, N_MESES)
            base["serie"] = serie
            feats = calcular_features(serie)
            cat, conf, nota = clasificar(feats)
            base.update(feats)
            base["categoria"] = cat
            base["confianza"] = conf
            base["nota"] = nota
            log(f"[{idx}/{total}] {lid:18s} → {cat:25s} ({conf:6s}) "
                f"area={area_ha:6.1f}ha drops={feats.get('n_drops','?')} "
                f"NDVI_actual={feats.get('ndvi_actual', float('nan')):.2f}")
            return base
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2 + attempt * 2)
                continue
            log(f"[{idx}/{total}] {lid} × ERROR: {e}")
            base["categoria"] = "ERROR"
            base["nota"] = str(e)[:200]
            return base


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("═══ Clasificador de cobertura — Hacienda del Señor ═══")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    init_ee()

    lotes = descubrir_lotes(LOTES_ROOT)
    log(f"Lotes detectados: {len(lotes)}")

    end_date_ee = ee.Date(int(datetime.now(timezone.utc).timestamp() * 1000))

    t0 = time.time()
    resultados = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = {ex.submit(procesar_lote, l, end_date_ee, i, len(lotes)): l
                for i, l in enumerate(lotes, 1)}
        for fu in as_completed(futs):
            try:
                r = fu.result()
                resultados.append(r)
            except Exception as e:
                log(f"  worker error: {e}")
    log(f"Done en {(time.time()-t0)/60:.1f} min")

    # ───────── salidas
    fecha = datetime.now().strftime("%Y-%m-%d")

    # CSV principal
    rows = []
    series_rows = []
    for r in resultados:
        rows.append({k: v for k, v in r.items() if k != "serie"})
        for s in (r.get("serie") or []):
            series_rows.append({"lote_id": r["lote_id"], **s})
    df = pd.DataFrame(rows).sort_values(["categoria", "lote_id"])
    cols_first = ["lote_id", "area_ha", "categoria", "confianza", "nota",
                  "ndvi_mean", "ndvi_min", "ndvi_max", "ndvi_range",
                  "ndvi_actual", "n_drops", "months_since_drop",
                  "recovery_post_drop", "n_low", "n_high", "n_valid"]
    cols_first = [c for c in cols_first if c in df.columns]
    cols_rest  = [c for c in df.columns if c not in cols_first]
    df = df[cols_first + cols_rest]

    csv_main = OUTPUT_DIR / f"clasificacion_lotes_{fecha}.csv"
    df.to_csv(csv_main, index=False)
    log(f"  → {csv_main.name}")

    # Series
    df_ser = pd.DataFrame(series_rows)
    csv_ser = OUTPUT_DIR / f"serie_ndvi_lotes_{fecha}.csv"
    df_ser.to_csv(csv_ser, index=False)
    log(f"  → {csv_ser.name}")

    # Subset NO-caña + caña-confirmada
    no_cana = df[~df["categoria"].isin(
        ["CAÑA_ACTIVA", "CAÑA_SOCA", "CAÑA_PRE_COSECHA_RECIENTE",
         "CAÑA_INMADURA_NUEVA"])].copy()
    si_cana = df[df["categoria"].isin(
        ["CAÑA_ACTIVA", "CAÑA_SOCA", "CAÑA_PRE_COSECHA_RECIENTE",
         "CAÑA_INMADURA_NUEVA"])].copy()
    no_cana.to_csv(OUTPUT_DIR / "lotes_NO_cana.csv", index=False)
    si_cana.to_csv(OUTPUT_DIR / "lotes_CANA_confirmada.csv", index=False)
    log(f"  → lotes_NO_cana.csv: {len(no_cana)} lotes")
    log(f"  → lotes_CANA_confirmada.csv: {len(si_cana)} lotes")

    # Gráfico de barras
    counts = df["categoria"].value_counts().sort_values(ascending=True)
    areas = df.groupby("categoria")["area_ha"].sum().reindex(counts.index)
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5), dpi=140)
    colores = {
        "CAÑA_ACTIVA":              "#1a9850",
        "CAÑA_SOCA":                "#66bd63",
        "CAÑA_PRE_COSECHA_RECIENTE":"#a6d96a",
        "CAÑA_INMADURA_NUEVA":      "#fee08b",
        "REFORMA_SIN_REPLANTAR":    "#fdae61",
        "CULTIVO_CORTO_SOYA":       "#f46d43",
        "PASTO_O_COBERTURA":        "#d73027",
        "MONTE_FOREST":             "#1B5E20",
        "SUELO_DESNUDO":            "#a50026",
        "OTRO_REVISAR":             "#666666",
        "DATOS_INSUFICIENTES":      "#999999",
        "ERROR":                    "#000000",
    }
    cls_colors = [colores.get(c, "#888") for c in counts.index]

    axes[0].barh(counts.index, counts.values, color=cls_colors)
    axes[0].set_title("Lotes por categoría", fontweight="bold", color="#1B5E20")
    axes[0].set_xlabel("# Lotes")
    for i, v in enumerate(counts.values):
        axes[0].text(v, i, f" {v}", va="center", fontsize=9)

    axes[1].barh(areas.index, areas.values, color=cls_colors)
    axes[1].set_title("Hectáreas por categoría",
                       fontweight="bold", color="#1B5E20")
    axes[1].set_xlabel("Hectáreas")
    for i, v in enumerate(areas.values):
        axes[1].text(v, i, f" {v:.0f}", va="center", fontsize=9)

    plt.suptitle(
        f"Clasificación de cobertura — Hacienda del Señor\n"
        f"Sentinel-2 últimos {N_MESES} meses · {fecha}",
        fontsize=13, fontweight="bold", color="#1B5E20")
    plt.tight_layout()
    png = OUTPUT_DIR / f"resumen_clasificacion_{fecha}.png"
    plt.savefig(png, dpi=140, bbox_inches="tight", facecolor="white")
    log(f"  → {png.name}")

    # ───────── Print resumen
    print()
    log("═══ RESUMEN ═══")
    print(df.groupby("categoria").agg(
        n=("lote_id", "count"),
        ha=("area_ha", "sum")
    ).sort_values("n", ascending=False).to_string())
    print()
    log(f"NO-caña: {len(no_cana)} lotes ({no_cana['area_ha'].sum():.0f} ha)")
    log(f"CAÑA confirmada: {len(si_cana)} lotes ({si_cana['area_ha'].sum():.0f} ha)")
    log(f"Total Hacienda: {len(df)} lotes ({df['area_ha'].sum():.0f} ha)")


if __name__ == "__main__":
    main()
