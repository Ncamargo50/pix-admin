# -*- coding: utf-8 -*-
"""CRITERIO v2: trayectoria por pixel + Mahalanobis.  **EN PRODUCCION.**

Criterio por defecto desde 2026-07-29 (`config.CRITERIO = 'v2'`). v1 sigue
disponible en `focos.py` para poder comparar, no como camino de produccion.

LA EVIDENCIA QUE LO APROBO
--------------------------
Tasa de marcado sobre fechas SIN evento (pares consecutivos de la linea base de los
4 lotes de trigo), alfa nominal 1%. Arnes: `medicion/calibrar_criterio.py`.

    lote                v1 mediana   v1 MAXIMO    v2 mediana   v2 MAXIMO
    SANTO_ANTONIO-01       2,11%       9,84%        0,00%       2,17%
    SANTO_ANTONIO-02       0,38%      11,25%        0,00%       1,66%
    SAO_FRANCISCO-01       1,81%      11,81%        0,00%       1,05%
    SAO_FRANCISCO-02       1,25%       7,88%        0,00%       0,19%

**v1 marcaba hasta el 11,8% del lote en fechas donde no pasaba nada.** Ese es el
comportamiento de cuota que se venia sospechando, medido. v2 baja el maximo a 2,2%.

Y ademas recupera area evaluable, que era el otro cuello de botella:

    area evaluada de SANTO_ANTONIO-02:   v1: 49%   ->   v2: 75%
    los otros tres lotes:                          92% a 95%

PERSEGUIR SD(z)=1 FUE UN DESVIO, Y QUEDA ESCRITO
------------------------------------------------
Esa igualdad solo vale si la distribucion es normal; con colas pesadas se puede
tener SD 1,8 con la tasa perfecta o SD 0,4 con la tasa disparada. Lo que decide en
un producto de alerta es la TASA EMPIRICA sobre fechas sin evento. Se llego ahi
despues de cuatro intentos de calibrar por SD; la bitacora esta mas abajo porque el
recorrido vale mas que el resultado.

QUE REEMPLAZA
-------------
El criterio v1 hacia: residuo contra LA ESCENA LIMPIA ANTERIOR, z por eje con MAD
TRANSVERSAL (espacial) de ese par de fechas, y conjuncion `z1<=-2 Y z2<=-2`.

Los cuatro defectos medidos el 2026-07-29, y como los ataca este diseño:

1. **SD(z) va de 0,38 a 1,56 segun lote y eje** (deberia ser 1). Un z mal escalado
   significa que la tasa de falsa alarma NO es la que el umbral implica. Peor: PSRI
   daba SD=0,38, o sea que el corte en -2 equivalia a -5 sigmas reales y como
   segundo eje habria matado toda deteccion.
   -> **La escala pasa a ser TEMPORAL Y POR PIXEL**: la MAD de los residuos del
      propio pixel contra su propia trayectoria. Cada pixel se estandariza por SU
      ruido, que es lo que hace que el z tenga SD 1 por construccion.

2. **La conjuncion de dos z no controla alfa**: la tasa depende de la correlacion r
   entre ejes, que va de 0,17 a 0,82 entre lotes -> el error tipo I varia varias
   veces sin que pase nada en el campo.
   -> **Mahalanobis con la covarianza medida**: `d2 >= chi2(2, 1-alfa)` da alfa FIJA
      y comparable entre lotes, y ademas usa la direccion de la anomalia, no dos
      cortes marginales.

3. **Cobertura 49%, que es exactamente 0,70^2**: no se pierde por nubes, se pierde
   por exigir DOS fechas limpias.
   -> **Solo la fecha `t` tiene que estar limpia.** La referencia la aporta la
      trayectoria, que se arma con todas las observaciones limpias previas. La
      cobertura vuelve a ser p, no p^2.

4. **Var(residuo) = 2*sigma^2 con una sola escena de referencia** (las dos fechas
   aportan ruido). Con N observaciones en la base pasa a `sigma^2*(1+1/N)`: con N=5
   se detecta un cambio 23% mas chico A LA MISMA tasa de falsa alarma.

LO QUE NO CAMBIA, A PROPOSITO
-----------------------------
La nula sigue siendo TEMPORAL: cada pixel contra su propia historia. No se compara
con vecinos ni con otros lotes, porque la nula espacial es falsa por construccion.

LIMITES QUE HAY QUE DECLARAR
----------------------------
· **VENTANA CIEGA.** Un deterioro que empiece DENTRO de la ventana de linea base se
  incorpora a la propia referencia y no se detecta. Con N minimo de observaciones y
  cadencia real de ~10 dias utiles, eso es el primer mes de campaña. Va al informe.
· Un deterioro MUY lento tampoco: la mediana movil lo absorbe. Es el mismo limite
  que tiene cualquier referencia adaptativa, y es el precio de no usar una tabla de
  valores esperados (que no existe como estandar transferible).
· Sigue SIN tasa de falsa alarma validada a campo. Esto mejora la CALIBRACION
  nominal; la puntería real solo la puede medir el campo.
"""
import ee

from . import config as cfg
from . import series as sr

# --- parametros, todos declarados ---------------------------------------------
ESCALA = 20               # m
# Observaciones limpias MINIMAS en la linea base. Con menos, la mediana y la MAD
# temporal son ruido: dos puntos no definen una trayectoria ni una dispersion.
MIN_BASE = 4
VENTANA_BASE_DIAS = 75    # hacia atras desde la fecha evaluada
# Piso de escala en unidades del indice. Mismo argumento que en `focos.SIGMA_MINIMA`:
# por debajo de esto la diferencia entre dos fechas no se puede atribuir al cultivo
# con S2, es ruido radiometrico + BRDF + aerosol residual.
SIGMA_MINIMA = 0.010
# alfa NOMINAL del criterio. chi2 con 2 grados de libertad: d2 >= 9,21 <=> alfa=0,01.
# Es el numero que la conjuncion NO podia fijar.
# Cuanto se puede retroceder buscando una escena CON DATOS para evaluar, y cuanta
# cobertura minima se le exige. Con revisita de 5 dias y nubes, la ultima del
# calendario suele estar tapada: el 2026-07-25 dio 0,00 en los cuatro lotes.
VENTANA_ACTUAL_DIAS = 12
# Cobertura MINIMA de la escena que se evalua. Se toma el MISMO 0,70 que ya usa
# `focos.COB_MINIMA` para decidir si una escena sirve para testear — no un numero
# nuevo elegido a conveniencia.
#
# ⚠️ MEDIDO por que importa: con 0,35, SANTO_ANTONIO-02 elegia la escena del
# 2026-07-20 (cobertura 0,606, medio lote tapado) y el criterio marcaba 3 focos que
# estaban a 16, 20 y 68 m del borde de la nube. O sea: borde de nube otra vez, con
# el criterio nuevo. **El problema no era el criterio: era usar esa escena.** Una
# escena con el 40% del lote enmascarado tiene borde de nube por todas partes, y el
# residuo de bruma que SCL y CloudScore+ no atrapan escala con la cantidad de nube.
COB_MINIMA_ACTUAL = 0.70
ALFA = 0.01
CHI2 = {0.05: 5.991, 0.02: 7.824, 0.01: 9.210, 0.005: 10.597, 0.001: 13.816}


class SinBase(Exception):
    """No hay observaciones limpias suficientes para armar la trayectoria."""


# Fraccion MINIMA de pixel valido sobre el lote para que una escena entre a la base.
# NO es cosmetico: sin esto la coleccion incluye escenas del tile MGRS vecino que
# apenas rozan el lote, y tambien las tapadas por nube. MEDIDO: con la base sin
# filtrar, las dos escenas mas recientes de cada lote no se solapaban y el z salia
# **enteramente enmascarado** (px=0) — que era el origen de los "SD = 0,000" que
# parecian un resultado y eran una serie vacia.
COB_MINIMA_BASE = 0.30


def _coleccion_limpia(geom, desde, hasta, cob_minima=COB_MINIMA_BASE):
    """Imagenes con los ejes, enmascaradas a pixel valido. Sin compuerta de dosel.

    La compuerta de dosel NO va aca: se aplica una sola vez, sobre la linea base
    (ver `evaluar`). Aplicarla por escena es lo que censuraba justo la anomalia —
    un pixel que perdio dosel es el daño que se busca.
    """
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(desde, hasta).filterBounds(geom))

    def preparar(img):
        img = ee.Image(img)
        valido = sr._mascara(img)
        ejes = sr._indices(img)
        # `copyProperties` con system:time_start NO es opcional: `_indices` arma
        # una imagen NUEVA y sin eso la marca de tiempo se pierde. El ajuste de la
        # trayectoria necesita el tiempo de cada escena, y sin el fallaba con
        # "Date: Parameter 'value' is required and may not be null".
        out = (ejes.select(list(cfg.EJES) + ['NDVI']).updateMask(valido)
               .copyProperties(img, ['system:time_start'])
               .set('fecha', ee.Date(img.get('system:time_start'))
                    .format('YYYY-MM-dd')))
        out = ee.Image(out)
        cob = valido.unmask(0, False).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0)
        return out.set('cob', ee.Algorithms.If(cob, cob, 0))

    salida = col.map(lambda i: ee.Image(preparar(i)))
    if cob_minima:
        salida = salida.filter(ee.Filter.gte('cob', cob_minima))
    # UNA OBSERVACION POR FECHA. Un lote sobre un borde MGRS recibe DOS granulos de
    # la MISMA adquisicion (T22KEU y T22KEV): son la misma foto, no dos
    # observaciones. Contarlas dos veces metia pares con hueco CERO en la serie, y
    # esos pares —diferencia casi nula, fenologia nula— arrastraban el estimador de
    # ruido a cero. MEDIDO: SAO_FRANCISCO-01 daba dt=0 y SD(z)=0,03, o sea un sigma
    # ~30x lo que corresponde.
    # `distinct` conserva la PRIMERA de cada fecha, asi que se ordena por cobertura
    # descendente antes: queda la que mas lote cubre.
    # `distinct` devuelve una Collection generica y le hace perder el tipo: sin el
    # `ee.ImageCollection(...)` de abajo, `.count()` explota mas tarde con
    # "'FeatureCollection' object has no attribute 'count'".
    salida = salida.sort('cob', False).distinct(['fecha'])
    return ee.ImageCollection(salida.sort('system:time_start'))


def evaluar(geom, hasta, alfa=ALFA, min_base=MIN_BASE,
            ventana=VENTANA_BASE_DIAS, escala=ESCALA):
    """Mahalanobis del residuo de la fecha `hasta` contra la trayectoria del pixel.

    Devuelve dict con:
        d2        imagen de distancia de Mahalanobis al cuadrado
        anomalia  mascara booleana d2 >= chi2 Y direccion de deterioro
        z         {eje: imagen de z temporal}
        n_base    imagen con cuantas observaciones tiene cada pixel en la base
        fecha     fecha de la escena evaluada
        umbral    el chi2 usado
    """
    import pandas as pd
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin_base = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]

    base = _coleccion_limpia(geom, desde, fin_base)

    # LA ESCENA A EVALUAR ES LA MAS RECIENTE **CON DATOS**, no la mas reciente.
    # Sin este chequeo se tomaba la ultima del calendario aunque estuviera 100%
    # nublada: paso el 2026-07-25, que dio cobertura 0,00 en los cuatro lotes, y
    # todo el z salia enmascarado sin decir por que.
    cand = _coleccion_limpia(
        geom, str(pd.Timestamp(hasta) - pd.Timedelta(days=VENTANA_ACTUAL_DIAS))[:10],
        str(pd.Timestamp(hasta) + pd.Timedelta(days=1))[:10])

    _e0 = list(cfg.EJES)[0]

    def _con_cobertura(img):
        img = ee.Image(img)
        cob = (img.select(_e0).mask()
               .unmask(0, False).reduceRegion(
                   reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
                   maxPixels=1e9, bestEffort=True).values().get(0))
        return img.set('cob', ee.Algorithms.If(cob, cob, 0))

    cand = cand.map(_con_cobertura).filter(ee.Filter.gte('cob', COB_MINIMA_ACTUAL))
    if not cand.size().getInfo():
        raise SinBase('sin escena con al menos %.0f%% de pixel valido en los '
                      'ultimos %d dias' % (100 * COB_MINIMA_ACTUAL,
                                           VENTANA_ACTUAL_DIAS))
    actual = ee.Image(cand.sort('system:time_start', False).first())
    fecha_actual = actual.get('fecha').getInfo()

    ejes = list(cfg.EJES)
    n_base = base.select([ejes[0]]).count().rename('n_base')

    # --- TRAYECTORIA: recta por pixel, no una mediana ------------------------
    #
    # ⚠️ ESTO NO PUEDE SER UNA MEDIANA, y el error se midio. Con la mediana como
    # referencia, los residuos de la base quedan dominados por la FENOLOGIA —el
    # trigo cambia a lo largo de la ventana— y no por el ruido. La MAD de esos
    # residuos sale inflada, sigma sale grande y el z sale APLASTADO:
    #
    #     con mediana constante:  SD(z) = 0,14 a 0,55   (deberia ser 1)
    #
    # Con SD(z)=0,14 el corte en chi2 equivale a varias veces mas sigmas de las
    # declaradas y el criterio no marca NADA. Es el mismo error que ya se habia
    # visto con PSRI en v1, por otro camino.
    #
    # La referencia correcta es la TENDENCIA del propio pixel: se ajusta una recta
    # contra el tiempo y el residuo se mide contra la recta, no contra un nivel.
    # Asi la MAD estima el ruido y no el crecimiento del cultivo.
    dia0 = ee.Date(desde).millis()

    def _con_t(img):
        img = ee.Image(img)
        t = ee.Image(ee.Date(img.get('system:time_start')).millis()
                     .subtract(dia0).divide(86400000)).float().rename('t')
        return t.addBands(img.select(ejes)).updateMask(img.select(ejes[0]).mask())

    con_t = base.map(_con_t)
    pend, orden = {}, {}
    for e in ejes:
        fit = con_t.select(['t', e]).reduce(ee.Reducer.linearFit())
        pend[e] = fit.select('scale')      # pendiente por dia
        orden[e] = fit.select('offset')

    t_act = ee.Number(ee.Date(fecha_actual).millis()).subtract(dia0).divide(86400000)

    def _esperado(e, t):
        return orden[e].add(pend[e].multiply(ee.Image(ee.Number(t))))

    # Residuos de la BASE contra su propia recta -> la MAD estima ruido puro.
    def resid(img):
        img = ee.Image(img)
        t = ee.Number(ee.Date(img.get('system:time_start')).millis())             .subtract(dia0).divide(86400000)
        cap = [img.select(e).subtract(_esperado(e, t)).abs().rename(e) for e in ejes]
        return ee.Image.cat(cap)

    mad = base.map(resid).median().multiply(1.4826)
    sigma = mad.max(SIGMA_MINIMA)

    r_actual = ee.Image.cat(
        [actual.select(e).subtract(_esperado(e, t_act)).rename(e) for e in ejes])
    med = ee.Image.cat([_esperado(e, t_act).rename(e) for e in ejes])
    z = {e: r_actual.select(e).divide(sigma.select(e)).rename('z_' + e)
         for e in ejes}

    # --- Mahalanobis con la covarianza MEDIDA de los z -----------------------
    # La conjuncion de cortes marginales no controla alfa porque la tasa depende de
    # la correlacion entre ejes. La Mahalanobis la usa explicitamente: con la
    # covarianza real, `d2` es chi2 con 2 grados de libertad bajo la nula, sea cual
    # sea r. Es el unico cambio que devuelve un alfa comparable entre lotes.
    zi = ee.Image.cat([z[e] for e in ejes])
    n = len(ejes)
    # `centeredCovariance` es el reductor que devuelve la matriz bajo la clave
    # 'array'; `covariance` no la produce en ese formato y deja el resultado en
    # null, que aguas abajo revienta con "Parameter 'values' may not be null".
    cov = ee.Array(zi.toArray().reduceRegion(
        reducer=ee.Reducer.centeredCovariance(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=True).get('array'))
    # Regularizacion minima: si un eje quedo casi constante la matriz es singular.
    cov = cov.add(ee.Array.identity(n).multiply(1e-6))
    inv = ee.Image(cov.matrixInverse())
    arr = zi.toArray().toArray(1)
    d2 = (arr.arrayTranspose().matrixMultiply(inv)
          .matrixMultiply(arr).arrayGet([0, 0]).rename('d2'))

    umbral = CHI2.get(round(alfa, 3), CHI2[0.01])
    # DIRECCION. La Mahalanobis es simetrica: un pixel que MEJORO mucho tambien da
    # d2 alto. Se exige ademas que el residuo apunte al deterioro en todos los ejes
    # —el mismo sentido que declara `ranking.SIGNO`—, o el motor marcaria el lote
    # que se recupero despues de una lluvia.
    from .ranking import SIGNO
    dir_mala = None
    for e in ejes:
        c = r_actual.select(e).multiply(SIGNO[e]).gte(0)
        dir_mala = c if dir_mala is None else dir_mala.And(c)

    anomalia = (d2.gte(umbral).And(dir_mala)
                .And(n_base.gte(min_base))
                .rename('anomalia'))
    return {'d2': d2, 'anomalia': anomalia, 'z': z, 'n_base': n_base,
            'fecha': fecha_actual, 'umbral': umbral, 'sigma': sigma,
            'mediana': med, 'residuo': r_actual}


def compuerta_dosel(geom, hasta, ventana=VENTANA_BASE_DIAS, escala=ESCALA):
    """Dosel util segun la LINEA BASE, no segun la fecha evaluada.

    La pregunta correcta es «¿este pixel alguna vez fue cultivo?», no «¿lo es hoy?».
    Preguntar lo segundo filtra sobre la variable de respuesta: un pixel que perdio
    dosel es exactamente la anomalia buscada, y la compuerta lo borraba.
    """
    import pandas as pd
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]
    base = _coleccion_limpia(geom, desde, fin)
    # NDVI maximo de la base: si alguna vez fue dosel pleno, cuenta como cultivo.
    ndvi_max = base.select('NDVI').max()
    q = ndvi_max.reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]), geometry=geom,
        scale=escala * 5, maxPixels=1e9, bestEffort=True)
    lo = ee.Number(ee.Algorithms.If(q.get('NDVI_p2'), q.get('NDVI_p2'), 0))
    hi = ee.Number(ee.Algorithms.If(q.get('NDVI_p98'), q.get('NDVI_p98'), 0))
    rango = hi.subtract(lo).max(1e-6)
    fvc = ndvi_max.subtract(lo).divide(rango).clamp(0, 1)
    return fvc.gte(cfg.FVC_MINIMA).rename('dosel')


# --- SEGUNDA CAPA: zonas por debajo de su propio porte ------------------------
#
# Responde una pregunta DISTINTA de la del criterio temporal, y por eso convive con
# el en vez de reemplazarlo:
#
#     temporal (`evaluar`)  ->  "acá CAMBIÓ algo esta semana"        -> ALERTA
#     zonas    (`zonas`)    ->  "esta zona VIENE peor de lo que su   -> ZONA DE
#                                porte indica"                          MANEJO
#
# MEDIDO 2026-07-29 sobre los 4 lotes: **0% de solapamiento entre las dos capas.**
# Marcan lugares completamente distintos. Ninguna sobra.
#
# COMO SE CONSTRUYE, Y POR QUE ASI
# --------------------------------
# Medido sobre imagen limpia (SANTO_ANTONIO-02, 2026-06-22, cobertura 1,000): los
# cinco indices correlacionan ESPACIALMENTE entre 0,97 y 0,998. Son biomasa con
# cinco nombres. Exigir varios sobre la imagen cruda NO es redundancia: es pedir la
# misma condicion tres veces.
#
# La informacion util aparece al SACAR ese factor: se regresa cada indice contra
# NDVI pixel a pixel y se mira el residuo. Ahi los residuos de NDMI, NDRE y CIRE
# correlacionan entre 0,62 y 0,74 — una segunda dimension REAL, chica (7-19% de la
# varianza) pero confirmada por tres indices independientes.
#
# Que significa un residuo negativo: un punto con LA MISMA BIOMASA que sus pares
# pero mas seco o con menos clorofila de la que le corresponde a su porte. No es
# "creció menos" —eso es biomasa— es "está mal para lo que creció".
#
# Y RESUELVE SOLO EL PROBLEMA DE LAS FECHAS DE SIEMBRA. Sembrar 9 dias mas tarde se
# manifiesta sobre todo como MENOS BIOMASA; al sacar el NDVI se saca tambien esa
# parte. No hace falta estimar la fenologia por pixel, que ademas no se puede: con
# ~10 escenas limpias en 80 dias el estimador de emergencia por medio-maximo da el
# mismo dia para casi todo el lote y confunde "sembrado tarde" con "crece poco".
#
# LAS DOS PRUEBAS QUE LO HABILITARON
# ----------------------------------
# 1. NO ES CUOTA. La fraccion marcada varia de 0,00% a 3,28% entre lotes y fechas —
#    SANTO_ANTONIO-01 marca 4x mas que SANTO_ANTONIO-02, en el mismo campo. Una
#    cuota marcaria lo mismo siempre. (La nula espacial es falsa por construccion y
#    esta es la unica defensa honesta: medir que la fraccion se mueva.)
# 2. ES PERSISTENTE. El solapamiento entre fechas consecutivas es de **18x a 73x**
#    lo que daria el azar. Una zona real esta en el mismo lugar la semana siguiente;
#    el ruido se mueve.
#
# LIMITE QUE HAY QUE DECLARAR: la persistencia prueba que es REAL, no que sea un
# PROBLEMA. Una mancha estable puede ser suelo, un bajo, un borde de terraza o una
# compactacion vieja. Por eso esta capa se entrega como ZONA A INVESTIGAR y no como
# alerta: la urgencia la marca la capa temporal.

Z_ZONA = 2.0          # sigmas del residuo, en ambos ejes
MMU_ZONA_HA = 0.30    # una zona de manejo mas chica que esto no se maneja distinto


def zonas(geom, fecha, z=Z_ZONA):
    """Zonas por debajo de su propio porte en la escena `fecha`.

    Devuelve (mascara, {eje: z del residuo}). Ver el bloque de arriba para el
    diseño y la evidencia.
    """
    img = ee.Image(ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                   .filterDate(fecha, ee.Date(fecha).advance(1, 'day'))
                   .filterBounds(geom).sort('CLOUDY_PIXEL_PERCENTAGE').first())
    idx = sr._indices(img).updateMask(sr._mascara(img))
    zs = {}
    for e in cfg.EJES:
        # Recta espacial del indice contra NDVI: es el "porte esperado" de cada
        # punto. El residuo es lo que le sobra o le falta respecto de su biomasa.
        fit = idx.select(['NDVI', e]).reduceRegion(
            reducer=ee.Reducer.linearFit(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True)
        esperado = (idx.select('NDVI').multiply(ee.Number(fit.get('scale')))
                    .add(ee.Number(fit.get('offset'))))
        r = idx.select(e).subtract(esperado)
        s = ee.Number(r.reduceRegion(
            reducer=ee.Reducer.stdDev(), geometry=geom, scale=ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0))
        zs[e] = r.divide(s.max(1e-6)).rename('zr_' + e)
    from .ranking import SIGNO
    m = None
    for e in cfg.EJES:
        # Mismo sentido de deterioro que declara SIGNO, aplicado al RESIDUO.
        cond = zs[e].multiply(SIGNO[e]).gte(z)
        m = cond if m is None else m.And(cond)
    return m.rename('zona'), zs


# --- puente hacia focos.py ----------------------------------------------------

def para_focos(geom, hasta, alfa=ALFA):
    """Lo que `focos.detectar_lote` necesita, calculado con el criterio v2.

    Devuelve exactamente la misma interfaz que ya consumia el vectorizador, para
    que TODO lo de aguas abajo —unidad minima de mapeo, filtro de moda, severidad,
    GeoJSON, informe— siga igual y el cambio quede acotado al criterio:

        zs        {eje: imagen de z}   (temporal por pixel, no espacial)
        foco      mascara booleana de anomalia
        evaluada  mascara de pixel con dato (para el area util)
        ref       imagen de la que sacar la proyeccion
        fecha_img fecha de la escena evaluada
        n_base    escenas de la linea base (para declararlo en el informe)
        base_desde / base_hasta

    `fecha_ref` deja de ser UNA fecha: la referencia es la trayectoria del propio
    pixel sobre `n_base` observaciones. El informe tiene que decirlo asi, no
    inventar una fecha de referencia que ya no existe.
    """
    import pandas as pd
    r = evaluar(geom, hasta, alfa=alfa)
    dosel = compuerta_dosel(geom, hasta)
    ejes = list(cfg.EJES)
    zs = {e: r['z'][e].updateMask(dosel).rename('z_' + e) for e in ejes}
    foco = r['anomalia'].And(dosel).rename('foco')
    evaluada = zs[ejes[0]].mask().rename('u')
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=VENTANA_BASE_DIAS))[:10]
    return {'zs': zs, 'foco': foco, 'evaluada': evaluada,
            'ref': zs[ejes[0]], 'fecha_img': r['fecha'],
            'n_base': r['n_base'], 'base_desde': desde,
            'base_hasta': str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10],
            'd2': r['d2'], 'umbral': r['umbral']}
