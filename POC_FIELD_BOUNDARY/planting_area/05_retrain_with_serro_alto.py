"""
Reentrena modelo V2 agregando Cerro Alto 2 como nueva region de training.

Necesitamos:
  1. Truth master expandido con SA2 (truth_master_v3.geojson)
  2. Feature stack para Cerro Alto 2 (ya cacheado en s2_cache/v2_features)
  3. Sample balanceado HDS + SA2
  4. Reentrenar LightGBM
  5. Guardar nuevo modelo lgb_planting_area_v3_2025.joblib
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
from sklearn.metrics import classification_report, roc_auc_score
import lightgbm as lgb
import joblib
import shutil

ROOT = Path(__file__).parent
OUT = ROOT / "output"

YEAR = 2025
TRUTH_GEO = OUT / "truth_master.geojson"
TRUTH_V3_GEO = OUT / "truth_master_v3.geojson"
SERRO2_KML = Path(r"C:/Users/Usuario/Desktop/Serro Alto 2.kml")

HDS_FEATURES = OUT / f"features_v2_HDS_{YEAR}.tif"
SA2_FEATURES_CACHE = ROOT.parent / "output" / "s2_cache" / "v2_features" / f"v2_-58.9042_-18.5264_-58.7762_-18.3786_{YEAR}.tif"
SA2_FEATURES_LOCAL = OUT / f"features_v2_SERRO2_{YEAR}.tif"

MODEL_OUT = OUT / f"lgb_planting_area_v3_{YEAR}.joblib"
REPORT_OUT = OUT / f"training_report_v3_{YEAR}.json"

N_SAMPLES_HDS = 30000
N_SAMPLES_SA2 = 30000
N_NEG_HDS = 30000
N_NEG_SA2 = 30000


def main():
    # 1) Agregar SA2 al truth master
    print(">>> Agregando Cerro Alto 2 al truth master")
    base = gpd.read_file(TRUTH_GEO)
    print(f"    Truth original: {len(base)} features ({base['source'].value_counts().to_dict()})")

    import fiona
    fiona.drvsupport.supported_drivers["KML"] = "rw"
    sa2 = gpd.read_file(SERRO2_KML, driver="KML")
    sa2 = sa2.to_crs("EPSG:4326")
    sa2["source"] = "SERRO_ALTO_2"
    sa2["lote_name"] = "serro_alto_2_full"
    sa2_utm = sa2.to_crs(32720)
    sa2["area_ha"] = sa2_utm.area.values / 10_000
    keep_cols = [c for c in base.columns if c in sa2.columns or c == "geometry"]
    sa2 = sa2[[c for c in ["source","lote_name","area_ha","geometry"] if c in sa2.columns]]
    print(f"    SA2: {len(sa2)} features, {sa2['area_ha'].sum():.1f} ha")

    import pandas as pd
    combined = pd.concat([base, sa2], ignore_index=True)
    combined = gpd.GeoDataFrame(combined, geometry="geometry", crs="EPSG:4326")
    combined.to_file(TRUTH_V3_GEO, driver="GeoJSON")
    print(f"<<< {TRUTH_V3_GEO} ({len(combined)} features)")

    # 2) Copiar SA2 features a planting_area/output/ para uso consistente
    if SA2_FEATURES_CACHE.exists() and not SA2_FEATURES_LOCAL.exists():
        shutil.copy2(SA2_FEATURES_CACHE, SA2_FEATURES_LOCAL)
        print(f"    SA2 features copy: {SA2_FEATURES_LOCAL}")

    # 3) Para HDS: rasterizar truth y samplear
    print("\n>>> HDS sampling")
    with rasterio.open(HDS_FEATURES) as src:
        hds_stack = src.read(); hds_transform = src.transform; hds_shape = src.shape
        band_names = [src.descriptions[i] or f"b{i+1}" for i in range(src.count)]
    hds_mask = geometry_mask(combined[combined.source=="HDS"].geometry,
                              out_shape=hds_shape, transform=hds_transform, invert=True)
    hds_valid = ~np.isnan(hds_stack).any(axis=0)
    hds_pos = np.argwhere(hds_mask & hds_valid)
    hds_neg = np.argwhere((~hds_mask) & hds_valid)

    # 4) Para SA2: rasterizar truth y samplear
    print(">>> SA2 sampling")
    with rasterio.open(SA2_FEATURES_LOCAL) as src:
        sa2_stack = src.read(); sa2_transform = src.transform; sa2_shape = src.shape
    sa2_mask = geometry_mask(combined[combined.source=="SERRO_ALTO_2"].geometry,
                              out_shape=sa2_shape, transform=sa2_transform, invert=True)
    sa2_valid = ~np.isnan(sa2_stack).any(axis=0)
    sa2_pos = np.argwhere(sa2_mask & sa2_valid)
    sa2_neg = np.argwhere((~sa2_mask) & sa2_valid)
    print(f"    HDS pos={len(hds_pos)}, neg={len(hds_neg)}")
    print(f"    SA2 pos={len(sa2_pos)}, neg={len(sa2_neg)}")

    # 5) Sample y construir matriz combinada
    rng = np.random.default_rng(42)
    def sample(idx, n):
        if len(idx) == 0: return np.empty((0,2), dtype=int)
        n = min(n, len(idx))
        return idx[rng.choice(len(idx), n, replace=False)]

    def stack_at(stack_arr, idx):
        rows, cols = idx[:,0], idx[:,1]
        return stack_arr[:, rows, cols].T

    X_parts = []; y_parts = []; src_parts = []
    for src, stack_arr, pos, neg, n_p, n_n in [
        ("HDS", hds_stack, hds_pos, hds_neg, N_SAMPLES_HDS, N_NEG_HDS),
        ("SA2", sa2_stack, sa2_pos, sa2_neg, N_SAMPLES_SA2, N_NEG_SA2),
    ]:
        pp = sample(pos, n_p); nn = sample(neg, n_n)
        if len(pp): X_parts.append(stack_at(stack_arr, pp)); y_parts.append(np.ones(len(pp))); src_parts.extend([src]*len(pp))
        if len(nn): X_parts.append(stack_at(stack_arr, nn)); y_parts.append(np.zeros(len(nn))); src_parts.extend([src]*len(nn))

    X = np.vstack(X_parts); y = np.concatenate(y_parts)
    print(f"    Total samples: {len(X)} (pos={(y==1).sum()}, neg={(y==0).sum()})")

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20,
                                                random_state=42, stratify=y)
    print(f"    Train: {len(X_tr)}, Test: {len(X_te)}")

    # 6) Train LightGBM
    print("\n>>> Training LightGBM V3 (HDS + SA2)")
    params = {
        "objective": "binary", "metric": ["binary_logloss","auc"],
        "learning_rate": 0.05, "num_leaves": 127, "max_depth": -1,
        "min_data_in_leaf": 20, "feature_fraction": 0.85,
        "bagging_fraction": 0.85, "bagging_freq": 5,
        "lambda_l2": 0.1, "verbose": -1, "n_jobs": -1, "seed": 42,
    }
    dtr = lgb.Dataset(X_tr, label=y_tr, feature_name=band_names)
    dte = lgb.Dataset(X_te, label=y_te, feature_name=band_names, reference=dtr)
    model = lgb.train(params, dtr, num_boost_round=600,
                       valid_sets=[dtr, dte], valid_names=["train","val"],
                       callbacks=[lgb.early_stopping(40), lgb.log_evaluation(100)])

    y_prob = model.predict(X_te, num_iteration=model.best_iteration)
    y_pred = (y_prob > 0.5).astype(int)
    auc = roc_auc_score(y_te, y_prob)
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    print(f"\n>>> Test AUC: {auc:.4f}")
    print(classification_report(y_te, y_pred, zero_division=0))

    fi = sorted(zip(band_names, model.feature_importance(importance_type="gain")),
                key=lambda x: -x[1])
    total = sum(i for _,i in fi)
    print("\nTop 10 features:")
    for n, i in fi[:10]: print(f"  {n:>22}: {i/total*100:.2f}%")

    joblib.dump({"model": model, "band_names": band_names, "year": YEAR,
                 "best_iteration": model.best_iteration,
                 "training_regions": ["HDS", "SERRO_ALTO_2"]},
                MODEL_OUT, compress=3)
    print(f"\n<<< {MODEL_OUT}")

    REPORT_OUT.write_text(json.dumps({
        "year": YEAR, "training_regions": ["HDS", "SERRO_ALTO_2"],
        "n_features": len(band_names), "n_train": len(X_tr), "n_test": len(X_te),
        "test_auc": float(auc), "classification_report": report,
        "feature_importance": [{"name": n, "gain": float(i)} for n, i in fi],
        "best_iteration": int(model.best_iteration), "params": params,
    }, indent=2), encoding="utf-8")
    print(f"<<< {REPORT_OUT}")


if __name__ == "__main__":
    main()
