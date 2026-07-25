# -*- coding: utf-8 -*-
"""Plan Estratégico de Gestión — Pixadvisor (branding Pix)."""
import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak)
from reportlab.platypus.flowables import HRFlowable
from reportlab.pdfgen import canvas

DESK=r"C:/Users/Usuario/Desktop"
FOLDER=os.path.join(DESK,"PIXADVISOR_Flujo_de_Caja_2026-05-31")
ASSET=os.path.join(DESK,"_assets_plan"); os.makedirs(ASSET,exist_ok=True)
OUT=os.path.join(FOLDER,"Plan_Estrategico_Pixadvisor.pdf")
TEAL=HexColor('#0D9488'); TEALD=HexColor('#0F766E'); LIME=HexColor('#7FD633'); BLUE=HexColor('#1E40AF')
DARK=HexColor('#0F172A'); TEXT=HexColor('#1E293B'); MUTED=HexColor('#64748B'); SURFACE=HexColor('#F8FAFC')
BORDER=HexColor('#E2E8F0'); TEAL_TINT=HexColor('#E8F6F4'); LIME_TINT=HexColor('#EFFAD9'); BLUE_TINT=HexColor('#EEF2FB')
TEAL_HEX='#0D9488'; LIME_HEX='#7FD633'

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
    c.drawString(LM,BM-36,'Plan estratégico interno · Socios: Nilton Camargo & Victor Velasco · uso confidencial')
    c.setFont('Helvetica',7.5); c.setFillColor(MUTED); c.drawRightString(PAGE_W-RM,BM-27,'Página %d'%doc.page)
    c.restoreState()

ss=getSampleStyleSheet()
def S(n,**k): k.setdefault('fontName','Helvetica'); return ParagraphStyle(n,parent=ss['Normal'],**k)
eyebrow=S('e',fontName='Helvetica-Bold',fontSize=9,textColor=TEAL,spaceAfter=6,leading=11)
ctitle=S('t',fontName='Helvetica-Bold',fontSize=22,textColor=DARK,leading=25,spaceAfter=4)
csub=S('s',fontSize=11,textColor=MUTED,leading=15)
h1=S('h1',fontName='Helvetica-Bold',fontSize=13.5,textColor=TEALD,spaceBefore=4,spaceAfter=2,leading=16)
body=S('b',fontSize=9.8,textColor=TEXT,leading=14,alignment=TA_JUSTIFY,spaceAfter=6)
bull=S('bu',fontSize=9.6,textColor=TEXT,leading=13.2,leftIndent=13,firstLineIndent=-11,spaceAfter=4)
kpi_lab=S('kl',fontName='Helvetica-Bold',fontSize=7.8,textColor=white,leading=10)
kpi_big=S('kb',fontName='Helvetica-Bold',fontSize=16,textColor=white,leading=18)
kpi_sub=S('ksu',fontSize=7.2,textColor=HexColor('#E6FFFA'),leading=9)
th=S('th',fontName='Helvetica-Bold',fontSize=8.3,textColor=white,leading=10.8)
thr=S('thr',fontName='Helvetica-Bold',fontSize=8.3,textColor=white,leading=10.8,alignment=TA_RIGHT)
thc=S('thc',fontName='Helvetica-Bold',fontSize=8.3,textColor=white,leading=10.8)
td=S('td',fontSize=8.8,textColor=TEXT,leading=11.5)
tdc=S('tdc',fontSize=8.8,textColor=TEXT,leading=11.5)
tdb=S('tb',fontName='Helvetica-Bold',fontSize=9,textColor=DARK,leading=11.5)
callout=S('c',fontName='Helvetica-Oblique',fontSize=10,textColor=TEXT,leading=14.5,alignment=TA_JUSTIFY)

def bs(x): return ('Bs {:,.0f}'.format(x)).replace(',','.')

# ---- numeros
META=1535600; OPEX_A=835600; OPEX_M=69633; FONDO=348167; INV=948600; RETIRO=700000
mix=[('Mapeamento',100,0.35,0.40),('MAX PIROL',80,0.25,0.30),('Análisis de suelo',150,0.20,0.20),('On-Farm',79.79,0.15,0.10)]
FACT=sum((META*ap)/mg for _,_,mg,ap in mix); BLEND=META/FACT

def section(num,title):
    return KeepTogether([Paragraph('%s.&nbsp;&nbsp;%s'%(num,title),h1),
        HRFlowable(width='100%',thickness=2,color=LIME,lineCap='round',spaceBefore=3,spaceAfter=8)])
def kpi_row(cards):
    gut=10; nn=len(cards); cw=(CONTENT_W-gut*(nn-1))/nn; cols=[]; widths=[]
    for i,(lab,big,sub,bg) in enumerate(cards):
        if i>0: cols.append(''); widths.append(gut)
        cols.append([Paragraph(lab,kpi_lab),Spacer(1,3),Paragraph(big,kpi_big),Spacer(1,2),Paragraph(sub,kpi_sub)]); widths.append(cw)
    t=Table([cols],colWidths=widths); st=[('VALIGN',(0,0),(-1,-1),'MIDDLE')]
    for i,(lab,big,sub,bg) in enumerate(cards):
        ci=2*i; st+=[('BACKGROUND',(ci,0),(ci,0),bg),('LEFTPADDING',(ci,0),(ci,0),11),('RIGHTPADDING',(ci,0),(ci,0),11),('TOPPADDING',(ci,0),(ci,0),10),('BOTTOMPADDING',(ci,0),(ci,0),10)]
    t.setStyle(TableStyle(st)); return t
def box(items,accent=TEAL,bg=SURFACE):
    paras=[Paragraph('<font color="%s">▸</font> %s'%(TEAL_HEX,t),bull) for t in items]
    t=Table([[paras]],colWidths=[CONTENT_W])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),bg),('BOX',(0,0),(-1,-1),0.8,BORDER),('LINEBEFORE',(0,0),(0,-1),3,accent),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(0,0),(-1,-1),12)]))
    return t
def callout_box(text,strip=TEAL,bg=TEAL_TINT):
    p=Paragraph(text,callout); t=Table([['',p]],colWidths=[6,CONTENT_W-6])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,0),strip),('BACKGROUND',(1,0),(1,0),bg),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(1,0),(1,0),14),('RIGHTPADDING',(1,0),(1,0),14),('TOPPADDING',(1,0),(1,0),11),('BOTTOMPADDING',(1,0),(1,0),11),
        ('LEFTPADDING',(0,0),(0,0),0),('RIGHTPADDING',(0,0),(0,0),0)])); return t

story=[]
story.append(Spacer(1,2))
story.append(Paragraph('PLAN ESTRATÉGICO DE GESTIÓN',eyebrow))
story.append(Paragraph('Cómo administrar y hacer crecer Pixadvisor',ctitle))
story.append(Paragraph('Administración · ventas · flujo de caja · prioridad de productos — hoja de ruta a 3 años',csub))
story.append(HRFlowable(width=130,thickness=3,color=LIME,lineCap='round',spaceBefore=8,spaceAfter=12,hAlign='LEFT'))

story.append(kpi_row([
    ('META DE MARGEN/AÑO', bs(META), 'cubre operación + retiros', TEAL),
    ('FACTURACIÓN OBJETIVO', bs(FACT), '≈ '+bs(FACT/12)+'/mes', BLUE),
    ('FONDO DE SEGURIDAD', bs(FONDO), '5 meses de operación', TEALD),
]))
story.append(Spacer(1,12))

story+= [section('1','Diagnóstico y meta')]
story.append(Paragraph('Pixadvisor sostiene hoy una estructura fija de <b>'+bs(OPEX_M)+'/mes</b> ('+bs(OPEX_A)+'/año), '
    'donde las retiradas de los socios son ~66%. La meta sostenible (Año 3+, con retiros de Bs 350.000 por socio) '
    'es generar <b>'+bs(META)+' de margen al año</b>. Como los productos dejan entre 15% y 35%, eso exige facturar '
    '~<b>'+bs(FACT)+'/año</b> (≈ '+bs(FACT/12)+'/mes) con la mezcla correcta. El orden ganador es claro: '
    '<b>1) blindar la caja, 2) invertir por etapas, 3) escalar las ventas de lo más rentable.</b>',body))
story.append(Spacer(1,4))

story+= [section('2','Administración: disciplina financiera')]
story.append(box([
    '<b>Fondo de seguridad primero:</b> juntar '+bs(FONDO)+' (5 meses) ANTES de invertir fuerte. Es el seguro ante paros, falta de combustible y saltos del dólar.',
    '<b>Sueldos fijos, cero retiros sueltos:</b> cada socio Bs 23.000/mes y nada más hasta el Año 3. La previsibilidad es la base del flujo.',
    '<b>Cierre mensual obligatorio:</b> cargar lo facturado real en el Excel, comparar contra la meta y decidir entre los dos socios. Lo que no se mide, no se gestiona.',
    '<b>Inversiones por etapas (Año 1-2):</b> primero los 2 drones (generan ingreso), después la casa y el 2º vehículo.',
    '<b>Riesgo dólar:</b> costos e inversiones están en USD. Mantené parte del fondo en dólares y cobrá al paralelo (como MAX PIROL) para no perder contra el tipo de cambio.',
]))
story.append(Spacer(1,4))

story+= [section('3','Ventas: cómo vender más y mejor')]
story.append(box([
    '<b>Mapeo = puerta de entrada:</b> es técnico, visible y de alto margen. Entrá a cada hacienda con un mapeo y abrí la relación.',
    '<b>Combo / venta cruzada:</b> mapeo → análisis de suelo → prescripción → MAX PIROL. La meta: que cada cliente compre 2-3 servicios, no uno.',
    '<b>MAX PIROL = ingreso recurrente:</b> es un consumible; construí una cartera de clientes que recompran cada campaña.',
    '<b>On-Farm = proyectos grandes puntuales:</b> apuntá a 1-2 proyectos por año (tipo Gil Aguilera) para ingresos fuertes, sin depender de ellos.',
    '<b>Enfocá haciendas grandes:</b> los servicios por hectárea escalan con el tamaño del campo — más ha por visita, mejor rentabilidad.',
    '<b>Metas mensuales claras:</b> ~1.462 ha de mapeo · 1.920 L de MAX PIROL · 853 ha de análisis · 1.069 L de On-Farm.',
],accent=BLUE,bg=BLUE_TINT))
story.append(Spacer(1,4))

story+= [section('4','Flujo de caja sano')]
story.append(box([
    '<b>Meta de facturación:</b> ~'+bs(FACT/12)+'/mes para generar el margen objetivo. Ese es el número a seguir cada mes.',
    '<b>Cobranza con anticipos:</b> pedí 30-50% por adelantado en servicios y proyectos. La mora es lo que más mata el flujo de una empresa chica.',
    '<b>Estacionalidad:</b> el agro factura por campaña; acumulá en los meses fuertes para cubrir los flojos. Para eso existe el fondo.',
    '<b>Caja siempre visible:</b> el saldo acumulado nunca debería bajar del fondo de seguridad ('+bs(FONDO)+').',
],accent=LIME,bg=LIME_TINT))
story.append(Spacer(1,6))

# 5. producto estrategico
story+= [section('5','¿Qué producto/servicio es el más estratégico?')]
story.append(Paragraph('Comparando margen, escalabilidad y recurrencia, el orden de prioridad comercial es:',body))
rows=[[Paragraph('<b>1 · Mapeamento</b>',td),Paragraph('35%',tdc),Paragraph('Alta',tdc),Paragraph('Alta',tdc),Paragraph('<b>MOTOR — puerta de entrada</b>',td)],
      [Paragraph('2 · MAX PIROL',td),Paragraph('25%',tdc),Paragraph('Alta',tdc),Paragraph('Alta',tdc),Paragraph('Ingreso recurrente / cross-sell',td)],
      [Paragraph('3 · Análisis de suelo',td),Paragraph('20%',tdc),Paragraph('Media',tdc),Paragraph('Media',tdc),Paragraph('Servicio gancho / bundle',td)],
      [Paragraph('4 · On-Farm',td),Paragraph('15%',tdc),Paragraph('Baja',tdc),Paragraph('Baja',tdc),Paragraph('Proyecto grande puntual',td)]]
hdr=[Paragraph('Producto / servicio',thc),Paragraph('Margen',thc),Paragraph('Escalab.',thc),Paragraph('Recurr.',thc),Paragraph('Rol estratégico',thc)]
t=Table([hdr]+rows,colWidths=[CONTENT_W*0.24,CONTENT_W*0.11,CONTENT_W*0.12,CONTENT_W*0.12,CONTENT_W*0.41])
tst=[('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
     ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,1),(-1,-1),0.4,BORDER),('BOX',(0,0),(-1,-1),0.7,BORDER),
     ('ALIGN',(1,1),(3,-1),'CENTER'),('BACKGROUND',(0,1),(-1,1),LIME_TINT)]
for ri in range(2,5):
    if ri%2==0: tst.append(('BACKGROUND',(0,ri),(-1,ri),SURFACE))
t.setStyle(TableStyle(tst))
story.append(KeepTogether([t]))
story.append(Spacer(1,8))
story.append(callout_box('<b>Conclusión:</b> concentrá la energía comercial en MAPEAMENTO + MAX PIROL — juntos ~70% de las ventas. '
    'Son los que más margen dejan por esfuerzo y se sostienen solos. El análisis de suelo es el gancho para entrar, '
    'y On-Farm el "golpe grande" ocasional. Vender mucho On-Farm (margen 15%) obliga a facturar el doble para el mismo resultado.'))
story.append(Spacer(1,6))

# 6. hoja de ruta
story+= [section('6','Hoja de ruta a 3 años')]
rmap_h=[Paragraph('',thc),Paragraph('AÑO 1 — Blindar',thc),Paragraph('AÑO 2 — Escalar',thc),Paragraph('AÑO 3+ — Consolidar',thc)]
rmap=[[Paragraph('<b>Foco</b>',td),Paragraph('Caja segura + arrancar ventas',td),Paragraph('Cartera recurrente + completar activos',td),Paragraph('Régimen objetivo',td)],
      [Paragraph('<b>Inversión</b>',td),Paragraph('2 drones + 1 camioneta (Bs 531.000)',td),Paragraph('Casa + 2ª camioneta (Bs 417.600)',td),Paragraph('—',td)],
      [Paragraph('<b>Caja</b>',td),Paragraph('Constituir fondo Bs 348.167',td),Paragraph('Mantener el fondo',td),Paragraph('Retiros Bs 350.000/socio',td)],
      [Paragraph('<b>Comercial</b>',td),Paragraph('Empujar mapeo + MAX PIROL',td),Paragraph('Subir volumen y clientes fijos',td),Paragraph('Mezcla 40/30/20/10',td)]]
t2=Table([rmap_h]+rmap,colWidths=[CONTENT_W*0.13,CONTENT_W*0.29,CONTENT_W*0.29,CONTENT_W*0.29])
t2st=[('BACKGROUND',(0,0),(-1,0),TEALD),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
      ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,1),(-1,-1),0.4,BORDER),('BOX',(0,0),(-1,-1),0.7,BORDER),
      ('BACKGROUND',(0,1),(0,-1),TEAL_TINT)]
for ri in range(1,5):
    if ri%2==0: t2st.append(('BACKGROUND',(1,ri),(-1,ri),SURFACE))
t2.setStyle(TableStyle(t2st))
story.append(KeepTogether([t2]))
story.append(Spacer(1,8))

# 7. KPIs
story+= [section('7','Indicadores a vigilar cada mes')]
story.append(box([
    'Facturación del mes vs meta (~'+bs(FACT/12)+').',
    'Margen del mes vs ~'+bs(META/12)+' (lo que debe quedar después de costos directos).',
    'Saldo de caja vs fondo objetivo ('+bs(FONDO)+') — nunca por debajo.',
    'Hectáreas mapeadas y litros de MAX PIROL vendidos (los dos motores).',
    '% cobrado vs facturado (salud de la cobranza).',
    'Mezcla de ventas: ¿mapeo + MAX PIROL ≥ 70%?',
]))
story.append(Spacer(1,8))
story.append(callout_box('En una frase: <b>caja blindada, sueldos fijos, foco en mapeo y MAX PIROL, y cierre financiero todos los meses.</b> '
    'Con eso Pixadvisor pasa de "sobrevivir" a crecer con previsibilidad.',strip=LIME,bg=LIME_TINT))

doc=SimpleDocTemplate(OUT,pagesize=letter,leftMargin=LM,rightMargin=RM,topMargin=TM,bottomMargin=BM,
    title='Plan Estratégico de Gestión — Pixadvisor',author='Pixadvisor — Agricultura de Precisión',
    subject='Administración, ventas, flujo de caja y prioridad de productos')
doc.build(story,onFirstPage=header_footer,onLaterPages=header_footer)
print('OK ->',OUT,'|',os.path.getsize(OUT),'bytes | factura',bs(FACT),'blend','{:.1f}%'.format(BLEND*100))
