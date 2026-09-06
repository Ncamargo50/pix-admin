# -*- coding: utf-8 -*-
"""an_04_mapas — mapas tematicos del diagnostico APP / RL / vegetacao nativa.

    python an_04_mapas.py --lang pt      -> 03_MAPAS/*.png  (+ 03_MAPAS/A4_horizontal/*.png)
    python an_04_mapas.py --lang es      -> 03_MAPAS/ES/*.png (+ ES/A4_horizontal/*.png)

Regla: NINGUN numero se recalcula aqui. Todas las cifras rotuladas salen de
02_ANALISIS/resultados_analisis.json y de las tablas de atributos de las capas.
Las unicas geometrias derivadas son de DIBUJO (contorno del buffer de 30 m,
faixa de 20 m del cenario B): no producen ninguna cifra del informe. La faixa
oficial FBDS/IAT del reservatorio se dibuja desde la capa de analisis
mapa_uso_car_cenario_fbds.geojson y el talvegue DEM desde talvegue_dem_candidatos.geojson.

Cada mapa sale en dos formatos:
  * vertical  (~15 cm de ancho util para A4 vertical, figura alta, 250 dpi)
  * A4 apaisado (titulo grande, leyenda lateral) en la subcarpeta A4_horizontal/
"""
import argparse
import json
import os
import sys
import textwrap

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import (ANALISIS, PROYECTO, R, DATOS_EXT, RESULTADOS_JSON,   # noqa: E402
                          CRS_METRICO, PROPIEDAD_GEOJSON, leer_json, log)

import matplotlib                                   # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402
from matplotlib.patches import Patch, Polygon as MPolygon  # noqa: E402
from matplotlib.ticker import FuncFormatter        # noqa: E402
import geopandas as gpd                            # noqa: E402
import rasterio                                    # noqa: E402
from rasterio import features                      # noqa: E402
from rasterio.windows import from_bounds           # noqa: E402
from shapely.geometry import box, shape            # noqa: E402
from shapely.ops import unary_union                # noqa: E402

MAPAS = os.path.join(PROYECTO, '03_MAPAS')
DPI = 250

# ------------------------------------------------------------------ marca ----
AZUL, TEAL, LIMA = '#1E40AF', '#0D9488', '#7FD633'
GRIS = '#333333'
COL = {
    'prop': '#FFE600',
    'fbds': '#1D4ED8', 'fbds_perene': '#0B1F7A', 'otto': '#60A5FA',
    'dem': '#6B7280', 'agua_s2': '#7DD3FC', 'massa': '#0369A1',
    'nasc': '#1D4ED8', 'cand': '#F97316',
    'floresta': '#1B5E20', 'silv': '#9E9D24', 'agua': '#1E88E5', 'antrop': '#F5E6B3',
    'persist': '#1B5E20', 'regen': '#7FD633', 'supr': '#D32F2F', 'hansen': '#B91C1C',
    'app_conf': '#2E7D32', 'app_agua': '#1E88E5', 'app_rec': '#D32F2F', 'app_silv': '#F97316',
    'faixa20': '#FF00E5', 'app_lim': '#111111', 'reserv_faixa': '#6D28D9',
    'rl_rem': '#145A32', 'rl_app': '#4CAF50', 'rl_app_rec': '#EF9A9A', 'rl_corr': '#7FD633',
    'rl_lim': '#6A1B9A',
    'car_app_conf': '#4CAF50', 'car_app_rec': '#D32F2F', 'car_reserv': '#1E88E5',
    'car_rem': '#145A32', 'car_cons': '#F5E6B3', 'car_silv': '#9E9D24',
}
# series del grafico NDVI (validadas con validate_palette.js: 5 slots, todos los checks PASS)
SERIE_COL = {'frag13_ribeira': '#0D9488', 'frag2_mata_antiga': '#2F55C9', 'frag30': '#7E22CE',
             'lavoura_norte': '#C2410C', 'lavoura_sul': '#A16207'}

# ------------------------------------------------------------ textos PT/ES ---
T = {
    'fonte_s2': {'pt': 'Fundo: Sentinel-2C L2A 29/08/2026 (RGB B4-B3-B2, tile T22KEV)',
                 'es': 'Fondo: Sentinel-2C L2A 29/08/2026 (RGB B4-B3-B2, tile T22KEV)'},
    'notas': {'pt': 'Cena S2C 29/08/2026 · CRS SIRGAS 2000 / UTM 22S (EPSG:31982) · '
                    'Hidrografia FBDS/IAT 2013 (1:25.000) · DIAGNÓSTICO PRELIMINAR: não substitui '
                    'laudo; leito regular e nascentes a confirmar em campo (RTK).',
              'es': 'Escena S2C 29/08/2026 · CRS SIRGAS 2000 / UTM 22S (EPSG:31982) · '
                    'Hidrografía FBDS/IAT 2013 (1:25.000) · DIAGNÓSTICO PRELIMINAR: no sustituye '
                    'un laudo; leito regular y nascentes a confirmar en campo (RTK).'},
    'marca': {'pt': 'Pixadvisor Agricultura de Precisão · Eng. Agr. Nilton Camargo · 06/09/2026',
              'es': 'Pixadvisor Agricultura de Precisión · Ing. Agr. Nilton Camargo · 06/09/2026'},
    'prop': {'pt': 'Limite do imóvel (157,75 ha, 2 polígonos)', 'es': 'Límite del inmueble (157,75 ha, 2 polígonos)'},
    'legenda': {'pt': 'Legenda', 'es': 'Leyenda'},
    'escala': {'pt': 'Escala gráfica', 'es': 'Escala gráfica'},
    # M01
    'm01_t': {'pt': 'M01 · Localização da Fazenda Santo Antônio', 'es': 'M01 · Localización de la Fazenda Santo Antônio'},
    'm01_s': {'pt': 'São Sebastião da Amoreira – PR (IBGE 4126009) · Norte Pioneiro Paranaense · Mata Atlântica',
              'es': 'São Sebastião da Amoreira – PR (IBGE 4126009) · Norte Pioneiro Paranaense · Mata Atlántica'},
    'aoi': {'pt': 'Área de análise (AOI, imóvel + 1.500 m)', 'es': 'Área de análisis (AOI, inmueble + 1.500 m)'},
    'fbds_ctx': {'pt': "Cursos d'água FBDS/IAT (≤ 10 m)", 'es': "Cursos de agua FBDS/IAT (≤ 10 m)"},
    'muni': {'pt': 'Município de São Sebastião da Amoreira (IBGE)', 'es': 'Municipio de São Sebastião da Amoreira (IBGE)'},
    'faz': {'pt': 'Fazenda Santo Antônio', 'es': 'Fazenda Santo Antônio'},
    'inset_muni': {'pt': 'Situação no município', 'es': 'Situación en el municipio'},
    'sem_pr': {'pt': 'Inset do Paraná omitido: sem base estadual carregada.', 'es': 'Inset de Paraná omitido: sin base estatal cargada.'},
    'ficha_m01': {'pt': ['Cliente: Sonia Maria Bigati', 'Imóvel: 157,75 ha (144,21 + 13,54 ha)',
                         'Módulo fiscal: 20 ha → 7,89 MF', 'Centroide: 23,4858° S · 50,6586° W',
                         'Bioma: Mata Atlântica (IBGE 2024)'],
                  'es': ['Cliente: Sonia Maria Bigati', 'Inmueble: 157,75 ha (144,21 + 13,54 ha)',
                         'Módulo fiscal: 20 ha → 7,89 MF', 'Centroide: 23,4858° S · 50,6586° O',
                         'Bioma: Mata Atlántica (IBGE 2024)']},
    # M02
    'm02_t': {'pt': 'M02 · Hidrografia consolidada', 'es': 'M02 · Hidrografía consolidada'},
    'm02_s': {'pt': 'FBDS/IAT 2013 (1:25.000) · rede DEM GLO-30 (controle) · água aberta S2 29/08/2026',
              'es': 'FBDS/IAT 2013 (1:25.000) · red DEM GLO-30 (control) · agua abierta S2 29/08/2026'},
    'fbds_perene': {'pt': "Curso FBDS ≤ 10 m — coincide c/ IBGE BC250 (que rotula tudo \"Permanente\": regime não discriminado)",
                    'es': "Curso FBDS ≤ 10 m — coincide c/ IBGE BC250 (que rotula todo \"Permanente\": régimen no discriminado)"},
    'fbds_nc': {'pt': "Curso FBDS ≤ 10 m — regime a classificar em campo", 'es': "Curso FBDS ≤ 10 m — régimen a clasificar en campo"},
    'talvegue': {'pt': 'Talvegue DEM ({m} m) — A VALIDAR em campo: sem curso em 5 bases; risco de +{ha} ha de APP',
                 'es': 'Talweg DEM ({m} m) — A VALIDAR en campo: sin curso en 5 bases; riesgo de +{ha} ha de APP'},
    'corpo_txt': {'pt': 'Reservatórios 19083 + 20452 contíguos = UM corpo: FBDS 2013 {fb} ha · JRC máx. {jrc} · NDWI {ndwi} · RF {rf} · MNDWI seca {mn} (limite inferior). Não se presume a dispensa do art. 4º §4º: faixa a definir pelo IAT (art. 4º III).',
                  'es': 'Reservorios 19083 + 20452 contiguos = UN cuerpo: FBDS 2013 {fb} ha · JRC máx. {jrc} · NDWI {ndwi} · RF {rf} · MNDWI seca {mn} (límite inferior). No se presume la dispensa del art. 4º §4º: faja a definir por el IAT (art. 4º III).'},
    'car_viz': {'pt': 'CAR vizinho PR-4124301-F127CD1E… declara reservatório de {ha} ha 100% dentro do imóvel: sobreposição de CAR — verificar no SICAR antes de retificar.',
                'es': 'CAR vecino PR-4124301-F127CD1E… declara un reservorio de {ha} ha 100% dentro del inmueble: superposición de CAR — verificar en el SICAR antes de rectificar.'},
    'fbds_fora': {'pt': 'Curso FBDS fora do imóvel', 'es': 'Curso FBDS fuera del inmueble'},
    'dem_red': {'pt': 'Rede de drenagem DEM (20 ha) — só controle', 'es': 'Red de drenaje DEM (20 ha) — solo control'},
    'nasc_fbds': {'pt': 'Nascente FBDS 2013 (perenidade a confirmar)', 'es': 'Nascente FBDS 2013 (perennidad a confirmar)'},
    'cand_dem': {'pt': 'Candidato DEM a nascente — A VALIDAR', 'es': 'Candidato DEM a nascente — A VALIDAR'},
    'agua_s2': {'pt': 'Espelho d\'água S2 (MNDWI > 0, 29/08/2026)', 'es': 'Espejo de agua S2 (MNDWI > 0, 29/08/2026)'},
    'massa': {'pt': "Massa d'água FBDS 2013 (contorno)", 'es': "Masa de agua FBDS 2013 (contorno)"},
    'reserv': {'pt': 'Reservatório', 'es': 'Reservorio'},
    'tab_hidro': {'pt': [['Fonte', 'km no imóvel', 'Tramos'], ], 'es': [['Fuente', 'km en inmueble', 'Tramos'], ]},
    'nasc_lin': {'pt': 'Nascentes FBDS no imóvel: {n} · candidatos DEM: {c}', 'es': 'Nascentes FBDS en el inmueble: {n} · candidatos DEM: {c}'},
    'consist': {'pt': 'FBDS vs DEM (no imóvel): mediana {m} m · P90 {p} m', 'es': 'FBDS vs DEM (en el inmueble): mediana {m} m · P90 {p} m'},
    # M03
    'm03_t': {'pt': 'M03 · Vegetação nativa a 10 m (Random Forest)', 'es': 'M03 · Vegetación nativa a 10 m (Random Forest)'},
    'm03_s': {'pt': 'Classificação RF sobre S2 29/08/2026 (OA 0,976 · kappa 0,961, medidos sobre píxeles de consenso) · fragmentos ≥ 0,5 ha',
              'es': 'Clasificación RF sobre S2 29/08/2026 (OA 0,976 · kappa 0,961, medidos sobre píxeles de consenso) · fragmentos ≥ 0,5 ha'},
    'm03_nota': {'pt': '{sc} das {ft} ha de floresta do imóvel estão fora do consenso MapBiomas/DW/WorldCover (p média {p}): sem exatidão medida. Frag. 13: B11 {b11} vs pastagem {bp} (arbóreo); DW trees {dw}%; núcleo {nuc} ha (p {pn}) / borda {bor} ha (p {pb}); {lt} ha com p<0,5.',
                 'es': '{sc} de las {ft} ha de floresta del inmueble están fuera del consenso MapBiomas/DW/WorldCover (p media {p}): sin exactitud medida. Frag. 13: B11 {b11} vs pastura {bp} (arbóreo); DW trees {dw}%; núcleo {nuc} ha (p {pn}) / borde {bor} ha (p {pb}); {lt} ha con p<0,5.'},
    'cl_flor': {'pt': 'Floresta nativa (RF) — {ha} ha no imóvel', 'es': 'Floresta nativa (RF) — {ha} ha en inmueble'},
    'cl_silv': {'pt': 'Silvicultura (RF, F1 0,60: incerta) — {ha} ha', 'es': 'Silvicultura (RF, F1 0,60: incierta) — {ha} ha'},
    'cl_agua': {'pt': 'Água (RF) — {ha} ha', 'es': 'Agua (RF) — {ha} ha'},
    'cl_antr': {'pt': 'Área antropizada — {ha} ha', 'es': 'Área antropizada — {ha} ha'},
    'frag': {'pt': 'Fragmento de floresta (id · ha no imóvel)', 'es': 'Fragmento de floresta (id · ha en inmueble)'},
    'frag_lbl': {'pt': 'Frag. {id}\n{ha} ha', 'es': 'Frag. {id}\n{ha} ha'},
    'g01_t': {'pt': 'NDVI mensal (mediana, 24 meses): faixa ciliar norte vs mata antiga vs lavouras',
              'es': 'NDVI mensual (mediana, 24 meses): faja ribereña norte vs monte antiguo vs cultivos'},
    'g01_s': {'pt': 'S2 SR harmonizado + Cloud Score+ (cs_cdf ≥ 0,65) · set/2024 – ago/2026',
              'es': 'S2 SR armonizado + Cloud Score+ (cs_cdf ≥ 0,65) · sep/2024 – ago/2026'},
    'g01_ins': {'pt': 'NDVI mensal, 24 meses', 'es': 'NDVI mensual, 24 meses'},
    'serie': {'pt': {'frag13_ribeira': 'Frag. 13 — faixa ciliar norte', 'frag2_mata_antiga': 'Frag. 2 — mata antiga (1985)',
                     'frag30': 'Frag. 30 — sul', 'lavoura_norte': 'Lavoura norte', 'lavoura_sul': 'Lavoura sul'},
              'es': {'frag13_ribeira': 'Frag. 13 — faja ribereña norte', 'frag2_mata_antiga': 'Frag. 2 — monte antiguo (1985)',
                     'frag30': 'Frag. 30 — sur', 'lavoura_norte': 'Cultivo norte', 'lavoura_sul': 'Cultivo sur'}},
    'g01_nota': {'pt': 'Frag. 13: NDVI {mn}–{mx} o ano todo, sem a queda de entressafra das lavouras ({lmn}–{lmx}) → vegetação permanente, não cultivo anual.',
                 'es': 'Frag. 13: NDVI {mn}–{mx} todo el año, sin la caída de entre-zafra de los cultivos ({lmn}–{lmx}) → vegetación permanente, no cultivo anual.'},
    'ndvi': {'pt': 'NDVI (mediana mensal)', 'es': 'NDVI (mediana mensual)'},
    # M04
    'm04_t': {'pt': 'M04 · Mudança da cobertura florestal 2008 → 2025', 'es': 'M04 · Cambio de cobertura forestal 2008 → 2025'},
    'm04_s': {'pt': 'MapBiomas col. 11 (30 m) · corte legal 22/07/2008 · perda Hansen GFC 2001-2025',
              'es': 'MapBiomas col. 11 (30 m) · corte legal 22/07/2008 · pérdida Hansen GFC 2001-2025'},
    'mb_persist': {'pt': 'Floresta estável 2008–2025 — {ha} ha', 'es': 'Floresta estable 2008–2025 — {ha} ha'},
    'mb_regen': {'pt': 'Regeneração pós-2008 — {ha} ha', 'es': 'Regeneración pos-2008 — {ha} ha'},
    'mb_supr': {'pt': 'Supressão pós-2008 MapBiomas, bruta (indício) — {ha} ha', 'es': 'Supresión pos-2008 MapBiomas, bruta (indicio) — {ha} ha'},
    'mb_agua': {'pt': 'Água — {ha} ha', 'es': 'Agua — {ha} ha'},
    'mb_antr': {'pt': 'Antrópico estável — {ha} ha', 'es': 'Antrópico estable — {ha} ha'},
    'hansen': {'pt': 'Perda Hansen (ano) — no imóvel só 2006 ({ha} ha); pós-2008: {p} ha',
               'es': 'Pérdida Hansen (año) — en el inmueble solo 2006 ({ha} ha); pos-2008: {p} ha'},
    'rf_flor_ctx': {'pt': 'Floresta nativa RF 2026 (contorno)', 'es': 'Floresta nativa RF 2026 (contorno)'},
    'm04_nota': {'pt': 'Supressão pós-2008 do MapBiomas ({s} ha) NÃO confirmada pelo Hansen (0,00 ha): indício de borda, não prova.',
                 'es': 'Supresión pos-2008 de MapBiomas ({s} ha) NO confirmada por Hansen (0,00 ha): indicio de borde, no prueba.'},
    # M05
    'm05_t': {'pt': 'M05 · APP exigível e conformidade', 'es': 'M05 · APP exigible y conformidad'},
    'm05b_t': {'pt': 'M05b · Detalhe norte — APP, nascente e faixa ciliar', 'es': 'M05b · Detalle norte — APP, nascente y faja ribereña'},
    'm05c_t': {'pt': 'M05c · Detalhe sul — APP e reservatórios', 'es': 'M05c · Detalle sur — APP y reservorios'},
    'm05_s': {'pt': 'Lei 12.651/2012 art. 4º: 30 m cursos ≤ 10 m + 50 m nascentes · cobertura RF 29/08/2026',
              'es': 'Ley 12.651/2012 art. 4º: 30 m cursos ≤ 10 m + 50 m nascentes · cobertura RF 29/08/2026'},
    'app_conf': {'pt': 'APP conforme (vegetação nativa) — {ha} ha', 'es': 'APP conforme (vegetación nativa) — {ha} ha'},
    'app_agua': {'pt': 'APP com água — {ha} ha', 'es': 'APP con agua — {ha} ha'},
    'app_rec': {'pt': 'APP a recompor — {ha} ha', 'es': 'APP a recomponer — {ha} ha'},
    'app_silv': {'pt': '   dos quais silvicultura em APP — {ha} ha', 'es': '   de los cuales silvicultura en APP — {ha} ha'},
    'app_lim': {'pt': 'Limite da APP exigível (30 m / 50 m) — {ha} ha', 'es': 'Límite de la APP exigible (30 m / 50 m) — {ha} ha'},
    'faixa20': {'pt': 'Faixa cenário B (PRA-PR: 20 m / 15 m) — recompor {ha} ha', 'es': 'Faja escenario B (PRA-PR: 20 m / 15 m) — recomponer {ha} ha'},
    'reserv_faixa': {'pt': 'Reservatório: faixa "a definir" (IAT, art. 4º III)', 'es': 'Reservorio: faja "a definir" (IAT, art. 4º III)'},
    'reserv_esp': {'pt': "Espelho d'água do reservatório (RF) — {ha} ha", 'es': 'Espejo de agua del reservorio (RF) — {ha} ha'},
    'nasc_app': {'pt': 'Nascente FBDS (APP raio 50 m)', 'es': 'Nascente FBDS (APP radio 50 m)'},
    'curso': {'pt': "Eixo do curso d'água FBDS", 'es': 'Eje del curso de agua FBDS'},
    'm05_kpi': {'pt': 'APP exigível {t} ha [{mn}; {mx}] · conforme {pc}%', 'es': 'APP exigible {t} ha [{mn}; {mx}] · conforme {pc}%'},
    'm05_nota': {'pt': 'Cenário A (integral): recompor {a} ha · Cenário B (PRA-PR, exige CAR até 31/12/2023): {b} ha. Candidatos DEM a nascente (+{c} ha se confirmados) e faixa do reservatório NÃO somados.',
                 'es': 'Escenario A (integral): recomponer {a} ha · Escenario B (PRA-PR, exige CAR hasta 31/12/2023): {b} ha. Candidatos DEM a nascente (+{c} ha si se confirman) y faja del reservorio NO sumados.'},
    # M06
    'm06_t': {'pt': 'M06 · Reserva Legal — proposta de localização', 'es': 'M06 · Reserva Legal — propuesta de localización'},
    'm06_s': {'pt': 'Art. 12 (20%) · art. 15 (APP computa) · art. 14 (contiguidade) · sujeita à aprovação do IAT',
              'es': 'Art. 12 (20%) · art. 15 (APP computa) · art. 14 (contigüidad) · sujeta a aprobación del IAT'},
    'rl_rem': {'pt': 'Remanescente fora da APP — {ha} ha', 'es': 'Remanente fuera de la APP — {ha} ha'},
    'rl_app': {'pt': 'APP vegetada computável (art. 15) — {ha} ha', 'es': 'APP vegetada computable (art. 15) — {ha} ha'},
    'rl_app_rec': {'pt': 'APP a recompor incluída — {ha} ha', 'es': 'APP a recomponer incluida — {ha} ha'},
    'rl_corr': {'pt': 'Corredor de recomposição proposto — {ha} ha', 'es': 'Corredor de recomposición propuesto — {ha} ha'},
    'rl_lim': {'pt': 'Reserva Legal Proposta — {ha} ha', 'es': 'Reserva Legal Propuesta — {ha} ha'},
    'rl_kpi': {'pt': [['RL exigida (20%)', '{ex} ha'], ['Disponível (com APP, art. 15)', '{disp} ha'],
                      ['Déficit', '{def} ha'], ['Déficit conservador (sem frag. 13)', '{cons} ha'],
                      ['RL proposta', '{prop} ha']],
               'es': [['RL exigida (20%)', '{ex} ha'], ['Disponible (con APP, art. 15)', '{disp} ha'],
                      ['Déficit', '{def} ha'], ['Déficit conservador (sin frag. 13)', '{cons} ha'],
                      ['RL propuesta', '{prop} ha']]},
    'rl_status': {'pt': 'PROPOSTA sujeita à aprovação do IAT; a APP só computa na RL com CAR inscrito e APP conservada ou em recuperação (art. 15).',
                  'es': 'PROPUESTA sujeta a aprobación del IAT; la APP solo computa en la RL con CAR inscrito y APP conservada o en recuperación (art. 15).'},
    'car_short': {'pt': {
        ("APP – Nascente ou olho d'água perene", 'conforme'): "APP nascente (conforme)",
        ("APP – Nascente ou olho d'água perene", 'a recompor'): "APP nascente (a recompor)",
        ("APP – Curso d'água natural de até 10 metros", 'conforme'): "APP curso ≤ 10 m (conforme)",
        ("APP – Curso d'água natural de até 10 metros", 'a recompor'): "APP curso ≤ 10 m (a recompor)",
        ("Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais", 'espelho d agua'): "Reservatório artificial (espelho)",
        ('Remanescente de Vegetação Nativa', 'floresta fora da APP'): 'Remanescente de Veg. Nativa',
        ('Área Consolidada', 'uso agricola'): 'Área Consolidada – agrícola',
        ('Área Consolidada', 'silvicultura'): 'Área Consolidada – silvicultura'},
        'es': {
        ("APP – Nascente ou olho d'água perene", 'conforme'): "APP nascente (conforme)",
        ("APP – Nascente ou olho d'água perene", 'a recompor'): "APP nascente (a recomponer)",
        ("APP – Curso d'água natural de até 10 metros", 'conforme'): "APP curso ≤ 10 m (conforme)",
        ("APP – Curso d'água natural de até 10 metros", 'a recompor'): "APP curso ≤ 10 m (a recomponer)",
        ("Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais", 'espelho d agua'): "Reservatório artificial (espejo)",
        ('Remanescente de Vegetação Nativa', 'floresta fora da APP'): 'Remanescente de Veg. Nativa',
        ('Área Consolidada', 'uso agricola'): 'Área Consolidada – agrícola',
        ('Área Consolidada', 'silvicultura'): 'Área Consolidada – silvicultura'}},
    # M07
    'm07_t': {'pt': 'M07 · Uso e cobertura — nomenclatura CAR/SICAR', 'es': 'M07 · Uso y cobertura — nomenclatura CAR/SICAR'},
    'm07_s': {'pt': 'Polígonos sem sobreposição, 100% do imóvel · IN MMA 2/2014 · Manual SICAR',
              'es': 'Polígonos sin superposición, 100% del inmueble · IN MMA 2/2014 · Manual SICAR'},
    'tab_car': {'pt': ['Classe CAR / subclasse', 'ha'], 'es': ['Clase CAR / subclase', 'ha']},
    'soma': {'pt': 'Soma', 'es': 'Suma'},
    'rl_prop_ctx': {'pt': 'Reserva Legal Proposta (contorno)', 'es': 'Reserva Legal Propuesta (contorno)'},
    'car_names': {'pt': {
        ("APP – Nascente ou olho d'água perene", 'conforme'): "APP – Nascente (conforme)",
        ("APP – Nascente ou olho d'água perene", 'a recompor'): "APP – Nascente (a recompor)",
        ("APP – Curso d'água natural de até 10 metros", 'conforme'): "APP – Curso d'água ≤ 10 m (conforme)",
        ("APP – Curso d'água natural de até 10 metros", 'a recompor'): "APP – Curso d'água ≤ 10 m (a recompor)",
        ("Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais", 'espelho d agua'): "Reservatório artificial (barramento) – espelho",
        ('Remanescente de Vegetação Nativa', 'floresta fora da APP'): 'Remanescente de Vegetação Nativa',
        ('Área Consolidada', 'uso agricola'): 'Área Consolidada – uso agrícola',
        ('Área Consolidada', 'silvicultura'): 'Área Consolidada – silvicultura'},
        'es': {
        ("APP – Nascente ou olho d'água perene", 'conforme'): "APP – Nascente (conforme)",
        ("APP – Nascente ou olho d'água perene", 'a recompor'): "APP – Nascente (a recomponer)",
        ("APP – Curso d'água natural de até 10 metros", 'conforme'): "APP – Curso de agua ≤ 10 m (conforme)",
        ("APP – Curso d'água natural de até 10 metros", 'a recompor'): "APP – Curso de agua ≤ 10 m (a recomponer)",
        ("Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais", 'espelho d agua'): "Reservatório artificial (represamiento) – espejo",
        ('Remanescente de Vegetação Nativa', 'floresta fora da APP'): 'Remanescente de Vegetação Nativa',
        ('Área Consolidada', 'uso agricola'): 'Área Consolidada – uso agrícola',
        ('Área Consolidada', 'silvicultura'): 'Área Consolidada – silvicultura'}},
}
LANG = 'pt'


def t(k):
    return T[k][LANG]


def fmt(x, d=2):
    """Formato brasileiro/espanhol: coma decimal, punto de miles."""
    s = f'{float(x):,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


def fmt_utm(v, _pos=None):
    return f'{int(round(v)):,}'.replace(',', '.')


# ------------------------------------------------------------------ dados ----
class Dados:
    def __init__(self):
        self.res = leer_json(RESULTADOS_JSON)
        self.prop = gpd.read_file(PROPIEDAD_GEOJSON).to_crs(CRS_METRICO)
        self.prop_u = unary_union(self.prop.geometry)
        A = lambda n: gpd.read_file(os.path.join(ANALISIS, n + '.geojson'))
        self.hidro = A('hidrografia_consolidada')
        self.nasc = A('nascentes_consolidadas')
        self.dem_red = A('hidro_dem_red')
        self.agua_s2 = A('agua_s2_2026-08-29')
        self.massas = A('massas_dagua_propriedade')
        self.frag = A('fragmentos_floresta')
        self.mud = A('mudanca_2008_2025')
        self.rl = A('RL_proposta')
        self.corr = A('RL_corredor_recomposicao')
        self.car = A('mapa_uso_car')
        self.veg = A('vegetacao_nativa_10m')
        self.muni = gpd.read_file(os.path.join(DATOS_EXT, 'IBGE_municipio_4126009.geojson')).to_crs(CRS_METRICO)
        self.fbds_ctx = gpd.read_file(os.path.join(DATOS_EXT, 'IAT_FBDS_rios_ate10m.geojson')).to_crs(CRS_METRICO)
        self.serie = leer_json(os.path.join(ANALISIS, 'serie_ndvi_fragmentos_24m.json'))
        with rasterio.open(R['rgb']) as ds:
            self.aoi_bounds = ds.bounds
        # geometrias SOLO para dibujo (no generan cifras)
        fb = self.hidro[(self.hidro.fonte == 'FBDS')]
        fb_in = fb[fb.dentro_propriedade]
        n_in = self.nasc[(self.nasc.fonte == 'FBDS') & self.nasc.dentro_propriedade]
        self.app30 = unary_union([unary_union(fb.geometry).buffer(30), unary_union(n_in.geometry).buffer(50)]).intersection(self.prop_u)
        self.faixa20 = unary_union([unary_union(fb.geometry).buffer(20), unary_union(n_in.geometry).buffer(15)]).intersection(self.prop_u)
        m = unary_union(self.massas.geometry)
        self.reserv_faixa = m.buffer(30).difference(m).intersection(self.prop_u)
        log('  [dibujo] app30 %.2f ha (JSON: %.2f) · faixa20 %.2f ha · faixa reserv %.2f ha' % (
            self.app30.area / 1e4, self.res['legal']['app_total_exigivel']['ha'],
            self.faixa20.area / 1e4, self.reserv_faixa.area / 1e4))


# ------------------------------------------------------------------ mapa -----
class Mapa:
    """Figura con mapa (izquierda), columna de leyenda (derecha), titulo, grilla UTM, norte, escala."""

    def __init__(self, layout, titulo, subtitulo, extent, leg_min_cm=4.8, notas_abajo=False):
        self.layout = layout
        self.notas_abajo = notas_abajo
        x0, y0, x1, y1 = extent
        ratio = (x1 - x0) / (y1 - y0)
        if layout == 'V':
            W, H = 15.0, 22.0
            title_h, map_l, map_b, top_pad = 1.55, 1.45, 1.35, 0.35
        else:
            W, H = 29.7, 21.0
            title_h, map_l, map_b, top_pad = 2.0, 1.9, 1.5, 0.5
        map_h = H - title_h - map_b - top_pad
        max_w = W - map_l - 0.9 - 0.4 - leg_min_cm
        map_w = map_h * ratio
        if map_w > max_w:
            map_w = max_w
            map_h = map_w / ratio
            if layout == 'V':          # figura mas baja: no dejar aire vacio
                H = title_h + map_h + map_b + top_pad + (1.45 if notas_abajo else 0)
                if notas_abajo:
                    map_b += 1.45
        self.W, self.H = W, H
        self.fig = plt.figure(figsize=(W / 2.54, H / 2.54))
        self.ax = self.fig.add_axes([map_l / W, map_b / H, map_w / W, map_h / H])
        leg_l = map_l + map_w + 0.85
        self.leg_w_cm = min(W - leg_l - 0.4, 12.5 if layout == 'H' else 99)
        self.leg = self.fig.add_axes([leg_l / W, map_b / H, self.leg_w_cm / W, map_h / H])
        self.leg.axis('off')
        self.map_h_cm, self.map_w_cm = map_h, map_w
        self.extent = extent
        self.ax.set_xlim(x0, x1); self.ax.set_ylim(y0, y1); self.ax.set_aspect('equal')
        # titulo + barra de marca
        fs_t = 11.5 if layout == 'V' else 16
        fs_s = 7.2 if layout == 'V' else 9.5
        self.fig.text(map_l / W, 1 - 0.45 / H, titulo, fontsize=fs_t, fontweight='bold', color=AZUL, va='top')
        self.fig.text(map_l / W, 1 - (0.45 + (0.55 if layout == 'V' else 0.8)) / H, subtitulo, fontsize=fs_s, color='#444444', va='top')
        self.fig.add_artist(plt.Line2D([map_l / W, 1 - 0.4 / W], [1 - (title_h - 0.12) / H] * 2, color=TEAL, lw=1.4))
        self.fig.add_artist(plt.Line2D([1 - 3.5 / W, 1 - 0.4 / W], [1 - (title_h - 0.12) / H] * 2, color=LIMA, lw=1.4))
        self.fig.text(1 - 0.4 / W, 0.22 / H, t('marca'), fontsize=5.8, color='#666666', ha='right', va='bottom')
        self._ycur = 1.0
        self.fs = 6.6 if layout == 'V' else 7.6

    # ---- capas base ----
    def fondo(self, dados, gamma=1.0, gain=1.15):
        x0, y0, x1, y1 = self.extent
        with rasterio.open(R['rgb']) as ds:
            bx0, by0 = max(x0, ds.bounds.left), max(y0, ds.bounds.bottom)
            bx1, by1 = min(x1, ds.bounds.right), min(y1, ds.bounds.top)
            win = from_bounds(bx0, by0, bx1, by1, ds.transform)
            img = ds.read(window=win).astype(np.float32) / 255.0
            tr = ds.window_transform(win)
            h, w = img.shape[1], img.shape[2]
            ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
        img = np.clip((img ** gamma) * gain, 0, 1)
        self.ax.imshow(np.moveaxis(img, 0, -1), extent=ex, interpolation='nearest', zorder=1)
        self.ax.set_facecolor('#DDDDDD')

    def propriedade(self, dados, lw=None, zorder=30):
        lw = lw or (1.8 if self.layout == 'V' else 2.2)
        dados.prop.boundary.plot(ax=self.ax, color='black', lw=lw + 1.2, zorder=zorder)
        dados.prop.boundary.plot(ax=self.ax, color=COL['prop'], lw=lw, zorder=zorder + 1)

    def grilla(self, paso=500):
        x0, y0, x1, y1 = self.extent
        xt = np.arange(np.ceil(x0 / paso) * paso, x1 + 1, paso)
        yt = np.arange(np.ceil(y0 / paso) * paso, y1 + 1, paso)
        self.ax.set_xticks(xt); self.ax.set_yticks(yt)
        self.ax.xaxis.set_major_formatter(FuncFormatter(fmt_utm))
        self.ax.yaxis.set_major_formatter(FuncFormatter(fmt_utm))
        self.ax.tick_params(labelsize=5.6, length=2, pad=1.5, colors='#333333')
        for lab in self.ax.get_yticklabels():
            lab.set_rotation(90); lab.set_va('center')
        self.ax.grid(True, color='white', alpha=0.55, lw=0.5, ls='--', zorder=20)
        self.ax.set_xlabel('E (m) — UTM 22S', fontsize=5.6, labelpad=1)
        self.ax.set_ylabel('N (m) — UTM 22S', fontsize=5.6, labelpad=1)
        for s in self.ax.spines.values():
            s.set_linewidth(0.8)

    def norte_escala(self, bar_m=None):
        x0, y0, x1, y1 = self.extent
        dx, dy = x1 - x0, y1 - y0
        # norte (arriba-derecha)
        xn, yn = x1 - 0.12 * dx, y1 - 0.03 * dy
        self.ax.annotate('', xy=(xn, yn), xytext=(xn, yn - 0.05 * dy),
                         arrowprops=dict(facecolor='white', edgecolor='black', width=3, headwidth=8, headlength=7, lw=0.6), zorder=60)
        self.ax.text(xn, yn - 0.062 * dy, 'N', ha='center', va='top', fontsize=7, fontweight='bold',
                     color='black', zorder=60, bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
        # escala (abajo-izquierda)
        if bar_m is None:
            bar_m = 250 if dx < 1500 else 500
        xs, ys = x0 + 0.06 * dx, y0 + 0.025 * dy
        hb = 0.006 * dy
        for i in range(2):
            self.ax.add_patch(plt.Rectangle((xs + i * bar_m / 2, ys), bar_m / 2, hb, fc='white' if i else 'black',
                                            ec='black', lw=0.6, zorder=60))
        for i, v in enumerate([0, bar_m // 2, bar_m]):
            self.ax.text(xs + v, ys + hb * 1.4, f'{v}' + (' m' if i == 2 else ''), ha='center', va='bottom', fontsize=5.2, zorder=60,
                         bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.8))

    # ---- columna de leyenda ----
    def _wrap(self, s, factor=1.0):
        n = int(self.leg_w_cm / (0.155 * factor) * (6.6 / self.fs))
        return '\n'.join(textwrap.fill(p, max(18, n)) for p in s.split('\n'))

    def leg_titulo(self, txt):
        self.leg.text(0, self._ycur, txt, fontsize=self.fs + 1.2, fontweight='bold', color=AZUL, va='top', transform=self.leg.transAxes)
        self._ycur -= (0.42 / self.map_h_cm)

    def leg_items(self, handles, labels, ncol=1):
        labels = [self._wrap(l, 1.25) for l in labels]
        lg = self.leg.legend(handles, labels, loc='upper left', bbox_to_anchor=(-0.02, self._ycur), fontsize=self.fs,
                             frameon=False, ncol=ncol, handlelength=1.9, handleheight=1.1, labelspacing=0.45,
                             borderaxespad=0, borderpad=0)
        self.leg.add_artist(lg)
        self.fig.canvas.draw()
        bb = lg.get_window_extent(self.fig.canvas.get_renderer()).transformed(self.leg.transAxes.inverted())
        self._ycur = bb.y0 - 0.18 / self.map_h_cm

    def leg_tabla(self, rows, col_w=None, bold_last=False, header=True):
        n = len(rows)
        row_h = (0.36 if self.layout == 'V' else 0.44) / self.map_h_cm
        h = n * row_h
        col_w = col_w or [0.66, 0.34][:len(rows[0])]
        tab = self.leg.table(cellText=rows, colWidths=col_w, bbox=[0, self._ycur - h, 1, h], cellLoc='left')
        tab.auto_set_font_size(False); tab.set_fontsize(self.fs - 0.3)
        for (r, c), cell in tab.get_celld().items():
            cell.set_linewidth(0.3); cell.set_edgecolor('#BBBBBB')
            cell.PAD = 0.03
            if c > 0:
                cell.get_text().set_ha('right')
            if header and r == 0:
                cell.set_facecolor(TEAL); cell.get_text().set_color('white'); cell.get_text().set_fontweight('bold')
            elif bold_last and r == n - 1:
                cell.set_facecolor('#EAF6F4'); cell.get_text().set_fontweight('bold')
            elif r % 2 == 0:
                cell.set_facecolor('#F5F7FA')
        self._ycur -= h + 0.25 / self.map_h_cm

    def leg_texto(self, txt, fs=None, color=GRIS, bold=False):
        fs = fs or self.fs - 0.3
        s = self._wrap(txt, fs / self.fs)
        tx = self.leg.text(0, self._ycur, s, fontsize=fs, color=color, va='top', transform=self.leg.transAxes,
                           fontweight='bold' if bold else 'normal', linespacing=1.25)
        self.fig.canvas.draw()
        bb = tx.get_window_extent(self.fig.canvas.get_renderer()).transformed(self.leg.transAxes.inverted())
        self._ycur = bb.y0 - 0.2 / self.map_h_cm

    def leg_espacio(self, cm=0.3):
        self._ycur -= cm / self.map_h_cm

    def leg_inset(self, h_cm, w_frac=1.0):
        """Devuelve un axes dentro de la columna de leyenda (para insets y graficos)."""
        h = h_cm / self.map_h_cm
        bb = self.leg.get_position()
        ax = self.fig.add_axes([bb.x0, bb.y0 + (self._ycur - h) * bb.height, bb.width * w_frac, h * bb.height])
        self._ycur -= h + 0.3 / self.map_h_cm
        return ax

    def notas(self):
        txt = t('fonte_s2') + ' · ' + t('notas')
        if self.notas_abajo:
            s = chr(10).join(textwrap.wrap(txt, int((self.W - 2.0) / 0.13)))
            self.fig.text(1.45 / self.W, 0.55 / self.H, s, fontsize=self.fs - 0.9, color='#444444', va='bottom',
                          linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
            return
        s = self._wrap(txt, 0.92)
        self.leg.text(0, 0.0, s, fontsize=self.fs - 0.9, color='#444444', va='bottom', transform=self.leg.transAxes,
                      linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))

    def guardar(self, nome, subdir=''):
        out_dir = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', subdir)
        os.makedirs(out_dir, exist_ok=True)
        ruta = os.path.join(out_dir, nome + '.png')
        self.fig.savefig(ruta, dpi=DPI, facecolor='white')
        plt.close(self.fig)
        log('  -> %s' % ruta)
        return ruta


# ---------------------------------------------------------- helpers dibujo ---
def poly_patches(ax, geoms, **kw):
    """Dibuja (Multi)Polygons como patches (fill/hatch/edge)."""
    for g in geoms:
        if g is None or g.is_empty:
            continue
        parts = g.geoms if hasattr(g, 'geoms') else [g]
        for p in parts:
            if p.geom_type != 'Polygon':
                continue
            ax.add_patch(MPolygon(np.asarray(p.exterior.coords), closed=True, **kw))
            for r in p.interiors:      # agujeros: pintar con el color de fondo no es posible; se dibuja borde
                ax.add_patch(MPolygon(np.asarray(r.coords), closed=True, fc='none', ec=kw.get('ec', 'none'), lw=kw.get('lw', 0), zorder=kw.get('zorder', 1)))


def plot_lines(ax, geoms, **kw):
    """Lineas con matplotlib puro (geopandas no acepta linestyle en tupla)."""
    for g in geoms:
        if g is None or g.is_empty:
            continue
        parts = g.geoms if hasattr(g, 'geoms') else [g]
        for p in parts:
            xy = np.asarray(p.coords)
            ax.plot(xy[:, 0], xy[:, 1], **kw)


def raster_clases(ax, ruta, extent, cmap_dict, alpha=1.0, zorder=5, clip=None, banda=1):
    """Pinta un raster categorico con un dict {valor: rgba}; valores ausentes = transparente."""
    x0, y0, x1, y1 = extent
    with rasterio.open(ruta) as ds:
        win = from_bounds(max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top), ds.transform)
        a = ds.read(banda, window=win)
        tr = ds.window_transform(win)
        h, w = a.shape
        ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
        if clip is not None:
            m = features.rasterize([(clip, 1)], out_shape=a.shape, transform=tr, fill=0, dtype=np.uint8)
            a = np.where(m == 1, a, 0)
    rgba = np.zeros(a.shape + (4,), dtype=np.float32)
    for v, col in cmap_dict.items():
        c = matplotlib.colors.to_rgba(col)
        rgba[a == v] = (c[0], c[1], c[2], c[3] * alpha)
    ax.imshow(rgba, extent=ex, interpolation='nearest', zorder=zorder)
    return a, tr


def extent_prop(dados, margen):
    x0, y0, x1, y1 = dados.prop.total_bounds
    return (x0 - margen, y0 - margen, x1 + margen, y1 + margen)


def ext_layout(dados, layout, mv=200, mh=450):
    return extent_prop(dados, mv if layout == 'V' else mh)


# ---------------------------------------------------------- grafico NDVI -----
def grafico_ndvi(dados, ax=None, compacto=False):
    S = dados.serie['serie']
    meses = [r['mes'] for r in S]
    x = np.arange(len(meses))
    propio = ax is None
    if propio:
        fig = plt.figure(figsize=(15 / 2.54, 9.0 / 2.54))
        ax = fig.add_axes([0.075, 0.40, 0.9, 0.47])
    fs = 5.6 if compacto else 7
    orden = ['frag13_ribeira', 'frag2_mata_antiga', 'frag30', 'lavoura_norte', 'lavoura_sul']
    for k in orden:
        y = [r[k] for r in S]
        lw = 2.2 if k == 'frag13_ribeira' else 1.4
        ls = '-' if k.startswith('frag') else '--'
        ax.plot(x, y, color=SERIE_COL[k], lw=lw, ls=ls, marker='o', ms=2.2 if not compacto else 1.4,
                label=t('serie')[k], zorder=3 + (k == 'frag13_ribeira'))
    ax.set_ylim(0, 1.32 if compacto else 1.0); ax.set_xlim(-0.5, len(x) - 0.5 + (0 if compacto else 0.2))
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels([fmt(v, 1) for v in [0, 0.2, 0.4, 0.6, 0.8, 1.0]], fontsize=fs)
    ax.set_xticks(x[::3 if compacto else 2])
    ax.set_xticklabels([meses[i] for i in range(0, len(meses), 3 if compacto else 2)], fontsize=fs - 0.4, rotation=90 if compacto else 45, ha='right' if not compacto else 'center')
    ax.grid(True, axis='y', color='#DDDDDD', lw=0.5); ax.set_axisbelow(True)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=2, pad=1.5)
    ax.set_ylabel(t('ndvi'), fontsize=fs)
    f13 = [r['frag13_ribeira'] for r in S]
    lav = [r['lavoura_norte'] for r in S] + [r['lavoura_sul'] for r in S]
    if propio:
        fig.text(0.075, 0.965, t('g01_t'), fontsize=8.5, fontweight='bold', color=AZUL, va='top')
        fig.text(0.075, 0.895, t('g01_s'), fontsize=6.2, color='#444444', va='top')
        ax.legend(fontsize=fs - 0.6, frameon=False, loc='upper left', ncol=3, bbox_to_anchor=(0, -0.40), handlelength=2.2, columnspacing=1.2)
        fig.text(0.075, 0.06, textwrap.fill(t('g01_nota').format(mn=fmt(min(f13)), mx=fmt(max(f13)), lmn=fmt(min(lav)), lmx=fmt(max(lav))), 118),
                 fontsize=5.8, color='#333333', va='bottom', linespacing=1.3)
        fig.text(0.975, 0.015, t('marca'), fontsize=5, color='#777777', ha='right', va='bottom')
        return fig
    else:
        ax.set_title(t('g01_ins'), fontsize=fs + 0.6, fontweight='bold', color=AZUL, loc='left', pad=2)
        ax.legend(fontsize=fs - 0.8, frameon=False, loc='upper left', ncol=2, handlelength=1.8, columnspacing=0.8, labelspacing=0.2, borderaxespad=0.2)
        return ax


# ---------------------------------------------------------------- mapas ------
def M01(d, layout):
    b = d.aoi_bounds
    ext = (b.left, b.bottom, b.right, b.top)
    M = Mapa(layout, t('m01_t'), t('m01_s'), ext, leg_min_cm=5.2, notas_abajo=(layout == 'V'))
    M.fondo(d)
    d.fbds_ctx.plot(ax=M.ax, color=COL['fbds'], lw=0.7, zorder=10)
    M.ax.add_patch(plt.Rectangle((b.left + 15, b.bottom + 15), b.right - b.left - 30, b.top - b.bottom - 30, fc='none', ec='white', lw=1.0, ls='--', zorder=25))
    M.propriedade(d)
    M.grilla(1000 if layout == 'V' else 500)
    M.norte_escala(1000)
    # rotulos de cursos con nombre (otto/ANA)
    nomes = d.hidro[(d.hidro.nome != '') & (d.hidro.fonte == 'ANA')]
    for _, r in nomes.iterrows():
        c = r.geometry.interpolate(0.5, normalized=True)
        M.ax.text(c.x, c.y + 40, r.nome, fontsize=5, color='white', ha='center', style='italic', zorder=26,
                  bbox=dict(boxstyle='round,pad=0.15', fc=COL['fbds'], ec='none', alpha=0.75))
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['prop'], lw=2.2, path_effects=None),
                 Line2D([], [], color='white', lw=1, ls='--'),
                 Line2D([], [], color=COL['fbds'], lw=1)],
                [t('prop'), t('aoi'), t('fbds_ctx')])
    for lin in t('ficha_m01'):
        M.leg_texto(lin)
    M.leg_espacio(0.2)
    M.leg_texto(t('inset_muni'), bold=True, color=AZUL)
    axi = M.leg_inset(5.0 if layout == 'V' else 7.5)
    d.muni.plot(ax=axi, fc='#EAF6F4', ec=TEAL, lw=0.8)
    c = d.prop_u.centroid
    axi.plot(c.x, c.y, marker='*', ms=9, color='#D32F2F', mec='black', mew=0.4)
    axi.text(c.x, c.y - 900, t('faz'), fontsize=5.5, ha='center', va='top', color='#D32F2F', fontweight='bold')
    mb = d.muni.total_bounds
    axi.set_xlim(mb[0] - 500, mb[2] + 500); axi.set_ylim(mb[1] - 1200, mb[3] + 2600); axi.set_aspect('equal')
    axi.set_xticks([]); axi.set_yticks([])
    for s in axi.spines.values():
        s.set_color('#BBBBBB'); s.set_linewidth(0.5)
    axi.text(0.02, 0.98, t('muni'), transform=axi.transAxes, fontsize=5, va='top', color='#333333')
    axi.text(0.02, 0.02, 'EPSG:31982', transform=axi.transAxes, fontsize=4.5, va='bottom', color='#666666')
    M.leg_texto(t('sem_pr'), fs=M.fs - 1.2, color='#777777')
    M.notas()
    return M


def M02(d, layout):
    ext = ext_layout(d, layout)
    M = Mapa(layout, t('m02_t'), t('m02_s'), ext)
    M.fondo(d)
    ax = M.ax
    plot_lines(ax, d.dem_red.geometry, color=COL['dem'], lw=0.9, ls=(0, (2, 1.5)), zorder=8)
    fb = d.hidro[d.hidro.fonte == 'FBDS']
    fb[~fb.dentro_propriedade].plot(ax=ax, color=COL['fbds'], lw=0.9, alpha=0.6, zorder=9)
    fb[fb.dentro_propriedade & (fb.regime != 'perene')].plot(ax=ax, color=COL['fbds'], lw=1.6, zorder=10)
    fb[fb.dentro_propriedade & (fb.regime == 'perene')].plot(ax=ax, color=COL['fbds_perene'], lw=2.4, zorder=11)
    ag = d.agua_s2[~d.agua_s2.possivel_falso_positivo]
    ag.plot(ax=ax, fc=COL['agua_s2'], ec='none', alpha=0.9, zorder=12)
    d.massas.boundary.plot(ax=ax, color=COL['massa'], lw=1.2, zorder=13)
    nf = d.nasc[d.nasc.fonte == 'FBDS']
    ax.scatter(nf.geometry.x, nf.geometry.y, s=34, marker='o', c=COL['nasc'], edgecolors='white', linewidths=0.8, zorder=15)
    nd = d.nasc[d.nasc.candidato_dem]
    ax.scatter(nd.geometry.x, nd.geometry.y, s=48, marker='^', c=COL['cand'], edgecolors='black', linewidths=0.6, zorder=16)
    for _, r in nd.iterrows():
        ax.text(r.geometry.x + 25, r.geometry.y, r.id_fonte, fontsize=5.5, color='black', va='center', zorder=17,
                bbox=dict(boxstyle='round,pad=0.12', fc=COL['cand'], ec='none', alpha=0.85))
    for _, r in d.massas.iterrows():
        c = r.geometry.centroid
        ax.annotate('%s %d\n%s ha (FBDS 2013)' % (t('reserv'), r.massa_id, fmt(r.area_fbds_2013_ha)),
                    xy=(c.x, c.y), xytext=(c.x + (140 if r.massa_id == 20452 else -60), c.y + (110 if r.massa_id == 20452 else -140)),
                    fontsize=5.2, ha='center', zorder=18, arrowprops=dict(arrowstyle='-', lw=0.5, color='black'),
                    bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=COL['massa'], lw=0.6, alpha=0.92))
    nomes = d.hidro[(d.hidro.nome != '') & (d.hidro.fonte == 'ANA')]
    for _, r in nomes.iterrows():
        c = r.geometry.interpolate(0.5, normalized=True)
        ax.text(c.x, c.y + 35, r.nome, fontsize=5, color='white', ha='center', style='italic', zorder=26,
                bbox=dict(boxstyle='round,pad=0.15', fc=COL['fbds'], ec='none', alpha=0.75))
    M.propriedade(d)
    M.grilla(); M.norte_escala()
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['prop'], lw=2.2),
                 Line2D([], [], color=COL['fbds_perene'], lw=2.4),
                 Line2D([], [], color=COL['fbds'], lw=1.6),
                 Line2D([], [], color=COL['fbds'], lw=0.9, alpha=0.6),
                 Line2D([], [], color=COL['dem'], lw=0.9, ls=(0, (2, 1.5))),
                 Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc'], markeredgecolor='white', ms=6),
                 Line2D([], [], marker='^', color='none', markerfacecolor=COL['cand'], markeredgecolor='black', ms=7),
                 Patch(fc=COL['agua_s2']),
                 Patch(fc='none', ec=COL['massa'], lw=1.2)],
                [t('prop'), t('fbds_perene'), t('fbds_nc'), t('fbds_fora'), t('dem_red'), t('nasc_fbds'), t('cand_dem'), t('agua_s2'), t('massa')])
    H = d.res['hidrografia']
    tf = H['tabla_fontes_propriedade']
    rows = list(t('tab_hidro'))
    for k, lab in [('FBDS', 'FBDS/IAT 2013'), ('otto', 'IAT otto 2020'), ('ANA', 'ANA BHO 2017'), ('IBGE', 'IBGE BC250'), ('DEM', 'DEM GLO-30')]:
        rows.append([lab, fmt(tf[k]['km_dentro_propriedade'], 3), str(tf[k]['n_tramos_dentro'])])
    M.leg_tabla(rows, col_w=[0.5, 0.3, 0.2])
    M.leg_texto(t('nasc_lin').format(n=H['nascentes']['fbds_dentro'], c=H['nascentes']['candidatos_dem_dentro']))
    g = H['dem']['consistencia_fbds_vs_dem_global_propriedade']
    M.leg_texto(t('consist').format(m=fmt(g['dist_mediana_m'], 1), p=fmt(g['dist_p90_m'], 1)))
    M.notas()
    return M


def M03(d, layout):
    ext = ext_layout(d, layout)
    M = Mapa(layout, t('m03_t'), t('m03_s'), ext, leg_min_cm=5.6)
    M.fondo(d)
    ax = M.ax
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), ext,
                  {1: COL['floresta'], 2: COL['agua'], 3: COL['antrop'] + '99', 4: COL['silv']}, alpha=0.85, zorder=5)
    # silvicultura rayada
    sv = d.veg[d.veg.classe == 'SILVICULTURA']
    poly_patches(ax, sv.geometry, fc='none', ec='#4E4E00', hatch='////', lw=0.3, zorder=6)
    d.frag.boundary.plot(ax=ax, color='white', lw=1.4, zorder=12)
    d.frag.boundary.plot(ax=ax, color=LIMA, lw=0.7, zorder=13)
    off = {2: (230, -150), 13: (0, 0), 30: (-40, -190)}
    for _, r in d.frag.iterrows():
        g = r.geometry.intersection(d.prop_u)
        c = (g if not g.is_empty else r.geometry).representative_point()
        dx_, dy_ = off.get(int(r.frag_id), (0, 0))
        ax.annotate(t('frag_lbl').format(id=r.frag_id, ha=fmt(r.area_dentro_propriedade_ha)), xy=(c.x, c.y),
                    xytext=(c.x + dx_, c.y + dy_), fontsize=5.6, ha='center', va='center', zorder=20, fontweight='bold',
                    arrowprops=dict(arrowstyle='-', lw=0.6, color='black') if (dx_ or dy_) else None,
                    bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['floresta'], lw=0.7, alpha=0.93))
    M.propriedade(d)
    M.grilla(); M.norte_escala()
    cb = d.res['vegetacao']['cobertura_propriedade']['por_fonte_ha']['RF_10m']
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['prop'], lw=2.2),
                 Patch(fc=COL['floresta']),
                 Patch(fc=COL['silv'], hatch='////', ec='#4E4E00'),
                 Patch(fc=COL['agua']),
                 Patch(fc=COL['antrop'], ec='#BBBBBB'),
                 Patch(fc='none', ec=LIMA, lw=1.5)],
                [t('prop'), t('cl_flor').format(ha=fmt(cb['FLORESTA_NATIVA'])), t('cl_silv').format(ha=fmt(cb['SILVICULTURA'])),
                 t('cl_agua').format(ha=fmt(cb['AGUA'])), t('cl_antr').format(ha=fmt(cb['AREA_ANTROPIZADA'])), t('frag')])
    rows = [['Frag.', 'ha', 'NDVI', 'MB 2008'] if LANG == 'pt' else ['Frag.', 'ha', 'NDVI', 'MB 2008']]
    for f in d.res['vegetacao']['fragmentos']['lista']:
        rows.append([str(f['frag_id']), fmt(f['area_dentro_propriedade_ha']), fmt(f['ndvi_medio'], 3), fmt(100 * f['frac_floresta_mb_2008'], 0) + '%'])
    M.leg_tabla(rows, col_w=[0.2, 0.25, 0.27, 0.28])
    axg = M.leg_inset(5.2 if layout == 'V' else 7.6)
    grafico_ndvi(d, ax=axg, compacto=True)
    M.notas()
    return M


def M04(d, layout):
    ext = ext_layout(d, layout)
    M = Mapa(layout, t('m04_t'), t('m04_s'), ext)
    M.fondo(d)
    ax = M.ax
    cores = {'floresta_estavel_2008_2025': COL['persist'], 'regeneracao_pos_2008': COL['regen'],
             'supressao_pos_2008': COL['supr'], 'agua': COL['agua'], 'antropico_estavel': COL['antrop'] + '77'}
    for cl, col in cores.items():
        sub = d.mud[d.mud.classe == cl]
        if len(sub):
            sub.plot(ax=ax, fc=col, ec='none', alpha=0.9 if cl != 'antropico_estavel' else 1.0, zorder=5)
    # Hansen lossyear (30 m) en el extent: contorno + ano
    x0, y0, x1, y1 = ext
    with rasterio.open(R['hansen']) as ds:
        win = from_bounds(max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top), ds.transform)
        ly = ds.read(2, window=win); tr = ds.window_transform(win)
    for geom, v in features.shapes(ly.astype(np.int32), mask=(ly > 0) & (ly < 100), transform=tr):
        g = shape(geom)
        dentro = g.representative_point().within(d.prop_u)
        poly_patches(ax, [g], fc='none', ec=COL['hansen'], lw=1.0 if dentro else 0.5, hatch='xx' if dentro else None, zorder=9)
        if dentro:
            c = g.representative_point()
            ax.text(c.x, c.y, str(2000 + int(v)), fontsize=5, color='white', ha='center', va='center', zorder=10,
                    bbox=dict(boxstyle='round,pad=0.12', fc=COL['hansen'], ec='none', alpha=0.9))
    fl = d.veg[(d.veg.classe == 'FLORESTA_NATIVA') & d.veg.intersecta_propriedade]
    fl.boundary.plot(ax=ax, color='white', lw=0.6, ls='-', zorder=8)
    M.propriedade(d)
    M.grilla(); M.norte_escala()
    V = d.res['vegetacao']['mudanca_2008_2025']
    ha = V['ha_por_classe']
    hz = V['hansen']['dentro']
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['prop'], lw=2.2),
                 Patch(fc=COL['persist']), Patch(fc=COL['regen']), Patch(fc=COL['supr']), Patch(fc=COL['agua']),
                 Patch(fc=COL['antrop'], ec='#BBBBBB'),
                 Patch(fc='none', ec=COL['hansen'], hatch='xx', lw=1),
                 Line2D([], [], color='white', lw=0.8)],
                [t('prop'), t('mb_persist').format(ha=fmt(ha['floresta_estavel_2008_2025'])),
                 t('mb_regen').format(ha=fmt(ha['regeneracao_pos_2008'])), t('mb_supr').format(ha=fmt(ha['supressao_pos_2008'])),
                 t('mb_agua').format(ha=fmt(ha['agua'])), t('mb_antr').format(ha=fmt(ha['antropico_estavel'])),
                 t('hansen').format(ha=fmt(hz['ha_perda_total_2001_2025']), p=fmt(hz['ha_perda_pos_2008'])), t('rf_flor_ctx')])
    M.leg_texto(t('m04_nota').format(s=fmt(ha['supressao_pos_2008'])))
    M.notas()
    return M


def _app_capas(M, d, detalle=False):
    """Capas comunes de M05/M05b/M05c."""
    ax = M.ax
    car = d.car
    app = car[car.classe_car.str.startswith('APP')]
    app[app.subclasse == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='none', alpha=0.88, zorder=6)
    app[app.subclasse == 'a recompor'].plot(ax=ax, fc=COL['app_rec'], ec='none', alpha=0.88, zorder=6)
    res = car[car.classe_car.str.startswith('Reservat')]
    res.plot(ax=ax, fc=COL['app_agua'], ec='none', alpha=0.9, zorder=6)
    # silvicultura dentro de la APP a recompor (RF clase 4) -> naranja
    rec_u = unary_union(app[app.subclasse == 'a recompor'].geometry)
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {4: COL['app_silv']}, zorder=7, clip=rec_u)
    # faixa "a definir" del reservatorio (hachurado), limite APP 30 m, faixa 20 m
    poly_patches(ax, [d.reserv_faixa], fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8, zorder=8)
    poly_patches(ax, [d.app30], fc='none', ec=COL['app_lim'], lw=0.9, ls='--', zorder=12)
    poly_patches(ax, [d.faixa20], fc='none', ec=COL['faixa20'], lw=0.9 if not detalle else 1.2, ls=(0, (3, 1.5)), zorder=13)
    fb = d.hidro[(d.hidro.fonte == 'FBDS')]
    fb.plot(ax=ax, color=COL['fbds'], lw=1.0, zorder=11)
    nf = d.nasc[(d.nasc.fonte == 'FBDS') & d.nasc.dentro_propriedade]
    ax.scatter(nf.geometry.x, nf.geometry.y, s=30, marker='o', c=COL['nasc'], edgecolors='white', linewidths=0.8, zorder=15)
    nd = d.nasc[d.nasc.candidato_dem]
    ax.scatter(nd.geometry.x, nd.geometry.y, s=44, marker='^', c=COL['cand'], edgecolors='black', linewidths=0.6, zorder=16)
    if detalle:
        for _, r in nd.iterrows():
            ax.text(r.geometry.x + 20, r.geometry.y, r.id_fonte, fontsize=5.5, va='center', zorder=17,
                    bbox=dict(boxstyle='round,pad=0.12', fc=COL['cand'], ec='none', alpha=0.85))
        for _, r in d.massas.iterrows():
            c = r.geometry.centroid
            ax.text(c.x, c.y, '%s %d' % (t('reserv'), r.massa_id), fontsize=5.2, ha='center', va='center', zorder=18,
                    bbox=dict(boxstyle='round,pad=0.15', fc='white', ec=COL['massa'], lw=0.5, alpha=0.9))


def _app_legenda(M, d):
    L = d.res['legal']
    A = L['app_total_exigivel']; C = L['area_consolidada_app']
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['prop'], lw=2.2),
                 Patch(fc=COL['app_conf']), Patch(fc=COL['app_agua']), Patch(fc=COL['app_rec']), Patch(fc=COL['app_silv']),
                 Line2D([], [], color=COL['app_lim'], lw=0.9, ls='--'),
                 Line2D([], [], color=COL['faixa20'], lw=1.1, ls=(0, (3, 1.5))),
                 Patch(fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8),
                 Line2D([], [], color=COL['fbds'], lw=1.0),
                 Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc'], markeredgecolor='white', ms=6),
                 Line2D([], [], marker='^', color='none', markerfacecolor=COL['cand'], markeredgecolor='black', ms=7)],
                [t('prop'), t('app_conf').format(ha=fmt(A['com_vegetacao_nativa_ha'])), t('app_agua').format(ha=fmt(A['agua_ha'])),
                 t('app_rec').format(ha=fmt(A['sem_vegetacao_ha'])), t('app_silv').format(ha=fmt(A['sem_vegetacao_silvicultura_ha'])),
                 t('app_lim').format(ha=fmt(A['ha'])), t('faixa20').format(ha=fmt(C['cenario_B_pra_ha'])), t('reserv_faixa'),
                 t('curso'), t('nasc_app'), t('cand_dem')])
    M.leg_texto(t('m05_kpi').format(t=fmt(A['ha']), mn=fmt(A['ha_min']), mx=fmt(A['ha_max']), pc=fmt(A['pct_conforme'], 1)), bold=True, color=AZUL)
    M.leg_texto(t('m05_nota').format(a=fmt(C['cenario_A_integral_ha']), b=fmt(C['cenario_B_pra_ha']),
                                     c=fmt(L['app_nascente']['candidatas_dem']['ha_adicional_fora_app_exigivel'])))


def M05(d, layout):
    ext = ext_layout(d, layout)
    M = Mapa(layout, t('m05_t'), t('m05_s'), ext, leg_min_cm=5.4)
    M.fondo(d)
    _app_capas(M, d)
    M.propriedade(d); M.grilla(); M.norte_escala()
    _app_legenda(M, d)
    M.notas()
    return M


def M05_detalhe(d, layout, zona):
    x0, y0, x1, y1 = d.prop.total_bounds
    if zona == 'norte':
        ext = (x0 - 80, 7402650, x1 + 80, y1 + 60)
        tit = t('m05b_t')
    else:
        ext = (x0 - 80, y0 - 60, x1 + 80, 7402350)
        tit = t('m05c_t')
    M = Mapa(layout, tit, t('m05_s'), ext, leg_min_cm=5.4, notas_abajo=(layout == 'V'))
    M.fondo(d)
    _app_capas(M, d, detalle=True)
    M.propriedade(d); M.grilla(250); M.norte_escala(250)
    _app_legenda(M, d)
    M.notas()
    return M


def M06(d, layout):
    ext = ext_layout(d, layout)
    M = Mapa(layout, t('m06_t'), t('m06_s'), ext, leg_min_cm=5.4)
    M.fondo(d)
    ax = M.ax
    car = d.car
    rem = car[car.classe_car.str.startswith('Remanescente')]
    rem.plot(ax=ax, fc=COL['rl_rem'], ec='none', alpha=0.9, zorder=6)
    app = car[car.classe_car.str.startswith('APP')]
    rl_u = unary_union(d.rl.geometry)
    app_c = app[app.subclasse == 'conforme'].geometry.intersection(rl_u)
    app_r = app[app.subclasse == 'a recompor'].geometry.intersection(rl_u)
    poly_patches(ax, app_c, fc=COL['rl_app'], ec='none', alpha=0.9, zorder=6)
    poly_patches(ax, app_r, fc=COL['rl_app_rec'], ec='none', alpha=0.9, zorder=6)
    poly_patches(ax, d.corr.geometry, fc=COL['rl_corr'] + '99', ec='#3F6B00', hatch='///', lw=0.4, zorder=7)
    d.rl.boundary.plot(ax=ax, color='white', lw=2.2, zorder=12)
    d.rl.boundary.plot(ax=ax, color=COL['rl_lim'], lw=1.3, zorder=13)
    fb = d.hidro[(d.hidro.fonte == 'FBDS')]
    fb.plot(ax=ax, color=COL['fbds'], lw=0.8, zorder=11)
    M.propriedade(d); M.grilla(); M.norte_escala()
    RL = d.res['legal']['reserva_legal']; P = RL['proposta']
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['prop'], lw=2.2),
                 Patch(fc=COL['rl_rem']), Patch(fc=COL['rl_app']), Patch(fc=COL['rl_app_rec']),
                 Patch(fc=COL['rl_corr'], hatch='///', ec='#3F6B00'),
                 Line2D([], [], color=COL['rl_lim'], lw=1.6),
                 Line2D([], [], color=COL['fbds'], lw=0.8)],
                [t('prop'), t('rl_rem').format(ha=fmt(P['remanescente_ha'])), t('rl_app').format(ha=fmt(P['app_vegetada_ha'])),
                 t('rl_app_rec').format(ha=fmt(P['app_a_recompor_incluida_ha'])), t('rl_corr').format(ha=fmt(P['corredor_recomposicao_ha'])),
                 t('rl_lim').format(ha=fmt(P['ha'])), t('curso')])
    rows = [[a, b.format(ex=fmt(RL['exigida_ha']), disp=fmt(RL['disponivel_com_app_art15_ha']), **{'def': fmt(RL['deficit_com_app_art15_ha'])},
                         cons=fmt(RL['variante_conservadora_floresta_com_historico']['deficit_com_app_art15_ha']), prop=fmt(P['ha']))]
            for a, b in t('rl_kpi')]
    M.leg_tabla(rows, col_w=[0.68, 0.32], header=False)
    M.leg_texto(t('rl_status'), fs=M.fs - 0.8, color='#555555')
    M.notas()
    return M


def M07(d, layout):
    ext = ext_layout(d, layout)
    M = Mapa(layout, t('m07_t'), t('m07_s'), ext, leg_min_cm=5.6)
    M.fondo(d)
    ax = M.ax
    estilo = {
        ("APP – Nascente ou olho d'água perene", 'conforme'): dict(fc=COL['car_app_conf'], hatch='..', ec='#1B5E20'),
        ("APP – Nascente ou olho d'água perene", 'a recompor'): dict(fc=COL['car_app_rec'], hatch='..', ec='#7F0000'),
        ("APP – Curso d'água natural de até 10 metros", 'conforme'): dict(fc=COL['car_app_conf']),
        ("APP – Curso d'água natural de até 10 metros", 'a recompor'): dict(fc=COL['car_app_rec']),
        ("Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais", 'espelho d agua'): dict(fc=COL['car_reserv']),
        ('Remanescente de Vegetação Nativa', 'floresta fora da APP'): dict(fc=COL['car_rem']),
        ('Área Consolidada', 'uso agricola'): dict(fc=COL['car_cons'] + 'AA'),
        ('Área Consolidada', 'silvicultura'): dict(fc=COL['car_silv'], hatch='////', ec='#4E4E00'),
    }
    handles, labels, rows = [Line2D([], [], color=COL['prop'], lw=2.2)], [t('prop')], [t('tab_car')]
    for (cl, sc), st in estilo.items():
        sub = d.car[(d.car.classe_car == cl) & (d.car.subclasse == sc)]
        if not len(sub):
            continue
        poly_patches(ax, sub.geometry, ec=st.get('ec', 'none'), fc=st['fc'], hatch=st.get('hatch'), lw=0.3, alpha=0.9, zorder=6)
        handles.append(Patch(fc=st['fc'], hatch=st.get('hatch'), ec=st.get('ec', '#999999'), lw=0.4))
        nm = t('car_names')[(cl, sc)]
        labels.append(nm)
        rows.append([t('car_short')[(cl, sc)], fmt(float(sub.area_ha.sum()))])
    d.rl.boundary.plot(ax=ax, color='white', lw=2.0, zorder=12)
    d.rl.boundary.plot(ax=ax, color=COL['rl_lim'], lw=1.1, ls='-', zorder=13)
    handles.append(Line2D([], [], color=COL['rl_lim'], lw=1.4)); labels.append(t('rl_prop_ctx'))
    M.propriedade(d); M.grilla(); M.norte_escala()
    M.leg_titulo(t('legenda'))
    M.leg_items(handles, labels)
    U = d.res['legal']['mapa_uso_car']
    rows.append([t('soma') + ' (%s)' % ('imóvel' if LANG == 'pt' else 'inmueble'), fmt(U['soma_ha'])])
    M.leg_tabla(rows, col_w=[0.74, 0.26], bold_last=True)
    M.notas()
    return M


# ---------------------------------------------------------------- main -------
def main():
    global LANG
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='pt', choices=['pt', 'es'])
    ap.add_argument('--solo', default='', help='lista de mapas, p.ej. M02,M05')
    ap.add_argument('--sin-h', action='store_true', help='no generar A4 apaisado')
    a = ap.parse_args()
    LANG = a.lang
    log('=' * 78); log('an_04_mapas — lang=%s' % LANG); log('=' * 78)
    d = Dados()
    quiere = set(a.solo.split(',')) if a.solo else None
    tareas = [('M01_localizacao', lambda l: M01(d, l)), ('M02_hidrografia', lambda l: M02(d, l)),
              ('M03_vegetacao_nativa_10m', lambda l: M03(d, l)), ('M04_mudanca_2008_2025', lambda l: M04(d, l)),
              ('M05_app_conformidade', lambda l: M05(d, l)), ('M05b_detalhe_norte', lambda l: M05_detalhe(d, l, 'norte')),
              ('M05c_detalhe_sul', lambda l: M05_detalhe(d, l, 'sul')), ('M06_reserva_legal_proposta', lambda l: M06(d, l)),
              ('M07_mapa_uso_car', lambda l: M07(d, l))]
    for nome, fn in tareas:
        if quiere and nome.split('_')[0] not in quiere:
            continue
        fn('V').guardar(nome)
        if not a.sin_h:
            fn('H').guardar(nome, 'A4_horizontal')
    if not quiere or 'G01' in quiere:
        fig = grafico_ndvi(d)
        out_dir = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES')
        os.makedirs(out_dir, exist_ok=True)
        ruta = os.path.join(out_dir, 'G01_serie_ndvi.png')
        fig.savefig(ruta, dpi=DPI, facecolor='white'); plt.close(fig)
        log('  -> %s' % ruta)
    log('an_04 listo')


if __name__ == '__main__':
    main()
