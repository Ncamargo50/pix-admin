# -*- coding: utf-8 -*-
"""dron_04: APP, Reserva Legal, mapa CAR e cruzamento com o governo POR IMOVEL (v5, so drone).

APP (Lei 12.651/2012 art. 4): curso d'agua <= 10 m -> 30 m desde o EIXO OFICIAL FBDS/IAT 1:25.000
(sob dossel o drone nao ve a calha; o eixo e referencia oficial, e se diz); nascente FBDS 306158 ->
raio 50 m; reservatorio por barramento (represa, espelho 22-mai-2026 >= 1 ha: sem dispensa do par. 4)
-> faixa "a definir pelo IAT" (art. 4 III): cenario espelho + 30 m.
Cenario PRA (art. 61-A + Lei PR 18.295 art. 17 par. 2): Santo Antonio = 7,2 MF (4-10 MF) -> 20 m /
nascente 15 m. Os 6 alqueires (0,56 MF pelo poligono): se imovel proprio <= 1 MF -> art. 61-A par. 1 =
5 m, nascente 15 m, art. 61-B I (teto 10 % da area); se parte do imovel de origem > 4 MF -> 20 m.
Ambos os regimes se reportam com a aritmetica.
RL (art. 12 II): 20 % do imovel; art. 15: APP vegetada computa; art. 12 par. 1: area desmembrada de
imovel > 4 MF mantem os 20 %. Vegetacao computavel = nativa (arborea + arbustiva) medida SO no drone,
MMU 0,05 ha. Faixa sem cobertura do drone: NAO AVALIADO (nem soma nem desconta).
Os 6 alqueires: comprados como terra limpa -> computavel 0 por regra; a mata da ponta norte (fora do
poligono atual) se reporta a parte, "a conferir na escritura".
Cruzamento com o governo: consulta HOJE (2026-09-06) a replica SICAR do IAT (ArcGIS REST) e a camada
de outorgas SIGARH; se um servico nao responde, usa datos_externos/gov_pro (data daquela consulta).
"""
import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dron_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Point, Polygon
from shapely.ops import unary_union

cabecera('dron_04_legal')
LEG = leer_json(PARAMETROS_LEGALES)
APP_M = LEG['app_curso_dagua_m']['lt10']; NASC_M = LEG['app_nascente_m']
PRA_M = LEG['recomposicao_61A']['curso_dagua_ate_10m_m']; PRA_NASC_M = LEG['recomposicao_61A']['nascente_raio_m']
RL_PCT = LEG['rl_pct']; MF_HA = LEG['modulo_fiscal_ha']
FAIXA_RESERV_M = 30
MMU_RL_HA = 0.05
CARS = {k: IMOVEIS[k]['car'] for k in ORDEM_IMOVEIS}
GOV_DIR = os.path.join(SALIDA_RAIZ, 'gov_%s' % HOY)
os.makedirs(GOV_DIR, exist_ok=True)

# =====================================================================================================
# 0. consulta de HOJE ao governo (IAT replica SICAR + outorgas SIGARH/CRH)
# =====================================================================================================
IAT = 'https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/%s/FeatureServer/%d'
CAPAS_CAR = {0: 'hidrografia', 1: 'app_total', 2: 'reserva_legal', 3: 'vegetacao_nativa', 4: 'area_consolidada', 5: 'area_pousio',
             6: 'servidao_administrativa', 7: 'uso_restrito', 8: 'area_imovel'}


def consultar_gov_hoje():
    """Devuelve dict con la situacion ACTUAL (o la cache con su fecha si el servicio no responde)."""
    import requests
    CA = 'C:/certs/certifi_icpbrasil.pem'
    verify = CA if os.path.exists(CA) else True
    where_car = "cod_imovel IN ('%s','%s')" % (CARS['santo_antonio'], CARS['seis_alqueires'])
    SIT = {'data_consulta': HOY, 'hora_inicio': time.strftime('%Y-%m-%d %H:%M:%S'), 'servicos': {}, 'car': {}, 'outorga': {}, 'sicar_nacional': {}}
    log('[consulta ao governo HOJE %s]' % SIT['hora_inicio'])
    # --- CAR (IAT, replica SICAR) ----------------------------------------------------------------
    for lid, nome in CAPAS_CAR.items():
        url = IAT % ('Base_Geo_Cadastro_Ambiental_rural', lid)
        reg = {'url': url + '/query', 'where': where_car, 'hora': time.strftime('%H:%M:%S'), 'ok': False}
        try:
            m = requests.get(url, params={'f': 'json'}, timeout=60, verify=verify).json()
            reg['copyright_servico'] = m.get('copyrightText'); reg['nome_capa'] = m.get('name')
            r = requests.get(url + '/query', params={'where': where_car, 'outFields': '*', 'outSR': 4326, 'f': 'geojson'}, timeout=120, verify=verify)
            r.raise_for_status()
            j = r.json()
            if 'error' in j:
                raise RuntimeError(str(j['error'])[:200])
            feats = j.get('features', [])
            reg['ok'] = True; reg['n'] = len(feats); reg['http'] = r.status_code
            with open(os.path.join(GOV_DIR, 'IAT_CAR_%s_%s.geojson' % (nome, HOY)), 'w', encoding='utf-8') as f:
                json.dump({'type': 'FeatureCollection', 'features': feats}, f, ensure_ascii=False)
            reg['campos_crus'] = [ft['properties'] for ft in feats]
            log('  IAT CAR/%-24s %2d feats  (copyright %s)' % (nome, len(feats), reg.get('copyright_servico')))
        except Exception as e:   # noqa: BLE001
            reg['erro'] = str(e)[:300]
            log('  IAT CAR/%-24s NAO RESPONDEU: %s' % (nome, reg['erro'][:120]))
        SIT['servicos']['IAT_CAR_%s' % nome] = reg
    # --- outorga SIGARH + CRH (IAT) ------------------------------------------------------------------
    for serv, where, nome in (('outorgas_sigarh', "nr_portaria='26039/2023/OP-GOUT'", 'outorga_sigarh_26039_2023'),
                              ('outorgas_sigarh', "nm_requerente LIKE '%Bigati%'", 'outorgas_sigarh_requerente_bigati'),
                              ('out_captacao_crh', None, 'outorgas_captacao_crh_bbox')):
        url = IAT % (serv, 0)
        p = {'outFields': '*', 'outSR': 4326, 'f': 'geojson'}
        if where:
            p['where'] = where
        else:
            p.update(where='1=1', geometry='-50.70,-23.52,-50.62,-23.45', geometryType='esriGeometryEnvelope', inSR=4326, spatialRel='esriSpatialRelIntersects')
        reg = {'url': url + '/query', 'where': p.get('where'), 'hora': time.strftime('%H:%M:%S'), 'ok': False}
        try:
            r = requests.get(url + '/query', params=p, timeout=120, verify=verify)
            r.raise_for_status(); j = r.json()
            if 'error' in j:
                raise RuntimeError(str(j['error'])[:200])
            feats = j.get('features', [])
            reg['ok'] = True; reg['n'] = len(feats); reg['http'] = r.status_code
            reg['campos_crus'] = [ft['properties'] for ft in feats]
            reg['geometrias'] = [ft['geometry'] for ft in feats]
            with open(os.path.join(GOV_DIR, 'IAT_%s_%s.geojson' % (nome, HOY)), 'w', encoding='utf-8') as f:
                json.dump({'type': 'FeatureCollection', 'features': feats}, f, ensure_ascii=False)
            log('  IAT %-36s %2d feats' % (nome, len(feats)))
        except Exception as e:   # noqa: BLE001
            reg['erro'] = str(e)[:300]
            log('  IAT %-36s NAO RESPONDEU: %s' % (nome, reg['erro'][:120]))
        SIT['servicos'][nome] = reg
    # --- SICAR nacional (consulta publica): so se registra se responde; a ficha exige captcha ------------
    for nome, url in (('sicar_consulta_publica', 'https://consultapublica.car.gov.br/publico/imoveis/index'),
                      ('sicar_www', 'https://www.car.gov.br/')):
        reg = {'url': url, 'hora': time.strftime('%H:%M:%S'), 'ok': False}
        try:
            from hp_gov_descarga import sesion_legacy
            r = sesion_legacy().get(url, timeout=40)
            reg['http'] = r.status_code; reg['ok'] = r.status_code == 200; reg['bytes'] = len(r.content)
            reg['nota'] = 'responde; a ficha do imovel (demonstrativo) exige captcha: nao automatizavel; usar a replica do IAT'
        except Exception as e:   # noqa: BLE001
            reg['erro'] = str(e)[:200]
        SIT['servicos'][nome] = reg
        log('  %-36s %s' % (nome, 'HTTP %s' % reg.get('http') if reg.get('http') else 'NAO RESPONDEU: %s' % reg.get('erro', '')[:80]))
    SIT['hora_fim'] = time.strftime('%Y-%m-%d %H:%M:%S')
    return SIT


def cargar_car_hoje(SIT):
    """GeoDataFrame 31982 con TODAS las capas CAR de los 2 imoveis: de hoy si respondio, si no de gov_pro (con fecha)."""
    partes = []
    fuente = {}
    logp = leer_json(os.path.join(GOV_PRO, '_download_log_gov_pro.json')) if os.path.exists(os.path.join(GOV_PRO, '_download_log_gov_pro.json')) else {}
    for lid, nome in CAPAS_CAR.items():
        reg = SIT['servicos'].get('IAT_CAR_%s' % nome, {})
        ruta_hoy = os.path.join(GOV_DIR, 'IAT_CAR_%s_%s.geojson' % (nome, HOY))
        if reg.get('ok') and os.path.exists(ruta_hoy):
            if reg.get('n', 0) == 0:
                fuente[nome] = 'IAT hoje %s (0 registros)' % HOY
                continue
            g = gpd.read_file(ruta_hoy); fuente[nome] = 'IAT hoje %s' % HOY
        else:
            ruta = os.path.join(GOV_PRO, 'IAT_CAR_%s.geojson' % nome)
            if not os.path.exists(ruta) or os.path.getsize(ruta) < 60:
                fuente[nome] = 'sem dado'; continue
            g = gpd.read_file(ruta)
            g = g[g.cod_imovel.astype(str).isin(CARS.values())]
            fuente[nome] = 'cache gov_pro (consulta %s)' % logp.get('IAT_CAR_%s' % nome, {}).get('fecha', '?')
        if len(g) == 0:
            continue
        g = g.to_crs(CRS_METRICO)
        g['capa'] = nome
        partes.append(g[['capa', 'cod_tema', 'nom_tema', 'cod_imovel', 'ind_status', 'des_condic', 'geometry'] + [c for c in ('num_area', 'mod_fiscal', 'ind_tipo', 'municipio') if c in g.columns]])
    car = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=CRS_METRICO)
    car['geometry'] = car.geometry.buffer(0)
    car['area_geom_ha'] = (car.geometry.area / 1e4).round(3)
    return car, fuente


SIT = consultar_gov_hoje()
CAR, FUENTE_CAR = cargar_car_hoje(SIT)
guardar_gdf(CAR, os.path.join(GOV_DIR, 'CAR_dois_imoveis_%s.geojson' % HOY))
SIT['car']['fonte_por_capa'] = FUENTE_CAR
SIT['car']['registros'] = [{k: (v if not isinstance(v, float) or np.isfinite(v) else None) for k, v in r.items() if k != 'geometry'} for r in CAR.to_dict('records')]
# outorga actual
o = SIT['servicos'].get('outorga_sigarh_26039_2023', {})
if o.get('ok') and o.get('n'):
    a = o['campos_crus'][0]
    def _d(ms):
        return time.strftime('%Y-%m-%d', time.gmtime(ms / 1000.0)) if ms else None
    SIT['outorga'] = {'fonte': 'IAT outorgas_sigarh HOJE %s' % HOY, 'nr_portaria': a.get('nr_portaria'), 'status': a.get('st_portaria'), 'tipo_documento': a.get('nm_tipo_documento'),
                      'tipo_solicitacao': a.get('nm_tipo_solicitacao'), 'titular': a.get('nm_requerente'), 'empreendimento': a.get('nm_empreendimento'), 'interferencia': a.get('nm_tipo_interferencia'),
                      'corpo_hidrico': (a.get('nm_tipo_corpo_hidrico') or '') + ' ' + (a.get('nm_corpo_hidrico_complemento') or ''), 'finalidades': a.get('desc_finalidades'),
                      'bacia': a.get('nm_bacia_hidrografica'), 'otto': a.get('cod_otto'), 'publicacao': _d(a.get('dt_publicacao')), 'vencimento': _d(a.get('dt_vencimento')),
                      'vencida_em_%s' % HOY: bool(a.get('dt_vencimento') and _d(a.get('dt_vencimento')) < HOY), 'protocolo': a.get('nr_e_protocolo'),
                      'coordenadas_wgs84': [a.get('coord_longitude'), a.get('coord_latitude')], 'campos_crus': a}
else:
    og = cargar_oficial('outorgas'); og = og[og.nr_portaria.astype(str).str.contains('26039')]
    a = og.iloc[0].to_dict() if len(og) else {}
    SIT['outorga'] = {'fonte': 'cache gov_pro (consulta 2026-09-06 18:31; servico IAT nao respondeu hoje)', 'nr_portaria': a.get('nr_portaria'), 'status': a.get('st_portaria'),
                      'titular': a.get('nm_requerente'), 'finalidades': a.get('desc_finalidades'), 'vencimento': '2025-11-08', 'vencida_em_%s' % HOY: True}
log('  OUTORGA %s: status %s, validade %s (%s), titular %s' % (SIT['outorga'].get('nr_portaria'), SIT['outorga'].get('status'), SIT['outorga'].get('vencimento'),
                                                              'VENCIDA' if SIT['outorga'].get('vencida_em_%s' % HOY) else 'vigente', SIT['outorga'].get('titular')))
if SIT['outorga'].get('coordenadas_wgs84') and all(SIT['outorga']['coordenadas_wgs84']):
    from pyproj import Transformer
    t_ = Transformer.from_crs('EPSG:4326', CRS_METRICO, always_xy=True)
    P_OUT = Point(*t_.transform(*SIT['outorga']['coordenadas_wgs84']))
    SIT['outorga']['dentro_de'] = {k: bool(imoveis()[k].contains(P_OUT)) for k in ORDEM_IMOVEIS}
    SIT['outorga']['dist_imovel_m'] = {k: round(float(imoveis()[k].distance(P_OUT)), 1) for k in ORDEM_IMOVEIS}
guardar_json(os.path.join(SALIDA_RAIZ, 'situacao_car_outorga_%s.json' % HOY), SIT)

# =====================================================================================================
# 1. ejes oficiales (referencia) y nascente
# =====================================================================================================
hid = cargar_oficial('hidro'); hid = hid[hid.fonte.astype(str) == 'FBDS']
FBDS_LINES = list(hid.geometry)
NASC = cargar_oficial('nascentes'); P_NASC = NASC[NASC.id_fonte.astype(str) == '306158'].geometry.iloc[0]
log('  eixos FBDS/IAT (referencia oficial do eixo): %d linhas; nascente FBDS 306158 em (%.0f, %.0f)' % (len(FBDS_LINES), P_NASC.x, P_NASC.y))


def app_de(faixa, nasc_r):
    cursos = unary_union([l.buffer(faixa, join_style=1) for l in FBDS_LINES]).buffer(0)
    return cursos, P_NASC.buffer(nasc_r)


def I(a, b):
    """interseccion segura (GEOS revienta con overlays sobre vacios)."""
    a = poly_only(a); b = poly_only(b)
    if a.is_empty or b.is_empty:
        return Polygon()
    return poly_only(a.intersection(b))


def D(a, b):
    a = poly_only(a); b = poly_only(b)
    if a.is_empty:
        return Polygon()
    if b.is_empty:
        return a
    return poly_only(a.difference(b))


def compor(A, NAT, NAT_ALL, AGUA, HERB, SOLO, CONSTR, SEM, rotulo):
    """Particion de un poligono de APP A en: nativa / agua / sem cobertura / a recompor (por subclase)."""
    A = poly_only(A)
    conf = I(A, NAT)
    ag = D(I(A, AGUA), NAT)
    sem = D(D(I(A, SEM), NAT), AGUA)
    rec = D(D(D(A, NAT), AGUA), SEM)
    isol = I(rec, NAT_ALL)
    sub = {'pasto_herbacea': ha(D(I(rec, HERB), isol)), 'construcoes': ha(D(I(rec, CONSTR), isol)),
           'arvores_isoladas_lt_0_05ha': ha(isol)}
    sub['lavoura_solo'] = round(ha(rec) - sum(sub.values()), 3)
    d = {'exigida_ha': ha(A), 'com_vegetacao_nativa_ha': ha(conf), 'agua_ha': ha(ag), 'sem_cobertura_drone_nao_avaliado_ha': ha(sem), 'a_recompor_ha': ha(rec),
         'a_recompor_por_subclasse_ha': sub, 'pct_com_vegetacao_da_avaliada': (round(100.0 * ha(conf) / (ha(A) - ha(sem)), 1) if (ha(A) - ha(sem)) > 0 else None),
         'envolvente_borda_0_25m_ha': [round(ha(A) - A.length * 0.25 / 1e4, 3), round(ha(A) + A.length * 0.25 / 1e4, 3)],
         '_g': {'app': A, 'conforme': conf, 'agua': ag, 'sem': sem, 'recompor': rec, 'isol': isol}}
    fecha = d['com_vegetacao_nativa_ha'] + d['agua_ha'] + d['sem_cobertura_drone_nao_avaliado_ha'] + d['a_recompor_ha']
    assert abs(fecha - d['exigida_ha']) < 0.02, (rotulo, fecha, d['exigida_ha'])
    log('  APP %-34s exigida %.3f | nativa %.3f | agua %.3f | sem cobertura %.3f | recompor %.3f %s' % (rotulo, d['exigida_ha'], d['com_vegetacao_nativa_ha'], d['agua_ha'], d['sem_cobertura_drone_nao_avaliado_ha'], d['a_recompor_ha'], sub))
    return d


def sin_g(d):
    return {k: v for k, v in d.items() if k != '_g'}


TODOS = {'_meta': {'versao': 5, 'gerado': HOY, 'crs': CRS_METRICO, 'fecha_voo': FECHA_VUELO, 'regras_cliente': [
    'dois imoveis separados (poligonos do GeoJSON); nada se soma entre eles',
    'so imagem de drone (ortofoto + DSM/DTM 22-mai-2026) para medir; sem Sentinel-2 nem produtos de satelite',
    'eixo dos arroios e nascente = dados oficiais FBDS/IAT (referencia do eixo; sob dossel o drone nao ve a calha)',
    'sem cobertura do drone = NAO AVALIADO', 'cruzamento com CAR (replica IAT do SICAR) e outorga SIGARH consultados em %s' % HOY],
    'consulta_governo': os.path.join(SALIDA_RAIZ, 'situacao_car_outorga_%s.json' % HOY)}}

for imovel in ORDEM_IMOVEIS:
    log('\n' + '#' * 78)
    log('# %s  (%s, %.3f ha)' % (imovel, IMOVEIS[imovel]['nome'], area_ha(imovel)))
    log('#' * 78)
    IM = imoveis()[imovel]
    A_IM = area_ha(imovel)
    A_INF = AREA_INFORMADA_CLIENTE[imovel]
    n_mf = round(A_IM / MF_HA, 2)
    J01 = leer_json(R(imovel, 'dron_01_recorte.json')); J02 = leer_json(R(imovel, 'dron_02_agua.json')); J03 = leer_json(R(imovel, 'dron_03_vegetacao.json'))
    # --- capas medidas por el dron (dron_01..03) ----------------------------------------------------------
    SEM = no_vazio(shape(J01['huellas']['sem_ortofoto']).buffer(0) if J01['huellas']['sem_ortofoto'] else Polygon())
    uso = gpd.read_file(R(imovel, 'uso_solo_%s.geojson' % imovel))
    def clase(nm):
        g = uso[uso.classe == nm]
        return no_vazio(unary_union(list(g.geometry)).buffer(0) if len(g) else Polygon())
    HERB, SOLO, CONSTR, AGUA_C = clase('herbacea_pasto'), clase('solo_lavoura'), clase('construcoes'), clase('agua')
    rv = R(imovel, 'vegetacao_nativa_%s.geojson' % imovel)
    veg = gpd.read_file(rv) if os.path.exists(rv) else gpd.GeoDataFrame(geometry=[], crs=CRS_METRICO)
    NAT_ALL = no_vazio(unary_union(list(veg.geometry)).buffer(0) if len(veg) else Polygon())
    NAT = no_vazio(unary_union(list(veg[veg.area_ha >= MMU_RL_HA].geometry)).buffer(0) if len(veg) else Polygon())
    ra = R(imovel, 'agua_%s_%s.geojson' % (imovel, FECHA_VUELO))
    agua = gpd.read_file(ra) if os.path.exists(ra) else gpd.GeoDataFrame(geometry=[], crs=CRS_METRICO)
    AGUA = no_vazio(unary_union(list(agua[agua.tipo == 'agua_aberta'].geometry)).buffer(0) if len(agua) else Polygon())
    REPRESA = agua[agua.corpo == 'represa_principal'].geometry.iloc[0] if len(agua) and (agua.corpo == 'represa_principal').any() else None
    log('  medido no drone: nativa (MMU %.2f ha) %.3f ha [todas manchas %.3f]; agua %.3f; pasto %.3f; lavoura/solo %.3f; construcoes %.3f; sem cobertura %.3f'
        % (MMU_RL_HA, ha(NAT.intersection(IM)), ha(NAT_ALL.intersection(IM)), ha(AGUA.intersection(IM)), ha(HERB.intersection(IM)), ha(SOLO.intersection(IM)), ha(CONSTR.intersection(IM)), ha(SEM.intersection(IM))))

    RES = {'imovel': imovel, 'nome': IMOVEIS[imovel]['rotulo'], 'area_poligono_ha': A_IM, 'area_informada_cliente_ha': A_INF,
           'alqueires_paulistas_poligono': round(A_IM / ALQUEIRE_PAULISTA_HA, 2), 'modulos_fiscais': n_mf, 'mf_ha': MF_HA,
           'car': CARS[imovel], 'car_relacao': IMOVEIS[imovel]['car_relacao'],
           'cobertura_drone': J01['cobertura'], 'agua': J02['resumo'], 'vegetacao_ha': J03['tabela_ha'],
           'vegetacao_nativa_poligonos': J03['vegetacao_nativa_poligonos'], 'silvicultura_indicio': J03['silvicultura']['com_indicio'], 'app': {}, 'reserva_legal': {}}
    if abs(A_IM - A_INF) > 0.05:
        RES['aviso_area'] = ('o poligono do GeoJSON (editado pelo cliente em %s 23:10) mede %.3f ha; o pedido informa %.2f ha. MANDA O POLIGONO. '
                             'A diferenca (%.3f ha) e a ponta norte removida, reportada a parte como "a conferir na escritura".' % (HOY, A_IM, A_INF, A_INF - A_IM))
        log('  AVISO: %s' % RES['aviso_area'])

    # --- APP: variantes -------------------------------------------------------------------------------
    cur30, nas50 = app_de(APP_M, NASC_M)
    variantes = {'legal_30m_nascente_50m': (unary_union([cur30, nas50]).buffer(0), 'art. 4 I a) e IV: 30 m do eixo FBDS (curso <= 10 m) + raio 50 m da nascente')}
    if imovel == 'santo_antonio':
        c20, n15 = app_de(PRA_M, PRA_NASC_M)
        variantes['pra_20m_nascente_15m'] = (unary_union([c20, n15]).buffer(0), 'art. 61-A par. 4 + Lei PR 18.295 art. 17 par. 2 (imovel 4-10 MF: 7,2 MF): 20 m + nascente 15 m, so em area consolidada ate 22-jul-2008')
        if REPRESA is not None:
            FR = REPRESA.buffer(FAIXA_RESERV_M).buffer(0)
            variantes['legal_mais_faixa_reservatorio_30m'] = (unary_union([cur30, nas50, FR]).buffer(0), 'cenario art. 4 III: faixa do reservatorio "a definir pelo IAT" (sem dispensa: espelho %.3f ha >= 1 ha) = espelho + 30 m' % ha(REPRESA))
    else:
        c20, n15 = app_de(PRA_M, PRA_NASC_M)
        variantes['pra_se_parte_do_imovel_de_origem_gt4mf_20m'] = (unary_union([c20, n15]).buffer(0), 'se tratado como parte do imovel de origem (> 4 MF): art. 61-A par. 4 / Lei PR 18.295 art. 17 par. 2 = 20 m + nascente 15 m')
        c5, n15b = app_de(5, PRA_NASC_M)
        variantes['pra_se_imovel_proprio_le1mf_5m'] = (unary_union([c5, n15b]).buffer(0), 'se imovel proprio <= 1 MF (%.2f MF): art. 61-A par. 1 = 5 m + nascente 15 m (par. 5); art. 61-B I: recomposicao de APP limitada a 10 %% da area = %.3f ha' % (n_mf, 0.10 * A_IM))
    for nome, (G, base) in variantes.items():
        d = compor(I(G, IM), NAT, NAT_ALL, AGUA, HERB, SOLO, CONSTR, SEM, '%s/%s' % (imovel, nome))
        d['base_legal'] = base
        if nome.startswith('legal'):
            d['curso_ha'] = ha(I(D(cur30, nas50), IM)); d['nascente_ha'] = ha(I(nas50, IM))
            if 'reservatorio' in nome:
                d['faixa_reservatorio_adicional_ha'] = ha(I(D(FR, unary_union([cur30, nas50])), IM))
        RES['app'][nome] = d
    RES['app']['eixo_nota'] = ('eixo dos cursos = FBDS/IAT 1:25.000 (dado oficial); o drone nao substitui o eixo sob dossel (ortho_03: < 50 %% das secoes com DTM de solo). '
                               'Trechos FBDS que tocam o imovel: %s' % sorted(set(str(r.id_fonte) for _, r in hid.iterrows() if r.geometry.buffer(APP_M).intersects(IM))))

    # --- RL ----------------------------------------------------------------------------------------------
    A_APP = RES['app']['legal_30m_nascente_50m']['_g']['app']
    rl_ex = round(RL_PCT * A_IM, 3)
    fora = D(I(NAT, IM), A_APP); dentro = I(I(NAT, IM), A_APP)
    comp_med = round(ha(fora) + ha(dentro), 3)
    rl = {'exigida_pct': RL_PCT, 'exigida_ha': rl_ex, 'exigida_sobre_area_informada_%.2fha' % A_INF: round(RL_PCT * A_INF, 3),
          'base_legal': 'art. 12 II (20 %%); art. 15 (APP vegetada computa); art. 12 par. 1 (area desmembrada de imovel > 4 MF mantem 20 %%)',
          'medido_drone': {'remanescente_fora_app_ha': ha(fora), 'app_vegetada_art15_ha': ha(dentro), 'vegetacao_nativa_computavel_ha': comp_med,
                           'mmu_ha': MMU_RL_HA, 'arvores_isoladas_nao_computadas_ha': ha(D(I(NAT_ALL, IM), NAT)),
                           'sem_cobertura_drone_nao_avaliado_ha': ha(SEM.intersection(IM))}}
    if imovel == 'santo_antonio':
        rl['vegetacao_computavel_ha'] = comp_med
        rl['deficit_ha'] = round(rl_ex - comp_med, 3)
        rl['pct_atendido'] = round(100.0 * comp_med / rl_ex, 1)
        rl['sensibilidade'] = {'todas_as_manchas_ge_25m2': round(ha(NAT_ALL.intersection(IM)), 3),
                               'so_fragmentos_ge_0_5ha': round(ha(no_vazio(unary_union(list(veg[veg.area_ha >= 0.5].geometry)).buffer(0)).intersection(IM)), 3) if len(veg) else 0.0,
                               'so_com_altura_medida_chm_ge_3m': J03['tabela_ha']['arborea_altura_medida'],
                               'nota': 'a faixa sem cobertura (%.3f ha) nao soma nem desconta: se toda fosse mata o deficit cairia no maximo a %.3f ha' % (ha(SEM.intersection(IM)), rl_ex - comp_med - ha(SEM.intersection(IM)))}
        rl['veredicto'] = 'NAO CONFORME: deficit %.3f ha (%.1f %% atendido)' % (rl['deficit_ha'], rl['pct_atendido'])
    else:
        PN = imoveis().get(PONTA_NORTE)
        J03pn = leer_json(R(PONTA_NORTE, 'dron_03_vegetacao.json')) if PN is not None and os.path.exists(R(PONTA_NORTE, 'dron_03_vegetacao.json')) else None
        J01pn = leer_json(R(PONTA_NORTE, 'dron_01_recorte.json')) if PN is not None and os.path.exists(R(PONTA_NORTE, 'dron_01_recorte.json')) else None
        rl['vegetacao_computavel_ha'] = 0.0
        rl['regra_terra_limpa'] = 'comprada como terra limpa, sem monte: vegetacao existente considerada 0 por regra do cliente (o drone mede %.3f ha de nativa dentro do poligono: %s)' % (
            comp_med, 'coerente com terra limpa' if comp_med < 0.05 else 'VERIFICAR: ha vegetacao dentro do poligono')
        rl['deficit_ha'] = rl_ex
        rl['deficit_sobre_area_informada_ha'] = round(RL_PCT * A_INF, 3)
        rl['quanto_falta_ha'] = {'sobre_o_poligono_%.3fha' % A_IM: rl_ex, 'sobre_os_%.2fha_informados' % A_INF: round(RL_PCT * A_INF, 3)}
        pn = {'area_ha': round(PN.area / 1e4, 3) if PN is not None else None, 'situacao': 'FORA do poligono atual dos 6 alqueires (removida pelo cliente em %s); NAO computada; a conferir na escritura' % HOY}
        if J03pn:
            t = J03pn['tabela_ha']
            pn.update({'com_ortofoto_ha': J01pn['cobertura']['ortofoto']['com_cobertura_ha'], 'sem_cobertura_drone_ha': J01pn['cobertura']['ortofoto']['sem_cobertura_ha'],
                       'mata_medida_ha': t['vegetacao_nativa_arborea_arbustiva_ha'], 'arborea_ha': t['arborea_ha'], 'arbustiva_ha': t['arbustiva_ha'],
                       'altura_chm': {k: v for k, v in (J03pn['vegetacao_nativa_poligonos']['fragmentos_ge_0_5ha'][0] if J03pn['vegetacao_nativa_poligonos']['fragmentos_ge_0_5ha'] else {}).items() if k.startswith('altura') or k == 'pct_altura_medida'},
                       'se_fosse_do_imovel': {'area_imovel_ha': round(A_IM + PN.area / 1e4, 3), 'rl_exigida_ha': round(RL_PCT * (A_IM + PN.area / 1e4), 3),
                                              'computavel_medida_ha': t['vegetacao_nativa_arborea_arbustiva_ha'],
                                              'deficit_ha_se_a_faixa_sem_cobertura_nao_for_mata': round(RL_PCT * (A_IM + PN.area / 1e4) - t['vegetacao_nativa_arborea_arbustiva_ha'], 3),
                                              'deficit_ha_se_a_faixa_sem_cobertura_for_toda_mata': round(RL_PCT * (A_IM + PN.area / 1e4) - t['vegetacao_nativa_arborea_arbustiva_ha'] - J01pn['cobertura']['ortofoto']['sem_cobertura_ha'], 3)}})
        if PN is not None:
            app_pn = I(unary_union([cur30, nas50]), PN)
            pn['app_legal_30m_dentro_da_ponta_ha'] = ha(app_pn)
            pn['app_trechos_fbds'] = sorted(set(str(r.id_fonte) for _, r in hid.iterrows() if r.geometry.buffer(APP_M).intersects(PN)))
            pn['app_nota'] = 'o Arroio 1 (FBDS 647524) passa pela ponta norte: se a ponta for do imovel, entra essa APP; no poligono atual nenhuma APP toca os 6 alqueires'
        rl['ponta_norte_a_conferir'] = pn
        rl['veredicto'] = 'FALTA TODA A RL: %.3f ha (20 %% de %.3f ha do poligono; %.3f ha sobre os %.2f ha informados); vegetacao computavel 0 (terra limpa)' % (rl_ex, A_IM, RL_PCT * A_INF, A_INF)
    # recomposicao / compensacao (art. 66; Lei PR 18.295: 20 anos, 1/10 a cada 2 anos)
    defi = rl['deficit_ha']
    rl['regularizacao_art66'] = {
        'deficit_ha': defi,
        'opcoes': ['recompor (art. 66 I): plantio de nativas, ate 20 anos, minimo 1/10 da area a cada 2 anos (art. 66 par. 2; Lei PR 18.295)',
                   'regeneracao natural (art. 66 II): condicionada a laudo de viabilidade',
                   'compensar (art. 66 III / par. 5): CRA, arrendamento (servidao ambiental), doacao de area em UC pendente de regularizacao fundiaria, ou cadastro de outra area equivalente em extensao (mesmo bioma, IN IAT 53/2025: preferencialmente mesma formacao fitogeografica)'],
        'cronograma_recomposicao_1_10_a_cada_2_anos': [{'etapa': i + 1, 'ate_ano': 2 * (i + 1), 'ha_acumulado_minimo': round(defi * (i + 1) / 10.0, 3)} for i in range(10)],
        'observacao': ('a recomposicao pode usar ate 50 % de exoticas em sistema intercalado (art. 66 par. 3) e a APP recomposta computa (art. 15)' if imovel == 'santo_antonio' else
                       'o desmembramento de imovel > 4 MF nao reduz o percentual (art. 12 par. 1): os 20 % valem integralmente; sem vegetacao no poligono, toda a RL sera recomposicao ou compensacao')}
    RES['reserva_legal'] = rl
    log('  RL %s: exigida %.3f | computavel %.3f | deficit %.3f -> %s' % (imovel, rl_ex, rl['vegetacao_computavel_ha'], rl['deficit_ha'], rl['veredicto']))

    # --- mapa CAR v5 (particion que cierra) ----------------------------------------------------------------
    with Cronometro('mapa CAR v5'):
        filas = []
        def add(geom, classe, sub, sit, nota=''):
            geom = poly_only(geom)
            if geom.is_empty or geom.area < 1:
                return
            filas.append({'imovel': imovel, 'classe_car': classe, 'subclasse': sub, 'situacao': sit, 'area_ha': ha(geom), 'nota': nota, 'geometry': geom})
        nasc_c = I(nas50, IM); curso = I(D(cur30, nas50), IM)
        for nome, A, cl in (('nascente', nasc_c, "APP - Nascente ou olho d'agua perene"), ('curso', curso, "APP - Curso d'agua natural de ate 10 metros")):
            add(I(A, NAT), cl, 'conforme', 'vegetacao nativa (drone 0,25 m)')
            add(D(I(A, AGUA), NAT), cl, 'agua', 'agua (drone 22-mai-2026)')
            add(D(D(I(A, SEM), NAT), AGUA), cl, 'sem cobertura do drone', 'NAO AVALIADO')
            rec = D(D(D(A, NAT), AGUA), SEM)
            isol = I(rec, NAT_ALL)
            add(isol, cl, 'a recompor', 'arvores isoladas (< 0,05 ha)')
            add(D(I(rec, HERB), isol), cl, 'a recompor', 'pasto/herbacea')
            add(D(D(I(rec, CONSTR), isol), HERB), cl, 'a recompor', 'construcoes')
            add(D(D(D(rec, isol), HERB), CONSTR), cl, 'a recompor', 'lavoura/solo')
        A_all = I(unary_union([cur30, nas50]), IM)
        resto = D(IM, A_all)
        if REPRESA is not None:
            add(I(resto, REPRESA), 'Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua', 'agua 22-mai-2026 (%.3f ha; faixa a definir pelo IAT)' % ha(REPRESA))
            add(D(I(resto, AGUA), REPRESA), 'Reservatorio artificial / lagoa', 'espelho d agua', 'lamina fora da APP (drone)')
        else:
            add(I(resto, AGUA), 'Reservatorio artificial / lagoa', 'espelho d agua', 'lamina fora da APP (drone)')
        add(D(I(resto, SEM), AGUA), 'Sem cobertura do drone', 'nao avaliado', 'fora da cobertura do voo')
        rem = D(D(I(resto, NAT), AGUA), SEM)
        add(rem, 'Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP', 'conservada (estagio requer campo)' + ('' if imovel == 'santo_antonio' else '; terra limpa: NAO computada por regra do cliente'))
        cons = D(D(D(resto, NAT), AGUA), SEM)
        isol = I(cons, NAT_ALL)
        add(I(cons, CONSTR), 'Area Consolidada', 'construcoes', 'sede/benfeitorias')
        add(D(isol, CONSTR), 'Area Consolidada', 'arvores isoladas (< 0,05 ha)', 'nao computadas como remanescente')
        add(D(D(I(cons, HERB), CONSTR), isol), 'Area Consolidada', 'pasto/herbacea', 'uso antropico fora da APP')
        add(D(D(D(cons, CONSTR), isol), HERB), 'Area Consolidada', 'uso agricola', 'lavoura/solo fora da APP')
        car5 = gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geometry'} for f in filas], geometry=[f['geometry'] for f in filas], crs=CRS_METRICO)
        car5['fecha'] = FECHA_VUELO
        guardar_gdf(car5, R(imovel, 'mapa_uso_car_v5_%s.geojson' % imovel))
        soma = round(float(car5.area_ha.sum()), 3)
        uni = unary_union(list(car5.geometry)); solape = round(float(car5.geometry.area.sum() - uni.area) / 1e4, 4)
        RES['mapa_car_v5'] = {'soma_ha': soma, 'area_imovel_ha': A_IM, 'diferenca_ha': round(soma - A_IM, 3), 'solape_ha': solape, 'fecha': bool(abs(soma - A_IM) < 0.02 and solape < 0.01),
                              'linhas': [{k: v for k, v in f.items() if k != 'geometry'} for f in filas]}
        log('  CAR v5 %s: soma %.3f vs imovel %.3f (dif %.3f, solape %.4f) -> %s' % (imovel, soma, A_IM, soma - A_IM, solape, 'FECHA' if RES['mapa_car_v5']['fecha'] else 'NAO FECHA'))
        if not RES['mapa_car_v5']['fecha']:
            raise RuntimeError('o mapa CAR v5 de %s nao fecha' % imovel)

    # --- cruce CAR: declarado vs medido ---------------------------------------------------------------------
    with Cronometro('cruzamento CAR declarado vs medido'):
        cc = CAR[CAR.cod_imovel == CARS[imovel]]
        def decl(capa, tema=None):
            g = cc[cc.capa == capa]
            if tema:
                g = g[g.cod_tema.astype(str).str.contains(tema)]
            if not len(g):
                return None, None, Polygon()
            G = unary_union(list(g.geometry)).buffer(0)
            na = float(g.num_area.sum()) if 'num_area' in g.columns and g.num_area.notna().any() else None
            return (round(na, 3) if na is not None else None), ha(G), no_vazio(G)
        im_decl = cc[cc.capa == 'area_imovel']
        ai_na, ai_ha, AI = decl('area_imovel')
        app_na, app_ha, APPd = decl('app_total')
        rl_na, rl_ha, RLd = decl('reserva_legal')
        vn_na, vn_ha, VNd = decl('vegetacao_nativa')
        co_na, co_ha, COd = decl('area_consolidada')
        rs_na, rs_ha, RSd = decl('hidrografia', 'RESERVATORIO')
        ri_na, ri_ha, RId = decl('hidrografia', 'RIO')
        sv_na, sv_ha, SVd = decl('servidao_administrativa')
        rl_tipo = sorted(set(cc[cc.capa == 'reserva_legal'].cod_tema.astype(str))) if (cc.capa == 'reserva_legal').any() else []
        status = {'ind_status': im_decl.ind_status.iloc[0] if len(im_decl) else None, 'des_condic': im_decl.des_condic.iloc[0] if len(im_decl) else None,
                  'ind_tipo': im_decl.ind_tipo.iloc[0] if len(im_decl) and 'ind_tipo' in im_decl.columns else None,
                  'mod_fiscal_declarado': float(im_decl.mod_fiscal.iloc[0]) if len(im_decl) and 'mod_fiscal' in im_decl.columns else None,
                  'municipio_car': im_decl.municipio.iloc[0] if len(im_decl) and 'municipio' in im_decl.columns else None,
                  'data_inscricao': 'nao publicada na replica do IAT (campos: cod_imovel, ind_status, des_condic, num_area, mod_fiscal); copyright do servico: %s' % SIT['servicos'].get('IAT_CAR_area_imovel', {}).get('copyright_servico'),
                  'fonte': FUENTE_CAR}
        Af = RES['app']['legal_30m_nascente_50m']
        med_app_veg = Af['com_vegetacao_nativa_ha']
        cruce = {'car': CARS[imovel], 'relacao': IMOVEIS[imovel]['car_relacao'], 'status_atual': status,
                 'declarado_no_car_inteiro': {'area_imovel_ha': ai_na, 'area_imovel_geom_ha': ai_ha, 'app_total_ha': app_na, 'app_total_geom_ha': app_ha,
                                              'reserva_legal_ha': rl_na, 'reserva_legal_geom_ha': rl_ha, 'reserva_legal_tipo': rl_tipo,
                                              'vegetacao_nativa_ha': vn_na, 'vegetacao_nativa_geom_ha': vn_ha, 'area_consolidada_ha': co_na, 'area_consolidada_geom_ha': co_ha,
                                              'reservatorios_geom_ha': rs_ha, 'rios_ate_10m_geom_ha': ri_ha, 'servidao_administrativa_ha': sv_na},
                 'declarado_DENTRO_do_poligono_deste_imovel_ha': {'area_imovel_car': ha(I(AI, IM)), 'app_total': ha(I(APPd, IM)), 'reserva_legal': ha(I(RLd, IM)),
                                                                  'vegetacao_nativa': ha(I(VNd, IM)), 'area_consolidada': ha(I(COd, IM)), 'reservatorios': ha(I(RSd, IM)),
                                                                  'rios_ate_10m': ha(I(RId, IM))},
                 'poligono_fora_do_car_ha': ha(D(IM, AI)),
                 'medido_drone_v5': {'area_poligono_ha': A_IM, 'app_exigida_30m_50m_ha': Af['exigida_ha'], 'app_com_vegetacao_ha': med_app_veg, 'app_agua_ha': Af['agua_ha'], 'app_a_recompor_ha': Af['a_recompor_ha'],
                                     'app_sem_cobertura_ha': Af['sem_cobertura_drone_nao_avaliado_ha'], 'rl_exigida_ha': rl_ex, 'rl_vegetacao_computavel_ha': rl['vegetacao_computavel_ha'], 'rl_deficit_ha': rl['deficit_ha'],
                                     'vegetacao_nativa_ha': J03['tabela_ha']['vegetacao_nativa_arborea_arbustiva_ha'], 'vegetacao_nativa_fora_app_ha': ha(fora),
                                     'reservatorios_agua_aberta_ha': J02['resumo']['agua_aberta_total_ha'], 'represa_ha': J02['resumo']['represa_ha'],
                                     'area_antropizada_pasto_lavoura_construcoes_ha': round(J03['tabela_ha']['pasto_ha'] + J03['tabela_ha']['lavoura_solo_ha'] + J03['tabela_ha']['construcoes'], 3)}}
        dif = {}
        dec_in = cruce['declarado_DENTRO_do_poligono_deste_imovel_ha']; med = cruce['medido_drone_v5']
        dif['app: declarada dentro do poligono vs exigida medida'] = [dec_in['app_total'], med['app_exigida_30m_50m_ha'], round(med['app_exigida_30m_50m_ha'] - dec_in['app_total'], 3)]
        dif['reserva legal: declarada dentro do poligono vs exigida (20 %)'] = [dec_in['reserva_legal'], rl_ex, round(rl_ex - dec_in['reserva_legal'], 3)]
        dif['vegetacao nativa: declarada dentro do poligono vs medida no drone'] = [dec_in['vegetacao_nativa'], med['vegetacao_nativa_ha'], round(med['vegetacao_nativa_ha'] - dec_in['vegetacao_nativa'], 3)]
        dif['area consolidada: declarada dentro do poligono vs antropizada medida'] = [dec_in['area_consolidada'], med['area_antropizada_pasto_lavoura_construcoes_ha'], round(med['area_antropizada_pasto_lavoura_construcoes_ha'] - dec_in['area_consolidada'], 3)]
        dif['reservatorios: declarados dentro do poligono vs agua aberta medida'] = [dec_in['reservatorios'], med['reservatorios_agua_aberta_ha'], round(med['reservatorios_agua_aberta_ha'] - dec_in['reservatorios'], 3)]
        dif['area: CAR (num_area) vs poligono'] = [ai_na, A_IM, round(A_IM - (ai_na or 0), 3)]
        cruce['diferencas_[declarado, medido, medido-declarado]'] = dif
        if imovel == 'santo_antonio':
            cruce['leitura'] = ('CAR do proprio imovel, status %s / "%s": declara RL %s ha (%s) contra %.3f ha exigidas; vegetacao nativa %s ha contra %.3f ha medidas; '
                                'APP %s ha contra %.3f ha exigidas (%.3f com mata); reservatorio %s ha contra %.3f ha de espelho em 22-mai-2026. Cabe RETIFICACAO do CAR.'
                                % (status['ind_status'], status['des_condic'], rl_na, ','.join(rl_tipo), rl_ex, vn_na, med['vegetacao_nativa_ha'], app_na, med['app_exigida_30m_50m_ha'], med_app_veg, rs_ha, med['represa_ha']))
        else:
            cruce['leitura'] = ('o poligono dos 6 alqueires esta DENTRO do CAR de origem %s (%s ha, %.2f MF, status %s / "%s"); dentro do poligono esse CAR declara RL %.3f ha, APP %.3f ha, '
                                'vegetacao nativa %.3f ha e area consolidada %.3f ha; o drone mede %.3f ha de nativa e %.3f ha de APP exigida. O desmembramento exige CAR proprio (ou retificacao do de origem) com RL de %.3f ha.'
                                % (CARS[imovel], ai_na, (status['mod_fiscal_declarado'] or 0), status['ind_status'], status['des_condic'], dec_in['reserva_legal'], dec_in['app_total'], dec_in['vegetacao_nativa'], dec_in['area_consolidada'],
                                   med['vegetacao_nativa_ha'], med['app_exigida_30m_50m_ha'], rl_ex))
        RES['cruzamento_car'] = cruce
        log('  CAR %s: %s' % (CARS[imovel], cruce['leitura']))
        for k, v in dif.items():
            log('    %-70s declarado %8s | medido %8s | dif %8s' % (k, v[0], v[1], v[2]))
        # capas CAR recortadas al poligono para QGIS
        if len(cc):
            ccp = cc.copy(); ccp['geometry'] = [I(g, IM) for g in ccp.geometry]
            ccp = ccp[~ccp.geometry.is_empty]
            ccp['area_dentro_poligono_ha'] = (ccp.geometry.area / 1e4).round(3)
            guardar_gdf(ccp, R(imovel, 'car_declarado_dentro_%s_%s.geojson' % (imovel, HOY)))

    # --- outorga ---------------------------------------------------------------------------------------------
    RES['outorga_sigarh'] = dict(SIT['outorga'])
    RES['outorga_sigarh']['aplica_a_este_imovel'] = bool(SIT['outorga'].get('dentro_de', {}).get(imovel, imovel == 'santo_antonio'))
    RES['outorga_sigarh']['leitura'] = ('outorga PREVIA da barragem do Ribeirao do Salto (represa deste imovel): status %s, validade %s (%s em %s): a regularizacao hidrica do barramento esta pendente; '
                                        'a faixa de APP do reservatorio (art. 4 III) sera a da licenca/outorga definitiva' % (SIT['outorga'].get('status'), SIT['outorga'].get('vencimento'),
                                                                                                                              'VENCIDA' if SIT['outorga'].get('vencida_em_%s' % HOY) else 'vigente', HOY)) if imovel == 'santo_antonio' else \
        'a outorga 26039/2023 e da represa da Fazenda Santo Antonio (a %.0f m deste poligono): nao ha outorga/interferencia cadastrada dentro dos 6 alqueires' % SIT['outorga'].get('dist_imovel_m', {}).get(imovel, -1)

    # --- capas APP / RL vectoriales ------------------------------------------------------------------------------
    filas = []
    for nome, d in RES['app'].items():
        if not isinstance(d, dict) or '_g' not in d:
            continue
        for sit in ('conforme', 'agua', 'sem', 'recompor'):
            g = d['_g'][sit]
            if not g.is_empty:
                filas.append({'variante': nome, 'imovel': imovel, 'situacao': {'sem': 'sem cobertura do drone (nao avaliado)'}.get(sit, sit), 'area_ha': ha(g), 'geometry': g})
    if filas:
        guardar_gdf(gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geometry'} for f in filas], geometry=[f['geometry'] for f in filas], crs=CRS_METRICO), R(imovel, 'app_v5_%s.geojson' % imovel))
    if imovel == 'santo_antonio':
        rlg = [{'parte': 'remanescente fora APP', 'area_ha': ha(fora), 'geometry': fora}, {'parte': 'APP vegetada (art. 15)', 'area_ha': ha(dentro), 'geometry': dentro}]
        rlg = [r for r in rlg if not r['geometry'].is_empty]
        if rlg:
            guardar_gdf(gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geometry'} for f in rlg], geometry=[f['geometry'] for f in rlg], crs=CRS_METRICO), R(imovel, 'rl_vegetacao_computavel_v5_%s.geojson' % imovel))
    for nome in list(RES['app'].keys()):
        if isinstance(RES['app'][nome], dict):
            RES['app'][nome] = sin_g(RES['app'][nome])

    # --- KPI y avisos --------------------------------------------------------------------------------------------
    Af = RES['app']['legal_30m_nascente_50m']
    RES['kpi'] = {'area_poligono_ha': A_IM, 'cobertura_ortofoto_ha': J01['cobertura']['ortofoto']['com_cobertura_ha'], 'sem_cobertura_ha': J01['cobertura']['ortofoto']['sem_cobertura_ha'],
                  'cobertura_dsm_ha': J01['cobertura']['dsm_dtm']['com_cobertura_ha'], 'represa_ha': J02['resumo']['represa_ha'], 'represa_ge_1ha': J02['resumo']['represa_ge_1ha'],
                  'acude_ha': J02['resumo']['acude_cabeceira_ha'], 'lagoas_menores_ha': J02['resumo']['lagoas_menores_ha'],
                  'arborea_ha': J03['tabela_ha']['arborea_ha'], 'arbustiva_ha': J03['tabela_ha']['arbustiva_ha'], 'pasto_ha': J03['tabela_ha']['pasto_ha'], 'lavoura_solo_ha': J03['tabela_ha']['lavoura_solo_ha'],
                  'app_exigida_ha': Af['exigida_ha'], 'app_com_mata_ha': Af['com_vegetacao_nativa_ha'], 'app_agua_ha': Af['agua_ha'], 'app_a_recompor_ha': Af['a_recompor_ha'], 'app_sem_cobertura_ha': Af['sem_cobertura_drone_nao_avaliado_ha'],
                  'rl_exigida_ha': rl_ex, 'rl_computavel_ha': rl['vegetacao_computavel_ha'], 'rl_deficit_ha': rl['deficit_ha']}
    for k, v in RES['app'].items():
        if isinstance(v, dict) and k.startswith('pra'):
            RES['kpi']['app_a_recompor_%s_ha' % k] = v['a_recompor_ha']; RES['kpi']['app_exigida_%s_ha' % k] = v['exigida_ha']
    RES['avisos'] = [
        'Sem satelite: nenhuma camada de Sentinel-2/FABDEM/RF 10 m entra nos calculos; a faixa sem cobertura do drone (%.3f ha) fica NAO AVALIADA.' % J01['cobertura']['ortofoto']['sem_cobertura_ha'],
        'Eixo dos arroios e nascente: FBDS/IAT 1:25.000 (oficial). O drone nao ve a calha sob dossel: a borda da calha (art. 4 I) exige levantamento em campo (GNSS) ou LiDAR.',
        'DSM/DTM no datum do voo (sem GCP/RTK): cotas relativas; CHM subestima sob dossel fechado (classe "arborea dossel fechado" = copa reconhecida, altura nao medida).',
        'Vegetacao "arborea (so cor)" = faixa sul sem DSM (N < 7401711): altura desconhecida; MMU 25 m2; nativa para RL com MMU 0,05 ha.',
        'Represa: espelho de 22-mai-2026 (fim do outono); o espelho legal e o do nivel maximo normal/vertedouro, a medir em campo. Outorga previa %s: status %s, vencida em %s.' % (SIT['outorga'].get('nr_portaria'), SIT['outorga'].get('status'), SIT['outorga'].get('vencimento')),
        'Estagio sucessional (CONAMA 2/1994) e inventario da RL exigem campo.',
    ]
    if imovel == 'seis_alqueires':
        RES['avisos'].insert(0, RES.get('aviso_area', ''))
    guardar_json(R(imovel, 'resultados_v5.json'), RES)
    TODOS[imovel] = RES

TODOS['_meta']['servicos_governo_hoje'] = {k: {'ok': v.get('ok'), 'n': v.get('n'), 'http': v.get('http'), 'hora': v.get('hora'), 'erro': v.get('erro')} for k, v in SIT['servicos'].items()}
TODOS['_meta']['replica_sicar_iat_data_dos_dados'] = SIT['servicos'].get('IAT_CAR_area_imovel', {}).get('copyright_servico')
TODOS['_meta']['nota_soma'] = 'os dois imoveis NAO se somam: cada bloco e independente'
guardar_json(os.path.join(SALIDA_RAIZ, 'resultados_v5.json'), TODOS)
log('dron_04 listo.')
