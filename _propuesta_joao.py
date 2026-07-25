#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Propuesta de Análisis de Suelo — Pixadvisor (PDF, 5 páginas).
Variables de entorno (todas opcionales):
  HERO   -> imagen de portada (default: ./zonemap_real.png ; generar antes con make_zonemap.py)
  LOGO   -> logo PNG (default: ../assets/LOGO-PIX.png embebido en la skill)
  OUT    -> ruta PDF de salida (default: ./Propuesta_Analisis_Suelo.pdf)
  CLIENTE, CULTIVO, SUPERFICIE, UBICACION, FECHA -> datos de portada
  TEL, EMAIL, WEB -> contacto (default: datos Pixadvisor)
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
    Spacer, Table, TableStyle, PageBreak, Image, HRFlowable, NextPageTemplate)
from PIL import Image as PILImage

BASE   = os.path.dirname(os.path.abspath(__file__))
SKILL  = os.path.dirname(BASE)
ASSETS = os.path.join(SKILL, "assets")
HERO = os.environ.get("HERO", os.path.join(os.getcwd(), "zonemap_real.png"))
LOGO = os.environ.get("LOGO", os.path.join(ASSETS, "LOGO-PIX.png"))
OUT  = os.environ.get("OUT",  os.path.join(os.getcwd(), "Propuesta_Analisis_Suelo.pdf"))

CLIENTE    = os.environ.get("CLIENTE", "[Nombre del cliente]")
CULTIVO    = os.environ.get("CULTIVO", "[Cultivo]")
SUPERFICIE = os.environ.get("SUPERFICIE", "[___ ha]")
UBICACION  = os.environ.get("UBICACION", "[Localidad / Coord.]")
FECHA      = os.environ.get("FECHA", "[dd/mm/aaaa]")
TEL   = os.environ.get("TEL",   "+591 72149171")
EMAIL = os.environ.get("EMAIL", "nilton.camargo@pixadvisor.network")
WEB   = os.environ.get("WEB",   "pixadvisor.network")

VERDE=HexColor("#1B5E20"); VERDE2=HexColor("#4CAF50"); GRIS=HexColor("#333333")
GRISC=HexColor("#F5F5F5"); GRISL=HexColor("#E8EDE9")
PW, PHH = letter

ss = getSampleStyleSheet()
def st(name, **kw):
    ss.add(ParagraphStyle(name, **kw)); return ss[name]
H2  = st("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=14,
         textColor=VERDE, spaceBefore=10, spaceAfter=6, leading=17)
H3  = st("H3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=11,
         textColor=VERDE2, spaceBefore=6, spaceAfter=3)
BODY= st("BODY", parent=ss["BodyText"], fontName="Helvetica", fontSize=10,
         textColor=GRIS, leading=14.5, alignment=TA_JUSTIFY, spaceAfter=6)
BULL= st("BULL", parent=BODY, leftIndent=12, spaceAfter=3, alignment=TA_LEFT)
TH  = st("TH", fontName="Helvetica-Bold", fontSize=9.5, textColor=white, leading=12)
TD  = st("TD", fontName="Helvetica", fontSize=9, textColor=GRIS, leading=12)
TDB = st("TDB", fontName="Helvetica-Bold", fontSize=9, textColor=VERDE, leading=12)
CK  = st("CK", fontName="Helvetica-Bold", fontSize=11, textColor=VERDE2, alignment=TA_CENTER, spaceAfter=2)
CT  = st("CT", fontName="Helvetica-Bold", fontSize=30, textColor=VERDE, alignment=TA_CENTER, leading=33, spaceAfter=4)
CS  = st("CS", fontName="Helvetica", fontSize=11.5, textColor=GRIS, alignment=TA_CENTER, leading=16, spaceAfter=4)

def logo_flowable(width):
    iw, ih = PILImage.open(LOGO).size
    return Image(LOGO, width=width, height=width*ih/iw)

def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        iw, ih = PILImage.open(LOGO).size
        lw = 1.05*inch; lh = lw*ih/iw
        canvas.drawImage(LOGO, 0.7*inch, PHH-0.38*inch-lh, width=lw, height=lh,
                         mask="auto", preserveAspectRatio=True)
        canvas.setFillColor(VERDE); canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawRightString(PW-0.7*inch, PHH-0.45*inch, "PROPUESTA DE SERVICIO")
        canvas.setFillColor(HexColor("#999999")); canvas.setFont("Helvetica", 7.5)
        canvas.drawRightString(PW-0.7*inch, PHH-0.58*inch, "Análisis de Suelo · Agricultura de Precisión")
        canvas.setStrokeColor(VERDE2); canvas.setLineWidth(1.4)
        canvas.line(0.7*inch, PHH-0.78*inch, PW-0.7*inch, PHH-0.78*inch)
    canvas.setFillColor(VERDE); canvas.rect(0, 0, PW, 0.42*inch, fill=1, stroke=0)
    canvas.setFillColor(white); canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(0.7*inch, 0.17*inch, "PIXADVISOR — Agricultura de Precisión")
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(PW/2+0.35*inch, 0.17*inch, "Muestreo georreferenciado · Mapas de fertilidad · VRT")
    canvas.drawRightString(PW-0.7*inch, 0.17*inch, f"Pág. {doc.page}")
    canvas.restoreState()

doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=0.7*inch, rightMargin=0.7*inch,
    topMargin=0.9*inch, bottomMargin=0.6*inch, title="Propuesta de Análisis de Suelo — Pixadvisor")
doc.addPageTemplates([
    PageTemplate(id="Cover", frames=[Frame(0.7*inch,0.5*inch,PW-1.4*inch,PHH-1.0*inch,id="c")], onPage=header_footer),
    PageTemplate(id="Body",  frames=[Frame(0.7*inch,0.55*inch,PW-1.4*inch,PHH-1.80*inch,id="b")], onPage=header_footer),
])

S = []
# -------- Portada --------
S += [Spacer(1,6), logo_flowable(2.6*inch), Spacer(1,14),
      Paragraph("PROPUESTA DE SERVICIO", CK), Paragraph("Análisis de Suelo", CT),
      Paragraph("Mapeo de Fertilidad &amp; Zonas de Manejo", CS), Spacer(1,4),
      HRFlowable(width="40%", thickness=2, color=VERDE2, spaceAfter=10)]
iw, ih = PILImage.open(HERO).size
hw = PW-1.4*inch; hh = hw*ih/iw
if hh > 3.3*inch:                       # cap altura para que la portada quepa en 1 pagina
    hh = 3.3*inch; hw = hh*iw/ih
S += [Image(HERO, width=hw, height=hh, hAlign='CENTER'), Spacer(1,12)]
def field(lbl, val):
    return [Paragraph(lbl, ParagraphStyle("fl", fontName="Helvetica-Bold", fontSize=8.5, textColor=VERDE2)),
            Paragraph(val, ParagraphStyle("fv", fontName="Helvetica", fontSize=10, textColor=GRIS))]
data = [field("CLIENTE / HACIENDA", CLIENTE)+field("CULTIVO", CULTIVO),
        field("SUPERFICIE (ha)", SUPERFICIE)+field("UBICACIÓN", UBICACION),
        field("FECHA", FECHA)+field("VÁLIDA POR", "30 días")]
t = Table(data, colWidths=[1.55*inch,2.05*inch,1.35*inch,2.15*inch])
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),GRISC),("BOX",(0,0),(-1,-1),0.8,VERDE2),
    ("INNERGRID",(0,0),(-1,-1),0.4,GRISL),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),("LEFTPADDING",(0,0),(-1,-1),8)]))
S += [t, NextPageTemplate("Body"), PageBreak()]

# -------- Pág 2 --------
S += [Paragraph("1. Presentación", H2),
 Paragraph("Pixadvisor es una consultora de <b>agricultura de precisión</b> especializada en el "
   "diagnóstico de la variabilidad espacial de los lotes mediante percepción remota (Sentinel-2 y "
   "drones), muestreo de suelo georreferenciado y análisis de datos geoespaciales. Convertimos los "
   "datos del campo en <b>decisiones de manejo sitio-específico</b> que aumentan la eficiencia de la "
   "fertilización y el rendimiento.", BODY),
 Paragraph("Esta propuesta detalla el servicio de <b>análisis de suelo y mapeo de fertilidad</b> "
   "para el lote indicado, su metodología, entregables, plazos e inversión.", BODY),
 Paragraph("2. Objetivo del servicio", H2)]
for it in ["Caracterizar la <b>fertilidad y la variabilidad espacial</b> del lote a partir de muestreo georreferenciado.",
 "Delimitar <b>zonas de manejo (ambientes productivos)</b> según la variabilidad real del suelo y el vigor histórico.",
 "Generar <b>mapas de fertilidad</b> interpolados por nutriente y propiedad química.",
 "Entregar una <b>recomendación de fertilización y enmiendas</b> en dosis fija o de tasa variable (VRT)."]:
    S.append(Paragraph("•&nbsp;&nbsp;"+it, BULL))
S += [Paragraph("3. Alcance", H2),
 Paragraph("El servicio cubre desde la planificación de la grilla de muestreo hasta la entrega del "
   "reporte de diagnóstico, los mapas y la prescripción de tasa variable. El servicio se aplica sobre el <b>área útil</b> de cada lote (cañadas y drenajes ya descontados). <b>No incluye</b> el costo de los fertilizantes ni la "
   "operación de aplicación, salvo que se contrate por separado en un protocolo de aplicación.", BODY),
 PageBreak()]

# -------- Pág 3 --------
S += [Paragraph("4. Metodología de muestreo", H2),
 Paragraph("El muestreo se realiza con grilla georreferenciada y registro GPS de cada punto mediante "
   "la app <b>PIX-Muestreo</b>, garantizando trazabilidad y repetibilidad entre campañas.", BODY)]
meth = [[Paragraph("Parámetro", TH), Paragraph("Especificación", TH)],
 [Paragraph("Tipo de muestreo", TD), Paragraph("Dirigido por ambientes productivos (zonas de manejo)", TD)],
 [Paragraph("Estrategia", TD), Paragraph("Dirigido por ambientes de manejo · hasta 3 ambientes por lote · 168 muestras compuestas", TD)],
 [Paragraph("Submuestras por punto", TD), Paragraph("5–10 piques distribuidos por todo el ambiente · buffer ≥ 20 m del borde", TD)],
 [Paragraph("Profundidad", TD), Paragraph("0–20 cm (y 20–40 cm opcional)", TD)],
 [Paragraph("Georreferenciación", TD), Paragraph("GPS por punto · app PIX-Muestreo · exporta KML/SHP", TD)],
 [Paragraph("Laboratorio", TD), Paragraph("[Laboratorio acreditado] · metodología estándar", TD)]]
tm = Table(meth, colWidths=[1.9*inch,5.2*inch])
tm.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),VERDE),("ROWBACKGROUNDS",(0,1),(-1,-1),[white,GRISC]),
    ("GRID",(0,0),(-1,-1),0.4,GRISL),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)]))
S += [tm, Spacer(1,8), Paragraph("Parámetros analizados", H3)]
params = [[Paragraph("Químicos base", TDB), Paragraph("pH, Materia Orgánica (MO), CIC/CTC, Conductividad Eléctrica (CE)", TD)],
 [Paragraph("Macronutrientes", TDB), Paragraph("P (disponible), K, Ca, Mg, S", TD)],
 [Paragraph("Saturaciones", TDB), Paragraph("Saturación de bases y de Al; relaciones Ca:Mg, Ca:K, Mg:K", TD)],
 [Paragraph("Micronutrientes", TDB), Paragraph("Zn, B, Cu, Fe, Mn (según paquete contratado)", TD)],
 [Paragraph("Físicos", TDB), Paragraph("Textura (arena/limo/arcilla) — opcional", TD)]]
tp = Table(params, colWidths=[1.6*inch,5.5*inch])
tp.setStyle(TableStyle([("ROWBACKGROUNDS",(0,0),(-1,-1),[white,GRISC]),("GRID",(0,0),(-1,-1),0.4,GRISL),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)]))
S += [tp, PageBreak()]

# -------- Pág 4 --------
S += [Paragraph("5. Entregables", H2),
 Paragraph("El cliente recibe un paquete técnico completo, en PDF y en formatos GIS:", BODY)]
deliv = [[Paragraph("Entregable", TH), Paragraph("Descripción", TH), Paragraph("Formato", TH)],
 [Paragraph("Mapas de fertilidad", TD), Paragraph("Mapa interpolado por nutriente y propiedad (pH, MO, P, K, Ca, Mg, CIC, sat. bases)", TD), Paragraph("PDF · GeoTIFF", TD)],
 [Paragraph("Zonas de manejo", TD), Paragraph("Delimitación de ambientes productivos (UGD) por variabilidad y vigor histórico", TD), Paragraph("PDF · SHP/KML", TD)],
 [Paragraph("Reporte de diagnóstico", TD), Paragraph("Interpretación técnica, relaciones entre nutrientes y limitantes por zona", TD), Paragraph("PDF", TD)],
 [Paragraph("Recomendación de fertilización", TD), Paragraph("Dosis por nutriente (kg/ha) y enmiendas; dosis fija o tasa variable", TD), Paragraph("PDF", TD)],
 [Paragraph("Mapa de prescripción VRT", TD), Paragraph("Prescripción georreferenciada para monitor de siembra/fertilización (opcional)", TD), Paragraph("SHP · ISO-XML", TD)]]
td = Table(deliv, colWidths=[1.7*inch,4.0*inch,1.4*inch])
td.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),VERDE),("ROWBACKGROUNDS",(0,1),(-1,-1),[white,GRISC]),
    ("GRID",(0,0),(-1,-1),0.4,GRISL),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)]))
S += [td, Spacer(1,10), Paragraph("6. Fases y cronograma", H2)]
fases = [[Paragraph("Fase", TH), Paragraph("Actividad", TH), Paragraph("Plazo estimado", TH)],
 [Paragraph("1", TDB), Paragraph("Planificación de grilla y aprobación con el cliente", TD), Paragraph("1–2 días", TD)],
 [Paragraph("2", TDB), Paragraph("Muestreo de campo georreferenciado", TD), Paragraph("[según superficie]", TD)],
 [Paragraph("3", TDB), Paragraph("Envío a laboratorio y análisis", TD), Paragraph("7–15 días", TD)],
 [Paragraph("4", TDB), Paragraph("Procesamiento GIS, mapas y diagnóstico", TD), Paragraph("3–5 días", TD)],
 [Paragraph("5", TDB), Paragraph("Entrega y reunión de presentación de resultados", TD), Paragraph("1 día", TD)]]
tf = Table(fases, colWidths=[0.6*inch,4.9*inch,1.6*inch])
tf.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),VERDE),("ROWBACKGROUNDS",(0,1),(-1,-1),[white,GRISC]),
    ("GRID",(0,0),(-1,-1),0.4,GRISL),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(0,0),(0,-1),"CENTER"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)]))
S += [tf, PageBreak()]

# -------- Pág 5 --------
S += [Paragraph("7. Inversión", H2),
 Paragraph("Servicio integral de análisis de suelo y mapeo de fertilidad, con tarifa única por hectárea de área útil (todo incluido).", BODY)]
inv = [[Paragraph("Concepto", TH), Paragraph("Unidad", TH), Paragraph("Cant.", TH), Paragraph("P. unit. (USD)", TH), Paragraph("Subtotal (USD)", TH)],
 [Paragraph("Servicio integral de análisis de suelo y mapeo de fertilidad — incluye muestreo georreferenciado, análisis de laboratorio, procesamiento GIS, delimitación de zonas de manejo, reporte de diagnóstico, recomendación de fertilización y mapas de prescripción de tasa variable (VRT)", TD), Paragraph("por ha útil", TD), Paragraph("1.782,8", TD), Paragraph("15,00", TD), Paragraph("26.742", TD)],
 [Paragraph("TOTAL (USD)", TH), Paragraph("", TD), Paragraph("", TD), Paragraph("", TD), Paragraph("USD 26.742", TH)]]
ti = Table(inv, colWidths=[3.0*inch,1.1*inch,0.7*inch,1.1*inch,1.2*inch])
ti.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),VERDE),("BACKGROUND",(0,-1),(-1,-1),VERDE2),
    ("ROWBACKGROUNDS",(0,1),(-1,-2),[white,GRISC]),("GRID",(0,0),(-1,-1),0.4,GRISL),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("ALIGN",(1,0),(-1,-1),"CENTER"),
    ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),7)]))
S += [ti, Spacer(1,8), Paragraph("<b>Tarifa: USD 15 por hectárea de área útil — todo incluido.</b> Total del servicio: <b>USD 26.742</b> sobre 1.782,8 ha útiles (cañadas y drenajes ya descontados; el lote bruto es 1.871,5 ha).", BODY), Spacer(1,4), Paragraph("8. Condiciones comerciales", H2)]
for it in ["<b>Validez de la oferta:</b> 30 días desde la fecha de emisión.",
 "<b>Forma de pago:</b> 50% a la firma del contrato y 50% contra la entrega de los mapas de prescripción de tasa variable (VRT) y las recomendaciones de fertilización.",
 "<b>Plazos:</b> sujetos a condiciones de campo (humedad/accesibilidad) y a los tiempos del laboratorio.",
 "<b>No incluye:</b> costo de fertilizantes, enmiendas ni operación de aplicación.",
 "<b>Confidencialidad:</b> los datos del lote son propiedad del cliente y no se comparten con terceros."]:
    S.append(Paragraph("•&nbsp;&nbsp;"+it, BULL))
S += [Spacer(1,14), HRFlowable(width="100%", thickness=1, color=VERDE2), Spacer(1,6)]
contact = Table([[logo_flowable(1.7*inch),
    Paragraph(f"<b>PIXADVISOR — Agricultura de Precisión</b><br/>Contacto: {TEL}<br/>"
              f"Email: {EMAIL}<br/>Web: {WEB}", ParagraphStyle("ct", fontName="Helvetica",
              fontSize=9.5, textColor=GRIS, leading=14, alignment=TA_RIGHT))]],
    colWidths=[3.0*inch,4.1*inch])
contact.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
S.append(contact)

doc.build(S)
print("OK pdf ->", OUT, os.path.getsize(OUT), "bytes")
