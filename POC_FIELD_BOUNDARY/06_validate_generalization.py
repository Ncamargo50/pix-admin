"""
POC Field Boundary - Validation 2: generalizacion sobre Hacienda Cerro Alto, Bolivia.

Pipeline:
  1. Lee proyecto_serro_alto_prueba.json -> extrae LOTE-01 (681 ha) como nuevo truth.
  2. Descarga Sentinel-2 RGB del bbox via GEE.
  3. Corre Delineate Anything S (16.8 MB) y standard (125 MB).
  4. Compara cada modelo vs truth con clip y reporta IoU.

Uso:
    python 06_validate_generalization.py
    python 06_validate_generalization.py --lote LOTE-02
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape, Polygon
from PIL import Image
import urllib.request

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

PROJECT_JSON = Path("D:/PIXADVISOR_AGENT_WORKSPACE/pix-muestreo-apk/proyecto_serro_alto_prueba.json")
PERIOD = ("2026-01-01", "2026-02-25")
MODEL_SMALL = OUT / "delineate-anything-s.pt"
MODEL_LARGE = OUT / "delineate-anything-large.pt"
MODEL_LARGE_URL = "https://huggingface.co/MykolaL/DelineateAnything/resolve/main/DelineateAnything.pt"


def extract_truth(lote_name: str) -> tuple[Path, list[float], float]:
    proj = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
    target = None
    for lote in proj["lotes"]:
        if lote["name"] == lote_name:
            target = lote
            break
    if not target:
        raise SystemExit(f"Lote {lote_name} no encontrado")

    fc = target["zonas"]
    feats = []
    for f in fc["features"]:
        feats.append({
            "type": "Feature",
            "properties": {"zona": f["properties"].get("zona", "?")},
            "geometry": f["geometry"],
        })
    out_truth = OUT / f"truth_{lote_name.replace(' ', '_')}.geojson"
    out_truth.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": feats,
    }), encoding="utf-8")
    print(f"<<< {out_truth}")

    g = gpd.read_file(out_truth)
    g_utm = g.to_crs(32720)  # UTM 20S, Bolivia
    bx = g.total_bounds.tolist()
    print(f"    Truth: {len(g)} features, area_ha={g_utm.area.sum()/10000:.2f}")
    print(f"    BBOX WGS84: {bx}")

    buf = 0.002  # ~220 m
    bbox_pad = [bx[0]-buf, bx[1]-buf, bx[2]+buf, bx[3]+buf]
    return out_truth, bbox_pad, g_utm.area.sum() / 10000


def download_s2(bbox_pad: list[float], out_tif: Path):
    if out_tif.exists():
        print(f"    {out_tif} ya existe")
        return
    import ee
    ee.Initialize()
    aoi = ee.Geometry.Rectangle(bbox_pad)
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(PERIOD[0], PERIOD[1])
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))
    n = coll.size().getInfo()
    print(f">>> S2 scenes: {n}")

    def mask(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        return img.updateMask(clear).divide(10000)

    comp = coll.map(mask).median().clip(aoi)
    rgb = comp.select(["B4", "B3", "B2"]).multiply(2200).clamp(0, 255).toUint8()
    url = rgb.getDownloadURL({"region": aoi, "scale": 10, "crs": "EPSG:4326",
                              "format": "GEO_TIFF"})
    print(f">>> Bajando S2 RGB...")
    urllib.request.urlretrieve(url, out_tif)
    print(f"<<< {out_tif} ({out_tif.stat().st_size/1024:.0f} KB)")


def ensure_large_model():
    if not MODEL_LARGE.exists() or MODEL_LARGE.stat().st_size < 50_000_000:
        print(f">>> Bajando modelo large {MODEL_LARGE_URL}")
        urllib.request.urlretrieve(MODEL_LARGE_URL, MODEL_LARGE)
        print(f"<<< {MODEL_LARGE} ({MODEL_LARGE.stat().st_size/1024/1024:.1f} MB)")


def run_inference(model_path: Path, tif: Path, label: str) -> Path:
    from ultralytics import YOLO

    print(f">>> Cargando {model_path.name}")
    model = YOLO(str(model_path))

    with rasterio.open(tif) as src:
        rgb = src.read([1, 2, 3]).transpose(1, 2, 0)
        transform = src.transform
        crs = src.crs
        h, w = src.height, src.width

    if rgb.dtype != np.uint8:
        p2, p98 = np.percentile(rgb, (2, 98))
        rgb = np.clip((rgb - p2) / max(p98 - p2, 1e-6) * 255, 0, 255).astype(np.uint8)

    img_path = OUT / f"_serro_alto_rgb.png"
    Image.fromarray(rgb).save(img_path)

    imgsz = max(640, ((max(h, w) + 31) // 32) * 32)
    print(f">>> Inferencia imgsz={imgsz}")
    results = model.predict(source=str(img_path), imgsz=imgsz,
                            conf=0.05, iou=0.4, retina_masks=True,
                            agnostic_nms=True, verbose=False)
    geoms = []
    for r in results:
        if r.masks is None: continue
        masks = r.masks.data.cpu().numpy()
        for m in masks:
            mask = (m > 0.5).astype("uint8")
            for geom, val in shapes(mask, transform=transform):
                if val == 1:
                    g = shape(geom)
                    if g.area > 1e-7:
                        geoms.append(g)

    if not geoms:
        print("    Sin mascaras")
        return None
    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs or "EPSG:4326")
    gdf["area_ha"] = gdf.to_crs(32720).area / 10_000
    gdf = gdf[gdf["area_ha"] >= 0.5].copy()
    out = OUT / f"serro_alto_{label}.geojson"
    gdf.to_file(out, driver="GeoJSON")
    print(f"<<< {out} ({len(gdf)} poligonos, {gdf['area_ha'].sum():.1f} ha)")
    return out


def evaluate(truth_path: Path, cand_path: Path, label: str, truth_ha: float, clip_buf_m=50):
    from shapely import make_valid
    truth = gpd.read_file(truth_path).to_crs(32720)
    cand = gpd.read_file(cand_path).to_crs(32720)

    # Sanitizar geometrias (poligonos derivados de raster pueden ser invalidos)
    truth["geometry"] = truth.geometry.apply(make_valid).buffer(0)
    cand["geometry"] = cand.geometry.apply(make_valid).buffer(0)

    truth_u = truth.union_all()
    bx = truth.total_bounds
    from shapely.geometry import box
    roi = box(bx[0]-clip_buf_m, bx[1]-clip_buf_m, bx[2]+clip_buf_m, bx[3]+clip_buf_m)
    cand_clipped = gpd.GeoDataFrame(
        geometry=[make_valid(g.intersection(roi)).buffer(0) for g in cand.geometry], crs=32720)
    cand_clipped = cand_clipped[~cand_clipped.is_empty].copy()
    cand_u = cand_clipped.union_all()

    inter = truth_u.intersection(cand_u).area
    union = truth_u.union(cand_u).area
    iou = inter / union if union > 0 else 0
    prec = inter / cand_u.area if cand_u.area > 0 else 0
    rec = inter / truth_u.area if truth_u.area > 0 else 0
    f1 = 2*prec*rec/(prec+rec) if (prec+rec) > 0 else 0
    over = (cand_u.difference(truth_u)).area / 10000
    miss = (truth_u.difference(cand_u)).area / 10000

    print(f"\n=== {label} (clip+{clip_buf_m}m) ===")
    print(f"  Truth: {truth_ha:.2f} ha")
    print(f"  Cand:  {cand_u.area/10000:.2f} ha ({len(cand_clipped)} polys)")
    print(f"  IoU:   {iou:.3f}  F1: {f1:.3f}")
    print(f"  Prec:  {prec:.3f}  Recall: {rec:.3f}")
    print(f"  Missed:{miss:.2f} ha   Over:{over:.2f} ha")

    return {
        "candidate": label, "truth_ha": round(truth_ha, 2),
        "candidate_ha": round(cand_u.area/10000, 2),
        "intersect_ha": round(inter/10000, 2),
        "missed_ha": round(miss, 2), "over_detection_ha": round(over, 2),
        "precision": round(prec, 3), "recall": round(rec, 3),
        "f1": round(f1, 3), "IoU": round(iou, 3),
        "n_candidate_features": len(cand_clipped),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lote", default="LOTE-01")
    args = ap.parse_args()

    print(f">>> Lote target: {args.lote}")
    truth_path, bbox_pad, truth_ha = extract_truth(args.lote)

    tif = OUT / f"s2_rgb_serro_alto_{args.lote}.tif"
    download_s2(bbox_pad, tif)

    ensure_large_model()

    out_small = run_inference(MODEL_SMALL, tif, f"{args.lote}_small")
    out_large = run_inference(MODEL_LARGE, tif, f"{args.lote}_large")

    results = []
    if out_small:
        results.append(evaluate(truth_path, out_small, f"DA-S_{args.lote}", truth_ha))
    if out_large:
        results.append(evaluate(truth_path, out_large, f"DA-L_{args.lote}", truth_ha))

    # Append al CSV consolidado
    import pandas as pd
    csv = OUT / "comparison_report.csv"
    new = pd.DataFrame(results)
    if csv.exists():
        old = pd.read_csv(csv)
        df = pd.concat([old[~old["candidate"].isin(new["candidate"])], new], ignore_index=True)
    else:
        df = new
    df = df.sort_values("IoU", ascending=False).reset_index(drop=True)
    df.to_csv(csv, index=False)
    print(f"\n<<< {csv}")
    print(df[["candidate","IoU","f1","precision","recall","missed_ha","over_detection_ha"]].to_string(index=False))


if __name__ == "__main__":
    main()
