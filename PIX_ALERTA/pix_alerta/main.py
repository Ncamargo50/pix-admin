"""Orquestador: de los poligonos de lote a la lista de a donde ir hoy.

    python -m pix_alerta.main --sitio HDS --hasta 2026-04-30 --K 10

Contrato de salida:
    10 = ENTREGADO      se genero entregable
     0 = SIN NOVEDAD    se evaluo y no hay nada que reportar
    20 = NO EVALUABLE   **no se pudo mirar** (sin escenas, todo nube, serie corta)
    21 = FUERA DE CAMPANA  no toca mirar
    cualquier otro = fallo real, que se vea

20 y 0 estuvieron confundidos hasta 2026-07-27 y los dos salian rotulados "sin
novedad". En un producto de alerta esa confusion es la peor de todas, porque el
modo de falla TRANQUILIZA: el cliente lee lo mismo cuando el campo esta sano que
cuando el satelite no vio nada en tres semanas.

Emite el CSV de ranking y el GeoJSON para la app de campo. El GeoJSON lleva
`lote_id` estable y `estrato` — que la app debe guardar y NO mostrar: si el tecnico
sabe que va a un rojo, encuentra algo.
"""
import argparse
import json
import os
import sys
from datetime import date

import pandas as pd

from . import cohorte as coh
from . import config as cfg
from . import ranking as rk
from . import series as sr


# Severidad que entiende la app a partir del veredicto del criterio. La app deriva
# color y orden de `sev`; sin este campo `deriveSev` devuelve null y TODOS los lotes
# salen "sin dato de severidad".
SEV_APP = {'ATENCION': 'alta', 'VIGILANCIA': 'media'}


# Tolerancia de simplificacion del perimetro, en grados (~0,0002 = ~22 m).
# El perimetro es SOLO para encuadrar el mapa: no se mide sobre el, asi que no hace
# falta resolucion de borde. Medido sobre HDS: el contorno crudo de los 220 lotes son
# 16.107 vertices y 776 KB de GeoJSON para 6 focos — el 97% del archivo era el marco.
# En una APK offline sobre conectividad rural eso se paga en cada descarga. Con esta
# tolerancia baja a 3.607 vertices y 192 KB. Las 148 partes que quedan NO son astillas:
# son parcelas reales (mediana 16 ha, maxima 358), o sea la forma verdadera del campo.
PERIM_TOLERANCIA = 0.0002
PERIM_AREA_MINIMA = 1e-7          # ~1 ha en grados: descarta astillas del disolvido


def _perimetro(gj):
    """Contorno del campo, disuelto de los propios lotes y simplificado.

    La app lo usa para encuadrar el mapa. Sin el, el tecnico ve poligonos flotando sin
    referencia de donde esta el campo. Si no hay shapely se sigue sin perimetro: es
    degradacion, no motivo para no entregar.
    """
    try:
        from shapely.geometry import MultiPolygon, Polygon, mapping, shape
        from shapely.ops import unary_union
    except ImportError:
        return None
    try:
        u = unary_union([shape(f['geometry']) for f in gj['features']
                         if f.get('geometry')]).buffer(0)
        u = u.simplify(PERIM_TOLERANCIA, preserve_topology=True)
        # Las astillas que deja el disolvido no son campo y son la mitad de las partes.
        if isinstance(u, MultiPolygon):
            partes = [g for g in u.geoms if g.area >= PERIM_AREA_MINIMA]
            if partes:
                u = MultiPolygon(partes) if len(partes) > 1 else partes[0]
        if u.is_empty or not isinstance(u, (Polygon, MultiPolygon)):
            return None
        return mapping(u)
    except Exception:
        return None


def _geojson_salida(sitio, rank, ruta):
    """Poligonos de los lotes priorizados, en el formato que LEE la app de campo.

    OJO: los nombres de campo no son decorativos, son la interfaz con PIX Scout.
    Medido antes de este cambio: la app cargaba los 6 lotes con id `F-1`..`F-6`
    —posicionales, se renumeran en cada corrida—, el nombre del lote como "Lote 1" en
    vez de `J1_soya`, hacienda "Campo", sin severidad y sin perimetro. Con ids
    posicionales **el lazo de retorno no existe**: una validacion registrada hoy no se
    puede rastrear al lote la semana que viene, que es justo el dato con el que se mide
    la precision del motor.
    """
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    por_id = {str(f['properties'].get(sitio.campo_id)): f for f in gj['features']}
    feats = []
    vistos = set()
    for _, r in rank.iterrows():
        f = por_id.get(str(r['lote_id']))
        if f is None:
            continue
        lid = str(r['lote_id'])
        if lid in vistos:                      # el ID tiene que ser unico o no sirve
            raise RuntimeError(f'lote_id duplicado en la salida: {lid}')
        vistos.add(lid)
        est = r['estado']
        props = {
            # --- interfaz con la app: `id` es lo que ancla el lazo de retorno ---
            'id': lid,
            'name': lid,
            'etiqueta': lid,                   # lo que el tecnico casa con el informe
            'lote': lid,
            'hacienda': sitio.titulo,
            'fecha_img': str(r['fecha_dato'])[:10],
            'sev': SEV_APP.get(est),           # None si no esta alertado
            'cultivo': getattr(sitio, 'cultivo', '') or None,
            # Redondeado: la app lo imprime tal cual y salia "Sev 2.2025829689196113".
            # NO se reescala a 1-99: ese numero seria inventado. Es el estadistico del
            # criterio (EWMA dirigido); lo que el tecnico usa es el ORDEN.
            'score': (round(float(r['score']), 2)
                      if pd.notna(r.get('score')) else None),
            # --- criterio ---
            'lote_id': lid,
            'orden': int(r['orden']),
            'estrato': est,                    # la app lo GUARDA y no lo muestra
            'fecha_dato': str(r['fecha_dato'])[:10],
            'dias_atras': int(r['dias_atras']),
            'area_ha': float(r['area_ha']),
            'status': 'pending',
        }
        feats.append({'type': 'Feature', 'geometry': f['geometry'],
                      'properties': props})

    n_focos = len(feats)
    per = _perimetro(gj)
    if per is not None:
        # Va PRIMERO y con tipo 'perimetro': asi la app lo excluye de la lista de focos
        # y lo usa solo para encuadrar (geojson.js -> isPerimeter).
        feats.insert(0, {'type': 'Feature', 'geometry': per,
                         'properties': {'tipo': 'perimetro',
                                        'id': '%s-PERIMETRO' % sitio.clave,
                                        'hacienda': sitio.titulo}})
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump({'type': 'FeatureCollection', 'features': feats}, fh,
                  ensure_ascii=False)
    return n_focos


# Fraccion MINIMA del area del sitio que hay que haber mirado para poder afirmar
# que no hay nada. Por debajo, "sin novedad" seria una afirmacion sobre un campo que
# en su mayor parte no se observo. 0,70 es el mismo criterio de cobertura que usa
# `focos.COB_MINIMA` dentro del lote, aplicado ahora al sitio.
COBERTURA_MINIMA_SITIO = 0.70


def _paquete_validacion(sitio, gj, por_lote, a):
    """Focos + puntos de control, mezclados a ciegas, con la clave en otro archivo.

    Se llama DESPUES de escribir la entrega normal: esto es un producto adicional para
    la campaña de validacion, no un reemplazo. Nunca levanta.
    """
    from . import controles as ct
    feats = {str(f['properties'].get(sitio.campo_id)): f for f in gj['features']}
    ctrl = {}
    try:
        for lid, r in sorted(por_lote.items()):
            f = feats.get(lid)
            if f is None or not r.get('fecha_img'):
                continue          # sin escena evaluada no hay area donde muestrear
            # Tantos controles como focos, con el piso y el techo del modulo: el
            # tecnico camina el doble, no diez veces mas.
            n = max(len(r.get('focos') or []), ct.CONTROLES_MIN)
            # Las areas de los focos viajan para que los controles tengan las MISMAS
            # areas: si no, el punto con area distinta ES el foco y el ciego se pierde.
            areas = [x['properties'].get('area_ha') for x in (r.get('focos') or [])]
            c = ct.controles_lote(sitio, f, a.hasta, n=n, areas_foco=areas)
            if c.get('error'):
                print('  [validacion] controles %s: %s' % (lid, c['error']))
            elif c.get('nota'):
                print('  [validacion] %s: %s' % (lid, c['nota']))
            ctrl[lid] = c
        gjv, clave = ct.paquete_ciego(sitio, por_lote, ctrl,
                                      a.hasta, perimetro=_perimetro(gj))
        if clave['n_focos'] + clave['n_controles'] == 0:
            print('  [validacion] no hay ningun punto para esta ronda')
            return None
        f_gj, f_cl = ct.guardar(a.salida, sitio, a.hasta, gjv, clave)
        print('  -> %s  (%d punto(s): %d foco(s) + %d control(es), a ciegas)'
              % (f_gj, clave['n_focos'] + clave['n_controles'],
                 clave['n_focos'], clave['n_controles']))
        print('     CLAVE (NO mandar al telefono): %s' % f_cl)
        return f_gj
    except Exception as e:                        # noqa: BLE001
        print('  [validacion] no se pudo armar el paquete: %s: %s'
              % (type(e).__name__, str(e)[:120]))
        return None


def _capas_de_contexto(sitio, gj, por_lote, a):
    """Zonas y estratos de cada lote mirado, en `contexto_<sitio>_<fecha>.geojson`.

    Devuelve el dict que consume el informe. Nunca levanta: cualquier averia se
    imprime y se sigue, porque esto es contexto y el producto es el foco.
    """
    from . import capas as cp
    vacio = {'zonas': {}, 'estratos': {}, 'resumen': None, 'ruta': None}
    feats = {str(f['properties'].get(sitio.campo_id)): f for f in gj['features']}
    zonas, estr = {}, {}
    try:
        for lid, r in sorted(por_lote.items()):
            f = feats.get(lid)
            if f is None:
                continue
            # ESTRATOS: no dependen de que hoy haya escena limpia — se separan con
            # una escena TEMPRANA de la campaña. Se calculan aunque el lote no se
            # haya podido mirar hoy.
            e = cp.estratos_lote(sitio, f, a.hasta)
            if e.get('error'):
                print('  [contexto] estratos %s: %s' % (lid, e['error']))
            estr[lid] = e
            # ZONAS: si que necesitan la escena de hoy, porque miden el estado
            # espacial de ESA imagen. Sin fecha evaluada no hay zonas que calcular.
            if r.get('fecha_img'):
                zz = cp.zonas_lote(sitio, f, r['fecha_img'])
                if zz.get('error'):
                    print('  [contexto] zonas %s: %s' % (lid, zz['error']))
                zonas[lid] = zz
    except Exception as e:                        # noqa: BLE001
        print('  [contexto] no se pudieron calcular las capas: %s: %s'
              % (type(e).__name__, str(e)[:120]))
        return vacio

    res = cp.resumen(zonas, estr)
    ruta = None
    try:
        paquete = cp.a_geojson(sitio, zonas, estr, perimetro=_perimetro(gj))
        # SOLO si hay algo ADEMAS del perimetro. Un archivo con el contorno del campo
        # y nada mas parece una entrega y no dice nada: Sao Francisco lo generaba en
        # cada corrida porque no declara varias siembras y no tuvo zonas.
        util = [f for f in paquete['features']
                if f['properties'].get('tipo') != 'perimetro']
        if util:
            ruta = os.path.join(a.salida,
                                'contexto_%s_%s.geojson' % (sitio.clave, a.hasta))
            with open(ruta, 'w', encoding='utf-8') as fh:
                json.dump(paquete, fh, ensure_ascii=False)
    except Exception as e:                        # noqa: BLE001
        print('  [contexto] no se pudo escribir el geojson: %s' % e)
        ruta = None

    if res['n_zonas']:
        print('   contexto: %d zona(s) a investigar, %.2f ha  (NO son alerta)'
              % (res['n_zonas'], res['area_zonas_ha']))
    for b in res['bloques_en_atencion']:
        print('   contexto: %s bloque B%s se implanto %.0f dia(s) mas tarde de lo '
              'que su fecha de siembra explica' % (b['lote_id'], b['estrato'],
                                                   b['diferencia_dias']))
    return {'zonas': zonas, 'estratos': estr, 'resumen': res, 'ruta': ruta}


def _entregar_acercamiento(sitio, a):
    """Producto para campos CHICOS: focos DENTRO del lote, sin ranking entre lotes.

    POR QUE EXISTE
    --------------
    El ranking compara cada lote contra la mediana de su cohorte y necesita >= 8
    lotes. Un campo de dos parcelas —el caso de Santo Antonio y Sao Francisco en
    trigo— no tiene cohorte y NUNCA va a tenerla: esperar no lo arregla. Sin este
    modo, ese cliente recibe "NO EVALUABLE" todos los dias de la campaña.

    El acercamiento no necesita cohorte: compara cada pixel contra el MISMO lote en
    la escena limpia anterior. Medido el 2026-07-27 sobre el LOTE Santo Antonio-02
    (par 2026-07-20 / 2026-07-15): 3 focos, 1,28 ha, 2,19% de su area evaluada. Cada
    lote arma su propio par —Santo Antonio-01 uso 07-15/07-10—, asi que no existe
    "el par del sitio" ni un porcentaje unico del sitio.

    LO QUE ESTE MODO NO TIENE, Y HAY QUE DECIRLO
    --------------------------------------------
    **Tasa de falsa alarma.** La nula del acercamiento fue auditada y RECHAZADA
    (comparte estimador y par de fechas con el detector: estan anticorrelados por
    construccion). Entrega POLIGONOS Y HECTAREAS para ir a mirar, no una
    probabilidad de que sea real. Es una herramienta para dirigir el recorrido, y
    se ofrece como tal.
    """
    from . import focos as fo
    from .ee_init import inicializar
    print('[GEE] %s' % inicializar())
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    ids = [str(f['properties'].get(sitio.campo_id)) for f in gj['features']]
    # EL ID TIENE QUE EXISTIR Y SER UNICO, o el producto es irrastreable.
    # La ruta de ranking esta protegida por dos lados (`series._lotes_ee` saltea los
    # None y `_geojson_salida` revienta con id duplicado); esta no tenia ninguno.
    # Con un `campo_id` mal escrito, los dos lotes colapsaban en la clave 'None', se
    # evaluaba uno solo y se entregaba ENTREGADO con focos rotulados 'None-F1' — y
    # sin id estable no hay lazo de retorno: la validacion del tecnico no se puede
    # atribuir a ningun lote. Es la ruta que estrena el alta web, o sea la mas
    # expuesta a un GeoJSON nuevo.
    if not ids:
        print('[FALLO] el GeoJSON de %s no tiene ningun lote.' % sitio.clave)
        return 1
    sin_id = [i for i in ids if i in ('None', '', 'nan')]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if sin_id or dup:
        print('[FALLO] los lotes de %s no tienen id utilizable con campo_id=%r.'
              % (sitio.clave, sitio.campo_id))
        if sin_id:
            print('   %d lote(s) sin ese campo. Propiedades disponibles: %s'
                  % (len(sin_id), sorted((gj['features'][0].get('properties') or {}))))
        if dup:
            print('   ids repetidos: %s' % ', '.join(dup[:5]))
        print('   Sin id estable y unico no hay lazo de retorno: lo que registre el '
              'tecnico no se puede atribuir a un lote.')
        return 1

    print('[acercamiento] modo campo chico: %d lote(s), sin ranking entre lotes'
          % len(ids))

    por_lote = fo.detectar(sitio, ids, a.hasta)
    # QUE CUENTA COMO "MIRADO": tener `fecha_img`, o sea haber conseguido el par de
    # escenas. **No sirve mirar `nota`**: `detectar_lote` tambien escribe nota cuando
    # SI miro y no encontro nada sobre la unidad minima ("el deterioro no esta
    # concentrado"), que es justo el caso contrario. Usar la nota daba NO EVALUABLE
    # sobre Sao Francisco cuando sus dos lotes se habian mirado y estaban limpios —
    # el mismo error que este modulo viene a evitar, en el otro sentido.
    mirados = [r for r in por_lote.values() if r.get('fecha_img')]
    n_focos = sum(len(r['focos']) for r in mirados)
    ha = sum(r['area_focos_ha'] for r in mirados)

    # El archivo de esta fecha se limpia ANTES de cualquier retorno temprano. Si no,
    # una segunda corrida del mismo dia que falla deja vivo el mapa de la corrida
    # buena de la mañana, y `publicar_ultimo` lo publica como vigente.
    os.makedirs(a.salida, exist_ok=True)
    ruta = os.path.join(a.salida, 'focos_%s_%s.geojson' % (sitio.clave, a.hasta))
    if os.path.exists(ruta):
        os.remove(ruta)

    if not mirados:
        # UNA AVERIA NO ES MAL TIEMPO. Si ningun lote se pudo mirar y la causa fue
        # una EXCEPCION (cuota de GEE agotada, EEException, timeout), el sitio no es
        # "no evaluable por nubes": esta roto. Para un cliente `solo_focos` este es
        # el UNICO producto, asi que una averia persistente que sale como
        # NO_EVALUABLE —que esta en NO_FALLO— no despierta nunca a nadie.
        averias = sorted({r['error'] for r in por_lote.values() if r.get('error')})
        for lid, r in sorted(por_lote.items()):
            print('   %-20s %s' % (lid, r.get('nota')))
        if averias and all(r.get('error') for r in por_lote.values()):
            print('[FALLO] ningun lote se pudo mirar y TODOS fallaron por averia '
                  '(%s). Esto no es falta de escenas: es el servicio.'
                  % ', '.join(averias))
            return 1
        print('[NO EVALUABLE] ningun lote tuvo un par de escenas utilizable. '
              'No se pudo mirar.')
        return NO_EVALUABLE

    # CADUCIDAD. `focos.VENTANA_DIAS` busca hasta 90 dias hacia atras, asi que una
    # corrida de septiembre con nubes desde agosto seguiria formando el par
    # 07-15/07-10 y devolviendo SIN_NOVEDAD con imagenes de 50 dias. El ranking ya
    # declara SIN DATO pasados `CADUCIDAD_DIAS`; aca no habia equivalente.
    def _atras(f):
        from datetime import date as _d
        try:
            y1, m1, d1 = (int(x) for x in str(f)[:10].split('-'))
            y2, m2, d2 = (int(x) for x in str(a.hasta)[:10].split('-'))
            return (_d(y2, m2, d2) - _d(y1, m1, d1)).days
        except Exception:
            return None
    frescos = [r for r in mirados
               if (_atras(r['fecha_img']) or 0) <= rk.CADUCIDAD_DIAS]
    if not frescos:
        viejas = sorted({str(r['fecha_img'])[:10] for r in mirados})
        print('[NO EVALUABLE] la escena mas reciente utilizable es de hace mas de %d '
              'dias (%s). No se puede decir nada de hoy con eso.'
              % (rk.CADUCIDAD_DIAS, ', '.join(viejas)))
        return NO_EVALUABLE
    mirados = frescos

    # CEGUERA PARCIAL, MEDIDA POR AREA. "Al menos un lote mirado" no alcanza: en
    # Santo Antonio los dos lotes son 18,1 ha y 120,4 ha, asi que mirar el chico y
    # perder el grande deja el 87% del campo sin observar — y el contrato de salida
    # diria "se evaluo y no hay nada que reportar".
    def _ha(r):
        return float(r.get('area_lote_ha') or 0.0)
    ha_total = sum(_ha(r) for r in por_lote.values())
    ha_mirada = sum(_ha(r) for r in mirados)
    frac = (ha_mirada / ha_total) if ha_total > 0 else float(len(mirados)) / len(ids)
    if frac < COBERTURA_MINIMA_SITIO and not n_focos:
        # Con focos SI se entrega: encontrar algo en la parte que se vio es un
        # resultado valido. Lo que no se puede afirmar es que NO haya nada cuando
        # la mayor parte del campo quedo sin mirar.
        print('[NO EVALUABLE] solo se miro el %.0f%% del area del sitio (%.1f de '
              '%.1f ha) y no se encontraron focos ahi. No alcanza para decir que el '
              'campo esta limpio.' % (100 * frac, ha_mirada, ha_total))
        for lid, r in sorted(por_lote.items()):
            if not r.get('fecha_img'):
                print('   %-20s sin mirar — %s' % (lid, r.get('nota')))
        return NO_EVALUABLE
    # SE ESCRIBE SIEMPRE, TAMBIEN CON CERO FOCOS.
    #
    # Auditado 2026-07-27: no escribir nada cuando el campo esta limpio dejaba a la
    # corrida de hoy SIN RASTRO, y `publicar_ultimo` volvia a publicar el mapa de la
    # semana pasada — el tablero lo mostraba en verde como la accion de hoy y el
    # WhatsApp decia "Hay entrega nueva" con una fecha vieja. Tres mentiras
    # encadenadas a partir de un archivo que faltaba.
    #
    # Un archivo con cero focos ES la entrega: dice "hoy se miro y no hay manchas",
    # que es informacion, y ademas pisa cualquier archivo previo de esta fecha.
    paquete = fo.a_geojson(sitio, por_lote, perimetro=_perimetro(gj))
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(paquete, fh, ensure_ascii=False)

    # --- CAPAS DE CONTEXTO ----------------------------------------------------
    # Zonas estructurales y estratos de siembra. Van a SU PROPIO archivo y NO al
    # geojson de la app: PIX Scout convierte en foco todo lo que no sea perimetro,
    # asi que mezclarlas mandaria al tecnico a caminar una zona de suelo como si
    # fuera un brote de la semana. Ver la cabecera de `capas.py`.
    #
    # Y son NO BLOQUEANTES por diseño: si fallan, la entrega principal sale igual.
    # Una capa de contexto que voltea la corrida nocturna cuesta mas de lo que vale.
    capas_por_lote = _capas_de_contexto(sitio, gj, por_lote, a)

    # --- PAQUETE DE VALIDACION A CIEGAS --------------------------------------
    # Solo si el cliente lo pidio. Agrega puntos de control y escribe la clave en un
    # archivo separado. NO BLOQUEANTE: si falla, la entrega normal sale igual.
    if getattr(sitio, 'validacion_campo', False):
        _paquete_validacion(sitio, gj, por_lote, a)

    print('\n%d de %d lote(s) evaluado(s):' % (len(mirados), len(ids)))
    for lid, r in sorted(por_lote.items()):
        if not r.get('fecha_img'):
            print('   %-20s NO EVALUABLE — %s' % (lid, r.get('nota') or 'sin par de escenas'))
        else:
            print('   %-20s %s vs %s · %d foco(s) · %.2f ha · %.1f%% del area util'
                  % (lid, r['fecha_img'], r['fecha_ref'], len(r['focos']),
                     r['area_focos_ha'], r['pct_util'] or 0.0))
    # EL INFORME TAMBIEN EN CAMPO CHICO. Sin el, este cliente recibe poligonos rojos
    # y ningun documento: las advertencias que declaran que esto no dice la causa y
    # que NO tiene tasa de falsa alarma validada vivian solo en la rama de ranking.
    # Se genera SIEMPRE, tambien con cero focos: "se miro y esta limpio" es el
    # entregable de esa ronda, y ademas deja constancia de lo que NO se pudo mirar.
    pdf = None
    try:
        from . import clientes as cl
        from . import informe_focos as inf
        cliente = cl.de_sitio(sitio.clave)
        if cliente is not None:
            geoms = {str(f['properties'].get(sitio.campo_id)): f['geometry']
                     for f in gj['features']}
            feats = {str(f['properties'].get(sitio.campo_id)): f
                     for f in gj['features']}
            pdf = inf.generar(
                cliente, sitio, por_lote, geoms,
                os.path.join(a.salida, 'Informe_%s_%s.pdf' % (sitio.clave, a.hasta)),
                a.hasta, feats=feats, contexto=capas_por_lote)
    except Exception as e:                       # noqa: BLE001 — se declara y sigue
        # El PDF es importante pero no puede tumbar la entrega del GeoJSON, que es
        # lo que el tecnico necesita para salir. Se avisa fuerte.
        print('  [AVISO] no se pudo generar el informe: %s: %s'
              % (type(e).__name__, str(e)[:120]))

    if pdf:
        print('  -> %s' % pdf)
    if n_focos:
        print('  -> %s (%d focos, %.2f ha)' % (ruta, n_focos, ha))
        return ENTREGADO
    print('\nSe miraron %d lote(s) y no hay focos sobre la unidad minima. '
          'Esto SI es "sin novedad".' % len(mirados))
    return SIN_NOVEDAD


# CODIGOS DE SALIDA. Los tres primeros NO son fallos, y son TRES cosas distintas.
#
# Hasta 2026-07-27 "mire y no hay nada" y "no pude mirar" salian los dos con 0, y el
# resumen los rotulaba igual: "sin novedad". Medido sobre la campaña de trigo de
# Santo Antonio / Sao Francisco, donde el 84% de las observaciones no son plenas: el
# cliente habria visto "sin novedad" todos los dias de la campaña sin que el motor
# hubiera evaluado un solo lote. Es la peor falla posible en un producto de alerta,
# porque tranquiliza.
ENTREGADO = 10        # hay ranking y hay entregable
SIN_NOVEDAD = 0       # se evaluo y no hay nada que reportar
NO_EVALUABLE = 20     # NO se pudo evaluar: faltan escenas, nubes, o serie corta
FUERA_CAMPANA = 21    # no toca mirar: fuera de las ventanas declaradas
NO_FALLO = (ENTREGADO, SIN_NOVEDAD, NO_EVALUABLE, FUERA_CAMPANA)


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — ranking de lotes')
    p.add_argument('--sitio', default='HDS', choices=sorted(cfg.SITIOS))
    p.add_argument('--desde', default=None, help='YYYY-MM-DD (def: 150 dias atras)')
    p.add_argument('--hasta', default=str(date.today()))
    p.add_argument('--K', type=int, default=None, help='capacidad de scouting')
    p.add_argument('--serie', default=None, help='CSV ya extraido, para no repetir GEE')
    p.add_argument('--salida', default='salida')
    p.add_argument('--control-nulo', action='store_true',
                   help='corre la puerta 2.1 y reporta la tasa de alarma')
    p.add_argument('--sin-focos', action='store_true',
                   help='no corre el acercamiento intra-lote (mas rapido)')
    p.add_argument('--sin-radar', action='store_true',
                   help='no consulta Sentinel-1 por los lotes sin observacion')
    p.add_argument('--solo-focos', action='store_true',
                   help='campo chico: acercamiento intra-lote, sin ranking de cohorte')
    a = p.parse_args(argv)

    sitio = cfg.SITIOS[a.sitio]
    # Fuera de campaña el criterio no distingue cosecha de deterioro: en madurez
    # el NDMI baja y el PSRI sube, que es la firma que busca. Se para aca.
    if sitio.campanas and not rk.dentro_de_campana(a.hasta, sitio):
        vent = " · ".join("%s..%s" % v for v in sitio.campanas.values())
        print("[NO-OP] %s esta FUERA de las campañas declaradas de %s (%s). "
              "En cosecha/madurez la firma de senescencia es indistinguible del "
              "deterioro: no se emite ranking." % (a.hasta, sitio.clave, vent))
        return FUERA_CAMPANA
    os.makedirs(a.salida, exist_ok=True)

    # CAMPO CHICO: se decide ACA, antes de gastar una extraccion de serie completa
    # cuyo resultado el criterio va a descartar igual por falta de cohorte. No se
    # finge un ranking que no se puede calcular.
    if a.solo_focos or getattr(sitio, 'solo_focos', False):
        return _entregar_acercamiento(sitio, a)

    # La ventana arranca con la CAMPAÑA, no N dias atras: el estimador de cohorte
    # necesita ver la emergencia. Ver ranking.inicio_de_campana para lo que paso al
    # cortar a 150 dias (188 de 207 lotes quedaron sin ciclo y el ranking salio vacio).
    desde = a.desde or rk.inicio_de_campana(a.hasta, sitio)
    if not desde:
        desde = str(pd.Timestamp(a.hasta) - pd.Timedelta(days=150))[:10]
        print(f'[aviso] {sitio.clave} no declara campañas: se usan 150 dias hacia atras. '
              'Sin ver la emergencia, la cohorte puede salir sin ciclo.')
    print(f'[ventana] {desde} .. {a.hasta}')

    if a.serie:
        df = pd.read_csv(a.serie, parse_dates=['fecha'])
        # Una serie archivada ANTES de cambiar de ejes no trae la columna que el
        # criterio ahora necesita, y reventaba con un `KeyError: 'Column not found:
        # NDRE'` desde adentro de `residuos`, sin decir que el problema es el CSV.
        faltan = [e for e in cfg.EJES if e not in df.columns]
        if faltan:
            raise SystemExit(
                '[ERROR] la serie %s no tiene %s.\n'
                '        Fue extraida con otra configuracion de ejes (EJES=%s).\n'
                '        Volve a extraerla sin --serie, o usa una serie nueva.'
                % (a.serie, ', '.join(faltan), ' + '.join(cfg.EJES)))
        # Una serie extraida antes de declararse el filtro trae pista y monte.
        validas = cfg.unidades_validas(sitio)
        if validas is not None:
            antes = df['lote_id'].nunique()
            df = df[df['lote_id'].astype(str).isin(validas)]
            fuera = antes - df['lote_id'].nunique()
            if fuera:
                print(f'{fuera} unidades descartadas por no ser cultivo')
    else:
        # NO usar ee.Initialize() a secas: en la nube no hay credencial personal y la
        # primera corrida real murio con "Please authorize access to your Earth Engine
        # account". Ver ee_init.
        from .ee_init import inicializar
        print('[GEE] %s' % inicializar())
        df = sr.extraer(sitio, desde, a.hasta)
        if df.empty:
            print('[NO EVALUABLE] sin ninguna escena S2 en la ventana. No es que no '
                  'haya nada: es que no se pudo mirar.')
            return NO_EVALUABLE
        df.to_csv(os.path.join(a.salida, f'serie_{sitio.clave}.csv'), index=False)

    plenas = (df['calidad'] == 'pleno').sum()
    if plenas == 0:
        # No se inventa un rojo con escena nublada: se declara y se sale limpio.
        print('[NO EVALUABLE] %d fila(s) en la ventana y NINGUNA observacion plena '
              '(todo nube, sombra o cobertura parcial). No se pudo mirar.' % len(df))
        return NO_EVALUABLE

    # COHORTE. La especificacion la declara obligatoria (Paso 2) y, a falta de fecha
    # de siembra declarada, manda estimarla del satelite y rotularla como estimada.
    # Medido sobre HDS: con cohorte unica el criterio marcaba 1,3% contra un nulo de
    # 2,0% — no discriminaba nada. Con cohorte estimada por fenologia pasa a 4,7%
    # contra 3,1%. No es un ajuste: sin cohorte el criterio esta ciego.
    if 'cohorte' not in df.columns:
        df = coh.estimar(df)
    # DOS FILTROS DISTINTOS VACIAN ESTO, y se arreglan de manera OPUESTA:
    #   · `residuos` descarta las cohortes de menos de MIN_LOTES_COHORTE -> el campo
    #     es CHICO. Esperar no sirve: no va a haber mas lotes la semana que viene.
    #   · `ewma` descarta los lotes con menos de MIN_OBS_LOTE plenas -> falta SERIE.
    #     Esperar SI sirve: con dos escenas limpias mas, entrega.
    # Diagnosticarlos juntos manda a revisar lo que no es. Se separan a proposito.
    res = rk.residuos(df)
    n_lotes = df['lote_id'].nunique()
    if res.empty:
        print('[NO EVALUABLE] el criterio compara cada lote contra la MEDIANA DE SU '
              'COHORTE y ninguna cohorte llega a %d lotes (el sitio tiene %d). '
              'Esperar no lo resuelve: para un campo de esta escala el producto que '
              'corresponde es el acercamiento intra-lote, no el ranking entre lotes.'
              % (rk.MIN_LOTES_COHORTE, n_lotes))
        return NO_EVALUABLE
    car = rk.ewma(res)
    if car.empty:
        # Cuantas tiene el mejor lote: sin ese numero, "serie insuficiente" no dice
        # si falta una escena o faltan diez, y no se puede decidir si esperar sirve.
        try:
            mejor = int(df[df['calidad'] == 'pleno']
                        .groupby('lote_id').size().max())
        except Exception:
            mejor = 0
        print('[NO EVALUABLE] ningun lote llega a %d observaciones plenas '
              '(el mejor tiene %d, sobre %.0f%% de observaciones plenas en la '
              'ventana). Falta SERIE, no falta campo: con un par de escenas limpias '
              'mas, entrega. NO es "sin novedad".'
              % (rk.MIN_OBS_LOTE, mejor, 100 * (df['calidad'] == 'pleno').mean()))
        return NO_EVALUABLE

    # Se calcula el ranking COMPLETO y aparte el recortado por K. El informe declara
    # cuantos lotes quedaron SIN DATO, y eso desaparece en el recorte.
    rank_todos = rk.ranking(car, fecha=a.hasta, K=None)
    cob = (df['calidad'] == 'pleno').mean()
    rank = rk.ranking(car, fecha=a.hasta, K=a.K)
    n_at = int((rank['estado'] == 'ATENCION').sum())
    n_vi = int((rank['estado'] == 'VIGILANCIA').sum())

    csv = os.path.join(a.salida, f'ranking_{sitio.clave}_{a.hasta}.csv')
    rank.to_csv(csv, index=False)
    gj = os.path.join(a.salida, f'lotes_{sitio.clave}_{a.hasta}.geojson')
    n = _geojson_salida(sitio, rank, gj)

    # ACERCAMIENTO: donde dentro del lote. Corre SOLO sobre los alertados — bajar a
    # pixel en la cartera entera cuesta y no aporta: si el lote no salio de control,
    # no hay a donde mandar a nadie. Si falla, se entrega igual el ranking: el
    # acercamiento es precision adicional, no el producto.
    focos_por_lote, geometrias, gj_focos, tasa_nula = {}, {}, None, None
    alertados = rank[rank['estado'].isin(('ATENCION', 'VIGILANCIA'))]['lote_id']
    alertados = [str(x) for x in alertados]

    # LA LIMPIEZA DEL MAPA VIEJO VA ANTES Y FUERA DEL `if`, o no cubre nada.
    # Estaba DENTRO del bloque de acercamiento, asi que no corria cuando hoy no hay
    # ningun alertado, ni con `--sin-focos` (que es como lo llama la nube), ni si el
    # acercamiento tiraba excepcion. Caso real: la corrida de la mañana escribe 3
    # focos; la de la tarde no alerta a nadie y los deja — el ranking dice "ningun
    # lote sale de control" y al lado se publica un GeoJSON con 3 focos de la MISMA
    # fecha. Auditado 2026-07-27.
    _ruta_focos = os.path.join(a.salida, f'focos_{sitio.clave}_{a.hasta}.geojson')
    if os.path.exists(_ruta_focos):
        os.remove(_ruta_focos)
        print('  [limpieza] se borro el focos_*.geojson previo de esta fecha')

    if alertados and not a.sin_focos:
        try:
            from . import focos as fo
            # Con `--serie` la extraccion no corrio y GEE quedo sin inicializar; el
            # acercamiento SI necesita imagenes. Sin esto, reprocesar una serie
            # cacheada perdia los focos con un EEException por lote.
            if a.serie:
                from .ee_init import inicializar
                print('[GEE] %s' % inicializar())
            print(f'\n[acercamiento] {len(alertados)} lote(s) alertado(s)')
            focos_por_lote = fo.detectar(sitio, alertados, a.hasta)
            with open(sitio.lotes_geojson, encoding='utf-8') as fh:
                _gj = json.load(fh)
            geometrias = {str(f['properties'].get(sitio.campo_id)): f['geometry']
                          for f in _gj['features']}
            paquete = fo.a_geojson(sitio, focos_por_lote, perimetro=_perimetro(_gj))
            n_f = len([f for f in paquete['features']
                       if f['properties'].get('tipo') != 'perimetro'])
            # El archivo previo de esta fecha ya se borro arriba, fuera del `if`.
            if n_f:
                gj_focos = _ruta_focos
                with open(gj_focos, 'w', encoding='utf-8') as fh:
                    json.dump(paquete, fh, ensure_ascii=False)
            # NO se corre la "puerta" del acercamiento: auditada 2026-07-26 y
            # rechazada. Detector y nula parten las dos colas del MISMO campo de
            # delta, con el mismo estimador y el mismo par de fechas: estan
            # anticorrelados por construccion y ante una sombra de nube el detector
            # marca 25% y la puerta devuelve 0,09%. Ver focos.control_nulo.
            # Hasta tener una nula que no comparta el estimador, el acercamiento
            # entrega POLIGONOS Y HECTAREAS, no una tasa de falsa alarma.
        except Exception as e:
            print(f'  [AVISO] acercamiento no disponible: {type(e).__name__}: {e}')
            focos_por_lote = {}

    # CONTINUIDAD POR RADAR. Se consulta SOLO por los lotes que el criterio optico
    # declaro SIN DATO: son el agujero real del producto (66% de los lotes lo sufre
    # en algun momento, con huecos de hasta 175 dias). El radar no dice si hay
    # enfermedad —no puede—, dice si hubo un cambio ESTRUCTURAL grueso. Convierte
    # un "no se" en "no vi cambio" o en "andá a mirar".
    radar_estados, radar_res = {}, None
    # OJO: los lotes SIN DATO del ranking NO son todos los que quedaron sin mirar.
    # Un lote que nunca alcanzo MIN_OBS_LOTE observaciones plenas ni siquiera ENTRA
    # al ranking (`ranking.ewma` lo descarta), asi que no figura como SIN DATO: es
    # invisible. Medido sobre HDS 2025/26 al 2026-04-29: 207 lotes en la serie, 133
    # en el ranking, **74 invisibles**. El informe decia "4 lote(s) sin observacion"
    # cuando el numero real era 78, y el radar se consultaba solo por esos 4.
    en_ranking = set(str(x) for x in rank_todos['lote_id'])
    invisibles = sorted(set(str(x) for x in df['lote_id']) - en_ranking)
    sin_dato_ids = [str(x) for x in
                    rank_todos.loc[rank_todos['estado'] == 'SIN DATO', 'lote_id']]
    sin_mirar_ids = sin_dato_ids + invisibles
    if invisibles:
        print(f'\n[cobertura] {len(invisibles)} lote(s) NO entraron al ranking por '
              f'serie insuficiente (<{rk.MIN_OBS_LOTE} observaciones plenas)')
    if sin_mirar_ids and not a.sin_radar:
        try:
            from . import radar as rad
            print(f'\n[radar] {len(sin_dato_ids)} lote(s) sin observacion optica')
            if a.serie:
                from .ee_init import inicializar
                inicializar()
            dfr = rad.extraer(sitio, desde, a.hasta)
            if not dfr.empty:
                coh_tab = (df[['lote_id', 'cohorte']].drop_duplicates()
                           if 'cohorte' in df.columns else None)
                todos_r = rad.cambio_estructural(dfr, a.hasta, cohortes=coh_tab)
                radar_estados = {k: v for k, v in todos_r.items()
                                 if k in set(sin_mirar_ids)}
                radar_res = rad.resumen(radar_estados)
                if radar_res:
                    print('  cambio estructural: %d | sin cambio: %d | sin dato: %d'
                          % (radar_res['cambio'], radar_res['sin_cambio'],
                             radar_res['sin_dato']))
        except Exception as e:
            # La continuidad es una mejora, no el producto: si falla se entrega igual.
            print(f'  [AVISO] radar no disponible: {type(e).__name__}: {e}')

    # Informe PDF. El ranking que se le pasa es el COMPLETO (rank_todos), no el cortado
    # por K: el informe tiene que poder declarar cuantos lotes quedaron sin observacion,
    # y eso no esta en el recorte.
    pdf = os.path.join(a.salida, f'Informe_{sitio.clave}_{a.hasta}.pdf')
    try:
        from . import informe as inf
        inf.generar(sitio, sitio, rank_todos, pdf, a.hasta,
                    cobertura=cob, huecos=getattr(sitio, 'hueco_dias', None),
                    focos=focos_por_lote, geometrias=geometrias,
                    falsa_alarma=tasa_nula, radar=radar_res,
                    sin_mirar=len(sin_mirar_ids),
                    total_lotes=int(df['lote_id'].nunique()),
                    hay_geojson_focos=bool(gj_focos))
    except Exception as e:
        # El PDF es presentacion; el CSV y el GeoJSON son el producto. Si el informe
        # falla se avisa y se entrega igual, en vez de perder la corrida entera.
        print(f'  [AVISO] no se pudo generar el PDF: {type(e).__name__}: {e}')
        pdf = None

    cob = (df['calidad'] == 'pleno').mean()
    print(f'\n{sitio.titulo} — corte {a.hasta}')
    print(f'  observaciones plenas: {cob*100:.1f}% de las disponibles')
    print(f'  lotes evaluados     : {len(rank)}')
    print(f'  ATENCION            : {n_at}')
    print(f'  VIGILANCIA          : {n_vi}')
    if n_at == 0 and n_vi == 0:
        print('  >> ningun lote sale de control. No hay a donde mandar al tecnico.')
    print(f'  -> {csv}')
    print(f'  -> {gj} ({n} lotes)')
    if gj_focos:
        n_f = sum(len(r['focos']) for r in focos_por_lote.values())
        ha = sum(r['area_focos_ha'] for r in focos_por_lote.values())
        print(f'  -> {gj_focos} ({n_f} focos, {ha:.2f} ha)')
    if pdf:
        print(f'  -> {pdf}')

    if a.control_nulo:
        t = rk.control_nulo(df, n_rep=10)
        print(f'\n  PUERTA 2.1 control nulo: tasa de alarma {100*t:.1f}%')
        print('  (referencia: Gi* sobre el indice crudo marca ~30%)')

    return ENTREGADO


if __name__ == '__main__':
    sys.exit(main())
