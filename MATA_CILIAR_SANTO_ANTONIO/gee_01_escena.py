# -*- coding: utf-8 -*-
"""Paso 1: listar escenas S2 L2A de los ultimos 120 dias sobre el AOI y elegir una.

    python gee_01_escena.py [--dias 120] [--hasta 2026-09-06]

COMO SE MIDE CADA ESCENA
------------------------
- HUELLA (cobertura geometrica): fraccion del AOI que el granulo realmente
  cubre. Se mide con la mascara de B4 rellenada con `unmask(0, False)`: con el
  default (sameFootprint=True) los pixeles fuera del granulo salen del
  denominador y un granulo que toca el AOI de refilon reporta 100%.
- % CLARO: fraccion de pixeles con cs_cdf >= 0.60 (Cloud Score+), calculada
  SOLO sobre la huella real (cs_cdf esta enmascarado fuera del granulo, y ahi
  NO se rellena: fuera de la huella no hay nada que evaluar).
- cs medio: media de cs_cdf sobre la huella.

Huella y claro son dos cosas distintas y se reportan por separado. Se elige
por huella primero (regla de la casa: un granulo puede cubrir solo parte).

REGLA DE ELECCION
-----------------
La mas reciente con huella >= 99.5% del AOI y claro >= 97%. Si ninguna, la
mas reciente con claro >= 95% e informar. Si tampoco, falla ruidoso: no se
elige una escena nublada en silencio.
(99.5% y no 100.0 porque el borde del granulo cae entre pixeles; 0.5% del AOI
son ~11 ha en el margen de 1500 m, nunca sobre la propiedad — se verifica
aparte que la huella sobre la PROPIEDAD sea 100%.)

"Sentinel-2A" en el pedido del usuario significa NIVEL L2A (reflectancia de
superficie), no el satelite A. Cualquier plataforma sirve; se registra cual.
"""
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import (HOY, SALIDA, cargar_propiedad, describir_aoi, ee_bbox, ee_geom,
                   guardar_json, inicializar_ee, log, safe_getInfo)

COLECCION_S2 = 'COPERNICUS/S2_SR_HARMONIZED'
COLECCION_CS = 'GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED'
UMBRAL_CS = 0.60          # cs_cdf >= 0.60: valor recomendado por el propio dataset
HUELLA_MINIMA = 0.995
CLARO_OBJETIVO = 0.97
CLARO_RESPALDO = 0.95
ESCALA_MEDICION = 10      # cs_cdf es nativo 10 m; el AOI son 22 km2, 224k px


def medir_escenas(ee, aoi, propiedad, desde, hasta):
    s2 = (ee.ImageCollection(COLECCION_S2)
          .filterBounds(aoi).filterDate(desde, hasta))
    cs = (ee.ImageCollection(COLECCION_CS)
          .filterBounds(aoi).filterDate(desde, hasta))
    # Cloud Score+ se une por system:index (mismo indice que la escena S2).
    s2 = s2.linkCollection(cs, ['cs_cdf'])

    def medir(img):
        huella = img.select('B4').mask().unmask(0, False).rename('huella')
        claro = img.select('cs_cdf').gte(UMBRAL_CS).rename('claro')
        cs_med = img.select('cs_cdf').rename('cs_medio')
        r_aoi = huella.addBands(claro).addBands(cs_med).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=aoi, scale=ESCALA_MEDICION,
            maxPixels=1e8)
        r_prop = huella.addBands(claro).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=propiedad, scale=ESCALA_MEDICION,
            maxPixels=1e8)
        return ee.Feature(None, {
            'id': img.get('system:index'),
            'fecha': ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'),
            'hora': ee.Date(img.get('system:time_start')).format('HH:mm'),
            'granulo': img.get('MGRS_TILE'),
            'satelite': img.get('SPACECRAFT_NAME'),
            'baseline': img.get('PROCESSING_BASELINE'),
            'huella_aoi': r_aoi.get('huella'),
            'claro_aoi': r_aoi.get('claro'),
            'cs_medio_aoi': r_aoi.get('cs_medio'),
            'huella_prop': r_prop.get('huella'),
            'claro_prop': r_prop.get('claro'),
        })

    fc = ee.FeatureCollection(s2.map(medir))
    info = safe_getInfo(fc, timeout=600, descripcion='medicion de escenas')
    filas = [f['properties'] for f in info['features']]
    filas.sort(key=lambda r: (r['fecha'], r['granulo']))
    return filas


def elegir(filas):
    """Devuelve (fila, criterio). Falla si no hay nada usable."""
    utiles = [r for r in filas if r['huella_aoi'] is not None and r['claro_aoi'] is not None]
    plenas = [r for r in utiles if r['huella_aoi'] >= HUELLA_MINIMA]
    a = [r for r in plenas if r['claro_aoi'] >= CLARO_OBJETIVO]
    if a:
        return max(a, key=lambda r: r['fecha']), 'huella>=%.1f%% y claro>=%d%%' % (
            HUELLA_MINIMA * 100, CLARO_OBJETIVO * 100)
    b = [r for r in plenas if r['claro_aoi'] >= CLARO_RESPALDO]
    if b:
        return max(b, key=lambda r: r['fecha']), 'RESPALDO: huella>=%.1f%% y claro>=%d%% (ninguna llego a %d%%)' % (
            HUELLA_MINIMA * 100, CLARO_RESPALDO * 100, CLARO_OBJETIVO * 100)
    return None, 'ninguna escena con huella completa y claro >= %d%%' % (CLARO_RESPALDO * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dias', type=int, default=120)
    ap.add_argument('--hasta', default=HOY)
    args = ap.parse_args()

    hasta = dt.date.fromisoformat(args.hasta)
    desde = hasta - dt.timedelta(days=args.dias)
    hasta_excl = hasta + dt.timedelta(days=1)   # filterDate excluye el limite superior
    log('=== gee_01_escena: S2 L2A %s .. %s (%d dias) ===' % (desde, hasta, args.dias))

    p = cargar_propiedad()
    describir_aoi(p)
    ee = inicializar_ee()
    aoi = ee_bbox(p['aoi_31982'])
    propiedad = ee_geom(p['geom'])

    filas = medir_escenas(ee, aoi, propiedad, str(desde), str(hasta_excl))
    if not filas:
        raise SystemExit('NO EVALUABLE: ninguna escena %s intersecta el AOI en la ventana' % COLECCION_S2)

    log('')
    log('%-10s %-6s %-36s %-7s %-4s %7s %7s %7s %7s %7s' % (
        'fecha', 'hora', 'id', 'granulo', 'sat', 'huella%', 'claro%', 'cs_med', 'hue_pr%', 'cla_pr%'))
    for r in filas:
        sat = (r['satelite'] or '?').replace('Sentinel-2', '')
        def pct(v):
            return '%7.1f' % (v * 100) if v is not None else '      -'
        def num(v):
            return '%7.3f' % v if v is not None else '      -'
        log('%-10s %-6s %-36s %-7s %-4s %s %s %s %s %s' % (
            r['fecha'], r['hora'], r['id'], r['granulo'], sat,
            pct(r['huella_aoi']), pct(r['claro_aoi']), num(r['cs_medio_aoi']),
            pct(r['huella_prop']), pct(r['claro_prop'])))
    log('%d escenas medidas' % len(filas))
    sin_cs = sorted({r['fecha'] for r in filas if r['claro_aoi'] is None})
    if sin_cs:
        # Cloud Score+ llega con dias de retraso: la escena mas nueva puede no
        # tener cs_cdf todavia. Se dice, no se deja como un guion.
        log('SIN Cloud Score+ todavia (no evaluables hoy, latencia del dataset): %s' % ', '.join(sin_cs))

    elegida, criterio = elegir(filas)
    if elegida is None:
        raise SystemExit('NO EVALUABLE: %s. No se elige una escena nublada en silencio.' % criterio)

    log('')
    log('ELEGIDA: %s  %s  %s  %s  huella %.1f%%  claro %.1f%%  cs %.3f  (%s)' % (
        elegida['fecha'], elegida['id'], elegida['granulo'], elegida['satelite'],
        elegida['huella_aoi'] * 100, elegida['claro_aoi'] * 100, elegida['cs_medio_aoi'], criterio))
    if elegida['huella_prop'] < 0.999:
        raise SystemExit('La escena elegida NO cubre toda la propiedad (%.1f%%): revisar'
                         % (elegida['huella_prop'] * 100))
    if criterio.startswith('RESPALDO'):
        log('AVISO: se uso el criterio de respaldo (%d%%); la escena tiene %.1f%% claro.'
            % (CLARO_RESPALDO * 100, elegida['claro_aoi'] * 100))

    os.makedirs(SALIDA, exist_ok=True)
    salida = {
        'coleccion': COLECCION_S2,
        'id_completo': '%s/%s' % (COLECCION_S2, elegida['id']),
        'id': elegida['id'],
        'fecha': elegida['fecha'],
        'hora_utc': elegida['hora'],
        'granulo': elegida['granulo'],
        'satelite': elegida['satelite'],
        'processing_baseline': elegida['baseline'],
        'huella_aoi': elegida['huella_aoi'],
        'claro_aoi': elegida['claro_aoi'],
        'cs_medio_aoi': elegida['cs_medio_aoi'],
        'huella_propiedad': elegida['huella_prop'],
        'claro_propiedad': elegida['claro_prop'],
        'criterio': criterio,
        'umbral_cs_cdf': UMBRAL_CS,
        'ventana': {'desde': str(desde), 'hasta': str(hasta), 'dias': args.dias},
        'nota': 'L2A = nivel de procesamiento (SR); el satelite puede ser A, B o C',
        'fechas_sin_cloud_score_plus': sin_cs,
        'todas': filas,
    }
    guardar_json(os.path.join(SALIDA, 'escena_elegida.json'), salida)


if __name__ == '__main__':
    main()
