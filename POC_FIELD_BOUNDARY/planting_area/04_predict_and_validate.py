"""
Predice mascara de Area de Plantio sobre cualquier AOI y valida contra truth.

Pipeline:
  1. Carga modelo entrenado.
  2. Carga feature stack del AOI.
  3. Predice probabilidad por pixel.
  4. Aplica umbral + morfologia.
  5. Vectoriza a poligonos.
  6. Calcula IoU vs truth.
  7. Genera overlay PNG con S2 RGB de fondo.

Uso:
    python 04_predict_and_validate.py --aoi HDS
    python 04_predict_and_validate.py --aoi SANTO_ANTONIO --threshold 0.5
"""
from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"
warnings.filterwarnings("ignore")

import numpy as np
import rasterio
from rasterio.features import shapes as rio_shapes
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from shapely.geometry import shape as shp_shape, mapping
from shapely import make_valid
from shapely.ops import unary_union
from scipy.ndimage import binary_closing, binary_opening
import joblib

ROOT = Path(__file__).parent
OUT = ROOT / "output"

YEAR = 2025
MODEL_PATH = OUT / f"rf_planting_area_{YEAR}.joblib"
TRUTH_GEO = OUT / "truth_master.geojson"


def utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    south = lat_mid < 0
    return f"EPSG:{32700 + zone if south else 32600 + zone}"


def predict_mask(aoi_name, threshold=0.5, min_area_ha=1.0,
                 closing_iters=2, opening_iters=1):
    print(f">>> Cargando modelo {MODEL_PATH}")
    bundle = joblib.load(MODEL_PATH)
    clf, band_names = bundle["model"], bundle["band_names"]

    feat_tif = OUT / f"features_{aoi_name}_{YEAR}.tif"
    print(f">>> Cargando features {feat_tif}")
    with rasterio.open(feat_tif) as src:
        stack = src.read()
        transform = src.transform
        crs = src.crs
        shape = src.shape

    H, W = shape
    valid = ~np.isnan(stack).any(axis=0)
    print(f"    Pixels validos: {valid.sum():,} / {valid.size:,}")

    # Reshape para predict
    flat = stack.reshape(stack.shape[0], -1).T  # (H*W, n_features)
    valid_flat = valid.flatten()
    proba = np.zeros(H * W, dtype=np.float32)
    proba_valid = clf.predict_proba(flat[valid_flat])[:, 1]
    proba[valid_flat] = proba_valid
    proba = proba.reshape(H, W)

    print(f">>> Postprocesando con threshold={threshold}")
    raw_mask = (proba > threshold) & valid
    print(f"    Mask raw: {raw_mask.sum():,} pixels")

    # Morfologia: closing para tapar gaps internos, opening para limpiar pixeles aislados
    if closing_iters > 0:
        raw_mask = binary_closing(raw_mask, iterations=closing_iters)
    if opening_iters > 0:
        raw_mask = binary_opening(raw_mask, iterations=opening_iters)
    print(f"    Mask post-morph: {raw_mask.sum():,} pixels")

    # Vectorizar
    print(">>> Vectorizando")
    geoms = []
    for geom_dict, val in rio_shapes(raw_mask.astype(np.uint8), transform=transform):
        if val == 1:
            g = shp_shape(geom_dict)
            if g.is_valid and g.area > 0:
                geoms.append(g)

    if not geoms:
        print("    Sin poligonos detectados.")
        return None, proba, transform, crs

    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs)
    gdf["geometry"] = gdf.geometry.apply(make_valid).buffer(0)

    # Calcular area en UTM regional
    utm = utm_for_bounds(gdf.total_bounds)
    gdf_utm = gdf.to_crs(utm)
    gdf["area_ha"] = gdf_utm.area / 10_000

    # Filtrar por area minima
    before = len(gdf)
    gdf = gdf[gdf["area_ha"] >= min_area_ha].copy().reset_index(drop=True)
    print(f"    Filtro >= {min_area_ha} ha: {before} -> {len(gdf)}")

    out_geo = OUT / f"predicted_planting_{aoi_name}_{YEAR}.geojson"
    gdf.to_file(out_geo, driver="GeoJSON")
    print(f"<<< {out_geo} ({len(gdf)} poligonos, {gdf['area_ha'].sum():.1f} ha)")

    return gdf, proba, transform, crs


def evaluate_iou(predicted_gdf, aoi_name):
    print(f">>> Evaluando IoU contra truth {aoi_name}")
    truth = gpd.read_file(TRUTH_GEO)
    truth = truth[truth["source"] == aoi_name].copy()
    print(f"    Truth: {len(truth)} features, {truth['area_ha'].sum():.1f} ha")

    if predicted_gdf is None or predicted_gdf.empty:
        return {"iou": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    # UTM para metricas precisas
    utm = utm_for_bounds(truth.total_bounds)
    truth_u = truth.to_crs(utm).geometry.union_all()
    pred_u = predicted_gdf.to_crs(utm).geometry.union_all()

    inter = truth_u.intersection(pred_u).area
    union = truth_u.union(pred_u).area
    iou = inter / union if union > 0 else 0
    precision = inter / pred_u.area if pred_u.area > 0 else 0
    recall = inter / truth_u.area if truth_u.area > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    truth_ha = truth_u.area / 10_000
    pred_ha = pred_u.area / 10_000
    inter_ha = inter / 10_000
    over_ha = (pred_u.difference(truth_u)).area / 10_000
    miss_ha = (truth_u.difference(pred_u)).area / 10_000

    metrics = {
        "iou": round(iou, 3), "precision": round(precision, 3),
        "recall": round(recall, 3), "f1": round(f1, 3),
        "truth_ha": round(truth_ha, 2), "predicted_ha": round(pred_ha, 2),
        "intersect_ha": round(inter_ha, 2),
        "over_detection_ha": round(over_ha, 2), "missed_ha": round(miss_ha, 2),
    }
    print(f"    IoU={iou:.3f}  F1={f1:.3f}  P={precision:.3f}  R={recall:.3f}")
    print(f"    Truth={truth_ha:.1f}ha  Pred={pred_ha:.1f}ha  "
          f"Inter={inter_ha:.1f}ha  Over={over_ha:.1f}ha  Miss={miss_ha:.1f}ha")
    return metrics


def plot_overlay(predicted_gdf, proba, transform, crs, aoi_name, metrics, out_png):
    truth = gpd.read_file(TRUTH_GEO)
    truth = truth[truth["source"] == aoi_name].to_crs("EPSG:4326")

    bounds = rasterio.transform.array_bounds(proba.shape[0], proba.shape[1], transform)
    extent = [bounds[0], bounds[2], bounds[1], bounds[3]]

    fig, axes = plt.subplots(1, 2, figsize=(18, 9))

    # Heatmap proba
    axes[0].imshow(proba, extent=extent, cmap="RdYlGn", vmin=0, vmax=1, origin="upper")
    truth.plot(ax=axes[0], facecolor="none", edgecolor="black", linewidth=1.5)
    axes[0].set_title(f"{aoi_name}: probabilidad area-plantio (truth en negro)")
    axes[0].set_xlabel("Lon"); axes[0].set_ylabel("Lat")

    # Predicciones vs truth
    if predicted_gdf is not None and not predicted_gdf.empty:
        predicted_gdf.to_crs("EPSG:4326").plot(
            ax=axes[1], facecolor="cyan", edgecolor="blue", alpha=0.40, linewidth=0.6)
    truth.plot(ax=axes[1], facecolor="none", edgecolor="black", linewidth=1.5)
    title = f"{aoi_name}: Predicted (cyan) vs Truth (negro)"
    if metrics:
        title += f"\nIoU={metrics['iou']} F1={metrics['f1']} P={metrics['precision']} R={metrics['recall']}"
    axes[1].set_title(title)
    axes[1].set_xlabel("Lon")
    axes[1].set_aspect("equal")

    plt.tight_layout()
    plt.savefig(out_png, dpi=110)
    plt.close()
    print(f"<<< {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aoi", choices=["HDS", "SANTO_ANTONIO"], required=True)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--min-area-ha", type=float, default=1.0)
    args = ap.parse_args()

    gdf, proba, transform, crs = predict_mask(
        args.aoi, threshold=args.threshold, min_area_ha=args.min_area_ha)
    metrics = evaluate_iou(gdf, args.aoi)

    out_png = OUT / f"overlay_{args.aoi}_{YEAR}.png"
    plot_overlay(gdf, proba, transform, crs, args.aoi, metrics, out_png)

    # Guardar metrics
    import json as _j
    metrics_json = OUT / f"metrics_{args.aoi}_{YEAR}.json"
    metrics_json.write_text(_j.dumps(metrics, indent=2), encoding="utf-8")
    print(f"<<< {metrics_json}")


if __name__ == "__main__":
    main()
