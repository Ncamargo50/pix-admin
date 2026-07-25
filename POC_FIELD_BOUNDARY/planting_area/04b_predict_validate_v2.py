"""
Inferencia + IoU para modelo V2 (LightGBM, 28 features).

Uso:
    python 04b_predict_validate_v2.py --aoi HDS --threshold 0.5
    python 04b_predict_validate_v2.py --aoi SANTO_ANTONIO --threshold 0.5
"""
from __future__ import annotations

import argparse
import os
import json
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
from shapely.geometry import shape as shp_shape
from shapely import make_valid
from scipy.ndimage import binary_closing, binary_opening
import joblib

ROOT = Path(__file__).parent
OUT = ROOT / "output"

YEAR = 2025
MODEL_PATH = OUT / f"lgb_planting_area_v2_{YEAR}.joblib"
TRUTH_GEO = OUT / "truth_master.geojson"


def utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    south = lat_mid < 0
    return f"EPSG:{32700 + zone if south else 32600 + zone}"


def predict(aoi_name, threshold=0.5, min_area_ha=1.0,
            closing=2, opening=1):
    bundle = joblib.load(MODEL_PATH)
    model, band_names = bundle["model"], bundle["band_names"]
    best_iter = bundle.get("best_iteration", model.best_iteration)

    feat_tif = OUT / f"features_v2_{aoi_name}_{YEAR}.tif"
    print(f">>> {aoi_name} thr={threshold}")
    print(f"    Stack: {feat_tif}")
    with rasterio.open(feat_tif) as src:
        stack = src.read()
        transform = src.transform
        crs = src.crs
        H, W = src.shape

    valid = ~np.isnan(stack).any(axis=0)
    flat = stack.reshape(stack.shape[0], -1).T
    valid_flat = valid.flatten()
    proba = np.zeros(H * W, dtype=np.float32)
    proba[valid_flat] = model.predict(flat[valid_flat], num_iteration=best_iter)
    proba = proba.reshape(H, W)

    raw = (proba > threshold) & valid
    if closing: raw = binary_closing(raw, iterations=closing)
    if opening: raw = binary_opening(raw, iterations=opening)
    print(f"    Mask: {raw.sum():,} pixels post-morph")

    geoms = []
    for geom_dict, val in rio_shapes(raw.astype(np.uint8), transform=transform):
        if val == 1:
            g = shp_shape(geom_dict)
            if g.is_valid and g.area > 0:
                geoms.append(g)
    if not geoms:
        return None, proba, transform, crs

    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs)
    gdf["geometry"] = gdf.geometry.apply(make_valid).buffer(0)
    utm = utm_for_bounds(gdf.total_bounds)
    gdf["area_ha"] = gdf.to_crs(utm).area / 10_000
    gdf = gdf[gdf["area_ha"] >= min_area_ha].copy().reset_index(drop=True)
    out_geo = OUT / f"predicted_v2_{aoi_name}_{YEAR}.geojson"
    gdf.to_file(out_geo, driver="GeoJSON")
    print(f"<<< {out_geo} ({len(gdf)} polys, {gdf['area_ha'].sum():.1f} ha)")
    return gdf, proba, transform, crs


def evaluate(predicted, aoi_name):
    truth = gpd.read_file(TRUTH_GEO)
    truth = truth[truth["source"] == aoi_name].copy()
    if predicted is None or predicted.empty:
        return {"iou": 0, "f1": 0, "precision": 0, "recall": 0}
    utm = utm_for_bounds(truth.total_bounds)
    t_u = truth.to_crs(utm).geometry.union_all()
    p_u = predicted.to_crs(utm).geometry.union_all()
    inter = t_u.intersection(p_u).area
    union = t_u.union(p_u).area
    iou = inter / union if union > 0 else 0
    pre = inter / p_u.area if p_u.area > 0 else 0
    rec = inter / t_u.area if t_u.area > 0 else 0
    f1 = 2*pre*rec / (pre+rec) if (pre+rec) > 0 else 0
    print(f"    IoU={iou:.3f}  F1={f1:.3f}  P={pre:.3f}  R={rec:.3f}  "
          f"truth={t_u.area/1e4:.1f}ha pred={p_u.area/1e4:.1f}ha "
          f"over={(p_u.difference(t_u)).area/1e4:.1f}ha miss={(t_u.difference(p_u)).area/1e4:.1f}ha")
    return {
        "iou": round(iou, 3), "f1": round(f1, 3),
        "precision": round(pre, 3), "recall": round(rec, 3),
        "truth_ha": round(t_u.area/1e4, 2), "pred_ha": round(p_u.area/1e4, 2),
        "over_ha": round((p_u.difference(t_u)).area/1e4, 2),
        "miss_ha": round((t_u.difference(p_u)).area/1e4, 2),
    }


def plot_overlay(predicted, proba, transform, crs, aoi_name, metrics, out_png):
    truth = gpd.read_file(TRUTH_GEO)
    truth = truth[truth["source"] == aoi_name].to_crs("EPSG:4326")
    bounds = rasterio.transform.array_bounds(proba.shape[0], proba.shape[1], transform)
    extent = [bounds[0], bounds[2], bounds[1], bounds[3]]
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    axes[0].imshow(proba, extent=extent, cmap="RdYlGn", vmin=0, vmax=1, origin="upper")
    truth.plot(ax=axes[0], facecolor="none", edgecolor="black", linewidth=1.4)
    axes[0].set_title(f"{aoi_name} V2: probabilidad area-plantio (truth en negro)")
    if predicted is not None and not predicted.empty:
        predicted.to_crs("EPSG:4326").plot(ax=axes[1], facecolor="cyan", edgecolor="blue",
                                            alpha=0.45, linewidth=0.6)
    truth.plot(ax=axes[1], facecolor="none", edgecolor="black", linewidth=1.4)
    title = f"{aoi_name} V2: Pred (cyan) vs Truth (negro)"
    if metrics: title += f"\nIoU={metrics['iou']} F1={metrics['f1']} P={metrics['precision']} R={metrics['recall']}"
    axes[1].set_title(title)
    axes[1].set_aspect("equal")
    plt.tight_layout()
    plt.savefig(out_png, dpi=110)
    plt.close()
    print(f"<<< {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aoi", choices=["HDS","SANTO_ANTONIO"], required=True)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--min-area-ha", type=float, default=1.0)
    args = ap.parse_args()
    gdf, proba, tr, crs = predict(args.aoi, args.threshold, args.min_area_ha)
    metrics = evaluate(gdf, args.aoi)
    out_png = OUT / f"overlay_v2_{args.aoi}_{YEAR}_thr{int(args.threshold*100)}.png"
    plot_overlay(gdf, proba, tr, crs, args.aoi, metrics, out_png)
    metrics["aoi"] = args.aoi; metrics["threshold"] = args.threshold; metrics["model"] = "v2"
    (OUT / f"metrics_v2_{args.aoi}_{int(args.threshold*100)}.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
