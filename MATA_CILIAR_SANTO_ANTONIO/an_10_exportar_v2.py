# -*- coding: utf-8 -*-
"""an_10_exportar_v2 — vetores de entrega POR GLEBA (cliente / CAR).

    python an_10_exportar_v2.py   -> 04_VETORES_ENTREGA_V2/

Para cada capa: GeoJSON (EPSG:4674, datum do CAR), Shapefile (EPSG:4674, campos <= 10 caracteres, UTF-8)
e KML (Google Earth, WGS 84). Mais LEIAME.txt bilingue e um zip. Nada se recalcula: os atributos sao os
de 02_ANALISIS/gleba_*.geojson (an_07). Reutiliza kml() e limpiar() de an_06_exportar.
"""
import os
import sys
import zipfile

import geopandas as gpd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, leer_json, log  # noqa: E402
from an_06_exportar import kml, limpiar                       # noqa: E402

ENTREGA = os.path.join(PROYECTO, '04_VETORES_ENTREGA_V2')
CRS_CAR = 'EPSG:4674'

CAPAS = {
    'gleba_limites': dict(shp={'gleba': 'gleba', 'nome': 'nome', 'area_ha': 'area_ha', 'alqueires': 'alqueires', 'rl_exigida_ha': 'rl_exig_ha'},
                          pt='As duas glebas do imóvel (G1 144,21 ha; G2 13,54 ha = 5,6 alqueires) com área e RL exigida (20%)',
                          es='Las dos glebas del inmueble (G1 144,21 ha; G2 13,54 ha = 5,6 alqueires) con área y RL exigida (20%)'),
    'gleba_G1_car': dict(shp={'gleba': 'gleba', 'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao', 'area_ha': 'area_ha', 'nota': 'nota'},
                         pt='Uso e cobertura da Gleba 1 com a nomenclatura CAR/SICAR (fecha em 144,21 ha)', es='Uso y cobertura de la Gleba 1 con la nomenclatura CAR/SICAR (cierra en 144,21 ha)'),
    'gleba_G2_car': dict(shp={'gleba': 'gleba', 'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao', 'area_ha': 'area_ha', 'nota': 'nota'},
                         pt='Uso e cobertura da Gleba 2 com a nomenclatura CAR/SICAR (fecha em 13,54 ha)', es='Uso y cobertura de la Gleba 2 con la nomenclatura CAR/SICAR (cierra en 13,54 ha)'),
    'gleba_G1_app': dict(shp={'gleba': 'gleba', 'feicao': 'feicao', 'situacao': 'situacao', 'cenario': 'cenario', 'pra_pr_recompor': 'pra_recomp', 'area_ha': 'area_ha'},
                         pt='APP da Gleba 1 por feição (curso / nascente / faixa do reservatório) e situação (conforme / a recompor / água); cenario = base (30 m / 50 m) ou fbds_iat_adicional (faixa de 30 m do reservatório, NÃO somada); pra_pr_recompor = True onde a faixa reduzida do PRA-PR (20 m / 15 m) ainda exige recompor',
                         es='APP de la Gleba 1 por rasgo (curso / nascente / faja del reservorio) y situación (conforme / a recomponer / agua); cenario = base (30 m / 50 m) o fbds_iat_adicional (faja de 30 m del reservorio, NO sumada); pra_pr_recompor = True donde la faja reducida del PRA-PR (20 m / 15 m) aún exige recomponer'),
    'gleba_G2_app': dict(shp={'gleba': 'gleba', 'feicao': 'feicao', 'situacao': 'situacao', 'cenario': 'cenario', 'pra_pr_recompor': 'pra_recomp', 'area_ha': 'area_ha'},
                         pt='APP da Gleba 2 (0,22 ha do Arroio 1 na ponta norte, toda com vegetação nativa)', es='APP de la Gleba 2 (0,22 ha del Arroyo 1 en la punta norte, toda con vegetación nativa)'),
    'gleba_G1_rl_existente': dict(shp={'gleba': 'gleba', 'classe': 'classe', 'area_ha': 'area_ha', 'rl_exigida_ha': 'rl_exig_ha', 'rl_existente_ha': 'rl_exis_ha', 'deficit_ha': 'deficit_ha'},
                                  pt='Reserva Legal existente na Gleba 1: remanescente fora da APP + APP com vegetação (art. 15); exigida 28,84 ha, existente 17,70 ha, déficit 11,14 ha',
                                  es='Reserva Legal existente en la Gleba 1: remanente fuera de la APP + APP con vegetación (art. 15); exigida 28,84 ha, existente 17,70 ha, déficit 11,14 ha'),
    'gleba_G2_rl_existente': dict(shp={'gleba': 'gleba', 'classe': 'classe', 'area_ha': 'area_ha', 'rl_exigida_ha': 'rl_exig_ha', 'rl_existente_ha': 'rl_exis_ha', 'deficit_ha': 'deficit_ha'},
                                  pt='Reserva Legal existente na Gleba 2 (2,68 ha na ponta norte; exigida 2,71 ha): só vale se a floresta pertencer à gleba – confirmar em campo / escritura',
                                  es='Reserva Legal existente en la Gleba 2 (2,68 ha en la punta norte; exigida 2,71 ha): solo vale si la floresta pertenece a la gleba – confirmar en campo / escritura'),
    'gleba_G1_arroios': dict(shp={'gleba': 'gleba', 'n': 'n', 'nome': 'nome', 'posicao': 'posicao', 'fbds_ids': 'fbds_ids', 'comprimento_dentro_m': 'comp_in_m', 'comprimento_total_fbds_m': 'comp_tot_m',
                                  'nasce_dentro': 'nasce_in', 'nascente_fbds_id': 'nasc_id', 'tipo': 'tipo', 'represado': 'represado', 'regime_coincide_ibge_perene_m': 'per_ibge_m'},
                             pt='Arroios da Gleba 1 (cursos FBDS 2013 distintos, recortados à gleba): 1 norte (523 m), 2 central (951 m, nasce na gleba), 3 sul (564 m, represado)',
                             es='Arroyos de la Gleba 1 (cursos FBDS 2013 distintos, recortados a la gleba): 1 norte (523 m), 2 central (951 m, nace en la gleba), 3 sur (564 m, represado)'),
    'gleba_G2_arroios': dict(shp={'gleba': 'gleba', 'n': 'n', 'nome': 'nome', 'posicao': 'posicao', 'fbds_ids': 'fbds_ids', 'comprimento_dentro_m': 'comp_in_m', 'comprimento_total_fbds_m': 'comp_tot_m',
                                  'nasce_dentro': 'nasce_in', 'tipo': 'tipo', 'represado': 'represado'},
                             pt='Arroio 1 na Gleba 2 (33 m na ponta norte)', es='Arroyo 1 en la Gleba 2 (33 m en la punta norte)'),
    'gleba_G1_lagoas': dict(shp={'gleba': 'gleba', 'massa_id': 'massa_id', 'corpo_id': 'corpo_id', 'natureza': 'natureza', 'barramento_curso_natural': 'barram', 'espelho_fbds_2013_dentro_ha': 'esp13_ha',
                                 'espelho_mndwi_2026_ha': 'esp26_ha', 'jrc_occurrence_media': 'jrc_occ', 'espelho_jrc_max_extent_ha': 'jrc_max_ha'},
                            pt='Reservatório da Gleba 1: 2 massas FBDS 2013 contíguas (19083 + 20452) = 1 corpo; espelho 1,95 ha (2013) / 1,98 ha (RF 2026) / 0,91 ha (água clara na seca)',
                            es='Reservorio de la Gleba 1: 2 masas FBDS 2013 contiguas (19083 + 20452) = 1 cuerpo; espejo 1,95 ha (2013) / 1,98 ha (RF 2026) / 0,91 ha (agua clara en la seca)'),
    'gleba_G1_floresta': dict(shp={'gleba': 'gleba', 'frag_id': 'frag_id', 'area_dentro_ha': 'area_in_ha', 'area_total_ha': 'area_tot', 'persistencia': 'persist'},
                              pt='Fragmentos de floresta nativa (RF 2026, maiores que 0,5 ha) recortados à Gleba 1', es='Fragmentos de floresta nativa (RF 2026, mayores que 0,5 ha) recortados a la Gleba 1'),
    'gleba_G2_floresta': dict(shp={'gleba': 'gleba', 'frag_id': 'frag_id', 'area_dentro_ha': 'area_in_ha', 'area_total_ha': 'area_tot', 'persistencia': 'persist'},
                              pt='Floresta da ponta norte da Gleba 2 (2,68 ha, fragmento 2, floresta desde 1985): pertence à gleba? confirmar', es='Floresta de la punta norte de la Gleba 2 (2,68 ha, fragmento 2, floresta desde 1985): ¿pertenece a la gleba? confirmar'),
}
CAMPOS = {
    'gleba': ('G1 = imóvel principal; G2 = os 6 alqueires', 'G1 = inmueble principal; G2 = los 6 alqueires'),
    'nome': ('nome', 'nombre'), 'area_ha': ('área em hectares (EPSG:31982)', 'área en hectáreas (EPSG:31982)'),
    'alqueires': ('alqueires paulistas (2,42 ha)', 'alqueires paulistas (2,42 ha)'), 'rl_exigida_ha': ('RL exigida = 20% da gleba', 'RL exigida = 20% de la gleba'),
    'classe_car': ('classe oficial CAR/SICAR', 'clase oficial CAR/SICAR'), 'subclasse': ('subclasse', 'subclase'), 'situacao': ('situação (RF 2026)', 'situación (RF 2026)'),
    'nota': ('observação técnica', 'observación técnica'), 'feicao': ('curso / nascente / reservatorio faixa 30 m', 'curso / nascente / reservatorio faixa 30 m'),
    'cenario': ('base (exigível) ou fbds_iat_adicional (cenário, não somado)', 'base (exigible) o fbds_iat_adicional (escenario, no sumado)'),
    'pra_pr_recompor': ('1 = ainda a recompor pela faixa reduzida do PRA-PR', '1 = aún a recomponer por la faja reducida del PRA-PR'),
    'classe': ('classe', 'clase'), 'rl_existente_ha': ('RL existente da gleba (ha)', 'RL existente de la gleba (ha)'), 'deficit_ha': ('déficit de RL da gleba (ha)', 'déficit de RL de la gleba (ha)'),
    'n': ('número do arroio', 'número del arroyo'), 'posicao': ('norte / central / sul', 'norte / central / sur'), 'fbds_ids': ('ids FBDS 2013 do curso', 'ids FBDS 2013 del curso'),
    'comprimento_dentro_m': ('comprimento dentro da gleba (m)', 'longitud dentro de la gleba (m)'), 'comprimento_total_fbds_m': ('comprimento total do curso FBDS (m)', 'longitud total del curso FBDS (m)'),
    'nasce_dentro': ('1 = nasce na gleba (nascente FBDS)', '1 = nace en la gleba (nascente FBDS)'), 'nascente_fbds_id': ('id da nascente FBDS', 'id de la nascente FBDS'),
    'tipo': ('atravessa / nasce na gleba', 'atraviesa / nace en la gleba'), 'represado': ('1 = represado', '1 = represado'),
    'regime_coincide_ibge_perene_m': ('m que coincidem com IBGE BC250 permanente (não prova perenidade)', 'm que coinciden con IBGE BC250 permanente (no prueba perennidad)'),
    'massa_id': ('objectid FBDS', 'objectid FBDS'), 'corpo_id': ('corpo (massas contíguas)', 'cuerpo (masas contiguas)'), 'natureza': ('natural / artificial', 'natural / artificial'),
    'barramento_curso_natural': ('1 = art. 4º III aplica', '1 = aplica art. 4º III'), 'espelho_fbds_2013_dentro_ha': ('espelho FBDS 2013 dentro da gleba (ha)', 'espejo FBDS 2013 dentro de la gleba (ha)'),
    'espelho_mndwi_2026_ha': ('água clara S2 29/08/2026 (ha, limite inferior)', 'agua clara S2 29/08/2026 (ha, límite inferior)'), 'jrc_occurrence_media': ('ocorrência JRC 1984-2021 (%)', 'ocurrencia JRC 1984-2021 (%)'),
    'espelho_jrc_max_extent_ha': ('extensão máxima JRC (ha)', 'extensión máxima JRC (ha)'),
    'frag_id': ('id do fragmento', 'id del fragmento'), 'area_dentro_ha': ('área dentro da gleba (ha)', 'área dentro de la gleba (ha)'), 'area_total_ha': ('área total do fragmento (ha)', 'área total del fragmento (ha)'),
    'persistencia': ('histórico MapBiomas 1985/2008', 'histórico MapBiomas 1985/2008'),
    'n_partes': ('partes', 'partes'), 'composicao': ('composição', 'composición'), 'status': ('status', 'estado'),
}


def main():
    os.makedirs(ENTREGA, exist_ok=True)
    log('=' * 78); log('an_10_exportar_v2 -> %s' % ENTREGA); log('=' * 78)
    G = leer_json(os.path.join(ANALISIS, 'resultados_glebas.json'))
    # RL proposta recortada a G1 (a partir de RL_proposta e do limite da G1; area de an_07)
    rl = gpd.read_file(os.path.join(ANALISIS, 'RL_proposta.geojson'))
    lim = gpd.read_file(os.path.join(ANALISIS, 'gleba_limites.geojson'))
    g1 = lim[lim.gleba == 'G1'].geometry.iloc[0]
    rlg1 = rl.copy(); rlg1['geometry'] = rlg1.geometry.intersection(g1)
    rlg1['area_ha'] = G['G1']['reserva_legal']['rl_proposta_recortada_ha']; rlg1['gleba'] = 'G1'
    rlg1['status'] = 'PROPOSTA recortada a Gleba 1: %.2f ha, %.2f ha aquem dos %.2f ha exigidos; ampliar corredor dentro da G1; sujeita ao IAT' % (
        G['G1']['reserva_legal']['rl_proposta_recortada_ha'], -G['G1']['reserva_legal']['rl_proposta_recortada_vs_exigida_ha'], G['G1']['reserva_legal']['exigida_ha'])
    rlg1.to_file(os.path.join(ANALISIS, 'RL_proposta_G1.geojson'), driver='GeoJSON')
    capas = dict(CAPAS)
    capas['RL_proposta_G1'] = dict(shp={'gleba': 'gleba', 'classe_car': 'classe_car', 'area_ha': 'area_ha', 'n_partes': 'n_partes', 'composicao': 'composicao', 'status': 'status'},
                                   pt='Reserva Legal Proposta recortada à Gleba 1 (28,57 ha; faltam 0,27 ha para 28,84): ampliar o corredor dentro da G1; sujeita ao IAT',
                                   es='Reserva Legal Propuesta recortada a la Gleba 1 (28,57 ha; faltan 0,27 ha para 28,84): ampliar el corredor dentro de G1; sujeta al IAT')
    leiame = ['LEIAME / LÉAME — Fazenda Santo Antônio · Diagnóstico APP / RL POR GLEBA (v2) · Pixadvisor Agricultura de Precisão · 06/09/2026', '=' * 100, '',
              '[PT] Duas glebas avaliadas SEPARADAMENTE: G1 = imóvel principal (144,21 ha, RL 28,84 ha); G2 = "os 6 alqueires" (13,54 ha = 5,6 alqueires paulistas, RL 2,71 ha).',
              '     SÓ o interior do perímetro: nenhuma feição fora das glebas. Sistema de referência: SIRGAS 2000 geográfico (EPSG:4674), datum do CAR (IN MMA 2/2014 art. 11 §2º);',
              '     áreas (ha) e comprimentos (m) calculados em SIRGAS 2000 / UTM 22S (EPSG:31982). Formatos: .geojson, .shp (+shx/dbf/prj/cpg, UTF-8, campos até 10 caracteres), .kml (WGS 84).',
              '     DIAGNÓSTICO PRELIMINAR por satélite (Sentinel-2 29/08/2026 + hidrografia FBDS/IAT 2013): não substitui laudo; leito, nascentes e estágio sucessional exigem campo.',
              '[ES] Dos glebas evaluadas POR SEPARADO: G1 = inmueble principal (144,21 ha, RL 28,84 ha); G2 = "los 6 alqueires" (13,54 ha = 5,6 alqueires paulistas, RL 2,71 ha).',
              '     SOLO el interior del perímetro: ningún rasgo fuera de las glebas. Sistema de referencia: SIRGAS 2000 geográfico (EPSG:4674), datum del CAR (IN MMA 2/2014 art. 11 §2º);',
              '     áreas (ha) y longitudes (m) calculadas en SIRGAS 2000 / UTM 22S (EPSG:31982). Formatos: .geojson, .shp (+shx/dbf/prj/cpg, UTF-8, campos de hasta 10 caracteres), .kml (WGS 84).',
              '     DIAGNÓSTICO PRELIMINAR por satélite (Sentinel-2 29/08/2026 + hidrografía FBDS/IAT 2013): no sustituye un laudo; leito, nascentes y estadio sucesional exigen campo.', '']
    for nombre, cfg in capas.items():
        g = gpd.read_file(os.path.join(ANALISIS, nombre + '.geojson'))
        cols = [c for c in cfg['shp'] if c in g.columns]
        g = limpiar(g[cols + ['geometry']]).to_crs(CRS_CAR)
        for ext in ('geojson', 'shp', 'shx', 'dbf', 'prj', 'cpg', 'kml'):
            p = os.path.join(ENTREGA, nombre + '.' + ext)
            if os.path.exists(p):
                os.remove(p)
        g.to_file(os.path.join(ENTREGA, nombre + '.geojson'), driver='GeoJSON')
        gs = g.rename(columns={c: cfg['shp'][c] for c in cols})
        assert all(len(c) <= 10 for c in gs.columns if c != 'geometry'), nombre
        gs.to_file(os.path.join(ENTREGA, nombre + '.shp'), driver='ESRI Shapefile', encoding='utf-8')
        kml(g, os.path.join(ENTREGA, nombre + '.kml'), nombre, cfg['pt'], cols)
        chk = gpd.read_file(os.path.join(ENTREGA, nombre + '.shp'))
        assert len(chk) == len(g) and chk.crs.to_epsg() == 4674, nombre
        area = (' · soma area_ha = %.2f' % g['area_ha'].astype(float).sum()) if ('area_ha' in g.columns and g.geom_type.iloc[0].endswith('Polygon')) else ''
        log('  %-24s %2d feats · %-12s -> geojson + shp + kml (EPSG:4674)%s' % (nombre, len(g), g.geom_type.iloc[0], area))
        leiame += ['-' * 100, '%s  (%s, %d feições / entidades)' % (nombre, g.geom_type.iloc[0], len(g)), '  [PT] ' + cfg['pt'], '  [ES] ' + cfg['es'], '  Campos (GeoJSON/KML -> Shapefile):']
        for c in cols:
            d = CAMPOS.get(c, (c, c))
            leiame.append('    %-30s -> %-10s  [PT] %s' % (c, cfg['shp'][c], d[0]))
            leiame.append('    %-30s    %-10s  [ES] %s' % ('', '', d[1]))
        leiame.append('')
    leiame += ['-' * 100, 'Contato / Contacto: Eng. Agr. Nilton Camargo · Director Técnico · Pixadvisor Agricultura de Precisão',
               'nilton.camargo@pixadvisor.network · +591 721 49171']
    with open(os.path.join(ENTREGA, 'LEIAME.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(leiame))
    z = os.path.join(ENTREGA, 'Fazenda_Santo_Antonio_vetores_por_gleba_EPSG4674.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(ENTREGA)):
            if not f.endswith('.zip'):
                zf.write(os.path.join(ENTREGA, f), f)
    log('  -> LEIAME.txt + %s' % z)
    log('an_10 listo')


if __name__ == '__main__':
    main()
