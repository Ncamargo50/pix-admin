# -*- coding: utf-8 -*-
"""an_15_exportar_v3 — vetores de entrega da v3 (cliente / retificacao do CAR).

    python an_15_exportar_v3.py   -> 04_VETORES_ENTREGA_V3/

Para cada capa: GeoJSON (EPSG:4674, datum do CAR), Shapefile (EPSG:4674, campos <= 10 caracteres, UTF-8) e KML (WGS 84).
Mais LEIAME.txt bilingue e um zip. Nada se recalcula: os atributos sao os de 02_ANALISIS (an_07, an_11, an_12).
Reutiliza kml() e limpiar() de an_06_exportar.
"""
import os
import sys
import zipfile

import geopandas as gpd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, CRS_METRICO, leer_json, log  # noqa: E402
from an_06_exportar import kml, limpiar                                    # noqa: E402

ENTREGA = os.path.join(PROYECTO, '04_VETORES_ENTREGA_V3')
HP = os.path.join(ANALISIS, 'hidrologia_pro')
CRS_CAR = 'EPSG:4674'

D = leer_json(os.path.join(ANALISIS, 'resultados_v3.json'))
K = D['kpi']; RL = D['reserva_legal']
f2 = lambda x: ('%.2f' % x).replace('.', ',')

CAPAS = {
    'v3_limites': dict(src='gleba_limites', shp={'gleba': 'gleba', 'nome': 'nome', 'area_ha': 'area_ha', 'alqueires': 'alqueires', 'rl_parcela_ha': 'rl_parc_ha', 'rl_imovel_ha': 'rl_imov_ha', 'terra_limpa': 'terra_limp'},
                       pt='As duas glebas do imóvel único (G1 %s ha; G2 %s ha = %s alqueires, comprada como terra limpa); RL do imóvel = 20%% de %s ha = %s ha (parcela por gleba só como inventário)' % (f2(K['area_g1_ha']), f2(K['area_g2_ha']), f2(K['g2_alqueires']), f2(K['area_imovel_ha']), f2(K['rl_exigida_ha'])),
                       es='Las dos glebas del inmueble único (G1 %s ha; G2 %s ha = %s alqueires, comprada como tierra limpia); RL del inmueble = 20%% de %s ha = %s ha (parcela por gleba solo como inventario)' % (f2(K['area_g1_ha']), f2(K['area_g2_ha']), f2(K['g2_alqueires']), f2(K['area_imovel_ha']), f2(K['rl_exigida_ha']))),
    'v3_CAR_existente': dict(src='v3_CAR_existente', shp={'capa': 'capa', 'cod_tema': 'cod_tema', 'cod_imovel': 'cod_imovel', 'relacao': 'relacao', 'ind_status': 'status', 'des_condic': 'condicao', 'num_area_decl': 'num_area', 'area_geom_ha': 'geom_ha', 'area_no_imovel_ha': 'no_imov_ha'},
                             pt='CAR existente PR-4124301-F127CD1E... (próprio, %s ha, "%s") e CAR de origem da Gleba 2 PR-4124301-5223911747...: área do imóvel, APP, RL averbada/proposta, vegetação nativa, consolidada, hidrografia (réplica IAT do SICAR, 06/09/2026)' % (f2(K['car_area_ha']), D['car_existente']['condicao']),
                             es='CAR existente PR-4124301-F127CD1E... (propio, %s ha, "%s") y CAR de origen de la Gleba 2 PR-4124301-5223911747...: área del inmueble, APP, RL inscrita/propuesta, vegetación nativa, consolidada, hidrografía (réplica IAT del SICAR, 06/09/2026)' % (f2(K['car_area_ha']), D['car_existente']['condicao'])),
    'v3_APP_G1': dict(src='gleba_G1_app', shp={'gleba': 'gleba', 'feicao': 'feicao', 'situacao': 'situacao', 'cenario': 'cenario', 'pra_pr_recompor': 'pra_recomp', 'area_ha': 'area_ha'},
                      pt='APP da Gleba 1 (referência FBDS: %s ha; envolvente [%s; %s]) por feição (curso / nascente / faixa da represa) e situação (conforme / a recompor / água); cenario = base ou fbds_iat_adicional (faixa de 30 m da represa, SE o IAT a aplicar, NÃO somada); pra_pr_recompor = 1 onde a faixa do PRA-PR (20 m / 15 m) ainda exige recompor' % (f2(K['app_g1_ha']), f2(K['app_g1_envolvente_ha'][0]), f2(K['app_g1_envolvente_ha'][1])),
                      es='APP de la Gleba 1 (referencia FBDS: %s ha; envolvente [%s; %s]) por rasgo (curso / naciente / faja de la represa) y situación (conforme / a recomponer / agua); cenario = base o fbds_iat_adicional (faja de 30 m de la represa, SI el IAT la aplica, NO sumada); pra_pr_recompor = 1 donde la faja del PRA-PR (20 m / 15 m) aún exige recomponer' % (f2(K['app_g1_ha']), f2(K['app_g1_envolvente_ha'][0]), f2(K['app_g1_envolvente_ha'][1]))),
    'v3_APP_G2': dict(src='gleba_G2_app', shp={'gleba': 'gleba', 'feicao': 'feicao', 'situacao': 'situacao', 'cenario': 'cenario', 'pra_pr_recompor': 'pra_recomp', 'area_ha': 'area_ha'},
                      pt='APP da Gleba 2 (%s ha [%s; %s], 33 m do Arroio 1 na ponta norte, com vegetação): passa a 0 se o limite da ponta norte for corrigido' % (f2(K['app_g2_ha']), f2(K['app_g2_envolvente_ha'][0]), f2(K['app_g2_envolvente_ha'][1])),
                      es='APP de la Gleba 2 (%s ha [%s; %s], 33 m del Arroyo 1 en la punta norte, con vegetación): pasa a 0 si se corrige el límite de la punta norte' % (f2(K['app_g2_ha']), f2(K['app_g2_envolvente_ha'][0]), f2(K['app_g2_envolvente_ha'][1]))),
    'v3_APP_envolvente': dict(src='__app_env__', shp={'gleba': 'gleba', 'base': 'base', 'area_ha': 'area_ha'},
                              pt='APP de 30 m / 50 m pelo eixo FBDS e pela mediana do conjunto de 5 DEM (GLO30, NASADEM, SRTMGL1, AW3D30, FABDEM): envolvente [%s; %s] ha no imóvel; o Arroio 1 tem desvio sistemático de 29 m (levantar com GNSS)' % (f2(K['app_envolvente_imovel_ha'][0]), f2(K['app_envolvente_imovel_ha'][1])),
                              es='APP de 30 m / 50 m por el eje FBDS y por la mediana del ensamble de 5 DEM (GLO30, NASADEM, SRTMGL1, AW3D30, FABDEM): envolvente [%s; %s] ha en el inmueble; el Arroyo 1 tiene un sesgo sistemático de 29 m (levantar con GNSS)' % (f2(K['app_envolvente_imovel_ha'][0]), f2(K['app_envolvente_imovel_ha'][1]))),
    'v3_vegetacao_computavel': dict(src='v3_vegetacao_computavel', shp={'gleba': 'gleba', 'classe': 'classe', 'area_ha': 'area_ha', 'rl_exigida_ha': 'rl_exig_ha', 'veg_computavel_ha': 'veg_comp', 'deficit_ha': 'deficit_ha', 'deficit_conservador_ha': 'defic_cons', 'frag13_regeneracao': 'frag13'},
                                    pt='Vegetação nativa computável para a RL (art. 12 + art. 15): remanescente fora da APP + APP vegetada = %s ha na Gleba 1 (imóvel único: exigida %s, déficit %s; conservador sem o fragmento 13: %s / déficit %s). NÃO é "RL existente": a RL só existe quando localizada e aprovada pelo IAT' % (f2(K['veg_computavel_ha']), f2(K['rl_exigida_ha']), f2(K['deficit_ha']), f2(K['veg_conservador_ha']), f2(K['deficit_conservador_ha'])),
                                    es='Vegetación nativa computable para la RL (art. 12 + art. 15): remanente fuera de la APP + APP vegetada = %s ha en la Gleba 1 (inmueble único: exigida %s, déficit %s; conservador sin el fragmento 13: %s / déficit %s). NO es "RL existente": la RL solo existe cuando está localizada y aprobada por el IAT' % (f2(K['veg_computavel_ha']), f2(K['rl_exigida_ha']), f2(K['deficit_ha']), f2(K['veg_conservador_ha']), f2(K['deficit_conservador_ha']))),
    'v3_fragmentos': dict(src='v3_fragmentos', shp={'gleba': 'gleba', 'frag_id': 'frag_id', 'area_dentro_ha': 'area_in_ha', 'area_total_ha': 'area_tot', 'persistencia': 'persist', 'leitura_v3': 'leitura'},
                          pt='Fragmentos de floresta nativa (RF 2026): 2 (parte de fragmento contínuo, IAT prioridade A), 13 (regeneração arbórea sem histórico 2008/2013, a confirmar em campo), 30 (idem); ponta norte da G2 não computada',
                          es='Fragmentos de bosque nativo (RF 2026): 2 (parte de fragmento continuo, IAT prioridad A), 13 (regeneración arbórea sin historial 2008/2013, a confirmar en campo), 30 (ídem); punta norte de G2 no computada'),
    'v3_RL_proposta': dict(src='v3_RL_proposta', shp={'classe_car': 'classe_car', 'area_ha': 'area_ha', 'rl_exigida_ha': 'rl_exig_ha', 'falta_localizar_ha': 'falta_ha', 'corredor_ha': 'corredor', 'status': 'status'},
                           pt='Reserva Legal Proposta recortada à Gleba 1: %s ha (faltam %s ha para %s): ampliar o corredor junto ao fragmento IAT prioridade A ou compensar (art. 66 III); APP a recompor incluída só computa após art. 15 II; sujeita ao IAT (art. 14)' % (f2(RL['localizacao_proposta']['rl_proposta_recortada_g1_ha']), f2(RL['localizacao_proposta']['falta_para_exigida_ha']), f2(K['rl_exigida_ha'])),
                           es='Reserva Legal Propuesta recortada a la Gleba 1: %s ha (faltan %s ha para %s): ampliar el corredor junto al fragmento IAT prioridad A o compensar (art. 66 III); la APP a recomponer incluida solo computa tras el art. 15 II; sujeta al IAT (art. 14)' % (f2(RL['localizacao_proposta']['rl_proposta_recortada_g1_ha']), f2(RL['localizacao_proposta']['falta_para_exigida_ha']), f2(K['rl_exigida_ha']))),
    'v3_IAT_fragmento_prioritario': dict(src='v3_IAT_fragmento_prioritario', shp={'fragmento': 'fragmento', 'area_total_ha': 'area_tot', 'idade_anos': 'idade', 'prioridade': 'priorid', 'fito': 'fito', 'dentro_ha': 'dentro_ha', 'em_G1_ha': 'g1_ha', 'em_G2_ha': 'g2_ha', 'coincide_com_floresta_rf_G1_ha': 'rf_g1_ha'},
                                         pt='Fragmentos florestais prioritários do IAT-PR recortados ao imóvel (163756: prioridade A, 23 anos, 7,07 ha no imóvel): âncora natural da Reserva Legal',
                                         es='Fragmentos forestales prioritarios del IAT-PR recortados al inmueble (163756: prioridad A, 23 años, 7,07 ha en el inmueble): ancla natural de la Reserva Legal'),
    'v3_arroios_G1': dict(src='gleba_G1_arroios', shp={'gleba': 'gleba', 'n': 'n', 'nome': 'nome', 'posicao': 'posicao', 'fbds_ids': 'fbds_ids', 'comprimento_dentro_m': 'comp_in_m', 'comprimento_total_fbds_m': 'comp_tot_m', 'nasce_dentro': 'nasce_in', 'nascente_fbds_id': 'nasc_id', 'tipo': 'tipo', 'represado': 'represado'},
                          pt='Arroios da Gleba 1 (eixo FBDS 2013): 1 norte (523 m), 2 central (951 m, nasce na gleba), 3 sul = Ribeirão do Salto (564 m, represado); largura até 10 m; regime NÃO verificado (BC250 não discrimina)',
                          es='Arroyos de la Gleba 1 (eje FBDS 2013): 1 norte (523 m), 2 central (951 m, nace en la gleba), 3 sur = Ribeirão do Salto (564 m, represado); ancho hasta 10 m; régimen NO verificado (BC250 no discrimina)'),
    'v3_arroios_G2': dict(src='gleba_G2_arroios', shp={'gleba': 'gleba', 'n': 'n', 'nome': 'nome', 'posicao': 'posicao', 'fbds_ids': 'fbds_ids', 'comprimento_dentro_m': 'comp_in_m', 'comprimento_total_fbds_m': 'comp_tot_m', 'nasce_dentro': 'nasce_in', 'tipo': 'tipo', 'represado': 'represado'},
                          pt='Arroio 1 na Gleba 2 (33 m na ponta norte; limite a conferir)', es='Arroyo 1 en la Gleba 2 (33 m en la punta norte; límite a verificar)'),
    'v3_arroio1_ensamble_DEM': dict(src='__ens__', shp={'gleba': 'gleba', 'arroio': 'arroio', 'tipo': 'tipo'},
                                    pt='Mediana do conjunto de 5 DEM por arroio (envolvente do eixo FBDS); no Arroio 1 fica a 29 m (mediana) / 55 m (P90) do eixo FBDS, todos os DEM para o mesmo lado',
                                    es='Mediana del ensamble de 5 DEM por arroyo (envolvente del eje FBDS); en el Arroyo 1 queda a 29 m (mediana) / 55 m (P90) del eje FBDS, todos los DEM hacia el mismo lado'),
    'v3_nascentes': dict(src='v3_nascentes', shp={'fonte': 'fonte', 'id': 'id', 'gleba': 'gleba', 'veredicto_v3': 'veredito', 'hand_m': 'hand_m', 'dist_inicio_trecho_otto2020_m': 'd_otto_m', 'n_dem_con_cabecera_a_100m': 'n_dem100', 's2_freq_chuva_max_30m': 's2_chuva', 's1_freq20_max_30m': 's1_f20', 'ndmi_p10_seca_z_robusto': 'ndmi_z', 'uso_iat_2012_wv2': 'uso_2012'},
                         pt='Nascentes com veredito: FBDS 306158 PROVÁVEL (APP de 50 m aplicada; perenidade NÃO verificada), dem_1 = mesma cabeceira (não soma), dem_2 (em soja) POUCO PROVÁVEL (0 água em 338 cenas S2 + 43 S1; nota topográfica)',
                         es='Nacientes con veredicto: FBDS 306158 PROBABLE (APP de 50 m aplicada; perennidad NO verificada), dem_1 = misma cabecera (no suma), dem_2 (en soja) POCO PROBABLE (0 agua en 338 escenas S2 + 43 S1; nota topográfica)'),
    'v3_represa_espelhos': dict(src='v3_represa_espelhos', shp={'fuente': 'fonte', 'area_ha': 'area_ha'},
                                pt='Espelho da represa (Arroio 3) por fonte: S2 mediana chuvosa 2024-26 0,83 ha (referência), S2 extensão máxima 1,12, S1 1,16, MapBiomas 2024 1,08, JRC máx. 1,71, FBDS 2013 1,95, CAR 2,12; >= 1 ha INDETERMINADO, sem presumir a dispensa do art. 4º §4º',
                                es='Espejo de la represa (Arroyo 3) por fuente: S2 mediana lluviosa 2024-26 0,83 ha (referencia), S2 extensión máxima 1,12, S1 1,16, MapBiomas 2024 1,08, JRC máx. 1,71, FBDS 2013 1,95, CAR 2,12; >= 1 ha INDETERMINADO, sin presumir la dispensa del art. 4º §4º'),
    'v3_outorga_sigarh': dict(src='v3_outorga_sigarh', shp={'nm_empreendimento': 'empreend', 'nm_tipo_interferencia': 'interfer', 'nr_portaria': 'portaria', 'st_portaria': 'status', 'nm_tipo_documento': 'tipo_doc', 'desc_finalidades': 'finalid', 'nm_corpo_hidrico_complemento': 'corpo_hid', 'dt_publicacao': 'dt_publ', 'dt_vencimento': 'dt_venc', 'vencida': 'vencida', 'leitura': 'leitura'},
                              pt='Outorga SIGARH da barragem (Ribeirão do Salto): portaria 26039/2023/OP-GOUT, prévia, status IRREGULAR, vencida em 08/11/2025 — regularizar junto com o CAR',
                              es='Concesión SIGARH de la represa (Ribeirão do Salto): portaria 26039/2023/OP-GOUT, previa, estado IRREGULAR, vencida el 08/11/2025 — regularizar junto con el CAR'),
    'v3_mapa_CAR_G1': dict(src='gleba_G1_car', shp={'gleba': 'gleba', 'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao', 'area_ha': 'area_ha', 'nota': 'nota'},
                           pt='Uso e cobertura da Gleba 1 com a nomenclatura do Módulo de Cadastro do SICAR (fecha em 144,21 ha); "perene" = nomenclatura, perenidade não verificada; camada a conferir pelo responsável pela inscrição',
                           es='Uso y cobertura de la Gleba 1 con la nomenclatura del Módulo de Catastro del SICAR (cierra en 144,21 ha); "perene" = nomenclatura, perennidad no verificada; capa a verificar por el responsable de la inscripción'),
    'v3_mapa_CAR_G2': dict(src='gleba_G2_car', shp={'gleba': 'gleba', 'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao', 'area_ha': 'area_ha', 'nota': 'nota'},
                           pt='Uso e cobertura da Gleba 2 (fecha em 13,54 ha); o remanescente e a APP da ponta norte só valem se o limite for confirmado', es='Uso y cobertura de la Gleba 2 (cierra en 13,54 ha); el remanente y la APP de la punta norte solo valen si se confirma el límite'),
    'v3_G2_ponta_norte': dict(src='v3_G2_ponta_norte', shp={'gleba': 'gleba', 'floresta_ha': 'flor_ha', 'status': 'status'},
                              pt='Ponta norte da Gleba 2: 2,68 ha de floresta (fragmento 2) NÃO computada — o cliente afirma ter comprado terra limpa; limite a conferir com a escritura/SIGEF',
                              es='Punta norte de la Gleba 2: 2,68 ha de bosque (fragmento 2) NO computado — el cliente afirma haber comprado tierra limpia; límite a verificar con la escritura/SIGEF'),
}
CAMPOS = {
    'gleba': ('G1 = imóvel principal; G2 = os 6 alqueires', 'G1 = inmueble principal; G2 = los 6 alqueires'), 'nome': ('nome', 'nombre'),
    'area_ha': ('área em hectares (EPSG:31982)', 'área en hectáreas (EPSG:31982)'), 'alqueires': ('alqueires paulistas (2,42 ha)', 'alqueires paulistas (2,42 ha)'),
    'rl_parcela_ha': ('parcela da RL (20% da gleba) — só inventário', 'parcela de la RL (20% de la gleba) — solo inventario'), 'rl_imovel_ha': ('RL exigida do imóvel único', 'RL exigida del inmueble único'),
    'terra_limpa': ('1 = comprada como terra limpa (0 ha de vegetação computável)', '1 = comprada como tierra limpia (0 ha de vegetación computable)'),
    'capa': ('camada CAR', 'capa CAR'), 'cod_tema': ('tema SICAR', 'tema SICAR'), 'cod_imovel': ('código do imóvel no CAR', 'código del inmueble en el CAR'), 'relacao': ('propio_G1 / cubre_G2', 'propio_G1 / cubre_G2'),
    'ind_status': ('status do CAR', 'estado del CAR'), 'des_condic': ('condição da análise', 'condición del análisis'), 'num_area_decl': ('área declarada (ha)', 'área declarada (ha)'),
    'area_geom_ha': ('área da geometria (ha)', 'área de la geometría (ha)'), 'area_no_imovel_ha': ('área dentro do imóvel (ha)', 'área dentro del inmueble (ha)'),
    'feicao': ('curso / nascente / reservatorio faixa 30 m', 'curso / naciente / reservatorio faixa 30 m'), 'situacao': ('situação (RF 2026)', 'situación (RF 2026)'),
    'cenario': ('base (exigível) ou fbds_iat_adicional (sensibilidade, não somado)', 'base (exigible) o fbds_iat_adicional (sensibilidad, no sumado)'),
    'pra_pr_recompor': ('1 = ainda a recompor pela faixa do PRA-PR', '1 = aún a recomponer por la faja del PRA-PR'), 'base': ('FBDS ou mediana_ensamble_5dem', 'FBDS o mediana_ensamble_5dem'),
    'classe': ('classe', 'clase'), 'rl_exigida_ha': ('RL exigida do imóvel (ha)', 'RL exigida del inmueble (ha)'), 'veg_computavel_ha': ('vegetação computável (ha)', 'vegetación computable (ha)'),
    'deficit_ha': ('déficit principal (ha)', 'déficit principal (ha)'), 'deficit_conservador_ha': ('déficit conservador, sem o fragmento 13 (ha)', 'déficit conservador, sin el fragmento 13 (ha)'),
    'frag13_regeneracao': ('1 = polígono do fragmento 13 (regeneração a confirmar)', '1 = polígono del fragmento 13 (regeneración a confirmar)'),
    'frag_id': ('id do fragmento', 'id del fragmento'), 'area_dentro_ha': ('área dentro da gleba (ha)', 'área dentro de la gleba (ha)'), 'area_total_ha': ('área total do fragmento (ha)', 'área total del fragmento (ha)'),
    'persistencia': ('histórico MapBiomas 1985/2008', 'histórico MapBiomas 1985/2008'), 'leitura_v3': ('leitura da v3', 'lectura de la v3'),
    'classe_car': ('classe oficial CAR/SICAR', 'clase oficial CAR/SICAR'), 'falta_localizar_ha': ('ha que faltam para a RL exigida', 'ha que faltan para la RL exigida'), 'corredor_ha': ('corredor de recomposição (ha)', 'corredor de recomposición (ha)'),
    'status': ('status', 'estado'), 'fragmento': ('id do fragmento IAT', 'id del fragmento IAT'), 'idade_anos': ('idade (anos, IAT)', 'edad (años, IAT)'), 'prioridade': ('prioridade IAT', 'prioridad IAT'), 'fito': ('fitofisionomia', 'fitofisionomía'),
    'dentro_ha': ('ha dentro do imóvel', 'ha dentro del inmueble'), 'em_G1_ha': ('ha na G1', 'ha en G1'), 'em_G2_ha': ('ha na G2', 'ha en G2'), 'coincide_com_floresta_rf_G1_ha': ('ha que coincidem com a floresta RF na G1', 'ha que coinciden con el bosque RF en G1'),
    'n': ('número do arroio', 'número del arroyo'), 'posicao': ('norte / central / sul', 'norte / central / sur'), 'fbds_ids': ('ids FBDS 2013', 'ids FBDS 2013'), 'comprimento_dentro_m': ('comprimento dentro da gleba (m)', 'longitud dentro de la gleba (m)'),
    'comprimento_total_fbds_m': ('comprimento total do curso FBDS (m)', 'longitud total del curso FBDS (m)'), 'nasce_dentro': ('1 = nasce na gleba', '1 = nace en la gleba'), 'nascente_fbds_id': ('id da nascente FBDS', 'id de la naciente FBDS'),
    'tipo': ('atravessa / nasce na gleba', 'atraviesa / nace en la gleba'), 'represado': ('1 = represado', '1 = represado'), 'arroio': ('arroio', 'arroyo'),
    'fonte': ('fonte', 'fuente'), 'id': ('id', 'id'), 'veredicto_v3': ('veredito v3', 'veredicto v3'), 'hand_m': ('HAND (m)', 'HAND (m)'), 'dist_inicio_trecho_otto2020_m': ('distância ao início de trecho otto (m)', 'distancia al inicio de tramo otto (m)'),
    'n_dem_con_cabecera_a_100m': ('DEM (de 5) com cabeceira a < 100 m', 'DEM (de 5) con cabecera a < 100 m'), 's2_freq_chuva_max_30m': ('freq. de água S2 chuvosa (máx. 30 m)', 'frec. de agua S2 lluviosa (máx. 30 m)'),
    's1_freq20_max_30m': ('freq. S1 VV < -20 dB (máx. 30 m)', 'frec. S1 VV < -20 dB (máx. 30 m)'), 'ndmi_p10_seca_z_robusto': ('NDMI seco z vs entorno', 'NDMI seco z vs entorno'), 'uso_iat_2012_wv2': ('uso IAT 2012 (WorldView-2)', 'uso IAT 2012 (WorldView-2)'),
    'fuente': ('fonte / métrica do espelho', 'fuente / métrica del espejo'),
    'nm_empreendimento': ('empreendimento', 'emprendimiento'), 'nm_tipo_interferencia': ('interferência', 'interferencia'), 'nr_portaria': ('portaria', 'portaria'), 'st_portaria': ('status', 'estado'), 'nm_tipo_documento': ('tipo de documento', 'tipo de documento'),
    'desc_finalidades': ('finalidades', 'finalidades'), 'nm_corpo_hidrico_complemento': ('corpo hídrico', 'cuerpo hídrico'), 'dt_publicacao': ('publicação', 'publicación'), 'dt_vencimento': ('vencimento', 'vencimiento'), 'vencida': ('1 = vencida', '1 = vencida'), 'leitura': ('leitura', 'lectura'),
    'subclasse': ('subclasse', 'subclase'), 'nota': ('observação técnica', 'observación técnica'), 'floresta_ha': ('floresta RF na ponta norte (ha)', 'bosque RF en la punta norte (ha)'),
}


def carregar(nome, cfg):
    src = cfg['src']
    if src == '__app_env__':
        a = gpd.read_file(os.path.join(HP, 'app_G1_fbds_vs_ensamble.geojson')); b = gpd.read_file(os.path.join(HP, 'app_G2_fbds_vs_ensamble.geojson'))
        import pandas as pd
        return gpd.GeoDataFrame(pd.concat([a, b], ignore_index=True), crs=a.crs)
    if src == '__ens__':
        e = gpd.read_file(os.path.join(HP, 'hidro_ensamble_mediana_por_arroio.geojson'))
        return e[e.tipo == 'mediana_ensamble'].copy()
    g = gpd.read_file(os.path.join(ANALISIS, src + '.geojson'))
    if nome == 'v3_limites':
        g['rl_parcela_ha'] = g['rl_exigida_ha']; g['rl_imovel_ha'] = K['rl_exigida_ha']; g['terra_limpa'] = (g.gleba == 'G2').astype(int)
    return g


def main():
    os.makedirs(ENTREGA, exist_ok=True)
    log('=' * 78); log('an_15_exportar_v3 -> %s' % ENTREGA); log('=' * 78)
    leiame = ['LEIAME / LÉAME — Fazenda Santo Antônio · Parecer técnico preliminar APP / Reserva Legal v3 · Pixadvisor Agricultura de Precisão · 06/09/2026', '=' * 100, '',
              '[PT] Cenário principal: IMÓVEL ÚNICO de %s ha (IN MMA 2/2014 art. 32) com a Gleba 2 (%s ha, os 6 alqueires) comprada como terra limpa. RL exigida %s ha; vegetação computável %s ha (conservador %s);' % (f2(K['area_imovel_ha']), f2(K['area_g2_ha']), f2(K['rl_exigida_ha']), f2(K['veg_computavel_ha']), f2(K['veg_conservador_ha'])),
              '     déficit %s ha (conservador %s). APP exigível %s ha [%s; %s]; a recompor %s ha (PRA-PR %s). CAR existente PR-4124301-F127CD1E... averba só %s ha de RL: subsídio à RETIFICAÇÃO.' % (f2(K['deficit_ha']), f2(K['deficit_conservador_ha']), f2(K['app_exigivel_imovel_ha']), f2(K['app_envolvente_imovel_ha'][0]), f2(K['app_envolvente_imovel_ha'][1]), f2(K['app_a_recompor_ha']), f2(K['app_a_recompor_pra_ha']), f2(K['car_rl_averbada_ha'])),
              '     Sistema de referência: SIRGAS 2000 geográfico (EPSG:4674), datum do CAR (IN MMA 2/2014 art. 11 §2º); áreas (ha) e comprimentos (m) calculados em SIRGAS 2000 / UTM 22S (EPSG:31982).',
              '     Formatos: .geojson, .shp (+shx/dbf/prj/cpg, UTF-8, campos até 10 caracteres), .kml (WGS 84). PARECER PRELIMINAR por satélite: não substitui laudo; leito, nascentes, limite da Gleba 2 e estágio sucessional exigem campo/escritura.',
              '[ES] Escenario principal: INMUEBLE ÚNICO de %s ha (IN MMA 2/2014 art. 32) con la Gleba 2 (%s ha, los 6 alqueires) comprada como tierra limpia. RL exigida %s ha; vegetación computable %s ha (conservador %s);' % (f2(K['area_imovel_ha']), f2(K['area_g2_ha']), f2(K['rl_exigida_ha']), f2(K['veg_computavel_ha']), f2(K['veg_conservador_ha'])),
              '     déficit %s ha (conservador %s). APP exigible %s ha [%s; %s]; a recomponer %s ha (PRA-PR %s). El CAR existente PR-4124301-F127CD1E... inscribe solo %s ha de RL: insumo para la RECTIFICACIÓN.' % (f2(K['deficit_ha']), f2(K['deficit_conservador_ha']), f2(K['app_exigivel_imovel_ha']), f2(K['app_envolvente_imovel_ha'][0]), f2(K['app_envolvente_imovel_ha'][1]), f2(K['app_a_recompor_ha']), f2(K['app_a_recompor_pra_ha']), f2(K['car_rl_averbada_ha'])),
              '     Sistema de referencia: SIRGAS 2000 geográfico (EPSG:4674), datum del CAR (IN MMA 2/2014 art. 11 §2º); áreas (ha) y longitudes (m) calculadas en SIRGAS 2000 / UTM 22S (EPSG:31982).',
              '     Formatos: .geojson, .shp (+shx/dbf/prj/cpg, UTF-8, campos de hasta 10 caracteres), .kml (WGS 84). INFORME PRELIMINAR por satélite: no sustituye un informe pericial; cauce, nacientes, límite de la Gleba 2 y estadio sucesional exigen campo/escritura.', '']
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
        area = (' · soma area_ha = %.2f' % g['area_ha'].astype(float).sum()) if ('area_ha' in g.columns and g.geom_type.iloc[0].endswith('Polygon')) else ''
        log('  %-30s %2d feats · %-12s -> geojson + shp + kml (EPSG:4674)%s' % (nome, len(g), g.geom_type.iloc[0], area))
        leiame += ['-' * 100, '%s  (%s, %d feições / entidades)' % (nome, g.geom_type.iloc[0], len(g)), '  [PT] ' + cfg['pt'], '  [ES] ' + cfg['es'], '  Campos (GeoJSON/KML -> Shapefile):']
        for c in cols:
            d = CAMPOS.get(c, (c, c))
            leiame.append('    %-32s -> %-10s  [PT] %s' % (c, cfg['shp'][c], d[0]))
            leiame.append('    %-32s    %-10s  [ES] %s' % ('', '', d[1]))
        leiame.append('')
    leiame += ['-' * 100, 'Contato / Contacto: Eng. Agr. Nilton Camargo · Diretor Técnico · Pixadvisor Agricultura de Precisão', 'nilton.camargo@pixadvisor.network · +591 721 49171']
    with open(os.path.join(ENTREGA, 'LEIAME.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(leiame))
    z = os.path.join(ENTREGA, 'Fazenda_Santo_Antonio_vetores_v3_EPSG4674.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(ENTREGA)):
            if not f.endswith('.zip'):
                zf.write(os.path.join(ENTREGA, f), f)
    log('  -> LEIAME.txt + %s' % z)
    log('an_15 listo')


if __name__ == '__main__':
    main()
