#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genera PDF de glosario técnico explicando qué es Pol en caña de azúcar.
Branding Pixadvisor. Una página A4.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle)

OUTPUT_DIR = Path(
    r"C:\Users\Usuario\Desktop\PIXADVISOR\01-CLIENTES-PROYECTOS"
    r"\Hacienda-Del-Senor\04-Sacarosa-Sentinel2"
)
PDF_OUT = OUTPUT_DIR / "00_Glosario_POL_Pixadvisor.pdf"

VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#BDBDBD")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_OUT), pagesize=A4,
        topMargin=15 * mm, bottomMargin=18 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title="Glosario Pol — Pixadvisor",
        author="Pixadvisor AP",
    )

    s = getSampleStyleSheet()
    s_title = ParagraphStyle("PixTitle", parent=s["Title"],
        fontName="Helvetica-Bold", fontSize=20, textColor=VERDE,
        alignment=TA_LEFT, spaceAfter=2, leading=22)
    s_subtitle = ParagraphStyle("PixSub", parent=s["Normal"],
        fontName="Helvetica", fontSize=10, textColor=GRIS,
        alignment=TA_LEFT, spaceAfter=6, leading=13)
    s_h2 = ParagraphStyle("PixH2", parent=s["Heading2"],
        fontName="Helvetica-Bold", fontSize=12, textColor=VERDE,
        alignment=TA_LEFT, spaceBefore=8, spaceAfter=4, leading=14)
    s_body = ParagraphStyle("PixBody", parent=s["Normal"],
        fontName="Helvetica", fontSize=9.5, textColor=GRIS,
        leading=13, alignment=TA_JUSTIFY, spaceAfter=2)
    s_bullet = ParagraphStyle("PixBul", parent=s["Normal"],
        fontName="Helvetica", fontSize=9.5, textColor=GRIS,
        leading=13, leftIndent=14, bulletIndent=4, spaceAfter=1)

    story = []

    # Header
    header = [[
        Paragraph("<b>PIXADVISOR</b><br/>Agricultura de Precisión", s_subtitle),
        Paragraph(
            f"<para align=right>Glosario Técnico<br/>"
            f"{datetime.now():%Y-%m-%d}</para>", s_subtitle),
    ]]
    h_tbl = Table(header, colWidths=[110 * mm, 60 * mm])
    h_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, VERDE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(h_tbl)
    story.append(Spacer(1, 6))

    # Título
    story.append(Paragraph("Pol — Polarización en Caña de Azúcar", s_title))
    story.append(Paragraph(
        "Definición técnica, escala industrial e interpretación en los "
        "mapas Pixadvisor de Hacienda del Señor", s_subtitle))
    story.append(Spacer(1, 4))

    # Qué es
    story.append(Paragraph("¿Qué es Pol?", s_h2))
    story.append(Paragraph(
        "<b>Pol</b> (de <i>polarización</i>) es la medida estándar industrial "
        "del contenido de <b>sacarosa</b> en el jugo extraído del tallo de "
        "caña de azúcar. Se expresa como porcentaje en masa (%) sobre el "
        "jugo.", s_body))

    item = ParagraphStyle("Item", parent=s_body, leftIndent=14, bulletIndent=4)
    story.append(Paragraph(
        "<b>Método de medición:</b> sacarímetro polarímetro de laboratorio. "
        "La molécula de sacarosa es ópticamente activa y rota la luz "
        "polarizada en +66.5° por cada gramo disuelto en 100 mL de jugo. "
        "El ángulo medido es proporcional a la concentración.", item))
    story.append(Paragraph(
        "<b>Variable que paga el ingenio.</b> El sistema CONSECANA (Brasil) "
        "y equivalentes en Bolivia y Argentina usan Pol para calcular el "
        "<b>ATR</b> (Açúcar Total Recuperável) — los kg de azúcar "
        "recuperables por tonelada de caña entregada. A mayor Pol, mayor "
        "precio recibido por el productor.", item))

    # Escala
    story.append(Paragraph("Escala típica en caña madurando", s_h2))
    escala = [
        ["Pol %",     "Estado fenológico",                     "Decisión operativa"],
        ["8 – 10",    "Inmadura",                              "No cosechar"],
        ["10 – 12",   "Maduración temprana",                   "Monitorear semanalmente"],
        ["12 – 14",   "Maduración avanzada",                   "Planificar cosecha"],
        ["14 – 16",   "Maduración plena",                      "Cosecha óptima"],
        ["> 16",      "Sobre-maduración (raro)",               "Cosechar urgente — pérdida de Pol"],
    ]
    t_esc = Table(escala, colWidths=[25 * mm, 55 * mm, 75 * mm], repeatRows=1)
    t_esc.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), GRIS),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
    ]))
    story.append(t_esc)
    story.append(Spacer(1, 4))

    # Pol vs Brix vs Pureza
    story.append(Paragraph("Pol, Brix y Pureza — las tres métricas industriales", s_h2))
    comp = [
        ["Métrica",  "Qué mide",                                            "Cómo se mide",          "Rango típico"],
        ["Brix (°)", "Sólidos solubles totales (azúcares + otros)",         "Refractómetro",         "16 – 22 °Brix"],
        ["Pol (%)",  "Sacarosa aparente",                                   "Polarímetro",           "10 – 16 %"],
        ["Pureza",   "(Pol / Brix) x 100 — qué tan puro es el jugo",         "Cálculo",             "> 85 % (madura)"],
    ]
    t_comp = Table(comp, colWidths=[20 * mm, 65 * mm, 35 * mm, 35 * mm], repeatRows=1)
    t_comp.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), GRIS),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, GRIS_CLARO]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, GRIS_LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 4))

    # En los mapas Pixadvisor
    story.append(Paragraph(
        "¿Qué es el “Pol estimado” en los mapas Pixadvisor?", s_h2))
    story.append(Paragraph(
        "Los mapas y reportes PDF lote-a-lote de Pixadvisor muestran un "
        "<b>Pol estimado</b> que <u>no</u> es una medición de laboratorio: "
        "es una <b>predicción modelada</b> derivada de las bandas espectrales "
        "Sentinel-2 (verde B3, NIR B8/B8A y SWIR B11) mediante la regresión "
        "lineal de <b>Canata et al. (2024)</b>:", s_body))
    story.append(Paragraph(
        "Pol(%) = 8.94 − 6.76 · NDWI + 2.69 · GNDVI + 3.7e-5 · B3",
        ParagraphStyle("Form", parent=s_body, fontName="Helvetica-Oblique",
                        alignment=TA_LEFT, leftIndent=20, spaceBefore=2,
                        spaceAfter=4, textColor=VERDE)))
    story.append(Paragraph(
        "donde NDWI = (B8A − B11)/(B8A + B11) representa el contenido de "
        "agua foliar (cae cuando la caña madura) y GNDVI = (B8 − B3)/(B8 + B3) "
        "representa la actividad clorofílica.", s_body))

    story.append(Paragraph(
        "<b>Precisión esperable:</b> R² absoluto de 0.55–0.70 contra Pol de "
        "laboratorio. El mapa funciona principalmente como <b>indicador "
        "RELATIVO</b> de madurez: zonas más verdes dentro de un lote indican "
        "mayor Pol que zonas más rojas. Para Pol absoluto a nivel industrial "
        "se requiere calibración local con &gt;30 muestras de jugo "
        "CONSECANA-equivalentes.", s_body))

    story.append(Paragraph(
        "<b>Uso operativo recomendado:</b> ordenar la secuencia de cosecha "
        "por Pol estimado descendente (los lotes con Pol más alto primero), "
        "y dentro de un lote heterogéneo cosechar primero las zonas que "
        "aparecen en verde en el mapa.", s_body))

    # Footer
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS)
        canvas.drawCentredString(
            A4[0] / 2, 10 * mm,
            f"Pixadvisor AP · Glosario Técnico · "
            f"{datetime.now():%Y-%m-%d} · pág {doc_.page}",
        )
        canvas.setStrokeColor(VERDE)
        canvas.setLineWidth(0.4)
        canvas.line(20 * mm, 13 * mm, A4[0] - 20 * mm, 13 * mm)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    print(f"PDF: {PDF_OUT}")


if __name__ == "__main__":
    main()
