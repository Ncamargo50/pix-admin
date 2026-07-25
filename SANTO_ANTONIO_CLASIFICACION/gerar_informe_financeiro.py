# -*- coding: utf-8 -*-
"""
Informe Financeiro de Consultoria Agrícola
Safra 2025/2026 — Sra. Sônia Maria Bigati
Cotações oficiais SIMA-PR 22/04/2026
"""
import pathlib, shutil
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable, KeepTogether
)

HERE = pathlib.Path(__file__).parent
LOGO = pathlib.Path(r"D:\PIXADVISOR_AGENT_WORKSPACE\pix-admin\img\LOGO-PIX.png")
OUT  = HERE / "output"
OUT.mkdir(exist_ok=True)
PDF_PATH = OUT / "Informe_Financeiro_Consultoria_Safra_2025-2026.pdf"

# ======== BRANDING PIXADVISOR =========
TEAL      = HexColor("#7FD633")
TEAL_DARK = HexColor("#6BBF2A")
BLUE      = HexColor("#00A4CC")
DARK      = HexColor("#0F1B2D")
DARK_2    = HexColor("#1a2a40")
GRAY_LT   = HexColor("#F1F5F9")
GRAY_MD   = HexColor("#CBD5E1")
GRAY_TXT  = HexColor("#334155")
WHITE     = colors.white
GOLD      = HexColor("#FFB300")
RED_SOFT  = HexColor("#EF4444")

# =============== DADOS ===============
# Cotações oficiais SIMA-PR (22/04/2026 — Cornélio Procópio)
PRECO_SOJA  = 111.00   # R$/saca 60kg
PRECO_MILHO = 52.00    # R$/saca 60kg

# Áreas (alqueires paulistas, 1 alq = 2,42 ha)
ALQ_SOJA_SA   = 34.99   # Santo Antônio
ALQ_SOJA_SF   = 38.59   # São Francisco
ALQ_MILHO_SA  = 21.64   # Santo Antônio
ALQ_SOJA      = ALQ_SOJA_SA + ALQ_SOJA_SF    # 73,58
ALQ_MILHO     = ALQ_MILHO_SA                  # 21,64

# Remuneração (sacas por alqueire, com bônus aplicado)
SC_POR_ALQ_SOJA  = 4   # 3 base + 1 bônus (rend 178 >= 160)
SC_POR_ALQ_MILHO = 5   # 4 base + 1 bônus (rend 478 >= 460)

# Rendimentos obtidos na safra
REND_SOJA_SC_ALQ  = 178
REND_MILHO_SC_ALQ = 478

# Cálculos
SACAS_SOJA   = ALQ_SOJA  * SC_POR_ALQ_SOJA    # 294,32
SACAS_MILHO  = ALQ_MILHO * SC_POR_ALQ_MILHO   # 108,20
REM_SOJA     = SACAS_SOJA  * PRECO_SOJA       # R$ 32.669,52
REM_MILHO    = SACAS_MILHO * PRECO_MILHO      # R$ 5.626,40
REM_TOTAL    = REM_SOJA + REM_MILHO

# Adiantamentos recebidos
ADIANTAMENTOS = [
    ("19/01/2026", "Adiantamento em dinheiro", 2000.00),
]
TOTAL_ADIANT = sum(v for _, _, v in ADIANTAMENTOS)
SALDO_LIQUIDO = REM_TOTAL - TOTAL_ADIANT

# Produção total estimada
PROD_SOJA_SC   = ALQ_SOJA  * REND_SOJA_SC_ALQ   # 13.097,24 sc
PROD_MILHO_SC  = ALQ_MILHO * REND_MILHO_SC_ALQ  # 10.343,92 sc
VALOR_PROD_SOJA   = PROD_SOJA_SC  * PRECO_SOJA
VALOR_PROD_MILHO  = PROD_MILHO_SC * PRECO_MILHO
VALOR_PROD_TOTAL  = VALOR_PROD_SOJA + VALOR_PROD_MILHO

# % consultoria sobre a produção bruta
PCT_CONS_SOJA  = REM_SOJA  / VALOR_PROD_SOJA  * 100
PCT_CONS_MILHO = REM_MILHO / VALOR_PROD_MILHO * 100
PCT_CONS_TOTAL = REM_TOTAL / VALOR_PROD_TOTAL * 100

# ================ CUSTO-BENEFÍCIO ================
# Custo referencial de produção (sacas do próprio cultivo por alqueire)
CUSTO_SOJA_SC_ALQ  = 110    # sc/alq
CUSTO_MILHO_SC_ALQ = 220    # sc/alq

# Sacas consumidas em custos
SC_CUSTO_SOJA   = ALQ_SOJA  * CUSTO_SOJA_SC_ALQ     # 8.094
SC_CUSTO_MILHO  = ALQ_MILHO * CUSTO_MILHO_SC_ALQ    # 4.761

# Custo em R$
CUSTO_SOJA   = SC_CUSTO_SOJA  * PRECO_SOJA
CUSTO_MILHO  = SC_CUSTO_MILHO * PRECO_MILHO
CUSTO_TOTAL  = CUSTO_SOJA + CUSTO_MILHO

# Margem bruta (receita – custo de produção, antes da consultoria)
MARGEM_BRUTA_SOJA   = VALOR_PROD_SOJA  - CUSTO_SOJA
MARGEM_BRUTA_MILHO  = VALOR_PROD_MILHO - CUSTO_MILHO
MARGEM_BRUTA_TOTAL  = MARGEM_BRUTA_SOJA + MARGEM_BRUTA_MILHO

# Margem líquida (receita – custo – consultoria)
MARGEM_LIQ_SOJA   = MARGEM_BRUTA_SOJA  - REM_SOJA
MARGEM_LIQ_MILHO  = MARGEM_BRUTA_MILHO - REM_MILHO
MARGEM_LIQ_TOTAL  = MARGEM_LIQ_SOJA + MARGEM_LIQ_MILHO

# Indicadores de custo-benefício
PCT_CONS_CUSTO   = REM_TOTAL / CUSTO_TOTAL        * 100  # consultoria / custo produção
PCT_CONS_MARGEM  = REM_TOTAL / MARGEM_BRUTA_TOTAL * 100  # consultoria / margem bruta
PCT_MARGEM_REC   = MARGEM_LIQ_TOTAL / VALOR_PROD_TOTAL * 100  # margem líq / receita

# Receita extra gerada pelo bônus de produtividade (vs limiar mínimo)
EXTRA_SC_SOJA   = (REND_SOJA_SC_ALQ  - 160) * ALQ_SOJA    # sacas acima do limiar
EXTRA_SC_MILHO  = (REND_MILHO_SC_ALQ - 460) * ALQ_MILHO
RECEITA_EXTRA_SOJA   = EXTRA_SC_SOJA  * PRECO_SOJA
RECEITA_EXTRA_MILHO  = EXTRA_SC_MILHO * PRECO_MILHO
RECEITA_EXTRA_TOTAL  = RECEITA_EXTRA_SOJA + RECEITA_EXTRA_MILHO
# ROI aproximado: receita extra (acima do limiar do bônus) / custo da consultoria
ROI_CONSULTORIA = RECEITA_EXTRA_TOTAL / REM_TOTAL  # vezes (x)

# ================== GRÁFICOS ==================
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans"]

def fmt_brl(x, pos=None):
    return f"R$ {x:,.0f}".replace(",", ".")

# --- G1: Pie de áreas ---
fig, ax = plt.subplots(figsize=(5.2, 3.8), dpi=150)
vals = [ALQ_SOJA_SA*2.42, ALQ_SOJA_SF*2.42, ALQ_MILHO_SA*2.42]
labels = [f"Soja Sto. Antônio\n{vals[0]:.1f} ha",
          f"Soja S. Francisco\n{vals[1]:.1f} ha",
          f"Milho Sto. Antônio\n{vals[2]:.1f} ha"]
cols = ["#2E7D32", "#66BB6A", "#FFB300"]
w, _, autotxts = ax.pie(vals, labels=labels, colors=cols, startangle=90,
    autopct=lambda p: f"{p:.1f}%", wedgeprops=dict(edgecolor="white", linewidth=2),
    textprops={"fontsize":9, "color":"#0F1B2D"})
for t in autotxts:
    t.set_color("white"); t.set_fontweight("bold"); t.set_fontsize(10)
ax.set_title(f"Distribuição de Áreas — Total {sum(vals):.1f} ha",
             fontsize=11, fontweight="bold", color="#0F1B2D", pad=12)
plt.tight_layout()
G1 = OUT / "_graf_areas.png"
plt.savefig(G1, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()

# --- G2: Barras de remuneração vs produção ---
fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=150)
x = np.arange(2)
w_bar = 0.35
prod_vals = [VALOR_PROD_SOJA, VALOR_PROD_MILHO]
cons_vals = [REM_SOJA, REM_MILHO]
b1 = ax.bar(x - w_bar/2, prod_vals, w_bar, label="Produção bruta (R$)",
            color="#0F1B2D", edgecolor="white")
b2 = ax.bar(x + w_bar/2, cons_vals, w_bar, label="Consultoria (R$)",
            color="#7FD633", edgecolor="white")
ax.set_xticks(x)
ax.set_xticklabels(["Soja", "Milho"], fontsize=11, fontweight="bold")
ax.set_ylabel("R$", fontsize=10)
ax.set_title("Produção bruta vs Consultoria — Safra 2025/2026",
             fontsize=11, fontweight="bold", color="#0F1B2D")
ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt_brl))
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.legend(loc="upper right", frameon=False, fontsize=9)
for b in b1:
    h = b.get_height()
    ax.annotate(fmt_brl(h), xy=(b.get_x()+b.get_width()/2, h),
                xytext=(0,3), textcoords="offset points",
                ha="center", fontsize=8, color="#0F1B2D")
for b in b2:
    h = b.get_height()
    ax.annotate(fmt_brl(h), xy=(b.get_x()+b.get_width()/2, h),
                xytext=(0,3), textcoords="offset points",
                ha="center", fontsize=8, color="#6BBF2A", fontweight="bold")
plt.tight_layout()
G2 = OUT / "_graf_prod_cons.png"
plt.savefig(G2, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()

# ================== PDF ==================
styles = getSampleStyleSheet()
s_title = ParagraphStyle("t", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=16, textColor=WHITE, alignment=TA_CENTER, leading=20)
s_subtitle = ParagraphStyle("st", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10, textColor=WHITE, alignment=TA_CENTER, leading=13)
s_h1 = ParagraphStyle("h1", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11, textColor=DARK, alignment=TA_LEFT, leading=13,
    spaceBefore=5, spaceAfter=3)
s_h2 = ParagraphStyle("h2", parent=styles["Heading3"], fontName="Helvetica-Bold",
    fontSize=10, textColor=TEAL_DARK, alignment=TA_LEFT, leading=12.5,
    spaceBefore=4, spaceAfter=2)
s_body = ParagraphStyle("b", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9.5, textColor=GRAY_TXT, alignment=TA_JUSTIFY, leading=12.5, spaceAfter=3)
s_body_c = ParagraphStyle("bc", parent=s_body, alignment=TA_CENTER)
s_small = ParagraphStyle("s", parent=styles["Normal"], fontName="Helvetica",
    fontSize=8.5, textColor=GRAY_TXT, alignment=TA_JUSTIFY, leading=11)
s_tablehdr = ParagraphStyle("th", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=9, textColor=WHITE, alignment=TA_CENTER, leading=12)
s_tablecell = ParagraphStyle("td", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9, textColor=DARK, alignment=TA_CENTER, leading=12)
s_tablecell_b = ParagraphStyle("tdb", parent=s_tablecell, fontName="Helvetica-Bold")
s_tablecell_l = ParagraphStyle("tdl", parent=s_tablecell, alignment=TA_LEFT)
s_big = ParagraphStyle("big", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=22, textColor=DARK, alignment=TA_CENTER, leading=26)
s_huge = ParagraphStyle("huge", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=26, textColor=TEAL_DARK, alignment=TA_CENTER, leading=30)

def header_footer(canv, doc):
    canv.saveState()
    W, H = A4
    bar_h = 24*mm
    canv.setFillColor(DARK); canv.rect(0, H-bar_h, W, bar_h, stroke=0, fill=1)
    # Banda gradient
    for i in range(60):
        r = 127/255 + (0 - 127/255) * (i/60)
        g = 214/255 + (164/255 - 214/255) * (i/60)
        b = 51/255  + (204/255 - 51/255) * (i/60)
        canv.setFillColorRGB(r, g, b)
        canv.rect((i/60)*W, H-bar_h-2*mm, W/60+0.5, 2*mm, stroke=0, fill=1)
    # Painel branco p/ logo
    canv.setFillColor(WHITE)
    canv.roundRect(8*mm, H-bar_h+2*mm, 40*mm, 20*mm, 2*mm, stroke=0, fill=1)
    if LOGO.exists():
        canv.drawImage(str(LOGO), 9*mm, H-bar_h+3*mm, width=38*mm, height=18*mm,
                       preserveAspectRatio=True, mask='auto')
    canv.setFillColor(WHITE)
    canv.setFont("Helvetica-Bold", 11)
    canv.drawRightString(W-10*mm, H-10*mm, "PIXADVISOR")
    canv.setFillColor(TEAL)
    canv.setFont("Helvetica", 8)
    canv.drawRightString(W-10*mm, H-14*mm, "Agricultura de Precisão")
    canv.setFillColor(GRAY_MD)
    canv.setFont("Helvetica", 7.5)
    canv.drawRightString(W-10*mm, H-18*mm, "Engenharia Agronômica  |  Consultoria Técnica")

    # Footer
    canv.setFillColor(DARK); canv.rect(0, 0, W, 12*mm, stroke=0, fill=1)
    canv.setFillColor(TEAL); canv.rect(0, 12*mm, W, 1.5*mm, stroke=0, fill=1)
    canv.setFillColor(WHITE); canv.setFont("Helvetica", 8)
    canv.drawString(10*mm, 6.5*mm, "Nilton Luiz Camargo — Engenheiro Agrônomo — CPF: 869.321.959-68")
    canv.drawString(10*mm, 3*mm, "Ibiporã / PR — Brasil")
    canv.drawRightString(W-10*mm, 6.5*mm,
        "Informe Financeiro — Safra 2025/2026  —  Sra. Sônia Maria Bigati")
    canv.drawRightString(W-10*mm, 3*mm, f"Página {canv.getPageNumber()}")
    canv.restoreState()

doc = BaseDocTemplate(str(PDF_PATH), pagesize=A4,
    leftMargin=15*mm, rightMargin=15*mm, topMargin=27*mm, bottomMargin=14*mm,
    title="Informe Financeiro Consultoria - Safra 2025/2026",
    author="Pixadvisor / Nilton Luiz Camargo")
doc.addPageTemplates(PageTemplate(id="main",
    frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  showBoundary=0)], onPage=header_footer))

story = []

# ============ TÍTULO ============
tbox = Table([[Paragraph(
    "<b>INFORME FINANCEIRO DE CONSULTORIA AGRÍCOLA</b><br/>"
    "<b>Safra 2025/2026</b>", s_title)]], colWidths=[doc.width])
tbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK),
    ("TOPPADDING",(0,0),(-1,-1),10), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
story.append(tbox)

sbox = Table([[Paragraph(
    "Sra. Sônia Maria Bigati  |  Faz. Santo Antônio &amp; Faz. São Francisco<br/>"
    "Cálculo de remuneração com cotações oficiais SIMA-PR (22/04/2026)",
    s_subtitle)]], colWidths=[doc.width])
sbox.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),TEAL_DARK),
    ("TOPPADDING",(0,0),(-1,-1),6), ("BOTTOMPADDING",(0,0),(-1,-1),6)]))
story.append(sbox)
story.append(Spacer(1, 6*mm))

# ============ 1. RESUMO EXECUTIVO ============
story.append(Paragraph("1. RESUMO EXECUTIVO", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

# Card destaque: Bruto, Adiantamentos, Saldo líquido
def brl(v):
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

destaque_data = [
    [Paragraph("<b>REMUNERAÇÃO BRUTA</b>", s_tablehdr),
     Paragraph("<b>(−) ADIANTAMENTOS</b>", s_tablehdr),
     Paragraph("<b>SALDO LÍQUIDO A PAGAR</b>", s_tablehdr)],
    [Paragraph(f"<b>{brl(REM_TOTAL)}</b>",
               ParagraphStyle("g1", parent=s_big, fontSize=16, textColor=DARK)),
     Paragraph(f"<b>− {brl(TOTAL_ADIANT)}</b>",
               ParagraphStyle("g2", parent=s_big, fontSize=16, textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(SALDO_LIQUIDO)}</b>",
               ParagraphStyle("g3", parent=s_big, fontSize=18, textColor=TEAL_DARK))],
]
t_destaque = Table(destaque_data,
                   colWidths=[doc.width*0.32, doc.width*0.28, doc.width*0.40])
t_destaque.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,1), (0,1), GRAY_LT),
    ("BACKGROUND", (1,1), (1,1), HexColor("#FEE2E2")),
    ("BACKGROUND", (2,1), (2,1), HexColor("#E8F5DC")),
    ("BOX", (0,0), (-1,-1), 1, TEAL_DARK),
    ("INNERGRID", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,0), 6),
    ("BOTTOMPADDING", (0,0), (-1,0), 6),
    ("TOPPADDING", (0,1), (-1,1), 14),
    ("BOTTOMPADDING", (0,1), (-1,1), 14),
]))
story.append(t_destaque)
story.append(Spacer(1, 2*mm))
story.append(Paragraph(
    f"Valor bruto composto por <b>{SACAS_SOJA:.2f} sacas de soja</b> "
    f"({ALQ_SOJA:.2f} alq × {SC_POR_ALQ_SOJA} sc/alq × R$ {PRECO_SOJA:.2f}/sc) "
    f"mais <b>{SACAS_MILHO:.2f} sacas de milho</b> "
    f"({ALQ_MILHO:.2f} alq × {SC_POR_ALQ_MILHO} sc/alq × R$ {PRECO_MILHO:.2f}/sc), "
    f"deduzido adiantamento de {brl(TOTAL_ADIANT)} recebido em 19/01/2026.",
    s_small))
story.append(Spacer(1, 3*mm))

kpi_data = [
    [Paragraph("<b>Área contratada</b>", s_tablehdr),
     Paragraph("<b>Receita bruta estimada</b>", s_tablehdr),
     Paragraph("<b>Margem líquida</b><br/><font size=7>(receita − custo − consultoria)</font>", s_tablehdr),
     Paragraph("<b>Consultoria / Receita</b>", s_tablehdr)],
    [Paragraph(f"<b>230,44 ha</b><br/>95,22 alqueires", s_tablecell_b),
     Paragraph(f"<b>R$ {VALOR_PROD_TOTAL:,.0f}</b>".replace(",",".") + "<br/>"
               f"<font size=7>{PROD_SOJA_SC:,.0f} sc soja + {PROD_MILHO_SC:,.0f} sc milho</font>".replace(",","."),
               s_tablecell_b),
     Paragraph(f"<b>R$ {MARGEM_LIQ_TOTAL:,.0f}</b>".replace(",",".") + "<br/>"
               f"<font size=7>{PCT_MARGEM_REC:.1f}% da receita</font>",
               ParagraphStyle("mg",parent=s_tablecell_b,textColor=TEAL_DARK)),
     Paragraph(f"<b>{PCT_CONS_TOTAL:.2f}%</b><br/>"
               f"<font size=7>da receita bruta</font>", s_tablecell_b)],
]
t_kpi = Table(kpi_data, colWidths=[doc.width*0.22, doc.width*0.28, doc.width*0.27, doc.width*0.23])
t_kpi.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK_2),
    ("BACKGROUND", (0,1), (-1,1), GRAY_LT),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]))
story.append(t_kpi)
story.append(Spacer(1, 5*mm))

# ============ 2. COTAÇÕES OFICIAIS ============
story.append(Paragraph("2. COTAÇÕES OFICIAIS DE REFERÊNCIA", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))
story.append(Paragraph(
    "Preços levantados em fontes oficiais para a mesorregião "
    "<b>Norte Pioneiro Paranaense</b> — microrregião de Cornélio Procópio — "
    "na qual está situado o município de <b>São Sebastião da Amoreira</b>.",
    s_body))

cot_data = [
    [Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>FONTE</b>", s_tablehdr),
     Paragraph("<b>LOCALIDADE</b>", s_tablehdr),
     Paragraph("<b>DATA</b>", s_tablehdr),
     Paragraph("<b>R$/SACA 60 kg</b>", s_tablehdr)],
    [Paragraph("<b>Soja</b>", s_tablecell_b),
     Paragraph("SIMA-PR (SEAB)", s_tablecell),
     Paragraph("Cornélio Procópio", s_tablecell),
     Paragraph("22/04/2026", s_tablecell),
     Paragraph(f"<b>R$ {PRECO_SOJA:.2f}</b>", s_tablecell_b)],
    [Paragraph("Soja", s_tablecell),
     Paragraph("CEPEA/ESALQ-USP", s_tablecell),
     Paragraph("Indicador PR", s_tablecell),
     Paragraph("22/04/2026", s_tablecell),
     Paragraph("R$ 120,62", s_tablecell)],
    [Paragraph("<b>Milho</b>", s_tablecell_b),
     Paragraph("SIMA-PR (SEAB)", s_tablecell),
     Paragraph("Cornélio Procópio", s_tablecell),
     Paragraph("22/04/2026", s_tablecell),
     Paragraph(f"<b>R$ {PRECO_MILHO:.2f}</b>", s_tablecell_b)],
    [Paragraph("Milho", s_tablecell),
     Paragraph("CEPEA/ESALQ-USP", s_tablecell),
     Paragraph("Campinas/SP ref.", s_tablecell),
     Paragraph("22/04/2026", s_tablecell),
     Paragraph("R$ 67,00", s_tablecell)],
]
t_cot = Table(cot_data, colWidths=[
    doc.width*0.12, doc.width*0.22, doc.width*0.23,
    doc.width*0.18, doc.width*0.25])
t_cot.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GRAY_LT]),
    # destacar linhas aplicadas ao contrato
    ("BACKGROUND", (0,1), (-1,1), HexColor("#E8F5DC")),
    ("BACKGROUND", (0,3), (-1,3), HexColor("#FFF4D6")),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_cot)
story.append(Spacer(1, 2*mm))
story.append(Paragraph(
    "<i>As linhas destacadas (verde para soja, amarela para milho) correspondem "
    "aos valores adotados para o cálculo deste informe. A opção pelo SIMA-PR "
    "deve-se à sua natureza oficial (SEAB/DERAL) e por refletir o preço "
    "efetivamente pago ao produtor pelo mercado atacadista regional.</i>",
    s_small))
story.append(Spacer(1, 4*mm))

# ============ 3. ÁREAS E PRODUÇÃO ============
story.append(Paragraph("3. ÁREAS CONTRATADAS E RENDIMENTOS OBTIDOS", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

prod_data = [
    [Paragraph("<b>FAZENDA</b>", s_tablehdr),
     Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>ÁREA (ha)</b>", s_tablehdr),
     Paragraph("<b>ÁREA (alq)</b>", s_tablehdr),
     Paragraph("<b>REND. (sc/alq)</b>", s_tablehdr),
     Paragraph("<b>PRODUÇÃO (sc)</b>", s_tablehdr)],
    [Paragraph("Santo Antônio", s_tablecell),
     Paragraph("Soja", s_tablecell),
     Paragraph("84,67", s_tablecell),
     Paragraph("34,99", s_tablecell),
     Paragraph(f"{REND_SOJA_SC_ALQ}", s_tablecell_b),
     Paragraph(f"{ALQ_SOJA_SA*REND_SOJA_SC_ALQ:,.0f}".replace(",","."),
               s_tablecell_b)],
    [Paragraph("Santo Antônio", s_tablecell),
     Paragraph("Milho", s_tablecell),
     Paragraph("52,38", s_tablecell),
     Paragraph("21,64", s_tablecell),
     Paragraph(f"{REND_MILHO_SC_ALQ}", s_tablecell_b),
     Paragraph(f"{ALQ_MILHO_SA*REND_MILHO_SC_ALQ:,.0f}".replace(",","."),
               s_tablecell_b)],
    [Paragraph("São Francisco", s_tablecell),
     Paragraph("Soja", s_tablecell),
     Paragraph("93,39", s_tablecell),
     Paragraph("38,59", s_tablecell),
     Paragraph(f"{REND_SOJA_SC_ALQ}", s_tablecell_b),
     Paragraph(f"{ALQ_SOJA_SF*REND_SOJA_SC_ALQ:,.0f}".replace(",","."),
               s_tablecell_b)],
    [Paragraph("<b>TOTAL</b>", s_tablecell_b),
     Paragraph("—", s_tablecell),
     Paragraph("<b>230,44</b>", s_tablecell_b),
     Paragraph("<b>95,22</b>", s_tablecell_b),
     Paragraph("—", s_tablecell),
     Paragraph(f"<b>{PROD_SOJA_SC+PROD_MILHO_SC:,.0f}</b>".replace(",","."),
               s_tablecell_b)],
]
t_prod = Table(prod_data, colWidths=[
    doc.width*0.22, doc.width*0.13, doc.width*0.14,
    doc.width*0.14, doc.width*0.16, doc.width*0.21])
t_prod.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), TEAL),
    ("TEXTCOLOR", (0,-1), (-1,-1), WHITE),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(KeepTogether([
    t_prod,
    Spacer(1, 3*mm),
    Image(str(G1), width=95*mm, height=65*mm),
]))
story.append(Spacer(1, 3*mm))

# ============ 4. CÁLCULO DA REMUNERAÇÃO ============
story.append(PageBreak())
story.append(Paragraph("4. CÁLCULO DETALHADO DA REMUNERAÇÃO", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

story.append(Paragraph("4.1. Fórmula aplicada", s_h2))
story.append(Paragraph(
    "A remuneração da consultoria técnica é calculada em <b>sacas do respectivo "
    "cultivo por alqueire contratado</b>, incluindo o bônus de produtividade "
    "quando aplicável, conforme estabelecido na Cláusula IV do contrato.",
    s_body))

formula_data = [
    [Paragraph(
        "<b>Remuneração</b> = Alqueires × (Taxa base + Bônus) × Preço saca",
        s_tablecell_b)],
]
t_form = Table(formula_data, colWidths=[doc.width])
t_form.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), GRAY_LT),
    ("BOX", (0,0), (-1,-1), 0.5, TEAL_DARK),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 8),
    ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]))
story.append(t_form)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("4.2. Aplicação do bônus de produtividade", s_h2))

bonus_data = [
    [Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>REND. OBTIDO</b>", s_tablehdr),
     Paragraph("<b>LIMIAR DO BÔNUS</b>", s_tablehdr),
     Paragraph("<b>DIFERENÇA</b>", s_tablehdr),
     Paragraph("<b>BÔNUS</b>", s_tablehdr)],
    [Paragraph("Soja", s_tablecell),
     Paragraph("<b>178 sc/alq</b>", s_tablecell_b),
     Paragraph("≥ 160 sc/alq", s_tablecell),
     Paragraph("+18 sc/alq", s_tablecell_b),
     Paragraph("✓ APLICA (+1 sc)", s_tablecell_b)],
    [Paragraph("Milho", s_tablecell),
     Paragraph("<b>478 sc/alq</b>", s_tablecell_b),
     Paragraph("≥ 460 sc/alq", s_tablecell),
     Paragraph("+18 sc/alq", s_tablecell_b),
     Paragraph("✓ APLICA (+1 sc)", s_tablecell_b)],
]
t_bonus = Table(bonus_data, colWidths=[
    doc.width*0.14, doc.width*0.22, doc.width*0.22, doc.width*0.18, doc.width*0.24])
t_bonus.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (4,1), (4,-1), HexColor("#E8F5DC")),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_bonus)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("4.3. Memória de cálculo", s_h2))

mem_data = [
    [Paragraph("<b>ITEM</b>", s_tablehdr),
     Paragraph("<b>SOJA</b>", s_tablehdr),
     Paragraph("<b>MILHO</b>", s_tablehdr)],
    [Paragraph("Alqueires contratados", s_tablecell_l),
     Paragraph(f"{ALQ_SOJA:,.2f} alq".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"{ALQ_MILHO:,.2f} alq".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b)],
    [Paragraph("(×) Remuneração base", s_tablecell_l),
     Paragraph("3 sc/alq", s_tablecell),
     Paragraph("4 sc/alq", s_tablecell)],
    [Paragraph("(+) Bônus de produtividade", s_tablecell_l),
     Paragraph("+1 sc/alq", s_tablecell_b),
     Paragraph("+1 sc/alq", s_tablecell_b)],
    [Paragraph("(=) Taxa efetiva", s_tablecell_l),
     Paragraph(f"{SC_POR_ALQ_SOJA} sc/alq", s_tablecell_b),
     Paragraph(f"{SC_POR_ALQ_MILHO} sc/alq", s_tablecell_b)],
    [Paragraph("<b>Total de sacas a receber</b>", s_tablecell_l),
     Paragraph(f"<b>{SACAS_SOJA:,.2f} sacas</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"<b>{SACAS_MILHO:,.2f} sacas</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b)],
    [Paragraph("(×) Preço saca (SIMA-PR)", s_tablecell_l),
     Paragraph(f"R$ {PRECO_SOJA:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"R$ {PRECO_MILHO:.2f}".replace(".",","), s_tablecell)],
    [Paragraph("<b>(=) Remuneração por cultivo</b>", s_tablecell_l),
     Paragraph(f"<b>R$ {REM_SOJA:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"<b>R$ {REM_MILHO:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b)],
]
t_mem = Table(mem_data, colWidths=[doc.width*0.48, doc.width*0.26, doc.width*0.26])
t_mem.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), TEAL),
    ("TEXTCOLOR", (0,-1), (-1,-1), WHITE),
    ("BACKGROUND", (0,5), (-1,5), HexColor("#FFF4D6")),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,1), (0,-1), 10),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_mem)
story.append(Spacer(1, 4*mm))

# Total consolidado BRUTO
consol_data = [
    [Paragraph("<b>REMUNERAÇÃO BRUTA TOTAL DA CONSULTORIA</b>", s_tablehdr)],
    [Paragraph(f"<b>{brl(REM_TOTAL)}</b>", s_huge)],
]
t_consol = Table(consol_data, colWidths=[doc.width])
t_consol.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,1), (-1,1), HexColor("#E8F5DC")),
    ("BOX", (0,0), (-1,-1), 1, TEAL_DARK),
    ("TOPPADDING", (0,0), (-1,0), 6),
    ("BOTTOMPADDING", (0,0), (-1,0), 6),
    ("TOPPADDING", (0,1), (-1,1), 10),
    ("BOTTOMPADDING", (0,1), (-1,1), 10),
]))
story.append(t_consol)
story.append(Spacer(1, 5*mm))

# ============ 4.4 ADIANTAMENTOS E SALDO LÍQUIDO ============
story.append(Paragraph("4.4. Adiantamentos e apuração do saldo líquido", s_h2))
story.append(Paragraph(
    "Conforme previsto na <b>Cláusula V do contrato</b>, eventuais "
    "adiantamentos em dinheiro solicitados pela CONTRATADA durante a "
    "safra são descontados no pagamento total no fechamento. Registra-se "
    "o(s) seguinte(s) adiantamento(s) recebido(s):",
    s_body))

adi_data = [[
    Paragraph("<b>Nº</b>", s_tablehdr),
    Paragraph("<b>DATA</b>", s_tablehdr),
    Paragraph("<b>DESCRIÇÃO</b>", s_tablehdr),
    Paragraph("<b>VALOR (R$)</b>", s_tablehdr),
]]
for i, (d, desc, v) in enumerate(ADIANTAMENTOS, start=1):
    adi_data.append([
        Paragraph(str(i), s_tablecell),
        Paragraph(d, s_tablecell),
        Paragraph(desc, s_tablecell_l),
        Paragraph(f"<b>{brl(v)}</b>", s_tablecell_b),
    ])
adi_data.append([
    Paragraph("", s_tablecell),
    Paragraph("", s_tablecell),
    Paragraph("<b>TOTAL DE ADIANTAMENTOS</b>", s_tablecell_b),
    Paragraph(f"<b>{brl(TOTAL_ADIANT)}</b>", s_tablecell_b),
])
t_adi = Table(adi_data, colWidths=[doc.width*0.08, doc.width*0.18,
                                    doc.width*0.50, doc.width*0.24])
t_adi.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), HexColor("#FEE2E2")),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (2,1), (2,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_adi)
story.append(Spacer(1, 4*mm))

# Apuração final
apur_data = [
    [Paragraph("<b>APURAÇÃO FINAL</b>", s_tablehdr),
     Paragraph("<b>VALOR (R$)</b>", s_tablehdr)],
    [Paragraph("Remuneração bruta (Soja + Milho)", s_tablecell_l),
     Paragraph(f"<b>{brl(REM_TOTAL)}</b>", s_tablecell_b)],
    [Paragraph("(−) Total de adiantamentos recebidos", s_tablecell_l),
     Paragraph(f"<b>− {brl(TOTAL_ADIANT)}</b>",
               ParagraphStyle("rd", parent=s_tablecell_b, textColor=RED_SOFT))],
    [Paragraph("<b>(=) SALDO LÍQUIDO A PAGAR</b>", s_tablecell_b),
     Paragraph(f"<b>{brl(SALDO_LIQUIDO)}</b>",
               ParagraphStyle("gn", parent=s_tablecell_b, textColor=TEAL_DARK,
                              fontSize=11))],
]
t_apur = Table(apur_data, colWidths=[doc.width*0.65, doc.width*0.35])
t_apur.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), HexColor("#E8F5DC")),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.8, TEAL_DARK),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,1), (0,-1), 10),
    ("TOPPADDING", (0,0), (-1,-2), 6),
    ("BOTTOMPADDING", (0,0), (-1,-2), 6),
    ("TOPPADDING", (0,-1), (-1,-1), 10),
    ("BOTTOMPADDING", (0,-1), (-1,-1), 10),
]))
# Destaque saldo líquido
saldo_data = [
    [Paragraph("<b>SALDO LÍQUIDO A PAGAR À CONTRATADA</b>", s_tablehdr)],
    [Paragraph(f"<b>{brl(SALDO_LIQUIDO)}</b>", s_huge)],
]
t_saldo = Table(saldo_data, colWidths=[doc.width])
t_saldo.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), TEAL_DARK),
    ("BACKGROUND", (0,1), (-1,1), HexColor("#E8F5DC")),
    ("BOX", (0,0), (-1,-1), 1.2, TEAL_DARK),
    ("TOPPADDING", (0,0), (-1,0), 6),
    ("BOTTOMPADDING", (0,0), (-1,0), 6),
    ("TOPPADDING", (0,1), (-1,1), 8),
    ("BOTTOMPADDING", (0,1), (-1,1), 8),
]))
story.append(KeepTogether([t_apur, Spacer(1, 3*mm), t_saldo]))
story.append(Spacer(1, 4*mm))

# ============ 5. ANÁLISE ECONÔMICA ============
story.append(Paragraph("5. ANÁLISE ECONÔMICA DA SAFRA", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

story.append(Paragraph("5.1. Produção bruta estimada", s_h2))
story.append(Paragraph(
    "Com base nos rendimentos médios obtidos na safra 2025/2026 e nos preços "
    "oficiais SIMA-PR, estima-se a seguinte produção bruta nas áreas assistidas:",
    s_body))

prodb_data = [
    [Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>PRODUÇÃO (sacas)</b>", s_tablehdr),
     Paragraph("<b>PREÇO R$/sc</b>", s_tablehdr),
     Paragraph("<b>VALOR BRUTO (R$)</b>", s_tablehdr)],
    [Paragraph("Soja", s_tablecell),
     Paragraph(f"{PROD_SOJA_SC:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"R$ {PRECO_SOJA:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"<b>R$ {VALOR_PROD_SOJA:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b)],
    [Paragraph("Milho", s_tablecell),
     Paragraph(f"{PROD_MILHO_SC:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"R$ {PRECO_MILHO:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"<b>R$ {VALOR_PROD_MILHO:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b)],
    [Paragraph("<b>TOTAL</b>", s_tablecell_b),
     Paragraph(f"<b>{PROD_SOJA_SC+PROD_MILHO_SC:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph("—", s_tablecell),
     Paragraph(f"<b>R$ {VALOR_PROD_TOTAL:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b)],
]
t_prodb = Table(prodb_data,
    colWidths=[doc.width*0.18, doc.width*0.25, doc.width*0.20, doc.width*0.37])
t_prodb.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), TEAL),
    ("TEXTCOLOR", (0,-1), (-1,-1), WHITE),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(t_prodb)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("5.2. Proporção da consultoria sobre a produção bruta", s_h2))

prop_data = [
    [Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>PRODUÇÃO (R$)</b>", s_tablehdr),
     Paragraph("<b>CONSULTORIA (R$)</b>", s_tablehdr),
     Paragraph("<b>% da produção</b>", s_tablehdr)],
    [Paragraph("Soja", s_tablecell),
     Paragraph(f"R$ {VALOR_PROD_SOJA:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell),
     Paragraph(f"R$ {REM_SOJA:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell),
     Paragraph(f"<b>{PCT_CONS_SOJA:.2f}%</b>", s_tablecell_b)],
    [Paragraph("Milho", s_tablecell),
     Paragraph(f"R$ {VALOR_PROD_MILHO:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell),
     Paragraph(f"R$ {REM_MILHO:,.2f}".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell),
     Paragraph(f"<b>{PCT_CONS_MILHO:.2f}%</b>", s_tablecell_b)],
    [Paragraph("<b>Total</b>", s_tablecell_b),
     Paragraph(f"<b>R$ {VALOR_PROD_TOTAL:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"<b>R$ {REM_TOTAL:,.2f}</b>".replace(",","X").replace(".",",").replace("X","."),
               s_tablecell_b),
     Paragraph(f"<b>{PCT_CONS_TOTAL:.2f}%</b>", s_tablecell_b)],
]
t_prop = Table(prop_data,
    colWidths=[doc.width*0.18, doc.width*0.30, doc.width*0.27, doc.width*0.25])
t_prop.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), HexColor("#E8F5DC")),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(KeepTogether([
    t_prop,
    Spacer(1, 3*mm),
    Image(str(G2), width=130*mm, height=68*mm),
]))
story.append(Spacer(1, 3*mm))

# ============ 6. ANÁLISE CUSTO-BENEFÍCIO ============
story.append(PageBreak())
story.append(Paragraph("6. ANÁLISE CUSTO-BENEFÍCIO DA CONSULTORIA", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

story.append(Paragraph(
    "Esta seção compara a receita obtida, o custo referencial de produção e o "
    "valor da consultoria, oferecendo uma visão do <b>retorno sobre investimento</b> "
    "da consultoria técnica na safra 2025/2026.",
    s_body))

story.append(Paragraph("6.1. Custo referencial de produção", s_h2))
story.append(Paragraph(
    f"Considera-se, para fins desta análise, o custo total de produção "
    f"(insumos, operações mecanizadas, mão-de-obra, colheita e despesas "
    f"administrativas) equivalente a <b>{CUSTO_SOJA_SC_ALQ} sacas por alqueire "
    f"para a cultura da soja</b> e <b>{CUSTO_MILHO_SC_ALQ} sacas por alqueire "
    f"para a cultura do milho</b>, conforme média do produtor para a região "
    "do Norte Pioneiro Paranaense.",
    s_body))

custo_data = [
    [Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>ALQ.</b>", s_tablehdr),
     Paragraph("<b>CUSTO (sc/alq)</b>", s_tablehdr),
     Paragraph("<b>SACAS (custo)</b>", s_tablehdr),
     Paragraph("<b>PREÇO/saca</b>", s_tablehdr),
     Paragraph("<b>CUSTO TOTAL (R$)</b>", s_tablehdr)],
    [Paragraph("Soja", s_tablecell),
     Paragraph(f"{ALQ_SOJA:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"{CUSTO_SOJA_SC_ALQ}", s_tablecell_b),
     Paragraph(f"{SC_CUSTO_SOJA:,.0f}".replace(",","."), s_tablecell_b),
     Paragraph(f"R$ {PRECO_SOJA:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"<b>{brl(CUSTO_SOJA)}</b>", s_tablecell_b)],
    [Paragraph("Milho", s_tablecell),
     Paragraph(f"{ALQ_MILHO:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"{CUSTO_MILHO_SC_ALQ}", s_tablecell_b),
     Paragraph(f"{SC_CUSTO_MILHO:,.0f}".replace(",","."), s_tablecell_b),
     Paragraph(f"R$ {PRECO_MILHO:.2f}".replace(".",","), s_tablecell),
     Paragraph(f"<b>{brl(CUSTO_MILHO)}</b>", s_tablecell_b)],
    [Paragraph("<b>TOTAL</b>", s_tablecell_b),
     Paragraph(f"<b>{ALQ_SOJA+ALQ_MILHO:.2f}</b>".replace(".",","), s_tablecell_b),
     Paragraph("—", s_tablecell),
     Paragraph(f"<b>{SC_CUSTO_SOJA+SC_CUSTO_MILHO:,.0f}</b>".replace(",","."),
               s_tablecell_b),
     Paragraph("—", s_tablecell),
     Paragraph(f"<b>{brl(CUSTO_TOTAL)}</b>", s_tablecell_b)],
]
t_custo = Table(custo_data, colWidths=[
    doc.width*0.12, doc.width*0.10, doc.width*0.16, doc.width*0.17,
    doc.width*0.15, doc.width*0.30])
t_custo.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), HexColor("#FEE2E2")),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_custo)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("6.2. Receita, margem bruta e consultoria", s_h2))

marg_data = [
    [Paragraph("<b>CULTIVO</b>", s_tablehdr),
     Paragraph("<b>RECEITA (R$)</b>", s_tablehdr),
     Paragraph("<b>(−) CUSTO (R$)</b>", s_tablehdr),
     Paragraph("<b>(=) MARGEM BRUTA</b>", s_tablehdr),
     Paragraph("<b>(−) CONSULTORIA</b>", s_tablehdr),
     Paragraph("<b>(=) MARGEM LÍQ.</b>", s_tablehdr)],
    [Paragraph("Soja", s_tablecell),
     Paragraph(f"{brl(VALOR_PROD_SOJA)}", s_tablecell_b),
     Paragraph(f"− {brl(CUSTO_SOJA)}",
               ParagraphStyle("rs",parent=s_tablecell,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(MARGEM_BRUTA_SOJA)}</b>", s_tablecell_b),
     Paragraph(f"− {brl(REM_SOJA)}",
               ParagraphStyle("rs2",parent=s_tablecell,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(MARGEM_LIQ_SOJA)}</b>",
               ParagraphStyle("gs",parent=s_tablecell_b,textColor=TEAL_DARK))],
    [Paragraph("Milho", s_tablecell),
     Paragraph(f"{brl(VALOR_PROD_MILHO)}", s_tablecell_b),
     Paragraph(f"− {brl(CUSTO_MILHO)}",
               ParagraphStyle("rm",parent=s_tablecell,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(MARGEM_BRUTA_MILHO)}</b>", s_tablecell_b),
     Paragraph(f"− {brl(REM_MILHO)}",
               ParagraphStyle("rm2",parent=s_tablecell,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(MARGEM_LIQ_MILHO)}</b>",
               ParagraphStyle("gm",parent=s_tablecell_b,textColor=TEAL_DARK))],
    [Paragraph("<b>TOTAL</b>", s_tablecell_b),
     Paragraph(f"<b>{brl(VALOR_PROD_TOTAL)}</b>", s_tablecell_b),
     Paragraph(f"<b>− {brl(CUSTO_TOTAL)}</b>",
               ParagraphStyle("rt",parent=s_tablecell_b,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(MARGEM_BRUTA_TOTAL)}</b>", s_tablecell_b),
     Paragraph(f"<b>− {brl(REM_TOTAL)}</b>",
               ParagraphStyle("rt2",parent=s_tablecell_b,textColor=RED_SOFT)),
     Paragraph(f"<b>{brl(MARGEM_LIQ_TOTAL)}</b>",
               ParagraphStyle("gt",parent=s_tablecell_b,textColor=WHITE))],
]
t_marg = Table(marg_data, colWidths=[
    doc.width*0.11, doc.width*0.18, doc.width*0.16, doc.width*0.19,
    doc.width*0.17, doc.width*0.19])
t_marg.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,-1), (-1,-1), TEAL_DARK),
    ("TEXTCOLOR", (0,-1), (-1,-1), WHITE),
    ("ROWBACKGROUNDS", (0,1), (-1,-2), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_marg)
story.append(Spacer(1, 4*mm))

story.append(Paragraph("6.3. Indicadores de custo-benefício", s_h2))

kpi_cb_data = [
    [Paragraph("<b>INDICADOR</b>", s_tablehdr),
     Paragraph("<b>CÁLCULO</b>", s_tablehdr),
     Paragraph("<b>RESULTADO</b>", s_tablehdr)],
    [Paragraph("Consultoria / Receita bruta", s_tablecell_l),
     Paragraph(f"{brl(REM_TOTAL)} ÷ {brl(VALOR_PROD_TOTAL)}", s_tablecell),
     Paragraph(f"<b>{PCT_CONS_TOTAL:.2f}%</b>",
               ParagraphStyle("k1",parent=s_tablecell_b,textColor=TEAL_DARK,fontSize=11))],
    [Paragraph("Consultoria / Custo de produção", s_tablecell_l),
     Paragraph(f"{brl(REM_TOTAL)} ÷ {brl(CUSTO_TOTAL)}", s_tablecell),
     Paragraph(f"<b>{PCT_CONS_CUSTO:.2f}%</b>",
               ParagraphStyle("k2",parent=s_tablecell_b,textColor=TEAL_DARK,fontSize=11))],
    [Paragraph("Consultoria / Margem bruta", s_tablecell_l),
     Paragraph(f"{brl(REM_TOTAL)} ÷ {brl(MARGEM_BRUTA_TOTAL)}", s_tablecell),
     Paragraph(f"<b>{PCT_CONS_MARGEM:.2f}%</b>",
               ParagraphStyle("k3",parent=s_tablecell_b,textColor=TEAL_DARK,fontSize=11))],
    [Paragraph("<b>Margem líquida / Receita</b>", s_tablecell_l),
     Paragraph(f"{brl(MARGEM_LIQ_TOTAL)} ÷ {brl(VALOR_PROD_TOTAL)}", s_tablecell),
     Paragraph(f"<b>{PCT_MARGEM_REC:.1f}%</b>",
               ParagraphStyle("k4",parent=s_tablecell_b,textColor=DARK,fontSize=12))],
    [Paragraph("Retorno do bônus de produtividade<br/>"
               "<font size=7>(receita extra acima do limiar ÷ custo consultoria)</font>",
               s_tablecell_l),
     Paragraph(f"{brl(RECEITA_EXTRA_TOTAL)} ÷ {brl(REM_TOTAL)}", s_tablecell),
     Paragraph(f"<b>{ROI_CONSULTORIA:.1f}×</b>",
               ParagraphStyle("k5",parent=s_tablecell_b,textColor=TEAL_DARK,fontSize=13))],
]
t_kpi_cb = Table(kpi_cb_data,
    colWidths=[doc.width*0.38, doc.width*0.37, doc.width*0.25])
t_kpi_cb.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), DARK),
    ("BACKGROUND", (0,4), (-1,4), HexColor("#E8F5DC")),
    ("BACKGROUND", (0,5), (-1,5), HexColor("#FFF4D6")),
    ("ROWBACKGROUNDS", (0,1), (-1,3), [WHITE, GRAY_LT]),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING", (0,1), (0,-1), 10),
    ("TOPPADDING", (0,0), (-1,-1), 6),
    ("BOTTOMPADDING", (0,0), (-1,-1), 6),
]))
story.append(t_kpi_cb)
story.append(Spacer(1, 4*mm))

story.append(Paragraph(
    f"<b>Interpretação:</b> o custo da consultoria técnica "
    f"({brl(REM_TOTAL)}) representa apenas <b>{PCT_CONS_TOTAL:.2f}%</b> "
    f"da receita bruta e <b>{PCT_CONS_MARGEM:.2f}%</b> da margem bruta, "
    f"preservando uma <b>margem líquida de {brl(MARGEM_LIQ_TOTAL)} "
    f"({PCT_MARGEM_REC:.1f}% da receita)</b> para a CONTRATANTE após deduzidos "
    f"custo de produção e consultoria.",
    s_body))

story.append(Paragraph(
    f"O bônus de produtividade aplicado (soja com {REND_SOJA_SC_ALQ} vs "
    f"limiar de 160 sc/alq, e milho com {REND_MILHO_SC_ALQ} vs limiar de 460 "
    f"sc/alq) gerou uma <b>receita adicional estimada de {brl(RECEITA_EXTRA_TOTAL)}</b> "
    f"— aproximadamente <b>{ROI_CONSULTORIA:.1f}× o custo total da consultoria</b>, "
    "indicando retorno positivo do investimento em assessoria técnica.",
    s_body))

# ============ 7. OBSERVAÇÕES E RESSALVAS ============
story.append(PageBreak())
story.append(Paragraph("7. OBSERVAÇÕES E RESSALVAS", s_h1))
story.append(HRFlowable(width="100%", color=TEAL, thickness=1.2, spaceAfter=4))

story.append(Paragraph(
    "<b>7.1. Preço de referência:</b> Os valores apresentados utilizam a "
    "cotação oficial SIMA-PR da praça de Cornélio Procópio em 22/04/2026. "
    "O valor final a ser pago pela CONTRATANTE será recalculado com base "
    "no <b>preço efetivo de venda do dia</b> da comercialização de cada "
    "cultivo, conforme Cláusula V do contrato.",
    s_body))

story.append(Paragraph(
    "<b>7.2. Cláusula alternativa de mercado (soja):</b> O preço atual da "
    f"saca de soja (R$ {PRECO_SOJA:.2f}) encontra-se <b>abaixo do limiar "
    f"de R$ 150,00</b> estabelecido na Cláusula 4.1 do contrato. Portanto, "
    "mantém-se a remuneração base de 3 sacas/alq + 1 saca de bônus "
    "(4 sacas/alq), sem aplicação da redução para 2 sacas.",
    s_body))

story.append(Paragraph(
    "<b>7.3. Bônus de produtividade:</b> Ambos os cultivos ultrapassaram "
    "os limiares de rendimento estabelecidos no contrato "
    "(soja ≥ 160 sc/alq e milho ≥ 460 sc/alq), com 178 sc/alq e 478 sc/alq "
    "respectivamente. O bônus de +1 saca/alq foi aplicado nas duas culturas.",
    s_body))

story.append(Paragraph(
    f"<b>7.4. Custo-benefício:</b> A análise de custo-benefício (seção 6) "
    f"utiliza custos referenciais de {CUSTO_SOJA_SC_ALQ} sc/alq para soja e "
    f"{CUSTO_MILHO_SC_ALQ} sc/alq para milho. Trata-se de uma estimativa "
    "indicativa; os custos reais podem variar conforme o pacote tecnológico "
    "adotado, preço de insumos e operações da safra.",
    s_body))

story.append(Paragraph(
    f"<b>7.5. Adiantamentos recebidos:</b> Foi deduzido do valor bruto o "
    f"adiantamento de <b>{brl(TOTAL_ADIANT)}</b> recebido da CONTRATANTE "
    f"em 19/01/2026, conforme previsto na Cláusula V do contrato. "
    f"O saldo líquido remanescente a pagar corresponde a "
    f"<b>{brl(SALDO_LIQUIDO)}</b>.",
    s_body))

story.append(Paragraph(
    "<b>7.6. Tendência de mercado:</b> Os preços de milho apresentaram "
    "variação de −2,3% entre 17/04 e 20/04/2026 na plaza de referência. "
    "Em função da volatilidade, sugere-se avaliar o momento ótimo de "
    "comercialização junto à CONTRATADA.",
    s_body))

story.append(Spacer(1, 6*mm))

# Tabela de emissão
emit_data = [
    [Paragraph("<b>Data de emissão</b>", s_tablecell_b),
     Paragraph("22/04/2026", s_tablecell)],
    [Paragraph("<b>Praça de referência</b>", s_tablecell_b),
     Paragraph("Cornélio Procópio / PR (SIMA-PR)", s_tablecell)],
    [Paragraph("<b>Emitido por</b>", s_tablecell_b),
     Paragraph("Nilton Luiz Camargo — Engenheiro Agrônomo<br/>"
               "CPF: 869.321.959-68 — Ibiporã / PR", s_tablecell)],
    [Paragraph("<b>Destinatário</b>", s_tablecell_b),
     Paragraph("Sra. Sônia Maria Bigati — CPF: 095.660.409-97", s_tablecell)],
]
t_emit = Table(emit_data, colWidths=[doc.width*0.30, doc.width*0.70])
t_emit.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (0,-1), GRAY_LT),
    ("BOX", (0,0), (-1,-1), 0.5, GRAY_MD),
    ("INNERGRID", (0,0), (-1,-1), 0.3, GRAY_MD),
    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
]))
story.append(t_emit)
story.append(Spacer(1, 3*mm))

story.append(Paragraph(
    "<i>Este informe financeiro é parte integrante do Contrato de Prestação "
    "de Serviços de Consultoria Agrícola firmado para a safra 2025/2026, "
    "tendo caráter <b>informativo e de prestação de contas</b>. Os valores "
    "finais serão ajustados no ato da comercialização efetiva da produção, "
    "conforme o preço de mercado do dia.</i>",
    s_small))

# Build
doc.build(story)
print(f"OK -> {PDF_PATH}")
print(f"     tamanho: {PDF_PATH.stat().st_size/1024:.1f} KB")

# Copiar al Desktop
dest = pathlib.Path.home() / "Desktop" / PDF_PATH.name
shutil.copy(PDF_PATH, dest)
print(f"     copiado -> {dest}")
