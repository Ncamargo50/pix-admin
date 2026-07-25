"""
POC Field Boundary - Tool C: SLIC + Canny en Python (equivalente local del GEE).

Replica el flujo del 02_gee_snic_canny.js usando skimage para correrlo en
local sin Earth Engine. Usa la misma TIFF S2 RGB que descargo
03_run_delineate_anything.py.

Uso:
    python 05_python_slic_canny.py
    python 05_python_slic_canny.py --tif output/s2_rgb_santoantonio.tif

Pipeline:
  1. Lee S2 RGB GeoTIFF.
  2. SLIC super-pixels (n_segments=400, compactness=10).
  3. Canny edge detection sobre R, G, B + brillo.
  4. Consenso de edges (>=2 bandas).
  5. Vectoriza regiones interiores (no-edge) -> GeoJSON.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"

import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
from skimage.segmentation import slic
from skimage.feature import canny
from skimage.morphology import binary_dilation, disk

ROOT = Path(__file__).parent
OUT = ROOT / "output"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tif", default=str(OUT / "s2_rgb_santoantonio.tif"),
                    help="Sentinel-2 RGB GeoTIFF")
    ap.add_argument("--n-segments", type=int, default=400)
    ap.add_argument("--compactness", type=float, default=10.0)
    ap.add_argument("--canny-sigma", type=float, default=1.2)
    ap.add_argument("--min-area-ha", type=float, default=0.5)
    args = ap.parse_args()

    tif = Path(args.tif)
    print(f">>> Leyendo {tif}")
    with rasterio.open(tif) as src:
        rgb = src.read([1, 2, 3]).transpose(1, 2, 0)  # H,W,3 uint8
        transform = src.transform
        crs = src.crs
        h, w = src.height, src.width
    print(f"    {w}x{h} {rgb.dtype} CRS={crs}")

    rgb_f = rgb.astype(np.float32) / 255.0

    # --- SLIC super-pixels (analogo a SNIC en GEE) -------------------------
    print(f">>> SLIC n_segments={args.n_segments} compactness={args.compactness}")
    seg = slic(rgb_f, n_segments=args.n_segments, compactness=args.compactness,
               sigma=1, start_label=0, channel_axis=2)
    print(f"    {seg.max()+1} super-pixels generados")

    # Promedio por super-pixel para suavizar dentro de cada region
    smooth = np.zeros_like(rgb_f)
    for c in range(3):
        flat = rgb_f[:, :, c].ravel()
        means = np.bincount(seg.ravel(), weights=flat) / np.bincount(seg.ravel())
        smooth[:, :, c] = means[seg]

    # --- Canny por banda + consenso ---------------------------------------
    print(f">>> Canny edges (sigma={args.canny_sigma})")
    edges = []
    for c in range(3):
        e = canny(smooth[:, :, c], sigma=args.canny_sigma)
        edges.append(e.astype(np.uint8))
    bright = smooth.mean(axis=2)
    edges.append(canny(bright, sigma=args.canny_sigma).astype(np.uint8))

    edge_count = np.sum(edges, axis=0)
    edge_consensus = (edge_count >= 2).astype(np.uint8)
    # Pequena dilatacion para cerrar bordes interrumpidos
    edge_consensus = binary_dilation(edge_consensus, footprint=disk(1)).astype(np.uint8)
    print(f"    edge pixels: {int(edge_consensus.sum())} / {h*w}")

    # --- Mascara interior de campo: NOT edge AND verde -------------------
    # Verde aproximado: NDVI proxy desde RGB (G - R)/(G + R + eps)
    green_idx = (rgb_f[:, :, 1] - rgb_f[:, :, 0]) / (rgb_f[:, :, 1] + rgb_f[:, :, 0] + 1e-6)
    interior = ((edge_consensus == 0) & (green_idx > -0.05)).astype(np.uint8)
    print(f"    interior pixels: {int(interior.sum())} / {h*w}")

    # --- Vectorizar -------------------------------------------------------
    print(">>> Vectorizando")
    geoms = []
    for geom, val in shapes(interior, transform=transform):
        if val == 1:
            geoms.append(shape(geom))
    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs)
    print(f"    {len(gdf)} poligonos crudos")

    # Filtro por area en metros (UTM 22S)
    gdf_utm = gdf.to_crs(32722)
    gdf_utm["area_ha"] = gdf_utm.area / 10_000
    gdf_utm = gdf_utm[gdf_utm["area_ha"] >= args.min_area_ha].copy()
    gdf_filt = gdf_utm.to_crs(crs)

    out = OUT / "python_slic_canny_result.geojson"
    gdf_filt.to_file(out, driver="GeoJSON")
    print(f"<<< {out} ({len(gdf_filt)} poligonos, "
          f"{gdf_utm['area_ha'].sum():.1f} ha total)")


if __name__ == "__main__":
    main()
