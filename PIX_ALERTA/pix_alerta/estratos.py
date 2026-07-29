# -*- coding: utf-8 -*-
"""ESTRATOS DE SIEMBRA: separar el lote en bloques de la misma edad real.

POR QUE ESTE MODULO EXISTE
--------------------------
El 2026-07-29 se encontro, mirando la imagen del 31/05 de Santo Antonio-02, que el
lote esta sembrado en TRES pasadas y que los bloques se ven a simple vista: marron
al fondo, verde medio al centro, verde oscuro en la cabecera junto al camino. Las
superficies dieron 37,6 / 38,4 / 39,1 ha — casi exactamente tercios.

Y lo que importa: **ninguno de los dos criterios del motor lo habria detectado.**
No hubo cambio brusco, asi que el criterio temporal no marca; y dentro de cada
bloque todos los pixeles estan igual de atrasados entre si, asi que el criterio
espacial tampoco. La referencia de "sano" NO estaba dentro del lote: estaba en los
otros bloques A LA MISMA EDAD.

Medido en ese lote, dia en que cada estrato alcanza NDVI 0,80:

    cabecera (1a siembra)   dia 37
    segunda siembra         dia 48    -> 11 dias de atraso (declarado: 3)
    fondo (ultima siembra)  dia 73    -> 35 dias de atraso (declarado: 9)

El cliente confirmo despues que el fondo NO se resembro: fue siembra normal
retrasada por lluvias. O sea que el desfase real era mayor que el recordado, y el
satelite lo midio bien. **Esa comparacion —desfase MEDIDO contra DECLARADO— es en
si misma un producto**: una diferencia grande es implantacion fallida, resiembra o,
como aca, una siembra que se corrio y nadie anoto.

QUE HACE
--------
1. `escena_de_separacion`  elige la fecha donde los bloques MAS se distinguen.
2. `segmentar`             parte el lote en estratos y VALIDA que sean bloques
                           reales y no ruido.
3. `desfase`               mide el atraso de cada estrato en dias.
4. `contraste`             compara el desfase medido contra el declarado.

LIMITE DECLARADO: si el lote se sembro en una sola pasada, no hay estratos que
encontrar y el modulo lo dice en vez de inventar tres. La puerta es la coherencia
espacial: un bloque de siembra es CONTIGUO; el ruido esta desparramado.
"""
import ee

from . import config as cfg
from . import criterio as cr
from . import series as sr

ESCALA = 20
# PUERTA DE COHERENCIA ESPACIAL, derivada de la NULA y no de un cultivo.
#
# Es la fraccion de pixeles cuyo vecindario 3x3 pertenece mayoritariamente a su
# mismo estrato. Un bloque de siembra es CONTIGUO; una clasificacion de ruido no.
#
# ⚠️ NO se fija un numero absoluto. Con `n` estratos, una clasificacion al azar da
# coherencia ~1/n (0,33 con tres, 0,50 con dos). El umbral se calcula como el punto
# medio entre esa nula y el 1 perfecto, lo cual lo hace valido para cualquier
# cantidad de estratos y para cualquier cultivo:
#
#     umbral(n) = 1/n + FACTOR * (1 - 1/n)
#
# Con FACTOR=0,70 y n=3 da 0,80, que es el valor con el que se verifico sobre trigo
# (3 lotes de una sola siembra dieron 0,69-0,78 y el de tres pasadas 0,93). Pero el
# 0,80 sale de la formula, no al reves: con n=2 la formula da 0,85 y con n=4, 0,78.
FACTOR_COHERENCIA = 0.70
# Fraccion del RECORRIDO de NDVI del cultivo a la que se compara la edad de los
# estratos. NO un valor absoluto: 0,80 de NDVI es plena cobertura en trigo pero
# puede ser inalcanzable en un cultivo de dosel ralo y ya saturado en otro. Se toma
# el 75% del camino entre el minimo y el maximo observados en el propio lote, que es
# la zona de crecimiento rapido —donde las curvas mas se separan— y esta por debajo
# de la saturacion, donde todos los estratos llegan juntos y el atraso se aplasta.
FRACCION_REFERENCIA = 0.75
MIN_SEPARACION = 0.12      # diferencia minima de NDVI entre estratos vecinos


def umbral_coherencia(n):
    """Puerta de coherencia para `n` estratos, derivada de la nula 1/n."""
    nula = 1.0 / max(n, 2)
    return nula + FACTOR_COHERENCIA * (1.0 - nula)


def escena_de_separacion(geom, desde, hasta):
    """Fecha en que los bloques MAS se distinguen: la de mayor dispersion de NDVI.

    No se elige a mano. Antes del cierre del dosel los bloques tienen NDVI muy
    distinto; despues todos saturan cerca de 0,93 y se vuelven indistinguibles. La
    fecha de maxima dispersion es, por construccion, la mejor para separarlos.
    """
    col = cr._coleccion_limpia(geom, desde, hasta, cob_minima=0.85)
    n = col.size().getInfo()
    if not n:
        return None, None
    lst = col.toList(n)
    mejor, sd_max = None, -1.0
    fechas = ee.List([ee.Image(lst.get(i)).get('fecha') for i in range(n)]).getInfo()
    sds = ee.List([
        ee.Image(lst.get(i)).select('NDVI').reduceRegion(
            reducer=ee.Reducer.stdDev(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0) for i in range(n)
    ]).getInfo()
    for f, s in zip(fechas, sds):
        if s is not None and float(s) > sd_max:
            mejor, sd_max = f, float(s)
    return mejor, sd_max


def _coherencia(estrato, geom, n):
    """Fraccion de pixeles cuyo vecindario coincide con su propio estrato.

    Es la puerta contra inventar estratos: un bloque de siembra es CONTIGUO, el
    ruido esta desparramado. Con `n` estratos, el azar da ~1/n.
    """
    moda = estrato.focalMode(1.5, 'square', 'pixels')
    igual = estrato.eq(moda)
    return ee.Number(igual.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=geom, scale=ESCALA,
        maxPixels=1e9, bestEffort=True).values().get(0))


def segmentar(geom, fecha, n=3):
    """Parte el lote en `n` estratos por NDVI de `fecha`. Valida que sean bloques.

    Devuelve (imagen de estrato 1..n, dict con coherencia, superficies y cortes) o
    (None, motivo) si los estratos no pasan la puerta de coherencia espacial.
    El estrato 1 es el MAS ATRASADO y el `n` el mas adelantado.
    """
    img = ee.Image(ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                   .filterDate(fecha, ee.Date(fecha).advance(1, 'day'))
                   .filterBounds(geom).sort('CLOUDY_PIXEL_PERCENTAGE').first())
    nd = sr._indices(img).select('NDVI').updateMask(sr._mascara(img))
    pcts = [round(100.0 * i / n, 2) for i in range(1, n)]
    q = nd.reduceRegion(reducer=ee.Reducer.percentile(pcts), geometry=geom,
                        scale=ESCALA, maxPixels=1e9, bestEffort=True).getInfo()
    cortes = sorted(float(v) for v in q.values() if v is not None)
    if len(cortes) != n - 1:
        return None, {'motivo': 'no se pudieron calcular los cortes de NDVI'}

    # Si los cortes estan pegados, no hay bloques distintos: hay un solo cultivo.
    seps = [cortes[i] - cortes[i - 1] for i in range(1, len(cortes))] or [1.0]
    est = ee.Image(1)
    for c in cortes:
        est = est.add(nd.gt(c))
    est = est.updateMask(nd.mask()).rename('estrato')

    coh = _coherencia(est, geom, n)
    areas = ee.Dictionary({
        str(k): est.eq(k).selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0) for k in range(1, n + 1)})
    info = ee.Dictionary({'coherencia': coh, 'areas': areas}).getInfo()
    c = float(info['coherencia'] or 0)
    ha = {int(k): float(v or 0) / 1e4 for k, v in info['areas'].items()}

    diag = {'fecha': fecha, 'cortes': [round(x, 3) for x in cortes],
            'coherencia': round(c, 3), 'areas_ha': {k: round(v, 1) for k, v in ha.items()},
            'separacion_min': round(min(seps), 3) if len(cortes) > 1 else None}
    umbral = umbral_coherencia(n)
    diag['umbral_coherencia'] = round(umbral, 3)
    if c < umbral:
        diag['motivo'] = ('los estratos no son bloques contiguos (coherencia %.2f < '
                          '%.2f): el lote parece de una sola siembra' % (c, umbral))
        return None, diag
    return est, diag


def desfase(geom, estrato, n, desde, hasta, siembra, ndvi_ref=None):
    """Dia (desde `siembra`) en que cada estrato alcanza `ndvi_ref`.

    Comparar curvas desplazadas por su VALOR en una fecha comun es enganoso: hay que
    comparar CUANDO cada una llega al mismo punto. Eso da el atraso en dias, que es
    lo unico que se puede contrastar contra la fecha de siembra declarada.
    """
    import pandas as pd
    col = cr._coleccion_limpia(geom, desde, hasta, cob_minima=0.85)
    m = col.size().getInfo()
    if not m:
        return {}
    lst = col.toList(m)
    fechas = ee.List([ee.Image(lst.get(i)).get('fecha') for i in range(m)]).getInfo()
    series = {k: [] for k in range(1, n + 1)}
    for i, f in enumerate(fechas):
        im = ee.Image(lst.get(i))
        vals = ee.Dictionary({
            str(k): im.select('NDVI').updateMask(estrato.eq(k)).reduceRegion(
                reducer=ee.Reducer.median(), geometry=geom, scale=ESCALA,
                maxPixels=1e9, bestEffort=True).values().get(0)
            for k in range(1, n + 1)}).getInfo()
        dds = (pd.Timestamp(f) - pd.Timestamp(siembra)).days
        for k in range(1, n + 1):
            v = vals.get(str(k))
            if v is not None:
                series[k].append((dds, float(v)))

    # NIVEL DE REFERENCIA DERIVADO DEL PROPIO CULTIVO, no un 0,80 fijo. Se toma el
    # 75% del recorrido entre el minimo y el maximo observados: zona de crecimiento
    # rapido, donde las curvas mas se separan, y por debajo de la saturacion.
    if ndvi_ref is None:
        vals = [v for s in series.values() for _d, v in s]
        if not vals:
            return {}
        lo, hi = min(vals), max(vals)
        ndvi_ref = lo + FRACCION_REFERENCIA * (hi - lo)

    # ⚠️ EL DICCIONARIO DE SALIDA SE MANTIENE HOMOGENEO: claves enteras (el numero
    # de estrato) y nada mas. Meter aca el NDVI de referencia bajo una clave de
    # texto —como estaba— hacia que `sorted(medido.items())` en `contraste` comparara
    # un int con un str y reventara con `TypeError: '<' not supported`. La averia la
    # tapaba el try/except de `analizar`, asi que el analisis de estratos devolvia
    # None en SILENCIO: el motor decia "este lote no tiene estratos" cuando en
    # realidad se habia roto al medir el atraso. Medido en produccion el 2026-07-29
    # sobre SANTO_ANTONIO-02, que es justo el lote que SI tiene tres bloques.
    out = {}
    for k, s in series.items():
        s.sort()
        dia = None
        for i in range(1, len(s)):
            (d0, v0), (d1, v1) = s[i - 1], s[i]
            if v0 <= ndvi_ref <= v1 and v1 > v0:
                dia = d0 + (ndvi_ref - v0) * (d1 - d0) / (v1 - v0)
                break
        out[k] = {'dia_ndvi_ref': round(dia, 1) if dia is not None else None,
                  'serie': s}
    vv = list(out.values())
    base = min((v['dia_ndvi_ref'] for v in vv
                if v.get('dia_ndvi_ref') is not None), default=None)
    for v in vv:
        v['atraso_dias'] = (round(v['dia_ndvi_ref'] - base, 1)
                            if (v.get('dia_ndvi_ref') is not None and base is not None)
                            else None)
        v['ndvi_ref'] = round(ndvi_ref, 3)   # dentro de cada estrato, no como clave
    return out


def analizar(sitio, feat, hasta, geom=None):
    """Todo el analisis de estratos de un lote, o None si el lote no los tiene.

    Es el punto de entrada que usa el motor. Devuelve un dict listo para el informe
    o None cuando el lote se sembro de una sola vez — que es el caso de 3 de los 4
    lotes de trigo, y esta bien que asi sea.
    """
    import pandas as pd
    from . import focos as fo
    siembras = list(getattr(sitio, 'siembras', ()) or [])
    if len(siembras) < 2:
        return None                     # el cliente no declaro varias pasadas
    geom = geom if geom is not None else fo._geom_lote(sitio, feat)
    n = len(siembras)

    # La ventana de busqueda arranca en la primera siembra y corta antes de que el
    # dosel cierre: despues de eso los bloques ya no se distinguen.
    ini = siembras[0]
    # Hasta donde buscar la escena de separacion: los bloques solo se distinguen
    # ANTES del cierre del dosel. Se toma la mitad del ciclo DEL CULTIVO —dato que
    # ya declara `ciclos.py` por especie— y no un numero de dias de trigo.
    from . import ciclos
    try:
        ciclo = (getattr(sitio, 'ciclo_dias', None)
                 or ciclos.CICLOS[sitio.cultivo][0])
    except Exception:
        ciclo = 120
    fin = str(pd.Timestamp(siembras[-1]) + pd.Timedelta(days=int(ciclo * 0.5)))[:10]
    fin = min(fin, str(hasta))
    try:
        fecha, sd = escena_de_separacion(geom, ini, fin)
        if not fecha:
            return None
        est, diag = segmentar(geom, fecha, n=n)
        if est is None:
            diag['sin_estratos'] = True
            return diag
        med = desfase(geom, est, n, ini, str(hasta), siembras[0])
        # El estrato n es el mas adelantado = la PRIMERA siembra declarada.
        decl = {}
        for k in range(1, n + 1):
            i = n - k                   # estrato n -> siembras[0]
            decl[k] = (pd.Timestamp(siembras[i]) - pd.Timestamp(siembras[0])).days
        diag.update({'estrato': est, 'desfase': med,
                     'contraste': contraste(med, decl),
                     'sd_separacion': round(float(sd or 0), 3),
                     'siembras': siembras, 'n': n})
        return diag
    except Exception as e:                       # noqa: BLE001 — se declara y sigue
        # ⚠️ UNA AVERIA NO SE DEVUELVE COMO `None`.
        #
        # `None` significa rio arriba "este lote se sembro de una sola vez", que es
        # un resultado legitimo y tranquilizador. Devolver lo mismo cuando el
        # analisis se ROMPIO hace que una averia se lea como una respuesta.
        #
        # Paso de verdad el 2026-07-29: un `TypeError` al ordenar el contraste dejo
        # a SANTO_ANTONIO-02 —el unico lote con tres bloques reales— reportado como
        # lote de una sola siembra, y la unica huella era una linea de log entre
        # cuarenta. Es la misma regla que el motor ya aplica a NO EVALUABLE contra
        # SIN NOVEDAD: 'no pude mirar' nunca comparte codigo con 'no hay nada'.
        print('  [estratos] AVERIA en %s: %s: %s'
              % (feat['properties'].get(sitio.campo_id),
                 type(e).__name__, str(e)[:100]))
        return {'error': '%s: %s' % (type(e).__name__, str(e)[:120]),
                'averia': True}


def contraste(medido, declarado):
    """Desfase MEDIDO contra DECLARADO. La diferencia ES el producto.

    `declarado` es {estrato: dias de atraso respecto de la primera siembra}. Una
    diferencia grande significa que ese bloque tardo mucho mas en implantarse de lo
    que la fecha de siembra explica: emergencia fallida, resiembra, o una siembra
    que se corrio y nadie anoto. Es una anomalia que NINGUN criterio por pixel ve,
    porque dentro del bloque todo esta igual de atrasado.
    """
    out = {}
    # Solo claves de estrato. Si alguna vez vuelve a colarse una clave de texto, se
    # la ignora en vez de reventar la corrida nocturna por un dato accesorio.
    filas = {k: v for k, v in (medido or {}).items() if isinstance(k, int)}
    for k, v in sorted(filas.items()):
        med = v.get('atraso_dias')
        dec = declarado.get(k)
        dif = (round(med - dec, 1) if (med is not None and dec is not None) else None)
        out[k] = {'medido': med, 'declarado': dec, 'diferencia': dif}
    return out
