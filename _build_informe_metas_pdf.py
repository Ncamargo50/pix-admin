# -*- coding: utf-8 -*-
"""Informe de Metas de Venta — Pixadvisor (branding Pix, sin Nova)."""
import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas

DESK=r"C:/Users/Usuario/Desktop"
FOLDER=os.path.join(DESK,"PIXADVISOR_Flujo_de_Caja_2026-05-31")
ASSET=os.path.join(DESK,"_assets_informe"); os.makedirs(ASSET,exist_ok=True)
OUT=os.path.join(FOLDER,"Informe_Metas_de_Venta_Pixadvisor.pdf")
TEAL=HexColor('#0D9488'); TEALD=HexColor('#0F766E'); LIME=HexColor('#7FD633'); BLUE=HexColor('#1E40AF')
DARK=HexColor('#0F172A'); TEXT=HexColor('#1E293B'); MUTED=HexColor('#64748B'); SURFACE=HexColor('#F8FAFC')
BORDER=HexColor('#E2E8F0'); TEAL_TINT=HexColor('#E8F6F4'); LIME_TINT=HexColor('#EFFAD9'); TEAL_HEX='#0D9488'

def trim_alpha(src,dst):
    im=Image.open(src).convert('RGBA'); b=im.split()[3].getbbox()
    if b: im=im.crop(b)
    im.save(dst); return im.size
pix_sz=trim_alpha(r'D:/PIXADVISOR_AGENT_WORKSPACE/pixadvisor-website/img/logo-pix.png',os.path.join(ASSET,'pix.png'))
PIX=os.path.join(ASSET,'pix.png'); PIX_RATIO=pix_sz[0]/pix_sz[1]

PAGE_W,PAGE_H=letter; LM=RM=0.8*inch; TM=1.05*inch; BM=0.8*inch; CONTENT_W=PAGE_W-LM-RM

def grad_rect(c,x,y,w,h,cols,pos):
    c.saveState(); p=c.beginPath(); p.rect(x,y,w,h); c.clipPath(p,stroke=0,fill=0)
    c.linearGradient(x,y,x+w,y,cols,pos,extend=True); c.restoreState()
def header_footer(c,doc):
    c.saveState(); pix_h=34.0; pix_w=pix_h*PIX_RATIO; top=PAGE_H-26
    c.drawImage(PIX,LM,top-pix_h,width=pix_w,height=pix_h,mask='auto',preserveAspectRatio=True)
    grad_rect(c,LM,top-pix_h-9,CONTENT_W,2.4,[LIME,TEAL,BLUE],[0,0.5,1])
    c.setStrokeColor(BORDER); c.setLineWidth(0.6); c.line(LM,BM-16,PAGE_W-RM,BM-16)
    c.setFont('Helvetica-Bold',7.5); c.setFillColor(TEAL); c.drawString(LM,BM-27,'PIXADVISOR  —  Agricultura de Precisión')
    c.setFont('Helvetica',6.8); c.setFillColor(MUTED)
    c.drawString(LM,BM-36,'Documento interno · Socios: Nilton Camargo & Victor Velasco · uso confidencial')
    c.setFont('Helvetica',7.5); c.setFillColor(MUTED)
    c.drawRightString(PAGE_W-RM,BM-27,'Página %d'%doc.page)
    c.restoreState()

ss=getSampleStyleSheet()
def S(n,**k): k.setdefault('fontName','Helvetica'); return ParagraphStyle(n,parent=ss['Normal'],**k)
eyebrow=S('e',fontName='Helvetica-Bold',fontSize=9,textColor=TEAL,spaceAfter=6,leading=11)
ctitle=S('t',fontName='Helvetica-Bold',fontSize=21,textColor=DARK,leading=24,spaceAfter=4)
csub=S('s',fontSize=11,textColor=MUTED,leading=15)
h1=S('h1',fontName='Helvetica-Bold',fontSize=13,textColor=TEALD,spaceBefore=4,spaceAfter=3,leading=16)
body=S('b',fontSize=9.7,textColor=TEXT,leading=14,alignment=TA_JUSTIFY,spaceAfter=6)
kpi_lab=S('kl',fontName='Helvetica-Bold',fontSize=7.8,textColor=white,leading=10)
kpi_big=S('kb',fontName='Helvetica-Bold',fontSize=17,textColor=white,leading=19)
kpi_sub=S('ksu',fontSize=7.3,textColor=HexColor('#E6FFFA'),leading=9)
th=S('th',fontName='Helvetica-Bold',fontSize=8.4,textColor=white,leading=11)
thr=S('thr',fontName='Helvetica-Bold',fontSize=8.4,textColor=white,leading=11,alignment=TA_RIGHT)
td=S('td',fontSize=9,textColor=TEXT,leading=11.5)
tdr=S('tdr',fontSize=9,textColor=TEXT,leading=11.5,alignment=TA_RIGHT)
tdb=S('tb',fontName='Helvetica-Bold',fontSize=9.2,textColor=DARK,leading=11.5)
tdbr=S('tbr',fontName='Helvetica-Bold',fontSize=9.2,textColor=DARK,leading=11.5,alignment=TA_RIGHT)
rec=S('rec',fontSize=9.3,textColor=TEXT,leading=13,leftIndent=12,firstLineIndent=-10,spaceAfter=4)

def bs(x): return ('Bs {:,.0f}'.format(x)).replace(',','.')
def n0(x): return '{:,.0f}'.format(x).replace(',','.')

# ---- datos
RATE=10; META=1535600; EQU=835600
# producto: (nombre, unidad, precio_bs, margen, aporte)
P=[('Mapeamento','ha',10*RATE,0.35,0.40),
   ('MAX PIROL','L',8*RATE,0.25,0.30),
   ('Análisis de suelo','ha',15*RATE,0.20,0.20),
   ('On-Farm biofertilizante','L',79.79,0.15,0.10)]
FACT_TOTAL=sum((META*ap)/mg for _,_,_,mg,ap in P)
BLEND=META/FACT_TOTAL

def kpi_row(cards):
    gut=10; nn=len(cards); cw=(CONTENT_W-gut*(nn-1))/nn; cols=[]; widths=[]
    for i,(lab,big,sub,bg) in enumerate(cards):
        if i>0: cols.append(''); widths.append(gut)
        cols.append([Paragraph(lab,kpi_lab),Spacer(1,3),Paragraph(big,kpi_big),Spacer(1,2),Paragraph(sub,kpi_sub)]); widths.append(cw)
    t=Table([cols],colWidths=widths); st=[('VALIGN',(0,0),(-1,-1),'MIDDLE')]
    for i,(lab,big,sub,bg) in enumerate(cards):
        ci=2*i; st+=[('BACKGROUND',(ci,0),(ci,0),bg),('LEFTPADDING',(ci,0),(ci,0),11),('RIGHTPADDING',(ci,0),(ci,0),11),
                     ('TOPPADDING',(ci,0),(ci,0),11),('BOTTOMPADDING',(ci,0),(ci,0),11)]
    t.setStyle(TableStyle(st)); return t

def table(headers,rows,colw,total_idx=None):
    data=[[Paragraph(headers[0],th)]+[Paragraph(h,thr) for h in headers[1:]]]
    for ri,r in enumerate(rows):
        istot=(total_idx is not None and ri==total_idx)
        data.append([Paragraph(str(r[0]),tdb if istot else td)]+[Paragraph(str(v),tdbr if istot else tdr) for v in r[1:]])
    t=Table(data,colWidths=colw,repeatRows=1)
    stl=[('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
         ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
         ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
         ('LINEBELOW',(0,1),(-1,-1),0.4,BORDER),('BOX',(0,0),(-1,-1),0.7,BORDER)]
    for ri in range(1,len(data)):
        if total_idx is not None and ri-1==total_idx:
            stl+=[('BACKGROUND',(0,ri),(-1,ri),LIME_TINT),('LINEABOVE',(0,ri),(-1,ri),0.8,TEAL)]
        elif ri%2==1: stl.append(('BACKGROUND',(0,ri),(-1,ri),SURFACE))
    t.setStyle(TableStyle(stl)); return t

story=[]
story.append(Spacer(1,2))
story.append(Paragraph('PLAN COMERCIAL &nbsp;·&nbsp; METAS DE VENTA',eyebrow))
story.append(Paragraph('Metas de Venta por Producto — Pixadvisor',ctitle))
story.append(Paragraph('Cuánto vender de cada producto y servicio para sostener la empresa · 31 de mayo de 2026',csub))
story.append(HRFlowable(width=120,thickness=3,color=LIME,lineCap='round',spaceBefore=8,spaceAfter=12,hAlign='LEFT'))

# 1. la meta
story.append(Paragraph('1.&nbsp;&nbsp;La meta anual',h1))
story.append(Paragraph('El <b>margen</b> (ganancia) que el negocio debe generar al año para cubrir toda la operación '
    '—incluidos los sueldos de los socios— y los retiros extra del Año 3 en adelante es de <b>'+bs(META)+'</b>. '
    'Como cada producto deja entre 15% y 35% de margen, la <b>facturación</b> necesaria es mayor: con la mezcla '
    'recomendada, ~<b>'+bs(FACT_TOTAL)+'/año</b> (≈ '+bs(FACT_TOTAL/12)+'/mes).',body))
story.append(kpi_row([
    ('META DE MARGEN ANUAL', bs(META), 'cubre operación + retiros', TEAL),
    ('FACTURACIÓN NECESARIA', bs(FACT_TOTAL), '≈ '+bs(FACT_TOTAL/12)+'/mes', BLUE),
    ('MARGEN PROMEDIO', '{:.1f}%'.format(BLEND*100), 'mezcla recomendada', TEALD),
]))
story.append(Spacer(1,12))

# 2. economia por producto
story.append(Paragraph('2.&nbsp;&nbsp;Economía por producto',h1))
econ=[[nm, bs(pb)+'/'+u, '{:.0f}%'.format(mg*100), bs(pb*mg)+'/'+u] for nm,u,pb,mg,ap in P]
story.append(table(['Producto','Precio','Margen','Ganancia por unidad'],econ,
                   [CONTENT_W*0.40,CONTENT_W*0.22,CONTENT_W*0.16,CONTENT_W*0.22]))
story.append(Spacer(1,12))

# 3. mezcla recomendada
story.append(Paragraph('3.&nbsp;&nbsp;Mezcla recomendada (más peso a lo más rentable)',h1))
rows=[]
for nm,u,pb,mg,ap in P:
    margin=META*ap; vol=margin/(pb*mg); fact=margin/mg
    rows.append([nm,'{:.0f}%'.format(ap*100), n0(vol)+' '+u+'/año', n0(vol/12)+' '+u+'/mes', bs(fact)])
rows.append(['TOTAL','100%','—','—',bs(FACT_TOTAL)])
story.append(table(['Producto','Aporte','Volumen al año','Volumen al mes','Facturación/año'],rows,
                   [CONTENT_W*0.30,CONTENT_W*0.12,CONTENT_W*0.21,CONTENT_W*0.19,CONTENT_W*0.18],total_idx=len(rows)-1))
story.append(Spacer(1,12))

# 4. referencia opcion A (se mantiene junta)
solo=[[nm, n0(META/(pb*mg))+' '+u+'/año', n0(META/(pb*mg)/12)+' '+u+'/mes'] for nm,u,pb,mg,ap in P]
story.append(KeepTogether([
    Paragraph('4.&nbsp;&nbsp;Referencia: si un solo producto cubriera toda la meta',h1),
    Paragraph('Si el negocio dependiera de un único producto, el volumen anual necesario sería:',body),
    table(['Producto','Volumen al año','Volumen al mes'],solo,
          [CONTENT_W*0.42,CONTENT_W*0.29,CONTENT_W*0.29])]))
story.append(Spacer(1,12))

# 5. conclusiones
story.append(Paragraph('5.&nbsp;&nbsp;Conclusiones',h1))
for t in ['<b>Mapeamento es el motor:</b> con 35% de margen es el más rentable; cada hectárea aporta Bs 35. Por eso lleva el mayor peso (40%).',
          '<b>MAX PIROL aporta volumen:</b> producto con buen margen (25%); meta ~1.920 L/mes.',
          '<b>On-Farm, peso bajo:</b> su margen (15%) es el más chico, así que conviene usarlo para proyectos grandes y puntuales (tipo Gil Aguilera), no como base.',
          '<b>Meta mensual de facturación:</b> ~'+bs(FACT_TOTAL/12)+', repartida ~1.462 ha mapeo + 1.920 L MAX PIROL + 853 ha análisis + 1.069 L On-Farm.',
          '<b>Palanca clave:</b> cuanto más se cargue la mezcla hacia mapeo y MAX PIROL, menos facturación total hace falta para el mismo margen.']:
    story.append(Paragraph('<font color="%s">•</font> %s'%(TEAL_HEX,t),rec))

doc=SimpleDocTemplate(OUT,pagesize=letter,leftMargin=LM,rightMargin=RM,topMargin=TM,bottomMargin=BM,
    title='Informe de Metas de Venta — Pixadvisor',author='Pixadvisor — Agricultura de Precisión',
    subject='Plan comercial · metas de venta por producto')
doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)
print('OK ->',OUT,'|',os.path.getsize(OUT),'bytes')
print('FACT_TOTAL',bs(FACT_TOTAL),'| blend','{:.1f}%'.format(BLEND*100))
