# -*- coding: utf-8 -*-
"""an_07_glebas — diagnostico POR GLEBA (G1 144,21 ha / G2 13,54 ha) e variante "imovel unico".

    python an_07_glebas.py   -> 02_ANALISIS/resultados_glebas.json + gleba_G1_*.geojson / gleba_G2_*.geojson

Regra do cliente: SO o que esta dentro do perimetro; cada gleba avaliada por separado (RL 20% propria,
APP propria). NADA se reclassifica aqui: as capas de 02_ANALISIS (mapa_uso_car, hidrografia FBDS,
nascentes, massas d'agua, RF 10 m, RL_proposta) sao recortadas ao poligono de cada gleba e somadas.
As unicas geometrias derivadas sao as mesmas de desenho de an_03/an_04 (buffer 30/50 m e 20/15 m do
eixo FBDS; faixa oficial FBDS/IAT do reservatorio), usadas para repartir a agua da APP e os cenarios.
No final verifica-se que G1 + G2 reproduz os totais auditados de resultados_analisis.json (+-0,05 ha).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import (ANALISIS, R, P, RESULTADOS_JSON, PROPIEDAD_GEOJSON, CRS_METRICO, FECHA_ESCENA,   # noqa: E402
                          leer_json, guardar_json, leer_vector, leer_raster, vectorizar, guardar_vector,
                          sin_acentos, _limpio, log, titulo)

import geopandas as gpd                                     # noqa: E402
import shapely                                              # noqa: E402
from shapely.geometry import (GeometryCollection, LineString, MultiLineString, MultiPolygon, Point,  # noqa: E402
                              Polygon, shape)
from shapely.ops import linemerge, unary_union              # noqa: E402

RESULTADOS_GLEBAS = os.path.join(ANALISIS, 'resultados_glebas.json')
TOL_HA = 0.05
ALQ_PAULISTA_HA = 2.42


# ------------------------------------------------------------------ helpers ---
def poly_only(g):
    if g is None or g.is_empty:
        return Polygon()
    if isinstance(g, (Polygon, MultiPolygon)):
        return g
    if isinstance(g, GeometryCollection):
        parts = [p for p in g.geoms if isinstance(p, (Polygon, MultiPolygon)) and not p.is_empty]
        return unary_union(parts) if parts else Polygon()
    return Polygon()


def line_only(g):
    if g is None or g.is_empty:
        return LineString()
    if isinstance(g, (LineString, MultiLineString)):
        return g
    if isinstance(g, GeometryCollection):
        parts = [p for p in g.geoms if isinstance(p, (LineString, MultiLineString)) and not p.is_empty]
        return unary_union(parts) if parts else LineString()
    return LineString()


def ha(g):
    return round(poly_only(g).area / 1e4, 2)


def ha3(g):
    return round(poly_only(g).area / 1e4, 3)


def m(g):
    return round(line_only(g).length, 1)


def A_int(g, u):
    return poly_only(g.intersection(u))


# ------------------------------------------------------------------ insumos ---
titulo('an_07_glebas: diagnostico por gleba')
gj = leer_json(PROPIEDAD_GEOJSON)
geoms = [shapely.force_2d(shape(f['geometry'])) for f in gj['features']]
geoms = sorted(geoms, key=lambda g: -g.area)                 # G1 = maior
G1, G2 = geoms[0], geoms[1]
PROP = unary_union(geoms)
UNID = {'G1': G1, 'G2': G2, 'UNICO': PROP}
log('  G1 %.3f ha · G2 %.3f ha (%.2f alqueires paulistas de %.2f ha) · uniao %.3f ha · distancia entre glebas %.1f m'
    % (G1.area / 1e4, G2.area / 1e4, G2.area / 1e4 / ALQ_PAULISTA_HA, ALQ_PAULISTA_HA, PROP.area / 1e4, G1.distance(G2)))

RES = leer_json(RESULTADOS_JSON)
L, H, VG = RES['legal'], RES['hidrografia'], RES['vegetacao']
A_ = lambda n: gpd.read_file(os.path.join(ANALISIS, n + '.geojson'))
car = A_('mapa_uso_car')
car_f = A_('mapa_uso_car_cenario_fbds')
hidro = A_('hidrografia_consolidada')
fb = hidro[hidro.fonte == 'FBDS'].copy()
nasc = A_('nascentes_consolidadas')
massas = A_('massas_dagua_propriedade')
agua_s2 = A_('agua_s2_2026-08-29')
frag = A_('fragmentos_floresta')
rl_prop = A_('RL_proposta')
corr = A_('RL_corredor_recomposicao')
mud = A_('mudanca_2008_2025')
talv = A_('talvegue_dem_candidatos')

# classes RF vetorizadas (mesma fonte de an_03) e recortadas ao imovel
veg_r, prof10 = leer_raster(os.path.join(ANALISIS, 'vegetacao_10m_%s.tif' % FECHA_ESCENA))
veg_r = veg_r['classe']
CL = {}
for cid, nome in [(1, 'FLORESTA'), (2, 'AGUA'), (3, 'ANTROP'), (4, 'SILVI')]:
    v = vectorizar((veg_r == cid).astype(np.uint8), prof10, 'v')
    CL[nome] = poly_only(unary_union(list(v.geometry)).intersection(PROP)) if len(v) else Polygon()
log('  RF dentro do imovel: floresta %.2f · agua %.2f · antropizada %.2f · silvicultura %.2f ha'
    % (ha(CL['FLORESTA']), ha(CL['AGUA']), ha(CL['ANTROP']), ha(CL['SILVI'])))

# MapBiomas 2008 (floresta/agua) para separar consolidada de supressao pos-2008 (mesmo criterio de an_03)
mb, prof30 = leer_raster(R['mb_hist'], bandas=['classification_2008'])
mb08 = mb['classification_2008']
nat08 = vectorizar(np.isin(mb08, [3, 33]).astype(np.uint8), prof30, 'v')
NAT08 = poly_only(unary_union(list(nat08.geometry))) if len(nat08) else Polygon()

# geometrias de DESENHO identicas as de an_03/an_04 (nao produzem cifras novas: repartem as ja auditadas)
lin_fbds = unary_union(list(fb.geometry))
n_fbds_in = nasc[(nasc.fonte == 'FBDS') & nasc.dentro_propriedade]
pts_nasc = unary_union(list(n_fbds_in.geometry)) if len(n_fbds_in) else Point()
APP30 = poly_only(unary_union([lin_fbds.buffer(P['app_curso_m']), pts_nasc.buffer(P['app_nascente_m'])]).intersection(PROP))
FAIXA20 = poly_only(unary_union([lin_fbds.buffer(P['pra_curso_m']), pts_nasc.buffer(P['pra_nascente_m'])]).intersection(PROP))
fbds_app = leer_vector('fbds_app', PROP)
fbds_app['tipo'] = fbds_app['hidrografia'].map(sin_acentos)
fa_massa = fbds_app[fbds_app.tipo.str.contains('massa')]
ESP_FBDS = poly_only(unary_union(list(massas.geometry)))
FAIXA_OFICIAL = poly_only(unary_union(list(fa_massa.geometry)).difference(ESP_FBDS)) if len(fa_massa) else Polygon()
APP_F = poly_only(unary_union([APP30, FAIXA_OFICIAL]))
log('  [desenho] APP30 %.2f ha (JSON %.2f) · faixa20 %.2f · faixa oficial FBDS %.2f (JSON %.2f) · APP cenario FBDS %.2f (JSON %.2f)'
    % (ha(APP30), L['app_total_exigivel']['ha'], ha(FAIXA20), ha(FAIXA_OFICIAL),
       L['reservatorio_artificial']['faixa_oficial_fbds_app_hidrica_dentro_ha'], ha(APP_F), L['app_total_exigivel']['app_total_cenario_fbds_ha']))

# particoes CAR (ja fechadas em 157,75)
def car_sel(prefix, sub=None):
    s = car[car.classe_car.str.startswith(prefix)]
    if sub is not None:
        s = s[s.subclasse == sub]
    return poly_only(unary_union(list(s.geometry))) if len(s) else Polygon()

CAR_APP_CONF = car_sel('APP', 'conforme')
CAR_APP_REC = car_sel('APP', 'a recompor')
CAR_APP_NASC_CONF = poly_only(unary_union(list(car[car.classe_car.str.contains('Nascente') & (car.subclasse == 'conforme')].geometry)))
CAR_APP_NASC_REC = poly_only(unary_union(list(car[car.classe_car.str.contains('Nascente') & (car.subclasse == 'a recompor')].geometry)))
CAR_RESERV = car_sel('Reservat')
CAR_REM = car_sel('Remanescente')
CAR_AGRI = car_sel('Área Consolidada', 'uso agricola')
CAR_SILV = car_sel('Área Consolidada', 'silvicultura')
APP_AGUA = poly_only(CAR_RESERV.intersection(APP30))          # espelho dentro da APP (1,16 ha no total)
APP_SEM = CAR_APP_REC
SUPR = poly_only(APP_SEM.intersection(NAT08))
CONSOL = poly_only(APP_SEM.difference(NAT08))
RECOMP_B = poly_only(unary_union([CONSOL.intersection(FAIXA20), SUPR]))
# cenario FBDS/IAT (mesma logica de an_03)
APPF_VEG = poly_only(APP_F.intersection(CL['FLORESTA']))
APPF_AGUA = poly_only(APP_F.intersection(CL['AGUA']).difference(APPF_VEG))
APPF_SEM = poly_only(APP_F.difference(unary_union([APPF_VEG, APPF_AGUA])))
APPF_SILV = poly_only(APPF_SEM.intersection(CL['SILVI']))
FAIXA_ADIC = poly_only(FAIXA_OFICIAL.difference(APP30))
log('  [check total] APP base %.2f = conforme %.2f + agua %.2f + recompor %.2f · cenario B %.2f (JSON %.2f) · cenario FBDS %.2f / recompor %.2f (JSON %.2f / %.2f)'
    % (ha(APP30), ha(CAR_APP_CONF), ha(APP_AGUA), ha(APP_SEM), ha(RECOMP_B), L['area_consolidada_app']['cenario_B_pra_ha'],
       ha(APP_F), ha(APPF_SEM), L['app_total_exigivel']['cenario_fbds_iat']['ha'], L['app_total_exigivel']['cenario_fbds_iat']['sem_vegetacao_ha']))

# ------------------------------------------------------------------ arroios ---
# fusao topologica dos tramos FBDS COMPLETOS (antes do recorte): linemerge une so nos de grau 2,
# logo uma confluencia (grau 3) separa afluente de curso principal = "cursos distintos"
merged = linemerge(unary_union(list(fb.geometry)))
cursos_all = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
cursos = []
for c in cursos_all:
    inter = line_only(c.intersection(PROP))
    if inter.is_empty or inter.length < 1:
        continue
    seg = fb[fb.geometry.apply(lambda s: s.interpolate(0.5, normalized=True).distance(c) < 1.0)]
    ids = sorted(set(seg.id_fonte.astype(str)))
    ends = [Point(c.coords[0]), Point(c.coords[-1])]
    nasc_end = [r for _, r in n_fbds_in.iterrows() if min(r.geometry.distance(e) for e in ends) < 2.0]
    perene_m = float(sum(line_only(r.geometry.intersection(PROP)).length for _, r in seg.iterrows() if r.regime == 'perene'))
    represado = bool(c.intersects(ESP_FBDS.buffer(15)))
    cursos.append(dict(geom=c, ids=ids, dentro_m=inter.length, y=inter.centroid.y, nasce_dentro=bool(nasc_end),
                       nascente_id=str(nasc_end[0].id_fonte) if nasc_end else None, perene_m=perene_m, represado=represado,
                       comprimento_total_m=c.length))
cursos.sort(key=lambda d: -d['y'])
POS = ['norte', 'central', 'sul', 'sul-2', 'sul-3']
for k, c in enumerate(cursos, start=1):
    c['n'] = k
    c['posicao'] = POS[k - 1]
    c['nome'] = 'Arroio %d (%s)' % (k, c['posicao'])
# confluencias: no de grau >=3 mais proximo do imovel entre cursos
nodes = {}
for c in cursos_all:
    for e in (c.coords[0], c.coords[-1]):
        key = (round(e[0], 1), round(e[1], 1))
        nodes[key] = nodes.get(key, 0) + 1
conflu = [(Point(k), Point(k).distance(PROP)) for k, v in nodes.items() if v >= 3]
conflu.sort(key=lambda kv: kv[1])
for c in cursos:
    c['confluencia_dist_limite_m'] = round(min(Point(c['geom'].coords[0]).distance(PROP), Point(c['geom'].coords[-1]).distance(PROP)), 1)
log('  cursos FBDS distintos que tocam o imovel: %d' % len(cursos))
for c in cursos:
    log('    %-18s ids %-16s dentro %6.1f m · nasce dentro=%s (%s) · perene(IBGE) %.0f m · represado=%s · extremo mais proximo do limite %.1f m'
        % (c['nome'], ','.join(c['ids']), c['dentro_m'], c['nasce_dentro'], c['nascente_id'], c['perene_m'], c['represado'], c['confluencia_dist_limite_m']))
if conflu:
    log('  confluencia mais proxima do limite: %.1f m (%s)' % (conflu[0][1], [round(v) for v in conflu[0][0].coords[0]]))

# ------------------------------------------------------------------ por unidade
OUT = {}
CAPAS = {}


def situ_area(g, u):
    return ha(A_int(g, u))


for uid, U in UNID.items():
    area_ha = U.area / 1e4
    rl_ex = round(0.2 * area_ha, 2)
    d = {'area_ha': round(area_ha, 2), 'area_ha_3dec': round(area_ha, 3),
         'alqueires_paulistas': round(area_ha / ALQ_PAULISTA_HA, 2),
         'rl_pct': 0.2, 'rl_exigida_ha': rl_ex}
    # --- arroios
    arr = []
    for c in cursos:
        inter = line_only(c['geom'].intersection(U))
        if inter.is_empty or inter.length < 1:
            continue
        nasc_in = bool(c['nasce_dentro'] and n_fbds_in[n_fbds_in.id_fonte.astype(str) == c['nascente_id']].geometry.iloc[0].within(U))
        per_in = float(sum(line_only(r.geometry.intersection(U)).length
                           for _, r in fb[fb.id_fonte.astype(str).isin(c['ids'])].iterrows() if r.regime == 'perene'))
        arr.append({'n': c['n'], 'nome': c['nome'], 'posicao': c['posicao'], 'fbds_ids': c['ids'],
                    'comprimento_dentro_m': round(inter.length, 1), 'comprimento_total_fbds_m': round(c['comprimento_total_m'], 1),
                    'nasce_dentro': nasc_in, 'nascente_fbds_id': c['nascente_id'] if nasc_in else None,
                    'tipo': 'nasce na gleba' if nasc_in else 'atravessa',
                    'represado': bool(inter.intersects(ESP_FBDS.buffer(15))) or (c['represado'] and uid != 'G2'),
                    'regime_coincide_ibge_perene_m': round(per_in, 1),
                    'largura_classe': 'ate 10 m (FBDS)', 'app_faixa_m': P['app_curso_m'], 'geom': inter})
    d['arroios'] = {'n': len(arr), 'km_dentro': round(sum(a['comprimento_dentro_m'] for a in arr) / 1e3, 3),
                    'lista': [{k: v for k, v in a.items() if k != 'geom'} for a in arr]}
    # --- nascentes
    nf = n_fbds_in[n_fbds_in.geometry.within(U)]
    nd = nasc[nasc.candidato_dem & nasc.geometry.within(U)]
    d['nascentes'] = {'fbds_n': int(len(nf)), 'fbds_ids': nf.id_fonte.astype(str).tolist(),
                      'candidatos_dem_n': int(len(nd)), 'candidatos_dem_ids': nd.id_fonte.astype(str).tolist(),
                      'talvegue_dem_risco_ha': (L['app_nascente']['candidatas_dem']['talvegue_dem_risco']['app_potencial_talvegue_fora_app_exigivel_ha']
                                                if len(talv) and talv.geometry.iloc[0].intersects(U) else 0.0)}
    # --- lagoas / represas
    ms = massas[massas.geometry.intersects(U)]
    lag = []
    for _, r in ms.iterrows():
        gi = A_int(r.geometry, U)
        if gi.area < 10:
            continue
        lag.append({'massa_id': int(r.massa_id), 'corpo_id': int(r.corpo_id), 'natureza': r.natureza,
                    'barramento_curso_natural': bool(r.barramento_curso_natural),
                    'espelho_fbds_2013_dentro_ha': ha(gi),
                    'espelho_mndwi_2026_ha': float(r.area_s2_2026_ha), 'jrc_occurrence_media': float(r.jrc_occurrence_media),
                    'espelho_jrc_max_extent_ha': float(r.area_jrc_max_extent_ha), 'geom': gi})
    corpos = sorted(set(x['corpo_id'] for x in lag))
    d['lagoas'] = {'n_massas_fbds': len(lag), 'n_corpos': len(corpos),
                   'espelho_fbds_2013_ha': ha(A_int(ESP_FBDS, U)), 'espelho_rf_2026_ha': situ_area(CAR_RESERV, U),
                   'espelho_mndwi_2026_ha': round(float(sum(x['espelho_mndwi_2026_ha'] for x in lag)), 2),
                   'espelho_jrc_max_extent_ha': (L['reservatorio_artificial']['corpos_dagua'][0]['area_jrc_max_extent_ha'] if lag else 0.0),
                   'dispensa_art4_par4_lt1ha': bool(any(x for x in lag)) and bool(L['reservatorio_artificial']['dispensa_art4_par4_algum']),
                   'lista': [{k: v for k, v in x.items() if k != 'geom'} for x in lag]}
    # --- APP base (30 m / 50 m) a partir das particoes CAR
    app_conf = A_int(CAR_APP_CONF, U); app_rec = A_int(CAR_APP_REC, U); app_agua = A_int(APP_AGUA, U)
    app_tot = ha3(app_conf) + ha3(app_rec) + ha3(app_agua)
    app30_u = A_int(APP30, U)
    app_silv = A_int(CL['SILVI'].intersection(APP_SEM), U)
    recB = A_int(RECOMP_B, U)
    appF_veg = A_int(APPF_VEG, U); appF_agua = A_int(APPF_AGUA, U); appF_sem = A_int(APPF_SEM, U); appF_silv = A_int(APPF_SILV, U)
    appF_tot = A_int(APP_F, U)
    d['app'] = {
        'exigida_ha': round(app_tot, 2), 'exigida_buffer_desenho_ha': ha(app30_u),
        'curso_dagua_ha': round(ha3(A_int(CAR_APP_CONF.difference(CAR_APP_NASC_CONF), U)) + ha3(A_int(CAR_APP_REC.difference(CAR_APP_NASC_REC), U)) + ha3(app_agua), 2),
        'nascente_ha': round(ha3(A_int(CAR_APP_NASC_CONF, U)) + ha3(A_int(CAR_APP_NASC_REC, U)), 2),
        'com_vegetacao_nativa_ha': ha(app_conf), 'agua_ha': ha(app_agua), 'a_recompor_ha': ha(app_rec),
        'a_recompor_silvicultura_ha': ha(app_silv),
        'pct_conforme': min(100.0, round(100 * app_conf.area / (app_tot * 1e4), 1)) if app_tot > 0 else None,
        'pct_conforme_incl_agua': min(100.0, round(100 * (app_conf.area + app_agua.area) / (app_tot * 1e4), 1)) if app_tot > 0 else None,
        'cenario_pra_pr_20m': {'a_recompor_ha': ha(recB), 'supressao_pos_2008_integral_ha': ha(A_int(SUPR, U)),
                               'consolidada_na_faixa_20m_ha': ha(A_int(CONSOL.intersection(FAIXA20), U)),
                               'excedente_20_30m_mantido_ha': ha(A_int(CONSOL.difference(FAIXA20), U)),
                               'base': 'Lei PR 18.295/2014 art. 17 par. 2 (4-10 MF): 20 m em cursos ate 10 m; nascente raio 15 m; exige CAR ate 31/12/2023 e adesao ao PRA'},
        'cenario_fbds_iat': {'exigida_ha': ha(appF_tot), 'faixa_reservatorio_adicional_ha': ha(A_int(FAIXA_ADIC, U)),
                             'com_vegetacao_nativa_ha': ha(appF_veg), 'agua_ha': ha(appF_agua), 'a_recompor_ha': ha(appF_sem),
                             'a_recompor_silvicultura_ha': ha(appF_silv),
                             'base': 'APP base U faixa de 30 m da capa oficial IAT_FBDS_app_hidrica (massa d agua) do reservatorio'},
        'veredicto': 'CONFORME' if ha(app_rec) < 0.005 else 'NAO CONFORME',
        'veredicto_txt': ('CONFORME' if ha(app_rec) < 0.005 else 'NAO CONFORME (%.2f ha a recompor; %.2f ha no cenario PRA-PR)' % (ha(app_rec), ha(recB))),
    }
    # --- vegetacao nativa
    fl_u = A_int(CL['FLORESTA'], U)
    rem = A_int(CAR_REM, U)
    frs = []
    for _, r in frag.iterrows():
        gi = A_int(r.geometry, U)
        if gi.area >= 100:
            frs.append({'frag_id': int(r.frag_id), 'area_dentro_ha': ha(gi), 'area_total_ha': float(r.area_ha),
                        'persistencia': r.persistencia, 'geom': gi})
    d['vegetacao'] = {
        'floresta_nativa_rf_ha': ha(fl_u), 'floresta_nativa_car_ha': round(ha3(rem) + ha3(app_conf), 2),
        'pct_da_gleba': round(100 * (rem.area + app_conf.area) / U.area, 1),
        'dentro_app_ha': ha(app_conf), 'fora_app_ha': ha(rem),
        'silvicultura_ha': situ_area(CL['SILVI'], U), 'silvicultura_fora_app_car_ha': situ_area(CAR_SILV, U),
        'agua_rf_ha': situ_area(CL['AGUA'], U), 'area_agricola_car_ha': situ_area(CAR_AGRI, U),
        'antropizada_rf_ha': situ_area(CL['ANTROP'], U),
        'fragmentos': [{k: v for k, v in f.items() if k != 'geom'} for f in frs],
        'supressao_pos_2008_indicio_ha': ha(A_int(poly_only(unary_union(list(mud[mud.classe == 'supressao_pos_2008'].geometry))), U)),
    }
    # --- Reserva Legal
    exist = ha3(rem) + ha3(app_conf)
    deficit = round(max(0.0, rl_ex - exist), 2)
    rlp = A_int(poly_only(unary_union(list(rl_prop.geometry))), U)
    cor = A_int(poly_only(unary_union(list(corr.geometry))), U)
    d['reserva_legal'] = {
        'exigida_ha': rl_ex, 'remanescente_fora_app_ha': ha(rem), 'app_com_vegetacao_art15_ha': ha(app_conf),
        'existente_com_app_art15_ha': round(exist, 2), 'existente_sem_app_ha': ha(rem),
        'deficit_com_app_art15_ha': deficit, 'deficit_sem_app_ha': round(max(0.0, rl_ex - ha3(rem)), 2),
        'pct_atendido': round(100 * exist / rl_ex, 1) if rl_ex else None,
        'rl_proposta_recortada_ha': ha(rlp), 'corredor_recomposicao_recortado_ha': ha(cor),
        'rl_proposta_recortada_vs_exigida_ha': round(ha3(rlp) - rl_ex, 2),
        'veredicto': 'CONFORME' if deficit < 0.005 else 'NAO CONFORME',
        'veredicto_txt': 'CONFORME' if deficit < 0.005 else 'NAO CONFORME (deficit %.2f ha)' % deficit,
    }
    if uid == 'G2':
        d['reserva_legal']['monte_necessario_para_estar_na_lei'] = {
            'rl_20pct_ha': rl_ex, 'app_propria_ha': round(app_tot, 2),
            'minimo_vegetacao_nativa_com_art15_ha': rl_ex,                      # APP vegetada computa dentro da RL (art. 15)
            'minimo_vegetacao_nativa_sem_art15_ha': round(rl_ex + app_tot, 2),  # se a APP nao for computada na RL
            'hoje_imagem_mostra_ha': round(exist, 2), 'hoje_imagem_mostra_rf_raster_ha': ha(fl_u),
            'falta_com_art15_ha': deficit, 'falta_sem_art15_ha': round(max(0.0, rl_ex + app_tot - exist), 2),
            'nota': 'o cliente afirma que a compra dos 6 alqueires NAO incluia monte; a imagem mostra floresta na ponta norte da '
                    'gleba (fragmento 2, continuo com a mata do vizinho): confirmar em campo / escritura se pertence a gleba 2'}
    # --- mapa CAR por gleba
    rows = []
    geoms_car = []
    for _, r in car.iterrows():
        gi = A_int(r.geometry, U)
        if gi.area < 1:
            continue
        rows.append({'classe_car': r.classe_car, 'subclasse': r.subclasse, 'situacao': r.situacao, 'area_ha': ha(gi), 'nota': r.nota})
        geoms_car.append(gi)
    soma = round(sum(x['area_ha'] for x in rows), 2)
    soma3 = round(sum(A_int(r.geometry, U).area for _, r in car.iterrows()) / 1e4, 3)
    d['mapa_car'] = {'ha': rows, 'soma_ha': round(soma3, 2), 'soma_2dec_das_linhas_ha': soma, 'soma_ha_3dec': soma3, 'fecha': bool(abs(soma3 - area_ha) <= 0.02),
                     'diferenca_ha': round(soma3 - area_ha, 3)}
    log('  %-5s %7.2f ha · arroios %d (%.3f km) · nasc FBDS %d · lagoas %d massas/%d corpo · APP %.2f (veg %.2f | agua %.2f | recompor %.2f; PRA %.2f; FBDS %.2f/%.2f) · '
        'floresta %.2f · RL %.2f / existente %.2f / deficit %.2f · CAR soma %.3f (%s)'
        % (uid, area_ha, d['arroios']['n'], d['arroios']['km_dentro'], d['nascentes']['fbds_n'], d['lagoas']['n_massas_fbds'], d['lagoas']['n_corpos'],
           d['app']['exigida_ha'], d['app']['com_vegetacao_nativa_ha'], d['app']['agua_ha'], d['app']['a_recompor_ha'],
           d['app']['cenario_pra_pr_20m']['a_recompor_ha'], d['app']['cenario_fbds_iat']['exigida_ha'], d['app']['cenario_fbds_iat']['a_recompor_ha'],
           d['vegetacao']['floresta_nativa_car_ha'], rl_ex, exist, deficit, soma3, 'fecha' if d['mapa_car']['fecha'] else 'NAO FECHA'))
    OUT[uid] = d
    # capas
    if uid in ('G1', 'G2'):
        CAPAS[uid] = {}
        CAPAS[uid]['car'] = gpd.GeoDataFrame([{**r, 'gleba': uid} for r in rows], geometry=geoms_car, crs=CRS_METRICO)
        app_rows, app_geoms = [], []
        for nome_cl, g_, sit in [('curso', A_int(CAR_APP_CONF.difference(CAR_APP_NASC_CONF), U), 'conforme'),
                                 ('curso', A_int(CAR_APP_REC.difference(CAR_APP_NASC_REC), U), 'a recompor'),
                                 ('nascente', A_int(CAR_APP_NASC_CONF, U), 'conforme'),
                                 ('nascente', A_int(CAR_APP_NASC_REC, U), 'a recompor'),
                                 ('curso', app_agua, 'agua')]:
            if g_.area < 1:
                continue
            if sit == 'a recompor':
                for g2_, pra in [(poly_only(g_.intersection(RECOMP_B)), True), (poly_only(g_.difference(RECOMP_B)), False)]:
                    if g2_.area >= 1:
                        app_rows.append({'gleba': uid, 'feicao': nome_cl, 'situacao': sit, 'cenario': 'base', 'pra_pr_recompor': pra, 'area_ha': ha(g2_)}); app_geoms.append(g2_)
            else:
                app_rows.append({'gleba': uid, 'feicao': nome_cl, 'situacao': sit, 'cenario': 'base', 'pra_pr_recompor': False, 'area_ha': ha(g_)}); app_geoms.append(g_)
        for g_, sit in [(A_int(poly_only(FAIXA_ADIC.intersection(APPF_SEM)), U), 'a recompor'),
                        (A_int(poly_only(FAIXA_ADIC.intersection(APPF_AGUA)), U), 'agua'),
                        (A_int(poly_only(FAIXA_ADIC.intersection(APPF_VEG)), U), 'conforme')]:
            if g_.area >= 1:
                app_rows.append({'gleba': uid, 'feicao': 'reservatorio faixa 30 m', 'situacao': sit, 'cenario': 'fbds_iat_adicional', 'pra_pr_recompor': False, 'area_ha': ha(g_)}); app_geoms.append(g_)
        CAPAS[uid]['app'] = gpd.GeoDataFrame(app_rows, geometry=app_geoms, crs=CRS_METRICO)
        rl_rows, rl_geoms = [], []
        for g_, cl in [(rem, 'remanescente fora da APP'), (app_conf, 'APP com vegetacao (art. 15)')]:
            if g_.area >= 1:
                rl_rows.append({'gleba': uid, 'classe': cl, 'area_ha': ha(g_), 'rl_exigida_ha': rl_ex, 'rl_existente_ha': round(exist, 2), 'deficit_ha': deficit}); rl_geoms.append(g_)
        CAPAS[uid]['rl_existente'] = gpd.GeoDataFrame(rl_rows, geometry=rl_geoms, crs=CRS_METRICO)
        CAPAS[uid]['arroios'] = gpd.GeoDataFrame([{k: (','.join(v) if k == 'fbds_ids' else v) for k, v in a.items() if k != 'geom'} for a in arr],
                                                 geometry=[a['geom'] for a in arr], crs=CRS_METRICO)
        CAPAS[uid]['lagoas'] = gpd.GeoDataFrame([{k: v for k, v in x.items() if k != 'geom'} for x in lag] or [], geometry=[x['geom'] for x in lag], crs=CRS_METRICO)
        CAPAS[uid]['floresta'] = gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geom'} for f in frs], geometry=[f['geom'] for f in frs], crs=CRS_METRICO)

# ------------------------------------------------------------------ verificacao G1 + G2 vs auditado
titulo('Verificacao: G1 + G2 vs totais auditados (resultados_analisis.json)')
g1, g2, un = OUT['G1'], OUT['G2'], OUT['UNICO']
AT = L['app_total_exigivel']; RLJ = L['reserva_legal']; CB = L['area_consolidada_app']
checks = [
    ('area imovel', g1['area_ha_3dec'] + g2['area_ha_3dec'], L['imovel_ha']),
    ('CAR soma', g1['mapa_car']['soma_ha_3dec'] + g2['mapa_car']['soma_ha_3dec'], L['mapa_uso_car']['soma_ha']),
    ('APP exigivel', g1['app']['exigida_ha'] + g2['app']['exigida_ha'], AT['ha']),
    ('APP com vegetacao', g1['app']['com_vegetacao_nativa_ha'] + g2['app']['com_vegetacao_nativa_ha'], AT['com_vegetacao_nativa_ha']),
    ('APP agua', g1['app']['agua_ha'] + g2['app']['agua_ha'], AT['agua_ha']),
    ('APP a recompor', g1['app']['a_recompor_ha'] + g2['app']['a_recompor_ha'], AT['sem_vegetacao_ha']),
    ('APP recompor PRA-PR', g1['app']['cenario_pra_pr_20m']['a_recompor_ha'] + g2['app']['cenario_pra_pr_20m']['a_recompor_ha'], CB['cenario_B_pra_ha']),
    ('APP cenario FBDS', g1['app']['cenario_fbds_iat']['exigida_ha'] + g2['app']['cenario_fbds_iat']['exigida_ha'], AT['cenario_fbds_iat']['ha']),
    ('APP cenario FBDS recompor', g1['app']['cenario_fbds_iat']['a_recompor_ha'] + g2['app']['cenario_fbds_iat']['a_recompor_ha'], AT['cenario_fbds_iat']['sem_vegetacao_ha']),
    ('floresta (CAR: rem + APP veg)', g1['vegetacao']['floresta_nativa_car_ha'] + g2['vegetacao']['floresta_nativa_car_ha'], RLJ['disponivel_com_app_art15_ha']),
    ('floresta RF raster', g1['vegetacao']['floresta_nativa_rf_ha'] + g2['vegetacao']['floresta_nativa_rf_ha'], VG['cobertura_propriedade']['floresta_rf_ha']),
    ('remanescente fora APP', g1['reserva_legal']['remanescente_fora_app_ha'] + g2['reserva_legal']['remanescente_fora_app_ha'], RLJ['remanescente_fora_app_ha']),
    ('RL exigida', g1['reserva_legal']['exigida_ha'] + g2['reserva_legal']['exigida_ha'], RLJ['exigida_ha']),
    ('RL deficit', g1['reserva_legal']['deficit_com_app_art15_ha'] + g2['reserva_legal']['deficit_com_app_art15_ha'], RLJ['deficit_com_app_art15_ha']),
    ('km FBDS dentro', g1['arroios']['km_dentro'] + g2['arroios']['km_dentro'], H['tabla_fontes_propriedade']['FBDS']['km_dentro_propriedade']),
    ('espelho FBDS 2013', g1['lagoas']['espelho_fbds_2013_ha'] + g2['lagoas']['espelho_fbds_2013_ha'], L['reservatorio_artificial']['espelho_fbds_total_ha']),
    ('espelho RF 2026', g1['lagoas']['espelho_rf_2026_ha'] + g2['lagoas']['espelho_rf_2026_ha'], L['reservatorio_artificial']['espelho_rf_agua_2026_total_ha']),
    ('RL proposta recortada', g1['reserva_legal']['rl_proposta_recortada_ha'] + g2['reserva_legal']['rl_proposta_recortada_ha'], RLJ['proposta']['ha']),
]
verif = []
todo_ok = True
for nome, soma, ref in checks:
    dif = round(soma - ref, 3)
    ok = abs(dif) <= TOL_HA
    todo_ok &= ok
    verif.append({'item': nome, 'g1_mais_g2': round(soma, 3), 'auditado': ref, 'diferenca': dif, 'ok': ok})
    log('  %-32s G1+G2 = %8.3f   auditado = %8.3f   dif = %+.3f  %s' % (nome, soma, ref, dif, 'OK' if ok else '<< REVISAR'))
explica = ('As diferencas ficam no arredondamento a 2 decimais por gleba (ate 0,01 ha por parcela). A APP e os cursos foram calculados sobre '
           'a UNIAO das duas glebas e depois recortados: como as glebas nao se tocam (%.1f m de distancia) nada se perde na linha de divisao; '
           'a faixa de 30 m do Arroio 1 cruza a franja entre as glebas e a parte que cai fora dos dois poligonos nao e APP do imovel. '
           'A floresta por gleba a partir do raster RF (contagem de pixeles de 10 m cortados pelo limite) difere ate 0,03 ha da soma das '
           'particoes CAR (remanescente + APP vegetada), que e a cifra oficial usada.' % G1.distance(G2))
log('  ' + explica)

OUT['_verificacao'] = {'tolerancia_ha': TOL_HA, 'todo_ok': bool(todo_ok), 'itens': verif, 'explicacao': explica}
OUT['_meta'] = {'crs': CRS_METRICO, 'escena': RES['_meta']['escena'], 'fecha_escena': FECHA_ESCENA,
                'generado': __import__('datetime').date.today().isoformat(),
                'glebas': {'G1': 'imovel principal (poligono maior)', 'G2': 'os "6 alqueires" (poligono menor, %.2f alq. paulistas de %.2f ha)' % (G2.area / 1e4 / ALQ_PAULISTA_HA, ALQ_PAULISTA_HA),
                           'UNICO': 'variante imovel unico (uniao das duas glebas, CAR em uma so matricula)'},
                'distancia_entre_glebas_m': round(G1.distance(G2), 1),
                'cursos_distintos_criterio': 'linemerge sobre os tramos FBDS completos (nos de grau 2 unidos; confluencia separa afluente de curso principal)',
                'confluencia_mais_proxima_do_limite_m': round(conflu[0][1], 1) if conflu else None}
guardar_json(RESULTADOS_GLEBAS, _limpio(OUT))

# ------------------------------------------------------------------ capas
lim = gpd.GeoDataFrame([{'gleba': 'G1', 'nome': 'Gleba 1 - imovel principal', 'area_ha': round(G1.area / 1e4, 2), 'alqueires': round(G1.area / 1e4 / ALQ_PAULISTA_HA, 2), 'rl_exigida_ha': OUT['G1']['rl_exigida_ha']},
                        {'gleba': 'G2', 'nome': 'Gleba 2 - os 6 alqueires', 'area_ha': round(G2.area / 1e4, 2), 'alqueires': round(G2.area / 1e4 / ALQ_PAULISTA_HA, 2), 'rl_exigida_ha': OUT['G2']['rl_exigida_ha']}],
                       geometry=[G1, G2], crs=CRS_METRICO)
guardar_vector(lim, 'gleba_limites')
for uid in ('G1', 'G2'):
    for nome, g in CAPAS[uid].items():
        if len(g) == 0:
            log('  (%s_%s vazia: nao se grava)' % (uid, nome))
            continue
        guardar_vector(g, 'gleba_%s_%s' % (uid, nome))
log('an_07 listo' + ('' if todo_ok else '  << HA ITENS FORA DE TOLERANCIA'))
