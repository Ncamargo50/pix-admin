"""
Descarga + stitch de tiles Esri World Imagery (alta resolucion, ~30cm-1m).
Sin auth, sin API key.

Tile URL: https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}

Uso:
    rgb, transform, crs = download_highres_bbox(bbox, zoom=17)
"""
from __future__ import annotations

import io
import math
import urllib.request
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
from PIL import Image

ESRI_TILE = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
GOOGLE_TILE = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
TILE_SIZE = 256


def lonlat_to_tile(lon, lat, zoom):
    """Web Mercator tile XY desde lon/lat."""
    n = 2 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile


def tile_to_lonlat(x, y, zoom):
    """Esquina superior-izquierda del tile."""
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lon, lat


def _fetch_tile(url, retries=3):
    last_err = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 PixadvisorAgent"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
            return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Tile fetch failed {url}: {last_err}")


def download_highres_bbox(bbox, zoom=17, source="esri", workers=8, cache_dir=None):
    """
    Descarga y stitchea tiles para cubrir el bbox.

    Args:
        bbox: [W, S, E, N] WGS84
        zoom: 15 (~5m), 16 (~2.5m), 17 (~1.2m), 18 (~0.6m), 19 (~0.3m)
        source: 'esri' (libre) o 'google'
    Returns:
        (rgb_array (H,W,3) uint8, rasterio.Affine transform, crs string)
    """
    W, S, E, N = bbox
    tx0, ty0 = lonlat_to_tile(W, N, zoom)  # esquina NW
    tx1, ty1 = lonlat_to_tile(E, S, zoom)  # esquina SE
    n_tiles = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
    print(f"  highres: zoom={zoom} tiles={n_tiles} ({tx0}..{tx1} x {ty0}..{ty1})")
    if n_tiles > 800:
        raise ValueError(f"Demasiados tiles ({n_tiles}). Bajar zoom o achicar bbox.")

    template = ESRI_TILE if source == "esri" else GOOGLE_TILE

    cache = Path(cache_dir) if cache_dir else None
    if cache: cache.mkdir(parents=True, exist_ok=True)

    def _get(x, y):
        if cache:
            p = cache / f"{source}_{zoom}_{x}_{y}.jpg"
            if p.exists():
                try: return x, y, Image.open(p).convert("RGB")
                except Exception: pass
        img = _fetch_tile(template.format(z=zoom, x=x, y=y))
        if cache:
            try: img.save(cache / f"{source}_{zoom}_{x}_{y}.jpg", "JPEG", quality=88)
            except Exception: pass
        return x, y, img

    # Stitch
    width = (tx1 - tx0 + 1) * TILE_SIZE
    height = (ty1 - ty0 + 1) * TILE_SIZE
    canvas = Image.new("RGB", (width, height), (0, 0, 0))

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = []
        for y in range(ty0, ty1 + 1):
            for x in range(tx0, tx1 + 1):
                futures.append(ex.submit(_get, x, y))
        done = 0
        for fut in as_completed(futures):
            try:
                x, y, img = fut.result()
                canvas.paste(img, ((x - tx0) * TILE_SIZE, (y - ty0) * TILE_SIZE))
            except Exception as e:
                print(f"  WARN tile fail: {e}")
            done += 1

    rgb = np.asarray(canvas)

    # Calcular transform a partir de las esquinas reales del mosaico
    nw_lon, nw_lat = tile_to_lonlat(tx0, ty0, zoom)
    se_lon, se_lat = tile_to_lonlat(tx1 + 1, ty1 + 1, zoom)
    px_w = (se_lon - nw_lon) / width
    px_h = (se_lat - nw_lat) / height
    from rasterio.transform import Affine
    transform = Affine(px_w, 0, nw_lon, 0, px_h, nw_lat)
    crs = "EPSG:4326"

    print(f"  highres OK: {rgb.shape[1]}x{rgb.shape[0]}, ~{abs(px_w)*111000:.2f}m/pixel")
    return rgb, transform, crs


def crop_to_exact_bbox(rgb, transform, bbox):
    """Recorta el mosaico al bbox exacto del usuario (saca el padding de tiles externos)."""
    W, S, E, N = bbox
    inv = ~transform
    col0, row0 = inv * (W, N)
    col1, row1 = inv * (E, S)
    col0 = max(0, int(round(col0)))
    row0 = max(0, int(round(row0)))
    col1 = min(rgb.shape[1], int(round(col1)))
    row1 = min(rgb.shape[0], int(round(row1)))
    if col1 <= col0 or row1 <= row0:
        return rgb, transform
    rgb_c = rgb[row0:row1, col0:col1]
    new_origin = transform * (col0, row0)
    new_transform = transform.__class__(
        transform.a, transform.b, new_origin[0],
        transform.d, transform.e, new_origin[1],
    )
    return rgb_c, new_transform
