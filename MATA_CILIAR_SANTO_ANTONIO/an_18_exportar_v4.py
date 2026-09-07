# -*- coding: utf-8 -*-
"""an_18_exportar_v4 — vetores de entrega da v4 (ortofoto de drone 22/05/2026; cliente / retificacao do CAR).

    python an_18_exportar_v4.py   -> 04_VETORES_ENTREGA_V4/

Para cada capa: GeoJSON (EPSG:4674, datum do CAR), Shapefile (EPSG:4674, campos <= 10 caracteres, UTF-8) e KML (WGS 84).
Mais LEIAME.txt bilingue e um zip. Nada se recalcula: os atributos sao os de 05_ORTOFOTO (ortho_02..07) e de 02_ANALISIS (v3).
Reutiliza kml() e limpiar() de an_06_exportar.
"""
import os
import sys
import zipfile

import geopandas as gpd
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, CRS_METRICO, leer_json, log  # noqa: E402
from an_06_exportar import kml, limpiar                                    # noqa: E402

ENTREGA = os.path.join(PROYECTO, '04_VETORES_ENTREGA_V4')
ORTO = os.path.join(PROYECTO, '05_ORTOFOTO')
CAUCE = os.path.join(ORTO, 'cauce')
HP = os.path.join(ANALISIS, 'hidrologia_pro')
CRS_CAR = 'EPSG:4674'

D = leer_json(os.path.join(ORTO, 'resultados_v4.json'))
D3 = leer_json(os.path.join(ANALISIS, 'resultados_v3.json'))
K = D['kpi']; RL = D['reserva_legal']['principal_mmu_0_05ha_g2_terra_limpa']; RP = D['represa']; K3 = D3['kpi']
f2 = lambda x: ('%.2f' % x).replace('.', ',')
_COB = {r['capa']: r['area_ha'] for _, r in gpd.read_file(os.path.join(ORTO, 'cobertura_vuelo.geojson')).iterrows()}
_COBT = tuple(_COB[c] for c in ('ortofoto', 'dtm_dsm', 'imovel_sem_ortofoto', 'imovel_sem_dtm'))
f3 = lambda x: ('%.3f' % x).replace('.', ',')

CAPAS = {
    'v4_limites': dict(src='v3_limites', shp={'gleba': 'gleba', 'nome': 'nome', 'area_ha': 'area_ha', 'alqueires': 'alqueires', 'rl_parcela_ha': 'rl_parc_ha', 'rl_imovel_ha': 'rl_imov_ha', 'terra_limpa': 'terra_limp'},
                       pt='As duas glebas do imóvel único (G1 %s ha; G2 %s ha = %s alqueires, comprada como terra limpa); RL do imóvel = 20%% de %s ha = %s ha' % (f2(K3['area_g1_ha']), f2(K3['area_g2_ha']), f2(K3['g2_alqueires']), f2(K['area_imovel_ha']), f2(K['rl_exigida_ha'])),
                       es='Las dos glebas del inmueble único (G1 %s ha; G2 %s ha = %s alqueires, comprada como tierra limpia); RL del inmueble = 20%% de %s ha = %s ha' % (f2(K3['area_g1_ha']), f2(K3['area_g2_ha']), f2(K3['g2_alqueires']), f2(K['area_imovel_ha']), f2(K['rl_exigida_ha']))),
    'v4_CAR_existente': dict(src='v3_CAR_existente', shp={'capa': 'capa', 'cod_tema': 'cod_tema', 'cod_imovel': 'cod_imovel', 'relacao': 'relacao', 'ind_status': 'status', 'des_condic': 'condicao', 'num_area_decl': 'num_area', 'area_geom_ha': 'geom_ha', 'area_no_imovel_ha': 'no_imov_ha'},
                             pt='CAR existente PR-4124301-F127CD1E... (próprio, %s ha) e CAR de origem da Gleba 2 PR-4124301-5223911747...: área, APP, RL averbada/proposta, vegetação nativa, consolidada, hidrografia (réplica IAT do SICAR, 06/09/2026). Na ortofoto o dique da represa fica 9 m a leste do espelho FBDS e 8 m a oeste do polígono do CAR' % f2(K3['car_area_ha']),
                             es='CAR existente PR-4124301-F127CD1E... (propio, %s ha) y CAR de origen de la Gleba 2 PR-4124301-5223911747...: área, APP, RL inscrita/propuesta, vegetación nativa, consolidada, hidrografía (réplica IAT del SICAR, 06/09/2026). En la ortofoto el dique de la represa queda 9 m al este del espejo FBDS y 8 m al oeste del polígono del CAR' % f2(K3['car_area_ha'])),
    'v4_APP': dict(src=os.path.join(ORTO, 'app_v4'), shp={'variante': 'variante', 'gleba': 'gleba', 'situacao': 'situacao', 'area_ha': 'area_ha'},
                   pt='APP v4 por variante e situação (cobertura da ortofoto 0,5 m de 22/05/2026): fbds = exigível do eixo FBDS (imóvel %s ha [%s; %s]; G1 %s; G2 %s): conforme (vegetação nativa) %s, água %s, a recompor %s ha (PRA-PR 20 m: %s); dtm = eixo alternativo pelo talvegue do DTM do drone (INDICATIVO, %s ha); pra = faixa PRA-PR 20 m / 15 m; fbds_reservatorio = cenário com faixa de 30 m da represa (exigível %s, a recompor %s ha). Borda da calha NÃO medida (dossel fechado): levantar com GNSS' % (
                       f2(K['app_exigivel_imovel_ha']), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][0]), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][1]), f2(K['app_g1_ha']), f2(K['app_g2_ha']), f2(D['app']['fbds']['IMOVEL']['com_vegetacao_nativa_ha']), f2(K['app_agua_g1_ha']), f2(K['app_a_recompor_g1_ha']), f2(K['app_a_recompor_pra_ha']), f2(D['app']['dtm']['IMOVEL']['exigida_ha']), f2(K['app_cenario_reserv_exigida_ha']), f2(K['app_cenario_reserv_recompor_ha'])),
                   es='APP v4 por variante y situación (cobertura de la ortofoto 0,5 m del 22/05/2026): fbds = exigible desde el eje FBDS (inmueble %s ha [%s; %s]; G1 %s; G2 %s): conforme (vegetación nativa) %s, agua %s, a recomponer %s ha (PRA-PR 20 m: %s); dtm = eje alternativo por el talweg del DTM del dron (INDICATIVO, %s ha); pra = faja PRA-PR 20 m / 15 m; fbds_reservatorio = escenario con faja de 30 m de la represa (exigible %s, a recomponer %s ha). Borde del cauce NO medido (dosel cerrado): levantar con GNSS' % (
                       f2(K['app_exigivel_imovel_ha']), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][0]), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][1]), f2(K['app_g1_ha']), f2(K['app_g2_ha']), f2(D['app']['fbds']['IMOVEL']['com_vegetacao_nativa_ha']), f2(K['app_agua_g1_ha']), f2(K['app_a_recompor_g1_ha']), f2(K['app_a_recompor_pra_ha']), f2(D['app']['dtm']['IMOVEL']['exigida_ha']), f2(K['app_cenario_reserv_exigida_ha']), f2(K['app_cenario_reserv_recompor_ha']))),
    'v4_vegetacao_nativa_ortofoto': dict(src=os.path.join(ORTO, 'vegetacao_nativa_ortofoto'), shp={'area_ha': 'area_ha', 'classe_dominante': 'classe', 'gleba': 'gleba', 'frag_id_s2': 'frag_s2', 'sem_chm': 'sem_chm', 'area_dentro_imovel_ha': 'in_imov_ha', 'fecha': 'fecha'},
                                         pt='Manchas de vegetação nativa arbórea/arbustiva (>= 25 m²) classificadas a 0,5 m sobre a ortofoto + DSM/DTM (RF, 22/05/2026), com o fragmento RF S2 (v3) correspondente e se têm CHM; computável para a RL = manchas >= 0,05 ha na Gleba 1 (%s ha)' % f2(K['veg_computavel_ha']),
                                         es='Manchas de vegetación nativa arbórea/arbustiva (>= 25 m²) clasificadas a 0,5 m sobre la ortofoto + DSM/DTM (RF, 22/05/2026), con el fragmento RF S2 (v3) correspondiente y si tienen CHM; computable para la RL = manchas >= 0,05 ha en la Gleba 1 (%s ha)' % f2(K['veg_computavel_ha'])),
    'v4_RL_computavel': dict(src=os.path.join(ORTO, 'rl_vegetacao_computavel_v4'), shp={'parte': 'parte', 'area_ha': 'area_ha'},
                             pt='Vegetação nativa computável para a RL (art. 12 + art. 15) na ortofoto: remanescente fora da APP %s + APP vegetada %s = %s ha [%s; %s] (imóvel único: exigida %s, déficit %s; conservador sem o fragmento 13: %s / déficit %s). NÃO é "RL existente": a RL só existe quando localizada e aprovada pelo IAT' % (
                                 f2(RL['remanescente_fora_app_ha']), f2(RL['app_vegetada_art15_ha']), f2(K['veg_computavel_ha']), f2(RL['envolvente_0_5m_ha'][0]), f2(RL['envolvente_0_5m_ha'][1]), f2(K['rl_exigida_ha']), f2(K['deficit_ha']), f2(K['veg_conservador_ha']), f2(K['deficit_conservador_ha'])),
                             es='Vegetación nativa computable para la RL (art. 12 + art. 15) en la ortofoto: remanente fuera de la APP %s + APP vegetada %s = %s ha [%s; %s] (inmueble único: exigida %s, déficit %s; conservador sin el fragmento 13: %s / déficit %s). NO es "RL existente": la RL solo existe cuando está localizada y aprobada por el IAT' % (
                                 f2(RL['remanescente_fora_app_ha']), f2(RL['app_vegetada_art15_ha']), f2(K['veg_computavel_ha']), f2(RL['envolvente_0_5m_ha'][0]), f2(RL['envolvente_0_5m_ha'][1]), f2(K['rl_exigida_ha']), f2(K['deficit_ha']), f2(K['veg_conservador_ha']), f2(K['deficit_conservador_ha']))),
    'v4_RL_proposta': dict(src='v3_RL_proposta', shp={'classe_car': 'classe_car', 'area_ha': 'area_ha', 'rl_exigida_ha': 'rl_exig_ha', 'falta_localizar_ha': 'falta_ha', 'corredor_ha': 'corredor', 'status': 'status'},
                           pt='Reserva Legal Proposta da v3 recortada à Gleba 1 (%s ha): A REVER sobre a vegetação v4 (computável %s ha + corredor %s ha; falta localizar cerca de %s ha ou compensar, art. 66 III); sujeita ao IAT (art. 14)' % (f2(D3['reserva_legal']['localizacao_proposta']['rl_proposta_recortada_g1_ha']), f2(K['veg_computavel_ha']), f2(D3['reserva_legal']['localizacao_proposta']['corredor_g1_ha']), f2(K['rl_exigida_ha'] - K['veg_computavel_ha'] - D3['reserva_legal']['localizacao_proposta']['corredor_g1_ha'])),
                           es='Reserva Legal Propuesta de la v3 recortada a la Gleba 1 (%s ha): A REVISAR sobre la vegetación v4 (computable %s ha + corredor %s ha; falta localizar cerca de %s ha o compensar, art. 66 III); sujeta al IAT (art. 14)' % (f2(D3['reserva_legal']['localizacao_proposta']['rl_proposta_recortada_g1_ha']), f2(K['veg_computavel_ha']), f2(D3['reserva_legal']['localizacao_proposta']['corredor_g1_ha']), f2(K['rl_exigida_ha'] - K['veg_computavel_ha'] - D3['reserva_legal']['localizacao_proposta']['corredor_g1_ha']))),
    'v4_arroios_FBDS': dict(src='__arroios__', shp={'gleba': 'gleba', 'n': 'n', 'nome': 'nome', 'posicao': 'posicao', 'fbds_ids': 'fbds_ids', 'comprimento_dentro_m': 'comp_in_m', 'comprimento_total_fbds_m': 'comp_tot_m', 'nasce_dentro': 'nasce_in', 'tipo': 'tipo', 'represado': 'represado'},
                            pt='Arroios (eixo FBDS 2013, referência legal da APP): 1 norte (523 m), 2 central (951 m, nasce na gleba), 3 sul = Ribeirão do Salto (564 m, represado); 33 m do Arroio 1 na Gleba 2. Largura: classe FBDS 0-10 m; estimativa M3 5,9 / 2,5 / 6,5 m; <= 10 m PROVÁVEL, sem medição direta (protocolo de campo M5)',
                            es='Arroyos (eje FBDS 2013, referencia legal de la APP): 1 norte (523 m), 2 central (951 m, nace en la gleba), 3 sur = Ribeirão do Salto (564 m, represado); 33 m del Arroyo 1 en la Gleba 2. Ancho: clase FBDS 0-10 m; estimación M3 5,9 / 2,5 / 6,5 m; <= 10 m PROBABLE, sin medición directa (protocolo de campo M5)'),
    'v4_eixo_DTM': dict(src=os.path.join(ORTO, 'eixo_dtm_arroios'), shp={'gleba': 'gleba', 'arroio': 'arroio', 'fonte': 'fonte', 'pct_com_dtm_de_solo': 'pct_solo', 'comprimento_m': 'comp_m', 'comprimento_dentro_gleba_m': 'comp_in_m', 'acc_ha_max': 'acc_ha_max'},
                        pt='Talvegue dos Arroios 1 e 2 no DTM híbrido do drone (mínimo custo no corredor ±60 m do FBDS): INDICATIVO — sob dossel o DTM é a copa (Arroio 1: 44 %% do talvegue com solo; Arroio 2: 8 %%); fica a 20 / 17 m (mediana) do eixo FBDS. Arroio 3 sem DTM',
                        es='Talweg de los Arroyos 1 y 2 en el DTM híbrido del dron (mínimo costo en el corredor ±60 m del FBDS): INDICATIVO — bajo dosel el DTM es la copa (Arroyo 1: 44 %% del talweg con suelo; Arroyo 2: 8 %%); queda a 20 / 17 m (mediana) del eje FBDS. Arroyo 3 sin DTM'),
    'v4_secoes': dict(src=os.path.join(ORTO, 'secoes_transversais'), shp={'gleba': 'gleba', 'arroio': 'arroio', 'id_secao': 'id_secao', 's_m': 's_m', 'pct_com_dado': 'pct_dado', 'pct_dosel_centro': 'pct_dosel', 'pct_arboreo_perfil': 'pct_arb', 'valida': 'valida', 'motivo': 'motivo', 'z_fondo_m': 'z_fondo', 'largura_h0.5_m': 'larg_h05', 'largura_h1.0_m': 'larg_h10', 'largura_quiebre_m': 'larg_queb', 'incisao_m': 'incisao'},
                      pt='Seções transversais a cada 20 m (60 m) sobre o talvegue DTM: Arroio 1 = 3 de 26 válidas (DTM de solo), Arroio 2 = 0 de 56 — a borda da calha NÃO é medível por fotogrametria sob dossel; larguras relativas ao fundo (sem valor legal)',
                      es='Secciones transversales cada 20 m (60 m) sobre el talweg DTM: Arroyo 1 = 3 de 26 válidas (DTM de suelo), Arroyo 2 = 0 de 56 — el borde del cauce NO es medible por fotogrametría bajo dosel; anchos relativos al fondo (sin valor legal)'),
    'v4_cauce_medicoes': dict(src=os.path.join(CAUCE, 'cauce_medicoes'), shp={'arroio': 'arroio', 'metodo': 'metodo', 's_m': 's_m', 'largura_h0.5_m': 'larg_h05', 'largura_h1.0_m': 'larg_h10', 'cobertura': 'cobertura', 'aviso': 'aviso', 'largura_m': 'largura_m', 'largura_max_m': 'larg_max', 'calha_veg_m': 'calha_veg', 'qualidade': 'qualidade', 'contexto': 'contexto', 'posicao': 'posicao', 'A_km2': 'A_km2', 'largura_int_m': 'larg_int', 'extrapolacao': 'extrapol'},
                              pt='Medições/estimativas da largura da calha (ortho_07): M2_secao = seções no DTM 5 cm (Arroio 1: 7, todas na borda campo-floresta, excluídas); M1_espelho = claros com água (Arroio 3: 3, todos no vertedouro da represa, artificiais); M3_estimativa = geometria hidráulica (Bieger 2015) em 5 pontos por arroio (ESTIMATIVA, não medição). Conclusão: <= 10 m provável, sem medição direta',
                              es='Mediciones/estimaciones del ancho del cauce (ortho_07): M2_secao = secciones en el DTM 5 cm (Arroyo 1: 7, todas en el borde campo-bosque, excluidas); M1_espelho = claros con agua (Arroyo 3: 3, todos en el vertedero de la represa, artificiales); M3_estimativa = geometría hidráulica (Bieger 2015) en 5 puntos por arroyo (ESTIMACIÓN, no medición). Conclusión: <= 10 m probable, sin medición directa'),
    'v4_nascentes': dict(src=os.path.join(ORTO, 'nascentes_ortofoto'), shp={'id': 'id', 'fonte': 'fonte', 'gleba': 'gleba', 'tem_dtm': 'tem_dtm', 'aporte_30m_ha_max45m': 'aporte_ha', 'chm_media_15m': 'chm_15m', 'cobertura_arborea_15m_pct': 'arb_pct', 'herbacea_15m_pct': 'herb_pct', 'solo_cultivo_15m_pct': 'solo_pct', 'higrofila_verde_baixa_15m_pct': 'varzea_pct', 'dist_agua_aberta_m': 'd_agua_m', 'relevo_local_ponto_menos_min50m_m': 'relevo_m', 'cota_dtm_m_fabdem': 'cota_m', 'veredicto': 'veredito', 'perenidade': 'perenid'},
                         pt='Nascentes com veredito v4: FBDS 306158 PROVÁVEL (cabeceira úmida: várzea herbácea, água aberta a 59 m; APP de 50 m aplicada; olho d\'água exato e perenidade só em campo); dem_1 = mesma cabeceira; 2º reservatório (0,048 ha) = corpo d\'água artificial sobre a cabeceira; dem_2 = NÃO nascente (lavoura). Cotas do DTM sem GCP: sem valor legal',
                         es='Nacientes con veredicto v4: FBDS 306158 PROBABLE (cabecera húmeda: várzea herbácea, agua abierta a 59 m; APP de 50 m aplicada; ojo de agua exacto y perennidad solo en campo); dem_1 = misma cabecera; 2º reservorio (0,048 ha) = cuerpo de agua artificial sobre la cabecera; dem_2 = NO naciente (cultivo). Cotas del DTM sin GCP: sin valor legal'),
    'v4_agua_ortofoto': dict(src=os.path.join(ORTO, 'agua_ortofoto_2026-05-22'), shp={'corpo': 'corpo', 'nome': 'nome', 'tipo': 'tipo', 'area_ha': 'area_ha', 'cota_dsm_m': 'cota_dsm', 'dsm_disponivel': 'tem_dsm', 'metodo': 'metodo', 'fecha': 'fecha'},
                             pt='Água na ortofoto de 22/05/2026: represa do Ribeirão do Salto %s ha (>= 1 ha: a dispensa do art. 4º §4º só cabe abaixo de 1 ha e não se aplica; faixa pela licença; sem DSM: cota não medida), vaso indicador %s ha, 2º reservatório na cabeceira do Arroio 2 %s ha (CAR %s) + vaso até +0,5 m, e 8 lâminas menores candidatas. Espelho do dia, não o máximo' % (f3(RP['espelho_22_mai_2026_ha']), f3(RP['vaso_indicador_ha']), f3(RP['reservatorio_cabeceira_arroio2']['area_agua_ha']), f3(RP['reservatorio_cabeceira_arroio2']['area_car_declarada_ha'])),
                             es='Agua en la ortofoto del 22/05/2026: represa del Ribeirão do Salto %s ha (>= 1 ha: la dispensa del art. 4º §4º solo cabe por debajo de 1 ha y no se aplica; faja por la licencia; sin DSM: cota no medida), vaso indicador %s ha, 2º reservorio en la cabecera del Arroyo 2 %s ha (CAR %s) + vaso hasta +0,5 m, y 8 láminas menores candidatas. Espejo del día, no el máximo' % (f3(RP['espelho_22_mai_2026_ha']), f3(RP['vaso_indicador_ha']), f3(RP['reservatorio_cabeceira_arroio2']['area_agua_ha']), f3(RP['reservatorio_cabeceira_arroio2']['area_car_declarada_ha']))),
    'v4_mapa_CAR': dict(src=os.path.join(ORTO, 'mapa_uso_car_v4'), shp={'gleba': 'gleba', 'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao', 'area_ha': 'area_ha', 'nota': 'nota', 'fecha': 'fecha'},
                        pt='Uso e cobertura com a nomenclatura do Módulo de Cadastro do SICAR a partir da ortofoto 0,5 m (faixa sem voo: classes v3); sem sobreposição; fecha em 144,21 (G1) + 13,54 (G2) = 157,75 ha; "perene" = nomenclatura, perenidade não verificada; camada a conferir pelo responsável pela inscrição',
                        es='Uso y cobertura con la nomenclatura del Módulo de Catastro del SICAR a partir de la ortofoto 0,5 m (faja sin vuelo: clases v3); sin superposición; cierra en 144,21 (G1) + 13,54 (G2) = 157,75 ha; "perene" = nomenclatura, perennidad no verificada; capa a verificar por el responsable de la inscripción'),
    'v4_cobertura_voo': dict(src=os.path.join(ORTO, 'cobertura_vuelo'), shp={'capa': 'capa', 'area_ha': 'area_ha'},
                             pt='Cobertura do voo de 22/05/2026: ortofoto (%s ha), DSM/DTM (%s ha, só ao norte de N 7.401.711), imóvel sem ortofoto (%s ha, faixa norte) e imóvel sem DTM (%s ha)' % tuple(f2(x) for x in _COBT),
                             es='Cobertura del vuelo del 22/05/2026: ortofoto (%s ha), DSM/DTM (%s ha, solo al norte de N 7.401.711), inmueble sin ortofoto (%s ha, faja norte) e inmueble sin DTM (%s ha)' % tuple(f2(x) for x in _COBT)),
}
CAMPOS = {
    'gleba': ('G1 = imóvel principal; G2 = os 6 alqueires', 'G1 = inmueble principal; G2 = los 6 alqueires'), 'nome': ('nome', 'nombre'), 'area_ha': ('área em hectares (EPSG:31982)', 'área en hectáreas (EPSG:31982)'),
    'alqueires': ('alqueires paulistas (2,42 ha)', 'alqueires paulistas (2,42 ha)'), 'rl_parcela_ha': ('parcela da RL (20% da gleba) — só inventário', 'parcela de la RL (20% de la gleba) — solo inventario'), 'rl_imovel_ha': ('RL exigida do imóvel único', 'RL exigida del inmueble único'),
    'terra_limpa': ('1 = comprada como terra limpa', '1 = comprada como tierra limpia'), 'capa': ('camada', 'capa'), 'cod_tema': ('tema SICAR', 'tema SICAR'), 'cod_imovel': ('código do imóvel no CAR', 'código del inmueble en el CAR'), 'relacao': ('propio_G1 / cubre_G2', 'propio_G1 / cubre_G2'),
    'ind_status': ('status do CAR', 'estado del CAR'), 'des_condic': ('condição da análise', 'condición del análisis'), 'num_area_decl': ('área declarada (ha)', 'área declarada (ha)'), 'area_geom_ha': ('área da geometria (ha)', 'área de la geometría (ha)'), 'area_no_imovel_ha': ('área dentro do imóvel (ha)', 'área dentro del inmueble (ha)'),
    'variante': ('fbds (exigível) / dtm (indicativo) / pra (faixa PRA-PR) / fbds_reservatorio (cenário faixa da represa)', 'fbds (exigible) / dtm (indicativo) / pra (faja PRA-PR) / fbds_reservatorio (escenario faja de la represa)'),
    'situacao': ('conforme (vegetação nativa) / agua / recompor; no mapa CAR: leitura da ortofoto', 'conforme (vegetación nativa) / agua / recompor; en el mapa CAR: lectura de la ortofoto'),
    'classe_dominante': ('arborea_dosel_fechado / arborea_arbustiva_sem_chm', 'arborea_dosel_fechado / arborea_arbustiva_sem_chm'), 'frag_id_s2': ('fragmento RF S2 (v3) correspondente', 'fragmento RF S2 (v3) correspondiente'), 'sem_chm': ('1 = sem CHM (fora do DSM)', '1 = sin CHM (fuera del DSM)'),
    'area_dentro_imovel_ha': ('área dentro do imóvel (ha)', 'área dentro del inmueble (ha)'), 'fecha': ('data do voo', 'fecha del vuelo'), 'parte': ('remanescente fora APP / APP vegetada (art. 15)', 'remanente fuera APP / APP vegetada (art. 15)'),
    'classe_car': ('classe oficial CAR/SICAR', 'clase oficial CAR/SICAR'), 'rl_exigida_ha': ('RL exigida (ha)', 'RL exigida (ha)'), 'falta_localizar_ha': ('ha que faltavam na v3', 'ha que faltaban en la v3'), 'corredor_ha': ('corredor (ha)', 'corredor (ha)'), 'status': ('status', 'estado'),
    'n': ('número do arroio', 'número del arroyo'), 'posicao': ('norte / central / sul; em cauce_medicoes: posição M3', 'norte / central / sur; en cauce_medicoes: posición M3'), 'fbds_ids': ('ids FBDS 2013', 'ids FBDS 2013'), 'comprimento_dentro_m': ('comprimento dentro da gleba (m)', 'longitud dentro de la gleba (m)'),
    'comprimento_total_fbds_m': ('comprimento total do curso FBDS (m)', 'longitud total del curso FBDS (m)'), 'nasce_dentro': ('1 = nasce na gleba', '1 = nace en la gleba'), 'tipo': ('tipo', 'tipo'), 'represado': ('1 = represado', '1 = represado'), 'arroio': ('arroio', 'arroyo'), 'fonte': ('fonte', 'fuente'),
    'pct_com_dtm_de_solo': ('% do talvegue com DTM de solo', '% del talweg con DTM de suelo'), 'comprimento_m': ('comprimento (m)', 'longitud (m)'), 'comprimento_dentro_gleba_m': ('comprimento dentro da gleba (m)', 'longitud dentro de la gleba (m)'), 'acc_ha_max': ('acumulação máxima (ha, indicador)', 'acumulación máxima (ha, indicador)'),
    'id_secao': ('id da seção', 'id de la sección'), 's_m': ('abscissa ao longo do eixo (m)', 'abscisa a lo largo del eje (m)'), 'pct_com_dado': ('% do perfil com dado', '% del perfil con dato'), 'pct_dosel_centro': ('% sob dossel nos ±6 m centrais', '% bajo dosel en los ±6 m centrales'), 'pct_arboreo_perfil': ('% arbóreo no perfil', '% arbóreo en el perfil'),
    'valida': ('1 = seção válida (DTM de solo)', '1 = sección válida (DTM de suelo)'), 'motivo': ('motivo de invalidez', 'motivo de invalidez'), 'z_fondo_m': ('cota do fundo (DTM, sem valor legal)', 'cota del fondo (DTM, sin valor legal)'), 'largura_h0.5_m': ('largura a fundo + 0,5 m', 'ancho a fondo + 0,5 m'), 'largura_h1.0_m': ('largura a fundo + 1,0 m', 'ancho a fondo + 1,0 m'),
    'largura_quiebre_m': ('largura na ruptura de declive', 'ancho en la ruptura de pendiente'), 'incisao_m': ('incisão (m)', 'incisión (m)'), 'metodo': ('M1_espelho / M2_secao / M3_estimativa', 'M1_espelho / M2_secao / M3_estimativa'), 'cobertura': ('bosque / borda / campo (M2)', 'bosque / borde / campo (M2)'), 'aviso': ('aviso', 'aviso'),
    'largura_m': ('largura do espelho (M1) ou W estimado (M3), m', 'ancho del espejo (M1) o W estimado (M3), m'), 'largura_max_m': ('largura máxima (M1)', 'ancho máximo (M1)'), 'calha_veg_m': ('calha até a vegetação (M1)', 'cauce hasta la vegetación (M1)'), 'qualidade': ('alta / media / estimativa', 'alta / media / estimativa'), 'contexto': ('contexto (artificial etc.)', 'contexto (artificial etc.)'),
    'A_km2': ('área de aporte usada (km²)', 'área de aporte usada (km²)'), 'largura_int_m': ('intervalo de W (M3)', 'intervalo de W (M3)'), 'extrapolacao': ('1 = A fora da faixa da curva', '1 = A fuera del rango de la curva'),
    'id': ('id', 'id'), 'tem_dtm': ('1 = com DTM', '1 = con DTM'), 'aporte_30m_ha_max45m': ('área de aporte (ha, DEM 30 m)', 'área de aporte (ha, DEM 30 m)'), 'chm_media_15m': ('CHM médio em 15 m', 'CHM medio en 15 m'), 'cobertura_arborea_15m_pct': ('% arbóreo em 15 m', '% arbóreo en 15 m'), 'herbacea_15m_pct': ('% herbácea em 15 m', '% herbácea en 15 m'),
    'solo_cultivo_15m_pct': ('% solo/cultivo em 15 m', '% suelo/cultivo en 15 m'), 'higrofila_verde_baixa_15m_pct': ('% várzea (herbácea verde baixa) em 15 m', '% várzea (herbácea verde baja) en 15 m'), 'dist_agua_aberta_m': ('distância à água aberta (m)', 'distancia al agua abierta (m)'), 'relevo_local_ponto_menos_min50m_m': ('relevo local (m)', 'relieve local (m)'),
    'cota_dtm_m_fabdem': ('cota DTM (m, sem valor legal)', 'cota DTM (m, sin valor legal)'), 'veredicto': ('veredito v4', 'veredicto v4'), 'perenidade': ('perenidade: não verificável por imagem', 'perennidad: no verificable por imagen'),
    'corpo': ('corpo d\'água', 'cuerpo de agua'), 'cota_dsm_m': ('cota do espelho (DSM, sem valor legal; nulo na represa)', 'cota del espejo (DSM, sin valor legal; nulo en la represa)'), 'dsm_disponivel': ('1 = com DSM', '1 = con DSM'),
    'subclasse': ('subclasse', 'subclase'), 'nota': ('observação', 'observación'),
}


def carregar(nome, cfg):
    src = cfg['src']
    if src == '__arroios__':
        a = gpd.read_file(os.path.join(ANALISIS, 'gleba_G1_arroios.geojson')); b = gpd.read_file(os.path.join(ANALISIS, 'gleba_G2_arroios.geojson'))
        return gpd.GeoDataFrame(pd.concat([a, b], ignore_index=True), crs=a.crs)
    if src == 'v3_limites':
        g = gpd.read_file(os.path.join(ANALISIS, 'gleba_limites.geojson'))
        g['rl_parcela_ha'] = g['rl_exigida_ha']; g['rl_imovel_ha'] = K['rl_exigida_ha']; g['terra_limpa'] = (g.gleba == 'G2').astype(int)
        return g
    ruta = src if os.path.isabs(src) else os.path.join(ANALISIS, src)
    g = gpd.read_file(ruta + '.geojson')
    for c in g.columns:
        if c != 'geometry' and g[c].dtype == object:
            g[c] = g[c].map(lambda v: '' if v is None else (str(v)[:250]))
    return g


def main():
    os.makedirs(ENTREGA, exist_ok=True)
    log('=' * 78); log('an_18_exportar_v4 -> %s' % ENTREGA); log('=' * 78)
    leiame = ['LEIAME / LÉAME — Fazenda Santo Antônio · Parecer técnico preliminar APP / Reserva Legal v4 (ortofoto de drone 22/05/2026) · Pixadvisor Agricultura de Precisão · 06/09/2026', '=' * 100, '',
              '[PT] Cenário principal: IMÓVEL ÚNICO de %s ha (IN MMA 2/2014 art. 32) com a Gleba 2 (%s ha, os 6 alqueires) comprada como terra limpa. RL exigida %s ha; vegetação nativa computável (ortofoto 0,5 m) %s ha [%s; %s] (conservador %s);' % (f2(K['area_imovel_ha']), f2(K3['area_g2_ha']), f2(K['rl_exigida_ha']), f2(K['veg_computavel_ha']), f2(RL['envolvente_0_5m_ha'][0]), f2(RL['envolvente_0_5m_ha'][1]), f2(K['veg_conservador_ha'])),
              '     déficit %s ha (conservador %s). APP exigível %s ha [%s; %s] do eixo FBDS (borda da calha NÃO medida: dossel fechado); a recompor %s ha (PRA-PR %s). Represa %s ha em 22/05/2026 (>= 1 ha). 2º reservatório %s ha (existe). CAR existente PR-4124301-F127CD1E... averba só %s ha de RL: subsídio à RETIFICAÇÃO.' % (
                  f2(K['deficit_ha']), f2(K['deficit_conservador_ha']), f2(K['app_exigivel_imovel_ha']), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][0]), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][1]), f2(K['app_a_recompor_g1_ha']), f2(K['app_a_recompor_pra_ha']), f3(RP['espelho_22_mai_2026_ha']), f3(RP['reservatorio_cabeceira_arroio2']['area_agua_ha']), f2(K3['car_rl_averbada_ha'])),
              '     Largura dos arroios: <= 10 m PROVÁVEL, sem medição direta (estimativa 5,9 / 2,5 / 6,5 m): protocolo de campo M5 (trena + GNSS; 8/10/8 seções). Voo: ODM 3.7.4, GSD 5 cm, sem GCP (planimetria ±0,1 m; cotas sem valor legal); DSM/DTM só ao norte de N 7.401.711.',
              '     Sistema de referência: SIRGAS 2000 geográfico (EPSG:4674), datum do CAR (IN MMA 2/2014 art. 11 §2º); áreas (ha) e comprimentos (m) calculados em SIRGAS 2000 / UTM 22S (EPSG:31982, idêntico ao 32722 da ortofoto).',
              '     Formatos: .geojson, .shp (+shx/dbf/prj/cpg, UTF-8, campos até 10 caracteres), .kml (WGS 84). PARECER PRELIMINAR: não substitui laudo; borda da calha, nascente, estágio sucessional e limite da Gleba 2 exigem campo/escritura.',
              '[ES] Escenario principal: INMUEBLE ÚNICO de %s ha (IN MMA 2/2014 art. 32) con la Gleba 2 (%s ha, los 6 alqueires) comprada como tierra limpia. RL exigida %s ha; vegetación nativa computable (ortofoto 0,5 m) %s ha [%s; %s] (conservador %s);' % (f2(K['area_imovel_ha']), f2(K3['area_g2_ha']), f2(K['rl_exigida_ha']), f2(K['veg_computavel_ha']), f2(RL['envolvente_0_5m_ha'][0]), f2(RL['envolvente_0_5m_ha'][1]), f2(K['veg_conservador_ha'])),
              '     déficit %s ha (conservador %s). APP exigible %s ha [%s; %s] desde el eje FBDS (borde del cauce NO medido: dosel cerrado); a recomponer %s ha (PRA-PR %s). Represa %s ha el 22/05/2026 (>= 1 ha). 2º reservorio %s ha (existe). El CAR existente PR-4124301-F127CD1E... inscribe solo %s ha de RL: insumo para la RECTIFICACIÓN.' % (
                  f2(K['deficit_ha']), f2(K['deficit_conservador_ha']), f2(K['app_exigivel_imovel_ha']), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][0]), f2(D['app']['fbds']['IMOVEL']['envolvente_borda_0_5m_ha'][1]), f2(K['app_a_recompor_g1_ha']), f2(K['app_a_recompor_pra_ha']), f3(RP['espelho_22_mai_2026_ha']), f3(RP['reservatorio_cabeceira_arroio2']['area_agua_ha']), f2(K3['car_rl_averbada_ha'])),
              '     Ancho de los arroyos: <= 10 m PROBABLE, sin medición directa (estimación 5,9 / 2,5 / 6,5 m): protocolo de campo M5 (cinta + GNSS; 8/10/8 secciones). Vuelo: ODM 3.7.4, GSD 5 cm, sin GCP (planimetría ±0,1 m; cotas sin valor legal); DSM/DTM solo al norte de N 7.401.711.',
              '     Sistema de referencia: SIRGAS 2000 geográfico (EPSG:4674), datum del CAR (IN MMA 2/2014 art. 11 §2º); áreas (ha) y longitudes (m) calculadas en SIRGAS 2000 / UTM 22S (EPSG:31982, idéntico al 32722 de la ortofoto).',
              '     Formatos: .geojson, .shp (+shx/dbf/prj/cpg, UTF-8, campos de hasta 10 caracteres), .kml (WGS 84). INFORME PRELIMINAR: no sustituye un informe pericial; borde del cauce, naciente, estadio sucesional y límite de la Gleba 2 exigen campo/escritura.', '']
    for nome, cfg in CAPAS.items():
        g = carregar(nome, cfg)
        if g.crs is None:
            g = g.set_crs(CRS_METRICO)
        cols = [c for c in cfg['shp'] if c in g.columns]
        g = limpiar(g[cols + ['geometry']]).to_crs(CRS_CAR)
        for ext in ('geojson', 'shp', 'shx', 'dbf', 'prj', 'cpg', 'kml'):
            p = os.path.join(ENTREGA, nome + '.' + ext)
            if os.path.exists(p):
                os.remove(p)
        g.to_file(os.path.join(ENTREGA, nome + '.geojson'), driver='GeoJSON')
        gs = g.rename(columns={c: cfg['shp'][c] for c in cols})
        assert all(len(c) <= 10 for c in gs.columns if c != 'geometry'), (nome, list(gs.columns))
        gs.to_file(os.path.join(ENTREGA, nome + '.shp'), driver='ESRI Shapefile', encoding='utf-8')
        kml(g, os.path.join(ENTREGA, nome + '.kml'), nome, cfg['pt'], cols)
        chk = gpd.read_file(os.path.join(ENTREGA, nome + '.shp'))
        assert len(chk) == len(g) and chk.crs.to_epsg() == 4674, nome
        area = (' · soma area_ha = %.3f' % g['area_ha'].astype(float).sum()) if ('area_ha' in g.columns and g.geom_type.iloc[0].endswith('Polygon')) else ''
        log('  %-30s %3d feats · %-12s -> geojson + shp + kml (EPSG:4674)%s' % (nome, len(g), g.geom_type.iloc[0], area))
        leiame += ['-' * 100, '%s  (%s, %d feições / entidades)' % (nome, g.geom_type.iloc[0], len(g)), '  [PT] ' + cfg['pt'], '  [ES] ' + cfg['es'], '  Campos (GeoJSON/KML -> Shapefile):']
        for c in cols:
            d = CAMPOS.get(c, (c, c))
            leiame.append('    %-34s -> %-10s  [PT] %s' % (c, cfg['shp'][c], d[0]))
            leiame.append('    %-34s    %-10s  [ES] %s' % ('', '', d[1]))
        leiame.append('')
    leiame += ['-' * 100, 'Rasters (05_ORTOFOTO, EPSG:31982, não incluídos no zip pelo tamanho): ortofoto_rgba_0_25m/0_50m.tif, dsm/dtm/dtm_hibrido 0,25/0,5 m, chm_hibrido, dtm_hillshade, vegetacao_ortofoto_0_50m.tif (legenda nas tags), dtm_fonte (1 = solo; 2 = dossel não penetrado).',
               'Contato / Contacto: Eng. Agr. Nilton Camargo · Diretor Técnico · Pixadvisor Agricultura de Precisão', 'nilton.camargo@pixadvisor.network · +591 721 49171']
    with open(os.path.join(ENTREGA, 'LEIAME.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(leiame))
    z = os.path.join(ENTREGA, 'Fazenda_Santo_Antonio_vetores_v4_EPSG4674.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(ENTREGA)):
            if not f.endswith('.zip'):
                zf.write(os.path.join(ENTREGA, f), f)
    log('  -> LEIAME.txt + %s' % z)
    log('an_18 listo')


if __name__ == '__main__':
    main()
