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
# Coherencia espacial minima para aceptar que los estratos son bloques reales.
# Es la fraccion de pixeles cuyo vecindario 3x3 pertenece mayoritariamente a su
# mismo estrato. Un bloque de siembra da valores altos; una clasificacion de ruido
# da ~1/n. Con 3 estratos el azar es 0,33, asi que 0,80 es una puerta exigente.
COHERENCIA_MINIMA = 0.80
NDVI_REFERENCIA = 0.80     # nivel al que se compara la edad de los estratos
MIN_SEPARACION = 0.12      # diferencia minima de NDVI entre estratos vecinos


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
    if c < COHERENCIA_MINIMA:
        diag['motivo'] = ('los estratos no son bloques contiguos (coherencia %.2f < '
                          '%.2f): el lote parece de una sola siembra' %
                          (c, COHERENCIA_MINIMA))
        return None, diag
    return est, diag


def desfase(geom, estrato, n, desde, hasta, siembra, ndvi_ref=NDVI_REFERENCIA):
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
    base = min((v['dia_ndvi_ref'] for v in out.values()
                if v['dia_ndvi_ref'] is not None), default=None)
    for k, v in out.items():
        v['atraso_dias'] = (round(v['dia_ndvi_ref'] - base, 1)
                            if (v['dia_ndvi_ref'] is not None and base is not None)
                            else None)
    return out


def contraste(medido, declarado):
    """Desfase MEDIDO contra DECLARADO. La diferencia ES el producto.

    `declarado` es {estrato: dias de atraso respecto de la primera siembra}. Una
    diferencia grande significa que ese bloque tardo mucho mas en implantarse de lo
    que la fecha de siembra explica: emergencia fallida, resiembra, o una siembra
    que se corrio y nadie anoto. Es una anomalia que NINGUN criterio por pixel ve,
    porque dentro del bloque todo esta igual de atrasado.
    """
    out = {}
    for k, v in sorted(medido.items()):
        med = v.get('atraso_dias')
        dec = declarado.get(k)
        dif = (round(med - dec, 1) if (med is not None and dec is not None) else None)
        out[k] = {'medido': med, 'declarado': dec, 'diferencia': dif}
    return out
