"""Build corrected MDO AGRO authorization letter for PIXADVISOR S.R.L."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PIL import Image as PILImage

OUT = r"D:\PIXADVISOR_AGENT_WORKSPACE\Autorizacion_MDO_Agro_Pixadvisor.pdf"
LOGO = r"D:\PIXADVISOR_AGENT_WORKSPACE\mdo_logo_hd.png"
STAMP = r"D:\PIXADVISOR_AGENT_WORKSPACE\stamp_digital_hd.png"

# Page geometry
PAGE_W, PAGE_H = A4
MARGIN_L = 2.5 * cm
MARGIN_R = 2.5 * cm
MARGIN_T = 2.5 * cm
MARGIN_B = 2.0 * cm

# Logo dimensions (proportional)
logo_img = PILImage.open(LOGO)
logo_w_orig, logo_h_orig = logo_img.size
LOGO_W = 5.5 * cm
LOGO_H = LOGO_W * logo_h_orig / logo_w_orig

# Stamp dimensions
stamp_img = PILImage.open(STAMP)
stamp_w_orig, stamp_h_orig = stamp_img.size
STAMP_W = 7.5 * cm
STAMP_H = STAMP_W * stamp_h_orig / stamp_w_orig


def draw_static(c: canvas.Canvas, doc):
    """Draw logo (top-left) and stamp (bottom-right) on every page."""
    # Top-left logo
    c.drawImage(
        LOGO,
        MARGIN_L,
        PAGE_H - MARGIN_T - LOGO_H + 0.3 * cm,
        width=LOGO_W,
        height=LOGO_H,
        mask="auto",
    )
    # Bottom-right stamp
    c.drawImage(
        STAMP,
        PAGE_W - MARGIN_R - STAMP_W,
        MARGIN_B,
        width=STAMP_W,
        height=STAMP_H,
        mask="auto",
    )


styles = getSampleStyleSheet()
body_style = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    leading=16,
    alignment=TA_JUSTIFY,
    spaceAfter=10,
)
left_style = ParagraphStyle(
    "Left",
    parent=body_style,
    alignment=TA_LEFT,
    spaceAfter=4,
)
title_style = ParagraphStyle(
    "Title",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    alignment=TA_CENTER,
    spaceAfter=14,
    spaceBefore=10,
)
center_style = ParagraphStyle(
    "Center",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=11,
    leading=15,
    alignment=TA_CENTER,
    spaceAfter=4,
)
center_bold = ParagraphStyle(
    "CenterBold",
    parent=center_style,
    fontName="Helvetica-Bold",
    fontSize=12,
    spaceAfter=8,
)
product_style = ParagraphStyle(
    "Product",
    parent=styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    alignment=TA_LEFT,
    spaceAfter=8,
    spaceBefore=4,
)


doc = SimpleDocTemplate(
    OUT,
    pagesize=A4,
    leftMargin=MARGIN_L,
    rightMargin=MARGIN_R,
    topMargin=MARGIN_T + LOGO_H + 0.5 * cm,  # leave space for logo
    bottomMargin=MARGIN_B + STAMP_H + 0.4 * cm,  # leave space for stamp
)

story = []

# Header recipient block
story.append(Paragraph("Respetados Se&#241;ores", left_style))
story.append(Paragraph(
    "Servicio Nacional de Sanidad Agropecuaria e Inocuidad Alimentaria &#8211; SENASAG",
    left_style,
))
story.append(Paragraph("Santa Cruz &#8211; Bol&#237;via", left_style))
story.append(Spacer(1, 0.6 * cm))

# Title
story.append(Paragraph("CARTA DE AUTORIZACI&#211;N", title_style))

# Main body — corrected text per user request
body = (
    "Mediante la presente, certificamos ante ustedes que la empresa "
    "<b>PIXADVISOR S.R.L</b>, NIT <b>527663028</b>, est&#225; autorizada por "
    "parte de <b>MDO AGRO INDUSTRIA LTDA</b>, CNPJ <b>44631321/0001-60</b>, "
    "a utilizar como importaci&#243;n, distribuci&#243;n y comercializaci&#243;n; "
    "dentro de Estado plurinacional de Bolivia, el fertilizante detallado a "
    "continuaci&#243;n, propio de: <b>MDO AGRO INDUSTRIA LTDA</b>, "
    "CNPJ <b>44631321/0001-60</b>, siendo el producto a incorporar lo que "
    "figura la siguiente relaci&#243;n:"
)
story.append(Paragraph(body, body_style))
story.append(Spacer(1, 0.5 * cm))

# Product details
product_block = [
    Paragraph("MAXX PIROL &#8211; EXTRACTO PIROLE&#209;OSO", product_style),
    Paragraph("LOTE: 11/023", left_style),
    Paragraph("FABRICACI&#211;N: 20-06-2025", left_style),
    Paragraph("VALIDEZ: 20/06/2027", left_style),
]
story.append(KeepTogether(product_block))
story.append(Spacer(1, 0.6 * cm))

# Closing
closing = (
    "Agradeciendo de antemano la gentil atenci&#243;n prestada a la presente, "
    "les expresamos nuestros m&#225;s sinceros agradecimientos."
)
story.append(Paragraph(closing, body_style))
story.append(Spacer(1, 1.2 * cm))

# Company footer (centered)
story.append(Paragraph("MDO AGRO INDUSTRIA LTDA", center_bold))
story.append(Paragraph("AVENIDA MERCOSUL, 1.474, PARQUE INDUSTRIAL", center_style))
story.append(Paragraph("CEP: 87600000 &#8211; NOVA ESPERAN&#199;A &#8211; PARAN&#193;", center_style))
story.append(Paragraph("TELEFONE: 44-97400-9877", center_style))
story.append(Paragraph("WWW.MDOAGRO.COM.BR", center_style))

doc.build(story, onFirstPage=draw_static, onLaterPages=draw_static)
print(f"Built: {OUT}")
