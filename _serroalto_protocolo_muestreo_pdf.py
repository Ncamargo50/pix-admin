# -*- coding: utf-8 -*-
"""Protocolo de Muestreo de Suelo de Campo — PDF Pixadvisor. 1 pagina por lote
(mapa + plan de muestras + nomenclatura) + instrucciones de composite."""
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
PNGDIR = os.path.join(DIRBASE, '_analisis_canadas', 'muestreo_png')
FECHA = '25/06/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
ROJO = HexColor('#F44336'); AMA = HexColor('#FBC02D'); VER = HexColor('#4CAF50')
CLCOL = {'Baja': ROJO, 'Media': AMA, 'Alta': VER}

pts = pd.read_csv(os.path.join(DIRBASE, 'Puntos_muestreo.csv'))
pts['bloque'] = pts['bloque'].astype(int)
zst = pd.read_csv(os.path.join(DIRBASE, 'Zonas_manejo_estadisticas.csv'))
zarea = {(r['lote_id'], int(r['zona'])): r['area_ha'] for _, r in zst.iterrows()}
util = pd.read_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv')).set_index('lote_id')

ss = getSampleStyleSheet()
ss.add(ParagraphStyle('T', parent=ss['Title'], fontSize=19, textColor=VERDE, spaceAfter=4, leading=22))
ss.add(ParagraphStyle('Sub', parent=ss['Normal'], fontSize=11, textColor=GRIS, spaceAfter=8))
ss.add(ParagraphStyle('H', parent=ss['Heading2'], fontSize=13, textColor=VERDE, spaceBefore=8, spaceAfter=4))
ss.add(ParagraphStyle('B', parent=ss['Normal'], fontSize=9.5, textColor=GRIS, leading=13, spaceAfter=4))
ss.add(ParagraphStyle('Cap', parent=ss['Normal'], fontSize=8, textColor=GRIS, alignment=1))
ss.add(ParagraphStyle('LH', parent=ss['Heading2'], fontSize=13, textColor=VERDE, spaceAfter=3))

def hf(canvas, doc):
    canvas.saveState(); canvas.setFont('Helvetica-Bold', 9); canvas.setFillColor(VERDE)
    canvas.drawString(2*cm, A4[1]-1.1*cm, 'PIXADVISOR — Agricultura de Precisión')
    canvas.setStrokeColor(VERDE); canvas.setLineWidth(1.1); canvas.line(2*cm, A4[1]-1.25*cm, A4[0]-2*cm, A4[1]-1.25*cm)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(GRIS)
    canvas.drawString(2*cm, 1*cm, 'Pixadvisor AP · Protocolo de muestreo de suelo · %s' % FECHA)
    canvas.drawRightString(A4[0]-2*cm, 1*cm, 'Página %d' % doc.page); canvas.restoreState()

story = []
nP = (pts.tipo == 'PRINCIPAL').sum(); nS = (pts.tipo == 'SUBMUESTRA').sum()
story.append(Paragraph('Protocolo de Muestreo de Suelo de Campo', ss['T']))
story.append(Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27 · Bloques 2, 3 y 14', ss['Sub']))
story.append(Paragraph('Objetivo', ss['H']))
story.append(Paragraph('Guía operativa para la colecta georreferenciada de muestras de suelo por ambiente de manejo. '
    'Cada lote está dividido en 3 ambientes (Baja/Media/Alta); cada ambiente se muestrea con una o más muestras '
    '<b>compuestas</b> (principales), formadas por submuestras distribuidas en todo el ambiente.', ss['B']))
story.append(Paragraph('Resumen de la campaña', ss['H']))
bl = pts.groupby('bloque').agg(lotes=('lote_id', 'nunique'),
     P=('tipo', lambda s: (s == 'PRINCIPAL').sum()), S=('tipo', lambda s: (s == 'SUBMUESTRA').sum())).reset_index()
data = [['Bloque', 'Lotes', 'Muestras principales', 'Submuestras', 'Área útil (ha)']]
for _, r in bl.iterrows():
    ut = util[util.bloque == r['bloque']]['util_ha'].sum()
    data.append([str(r['bloque']), int(r['lotes']), int(r['P']), int(r['S']), '%.1f' % ut])
data.append(['TOTAL', pts['lote_id'].nunique(), int(nP), int(nS), '%.1f' % util['util_ha'].sum()])
t = Table(data, colWidths=[2.2*cm, 2*cm, 4.2*cm, 3*cm, 3.2*cm])
t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
story.append(t); story.append(Spacer(1, 8))

story.append(Paragraph('Instrucciones de colecta (muestra compuesta por ambiente)', ss['H']))
for txt in [
    '<b>1. Profundidad:</b> 0–20 cm (capa arable). Mantener la misma profundidad en todas las submuestras.',
    '<b>2. Recorrido:</b> dentro de cada ambiente, dirigirse a cada punto <b>principal</b> (rojo) y recolectar las submuestras '
    '(naranja) <b>distribuidas por toda la zona</b> con barreno o pala recta. Los puntos ya están a ≥20 m del borde.',
    '<b>3. Composite:</b> mezclar TODAS las submuestras de un mismo principal en un balde plástico limpio, homogeneizar bien y '
    'extraer ~500 g → 1 bolsa = 1 muestra compuesta = 1 ambiente.',
    '<b>4. Rótulo:</b> etiquetar la bolsa con el ID del principal (ej. <b>B14-L06-Z1-P1</b>). Una bolsa por principal.',
    '<b>5. Evitar:</b> bordes, cabeceras, caminos, cañadas/drenajes, manchas anómalas y sitios de acopio o quema.',
    '<b>6. Registro:</b> marcar cada punto como colectado en el APK PIX Muestreo (GPS) a medida que se avanza.']:
    story.append(Paragraph(txt, ss['B']))
story.append(Paragraph('Colores de ambiente: <b>Baja</b> (rojo) · <b>Media</b> (amarillo) · <b>Alta</b> (verde).', ss['B']))

# --- pagina por lote ---
for lid in sorted(pts['lote_id'].unique()):
    sub = pts[pts.lote_id == lid]; bloque = sub['bloque'].iloc[0]
    story.append(PageBreak())
    el = [Paragraph('%s — Bloque %s' % (lid, bloque), ss['LH'])]
    png = os.path.join(PNGDIR, '%s_muestreo.png' % lid)
    if os.path.exists(png):
        im = RLImage(png); im._restrictSize(17*cm, 9*cm); el.append(im)
    # tabla por zona
    d = [['Ambiente', 'Área (ha)', 'Principales', 'Submuestras', 'Nomenclatura principales']]
    for zona in sorted(sub['zona'].unique()):
        zs = sub[sub.zona == zona]; clase = zs['clase'].iloc[0]
        prins = sorted(zs[zs.tipo == 'PRINCIPAL']['punto_id'].unique())
        nsub = (zs.tipo == 'SUBMUESTRA').sum()
        area = zarea.get((lid, int(zona)), 0)
        nom = ', '.join(p.split('-Z')[-1] and 'Z'+p.split('-Z')[1] for p in prins)
        d.append([clase, '%.1f' % area, str(len(prins)), str(nsub), nom])
    totP = (sub.tipo == 'PRINCIPAL').sum(); totS = (sub.tipo == 'SUBMUESTRA').sum()
    d.append(['TOTAL LOTE', '%.1f' % (util.loc[lid, 'util_ha'] if lid in util.index else 0), str(totP), str(totS), '%d muestras compuestas' % totP])
    tt = Table(d, colWidths=[2.6*cm, 2*cm, 2.2*cm, 2.4*cm, 6.8*cm])
    tstyle = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
              ('FONTSIZE', (0, 0), (-1, -1), 8.5), ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('ALIGN', (1, 0), (3, -1), 'CENTER'),
              ('BACKGROUND', (0, -1), (-1, -1), GRISC), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
              ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
    for i, zona in enumerate(sorted(sub['zona'].unique()), 1):
        clase = sub[sub.zona == zona]['clase'].iloc[0]
        tstyle.append(('TEXTCOLOR', (0, i), (0, i), CLCOL.get(clase, GRIS)))
        tstyle.append(('FONTNAME', (0, i), (0, i), 'Helvetica-Bold'))
    tt.setStyle(TableStyle(tstyle))
    el.append(Spacer(1, 5)); el.append(tt)
    story.append(KeepTogether(el))

OUT = os.path.join(DIRBASE, 'Protocolo_Muestreo_Campo_SerroAlto.pdf')
SimpleDocTemplate(OUT, pagesize=A4, topMargin=1.6*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(
    story, onFirstPage=hf, onLaterPages=hf)
print('Protocolo ->', os.path.basename(OUT), '%.0f KB' % (os.path.getsize(OUT)/1024))
print('DONE')
