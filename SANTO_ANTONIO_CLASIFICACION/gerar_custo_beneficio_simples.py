# -*- coding: utf-8 -*-
"""
CUSTO x BENEFÍCIO DA SAFRA — Linguagem simples para o produtor.
Safra 2025/2026 — Sra. Sônia Maria Bigati.
Branding: Pixadvisor.
"""
import pathlib, shutil
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether
)

HERE = pathlib.Path(__file__).parent
OUT = HERE / "output"
LOGO = pathlib.Path(r"D:\PIXADVISOR_AGENT_WORKSPACE\pix-admin\img\LOGO-PIX.png")
PDF = OUT / "Custo_Beneficio_Simples_Safra_2025-2026.pdf"

# ===== CORES =====
TEAL      = HexColor("#7FD633")
TEAL_DARK = HexColor("#6BBF2A")
BLUE      = HexColor("#00A4CC")
DARK      = HexColor("#0F1B2D")
GRAY_LT   = HexColor("#F1F5F9")
GRAY_MD   = HexColor("#CBD5E1")
GRAY_TXT  = HexColor("#334155")
RED_SOFT  = HexColor("#DC2626")
AMBER     = HexColor("#F59E0B")
WHITE     = colors.white

# ===== DADOS =====
PRECO_SOJA, PRECO_MILHO = 111.00, 52.00
ALQ_SOJA, ALQ_MILHO     = 73.58, 21.64
REND_SOJA, REND_MILHO   = 178, 478            # sc/alq
CUSTO_SOJA_ALQ          = 110                 # sc/alq
CUSTO_MILHO_ALQ         = 220                 # sc/alq
SC_PAGO_SOJA, SC_PAGO_MILHO = 4, 5            # sacas/alq ao consultor (c/ bônus)

# Produção (sacas e R$)
SC_PROD_SOJA   = ALQ_SOJA  * REND_SOJA
SC_PROD_MILHO  = ALQ_MILHO * REND_MILHO
R_SOJA   = SC_PROD_SOJA  * PRECO_SOJA
R_MILHO  = SC_PROD_MILHO * PRECO_MILHO
RECEITA_TOTAL = R_SOJA + R_MILHO

# Custo estimado
CUSTO_SC_SOJA  = ALQ_SOJA  * CUSTO_SOJA_ALQ
CUSTO_SC_MILHO = ALQ_MILHO * CUSTO_MILHO_ALQ
CUSTO_SOJA   = CUSTO_SC_SOJA  * PRECO_SOJA
CUSTO_MILHO  = CUSTO_SC_MILHO * PRECO_MILHO
CUSTO_TOTAL  = CUSTO_SOJA + CUSTO_MILHO

# Sobra após custos (margem bruta)
SOBRA_SOJA   = R_SOJA  - CUSTO_SOJA
SOBRA_MILHO  = R_MILHO - CUSTO_MILHO
SOBRA_TOTAL  = SOBRA_SOJA + SOBRA_MILHO

# Consultoria
CONS_SOJA    = ALQ_SOJA  * SC_PAGO_SOJA  * PRECO_SOJA
CONS_MILHO   = ALQ_MILHO * SC_PAGO_MILHO * PRECO_MILHO
CONS_TOTAL   = CONS_SOJA + CONS_MILHO

# Lucro final (após consultoria)
LUCRO_TOTAL  = SOBRA_TOTAL - CONS_TOTAL

# % consultoria sobre total
PCT_CONS_RECEITA = CONS_TOTAL / RECEITA_TOTAL * 100

# Receita extra pelo bônus (produtividade acima do limiar)
EXTRA_SOJA  = (REND_SOJA  - 160) * ALQ_SOJA  * PRECO_SOJA
EXTRA_MILHO = (REND_MILHO - 460) * ALQ_MILHO * PRECO_MILHO
EXTRA_TOTAL = EXTRA_SOJA + EXTRA_MILHO
VEZES_PAGOU = EXTRA_TOTAL / CONS_TOTAL

def brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def brl0(v):
    return f"R$ {v:,.0f}".replace(",",".")

# ===== ESTILOS =====
styles = getSampleStyleSheet()
s_title = ParagraphStyle("t", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=18, textColor=WHITE, alignment=TA_CENTER, leading=22)
s_sub = ParagraphStyle("s", parent=styles["Normal"], fontName="Helvetica",
    fontSize=11, textColor=WHITE, alignment=TA_CENTER, leading=14)
s_h1 = ParagraphStyle("h1", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=13, textColor=DARK, alignment=TA_LEFT, leading=16,
    spaceBefore=6, spaceAfter=3)
s_body = ParagraphStyle("b", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10.5, textColor=GRAY_TXT, alignment=TA_JUSTIFY, leading=14,
    spaceAfter=3)
s_body_c = ParagraphStyle("bc", parent=s_body, alignment=TA_CENTER)
s_th = ParagraphStyle("th", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=9.5, textColor=WHITE, alignment=TA_CENTER, leading=12)
s_td = ParagraphStyle("td", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=DARK, alignment=TA_CENTER, leading=12.5)
s_td_b = ParagraphStyle("tdb", parent=s_td, fontName="Helvetica-Bold")
s_td_l = ParagraphStyle("tdl", parent=s_td, alignment=TA_LEFT)
s_card_ttl = ParagraphStyle("ct", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=10, textColor=WHITE, alignment=TA_CENTER, leading=13)
s_card_num = ParagraphStyle("cn", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=22, textColor=DARK, alignment=TA_CENTER, leading=26)
s_card_sub = ParagraphStyle("cs", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.5, textColor=GRAY_TXT, alignment=TA_CENTER, leading=11)
s_huge = ParagraphStyle("hg", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=30, textColor=TEAL_DARK, alignment=TA_CENTER, leading=34)

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
    canv.drawRightString(W-10*mm, 6.5*mm, "Custo x Benefício — Safra 2025/2026")
    canv.drawRightString(W-10*mm, 3*mm, f"Página {canv.getPageNumber()}")
    canv.restoreState()

doc = BaseDocTemplate(str(PDF), pagesize=A4,
    leftMargin=15*mm, rightMargin=15*mm, topMargin=27*mm, bottomMargin=14*mm,
    title="Custo x Beneficio - Safra 2025/2026",
    author="Pixadvisor / Nilton Luiz Camargo")
doc.addPageTemplates(PageTemplate(id="m",
    frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  showBoundary=0)], onPage=hdr_ftr))

story = []

# ===== TÍTULO =====
ttl = Table([[Paragraph(
    "<b>CUSTO x BENEFÍCIO DA SAFRA</b><br/>"
    "<font size=13>Safra 2025/2026</font>", s_title)]], colWidths=[doc.width])
ttl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK),
    ("TOPPADDING",(0,0),(-1,-1),12), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
story.append(ttl)
sub = Table([[Paragraph(
    "Sra. Sônia Maria Bigati &nbsp;|&nbsp; Faz. Santo Antônio + Faz. São Francisco &nbsp;|&nbsp; 95,22 alqueires (230,44 ha)",
    s_sub)]], colWidths=[doc.width])
sub.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),TEAL_DARK),
    ("TOPPADDING",(0,0),(-1,-1),7), ("BOTTOMPADDING",(0,0),(-1,-1),7)]))
story.append(sub)
story.append(Spacer(1, 6*mm))

# ===== INTRO SIMPLES =====
story.append(Paragraph(
    "Este resumo mostra, em números simples, <b>quanto a lavoura produziu, "
    "quanto custou plantar e quanto sobrou</b> nesta safra. Os valores de "
    "custo são uma <b>estimativa</b> baseada em referências da região "
    "(110 sacas/alq para soja e 220 sacas/alq para milho).",
    s_body))
story.append(Spacer(1, 5*mm))

# ===== 3 CARDS GRANDES: RECEITA / CUSTO / SOBRA =====
card_data = [
    [Paragraph("<b>VOCÊ PRODUZIU</b><br/><font size=7>(valor em R$)</font>", s_card_ttl),
     Paragraph("<b>VOCÊ GASTOU</b><br/><font size=7>(custo estimado)</font>", s_card_ttl),
     Paragraph("<b>SOBRA NO BOLSO</b><br/><font size=7>(antes da consultoria)</font>", s_card_ttl)],
    [Paragraph(f"<b>{brl0(RECEITA_TOTAL)}</b>", s_card_num),
     Paragraph(f"<b>{brl0(CUSTO_TOTAL)}</b>",
               ParagraphStyle("cx",parent=s_card_num,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl0(SOBRA_TOTAL)}</b>",
               ParagraphStyle("cy",parent=s_card_num,textColor=TEAL_DARK))],
    [Paragraph(f"{SC_PROD_SOJA+SC_PROD_MILHO:,.0f} sacas colhidas".replace(",","."),
               s_card_sub),
     Paragraph(f"plantar, tratar e colher", s_card_sub),
     Paragraph(f"receita menos custos", s_card_sub)],
]
t_cards = Table(card_data, colWidths=[doc.width/3]*3)
t_cards.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,1), (0,2), GRAY_LT),
    ("BACKGROUND", (1,1), (1,2), HexColor("#FEE2E2")),
    ("BACKGROUND", (2,1), (2,2), HexColor("#E8F5DC")),
    ("BOX", (0,0), (-1,-1), 1, TEAL_DARK),
    ("INNERGRID", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,0), 6),
    ("BOTTOMPADDING", (0,0), (-1,0), 6),
    ("TOPPADDING", (0,1), (-1,1), 10),
    ("BOTTOMPADDING", (0,1), (-1,1), 4),
    ("TOPPADDING", (0,2), (-1,2), 0),
    ("BOTTOMPADDING", (0,2), (-1,2), 8),
]))
story.append(t_cards)
story.append(Spacer(1, 6*mm))

# ===== DETALHE POR LAVOURA =====
story.append(Paragraph("DETALHE POR LAVOURA", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

det_data = [
    [Paragraph("<b>LAVOURA</b>", s_th),
     Paragraph("<b>COLHEU</b>", s_th),
     Paragraph("<b>VALOR PRODUZIDO</b>", s_th),
     Paragraph("<b>(−) CUSTO</b>", s_th),
     Paragraph("<b>(=) SOBRA</b>", s_th)],
    [Paragraph("<b>Soja</b><br/>"
               f"<font size=8>{ALQ_SOJA:.2f} alq  •  {REND_SOJA} sc/alq</font>".replace(".",","),
               s_td_b),
     Paragraph(f"{SC_PROD_SOJA:,.0f} sc".replace(",","."), s_td_b),
     Paragraph(f"<b>{brl0(R_SOJA)}</b>", s_td_b),
     Paragraph(f"− {brl0(CUSTO_SOJA)}",
               ParagraphStyle("rs",parent=s_td,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl0(SOBRA_SOJA)}</b>",
               ParagraphStyle("gs",parent=s_td_b,textColor=TEAL_DARK))],
    [Paragraph("<b>Milho</b><br/>"
               f"<font size=8>{ALQ_MILHO:.2f} alq  •  {REND_MILHO} sc/alq</font>".replace(".",","),
               s_td_b),
     Paragraph(f"{SC_PROD_MILHO:,.0f} sc".replace(",","."), s_td_b),
     Paragraph(f"<b>{brl0(R_MILHO)}</b>", s_td_b),
     Paragraph(f"− {brl0(CUSTO_MILHO)}",
               ParagraphStyle("rm",parent=s_td,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl0(SOBRA_MILHO)}</b>",
               ParagraphStyle("gm",parent=s_td_b,textColor=TEAL_DARK))],
    [Paragraph("<b>TOTAL</b>", s_td_b),
     Paragraph(f"<b>{SC_PROD_SOJA+SC_PROD_MILHO:,.0f} sc</b>".replace(",","."), s_td_b),
     Paragraph(f"<b>{brl0(RECEITA_TOTAL)}</b>", s_td_b),
     Paragraph(f"<b>− {brl0(CUSTO_TOTAL)}</b>", s_td_b),
     Paragraph(f"<b>{brl0(SOBRA_TOTAL)}</b>", s_td_b)],
]
t_det = Table(det_data, colWidths=[
    doc.width*0.22, doc.width*0.15, doc.width*0.21, doc.width*0.20, doc.width*0.22])
t_det.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), TEAL),
    ("TEXTCOLOR", (0,-1), (-1,-1), WHITE),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.6, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]))
story.append(t_det)
story.append(Spacer(1, 7*mm))

# ===== QUANTO FOI PARA CONSULTORIA =====
story.append(Paragraph("QUANTO FOI PAGO DE CONSULTORIA", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

cons_box = [
    [Paragraph(f"<b>{brl0(CONS_TOTAL)}</b>", s_huge)],
    [Paragraph(
        f"= <b>{PCT_CONS_RECEITA:.2f}%</b> do que a lavoura produziu  "
        f"&nbsp;|&nbsp;  <b>{CONS_TOTAL/SOBRA_TOTAL*100:.1f}%</b> da sobra (margem)",
        ParagraphStyle("cs1",parent=s_body_c,fontSize=11,textColor=DARK))],
]
t_cons = Table(cons_box, colWidths=[doc.width])
t_cons.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), HexColor("#E8F5DC")),
    ("BOX", (0,0), (-1,-1), 1.2, TEAL_DARK),
    ("TOPPADDING", (0,0), (-1,0), 10),
    ("BOTTOMPADDING", (0,0), (-1,0), 2),
    ("TOPPADDING", (0,1), (-1,1), 2),
    ("BOTTOMPADDING", (0,1), (-1,1), 10),
]))
story.append(t_cons)
story.append(Spacer(1, 6*mm))

# ===== A CONSULTORIA SE PAGOU (todo em KeepTogether) =====
extra_data = [
    [Paragraph("<b>Extra produzido na soja</b><br/>"
               f"<font size=8>{REND_SOJA}−160 = 18 sc/alq × {ALQ_SOJA:.2f} alq</font>".replace(".",","),
               s_td_l),
     Paragraph(f"<b>{brl0(EXTRA_SOJA)}</b>",
               ParagraphStyle("ex1",parent=s_td_b,textColor=TEAL_DARK,fontSize=12))],
    [Paragraph("<b>Extra produzido no milho</b><br/>"
               f"<font size=8>{REND_MILHO}−460 = 18 sc/alq × {ALQ_MILHO:.2f} alq</font>".replace(".",","),
               s_td_l),
     Paragraph(f"<b>{brl0(EXTRA_MILHO)}</b>",
               ParagraphStyle("ex2",parent=s_td_b,textColor=TEAL_DARK,fontSize=12))],
    [Paragraph("<b>Total produzido a mais</b>", s_td_l),
     Paragraph(f"<b>{brl0(EXTRA_TOTAL)}</b>",
               ParagraphStyle("ex3",parent=s_td_b,textColor=WHITE,fontSize=13))],
]
t_extra = Table(extra_data, colWidths=[doc.width*0.68, doc.width*0.32])
t_extra.setStyle(TableStyle([
    ("BACKGROUND", (0,-1), (-1,-1), TEAL_DARK),
    ("ROWBACKGROUNDS", (0,0), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.6, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,0), (0,-1), 10),
    ("TOPPADDING", (0,0), (-1,-1), 7),
    ("BOTTOMPADDING", (0,0), (-1,-1), 7),
]))

# Conclusão: o extra pagou várias vezes a consultoria
concl = Table([[Paragraph(
    f"<b>Esse extra ({brl0(EXTRA_TOTAL)}) é cerca de "
    f"<font color='#6BBF2A' size=16>{VEZES_PAGOU:.1f}×</font> o valor pago de consultoria "
    f"({brl0(CONS_TOTAL)}).</b><br/>"
    f"<font size=10>Em palavras simples: a produção extra obtida pagou muitas vezes "
    f"o custo da consultoria — o investimento em orientação técnica teve "
    f"<b>retorno positivo</b>.</font>",
    ParagraphStyle("con",parent=s_body_c,fontSize=11,textColor=DARK,leading=16))]],
    colWidths=[doc.width])
concl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), HexColor("#FFF4D6")),
    ("BOX", (0,0), (-1,-1), 1, AMBER),
    ("TOPPADDING", (0,0), (-1,-1), 10),
    ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ("LEFTPADDING", (0,0), (-1,-1), 14),
    ("RIGHTPADDING", (0,0), (-1,-1), 14),
]))

story.append(KeepTogether([
    Paragraph("A CONSULTORIA SE PAGOU? SIM.", s_h1),
    HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4),
    Paragraph(
        f"O bônus de produtividade só foi pago porque a lavoura <b>passou do alvo "
        f"combinado</b> (160 sc/alq na soja e 460 sc/alq no milho). "
        f"As <b>sacas produzidas a mais</b> por ter passado desses limites valem:",
        s_body),
    t_extra,
    Spacer(1, 3*mm),
    concl,
]))
story.append(Spacer(1, 5*mm))

# ===== OBS FINAIS CURTAS =====
story.append(Paragraph(
    "<b>Importante:</b> os custos de produção (110 sc/alq soja e 220 sc/alq milho) "
    "são uma <b>estimativa de referência</b>. O custo real pode ser diferente, "
    "dependendo dos insumos que a senhora usou, das operações mecanizadas "
    "e do preço pago na safra. Os preços das sacas são da <b>SIMA-PR em 22/04/2026</b> "
    "(soja R$ 111,00 / milho R$ 52,00) — no dia da venda efetiva, recalculamos "
    "pelo preço do mercado.",
    ParagraphStyle("ob",parent=s_body,fontSize=9.5,textColor=GRAY_TXT,leading=12.5)))

# BUILD
doc.build(story)
print(f"OK -> {PDF}")
print(f"     tamanho: {PDF.stat().st_size/1024:.1f} KB")

dest = pathlib.Path.home() / "Desktop" / PDF.name
shutil.copy(PDF, dest)
print(f"     copiado -> {dest}")
