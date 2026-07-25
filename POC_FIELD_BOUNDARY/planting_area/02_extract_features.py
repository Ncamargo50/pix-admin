"""
Feature extraction multi-temporal para detector de Area de Plantio.

Por cada AOI (HDS, Santo Antonio) genera un stack GeoTIFF con:
  - 4 NDVIs trimestrales (Q1, Q2, Q3, Q4) del ano de referencia
  - 4 stats anuales NDVI: mean, std, range, amplitude
  - 2 DEM features: elevation, slope

Total 10 features por pixel a 20m de resolucion (downsampled de S2 10m).

Salida:
    output/features_HDS_YYYY.tif        (stack 10 bands)
    output/features_SANTO_ANTONIO_YYYY.tif

Uso:
    python 02_extract_features.py --year 2026 --aoi HDS
    python 02_extract_features.py --year 2026 --aoi SANTO_ANTONIO
"""
from __future__ import annotations

import argparse
import os
import urllib.request
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"

import numpy as np
import rasterio
import geopandas as gpd

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

AOI_BBOXES = {
    "HDS": [-63.37, -16.86, -63.27, -16.71],
    "SANTO_ANTONIO": [-50.665, -23.502, -50.652, -23.471],
}

QUARTERS = [
    ("Q1", "01-01", "03-31"),
    ("Q2", "04-01", "06-30"),
    ("Q3", "07-01", "09-30"),
    ("Q4", "10-01", "12-31"),
]


def initialize_ee():
    import ee
    try:
        ee.Number(1).getInfo()
    except Exception:
        ee.Initialize()


def fetch_quarterly_ndvi(bbox, year, quarter_start, quarter_end, scale=20):
    """NDVI mediano del trimestre."""
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(f"{year}-{quarter_start}", f"{year}-{quarter_end}")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50)))
    n = coll.size().getInfo()
    if n == 0:
        return None, n

    def mask_clean(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        return img.updateMask(clear).divide(10000)

    ndvi = coll.map(mask_clean).map(
        lambda i: i.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ).median().clip(aoi)
    return ndvi, n


def fetch_dem_slope(bbox, scale=20):
    """SRTM elevation + slope."""
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    dem = ee.Image("USGS/SRTMGL1_003").clip(aoi)
    slope = ee.Terrain.slope(dem).rename("slope")
    return dem.rename("elevation"), slope


def download_image(image, bbox, scale, out_tif):
    """Descarga una image GEE como GeoTIFF."""
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    url = image.getDownloadURL({
        "region": aoi, "scale": scale, "crs": "EPSG:4326",
        "format": "GEO_TIFF",
    })
    urllib.request.urlretrieve(url, out_tif)
    return out_tif


def stack_features(aoi_name: str, year: int, scale: int = 20):
    print(f">>> Feature extraction {aoi_name} year={year} scale={scale}m")
    bbox = AOI_BBOXES[aoi_name]
    initialize_ee()

    bands = []
    band_names = []

    # 1) NDVI trimestrales
    for label, start, end in QUARTERS:
        print(f"    NDVI {label}...")
        ndvi, n = fetch_quarterly_ndvi(bbox, year, start, end, scale)
        if ndvi is None:
            print(f"      WARN: sin escenas en {label}, usando NaN")
            tmp = OUT / f"_tmp_{aoi_name}_{label}.tif"
            tmp.write_bytes(b"")  # placeholder
            arr = None
        else:
            tmp = OUT / f"_tmp_{aoi_name}_{label}.tif"
            download_image(ndvi, bbox, scale, tmp)
            with rasterio.open(tmp) as src:
                arr = src.read(1)
                if not bands: ref_transform = src.transform; ref_crs = src.crs; ref_shape = src.shape
                # Resize si shape difiere
                if arr.shape != ref_shape:
                    from skimage.transform import resize
                    arr = resize(arr, ref_shape, preserve_range=True, anti_aliasing=False)
        bands.append(arr if arr is not None else np.full(ref_shape if bands else (100,100), np.nan))
        band_names.append(f"ndvi_{label}")

    # 2) Stats anuales NDVI
    print(f"    Stats anuales NDVI...")
    ndvi_stack = np.stack([b for b in bands if b is not None], axis=0)
    ndvi_mean = np.nanmean(ndvi_stack, axis=0)
    ndvi_std = np.nanstd(ndvi_stack, axis=0)
    ndvi_min = np.nanmin(ndvi_stack, axis=0)
    ndvi_max = np.nanmax(ndvi_stack, axis=0)
    ndvi_range = ndvi_max - ndvi_min
    bands.extend([ndvi_mean, ndvi_std, ndvi_range, ndvi_max - ndvi_min])
    band_names.extend(["ndvi_mean", "ndvi_std", "ndvi_range", "ndvi_amplitude"])

    # 3) DEM + slope
    print(f"    DEM + slope...")
    dem, slope = fetch_dem_slope(bbox, scale)
    tmp_dem = OUT / f"_tmp_{aoi_name}_dem.tif"
    download_image(dem, bbox, scale, tmp_dem)
    tmp_slope = OUT / f"_tmp_{aoi_name}_slope.tif"
    download_image(slope, bbox, scale, tmp_slope)
    with rasterio.open(tmp_dem) as src:
        dem_arr = src.read(1)
        if dem_arr.shape != ref_shape:
            from skimage.transform import resize
            dem_arr = resize(dem_arr, ref_shape, preserve_range=True, anti_aliasing=False)
    with rasterio.open(tmp_slope) as src:
        slope_arr = src.read(1)
        if slope_arr.shape != ref_shape:
            from skimage.transform import resize
            slope_arr = resize(slope_arr, ref_shape, preserve_range=True, anti_aliasing=False)
    bands.extend([dem_arr, slope_arr])
    band_names.extend(["elevation", "slope"])

    # 4) Stack final
    stack = np.stack(bands, axis=0).astype(np.float32)
    print(f"    Stack: {stack.shape} ({len(band_names)} bands)")

    out_tif = OUT / f"features_{aoi_name}_{year}.tif"
    profile = {
        "driver": "GTiff", "dtype": "float32", "count": len(bands),
        "height": stack.shape[1], "width": stack.shape[2],
        "transform": ref_transform, "crs": ref_crs, "nodata": np.nan,
        "compress": "deflate",
    }
    with rasterio.open(out_tif, "w", **profile) as dst:
        for i, (b, name) in enumerate(zip(bands, band_names), 1):
            dst.write(b, i)
            dst.set_band_description(i, name)
    print(f"<<< {out_tif} ({out_tif.stat().st_size//1024} KB)")

    # Limpiar tmp
    for f in OUT.glob(f"_tmp_{aoi_name}_*.tif"):
        f.unlink(missing_ok=True)

    return out_tif, band_names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--aoi", choices=list(AOI_BBOXES.keys()), required=True)
    ap.add_argument("--scale", type=int, default=20)
    args = ap.parse_args()
    stack_features(args.aoi, args.year, args.scale)


if __name__ == "__main__":
    main()
