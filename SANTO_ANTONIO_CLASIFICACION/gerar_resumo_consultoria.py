# -*- coding: utf-8 -*-
"""
RESUMO DA CONSULTORIA — Safra 2025/2026
Versão simplificada em linguagem direta para a CONTRATANTE.
Branding: Pixadvisor.
"""
import pathlib, shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether
)

HERE = pathlib.Path(__file__).parent
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)
LOGO = pathlib.Path(r"D:\PIXADVISOR_AGENT_WORKSPACE\pix-admin\img\LOGO-PIX.png")
PDF = OUT / "Resumo_Consultoria_Simples_Safra_2025-2026.pdf"

# ===== CORES PIXADVISOR =====
TEAL      = HexColor("#7FD633")
TEAL_DARK = HexColor("#6BBF2A")
BLUE      = HexColor("#00A4CC")
DARK      = HexColor("#0F1B2D")
GRAY_LT   = HexColor("#F1F5F9")
GRAY_MD   = HexColor("#CBD5E1")
GRAY_TXT  = HexColor("#334155")
RED_SOFT  = HexColor("#DC2626")
WHITE     = colors.white

# ===== DADOS =====
PRECO_SOJA  = 111.00
PRECO_MILHO = 52.00
ALQ_SOJA    = 73.58
ALQ_MILHO   = 21.64
SC_SOJA_ALQ  = 4   # 3 base + 1 bônus
SC_MILHO_ALQ = 5   # 4 base + 1 bônus
SACAS_SOJA   = ALQ_SOJA  * SC_SOJA_ALQ
SACAS_MILHO  = ALQ_MILHO * SC_MILHO_ALQ
REM_SOJA     = SACAS_SOJA  * PRECO_SOJA
REM_MILHO    = SACAS_MILHO * PRECO_MILHO
REM_TOTAL    = REM_SOJA + REM_MILHO
ADIANT       = 2000.00
SALDO        = REM_TOTAL - ADIANT

def brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

# ===== ESTILOS =====
styles = getSampleStyleSheet()
s_title = ParagraphStyle("t", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=18, textColor=WHITE, alignment=TA_CENTER, leading=22)
s_sub = ParagraphStyle("s", parent=styles["Normal"], fontName="Helvetica",
    fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14)
s_h1 = ParagraphStyle("h1", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=13, textColor=DARK, alignment=TA_LEFT, leading=16,
    spaceBefore=8, spaceAfter=4)
s_body = ParagraphStyle("b", parent=styles["Normal"], fontName="Helvetica",
    fontSize=11, textColor=GRAY_TXT, alignment=TA_JUSTIFY, leading=14.5,
    spaceAfter=4)
s_body_c = ParagraphStyle("bc", parent=s_body, alignment=TA_CENTER)
s_th = ParagraphStyle("th", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=10, textColor=WHITE, alignment=TA_CENTER, leading=13)
s_td = ParagraphStyle("td", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.5, textColor=DARK, alignment=TA_CENTER, leading=13)
s_td_b = ParagraphStyle("tdb", parent=s_td, fontName="Helvetica-Bold")
s_td_l = ParagraphStyle("tdl", parent=s_td, alignment=TA_LEFT)
s_huge = ParagraphStyle("hg", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=34, textColor=TEAL_DARK, alignment=TA_CENTER, leading=38)
s_med = ParagraphStyle("md", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=16, textColor=DARK, alignment=TA_CENTER, leading=20)

# ===== HEADER / FOOTER =====
def hdr_ftr(canv, doc):
    canv.saveState()
    W, H = A4
    bar_h = 24*mm
    canv.setFillColor(DARK); canv.rect(0, H-bar_h, W, bar_h, stroke=0, fill=1)
    for i in range(60):
        r = 127/255 + (0 - 127/255) * (i/60)
        g = 214/255 + (164/255 - 214/255) * (i/60)
        b = 51/255  + (204/255 - 51/255) * (i/60)
        canv.setFillColorRGB(r, g, b)
        canv.rect((i/60)*W, H-bar_h-2*mm, W/60+0.5, 2*mm, stroke=0, fill=1)
    canv.setFillColor(WHITE)
    canv.roundRect(8*mm, H-bar_h+2*mm, 40*mm, 20*mm, 2*mm, stroke=0, fill=1)
    if LOGO.exists():
        canv.drawImage(str(LOGO), 9*mm, H-bar_h+3*mm, width=38*mm, height=18*mm,
                       preserveAspectRatio=True, mask='auto')
    canv.setFillColor(WHITE); canv.setFont("Helvetica-Bold", 11)
    canv.drawRightString(W-10*mm, H-10*mm, "PIXADVISOR")
    canv.setFillColor(TEAL); canv.setFont("Helvetica", 8)
    canv.drawRightString(W-10*mm, H-14*mm, "Agricultura de Precisão")
    canv.setFillColor(GRAY_MD); canv.setFont("Helvetica", 7.5)
    canv.drawRightString(W-10*mm, H-18*mm, "Engenharia Agronômica  |  Consultoria Técnica")

    canv.setFillColor(DARK); canv.rect(0, 0, W, 12*mm, stroke=0, fill=1)
    canv.setFillColor(TEAL); canv.rect(0, 12*mm, W, 1.5*mm, stroke=0, fill=1)
    canv.setFillColor(WHITE); canv.setFont("Helvetica", 8)
    canv.drawString(10*mm, 6.5*mm, "Nilton Luiz Camargo — Engenheiro Agrônomo")
    canv.drawString(10*mm, 3*mm, "Ibiporã / PR — Brasil")
    canv.drawRightString(W-10*mm, 6.5*mm, "Resumo da Consultoria — Safra 2025/2026")
    canv.drawRightString(W-10*mm, 3*mm, f"Página {canv.getPageNumber()}")
    canv.restoreState()

doc = BaseDocTemplate(str(PDF), pagesize=A4,
    leftMargin=15*mm, rightMargin=15*mm, topMargin=27*mm, bottomMargin=14*mm,
    title="Resumo da Consultoria - Safra 2025/2026",
    author="Pixadvisor / Nilton Luiz Camargo")
doc.addPageTemplates(PageTemplate(id="m",
    frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  showBoundary=0)], onPage=hdr_ftr))

story = []

# TÍTULO
ttl = Table([[Paragraph(
    "<b>RESUMO DA CONSULTORIA</b><br/>"
    "<font size=13>Safra 2025/2026</font>", s_title)]], colWidths=[doc.width])
ttl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK),
    ("TOPPADDING",(0,0),(-1,-1),12), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
story.append(ttl)

sub = Table([[Paragraph(
    "Sra. Sônia Maria Bigati &nbsp;|&nbsp; Faz. Santo Antônio + Faz. São Francisco",
    s_sub)]], colWidths=[doc.width])
sub.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),TEAL_DARK),
    ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7)]))
story.append(sub)
story.append(Spacer(1, 7*mm))

# DESTAQUE GRANDE: SALDO A PAGAR
dest_data = [
    [Paragraph("<b>VALOR A RECEBER NESTA SAFRA</b>", s_th)],
    [Paragraph(f"<b>{brl(SALDO)}</b>", s_huge)],
    [Paragraph("(já descontado o adiantamento de R$ 2.000,00 recebido em 19/01/2026)",
               ParagraphStyle("sm",parent=s_body_c,fontSize=9,textColor=GRAY_TXT))],
]
t_dest = Table(dest_data, colWidths=[doc.width])
t_dest.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), TEAL_DARK),
    ("BACKGROUND", (0,1), (-1,2), HexColor("#E8F5DC")),
    ("BOX", (0,0), (-1,-1), 1.5, TEAL_DARK),
    ("TOPPADDING", (0,0), (-1,0), 6),
    ("BOTTOMPADDING", (0,0), (-1,0), 6),
    ("TOPPADDING", (0,1), (-1,1), 12),
    ("BOTTOMPADDING", (0,1), (-1,1), 6),
    ("TOPPADDING", (0,2), (-1,2), 0),
    ("BOTTOMPADDING", (0,2), (-1,2), 10),
]))
story.append(t_dest)
story.append(Spacer(1, 7*mm))

# COMO CALCULAMOS
story.append(Paragraph("COMO CHEGAMOS A ESSE VALOR", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))
story.append(Paragraph(
    "O pagamento da consultoria é combinado em <b>sacas</b> por alqueire, "
    "e cada saca é contada pelo preço do dia. Nesta safra os rendimentos "
    "passaram dos limites combinados, então entrou o <b>bônus de produtividade</b> "
    "(+1 saca por alqueire).",
    s_body))

calc_data = [
    [Paragraph("<b>LAVOURA</b>", s_th),
     Paragraph("<b>ÁREA</b>", s_th),
     Paragraph("<b>SACAS POR ALQ.</b><br/><font size=7>(com bônus)</font>", s_th),
     Paragraph("<b>SACAS TOTAIS</b>", s_th),
     Paragraph("<b>PREÇO/ SACA</b>", s_th),
     Paragraph("<b>VALOR</b>", s_th)],
    [Paragraph("<b>Soja</b>", s_td_b),
     Paragraph(f"{ALQ_SOJA:.2f} alq".replace(".",","), s_td),
     Paragraph(f"{SC_SOJA_ALQ} sc", s_td_b),
     Paragraph(f"{SACAS_SOJA:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_td_b),
     Paragraph(f"R$ {PRECO_SOJA:.2f}".replace(".",","), s_td),
     Paragraph(f"<b>{brl(REM_SOJA)}</b>", s_td_b)],
    [Paragraph("<b>Milho</b>", s_td_b),
     Paragraph(f"{ALQ_MILHO:.2f} alq".replace(".",","), s_td),
     Paragraph(f"{SC_MILHO_ALQ} sc", s_td_b),
     Paragraph(f"{SACAS_MILHO:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_td_b),
     Paragraph(f"R$ {PRECO_MILHO:.2f}".replace(".",","), s_td),
     Paragraph(f"<b>{brl(REM_MILHO)}</b>", s_td_b)],
    [Paragraph("<b>TOTAL</b>", s_td_b),
     Paragraph(f"<b>{ALQ_SOJA+ALQ_MILHO:.2f} alq</b>".replace(".",","), s_td_b),
     Paragraph("—", s_td),
     Paragraph(f"<b>{SACAS_SOJA+SACAS_MILHO:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_td_b),
     Paragraph("—", s_td),
     Paragraph(f"<b>{brl(REM_TOTAL)}</b>", s_td_b)],
]
t_calc = Table(calc_data, colWidths=[
    doc.width*0.13, doc.width*0.14, doc.width*0.19,
    doc.width*0.17, doc.width*0.15, doc.width*0.22])
t_calc.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), TEAL),
    ("TEXTCOLOR", (0,-1), (-1,-1), WHITE),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.6, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
]))
story.append(t_calc)
story.append(Spacer(1, 5*mm))

# SALDO FINAL — LINHA SIMPLES
saldo_lines = [
    [Paragraph("Total da consultoria (bruto)", s_td_l),
     Paragraph(f"<b>{brl(REM_TOTAL)}</b>", s_td_b)],
    [Paragraph("(−) Adiantamento recebido em 19/01/2026", s_td_l),
     Paragraph(f"<b>− {brl(ADIANT)}</b>",
               ParagraphStyle("rr",parent=s_td_b,textColor=RED_SOFT))],
    [Paragraph("<b>(=) VALOR FINAL A PAGAR</b>", s_td_l),
     Paragraph(f"<b>{brl(SALDO)}</b>",
               ParagraphStyle("gg",parent=s_td_b,textColor=WHITE,fontSize=12))],
]
t_saldo = Table(saldo_lines, colWidths=[doc.width*0.68, doc.width*0.32])
t_saldo.setStyle(TableStyle([
    ("BACKGROUND", (0,-1), (-1,-1), TEAL_DARK),
    ("ROWBACKGROUNDS", (0,0), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.6, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (0,-1), 10),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]))
story.append(t_saldo)
story.append(Spacer(1, 7*mm))

# DADOS BANCÁRIOS
story.append(Paragraph("PARA O PAGAMENTO", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))
banco_data = [
    [Paragraph("<b>Titular</b>", s_td_l),
     Paragraph("Nilton Luiz Camargo (CPF 869.321.959-68)", s_td_l)],
    [Paragraph("<b>Banco</b>", s_td_l),
     Paragraph("Banco do Brasil", s_td_l)],
    [Paragraph("<b>Agência / Conta</b>", s_td_l),
     Paragraph("2110-5 / 31842-6", s_td_l)],
    [Paragraph("<b>Praça</b>", s_td_l),
     Paragraph("Ibiporã / PR", s_td_l)],
]
t_banco = Table(banco_data, colWidths=[doc.width*0.28, doc.width*0.72])
t_banco.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,-1), GRAY_LT),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (-1,-1), 10),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(t_banco)
story.append(Spacer(1, 5*mm))

# OBSERVAÇÃO IMPORTANTE
story.append(Paragraph(
    "<b>Observação importante:</b> o valor acima foi calculado com o preço "
    "oficial SIMA-PR de 22/04/2026 (soja R$ 111,00 / milho R$ 52,00). "
    "No momento da venda de cada lavoura, o valor é recalculado pelo "
    "<b>preço do dia</b>, conforme combinado na Cláusula V do contrato.",
    s_body))

story.append(Spacer(1, 10*mm))

# ASSINATURAS
sig_data = [
    [Paragraph("_______________________________________", s_td),
     Paragraph("_______________________________________", s_td)],
    [Paragraph("<b>Sônia Maria Bigati</b><br/>CONTRATANTE", s_td),
     Paragraph("<b>Nilton Luiz Camargo</b><br/>CONTRATADA", s_td)],
]
t_sig = Table(sig_data, colWidths=[doc.width/2, doc.width/2])
t_sig.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
    ("TOPPADDING",(0,0),(-1,-1),3), ("BOTTOMPADDING",(0,0),(-1,-1),3)]))
story.append(t_sig)

# BUILD
doc.build(story)
print(f"OK -> {PDF}")
print(f"     tamanho: {PDF.stat().st_size/1024:.1f} KB")

dest = pathlib.Path.home() / "Desktop" / PDF.name
shutil.copy(PDF, dest)
print(f"     copiado -> {dest}")
