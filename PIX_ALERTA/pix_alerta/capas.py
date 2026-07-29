# -*- coding: utf-8 -*-
"""Las DOS capas que no son alerta: zonas estructurales y estratos de siembra.

POR QUE EN UN ARCHIVO APARTE, Y NO JUNTO CON LOS FOCOS
------------------------------------------------------
PIX Scout trata como FOCO **todo lo que no este marcado como perimetro**
(`app/js/geojson.js`, `isPerimeter`): lo mete en la lista, le da una severidad y le
asigna un numero de recorrida `n/N`. O sea que meter una zona estructural en el
geojson de focos la convierte en una parada del recorrido del tecnico, con severidad
inventada — exactamente lo contrario de lo que la zona significa.

Y la lista de `isPerimeter` esta CABLEADA en la app ya firmada (v1.0.11): no alcanza
con inventar `tipo: 'zona'`, porque esa APK no lo conoce y la trataria como foco
igual. Un cambio de contrato con una app ya instalada en el campo se hace al reves:
primero la app aprende a ignorar lo que no entiende, despues el motor se lo manda.

Mientras tanto estas capas salen en su propio archivo y en el informe, que es donde
las lee el agronomo. **Es una decision de contrato, no una limitacion tecnica.**

LAS DOS CAPAS RESPONDEN PREGUNTAS DISTINTAS, Y NINGUNA ES "ALERTA"
-------------------------------------------------------------------
    capa       pregunta                                     accion
    -------    ------------------------------------------   ---------------------
    FOCO       aca CAMBIO algo esta semana                   ir a mirar YA
    ZONA       esta parte VIENE peor de lo que su porte      investigar la causa
               indica, y sigue ahi semana tras semana        (suelo, bajo, compactacion)
    ESTRATO    este BLOQUE se implanto mas tarde de lo que   revisar la siembra
               su fecha de siembra explica                   de ese bloque

El foco es la unica que exige recorrida inmediata. Las otras dos se entregan con otro
lenguaje a proposito: "zona a investigar" y "bloque atrasado", nunca "alerta".

LIMITES DECLARADOS
------------------
· La persistencia de una zona prueba que es REAL, no que sea un PROBLEMA. Una mancha
  estable puede ser suelo, un bajo o una compactacion vieja que el productor ya
  conoce. Por eso no dispara aviso.
· Los estratos solo se pueden delimitar ANTES del cierre del dosel. Pasada esa
  ventana el analisis no se rehace: se conserva el de la escena en que se separaron.
· El contraste medido-vs-declarado depende de que el cliente haya declarado bien las
  fechas. Cuando no las declara, no hay contraste: se informa el atraso medido y se
  dice que no hay con que compararlo, en vez de suponer cero.
"""
import ee

from . import config as cfg
from . import criterio as cri

ESCALA = cri.ESCALA

# DIFERENCIA QUE MERECE MIRARSE, en dias entre el atraso medido y el declarado.
#
# NO es un umbral fino: es el orden de la CADENCIA de observacion. Con revisita util
# de ~10 dias (48% de dekadas con escena util medido en Santa Cruz), el dia en que un
# bloque alcanza un NDVI se conoce con una incertidumbre de ese orden. Una diferencia
# menor que la cadencia no se puede distinguir del muestreo temporal.
#
# MEDIDO en Santo Antonio-02: los bloques dieron diferencias de 0 / 9,0 / 27,9 dias
# contra lo declarado. El de 27,9 es el que el cliente confirmo (siembra corrida por
# lluvias, no resiembra); el de 9,0 esta justo en el borde y por eso no se afirma.
DIF_ATENCION_DIAS = 10.0

# ASTILLAS DE BORDE DE LOS ESTRATOS. Un bloque de siembra es UNA pasada de la
# sembradora: ocupa una fraccion grande del lote y es contiguo. El corte por
# percentiles de NDVI, en cambio, produce ademas decenas de manchitas en los bordes
# entre bloques, donde el dosel de dos pasadas se mezcla dentro del mismo pixel.
#
# MEDIDO en SANTO_ANTONIO-02: la clasificacion cruda dio **20 poligonos** para 3
# bloques — tres de 39,4 / 21,5 / 36,5 ha y diecisiete de entre 0,00 y 4,3 ha. Un
# mapa con veinte piezas no se lee, y ademas sugiere veinte siembras que no hubo.
#
# Se descarta cada PARTE por debajo del 0,5% del lote, con piso en la unidad minima
# de mapeo de los focos: por debajo de eso no es una pasada de sembradora, es el
# borde entre dos. Los bloques se entregan DISUELTOS: un rasgo por bloque.
FRACCION_PARTE_ESTRATO = 0.005


def _vectorizar(mascara, geom, escala, mmu_ha, extra=None, etiqueta='zona'):
    """Mascara -> poligonos por encima de la unidad minima, con sus atributos.

    Mismo camino que usa `focos.detectar_lote`: filtro de moda para sacar sal y
    pimienta, reproyeccion a la grilla declarada y corte por area. Sin el filtro de
    moda un pixel suelto se convierte en un poligono de 0,04 ha que el tecnico no
    puede encontrar en el campo.
    """
    proj = mascara.projection().atScale(escala)
    # Sobre una mascara binaria esto saca sal y pimienta; sobre una imagen de CLASE
    # es un filtro de mayoria, que es lo que corresponde. `toInt` porque
    # `reduceToVectors` exige banda de etiqueta entera.
    limpio = (mascara.focalMode(1.5, 'square', 'pixels')
              .reproject(proj).selfMask().toInt().rename(etiqueta))
    apilado = limpio
    for k, img in (extra or {}).items():
        apilado = apilado.addBands(img.rename(k))
    # `reduceToVectors` gasta la PRIMERA banda como etiqueta y le exige al reductor
    # al menos una banda de valor: con una sola banda tira
    # `Need 1+1 bands for Reducer.mean`. Cuando no hay atributos que promediar se
    # agrega el area del pixel, que ademas sirve de control: su suma por poligono
    # tiene que dar el area del poligono.
    if not extra:
        apilado = apilado.addBands(ee.Image.pixelArea().rename('m2'))
    vec = apilado.reduceToVectors(
        reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
        geometryType='polygon', eightConnected=True, labelProperty=etiqueta,
        maxPixels=1e9, bestEffort=True)
    vec = (vec.map(lambda f: f.set('area_ha', f.geometry().area(1).divide(1e4)))
              .filter(ee.Filter.gte('area_ha', mmu_ha)))
    return vec.getInfo()


# --- capa 2: zonas por debajo de su propio porte ------------------------------
#
# ⚠️ MEDIDO 2026-07-29, Y HAY QUE DECIRLO: EN ESTE CAMPO LA CAPA NO ENTREGA.
#
# Barrido de los 4 lotes de trigo x 5 fechas limpias, **con la unidad minima puesta
# en cero** para no confundir "no hay zonas" con "el umbral las corta":
#
#     combinaciones lote-fecha con al menos una zona:   4 de 20
#     zona MAS GRANDE encontrada en todo el barrido:    0,16 ha
#     resto:                                            0,08 a 0,12 ha
#
# 0,16 ha a 20 m son cuatro pixeles. **No es una zona de manejo: es un grumo.** No se
# puede mandar a nadie a caminarlo, no se puede manejar distinto, y llamarlo "zona"
# en un informe seria inventar una entidad que no existe en el campo.
#
# LA TENTACION ERA BAJAR `MMU_ZONA_HA` HASTA QUE SALIERA ALGO, y es exactamente el
# error que este motor viene corrigiendo desde el principio: elegir el umbral por la
# salida que produce y no por lo que significa. El umbral se queda donde estaba —una
# zona mas chica que eso no se maneja distinto— y la capa queda **muda en este
# cliente**, que es el resultado honesto.
#
# QUE SIGNIFICA, ENTONCES: en estos lotes, una vez descontado el porte, no hay
# ninguna parte que venga sistematicamente peor que sus pares. Es informacion buena
# para el productor, no un fracaso del metodo. Y la capa sigue conectada porque en un
# lote con un bajo, un cambio de suelo o una compactacion real SI tiene que salir —
# eso se vera en el proximo cliente, no se puede afirmar con estos cuatro lotes.
#
# El barrido se rehace con `medicion/barrer_zonas.py`.

def zonas_lote(sitio, feat, fecha, z=None, mmu_ha=None):
    """Zonas estructurales de un lote en la escena `fecha`.

    Devuelve un dict SIEMPRE, tambien cuando no hay zonas o cuando fallo: un
    `None` mudo no se distingue de "no hay nada", que es el modo de falla que mas
    tranquiliza y el que este motor tiene prohibido.
    """
    from . import focos as fo
    lote_id = str(feat['properties'].get(sitio.campo_id))
    z = cri.Z_ZONA if z is None else z
    mmu_ha = cri.MMU_ZONA_HA if mmu_ha is None else mmu_ha
    base = {'lote_id': lote_id, 'zonas': [], 'area_zonas_ha': 0.0,
            'fecha': str(fecha)[:10], 'error': None, 'nota': None}
    try:
        geom = fo._geom_lote(sitio, feat)
        m, zs = cri.zonas(geom, str(fecha)[:10], z=z)
        extra = {'zr_' + e.lower(): zs[e] for e in cfg.EJES}
        fc = _vectorizar(m, geom, ESCALA, mmu_ha, extra=extra, etiqueta='zona')
    except cri.SinEscena as e:
        # No es averia y no es "no hay zonas": es que ese dia no se pudo mirar. Los
        # tres casos tienen que quedar distinguibles o el resumen miente.
        base['sin_escena'] = True
        base['nota'] = str(e)
        return base
    except Exception as e:                        # noqa: BLE001 — se declara y sigue
        # Una capa secundaria NO puede voltear la corrida nocturna. Se registra la
        # averia con nombre y tipo para que sea auditable, y el producto principal
        # (los focos) se entrega igual.
        base['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
        base['nota'] = 'no se pudieron calcular las zonas de este lote'
        return base

    area_lote = float(feat['properties'].get(sitio.campo_area, 0) or 0)
    salida, total = [], 0.0
    # Peor primero. El residuo se ordena por el eje 0 igual que los focos, pero
    # aca NO se traduce a severidad: una zona no tiene severidad, tiene tamaño.
    k0 = 'zr_' + cfg.EJES[0].lower()
    orden = sorted(fc.get('features', []),
                   key=lambda x: -abs(float(x['properties'].get(k0) or 0)))
    for i, f in enumerate(orden):
        p = f['properties']
        a = round(float(p.get('area_ha', 0)), 3)
        total += a
        props = {
            'tipo': 'zona',
            'id': '%s-Z%d' % (lote_id, i + 1),
            'etiqueta': 'Z%d' % (i + 1),
            'lote_id': lote_id, 'orden': i + 1, 'area_ha': a,
            'pct_lote': round(100 * a / area_lote, 2) if area_lote else None,
            'fecha': str(fecha)[:10],
            'ejes': '+'.join(cfg.EJES),
            # LENGUAJE DISTINTO DEL FOCO, a proposito. Esto viaja al informe y al
            # tablero: si dice "alerta" en algun lado, ya se perdio la distincion.
            'clase': 'zona a investigar',
            'accion': 'investigar la causa; no exige recorrida inmediata',
        }
        for e in cfg.EJES:
            k = 'zr_' + e.lower()
            v = p.get(k)
            props[k] = round(float(v), 2) if v is not None else None
            # Cuanto le FALTA a esa zona respecto de lo que su biomasa indica, en
            # el sentido de deterioro que declara SIGNO.
        props['deficit_z'] = round(
            abs(float(p.get(k0) or 0)), 2)
        salida.append({'type': 'Feature', 'geometry': f['geometry'],
                       'properties': props})
    base.update({'zonas': salida, 'area_zonas_ha': round(total, 3),
                 'pct_lote': round(100 * total / area_lote, 2) if area_lote else None,
                 'area_lote_ha': round(area_lote, 3) if area_lote else None})
    if not salida:
        base['nota'] = ('no hay zonas por encima de %.2f ha que esten por debajo de '
                        'su porte' % mmu_ha)
    return base


# --- capa 3: estratos de siembra ----------------------------------------------

def estratos_lote(sitio, feat, hasta):
    """Bloques de siembra de un lote, con el atraso medido contra el declarado.

    Devuelve dict siempre. `sin_estratos` en True significa que el lote se sembro
    de una sola vez —que es el resultado correcto en 3 de cada 4 lotes medidos— y
    NO que el analisis fallara.
    """
    from . import estratos as es
    from . import focos as fo
    lote_id = str(feat['properties'].get(sitio.campo_id))
    base = {'lote_id': lote_id, 'estratos': [], 'contraste': {},
            'sin_estratos': True, 'error': None, 'nota': None}
    if len(list(getattr(sitio, 'siembras', ()) or [])) < 2:
        base['nota'] = 'el cliente no declaro mas de una fecha de siembra'
        return base
    try:
        geom = fo._geom_lote(sitio, feat)
        d = es.analizar(sitio, feat, hasta, geom=geom)
    except Exception as e:                        # noqa: BLE001
        base['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
        return base
    if not d:
        base['nota'] = 'no se encontro escena util para separar los bloques'
        return base
    if d.get('averia'):
        # El analisis se rompio. NO puede salir como 'sin estratos', que es el
        # resultado tranquilizador. `sin_estratos` queda en None: ni si ni no.
        base['error'] = d.get('error')
        base['sin_estratos'] = None
        base['nota'] = 'el analisis de bloques fallo en este lote; no se sabe'
        return base
    base.update({k: v for k, v in d.items()
                 if k not in ('estrato',) and not hasattr(v, 'getInfo')})
    if d.get('sin_estratos') or d.get('estrato') is None:
        base['sin_estratos'] = True
        base['nota'] = d.get('motivo') or 'el lote parece de una sola siembra'
        return base

    base['sin_estratos'] = False
    n = int(d.get('n') or 0)
    contraste = d.get('contraste') or {}
    try:
        # Cada estrato como poligono, para que el mapa del informe muestre DONDE
        # esta el bloque atrasado y no solo cuantos dias tiene de atraso.
        #
        # SE VECTORIZA LA CLASIFICACION, NO UNA MASCARA. Pasar `estrato.gt(0)` seria
        # una mascara uniforme: `reduceToVectors` la ve como UNA sola region y
        # devuelve un poligono con el PROMEDIO de las clases (2,0 con tres estratos),
        # o sea el lote entero rotulado como un bloque inexistente. Con la imagen de
        # clase como banda de etiqueta, agrupa por valor y sale un poligono por
        # bloque, que es lo que el mapa necesita.
        fc = _vectorizar(d['estrato'].toInt(), geom, ESCALA, 0.0, etiqueta='k',
                         extra={'clase': d['estrato']})
    except Exception as e:                        # noqa: BLE001
        base['error'] = '%s: %s' % (type(e).__name__, str(e)[:120])
        return base

    # UN RASGO POR BLOQUE, no uno por mancha. Las partes se juntan en un
    # MultiPolygon y las astillas de borde se descartan (ver FRACCION_PARTE_ESTRATO).
    area_lote = float(feat['properties'].get(sitio.campo_area, 0) or 0)
    from .focos import MMU_HA
    minima = max(area_lote * FRACCION_PARTE_ESTRATO,
                 cfg.valor_de(sitio, 'mmu_ha', MMU_HA))
    partes, areas, descartadas = {}, {}, 0
    for f in fc.get('features', []):
        p = f['properties']
        # `k` es la ETIQUETA (el valor de clase con que agrupo reduceToVectors);
        # `clase` es su media dentro del poligono, que por construccion es la misma.
        k = int(round(float(p.get('k') if p.get('k') is not None
                            else p.get('clase') or 0)))
        if k < 1:
            continue
        a = float(p.get('area_ha', 0) or 0)
        if a < minima:
            descartadas += 1
            continue
        g = f['geometry']
        trozos = ([g['coordinates']] if g['type'] == 'Polygon'
                  else list(g['coordinates']))
        partes.setdefault(k, []).extend(trozos)
        areas[k] = areas.get(k, 0.0) + a
    if descartadas:
        base['nota'] = ('se descartaron %d mancha(s) de borde por debajo de %.2f ha: '
                        'son la transicion entre pasadas, no una siembra'
                        % (descartadas, minima))
    for k in sorted(partes):
        c = contraste.get(k) or contraste.get(str(k)) or {}
        base['estratos'].append({
            'type': 'Feature',
            'geometry': {'type': 'MultiPolygon', 'coordinates': partes[k]},
            'properties': {
                'tipo': 'estrato',
                'id': '%s-B%d' % (lote_id, k),
                'etiqueta': 'B%d' % k,
                'lote_id': lote_id, 'estrato': k,
                'area_ha': round(areas[k], 3),
                'partes': len(partes[k]),
                # El estrato n es el mas ADELANTADO (primera siembra declarada) y
                # el 1 el mas atrasado. La convencion la fija `estratos.segmentar`.
                'atraso_medido_dias': c.get('medido'),
                'atraso_declarado_dias': c.get('declarado'),
                'diferencia_dias': c.get('diferencia'),
                'clase': 'bloque de siembra',
                'accion': ('revisar la implantacion de este bloque'
                           if (c.get('diferencia') or 0) >= DIF_ATENCION_DIAS
                           else 'sin diferencia relevante con lo declarado'),
            }})
    base['contraste'] = contraste
    return base



# --- salida ------------------------------------------------------------------

def a_geojson(sitio, zonas_por_lote=None, estratos_por_lote=None, perimetro=None):
    """FeatureCollection de las capas de CONTEXTO. No es el archivo de la app.

    Se marca con `capa: 'contexto'` en cada feature y con `tipo` propio, para que
    cualquier consumidor futuro pueda separarlas sin adivinar. El nombre del archivo
    tambien las separa (`contexto_*.geojson`, no `focos_*.geojson`).
    """
    feats = []
    if perimetro is not None:
        feats.append({'type': 'Feature', 'geometry': perimetro,
                      'properties': {'tipo': 'perimetro',
                                     'id': '%s-PERIMETRO' % sitio.clave,
                                     'hacienda': sitio.titulo}})
    for lid, r in sorted((zonas_por_lote or {}).items()):
        for f in r.get('zonas', []):
            p = dict(f['properties'])
            p.update({'capa': 'contexto', 'hacienda': sitio.titulo,
                      'cultivo': getattr(sitio, 'cultivo', '') or None,
                      'name': '%s / %s' % (lid, p.get('etiqueta'))})
            feats.append({'type': 'Feature', 'geometry': f['geometry'],
                          'properties': p})
    for lid, r in sorted((estratos_por_lote or {}).items()):
        for f in r.get('estratos', []):
            p = dict(f['properties'])
            p.update({'capa': 'contexto', 'hacienda': sitio.titulo,
                      'cultivo': getattr(sitio, 'cultivo', '') or None,
                      'name': '%s / %s' % (lid, p.get('etiqueta'))})
            feats.append({'type': 'Feature', 'geometry': f['geometry'],
                          'properties': p})
    return {'type': 'FeatureCollection', 'features': feats}


def resumen(zonas_por_lote=None, estratos_por_lote=None):
    """Numeros para el informe y el log, sin volver a tocar GEE."""
    z = zonas_por_lote or {}
    e = estratos_por_lote or {}
    n_z = sum(len(r.get('zonas', [])) for r in z.values())
    ha_z = sum(float(r.get('area_zonas_ha') or 0) for r in z.values())
    # `is False` A PROPOSITO, no `not ...`: `sin_estratos` tiene TRES estados —
    # True (una sola siembra), False (hay bloques) y None (el analisis se rompio).
    # Con `not` el lote averiado entraba en la cuenta de lotes CON estratos.
    con_est = [r for r in e.values() if r.get('sin_estratos') is False]
    averiados = [r for r in e.values() if r.get('sin_estratos') is None]
    atencion = []
    for r in con_est:
        for k, c in sorted((r.get('contraste') or {}).items()):
            d = c.get('diferencia')
            if d is not None and d >= DIF_ATENCION_DIAS:
                atencion.append({'lote_id': r['lote_id'], 'estrato': k,
                                 'diferencia_dias': d,
                                 'medido': c.get('medido'),
                                 'declarado': c.get('declarado')})
    return {'n_zonas': n_z, 'area_zonas_ha': round(ha_z, 2),
            'lotes_con_estratos': len(con_est),
            # Se cuenta y se informa: un lote donde el analisis fallo no es un lote
            # sin bloques, y quien lea el resumen tiene que poder verlo.
            'lotes_con_averia': len(averiados),
            'bloques_en_atencion': atencion}
