"""
Train V2: LightGBM con stack 28 features.

Mejoras vs V1:
  - LightGBM (gradient boosting) supera tipicamente a RF en tabular
  - 28 features (vs 10) -> mas senial discriminante
  - Early stopping para evitar overfitting
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
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import lightgbm as lgb
import joblib

ROOT = Path(__file__).parent
OUT = ROOT / "output"

YEAR = 2025
TRUTH_GEO = OUT / "truth_master.geojson"
FEATURES_TIF = OUT / f"features_v2_HDS_{YEAR}.tif"
MODEL_OUT = OUT / f"lgb_planting_area_v2_{YEAR}.joblib"
REPORT_OUT = OUT / f"training_report_v2_{YEAR}.json"

N_SAMPLES_PER_CLASS = 50000  # mas que V1 (30K)


def main():
    print(f">>> Cargando feature stack V2 {FEATURES_TIF}")
    with rasterio.open(FEATURES_TIF) as src:
        stack = src.read()
        transform = src.transform
        shape = src.shape
        band_names = [src.descriptions[i] or f"b{i+1}" for i in range(src.count)]
    print(f"    Shape: {stack.shape}, bands ({len(band_names)}): {band_names[:5]}...")

    print(">>> Cargando truth (HDS)")
    truth = gpd.read_file(TRUTH_GEO)
    truth_hds = truth[truth["source"] == "HDS"].copy()
    print(f"    HDS: {len(truth_hds)} poligonos, {truth_hds['area_ha'].sum():.1f} ha")

    print(">>> Rasterizando truth")
    mask = geometry_mask(truth_hds.geometry, out_shape=shape,
                          transform=transform, invert=True)
    valid = ~np.isnan(stack).any(axis=0)
    valid_pos = mask & valid
    valid_neg = (~mask) & valid
    print(f"    Pos validos: {valid_pos.sum():,}  Neg: {valid_neg.sum():,}")

    rng = np.random.default_rng(42)
    pos_idx = np.argwhere(valid_pos)
    neg_idx = np.argwhere(valid_neg)
    n_each = min(N_SAMPLES_PER_CLASS, len(pos_idx), len(neg_idx))
    pos_pick = pos_idx[rng.choice(len(pos_idx), n_each, replace=False)]
    neg_pick = neg_idx[rng.choice(len(neg_idx), n_each, replace=False)]
    print(f"    Sample: {n_each} pos + {n_each} neg")

    def stack_at(idx):
        rows, cols = idx[:, 0], idx[:, 1]
        return stack[:, rows, cols].T

    X = np.vstack([stack_at(pos_pick), stack_at(neg_pick)])
    y = np.concatenate([np.ones(n_each), np.zeros(n_each)])

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20,
                                                random_state=42, stratify=y)
    print(f"    Train: {len(X_tr)}, Test: {len(X_te)}")

    # LightGBM
    print(">>> Training LightGBM")
    dtr = lgb.Dataset(X_tr, label=y_tr, feature_name=band_names)
    dte = lgb.Dataset(X_te, label=y_te, feature_name=band_names, reference=dtr)

    params = {
        "objective": "binary",
        "metric": ["binary_logloss", "auc"],
        "learning_rate": 0.05,
        "num_leaves": 127,
        "max_depth": -1,
        "min_data_in_leaf": 20,
        "feature_fraction": 0.85,
        "bagging_fraction": 0.85,
        "bagging_freq": 5,
        "lambda_l2": 0.1,
        "verbose": -1,
        "n_jobs": -1,
        "seed": 42,
    }
    model = lgb.train(
        params, dtr,
        num_boost_round=500,
        valid_sets=[dtr, dte],
        valid_names=["train", "val"],
        callbacks=[lgb.early_stopping(30), lgb.log_evaluation(50)],
    )
    print(f"    Best iter: {model.best_iteration}")

    # Evaluate
    y_prob = model.predict(X_te, num_iteration=model.best_iteration)
    y_pred = (y_prob > 0.5).astype(int)
    auc = roc_auc_score(y_te, y_prob)
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_te, y_pred).tolist()
    print(f"\n>>> Test AUC: {auc:.4f}")
    print(classification_report(y_te, y_pred, zero_division=0))
    print(f"Confusion: {cm}")

    # Feature importance
    fi = sorted(zip(band_names, model.feature_importance(importance_type="gain")),
                key=lambda x: -x[1])
    total = sum(i for _, i in fi)
    print("\nFeature importance (top 10 por gain):")
    for name, imp in fi[:10]:
        print(f"  {name:>22}: {imp/total*100:.2f}%")

    joblib.dump({"model": model, "band_names": band_names, "year": YEAR,
                 "best_iteration": model.best_iteration},
                MODEL_OUT, compress=3)
    print(f"\n<<< {MODEL_OUT} ({MODEL_OUT.stat().st_size//1024} KB)")

    report_full = {
        "year": YEAR, "n_features": len(band_names),
        "n_train": len(X_tr), "n_test": len(X_te),
        "test_auc": float(auc),
        "classification_report": report,
        "confusion_matrix": cm,
        "feature_importance": [{"name": n, "importance_gain": float(i)} for n, i in fi],
        "best_iteration": int(model.best_iteration),
        "params": {k: v for k, v in params.items() if not isinstance(v, list)},
    }
    REPORT_OUT.write_text(json.dumps(report_full, indent=2), encoding="utf-8")
    print(f"<<< {REPORT_OUT}")


if __name__ == "__main__":
    main()
