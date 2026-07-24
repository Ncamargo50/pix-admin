#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — GeoPDF para Avenza Maps (sin GDAL)
============================================================================
Genera PDF georreferenciado estándar OGC GeoPDF para los Top 20 lotes.
Compatible con Avenza Maps (gratis), QGIS, GlobalMapper, ArcGIS.

Implementación pura Python:
  1. Descarga imagen S2 RGB del lote (GEE)
  2. Renderiza overlay (borde lote + 5 puntos GPS) con PIL
  3. Genera PDF con reportlab (imagen + título + GPS table + leyenda)
  4. Post-procesa con pypdf para agregar GeoPDF metadata OGC:
     - Viewport dictionary con BBox en page coords
     - Measure dictionary con GCS WGS84
     - GPTS (lat/lon de las 4 esquinas)
     - LPTS (puntos lógicos en viewport normalizado)

Resultado: PDF que Avenza Maps abre con georreferenciación,
mostrando ubicación GPS en tiempo real sobre la imagen del lote.
============================================================================
"""
from __future__ import annotations
import sys
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import geopandas as gpd
import shapely
from shapely.ops import transform as shp_transform
import rasterio

from PIL import Image, ImageDraw, ImageFont

import ee

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    DictionaryObject, ArrayObject, NameObject,
    FloatObject, NumberObject, TextStringObject,
)

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage,
                                 PageBreak, KeepTogether)
from reportlab.pdfgen import canvas as pdfcanvas

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
SAMPL_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\05-Muestreo-InSitu-Top20")
CSV_RANK    = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
                   r"\ranking_prioridad_v3_S2_S1_2026-05-15.csv")

N_TOP = 20
BUFFER_LOTE_M = 60   # menos buffer = más zoom al lote
GEOTIFF_SCALE = 2    # m/pixel S2 RGB upsampled (más detalle = mejor zoom)

# Layout PDF (A4 landscape)
PAGE_W, PAGE_H = landscape(A4)  # 842 x 595 puntos
MARGIN = 28   # 28 puntos = 10 mm

VERDE       = HexColor("#1B5E20")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


def init_ee():
    try: ee.Initialize()
    except Exception: ee.Authenticate(); ee.Initialize()


def cargar_geom(lote_id: str):
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    return gdf.dissolve()


# ════════════════════════════════════════════════════════════════════════════
# 1) DESCARGA S2 RGB
# ════════════════════════════════════════════════════════════════════════════
def descargar_s2_rgb(geom_utm, dias_atras=30):
    bounds_utm = geom_utm.bounds
    minx, miny, maxx, maxy = bounds_utm
    bx = maxx - minx; by = maxy - miny
    buf = max(BUFFER_LOTE_M, max(bx, by) * 0.10)
    minx -= buf; miny -= buf; maxx += buf; maxy += buf

    geom_buf_utm = shapely.geometry.box(minx, miny, maxx, maxy)
    geom_buf_wgs = gpd.GeoSeries([geom_buf_utm], crs="EPSG:32720"
                                  ).to_crs("EPSG:4326").iloc[0]
    region_ee = ee.Geometry(geom_buf_wgs.__geo_interface__)

    end = ee.Date(int(datetime.now().timestamp()*1000))
    start = end.advance(-dias_atras, "day")
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterBounds(region_ee)
           .filterDate(start, end)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
           .sort("system:time_start", False))
    if col.size().getInfo() == 0:
        return None, None, None, None

    img = ee.Image(col.first()).select(["B4","B3","B2"]).divide(10000)
    fecha_ms = ee.Image(col.first()).get("system:time_start").getInfo()
    fecha_str = datetime.fromtimestamp(fecha_ms/1000).strftime("%Y-%m-%d")

    rgb_vis = img.visualize(min=0.0, max=0.3, bands=["B4","B3","B2"])
    url = rgb_vis.getDownloadURL({
        "scale": GEOTIFF_SCALE,
        "region": region_ee,
        "format": "GEO_TIFF",
        "crs": "EPSG:32720"})
    r = requests.get(url, timeout=180)
    if r.status_code != 200:
        return None, None, None, None

    with rasterio.io.MemoryFile(r.content) as mf:
        with mf.open() as src:
            arr = src.read()
            transform = src.transform
            crs = src.crs
            bounds = src.bounds  # (left, bottom, right, top) en UTM
    return arr, transform, crs, fecha_str, bounds


# ════════════════════════════════════════════════════════════════════════════
# 2) OVERLAY PIL (borde + puntos)
# ════════════════════════════════════════════════════════════════════════════
def overlay_lote_y_puntos(arr_rgb, transform, lote_geom_utm,
                            puntos_utm, lote_id, fecha_s2, rank):
    """Overlay profesional para navegación GPS:
       - Borde lote: línea cyan fina (mejor contraste sobre verde cultivo)
       - Waypoints: crosshair topográfico pequeño + label al lado
       Diseñado para zoom alto en Avenza Maps móvil."""
    img_pil = Image.fromarray(np.transpose(arr_rgb, (1,2,0)).astype(np.uint8))
    draw = ImageDraw.Draw(img_pil, "RGBA")

    def utm_to_pixel(x, y):
        col = (x - transform.c) / transform.a
        row = (y - transform.f) / transform.e
        return col, row

    # ─── Borde lote: línea cyan brillante 2px sobre línea negra 1px (halo)
    geoms = [lote_geom_utm] if lote_geom_utm.geom_type == "Polygon" else list(lote_geom_utm.geoms)
    for g in geoms:
        coords = list(g.exterior.coords)
        pixs = [utm_to_pixel(x, y) for x, y in coords]
        # Halo negro fino
        draw.line(pixs, fill=(0, 0, 0, 200), width=3)
        # Cyan brillante encima
        draw.line(pixs, fill=(0, 255, 255, 255), width=1)

    # ─── Waypoints estilo topográfico GPS (pequeños, precisos)
    try:
        font = ImageFont.truetype("arialbd.ttf", 11)
    except Exception:
        font = ImageFont.load_default()

    for _, p in puntos_utm.iterrows():
        cx, cy = utm_to_pixel(p.geometry.x, p.geometry.y)
        cx, cy = int(cx), int(cy)

        # 1) Crosshair fino blanco (halo) + rojo
        L = 8  # largo de cada brazo del crosshair
        # Halo blanco grueso
        draw.line([cx-L, cy, cx+L, cy], fill=(255,255,255,255), width=3)
        draw.line([cx, cy-L, cx, cy+L], fill=(255,255,255,255), width=3)
        # Rojo encima fino
        draw.line([cx-L, cy, cx+L, cy], fill=(255,0,0,255), width=1)
        draw.line([cx, cy-L, cx, cy+L], fill=(255,0,0,255), width=1)

        # 2) Punto central pequeño (4 px)
        draw.ellipse([cx-2, cy-2, cx+2, cy+2],
                      fill=(255,0,0,255), outline=(255,255,255,255), width=1)

        # 3) Etiqueta "P1" al costado superior-derecho (no encima)
        txt = f"P{int(p['punto_n'])}"
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        # Posición del label: arriba-derecha del crosshair
        lx = cx + 10
        ly = cy - 10 - th
        # Fondo blanco semi-transparente legible
        pad = 2
        draw.rectangle([lx-pad, ly-pad, lx+tw+pad, ly+th+pad],
                        fill=(255,255,255,220), outline=(0,0,0,255), width=1)
        draw.text((lx, ly), txt, fill=(180,0,0,255), font=font)

    return img_pil


# ════════════════════════════════════════════════════════════════════════════
# 3) GENERAR PDF BASE con ReportLab + recordar bbox imagen en page coords
# ════════════════════════════════════════════════════════════════════════════
def generar_pdf_base(meta: dict, img_pil: Image.Image, puntos_wgs: gpd.GeoDataFrame,
                      pdf_out: Path, fecha_s2: str):
    """Genera PDF con imagen del lote + título + tabla GPS.
    Retorna el bbox en page coords (puntos PDF) donde está la imagen."""

    # Calcular dimensiones imagen para que entre en página landscape
    # Layout: imagen al centro/izquierda, tabla GPS + título a la derecha
    img_w_pix, img_h_pix = img_pil.size
    aspect = img_w_pix / img_h_pix

    # Área disponible para imagen
    panel_right_w = 200  # ancho panel derecho (texto/tabla GPS)
    img_area_w = PAGE_W - 2*MARGIN - panel_right_w - 10
    img_area_h = PAGE_H - 2*MARGIN - 60  # 60 para título arriba

    # Dim final imagen
    if img_area_w / aspect <= img_area_h:
        img_pdf_w = img_area_w
        img_pdf_h = img_area_w / aspect
    else:
        img_pdf_h = img_area_h
        img_pdf_w = img_area_h * aspect

    # Coords imagen en page (origen lower-left en PDF)
    img_x0 = MARGIN
    img_y0 = MARGIN
    img_x1 = img_x0 + img_pdf_w
    img_y1 = img_y0 + img_pdf_h

    # Crear canvas reportlab
    c = pdfcanvas.Canvas(str(pdf_out), pagesize=(PAGE_W, PAGE_H))
    c.setTitle(f"Pixadvisor GeoPDF Lote {meta['lote_id']}")
    c.setAuthor("Pixadvisor AP")

    # Header verde
    c.setFillColor(VERDE)
    c.setStrokeColor(VERDE)
    c.setLineWidth(1.5)
    c.line(MARGIN, PAGE_H - MARGIN - 24, PAGE_W - MARGIN, PAGE_H - MARGIN - 24)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, PAGE_H - MARGIN - 12, "PIXADVISOR")
    c.setFont("Helvetica", 9)
    c.setFillColor(GRIS)
    c.drawString(MARGIN, PAGE_H - MARGIN - 22, "Agricultura de Precisión")

    c.setFont("Helvetica", 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN - 12,
                       f"GeoPDF Avenza Maps · {datetime.now():%Y-%m-%d}")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN - 22,
                       "Hacienda del Señor")

    # Título lote
    rank = int(meta.get("Rank_v3", 0))
    c.setFillColor(VERDE)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGIN, PAGE_H - MARGIN - 45,
                  f"Lote {meta['lote_id']} — Rank #{rank} prioridad cosecha")
    c.setFillColor(GRIS)
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN, PAGE_H - MARGIN - 58,
                  f"Área: {meta.get('area_ha',0):.2f} ha  ·  "
                  f"Estado: {meta.get('Estado_fenologico_v3','—')}  ·  "
                  f"S2A: {fecha_s2}")

    # Insertar imagen
    img_buf = BytesIO()
    img_pil.save(img_buf, format="PNG")
    img_buf.seek(0)
    from reportlab.lib.utils import ImageReader
    img_reader = ImageReader(img_buf)
    c.drawImage(img_reader, img_x0, img_y0, width=img_pdf_w, height=img_pdf_h,
                 mask=None)

    # Marco
    c.setStrokeColor(black)
    c.setLineWidth(1)
    c.rect(img_x0, img_y0, img_pdf_w, img_pdf_h, fill=0, stroke=1)

    # Panel derecho: tabla GPS + leyenda + protocolo breve
    panel_x = img_x1 + 12
    panel_y = PAGE_H - MARGIN - 80

    c.setFillColor(VERDE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(panel_x, panel_y, "PUNTOS GPS")
    panel_y -= 14

    # Header tabla
    c.setFillColor(VERDE)
    c.rect(panel_x, panel_y - 12, 190, 14, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(panel_x + 4, panel_y - 9, "Punto")
    c.drawString(panel_x + 50, panel_y - 9, "Latitud")
    c.drawString(panel_x + 120, panel_y - 9, "Longitud")
    panel_y -= 14

    c.setFillColor(GRIS)
    c.setFont("Helvetica", 8)
    for i, (_, p) in enumerate(puntos_wgs.iterrows()):
        if i % 2 == 1:
            c.setFillColor(GRIS_CLARO)
            c.rect(panel_x, panel_y - 12, 190, 12, fill=1, stroke=0)
            c.setFillColor(GRIS)
        c.drawString(panel_x + 4, panel_y - 9, f"P{int(p['punto_n'])}")
        c.drawString(panel_x + 50, panel_y - 9, f"{p['lat']:.6f}")
        c.drawString(panel_x + 120, panel_y - 9, f"{p['lon']:.6f}")
        panel_y -= 12

    panel_y -= 14

    # Leyenda
    c.setFillColor(VERDE)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(panel_x, panel_y, "LEYENDA")
    panel_y -= 14

    c.setFillColor((1.0, 1.0, 0.0))
    c.rect(panel_x, panel_y - 5, 12, 4, fill=1, stroke=1)
    c.setFillColor(GRIS); c.setFont("Helvetica", 8)
    c.drawString(panel_x + 16, panel_y - 4, "Borde del lote")
    panel_y -= 14

    c.setFillColor((1.0, 0.0, 0.0))
    c.circle(panel_x + 6, panel_y - 4, 5, fill=1, stroke=1)
    c.setFillColor(GRIS)
    c.drawString(panel_x + 16, panel_y - 4, "Punto de muestreo (1-5)")
    panel_y -= 18

    # Protocolo breve
    c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 11)
    c.drawString(panel_x, panel_y, "PROTOCOLO")
    panel_y -= 12

    c.setFillColor(GRIS); c.setFont("Helvetica", 8)
    protocol_lines = [
        "Por cada uno de los 5 puntos:",
        "• 10 tallos representativos",
        "• Brix sup (BS) entrenudo 3 ápice",
        "• Brix inf (BI) entrenudo 3 base",
        "• CMI = (BS/BI) × 100",
        "",
        "CMI ≥ 85% → COSECHAR 7-14 días",
        "75-85% → esperar 2-3 semanas",
        "< 75% → esperar 4 semanas",
    ]
    for line in protocol_lines:
        c.drawString(panel_x, panel_y, line)
        panel_y -= 11

    # Footer
    c.setFillColor(GRIS); c.setFont("Helvetica", 7)
    c.drawCentredString(PAGE_W/2, MARGIN/2,
        f"Pixadvisor AP · GeoPDF Avenza · Lote {meta['lote_id']} · "
        f"{datetime.now():%Y-%m-%d}  ·  Coordenadas WGS84 (EPSG:4326)")

    c.save()
    return (img_x0, img_y0, img_x1, img_y1)


# ════════════════════════════════════════════════════════════════════════════
# 4) AGREGAR GeoPDF metadata OGC con pypdf (Avenza-compatible)
# ════════════════════════════════════════════════════════════════════════════
def agregar_geopdf_metadata(pdf_path: Path, image_bbox_pdf: tuple,
                              geo_bounds_utm: tuple, utm_zone: int = 20,
                              hemisphere: str = "S"):
    """
    Agrega metadata GeoPDF estándar OGC a la página.

    image_bbox_pdf: (x0, y0, x1, y1) en puntos PDF (page coords, lower-left origin)
    geo_bounds_utm: (left, bottom, right, top) en UTM 20S (EPSG:32720)
    """
    # Convertir UTM 20S a WGS84 lat/lon usando geopandas
    minx, miny, maxx, maxy = geo_bounds_utm
    corners_utm = gpd.GeoSeries(
        [shapely.geometry.Point(minx, miny),  # bottom-left
         shapely.geometry.Point(minx, maxy),  # top-left
         shapely.geometry.Point(maxx, maxy),  # top-right
         shapely.geometry.Point(maxx, miny)], # bottom-right
        crs=f"EPSG:327{utm_zone}")
    corners_wgs = corners_utm.to_crs("EPSG:4326")

    # GPTS = lat,lon en orden BL, TL, TR, BR (8 floats)
    gpts = []
    for pt in corners_wgs:
        gpts.append(FloatObject(pt.y))  # lat
        gpts.append(FloatObject(pt.x))  # lon

    # Bounds = page-relative (0-1), 8 floats: BL, TL, TR, BR
    bounds = ArrayObject([
        NumberObject(0), NumberObject(0),
        NumberObject(0), NumberObject(1),
        NumberObject(1), NumberObject(1),
        NumberObject(1), NumberObject(0),
    ])

    # LPTS = posiciones lógicas en bbox normalizado (mismo que Bounds)
    lpts = ArrayObject([
        NumberObject(0), NumberObject(0),
        NumberObject(0), NumberObject(1),
        NumberObject(1), NumberObject(1),
        NumberObject(1), NumberObject(0),
    ])

    # GCS — Geographic Coordinate System WGS84
    gcs = DictionaryObject({
        NameObject("/Type"): NameObject("/PROJCS"),
        NameObject("/EPSG"): NumberObject(4326),
        NameObject("/WKT"): TextStringObject(
            'GEOGCS["WGS 84",DATUM["WGS_1984",'
            'SPHEROID["WGS 84",6378137,298.257223563,'
            'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],'
            'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
            'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
            'AUTHORITY["EPSG","4326"]]'
        ),
    })

    # Measure dictionary
    measure = DictionaryObject({
        NameObject("/Type"): NameObject("/Measure"),
        NameObject("/Subtype"): NameObject("/GEO"),
        NameObject("/Bounds"): bounds,
        NameObject("/GPTS"): ArrayObject(gpts),
        NameObject("/LPTS"): lpts,
        NameObject("/GCS"): gcs,
    })

    # Viewport dictionary — define el área georreferenciada en page coords
    viewport = DictionaryObject({
        NameObject("/Type"): NameObject("/Viewport"),
        NameObject("/BBox"): ArrayObject([
            FloatObject(image_bbox_pdf[0]),
            FloatObject(image_bbox_pdf[1]),
            FloatObject(image_bbox_pdf[2]),
            FloatObject(image_bbox_pdf[3]),
        ]),
        NameObject("/Name"): TextStringObject("Pixadvisor Map"),
        NameObject("/Measure"): measure,
    })

    # Leer PDF, agregar VP a la página, escribir
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter(clone_from=reader)
    page = writer.pages[0]
    page[NameObject("/VP")] = ArrayObject([viewport])

    tmp_path = pdf_path.with_suffix(".geo.pdf")
    with open(tmp_path, "wb") as f:
        writer.write(f)
    # Reemplazar archivo original
    os.replace(tmp_path, pdf_path)


# ════════════════════════════════════════════════════════════════════════════
# 5) PROCESAR UN LOTE
# ════════════════════════════════════════════════════════════════════════════
def procesar_lote_geopdf(meta: dict, out_dir: Path) -> bool:
    lote_id = str(meta["lote_id"])
    rank = int(meta["Rank_v3"])
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        gdf_lote = cargar_geom(lote_id)

        # Cargar puntos
        shp_pts = SAMPL_ROOT / f"{rank:02d}_{lote_id}" / f"puntos_muestreo_{lote_id}.shp"
        if not shp_pts.exists():
            log(f"  ! sin puntos: {shp_pts}"); return False
        puntos_utm = gpd.read_file(shp_pts)
        if puntos_utm.crs is None: puntos_utm.set_crs("EPSG:32720", inplace=True)
        puntos_wgs = puntos_utm.to_crs("EPSG:4326").copy()
        puntos_wgs["lat"] = puntos_wgs.geometry.y
        puntos_wgs["lon"] = puntos_wgs.geometry.x

        # S2 RGB
        result = descargar_s2_rgb(gdf_lote.geometry.iloc[0])
        if result[0] is None:
            log(f"  ! sin S2"); return False
        arr, transform, crs, fecha_s2, bounds_utm = result

        # Overlay
        img_pil = overlay_lote_y_puntos(arr, transform,
                                         gdf_lote.geometry.iloc[0],
                                         puntos_utm, lote_id, fecha_s2, rank)

        # PDF base
        pdf_out = out_dir / f"GEOPDF_{rank:02d}_{lote_id}.pdf"
        meta_with_fecha = {**meta, "fecha_s2": fecha_s2}
        image_bbox_pdf = generar_pdf_base(meta_with_fecha, img_pil,
                                            puntos_wgs, pdf_out, fecha_s2)

        # GeoPDF metadata
        agregar_geopdf_metadata(pdf_out, image_bbox_pdf,
                                  bounds_utm, utm_zone=20, hemisphere="S")
        log(f"  ✓ {pdf_out.name}")
        return True
    except Exception as e:
        log(f"  × {e}")
        import traceback; traceback.print_exc()
        return False


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — GeoPDF Avenza Maps (puro Python, sin GDAL) ══")
    if not CSV_RANK.exists():
        log(f"ERROR: falta {CSV_RANK}"); sys.exit(1)
    init_ee()

    df = pd.read_csv(CSV_RANK)
    df["lote_id"] = df["lote_id"].astype(str)
    top20 = df.sort_values("Rank_v3").head(N_TOP).reset_index(drop=True)

    out_dir = SAMPL_ROOT / "GEOPDF_AVENZA"
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for i, (_, r) in enumerate(top20.iterrows(), 1):
        log(f"[{i}/{N_TOP}] Lote {r['lote_id']}")
        if procesar_lote_geopdf(r.to_dict(), out_dir):
            ok += 1

    log(f"OK — {ok}/{N_TOP} GeoPDFs generados en {out_dir}")
    log("Cargar en Avenza Maps: ➕ → Import from device → seleccionar GEOPDF_##_LOTE.pdf")


if __name__ == "__main__":
    main()
