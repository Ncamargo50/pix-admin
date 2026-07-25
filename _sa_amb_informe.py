# -*- coding: utf-8 -*-
"""SERRO ALTO v2.1 — Informe al CLIENTE (Joao Geraldo): plan de muestreo por AMBIENTES,
los 3 bloques (2, 3, 14). Encuadre honesto: ambientes NOMINALES por color/drenaje;
textura/MO/fertilidad -> laboratorio."""
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
OVER = os.path.join(OUT, 'MAPA_AMBIENTES_SerroAlto_v2.png')
CLIENTE = 'João Geraldo'; FECHA = '06/07/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
AMBCOL = {'Altura roja': HexColor('#D84315'), 'Transicion': HexColor('#FFB300'), 'Bajura negra': HexColor('#3E2723')}
ORD = ['Altura roja', 'Transicion', 'Bajura negra']

def _natkey(s):  # orden natural por numero de fila + letra (1C, 2B, 2C, ... 10C)
    s = str(s); num = ''
    for ch in s:
        if ch.isdigit(): num += ch
        else: break
    return (int(num) if num else 0, s)

zdf = pd.read_csv(os.path.join(OUT, 'SerroAlto_zonas_V2.csv')); zdf['bloque'] = zdf['bloque'].astype(str)
pdf_ = pd.read_csv(os.path.join(OUT, 'SerroAlto_puntos_V2.csv')); pdf_['bloque'] = pdf_['bloque'].astype(str)
nP = int((pdf_.tipo == 'PRINCIPAL').sum()); nS = int((pdf_.tipo == 'SUBMUESTRA').sum())
area_total = zdf['area_ha'].sum()

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
    canvas.drawString(2*cm, 1*cm, 'Pixadvisor AP · Muestreo de suelo por ambientes · Hacienda Cerro Alto · %s · %s' % (CLIENTE, FECHA))
    canvas.drawRightString(A4[0]-2*cm, 1*cm, 'Página %d' % doc.page); canvas.restoreState()

story = [Spacer(1, 6)]
story.append(Paragraph('Plan de Muestreo de Suelo por Ambientes', ss['T']))
story.append(Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27 · Bloques 2, 3 y 14', ss['Sub']))
story.append(Paragraph('Cliente: %s' % CLIENTE, ss['Cli']))

story.append(Paragraph('¿Qué hicimos y por qué?', ss['H']))
for txt in [
    'A pedido del equipo de campo, <b>re-analizamos los ambientes de toda la hacienda</b> porque la primera versión no '
    'reflejaba lo observado en el terreno: las <b>bajuras con suelo oscuro</b> y las <b>alturas con suelo rojo</b>.',
    '<b>1. Color de suelo real.</b> Reconstruimos el color del suelo con imágenes satelitales de <b>suelo desnudo '
    '(sin cultivo), de la época seca</b>, separando el <b>suelo rojo (bien drenado, en las lomas)</b> del <b>suelo '
    'oscuro (húmedo, en las bajuras)</b>. Este es el eje que ahora define los ambientes.',
    '<b>2. Drenaje y relieve.</b> Sumamos el <b>flujo de agua, la red de drenaje y el relieve</b> para reforzar la '
    'separación entre zonas altas bien drenadas y bajuras que acumulan humedad.',
    '<b>3. Comportamiento del cultivo.</b> Usamos el <b>vigor de la soya de verano</b> (campañas 2024/25 y 2025/26, '
    'noviembre a marzo) como capa de apoyo.',
    '<b>4. Muestreo dirigido.</b> En cada ambiente de cada lote se toma una <b>muestra compuesta</b> (mezcla de varias '
    'submuestras distribuidas por toda la zona y alejadas de los bordes), representativa de ese ambiente.']:
    story.append(Paragraph(txt, ss['B']))

story.append(Paragraph('Importante sobre la interpretación', ss['H']))
story.append(Paragraph(
    'Los tres ambientes son <b>categorías por color de suelo y posición en el terreno</b>, <b>no</b> un ranking de '
    'calidad. El suelo oscuro de bajura suele tener más materia orgánica y retención de agua; el rojo de altura suele '
    'estar mejor drenado. <b>La textura (arcilla), la materia orgánica y la fertilidad exactas se confirmarán con los '
    'análisis de laboratorio</b> — ese es el objetivo de esta campaña. El mapa define <b>dónde muestrear</b>; el '
    'laboratorio dirá <b>cuánto y qué aplicar</b> en cada zona.', ss['Note']))

if os.path.exists(OVER):
    im = RLImage(OVER); im._restrictSize(17*cm, 12*cm); story.append(Spacer(1, 4)); story.append(im)
    story.append(Paragraph('Mapa general de ambientes de la Hacienda Cerro Alto (Bloques 2, 3 y 14).', ss['Cap']))

story.append(Paragraph('Alcance del plan', ss['H']))
data = [['Bloque', 'Lotes', 'Ambientes', 'Muestras compuestas', 'Submuestras', 'Área (ha)']]
for bk in ['2', '3', '14']:
    zb = zdf[zdf.bloque == bk]; pb = pdf_[pdf_.bloque == bk]
    data.append([bk, zb['lote'].nunique(), len(zb), int((pb.tipo == 'PRINCIPAL').sum()),
                 int((pb.tipo == 'SUBMUESTRA').sum()), '%.0f' % zb['area_ha'].sum()])
data.append(['TOTAL', zdf['lote'].nunique() if False else zdf.groupby(['bloque', 'lote']).ngroups, len(zdf), nP, nS, '%.0f' % area_total])
t = Table(data, colWidths=[2*cm, 2*cm, 2.2*cm, 3.6*cm, 2.6*cm, 2.4*cm])
t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9.5),
    ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(t); story.append(Spacer(1, 6))
story.append(Paragraph('En total se analizarán <b>%d muestras compuestas</b> sobre <b>%.0f ha</b> en <b>%d lotes</b> de '
    'los 3 bloques, integrando <b>%d submuestras</b> para máxima representatividad.' % (
    nP, area_total, zdf.groupby(['bloque', 'lote']).ngroups, nS), ss['B']))

# páginas por lote (agrupadas por bloque)
for bk in ['2', '3', '14']:
    zb = zdf[zdf.bloque == bk]
    story.append(PageBreak())
    story.append(Paragraph('BLOQUE %s' % bk, ss['T']))
    story.append(Paragraph('%d lotes · %.0f ha · %d muestras compuestas' % (
        zb['lote'].nunique(), zb['area_ha'].sum(), int((pdf_[(pdf_.bloque == bk) & (pdf_.tipo == 'PRINCIPAL')]).shape[0])), ss['Sub']))
    for lote in sorted(zb['lote'].unique(), key=_natkey):
        s = zb[zb.lote == lote].copy()
        s['ord'] = s['ambiente'].map({a: i for i, a in enumerate(ORD)}); s = s.sort_values('ord')
        el = [Paragraph('%s — Bloque %s' % (lote, bk), ss['LH'])]
        png = os.path.join(PNGD, 'B%s_%s.png' % (bk, lote))
        if os.path.exists(png):
            im = RLImage(png); im._restrictSize(17*cm, 10*cm); el.append(im)
            el.append(Paragraph('Ambientes y puntos de muestreo sobre imagen satelital.', ss['Cap']))
        uha = s['area_ha'].sum()
        d = [['Ambiente', 'Punto principal', 'Submuestras', 'Área (ha)', '% lote', 'Elev (m)']]
        for _, r in s.iterrows():
            pp = pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.zona == r['zona']) & (pdf_.tipo == 'PRINCIPAL')]
            pid = pp['punto_id'].iloc[0] if len(pp) else '-'
            nsub = int(pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.zona == r['zona']) & (pdf_.tipo == 'SUBMUESTRA')].shape[0])
            d.append([r['ambiente'], pid, str(nsub), '%.1f' % r['area_ha'],
                      '%.0f%%' % (r['area_ha']/uha*100 if uha else 0), '%.0f' % r['elev_m']])
        nprin_l = int(pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.tipo == 'PRINCIPAL')].shape[0])
        nsub_l = int(pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.tipo == 'SUBMUESTRA')].shape[0])
        d.append(['TOTAL (%d muestras)' % nprin_l, '', str(nsub_l), '%.1f' % uha, '100%', ''])
        tt = Table(d, colWidths=[3.2*cm, 3.6*cm, 2.4*cm, 2.2*cm, 1.8*cm, 1.8*cm])
        ts = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
              ('FONTSIZE', (0, 0), (-1, -1), 9), ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
              ('BACKGROUND', (0, -1), (-1, -1), GRISC), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
              ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]
        for i, (_, r) in enumerate(s.iterrows(), 1):
            ts += [('TEXTCOLOR', (0, i), (0, i), AMBCOL.get(r['ambiente'], GRIS)), ('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')]
        tt.setStyle(TableStyle(ts)); el.append(Spacer(1, 5)); el.append(tt)
        story.append(KeepTogether(el)); story.append(Spacer(1, 10))

OUTPDF = os.path.join(BASE, 'Informe_Cliente_SerroAlto_Ambientes_v2.pdf')
SimpleDocTemplate(OUTPDF, pagesize=A4, topMargin=1.6*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(
    story, onFirstPage=hf, onLaterPages=hf)
print('Informe cliente ->', os.path.basename(OUTPDF), '%.0f KB' % (os.path.getsize(OUTPDF)/1024))
print('DONE informe')
