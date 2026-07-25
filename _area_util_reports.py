# -*- coding: utf-8 -*-
"""Regenera informes de Área Útil (Resumen + Completo) con nomenclatura final."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd, geopandas as gpd, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
import warnings; warnings.filterwarnings('ignore')

D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUT = os.path.join(D, '_analisis_canadas'); FECHA = '26/06/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
m = pd.read_csv(os.path.join(D, 'MAESTRO_lotes_FINAL.csv'))
TOT = m[['gross_ha', 'canada_ha', 'util_ha']].sum()

# overview map
OVER = os.path.join(OUT, 'overview_area_util_FINAL.png')
div = gpd.read_file(os.path.join(D, 'LOTES_DIVISIONES_GLOBAL.geojson')).to_crs(31981)
dren = gpd.read_file(os.path.join(D, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(31981)
cmap = {2: '#66bd63', 3: '#1a9850', 14: '#a6d96a'}
fig, ax = plt.subplots(figsize=(9, 10))
for b, s in div.groupby(div.bloque.astype(int)):
    s.plot(ax=ax, color=cmap.get(b, '#a6d96a'), edgecolor='#333', linewidth=0.4)
dren.plot(ax=ax, color='#1565C0', alpha=0.9)
ax.legend(handles=[mp.Patch(color='#66bd63', label='Bloque 2'), mp.Patch(color='#1a9850', label='Bloque 3'),
                   mp.Patch(color='#a6d96a', label='Bloque 14'), mp.Patch(color='#1565C0', label='Cañada/drenaje')], loc='upper right', fontsize=9)
ax.set_title('Cerro Alto — Área útil por lote/división (verde) y cañadas/drenajes (azul)', fontsize=12)
ax.set_axis_off(); plt.tight_layout(); plt.savefig(OVER, dpi=140, bbox_inches='tight'); plt.close()

ss = getSampleStyleSheet()
def stl(n, **k): ss.add(ParagraphStyle(n, **k)); return ss[n]
T = stl('T', fontName='Helvetica-Bold', fontSize=19, textColor=VERDE, spaceAfter=3, leading=22)
SUB = stl('SUB', fontName='Helvetica', fontSize=11, textColor=GRIS, spaceAfter=8)
HH = stl('HH', fontName='Helvetica-Bold', fontSize=13, textColor=VERDE, spaceBefore=8, spaceAfter=4)
BB = stl('BB', fontName='Helvetica', fontSize=10, textColor=GRIS, leading=14, spaceAfter=5)
CAP = stl('CAP', fontName='Helvetica', fontSize=8, textColor=VERDE, alignment=1, spaceBefore=2)

def hf(c, doc):
    c.saveState(); c.setFont('Helvetica-Bold', 9); c.setFillColor(VERDE)
    c.drawString(2*cm, A4[1]-1.1*cm, 'PIXADVISOR — Agricultura de Precisión')
    c.setStrokeColor(VERDE); c.setLineWidth(1.1); c.line(2*cm, A4[1]-1.25*cm, A4[0]-2*cm, A4[1]-1.25*cm)
    c.setFont('Helvetica', 7); c.setFillColor(GRIS); c.drawString(2*cm, 1*cm, 'Pixadvisor AP · Informe de área útil · %s' % FECHA)
    c.drawRightString(A4[0]-2*cm, 1*cm, 'Pág. %d' % doc.page); c.restoreState()

def bloque_tbl():
    data = [['Bloque', 'Lotes/div.', 'Área bruta (ha)', 'Cañada/drenaje (ha)', '% cañada', 'ÁREA ÚTIL (ha)']]
    for b in [2, 3, 14]:
        g = m[m.bloque == b]; gr = g.gross_ha.sum(); ca = g.canada_ha.sum()
        data.append([str(b), len(g), '%.1f' % gr, '%.1f' % ca, '%.1f%%' % (ca/gr*100), '%.1f' % g.util_ha.sum()])
    data.append(['TOTAL', len(m), '%.1f' % TOT.gross_ha, '%.1f' % TOT.canada_ha, '%.1f%%' % (TOT.canada_ha/TOT.gross_ha*100), '%.1f' % TOT.util_ha])
    t = Table(data, colWidths=[1.9*cm, 2*cm, 3*cm, 3.4*cm, 2*cm, 3.1*cm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9), ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]), ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), .4, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return t

def intro():
    s = [Spacer(1, 4), Paragraph('Informe de Área Útil de Siembra', T), Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27 · Bloques 2, 3 y 14', SUB),
         Paragraph('Objetivo', HH), Paragraph('Cuantificar el área sembrable de cada lote y sus divisiones (por camino/cañada), descontando los drenajes no cultivables.', BB),
         Paragraph('Metodología', HH), Paragraph('Drenajes = <b>relevados a mano por el técnico</b> + <b>detección satelital multi-fuente</b> (FABDEM + ruteo hidrológico + vegetación riparia Sentinel-2). '
            'Cada lote dividido por camino o cañada se trata como lote independiente (letra A/B/C).', BB),
         Paragraph('Resultado por bloque', HH), bloque_tbl(), Spacer(1, 5),
         Paragraph('<b>Área útil total: %.1f ha</b> de %.1f ha brutas — se descuentan %.1f ha (%.1f%%) de cañadas/drenajes, en <b>%d lotes/divisiones</b>.'
                   % (TOT.util_ha, TOT.gross_ha, TOT.canada_ha, TOT.canada_ha/TOT.gross_ha*100, len(m)), BB)]
    return s

# RESUMEN
S = intro() + [Spacer(1, 8), RLImage(OVER, width=15*cm, height=15*cm*np.array(__import__('PIL').Image.open(OVER).size)[1]/np.array(__import__('PIL').Image.open(OVER).size)[0]),
               Paragraph('Mapa general: área útil por bloque y cañadas/drenajes (azul).', CAP)]
o1 = os.path.join(D, 'Informe_RESUMEN_Area_Util_SerroAlto.pdf')
SimpleDocTemplate(o1, pagesize=A4, topMargin=1.7*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(S, onFirstPage=hf, onLaterPages=hf)
print('Resumen ->', os.path.basename(o1))

# COMPLETO: + tabla por division
S = intro()
S.append(PageBreak()); S.append(Paragraph('Detalle por lote/división', HH))
data = [['Bloque', 'Lote', 'Bruta (ha)', 'Cañada (ha)', 'ÚTIL (ha)', 'Baja', 'Media', 'Alta']]
for _, r in m.iterrows():
    data.append([int(r.bloque), r.lote, '%.1f' % r.gross_ha, '%.1f' % r.canada_ha, '%.1f' % r.util_ha, '%.1f' % r.Baja, '%.1f' % r.Media, '%.1f' % r.Alta])
t = Table(data, colWidths=[1.5*cm, 2.2*cm, 2.1*cm, 2.2*cm, 2.1*cm, 1.7*cm, 1.7*cm, 1.7*cm], repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 8), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRISC]), ('ALIGN', (2, 0), (-1, -1), 'CENTER'), ('ALIGN', (0, 0), (1, -1), 'CENTER'),
    ('GRID', (0, 0), (-1, -1), .3, colors.grey), ('TOPPADDING', (0, 0), (-1, -1), 2.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5)]))
S.append(t)
o2 = os.path.join(D, 'Informe_COMPLETO_Area_Util_SerroAlto.pdf')
SimpleDocTemplate(o2, pagesize=A4, topMargin=1.7*cm, bottomMargin=1.4*cm, leftMargin=1.6*cm, rightMargin=1.6*cm).build(S, onFirstPage=hf, onLaterPages=hf)
print('Completo ->', os.path.basename(o2))
print('DONE')
