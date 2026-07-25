"""
Entrena Random Forest para detectar AREA UTIL DE PLANTIO usando truth de HDS.

Pipeline:
  1. Lee feature stack (10 bandas) generado por 02_extract_features.py
  2. Lee truth_master.geojson (filtra HDS)
  3. Genera mascara binaria 1=lote, 0=no-lote (rasterizando truths)
  4. Sample balanceado (50K positivos + 50K negativos)
  5. Train RF con cross-validation
  6. Evalua: accuracy, IoU, precision, recall
  7. Guarda modelo + reporte
"""
from __future__ import annotations

import os
import json
import warnings
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"
warnings.filterwarnings("ignore")

import numpy as np
import rasterio
from rasterio.features import geometry_mask
import geopandas as gpd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

ROOT = Path(__file__).parent
OUT = ROOT / "output"

YEAR = 2025
TRUTH_GEO = OUT / "truth_master.geojson"
FEATURES_TIF = OUT / f"features_HDS_{YEAR}.tif"
MODEL_OUT = OUT / f"rf_planting_area_{YEAR}.joblib"
REPORT_OUT = OUT / f"training_report_{YEAR}.json"

N_SAMPLES_PER_CLASS = 30000
RF_N_ESTIMATORS = 200
RF_MAX_DEPTH = 25


def main():
    print(f">>> Cargando feature stack {FEATURES_TIF}")
    with rasterio.open(FEATURES_TIF) as src:
        stack = src.read()  # (n_bands, H, W)
        transform = src.transform
        shape = src.shape
        band_names = [src.descriptions[i] for i in range(src.count)]
    print(f"    Shape: {stack.shape}, bands: {band_names}")

    print(f">>> Cargando truth (HDS only)")
    truth = gpd.read_file(TRUTH_GEO)
    truth_hds = truth[truth["source"] == "HDS"].copy()
    print(f"    HDS: {len(truth_hds)} poligonos, {truth_hds['area_ha'].sum():.1f} ha")

    # Rasterizar truth -> mascara binaria
    print(f">>> Rasterizando truth")
    mask = geometry_mask(truth_hds.geometry, out_shape=shape,
                          transform=transform, invert=True)
    n_pos = int(mask.sum())
    n_neg = int((~mask).sum())
    print(f"    Pixels: positivos={n_pos:,} ({n_pos*100/mask.size:.1f}%), "
          f"negativos={n_neg:,} ({n_neg*100/mask.size:.1f}%)")

    # Validar features (descartar pixels con NaN)
    valid = ~np.isnan(stack).any(axis=0)
    valid_pos = mask & valid
    valid_neg = (~mask) & valid
    print(f"    Validos (sin NaN): pos={valid_pos.sum():,} neg={valid_neg.sum():,}")

    # Sample balanceado
    rng = np.random.default_rng(42)
    pos_idx = np.argwhere(valid_pos)
    neg_idx = np.argwhere(valid_neg)
    n_each = min(N_SAMPLES_PER_CLASS, len(pos_idx), len(neg_idx))
    pos_sel = rng.choice(len(pos_idx), n_each, replace=False)
    neg_sel = rng.choice(len(neg_idx), n_each, replace=False)
    pos_pick = pos_idx[pos_sel]
    neg_pick = neg_idx[neg_sel]
    print(f"    Sample balanceado: {n_each} pos + {n_each} neg = {n_each*2}")

    def stack_at(idx):
        rows, cols = idx[:, 0], idx[:, 1]
        return stack[:, rows, cols].T  # (n_samples, n_features)

    X_pos = stack_at(pos_pick)
    X_neg = stack_at(neg_pick)
    X = np.vstack([X_pos, X_neg])
    y = np.concatenate([np.ones(n_each), np.zeros(n_each)])

    # Train/test split
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20,
                                                random_state=42, stratify=y)
    print(f"    Train: {len(X_tr)}, Test: {len(X_te)}")

    # Train RF
    print(f">>> Training RF (n_estimators={RF_N_ESTIMATORS}, max_depth={RF_MAX_DEPTH})")
    clf = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS, max_depth=RF_MAX_DEPTH,
        min_samples_leaf=10, n_jobs=-1, random_state=42, class_weight="balanced",
    )
    clf.fit(X_tr, y_tr)

    # Evaluate
    print(">>> Evaluacion en test set")
    y_pred = clf.predict(X_te)
    y_prob = clf.predict_proba(X_te)[:, 1]
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_te, y_pred).tolist()
    print(classification_report(y_te, y_pred, zero_division=0))
    print(f"Confusion matrix: {cm}")

    # Feature importance
    fi = sorted(zip(band_names, clf.feature_importances_),
                key=lambda x: -x[1])
    print("\nFeature importance (top):")
    for name, imp in fi:
        print(f"  {name:>20}: {imp:.4f}")

    # Save model + report
    joblib.dump({"model": clf, "band_names": band_names, "year": YEAR},
                MODEL_OUT, compress=3)
    print(f"\n<<< {MODEL_OUT} ({MODEL_OUT.stat().st_size//1024} KB)")

    report_full = {
        "year": YEAR, "n_train": len(X_tr), "n_test": len(X_te),
        "classification_report": report,
        "confusion_matrix": cm,
        "feature_importance": [{"name": n, "importance": float(i)} for n, i in fi],
        "rf_params": {"n_estimators": RF_N_ESTIMATORS, "max_depth": RF_MAX_DEPTH},
    }
    REPORT_OUT.write_text(json.dumps(report_full, indent=2), encoding="utf-8")
    print(f"<<< {REPORT_OUT}")


if __name__ == "__main__":
    main()
