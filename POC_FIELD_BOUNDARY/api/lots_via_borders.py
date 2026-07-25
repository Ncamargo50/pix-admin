"""
Detector de lotes basado en BORDES VISIBLES (la logica que el operador dibuja a mano).

Approach (alineado con como el humano demilita un lote):
  1. Imagen alta resolucion (Esri ~1m o Google sat) del bbox.
  2. Detectar pixels OSCUROS (lineas de arboles, caminos, alambres) -> mascara de bordes.
  3. Engrosar bordes via morfologia para conectar tree-lines interrumpidas.
  4. Invertir -> mascara de FIELDS (lo que NO es borde).
  5. Erosion fuerte para separar lotes adjacentes que comparten poca conexion.
  6. Connected components labeling -> cada lote = un component individual.
  7. Para cada lote: dilatar de vuelta + find contours en OpenCV (TC89 simplifica).
  8. approxPolyDP (Douglas-Peucker) para reducir vertices manteniendo forma.
  9. Convertir pixel coords a lon/lat via transform.
  10. Filtrar por area minima.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Polygon, mapping
from shapely import make_valid

from highres_tiles import download_highres_bbox, crop_to_exact_bbox

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "output" / "highres_cache"


def _utm_for_bounds(bounds):
    lon_mid = (bounds[0] + bounds[2]) / 2
    lat_mid = (bounds[1] + bounds[3]) / 2
    zone = int((lon_mid + 180) / 6) + 1
    return f"EPSG:{32700 + zone if lat_mid < 0 else 32600 + zone}"


def detect_lots_via_borders(bbox, zoom=17, source="esri",
                             border_block_size=51,    # tamano vecindad para adaptive threshold
                             border_C=3,              # offset adaptive threshold
                             border_dilate=2,         # iteraciones para engrosar bordes
                             field_erode=4,           # iteraciones para SEPARAR lotes
                             field_open=2,            # opening final
                             min_area_ha=2.0,
                             approx_epsilon_pct=0.008, # 0.8% del perimetro = simplificacion DP
                             smooth_iters=1) -> dict:
    """
    Detecta lotes individuales en imagen high-res via bordes oscuros.
    Devuelve poligonos suaves siguiendo los limites visibles.
    """
    import time
    t0 = time.time()
    timings = {}

    # 1) Descargar mosaic
    rgb, transform, crs = download_highres_bbox(
        bbox, zoom=zoom, source=source, cache_dir=CACHE_DIR)
    rgb, transform = crop_to_exact_bbox(rgb, transform, bbox)
    timings["download"] = round(time.time() - t0, 2)
    H, W = rgb.shape[:2]
    px_size_m = abs(transform.a) * 111000

    # 2) Detectar bordes COMBINANDO 3 detectores (lineas oscuras de arboles/caminos)
    t0 = time.time()
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.bilateralFilter(gray, 9, 75, 75)

    # 2a) Canny edges - excelente para lineas finas
    canny = cv2.Canny(blur, 40, 120)

    # 2b) Adaptive threshold - capta zonas oscuras grandes
    adaptive = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        border_block_size if border_block_size % 2 == 1 else border_block_size + 1,
        border_C)

    # 2c) Black-hat morfologico - resalta lineas oscuras delgadas en fondo claro
    blackhat_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    blackhat = cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, blackhat_kernel)
    _, blackhat_th = cv2.threshold(blackhat, 15, 255, cv2.THRESH_BINARY)

    # 2d) Combinar via OR - cualquier detector que diga "borde" cuenta
    border_mask = cv2.bitwise_or(canny, adaptive)
    border_mask = cv2.bitwise_or(border_mask, blackhat_th)

    # 3) Engrosar bordes para conectar tree-lines fragmentadas
    if border_dilate > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        border_mask = cv2.dilate(border_mask, kernel, iterations=border_dilate)
    # Cerrar gaps pequenos en las lineas
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    border_mask = cv2.morphologyEx(border_mask, cv2.MORPH_CLOSE, close_kernel, iterations=2)
    timings["border_detect"] = round(time.time() - t0, 2)

    # 4) Mascara FIELDS = NOT border
    t0 = time.time()
    field_mask = (border_mask == 0).astype(np.uint8) * 255

    # 5) Eliminar manchas chicas (ruido) en field_mask
    if field_open > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        field_mask = cv2.morphologyEx(field_mask, cv2.MORPH_OPEN, kernel,
                                       iterations=field_open)

    # 6) EROSION fuerte para separar lotes que estan apenas conectados
    if field_erode > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        field_eroded = cv2.erode(field_mask, kernel, iterations=field_erode)
    else:
        field_eroded = field_mask

    # 7) Connected components etiquetado
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(field_eroded)
    timings["morphology_ccl"] = round(time.time() - t0, 2)
    timings["n_components_raw"] = int(n_labels - 1)

    # 8) Para cada componente: dilatar de vuelta para recuperar tamano + extract contour
    t0 = time.time()
    min_pixels = int(min_area_ha * 10000 / (px_size_m ** 2))
    polygons = []
    for i in range(1, n_labels):
        area_px = stats[i, cv2.CC_STAT_AREA]
        if area_px < min_pixels: continue

        # Crear bbox local para procesar solo la region del componente
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        # Padding para dilatacion
        pad = field_erode + 2
        x0 = max(0, x - pad); y0 = max(0, y - pad)
        x1 = min(W, x + w + pad); y1 = min(H, y + h + pad)
        comp_local = ((labels[y0:y1, x0:x1] == i)).astype(np.uint8) * 255

        # Dilatar para recuperar tamano original perdido por erode
        if field_erode > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            comp_local = cv2.dilate(comp_local, kernel, iterations=field_erode)
            # Pero clip al field_mask original (sin erode) para no salir de los bordes
            field_local = field_mask[y0:y1, x0:x1]
            comp_local = cv2.bitwise_and(comp_local, field_local)

        # Find external contour
        contours, _ = cv2.findContours(comp_local, cv2.RETR_EXTERNAL,
                                         cv2.CHAIN_APPROX_TC89_KCOS)
        if not contours: continue
        # Tomar contour mas grande
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) * (px_size_m ** 2) / 10000 < min_area_ha:
            continue

        # Douglas-Peucker simplification para suavizar
        peri = cv2.arcLength(cnt, True)
        eps = approx_epsilon_pct * peri
        approx = cv2.approxPolyDP(cnt, eps, True)

        # Reproyectar pixel coords -> lat/lon
        points_lonlat = []
        for pt in approx[:, 0, :]:
            px = pt[0] + x0  # absoluto
            py = pt[1] + y0
            lon, lat = transform * (px + 0.5, py + 0.5)
            points_lonlat.append((lon, lat))
        if len(points_lonlat) < 3: continue
        points_lonlat.append(points_lonlat[0])  # cerrar

        try:
            poly = Polygon(points_lonlat)
            poly = make_valid(poly).buffer(0)
            if not poly.is_valid or poly.is_empty: continue
            if hasattr(poly, "geoms"):
                poly = max(poly.geoms, key=lambda p: p.area)
        except Exception:
            continue

        polygons.append(poly)

    timings["vectorize"] = round(time.time() - t0, 2)

    if not polygons:
        return {
            "type": "FeatureCollection", "features": [],
            "metadata": {"timings": timings, "n_polygons": 0,
                         "imagery": {"source": source, "zoom": zoom,
                                      "shape": [H, W], "m_per_pixel": round(px_size_m, 3)}}
        }

    # 9) Smooth Chaikin liviano + filtros area en metric
    from shapely.geometry import Polygon as Pgon
    def chaikin(p, iters):
        def _ring(coords):
            if len(coords) < 4: return coords
            new = []
            for i in range(len(coords) - 1):
                a, b = coords[i], coords[i + 1]
                new.append((0.75*a[0] + 0.25*b[0], 0.75*a[1] + 0.25*b[1]))
                new.append((0.25*a[0] + 0.75*b[0], 0.25*a[1] + 0.75*b[1]))
            new.append(new[0])
            return new
        ext = list(p.exterior.coords)
        for _ in range(iters): ext = _ring(ext)
        return Pgon(ext)

    if smooth_iters > 0:
        polygons = [chaikin(p, smooth_iters) for p in polygons]

    gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")
    metric = _utm_for_bounds(gdf.total_bounds)
    gdf_m = gdf.to_crs(metric)
    gdf["area_ha"] = gdf_m.area / 10_000
    gdf = gdf[gdf["area_ha"] >= min_area_ha].sort_values("area_ha", ascending=False).reset_index(drop=True)

    feats = [{
        "type": "Feature",
        "properties": {
            "id": int(i), "area_ha": round(float(row.area_ha), 3),
            "model": "borders_opencv", "zoom": zoom, "source": source,
        },
        "geometry": mapping(row.geometry),
    } for i, row in gdf.iterrows()]

    timings["total"] = round(sum(v for v in timings.values() if isinstance(v,(int,float))), 2)

    return {
        "type": "FeatureCollection",
        "features": feats,
        "metadata": {
            "n_polygons": len(feats),
            "total_area_ha": round(float(gdf["area_ha"].sum()), 2),
            "imagery": {"source": source, "zoom": zoom, "shape": [H, W],
                         "m_per_pixel": round(px_size_m, 3)},
            "timings": timings,
            "params": {
                "border_block_size": border_block_size, "border_C": border_C,
                "border_dilate": border_dilate, "field_erode": field_erode,
                "approx_epsilon_pct": approx_epsilon_pct, "smooth_iters": smooth_iters,
            },
            "bbox": bbox,
        },
    }
