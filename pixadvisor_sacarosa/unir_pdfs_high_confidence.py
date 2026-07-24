#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
============================================================================
PIXADVISOR — Reporte FINAL HIGH-CONFIDENCE para cliente
============================================================================
Reconstruye CSV consolidado leyendo los TIFs Pol existentes (más confiable
que recalcular desde GEE) y genera el PDF unificado solo con lotes
clasificados como CAÑA con confianza HIGH.

Salidas:
  pix_sacarosa_HIGH_<fecha>.csv
  RELATORIO_FINAL_HIGH_Sacarosa_Hacienda_del_Senor_<fecha>.pdf
  Anexo_NO_cana_<fecha>.pdf  → lotes excluidos con justificación
============================================================================
"""
from __future__ import annotations
import re
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pypdf import PdfReader, PdfWriter

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ════════════════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════════════════
ROOT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
            r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2")
CSV_CLAS = ROOT / "clasificacion_lotes_2026-05-13.csv"
GLOSARIO = ROOT / "00_Glosario_POL_Pixadvisor.pdf"

CLIENTE = "Hacienda del Señor"
UBICACION = "Santa Cruz, Bolivia"

VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")
NARANJA     = HexColor("#EF6C00")

CANA_CATS = {"CAÑA_ACTIVA", "CAÑA_SOCA",
             "CAÑA_PRE_COSECHA_RECIENTE", "CAÑA_INMADURA_NUEVA"}
MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]


def log(m): print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)
def fecha_es(d): return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


# ════════════════════════════════════════════════════════════════════════════
# RECONSTRUIR STATS LEYENDO TIFs
# ════════════════════════════════════════════════════════════════════════════
def stats_desde_tif(tif: Path) -> dict | None:
    try:
        with rasterio.open(tif) as src:
            arr = src.read(1).astype(float)
            nd = src.nodata if src.nodata is not None else -9999
            mask = (arr == nd) | np.isnan(arr)
            v = arr[~mask]
            if v.size < 3: return None
            return {
                "POL_mean":   float(v.mean()),
                "POL_min":    float(v.min()),
                "POL_max":    float(v.max()),
                "POL_stdDev": float(v.std()),
                "POL_p10":    float(np.percentile(v, 10)),
                "POL_p25":    float(np.percentile(v, 25)),
                "POL_p50":    float(np.percentile(v, 50)),
                "POL_p75":    float(np.percentile(v, 75)),
                "POL_p90":    float(np.percentile(v, 90)),
                "n_pixeles":  int(v.size),
            }
    except Exception as e:
        log(f"  × stats {tif.name}: {e}")
        return None


def reconstruir_csv(df_clas_high: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, lote in df_clas_high.iterrows():
        lid = str(lote["lote_id"])
        ldir = ROOT / lid
        if not ldir.exists():
            log(f"  ! sin carpeta: {lid}")
            continue
        tifs = sorted(ldir.glob("POL_*.tif"))
        if not tifs:
            log(f"  ! sin TIF Pol: {lid}")
            continue
        tif = tifs[-1]
        m = re.match(r"POL_(.+)_(\d{4}-\d{2}-\d{2})\.tif$", tif.name)
        fecha = m.group(2) if m else "—"
        st = stats_desde_tif(tif)
        if st is None: continue

        # Brix (si existe)
        btifs = sorted(ldir.glob("BRIX_*.tif"))
        bmean = None
        if btifs:
            bs = stats_desde_tif(btifs[-1])
            bmean = bs["POL_mean"] if bs else None

        rows.append({
            "lote_id":      lid,
            "area_ha":      float(lote["area_ha"]),
            "categoria":    str(lote["categoria"]),
            "confianza":    str(lote["confianza"]),
            "nota_clas":    str(lote["nota"]),
            "fecha_imagen": fecha,
            "BRIX_mean":    bmean,
            **st,
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("POL_mean", ascending=False).reset_index(drop=True)
    return df


# ════════════════════════════════════════════════════════════════════════════
# PORTADA + RESUMEN EJECUTIVO HIGH
# ════════════════════════════════════════════════════════════════════════════
def build_intro(df: pd.DataFrame, df_clas: pd.DataFrame) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Reporte FINAL Sacarosa — HIGH confidence",
        author="Pixadvisor AP",
    )

    s = getSampleStyleSheet()
    s_huge = ParagraphStyle("Huge", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=28, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=8, leading=32)
    s_big = ParagraphStyle("Big", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=20)
    s_subtitle = ParagraphStyle("PixSub", parent=s["Normal"],
        fontName="Helvetica", fontSize=11, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=14)
    s_h2 = ParagraphStyle("PixH2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=13, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=10, spaceAfter=6, leading=15)
    s_body = ParagraphStyle("PixBody", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS, leading=13)
    s_warn = ParagraphStyle("PixWarn", parent=s["Normal"],
        fontName="Helvetica-Bold", fontSize=10, textColor=ROJO, leading=13)

    story = []

    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_subtitle),
        Paragraph(f"<para align=right>{datetime.now():%Y-%m-%d}</para>", s_subtitle),
    ]]
    h_tbl = Table(header, colWidths=[110 * mm, 60 * mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LINEBELOW", (0,0), (-1,0), 1.5, VERDE),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(h_tbl)
    story.append(Spacer(1, 35 * mm))

    story.append(Paragraph("REPORTE FINAL DE MADUREZ", s_big))
    story.append(Paragraph("Índice de Sacarosa por Lote", s_huge))
    story.append(Paragraph(
        "<font color='#1B5E20'><b>Solo lotes con CAÑA confirmada · "
        "Confianza HIGH</b></font>", s_subtitle))
    story.append(Spacer(1, 15 * mm))

    es_high = df_clas['categoria'].isin(CANA_CATS) & (df_clas['confianza']=='HIGH')
    no_cana = df_clas[~df_clas['categoria'].isin(CANA_CATS)]
    medium_low = df_clas[df_clas['categoria'].isin(CANA_CATS) & (df_clas['confianza']!='HIGH')]

    meta = [
        ["Cliente",                CLIENTE],
        ["Ubicación",              UBICACION],
        ["Cultivo objetivo",       "Caña de azúcar"],
        ["Sensor",                 "Sentinel-2A (ESA Copernicus)"],
        ["Modelo Pol",             "Canata et al. (2024)"],
        ["Clasificación cobertura","Firma fenológica NDVI 14 meses"],
        ["Lotes en hacienda",      f"{len(df_clas)}"],
        ["Lotes en este reporte",  f"{len(df)}  (HIGH confidence)"],
        ["Hectáreas analizadas",   f"{df['area_ha'].sum():,.0f} ha"],
        ["Lotes excluidos",        f"{len(no_cana)} no-caña + "
                                   f"{len(medium_low)} caña confianza media/baja"],
        ["Fecha del reporte",      fecha_es(datetime.now())],
    ]
    t_meta = Table(meta, colWidths=[58 * mm, 107 * mm])
    t_meta.setStyle(TableStyle([
        ("FONT", (0,0), (-1,-1), "Helvetica", 10),
        ("FONT", (0,0), (0,-1), "Helvetica-Bold", 10),
        ("TEXTCOLOR", (0,0), (0,-1), VERDE),
        ("TEXTCOLOR", (1,0), (1,-1), GRIS),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("LINEBELOW", (0,0), (-1,-1), 0.3, GRIS_LINEA),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 25 * mm))
    story.append(Paragraph(
        "<b>Garantía de calidad:</b> antes de aplicar el modelo Pol, todos "
        "los lotes fueron filtrados por <b>clasificación automática de "
        "cobertura</b> usando 14 meses de Sentinel-2 NDVI. Solo se "
        "incluyen aquí los lotes con firma fenológica de caña validada. "
        "Lotes con soya, pasto, monte o reforma fueron excluidos para "
        "garantizar la confiabilidad del Pol estimado.", s_body))
    story.append(PageBreak())

    # ═══ Resumen ejecutivo
    story.append(h_tbl)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Resumen Ejecutivo", s_big))
    story.append(Paragraph(
        f"Madurez de la caña al {datetime.now():%Y-%m-%d} · "
        f"{len(df)} lotes · {df['area_ha'].sum():,.0f} ha", s_subtitle))
    story.append(Spacer(1, 6))

    # Auditoría: qué se filtró
    story.append(Paragraph(
        "Auditoría de cobertura — qué se procesó y qué se excluyó", s_h2))
    aud = df_clas.groupby(["categoria", "confianza"]).agg(
        n=("lote_id", "count"), ha=("area_ha", "sum")).reset_index()
    aud_rows = [["Categoría", "Confianza", "# Lotes", "Hectáreas", "En reporte"]]
    for _, r in aud.iterrows():
        en_rep = "SÍ" if r["categoria"] in CANA_CATS and r["confianza"]=="HIGH" else "NO"
        aud_rows.append([str(r["categoria"]), str(r["confianza"]),
                         f"{int(r['n'])}", f"{r['ha']:,.0f}", en_rep])
    t_aud = Table(aud_rows, colWidths=[55*mm, 20*mm, 18*mm, 28*mm, 22*mm], repeatRows=1)
    t_aud.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0,0), (-1,0), VERDE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONT", (0,1), (-1,-1), "Helvetica", 8.5),
        ("TEXTCOLOR", (0,1), (-1,-1), GRIS),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
        ("GRID", (0,0), (-1,-1), 0.3, GRIS_LINEA),
        ("ALIGN", (2,1), (-1,-1), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t_aud)
    story.append(Spacer(1, 8))

    # KPIs
    story.append(Paragraph("KPIs HIGH-confidence", s_h2))
    pol_mean = df["POL_mean"].mean()
    pol_min = df["POL_mean"].min()
    pol_max = df["POL_mean"].max()
    pol_std = df["POL_mean"].std()
    area_tot = df["area_ha"].sum()
    kpis = [
        ["Lotes incluidos",       f"{len(df)}",            "CAÑA confirmada HIGH"],
        ["Área caña confirmada",  f"{area_tot:,.0f} ha",   "100% verificado"],
        ["Pol estimado medio",    f"{pol_mean:.2f} %",     "Promedio entre lotes"],
        ["Rango Pol entre lotes", f"{pol_min:.2f}–{pol_max:.2f} %", "Heterogeneidad"],
        ["Desvío entre lotes",    f"{pol_std:.2f} %",      "Variabilidad inter-lote"],
    ]
    t_kpi = Table(kpis, colWidths=[55*mm, 40*mm, 65*mm])
    t_kpi.setStyle(TableStyle([
        ("FONT", (0,0), (-1,-1), "Helvetica", 10),
        ("FONT", (0,0), (0,-1), "Helvetica-Bold", 10),
        ("FONT", (1,0), (1,-1), "Helvetica-Bold", 11),
        ("TEXTCOLOR", (0,0), (0,-1), VERDE),
        ("TEXTCOLOR", (1,0), (1,-1), GRIS),
        ("TEXTCOLOR", (2,0), (2,-1), GRIS),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("LINEBELOW", (0,0), (-1,-1), 0.3, GRIS_LINEA),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 8))

    # Distribución
    story.append(Paragraph("Distribución por madurez", s_h2))
    bins = [-1e9, 9, 10, 11, 12, 14, 1e9]
    labels = ["< 9% muy inmaduro", "9–10% inmaduro",
              "10–11% temprano", "11–12% medio",
              "12–14% avanzado", "> 14% cosecha óptima"]
    df["cat_pol"] = pd.cut(df["POL_mean"], bins=bins, labels=labels)
    dist = df.groupby("cat_pol", observed=True).agg(
        n=("lote_id", "count"), ha=("area_ha", "sum")).reset_index()
    dist["pct_ha"] = dist["ha"] / dist["ha"].sum() * 100
    dist_rows = [["Categoría", "# Lotes", "Hectáreas", "% del área"]]
    for _, r in dist.iterrows():
        dist_rows.append([str(r["cat_pol"]), f"{int(r['n'])}",
                          f"{r['ha']:,.1f}", f"{r['pct_ha']:.1f} %"])
    t_dist = Table(dist_rows, colWidths=[60*mm, 25*mm, 35*mm, 28*mm], repeatRows=1)
    t_dist.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0,0), (-1,0), VERDE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONT", (0,1), (-1,-1), "Helvetica", 9),
        ("TEXTCOLOR", (0,1), (-1,-1), GRIS),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
        ("GRID", (0,0), (-1,-1), 0.3, GRIS_LINEA),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
    ]))
    story.append(t_dist)
    story.append(Spacer(1, 8))

    # Top 15
    story.append(Paragraph(
        "Top 15 lotes — prioridad de cosecha (Pol descendente)", s_h2))
    top = df.head(15).reset_index(drop=True)
    top_rows = [["#", "Lote", "Área (ha)", "Pol %", "Desvío %", "Fecha S2A"]]
    for i, r in top.iterrows():
        top_rows.append([
            str(i+1), str(r["lote_id"]), f"{r['area_ha']:,.2f}",
            f"{r['POL_mean']:.2f}", f"{r['POL_stdDev']:.2f}",
            str(r["fecha_imagen"])])
    t_top = Table(top_rows,
                  colWidths=[10*mm, 32*mm, 28*mm, 22*mm, 22*mm, 28*mm],
                  repeatRows=1)
    t_top.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0,0), (-1,0), VERDE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONT", (0,1), (-1,-1), "Helvetica", 9),
        ("TEXTCOLOR", (0,1), (-1,-1), GRIS),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
        ("GRID", (0,0), (-1,-1), 0.3, GRIS_LINEA),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("ALIGN", (2,1), (-1,-1), "RIGHT"),
        ("ALIGN", (0,0), (0,-1), "CENTER"),
    ]))
    story.append(t_top)
    story.append(Spacer(1, 8))

    # Recomendación
    story.append(Paragraph("Recomendación general", s_h2))
    if pol_mean < 11:
        rec = ("La caña confirmada se encuentra en fase de "
               "<b>pre-maduración</b>. Cosecha generalizada aún no "
               "recomendada. Priorizar monitoreo de lotes Top 15. "
               "Re-correr análisis cada 3-4 semanas para detectar avance.")
    elif pol_mean < 13:
        rec = ("Caña en <b>maduración temprana</b>. Algunos lotes ya son "
               "candidatos. Planificar logística para próximos 30-45 días.")
    else:
        rec = ("Caña en <b>maduración avanzada</b>. Iniciar cosecha por "
               "orden de prioridad (Top 15 primero).")
    story.append(Paragraph(rec, s_body))

    # Footer
    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS)
        canvas.drawCentredString(
            A4[0]/2, 10*mm,
            f"Pixadvisor AP · Hacienda del Señor · Reporte FINAL "
            f"HIGH confidence · {datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE)
        canvas.setLineWidth(0.4)
        canvas.line(20*mm, 13*mm, A4[0]-20*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
# ANEXO NO-CAÑA (justificación de exclusiones)
# ════════════════════════════════════════════════════════════════════════════
def build_anexo_no_cana(df_clas: pd.DataFrame) -> bytes:
    no_cana = df_clas[~df_clas['categoria'].isin(CANA_CATS)].copy()
    medium_low = df_clas[df_clas['categoria'].isin(CANA_CATS) &
                          (df_clas['confianza']!='HIGH')].copy()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=15*mm, bottomMargin=18*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="Anexo — Lotes excluidos del reporte HIGH",
        author="Pixadvisor AP")
    s = getSampleStyleSheet()
    s_title = ParagraphStyle("T", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=20)
    s_sub = ParagraphStyle("S", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=14)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS, leading=12)

    story = []

    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Anexo · {datetime.now():%Y-%m-%d}</para>", s_sub),
    ]]
    h_tbl = Table(header, colWidths=[110*mm, 60*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LINEBELOW", (0,0), (-1,0), 1.5, VERDE),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(h_tbl)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Anexo — Lotes excluidos del reporte", s_title))
    story.append(Paragraph(
        "Resultados de la clasificación automática de cobertura "
        "(Sentinel-2 NDVI 14 meses) que justifican por qué cada lote "
        "fue excluido del reporte principal.", s_sub))
    story.append(Spacer(1, 6))

    # Sección 1: NO-caña
    story.append(Paragraph(
        f"Lotes detectados como NO-caña ({len(no_cana)} lotes · "
        f"{no_cana['area_ha'].sum():,.0f} ha)", s_h2))

    no_cana = no_cana.sort_values(["categoria", "area_ha"], ascending=[True, False])
    rows = [["Lote", "Área (ha)", "Categoría", "Justificación NDVI"]]
    for _, r in no_cana.iterrows():
        rows.append([str(r["lote_id"]), f"{r['area_ha']:,.1f}",
                     str(r["categoria"]), str(r["nota"])[:90]])
    t = Table(rows, colWidths=[28*mm, 18*mm, 42*mm, 86*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0,0), (-1,0), "Helvetica-Bold", 8),
        ("BACKGROUND", (0,0), (-1,0), VERDE),
        ("TEXTCOLOR", (0,0), (-1,0), white),
        ("FONT", (0,1), (-1,-1), "Helvetica", 7.5),
        ("TEXTCOLOR", (0,1), (-1,-1), GRIS),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
        ("GRID", (0,0), (-1,-1), 0.2, GRIS_LINEA),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("ALIGN", (1,1), (1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(t)

    if len(medium_low) > 0:
        story.append(PageBreak())
        story.append(h_tbl)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Lotes con CAÑA — confianza media o baja "
            f"({len(medium_low)} lotes · "
            f"{medium_low['area_ha'].sum():,.0f} ha)", s_h2))
        story.append(Paragraph(
            "Estos lotes muestran patrón fenológico compatible con caña "
            "pero sin firma definitiva. <b>Verificar visita a campo</b> "
            "antes de incluirlos en próximo reporte.", s_body))
        story.append(Spacer(1, 4))
        ml = medium_low.sort_values("area_ha", ascending=False)
        rows2 = [["Lote", "Área (ha)", "Categoría", "Confianza", "Nota NDVI"]]
        for _, r in ml.iterrows():
            rows2.append([str(r["lote_id"]), f"{r['area_ha']:,.1f}",
                          str(r["categoria"]), str(r["confianza"]),
                          str(r["nota"])[:75]])
        t2 = Table(rows2, colWidths=[26*mm, 18*mm, 38*mm, 18*mm, 74*mm], repeatRows=1)
        t2.setStyle(TableStyle([
            ("FONT", (0,0), (-1,0), "Helvetica-Bold", 8),
            ("BACKGROUND", (0,0), (-1,0), VERDE),
            ("TEXTCOLOR", (0,0), (-1,0), white),
            ("FONT", (0,1), (-1,-1), "Helvetica", 7.5),
            ("TEXTCOLOR", (0,1), (-1,-1), GRIS),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [white, GRIS_CLARO]),
            ("GRID", (0,0), (-1,-1), 0.2, GRIS_LINEA),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("ALIGN", (1,1), (1,-1), "RIGHT"),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(t2)

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Anexo Lotes Excluidos · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("=== Pixadvisor — Reporte FINAL HIGH-confidence ===")
    if not CSV_CLAS.exists():
        log(f"ERROR: falta {CSV_CLAS}"); sys.exit(1)

    df_clas = pd.read_csv(CSV_CLAS)
    es_high = df_clas['categoria'].isin(CANA_CATS) & (df_clas['confianza']=='HIGH')
    df_high_cls = df_clas[es_high].copy()
    log(f"Clasificación cargada: {len(df_clas)} lotes total · "
        f"{len(df_high_cls)} HIGH-caña")

    log("Reconstruyendo stats desde TIFs Pol existentes...")
    df = reconstruir_csv(df_high_cls)
    log(f"  → stats reconstruidos: {len(df)} lotes")

    fecha = datetime.now().strftime("%Y-%m-%d")
    csv_out = ROOT / f"pix_sacarosa_HIGH_{fecha}.csv"
    df.to_csv(csv_out, index=False)
    log(f"  → CSV: {csv_out.name}")

    # Generar portada+resumen
    log("Generando portada + resumen ejecutivo...")
    intro_pdf = build_intro(df, df_clas)
    intro_reader = PdfReader(BytesIO(intro_pdf))
    log(f"  páginas: {len(intro_reader.pages)}")

    # Glosario
    if GLOSARIO.exists():
        gloss = PdfReader(str(GLOSARIO))
        log(f"  glosario: {len(gloss.pages)} pág")
    else: gloss = None

    # Anexo
    log("Generando anexo NO-caña...")
    anexo_pdf = build_anexo_no_cana(df_clas)
    anexo_reader = PdfReader(BytesIO(anexo_pdf))
    log(f"  páginas anexo: {len(anexo_reader.pages)}")
    anexo_path = ROOT / f"Anexo_Lotes_Excluidos_{fecha}.pdf"
    with open(anexo_path, "wb") as f:
        f.write(anexo_pdf)
    log(f"  → anexo: {anexo_path.name}")

    # Merge final
    writer = PdfWriter()
    for p in intro_reader.pages: writer.add_page(p)
    if gloss:
        for p in gloss.pages: writer.add_page(p)

    incluidos = 0
    for _, row in df.iterrows():
        lid = str(row["lote_id"])
        fecha_img = row["fecha_imagen"]
        pdf_path = ROOT / lid / f"PIX_Sacarosa_{lid}_{fecha_img}.pdf"
        if not pdf_path.exists(): continue
        try:
            r = PdfReader(str(pdf_path))
            for p in r.pages: writer.add_page(p)
            incluidos += 1
        except Exception as e:
            log(f"  × {lid}: {e}")

    # Anexo al final
    for p in anexo_reader.pages: writer.add_page(p)

    # Bookmarks
    try:
        writer.add_outline_item("Portada", 0)
        writer.add_outline_item("Resumen ejecutivo", 1)
        offset = len(intro_reader.pages)
        if gloss:
            writer.add_outline_item("Glosario Pol", offset)
            offset += len(gloss.pages)
        writer.add_outline_item(
            "Reportes lote-a-lote (Pol descendente)", offset)
        # Final del documento donde inicia anexo
        writer.add_outline_item("Anexo: lotes excluidos",
                                 offset + incluidos)
    except Exception as e:
        log(f"  ! bookmarks: {e}")

    writer.add_metadata({
        "/Title": "Reporte FINAL Sacarosa HIGH-confidence — Hacienda del Señor",
        "/Author": "Pixadvisor AP",
        "/Subject": "Madurez Pol caña con clasificación previa de cobertura",
        "/Creator": "Pixadvisor Sacarosa Pipeline v2",
    })

    out = ROOT / f"RELATORIO_FINAL_HIGH_Sacarosa_Hacienda_del_Senor_{fecha}.pdf"
    with open(out, "wb") as f: writer.write(f)

    size_mb = out.stat().st_size / 1024 / 1024
    total_pags = (len(intro_reader.pages)
                  + (len(gloss.pages) if gloss else 0)
                  + incluidos
                  + len(anexo_reader.pages))
    log(f"OK → {out.name}")
    log(f"   tamaño: {size_mb:.1f} MB · páginas: {total_pags} · "
        f"lotes HIGH incluidos: {incluidos}")


if __name__ == "__main__":
    main()
