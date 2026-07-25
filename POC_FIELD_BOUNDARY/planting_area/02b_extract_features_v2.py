"""
Feature extraction V2 — expandido para mayor IoU.

Mejoras vs V1:
  - 4 indices espectrales por trimestre (no solo NDVI):
      NDVI = (B8-B4)/(B8+B4)         vegetacion
      NDWI = (B3-B8)/(B3+B8)         agua
      NDBI = (B11-B8)/(B11+B8)       urbano / suelo desnudo
      BSI  = ((B11+B4)-(B8+B2))/((B11+B4)+(B8+B2))  bare soil
  - B11 mediano (SWIR1) por trimestre — discrimina agua/bare/urbano
  - Stats anuales NDVI: mean, std, range, amplitude
  - Contexto espacial: NDVI local mean (3x3), local std (3x3)
  - Topografia: elevation, slope

Total: 4 trim x 5 bandas + 4 stats + 2 spatial + 2 dem = 28 features

Uso:
    python 02b_extract_features_v2.py --aoi HDS --year 2025
"""
from __future__ import annotations

import argparse
import os
import urllib.request
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"

import numpy as np
import rasterio

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


def fetch_quarterly_indices(bbox, year, quarter_start, quarter_end, scale=20):
    """Devuelve image GEE con bandas: NDVI, NDWI, NDBI, BSI, B11."""
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

    def with_indices(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        ndwi = img.normalizedDifference(["B3", "B8"]).rename("NDWI")
        ndbi = img.normalizedDifference(["B11", "B8"]).rename("NDBI")
        # BSI = ((B11+B4) - (B8+B2)) / ((B11+B4) + (B8+B2))
        b11_b4 = img.select("B11").add(img.select("B4"))
        b8_b2 = img.select("B8").add(img.select("B2"))
        bsi = b11_b4.subtract(b8_b2).divide(b11_b4.add(b8_b2)).rename("BSI")
        b11 = img.select("B11").rename("B11")
        return img.addBands(ndvi).addBands(ndwi).addBands(ndbi).addBands(bsi).addBands(b11)

    composite = coll.map(mask_clean).map(with_indices).median().clip(aoi)
    return composite.select(["NDVI", "NDWI", "NDBI", "BSI", "B11"]), n


def download_image(image, bbox, scale, out_tif):
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    url = image.getDownloadURL({
        "region": aoi, "scale": scale, "crs": "EPSG:4326",
        "format": "GEO_TIFF",
    })
    urllib.request.urlretrieve(url, out_tif)
    return out_tif


def fetch_dem_slope(bbox):
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    dem = ee.Image("USGS/SRTMGL1_003").clip(aoi)
    slope = ee.Terrain.slope(dem).rename("slope")
    return dem.rename("elevation"), slope


def stack_features_v2(aoi_name: str, year: int, scale: int = 20):
    print(f">>> V2 feature extraction {aoi_name} year={year} scale={scale}m")
    bbox = AOI_BBOXES[aoi_name]
    initialize_ee()

    bands = []
    band_names = []
    ref_transform = None
    ref_crs = None
    ref_shape = None

    # 1) 4 trimestres x 5 bandas (NDVI, NDWI, NDBI, BSI, B11)
    quarterly_ndvi = []
    for label, start, end in QUARTERS:
        print(f"    Bandas {label}...")
        composite, n = fetch_quarterly_indices(bbox, year, start, end, scale)
        if composite is None:
            print(f"      WARN: sin escenas en {label}, saltando")
            for idx_name in ["NDVI", "NDWI", "NDBI", "BSI", "B11"]:
                if ref_shape is not None:
                    bands.append(np.full(ref_shape, np.nan, dtype=np.float32))
                else:
                    bands.append(None)
                band_names.append(f"{idx_name}_{label}")
            continue
        tmp = OUT / f"_tmp_{aoi_name}_{label}_v2.tif"
        download_image(composite, bbox, scale, tmp)
        with rasterio.open(tmp) as src:
            if ref_transform is None:
                ref_transform = src.transform
                ref_crs = src.crs
                ref_shape = src.shape
            for i, idx_name in enumerate(["NDVI", "NDWI", "NDBI", "BSI", "B11"], 1):
                arr = src.read(i)
                if arr.shape != ref_shape:
                    from skimage.transform import resize
                    arr = resize(arr, ref_shape, preserve_range=True, anti_aliasing=False)
                bands.append(arr.astype(np.float32))
                band_names.append(f"{idx_name}_{label}")
                if idx_name == "NDVI":
                    quarterly_ndvi.append(arr.astype(np.float32))
        tmp.unlink(missing_ok=True)

    # Reemplazar None bands por NaN-array con shape correcto
    bands = [b if b is not None else np.full(ref_shape, np.nan, dtype=np.float32)
             for b in bands]

    # 2) Stats anuales NDVI
    print("    Stats anuales NDVI...")
    if quarterly_ndvi:
        ndvi_stack = np.stack(quarterly_ndvi, axis=0)
        ndvi_mean = np.nanmean(ndvi_stack, axis=0)
        ndvi_std = np.nanstd(ndvi_stack, axis=0)
        ndvi_min = np.nanmin(ndvi_stack, axis=0)
        ndvi_max = np.nanmax(ndvi_stack, axis=0)
        ndvi_range = ndvi_max - ndvi_min
    else:
        ndvi_mean = np.full(ref_shape, np.nan, dtype=np.float32)
        ndvi_std = np.full(ref_shape, np.nan, dtype=np.float32)
        ndvi_range = np.full(ref_shape, np.nan, dtype=np.float32)
    bands.extend([ndvi_mean, ndvi_std, ndvi_range, ndvi_max - ndvi_min if quarterly_ndvi else ndvi_range])
    band_names.extend(["ndvi_mean_yr", "ndvi_std_yr", "ndvi_range_yr", "ndvi_amplitude_yr"])

    # 3) Contexto espacial: NDVI local mean / std (3x3)
    print("    Contexto espacial (3x3) NDVI...")
    from scipy.ndimage import generic_filter, uniform_filter
    ndvi_local_mean = uniform_filter(np.nan_to_num(ndvi_mean, nan=0.0), size=3, mode="nearest")
    # local std via E[X^2] - E[X]^2
    sq = np.nan_to_num(ndvi_mean, nan=0.0) ** 2
    ndvi_local_var = uniform_filter(sq, size=3, mode="nearest") - ndvi_local_mean ** 2
    ndvi_local_std = np.sqrt(np.maximum(ndvi_local_var, 0))
    bands.extend([ndvi_local_mean.astype(np.float32), ndvi_local_std.astype(np.float32)])
    band_names.extend(["ndvi_local_mean_3x3", "ndvi_local_std_3x3"])

    # 4) DEM + slope
    print("    DEM + slope...")
    dem, slope = fetch_dem_slope(bbox)
    tmp_dem = OUT / f"_tmp_{aoi_name}_dem_v2.tif"
    download_image(dem, bbox, scale, tmp_dem)
    tmp_slope = OUT / f"_tmp_{aoi_name}_slope_v2.tif"
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
    bands.extend([dem_arr.astype(np.float32), slope_arr.astype(np.float32)])
    band_names.extend(["elevation", "slope"])
    tmp_dem.unlink(missing_ok=True); tmp_slope.unlink(missing_ok=True)

    # 5) Stack final
    stack = np.stack(bands, axis=0).astype(np.float32)
    print(f"    Stack: {stack.shape}, {len(band_names)} bands")

    out_tif = OUT / f"features_v2_{aoi_name}_{year}.tif"
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
    return out_tif, band_names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--aoi", choices=list(AOI_BBOXES.keys()), required=True)
    ap.add_argument("--scale", type=int, default=20)
    args = ap.parse_args()
    stack_features_v2(args.aoi, args.year, args.scale)


if __name__ == "__main__":
    main()
