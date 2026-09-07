# -*- coding: utf-8 -*-
"""an_12_glebas_v3 — cifras da VERSAO 3 (imovel unico + Gleba 2 "terra limpa" + CAR existente + hidrologia PRO).

    python an_12_glebas_v3.py   -> 02_ANALISIS/resultados_v3.json (+ capas v3 em 02_ANALISIS)

O que muda em relacao a an_07 (v2):
  * HIPOTESE PRINCIPAL = IMOVEL UNICO (IN MMA 2/2014 art. 32; Lei 8.629 art. 4 I): RL 20% sobre 157,75 ha = 31,55 ha.
    As cifras por gleba ficam como INVENTARIO descritivo e para localizar a RL, nao como cotas independentes.
  * GLEBA 2 = terra limpa, sem monte (afirmacao do cliente tomada como fato): vegetacao computavel do imovel = a da G1.
    A ponta norte da G2 cai sobre 2,68 ha de floresta (fragmento 2) que o cliente diz nao ter comprado -> limite a
    conferir na escritura/SIGEF; se corrigido, APP e vegetacao da G2 = 0.
  * Tres cenarios para "os 6 alqueires": (A) imovel unico; (B) imovel separado desmembrado de > 4 MF (art. 12 par. 1);
    (C) excecao art. 67 se o imovel de origem tinha <= 4 MF em 22/07/2008.
  * Deficit principal (31,55 - 17,70) e conservador (sem o fragmento 13, sem historico 2008/2013).
  * Envolventes: APP por gleba do ensamble de 5 DEM (an_11); floresta +-1 px (perimetro x 10 m / 2, como an_03).
  * CAR existente PR-4124301-F127CD1E... vs medido (retificacao do CAR); represa por fonte + outorga; manancial;
    nascentes com veredicto; cursos por fonte.
Nada se reclassifica: tudo sai de resultados_glebas.json, resultados_analisis.json, resultados_hidrologia_pro.json
e das capas ja geradas. No final verifica-se que as somas fecham (3 decimais) e que os KPIs do informe existem.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import (ANALISIS, R, P, RESULTADOS_JSON, PARAMETROS_LEGALES, CRS_METRICO, CRS_WGS84, DATOS_EXT,  # noqa: E402
                          leer_json, guardar_json, leer_raster, vectorizar, guardar_vector, _limpio, log, titulo)

import geopandas as gpd                                     # noqa: E402
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon   # noqa: E402
from shapely.ops import unary_union                          # noqa: E402

HP = os.path.join(ANALISIS, 'hidrologia_pro')
GOV = os.path.join(DATOS_EXT, 'gov_pro')
RESULTADOS_V3 = os.path.join(ANALISIS, 'resultados_v3.json')
MF_HA = 20.0
ALQ = 2.42


def poly_only(g):
    if g is None or g.is_empty:
        return Polygon()
    if isinstance(g, (Polygon, MultiPolygon)):
        return g
    if isinstance(g, GeometryCollection):
        parts = [p for p in g.geoms if isinstance(p, (Polygon, MultiPolygon)) and not p.is_empty]
        return unary_union(parts) if parts else Polygon()
    return Polygon()


def ha3(g):
    return round(poly_only(g).area / 1e4, 3)


def r2(x):
    return round(float(x), 2)


titulo('an_12_glebas_v3: cifras v3 (imovel unico, G2 terra limpa, CAR existente)')
G = leer_json(os.path.join(ANALISIS, 'resultados_glebas.json'))
RES = leer_json(RESULTADOS_JSON)
HPJ = leer_json(os.path.join(HP, 'resultados_hidrologia_pro.json'))
PL = leer_json(PARAMETROS_LEGALES)
g1, g2, un = G['G1'], G['G2'], G['UNICO']
L, VG = RES['legal'], RES['vegetacao']

A_ = lambda n: gpd.read_file(os.path.join(ANALISIS, n + '.geojson'))
lim = A_('gleba_limites')
G1 = lim[lim.gleba == 'G1'].geometry.iloc[0]
G2 = lim[lim.gleba == 'G2'].geometry.iloc[0]
PROP = unary_union([G1, G2])
flor1 = A_('gleba_G1_floresta'); flor2 = A_('gleba_G2_floresta')
rl1 = A_('gleba_G1_rl_existente')          # remanescente fora da APP + APP vegetada (art. 15) = vegetacao computavel
rl_prop = A_('RL_proposta')
car_hp = gpd.read_file(os.path.join(HP, 'CAR_propriedade_e_vizinhos.geojson'))
nasc_v = gpd.read_file(os.path.join(HP, 'nascentes_veredicto.geojson'))

# ------------------------------------------------------------- areas base ----
area1, area2 = g1['area_ha_3dec'], g2['area_ha_3dec']
area_un = round(area1 + area2, 3)
assert abs(area_un - un['area_ha_3dec']) < 0.002, (area_un, un['area_ha_3dec'])
rl_ex_un = round(0.2 * area_un, 3)          # 31,550
rl_ex_g1 = round(0.2 * area1, 3)            # 28,842
rl_ex_g2 = round(0.2 * area2, 3)            # 2,708
n_mf_un, n_mf_g1, n_mf_g2 = area_un / MF_HA, area1 / MF_HA, area2 / MF_HA

# ------------------------------------------------------------- vegetacao ----
veg_g1 = g1['vegetacao']['floresta_nativa_car_ha']          # 17,70 = 9,81 rem + 7,89 APP vegetada
veg_g1_3 = round(sum(float(a) for a in rl1.area_ha) , 3)   # soma das particoes (2 dec cada)
rem_g1, appveg_g1 = g1['reserva_legal']['remanescente_fora_app_ha'], g1['reserva_legal']['app_com_vegetacao_art15_ha']
frag13 = next(f for f in g1['vegetacao']['fragmentos'] if f['frag_id'] == 13)
frag30 = next(f for f in g1['vegetacao']['fragmentos'] if f['frag_id'] == 30)
frag2_g1 = next(f for f in g1['vegetacao']['fragmentos'] if f['frag_id'] == 2)
frag2_g2 = next(f for f in g2['vegetacao']['fragmentos'] if f['frag_id'] == 2)
f13_ha = frag13['area_dentro_ha']                            # 10,46
veg_cons = round(veg_g1 - f13_ha, 2)                         # 7,24
veg_g2_imagem = g2['vegetacao']['floresta_nativa_car_ha']    # 2,68 (ponta norte, NAO computa: terra limpa)

# envolvente +-1 px da floresta (perimetro x 10 m / 2), mesmo criterio de an_03 (inclui borda com o limite: conservador)
FL1 = poly_only(unary_union(list(rl1.geometry)))
per1 = FL1.length
inc1 = round(per1 * P['pixel_s2_m'] / 2 / 1e4, 2)
veg_g1_env = [r2(veg_g1 - inc1), r2(veg_g1 + inc1)]
FL13 = poly_only(unary_union(list(flor1[flor1.frag_id == 13].geometry)))
FLcons = poly_only(FL1.difference(FL13.buffer(0.01)))
inc_cons = round(FLcons.length * P['pixel_s2_m'] / 2 / 1e4, 2)
veg_cons_env = [r2(max(0, veg_cons - inc_cons)), r2(veg_cons + inc_cons)]
log('  floresta computavel G1 %.2f ha (perimetro %.0f m, +-%.2f) -> [%s]; conservadora %.2f (+-%.2f) -> [%s]'
    % (veg_g1, per1, inc1, veg_g1_env, veg_cons, inc_cons, veg_cons_env))

# ------------------------------------------------------------- Reserva Legal (principal = imovel unico, G2 terra limpa)
def_princ = round(rl_ex_un - veg_g1, 2)                 # 13,85
def_cons = round(rl_ex_un - veg_cons, 2)                # 24,31
def_se_ponta_norte = un['reserva_legal']['deficit_com_app_art15_ha']   # 11,17 (so se a mata da ponta norte for do imovel)
assert abs(def_princ - 13.85) < 0.006 and abs(def_cons - 24.31) < 0.006, (def_princ, def_cons)
# RL proposta (an_03, imovel unico, 5 blocos) recortada a G1 (a G2 e terra limpa e sua mata nao e do imovel)
RLP_G1 = poly_only(unary_union(list(rl_prop.geometry)).intersection(G1))
rlp_g1 = g1['reserva_legal']['rl_proposta_recortada_ha']       # 28,57
falta_rlp = round(rl_ex_un - rlp_g1, 2)                        # 2,98
corr_g1 = g1['reserva_legal']['corredor_recomposicao_recortado_ha']   # 8,55
app_rec_incl = L['reserva_legal']['proposta']['app_a_recompor_incluida_ha']   # 2,33 (imovel) -> so computa apos art. 15 II
RLP_APP_REC = None
try:
    app1 = A_('gleba_G1_app')
    rec1 = poly_only(unary_union(list(app1[(app1.cenario == 'base') & (app1.situacao == 'a recompor')].geometry)))
    app_rec_incl_g1 = ha3(RLP_G1.intersection(rec1))
except Exception:
    app_rec_incl_g1 = None

# IAT fragmento prioritario dentro das glebas
iat_fr = gpd.read_file(os.path.join(GOV, 'IAT_fragmentos_florestais_prioritarios.geojson')).to_crs(CRS_METRICO)
iat_fr['geometry'] = iat_fr.geometry.make_valid()
iat_fr = iat_fr[iat_fr.intersects(PROP)].copy()
frag_iat = []
for _, r in iat_fr.iterrows():
    gi = poly_only(r.geometry.intersection(PROP))
    if gi.area < 100:
        continue
    frag_iat.append({'fragmento': str(r.fragmento), 'area_total_ha': float(r.area_ha), 'idade_anos': int(r.idade), 'prioridade': str(r.prioridade),
                     'fito': str(r.fito).replace('  ', ' '), 'dentro_ha': ha3(gi), 'em_G1_ha': ha3(gi.intersection(G1)), 'em_G2_ha': ha3(gi.intersection(G2)),
                     'coincide_com_floresta_rf_G1_ha': ha3(gi.intersection(FL1)), 'geom': gi})
frag_iat.sort(key=lambda d: -d['dentro_ha'])
log('  fragmentos IAT prioritarios dentro: %s' % [(f['fragmento'], f['dentro_ha'], f['em_G1_ha'], f['em_G2_ha']) for f in frag_iat])

# ------------------------------------------------------------- APP (referencia FBDS + envolvente do ensamble) ----
apph = HPJ['app']['por_gleba']
app_g1 = g1['app']['exigida_ha']; app_g2 = g2['app']['exigida_ha']; app_un = un['app']['exigida_ha']
env1 = apph['G1']['envolvente_min_max_ha']; env2 = apph['G2']['envolvente_min_max_ha']
env_un = [r2(env1[0] + env2[0]), r2(env1[1] + env2[1])]
disp1 = HPJ['dem_ensamble']['dispersion_por_arroio']['G1']
arr1_sesgo = disp1['Arroio 1 (norte)']
app_arroios = {k: {'app30_fbds_ha': v['app30_fbds_ha'], 'app30_ensamble_ha': v['app30_mediana_ensamble_ha'], 'envolvente_ha': v['app30_envolvente_ha'],
                   'mediana_ensamble_vs_fbds_med_m': v['mediana_ensamble_vs_fbds_med_m'], 'p90_m': v['mediana_ensamble_vs_fbds_p90_m'],
                   'dist_por_dem_mediana_m': {d: x['dist_mediana_m'] for d, x in v['por_dem'].items()}} for k, v in disp1.items()}
# G1: 3 decimais que fecham: 7,89 + 1,16 + 2,92 = 11,97 (arredondamento) -> reportar as 3 dec
app1 = A_('gleba_G1_app'); b1 = app1[app1.cenario == 'base']
app_g1_3 = {s: ha3(unary_union(list(b1[b1.situacao == s].geometry))) for s in ('conforme', 'agua', 'a recompor')}
app_g1_3['soma'] = round(sum(app_g1_3.values()), 3)
log('  APP G1 3 dec: %s (JSON 11,96 = %s)' % (app_g1_3, apph['G1']['app_fbds_recalculada_ha']))

# ------------------------------------------------------------- Gleba 2: tres cenarios ----
# vegetacao nativa em 22/07/2008 dentro da G2 (MapBiomas 2008, 30 m: indicio) — numero do art. 67 (cenario C)
mb, prof30 = leer_raster(R['mb_hist'], bandas=['classification_2008'])
nat08 = vectorizar(np.isin(mb['classification_2008'], [3]).astype(np.uint8), prof30, 'v')
NAT08 = poly_only(unary_union(list(nat08.geometry))) if len(nat08) else Polygon()
veg08_g2 = ha3(NAT08.intersection(G2))
FL2 = poly_only(unary_union(list(flor2.geometry)))
veg08_g2_na_ponta = ha3(NAT08.intersection(G2).intersection(FL2.buffer(30)))
x0, y0, x1, y1 = FL2.bounds
ponta_norte = {'floresta_rf_2026_ha': veg_g2_imagem, 'fragmento': 2, 'y_min_utm': round(y0), 'y_max_utm': round(y1),
               'extensao_norte_sul_m': round(y1 - y0), 'floresta_mb_2008_ha_indicio': veg08_g2,
               'nota': 'ponta norte do poligono da Gleba 2: cai sobre floresta continua com o fragmento 2 (IAT prioridade A). O cliente afirma que a '
                       'compra foi de terra limpa, sem monte: o limite deve ser conferido na escritura/SIGEF (matricula 1168, CAR 5223911747...). '
                       'Se o limite for corrigido, a APP e a vegetacao da Gleba 2 passam a 0.'}
car_g2_mf = next(c for c in HPJ['car']['imoveis_intersectan'] if c['cod_imovel'] == HPJ['car']['car_g2'])
cenarios_g2 = {
    'A_imovel_unico_principal': {
        'base_legal': 'IN MMA 2/2014 art. 32 e par. unico; Lei 8.629/1993 art. 4 I; Lei 12.651 art. 12 II, 14 e 15',
        'rl_exigida_imovel_ha': r2(rl_ex_un), 'rl_parcela_g1_ha': r2(rl_ex_g1), 'rl_parcela_g2_ha': r2(rl_ex_g2),
        'aporte_vegetacao_g2_ha': 0.0, 'vegetacao_computavel_imovel_ha': veg_g1, 'deficit_ha': def_princ,
        'deficit_conservador_ha': def_cons, 'deficit_se_ponta_norte_for_do_imovel_ha': def_se_ponta_norte,
        'localizacao': 'em qualquer gleba (art. 14), aprovada pelo IAT; proposta apoiada na G1 (corredor + fragmento prioritario IAT)',
        'resposta': 'os 6 alqueires nao tem conta propria: somam %.2f ha a RL do imovel (%.2f -> %.2f ha) e nao aportam vegetacao' % (rl_ex_g2, rl_ex_g1, rl_ex_un)},
    'B_imovel_separado_desmembrado_de_maior_4MF': {
        'base_legal': 'Lei 12.651 art. 12 par. 1 (fracionamento: RL sobre o imovel antes do fracionamento) + art. 66',
        'imovel_de_origem': {'cod_imovel': HPJ['car']['car_g2'], 'area_ha': car_g2_mf['num_area'], 'mod_fiscal_declarado': car_g2_mf['mod_fiscal'],
                             'condicao': car_g2_mf['des_condic'], 'matricula_sigef': '1168', 'area_sigef_ha': 95.90},
        'rl_exigida_ha': r2(rl_ex_g2), 'vegetacao_computavel_ha': 0.0, 'deficit_ha': r2(rl_ex_g2),
        'resposta': 'RL propria de 20%% = %.2f ha (o imovel de origem tem %.2f MF > 4 MF); com terra limpa, os %.2f ha ficam integralmente a recompor, regenerar ou compensar (art. 66)' % (rl_ex_g2, car_g2_mf['mod_fiscal'], rl_ex_g2)},
    'C_excecao_art67_origem_ate_4MF_em_2008': {
        'base_legal': 'Lei 12.651 art. 67; Lei PR 18.295 art. 31; IN MMA 2/2014 art. 24 — SO se o imovel de origem tinha <= 4 MF em 22/07/2008 (a provar com a matricula de origem)',
        'rl_exigida_ha': 'vegetacao nativa existente em 22/07/2008 dentro do limite conferido',
        'vegetacao_2008_g2_mapbiomas_ha_indicio': veg08_g2, 'vegetacao_2008_na_ponta_norte_ha': veg08_g2_na_ponta,
        'rl_se_ponta_norte_nao_for_da_gleba_ha': 0.0,
        'resposta': 'RL = vegetacao de 2008: 0 ha se a gleba era terra limpa; obrigacao = nao converter vegetacao nativa (art. 67, vedadas novas conversoes)'},
    'app_g2': {'exigida_fbds_ha': app_g2, 'envolvente_ha': env2, 'com_vegetacao_ha': g2['app']['com_vegetacao_nativa_ha'],
               'se_limite_corrigido_ha': 0.0, 'curso_m': g2['arroios']['lista'][0]['comprimento_dentro_m'],
               'nota': '33 m do Arroio 1 na ponta norte; se a ponta norte nao for da gleba, APP = 0'},
    'supressao_pos_2008_indicio_ha': g2['vegetacao']['supressao_pos_2008_indicio_ha'],
}
log('  G2: veg MB2008 %.2f ha (na ponta norte %.2f) · RL 20%% %.2f · origem CAR %.2f ha = %.2f MF' % (veg08_g2, veg08_g2_na_ponta, rl_ex_g2, car_g2_mf['num_area'], car_g2_mf['mod_fiscal']))

# ------------------------------------------------------------- CAR existente vs medido ----
cmp1 = HPJ['car']['comparacion_declarado_vs_medido']['G1']
car_g1_meta = next(c for c in HPJ['car']['imoveis_intersectan'] if c['cod_imovel'] == HPJ['car']['car_g1'])
sigef = next(s for s in HPJ['car']['sigef_intersecta'] if s['registro_m'] == '8.334')
res_partes = HPJ['agua']['represa']['reservatorio_car_partes']
car_v3 = {
    'cod_imovel': HPJ['car']['car_g1'], 'status': car_g1_meta['ind_status'], 'condicao': car_g1_meta['des_condic'],
    'municipio_no_car': car_g1_meta['municipio'] + ' (cod. 4124301)', 'municipio_do_centroide': PL['municipio'] + ' (IBGE %s)' % PL['codigo_ibge'],
    'area_declarada_ha': car_g1_meta['num_area'], 'mod_fiscal_declarado': car_g1_meta['mod_fiscal'],
    'matricula_sigef': sigef['registro_m'], 'area_sigef_ha': round(float(sigef['area_ha']), 2), 'sigef_status': sigef['status'],
    'cobertura_g1_pct': HPJ['car']['cobertura']['G1']['pct_gleba_cubierta'], 'g1_sem_car_ha': HPJ['car']['cobertura']['G1']['gleba_sin_ningun_car_ha'],
    'solape_com_car_g2_ha': HPJ['car']['solapes_entre_car'][0]['solape_en_prop_ha'],
    'data_inscricao': 'NAO disponivel na replica IAT: verificar no recibo do CAR (decide o PRA-PR: art. 29 par. 4, CAR ate 31/12/2023)',
    'tabela': [
        {'tema': 'Area do imovel', 'declarado_ha': cmp1['area_imovel_decl_ha'], 'medido_ha': area1, 'medido_imovel_ha': area_un, 'nota': 'poligono do cliente G1 vs CAR/SIGEF 143,34; imovel unico 157,75'},
        {'tema': 'APP', 'declarado_ha': cmp1['app_car_geom_en_gleba_ha'], 'declarado_num_area_ha': cmp1['app_car_num_area_decl_ha'], 'medido_ha': app_g1, 'medido_envolvente_ha': env1,
         'nota': 'geometria CAR na gleba 12,44 (num_area 10,45) vs 11,96 FBDS [11,96; 14,00 ensamble]'},
        {'tema': 'Reserva Legal averbada', 'declarado_ha': cmp1['rl_car_geom_en_gleba_ha'], 'exigida_g1_ha': r2(rl_ex_g1), 'exigida_imovel_ha': r2(rl_ex_un), 'nota': 'averbada 2,45 vs exigida 28,84 (G1) / 31,55 (imovel unico)'},
        {'tema': 'Vegetacao nativa', 'declarado_ha': cmp1['veg_nativa_car_en_gleba_ha'], 'medido_ha': veg_g1, 'medido_envolvente_ha': veg_g1_env, 'medido_conservador_ha': veg_cons,
         'nota': 'declarada 3,80 vs 17,70 medida (7,24 sem o fragmento 13)'},
        {'tema': 'Area consolidada', 'declarado_ha': cmp1['area_consolidada_car_en_gleba_ha'], 'medido_ha': g1['vegetacao']['area_agricola_car_ha'], 'nota': 'uso agricola fora da APP (RF 2026) + silvicultura %.2f' % g1['vegetacao']['silvicultura_fora_app_car_ha']},
        {'tema': 'Reservatorio artificial (represa)', 'declarado_ha': res_partes[0]['area_ha'], 'medido_ha': HPJ['agua']['represa']['fbds_2013_ha'], 'medido_atual_ha': HPJ['agua']['espelho_referencia']['envolvente_actual_ha'],
         'nota': 'CAR 2,12 vs FBDS 2013 1,95; espelho atual 2024-26 0,83-1,23'},
        {'tema': 'Reservatorio na cabeceira do Arroio 2', 'declarado_ha': res_partes[1]['area_ha'], 'medido_ha': 0.0,
         'nota': 'declarado 0,15 ha a %.0f m da nascente FBDS 306158; sem agua em 2024-26 (S2 freq 0, S1 f16 max %.3f): acude seco/colmatado? verificar em campo; se ha barramento sobre a nascente, APP = raio de 50 m e o barramento exige outorga' % (res_partes[1]['dist_nascente_fbds_m'], res_partes[1]['s1_freq16_max'])},
        {'tema': "Hidrografia rio ate 10 m (poligono)", 'declarado_ha': cmp1['hidro_car_rio_ate10_en_gleba_ha'], 'medido_km': cmp1['hidro_medida_fbds_km'], 'nota': 'CAR declara %.3f ha de leito; FBDS %.3f km' % (cmp1['hidro_car_rio_ate10_en_gleba_ha'], cmp1['hidro_medida_fbds_km'])},
    ],
    'o_que_retificar': ['Reserva Legal: passar de 2,45 ha averbados para %.2f ha (imovel unico) — localizar sobre a vegetacao computavel (%.2f ha) + corredor, declarar o deficit (%.2f ha) e o instrumento do art. 66' % (rl_ex_un, veg_g1, def_princ),
                        'Vegetacao nativa: declarar %.2f ha (hoje 3,80), com o fragmento 13 rotulado como regeneracao a confirmar' % veg_g1,
                        'APP: conferir a geometria declarada (12,44 ha) contra o eixo FBDS e o levantamento GNSS do Arroio 1 (envolvente [%.2f; %.2f])' % tuple(env1),
                        'Incluir a Gleba 2 no mesmo CAR (IN MMA 2/2014 art. 32) apos conferir o limite da ponta norte; retificar o CAR de origem 5223911747... (desmembramento)',
                        'Reservatorio: declarar o espelho medido em campo (perimetro GNSS) e anexar a outorga regularizada; conferir o 2o reservatorio (0,15 ha) na cabeceira do Arroio 2',
                        'Municipio: o CAR esta em Santo Antonio do Paraiso (4124301) e o centroide geocodifica em Sao Sebastiao da Amoreira (4126009): conferir a matricula (a divisa municipal nao muda o MF de 20 ha em nenhum dos dois)'],
}

# ------------------------------------------------------------- represa / outorga / manancial ----
rep = HPJ['agua']['represa']; ref = HPJ['agua']['espelho_referencia']
represa_v3 = {
    'arroio': 'Arroio 3 (sul) = Ribeirao do Salto (otto/ANA/BC250)', 'natureza': 'artificial por barramento de curso natural (FBDS; outorga SIGARH de barragem)',
    'espelho_por_fonte_ha': {'FBDS 2013 (RapidEye 5 m)': rep['fbds_2013_ha'], 'IAT WorldView-2 2012': rep['iat_uso2012_wv2_corpos_dagua_ha'], 'ANA massa d agua': rep['ana_massa_dagua_ha'],
                             'IAT 1:50k Paranacidade': rep['iat_massa_50k_paranacidade_ha'], 'CAR declarado': rep['car_declarado_iat_ha'], 'JRC max 1984-2021': rep['jrc_max_extent_1984_2021_ha'],
                             'MapBiomas agua 2024': rep['mapbiomas_agua_2024_ha'], 'S1 -18 dB mediana 2024-26': ref['espejo_actual_por_sensor_ha']['S1 -18 dB mediana'],
                             'S1 -16 dB mediana 2024-26': ref['espejo_actual_por_sensor_ha']['S1 -16 dB mediana'], 'S2 mediana chuvosa 2024-26': ref['valor_ha'],
                             'S2 MNDWI 29/08/2026 (seca)': rep['escena_2026_08_29_mndwi_ha'], 'RF 29/08/2026 (inclui margem umida)': rep['escena_2026_08_29_rf_ha']},
    'espelho_atual_envolvente_ha': ref['envolvente_actual_ha'], 'espelho_referencia_ha': ref['valor_ha'], 'historico_ha': ref['historico_ha'],
    'maior_ou_igual_1ha': 'INDETERMINADO', 'nota_1ha': ref['mayor_o_igual_1ha'],
    'regra': 'art. 4 III: faixa = a da licenca/outorga do barramento; par. 4: dispensa da faixa se espelho < 1 ha — NAO se presume ate medir o perimetro em campo; os 30 m do Arroio 3 sob o espelho nao dependem disso',
    'cenario_faixa_30m': {'app_exigida_g1_ha': g1['app']['cenario_fbds_iat']['exigida_ha'], 'faixa_adicional_ha': g1['app']['cenario_fbds_iat']['faixa_reservatorio_adicional_ha'],
                          'a_recompor_g1_ha': g1['app']['cenario_fbds_iat']['a_recompor_ha'], 'delta_recompor_ha': r2(g1['app']['cenario_fbds_iat']['a_recompor_ha'] - g1['app']['a_recompor_ha']),
                          'nota': 'sensibilidade "se o IAT aplicar a faixa de 30 m do reservatorio" (criterio do mapeamento FBDS app_hidrica); sem faixa legal por defeito'},
    'n_escenas': {'S2_total': HPJ['agua']['n_escenas_s2_total'], 'S2_uteis_represa': HPJ['agua']['n_escenas_s2_utiles_represa'], 'S1': HPJ['agua']['n_escenas_s1']},
    'serie_s2_por_mes_ha': rep['s2_serie_por_escena']['por_mes'],
}
out = HPJ['contexto_regulatorio']['outorgas_en_propiedad'][0]
outorga_v3 = {k: out[k] for k in ('nm_empreendimento', 'nm_tipo_interferencia', 'nr_portaria', 'st_portaria', 'nm_tipo_documento', 'nm_tipo_solicitacao', 'desc_finalidades',
                                   'nm_corpo_hidrico_complemento', 'nm_bacia_hidrografica', 'cod_otto', 'dt_publicacao', 'dt_vencimento', 'vencida', 'dist_espelho_fbds_m', 'x', 'y')}
outorga_v3['leitura'] = 'outorga PREVIA de barragem (Ribeirao do Salto) IRREGULAR e vencida em 08/11/2025: regularizar (outorga de direito de uso / renovacao) junto com o CAR'
man = HPJ['contexto_regulatorio']['mananciais_abastecimento']
manancial_v3 = {'principal': next(m for m in man if m['impeditivo'] == 'Sim'), 'todos': man,
                'leitura': '100% do imovel dentro do manancial de abastecimento publico Rio Congonhas (Portaria 233/2018, impeditivo; ICMS ecologico): intervencoes em APP/RL e o barramento se licenciam sob esse regime'}

# ------------------------------------------------------------- nascentes com veredicto ----
nasc_v3 = []
for c in HPJ['nascentes']['candidatos']:
    v = c['veredicto']
    cls = 'PROVAVEL' if v.startswith('probable') and not c['misma_cabecera_que_nascente_fbds'] else ('MESMA CABECEIRA (nao soma)' if c['misma_cabecera_que_nascente_fbds'] else 'POUCO PROVAVEL')
    nasc_v3.append({'id': c['id'], 'fonte': c['fonte'], 'gleba': c['gleba'], 'x_utm': round(c['x'], 1), 'y_utm': round(c['y'], 1), 'veredicto': cls, 'veredicto_an11': v,
                    'hand_m': c['hand_m'], 'dist_inicio_trecho_otto_m': c['dist_inicio_trecho_otto2020_m'], 'n_dem_cabeceira_100m': c['n_dem_con_cabecera_a_100m'],
                    's2_freq_chuva_max': c['s2_freq_chuva_max_30m'], 's1_freq20_max': c['s1_freq20_max_30m'], 'ndmi_seca_z': c['ndmi_p10_seca_z_robusto'],
                    'uso_iat_2012': c['uso_iat_2012_wv2'], 'puntaje_0_6': c['evidencia']['puntaje_0_6'],
                    'app_50m_ha': g1['app']['nascente_ha'] if c['id'] == '306158' else 0.0,
                    'perenidade': 'NAO verificada por satelite; STF ADI 4903 (interpretacao conforme) inclui intermitentes: raio de 50 m aplicado' if c['id'] == '306158' else None})
nasc_v3.append({'nota': 'dem_2 (em soja): 0 agua em %d cenas S2 e %d S1, NDMI z %.2f, sem base oficial -> sai dos avisos de risco principal; fica como nota topografica (talvegue de 700 m, %.2f ha potenciais SO se houver curso em campo)'
                % (HPJ['agua']['n_escenas_s2_total'], HPJ['agua']['n_escenas_s1'], HPJ['nascentes']['candidatos'][2]['ndmi_p10_seca_z_robusto'], g1['nascentes']['talvegue_dem_risco_ha'])})

# ------------------------------------------------------------- cursos por fonte ----
cursos_v3 = {}
for gl in ('G1', 'G2'):
    cursos_v3[gl] = []
    lst = {a['nome']: a for a in G[gl]['arroios']['lista']}
    for nome, c in HPJ['cursos'][gl].items():
        if nome.startswith('_'):
            continue
        a = lst[nome]
        f = c['long_por_fuente_en_gleba']
        cursos_v3[gl].append({'n': a['n'], 'nome': nome, 'fbds_m': c['long_fbds_m'], 'otto_2020_m': round(f['otto_iat_2020']['km'] * 1000), 'ana_5k_m': round(f['ana_bho_5k_2017']['km'] * 1000),
                              'ibge_bc250_m': round(f['ibge_bc250_2025']['km'] * 1000), 'ensamble_dem_m': round(f['mediana_ensamble_5dem']['km'] * 1000),
                              'car_rio_ate10_m': (c['car_hidrografia_rio_ate10'] or {}).get('long_aprox_m'), 'nome_oficial': ' / '.join(c['nombre_oficial_otto']) or ('Agua do Chapadao ou Agua da Marreca (ANA)' if f['ana_bho_5k_2017']['nombres'] else 'sem nome'),
                              'tipo': a['tipo'], 'represado': a['represado'], 'regime_ibge': ', '.join(c['regime_ibge']) or '-',
                              'regime_nota': 'BC250 rotula todos os trechos da area como Permanente: o atributo nao discrimina' if c['regime_ibge'] else 'sem trecho BC250',
                              'largura': 'ate 10 m (FBDS e CAR); sem agua aberta persistente > 10 m em S2/S1', 'ndmi_seca_eixo_vs_entorno': '%.3f vs %.3f' % (c['perenidad_indicio']['ndmi_p10_seca_eje_media'], c['perenidad_indicio']['ndmi_p10_seca_entorno_100_300m']),
                              'app30_fbds_ha': c['dispersion_dem']['app30_fbds_ha'], 'app30_envolvente_ha': c['dispersion_dem']['app30_envolvente_ha'],
                              'sesgo_ensamble_med_m': c['dispersion_dem']['mediana_ensamble_vs_fbds_med_m'], 'sesgo_ensamble_p90_m': c['dispersion_dem']['mediana_ensamble_vs_fbds_p90_m']})
km_g1_fontes = {'FBDS': G['G1']['arroios']['km_dentro'], 'otto_2020': round(sum(c['otto_2020_m'] for c in cursos_v3['G1']) / 1000, 3), 'ANA_5k': round(sum(c['ana_5k_m'] for c in cursos_v3['G1']) / 1000, 3),
                'IBGE_BC250': round(sum(c['ibge_bc250_m'] for c in cursos_v3['G1']) / 1000, 3), 'ensamble_DEM': round(sum(c['ensamble_dem_m'] for c in cursos_v3['G1']) / 1000, 3)}

# ------------------------------------------------------------- vegetacao v3 (fragmentos com redacao) ----
fr13 = next(f for f in VG['fragmentos']['lista'] if f['frag_id'] == 13)
veg_v3 = {
    'computavel_imovel_ha': veg_g1, 'envolvente_1px_ha': veg_g1_env, 'pct_g1': g1['vegetacao']['pct_da_gleba'],
    'em_app_ha': appveg_g1, 'fora_app_ha': rem_g1, 'conservador_sem_frag13_ha': veg_cons, 'conservador_envolvente_ha': veg_cons_env,
    'g2_floresta_na_imagem_nao_computada_ha': veg_g2_imagem,
    'fragmentos_g1': [
        {'frag_id': 2, 'ha': frag2_g1['area_dentro_ha'], 'leitura': 'parte do fragmento 2 (continuo alem do limite; IAT prioridade A, 23 anos); MapBiomas: 58% floresta em 1985, 71% em 2008 (indicio a 30 m)'},
        {'frag_id': 13, 'ha': f13_ha, 'leitura': 'vegetacao arborea em regeneracao — indicio por serie NDVI 24 meses (min %.2f / max %.2f, sem entressafra), SWIR B11 %.3f vs pastagem 0,250 e textura; sem historico florestal em 2008 (MapBiomas 0%%) nem 2013 (FBDS antropizado); nucleo %.2f ha (p %.2f) / borda %.2f ha (p %.2f); %.2f ha com p < 0,5; estagio sucessional e idade a confirmar em campo (CONAMA 2/1994)'
                                       % (0.57, 0.87, fr13['b11_medio'], fr13['nucleo_ha'], fr13['nucleo_prob_floresta_media'], fr13['borda_ha'], fr13['borda_prob_floresta_media'], fr13['ha_prob_floresta_lt_05'])},
        {'frag_id': 30, 'ha': frag30['area_dentro_ha'], 'leitura': 'sul; sem historico florestal em 2008 (MapBiomas 0%); regeneracao recente a confirmar'}],
    'supressao_pos_2008': {'app_g1_indicio_ha': g1['app']['cenario_pra_pr_20m']['supressao_pos_2008_integral_ha'], 'hansen_pos_2008_ha': VG['mudanca_2008_2025']['hansen']['dentro']['ha_perda_pos_2008'],
                           'imovel_indicio_bruto_ha': VG['mudanca_2008_2025']['ha_por_classe']['supressao_pos_2008'], 'g2_indicio_ha': g2['vegetacao']['supressao_pos_2008_indicio_ha'],
                           'leitura': 'indicio de 0,04 ha na APP da G1 (MapBiomas 30 m; Hansen 0), a validar; o restante da APP sem vegetacao e elegivel ao regime de area consolidada (art. 61-A), sujeito a validacao do IAT'},
    'rf': {'OA': VG['rf']['OA'], 'kappa': VG['rf']['kappa'], 'F1_silvicultura': VG['rf']['F1']['SILVICULTURA'], 'floresta_fora_consenso_ha': VG['rf']['floresta_ha_sem_consenso'], 'floresta_total_ha': VG['rf']['floresta_ha_total_propriedade']},
}

# ------------------------------------------------------------- prazos / PRA ----
pra_v3 = {'faixa_pra_pr': '20 m cursos ate 10 m / 15 m nascente (Lei PR 18.295 art. 17 par. 2, banda 4-10 MF)', 'a_recompor_integral_ha': g1['app']['a_recompor_ha'], 'a_recompor_pra_ha': g1['app']['cenario_pra_pr_20m']['a_recompor_ha'],
          'condicao': 'CAR inscrito ate 31/12/2023 (> 4 MF; art. 29 par. 4, Lei 14.595/2023) e adesao ao PRA em 1 ano da notificacao (art. 59 par. 2); o CAR existe — verificar a data de inscricao',
          'prazos': {'car_maior_4mf': '2023-12-31', 'car_ate_4mf': '2025-12-31', 'prorrogacao_localizada': False},
          'rl_independe_do_pra': 'a regularizacao da RL (art. 66) e independente da adesao ao PRA'}

# ------------------------------------------------------------- KPIs + verificacao ----
kpi = {'area_imovel_ha': r2(area_un), 'area_g1_ha': r2(area1), 'area_g2_ha': r2(area2), 'g2_alqueires': g2['alqueires_paulistas'], 'mf_ha': MF_HA, 'n_mf_imovel': round(n_mf_un, 2), 'n_mf_g1': round(n_mf_g1, 2), 'n_mf_g2': round(n_mf_g2, 2),
       'app_exigivel_imovel_ha': app_un, 'app_envolvente_imovel_ha': env_un, 'app_g1_ha': app_g1, 'app_g1_envolvente_ha': env1, 'app_g2_ha': app_g2, 'app_g2_envolvente_ha': env2,
       'app_com_vegetacao_g1_ha': appveg_g1, 'app_agua_g1_ha': g1['app']['agua_ha'], 'app_a_recompor_ha': g1['app']['a_recompor_ha'], 'app_a_recompor_pra_ha': g1['app']['cenario_pra_pr_20m']['a_recompor_ha'],
       'app_cenario_reserv_exigida_ha': g1['app']['cenario_fbds_iat']['exigida_ha'], 'app_cenario_reserv_recompor_ha': g1['app']['cenario_fbds_iat']['a_recompor_ha'],
       'rl_exigida_ha': r2(rl_ex_un), 'rl_parcela_g1_ha': r2(rl_ex_g1), 'rl_parcela_g2_ha': r2(rl_ex_g2), 'veg_computavel_ha': veg_g1, 'veg_conservador_ha': veg_cons,
       'deficit_ha': def_princ, 'deficit_conservador_ha': def_cons, 'car_rl_averbada_ha': cmp1['rl_car_geom_en_gleba_ha'], 'car_area_ha': car_g1_meta['num_area'],
       'represa_espelho_atual_ha': ref['envolvente_actual_ha'], 'represa_fbds_ha': rep['fbds_2013_ha'], 'rl_proposta_g1_ha': rlp_g1, 'rl_proposta_falta_ha': falta_rlp,
       'km_cursos_g1': G['G1']['arroios']['km_dentro'], 'oa': VG['rf']['OA']}
checks = [
    ('area G1 + G2 = imovel', area1 + area2, area_un),
    ('RL G1 + G2 = RL imovel (3 dec)', rl_ex_g1 + rl_ex_g2, rl_ex_un),
    ('RL exigida = 20% x 157,75', 0.2 * 157.75, rl_ex_un),
    ('deficit principal = 31,55 - 17,70', rl_ex_un - veg_g1, def_princ),
    ('veg conservadora = 17,70 - 10,46', veg_g1 - f13_ha, veg_cons),
    ('deficit conservador = 31,55 - 7,24', rl_ex_un - veg_cons, def_cons),
    ('veg computavel = rem + APP vegetada', rem_g1 + appveg_g1, veg_g1),
    ('APP G1 + G2 = APP imovel', app_g1 + app_g2, app_un),
    ('APP G1 = conforme + agua + recompor (3 dec)', app_g1_3['soma'], apph['G1']['app_fbds_recalculada_ha']),
    ('CAR G1 fecha', g1['mapa_car']['soma_ha_3dec'], area1),
    ('CAR G2 fecha', g2['mapa_car']['soma_ha_3dec'], area2),
    ('CAR imovel fecha', un['mapa_car']['soma_ha_3dec'], area_un),
    ('RL proposta G1 + falta = exigida', rlp_g1 + falta_rlp, rl_ex_un),
    ('cenario reservatorio: 11,96 + 1,66 = 13,62', app_g1 + g1['app']['cenario_fbds_iat']['faixa_reservatorio_adicional_ha'], g1['app']['cenario_fbds_iat']['exigida_ha']),
]
verif = []; ok_all = True
for nome, a, b in checks:
    d = round(float(a) - float(b), 3); ok = abs(d) <= 0.011
    ok_all &= ok
    verif.append({'item': nome, 'a': round(float(a), 3), 'b': round(float(b), 3), 'dif': d, 'ok': ok})
    log('  %-48s %9.3f vs %9.3f  dif %+.3f  %s' % (nome, a, b, d, 'OK' if ok else '<< REVISAR'))

OUT = {
    '_meta': {'versao': 3, 'crs': CRS_METRICO, 'escena': RES['_meta']['escena'], 'fecha_escena': RES['_meta']['fecha_escena'], 'generado': __import__('datetime').date.today().isoformat(),
              'hipotese_principal': 'IMOVEL UNICO (157,75 ha; 7,89 MF; RL 31,55 ha) com a Gleba 2 comprada como terra limpa (0 ha de vegetacao computavel)',
              'fontes': ['resultados_glebas.json (an_07)', 'resultados_analisis.json (an_01-03)', 'hidrologia_pro/resultados_hidrologia_pro.json (an_11)', 'parametros_legales.json']},
    'imovel': {'area_ha': r2(area_un), 'area_ha_3dec': area_un, 'alqueires': un['alqueires_paulistas'], 'n_mf': round(n_mf_un, 2), 'n_mf_em_2008_se_g2_comprada_depois': round(n_mf_g1, 2), 'mf_ha': MF_HA,
               'classe': 'media propriedade (4-15 MF, IN MMA 2/2014 art. 2 I b); faixa de recomposicao da banda 4-10 MF (Lei PR 18.295 art. 17 par. 2)',
               'glebas': {'G1': {'area_ha': r2(area1), 'area_ha_3dec': area1, 'n_mf': round(n_mf_g1, 2), 'rl_parcela_ha': r2(rl_ex_g1)},
                          'G2': {'area_ha': r2(area2), 'area_ha_3dec': area2, 'alqueires': g2['alqueires_paulistas'], 'n_mf': round(n_mf_g2, 2), 'rl_parcela_ha': r2(rl_ex_g2), 'terra_limpa': True}},
               'distancia_entre_glebas_m': G['_meta']['distancia_entre_glebas_m'], 'municipio': PL['municipio'], 'bioma': PL['bioma'], 'manancial': manancial_v3['principal']['nome']},
    'kpi': kpi,
    'reserva_legal': {'exigida_ha': r2(rl_ex_un), 'exigida_3dec': rl_ex_un, 'vegetacao_computavel_ha': veg_g1, 'vegetacao_computavel_envolvente_ha': veg_g1_env, 'remanescente_fora_app_ha': rem_g1, 'app_vegetada_art15_ha': appveg_g1,
                      'deficit_ha': def_princ, 'deficit_envolvente_ha': [r2(rl_ex_un - veg_g1_env[1]), r2(rl_ex_un - veg_g1_env[0])],
                      'variante_conservadora': {'vegetacao_computavel_ha': veg_cons, 'envolvente_ha': veg_cons_env, 'deficit_ha': def_cons, 'exclui': 'fragmento 13 (%.2f ha): sem historico 2008/2013 e fora do consenso do RF' % f13_ha,
                                                'nota_frag30': 'o fragmento 30 (%.2f ha) tambem nao tem historico em 2008; mantido na variante principal' % frag30['area_dentro_ha']},
                      'se_ponta_norte_da_g2_for_do_imovel': {'vegetacao_computavel_ha': un['reserva_legal']['existente_com_app_art15_ha'], 'deficit_ha': def_se_ponta_norte},
                      'sem_computar_app': {'vegetacao_ha': rem_g1, 'deficit_ha': r2(rl_ex_un - rem_g1)},
                      'pct_atendido': round(100 * veg_g1 / rl_ex_un, 1),
                      'localizacao_proposta': {'rl_proposta_recortada_g1_ha': rlp_g1, 'falta_para_exigida_ha': falta_rlp, 'corredor_g1_ha': corr_g1, 'app_a_recompor_incluida_g1_ha': app_rec_incl_g1,
                                               'blocos_imovel': L['reserva_legal']['proposta']['partes_ha'],
                                               'condicao_art15_II': 'a APP a recompor incluida so computa depois de declarada "em processo de recuperacao" ao IAT (PRADA/termo)',
                                               'fragmento_iat_prioridade_A': [{k: v for k, v in f.items() if k != 'geom'} for f in frag_iat],
                                               'nota': 'proposta de an_03 (imovel unico, 5 blocos, %.2f ha) recortada a G1: %.2f ha; faltam %.2f ha a localizar na G1 (ampliar o corredor junto ao fragmento prioritario IAT / Arroio 2) ou compensar (art. 66 III)' % (L['reserva_legal']['proposta']['ha'], rlp_g1, falta_rlp)},
                      'art66': PL['rl_regularizacao_art66'], 'veredicto': 'NAO CONFORME (deficit %.2f ha; conservador %.2f ha)' % (def_princ, def_cons)},
    'app': {'referencia': HPJ['app']['referencia_recomendada'], 'justificacao': HPJ['app']['justificacion'], 'envolvente_regra': HPJ['app']['envolvente_regla'],
            'imovel': {'exigida_ha': app_un, 'envolvente_ha': env_un, 'com_vegetacao_ha': un['app']['com_vegetacao_nativa_ha'], 'agua_ha': un['app']['agua_ha'], 'a_recompor_ha': un['app']['a_recompor_ha']},
            'G1': {'exigida_ha': app_g1, 'exigida_3dec': app_g1_3, 'ensamble_ha': apph['G1']['app_mediana_ensamble_ha'], 'envolvente_ha': env1, 'car_declarada_ha': apph['G1']['app_car_declarada_en_gleba_ha'],
                   'curso_ha': g1['app']['curso_dagua_ha'], 'nascente_ha': g1['app']['nascente_ha'], 'com_vegetacao_ha': appveg_g1, 'agua_ha': g1['app']['agua_ha'], 'a_recompor_ha': g1['app']['a_recompor_ha'],
                   'a_recompor_silvicultura_ha': g1['app']['a_recompor_silvicultura_ha'], 'pct_conforme': g1['app']['pct_conforme'], 'pra_pr': g1['app']['cenario_pra_pr_20m'],
                   'cenario_faixa_reservatorio': represa_v3['cenario_faixa_30m'], 'por_arroio': app_arroios,
                   'arroio1_sesgo': 'todos os 5 DEM deslocam o Arroio 1 para o mesmo lado: mediana %.1f m (p90 %.1f m) do eixo FBDS; APP do arroio %.2f -> %.2f ha: levantar o eixo com GNSS antes de retificar o CAR' % (arr1_sesgo['mediana_ensamble_vs_fbds_med_m'], arr1_sesgo['mediana_ensamble_vs_fbds_p90_m'], arr1_sesgo['app30_fbds_ha'], arr1_sesgo['app30_mediana_ensamble_ha']),
                   'veredicto': 'NAO CONFORME (%.2f ha a recompor; %.2f ha no cenario PRA-PR)' % (g1['app']['a_recompor_ha'], g1['app']['cenario_pra_pr_20m']['a_recompor_ha'])},
            'G2': cenarios_g2['app_g2'], 'conforme_definicao': 'APP com vegetacao nativa segundo a classificacao RF 10 m da cena de 29/08/2026 (nao e a "conformidade" da analise do IAT)',
            'prazos_pra': pra_v3},
    'gleba2_cenarios': cenarios_g2, 'gleba2_ponta_norte': ponta_norte,
    'car_existente': car_v3, 'represa': represa_v3, 'outorga': outorga_v3, 'manancial': manancial_v3,
    'nascentes': nasc_v3, 'cursos': {'G1': cursos_v3['G1'], 'G2': cursos_v3['G2'], 'km_g1_por_fonte': km_g1_fontes, 'criterio_cursos_distintos': G['_meta']['cursos_distintos_criterio'], 'confluencia_m_fora_limite': G['_meta']['confluencia_mais_proxima_do_limite_m']},
    'vegetacao': veg_v3,
    'inventario_por_gleba': {'G1': {k: g1[k] for k in ('area_ha', 'arroios', 'nascentes', 'lagoas', 'app', 'vegetacao', 'mapa_car')}, 'G2': {k: g2[k] for k in ('area_ha', 'arroios', 'nascentes', 'lagoas', 'app', 'vegetacao', 'mapa_car')},
                             'nota': 'inventario descritivo por gleba (an_07); as cotas de RL por gleba NAO sao exigencias independentes no cenario principal'},
    'mapa_car_imovel': un['mapa_car'],
    'dem_vs_curvas_iat': HPJ['dem_ensamble']['dem_vs_curvas_iat_50k'],
    'fontes_governo': HPJ['fuentes'],
    '_verificacao': {'todo_ok': bool(ok_all), 'itens': verif},
}
guardar_json(RESULTADOS_V3, _limpio(OUT))
log('  -> %s (%s)' % (RESULTADOS_V3, 'sumas OK' if ok_all else 'HA ITENS FORA DE TOLERANCIA'))

# ------------------------------------------------------------- capas v3 ----
# vegetacao computavel (renomeada; era gleba_G1_rl_existente)
vc = rl1.copy()
vc = vc.rename(columns={'rl_existente_ha': 'veg_computavel_ha'})
vc['classe'] = vc['classe'].str.replace('remanescente fora da APP', 'remanescente fora da APP (computavel)')
vc['rl_exigida_ha'] = r2(rl_ex_un); vc['deficit_ha'] = def_princ; vc['deficit_conservador_ha'] = def_cons; vc['veg_computavel_ha'] = veg_g1
vc['frag13_regeneracao'] = [bool(poly_only(g).intersection(FL13).area / max(poly_only(g).area, 1) > 0.5) for g in vc.geometry]
guardar_vector(vc, 'v3_vegetacao_computavel')
# fragmentos com rotulo v3
fr = flor1.copy(); fr['gleba'] = 'G1'
fr['leitura_v3'] = fr.frag_id.map({2: veg_v3['fragmentos_g1'][0]['leitura'], 13: 'regeneracao/a confirmar em campo', 30: veg_v3['fragmentos_g1'][2]['leitura']})
fr2 = flor2.copy(); fr2['gleba'] = 'G2'; fr2['leitura_v3'] = 'ponta norte: floresta NAO computada (terra limpa segundo o cliente); limite a conferir'
guardar_vector(gpd.GeoDataFrame(__import__('pandas').concat([fr, fr2], ignore_index=True), crs=CRS_METRICO), 'v3_fragmentos')
# RL proposta v3 = recortada a G1
rlp = gpd.GeoDataFrame([{'classe_car': 'Reserva Legal Proposta', 'area_ha': rlp_g1, 'rl_exigida_ha': r2(rl_ex_un), 'falta_localizar_ha': falta_rlp, 'corredor_ha': corr_g1,
                         'status': 'PROPOSTA recortada a Gleba 1 (imovel unico, G2 terra limpa): %.2f ha; faltam %.2f ha para %.2f; sujeita ao IAT (art. 14); APP a recompor incluida so computa apos art. 15 II' % (rlp_g1, falta_rlp, rl_ex_un)}],
                       geometry=[RLP_G1], crs=CRS_METRICO)
guardar_vector(rlp, 'v3_RL_proposta')
# CAR existente (temas do proprio imovel + CAR de origem da G2), recortado ao imovel + 60 m para o mapa
own = car_hp[car_hp.relacao.isin(['propio_G1', 'cubre_G2'])].copy()
own['tema'] = own.cod_tema
own['area_no_imovel_ha'] = [ha3(poly_only(g).intersection(PROP)) for g in own.geometry]
own = own[['capa', 'cod_tema', 'cod_imovel', 'relacao', 'ind_status', 'des_condic', 'num_area_decl', 'area_geom_ha', 'area_no_imovel_ha', 'geometry']]
guardar_vector(own, 'v3_CAR_existente')
# fragmento IAT prioritario dentro do imovel
if frag_iat:
    guardar_vector(gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geom'} for f in frag_iat], geometry=[f['geom'] for f in frag_iat], crs=CRS_METRICO), 'v3_IAT_fragmento_prioritario')
# nascentes v3
nv = nasc_v.copy()
nv['veredicto_v3'] = [n['veredicto'] for n in nasc_v3[:3]]
nv = nv[['fonte', 'id', 'gleba', 'veredicto_v3', 'veredicto', 'hand_m', 'dist_inicio_trecho_otto2020_m', 'n_dem_con_cabecera_a_100m', 's2_freq_chuva_max_30m', 's1_freq20_max_30m', 'ndmi_p10_seca_z_robusto', 'uso_iat_2012_wv2', 'geometry']]
guardar_vector(nv, 'v3_nascentes')
# represa: espelhos por fonte (capa an_11) + outorga (ponto)
esp = gpd.read_file(os.path.join(HP, 'agua_extensao_maxima.geojson'))
guardar_vector(esp, 'v3_represa_espelhos')
guardar_vector(gpd.GeoDataFrame([outorga_v3], geometry=gpd.points_from_xy([out['x']], [out['y']]), crs=CRS_METRICO), 'v3_outorga_sigarh')
# ponta norte da G2 (a conferir)
guardar_vector(gpd.GeoDataFrame([{'gleba': 'G2', 'floresta_ha': veg_g2_imagem, 'status': 'ponta norte: limite a conferir com a escritura/SIGEF; floresta nao computada (terra limpa)'}], geometry=[FL2], crs=CRS_METRICO), 'v3_G2_ponta_norte')
log('an_12 listo')
