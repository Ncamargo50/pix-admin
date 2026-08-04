# -*- coding: utf-8 -*-
"""Informe de acercamiento con identidad de marca Pixadvisor.

QUE REEMPLAZA Y POR QUE
-----------------------
El informe anterior era un PDF genérico: sin portada, sin marca, con un mapa
vectorial en blanco y negro y el veredicto perdido entre la metodología. El cliente
lo rechazó con una frase que resume el problema: «no se ve nada profesional, el mapa
no es intuitivo».

Los tres cambios que importan:

1. **Marca.** Usa el mismo sistema (`pix_branding.Brand`) que las propuestas y los
   protocolos: portada con degradado, logo, encabezado y pie en cada página, tablas
   con la paleta real. El cliente ya reconoce ese lenguaje visual.
2. **Mapa con la foto real.** Imagen satelital en color natural de la MISMA escena
   que disparó la alerta, con el lote y los focos encima. Antes el técnico veía un
   polígono flotando en blanco y no tenía cómo ubicarse en el terreno.
3. **El veredicto primero.** Qué pasó, dónde y qué hacer, arriba. La metodología y
   los límites van al final, completos, pero no compiten con la decisión.

LO QUE NO CAMBIA: todo lo que el informe declara sigue siendo cierto y sigue estando.
Este producto **no tiene tasa de falsa alarma validada** y eso se dice en la misma
página, no en una nota al pie. Un informe más lindo que esconda eso sería peor que
el anterior.
"""
import os
import sys

from reportlab.lib.units import cm
from reportlab.platypus import KeepTogether, PageBreak, Spacer, Table, TableStyle

from . import mapa as mp

# EL SISTEMA DE MARCA VIAJA DENTRO DEL REPOSITORIO (`PIX_ALERTA/marca/`).
#
# Al principio se leía de `~/.claude/skills/pixadvisor-propuesta-ejecutiva`, que es
# donde el usuario lo mantiene. Anduvo perfecto en la máquina del usuario y **falló
# en silencio en la nube**: el runner de GitHub es una máquina Linux vacía, no tiene
# esa carpeta, así que `HAY_MARCA` daba False y el informe caía al formato simple.
# Medido: el PDF local pesaba 297 KB con la foto satelital y el que publicaba la
# nube 9,5 KB sin nada. El cliente habría recibido el informe viejo todos los días.
#
# La copia local de la skill se sigue aceptando como respaldo, para no romper si
# alguien corre desde una copia sin la carpeta `marca/`.
_AQUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MARCA = os.path.join(_AQUI, 'marca')
_SKILL = os.path.join(os.path.expanduser('~'), '.claude', 'skills',
                      'pixadvisor-propuesta-ejecutiva')

_ASSETS = _MARCA if os.path.exists(os.path.join(_MARCA, 'pix_branding.py')) \
    else os.path.join(_SKILL, 'assets')
for _p in (_MARCA, os.path.join(_SKILL, 'scripts')):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import pix_branding as pbr
    HAY_MARCA = True
except Exception as _e:                          # noqa: BLE001
    print('[informe] SIN sistema de marca (%s): sale el formato simple. '
          'Revisar PIX_ALERTA/marca/pix_branding.py' % type(_e).__name__)
    HAY_MARCA = False


ANCHO = 15 * cm
# Alto máximo del mapa de contexto. Los lotes de trigo son angostos y largos; el
# recuadro se adapta a la forma del campo (ver `mapa.encajar`) y este es el techo.
MAPA_ALTO = 10.2 * cm
DET_W, DET_H = 7.1 * cm, 5.4 * cm


def _coord(g):
    c = mp.centro(g)
    return '%.5f, %.5f' % (c[1], c[0]) if c else '—'


def _fondo_lote(sitio, feat, r):
    """(png, marco) de la escena que disparó el foco, encuadrando el lote."""
    try:
        import ee
        from . import focos as fo
        geom = fo._geom_lote(sitio, feat)
        esc = fo._cobertura_por_escena(
            geom, str(__import__('pandas').Timestamp(r['fecha_img'])
                      - __import__('pandas').Timedelta(days=2))[:10],
            str(__import__('pandas').Timestamp(r['fecha_img'])
                + __import__('pandas').Timedelta(days=2))[:10])
        idx = None
        for f, i, _c in esc:
            if f == r['fecha_img']:
                idx = i
        if idx is None:
            return None, None
        return mp.fondo_rgb(idx, geom)
    except Exception as e:                       # noqa: BLE001
        print('  [informe] sin fondo para %s (%s)' % (r.get('lote_id'),
                                                      type(e).__name__))
        return None, None


def _fondo_detalle(sitio, feat, r, marco):
    try:
        import ee
        from . import focos as fo
        del feat, sitio, fo
        reg = ee.Geometry.Rectangle(list(marco), None, False)
        esc_idx = r.get('_idx_escena')
        if not esc_idx:
            return None
        png, _ = mp.fondo_rgb(esc_idx, reg, margen=0.0, max_px=640)
        return png
    except Exception:                            # noqa: BLE001
        return None


def _severidad(p):
    """Alta / Media con el MISMO corte que usa el GeoJSON que baja el teléfono.

    `detectar_lote` devuelve los focos sin el campo `sev` —ese lo agrega
    `a_geojson`—, así que el informe mostraba un guion en toda la columna. Se deriva
    acá del `z_sev`, que ya viene ORIENTADO (más negativo = peor), en vez de dejar
    la columna vacía o, peor, inventar un rótulo.
    """
    from .focos import Z_FOCO
    z = p.get('z_sev')
    if z is None:
        return '—'
    return 'ALTA' if float(z) <= -(Z_FOCO + 1) else 'MEDIA'


def _tabla_focos(B, r):
    """Foco · área · % del área evaluada · severidad · coordenadas."""
    filas = [['Foco', 'Área', '% del área\nevaluada', 'Severidad', 'Coordenadas (lat, lon)']]
    for f in r['focos']:
        p = f['properties']
        pc = p.get('pct_util')
        filas.append([
            p['etiqueta'],
            '%.2f ha' % p['area_ha'],
            '%.2f %%' % pc if pc is not None else '—',
            _severidad(p),
            _coord(f['geometry']),
        ])
    filas.append(['TOTAL', '%.2f ha' % r['area_focos_ha'],
                  '%.2f %%' % (r.get('pct_util') or 0.0), '', ''])
    t = B.tbl(filas, [1.6 * cm, 2.1 * cm, 2.4 * cm, 2.4 * cm, 6.5 * cm],
              aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'})
    return t


def generar(cliente, sitio, por_lote, geometrias, ruta, fecha, feats=None,
            contexto=None):
    """PDF de marca. `por_lote` = {lote_id: resultado de focos.detectar_lote}."""
    if not HAY_MARCA:
        from . import informe as inf
        return inf.generar_acercamiento(cliente, sitio, por_lote, geometrias,
                                        ruta, fecha)

    logo = os.path.join(_ASSETS, 'logo_pix_azulnegro_trim.png')
    B = pbr.Brand(logo=logo if os.path.exists(logo) else None,
                  content_w=ANCHO,
                  # Corto A PROPÓSITO: el pie ya lleva la marca a la izquierda y el
                  # número de página a la derecha. Con el nombre completo del
                  # cliente los tres bloques se pisaban entre sí.
                  footer_center='%s · %s' % (sitio.titulo, fecha))
    feats = feats or {}

    mirados = {k: v for k, v in por_lote.items() if v.get('fecha_img')}
    ciegos = {k: v for k, v in por_lote.items() if not v.get('fecha_img')}
    con_foco = {k: v for k, v in mirados.items() if v.get('focos')}
    n_focos = sum(len(v['focos']) for v in mirados.values())
    ha = sum(v['area_focos_ha'] for v in mirados.values())
    ha_util = sum(float(v.get('area_util_ha') or 0) for v in mirados.values())
    ha_lote = sum(float(v.get('area_lote_ha') or 0) for v in por_lote.values())
    fechas = sorted({v['fecha_img'] for v in mirados.values()})

    st = list(B.cover_filler())

    # --- 1. EL VEREDICTO, antes que nada -------------------------------------
    if con_foco:
        st.append(B.callout(
            'Qué encontramos',
            '<b>%d mancha(s) para revisar, %.2f ha en total.</b> Están DENTRO de los '
            'lotes: el mapa las ubica para que el recorrido vaya al punto y no al '
            'campo entero.' % (n_focos, ha)))
    else:
        st.append(B.callout(
            'Qué encontramos',
            '<b>Ninguna mancha para revisar en esta ronda.</b> Se evaluaron %d de %d '
            'lote(s) y no aparece ningún sector con cambio simultáneo en los dos '
            'indicadores.' % (len(mirados), len(por_lote))))
    st.append(Spacer(1, 0.45 * cm))

    st.append(B.kpi_strip([
        (str(n_focos), 'manchas<br/>detectadas'),
        ('%.2f' % ha, 'hectáreas<br/>comprometidas'),
        ('%d/%d' % (len(mirados), len(por_lote)), 'lotes<br/>evaluados'),
        # Sólo la MÁS RECIENTE y en formato corto: dos fechas completas no entran
        # en la caja del KPI y se pisaban entre sí.
        (('%s/%s' % (fechas[-1][8:10], fechas[-1][5:7])) if fechas else '—',
         'imagen más<br/>reciente'),
    ]))
    st.append(Spacer(1, 0.4 * cm))

    st.append(B.meta_table([
        ('Propiedad', sitio.titulo),
        ('Cultivo', (getattr(sitio, 'cultivo', '') or '—').capitalize()),
        ('Fecha del análisis', str(fecha)),
        ('Imagen utilizada', ' · '.join(fechas) or 'sin imagen'),
        ('Superficie evaluada', '%.1f ha de %.1f ha declaradas (%.0f %%)'
         % (ha_util, ha_lote, 100 * ha_util / ha_lote) if ha_lote else '—'),
        ('Satélite', 'Sentinel-2 (Copernicus) · 10–20 m'),
    ]))

    if ciegos:
        st.append(Spacer(1, 0.35 * cm))
        st.append(B.callout(
            'Atención',
            '<b>%d lote(s) NO se pudieron evaluar</b> por falta de dos imágenes '
            'limpias para comparar. Eso NO significa que estén bien: significa que '
            'no se vieron. %s'
            % (len(ciegos), ' · '.join('%s' % k for k in sorted(ciegos)))))

    st.append(PageBreak())

    # --- 2. Una página por lote evaluado -------------------------------------
    n = 0
    for lid, r in sorted(mirados.items()):
        n += 1
        st.append(B.sec(n, 'Lote %s' % lid))

        feat = feats.get(lid)
        png, marco = (None, None)
        if feat is not None:
            png, marco = _fondo_lote(sitio, feat, r)
        geom_lote = (geometrias or {}).get(lid)
        pares = [(f['properties']['etiqueta'], f['geometry'])
                 for f in r.get('focos', [])]

        if marco is None and geom_lote is not None:
            marco = mp.marco_de([geom_lote], margen=0.10, minimo_m=200)
        if marco is not None:
            w, h = mp.encajar(marco, ANCHO, MAPA_ALTO)
            st.append(mp.dibujar(marco, png, geom_lote, pares, w, h,
                                 radio_min=6.5))
            st.append(Spacer(1, 0.12 * cm))
            # La referencia ya NO es una fecha: es la trayectoria del propio píxel
            # sobre todas las imágenes limpias previas. El texto tiene que decir eso
            # y no pegar la cadena "trayectoria ..." donde antes iba una fecha.
            ref = str(r.get('fecha_ref') or '')
            if ref.startswith('trayectoria'):
                comparacion = ('comparada contra el comportamiento propio de cada '
                               'punto del lote entre el %s'
                               % ref.replace('trayectoria ', '').replace(' a ', ' y el '))
            else:
                comparacion = 'comparada contra la del %s' % (ref or '—')
            st.append(B.P(
                'Imagen Sentinel-2 en color natural del <b>%s</b>, %s. El contorno '
                'blanco es el lote; los círculos amarillos marcan dónde está cada '
                'mancha.' % (r['fecha_img'], comparacion), 'Note'))
            # CUANDO PUDO APARECER LA MANCHA. Si la escena limpia anterior esta
            # lejos, decir "aparecio el 1 de agosto" es inventar una precision que
            # no se tiene: pudo aparecer cualquier dia del intervalo. Patron Δt_max
            # de Sen4CAP. Ver `criterio.DT_MAX_DIAS`.
            if r.get('fecha_imprecisa') and r.get('fecha_previa'):
                st.append(B.P(
                    '<b>Cuándo pudo aparecer:</b> la imagen limpia anterior es del '
                    '%s, o sea <b>%d días antes</b>. La mancha pudo formarse en '
                    'cualquier momento de ese intervalo — esta fecha es cuando se '
                    'la vio, no cuando apareció.'
                    % (r['fecha_previa'], r['dt_dias']), 'Note'))
            st.append(Spacer(1, 0.3 * cm))

        if pares:
            st.append(_tabla_focos(B, r))
            st.append(Spacer(1, 0.15 * cm))
            au, al = r.get('area_util_ha'), r.get('area_lote_ha')
            if au and al:
                st.append(B.P(
                    'Los porcentajes son sobre el <b>área realmente evaluada</b>: '
                    '%.1f ha de las %.1f del lote (%.0f %%). El resto quedó fuera '
                    'por nube, sombra o poca cobertura vegetal en alguna de las dos '
                    'fechas — y lo que queda fuera no es al azar, es el sector de '
                    'menor vigor.' % (au, al, 100 * au / al), 'Note'))
        else:
            st.append(B.P(
                'Se evaluó el lote y <b>no hay ninguna mancha</b> de al menos %.2f ha '
                'con cambio simultáneo en los dos indicadores.' % _mmu(), 'Body'))

        # Acercamiento a cada foco
        if pares and marco is not None:
            st.append(Spacer(1, 0.35 * cm))
            titulo_donde = [B.P('Dónde ir', 'H2'),
                            B.P('Acercamiento a cada mancha, con la coordenada para '
                                'cargar en el GPS.', 'Note')]
            celdas, fila = [], []
            for etq, g in pares[:6]:
                m = mp.marco_de([g], margen=1.5, minimo_m=320)
                r2 = dict(r)
                r2['_idx_escena'] = r.get('_idx_escena')
                pd = _fondo_detalle(sitio, feat, r2, m) if r.get('_idx_escena') else None
                w2, h2 = mp.encajar(m, DET_W, DET_H)
                fila.append([mp.dibujar(m, pd, geom_lote, [(etq, g)], w2, h2),
                             B.P('<b>%s</b> · %s' % (etq, _coord(g)), 'Note')])
                if len(fila) == 2:
                    celdas.append(fila)
                    fila = []
            if fila:
                fila.append('')
                celdas.append(fila)
            for i_par, par in enumerate(celdas):
                cols = []
                for c in par:
                    cols.append(Table([[c[0]], [c[1]]]) if isinstance(c, list) else '')
                t = Table([cols], colWidths=[ANCHO / 2, ANCHO / 2])
                t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                       ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                       ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
                # El título viaja PEGADO al primer par de mapas: si no, queda
                # huérfano al pie de una página y los mapas arrancan en la siguiente.
                st.append(KeepTogether((titulo_donde + [t]) if i_par == 0 else [t]))

        if n < len(mirados):
            st.append(PageBreak())

    # --- 2 ter. Confirmacion entre imagenes ---------------------------------
    _seccion_confirmacion(B, st, por_lote)

    # --- 2 bis. Contexto: lo que NO es alerta --------------------------------
    # Va DESPUES de los focos y ANTES del metodo, y con otro lenguaje. Si esta
    # seccion habla de "alerta" o de "severidad", la distincion que la justifica se
    # perdio y el tecnico sale a caminar una mancha de suelo.
    n = _seccion_contexto(B, st, n, contexto)

    # --- 3. Método y límites, completos y al final ---------------------------
    st.append(PageBreak())
    from . import config as cfg
    st.append(B.sec(n + 1, 'Cómo se obtuvo'))
    st.append(B.P(
        'Se sigue <b>cada punto del lote a lo largo de la campaña</b> y se calcula '
        'cómo viene comportándose. En cada imagen nueva se mide cuánto se aparta ese '
        'punto de su propio comportamiento, y se marca donde %s se mueven a la vez '
        'en el sentido del deterioro. La comparación es del lote contra sí mismo en '
        'el tiempo: no se lo compara con otros lotes ni con una tabla de valores '
        'esperados.' % ' y '.join(cfg.EJES)))
    st.append(B.P(
        'Comparar contra el historial de cada punto —y no contra una sola imagen '
        'anterior— hace que baste con que la imagen del día esté limpia, y no dos. '
        'Por eso se puede evaluar bastante más superficie del lote.', 'Note'))
    st.append(B.P(
        '· <b>%s</b> mide el agua del dosel: baja cuando la planta se seca.<br/>'
        '· <b>%s</b> mide la clorofila: baja cuando el dosel pierde pigmento.'
        % (cfg.EJES[0], cfg.EJES[-1]), 'Bull'))
    st.append(B.P(
        'Exigir que los <b>dos</b> se muevan juntos es lo que evita marcar ruido. '
        'Sólo se reportan manchas de al menos %.2f ha: por debajo de eso no hay a '
        'dónde mandar a nadie.' % _mmu(), 'Body'))
    st.append(Spacer(1, 0.3 * cm))
    st.append(B.P(
        'Este campo <b>no emite ranking entre lotes</b>. Ese criterio compara cada '
        'lote contra la mediana de su grupo y necesita al menos %d lotes; esta '
        'propiedad tiene %d. No es una limitación temporal.'
        % (_min_cohorte(), len(por_lote)), 'Note'))

    st.append(Spacer(1, 0.5 * cm))
    st.append(B.sec(n + 2, 'Lo que este informe no dice'))
    st.append(B.P(
        'Es un producto de <b>priorización de recorrido</b>, no un diagnóstico. El '
        'satélite marca dónde el cultivo cambió respecto de la imagen anterior; '
        '<b>no dice la causa</b>. Suelo, nitrógeno, agua, pisoteo o enfermedad dan '
        'la misma señal. La causa la confirma el técnico en el lote.'))
    st.append(B.P(
        'No detecta chinches ni roya asiática a escala de lote comercial, y no ve el '
        'daño antes de que sea visible a campo.', 'Note'))
    st.append(Spacer(1, 0.25 * cm))
    st.append(B.callout(
        'Importante',
        '<b>Este producto todavía no tiene una tasa de falsa alarma medida.</b> '
        'Entrega polígonos y hectáreas para ir a mirar, no una probabilidad de que '
        'la mancha sea un problema real. Medirla requiere una campaña de validación '
        'a campo — y para eso sirve registrar cada visita en la aplicación, '
        'incluidas las visitas donde no se encuentra nada.'))

    B.build(ruta, st,
            cover_title='Monitoreo satelital de cultivo',
            cover_subtitle='%s · %s · Imagen del %s'
                           % (cliente.titulo, sitio.titulo,
                              ' y '.join(fechas) or str(fecha)))
    return ruta


def _seccion_confirmacion(B, st, por_lote):
    """Explica la etiqueta de confirmacion, y SOLO si algun foco la trae.

    Va como nota y no como seccion numerada: es una propiedad de los focos que ya se
    listaron, no un hallazgo aparte.
    """
    estados = [f['properties'].get('confirmacion')
               for r in (por_lote or {}).values() for f in (r.get('focos') or [])]
    estados = [e for e in estados if e]
    if not estados:
        return
    st.append(Spacer(1, 0.3 * cm))
    st.append(B.P('¿La mancha ya estaba en la imagen anterior?', 'H2'))
    st.append(B.P(
        'Un deterioro del cultivo no se mueve: si una parte del lote está afectada hoy, '
        'en la imagen limpia anterior ya debería aparecer algo en el mismo lugar — aunque '
        'todavía fuera demasiado chico para reportarlo. Una bruma, en cambio, está en una '
        'imagen y no en la otra. Cada mancha lleva ese dato.'))
    filas = [['Mancha', 'Superficie', 'Ya estaba', 'Por azar sería', 'Lectura']]
    LECT = {'persistente': 'ya estaba antes',
            'sin_confirmar': 'aparece por primera vez',
            'no_evaluable': 'no había imagen anterior utilizable'}
    for lid, r in sorted((por_lote or {}).items()):
        for f in (r.get('focos') or []):
            p = f['properties']
            e = p.get('confirmacion')
            if not e:
                continue
            pp, az = p.get('persistencia_pct'), p.get('persistencia_azar_pct')
            filas.append(['%s / %s' % (lid, p.get('etiqueta')),
                          '%.2f ha' % (p.get('area_ha') or 0),
                          ('%.0f%%' % pp) if pp is not None else '—',
                          ('%.1f%%' % az) if az is not None else '—',
                          LECT.get(e, e)])
    if len(filas) > 1:
        st.append(B.tbl(filas, [3.8 * cm, 2.4 * cm, 2.2 * cm, 2.8 * cm, 4.0 * cm],
                        aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))
    st.append(B.P(
        '<b>«Aparece por primera vez» no quiere decir que sea falso.</b> Un problema que '
        'recién empieza tampoco estaba en la imagen anterior. Lo que la columna dice es '
        'cuánta confianza da <i>esta</i> imagen sola, no si hay que ir o no: se va a '
        'mirar igual.', 'Note'))
    return


def _seccion_contexto(B, st, n, contexto):
    """Zonas estructurales y bloques de siembra. Devuelve el nuevo numero de seccion.

    Se OMITE entera cuando no hay nada que decir: una seccion que dice "no se
    encontraron zonas" en todos los informes se vuelve invisible y ademas ocupa la
    pagina que necesita lo que si importa.
    """
    if not contexto:
        return n
    res = contexto.get('resumen') or {}
    zonas = contexto.get('zonas') or {}
    bloques = res.get('bloques_en_atencion') or []
    if not res.get('n_zonas') and not bloques:
        return n

    st.append(PageBreak())
    n += 1
    st.append(B.sec(n, 'Contexto del lote — para investigar, no para recorrer'))
    st.append(B.P(
        'Lo que sigue <b>no es una alerta</b>. Las manchas de la sección anterior '
        'dicen «acá cambió algo esta semana» y se van a mirar ya. Esto dice otra '
        'cosa: «esta parte viene distinta desde hace tiempo». No hace falta salir '
        'hoy; hace falta entender por qué.'))

    if res.get('n_zonas'):
        st.append(Spacer(1, 0.3 * cm))
        st.append(B.P('Zonas por debajo de lo que su porte indica', 'H2'))
        st.append(B.P(
            'Dentro de una misma imagen se compara cada punto con los puntos del '
            'mismo lote que tienen <b>su mismo desarrollo</b>. Una zona aparece '
            'cuando, teniendo el mismo porte que sus pares, está más seca o con '
            'menos pigmento del que le correspondería. Por eso <b>no la explica la '
            'fecha de siembra</b>: sembrar más tarde da menos porte, y el porte ya '
            'está descontado.'))
        filas = [['Lote', 'Zona', 'Superficie', '% del lote', 'Cuánto le falta']]
        for lid, r in sorted(zonas.items()):
            for zz in r.get('zonas', []):
                p = zz['properties']
                filas.append([lid, p['etiqueta'], '%.2f ha' % p['area_ha'],
                              ('%.1f%%' % p['pct_lote']) if p.get('pct_lote') else '—',
                              '%.1f σ' % (p.get('deficit_z') or 0)])
        st.append(B.tbl(filas, [4.2 * cm, 2.0 * cm, 3.0 * cm, 2.6 * cm, 3.2 * cm],
                        aligns={2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}))
        st.append(B.P(
            'Que una zona vuelva a salir en el mismo lugar semana tras semana prueba '
            'que <b>es real</b>, no que sea un problema: puede ser un bajo, un cambio '
            'de suelo o una compactación vieja que el productor ya conoce. Se '
            'entrega para que la mire quien conoce el lote.', 'Note'))

    if bloques:
        st.append(Spacer(1, 0.4 * cm))
        st.append(B.P('Bloques de siembra que se implantaron más tarde de lo previsto',
                      'H2'))
        st.append(B.P(
            'Cuando el lote se sembró en varias pasadas, cada bloque se sigue por '
            'separado y se mide <b>en qué día alcanzó el mismo desarrollo</b>. Ese '
            'atraso medido se compara con el que las fechas de siembra declaradas '
            'explican. La diferencia es el dato: un bloque que tardó bastante más de '
            'lo que su fecha justifica tuvo un problema de implantación.'))
        filas = [['Lote', 'Bloque', 'Atraso medido', 'Según la siembra', 'Diferencia']]
        for b in bloques:
            filas.append([b['lote_id'], 'B%s' % b['estrato'],
                          '%.0f días' % (b.get('medido') or 0),
                          '%.0f días' % (b.get('declarado') or 0),
                          '%.0f días' % b['diferencia_dias']])
        st.append(B.tbl(filas, [4.2 * cm, 2.0 * cm, 3.2 * cm, 3.4 * cm, 2.2 * cm],
                        aligns={2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}))
        st.append(B.P(
            'Ningún criterio por punto ve esto: dentro del bloque todas las plantas '
            'están igual de atrasadas entre sí, así que no hay contraste interno que '
            'marcar. Sólo se ve comparando el bloque con los demás a la misma edad.',
            'Note'))
    return n


def _mmu():
    from .focos import MMU_HA
    return MMU_HA


def _min_cohorte():
    from .ranking import MIN_LOTES_COHORTE
    return MIN_LOTES_COHORTE
