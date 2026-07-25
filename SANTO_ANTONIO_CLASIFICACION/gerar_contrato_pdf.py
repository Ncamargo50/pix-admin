# -*- coding: utf-8 -*-
"""
Contrato de Prestacao de Servicos de Consultoria Agricola
Safra 2025/2026 - Sra. Sonia Maria Bigati
Branding: Pixadvisor Agricultura de Precisao
"""
import pathlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = pathlib.Path(__file__).parent
LOGO = pathlib.Path(r"D:\PIXADVISOR_AGENT_WORKSPACE\pix-admin\img\LOGO-PIX.png")
OUT = HERE / "output"
OUT.mkdir(exist_ok=True)
PDF_PATH = OUT / "Contrato_Consultoria_Agricola_Safra_2025-2026_Sonia_Bigati.pdf"

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

# ======== ESTILOS =========
styles = getSampleStyleSheet()

s_title = ParagraphStyle("title", parent=styles["Heading1"],
    fontName="Helvetica-Bold", fontSize=16, textColor=WHITE,
    alignment=TA_CENTER, leading=20, spaceAfter=4)
s_subtitle = ParagraphStyle("subt", parent=styles["Normal"],
    fontName="Helvetica", fontSize=10, textColor=WHITE,
    alignment=TA_CENTER, leading=13)
s_h1 = ParagraphStyle("h1", parent=styles["Heading2"],
    fontName="Helvetica-Bold", fontSize=11, textColor=DARK,
    alignment=TA_LEFT, leading=13, spaceBefore=6, spaceAfter=3)
s_h2 = ParagraphStyle("h2", parent=styles["Heading3"],
    fontName="Helvetica-Bold", fontSize=10, textColor=TEAL_DARK,
    alignment=TA_LEFT, leading=12.5, spaceBefore=4, spaceAfter=2)
s_body = ParagraphStyle("body", parent=styles["Normal"],
    fontName="Helvetica", fontSize=10, textColor=GRAY_TXT,
    alignment=TA_JUSTIFY, leading=14, spaceAfter=4)
s_body_c = ParagraphStyle("bodyc", parent=s_body, alignment=TA_CENTER)
s_clause = ParagraphStyle("clause", parent=s_body,
    firstLineIndent=0, spaceBefore=6, spaceAfter=4)
s_small = ParagraphStyle("small", parent=styles["Normal"],