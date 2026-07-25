# -*- coding: utf-8 -*-
"""
Estudio de inversion para el cliente Gil Jorge Aguilera (biofabrica OnFarm).
Genera DOS PDFs con branding Pixadvisor + doble logo (Nova izq / Pix der):
  1) CLIENTE  -> solo precio final (sin costo interno ni margen)
  2) INTERNO  -> desglose completo (costo landed, impuestos, margen 30%)
"""
import os
from PIL import Image, ImageChops
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_RIGHT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas

DESK  = r"C:/Users/Usuario/Desktop"
ASSET = os.path.join(DESK, "_assets_estudio")
os.makedirs(ASSET, exist_ok=True)
OUT_CLIENT   = os.path.join(DESK, "Estudio_Inversion_Gil_Jorge_Aguilera_CLIENTE.pdf")
OUT_INTERNAL = os.path.join(DESK, "Estudio_Inversion_Gil_Jorge_Aguilera_INTERNO_Pixadvisor.pdf")

# ---------------------------------------------------------------- colors
TEAL=HexColor('#0D9488'); TEAL_D=HexColor('#0F766E')
LIME=HexColor('#7FD633'); BLUE=HexColor('#1E40AF'); DARK=HexColor('#0F172A')
TEXT=HexColor('#1E293B'); MUTED=HexColor('#64748B'); SURFACE=HexColor('#F8FAFC')
BORDER=HexColor('#E2E8F0'); TEAL_TINT=HexColor('#E8F6F4'); LIME_TINT=HexColor('#F2FAE6')
AMBER=HexColor('#D97706'); AMBER_TINT=HexColor('#FEF3C7')
TEAL_HEX='#0D9488'

# ---------------------------------------------------------------- assets (logos)
def trim_white(src, dst):
    im = Image.open(src).convert('RGB')
    bbox = ImageChops.difference(im, Image.new('RGB', im.size, (255,255,255))).getbbox()
    if bbox:
        p=2; bbox=(max(0,bbox[0]-p),max(0,bbox[1]-p),min(im.size[0],bbox[2]+p),min(im.size[1],bbox[3]+p))
        im=im.crop(bbox)
    im.save(dst); return im.size

def trim_alpha(src, dst):
    im = Image.open(src).convert('RGBA'); bbox=im.split()[3].getbbox()
    if bbox: im=im.crop(bbox)
    im.save(dst); return im.size

def extract_nova_logo(src_pdf, dst):
    import fitz
    doc = fitz.open(src_pdf); best=None
    for img in doc[0].get_images(full=True):
        b=doc.extract_image(img[0]); w,h=b['width'],b['height']
        if 1.3 < w/float(h) < 4.0 and w>80 and (best is None or w>best[1]):
            best=(b['image'],w,h)
    open(dst,'wb').write(best[0]); return dst

_nraw = extract_nova_logo(os.path.join(DESK,'Propuesta_Gil_Gorje_Aguilera.pdf'), os.path.join(ASSET,'nova_raw.png'))
nova_sz = trim_white(_nraw, os.path.join(ASSET,'nova.png'))
pix_sz  = trim_alpha(r'D:/PIXADVISOR_AGENT_WORKSPACE/pixadvisor-website/img/logo-pix.png', os.path.join(ASSET,'pix.png'))
NOVA_RATIO=nova_sz[0]/nova_sz[1]; PIX_RATIO=pix_sz[0]/pix_sz[1]
NOVA=os.path.join(ASSET,'nova.png'); PIX=os.path.join(ASSET,'pix.png')

# ---------------------------------------------------------------- geometry
PAGE_W, PAGE_H = letter
LM=RM=0.85*inch; TM=1.18*inch; BM=1.00*inch
CONTENT_W = PAGE_W-LM-RM

def grad_rect(c,x,y,w,h,colors,positions):
    c.saveState(); p=c.beginPath(); p.rect(x,y,w,h); c.clipPath(p,stroke=0,fill=0)
    c.linearGradient(x,y,x+w,y,colors,positions,extend=True); c.restoreState()

def header_footer(c, doc):
    c.saveState()
    nova_h=26.0; nova_w=nova_h*NOVA_RATIO; pix_h=34.0; pix_w=pix_h*PIX_RATIO
    top=PAGE_H-24; center=top-pix_h/2.0
    c.drawImage(NOVA, LM, center-nova_h/2.0, width=nova_w, height=nova_h, mask='auto', preserveAspectRatio=True)
    c.drawImage(PIX, PAGE_W-RM-pix_w, center-pix_h/2.0, width=pix_w, height=pix_h, mask='auto', preserveAspectRatio=True)
    grad_rect(c, LM, top-pix_h-9, CONTENT_W, 2.4, [LIME,TEAL,BLUE], [0,0.5,1])
    c.setStrokeColor(BORDER); c.setLineWidth(0.6); c.line(LM, BM-16, PAGE_W-RM, BM-16)
    c.setFont('Helvetica-Bold',7.5); c.setFillColor(TEAL); c.drawString(LM, BM-28, 'PIXADVISOR  —  Agricultura de Precisión')
    c.setFont('Helvetica',6.8); c.setFillColor(MUTED)
    c.drawString(LM, BM-37, 'En alianza con Nova Agrícola — Comércio de Biodefensivos Ltda · Canoinhas/SC · novaagricola@gmail.com · (47) 3622-1471')
    c.restoreState()

class NumberedCanvas(canvas.Canvas):
    def __init__(self,*a,**k): canvas.Canvas.__init__(self,*a,**k); self._saved=[]
    def showPage(self): self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        n=len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.setFont('Helvetica',7.5); self.setFillColor(MUTED)
            self.drawRightString(PAGE_W-RM, BM-28, 'Página %d de %d' % (self._pageNumber, n))
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

# ---------------------------------------------------------------- styles
ss=getSampleStyleSheet()
def S(name,**kw): kw.setdefault('fontName','Helvetica'); return ParagraphStyle(name,parent=ss['Normal'],**kw)
eyebrow=S('eyebrow',fontName='Helvetica-Bold',fontSize=9.5,textColor=TEAL,spaceAfter=10,leading=12)
ctitle =S('ctitle',fontName='Helvetica-Bold',fontSize=24,textColor=DARK,leading=28,spaceAfter=8)
csub   =S('csub',fontSize=12.5,textColor=MUTED,leading=17,spaceAfter=2)
h1     =S('h1',fontName='Helvetica-Bold',fontSize=15,textColor=TEAL_D,spaceBefore=4,spaceAfter=2,leading=18)
h2     =S('h2',fontName='Helvetica-Bold',fontSize=12,textColor=DARK,spaceBefore=10,spaceAfter=4,leading=15)
body   =S('body',fontSize=10,textColor=TEXT,leading=14.5,alignment=TA_JUSTIFY,spaceAfter=7)
obj_b  =S('obj_b',fontSize=10,textColor=TEXT,leading=14,leftIndent=13,firstLineIndent=-11,spaceAfter=4)
cb_lab =S('cb_lab',fontName='Helvetica-Bold',fontSize=8,textColor=MUTED,leading=11)
cb_val =S('cb_val',fontName='Helvetica-Bold',fontSize=11,textColor=DARK,leading=14)
th     =S('th',fontName='Helvetica-Bold',fontSize=8.7,textColor=white,leading=11)
th_r   =S('th_r',fontName='Helvetica-Bold',fontSize=8.7,textColor=white,leading=11,alignment=TA_RIGHT)
td     =S('td',fontSize=9.3,textColor=TEXT,leading=12)
td_r   =S('td_r',fontSize=9.3,textColor=TEXT,leading=12,alignment=TA_RIGHT)
td_b   =S('td_b',fontName='Helvetica-Bold',fontSize=9.6,textColor=DARK,leading=12)
td_br  =S('td_br',fontName='Helvetica-Bold',fontSize=9.6,textColor=DARK,leading=12,alignment=TA_RIGHT)
kpi_lab=S('kpi_lab',fontName='Helvetica-Bold',fontSize=8.3,textColor=white,leading=10.5)
kpi_big=S('kpi_big',fontName='Helvetica-Bold',fontSize=21,textColor=white,leading=23)
kpi_sub=S('kpi_sub',fontSize=8,textColor=HexColor('#E6FFFA'),leading=10.5)
note_st=S('note_st',fontSize=9,textColor=TEXT,leading=12.8,leftIndent=12,firstLineIndent=-10,spaceAfter=3)
callout=S('callout',fontName='Helvetica-Oblique',fontSize=10.5,textColor=TEXT,leading=15.5,alignment=TA_JUSTIFY)
badge_s=S('badge_s',fontName='Helvetica-Bold',fontSize=8,textColor=white,leading=10,alignment=TA_CENTER)

# ---------------------------------------------------------------- builders
def section(num,title):
    return [KeepTogether([Paragraph('%s.&nbsp;&nbsp;%s'%(num,title),h1),
        HRFlowable(width='100%',thickness=2,color=LIME,lineCap='round',spaceBefore=3,spaceAfter=9)])]

def client_box(rows):
    data=[[Paragraph(l,cb_lab),Paragraph(v,cb_val)] for l,v in rows]
    inner=Table(data,colWidths=[145,CONTENT_W-6-145])
    st=[('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),12)]
    for i in range(len(data)):
        st.append(('BACKGROUND',(0,i),(-1,i),SURFACE if i%2==0 else white))
        if i: st.append(('LINEABOVE',(0,i),(-1,i),0.6,BORDER))
    inner.setStyle(TableStyle(st))
    box=Table([['',inner]],colWidths=[6,CONTENT_W-6])
    box.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),TEAL),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOX',(0,0),(-1,-1),0.8,BORDER),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    return box

def kpi_row(cards):
    gut=12; n=len(cards); cw=(CONTENT_W-gut*(n-1))/n
    cols=[]; widths=[]
    for i,(lab,big,sub,bg) in enumerate(cards):
        if i>0: cols.append(''); widths.append(gut)
        cols.append([Paragraph(lab,kpi_lab),Spacer(1,4),Paragraph(big,kpi_big),Spacer(1,2),Paragraph(sub,kpi_sub)])
        widths.append(cw)
    t=Table([cols],colWidths=widths)
    st=[('VALIGN',(0,0),(-1,-1),'MIDDLE')]
    for i,(lab,big,sub,bg) in enumerate(cards):
        ci=2*i
        st+=[('BACKGROUND',(ci,0),(ci,0),bg),('LEFTPADDING',(ci,0),(ci,0),13),('RIGHTPADDING',(ci,0),(ci,0),13),
             ('TOPPADDING',(ci,0),(ci,0),13),('BOTTOMPADDING',(ci,0),(ci,0),13)]
    t.setStyle(TableStyle(st))
    return t

def money_table(header, rows, ncols=3):
    """rows: list of tuples (concepto, c1, [c2], kind). kind in normal/sub/total."""
    head=[Paragraph(header[0],th)]+[Paragraph(h,th_r) for h in header[1:]]
    data=[head]; kinds=['head']
    for r in rows:
        concepto=r[0]; vals=r[1:-1]; kind=r[-1]
        if kind=='normal':
            data.append([Paragraph(concepto,td)]+[Paragraph(v,td_r) for v in vals])
        else:
            data.append([Paragraph(concepto,td_b)]+[Paragraph(v,td_br) for v in vals])
        kinds.append(kind)
    if ncols==3: colW=[CONTENT_W*0.50, CONTENT_W*0.25, CONTENT_W*0.25]
    else:        colW=[CONTENT_W*0.62, CONTENT_W*0.38]
    t=Table(data,colWidths=colW,repeatRows=1)
    st=[('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW',(0,0),(-1,0),0.8,TEAL_D),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('LINEBELOW',(0,1),(-1,-1),0.5,BORDER),('BOX',(0,0),(-1,-1),0.8,BORDER)]
    for i,k in enumerate(kinds):
        if k=='normal' and i%2==0: st.append(('BACKGROUND',(0,i),(-1,i),SURFACE))
        if k=='sub':   st.append(('BACKGROUND',(0,i),(-1,i),TEAL_TINT))
        if k=='total': st+=[('BACKGROUND',(0,i),(-1,i),LIME_TINT),('LINEABOVE',(0,i),(-1,i),1.0,TEAL)]
    t.setStyle(TableStyle(st))
    return t

def bullets_box(items, accent=TEAL):
    paras=[Paragraph('<font color="%s">•</font> %s'%(TEAL_HEX,t),obj_b) for t in items]
    t=Table([[paras]],colWidths=[CONTENT_W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),SURFACE),('BOX',(0,0),(-1,-1),0.8,BORDER),
        ('LINEBEFORE',(0,0),(0,-1),3,accent),('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING',(0,0),(-1,-1),15),('RIGHTPADDING',(0,0),(-1,-1),12)]))
    return t

def callout_box(text, strip=TEAL, bg=TEAL_TINT):
    p=Paragraph(text,callout)
    t=Table([['',p]],colWidths=[6,CONTENT_W-6])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),strip),('BACKGROUND',(1,0),(1,0),bg),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(1,0),(1,0),15),('RIGHTPADDING',(1,0),(1,0),15),
        ('TOPPADDING',(1,0),(1,0),12),('BOTTOMPADDING',(1,0),(1,0),12),
        ('LEFTPADDING',(0,0),(0,0),0),('RIGHTPADDING',(0,0),(0,0),0)]))
    return t

def note_box(title, items, strip=AMBER, bg=AMBER_TINT):
    inner=[Paragraph('<b>%s</b>'%title, S('nt',fontName='Helvetica-Bold',fontSize=9.5,textColor=HexColor('#92400E'),spaceAfter=5))]
    inner+=[Paragraph('<font color="#92400E">•</font> %s'%it, note_st) for it in items]
    t=Table([['',inner]],colWidths=[6,CONTENT_W-6])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),strip),('BACKGROUND',(1,0),(1,0),bg),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(1,0),(1,0),14),('RIGHTPADDING',(1,0),(1,0),12),
        ('TOPPADDING',(1,0),(1,0),11),('BOTTOMPADDING',(1,0),(1,0),9),
        ('LEFTPADDING',(0,0),(0,0),0),('RIGHTPADDING',(0,0),(0,0),0)]))
    return t

def badge(txt, bg=AMBER):
    t=Table([[Paragraph(txt,badge_s)]],colWidths=[150])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg),('TOPPADDING',(0,0),(-1,-1),4),
        ('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
    t.hAlign='LEFT'; return t

# ---------------------------------------------------------------- financials
VOL=6000; FOB_L=20.00; FOB=VOL*FOB_L
F_COR=12000.0; F_HAC=11000.0
IMP_IMPO=0.10; IMP_FACT=0.16; MARGEN=0.15; FX=2.10
SUBLOG=FOB+F_COR+F_HAC
IMPORT=SUBLOG*IMP_IMPO
INTERNADO=SUBLOG+IMPORT
DIV=1-IMP_FACT-MARGEN
PVENTA=INTERNADO/DIV
T_IMP=PVENTA*IMP_FACT
T_MAR=PVENTA*MARGEN
PV_L=PVENTA/VOL
PCTm=lambda x:"{:.0f}%".format(x*100)
PCT_COSTO=PCTm(DIV); PCT_IMP=PCTm(IMP_FACT); PCT_MAR=PCTm(MARGEN)
DIV_STR=("{:.2f}".format(DIV)).replace('.',',')
FACTOR_STR=("{:.2f}".format(PVENTA/FOB)).replace('.',',')+'×'
MK_PV_L=INTERNADO*(1+MARGEN)*(1+IMP_FACT)/VOL            # alternativa markup
ALT_INT=(FOB+F_COR)*(1+IMP_IMPO)+F_HAC                   # alternativa import CIF frontera
ALT_PV=ALT_INT/DIV

# rs/rs0 reciben valores en R$ y los etiquetan; bs/bs0 reciben R$ y CONVIERTEN a Bs (×FX)
def rs(x): return ("R$ {:,.2f}".format(x)).replace(',','X').replace('.',',').replace('X','.')
def bs(x): return ("Bs {:,.2f}".format(x*FX)).replace(',','X').replace('.',',').replace('X','.')
def rs0(x):return ("R$ {:,.0f}".format(x)).replace(',','.')
def bs0(x):return ("Bs {:,.0f}".format(x*FX)).replace(',','.')

FECHA='31 de mayo de 2026'
ALCANCE=['Instalación y puesta en marcha del sistema biológico (6 biorreactores).',
         'Producción On-Farm de microorganismos seleccionados.',
         'Desarrollo de consorcios microbianos para el tratamiento de deyecciones porcinas.',
         'Acompañamiento técnico y protocolos de producción.',
         'Monitoreo de calidad microbiológica y validación de procesos.',
         'Capacitación operativa del personal responsable.']

# ================================================================ CLIENT PDF
def build_client():
    s=[]
    s.append(Spacer(1,14))
    s.append(Paragraph('ESTUDIO DE INVERSIÓN &nbsp;·&nbsp; BIOFÁBRICA ON-FARM', eyebrow))
    s.append(Paragraph('Inversión del Proyecto — Producción de Biofertilizantes', ctitle))
    s.append(Paragraph('Sistema de valorización de deyecciones porcinas mediante producción On-Farm de microorganismos', csub))
    s.append(HRFlowable(width=130,thickness=3,color=LIME,lineCap='round',spaceBefore=12,spaceAfter=20,hAlign='LEFT'))
    s.append(client_box([('CLIENTE','Gil Jorge Aguilera'),
                         ('DESTINO','Hacienda San Jorge'),
                         ('PRESENTADO POR','Pixadvisor — Agricultura de Precisión'),
                         ('EN ALIANZA CON','Nova Agrícola — Comércio de Biodefensivos Ltda'),
                         ('FECHA',FECHA)]))
    s.append(Spacer(1,14))
    s+=section('1','Inversión del Proyecto')
    s.append(Paragraph('Valores correspondientes al ciclo de producción contratado, con el producto '
                       '<b>entregado y puesto en la Hacienda San Jorge</b>. El precio incluye flete internacional '
                       '(Brasil–Bolivia), transporte nacional hasta la hacienda, nacionalización e impuestos.', body))
    s.append(kpi_row([
        ('COSTO POR LITRO', bs(PV_L), 'por litro · puesto en finca', TEAL),
        ('INVERSIÓN TOTAL POR CICLO', bs0(PVENTA), '6.000 litros / ciclo', BLUE),
    ]))
    s.append(Spacer(1,10))
    inv_tbl=money_table(('Concepto','Cantidad'),
        [('Volumen contratado','6.000 litros / ciclo','normal'),
         ('Precio por litro (puesto en Hacienda San Jorge)', bs(PV_L),'normal'),
         ('INVERSIÓN TOTAL POR CICLO', bs(PVENTA),'total')], ncols=2)
    fxnote=Paragraph('<font size="7" color="#64748B">Precio puesto en Hacienda San Jorge — incluye flete, '
                     'nacionalización e impuestos. Valores expresados en bolivianos (Bs).</font>',
                     S('fx',fontSize=7,textColor=MUTED,leading=10))
    s.append(KeepTogether([inv_tbl, Spacer(1,4), fxnote]))
    s+=section('2','Alcance Contratado')
    s.append(bullets_box(ALCANCE))
    s+=section('3','Retorno Estratégico')
    s.append(callout_box('El proyecto convierte las deyecciones porcinas en un insumo biológico de alto valor '
        'agregado, reduciendo costos de manejo de residuos y la dependencia de fertilizantes químicos, '
        'e incrementando la materia orgánica y la productividad del suelo a mediano y largo plazo — '
        'una fuente permanente de rentabilidad alineada con la economía circular.'))
    doc=SimpleDocTemplate(OUT_CLIENT,pagesize=letter,leftMargin=LM,rightMargin=RM,topMargin=TM,bottomMargin=BM,
        title='Estudio de Inversión — Biofábrica On-Farm', author='Pixadvisor — Agricultura de Precisión',
        subject='Inversión del proyecto · Cliente: Gil Jorge Aguilera')
    doc.build(s,onFirstPage=header_footer,onLaterPages=header_footer,canvasmaker=NumberedCanvas)

# ================================================================ INTERNAL PDF
def build_internal():
    s=[]
    s.append(Spacer(1,40))
    s.append(badge('USO INTERNO — NO DISTRIBUIR'))
    s.append(Spacer(1,8))
    s.append(Paragraph('ESTUDIO FINANCIERO &nbsp;·&nbsp; ANÁLISIS DE COSTO Y PRECIO', eyebrow))
    s.append(Paragraph('Estructura de Costo, Impuestos y Margen', ctitle))
    s.append(Paragraph('Proyecto biofábrica On-Farm — Cliente Gil Jorge Aguilera · Hacienda San Jorge', csub))
    s.append(HRFlowable(width=130,thickness=3,color=LIME,lineCap='round',spaceBefore=12,spaceAfter=18,hAlign='LEFT'))
    s.append(kpi_row([
        ('COSTO INTERNADO (Pix)', bs0(INTERNADO), rs0(INTERNADO), TEAL_D),
        ('PRECIO DE VENTA', bs0(PVENTA), rs0(PVENTA), BLUE),
        ('MARGEN NETA ('+PCT_MAR+')', bs0(T_MAR), rs0(T_MAR), TEAL),
    ]))
    s.append(Spacer(1,16))
    s+=section('1','Cadena de Costo hasta la Hacienda')
    s.append(money_table(('Concepto','R$','Bs'),
        [('FOB Brasil — 6.000 L × R$ 20,00 (Canoinhas, SC)', rs(FOB), bs(FOB),'normal'),
         ('+ Flete Canoinhas → Corumbá', rs(F_COR), bs(F_COR),'normal'),
         ('+ Flete Corumbá → Hacienda San Jorge', rs(F_HAC), bs(F_HAC),'normal'),
         ('= Subtotal logística', rs(SUBLOG), bs(SUBLOG),'sub'),
         ('+ Importación (10% sobre el total)', rs(IMPORT), bs(IMPORT),'normal'),
         ('= COSTO TOTAL INTERNADO (landed cost)', rs(INTERNADO), bs(INTERNADO),'total')]))
    s+=section('2','Estructura del Precio de Venta')
    s.append(Paragraph('Con margen <b>neta del '+PCT_MAR+'</b> e impuesto de facturación del <b>'+PCT_IMP+'</b> (IVA 13% + IT 3%), '
        'ambos sobre el precio de venta, la composición de cada unidad facturada es: '
        '<b>'+PCT_COSTO+' costo + '+PCT_IMP+' impuesto + '+PCT_MAR+' margen</b>. Precio = Costo ÷ '+DIV_STR+'.', body))
    s.append(money_table(('Componente','R$','Bs'),
        [('Costo internado ('+PCT_COSTO+')', rs(INTERNADO), bs(INTERNADO),'normal'),
         ('Impuesto de facturación '+PCT_IMP+' (IVA + IT)', rs(T_IMP), bs(T_IMP),'normal'),
         ('Margen neta Pixadvisor '+PCT_MAR, rs(T_MAR), bs(T_MAR),'normal'),
         ('= PRECIO DE VENTA TOTAL', rs(PVENTA), bs(PVENTA),'total')]))
    s.append(Spacer(1,8))
    s+=section('3','Resultado por Litro y Parámetros')
    s.append(money_table(('Indicador','R$','Bs'),
        [('Precio de venta por litro', rs(PV_L), bs(PV_L),'total'),
         ('Costo FOB por litro (referencia)', rs(FOB_L), bs(FOB_L),'normal'),
         ('Factor FOB → cliente', FACTOR_STR, FACTOR_STR,'normal'),
         ('Tipo de cambio aplicado', '—', '2,10 Bs / R$','normal')]))
    s.append(Spacer(1,8))
    s.append(note_box('Supuestos del cálculo (confirmar antes de cotizar)', [
        '«Margen neta '+PCT_MAR+'» tomada sobre el precio de venta (Precio = Costo ÷ '+DIV_STR+'). Si fuera markup '+PCT_MAR+' sobre costo, el precio/L baja a ~'+bs(MK_PV_L)+' ('+rs(MK_PV_L)+').',
        'Importación 10% aplicada sobre el total (FOB + ambos fletes). Si va solo sobre CIF en frontera (FOB + flete a Corumbá): '+bs(ALT_PV/VOL)+'/L y total '+bs0(ALT_PV)+'.',
        '16% = IVA 13% + IT 3% de Bolivia sobre la factura. Fletes e importación tratados como costo (no se computó crédito fiscal).',
    ]))
    doc=SimpleDocTemplate(OUT_INTERNAL,pagesize=letter,leftMargin=LM,rightMargin=RM,topMargin=TM,bottomMargin=BM,
        title='Estudio Financiero (INTERNO) — Proyecto Gil Jorge Aguilera', author='Pixadvisor — Agricultura de Precisión',
        subject='USO INTERNO · Costo, impuestos y margen')
    doc.build(s,onFirstPage=header_footer,onLaterPages=header_footer,canvasmaker=NumberedCanvas)

build_client()
build_internal()
print('OK CLIENTE  ->', OUT_CLIENT, '|', os.path.getsize(OUT_CLIENT), 'bytes')
print('OK INTERNO  ->', OUT_INTERNAL, '|', os.path.getsize(OUT_INTERNAL), 'bytes')
print('precio/L Bs', round(PV_L*FX,2), '| total Bs', round(PVENTA*FX,2))
