# -*- coding: utf-8 -*-
"""an_13_mapas_v3 — mapas W01..W07 da versao 3 (imovel unico; CAR existente; hidrologia PRO), so o interior.

    python an_13_mapas_v3.py --lang pt   -> 03_MAPAS_V3/*.png
    python an_13_mapas_v3.py --lang es   -> 03_MAPAS_V3/ES/*.png

Reutiliza a classe Mapa (an_04) e os helpers de an_08 (fundo mascarado, glebas, arroios). Toda cifra rotulada sai de
02_ANALISIS/resultados_v3.json (an_12) ou das capas v3_* / hidrologia_pro; nada se recalcula aqui.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, R, CRS_METRICO, leer_json, log   # noqa: E402
import an_04_mapas as m4                                                   # noqa: E402
import an_08_mapas_interior as m8                                          # noqa: E402
from an_04_mapas import COL, AZUL, TEAL, LIMA, GRIS, fmt, poly_patches, plot_lines, raster_clases, DPI   # noqa: E402
from an_08_mapas_interior import DadosV2, novo, glebas, leg_glebas, arroios, patch_agujeros, FORA        # noqa: E402

import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402
from matplotlib.patches import Patch               # noqa: E402
import geopandas as gpd                            # noqa: E402
from shapely.ops import unary_union                # noqa: E402

MAPAS_V3 = os.path.join(PROYECTO, '03_MAPAS_V3')
HP = os.path.join(ANALISIS, 'hidrologia_pro')
LANG = 'pt'
COL.update({'g2': '#FF8C00', 'frag13': '#FFFFFF', 'rl_corr': '#F59E0B', 'iat': '#D946EF', 'ens': '#00E5FF', 'esp_chuva': '#38BDF8', 'esp_max': '#0C4A6E',
            'car_app': '#7C3AED', 'car_rl': '#F97316', 'car_veg': '#16A34A', 'car_res': '#0EA5E9', 'outorga': '#DC2626', 'nasc_prov': '#1D4ED8', 'nasc_pp': '#9CA3AF',
            'rl_app': '#66BB6A', 'ponta': '#B91C1C'})

W = {
    'notas': {'pt': 'Cena S2C 29/08/2026 · SIRGAS 2000 / UTM 22S (EPSG:31982) · Hidrografia FBDS/IAT 2013 (1:25.000) disponibilizada pelo IAT · SÓ O INTERIOR DO PERÍMETRO '
                    '(exterior em cinza) · PARECER TÉCNICO PRELIMINAR: não substitui laudo; leito regular, nascentes e limites a confirmar em campo (GNSS).',
              'es': 'Escena S2C 29/08/2026 · SIRGAS 2000 / UTM 22S (EPSG:31982) · Hidrografía FBDS/IAT 2013 (1:25.000) publicada por el IAT · SOLO EL INTERIOR DEL PERÍMETRO '
                    '(exterior en gris) · INFORME TÉCNICO PRELIMINAR: no sustituye un informe pericial; cauce regular, nacientes y límites a confirmar en campo (GNSS).'},
    'legenda': {'pt': 'Legenda', 'es': 'Leyenda'},
    'arroio': {'pt': 'Arroio', 'es': 'Arroyo'},
    'curso': {'pt': "Eixo do curso d'água FBDS 2013", 'es': 'Eje del curso de agua FBDS 2013'},
    # W01
    'w01_t': {'pt': 'W01 · Vegetação nativa no interior do imóvel', 'es': 'W01 · Vegetación nativa en el interior del inmueble'},
    'w01_s': {'pt': 'RF 10 m sobre S2 29/08/2026 · imóvel único {ha} ha · computável = só a Gleba 1 (G2 = terra limpa)',
              'es': 'RF 10 m sobre S2 29/08/2026 · inmueble único {ha} ha · computable = solo la Gleba 1 (G2 = tierra limpia)'},
    'cl_flor': {'pt': 'Floresta nativa RF — computável G1 {a} ha [{mn}; {mx}]', 'es': 'Bosque nativo RF — computable G1 {a} ha [{mn}; {mx}]'},
    'cl_flor_g2': {'pt': 'Floresta na ponta norte da G2 — {b} ha NÃO computada (limite a conferir)', 'es': 'Bosque en la punta norte de G2 — {b} ha NO computado (límite a verificar)'},
    'cl_frag13': {'pt': 'Fragmento 13 ({ha} ha): regeneração arbórea, sem histórico 2008/2013 — a confirmar em campo', 'es': 'Fragmento 13 ({ha} ha): regeneración arbórea, sin historial 2008/2013 — a confirmar en campo'},
    'cl_silv': {'pt': 'Silvicultura (RF, incerta) — {a} ha', 'es': 'Silvicultura (RF, incierta) — {a} ha'},
    'cl_agua': {'pt': 'Água (RF) — {a} ha', 'es': 'Agua (RF) — {a} ha'},
    'cl_antr': {'pt': 'Área agrícola / antropizada — G1 {a} · G2 {b} ha', 'es': 'Área agrícola / antropizada — G1 {a} · G2 {b} ha'},
    'frag': {'pt': 'Fragmento (id · ha na gleba)', 'es': 'Fragmento (id · ha en la gleba)'},
    'frag_lbl': {'pt': 'Frag. {id}\n{ha} ha', 'es': 'Frag. {id}\n{ha} ha'},
    'tab_veg': {'pt': ['Vegetação nativa', 'ha'], 'es': ['Vegetación nativa', 'ha']},
    'tab_veg_rows': {'pt': ['Computável (G1, art. 12 + 15)', '   na APP (art. 15)', '   fora da APP', 'Conservadora (sem frag. 13)', 'G2 ponta norte (não computa)'],
                     'es': ['Computable (G1, art. 12 + 15)', '   en la APP (art. 15)', '   fuera de la APP', 'Conservadora (sin frag. 13)', 'G2 punta norte (no computa)']},
    'w01_nota': {'pt': 'Frag. 2: parte de um fragmento contínuo além do limite (IAT prioridade A, 23 anos; MapBiomas: floresta em 1985/2008 — indício a 30 m). '
                       'Frag. 13: NDVI 0,57-0,87 em 24 meses e SWIR arbóreo, mas sem floresta em 2008 (MapBiomas) nem 2013 (FBDS): estágio e idade a confirmar (CONAMA 2/1994). Frag. 30: idem, sem histórico.',
                 'es': 'Frag. 2: parte de un fragmento continuo más allá del límite (IAT prioridad A, 23 años; MapBiomas: bosque en 1985/2008 — indicio a 30 m). '
                       'Frag. 13: NDVI 0,57-0,87 en 24 meses y SWIR arbóreo, pero sin bosque en 2008 (MapBiomas) ni 2013 (FBDS): estadio y edad a confirmar (CONAMA 2/1994). Frag. 30: ídem, sin historial.'},
    # W02
    'w02_t': {'pt': 'W02 · Hidrografia no interior do imóvel', 'es': 'W02 · Hidrografía en el interior del inmueble'},
    'w02_s': {'pt': 'Arroios FBDS numerados · nascente com veredito · represa por fonte · conjunto de 5 DEM · outorga',
              'es': 'Arroyos FBDS numerados · naciente con veredicto · represa por fuente · ensamble de 5 DEM · concesión'},
    'arr_lbl': {'pt': 'Arroio {n}\n{m} m', 'es': 'Arroyo {n}\n{m} m'},
    'ens': {'pt': 'Mediana do conjunto de 5 DEM (Arroio 1: {m} m do eixo FBDS) — envolvente', 'es': 'Mediana del ensamble de 5 DEM (Arroyo 1: {m} m del eje FBDS) — envolvente'},
    'nasc_prov': {'pt': 'Nascente FBDS 306158 — PROVÁVEL (perenidade não verificada)', 'es': 'Naciente FBDS 306158 — PROBABLE (perennidad no verificada)'},
    'nasc_dem1': {'pt': 'dem_1 — mesma cabeceira (não soma)', 'es': 'dem_1 — misma cabecera (no suma)'},
    'nasc_pp': {'pt': 'dem_2 (em soja) — POUCO PROVÁVEL (nota topográfica)', 'es': 'dem_2 (en soja) — POCO PROBABLE (nota topográfica)'},
    'esp_chuva': {'pt': 'Represa: espelho mediano chuvoso 2024-26 (S2) — {a} ha', 'es': 'Represa: espejo mediano lluvioso 2024-26 (S2) — {a} ha'},
    'esp_max': {'pt': 'Extensão máxima histórica (JRC 1984-2021) — {a} ha', 'es': 'Extensión máxima histórica (JRC 1984-2021) — {a} ha'},
    'esp_fbds': {'pt': 'Espelho FBDS 2013 — {a} ha (CAR declara {b} ha)', 'es': 'Espejo FBDS 2013 — {a} ha (el CAR declara {b} ha)'},
    'outorga': {'pt': 'Outorga SIGARH da barragem — prévia, IRREGULAR, vencida 08/11/2025', 'es': 'Concesión SIGARH de la represa — previa, IRREGULAR, vencida 08/11/2025'},
    'res2': {'pt': '2º reservatório declarado no CAR (0,15 ha) — sem água 2024-26', 'es': '2º reservorio declarado en el CAR (0,15 ha) — sin agua 2024-26'},
    'tab_arr': {'pt': ['Curso', 'FBDS', 'otto', 'ANA', 'BC250'], 'es': ['Curso', 'FBDS', 'otto', 'ANA', 'BC250']},
    'w02_nota': {'pt': 'Comprimentos em m dentro da Gleba 1. Arroio 3 = Ribeirão do Salto (represado; BC250 "Permanente" não discrimina regime). Largura até 10 m em todas as fontes. '
                       'Gleba 2: {g2m} m do Arroio 1 na ponta norte. Espelho atual da represa 0,83-1,23 ha: >= 1 ha INDETERMINADO; histórico >= 1 ha.',
                 'es': 'Longitudes en m dentro de la Gleba 1. Arroyo 3 = Ribeirão do Salto (represado; BC250 "Permanente" no discrimina régimen). Ancho hasta 10 m en todas las fuentes. '
                       'Gleba 2: {g2m} m del Arroyo 1 en la punta norte. Espejo actual de la represa 0,83-1,23 ha: >= 1 ha INDETERMINADO; histórico >= 1 ha.'},
    # W03
    'w03_t': {'pt': 'W03 · Mata ciliar (APP) do imóvel', 'es': 'W03 · Mata ciliar (APP) del inmueble'},
    'w03_s': {'pt': 'Art. 4º: 30 m dos cursos até 10 m + 50 m da nascente · FBDS/IAT · envolvente de 5 DEM · RF 29/08/2026',
              'es': 'Art. 4º: 30 m de cursos hasta 10 m + 50 m de la naciente · FBDS/IAT · envolvente 5 DEM · RF 29/08/2026'},
    'app_conf': {'pt': 'APP conforme (vegetação nativa, RF 10 m) — {a} ha', 'es': 'APP conforme (vegetación nativa, RF 10 m) — {a} ha'},
    'app_agua': {'pt': 'APP com água — {a} ha', 'es': 'APP con agua — {a} ha'},
    'app_rec': {'pt': 'APP a recompor — {a} ha (dos quais silvicultura {s} ha)', 'es': 'APP a recomponer — {a} ha (de los cuales silvicultura {s} ha)'},
    'app_lim': {'pt': 'Limite da APP exigível FBDS (30 / 50 m) — {a} ha', 'es': 'Límite de la APP exigible FBDS (30 / 50 m) — {a} ha'},
    'app_ens': {'pt': 'APP pela mediana do conjunto de DEM — envolvente [{mn}; {mx}] ha', 'es': 'APP por la mediana del ensamble DEM — envolvente [{mn}; {mx}] ha'},
    'faixa20': {'pt': 'Faixa PRA-PR (20 m / 15 m) — recompor {a} ha', 'es': 'Faja PRA-PR (20 m / 15 m) — recomponer {a} ha'},
    'reserv_faixa': {'pt': 'Faixa 30 m da represa SE o IAT a aplicar — +{a} ha a recompor', 'es': 'Faja 30 m de la represa SI el IAT la aplica — +{a} ha a recomponer'},
    'tab_app': {'pt': ['APP (ha)', 'G1', 'G2', 'Imóvel'], 'es': ['APP (ha)', 'G1', 'G2', 'Inmueble']},
    'tab_app_rows': {'pt': ['Exigida (FBDS)', 'Envolvente mín.', 'Envolvente máx.', 'Com vegetação', 'Água', 'A recompor', 'Recompor PRA-PR', 'Se faixa da represa'],
                     'es': ['Exigida (FBDS)', 'Envolvente mín.', 'Envolvente máx.', 'Con vegetación', 'Agua', 'A recomponer', 'Recomponer PRA-PR', 'Si faja de la represa']},
    'w03_ver': {'pt': 'NÃO CONFORME: {a} ha a recompor ({b} ha pela faixa PRA-PR, condicionada à data do CAR). Arroio 1: desvio sistemático de {m} m entre FBDS e os 5 DEM — levantar com GNSS.',
                'es': 'NO CONFORME: {a} ha a recomponer ({b} ha por la faja PRA-PR, condicionada a la fecha del CAR). Arroyo 1: sesgo sistemático de {m} m entre FBDS y los 5 DEM — levantar con GNSS.'},
    # W04
    'w04_t': {'pt': 'W04 · Reserva Legal do imóvel único (20%)', 'es': 'W04 · Reserva Legal del inmueble único (20%)'},
    'w04_s': {'pt': 'Art. 12 (20% de {ha} ha = {rl} ha) · art. 15 (APP vegetada computa) · art. 14 · G2 sem vegetação',
              'es': 'Art. 12 (20% de {ha} ha = {rl} ha) · art. 15 (APP vegetada computa) · art. 14 · G2 sin vegetación'},
    'rl_rem': {'pt': 'Vegetação nativa computável fora da APP — {a} ha', 'es': 'Vegetación nativa computable fuera de la APP — {a} ha'},
    'rl_app': {'pt': 'APP vegetada computável (art. 15) — {a} ha', 'es': 'APP vegetada computable (art. 15) — {a} ha'},
    'rl_f13': {'pt': 'Fragmento 13 — regeneração a confirmar (excluído na variante conservadora)', 'es': 'Fragmento 13 — regeneración a confirmar (excluido en la variante conservadora)'},
    'rl_corr': {'pt': 'Corredor de recomposição proposto — {a} ha', 'es': 'Corredor de recomposición propuesto — {a} ha'},
    'rl_lim': {'pt': 'RL proposta (G1) — {a} ha; faltam {f} ha a localizar', 'es': 'RL propuesta (G1) — {a} ha; faltan {f} ha por localizar'},
    'rl_iat': {'pt': 'Fragmento IAT prioridade A (23 anos) — {a} ha no imóvel: âncora da RL', 'es': 'Fragmento IAT prioridad A (23 años) — {a} ha en el inmueble: ancla de la RL'},
    'rl_g2': {'pt': 'Floresta da ponta norte da G2 — não computada', 'es': 'Bosque de la punta norte de G2 — no computado'},
    'tab_rl': {'pt': ['Reserva Legal (ha)', 'Principal', 'Conserv.'], 'es': ['Reserva Legal (ha)', 'Principal', 'Conserv.']},
    'tab_rl_rows': {'pt': ['Exigida (20% de {ha})', 'Vegetação computável', 'Déficit', 'CAR averba', 'RL proposta (G1)'], 'es': ['Exigida (20% de {ha})', 'Vegetación computable', 'Déficit', 'CAR inscribe', 'RL propuesta (G1)']},
    'w04_nota': {'pt': 'NÃO CONFORME: déficit de {d} ha (conservador {dc} ha, sem o fragmento 13). A RL de 31,55 ha é do imóvel inteiro e pode localizar-se em qualquer gleba (art. 14). '
                       'Se a mata da ponta norte da G2 for do imóvel, computável 20,38 e déficit 11,17 ha. A APP a recompor só computa depois de declarada em recuperação (art. 15 II).',
                 'es': 'NO CONFORME: déficit de {d} ha (conservador {dc} ha, sin el fragmento 13). La RL de 31,55 ha es del inmueble entero y puede localizarse en cualquier gleba (art. 14). '
                       'Si el bosque de la punta norte de G2 fuera del inmueble, computable 20,38 y déficit 11,17 ha. La APP a recomponer solo computa tras declararse en recuperación (art. 15 II).'},
    # W05
    'w05_t': {'pt': 'W05 · Uso e cobertura com a nomenclatura CAR/SICAR', 'es': 'W05 · Uso y cobertura con la nomenclatura CAR/SICAR'},
    'w05_s': {'pt': 'Sem sobreposição · Módulo de Cadastro do SICAR (Manual SFB) · fecha em {a} ha ({b} + {c})', 'es': 'Sin superposición · Módulo de Catastro del SICAR (Manual SFB) · cierra en {a} ha ({b} + {c})'},
    'tab_car': {'pt': ['Classe CAR / subclasse', 'G1', 'G2'], 'es': ['Clase CAR / subclase', 'G1', 'G2']},
    'soma': {'pt': 'Soma', 'es': 'Suma'},
    'w05_nota': {'pt': 'Somas sobre áreas a 3 decimais; linhas arredondadas podem diferir em até 0,01 ha. "Perene" é nomenclatura SICAR obrigatória: perenidade NÃO verificada. Camada preparada no formato do SICAR, a conferir pelo responsável pela inscrição.',
                 'es': 'Sumas sobre áreas a 3 decimales; las filas redondeadas pueden diferir hasta 0,01 ha. "Perene" es nomenclatura SICAR obligatoria: perennidad NO verificada. Capa preparada en el formato del SICAR, a verificar por el responsable de la inscripción.'},
    # W06
    'w06_t': {'pt': 'W06 · CAR existente (declarado) vs medido', 'es': 'W06 · CAR existente (declarado) vs medido'},
    'w06_s': {'pt': 'CAR PR-4124301-F127CD1E… ({a} ha, "{c}") sobre a RF 2026 · retificação', 'es': 'CAR PR-4124301-F127CD1E… ({a} ha, "{c}") sobre la RF 2026 · rectificación'},
    'car_app': {'pt': 'APP declarada no CAR — {a} ha (medida {b} ha)', 'es': 'APP declarada en el CAR — {a} ha (medida {b} ha)'},
    'car_rl': {'pt': 'Reserva Legal averbada no CAR — {a} ha (exigida {b} ha)', 'es': 'Reserva Legal inscrita en el CAR — {a} ha (exigida {b} ha)'},
    'car_veg': {'pt': 'Vegetação nativa declarada — {a} ha (medida {b} ha)', 'es': 'Vegetación nativa declarada — {a} ha (medida {b} ha)'},
    'car_res': {'pt': 'Reservatórios declarados — {a} + {b} ha', 'es': 'Reservorios declarados — {a} + {b} ha'},
    'car_g2': {'pt': 'CAR de origem da G2 (PR-4124301-5223911747…, {a} ha) — RL declarada dentro da G2 {b} ha', 'es': 'CAR de origen de G2 (PR-4124301-5223911747…, {a} ha) — RL declarada dentro de G2 {b} ha'},
    'rf_flor': {'pt': 'Floresta nativa RF 2026 (fundo)', 'es': 'Bosque nativo RF 2026 (fondo)'},
    'tab_car6': {'pt': ['Tema', 'CAR', 'Medido'], 'es': ['Tema', 'CAR', 'Medido']},
    'tab_car6_rows': {'pt': ['Área (ha)', 'APP (ha)', 'RL (ha)', 'Veg. nativa (ha)', 'Consolidada (ha)', 'Represa (ha)'], 'es': ['Área (ha)', 'APP (ha)', 'RL (ha)', 'Veg. nativa (ha)', 'Consolidada (ha)', 'Represa (ha)']},
    'w06_nota': {'pt': 'O CAR cobre {p}% da Gleba 1 (matrícula 8.334, SIGEF registrada). Retificar: RL de 2,45 para 31,55 ha (imóvel único), vegetação nativa de 3,80 para 17,70 ha, '
                       'incluir a Gleba 2 (IN MMA 2/2014 art. 32), conferir a APP do Arroio 1 (GNSS) e o 2º reservatório na cabeceira do Arroio 2. Data de inscrição a verificar (PRA-PR).',
                 'es': 'El CAR cubre el {p}% de la Gleba 1 (matrícula 8.334, SIGEF registrada). Rectificar: RL de 2,45 a 31,55 ha (inmueble único), vegetación nativa de 3,80 a 17,70 ha, '
                       'incluir la Gleba 2 (IN MMA 2/2014 art. 32), verificar la APP del Arroyo 1 (GNSS) y el 2º reservorio en la cabecera del Arroyo 2. Fecha de inscripción a verificar (PRA-PR).'},
    # W07
    'w07_t': {'pt': 'W07 · Gleba 2 ("os 6 alqueires"): terra limpa', 'es': 'W07 · Gleba 2 ("los 6 alqueires"): tierra limpia'},
    'w07_s': {'pt': '{ha} ha = {alq} alqueires · comprada sem monte · limite da ponta norte a conferir (fragmento 2)', 'es': '{ha} ha = {alq} alqueires · comprada sin monte · límite de la punta norte a verificar (fragmento 2)'},
    'ponta': {'pt': 'Ponta norte: {a} ha de floresta NÃO computada — limite a conferir com a escritura/SIGEF', 'es': 'Punta norte: {a} ha de bosque NO computado — límite a verificar con la escritura/SIGEF'},
    'app_g2': {'pt': 'APP do Arroio 1 ({m} m): {a} ha [{mn}; {mx}] com vegetação; 0 se o limite for corrigido', 'es': 'APP del Arroyo 1 ({m} m): {a} ha [{mn}; {mx}] con vegetación; 0 si se corrige el límite'},
    'car_g2_lim': {'pt': 'CAR de origem PR-4124301-5223911747… ({a} ha = {mf} MF)', 'es': 'CAR de origen PR-4124301-5223911747… ({a} ha = {mf} MF)'},
    'w07_kpi': {'pt': 'Quanto monte precisa a Gleba 2?', 'es': '¿Cuánto monte necesita la Gleba 2?'},
    'w07_txt': {'pt': ['(A) IMÓVEL ÚNICO — principal (IN MMA 2/2014 art. 32): não há conta própria. Os 6 alqueires somam {g2rl} ha à RL do imóvel ({g1rl} -> {rl} ha), localizável em qualquer gleba (art. 14), e aportam 0 ha de vegetação. Déficit do imóvel: {d} ha.',
                       '(B) IMÓVEL SEPARADO, desmembrado de imóvel > 4 MF (origem {car} ha = {mf} MF; art. 12 §1º): RL própria de 20% = {g2rl} ha; com terra limpa, {g2rl} ha a recompor, regenerar ou compensar (art. 66).',
                       '(C) EXCEÇÃO art. 67 — só se o imóvel de origem tinha até 4 MF em 22/07/2008 (provar com a matrícula de origem): RL = vegetação de 2008; 0 ha se era terra limpa (MapBiomas 2008 mostra {v08} ha só na ponta norte).',
                       'APP: {m} m do Arroio 1 na ponta norte, {app} ha vegetados; se a ponta norte não for da gleba, APP e vegetação = 0. Indício de supressão pós-2008 na borda: {sup} ha (MapBiomas 30 m, a validar).'],
                'es': ['(A) INMUEBLE ÚNICO — principal (IN MMA 2/2014 art. 32): no hay cuenta propia. Los 6 alqueires suman {g2rl} ha a la RL del inmueble ({g1rl} -> {rl} ha), localizable en cualquier gleba (art. 14), y aportan 0 ha de vegetación. Déficit del inmueble: {d} ha.',
                       '(B) INMUEBLE SEPARADO, desmembrado de inmueble > 4 MF (origen {car} ha = {mf} MF; art. 12 §1º): RL propia del 20% = {g2rl} ha; con tierra limpia, {g2rl} ha a recomponer, regenerar o compensar (art. 66).',
                       '(C) EXCEPCIÓN art. 67 — solo si el inmueble de origen tenía hasta 4 MF el 22/07/2008 (probar con la matrícula de origen): RL = vegetación de 2008; 0 ha si era tierra limpia (MapBiomas 2008 muestra {v08} ha solo en la punta norte).',
                       'APP: {m} m del Arroyo 1 en la punta norte, {app} ha vegetados; si la punta norte no fuera de la gleba, APP y vegetación = 0. Indicio de supresión pos-2008 en el borde: {sup} ha (MapBiomas 30 m, a validar).']},
    'g1': {'pt': 'Gleba 1 – {ha} ha', 'es': 'Gleba 1 – {ha} ha'},
    'g2': {'pt': 'Gleba 2 – {ha} ha ({alq} alq.)', 'es': 'Gleba 2 – {ha} ha ({alq} alq.)'},
}


def t(k):
    return W[k][LANG]


class DadosV3(DadosV2):
    def __init__(self):
        super().__init__()
        self.v3 = leer_json(os.path.join(ANALISIS, 'resultados_v3.json'))
        A = lambda n: gpd.read_file(os.path.join(ANALISIS, n + '.geojson'))
        self.vc = A('v3_vegetacao_computavel')
        self.frag = A('v3_fragmentos')
        self.rlp = A('v3_RL_proposta')
        self.carx = A('v3_CAR_existente')
        self.iat = A('v3_IAT_fragmento_prioritario')
        self.nv = A('v3_nascentes')
        self.esp = A('v3_represa_espelhos')
        self.outorga = A('v3_outorga_sigarh')
        self.ponta = A('v3_G2_ponta_norte')
        H = lambda n: gpd.read_file(os.path.join(HP, n + '.geojson'))
        ens = H('hidro_ensamble_mediana_por_arroio')
        self.ens_a1 = ens[(ens.gleba == 'G1') & (ens.tipo == 'mediana_ensamble') & (ens.arroio == 'Arroio 1 (norte)')]
        self.ens_all = ens[ens.tipo == 'mediana_ensamble']
        a1 = H('app_G1_fbds_vs_ensamble'); a2 = H('app_G2_fbds_vs_ensamble')
        self.app_ens = unary_union(list(a1[a1.base != 'FBDS'].geometry) + list(a2[a2.base != 'FBDS'].geometry))
        self.f13 = unary_union(self.frag[(self.frag.gleba == 'G1') & (self.frag.frag_id == 13)].geometry)


def esp_por(d, key):
    s = d.esp[d.esp.fuente.str.startswith(key)]
    return unary_union(list(s.geometry)) if len(s) else None


# ---------------------------------------------------------------- W01 --------
def W01(d):
    v = d.v3['vegetacao']; k = d.v3['kpi']
    M = novo(d, t('w01_t'), t('w01_s').format(ha=fmt(k['area_imovel_ha'])), leg_min_cm=6.2)
    ax = M.ax
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent,
                  {1: COL['floresta'], 2: COL['agua'], 3: COL['antrop'] + 'AA', 4: COL['silv']}, alpha=0.88, zorder=5, clip=d.prop_u)
    poly_patches(ax, [d.f13], fc='none', ec='white', hatch='///', lw=0.0, zorder=8)
    poly_patches(ax, list(d.ponta.geometry), fc='none', ec=COL['ponta'], hatch='xx', lw=1.0, zorder=9)
    for u in ('G1', 'G2'):
        fl = d.frag[d.frag.gleba == u]
        fl.boundary.plot(ax=ax, color='white', lw=1.2, zorder=12); fl.boundary.plot(ax=ax, color=LIMA, lw=0.6, zorder=13)
    off = {('G1', 2): (230, -90), ('G1', 13): (150, 40), ('G1', 30): (-20, -190), ('G2', 2): (-250, -30)}
    for _, r in d.frag.iterrows():
        c = r.geometry.representative_point(); dx_, dy_ = off.get((r.gleba, int(r.frag_id)), (0, 0))
        ax.annotate(t('frag_lbl').format(id=r.frag_id, ha=fmt(r.area_dentro_ha)), xy=(c.x, c.y), xytext=(c.x + dx_, c.y + dy_), fontsize=5.4, ha='center', va='center',
                    zorder=41, fontweight='bold', arrowprops=dict(arrowstyle='-', lw=0.6, color='black'), bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['floresta'], lw=0.7, alpha=0.93))
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['floresta']), Patch(fc=COL['floresta'], hatch='///', ec='white'), Patch(fc=COL['floresta'], hatch='xx', ec=COL['ponta']),
                     Patch(fc=COL['silv'], hatch='////', ec='#4E4E00'), Patch(fc=COL['agua']), Patch(fc=COL['antrop'], ec='#BBBBBB'), Patch(fc='none', ec=LIMA, lw=1.5)],
                l + [t('cl_flor').format(a=fmt(v['computavel_imovel_ha']), mn=fmt(v['envolvente_1px_ha'][0]), mx=fmt(v['envolvente_1px_ha'][1])),
                     t('cl_frag13').format(ha=fmt(v['fragmentos_g1'][1]['ha'])), t('cl_flor_g2').format(b=fmt(v['g2_floresta_na_imagem_nao_computada_ha'])),
                     t('cl_silv').format(a=fmt(d.g1['vegetacao']['silvicultura_ha'] + d.g2['vegetacao']['silvicultura_ha'])), t('cl_agua').format(a=fmt(d.g1['vegetacao']['agua_rf_ha'])),
                     t('cl_antr').format(a=fmt(d.g1['vegetacao']['area_agricola_car_ha']), b=fmt(d.g2['vegetacao']['area_agricola_car_ha'])), t('frag')])
    rows = [t('tab_veg')]
    for lab, val in zip(t('tab_veg_rows'), [v['computavel_imovel_ha'], v['em_app_ha'], v['fora_app_ha'], v['conservador_sem_frag13_ha'], v['g2_floresta_na_imagem_nao_computada_ha']]):
        rows.append([lab, fmt(val)])
    M.leg_tabla(rows, col_w=[0.74, 0.26])
    M.leg_texto(t('w01_nota')); M.notas()
    return M


# ---------------------------------------------------------------- W02 --------
def W02(d):
    M = novo(d, t('w02_t'), t('w02_s'), leg_min_cm=6.3)
    ax = M.ax; rp = d.v3['represa']; k = d.v3['kpi']
    jrc = esp_por(d, 'JRC'); chuva = esp_por(d, 'S2 freq_chuva'); fb = esp_por(d, 'FBDS')
    if jrc is not None:
        poly_patches(ax, [jrc.intersection(d.prop_u)], fc=COL['esp_max'] + '55', ec=COL['esp_max'], lw=0.8, zorder=8)
    if fb is not None:
        poly_patches(ax, [fb.intersection(d.prop_u)], fc='none', ec=COL['massa'], lw=1.1, ls='--', zorder=9)
    if chuva is not None:
        poly_patches(ax, [chuva.intersection(d.prop_u)], fc=COL['esp_chuva'], ec='white', lw=0.4, zorder=10)
    plot_lines(ax, d.ens_a1.geometry.intersection(d.prop_u), color=COL['ens'], lw=1.3, ls=(0, (4, 2)), zorder=12)
    arroios(M, d)
    # nascentes com veredito
    for _, r in d.nv.iterrows():
        if r.id == '306158':
            ax.scatter([r.geometry.x], [r.geometry.y], s=44, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=0.9, zorder=16)
        elif r.id == 'dem_1':
            ax.scatter([r.geometry.x], [r.geometry.y], s=30, marker='o', facecolors='none', edgecolors=COL['nasc_prov'], linewidths=1.0, zorder=16)
        else:
            ax.scatter([r.geometry.x], [r.geometry.y], s=34, marker='v', c=COL['nasc_pp'], edgecolors='black', linewidths=0.5, zorder=16)
            ax.text(r.geometry.x + 30, r.geometry.y, 'dem_2', fontsize=5.0, va='center', zorder=17, bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.8))
    # 2o reservatorio declarado (cabeceira) e outorga
    r2 = d.carx[(d.carx.cod_tema == 'RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO') & (d.carx.relacao == 'propio_G1')]
    if len(r2):
        parts = [p for g in r2.geometry for p in (g.geoms if hasattr(g, 'geoms') else [g])]
        small = [p for p in parts if p.area < 5000]
        if small:
            poly_patches(ax, small, fc='none', ec=COL['car_res'], lw=1.2, zorder=14)
    o = d.outorga.geometry.iloc[0]
    ax.scatter([o.x], [o.y], s=60, marker='*', c=COL['outorga'], edgecolors='white', linewidths=0.6, zorder=18)
    c = unary_union(d.lag.geometry).centroid
    ax.annotate('%s ha' % fmt(rp['espelho_referencia_ha']), xy=(c.x, c.y), xytext=(c.x - 60, c.y - 200), fontsize=5.4, ha='center', zorder=40,
                arrowprops=dict(arrowstyle='-', lw=0.5, color='black'), bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=COL['esp_chuva'], lw=0.8, alpha=0.92))
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    a1 = d.v3['app']['G1']['por_arroio']['Arroio 1 (norte)']
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Line2D([], [], color=COL['fbds'], lw=1.6), Line2D([], [], color=COL['ens'], lw=1.3, ls=(0, (4, 2))),
                     Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=6.5),
                     Line2D([], [], marker='o', color='none', markerfacecolor='none', markeredgecolor=COL['nasc_prov'], ms=6),
                     Line2D([], [], marker='v', color='none', markerfacecolor=COL['nasc_pp'], markeredgecolor='black', ms=6),
                     Patch(fc=COL['esp_chuva']), Patch(fc=COL['esp_max'] + '55', ec=COL['esp_max']), Patch(fc='none', ec=COL['massa'], ls='--', lw=1.1),
                     Line2D([], [], marker='*', color='none', markerfacecolor=COL['outorga'], markeredgecolor='white', ms=9), Patch(fc='none', ec=COL['car_res'], lw=1.2)],
                l + [t('curso') + ' — %s km' % fmt(k['km_cursos_g1'], 3), t('ens').format(m=fmt(a1['mediana_ensamble_vs_fbds_med_m'], 0)), t('nasc_prov'), t('nasc_dem1'), t('nasc_pp'),
                     t('esp_chuva').format(a=fmt(rp['espelho_referencia_ha'])), t('esp_max').format(a=fmt(rp['espelho_por_fonte_ha']['JRC max 1984-2021'])),
                     t('esp_fbds').format(a=fmt(rp['espelho_por_fonte_ha']['FBDS 2013 (RapidEye 5 m)']), b=fmt(rp['espelho_por_fonte_ha']['CAR declarado'])), t('outorga'), t('res2')])
    rows = [t('tab_arr')]
    for c_ in d.v3['cursos']['G1']:
        rows.append(['%s %d' % (t('arroio'), c_['n']), fmt(c_['fbds_m'], 0), fmt(c_['otto_2020_m'], 0), fmt(c_['ana_5k_m'], 0) if c_['ana_5k_m'] else '—', fmt(c_['ibge_bc250_m'], 0) if c_['ibge_bc250_m'] else '—'])
    M.leg_tabla(rows, col_w=[0.30, 0.18, 0.17, 0.17, 0.18])
    M.leg_texto(t('w02_nota').format(g2m=fmt(d.v3['cursos']['G2'][0]['fbds_m'], 0))); M.notas()
    return M


# ---------------------------------------------------------------- W03 --------
def W03(d):
    M = novo(d, t('w03_t'), t('w03_s'), leg_min_cm=6.3)
    ax = M.ax; A = d.v3['app']; a1 = A['G1']; k = d.v3['kpi']
    for u in ('G1', 'G2'):
        a = d.app[u]; base = a[a.cenario == 'base']
        base[base.situacao == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='none', alpha=0.9, zorder=6)
        base[base.situacao == 'a recompor'].plot(ax=ax, fc=COL['app_rec'], ec='none', alpha=0.9, zorder=6)
        base[base.situacao == 'agua'].plot(ax=ax, fc=COL['app_agua'], ec='none', alpha=0.9, zorder=6)
        if (base.situacao == 'a recompor').any():
            rec_u = unary_union(base[base.situacao == 'a recompor'].geometry)
            raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {4: COL['app_silv']}, zorder=7, clip=rec_u)
    if d.reserv_faixa is not None:
        poly_patches(ax, [d.reserv_faixa], fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8, zorder=8)
    poly_patches(ax, [d.app30], fc='none', ec=COL['app_lim'], lw=0.8, ls='--', zorder=12)
    poly_patches(ax, [d.faixa20], fc='none', ec=COL['faixa20'], lw=0.9, ls=(0, (3, 1.5)), zorder=13)
    arroios(M, d, rotular=False, lw=1.0)
    nf = d.nv[d.nv.id == '306158']
    ax.scatter(nf.geometry.x, nf.geometry.y, s=34, marker='o', c=COL['nasc'], edgecolors='white', linewidths=0.8, zorder=15)
    poly_patches(ax, [d.app_ens], fc='none', ec=COL['ens'], lw=0.9, ls=(0, (4, 2)), zorder=14)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['app_conf']), Patch(fc=COL['app_agua']), Patch(fc=COL['app_rec']), Line2D([], [], color=COL['app_lim'], lw=0.9, ls='--'),
                     Line2D([], [], color=COL['ens'], lw=1.1, ls=(0, (4, 2))), Line2D([], [], color=COL['faixa20'], lw=1.1, ls=(0, (3, 1.5))),
                     Patch(fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8), Line2D([], [], color=COL['fbds'], lw=1.0),
                     Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc'], markeredgecolor='white', ms=6)],
                l + [t('app_conf').format(a=fmt(A['imovel']['com_vegetacao_ha'])), t('app_agua').format(a=fmt(A['imovel']['agua_ha'])),
                     t('app_rec').format(a=fmt(A['imovel']['a_recompor_ha']), s=fmt(a1['a_recompor_silvicultura_ha'])),
                     t('app_lim').format(a=fmt(A['imovel']['exigida_ha'])), t('app_ens').format(mn=fmt(A['imovel']['envolvente_ha'][0]), mx=fmt(A['imovel']['envolvente_ha'][1])),
                     t('faixa20').format(a=fmt(a1['pra_pr']['a_recompor_ha'])), t('reserv_faixa').format(a=fmt(a1['cenario_faixa_reservatorio']['delta_recompor_ha'])), t('curso'), t('nasc_prov')])
    g2 = A['G2']
    rows = [t('tab_app')]
    vals = [(a1['exigida_ha'], g2['exigida_fbds_ha'], A['imovel']['exigida_ha']), (a1['envolvente_ha'][0], g2['envolvente_ha'][0], A['imovel']['envolvente_ha'][0]),
            (a1['envolvente_ha'][1], g2['envolvente_ha'][1], A['imovel']['envolvente_ha'][1]), (a1['com_vegetacao_ha'], g2['com_vegetacao_ha'], A['imovel']['com_vegetacao_ha']),
            (a1['agua_ha'], 0.0, A['imovel']['agua_ha']), (a1['a_recompor_ha'], 0.0, A['imovel']['a_recompor_ha']), (a1['pra_pr']['a_recompor_ha'], 0.0, a1['pra_pr']['a_recompor_ha']),
            (a1['cenario_faixa_reservatorio']['a_recompor_g1_ha'], 0.0, a1['cenario_faixa_reservatorio']['a_recompor_g1_ha'])]
    for lab, v in zip(t('tab_app_rows'), vals):
        rows.append([lab] + [fmt(x) for x in v])
    M.leg_tabla(rows, col_w=[0.46, 0.18, 0.18, 0.18])
    M.leg_texto(t('w03_ver').format(a=fmt(a1['a_recompor_ha']), b=fmt(a1['pra_pr']['a_recompor_ha']), m=fmt(a1['por_arroio']['Arroio 1 (norte)']['mediana_ensamble_vs_fbds_med_m'], 0)), bold=True, color=AZUL)
    M.notas()
    return M


# ---------------------------------------------------------------- W04 --------
def W04(d):
    RL = d.v3['reserva_legal']; k = d.v3['kpi']
    M = novo(d, t('w04_t'), t('w04_s').format(ha=fmt(k['area_imovel_ha']), rl=fmt(RL['exigida_ha'])), leg_min_cm=6.3)
    ax = M.ax
    d.vc[d.vc.classe.str.startswith('remanescente')].plot(ax=ax, fc=COL['rl_rem'], ec='none', alpha=0.92, zorder=6)
    d.vc[d.vc.classe.str.startswith('APP')].plot(ax=ax, fc=COL['rl_app'], ec='none', alpha=0.92, zorder=6)
    poly_patches(ax, [d.f13], fc='none', ec='white', hatch='///', lw=0.0, zorder=8)
    poly_patches(ax, [d.corr_g1], fc=COL['rl_corr'] + 'AA', ec='#92400E', hatch='\\\\', lw=0.4, zorder=7)
    iat = unary_union(list(d.iat[d.iat.fragmento == '163756'].geometry))
    poly_patches(ax, [iat], fc='none', ec=COL['iat'], lw=1.3, ls=(0, (1, 1.2)), zorder=11)
    poly_patches(ax, list(d.ponta.geometry), fc=COL['floresta'] + '66', ec=COL['ponta'], hatch='xx', lw=0.9, zorder=9)
    rlg = unary_union(list(d.rlp.geometry))
    gpd.GeoSeries([rlg], crs=CRS_METRICO).boundary.plot(ax=ax, color='white', lw=2.0, zorder=12)
    gpd.GeoSeries([rlg], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['rl_lim'], lw=1.2, zorder=13)
    arroios(M, d, rotular=False, lw=0.8)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    loc = RL['localizacao_proposta']; f_iat = next(f for f in loc['fragmento_iat_prioridade_A'] if f['fragmento'] == '163756')
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['rl_rem']), Patch(fc=COL['rl_app']), Patch(fc=COL['rl_rem'], hatch='///', ec='white'), Patch(fc=COL['rl_corr'], hatch='\\\\', ec='#92400E'),
                     Line2D([], [], color=COL['rl_lim'], lw=1.6), Line2D([], [], color=COL['iat'], lw=1.3, ls=(0, (1, 1.2))), Patch(fc=COL['floresta'] + '66', hatch='xx', ec=COL['ponta']),
                     Line2D([], [], color=COL['fbds'], lw=0.8)],
                l + [t('rl_rem').format(a=fmt(RL['remanescente_fora_app_ha'])), t('rl_app').format(a=fmt(RL['app_vegetada_art15_ha'])), t('rl_f13'),
                     t('rl_corr').format(a=fmt(loc['corredor_g1_ha'])), t('rl_lim').format(a=fmt(loc['rl_proposta_recortada_g1_ha']), f=fmt(loc['falta_para_exigida_ha'])),
                     t('rl_iat').format(a=fmt(f_iat['dentro_ha'])), t('rl_g2'), t('curso')])
    cons = RL['variante_conservadora']
    rows = [t('tab_rl')]
    vals = [(RL['exigida_ha'], RL['exigida_ha']), (RL['vegetacao_computavel_ha'], cons['vegetacao_computavel_ha']), (RL['deficit_ha'], cons['deficit_ha']),
            (k['car_rl_averbada_ha'], k['car_rl_averbada_ha']), (loc['rl_proposta_recortada_g1_ha'], '—')]
    for lab, v in zip(t('tab_rl_rows'), vals):
        rows.append([lab.format(ha=fmt(k['area_imovel_ha']))] + [fmt(x) if not isinstance(x, str) else x for x in v])
    M.leg_tabla(rows, col_w=[0.56, 0.22, 0.22])
    M.leg_texto(t('w04_nota').format(d=fmt(RL['deficit_ha']), dc=fmt(cons['deficit_ha']))); M.notas()
    return M


# ---------------------------------------------------------------- W05 --------
def W05(d):
    m8.LANG = LANG
    m8.TV['v05_t'] = W['w05_t']; m8.TV['v05_s'] = {LANG: t('w05_s').replace('{a}', '{t}')}
    k = d.v3['kpi']
    M = novo(d, t('w05_t'), t('w05_s').format(a=fmt(k['area_imovel_ha']), b=fmt(d.g1['mapa_car']['soma_ha']), c=fmt(d.g2['mapa_car']['soma_ha'])), leg_min_cm=6.3)
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
    handles, labels = leg_glebas(d)
    rows = [t('tab_car')]
    for (cl, sc), st in estilo.items():
        tot = {}
        for u in ('G1', 'G2'):
            sub = d.car[u][(d.car[u].classe_car == cl) & (d.car[u].subclasse == sc)]
            tot[u] = float(sub.area_ha.sum()) if len(sub) else 0.0
            if len(sub):
                poly_patches(ax, sub.geometry, ec=st.get('ec', 'none'), fc=st['fc'], hatch=st.get('hatch'), lw=0.3, alpha=0.9, zorder=6)
        if tot['G1'] + tot['G2'] <= 0:
            continue
        handles.append(Patch(fc=st['fc'], hatch=st.get('hatch'), ec=st.get('ec', '#999999'), lw=0.4))
        labels.append(m4.T['car_names'][LANG][(cl, sc)])
        rows.append([m4.T['car_short'][LANG][(cl, sc)], fmt(tot['G1']), fmt(tot['G2']) if tot['G2'] > 0 else '—'])
    glebas(M, d); M.grilla(); M.norte_escala()
    M.leg_titulo(t('legenda')); M.leg_items(handles, labels)
    rows.append([t('soma'), fmt(d.g1['mapa_car']['soma_ha']), fmt(d.g2['mapa_car']['soma_ha'])])
    M.leg_tabla(rows, col_w=[0.58, 0.21, 0.21], bold_last=True)
    M.leg_texto(t('w05_nota')); M.notas()
    return M


# ---------------------------------------------------------------- W06 --------
def W06(d):
    C = d.v3['car_existente']; k = d.v3['kpi']; RL = d.v3['reserva_legal']
    M = novo(d, t('w06_t'), t('w06_s').format(a=fmt(C['area_declarada_ha']), c=C['condicao']), leg_min_cm=6.3)
    ax = M.ax
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {1: COL['floresta'] + 'BB', 2: COL['agua'] + 'BB', 4: COL['silv'] + '99'}, alpha=0.9, zorder=5, clip=d.prop_u)
    own = d.carx[d.carx.relacao == 'propio_G1']; org = d.carx[d.carx.relacao == 'cubre_G2']
    veg = own[own.cod_tema == 'VEGETACAO_NATIVA']; rl = own[own.cod_tema == 'ARL_AVERBADA']; app = own[own.cod_tema == 'APP_TOTAL']
    res = own[own.cod_tema == 'RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO']
    clip = lambda g: unary_union(list(g.geometry)).intersection(d.prop_u)
    if len(veg):
        poly_patches(ax, [clip(veg)], fc=COL['car_veg'] + '55', ec=COL['car_veg'], lw=1.0, zorder=8)
    if len(rl):
        poly_patches(ax, [clip(rl)], fc='none', ec=COL['car_rl'], hatch='///', lw=1.4, zorder=10)
    if len(app):
        poly_patches(ax, [clip(app)], fc='none', ec=COL['car_app'], lw=1.1, ls='--', zorder=9)
    if len(res):
        poly_patches(ax, [clip(res)], fc='none', ec=COL['car_res'], lw=1.3, zorder=11)
    rl2 = org[org.cod_tema == 'ARL_AVERBADA'] if (org.cod_tema == 'ARL_AVERBADA').any() else org[org.cod_tema == 'ARL_PROPOSTA']
    if len(rl2):
        poly_patches(ax, [clip(rl2).intersection(d.G2)], fc='none', ec=COL['iat'], hatch='\\\\', lw=1.0, zorder=10)
    arroios(M, d, rotular=False, lw=0.7)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    tb = {r['tema']: r for r in C['tabela']}
    g2car = d.v3['gleba2_cenarios']['B_imovel_separado_desmembrado_de_maior_4MF']['imovel_de_origem']
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['floresta'] + 'BB'), Patch(fc=COL['car_veg'] + '55', ec=COL['car_veg']), Patch(fc='none', ec=COL['car_rl'], hatch='///', lw=1.4),
                     Line2D([], [], color=COL['car_app'], lw=1.1, ls='--'), Patch(fc='none', ec=COL['car_res'], lw=1.3), Patch(fc='none', ec=COL['iat'], hatch='\\\\', lw=1.0)],
                l + [t('rf_flor'), t('car_veg').format(a=fmt(tb['Vegetacao nativa']['declarado_ha']), b=fmt(tb['Vegetacao nativa']['medido_ha'])),
                     t('car_rl').format(a=fmt(tb['Reserva Legal averbada']['declarado_ha']), b=fmt(RL['exigida_ha'])),
                     t('car_app').format(a=fmt(tb['APP']['declarado_ha']), b=fmt(tb['APP']['medido_ha'])),
                     t('car_res').format(a=fmt(tb['Reservatorio artificial (represa)']['declarado_ha']), b=fmt(tb['Reservatorio na cabeceira do Arroio 2']['declarado_ha'])),
                     t('car_g2').format(a=fmt(g2car['area_ha']), b=fmt(HPJ_G2_RL(d)))])
    rows = [t('tab_car6')]
    vals = [(tb['Area do imovel']['declarado_ha'], tb['Area do imovel']['medido_ha']), (tb['APP']['declarado_ha'], tb['APP']['medido_ha']),
            (tb['Reserva Legal averbada']['declarado_ha'], RL['exigida_ha']), (tb['Vegetacao nativa']['declarado_ha'], tb['Vegetacao nativa']['medido_ha']),
            (tb['Area consolidada']['declarado_ha'], tb['Area consolidada']['medido_ha']), (tb['Reservatorio artificial (represa)']['declarado_ha'], tb['Reservatorio artificial (represa)']['medido_ha'])]
    for lab, v in zip(t('tab_car6_rows'), vals):
        rows.append([lab, fmt(v[0]), fmt(v[1])])
    M.leg_tabla(rows, col_w=[0.5, 0.25, 0.25])
    M.leg_texto(t('w06_nota').format(p=fmt(C['cobertura_g1_pct'], 1))); M.notas()
    return M


def HPJ_G2_RL(d):
    hp = leer_json(os.path.join(HP, 'resultados_hidrologia_pro.json'))
    return hp['car']['comparacion_declarado_vs_medido']['G2']['rl_car_geom_en_gleba_ha']


# ---------------------------------------------------------------- W07 --------
def W07(d):
    C2 = d.v3['gleba2_cenarios']; k = d.v3['kpi']; RL = d.v3['reserva_legal']
    x0, y0, x1, y1 = d.G2.bounds
    ext = (x0 - 150, y0 - 330, x1 + 150, y1 + 330)
    M = novo(d, t('w07_t'), t('w07_s').format(ha=fmt(k['area_g2_ha']), alq=fmt(k['g2_alqueires'], 1)), leg_min_cm=6.4, extent=ext)
    ax = M.ax
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {1: COL['floresta'], 3: COL['antrop'] + '99', 4: COL['silv']}, alpha=0.85, zorder=5, clip=d.G2)
    poly_patches(ax, list(d.ponta.geometry), fc='none', ec=COL['ponta'], hatch='xx', lw=1.2, zorder=9)
    a = d.app['G2']
    a[a.situacao == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='white', lw=0.5, alpha=0.95, zorder=8)
    poly_patches(ax, [d.app30.intersection(d.G2)], fc='none', ec=COL['app_lim'], lw=0.9, ls='--', zorder=12)
    d.arr['G2'].plot(ax=ax, color=COL['fbds'], lw=1.6, zorder=11)
    org = d.carx[(d.carx.relacao == 'cubre_G2') & (d.carx.cod_tema == 'AREA_IMOVEL')]
    if len(org):
        # Regla del cliente: NADA fuera del perimetro -> el limite del CAR de origen se recorta al interior de las glebas
        _int = gpd.GeoSeries([d.G1, d.G2], crs=CRS_METRICO).union_all().buffer(1)
        _segs = [g.boundary.intersection(_int) for g in org.geometry]
        _segs = [s for s in _segs if not s.is_empty]
        if _segs:
            plot_lines(ax, _segs, color=COL['iat'], lw=1.2, ls=(0, (2, 1.5)), zorder=29)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=2.4, zorder=30)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['prop'], lw=1.4, zorder=31)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=3.0, zorder=32)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['g2'], lw=2.0, zorder=33)
    patch_agujeros(ax, d.G1, fc=FORA + 'DD', ec='none', lw=0, zorder=26)
    c = unary_union(d.ponta.geometry).representative_point()
    ax.annotate(('Ponta norte\n%s ha — a conferir' if LANG == 'pt' else 'Punta norte\n%s ha — a verificar') % fmt(k['app_g2_ha'] and d.v3['vegetacao']['g2_floresta_na_imagem_nao_computada_ha']),
                xy=(c.x, c.y), xytext=(c.x + 10, c.y - 190), fontsize=5.6, ha='center', va='center', zorder=41, fontweight='bold', color=COL['ponta'],
                arrowprops=dict(arrowstyle='-', lw=0.6, color=COL['ponta']), bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['ponta'], lw=0.8, alpha=0.95))
    ca = unary_union(a.geometry).representative_point()
    ax.annotate('APP %s ha' % fmt(k['app_g2_ha']), xy=(ca.x, ca.y), xytext=(ca.x + 60, ca.y + 70), fontsize=5.4, ha='center', va='center', zorder=41, color='white', fontweight='bold',
                arrowprops=dict(arrowstyle='-', lw=0.6, color=COL['app_conf']), bbox=dict(boxstyle='round,pad=0.25', fc=COL['app_conf'], ec='white', lw=0.5, alpha=0.95))
    xm = (x0 + x1) / 2
    ax.text(xm, (y0 + y1) / 2 - 80, t('g2').format(ha=fmt(k['area_g2_ha']), alq=fmt(k['g2_alqueires'], 1)), fontsize=6.2, fontweight='bold', ha='center', va='center', rotation=90, zorder=40,
            bbox=dict(boxstyle='round,pad=0.25', fc=COL['g2'], ec='black', lw=0.5, alpha=0.9))
    ax.text(x0 - 75, (y0 + y1) / 2 + 300, t('g1').format(ha=fmt(k['area_g1_ha'])), fontsize=5.4, fontweight='bold', ha='center', va='center', rotation=90, zorder=40,
            bbox=dict(boxstyle='round,pad=0.2', fc=COL['prop'], ec='black', lw=0.4, alpha=0.9))
    M.grilla(250); M.norte_escala(250)
    B = C2['B_imovel_separado_desmembrado_de_maior_4MF']['imovel_de_origem']; ap = C2['app_g2']
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['g2'], lw=2.4), Line2D([], [], color=COL['prop'], lw=2.0), Line2D([], [], color=COL['iat'], lw=1.2, ls=(0, (2, 1.5))), Patch(fc=FORA, ec='#BBBBBB'),
                 Patch(fc=COL['floresta'], hatch='xx', ec=COL['ponta']), Patch(fc=COL['antrop'], ec='#BBBBBB'), Patch(fc=COL['silv'], hatch='////', ec='#4E4E00'),
                 Patch(fc=COL['app_conf'], ec='white'), Line2D([], [], color=COL['fbds'], lw=1.6)],
                [m8.TV['lim_g2'][LANG].format(ha=fmt(k['area_g2_ha']), alq=fmt(k['g2_alqueires'], 1)), m8.TV['lim_g1'][LANG].format(ha=fmt(k['area_g1_ha'])),
                 t('car_g2_lim').format(a=fmt(B['area_ha']), mf=fmt(B['mod_fiscal_declarado'])), m8.TV['fora'][LANG],
                 t('ponta').format(a=fmt(d.v3['vegetacao']['g2_floresta_na_imagem_nao_computada_ha'])),
                 t('cl_antr').format(a='', b='').replace('G1  · G2  ha', '%s ha' % fmt(d.g2['vegetacao']['area_agricola_car_ha'])), t('cl_silv').format(a=fmt(d.g2['vegetacao']['silvicultura_ha'])),
                 t('app_g2').format(m=fmt(ap['curso_m'], 0), a=fmt(ap['exigida_fbds_ha']), mn=fmt(ap['envolvente_ha'][0]), mx=fmt(ap['envolvente_ha'][1])), t('curso')])
    M.leg_texto(t('w07_kpi'), bold=True, color=AZUL, fs=M.fs + 0.8)
    A_ = C2['A_imovel_unico_principal']; Cc = C2['C_excecao_art67_origem_ate_4MF_em_2008']
    for s in t('w07_txt'):
        M.leg_texto(s.format(g2rl=fmt(A_['rl_parcela_g2_ha']), g1rl=fmt(A_['rl_parcela_g1_ha']), rl=fmt(A_['rl_exigida_imovel_ha']), d=fmt(A_['deficit_ha']), car=fmt(B['area_ha']), mf=fmt(B['mod_fiscal_declarado']),
                             v08=fmt(Cc['vegetacao_2008_g2_mapbiomas_ha_indicio']), m=fmt(ap['curso_m'], 0), app=fmt(ap['exigida_fbds_ha']), sup=fmt(C2['supressao_pos_2008_indicio_ha'])))
    M.notas()
    return M


def guardar(M, nome):
    out_dir = os.path.join(MAPAS_V3, '' if LANG == 'pt' else 'ES')
    os.makedirs(out_dir, exist_ok=True)
    ruta = os.path.join(out_dir, nome + '.png')
    M.fig.savefig(ruta, dpi=DPI, facecolor='white'); plt.close(M.fig)
    log('  -> %s' % ruta)


def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='pt', choices=['pt', 'es']); ap.add_argument('--solo', default='')
    a = ap.parse_args(); LANG = a.lang
    m4.LANG = LANG; m8.LANG = LANG
    m8.TV['notas'] = W['notas']
    m8.TV['arr_lbl'] = W['arr_lbl']
    log('=' * 78); log('an_13_mapas_v3 — lang=%s' % LANG); log('=' * 78)
    d = DadosV3()
    quiere = set(a.solo.split(',')) if a.solo else None
    tareas = [('W01_vegetacao_nativa', W01), ('W02_hidrografia', W02), ('W03_app_mata_ciliar', W03), ('W04_reserva_legal', W04), ('W05_mapa_car_sicar', W05),
              ('W06_car_declarado_vs_medido', W06), ('W07_gleba2_terra_limpa', W07)]
    for nome, fn in tareas:
        if quiere and nome.split('_')[0] not in quiere:
            continue
        guardar(fn(d), nome)
    log('an_13 listo')


if __name__ == '__main__':
    main()
