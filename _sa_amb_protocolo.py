# -*- coding: utf-8 -*-
"""Protocolo de Muestreo de Suelo de Campo — Hacienda CERRO ALTO (ambientes v2.1).
1 pagina por lote (mapa + plan de muestras + nomenclatura P{zona}) + instrucciones de composite.
Datos v2.1: SerroAlto_{puntos,zonas}_V2.csv + informe_png_lote."""
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
FECHA = '06/07/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
AMBCOL = {'Altura roja': HexColor('#D84315'), 'Transicion': HexColor('#FFB300'), 'Bajura negra': HexColor('#3E2723')}
ORD = ['Altura roja', 'Transicion', 'Bajura negra']

zdf = pd.read_csv(os.path.join(OUT, 'SerroAlto_zonas_V2.csv')); zdf['bloque'] = zdf['bloque'].astype(str)
pdf_ = pd.read_csv(os.path.join(OUT, 'SerroAlto_puntos_V2.csv')); pdf_['bloque'] = pdf_['bloque'].astype(str)
nP = int((pdf_.tipo == 'PRINCIPAL').sum()); nS = int((pdf_.tipo == 'SUBMUESTRA').sum())

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
    canvas.drawString(2*cm, 1*cm, 'Pixadvisor AP · Protocolo de muestreo de suelo · Hacienda Cerro Alto · %s' % FECHA)
    canvas.drawRightString(A4[0]-2*cm, 1*cm, 'Página %d' % doc.page); canvas.restoreState()

story = []
story.append(Paragraph('Protocolo de Muestreo de Suelo de Campo', ss['T']))
story.append(Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27 · Bloques 2, 3 y 14', ss['Sub']))
story.append(Paragraph('Objetivo', ss['H']))
story.append(Paragraph('Guía operativa para la colecta georreferenciada de muestras de suelo por ambiente. Cada lote está '
    'dividido en ambientes por <b>color y posición del suelo</b> (Altura roja / Transición / Bajura negra); cada ambiente '
    'se muestrea con <b>una muestra compuesta</b> (punto principal), formada por submuestras distribuidas en toda la zona.', ss['B']))
story.append(Paragraph('Resumen de la campaña', ss['H']))
data = [['Bloque', 'Lotes', 'Muestras compuestas', 'Submuestras', 'Área (ha)']]
for bk in ['2', '3', '14']:
    zb = zdf[zdf.bloque == bk]; pb = pdf_[pdf_.bloque == bk]
    data.append([bk, zb['lote'].nunique(), int((pb.tipo == 'PRINCIPAL').sum()), int((pb.tipo == 'SUBMUESTRA').sum()), '%.0f' % zb['area_ha'].sum()])
data.append(['TOTAL', zdf.groupby(['bloque', 'lote']).ngroups, int(nP), int(nS), '%.0f' % zdf['area_ha'].sum()])
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
    '<b>2. Recorrido:</b> dentro de cada ambiente, ir al punto <b>principal (P1/P2/P3)</b> y recolectar las submuestras '
    'distribuidas por toda la zona con barreno o pala recta. Los puntos ya están a ≥20 m del borde.',
    '<b>3. Composite:</b> mezclar TODAS las submuestras de un mismo principal en un balde plástico limpio, homogeneizar y '
    'extraer ~500 g → 1 bolsa = 1 muestra compuesta = 1 ambiente.',
    '<b>4. Rótulo:</b> etiquetar la bolsa con el ID del principal (ej. <b>L07-B14-P1</b>). Una bolsa por principal.',
    '<b>5. Evitar:</b> bordes, cabeceras, caminos, cañadas/drenajes, manchas anómalas y sitios de acopio o quema.',
    '<b>6. Registro:</b> marcar cada punto como colectado en el APK <b>PIX Muestreo</b> (GPS) a medida que se avanza. '
    'En el APK las zonas se ven en rojo/amarillo/verde (Bajura/Transición/Altura).']:
    story.append(Paragraph(txt, ss['B']))
story.append(Paragraph('Ambientes: <b>Altura roja</b> (suelo rojo, bien drenado) · <b>Transición</b> · '
    '<b>Bajura negra</b> (suelo oscuro, húmedo). El punto principal de cada ambiente se identifica como P{nº de ambiente}.', ss['B']))

# --- pagina por lote (agrupado por bloque) ---
for bk in ['2', '3', '14']:
    zb = zdf[zdf.bloque == bk]
    for lote in sorted(zb['lote'].unique()):
        s = zb[zb.lote == lote].copy()
        s['ord'] = s['ambiente'].map({a: i for i, a in enumerate(ORD)}); s = s.sort_values('ord')
        story.append(PageBreak())
        el = [Paragraph('%s — Bloque %s' % (lote, bk), ss['LH'])]
        png = os.path.join(PNGD, 'B%s_%s.png' % (bk, lote))
        if os.path.exists(png):
            im = RLImage(png); im._restrictSize(17*cm, 9*cm); el.append(im)
        d = [['Ambiente', 'Área (ha)', 'Muestra compuesta', 'Submuestras', 'Rótulo bolsa']]
        for _, r in s.iterrows():
            pp = pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.zona == r['zona']) & (pdf_.tipo == 'PRINCIPAL')]
            pid = pp['punto_id'].iloc[0] if len(pp) else '-'
            nsub = int(pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.zona == r['zona']) & (pdf_.tipo == 'SUBMUESTRA')].shape[0])
            d.append([r['ambiente'], '%.1f' % r['area_ha'], 'P%d' % r['zona'], str(nsub), pid])
        totP = int((pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.tipo == 'PRINCIPAL')]).shape[0])
        totS = int((pdf_[(pdf_.bloque == bk) & (pdf_.lote == lote) & (pdf_.tipo == 'SUBMUESTRA')]).shape[0])
        d.append(['TOTAL LOTE', '%.1f' % s['area_ha'].sum(), '%d muestras' % totP, str(totS), ''])
        tt = Table(d, colWidths=[3.4*cm, 2.2*cm, 3.2*cm, 2.4*cm, 4.8*cm])
        tstyle = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                  ('FONTSIZE', (0, 0), (-1, -1), 8.5), ('GRID', (0, 0), (-1, -1), 0.4, colors.grey), ('ALIGN', (1, 0), (3, -1), 'CENTER'),
                  ('BACKGROUND', (0, -1), (-1, -1), GRISC), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                  ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]
        for i, (_, r) in enumerate(s.iterrows(), 1):
            tstyle += [('TEXTCOLOR', (0, i), (0, i), AMBCOL.get(r['ambiente'], GRIS)), ('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')]
        tt.setStyle(TableStyle(tstyle)); el.append(Spacer(1, 5)); el.append(tt)
        story.append(KeepTogether(el))

OUTPDF = os.path.join(BASE, 'Protocolo_Muestreo_Campo_CerroAlto.pdf')
SimpleDocTemplate(OUTPDF, pagesize=A4, topMargin=1.6*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(
    story, onFirstPage=hf, onLaterPages=hf)
print('Protocolo ->', os.path.basename(OUTPDF), '%.0f KB' % (os.path.getsize(OUTPDF)/1024))
print('DONE protocolo')
