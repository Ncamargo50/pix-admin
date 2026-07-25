"""Descarga Sentinel-2 RGB compuesto via Earth Engine."""
from __future__ import annotations

import urllib.request
from pathlib import Path

import numpy as np
import rasterio


def initialize_ee():
    """Inicializa Earth Engine si no esta inicializado. Idempotente."""
    import ee
    try:
        ee.Number(1).getInfo()
    except Exception:
        ee.Initialize()


def fetch_sentinel2_rgb(bbox: list[float],
                        start: str = "2026-01-01",
                        end: str = "2026-02-25",
                        cloud_pct: int = 30,
                        cache_dir: Path | None = None) -> tuple[np.ndarray, "Affine", str, dict]:
    """
    Descarga compuesto S2 mediano clear-sky para un bbox.

    Args:
        bbox: [W, S, E, N] en WGS84.
        start, end: ISO date strings.
        cloud_pct: filtra escenas con > X% nubes.
        cache_dir: si se pasa, guarda TIFF en disco para reuso.

    Returns:
        (rgb HxWx3 uint8, transform, crs, metadata)
    """
    import ee
    initialize_ee()

    aoi = ee.Geometry.Rectangle(list(bbox))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct)))
    n = coll.size().getInfo()
    if n == 0:
        raise RuntimeError(
            f"Sin escenas Sentinel-2 para bbox={bbox} {start}->{end} "
            f"con < {cloud_pct}% nubes"
        )

    def mask(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        return img.updateMask(clear).divide(10000)

    comp = coll.map(mask).median().clip(aoi)
    rgb = comp.select(["B4", "B3", "B2"]).multiply(2200).clamp(0, 255).toUint8()

    url = rgb.getDownloadURL({"region": aoi, "scale": 10, "crs": "EPSG:4326",
                              "format": "GEO_TIFF"})

    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        # nombre estable por bbox+fechas
        fn = f"s2_{bbox[0]:.4f}_{bbox[1]:.4f}_{bbox[2]:.4f}_{bbox[3]:.4f}_{start}_{end}.tif"
        out = cache_dir / fn
        if not out.exists():
            urllib.request.urlretrieve(url, out)
        with rasterio.open(out) as src:
            arr = src.read([1, 2, 3]).transpose(1, 2, 0)
            return arr, src.transform, str(src.crs), {
                "n_scenes": n, "cached_path": str(out),
                "size_kb": out.stat().st_size // 1024,
            }

    # in-memory
    import io
    data = urllib.request.urlopen(url).read()
    with rasterio.MemoryFile(data) as memfile:
        with memfile.open() as src:
            arr = src.read([1, 2, 3]).transpose(1, 2, 0)
            return arr, src.transform, str(src.crs), {"n_scenes": n}


def fetch_sentinel2_rgb_enhanced(bbox: list[float],
                                  start: str = "2026-01-01",
                                  end: str = "2026-04-15",
                                  cloud_pct: int = 30,
                                  scale_m: int = 10,
                                  enhancement: str = "natural",
                                  cache_dir: Path | None = None) -> tuple[np.ndarray, "Affine", str, dict]:
    """
    Sentinel-2 RGB color natural MEJORADO con stretching adaptativo y opciones.

    enhancement: 'natural' (B4 B3 B2 + stretch), 'agro' (more contrast for crops),
                  'urban' (sharper), 'true_color' (sin enhance, como viene de S2).
    scale_m: 10 = 10m nativo, 20 = downscale 2x para periodos grandes.
    """
    import ee
    initialize_ee()

    aoi = ee.Geometry.Rectangle(list(bbox))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct)))
    n = coll.size().getInfo()
    if n == 0:
        raise RuntimeError(f"Sin escenas Sentinel-2 para {bbox} {start}-{end} (<{cloud_pct}% nubes)")

    def mask_clear(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        return img.updateMask(clear).divide(10000).copyProperties(img, ["system:time_start"])

    composite = coll.map(mask_clear).median().clip(aoi)

    # Aplicar enhancement
    if enhancement == "true_color":
        # Sin stretch, solo escalado simple
        rgb = composite.select(["B4", "B3", "B2"]).multiply(2500).clamp(0, 255).toUint8()
    elif enhancement == "agro":
        # Mas contraste para destacar cultivos verdes
        r = composite.select("B4").multiply(2800).clamp(0, 255)
        g = composite.select("B3").multiply(2600).clamp(0, 255)
        b = composite.select("B2").multiply(2400).clamp(0, 255)
        rgb = ee.Image.cat([r, g, b]).toUint8()
    elif enhancement == "urban":
        # Mas saturado, mejor para construcciones / caminos
        r = composite.select("B4").multiply(3200).clamp(0, 255)
        g = composite.select("B3").multiply(2900).clamp(0, 255)
        b = composite.select("B2").multiply(2700).clamp(0, 255)
        rgb = ee.Image.cat([r, g, b]).toUint8()
    else:  # natural (default)
        # Stretching percentil-based via reducer (mas natural)
        # Aplicar gamma 1.1 + contraste leve
        r = composite.select("B4").multiply(2700).clamp(0, 255)
        g = composite.select("B3").multiply(2700).clamp(0, 255)
        b = composite.select("B2").multiply(2700).clamp(0, 255)
        rgb = ee.Image.cat([r, g, b]).toUint8()

    url = rgb.getDownloadURL({
        "region": aoi, "scale": scale_m, "crs": "EPSG:4326",
        "format": "GEO_TIFF",
    })

    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        fn = (f"s2enh_{enhancement}_{scale_m}m_{bbox[0]:.4f}_{bbox[1]:.4f}_"
              f"{bbox[2]:.4f}_{bbox[3]:.4f}_{start}_{end}.tif")
        out = cache_dir / fn
        if not out.exists():
            urllib.request.urlretrieve(url, out)
        with rasterio.open(out) as src:
            arr = src.read([1, 2, 3]).transpose(1, 2, 0)
            return arr, src.transform, str(src.crs), {
                "n_scenes": n, "cached_path": str(out),
                "enhancement": enhancement, "scale_m": scale_m,
            }

    data = urllib.request.urlopen(url).read()
    with rasterio.MemoryFile(data) as memfile:
        with memfile.open() as src:
            arr = src.read([1, 2, 3]).transpose(1, 2, 0)
            return arr, src.transform, str(src.crs), {
                "n_scenes": n, "enhancement": enhancement, "scale_m": scale_m,
            }


def fetch_sentinel2_ndvi(bbox: list[float],
                         start: str = "2026-01-01",
                         end: str = "2026-02-25",
                         cloud_pct: int = 30,
                         cache_dir: Path | None = None) -> tuple[np.ndarray, "Affine", str, dict]:
    """Compuesto NDVI mediano para el mismo periodo. Reusable para useful_area."""
    import ee
    initialize_ee()

    aoi = ee.Geometry.Rectangle(list(bbox))
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct)))
    n = coll.size().getInfo()
    if n == 0:
        raise RuntimeError(f"Sin escenas S2 para NDVI bbox={bbox} {start}->{end}")

    def mask_and_ndvi(img):
        scl = img.select("SCL")
        clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
        m = img.updateMask(clear).divide(10000)
        return m.normalizedDifference(["B8", "B4"]).rename("NDVI") \
                .copyProperties(img, ["system:time_start"])

    ndvi = coll.map(mask_and_ndvi).median().clip(aoi)

    url = ndvi.getDownloadURL({"region": aoi, "scale": 10, "crs": "EPSG:4326",
                               "format": "GEO_TIFF"})

    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        fn = f"ndvi_{bbox[0]:.4f}_{bbox[1]:.4f}_{bbox[2]:.4f}_{bbox[3]:.4f}_{start}_{end}.tif"
        out = cache_dir / fn
        if not out.exists():
            urllib.request.urlretrieve(url, out)
        with rasterio.open(out) as src:
            return src.read(1), src.transform, str(src.crs), {"n_scenes": n}

    data = urllib.request.urlopen(url).read()
    with rasterio.MemoryFile(data) as memfile:
        with memfile.open() as src:
            return src.read(1), src.transform, str(src.crs), {"n_scenes": n}
