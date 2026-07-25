# -*- coding: utf-8 -*-
"""Resumen ejecutivo (1 pag) del flujo de caja Pixadvisor — branding Pix (sin Nova)."""
import os
from PIL import Image, ImageChops
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas

DESK=r"C:/Users/Usuario/Desktop"; ASSET=os.path.join(DESK,"_assets_resumen"); os.makedirs(ASSET,exist_ok=True)
OUT=os.path.join(DESK,"Resumen_Flujo_de_Caja_Pixadvisor.pdf")
TEAL=HexColor('#0D9488'); TEALD=HexColor('#0F766E'); LIME=HexColor('#7FD633'); BLUE=HexColor('#1E40AF')
DARK=HexColor('#0F172A'); TEXT=HexColor('#1E293B'); MUTED=HexColor('#64748B'); SURFACE=HexColor('#F8FAFC')
BORDER=HexColor('#E2E8F0'); TEAL_TINT=HexColor('#E8F6F4'); LIME_TINT=HexColor('#EFFAD9'); TEAL_HEX='#0D9488'

def trim_alpha(src,dst):
    im=Image.open(src).convert('RGBA'); b=im.split()[3].getbbox()
    if b: im=im.crop(b)
    im.save(dst); return im.size
pix_sz=trim_alpha(r'D:/PIXADVISOR_AGENT_WORKSPACE/pixadvisor-website/img/logo-pix.png',os.path.join(ASSET,'pix.png'))
PIX=os.path.join(ASSET,'pix.png'); PIX_RATIO=pix_sz[0]/pix_sz[1]

PAGE_W,PAGE_H=letter; LM=RM=0.8*inch; TM=1.05*inch; BM=0.7*inch; CONTENT_W=PAGE_W-LM-RM

def grad_rect(c,x,y,w,h,cols,pos):
    c.saveState(); p=c.beginPath(); p.rect(x,y,w,h); c.clipPath(p,stroke=0,fill=0)
    c.linearGradient(x,y,x+w,y,cols,pos,extend=True); c.restoreState()

def header_footer(c,doc):
    c.saveState()
    pix_h=34.0; pix_w=pix_h*PIX_RATIO; top=PAGE_H-26
    c.drawImage(PIX, LM, top-pix_h, width=pix_w, height=pix_h, mask='auto', preserveAspectRatio=True)
    grad_rect(c, LM, top-pix_h-9, CONTENT_W, 2.4, [LIME,TEAL,BLUE],[0,0.5,1])
    c.setStrokeColor(BORDER); c.setLineWidth(0.6); c.line(LM,BM-14,PAGE_W-RM,BM-14)
    c.setFont('Helvetica-Bold',7.5); c.setFillColor(TEAL); c.drawString(LM,BM-25,'PIXADVISOR  —  Agricultura de Precisión')
    c.setFont('Helvetica',7); c.setFillColor(MUTED)
    c.drawString(LM,BM-34,'Documento interno · Socios: Nilton Camargo & Victor Velasco · uso confidencial')
    c.setFont('Helvetica',7.5); c.setFillColor(MUTED); c.drawRightString(PAGE_W-RM,BM-25,'31 de mayo de 2026')
    c.restoreState()

ss=getSampleStyleSheet()
def S(n,**k): k.setdefault('fontName','Helvetica'); return ParagraphStyle(n,parent=ss['Normal'],**k)
eyebrow=S('e',fontName='Helvetica-Bold',fontSize=9,textColor=TEAL,spaceAfter=6,leading=11)
ctitle=S('t',fontName='Helvetica-Bold',fontSize=20,textColor=DARK,leading=23,spaceAfter=4)
csub=S('s',fontSize=10.5,textColor=MUTED,leading=14)
h1=S('h1',fontName='Helvetica-Bold',fontSize=12,textColor=TEALD,spaceBefore=2,spaceAfter=2,leading=15)
kpi_lab=S('kl',fontName='Helvetica-Bold',fontSize=7.8,textColor=white,leading=10)
kpi_big=S('kb',fontName='Helvetica-Bold',fontSize=18,textColor=white,leading=20)
kpi_sub=S('ksu',fontSize=7.3,textColor=HexColor('#E6FFFA'),leading=9)
th=S('th',fontName='Helvetica-Bold',fontSize=8.3,textColor=white,leading=10.5)
th_r=S('thr',fontName='Helvetica-Bold',fontSize=8.3,textColor=white,leading=10.5,alignment=TA_RIGHT)
td=S('td',fontSize=8.7,textColor=TEXT,leading=11)
td_r=S('tdr',fontSize=8.7,textColor=TEXT,leading=11,alignment=TA_RIGHT)
td_b=S('tdb',fontName='Helvetica-Bold',fontSize=8.9,textColor=DARK,leading=11)
td_br=S('tdbr',fontName='Helvetica-Bold',fontSize=8.9,textColor=DARK,leading=11,alignment=TA_RIGHT)
rec=S('rec',fontSize=8.7,textColor=TEXT,leading=12,leftIndent=11,firstLineIndent=-9,spaceAfter=3)

def bs(x): return ('Bs {:,.0f}'.format(x)).replace(',','.')

# numbers
em=23000*2+4500+2500*(52/12)+2800+1000+1500+3000; ea=em*12; fondo=em*5
veh=25000*6.96; dron=85000*2.10; casa=35000*6.96
inv_tot=2*veh+2*dron+casa; inv1=veh+2*dron; inv2=veh+casa
y1=ea+fondo+inv1; y2=ea+inv2; y3=ea+350000*2

def kpi_row(cards):
    gut=10; n=len(cards); cw=(CONTENT_W-gut*(n-1))/n; cols=[]; widths=[]
    for i,(lab,big,sub,bg) in enumerate(cards):
        if i>0: cols.append(''); widths.append(gut)
        cols.append([Paragraph(lab,kpi_lab),Spacer(1,3),Paragraph(big,kpi_big),Spacer(1,2),Paragraph(sub,kpi_sub)]); widths.append(cw)
    t=Table([cols],colWidths=widths); st=[('VALIGN',(0,0),(-1,-1),'MIDDLE')]
    for i,(lab,big,sub,bg) in enumerate(cards):
        ci=2*i; st+=[('BACKGROUND',(ci,0),(ci,0),bg),('LEFTPADDING',(ci,0),(ci,0),11),('RIGHTPADDING',(ci,0),(ci,0),11),
                     ('TOPPADDING',(ci,0),(ci,0),10),('BOTTOMPADDING',(ci,0),(ci,0),10)]
    t.setStyle(TableStyle(st)); return t

def mtable(header,rows,colw):
    data=[[Paragraph(header[0],th)]+[Paragraph(h,th_r) for h in header[1:]]]; kinds=['h']
    for r in rows:
        kind=r[-1]; vals=r[1:-1]
        if kind=='total': data.append([Paragraph(r[0],td_b)]+[Paragraph(v,td_br) for v in vals])
        else: data.append([Paragraph(r[0],td)]+[Paragraph(v,td_r) for v in vals])
        kinds.append(kind)
    t=Table(data,colWidths=colw,repeatRows=1)
    stl=[('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
         ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
         ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
         ('LINEBELOW',(0,1),(-1,-1),0.4,BORDER),('BOX',(0,0),(-1,-1),0.7,BORDER)]
    for i,k in enumerate(kinds):
        if k=='n' and i%2==0: stl.append(('BACKGROUND',(0,i),(-1,i),SURFACE))
        if k=='total': stl+=[('BACKGROUND',(0,i),(-1,i),LIME_TINT),('LINEABOVE',(0,i),(-1,i),0.8,TEAL)]
    t.setStyle(TableStyle(stl)); return t

story=[]
story.append(Spacer(1,2))
story.append(Paragraph('RESUMEN EJECUTIVO &nbsp;·&nbsp; PLAN FINANCIERO',eyebrow))
story.append(Paragraph('Flujo de Caja — Pixadvisor',ctitle))
story.append(Paragraph('Estructura de costos, fondo de subsistencia, inversiones y metas de facturación',csub))
story.append(HRFlowable(width=120,thickness=3,color=LIME,lineCap='round',spaceBefore=8,spaceAfter=12,hAlign='LEFT'))

story.append(kpi_row([
    ('EGRESOS MENSUALES', bs(em), 'fijos · '+bs(ea)+'/año', TEAL),
    ('FONDO SUBSISTENCIA', bs(fondo), 'colchón de 5 meses', TEALD),
    ('META AÑO 3+', bs(y3), 'facturación anual', BLUE),
]))
story.append(Spacer(1,12))

# dos tablas lado a lado: egresos | proyeccion
egresos=[('Retiradas socios (2)',bs(46000),'n'),('Técnico de campo',bs(4500),'n'),
         ('Viáticos de campo',bs(2500*52/12),'n'),('APRISA',bs(2800),'n'),
         ('Mantenimiento camioneta',bs(1000),'n'),('Internet/agua/luz/tel.',bs(1500),'n'),
         ('Despensas extras',bs(3000),'n'),('TOTAL MENSUAL',bs(em),'total')]
left=[Paragraph('Egresos mensuales',h1), Spacer(1,3), mtable(('Concepto','Bs/mes'),egresos,[1.55*inch,0.95*inch])]
proy=[('Egresos operativos',bs(ea),'n'),('Fondo subsistencia',bs(fondo),'n'),
      ('Inversiones del año',bs(inv1),'n'),('Retiros socios',bs(0),'n'),('INGRESO REQ. AÑO 1',bs(y1),'total')]
proy2=[('Egresos operativos',bs(ea),'n'),('Inversiones del año',bs(inv2),'n'),('INGRESO REQ. AÑO 2',bs(y2),'total')]
right=[Paragraph('Ingreso requerido por año',h1), Spacer(1,3),
       mtable(('Concepto','Año 1'),proy,[1.55*inch,0.95*inch]), Spacer(1,4),
       mtable(('Concepto','Año 2'),proy2,[1.55*inch,0.95*inch])]
two=Table([[left,'',right]],colWidths=[(CONTENT_W-16)/2,16,(CONTENT_W-16)/2])
two.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
story.append(two)
story.append(Spacer(1,12))

# inversiones + metas en una fila
story.append(Paragraph('Plan de inversiones y metas',h1))
story.append(Spacer(1,3))
inv_rows=[('2 vehículos ($25.000 c/u · USD 6,96)',bs(2*veh),'n'),
          ('2 drones de mapeo (R$85.000 c/u · 2,10)',bs(2*dron),'n'),
          ('Casa en anticrético ($35.000)',bs(casa),'n'),
          ('INVERSIÓN TOTAL (Año 1 + Año 2)',bs(inv_tot),'total')]
metas_rows=[('Equilibrio (cubrir costos)',bs(ea),'n'),
            ('+ Fondo de subsistencia',bs(ea+fondo),'n'),
            ('Régimen objetivo Año 3+',bs(y3),'total')]
inv_t=mtable(('Inversiones','Bs'),inv_rows,[2.7*inch,1.1*inch])
metas_t=mtable(('Meta de facturación','Bs/año'),metas_rows,[1.95*inch,1.05*inch])
row2=Table([[inv_t,'',metas_t]],colWidths=[3.85*inch,0.12*inch,CONTENT_W-3.85*inch-0.12*inch])
row2.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
story.append(row2)
story.append(Spacer(1,11))

story.append(Paragraph('Recomendaciones',h1))
story.append(Spacer(1,2))
for t in ['<b>Primero el colchón:</b> juntar los '+bs(fondo)+' (5 meses) antes de invertir fuerte — protege ante paros o falta de combustible.',
          '<b>Año 1 es el más exigente:</b> apuntar a ~'+bs(y1/12)+'/mes; al cierre se cubre el fondo y la 1ª etapa de inversión.',
          '<b>Orden de compra:</b> 2 drones + 1 camioneta en Año 1 (generan ingresos); casa y 2ª camioneta en Año 2.',
          '<b>Ojo con el dólar:</b> cálculo al oficial Bs 6,96; si compran en el paralelo, la inversión sube — ajustar en el Excel.']:
    story.append(Paragraph('<font color="%s">•</font> %s'%(TEAL_HEX,t),rec))

doc=SimpleDocTemplate(OUT,pagesize=letter,leftMargin=LM,rightMargin=RM,topMargin=TM,bottomMargin=BM,
    title='Resumen Flujo de Caja — Pixadvisor',author='Pixadvisor — Agricultura de Precisión')
doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)
print('OK ->',OUT,'|',os.path.getsize(OUT),'bytes')
