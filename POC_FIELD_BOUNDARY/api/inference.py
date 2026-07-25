"""Inferencia Delineate Anything con modelo cargado en memoria."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS_DIR = ROOT / "output"
WEIGHTS = {
    "small": WEIGHTS_DIR / "delineate-anything-s.pt",
    "large": WEIGHTS_DIR / "delineate-anything-large.pt",
}


@lru_cache(maxsize=2)
def load_model(size: str = "small"):
    """Carga modelo YOLO una sola vez. Cached por tamano."""
    from ultralytics import YOLO
    path = WEIGHTS.get(size)
    if path is None or not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Bajar de huggingface.co/MykolaL/DelineateAnything"
        )
    return YOLO(str(path))


def run_inference(rgb: np.ndarray, transform, crs,
                  size: str = "small", conf: float = 0.05,
                  iou_thr: float = 0.4, min_area_ha: float = 0.3) -> list:
    """
    Corre Delineate Anything sobre un array RGB HxWx3 y devuelve poligonos.

    Args:
        rgb: array HxWx3 en uint8 (0-255).
        transform: rasterio Affine.
        crs: CRS del raster (str o pyproj CRS).
        size: 'small' (16.8 MB) o 'large' (125 MB).
        conf: confianza minima.
        iou_thr: IoU threshold para NMS.
        min_area_ha: descarta poligonos menores.

    Returns:
        Lista de dicts {geometry: shapely.Polygon, area_ha: float}.
    """
    from PIL import Image
    import tempfile
    from rasterio.features import shapes
    from shapely.geometry import shape
    import geopandas as gpd

    model = load_model(size)

    if rgb.dtype != np.uint8:
        p2, p98 = np.percentile(rgb, (2, 98))
        rgb = np.clip((rgb - p2) / max(p98 - p2, 1e-6) * 255, 0, 255).astype(np.uint8)

    h, w = rgb.shape[:2]
    imgsz = max(640, ((max(h, w) + 31) // 32) * 32)

    # YOLO espera path o PIL.Image; usar tempfile para evitar pasar array crudo
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        Image.fromarray(rgb).save(tmp.name)
        tmp_path = tmp.name

    try:
        results = model.predict(source=tmp_path, imgsz=imgsz,
                                conf=conf, iou=iou_thr, retina_masks=True,
                                agnostic_nms=True, verbose=False)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    geoms = []
    for r in results:
        if r.masks is None:
            continue
        masks = r.masks.data.cpu().numpy()
        for m in masks:
            mask = (m > 0.5).astype("uint8")
            for geom, val in shapes(mask, transform=transform):
                if val == 1:
                    g = shape(geom)
                    if g.area > 1e-7:
                        geoms.append(g)

    if not geoms:
        return []

    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs or "EPSG:4326")
    # area en m2 - reproyectar a equal-area
    metric_crs = gdf.estimate_utm_crs()
    gdf["area_ha"] = gdf.to_crs(metric_crs).area / 10_000
    gdf = gdf[gdf["area_ha"] >= min_area_ha].copy()
    gdf = gdf.reset_index(drop=True)

    return [
        {"geometry": row.geometry, "area_ha": float(row.area_ha)}
        for row in gdf.itertuples()
    ]
