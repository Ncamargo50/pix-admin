# -*- coding: utf-8 -*-
"""PUNTOS DE CONTROL: la otra mitad del experimento que el tecnico camina.

POR QUE EXISTE ESTE MODULO
--------------------------
La validacion la hace el tecnico a campo con los mapas del motor. Un recorrido que
visita SOLO lo que el motor marco puede medir una cosa:

    de los puntos que el motor marco, ¿cuantos tenian algo?     -> PRECISION

y no puede medir la que mas falta:

    de los lugares donde HABIA algo, ¿cuantos marco el motor?   -> SENSIBILIDAD

La diferencia no es academica. Un motor SORDO —que casi no marca— da una precision
excelente: los pocos puntos que entrega son los mas extremos del lote y es probable que
tengan algo. Y al mismo tiempo puede estar dejando pasar casi todo. Con solo focos
visitados, los dos motores —el bueno y el sordo— dan el MISMO informe.

Y la sordera no es una hipotesis en este motor. MEDIDO el 2026-07-29 sobre los 4 lotes
reales: la escala del criterio es 2,7 a 6,5 veces el ruido de corto plazo, porque la MAD
de los residuos contra una recta mide sobre todo el ERROR DEL MODELO y no ruido. Eso
comprime el z. Ver el docstring de `criterio.py`.

Por eso el motor entrega tambien PUNTOS DE CONTROL: lugares del mismo lote, dentro del
area que SI se pudo evaluar, que el criterio NO marco, elegidos al azar, y caminados A
CIEGAS mezclados con los focos.

POR QUE AL AZAR Y NO PAREADOS POR VIGOR
---------------------------------------
La tentacion es elegir controles parecidos a los focos en NDVI o en porte para que la
comparacion sea "justa". Eso arruina la medicion: lo que se quiere estimar es cuanto se
le escapa al motor en el RESTO del lote, asi que el control tiene que ser una muestra
REPRESENTATIVA del area no marcada, y para eso el muestreo al azar simple es lo
correcto. Emparejar por vigor sesga la muestra hacia donde el motor casi marco y sube
la sensibilidad aparente.

POR QUE EL CIEGO FUNCIONA — VERIFICADO EN EL CODIGO DE LA APP, NO SUPUESTO
--------------------------------------------------------------------------
Con `MODO_CIEGO` activo (default en `PIX_SCOUT/app/js/config.js`), la app:
  · muestra el nivel de alerta como `—`            (`sevTxt`, app.js)
  · pinta todas las fichas con la misma clase      (`sevCls` devuelve 'media')
  · muestra el score como `·`                      (`scoreTxt`)
  · y el resumen dice "punto asignado para recorrida" (`resumenOf`, geojson.js)
Y cada registro guarda `registro_a_ciegas`: si el tecnico destapo la severidad antes de
anotar, queda asentado y ese registro se puede excluir del analisis.

LO QUE FALTABA CERRAR, Y ES LA RAZON DE `paquete_ciego`: LA ETIQUETA. La app muestra
`props.etiqueta` en la ficha, y los focos salen `F1, F2...`. Un control rotulado `C1` se
delata solo, y nadie lo notaria mirando la app. Aca TODOS los puntos salen `P1, P2...`
en orden mezclado de forma determinista, y la correspondencia va a un archivo aparte que
el telefono no recibe.

LIMITE ESTADISTICO, DECLARADO
-----------------------------
Con pocos controles por lote y por ronda no se estima ninguna tasa: **el valor es
ACUMULATIVO a lo largo de la campaña.** Diez rondas con 3 controles cada una dan 30
negativos, que ya permiten decir algo; una ronda sola, no. `analizar` se niega a dar un
resultado por debajo de `validacion.N_MINIMO_CONFIABLE` en cualquiera de los dos grupos,
en vez de imprimir un porcentaje con dos decimales que nadie deberia creer.

Y el costo es real y hay que decirlo: son puntos EXTRA que el tecnico camina.
"""
import hashlib
import json
import math
import os

import ee

from . import criterio as cri

# AREA del punto de control. Tiene que ser comparable a la de los focos: un control
# mucho mas chico o mas grande recorre otra superficie, y la probabilidad de encontrar
# algo cambia con el area y no con el criterio. Por defecto se toma la unidad minima de
# mapeo de los focos, que es el piso de lo que se le manda a caminar a alguien.
AREA_CONTROL_MINIMA_HA = 0.20
# SEPARACION MINIMA de cualquier foco, en metros. Un control pegado a un foco no es un
# negativo: es el borde del mismo fenomeno. Contarlo como negativo le carga al motor un
# falso negativo que en realidad es un acierto corrido de lugar.
SEPARACION_M = 60.0
# CONTROLES por lote y por ronda. Pocos a proposito: el tecnico camina el doble, no diez
# veces mas. El piso existe para que la ronda aporte negativos aunque no haya focos —que
# es justo cuando mas hace falta saber si el motor esta ciego.
CONTROLES_MIN = 2
CONTROLES_MAX = 6


def _semilla(*partes):
    """Semilla DETERMINISTA. Determinista a proposito: dos corridas del mismo dia tienen
    que mandar al tecnico a los MISMOS puntos, y el experimento tiene que ser
    reproducible meses despues."""
    crudo = '|'.join(str(p) for p in partes)
    return int(hashlib.sha256(crudo.encode('utf-8')).hexdigest()[:8], 16) % (2 ** 31)


def _radio_m(area_ha):
    return math.sqrt(max(float(area_ha), AREA_CONTROL_MINIMA_HA) * 1e4 / math.pi)


def _area_circulo_ha(radio_m):
    return math.pi * radio_m ** 2 / 1e4


def _circulo(lon, lat, radio_m, lados=24):
    """Circulo aproximado en grados. Se hace en el cliente para no gastar un viaje a GEE
    por punto; el error de aproximar el meridiano es de centimetros a esta escala."""
    dlat = radio_m / 111320.0
    dlon = radio_m / (111320.0 * max(math.cos(math.radians(lat)), 1e-6))
    anillo = [[round(lon + dlon * math.cos(2 * math.pi * k / lados), 7),
               round(lat + dlat * math.sin(2 * math.pi * k / lados), 7)]
              for k in range(lados + 1)]
    return {'type': 'Polygon', 'coordinates': [anillo]}


def _separados(feats, dist_m, n):
    """Hasta `n` puntos separados al menos `dist_m` entre si.

    Dos controles superpuestos son un solo control caminado dos veces. Se recorre en el
    orden que devolvio el muestreo —ya aleatorio con semilla fija—, asi que la seleccion
    sigue siendo reproducible.
    """
    out = []
    for f in feats:
        c = ((f or {}).get('geometry') or {}).get('coordinates')
        if not c or len(c) < 2:
            continue
        lon, lat = c[0], c[1]
        choca = False
        for o in out:
            olon, olat = o['geometry']['coordinates'][:2]
            dy = (lat - olat) * 111320.0
            dx = (lon - olon) * 111320.0 * math.cos(math.radians(lat))
            if math.hypot(dx, dy) < dist_m:
                choca = True
                break
        if not choca:
            out.append(f)
        if len(out) >= n:
            break
    return out


def controles_lote(sitio, feat, hasta, n=None, escala=None, area_ha=None,
                   areas_foco=None):
    """Puntos de control de un lote: area evaluada, sin marcar y lejos de los focos.

    Devuelve dict SIEMPRE, con `error` y `nota` cuando no se pudo. Un `None` mudo no se
    distingue de "no habia donde ponerlos", y esa confusion tranquiliza.
    """
    from . import focos as fo
    escala = escala or cri.ESCALA
    lote_id = str(feat['properties'].get(sitio.campo_id))
    base = {'lote_id': lote_id, 'controles': [], 'error': None, 'nota': None,
            'fecha_img': None, 'area_disponible_ha': None}
    try:
        geom = fo._geom_lote(sitio, feat)
        r = cri.para_focos(geom, hasta, sitio=sitio)
    except cri.SinBase as e:
        base['nota'] = str(e)
        return base
    except Exception as e:                          # noqa: BLE001
        base['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
        return base
    base['fecha_img'] = r['fecha_img']

    # ⚠️ EL AREA DE CADA CONTROL SALE DE LAS AREAS DE LOS FOCOS. Encontrado mirando
    # la salida real del 2026-07-16: los cuatro controles median exactamente 0,20 ha y
    # el unico foco 0,441 ha. La app muestra `area_ha` en la ficha, asi que el punto
    # con area distinta ERA el foco, y ademas todos los controles con el MISMO numero
    # forman un patron que se ve de una. El ciego se perdia por un campo que nadie
    # pensaba como revelador.
    #
    # Y ademas es lo correcto por otra razon: la probabilidad de encontrar algo crece
    # con el area recorrida. Si los controles son mas chicos que los focos, la
    # comparacion queda sesgada a favor del motor sin que el criterio tenga merito.
    areas = [a for a in (areas_foco or []) if a and a > 0]
    try:
        # CANDIDATO = area evaluada, MENOS los focos, MENOS su vecindad.
        px = max(int(round(SEPARACION_M / float(escala))), 1)
        cerca = r['foco'].unmask(0, False).focalMax(px, 'circle', 'pixels')
        candidato = r['evaluada'].And(cerca.Not()).selfMask().rename('c')
        n_px = int(candidato.reduceRegion(
            reducer=ee.Reducer.count(), geometry=geom, scale=escala,
            maxPixels=1e9, bestEffort=True).get('c').getInfo() or 0)
    except Exception as e:                          # noqa: BLE001
        base['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
        return base

    disp_ha = n_px * (escala ** 2) / 1e4
    base['area_disponible_ha'] = round(disp_ha, 2)
    # El cupo se calcula con el area MAS GRANDE que va a tener un control.
    radio_max = _radio_m(max(areas) if areas else AREA_CONTROL_MINIMA_HA)
    cupo = int(disp_ha / max(_area_circulo_ha(radio_max) * 3.0, 1e-6))
    n = CONTROLES_MIN if n is None else int(n)
    n = max(min(n, CONTROLES_MAX), 0)
    n = min(n, max(cupo, 0))
    if n < 1:
        base['nota'] = ('no queda area evaluada, sin marcar y a mas de %.0f m de un '
                        'foco donde poner controles (habia %.2f ha)'
                        % (SEPARACION_M, disp_ha))
        return base

    try:
        pts = candidato.sample(
            region=geom, scale=escala, numPixels=max(n * 40, 200),
            seed=_semilla(getattr(sitio, 'clave', ''), lote_id, r['fecha_img']),
            geometries=True, dropNulls=True)
        info = pts.limit(n * 40).getInfo()
    except Exception as e:                          # noqa: BLE001
        base['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
        return base

    for i, p in enumerate(_separados(info.get('features', []), radio_max * 2.0, n)):
        lon, lat = p['geometry']['coordinates'][:2]
        # Se cicla sobre las areas de los focos para que el conjunto de areas de los
        # controles salga del MISMO conjunto de valores. Sin focos en el lote se usa
        # el piso, y en ese caso no hay foco con el que confundirlo.
        a_i = areas[i % len(areas)] if areas else AREA_CONTROL_MINIMA_HA
        rad_i = _radio_m(a_i)
        base['controles'].append({
            'type': 'Feature',
            'geometry': _circulo(lon, lat, rad_i),
            'properties': {'lote_id': lote_id, 'orden': i + 1,
                           'area_ha': round(a_i, 3),
                           'fecha_img': r['fecha_img']}})
    if not base['controles']:
        base['nota'] = ('se muestrearon puntos pero ninguno quedo a mas de %.0f m de '
                        'otro control' % (radio_max * 2))
    return base


# --- el paquete que va al telefono, y la clave que NO ------------------------

# Todo lo que pueda revelar la clase o la severidad se BORRA del paquete de campo.
# `z_sev` y `sev` los usa la app para ordenar y para el color: en modo ciego no los
# muestra, pero si alguien apagara el modo ciego, un archivo de validacion sin estos
# campos sigue siendo ciego. Defensa en profundidad, no confianza en una bandera.
CAMPOS_QUE_REVELAN = ('z_sev', 'sev', 'nivel', 'clase', 'SI', 'etiqueta', 'id',
                      'orden', 'resumen', 'clorofila_pct_vs_mejor5')

# ⚠️ LISTA BLANCA, NO LISTA NEGRA. Encontrado mirando la salida real del 2026-07-16:
# el control llevaba un campo `radio_m` que el foco no tenia, asi que **el CONJUNTO de
# campos delataba la clase** aunque ningun campo individual dijera nada. Una lista
# negra no puede protegerse de eso: hay que enumerar lo que SI viaja, y todo lo demas
# se cae. Asi, un campo nuevo en el foco o en el control no rompe el ciego en silencio.
#
# Son exactamente los campos que la app usa (`app/js/geojson.js`) mas los dos de
# trazabilidad del lazo de retorno.
CAMPOS_DEL_PUNTO = ('id', 'etiqueta', 'name', 'lote_id', 'orden', 'area_ha',
                    'fecha_img', 'hacienda', 'cultivo', 'campana_validacion',
                    'status')


def _limpio(props):
    """Solo los campos de la lista blanca, y con el MISMO conjunto para todos.

    Devuelve las claves que hay; las que falten las completa `paquete_ciego` para que
    ningun punto tenga un conjunto de campos distinto de los demas.
    """
    p = props or {}
    return {k: p[k] for k in CAMPOS_DEL_PUNTO if k in p}


def _centroide(geom):
    """(lon, lat) del promedio de vertices del anillo exterior. None si no se puede.

    Basta el promedio de vertices: el punto solo tiene que caer DENTRO de la mancha
    para que el GPS lleve al tecnico ahi, y los focos son compactos por la MMU.
    """
    if not geom:
        return None
    t, c = geom.get('type'), geom.get('coordinates')
    if t == 'Point':
        return float(c[0]), float(c[1])
    anillo = None
    if t == 'Polygon' and c:
        anillo = c[0]
    elif t == 'MultiPolygon' and c and c[0]:
        anillo = c[0][0]
    if not anillo:
        return None
    pts = [p for p in anillo if isinstance(p, (list, tuple)) and len(p) >= 2]
    if not pts:
        return None
    return (sum(float(p[0]) for p in pts) / len(pts),
            sum(float(p[1]) for p in pts) / len(pts))


def _geometria_uniforme(geom, area_ha):
    """MISMA FORMA para todos los puntos del paquete ciego: un circulo del mismo tipo.

    ⚠️ ESTA ES LA TERCERA FUGA DEL CIEGO DE ESTE PROYECTO, y la encontro una revision
    de la salida real del 2026-08-03. Las dos anteriores fueron de PROPIEDADES y se
    taparon con la lista blanca de `CAMPOS_DEL_PUNTO`. Esta es de GEOMETRIA, que hasta
    hoy viajaba tal cual:

        control -> circulo generado por `_circulo()`, SIEMPRE 25 vertices
        foco    -> poligono vectorizado del raster, forma irregular, 15 vertices

    Y `PIX_SCOUT/app/js/map.js` (`ringFor`) DIBUJA el anillo real cuando el punto lo
    trae. O sea que el tecnico veia circulos perfectos para los controles y una mancha
    irregular para el foco: despues de una sola ronda aprende que "los redondos son los
    de mentira", y a partir de ahi registra distinto sabiendo cual es cual — que es
    exactamente el sesgo de verificacion que la campaña entera existe para evitar.

    POR QUE SE ARREGLA EN EL DATO Y NO EN LA APP: si el ciego dependiera de que la app
    no dibuje la forma, cualquiera que abra el GeoJSON en QGIS —o una version futura de
    la app, u otro visor— vuelve a ver la diferencia. **El ciego tiene que estar en el
    archivo, no en el visor.** Es el mismo principio por el que la clave va en un
    archivo aparte en vez de en un campo oculto.

    QUE SE PIERDE, Y ES ACEPTABLE: la forma real del foco no llega al telefono durante
    una campaña de validacion. No hace falta para caminarlo —el GPS lleva al centro y el
    radio marca hasta donde mirar— y la forma real queda igual en `focos_*.geojson`,
    que es el entregable normal del cliente y no es ciego.
    """
    c = _centroide(geom)
    if c is None:
        return geom
    try:
        a = float(area_ha)
    except (TypeError, ValueError):
        a = AREA_CONTROL_MINIMA_HA
    return _circulo(c[0], c[1], _radio_m(a))


def paquete_ciego(sitio, focos_por_lote, controles_por_lote, fecha, perimetro=None):
    """(geojson, clave). El geojson va al telefono; la clave NO.

    Todos los puntos salen `P1, P2, ...` en orden mezclado determinista. La clave es la
    que permite, cuando vuelven los registros, separar aciertos de falsos negativos.
    """
    puntos = []
    for lid, r in sorted((focos_por_lote or {}).items()):
        for f in r.get('focos', []):
            puntos.append((lid, 'foco', f))
    for lid, r in sorted((controles_por_lote or {}).items()):
        for f in r.get('controles', []):
            puntos.append((lid, 'control', f))

    sem = _semilla(getattr(sitio, 'clave', ''), str(fecha)[:10], len(puntos))
    puntos = [x for _, x in sorted(
        enumerate(puntos),
        key=lambda par: hashlib.sha256(('%d|%d' % (sem, par[0])).encode()).hexdigest())]

    feats, clave = [], {}
    if perimetro is not None:
        feats.append({'type': 'Feature', 'geometry': perimetro,
                      'properties': {'tipo': 'perimetro',
                                     'id': '%s-PERIMETRO' % sitio.clave,
                                     'hacienda': sitio.titulo}})
    for i, (lid, clase, f) in enumerate(puntos):
        etq = 'P%d' % (i + 1)
        pid = '%s-%s' % (lid, etq)
        p = _limpio(f.get('properties'))
        p.update({'id': pid, 'etiqueta': etq, 'name': '%s / %s' % (lid, etq),
                  'lote_id': lid, 'orden': i + 1, 'hacienda': sitio.titulo,
                  'cultivo': getattr(sitio, 'cultivo', '') or None,
                  'campana_validacion': True, 'status': 'pending'})
        # TODOS los puntos con el MISMO conjunto de claves, en el mismo orden. Un campo
        # presente en unos y ausente en otros es una fuga aunque su valor sea inocente.
        p = {k: p.get(k) for k in CAMPOS_DEL_PUNTO}
        # La GEOMETRIA se normaliza igual que las propiedades (ver `_geometria_uniforme`):
        # la forma del poligono delataba la clase aunque ningun campo lo dijera.
        geom_u = _geometria_uniforme(f.get('geometry'), p.get('area_ha'))
        feats.append({'type': 'Feature', 'geometry': geom_u, 'properties': p})
        clave[pid] = {'lote_id': lid, 'clase': clase, 'orden': i + 1,
                      'area_ha': (f.get('properties') or {}).get('area_ha')}
    return ({'type': 'FeatureCollection', 'features': feats},
            {'sitio': getattr(sitio, 'clave', ''), 'fecha': str(fecha)[:10],
             'n_focos': sum(1 for _, c, _ in puntos if c == 'foco'),
             'n_controles': sum(1 for _, c, _ in puntos if c == 'control'),
             'puntos': clave})


def guardar(carpeta, sitio, fecha, geojson, clave):
    """Escribe el paquete de campo y la clave EN ARCHIVOS SEPARADOS.

    Separados a proposito: el geojson se le manda al telefono y la clave NO. Si
    viajaran juntos, alcanzaria con abrir el archivo para saber que punto es foco.
    """
    os.makedirs(carpeta, exist_ok=True)
    f_gj = os.path.join(carpeta, 'validacion_%s_%s.geojson'
                        % (sitio.clave, str(fecha)[:10]))
    f_cl = os.path.join(carpeta, 'CLAVE_validacion_%s_%s.json'
                        % (sitio.clave, str(fecha)[:10]))
    with open(f_gj, 'w', encoding='utf-8') as fh:
        json.dump(geojson, fh, ensure_ascii=False)
    with open(f_cl, 'w', encoding='utf-8') as fh:
        json.dump(clave, fh, ensure_ascii=False, indent=1)
    return f_gj, f_cl


# --- lo que se puede decir cuando vuelven los registros ---------------------

def analizar(claves, registros):
    """Tasa de hallazgo en FOCOS contra la de CONTROLES, con IC de Wilson.

    `claves` es una lista de las claves guardadas (una por ronda: el valor esta en
    ACUMULAR rondas, no en una sola). `registros` son los crudos que devuelve
    `lazo.descargar`.

    Devuelve dict con las dos tasas, sus IC, y `concluyente`. **Se niega a concluir**
    por debajo de `validacion.N_MINIMO_CONFIABLE` en cualquiera de los dos grupos: con
    3 controles no hay nada que decir, y decirlo igual seria peor que callarse.

    LO QUE ESTA COMPARACION SI DICE: si la tasa de hallazgo en los focos NO supera a la
    de los controles, el motor no esta agregando informacion sobre caminar al azar. Ese
    es el piso que tiene que superar, y es una prueba que el motor puede FALLAR — que es
    lo que la hace valer.

    LO QUE NO DICE: no es sensibilidad en sentido estricto. Para eso habria que conocer
    la verdad en TODO el lote, no en una muestra. Lo que estima es la razon entre
    encontrar algo donde el motor marco y encontrarlo donde no marco.
    """
    from . import lazo
    from . import validacion as vl

    clase_de = {}
    for c in (claves or []):
        for pid, d in (c.get('puntos') or {}).items():
            clase_de[pid] = d.get('clase')

    cuenta = {'foco': [0, 0], 'control': [0, 0]}      # [visitados, con hallazgo]
    descartes = {'sin_id_estable': 0, 'id_desconocido': 0, 'sin_hallazgo': 0,
                 'destapo_la_severidad': 0}
    for reg in _filas(registros):
        pid = str(reg.get('focoId') or reg.get('foco_id') or '')
        estable = reg.get('focoIdEstable', reg.get('foco_id_estable', True))
        if estable is False:
            descartes['sin_id_estable'] += 1
            continue
        # Si la app registro que se destapo la severidad antes de anotar, el ciego se
        # rompio para ese punto y no puede entrar al analisis.
        if reg.get('registro_a_ciegas') is False:
            descartes['destapo_la_severidad'] += 1
            continue
        clase = clase_de.get(pid)
        if clase not in ('foco', 'control'):
            descartes['id_desconocido'] += 1
            continue
        h = reg.get('hallazgo')
        if h is None:
            descartes['sin_hallazgo'] += 1
            continue
        cuenta[clase][0] += 1
        if str(h).strip().lower() not in lazo.SIN_HALLAZGO:
            cuenta[clase][1] += 1

    out = {'descartes': descartes}
    for clase in ('foco', 'control'):
        n, ex = cuenta[clase]
        lo, hi = vl.ic_wilson(ex, n) if n else (float('nan'), float('nan'))
        out[clase] = {'n': n, 'con_hallazgo': ex,
                      'tasa': (ex / n) if n else None, 'ic95': (lo, hi)}
    n_min = min(out['foco']['n'], out['control']['n'])
    out['n_minimo'] = n_min
    out['concluyente'] = n_min >= vl.N_MINIMO_CONFIABLE
    if not out['concluyente']:
        out['aviso'] = ('con %d observacion(es) en el grupo mas chico no se puede '
                        'concluir nada (hacen falta %d). Seguir acumulando rondas.'
                        % (n_min, vl.N_MINIMO_CONFIABLE))
    else:
        tf, tc = out['foco']['tasa'], out['control']['tasa']
        out['supera_al_azar'] = bool(tf is not None and tc is not None and tf > tc)
        if not out['supera_al_azar']:
            out['aviso'] = ('la tasa de hallazgo en los focos (%.0f%%) NO supera a la '
                            'de los controles (%.0f%%): con estos datos el motor no '
                            'agrega informacion sobre caminar al azar.'
                            % (100 * (tf or 0), 100 * (tc or 0)))
    return out


def _filas(registros):
    """Itera filas de un DataFrame o de una lista de dicts, sin exigir pandas."""
    if registros is None:
        return []
    if hasattr(registros, 'to_dict'):
        return registros.to_dict('records')
    return list(registros)
