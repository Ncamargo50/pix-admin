# -*- coding: utf-8 -*-
"""Paso 2: bajar la escena elegida (escena_elegida.json) recortada al AOI a 10 m.

    python gee_02_descarga_s2.py [--offset]

SALIDAS (en 01_DATOS_SATELITE, todas EPSG:31982, grid alineado a 10 m)
- S2_<fecha>_AOI_10m.tif      float32, 12 bandas: B2 B3 B4 B8 (10 m nativo),
                              B5 B6 B7 B8A B11 B12 (20 m -> 10 m bilineal),
                              SCL (vecino mas cercano), cs_cdf (Cloud Score+).
                              Reflectancia = DN / 10000. nodata -9999.
- S2_<fecha>_SCL_10m.tif      uint8, la SCL sola (comodidad para enmascarar).
- S2_<fecha>_RGB.tif          uint8 x3, B4/B3/B2 estirado p2-p98 sobre el AOI.
- S2_<fecha>_INDICES_10m.tif  float32: NDVI NDWI MNDWI NDMI AWEInsh NDRE.
- S2_<fecha>_estadisticas.json  n/min/max/media por banda, AOI y propiedad.

ESCALA FISICA Y EL OFFSET
-------------------------
COPERNICUS/S2_SR_HARMONIZED ya resto el BOA_ADD_OFFSET (1000) a las escenas con
baseline >= 04.00; reflectancia = DN/10000 y nada mas. Restar 1000 a mano es
doble correccion. `--offset` existe solo para forzarlo a proposito y queda
registrado en el JSON. Se verifica con el dato: si la MEDIANA de B2 sobre el
AOI cae por debajo de 0 la escena fue corregida dos veces; unos pocos pixeles
en -0.0999 NO son eso, son el recorte de Sen2Cor (DN minimo 1 - 1000).

FORMULAS (verificadas contra la fuente primaria, ver tabla de la casa)
- NDVI    = (B8 - B4) / (B8 + B4)
- NDWI    = (B3 - B8) / (B3 + B8)         McFeeters 1996: cuerpos de agua (verde-NIR)
- MNDWI   = (B3 - B11) / (B3 + B11)       Xu 2006
- NDMI    = (B8A - B11) / (B8A + B11)     Hardisky 1983 / Wilson & Sader 2002.
            B8A y NO B8: B8A tiene FWHM 20 nm y es nativo de 20 m como B11;
            B8 (118 nm) incluye el borde de absorcion de vapor de agua.
- AWEInsh = 4*(B3 - B11) - (0.25*B8 + 2.75*B12)   Feyisa et al. 2014
- NDRE    = (B8A - B5) / (B8A + B5)       no hay forma canonica; se elige B8A
            por coherencia con NDMI (ambas bandas nativas de 20 m).
Todo denominador de diferencia normalizada lleva max(den, 0.001): sobre agua
y sombra B8+B4 tiende a 0 y el NaN se propaga callado.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import (NODATA_FLOAT, SALIDA, cargar_propiedad, descargar_geotiff, describir_aoi,
                   escribir_geotiff, guardar_json, inicializar_ee, leer_json, log,
                   mascara_propiedad, safe_getInfo, verificar_raster)

COLECCION_CS = 'GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED'
BANDAS_10 = ['B2', 'B3', 'B4', 'B8']
BANDAS_20 = ['B5', 'B6', 'B7', 'B8A', 'B11', 'B12']
BANDAS_REFL = BANDAS_10 + BANDAS_20
BANDAS_TODAS = BANDAS_REFL + ['SCL', 'cs_cdf']
INDICES = ['NDVI', 'NDWI', 'MNDWI', 'NDMI', 'AWEInsh', 'NDRE']
GUARDA_DEN = 0.001


def nd(a, b):
    """Diferencia normalizada con guarda en el denominador."""
    return (a - b) / np.maximum(a + b, GUARDA_DEN)


def calcular_indices(r):
    """r: dict banda -> float64 2D (reflectancia). Devuelve dict indice -> 2D."""
    return {
        'NDVI': nd(r['B8'], r['B4']),
        'NDWI': nd(r['B3'], r['B8']),
        'MNDWI': nd(r['B3'], r['B11']),
        'NDMI': nd(r['B8A'], r['B11']),
        'AWEInsh': 4.0 * (r['B3'] - r['B11']) - (0.25 * r['B8'] + 2.75 * r['B12']),
        'NDRE': nd(r['B8A'], r['B5']),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--offset', action='store_true',
                    help='restar 0.1 (1000 DN) ademas de dividir por 10000. NO va por defecto.')
    args = ap.parse_args()

    esc = leer_json(os.path.join(SALIDA, 'escena_elegida.json'))
    fecha = esc['fecha']
    log('=== gee_02_descarga_s2: %s (%s, %s, baseline %s) ==='
        % (esc['id'], fecha, esc['satelite'], esc['processing_baseline']))

    p = cargar_propiedad()
    describir_aoi(p)
    ee = inicializar_ee()

    img = ee.Image(esc['id_completo'])
    props = safe_getInfo(img.propertyNames(), descripcion='propiedades de la escena')
    offsets = [k for k in props if 'ADD_OFFSET' in k]
    log('Propiedades BOA_ADD_OFFSET presentes en la escena: %s' % (offsets or 'ninguna'))
    log('Escala: reflectancia = DN/10000%s' % (' - 0.1 (FORZADO con --offset)' if args.offset else ''))

    cs = ee.Image(ee.ImageCollection(COLECCION_CS)
                  .filter(ee.Filter.eq('system:index', esc['id'])).first())
    n_cs = safe_getInfo(cs.bandNames().size(), descripcion='cs_cdf')
    if not n_cs:
        raise SystemExit('La escena no tiene Cloud Score+ asociado: no se puede bajar cs_cdf')

    refl = img.select(BANDAS_10).addBands(img.select(BANDAS_20).resample('bilinear'))
    refl = refl.divide(10000)
    if args.offset:
        refl = refl.subtract(0.1)
    compuesta = (refl.addBands(img.select('SCL'))
                 .addBands(cs.select('cs_cdf')))

    os.makedirs(SALIDA, exist_ok=True)
    ruta_s2 = os.path.join(SALIDA, 'S2_%s_AOI_10m.tif' % fecha)
    descargar_geotiff(compuesta, p['aoi_31982'], 10, ruta_s2, BANDAS_TODAS,
                      dtype='float32', nodata=NODATA_FLOAT, descripcion='S2 12 bandas')

    log('')
    log('Verificacion sobre el AOI completo:')
    st_aoi = verificar_raster(ruta_s2)
    m_prop = mascara_propiedad(ruta_s2, p['geom'])
    log('Verificacion dentro de la propiedad (%d px = %.1f ha):' % (m_prop.sum(), m_prop.sum() * 0.01))
    st_prop = verificar_raster(ruta_s2, mascara=m_prop)

    import rasterio
    with rasterio.open(ruta_s2) as src:
        transform = src.transform
        arr = src.read().astype('float64')
        nodata = src.nodata
    valido = np.all(arr != nodata, axis=0)
    if valido.sum() == 0:
        raise SystemExit('La descarga vino vacia (todo nodata)')
    r = {b: arr[i] for i, b in enumerate(BANDAS_TODAS)}

    # --- chequeo del offset con el dato, no con la memoria -----------------
    b2 = r['B2'][valido]
    mediana_b2 = float(np.median(b2))
    pct_neg = 100.0 * float((b2 < 0).mean())
    pct_clip = 100.0 * float((b2 <= -0.0999).mean())
    log('')
    log('Chequeo offset: mediana B2 = %.4f; %% B2<0 = %.3f%%; %% B2 en recorte Sen2Cor (-0.0999) = %.3f%%'
        % (mediana_b2, pct_neg, pct_clip))
    if mediana_b2 <= 0:
        raise SystemExit('Mediana de B2 <= 0: la reflectancia esta corregida DOS veces (o la '
                         'escena no es lo que se cree). No se sigue.')
    if pct_neg > 1.0:
        log('AVISO: %.2f%% de pixeles con B2 < 0 — mas que el recorte habitual; revisar' % pct_neg)

    # --- SCL: que fraccion de la propiedad es nube/sombra segun la escena ----
    scl = r['SCL']
    scl_prop = scl[m_prop & valido]
    clases_nube = {3: 'sombra', 8: 'nube media', 9: 'nube alta', 10: 'cirro', 11: 'nieve'}
    hist_scl = {int(k): int((scl_prop == k).sum()) for k in np.unique(scl_prop)}
    log('SCL dentro de la propiedad: %s' % ', '.join('%d:%d' % kv for kv in sorted(hist_scl.items())))
    px_nube = sum(v for k, v in hist_scl.items() if k in clases_nube)
    log('  nube+sombra (SCL 3,8,9,10,11) en la propiedad: %.2f%%; cs_cdf medio en la propiedad: %.3f'
        % (100.0 * px_nube / max(1, scl_prop.size), float(r['cs_cdf'][m_prop & valido].mean())))

    # --- SCL uint8 aparte -----------------------------------------------------
    ruta_scl = os.path.join(SALIDA, 'S2_%s_SCL_10m.tif' % fecha)
    scl_u8 = np.where(valido, scl, 0).astype('uint8')    # SCL 0 = sin dato, coincide
    escribir_geotiff(ruta_scl, scl_u8, transform, ['SCL'], dtype='uint8', nodata=0,
                     tags={'escena': esc['id']})

    # --- RGB uint8 estirado p2-p98 sobre el AOI -------------------------------
    rgb = np.zeros((3, arr.shape[1], arr.shape[2]), dtype='uint8')
    estiramiento = {}
    for i, b in enumerate(['B4', 'B3', 'B2']):
        v = r[b][valido]
        lo, hi = np.percentile(v, [2, 98])
        if hi - lo < 1e-4:
            raise SystemExit('banda %s degenerada (p2=%.4f p98=%.4f): no se puede estirar' % (b, lo, hi))
        estiramiento[b] = [float(lo), float(hi)]
        e = np.clip((r[b] - lo) / (hi - lo), 0, 1)
        rgb[i] = np.where(valido, np.round(1 + e * 254), 0).astype('uint8')   # 0 reservado a nodata
    ruta_rgb = os.path.join(SALIDA, 'S2_%s_RGB.tif' % fecha)
    escribir_geotiff(ruta_rgb, rgb, transform, ['R_B4', 'G_B3', 'B_B2'], dtype='uint8', nodata=0,
                     tags={'estiramiento_p2_p98': str(estiramiento), 'escena': esc['id']},
                     photometric='RGB')
    verificar_raster(ruta_rgb)

    # --- indices a 10 m ---------------------------------------------------------
    idx = calcular_indices(r)
    pila = np.full((len(INDICES), arr.shape[1], arr.shape[2]), NODATA_FLOAT, dtype='float32')
    for i, k in enumerate(INDICES):
        v = idx[k]
        if not np.all(np.isfinite(v[valido])):
            raise SystemExit('%s tiene NaN/inf dentro del area valida: falta una guarda' % k)
        pila[i] = np.where(valido, v, NODATA_FLOAT)
    ruta_idx = os.path.join(SALIDA, 'S2_%s_INDICES_10m.tif' % fecha)
    escribir_geotiff(ruta_idx, pila, transform, INDICES, dtype='float32', nodata=NODATA_FLOAT,
                     tags={'escena': esc['id'],
                           'NDMI': '(B8A-B11)/(B8A+B11)', 'NDRE': '(B8A-B5)/(B8A+B5)',
                           'NDWI': 'McFeeters (B3-B8)/(B3+B8)', 'MNDWI': '(B3-B11)/(B3+B11)',
                           'AWEInsh': '4*(B3-B11)-(0.25*B8+2.75*B12)', 'guarda_den': str(GUARDA_DEN)})
    log('')
    log('Indices sobre el AOI:')
    st_idx_aoi = verificar_raster(ruta_idx)
    log('Indices dentro de la propiedad:')
    st_idx_prop = verificar_raster(ruta_idx, mascara=m_prop)
    for k in ['NDVI', 'NDWI', 'MNDWI', 'NDMI', 'NDRE']:
        s = st_idx_aoi[k]
        if s['min'] < -1.0001 or s['max'] > 1.0001:
            raise SystemExit('%s fuera de [-1,1]: min %.4f max %.4f' % (k, s['min'], s['max']))

    guardar_json(os.path.join(SALIDA, 'S2_%s_estadisticas.json' % fecha), {
        'escena': esc['id'], 'fecha': fecha, 'satelite': esc['satelite'],
        'escala': 'DN/10000' + (' - 0.1' if args.offset else ''),
        'offset_forzado': args.offset,
        'chequeo_offset': {'mediana_B2': mediana_b2, 'pct_B2_negativo': pct_neg,
                           'pct_B2_recorte_sen2cor': pct_clip},
        'scl_propiedad': hist_scl,
        'estiramiento_rgb_p2_p98': estiramiento,
        'archivos': {'reflectancia': ruta_s2, 'scl': ruta_scl, 'rgb': ruta_rgb, 'indices': ruta_idx},
        'bandas_aoi': st_aoi, 'bandas_propiedad': st_prop,
        'indices_aoi': st_idx_aoi, 'indices_propiedad': st_idx_prop,
    })


if __name__ == '__main__':
    main()
