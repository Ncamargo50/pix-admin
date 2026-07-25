# -*- coding: utf-8 -*-
"""Informe al CLIENTE (Joao Geraldo) — Plan de muestreo de suelo por ambientes.
1 pagina por lote: mapa (ambientes + puntos) + resumen del plan. PDF Pixadvisor."""
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

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas')
PNGDIR = os.path.join(OUTDIR, 'muestreo_png')
CLIENTE = 'João Geraldo'; FECHA = '25/06/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
ROJO = HexColor('#F44336'); AMA = HexColor('#FBC02D'); VER = HexColor('#4CAF50')
CLCOL = {'Baja': ROJO, 'Media': AMA, 'Alta': VER}

pts = pd.read_csv(os.path.join(DIRBASE, 'Puntos_muestreo.csv')); pts['bloque'] = pts['bloque'].astype(int)
zst = pd.read_csv(os.path.join(DIRBASE, 'Zonas_manejo_estadisticas.csv'))
zarea = {(r['lote_id'], int(r['zona'])): r['area_ha'] for _, r in zst.iterrows()}
util = pd.read_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv')); util['bloque'] = util['bloque'].astype(int)
utidx = util.set_index('lote_id')

ss = getSampleStyleSheet()
ss.add(ParagraphStyle('T', parent=ss['Title'], fontSize=21, textColor=VERDE, spaceAfter=4, leading=24))
ss.add(ParagraphStyle('Sub', parent=ss['Normal'], fontSize=12, textColor=GRIS, spaceAfter=3))
ss.add(ParagraphStyle('Cli', parent=ss['Normal'], fontSize=13, textColor=VERDE, spaceAfter=10, fontName='Helvetica-Bold'))
ss.add(ParagraphStyle('H', parent=ss['Heading2'], fontSize=13.5, textColor=VERDE, spaceBefore=8, spaceAfter=4))
ss.add(ParagraphStyle('B', parent=ss['Normal'], fontSize=10, textColor=GRIS, leading=14, spaceAfter=5))
ss.add(ParagraphStyle('LH', parent=ss['Heading2'], fontSize=13, textColor=VERDE, spaceAfter=3))
ss.add(ParagraphStyle('Cap', parent=ss['Normal'], fontSize=8, textColor=GRIS, alignment=1, spaceBefore=2))

def hf(canvas, doc):
    canvas.saveState(); canvas.setFont('Helvetica-Bold', 9); canvas.setFillColor(VERDE)
    canvas.drawString(2*cm, A4[1]-1.1*cm, 'PIXADVISOR — Agricultura de Precisión')
    canvas.setStrokeColor(VERDE); canvas.setLineWidth(1.1); canvas.line(2*cm, A4[1]-1.25*cm, A4[0]-2*cm, A4[1]-1.25*cm)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(GRIS)
    canvas.drawString(2*cm, 1*cm, 'Pixadvisor AP · Plan de muestreo de suelo · Cliente: %s · %s' % (CLIENTE, FECHA))
    canvas.drawRightString(A4[0]-2*cm, 1*cm, 'Página %d' % doc.page); canvas.restoreState()

story = []
nP = (pts.tipo == 'PRINCIPAL').sum(); nS = (pts.tipo == 'SUBMUESTRA').sum()
story.append(Spacer(1, 6))
story.append(Paragraph('Plan de Muestreo de Suelo por Ambientes', ss['T']))
story.append(Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27', ss['Sub']))
story.append(Paragraph('Cliente: %s' % CLIENTE, ss['Cli']))
story.append(Paragraph('¿Qué vamos a hacer?', ss['H']))
for txt in [
    '<b>1. Área útil real.</b> Delimitamos la superficie efectivamente sembrable de cada lote, descontando las '
    'cañadas y drenajes no cultivables (combinando los drenajes relevados en campo con análisis satelital y de relieve).',
    '<b>2. Ambientes productivos.</b> Dividimos cada lote en 3 ambientes (Alta, Media y Baja productividad) a partir de '
    '<b>3 años de imágenes satelitales</b> (vigor estable de la vegetación) combinados con el <b>relieve y la red de drenaje</b>. '
    'Así separamos las zonas que históricamente rinden distinto.',
    '<b>3. Muestreo dirigido y representativo.</b> En cada ambiente tomamos una <b>muestra compuesta</b> (mezcla de varias '
    'submuestras distribuidas por toda la zona y alejadas de los bordes), que caracteriza fielmente la fertilidad de ese ambiente.',
    '<b>4. Resultado para usted.</b> Recomendaciones de <b>fertilización y manejo sitio-específicas por ambiente</b>: '
    'aplicar lo justo donde corresponde, optimizando insumos y apuntando a un rendimiento más parejo y rentable.']:
    story.append(Paragraph(txt, ss['B']))

story.append(Paragraph('Alcance del plan', ss['H']))
bl = pts.groupby('bloque').agg(lotes=('lote_id', 'nunique'),
     P=('tipo', lambda s: (s == 'PRINCIPAL').sum()), S=('tipo', lambda s: (s == 'SUBMUESTRA').sum())).reset_index()
data = [['Bloque', 'Lotes', 'Ambientes', 'Muestras a analizar', 'Área útil (ha)']]
for _, r in bl.iterrows():
    ut = util[util.bloque == r['bloque']]['util_ha'].sum()
    data.append([str(r['bloque']), int(r['lotes']), int(r['lotes'])*3, int(r['P']), '%.1f' % ut])
data.append(['TOTAL', pts['lote_id'].nunique(), pts['lote_id'].nunique()*3, int(nP), '%.1f' % util['util_ha'].sum()])
t = Table(data, colWidths=[2.2*cm, 2*cm, 2.6*cm, 4*cm, 3.2*cm])
t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9.5),
    ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(t); story.append(Spacer(1, 6))
story.append(Paragraph('Se analizarán <b>%d muestras compuestas</b> (una por ambiente) sobre <b>%.0f ha útiles</b> en %d lotes. '
    'Cada muestra integra varias submuestras (%d sub-tomas en total) para máxima representatividad.'
    % (nP, util['util_ha'].sum(), pts['lote_id'].nunique(), nS), ss['B']))
story.append(Paragraph('En las páginas siguientes se presenta cada lote con sus 3 ambientes (Alta = verde, Media = amarillo, '
    'Baja = rojo) y la ubicación de los puntos de muestreo.', ss['B']))

# --- pagina por lote ---
for lid in sorted(pts['lote_id'].unique()):
    sub = pts[pts.lote_id == lid]; bloque = sub['bloque'].iloc[0]
    story.append(PageBreak())
    el = [Paragraph('%s — Bloque %s' % (lid, bloque), ss['LH'])]
    png = os.path.join(PNGDIR, '%s_muestreo.png' % lid)
    if os.path.exists(png):
        im = RLImage(png); im._restrictSize(17*cm, 9.5*cm); el.append(im)
        el.append(Paragraph('Ambientes de manejo y puntos de muestreo sobre imagen satelital.', ss['Cap']))
    d = [['Ambiente', 'Área (ha)', '% del lote', 'Muestras compuestas']]
    uha = utidx.loc[lid, 'util_ha'] if lid in utidx.index else 0
    for zona in sorted(sub['zona'].unique()):
        zs = sub[sub.zona == zona]; clase = zs['clase'].iloc[0]
        nprin = (zs.tipo == 'PRINCIPAL').sum(); area = zarea.get((lid, int(zona)), 0)
        d.append([clase, '%.1f' % area, '%.0f%%' % (area/uha*100 if uha else 0), str(nprin)])
    d.append(['TOTAL', '%.1f' % uha, '100%', str((sub.tipo == 'PRINCIPAL').sum())])
    tt = Table(d, colWidths=[3.2*cm, 3*cm, 3*cm, 4.5*cm])
    tstyle = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
              ('FONTSIZE', (0, 0), (-1, -1), 9.5), ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
              ('BACKGROUND', (0, -1), (-1, -1), GRISC), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
              ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]
    for i, zona in enumerate(sorted(sub['zona'].unique()), 1):
        clase = sub[sub.zona == zona]['clase'].iloc[0]
        tstyle += [('TEXTCOLOR', (0, i), (0, i), CLCOL.get(clase, GRIS)), ('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')]
    tt.setStyle(TableStyle(tstyle)); el.append(Spacer(1, 5)); el.append(tt)
    story.append(KeepTogether(el))

OUT = os.path.join(DIRBASE, 'Informe_Cliente_JoaoGeraldo_Plan_Muestreo_SerroAlto.pdf')
SimpleDocTemplate(OUT, pagesize=A4, topMargin=1.6*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(
    story, onFirstPage=hf, onLaterPages=hf)
print('Informe cliente ->', os.path.basename(OUT), '%.0f KB' % (os.path.getsize(OUT)/1024))
print('DONE')
