# -*- coding: utf-8 -*-
"""Genera 2 PDFs Pixadvisor: (1) Resumen area util por bloque, (2) Completo con
PNG por lote. Branding Pixadvisor."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd, geopandas as gpd
from shapely.ops import unary_union
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import matplotlib.patches as mp
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Image as RLImage)
import warnings; warnings.filterwarnings('ignore')

DIRBASE = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
OUTDIR = os.path.join(DIRBASE, '_analisis_canadas'); PNGDIR = os.path.join(OUTDIR, 'lotes_png')
FECHA = '24/06/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333')
GRISC = HexColor('#F5F5F5'); ROJO = HexColor('#C0392B')

df = pd.read_csv(os.path.join(DIRBASE, 'AREA_UTIL_por_lote.csv'))
df['bloque'] = df['bloque'].astype(float).astype(int)
df['lote'] = df['lote_id'].str.replace(r'Bloque-\d+-', '', regex=True)
bl = df.groupby('bloque').agg(lotes=('lote_id', 'nunique'), gross=('gross_ha', 'sum'),
                              canada=('dren_ha', 'sum'), util=('util_ha', 'sum')).reset_index()
bl['pct'] = bl['canada'] / bl['gross'] * 100
TOT = dict(gross=df['gross_ha'].sum(), canada=df['dren_ha'].sum(), util=df['util_ha'].sum(), lotes=len(df))

# ---------- mapa overview consolidado ----------
OVER = os.path.join(OUTDIR, 'overview_consolidado.png')
glob = gpd.read_file(os.path.join(DIRBASE, 'AREA_UTIL_GLOBAL_SerroAlto.geojson')).to_crs(31981)
can = gpd.read_file(os.path.join(DIRBASE, 'DRENAJES_FINAL_SerroAlto.geojson')).to_crs(31981)
fig, ax = plt.subplots(figsize=(9, 9))
cmap = {'2': '#66bd63', '3': '#1a9850', '14': '#a6d96a'}
for b, s in glob.groupby('bloque'):
    s.plot(ax=ax, color=cmap.get(str(b), '#a6d96a'), edgecolor='#333', linewidth=0.4)
can.plot(ax=ax, color='#C0392B', alpha=0.85, edgecolor='none')
ax.set_title('Serro Alto — Area util (verde) y cañadas/drenajes (rojo)', fontsize=12)
ax.legend(handles=[mp.Patch(color='#66bd63', label='Bloque 2'), mp.Patch(color='#1a9850', label='Bloque 3'),
                   mp.Patch(color='#a6d96a', label='Bloque 14'), mp.Patch(color='#C0392B', label='Cañada/drenaje')],
          loc='upper right', fontsize=9)
ax.set_axis_off(); plt.tight_layout(); plt.savefig(OVER, dpi=140, bbox_inches='tight'); plt.close()

# ---------- estilos ----------
ss = getSampleStyleSheet()
ss.add(ParagraphStyle('PixT', parent=ss['Title'], fontSize=19, textColor=VERDE, spaceAfter=4, leading=22))
ss.add(ParagraphStyle('PixSub', parent=ss['Normal'], fontSize=11, textColor=GRIS, spaceAfter=10))
ss.add(ParagraphStyle('PixH', parent=ss['Heading2'], fontSize=13, textColor=VERDE, spaceBefore=10, spaceAfter=5))
ss.add(ParagraphStyle('PixBody', parent=ss['Normal'], fontSize=10, textColor=GRIS, leading=14, spaceAfter=5))
ss.add(ParagraphStyle('PixSmall', parent=ss['Normal'], fontSize=8, textColor=GRIS))
ss.add(ParagraphStyle('PixCap', parent=ss['Normal'], fontSize=8.5, textColor=VERDE, alignment=1, spaceBefore=3))

def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 9); canvas.setFillColor(VERDE)
    canvas.drawString(2*cm, A4[1]-1.2*cm, 'PIXADVISOR — Agricultura de Precisión')
    canvas.setStrokeColor(VERDE); canvas.setLineWidth(1.2); canvas.line(2*cm, A4[1]-1.35*cm, A4[0]-2*cm, A4[1]-1.35*cm)
    canvas.setFont('Helvetica', 7); canvas.setFillColor(GRIS)
    canvas.drawString(2*cm, 1*cm, 'Pixadvisor AP · Informe técnico · %s' % FECHA)
    canvas.drawRightString(A4[0]-2*cm, 1*cm, 'Página %d' % doc.page)
    canvas.restoreState()

def tbl_bloque():
    data = [['Bloque', 'Lotes', 'Área bruta (ha)', 'Cañada/drenaje (ha)', '% cañada', 'ÁREA ÚTIL (ha)']]
    for _, r in bl.sort_values('bloque').iterrows():
        data.append([str(r['bloque']), int(r['lotes']), '%.1f' % r['gross'], '%.1f' % r['canada'], '%.1f%%' % r['pct'], '%.1f' % r['util']])
    data.append(['TOTAL', TOT['lotes'], '%.1f' % TOT['gross'], '%.1f' % TOT['canada'], '%.1f%%' % (TOT['canada']/TOT['gross']*100), '%.1f' % TOT['util']])
    t = Table(data, colWidths=[2*cm, 1.6*cm, 3*cm, 3.4*cm, 2*cm, 3.2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    return t

def intro_story():
    s = []
    s.append(Paragraph('Informe de Área Útil de Siembra', ss['PixT']))
    s.append(Paragraph('Hacienda Serro Alto · Campaña Soya 2026/27 · Bloques 2, 3 y 14', ss['PixSub']))
    s.append(Paragraph('Objetivo', ss['PixH']))
    s.append(Paragraph('Cuantificar el área efectivamente sembrable de cada lote descontando los canales y '
        'cañadas de drenaje no cultivables, para planificar la campaña de soya 2026/27.', ss['PixBody']))
    s.append(Paragraph('Metodología (drenajes de campo + corroboración satelital)', ss['PixH']))
    s.append(Paragraph('El drenaje no cultivable de cada lote es la <b>unión de dos fuentes</b>: '
        '<b>(1) Drenajes digitalizados a mano</b> por el técnico sobre imagen de alta resolución '
        '(verdad de campo, 30,4 ha en 41 trazos). '
        '<b>(2) Detección satelital multi-fuente</b> como respaldo: modelo de elevación FABDEM con ruteo '
        'hidrológico (acumulación de flujo, validado contra MERIT Hydro 121 vs 106 km²) + vegetación riparia '
        'Sentinel-2. La capa final descuenta <b>ambas</b> para no omitir ningún drenaje.', ss['PixBody']))
    s.append(Paragraph('<b>Nota:</b> los drenajes dibujados a mano son la referencia principal (verdad de campo); '
        'la detección satelital agrega corredores que el trazo manual pudiera no cubrir. '
        'Para el borde exacto a escala centimétrica, un vuelo de dron afina la delimitación.', ss['PixBody']))
    return s

# ---------- PDF 1: RESUMEN ----------
def build_resumen():
    out = os.path.join(DIRBASE, 'Informe_RESUMEN_Area_Util_SerroAlto_FINAL.pdf')
    doc = SimpleDocTemplate(out, pagesize=A4, topMargin=1.8*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    s = intro_story()
    s.append(Paragraph('Resultado por bloque', ss['PixH']))
    s.append(tbl_bloque())
    s.append(Spacer(1, 6))
    s.append(Paragraph('<b>Área útil total: %.1f ha</b> de %.1f ha brutas — se descuentan %.1f ha (%.1f%%) de cañadas/drenajes.'
        % (TOT['util'], TOT['gross'], TOT['canada'], TOT['canada']/TOT['gross']*100), ss['PixBody']))
    s.append(Spacer(1, 8))
    img = RLImage(OVER); img._restrictSize(16*cm, 16*cm); s.append(img)
    s.append(Paragraph('Mapa general: área útil (verde) y cañadas/drenajes (rojo).', ss['PixCap']))
    doc.build(s, onFirstPage=header_footer, onLaterPages=header_footer)
    print('PDF resumen ->', os.path.basename(out), '%.0f KB' % (os.path.getsize(out)/1024))

# ---------- PDF 2: COMPLETO ----------
def build_completo():
    out = os.path.join(DIRBASE, 'Informe_COMPLETO_Area_Util_SerroAlto_FINAL.pdf')
    doc = SimpleDocTemplate(out, pagesize=A4, topMargin=1.8*cm, bottomMargin=1.5*cm, leftMargin=2*cm, rightMargin=2*cm)
    s = intro_story()
    s.append(Paragraph('Resultado por bloque', ss['PixH'])); s.append(tbl_bloque())
    s.append(Spacer(1, 8)); img = RLImage(OVER); img._restrictSize(16*cm, 15*cm); s.append(img)
    s.append(Paragraph('Mapa general: área útil (verde) y cañadas/drenajes (rojo).', ss['PixCap']))
    # detalle por lote (2 por pagina)
    for bq in sorted(bl['bloque'], key=lambda x: int(x)):
        sub = df[df['bloque'] == bq].sort_values('lote')
        s.append(PageBreak()); s.append(Paragraph('Bloque %s — detalle por lote' % bq, ss['PixH']))
        c = 0
        for _, r in sub.iterrows():
            png = os.path.join(PNGDIR, '%s.png' % r['lote_id'])
            if os.path.exists(png):
                im = RLImage(png); im._restrictSize(11*cm, 9.5*cm); s.append(im)
            s.append(Paragraph('<b>%s</b> — Bruta %.1f ha · Cañada/drenaje %.1f ha (%.1f%%) · <b>ÚTIL %.1f ha</b>'
                % (r['lote_id'], r['gross_ha'], r['dren_ha'], r['dren_pct'], r['util_ha']), ss['PixCap']))
            s.append(Spacer(1, 4)); c += 1
            if c % 2 == 0: s.append(PageBreak())
    doc.build(s, onFirstPage=header_footer, onLaterPages=header_footer)
    print('PDF completo ->', os.path.basename(out), '%.0f KB' % (os.path.getsize(out)/1024))

build_resumen()
build_completo()
print('DONE')
