"""Informe PDF del cliente. Autocontenido: corre en la nube sin nada instalado a mano.

La marca va INLINE a proposito. La plantilla de marca vive en una skill del Escritorio
del usuario, y un runner de GitHub Actions no la tiene: si el informe dependiera de esa
ruta, la corrida programada fallaria todas las noches y el cliente no recibiria nada.

QUE DICE EL INFORME
-------------------
Lo mismo que el motor puede sostener, ni mas ni menos: a que lotes ir, en que orden, con
que fecha de imagen, y **que parte del campo no se pudo mirar**. Un informe que calla la
omision y publica un verde destruye la confianza que uno que dice "no pude ver" conserva.
"""
import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

AZUL = colors.HexColor('#1E40AF')
AZUL_D = colors.HexColor('#152C7A')
TEAL = colors.HexColor('#0D9488')
LIMA = colors.HexColor('#7FD633')
TEAL_BG = colors.HexColor('#EAF6F4')
GRIS = colors.HexColor('#F5F7FA')
GRIS_M = colors.HexColor('#DCE3EA')
ROJO = colors.HexColor('#B4322A')
AMBAR = colors.HexColor('#B4740A')
VERDE = colors.HexColor('#1B7A1B')

COLOR_ESTADO = {'ATENCION': ROJO, 'VIGILANCIA': AMBAR,
                'SIN SEÑAL': VERDE, 'SIN DATO': colors.HexColor('#6D8783')}


def _estilos():
    ss = getSampleStyleSheet()
    def S(n, **kw):
        kw.setdefault('fontName', 'Helvetica')
        ss.add(ParagraphStyle(n, parent=ss['Normal'], **kw))
    S('Body', fontSize=9.5, leading=13.5, textColor=colors.HexColor('#333333'))
    S('H1', fontSize=14, textColor=AZUL, fontName='Helvetica-Bold', spaceBefore=13,
      spaceAfter=5, leading=17)
    S('H2', fontSize=10.5, textColor=TEAL, fontName='Helvetica-Bold', spaceBefore=8,
      spaceAfter=3)
    S('Note', fontSize=8, leading=11, textColor=colors.HexColor('#5A6B79'))
    S('Cell', fontSize=8.6, leading=11.5, textColor=colors.HexColor('#333333'))
    S('CellB', fontSize=8.6, leading=11.5, textColor=colors.white,
      fontName='Helvetica-Bold')
    S('Big', fontSize=8.6, leading=11.5, fontName='Helvetica-Bold')
    return ss


def _cabecera(c, doc, titulo, sub):
    c.saveState()
    c.setFillColor(AZUL_D); c.rect(0, A4[1] - 2.5 * cm, A4[0], 2.5 * cm, fill=1, stroke=0)
    c.setFillColor(LIMA); c.rect(0, A4[1] - 2.62 * cm, A4[0], 0.12 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont('Helvetica-Bold', 13)
    c.drawString(2 * cm, A4[1] - 1.35 * cm, titulo)
    c.setFont('Helvetica', 8.5); c.setFillColor(colors.HexColor('#BFE6E1'))
    c.drawString(2 * cm, A4[1] - 1.95 * cm, sub)
    c.setFillColor(AZUL_D); c.rect(0, 0, A4[0], 0.8 * cm, fill=1, stroke=0)
    c.setFillColor(LIMA); c.rect(0, 0.8 * cm, A4[0], 0.08 * cm, fill=1, stroke=0)
    c.setFont('Helvetica-Bold', 7); c.setFillColor(colors.white)
    c.drawString(2 * cm, 0.3 * cm, 'PIXADVISOR  ·  AGRICULTURA DE PRECISION')
    c.setFont('Helvetica', 7)
    c.drawRightString(A4[0] - 2 * cm, 0.3 * cm, 'Pag. %d' % doc.page)
    c.restoreState()


def generar(cliente, sitio, rank, ruta, fecha, cobertura=None, huecos=None):
    """rank: DataFrame del ranking SIN cortar por K (para poder declarar el total)."""
    ss = _estilos()
    P = lambda t, s='Body': Paragraph(t, ss[s])
    st = []

    alertados = rank[rank['estado'].isin(('ATENCION', 'VIGILANCIA'))]
    sin_dato = int((rank['estado'] == 'SIN DATO').sum())
    n_at = int((rank['estado'] == 'ATENCION').sum())
    n_vi = int((rank['estado'] == 'VIGILANCIA').sum())

    st.append(Spacer(1, 0.5 * cm))

    # --- lo primero es el veredicto, no la metodologia ---
    if alertados.empty:
        st.append(_callout(P, 'Esta semana no hay lotes fuera de control.',
                           'De los %d lotes evaluados, ninguno se aparta de su cohorte. '
                           'No hay a donde mandar al tecnico por este criterio.'
                           % len(rank), VERDE))
    else:
        st.append(_callout(
            P, '%d lote(s) para recorrer esta semana' % len(alertados),
            '%d en ATENCION y %d en VIGILANCIA, sobre %d lotes evaluados. Van ordenados '
            'por prioridad: si no se alcanza a recorrer todos, empezar por el primero.'
            % (n_at, n_vi, len(rank)), ROJO if n_at else AMBAR))

    st.append(Spacer(1, 0.35 * cm))

    # --- la tabla ---
    if not alertados.empty:
        st.append(P('A donde ir', 'H1'))
        filas = [[P('#', 'CellB'), P('Lote', 'CellB'), P('Estado', 'CellB'),
                  P('Area', 'CellB'), P('Ultima imagen', 'CellB')]]
        for _, r in alertados.iterrows():
            filas.append([
                P(str(int(r['orden'])), 'Cell'),
                P('<b>%s</b>' % r['lote_id'], 'Cell'),
                P('<font color="#%s"><b>%s</b></font>'
                  % (COLOR_ESTADO.get(r['estado'], colors.black).hexval()[2:],
                     r['estado']), 'Cell'),
                P('%.1f ha' % r['area_ha'], 'Cell'),
                P('hace %d dia(s)' % int(r['dias_atras']), 'Cell')])
        t = Table(filas, colWidths=[1.1 * cm, 4.6 * cm, 3.2 * cm, 2.6 * cm, 5.5 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TEAL),
            ('LINEBELOW', (0, 0), (-1, 0), 1.3, LIMA),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TEAL_BG]),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, GRIS_M),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 7)]))
        st.append(t)
        st.append(P('Los focos van tambien en el GeoJSON adjunto, para navegar con la '
                    'app PIX Scout.', 'Note'))

    # --- COBERTURA: lo que no se pudo mirar. Va SIEMPRE, aunque este limpio ---
    st.append(P('Cobertura del analisis', 'H1'))
    lineas = []
    if sin_dato:
        lineas.append('<b>%d lote(s) SIN OBSERVACION reciente</b> — no se pudieron '
                      'evaluar y no estan en la lista de arriba. No estan sanos: no se '
                      'miraron.' % sin_dato)
    if cobertura is not None:
        lineas.append('Observaciones plenas en la ventana: <b>%.0f%%</b> de las '
                      'disponibles.' % (100 * cobertura))
    if huecos:
        lineas.append('Hueco maximo declarado para la zona: <b>%d dias</b> sin escena '
                      'util.' % huecos)
    if not lineas:
        lineas.append('Todos los lotes tuvieron observacion reciente.')
    for ln in lineas:
        st.append(P('· ' + ln))

    # --- limites, en el mismo documento ---
    st.append(P('Lo que este informe no dice', 'H1'))
    st.append(P(
        'Este es un producto de <b>priorizacion de scouting</b>, no un diagnostico. '
        'El satelite detecta que un lote se aparta de sus vecinos de la misma cohorte; '
        '<b>no dice la causa</b>. Un indice bajo es un sintoma inespecifico: suelo, '
        'nitrogeno, agua o enfermedad dan la misma firma. La causa la confirma el '
        'tecnico en el lote.'))
    st.append(P(
        'No detecta chinches ni roya asiatica a escala de lote comercial, y no ve el '
        'daño antes de que sea visible.', 'Note'))

    doc = SimpleDocTemplate(ruta, pagesize=A4, topMargin=3.2 * cm, bottomMargin=1.6 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            title='Monitoreo %s %s' % (cliente.titulo, fecha),
                            author='Pixadvisor Agricultura de Precision')
    cab = lambda c, d: _cabecera(c, d, cliente.titulo,
                                 '%s · escena Sentinel-2 del %s' % (sitio.titulo, fecha))
    doc.build(st, onFirstPage=cab, onLaterPages=cab)
    return ruta


def _callout(P, titulo, texto, color):
    t = Table([[P('<font color="white"><b>%s</b></font>' % titulo, 'Cell')],
               [P('<font color="white">%s</font>' % texto, 'Cell')]],
              colWidths=[15 * cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('LINEBEFORE', (0, 0), (0, -1), 4, LIMA),
        ('LEFTPADDING', (0, 0), (-1, -1), 11), ('RIGHTPADDING', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (0, 0), 9), ('BOTTOMPADDING', (0, -1), (-1, -1), 9)]))
    return KeepTogether(t)
