# -*- coding: utf-8 -*-
"""Helper de an_11: serie temporal de AGUA en GEE (2024-09 -> 2026-09) para el AOI.

Productos (todos en 02_ANALISIS/hidrologia_pro/, EPSG:31982, grid alineado a 10 m):
  agua_frecuencia_10m.tif    S2: freq_total, freq_chuva (Oct-Mar), freq_seca (Abr-Set), n_valid,
                                 ndmi_min_seca, ndmi_p10_seca, mndwi_max, mndwi_p90
  agua_s1_frecuencia_10m.tif S1 VV: freq_16, freq_18, freq_20 (dB), n_obs, vv_p10, vv_p50, vv_p90
  agua_jrc_mensual_30m.tif   JRC MonthlyHistory: freq (2015-2021), max_extent, n_valid
  agua_mapbiomas_30m.tif     MapBiomas Agua col.4: freq 2020-2024 (anos con agua / 5)
  serie_represa_s2.json / serie_represa_s1.json : area de agua por escena en la zona de la represa
IDs de GEE verificados con getInfo el 2026-09-06 (ver an_11 log).
"""
import json
import os

import ee

from an_00_config import ANALISIS, log
from comun import (cargar_propiedad, descargar_geotiff, ee_geom, inicializar_ee,
                   safe_getInfo)

HP = os.path.join(ANALISIS, 'hidrologia_pro')
os.makedirs(HP, exist_ok=True)

FECHA_INI, FECHA_FIN = '2024-09-01', '2026-09-07'
IDS = {'s2': 'COPERNICUS/S2_SR_HARMONIZED', 'csp': 'GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED',
       's1': 'COPERNICUS/S1_GRD', 'jrc_m': 'JRC/GSW1_4/MonthlyHistory',
       'jrc': 'JRC/GSW1_4/GlobalSurfaceWater',
       'mb_agua': 'projects/mapbiomas-public/assets/brazil/water/collection4/mapbiomas_brazil_collection4_water_v3'}
CS_MIN = 0.60            # Cloud Score+ cs_cdf >= 0.60 = pixel claro (umbral recomendado por Google)
MNDWI_MIN = 0.0          # misma regla que an_01 (Otsu cayo a 0 por distribucion unimodal)
NDVI_MAX_AGUA = 0.30
S1_UMBRALES_DB = [-16, -18, -20]
MESES_CHUVA = [10, 11, 12, 1, 2, 3]


def _s2_coleccion(aoi):
    s2 = ee.ImageCollection(IDS['s2']).filterBounds(aoi).filterDate(FECHA_INI, FECHA_FIN)
    csp = ee.ImageCollection(IDS['csp']).filterBounds(aoi).filterDate(FECHA_INI, FECHA_FIN)
    s2 = s2.linkCollection(csp, ['cs_cdf'])

    def prep(im):
        claro = im.select('cs_cdf').gte(CS_MIN)
        scl = im.select('SCL')
        valido = claro.And(scl.neq(0)).And(scl.neq(1)).And(scl.neq(3)).And(scl.neq(8)) \
                      .And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
        b = im.select(['B3', 'B4', 'B8', 'B11']).divide(1e4)
        mndwi = b.normalizedDifference(['B3', 'B11']).rename('mndwi')
        ndvi = b.normalizedDifference(['B8', 'B4']).rename('ndvi')
        ndmi = b.normalizedDifference(['B8', 'B11']).rename('ndmi')
        agua = mndwi.gt(MNDWI_MIN).And(ndvi.lt(NDVI_MAX_AGUA)).rename('agua')
        mes = ee.Number(im.date().get('month'))
        chuva = ee.Number(ee.List(MESES_CHUVA).indexOf(mes)).gte(0)  # ee.Number 0/1 (no Boolean: el filtro eq(1) fallaria)
        out = ee.Image.cat([agua.updateMask(valido), mndwi.updateMask(valido), ndmi.updateMask(valido),
                            valido.rename('valido')]) \
            .set({'chuva': chuva, 'fecha': im.date().format('YYYY-MM-dd'), 'mes': mes,
                  'nube_pct': im.get('CLOUDY_PIXEL_PERCENTAGE')})
        return out.copyProperties(im, ['system:time_start'])
    return s2.map(prep)


def _s1_coleccion(aoi):
    s1 = ee.ImageCollection(IDS['s1']).filterBounds(aoi).filterDate(FECHA_INI, FECHA_FIN) \
        .filter(ee.Filter.eq('instrumentMode', 'IW')) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))

    def prep(im):
        vv = im.select('VV')
        # filtro de speckle: mediana focal 3x3 (30 m) en dB
        vvf = vv.focal_median(radius=15, units='meters').rename('vv')
        bands = [vvf]
        for u in S1_UMBRALES_DB:
            bands.append(vvf.lt(u).rename('agua_%d' % abs(u)))
        mes = ee.Number(im.date().get('month'))
        return ee.Image.cat(bands).set({'chuva': ee.Number(ee.List(MESES_CHUVA).indexOf(mes)).gte(0),
                                        'fecha': im.date().format('YYYY-MM-dd'),
                                        'orbita': im.get('relativeOrbitNumber_start'),
                                        'paso': im.get('orbitProperties_pass')}) \
            .copyProperties(im, ['system:time_start'])
    return s1.map(prep)


def descargar_frecuencias(p):
    """Rasters de frecuencia S2, S1, JRC y MapBiomas. Devuelve dict de rutas + metadatos."""
    ee = inicializar_ee()
    aoi = ee.Geometry.Rectangle(list(p['aoi_31982']), 'EPSG:31982', False)
    out = {}
    # --- Sentinel-2 -----------------------------------------------------------
    s2 = _s2_coleccion(aoi)
    n_s2 = safe_getInfo(s2.size(), descripcion='S2 size')
    log('  S2 escenas %s..%s: %d' % (FECHA_INI, FECHA_FIN, n_s2))
    n_valid = s2.select('valido').sum().rename('n_valid')
    freq = s2.select('agua').sum().divide(n_valid).rename('freq_total')
    chu = s2.filter(ee.Filter.eq('chuva', 1)); sec = s2.filter(ee.Filter.eq('chuva', 0))
    n_chu = safe_getInfo(chu.size()); n_sec = safe_getInfo(sec.size())
    freq_c = chu.select('agua').sum().divide(chu.select('valido').sum()).rename('freq_chuva')
    freq_s = sec.select('agua').sum().divide(sec.select('valido').sum()).rename('freq_seca')
    seca_ndmi = s2.filter(ee.Filter.inList('mes', [6, 7, 8, 9])).select('ndmi')
    ndmi_min = seca_ndmi.min().rename('ndmi_min_seca')
    ndmi_p10 = seca_ndmi.reduce(ee.Reducer.percentile([10])).rename('ndmi_p10_seca')
    mndwi_max = s2.select('mndwi').max().rename('mndwi_max')
    mndwi_p90 = s2.select('mndwi').reduce(ee.Reducer.percentile([90])).rename('mndwi_p90')
    img = ee.Image.cat([freq, freq_c, freq_s, n_valid.toFloat(), ndmi_min, ndmi_p10, mndwi_max, mndwi_p90])
    bandas = ['freq_total', 'freq_chuva', 'freq_seca', 'n_valid', 'ndmi_min_seca', 'ndmi_p10_seca', 'mndwi_max', 'mndwi_p90']
    ruta = os.path.join(HP, 'agua_frecuencia_10m.tif')
    descargar_geotiff(img, p['aoi_31982'], 10, ruta, bandas, descripcion='S2 frecuencia de agua 10 m')
    out['s2'] = {'ruta': ruta, 'bandas': bandas, 'n_escenas': n_s2, 'n_chuva': n_chu, 'n_seca': n_sec,
                 'regla': 'cs_cdf>=%.2f & SCL valido; agua = MNDWI>%.1f & NDVI<%.2f' % (CS_MIN, MNDWI_MIN, NDVI_MAX_AGUA),
                 'id': IDS['s2'], 'periodo': [FECHA_INI, FECHA_FIN]}
    # --- Sentinel-1 -----------------------------------------------------------
    s1 = _s1_coleccion(aoi)
    n_s1 = safe_getInfo(s1.size(), descripcion='S1 size')
    orb = safe_getInfo(s1.aggregate_histogram('orbita'))
    log('  S1 escenas IW VV: %d  orbitas %s' % (n_s1, orb))
    bands = [s1.select('agua_%d' % abs(u)).mean().rename('freq_%d' % abs(u)) for u in S1_UMBRALES_DB]
    n_obs = s1.select('vv').count().rename('n_obs').toFloat()
    pct = s1.select('vv').reduce(ee.Reducer.percentile([10, 50, 90])).rename(['vv_p10', 'vv_p50', 'vv_p90'])
    chu1 = s1.filter(ee.Filter.eq('chuva', 1)); sec1 = s1.filter(ee.Filter.eq('chuva', 0))
    bands += [chu1.select('agua_16').mean().rename('freq_16_chuva'), sec1.select('agua_16').mean().rename('freq_16_seca')]
    img1 = ee.Image.cat(bands + [n_obs, pct])
    bandas1 = ['freq_%d' % abs(u) for u in S1_UMBRALES_DB] + ['freq_16_chuva', 'freq_16_seca', 'n_obs', 'vv_p10', 'vv_p50', 'vv_p90']
    ruta1 = os.path.join(HP, 'agua_s1_frecuencia_10m.tif')
    descargar_geotiff(img1, p['aoi_31982'], 10, ruta1, bandas1, descripcion='S1 frecuencia de agua 10 m')
    out['s1'] = {'ruta': ruta1, 'bandas': bandas1, 'n_escenas': n_s1, 'orbitas': orb,
                 'regla': 'VV dB, mediana focal 3x3, agua = VV < umbral', 'umbrales_db': S1_UMBRALES_DB,
                 'id': IDS['s1'], 'periodo': [FECHA_INI, FECHA_FIN]}
    # --- JRC mensual 2015 -> fin de la coleccion (2021-12 en GSW1_4) ---------------
    jm = ee.ImageCollection(IDS['jrc_m']).filterBounds(aoi).filterDate('2015-01-01', '2022-01-01')
    n_jm = safe_getInfo(jm.size())
    ultimo = safe_getInfo(jm.aggregate_max('system:index'))
    val = jm.map(lambda im: im.select('water').gt(0)).sum().rename('n_valid')
    agua = jm.map(lambda im: im.select('water').eq(2)).sum()
    fq = agua.divide(val).rename('freq')
    mx = ee.Image(IDS['jrc']).select('max_extent').rename('max_extent')
    occ = ee.Image(IDS['jrc']).select('occurrence').rename('occurrence')
    rutaj = os.path.join(HP, 'agua_jrc_mensual_30m.tif')
    descargar_geotiff(ee.Image.cat([fq, val.toFloat(), mx.toFloat(), occ.toFloat()]), p['aoi_31982'], 30, rutaj,
                      ['freq', 'n_valid', 'max_extent', 'occurrence'], descripcion='JRC mensual 30 m')
    out['jrc'] = {'ruta': rutaj, 'bandas': ['freq', 'n_valid', 'max_extent', 'occurrence'], 'n_meses': n_jm,
                  'ultimo_mes': ultimo, 'id': IDS['jrc_m'], 'nota': 'GSW1_4 termina en 2021-12: no hay 2022-2024'}
    # --- MapBiomas Agua col.4 2020-2024 ------------------------------------------
    mb = ee.Image(IDS['mb_agua'])
    anos = list(range(2020, 2025))
    stack = ee.Image.cat([mb.select('classification_%d' % a).eq(1).unmask(0).rename('a%d' % a) for a in anos])
    fmb = stack.reduce(ee.Reducer.sum()).divide(len(anos)).rename('freq_2020_2024')
    stack_all = ee.Image.cat([mb.select('classification_%d' % a).eq(1).unmask(0) for a in range(1985, 2025)])
    fmb_all = stack_all.reduce(ee.Reducer.sum()).divide(40).rename('freq_1985_2024')
    rutam = os.path.join(HP, 'agua_mapbiomas_30m.tif')
    descargar_geotiff(ee.Image.cat([fmb, fmb_all, mb.select('classification_2024').unmask(0).rename('agua_2024').toFloat()]),
                      p['aoi_31982'], 30, rutam, ['freq_2020_2024', 'freq_1985_2024', 'agua_2024'],
                      descripcion='MapBiomas Agua col4 30 m')
    out['mapbiomas'] = {'ruta': rutam, 'bandas': ['freq_2020_2024', 'freq_1985_2024', 'agua_2024'], 'id': IDS['mb_agua'],
                        'nota': 'valor 1 = agua anual; freq = anos con agua / n anos'}
    return out


def serie_represa(p, geom_represa_31982):
    """Area de agua (ha) por escena S2 y S1 dentro de la zona de la represa."""
    ee = inicializar_ee()
    aoi = ee.Geometry.Rectangle(list(p['aoi_31982']), 'EPSG:31982', False)
    g = ee_geom(geom_represa_31982)
    area_zona_ha = geom_represa_31982.area / 1e4
    s2 = _s2_coleccion(aoi)

    def f2(im):
        r = ee.Image.cat([im.select('agua').unmask(0).And(im.select('valido')).rename('agua'), im.select('valido').unmask(0)]) \
            .multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(), g, 10, crs='EPSG:31982')
        return ee.Feature(None, {'fecha': im.get('fecha'), 'chuva': im.get('chuva'), 'nube_pct': im.get('nube_pct'),
                                 'agua_ha': ee.Number(r.get('agua')).divide(1e4),
                                 'valido_ha': ee.Number(r.get('valido')).divide(1e4)})
    fc2 = safe_getInfo(s2.map(f2), descripcion='serie S2 represa')
    rows2 = [f['properties'] for f in fc2['features']]
    s1 = _s1_coleccion(aoi)

    def f1(im):
        r = im.select(['agua_16', 'agua_18', 'agua_20']).multiply(ee.Image.pixelArea()) \
            .reduceRegion(ee.Reducer.sum(), g, 10, crs='EPSG:31982')
        return ee.Feature(None, {'fecha': im.get('fecha'), 'chuva': im.get('chuva'), 'orbita': im.get('orbita'),
                                 'agua16_ha': ee.Number(r.get('agua_16')).divide(1e4),
                                 'agua18_ha': ee.Number(r.get('agua_18')).divide(1e4),
                                 'agua20_ha': ee.Number(r.get('agua_20')).divide(1e4)})
    fc1 = safe_getInfo(s1.map(f1), descripcion='serie S1 represa')
    rows1 = [f['properties'] for f in fc1['features']]
    for nombre, rows in (('serie_represa_s2.json', rows2), ('serie_represa_s1.json', rows1)):
        with open(os.path.join(HP, nombre), 'w', encoding='utf-8') as f:
            json.dump({'zona_ha': area_zona_ha, 'filas': rows}, f, ensure_ascii=False, indent=1)
        log('  -> %s (%d escenas)' % (nombre, len(rows)))
    return rows2, rows1, area_zona_ha


if __name__ == '__main__':
    p = cargar_propiedad()
    r = descargar_frecuencias(p)
    print(json.dumps(r, indent=1, ensure_ascii=False))
