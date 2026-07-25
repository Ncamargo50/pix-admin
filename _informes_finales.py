# -*- coding: utf-8 -*-
"""Regenera Informe al Cliente (Plan de Muestreo) + Protocolo de Campo con la
nomenclatura FINAL (66 divisiones, P1/P2/P3). Una página por división."""
import os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
import warnings; warnings.filterwarnings('ignore')

D = r'C:\Users\Usuario\Desktop\Clientes\SerroAlto\Lotes para muestreo de suelo campaña soya 26-27'
PNG = lambda b, l: os.path.join(D, '_analisis_canadas', 'B%d_muestreo_png' % b, '%s.png' % l)
CLIENTE = 'João Geraldo'; FECHA = '26/06/2026'
VERDE = HexColor('#1B5E20'); VERDE2 = HexColor('#4CAF50'); GRIS = HexColor('#333333'); GRISC = HexColor('#F5F5F5')
ROJO = HexColor('#F44336'); AMA = HexColor('#FBC02D'); VER = HexColor('#4CAF50'); CLCOL = {'Baja': ROJO, 'Media': AMA, 'Alta': VER}

m = pd.read_csv(os.path.join(D, 'MAESTRO_lotes_FINAL.csv'))
TOT = dict(lotes=len(m), util=m.util_ha.sum(), prin=int(m.n_prin.sum()), sub=int(m.n_sub.sum()))

ss = getSampleStyleSheet()
def stl(n, **k): ss.add(ParagraphStyle(n, **k)); return ss[n]
T = stl('T', fontName='Helvetica-Bold', fontSize=20, textColor=VERDE, spaceAfter=3, leading=23)
SUB = stl('SUB', fontName='Helvetica', fontSize=11.5, textColor=GRIS, spaceAfter=3)
CLI = stl('CLI', fontName='Helvetica-Bold', fontSize=13, textColor=VERDE, spaceAfter=9)
HH = stl('HH', fontName='Helvetica-Bold', fontSize=13, textColor=VERDE, spaceBefore=8, spaceAfter=4)
BB = stl('BB', fontName='Helvetica', fontSize=10, textColor=GRIS, leading=14, spaceAfter=4)
LH = stl('LH', fontName='Helvetica-Bold', fontSize=12.5, textColor=VERDE, spaceAfter=3)
CAP = stl('CAP', fontName='Helvetica', fontSize=8, textColor=GRIS, alignment=1, spaceBefore=2)

def hf(tipo):
    def f(c, doc):
        c.saveState(); c.setFont('Helvetica-Bold', 9); c.setFillColor(VERDE)
        c.drawString(2*cm, A4[1]-1.1*cm, 'PIXADVISOR — Agricultura de Precisión')
        c.setStrokeColor(VERDE); c.setLineWidth(1.1); c.line(2*cm, A4[1]-1.25*cm, A4[0]-2*cm, A4[1]-1.25*cm)
        c.setFont('Helvetica', 7); c.setFillColor(GRIS)
        c.drawString(2*cm, 1*cm, 'Pixadvisor AP · %s · Cliente: %s · %s' % (tipo, CLIENTE, FECHA))
        c.drawRightString(A4[0]-2*cm, 1*cm, 'Pág. %d' % doc.page); c.restoreState()
    return f

def tbl_bloque(cols, mode):
    data = [cols]
    for b in [2, 3, 14]:
        g = m[m.bloque == b]
        if mode == 'cli': data.append([str(b), len(g), len(g)*3, int(g.n_prin.sum()), '%.1f' % g.util_ha.sum()])
        else: data.append([str(b), len(g), int(g.n_prin.sum()), int(g.n_sub.sum()), '%.1f' % g.util_ha.sum()])
    if mode == 'cli': data.append(['TOTAL', TOT['lotes'], TOT['lotes']*3, TOT['prin'], '%.1f' % TOT['util']])
    else: data.append(['TOTAL', TOT['lotes'], TOT['prin'], TOT['sub'], '%.1f' % TOT['util']])
    t = Table(data, colWidths=[2.2*cm, 2.2*cm, 3.8*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5), ('BACKGROUND', (0, -1), (-1, -1), VERDE2), ('TEXTCOLOR', (0, -1), (-1, -1), colors.white), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, GRISC]), ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('GRID', (0, 0), (-1, -1), .4, colors.grey),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    return t

def lote_pages(mode):
    out = []
    for _, r in m.iterrows():
        out.append(PageBreak()); el = [Paragraph('Bloque %d — Lote %s' % (r['bloque'], r['lote']), LH)]
        p = PNG(int(r['bloque']), r['lote'])
        if os.path.exists(p):
            im = RLImage(p); im._restrictSize(17*cm, 9.5*cm); el.append(im)
            el.append(Paragraph('Ambientes de manejo y puntos de muestreo sobre imagen satelital.', CAP))
        if mode == 'cli':
            d = [['Ambiente', 'Área (ha)', '% del lote', 'Muestras compuestas']]
            for cl in ['Baja', 'Media', 'Alta']:
                a = r[cl]; d.append([cl, '%.1f' % a, '%.0f%%' % (a/r['util_ha']*100 if r['util_ha'] else 0), '1'])
            d.append(['TOTAL', '%.1f' % r['util_ha'], '100%', str(int(r['n_prin']))])
            cw = [3.2*cm, 3*cm, 3*cm, 4.5*cm]
        else:
            d = [['Ambiente', 'Área (ha)', 'Principal', 'Submuestras', 'Nomenclatura']]
            for zz, cl in [(1, 'Baja'), (2, 'Media'), (3, 'Alta')]:
                a = r[cl]; pid = 'L%s-B%d-P%d' % (r['lote'][1:], r['bloque'], zz) if False else '%s-B%d-P%d' % (r['lote'], r['bloque'], zz)
                d.append([cl, '%.1f' % a, 'P%d' % zz, str(int(round(r['n_sub']/3))), pid])
            d.append(['TOTAL', '%.1f' % r['util_ha'], str(int(r['n_prin'])), str(int(r['n_sub'])), '%d compuestas' % int(r['n_prin'])])
            cw = [2.6*cm, 2.2*cm, 2*cm, 2.6*cm, 5.6*cm]
        tt = Table(d, colWidths=cw)
        styc = [('BACKGROUND', (0, 0), (-1, 0), VERDE), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9), ('GRID', (0, 0), (-1, -1), .4, colors.grey), ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, -1), (-1, -1), GRISC), ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), ('TOPPADDING', (0, 0), (-1, -1), 3.5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5)]
        for i, cl in enumerate(['Baja', 'Media', 'Alta'], 1):
            styc += [('TEXTCOLOR', (0, i), (0, i), CLCOL[cl]), ('FONTNAME', (0, i), (0, i), 'Helvetica-Bold')]
        tt.setStyle(TableStyle(styc)); el += [Spacer(1, 5), tt]
        out.append(KeepTogether(el))
    return out

# ---- Informe Cliente ----
S = [Spacer(1, 4), Paragraph('Plan de Muestreo de Suelo por Ambientes', T), Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27', SUB), Paragraph('Cliente: %s' % CLIENTE, CLI),
     Paragraph('¿Qué vamos a hacer?', HH)]
for t in ['<b>1. Área útil real.</b> Delimitamos la superficie sembrable de cada lote (y sus divisiones por camino/cañada), descontando drenajes no cultivables.',
          '<b>2. Ambientes productivos.</b> Cada lote/división se divide en 3 ambientes (Alta/Media/Baja) con 3 años de satélite + relieve y drenaje.',
          '<b>3. Muestreo dirigido.</b> Una muestra compuesta por ambiente (P1=Baja, P2=Media, P3=Alta), con submuestras distribuidas por toda la zona.',
          '<b>4. Resultado.</b> Recomendaciones de fertilización sitio-específicas por ambiente, optimizando insumos.']:
    S.append(Paragraph(t, BB))
S += [Paragraph('Alcance del plan', HH), tbl_bloque(['Bloque', 'Lotes/divisiones', 'Ambientes', 'Muestras a analizar', 'Área útil (ha)'], 'cli'), Spacer(1, 5),
      Paragraph('Se analizarán <b>%d muestras compuestas</b> (una por ambiente) sobre <b>%.0f ha útiles</b> en <b>%d lotes/divisiones</b> (%d sub-tomas en total). Cada lote dividido por camino o cañada se trata de forma independiente.' % (TOT['prin'], TOT['util'], TOT['lotes'], TOT['sub']), BB)]
S += lote_pages('cli')
o1 = os.path.join(D, 'Informe_Cliente_JoaoGeraldo_Plan_Muestreo_SerroAlto.pdf')
SimpleDocTemplate(o1, pagesize=A4, topMargin=1.7*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(S, onFirstPage=hf('Plan de muestreo'), onLaterPages=hf('Plan de muestreo'))
print('Informe Cliente ->', os.path.basename(o1), '%.0f pág' % (len(m)+1))

# ---- Protocolo ----
S = [Spacer(1, 4), Paragraph('Protocolo de Muestreo de Suelo de Campo', T), Paragraph('Hacienda Cerro Alto · Campaña Soya 2026/27', SUB), Paragraph('Cliente: %s' % CLIENTE, CLI),
     Paragraph('Resumen', HH), tbl_bloque(['Bloque', 'Lotes/div.', 'Muestras princ.', 'Submuestras', 'Área útil (ha)'], 'prot'), Spacer(1, 6),
     Paragraph('Instrucciones de colecta (muestra compuesta por ambiente)', HH)]
for t in ['<b>1. Profundidad:</b> 0–20 cm. Misma profundidad en todas las submuestras.',
          '<b>2. Recorrido:</b> en cada ambiente ir al punto <b>principal</b> (P1=Baja, P2=Media, P3=Alta, centrado) y recolectar las submuestras distribuidas por toda la zona. Todos los puntos a ≥20 m del borde.',
          '<b>3. Composite:</b> mezclar las submuestras de un mismo principal, homogeneizar y extraer ~500 g → 1 bolsa = 1 ambiente.',
          '<b>4. Rótulo:</b> ID del principal, ej. <b>L13B-B14-P1</b> (Baja). Submuestras: <b>L13B-B14-P1-01</b>, -02…',
          '<b>5. Evitar:</b> bordes, cabeceras, caminos, cañadas/drenajes, manchas anómalas.',
          '<b>6. Registro:</b> marcar cada punto como colectado en el APK PIX-Muestreo.']:
    S.append(Paragraph(t, BB))
S += lote_pages('prot')
o2 = os.path.join(D, 'Protocolo_Muestreo_Campo_SerroAlto.pdf')
SimpleDocTemplate(o2, pagesize=A4, topMargin=1.7*cm, bottomMargin=1.4*cm, leftMargin=2*cm, rightMargin=2*cm).build(S, onFirstPage=hf('Protocolo de muestreo'), onLaterPages=hf('Protocolo de muestreo'))
print('Protocolo ->', os.path.basename(o2), '%.0f pág' % (len(m)+1))
print('DONE')
