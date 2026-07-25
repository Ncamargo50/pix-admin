# -*- coding: utf-8 -*-
"""Contrato de Aceptacion / Prestacion de Servicio de Analisis de Suelo
Pixadvisor S.R.L. <-> Joao Geraldo (Hacienda Serro Alto). PDF branding Pixadvisor."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image)
from PIL import Image as PILImage
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
LOGO = r'C:\Users\Usuario\AppData\Roaming\Claude\local-agent-mode-sessions\skills-plugin\0fecab30-5b73-43f6-a6dd-93f3db3c3ddb\3e588912-7e49-4dbe-bdfc-5d0c46177343\skills\propuesta-analisis-suelo\assets\LOGO-PIX.png'
OUT = os.path.join(DIRBASE, 'Contrato_Aceptacion_Servicio_JoaoGeraldo_SerroAlto.pdf')
FECHA = '25 de junio de 2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')

ss = getSampleStyleSheet()
def st(n, **k): ss.add(ParagraphStyle(n, **k)); return ss[n]
T = st('T', fontName='Helvetica-Bold', fontSize=15, textColor=VERDE, alignment=TA_CENTER, leading=18, spaceAfter=2)
SUBT = st('SUBT', fontName='Helvetica', fontSize=10, textColor=GRIS, alignment=TA_CENTER, spaceAfter=8)
CL = st('CL', fontName='Helvetica-Bold', fontSize=10.5, textColor=VERDE, spaceBefore=8, spaceAfter=3)
B = st('B', fontName='Helvetica', fontSize=9.5, textColor=GRIS, leading=13.5, alignment=TA_JUSTIFY, spaceAfter=4)
BL = st('BL', parent=B, leftIndent=12, spaceAfter=2)

def hf(canvas, doc):
    canvas.saveState()
    try:
        iw, ih = PILImage.open(LOGO).size; lw = 2.0*cm; lh = lw*ih/iw
        canvas.drawImage(LOGO, 2*cm, A4[1]-1.55*cm, width=lw, height=lh, mask='auto', preserveAspectRatio=True)
    except Exception: pass
    canvas.setStrokeColor(VERDE2); canvas.setLineWidth(1.2); canvas.line(2*cm, A4[1]-1.7*cm, A4[0]-2*cm, A4[1]-1.7*cm)
    canvas.setFillColor(VERDE); canvas.setFont('Helvetica-Bold', 8)
    canvas.drawRightString(A4[0]-2*cm, A4[1]-1.4*cm, 'CONTRATO DE SERVICIO')
    canvas.setFillColor(VERDE); canvas.rect(0, 0, A4[0], 0.7*cm, fill=1, stroke=0)
    canvas.setFillColor(white); canvas.setFont('Helvetica', 7.5)
    canvas.drawString(2*cm, 0.27*cm, 'PIXADVISOR — Agricultura de Precisión')
    canvas.drawRightString(A4[0]-2*cm, 0.27*cm, 'Pág. %d' % doc.page); canvas.restoreState()

S = []
S += [Spacer(1, 0.3*cm), Paragraph('CONTRATO DE PRESTACIÓN DE SERVICIOS DE ANÁLISIS DE SUELO Y AGRICULTURA DE PRECISIÓN', T),
      Paragraph('(Aceptación de servicio — Hacienda Serro Alto · Campaña Soya 2026/27)', SUBT),
      HRFlowable(width='100%', thickness=1, color=VERDE2, spaceAfter=8)]

S += [Paragraph('Entre las partes:', B),
 Paragraph('<b>EL PRESTADOR:</b> <b>PIXADVISOR S.R.L.</b>, con domicilio en Santa Cruz de la Sierra, Bolivia, '
   'representada por el Sr. <b>Nilton Luiz Camargo</b> (en adelante, “PIXADVISOR” o “EL PRESTADOR”); y', BL),
 Paragraph('<b>EL CLIENTE:</b> <b>João Geraldo</b>, con C.I./N.I.T. N.º [____________], con domicilio en '
   '[__________________________], propietario/responsable de la <b>Hacienda Serro Alto</b> (en adelante, “EL CLIENTE”).', BL),
 Paragraph('Ambas partes, en adelante “LAS PARTES”, acuerdan celebrar el presente contrato de prestación de servicios, '
   'que se regirá por las siguientes cláusulas:', B)]

clauses = [
 ('PRIMERA — OBJETO',
  'EL PRESTADOR se obliga a ejecutar para EL CLIENTE el servicio de <b>análisis de suelo y mapeo de fertilidad por '
  'ambientes de manejo</b> sobre los lotes de la Hacienda Serro Alto correspondientes a los Bloques 2, 3 y 14, con una '
  '<b>superficie útil de 1.782,8 hectáreas</b> (área de siembra efectiva, con cañadas y drenajes ya descontados, de un '
  'total bruto de 1.871,5 ha), con destino a la campaña de soya 2026/27.'),
 ('SEGUNDA — ALCANCE Y ENTREGABLES',
  'El servicio comprende: (a) delimitación del área útil de cada lote; (b) división en <b>3 ambientes productivos</b> '
  '(Alta/Media/Baja) mediante análisis satelital multitemporal (3 años) y de relieve; (c) <b>muestreo de suelo '
  'georreferenciado</b> (198 muestras compuestas, una por ambiente, con submuestras distribuidas); (d) análisis de '
  'laboratorio; (e) <b>mapas de fertilidad</b> por nutriente; (f) <b>reporte de diagnóstico</b>; (g) <b>recomendación '
  'de fertilización</b>; y (h) <b>mapas de prescripción de tasa variable (VRT)</b>. Los entregables se proveen en PDF y '
  'formatos GIS (GeoJSON/SHP/KML/GeoTIFF).'),
 ('TERCERA — PRECIO',
  'EL CLIENTE pagará a EL PRESTADOR la suma de <b>USD 15,00 (quince 00/100 dólares estadounidenses) por hectárea útil</b>, '
  'lo que sobre 1.782,8 ha arroja un total de <b>USD 26.742,00 (veintiséis mil setecientos cuarenta y dos 00/100 dólares '
  'estadounidenses)</b>, todo incluido. El precio no incluye impuestos de ley si correspondieran, ni el costo de los '
  'fertilizantes o enmiendas.'),
 ('CUARTA — FORMA DE PAGO',
  'El pago se efectuará en dos cuotas: <b>(i) 50% (USD 13.371,00) a la firma del presente contrato</b>; y <b>(ii) 50% '
  '(USD 13.371,00) contra la entrega de los mapas de prescripción de tasa variable (VRT) y las recomendaciones de '
  'fertilización</b>. Los pagos podrán realizarse en dólares estadounidenses o su equivalente en bolivianos al tipo de '
  'cambio oficial del día de pago, mediante depósito/transferencia a la cuenta del PRESTADOR: <b>Banco BISA, Cuenta '
  'Corriente N.º 731810010</b>, a nombre de Pixadvisor S.R.L.'),
 ('QUINTA — PLAZOS Y CRONOGRAMA',
  'El servicio se ejecutará según el siguiente cronograma estimado, contado desde la firma y el primer pago: '
  '(1) planificación y aprobación de la grilla: 1–2 días; (2) muestreo de campo: según superficie y condiciones de acceso; '
  '(3) laboratorio: 7–15 días; (4) procesamiento GIS, mapas y diagnóstico: 3–5 días; (5) entrega y reunión de '
  'presentación de resultados: 1 día. Los plazos están sujetos a las condiciones de campo (humedad/accesibilidad) y a '
  'los tiempos del laboratorio.'),
 ('SEXTA — OBLIGACIONES DEL PRESTADOR',
  'EL PRESTADOR se obliga a: (a) ejecutar el servicio con diligencia profesional y conforme a las buenas prácticas de '
  'agricultura de precisión; (b) registrar cada punto de muestreo con GPS y trazabilidad mediante la app PIX-Muestreo; '
  '(c) entregar la totalidad de los entregables descritos en la cláusula segunda; y (d) mantener la confidencialidad '
  'de los datos del CLIENTE.'),
 ('SÉPTIMA — OBLIGACIONES DEL CLIENTE',
  'EL CLIENTE se obliga a: (a) garantizar el acceso al predio y la información necesaria (límites de lotes, historial); '
  '(b) abonar el precio en la forma y plazos pactados; y (c) designar un responsable de contacto para la coordinación de '
  'campo y la recepción de los entregables.'),
 ('OCTAVA — EXCLUSIONES',
  'El presente contrato <b>no incluye</b> el costo de los fertilizantes, enmiendas ni la operación de su aplicación, los '
  'que, de requerirse, serán objeto de un acuerdo separado (protocolo de aplicación).'),
 ('NOVENA — PROPIEDAD DE LOS DATOS Y CONFIDENCIALIDAD',
  'Los datos, mapas y resultados generados son <b>propiedad del CLIENTE</b>. EL PRESTADOR se compromete a no divulgar ni '
  'compartir con terceros la información del predio (rendimientos, costos, datos de suelo, mapas de prescripción) sin '
  'autorización escrita del CLIENTE, salvo obligación legal.'),
 ('DÉCIMA — FUERZA MAYOR',
  'Ninguna de LAS PARTES será responsable por el incumplimiento o demora derivados de eventos de fuerza mayor o caso '
  'fortuito (sequía extrema, inundación, granizo, restricciones gubernamentales, pandemia u otros fuera de su control). '
  'La parte afectada notificará a la otra dentro de los 5 días y LAS PARTES acordarán la suspensión o renegociación de '
  'los plazos.'),
 ('UNDÉCIMA — RESOLUCIÓN DE CONFLICTOS',
  'Toda controversia derivada del presente contrato se procurará resolver, primero, mediante <b>negociación directa</b>; '
  'en su defecto, mediante <b>conciliación/mediación</b>; y, de subsistir, se someterá a la jurisdicción de los tribunales '
  'ordinarios de <b>Santa Cruz de la Sierra, Estado Plurinacional de Bolivia</b>, renunciando a cualquier otro fuero.'),
 ('DUODÉCIMA — DOMICILIOS Y VIGENCIA',
  'LAS PARTES constituyen domicilio en los indicados en el encabezado, donde se tendrán por válidas las notificaciones. '
  'El presente contrato entra en vigencia a la fecha de su firma y permanecerá vigente hasta la entrega total de los '
  'servicios y la cancelación del precio.'),
]
for tit, txt in clauses:
    S += [Paragraph(tit, CL), Paragraph(txt, B)]

S += [Spacer(1, 6),
 Paragraph('En conformidad, LAS PARTES firman el presente contrato en dos ejemplares de igual tenor, en la ciudad de '
   'Santa Cruz de la Sierra, a los ____ días del mes de __________ de 2026.', B), Spacer(1, 22)]

firmas = Table([
 [Paragraph('______________________________', B), Paragraph('______________________________', B)],
 [Paragraph('<b>PIXADVISOR S.R.L.</b><br/>Nilton Luiz Camargo<br/>EL PRESTADOR', ss['B']),
  Paragraph('<b>João Geraldo</b><br/>C.I./N.I.T. [____________]<br/>EL CLIENTE', ss['B'])]],
 colWidths=[8*cm, 8*cm])
firmas.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 2)]))
S += [firmas]

SimpleDocTemplate(OUT, pagesize=A4, topMargin=2.0*cm, bottomMargin=1.2*cm, leftMargin=2*cm, rightMargin=2*cm,
    title='Contrato de Servicio — Pixadvisor / Joao Geraldo').build(S, onFirstPage=hf, onLaterPages=hf)
print('Contrato ->', os.path.basename(OUT), '%.0f KB' % (os.path.getsize(OUT)/1024))
print('DONE')
