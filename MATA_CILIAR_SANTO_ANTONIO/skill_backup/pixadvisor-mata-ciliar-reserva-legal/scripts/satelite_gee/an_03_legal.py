# -*- coding: utf-8 -*-
"""an_03_legal.py — geometria legal (APP, reservatorio, area consolidada, RL) e mapa CAR.

Leito = rede FBDS (oficial, 2013, 1:25.000). A rede DEM entra so como controle.
Os buffers se medem desde a LINHA CENTRAL FBDS: como o leito regular de um curso
<=10 m tem borda a <=5 m do eixo, cada area APP se reporta como intervalo
[buffer 30 m ; buffer 30 + 3 m] e ainda +-10 m de incerteza posicional (1 px).

1. APP_curso_dagua_ate10m (+ controle DEM)          2. APP_nascente (+ candidatas DEM)
3. Reservatorio artificial por barramento (massas contiguas = UM corpo; sem presumir dispensa)
4. APP_total_exigivel (base) e cenario FBDS/IAT (+ faixa oficial de 30 m dos reservatorios); cobertura RF
5. Area rural consolidada / supressao pos-2008; cenarios A (integral) e B (PRA Lei PR 18.295)
6. Reserva Legal: exigida, disponivel, deficit, proposta (sem silvicultura/agua, 4-conexa, sem lascas < 0,05 ha)
7. Mapa de uso com nomenclatura CAR (sem sobreposicao, 100% do imovel) + capa separada do cenario FBDS/IAT
8. resultados_analisis.json (cifras + avisos calculados, nao copiados a mao)
"""
import os
import time

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import ndimage as ndi
from shapely.geometry import Point, MultiPolygon, Polygon, GeometryCollection
from shapely.ops import unary_union

from an_00_config import *  # noqa: F401,F403

T0 = time.time()
titulo('an_03_legal — APP, reservatorio, area consolidada, RL, mapa CAR  (%s)' % FECHA_ESCENA)
prop = propiedad()
PROP = prop['geom']
AREA_IMOVEL = prop['area_ha']
LEG = leer_json(PARAMETROS_LEGALES)
RL_PCT = LEG['rl_pct']
RL_HA = round(AREA_IMOVEL * RL_PCT, 2)
log('Imovel %.2f ha; RL %d%% = %.2f ha (servidoes administrativas: sem dado, assumidas 0 — IN MMA 2/2014 art. 23)'
    % (AREA_IMOVEL, RL_PCT * 100, RL_HA))
RES = {'fecha_escena': FECHA_ESCENA, 'imovel_ha': round(AREA_IMOVEL, 2), 'rl_pct': RL_PCT, 'rl_exigida_ha': RL_HA}
AV = []   # avisos


def poly_only(g):
    """Deja solo la parte poligonal de una geometria (sin lineas/puntos de GeometryCollection)."""
    if g is None or g.is_empty:
        return Polygon()
    if isinstance(g, (Polygon, MultiPolygon)):
        return g
    if isinstance(g, GeometryCollection):
        parts = [p for p in g.geoms if isinstance(p, (Polygon, MultiPolygon)) and not p.is_empty]
        return unary_union(parts) if parts else Polygon()
    return Polygon()


def A(g):
    return round(poly_only(g).area / 1e4, 2)


def clip(g):
    return poly_only(g.intersection(PROP))


# --- insumos -------------------------------------------------------------------
hidro = gpd.read_file(os.path.join(ANALISIS, 'hidrografia_consolidada.geojson'))
fbds = hidro[hidro.fonte == 'FBDS']
dem_red = hidro[hidro.fonte == 'DEM']
nasc = gpd.read_file(os.path.join(ANALISIS, 'nascentes_consolidadas.geojson'))
masas = gpd.read_file(os.path.join(ANALISIS, 'massas_dagua_propriedade.geojson'))
veg_r, prof10 = leer_raster(os.path.join(ANALISIS, 'vegetacao_10m_%s.tif' % FECHA_ESCENA))
veg_r = veg_r['classe']
idx, _ = leer_raster(R['indices'])
mb10, _ = leer_raster(R['mb_10m']); mb10 = mb10['classification_2025']
mb08 = remuestrear_a(R['mb_hist'], prof10, banda=2, metodo='nearest')
mb85 = remuestrear_a(R['mb_hist'], prof10, banda=3, metodo='nearest')
veg_v = gpd.read_file(os.path.join(ANALISIS, 'vegetacao_nativa_10m.geojson'))
FLORESTA = unary_union(list(veg_v[veg_v.classe == 'FLORESTA_NATIVA'].geometry))
AGUA = unary_union(list(veg_v[veg_v.classe == 'AGUA'].geometry))
SILVI = unary_union(list(veg_v[veg_v.classe == 'SILVICULTURA'].geometry)) if (veg_v.classe == 'SILVICULTURA').any() else Polygon()
# floresta "com historico" (MB 2008 floresta ou FBDS 2013 floresta): variante conservadora
uso13 = leer_vector('fbds_uso2013', PROP)
uso13['classe'] = uso13['classe_uso'].map(sin_acentos)
FL13 = unary_union(list(uso13[uso13.classe.str.contains('florestal')].geometry)) if len(uso13) else Polygon()
fl08_v = vectorizar(np.isin(mb08, list(MB_FLORESTA)).astype(np.uint8), prof10, 'v')
FL08 = unary_union(list(fl08_v.geometry)) if len(fl08_v) else Polygon()
FLORESTA_HIST = poly_only(FLORESTA.intersection(unary_union([FL13, FL08])))
log('  floresta RF dentro: %.2f ha; com historico (MB2008 ou FBDS2013): %.2f ha' % (A(clip(FLORESTA)), A(clip(FLORESTA_HIST))))

# ==============================================================================
# 1. APP curso d'agua <= 10 m
# ==============================================================================
titulo("1. APP curso d'agua ate 10 m (buffer %d m do eixo FBDS)" % P['app_curso_m'])
lin_fbds = unary_union(list(fbds.geometry))
lin_dem = unary_union(list(dem_red.geometry))
B = P['app_curso_m']; MA = P['media_anchura_curso_m']; INC = P['incert_pos_m']
app_curso = {'central': clip(lin_fbds.buffer(B)), 'borda_calha': clip(lin_fbds.buffer(B + MA)),
             'min': clip(lin_fbds.buffer(B - INC)), 'max': clip(lin_fbds.buffer(B + MA + INC))}
app_curso_dem = clip(lin_dem.buffer(B))
iou = app_curso['central'].intersection(app_curso_dem).area / app_curso['central'].union(app_curso_dem).area
for k, g in app_curso.items():
    log('  APP curso %-12s %.2f ha' % (k, A(g)))
log('  controle DEM: %.2f ha; IoU FBDS/DEM = %.2f' % (A(app_curso_dem), iou))
RES['app_curso_dagua_ate10m'] = {'ha': A(app_curso['central']), 'ha_borda_calha_33m': A(app_curso['borda_calha']),
                                 'ha_min_20m': A(app_curso['min']), 'ha_max_43m': A(app_curso['max']),
                                 'km_curso_fbds_dentro': km(lin_fbds.intersection(PROP).length),
                                 'controle_dem_ha': A(app_curso_dem), 'iou_fbds_dem': round(iou, 3),
                                 'origem': 'buffer %d m do eixo FBDS (ate 10 m); leito regular nao levantado' % B}

# ==============================================================================
# 2. APP nascente
# ==============================================================================
titulo('2. APP nascente (raio %d m)' % P['app_nascente_m'])
n_fbds = nasc[nasc.fonte == 'FBDS']
n_dem = nasc[nasc.candidato_dem == True]  # noqa: E712
RN = P['app_nascente_m']
pts = unary_union(list(n_fbds.geometry))
app_nasc = {'central': clip(pts.buffer(RN)), 'min': clip(pts.buffer(RN - INC)), 'max': clip(pts.buffer(RN + INC))}
app_nasc_dem = clip(unary_union(list(n_dem.geometry)).buffer(RN)) if len(n_dem) else Polygon()
app_nasc_dem_extra = poly_only(app_nasc_dem.difference(unary_union([app_curso['central'], app_nasc['central']])))
for k, g in app_nasc.items():
    log('  APP nascente %-8s %.2f ha (nascentes FBDS que geram APP no imovel: %d)' % (k, A(g), int(n_fbds.geometry.buffer(RN).intersects(PROP).sum())))
log('  candidatas DEM (%d): %.2f ha, dos quais %.2f ha fora da APP ja exigivel (RISCO, nao somado)' % (len(n_dem), A(app_nasc_dem), A(app_nasc_dem_extra)))
RES['app_nascente'] = {'ha': A(app_nasc['central']), 'ha_min_40m': A(app_nasc['min']), 'ha_max_60m': A(app_nasc['max']),
                       'n_nascentes_fbds_dentro': int(n_fbds.dentro_propriedade.sum()),
                       'n_nascentes_fbds_geram_app': int(n_fbds.geometry.buffer(RN).intersects(PROP).sum()),
                       'perenidade': 'NAO verificada (art. 4 IV exige perene; STF ADI 4903: intermitente tambem)',
                       'candidatas_dem': {'n': len(n_dem), 'ha_app_50m': A(app_nasc_dem), 'ha_adicional_fora_app_exigivel': A(app_nasc_dem_extra),
                                          'nota': 'RISCO: se confirmadas em campo, somam APP; nao incluidas no total'}}

# ==============================================================================
# 3. Reservatorio artificial por barramento de curso natural
# ==============================================================================
titulo('3. Reservatorio artificial decorrente de barramento (art. 4 III, par. 1, par. 4)')
HJ = leer_json(RESULTADOS_JSON)['hidrografia']
corpos = HJ['agua_s2'].get('corpos_dagua_propriedade', [])
corpo_de = {int(mid): c for c in corpos for mid in c['massa_ids']}
res_list = []
esp_union = Polygon()
faixa30_union = Polygon()
corpo_rf = {}
for cid in {c['corpo_id'] for c in corpos}:
    g_c = unary_union(list(masas[masas.corpo_id == cid].geometry))
    corpo_rf[cid] = A(clip(AGUA.intersection(g_c.buffer(20))))
for r in masas.itertuples():
    esp_fbds = clip(r.geometry)
    esp_s2 = clip(AGUA.intersection(r.geometry.buffer(20)))
    faixa30 = poly_only(clip(r.geometry.buffer(P['reservatorio_faixa_ref_m'])).difference(r.geometry))
    faixa30_extra = poly_only(faixa30.difference(unary_union([app_curso['central'], app_nasc['central']])))
    c = corpo_de.get(int(r.massa_id), {})
    medidas_ge1 = {'fbds_2013': c.get('area_fbds_2013_ha'), 'ndwi_gt0_2026': c.get('area_ndwi_gt0_2026_ha'),
                   'jrc_max_extent_1984_2021': c.get('area_jrc_max_extent_ha'), 'rf_agua_2026': corpo_rf.get(c.get('corpo_id'))}
    d = {'massa_id': int(r.massa_id), 'natureza': r.natureza, 'barramento_curso_natural': bool(r.barramento_curso_natural),
         'espelho_fbds_2013_ha': A(esp_fbds), 'espelho_s2_mndwi_2026_ha': round(float(r.area_s2_2026_ha), 2),
         'espelho_rf_agua_2026_ha': A(esp_s2), 'jrc_occurrence_media': r.jrc_occurrence_media,
         'espelho_ndwi_gt0_2026_ha': round(float(getattr(r, 'area_ndwi_gt0_2026_ha', float('nan'))), 2),
         'espelho_jrc_max_extent_ha': round(float(getattr(r, 'area_jrc_max_extent_ha', float('nan'))), 2),
         'corpo_id': c.get('corpo_id'), 'corpo_massa_ids': c.get('massa_ids'),
         'corpo_espelho_ha': medidas_ge1,
         'dispensa_art4_par4': bool(c.get('dispensa_art4_par4_lt1ha', False)),
         'dispensa_ambigua': bool(c.get('dispensa_ambigua', False)),
         'justificativa_dispensa': ('NAO se presume a dispensa do art. 4 par. 4: as massas FBDS %s sao contiguas (distancia 0 m) e formam UM corpo; '
                                    'a unica medida < 1 ha e a lamina de agua clara na seca (MNDWI>0 & NDVI<0,3 = limite inferior); '
                                    'a cota normal excede 1 ha (FBDS 2013 %.2f / NDWI>0 %.2f / JRC max_extent %.2f / RF 2026 %.2f ha). '
                                    'Tratar como >= 1 ha ate levantamento da cota maxima normal / licenca'
                                    % (c.get('massa_ids'), medidas_ge1['fbds_2013'] or 0, medidas_ge1['ndwi_gt0_2026'] or 0,
                                       medidas_ge1['jrc_max_extent_1984_2021'] or 0, medidas_ge1['rf_agua_2026'] or 0))
                                   if not c.get('dispensa_art4_par4_lt1ha', False) else 'corpo < 1 ha em todas as medidas a cota normal (+ incerteza)',
         'faixa': 'a definir pelo IAT / licenca (art. 4 III); sem licenca conhecida; cenario FBDS/IAT = 30 m (base app_hidrica FBDS)',
         'cenario_0m_ha': 0.0, 'cenario_30m_ha': A(faixa30), 'cenario_30m_adicional_fora_app_ha': A(faixa30_extra)}
    res_list.append(d)
    esp_union = unary_union([esp_union, esp_fbds]); faixa30_union = unary_union([faixa30_union, faixa30])
    log('  massa %d (corpo %s): espelho FBDS2013 %.2f ha / MNDWI-2026 %.2f ha / RF-agua-2026 %.2f ha; barramento=%s; dispensa <1 ha=%s%s; faixa 30 m = %.2f ha (adicional fora da APP: %.2f)'
        % (d['massa_id'], d['corpo_id'], d['espelho_fbds_2013_ha'], d['espelho_s2_mndwi_2026_ha'], d['espelho_rf_agua_2026_ha'], d['barramento_curso_natural'], d['dispensa_art4_par4'],
           ' (AMBIGUA)' if d['dispensa_ambigua'] else '', d['cenario_30m_ha'], d['cenario_30m_adicional_fora_app_ha']))
# espelho = FBDS 2013 U RF agua 2026 (dentro do imovel); faixa 30 m ao redor do espelho (cenario proprio)
ESPELHO = poly_only(unary_union([esp_union, clip(AGUA)]))
FAIXA_ESP = poly_only(clip(ESPELHO.buffer(P['reservatorio_faixa_ref_m'])).difference(ESPELHO))
# capa OFICIAL FBDS/IAT app_hidrica: poligonos "massa d'agua" (30 m) dentro do imovel
fbds_app = leer_vector('fbds_app', PROP)
fbds_app['tipo'] = fbds_app['hidrografia'].map(sin_acentos)
fa_massa = fbds_app[fbds_app.tipo.str.contains('massa')]
# a faixa oficial e o anel de 30 m ao redor do espelho FBDS 2013 (ja recortado ao imovel por leer_vector); so se desconta o espelho FBDS.
# A agua RF 2026 que cai no anel fica como "agua" no desglose do cenario (nao se subtrai aqui).
FAIXA_OFICIAL = poly_only(unary_union(list(fa_massa.geometry)).difference(esp_union)) if len(fa_massa) else Polygon()
log('  espelho FBDS U RF dentro: %.2f ha; faixa 30 m ao redor (propria): %.2f ha; faixa OFICIAL FBDS app_hidrica "massa d agua" dentro: %.2f ha (objectid %s)'
    % (A(ESPELHO), A(FAIXA_ESP), A(FAIXA_OFICIAL), fa_massa.objectid.astype(int).unique().tolist() if len(fa_massa) else []))
RES['reservatorio_artificial'] = {'lista': res_list, 'corpos_dagua': corpos,
                                  'espelho_fbds_total_ha': A(esp_union),
                                  'espelho_rf_agua_2026_total_ha': A(clip(AGUA)),
                                  'espelho_fbds_ou_rf_total_ha': A(ESPELHO),
                                  'cenario_30m_total_ha': A(faixa30_union),
                                  'cenario_30m_adicional_fora_app_total_ha': A(poly_only(faixa30_union.difference(unary_union([app_curso['central'], app_nasc['central']])))),
                                  'cenario_30m_espelho_fbds_rf_ha': A(FAIXA_ESP),
                                  'faixa_oficial_fbds_app_hidrica_dentro_ha': A(FAIXA_OFICIAL),
                                  'faixa_oficial_fbds_objectids': fa_massa.objectid.astype(int).unique().tolist() if len(fa_massa) else [],
                                  'espelho_mndwi_2026_total_ha': round(float(masas.area_s2_2026_ha.sum()), 2),
                                  'dispensa_art4_par4_algum': bool(any(d['dispensa_art4_par4'] for d in res_list)),
                                  'nota': 'NAO somado ao total exigivel (base); reportado como cenario FBDS/IAT (a capa oficial app_hidrica FBDS mapeia 30 m para ambos). '
                                          'Espelho: FBDS 2013 (nivel de referencia) vs MNDWI 29-ago-2026 (agua clara, estacao seca: limite inferior) vs RF agua 2026 '
                                          '(inclui margens umidas: superestima). Massas contiguas = UM corpo para o teste de 1 ha'}
for c in corpos:
    if not c['dispensa_art4_par4_lt1ha']:
        AV.append('Reservatorio (massas FBDS %s, contiguas = UM corpo): nao se presume a dispensa do art. 4 par. 4 — a unica medida < 1 ha e a lamina de agua clara na seca '
                  '(MNDWI 2026 %.2f ha, limite inferior); a cota normal excede 1 ha (FBDS 2013 %.2f, NDWI>0 %.2f, JRC max_extent %.2f, RF 2026 %.2f ha). '
                  'Tratar como >= 1 ha ate levantamento da cota maxima normal / licenca'
                  % (c['massa_ids'], c['area_s2_mndwi_2026_ha'], c['area_fbds_2013_ha'], c['area_ndwi_gt0_2026_ha'], c['area_jrc_max_extent_ha'], corpo_rf.get(c['corpo_id'], 0)))

# ==============================================================================
# 4. APP total exigivel e cobertura
# ==============================================================================
titulo('4. APP total exigivel = curso + nascente; cobertura RF 10 m')
APP = unary_union([app_curso['central'], app_nasc['central']])
APP_min = unary_union([app_curso['min'], app_nasc['min']])
APP_max = unary_union([app_curso['max'], app_nasc['max']])
app_veg = poly_only(APP.intersection(FLORESTA))
app_agua = poly_only(APP.intersection(AGUA).difference(app_veg))
app_sem = poly_only(APP.difference(unary_union([app_veg, app_agua])))
app_silvi = poly_only(app_sem.intersection(SILVI))
log('  APP exigivel: %.2f ha  [min %.2f ; max %.2f]' % (A(APP), A(APP_min), A(APP_max)))
log('  com vegetacao nativa (conforme): %.2f ha (%.0f%%)' % (A(app_veg), 100 * app_veg.area / APP.area))
log('  agua: %.2f ha | sem vegetacao (a recompor): %.2f ha (silvicultura dentro: %.2f)' % (A(app_agua), A(app_sem), A(app_silvi)))
# FBDS 2013 app_uso dentro do imovel
app_uso13 = leer_vector('fbds_app_uso', PROP)
app_uso13['classe'] = app_uso13['classe_uso'].map(sin_acentos)
t13 = app_uso13.assign(a=app_uso13.geometry.area / 1e4).groupby('classe')['a'].sum().round(2).to_dict()
log('  FBDS APP hidrica 2013 dentro: %.2f ha; uso 2013 dentro da APP FBDS: %s' % (fbds_app.geometry.area.sum() / 1e4, t13))
# mesma APP (nossa) com o uso 2013 FBDS -> evolucao 2013 -> 2026
uso13_fl_app = A(APP.intersection(FL13))
# --- cenario FBDS/IAT: APP base + faixa oficial FBDS de 30 m dos reservatorios (app_hidrica "massa d'agua")
APP_F = poly_only(unary_union([APP, FAIXA_OFICIAL]))
appF_veg = poly_only(APP_F.intersection(FLORESTA))
appF_agua = poly_only(APP_F.intersection(AGUA).difference(appF_veg))
appF_sem = poly_only(APP_F.difference(unary_union([appF_veg, appF_agua])))
appF_silvi = poly_only(appF_sem.intersection(SILVI))
FAIXA_ADIC = poly_only(FAIXA_OFICIAL.difference(APP))
log('  CENARIO FBDS/IAT: APP %.2f ha (= base %.2f + faixa reservatorio adicional %.2f); conforme %.2f | agua %.2f | a recompor %.2f (silvicultura %.2f)'
    % (A(APP_F), A(APP), A(FAIXA_ADIC), A(appF_veg), A(appF_agua), A(appF_sem), A(appF_silvi)))
RES['app_total_exigivel'] = {'ha': A(APP), 'ha_min': A(APP_min), 'ha_max': A(APP_max),
                             'com_vegetacao_nativa_ha': A(app_veg), 'agua_ha': A(app_agua), 'sem_vegetacao_ha': A(app_sem),
                             'sem_vegetacao_silvicultura_ha': A(app_silvi),
                             'pct_conforme': round(100 * app_veg.area / APP.area, 1),
                             'pct_conforme_incl_agua': round(100 * (app_veg.area + app_agua.area) / APP.area, 1),
                             'app_total_exigivel_ha': A(APP),
                             'app_total_cenario_fbds_ha': A(APP_F),
                             'cenario_fbds_iat': {'ha': A(APP_F), 'faixa_reservatorio_adicional_ha': A(FAIXA_ADIC),
                                                  'faixa_oficial_fbds_dentro_ha': A(FAIXA_OFICIAL),
                                                  'com_vegetacao_nativa_ha': A(appF_veg), 'agua_ha': A(appF_agua), 'sem_vegetacao_ha': A(appF_sem),
                                                  'sem_vegetacao_silvicultura_ha': A(appF_silvi),
                                                  'pct_conforme': round(100 * appF_veg.area / APP_F.area, 1),
                                                  'base': 'IAT_FBDS_app_hidrica (massa d agua, 30 m) U APP base; provavel base do Modulo de Analise do IAT (nao verificado)'},
                             'fbds_2013': {'app_hidrica_fbds_dentro_ha': ha(fbds_app.geometry.area.sum()), 'uso_2013_dentro_app_fbds_ha': t13,
                                           'floresta_2013_dentro_da_nossa_app_ha': uso13_fl_app},
                             'evolucao_2013_2026': 'floresta na APP: %.2f ha (FBDS 2013, mesma APP) -> %.2f ha (RF 2026)' % (uso13_fl_app, A(app_veg))}

# ==============================================================================
# 5. Area rural consolidada e cenarios de recomposicao
# ==============================================================================
titulo('5. Area consolidada (corte 22/07/2008) e cenarios A (integral) / B (PRA Lei PR 18.295 art. 17 par. 2)')
fl08_or_agua = vectorizar(np.isin(mb08, list(MB_FLORESTA | MB_AGUA)).astype(np.uint8), prof10, 'v')
NAT08 = unary_union(list(fl08_or_agua.geometry)) if len(fl08_or_agua) else Polygon()
consol = poly_only(app_sem.difference(NAT08))            # uso antropico em 2008 -> elegivel 61-A
supr = poly_only(app_sem.intersection(NAT08))            # floresta/agua em 2008 -> supressao pos-2008 (nao elegivel)
log('  APP sem vegetacao: %.2f ha = consolidada (MB2008 antropico) %.2f ha + supressao pos-2008 (MB2008 floresta/agua) %.2f ha'
    % (A(app_sem), A(consol), A(supr)))
# cenario B: faixa PRA 20 m do eixo + raio 15 m nascente, so sobre consolidada; nao consolidada integral
faixa_pra = unary_union([clip(lin_fbds.buffer(P['pra_curso_m'])), clip(pts.buffer(P['pra_nascente_m']))])
recomp_B_consol = poly_only(consol.intersection(faixa_pra))
excedente_B = poly_only(consol.difference(faixa_pra))     # entre 20 e 30 m: consolidada mantida
recomp_B = unary_union([recomp_B_consol, supr])
faixa_pra_bc = unary_union([clip(lin_fbds.buffer(P['pra_curso_m'] + MA)), clip(pts.buffer(P['pra_nascente_m']))])
recomp_B_bc = unary_union([poly_only(consol.intersection(faixa_pra_bc)), supr])
cenA = A(app_sem); cenB = A(recomp_B)
cenA_F = A(appF_sem)
log('  Cenario A (integral 30/50 m): recompor %.2f ha  [cenario FBDS/IAT: %.2f ha]' % (cenA, cenA_F))
log('  Cenario B (PRA 20 m / 15 m): recompor %.2f ha (= %.2f consolidada na faixa + %.2f supressao pos-2008); excedente mantido %.2f ha; com borda da calha (23 m): %.2f ha'
    % (cenB, A(recomp_B_consol), A(supr), A(excedente_B), A(recomp_B_bc)))
RES['area_consolidada_app'] = {'app_sem_vegetacao_ha': A(app_sem), 'consolidada_elegivel_61A_ha': A(consol), 'supressao_pos_2008_ha': A(supr),
                               'criterio': 'MapBiomas col11 2008 (30 m -> 10 m nearest): antropico = elegivel; floresta/agua = supressao (indicio, nao prova)',
                               'cenario_A_integral_ha': cenA, 'cenario_A_min_ha': A(poly_only(APP_min.difference(unary_union([FLORESTA, AGUA])))),
                               'cenario_A_max_ha': A(poly_only(APP_max.difference(unary_union([FLORESTA, AGUA])))),
                               'cenario_A_cenario_fbds_ha': cenA_F,
                               'cenario_B_pra_ha': cenB, 'cenario_B_pra_borda_calha_23m_ha': A(recomp_B_bc),
                               'cenario_B_consolidada_na_faixa_ha': A(recomp_B_consol),
                               'cenario_B_supressao_integral_ha': A(supr), 'cenario_B_excedente_mantido_ha': A(excedente_B),
                               'base_B': 'Lei PR 18.295/2014 art. 17 par. 2 (4-10 MF): 20 m em cursos <=10 m; nascente raio 15 m; exige CAR ate 31/12/2023 e adesao ao PRA'}

# ==============================================================================
# 6. Reserva Legal
# ==============================================================================
titulo('6. Reserva Legal: exigida %.2f ha' % RL_HA)
rem = poly_only(clip(FLORESTA).difference(APP))                       # remanescente fora da APP
rem_hist = poly_only(clip(FLORESTA_HIST).difference(APP))
app_veg_hist = poly_only(APP.intersection(FLORESTA_HIST))
rl = {'exigida_ha': RL_HA, 'remanescente_fora_app_ha': A(rem), 'app_com_vegetacao_ha': A(app_veg),
      'disponivel_sem_app_ha': A(rem), 'disponivel_com_app_art15_ha': A(unary_union([rem, app_veg])),
      'deficit_sem_app_ha': round(max(0.0, RL_HA - A(rem)), 2),
      'deficit_com_app_art15_ha': round(max(0.0, RL_HA - A(unary_union([rem, app_veg]))), 2),
      'variante_conservadora_floresta_com_historico': {
          'remanescente_fora_app_ha': A(rem_hist), 'app_com_vegetacao_ha': A(app_veg_hist),
          'deficit_sem_app_ha': round(max(0.0, RL_HA - A(rem_hist)), 2),
          'deficit_com_app_art15_ha': round(max(0.0, RL_HA - A(unary_union([rem_hist, app_veg_hist]))), 2),
          'nota': 'so floresta RF que ja era floresta em MB 2008 ou FBDS 2013; exclui a faixa ciliar jovem (frag. 13) ate confirmacao em campo'},
      'incerteza_floresta_ha': leer_json(RESULTADOS_JSON)['vegetacao']['cobertura_propriedade']['floresta_incerteza_ha'],
      'servidoes_administrativas': 'sem dado; assumidas 0 ha (IN MMA 2/2014 art. 23 I)',
      'compensacao_art66_III_ha_minima': None}
rl['compensacao_art66_III_ha_minima'] = rl['deficit_com_app_art15_ha']
log('  remanescente fora da APP: %.2f ha | APP vegetada (art. 15): %.2f ha' % (rl['remanescente_fora_app_ha'], rl['app_com_vegetacao_ha']))
log('  disponivel: sem APP %.2f ha -> deficit %.2f | com APP %.2f ha -> deficit %.2f'
    % (rl['disponivel_sem_app_ha'], rl['deficit_sem_app_ha'], rl['disponivel_com_app_art15_ha'], rl['deficit_com_app_art15_ha']))
v = rl['variante_conservadora_floresta_com_historico']
log('  conservador (floresta com historico): rem %.2f + APP veg %.2f -> deficit com APP %.2f' % (v['remanescente_fora_app_ha'], v['app_com_vegetacao_ha'], v['deficit_com_app_art15_ha']))

# proposta de localizacao: remanescentes + APP computavel (sem agua, SEM silvicultura) + corredor por dilatacao iterativa.
# Regras: silvicultura (RF 4) nao e vegetacao nativa -> fora da semente e do corredor; dilatacao 4-conexa (sem lascas
# diagonais); partes < 0,05 ha eliminadas e compensadas; composicao calculada da geometria FINAL.
MIN_PARTE_HA = 0.05
prop10 = rasterizar([PROP], prof10) > 0
agua10 = veg_r == 2
silvi10 = veg_r == 4
APP_COMP = poly_only(APP.difference(unary_union([AGUA, SILVI])))       # APP computavel (art. 15): sem agua, sem plantio
NUCLEO = poly_only(unary_union([rem, APP_COMP]))


def partes(g):
    g = poly_only(g)
    if g.is_empty:
        return []
    return list(g.geoms) if g.geom_type == 'MultiPolygon' else [g]


def sem_lascas(g, minimo=MIN_PARTE_HA):
    ps = partes(g)
    keep = [p for p in ps if p.area / 1e4 >= minimo]
    drop = [p for p in ps if p.area / 1e4 < minimo]
    return (unary_union(keep) if keep else Polygon()), drop


NUCLEO_OK, lascas_nucleo = sem_lascas(NUCLEO)
log('  nucleo (remanescente %.2f + APP computavel %.2f = %.2f ha); silvicultura excluida da APP: %.2f ha; lascas < %.2f ha do nucleo removidas: %d (%.3f ha)'
    % (A(rem), A(APP_COMP), A(NUCLEO), A(poly_only(APP.intersection(SILVI))), MIN_PARTE_HA, len(lascas_nucleo), sum(p.area for p in lascas_nucleo) / 1e4))
semilla = rasterizar([NUCLEO_OK], prof10) > 0
livre = prop10 & ~agua10 & ~silvi10
semilla &= livre
ESTR4 = ndi.generate_binary_structure(2, 1)      # 4-conectividade
alvo_px = int(round(RL_HA * 100))
atual = semilla.copy()
mosaico = np.isin(mb10, [21, 15])              # nao cultivado (mosaico/pastagem) primeiro
ndvi = np.nan_to_num(idx['NDVI'], nan=1.0)


def rl_vec(m):
    g = clip(unary_union(list(vectorizar(m.astype(np.uint8), prof10, 'v').geometry)))
    g = poly_only(unary_union([g, NUCLEO_OK]))       # o nucleo vetorial entra inteiro (sem perder bordas na rasterizacao)
    return sem_lascas(g)


def crescer(n_px):
    anel = ndi.binary_dilation(atual, structure=ESTR4) & ~atual & livre
    if not anel.any():
        return False
    ii = np.flatnonzero(anel.ravel())
    if len(ii) > n_px:
        chave = np.lexsort((ndvi.ravel()[ii], (~mosaico.ravel()[ii]).astype(int)))
        ii = ii[chave[:n_px]]
    atual.ravel()[ii] = True
    return True


it = 0
while atual.sum() < alvo_px and it < 500:
    it += 1
    if not crescer(alvo_px - int(atual.sum())):
        break
RL_PROP, lascas_rl = rl_vec(atual)
# o recorte vetorial e a remocao de lascas perdem area: seguir crescendo em lotes de 5 px ate a area FINAL >= RL
while A(RL_PROP) < RL_HA and it < 900:
    it += 1
    if not crescer(5):
        break
    RL_PROP, lascas_rl = rl_vec(atual)
# composicao a partir da geometria FINAL
app_rec_comp = poly_only(APP_COMP.difference(FLORESTA))               # APP a recompor computavel (sem agua, sem silvicultura)
rem_in = poly_only(RL_PROP.intersection(rem))
appv_in = poly_only(RL_PROP.intersection(app_veg))
appr_in = poly_only(RL_PROP.intersection(app_rec_comp))
corredor = poly_only(RL_PROP.difference(NUCLEO))
tot_ha = A(RL_PROP)
rem_ha, appv_ha, appr_ha = A(rem_in), A(appv_in), A(appr_in)
corr_ha = round(tot_ha - rem_ha - appv_ha - appr_ha, 2)
assert abs(corr_ha - A(corredor)) <= 0.02, 'composicao nao fecha: corredor %.3f vs %.3f' % (corr_ha, A(corredor))
ps = sorted([round(p.area / 1e4, 2) for p in partes(RL_PROP)], reverse=True)
log('  RL proposta: %.2f ha em %d iteracoes = remanescente %.2f + APP vegetada %.2f + APP a recompor %.2f + corredor de recomposicao %.2f (soma %.2f)'
    % (tot_ha, it, rem_ha, appv_ha, appr_ha, corr_ha, rem_ha + appv_ha + appr_ha + corr_ha))
log('  RL proposta: %d parte(s) %s ha; lascas < %.2f ha removidas: %d; silvicultura dentro %.2f ha; agua dentro %.2f ha; RL >= exigida: %s'
    % (len(ps), ps, MIN_PARTE_HA, len(lascas_rl), A(RL_PROP.intersection(SILVI)), A(RL_PROP.intersection(AGUA)), tot_ha >= RL_HA))
if tot_ha < RL_HA:
    raise RuntimeError('RL proposta %.2f < exigida %.2f' % (tot_ha, RL_HA))
rl['proposta'] = {'ha': tot_ha, 'remanescente_ha': rem_ha, 'app_incluida_ha': round(appv_ha + appr_ha, 2), 'app_vegetada_ha': appv_ha,
                  'app_a_recompor_incluida_ha': appr_ha, 'app_agua_incluida_ha': A(poly_only(RL_PROP.intersection(AGUA))),
                  'silvicultura_incluida_ha': A(poly_only(RL_PROP.intersection(SILVI))),
                  'silvicultura_excluida_da_app_ha': A(poly_only(APP.intersection(SILVI))),
                  'remanescente_fora_da_proposta_ha': round(A(rem) - rem_ha, 2),
                  'corredor_recomposicao_ha': corr_ha, 'iteracoes_dilatacao_10m': it,
                  'soma_composicao_ha': round(rem_ha + appv_ha + appr_ha + corr_ha, 2),
                  'n_partes': len(ps), 'partes_ha': ps, 'parte_minima_ha': MIN_PARTE_HA,
                  'lascas_removidas_n': len(lascas_rl) + len(lascas_nucleo),
                  'lascas_removidas_ha': round(sum(p.area for p in lascas_rl + lascas_nucleo) / 1e4, 3),
                  'criterio': 'art. 14: %d bloco(s), cada um contiguo a APP/remanescente; silvicultura e agua excluidas; dilatacao iterativa 10 m 4-conexa; '
                              'prioridade MB 21/15 (nao cultivado) e menor NDVI; partes < %.2f ha eliminadas e compensadas' % (len(ps), MIN_PARTE_HA),
                  'status': 'PROPOSTA sujeita a aprovacao do IAT; APP so computa na RL se CAR inscrito e APP conservada/em recuperacao (art. 15)'}
RES['reserva_legal'] = rl
rl_gdf = gpd.GeoDataFrame({'classe_car': ['Reserva Legal Proposta'], 'area_ha': [tot_ha], 'n_partes': [len(ps)],
                           'composicao': ['remanescente %.2f + APP vegetada %.2f + APP a recompor %.2f + corredor %.2f' % (rem_ha, appv_ha, appr_ha, corr_ha)],
                           'status': ['PROPOSTA sujeita a aprovacao do IAT']}, geometry=[RL_PROP], crs=CRS_METRICO)
guardar_vector(rl_gdf, 'RL_proposta')
corr_gdf = gpd.GeoDataFrame({'classe': ['corredor_recomposicao_RL'], 'area_ha': [A(corredor)]}, geometry=[corredor], crs=CRS_METRICO)
guardar_vector(corr_gdf, 'RL_corredor_recomposicao')

# ==============================================================================
# 7. Mapa de uso com nomenclatura CAR (sem sobreposicao)
# ==============================================================================
titulo('7. Mapa de uso CAR (poligonos sem sobreposicao, 100% do imovel)')
agua_p = clip(AGUA)
app_n_p = poly_only(app_nasc['central'].difference(agua_p))
app_c_p = poly_only(app_curso['central'].difference(unary_union([agua_p, app_n_p])))
rem_p = poly_only(clip(FLORESTA).difference(unary_union([agua_p, app_n_p, app_c_p])))
cons_p = poly_only(PROP.difference(unary_union([agua_p, app_n_p, app_c_p, rem_p])))
silvi_cons = poly_only(cons_p.intersection(SILVI))
cons_agri = poly_only(cons_p.difference(silvi_cons))
filas = []


def add(classe, sub, sit, g, nota=''):
    g = poly_only(g)
    if g.is_empty:
        return
    filas.append({'classe_car': classe, 'subclasse': sub, 'situacao': sit, 'area_ha': A(g), 'nota': nota, 'geometry': g})


NA = "Nascente ou olho d'água perene"
CA = "Curso d'água natural de até 10 metros"
RV = "Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais"
RF_ = "Reservatório – faixa de APP (cenário FBDS/IAT)"
add('APP – ' + NA, 'conforme', 'vegetacao nativa (RF 2026)', app_n_p.intersection(FLORESTA), 'perenidade NAO verificada')
add('APP – ' + NA, 'a recompor', 'sem vegetacao nativa', app_n_p.difference(FLORESTA), 'perenidade NAO verificada')
add('APP – ' + CA, 'conforme', 'vegetacao nativa (RF 2026)', app_c_p.intersection(FLORESTA), 'buffer 30 m do eixo FBDS 2013')
add('APP – ' + CA, 'a recompor', 'sem vegetacao nativa', app_c_p.difference(FLORESTA), 'buffer 30 m do eixo FBDS 2013')
add(RV, 'espelho d agua', 'agua (RF 2026)', agua_p, 'faixa de APP a definir pelo IAT; espelho FBDS 2013 = %.2f ha; cenario FBDS/IAT = faixa 30 m' % A(esp_union))
add('Remanescente de Vegetação Nativa', 'floresta fora da APP', 'conservada', rem_p, 'estagio sucessional requer campo')
add('Área Consolidada', 'uso agricola', 'consolidada', cons_agri, 'uso antropico fora da APP')
add('Área Consolidada', 'silvicultura', 'consolidada', silvi_cons, 'plantio florestal (RF); confirmar em campo')
mapa = gpd.GeoDataFrame(filas, geometry='geometry', crs=CRS_METRICO)
soma = mapa.area_ha.sum()
log('  %-70s %-16s %8s' % ('classe_car', 'subclasse', 'ha'))
for r in mapa.itertuples():
    log('  %-70s %-16s %8.2f' % (r.classe_car[:70], r.subclasse, r.area_ha))
log('  SOMA = %.2f ha (imovel %.2f) -> %s' % (soma, AREA_IMOVEL, 'OK' if abs(soma - AREA_IMOVEL) <= 0.1 else '!! NAO FECHA'))
if abs(soma - AREA_IMOVEL) > 0.1:
    raise RuntimeError('o mapa CAR nao fecha: %.2f vs %.2f ha' % (soma, AREA_IMOVEL))
# sobreposicao: soma das intersecoes par a par
sob = 0.0
gl = list(mapa.geometry)
for i in range(len(gl)):
    for j in range(i + 1, len(gl)):
        sob += gl[i].intersection(gl[j]).area
log('  sobreposicao total entre poligonos: %.4f ha' % (sob / 1e4))
mapa['pousio'] = False
# cenario FBDS/IAT (campo adicional, NAO altera o fechamento base): quanto de cada poligono cairia na faixa de reservatorio
FAIXA_CEN = poly_only(FAIXA_OFICIAL.difference(unary_union([app_n_p, app_c_p, agua_p])))
mapa['ha_faixa_reserv_cenario_fbds'] = [A(poly_only(g.intersection(FAIXA_CEN))) for g in mapa.geometry]
mapa['situacao_cenario_fbds'] = [
    (r.situacao if r.ha_faixa_reserv_cenario_fbds == 0 else
     '%s; %.2f ha viram "%s" %s no cenario FBDS/IAT' % (r.situacao, r.ha_faixa_reserv_cenario_fbds, RF_,
                                                          'conforme' if 'Remanescente' in r.classe_car else 'a recompor'))
    for r in mapa.itertuples()]
guardar_vector(mapa, 'mapa_uso_car')
# capa separada do cenario: faixa oficial FBDS de reservatorio fora da APP base, conforme / a recompor
filas_c = []
for sub, sit, g in (('conforme', 'vegetacao nativa (RF 2026)', FAIXA_CEN.intersection(FLORESTA)),
                    ('a recompor', 'sem vegetacao nativa', FAIXA_CEN.difference(FLORESTA).difference(SILVI)),
                    ('a recompor (substituir plantio)', 'silvicultura', FAIXA_CEN.difference(FLORESTA).intersection(SILVI))):
    g = poly_only(g)
    if not g.is_empty:
        filas_c.append({'classe_car': RF_, 'subclasse': sub, 'situacao': sit, 'area_ha': A(g),
                        'nota': 'faixa de 30 m da base IAT_FBDS_app_hidrica (objectid %s) fora da APP base; NAO somada ao mapa CAR base' % RES['reservatorio_artificial']['faixa_oficial_fbds_objectids'],
                        'geometry': g})
mapa_c = gpd.GeoDataFrame(filas_c, geometry='geometry', crs=CRS_METRICO) if filas_c else None
if mapa_c is not None:
    guardar_vector(mapa_c, 'mapa_uso_car_cenario_fbds')
    for r in mapa_c.itertuples():
        log('  [cenario FBDS/IAT] %-52s %-32s %8.2f' % (r.classe_car, r.subclasse, r.area_ha))
RES['mapa_uso_car'] = {'ha': [{k: v for k, v in r.items() if k != 'geometry'} for _, r in mapa.iterrows()], 'soma_ha': round(soma, 2),
                       'area_pousio_ha': 0.0, 'nota_pousio': 'nao identificavel com uma cena; RF/MB nao mostram solo em pousio',
                       'sobreposicao_ha': round(sob / 1e4, 4),
                       'cenario_fbds': {'classe_car': RF_, 'ha': [{k: v for k, v in r.items() if k != 'geometry'} for _, r in mapa_c.iterrows()] if mapa_c is not None else [],
                                        'faixa_total_ha': A(FAIXA_CEN),
                                        'nota': 'capa separada (mapa_uso_car_cenario_fbds.geojson); o fechamento base em %.2f ha nao muda; '
                                                'campo situacao_cenario_fbds em cada poligono base indica o que mudaria' % AREA_IMOVEL}}

# ==============================================================================
# 8. resultados + avisos
# ==============================================================================
titulo('8. resultados_analisis.json')
prev = leer_json(RESULTADOS_JSON)
h = prev['hidrografia']; vg = prev['vegetacao']
# --- fragmento 13 (faixa ciliar norte): evidencia calculada em an_02, nao copiada a mao
f13 = next((f for f in vg['fragmentos']['lista'] if int(f['frag_id']) == 13), None)
ref = vg['fragmentos'].get('referencias_espectrais_aoi', {})
past = ref.get('pastagem', {}); cafe = ref.get('cafe', {})
serie_conc = vg['fragmentos'].get('serie_ndvi_24m_conclusao')
if f13 is not None:
    AV.append('Fragmento 13 (%.2f ha, faixa ciliar norte): sem historico florestal (MapBiomas 2008 %.0f%%, Hansen tc2000>30%% %.0f%%, FBDS 2013 = antropizado)%s; '
              'SWIR B11 %.3f +- %.3f vs pastagem %.3f +- %.3f (%.0f%% dos pixeles abaixo do p5 da pastagem)%s; DW trees %.0f%% -> arboreo em regeneracao; '
              'nucleo %.2f ha (p_floresta %.2f) alta confianca, borda %.2f ha (p %.2f) media; %.2f ha de borda com p<0,5 incertas (provavel cultivo de inverno); '
              'natureza (regeneracao vs plantio) e altura de dossel a confirmar em campo; variante conservadora da RL exclui-o'
              % (f13['area_dentro_propriedade_ha'], 100 * f13['frac_floresta_mb_2008'], 100 * (f13.get('frac_hansen_treecover2000_gt30') or 0),
                 '; serie NDVI 24 meses = vegetacao permanente (sem entressafra)' if serie_conc else '',
                 f13['b11_medio'], f13['b11_sd'], past.get('b11_media', float('nan')), past.get('b11_sd', float('nan')),
                 100 * (f13.get('frac_b11_abaixo_p5_pastagem') or 0),
                 ('; textura GLCM %.0f vs %.0f do cafe (descarta cafe em fileiras)' % (f13['glcm_contraste_medio'], cafe['glcm_contraste_medio'])) if 'glcm_contraste_medio' in cafe else '',
                 100 * f13['frac_dw_trees'], f13['nucleo_ha'], f13.get('nucleo_prob_floresta_media') or 0, f13['borda_ha'], f13.get('borda_prob_floresta_media') or 0,
                 f13['ha_prob_floresta_lt_05']))
# --- nascente FBDS e candidatos DEM (talvegue)
for n_ in h['nascentes'].get('fbds_lista', []):
    if n_['dentro']:
        AV.append('Nascente FBDS %s (%.0f, %.0f), a %.0f m do limite: %s; APP de 50 m = %.2f ha; perenidade a confirmar em campo'
                  % (n_['id'], n_['x'], n_['y'], n_['dist_limite_propriedade_m'],
                     ('conectada ao curso FBDS %s (inicio do curso)' % n_['curso_fbds_id']) if n_['conectada_curso_fbds'] else 'SEM curso FBDS conectado',
                     RES['app_nascente']['ha']))
talv_tot = 0.0
for c_ in h['nascentes'].get('candidatos', []):
    t_ = c_.get('talvegue_dem')
    if t_ and not c_.get('conectada_curso_fbds') and (c_.get('dist_curso_fbds_m') or 0) > 100:
        talv_tot += t_.get('app_potencial_so_curso_fora_app_e_circulo_ha', t_['app_potencial_fora_app_fbds_ha'])
        AV.append('Candidato DEM %s (%.0f, %.0f) NAO e nascente: cabeceira DEM em %s, HAND %s m, a %.0f m de qualquer curso FBDS e sem curso em 5 bases (FBDS/otto/ANA/IBGE/DEM-oficial); '
                  'talvegue DEM de %.0f m a jusante (ate %.0f, %.0f) sobre cultivo (NDVI %.2f, MNDWI %.2f: sem agua), ausente em todas as bases; '
                  'RISCO: se houver curso intermitente, ate %.2f ha de APP adicional do curso (fora da APP exigivel e alem do circulo de 50 m ja contabilizado); verificar em campo na estacao chuvosa'
                  % (c_['id'], c_['x'], c_['y'], c_.get('mb_2025'), c_.get('hand_m'), c_.get('dist_curso_fbds_m') or 0,
                     t_['comprimento_m'], t_['x_fim'], t_['y_fim'], t_.get('ndvi_medio') or 0, t_.get('mndwi_medio') or 0,
                     t_.get('app_potencial_so_curso_fora_app_e_circulo_ha', t_['app_potencial_fora_app_fbds_ha'])))
RES['app_nascente']['candidatas_dem']['talvegue_dem_risco'] = {
    'candidatos': [{'id': c_['id'], 'x': c_['x'], 'y': c_['y'], 'conectada_curso_fbds': c_.get('conectada_curso_fbds'), 'mb_2025': c_.get('mb_2025'),
                    'talvegue': c_.get('talvegue_dem')} for c_ in h['nascentes'].get('candidatos', [])],
    'app_potencial_talvegue_fora_app_exigivel_ha': round(talv_tot, 2),
    'app_potencial_total_se_confirmado_ha': round(talv_tot + RES['app_nascente']['candidatas_dem']['ha_adicional_fora_app_exigivel'], 2),
    'nota': 'RISCO separado da APP exigivel: talvegue DEM sem curso em nenhuma base; so vira APP se confirmado curso em campo; '
            'total se confirmado = circulos de 50 m dos candidatos (ha_adicional_fora_app_exigivel) + faixa de 30 m do talvegue'}
# --- CAR vizinho sobreposto
for c_ in h['fontes']['CAR_vizinhos_hidro_pol'].get('sobreposicao_imoveis', []):
    AV.append('SOBREPOSICAO DE CAR VIZINHO: o imovel %s (status %s) declara "%s" de %.2f ha, %.0f%% dentro do poligono do cliente — '
              'ou o perimetro do vizinho se sobrepoe ao do cliente, ou o poligono do cliente inclui reservatorio alheio; afeta a area-base (RL 20%%) e a APP do reservatorio: '
              'verificar no SICAR e conferir o perimetro (matricula/RTK) ANTES de inscrever'
              % (c_['cod_imovel'], c_['status'], c_['tema'], c_['ha_total'], 100 * c_['frac_dentro']))
# --- supressao pos-2008
M_ = vg['mudanca_2008_2025']
AV.append('Supressao pos-2008 (MapBiomas 30 m): %.2f ha brutas, das quais %.2f ha sao floresta RF em 2026 e Hansen loss = %.2f ha -> artefato de borda do MapBiomas 30 m, '
          'indicio nao confirmado; supressao CONFIRMADA (nao floresta RF 2026 e/ou Hansen loss) = %.2f ha'
          % (M_.get('supressao_pos2008_bruta_ha', 0), M_.get('supressao_pos2008_floresta_rf_2026_ha', 0),
             M_.get('supressao_pos_2008_confirmada_hansen_ha', 0), M_.get('supressao_pos2008_confirmada_ha', 0)))
# --- exatidao RF sobre consenso
RF = vg['rf']
AV.append('Classificacao RF treinada com consenso de 3 produtos globais (nao verdade de campo); OA %.3f por blocos espaciais MEDIDA SO SOBRE PIXELES DE CONSENSO: '
          '%.2f das %.2f ha de floresta do imovel estao fora desse consenso (faixa ciliar norte + bordas; p_floresta media %.2f) e nao tem exatidao medida — '
          'sao as que decidem se o deficit de RL e %.2f ou %.2f ha (variante conservadora); silvicultura F1 %.2f'
          % (RF['OA'], RF.get('floresta_ha_sem_consenso', 0), RF.get('floresta_ha_total_propriedade', 0), RF.get('prob_floresta_media_sem_consenso') or 0,
             rl['deficit_com_app_art15_ha'], v['deficit_com_app_art15_ha'], RF['F1'].get('SILVICULTURA', float('nan'))))
# --- regime / perenidade
reg = h['regime']
AV.append('Perenidade dos cursos e das nascentes NAO verificada por satelite; regime "perene" so onde coincide com IBGE BC250 (1:250.000)'
          + ('' if reg.get('ibge_discrimina_regime', True) else
             ' — e TODOS os %d trechos BC250 do recorte sao "Permanente": o atributo nao discrimina, a coincidencia (%.3f km) nao e evidencia de perenidade'
             % (reg.get('ibge_trechos_recorte', 0), reg.get('km_fbds_dentro_perene', 0))))
AV += [
    'Faixa de APP do reservatorio artificial a definir pelo IAT/licenca (art. 4 III; IN IAT 64/2025); nao somada ao total exigivel BASE (%.2f ha). '
    'CENARIO FBDS/IAT (base oficial app_hidrica, 30 m para ambos os reservatorios): APP %.2f ha, a recompor %.2f ha (vs %.2f)'
    % (RES['app_total_exigivel']['ha'], RES['app_total_exigivel']['app_total_cenario_fbds_ha'], cenA_F, cenA),
    'Leito medido desde o EIXO da linha FBDS 2013 (RapidEye 5 m, 1:25.000); a borda da calha do leito regular exige levantamento em campo (RTK)',
    'Estagio sucessional NAO se determina por satelite (CONAMA 2/1994 exige DAP, area basal, estratos): inventario de campo obrigatorio',
    'PRA / recomposicao reduzida (cenario B) exige CAR inscrito ate 31/12/2023 e adesao ao PRA; sem essa condicao vale o cenario A',
    'Area consolidada inferida do MapBiomas 2008 (30 m): indicio, nao prova; o IAT analisa com suas proprias bases (IN IAT 05/2023)',
    'RL proposta (%.2f ha) em %d bloco(s) %s ha, todos >= %.2f ha; silvicultura (%.2f ha na APP) e agua excluidas; composicao = remanescente %.2f + APP vegetada %.2f + APP a recompor %.2f + corredor %.2f'
    % (tot_ha, len(ps), ps, MIN_PARTE_HA, A(poly_only(APP.intersection(SILVI))), rem_ha, appv_ha, appr_ha, corr_ha),
    'Servidoes administrativas: sem dado (assumidas 0); RL = 20%% x %.2f ha' % AREA_IMOVEL,
    'Este diagnostico e PRELIMINAR e nao substitui laudo: o CAR e declaratorio (art. 29) e a validacao e do IAT-PR',
]
RES['avisos'] = AV
RES['resumo'] = {
    'imovel_ha': round(AREA_IMOVEL, 2), 'escena': ESCENA_ID,
    'cursos_fbds_dentro_km': h['tabla_fontes_propriedade']['FBDS']['km_dentro_propriedade'],
    'nascentes_fbds_dentro': h['nascentes']['fbds_dentro'], 'candidatos_dem_dentro': h['nascentes']['candidatos_dem_dentro'],
    'app_exigivel_ha': RES['app_total_exigivel']['ha'], 'app_exigivel_min_max': [RES['app_total_exigivel']['ha_min'], RES['app_total_exigivel']['ha_max']],
    'app_total_cenario_fbds_ha': RES['app_total_exigivel']['app_total_cenario_fbds_ha'],
    'app_conforme_ha': RES['app_total_exigivel']['com_vegetacao_nativa_ha'], 'app_pct_conforme': RES['app_total_exigivel']['pct_conforme'],
    'app_conforme_cenario_fbds_ha': RES['app_total_exigivel']['cenario_fbds_iat']['com_vegetacao_nativa_ha'],
    'app_a_recompor_A_ha': cenA, 'app_a_recompor_B_ha': cenB, 'app_a_recompor_A_cenario_fbds_ha': cenA_F,
    'app_talvegue_dem_risco_ha': round(talv_tot, 2),
    'reservatorio_dispensa_art4_par4': RES['reservatorio_artificial']['dispensa_art4_par4_algum'],
    'rl_exigida_ha': RL_HA, 'rl_disponivel_com_app_ha': rl['disponivel_com_app_art15_ha'], 'rl_deficit_com_app_ha': rl['deficit_com_app_art15_ha'],
    'rl_deficit_sem_app_ha': rl['deficit_sem_app_ha'], 'rl_deficit_conservador_com_app_ha': v['deficit_com_app_art15_ha'],
    'rl_proposta_ha': tot_ha, 'rl_proposta_n_partes': len(ps), 'rl_proposta_corredor_ha': corr_ha,
    'supressao_pos2008_bruta_ha': M_.get('supressao_pos2008_bruta_ha'), 'supressao_pos2008_confirmada_ha': M_.get('supressao_pos2008_confirmada_ha'),
    'floresta_ha_sem_consenso': RF.get('floresta_ha_sem_consenso'),
    'car_vizinho_sobreposto_n': len(h['fontes']['CAR_vizinhos_hidro_pol'].get('sobreposicao_imoveis', [])),
    'rf_OA': prev['vegetacao']['rf']['OA'], 'rf_F1': prev['vegetacao']['rf']['F1'],
    'fbds_vs_dem_mediana_m': h['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_mediana_m'],
    'fbds_vs_dem_p90_m': h['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_p90_m'],
}
actualizar_resultados('legal', RES)
log('an_03 listo en %.0f s' % (time.time() - T0))
