# -*- coding: utf-8 -*-
"""
pix_branding.py — Sistema de marca Pixadvisor para PDFs ejecutivos (ReportLab).
Reutilizable: portada hero con logo, encabezado/pie de marca, TOC con paginacion
automatica, resumen ejecutivo con tarjetas KPI, secciones numeradas con insignia,
tablas de marca. Usa Helvetica (soporta acentos y ñ vía WinAnsi).

USO MINIMO:
    from pix_branding import *
    B = Brand(logo="assets/logo_pix_azulnegro_trim.png")
    story = []
    story += B.cover_filler()                       # deja hueco para el hero
    story += [B.P("Ficha tecnica","H1"), B.hr()]
    ... contenido ...
    story += [B.sec(1,"Contexto")]                  # encabezado con insignia -> entra al TOC
    story += [B.kpi_strip([("2","cultivares"),("9","parcelas")])]
    B.build("salida.pdf", story,
            cover_title="Titulo", cover_subtitle="Subtitulo")

Acentos: escribi el texto CON acentos directamente, o corre scripts/fix_ortografia.py
sobre tu script para acentuar automaticamente (solo dentro de literales de cadena).
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable, Image)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------- Paleta de marca Pixadvisor (del logo real) ----------------
AZUL     = HexColor("#1E40AF")   # wordmark "PIX"
AZUL_D   = HexColor("#152C7A")   # azul profundo (hero)
TEAL     = HexColor("#0D9488")   # teal marca
CIAN     = HexColor("#22B7D6")
LIMA     = HexColor("#7FD633")   # lima acento
LIMA_D   = HexColor("#5DBB2E")
LIMA_PALE= HexColor("#EAFBD9")
GRIS     = HexColor("#333333")
GRIS_CLR = HexColor("#F5F7FA")
GRIS_MED = HexColor("#DCE3EA")
TEAL_BG  = HexColor("#EAF6F4")   # bandas de fila
AMBAR    = HexColor("#B8860B")

class Brand:
    """Fabrica de estilos, flowables y plantillas de pagina con la identidad Pixadvisor."""
    def __init__(self, logo, logo_ar=2.94, content_w=15.0*cm,
                 footer_left="PIXADVISOR  ·  Agricultura de Precisión",
                 footer_center="Documento técnico", footer_right_fmt="Pág. %d",
                 hero_h=9.6*cm):
        # hero_h: alto del degradado de portada. El default 9,6 cm es el de siempre y no
        # cambia ningun documento existente. Se baja a ~7,4 cm en documentos de UNA
        # CARILLA, donde el hero se llevaba 2,5 cm de degradado vacio bajo el subtitulo
        # que hacian desbordar el cierre a una segunda pagina.
        self.HERO_H = hero_h
        self.logo = logo; self.logo_ar = logo_ar; self.CONTENT_W = content_w
        self.footer_left = footer_left; self.footer_center = footer_center
        self.footer_right_fmt = footer_right_fmt
        self.ss = getSampleStyleSheet()
        self._styles()

    def _st(self, name, **kw):
        base = kw.pop("parent", self.ss["Normal"])
        self.ss.add(ParagraphStyle(name, parent=base, **kw))

    def _styles(self):
        S=self._st
        S("H1", fontSize=15, textColor=AZUL, fontName="Helvetica-Bold", spaceBefore=15, spaceAfter=7, leading=18)
        S("H2", fontSize=11.5, textColor=TEAL, fontName="Helvetica-Bold", spaceBefore=9, spaceAfter=4)
        S("Body", fontSize=10, textColor=GRIS, alignment=TA_JUSTIFY, leading=14.5, spaceAfter=5)
        S("Bull", fontSize=10, textColor=GRIS, leading=14, leftIndent=14, spaceAfter=2.5, bulletIndent=4)
        S("Cell", fontSize=9, textColor=GRIS, leading=12)
        S("CellB", fontSize=9, textColor=white, leading=12, fontName="Helvetica-Bold")
        S("CellBold", fontSize=9, textColor=GRIS, leading=12, fontName="Helvetica-Bold")
        S("CellKey", fontSize=9.5, textColor=TEAL, leading=12.5, fontName="Helvetica-Bold")
        S("Note", fontSize=8.5, textColor=HexColor("#555555"), leading=12, alignment=TA_JUSTIFY)
        S("Reco", fontSize=10, textColor=white, alignment=TA_JUSTIFY, leading=14.5)
        S("SecNum", fontSize=15, textColor=white, fontName="Helvetica-Bold", alignment=TA_CENTER, leading=17)
        S("SecTitle", fontSize=15, textColor=AZUL, fontName="Helvetica-Bold", leading=18)

    # ---- helpers de contenido ----
    def P(self, t, s="Body"): return Paragraph(t, self.ss[s])
    def hr(self, c=LIMA, w=2.0):
        return HRFlowable(width="100%", thickness=w, color=c, spaceBefore=2, spaceAfter=8)

    def sec(self, num, title):
        """Encabezado de seccion: insignia teal + numero blanco + titulo azul + regla lima. Entra al TOC."""
        head = Table([[self.P(str(num),"SecNum"), self.P(title,"SecTitle")]],
                     colWidths=[0.95*cm, self.CONTENT_W-0.95*cm])
        head.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(0,0),TEAL), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("ALIGN",(0,0),(0,0),"CENTER"),
            ("LEFTPADDING",(0,0),(0,0),0),("RIGHTPADDING",(0,0),(0,0),0),("LEFTPADDING",(1,0),(1,0),10),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LINEBELOW",(0,0),(-1,-1),2,LIMA),
        ]))
        head._toc = "%d.  %s" % (num, title)
        head.spaceBefore = 14; head.spaceAfter = 8
        return head

    def kpi_strip(self, cards):
        """cards: [(numero_grande, etiqueta_html), ...] -> tira de tarjetas KPI."""
        cells=[self.P("<font size=19 color='#1E40AF'><b>%s</b></font><br/>"
                      "<font size=8 color='#555555'>%s</font>"%(n,lab),"Cell") for n,lab in cards]
        w=self.CONTENT_W/len(cards)
        t=Table([cells], colWidths=[w]*len(cards))
        sty=[("BACKGROUND",(0,0),(-1,-1),GRIS_CLR),("LINEABOVE",(0,0),(-1,0),3,LIMA),
             ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),9),("BOTTOMPADDING",(0,0),(-1,-1),10),
             ("LEFTPADDING",(0,0),(-1,-1),10),("RIGHTPADDING",(0,0),(-1,-1),8)]
        for i in range(1,len(cards)): sty.append(("LINEBEFORE",(i,0),(i,0),3,white))
        t.setStyle(TableStyle(sty)); return t

    def tbl(self, data, widths, header=True, aligns=None):
        """Tabla de marca: cabecera teal + subrayado lima + filas alternadas."""
        t=Table(data, colWidths=widths, repeatRows=1 if header else 0)
        cmds=[("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LINEBELOW",(0,0),(-1,-1),0.5,GRIS_MED),
              ("LINEAFTER",(0,0),(-2,-1),0.5,GRIS_MED),
              ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),
              ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]
        if header:
            cmds+=[("BACKGROUND",(0,0),(-1,0),TEAL),("LINEBELOW",(0,0),(-1,0),1.4,LIMA),
                   ("ROWBACKGROUNDS",(0,1),(-1,-1),[white, TEAL_BG])]
        if aligns:
            for col,a in aligns.items(): cmds.append(("ALIGN",(col,0),(col,-1),a))
        t.setStyle(TableStyle(cmds)); return t

    def callout(self, label, text, label_style="CellB", text_style="Reco", bg=TEAL):
        """Recuadro destacado (p. ej. recomendacion): barra lima + fondo teal + texto blanco."""
        c=Table([[self.P(label,label_style), self.P(text,text_style)]], colWidths=[3.5*cm, self.CONTENT_W-3.5*cm])
        c.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),bg),("LINEBEFORE",(0,0),(0,0),4,LIMA),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),11),("BOTTOMPADDING",(0,0),(-1,-1),11),
            ("LEFTPADDING",(0,0),(-1,-1),11),("RIGHTPADDING",(0,0),(-1,-1),11)])); return c

    def meta_table(self, rows):
        """Ficha clave/valor: claves teal, barra lima, filas alternadas."""
        mt=Table([[self.P(k,"CellKey"), self.P(v,"Cell")] for k,v in rows], colWidths=[4.4*cm, self.CONTENT_W-4.4*cm])
        mt.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),TEAL_BG),
            ("ROWBACKGROUNDS",(1,0),(1,-1),[white, GRIS_CLR]),("LINEBEFORE",(0,0),(0,-1),3,LIMA),
            ("LINEBELOW",(0,0),(-1,-1),0.5,GRIS_MED),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("LEFTPADDING",(0,0),(-1,-1),9)]))
        return mt

    def toc(self):
        t=TableOfContents()
        t.levelStyles=[ParagraphStyle("TL0", fontName="Helvetica-Bold", fontSize=11,
                                      textColor=GRIS, leading=21, spaceAfter=4)]
        return t

    def cover_filler(self, h=None):
        """Hueco superior en la 1a pagina para que el contenido caiga bajo el hero.

        Por defecto se calcula del alto real del hero (menos el margen superior de
        2,4 cm, mas un respiro), asi no hay que recordar dos numeros que deben coincidir.
        """
        if h is None:
            h = max(0.0, self.HERO_H - 2.4*cm + 0.7*cm)
        return [Spacer(1, h)]

    # ---- plantillas de pagina (canvas) ----
    def _footer(self, c, doc):
        c.saveState()
        c.setFillColor(AZUL_D); c.rect(0,0,A4[0],0.85*cm,fill=1,stroke=0)
        c.setFillColor(LIMA);   c.rect(0,0.85*cm,A4[0],0.09*cm,fill=1,stroke=0)
        c.setFont("Helvetica-Bold",7.5); c.setFillColor(white)
        c.drawString(2*cm,0.31*cm,self.footer_left)
        c.setFont("Helvetica",7.5)
        c.drawCentredString(A4[0]/2,0.31*cm,self.footer_center)
        c.drawRightString(A4[0]-2*cm,0.31*cm,self.footer_right_fmt % doc.page)
        c.restoreState()

    def _later(self, c, doc):
        c.saveState()
        lw=2.9*cm; lh=lw/self.logo_ar
        c.drawImage(self.logo,2*cm,A4[1]-1.5*cm,width=lw,height=lh,mask='auto')
        c.setStrokeColor(TEAL); c.setLineWidth(1.3); c.line(2*cm,A4[1]-1.62*cm,A4[0]-2*cm,A4[1]-1.62*cm)
        c.setStrokeColor(LIMA); c.setLineWidth(1.3); c.line(A4[0]-2*cm-4*cm,A4[1]-1.62*cm,A4[0]-2*cm,A4[1]-1.62*cm)
        c.restoreState(); self._footer(c,doc)

    def _first(self, c, doc):
        HEROH=self.HERO_H
        c.saveState()
        p=c.beginPath(); p.rect(0,A4[1]-HEROH,A4[0],HEROH); c.clipPath(p,stroke=0,fill=0)
        c.linearGradient(0,A4[1]-HEROH,A4[0],A4[1],(AZUL_D,TEAL,LIMA_D),positions=(0.0,0.55,1.0),extend=True)
        c.restoreState()
        c.saveState(); c.setFillColor(LIMA); c.rect(0,A4[1]-HEROH-0.13*cm,A4[0],0.13*cm,fill=1,stroke=0); c.restoreState()
        cw,ch=10.2*cm,3.3*cm; cardx=(A4[0]-cw)/2
        cardy=A4[1]-max(1.1*cm, (HEROH-ch-2.6*cm)/2)-ch
        c.saveState(); c.setFillColor(white); c.roundRect(cardx,cardy,cw,ch,11,fill=1,stroke=0)
        lw=8.0*cm; lh=lw/self.logo_ar; c.drawImage(self.logo,(A4[0]-lw)/2,cardy+(ch-lh)/2,width=lw,height=lh,mask='auto')
        c.restoreState()
        c.saveState(); c.setFillColor(white); c.setFont("Helvetica-Bold",21)
        ty=cardy-1.15*cm
        c.drawCentredString(A4[0]/2,ty,self._ct)
        c.setFont("Helvetica-Bold",12.5); c.setFillColor(LIMA_PALE)
        c.drawCentredString(A4[0]/2,ty-0.78*cm,self._cs)
        c.restoreState(); self._footer(c,doc)

    def build(self, out, story, cover_title="", cover_subtitle="",
              topMargin=2.4*cm, bottomMargin=1.9*cm, author="Pixadvisor Agricultura de Precision", title=None):
        """Compila el PDF (doble pasada para resolver el TOC)."""
        self._ct=cover_title; self._cs=cover_subtitle
        brand=self
        class DocT(SimpleDocTemplate):
            def afterFlowable(self, flowable):
                t=getattr(flowable,"_toc",None)
                if t: self.notify("TOCEntry",(0,t,self.page))
        doc=DocT(out, pagesize=A4, topMargin=topMargin, bottomMargin=bottomMargin,
                 leftMargin=2*cm, rightMargin=2*cm, title=title or cover_title, author=author)
        doc.multiBuild(story, onFirstPage=self._first, onLaterPages=self._later)
        return out
