#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIXADVISOR — Índice Maestro de Entregables
Hacienda del Señor — Prioridad de Cosecha 2026
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak)

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

OUT = Path(r"C:\Users\Usuario\Desktop\PIXADVISOR_INDICE_MAESTRO.pdf")

VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")
ROJO        = HexColor("#C62828")
NARANJA     = HexColor("#EF6C00")
AZUL        = HexColor("#1565C0")

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
            "agosto","septiembre","octubre","noviembre","diciembre"]
def fecha_es(d): return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


def main():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4,
        topMargin=15*mm, bottomMargin=15*mm,
        leftMargin=18*mm, rightMargin=18*mm,
        title="Índice Maestro Pixadvisor",
        author="Pixadvisor AP")

    s = getSampleStyleSheet()
    s_huge = ParagraphStyle("Huge", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=22, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=24)
    s_big = ParagraphStyle("Big", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=15, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=4, leading=17)
    s_h2 = ParagraphStyle("H2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=14)
    s_sub = ParagraphStyle("Sub", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=4, leading=13)
    s_body = ParagraphStyle("B", parent=s["Normal"],
        fontName="Helvetica", fontSize=9, textColor=GRIS, leading=12)

    story = []

    # Header
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_sub),
        Paragraph(f"<para align=right>Índice Maestro<br/>"
                   f"{datetime.now():%Y-%m-%d}</para>", s_sub)]]
    h_tbl = Table(header, colWidths=[100*mm, 70*mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LINEBELOW",(0,0),(-1,0),1.5,VERDE),
        ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(h_tbl); story.append(Spacer(1, 4))

    story.append(Paragraph("ÍNDICE MAESTRO DE ENTREGABLES", s_big))
    story.append(Paragraph("Hacienda del Señor — Zafra 2026", s_huge))
    story.append(Paragraph(
        "Sistema completo de prioridad de cosecha caña basado en "
        "Sentinel-2 + Sentinel-1 SAR + ERA5-Land + protocolo SASRI/CONSECANA "
        f"de validación in-situ. Generado el {fecha_es(datetime.now())}.",
        s_sub))
    story.append(Spacer(1, 6))

    # Tabla 1: Reportes de análisis
    story.append(Paragraph("📊 REPORTES DE ANÁLISIS (al cliente)", s_h2))
    rep = [
        ["Archivo", "Qué es", "Cuándo usar"],
        ["PIXADVISOR_RelatorioPrincipal.pdf",
         "Reporte v3 completo: 131 lotes confirmados como caña, ranking de prioridad de cosecha con S2+S1+ERA5, mapa global hacienda, 131 mapas individuales, justificación técnica con DOIs verificables.",
         "Entrega principal al cliente (139 págs · 33 MB)."],
        ["PIXADVISOR_Anexo_LotesExcluidos.pdf",
         "Anexo: lotes detectados como NO-caña (37 soya/pasto/monte/reforma) y lotes de caña con confianza media/baja (53). Justificación de cada exclusión.",
         "Anexo del relatorio principal. Soporta auditoría."],
    ]
    t = Table(rep, colWidths=[55*mm, 75*mm, 40*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("FONT",(0,1),(0,-1),"Helvetica-Bold",8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(t)
    story.append(Spacer(1, 6))

    # Tabla 2: Sistema muestreo in-situ
    story.append(Paragraph(
        "🌾 SISTEMA DE VALIDACIÓN IN-SITU TOP 20 LOTES", s_h2))
    mst = [
        ["Archivo", "Qué es", "Cuándo usar"],
        ["PIXADVISOR_PlanMuestreo_Top20.pdf",
         "Plan general: lista Top 20 con orden de visita, mapa global, protocolo SASRI/CONSECANA, interpretación CMI.",
         "Leer ANTES de salir al campo. Contexto general."],
        ["PIXADVISOR_Tutorial_Muestreo.pdf",
         "Tutorial paso a paso (7 págs): equipamiento, calibración refractómetro, cómo cargar KMZ/GeoTIFF en apps GPS, protocolo en campo, errores comunes, reglas de oro.",
         "Imprimir y llevar al campo. Especialmente útil para agrónomos nuevos en el procedimiento."],
        ["PIXADVISOR_Top20.kmz",
         "Archivo universal con los 20 polígonos de lote + 100 puntos GPS para muestreo. Compatible con Avenza Maps (gratis), Google Earth, Garmin, Locus Map, BackcountryNav.",
         "Cargar en GPS handheld o app móvil ANTES de salir al campo. Permite navegar a cada punto con GPS en tiempo real."],
        ["PIXADVISOR_MuestreoTop20_Datos.xlsx",
         "Excel template: hoja por lote con tabla 50 muestras (5 puntos × 10 tallos) + cálculo automático CMI por tallo, por punto, por lote + hoja RESUMEN ranking final + conditional formatting de colores.",
         "Llenar AL VOLVER de campo. CMI se calcula solo. Hoja RESUMEN da el ranking validado."],
    ]
    t2 = Table(mst, colWidths=[55*mm, 75*mm, 40*mm], repeatRows=1)
    t2.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("FONT",(0,1),(0,-1),"Helvetica-Bold",8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(t2)
    story.append(Spacer(1, 6))

    # Tabla 3: Carpetas con archivos por lote
    story.append(Paragraph(
        "📂 ARCHIVOS POR LOTE (en carpeta interna)", s_h2))
    story.append(Paragraph(
        "Ubicación: <b>Hacienda-Del-Senor\\05-Muestreo-InSitu-Top20\\</b>", s_body))
    car = [
        ["Subcarpeta", "Contenido"],
        ["01_E2/  hasta  20_B2/",
         "Una carpeta por lote ordenada por rank. Cada una contiene:\n"
         "• puntos_muestreo_LOTE.kml/.shp/.csv  → GPS handheld\n"
         "• mapa_campo_LOTE.png  → mapa de referencia\n"
         "• FICHA_CAMPO_LOTE.pdf  → ficha imprimible (2 págs) con tabla blanca para 50 mediciones"],
        ["AVENZA_MAPS/",
         "20 GeoTIFFs georreferenciados (AVENZA_##_LOTE.tif) con imagen Sentinel-2 RGB del lote + borde + 5 puntos numerados. Compatible Avenza Maps Pro, QGIS, ArcGIS."],
    ]
    t3 = Table(car, colWidths=[55*mm, 115*mm], repeatRows=1)
    t3.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("FONT",(0,1),(0,-1),"Helvetica-Bold",8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(t3)

    # PÁG 2 — FLUJO DE TRABAJO
    story.append(PageBreak())
    story.append(h_tbl); story.append(Spacer(1, 6))
    story.append(Paragraph("Flujo de trabajo recomendado", s_big))
    story.append(Spacer(1, 4))

    flujo = [
        ["#", "Etapa", "Archivos a usar", "Responsable", "Tiempo"],
        ["1", "Revisar reporte satelital v3 con cliente",
         "PIXADVISOR_RelatorioPrincipal.pdf",
         "Pixadvisor + Cliente", "1-2 hr"],
        ["2", "Acordar plan muestreo Top 20",
         "PIXADVISOR_PlanMuestreo_Top20.pdf",
         "Pixadvisor + Cliente", "30 min"],
        ["3", "Preparar equipo de campo (calibrar refractómetro, imprimir fichas, cargar KMZ en GPS)",
         "PIXADVISOR_Tutorial_Muestreo.pdf + PIXADVISOR_Top20.kmz",
         "Agrónomo", "2 hr (1 vez)"],
        ["4", "Visita en campo: 20 lotes × 30-45 min cada uno",
         "FICHA_CAMPO_LOTE.pdf (impresa) + Avenza con GeoTIFF + KMZ en GPS",
         "Agrónomo", "4-5 días"],
        ["5", "Ingreso de datos en oficina",
         "PIXADVISOR_MuestreoTop20_Datos.xlsx",
         "Agrónomo", "2-3 hr"],
        ["6", "Decisión final cosecha lote por lote",
         "Hoja RESUMEN del Excel + comparación con ranking v3",
         "Cliente + Pixadvisor", "1 hr"],
        ["7", "Cosecha programada",
         "Lista de lotes con CMI ≥ 85%",
         "Cliente", "según logística"],
        ["8", "Registro Pol post-cosecha (ingenio)",
         "Reportes CONSECANA del ingenio",
         "Cliente / Ingenio", "continuo"],
        ["9", "Re-correr pipeline cada 3-4 semanas",
         "compute_ranking_v3_s1.py + generar_reporte_v3_completo.py",
         "Pixadvisor", "30 min"],
    ]
    t_f = Table(flujo, colWidths=[8*mm, 40*mm, 60*mm, 32*mm, 25*mm], repeatRows=1)
    t_f.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(0,0),(0,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_f)
    story.append(Spacer(1, 8))

    # Resumen técnico
    story.append(Paragraph("Resumen técnico del sistema", s_h2))
    story.append(Paragraph(
        "<b>Composite v3:</b><br/>"
        "Score = −0.25·Z_NDWI − 0.15·Z_NDMI − 0.20·Z_CIRE + 0.10·Z_PSRI − 0.10·Z_VV_S1 + 0.20·Z_GDD<br/><br/>"
        "<b>Validación empírica local (Hacienda del Señor, n=131):</b><br/>"
        "Z_VV S1 vs Priority_score S2 → Spearman r = −0.529 (p&lt;0.001)<br/><br/>"
        "<b>Referencias DOI verificables:</b><br/>"
        "• Leandro 2024 Crops 4(3):333 → <i>10.3390/crops4030024</i><br/>"
        "• Bocca 2024 Sugar Tech → <i>10.1007/s12355-024-01468-z</i><br/>"
        "• Inman-Bamber 1994 Field Crops Res → <i>10.1016/0378-4290(94)90051-5</i><br/>"
        "• Meroni 2019 (JRC ASAP) → <i>10.1016/j.agsy.2018.07.002</i><br/>"
        "• Gao 1996 NDWI → <i>10.1016/S0034-4257(96)00067-3</i><br/>"
        "• Gitelson 2005 CIRE → <i>10.1029/2005GL022688</i><br/>"
        "• Merzlyak 1999 PSRI → <i>10.1034/j.1399-3054.1999.106119.x</i><br/><br/>"
        "<b>Lo que el sistema NO afirma:</b> Pol/Brix absoluto numérico. "
        "Para liquidación CONSECANA usar análisis polarimétrico de juice del ingenio.",
        s_body))
    story.append(Spacer(1, 6))

    # Roadmap futuro
    story.append(Paragraph("Roadmap futuro (próximas zafras)", s_h2))
    rm = [
        ["Plazo", "Acción", "Prioridad"],
        ["Zafra 2026 (en curso)",
         "Validar Top 20 con CMI in-situ. Re-correr pipeline cada 3-4 semanas.", "ALTA"],
        ["Post-zafra 2026",
         "Convenio con ingenio (Guabirá/UNAGRO/Aguaí) para 30-50 muestras Pol+Brix → calibración local progresiva.",
         "ALTA"],
        ["Zafra 2027",
         "Aplicar modelo CALIBRADO localmente (R² esperable 0.75-0.85). Pol absoluto defendible.",
         "ALTA"],
        ["Zafra 2027+",
         "Considerar EnMAP Cat-1 pilot técnico (upskilling para CHIME 2029).",
         "MEDIA"],
        ["2028-2030",
         "Evaluar CHIME (Copernicus): hyperspectral global gratuito, sucesor real de PRISMA/EnMAP.",
         "BAJA"],
    ]
    t_rm = Table(rm, colWidths=[35*mm, 110*mm, 25*mm], repeatRows=1)
    t_rm.setStyle(TableStyle([
        ("FONT",(0,0),(-1,0),"Helvetica-Bold",9),
        ("BACKGROUND",(0,0),(-1,0),VERDE),
        ("TEXTCOLOR",(0,0),(-1,0),white),
        ("FONT",(0,1),(-1,-1),"Helvetica",8),
        ("TEXTCOLOR",(0,1),(-1,-1),GRIS),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, GRIS_CLARO]),
        ("GRID",(0,0),(-1,-1),0.3,GRIS_LINEA),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ALIGN",(2,1),(2,-1),"CENTER"),
        ("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("TOPPADDING",(0,0),(-1,-1),3)]))
    story.append(t_rm)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Soporte y contacto", s_h2))
    story.append(Paragraph(
        "Pixadvisor AP — Agricultura de Precisión<br/>"
        "Nilton Camargo · gis.agronomico@gmail.com<br/>"
        "Toda la metodología y referencias en el reporte unificado "
        "<b>PIXADVISOR_RelatorioPrincipal.pdf</b>.",
        s_sub))

    def _f(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7); canvas.setFillColor(GRIS)
        canvas.drawCentredString(A4[0]/2, 10*mm,
            f"Pixadvisor AP · Índice Maestro Hacienda del Señor · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}")
        canvas.setStrokeColor(VERDE); canvas.setLineWidth(0.4)
        canvas.line(18*mm, 13*mm, A4[0]-18*mm, 13*mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_f, onLaterPages=_f)
    print(f"OK → {OUT}")


if __name__ == "__main__":
    main()
