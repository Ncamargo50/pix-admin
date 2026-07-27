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
import math
import os
from datetime import date

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
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


# ---------------------------------------------------------------------------
# MAPA DEL LOTE. Vectorial a proposito: un mapa que depende de bajar un raster de
# Earth Engine agrega un modo de falla nocturno al unico entregable que ve el
# cliente. El contorno del lote y los focos son lo que el tecnico necesita para
# ubicarse; el fondo de color real se puede sumar despues sin cambiar nada de esto.
# ---------------------------------------------------------------------------
MAPA_ANCHO = 8.4 * cm
MAPA_ALTO = 5.6 * cm
_MARGEN = 8


def _anillos(geom):
    """Anillos exteriores de un Polygon o MultiPolygon, en [lon, lat]."""
    if not geom:
        return []
    t = geom.get('type')
    if t == 'Polygon':
        return [geom['coordinates'][0]]
    if t == 'MultiPolygon':
        return [p[0] for p in geom['coordinates']]
    return []


def _escala_bonita(m):
    """Un numero redondo de metros que entre en la barra de escala."""
    for v in (1000, 500, 250, 200, 100, 50, 25, 10):
        if v <= m:
            return v
    return max(int(m), 1)


def _mapa_lote(geom_lote, focos, ancho=MAPA_ANCHO, alto=MAPA_ALTO):
    """Dibujo del lote con sus focos numerados. None si no hay geometria."""
    anillos = _anillos(geom_lote)
    if not anillos:
        return None
    todos = [p for a in anillos for p in a]
    for f in focos:
        for a in _anillos(f.get('geometry')):
            todos.extend(a)
    lons = [p[0] for p in todos]
    lats = [p[1] for p in todos]
    lon0, lat0 = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
    kx = math.cos(math.radians(lat0))          # los grados de lon se acortan con la lat

    def plano(p):
        return ((p[0] - lon0) * kx, p[1] - lat0)

    xs = [plano(p)[0] for p in todos]
    ys = [plano(p)[1] for p in todos]
    dx, dy = max(max(xs) - min(xs), 1e-9), max(max(ys) - min(ys), 1e-9)
    # Una sola escala para los dos ejes: si se estiraran por separado, el lote
    # saldria deformado y el tecnico no reconoceria su propio campo.
    s = min((ancho - 2 * _MARGEN) / dx, (alto - 2 * _MARGEN - 14) / dy)
    cx = (ancho - dx * s) / 2 - min(xs) * s
    cy = (alto - 14 - dy * s) / 2 - min(ys) * s + 12

    def pt(p):
        x, y = plano(p)
        return [x * s + cx, y * s + cy]

    d = Drawing(ancho, alto)
    d.add(Rect(0, 0, ancho, alto, fillColor=colors.HexColor('#FBFCFD'),
               strokeColor=GRIS_M, strokeWidth=0.6))
    for a in anillos:
        pts = [c for p in a for c in pt(p)]
        d.add(Polygon(pts, fillColor=colors.HexColor('#EAF6F4'),
                      strokeColor=TEAL, strokeWidth=1.1))
    for i, f in enumerate(focos):
        p = f.get('properties', {})
        for a in _anillos(f.get('geometry')):
            pts = [c for q in a for c in pt(q)]
            d.add(Polygon(pts, fillColor=colors.HexColor('#E86A5E'),
                          strokeColor=ROJO, strokeWidth=0.9))
        a0 = _anillos(f.get('geometry'))
        if a0:
            xs_ = [pt(q)[0] for q in a0[0]]
            ys_ = [pt(q)[1] for q in a0[0]]
            d.add(String((min(xs_) + max(xs_)) / 2, max(ys_) + 3,
                         p.get('etiqueta', 'F%d' % (i + 1)), fontSize=7,
                         fontName='Helvetica-Bold', fillColor=ROJO,
                         textAnchor='middle'))
    # Barra de escala: sin esto el mapa no dice si el foco son 20 m o 200.
    m_por_grado = 110540.0
    metros_totales = dy * m_por_grado
    if metros_totales > 0:
        objetivo = _escala_bonita(metros_totales / 3)
        largo = objetivo / m_por_grado * s
        y0 = 7
        d.add(Line(_MARGEN, y0, _MARGEN + largo, y0, strokeColor=AZUL_D,
                   strokeWidth=1.2))
        d.add(Line(_MARGEN, y0 - 2, _MARGEN, y0 + 2, strokeColor=AZUL_D,
                   strokeWidth=1.2))
        d.add(Line(_MARGEN + largo, y0 - 2, _MARGEN + largo, y0 + 2,
                   strokeColor=AZUL_D, strokeWidth=1.2))
        d.add(String(_MARGEN + largo + 4, y0 - 2.5, '%d m' % objetivo, fontSize=6.5,
                     fillColor=colors.HexColor('#5A6B79')))
    d.add(String(ancho - _MARGEN, alto - _MARGEN - 4, 'N', fontSize=7.5,
                 fontName='Helvetica-Bold', fillColor=colors.HexColor('#5A6B79'),
                 textAnchor='end'))
    d.add(Line(ancho - _MARGEN - 3.2, alto - _MARGEN - 12,
               ancho - _MARGEN - 3.2, alto - _MARGEN - 5,
               strokeColor=colors.HexColor('#5A6B79'), strokeWidth=1))
    return d


# Como se describe el criterio EN PALABRAS, derivado de los ejes configurados.
# Cablearlo hacia que el PDF describiera un criterio distinto del que produjo el
# mapa: decia "sube la senescencia (PSRI)" cuando el motor ya exigia que BAJE el
# NDRE. El cliente leia una explicacion que no correspondia a su propio informe.
_COMO_SE_LLAMA = {'NDMI': ('la humedad del dosel', 'NDMI'),
                  'NDRE': ('la clorofila', 'NDRE'),
                  'CIRE': ('la clorofila', 'CIred-edge'),
                  'PSRI': ('la senescencia', 'PSRI')}


def _criterio_en_palabras():
    from . import config as cfg
    from .ranking import SIGNO
    partes = []
    for e in cfg.EJES:
        que, sigla = _COMO_SE_LLAMA.get(e, (e.lower(), e))
        verbo = 'caiga' if SIGNO[e] < 0 else 'suba'
        partes.append('%s %s (%s)' % (verbo, que, sigla))
    return ' y '.join(partes)


def _mmu():
    from .focos import MMU_HA
    return MMU_HA


def _bloque_lote(P, lote_id, r, geom):
    """Ficha de un lote alertado: mapa + focos + porcentaje. Nunca se parte en dos."""
    el = [P('Lote %s' % lote_id, 'H2')]
    mapa = _mapa_lote(geom, r.get('focos', []))
    focos = r.get('focos', [])
    if focos:
        # EL DENOMINADOR ES EL AREA REALMENTE TESTEADA, no el poligono declarado.
        # `focos.detectar_lote` argumenta que usar el poligono completo SUBESTIMA
        # entre 1,4x y 2x —la compuerta de FVC tiene que cumplirse en LAS DOS
        # fechas—, la consola ya usaba `pct_util`, y este PDF —que es lo que ve el
        # cliente— seguia con `pct_lote`. Medido en SANTO_ANTONIO-02: 58,79 ha
        # testeadas de 120,39 declaradas, o sea el 49% del lote.
        def _pc(d, k='pct_util'):
            v = d.get(k)
            if v is None:
                v = d.get('pct_lote')
            return '%.2f %%' % v if v is not None else '-'

        det = [[P('Foco', 'CellB'), P('Area', 'CellB'),
                P('% del area<br/>evaluada', 'CellB')]]
        for f in focos:
            p = f['properties']
            det.append([P('<b>%s</b>' % p['etiqueta'], 'Cell'),
                        P('%.2f ha' % p['area_ha'], 'Cell'),
                        P(_pc(p), 'Cell')])
        det.append([P('<b>Total</b>', 'Cell'),
                    P('<b>%.2f ha</b>' % r['area_focos_ha'], 'Cell'),
                    P('<b>%s</b>' % _pc(r), 'Cell')])
        tab = Table(det, colWidths=[1.9 * cm, 2.2 * cm, 2.3 * cm])
        tab.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), TEAL),
            ('LINEBELOW', (0, 0), (-1, 0), 1.1, LIMA),
            ('LINEABOVE', (0, -1), (-1, -1), 0.8, GRIS_M),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, TEAL_BG]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6)]))
        # QUE FRACCION DEL LOTE SE PUDO TESTEAR. Sin este numero, "2,2%" se lee como
        # 2,2% del lote y no lo es: es 2,2% de lo que se pudo mirar. Y lo excluido no
        # es aleatorio —es el cuartil bajo de NDVI—, o sea que los focos que se
        # entregan estan, por construccion, dentro de la parte de mas vigor.
        au, al = r.get('area_util_ha'), r.get('area_lote_ha')
        nota_area = ''
        if au and al:
            nota_area = (' Se pudo evaluar %.1f ha de las %.1f del lote (%.0f%%): el '
                         'resto quedo fuera por nube, sombra o poca cobertura vegetal '
                         'en alguna de las dos fechas.' % (au, al, 100 * au / al))
        lado = [tab, Spacer(1, 0.15 * cm),
                P('Imagen del %s, comparada contra la del %s.%s'
                  % (r.get('fecha_img') or '?', r.get('fecha_ref') or '?',
                     nota_area), 'Note')]
    else:
        lado = [P(r.get('nota') or 'Sin focos delimitados en este lote.', 'Note')]

    if mapa is not None:
        marco = Table([[mapa, lado]], colWidths=[MAPA_ANCHO + 2, 6.5 * cm])
        marco.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                   ('LEFTPADDING', (0, 0), (0, 0), 0)]))
        el.append(marco)
    else:
        el.extend(lado)
    return KeepTogether(el)


def generar(cliente, sitio, rank, ruta, fecha, cobertura=None, huecos=None,
            focos=None, geometrias=None, falsa_alarma=None, radar=None,
            sin_mirar=None, total_lotes=None, hay_geojson_focos=False):
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
                           % (len(rank) - sin_dato), VERDE))
    else:
        # `len(rank)` incluye los SIN DATO, que TAMBIEN se cuentan mas abajo como
        # "sin observacion suficiente": los dos numeros del informe sumaban 211 sobre
        # una cartera de 207. Evaluado = se midio y se pudo juzgar.
        n_eval = len(rank) - sin_dato
        st.append(_callout(
            P, '%d lote(s) para recorrer esta semana' % len(alertados),
            '%d en ATENCION y %d en VIGILANCIA, sobre %d lotes evaluados. Van ordenados '
            'por prioridad: si no se alcanza a recorrer todos, empezar por el primero.'
            % (n_at, n_vi, n_eval), ROJO if n_at else AMBAR))

    st.append(Spacer(1, 0.35 * cm))

    # --- la tabla ---
    if not alertados.empty:
        st.append(P('A donde ir', 'H1'))
        filas = [[P('#', 'CellB'), P('Lote', 'CellB'), P('Estado', 'CellB'),
                  P('Area', 'CellB'), P('Ultima imagen', 'CellB')]]
        # Se numera LA TABLA, 1..N. `orden` es el puesto en el ranking completo y
        # dejaba huecos (1,2,3,4,6,...) donde habia un SIN DATO intercalado: el
        # cliente veia un numero faltante sin ninguna explicacion.
        for i, (_, r) in enumerate(alertados.iterrows(), 1):
            filas.append([
                P(str(i), 'Cell'),
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
        st.append(P(
            'Los lotes de esta lista van tambien en el GeoJSON adjunto, para navegar '
            'con la app PIX Scout.' +
            (' El acercamiento intra-lote va en un GeoJSON aparte.'
             if hay_geojson_focos else
             ' Esta corrida NO produjo acercamiento intra-lote, asi que no hay archivo '
             'de focos.'), 'Note'))

    if not alertados.empty:
        st.append(P(
            '<b>ATENCION</b>: los dos ejes del criterio se apartaron a la vez. '
            '<b>VIGILANCIA</b>: se aparto uno solo. El criterio compara cada lote '
            'contra la trayectoria de su cohorte de siembra, no contra sus vecinos.',
            'Note'))

    # --- ACERCAMIENTO: donde dentro del lote, y cuanto ---
    if focos:
        st.append(P('Donde mirar dentro de cada lote', 'H1'))
        st.append(P(
            'El area marcada se obtuvo comparando la escena con la <b>escena limpia '
            'anterior del mismo lote</b>, exigiendo que %s <b>a la vez</b>. Los focos '
            'por debajo de %.2f ha se descartan por ruido.'
            % (_criterio_en_palabras(), _mmu()), 'Note'))
        st.append(Spacer(1, 0.2 * cm))
        con_focos = 0
        for _, r0 in alertados.iterrows():
            lid = str(r0['lote_id'])
            r = (focos or {}).get(lid)
            if not r:
                continue
            con_focos += 1 if r.get('focos') else 0
            st.append(_bloque_lote(P, lid, r, (geometrias or {}).get(lid)))
            st.append(Spacer(1, 0.25 * cm))
        if not con_focos:
            st.append(P(
                'Ningun lote alertado tiene el deterioro concentrado en focos por '
                'encima de la unidad minima de mapeo. El apartamiento es del promedio '
                'del lote: conviene recorrerlo entero, no un punto.', 'Note'))

    # --- COBERTURA: lo que no se pudo mirar. Va SIEMPRE, aunque este limpio ---
    st.append(P('Cobertura del analisis', 'H1'))
    lineas = []
    n_sin = sin_mirar if sin_mirar is not None else sin_dato
    if n_sin:
        # `sin_dato` son solo los que ENTRARON al ranking y caducaron. Los que nunca
        # juntaron serie suficiente no entran al ranking y quedaban sin contar: el
        # informe declaraba 4 cuando el numero real era 78.
        de_cuantos = (' de %d' % total_lotes) if total_lotes else ''
        lineas.append('<b>%d lote(s)%s SIN OBSERVACION suficiente</b> — no se pudieron '
                      'evaluar y no estan en la lista de arriba. No estan sanos: no se '
                      'miraron.' % (n_sin, de_cuantos))
        if radar and radar.get('total'):
            # El radar atraviesa la nube. NO dice si hay enfermedad — mide estructura,
            # no pigmentos. Dice si el lote cambio de forma gruesa: vuelco, cosecha,
            # anegamiento, perdida severa de biomasa.
            lineas.append('De esos, el <b>radar Sentinel-1</b> (que atraviesa la nube) '
                          'no detecto cambio estructural en <b>%d</b>, si detecto '
                          'cambio en <b>%d</b>, y no tuvo pasada util sobre <b>%d</b>. '
                          'El radar mide estructura del dosel, no pigmentos: un cambio '
                          'ahi es vuelco, cosecha, anegamiento o perdida de biomasa, '
                          '<b>no una enfermedad</b>.'
                          % (radar.get('sin_cambio', 0), radar.get('cambio', 0),
                             radar.get('sin_dato', 0)))
    if cobertura is not None:
        lineas.append('Observaciones plenas en la ventana: <b>%.0f%%</b> de las '
                      'disponibles.' % (100 * cobertura))
    if huecos:
        lineas.append('Hueco maximo declarado para la zona: <b>%d dias</b> sin escena '
                      'util.' % huecos)
    if falsa_alarma is not None:
        # El porcentaje de area marcada solo significa algo si el mismo procedimiento
        # marca poco donde no hay evento. Se publica el numero, no la conclusion.
        lineas.append('Falsa alarma medida del acercamiento en esta corrida: '
                      '<b>%.2f%%</b> del area. Un corte espacial simple marcaria '
                      '~9,7%% por construccion.' % falsa_alarma)
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


def generar_acercamiento(cliente, sitio, focos, geometrias, ruta, fecha):
    """Informe del modo CAMPO CHICO: acercamiento intra-lote, sin ranking.

    POR QUE EXISTE
    --------------
    Auditado 2026-07-27: un cliente `solo_focos` recibia un GeoJSON con poligonos
    rojos y un WhatsApp, y **ningun documento**. Todo el texto que declara los
    limites —que esto no dice la causa, que no ve el daño antes de que sea visible,
    y sobre todo que el acercamiento NO TIENE TASA DE FALSA ALARMA VALIDADA— vivia
    solo en `generar()`, que este cliente nunca ejecuta. La honestidad estaba
    escrita en un archivo que el cliente no recibe, y eso no es honestidad.

    `focos` es {lote_id: resultado de focos.detectar_lote}.
    """
    ss = _estilos()
    P = lambda t, s='Body': Paragraph(t, ss[s])
    st = [Spacer(1, 0.5 * cm)]

    mirados = {k: v for k, v in focos.items() if v.get('fecha_img')}
    ciegos = {k: v for k, v in focos.items() if not v.get('fecha_img')}
    con_foco = {k: v for k, v in mirados.items() if v.get('focos')}
    n_focos = sum(len(v['focos']) for v in mirados.values())
    ha = sum(v['area_focos_ha'] for v in mirados.values())

    # --- el veredicto primero, no la metodologia ---
    if not con_foco:
        st.append(_callout(
            P, 'No hay manchas para revisar esta ronda.',
            'Se evaluaron %d de %d lote(s) y no aparece ninguna mancha de al menos '
            '%.2f ha con cambio en los dos ejes a la vez.'
            % (len(mirados), len(focos), _mmu()), VERDE))
    else:
        st.append(_callout(
            P, '%d mancha(s) para ir a mirar, %.2f ha en total.' % (n_focos, ha),
            'Son manchas DENTRO del lote, no lotes enteros: el mapa las ubica para '
            'que el tecnico vaya al punto y no recorra el campo completo.',
            AMBAR))
    if ciegos:
        st.append(Spacer(1, 0.3 * cm))
        st.append(_callout(
            P, '%d lote(s) NO se pudieron evaluar.' % len(ciegos),
            'No hubo dos escenas limpias para comparar. <b>No significa que esten '
            'bien: significa que no se vieron.</b> ' +
            ' · '.join('%s: %s' % (k, v.get('nota') or 'sin par de escenas')
                       for k, v in sorted(ciegos.items())), ROJO))

    # --- ficha por lote ---
    for lid, r in sorted(mirados.items()):
        st.append(Spacer(1, 0.4 * cm))
        st.append(_bloque_lote(P, lid, r, (geometrias or {}).get(lid)))

    # --- que se hizo, en una linea ---
    from . import config as cfg
    st.append(P('Como se obtuvo', 'H1'))
    st.append(P(
        'Se compara cada punto del lote contra <b>ese mismo punto</b> en la escena '
        'limpia anterior, y se marca donde %s se mueven a la vez en el sentido del '
        'deterioro. La comparacion es del lote contra si mismo en el tiempo: no se '
        'lo compara con otros lotes.' % ' y '.join(cfg.EJES)))
    st.append(P(
        'Este campo <b>no emite ranking entre lotes</b>. Ese criterio compara cada '
        'lote contra la mediana de su cohorte y necesita al menos %d lotes; %s tiene '
        '%d. No es una limitacion temporal: no va a cambiar mientras el campo tenga '
        'esta escala.' % (_min_cohorte(), sitio.titulo, len(focos)), 'Note'))

    # --- limites. EL MISMO TEXTO que ve el cliente de ranking, mas el propio ---
    st.append(P('Lo que este informe no dice', 'H1'))
    st.append(P(
        'Es un producto de <b>priorizacion de recorrido</b>, no un diagnostico. El '
        'satelite marca donde el dosel cambio respecto de la semana anterior; '
        '<b>no dice la causa</b>. Suelo, nitrogeno, agua, pisoteo o enfermedad dan '
        'la misma firma. La causa la confirma el tecnico en el lote.'))
    st.append(P(
        'No detecta chinches ni roya asiatica a escala de lote comercial, y no ve el '
        'daño antes de que sea visible.', 'Note'))
    st.append(P(
        '<b>Este producto no tiene una tasa de falsa alarma validada.</b> Entrega '
        'poligonos y hectareas para ir a mirar, no una probabilidad de que la mancha '
        'sea un problema real. Medirla requiere una campaña de validacion a campo, '
        'que es justamente para lo que sirve registrar cada visita en la app — '
        'incluidas las visitas donde no se encuentra nada.', 'Note'))

    doc = SimpleDocTemplate(ruta, pagesize=A4, topMargin=3.2 * cm, bottomMargin=1.6 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            title='Acercamiento %s %s' % (cliente.titulo, fecha),
                            author='Pixadvisor Agricultura de Precision')
    cab = lambda c, d: _cabecera(c, d, cliente.titulo,
                                 '%s · escena Sentinel-2 del %s' % (sitio.titulo, fecha))
    doc.build(st, onFirstPage=cab, onLaterPages=cab)
    return ruta


def _min_cohorte():
    from .ranking import MIN_LOTES_COHORTE
    return MIN_LOTES_COHORTE


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
