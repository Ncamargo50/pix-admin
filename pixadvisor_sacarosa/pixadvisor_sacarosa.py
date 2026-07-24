#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — PIPELINE DE SACAROSA EN CAÑA DE AZÚCAR
Hacienda del Señor — Sentinel-2A más reciente sin nubes, lote por lote
============================================================================

Pipeline end-to-end:
  1) Descubre lotes en estructura local (zonas_manejo_<lote>_PRO.shp).
  2) Disuelve zonas internas → polígono del lote (EPSG:32720 UTM 20S).
  3) Para cada lote: busca imagen Sentinel-2A más reciente con
     CLOUDY_PIXEL_PERCENTAGE < 30% y >80% de píxeles válidos sobre el lote.
  4) Calcula índice de sacarosa Canata et al. (2024):
        Pol(%)  = 8.94  − 6.76·NDWI + 2.69·GNDVI + 3.7e-5·B3
        Brix(°) = 12.80 − 5.28·NDWI + 2.19·GNDVI + 2.9e-5·B3
     con NDWI(Gao) = (B8A − B11)/(B8A + B11)
         GNDVI    = (B8 − B3)/(B8 + B3)
  5) Suavizado Gaussiano server-side (anti-serrilhado).
  6) Descarga GeoTIFF (POL + BRIX) recortado al lote.
  7) Calcula estadísticas (min/max/media/desvío/percentiles).
  8) Renderiza mapa color profesional (matplotlib bicubic 220 DPI).
  9) Genera reporte PDF con branding Pixadvisor (verde #1B5E20).
 10) Escribe CSV resumen pix_sacarosa_index_<fecha>.csv.

REQUISITOS:
  pip install earthengine-api geopandas rasterio numpy pandas scipy ^
              matplotlib reportlab requests pyproj shapely
  earthengine authenticate          # solo la primera vez

EJECUCIÓN:
  python pixadvisor_sacarosa.py

SALIDAS (en OUTPUT_ROOT):
  pix_sacarosa_index_<fecha>.csv
  <lote>/POL_<lote>_<fecha>.tif
  <lote>/BRIX_<lote>_<fecha>.tif
  <lote>/mapa_<lote>.png
  <lote>/PIX_Sacarosa_<lote>_<fecha>.pdf

CAVEAT CIENTÍFICO:
  R² esperable Pol absoluto: 0.55–0.70 (referencia: literatura).
  El mapa es principalmente RELATIVO (zonas más maduras vs menos).
  Para Pol absoluto industrial → calibración local con análisis lab.

Pixadvisor AP — 2026-05-13
============================================================================
"""

from __future__ import annotations

import re
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para Windows (cp1252 default rompe con ✓ → etc.)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
import requests

import geopandas as gpd
import rasterio
from scipy.ndimage import gaussian_filter, zoom
import shapely
from shapely.ops import transform as shp_transform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

import ee

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage)

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN — EDITAR SI ES NECESARIO
# ════════════════════════════════════════════════════════════════════════════

LOTES_ROOT = Path(
    r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
    r"\Hacienda-Del-Senor\03-Zonas-Manejo"
)
OUTPUT_ROOT = Path(
    r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
    r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
)

# Patrón para shapefile de cada lote
SHP_PATTERN = "zonas_manejo_*_PRO.shp"

# Búsqueda de imagen
DIAS_ATRAS    = 60     # ventana de búsqueda S2 (días)
NUBES_MAX     = 30     # % nubosidad máxima de escena
COBERTURA_MIN = 0.80   # % píxeles válidos mínimos sobre el lote

# Suavizado
SMOOTH_PX_GEE   = 3    # radio Gaussiano server-side (px)
SMOOTH_PX_LOCAL = 1.5  # extra suavizado al renderizar (sigma sobre raster upsampleado)
RESAMPLE_FACTOR = 4    # upsample bicúbico raster antes de renderizar (10 m → 2.5 m efectivo)

# Export
EXPORT_SCALE = 10      # m/px GeoTIFF
EXPORT_CRS   = "EPSG:32720"   # UTM 20S — Bolivia Santa Cruz
RENDER_DPI   = 220     # DPI render PNG

# Escala visual del Pol (%): rango FIJO (si VIZ_ADAPTIVE = False)
POL_MIN, POL_MAX = 8.0, 16.0
# Rango ADAPTATIVO por lote — usa percentiles p2–p98 (recomendado: True)
VIZ_ADAPTIVE  = True
VIZ_PCT_LOW   = 2
VIZ_PCT_HIGH  = 98
VIZ_MIN_RANGE = 0.6    # rango mínimo si el lote es muy homogéneo

# Paleta sacarosa: rojo (inmaduro) → amarillo → verde (maduro)
PALETA_POL = [
    "#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b",
    "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850", "#006837",
]

# Lotes a EXCLUIR (no son caña): monte, pista, soya, sorgo, teca
LOTES_EXCLUIR = {
    "MONTE", "monte4B1", "montelote6", "monte6d1", "monte6d2", "monte6e+6f",
    "MONTE_C1", "MONTE_lote6",
    "PISTA", "TECA",
    "J1_soya", "J2_soya", "J3-soya", "J4-soya", "J5-soya", "J6-soya",
    "M2-S", "M3-S", "LOTE_M1_-_S",
    "6SORGO",
}

# Si querés procesar SOLO algunos lotes, listalos acá (vacío = todos):
LOTES_FILTRO: set[str] = set()

# Branding Pixadvisor
VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")

# ════════════════════════════════════════════════════════════════════════════
# UTILIDADES BÁSICAS
# ════════════════════════════════════════════════════════════════════════════

def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def init_ee() -> None:
    """Inicializa Earth Engine. Pide autenticación si hace falta."""
    try:
        ee.Initialize()
    except Exception:
        try:
            ee.Authenticate()
            ee.Initialize()
        except Exception as e:
            log("ERROR Earth Engine: " + str(e))
            log("Ejecutá `earthengine authenticate` en una terminal y reintentá.")
            sys.exit(1)
    log("Earth Engine OK")


def force_2d(geom):
    """Quita la dimensión Z para evitar problemas en EE."""
    try:
        return shapely.force_2d(geom)
    except (AttributeError, TypeError):
        return shp_transform(lambda x, y, *_: (x, y), geom)


def safe_float(v, default=float("nan")):
    try:
        f = float(v)
        return f if not (f != f) else default  # NaN check
    except (TypeError, ValueError):
        return default


def fmt(v, dig=2):
    f = safe_float(v)
    return f"{f:.{dig}f}" if f == f else "—"  # NaN-safe


# ════════════════════════════════════════════════════════════════════════════
# DESCUBRIMIENTO DE LOTES
# ════════════════════════════════════════════════════════════════════════════

def descubrir_lotes(root: Path) -> list[dict]:
    """Recorre root y devuelve lista de dicts {lote_id, shp}."""
    lotes = []
    for shp in root.rglob(SHP_PATTERN):
        m = re.match(r"zonas_manejo_(.+)_PRO\.shp$", shp.name)
        if not m:
            continue
        lote_id = m.group(1)
        if lote_id in LOTES_EXCLUIR:
            continue
        if LOTES_FILTRO and lote_id not in LOTES_FILTRO:
            continue
        lotes.append({"lote_id": lote_id, "shp": shp})
    lotes.sort(key=lambda x: x["lote_id"])
    return lotes


def cargar_geometria_lote(shp_path: Path) -> tuple[gpd.GeoDataFrame, dict]:
    """
    Carga shapefile, disuelve zonas en un solo polígono (límite del lote)
    y reproyecta a WGS84 para Earth Engine.
    """
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        raise ValueError("shapefile vacío")

    crs_orig = gdf.crs
    if crs_orig is None:
        gdf.set_crs("EPSG:32720", inplace=True)  # asumir UTM 20S si falta

    # Quitar Z
    gdf["geometry"] = gdf.geometry.apply(force_2d)

    # Área antes de disolver (sumar zonas)
    area_ha = gdf.geometry.area.sum() / 10000.0
    n_zonas = len(gdf)

    # Disolver en un solo polígono = lote completo
    gdf_lote = gdf.dissolve()
    gdf_wgs84 = gdf_lote.to_crs("EPSG:4326")

    return gdf_lote, {
        "crs_orig": str(crs_orig),
        "gdf_wgs84": gdf_wgs84,
        "area_ha": area_ha,
        "n_zonas": n_zonas,
    }


# ════════════════════════════════════════════════════════════════════════════
# EARTH ENGINE — modelo Canata 2024 + búsqueda de imagen
# ════════════════════════════════════════════════════════════════════════════

def mask_scl(img):
    """Mantiene SCL 4 (veg), 5 (suelo desnudo), 6 (agua); descarta nubes/sombras."""
    scl = img.select("SCL")
    keep = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6))
    return img.updateMask(keep)


def scale_sr(img):
    """Convierte SR (0-10000) a reflectancia 0-1."""
    bands = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
    return (img.select(bands).divide(10000)
              .copyProperties(img, ["system:time_start", "system:index",
                                    "CLOUDY_PIXEL_PERCENTAGE"]))


def add_canata_2024(img):
    """Modelo Canata et al. (2024) — Pol y Brix."""
    b3  = img.select("B3")
    b8  = img.select("B8")
    b8a = img.select("B8A")
    b11 = img.select("B11")

    # NDWI Gao — agua foliar (correlación negativa con sacarosa)
    sum_ndwi = b8a.add(b11).max(1e-6)
    ndwi = b8a.subtract(b11).divide(sum_ndwi).rename("NDWI")

    # GNDVI — clorofila/senescencia
    sum_gndvi = b8.add(b3).max(1e-6)
    gndvi = b8.subtract(b3).divide(sum_gndvi).rename("GNDVI")

    pol = (ee.Image(8.93896)
           .subtract(ndwi.multiply(6.75543))
           .add(gndvi.multiply(2.69357))
           .add(b3.multiply(0.00003741))
           .rename("POL"))
    brix = (ee.Image(12.80412)
            .subtract(ndwi.multiply(5.27616))
            .add(gndvi.multiply(2.1931))
            .add(b3.multiply(0.00002903))
            .rename("BRIX"))

    return img.addBands([ndwi, gndvi, pol, brix])


def smooth_image(img, radius_px: int):
    """Suavizado Gaussiano server-side (anti-serrilhado)."""
    k = ee.Kernel.gaussian(radius=radius_px, sigma=radius_px / 2,
                           units="pixels", normalize=True)
    return img.convolve(k)


def buscar_mejor_s2(geom_ee, end_date_ee, dias: int, max_cloud: int,
                    min_cov: float):
    """Devuelve (image, info_dict) o (None, None)."""
    start = end_date_ee.advance(-dias, "day")

    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(geom_ee)
           .filterDate(start, end_date_ee)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
           .map(mask_scl)
           .map(scale_sr))

    def add_coverage(img):
        m = img.select("B4").mask()
        cov = m.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geom_ee, scale=20, maxPixels=int(1e9), bestEffort=True,
        ).get("B4")
        return img.set("VALID_COVERAGE", ee.Number(cov))

    col = (col.map(add_coverage)
              .filter(ee.Filter.gte("VALID_COVERAGE", min_cov))
              .sort("system:time_start", False))

    n = col.size().getInfo()
    if n == 0:
        return None, None

    img = ee.Image(col.first())
    info = img.toDictionary([
        "system:index", "system:time_start",
        "CLOUDY_PIXEL_PERCENTAGE", "VALID_COVERAGE",
    ]).getInfo()
    return img, info


def descargar_tif(img, geom_ee, scale: int, out_path: Path) -> bool:
    """Descarga GeoTIFF recortado al lote (proyección EXPORT_CRS)."""
    try:
        url = img.getDownloadURL({
            "scale": scale,
            "region": geom_ee,
            "format": "GEO_TIFF",
            "crs": EXPORT_CRS,
        })
    except Exception as e:
        log(f"  × getDownloadURL: {e}")
        return False

    try:
        r = requests.get(url, timeout=240)
    except Exception as e:
        log(f"  × HTTP error: {e}")
        return False

    if r.status_code != 200:
        log(f"  × HTTP {r.status_code}")
        return False

    out_path.write_bytes(r.content)
    return True


def stats_pol(img_pol_smooth, geom_ee) -> dict:
    """Estadísticas del Pol suavizado sobre el lote."""
    reducers = (ee.Reducer.mean()
                .combine(ee.Reducer.minMax(), "", True)
                .combine(ee.Reducer.stdDev(), "", True)
                .combine(ee.Reducer.percentile([10, 25, 50, 75, 90]), "", True))
    return img_pol_smooth.reduceRegion(
        reducer=reducers, geometry=geom_ee, scale=10,
        maxPixels=int(1e9), bestEffort=True,
    ).getInfo()


def stats_brix(img_brix_smooth, geom_ee) -> dict:
    return img_brix_smooth.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
        geometry=geom_ee, scale=10, maxPixels=int(1e9), bestEffort=True,
    ).getInfo()


# ════════════════════════════════════════════════════════════════════════════
# RENDER MAPA (matplotlib alta resolución, sin serrilhado)
# ════════════════════════════════════════════════════════════════════════════

CMAP_POL = LinearSegmentedColormap.from_list("pol", PALETA_POL, N=256)


def render_mapa(tif_pol: Path, gdf_lote: gpd.GeoDataFrame, lote_meta: dict,
                png_out: Path) -> None:
    """Mapa color profesional con upsample bicúbico + suavizado Gaussiano."""
    with rasterio.open(tif_pol) as src:
        arr = src.read(1).astype(float)
        nodata = src.nodata if src.nodata is not None else -9999
        arr = np.where((arr == nodata) | np.isnan(arr), np.nan, arr)
        l, b, r, t = src.bounds
        crs_raster = src.crs

    valid = arr[np.isfinite(arr)]
    if valid.size < 3:
        log("  (advertencia: pocos píxeles para render)")
        return

    # Rango de color: adaptativo (p2-p98) o fijo
    if VIZ_ADAPTIVE:
        vmin = float(np.percentile(valid, VIZ_PCT_LOW))
        vmax = float(np.percentile(valid, VIZ_PCT_HIGH))
        if vmax - vmin < VIZ_MIN_RANGE:
            vc = (vmin + vmax) / 2
            vmin = vc - VIZ_MIN_RANGE / 2
            vmax = vc + VIZ_MIN_RANGE / 2
    else:
        vmin, vmax = POL_MIN, POL_MAX

    # Upsample bicúbico preservando NaN (4x → 2.5 m efectivo desde 10 m)
    mask = np.isnan(arr)
    fill = float(np.nanmean(arr))
    arr_filled = np.where(mask, fill, arr)
    mask_f = mask.astype(float)

    factor = RESAMPLE_FACTOR
    if factor > 1:
        arr_up = zoom(arr_filled, factor, order=3, mode="nearest")
        mask_up = zoom(mask_f, factor, order=1, mode="nearest") > 0.5
    else:
        arr_up = arr_filled
        mask_up = mask

    # Suavizado Gaussiano (escala con factor de upsample)
    if SMOOTH_PX_LOCAL > 0:
        arr_up = gaussian_filter(arr_up, sigma=SMOOTH_PX_LOCAL * max(factor, 1))

    arr_up = np.where(mask_up, np.nan, arr_up)

    fig, ax = plt.subplots(figsize=(8.5, 8.0), dpi=RENDER_DPI)
    fig.patch.set_facecolor("white")

    im = ax.imshow(
        arr_up, cmap=CMAP_POL, vmin=vmin, vmax=vmax,
        extent=(l, r, b, t), interpolation="bicubic",
        origin="upper", aspect="equal",
    )

    # Borde del lote
    try:
        gdf_utm = gdf_lote.to_crs(crs_raster)
        gdf_utm.boundary.plot(ax=ax, color="black", linewidth=1.6, alpha=0.9)
    except Exception:
        pass

    ax.set_xlim(l, r)
    ax.set_ylim(b, t)
    ax.set_axis_off()

    ax.set_title(
        f"Madurez por Pol estimado — Lote {lote_meta['lote_id']}",
        fontsize=14, fontweight="bold", color="#1B5E20", pad=12,
    )

    p_mean = safe_float(lote_meta.get("POL_mean"))
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04, shrink=0.85,
                        ticks=np.linspace(vmin, vmax, 6))
    cbar.set_label(
        "Pol estimado (%)  —  rojo: menor madurez · verde: mayor madurez",
        fontsize=9,
    )
    cbar.ax.tick_params(labelsize=8)
    if p_mean == p_mean and vmin <= p_mean <= vmax:
        cbar.ax.axhline(p_mean, color="black", linewidth=1.5, alpha=0.85)

    mean_txt = f"Pol medio lote: {p_mean:.2f}%" if p_mean == p_mean else "Pol medio: —"
    plt.figtext(
        0.5, 0.015,
        f"Sentinel-2A {lote_meta.get('fecha_imagen','—')}  ·  "
        f"{mean_txt}  ·  Modelo Canata 2024  ·  Pixadvisor AP",
        ha="center", fontsize=8, color="#555555",
    )

    fig.tight_layout()
    fig.savefig(png_out, dpi=RENDER_DPI, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# PDF — branding Pixadvisor (REPORTE DE DIAGNÓSTICO)
# ════════════════════════════════════════════════════════════════════════════

def interp_pol(p):
    f = safe_float(p)
    if f != f:
        return "Sin datos"
    if f < 11:  return "Inmaduro — esperar"
    if f < 13:  return "Maduración temprana"
    if f < 15:  return "Maduración avanzada"
    return "Maduración plena — cosechar"


def interp_desvio(s):
    f = safe_float(s)
    if f != f:
        return "Sin datos"
    if f < 0.5: return "Lote homogéneo"
    if f < 1.0: return "Variabilidad moderada"
    return "Lote heterogéneo — considerar cosecha zonificada"


def generar_pdf(lote_meta: dict, png_mapa: Path, pdf_out: Path) -> None:
    """Reporte PDF de una página con branding Pixadvisor."""
    doc = SimpleDocTemplate(
        str(pdf_out), pagesize=A4,
        topMargin=15 * mm, bottomMargin=18 * mm,
        leftMargin=18 * mm, rightMargin=18 * mm,
        title=f"Sacarosa Lote {lote_meta['lote_id']}",
        author="Pixadvisor AP",
    )

    styles = getSampleStyleSheet()
    s_title = ParagraphStyle(
        "PixTitle", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=2, leading=20,
    )
    s_subtitle = ParagraphStyle(
        "PixSub", parent=styles["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13,
    )
    s_h2 = ParagraphStyle(
        "PixH2", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=11, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=13,
    )
    s_body = ParagraphStyle(
        "PixBody", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS, leading=12,
    )

    story = []

    # Header
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión",
                  s_subtitle),
        Paragraph(
            f"<para align=right>Reporte de Madurez<br/>"
            f"{datetime.now():%Y-%m-%d}</para>", s_subtitle),
    ]]
    h_tbl = Table(header, colWidths=[100 * mm, 70 * mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, VERDE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(h_tbl)
    story.append(Spacer(1, 6))

    # Título
    story.append(Paragraph(
        f"Mapa de Madurez — Lote {lote_meta['lote_id']}", s_title))
    story.append(Paragraph(
        f"Sentinel-2A · imagen del <b>{lote_meta.get('fecha_imagen','—')}</b>"
        f" · Modelo Canata 2024 (Pol estimado)", s_subtitle))
    story.append(Spacer(1, 6))

    # Stats
    p_mean = lote_meta.get("POL_mean")
    p_min  = lote_meta.get("POL_min")
    p_max  = lote_meta.get("POL_max")
    p_std  = lote_meta.get("POL_stdDev")
    p_p25  = lote_meta.get("POL_p25")
    p_p75  = lote_meta.get("POL_p75")
    b_mean = lote_meta.get("BRIX_mean")

    info_data = [
        ["ID Lote",          str(lote_meta["lote_id"])],
        ["Área",             f"{lote_meta.get('area_ha', 0):.2f} ha"],
        ["Zonas de manejo",  str(lote_meta.get("n_zonas", "—"))],
        ["Imagen S2A",       str(lote_meta.get("imagen_id", "—"))[:24]],
        ["Fecha imagen",     str(lote_meta.get("fecha_imagen", "—"))],
        ["Nubosidad escena", f"{safe_float(lote_meta.get('cloud_pct'), 0):.1f}%"],
        ["Cobertura útil",
         f"{safe_float(lote_meta.get('valid_coverage'), 0) * 100:.0f}%"],
    ]
    stat_data = [
        ["Pol medio",   fmt(p_mean), "%"],
        ["Pol mínimo",  fmt(p_min),  "%"],
        ["Pol máximo",  fmt(p_max),  "%"],
        ["Desvío Pol",  fmt(p_std),  "%"],
        ["P25 Pol",     fmt(p_p25),  "%"],
        ["P75 Pol",     fmt(p_p75),  "%"],
        ["Brix medio",  fmt(b_mean), "°"],
    ]

    t_info = Table(info_data, colWidths=[33 * mm, 50 * mm])
    t_info.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
    ]))

    t_stat = Table(stat_data, colWidths=[28 * mm, 25 * mm, 8 * mm])
    t_stat.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 8),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
    ]))

    side = Table([[t_info, t_stat]], colWidths=[85 * mm, 65 * mm])
    side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(side)
    story.append(Spacer(1, 6))

    # Mapa
    img = RLImage(str(png_mapa), width=165 * mm, height=120 * mm,
                  kind="proportional")
    img.hAlign = "CENTER"
    story.append(img)
    story.append(Spacer(1, 2))

    # Diagnóstico
    story.append(Paragraph("Diagnóstico", s_h2))
    diag = (f"<b>Estado:</b> {interp_pol(p_mean)}.&nbsp;&nbsp;"
            f"<b>Homogeneidad:</b> {interp_desvio(p_std)}.")
    story.append(Paragraph(diag, s_body))

    # Recomendación
    story.append(Paragraph("Recomendación de cosecha", s_h2))
    p_std_f  = safe_float(p_std)
    p_mean_f = safe_float(p_mean)
    p_p75_f  = safe_float(p_p75)
    if p_std_f == p_std_f and p_std_f > 1.0 and p_p75_f == p_p75_f:
        rec = (f"Existe variabilidad espacial significativa en el lote. "
               f"Cosechar primero las zonas con <b>Pol &gt; "
               f"{p_p75_f:.1f}%</b> (zonas verdes en el mapa). "
               f"Las zonas rojas requieren mayor tiempo de maduración.")
    elif p_mean_f == p_mean_f and p_mean_f >= 13:
        rec = ("La maduración es uniforme y se encuentra en rango de cosecha. "
               "<b>Cosechar el lote completo.</b>")
    elif p_mean_f != p_mean_f:
        rec = ("Sin datos suficientes — verificar que la imagen S2 "
               "tenga cobertura útil sobre el lote.")
    else:
        rec = ("La maduración aún no alcanzó el umbral comercial. "
               "<b>Postergar cosecha</b> y reevaluar en 15-30 días con "
               "una nueva imagen Sentinel-2.")
    story.append(Paragraph(rec, s_body))

    # Limitaciones
    story.append(Paragraph("Limitaciones del modelo", s_h2))
    lim = ("Estimación derivada de regresión lineal Canata et al. (2024) "
           "calibrada en Brasil con UAV multiespectral y trasladada a "
           "Sentinel-2 SR. R² esperable absoluto: 0.55-0.70. <b>El mapa "
           "es principalmente RELATIVO</b>: zonas más verdes indican "
           "mayor madurez. Para Pol absoluto industrial se requiere "
           "calibración local con &gt;30 muestras CONSECANA-equivalente.")
    story.append(Paragraph(lim, s_body))

    # Footer
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            f"Pixadvisor AP · Hacienda del Señor · "
            f"Lote {lote_meta['lote_id']} · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}",
        )
        canvas.setStrokeColor(VERDE)
        canvas.setLineWidth(0.4)
        canvas.line(18 * mm, 13 * mm, A4[0] - 18 * mm, 13 * mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


# ════════════════════════════════════════════════════════════════════════════
# PROCESAMIENTO POR LOTE
# ════════════════════════════════════════════════════════════════════════════

def procesar_lote(lote: dict, end_date_ee, idx: int, total: int) -> dict | None:
    lote_id = lote["lote_id"]
    log(f"[{idx}/{total}] Lote {lote_id}")

    out_dir = OUTPUT_ROOT / lote_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Geometría
    try:
        gdf_lote, meta_geom = cargar_geometria_lote(lote["shp"])
    except Exception as e:
        log(f"  × geometría: {e}")
        return None

    geom_wgs = meta_geom["gdf_wgs84"].geometry.iloc[0]
    geom_ee = ee.Geometry(geom_wgs.__geo_interface__)

    # Imagen
    img, info = buscar_mejor_s2(geom_ee, end_date_ee, DIAS_ATRAS,
                                 NUBES_MAX, COBERTURA_MIN)
    if img is None:
        log(f"  × sin imagen S2 válida en últimos {DIAS_ATRAS} días")
        return {
            "lote_id": lote_id,
            "fecha_imagen": "sin_imagen",
            "area_ha": meta_geom["area_ha"],
            "n_zonas": meta_geom["n_zonas"],
        }

    fecha_ms = info["system:time_start"]
    fecha_str = datetime.fromtimestamp(
        fecha_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    log(f"  → S2A {fecha_str}  cob={info['VALID_COVERAGE']:.0%}  "
        f"nubes={info['CLOUDY_PIXEL_PERCENTAGE']:.0f}%")

    # Índices + suavizado
    idx_img = add_canata_2024(img)
    pol_smooth  = smooth_image(idx_img.select("POL"),  SMOOTH_PX_GEE).clip(geom_ee)
    brix_smooth = smooth_image(idx_img.select("BRIX"), SMOOTH_PX_GEE).clip(geom_ee)

    # Descargas
    tif_pol  = out_dir / f"POL_{lote_id}_{fecha_str}.tif"
    tif_brix = out_dir / f"BRIX_{lote_id}_{fecha_str}.tif"

    if not descargar_tif(pol_smooth.toFloat(), geom_ee, EXPORT_SCALE, tif_pol):
        log("  × no pude descargar POL.tif")
        return None
    descargar_tif(brix_smooth.toFloat(), geom_ee, EXPORT_SCALE, tif_brix)

    # Stats
    sp = stats_pol(pol_smooth, geom_ee)
    sb = stats_brix(brix_smooth, geom_ee)

    lote_meta = {
        "lote_id": lote_id,
        "area_ha": meta_geom["area_ha"],
        "n_zonas": meta_geom["n_zonas"],
        "imagen_id": info.get("system:index", "—"),
        "fecha_imagen": fecha_str,
        "cloud_pct": info.get("CLOUDY_PIXEL_PERCENTAGE", -1),
        "valid_coverage": info.get("VALID_COVERAGE", 0),
        **sp,    # POL_mean, POL_min, POL_max, POL_stdDev, POL_p10..p90
        **sb,    # BRIX_mean, BRIX_min, BRIX_max
    }

    # Render mapa
    png_mapa = out_dir / f"mapa_{lote_id}.png"
    try:
        render_mapa(tif_pol, gdf_lote, lote_meta, png_mapa)
    except Exception as e:
        log(f"  × render: {e}")
        return lote_meta

    # PDF
    pdf_out = out_dir / f"PIX_Sacarosa_{lote_id}_{fecha_str}.pdf"
    try:
        generar_pdf(lote_meta, png_mapa, pdf_out)
        if pdf_out.exists() and pdf_out.stat().st_size > 0:
            log(f"  ✓ {pdf_out.name}")
        else:
            log("  × PDF vacío")
    except Exception as e:
        log(f"  × PDF: {e}")

    return lote_meta


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    log("═══════════════════════════════════════════════")
    log("PIXADVISOR — Sacarosa Caña — Sentinel-2A")
    log("Hacienda del Señor — Modelo Canata 2024")
    log("═══════════════════════════════════════════════")

    if not LOTES_ROOT.exists():
        log(f"ERROR: no existe {LOTES_ROOT}")
        sys.exit(1)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    init_ee()

    lotes = descubrir_lotes(LOTES_ROOT)
    log(f"Lotes detectados (caña): {len(lotes)}")
    if LOTES_FILTRO:
        log(f"  filtro activo: {sorted(LOTES_FILTRO)}")
    log(f"  excluidos (no-caña): {len(LOTES_EXCLUIR)}")

    if not lotes:
        log("Nada para procesar.")
        return

    end_date_ee = ee.Date(int(datetime.now(timezone.utc).timestamp() * 1000))

    resultados = []
    t0 = time.time()
    for i, lote in enumerate(lotes, 1):
        try:
            r = procesar_lote(lote, end_date_ee, i, len(lotes))
            if r:
                resultados.append(r)
        except KeyboardInterrupt:
            log("⚠ Interrumpido por usuario")
            break
        except Exception as e:
            log(f"  × ERROR lote {lote['lote_id']}: {e}")

    # CSV resumen
    if resultados:
        df = pd.DataFrame(resultados)
        # Orden de columnas amigable
        cols_first = ["lote_id", "fecha_imagen", "area_ha", "n_zonas",
                      "valid_coverage", "cloud_pct",
                      "POL_mean", "POL_min", "POL_max", "POL_stdDev",
                      "POL_p25", "POL_p50", "POL_p75",
                      "BRIX_mean", "imagen_id"]
        cols_first = [c for c in cols_first if c in df.columns]
        cols_rest = [c for c in df.columns if c not in cols_first]
        df = df[cols_first + cols_rest]

        csv_path = OUTPUT_ROOT / f"pix_sacarosa_index_{datetime.now():%Y-%m-%d}.csv"
        df.to_csv(csv_path, index=False)
        log(f"CSV resumen → {csv_path.name}")

    elapsed = (time.time() - t0) / 60
    log(f"Listo: {len(resultados)} lotes procesados en {elapsed:.1f} min.")
    log(f"Salidas en: {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
