#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — Unificador de Reportes de Sacarosa
============================================================================
Compila un único PDF para enviar al cliente:
  1) Portada Pixadvisor
  2) Resumen ejecutivo (KPIs, distribución, top 10 lotes maduros)
  3) Glosario Pol
  4) Reportes lote-a-lote ordenados por Pol descendente
============================================================================
"""
from __future__ import annotations
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
from pypdf import PdfReader, PdfWriter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak)

# Forzar UTF-8 stdout (Windows cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
ROOT = Path(
    r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
    r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
)
CSV_STATS = ROOT / "pix_sacarosa_index_2026-05-13.csv"
GLOSARIO_PDF = ROOT / "00_Glosario_POL_Pixadvisor.pdf"
PDF_PATTERN = "PIX_Sacarosa_*_*.pdf"

CLIENTE = "Hacienda del Señor"
UBICACION = "Santa Cruz, Bolivia"
FECHA_IMAGEN_REPRESENTATIVA = "2026-05-04 / 2026-05-06"

OUT_PDF = ROOT / f"RELATORIO_COMPLETO_Sacarosa_Hacienda_del_Senor_{datetime.now():%Y-%m-%d}.pdf"

# Branding Pixadvisor
VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

def fecha_es(d: datetime) -> str:
    return f"{d.day} de {MESES_ES[d.month - 1]} de {d.year}"


# ════════════════════════════════════════════════════════════════════════════
# PORTADA + RESUMEN EJECUTIVO
# ════════════════════════════════════════════════════════════════════════════

def build_portada_y_resumen(df: pd.DataFrame) -> bytes:
    """Genera portada + resumen ejecutivo en memoria, devuelve bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Reporte Sacarosa Hacienda del Señor",
        author="Pixadvisor AP",
    )

    s = getSampleStyleSheet()
    s_huge = ParagraphStyle("Huge", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=30, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=8, leading=34)
    s_big = ParagraphStyle("Big", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=20, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=22)
    s_subtitle = ParagraphStyle("PixSub", parent=s["Normal"],
        fontName="Helvetica", fontSize=11, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=14)
    s_h2 = ParagraphStyle("PixH2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=13, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=6, leading=15)
    s_body = ParagraphStyle("PixBody", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS, leading=13)
    s_meta = ParagraphStyle("Meta", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, leading=14)

    story = []

    # ═══ PORTADA ═══
    # Header con línea verde
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión",
                  s_subtitle),
        Paragraph(f"<para align=right>{datetime.now():%Y-%m-%d}</para>",
                  s_subtitle),
    ]]
    h_tbl = Table(header, colWidths=[110 * mm, 60 * mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, VERDE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(h_tbl)
    story.append(Spacer(1, 50 * mm))

    story.append(Paragraph("REPORTE DE MADUREZ", s_big))
    story.append(Paragraph("Índice de Sacarosa por Lote", s_huge))
    story.append(Spacer(1, 20 * mm))

    # Bloque identificación
    meta = [
        ["Cliente",                CLIENTE],
        ["Ubicación",              UBICACION],
        ["Cultivo",                "Caña de azúcar"],
        ["Sensor",                 "Sentinel-2A (ESA Copernicus)"],
        ["Modelo",                 "Canata et al. (2024) — Pol estimado"],
        ["Imagen utilizada",       FECHA_IMAGEN_REPRESENTATIVA],
        ["Lotes analizados",       str(len(df))],
        ["Área total caña",        f"{df['area_ha'].sum():.0f} ha"],
        ["Fecha del reporte",      fecha_es(datetime.now())],
    ]
    t_meta = Table(meta, colWidths=[55 * mm, 110 * mm])
    t_meta.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE),
        ("TEXTCOLOR", (1, 0), (1, -1), GRIS),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph(
        "<i>Este documento agrupa los análisis de madurez por contenido de "
        "Pol estimado para todos los lotes de caña de azúcar de la "
        "hacienda, derivados de la imagen Sentinel-2A más reciente sin "
        "nubes. Incluye glosario técnico, resumen ejecutivo y reporte "
        "individual por lote ordenado por prioridad de cosecha.</i>",
        s_body))
    story.append(PageBreak())

    # ═══ RESUMEN EJECUTIVO ═══
    # Header
    story.append(h_tbl)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Resumen Ejecutivo", s_big))
    story.append(Paragraph(
        f"Estado de madurez de la hacienda al "
        f"{datetime.now():%Y-%m-%d}", s_subtitle))
    story.append(Spacer(1, 6))

    # KPIs globales
    pol_mean_global = df["POL_mean"].mean()
    pol_std_lotes = df["POL_mean"].std()
    area_tot = df["area_ha"].sum()
    n_lotes = len(df)
    pmin = df["POL_mean"].min()
    pmax = df["POL_mean"].max()

    kpis = [
        ["Lotes analizados",        f"{n_lotes}",                            "Cobertura 100%"],
        ["Área total",              f"{area_tot:,.0f} ha",                   "Caña de azúcar"],
        ["Pol estimado medio",      f"{pol_mean_global:.2f} %",              "Promedio ponderado por lote"],
        ["Rango Pol entre lotes",   f"{pmin:.2f} – {pmax:.2f} %",            "Heterogeneidad espacial"],
        ["Desvío entre lotes",      f"{pol_std_lotes:.2f} %",                "Variabilidad inter-lote"],
    ]
    t_kpis = Table(kpis, colWidths=[55 * mm, 40 * mm, 65 * mm])
    t_kpis.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 10),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
        ("FONT", (1, 0), (1, -1), "Helvetica-Bold", 11),
        ("TEXTCOLOR", (0, 0), (0, -1), VERDE),
        ("TEXTCOLOR", (1, 0), (1, -1), GRIS),
        ("TEXTCOLOR", (2, 0), (2, -1), GRIS),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
    ]))
    story.append(t_kpis)
    story.append(Spacer(1, 8))

    # Distribución de madurez
    story.append(Paragraph("Distribución por categoría de madurez", s_h2))
    bins  = [-1e9, 9, 10, 11, 12, 14, 1e9]
    labels = ["< 9% (muy inmaduro)", "9–10% (inmaduro)",
              "10–11% (temprano)",   "11–12% (medio)",
              "12–14% (avanzado)",   "> 14% (cosecha óptima)"]
    df_ok = df.copy()
    df_ok["cat"] = pd.cut(df_ok["POL_mean"], bins=bins, labels=labels)
    dist = df_ok.groupby("cat", observed=True).agg(
        n=("lote_id", "count"),
        ha=("area_ha", "sum"),
    ).reset_index()
    dist["pct_ha"] = dist["ha"] / dist["ha"].sum() * 100

    dist_rows = [["Categoría", "# Lotes", "Hectáreas", "% del área"]]
    for _, r in dist.iterrows():
        dist_rows.append([
            str(r["cat"]),
            f"{int(r['n'])}",
            f"{r['ha']:,.1f}",
            f"{r['pct_ha']:.1f} %",
        ])
    t_dist = Table(dist_rows, colWidths=[65 * mm, 25 * mm, 35 * mm, 30 * mm],
                   repeatRows=1)
    t_dist.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), GRIS),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    story.append(t_dist)
    story.append(Spacer(1, 8))

    # Top 15 lotes con mayor Pol (prioridad de cosecha)
    story.append(Paragraph(
        "Top 15 lotes — prioridad de cosecha (mayor Pol primero)", s_h2))
    top = df.nlargest(15, "POL_mean").reset_index(drop=True)
    top_rows = [["#", "Lote", "Área (ha)", "Pol medio %", "Desvío %",
                 "Fecha S2A"]]
    for i, r in top.iterrows():
        top_rows.append([
            str(i + 1),
            str(r["lote_id"]),
            f"{r['area_ha']:,.2f}",
            f"{r['POL_mean']:.2f}",
            f"{r['POL_stdDev']:.2f}",
            str(r["fecha_imagen"]),
        ])
    t_top = Table(top_rows,
                  colWidths=[10 * mm, 30 * mm, 28 * mm, 28 * mm, 25 * mm, 30 * mm],
                  repeatRows=1)
    t_top.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), GRIS),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
    ]))
    story.append(t_top)
    story.append(Spacer(1, 8))

    # Recomendación general
    story.append(Paragraph("Recomendación general", s_h2))
    if pol_mean_global < 11:
        rec = ("La hacienda se encuentra en fase de <b>pre-maduración</b>. "
               "La cosecha generalizada aún no es recomendada. Priorizar el "
               "monitoreo de los lotes listados en el Top 15 — son los que "
               "primero alcanzarán el umbral de cosecha. Re-correr este "
               "análisis cada 3-4 semanas para detectar el avance.")
    elif pol_mean_global < 13:
        rec = ("La hacienda se encuentra en <b>maduración temprana</b>. "
               "Algunos lotes ya pueden ser candidatos a cosecha "
               "(ver Top 15). Planificar logística de cosecha para los "
               "próximos 30-45 días.")
    else:
        rec = ("La hacienda se encuentra en <b>maduración avanzada o plena</b>. "
               "Iniciar cosecha por orden de prioridad (Top 15 primero).")
    story.append(Paragraph(rec, s_body))

    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Las páginas siguientes contienen:</b> (1) glosario técnico "
        "sobre Pol, y (2) reporte individual de cada lote con su mapa "
        "color e indicadores estadísticos, ordenados por Pol decreciente "
        "para facilitar la planificación de cosecha.", s_body))

    # Footer
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            f"Pixadvisor AP · Hacienda del Señor · "
            f"Reporte de Madurez Sacarosa · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}",
        )
        canvas.setStrokeColor(VERDE)
        canvas.setLineWidth(0.4)
        canvas.line(20 * mm, 13 * mm, A4[0] - 20 * mm, 13 * mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
# MAIN — merge final
# ════════════════════════════════════════════════════════════════════════════

def main():
    log("PIXADVISOR — Unificando reportes")
    if not CSV_STATS.exists():
        log(f"ERROR: falta CSV {CSV_STATS}")
        sys.exit(1)

    df = pd.read_csv(CSV_STATS)
    # Solo lotes con imagen
    df_ok = df[df["fecha_imagen"] != "sin_imagen"].copy()
    df_ok = df_ok.sort_values("POL_mean", ascending=False).reset_index(drop=True)
    log(f"Lotes con datos: {len(df_ok)}")

    # 1) Generar portada + resumen
    log("Generando portada + resumen ejecutivo")
    portada_bytes = build_portada_y_resumen(df_ok)
    portada_reader = PdfReader(BytesIO(portada_bytes))
    log(f"  páginas: {len(portada_reader.pages)}")

    # 2) Glosario
    if not GLOSARIO_PDF.exists():
        log(f"AVISO: glosario no encontrado en {GLOSARIO_PDF}, omito")
        glosario_reader = None
    else:
        glosario_reader = PdfReader(str(GLOSARIO_PDF))
        log(f"Glosario: {len(glosario_reader.pages)} pág")

    # 3) Reportes lote-a-lote en orden Pol descendente
    writer = PdfWriter()
    for p in portada_reader.pages:
        writer.add_page(p)
    if glosario_reader is not None:
        for p in glosario_reader.pages:
            writer.add_page(p)

    encontrados = 0
    faltantes = []
    for _, row in df_ok.iterrows():
        lote_id = row["lote_id"]
        fecha = row["fecha_imagen"]
        pdf_path = ROOT / lote_id / f"PIX_Sacarosa_{lote_id}_{fecha}.pdf"
        if not pdf_path.exists():
            faltantes.append(lote_id)
            continue
        try:
            r = PdfReader(str(pdf_path))
            for p in r.pages:
                writer.add_page(p)
            encontrados += 1
        except Exception as e:
            log(f"  × error con {lote_id}: {e}")
            faltantes.append(lote_id)

    log(f"Lotes incluidos: {encontrados}")
    if faltantes:
        log(f"Faltantes ({len(faltantes)}): {faltantes[:5]}...")

    # Bookmarks/outline rápido
    try:
        writer.add_outline_item("Portada", 0)
        writer.add_outline_item("Resumen ejecutivo", 1)
        gloss_start = len(portada_reader.pages)
        if glosario_reader is not None:
            writer.add_outline_item("Glosario Pol", gloss_start)
            lotes_start = gloss_start + len(glosario_reader.pages)
        else:
            lotes_start = gloss_start
        writer.add_outline_item(
            "Reportes lote-a-lote (Pol descendente)", lotes_start)
    except Exception:
        pass

    # Metadata
    writer.add_metadata({
        "/Title":   "Reporte Sacarosa Hacienda del Señor",
        "/Author":  "Pixadvisor AP",
        "/Subject": "Mapas de madurez por contenido de Pol estimado, "
                    "derivados de Sentinel-2A",
        "/Creator": "Pixadvisor Sacarosa Pipeline",
    })

    log(f"Escribiendo {OUT_PDF.name}")
    with open(OUT_PDF, "wb") as f:
        writer.write(f)

    size_mb = OUT_PDF.stat().st_size / 1024 / 1024
    total_pags = (len(portada_reader.pages)
                  + (len(glosario_reader.pages) if glosario_reader else 0)
                  + encontrados)
    log(f"OK → {OUT_PDF}")
    log(f"   tamaño: {size_mb:.1f} MB")
    log(f"   páginas totales: {total_pags}")


if __name__ == "__main__":
    main()
