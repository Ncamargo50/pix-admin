"""
Inferencia con modelo V2 (LightGBM 28 features) para uso desde la API.

Funciones:
  - extract_features_v2_bbox(bbox, year): GEE -> array (28, H, W) + transform
  - predict_planting_v2(bbox, year, threshold): -> list of GeoJSON polys
"""
from __future__ import annotations

import os
import urllib.request
import warnings
from pathlib import Path

os.environ["SHAPE_RESTORE_SHX"] = "YES"
warnings.filterwarnings("ignore")

import numpy as np
import rasterio
from rasterio.features import shapes as rio_shapes
import geopandas as gpd
from shapely.geometry import shape as shp_shape, mapping
from shapely import make_valid
from scipy.ndimage import binary_closing, binary_opening, uniform_filter
import joblib

ROOT = Path(__file__).resolve().parent.parent
_MODEL_V3 = ROOT / "planting_area" / "output" / "lgb_planting_area_v3_2025.joblib"
_MODEL_V2 = ROOT / "planting_area" / "output" / "lgb_planting_area_v2_2025.joblib"
MODEL_PATH = _MODEL_V3 if _MODEL_V3.exists() else _MODEL_V2
CACHE_DIR = ROOT / "output" / "s2_cache"

QUARTERS = [
    ("Q1", "01-01", "03-31"),
    ("Q2", "04-01", "06-30"),
    ("Q3", "07-01", "09-30"),
    ("Q4", "10-01", "12-31"),
]


def _initialize_ee():
    import ee
    try:
        ee.Number(1).getInfo()
    except Exception:
        ee.Initialize()


def _utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    south = lat_mid < 0
    return f"EPSG:{32700 + zone if south else 32600 + zone}"


def _fetch_quarterly_indices_ee(bbox, year, qstart, qend):
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(f"{year}-{qstart}", f"{year}-{qend}")
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
        b11_b4 = img.select("B11").add(img.select("B4"))
        b8_b2 = img.select("B8").add(img.select("B2"))
        bsi = b11_b4.subtract(b8_b2).divide(b11_b4.add(b8_b2)).rename("BSI")
        b11 = img.select("B11").rename("B11")
        return img.addBands(ndvi).addBands(ndwi).addBands(ndbi).addBands(bsi).addBands(b11)

    composite = coll.map(mask_clean).map(with_indices).median().clip(aoi)
    return composite.select(["NDVI", "NDWI", "NDBI", "BSI", "B11"]), n


def _fetch_dem_slope_ee(bbox):
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    dem = ee.Image("USGS/SRTMGL1_003").clip(aoi)
    slope = ee.Terrain.slope(dem).rename("slope")
    return dem.rename("elevation"), slope


def _download_image(image, bbox, scale, out_tif):
    import ee
    aoi = ee.Geometry.Rectangle(list(bbox))
    url = image.getDownloadURL({
        "region": aoi, "scale": scale, "crs": "EPSG:4326",
        "format": "GEO_TIFF",
    })
    urllib.request.urlretrieve(url, out_tif)
    return out_tif


def extract_features_v2_bbox(bbox, year=2025, scale=20, cache_dir=None):
    """
    Extrae stack 28-band para un bbox arbitrario.
    Returns: (stack array (28,H,W), transform, crs, meta dict)
    """
    _initialize_ee()
    cache_dir = Path(cache_dir or CACHE_DIR / "v2_features")
    cache_dir.mkdir(parents=True, exist_ok=True)
    bbox_key = f"{bbox[0]:.4f}_{bbox[1]:.4f}_{bbox[2]:.4f}_{bbox[3]:.4f}_{year}"
    cached_tif = cache_dir / f"v2_{bbox_key}.tif"

    if cached_tif.exists():
        with rasterio.open(cached_tif) as src:
            return src.read(), src.transform, str(src.crs), {"cached": True, "n_scenes": "?"}

    bands = []
    band_names = []
    ref_transform = None; ref_crs = None; ref_shape = None
    quarterly_ndvi = []
    n_scenes_q = []

    for label, qs, qe in QUARTERS:
        comp, n = _fetch_quarterly_indices_ee(bbox, year, qs, qe)
        n_scenes_q.append(n)
        if comp is None:
            for idx_name in ["NDVI", "NDWI", "NDBI", "BSI", "B11"]:
                if ref_shape is not None:
                    bands.append(np.full(ref_shape, np.nan, dtype=np.float32))
                else:
                    bands.append(None)
                band_names.append(f"{idx_name}_{label}")
            continue
        tmp = cache_dir / f"_tmp_{bbox_key}_{label}.tif"
        _download_image(comp, bbox, scale, tmp)
        with rasterio.open(tmp) as src:
            if ref_transform is None:
                ref_transform = src.transform; ref_crs = src.crs; ref_shape = src.shape
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

    bands = [b if b is not None else np.full(ref_shape, np.nan, dtype=np.float32) for b in bands]

    # Stats anuales
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
    bands.extend([ndvi_mean, ndvi_std, ndvi_range, ndvi_range])
    band_names.extend(["ndvi_mean_yr", "ndvi_std_yr", "ndvi_range_yr", "ndvi_amplitude_yr"])

    # Spatial 3x3
    ndvi_local_mean = uniform_filter(np.nan_to_num(ndvi_mean, nan=0.0), size=3, mode="nearest")
    sq = np.nan_to_num(ndvi_mean, nan=0.0) ** 2
    ndvi_local_var = uniform_filter(sq, size=3, mode="nearest") - ndvi_local_mean ** 2
    ndvi_local_std = np.sqrt(np.maximum(ndvi_local_var, 0))
    bands.extend([ndvi_local_mean.astype(np.float32), ndvi_local_std.astype(np.float32)])
    band_names.extend(["ndvi_local_mean_3x3", "ndvi_local_std_3x3"])

    # DEM
    dem, slope = _fetch_dem_slope_ee(bbox)
    tmp_dem = cache_dir / f"_tmp_{bbox_key}_dem.tif"
    tmp_slope = cache_dir / f"_tmp_{bbox_key}_slope.tif"
    _download_image(dem, bbox, scale, tmp_dem)
    _download_image(slope, bbox, scale, tmp_slope)
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

    stack = np.stack(bands, axis=0).astype(np.float32)

    # Cache
    profile = {
        "driver": "GTiff", "dtype": "float32", "count": len(bands),
        "height": stack.shape[1], "width": stack.shape[2],
        "transform": ref_transform, "crs": ref_crs, "nodata": np.nan, "compress": "deflate",
    }
    with rasterio.open(cached_tif, "w", **profile) as dst:
        for i, (b, name) in enumerate(zip(bands, band_names), 1):
            dst.write(b, i)
            dst.set_band_description(i, name)

    return stack, ref_transform, str(ref_crs), {
        "n_scenes_quarterly": n_scenes_q, "cached_path": str(cached_tif),
        "scale_m": scale, "year": year,
    }


_MODEL_CACHE = None


def _load_model():
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Modelo V2 no encontrado en {MODEL_PATH}. "
                "Correr planting_area/03b_train_classifier_v2.py primero."
            )
        _MODEL_CACHE = joblib.load(MODEL_PATH)
    return _MODEL_CACHE


def _chaikin_smooth_metric(poly, iterations=2):
    """Suaviza coords (en metros). Acepta Polygon o MultiPolygon."""
    from shapely.geometry import Polygon as Pgon, MultiPolygon as MPgon
    def _smooth_ring(coords):
        if len(coords) < 4: return coords
        new = []
        for i in range(len(coords) - 1):
            p, q = coords[i], coords[i + 1]
            new.append((0.75*p[0] + 0.25*q[0], 0.75*p[1] + 0.25*q[1]))
            new.append((0.25*p[0] + 0.75*q[0], 0.25*p[1] + 0.75*q[1]))
        new.append(new[0])
        return new
    def _smooth_one(p):
        ext = list(p.exterior.coords)
        holes = [list(h.coords) for h in p.interiors]
        for _ in range(iterations):
            ext = _smooth_ring(ext)
            holes = [_smooth_ring(h) for h in holes]
        return Pgon(ext, holes)
    if isinstance(poly, MPgon):
        return MPgon([_smooth_one(g) for g in poly.geoms])
    return _smooth_one(poly)


def _run_delineate_anything_on_bbox(bbox, year, cache_dir):
    """Corre Delineate Anything sobre Sentinel-2 RGB del bbox y devuelve poligonos individuales."""
    from s2_fetch import fetch_sentinel2_rgb
    from inference import run_inference
    rgb, transform, crs, _ = fetch_sentinel2_rgb(
        bbox=bbox, start=f"{year}-01-01", end=f"{year}-04-15",
        cloud_pct=30, cache_dir=cache_dir,
    )
    polys = run_inference(rgb, transform, crs, size="small",
                          conf=0.05, iou_thr=0.4, min_area_ha=0.5)
    return polys  # lista de dicts {geometry, area_ha}


def predict_planting_v2(bbox, year=2025, threshold=0.5,
                        min_area_ha=1.0,
                        erode_pixels=2, dilate_pixels=2,
                        smooth_iters=2, simplify_m=12.0,
                        instance_separation=True,
                        use_delineate_anything=False) -> dict:
    """
    Inferencia con pipeline completo:
      1. Predict proba per pixel (LightGBM)
      2. Threshold + opening (limpia ruido)
      3. Erosion para separar lotes adjacentes (instance separation)
      4. Connected components labeling
      5. Dilation para recuperar tamano original (manteniendo separacion)
      6. Vectorizar cada componente como instancia separada
      7. Reproyectar a UTM, suavizar (Chaikin) y simplificar (Douglas-Peucker)
      8. Filtrar por area minima
    """
    from scipy.ndimage import label as ndi_label, binary_erosion, binary_dilation
    bundle = _load_model()
    model = bundle["model"]
    best_iter = bundle.get("best_iteration", model.best_iteration)

    stack, transform, crs, meta = extract_features_v2_bbox(bbox, year=year)
    H, W = stack.shape[1], stack.shape[2]

    valid = ~np.isnan(stack).any(axis=0)
    flat = stack.reshape(stack.shape[0], -1).T
    valid_flat = valid.flatten()
    proba = np.zeros(H * W, dtype=np.float32)
    proba[valid_flat] = model.predict(flat[valid_flat], num_iteration=best_iter)
    proba = proba.reshape(H, W)

    # Diagnostico de la prediccion
    proba_valid = proba[valid]
    pct_above = float((proba_valid > threshold).mean()) if proba_valid.size else 0
    proba_stats = {
        "valid_pixels": int(valid.sum()),
        "pct_above_threshold": round(pct_above * 100, 2),
        "proba_mean": round(float(proba_valid.mean()), 3) if proba_valid.size else None,
        "proba_median": round(float(np.median(proba_valid)), 3) if proba_valid.size else None,
    }

    raw = (proba > threshold) & valid
    # Pequeno opening para limpiar pixels aislados
    raw = binary_opening(raw, iterations=1)
    raw = binary_closing(raw, iterations=1)  # tapar gaps de 1 pixel

    if not raw.any():
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"imagery": meta, "n_polygons": 0,
                              "diagnostics": proba_stats, "model": "v2_lightgbm_28features",
                              "threshold": threshold, "year": year, "bbox": bbox,
                              "warning": "Ningun pixel supera threshold; bajar threshold."}}

    if instance_separation and erode_pixels > 0:
        eroded = binary_erosion(raw, iterations=erode_pixels)
        labels, n_inst = ndi_label(eroded, structure=np.ones((3, 3), dtype=int))
        n_components = int(n_inst)
        # Recuperar tamano via watershed-like dilation por etiqueta:
        # Para cada label expandir hasta tocar el borde de raw original.
        instance_mask = np.zeros_like(raw, dtype=np.int32)
        if n_inst > 0:
            from scipy.ndimage import distance_transform_edt
            # Distancia EDT por etiqueta usando watershed simple:
            # asignar cada pixel de raw al label mas cercano del eroded
            from scipy.ndimage import binary_dilation as bd
            # Empezar con eroded labels y dilatar todos juntos solo dentro de raw
            current = labels.copy()
            for _ in range(erode_pixels + dilate_pixels + 1):
                # Dilatar cada label una iteracion controlada
                growing = bd(current > 0, iterations=1) & raw
                # Para los pixels nuevos que no tienen label, asignar el label del vecino dominante
                new_pixels = growing & (current == 0)
                if not new_pixels.any():
                    break
                # Dilatar las labels existentes con max filter para asignar a vecinos
                from scipy.ndimage import grey_dilation
                expanded = grey_dilation(current, size=3)
                current = np.where(new_pixels, expanded, current)
            instance_mask = current
        else:
            instance_mask = labels
    else:
        labels, n_inst = ndi_label(raw, structure=np.ones((3, 3), dtype=int))
        instance_mask = labels
        n_components = int(n_inst)

    # Si activado: usar Delineate Anything para subdividir blobs grandes
    if use_delineate_anything:
        try:
            cache_dir = ROOT / "output" / "s2_cache"
            da_polys = _run_delineate_anything_on_bbox(bbox, year, cache_dir)
            # Mascara V3 binaria 1=planting, 0=otro
            v3_mask_full = raw  # binary mask post opening/closing
            # Para cada poligono de DA, calcular si esta MAYORMENTE dentro de v3_mask_full
            # y devolver solo esos como instancias individuales
            from rasterio.features import geometry_mask as gm
            keep = []
            for p in da_polys:
                g = p["geometry"]
                try:
                    mk = gm([g], out_shape=raw.shape, transform=transform, invert=True)
                    inter_pixels = int((mk & v3_mask_full).sum())
                    poly_pixels = int(mk.sum())
                    if poly_pixels == 0: continue
                    inside_pct = inter_pixels / poly_pixels
                    if inside_pct >= 0.50:  # >50% dentro de mascara V3 = lote real
                        keep.append((g, p["area_ha"], inside_pct))
                except Exception:
                    continue
            if keep:
                # Saltearse el connected components y usar directo los poligonos DA
                geoms = [(i+1, g) for i, (g, _, _) in enumerate(keep)]
                n_components = len(keep)
                proba_stats["delineate_anything_polygons_kept"] = len(keep)
                proba_stats["delineate_anything_polygons_total"] = len(da_polys)
            else:
                # Fallback a CCL si DA no detecto nada util
                geoms = []
                for inst_id in range(1, n_components + 1):
                    comp = (instance_mask == inst_id).astype(np.uint8)
                    if comp.sum() == 0: continue
                    for geom_dict, val in rio_shapes(comp, transform=transform):
                        if val == 1:
                            gg = shp_shape(geom_dict)
                            if gg.is_valid and gg.area > 0:
                                geoms.append((inst_id, gg))
                proba_stats["delineate_anything_fallback"] = "ccl"
        except Exception as e:
            proba_stats["delineate_anything_error"] = str(e)[:200]
            geoms = []
            for inst_id in range(1, n_components + 1):
                comp = (instance_mask == inst_id).astype(np.uint8)
                if comp.sum() == 0: continue
                for geom_dict, val in rio_shapes(comp, transform=transform):
                    if val == 1:
                        gg = shp_shape(geom_dict)
                        if gg.is_valid and gg.area > 0:
                            geoms.append((inst_id, gg))
    else:
        # Vectorizar cada componente individualmente (CCL standard)
        geoms = []
        for inst_id in range(1, n_components + 1):
            comp = (instance_mask == inst_id).astype(np.uint8)
            if comp.sum() == 0:
                continue
            for geom_dict, val in rio_shapes(comp, transform=transform):
                if val == 1:
                    g = shp_shape(geom_dict)
                    if g.is_valid and g.area > 0:
                        geoms.append((inst_id, g))

    if not geoms:
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"imagery": meta, "n_polygons": 0,
                              "diagnostics": proba_stats}}

    # Reproyectar a UTM para smoothing/simplify en metros
    utm = _utm_for_bounds([min(g[1].bounds[0] for g in geoms),
                           min(g[1].bounds[1] for g in geoms),
                           max(g[1].bounds[2] for g in geoms),
                           max(g[1].bounds[3] for g in geoms)])
    base_gdf = gpd.GeoDataFrame(
        {"inst_id": [g[0] for g in geoms]},
        geometry=[g[1] for g in geoms], crs=crs).to_crs(utm)

    refined_rows = []
    for inst_id, group in base_gdf.groupby("inst_id"):
        # Unir multipart por instance
        merged = group.geometry.unary_union if hasattr(group.geometry, "unary_union") \
            else group.geometry.union_all()
        merged = make_valid(merged).buffer(0)
        # Smoothing Chaikin
        if smooth_iters > 0:
            merged = _chaikin_smooth_metric(merged, iterations=smooth_iters)
        # Simplify (Douglas-Peucker) en metros
        if simplify_m > 0:
            merged = merged.simplify(simplify_m, preserve_topology=True)
        merged = make_valid(merged).buffer(0)
        if merged.is_empty: continue
        # Si tras smoothing es MultiPolygon, separar en piezas individuales
        if hasattr(merged, "geoms"):
            for sub in merged.geoms:
                refined_rows.append({"inst_id": int(inst_id), "geometry": sub,
                                      "area_ha": sub.area / 10_000})
        else:
            refined_rows.append({"inst_id": int(inst_id), "geometry": merged,
                                  "area_ha": merged.area / 10_000})

    if not refined_rows:
        return {"type": "FeatureCollection", "features": [],
                "metadata": {"imagery": meta, "n_polygons": 0,
                              "diagnostics": proba_stats}}

    refined_gdf = gpd.GeoDataFrame(refined_rows, crs=utm)
    refined_gdf = refined_gdf[refined_gdf["area_ha"] >= min_area_ha].copy()
    refined_gdf = refined_gdf.reset_index(drop=True)

    # Reasignar IDs secuenciales
    refined_wgs = refined_gdf.to_crs("EPSG:4326")

    feats = [{
        "type": "Feature",
        "properties": {
            "id": i,
            "area_ha": round(float(row.area_ha), 3),
            "model": "v2_smoothed",
            "threshold": threshold,
        },
        "geometry": mapping(row.geometry),
    } for i, row in refined_wgs.iterrows()]

    return {
        "type": "FeatureCollection",
        "features": feats,
        "metadata": {
            "n_polygons": len(feats),
            "total_area_ha": round(float(refined_gdf["area_ha"].sum()), 2),
            "imagery": meta,
            "model": "v2_lightgbm_28features",
            "threshold": threshold,
            "year": year,
            "bbox": bbox,
            "diagnostics": proba_stats,
            "instance_separation": instance_separation,
            "smooth_iters": smooth_iters,
            "simplify_m": simplify_m,
            "n_components_pre_filter": n_components,
        },
    }
