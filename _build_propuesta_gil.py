# -*- coding: utf-8 -*-
"""
Propuesta tecnica Pixadvisor (en alianza con Nova Agricola) para el cliente
Gil Jorge Aguilera. Rehace fielmente el contenido del PDF original de Nova
Agricola con branding Pixadvisor, doble logo en el encabezado (Nova izq / Pix der)
y correcciones ortograficas en espanol.
"""
import os, math
from PIL import Image, ImageChops, ImageDraw
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether, CondPageBreak, Image as RLImage)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas

DESK  = r"C:/Users/Usuario/Desktop"
ASSET = os.path.join(DESK, "_assets_propuesta")
os.makedirs(ASSET, exist_ok=True)
OUT   = os.path.join(DESK, "Propuesta_Gil_Jorge_Aguilera_Pixadvisor.pdf")

# ---------------------------------------------------------------- colors (marca)
TEAL=HexColor('#0D9488'); TEAL_D=HexColor('#0F766E')
LIME=HexColor('#7FD633'); BLUE=HexColor('#1E40AF'); DARK=HexColor('#0F172A')
TEXT=HexColor('#1E293B'); MUTED=HexColor('#64748B'); SURFACE=HexColor('#F8FAFC')
BORDER=HexColor('#E2E8F0'); TEAL_TINT=HexColor('#E8F6F4'); BLUE_TINT=HexColor('#EEF2FB')
TEAL_HEX='#0D9488'; BLUE_HEX='#1E40AF'; LIME_HEX='#7FD633'

# ---------------------------------------------------------------- assets
def trim_white(src, dst):
    im = Image.open(src).convert('RGB')
    bg = Image.new('RGB', im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        pad = 2
        bbox = (max(0,bbox[0]-pad), max(0,bbox[1]-pad),
                min(im.size[0],bbox[2]+pad), min(im.size[1],bbox[3]+pad))
        im = im.crop(bbox)
    im.save(dst); return im.size

def trim_alpha(src, dst):
    im = Image.open(src).convert('RGBA')
    bbox = im.split()[3].getbbox()
    if bbox: im = im.crop(bbox)
    im.save(dst); return im.size

def make_check(path, size=72):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([1, 1, size-1, size-1], fill=(127, 214, 51, 255))
    w = max(2, int(size*0.11))
    d.line([(size*0.27, size*0.52), (size*0.43, size*0.68), (size*0.74, size*0.33)],
           fill=(255, 255, 255, 255), width=w, joint='curve')
    im.save(path)

# Extrae el logo de Nova Agrícola directamente del PDF original (autosuficiente)
def extract_nova_logo(src_pdf, dst):
    import fitz
    doc = fitz.open(src_pdf)
    best = None
    for img in doc[0].get_images(full=True):
        base = doc.extract_image(img[0])
        w, h = base['width'], base['height']
        ratio = w/float(h)
        if 1.3 < ratio < 4.0 and w > 80:          # el logo, no la línea fina (ratio ~8)
            if best is None or w > best[1]:
                best = (base['image'], w, h)
    with open(dst, 'wb') as f:
        f.write(best[0])
    return dst

_nova_raw = extract_nova_logo(os.path.join(DESK, 'Propuesta_Gil_Gorje_Aguilera.pdf'),
                              os.path.join(ASSET, 'nova_raw.png'))
nova_sz = trim_white(_nova_raw, os.path.join(ASSET, 'nova.png'))
pix_sz  = trim_alpha(r'D:/PIXADVISOR_AGENT_WORKSPACE/pixadvisor-website/img/logo-pix.png',
                     os.path.join(ASSET, 'pix.png'))
make_check(os.path.join(ASSET, 'check.png'))
NOVA_RATIO = nova_sz[0]/nova_sz[1]
PIX_RATIO  = pix_sz[0]/pix_sz[1]
NOVA = os.path.join(ASSET, 'nova.png')
PIX  = os.path.join(ASSET, 'pix.png')
CHK  = os.path.join(ASSET, 'check.png')

# ---------------------------------------------------------------- geometry
PAGE_W, PAGE_H = letter
LM = RM = 0.85*inch
TM = 1.18*inch
BM = 1.00*inch
CONTENT_W = PAGE_W - LM - RM

# ---------------------------------------------------------------- header/footer
def grad_rect(c, x, y, w, h, colors, positions):
    c.saveState()
    p = c.beginPath(); p.rect(x, y, w, h); c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(x, y, x+w, y, colors, positions, extend=True)
    c.restoreState()

def header_footer(c, doc):
    c.saveState()
    nova_h = 26.0; nova_w = nova_h*NOVA_RATIO
    pix_h  = 34.0; pix_w  = pix_h*PIX_RATIO
    top = PAGE_H - 24
    center = top - pix_h/2.0
    c.drawImage(NOVA, LM, center-nova_h/2.0, width=nova_w, height=nova_h,
                mask='auto', preserveAspectRatio=True)
    c.drawImage(PIX, PAGE_W-RM-pix_w, center-pix_h/2.0, width=pix_w, height=pix_h,
                mask='auto', preserveAspectRatio=True)
    sep_y = top - pix_h - 9
    grad_rect(c, LM, sep_y, CONTENT_W, 2.4, [LIME, TEAL, BLUE], [0, 0.5, 1])
    # footer
    c.setStrokeColor(BORDER); c.setLineWidth(0.6)
    c.line(LM, BM-16, PAGE_W-RM, BM-16)
    c.setFont('Helvetica-Bold', 7.5); c.setFillColor(TEAL)
    c.drawString(LM, BM-28, 'PIXADVISOR  —  Agricultura de Precisión')
    c.setFont('Helvetica', 6.8); c.setFillColor(MUTED)
    c.drawString(LM, BM-37,
                 'En alianza con Nova Agrícola — Comércio de Biodefensivos Ltda · '
                 'Floriano Peixoto 183, Centro, Canoinhas/SC · novaagricola@gmail.com · (47) 3622-1471')
    c.restoreState()

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        canvas.Canvas.__init__(self, *a, **k); self._saved = []
    def showPage(self):
        self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.setFont('Helvetica', 7.5); self.setFillColor(MUTED)
            self.drawRightString(PAGE_W-RM, BM-28, 'Página %d de %d' % (self._pageNumber, n))
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

# ---------------------------------------------------------------- styles
ss = getSampleStyleSheet()
def S(name, **kw):
    kw.setdefault('fontName', 'Helvetica')
    return ParagraphStyle(name, parent=ss['Normal'], **kw)

eyebrow  = S('eyebrow', fontName='Helvetica-Bold', fontSize=9.5, textColor=TEAL,
             spaceAfter=10, leading=12)
ctitle   = S('ctitle', fontName='Helvetica-Bold', fontSize=25, textColor=DARK,
             leading=29, spaceAfter=8)
csub     = S('csub', fontSize=12.5, textColor=MUTED, leading=17, spaceAfter=2)
h1       = S('h1', fontName='Helvetica-Bold', fontSize=15, textColor=TEAL_D,
             spaceBefore=4, spaceAfter=2, leading=18)
h2       = S('h2', fontName='Helvetica-Bold', fontSize=12, textColor=DARK,
             spaceBefore=10, spaceAfter=4, leading=15)
body     = S('body', fontSize=10, textColor=TEXT, leading=14.5, alignment=TA_JUSTIFY,
             spaceAfter=7)
obj_b    = S('obj_b', fontSize=10, textColor=TEXT, leading=14, leftIndent=13,
             firstLineIndent=-11, spaceAfter=4)
org_name = S('org_name', fontSize=11.5, textColor=DARK, leading=14, spaceBefore=8, spaceAfter=2)
note_st  = S('note_st', fontName='Helvetica-Oblique', fontSize=9, textColor=MUTED,
             leftIndent=17, leading=12, spaceAfter=3)
colhdr   = S('colhdr', fontName='Helvetica-Bold', fontSize=8, textColor=white, leading=10.5)
cell_b   = S('cell_b', fontSize=8.7, textColor=TEXT, leading=11.7, leftIndent=11,
             firstLineIndent=-9, spaceAfter=2)
band_eye = S('band_eye', fontName='Helvetica-Bold', fontSize=8, textColor=HexColor('#D5F0AE'),
             leading=10, spaceAfter=1)
band_ttl = S('band_ttl', fontName='Helvetica-Bold', fontSize=14, textColor=white, leading=16.5)
res_txt  = S('res_txt', fontSize=9.5, textColor=TEXT, leading=12.6)
cb_lab   = S('cb_lab', fontName='Helvetica-Bold', fontSize=8, textColor=MUTED, leading=11)
cb_val   = S('cb_val', fontName='Helvetica-Bold', fontSize=11, textColor=DARK, leading=14)
callout  = S('callout', fontName='Helvetica-Oblique', fontSize=10.5, textColor=TEXT,
             leading=15.5, alignment=TA_JUSTIFY)
closing  = S('closing', fontName='Helvetica-Oblique', fontSize=9.5, textColor=MUTED,
             leading=13.5, alignment=TA_LEFT)

# ---------------------------------------------------------------- builders
def section(num, title):
    return [KeepTogether([
        Paragraph('%s.&nbsp;&nbsp;%s' % (num, title), h1),
        HRFlowable(width='100%', thickness=2, color=LIME, lineCap='round',
                   spaceBefore=3, spaceAfter=9),
    ])]

def objectives_box(items):
    paras = [Paragraph('<font color="%s">•</font> %s' % (TEAL_HEX, t), obj_b) for t in items]
    t = Table([[paras]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), SURFACE),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('LINEBEFORE', (0,0), (0,-1), 3, TEAL),
        ('TOPPADDING', (0,0), (-1,-1), 11), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 15), ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    return t

def bioreactor_band(n, title):
    cell = [Paragraph('BIORREACTOR %d' % n, band_eye), Paragraph(title.upper(), band_ttl)]
    t = Table([['', cell]], colWidths=[10, CONTENT_W-10])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), LIME),
        ('BACKGROUND', (1,0), (1,0), TEAL),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 13), ('RIGHTPADDING', (1,0), (1,0), 13),
        ('TOPPADDING', (1,0), (1,0), 8), ('BOTTOMPADDING', (1,0), (1,0), 8),
        ('LEFTPADDING', (0,0), (0,0), 0), ('RIGHTPADDING', (0,0), (0,0), 0),
    ]))
    return t

def benefit_table(dey, sue):
    left  = [Paragraph('<font color="%s">•</font> %s' % (TEAL_HEX, t), cell_b) for t in dey]
    right = [Paragraph('<font color="%s">•</font> %s' % (BLUE_HEX, t), cell_b) for t in sue]
    data = [[Paragraph('EN EL TRATAMIENTO DE LAS DEYECCIONES', colhdr), '',
             Paragraph('BENEFICIO EN EL SUELO AGRÍCOLA', colhdr)],
            [left, '', right]]
    col = (CONTENT_W-10)/2.0
    t = Table(data, colWidths=[col, 10, col])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), TEAL),
        ('BACKGROUND', (2,0), (2,0), BLUE),
        ('BACKGROUND', (0,1), (0,1), TEAL_TINT),
        ('BACKGROUND', (2,1), (2,1), BLUE_TINT),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (0,-1), 9), ('RIGHTPADDING', (0,0), (0,-1), 9),
        ('LEFTPADDING', (2,0), (2,-1), 9), ('RIGHTPADDING', (2,0), (2,-1), 9),
        ('LEFTPADDING', (1,0), (1,-1), 0), ('RIGHTPADDING', (1,0), (1,-1), 0),
        ('TOPPADDING', (0,0), (-1,0), 5), ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,1), (-1,1), 7), ('BOTTOMPADDING', (0,1), (-1,1), 7),
    ]))
    return t

def organism_parts(o):
    parts = [Paragraph('<font color="%s" size="14">•</font> <b><i>%s</i></b>' % (LIME_HEX, o['name']),
                       org_name)]
    if o.get('note'):
        parts.append(Paragraph(o['note'], note_st))
    parts.append(Spacer(1, 2))
    parts.append(benefit_table(o['dey'], o['sue']))
    parts.append(Spacer(1, 9))
    return parts

def resultados_block(items):
    half = math.ceil(len(items)/2.0)
    c1, c2 = items[:half], items[half:]
    rows = []
    for i in range(half):
        r = []
        for col in (c1, c2):
            if i < len(col):
                r += [RLImage(CHK, 12, 12), Paragraph(col[i], res_txt)]
            else:
                r += ['', '']
        rows.append(r)
    cw = (CONTENT_W - 18 - 18 - 16)/2.0
    inner = Table(rows, colWidths=[18, cw, 18, cw])
    inner.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (1,0), (1,-1), 5), ('LEFTPADDING', (3,0), (3,-1), 5),
        ('RIGHTPADDING', (1,0), (1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    box = Table([[inner]], colWidths=[CONTENT_W])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), SURFACE),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('LINEBEFORE', (0,0), (0,-1), 3, LIME),
        ('TOPPADDING', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 14), ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return box

def conclusion_callout(text):
    p = Paragraph(text, callout)
    t = Table([['', p]], colWidths=[6, CONTENT_W-6])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), TEAL),
        ('BACKGROUND', (1,0), (1,0), TEAL_TINT),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (1,0), (1,0), 15), ('RIGHTPADDING', (1,0), (1,0), 15),
        ('TOPPADDING', (1,0), (1,0), 13), ('BOTTOMPADDING', (1,0), (1,0), 13),
        ('LEFTPADDING', (0,0), (0,0), 0), ('RIGHTPADDING', (0,0), (0,0), 0),
    ]))
    return t

def client_box(rows):
    data = [[Paragraph(l, cb_lab), Paragraph(v, cb_val)] for l, v in rows]
    inner = Table(data, colWidths=[135, CONTENT_W-6-135])
    st = [('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
          ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
          ('LEFTPADDING', (0,0), (-1,-1), 14), ('RIGHTPADDING', (0,0), (-1,-1), 12)]
    for i in range(len(data)):
        st.append(('BACKGROUND', (0,i), (-1,i), SURFACE if i % 2 == 0 else white))
        if i:
            st.append(('LINEABOVE', (0,i), (-1,i), 0.6, BORDER))
    inner.setStyle(TableStyle(st))
    box = Table([['', inner]], colWidths=[6, CONTENT_W-6])
    box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), TEAL),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.8, BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    return box

# ---------------------------------------------------------------- content data
OBJETIVOS = [
    'Reducir la carga orgánica de las deyecciones.',
    'Disminuir olores y emisiones gaseosas indeseadas.',
    'Acelerar la degradación de la materia orgánica.',
    'Solubilizar nutrientes.',
    'Promover procesos biológicos de nitrificación.',
    'Producir metabolitos beneficiosos para el suelo.',
    'Generar un fertilizante biológico de alto valor agronómico.',
    'Transformar un pasivo ambiental en un activo agrícola sostenible.',
]

BIORREACTORES = [
 {'n':1, 'title':'Consorcio Bacillus', 'organisms':[
   {'name':'Bacillus subtilis',
    'note':'Considerada una de las bacterias más eficientes para la degradación biológica.',
    'dey':['Producción de enzimas proteasas, amilasas y celulasas.',
           'Acelera la descomposición de la materia orgánica.',
           'Reduce la formación de compuestos responsables de malos olores.',
           'Mejora la estabilidad biológica del sistema.'],
    'sue':['Solubilización de fósforo.','Producción de fitohormonas.',
           'Estimulación del crecimiento radicular.','Supresión de patógenos del suelo.']},
   {'name':'Bacillus amyloliquefaciens',
    'dey':['Elevada producción de enzimas degradadoras.',
           'Acelera la mineralización de residuos orgánicos.',
           'Reduce la acumulación de sólidos.'],
    'sue':['Producción de lipopéptidos antimicrobianos.','Promoción del crecimiento vegetal.',
           'Incremento de la disponibilidad de nutrientes.']},
   {'name':'Bacillus megaterium',
    'dey':['Solubilización del fósforo presente en los residuos.',
           'Conversión de nutrientes insolubles en formas disponibles para las plantas.'],
    'sue':['Excelente solubilizador de fósforo.','Incrementa la eficiencia nutricional.',
           'Favorece el desarrollo radicular.']},
   {'name':'Bacillus licheniformis',
    'dey':['Producción intensiva de proteasas.','Degradación de proteínas complejas.',
           'Reducción de la sedimentación.'],
    'sue':['Incrementa el reciclaje de nutrientes.','Mejora la actividad biológica del suelo.']},
   {'name':'Bacillus aryabhattai',
    'dey':['Participa en la degradación de compuestos orgánicos complejos.',
           'Contribuye a la estabilización microbiológica.'],
    'sue':['Solubiliza fósforo y potasio.','Produce sustancias promotoras del crecimiento vegetal.']},
   {'name':'Bacillus pumilus',
    'dey':['Alta actividad enzimática.','Reduce la carga orgánica.'],
    'sue':['Produce hormonas vegetales.','Mejora la tolerancia al estrés hídrico.']},
   {'name':'Bacillus velezensis',
    'dey':['Producción de compuestos antimicrobianos naturales.',
           'Contribuye al control microbiológico del sistema.'],
    'sue':['Control biológico de enfermedades.','Mayor vigor vegetativo.']},
 ]},
 {'n':2, 'title':'Pseudomonas + Azospirillum', 'organisms':[
   {'name':'Pseudomonas putida',
    'dey':['Degrada compuestos orgánicos complejos.',
           'Favorece la depuración biológica del sistema.'],
    'sue':['Solubilización de fósforo.','Producción de sideróforos.',
           'Mejora de la absorción de nutrientes.']},
   {'name':'Pseudomonas fluorescens',
    'dey':['Compite contra microorganismos indeseables.',
           'Favorece la estabilidad microbiológica.'],
    'sue':['Control biológico de enfermedades.',
           'Inducción de resistencia sistémica en las plantas.']},
   {'name':'Azospirillum brasilense',
    'dey':['Participa en el reciclaje biológico del nitrógeno.'],
    'sue':['Fijación biológica de nitrógeno.','Producción de auxinas.',
           'Mayor desarrollo radicular.','Mejor eficiencia en el uso del agua.']},
 ]},
 {'n':3, 'title':'Hongos del Suelo y Controladores de Nematodos', 'organisms':[
   {'name':'Pochonia chlamydosporia',
    'dey':['Contribuye al equilibrio microbiológico del sistema.'],
    'sue':['Control biológico de nematodos.','Colonización benéfica de raíces.']},
   {'name':'Purpureocillium lilacinum',
    'dey':['Participa en la descomposición de la materia orgánica.'],
    'sue':['Control de huevos y juveniles de nematodos.',
           'Reducción de poblaciones de fitonematodos.']},
   {'name':'Trichoderma harzianum',
    'dey':['Producción intensa de enzimas degradadoras.',
           'Acelera la humificación de la materia orgánica.'],
    'sue':['Control biológico de enfermedades.','Estimulación del crecimiento radicular.',
           'Solubilización de nutrientes.']},
   {'name':'Trichoderma asperellum',
    'dey':['Acelera el compostaje y la estabilización biológica.'],
    'sue':['Producción de metabolitos bioestimulantes.','Incremento de la eficiencia nutricional.']},
 ]},
 {'n':4, 'title':'Hongos Entomopatógenos', 'organisms':[
   {'name':'Clonostachys rosea',
    'dey':['Favorece el equilibrio microbiológico.'],
    'sue':['Control biológico de hongos fitopatógenos.','Colonización beneficiosa del suelo.']},
   {'name':'Beauveria bassiana',
    'dey':['Participa en la degradación de materia orgánica.'],
    'sue':['Control biológico de insectos plaga.','Colonización endofítica de las plantas.']},
   {'name':'Metarhizium anisopliae',
    'dey':['Incrementa la biodiversidad microbiológica.'],
    'sue':['Control biológico de insectos del suelo.','Promoción del crecimiento vegetal.']},
 ]},
 {'n':5, 'title':'Levaduras y Bioconversión', 'organisms':[
   {'name':'Saccharomyces cerevisiae',
    'dey':['Fermentación de azúcares y compuestos orgánicos.',
           'Producción de vitaminas y metabolitos beneficiosos.'],
    'sue':['Estimulación de la microbiología del suelo.',
           'Producción de aminoácidos y vitaminas.']},
   {'name':'Saccharomyces spp.',
    'dey':['Aceleración de procesos fermentativos.',
           'Reducción de compuestos fácilmente fermentables.'],
    'sue':['Mejora de la actividad microbiana.']},
   {'name':'Yarrowia lipolytica',
    'dey':['Degradación eficiente de grasas y lípidos.',
           'Alta eficiencia en residuos provenientes de porcicultura.'],
    'sue':['Producción de biosurfactantes.','Incremento de la disponibilidad de nutrientes.']},
 ]},
 {'n':6, 'title':'Microorganismos Fotosintéticos y Ciclo del Nitrógeno', 'organisms':[
   {'name':'Rhodopseudomonas palustris',
    'dey':['Reducción de olores.','Consumo de compuestos potencialmente tóxicos.',
           'Producción de sustancias bioactivas.'],
    'sue':['Producción de aminoácidos.','Bioestimulación vegetal.',
           'Incremento de la actividad microbiológica.']},
   {'name':'Lactobacillus plantarum',
    'dey':['Fermentación láctica.','Reducción de microorganismos patógenos.','Control de olores.'],
    'sue':['Estabilización de la microbiota benéfica.',
           'Producción de metabolitos favorables al desarrollo vegetal.']},
   {'name':'Lactobacillus acidophilus',
    'dey':['Acidificación controlada del medio.','Reducción de microorganismos indeseables.'],
    'sue':['Favorece el establecimiento de microorganismos beneficiosos.']},
   {'name':'Nitrosomonas europaea',
    'dey':['Conversión de amoníaco en nitrito.','Reducción de la toxicidad del nitrógeno.'],
    'sue':['Mejora la eficiencia del ciclo del nitrógeno.']},
   {'name':'Nitrospira moscoviensis',
    'dey':['Conversión de nitrito en nitrato.','Completa el proceso biológico de nitrificación.'],
    'sue':['Disponibiliza nitrógeno en formas fácilmente absorbidas por las plantas.',
           'Incrementa la eficiencia fertilizante.']},
 ]},
]

RESULTADOS = [
    'Reducción significativa de olores.',
    'Disminución de la carga orgánica de las deyecciones.',
    'Conversión acelerada de la materia orgánica en compuestos estables.',
    'Solubilización de fósforo y potasio.',
    'Conversión biológica del nitrógeno en formas asimilables.',
    'Producción de metabolitos bioactivos.',
    'Incremento de la biodiversidad microbiológica.',
    'Producción de biofertilizante líquido de alto valor agronómico.',
    'Reducción de la dependencia de fertilizantes químicos.',
    'Transformación definitiva del pasivo ambiental en un activo agrícola sostenible.',
]

INTRO = ('La porcicultura moderna genera grandes volúmenes de deyecciones ricas en materia '
         'orgánica, nitrógeno, fósforo, potasio y micronutrientes. Sin embargo, cuando estos '
         'residuos no son gestionados adecuadamente, pueden representar riesgos ambientales, '
         'generación de olores desagradables, pérdidas de nutrientes y elevados costos operativos.')

OBJ_LEAD = ('La presente propuesta tiene como objetivo implementar un sistema de biotecnología '
            'On-Farm basado en la multiplicación controlada de hongos, bacterias, levaduras y '
            'microorganismos fotosintéticos en seis biorreactores independientes, con el propósito de:')

BR_LEAD = ('El sistema se compone de seis biorreactores independientes, cada uno especializado en '
           'un consorcio microbiano con funciones complementarias para el tratamiento de las '
           'deyecciones y el enriquecimiento del suelo agrícola.')

CONCL = ('El proyecto propone la implementación de una Biofábrica On-Farm capaz de agregar valor a '
         'las deyecciones porcinas mediante la acción coordinada de bacterias, hongos, levaduras y '
         'microorganismos fotosintéticos. El resultado será un sistema circular de producción, donde '
         'los residuos dejan de representar un problema ambiental para convertirse en una fuente '
         'estratégica de fertilidad, productividad y sostenibilidad para la actividad agrícola.')

# ---------------------------------------------------------------- story
story = []
# COVER
story.append(Spacer(1, 58))
story.append(Paragraph('PROPUESTA TÉCNICA &nbsp;·&nbsp; BIOTECNOLOGÍA ON-FARM', eyebrow))
story.append(Paragraph('Transformación de Deyecciones Porcinas en un Activo Agrícola', ctitle))
story.append(Paragraph('Producción On-Farm de microorganismos &nbsp;·&nbsp; Biofábrica de '
                       'biofertilizantes de alto valor agronómico', csub))
story.append(HRFlowable(width=130, thickness=3, color=LIME, lineCap='round',
                        spaceBefore=12, spaceAfter=22, hAlign='LEFT'))
story.append(client_box([
    ('CLIENTE', 'Gil Jorge Aguilera'),
    ('PRESENTADO POR', 'Pixadvisor — Agricultura de Precisión'),
    ('EN ALIANZA CON', 'Nova Agrícola — Comércio de Biodefensivos Ltda'),
    ('FECHA', '31 de mayo de 2026'),
]))
story.append(Spacer(1, 20))
story.append(Paragraph('Documento técnico preparado por Pixadvisor — Agricultura de Precisión, en '
                       'alianza con Nova Agrícola, para la evaluación e implementación del proyecto '
                       'de biofábrica On-Farm de microorganismos.', closing))
story.append(PageBreak())

# 1. PRESENTACIÓN
story += section('1', 'Presentación')
story.append(Paragraph(INTRO, body))
story.append(Paragraph('Objetivos del Proyecto', h2))
story.append(Paragraph(OBJ_LEAD, body))
story.append(objectives_box(OBJETIVOS))
story.append(Spacer(1, 6))

# 2. BIORREACTORES
story += section('2', 'Los Seis Biorreactores')
story.append(Paragraph(BR_LEAD, body))
story.append(Spacer(1, 2))
for br in BIORREACTORES:
    story.append(Spacer(1, 6))
    orgs = br['organisms']
    # la banda nunca queda huérfana: viaja junto a su primer organismo
    story.append(KeepTogether([bioreactor_band(br['n'], br['title']), Spacer(1, 9)]
                              + organism_parts(orgs[0])))
    for o in orgs[1:]:
        story.append(KeepTogether(organism_parts(o)))

# 3. RESULTADOS
story.append(CondPageBreak(120))
story += section('3', 'Resultados Esperados')
story.append(Paragraph('La utilización integrada de los seis biorreactores permitirá:', body))
story.append(resultados_block(RESULTADOS))
story.append(Spacer(1, 8))

# 4. CONCLUSIÓN
story.append(CondPageBreak(110))
story += section('4', 'Conclusión')
story.append(conclusion_callout(CONCL))

doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=LM, rightMargin=RM,
                        topMargin=TM, bottomMargin=BM,
                        title='Propuesta — Transformación de Deyecciones Porcinas en un Activo Agrícola',
                        author='Pixadvisor — Agricultura de Precisión',
                        subject='Biofábrica On-Farm de microorganismos · Cliente: Gil Jorge Aguilera')
doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer, canvasmaker=NumberedCanvas)
print('OK ->', OUT, '|', os.path.getsize(OUT), 'bytes')
