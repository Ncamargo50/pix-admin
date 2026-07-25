"""
POC Field Boundary - Step 4: Comparador agnostico de candidatos vs truth.

Compara cualquier GeoJSON / Shapefile / KML candidato contra el shapefile real
de Santo Antonio. Calcula IoU, area diff, sub/sobre-deteccion y produce un
reporte CSV con metricas + un PNG con overlay.

Uso:
    python 04_compare_iou.py output/delineate_anything_result.geojson
    python 04_compare_iou.py output/ftw_export.geojson
    python 04_compare_iou.py output/gee_snic_canny.geojson --label "GEE SNIC+Canny"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).parent
TRUTH_SHP = Path("D:/PIXADVISOR_AGENT_WORKSPACE/_orphan_files/shp/Santo_Antonio.shp")
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
TARGET_CRS = "EPSG:32722"  # UTM 22S - metros

REPORT_CSV = OUT / "comparison_report.csv"


def load_truth():
    g = gpd.read_file(TRUTH_SHP)
    if g.crs is None:
        g = g.set_crs(TARGET_CRS)
    return g.to_crs(TARGET_CRS)


def metrics(truth_gdf, cand_gdf, label):
    truth_u = truth_gdf.union_all()
    cand_u = cand_gdf.union_all()

    inter = truth_u.intersection(cand_u).area
    union = truth_u.union(cand_u).area
    iou = inter / union if union > 0 else 0.0

    truth_ha = truth_u.area / 10_000
    cand_ha = cand_u.area / 10_000
    inter_ha = inter / 10_000
    over_ha = (cand_u.difference(truth_u)).area / 10_000  # detect fuera de truth
    miss_ha = (truth_u.difference(cand_u)).area / 10_000  # truth no detectado

    precision = inter / cand_u.area if cand_u.area > 0 else 0.0
    recall = inter / truth_u.area if truth_u.area > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "candidate": label,
        "truth_ha": round(truth_ha, 2),
        "candidate_ha": round(cand_ha, 2),
        "intersect_ha": round(inter_ha, 2),
        "over_detection_ha": round(over_ha, 2),
        "missed_ha": round(miss_ha, 2),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "IoU": round(iou, 3),
        "n_truth_features": len(truth_gdf),
        "n_candidate_features": len(cand_gdf),
    }


def plot_overlay(truth_gdf, cand_gdf, label, out_png):
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(9, 9))
    truth_gdf.plot(ax=ax, facecolor="none", edgecolor="black", linewidth=2.0)
    cand_gdf.plot(ax=ax, facecolor="cyan", edgecolor="blue",
                  alpha=0.35, linewidth=0.8)
    ax.set_title(f"Truth (negro) vs {label} (cyan)")
    ax.set_xlabel("UTM E (m)")
    ax.set_ylabel("UTM N (m)")
    ax.legend(handles=[
        mpatches.Patch(facecolor="none", edgecolor="black", label="Truth"),
        mpatches.Patch(facecolor="cyan", edgecolor="blue", alpha=0.35, label=label),
    ])
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(out_png, dpi=120)
    plt.close()


def append_report(row):
    if REPORT_CSV.exists():
        df = pd.read_csv(REPORT_CSV)
        df = pd.concat([df[df["candidate"] != row["candidate"]],
                        pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df = df.sort_values("IoU", ascending=False).reset_index(drop=True)
    df.to_csv(REPORT_CSV, index=False)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=str, help="Path a GeoJSON / shp / kml candidato")
    ap.add_argument("--label", type=str, default=None, help="Etiqueta del candidato")
    ap.add_argument("--clip-buffer-m", type=float, default=None,
                    help="Recorta candidato a bbox(truth)+buffer (m) para evaluacion justa")
    args = ap.parse_args()

    cand_path = Path(args.candidate)
    if not cand_path.exists():
        print(f"No existe: {cand_path}")
        sys.exit(1)

    label = args.label or cand_path.stem

    print(f">>> Cargando truth")
    truth = load_truth()
    print(f"    Truth: {len(truth)} features, {truth.area.sum()/10_000:.2f} ha")

    print(f">>> Cargando candidato '{label}'")
    cand = gpd.read_file(cand_path)
    if cand.crs is None:
        print("    Candidato sin CRS, asumiendo EPSG:4326")
        cand = cand.set_crs("EPSG:4326")
    cand = cand.to_crs(TARGET_CRS)
    print(f"    Candidato: {len(cand)} features, {cand.area.sum()/10_000:.2f} ha")

    if args.clip_buffer_m is not None:
        from shapely.geometry import box
        bx = truth.total_bounds  # minx, miny, maxx, maxy en metros
        roi = box(bx[0]-args.clip_buffer_m, bx[1]-args.clip_buffer_m,
                  bx[2]+args.clip_buffer_m, bx[3]+args.clip_buffer_m)
        cand = gpd.GeoDataFrame(geometry=[g.intersection(roi) for g in cand.geometry], crs=TARGET_CRS)
        cand = cand[~cand.is_empty].copy()
        cand = cand[cand.area > 1].copy()  # >1 m2
        print(f"    Tras clip a truth_bbox+{args.clip_buffer_m:.0f}m: "
              f"{len(cand)} features, {cand.area.sum()/10_000:.2f} ha")

    row = metrics(truth, cand, label)
    print("\n=== Metricas ===")
    for k, v in row.items():
        print(f"  {k:>22}: {v}")

    out_png = OUT / f"overlay_{label.replace(' ', '_')}.png"
    plot_overlay(truth, cand, label, out_png)
    print(f"\n<<< {out_png}")

    df = append_report(row)
    print(f"<<< {REPORT_CSV}")
    print("\n=== Ranking acumulado ===")
    print(df[["candidate", "IoU", "f1", "precision", "recall",
              "candidate_ha", "missed_ha", "over_detection_ha"]].to_string(index=False))


if __name__ == "__main__":
    main()
