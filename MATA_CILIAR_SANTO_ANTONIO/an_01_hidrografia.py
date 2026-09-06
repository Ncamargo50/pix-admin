# -*- coding: utf-8 -*-
"""an_01_hidrografia.py — red hidrica consolidada de la Fazenda Santo Antonio.

1. Hidrografia oficial (FBDS/IAT, otto 2020, ANA BHO 5k, IBGE BC250, CAR vecinos)
   recortada a propiedad + 500 m.
2. Red de drenaje por DEM (pysheds sobre GLO30 30 m), umbral de aporte calibrado
   contra FBDS (distancia mediana entre lineas), HAND.
3. Agua abierta S2 10 m (MNDWI Otsu + NDVI<0,3, sieve 3 px) cruzada con FBDS y JRC.
4. `hidrografia_consolidada.geojson`, `nascentes_consolidadas.geojson`.
5. Tabla fuente -> km dentro de la propiedad; desacuerdo entre fuentes.

La FBDS es la REFERENCIA del leito. La red DEM es control, y sus cabeceras son
CANDIDATOS a nascente, nunca nascentes.
"""
import os
import time

import numpy as np
import geopandas as gpd
import shapely
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union, linemerge
from shapely.strtree import STRtree
from scipy import ndimage as ndi
from skimage.filters import threshold_otsu

from an_00_config import *  # noqa: F401,F403

T0 = time.time()
titulo('an_01_hidrografia — red hidrica consolidada  (%s)' % FECHA_ESCENA)
prop = propiedad()
PROP = prop['geom']
AOI_H = PROP.buffer(P['margen_aoi_hidro_m'])
log('Propiedad %.2f ha; AOI hidro = propiedad + %d m (%.1f ha)'
    % (prop['area_ha'], P['margen_aoi_hidro_m'], AOI_H.area / 1e4))

RES = {'fecha_escena': FECHA_ESCENA, 'propiedad_ha': round(prop['area_ha'], 2)}


def long_dentro(gdf, geom=PROP):
    """Suma de longitud (m) de las lineas de `gdf` dentro de `geom`."""
    if len(gdf) == 0:
        return 0.0
    return float(gdf.geometry.intersection(geom).length.sum())


# ==============================================================================
# 1. Hidrografia oficial
# ==============================================================================
titulo('1. Hidrografia oficial recortada a propiedad + 500 m')
fbds_rios = leer_vector('fbds_rios', AOI_H)
fbds_nasc = leer_vector('fbds_nascentes', AOI_H)
fbds_massas = leer_vector('fbds_massas', AOI_H)
fbds_rios_pol = leer_vector('fbds_rios_pol', AOI_H)
otto = leer_vector('otto', AOI_H)
ana = leer_vector('ana', AOI_H)
ibge = leer_vector('ibge', AOI_H)
car_vec = leer_vector('car_vecinos', AOI_H)
fbds_rios['fbds_id'] = fbds_rios['objectid'].astype(int)
fbds_rios['comprimento_m'] = fbds_rios.geometry.length

fuentes = {
    'FBDS_rios_ate10m': fbds_rios, 'IAT_otto_2020': otto, 'ANA_BHO2017_5k': ana,
    'IBGE_BC250': ibge,
}
tabla_fuentes = {}
for k, g in fuentes.items():
    n_dentro = int(g.intersects(PROP).sum())
    tabla_fuentes[k] = {'tramos_aoi500': len(g), 'tramos_intersectan_propriedade': n_dentro,
                        'km_aoi500': km(g.length.sum()), 'km_dentro_propriedade': km(long_dentro(g))}
    log('  %-18s tramos AOI=%3d  intersectan prop=%2d  km AOI=%6.2f  km dentro=%5.3f'
        % (k, len(g), n_dentro, tabla_fuentes[k]['km_aoi500'], tabla_fuentes[k]['km_dentro_propriedade']))
n_nasc_dentro = int(fbds_nasc.within(PROP).sum())
n_massas_dentro = int(fbds_massas.intersects(PROP).sum())
log('  FBDS nascentes: %d en AOI, %d dentro de la propiedad' % (len(fbds_nasc), n_nasc_dentro))
log('  FBDS massas d agua: %d en AOI, %d intersectan la propiedad (natureza: %s)'
    % (len(fbds_massas), n_massas_dentro, fbds_massas['natureza'].value_counts().to_dict()))
log('  FBDS rios >10 m (poligono): %d en AOI, %d intersectan la propiedad'
    % (len(fbds_rios_pol), int(fbds_rios_pol.intersects(PROP).sum())))
log('  CAR vecinos (hidrografia declarada): %d poligonos en AOI; temas %s'
    % (len(car_vec), car_vec['nom_tema'].value_counts().to_dict()))
car_en_prop = car_vec[car_vec.intersects(PROP)]
log('  CAR vecinos que tocan la propiedad: %d (ha dentro: %.2f)'
    % (len(car_en_prop), car_en_prop.geometry.intersection(PROP).area.sum() / 1e4))
tabla_fuentes['FBDS_nascentes'] = {'n_aoi500': len(fbds_nasc), 'n_dentro_propriedade': n_nasc_dentro}
tabla_fuentes['FBDS_massas_dagua'] = {'n_aoi500': len(fbds_massas), 'n_intersectam_propriedade': n_massas_dentro}
# sobreposicao de CAR vizinho: um imovel vizinho que declara hidrografia (reservatorio/curso) CAIDA
# dentro do poligono do cliente indica perimetro sobreposto -> pendencia tipica no SICAR
car_grp = []
if len(car_en_prop):
    cg = car_en_prop.assign(ha_tot=car_en_prop.geometry.area / 1e4,
                            ha_in=car_en_prop.geometry.intersection(PROP).area / 1e4)
    cg = cg.groupby(['cod_imovel', 'nom_tema', 'ind_status'], as_index=False)[['ha_tot', 'ha_in']].sum()
    for r in cg.itertuples():
        frac = float(r.ha_in / r.ha_tot) if r.ha_tot > 0 else 0.0
        car_grp.append({'cod_imovel': str(r.cod_imovel), 'tema': str(r.nom_tema), 'status': str(r.ind_status),
                        'ha_total': round(float(r.ha_tot), 2), 'ha_dentro_propriedade': round(float(r.ha_in), 2),
                        'frac_dentro': round(frac, 2),
                        'sobreposicao_relevante': bool(r.ha_in >= 0.5 and frac >= 0.9)})
sobrep = [c for c in car_grp if c['sobreposicao_relevante']]
for c in sobrep:
    log('  !! SOBREPOSICAO DE CAR VIZINHO: imovel %s (%s) declara "%s" de %.2f ha, %.0f%% dentro do poligono do cliente'
        % (c['cod_imovel'], c['status'], c['tema'], c['ha_total'], 100 * c['frac_dentro']))
tabla_fuentes['CAR_vizinhos_hidro_pol'] = {'n_aoi500': len(car_vec), 'n_tocam_propriedade': len(car_en_prop),
                                          'ha_dentro_propriedade': ha(car_en_prop.geometry.intersection(PROP).area.sum()),
                                          'por_imovel_tema': car_grp,
                                          'sobreposicao_imoveis': sobrep,
                                          'nota': 'sobreposicao_relevante = feicao >= 0,5 ha com >= 90% dentro do poligono do cliente: verificar perimetro no SICAR antes de inscrever'}
if fbds_rios_pol.intersects(PROP).any():
    log('  !! AVISO: hay curso >10 m FBDS tocando la propiedad: APP 50 m aplicaria')
RES['fontes'] = tabla_fuentes

# ==============================================================================
# 2. Red de drenaje por DEM (pysheds) + HAND
# ==============================================================================
titulo('2. Red de drenaje por DEM GLO30 30 m (pysheds) y HAND')
from pysheds.grid import Grid
grid = Grid.from_raster(R['dem'])
dem = grid.read_raster(R['dem'])
verificar_rango('DEM GLO30', np.asarray(dem), 500, 900)
pit = grid.fill_pits(dem)
flooded = grid.fill_depressions(pit)
inflated = grid.resolve_flats(flooded)
fdir = grid.flowdir(inflated)
acc = grid.accumulation(fdir)
cell_ha = P['pixel_dem_m'] ** 2 / 1e4
verificar_rango('acumulacion (celdas)', np.asarray(acc), 1)
log('  aporte maximo en el AOI DEM: %.0f ha' % (float(acc.max()) * cell_ha))

_, prof_dem = leer_raster(R['dem'])


def red_dem(umbral_ha):
    """Extrae la red DEM para un umbral de aporte (ha) -> GeoDataFrame de lineas 31982."""
    mask = acc > (umbral_ha / cell_ha)
    net = grid.extract_river_network(fdir, mask)
    geoms = [shape(f['geometry']) for f in net['features']]
    geoms = [g for g in geoms if g.length > 0]
    return gpd.GeoDataFrame({'umbral_ha': [umbral_ha] * len(geoms)}, geometry=geoms, crs=CRS_METRICO)


def puntos_a_lo_largo(gdf, paso=10.0):
    pts = []
    for g in gdf.geometry:
        n = max(2, int(g.length // paso) + 1)
        pts.extend([g.interpolate(d) for d in np.linspace(0, g.length, n)])
    return pts


def distancias(pts, gdf_ref):
    if len(gdf_ref) == 0 or len(pts) == 0:
        return np.array([np.nan] * len(pts))
    tree = STRtree(list(gdf_ref.geometry))
    d = np.array([pts[i].distance(gdf_ref.geometry.iloc[j])
                  for i, j in zip(range(len(pts)), tree.nearest(pts))])
    return d


# calibracion: distancia mediana FBDS -> talweg DEM dentro de propiedad + 500 m
fbds_pts = puntos_a_lo_largo(fbds_rios)
calib = {}
redes = {}
for u in P['umbrales_aporte_ha']:
    g = red_dem(u)
    g_aoi = g[g.intersects(AOI_H)].copy()
    g_aoi['geometry'] = g_aoi.geometry.intersection(AOI_H)
    g_aoi = g_aoi.explode(index_parts=False)
    redes[u] = g_aoi
    d_f2d = distancias(fbds_pts, g_aoi)                  # FBDS -> DEM (omision)
    d_d2f = distancias(puntos_a_lo_largo(g_aoi), fbds_rios)  # DEM -> FBDS (comision)
    calib[u] = {'km_dem_aoi500': km(g_aoi.length.sum()), 'km_fbds_aoi500': km(fbds_rios.length.sum()),
                'dist_mediana_fbds_a_dem_m': round(float(np.nanmedian(d_f2d)), 1),
                'dist_p90_fbds_a_dem_m': round(float(np.nanpercentile(d_f2d, 90)), 1),
                'dist_mediana_dem_a_fbds_m': round(float(np.nanmedian(d_d2f)), 1),
                'dist_p90_dem_a_fbds_m': round(float(np.nanpercentile(d_d2f, 90)), 1),
                'km_dem_dentro_propriedade': km(long_dentro(g_aoi))}
    log('  umbral %2d ha: red DEM %6.2f km (FBDS %6.2f km) | FBDS->DEM med %5.1f m p90 %5.1f | '
        'DEM->FBDS med %5.1f m p90 %5.1f | dentro prop %.3f km'
        % (u, calib[u]['km_dem_aoi500'], calib[u]['km_fbds_aoi500'], calib[u]['dist_mediana_fbds_a_dem_m'],
           calib[u]['dist_p90_fbds_a_dem_m'], calib[u]['dist_mediana_dem_a_fbds_m'],
           calib[u]['dist_p90_dem_a_fbds_m'], calib[u]['km_dem_dentro_propriedade']))
# criterio: minimizar la suma simetrica de medianas (omision + comision)
umbral_opt = min(calib, key=lambda u: calib[u]['dist_mediana_fbds_a_dem_m'] + calib[u]['dist_mediana_dem_a_fbds_m'])
log('  => umbral elegido: %d ha (menor suma de medianas simetricas)' % umbral_opt)
red = redes[umbral_opt].copy()
red['fonte'] = 'DEM_GLO30_D8'
red['comprimento_m'] = red.geometry.length.round(1)
red['dentro_propriedade'] = red.intersects(PROP)
guardar_vector(red, 'hidro_dem_red')
todas = gpd.GeoDataFrame(__import__('pandas').concat([redes[u] for u in redes], ignore_index=True), crs=CRS_METRICO)
guardar_vector(todas, 'hidro_dem_red_umbrales')

# HAND con la red del umbral elegido
hand = grid.compute_hand(fdir, flooded, acc > (umbral_opt / cell_ha))
hand_arr = np.asarray(hand, dtype=np.float32)
hand_arr[~np.isfinite(hand_arr)] = -9999.0
verificar_rango('HAND (m)', np.where(hand_arr < 0, np.nan, hand_arr), 0, 300)
guardar_raster(os.path.join(ANALISIS, 'HAND_30m.tif'), hand_arr, prof_dem, nodata=-9999.0,
               tags={'fuente': 'pysheds D8 sobre DEM GLO30 30 m', 'umbral_aporte_ha': umbral_opt,
                     'red': 'acc > umbral', 'nota': 'NaN (=nodata) donde la celda no drena a la red dentro del AOI DEM'},
               descripciones=['HAND'])
acc_ha = (np.asarray(acc, dtype=np.float32) * cell_ha)
guardar_raster(os.path.join(ANALISIS, 'ACUMULACION_ha_30m.tif'), acc_ha, prof_dem, nodata=-9999.0,
               tags={'unidad': 'ha de area de aporte'}, descripciones=['aporte_ha'])

# consistencia por tramo FBDS dentro de la propiedad
fbds_prop = fbds_rios[fbds_rios.intersects(PROP)].copy()
consist = []
for _, r in fbds_prop.iterrows():
    seg = r.geometry.intersection(PROP)
    if seg.is_empty:
        continue
    segs = [seg] if isinstance(seg, LineString) else list(seg.geoms)
    pts = puntos_a_lo_largo(gpd.GeoDataFrame(geometry=segs, crs=CRS_METRICO))
    d = distancias(pts, red)
    d_otto = distancias(pts, otto)
    d_ana = distancias(pts, ana)
    consist.append({'fbds_id': int(r['fbds_id']), 'comprimento_dentro_m': round(seg.length, 1),
                    'dist_mediana_dem_m': round(float(np.nanmedian(d)), 1),
                    'dist_p90_dem_m': round(float(np.nanpercentile(d, 90)), 1),
                    'dist_mediana_otto_m': round(float(np.nanmedian(d_otto)), 1) if len(otto) else None,
                    'dist_mediana_ana_m': round(float(np.nanmedian(d_ana)), 1) if len(ana) else None})
    log('  tramo FBDS %-6d %6.1f m dentro | DEM med %5.1f p90 %5.1f | otto med %s | ANA med %s'
        % (r['fbds_id'], seg.length, consist[-1]['dist_mediana_dem_m'], consist[-1]['dist_p90_dem_m'],
           consist[-1]['dist_mediana_otto_m'], consist[-1]['dist_mediana_ana_m']))
d_all = distancias(puntos_a_lo_largo(gpd.GeoDataFrame(geometry=list(fbds_prop.geometry.intersection(PROP).explode(index_parts=False)), crs=CRS_METRICO)), red)
RES['dem'] = {'dem': 'Copernicus GLO30 2024_1 (30 m)', 'algoritmo': 'pysheds: fill_pits, fill_depressions, resolve_flats, D8, accumulation',
              'calibracion_umbral': calib, 'umbral_elegido_ha': umbral_opt,
              'consistencia_fbds_vs_dem_tramos_propriedade': consist,
              'consistencia_fbds_vs_dem_global_propriedade': {
                  'dist_mediana_m': round(float(np.nanmedian(d_all)), 1),
                  'dist_p90_m': round(float(np.nanpercentile(d_all, 90)), 1),
                  'pct_dentro_30m': round(100 * float(np.mean(d_all <= 30)), 1),
                  'pct_dentro_60m': round(100 * float(np.mean(d_all <= 60)), 1)},
              'nota': 'DEM 30 m es DSM (dosel incluido): el talweg bajo mata ciliar se desplaza; solo control'}
log('  FBDS dentro de la propiedad vs DEM: mediana %.1f m, p90 %.1f m, %.0f%% a <=30 m'
    % (RES['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_mediana_m'],
       RES['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_p90_m'],
       RES['dem']['consistencia_fbds_vs_dem_global_propriedade']['pct_dentro_30m']))

# ==============================================================================
# 3. Agua abierta S2 10 m
# ==============================================================================
titulo('3. Agua abierta en S2 %s (MNDWI Otsu + NDVI<%.2f, sieve %d px)' % (FECHA_ESCENA, P['ndvi_max_agua'], P['sieve_agua_px']))
idx, prof10 = leer_raster(R['indices'])
scl, _ = leer_raster(R['scl'])
scl = scl['SCL']
valido = ~np.isin(scl, list(SCL_INVALIDA)) & np.isfinite(idx['MNDWI']) & np.isfinite(idx['NDVI'])
for k in ('MNDWI', 'NDWI', 'AWEInsh', 'NDVI'):
    verificar_rango(k, np.where(valido, idx[k], np.nan), -1.5 if k != 'AWEInsh' else -5, 1.5 if k != 'AWEInsh' else 5)
mndwi_v = idx['MNDWI'][valido]
t_otsu = float(threshold_otsu(mndwi_v))
hist, edges = np.histogram(mndwi_v, bins=200, range=(-1, 1))
frac_otsu = float(np.mean(mndwi_v > t_otsu))
log('  Otsu MNDWI en AOI: %.3f  (fraccion > umbral: %.2f%%)' % (t_otsu, 100 * frac_otsu))
# guarda: Otsu sobre una distribucion casi unimodal (agua <1% del AOI) puede partir la moda
# principal; se acepta solo si esta en un rango fisico de agua y marca <5% del AOI.
umbral = t_otsu
umbral_fuente = 'otsu'
if not (-0.20 <= t_otsu <= 0.40) or frac_otsu > 0.05:
    umbral = 0.0
    umbral_fuente = 'fijo_0 (Otsu fuera de rango o >5% del AOI: distribucion unimodal)'
    log('  !! Otsu descartado, se usa MNDWI > 0 (Xu 2006)')
agua = valido & (idx['MNDWI'] > umbral) & (idx['NDVI'] < P['ndvi_max_agua'])
n_antes = int(agua.sum())
lab, n = ndi.label(agua, structure=np.ones((3, 3)))
tam = ndi.sum(agua, lab, index=np.arange(1, n + 1))
keep = np.isin(lab, np.arange(1, n + 1)[tam >= P['sieve_agua_px']])
agua = agua & keep
log('  pixeles agua: %d antes del sieve -> %d despues (%d cuerpos)' % (n_antes, int(agua.sum()), int(len(np.unique(lab[agua])))))
guardar_json(os.path.join(ANALISIS, 'agua_s2_histograma_mndwi.json'),
             {'bins': edges.tolist(), 'hist': hist.tolist(), 'otsu': t_otsu, 'umbral_usado': umbral,
              'umbral_fuente': umbral_fuente, 'n_validos': int(valido.sum())})
try:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(edges[:-1], hist, width=0.01, color='#0D9488')
    ax.axvline(t_otsu, color='#7FD633', label='Otsu %.3f' % t_otsu)
    ax.axvline(umbral, color='#1D4ED8', ls='--', label='usado %.3f' % umbral)
    ax.set_yscale('log'); ax.set_xlabel('MNDWI (AOI, pixeles validos)'); ax.set_ylabel('n'); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(ANALISIS, 'agua_s2_histograma_mndwi.png'), dpi=130); plt.close(fig)
except Exception as e:  # matplotlib es opcional
    log('  (sin PNG del histograma: %s)' % e)

agua_u8 = agua.astype(np.uint8)
guardar_raster(os.path.join(ANALISIS, 'agua_s2_%s_10m.tif' % FECHA_ESCENA), agua_u8, prof10, nodata=255,
               tags={'regla': 'MNDWI>%.3f & NDVI<%.2f & SCL valido, sieve %d px' % (umbral, P['ndvi_max_agua'], P['sieve_agua_px']),
                     'otsu': t_otsu, 'umbral_fuente': umbral_fuente}, descripciones=['agua'])
agua_v = vectorizar(agua_u8, prof10, 'agua')
agua_v['area_ha'] = (agua_v.geometry.area / 1e4).round(3)
agua_v['agua_id'] = np.arange(1, len(agua_v) + 1)
# JRC occurrence a 10 m (nearest) -> media por poligono
jrc10 = remuestrear_a(R['jrc'], prof10, banda=1, metodo='nearest').astype(np.float32)
from rasterio import features as rfeat
ids = rfeat.rasterize([(g, int(i)) for g, i in zip(agua_v.geometry, agua_v['agua_id'])],
                      out_shape=agua.shape, transform=prof10['transform'], dtype=np.int32) \
    if len(agua_v) else np.zeros(agua.shape, dtype=np.int32)
suma = np.bincount(ids.ravel(), weights=np.nan_to_num(jrc10).ravel(), minlength=len(agua_v) + 1)
cnt = np.bincount(ids.ravel(), minlength=len(agua_v) + 1)
agua_v['jrc_occurrence_media'] = [round(float(suma[i] / cnt[i]), 1) if cnt[i] else None for i in agua_v['agua_id']]
agua_v['mndwi_medio'] = [round(float(np.nanmean(idx['MNDWI'][ids == i])), 3) for i in agua_v['agua_id']]
# superficies brillantes (techos, silos, suelo calcareo) dan MNDWI>0 con NDVI bajo: agua real es OSCURA en el visible
s2b, _ = leer_raster(R['s2'], bandas=['B2', 'B4'])
agua_v['b2_medio'] = [round(float(np.nanmean(s2b['B2'][ids == i])), 3) for i in agua_v['agua_id']]
agua_v['possivel_falso_positivo'] = agua_v['b2_medio'] > 0.12
if agua_v['possivel_falso_positivo'].any():
    log('  !! %d cuerpo(s) con B2 medio > 0,12 (superficie brillante, no agua): marcados possivel_falso_positivo' % int(agua_v['possivel_falso_positivo'].sum()))
agua_v['intersecta_propriedade'] = agua_v.intersects(PROP)
agua_v['dentro_propriedade_ha'] = (agua_v.geometry.intersection(PROP).area / 1e4).round(3)
# cruce con FBDS massas
agua_v['fbds_massa_id'] = None
agua_v['fbds_natureza'] = None
for i, r in agua_v.iterrows():
    m = fbds_massas[fbds_massas.intersects(r.geometry)]
    if len(m):
        agua_v.at[i, 'fbds_massa_id'] = int(m.iloc[0]['objectid'])
        agua_v.at[i, 'fbds_natureza'] = str(m.iloc[0]['natureza'])
guardar_vector(agua_v, 'agua_s2_%s' % FECHA_ESCENA)
log('  agua S2 en AOI: %d cuerpos, %.2f ha; tocan la propiedad: %d cuerpos, %.2f ha dentro'
    % (len(agua_v), agua_v['area_ha'].sum(), int(agua_v['intersecta_propriedade'].sum()),
       agua_v['dentro_propriedade_ha'].sum()))

# masas de agua FBDS que tocan la propiedad: FBDS 2013 vs S2 2026 vs JRC, barramento
masas = fbds_massas[fbds_massas.intersects(PROP) & (fbds_massas.geometry.area > 10)].copy()  # sin astillas <10 m2
masas['massa_id'] = masas['objectid'].astype(int)
masas['area_fbds_2013_ha'] = (masas.geometry.area / 1e4).round(3)
masas['area_dentro_prop_ha'] = (masas.geometry.intersection(PROP).area / 1e4).round(3)
masas['area_s2_2026_ha'] = 0.0
masas['jrc_occurrence_media'] = None
masas['sobre_curso_fbds'] = False
masas['fbds_rio_ids'] = ''
for i, r in masas.iterrows():
    otras = unary_union([g for j, g in zip(masas.index, masas.geometry) if j != i]) if len(masas) > 1 else None
    env = r.geometry.buffer(20)
    if otras is not None:
        env = env.difference(otras)          # asignacion EXCLUSIVA: represas contiguas no se cuentan dos veces
    a = agua_v[agua_v.intersects(env)]
    masas.at[i, 'area_s2_2026_ha'] = round(float(a.geometry.intersection(env).area.sum() / 1e4), 3)
    mid = rasterizar([r.geometry], prof10) > 0
    masas.at[i, 'jrc_occurrence_media'] = round(float(np.nanmean(jrc10[mid])), 1) if mid.any() else None
    rios = fbds_rios[fbds_rios.intersects(r.geometry.buffer(15))]
    masas.at[i, 'sobre_curso_fbds'] = bool(len(rios) > 0)
    masas.at[i, 'fbds_rio_ids'] = ','.join(str(x) for x in rios['fbds_id'].tolist())
    log('  massa FBDS %d: natureza=%s  FBDS2013 %.3f ha (dentro prop %.3f)  S2-2026 %.3f ha  JRC occ %s  sobre curso FBDS=%s (%s)'
        % (r['massa_id'], r['natureza'], masas.at[i, 'area_fbds_2013_ha'], masas.at[i, 'area_dentro_prop_ha'],
           masas.at[i, 'area_s2_2026_ha'], masas.at[i, 'jrc_occurrence_media'], masas.at[i, 'sobre_curso_fbds'],
           masas.at[i, 'fbds_rio_ids']))
masas['barramento_curso_natural'] = masas['sobre_curso_fbds'] & (masas['natureza'].map(sin_acentos) == 'artificial')
# --- corpo d'agua: massas FBDS contiguas (distancia < 1 m) sao UM corpo para o teste de 1 ha (art. 4 par. 4).
# O teste sobre uma massa isolada nao e defensavel sem saber se ha dois barramentos; e todas as medidas
# < 1 ha (MNDWI>0 & NDVI<0,3 na seca) sao LIMITES INFERIORES da lamina a cota normal.
ml = list(masas.geometry)
corpo = {i: None for i in masas.index}
n_corpo = 0
for i, gi in zip(masas.index, ml):
    if corpo[i] is not None:
        continue
    n_corpo += 1
    pila = [i]; corpo[i] = n_corpo
    while pila:
        a = pila.pop()
        for j, gj in zip(masas.index, ml):
            if corpo[j] is None and masas.geometry[a].distance(gj) < 1.0:
                corpo[j] = n_corpo; pila.append(j)
masas['corpo_id'] = [corpo[i] for i in masas.index]
# medidas alternativas da lamina (a cota normal), por massa: NDWI>0, MNDWI>-0,1, JRC max_extent 1984-2021
ndwi_a = valido & (idx['NDWI'] > 0)
mndwi_l = valido & (idx['MNDWI'] > -0.1) & (idx['NDVI'] < P['ndvi_max_agua'] + 0.1)
jrc_max10 = remuestrear_a(R['jrc'], prof10, banda=2, metodo='nearest')
jrc_max10 = np.nan_to_num(jrc_max10.astype(np.float32), nan=0) == 1
for c_ in ('area_ndwi_gt0_2026_ha', 'area_mndwi_gt_m01_2026_ha', 'area_jrc_max_extent_ha'):
    masas[c_] = 0.0
for i, r in masas.iterrows():
    env = rasterizar([r.geometry.buffer(20)], prof10) > 0
    otras = [g for j, g in zip(masas.index, masas.geometry) if j != i]
    if otras:
        env &= ~(rasterizar([unary_union(otras)], prof10) > 0)
    masas.at[i, 'area_ndwi_gt0_2026_ha'] = round(float((env & ndwi_a).sum()) / 100, 3)
    masas.at[i, 'area_mndwi_gt_m01_2026_ha'] = round(float((env & mndwi_l).sum()) / 100, 3)
    masas.at[i, 'area_jrc_max_extent_ha'] = round(float((env & jrc_max10).sum()) / 100, 3)
corpos = []
for cid, grp in masas.groupby('corpo_id'):
    c = {'corpo_id': int(cid), 'massa_ids': [int(x) for x in grp.massa_id], 'n_massas': len(grp),
         'area_fbds_2013_ha': round(float(grp.area_fbds_2013_ha.sum()), 3),
         'area_s2_mndwi_2026_ha': round(float(grp.area_s2_2026_ha.sum()), 3),
         'area_ndwi_gt0_2026_ha': round(float(grp.area_ndwi_gt0_2026_ha.sum()), 3),
         'area_mndwi_gt_m01_2026_ha': round(float(grp.area_mndwi_gt_m01_2026_ha.sum()), 3),
         'area_jrc_max_extent_ha': round(float(grp.area_jrc_max_extent_ha.sum()), 3),
         'perimetro_fbds_m': round(float(unary_union(list(grp.geometry)).length), 1)}
    # incerteza de area = perimetro x 5 m (meio pixel S2)
    c['incerteza_ha'] = round(c['perimetro_fbds_m'] * 5 / 1e4, 3)
    cota_normal = [c['area_fbds_2013_ha'], c['area_ndwi_gt0_2026_ha'], c['area_jrc_max_extent_ha']]
    c['medidas_cota_normal_ge_1ha'] = [bool(v >= P['reservatorio_dispensa_ha']) for v in cota_normal]
    c['dispensa_art4_par4_lt1ha'] = bool(max(cota_normal) + c['incerteza_ha'] < P['reservatorio_dispensa_ha'])
    # ambigua so se a MAIORIA das medidas a cota normal, descontada a incerteza, fica abaixo de 1 ha
    n_marg = sum(1 for v_ in cota_normal if v_ - c['incerteza_ha'] < P['reservatorio_dispensa_ha'])
    c['medidas_cota_normal_marginais_lt_1ha'] = int(n_marg)
    c['dispensa_ambigua'] = bool((not c['dispensa_art4_par4_lt1ha']) and n_marg * 2 >= len(cota_normal))
    c['nota'] = ('massas contiguas tratadas como UM corpo; MNDWI>0 & NDVI<0,3 na seca e limite INFERIOR e nao decide a dispensa; '
                 'a cota normal (FBDS 2013, NDWI>0, JRC max_extent) decide, com banda +- perimetro x 5 m')
    corpos.append(c)
    log('  corpo %d (massas %s): FBDS2013 %.2f ha | NDWI>0 %.2f | MNDWI>-0,1 %.2f | JRC max_extent %.2f | MNDWI>0 seca %.2f | +-%.2f -> dispensa <1 ha = %s%s'
        % (c['corpo_id'], c['massa_ids'], c['area_fbds_2013_ha'], c['area_ndwi_gt0_2026_ha'], c['area_mndwi_gt_m01_2026_ha'],
           c['area_jrc_max_extent_ha'], c['area_s2_mndwi_2026_ha'], c['incerteza_ha'], c['dispensa_art4_par4_lt1ha'],
           ' (AMBIGUA)' if c['dispensa_ambigua'] else ''))
corpo_disp = {c['corpo_id']: c for c in corpos}
masas['corpo_area_fbds_2013_ha'] = masas['corpo_id'].map(lambda k: corpo_disp[k]['area_fbds_2013_ha'])
masas['dispensa_art4_par4_lt1ha'] = masas['corpo_id'].map(lambda k: corpo_disp[k]['dispensa_art4_par4_lt1ha'])
masas['dispensa_ambigua'] = masas['corpo_id'].map(lambda k: corpo_disp[k]['dispensa_ambigua'])
guardar_vector(masas.drop(columns=[c for c in ('Shape__Area', 'Shape__Length') if c in masas.columns]), 'massas_dagua_propriedade')
# agua S2 nueva (sin FBDS) tocando la propiedad
nuevas = agua_v[agua_v['intersecta_propriedade'] & agua_v['fbds_massa_id'].isna()]
nuevas_fp = nuevas[nuevas['possivel_falso_positivo']]
nuevas = nuevas[~nuevas['possivel_falso_positivo']]
if len(nuevas_fp):
    log('  %d cuerpo(s) "nuevo(s)" descartado(s) como superficie brillante (B2 %s)' % (len(nuevas_fp), nuevas_fp['b2_medio'].tolist()))
if len(nuevas):
    log('  !! %d cuerpo(s) de agua S2 tocando la propiedad SIN masa FBDS 2013 (posible represa post-2013): %s ha'
        % (len(nuevas), nuevas['area_ha'].tolist()))
RES['agua_s2'] = {'umbral_otsu_mndwi': round(t_otsu, 4), 'umbral_usado': round(umbral, 4), 'umbral_fuente': umbral_fuente,
                  'regla': 'MNDWI>umbral & NDVI<%.2f & SCL valido; sieve %d px' % (P['ndvi_max_agua'], P['sieve_agua_px']),
                  'n_cuerpos_aoi': len(agua_v), 'ha_aoi': ha(agua_v.geometry.area.sum()),
                  'n_cuerpos_tocam_propriedade': int(agua_v['intersecta_propriedade'].sum()),
                  'ha_dentro_propriedade': round(float(agua_v['dentro_propriedade_ha'].sum()), 3),
                  'cuerpos_novos_sem_fbds_2013': [{'agua_id': int(r.agua_id), 'area_ha': float(r.area_ha), 'jrc': r.jrc_occurrence_media}
                                                  for r in nuevas.itertuples()],
                  'falsos_positivos_brilhantes_propriedade': [{'agua_id': int(r.agua_id), 'area_ha': float(r.area_ha), 'b2': float(r.b2_medio)}
                                                              for r in nuevas_fp.itertuples()],
                  'massas_fbds_propriedade': [{k: (v.item() if hasattr(v, 'item') else v) for k, v in r.items() if k != 'geometry'}
                                              for _, r in masas.drop(columns=[c for c in ('Shape__Area', 'Shape__Length', 'arquivo', 'hidrografia', 'cod_ibge', 'municipio') if c in masas.columns]).iterrows()],
                  'corpos_dagua_propriedade': corpos,
                  'nota': 'cuerpos < %d px (%.2f ha) NO evaluables a 10 m; JRC v1.4 cubre 1984-2021' % (P['sieve_agua_px'], P['sieve_agua_px'] / 100)}

# ==============================================================================
# 4. Productos consolidados: lineas y nascentes
# ==============================================================================
titulo('4. hidrografia_consolidada + nascentes_consolidadas')
ibge_perm = ibge[ibge['regime'].map(sin_acentos) == 'permanente']
ibge_buf = unary_union(list(ibge_perm.geometry.buffer(P['tol_regime_m']))) if len(ibge_perm) else None
# BC250 so "respalda" o regime se DISCRIMINA: se todos os trechos do recorte sao "Permanente", o atributo
# nao separa nada e a coincidencia posicional nao e evidencia de perenidade (so de coincidencia com o IBGE)
ibge_regimes = ibge['regime'].map(sin_acentos).value_counts().to_dict() if len(ibge) else {}
ibge_discrimina = bool(len(ibge_perm) < len(ibge))
log('  IBGE BC250 no recorte: %d trechos, regimes %s -> %s' % (len(ibge), ibge_regimes,
    'discrimina regime' if ibge_discrimina else 'NAO discrimina (todos "Permanente"): "perene" = coincidencia posicional, nao evidencia'))


def regime_de(geom):
    if ibge_buf is None:
        return 'nao_classificado_campo', 0.0
    frac = geom.intersection(ibge_buf).length / geom.length if geom.length > 0 else 0
    return ('perene' if frac >= 0.5 else 'nao_classificado_campo'), round(float(frac), 2)


filas = []
for nombre, g, largura in (('FBDS', fbds_rios, 'ate_10m'), ('otto', otto, 'nao_informada'),
                           ('ANA', ana, 'nao_informada'), ('IBGE', ibge, 'nao_informada'), ('DEM', red, 'nao_aplica')):
    for _, r in g.iterrows():
        geom = r.geometry
        reg, frac = regime_de(geom)
        if nombre == 'IBGE':
            reg = 'perene' if sin_acentos(r.get('regime')) == 'permanente' else 'nao_classificado_campo'
        dentro = geom.intersection(PROP)
        filas.append({'fonte': nombre, 'id_fonte': str(r.get('objectid', r.get('OBJECTID', r.get('id', r.get('fbds_id', ''))))),
                      'largura_classe': largura, 'regime': reg, 'frac_coincide_ibge_perm': frac,
                      'dentro_propriedade': bool(not dentro.is_empty), 'comprimento_m': round(geom.length, 1),
                      'comprimento_dentro_m': round(dentro.length, 1),
                      'nome': str(r.get('nome', r.get('noriocomp', r.get('NORIOCOMP', '')) or '')),
                      'geometry': geom})
hidro = gpd.GeoDataFrame(filas, geometry='geometry', crs=CRS_METRICO)
guardar_vector(hidro, 'hidrografia_consolidada')
fb = hidro[(hidro.fonte == 'FBDS') & hidro.dentro_propriedade]
log('  FBDS dentro: %d tramos, %.3f km; regime perene (IBGE +-%d m): %.3f km; nao_classificado: %.3f km'
    % (len(fb), fb.comprimento_dentro_m.sum() / 1e3, P['tol_regime_m'],
       fb[fb.regime == 'perene'].comprimento_dentro_m.sum() / 1e3, fb[fb.regime != 'perene'].comprimento_dentro_m.sum() / 1e3))

# nascentes: FBDS + candidatos DEM (cabeceras de la red DEM)
starts = [Point(g.coords[0]) for g in red.geometry]
ends = [Point(g.coords[-1]) for g in red.geometry]
end_tree = STRtree(ends)
lin_tree = STRtree(list(red.geometry))
cabeceras = []
for s in starts:
    # cabecera = inicio que no es fin de otra rama y que no toca otra linea (salvo la propia)
    toca_fin = any(s.distance(ends[j]) < 1 for j in end_tree.query(s.buffer(1)))
    n_lineas = len(lin_tree.query(s.buffer(1)))
    if not toca_fin and n_lineas <= 1:
        cabeceras.append(s)
cabeceras = [c for c in cabeceras if c.within(PROP.buffer(P['margen_cabeceras_m']))]
hand_ok = np.where(hand_arr < 0, np.nan, hand_arr)
import rasterio
with rasterio.open(os.path.join(ANALISIS, 'HAND_30m.tif')) as hd:
    hand_vals = [list(hd.sample([(c.x, c.y)]))[0][0] for c in cabeceras]
nasc_rows = []
for _, r in fbds_nasc.iterrows():
    d_rios = fbds_rios.distance(r.geometry)
    d_min = float(d_rios.min())
    curso_id = int(fbds_rios.loc[d_rios.idxmin(), 'fbds_id']) if d_min <= 5 else None
    nasc_rows.append({'fonte': 'FBDS', 'id_fonte': str(r['objectid']), 'candidato_dem': False, 'validar_campo': True,
                      'dentro_propriedade': bool(r.geometry.within(PROP)),
                      'dist_nascente_fbds_m': 0.0, 'dist_curso_fbds_m': round(d_min, 1),
                      'curso_fbds_id': curso_id, 'conectada_curso_fbds': bool(curso_id is not None),
                      'dist_limite_propriedade_m': round(float(r.geometry.distance(PROP.boundary)), 1),
                      'hand_m': None, 'perenidade': 'nao_verificada',
                      'nota': 'nascente FBDS 2013 (RapidEye 5 m, 1:25.000); perenidade a confirmar em campo'
                              + ('; inicio do curso FBDS %d' % curso_id if curso_id else '; SEM curso FBDS conectado'),
                      'geometry': r.geometry})
n_cand = 0
for c, hv in zip(cabeceras, hand_vals):
    d = float(fbds_nasc.distance(c).min()) if len(fbds_nasc) else 9e9
    if d < P['dist_nascente_dem_m']:
        continue
    n_cand += 1
    d_rio = float(fbds_rios.distance(c).min()) if len(fbds_rios) else None
    nasc_rows.append({'fonte': 'DEM_GLO30_cabeceira', 'id_fonte': 'dem_%d' % n_cand, 'candidato_dem': True, 'validar_campo': True,
                      'dentro_propriedade': bool(c.within(PROP)), 'dist_nascente_fbds_m': round(d, 1),
                      'dist_curso_fbds_m': None if d_rio is None else round(d_rio, 1),
                      'curso_fbds_id': None, 'conectada_curso_fbds': bool(d_rio is not None and d_rio <= 5),
                      'dist_limite_propriedade_m': round(float(c.distance(PROP.boundary)), 1),
                      'hand_m': None if hv < 0 else round(float(hv), 1), 'perenidade': 'nao_verificada',
                      'nota': 'CANDIDATO: cabeceira da rede DEM (umbral %d ha) sem nascente FBDS a <%d m; nao e nascente ate verificacao em campo'
                              % (umbral_opt, P['dist_nascente_dem_m']),
                      'geometry': c})
nasc = gpd.GeoDataFrame(nasc_rows, geometry='geometry', crs=CRS_METRICO)
guardar_vector(nasc, 'nascentes_consolidadas')
n_fbds_in = int(((nasc.fonte == 'FBDS') & nasc.dentro_propriedade).sum())
n_dem_in = int((nasc.candidato_dem & nasc.dentro_propriedade).sum())
n_dem_100 = int(nasc.candidato_dem.sum())
log('  nascentes FBDS: %d en AOI, %d dentro de la propiedad' % (int((nasc.fonte == 'FBDS').sum()), n_fbds_in))
log('  candidatos DEM (cabeceras sin FBDS a <%d m, propiedad+%d m): %d (%d dentro de la propiedad)'
    % (P['dist_nascente_dem_m'], P['margen_cabeceras_m'], n_dem_100, n_dem_in))
for r in nasc[nasc.candidato_dem].itertuples():
    log('     %s  x=%.0f y=%.0f  dentro=%s  HAND=%s m  dist nascente FBDS=%.0f m  dist curso FBDS=%s m' % (r.id_fonte, r.geometry.x, r.geometry.y, r.dentro_propriedade, r.hand_m, r.dist_nascente_fbds_m, r.dist_curso_fbds_m))

# --- talvegue DEM a jusante de cada candidato: comprimento ate encostar (<= 30 m) na rede FBDS e APP potencial.
# Um candidato longe de qualquer curso oficial NAO e nascente; mas se em campo houver curso intermitente no
# talvegue, a APP (30 m do curso + 50 m da nascente) seria exigivel: quantifica-se como RISCO separado.
from shapely.ops import substring
lin_fbds_u = unary_union(list(fbds_rios.geometry))
app_fbds_u = unary_union([lin_fbds_u.buffer(P['app_curso_m']), unary_union(list(fbds_nasc.geometry)).buffer(P['app_nascente_m'])])
starts_tree = STRtree(starts)
mb10_, _ = leer_raster(R['mb_10m']); mb10_ = mb10_['classification_2025']
otras_bases = {'otto': otto, 'ANA': ana, 'IBGE': ibge}


def mb_moda(mask):
    if not mask.any():
        return None
    u_, c_ = np.unique(mb10_[mask], return_counts=True)
    return str(MB.get(int(u_[c_.argmax()]), int(u_[c_.argmax()])))


talv_rows = []
for r in nasc[nasc.candidato_dem].itertuples():
    cadena = []
    pt = r.geometry
    visitados = set()
    for _ in range(200):
        cand = [j for j in starts_tree.query(pt.buffer(1.0)) if starts[j].distance(pt) < 1.0 and j not in visitados]
        if not cand:
            break
        j = int(cand[0]); visitados.add(j)
        cadena.append(red.geometry.iloc[j]); pt = ends[j]
    if not cadena:
        continue
    L = linemerge(unary_union(cadena)) if len(cadena) > 1 else cadena[0]
    if L.geom_type != 'LineString':
        L = max(L.geoms, key=lambda g: g.length)
    # corte no primeiro ponto a <= 30 m da rede FBDS
    d_corte = L.length
    for dd in np.arange(0, L.length + 1e-6, 5.0):
        if L.interpolate(dd).distance(lin_fbds_u) <= P['app_curso_m']:
            d_corte = dd
            break
    if d_corte <= 0:
        continue
    talv = substring(L, 0, d_corte)
    app_pot = unary_union([talv.buffer(P['app_curso_m']), r.geometry.buffer(P['app_nascente_m'])]).intersection(PROP)
    app_pot_extra = app_pot.difference(app_fbds_u)
    # so o curso (30 m do talvegue), fora da APP FBDS e fora do circulo de 50 m do candidato (ja contado em ha_adicional_fora_app_exigivel)
    app_pot_curso = talv.buffer(P['app_curso_m']).intersection(PROP).difference(app_fbds_u).difference(r.geometry.buffer(P['app_nascente_m']))
    m_t = rasterizar([talv.buffer(10)], prof10) > 0
    d_bases = {k: (round(float(g.distance(talv).min()), 1) if len(g) else None) for k, g in otras_bases.items()}
    d_bases['FBDS'] = round(float(talv.distance(lin_fbds_u)), 1)
    fim = Point(talv.coords[-1])
    talv_rows.append({'id_fonte': r.id_fonte, 'comprimento_m': round(talv.length, 1),
                      'x_ini': round(talv.coords[0][0], 0), 'y_ini': round(talv.coords[0][1], 0),
                      'x_fim': round(fim.x, 0), 'y_fim': round(fim.y, 0),
                      'app_potencial_ha': ha(app_pot.area), 'app_potencial_fora_app_fbds_ha': ha(app_pot_extra.area),
                      'app_potencial_so_curso_fora_app_e_circulo_ha': ha(app_pot_curso.area),
                      'ndvi_medio': round(float(np.nanmean(idx['NDVI'][m_t])), 2) if m_t.any() else None,
                      'mndwi_medio': round(float(np.nanmean(idx['MNDWI'][m_t])), 2) if m_t.any() else None,
                      'mb_2025_moda': mb_moda(m_t),
                      'dist_min_bases_m': str(d_bases),
                      'nota': 'talvegue DEM sem curso em nenhuma base oficial; RISCO se houver curso intermitente (verificar em campo na estacao chuvosa)',
                      'geometry': talv})
    log('     talvegue DEM a jusante de %s: %.0f m (%.0f,%.0f -> %.0f,%.0f); APP potencial %.2f ha (fora da APP FBDS: %.2f ha; so curso, fora do circulo de 50 m: %.2f ha); NDVI %s MNDWI %s; MB2025 %s; dist minima a bases %s'
        % (r.id_fonte, talv.length, talv.coords[0][0], talv.coords[0][1], fim.x, fim.y, ha(app_pot.area), ha(app_pot_extra.area), ha(app_pot_curso.area),
           talv_rows[-1]['ndvi_medio'], talv_rows[-1]['mndwi_medio'], talv_rows[-1]['mb_2025_moda'], d_bases))
if talv_rows:
    guardar_vector(gpd.GeoDataFrame(talv_rows, geometry='geometry', crs=CRS_METRICO), 'talvegue_dem_candidatos')

# ==============================================================================
# 5. Tabla por fuente y desacuerdos
# ==============================================================================
titulo('5. Tabla fuente -> km dentro de la propiedad')
tabla = {}
for f in ('FBDS', 'otto', 'ANA', 'IBGE', 'DEM'):
    h = hidro[hidro.fonte == f]
    tabla[f] = {'km_dentro_propriedade': km(h.comprimento_dentro_m.sum()), 'n_tramos_dentro': int(h.dentro_propriedade.sum())}
tabla['FBDS']['n_nascentes_dentro'] = n_fbds_in
tabla['FBDS']['n_massas_dagua_intersectam'] = n_massas_dentro
tabla['DEM']['n_cabeceiras_candidatas_dentro'] = n_dem_in
tabla['DEM']['n_cabeceiras_candidatas_prop_100m'] = n_dem_100
log('  %-6s %10s %8s' % ('fonte', 'km dentro', 'tramos'))
for f, t in tabla.items():
    log('  %-6s %10.3f %8d' % (f, t['km_dentro_propriedade'], t['n_tramos_dentro']))
kmf = tabla['FBDS']['km_dentro_propriedade']
desac = {f: {'km_dentro': t['km_dentro_propriedade'], 'dif_vs_fbds_km': round(t['km_dentro_propriedade'] - kmf, 3),
             'dif_vs_fbds_pct': round(100 * (t['km_dentro_propriedade'] - kmf) / kmf, 1) if kmf else None}
         for f, t in tabla.items()}
log('  desacuerdo vs FBDS (%.3f km): %s' % (kmf, {f: d['dif_vs_fbds_km'] for f, d in desac.items()}))
RES['tabla_fontes_propriedade'] = tabla
RES['desacordo_fontes_vs_fbds'] = desac
talv_json = {t['id_fonte']: {k: v for k, v in t.items() if k != 'geometry'} for t in talv_rows}
RES['nascentes'] = {'fbds_dentro': n_fbds_in, 'fbds_aoi500': int((nasc.fonte == 'FBDS').sum()),
                    'candidatos_dem_dentro': n_dem_in, 'candidatos_dem_prop_100m': n_dem_100,
                    'fbds_lista': [{'id': r.id_fonte, 'x': round(r.geometry.x, 1), 'y': round(r.geometry.y, 1), 'dentro': r.dentro_propriedade,
                                    'curso_fbds_id': (int(r.curso_fbds_id) if r.curso_fbds_id is not None and r.curso_fbds_id == r.curso_fbds_id else None),
                                    'conectada_curso_fbds': bool(r.conectada_curso_fbds),
                                    'dist_curso_fbds_m': r.dist_curso_fbds_m, 'dist_limite_propriedade_m': r.dist_limite_propriedade_m}
                                   for r in nasc[nasc.fonte == 'FBDS'].itertuples()],
                    'candidatos': [{'id': r.id_fonte, 'x': round(r.geometry.x, 1), 'y': round(r.geometry.y, 1), 'dentro': r.dentro_propriedade,
                                    'hand_m': r.hand_m, 'dist_nascente_fbds_m': r.dist_nascente_fbds_m, 'dist_curso_fbds_m': r.dist_curso_fbds_m,
                                    'conectada_curso_fbds': r.conectada_curso_fbds,
                                    'mb_2025': mb_moda(rasterizar([r.geometry.buffer(15)], prof10) > 0),
                                    'talvegue_dem': talv_json.get(r.id_fonte)}
                                   for r in nasc[nasc.candidato_dem].itertuples()],
                    'nota': 'candidatos DEM NAO sao nascentes: rotulados candidato_dem=True, validar_campo=True; talvegue_dem = risco de APP se houver curso intermitente (nao somado)'}
RES['regime'] = {'criterio': 'perene se >=50%% do tramo a <=%d m de trecho IBGE BC250 regime Permanente; senao nao_classificado_campo' % P['tol_regime_m'],
                 'km_fbds_dentro_perene': km(fb[fb.regime == 'perene'].comprimento_dentro_m.sum()),
                 'km_fbds_dentro_nao_classificado': km(fb[fb.regime != 'perene'].comprimento_dentro_m.sum()),
                 'ibge_trechos_recorte': int(len(ibge)), 'ibge_trechos_permanente': int(len(ibge_perm)),
                 'ibge_regimes_recorte': ibge_regimes, 'ibge_discrimina_regime': ibge_discrimina,
                 'aviso': 'BC250 e 1:250.000 (erro posicional > 30 m): ausencia de coincidencia NAO significa intermitente'
                          + ('' if ibge_discrimina else '; e TODOS os %d trechos BC250 do recorte sao "Permanente": o atributo nao discrimina, '
                             '"perene" aqui = coincidencia posicional com o IBGE, nao evidencia de perenidade' % len(ibge))}
actualizar_resultados('hidrografia', RES)
log('an_01 listo en %.0f s' % (time.time() - T0))
