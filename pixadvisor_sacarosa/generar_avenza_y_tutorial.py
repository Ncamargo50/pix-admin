#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — GeoTIFF Avenza Maps + KMZ + Tutorial PDF
============================================================================
Genera para los Top 20 lotes:
  1) GeoTIFF georreferenciado por lote con RGB Sentinel-2 + borde lote +
     5 puntos GPS (compatible Avenza Maps Pro, QGIS, ArcGIS)
  2) GeoTIFF global de la hacienda Top 20 (un solo archivo navegable)
  3) KMZ universal con polígonos + puntos (Avenza free, Google Earth,
     Garmin, BackcountryNav, Locus Map)
  4) Tutorial PDF imprimible (8 págs) con protocolo paso a paso

Avenza Maps Pro acepta GeoTIFF nativo. Para GeoPDF estricto requiere GDAL
(instalar via conda: `conda install -c conda-forge gdal` y luego
`gdal_translate -of PDF input.tif output.pdf`).
============================================================================
"""
from __future__ import annotations
import sys
import zipfile
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
from rasterio.transform import from_bounds
from rasterio.crs import CRS

from PIL import Image, ImageDraw, ImageFont

import matplotlib
matplotlib.use("Agg")

import ee

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage,
                                 PageBreak, KeepTogether)

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
BUFFER_LOTE_M = 60    # zoom alto al lote
GEOTIFF_SCALE = 2     # m/pixel S2 RGB upsampled (más detalle)

VERDE       = HexColor("#1B5E20")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")
NARANJA     = HexColor("#EF6C00")
AMARILLO    = HexColor("#F9A825")
AZUL        = HexColor("#1565C0")

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
            "agosto","septiembre","octubre","noviembre","diciembre"]


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
# 1) DESCARGA S2 RGB TRUE COLOR como bytes
# ════════════════════════════════════════════════════════════════════════════
def descargar_s2_rgb(geom_utm, dias_atras=30):
    """Devuelve (rgb_array Hx Wx 3 uint8, transform, crs) del último S2 RGB."""
    bounds_utm = geom_utm.bounds  # (minx, miny, maxx, maxy)
    # Buffer
    minx, miny, maxx, maxy = bounds_utm
    bx = maxx - minx; by = maxy - miny
    buf = max(BUFFER_LOTE_M, max(bx, by) * 0.10)
    minx -= buf; miny -= buf; maxx += buf; maxy += buf

    geom_buf_utm = shapely.geometry.box(minx, miny, maxx, maxy)
    geom_buf_wgs = gpd.GeoSeries([geom_buf_utm], crs="EPSG:32720").to_crs("EPSG:4326").iloc[0]
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

    img = ee.Image(col.first()).select(["B4", "B3", "B2"]).divide(10000)
    fecha_ms = ee.Image(col.first()).get("system:time_start").getInfo()
    fecha_str = datetime.fromtimestamp(fecha_ms/1000).strftime("%Y-%m-%d")

    # Stretch contrast: 0-0.3 → 0-255
    rgb_vis = img.visualize(min=0.0, max=0.3, bands=["B4", "B3", "B2"])

    # Download as GeoTIFF in UTM
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
            arr = src.read()  # (3, H, W) uint8
            transform = src.transform
            crs = src.crs
    return arr, transform, crs, fecha_str


# ════════════════════════════════════════════════════════════════════════════
# 2) OVERLAY: dibujar borde del lote + 5 puntos sobre el array RGB
# ════════════════════════════════════════════════════════════════════════════
def overlay_lote_y_puntos(arr_rgb, transform, lote_geom_utm,
                            puntos_utm, lote_id, fecha_s2, rank):
    """Overlay GPS profesional: borde cyan fino + crosshairs pequeños
    con label al costado. Diseñado para zoom alto en Avenza Maps."""
    img_pil = Image.fromarray(np.transpose(arr_rgb, (1, 2, 0)).astype(np.uint8))
    draw = ImageDraw.Draw(img_pil, "RGBA")

    def utm_to_pixel(x, y):
        col = (x - transform.c) / transform.a
        row = (y - transform.f) / transform.e
        return col, row

    # Borde cyan brillante con halo negro
    geoms = [lote_geom_utm] if lote_geom_utm.geom_type == "Polygon" else list(lote_geom_utm.geoms)
    for g in geoms:
        coords = list(g.exterior.coords)
        pixs = [utm_to_pixel(x, y) for x, y in coords]
        draw.line(pixs, fill=(0, 0, 0, 200), width=3)
        draw.line(pixs, fill=(0, 255, 255, 255), width=1)

    # Waypoints crosshair pequeños
    try:
        font = ImageFont.truetype("arialbd.ttf", 11)
    except Exception:
        font = ImageFont.load_default()

    for _, p in puntos_utm.iterrows():
        cx, cy = utm_to_pixel(p.geometry.x, p.geometry.y)
        cx, cy = int(cx), int(cy)
        L = 8
        draw.line([cx-L, cy, cx+L, cy], fill=(255,255,255,255), width=3)
        draw.line([cx, cy-L, cx, cy+L], fill=(255,255,255,255), width=3)
        draw.line([cx-L, cy, cx+L, cy], fill=(255,0,0,255), width=1)
        draw.line([cx, cy-L, cx, cy+L], fill=(255,0,0,255), width=1)
        draw.ellipse([cx-2, cy-2, cx+2, cy+2],
                      fill=(255,0,0,255), outline=(255,255,255,255), width=1)
        # Label al costado
        txt = f"P{int(p['punto_n'])}"
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        lx = cx + 10
        ly = cy - 10 - th
        pad = 2
        draw.rectangle([lx-pad, ly-pad, lx+tw+pad, ly+th+pad],
                        fill=(255,255,255,220), outline=(0,0,0,255), width=1)
        draw.text((lx, ly), txt, fill=(180,0,0,255), font=font)

    arr_overlay = np.transpose(np.array(img_pil), (2, 0, 1))
    return arr_overlay


def guardar_geotiff(arr_rgb, transform, crs, out_path: Path):
    """Guarda como GeoTIFF compatible Avenza Maps Pro."""
    h = arr_rgb.shape[1]; w = arr_rgb.shape[2]
    with rasterio.open(
        out_path, "w",
        driver="GTiff",
        height=h, width=w, count=3, dtype="uint8",
        crs=crs, transform=transform,
        compress="LZW", photometric="RGB",
        tiled=True, blockxsize=256, blockysize=256,
    ) as dst:
        dst.write(arr_rgb)
        # Tags útiles
        dst.update_tags(
            Title=f"Pixadvisor Hacienda del Senor",
            Software="Pixadvisor v3 — Avenza-compatible GeoTIFF",
        )


# ════════════════════════════════════════════════════════════════════════════
# 3) KMZ universal (polígonos + puntos)
# ════════════════════════════════════════════════════════════════════════════
def generar_kmz_global(top20_meta: list[dict], kmz_out: Path):
    """KMZ con todos los Top 20 lotes (polígono + 5 puntos cada uno)."""
    kml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2">',
           '<Document>',
           f'<name>Pixadvisor Top 20 - Hacienda del Señor</name>',
           f'<description>Plan de muestreo CMI · {datetime.now():%Y-%m-%d}</description>',
           # Estilos
           '<Style id="loteRojoStyle"><LineStyle><color>ff0000ff</color>'
           '<width>3</width></LineStyle><PolyStyle><color>4000007f</color>'
           '</PolyStyle></Style>',
           '<Style id="puntoStyle"><IconStyle>'
           '<color>ff205e1b</color><scale>1.3</scale>'
           '<Icon><href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href></Icon>'
           '</IconStyle><LabelStyle><scale>1.0</scale></LabelStyle></Style>',
           ]
    for meta in top20_meta:
        lote_id = meta["lote_id"]
        rank = meta["rank"]
        # Folder para el lote
        kml.append(f'<Folder><name>#{rank} {lote_id} ({meta["area_ha"]:.1f} ha)</name>')
        kml.append(f'<description>Score v3: {meta["score"]:+.2f} · '
                    f'Estado: {meta["estado"]}</description>')

        # Polígono lote (WGS84 lat/lon)
        gdf = meta["gdf_lote"].to_crs("EPSG:4326")
        for geom in gdf.geometry:
            geoms_iter = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
            for g in geoms_iter:
                coords = list(g.exterior.coords)
                coords_str = " ".join([f"{x:.6f},{y:.6f},0" for x, y in coords])
                kml.append('<Placemark>')
                kml.append(f'<name>Lote {lote_id} (Rank #{rank})</name>')
                kml.append('<styleUrl>#loteRojoStyle</styleUrl>')
                kml.append('<Polygon><outerBoundaryIs><LinearRing>')
                kml.append(f'<coordinates>{coords_str}</coordinates>')
                kml.append('</LinearRing></outerBoundaryIs></Polygon>')
                kml.append('</Placemark>')

        # Puntos
        puntos_wgs = meta["puntos"].to_crs("EPSG:4326")
        for _, p in puntos_wgs.iterrows():
            kml.append('<Placemark>')
            kml.append(f'<name>{lote_id}_P{int(p["punto_n"])}</name>')
            kml.append(f'<description>Lote {lote_id} - Punto {int(p["punto_n"])} de 5</description>')
            kml.append('<styleUrl>#puntoStyle</styleUrl>')
            kml.append(f'<Point><coordinates>{p.geometry.x:.6f},{p.geometry.y:.6f},0</coordinates></Point>')
            kml.append('</Placemark>')

        kml.append('</Folder>')

    kml.append('</Document></kml>')
    kml_str = "\n".join(kml)

    # Empaquetar como KMZ (zip)
    with zipfile.ZipFile(kmz_out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", kml_str)


# ════════════════════════════════════════════════════════════════════════════
# 4) GENERAR LOS GEOTIFF Y KMZ
# ════════════════════════════════════════════════════════════════════════════
def generar_geotiffs_top20(top20: pd.DataFrame, out_dir: Path):
    """Genera GeoTIFF con basemap S2 RGB + overlay para cada lote Top 20."""
    out_dir.mkdir(parents=True, exist_ok=True)
    avenza_dir = out_dir / "AVENZA_MAPS"
    avenza_dir.mkdir(exist_ok=True)

    metas_for_kmz = []
    for i, (_, r) in enumerate(top20.iterrows(), 1):
        lote_id = str(r["lote_id"])
        rank = int(r["Rank_v3"])
        log(f"[{i}/{N_TOP}] {lote_id} — descargando S2 RGB + generando GeoTIFF...")
        try:
            gdf_lote = cargar_geom(lote_id)

            # Cargar puntos generados previamente
            shp_pts = SAMPL_ROOT / f"{rank:02d}_{lote_id}" / f"puntos_muestreo_{lote_id}.shp"
            if not shp_pts.exists():
                log(f"  ! sin puntos: {shp_pts}"); continue
            puntos_utm = gpd.read_file(shp_pts)
            if puntos_utm.crs is None: puntos_utm.set_crs("EPSG:32720", inplace=True)

            # Descarga S2 RGB
            arr, transform, crs, fecha_s2 = descargar_s2_rgb(gdf_lote.geometry.iloc[0])
            if arr is None:
                log(f"  ! sin imagen S2"); continue

            # Overlay
            arr_ov = overlay_lote_y_puntos(arr, transform, gdf_lote.geometry.iloc[0],
                                             puntos_utm, lote_id, fecha_s2, rank)

            # Guardar GeoTIFF en Avenza dir
            tif_out = avenza_dir / f"AVENZA_{rank:02d}_{lote_id}.tif"
            guardar_geotiff(arr_ov, transform, crs, tif_out)
            log(f"  ✓ {tif_out.name}")

            # Recolectar para KMZ
            metas_for_kmz.append({
                "lote_id": lote_id,
                "rank": rank,
                "area_ha": float(r["area_ha"]),
                "score": float(r["Priority_score_v3"]),
                "estado": str(r["Estado_fenologico_v3"]),
                "gdf_lote": gdf_lote,
                "puntos": puntos_utm,
            })
        except Exception as e:
            log(f"  × {e}")

    return metas_for_kmz


# ════════════════════════════════════════════════════════════════════════════
# 5) TUTORIAL PDF imprimible
# ════════════════════════════════════════════════════════════════════════════
def generar_tutorial_pdf(pdf_out: Path):
    doc = SimpleDocTemplate(str(pdf_out), pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="Tutorial Muestreo CMI Pixadvisor",
        author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_huge = ParagraphStyle("Huge", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=24, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=6, leading=28)
    s_big = ParagraphStyle("Big", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=20)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=14, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=4, leading=16)
    s_h3 = ParagraphStyle("H3", parent=s["Heading3"],
        fontName="Helvetica-Bold", fontSize=11, textColor=GRIS,
        alignment=TA_LEFT, spaceBefore=6, spaceAfter=2, leading=13)
    s_sub = ParagraphStyle("Sub", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS, leading=13,
        spaceAfter=3)
    s_step = ParagraphStyle("Step", parent=s_body,
        leftIndent=15, fontSize=10, leading=13)
    s_warn = ParagraphStyle("Warn", parent=s_body,
        fontSize=9.5, textColor=ROJO, leading=12)

    story = []

    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Tutorial Muestreo CMI<br/>"
                   f"v1.0 · {datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 70*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))

    # ═══ PORTADA ═══
    story.append(h_tbl); story.append(Spacer(1, 25*mm))
    story.append(Paragraph("TUTORIAL DE MUESTREO CMI", s_big))
    story.append(Paragraph("Validación in-situ de Madurez en Caña", s_huge))
    story.append(Paragraph("Hacienda del Señor · Top 20 Lotes", s_sub))
    story.append(Spacer(1, 15*mm))

    story.append(Paragraph("¿Qué vas a hacer?", s_h2))
    story.append(Paragraph(
        "Vas a visitar los 20 lotes que el sistema satelital identificó como "
        "más prioritarios para cosecha. En cada lote vas a tomar <b>50 muestras "
        "de jugo de caña</b> con un refractómetro de mano para medir el "
        "<b>CMI (Cane Maturity Index = BS/BI × 100)</b>. Este número define "
        "si el lote está realmente listo para cosechar.", s_body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("¿Por qué es importante?", s_h2))
    story.append(Paragraph(
        "El ranking satelital es un PROXY (NDWI, CIRE, S1 SAR). El CMI con "
        "refractómetro es la <b>medida industrial reconocida</b> por SASRI / "
        "CONSECANA. Validar in-situ confirma o ajusta el ranking antes de "
        "movilizar maquinaria de cosecha. Una equivocación de 1 semana puede "
        "costar 5-8% del Pol del lote.", s_body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Resultado esperado", s_h2))
    story.append(Paragraph(
        "Tras el muestreo: lista ordenada de los 20 lotes con su CMI medido. "
        "Lotes con <b>CMI ≥ 85% → cosecha confirmada en 7-14 días</b>. "
        "Lotes con CMI menor → re-evaluar 2-4 semanas.", s_body))

    # ═══ PÁG 2 — EQUIPAMIENTO ═══
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("1. Equipamiento necesario", s_h2))

    eq = [
        ["Item", "Especificación", "Costo aprox"],
        ["Refractómetro de mano",   "Rango 0-32 °Brix con compensación T° (ATC)", "USD 30-80"],
        ["GPS handheld o smartphone", "Garmin eTrex / app Avenza Maps / Locus / Google Earth", "USD 0-200"],
        ["Machete o cuchillo bien afilado", "Para cortar tallo y exponer entrenudo", "USD 10-20"],
        ["Botella agua destilada",     "300 mL para calibrar refractómetro",        "USD 2"],
        ["Paño suave / pañuelo",       "Limpiar prisma del refractómetro entre muestras", "USD 1"],
        ["Fichas impresas",            "1 PDF por lote (ya generadas)",             "USD 0"],
        ["Lápiz / lapicera",           "Anotar BS y BI en ficha",                   "USD 1"],
        ["Cinta métrica (opcional)",   "5 m × 5 m alrededor del punto P",           "USD 5"],
    ]
    t = Table(eq, colWidths=[55*mm, 90*mm, 25*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",9),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Cómo CALIBRAR el refractómetro (5 min, una vez por día)", s_h2))
    story.append(Paragraph(
        "1. Abrir tapa, limpiar prisma con paño<br/>"
        "2. Poner 1-2 gotas de <b>agua destilada</b> sobre prisma<br/>"
        "3. Cerrar tapa, mirar por el ocular contra luz<br/>"
        "4. Línea azul/blanco debe estar <b>EXACTAMENTE en 0.0 °Brix</b><br/>"
        "5. Si NO está en 0: girar el tornillo de calibración (parte trasera) "
        "con destornillador hasta que la línea coincida con 0<br/>"
        "6. Limpiar prisma, listo para usar", s_body))

    # ═══ PÁG 3 — ANTES DE SALIR ═══
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("2. Antes de salir al campo", s_h2))

    story.append(Paragraph("Checklist preparatorio", s_h3))
    story.append(Paragraph(
        "<b>[ ]</b> Imprimir las 20 fichas PDF (carpeta <i>05-Muestreo-InSitu-Top20/<rank>_<lote>/FICHA_CAMPO_<lote>.pdf</i>)<br/>"
        "<b>[ ]</b> Cargar el archivo <b>KMZ universal</b> en tu app GPS móvil "
        "(ver instrucciones siguiente)<br/>"
        "<b>[ ]</b> Cargar los <b>GeoTIFFs</b> (uno por lote) en Avenza Maps "
        "para ver tu posición sobre la imagen del lote en tiempo real<br/>"
        "<b>[ ]</b> Calibrar refractómetro con agua destilada<br/>"
        "<b>[ ]</b> Cargar baterías GPS / smartphone (full)<br/>"
        "<b>[ ]</b> Coordinar con encargado del lote (acceso, riego, etc.)<br/>"
        "<b>[ ]</b> Llevar Excel <b>MUESTREO_TOP20_DATOS.xlsx</b> al volver para ingresar datos",
        s_body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Cargar el KMZ en tu app GPS (universal, gratis)", s_h3))
    story.append(Paragraph(
        "<b>Avenza Maps (recomendado, gratis hasta 3 mapas)</b>:<br/>"
        "1. Bajar app Avenza Maps de Play Store / App Store<br/>"
        "2. Conectar celular a PC, copiar archivo "
        "<i>Pixadvisor_Top20.kmz</i> a carpeta del celular<br/>"
        "3. Abrir Avenza → ➕ → Open Map → seleccionar el KMZ<br/>"
        "4. El mapa muestra los 20 lotes + 100 puntos. Tu ubicación GPS "
        "aparece como punto azul en tiempo real<br/><br/>"
        "<b>Google Earth (alternativa, gratis ilimitada)</b>:<br/>"
        "1. Bajar Google Earth app<br/>"
        "2. Abrir KMZ desde gestor de archivos → 'Abrir con Google Earth'<br/>"
        "3. Activar 'Mi ubicación' (GPS)<br/><br/>"
        "<b>Locus Map / OruxMaps (avanzados)</b>:<br/>"
        "Soportan KMZ + offline maps + tracks + waypoints. Uso similar.",
        s_body))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Cargar GeoTIFF por lote en Avenza Maps Pro", s_h3))
    story.append(Paragraph(
        "Cada lote tiene su <b>GeoTIFF</b> (carpeta AVENZA_MAPS): un archivo "
        "<i>.tif</i> que muestra la imagen Sentinel-2 RGB del lote con el "
        "borde y los 5 puntos GPS marcados sobre la imagen.<br/>"
        "1. En Avenza Maps Pro: ➕ → Import from your device<br/>"
        "2. Seleccionar <i>AVENZA_##_LOTE.tif</i><br/>"
        "3. El mapa se carga georreferenciado. Tu posición GPS aparece sobre "
        "la imagen real del lote<br/>"
        "4. Útil para: orientarte en campo viendo el verde de la caña real, "
        "no solo polígonos abstractos", s_body))

    # ═══ PÁG 4-5 — PROTOCOLO PASO A PASO ═══
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("3. Protocolo de muestreo paso a paso (en campo)", s_h2))

    story.append(Paragraph("PASO 1 · Llegar al lote y al punto P1", s_h3))
    story.append(Paragraph(
        "• Abrir KMZ o GeoTIFF en tu app GPS<br/>"
        "• Navegar hasta el primer punto del lote (<i>LOTE_P1</i>)<br/>"
        "• Llegar con tolerancia ≤10 m del punto<br/>"
        "• Marcar fecha, hora inicio en la ficha", s_step))

    story.append(Paragraph("PASO 2 · Identificar 10 tallos representativos", s_h3))
    story.append(Paragraph(
        "Desde el punto GPS, en un cuadro de <b>5 m × 5 m</b> alrededor:<br/>"
        "• Elegir 10 tallos <b>representativos</b> del lote<br/>"
        "• <b>NO</b> tallos en el borde (efecto borde)<br/>"
        "• <b>NO</b> tallos atacados por plagas o quemados<br/>"
        "• <b>NO</b> tallos muy delgados o muy gruesos vs el promedio<br/>"
        "• Sí tallos sanos, de tamaño y altura promedio del lote", s_step))

    story.append(Paragraph("PASO 3 · Procesar el primer tallo", s_h3))
    story.append(Paragraph(
        "• Cortar el tallo con machete a <b>30 cm del suelo</b> (raíz queda "
        "para rebrote de soca)<br/>"
        "• Quitar las hojas hasta dejar el tallo limpio<br/>"
        "• Identificar entrenudos: las divisiones visibles del tallo<br/>"
        "• Contar 3 entrenudos <b>desde la base hacia arriba</b><br/>"
        "• Contar 3 entrenudos <b>desde el ápice hacia abajo</b>", s_step))

    story.append(Paragraph("PASO 4 · Tomar Brix INFERIOR (BI) — base del tallo", s_h3))
    story.append(Paragraph(
        "• En el <b>3er entrenudo desde la BASE</b>:<br/>"
        "• Hacer un corte transversal con el machete o cuchillo<br/>"
        "• Apretar el tallo o usar el filo de la hoja para extraer 1-2 gotas "
        "de jugo<br/>"
        "• Limpiar el prisma del refractómetro con paño<br/>"
        "• Poner 1-2 gotas sobre el prisma, cerrar tapa<br/>"
        "• Mirar por el ocular contra luz<br/>"
        "• Leer el valor donde la línea azul-blanco corta la escala<br/>"
        "• Anotar como <b>BI = X.X °Brix</b> en la ficha", s_step))

    story.append(Paragraph("PASO 5 · Tomar Brix SUPERIOR (BS) — ápice del tallo", s_h3))
    story.append(Paragraph(
        "• En el <b>3er entrenudo desde el ÁPICE</b>:<br/>"
        "• Mismo procedimiento de corte y extracción de jugo<br/>"
        "• Limpiar prisma con paño (importante)<br/>"
        "• Poner 1-2 gotas, leer<br/>"
        "• Anotar <b>BS = X.X °Brix</b><br/>"
        "<br/>"
        "<b>NOTA:</b> generalmente BI &gt; BS porque la sucrosa se acumula "
        "primero en la base. Cuando BS se acerca a BI, el tallo está "
        "completamente maduro.", s_step))

    story.append(Paragraph("PASO 6 · Calcular CMI del tallo", s_h3))
    story.append(Paragraph(
        "<b>CMI tallo = (BS / BI) × 100</b><br/>"
        "Ejemplo: BS = 18.5, BI = 22.0 → CMI = (18.5 / 22.0) × 100 = "
        "<b>84.1</b><br/>"
        "El Excel calcula esto automáticamente. La ficha solo necesita BS y BI.",
        s_step))

    story.append(Paragraph("PASO 7 · Repetir para los 10 tallos del punto P1", s_h3))
    story.append(Paragraph(
        "Repetir pasos 3-6 con los 10 tallos elegidos. Tiempo total por punto: "
        "~6-8 minutos.", s_step))

    # ═══ PÁG 5 (continuación protocolo) ═══
    story.append(Spacer(1, 6))
    story.append(Paragraph("PASO 8 · Mover al punto P2, P3, P4, P5", s_h3))
    story.append(Paragraph(
        "Navegar con GPS al siguiente punto del lote y repetir pasos 2-7.<br/>"
        "Total por lote: 5 puntos × 10 tallos = <b>50 mediciones</b>.<br/>"
        "Tiempo total por lote: <b>30-45 min</b>.", s_step))

    story.append(Paragraph("PASO 9 · Cerrar la ficha del lote", s_h3))
    story.append(Paragraph(
        "Antes de irte al siguiente lote:<br/>"
        "• Anotar hora fin<br/>"
        "• Calcular CMI promedio del lote (a mano o esperar al Excel)<br/>"
        "• Marcar la decisión preliminar en la ficha:<br/>"
        "&nbsp;&nbsp;[ ] COSECHAR · [ ] ESPERAR · [ ] RE-EVALUAR<br/>"
        "• Firmar ficha<br/>"
        "• Tomar foto de la ficha completada (backup)", s_step))

    story.append(Paragraph("PASO 10 · Próximo lote", s_h3))
    story.append(Paragraph(
        "Repetir todo el protocolo para los 20 lotes en orden de prioridad "
        "(Rank #1 primero). Distribuir en varias jornadas si necesario "
        "(estimado: 4-5 lotes por día).", s_step))

    # ═══ PÁG 6 — INTERPRETACIÓN ═══
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("4. Interpretación del CMI y decisión", s_h2))

    story.append(Paragraph("Tabla de interpretación CMI (estándar SASRI/CONSECANA)", s_h3))
    interp = [
        ["CMI promedio", "Estado fenológico", "Decisión"],
        ["< 75",         "Muy verde",                  "ESPERAR — re-evaluar 4 semanas"],
        ["75 – 85",      "Maduración temprana",        "Esperar 2-3 semanas"],
        ["85 – 95",      "Cosecha óptima",             "✓ COSECHAR EN 7-14 DÍAS"],
        ["> 95",         "Sobre-maduro",               "URGENTE — cosechar inmediato"],
    ]
    t_i = Table(interp, colWidths=[35*mm, 50*mm, 80*mm])
    t_i.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",10),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",10),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("BACKGROUND",(0,1),(-1,1), HexColor("#FFEBEE")),
        ("BACKGROUND",(0,2),(-1,2), HexColor("#FFF3E0")),
        ("BACKGROUND",(0,3),(-1,3), HexColor("#E8F5E9")),
        ("BACKGROUND",(0,4),(-1,4), HexColor("#FFF9C4")),
        ("FONT",(2,1),(2,-1),"Helvetica-Bold",10),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5)]))
    story.append(t_i)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Ejemplo numérico de cálculo", s_h3))
    ej = [
        ["Tallo","BS (°Brix)","BI (°Brix)","CMI"],
        ["1","17.5","21.0","83.3"],
        ["2","18.0","22.0","81.8"],
        ["3","19.5","22.5","86.7"],
        ["...","...","...","..."],
        ["50","19.0","22.0","86.4"],
        ["PROMEDIO LOTE", "18.6", "21.8", "85.3"],
    ]
    t_ej = Table(ej, colWidths=[30*mm, 30*mm, 30*mm, 30*mm])
    t_ej.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",10),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",10),
        ("ROWBACKGROUNDS",(0,1),(-1,-2),[white, GRIS_CLARO]),
        ("BACKGROUND",(0,-1),(-1,-1), HexColor("#FFF9C4")),
        ("FONT",(0,-1),(-1,-1),"Helvetica-Bold",10),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(t_ej)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Decisión</b>: CMI promedio = 85.3 → cae en rango <b>85-95</b> → "
        "<b>COSECHAR ESTE LOTE EN 7-14 DÍAS</b>.", s_body))

    # ═══ PÁG 7 — VOLVER A OFICINA + ERRORES ═══
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("5. Al volver a oficina — ingresar datos", s_h2))
    story.append(Paragraph(
        "1. Abrir <b>PIXADVISOR_MuestreoTop20_Datos.xlsx</b><br/>"
        "2. Para cada lote tiene una hoja separada (E2, B5, 12, etc.)<br/>"
        "3. Ingresar BS y BI de cada uno de los 50 tallos<br/>"
        "4. <b>El CMI por tallo se calcula automático</b><br/>"
        "5. <b>El CMI promedio del punto se calcula automático</b><br/>"
        "6. <b>El CMI promedio del lote se calcula automático</b><br/>"
        "7. Ir a hoja <b>RESUMEN</b>: ranking final con decisión por lote<br/>"
        "8. Conditional formatting: rojo &lt;75, amarillo 75-85, verde "
        "85-95, naranja &gt;95<br/>"
        "9. Comparar con ranking satelital v3 → reportar discrepancias",
        s_body))

    story.append(Paragraph("6. Errores comunes y troubleshooting", s_h2))
    err = [
        ["Problema",                                  "Solución"],
        ["Refractómetro lee 1-2 °Brix con agua destilada", "Re-calibrar tornillo trasero hasta 0.0"],
        ["Lectura difusa o ambigua",                  "Limpiar prisma, agregar más jugo, mejor iluminación"],
        ["BS &gt; BI (raro)",                         "Verificar que NO se confundió ápice con base. Repetir tallo"],
        ["GPS impreciso (&gt;20m de tolerancia)",     "Esperar 3-5 min para que adquiera satélites. Salir del dosel"],
        ["No encuentro entrenudos claros",            "Eliminar más hojas; los entrenudos son las divisiones visibles"],
        ["Tallo lechoso (no apretable)",              "Es muy verde. Anotar BS=BI=N/D y elegir otro tallo"],
        ["Refractómetro empañado",                    "Pasar paño seco en cada uso. Esperar 30 seg si frío"],
        ["Hojas en mal estado / lote en estrés",      "Anotar en NOTAS de la ficha. Decisión final con menos peso"],
    ]
    t_e = Table(err, colWidths=[75*mm, 95*mm], repeatRows=1)
    t_e.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",9),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_e)
    story.append(Spacer(1, 6))

    story.append(Paragraph("7. Reglas de oro", s_h2))
    story.append(Paragraph(
        "✓ <b>Calibrar TODOS los días</b> el refractómetro con agua destilada<br/>"
        "✓ <b>Limpiar el prisma</b> entre cada tallo (1 segundo, evita falsos altos)<br/>"
        "✓ <b>Tallos representativos</b> — no los más fáciles de cortar<br/>"
        "✓ <b>Trabajar a la misma hora</b> del día (10am-3pm ideal, evitar madrugada)<br/>"
        "✓ <b>Anotar TODO</b> — incluso anomalías (estrés, plagas, riego reciente)<br/>"
        "✓ <b>Backup foto</b> de cada ficha completada antes de salir del lote<br/>"
        "✓ Si <b>llovió en últimas 48h</b> → posponer 3 días (el agua diluye Brix)",
        s_body))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Soporte técnico", s_h3))
    story.append(Paragraph(
        "Pixadvisor AP · Nilton Camargo · gis.agronomico@gmail.com<br/>"
        "Documentación completa de la metodología en el reporte unificado "
        "<b>PIXADVISOR_PrioridadCosecha_HaciendaDelSenor.pdf</b>",
        s_sub))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Tutorial Muestreo CMI · v1.0 · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — Avenza Maps + Tutorial ══")
    if not CSV_RANK.exists():
        log(f"ERROR: falta {CSV_RANK}"); sys.exit(1)
    init_ee()

    df = pd.read_csv(CSV_RANK)
    df["lote_id"] = df["lote_id"].astype(str)
    top20 = df.sort_values("Rank_v3").head(N_TOP).reset_index(drop=True)
    log(f"Top {N_TOP} lotes")

    # 1) GeoTIFFs por lote (Avenza compatible) + recolectar metas para KMZ
    metas = generar_geotiffs_top20(top20, SAMPL_ROOT)

    # 2) KMZ universal
    log("Generando KMZ universal (todos los lotes)...")
    kmz_path = SAMPL_ROOT / "Pixadvisor_Top20.kmz"
    generar_kmz_global(metas, kmz_path)
    log(f"  → {kmz_path.name}")

    # 3) Tutorial PDF
    log("Generando Tutorial PDF...")
    tutorial_pdf = SAMPL_ROOT / "TUTORIAL_PROTOCOLO_MUESTREO.pdf"
    generar_tutorial_pdf(tutorial_pdf)
    log(f"  → {tutorial_pdf.name}")

    log("OK — Salidas en " + str(SAMPL_ROOT))


if __name__ == "__main__":
    main()
