# -*- coding: utf-8 -*-
"""Propuesta Tecnica Integral - Diagnostico de Suelos - Hacienda Efrain (Rainer Netzlaf)
Reconstruye el modelo de Joao Geraldo (Cerro Alto) en ReportLab con datos finales."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas

AST = r"D:\PIXADVISOR_AGENT_WORKSPACE\_efrain_build"
LOGO = AST + r"\img_p1_x3.png"
MAP1 = AST + r"\img_p4_x10.png"
MAP2 = AST + r"\img_p4_x11.png"
OUT  = r"C:\Users\Usuario\Desktop\Clientes\HaciendaEfrain\Propuesta_Pixadvisor_HaciendaEfrain_FINAL.pdf"

GREEN_DARK = HexColor("#2D7C31")
GREEN_MED  = HexColor("#43A047")
GREEN_GRAD = HexColor("#4AAF52")
CYAN_GRAD  = HexColor("#02BCCF")
SEC_BG     = HexColor("#E8F4E8")
GRAY_TXT   = HexColor("#4A4A4A")
GRAY_LBL   = HexColor("#6B7280")
INFO_BG    = HexColor("#F0F0F0")
CARD_BD    = HexColor("#DCDCDC")
DARK       = HexColor("#222222")
LINK       = HexColor("#1577B4")

W, H = A4
LM = 68.0; RM = 68.0
CW = W - LM - RM
CR = W - RM

body = ParagraphStyle('body', fontName='Helvetica', fontSize=10, leading=14,
                      textColor=GRAY_TXT, alignment=TA_JUSTIFY)
bullet = ParagraphStyle('bullet', fontName='Helvetica', fontSize=10, leading=15,
                        textColor=GRAY_TXT, leftIndent=15, bulletIndent=2,
                        bulletFontName='Helvetica', bulletFontSize=10)
cap = ParagraphStyle('cap', fontName='Helvetica-Oblique', fontSize=8.5, leading=11,
                     textColor=GRAY_LBL, alignment=TA_LEFT)

def gradient_h(c, x, y, w, h, c1, c2, steps=170):
    for i in range(steps):
        t = i/(steps-1)
        col = Color(c1.red+(c2.red-c1.red)*t, c1.green+(c2.green-c1.green)*t,
                    c1.blue+(c2.blue-c1.blue)*t)
        c.setFillColor(col); c.rect(x + w*i/steps, y, w/steps + 0.6, h, fill=1, stroke=0)

def para(c, text, style, x, y_top, w, bullet_text=None):
    P = Paragraph(text, style, bulletText=bullet_text)
    pw, ph = P.wrapOn(c, w, 2000); P.drawOn(c, x, y_top - ph)
    return ph

def section(c, y_top, text, h=30):
    gradient_h(c, LM, y_top-h, CW, h, SEC_BG, white)
    c.setFillColor(GREEN_MED); c.rect(LM, y_top-h, 5, h, fill=1, stroke=0)
    c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 13)
    c.drawString(LM+16, y_top-h+10, text)
    return y_top - h - 10

def phase_card(c, y_top, num, title, desc, h=64):
    c.setStrokeColor(CARD_BD); c.setLineWidth(1); c.setFillColor(white)
    c.roundRect(LM, y_top-h, CW, h, 6, stroke=1, fill=1)
    c.setFillColor(GREEN_MED); c.rect(LM+1.5, y_top-h+4, 4, h-8, fill=1, stroke=0)
    cx, cy = LM+30, y_top-22
    c.setFillColor(GREEN_MED); c.circle(cx, cy, 11, fill=1, stroke=0)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 11); c.drawCentredString(cx, cy-4, str(num))
    c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 12); c.drawString(LM+50, y_top-26, title)
    dstyle = ParagraphStyle('d', fontName='Helvetica', fontSize=9.5, leading=12.5, textColor=GRAY_TXT)
    para(c, desc, dstyle, LM+50, y_top-32, CW-66)
    return y_top - h - 7

def chrome(c, page_no):
    gradient_h(c, 0, H-8, W, 8, GREEN_GRAD, CYAN_GRAD)
    gradient_h(c, 0, 0, W, 40, CYAN_GRAD, GREEN_GRAD)
    c.setFillColor(white); c.setFont('Helvetica', 8)
    c.drawRightString(CR, 15, "Pixadvisor Agricultura de Precisión  |  Página %d" % page_no)
    lw, lh = 140, 140*768/2040.0
    c.drawImage(LOGO, CR-lw, H-16-lh, lw, lh, mask='auto', preserveAspectRatio=True)

c = canvas.Canvas(OUT, pagesize=A4)

# ===================== PAGE 1 - COVER =====================
gradient_h(c, 0, H-80, W, 80, GREEN_GRAD, CYAN_GRAD)
gradient_h(c, 0, 0, W, 48, CYAN_GRAD, GREEN_GRAD)
lw = 300; lh = lw*768/2040.0
c.drawImage(LOGO, (W-lw)/2.0, 600, lw, lh, mask='auto', preserveAspectRatio=True)
c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 26)
c.drawCentredString(W/2, 548, "PROPUESTA TÉCNICA INTEGRAL")
c.setFillColor(GRAY_LBL); c.setFont('Helvetica', 14)
c.drawCentredString(W/2, 518, "Diagnóstico de Suelos y Prescripción")
c.drawCentredString(W/2, 499, "en Agricultura de Precisión")
c.setStrokeColor(GREEN_MED); c.setLineWidth(3); c.line(W/2-65, 468, W/2+65, 468)
bx, by, bh = LM, 290, 142
c.setFillColor(INFO_BG); c.roundRect(bx, by, CW, bh, 6, stroke=0, fill=1)
c.setFillColor(GREEN_MED); c.rect(bx, by, 5, bh, fill=1, stroke=0)
rows = [("Cliente:", "Rainer Netzlaf"), ("Propiedad:", "Hacienda Efraín"),
        ("Superficie:", "4.000 hectáreas"), ("Cultivo:", "Soya"),
        ("Empresa ejecutora:", "Pixadvisor Agricultura de Precisión")]
ry = by + bh - 28
for lbl, val in rows:
    c.setFillColor(GRAY_LBL); c.setFont('Helvetica-Bold', 10); c.drawString(bx+24, ry, lbl)
    c.setFillColor(DARK); c.setFont('Helvetica-Bold', 11); c.drawString(bx+165, ry, val)
    ry -= 26
c.setFillColor(GRAY_LBL); c.setFont('Helvetica', 11); c.drawCentredString(W/2, 255, "Junio 2026")
c.showPage()

# ===================== PAGE 2 =====================
chrome(c, 2)
y = H-100
y = section(c, y, "ALCANCE DEL SERVICIO")
alcance = ("El presente proyecto comprende el diagnóstico integral de suelos en "
           "<b>4.000 hectáreas de soya</b> en Hacienda Efraín, mediante tecnología de "
           "Agricultura de Precisión. Incluye georeferenciamiento, estudio de ambientes "
           "por teledetección satelital, muestreo dirigido, análisis en laboratorio de "
           "referencia internacional (IBRA, Brasil) e interpretación agronómica con entrega "
           "de más de 24 mapas de distribución de nutrientes y prescripciones en tasa "
           "variable (VRT).")
y -= para(c, alcance, body, LM, y, CW) + 12
y = section(c, y, "OBJETIVO DEL PROYECTO")
y -= para(c, "Implementar un sistema completo de diagnóstico agronómico basado en "
             "Agricultura de Precisión, orientado a:", body, LM, y, CW) + 6
for b in ["Maximizar productividad en soya",
          "Optimizar inversión en fertilizantes y enmiendas",
          "Corregir desbalances químicos del suelo",
          "Reducir costos innecesarios por aplicación uniforme",
          "Aumentar rentabilidad por ambiente productivo"]:
    y -= para(c, b, bullet, LM, y, CW, bullet_text=u"•") + 2
y -= 10
y = section(c, y, "CRONOGRAMA DE TRABAJO — 6 FASES")
y -= 4
fases = [
 (1,"GEOREFERENCIAMIENTO","Georeferenciamiento de las áreas planificadas para realizar muestreo de suelo. Delimitación de los límites de cada lote con GPS de alta precisión."),
 (2,"ESTUDIO DE AMBIENTES","Estudios de ambientes de producción intra-lote. Generación de mapas de zonas de manejo utilizando imágenes satelitales Sentinel-2 y análisis multitemporal."),
 (3,"LOCACIÓN DE PUNTOS","Locación de puntos georeferenciados para posterior muestreo a campo. Distribución estratégica según ambientes identificados."),
 (4,"MUESTREO A CAMPO","Muestreo a campo por personal especializado de Pixadvisor. Extracción de muestras representativas por ambiente productivo."),
 (5,"ENVÍO A LABORATORIO","Envío de las muestras al laboratorio IBRA en Brasil. Análisis completo de macro y micronutrientes, textura, CIC, pH y más."),
 (6,"INTERPRETACIÓN Y ENTREGABLES","Interpretación de resultados y confección de mapas de distribución de nutrientes por ambiente. Prescripciones en tasa variable para fertilizantes y enmiendas."),
]
for n,t,d in fases[:3]:
    y = phase_card(c, y, n, t, d)
c.showPage()

# ===================== PAGE 3 =====================
chrome(c, 3)
y = H-100
for n,t,d in fases[3:]:
    y = phase_card(c, y, n, t, d)
y -= 4
y -= para(c, u"<i>IBRA Laboratorios — São Paulo  |  Laboratorio de referencia internacional</i>",
          cap, LM, y, CW) + 12
y = section(c, y, "ENTREGA DE MÁS DE 24 MAPAS AGRONÓMICOS")
y -= 4
c.setFillColor(GRAY_TXT); c.setFont('Helvetica', 10); c.drawString(LM, y-12, "Incluye:")
y -= 28
lcol = [("Macronutrientes:",1),("N, P, K, Ca, Mg, S",0),("Micronutrientes:",1),
        ("B, Zn, Mn, Cu, Fe",0),("Textura y Arcilla",0),("CIC",0),("pH en Agua",0)]
rcol = ["Saturación de Bases","Conductividad Eléctrica (EC)","Saturación de Ca, K, Al, Mg",
        "Relaciones entre Nutrientes","Mapas de recomendación VRT","Prescripción de fertilizantes",
        "Prescripción de enmiendas y semillas"]
ly = y
for (lft,bd),rgt in zip(lcol,rcol):
    c.setFillColor(DARK if bd else GRAY_TXT)
    c.setFont('Helvetica-Bold' if bd else 'Helvetica', 10); c.drawString(LM+10, ly, lft)
    c.setFillColor(GRAY_TXT); c.setFont('Helvetica', 10); c.drawString(LM+245, ly, rgt)
    ly -= 21
y = ly - 6
para(c, u"<i>Todos los mapas serán entregados en formato impreso y digital, de acuerdo a los "
        u"requerimientos específicos de la soya y sus rangos de suficiencia.</i>", cap, LM, y, CW)
c.showPage()

# ===================== PAGE 4 =====================
chrome(c, 4)
y = H-100
y = section(c, y, "EJEMPLO DE ENTREGABLES")
y -= para(c, "A continuación se muestran ejemplos reales de los mapas generados por Pixadvisor "
             "mediante tecnología de Agricultura de Precisión:", body, LM, y, CW) + 14
iw = 330; ih = iw*615/922.0
c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 11)
c.drawString(LM, y-12, "Mapa de Ambientes Productivos"); y -= 24
y -= para(c, u"<i>Delimitación de zonas de manejo intra-lote basada en análisis multitemporal de "
             u"imágenes satelitales Sentinel-2.</i>", cap, LM, y, CW) + 6
c.drawImage(MAP1, LM+(CW-iw)/2.0, y-ih, iw, ih, mask='auto', preserveAspectRatio=True); y -= ih+16
c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 11)
c.drawString(LM, y-12, u"Mapa de Prescripción en Tasa Variable — Fósforo (P2O5)"); y -= 24
y -= para(c, u"<i>Prescripción diferenciada por ambiente utilizando Monofosfato de Amonio (MAP). "
             u"Dosis ajustadas según nivel de suficiencia por zona.</i>", cap, LM, y, CW) + 6
c.drawImage(MAP2, LM+(CW-iw)/2.0, y-ih, iw, ih, mask='auto', preserveAspectRatio=True)
c.showPage()

# ===================== PAGE 5 =====================
chrome(c, 5)
y = H-100
y = section(c, y, "PLAZO DE ENTREGA")
y -= para(c, "20 días hábiles desde la finalización del muestreo y envío al laboratorio.",
          body, LM, y, CW) + 12
y = section(c, y, "INVERSIÓN DEL CLIENTE")
y -= 8
boxh = 92
c.setStrokeColor(GREEN_MED); c.setLineWidth(1.5); c.setFillColor(white)
c.roundRect(LM, y-boxh, CW, boxh, 8, stroke=1, fill=1)
def inv_row(label, value, vy, big=False):
    c.setFillColor(GRAY_LBL); c.setFont('Helvetica', 11); c.drawString(LM+22, vy, label)
    if big: c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 20)
    else: c.setFillColor(DARK); c.setFont('Helvetica-Bold', 12)
    c.drawString(LM+210, vy, value)
inv_row("Área total:", "4.000 hectáreas", y-26)
inv_row("Valor por hectárea:", "US$ 15/ha", y-52)
inv_row("Inversión total:", "US$ 60.000", y-84, big=True)
y -= boxh + 12
y = section(c, y, "FORMA DE PAGO")
y -= 8
pgh = 56
c.setFillColor(INFO_BG); c.roundRect(LM, y-pgh, CW, pgh, 6, stroke=0, fill=1)
def pago_row(label, value, vy):
    c.setFillColor(GREEN_MED); c.circle(LM+20, vy+3, 3.2, fill=1, stroke=0)
    c.setFillColor(DARK); c.setFont('Helvetica-Bold', 10); c.drawString(LM+32, vy, label)
    c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 11); c.drawString(LM+300, vy, value)
pago_row("50% al inicio del servicio:", "US$ 30.000", y-22)
pago_row("50% contra entrega de resultados:", "US$ 30.000", y-44)
y -= pgh + 12
y = section(c, y, "DIFERENCIAL PIXADVISOR")
y -= 6
dh = 92
c.setFillColor(SEC_BG); c.roundRect(LM, y-dh, CW, dh, 6, stroke=0, fill=1)
c.setFillColor(GREEN_MED); c.rect(LM, y-dh, 4, dh, fill=1, stroke=0)
dy = y-18
for d in [u"Metodología brasileña avanzada", u"Enfoque por ambientes reales de producción",
          u"Diagnóstico profundo y no superficial", u"Agricultura de Precisión verdadera, sitio-específica",
          u"Decisiones basadas en datos, no en promedios"]:
    c.setFillColor(GREEN_MED); c.circle(LM+22, dy+3, 2.0, fill=1, stroke=0)
    c.setFillColor(GRAY_TXT); c.setFont('Helvetica', 9.5); c.drawString(LM+32, dy, d)
    dy -= 15
y -= dh + 18
c.setFillColor(GREEN_DARK); c.setFont('Helvetica-Bold', 11)
c.drawCentredString(W/2, y, "RESPONSABLE TÉCNICO"); y -= 16
c.setFillColor(GRAY_TXT); c.setFont('Helvetica', 10)
c.drawCentredString(W/2, y, "Ing. Agr. Nilton Camargo"); y -= 14
c.setFillColor(DARK); c.setFont('Helvetica-Bold', 10)
c.drawCentredString(W/2, y, "Pixadvisor Agricultura de Precisión"); y -= 14
c.setFillColor(LINK); c.setFont('Helvetica', 10)
c.drawCentredString(W/2, y, "nilton.camargo@pixadvisor.network"); y -= 34
c.setStrokeColor(HexColor("#BBBBBB")); c.setLineWidth(0.8)
xL, xR = LM+115, W-RM-115
c.line(xL-85, y, xL+85, y); c.line(xR-85, y, xR+85, y); y -= 13
c.setFillColor(DARK); c.setFont('Helvetica-Bold', 9)
c.drawCentredString(xL, y, "Ing. Agr. Nilton Camargo"); c.drawCentredString(xR, y, "Rainer Netzlaf")
c.setFillColor(GRAY_LBL); c.setFont('Helvetica', 8)
c.drawCentredString(xL, y-12, "Pixadvisor Agricultura de Precisión"); c.drawCentredString(xR, y-12, "Hacienda Efraín")
c.drawCentredString(xL, y-23, "Responsable Técnico"); c.drawCentredString(xR, y-23, "Cliente")
y -= 44
c.setFillColor(GRAY_TXT); c.setFont('Helvetica', 10)
c.drawCentredString(W/2, y, u"Santa Cruz de la Sierra, Bolivia — Junio 2026"); y -= 16
c.setFillColor(GRAY_LBL); c.setFont('Helvetica-Oblique', 8.5)
c.drawCentredString(W/2, y, "Validez de la propuesta: 30 días a partir de la fecha de emisión.")
c.showPage()
c.save()
print("WROTE", OUT)
