"""
POC Field Boundary - Tool B: Delineate Anything (SOTA 2025) local.

Pipeline completo:
  1. Descarga Sentinel-2 RGB del AOI Santo Antonio (via Earth Engine API).
  2. Carga modelo Delineate Anything small (17.6 MB, YOLO instance segmentation).
  3. Corre inferencia, vectoriza poligonos, exporta GeoJSON.
  4. Imprime IoU contra el shapefile truth.

Pre-requisitos (instalar UNA SOLA VEZ):
    pip install ultralytics earthengine-api geemap rasterio pillow
    earthengine authenticate

Si ultralytics no esta instalado, el script imprime el comando exacto y termina.

Uso:
    python 03_run_delineate_anything.py
    python 03_run_delineate_anything.py --use-existing-tif output/s2_rgb.tif
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

TRUTH_SHP = Path("D:/PIXADVISOR_AGENT_WORKSPACE/_orphan_files/shp/Santo_Antonio.shp")
AOI_BBOX_WGS84 = (-50.660770, -23.477078, -50.652527, -23.451294)
PERIOD = ("2026-01-01", "2026-02-25")
MODEL_URL = "https://huggingface.co/torchgeo/delineate-anything-s/resolve/main/delineate_anything_s_rgb_yolo11n-b879d643.pt"
MODEL_URL_ALT = "https://huggingface.co/MykolaL/DelineateAnything/resolve/main/DelineateAnything-S.pt"
MODEL_FALLBACK = "yolo11n-seg.pt"  # ultralytics auto-download de respaldo


def fail_with_install_hint():
    print("ultralytics no esta instalado.")
    print("Instalalo con:")
    print("    pip install ultralytics earthengine-api geemap rasterio pillow")
    print()
    print("Mientras tanto, podes usar el GEE script (02_gee_snic_canny.js)")
    print("o FTW Explorer (https://fieldsofthe.world/ftw-inference-app)")
    sys.exit(1)


def download_s2_rgb(out_tif: Path) -> Path:
    """Descarga RGB compuesto de Sentinel-2 para el AOI via earthengine-api."""
    try:
        import ee
        import geemap
    except ImportError:
        print("Falta earthengine-api o geemap.")
        print("    pip install earthengine-api geemap")
        sys.exit(1)

    try:
        ee.Initialize(project=os.environ.get("EE_PROJECT", None))
    except Exception:
        print("Earth Engine no autenticado. Corre primero:")
        print("    earthengine authenticate")
        sys.exit(1)

    aoi = ee.Geometry.Rectangle(list(AOI_BBOX_WGS84))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(PERIOD[0], PERIOD[1])
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))

    def mask(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        return img.updateMask(clear).divide(10000)

    composite = coll.map(mask).median().clip(aoi)
    rgb = composite.select(["B4", "B3", "B2"]).multiply(2200).clamp(0, 255).toUint8()

    print(">>> Descargando S2 RGB composite (puede tomar ~30 s)")
    geemap.ee_export_image(rgb, filename=str(out_tif), scale=10, region=aoi, crs="EPSG:4326")
    return out_tif


def load_model():
    try:
        from ultralytics import YOLO
    except ImportError:
        fail_with_install_hint()

    print(">>> Cargando modelo Delineate Anything (small)")
    import urllib.request
    local = OUT / "delineate-anything-s.pt"
    if not local.exists() or local.stat().st_size < 1_000_000:
        for url in (MODEL_URL, MODEL_URL_ALT):
            try:
                print(f"    Bajando {url}")
                urllib.request.urlretrieve(url, local)
                if local.stat().st_size > 1_000_000:
                    print(f"    OK ({local.stat().st_size / 1024 / 1024:.1f} MB)")
                    break
            except Exception as exc:
                print(f"    Fall: {exc}")
                continue
    if local.exists() and local.stat().st_size > 1_000_000:
        try:
            return YOLO(str(local))
        except Exception as exc:
            print(f"    Modelo SOTA no carga ({exc}); fallback YOLO11n-seg")
    return YOLO(MODEL_FALLBACK)


def run_inference(model, tif_path: Path, out_geojson: Path) -> Path:
    import numpy as np
    import rasterio
    from rasterio.features import shapes
    from shapely.geometry import shape, mapping
    import geopandas as gpd
    from PIL import Image

    print(f">>> Leyendo {tif_path}")
    with rasterio.open(tif_path) as src:
        rgb = src.read([1, 2, 3]).transpose(1, 2, 0)
        transform = src.transform
        crs = src.crs
        h, w = src.height, src.width

    # Normalizar a uint8 si viene en float
    if rgb.dtype != np.uint8:
        p2, p98 = np.percentile(rgb, (2, 98))
        rgb = np.clip((rgb - p2) / max(p98 - p2, 1e-6) * 255, 0, 255).astype(np.uint8)

    img_path = OUT / "s2_rgb_uint8.png"
    Image.fromarray(rgb).save(img_path)
    print(f"    PNG: {img_path}  ({w}x{h})")

    print(">>> Inferencia (instance segmentation)")
    # imgsz multiplo de 32. AOI Santo Antonio = 111x322; padding a 640 funciona mejor.
    imgsz = max(640, ((max(h, w) + 31) // 32) * 32)
    results = model.predict(source=str(img_path), imgsz=imgsz,
                            conf=0.05, iou=0.4, retina_masks=True,
                            agnostic_nms=True, verbose=False)

    geoms = []
    for r in results:
        if r.masks is None:
            continue
        masks = r.masks.data.cpu().numpy()  # (N, H, W) bool
        for m in masks:
            mask = (m > 0.5).astype("uint8")
            for geom, val in shapes(mask, transform=transform):
                if val == 1:
                    g = shape(geom)
                    if g.area > 1e-7:  # ~10 m2 en grados
                        geoms.append(g)

    if not geoms:
        print("    Sin mascaras detectadas (probable falta de finetune o conf bajo).")
        return out_geojson

    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs or "EPSG:4326")
    gdf["area_ha"] = gdf.to_crs(32722).area / 10_000
    gdf = gdf[gdf["area_ha"] >= 0.3].copy()
    gdf.to_file(out_geojson, driver="GeoJSON")
    print(f"<<< {out_geojson} ({len(gdf)} poligonos, {gdf['area_ha'].sum():.1f} ha total)")
    return out_geojson


def quick_iou(candidate_geojson: Path):
    if not candidate_geojson.exists() or candidate_geojson.stat().st_size < 100:
        print("    Sin candidato para comparar.")
        return
    import geopandas as gpd
    truth = gpd.read_file(TRUTH_SHP)
    if truth.crs is None:
        truth = truth.set_crs("EPSG:32722")
    truth = truth.to_crs(32722)
    cand = gpd.read_file(candidate_geojson).to_crs(32722)

    truth_u = truth.union_all()
    cand_u = cand.union_all()
    inter = truth_u.intersection(cand_u).area
    union = truth_u.union(cand_u).area
    iou = inter / union if union > 0 else 0
    print(f"\n=== IoU Delineate Anything vs Truth ===")
    print(f"  Truth:    {truth_u.area / 10_000:.2f} ha")
    print(f"  Detected: {cand_u.area / 10_000:.2f} ha")
    print(f"  IoU:      {iou:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--use-existing-tif", type=str, default=None,
                    help="Saltar descarga GEE y usar este TIFF.")
    args = ap.parse_args()

    tif = Path(args.use_existing_tif) if args.use_existing_tif else (OUT / "s2_rgb.tif")
    if not tif.exists():
        download_s2_rgb(tif)

    model = load_model()
    out_geojson = OUT / "delineate_anything_result.geojson"
    run_inference(model, tif, out_geojson)
    quick_iou(out_geojson)


if __name__ == "__main__":
    main()
