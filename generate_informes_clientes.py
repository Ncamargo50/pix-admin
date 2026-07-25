#!/usr/bin/env python3
"""
Generate professional PDF reports for Pixadvisor clients:
1. Valdemar Pereira - Nematode Analysis + Technical Recommendation
2. Donizete Fernandes - Fertilizer Analysis Technical Comment
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import os

# ── Brand Colors ──
PRIMARY = HexColor('#0D9488')
PRIMARY_LIGHT = HexColor('#14B8A6')
PRIMARY_DARK = HexColor('#0F766E')
ACCENT = HexColor('#7FD633')
DARK = HexColor('#0F172A')
DARK_800 = HexColor('#1E293B')
SURFACE = HexColor('#F8FAFC')
BORDER = HexColor('#E2E8F0')
TEXT_COLOR = HexColor('#1E293B')
TEXT_MUTED = HexColor('#64748B')
RED_ALERT = HexColor('#DC2626')
AMBER = HexColor('#D97706')
AMBER_LIGHT = HexColor('#FEF3C7')
RED_LIGHT = HexColor('#FEE2E2')
GREEN_LIGHT = HexColor('#DCFCE7')
BLUE_LIGHT = HexColor('#DBEAFE')

BASE_DIR = r'D:\PIXADVISOR_AGENT_WORKSPACE'
LOGO_PATH = os.path.join(BASE_DIR, 'pixadvisor-website', 'img', 'logo.png')

WIDTH, HEIGHT = A4


def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'BrandTitle', parent=styles['Title'],
        fontSize=18, leading=22, textColor=white,
        fontName='Helvetica-Bold', alignment=TA_LEFT,
        spaceAfter=2*mm
    ))
    styles.add(ParagraphStyle(
        'BrandSubtitle', parent=styles['Normal'],
        fontSize=11, leading=14, textColor=HexColor('#A7F3D0'),
        fontName='Helvetica', alignment=TA_LEFT
    ))
    styles.add(ParagraphStyle(
        'SectionTitle', parent=styles['Heading1'],
        fontSize=13, leading=16, textColor=PRIMARY_DARK,
        fontName='Helvetica-Bold', spaceBefore=8*mm, spaceAfter=4*mm,
        borderPadding=(0, 0, 2, 0)
    ))
    styles.add(ParagraphStyle(
        'SubSection', parent=styles['Heading2'],
        fontSize=11, leading=14, textColor=DARK_800,
        fontName='Helvetica-Bold', spaceBefore=5*mm, spaceAfter=3*mm
    ))
    styles.add(ParagraphStyle(
        'BodyText2', parent=styles['Normal'],
        fontSize=9, leading=13, textColor=TEXT_COLOR,
        fontName='Helvetica', alignment=TA_JUSTIFY,
        spaceAfter=2*mm
    ))
    styles.add(ParagraphStyle(
        'BulletItem', parent=styles['Normal'],
        fontSize=9, leading=13, textColor=TEXT_COLOR,
        fontName='Helvetica', alignment=TA_LEFT,
        leftIndent=8*mm, bulletIndent=3*mm, spaceAfter=1.5*mm
    ))
    styles.add(ParagraphStyle(
        'AlertText', parent=styles['Normal'],
        fontSize=9, leading=13, textColor=RED_ALERT,
        fontName='Helvetica-Bold', alignment=TA_LEFT,
        spaceAfter=2*mm
    ))
    styles.add(ParagraphStyle(
        'SmallText', parent=styles['Normal'],
        fontSize=7.5, leading=10, textColor=TEXT_MUTED,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontSize=7, leading=9, textColor=white,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontSize=7.5, leading=10, textColor=TEXT_COLOR,
        fontName='Helvetica', alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'ClientInfo', parent=styles['Normal'],
        fontSize=9.5, leading=13, textColor=DARK_800,
        fontName='Helvetica'
    ))
    styles.add(ParagraphStyle(
        'RecommendTitle', parent=styles['Normal'],
        fontSize=10, leading=13, textColor=PRIMARY_DARK,
        fontName='Helvetica-Bold', spaceBefore=4*mm, spaceAfter=2*mm
    ))
    return styles


def header_footer(canvas, doc, title_text, subtitle_text):
    """Draw branded header and footer on every page."""
    canvas.saveState()

    # ── Header bar ──
    header_h = 28*mm
    canvas.setFillColor(DARK)
    canvas.rect(0, HEIGHT - header_h, WIDTH, header_h, fill=1, stroke=0)
    # Accent line
    canvas.setFillColor(ACCENT)
    canvas.rect(0, HEIGHT - header_h, WIDTH, 1.2*mm, fill=1, stroke=0)
    # Gradient overlay
    canvas.setFillColor(PRIMARY_DARK)
    canvas.setFillAlpha(0.3)
    canvas.rect(0, HEIGHT - header_h, WIDTH * 0.4, header_h, fill=1, stroke=0)
    canvas.setFillAlpha(1.0)

    # Logo
    if os.path.exists(LOGO_PATH):
        try:
            canvas.drawImage(LOGO_PATH, 10*mm, HEIGHT - 24*mm, width=28*mm, height=18*mm,
                           preserveAspectRatio=True, mask='auto')
        except:
            pass

    # Title
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 13)
    canvas.drawString(42*mm, HEIGHT - 14*mm, 'Pixadvisor Agricultura de Precision')
    canvas.setFillColor(HexColor('#A7F3D0'))
    canvas.setFont('Helvetica', 9)
    canvas.drawString(42*mm, HEIGHT - 20*mm, title_text)

    # Date right
    canvas.setFillColor(HexColor('#94A3B8'))
    canvas.setFont('Helvetica', 7.5)
    canvas.drawRightString(WIDTH - 12*mm, HEIGHT - 14*mm, subtitle_text)

    # ── Footer ──
    footer_y = 10*mm
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(15*mm, footer_y + 4*mm, WIDTH - 15*mm, footer_y + 4*mm)

    canvas.setFillColor(TEXT_MUTED)
    canvas.setFont('Helvetica', 6.5)
    canvas.drawString(15*mm, footer_y,
        'Pixadvisor Agricultura de Precision | Bolivia | pixadvisor.network')
    canvas.drawRightString(WIDTH - 15*mm, footer_y, f'Pagina {doc.page}')

    # Accent bottom line
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, WIDTH, 1.5*mm, fill=1, stroke=0)

    canvas.restoreState()


def make_client_info_table(data_pairs):
    """Create a styled client info box."""
    rows = []
    for label, value in data_pairs:
        rows.append([
            Paragraph(f'<b>{label}:</b>', ParagraphStyle('l', fontSize=8.5, textColor=TEXT_MUTED, fontName='Helvetica-Bold')),
            Paragraph(str(value), ParagraphStyle('v', fontSize=9, textColor=DARK_800, fontName='Helvetica'))
        ])

    t = Table(rows, colWidths=[35*mm, 130*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (0, -1), 4*mm),
        ('BACKGROUND', (0, 0), (-1, -1), SURFACE),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, BORDER),
    ]))
    return t


def colored_box(text, bg_color, text_color, styles):
    """Create a colored alert/info box."""
    box_style = ParagraphStyle('box', fontSize=9, leading=13, textColor=text_color,
                                fontName='Helvetica', alignment=TA_LEFT)
    content = [[Paragraph(text, box_style)]]
    t = Table(content, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 0.5, text_color),
        ('TOPPADDING', (0, 0), (-1, -1), 4*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4*mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 4*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4*mm),
    ]))
    return t


# ═══════════════════════════════════════════════════════════════
#  PDF 1: VALDEMAR PEREIRA - NEMATODE ANALYSIS
# ═══════════════════════════════════════════════════════════════

def generate_nematode_report():
    output_path = os.path.join(BASE_DIR, 'Informe_Nematodos_Valdemar_Pereira.pdf')
    styles = get_styles()

    def on_page(canvas, doc):
        header_footer(canvas, doc,
            'Informe Tecnico - Analisis Nematologico',
            'Fecha: 23/03/2026')

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=32*mm, bottomMargin=18*mm,
        leftMargin=15*mm, rightMargin=15*mm
    )

    story = []

    # ── Client Info ──
    story.append(Spacer(1, 2*mm))
    story.append(make_client_info_table([
        ('Cliente', 'Valdemar Pereira'),
        ('Propiedad', 'Hacienda Campo Verde'),
        ('Lote', '2B (Puntos P1 a P5)'),
        ('O.S.', '246877'),
        ('Tipo de Muestra', 'Solo'),
        ('Servicio', 'Identificacion y Conteo de Nematodos - SP'),
    ]))

    # ── Results Table ──
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('RESULTADOS DE ANALISIS NEMATOLOGICO', styles['SectionTitle']))

    # Build table with wrapped headers
    th = styles['TableHeader']
    tc = styles['TableCell']

    header_row = [
        Paragraph('<b>Punto</b>', th),
        Paragraph('<b>H. dihystera<br/>Raiz</b>', th),
        Paragraph('<b>H. dihystera<br/>Suelo</b>', th),
        Paragraph('<b>H. erythrinae<br/>Raiz</b>', th),
        Paragraph('<b>M. javanica<br/>Raiz</b>', th),
        Paragraph('<b>M. spp.<br/>Suelo</b>', th),
        Paragraph('<b>Ovos<br/>Raiz</b>', th),
        Paragraph('<b>P. brachyurus<br/>Raiz</b>', th),
    ]

    def cell(val, alert=False):
        if alert:
            s = ParagraphStyle('alert_cell', fontSize=8, leading=10, textColor=RED_ALERT,
                             fontName='Helvetica-Bold', alignment=TA_CENTER)
        else:
            s = tc
        return Paragraph(str(val), s)

    data = [
        header_row,
        [cell('P1'), cell('-'), cell('30'), cell('480'), cell('-'), cell('40'), cell('-'), cell('270')],
        [cell('P2'), cell('20'), cell('-'), cell('-'), cell('-'), cell('-'), cell('-'), cell('170')],
        [cell('P3'), cell('40'), cell('120'), cell('-'), cell('1.800', True), cell('240', True), cell('80'), cell('120')],
        [cell('P4'), cell('-'), cell('400'), cell('-'), cell('-'), cell('-'), cell('-'), cell('50')],
        [cell('P5'), cell('-'), cell('60'), cell('-'), cell('-'), cell('0'), cell('-'), cell('-')],
    ]

    col_w = [20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 18*mm, 22*mm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Body
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, SURFACE]),
        # P3 row highlight (row index 3)
        ('BACKGROUND', (0, 3), (-1, 3), RED_LIGHT),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.8, PRIMARY_DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        # Point column
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (0, -1), HexColor('#F0FDFA')),
    ]))
    story.append(t)

    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<i>Unidades: Raiz = ind./10g | Suelo = ind./250cm<super>3</super> | (-) = No detectado</i>',
        styles['SmallText']))

    # ── Alert Box for P3 ──
    story.append(Spacer(1, 5*mm))
    story.append(colored_box(
        '<b>ALERTA CRITICO - PUNTO P3:</b> <i>Meloidogyne javanica</i> con 1.800 ind./10g raiz. '
        'Nivel EXTREMADAMENTE ALTO (umbral critico &gt;500 ind.). Poblacion activa confirmada '
        'por presencia de 240 <i>Meloidogyne</i> spp. en suelo y 80 huevos en raiz.',
        RED_LIGHT, RED_ALERT, styles))

    # ── Technical Analysis ──
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('ANALISIS TECNICO', styles['SectionTitle']))

    analysis_items = [
        ('<b>Punto P3 - Nivel Critico:</b> La presencia de <i>M. javanica</i> a 1.800 ind./10g de raiz '
         'representa una infestacion severa que compromete seriamente el rendimiento del cultivo. '
         'La deteccion de 240 <i>Meloidogyne</i> spp./250cm<super>3</super> en suelo y 80 huevos/10g raiz '
         'confirma reproduccion activa y ciclo establecido.'),

        ('<b><i>Helicotylenchus dihystera</i> (presente en todos los puntos):</b> Poblaciones de 30 a 480 '
         'ind./250cm<super>3</super> en suelo. P4 presenta el mayor nivel (400/250cm<super>3</super>). Nematodo de menor '
         'patogenicidad directa, pero indica alta presion fitoparasitaria en el area.'),

        ('<b><i>Pratylenchus brachyurus</i> (P1 a P4):</b> Detectado en raiz de 4 de 5 puntos (50-270 ind./10g). '
         'P1 con mayor poblacion (270 ind./10g). Es un patogeno clave en soja y maiz, causante de lesiones '
         'radiculares que reducen absorcion de agua y nutrientes.'),

        ('<b>Punto P5 - Referencia:</b> El punto mas limpio con solo 60 <i>H. dihystera</i>/250cm<super>3</super> '
         'en suelo. Puede servir como area testigo para comparacion de manejos.'),

        ('<b>Diagnostico General:</b> Complejo nematologico mixto dominado por <i>Meloidogyne</i> + '
         '<i>Pratylenchus</i>, combinacion clasica en sistemas soja-maiz que causa perdidas de rendimiento '
         'del 15-40% si no se maneja adecuadamente.'),
    ]

    for item in analysis_items:
        story.append(Paragraph(item, styles['BulletItem']))

    # ── Technical Recommendation ──
    story.append(PageBreak())
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('RECOMENDACION TECNICA', styles['SectionTitle']))

    # Recommendation 1
    story.append(colored_box(
        '<b>1. MANEJO URGENTE EN P3 - <i>Meloidogyne javanica</i> (Nivel Critico)</b>',
        HexColor('#FEF2F2'), RED_ALERT, styles))
    story.append(Spacer(1, 1*mm))
    rec1_items = [
        'Rotacion con cultivos no hospederos: <i>Crotalaria spectabilis</i> o <i>C. ochroleuca</i> como cobertura entre zafras',
        'Aplicacion de nematicida biologico: <i>Purpureocillium lilacinum</i> o <i>Pochonia chlamydosporia</i> para parasitar huevos',
        'Considerar nematicida quimico en surco (fluopyram o abamectina) en la proxima siembra',
        'Monitoreo intensivo cada 60 dias para evaluar reduccion poblacional',
    ]
    for r in rec1_items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {r}', styles['BulletItem']))

    # Recommendation 2
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<b>2. MANEJO GENERAL - <i>Pratylenchus brachyurus</i> (P1-P4)</b>',
                          styles['RecommendTitle']))
    rec2_items = [
        'Uso de variedades de soja resistentes/tolerantes a <i>P. brachyurus</i>',
        'Tratamiento de semillas con abamectina + <i>Bacillus</i> spp.',
        'Rotacion con <i>Brachiaria ruziziensis</i> (demostrada reduccion de poblaciones de <i>Pratylenchus</i>)',
    ]
    for r in rec2_items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {r}', styles['BulletItem']))

    # Recommendation 3
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph('<b>3. MANEJO <i>Helicotylenchus</i> (todos los puntos)</b>',
                          styles['RecommendTitle']))
    rec3_items = [
        'Menor patogenicidad directa, pero indicador de alta presion fitoparasitaria',
        'El manejo integrado para <i>Meloidogyne</i> y <i>Pratylenchus</i> controlara indirectamente estas poblaciones',
    ]
    for r in rec3_items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {r}', styles['BulletItem']))

    # Recommendation 4
    story.append(Spacer(1, 4*mm))
    story.append(colored_box(
        '<b>4. ESTRATEGIA INTEGRADA RECOMENDADA (Plan de Manejo)</b>',
        HexColor('#F0FDF4'), PRIMARY_DARK, styles))
    story.append(Spacer(1, 1*mm))

    plan_data = [
        [Paragraph('<b>Accion</b>', th), Paragraph('<b>Detalle</b>', th), Paragraph('<b>Periodo</b>', th)],
        [Paragraph('Cobertura invernal', tc),
         Paragraph('<i>Crotalaria spectabilis</i> (enfasis en P3)', tc),
         Paragraph('Post-cosecha', tc)],
        [Paragraph('Trat. semillas', tc),
         Paragraph('<i>Bacillus subtilis</i> + <i>B. amyloliquefaciens</i> + abamectina', tc),
         Paragraph('Pre-siembra', tc)],
        [Paragraph('Nematicida biologico', tc),
         Paragraph('<i>P. lilacinum</i> o <i>P. chlamydosporia</i> en surco (P3)', tc),
         Paragraph('Siembra', tc)],
        [Paragraph('Rotacion', tc),
         Paragraph('Soja-maiz con <i>Crotalaria</i>/<i>Brachiaria</i> entre zafras', tc),
         Paragraph('Anual', tc)],
        [Paragraph('Monitoreo', tc),
         Paragraph('Analisis nematologico post-cosecha', tc),
         Paragraph('Cada 6 meses', tc)],
    ]
    plan_t = Table(plan_data, colWidths=[35*mm, 95*mm, 30*mm], repeatRows=1)
    plan_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F0FDFA')]),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.8, PRIMARY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(plan_t)

    # Disclaimer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<i>Este informe tecnico es de caracter orientativo. Las recomendaciones deben ser '
        'validadas por un ingeniero agronomo responsable considerando las condiciones '
        'especificas del lote, historico de cultivos y disponibilidad de insumos.</i>',
        styles['SmallText']))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '<b>Laboratorio:</b> IBRA Megalab | Resp. Tecnico: Carlos Eduardo Prieto - CRQ 04261966',
        styles['SmallText']))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'[OK] Nematode report: {output_path}')
    return output_path


# ═══════════════════════════════════════════════════════════════
#  PDF 2: DONIZETE FERNANDES - FERTILIZER ANALYSIS
# ═══════════════════════════════════════════════════════════════

def generate_fertilizer_report():
    output_path = os.path.join(BASE_DIR, 'Informe_Fertilizantes_Donizete_Fernandes_v2.pdf')
    styles = get_styles()

    def on_page(canvas, doc):
        header_footer(canvas, doc,
            'Informe Tecnico - Analisis de Fertilizantes e Insumos',
            'O.S.: 247231 | Lab: 06/03/2026')

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=32*mm, bottomMargin=18*mm,
        leftMargin=15*mm, rightMargin=15*mm
    )

    story = []
    th = styles['TableHeader']
    tc = styles['TableCell']

    # Compact cell styles for dense tables
    tc_left = ParagraphStyle('tc_left', fontSize=7, leading=9, textColor=TEXT_COLOR,
                              fontName='Helvetica', alignment=TA_LEFT)
    tc_val = ParagraphStyle('tc_val', fontSize=7, leading=9, textColor=DARK_800,
                             fontName='Helvetica-Bold', alignment=TA_CENTER)
    th_compact = ParagraphStyle('th_compact', fontSize=6.5, leading=8, textColor=white,
                                 fontName='Helvetica-Bold', alignment=TA_CENTER)

    # ── Client Info ──
    story.append(Spacer(1, 2*mm))
    story.append(make_client_info_table([
        ('Cliente', 'Donizete Fernandes'),
        ('O.S.', '247231'),
        ('Entrada Lab', '06/03/2026'),
        ('Periodo de Ensayo', '18/03/2026 a 26/03/2026'),
        ('Laboratorio', 'IBRA Megalab'),
    ]))

    # ── Helper: compact 2-column nutrient table (side by side) ──
    def nutrient_table_compact(data_list, title, sample_id, tipo):
        elements = []
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(
            f'<b>{title}</b> <font color="#64748B" size="7">| {tipo} | Amostra {sample_id}</font>',
            ParagraphStyle('sec', fontSize=9, leading=12, textColor=DARK_800,
                           fontName='Helvetica-Bold', spaceBefore=1*mm, spaceAfter=1.5*mm)))

        # Split data into 2 columns
        mid = (len(data_list) + 1) // 2
        col1 = data_list[:mid]
        col2 = data_list[mid:]

        rows = [[Paragraph('<b>Parametro</b>', th_compact), Paragraph('<b>Resultado</b>', th_compact),
                 Paragraph('<b>Parametro</b>', th_compact), Paragraph('<b>Resultado</b>', th_compact)]]
        for i in range(mid):
            r = [Paragraph(col1[i][0], tc_left), Paragraph(f'{col1[i][1]} {col1[i][2]}', tc_val)]
            if i < len(col2):
                r += [Paragraph(col2[i][0], tc_left), Paragraph(f'{col2[i][1]} {col2[i][2]}', tc_val)]
            else:
                r += [Paragraph('', tc_left), Paragraph('', tc_val)]
            rows.append(r)

        t = Table(rows, colWidths=[42*mm, 22*mm, 42*mm, 22*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_DARK),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, SURFACE]),
            ('GRID', (0, 0), (-1, -1), 0.3, BORDER),
            ('BOX', (0, 0), (-1, -1), 0.5, PRIMARY_DARK),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5*mm),
            # Divider between left/right halves
            ('LINEAFTER', (1, 0), (1, -1), 1, PRIMARY_DARK),
        ]))
        elements.append(t)
        return elements

    # ── 1. Rocha Fosfatica ──
    story.extend(nutrient_table_compact([
        ('Nitrogeno Total', '0,28', '%'),
        ('P sol. CNA + agua', '4,09', '%'),
        ('P sol. ac. citrico 2%', '6,09', '%'),
        ('P sol. en agua', '0,08', '%'),
        ('Potasio (sol. agua)', '0,02', '%'),
        ('Calcio Total', '24,20', '%'),
        ('Magnesio Total', '0,60', '%'),
        ('Azufre', '0,09', '%'),
        ('Hierro Total', '4,01', '%'),
        ('Aluminio Total', '0,71', '%'),
        ('Manganeso Total', '0,25', '%'),
        ('Zinc Total', '0,06', '%'),
        ('Sodio Total', '0,16', '%'),
        ('Boro', '0,00', '%'),
        ('Cobre Total', '0', 'ppm'),
    ], 'Rocha Fosfatica #32', '052456/26', 'Fertilizante Mineral'))

    # ── 2. Gesso Agricola ──
    story.extend(nutrient_table_compact([
        ('Nitrogeno', '0,12', '%'),
        ('Fosforo Total', '0,16', '%'),
        ('P sol. ac. citrico 2%', '0,08', '%'),
        ('P sol. en agua', '0,00', '%'),
        ('Potasio', '0,03', '%'),
        ('Calcio', '15,94', '%'),
        ('Magnesio', '0,17', '%'),
        ('Azufre', '16,93', '%'),
        ('Hierro', '0,05', '%'),
        ('Zinc', '88,72', 'ppm'),
        ('Manganeso', '21,14', 'ppm'),
        ('Aluminio', '0', 'ppm'),
        ('Sodio', '0,02', '%'),
        ('Boro', '0,00', '%'),
        ('Cobre', '0', 'ppm'),
        ('Materia Organica', '7,39', '%'),
        ('Humedad (65C)', '0,04', '%'),
        ('Cenizas', '92,61', '%'),
    ], 'Gesso Agricola', '052455/26', 'Condicionador de Solo'))

    # ── 3. Compostaje Muestra 1 ──
    story.extend(nutrient_table_compact([
        ('Nitrogeno', '0,31', '%'),
        ('Fosforo Total', '1,92', '%'),
        ('P sol. ac. citrico 2%', '1,28', '%'),
        ('P sol. en agua', '1,09', '%'),
        ('Potasio', '1,70', '%'),
        ('Calcio', '4,17', '%'),
        ('Magnesio', '0,57', '%'),
        ('Azufre', '0,82', '%'),
        ('Hierro', '1,34', '%'),
        ('Zinc', '164,37', 'ppm'),
        ('Manganeso', '424,23', 'ppm'),
        ('Aluminio', '1,79', '%'),
        ('Sodio', '0,16', '%'),
        ('Boro', '0,01', '%'),
        ('Cobre', '0', 'ppm'),
        ('pH (CaCl2)', '7,30', '-'),
    ], 'Compostaje - Muestra 1 (07/02/26)', '052453/26', 'Fertilizante Organico'))

    # ── 4. Compostaje Muestra 2 ──
    story.extend(nutrient_table_compact([
        ('Nitrogeno', '0,24', '%'),
        ('Fosforo Total', '2,16', '%'),
        ('P sol. ac. citrico 2%', '1,17', '%'),
        ('P sol. en agua', '1,12', '%'),
        ('Potasio', '1,78', '%'),
        ('Calcio', '3,25', '%'),
        ('Magnesio', '0,37', '%'),
        ('Azufre', '1,09', '%'),
        ('Hierro', '1,43', '%'),
        ('Zinc', '185,01', 'ppm'),
        ('Manganeso', '463,87', 'ppm'),
        ('Aluminio', '1,70', '%'),
        ('Sodio', '0,17', '%'),
        ('Boro', '0,01', '%'),
        ('Cobre', '0', 'ppm'),
        ('pH (CaCl2)', '7,30', '-'),
    ], 'Compostaje - Muestra 2 (07/02/26)', '052454/26', 'Fertilizante Organico'))

    # ── Technical Comment ──
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph('COMENTARIO TECNICO', styles['SectionTitle']))

    # Rocha Fosf.
    story.append(Paragraph('<b>ROCHA FOSFATICA #32</b>', styles['RecommendTitle']))
    rocha_items = [
        'Fuente de fosforo de liberacion lenta. El P soluble en acido citrico (6,09%) es superior '
        'al P soluble en CNA+agua (4,09%), indicando buena reactividad para suelos acidos donde '
        'la solubilizacion sera gradual y eficiente.',
        'Alto contenido de Calcio (24,2%) la convierte en fuente secundaria importante de Ca, '
        'complementando la nutricion del cultivo.',
        'Hierro elevado (4,01%) - considerar este aporte en suelos con exceso de Fe para evitar '
        'antagonismos con Mn y Zn.',
        'Baja solubilidad en agua (0,08%) confirma perfil de liberacion gradual, ideal para '
        'cultivos perennes y aplicaciones de base.',
    ]
    for r in rocha_items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {r}', styles['BulletItem']))

    # Gesso
    story.append(Paragraph('<b>GESSO AGRICOLA</b>', styles['RecommendTitle']))
    gesso_items = [
        'Producto adecuado con Ca 15,94% y S 16,93%, dentro de los parametros esperados para '
        'yeso agricola de buena calidad.',
        'Relacion Ca:S de aproximadamente 0,94, cercana al ideal teorico (1:1 en CaSO4.2H2O).',
        'Contenido de Aluminio no detectable (0 ppm) - seguro para uso, no aporta Al toxico al suelo.',
        'Materia Organica de 7,39% es inusualmente alto para un yeso puro; puede indicar mezcla '
        'con material organico o proceso de produccion diferenciado.',
        'Excelente para correccion de subsuelo (capa 20-40 cm), aporte de azufre y mejora de la '
        'relacion Ca/Mg en profundidad.',
    ]
    for r in gesso_items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {r}', styles['BulletItem']))

    # Compostaje
    story.append(Paragraph('<b>COMPOSTAJE (Muestras 1 y 2)</b>', styles['RecommendTitle']))
    comp_items = [
        'Ambas muestras presentan composicion muy similar, indicando buena homogeneidad del '
        'proceso de compostaje.',
        'pH 7,3 en ambas muestras: ligeramente alcalino, ideal para aplicacion en suelos acidos '
        'contribuyendo a la neutralizacion de la acidez.',
        'Buena relacion NPK aproximada de 0,3 : 2,0 : 1,7 - rico en Fosforo y Potasio, '
        'complemento ideal para fuentes nitrogenadas.',
        'Manganeso elevado (424-464 ppm) y Zinc moderado (164-185 ppm) representan un aporte '
        'significativo de micronutrientes que puede reducir la necesidad de aplicaciones foliares.',
        'Aluminio elevado (1,7-1,8%) requiere atencion en suelos que ya presentan problemas '
        'de toxicidad por Al; monitorear saturacion de Al en el complejo de intercambio.',
        'La Muestra 2 presenta ligeramente mas P (2,16 vs 1,92%) y K (1,78 vs 1,70%), '
        'sin diferencias significativas para la recomendacion practica.',
        'Ambos productos son aptos como fertilizante organico con buen aporte de macro y '
        'micronutrientes para cultivos anuales y perennes.',
    ]
    for r in comp_items:
        story.append(Paragraph(f'<bullet>&bull;</bullet> {r}', styles['BulletItem']))

    # Summary box
    story.append(Spacer(1, 3*mm))
    story.append(colored_box(
        '<b>RESUMEN:</b> Los cuatro insumos analizados presentan calidad adecuada para uso agricola. '
        'La Rocha Fosfatica #32 destaca como fuente de P de liberacion lenta + Ca. El Gesso Agricola '
        'cumple parametros para correccion de subsuelo. Los compostajes son homogeneos y ricos en '
        'P, K y micronutrientes, aptos como fertilizante organico.',
        HexColor('#F0FDFA'), PRIMARY_DARK, styles))

    # Disclaimer
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 1.5*mm))
    story.append(Paragraph(
        '<i>Este informe tecnico es de caracter orientativo. Los resultados corresponden '
        'exclusivamente a las muestras analizadas. Metodos segun MAPA (Ministerio da Agricultura).</i>',
        styles['SmallText']))
    story.append(Spacer(1, 1.5*mm))
    story.append(Paragraph(
        '<b>Laboratorio:</b> IBRA Megalab | Resp. Tecnico: Carlos Eduardo Prieto - CRQ 04261966',
        styles['SmallText']))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'[OK] Fertilizer report: {output_path}')
    return output_path


# ── Main ──
if __name__ == '__main__':
    print('Generating reports...')
    p1 = generate_nematode_report()
    p2 = generate_fertilizer_report()
    print(f'\nDone! Files created:')
    print(f'  1. {p1}')
    print(f'  2. {p2}')
