#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — MUESTREO IN-SITU TOP 20 LOTES (validación CMI)
============================================================================
Genera para los Top 20 lotes del ranking v3 (S2+S1):
  1) 5 puntos GPS estratificados por lote (k-means + buffer interno 30m)
  2) Shapefile + KML por lote (cargable en Garmin/smartphone GPS)
  3) Ficha de campo PDF imprimible (mapa + tabla en blanco para 5×10 tallos)
  4) Excel template consolidado (entrada datos + cálculo automático CMI)
  5) PDF índice general con mapa global y orden de visita

Protocolo SASRI PurEst / CONSECANA:
  - 5 puntos por lote, 10 tallos por punto = 50 muestras
  - Brix superior (BS) y Brix inferior (BI) con refractómetro de mano
  - CMI = (BS/BI) × 100
    < 75: muy verde, esperar
    75-85: maduración temprana
    85-95: cosecha óptima
    > 95: sobre-maduro, urgente
  - Lote con CMI ≥ 85% confirmado → cosecha autorizada
============================================================================
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from shapely.geometry import Point, MultiPoint
from shapely.ops import transform as shp_transform
from sklearn.cluster import KMeans

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image as RLImage, PageBreak)

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

# ════════════════════════════════════════════════════════════════════════════
LOTES_ROOT  = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\03-Zonas-Manejo")
OUTPUT_ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\05-Muestreo-InSitu-Top20")
CSV_RANK    = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
                   r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2\ranking_prioridad_v3_S2_S1_2026-05-15.csv")

N_TOP = 20
N_PUNTOS_POR_LOTE = 5
N_TALLOS_POR_PUNTO = 10
BUFFER_INTERNO_M = 30   # alejar puntos del borde

VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")
NARANJA     = HexColor("#EF6C00")
AMARILLO    = HexColor("#F9A825")

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
            "agosto","septiembre","octubre","noviembre","diciembre"]


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def fecha_es(d): return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


def force_2d(g):
    try: return shapely.force_2d(g)
    except Exception: return shp_transform(lambda x, y, *_: (x, y), g)


# ════════════════════════════════════════════════════════════════════════════
# 1) GENERACIÓN DE PUNTOS ESTRATIFICADOS
# ════════════════════════════════════════════════════════════════════════════
def cargar_geom(lote_id: str):
    shp = LOTES_ROOT / lote_id / "PRO" / f"zonas_manejo_{lote_id}_PRO.shp"
    gdf = gpd.read_file(shp)
    if gdf.crs is None: gdf.set_crs("EPSG:32720", inplace=True)
    gdf["geometry"] = gdf.geometry.apply(force_2d)
    return gdf.dissolve()  # UTM 20S


def generar_puntos_estratificados(gdf_lote: gpd.GeoDataFrame,
                                    n_puntos: int = N_PUNTOS_POR_LOTE,
                                    buffer_m: float = BUFFER_INTERNO_M
                                    ) -> gpd.GeoDataFrame:
    """
    Genera n_puntos espacialmente distribuidos dentro del lote, alejados
    al menos buffer_m del borde. K-means sobre grid denso de candidatos.
    Devuelve GeoDataFrame UTM con n_puntos puntos.
    """
    poly = gdf_lote.geometry.iloc[0]
    poly_buf = poly.buffer(-buffer_m)
    if poly_buf.is_empty or poly_buf.area < 1000:
        # Lote muy pequeño: usar buffer menor o sin buffer
        poly_buf = poly.buffer(-min(buffer_m, 10))
        if poly_buf.is_empty:
            poly_buf = poly

    # Grid denso de candidatos
    minx, miny, maxx, maxy = poly_buf.bounds
    spacing = max(20, min((maxx-minx), (maxy-miny)) / 30)
    xs = np.arange(minx, maxx, spacing)
    ys = np.arange(miny, maxy, spacing)
    candidatos = []
    for x in xs:
        for y in ys:
            p = Point(x, y)
            if poly_buf.contains(p):
                candidatos.append((x, y))

    if len(candidatos) < n_puntos:
        # Fallback: muestreo aleatorio con rejection
        candidatos = []
        rng = np.random.default_rng(42)
        attempts = 0
        while len(candidatos) < n_puntos * 10 and attempts < 5000:
            x = rng.uniform(minx, maxx)
            y = rng.uniform(miny, maxy)
            if poly_buf.contains(Point(x, y)):
                candidatos.append((x, y))
            attempts += 1
        if len(candidatos) < n_puntos:
            # Última opción: centroide replicado
            c = poly.centroid
            return gpd.GeoDataFrame(
                {"punto_n": list(range(1, n_puntos+1))},
                geometry=[c]*n_puntos, crs=gdf_lote.crs)

    # K-means para 5 centroides bien distribuidos
    arr = np.array(candidatos)
    km = KMeans(n_clusters=n_puntos, random_state=42, n_init=10)
    km.fit(arr)
    centros = km.cluster_centers_

    # Ajustar cada centroide al candidato real más cercano (asegurar dentro del lote)
    puntos_finales = []
    for cx, cy in centros:
        dists = np.sqrt((arr[:,0]-cx)**2 + (arr[:,1]-cy)**2)
        idx = np.argmin(dists)
        puntos_finales.append(Point(arr[idx, 0], arr[idx, 1]))

    return gpd.GeoDataFrame(
        {"punto_n": list(range(1, n_puntos+1))},
        geometry=puntos_finales, crs=gdf_lote.crs)


# ════════════════════════════════════════════════════════════════════════════
# 2) EXPORTAR SHAPEFILE + KML
# ════════════════════════════════════════════════════════════════════════════
def exportar_geofiles(puntos_utm: gpd.GeoDataFrame, lote_id: str, out_dir: Path):
    """Exporta puntos como shapefile (UTM) + KML (WGS84) + CSV (lat/lon)."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Asignar nombres tipo LOTE_PUNTO
    puntos_utm = puntos_utm.copy()
    puntos_utm["name"] = puntos_utm["punto_n"].apply(
        lambda n: f"{lote_id}_P{int(n)}")
    puntos_utm["lote_id"] = lote_id

    # Shapefile UTM
    shp_path = out_dir / f"puntos_muestreo_{lote_id}.shp"
    puntos_utm.to_file(shp_path)

    # WGS84 para KML y CSV
    puntos_wgs = puntos_utm.to_crs("EPSG:4326")
    puntos_wgs["lat"] = puntos_wgs.geometry.y
    puntos_wgs["lon"] = puntos_wgs.geometry.x

    # KML
    kml_path = out_dir / f"puntos_muestreo_{lote_id}.kml"
    with open(kml_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        f.write(f'<Document>\n<name>Muestreo {lote_id}</name>\n')
        f.write('<Style id="pinPix"><IconStyle><color>ff205e1b</color>'
                '<scale>1.2</scale></IconStyle></Style>\n')
        for _, r in puntos_wgs.iterrows():
            f.write(f'  <Placemark>\n')
            f.write(f'    <name>{r["name"]}</name>\n')
            f.write(f'    <description>Lote {lote_id} - Punto {int(r["punto_n"])} - '
                    f'Brix sup/inf x10 tallos</description>\n')
            f.write(f'    <styleUrl>#pinPix</styleUrl>\n')
            f.write(f'    <Point><coordinates>{r["lon"]:.6f},{r["lat"]:.6f},0</coordinates></Point>\n')
            f.write(f'  </Placemark>\n')
        f.write('</Document>\n</kml>\n')

    # CSV
    csv_path = out_dir / f"puntos_muestreo_{lote_id}.csv"
    puntos_wgs[["name","lote_id","punto_n","lat","lon"]].to_csv(
        csv_path, index=False)


# ════════════════════════════════════════════════════════════════════════════
# 3) MAPA DE CAMPO (PNG con puntos numerados)
# ════════════════════════════════════════════════════════════════════════════
def render_mapa_campo(gdf_lote: gpd.GeoDataFrame, puntos_utm: gpd.GeoDataFrame,
                       lote_id: str, out_png: Path):
    fig, ax = plt.subplots(figsize=(8, 7), dpi=200)
    fig.patch.set_facecolor("white")
    gdf_lote.plot(ax=ax, color="#E8F5E9", edgecolor="#1B5E20",
                   linewidth=2, alpha=0.7)
    puntos_utm.plot(ax=ax, color="red", markersize=200, marker="o",
                     edgecolor="black", linewidth=1.5, zorder=10)
    for _, r in puntos_utm.iterrows():
        ax.annotate(f"P{int(r['punto_n'])}",
                     xy=(r.geometry.x, r.geometry.y),
                     xytext=(8, 8), textcoords="offset points",
                     fontsize=14, fontweight="bold", color="black",
                     bbox=dict(boxstyle="round,pad=0.2", fc="yellow",
                                ec="black", lw=1))
    ax.set_title(f"Mapa de muestreo — Lote {lote_id}\n"
                  f"5 puntos × 10 tallos = 50 muestras Brix sup/inf",
                  fontsize=12, fontweight="bold", color="#1B5E20", pad=10)
    ax.set_xlabel("X UTM (m)", fontsize=8)
    ax.set_ylabel("Y UTM (m)", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ════════════════════════════════════════════════════════════════════════════
# 4) FICHA DE CAMPO PDF (1 lote)
# ════════════════════════════════════════════════════════════════════════════
def generar_ficha_campo(meta: dict, puntos_wgs: gpd.GeoDataFrame,
                          png_mapa: Path, pdf_out: Path):
    """Ficha PDF imprimible: mapa + tabla blanca para 5 puntos × 10 tallos."""
    doc = SimpleDocTemplate(str(pdf_out), pagesize=A4,
        topMargin=12*mm, bottomMargin=12*mm,
        leftMargin=12*mm, rightMargin=12*mm,
        title=f"Ficha campo lote {meta['lote_id']}",
        author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_title = ParagraphStyle("T", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=15, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=2, leading=17)
    s_sub = ParagraphStyle("S", parent=s["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=3, leading=11)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=10, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=4, spaceAfter=2, leading=12)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=8, textColor=GRIS, leading=10)

    story = []

    # Header
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Ficha de Muestreo Brix<br/>"
                   f"Hacienda del Señor</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 86*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    story.append(h_tbl); story.append(Spacer(1, 3))

    # Título
    rank = int(meta.get("Rank_v3", 0))
    story.append(Paragraph(
        f"Lote {meta['lote_id']} — Rank #{rank} prioridad cosecha", s_title))
    story.append(Paragraph(
        f"Área: <b>{meta.get('area_ha',0):.2f} ha</b>  ·  "
        f"Estado: <b>{meta.get('Estado_fenologico_v3','—')}</b>  ·  "
        f"Score v3: <b>{meta.get('Priority_score_v3',0):+.2f}</b>", s_sub))
    story.append(Spacer(1, 3))

    # Datos cabecera (campo a llenar)
    cab = [
        ["Fecha visita", "____ / ____ / 2026", "Hora inicio", "____:____"],
        ["Agrónomo", "_______________________", "Hora fin", "____:____"],
        ["Cultivar (verificar)", "_______________________", "Edad (meses)", "_______________________"],
    ]
    t_cab = Table(cab, colWidths=[35*mm, 60*mm, 25*mm, 60*mm])
    t_cab.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",8),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",8),
        ("FONT",(2,0),(2,-1),"Helvetica-Bold",8),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("TEXTCOLOR",(2,0),(2,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))
    story.append(t_cab); story.append(Spacer(1, 4))

    # Mapa + lista de puntos GPS lado a lado
    if png_mapa.exists():
        rim = RLImage(str(png_mapa), width=110*mm, height=78*mm,
                       kind="proportional")
        rim.hAlign = "LEFT"

        # Tabla GPS de los 5 puntos
        gps_data = [["Punto", "Latitud", "Longitud"]]
        for _, p in puntos_wgs.iterrows():
            gps_data.append([f"P{int(p['punto_n'])}",
                             f"{p['lat']:.5f}", f"{p['lon']:.5f}"])
        t_gps = Table(gps_data, colWidths=[15*mm, 28*mm, 28*mm])
        t_gps.setStyle(TableStyle([
            ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
            ("BACKGROUND",(0,0),(-1,0),VERDE),
            ("TEXTCOLOR",(0,0),(-1,0),white),
            ("FONT",(0,1),(-1,-1),"Helvetica",8),
            ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
            ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("BOTTOMPADDING",(0,0),(-1,-1),2),
            ("TOPPADDING",(0,0),(-1,-1),2)]))

        side = Table([[rim, t_gps]], colWidths=[115*mm, 75*mm])
        side.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(side); story.append(Spacer(1, 3))

    # Tabla en blanco para datos: 5 puntos × 10 tallos
    story.append(Paragraph(
        "Registro Brix — refractómetro de mano (°Brix) — "
        "BS = Brix superior tallo · BI = Brix inferior tallo", s_h2))

    blank_data = [["Punto", "Tallo",
                    "BS (°Brix)", "BI (°Brix)",
                    "CMI = BS/BI×100", "Notas"]]
    for p in range(1, N_PUNTOS_POR_LOTE+1):
        for t in range(1, N_TALLOS_POR_PUNTO+1):
            label_p = f"P{p}" if t == 1 else ""
            blank_data.append([label_p, str(t), "_____", "_____",
                                "_____", "_____________"])
    # Fila promedio por punto
    blank_data.append(["", "PROMEDIO LOTE", "", "", "_____", ""])

    t_blank = Table(blank_data, colWidths=[14*mm, 18*mm, 22*mm, 22*mm, 28*mm, 80*mm],
                    repeatRows=1)
    style = [
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",8),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",7.5),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),2),
        ("TOPPADDING",(0,0),(-1,-1),2),
    ]
    # Líneas separadoras entre puntos
    for p in range(1, N_PUNTOS_POR_LOTE):
        row = 1 + p * N_TALLOS_POR_PUNTO
        style.append(("LINEABOVE",(0,row),(-1,row), 1.0, VERDE))
    # Fondo amarillo para fila promedio
    style.append(("BACKGROUND",(0,-1),(-1,-1), HexColor("#FFF9C4")))
    style.append(("FONT",(0,-1),(-1,-1),"Helvetica-Bold",8))
    t_blank.setStyle(TableStyle(style))
    story.append(t_blank)
    story.append(Spacer(1, 3))

    # Tabla de interpretación CMI
    story.append(Paragraph("Interpretación CMI (estándar SASRI/CONSECANA)", s_h2))
    interp = [
        ["CMI < 75",  "Muy verde", "ESPERAR — re-evaluar 4 semanas"],
        ["75 ≤ CMI < 85", "Maduración temprana", "Esperar 2-3 semanas"],
        ["85 ≤ CMI < 95", "Cosecha óptima", "✓ COSECHAR EN 7-14 DÍAS"],
        ["CMI ≥ 95", "Sobre-maduro", "URGENTE — cosechar inmediato"],
    ]
    t_i = Table(interp, colWidths=[35*mm, 50*mm, 100*mm])
    t_i.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",8),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",8),
        ("FONT",(2,0),(2,-1),"Helvetica-Bold",8),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BACKGROUND",(0,0),(-1,0), HexColor("#FFEBEE")),
        ("BACKGROUND",(0,1),(-1,1), HexColor("#FFF3E0")),
        ("BACKGROUND",(0,2),(-1,2), HexColor("#E8F5E9")),
        ("BACKGROUND",(0,3),(-1,3), HexColor("#FFF9C4")),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_i)

    # Recomendación final firmada
    story.append(Spacer(1, 4))
    story.append(Paragraph("Decisión final del agrónomo", s_h2))
    final = [
        ["CMI promedio del lote:", "________"],
        ["Recomendación:", "[ ] COSECHAR  [ ] ESPERAR  [ ] RE-EVALUAR ___ días"],
        ["Firma agrónomo:", "_______________________________________"],
    ]
    t_f = Table(final, colWidths=[50*mm, 130*mm])
    t_f.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",9),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",9),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))
    story.append(t_f)

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 8*mm,
            f"Pixadvisor AP · Hacienda del Señor · Lote {meta['lote_id']} · "
            f"Ficha Muestreo · {datetime.now():%Y-%m-%d}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(12*mm, 11*mm, A4[0]-12*mm, 11*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)


# ════════════════════════════════════════════════════════════════════════════
# 5) EXCEL TEMPLATE consolidado (entrada datos + cálculo CMI)
# ════════════════════════════════════════════════════════════════════════════
def generar_excel_template(top20: pd.DataFrame, puntos_por_lote: dict,
                            xlsx_out: Path):
    """Excel con una hoja por lote + hoja Resumen. Cálculo CMI automático."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # Estilos
    fill_header = PatternFill("solid", fgColor="1B5E20")
    fill_alt = PatternFill("solid", fgColor="F5F5F5")
    fill_yellow = PatternFill("solid", fgColor="FFF9C4")
    fill_green = PatternFill("solid", fgColor="C8E6C9")
    fill_red = PatternFill("solid", fgColor="FFCDD2")
    fill_orange = PatternFill("solid", fgColor="FFE0B2")
    font_header = Font(bold=True, color="FFFFFF", size=11)
    font_bold = Font(bold=True, size=10)
    border_thin = Border(*[Side(style="thin", color="BDBDBD")]*4)

    # ═══ Hoja Resumen (vacía por ahora, se llenará con fórmulas)
    ws_r = wb.create_sheet("RESUMEN")
    headers_resumen = ["#", "Lote", "Área (ha)", "Rank v3", "Estado v3",
                        "CMI lote", "Estado CMI", "Recomendación"]
    for col, h in enumerate(headers_resumen, 1):
        c = ws_r.cell(1, col, h)
        c.fill = fill_header; c.font = font_header
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = border_thin

    for i, (_, row) in enumerate(top20.iterrows(), 2):
        lote_id = str(row["lote_id"])
        ws_r.cell(i, 1, i-1)
        ws_r.cell(i, 2, lote_id)
        ws_r.cell(i, 3, float(row["area_ha"]))
        ws_r.cell(i, 4, int(row["Rank_v3"]))
        ws_r.cell(i, 5, str(row["Estado_fenologico_v3"]))
        # CMI lote = referencia a hoja del lote (PROMEDIO de columna F)
        sheet_name = f"{lote_id}"
        ws_r.cell(i, 6, f"='{sheet_name}'!I{N_PUNTOS_POR_LOTE * N_TALLOS_POR_PUNTO + 4}")
        # Estado CMI con IF anidado
        cmi_ref = f"F{i}"
        ws_r.cell(i, 7,
            f'=IF(ISBLANK({cmi_ref}),"sin datos",'
            f'IF({cmi_ref}>=95,"sobre-maduro",'
            f'IF({cmi_ref}>=85,"cosecha óptima",'
            f'IF({cmi_ref}>=75,"madurando temprano","verde"))))')
        ws_r.cell(i, 8,
            f'=IF(ISBLANK({cmi_ref}),"esperar muestreo",'
            f'IF({cmi_ref}>=95,"URGENTE cosechar",'
            f'IF({cmi_ref}>=85,"COSECHAR 7-14d",'
            f'IF({cmi_ref}>=75,"esperar 2-3 sem","esperar 4 sem"))))')
        for col in range(1, 9):
            cc = ws_r.cell(i, col)
            cc.border = border_thin
            if i % 2 == 0: cc.fill = fill_alt

    # Anchos
    widths = [5, 12, 12, 10, 24, 12, 18, 22]
    for col, w in enumerate(widths, 1):
        ws_r.column_dimensions[get_column_letter(col)].width = w
    # Conditional formatting CMI
    ws_r.conditional_formatting.add(
        f"F2:F{len(top20)+1}",
        CellIsRule(operator="greaterThanOrEqual", formula=["95"], fill=fill_orange))
    ws_r.conditional_formatting.add(
        f"F2:F{len(top20)+1}",
        CellIsRule(operator="between", formula=["85","94.99"], fill=fill_green))
    ws_r.conditional_formatting.add(
        f"F2:F{len(top20)+1}",
        CellIsRule(operator="between", formula=["75","84.99"], fill=fill_yellow))
    ws_r.conditional_formatting.add(
        f"F2:F{len(top20)+1}",
        CellIsRule(operator="lessThan", formula=["75"], fill=fill_red))

    # ═══ Una hoja por lote
    for _, row in top20.iterrows():
        lote_id = str(row["lote_id"])
        ws = wb.create_sheet(lote_id[:31])  # max 31 chars

        # Header lote
        ws["A1"] = f"LOTE {lote_id}"
        ws["A1"].font = Font(bold=True, size=14, color="1B5E20")
        ws["A2"] = f"Rank v3: #{int(row['Rank_v3'])}  ·  Área: {row['area_ha']:.2f} ha  ·  Estado v3: {row['Estado_fenologico_v3']}"
        ws["A2"].font = Font(size=9, color="333333")
        ws["A3"] = f"Score v3: {row['Priority_score_v3']:+.2f}  ·  Imagen S2A: {row['fecha_imagen']}"
        ws["A3"].font = Font(size=9, color="333333")
        ws["A4"] = "Protocolo: 5 puntos × 10 tallos · Brix sup/inf con refractómetro · CMI = BS/BI × 100"
        ws["A4"].font = Font(size=8, italic=True, color="555555")

        # Puntos GPS reference (filas 6-10)
        ws["A6"] = "Puntos GPS"
        ws["A6"].font = font_bold
        for col, h in enumerate(["Punto","Latitud","Longitud"], 1):
            c = ws.cell(7, col, h); c.fill = fill_header; c.font = font_header
            c.alignment = Alignment(horizontal="center"); c.border = border_thin
        puntos_wgs = puntos_por_lote[lote_id]
        for i, (_, p) in enumerate(puntos_wgs.iterrows(), 8):
            ws.cell(i, 1, f"P{int(p['punto_n'])}").border = border_thin
            ws.cell(i, 2, f"{p['lat']:.6f}").border = border_thin
            ws.cell(i, 3, f"{p['lon']:.6f}").border = border_thin

        # Header tabla muestras
        row_start = 14
        headers = ["Punto","Tallo","BS (°Brix)","BI (°Brix)","CMI tallo",
                    "BS prom punto","BI prom punto","CMI prom punto","Notas"]
        for col, h in enumerate(headers, 1):
            c = ws.cell(row_start, col, h)
            c.fill = fill_header; c.font = font_header
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = border_thin

        # Filas de datos
        for p in range(1, N_PUNTOS_POR_LOTE+1):
            for t in range(1, N_TALLOS_POR_PUNTO+1):
                r = row_start + (p-1) * N_TALLOS_POR_PUNTO + t
                ws.cell(r, 1, f"P{p}" if t==1 else "").border = border_thin
                ws.cell(r, 2, t).border = border_thin
                # BS y BI vacíos para llenar
                bs = ws.cell(r, 3); bs.border = border_thin
                bi = ws.cell(r, 4); bi.border = border_thin
                # CMI tallo automático
                cmi_t = ws.cell(r, 5,
                    f'=IF(AND(ISNUMBER(C{r}),ISNUMBER(D{r}),D{r}>0),C{r}/D{r}*100,"")')
                cmi_t.border = border_thin
                cmi_t.alignment = Alignment(horizontal="center")
                # BS, BI, CMI prom solo en primera fila de cada punto
                if t == 1:
                    r_end = r + N_TALLOS_POR_PUNTO - 1
                    bs_p = ws.cell(r, 6, f"=AVERAGE(C{r}:C{r_end})")
                    bi_p = ws.cell(r, 7, f"=AVERAGE(D{r}:D{r_end})")
                    cmi_p = ws.cell(r, 8, f"=AVERAGE(E{r}:E{r_end})")
                    for c_idx in [6,7,8]:
                        cc = ws.cell(r, c_idx)
                        cc.border = border_thin; cc.fill = fill_yellow
                        cc.font = font_bold
                        cc.alignment = Alignment(horizontal="center")
                ws.cell(r, 9).border = border_thin
                # Alternancia color filas
                if r % 2 == 0:
                    for col in range(1, 10):
                        if not ws.cell(r, col).fill.fgColor.value or \
                           ws.cell(r, col).fill.fgColor.value == "00000000":
                            ws.cell(r, col).fill = fill_alt

        # PROMEDIO LOTE
        promedio_row = row_start + N_PUNTOS_POR_LOTE * N_TALLOS_POR_PUNTO + 2
        ws.cell(promedio_row, 1, "PROMEDIO LOTE").font = font_bold
        ws.cell(promedio_row, 1).fill = fill_green

        # Promedio CMI lote = promedio de los CMI promedio por punto
        cmi_p_rows = [row_start + (p-1)*N_TALLOS_POR_PUNTO + 1 for p in range(1, N_PUNTOS_POR_LOTE+1)]
        cmi_p_refs = ",".join([f"H{r}" for r in cmi_p_rows])
        ws.cell(promedio_row, 8, f"=AVERAGE({cmi_p_refs})").font = font_bold
        ws.cell(promedio_row, 8).fill = fill_green
        ws.cell(promedio_row, 8).alignment = Alignment(horizontal="center")
        ws.cell(promedio_row, 8).border = border_thin

        # Conditional formatting CMI tallo
        cmi_range = f"E{row_start+1}:E{row_start+N_PUNTOS_POR_LOTE*N_TALLOS_POR_PUNTO}"
        ws.conditional_formatting.add(cmi_range,
            CellIsRule(operator="greaterThanOrEqual", formula=["95"], fill=fill_orange))
        ws.conditional_formatting.add(cmi_range,
            CellIsRule(operator="between", formula=["85","94.99"], fill=fill_green))
        ws.conditional_formatting.add(cmi_range,
            CellIsRule(operator="between", formula=["75","84.99"], fill=fill_yellow))
        ws.conditional_formatting.add(cmi_range,
            CellIsRule(operator="lessThan", formula=["75"], fill=fill_red))

        # Anchos
        widths = [6, 6, 11, 11, 11, 13, 13, 13, 30]
        for col, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = w

    wb.save(xlsx_out)


# ════════════════════════════════════════════════════════════════════════════
# 6) PDF ÍNDICE GENERAL (orden de visita + mapa global)
# ════════════════════════════════════════════════════════════════════════════
def render_mapa_top20(top20: pd.DataFrame, all_geoms: dict, png_out: Path):
    fig, ax = plt.subplots(figsize=(13, 11), dpi=200)
    fig.patch.set_facecolor("white")
    # Plot todos los lotes Top 20
    polys = []
    for _, r in top20.iterrows():
        lid = str(r["lote_id"])
        if lid in all_geoms:
            g = all_geoms[lid].copy()
            g["lote_id"] = lid
            g["Rank"] = int(r["Rank_v3"])
            g["Score"] = r["Priority_score_v3"]
            polys.append(g)
    if not polys: return
    gdf_all = gpd.GeoDataFrame(pd.concat(polys, ignore_index=True), crs="EPSG:32720")
    gdf_all.plot(ax=ax, column="Score", cmap="Reds",
                  edgecolor="black", linewidth=1.0, alpha=0.85)
    for _, r in gdf_all.iterrows():
        c = r.geometry.centroid
        ax.annotate(f"#{r['Rank']}\n{r['lote_id']}",
                     xy=(c.x, c.y), xytext=(0,0), textcoords="offset points",
                     fontsize=9, fontweight="bold", color="black",
                     ha="center", va="center",
                     bbox=dict(boxstyle="round,pad=0.25", fc="yellow",
                                ec="black", lw=0.6, alpha=0.9))
    ax.set_axis_off()
    ax.set_title(f"Top 20 Lotes — Plan de Muestreo In-situ\n"
                  f"Hacienda del Señor · {datetime.now():%Y-%m-%d}",
                  fontsize=14, fontweight="bold", color="#1B5E20", pad=15)
    ax.set_aspect("equal")
    plt.tight_layout()
    plt.savefig(png_out, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generar_indice_pdf(top20: pd.DataFrame, mapa_global_png: Path,
                        pdf_out: Path):
    doc = SimpleDocTemplate(str(pdf_out), pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="Plan Muestreo Top 20", author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_huge = ParagraphStyle("Huge", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=22, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=24)
    s_sub = ParagraphStyle("S", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=14)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS, leading=13)

    story = []

    # Header
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Plan de Muestreo<br/>{datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 70*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(h_tbl); story.append(Spacer(1, 6))

    story.append(Paragraph("Plan de Muestreo In-situ — Top 20 Lotes", s_huge))
    story.append(Paragraph(
        "Validación CMI (Brix superior/inferior con refractómetro) sobre los "
        "lotes con mayor prioridad de cosecha según ranking v3 (S2+S1+ERA5).",
        s_sub))
    story.append(Spacer(1, 6))

    # Resumen logístico
    story.append(Paragraph("Resumen logístico", s_h2))
    info = [
        ["Total lotes a muestrear", f"{len(top20)}"],
        ["Total puntos GPS", f"{len(top20)*N_PUNTOS_POR_LOTE} (5 por lote)"],
        ["Total tallos a medir", f"{len(top20)*N_PUNTOS_POR_LOTE*N_TALLOS_POR_PUNTO} "
                                  f"(50 por lote)"],
        ["Tiempo estimado por lote", "30-45 min en campo"],
        ["Tiempo total estimado", f"{len(top20)*0.7:.1f} - {len(top20)*0.85:.1f} días-persona"],
        ["Equipamiento", "Refractómetro de mano (rango 0-32 °Brix), GPS handheld o smartphone, machete, ficha"],
        ["Hectáreas cubiertas", f"{top20['area_ha'].sum():.0f} ha"],
    ]
    t_i = Table(info, colWidths=[55*mm, 115*mm])
    t_i.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",10),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",10),
        ("TEXTCOLOR",(0,0),(0,-1),VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("LINEBELOW",(0,0),(-1,-1),0.3,GRIS_LINEA)]))
    story.append(t_i); story.append(Spacer(1, 6))

    # Mapa global
    if mapa_global_png.exists():
        rim = RLImage(str(mapa_global_png), width=170*mm, height=130*mm,
                       kind="proportional")
        rim.hAlign = "CENTER"
        story.append(rim)

    # Tabla orden de visita
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Orden de visita recomendado (por prioridad)", s_h2))
    rows = [["#","Lote","Área (ha)","Score v3","Estado","IC95%","Coord centroide (lat,lon)"]]
    for i, (_, r) in enumerate(top20.iterrows(), 1):
        rows.append([
            str(i), str(r["lote_id"]), f"{r['area_ha']:,.2f}",
            f"{r['Priority_score_v3']:+.2f}",
            str(r["Estado_fenologico_v3"])[:18],
            f"[{int(r['Rank_v3_p025'])}-{int(r['Rank_v3_p975'])}]",
            ""])
    t_t = Table(rows,
                colWidths=[8*mm, 22*mm, 22*mm, 18*mm, 38*mm, 22*mm, 40*mm],
                repeatRows=1)
    t_t.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",9),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("ALIGN",(2,1),(-1,-1),"RIGHT"),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_t)
    story.append(Spacer(1, 6))

    # Protocolo CMI
    story.append(Paragraph("Protocolo de muestreo (SASRI PurEst / CONSECANA)", s_h2))
    story.append(Paragraph(
        "<b>Por cada uno de los 5 puntos GPS</b> dentro del lote: muestrear "
        "<b>10 tallos</b> en línea o cuadrado de 5×5 m alrededor del punto. "
        "Por cada tallo:<br/>"
        "&nbsp;&nbsp;1. Cortar a 30 cm del suelo y eliminar hojas<br/>"
        "&nbsp;&nbsp;2. Extraer 1 gota de jugo del <b>tercer entrenudo desde la base</b> = BI<br/>"
        "&nbsp;&nbsp;3. Extraer 1 gota del <b>tercer entrenudo desde el ápice</b> = BS<br/>"
        "&nbsp;&nbsp;4. Leer °Brix con refractómetro (calibrar con agua destilada)<br/>"
        "&nbsp;&nbsp;5. Anotar BS, BI en la ficha. CMI = BS/BI × 100<br/>"
        "<br/>"
        "<b>Decisión final por lote</b> = promedio CMI de los 50 tallos.",
        s_body))

    story.append(Paragraph("Interpretación CMI", s_h2))
    interp = [
        ["CMI < 75",      "Muy verde",            "ESPERAR — re-evaluar 4 sem"],
        ["75 ≤ CMI < 85", "Maduración temprana",  "Esperar 2-3 sem"],
        ["85 ≤ CMI < 95", "Cosecha óptima",       "✓ COSECHAR EN 7-14 DÍAS"],
        ["CMI ≥ 95",      "Sobre-maduro",         "URGENTE — cosechar ya"],
    ]
    t_p = Table(interp, colWidths=[35*mm, 50*mm, 80*mm])
    t_p.setStyle(TableStyle([
        ("FONT",(0,0),(-1,-1),"Helvetica",9),
        ("FONT",(0,0),(0,-1),"Helvetica-Bold",9),
        ("FONT",(2,0),(2,-1),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0), HexColor("#FFEBEE")),
        ("BACKGROUND",(0,1),(-1,1), HexColor("#FFF3E0")),
        ("BACKGROUND",(0,2),(-1,2), HexColor("#E8F5E9")),
        ("BACKGROUND",(0,3),(-1,3), HexColor("#FFF9C4")),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(t_p)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Archivos generados (en carpeta del lote)", s_h2))
    files = (
        "• <b>puntos_muestreo_LOTE.kml</b> — cargar en GPS handheld o "
        "smartphone (Google Earth, Locus Map, BasicAirData)<br/>"
        "• <b>puntos_muestreo_LOTE.shp</b> — para QGIS / ArcGIS<br/>"
        "• <b>puntos_muestreo_LOTE.csv</b> — coordenadas plano texto<br/>"
        "• <b>FICHA_CAMPO_LOTE.pdf</b> — imprimir y llevar al campo<br/>"
        "• <b>MUESTREO_TOP20_DATOS.xlsx</b> — un solo archivo Excel para "
        "ingresar TODOS los datos al volver del campo. CMI se calcula automático."
    )
    story.append(Paragraph(files, s_body))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Plan Muestreo Top 20 · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("══ Pixadvisor — Muestreo In-situ Top 20 ══")
    if not CSV_RANK.exists():
        log(f"ERROR: falta {CSV_RANK}"); sys.exit(1)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV_RANK)
    df["lote_id"] = df["lote_id"].astype(str)
    top20 = df.sort_values("Rank_v3").head(N_TOP).reset_index(drop=True)
    log(f"Top {N_TOP} lotes seleccionados:")
    for i, r in top20.iterrows():
        log(f"  #{int(r['Rank_v3']):2d}  {r['lote_id']:14s}  {r['area_ha']:6.2f} ha  Score={r['Priority_score_v3']:+.2f}")

    # Generar archivos por lote
    all_geoms = {}
    puntos_por_lote_wgs = {}
    for i, r in top20.iterrows():
        lid = str(r["lote_id"])
        log(f"[{i+1}/{N_TOP}] {lid}")
        try:
            gdf = cargar_geom(lid)
            all_geoms[lid] = gdf
            lote_dir = OUTPUT_ROOT / f"{int(r['Rank_v3']):02d}_{lid}"
            lote_dir.mkdir(parents=True, exist_ok=True)

            # Puntos
            puntos_utm = generar_puntos_estratificados(gdf)

            # Geofiles
            exportar_geofiles(puntos_utm, lid, lote_dir)
            puntos_wgs = puntos_utm.to_crs("EPSG:4326")
            puntos_wgs["lat"] = puntos_wgs.geometry.y
            puntos_wgs["lon"] = puntos_wgs.geometry.x
            puntos_por_lote_wgs[lid] = puntos_wgs

            # Mapa de campo PNG
            png_mapa = lote_dir / f"mapa_campo_{lid}.png"
            render_mapa_campo(gdf, puntos_utm, lid, png_mapa)

            # Ficha PDF
            meta = r.to_dict()
            ficha_pdf = lote_dir / f"FICHA_CAMPO_{lid}.pdf"
            generar_ficha_campo(meta, puntos_wgs, png_mapa, ficha_pdf)
            log(f"     ✓ {ficha_pdf.name}")
        except Exception as e:
            log(f"     × {e}")

    # Excel template consolidado
    log("Generando Excel template...")
    xlsx = OUTPUT_ROOT / "MUESTREO_TOP20_DATOS.xlsx"
    generar_excel_template(top20, puntos_por_lote_wgs, xlsx)
    log(f"  → {xlsx.name}")

    # Mapa global Top 20
    log("Generando mapa global Top 20...")
    mapa_global = OUTPUT_ROOT / "_mapa_top20.png"
    render_mapa_top20(top20, all_geoms, mapa_global)
    log(f"  → {mapa_global.name}")

    # PDF índice general
    log("Generando PDF índice general...")
    indice_pdf = OUTPUT_ROOT / "PLAN_MUESTREO_TOP20.pdf"
    generar_indice_pdf(top20, mapa_global, indice_pdf)
    log(f"  → {indice_pdf.name}")

    log(f"OK — Salidas en {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
