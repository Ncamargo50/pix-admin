# -*- coding: utf-8 -*-
"""an_11 - HIDROLOGIA PRO: contraste con datos de GOBIERNO y ajuste de la hidrografia,
cuerpos de agua, nascentes y geometria de APP de la Fazenda Santo Antonio (G1 + G2).

Partes:
  1. CAR del propio inmueble y vecinos (replica oficial del SICAR publicada por el IAT-PR)
     -> CAR_propriedade_e_vizinhos.geojson + tabla declarado vs medido.
  2. Ensamble de 5 DEM (GLO30, NASADEM, SRTMGL1, AW3D30, FABDEM): red D8 por DEM con umbral
     calibrado contra FBDS, dispersion posicional por arroio y efecto en ha de APP.
  3. Agua: frecuencia S2 (Cloud Score+), S1 VV, JRC mensual, MapBiomas Agua; espejo de la
     represa por fuente y espejo de referencia.
  4. Nascentes: veredicto por candidato con toda la evidencia cruzada.
  5. Cursos: longitud/trazado por fuente dentro de cada gleba, clase de ancho, perenidad (indicio).
  6. APP recomputada con la mejor referencia + envolvente [min; max] por gleba.
Salidas: 02_ANALISIS/hidrologia_pro/ (rasters, GeoJSON, resultados_hidrologia_pro.json) y
COMPARACION_FUENTES_GOBIERNO.md en la carpeta del codigo. NO toca resultados_glebas.json ni an_07..10.
Regla de la casa: min/max/nodata de cada capa impresos (verificar_rango).
"""
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely
from rasterio import features as rfeat
from shapely.geometry import LineString, Point, MultiLineString, shape
from shapely.ops import unary_union, linemerge

warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import *  # noqa: F401,F403
from an_00_config import _limpio
from hp_gov_descarga import descargar_todo, GOV_PRO, LOG_JSON as GOV_LOG
from hp_dem_descarga import descargar_dems
from hp_gee_agua import descargar_frecuencias, serie_represa, HP, FECHA_INI, FECHA_FIN
from hp_dem_ensamble import (red_por_dem, cabeceras, calibrar_umbral, desplazamientos_por_arroio,
                             linea_mediana_ensamble, puntos_a_lo_largo, distancias)

T0 = time.time()
CODIGO_DIR = os.path.dirname(os.path.abspath(__file__))
MD_OUT = os.path.join(CODIGO_DIR, 'COMPARACION_FUENTES_GOBIERNO.md')
JSON_OUT = os.path.join(HP, 'resultados_hidrologia_pro.json')
LOG_TXT = os.path.join(HP, 'log_hidrologia_pro.txt')
_log_lines = []
_log_orig = log


def log(msg=''):  # noqa: F811  duplica el log a archivo
    _log_orig(msg)
    _log_lines.append(str(msg))


RES = {'_meta': {'crs': CRS_METRICO, 'generado': time.strftime('%Y-%m-%d %H:%M'),
                 'periodo_agua': [FECHA_INI, FECHA_FIN], 'script': 'an_11_hidrologia_pro.py'}}
FUENTES = []   # filas de la tabla fuente por fuente del MD


def fuente(institucion, capa, escala, fecha, url, respondio, aporta, discrepancia=''):
    FUENTES.append({'institucion': institucion, 'capa': capa, 'escala': escala, 'fecha': fecha, 'url': url,
                    'respondio': respondio, 'aporta': aporta, 'discrepancia': discrepancia})


def ha_(g):
    return round(float(g.area) / 1e4, 3) if g is not None and not g.is_empty else 0.0


def poly_only(g):
    if g is None or g.is_empty:
        return shapely.Polygon()
    if g.geom_type in ('Polygon', 'MultiPolygon'):
        return g
    if hasattr(g, 'geoms'):
        pp = [x for x in g.geoms if x.geom_type in ('Polygon', 'MultiPolygon')]
        return unary_union(pp) if pp else shapely.Polygon()
    return shapely.Polygon()


def line_only(g):
    if g is None or g.is_empty:
        return LineString()
    if g.geom_type in ('LineString', 'MultiLineString'):
        return g
    if hasattr(g, 'geoms'):
        ll = [x for x in g.geoms if x.geom_type in ('LineString', 'MultiLineString')]
        return unary_union(ll) if ll else LineString()
    return LineString()


def guardar_hp(gdf, nombre):
    """GeoJSON 31982 + wgs84 en hidrologia_pro."""
    gdf = gpd.GeoDataFrame(gdf, geometry='geometry', crs=CRS_METRICO)
    for c in gdf.columns:
        if c != 'geometry' and gdf[c].dtype == object:
            gdf[c] = gdf[c].map(lambda v: v if isinstance(v, (str, int, float, bool)) or v is None else str(v))
    for suf, g in (('', gdf), ('_wgs84', gdf.to_crs(CRS_WGS84))):
        r = os.path.join(HP, nombre + suf + '.geojson')
        if os.path.exists(r):
            os.remove(r)
        if len(g):
            g.to_file(r, driver='GeoJSON')
        else:
            with open(r, 'w') as f:
                json.dump({'type': 'FeatureCollection', 'features': []}, f)
    log('  -> %s (%d feats)' % (os.path.join(HP, nombre + '.geojson'), len(gdf)))


def leer_gov(nombre, recorte=None):
    """Lee una capa de gov_pro (WGS84) -> 31982, force_2d, make_valid, recorte opcional."""
    r = os.path.join(GOV_PRO, nombre + '.geojson')
    if not os.path.exists(r):
        return gpd.GeoDataFrame(geometry=[], crs=CRS_METRICO)
    g = gpd.read_file(r)
    if len(g) == 0:
        return gpd.GeoDataFrame(geometry=[], crs=CRS_METRICO)
    if g.crs is None:
        g = g.set_crs(CRS_WGS84)
    g = g[g.geometry.notna()].copy()
    g['geometry'] = shapely.force_2d(g.geometry.values)
    g = g.to_crs(CRS_METRICO)
    g['geometry'] = g.geometry.make_valid()
    if recorte is not None:
        g = g[g.intersects(recorte)].copy()
    return g.reset_index(drop=True)


def muestrear(ruta, banda, pts):
    """Valores de una banda en puntos (lista shapely Point). NaN fuera / nodata."""
    with rasterio.open(ruta) as ds:
        idx = [i + 1 for i, d in enumerate(ds.descriptions) if d == banda]
        if not idx and ds.count == 1:
            idx = [1]   # DEM de una banda con otro nombre (p.ej. 'NASADEM')
        if not idx:
            raise KeyError('banda %s no esta en %s (%s)' % (banda, ruta, ds.descriptions))
        vals = np.array([v[0] for v in ds.sample([(p.x, p.y) for p in pts], indexes=idx)], dtype=np.float64)
        if ds.nodata is not None:
            vals[vals == ds.nodata] = np.nan
    return vals


def estad_zona(ruta, banda, geom, func='mean'):
    """Estadistica de una banda dentro de un poligono (all_touched=False)."""
    with rasterio.open(ruta) as ds:
        i = [k + 1 for k, d in enumerate(ds.descriptions) if d == banda][0]
        a = ds.read(i).astype(np.float64)
        if ds.nodata is not None:
            a[a == ds.nodata] = np.nan
        m = rfeat.rasterize([(geom, 1)], out_shape=a.shape, transform=ds.transform, fill=0, dtype=np.uint8) > 0
        v = a[m]
        v = v[np.isfinite(v)]
        if v.size == 0:
            return np.nan, 0
        if func == 'mean':
            return float(v.mean()), int(v.size)
        if func == 'max':
            return float(v.max()), int(v.size)
        if func == 'min':
            return float(v.min()), int(v.size)
        if func.startswith('p'):
            return float(np.percentile(v, float(func[1:]))), int(v.size)
    return np.nan, 0


def area_umbral(ruta, banda, geom, umbral, mayor=True):
    """ha de pixeles (dentro de geom) con banda >= umbral (o <= si mayor=False) + poligono."""
    with rasterio.open(ruta) as ds:
        i = [k + 1 for k, d in enumerate(ds.descriptions) if d == banda][0]
        a = ds.read(i).astype(np.float64)
        if ds.nodata is not None:
            a[a == ds.nodata] = np.nan
        m = rfeat.rasterize([(geom, 1)], out_shape=a.shape, transform=ds.transform, fill=0, dtype=np.uint8) > 0
        sel = m & np.isfinite(a) & ((a >= umbral) if mayor else (a <= umbral))
        px = abs(ds.transform.a * ds.transform.e)
        geoms = [shape(g) for g, v in rfeat.shapes(sel.astype(np.uint8), mask=sel, transform=ds.transform)]
        return round(sel.sum() * px / 1e4, 3), (unary_union(geoms) if geoms else shapely.Polygon())


# ==============================================================================
titulo('0. Insumos: propiedad, glebas, hidrografia oficial ya descargada, capas gov_pro')
# ==============================================================================
p = propiedad()
PROP = p['geom']
glim = gpd.read_file(os.path.join(ANALISIS, 'gleba_limites.geojson'))
GLEBAS = {r.gleba: r.geometry for _, r in glim.iterrows()}
for k, g in GLEBAS.items():
    log('  %s %.2f ha' % (k, g.area / 1e4))
ZONA = PROP.buffer(P['margen_aoi_hidro_m'])
ZONA_DEM = PROP.buffer(3000)

fbds = leer_vector('fbds_rios', recorte=ZONA_DEM)
fbds['id'] = fbds['objectid'].astype(str)
nasc = leer_vector('fbds_nascentes', recorte=ZONA)
nasc['id'] = nasc['objectid'].astype(str)
massas = leer_vector('fbds_massas', recorte=ZONA)
otto = leer_vector('otto', recorte=ZONA)
ana = leer_vector('ana', recorte=ZONA)
ibge = leer_vector('ibge', recorte=ZONA)
car_geos = leer_vector('car_vecinos', recorte=ZONA)
arroios = {}
for gl in GLEBAS:
    a = gpd.read_file(os.path.join(ANALISIS, 'gleba_%s_arroios.geojson' % gl))
    a['fbds_ids'] = a['fbds_ids'].astype(str)
    arroios[gl] = a
    log('  %s: %d arroios (%s)' % (gl, len(a), ', '.join(a['nome'].tolist())))
nasc_cons = gpd.read_file(os.path.join(ANALISIS, 'nascentes_consolidadas.geojson'))
massas_prop = gpd.read_file(os.path.join(ANALISIS, 'massas_dagua_propriedade.geojson'))
ESPELHO_FBDS = unary_union(list(massas_prop.geometry))
ZONA_REPRESA = ESPELHO_FBDS.buffer(60)
RG = leer_json(os.path.join(ANALISIS, 'resultados_glebas.json'))

log('  descarga (o reutilizacion) de capas de gobierno adicionales -> %s' % GOV_PRO)
GOV = descargar_todo()
gov_log = leer_json(GOV_LOG)
log('  descarga (o reutilizacion) de DEM SRTMGL1 y AW3D30 -> 01_DATOS_SATELITE')
DEM_RUTAS = descargar_dems(p)

# capas gov_pro en memoria
car = {k: leer_gov(v if isinstance(v, str) else k) for k, v in {}.items()}
CAR_L = {}
for nombre in ['IAT_CAR_area_imovel', 'IAT_CAR_hidrografia', 'IAT_CAR_app_total', 'IAT_CAR_reserva_legal',
               'IAT_CAR_vegetacao_nativa', 'IAT_CAR_area_consolidada', 'IAT_CAR_servidao_administrativa',
               'IAT_CAR_area_pousio', 'IAT_CAR_uso_restrito']:
    CAR_L[nombre] = leer_gov(nombre)
sigef = leer_gov('INCRA_SIGEF_imoveis_certificados')
snci = leer_gov('INCRA_SNCI_imoveis_certificados')
curvas = leer_gov('IAT_curvas_nivel_50k_20m', recorte=ZONA)
enq = leer_gov('IAT_enquadramento_hidrografia_otto', recorte=ZONA)
uso2012 = leer_gov('IAT_uso_cobertura_terra_2012_wv2', recorte=ZONA)
massa50k = leer_gov('IAT_hidro50k_massa_dagua_paranacidade', recorte=ZONA)
ana_massa = leer_gov('ANA_massa_dagua', recorte=ZONA)
ana_res = leer_gov('ANA_reservatorios_UGRH', recorte=ZONA)
outorgas = leer_gov('IAT_outorgas_sigarh', recorte=ZONA)
outorgas_crh = leer_gov('IAT_outorgas_captacao_crh', recorte=ZONA)
frag_prio = leer_gov('IAT_fragmentos_florestais_prioritarios', recorte=PROP)
mananciais = leer_gov('IAT_mananciais_2023', recorte=ZONA)
mananciais26 = leer_gov('IAT_mananciais_superficiais_2026', recorte=ZONA)
for k, g in [('curvas 50k', curvas), ('enquadramento', enq), ('uso 2012 WV2', uso2012), ('massas 50k', massa50k),
             ('ANA massa', ana_massa), ('ANA reserv', ana_res), ('outorgas SIGARH', outorgas), ('outorgas CRH', outorgas_crh),
             ('frag prioritarios (en PROP)', frag_prio), ('mananciais', mananciais)]:
    log('  gov_pro %-28s %4d feats en zona' % (k, len(g)))

# ==============================================================================
titulo('1. CAR del inmueble y vecinos (replica oficial SICAR publicada por IAT-PR)')
# ==============================================================================
im = CAR_L['IAT_CAR_area_imovel'].copy()
im['area_geom_ha'] = im.area / 1e4
for gl, gg in GLEBAS.items():
    im['en_%s_ha' % gl] = im.geometry.intersection(gg).area / 1e4
im['en_prop_ha'] = im.geometry.intersection(PROP).area / 1e4
im_sel = im[im.en_prop_ha > 0.01].sort_values('en_prop_ha', ascending=False).copy()
log('  inmoveis CAR que intersectan las glebas:')
for _, r in im_sel.iterrows():
    log('    %s  status=%s  condicao="%s"  area_decl=%.2f ha  geom=%.2f ha  en G1=%.2f  en G2=%.2f  mod.fiscais=%s'
        % (r.cod_imovel, r.ind_status, r.des_condic, r.num_area, r.area_geom_ha, r.en_G1_ha, r.en_G2_ha, r.get('mod_fiscal')))
CAR_G1 = im_sel.iloc[0].cod_imovel if len(im_sel) else None
# el CAR "de G2": el que cubre la mayor parte de G2
CAR_G2 = im_sel.sort_values('en_G2_ha', ascending=False).iloc[0].cod_imovel if len(im_sel) and im_sel.en_G2_ha.max() > 0.01 else None
log('  => CAR que cubre G1: %s ; CAR que cubre G2: %s' % (CAR_G1, CAR_G2))
# solapes entre CAR (CAR se solapan entre si: declaratorio)
solapes = []
for i in range(len(im_sel)):
    for j in range(i + 1, len(im_sel)):
        s = im_sel.iloc[i].geometry.intersection(im_sel.iloc[j].geometry).intersection(PROP).area / 1e4
        if s > 0.01:
            solapes.append({'a': im_sel.iloc[i].cod_imovel, 'b': im_sel.iloc[j].cod_imovel, 'solape_en_prop_ha': round(s, 3)})
for s in solapes:
    log('    SOLAPE %.2f ha dentro de la propiedad entre %s y %s' % (s['solape_en_prop_ha'], s['a'][-8:], s['b'][-8:]))
# cobertura de cada gleba por su CAR
cobert = {}
for gl, gg in GLEBAS.items():
    cod = CAR_G1 if gl == 'G1' else CAR_G2
    geom_car = unary_union(list(im[im.cod_imovel == cod].geometry)) if cod else shapely.Polygon()
    dentro = gg.intersection(geom_car).area / 1e4
    fuera_gleba = geom_car.difference(PROP).area / 1e4
    sin_car = gg.difference(unary_union(list(im.geometry))).area / 1e4
    cobert[gl] = {'cod_imovel': cod, 'gleba_ha': round(gg.area / 1e4, 2), 'cubierta_por_su_car_ha': round(dentro, 2),
                  'pct_gleba_cubierta': round(100 * dentro / (gg.area / 1e4), 1),
                  'car_fuera_de_las_glebas_ha': round(fuera_gleba, 2), 'gleba_sin_ningun_car_ha': round(sin_car, 3)}
    log('  %s: %.1f%% cubierta por %s; %.2f ha del CAR quedan FUERA de las glebas; %.3f ha de gleba sin CAR'
        % (gl, cobert[gl]['pct_gleba_cubierta'], (cod or '-')[-8:], fuera_gleba, sin_car))
# SIGEF / SNCI
sg = sigef.copy(); sg['en_prop_ha'] = sg.geometry.intersection(PROP).area / 1e4; sg['area_ha'] = sg.area / 1e4
sg_sel = sg[sg.en_prop_ha > 0.01]
for _, r in sg_sel.iterrows():
    log('  SIGEF %s "%s" matricula=%s mun=%s status=%s area=%.2f ha  en prop=%.2f'
        % (r.codigo_imo, r.nome_area, r.registro_m, r.municipio_, r.status, r.area_ha, r.en_prop_ha))
sn = snci.copy(); sn['en_prop_ha'] = sn.geometry.intersection(PROP).area / 1e4
sn_sel = sn[sn.en_prop_ha > 0.01]
for _, r in sn_sel.iterrows():
    log('  SNCI %s "%s" area=%s en prop=%.2f' % (r.cod_imovel, r.nome_imove, r.qtd_area_p, r.en_prop_ha))

# temas por CAR y por gleba
TEMAS = {'IAT_CAR_hidrografia': 'hidrografia', 'IAT_CAR_app_total': 'app', 'IAT_CAR_reserva_legal': 'reserva_legal',
         'IAT_CAR_vegetacao_nativa': 'vegetacao_nativa', 'IAT_CAR_area_consolidada': 'area_consolidada',
         'IAT_CAR_servidao_administrativa': 'servidao', 'IAT_CAR_area_pousio': 'pousio', 'IAT_CAR_uso_restrito': 'uso_restrito'}
car_decl = {}
feats_out = []
codigos_rel = {c: ('propio_G1' if c == CAR_G1 else 'cubre_G2' if c == CAR_G2 else 'vecino_intersecta') for c in im_sel.cod_imovel}
vecinos_100 = im[(im.geometry.distance(PROP) < 100) & (~im.cod_imovel.isin(codigos_rel))]
for c in vecinos_100.cod_imovel:
    codigos_rel[c] = 'vecino_100m'
for _, r in im[im.cod_imovel.isin(codigos_rel)].iterrows():
    feats_out.append({'capa': 'area_imovel', 'cod_tema': r.cod_tema, 'cod_imovel': r.cod_imovel, 'relacao': codigos_rel[r.cod_imovel],
                      'ind_status': r.ind_status, 'des_condic': r.des_condic, 'num_area_decl': r.num_area,
                      'area_geom_ha': round(r.area_geom_ha, 3), 'geometry': r.geometry})
for capa, tema in TEMAS.items():
    g = CAR_L[capa]
    if len(g) == 0:
        continue
    for _, r in g[g.cod_imovel.isin(codigos_rel)].iterrows():
        feats_out.append({'capa': tema, 'cod_tema': r.cod_tema, 'cod_imovel': r.cod_imovel, 'relacao': codigos_rel[r.cod_imovel],
                          'ind_status': r.ind_status, 'des_condic': r.des_condic, 'num_area_decl': r.get('num_area'),
                          'area_geom_ha': round(r.geometry.area / 1e4, 3), 'geometry': r.geometry})
    for cod in [CAR_G1, CAR_G2]:
        if cod is None:
            continue
        s = g[g.cod_imovel == cod]
        d = car_decl.setdefault(cod, {})
        for _, r in s.iterrows():
            key = tema if tema != 'hidrografia' else 'hidro_' + str(r.cod_tema)
            e = d.setdefault(key, {'num_area_decl': 0.0, 'geom_total_ha': 0.0, 'en_G1_ha': 0.0, 'en_G2_ha': 0.0, 'n': 0})
            e['n'] += 1
            e['num_area_decl'] = round(e['num_area_decl'] + float(r.get('num_area') or 0.0), 3)
            e['geom_total_ha'] = round(e['geom_total_ha'] + r.geometry.area / 1e4, 3)
            for gl, gg in GLEBAS.items():
                e['en_%s_ha' % gl] = round(e['en_%s_ha' % gl] + r.geometry.intersection(gg).area / 1e4, 3)
for cod, d in car_decl.items():
    log('  CAR %s:' % cod)
    for k, e in d.items():
        log('    %-45s n=%d decl=%-9.3f geom=%-9.3f enG1=%-8.3f enG2=%.3f' % (k, e['n'], e['num_area_decl'], e['geom_total_ha'], e['en_G1_ha'], e['en_G2_ha']))
guardar_hp(gpd.GeoDataFrame(feats_out, geometry='geometry', crs=CRS_METRICO), 'CAR_propriedade_e_vizinhos')

# reservatorio declarado en CAR (propio) y su geometria
res_car = CAR_L['IAT_CAR_hidrografia']
res_car = res_car[(res_car.cod_imovel == CAR_G1) & (res_car.cod_tema.str.contains('RESERVATORIO'))]
RES_CAR_GEOM = unary_union(list(res_car.geometry)) if len(res_car) else shapely.Polygon()
res_geos = car_geos[(car_geos.cod_imovel == CAR_G1) & (car_geos.cod_tema.str.contains('RESERVATORIO'))]
RES_GEOS_GEOM = unary_union(list(res_geos.geometry)) if len(res_geos) else shapely.Polygon()
log('  reservatorio declarado (IAT replica) %.3f ha | (WFS geoserver.pr) %.3f ha | FBDS 2013 %.3f ha | interseccion CAR-FBDS %.3f ha'
    % (ha_(RES_CAR_GEOM), ha_(RES_GEOS_GEOM), ha_(ESPELHO_FBDS), ha_(RES_CAR_GEOM.intersection(ESPELHO_FBDS))))
RES_CAR_PARTES = []
for gpart in (RES_CAR_GEOM.geoms if hasattr(RES_CAR_GEOM, 'geoms') else [RES_CAR_GEOM]):
    if gpart.is_empty:
        continue
    RES_CAR_PARTES.append({'area_ha': ha_(gpart), 'x': round(gpart.centroid.x), 'y': round(gpart.centroid.y),
                           'dist_espelho_fbds_m': round(gpart.distance(ESPELHO_FBDS), 1), 'geom': gpart})
    log('    parte del reservatorio CAR: %.3f ha en (%d, %d), a %.0f m del espejo FBDS' % (ha_(gpart), gpart.centroid.x, gpart.centroid.y, gpart.distance(ESPELHO_FBDS)))

# comparacion declarado vs medido (medido = resultados_glebas.json vigente)
comp_car = {}
for gl in GLEBAS:
    cod = CAR_G1 if gl == 'G1' else CAR_G2
    d = car_decl.get(cod, {})
    g = RG[gl]
    fila = {'cod_imovel': cod,
            'area_imovel_decl_ha': float(im[im.cod_imovel == cod].num_area.iloc[0]) if cod else None,
            'area_gleba_medida_ha': g['area_ha'],
            'app_car_geom_en_gleba_ha': d.get('app', {}).get('en_%s_ha' % gl, 0.0),
            'app_car_num_area_decl_ha': d.get('app', {}).get('num_area_decl', 0.0),
            'app_medida_ha': g['app']['exigida_ha'],
            'app_medida_cenario_fbds_ha': g['app']['cenario_fbds_iat']['exigida_ha'],
            'rl_car_geom_en_gleba_ha': d.get('reserva_legal', {}).get('en_%s_ha' % gl, 0.0),
            'rl_car_num_area_decl_ha': d.get('reserva_legal', {}).get('num_area_decl', 0.0),
            'rl_car_tema': next((k for k in d if k == 'reserva_legal'), None),
            'rl_exigida_20pct_ha': g['rl_exigida_ha'],
            'rl_existente_medida_ha': g['reserva_legal'].get('remanescente_fora_app_ha'),
            'veg_nativa_car_en_gleba_ha': d.get('vegetacao_nativa', {}).get('en_%s_ha' % gl, 0.0),
            'veg_nativa_car_decl_ha': d.get('vegetacao_nativa', {}).get('num_area_decl', 0.0),
            'floresta_nativa_medida_ha': g['vegetacao']['floresta_nativa_car_ha'],
            'area_consolidada_car_en_gleba_ha': d.get('area_consolidada', {}).get('en_%s_ha' % gl, 0.0),
            'hidro_car_rio_ate10_en_gleba_ha': d.get('hidro_RIO_ATE_10', {}).get('en_%s_ha' % gl, 0.0),
            'hidro_car_reservatorio_en_gleba_ha': d.get('hidro_RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO', {}).get('en_%s_ha' % gl, 0.0),
            'hidro_medida_fbds_km': g['arroios']['km_dentro'],
            'reservatorio_medido_fbds_ha': g['lagoas']['espelho_fbds_2013_ha']}
    comp_car[gl] = fila
RES['car'] = {'car_g1': CAR_G1, 'car_g2': CAR_G2, 'imoveis_intersectan': im_sel.drop(columns='geometry').round(3).to_dict('records'),
              'solapes_entre_car': solapes, 'cobertura': cobert,
              'sigef_intersecta': sg_sel.drop(columns='geometry').astype(str).to_dict('records'),
              'snci_intersecta': sn_sel.drop(columns='geometry').astype(str).to_dict('records'),
              'declarado_por_tema': car_decl, 'comparacion_declarado_vs_medido': comp_car,
              'reservatorio_declarado_ha_iat': ha_(RES_CAR_GEOM), 'reservatorio_declarado_ha_geoserver': ha_(RES_GEOS_GEOM),
              'nascentes_declaradas': 'la replica IAT del CAR no publica tema de nascentes; en el bbox los temas de hidrografia son %s'
                                      % sorted(CAR_L['IAT_CAR_hidrografia'].cod_tema.unique().tolist()),
              'fuente': gov_log.get('IAT_CAR_area_imovel', {}).get('url'), 'fecha_descarga': gov_log.get('IAT_CAR_area_imovel', {}).get('fecha'),
              'sicar_directo': 'consultapublica.car.gov.br responde (TLS legacy SECLEVEL=1) pero la descarga por municipio/imovel exige reCAPTCHA: NO se intento saltar; se uso la replica oficial del IAT-PR'}
fuente('IAT-PR (replica SICAR)', 'Base_Geo_Cadastro_Ambiental_rural (9 capas CAR)', 'declaratorio (SICAR)', gov_log.get('IAT_CAR_area_imovel', {}).get('fecha'),
       gov_log.get('IAT_CAR_area_imovel', {}).get('url'), 'si', 'CAR PROPIO %s (%.1f ha) y CAR de G2 %s; APP, RL, veg. nativa, consolidada, hidrografia, reservatorio declarados'
       % ((CAR_G1 or '-'), float(im[im.cod_imovel == CAR_G1].num_area.iloc[0]) if CAR_G1 else 0, (CAR_G2 or '-')),
       'APP CAR %.2f vs medida %.2f ha (G1); RL averbada %.2f vs exigida %.2f ha; reservatorio %.2f vs FBDS %.2f ha'
       % (comp_car['G1']['app_car_geom_en_gleba_ha'], comp_car['G1']['app_medida_ha'], comp_car['G1']['rl_car_geom_en_gleba_ha'],
          comp_car['G1']['rl_exigida_20pct_ha'], ha_(RES_CAR_GEOM), ha_(ESPELHO_FBDS)))
fuente('INCRA via IAT', 'imoveis_certificados_sigef_incra / snci', 'certificacao georreferenciada', gov_log.get('INCRA_SIGEF_imoveis_certificados', {}).get('fecha'),
       gov_log.get('INCRA_SIGEF_imoveis_certificados', {}).get('url'), 'si',
       'parcelas SIGEF que cubren las glebas: %s' % '; '.join('%s %s %.2f ha (matr. %s, mun. %s)' % (r.nome_area, r.status, r.area_ha, r.registro_m, r.municipio_) for _, r in sg_sel.iterrows()),
       'perimetro SIGEF vs poligono del cliente: %.2f ha de G1 dentro del SIGEF principal' % (sg_sel.en_prop_ha.max() if len(sg_sel) else 0))
fuente('SICAR (SFB) directo', 'consultapublica.car.gov.br downloads/exportShapeFile', 'declaratorio', '2026-09-06',
       'https://consultapublica.car.gov.br/publico/estados/downloads', 'parcial', 'pagina responde solo con TLS legacy; descarga exige reCAPTCHA (no se salto)', 'n/a')
fuente('Paraná geoserver (CELEPAR)', 'car:hidrografia_pol_p4674 (WFS)', 'declaratorio', '2026-09-06',
       'https://geoserver.pr.gov.br/geoserver/ows (WFS)', 'si', 'hidrografia CAR (misma fuente, version WFS): reservatorio propio %.3f ha' % ha_(RES_GEOS_GEOM),
       'vs replica IAT %.3f ha (dif. %.3f ha)' % (ha_(RES_CAR_GEOM), abs(ha_(RES_GEOS_GEOM) - ha_(RES_CAR_GEOM))))

# ==============================================================================
titulo('2. Ensamble de DEM: red D8 por DEM, calibracion vs FBDS, dispersion por arroio')
# ==============================================================================
DEMS = {'GLO30': R['dem'], 'NASADEM': R['dem_nasa'], 'SRTMGL1': DEM_RUTAS['SRTMGL1'], 'AW3D30': DEM_RUTAS['AW3D30'],
        'FABDEM': os.path.join(DATOS_SAT, 'DEM_FABDEM_AOIdem_30m.tif')}
UMBRALES = [5, 10, 20, 40]
ens = {}
calib_all = {}
redes_opt = {}
cab_opt = {}
fbds_full = list(fbds.geometry)
for nombre, ruta in DEMS.items():
    if not os.path.exists(ruta):
        log('  DEM %s NO disponible (%s)' % (nombre, ruta)); continue
    t = time.time()
    r = red_por_dem(ruta, nombre, UMBRALES)
    calib, u = calibrar_umbral(r['redes'], fbds_full, ZONA)
    calib_all[nombre] = {'calibracion': {str(k): {a: (round(b, 1) if isinstance(b, float) else b) for a, b in v.items()} for k, v in calib.items()},
                         'umbral_elegido_ha': u}
    redes_opt[nombre] = r['redes'][u]
    cab_opt[nombre] = cabeceras(r['redes'][u], r['acc'], r['transform'], u / r['cell_ha'])
    ens[nombre] = r
    c = calib[u]
    log('  %-8s umbral %2d ha | red %.2f km vs FBDS %.2f km | FBDS->DEM med %.1f p90 %.1f | DEM->FBDS med %.1f p90 %.1f | cabeceras %d | %.1fs'
        % (nombre, u, c['km_dem'], c['km_fbds'], c['fbds_a_dem_med_m'], c['fbds_a_dem_p90_m'], c['dem_a_fbds_med_m'], c['dem_a_fbds_p90_m'],
           len(cab_opt[nombre]), time.time() - t))
# guardar redes y cabeceras
rows = []
for nombre, red in redes_opt.items():
    for g in red.geometry:
        gz = g.intersection(ZONA)
        if not gz.is_empty:
            rows.append({'dem': nombre, 'umbral_ha': calib_all[nombre]['umbral_elegido_ha'], 'geometry': gz})
guardar_hp(gpd.GeoDataFrame(rows, geometry='geometry', crs=CRS_METRICO).explode(index_parts=False), 'hidro_dem_ensamble_redes')
rows = [{'dem': n, 'geometry': c} for n, cc in cab_opt.items() for c in cc if c.within(ZONA)]
guardar_hp(gpd.GeoDataFrame(rows, geometry='geometry', crs=CRS_METRICO), 'hidro_dem_ensamble_cabeceras')

# dispersion por arroio (curso FBDS completo dentro de gleba + 60 m, para que el buffer de 30 m cierre bien)
disp = {}
lineas_ens = []
for gl, a in arroios.items():
    disp[gl] = {}
    for _, ar in a.iterrows():
        ids = [s.strip() for s in ar.fbds_ids.split(',')]
        curso_full = line_only(unary_union(list(fbds[fbds.id.isin(ids)].geometry)))
        curso_full = line_only(linemerge(curso_full) if curso_full.geom_type == 'MultiLineString' else curso_full)
        zona_ar = GLEBAS[gl].buffer(60)
        curso = line_only(curso_full.intersection(zona_ar))
        if curso.geom_type == 'MultiLineString':
            curso = max(curso.geoms, key=lambda x: x.length) if len(curso.geoms) else LineString()
        pts, dist, near = desplazamientos_por_arroio(curso, redes_opt, paso=10.0, dmax=150.0)
        # dispersion ENTRE DEM: rango de los puntos mas cercanos en cada punto
        rangos = []
        for i in range(len(pts)):
            xs = np.array([near[k][i] for k in near]); ok = np.isfinite(xs[:, 0])
            if ok.sum() >= 2:
                xy = xs[ok]
                dmax_pair = max(np.hypot(*(xy[m] - xy[n])) for m in range(len(xy)) for n in range(m + 1, len(xy)))
                rangos.append(dmax_pair)
        med = linea_mediana_ensamble(pts, near, min_dems=3)
        d_med_fbds = distancias(puntos_a_lo_largo([med]), [curso]) if med is not None else np.array([np.nan])
        por_dem = {k: {'dist_mediana_m': (round(float(np.nanmedian(v)), 1) if np.isfinite(v).any() else None),
                       'dist_p90_m': (round(float(np.nanpercentile(v[np.isfinite(v)], 90)), 1) if np.isfinite(v).any() else None),
                       'pct_con_correspondencia_150m': round(100 * float(np.isfinite(v).mean()), 1)} for k, v in dist.items()}
        # APP de 30 m del curso: FBDS vs mediana del ensamble vs cada DEM (linea emparejada)
        app_fbds = poly_only(curso.buffer(P['app_curso_m']).intersection(GLEBAS[gl]))
        app_ens = poly_only(med.buffer(P['app_curso_m']).intersection(GLEBAS[gl])) if med is not None else shapely.Polygon()
        app_dem = {}
        for k in near:
            xy = near[k]; ok = np.isfinite(xy[:, 0])
            if ok.sum() >= 2:
                ln = LineString([(x, y) if o else (pt.x, pt.y) for (x, y), o, pt in zip(xy, ok, pts)]).simplify(5.0)
                app_dem[k] = ha_(poly_only(ln.buffer(P['app_curso_m']).intersection(GLEBAS[gl])))
        # desplazamiento lateral neto de la mediana: area simetrica no compartida entre las dos APP
        sim_dif = ha_(app_fbds.symmetric_difference(app_ens)) if med is not None else None
        disp[gl][ar.nome] = {'fbds_ids': ids, 'long_fbds_en_gleba_m': round(float(line_only(curso_full.intersection(GLEBAS[gl])).length), 1),
                             'n_puntos_eje': len(pts), 'por_dem': por_dem,
                             'dispersion_entre_dem_mediana_m': round(float(np.median(rangos)), 1) if rangos else None,
                             'dispersion_entre_dem_p90_m': round(float(np.percentile(rangos, 90)), 1) if rangos else None,
                             'mediana_ensamble_vs_fbds_med_m': round(float(np.nanmedian(d_med_fbds)), 1) if np.isfinite(d_med_fbds).any() else None,
                             'mediana_ensamble_vs_fbds_p90_m': round(float(np.nanpercentile(d_med_fbds[np.isfinite(d_med_fbds)], 90)), 1) if np.isfinite(d_med_fbds).any() else None,
                             'app30_fbds_ha': ha_(app_fbds), 'app30_mediana_ensamble_ha': ha_(app_ens), 'app30_por_dem_ha': app_dem,
                             'app30_dif_simetrica_fbds_vs_ensamble_ha': sim_dif,
                             'app30_envolvente_ha': [round(min([ha_(app_fbds)] + list(app_dem.values())), 3), round(max([ha_(app_fbds)] + list(app_dem.values())), 3)]}
        if med is not None:
            lineas_ens.append({'gleba': gl, 'arroio': ar.nome, 'tipo': 'mediana_ensamble', 'geometry': med})
        lineas_ens.append({'gleba': gl, 'arroio': ar.nome, 'tipo': 'fbds', 'geometry': curso})
        dd = disp[gl][ar.nome]
        log('  %s %-20s eje %4d pts | %s | entre-DEM med %s p90 %s m | mediana-ens vs FBDS med %s p90 %s m | APP30 FBDS %.3f ens %.3f env [%.3f; %.3f] ha'
            % (gl, ar.nome, len(pts), ' '.join('%s:%s/%s' % (k[:4], v['dist_mediana_m'], v['dist_p90_m']) for k, v in por_dem.items()),
               dd['dispersion_entre_dem_mediana_m'], dd['dispersion_entre_dem_p90_m'], dd['mediana_ensamble_vs_fbds_med_m'], dd['mediana_ensamble_vs_fbds_p90_m'],
               dd['app30_fbds_ha'], dd['app30_mediana_ensamble_ha'], *dd['app30_envolvente_ha']))
guardar_hp(gpd.GeoDataFrame(lineas_ens, geometry='geometry', crs=CRS_METRICO), 'hidro_ensamble_mediana_por_arroio')
RES['dem_ensamble'] = {'dems': {k: {'ruta': v, 'existe': os.path.exists(v)} for k, v in DEMS.items()},
                       'umbrales_probados_ha': UMBRALES, 'calibracion_por_dem': calib_all, 'dispersion_por_arroio': disp,
                       'metodo': 'pysheds fill_pits+fill_depressions+resolve_flats+D8; umbral = min(med FBDS->DEM + med DEM->FBDS) en PROP+500 m; '
                                 'correspondencia punto a punto cada 10 m del eje FBDS con dmax 150 m; mediana del ensamble = mediana por componente de los '
                                 'puntos mas cercanos de >=3 DEM'}
fuente('Copernicus/NASA/USGS/JAXA/Bristol via GEE', 'GLO30_2024_1, NASADEM_HGT/001, SRTMGL1_003, AW3D30 V4_1, FABDEM V1-2', '30 m (1 arc-sec)', '2000-2024',
       'GEE (IDs verificados con getInfo 2026-09-06)', 'si', 'ensamble de 5 DEM: red D8 con umbral calibrado y dispersion por arroio',
       'ver tabla por arroio (dispersion entre DEM y vs FBDS)')
fuente('INPE', 'TOPODATA (SRTM refinado 30 m)', '30 m', '2008', 'http://www.dsr.inpe.br/topodata/', 'no',
       'DNS no resuelve el 2026-09-06 (espejo webmapit 404); reemplazado por SRTMGL1 1 arc-sec real', 'n/a')
fuente('IAT-PR', 'curvas_de_nivel_1_50000_20m', '1:50.000 (eq. 20 m) / 1:25.000 (10 m)', gov_log.get('IAT_curvas_nivel_50k_20m', {}).get('fecha'),
       gov_log.get('IAT_curvas_nivel_50k_20m', {}).get('url'), 'si', '%d curvas en la zona (cotas %s-%s m): relieve oficial para contrastar el DEM'
       % (len(curvas), int(curvas.elevation.min()) if len(curvas) else '-', int(curvas.elevation.max()) if len(curvas) else '-'), 'ver seccion DEM vs curvas')
# curvas de nivel vs DEM: error vertical de cada DEM en los vertices de las curvas dentro de PROP+500
cv = {}
if len(curvas):
    pts_cv, z_cv = [], []
    for _, r in curvas.iterrows():
        for g in (r.geometry.geoms if hasattr(r.geometry, 'geoms') else [r.geometry]):
            gz = g.intersection(ZONA)
            for gg in (gz.geoms if hasattr(gz, 'geoms') else [gz]):
                if gg.is_empty or gg.geom_type != 'LineString':
                    continue
                for pp in puntos_a_lo_largo([gg], 30.0):
                    pts_cv.append(pp); z_cv.append(float(r.elevation))
    z_cv = np.array(z_cv)
    for nombre, ruta in DEMS.items():
        if not os.path.exists(ruta):
            continue
        zd = muestrear(ruta, 'DEM', pts_cv)
        e = zd - z_cv; e = e[np.isfinite(e)]
        cv[nombre] = {'n': int(e.size), 'sesgo_m': round(float(np.median(e)), 2), 'mad_m': round(float(np.median(np.abs(e - np.median(e)))), 2),
                      'rmse_m': round(float(np.sqrt(np.mean(e ** 2))), 2)}
        log('  DEM %-8s vs curvas IAT 1:50k: n=%d sesgo(mediana) %+.2f m  MAD %.2f m  RMSE %.2f m' % (nombre, e.size, cv[nombre]['sesgo_m'], cv[nombre]['mad_m'], cv[nombre]['rmse_m']))
RES['dem_ensamble']['dem_vs_curvas_iat_50k'] = cv

# ==============================================================================
titulo('3. Agua: serie temporal S2 + S1, JRC, MapBiomas; espejo de la represa por fuente')
# ==============================================================================
AG = descargar_frecuencias(p) if not all(os.path.exists(os.path.join(HP, f)) for f in ['agua_frecuencia_10m.tif', 'agua_s1_frecuencia_10m.tif', 'agua_jrc_mensual_30m.tif', 'agua_mapbiomas_30m.tif']) else None
R_S2 = os.path.join(HP, 'agua_frecuencia_10m.tif'); R_S1 = os.path.join(HP, 'agua_s1_frecuencia_10m.tif')
R_JRC = os.path.join(HP, 'agua_jrc_mensual_30m.tif'); R_MB = os.path.join(HP, 'agua_mapbiomas_30m.tif')
for ruta, rangos in [(R_S2, {'freq_total': (0, 1), 'freq_chuva': (0, 1), 'freq_seca': (0, 1), 'n_valid': (0, 400), 'ndmi_min_seca': (-1, 1),
                             'ndmi_p10_seca': (-1, 1), 'mndwi_max': (-1, 1), 'mndwi_p90': (-1, 1)}),
                     (R_S1, {'freq_16': (0, 1), 'freq_18': (0, 1), 'freq_20': (0, 1), 'freq_16_chuva': (0, 1), 'freq_16_seca': (0, 1),
                             'n_obs': (0, 100), 'vv_p10': (-35, 15), 'vv_p50': (-35, 15), 'vv_p90': (-35, 15)}),
                     (R_JRC, {'freq': (0, 1), 'n_valid': (0, 84), 'max_extent': (0, 1), 'occurrence': (0, 100)}),
                     (R_MB, {'freq_2020_2024': (0, 1), 'freq_1985_2024': (0, 1), 'agua_2024': (0, 1)})]:
    with rasterio.open(ruta) as ds:
        for i, d in enumerate(ds.descriptions, 1):
            a = ds.read(i).astype(np.float64)
            if ds.nodata is not None:
                a[a == ds.nodata] = np.nan
            verificar_rango('%s:%s' % (os.path.basename(ruta)[:14], d), a, *rangos.get(d, (None, None)))
if not os.path.exists(os.path.join(HP, 'serie_represa_s2.json')):
    serie_represa(p, ZONA_REPRESA)
s2s = leer_json(os.path.join(HP, 'serie_represa_s2.json')); s1s = leer_json(os.path.join(HP, 'serie_represa_s1.json'))
df2 = pd.DataFrame(s2s['filas']); df1 = pd.DataFrame(s1s['filas'])
zona_ha = s2s['zona_ha']
# S2: escenas utiles = >= 90% de la zona valida; por fecha (dos tiles) se toma la de mayor valido
df2 = df2[df2.valido_ha >= 0.9 * zona_ha].sort_values('valido_ha', ascending=False).drop_duplicates('fecha').sort_values('fecha')
df2['chuva'] = df2['chuva'].astype(int)
log('  S2 escenas con >=90%% de la zona de la represa (%.2f ha) validas: %d de %d' % (zona_ha, len(df2), len(s2s['filas'])))
def q(s):
    s = s.dropna()
    return {'n': int(s.size), 'min': round(float(s.min()), 3), 'p25': round(float(s.quantile(.25)), 3), 'mediana': round(float(s.median()), 3),
            'p75': round(float(s.quantile(.75)), 3), 'p90': round(float(s.quantile(.90)), 3), 'max': round(float(s.max()), 3)} if s.size else {'n': 0}
serie_s2 = {'todas': q(df2.agua_ha), 'chuva_out_mar': q(df2[df2.chuva == 1].agua_ha), 'seca_abr_set': q(df2[df2.chuva == 0].agua_ha),
            'por_mes': {str(k): round(float(v), 3) for k, v in df2.assign(m=df2.fecha.str[:7]).groupby('m').agua_ha.median().items()}}
for k in ['todas', 'chuva_out_mar', 'seca_abr_set']:
    log('  S2 espejo represa (%s): %s' % (k, serie_s2[k]))
df1 = df1.sort_values('fecha'); df1['chuva'] = df1['chuva'].astype(int)
serie_s1 = {u: {'todas': q(df1['agua%d_ha' % u]), 'chuva': q(df1[df1.chuva == 1]['agua%d_ha' % u]), 'seca': q(df1[df1.chuva == 0]['agua%d_ha' % u])} for u in (16, 18, 20)}
for u in (16, 18, 20):
    log('  S1 espejo represa (VV<-%d dB): todas %s | chuva med %s | seca med %s' % (u, serie_s1[u]['todas'], serie_s1[u]['chuva'].get('mediana'), serie_s1[u]['seca'].get('mediana')))
# Otsu local sobre VV p50 dentro de PROP+500 para decir cual umbral fijo se le acerca
from skimage.filters import threshold_otsu
with rasterio.open(R_S1) as ds:
    i50 = [k + 1 for k, d in enumerate(ds.descriptions) if d == 'vv_p50'][0]
    vv50 = ds.read(i50).astype(np.float64); vv50[vv50 == ds.nodata] = np.nan
    mz = rfeat.rasterize([(ZONA, 1)], out_shape=vv50.shape, transform=ds.transform, fill=0, dtype=np.uint8) > 0
    v = vv50[mz & np.isfinite(vv50)]
    otsu_vv = float(threshold_otsu(v)) if v.size > 100 else None
log('  Otsu sobre VV p50 (PROP+500 m): %s dB  (fraccion < Otsu: %.2f%%)' % (otsu_vv, 100 * float((v < otsu_vv).mean()) if otsu_vv else -1))
# areas por raster en la zona de la represa
esp = {}
esp['fbds_2013_ha'] = ha_(ESPELHO_FBDS)
esp['car_declarado_iat_ha'] = ha_(RES_CAR_GEOM.intersection(ZONA_REPRESA)); esp['car_declarado_geoserver_ha'] = ha_(RES_GEOS_GEOM.intersection(ZONA_REPRESA))
esp['car_declarado_total_incl_cabecera_ha'] = ha_(RES_CAR_GEOM.intersection(PROP))
esp['s2_freq_total_ge50_ha'], poly_s2_50 = area_umbral(R_S2, 'freq_total', ZONA_REPRESA, 0.5)
esp['s2_freq_chuva_ge50_ha'], poly_s2_c50 = area_umbral(R_S2, 'freq_chuva', ZONA_REPRESA, 0.5)
esp['s2_freq_seca_ge50_ha'], _ = area_umbral(R_S2, 'freq_seca', ZONA_REPRESA, 0.5)
esp['s2_freq_total_ge10_ha_extension_maxima'], poly_s2_10 = area_umbral(R_S2, 'freq_total', ZONA_REPRESA, 0.10)
esp['s2_freq_total_ge90_ha_nucleo_permanente'], poly_s2_90 = area_umbral(R_S2, 'freq_total', ZONA_REPRESA, 0.90)
esp['s2_serie_por_escena'] = serie_s2
esp['s1_freq16_ge50_ha'], poly_s1 = area_umbral(R_S1, 'freq_16', ZONA_REPRESA, 0.5)
esp['s1_freq18_ge50_ha'], _ = area_umbral(R_S1, 'freq_18', ZONA_REPRESA, 0.5)
esp['s1_freq20_ge50_ha'], _ = area_umbral(R_S1, 'freq_20', ZONA_REPRESA, 0.5)
esp['s1_serie_por_escena'] = serie_s1
esp['s1_otsu_vv_p50_db'] = round(otsu_vv, 2) if otsu_vv else None
esp['s1_otsu_nota'] = ('Otsu sobre VV p50 en PROP+500 m cae en %.1f dB con %.0f%% del area por debajo: separa cultivo/bosque, NO agua (el agua es <1%% del area y no forma modo). '
                       'Se usan umbrales fijos -16/-18/-20 dB; -18 dB es el mas cercano al espejo S2/MapBiomas.' % (otsu_vv, 100 * float((v < otsu_vv).mean()))) if otsu_vv else None
esp['jrc_max_extent_1984_2021_ha'], poly_jrc = area_umbral(R_JRC, 'max_extent', ZONA_REPRESA, 1)
esp['jrc_freq_mensual_2015_2021_ge50_ha'], _ = area_umbral(R_JRC, 'freq', ZONA_REPRESA, 0.5)
esp['jrc_occurrence_media_pct'] = round(estad_zona(R_JRC, 'occurrence', ESPELHO_FBDS)[0], 1)
esp['mapbiomas_agua_2024_ha'], poly_mb = area_umbral(R_MB, 'agua_2024', ZONA_REPRESA, 1)
esp['mapbiomas_freq_2020_2024_ge50_ha'], _ = area_umbral(R_MB, 'freq_2020_2024', ZONA_REPRESA, 0.5)
esp['mapbiomas_freq_1985_2024_ge50_ha'], _ = area_umbral(R_MB, 'freq_1985_2024', ZONA_REPRESA, 0.5)
esp['iat_massa_50k_paranacidade_ha'] = ha_(unary_union(list(massa50k.geometry)).intersection(ZONA_REPRESA)) if len(massa50k) else 0.0
esp['ana_massa_dagua_ha'] = ha_(unary_union(list(ana_massa.geometry)).intersection(ZONA_REPRESA)) if len(ana_massa) else 0.0
esp['iat_uso2012_wv2_corpos_dagua_ha'] = ha_(unary_union(list(uso2012[uso2012.nivel_ii.str.contains('gua', na=False)].geometry)).intersection(ZONA_REPRESA)) if len(uso2012) else 0.0
esp['uso2012_clases_en_zona_represa'] = {str(k): round(v, 3) for k, v in (uso2012.assign(a=uso2012.geometry.intersection(ZONA_REPRESA).area / 1e4).groupby('nivel_ii').a.sum().items() if len(uso2012) else [])}
for i, pt_ in enumerate(RES_CAR_PARTES):
    pt_['s2_freq_total_max'] = round(estad_zona(R_S2, 'freq_total', pt_['geom'], 'max')[0], 3)
    pt_['s2_freq_total_media'] = round(estad_zona(R_S2, 'freq_total', pt_['geom'], 'mean')[0], 3)
    pt_['s1_freq16_max'] = round(estad_zona(R_S1, 'freq_16', pt_['geom'], 'max')[0], 3)
    pt_['mndwi_max'] = round(estad_zona(R_S2, 'mndwi_max', pt_['geom'], 'max')[0], 3)
    pt_['con_agua_2024_2026'] = bool(pt_['s2_freq_total_max'] >= 0.25 or pt_['s1_freq16_max'] >= 0.5)
    pt_['dist_nascente_fbds_m'] = round(min(pt_['geom'].distance(g) for g in nasc.geometry), 1) if len(nasc) else None
    log('    reservatorio CAR parte %d: %.3f ha | S2 freq max %.2f media %.2f | S1 f16 max %.2f | MNDWI max %.2f | agua 2024-26: %s | nascente FBDS a %s m'
        % (i + 1, pt_['area_ha'], pt_['s2_freq_total_max'], pt_['s2_freq_total_media'], pt_['s1_freq16_max'], pt_['mndwi_max'], pt_['con_agua_2024_2026'], pt_['dist_nascente_fbds_m']))
esp['reservatorio_car_partes'] = [{k: v for k, v in pt_.items() if k != 'geom'} for pt_ in RES_CAR_PARTES]
esp['escena_2026_08_29_mndwi_ha'] = RG['G1']['lagoas']['espelho_mndwi_2026_ha']; esp['escena_2026_08_29_rf_ha'] = RG['G1']['lagoas']['espelho_rf_2026_ha']
for k, v in esp.items():
    if not isinstance(v, dict):
        log('  %-48s %s' % (k, v))
# referencia
ref_val = serie_s2['chuva_out_mar'].get('mediana')
ref_alt = esp['s2_freq_chuva_ge50_ha']
actuales = {'S2 mediana lluviosa': ref_val, 'S2 freq_total>=0.5': esp['s2_freq_total_ge50_ha'], 'S1 -16 dB mediana': serie_s1[16]['todas'].get('mediana'),
            'S1 -18 dB mediana': serie_s1[18]['todas'].get('mediana'), 'MapBiomas 2024': esp['mapbiomas_agua_2024_ha'], 'MapBiomas freq 2020-24>=0.5': esp['mapbiomas_freq_2020_2024_ge50_ha']}
actuales = {k: (round(float(v), 3) if v is not None else None) for k, v in actuales.items()}
act_v = [v for v in actuales.values() if v is not None]
espelho_ref = {'referencia_elegida': 'mediana del espejo S2 en estacion lluviosa (Oct-Mar) 2024-2026, escenas con >=90% de la zona valida',
               'valor_ha': ref_val, 'valor_raster_equivalente_ha': ref_alt,
               'rango_s2_2024_2026_ha': [serie_s2['todas'].get('min'), serie_s2['todas'].get('p90')],
               'espejo_actual_por_sensor_ha': actuales, 'envolvente_actual_ha': [round(min(act_v), 2), round(max(act_v), 2)],
               'historico_ha': {'FBDS 2013': esp['fbds_2013_ha'], 'IAT WV2 2012': esp['iat_uso2012_wv2_corpos_dagua_ha'], 'JRC max 1984-2021': esp['jrc_max_extent_1984_2021_ha'], 'CAR declarado': esp['car_declarado_iat_ha']},
               'mayor_o_igual_1ha': 'INDETERMINADO: el espejo ACTUAL (2024-26) va de %.2f (S2, 10 m, MNDWI>0) a %.2f ha (S1 -16 dB / MapBiomas) segun sensor y umbral; '
                                    'el historico (FBDS 2013 %.2f, WV2 2012 %.2f, JRC max %.2f, CAR %.2f) es >= 1 ha' % (min(act_v), max(act_v), esp['fbds_2013_ha'], esp['iat_uso2012_wv2_corpos_dagua_ha'], esp['jrc_max_extent_1984_2021_ha'], esp['car_declarado_iat_ha']),
               'nota': 'Lei 12.651 art. 4 III + par. 4: el reservatorio artificial decorrente de barramento de curso natural tiene APP en la faixa de la licencia y queda '
                       'DISPENSADO de esa faixa si el espejo es < 1 ha (vedada nova supressao). El espejo actual esta en la frontera de 1 ha: mientras no se mida en campo '
                       '(perimetro GNSS del espejo en estacion lluviosa o cota del vertedero), la lectura conservadora es la de las bases oficiales (FBDS/CAR >= 1 ha): '
                       'sin dispensa. Los 30 m del curso natural bajo el espejo (arroio 3) no dependen de esta cuestion.'}
log('  ESPEJO DE REFERENCIA: %s ha (%s); actual por sensor %s; >= 1 ha: %s' % (ref_val, espelho_ref['referencia_elegida'], actuales, espelho_ref['mayor_o_igual_1ha']))
# extension maxima (poligono) y frecuencia como GeoJSON
ext_rows = [{'fuente': 'S2 freq_total>=0.10 (extension maxima observada 2024-26)', 'area_ha': esp['s2_freq_total_ge10_ha_extension_maxima'], 'geometry': poly_s2_10},
            {'fuente': 'S2 freq_chuva>=0.50 (espejo tipico lluvioso)', 'area_ha': esp['s2_freq_chuva_ge50_ha'], 'geometry': poly_s2_c50},
            {'fuente': 'S2 freq_total>=0.90 (nucleo permanente)', 'area_ha': esp['s2_freq_total_ge90_ha_nucleo_permanente'], 'geometry': poly_s2_90},
            {'fuente': 'S1 VV<-16 dB freq>=0.50', 'area_ha': esp['s1_freq16_ge50_ha'], 'geometry': poly_s1},
            {'fuente': 'JRC max_extent 1984-2021', 'area_ha': esp['jrc_max_extent_1984_2021_ha'], 'geometry': poly_jrc},
            {'fuente': 'MapBiomas Agua 2024', 'area_ha': esp['mapbiomas_agua_2024_ha'], 'geometry': poly_mb},
            {'fuente': 'FBDS 2013', 'area_ha': esp['fbds_2013_ha'], 'geometry': ESPELHO_FBDS},
            {'fuente': 'CAR declarado (IAT)', 'area_ha': esp['car_declarado_iat_ha'], 'geometry': RES_CAR_GEOM.intersection(PROP)}]
guardar_hp(gpd.GeoDataFrame([r for r in ext_rows if not r['geometry'].is_empty], geometry='geometry', crs=CRS_METRICO), 'agua_extensao_maxima')
# otros cuerpos de agua persistentes dentro de la propiedad fuera de la represa
_, poly_otros = area_umbral(R_S2, 'freq_total', PROP.difference(ZONA_REPRESA), 0.5)
otros = [{'area_ha': ha_(g), 'geometry': g} for g in (poly_otros.geoms if hasattr(poly_otros, 'geoms') else [poly_otros]) if not g.is_empty and g.area >= 300]
log('  otros cuerpos con agua persistente (freq>=0.5, >=3 px) fuera de la represa: %d (%s ha)' % (len(otros), [o['area_ha'] for o in otros]))
RES['agua'] = {'series': AG or {'nota': 'rasters reutilizados de corrida previa (ver tags)'}, 'zona_represa_ha': round(zona_ha, 3), 'represa': esp,
               'espelho_referencia': espelho_ref, 'otros_cuerpos_persistentes_fuera_represa': [{'area_ha': o['area_ha']} for o in otros],
               'n_escenas_s2_total': len(s2s['filas']), 'n_escenas_s2_utiles_represa': int(len(df2)), 'n_escenas_s1': int(len(df1))}
fuente('ESA/Google via GEE', 'S2_SR_HARMONIZED + Cloud Score+ (%d escenas, %d utiles en la represa)' % (len(s2s['filas']), len(df2)), '10 m', '2024-09..2026-09',
       'GEE', 'si', 'frecuencia de agua por pixel, espejo por escena, NDMI seco', 'espejo represa mediana lluviosa %s ha vs FBDS %.2f / CAR %.2f' % (ref_val, esp['fbds_2013_ha'], esp['car_declarado_iat_ha']))
fuente('ESA via GEE', 'S1_GRD IW VV (%d escenas, orbita %s)' % (len(df1), sorted(set(df1.orbita.astype(int).astype(str))) if 'orbita' in df1 else 'ver json'), '10 m', '2024-09..2026-09', 'GEE', 'si',
       'frecuencia de agua a traves de nubes; Otsu %s dB' % esp['s1_otsu_vv_p50_db'], 'espejo S1(-16 dB) freq>=0.5: %.2f ha' % esp['s1_freq16_ge50_ha'])
fuente('JRC via GEE', 'GSW1_4 MonthlyHistory 2015-2021 + GlobalSurfaceWater', '30 m', '1984-2021', 'GEE', 'si', 'max_extent %.2f ha; freq mensual>=0.5 %.2f ha' % (esp['jrc_max_extent_1984_2021_ha'], esp['jrc_freq_mensual_2015_2021_ge50_ha']), 'GSW1_4 termina en 2021-12 (no cubre 2022-24)')
fuente('MapBiomas via GEE', 'Agua colecao 4 (water_v3) 1985-2024', '30 m', '2020-2024', 'GEE', 'si', 'agua 2024 %.2f ha; freq 2020-24>=0.5 %.2f ha' % (esp['mapbiomas_agua_2024_ha'], esp['mapbiomas_freq_2020_2024_ge50_ha']), 'vs FBDS %.2f ha' % esp['fbds_2013_ha'])
fuente('ANA/SNIRH', 'SPR/Massa_dagua, Armazena_Reservatorio_UGRH', '1:50k-1:250k', gov_log.get('ANA_massa_dagua', {}).get('fecha'), gov_log.get('ANA_massa_dagua', {}).get('url'), 'si',
       '%d masas ANA en zona; %.2f ha en la represa' % (len(ana_massa), esp['ana_massa_dagua_ha']), 'no registra la represa' if esp['ana_massa_dagua_ha'] == 0 else 'coincide')
fuente('IAT-PR / PARANACIDADE', 'hidro_50k_massa_dagua_prcidade', '1:50.000', gov_log.get('IAT_hidro50k_massa_dagua_paranacidade', {}).get('fecha'), gov_log.get('IAT_hidro50k_massa_dagua_paranacidade', {}).get('url'), 'si',
       '%.2f ha en la represa' % esp['iat_massa_50k_paranacidade_ha'], 'no registra la represa' if esp['iat_massa_50k_paranacidade_ha'] == 0 else 'coincide')
fuente('IAT-PR', 'map_uso_cobertura_terra_2012 (WorldView-2 2012-13)', '1:10.000 aprox.', gov_log.get('IAT_uso_cobertura_terra_2012_wv2', {}).get('fecha'), gov_log.get('IAT_uso_cobertura_terra_2012_wv2', {}).get('url'), 'si',
       "corpos d'agua %.2f ha en la represa; clases en zona %s" % (esp['iat_uso2012_wv2_corpos_dagua_ha'], esp['uso2012_clases_en_zona_represa']), 'vs FBDS %.2f ha' % esp['fbds_2013_ha'])
fuente('IAT-PR', 'outorgas_sigarh / out_captacao_crh / mananciais_2023', 'puntual', gov_log.get('IAT_outorgas_sigarh', {}).get('fecha'), gov_log.get('IAT_outorgas_sigarh', {}).get('url'), 'si',
       '%d outorgas SIGARH + %d CRH en PROP+500 m; %d en la propiedad' % (len(outorgas), len(outorgas_crh), int(outorgas.within(PROP).sum() + outorgas_crh.within(PROP).sum())), 'sin outorga para el barramento' if not (outorgas.within(PROP).any() or outorgas_crh.within(PROP).any()) else 'hay outorga en la propiedad')

# ==============================================================================
titulo('4. Nascentes: veredicto por candidato')
# ==============================================================================
HAND = os.path.join(ANALISIS, 'HAND_30m.tif')
otto_inicios = []
for _, r in otto.iterrows():
    g = r.geometry
    if g.geom_type == 'LineString' and (r.get('nustrahler') in (1, 1.0, '1') or pd.isna(r.get('nustrahler'))):
        otto_inicios.append(Point(g.coords[0]))
ana_inicios = [Point(r.geometry.coords[0]) for _, r in ana.iterrows() if r.geometry.geom_type == 'LineString']
car_hidro_prop = CAR_L['IAT_CAR_hidrografia']; car_hidro_prop = car_hidro_prop[car_hidro_prop.cod_imovel.isin([CAR_G1, CAR_G2])]
cand_rows = []
with rasterio.open(R_S2) as ds:
    b = {d: k + 1 for k, d in enumerate(ds.descriptions)}
    ndmi_p10 = ds.read(b['ndmi_p10_seca']).astype(np.float64); ndmi_p10[ndmi_p10 == ds.nodata] = np.nan
    prof_s2 = ds.profile
for _, c in nasc_cons.iterrows():
    pt = c.geometry
    if not pt.within(PROP.buffer(150)):
        continue
    ev = {}
    ev['fonte'] = c.fonte; ev['id'] = c.id_fonte; ev['dentro_propriedade'] = bool(pt.within(PROP))
    ev['gleba'] = next((gl for gl, gg in GLEBAS.items() if pt.within(gg)), None)
    ev['hand_m'] = None if not np.isfinite(muestrear(HAND, 'HAND', [pt])[0]) else round(float(muestrear(HAND, 'HAND', [pt])[0]), 1)
    ev['dist_nascente_fbds_m'] = round(float(min(pt.distance(g) for g in nasc.geometry)), 1) if len(nasc) else None
    ev['dist_curso_fbds_m'] = round(float(min(pt.distance(g) for g in fbds.geometry)), 1)
    ev['dist_inicio_trecho_otto2020_m'] = round(float(min(pt.distance(g) for g in otto_inicios)), 1) if otto_inicios else None
    ev['dist_inicio_trecho_ana5k_m'] = round(float(min(pt.distance(g) for g in ana_inicios)), 1) if ana_inicios else None
    ev['dist_hidro_car_propio_m'] = round(float(min(pt.distance(g) for g in car_hidro_prop.geometry)), 1) if len(car_hidro_prop) else None
    cab_d = {n: (round(float(min(pt.distance(q) for q in cc)), 1) if cc else None) for n, cc in cab_opt.items()}
    ev['dist_cabecera_por_dem_m'] = cab_d
    ev['n_dem_con_cabecera_a_100m'] = int(sum(1 for v in cab_d.values() if v is not None and v <= 100))
    ev['n_dem_con_cabecera_a_150m'] = int(sum(1 for v in cab_d.values() if v is not None and v <= 150))
    z30 = pt.buffer(30)
    ev['s2_freq_total_max_30m'] = round(estad_zona(R_S2, 'freq_total', z30, 'max')[0], 3)
    ev['s2_freq_chuva_max_30m'] = round(estad_zona(R_S2, 'freq_chuva', z30, 'max')[0], 3)
    ev['s1_freq16_max_30m'] = round(estad_zona(R_S1, 'freq_16', z30, 'max')[0], 3)
    ev['s1_freq20_max_30m'] = round(estad_zona(R_S1, 'freq_20', z30, 'max')[0], 3)
    ev['mndwi_max_30m'] = round(estad_zona(R_S2, 'mndwi_max', z30, 'max')[0], 3)
    ev['jrc_occurrence_max_30m'] = round(estad_zona(R_JRC, 'occurrence', z30, 'max')[0], 1)
    # NDMI p10 de la seca: punto (media 30 m) vs anillo 100-300 m (entorno del mismo lote) -> z robusto
    v_pt, _ = estad_zona(R_S2, 'ndmi_p10_seca', z30, 'mean')
    with rasterio.open(R_S2) as ds:
        anillo = pt.buffer(300).difference(pt.buffer(100)).intersection(PROP)
        m = rfeat.rasterize([(anillo, 1)], out_shape=ndmi_p10.shape, transform=ds.transform, fill=0, dtype=np.uint8) > 0
        va = ndmi_p10[m & np.isfinite(ndmi_p10)]
    med, mad = (float(np.median(va)), float(np.median(np.abs(va - np.median(va))) * 1.4826)) if va.size > 20 else (np.nan, np.nan)
    ev['ndmi_p10_seca_punto'] = round(v_pt, 3) if np.isfinite(v_pt) else None
    ev['ndmi_p10_seca_entorno_mediana'] = round(med, 3) if np.isfinite(med) else None
    ev['ndmi_p10_seca_z_robusto'] = round((v_pt - med) / mad, 2) if np.isfinite(v_pt) and np.isfinite(mad) and mad > 0 else None
    u12 = uso2012[uso2012.intersects(pt.buffer(15))]
    ev['uso_iat_2012_wv2'] = '; '.join(sorted(set(u12.nivel_ii.astype(str)))) if len(u12) else None
    # veredicto
    oficial = (ev['dist_nascente_fbds_m'] is not None and ev['dist_nascente_fbds_m'] <= 60) or \
              (ev['dist_inicio_trecho_otto2020_m'] is not None and ev['dist_inicio_trecho_otto2020_m'] <= 100)
    relieve = ev['n_dem_con_cabecera_a_100m'] >= 3
    humedad = (ev['s2_freq_chuva_max_30m'] >= 0.10) or (ev['s1_freq20_max_30m'] >= 0.20) or \
              (ev['ndmi_p10_seca_z_robusto'] is not None and ev['ndmi_p10_seca_z_robusto'] >= 1.5) or \
              (ev['uso_iat_2012_wv2'] is not None and ('rzea' in ev['uso_iat_2012_wv2'] or 'gua' in ev['uso_iat_2012_wv2']))
    hand_bajo = ev['hand_m'] is not None and ev['hand_m'] <= 2
    puntos = int(oficial) * 2 + int(relieve) + int(humedad) * 2 + int(hand_bajo)
    ev['ndmi_seco_mas_seco_que_entorno'] = bool(ev['ndmi_p10_seca_z_robusto'] is not None and ev['ndmi_p10_seca_z_robusto'] <= -1.0)
    ev['misma_cabecera_que_nascente_fbds'] = bool(c.fonte != 'FBDS' and ev['dist_nascente_fbds_m'] is not None and ev['dist_nascente_fbds_m'] <= 150 and ev['dist_curso_fbds_m'] <= 30)
    if oficial and (relieve or humedad):
        ver = 'probable'
        if ev['misma_cabecera_que_nascente_fbds']:
            ver = 'probable (misma cabecera que la nascente FBDS, no es una nascente adicional)'
    elif (not oficial) and (not humedad) and ev['ndmi_seco_mas_seco_que_entorno']:
        ver = 'poco probable (evidencia negativa: sin agua ni humedad, mas seco que el entorno en la seca)'
    elif (relieve and humedad):
        ver = 'probable'
    elif relieve or humedad or oficial:
        ver = 'sin evidencia concluyente'
    else:
        ver = 'poco probable'
    ev['evidencia'] = {'base_oficial_a_100m': oficial, 'relieve_>=3_dem_cabecera_100m': relieve, 'humedad_s2_s1_ndmi_uso2012': humedad, 'hand_<=2m': hand_bajo, 'puntaje_0_6': puntos}
    ev['veredicto'] = ver
    ev['geometry'] = pt
    cand_rows.append(ev)
    log('  %-22s %-6s dentro=%s HAND=%s | FBDS nasc %s m curso %s m | otto ini %s m | ANA ini %s m | CAR hidro %s m | DEM cab<=100m: %d/5 %s | S2 fchuva %.2f S1 f20 %.2f MNDWImax %.2f | NDMI z %s | uso2012 %s => %s'
        % (c.fonte, c.id_fonte, ev['dentro_propriedade'], ev['hand_m'], ev['dist_nascente_fbds_m'], ev['dist_curso_fbds_m'], ev['dist_inicio_trecho_otto2020_m'],
           ev['dist_inicio_trecho_ana5k_m'], ev['dist_hidro_car_propio_m'], ev['n_dem_con_cabecera_a_100m'], cab_d, ev['s2_freq_chuva_max_30m'], ev['s1_freq20_max_30m'],
           ev['mndwi_max_30m'], ev['ndmi_p10_seca_z_robusto'], ev['uso_iat_2012_wv2'], ver.upper()))
gc = gpd.GeoDataFrame(cand_rows, geometry='geometry', crs=CRS_METRICO)
gc['dist_cabecera_por_dem_m'] = gc['dist_cabecera_por_dem_m'].map(json.dumps); gc['evidencia'] = gc['evidencia'].map(json.dumps)
guardar_hp(gc, 'nascentes_veredicto')
RES['nascentes'] = {'candidatos': [{k: v for k, v in r.items() if k != 'geometry'} | {'x': r['geometry'].x, 'y': r['geometry'].y} for r in cand_rows],
                    'criterio': 'probable = base oficial (nascente FBDS<=60 m o inicio de trecho otto<=100 m) + (relieve: >=3 de 5 DEM con cabecera a <=100 m, o humedad: '
                                'S2 freq lluviosa>=0.10 / S1 VV<-20 freq>=0.20 / NDMI p10 seco z>=1.5 vs entorno 100-300 m / uso IAT 2012 varzea-agua); '
                                'probable tambien si relieve Y humedad sin base oficial; una sola linea = sin evidencia concluyente; ninguna = poco probable. '
                                'NINGUN veredicto sustituye la verificacion en campo en estacion seca (Lei 12.651 art. 3 XVII: perenidad).'}
fuente('IAT-PR', 'mananciais_2023_iat / Mananciais_Superficiais_IAT_2026', 'poligono de cuenca', gov_log.get('IAT_mananciais_2023', {}).get('fecha'), gov_log.get('IAT_mananciais_2023', {}).get('url'), 'si',
       'areas de manancial de abastecimento publico que contienen la propiedad', 'n/a (contexto)')
fuente('IAT-PR', 'fragmentos_florestais_prioritarios_iatpr', 'poligono (MapBiomas/IAT)', gov_log.get('IAT_fragmentos_florestais_prioritarios', {}).get('fecha'), gov_log.get('IAT_fragmentos_florestais_prioritarios', {}).get('url'), 'si',
       '%d fragmentos prioritarios tocan la propiedad' % len(frag_prio), 'coincide con el fragmento 2 (mata vecina) del an_02')
fuente('IAT-PR/FBDS', 'fbds_nascentes (re-descarga de control)', '1:25.000 (RapidEye 5 m, 2013)', gov_log.get('IAT_FBDS_nascentes_recheck', {}).get('fecha'),
       gov_log.get('IAT_FBDS_nascentes_recheck', {}).get('url'), 'si', '%d nascentes en bbox (identicas a la descarga previa: %s)' % (gov_log.get('IAT_FBDS_nascentes_recheck', {}).get('n', 0), gov_log.get('IAT_FBDS_nascentes_recheck', {}).get('n', 0) == 38),
       '1 nascente FBDS dentro de G1 (306158); ninguna en los candidatos DEM')

# ==============================================================================
titulo('5. Cursos: longitud y trazado por fuente dentro de cada gleba; ancho; perenidad (indicio)')
# ==============================================================================
def asignar_a_arroios(lineas_gdf, gl, nombre_fuente, dmax=100.0):
    """Recorta lineas a la gleba y las asigna al arroio FBDS mas cercano (mediana de distancia <= dmax)."""
    out = {ar.nome: {'km': 0.0, 'dist_med_m': [], 'nombres': set()} for _, ar in arroios[gl].iterrows()}
    out['sin_correspondencia'] = {'km': 0.0, 'dist_med_m': [], 'nombres': set()}
    gg = GLEBAS[gl]
    for _, r in lineas_gdf.iterrows():
        g = line_only(r.geometry.intersection(gg))
        if g.is_empty or g.length < 1:
            continue
        pts = puntos_a_lo_largo([g] if g.geom_type == 'LineString' else list(g.geoms), 10.0)
        best, bd = None, np.inf
        for _, ar in arroios[gl].iterrows():
            d = float(np.median([pp.distance(ar.geometry) for pp in pts]))
            if d < bd:
                best, bd = ar.nome, d
        key = best if bd <= dmax else 'sin_correspondencia'
        out[key]['km'] += g.length / 1e3
        out[key]['dist_med_m'].append(bd)
        for campo in ('noriocomp', 'NORIOCOMP', 'nome', 'nogenerico'):
            if campo in r and isinstance(r[campo], str) and r[campo].strip():
                out[key]['nombres'].add(r[campo].strip())
        if 'regime' in r and isinstance(r['regime'], str):
            out[key].setdefault('regime', set()).add(r['regime'])
    return {k: {'km': round(v['km'], 3), 'dist_med_m': (round(float(np.median(v['dist_med_m'])), 1) if v['dist_med_m'] else None), 'nombres': sorted(v['nombres']),
                'regime': sorted(v.get('regime', []))} for k, v in out.items()}


cursos = {}
for gl in GLEBAS:
    cursos[gl] = {}
    fuentes_l = {'otto_iat_2020': otto, 'ana_bho_5k_2017': ana, 'ibge_bc250_2025': ibge, 'enquadramento_iat': enq}
    por_fuente = {k: asignar_a_arroios(v, gl, k) for k, v in fuentes_l.items()}
    ens_l = gpd.GeoDataFrame([r for r in lineas_ens if r['gleba'] == gl and r['tipo'] == 'mediana_ensamble'], geometry='geometry', crs=CRS_METRICO)
    por_fuente['mediana_ensamble_5dem'] = asignar_a_arroios(ens_l, gl, 'ens') if len(ens_l) else {}
    # CAR hidrografia (poligonos): area y longitud aproximada = perimetro/2 (poligono delgado)
    ch = CAR_L['IAT_CAR_hidrografia']; ch = ch[ch.cod_tema == 'RIO_ATE_10']
    car_l = {}
    for _, ar in arroios[gl].iterrows():
        gg = ch.geometry.intersection(GLEBAS[gl])
        sel = [g for g in gg if not g.is_empty and g.distance(ar.geometry) < 60]
        if sel:
            u = poly_only(unary_union(sel).intersection(ar.geometry.buffer(60)))
            car_l[ar.nome] = {'area_ha': ha_(u), 'long_aprox_m': round(u.length / 2, 1), 'ancho_medio_m': round(2 * u.area / u.length, 1) if u.length else None, 'cod_imoveis': sorted(set(ch[ch.geometry.intersection(GLEBAS[gl]).distance(ar.geometry) < 60].cod_imovel))}
    for _, ar in arroios[gl].iterrows():
        n = ar.nome
        # ancho por agua persistente S2 (fuera de la represa): poligonos freq_total>=0.5 que tocan el eje
        _, pw = area_umbral(R_S2, 'freq_total', ar.geometry.buffer(40).difference(ZONA_REPRESA), 0.5)
        anchos = []
        for g in (pw.geoms if hasattr(pw, 'geoms') else [pw]):
            if not g.is_empty and g.intersects(ar.geometry.buffer(12)):
                anchos.append(round(2 * g.area / g.length, 1))
        eje15 = ar.geometry.buffer(15).difference(ZONA_REPRESA)
        peren = {'s2_freq_total_media': round(estad_zona(R_S2, 'freq_total', eje15)[0], 3), 's2_freq_chuva_media': round(estad_zona(R_S2, 'freq_chuva', eje15)[0], 3),
                 's2_freq_seca_media': round(estad_zona(R_S2, 'freq_seca', eje15)[0], 3), 's2_freq_total_max': round(estad_zona(R_S2, 'freq_total', eje15, 'max')[0], 3),
                 's1_freq16_media': round(estad_zona(R_S1, 'freq_16', eje15)[0], 3), 's1_freq20_media': round(estad_zona(R_S1, 'freq_20', eje15)[0], 3),
                 's1_freq16_chuva_media': round(estad_zona(R_S1, 'freq_16_chuva', eje15)[0], 3), 's1_freq16_seca_media': round(estad_zona(R_S1, 'freq_16_seca', eje15)[0], 3),
                 'jrc_occurrence_media': round(estad_zona(R_JRC, 'occurrence', eje15)[0], 1),
                 'ndmi_p10_seca_eje_media': round(estad_zona(R_S2, 'ndmi_p10_seca', eje15)[0], 3),
                 'ndmi_p10_seca_entorno_100_300m': round(estad_zona(R_S2, 'ndmi_p10_seca', ar.geometry.buffer(300).difference(ar.geometry.buffer(100)).intersection(PROP))[0], 3)}
        ibge_reg = por_fuente['ibge_bc250_2025'].get(n, {})
        ibge_sel = ibge[ibge.geometry.intersection(GLEBAS[gl]).distance(ar.geometry) < 100] if len(ibge) else ibge
        cursos[gl][n] = {'fbds_ids': ar.fbds_ids, 'long_fbds_m': round(float(ar.comprimento_dentro_m), 1), 'long_por_fuente_en_gleba': {k: v.get(n, {'km': 0.0}) for k, v in por_fuente.items()},
                         'car_hidrografia_rio_ate10': car_l.get(n), 'nombre_oficial_otto': por_fuente['otto_iat_2020'].get(n, {}).get('nombres') or por_fuente['enquadramento_iat'].get(n, {}).get('nombres'),
                         'regime_ibge': por_fuente['ibge_bc250_2025'].get(n, {}).get('regime', []), 'largura_media_ibge': sorted(set(ibge_sel.larguramedia.dropna().astype(str))) if len(ibge_sel) and 'larguramedia' in ibge_sel else [],
                         'clase_ancho': {'fbds': 'ate 10 m', 'car': 'RIO_ATE_10' if car_l.get(n) else None, 's2_ancho_agua_persistente_m': anchos, 'algun_tramo_mas_de_10m': bool(any(a > 10 for a in anchos))},
                         'perenidad_indicio': peren, 'dispersion_dem': disp[gl].get(n)}
        tot = cursos[gl][n]
        log('  %s %-20s FBDS %6.1f m | otto %.3f km | ANA %.3f km | IBGE %.3f km (%s) | enq %.3f km | ens %.3f km | CAR %s | ancho S2 %s | S2 f seca %.2f chuva %.2f, S1 f16 %.2f, JRC occ %.1f, NDMI eje %.3f vs entorno %.3f'
            % (gl, n, tot['long_fbds_m'], tot['long_por_fuente_en_gleba']['otto_iat_2020']['km'], tot['long_por_fuente_en_gleba']['ana_bho_5k_2017']['km'],
               tot['long_por_fuente_en_gleba']['ibge_bc250_2025']['km'], tot['regime_ibge'], tot['long_por_fuente_en_gleba']['enquadramento_iat']['km'],
               tot['long_por_fuente_en_gleba'].get('mediana_ensamble_5dem', {}).get('km', 0), (car_l.get(n) or {}).get('long_aprox_m'), anchos,
               peren['s2_freq_seca_media'], peren['s2_freq_chuva_media'], peren['s1_freq16_media'], peren['jrc_occurrence_media'], peren['ndmi_p10_seca_eje_media'], peren['ndmi_p10_seca_entorno_100_300m']))
    sc = {k: v.get('sin_correspondencia', {}) for k, v in por_fuente.items()}
    cursos[gl]['_sin_correspondencia'] = sc
    for k, v in sc.items():
        if v and v.get('km', 0) > 0.02:
            log('  %s %s: %.3f km dentro de la gleba SIN arroio FBDS a < 100 m (%s)' % (gl, k, v['km'], v.get('nombres')))
RES['cursos'] = cursos
log_iat = leer_json(os.path.join(DATOS_EXT, '_download_log_iat.json')); log_ana = leer_json(os.path.join(DATOS_EXT, '_download_log_ana_ibge_pr.json'))
URLS_PREV = {'otto_iat_2020': log_iat.get('IAT_otto_trecho_drenagem_2020', {}).get('url'), 'ana_bho_5k_2017': log_ana.get('ANA_BHO2017_5k_trecho_drenagem', {}).get('url'),
             'ibge_bc250_2025': log_ana.get('IBGE_BC250_trecho_drenagem', {}).get('url'), 'enquadramento_iat': gov_log.get('IAT_enquadramento_hidrografia_otto', {}).get('url')}
for k, cap, esc in [('otto_iat_2020', 'rede_otto_trech_drena_2020_iat', '1:50.000'), ('ana_bho_5k_2017', 'BHO2017_5K_TRECHODRENAGEM', '1:5k (cuencas >=5 km2)'),
                    ('ibge_bc250_2025', 'BC250_2025_hid_trecho_drenagem_l', '1:250.000'), ('enquadramento_iat', 'enquadramento_base_hidrografica', '1:50.000 (otto)')]:
    kmG1 = sum(v['long_por_fuente_en_gleba'][k]['km'] for n, v in cursos['G1'].items() if not n.startswith('_'))
    dmed = [v['long_por_fuente_en_gleba'][k].get('dist_med_m') for n, v in cursos['G1'].items() if not n.startswith('_') and v['long_por_fuente_en_gleba'][k].get('dist_med_m') is not None]
    fuente({'otto_iat_2020': 'IAT-PR', 'ana_bho_5k_2017': 'ANA/SNIRH', 'ibge_bc250_2025': 'IBGE', 'enquadramento_iat': 'IAT-PR / CBH'}[k], cap, esc,
           '2026-09-06', URLS_PREV.get(k) or 'ver datos_externos/_download_log_*.json', 'si',
           'trazado/longitud de cursos en G1: %.3f km asignados a arroios FBDS' % kmG1,
           'vs FBDS %.3f km en G1; desplazamiento mediano respecto del eje FBDS %s m por arroio' % (RG['G1']['arroios']['km_dentro'], dmed))

# ==============================================================================
titulo('6. APP recomputada: mejor referencia + envolvente por gleba')
# ==============================================================================
app_res = {}
nasc_in = nasc[nasc.within(PROP)]
for gl, gg in GLEBAS.items():
    d = disp[gl]
    app_fbds = sum(v['app30_fbds_ha'] for v in d.values())
    app_ens = sum(v['app30_mediana_ensamble_ha'] for v in d.values())
    # union real (los buffers de arroios se solapan en confluencias): recomputar con union
    cursos_fbds = [r['geometry'] for r in lineas_ens if r['gleba'] == gl and r['tipo'] == 'fbds']
    cursos_ens = [r['geometry'] for r in lineas_ens if r['gleba'] == gl and r['tipo'] == 'mediana_ensamble']
    circ = unary_union([n.buffer(P['app_nascente_m']) for n in nasc_in.geometry]) if len(nasc_in) else shapely.Polygon()
    u_fbds = poly_only(unary_union([unary_union(cursos_fbds).buffer(P['app_curso_m']), circ]).intersection(gg))
    u_ens = poly_only(unary_union([unary_union(cursos_ens).buffer(P['app_curso_m']), circ]).intersection(gg)) if cursos_ens else shapely.Polygon()
    env_min = min([ha_(u_fbds)] + [sum(v['app30_por_dem_ha'].get(k, v['app30_fbds_ha']) for v in d.values()) + ha_(circ.intersection(gg)) for k in redes_opt])
    env_max = max([ha_(u_fbds)] + [sum(v['app30_por_dem_ha'].get(k, v['app30_fbds_ha']) for v in d.values()) + ha_(circ.intersection(gg)) for k in redes_opt])
    app_res[gl] = {'app_vigente_json_ha': RG[gl]['app']['exigida_ha'], 'app_fbds_recalculada_ha': ha_(u_fbds), 'app_mediana_ensamble_ha': ha_(u_ens),
                   'dif_simetrica_fbds_vs_ensamble_ha': ha_(u_fbds.symmetric_difference(u_ens)) if not u_ens.is_empty else None,
                   'envolvente_min_max_ha': [round(env_min, 2), round(env_max, 2)],
                   'app_car_declarada_en_gleba_ha': comp_car[gl]['app_car_geom_en_gleba_ha'],
                   'nascente_circulo_50m_en_gleba_ha': ha_(circ.intersection(gg))}
    log('  %s APP: vigente %.2f | FBDS recalculada %.2f | mediana ensamble %.2f | envolvente [%.2f; %.2f] | CAR declarada %.2f ha'
        % (gl, RG[gl]['app']['exigida_ha'], ha_(u_fbds), ha_(u_ens), env_min, env_max, comp_car[gl]['app_car_geom_en_gleba_ha']))
    guardar_hp(gpd.GeoDataFrame([{'gleba': gl, 'base': 'FBDS', 'area_ha': ha_(u_fbds), 'geometry': u_fbds}] + ([{'gleba': gl, 'base': 'mediana_ensamble_5dem', 'area_ha': ha_(u_ens), 'geometry': u_ens}] if not u_ens.is_empty else []),
                                geometry='geometry', crs=CRS_METRICO), 'app_%s_fbds_vs_ensamble' % gl)
# eleccion de la referencia
peor_p90 = max((v['mediana_ensamble_vs_fbds_p90_m'] or 0) for gl in disp for v in disp[gl].values())
mejor_med = np.median([v['mediana_ensamble_vs_fbds_med_m'] for gl in disp for v in disp[gl].values() if v['mediana_ensamble_vs_fbds_med_m'] is not None])
mejor_dem = min(((n, np.median([v['por_dem'][n]['dist_mediana_m'] for gl in disp for v in disp[gl].values() if v['por_dem'][n]['dist_mediana_m'] is not None])) for n in redes_opt), key=lambda x: x[1])
RES['app'] = {'por_gleba': app_res,
              'referencia_recomendada': 'FBDS/IAT (RapidEye 5 m, 1:25.000)',
              'justificacion': 'La mediana del ensamble de 5 DEM de 30 m queda a %.0f m (mediana) / %.0f m (p90) del eje FBDS: la dispersion es del orden del pixel del DEM y '
                               'menor que la incertidumbre que el propio buffer de 30 m absorbe; ningun DEM global mejora a una base trazada sobre imagen de 5 m, y el IAT publica FBDS '
                               'como su capa institucional de APP hidrica. El ensamble sirve para la ENVOLVENTE de incertidumbre, no para reemplazar el eje. DEM mas cercano a FBDS: %s (%.0f m).'
                               % (mejor_med, peor_p90, mejor_dem[0], mejor_dem[1]),
              'envolvente_regla': 'min/max de APP (30 m del eje + circulo 50 m de nascente FBDS) sobre FBDS y sobre la linea emparejada de cada DEM'}

# ==============================================================================
titulo('6b. Contexto regulatorio de gobierno: outorga del barramento, mananciais, fragmentos prioritarios')
# ==============================================================================
ctx = {}
o_in = outorgas[outorgas.within(PROP)]
ctx['outorgas_en_propiedad'] = []
for _, r in o_in.iterrows():
    d = {k: (str(r[k]) if r[k] is not None and not (isinstance(r[k], float) and np.isnan(r[k])) else None) for k in
         ['nm_empreendimento', 'nm_tipo_interferencia', 'cod_tipo_interferencia', 'nr_portaria', 'st_portaria', 'nm_tipo_documento', 'nm_tipo_solicitacao',
          'desc_finalidades', 'nm_tipo_corpo_hidrico', 'nm_corpo_hidrico_complemento', 'nm_bacia_hidrografica', 'nm_comite', 'cod_otto', 'nr_e_protocolo', 'nm_requerente']
         if k in r}
    for k in ('dt_publicacao', 'dt_vencimento'):
        if k in r and r[k] is not None and np.isfinite(float(r[k])):
            d[k] = time.strftime('%Y-%m-%d', time.gmtime(float(r[k]) / 1000))
    d['x'] = round(r.geometry.x, 1); d['y'] = round(r.geometry.y, 1)
    d['dist_espelho_fbds_m'] = round(r.geometry.distance(ESPELHO_FBDS), 1)
    d['dist_arroio_mas_cercano_m'] = round(min(r.geometry.distance(a.geometry) for gl in arroios for _, a in arroios[gl].iterrows()), 1)
    d['vencida'] = bool(d.get('dt_vencimento') and d['dt_vencimento'] < time.strftime('%Y-%m-%d'))
    ctx['outorgas_en_propiedad'].append(d)
    log('  OUTORGA en la propiedad: %s | %s | portaria %s | status %s | %s | %s | corpo %s %s | publ. %s venc. %s (vencida=%s) | a %.0f m del espejo FBDS'
        % (d.get('nm_empreendimento'), d.get('nm_tipo_interferencia'), d.get('nr_portaria'), d.get('st_portaria'), d.get('nm_tipo_documento'), d.get('desc_finalidades'),
           d.get('nm_tipo_corpo_hidrico'), d.get('nm_corpo_hidrico_complemento'), d.get('dt_publicacao'), d.get('dt_vencimento'), d['vencida'], d['dist_espelho_fbds_m']))
ctx['mananciais_abastecimento'] = []
for nombre_c, g in (('IAT mananciais 2023', mananciais), ('IAT mananciais superficiais 2026', mananciais26)):
    for _, r in g.iterrows():
        inter = r.geometry.intersection(PROP).area / 1e4
        if inter < 0.01:
            continue
        d = {'capa': nombre_c, 'nome': r.get('nome') or r.get('manancial'), 'tipo': r.get('tipo'), 'impeditivo': r.get('impeditivo'), 'portaria': r.get('portaria'),
             'status_outorga': r.get('status_outorga'), 'municipio_abastecido': r.get('municipio_abastec'), 'icms': r.get('icms'), 'area_km2': r.get('area_km2'),
             'pct_propiedad_dentro': round(100 * inter / (PROP.area / 1e4), 1)}
        ctx['mananciais_abastecimento'].append({k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in d.items()})
        log('  MANANCIAL %s: "%s" tipo=%s impeditivo=%s portaria=%s abastece=%s -> %.1f%% de la propiedad dentro' % (nombre_c, d['nome'], d['tipo'], d['impeditivo'], d['portaria'], d['municipio_abastecido'], d['pct_propiedad_dentro']))
ctx['fragmentos_prioritarios_iat'] = []
for _, r in frag_prio.iterrows():
    inter = r.geometry.intersection(PROP).area / 1e4
    if inter < 0.01:
        continue
    d = {'fragmento': str(r.get('fragmento')), 'area_total_ha': round(float(r.get('area_ha') or 0), 2), 'idade_anos': r.get('idade'), 'classe': r.get('classe'),
         'prioridade': r.get('prioridade'), 'classe_tamanho': r.get('classe_tamanho'), 'fito': r.get('fito'), 'dentro_propriedade_ha': round(inter, 3)}
    ctx['fragmentos_prioritarios_iat'].append({k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in d.items()})
    log('  FRAGMENTO PRIORITARIO IAT %s: %.1f ha total, idade %s, prioridade %s, %.2f ha dentro de la propiedad' % (d['fragmento'], d['area_total_ha'], d['idade_anos'], d['prioridade'], inter))
RES['contexto_regulatorio'] = ctx

# ==============================================================================
titulo('7. Salidas: JSON + COMPARACION_FUENTES_GOBIERNO.md')
# ==============================================================================
RES['fuentes'] = FUENTES
RES['_meta']['segundos'] = round(time.time() - T0, 1)
RES['_meta']['tls'] = 'verify=certifi (bundle por defecto) para *.pr.gov.br: la cadena valido el 2026-09-06 sin CA extra; car.gov.br con SECLEVEL=1 (cifrados legacy, certificado verificado); nunca verify=False'
guardar_json(JSON_OUT, _limpio(RES))
log('  -> %s' % JSON_OUT)


def md_tabla(cols, filas):
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for f in filas:
        out.append('| ' + ' | '.join(str(x).replace('|', '/') for x in f) + ' |')
    return '\n'.join(out)


md = []
md.append('# COMPARACION FUENTES DE GOBIERNO — Hidrologia PRO, Fazenda Santo Antonio (G1 %.2f ha + G2 %.2f ha)\n' % (GLEBAS['G1'].area / 1e4, GLEBAS['G2'].area / 1e4))
md.append('Generado por `an_11_hidrologia_pro.py` el %s. CRS EPSG:31982. Solo cuenta lo que cae DENTRO de las glebas; lo exterior se uso para derivar (cuencas, correspondencia).\n' % RES['_meta']['generado'])
md.append('JSON de cifras: `02_ANALISIS/hidrologia_pro/resultados_hidrologia_pro.json`. Capas nuevas de gobierno: `datos_externos/gov_pro/` (log `_download_log_gov_pro.json`).\n')
md.append('\n## 1. Tabla fuente por fuente\n')
md.append(md_tabla(['Institucion', 'Capa', 'Escala', 'Fecha', 'URL', 'Respondio', 'Que aporta', 'Discrepancia con nuestro resultado'],
                   [[f['institucion'], f['capa'], f['escala'], f['fecha'], f['url'], f['respondio'], f['aporta'], f['discrepancia']] for f in FUENTES]))
md.append('\n\nNo respondieron / no usables: INPE TOPODATA (DNS), SICAR directo (reCAPTCHA; no se salto), IAT `pbnp_*` Norte Pioneiro (exige token), Sudersha 1:20.000 (0 feats en el bbox: solo litoral/RMC), BDGEx vectorial (login).\n')
md.append('\n## 2. CAR del inmueble: existe, y es el "vecino" que declaraba la represa\n')
md.append('El poligono `%s` cubre el %.1f%% de G1 (%.2f de %.2f ha) y coincide con la parcela SIGEF/INCRA "%s" (%.2f ha, matricula %s, %s). '
          'Es el CAR del propio inmueble (status %s, condicao "%s"), no de un vecino. G2 (los 6 alqueires) esta dentro del CAR `%s` (%.2f ha declaradas, condicao "%s"), '
          'que a su vez coincide con la parcela SIGEF "%s" (%.2f ha, matricula %s): G2 es parte de un inmueble mayor ya certificado.\n'
          % (CAR_G1, cobert['G1']['pct_gleba_cubierta'], cobert['G1']['cubierta_por_su_car_ha'], cobert['G1']['gleba_ha'],
             sg_sel.iloc[0].nome_area if len(sg_sel) else '-', sg_sel.iloc[0].area_ha if len(sg_sel) else 0, sg_sel.iloc[0].registro_m if len(sg_sel) else '-', sg_sel.iloc[0].status if len(sg_sel) else '-',
             im_sel.iloc[0].ind_status, im_sel.iloc[0].des_condic, CAR_G2, float(im[im.cod_imovel == CAR_G2].num_area.iloc[0]) if CAR_G2 else 0,
             im[im.cod_imovel == CAR_G2].des_condic.iloc[0] if CAR_G2 else '-',
             sg_sel.iloc[1].nome_area if len(sg_sel) > 1 else '-', sg_sel.iloc[1].area_ha if len(sg_sel) > 1 else 0, sg_sel.iloc[1].registro_m if len(sg_sel) > 1 else '-'))
filas = []
for gl in GLEBAS:
    c = comp_car[gl]
    filas += [[gl, 'Area do imovel' + (' (CAR mayor que la gleba: G2 es parte de el)' if gl == 'G2' else ''), c['area_imovel_decl_ha'], c['area_gleba_medida_ha'], round((c['area_imovel_decl_ha'] or 0) - c['area_gleba_medida_ha'], 2)],
              [gl, 'APP (geometria CAR en la gleba / num_area)', '%.2f / %.2f' % (c['app_car_geom_en_gleba_ha'], c['app_car_num_area_decl_ha']), '%.2f (30 m) / %.2f (cenario FBDS)' % (c['app_medida_ha'], c['app_medida_cenario_fbds_ha']), round(c['app_car_geom_en_gleba_ha'] - c['app_medida_ha'], 2)],
              [gl, 'Reserva Legal (%s)' % (next(iter(k for k in car_decl.get(c['cod_imovel'], {}) if k == 'reserva_legal'), '-')), '%.2f en gleba / %.2f decl.' % (c['rl_car_geom_en_gleba_ha'], c['rl_car_num_area_decl_ha']), 'exigida 20%%: %.2f; remanescente fuera APP: %s' % (c['rl_exigida_20pct_ha'], c['rl_existente_medida_ha']), round(c['rl_car_geom_en_gleba_ha'] - c['rl_exigida_20pct_ha'], 2)],
              [gl, 'Vegetacao nativa / remanescente', '%.2f en gleba / %.2f decl.' % (c['veg_nativa_car_en_gleba_ha'], c['veg_nativa_car_decl_ha']), c['floresta_nativa_medida_ha'], round(c['veg_nativa_car_en_gleba_ha'] - (c['floresta_nativa_medida_ha'] or 0), 2)],
              [gl, 'Area consolidada', c['area_consolidada_car_en_gleba_ha'], '-', '-'],
              [gl, 'Hidrografia rio ate 10 m (poligono CAR, ha)', c['hidro_car_rio_ate10_en_gleba_ha'], '%.3f km FBDS' % c['hidro_medida_fbds_km'], '-'],
              [gl, 'Reservatorio artificial (ha)', c['hidro_car_reservatorio_en_gleba_ha'], ('FBDS %.2f / S2 ref %s' % (c['reservatorio_medido_fbds_ha'], ref_val)) if gl == 'G1' else '-', round(c['hidro_car_reservatorio_en_gleba_ha'] - c['reservatorio_medido_fbds_ha'], 2)]]
md.append(md_tabla(['Gleba', 'Tema', 'Declarado en CAR (ha)', 'Medido por nosotros (ha)', 'Dif. CAR - medido'], filas))
md.append('\n\nNotas: (a) los CAR se solapan entre si dentro de la propiedad (%s); (b) la replica IAT del CAR no publica nascentes (temas de hidrografia en el bbox: %s); '
          '(c) el reservatorio declarado en el CAR propio mide %.3f ha (IAT) / %.3f ha (WFS geoserver), contra %.2f ha FBDS 2013.\n'
          % ('; '.join('%s-%s %.2f ha' % (s['a'][-8:], s['b'][-8:], s['solape_en_prop_ha']) for s in solapes) or 'ninguno', RES['car']['nascentes_declaradas'].split('son ')[-1], ha_(RES_CAR_GEOM), ha_(RES_GEOS_GEOM), ha_(ESPELHO_FBDS)))
md.append('\n## 3. Ensamble de 5 DEM vs FBDS: dispersion posicional del lecho\n')
md.append(md_tabla(['DEM', 'Umbral (ha)', 'Red en PROP+500 (km)', 'FBDS->DEM med/p90 (m)', 'DEM->FBDS med/p90 (m)', 'vs curvas IAT 1:50k sesgo/MAD/RMSE (m)'],
                   [[n, c['umbral_elegido_ha'], c['calibracion'][str(c['umbral_elegido_ha'])]['km_dem'],
                     '%s / %s' % (c['calibracion'][str(c['umbral_elegido_ha'])]['fbds_a_dem_med_m'], c['calibracion'][str(c['umbral_elegido_ha'])]['fbds_a_dem_p90_m']),
                     '%s / %s' % (c['calibracion'][str(c['umbral_elegido_ha'])]['dem_a_fbds_med_m'], c['calibracion'][str(c['umbral_elegido_ha'])]['dem_a_fbds_p90_m']),
                     '%s / %s / %s' % (cv.get(n, {}).get('sesgo_m'), cv.get(n, {}).get('mad_m'), cv.get(n, {}).get('rmse_m'))] for n, c in calib_all.items()]))
md.append('\n\n### Por arroio (dentro de cada gleba + 60 m)\n')
filas = []
for gl in disp:
    for n, v in disp[gl].items():
        filas.append([gl, n, v['long_fbds_en_gleba_m'], ' '.join('%s %s/%s' % (k, w['dist_mediana_m'], w['dist_p90_m']) for k, w in v['por_dem'].items()),
                      '%s / %s' % (v['dispersion_entre_dem_mediana_m'], v['dispersion_entre_dem_p90_m']), '%s / %s' % (v['mediana_ensamble_vs_fbds_med_m'], v['mediana_ensamble_vs_fbds_p90_m']),
                      v['app30_fbds_ha'], v['app30_mediana_ensamble_ha'], '[%s; %s]' % tuple(v['app30_envolvente_ha']), v['app30_dif_simetrica_fbds_vs_ensamble_ha']])
md.append(md_tabla(['Gleba', 'Arroio', 'Long. FBDS en gleba (m)', 'Dist. FBDS->cada DEM med/p90 (m)', 'Dispersion ENTRE DEM med/p90 (m)', 'Mediana ensamble vs FBDS med/p90 (m)', 'APP30 FBDS (ha)', 'APP30 ensamble (ha)', 'Envolvente APP30 (ha)', 'Dif. simetrica (ha)'], filas))
md.append('\n\n## 4. Represa: espejo por fuente y referencia\n')
filas = [[k, v] for k, v in esp.items() if not isinstance(v, (dict, list))]
md.append(md_tabla(['Fuente / metrica', 'ha'], filas))
md.append('\n\nSerie S2 por escena (zona de la represa %.2f ha; %d escenas utiles de %d): todas %s; lluviosa %s; seca %s.\n' % (zona_ha, len(df2), len(s2s['filas']), serie_s2['todas'], serie_s2['chuva_out_mar'], serie_s2['seca_abr_set']))
md.append('Serie S1 (VV<-16 dB): todas %s; lluviosa med %s; seca med %s. Otsu local sobre VV p50: %s dB.\n' % (serie_s1[16]['todas'], serie_s1[16]['chuva'].get('mediana'), serie_s1[16]['seca'].get('mediana'), esp['s1_otsu_vv_p50_db']))
md.append('**Espejo de referencia: %s ha** (%s). Espejo actual por sensor: %s -> envolvente [%s; %s] ha. >= 1 ha: **%s**. %s\n' % (ref_val, espelho_ref['referencia_elegida'], espelho_ref['espejo_actual_por_sensor_ha'], espelho_ref['envolvente_actual_ha'][0], espelho_ref['envolvente_actual_ha'][1], espelho_ref['mayor_o_igual_1ha'], espelho_ref['nota']))
md.append('\n## 5. Nascentes: veredicto por candidato\n')
md.append(md_tabla(['Candidato', 'Gleba', 'HAND (m)', 'Nasc. FBDS (m)', 'Inicio otto (m)', 'Inicio ANA (m)', 'DEM con cabecera <=100 m', 'S2 freq lluviosa max', 'S1 f(-20dB) max', 'NDMI seco z', 'Uso IAT 2012', 'Veredicto'],
                   [[r['fonte'] + ' ' + str(r['id']), r['gleba'], r['hand_m'], r['dist_nascente_fbds_m'], r['dist_inicio_trecho_otto2020_m'], r['dist_inicio_trecho_ana5k_m'],
                     '%d/5' % r['n_dem_con_cabecera_a_100m'], r['s2_freq_chuva_max_30m'], r['s1_freq20_max_30m'], r['ndmi_p10_seca_z_robusto'], r['uso_iat_2012_wv2'], r['veredicto'].upper()] for r in cand_rows]))
partes_cab = [pt_ for pt_ in RES_CAR_PARTES if pt_['dist_espelho_fbds_m'] > 100]
if partes_cab:
    md.append('\n\n**Dato nuevo del CAR propio:** ademas de la represa, declara un segundo `RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO` de %s ha en la cabecera del Arroio 2 (a %s m de la nascente FBDS 306158 y %s m de dem_1), '
              'SIN agua detectable en 2024-26 (S2 freq max %s, S1 f16 max %s, MNDWI max %s): coherente con un acude en la nascente hoy seco, colmatado o bajo vegetacion. Es un punto obligatorio de la visita de campo: '
              'si existe barramento sobre la nascente, la APP es el radio de 50 m de la nascente (art. 4 IV) y el barramento requiere outorga/regularizacion.\n'
              % (partes_cab[0]['area_ha'], partes_cab[0]['dist_nascente_fbds_m'], round(next((r['dist_hidro_car_propio_m'] for r in cand_rows if r['id'] == 'dem_1'), 0)), partes_cab[0]['s2_freq_total_max'], partes_cab[0]['s1_freq16_max'], partes_cab[0]['mndwi_max']))
md.append('\n\nCriterio: %s\n' % RES['nascentes']['criterio'])
md.append('\n## 6. Cursos por fuente dentro de cada gleba\n')
filas = []
for gl in cursos:
    for n, v in cursos[gl].items():
        if n.startswith('_'):
            continue
        lp = v['long_por_fuente_en_gleba']
        filas.append([gl, n, v['long_fbds_m'], round(lp['otto_iat_2020']['km'] * 1e3), round(lp['ana_bho_5k_2017']['km'] * 1e3), round(lp['ibge_bc250_2025']['km'] * 1e3), round(lp.get('mediana_ensamble_5dem', {}).get('km', 0) * 1e3),
                      (v['car_hidrografia_rio_ate10'] or {}).get('long_aprox_m'), v['nombre_oficial_otto'], v['regime_ibge'], v['clase_ancho']['s2_ancho_agua_persistente_m'],
                      '%.2f / %.2f' % (v['perenidad_indicio']['s2_freq_seca_media'], v['perenidad_indicio']['s2_freq_chuva_media']), v['perenidad_indicio']['s1_freq16_media'], (v['perenidad_indicio']['jrc_occurrence_media'] if np.isfinite(v['perenidad_indicio']['jrc_occurrence_media']) else '- (JRC nunca vio agua en el eje)'),
                      '%.3f vs %.3f' % (v['perenidad_indicio']['ndmi_p10_seca_eje_media'], v['perenidad_indicio']['ndmi_p10_seca_entorno_100_300m'])])
md.append(md_tabla(['Gleba', 'Arroio', 'FBDS (m)', 'otto 2020 (m)', 'ANA 5k (m)', 'IBGE BC250 (m)', 'Ensamble DEM (m)', 'CAR rio<=10 (m aprox.)', 'Nombre otto', 'Regime IBGE', 'Ancho agua persistente S2 (m)', 'S2 freq seca/lluv. (eje 15 m)', 'S1 f16', 'JRC occ %', 'NDMI seco eje vs entorno'], filas))
md.append('\n\nPerenidad: la frecuencia de agua en el eje es un INDICIO (arroios de 1-3 m no resuelven en 10 m); la prueba es de campo en estacion seca. Ancho: ningun tramo fuera de la represa muestra agua abierta persistente > 10 m -> faixa de 30 m se mantiene.\n' if not any(v['clase_ancho']['algun_tramo_mas_de_10m'] for gl in cursos for n, v in cursos[gl].items() if not n.startswith('_')) else '\n\n**AVISO: algun tramo muestra agua persistente > 10 m de ancho: revisar faixa de 50 m.**\n')
md.append('\n## 7. Que cambia en el diagnostico (antes -> despues)\n')
filas = []
for gl in GLEBAS:
    a = app_res[gl]
    filas.append([gl, 'APP exigible (30 m + nascente 50 m)', a['app_vigente_json_ha'], '%.2f (FBDS) | ensamble %.2f | envolvente [%.2f; %.2f] | CAR %.2f' % (a['app_fbds_recalculada_ha'], a['app_mediana_ensamble_ha'], a['envolvente_min_max_ha'][0], a['envolvente_min_max_ha'][1], a['app_car_declarada_en_gleba_ha'])])
filas.append(['G1', 'Represa: espejo', '%.2f (FBDS) / %.2f (MNDWI 29-ago) / %.2f (JRC max)' % (esp['fbds_2013_ha'], esp['escena_2026_08_29_mndwi_ha'], esp['jrc_max_extent_1984_2021_ha']), '%s (mediana S2 lluviosa 2024-26); rango %s; CAR declara %.2f' % (ref_val, espelho_ref['rango_s2_2024_2026_ha'], esp['car_declarado_iat_ha'])])
filas.append(['G1', 'Nascentes', '1 FBDS + 2 candidatos DEM', '; '.join('%s %s: %s' % (r['fonte'][:4], r['id'], r['veredicto']) for r in cand_rows if r['dentro_propriedade'])])
filas.append(['G1', 'Cursos (km dentro)', RG['G1']['arroios']['km_dentro'], 'FBDS %.3f | otto %.3f | ANA %.3f | ensamble %.3f km' % (RG['G1']['arroios']['km_dentro'], sum(v['long_por_fuente_en_gleba']['otto_iat_2020']['km'] for n, v in cursos['G1'].items() if not n.startswith('_')), sum(v['long_por_fuente_en_gleba']['ana_bho_5k_2017']['km'] for n, v in cursos['G1'].items() if not n.startswith('_')), sum(v['long_por_fuente_en_gleba'].get('mediana_ensamble_5dem', {}).get('km', 0) for n, v in cursos['G1'].items() if not n.startswith('_')))])
filas.append(['G1', 'CAR', 'sin CAR propio identificado (vecino F127CD1E)', 'CAR PROPIO %s: APP %.2f, RL averbada %.2f (exigida %.2f), veg. nativa %.2f, consolidada %.2f ha' % (CAR_G1[-8:], comp_car['G1']['app_car_geom_en_gleba_ha'], comp_car['G1']['rl_car_geom_en_gleba_ha'], comp_car['G1']['rl_exigida_20pct_ha'], comp_car['G1']['veg_nativa_car_en_gleba_ha'], comp_car['G1']['area_consolidada_car_en_gleba_ha'])])
md.append(md_tabla(['Gleba', 'Item', 'Antes (resultados_glebas.json)', 'Despues (an_11)'], filas))
md.append('\n\n**Referencia recomendada para el informe: %s.** %s\n' % (RES['app']['referencia_recomendada'], RES['app']['justificacion']))
md.append('\n\nSerie S1: %s\n' % esp.get('s1_otsu_nota'))
md.append('\n## 7b. Contexto regulatorio que aportan las capas de gobierno\n')
for d in ctx['outorgas_en_propiedad']:
    md.append('- **Outorga SIGARH dentro de la propiedad**: empreendimento "%s", interferencia **%s** en %s %s (cuenca %s, otto %s), portaria %s (%s, %s), finalidades "%s", '
              'publicada %s, vencimiento %s (**vencida: %s**), **status %s**; el punto esta a %.0f m del espejo FBDS y a %.0f m del arroio mas cercano. '
              'Es la outorga previa del barramento de la represa (Ribeirao do Salto = arroio 3): confirma que el reservatorio decorre de barramento de curso natural (art. 4 III) y que la regularizacion hidrica esta pendiente.'
              % (d.get('nm_empreendimento'), d.get('nm_tipo_interferencia'), d.get('nm_tipo_corpo_hidrico'), d.get('nm_corpo_hidrico_complemento'), d.get('nm_bacia_hidrografica'), d.get('cod_otto'),
                 d.get('nr_portaria'), d.get('nm_tipo_documento'), d.get('nm_tipo_solicitacao'), d.get('desc_finalidades'), d.get('dt_publicacao'), d.get('dt_vencimento'), d['vencida'], d.get('st_portaria'),
                 d['dist_espelho_fbds_m'], d['dist_arroio_mas_cercano_m']))
for d in ctx['mananciais_abastecimento']:
    md.append('- **Manancial de abastecimento publico** (%s): "%s", tipo %s, impeditivo **%s**, portaria %s, abastece %s, ICMS ecologico %s -> %.0f%% de la propiedad dentro.'
              % (d['capa'], d['nome'], d['tipo'], d['impeditivo'], d['portaria'], d['municipio_abastecido'], d['icms'], d['pct_propiedad_dentro']))
for d in ctx['fragmentos_prioritarios_iat']:
    md.append('- **Fragmento florestal prioritario IAT** %s: %.1f ha totales, idade %s anos, prioridade %s, tamanho %s -> %.2f ha dentro de la propiedad.'
              % (d['fragmento'], d['area_total_ha'], d['idade_anos'], d['prioridade'], d['classe_tamanho'], d['dentro_propriedade_ha']))
md.append('\n## 8. Lectura y recomendaciones para el informe\n')
a1 = disp['G1'].get('Arroio 1 (norte)', {})
md.append('\n'.join([
    '1. **El inmueble YA tiene CAR** (`%s`, %.2f ha, "%s"): no es un vecino. Declara APP %.2f ha (num_area %.2f), **Reserva Legal averbada de solo %.2f ha contra %.2f ha exigidas (20%%)**, vegetacion nativa %.2f ha contra %.1f ha de floresta medida, area consolidada %.2f ha y un reservatorio de %.2f ha. '
    'El diagnostico debe pasar de "propuesta de CAR" a **retificacao del CAR existente** (RL insuficiente y vegetacion nativa subdeclarada), y G2 debe tratarse como desmembramento del CAR `%s` (94 ha, ya notificado por el IAT).'
    % (CAR_G1, float(im[im.cod_imovel == CAR_G1].num_area.iloc[0]), im_sel.iloc[0].des_condic, comp_car['G1']['app_car_geom_en_gleba_ha'], comp_car['G1']['app_car_num_area_decl_ha'],
       comp_car['G1']['rl_car_geom_en_gleba_ha'], comp_car['G1']['rl_exigida_20pct_ha'], comp_car['G1']['veg_nativa_car_en_gleba_ha'], comp_car['G1']['floresta_nativa_medida_ha'] or 0,
       comp_car['G1']['area_consolidada_car_en_gleba_ha'], esp['car_declarado_iat_ha'], CAR_G2),
    '2. **La referencia del leito sigue siendo FBDS/IAT**: los 5 DEM coinciden entre si a %s m (mediana) y con FBDS a 8-29 m por arroio; ninguna base de gobierno (otto 1:50k, ANA 5k, BC250, CAR) mejora esa precision. '
    'La unica discrepancia sistematica esta en el **Arroio 1 (norte)**: la mediana del ensamble queda a %s m (p90 %s m) del eje FBDS y todos los DEM la desplazan hacia el mismo lado, lo que sube la APP de ese arroio de %.2f a %.2f ha (G1 total %.2f -> %.2f ha). '
    'Recomendacion: levantar el eje del Arroio 1 con GNSS (RTK o L1/L5) antes de la retificacao del CAR; hasta entonces reportar APP G1 = %.2f ha con envolvente [%.2f; %.2f].'
    % (np.median([v['dispersion_entre_dem_mediana_m'] for v in disp['G1'].values()]), a1.get('mediana_ensamble_vs_fbds_med_m'), a1.get('mediana_ensamble_vs_fbds_p90_m'), a1.get('app30_fbds_ha', 0), a1.get('app30_mediana_ensamble_ha', 0),
       app_res['G1']['app_fbds_recalculada_ha'], app_res['G1']['app_mediana_ensamble_ha'], app_res['G1']['app_fbds_recalculada_ha'], *app_res['G1']['envolvente_min_max_ha']),
    '3. **Represa**: el espejo actual (2024-26) es de %.2f-%.2f ha segun sensor (S2 mediana lluviosa %.2f; S1 -18 dB %.2f; MapBiomas 2024 %.2f), es decir la mitad del historico (FBDS 2013 %.2f, WorldView-2 2012 %.2f, CAR %.2f). Esta en la frontera de 1 ha: '
    'no se puede afirmar la dispensa del art. 4 par. 4. Recomendacion: medir el perimetro del espejo en campo (GNSS, estacion lluviosa, o cota del vertedero) y, mientras tanto, mantener el criterio conservador (>= 1 ha, sin dispensa) y la faixa de 30 m del arroio 3 bajo el espejo.'
    % (espelho_ref['envolvente_actual_ha'][0], espelho_ref['envolvente_actual_ha'][1], ref_val, serie_s1[18]['todas'].get('mediana'), esp['mapbiomas_agua_2024_ha'], esp['fbds_2013_ha'], esp['iat_uso2012_wv2_corpos_dagua_ha'], esp['car_declarado_iat_ha']),
    '4. **Nascentes**: la nascente FBDS 306158 se confirma como probable (inicio de trecho otto a 20 m, 3/5 DEM, varzea en el mapeo IAT 2012, NDMI seco por encima del entorno); dem_1 es la misma cabecera 97 m aguas arriba (no suma APP nueva; el circulo de 50 m debe centrarse donde aflore el agua en campo); '
    'dem_2 (en soja) queda como POCO PROBABLE: sin agua en 338 escenas S2 ni 43 S1, sin base oficial, y mas seco que su entorno en la seca (z = %s). El riesgo de %.2f ha del talvegue se mantiene solo como aviso topografico para la visita en estacion lluviosa.'
    % (next((r['ndmi_p10_seca_z_robusto'] for r in cand_rows if r['id'] == 'dem_2'), None), RG['G1']['nascentes']['talvegue_dem_risco_ha']),
    '5. **Cursos**: longitudes por fuente dentro de G1 coinciden con FBDS (otto %.3f km, enquadramento igual; ANA 5k y BC250 solo cubren los arroios 1 y 3, que BC250 clasifica como Permanente; el arroio 3 es el Ribeirao do Salto, clase 2). '
    'Ningun tramo muestra agua abierta persistente > 10 m fuera de la represa: la faixa de 30 m se mantiene. La frecuencia de agua en los ejes es ~0 en S2/S1 (cauces de 1-3 m bajo dosel no resuelven a 10 m): la perenidad NO se puede probar por satelite; el unico indicio positivo es el NDMI seco mas alto en el eje que en el entorno (%s).'
    % (sum(v['long_por_fuente_en_gleba']['otto_iat_2020']['km'] for n, v in cursos['G1'].items() if not n.startswith('_')),
       {n: '%.3f vs %.3f' % (v['perenidad_indicio']['ndmi_p10_seca_eje_media'], v['perenidad_indicio']['ndmi_p10_seca_entorno_100_300m']) for n, v in cursos['G1'].items() if not n.startswith('_')}),
    '6. **Contexto regulatorio nuevo** (seccion 7b): (i) la represa tiene una outorga PREVIA de barragem en SIGARH con status %s y vencida (%s): el informe debe recomendar regularizar la outorga (o su renovacion) junto con el CAR; '
    '(ii) el 100%% de la propiedad esta dentro del manancial de abastecimento publico "Rio Congonhas" (impeditivo %s, portaria %s): toda intervencion en APP/RL y el propio barramento se licencian bajo ese regimen; '
    '(iii) el fragmento IAT %s (prioridade A, %s anos) toca la propiedad en %.2f ha: es el corredor natural para la RL. Curvas de nivel 1:50k: sesgo vertical de los DEM +5 a +7 m, MAD 4-5 m, sin consecuencia para el trazado.'
    % (ctx['outorgas_en_propiedad'][0].get('st_portaria') if ctx['outorgas_en_propiedad'] else '-', ctx['outorgas_en_propiedad'][0].get('dt_vencimento') if ctx['outorgas_en_propiedad'] else '-',
       next((d['impeditivo'] for d in ctx['mananciais_abastecimento'] if d['impeditivo'] == 'Sim'), '-'), next((d['portaria'] for d in ctx['mananciais_abastecimento'] if d['impeditivo'] == 'Sim'), '-'),
       max(ctx['fragmentos_prioritarios_iat'], key=lambda d: d['dentro_propriedade_ha'])['fragmento'] if ctx['fragmentos_prioritarios_iat'] else '-',
       max(ctx['fragmentos_prioritarios_iat'], key=lambda d: d['dentro_propriedade_ha'])['idade_anos'] if ctx['fragmentos_prioritarios_iat'] else '-',
       max(ctx['fragmentos_prioritarios_iat'], key=lambda d: d['dentro_propriedade_ha'])['dentro_propriedade_ha'] if ctx['fragmentos_prioritarios_iat'] else 0),
]))
RES['recomendaciones'] = md[-1]
guardar_json(JSON_OUT, _limpio(RES))
with open(MD_OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(md))
log('  -> %s' % MD_OUT)
with open(LOG_TXT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(_log_lines))
log('an_11 terminado en %.0f s' % (time.time() - T0))
