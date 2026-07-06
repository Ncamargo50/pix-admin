# -*- coding: utf-8 -*-
"""BLOQUE 14 v2.1 — Informe al CLIENTE (Joao Geraldo): plan de muestreo de suelo por AMBIENTES
re-analizados (color de suelo desde suelo desnudo + drenaje/topografia + vigor verano).
Encuadre honesto (auditoria): ambientes NOMINALES por color/drenaje; textura/MO/fertilidad -> laboratorio."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether)
import warnings; warnings.filterwarnings('ignore')

BASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUT = os.path.join(BASE, '_analisis_canadas', 'AMBIENTES_V2'); PNGD = os.path.join(OUT, 'informe_png_lote')
CLIENTE = 'João Geraldo'; FECHA = '06/07/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
AMBCOL = {'Altura roja': HexColor('#D84315'), 'Transicion': HexColor('#FFB300'), 'Bajura negra': HexColor('#3E2723')}

zdf = pd.read_csv(os.path.join(OUT, 'B14_zonas_V2.csv'))
pdf_ = pd.read_csv(os.path.join(OUT, 'B14_puntos_V2.csv'))
nP = int((pdf_.tipo == 'PRINCIPAL').sum()); nS = int((pdf_.tipo == 'SUBMUESTRA').sum())
area_lote = zdf.groupby('lote')['area_ha'].sum().to_dict()
area_total = zdf['area_ha'].sum()
prin_lote = pdf_[pdf_.tipo == 'PRINCIPAL'].groupby('lote').size().to_dict()

ss = getSampleStyleSheet()
ss.add(ParagraphStyle('T', parent=ss['Title'], fontSize=20, textColor=VERDE, spaceAfter=4, leading=23))
ss.add(ParagraphStyle('Sub', parent=ss['Normal'], fontSize=12, textColor=GRIS, spaceAfter=3))
ss.add(ParagraphStyle('Cli', parent=ss['Normal'], fontSize=13, textColor=VERDE, spaceAfter=10, fontName='Helvetica-Bold'))
ss.add(ParagraphStyle('H', parent=ss['Heading2'], fontSize=13, textColor=VERDE, spaceBefore=8, spaceAfter=4))
ss.add(ParagraphStyle('B', parent=ss['Normal'], fontSize=10, textColor=GRIS, leading=14, spaceAfter=5))
ss.add(ParagraphStyle('LH', parent=ss['Heading2'], fontSize=13, textColor=VERDE, spaceAfter=3))
ss.add(ParagraphStyle('Cap', parent=ss['Normal'], fontSize=8, textColor=GRIS, alignment=1, spaceBefore=2))
ss.add(ParagraphStyle('Note', parent=ss['Normal'], fontSize=8.5, textColor=GRIS, leading=11, spaceAfter=3, leftIndent=6))

def hf(canvas, doc):
    canvas.saveState(); canvas.setFont('Helvetica-Bold', 9); canvas.setFillColor(VERDE)
    canvas.drawString(2*cm, A4[1]-1.1*cm, 'PIXADVISOR — Agricultura de Precisión')
    canvas.setStrokeColor(VERDE); canvas.setLineWidth(1.1); canvas.line(2*cm, A4[1]-1.25*cm, A4[0]-2*cm, A4[1]-1.25*cm)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(GRIS)
    canvas.drawString(2*cm, 1*cm, 'Pixadvisor AP · Muestreo de suelo por ambientes · Bloque 14 · %s · %s' % (CLIENTE, FECHA))
    canvas.drawRightString(A4[0]-2*cm, 1*cm, 'Página %d' % doc.page); canvas.restoreState()

story = []
story.append(Spacer(1, 6))
story.append(Paragraph('Plan de Muestreo de Suelo por Ambientes — Bloque 14', ss['T']))
story.append(Paragraph('Hacienda Serro Alto · Campaña Soya 2026/27 · Re-análisis con textura y color de suelo', ss['Sub']))
story.append(Paragraph('Cliente: %s' % CLIENTE, ss['Cli']))

story.append(Paragraph('¿Qué hicimos y por qué?', ss['H']))
for txt in [
    'A pedido del equipo de campo, <b>re-analizamos los ambientes del Bloque 14</b> porque la primera versión no '
    'reflejaba lo observado en el terreno: las <b>bajuras con suelo oscuro</b> y las <b>alturas con suelo rojo</b>.',
    '<b>1. Color de suelo real.</b> Reconstruimos el color del suelo a partir de imágenes satelitales de <b>suelo '
    'desnudo (sin cultivo)</b> de la época seca, separando el <b>suelo rojo (bien drenado, en las lomas)</b> del '
    '<b>suelo oscuro (húmedo, en las bajuras)</b>. Este es el eje que ahora define los ambientes.',
    '<b>2. Drenaje y relieve.</b> Incorporamos el <b>flujo de agua, la red de drenaje y el relieve</b> para reforzar '
    'la separación entre las zonas altas bien drenadas y las bajuras que acumulan humedad.',
    '<b>3. Comportamiento del cultivo.</b> Usamos el <b>vigor de la soya de verano</b> de las campañas 2024/25 y '
    '2025/26 (noviembre a marzo) como capa de apoyo.',
    '<b>4. Muestreo dirigido.</b> En cada ambiente de cada lote tomamos una <b>muestra compuesta</b> (mezcla de varias '
    'submuestras distribuidas por toda la zona y alejadas de los bordes), representativa de ese ambiente.']:
    story.append(Paragraph(txt, ss['B']))

story.append(Paragraph('Importante sobre la interpretación', ss['H']))
story.append(Paragraph(
    'Los tres ambientes son <b>categorías por color de suelo y posición en el terreno</b>, <b>no</b> un ranking de '
    'calidad. El suelo oscuro de bajura suele tener más materia orgánica y retención de agua; el suelo rojo de altura '
    'suele estar mejor drenado. <b>La textura (arcilla), la materia orgánica y la fertilidad exactas de cada ambiente '
    'se confirmarán con los análisis de laboratorio de las muestras</b> — ese es justamente el objetivo de esta campaña. '
    'El mapa satelital define <b>dónde muestrear</b>; el laboratorio dirá <b>cuánto y qué aplicar</b> en cada zona.', ss['Note']))

story.append(Paragraph('Alcance del plan', ss['H']))
data = [['Ambiente', 'Área (ha)', '% del bloque', 'Muestras compuestas']]
for amb in ['Altura roja', 'Transicion', 'Bajura negra']:
    s = zdf[zdf.ambiente == amb]; a = s['area_ha'].sum()
    mc = int(pdf_[(pdf_.ambiente == amb) & (pdf_.tipo == 'PRINCIPAL')].shape[0])
    data.append([amb, '%.1f' % a, '%.0f%%' % (a/area_total*100), str(mc)])
data.append(['TOTAL', '%.1f' % area_total, '100%', str(nP)])
t = Table(data, colWidths=[4.5*cm, 3*cm, 3*cm, 4*cm])
tstyle = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9.5),
    ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]
for i, amb in enumerate(['Altura roja', 'Transicion', 'Bajura negra'], 1):
    tstyle += [('TEXTCOLOR', (0, i), (0, i), AMBCOL[amb]), ('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')]
t.setStyle(TableStyle(tstyle)); story.append(t); story.append(Spacer(1, 6))
story.append(Paragraph('Se analizarán <b>%d muestras compuestas</b> sobre <b>%.0f ha</b> en <b>%d lotes</b> del Bloque 14, '
    'integrando <b>%d submuestras</b> en total (varias por muestra) para máxima representatividad. Cada muestra compuesta '
    'corresponde a un ambiente dentro de un lote.' % (nP, area_total, zdf['lote'].nunique(), nS), ss['B']))
story.append(Paragraph('En las páginas siguientes, cada lote con sus ambientes (rojo = altura bien drenada, amarillo = '
    'transición, marrón oscuro = bajura húmeda) y los puntos de muestreo (★ principal, ○ submuestras).', ss['B']))

for lote in sorted(zdf['lote'].unique()):
    s = zdf[zdf.lote == lote].sort_values('zona', ascending=False)
    story.append(PageBreak())
    el = [Paragraph('%s — Bloque 14' % lote, ss['LH'])]
    png = os.path.join(PNGD, '%s.png' % lote)
    if os.path.exists(png):
        im = RLImage(png); im._restrictSize(17*cm, 10*cm); el.append(im)
        el.append(Paragraph('Ambientes y puntos de muestreo sobre imagen satelital.', ss['Cap']))
    uha = area_lote.get(lote, 0)
    d = [['Ambiente', 'Área (ha)', '% del lote', 'Muestras', 'Color/redness', 'Elev (m)']]
    for _, r in s.iterrows():
        d.append([r['ambiente'], '%.1f' % r['area_ha'], '%.0f%%' % (r['area_ha']/uha*100 if uha else 0),
                  str(int(pdf_[(pdf_.lote == lote) & (pdf_.zona == r['zona']) & (pdf_.tipo == 'PRINCIPAL')].shape[0])),
                  '%.2f' % r['redness'], '%.0f' % r['elev_m']])
    d.append(['TOTAL', '%.1f' % uha, '100%', str(int(prin_lote.get(lote, 0))), '', ''])
    tt = Table(d, colWidths=[3.6*cm, 2.4*cm, 2.2*cm, 2*cm, 2.8*cm, 2.2*cm])
    ts = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
          ('FONTSIZE', (0, 0), (-1, -1), 9), ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
          ('BACKGROUND', (0, -1), (-1, -1), GRISC), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
          ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]
    for i, (_, r) in enumerate(s.iterrows(), 1):
        ts += [('TEXTCOLOR', (0, i), (0, i), AMBCOL.get(r['ambiente'], GRIS)), ('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')]
    tt.setStyle(TableStyle(ts)); el.append(Spacer(1, 5)); el.append(tt)
    story.append(KeepTogether(el))

OUTPDF = os.path.join(BASE, 'Informe_Cliente_Bloque14_Ambientes_v2_SerroAlto.pdf')
SimpleDocTemplate(OUTPDF, pagesize=A4, topMargin=1.6*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(
    story, onFirstPage=hf, onLaterPages=hf)
print('Informe cliente ->', os.path.basename(OUTPDF), '%.0f KB' % (os.path.getsize(OUTPDF)/1024))
print('DONE informe')
