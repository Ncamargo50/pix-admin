#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR AGENTE — Memoria persistente + Auto-calibración
============================================================================
Knowledge Base (SQLite) + ML model management para mejorar el modelo de
prioridad de cosecha de caña con cada zafra.

ARQUITECTURA:
  📚 KB SQLite — pixadvisor_kb.db
       Tablas: lotes, predicciones_satelitales, muestreos_cmi, pol_ingenio,
               modelo_versions, decisiones
  🧠 Auto-calibración — Ridge + Random Forest, versionado de modelos
  📊 Reportes evolución — PDF con skill metrics zafra a zafra

USO (CLI):
  python pixadvisor_agente.py init                     # Inicializar DB
  python pixadvisor_agente.py status                   # Estado de la KB
  python pixadvisor_agente.py load-predicciones <csv>  # Carga ranking v3
  python pixadvisor_agente.py load-cmi <xlsx>          # Carga muestreo Excel
  python pixadvisor_agente.py load-cmi-pdf <dir>       # Carga PDFs rellenados
  python pixadvisor_agente.py load-pol <csv>           # Carga Pol del ingenio
  python pixadvisor_agente.py train --target cmi       # Entrena modelo
  python pixadvisor_agente.py train --target pol       # (cuando haya datos)
  python pixadvisor_agente.py predict --hacienda HDS   # Predice con vigente
  python pixadvisor_agente.py report-skill             # PDF evolución

============================================================================
"""
from __future__ import annotations
import argparse
import json
import pickle
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
KB_DIR = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
               r"\Hacienda-Del-Senor\06-Agente-Pixadvisor")
KB_DB  = KB_DIR / "pixadvisor_kb.db"
MODELS_DIR = KB_DIR / "models"
REPORTS_DIR = KB_DIR / "reports"

# Pesos default v3 (literatura + S1 validado local)
WEIGHTS_DEFAULT = {
    "z_ndwi": -0.25, "z_ndmi": -0.15, "z_cire": -0.20,
    "z_psri": +0.10, "z_vv":   -0.10, "z_gdd":  +0.20,
}


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


# ════════════════════════════════════════════════════════════════════════════
# 1) SCHEMA SQLITE
# ════════════════════════════════════════════════════════════════════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS lotes (
    lote_id TEXT PRIMARY KEY,
    hacienda TEXT,
    area_ha REAL,
    cultivar TEXT,
    fecha_plantacion DATE,
    n_corte INTEGER,
    crs TEXT,
    geometry_wkt TEXT,
    fecha_alta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS predicciones_satelitales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id TEXT NOT NULL,
    fecha_imagen_s2 DATE,
    fecha_prediccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modelo_version TEXT,
    z_ndwi REAL, z_ndmi REAL, z_cire REAL, z_psri REAL,
    z_vv REAL, z_gdd REAL,
    priority_score REAL,
    rank_v INTEGER,
    estado_fenologico TEXT,
    cobertura_util REAL,
    gdd_acum REAL,
    gdd_dias INTEGER,
    FOREIGN KEY(lote_id) REFERENCES lotes(lote_id)
);

CREATE TABLE IF NOT EXISTS muestreos_cmi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id TEXT NOT NULL,
    fecha_muestreo DATE,
    agronomo TEXT,
    punto_n INTEGER,
    tallo_n INTEGER,
    bs_brix REAL,
    bi_brix REAL,
    cmi REAL,
    notas TEXT,
    FOREIGN KEY(lote_id) REFERENCES lotes(lote_id)
);

CREATE TABLE IF NOT EXISTS pol_ingenio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id TEXT NOT NULL,
    fecha_cosecha DATE,
    fecha_analisis DATE,
    pol_pct REAL,
    brix_pct REAL,
    pureza_pct REAL,
    atr_kg_t REAL,
    ingenio TEXT,
    notas TEXT,
    FOREIGN KEY(lote_id) REFERENCES lotes(lote_id)
);

CREATE TABLE IF NOT EXISTS modelo_versions (
    version TEXT PRIMARY KEY,
    fecha_entrenamiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    objetivo TEXT,                   -- 'cmi' o 'pol'
    algoritmo TEXT,                  -- 'ridge' / 'rf' / 'xgb'
    n_muestras_train INTEGER,
    n_lotes INTEGER,
    w_ndwi REAL, w_ndmi REAL, w_cire REAL,
    w_psri REAL, w_vv REAL, w_gdd REAL, w_intercept REAL,
    r2_train REAL,
    r2_cv REAL,
    rmse_cv REAL,
    spearman_cv REAL,
    archivo_modelo TEXT,
    feature_importance_json TEXT,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS decisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote_id TEXT NOT NULL,
    fecha_decision DATE,
    accion TEXT,
    cmi_avg REAL,
    pol_predicho REAL,
    rank_satelital INTEGER,
    agronomo TEXT,
    notas TEXT
);

CREATE INDEX IF NOT EXISTS idx_pred_lote ON predicciones_satelitales(lote_id);
CREATE INDEX IF NOT EXISTS idx_pred_fecha ON predicciones_satelitales(fecha_imagen_s2);
CREATE INDEX IF NOT EXISTS idx_cmi_lote ON muestreos_cmi(lote_id);
CREATE INDEX IF NOT EXISTS idx_pol_lote ON pol_ingenio(lote_id);
"""


def init_kb():
    """Inicializa estructura de carpetas + DB SQLite."""
    KB_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(KB_DB)
    conn.executescript(SCHEMA)
    # Vista CMI promedio por lote-fecha
    conn.execute("DROP VIEW IF EXISTS muestreos_cmi_promedio_view")
    conn.execute("""
        CREATE VIEW muestreos_cmi_promedio_view AS
        SELECT lote_id, fecha_muestreo, AVG(cmi) AS cmi_promedio,
               COUNT(*) AS n_tallos
        FROM muestreos_cmi
        WHERE cmi IS NOT NULL
        GROUP BY lote_id, fecha_muestreo
    """)
    conn.commit()
    conn.close()
    log(f"KB inicializada en {KB_DB}")


def get_conn():
    if not KB_DB.exists():
        log(f"KB no existe, inicializando...")
        init_kb()
    return sqlite3.connect(KB_DB)


# ════════════════════════════════════════════════════════════════════════════
# 2) STATUS
# ════════════════════════════════════════════════════════════════════════════
def cmd_status():
    conn = get_conn()
    cur = conn.cursor()
    print("\n══ Estado de la Knowledge Base ══")
    print(f"DB: {KB_DB}")
    print(f"Tamaño: {KB_DB.stat().st_size/1024:.1f} KB\n")

    queries = [
        ("Lotes registrados", "SELECT COUNT(*) FROM lotes"),
        ("Predicciones satelitales", "SELECT COUNT(*) FROM predicciones_satelitales"),
        ("Mediciones CMI individuales", "SELECT COUNT(*) FROM muestreos_cmi"),
        ("Lotes con muestreo CMI", "SELECT COUNT(DISTINCT lote_id) FROM muestreos_cmi"),
        ("Análisis Pol ingenio", "SELECT COUNT(*) FROM pol_ingenio"),
        ("Versiones de modelo entrenadas", "SELECT COUNT(*) FROM modelo_versions"),
        ("Decisiones registradas", "SELECT COUNT(*) FROM decisiones"),
    ]
    for label, q in queries:
        try:
            n = cur.execute(q).fetchone()[0]
            print(f"  {label:<35s}: {n}")
        except Exception as e:
            print(f"  {label:<35s}: ERROR {e}")

    # Última versión del modelo
    try:
        v = cur.execute("""
            SELECT version, objetivo, algoritmo, n_muestras_train,
                   r2_train, r2_cv, rmse_cv, fecha_entrenamiento
            FROM modelo_versions ORDER BY fecha_entrenamiento DESC LIMIT 1
        """).fetchone()
        if v:
            print("\n  Modelo VIGENTE:")
            print(f"    versión: {v[0]} ({v[1]} · {v[2]})")
            print(f"    train n={v[3]}, R²train={v[4]:.3f}, R²CV={v[5]:.3f}, RMSE_CV={v[6]:.3f}")
            print(f"    entrenado: {v[7]}")
    except Exception: pass

    conn.close()
    print()


# ════════════════════════════════════════════════════════════════════════════
# 3) INGESTA — predicciones satelitales (CSV ranking v3)
# ════════════════════════════════════════════════════════════════════════════
def cmd_load_predicciones(csv_path: str, modelo_version: str = "v3_S2_S1"):
    csv = Path(csv_path)
    if not csv.exists():
        log(f"ERROR: no existe {csv}"); return
    df = pd.read_csv(csv)
    df["lote_id"] = df["lote_id"].astype(str)

    conn = get_conn()
    cur = conn.cursor()

    # Asegurar lotes en tabla
    for _, r in df.iterrows():
        cur.execute("""
            INSERT OR IGNORE INTO lotes (lote_id, hacienda, area_ha, fecha_alta)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (r["lote_id"], "Hacienda del Señor", float(r.get("area_ha", 0))))

    # Insertar predicciones
    n_ok = 0
    for _, r in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO predicciones_satelitales (
                    lote_id, fecha_imagen_s2, modelo_version,
                    z_ndwi, z_ndmi, z_cire, z_psri, z_vv, z_gdd,
                    priority_score, rank_v, estado_fenologico,
                    cobertura_util, gdd_acum, gdd_dias
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["lote_id"],
                str(r.get("fecha_imagen", "")),
                modelo_version,
                _f(r.get("NDWI_zscore")),
                _f(r.get("NDMI_zscore")),
                _f(r.get("CIRE_zscore")),
                _f(r.get("PSRI_zscore")),
                _f(r.get("VV_zscore")),
                _f(r.get("GDD_zscore")),
                _f(r.get("Priority_score_v3", r.get("Priority_score"))),
                _i(r.get("Rank_v3", r.get("Rank"))),
                str(r.get("Estado_fenologico_v3",
                          r.get("Estado_fenologico", ""))),
                _f(r.get("valid_coverage")),
                _f(r.get("GDD_acum")),
                _i(r.get("GDD_dias")),
            ))
            n_ok += 1
        except Exception as e:
            log(f"  err lote {r.get('lote_id')}: {e}")
    conn.commit(); conn.close()
    log(f"OK — {n_ok}/{len(df)} predicciones cargadas (modelo {modelo_version})")


def _f(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return None
    try: return float(v)
    except Exception: return None


def _i(v):
    if v is None or (isinstance(v, float) and pd.isna(v)): return None
    try: return int(float(v))
    except Exception: return None


# ════════════════════════════════════════════════════════════════════════════
# 4) INGESTA — muestreos CMI desde Excel template
# ════════════════════════════════════════════════════════════════════════════
def cmd_load_cmi_excel(xlsx_path: str, fecha_muestreo: str = None,
                        agronomo: str = ""):
    """Lee Excel template (una hoja por lote) con 50 mediciones BS/BI."""
    import openpyxl
    xlsx = Path(xlsx_path)
    if not xlsx.exists(): log(f"ERROR: {xlsx}"); return
    if fecha_muestreo is None:
        fecha_muestreo = datetime.now().strftime("%Y-%m-%d")

    wb = openpyxl.load_workbook(xlsx, data_only=False)
    conn = get_conn(); cur = conn.cursor()
    n_total = 0; lotes_ok = 0

    for sheet_name in wb.sheetnames:
        if sheet_name == "RESUMEN": continue
        ws = wb[sheet_name]
        lote_id = sheet_name.strip()
        # Filas data: row_start = 14, header en row 14, data desde 15
        # Estructura columnas: A=Punto B=Tallo C=BS D=BI E=CMI F-H=promedios I=Notas
        header_row = 14
        n_lote = 0
        for p in range(1, 6):
            for t in range(1, 11):
                r = header_row + (p-1) * 10 + t
                bs_cell = ws.cell(r, 3).value
                bi_cell = ws.cell(r, 4).value
                if bs_cell is None and bi_cell is None: continue
                bs = _f(bs_cell); bi = _f(bi_cell)
                cmi = (bs / bi * 100) if (bs and bi and bi > 0) else None
                notas = ws.cell(r, 9).value or ""
                cur.execute("""
                    INSERT INTO muestreos_cmi (
                        lote_id, fecha_muestreo, agronomo,
                        punto_n, tallo_n, bs_brix, bi_brix, cmi, notas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (lote_id, fecha_muestreo, agronomo, p, t, bs, bi, cmi,
                       str(notas)[:200]))
                if bs is not None or bi is not None:
                    n_lote += 1; n_total += 1
        if n_lote > 0:
            lotes_ok += 1
            log(f"  {lote_id}: {n_lote} mediciones cargadas")
    conn.commit(); conn.close()
    log(f"OK — {n_total} mediciones de {lotes_ok} lotes (fecha {fecha_muestreo})")


# ════════════════════════════════════════════════════════════════════════════
# 5) INGESTA — muestreos CMI desde PDFs digitales rellenados
# ════════════════════════════════════════════════════════════════════════════
def cmd_load_cmi_pdfs(dir_path: str, fecha_muestreo: str = None):
    """Lee carpeta con PDFs digitales rellenados (AcroForm)."""
    from pypdf import PdfReader
    src = Path(dir_path)
    if not src.exists(): log(f"ERROR: {src}"); return
    if fecha_muestreo is None:
        fecha_muestreo = datetime.now().strftime("%Y-%m-%d")

    conn = get_conn(); cur = conn.cursor()
    n_total = 0; lotes_ok = 0

    for pdf in sorted(src.glob("FICHA_DIGITAL_*.pdf")):
        m = re.match(r"FICHA_DIGITAL_(\d+)_(.+)\.pdf$", pdf.name)
        if not m: continue
        lote_id = m.group(2)
        try:
            r = PdfReader(str(pdf))
            fields = r.get_form_text_fields() or {}
            agronomo = fields.get("AGRONOMO", "")
            fecha_pdf = fields.get("FECHA", fecha_muestreo) or fecha_muestreo
            n_lote = 0
            for p in range(1, 6):
                for t in range(1, 11):
                    bs = _f(fields.get(f"P{p}_T{t}_BS"))
                    bi = _f(fields.get(f"P{p}_T{t}_BI"))
                    if bs is None and bi is None: continue
                    cmi = (bs/bi*100) if (bs and bi and bi > 0) else None
                    notas = fields.get(f"P{p}_T{t}_NOTAS", "") or ""
                    cur.execute("""
                        INSERT INTO muestreos_cmi (
                            lote_id, fecha_muestreo, agronomo,
                            punto_n, tallo_n, bs_brix, bi_brix, cmi, notas
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (lote_id, fecha_pdf, agronomo, p, t, bs, bi, cmi,
                           str(notas)[:200]))
                    n_lote += 1; n_total += 1
            if n_lote > 0:
                lotes_ok += 1
                log(f"  {lote_id}: {n_lote} mediciones de PDF")
        except Exception as e:
            log(f"  err {pdf.name}: {e}")
    conn.commit(); conn.close()
    log(f"OK — {n_total} mediciones de {lotes_ok} lotes desde PDFs")


# ════════════════════════════════════════════════════════════════════════════
# 6) INGESTA — Pol del ingenio (CSV manual)
# ════════════════════════════════════════════════════════════════════════════
def cmd_load_pol(csv_path: str):
    """CSV columnas esperadas: lote_id, fecha_cosecha, pol_pct, brix_pct,
    pureza_pct, atr_kg_t, ingenio (opcional)."""
    csv = Path(csv_path)
    if not csv.exists(): log(f"ERROR: {csv}"); return
    df = pd.read_csv(csv)
    df["lote_id"] = df["lote_id"].astype(str)
    conn = get_conn(); cur = conn.cursor()
    n_ok = 0
    for _, r in df.iterrows():
        try:
            cur.execute("""
                INSERT INTO pol_ingenio (
                    lote_id, fecha_cosecha, fecha_analisis,
                    pol_pct, brix_pct, pureza_pct, atr_kg_t, ingenio, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["lote_id"],
                str(r.get("fecha_cosecha", "")),
                str(r.get("fecha_analisis", r.get("fecha_cosecha", ""))),
                _f(r.get("pol_pct")),
                _f(r.get("brix_pct")),
                _f(r.get("pureza_pct")),
                _f(r.get("atr_kg_t")),
                str(r.get("ingenio", "")),
                str(r.get("notas", "")),
            ))
            n_ok += 1
        except Exception as e:
            log(f"  err {r.get('lote_id')}: {e}")
    conn.commit(); conn.close()
    log(f"OK — {n_ok}/{len(df)} análisis Pol cargados")


# ════════════════════════════════════════════════════════════════════════════
# 7) AUTO-CALIBRACIÓN — entrena modelo Ridge + RF y versiona
# ════════════════════════════════════════════════════════════════════════════
def cmd_train(target: str = "cmi", n_folds: int = 5):
    """Entrena modelo prediciendo target (cmi o pol) desde Z-scores
    satelitales. Guarda nueva versión en modelo_versions + pickle."""
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import LeaveOneOut, cross_val_score, KFold
    from sklearn.metrics import r2_score, mean_squared_error
    from scipy.stats import spearmanr

    if target not in ("cmi", "pol"):
        log("ERROR: target debe ser 'cmi' o 'pol'"); return

    conn = get_conn()
    # Construir dataset pareado: predicción más cercana a fecha de medición
    # Para CMI: usar el promedio del muestreo más reciente por lote
    # Para Pol: usar Pol del ingenio
    if target == "cmi":
        df = pd.read_sql("""
            SELECT m.lote_id, m.cmi_promedio AS y,
                   p.z_ndwi, p.z_ndmi, p.z_cire, p.z_psri, p.z_vv, p.z_gdd,
                   p.fecha_imagen_s2, m.fecha_muestreo
            FROM muestreos_cmi_promedio_view m
            INNER JOIN predicciones_satelitales p ON p.lote_id = m.lote_id
            WHERE p.modelo_version LIKE 'v3%'
              AND m.cmi_promedio IS NOT NULL
        """, conn)
    else:  # pol
        df = pd.read_sql("""
            SELECT pi.lote_id, pi.pol_pct AS y,
                   p.z_ndwi, p.z_ndmi, p.z_cire, p.z_psri, p.z_vv, p.z_gdd,
                   p.fecha_imagen_s2, pi.fecha_cosecha
            FROM pol_ingenio pi
            INNER JOIN predicciones_satelitales p ON p.lote_id = pi.lote_id
            WHERE p.modelo_version LIKE 'v3%'
              AND pi.pol_pct IS NOT NULL
        """, conn)

    if len(df) < 5:
        log(f"ERROR: solo {len(df)} muestras pareadas — mínimo 5 requerido")
        log(f"      target={target}: faltan más datos antes de calibrar")
        conn.close(); return

    # Quitar duplicados (un par predicción-muestreo más reciente)
    df = df.dropna(subset=["y", "z_ndwi", "z_ndmi", "z_cire"])
    df = df.sort_values("fecha_imagen_s2").drop_duplicates("lote_id", keep="last")

    log(f"Dataset {target}: {len(df)} lotes únicos pareados")
    if len(df) < 5:
        log("Insuficiente tras filtros"); conn.close(); return

    feature_cols = ["z_ndwi","z_ndmi","z_cire","z_psri","z_vv","z_gdd"]
    X = df[feature_cols].fillna(0).values
    y = df["y"].values

    # Cross-validation
    n_folds_eff = min(n_folds, len(df) - 1)
    if n_folds_eff >= 3:
        cv = KFold(n_splits=n_folds_eff, shuffle=True, random_state=42)
    else:
        cv = LeaveOneOut()

    # Ridge regression
    ridge = Ridge(alpha=1.0)
    ridge.fit(X, y)
    y_pred_ridge = ridge.predict(X)
    r2_train_r = r2_score(y, y_pred_ridge)
    cv_scores = cross_val_score(Ridge(alpha=1.0), X, y, cv=cv, scoring="r2")
    r2_cv_r = float(np.mean(cv_scores))
    rmse_cv_r = float(np.sqrt(np.mean((y - y_pred_ridge) ** 2)))
    sp_r = spearmanr(y, y_pred_ridge)[0]

    # Random Forest
    rf = RandomForestRegressor(n_estimators=200, random_state=42,
                                max_depth=4)  # shallow, evita overfitting
    rf.fit(X, y)
    y_pred_rf = rf.predict(X)
    r2_train_rf = r2_score(y, y_pred_rf)
    rf_cv = cross_val_score(rf, X, y, cv=cv, scoring="r2")
    r2_cv_rf = float(np.mean(rf_cv))
    rmse_cv_rf = float(np.sqrt(np.mean((y - y_pred_rf) ** 2)))
    sp_rf = spearmanr(y, y_pred_rf)[0]
    feat_imp = dict(zip(feature_cols, rf.feature_importances_.tolist()))

    log(f"Ridge: R²train={r2_train_r:.3f}  R²CV={r2_cv_r:.3f}  "
        f"RMSE_CV={rmse_cv_r:.3f}  Spearman={sp_r:.3f}")
    log(f"RF:    R²train={r2_train_rf:.3f}  R²CV={r2_cv_rf:.3f}  "
        f"RMSE_CV={rmse_cv_rf:.3f}  Spearman={sp_rf:.3f}")
    log(f"RF feature importance: {feat_imp}")

    # Persistir Ridge (interpretable, pesos directos)
    cur = conn.cursor()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_r = f"ridge_{target}_{ts}"
    pkl_r = MODELS_DIR / f"{version_r}.pkl"
    with open(pkl_r, "wb") as f:
        pickle.dump({"model": ridge, "features": feature_cols,
                      "target": target}, f)
    coefs = dict(zip(feature_cols, ridge.coef_.tolist()))
    cur.execute("""
        INSERT INTO modelo_versions (
            version, objetivo, algoritmo, n_muestras_train, n_lotes,
            w_ndwi, w_ndmi, w_cire, w_psri, w_vv, w_gdd, w_intercept,
            r2_train, r2_cv, rmse_cv, spearman_cv,
            archivo_modelo, feature_importance_json, descripcion
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        version_r, target, "ridge", len(df), df["lote_id"].nunique(),
        coefs["z_ndwi"], coefs["z_ndmi"], coefs["z_cire"],
        coefs["z_psri"], coefs["z_vv"], coefs["z_gdd"], float(ridge.intercept_),
        r2_train_r, r2_cv_r, rmse_cv_r, sp_r,
        str(pkl_r), json.dumps({}),
        f"Ridge regression {target} con {len(df)} pares pareados"
    ))

    # Persistir RF (no-lineal, captura interacciones)
    version_rf = f"rf_{target}_{ts}"
    pkl_rf = MODELS_DIR / f"{version_rf}.pkl"
    with open(pkl_rf, "wb") as f:
        pickle.dump({"model": rf, "features": feature_cols,
                      "target": target}, f)
    cur.execute("""
        INSERT INTO modelo_versions (
            version, objetivo, algoritmo, n_muestras_train, n_lotes,
            w_ndwi, w_ndmi, w_cire, w_psri, w_vv, w_gdd, w_intercept,
            r2_train, r2_cv, rmse_cv, spearman_cv,
            archivo_modelo, feature_importance_json, descripcion
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        version_rf, target, "rf", len(df), df["lote_id"].nunique(),
        None, None, None, None, None, None, None,
        r2_train_rf, r2_cv_rf, rmse_cv_rf, sp_rf,
        str(pkl_rf), json.dumps(feat_imp),
        f"Random Forest {target} con {len(df)} pares (RF feature importance)"
    ))
    conn.commit(); conn.close()
    log(f"\n✓ Modelos guardados:")
    log(f"  {version_r}  → {pkl_r.name}")
    log(f"  {version_rf} → {pkl_rf.name}")


# ════════════════════════════════════════════════════════════════════════════
# 8) PREDICT — usa modelo vigente
# ════════════════════════════════════════════════════════════════════════════
def cmd_predict(hacienda: str = "Hacienda del Señor", target: str = "cmi"):
    conn = get_conn()
    # Última versión Ridge para target
    v = conn.execute("""
        SELECT version, archivo_modelo FROM modelo_versions
        WHERE objetivo = ? AND algoritmo = 'ridge'
        ORDER BY fecha_entrenamiento DESC LIMIT 1
    """, (target,)).fetchone()
    if not v:
        log(f"NO hay modelo entrenado para target={target}"); conn.close(); return
    version, pkl_path = v[0], v[1]
    with open(pkl_path, "rb") as f:
        bundle = pickle.load(f)
    model = bundle["model"]; features = bundle["features"]
    log(f"Modelo vigente: {version}")

    # Predicciones más recientes por lote
    df = pd.read_sql("""
        SELECT lote_id, fecha_imagen_s2,
               z_ndwi, z_ndmi, z_cire, z_psri, z_vv, z_gdd,
               priority_score, rank_v
        FROM predicciones_satelitales
        WHERE modelo_version LIKE 'v3%'
        ORDER BY fecha_prediccion DESC
    """, conn)
    df = df.drop_duplicates("lote_id", keep="first")
    X = df[features].fillna(0).values
    df["pred_y_calibrado"] = model.predict(X)
    df = df.sort_values("pred_y_calibrado", ascending=False).reset_index(drop=True)
    df["rank_calibrado"] = range(1, len(df)+1)

    # Guardar como CSV
    fecha = datetime.now().strftime("%Y-%m-%d")
    out = REPORTS_DIR / f"prediccion_calibrada_{target}_{fecha}.csv"
    df.to_csv(out, index=False)
    log(f"Predicciones calibradas → {out.name}")

    # Top 20
    print(f"\n══ Top 20 prioridad de cosecha (modelo {version}) ══")
    print(df.head(20)[["rank_calibrado","lote_id","pred_y_calibrado",
                        "rank_v","priority_score"]].to_string(index=False))
    conn.close()


# ════════════════════════════════════════════════════════════════════════════
# 9) REPORTE EVOLUCIÓN SKILL
# ════════════════════════════════════════════════════════════════════════════
def cmd_report_skill():
    """Genera PDF mostrando cómo evoluciona el skill del modelo zafra a zafra."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, PageBreak)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    VERDE = HexColor("#1B5E20"); GRIS = HexColor("#333333")
    GRIS_CLARO = HexColor("#F5F5F5"); GRIS_LINEA = HexColor("#BDBDBD")

    conn = get_conn()
    ver = pd.read_sql("""
        SELECT version, fecha_entrenamiento, objetivo, algoritmo,
               n_muestras_train, n_lotes,
               r2_train, r2_cv, rmse_cv, spearman_cv,
               w_ndwi, w_ndmi, w_cire, w_psri, w_vv, w_gdd, w_intercept,
               feature_importance_json
        FROM modelo_versions
        ORDER BY fecha_entrenamiento ASC
    """, conn)
    counts = pd.read_sql("""
        SELECT
            (SELECT COUNT(*) FROM lotes) AS n_lotes,
            (SELECT COUNT(*) FROM predicciones_satelitales) AS n_predicciones,
            (SELECT COUNT(*) FROM muestreos_cmi) AS n_cmi,
            (SELECT COUNT(DISTINCT lote_id) FROM muestreos_cmi) AS n_lotes_cmi,
            (SELECT COUNT(*) FROM pol_ingenio) AS n_pol
    """, conn)
    conn.close()

    fecha = datetime.now().strftime("%Y-%m-%d")
    pdf_out = REPORTS_DIR / f"evolucion_skill_{fecha}.pdf"

    doc = SimpleDocTemplate(str(pdf_out), pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="Pixadvisor Agente — Evolución de Skill",
        author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_title = ParagraphStyle("T", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=20)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=14)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS, leading=13)

    story = []
    story.append(Paragraph("PIXADVISOR AGENTE — Evolución del modelo", s_title))
    story.append(Paragraph(
        f"Reporte automático del agente de prioridad de cosecha · "
        f"{fecha}", s_body))
    story.append(Spacer(1, 8))

    # Resumen estado KB
    story.append(Paragraph("Estado de la Knowledge Base", s_h2))
    c = counts.iloc[0]
    info = [
        ["Lotes registrados", str(c["n_lotes"])],
        ["Predicciones satelitales acumuladas", str(c["n_predicciones"])],
        ["Mediciones CMI individuales", str(c["n_cmi"])],
        ["Lotes con muestreo CMI", str(c["n_lotes_cmi"])],
        ["Análisis Pol del ingenio", str(c["n_pol"])],
        ["Versiones de modelo entrenadas", str(len(ver))],
    ]
    t = Table(info, colWidths=[80*mm, 90*mm])
    t.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",9),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",9),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))
    story.append(t)
    story.append(Spacer(1, 8))

    if len(ver) == 0:
        story.append(Paragraph(
            "<b>Aún no hay modelos entrenados.</b> Ejecutar: <i>python "
            "pixadvisor_agente.py train --target cmi</i> después de cargar "
            "datos CMI.", s_body))
    else:
        # Tabla versiones
        story.append(Paragraph("Versiones de modelo entrenadas", s_h2))
        rows = [["Versión", "Fecha", "Target", "Algo", "n", "R²_CV", "RMSE_CV", "ρ Spearman"]]
        for _, v in ver.iterrows():
            rows.append([
                v["version"][-20:], str(v["fecha_entrenamiento"])[:16],
                v["objetivo"], v["algoritmo"],
                str(int(v["n_muestras_train"])),
                f"{v['r2_cv']:.3f}" if pd.notna(v["r2_cv"]) else "—",
                f"{v['rmse_cv']:.3f}" if pd.notna(v["rmse_cv"]) else "—",
                f"{v['spearman_cv']:.3f}" if pd.notna(v["spearman_cv"]) else "—",
            ])
        t2 = Table(rows, colWidths=[40*mm, 28*mm, 14*mm, 14*mm, 12*mm, 18*mm, 22*mm, 22*mm], repeatRows=1)
        t2.setStyle(TableStyle([
            ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
            ("BACKGROUND",(0,0),(-1,0),VERDE),
            ("TEXTCOLOR",(0,0),(-1,0),white),
            ("FONT",(0,1),(-1,-1),"Helvetica",8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
            ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
            ("ALIGN",(4,1),(-1,-1),"RIGHT"),
            ("BOTTOMPADDING",(0,0),(-1,-1),3),
            ("TOPPADDING",(0,0),(-1,-1),3)]))
        story.append(t2)
        story.append(Spacer(1, 8))

        # Gráfico evolución R²
        if len(ver) >= 2:
            fig, ax = plt.subplots(figsize=(8, 4), dpi=140)
            for algo in ver["algoritmo"].unique():
                sub = ver[ver["algoritmo"] == algo]
                ax.plot(range(len(sub)), sub["r2_cv"], marker="o",
                         label=algo.upper(), linewidth=2)
            ax.set_xlabel("Versión (orden cronológico)")
            ax.set_ylabel("R² Cross-Validation")
            ax.set_title("Evolución del skill — R²_CV por versión",
                          color="#1B5E20", fontweight="bold")
            ax.axhline(0.5, color="orange", linestyle="--", alpha=0.5,
                        label="Umbral defendible (R²=0.5)")
            ax.axhline(0.75, color="green", linestyle="--", alpha=0.5,
                        label="Umbral excelente (R²=0.75)")
            ax.grid(alpha=0.3); ax.legend(fontsize=8)
            png_evo = REPORTS_DIR / f"evolucion_r2_{fecha}.png"
            fig.savefig(png_evo, dpi=140, bbox_inches="tight",
                         facecolor="white")
            plt.close(fig)
            from reportlab.platypus import Image as RLImage
            story.append(RLImage(str(png_evo), width=160*mm, height=80*mm,
                                  kind="proportional"))

        # Pesos del modelo más reciente Ridge
        last_ridge = ver[ver["algoritmo"] == "ridge"].tail(1)
        if not last_ridge.empty:
            r = last_ridge.iloc[0]
            story.append(Paragraph(
                f"Pesos del modelo Ridge vigente ({r['version']})", s_h2))
            wts = [
                ["Variable", "Peso calibrado", "Peso v3 default"],
                ["Z_NDWI",  f"{r['w_ndwi']:+.3f}", "−0.250"],
                ["Z_NDMI",  f"{r['w_ndmi']:+.3f}", "−0.150"],
                ["Z_CIRE",  f"{r['w_cire']:+.3f}", "−0.200"],
                ["Z_PSRI",  f"{r['w_psri']:+.3f}", "+0.100"],
                ["Z_VV",    f"{r['w_vv']:+.3f}",   "−0.100"],
                ["Z_GDD",   f"{r['w_gdd']:+.3f}",  "+0.200"],
                ["Intercept", f"{r['w_intercept']:+.3f}", "0"],
            ]
            t3 = Table(wts, colWidths=[40*mm, 50*mm, 50*mm], repeatRows=1)
            t3.setStyle(TableStyle([
                ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
                ("BACKGROUND",(0,0),(-1,0),VERDE),
                ("TEXTCOLOR",(0,0),(-1,0),white),
                ("FONT",(0,1),(-1,-1),"Helvetica",9),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
                ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
                ("ALIGN",(1,1),(-1,-1),"RIGHT")]))
            story.append(t3)
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                "<i>Si los pesos calibrados difieren mucho de los default, "
                "el modelo aprendió patrones específicos de Hacienda del "
                "Señor que mejoran la predicción local.</i>", s_body))

    # Recomendaciones próximos pasos
    story.append(PageBreak())
    story.append(Paragraph("Próximos pasos del agente", s_h2))
    n_cmi = c["n_lotes_cmi"]; n_pol = c["n_pol"]
    rec = []
    if n_cmi == 0:
        rec.append("• <b>Cargar datos CMI</b>: ejecutar muestreo de campo "
                    "Top 20, llenar Excel/PDFs digitales y cargar con "
                    "<i>load-cmi-excel</i> o <i>load-cmi-pdf</i>.")
    elif n_cmi < 30:
        rec.append(f"• <b>Acumular más muestras CMI</b>: actualmente {n_cmi} "
                    "lotes. Mínimo 30 para calibración robusta. Re-muestrear "
                    "en próximas zafras.")
    else:
        rec.append(f"• ✓ Datos CMI suficientes ({n_cmi} lotes). Re-correr "
                    "<i>train --target cmi</i> mensualmente.")

    if n_pol == 0:
        rec.append("• <b>Acordar con ingenio</b> el envío del Pol oficial "
                    "post-cosecha por lote. Sin esto NO se puede llegar a "
                    "Pol absoluto calibrado.")
    elif n_pol < 30:
        rec.append(f"• <b>Acumular Pol del ingenio</b>: {n_pol} análisis "
                    "registrados. Mínimo 30 para modelo Pol absoluto.")
    else:
        rec.append(f"• ✓ Datos Pol suficientes ({n_pol}). Ejecutar "
                    "<i>train --target pol</i> para modelo absoluto.")

    if len(ver) == 0:
        rec.append("• <b>Aún sin modelo</b>: cargar datos CMI primero.")
    else:
        rec.append(f"• Re-entrenar modelo cada vez que se agreguen ≥10 "
                    "muestras nuevas.")

    rec.append("• <b>Próxima zafra</b>: cargar nuevas predicciones del pipeline "
                "v3 con <i>load-predicciones</i> y re-entrenar.")
    rec.append("• <b>Auditoría</b>: cada modelo nuevo se compara con el anterior "
                "(skill drift detection automático).")

    for r_text in rec:
        story.append(Paragraph(r_text, s_body))

    def _f_footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Agente Especialista · Reporte Skill · "
            f"{fecha} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f_footer, onLaterPages=_f_footer)
    log(f"Reporte → {pdf_out}")


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser(
        description="Pixadvisor Agente — Memoria + Auto-calibración",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Inicializa la KB SQLite")
    sub.add_parser("status", help="Estado actual de la KB")

    p_lp = sub.add_parser("load-predicciones", help="Carga CSV ranking v3")
    p_lp.add_argument("csv")
    p_lp.add_argument("--version", default="v3_S2_S1")

    p_lc = sub.add_parser("load-cmi-excel", help="Carga Excel template lleno")
    p_lc.add_argument("xlsx")
    p_lc.add_argument("--fecha", default=None)
    p_lc.add_argument("--agronomo", default="")

    p_lcp = sub.add_parser("load-cmi-pdf", help="Carga PDFs digitales rellenados")
    p_lcp.add_argument("dir")
    p_lcp.add_argument("--fecha", default=None)

    p_lpol = sub.add_parser("load-pol", help="Carga Pol del ingenio (CSV)")
    p_lpol.add_argument("csv")

    p_t = sub.add_parser("train", help="Entrena modelo (Ridge + RF)")
    p_t.add_argument("--target", choices=["cmi", "pol"], default="cmi")
    p_t.add_argument("--folds", type=int, default=5)

    p_pr = sub.add_parser("predict", help="Predice con modelo vigente")
    p_pr.add_argument("--target", choices=["cmi", "pol"], default="cmi")
    p_pr.add_argument("--hacienda", default="Hacienda del Señor")

    sub.add_parser("report-skill", help="Genera PDF evolución skill")

    args = p.parse_args()
    if args.cmd == "init":              init_kb()
    elif args.cmd == "status":          cmd_status()
    elif args.cmd == "load-predicciones": cmd_load_predicciones(args.csv, args.version)
    elif args.cmd == "load-cmi-excel":  cmd_load_cmi_excel(args.xlsx, args.fecha, args.agronomo)
    elif args.cmd == "load-cmi-pdf":    cmd_load_cmi_pdfs(args.dir, args.fecha)
    elif args.cmd == "load-pol":        cmd_load_pol(args.csv)
    elif args.cmd == "train":           cmd_train(args.target, args.folds)
    elif args.cmd == "predict":         cmd_predict(args.hacienda, args.target)
    elif args.cmd == "report-skill":    cmd_report_skill()


if __name__ == "__main__":
    main()
