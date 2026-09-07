# -*- coding: utf-8 -*-
"""ortho_06: recomputo legal v4 con la precision de la ortofoto (APP, RL, mapa CAR) por gleba
e imovel unico, con tabla ANTES (v3, S2 10 m + FBDS + DEM 30 m) -> DESPUES (ortofoto 0,25/0,5 m).

APP de cursos: 30 m desde (a) el eje FBDS [referencia, como v3], (b) el eje DTM del dron
[INDICATIVO: bajo dosel es la linea mas baja de la envolvente del dosel], (c) la borda da
calha [NO DISPONIBLE: ortho_03 no pudo construir bordas - < 50 % de secciones con DTM de
suelo; bajo dosel el DTM fotogrametrico es la copa]. Nascente: raio 50 m (306158 confirmada
como cabecera umida). Reservatorio: espelho 22-mai-2026 (1,388 ha >= 1 ha: NAO cabe a
dispensa do art. 4 par. 4) -> cenario faixa 30 m.
Vegetacao: clases de ortho_05 (arborea + arbustiva = vegetacao nativa; MMU 0,05 ha para RL).
Faixa sem cobertura do voo (norte): classes do mapa v3 (RF S2 10 m).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, shape, Polygon, MultiPolygon
from shapely.ops import unary_union

log('=' * 78)
log('ortho_06_legal_v4  ortofoto %s' % FECHA_VUELO)
log('=' * 78)
GL = glebas()
G1, G2, IM = GL['G1'], GL['G2'], GL['IMOVEL']
LEG = leer_json(PARAMETROS_LEGALES)
V3 = leer_json(PREV['resultados_v3'])
K3 = V3['kpi']
COB = cobertura()
H_ORTO = shape(COB['ortofoto']); H_DTM = shape(COB['dtm_dsm'])
SEM_ORTO = poly_only(IM.difference(H_ORTO))
J02 = leer_json(R('ortho_02_agua.json')); J03 = leer_json(R('ortho_03_canais.json')); J04 = leer_json(R('ortho_04_nascentes.json')); J05 = leer_json(R('ortho_05_vegetacao.json'))
APP_M = LEG['app_curso_dagua_m']['lt10']; NASC_M = LEG['app_nascente_m']
PRA_M = LEG['recomposicao_61A']['curso_dagua_ate_10m_m']; PRA_NASC_M = LEG['recomposicao_61A']['nascente_raio_m']
RL_PCT = LEG['rl_pct']
AREA_IM = round(IM.area / 1e4, 3); AREA_G1 = round(G1.area / 1e4, 3); AREA_G2 = round(G2.area / 1e4, 3)
RL_EX = round(RL_PCT * AREA_IM, 3)
log('  imovel %.3f ha (G1 %.3f + G2 %.3f); RL exigida %.3f; sem ortofoto %.3f ha' % (AREA_IM, AREA_G1, AREA_G2, RL_EX, ha(SEM_ORTO)))

# --- vegetacao / agua / usos desde la ortofoto (vector) ------------------------------------
veg = gpd.read_file(R('vegetacao_nativa_ortofoto.geojson'))
NAT_ALL = unary_union(list(veg.geometry)).buffer(0)
NAT = unary_union(list(veg[veg.area_ha >= 0.05].geometry)).buffer(0)          # MMU 0,05 ha (RL / remanescente)
NAT_05 = unary_union(list(veg[veg.area_ha >= 0.5].geometry)).buffer(0)        # fragmentos >= 0,5 ha (sensibilidade)
ARV_ISOL = poly_only(NAT_ALL.difference(NAT))
agua = gpd.read_file(R('agua_ortofoto_2026-05-22.geojson'))
agua_conf = agua[(agua.tipo == 'agua_aberta') | ((agua.tipo == 'candidato') & (agua.dsm_disponivel == True) & (agua.area_ha >= 0.03))]
AGUA = unary_union(list(agua_conf.geometry)).buffer(0)
REPRESA = agua[agua.corpo == 'represa_principal'].geometry.iloc[0]
POND = agua[agua.corpo == 'reservatorio_cabeceira_arroio2'].geometry.iloc[0] if (agua.corpo == 'reservatorio_cabeceira_arroio2').any() else Polygon()
cls, tr50 = leer(R('vegetacao_ortofoto.tif', 0.5), nan=False); cls = cls[0]
HERB = unary_union(list(vectorizar(cls == 4, 0.5, min_area_m2=25).geometry)).buffer(0)
CONSTR = unary_union(list(vectorizar(cls == 7, 0.5, min_area_m2=20).geometry)).buffer(0)
SILV = unary_union(list(vectorizar(cls == 8, 0.5, min_area_m2=25).geometry)).buffer(0) if (cls == 8).any() else Polygon()
def no_vazio(g):
    """GEOS (shapely 2.1) revienta al intersectar un multipoligono complejo con una geometria VACIA
    (AssertionFailedException: overlay result dimension). Un marcador de 0,0003 m2 fuera del imovel
    hace que toda interseccion sea vacia y toda diferencia identica, sin excepciones."""
    return g if (g is not None and not g.is_empty) else Point(0, 0).buffer(0.01)
HERB, CONSTR, SILV, ARV_ISOL = no_vazio(HERB), no_vazio(CONSTR), no_vazio(SILV), no_vazio(ARV_ISOL)
# faixa sem ortofoto: classes v3
car3 = cargar('mapa_car')
NAT_V3 = unary_union(list(car3[car3.situacao.astype(str).str.contains('vegetacao nativa') | car3.classe_car.astype(str).str.contains('Remanescente')].geometry)).buffer(0)
AGUA_V3 = unary_union(list(car3[car3.subclasse.astype(str).str.contains('espelho')].geometry)).buffer(0)
SEM_ORTO = no_vazio(SEM_ORTO)
NAT_U = no_vazio(poly_only(NAT_V3.intersection(SEM_ORTO))); AGUA_U = no_vazio(poly_only(AGUA_V3.intersection(SEM_ORTO)))
NAT_T = unary_union([poly_only(NAT.intersection(H_ORTO)), NAT_U]).buffer(0)
NAT_ALL_T = unary_union([poly_only(NAT_ALL.intersection(H_ORTO)), NAT_U]).buffer(0)
NAT_05_T = unary_union([poly_only(NAT_05.intersection(H_ORTO)), NAT_U]).buffer(0)
AGUA_T = unary_union([AGUA, AGUA_U]).buffer(0)
log('  nativa (>=0,05 ha) imovel %.3f ha [todas %.3f; >=0,5 ha %.3f]; na faixa sem voo (v3) %.3f; agua %.3f; herbacea %.3f; construcoes %.3f; silvicultura %.3f'
    % (ha(NAT_T.intersection(IM)), ha(NAT_ALL_T.intersection(IM)), ha(NAT_05_T.intersection(IM)), ha(NAT_U), ha(AGUA_T.intersection(IM)), ha(HERB.intersection(IM)), ha(CONSTR.intersection(IM)), ha(SILV.intersection(IM))))

# --- ejes -----------------------------------------------------------------------------------
arr_g1 = cargar('arroios_g1'); arr_g2 = cargar('arroios_g2')
# como na v3: TODAS as linhas FBDS (imovel + 500 m): o buffer de trechos vizinhos tambem entra no imovel
hid = cargar('hidro'); hid = hid[hid.fonte.astype(str) == 'FBDS']
FBDS_LINES = list(hid.geometry)
eix = gpd.read_file(R('eixo_dtm_arroios.geojson')) if os.path.exists(R('eixo_dtm_arroios.geojson')) else gpd.GeoDataFrame(geometry=[])
# variante DTM: eixo DTM dos arroios 1 e 2 dentro da huella do DTM; FBDS no resto (arroio 3, G2, trechos fora da huella, vizinhos)
ids_dtm = set()
for _, r in arr_g1.iterrows():
    e = eix[(eix.gleba == 'G1') & (eix.arroio == r['nome'])] if len(eix) else []
    if len(e):
        ids_dtm |= set(str(r['fbds_ids']).split(','))
DTM_LINES = list(eix.geometry) if len(eix) else []
for _, r in hid.iterrows():
    if str(r.id_fonte) in ids_dtm:
        fuera = r.geometry.difference(H_DTM.buffer(-5))
        if not fuera.is_empty:
            DTM_LINES.append(fuera)
    else:
        DTM_LINES.append(r.geometry)
log('  linhas FBDS: %d (ids com eixo DTM: %s)' % (len(FBDS_LINES), sorted(ids_dtm)))
nasc = gpd.read_file(R('nascentes_ortofoto.geojson'))
P_NASC = nasc[nasc.id == '306158'].geometry.iloc[0]
BORDAS_OK = any((J03.get(k) or {}).get('bordas') for k in J03 if k.startswith('G'))

def app_de(lineas, faixa, nasc_r):
    cursos = unary_union([l.buffer(faixa, join_style=1) for l in lineas])
    return cursos.buffer(0), P_NASC.buffer(nasc_r)

APP = {}
for nome, lineas in (('fbds', FBDS_LINES), ('dtm', DTM_LINES)):
    cur, nas_c = app_de(lineas, APP_M, NASC_M)
    APP[nome] = {'cursos': cur, 'nascente': nas_c, 'total': unary_union([cur, nas_c]).buffer(0)}
cur20, nas15 = app_de(FBDS_LINES, PRA_M, PRA_NASC_M)
APP['pra'] = {'cursos': cur20, 'nascente': nas15, 'total': unary_union([cur20, nas15]).buffer(0)}
FAIXA_RES = REPRESA.buffer(30).buffer(0)
APP['fbds_reservatorio'] = {'cursos': APP['fbds']['cursos'], 'nascente': APP['fbds']['nascente'], 'total': unary_union([APP['fbds']['total'], FAIXA_RES]).buffer(0), 'faixa_reservatorio': FAIXA_RES}


def compor(app_geom, gleba_geom, nombre):
    A = poly_only(app_geom.intersection(gleba_geom))
    conf = poly_only(A.intersection(NAT_T)); ag = poly_only(A.intersection(AGUA_T).difference(NAT_T))
    rec = poly_only(A.difference(NAT_T).difference(AGUA_T))
    d = {'exigida_ha': ha(A), 'com_vegetacao_nativa_ha': ha(conf), 'agua_ha': ha(ag), 'a_recompor_ha': ha(rec)}
    d['a_recompor_por_subclasse_ha'] = {
        'pasto_herbacea': ha(rec.intersection(HERB)), 'construcoes': ha(rec.intersection(CONSTR)), 'silvicultura': ha(rec.intersection(SILV)),
        'arvores_isoladas_lt_0_05ha': ha(rec.intersection(ARV_ISOL)),
        'sem_cobertura_do_voo': ha(rec.intersection(SEM_ORTO)),
    }
    d['a_recompor_por_subclasse_ha']['cultivo_solo'] = round(d['a_recompor_ha'] - sum(d['a_recompor_por_subclasse_ha'].values()), 3)
    d['pct_conforme'] = round(100.0 * d['com_vegetacao_nativa_ha'] / d['exigida_ha'], 1) if d['exigida_ha'] else None
    d['envolvente_borda_0_5m_ha'] = [round(ha(A) - A.length * 0.5 / 1e4, 3), round(ha(A) + A.length * 0.5 / 1e4, 3)]
    d['_geoms'] = {'app': A, 'conforme': conf, 'agua': ag, 'recompor': rec}
    log('  APP %-18s %-6s exigida %.3f | nativa %.3f | agua %.3f | recompor %.3f %s' % (nombre, '', d['exigida_ha'], d['com_vegetacao_nativa_ha'], d['agua_ha'], d['a_recompor_ha'], d['a_recompor_por_subclasse_ha']))
    return d


RES = {'_meta': {'versao': 4, 'crs': CRS_METRICO, 'fecha_vuelo': FECHA_VUELO, 'fecha_s2_v3': FECHA_S2, 'generado': HOY,
                 'hipotese_principal': V3['_meta']['hipotese_principal'],
                 'fontes': ['ortho_01..05 (05_ORTOFOTO)', 'resultados_v3.json (ANTES)', 'parametros_legales.json', 'mapa_uso_car.geojson v3 (faixa sem voo)']},
       'imovel': {'area_ha': AREA_IM, 'G1_ha': AREA_G1, 'G2_ha': AREA_G2, 'rl_exigida_ha': RL_EX, 'mf_ha': LEG['modulo_fiscal_ha'], 'n_mf': round(AREA_IM / LEG['modulo_fiscal_ha'], 2)},
       'cobertura_voo': COB['resumen'], 'app': {}, 'reserva_legal': {}, 'represa': {}, 'nascentes': {}, 'cursos': {}, 'vegetacao': {}}

# --- APP por variante y gleba ---------------------------------------------------------------
for var in ('fbds', 'dtm', 'pra', 'fbds_reservatorio'):
    RES['app'][var] = {}
    for g in ('G1', 'G2', 'IMOVEL'):
        d = compor(APP[var]['total'], GL[g], '%s/%s' % (var, g))
        if var in ('fbds', 'fbds_reservatorio'):
            d['curso_ha'] = ha(APP[var]['cursos'].difference(APP[var]['nascente']).intersection(GL[g]))
            d['nascente_ha'] = ha(APP[var]['nascente'].intersection(GL[g]))
            if var == 'fbds_reservatorio':
                d['faixa_reservatorio_adicional_ha'] = ha(FAIXA_RES.difference(APP['fbds']['total']).intersection(GL[g]))
        RES['app'][var][g] = {k: v for k, v in d.items() if k != '_geoms'}
        RES['app'][var][g]['_g'] = d['_geoms']
RES['app']['borda_calha'] = {'disponivel': bool(BORDAS_OK),
                             'nota': ('NAO DISPONIVEL: ortho_03 nao construiu bordas (Arroio 1: 3 de 26 secoes com DTM de solo; Arroio 2: 0 de 56; '
                                      'Arroio 3 e G2: sem DTM). Sob dossel o DTM fotogrametrico e a copa: a borda da calha exige LiDAR ou levantamento GNSS/topografico em campo.')}
RES['app']['dtm']['nota'] = ('eixo DTM = caminho de minimo custo no corredor +-60 m do FBDS sobre o DTM hibrido; INDICATIVO: %s' %
                             '; '.join('%s: %s%% do talweg com DTM de solo, FBDS->talweg mediana %s m' % (k, (J03[k].get('talweg_pct_com_dtm_de_solo')), (J03[k].get('dist_fbds_vs_talweg') or {}).get('mediana_m')) for k in J03 if k.startswith('G') and J03[k].get('talweg_m_total')))
RES['app']['referencia'] = 'fbds (eixo FBDS/IAT 1:25.000), como na v3: a ortofoto NAO permitiu substituir o eixo sob dossel; a melhora da v4 esta na COBERTURA (vegetacao 0,5 m, agua, nascente)'

# --- RL ----------------------------------------------------------------------------------------
A1 = RES['app']['fbds']['G1']['_g']['app']
frag = cargar('fragmentos'); F13 = frag[frag.frag_id == 13].geometry.iloc[0]
def rl(nat_geom, rotulo):
    fora = poly_only(nat_geom.intersection(G1).difference(A1)); dentro = poly_only(nat_geom.intersection(G1).intersection(A1))
    comp = ha(fora) + ha(dentro)
    per = poly_only(nat_geom.intersection(G1)).length
    d = {'remanescente_fora_app_ha': ha(fora), 'app_vegetada_art15_ha': ha(dentro), 'vegetacao_computavel_ha': round(comp, 3),
         'deficit_ha': round(RL_EX - comp, 3), 'envolvente_0_5m_ha': [round(comp - per * 0.5 / 1e4, 3), round(comp + per * 0.5 / 1e4, 3)],
         'pct_atendido': round(100 * comp / RL_EX, 1)}
    log('  RL %-34s fora APP %.3f + APP vegetada %.3f = %.3f -> deficit %.3f (env %s)' % (rotulo, d['remanescente_fora_app_ha'], d['app_vegetada_art15_ha'], comp, d['deficit_ha'], d['envolvente_0_5m_ha']))
    return d
RES['reserva_legal'] = {
    'exigida_ha': RL_EX,
    'principal_mmu_0_05ha_g2_terra_limpa': rl(NAT_T, 'principal (MMU 0,05 ha, G2 terra limpa)'),
    'sensibilidade_todas_arvores': rl(NAT_ALL_T, 'todas as manchas (>= 25 m2)'),
    'sensibilidade_fragmentos_ge_0_5ha': rl(NAT_05_T, 'so fragmentos >= 0,5 ha'),
    'conservador_sem_fragmento_13': rl(poly_only(NAT_T.difference(F13.buffer(0.5))), 'conservador (sem fragmento 13)'),
}
g2_nat = ha(NAT_T.intersection(G2))
RES['reserva_legal']['se_ponta_norte_da_g2_for_do_imovel'] = {'vegetacao_g2_ha': g2_nat,
    'vegetacao_computavel_ha': round(RES['reserva_legal']['principal_mmu_0_05ha_g2_terra_limpa']['vegetacao_computavel_ha'] + g2_nat, 3),
    'deficit_ha': round(RES['reserva_legal']['principal_mmu_0_05ha_g2_terra_limpa']['deficit_ha'] - g2_nat, 3),
    'nota': 'G2 sem ortofoto na ponta norte (%.3f ha): ali valem as classes v3' % (COB['resumen']['G2']['sem_ortofoto_ha'])}
RES['reserva_legal']['veredicto'] = 'NAO CONFORME (deficit %.2f ha; conservador %.2f ha)' % (RES['reserva_legal']['principal_mmu_0_05ha_g2_terra_limpa']['deficit_ha'], RES['reserva_legal']['conservador_sem_fragmento_13']['deficit_ha'])

# --- represa / nascentes / cursos / vegetacao (resumo) -------------------------------------------
rep = J02['represa']
RES['represa'] = {'espelho_22_mai_2026_ha': rep['area_agua_ha'], 'incerteza_borda_ha': rep['incerteza_borda_ha'], 'ge_1ha': rep['ge_1ha_22_mai_2026'],
                  'vaso_indicador_ha': rep['vaso_indicador_ha'], 'cota_espelho_m': rep['cota_espelho_m'], 'cota_nota': rep['cota_nota'],
                  'espelho_maximo_potencial_por_dtm_ha': rep['espelho_maximo_potencial_por_dtm_ha'], 'espelho_maximo_nota': rep['espelho_maximo_nota'],
                  'comparacao_fontes': rep['comparacao_fontes'], 'alinhamento_dique': rep['alinhamento_dique'],
                  'dispensa_art4_par4_lt1ha': not rep['ge_1ha_22_mai_2026'],
                  'regra': 'art. 4 III: faixa = a da licenca/outorga do barramento (outorga previa 26039/2023 IRREGULAR e vencida); par. 4: dispensa so se espelho < 1 ha -> NAO se aplica (1,388 ha em 22-mai-2026); cenario faixa 30 m = fbds_reservatorio',
                  'reservatorio_cabeceira_arroio2': J02.get('reservatorio_cabeceira')}
RES['nascentes'] = {'com_app_50m': J04['nascentes_com_app_50m'], 'pontos': J04['pontos'], 'nota_caudal': J04['nota_caudal'], 'leitura': J04['leitura']}
RES['cursos'] = {k: {kk: vv for kk, vv in v.items() if kk not in ('secoes',)} | {'secoes': v.get('secoes')} for k, v in J03.items() if k.startswith('G')}
RES['cursos']['metodo'] = J03['metodo']
RES['vegetacao'] = {'por_gleba': J05['por_gleba'], 'fragmentos': J05['fragmentos'], 'silvicultura': {'componentes': J05['silvicultura_componentes'], 'metodo': J05['silvicultura_metodo']},
                    'nativa_imovel_ha': {'mmu_0_05ha': ha(NAT_T.intersection(IM)), 'todas_ge_25m2': ha(NAT_ALL_T.intersection(IM)), 'fragmentos_ge_0_5ha': ha(NAT_05_T.intersection(IM))},
                    'nativa_G1_ha': ha(NAT_T.intersection(G1)), 'nativa_G2_ha': g2_nat}

# --- mapa CAR v4 (particion vectorial que cierra) ---------------------------------------------------
with Cronometro('mapa CAR v4'):
    filas = []
    def add(g, geom, classe, sub, sit, nota=''):
        geom = poly_only(geom)
        if geom.is_empty or geom.area < 1:
            return
        filas.append({'gleba': g, 'classe_car': classe, 'subclasse': sub, 'situacao': sit, 'area_ha': ha(geom), 'nota': nota, 'geometry': geom})
    for g in ('G1', 'G2'):
        GG = GL[g]
        nasc_c = poly_only(APP['fbds']['nascente'].intersection(GG)); curso = poly_only(APP['fbds']['cursos'].difference(APP['fbds']['nascente']).intersection(GG))
        for nome, A, cl in (('nascente', nasc_c, "APP - Nascente ou olho d'agua perene"), ('curso', curso, "APP - Curso d'agua natural de ate 10 metros")):
            add(g, A.intersection(NAT_T), cl, 'conforme', 'vegetacao nativa (ortofoto 0,5 m)')
            add(g, A.intersection(AGUA_T).difference(NAT_T), cl, 'agua', 'agua (ortofoto 22-mai-2026)')
            rec = A.difference(NAT_T).difference(AGUA_T)
            add(g, rec.intersection(HERB), cl, 'a recompor', 'pasto/herbacea')
            add(g, rec.intersection(CONSTR), cl, 'a recompor', 'construcoes')
            add(g, rec.intersection(SEM_ORTO).difference(HERB).difference(CONSTR), cl, 'a recompor', 'sem cobertura do voo (classe v3)')
            add(g, rec.difference(HERB).difference(CONSTR).difference(SEM_ORTO), cl, 'a recompor', 'cultivo/solo/arvores isoladas')
        A_all = poly_only(APP['fbds']['total'].intersection(GG))
        resto = poly_only(GG.difference(A_all))
        add(g, resto.intersection(REPRESA), 'Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua', 'agua 22-mai-2026 (1,388 ha; faixa a definir pelo IAT)')
        add(g, resto.intersection(AGUA_T).difference(REPRESA), 'Reservatorio artificial / lagoa', 'espelho d agua', 'lamina fora da APP (ortofoto)')
        rem = resto.intersection(NAT_T).difference(AGUA_T)
        add(g, rem, 'Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP', 'conservada (estagio requer campo)')
        cons = resto.difference(NAT_T).difference(AGUA_T)
        add(g, cons.intersection(SILV), 'Area Consolidada', 'silvicultura', 'plantio florestal (nao confirmado na ortofoto)')
        add(g, cons.intersection(CONSTR).difference(SILV), 'Area Consolidada', 'construcoes', 'sede/benfeitorias')
        add(g, cons.intersection(HERB).difference(SILV).difference(CONSTR), 'Area Consolidada', 'pasto/herbacea', 'uso antropico fora da APP')
        add(g, cons.intersection(ARV_ISOL).difference(SILV).difference(CONSTR).difference(HERB), 'Area Consolidada', 'arvores isoladas (< 0,05 ha)', 'nao computadas como remanescente')
        add(g, cons.intersection(SEM_ORTO).difference(SILV).difference(CONSTR).difference(HERB).difference(ARV_ISOL), 'Area Consolidada', 'sem cobertura do voo', 'classe v3 (RF S2 10 m)')
        add(g, cons.difference(SILV).difference(CONSTR).difference(HERB).difference(ARV_ISOL).difference(SEM_ORTO), 'Area Consolidada', 'uso agricola', 'cultivo/solo fora da APP')
    car = gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geometry'} for f in filas], geometry=[f['geometry'] for f in filas], crs=CRS_METRICO)
    car['fecha'] = FECHA_VUELO
    guardar_gdf(car, R('mapa_uso_car_v4.geojson'))
    fecha = {}
    for g, GG in (('G1', G1), ('G2', G2), ('IMOVEL', IM)):
        sub = car if g == 'IMOVEL' else car[car.gleba == g]
        soma = round(float(sub.area_ha.sum()), 3)
        uni = unary_union(list(sub.geometry))
        solape = round(float(sub.geometry.area.sum() - uni.area) / 1e4, 4)
        fecha[g] = {'soma_ha': soma, 'area_gleba_ha': round(GG.area / 1e4, 3), 'diferenca_ha': round(soma - GG.area / 1e4, 3), 'solape_ha': solape,
                    'fecha': bool(abs(soma - GG.area / 1e4) < 0.02 and solape < 0.01)}
        log('  CAR v4 %s: soma %.3f vs gleba %.3f (dif %.3f, solape %.4f) -> %s' % (g, soma, GG.area / 1e4, soma - GG.area / 1e4, solape, 'FECHA' if fecha[g]['fecha'] else 'NAO FECHA'))
    RES['mapa_car_v4'] = {'fecha': fecha, 'linhas': [{k: v for k, v in f.items() if k != 'geometry'} for f in filas]}
    if not all(v['fecha'] for v in fecha.values()):
        raise RuntimeError('o mapa CAR v4 nao fecha: %s' % fecha)

# --- capas APP / RL ---------------------------------------------------------------------------------
filas = []
for var in ('fbds', 'dtm', 'pra', 'fbds_reservatorio'):
    for g in ('G1', 'G2'):
        gg = RES['app'][var][g]['_g']
        for sit in ('conforme', 'agua', 'recompor'):
            if not gg[sit].is_empty:
                filas.append({'variante': var, 'gleba': g, 'situacao': sit, 'area_ha': ha(gg[sit]), 'geometry': gg[sit]})
guardar_gdf(gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geometry'} for f in filas], geometry=[f['geometry'] for f in filas], crs=CRS_METRICO), R('app_v4.geojson'))
rlg = [{'parte': 'remanescente fora APP', 'area_ha': ha(NAT_T.intersection(G1).difference(A1)), 'geometry': poly_only(NAT_T.intersection(G1).difference(A1))},
       {'parte': 'APP vegetada (art. 15)', 'area_ha': ha(NAT_T.intersection(G1).intersection(A1)), 'geometry': poly_only(NAT_T.intersection(G1).intersection(A1))}]
guardar_gdf(gpd.GeoDataFrame([{k: v for k, v in f.items() if k != 'geometry'} for f in rlg], geometry=[f['geometry'] for f in rlg], crs=CRS_METRICO), R('rl_vegetacao_computavel_v4.geojson'))
for var in RES['app']:
    if isinstance(RES['app'][var], dict):
        for g in list(RES['app'][var].keys()):
            if isinstance(RES['app'][var][g], dict):
                RES['app'][var][g].pop('_g', None)

# --- ANTES (v3) -> DEPOIS (v4) ------------------------------------------------------------------------
Af = RES['app']['fbds']; Ar = RES['app']['fbds_reservatorio']; Ap = RES['app']['pra']; RLp = RES['reserva_legal']['principal_mmu_0_05ha_g2_terra_limpa']
tab = [
    ('APP exigivel imovel (ha)', K3['app_exigivel_imovel_ha'], Af['IMOVEL']['exigida_ha']),
    ('APP exigivel G1 (ha)', K3['app_g1_ha'], Af['G1']['exigida_ha']),
    ('APP exigivel G2 (ha)', K3['app_g2_ha'], Af['G2']['exigida_ha']),
    ('APP G1 com vegetacao nativa (ha)', K3['app_com_vegetacao_g1_ha'], Af['G1']['com_vegetacao_nativa_ha']),
    ('APP G1 agua (ha)', K3['app_agua_g1_ha'], Af['G1']['agua_ha']),
    ('APP G1 a recompor (ha)', K3['app_a_recompor_ha'], Af['G1']['a_recompor_ha']),
    ('APP G1 a recompor cenario PRA-PR 20 m (ha)', K3['app_a_recompor_pra_ha'], Ap['G1']['a_recompor_ha']),
    ('APP G1 cenario faixa reservatorio: exigida (ha)', K3['app_cenario_reserv_exigida_ha'], Ar['G1']['exigida_ha']),
    ('APP G1 cenario faixa reservatorio: a recompor (ha)', K3['app_cenario_reserv_recompor_ha'], Ar['G1']['a_recompor_ha']),
    ('Vegetacao nativa computavel RL (ha)', K3['veg_computavel_ha'], RLp['vegetacao_computavel_ha']),
    ('Deficit RL imovel unico (ha)', K3['deficit_ha'], RLp['deficit_ha']),
    ('Vegetacao computavel conservadora sem frag. 13 (ha)', K3['veg_conservador_ha'], RES['reserva_legal']['conservador_sem_fragmento_13']['vegetacao_computavel_ha']),
    ('Deficit RL conservador (ha)', K3['deficit_conservador_ha'], RES['reserva_legal']['conservador_sem_fragmento_13']['deficit_ha']),
    ('Deficit RL se ponta norte G2 for do imovel (ha)', V3['reserva_legal']['se_ponta_norte_da_g2_for_do_imovel']['deficit_ha'], RES['reserva_legal']['se_ponta_norte_da_g2_for_do_imovel']['deficit_ha']),
    ('Represa: espelho (ha)', '%s-%s (2024-26)' % tuple(K3['represa_espelho_atual_ha']), rep['area_agua_ha']),
    ('Represa >= 1 ha', V3['represa']['maior_ou_igual_1ha'], 'SIM (22-mai-2026)' if rep['ge_1ha_22_mai_2026'] else 'NAO'),
    ('2o reservatorio cabeceira Arroio 2 (ha)', 0.0, (J02.get('reservatorio_cabeceira') or {}).get('area_agua_ha')),
    ('Nascentes com APP 50 m (n)', 1, len(J04['nascentes_com_app_50m'])),
]
RES['antes_depois'] = [{'item': a, 'v3_s2_10m_fbds_dem30': b, 'v4_ortofoto': c, 'delta': (round(c - b, 3) if isinstance(b, (int, float)) and isinstance(c, (int, float)) else None)} for a, b, c in tab]
log('\n  ANTES (v3) -> DEPOIS (v4):')
for t in RES['antes_depois']:
    log('    %-58s %12s -> %12s  %s' % (t['item'], t['v3_s2_10m_fbds_dem30'], t['v4_ortofoto'], ('(%+.3f)' % t['delta']) if t['delta'] is not None else ''))

RES['kpi'] = {'area_imovel_ha': AREA_IM, 'app_exigivel_imovel_ha': Af['IMOVEL']['exigida_ha'], 'app_g1_ha': Af['G1']['exigida_ha'], 'app_g2_ha': Af['G2']['exigida_ha'],
              'app_com_vegetacao_g1_ha': Af['G1']['com_vegetacao_nativa_ha'], 'app_agua_g1_ha': Af['G1']['agua_ha'], 'app_a_recompor_g1_ha': Af['G1']['a_recompor_ha'],
              'app_a_recompor_pra_ha': Ap['G1']['a_recompor_ha'], 'app_cenario_reserv_exigida_ha': Ar['G1']['exigida_ha'], 'app_cenario_reserv_recompor_ha': Ar['G1']['a_recompor_ha'],
              'rl_exigida_ha': RL_EX, 'veg_computavel_ha': RLp['vegetacao_computavel_ha'], 'deficit_ha': RLp['deficit_ha'],
              'veg_conservador_ha': RES['reserva_legal']['conservador_sem_fragmento_13']['vegetacao_computavel_ha'], 'deficit_conservador_ha': RES['reserva_legal']['conservador_sem_fragmento_13']['deficit_ha'],
              'represa_espelho_ha': rep['area_agua_ha'], 'represa_ge_1ha': rep['ge_1ha_22_mai_2026']}
RES['avisos'] = [
    'Data do voo 22-mai-2026 (fim do outono) vs cena S2 29-ago-2026 (seca): o nivel da represa e diferente (1,388 ha na ortofoto; 0,83-1,23 ha na serie 2024-26); o espelho legal deve ser medido em campo/na cota do vertedouro.',
    'DSM/DTM do voo terminam em N 7401711: a represa, o Arroio 3 e o fragmento 30 NAO tem modelo de elevacao (sem cota do espelho, sem espelho maximo potencial, sem secoes do Arroio 3).',
    'Faixa norte sem ortofoto (N > 7404007): %.3f ha da G1 e %.3f ha da G2 (inclui o trecho de 33 m do Arroio 1 na G2 e 26 %% do Arroio 1 na G1): ali valem as classes v3 (RF S2 10 m).' % (COB['resumen']['G1']['sem_ortofoto_ha'], COB['resumen']['G2']['sem_ortofoto_ha']),
    'Sob dossel fechado o DTM fotogrametrico (ODM/SMRF) E o proprio dossel: CHM ~ 0, talweg e borda da calha NAO mediveis (Arroio 1: 3/26 secoes com solo; Arroio 2: 0/56). A APP continua medida desde o eixo FBDS; a borda da calha exige LiDAR ou GNSS em campo.',
    'DTM sem GCP/RTK: desvio vertical ~ -40 m e inclinacao S-N ~12 m corrigidos por polinomio de 2o grau contra FABDEM (residuo MAD 0,2 m): cotas absolutas +-0,5 m em solo aberto, sem valor legal.',
    'CHM ODM pode ter ruido nas bordas das copas e SUBESTIMA a altura sob dossel fechado (fragmento 13: altura medida em so 23 %% da area arborea; fragmento 2: 47 %%).',
    'Estagio sucessional (CONAMA 2/1994) segue exigindo campo: a altura do dossel e so um indicador; DAP, area basal, estratos e especies indicadoras nao se medem por imagem.',
    'Silvicultura do RF S2 (1,06 ha) NAO confirmada na ortofoto (nenhum componente com fileiras regulares): confirmar em campo.',
    'Alinhamento: ortofoto vs S2 10 m |dx,dy| <= 3 m (global +1,5/-0,5 m); ortofoto vs DSM < 0,4 m; dique da represa: FBDS 2013 esta 9 m a oeste e o CAR 8 m a leste do dique na ortofoto.',
]
guardar_json(R('resultados_v4.json'), RES)
log('ortho_06 listo.')
