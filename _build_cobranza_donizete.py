# -*- coding: utf-8 -*-
"""
Informe de Cobranza - Cliente Donizete Fernandes
Pixadvisor - Agricultura de Precision
Genera un PDF profesional de cobranza (reembolso de gastos).
Regenerable. NO usa Unicode sub/superscript ni flechas (->) que rompen WinAnsi.
"""
import os
from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, KeepTogether)

# ---- Branding Pixadvisor ----
VERDE       = HexColor("#1B5E20")
VERDE_CLARO = HexColor("#4CAF50")
GRIS        = HexColor("#333333")
GRIS_CLARO  = HexColor("#F5F5F5")
GRIS_LINEA  = HexColor("#D9D9D9")

# ---- Datos del documento ----
FECHA_LARGA = "02 de junio de 2026"
FECHA_CORTA = "02/06/2026"
DOC_NUM     = "COB-2026-0602"
CLIENTE     = "Sr. Donizete Fernandes"

# IT 3% calculado EXACTAMENTE desde la base de cada factura (redondeo financiero)
def _it3(base):
    return float((Decimal(str(base)) * Decimal("0.03")).quantize(Decimal("0.01"),
                 rounding=ROUND_HALF_UP))

BASE1, BASE3, BASE4 = 633278.44, 206208.50, 168894.25      # facturas con IT 3%
IT1, IT3, IT4       = _it3(BASE1), _it3(BASE3), _it3(BASE4) # 18998.35 / 6186.26 / 5066.83
FLETE, ANALISIS     = 1800.00, 2800.00                      # montos fijos (sin IT)
TOTAL = round(IT1 + FLETE + IT3 + IT4 + ANALISIS, 2)        # 34851.44

OUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop",
                       "PIXADVISOR_Cobranza_Donizete_Fernandes_2026-06-02")
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PDF = os.path.join(OUT_DIR, "Informe_Cobranza_Donizete_Fernandes_2026-06-02.pdf")

MARGIN = 0.8 * inch

def bs(x):
    return f"Bs {x:,.2f}"

# ---- Estilos ----
ss = getSampleStyleSheet()
st_title = ParagraphStyle("PixTitle", parent=ss["Title"], fontName="Helvetica-Bold",
                          fontSize=19, textColor=VERDE, spaceAfter=2, alignment=TA_LEFT, leading=21)
st_sub   = ParagraphStyle("PixSub", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=9.5, textColor=GRIS, spaceAfter=7, alignment=TA_LEFT)
st_h2    = ParagraphStyle("PixH2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                          fontSize=12, textColor=VERDE, spaceBefore=9, spaceAfter=4)
st_body  = ParagraphStyle("PixBody", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=10, textColor=GRIS, alignment=TA_JUSTIFY, leading=13.5, spaceAfter=4)
st_note  = ParagraphStyle("PixNote", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=8.6, textColor=GRIS, alignment=TA_JUSTIFY, leading=11, spaceAfter=3)
st_meta_l = ParagraphStyle("MetaL", parent=ss["Normal"], fontName="Helvetica-Bold",
                           fontSize=9.5, textColor=VERDE, leading=13)
st_meta_v = ParagraphStyle("MetaV", parent=ss["Normal"], fontName="Helvetica",
                           fontSize=9.5, textColor=GRIS, leading=13)

# celdas de tabla
c_head = ParagraphStyle("cHead", parent=ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=9, textColor=white, leading=11)
c_head_r = ParagraphStyle("cHeadR", parent=c_head, alignment=TA_RIGHT)
c_num  = ParagraphStyle("cNum", parent=ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=9, textColor=GRIS, alignment=TA_CENTER, leading=11)
c_con  = ParagraphStyle("cCon", parent=ss["Normal"], fontName="Helvetica",
                        fontSize=9, textColor=GRIS, leading=11.5)
c_ref  = ParagraphStyle("cRef", parent=ss["Normal"], fontName="Helvetica",
                        fontSize=8.3, textColor=GRIS, leading=10.5)
c_imp  = ParagraphStyle("cImp", parent=ss["Normal"], fontName="Helvetica",
                        fontSize=9.3, textColor=GRIS, alignment=TA_RIGHT, leading=11)
c_tot_l = ParagraphStyle("cTotL", parent=ss["Normal"], fontName="Helvetica-Bold",
                         fontSize=10.5, textColor=white, alignment=TA_RIGHT, leading=13)
c_tot_v = ParagraphStyle("cTotV", parent=ss["Normal"], fontName="Helvetica-Bold",
                         fontSize=11, textColor=white, alignment=TA_RIGHT, leading=13)

# ---- Header / Footer ----
def header_footer(canvas, doc):
    canvas.saveState()
    w, h = letter
    # Encabezado
    canvas.setFillColor(VERDE)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(MARGIN, h - 46, "PIXADVISOR")
    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(MARGIN + 86, h - 46, "Agricultura de Precisión")
    canvas.setFont("Helvetica", 8.5)
    canvas.drawRightString(w - MARGIN, h - 46, "Informe de Cobranza")
    canvas.setStrokeColor(VERDE)
    canvas.setLineWidth(1.3)
    canvas.line(MARGIN, h - 53, w - MARGIN, h - 53)
    # Pie
    canvas.setStrokeColor(VERDE_CLARO)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 44, w - MARGIN, 44)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GRIS)
    canvas.drawString(MARGIN, 33, f"Pixadvisor AP · Documento de cobranza · {FECHA_CORTA}")
    canvas.drawRightString(w - MARGIN, 33, f"Página {doc.page}")
    canvas.restoreState()

# ---- Contenido ----
story = []

story.append(Paragraph("INFORME DE COBRANZA", st_title))
story.append(Paragraph("Reembolso de gastos de importación, impuestos, fletes y análisis "
                       "incurridos por Pixadvisor por cuenta del cliente.", st_sub))

# Bloque meta
meta_data = [
    [Paragraph("Cliente:", st_meta_l),      Paragraph(CLIENTE, st_meta_v),
     Paragraph("Documento N°:", st_meta_l), Paragraph(DOC_NUM, st_meta_v)],
    [Paragraph("Fecha:", st_meta_l),        Paragraph(FECHA_LARGA, st_meta_v),
     Paragraph("Moneda:", st_meta_l),       Paragraph("Bolivianos (Bs)", st_meta_v)],
]
meta = Table(meta_data, colWidths=[1.0*inch, 2.35*inch, 1.05*inch, 1.7*inch])
meta.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
    ("BOX",        (0, 0), (-1, -1), 0.6, GRIS_LINEA),
    ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING",(0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
]))
story.append(meta)
story.append(Spacer(1, 8))

# Intro
story.append(Paragraph(
    "Por medio del presente, Pixadvisor detalla los gastos abonados por cuenta del cliente "
    "—IT (3%) por emisión de facturas de importación, fletes y análisis— cuyo reembolso se "
    "solicita según el siguiente desglose:",
    st_body))

# Tabla principal
header = [
    Paragraph("N°", c_head),
    Paragraph("Concepto", c_head),
    Paragraph("Base imponible / Referencia", c_head),
    Paragraph("Importe (Bs)", c_head_r),
]
rows = [
    ("1",
     "IT 3% por emisión de factura de importación — Abonadora de Tasa Variable TT",
     "Factura Pixadvisor: " + bs(BASE1) + "<br/>IT 3% — pago obligatorio al fisco",
     IT1),
    ("2",
     "Flete de 2 transformadores (Corumbá a Santa Cruz)",
     "Servicio de transporte",
     FLETE),
    ("3",
     "IT 3% por emisión de factura de importación — 5.000 bandejas para plantines de caña de azúcar",
     "Compra importación: " + bs(BASE3) + "<br/>IT 3% — pago obligatorio al fisco",
     IT3),
    ("4",
     "IT 3% por emisión de factura de importación — Equipo cortador de soquera RS",
     "Factura Pixadvisor: " + bs(BASE4) + "<br/>IT 3% — pago obligatorio al fisco",
     IT4),
    ("5",
     "Análisis de fertilizantes (yeso agrícola y fosfato natural)",
     "Servicio de laboratorio",
     ANALISIS),
]

data = [header]
for n, con, ref, imp in rows:
    data.append([
        Paragraph(n, c_num),
        Paragraph(con, c_con),
        Paragraph(ref, c_ref),
        Paragraph(f"{imp:,.2f}", c_imp),
    ])
# Fila total (span de las 3 primeras columnas)
data.append([
    Paragraph("TOTAL A COBRAR (Bs)", c_tot_l), "", "",
    Paragraph(f"{TOTAL:,.2f}", c_tot_v),
])

col_w = [0.42*inch, 3.05*inch, 1.85*inch, 0.98*inch]
tbl = Table(data, colWidths=col_w, repeatRows=1)
ts = [
    # Encabezado
    ("BACKGROUND", (0, 0), (-1, 0), VERDE),
    ("TOPPADDING", (0, 0), (-1, 0), 5),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 1), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 1), (-1, -1), 2.5),
    ("GRID", (0, 0), (-1, -2), 0.5, GRIS_LINEA),
    # Fila total
    ("SPAN", (0, -1), (2, -1)),
    ("BACKGROUND", (0, -1), (-1, -1), VERDE),
    ("TOPPADDING", (0, -1), (-1, -1), 6),
    ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
    ("LINEABOVE", (0, -1), (-1, -1), 1.2, VERDE),
]
# Filas alternadas
for i in range(1, len(rows) + 1):
    if i % 2 == 0:
        ts.append(("BACKGROUND", (0, i), (-1, i), GRIS_CLARO))
tbl.setStyle(TableStyle(ts))
story.append(tbl)
story.append(Spacer(1, 4))

# Importe en letras
story.append(Paragraph(
    "<b>Son:</b> Treinta y cuatro mil ochocientos cincuenta y un 44/100 Bolivianos.",
    ParagraphStyle("words", parent=st_body, fontSize=9.5, spaceAfter=2, alignment=TA_LEFT)))

# Recuadro: naturaleza del IT 3% + credito fiscal del IVA
box_title_st = ParagraphStyle("boxTitle", parent=ss["Normal"], fontName="Helvetica-Bold",
                              fontSize=10.5, textColor=VERDE, spaceAfter=4, leading=13)
box_body_st = ParagraphStyle("boxBody", parent=ss["Normal"], fontName="Helvetica",
                             fontSize=8.3, textColor=GRIS, alignment=TA_JUSTIFY, leading=10.5, spaceAfter=3)
box_cell = [
    Paragraph("Naturaleza del impuesto (IT 3%) y crédito fiscal del IVA", box_title_st),
    Paragraph(
        "El <b>3%</b> de los ítems 1, 3 y 4 corresponde al <b>Impuesto a las Transacciones "
        "(IT, Ley 843)</b>, de aplicación obligatoria sobre el monto de cada factura emitida por "
        "Pixadvisor. Es un tributo de <b>pago definitivo al Estado</b> (Servicio de Impuestos "
        "Nacionales): se abona indefectiblemente —se paga sí o sí— y <b>no es recuperable</b> como "
        "crédito fiscal por el comprador.", box_body_st),
    Paragraph(
        "<b>Beneficio para el cliente:</b> al importar por su cuenta, Pixadvisor cancela en aduana el "
        "<b>IVA con tasa efectiva del 14,94%</b> sobre el valor de importación. Ese pago genera un "
        "<b>crédito fiscal que Pixadvisor traslada al cliente</b> mediante la factura, quedando a su "
        "favor. Por ello, el <b>único costo impositivo trasladado en esta cobranza es el IT del 3%</b> "
        "(el IVA no se cobra: se transfiere como crédito a favor del cliente).", box_body_st),
]
box = Table([[box_cell]], colWidths=[6.3 * inch])
box.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F1F8E9")),
    ("LINEBEFORE", (0, 0), (0, -1), 3, VERDE),
    ("BOX", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
    ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(Spacer(1, 5))
story.append(KeepTogether(box))

# Forma de pago + datos bancarios
story.append(Paragraph("Forma de pago — Datos bancarios", st_h2))
story.append(Paragraph(
    "Puede depositar o transferir el monto total de <b>" + bs(TOTAL) + "</b> (en bolivianos) "
    "a la siguiente cuenta de Pixadvisor:", st_body))

bank_l = ParagraphStyle("bankL", parent=ss["Normal"], fontName="Helvetica-Bold",
                        fontSize=9, textColor=VERDE, leading=12)
bank_v = ParagraphStyle("bankV", parent=ss["Normal"], fontName="Helvetica",
                        fontSize=9, textColor=GRIS, leading=12)
bank_vb = ParagraphStyle("bankVB", parent=bank_v, fontName="Helvetica-Bold", fontSize=9.5)
bank_data = [
    [Paragraph("Banco:", bank_l),          Paragraph("BISA", bank_v),
     Paragraph("Tipo de cuenta:", bank_l), Paragraph("Cuenta Corriente", bank_v)],
    [Paragraph("Titular:", bank_l),        Paragraph("Pixadvisor S.R.L.", bank_v),
     Paragraph("N.° de cuenta:", bank_l),  Paragraph("731810010", bank_vb)],
]
bank = Table(bank_data, colWidths=[0.95 * inch, 2.05 * inch, 1.15 * inch, 2.15 * inch])
bank.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
    ("LINEBEFORE", (0, 0), (0, -1), 3, VERDE),
    ("BOX", (0, 0), (-1, -1), 0.5, GRIS_LINEA),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(Spacer(1, 4))
story.append(KeepTogether(bank))

# Cierre + firma
story.append(Spacer(1, 5))
story.append(Paragraph(
    "Favor enviar el comprobante una vez efectuado el pago. Quedamos a disposición para "
    "cualquier aclaración.",
    ParagraphStyle("clo", parent=ss["Normal"], fontName="Helvetica", fontSize=8.5,
                   textColor=GRIS, alignment=TA_LEFT, leading=11)))
story.append(Spacer(1, 10))
firma = Table([
    [Paragraph("___________________________________", st_meta_v)],
    [Paragraph("<b>Pixadvisor — Agricultura de Precisión</b>", st_meta_v)],
    [Paragraph("Nilton Luiz Camargo", st_meta_v)],
], colWidths=[3.2*inch])
firma.setStyle(TableStyle([
    ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ("TOPPADDING", (0, 0), (-1, -1), 1),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
]))
story.append(firma)

# ---- Build ----
doc = SimpleDocTemplate(
    OUT_PDF, pagesize=letter,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=0.8 * inch, bottomMargin=0.7 * inch,
    title="Informe de Cobranza - Donizete Fernandes",
    author="Pixadvisor")
doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)

sz = os.path.getsize(OUT_PDF)
print("OK ->", OUT_PDF)
print("Tamano:", sz, "bytes")
assert sz > 0
