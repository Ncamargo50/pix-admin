# -*- coding: utf-8 -*-
"""an_06_exportar — vectores de entrega para el cliente / CAR.

    python an_06_exportar.py   -> 04_VETORES_ENTREGA/

Para cada capa: GeoJSON (EPSG:4674, SIRGAS 2000 geografico = datum del CAR), Shapefile
(EPSG:4674, campos <= 10 caracteres, UTF-8 con .cpg) y KML (Google Earth, WGS 84 por
definicion del formato; SIRGAS 2000 y WGS 84 difieren < 1 m). Mas LEIAME.txt bilingue.
No se recalcula nada: los atributos son los de 02_ANALISIS.
"""
import os
import sys
import zipfile

import geopandas as gpd
import numpy as np
import simplekml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, log  # noqa: E402

ENTREGA = os.path.join(PROYECTO, '04_VETORES_ENTREGA')
CRS_CAR = 'EPSG:4674'

# capa -> (archivo fuente, filtro, renombres shapefile (<=10 chars), descripcion PT, descripcion ES)
CAPAS = {
    'mapa_uso_car': dict(src='mapa_uso_car', shp={'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao',
                                                   'area_ha': 'area_ha', 'nota': 'nota', 'pousio': 'pousio'},
                         pt='Uso e cobertura do imóvel com a nomenclatura CAR/SICAR (8 polígonos sem sobreposição, soma 157,75 ha)',
                         es='Uso y cobertura del inmueble con la nomenclatura CAR/SICAR (8 polígonos sin superposición, suma 157,75 ha)'),
    'APP': dict(src='mapa_uso_car', filtro=lambda g: g[g.classe_car.str.startswith('APP')],
                shp={'classe_car': 'classe_car', 'subclasse': 'subclasse', 'situacao': 'situacao', 'area_ha': 'area_ha', 'nota': 'nota'},
                pt='APP exigível (curso d\'água até 10 m: 30 m do eixo FBDS; nascente: raio 50 m) por situação: conforme / a recompor. Soma 11,02 ha: o espelho d\'água dentro da APP (1,16 ha) está na camada mapa_uso_car (Reservatório artificial); total exigível 12,18 ha',
                es='APP exigible (curso de agua hasta 10 m: 30 m del eje FBDS; nascente: radio 50 m) por situación: conforme / a recomponer. Suma 11,02 ha: el espejo de agua dentro de la APP (1,16 ha) está en la capa mapa_uso_car (Reservatório artificial); total exigible 12,18 ha'),
    'RL_proposta': dict(src='RL_proposta', shp={'classe_car': 'classe_car', 'area_ha': 'area_ha', 'composicao': 'composicao', 'status': 'status'},
                        pt='Reserva Legal Proposta (31,57 ha): remanescente + APP computável + corredor de recomposição; sujeita ao IAT',
                        es='Reserva Legal Propuesta (31,57 ha): remanente + APP computable + corredor de recomposición; sujeta al IAT'),
    'hidrografia_consolidada': dict(src='hidrografia_consolidada',
                                    shp={'fonte': 'fonte', 'id_fonte': 'id_fonte', 'largura_classe': 'larg_cls', 'regime': 'regime',
                                         'frac_coincide_ibge_perm': 'frac_ibge', 'dentro_propriedade': 'dentro', 'comprimento_m': 'comp_m',
                                         'comprimento_dentro_m': 'comp_in_m', 'nome': 'nome'},
                                    pt='Cursos d\'água por fonte (FBDS 2013 = referência legal; otto 2020, ANA, IBGE BC250, rede DEM = controle) com regime e comprimento',
                                    es='Cursos de agua por fuente (FBDS 2013 = referencia legal; otto 2020, ANA, IBGE BC250, red DEM = control) con régimen y longitud'),
    'nascentes_consolidadas': dict(src='nascentes_consolidadas',
                                   shp={'fonte': 'fonte', 'id_fonte': 'id_fonte', 'candidato_dem': 'cand_dem', 'validar_campo': 'val_campo',
                                        'dentro_propriedade': 'dentro', 'dist_nascente_fbds_m': 'd_nasc_m', 'dist_curso_fbds_m': 'd_curso_m',
                                        'hand_m': 'hand_m', 'perenidade': 'perenid', 'nota': 'nota'},
                                   pt='Nascentes FBDS 2013 e candidatos DEM (candidato_dem = True NÃO é nascente até verificação em campo)',
                                   es='Nascentes FBDS 2013 y candidatos DEM (candidato_dem = True NO es nascente hasta verificación en campo)'),
    'vegetacao_nativa_10m': dict(src='vegetacao_nativa_10m',
                                 shp={'classe_id': 'classe_id', 'classe': 'classe', 'area_ha': 'area_ha', 'area_dentro_propriedade_ha': 'area_in_ha',
                                      'intersecta_propriedade': 'inters'},
                                 pt='Classificação Random Forest 10 m (S2 29/08/2026): FLORESTA_NATIVA, AGUA, AREA_ANTROPIZADA, SILVICULTURA (incerta)',
                                 es='Clasificación Random Forest 10 m (S2 29/08/2026): FLORESTA_NATIVA, AGUA, AREA_ANTROPIZADA, SILVICULTURA (incierta)'),
    'massas_dagua_propriedade': dict(src='massas_dagua_propriedade',
                                     shp={'massa_id': 'massa_id', 'municipio': 'municipio', 'natureza': 'natureza', 'rio': 'rio', 'setor': 'setor',
                                          'area_fbds_2013_ha': 'a_fbds_ha', 'area_dentro_prop_ha': 'a_in_ha', 'area_s2_2026_ha': 'a_s2_ha',
                                          'jrc_occurrence_media': 'jrc_occ', 'sobre_curso_fbds': 'sobre_crs', 'fbds_rio_ids': 'rio_ids',
                                          'barramento_curso_natural': 'barram', 'dispensa_art4_par4_lt1ha': 'disp_1ha'},
                                     pt='Reservatórios artificiais FBDS 2013 dentro do imóvel: espelho 2013 / 2026, ocorrência JRC, barramento e dispensa art. 4º §4º',
                                     es='Reservorios artificiales FBDS 2013 dentro del inmueble: espejo 2013 / 2026, ocurrencia JRC, represamiento y dispensa art. 4º §4º'),
}

CAMPOS = {   # descripcion de campos (nombre original -> pt / es)
    'classe_car': ('classe oficial CAR/SICAR', 'clase oficial CAR/SICAR'),
    'subclasse': ('subclasse: conforme / a recompor / espelho d agua / floresta fora da APP / uso agricola / silvicultura', 'subclase: conforme / a recomponer / espejo de agua / floresta fuera de la APP / uso agrícola / silvicultura'),
    'situacao': ('situação da cobertura (RF 2026)', 'situación de la cobertura (RF 2026)'),
    'area_ha': ('área em hectares (calculada em EPSG:31982)', 'área en hectáreas (calculada en EPSG:31982)'),
    'nota': ('observação técnica', 'observación técnica'),
    'pousio': ('área de pousio (sempre False: não identificável com uma cena)', 'área en descanso (siempre False: no identificable con una escena)'),
    'composicao': ('composição da RL proposta', 'composición de la RL propuesta'),
    'status': ('status: PROPOSTA sujeita à aprovação do IAT', 'estado: PROPUESTA sujeta a aprobación del IAT'),
    'fonte': ('fonte da geometria (FBDS, otto, ANA, IBGE, DEM, DEM_GLO30_cabeceira)', 'fuente de la geometría (FBDS, otto, ANA, IBGE, DEM, DEM_GLO30_cabeceira)'),
    'id_fonte': ('identificador na fonte original', 'identificador en la fuente original'),
    'largura_classe': ('classe de largura FBDS (ate_10m) / nao_informada / nao_aplica', 'clase de ancho FBDS (ate_10m) / nao_informada / nao_aplica'),
    'regime': ('perene (coincide com IBGE BC250) ou nao_classificado_campo', 'perenne (coincide con IBGE BC250) o nao_classificado_campo'),
    'frac_coincide_ibge_perm': ('fração do tramo a menos de 30 m de trecho BC250 permanente', 'fracción del tramo a menos de 30 m de un tramo BC250 permanente'),
    'dentro_propriedade': ('True se toca o imóvel', 'True si toca el inmueble'),
    'comprimento_m': ('comprimento total (m)', 'longitud total (m)'),
    'comprimento_dentro_m': ('comprimento dentro do imóvel (m)', 'longitud dentro del inmueble (m)'),
    'nome': ('nome do curso (otto/ANA/IBGE)', 'nombre del curso (otto/ANA/IBGE)'),
    'candidato_dem': ('True = cabeceira DEM, NÃO é nascente até verificação', 'True = cabecera DEM, NO es nascente hasta verificación'),
    'validar_campo': ('sempre True: toda nascente exige confirmação em campo', 'siempre True: toda nascente exige confirmación en campo'),
    'dist_nascente_fbds_m': ('distância à nascente FBDS mais próxima (m)', 'distancia a la nascente FBDS más cercana (m)'),
    'dist_curso_fbds_m': ('distância ao curso FBDS mais próximo (m)', 'distancia al curso FBDS más cercano (m)'),
    'hand_m': ('altura acima da drenagem mais próxima (m)', 'altura sobre el drenaje más cercano (m)'),
    'perenidade': ('nao_verificada', 'nao_verificada'),
    'classe_id': ('1 FLORESTA_NATIVA · 2 AGUA · 3 AREA_ANTROPIZADA · 4 SILVICULTURA', '1 FLORESTA_NATIVA · 2 AGUA · 3 AREA_ANTROPIZADA · 4 SILVICULTURA'),
    'classe': ('nome da classe RF', 'nombre de la clase RF'),
    'area_dentro_propriedade_ha': ('área dentro do imóvel (ha)', 'área dentro del inmueble (ha)'),
    'intersecta_propriedade': ('True se toca o imóvel', 'True si toca el inmueble'),
    'massa_id': ('objectid FBDS da massa d\'água', 'objectid FBDS de la masa de agua'),
    'municipio': ('município (FBDS)', 'municipio (FBDS)'), 'natureza': ('natural / artificial (FBDS)', 'natural / artificial (FBDS)'),
    'rio': ('rio presente/ausente (FBDS)', 'río presente/ausente (FBDS)'), 'setor': ('rural / urbano (FBDS)', 'rural / urbano (FBDS)'),
    'area_fbds_2013_ha': ('espelho FBDS 2013 (ha)', 'espejo FBDS 2013 (ha)'), 'area_dentro_prop_ha': ('área dentro do imóvel (ha)', 'área dentro del inmueble (ha)'),
    'area_s2_2026_ha': ('espelho MNDWI S2 29/08/2026 (ha, estação seca)', 'espejo MNDWI S2 29/08/2026 (ha, estación seca)'),
    'jrc_occurrence_media': ('ocorrência média de água JRC 1984-2021 (%)', 'ocurrencia media de agua JRC 1984-2021 (%)'),
    'sobre_curso_fbds': ('True se represa curso FBDS', 'True si represa un curso FBDS'), 'fbds_rio_ids': ('ids dos cursos FBDS represados', 'ids de los cursos FBDS represados'),
    'barramento_curso_natural': ('True = art. 4º III aplica (faixa da licença)', 'True = aplica art. 4º III (faja de la licencia)'),
    'dispensa_art4_par4_lt1ha': ('True se espelho FBDS menor que 1 ha (§4º)', 'True si el espejo FBDS es menor que 1 ha (§4º)'),
}


def limpiar(g):
    g = g.copy()
    for c in g.columns:
        if c == 'geometry':
            continue
        if g[c].dtype == bool or str(g[c].dtype) == 'boolean':
            g[c] = g[c].astype(int)          # shapefile no tiene booleanos
        elif g[c].dtype == object:
            g[c] = g[c].map(lambda v: '' if v is None else str(v))
    return g


def kml(g, ruta, nombre, desc, campos):
    k = simplekml.Kml(name=nombre)
    doc = k.newfolder(name=nombre, description=desc)
    for _, r in g.iterrows():
        props = {c: r[c] for c in campos if c in g.columns}
        etiqueta = str(props.get('classe_car') or props.get('classe') or props.get('nome') or props.get('id_fonte') or props.get('massa_id') or nombre)
        if 'subclasse' in props and props['subclasse']:
            etiqueta += ' — ' + str(props['subclasse'])
        html = '<table>' + ''.join('<tr><td><b>%s</b></td><td>%s</td></tr>' % (c, v) for c, v in props.items()) + '</table>'
        geom = r.geometry
        partes = geom.geoms if hasattr(geom, 'geoms') else [geom]
        for p in partes:
            if p.geom_type == 'Polygon':
                f = doc.newpolygon(name=etiqueta, description=html, outerboundaryis=list(p.exterior.coords))
                f.innerboundaryis = [list(i.coords) for i in p.interiors]
                f.style.linestyle.width = 2
                sub = str(props.get('subclasse', ''))
                cls = str(props.get('classe_car', '') or props.get('classe', ''))
                if 'recompor' in sub:
                    col = simplekml.Color.changealphaint(150, simplekml.Color.red)
                elif sub == 'conforme' or 'FLORESTA' in cls or 'Remanescente' in cls:
                    col = simplekml.Color.changealphaint(150, simplekml.Color.green)
                elif 'AGUA' in cls or 'espelho' in sub or 'Reservat' in cls:
                    col = simplekml.Color.changealphaint(150, simplekml.Color.blue)
                elif 'Reserva Legal' in cls:
                    col = simplekml.Color.changealphaint(110, simplekml.Color.purple)
                else:
                    col = simplekml.Color.changealphaint(70, simplekml.Color.yellow)
                f.style.polystyle.color = col
            elif p.geom_type == 'LineString':
                f = doc.newlinestring(name=etiqueta, description=html, coords=list(p.coords))
                f.style.linestyle.width = 3
                f.style.linestyle.color = simplekml.Color.blue if props.get('fonte') == 'FBDS' else simplekml.Color.gray
            elif p.geom_type == 'Point':
                f = doc.newpoint(name=etiqueta, description=html, coords=[(p.x, p.y)])
                f.style.iconstyle.color = simplekml.Color.orange if props.get('candidato_dem') else simplekml.Color.blue
    k.save(ruta)


def main():
    os.makedirs(ENTREGA, exist_ok=True)
    log('=' * 78); log('an_06_exportar -> %s' % ENTREGA); log('=' * 78)
    leiame = ['LEIAME / LÉAME — Fazenda Santo Antônio · Diagnóstico APP / RL · Pixadvisor Agricultura de Precisão · 06/09/2026',
              '=' * 100, '',
              '[PT] Sistema de referência: SIRGAS 2000 geográfico (EPSG:4674), datum exigido pelo CAR (IN MMA 2/2014 art. 11 §2º).',
              '     Áreas (ha) e comprimentos (m) foram calculados em SIRGAS 2000 / UTM 22S (EPSG:31982) antes da conversão.',
              '     Formatos: .geojson (EPSG:4674), .shp/.shx/.dbf/.prj/.cpg (EPSG:4674, UTF-8, nomes de campo até 10 caracteres),',
              '     .kml (Google Earth; WGS 84 por definição do formato, diferença < 1 m em relação ao SIRGAS 2000).',
              '     Este material é um DIAGNÓSTICO PRELIMINAR por satélite (Sentinel-2 29/08/2026 + hidrografia FBDS/IAT 2013):',
              '     não substitui laudo; leito regular, nascentes e estágio sucessional exigem confirmação em campo.',
              '[ES] Sistema de referencia: SIRGAS 2000 geográfico (EPSG:4674), datum exigido por el CAR (IN MMA 2/2014 art. 11 §2º).',
              '     Áreas (ha) y longitudes (m) se calcularon en SIRGAS 2000 / UTM 22S (EPSG:31982) antes de la conversión.',
              '     Formatos: .geojson (EPSG:4674), .shp/.shx/.dbf/.prj/.cpg (EPSG:4674, UTF-8, nombres de campo de hasta 10 caracteres),',
              '     .kml (Google Earth; WGS 84 por definición del formato, diferencia < 1 m respecto de SIRGAS 2000).',
              '     Este material es un DIAGNÓSTICO PRELIMINAR por satélite (Sentinel-2 29/08/2026 + hidrografía FBDS/IAT 2013):',
              '     no sustituye un laudo; el "leito regular", las nascentes y el estadio sucesional exigen confirmación en campo.', '']
    for nombre, cfg in CAPAS.items():
        g = gpd.read_file(os.path.join(ANALISIS, cfg['src'] + '.geojson'))
        if 'filtro' in cfg:
            g = cfg['filtro'](g).copy()
        g = g[list(cfg['shp'].keys()) + ['geometry']]
        g = limpiar(g).to_crs(CRS_CAR)
        # GeoJSON
        r_gj = os.path.join(ENTREGA, nombre + '.geojson')
        if os.path.exists(r_gj):
            os.remove(r_gj)
        g.to_file(r_gj, driver='GeoJSON')
        # Shapefile (campos <= 10 chars)
        gs = g.rename(columns=cfg['shp'])
        assert all(len(c) <= 10 for c in gs.columns if c != 'geometry'), nombre
        for ext in ('shp', 'shx', 'dbf', 'prj', 'cpg'):
            p = os.path.join(ENTREGA, nombre + '.' + ext)
            if os.path.exists(p):
                os.remove(p)
        gs.to_file(os.path.join(ENTREGA, nombre + '.shp'), driver='ESRI Shapefile', encoding='utf-8')
        # KML
        kml(g, os.path.join(ENTREGA, nombre + '.kml'), nombre, cfg['pt'], list(cfg['shp'].keys()))
        # verificacion: relectura
        chk = gpd.read_file(os.path.join(ENTREGA, nombre + '.shp'))
        assert len(chk) == len(g) and chk.crs.to_epsg() == 4674, nombre
        area = ''
        if g.geom_type.iloc[0].endswith('Polygon') and 'area_ha' in g.columns:
            area = ' · soma area_ha = %.2f' % g['area_ha'].astype(float).sum()
        log('  %-26s %3d feats · %-12s -> geojson + shp + kml (EPSG:4674)%s' % (nombre, len(g), g.geom_type.iloc[0], area))
        leiame += ['-' * 100, '%s  (%s, %d feições / entidades)' % (nombre, g.geom_type.iloc[0], len(g)),
                   '  [PT] ' + cfg['pt'], '  [ES] ' + cfg['es'], '  Campos (GeoJSON/KML -> Shapefile):']
        for c, cs in cfg['shp'].items():
            d = CAMPOS.get(c, (c, c))
            leiame.append('    %-28s -> %-10s  [PT] %s' % (c, cs, d[0]))
            leiame.append('    %-28s    %-10s  [ES] %s' % ('', '', d[1]))
        leiame.append('')
    leiame += ['-' * 100, 'Contato / Contacto: Eng. Agr. Nilton Camargo · Director Técnico · Pixadvisor Agricultura de Precisão',
               'nilton.camargo@pixadvisor.network · +591 721 49171']
    with open(os.path.join(ENTREGA, 'LEIAME.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(leiame))
    # zip de conveniencia
    z = os.path.join(ENTREGA, 'Fazenda_Santo_Antonio_vetores_EPSG4674.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(ENTREGA)):
            if not f.endswith('.zip'):
                zf.write(os.path.join(ENTREGA, f), f)
    log('  -> LEIAME.txt + %s' % z)
    log('an_06 listo')


if __name__ == '__main__':
    main()
