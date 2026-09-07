# -*- coding: utf-8 -*-
"""an_16_mapas_v4 — mapas X01..X09 da versao 4 (ortofoto de drone 22/05/2026), so o interior do perimetro.

    python an_16_mapas_v4.py --lang pt   -> 03_MAPAS_V4/*.png
    python an_16_mapas_v4.py --lang es   -> 03_MAPAS_V4/ES/*.png
    python an_16_mapas_v4.py --solo X03,X08

Reutiliza a classe Mapa (an_04), os helpers de an_08/an_13 (glebas, arroios, legenda) e a mascara "so o interior".
Fundo: ortofoto RGBA 0,5 m (reamostrada do GSD 5 cm) mascarada ao perimetro; na faixa norte sem voo entra a cena S2
(reamostrada) para nao deixar buraco; nos insets de detalhe (X08) le-se o original a 5 cm por janela.
Toda cifra rotulada sai de 05_ORTOFOTO/resultados_v4.json (ortho_06), de cauce/cauce_resumo.json (ortho_07) ou dos JSON v3
(faixa sem voo, CAR, cenarios da Gleba 2); nada se recalcula aqui. As unicas geometrias derivadas sao de DESENHO.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, R, CRS_METRICO, leer_json, log   # noqa: E402
import an_04_mapas as m4                                                   # noqa: E402
import an_08_mapas_interior as m8                                          # noqa: E402
import an_13_mapas_v3 as m13                                               # noqa: E402
from an_04_mapas import COL, AZUL, TEAL, LIMA, GRIS, fmt, fmt_utm, poly_patches, plot_lines, raster_clases, DPI, Mapa   # noqa: E402
from an_08_mapas_interior import novo, glebas, leg_glebas, arroios, patch_agujeros, FORA, extent_interior              # noqa: E402
from an_13_mapas_v3 import DadosV3                                                                                     # noqa: E402

import matplotlib                                  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402
from matplotlib.patches import Patch               # noqa: E402
from matplotlib.ticker import FuncFormatter        # noqa: E402
import geopandas as gpd                            # noqa: E402
import rasterio                                    # noqa: E402
from rasterio import features                      # noqa: E402
from rasterio.enums import Resampling              # noqa: E402
from rasterio.windows import from_bounds           # noqa: E402
from shapely.geometry import box, Point, LineString  # noqa: E402
from shapely.ops import unary_union                # noqa: E402

ORTO = os.path.join(PROYECTO, '05_ORTOFOTO')
CAUCE = os.path.join(ORTO, 'cauce')
MAPAS_V4 = os.path.join(PROYECTO, '03_MAPAS_V4')
ODM_5CM = r'D:\PIXADVISOR\Vuelos-Drone\Ortofoto-S.A\odm_orthophoto.tif'
LANG = 'pt'
COL.update({'arb': '#1B5E20', 'arb_sem': '#33691E', 'arbu': '#8BC34A', 'pasto': '#FFF176', 'solo': '#D7CCC8', 'constr': '#616161',
            'agua_o': '#1E88E5', 'vaso': '#90CAF9', 'acude': '#0D47A1', 'talweg': '#FF9800', 'rec_pasto': '#F57C00', 'rec_cult': '#D32F2F',
            'rec_arv': '#AD1457', 'cobert': '#7B1FA2', 'secao': '#FFEB3B', 'lagoa': '#4FC3F7'})
VEG_CLASSES = {1: 'arb', 2: 'arb', 9: 'arb_sem', 3: 'arbu', 4: 'pasto', 5: 'solo', 6: 'agua_o', 7: 'constr'}

X = {
    'fonte': {'pt': 'Fundo: ortofoto de drone 22/05/2026 (GSD 5 cm, ODM, sem GCP; reamostrada a 0,5 m) · faixa norte sem voo: Sentinel-2C 29/08/2026',
              'es': 'Fondo: ortofoto de dron 22/05/2026 (GSD 5 cm, ODM, sin GCP; remuestreada a 0,5 m) · faja norte sin vuelo: Sentinel-2C 29/08/2026'},
    'notas': {'pt': 'SIRGAS 2000 / UTM 22S (EPSG:31982) · Hidrografia FBDS/IAT 2013 (1:25.000) disponibilizada pelo IAT · SÓ O INTERIOR DO PERÍMETRO (exterior em cinza) · '
                    'PARECER TÉCNICO PRELIMINAR: não substitui laudo; borda da calha, perenidade e limites a confirmar em campo (GNSS).',
              'es': 'SIRGAS 2000 / UTM 22S (EPSG:31982) · Hidrografía FBDS/IAT 2013 (1:25.000) publicada por el IAT · SOLO EL INTERIOR DEL PERÍMETRO (exterior en gris) · '
                    'INFORME TÉCNICO PRELIMINAR: no sustituye un informe pericial; borde del cauce, perennidad y límites a confirmar en campo (GNSS).'},
    'legenda': {'pt': 'Legenda', 'es': 'Leyenda'},
    'arroio': {'pt': 'Arroio', 'es': 'Arroyo'},
    'arr_lbl': {'pt': 'Arroio {n}\n{m} m', 'es': 'Arroyo {n}\n{m} m'},
    'curso': {'pt': "Eixo do curso d'água FBDS 2013 (referência da APP)", 'es': 'Eje del curso de agua FBDS 2013 (referencia de la APP)'},
    'talweg': {'pt': 'Talvegue no DTM do drone (indicativo: sob dossel o DTM é a copa)', 'es': 'Talweg en el DTM del dron (indicativo: bajo dosel el DTM es la copa)'},
    'sem_orto': {'pt': 'Faixa sem ortofoto (N > 7.404.007; {a} ha): fundo S2, classes v3', 'es': 'Faja sin ortofoto (N > 7.404.007; {a} ha): fondo S2, clases v3'},
    'lim_dtm': {'pt': 'Limite sul do DSM/DTM: {a} ha da G1 sem elevação', 'es': 'Límite sur del DSM/DTM: {a} ha de G1 sin elevación'},
    'nasc_prov': {'pt': 'Nascente FBDS 306158 — PROVÁVEL (várzea; água a {d} m; perenidade não verificável por imagem)', 'es': 'Naciente FBDS 306158 — PROBABLE (várzea; agua a {d} m; perennidad no verificable por imagen)'},
    'nasc_nao': {'pt': 'dem_2 — NÃO nascente (área lavrada, sem água nem canal)', 'es': 'dem_2 — NO naciente (área labrada, sin agua ni canal)'},
    'represa': {'pt': 'Represa (Arroio 3): espelho {a} ha em 22/05/2026 (>= 1 ha)', 'es': 'Represa (Arroyo 3): espejo {a} ha el 22/05/2026 (>= 1 ha)'},
    'vaso': {'pt': 'Vaso indicador (água + faixa sem vegetação) — {a} ha', 'es': 'Vaso indicador (agua + faja sin vegetación) — {a} ha'},
    'acude': {'pt': '2º reservatório na cabeceira do Arroio 2 — {a} ha (CAR {b} ha)', 'es': '2º reservorio en la cabecera del Arroyo 2 — {a} ha (CAR {b} ha)'},
    'lagoas': {'pt': 'Lâminas menores (8; {a} ha no total)', 'es': 'Láminas menores (8; {a} ha en total)'},
    # X01
    'x01_t': {'pt': 'X01 · Ortofoto do imóvel e inventário hídrico', 'es': 'X01 · Ortofoto del inmueble e inventario hídrico'},
    'x01_s': {'pt': 'Voo de drone 22/05/2026 · imóvel único {ha} ha · arroios FBDS · nascente · represa · açude', 'es': 'Vuelo de dron 22/05/2026 · inmueble único {ha} ha · arroyos FBDS · naciente · represa · embalse'},
    'tab_x01': {'pt': ['Curso (G1)', 'FBDS m', 'Orto %', 'DTM %', 'Largura est.'], 'es': ['Curso (G1)', 'FBDS m', 'Orto %', 'DTM %', 'Ancho est.']},
    'x01_nota': {'pt': 'Largura da calha: estimativa M3 (geometria hidráulica) e classe FBDS <= 10 m; sem medição direta na ortofoto (dossel contínuo) — protocolo de campo M5. '
                       'Arroio 3 e represa sem DSM/DTM. Arroio 2 nasce na gleba; confluência dos arroios 1 e 2 fora do limite oeste.',
                 'es': 'Ancho del cauce: estimación M3 (geometría hidráulica) y clase FBDS <= 10 m; sin medición directa en la ortofoto (dosel continuo) — protocolo de campo M5. '
                       'Arroyo 3 y represa sin DSM/DTM. El Arroyo 2 nace en la gleba; la confluencia de los arroyos 1 y 2 queda fuera del lindero oeste.'},
    # X02
    'x02_t': {'pt': 'X02 · Vegetação a 0,5 m: ortofoto + CHM', 'es': 'X02 · Vegetación a 0,5 m: ortofoto + CHM'},
    'x02_s': {'pt': 'Classificação ortofoto + DSM/DTM (RF, acc 0,997) · MMU 25 m² · fragmentos com altura (CHM)', 'es': 'Clasificación ortofoto + DSM/DTM (RF, acc 0,997) · MMU 25 m² · fragmentos con altura (CHM)'},
    'cl_arb': {'pt': 'Arbórea (altura medida ou dossel fechado) — G1 {a} · G2 {b} ha', 'es': 'Arbórea (altura medida o dosel cerrado) — G1 {a} · G2 {b} ha'},
    'cl_arb_sem': {'pt': 'Arbórea/arbustiva sem CHM (sul, sem DSM) — {a} ha', 'es': 'Arbórea/arbustiva sin CHM (sur, sin DSM) — {a} ha'},
    'cl_arbu': {'pt': 'Arbustiva / regeneração — G1 {a} · G2 {b} ha', 'es': 'Arbustiva / regeneración — G1 {a} · G2 {b} ha'},
    'cl_pasto': {'pt': 'Herbácea / pasto — G1 {a} · G2 {b} ha', 'es': 'Herbácea / pastura — G1 {a} · G2 {b} ha'},
    'cl_solo': {'pt': 'Solo / cultivo — G1 {a} · G2 {b} ha', 'es': 'Suelo / cultivo — G1 {a} · G2 {b} ha'},
    'cl_agua_o': {'pt': 'Água (22/05/2026) — {a} ha', 'es': 'Agua (22/05/2026) — {a} ha'},
    'cl_constr': {'pt': 'Construções — {a} ha · silvicultura: 0,00 ha (não confirmada)', 'es': 'Construcciones — {a} ha · silvicultura: 0,00 ha (no confirmada)'},
    'frag_lbl': {'pt': 'Frag. {id} · {ha} ha\narbóreo {p}% · h {h} m (P90 {p90})', 'es': 'Frag. {id} · {ha} ha\narbóreo {p}% · h {h} m (P90 {p90})'},
    'frag_lbl_sem': {'pt': 'Frag. {id} · {ha} ha\nsem CHM', 'es': 'Frag. {id} · {ha} ha\nsin CHM'},
    'frag': {'pt': 'Fragmento (polígono RF S2 v3) com indicador de altura', 'es': 'Fragmento (polígono RF S2 v3) con indicador de altura'},
    'tab_veg': {'pt': ['Classe 0,5 m (ha)', 'G1', 'G2', 'Imóvel'], 'es': ['Clase 0,5 m (ha)', 'G1', 'G2', 'Inm.']},
    'tab_veg_rows': {'pt': ['Arbórea (incl. sem CHM)', 'Arbustiva', 'Herbácea / pasto', 'Solo / cultivo', 'Água', 'Construções', 'Sem dado (faixa sem voo)', 'Nativa (arb. + arbustiva)'],
                     'es': ['Arbórea (incl. sin CHM)', 'Arbustiva', 'Herbácea / pastura', 'Suelo / cultivo', 'Agua', 'Construcciones', 'Sin dato (faja sin vuelo)', 'Nativa (arb. + arbustiva)']},
    'x02_nota': {'pt': 'Altura = CHM híbrido (DSM − DTM; FABDEM sob dossel): SUBESTIMA sob dossel fechado (frag. 13: altura medida em 23% da área arbórea; frag. 2: 47%). '
                       'O indicador "inicial–médio" (CONAMA 2/1994) é só indicador: DAP, área basal e estratos exigem campo. A silvicultura do RF S2 (1,06 ha) não tem fileiras na ortofoto.',
                 'es': 'Altura = CHM híbrido (DSM − DTM; FABDEM bajo dosel): SUBESTIMA bajo dosel cerrado (frag. 13: altura medida en el 23% del área arbórea; frag. 2: 47%). '
                       'El indicador "inicial–medio" (CONAMA 2/1994) es solo indicador: DAP, área basal y estratos exigen campo. La silvicultura del RF S2 (1,06 ha) no tiene hileras en la ortofoto.'},
    # X03
    'x03_t': {'pt': 'X03 · Mata ciliar (APP) sobre a ortofoto', 'es': 'X03 · Mata ciliar (APP) sobre la ortofoto'},
    'x03_s': {'pt': 'Art. 4º: 30 m dos cursos até 10 m + 50 m da nascente · eixo FBDS · cobertura a 0,5 m (22/05/2026)', 'es': 'Art. 4º: 30 m de cursos hasta 10 m + 50 m de la naciente · eje FBDS · cobertura a 0,5 m (22/05/2026)'},
    'app_conf': {'pt': 'APP com vegetação nativa (ortofoto 0,5 m) — {a} ha', 'es': 'APP con vegetación nativa (ortofoto 0,5 m) — {a} ha'},
    'app_agua': {'pt': 'APP com água (22/05/2026) — {a} ha', 'es': 'APP con agua (22/05/2026) — {a} ha'},
    'app_rec_p': {'pt': 'A recompor: pasto / herbácea — {a} ha', 'es': 'A recomponer: pastura / herbácea — {a} ha'},
    'app_rec_c': {'pt': 'A recompor: cultivo / solo — {a} ha', 'es': 'A recomponer: cultivo / suelo — {a} ha'},
    'app_rec_a': {'pt': 'A recompor: árvores isoladas (< 0,05 ha) — {a} ha', 'es': 'A recomponer: árboles aislados (< 0,05 ha) — {a} ha'},
    'app_lim': {'pt': 'Limite da APP exigível (30 / 50 m do eixo FBDS) — {a} ha [{mn}; {mx}]', 'es': 'Límite de la APP exigible (30 / 50 m del eje FBDS) — {a} ha [{mn}; {mx}]'},
    'faixa20': {'pt': 'Faixa PRA-PR (20 m / 15 m) — recompor {a} ha', 'es': 'Faja PRA-PR (20 m / 15 m) — recomponer {a} ha'},
    'reserv_faixa': {'pt': 'Faixa 30 m da represa SE o IAT a aplicar — exigível {a}, recompor {b} ha', 'es': 'Faja 30 m de la represa SI el IAT la aplica — exigible {a}, recomponer {b} ha'},
    'tab_app': {'pt': ['APP (ha)', 'G1', 'G2', 'Imóvel'], 'es': ['APP (ha)', 'G1', 'G2', 'Inm.']},
    'tab_app_rows': {'pt': ['Exigida (eixo FBDS)', 'Envolvente mín. (0,5 m)', 'Envolvente máx.', 'Com vegetação nativa', 'Água', 'A recompor', '   pasto / herbácea', '   cultivo / solo', '   árvores isoladas', 'Recompor PRA-PR (20 m)', 'Faixa represa: exigível', 'Faixa represa: a recompor'],
                     'es': ['Exigida (eje FBDS)', 'Envolvente mín. (0,5 m)', 'Envolvente máx.', 'Con vegetación nativa', 'Agua', 'A recomponer', '   pastura / herbácea', '   cultivo / suelo', '   árboles aislados', 'Recomponer PRA-PR (20 m)', 'Faja represa: exigible', 'Faja represa: a recomponer']},
    'x03_ver': {'pt': 'NÃO CONFORME: {a} ha a recompor ({b} ha pela faixa PRA-PR). APP medida do EIXO FBDS: a borda da calha do leito regular NÃO pôde ser medida (dossel fechado, DTM fotogramétrico = copa; Arroio 1: 3 de 26 seções com solo, Arroio 2: 0 de 56) — levantar com GNSS.',
                'es': 'NO CONFORME: {a} ha a recomponer ({b} ha por la faja PRA-PR). APP medida desde el EJE FBDS: el borde del cauce regular NO pudo medirse (dosel cerrado, DTM fotogramétrico = copa; Arroyo 1: 3 de 26 secciones con suelo, Arroyo 2: 0 de 56) — levantar con GNSS.'},
    # X04
    'x04_t': {'pt': 'X04 · Reserva Legal do imóvel único (20%) — v4', 'es': 'X04 · Reserva Legal del inmueble único (20%) — v4'},
    'x04_s': {'pt': 'Art. 12 (20% de {ha} ha = {rl} ha) · art. 15 · vegetação computável a 0,5 m · G2 terra limpa', 'es': 'Art. 12 (20% de {ha} ha = {rl} ha) · art. 15 · vegetación computable a 0,5 m · G2 tierra limpia'},
    'rl_rem': {'pt': 'Vegetação nativa computável fora da APP — {a} ha', 'es': 'Vegetación nativa computable fuera de la APP — {a} ha'},
    'rl_app': {'pt': 'APP vegetada computável (art. 15) — {a} ha', 'es': 'APP vegetada computable (art. 15) — {a} ha'},
    'rl_f13': {'pt': 'Fragmento 13 — regeneração a confirmar (excluído na variante conservadora)', 'es': 'Fragmento 13 — regeneración a confirmar (excluido en la variante conservadora)'},
    'rl_corr': {'pt': 'Corredor de recomposição proposto (v3) — {a} ha', 'es': 'Corredor de recomposición propuesto (v3) — {a} ha'},
    'rl_lim': {'pt': 'RL proposta (G1, v3) — {a} ha; a rever com a vegetação v4', 'es': 'RL propuesta (G1, v3) — {a} ha; a revisar con la vegetación v4'},
    'rl_iat': {'pt': 'Fragmento IAT prioridade A (23 anos) — {a} ha no imóvel', 'es': 'Fragmento IAT prioridad A (23 años) — {a} ha en el inmueble'},
    'rl_g2': {'pt': 'Vegetação da ponta norte da G2 ({a} ha) — não computada', 'es': 'Vegetación de la punta norte de G2 ({a} ha) — no computada'},
    'tab_rl': {'pt': ['RL (ha)', 'Principal', 'Conserv.', 'Ponta N'], 'es': ['RL (ha)', 'Principal', 'Conserv.', 'Punta N']},
    'tab_rl_rows': {'pt': ['Exigida (20%)', 'Computável', 'Envolvente 0,5 m', 'Déficit', 'Atendimento (%)', 'CAR averba'], 'es': ['Exigida (20%)', 'Computable', 'Envolvente 0,5 m', 'Déficit', 'Cumplimiento (%)', 'CAR inscribe']},
    'x04_nota': {'pt': 'NÃO CONFORME: déficit de {d} ha [{mn}; {mx}] (conservador {dc} ha, sem o fragmento 13; {dp} ha se a mata da ponta norte for do imóvel). A RL de 31,55 ha é do imóvel inteiro (art. 14). '
                       'A ortofoto acrescenta {dv} ha de vegetação computável em relação à v3 (S2 10 m); o estágio sucessional segue exigindo campo.',
                 'es': 'NO CONFORME: déficit de {d} ha [{mn}; {mx}] (conservador {dc} ha, sin el fragmento 13; {dp} ha si el monte de la punta norte fuera del inmueble). La RL de 31,55 ha es del inmueble entero (art. 14). '
                       'La ortofoto agrega {dv} ha de vegetación computable respecto de la v3 (S2 10 m); el estadio sucesional sigue exigiendo campo.'},
    # X05
    'x05_t': {'pt': 'X05 · Uso e cobertura na nomenclatura CAR/SICAR', 'es': 'X05 · Uso y cobertura en la nomenclatura CAR/SICAR'},
    'x05_s': {'pt': 'Sem sobreposição · Módulo de Cadastro do SICAR · ortofoto 0,5 m · fecha em {a} ha ({b} + {c})', 'es': 'Sin superposición · Módulo de Catastro del SICAR · ortofoto 0,5 m · cierra en {a} ha ({b} + {c})'},
    'tab_car': {'pt': ['Classe CAR / subclasse', 'G1', 'G2'], 'es': ['Clase CAR / subclase', 'G1', 'G2']},
    'soma': {'pt': 'Soma', 'es': 'Suma'},
    'x05_nota': {'pt': 'Somas sobre áreas a 3 decimais. "Perene" é nomenclatura SICAR obrigatória: perenidade NÃO verificada. Faixa sem voo classificada com o RF S2 (v3). Camada no formato do SICAR, a conferir pelo responsável pela inscrição.',
                 'es': 'Sumas sobre áreas a 3 decimales. "Perene" es nomenclatura SICAR obligatoria: perennidad NO verificada. Faja sin vuelo clasificada con el RF S2 (v3). Capa en el formato del SICAR, a verificar por el responsable de la inscripción.'},
    'car_names': {'pt': {("APP - Nascente ou olho d'agua perene", 'conforme'): "APP – nascente ou olho d'água perene: conforme",
                         ("APP - Nascente ou olho d'agua perene", 'a recompor'): "APP – nascente: a recompor",
                         ("APP - Curso d'agua natural de ate 10 metros", 'conforme'): "APP – curso d'água até 10 m: conforme",
                         ("APP - Curso d'agua natural de ate 10 metros", 'agua'): "APP – curso d'água até 10 m: água",
                         ("APP - Curso d'agua natural de ate 10 metros", 'a recompor'): "APP – curso d'água até 10 m: a recompor",
                         ('Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua'): 'Reservatório artificial por barramento: espelho',
                         ('Reservatorio artificial / lagoa', 'espelho d agua'): 'Reservatório artificial / lagoa fora da APP',
                         ('Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP'): 'Remanescente de vegetação nativa',
                         ('Area Consolidada', 'construcoes'): 'Área consolidada – construções',
                         ('Area Consolidada', 'pasto/herbacea'): 'Área consolidada – pasto / herbácea',
                         ('Area Consolidada', 'arvores isoladas (< 0,05 ha)'): 'Área consolidada – árvores isoladas (< 0,05 ha)',
                         ('Area Consolidada', 'uso agricola'): 'Área consolidada – uso agrícola'},
                  'es': {("APP - Nascente ou olho d'agua perene", 'conforme'): "APP – nascente ou olho d'água perene: conforme",
                         ("APP - Nascente ou olho d'agua perene", 'a recompor'): "APP – naciente: a recomponer",
                         ("APP - Curso d'agua natural de ate 10 metros", 'conforme'): "APP – curso de agua hasta 10 m: conforme",
                         ("APP - Curso d'agua natural de ate 10 metros", 'agua'): "APP – curso de agua hasta 10 m: agua",
                         ("APP - Curso d'agua natural de ate 10 metros", 'a recompor'): "APP – curso de agua hasta 10 m: a recomponer",
                         ('Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua'): 'Reservorio artificial por represamiento: espejo',
                         ('Reservatorio artificial / lagoa', 'espelho d agua'): 'Reservorio artificial / laguna fuera de la APP',
                         ('Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP'): 'Remanente de vegetación nativa',
                         ('Area Consolidada', 'construcoes'): 'Área consolidada – construcciones',
                         ('Area Consolidada', 'pasto/herbacea'): 'Área consolidada – pastura / herbácea',
                         ('Area Consolidada', 'arvores isoladas (< 0,05 ha)'): 'Área consolidada – árboles aislados (< 0,05 ha)',
                         ('Area Consolidada', 'uso agricola'): 'Área consolidada – uso agrícola'}},
    'car_short': {'pt': {("APP - Nascente ou olho d'agua perene", 'conforme'): 'APP nascente: conforme', ("APP - Nascente ou olho d'agua perene", 'a recompor'): 'APP nascente: a recompor',
                         ("APP - Curso d'agua natural de ate 10 metros", 'conforme'): 'APP curso <= 10 m: conforme', ("APP - Curso d'agua natural de ate 10 metros", 'agua'): 'APP curso <= 10 m: água',
                         ("APP - Curso d'agua natural de ate 10 metros", 'a recompor'): 'APP curso <= 10 m: a recompor',
                         ('Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua'): 'Reservatório (barramento)',
                         ('Reservatorio artificial / lagoa', 'espelho d agua'): 'Reservatório / lagoa fora APP', ('Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP'): 'Remanescente veg. nativa',
                         ('Area Consolidada', 'construcoes'): 'Consolidada – construções', ('Area Consolidada', 'pasto/herbacea'): 'Consolidada – pasto/herbácea',
                         ('Area Consolidada', 'arvores isoladas (< 0,05 ha)'): 'Consolidada – árvores isoladas', ('Area Consolidada', 'uso agricola'): 'Consolidada – uso agrícola'},
                  'es': {("APP - Nascente ou olho d'agua perene", 'conforme'): 'APP naciente: conforme', ("APP - Nascente ou olho d'agua perene", 'a recompor'): 'APP naciente: a recomponer',
                         ("APP - Curso d'agua natural de ate 10 metros", 'conforme'): 'APP curso <= 10 m: conforme', ("APP - Curso d'agua natural de ate 10 metros", 'agua'): 'APP curso <= 10 m: agua',
                         ("APP - Curso d'agua natural de ate 10 metros", 'a recompor'): 'APP curso <= 10 m: a recomponer',
                         ('Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua'): 'Reservorio (represamiento)',
                         ('Reservatorio artificial / lagoa', 'espelho d agua'): 'Reservorio / laguna fuera APP', ('Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP'): 'Remanente veg. nativa',
                         ('Area Consolidada', 'construcoes'): 'Consolidada – construcciones', ('Area Consolidada', 'pasto/herbacea'): 'Consolidada – pastura/herbácea',
                         ('Area Consolidada', 'arvores isoladas (< 0,05 ha)'): 'Consolidada – árboles aislados', ('Area Consolidada', 'uso agricola'): 'Consolidada – uso agrícola'}},
    # X06
    'x06_t': {'pt': 'X06 · CAR existente (declarado) vs medido na ortofoto', 'es': 'X06 · CAR existente (declarado) vs medido en la ortofoto'},
    'x06_s': {'pt': 'CAR PR-4124301-F127CD1E… ({a} ha, "{c}") sobre a vegetação a 0,5 m · retificação', 'es': 'CAR PR-4124301-F127CD1E… ({a} ha, "{c}") sobre la vegetación a 0,5 m · rectificación'},
    'car_app': {'pt': 'APP declarada no CAR — {a} ha (medida {b} ha)', 'es': 'APP declarada en el CAR — {a} ha (medida {b} ha)'},
    'car_rl': {'pt': 'Reserva Legal averbada — {a} ha (exigida {b} ha)', 'es': 'Reserva Legal inscrita — {a} ha (exigida {b} ha)'},
    'car_veg': {'pt': 'Vegetação nativa declarada — {a} ha (medida {b} ha)', 'es': 'Vegetación nativa declarada — {a} ha (medida {b} ha)'},
    'car_res': {'pt': 'Reservatórios declarados — {a} + {b} ha (medidos {c} + {d} ha)', 'es': 'Reservorios declarados — {a} + {b} ha (medidos {c} + {d} ha)'},
    'car_g2': {'pt': 'CAR de origem da G2 (PR-4124301-5223911747…, {a} ha) — RL declarada dentro da G2', 'es': 'CAR de origen de G2 (PR-4124301-5223911747…, {a} ha) — RL declarada dentro de G2'},
    'orto_arb': {'pt': 'Vegetação arbórea/arbustiva na ortofoto (fundo)', 'es': 'Vegetación arbórea/arbustiva en la ortofoto (fondo)'},
    'tab_car6': {'pt': ['Tema (ha)', 'CAR', 'Medido v4'], 'es': ['Tema (ha)', 'CAR', 'Medido v4']},
    'tab_car6_rows': {'pt': ['Área do imóvel', 'APP', 'Reserva Legal', 'Vegetação nativa', 'Área consolidada', 'Represa (espelho)', '2º reservatório'], 'es': ['Área del inmueble', 'APP', 'Reserva Legal', 'Vegetación nativa', 'Área consolidada', 'Represa (espejo)', '2º reservorio']},
    'x06_nota': {'pt': 'Retificar: RL de {r1} para {r2} ha (imóvel único), vegetação nativa de {v1} para {v2} ha, incluir a Gleba 2 (IN MMA 2/2014 art. 32), declarar o espelho medido ({e} ha) e o 2º reservatório ({e2} ha; existe). '
                       'Dique da represa: o FBDS 2013 fica 9 m a oeste e o CAR 8 m a leste do dique visto na ortofoto.',
                 'es': 'Rectificar: RL de {r1} a {r2} ha (inmueble único), vegetación nativa de {v1} a {v2} ha, incluir la Gleba 2 (IN MMA 2/2014 art. 32), declarar el espejo medido ({e} ha) y el 2º reservorio ({e2} ha; existe). '
                       'Dique de la represa: el FBDS 2013 queda 9 m al oeste y el CAR 8 m al este del dique visto en la ortofoto.'},
    # X07
    'x07_t': {'pt': 'X07 · Gleba 2 ("os 6 alqueires"): terra limpa — v4', 'es': 'X07 · Gleba 2 ("los 6 alqueires"): tierra limpia — v4'},
    'x07_s': {'pt': '{ha} ha = {alq} alqueires · comprada sem monte · ortofoto 0,5 m · ponta norte a conferir', 'es': '{ha} ha = {alq} alqueires · comprada sin monte · ortofoto 0,5 m · punta norte a verificar'},
    'ponta': {'pt': 'Ponta norte: {a} ha de vegetação nativa NÃO computada — limite a conferir com a escritura/SIGEF', 'es': 'Punta norte: {a} ha de vegetación nativa NO computada — límite a verificar con la escritura/SIGEF'},
    'app_g2': {'pt': 'APP do Arroio 1 ({m} m): {a} ha [{mn}; {mx}] com vegetação; 0 se o limite for corrigido', 'es': 'APP del Arroyo 1 ({m} m): {a} ha [{mn}; {mx}] con vegetación; 0 si se corrige el límite'},
    'car_g2_lim': {'pt': 'CAR de origem PR-4124301-5223911747… ({a} ha = {mf} MF)', 'es': 'CAR de origen PR-4124301-5223911747… ({a} ha = {mf} MF)'},
    'x07_kpi': {'pt': 'Quanto monte precisa a Gleba 2?', 'es': '¿Cuánto monte necesita la Gleba 2?'},
    'x07_txt': {'pt': ['(A) IMÓVEL ÚNICO — principal (IN MMA 2/2014 art. 32): sem conta própria. Os 6 alqueires somam {g2rl} ha à RL do imóvel ({g1rl} -> {rl} ha), localizável em qualquer gleba (art. 14), e aportam 0 ha de vegetação. Déficit do imóvel (v4): {d} ha (conserv. {dc}).',
                       '(B) IMÓVEL SEPARADO, desmembrado de imóvel > 4 MF (origem {car} ha = {mf} MF; art. 12 §1º): RL própria de 20% = {g2rl} ha; com terra limpa, {g2rl} ha a recompor, regenerar ou compensar (art. 66).',
                       '(C) EXCEÇÃO art. 67 — só se o imóvel de origem tinha até 4 MF em 22/07/2008 (provar com a matrícula de origem): RL = vegetação de 2008; 0 ha se era terra limpa (MapBiomas 2008: {v08} ha só na ponta norte).',
                       'Ortofoto: a Gleba 2 é solo/cultivo em {solo} ha; a vegetação ({veg} ha) está toda na ponta norte, {sem} ha dos quais fora do voo (classes v3). APP: {m} m do Arroio 1, {app} ha vegetados; se a ponta não for da gleba, APP e vegetação = 0.'],
                'es': ['(A) INMUEBLE ÚNICO — principal (IN MMA 2/2014 art. 32): sin cuenta propia. Los 6 alqueires suman {g2rl} ha a la RL del inmueble ({g1rl} -> {rl} ha), localizable en cualquier gleba (art. 14), y aportan 0 ha de vegetación. Déficit del inmueble (v4): {d} ha (conserv. {dc}).',
                       '(B) INMUEBLE SEPARADO, desmembrado de inmueble > 4 MF (origen {car} ha = {mf} MF; art. 12 §1º): RL propia del 20% = {g2rl} ha; con tierra limpia, {g2rl} ha a recomponer, regenerar o compensar (art. 66).',
                       '(C) EXCEPCIÓN art. 67 — solo si el inmueble de origen tenía hasta 4 MF el 22/07/2008 (probar con la matrícula de origen): RL = vegetación de 2008; 0 ha si era tierra limpia (MapBiomas 2008: {v08} ha solo en la punta norte).',
                       'Ortofoto: la Gleba 2 es suelo/cultivo en {solo} ha; la vegetación ({veg} ha) está toda en la punta norte, {sem} ha de ellas fuera del vuelo (clases v3). APP: {m} m del Arroyo 1, {app} ha vegetados; si la punta no fuera de la gleba, APP y vegetación = 0.']},
    'g1': {'pt': 'Gleba 1 – {ha} ha', 'es': 'Gleba 1 – {ha} ha'},
    'g2': {'pt': 'Gleba 2 – {ha} ha ({alq} alq.)', 'es': 'Gleba 2 – {ha} ha ({alq} alq.)'},
    # X08
    'x08_t': {'pt': 'X08 · Detalhes a 5 cm', 'es': 'X08 · Detalles a 5 cm'},
    'x08_s': {'pt': 'Represa · açude e nascente · cauce · corredor do Arroio 2 · ortofoto 22/05/2026 (GSD 5 cm) e CHM 0,25 m', 'es': 'Represa · embalse y naciente · cauce · corredor del Arroyo 2 · ortofoto 22/05/2026 (GSD 5 cm) y CHM 0,25 m'},
    'p_a': {'pt': '(a) Represa do Ribeirão do Salto: espelho {a} ha (22/05/2026) vs FBDS 2013 {f} ha vs CAR {c} ha; vaso indicador {v} ha. Dique: FBDS 9 m a oeste, CAR 8 m a leste. Sem DSM: cota do espelho não medida.',
            'es': '(a) Represa del Ribeirão do Salto: espejo {a} ha (22/05/2026) vs FBDS 2013 {f} ha vs CAR {c} ha; vaso indicador {v} ha. Dique: FBDS 9 m al oeste, CAR 8 m al este. Sin DSM: cota del espejo no medida.'},
    'p_b': {'pt': '(b) Cabeceira do Arroio 2: 2º reservatório {a} ha (CAR {c} ha; existe) e nascente FBDS 306158 a {d} m, na borda da várzea; olho d\'água exato a levantar com GNSS. dem_1 = mesma cabeceira.',
            'es': '(b) Cabecera del Arroyo 2: 2º reservorio {a} ha (CAR {c} ha; existe) y naciente FBDS 306158 a {d} m, en el borde de la várzea; ojo de agua exacto a levantar con GNSS. dem_1 = misma cabecera.'},
    'p_c': {'pt': '(c) Único claro com água no eixo dos três arroios: vertedouro/saída da represa (Arroio 3), poça ARTIFICIAL a jusante do dique — espelho {e} m, calha por vegetação {c} m. NÃO é a calha natural: sob dossel o cauce é invisível a 5 cm.',
            'es': '(c) Único claro con agua en el eje de los tres arroyos: vertedero/salida de la represa (Arroyo 3), poza ARTIFICIAL aguas abajo del dique — espejo {e} m, cauce por vegetación {c} m. NO es el cauce natural: bajo dosel el cauce es invisible a 5 cm.'},
    'p_d': {'pt': '(d) Corredor do Arroio 2 no CHM híbrido 0,25 m: talvegue DTM (laranja) a {m} m (mediana) do eixo FBDS (azul); seções de 60 m sem solo (0 de 56) — a borda da calha não é medível; CHM ~0 sob dossel fechado.',
            'es': '(d) Corredor del Arroyo 2 en el CHM híbrido 0,25 m: talweg DTM (naranja) a {m} m (mediana) del eje FBDS (azul); secciones de 60 m sin suelo (0 de 56) — el borde del cauce no es medible; CHM ~0 bajo dosel cerrado.'},
    'chm_lbl': {'pt': 'CHM (m)', 'es': 'CHM (m)'},
    # X09
    'x09_t': {'pt': 'X09 · Sentinel-2 10 m (v3) vs ortofoto 0,5 m (v4)', 'es': 'X09 · Sentinel-2 10 m (v3) vs ortofoto 0,5 m (v4)'},
    'x09_s': {'pt': 'Mesma extensão (fragmento 13, nascente, açude, Arroio 2) · vegetação nativa por método · antes/depois', 'es': 'Misma extensión (fragmento 13, naciente, embalse, Arroyo 2) · vegetación nativa por método · antes/después'},
    'x09_a': {'pt': 'S2C 29/08/2026 · RF 10 m (v3)', 'es': 'S2C 29/08/2026 · RF 10 m (v3)'},
    'x09_b': {'pt': 'Ortofoto 22/05/2026 · classes 0,5 m (v4)', 'es': 'Ortofoto 22/05/2026 · clases 0,5 m (v4)'},
    'tab_x09': {'pt': ['Item (ha)', 'v3 S2 10 m', 'v4 ortofoto', 'Delta'], 'es': ['Ítem (ha)', 'v3 S2 10 m', 'v4 ortofoto', 'Delta']},
    'x09_nota': {'pt': 'Alinhamento ortofoto–S2 <= 3 m. A ortofoto separa pasto de arbustiva, mede a água do dia e descarta a silvicultura do RF S2; não muda a APP exigível (mesmo eixo FBDS) nem substitui o campo para o estágio sucessional.',
                 'es': 'Alineación ortofoto–S2 <= 3 m. La ortofoto separa pastura de arbustiva, mide el agua del día y descarta la silvicultura del RF S2; no cambia la APP exigible (mismo eje FBDS) ni sustituye al campo para el estadio sucesional.'},
    'ad_items': {'pt': {'APP exigivel imovel (ha)': 'APP exigível (imóvel)', 'APP G1 com vegetacao nativa (ha)': 'APP G1 com vegetação', 'APP G1 agua (ha)': 'APP G1 água', 'APP G1 a recompor (ha)': 'APP G1 a recompor',
                        'APP G1 a recompor cenario PRA-PR 20 m (ha)': 'A recompor PRA-PR 20 m', 'Vegetacao nativa computavel RL (ha)': 'Vegetação computável (RL)', 'Deficit RL imovel unico (ha)': 'Déficit de RL',
                        'Vegetacao computavel conservadora sem frag. 13 (ha)': 'Computável conservadora', 'Deficit RL conservador (ha)': 'Déficit conservador', 'Represa: espelho (ha)': 'Represa: espelho',
                        'Represa >= 1 ha': 'Represa >= 1 ha', '2o reservatorio cabeceira Arroio 2 (ha)': '2º reservatório (cabeceira)'},
                 'es': {'APP exigivel imovel (ha)': 'APP exigible (inmueble)', 'APP G1 com vegetacao nativa (ha)': 'APP G1 con vegetación', 'APP G1 agua (ha)': 'APP G1 agua', 'APP G1 a recompor (ha)': 'APP G1 a recomponer',
                        'APP G1 a recompor cenario PRA-PR 20 m (ha)': 'A recomponer PRA-PR 20 m', 'Vegetacao nativa computavel RL (ha)': 'Vegetación computable (RL)', 'Deficit RL imovel unico (ha)': 'Déficit de RL',
                        'Vegetacao computavel conservadora sem frag. 13 (ha)': 'Computable conservadora', 'Deficit RL conservador (ha)': 'Déficit conservador', 'Represa: espelho (ha)': 'Represa: espejo',
                        'Represa >= 1 ha': 'Represa >= 1 ha', '2o reservatorio cabeceira Arroio 2 (ha)': '2º reservorio (cabecera)'}},
    'ad_txt': {'pt': {'INDETERMINADO': 'INDETERMINADO', 'SIM (22-mai-2026)': 'SIM (22/05/2026)'}, 'es': {'INDETERMINADO': 'INDETERMINADO', 'SIM (22-mai-2026)': 'SÍ (22/05/2026)'}},
}


def t(k):
    return X[k][LANG]


# ------------------------------------------------------------------ dados ----
class DadosV4(DadosV3):
    def __init__(self):
        super().__init__()
        self.v4 = leer_json(os.path.join(ORTO, 'resultados_v4.json'))
        self.cauce = leer_json(os.path.join(CAUCE, 'cauce_resumo.json'))
        O = lambda n: gpd.read_file(os.path.join(ORTO, n + '.geojson'))
        self.app4 = O('app_v4')
        self.veg4 = O('vegetacao_nativa_ortofoto')
        self.car4 = O('mapa_uso_car_v4')
        self.rl4 = O('rl_vegetacao_computavel_v4')
        self.agua4 = O('agua_ortofoto_2026-05-22')
        self.eixo = O('eixo_dtm_arroios')
        self.sec = O('secoes_transversais')
        self.nasc4 = O('nascentes_ortofoto')
        self.cob = O('cobertura_vuelo')
        self.med = gpd.read_file(os.path.join(CAUCE, 'cauce_medicoes.geojson'))
        # geometrias de DESENHO (nao produzem cifra)
        fb = self.app4[self.app4.variante == 'fbds']; pr = self.app4[self.app4.variante == 'pra']; fr = self.app4[self.app4.variante == 'fbds_reservatorio']
        self.app4_fbds = unary_union(list(fb.geometry)); self.app4_pra = unary_union(list(pr.geometry))
        self.app4_res = unary_union(list(fr.geometry)).difference(self.app4_fbds)
        self.represa = self.agua4[self.agua4.corpo == 'represa_principal'].geometry.iloc[0]
        self.vaso = self.agua4[self.agua4.corpo == 'represa_vaso_indicador'].geometry.iloc[0]
        self.acude = self.agua4[self.agua4.corpo == 'reservatorio_cabeceira_arroio2'].geometry.iloc[0]
        self.lagoas = self.agua4[self.agua4.tipo == 'candidato']
        self.sem_orto = unary_union(list(self.cob[self.cob.capa == 'imovel_sem_ortofoto'].geometry))
        self.dtm_cob = unary_union(list(self.cob[self.cob.capa == 'dtm_dsm'].geometry))
        self.orto_cob = unary_union(list(self.cob[self.cob.capa == 'ortofoto'].geometry))


# ------------------------------------------------------------ fundo orto -----
def fondo_orto(M, d, ruta=None, gain=1.0):
    """Ortofoto RGBA mascarada ao perimetro; alpha=0 dentro do imovel (faixa sem voo) -> S2 RGB reamostrado; fora = cinza."""
    ruta = ruta or os.path.join(ORTO, 'ortofoto_rgba_0_50m.tif')
    x0, y0, x1, y1 = M.extent
    with rasterio.open(ruta) as ds:
        bx0, by0, bx1, by1 = max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top)
        win = from_bounds(bx0, by0, bx1, by1, ds.transform)
        img = ds.read(window=win)
        tr = ds.window_transform(win)
    h, w = img.shape[1], img.shape[2]
    ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
    rgb = np.clip(np.moveaxis(img[:3], 0, -1).astype(np.float32) / 255.0 * gain, 0, 1)
    alpha = img[3] > 0
    with rasterio.open(R['rgb']) as ds:
        w2 = from_bounds(tr.c, tr.f + h * tr.e, tr.c + w * tr.a, tr.f, ds.transform)
        s2 = ds.read(window=w2, out_shape=(3, h, w), resampling=Resampling.bilinear, boundless=True, fill_value=0).astype(np.float32) / 255.0
    s2 = np.clip(np.moveaxis(s2, 0, -1) * 1.15, 0, 1)
    rgb = np.where(alpha[..., None], rgb, s2)
    mask = features.rasterize([(d.prop_u, 1)], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8, all_touched=True)
    fora = np.array(matplotlib.colors.to_rgb(FORA), dtype=np.float32)
    rgb = np.where(mask[..., None] == 1, rgb, fora)
    M.ax.imshow(rgb, extent=ex, interpolation='nearest', zorder=1)
    M.ax.set_facecolor(FORA)
    ext_poly = box(x0 - 50, y0 - 50, x1 + 50, y1 + 50).difference(d.prop_u)
    patch_agujeros(M.ax, ext_poly, fc=FORA, ec='none', lw=0, zorder=25)


def novo4(d, titulo, sub, leg_min_cm=6.3, extent=None):
    m4.LANG = LANG; m8.LANG = LANG
    m4.T['notas'] = X['notas']; m4.T['fonte_s2'] = X['fonte']
    m8.TV['notas'] = X['notas']; m8.TV['arr_lbl'] = X['arr_lbl']
    M = Mapa('V', titulo, sub, extent or extent_interior(d), leg_min_cm=leg_min_cm)
    fondo_orto(M, d)
    return M


def cobertura(M, d, legenda=True):
    """Faixa sem ortofoto (hachura) e limite sul do DSM/DTM (linha pontilhada) — so desenho."""
    ax = M.ax
    poly_patches(ax, [d.sem_orto], fc='none', ec=COL['cobert'], hatch='////', lw=0.6, zorder=9)
    lim = d.dtm_cob.boundary.intersection(d.prop_u.buffer(-2))
    plot_lines(ax, [lim], color=COL['cobert'], lw=1.0, ls=(0, (1, 1.5)), zorder=13)
    cv = d.v4['cobertura_voo']
    return ([Patch(fc='none', ec=COL['cobert'], hatch='////', lw=0.6), Line2D([], [], color=COL['cobert'], lw=1.0, ls=(0, (1, 1.5)))],
            [t('sem_orto').format(a=fmt(cv['G1']['sem_ortofoto_ha'] + cv['G2']['sem_ortofoto_ha'])), t('lim_dtm').format(a=fmt(cv['G1']['sem_dtm_ha']))])


def agua_layers(M, d, lagoas=True):
    ax = M.ax
    poly_patches(ax, [d.vaso], fc=COL['vaso'] + '66', ec=COL['vaso'], lw=0.5, zorder=7)
    poly_patches(ax, [d.represa], fc=COL['agua_o'], ec='white', lw=0.5, zorder=8)
    poly_patches(ax, [d.acude], fc=COL['acude'], ec='white', lw=0.6, zorder=8)
    if lagoas:
        poly_patches(ax, list(d.lagoas.geometry), fc=COL['lagoa'], ec='white', lw=0.3, zorder=8)


def nascentes4(M, d, rotular=True):
    ax = M.ax
    for _, r in d.nasc4.iterrows():
        if r.id == '306158':
            ax.scatter([r.geometry.x], [r.geometry.y], s=46, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=0.9, zorder=16)
        elif r.id == 'dem_2':
            ax.scatter([r.geometry.x], [r.geometry.y], s=40, marker='x', c=COL['nasc_pp'], linewidths=1.2, zorder=16)
            if rotular:
                ax.text(r.geometry.x + 30, r.geometry.y, 'dem_2', fontsize=5.0, va='center', zorder=17, bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.8))


# ---------------------------------------------------------------- X01 --------
def X01(d):
    k = d.v4['kpi']; rp = d.v4['represa']; cu = d.v4['cursos']
    M = novo4(d, t('x01_t'), t('x01_s').format(ha=fmt(k['area_imovel_ha'])), leg_min_cm=6.3)
    ax = M.ax
    agua_layers(M, d)
    plot_lines(ax, list(d.eixo.geometry), color=COL['talweg'], lw=1.1, ls=(0, (3, 1.5)), zorder=12)
    arroios(M, d)
    nascentes4(M, d)
    hc, lc = cobertura(M, d)
    c = d.represa.centroid
    ax.annotate('%s ha' % fmt(rp['espelho_22_mai_2026_ha'], 3), xy=(c.x, c.y), xytext=(c.x - 40, c.y - 190), fontsize=5.4, ha='center', zorder=40,
                arrowprops=dict(arrowstyle='-', lw=0.5, color='black'), bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=COL['agua_o'], lw=0.8, alpha=0.92))
    c = d.acude.centroid
    ax.annotate('%s ha' % fmt(rp['reservatorio_cabeceira_arroio2']['area_agua_ha'], 3), xy=(c.x, c.y), xytext=(c.x - 150, c.y + 110), fontsize=5.2, ha='center', zorder=40,
                arrowprops=dict(arrowstyle='-', lw=0.5, color='black'), bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=COL['acude'], lw=0.8, alpha=0.92))
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    n = d.v4['nascentes']['pontos'][0]
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Line2D([], [], color=COL['fbds'], lw=1.6), Line2D([], [], color=COL['talweg'], lw=1.1, ls=(0, (3, 1.5))),
                     Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=6.5),
                     Line2D([], [], marker='x', color='none', markeredgecolor=COL['nasc_pp'], markeredgewidth=1.2, ms=6),
                     Patch(fc=COL['agua_o'], ec='white'), Patch(fc=COL['vaso'] + '66', ec=COL['vaso']), Patch(fc=COL['acude'], ec='white'), Patch(fc=COL['lagoa'], ec='white')] + hc,
                l + [t('curso'), t('talweg'), t('nasc_prov').format(d=fmt(n['dist_agua_aberta_m'], 0)), t('nasc_nao'),
                     t('represa').format(a=fmt(rp['espelho_22_mai_2026_ha'], 3)), t('vaso').format(a=fmt(rp['vaso_indicador_ha'], 3)),
                     t('acude').format(a=fmt(rp['reservatorio_cabeceira_arroio2']['area_agua_ha'], 3), b=fmt(rp['reservatorio_cabeceira_arroio2']['area_car_declarada_ha'], 3)),
                     t('lagoas').format(a=fmt(float(d.lagoas.area_ha.sum())))] + lc)
    rows = [t('tab_x01')]
    for key, n_ in [('G1 Arroio 1 (norte)', 1), ('G1 Arroio 2 (central)', 2), ('G1 Arroio 3 (sul)', 3)]:
        c_ = cu[key]; m3 = d.cauce['consolidado'][key.replace('G1 ', '')]['M3']
        rows.append(['%s %d' % (t('arroio'), n_), fmt(c_['fbds_m'], 0), fmt(c_['cobertura_ortofoto_pct'], 0), fmt(c_['cobertura_dtm_pct'], 0),
                     '%s [%s–%s]' % (fmt(m3['W_m'], 1), fmt(m3['intervalo_m'][0], 1), fmt(m3['intervalo_m'][1], 1))])
    M.leg_espacio(0.12); M.leg_tabla(rows, col_w=[0.24, 0.16, 0.14, 0.14, 0.32])
    M.leg_texto(t('x01_nota')); M.notas()
    return M


# ---------------------------------------------------------------- X02 --------
def X02(d):
    V = d.v4['vegetacao']; g1 = V['por_gleba']['G1']; g2 = V['por_gleba']['G2']; im = V['por_gleba']['IMOVEL']
    M = novo4(d, t('x02_t'), t('x02_s'), leg_min_cm=6.3)
    ax = M.ax
    cm = {v: COL[c] + ('88' if c in ('solo',) else 'CC' if c == 'pasto' else 'EE') for v, c in VEG_CLASSES.items()}
    raster_clases(ax, os.path.join(ORTO, 'vegetacao_ortofoto_0_50m.tif'), M.extent, cm, zorder=5, clip=d.prop_u)
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {1: COL['arb'] + 'AA'}, zorder=4, clip=d.sem_orto)
    for u in ('G1', 'G2'):
        fl = d.frag[d.frag.gleba == u]
        fl.boundary.plot(ax=ax, color='white', lw=1.3, zorder=12); fl.boundary.plot(ax=ax, color=LIMA, lw=0.6, zorder=13)
    fr = {f['frag_id']: f for f in V['fragmentos']}
    off = {('G1', 2): (250, -110), ('G1', 13): (190, 60), ('G1', 30): (-20, -200), ('G2', 2): (-270, -40)}
    for _, r in d.frag.iterrows():
        c = r.geometry.representative_point(); dx_, dy_ = off.get((r.gleba, int(r.frag_id)), (0, 0)); f = fr.get(int(r.frag_id))
        if r.gleba == 'G2' or f is None or f['altura_media_m'] is None:
            lab = t('frag_lbl_sem').format(id=r.frag_id, ha=fmt(r.area_dentro_ha)) if (f is None or f['altura_media_m'] is None) else ('Frag. %s · %s ha' % (r.frag_id, fmt(r.area_dentro_ha)))
        else:
            lab = t('frag_lbl').format(id=r.frag_id, ha=fmt(r.area_dentro_ha), p=fmt(f['cobertura_arborea_pct'], 0), h=fmt(f['altura_media_m'], 1), p90=fmt(f['altura_p90_m'], 1))
        ax.annotate(lab, xy=(c.x, c.y), xytext=(c.x + dx_, c.y + dy_), fontsize=5.0, ha='center', va='center', zorder=41, fontweight='bold',
                    arrowprops=dict(arrowstyle='-', lw=0.6, color='black'), bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['arb'], lw=0.7, alpha=0.93))
    hc, lc = cobertura(M, d)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['arb']), Patch(fc=COL['arb_sem']), Patch(fc=COL['arbu']), Patch(fc=COL['pasto'], ec='#BBBBBB'), Patch(fc=COL['solo'], ec='#BBBBBB'), Patch(fc=COL['agua_o']), Patch(fc=COL['constr']),
                     Patch(fc='none', ec=LIMA, lw=1.5)] + hc,
                l + [t('cl_arb').format(a=fmt(g1['arborea_altura_medida'] + g1['arborea_dosel_fechado']), b=fmt(g2['arborea_altura_medida'] + g2['arborea_dosel_fechado'])),
                     t('cl_arb_sem').format(a=fmt(im['arborea_arbustiva_sem_chm'])), t('cl_arbu').format(a=fmt(g1['arbustiva_regeneracao']), b=fmt(g2['arbustiva_regeneracao'])),
                     t('cl_pasto').format(a=fmt(g1['herbacea_pasto']), b=fmt(g2['herbacea_pasto'])), t('cl_solo').format(a=fmt(g1['solo_cultivo']), b=fmt(g2['solo_cultivo'])),
                     t('cl_agua_o').format(a=fmt(im['agua'])), t('cl_constr').format(a=fmt(im['construcoes'])), t('frag')] + lc)
    rows = [t('tab_veg')]
    keys = [('arborea_ha',), ('arbustiva_ha',), ('herbacea_pasto',), ('solo_cultivo',), ('agua',), ('construcoes',), ('sem_dado',), ('vegetacao_nativa_arborea_arbustiva_ha',)]
    for lab, (kk,) in zip(t('tab_veg_rows'), keys):
        rows.append([lab, fmt(g1[kk]), fmt(g2[kk]), fmt(im[kk])])
    M.leg_espacio(0.12); M.leg_tabla(rows, col_w=[0.49, 0.17, 0.17, 0.17], bold_last=True)
    M.leg_texto(t('x02_nota')); M.notas()
    return M


# ---------------------------------------------------------------- X03 --------
def X03(d):
    A = d.v4['app']; F = A['fbds']; g1 = F['G1']; g2 = F['G2']; im = F['IMOVEL']; P = A['pra']; Rz = A['fbds_reservatorio']
    M = novo4(d, t('x03_t'), t('x03_s'), leg_min_cm=6.3)
    ax = M.ax
    c4 = d.car4[d.car4.classe_car.str.startswith('APP')]
    c4[c4.subclasse == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='none', alpha=0.9, zorder=6)
    c4[c4.subclasse == 'agua'].plot(ax=ax, fc=COL['app_agua'], ec='none', alpha=0.9, zorder=6)
    rec = c4[c4.subclasse == 'a recompor']
    rec[rec.situacao == 'pasto/herbacea'].plot(ax=ax, fc=COL['rec_pasto'], ec='none', alpha=0.92, zorder=6)
    rec[rec.situacao != 'pasto/herbacea'].plot(ax=ax, fc=COL['rec_cult'], ec='none', alpha=0.92, zorder=6)
    poly_patches(ax, [d.app4_res], fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8, zorder=8)
    poly_patches(ax, [d.app4_fbds], fc='none', ec=COL['app_lim'], lw=0.8, ls='--', zorder=12)
    poly_patches(ax, [d.app4_pra], fc='none', ec=COL['faixa20'], lw=0.9, ls=(0, (3, 1.5)), zorder=13)
    arroios(M, d, rotular=False, lw=1.0)
    nascentes4(M, d, rotular=False)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    sub = g1['a_recompor_por_subclasse_ha']
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['app_conf']), Patch(fc=COL['app_agua']), Patch(fc=COL['rec_pasto']), Patch(fc=COL['rec_cult']), Line2D([], [], color=COL['app_lim'], lw=0.9, ls='--'),
                     Line2D([], [], color=COL['faixa20'], lw=1.1, ls=(0, (3, 1.5))), Patch(fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8), Line2D([], [], color=COL['fbds'], lw=1.0),
                     Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=6)],
                l + [t('app_conf').format(a=fmt(im['com_vegetacao_nativa_ha'])), t('app_agua').format(a=fmt(im['agua_ha'])), t('app_rec_p').format(a=fmt(sub['pasto_herbacea'])),
                     t('app_rec_c').format(a=fmt(sub['cultivo_solo'])) + ' · ' + t('app_rec_a').format(a=fmt(sub['arvores_isoladas_lt_0_05ha'])).replace('A recompor: ', '').replace('A recomponer: ', ''),
                     t('app_lim').format(a=fmt(im['exigida_ha']), mn=fmt(im['envolvente_borda_0_5m_ha'][0]), mx=fmt(im['envolvente_borda_0_5m_ha'][1])),
                     t('faixa20').format(a=fmt(P['G1']['a_recompor_ha'])), t('reserv_faixa').format(a=fmt(Rz['G1']['exigida_ha']), b=fmt(Rz['G1']['a_recompor_ha'])), t('curso'),
                     t('nasc_prov').format(d=fmt(d.v4['nascentes']['pontos'][0]['dist_agua_aberta_m'], 0))])
    rows = [t('tab_app')]
    s1 = g1['a_recompor_por_subclasse_ha']; z = fmt(0.0)
    e0 = lambda g: fmt(g['envolvente_borda_0_5m_ha'][0]); e1 = lambda g: fmt(g['envolvente_borda_0_5m_ha'][1])
    vals = [(fmt(g1['exigida_ha']), fmt(g2['exigida_ha']), fmt(im['exigida_ha'])), (e0(g1), e0(g2), e0(im)), (e1(g1), e1(g2), e1(im)),
            (fmt(g1['com_vegetacao_nativa_ha']), fmt(g2['com_vegetacao_nativa_ha']), fmt(im['com_vegetacao_nativa_ha'])), (fmt(g1['agua_ha']), fmt(g2['agua_ha']), fmt(im['agua_ha'])),
            (fmt(g1['a_recompor_ha']), fmt(g2['a_recompor_ha']), fmt(im['a_recompor_ha'])),
            (fmt(s1['pasto_herbacea']), z, fmt(s1['pasto_herbacea'])), (fmt(s1['cultivo_solo']), z, fmt(s1['cultivo_solo'])), (fmt(s1['arvores_isoladas_lt_0_05ha']), z, fmt(s1['arvores_isoladas_lt_0_05ha'])),
            (fmt(P['G1']['a_recompor_ha']), fmt(P['G2']['a_recompor_ha']), fmt(P['IMOVEL']['a_recompor_ha'])),
            (fmt(Rz['G1']['exigida_ha']), fmt(Rz['G2']['exigida_ha']), fmt(Rz['IMOVEL']['exigida_ha'])), (fmt(Rz['G1']['a_recompor_ha']), fmt(Rz['G2']['a_recompor_ha']), fmt(Rz['IMOVEL']['a_recompor_ha']))]
    for lab, v in zip(t('tab_app_rows'), vals):
        rows.append([lab] + list(v))
    M.leg_espacio(0.12); M.leg_tabla(rows, col_w=[0.49, 0.17, 0.17, 0.17])
    M.leg_texto(t('x03_ver').format(a=fmt(g1['a_recompor_ha']), b=fmt(P['G1']['a_recompor_ha'])), bold=True, color=AZUL)
    M.notas()
    return M


# ---------------------------------------------------------------- X04 --------
def X04(d):
    RL = d.v4['reserva_legal']; k = d.v4['kpi']; pr = RL['principal_mmu_0_05ha_g2_terra_limpa']; co = RL['conservador_sem_fragmento_13']; pn = RL['se_ponta_norte_da_g2_for_do_imovel']
    v3RL = d.v3['reserva_legal']; loc = v3RL['localizacao_proposta']; f_iat = next(f for f in loc['fragmento_iat_prioridade_A'] if f['fragmento'] == '163756')
    M = novo4(d, t('x04_t'), t('x04_s').format(ha=fmt(k['area_imovel_ha']), rl=fmt(RL['exigida_ha'])), leg_min_cm=6.3)
    ax = M.ax
    d.rl4[d.rl4.parte.str.startswith('remanescente')].plot(ax=ax, fc=COL['rl_rem'], ec='none', alpha=0.92, zorder=6)
    d.rl4[d.rl4.parte.str.startswith('APP')].plot(ax=ax, fc=COL['rl_app'], ec='none', alpha=0.92, zorder=6)
    poly_patches(ax, [d.f13], fc='none', ec='white', hatch='///', lw=0.0, zorder=8)
    poly_patches(ax, [d.corr_g1], fc=COL['rl_corr'] + 'AA', ec='#92400E', hatch='\\\\', lw=0.4, zorder=7)
    iat = unary_union(list(d.iat[d.iat.fragmento == '163756'].geometry))
    poly_patches(ax, [iat], fc='none', ec=COL['iat'], lw=1.3, ls=(0, (1, 1.2)), zorder=11)
    poly_patches(ax, list(d.ponta.geometry), fc='none', ec=COL['ponta'], hatch='xx', lw=0.9, zorder=9)
    rlg = unary_union(list(d.rlp.geometry))
    gpd.GeoSeries([rlg], crs=CRS_METRICO).boundary.plot(ax=ax, color='white', lw=2.0, zorder=12)
    gpd.GeoSeries([rlg], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['rl_lim'], lw=1.2, zorder=13)
    arroios(M, d, rotular=False, lw=0.8)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['rl_rem']), Patch(fc=COL['rl_app']), Patch(fc=COL['rl_rem'], hatch='///', ec='white'), Patch(fc=COL['rl_corr'], hatch='\\\\', ec='#92400E'),
                     Line2D([], [], color=COL['rl_lim'], lw=1.6), Line2D([], [], color=COL['iat'], lw=1.3, ls=(0, (1, 1.2))), Patch(fc='none', hatch='xx', ec=COL['ponta']), Line2D([], [], color=COL['fbds'], lw=0.8)],
                l + [t('rl_rem').format(a=fmt(pr['remanescente_fora_app_ha'])), t('rl_app').format(a=fmt(pr['app_vegetada_art15_ha'])), t('rl_f13'),
                     t('rl_corr').format(a=fmt(loc['corredor_g1_ha'])), t('rl_lim').format(a=fmt(loc['rl_proposta_recortada_g1_ha'])), t('rl_iat').format(a=fmt(f_iat['dentro_ha'])),
                     t('rl_g2').format(a=fmt(pn['vegetacao_g2_ha'])), t('curso')])
    rows = [t('tab_rl')]
    vals = [(fmt(RL['exigida_ha']), fmt(RL['exigida_ha']), fmt(RL['exigida_ha'])),
            (fmt(pr['vegetacao_computavel_ha']), fmt(co['vegetacao_computavel_ha']), fmt(pn['vegetacao_computavel_ha'])),
            ('%s–%s' % (fmt(pr['envolvente_0_5m_ha'][0]), fmt(pr['envolvente_0_5m_ha'][1])), '%s–%s' % (fmt(co['envolvente_0_5m_ha'][0]), fmt(co['envolvente_0_5m_ha'][1])), '—'),
            (fmt(pr['deficit_ha']), fmt(co['deficit_ha']), fmt(pn['deficit_ha'])), (fmt(pr['pct_atendido'], 1), fmt(co['pct_atendido'], 1), '—'),
            (fmt(d.v3['kpi']['car_rl_averbada_ha']), fmt(d.v3['kpi']['car_rl_averbada_ha']), fmt(d.v3['kpi']['car_rl_averbada_ha']))]
    for lab, v in zip(t('tab_rl_rows'), vals):
        rows.append([lab.format(ha=fmt(k['area_imovel_ha']))] + list(v))
    M.leg_espacio(0.12); M.leg_tabla(rows, col_w=[0.37, 0.23, 0.22, 0.18])
    ad = {a['item']: a for a in d.v4['antes_depois']}
    M.leg_texto(t('x04_nota').format(d=fmt(pr['deficit_ha']), mn=fmt(RL['exigida_ha'] - pr['envolvente_0_5m_ha'][1]), mx=fmt(RL['exigida_ha'] - pr['envolvente_0_5m_ha'][0]), dc=fmt(co['deficit_ha']), dp=fmt(pn['deficit_ha']),
                                     dv=fmt(ad['Vegetacao nativa computavel RL (ha)']['delta']))); M.notas()
    return M


# ---------------------------------------------------------------- X05 --------
def X05(d):
    k = d.v4['kpi']; F = d.v4['mapa_car_v4']['fecha']
    M = novo4(d, t('x05_t'), t('x05_s').format(a=fmt(k['area_imovel_ha']), b=fmt(F['G1']['soma_ha']), c=fmt(F['G2']['soma_ha'])), leg_min_cm=6.3)
    ax = M.ax
    estilo = {
        ("APP - Nascente ou olho d'agua perene", 'conforme'): dict(fc=COL['car_app_conf'], hatch='..', ec='#1B5E20'),
        ("APP - Nascente ou olho d'agua perene", 'a recompor'): dict(fc=COL['car_app_rec'], hatch='..', ec='#7F0000'),
        ("APP - Curso d'agua natural de ate 10 metros", 'conforme'): dict(fc=COL['car_app_conf']),
        ("APP - Curso d'agua natural de ate 10 metros", 'agua'): dict(fc=COL['app_agua']),
        ("APP - Curso d'agua natural de ate 10 metros", 'a recompor'): dict(fc=COL['car_app_rec']),
        ('Reservatorio artificial decorrente de barramento ou represamento de cursos d agua naturais', 'espelho d agua'): dict(fc=COL['car_reserv']),
        ('Reservatorio artificial / lagoa', 'espelho d agua'): dict(fc=COL['lagoa']),
        ('Remanescente de Vegetacao Nativa', 'vegetacao nativa fora da APP'): dict(fc=COL['car_rem']),
        ('Area Consolidada', 'construcoes'): dict(fc=COL['constr']),
        ('Area Consolidada', 'pasto/herbacea'): dict(fc=COL['pasto'] + 'CC', ec='#BBBBBB'),
        ('Area Consolidada', 'arvores isoladas (< 0,05 ha)'): dict(fc=COL['arbu'] + 'CC'),
        ('Area Consolidada', 'uso agricola'): dict(fc=COL['car_cons'] + '99'),
    }
    handles, labels = leg_glebas(d)
    rows = [t('tab_car')]
    for (cl, sc), st in estilo.items():
        tot = {}
        for u in ('G1', 'G2'):
            sub = d.car4[(d.car4.gleba == u) & (d.car4.classe_car == cl) & (d.car4.subclasse == sc)]
            tot[u] = float(sub.area_ha.sum()) if len(sub) else 0.0
            if len(sub):
                poly_patches(ax, sub.geometry, ec=st.get('ec', 'none'), fc=st['fc'], hatch=st.get('hatch'), lw=0.3, alpha=0.9, zorder=6)
        if tot['G1'] + tot['G2'] <= 0:
            continue
        handles.append(Patch(fc=st['fc'], hatch=st.get('hatch'), ec=st.get('ec', '#999999'), lw=0.4))
        labels.append(t('car_names')[(cl, sc)])
        rows.append([t('car_short')[(cl, sc)], fmt(tot['G1']), fmt(tot['G2']) if tot['G2'] > 0 else '—'])
    glebas(M, d); M.grilla(); M.norte_escala()
    M.leg_titulo(t('legenda')); M.leg_items(handles, labels)
    rows.append([t('soma'), fmt(F['G1']['soma_ha']), fmt(F['G2']['soma_ha'])])
    M.leg_espacio(0.12); M.leg_tabla(rows, col_w=[0.62, 0.19, 0.19], bold_last=True)
    M.leg_texto(t('x05_nota')); M.notas()
    return M


# ---------------------------------------------------------------- X06 --------
def X06(d):
    C = d.v3['car_existente']; k = d.v4['kpi']; RL = d.v4['reserva_legal']; rp = d.v4['represa']
    M = novo4(d, t('x06_t'), t('x06_s').format(a=fmt(C['area_declarada_ha']), c=C['condicao'].replace('analise', 'análise')), leg_min_cm=6.3)
    ax = M.ax
    raster_clases(ax, os.path.join(ORTO, 'vegetacao_ortofoto_0_50m.tif'), M.extent, {1: COL['arb'] + 'BB', 2: COL['arb'] + 'BB', 9: COL['arb'] + 'BB', 3: COL['arbu'] + 'BB', 6: COL['agua_o'] + 'BB'}, zorder=5, clip=d.prop_u)
    own = d.carx[d.carx.relacao == 'propio_G1']; org = d.carx[d.carx.relacao == 'cubre_G2']
    veg = own[own.cod_tema == 'VEGETACAO_NATIVA']; rl = own[own.cod_tema == 'ARL_AVERBADA']; app = own[own.cod_tema == 'APP_TOTAL']
    res = own[own.cod_tema == 'RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO']
    clip = lambda g: unary_union(list(g.geometry)).intersection(d.prop_u)
    poly_patches(ax, [clip(veg)], fc=COL['car_veg'] + '55', ec=COL['car_veg'], lw=1.0, zorder=8)
    poly_patches(ax, [clip(rl)], fc='none', ec=COL['car_rl'], hatch='///', lw=1.4, zorder=10)
    poly_patches(ax, [clip(app)], fc='none', ec=COL['car_app'], lw=1.1, ls='--', zorder=9)
    poly_patches(ax, [clip(res)], fc='none', ec=COL['car_res'], lw=1.3, zorder=11)
    poly_patches(ax, [d.represa, d.acude], fc='none', ec='white', lw=0.9, zorder=12)
    rl2 = org[org.cod_tema == 'ARL_PROPOSTA']
    if len(rl2):
        poly_patches(ax, [clip(rl2).intersection(d.G2)], fc='none', ec=COL['iat'], hatch='\\\\', lw=1.0, zorder=10)
    arroios(M, d, rotular=False, lw=0.7)
    glebas(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    tb = {r['tema']: r for r in C['tabela']}
    g2car = d.v3['gleba2_cenarios']['B_imovel_separado_desmembrado_de_maior_4MF']['imovel_de_origem']
    cons4 = sum(r['area_ha'] for r in d.v4['mapa_car_v4']['linhas'] if r['gleba'] == 'G1' and r['classe_car'] == 'Area Consolidada')
    r2 = rp['reservatorio_cabeceira_arroio2']
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['arb'] + 'BB'), Patch(fc=COL['car_veg'] + '55', ec=COL['car_veg']), Patch(fc='none', ec=COL['car_rl'], hatch='///', lw=1.4),
                     Line2D([], [], color=COL['car_app'], lw=1.1, ls='--'), Patch(fc='none', ec=COL['car_res'], lw=1.3), Patch(fc='white', ec='#555555', lw=0.8), Patch(fc='none', ec=COL['iat'], hatch='\\\\', lw=1.0)],
                l + [t('orto_arb'), t('car_veg').format(a=fmt(tb['Vegetacao nativa']['declarado_ha']), b=fmt(k['veg_computavel_ha'])),
                     t('car_rl').format(a=fmt(tb['Reserva Legal averbada']['declarado_ha']), b=fmt(RL['exigida_ha'])),
                     t('car_app').format(a=fmt(tb['APP']['declarado_ha']), b=fmt(k['app_g1_ha'])),
                     t('car_res').format(a=fmt(tb['Reservatorio artificial (represa)']['declarado_ha']), b=fmt(tb['Reservatorio na cabeceira do Arroio 2']['declarado_ha']), c=fmt(rp['espelho_22_mai_2026_ha'], 3), d=fmt(r2['area_agua_ha'], 3)),
                     ('Espelhos medidos na ortofoto (22/05/2026)' if LANG == 'pt' else 'Espejos medidos en la ortofoto (22/05/2026)'),
                     t('car_g2').format(a=fmt(g2car['area_ha']))])
    rows = [t('tab_car6')]
    vals = [(fmt(tb['Area do imovel']['declarado_ha']), '%s (G1) · %s' % (fmt(k['area_imovel_ha'] - d.v4['imovel']['G2_ha']), fmt(k['area_imovel_ha']))), (fmt(tb['APP']['declarado_ha']), fmt(k['app_g1_ha'])),
            (fmt(tb['Reserva Legal averbada']['declarado_ha']), fmt(RL['exigida_ha'])), (fmt(tb['Vegetacao nativa']['declarado_ha']), fmt(k['veg_computavel_ha'])),
            (fmt(tb['Area consolidada']['declarado_ha']), fmt(cons4)), (fmt(tb['Reservatorio artificial (represa)']['declarado_ha']), fmt(rp['espelho_22_mai_2026_ha'], 3)),
            (fmt(tb['Reservatorio na cabeceira do Arroio 2']['declarado_ha']), fmt(r2['area_agua_ha'], 3))]
    for lab, v in zip(t('tab_car6_rows'), vals):
        rows.append([lab, v[0], v[1]])
    M.leg_espacio(0.12); M.leg_tabla(rows, col_w=[0.40, 0.22, 0.38])
    M.leg_texto(t('x06_nota').format(r1=fmt(tb['Reserva Legal averbada']['declarado_ha']), r2=fmt(RL['exigida_ha']), v1=fmt(tb['Vegetacao nativa']['declarado_ha']), v2=fmt(k['veg_computavel_ha']),
                                     e=fmt(rp['espelho_22_mai_2026_ha'], 3), e2=fmt(r2['area_agua_ha'], 3))); M.notas()
    return M


# ---------------------------------------------------------------- X07 --------
def X07(d):
    C2 = d.v3['gleba2_cenarios']; k3 = d.v3['kpi']; RL = d.v4['reserva_legal']; pr = RL['principal_mmu_0_05ha_g2_terra_limpa']; co = RL['conservador_sem_fragmento_13']
    g2v = d.v4['vegetacao']['por_gleba']['G2']; g2a = d.v4['app']['fbds']['G2']
    x0, y0, x1, y1 = d.G2.bounds
    ext = (x0 - 150, y0 - 330, x1 + 150, y1 + 330)
    M = novo4(d, t('x07_t'), t('x07_s').format(ha=fmt(k3['area_g2_ha']), alq=fmt(k3['g2_alqueires'], 1)), leg_min_cm=6.4, extent=ext)
    ax = M.ax
    raster_clases(ax, os.path.join(ORTO, 'vegetacao_ortofoto_0_50m.tif'), M.extent, {1: COL['arb'] + 'CC', 2: COL['arb'] + 'CC', 9: COL['arb'] + 'CC', 3: COL['arbu'] + 'CC', 4: COL['pasto'] + '99', 5: COL['solo'] + '66'}, zorder=5, clip=d.G2)
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {1: COL['arb'] + 'AA', 3: COL['solo'] + '66'}, zorder=4, clip=d.sem_orto.intersection(d.G2))
    poly_patches(ax, list(d.ponta.geometry), fc='none', ec=COL['ponta'], hatch='xx', lw=1.2, zorder=9)
    poly_patches(ax, [d.sem_orto.intersection(d.G2)], fc='none', ec=COL['cobert'], hatch='////', lw=0.6, zorder=9)
    a = d.app4[(d.app4.variante == 'fbds') & (d.app4.gleba == 'G2')]
    a[a.situacao == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='white', lw=0.5, alpha=0.95, zorder=8)
    poly_patches(ax, [d.app4_fbds.intersection(d.G2)], fc='none', ec=COL['app_lim'], lw=0.9, ls='--', zorder=12)
    d.arr['G2'].plot(ax=ax, color=COL['fbds'], lw=1.6, zorder=11)
    org = d.carx[(d.carx.relacao == 'cubre_G2') & (d.carx.cod_tema == 'AREA_IMOVEL')]
    _int = gpd.GeoSeries([d.G1, d.G2], crs=CRS_METRICO).union_all().buffer(1)
    _segs = [s for s in [g.boundary.intersection(_int) for g in org.geometry] if not s.is_empty]
    if _segs:
        plot_lines(ax, _segs, color=COL['iat'], lw=1.2, ls=(0, (2, 1.5)), zorder=29)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=2.4, zorder=30)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['prop'], lw=1.4, zorder=31)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=3.0, zorder=32)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['g2'], lw=2.0, zorder=33)
    patch_agujeros(ax, d.G1, fc=FORA + 'DD', ec='none', lw=0, zorder=26)
    c = unary_union(d.ponta.geometry).representative_point()
    ax.annotate(('Ponta norte\n%s ha — a conferir' if LANG == 'pt' else 'Punta norte\n%s ha — a verificar') % fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha']),
                xy=(c.x, c.y), xytext=(c.x + 10, c.y - 190), fontsize=5.6, ha='center', va='center', zorder=41, fontweight='bold', color=COL['ponta'],
                arrowprops=dict(arrowstyle='-', lw=0.6, color=COL['ponta']), bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['ponta'], lw=0.8, alpha=0.95))
    ca = unary_union(a.geometry).representative_point()
    ax.annotate('APP %s ha' % fmt(g2a['exigida_ha']), xy=(ca.x, ca.y), xytext=(ca.x + 60, ca.y + 70), fontsize=5.4, ha='center', va='center', zorder=41, color='white', fontweight='bold',
                arrowprops=dict(arrowstyle='-', lw=0.6, color=COL['app_conf']), bbox=dict(boxstyle='round,pad=0.25', fc=COL['app_conf'], ec='white', lw=0.5, alpha=0.95))
    xm = (x0 + x1) / 2
    ax.text(xm, (y0 + y1) / 2 - 80, t('g2').format(ha=fmt(k3['area_g2_ha']), alq=fmt(k3['g2_alqueires'], 1)), fontsize=6.2, fontweight='bold', ha='center', va='center', rotation=90, zorder=40,
            bbox=dict(boxstyle='round,pad=0.25', fc=COL['g2'], ec='black', lw=0.5, alpha=0.9))
    ax.text(x0 - 75, (y0 + y1) / 2 + 300, t('g1').format(ha=fmt(k3['area_g1_ha'])), fontsize=5.4, fontweight='bold', ha='center', va='center', rotation=90, zorder=40,
            bbox=dict(boxstyle='round,pad=0.2', fc=COL['prop'], ec='black', lw=0.4, alpha=0.9))
    M.grilla(250); M.norte_escala(250)
    B = C2['B_imovel_separado_desmembrado_de_maior_4MF']['imovel_de_origem']; ap = C2['app_g2']
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['g2'], lw=2.4), Line2D([], [], color=COL['prop'], lw=2.0), Line2D([], [], color=COL['iat'], lw=1.2, ls=(0, (2, 1.5))), Patch(fc=FORA, ec='#BBBBBB'),
                 Patch(fc=COL['arb'], hatch='xx', ec=COL['ponta']), Patch(fc=COL['solo'], ec='#BBBBBB'), Patch(fc='none', ec=COL['cobert'], hatch='////', lw=0.6),
                 Patch(fc=COL['app_conf'], ec='white'), Line2D([], [], color=COL['fbds'], lw=1.6)],
                [m8.TV['lim_g2'][LANG].format(ha=fmt(k3['area_g2_ha']), alq=fmt(k3['g2_alqueires'], 1)), m8.TV['lim_g1'][LANG].format(ha=fmt(k3['area_g1_ha'])),
                 t('car_g2_lim').format(a=fmt(B['area_ha']), mf=fmt(B['mod_fiscal_declarado'])), m8.TV['fora'][LANG],
                 t('ponta').format(a=fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha'])),
                 t('cl_solo').format(a='', b='').replace('G1  · G2  ha', '%s ha' % fmt(g2v['solo_cultivo'])),
                 t('sem_orto').format(a=fmt(d.v4['cobertura_voo']['G2']['sem_ortofoto_ha'])),
                 t('app_g2').format(m=fmt(ap['curso_m'], 0), a=fmt(g2a['exigida_ha']), mn=fmt(g2a['envolvente_borda_0_5m_ha'][0]), mx=fmt(g2a['envolvente_borda_0_5m_ha'][1])), t('curso')])
    M.leg_texto(t('x07_kpi'), bold=True, color=AZUL, fs=M.fs + 0.8)
    A_ = C2['A_imovel_unico_principal']; Cc = C2['C_excecao_art67_origem_ate_4MF_em_2008']
    for s in t('x07_txt'):
        M.leg_texto(s.format(g2rl=fmt(A_['rl_parcela_g2_ha']), g1rl=fmt(A_['rl_parcela_g1_ha']), rl=fmt(A_['rl_exigida_imovel_ha']), d=fmt(pr['deficit_ha']), dc=fmt(co['deficit_ha']), car=fmt(B['area_ha']),
                             mf=fmt(B['mod_fiscal_declarado']), v08=fmt(Cc['vegetacao_2008_g2_mapbiomas_ha_indicio']), m=fmt(ap['curso_m'], 0), app=fmt(g2a['exigida_ha']),
                             solo=fmt(g2v['solo_cultivo']), veg=fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha']), sem=fmt(d.v4['cobertura_voo']['G2']['sem_ortofoto_ha'])))
    M.notas()
    return M


# ------------------------------------------------------- figuras compostas ---
def fig_marca(titulo, sub, W=15.0, H=22.0):
    m4.LANG = LANG
    fig = plt.figure(figsize=(W / 2.54, H / 2.54))
    fig.text(1.45 / W, 1 - 0.45 / H, titulo, fontsize=11.5, fontweight='bold', color=AZUL, va='top')
    fig.text(1.45 / W, 1 - 1.0 / H, sub, fontsize=7.2, color='#444444', va='top')
    fig.add_artist(plt.Line2D([1.45 / W, 1 - 0.4 / W], [1 - 1.43 / H] * 2, color=TEAL, lw=1.4))
    fig.add_artist(plt.Line2D([1 - 3.5 / W, 1 - 0.4 / W], [1 - 1.43 / H] * 2, color=LIMA, lw=1.4))
    fig.text(1 - 0.4 / W, 0.22 / H, m4.T['marca'][LANG], fontsize=5.8, color='#666666', ha='right', va='bottom')
    return fig


def panel_axes(fig, W, H, l, b, w, h, extent):
    ax = fig.add_axes([l / W, b / H, w / W, h / H])
    x0, y0, x1, y1 = extent
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    ax.tick_params(labelsize=4.4, length=1.5, pad=1)
    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(4)); ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_utm)); ax.yaxis.set_major_formatter(FuncFormatter(fmt_utm))
    for lab in ax.get_yticklabels():
        lab.set_rotation(90); lab.set_va('center')
    for s in ax.spines.values():
        s.set_linewidth(0.6)
    return ax


def escala(ax, extent, bar_m, fs=4.8, norte='right'):
    x0, y0, x1, y1 = extent; dx, dy = x1 - x0, y1 - y0
    xn = x1 - 0.07 * dx if norte == 'right' else x0 + 0.07 * dx
    xs, ys = x0 + 0.05 * dx, y0 + 0.04 * dy; hb = 0.012 * dy
    for i in range(2):
        ax.add_patch(plt.Rectangle((xs + i * bar_m / 2, ys), bar_m / 2, hb, fc='white' if i else 'black', ec='black', lw=0.5, zorder=60))
    ax.text(xs + bar_m / 2, ys + hb * 1.5, '%s m' % fmt(bar_m, 0), ha='center', va='bottom', fontsize=fs, zorder=60, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.8))
    ax.annotate('', xy=(xn, y1 - 0.04 * dy), xytext=(xn, y1 - 0.14 * dy), arrowprops=dict(facecolor='white', edgecolor='black', width=2, headwidth=6, headlength=5, lw=0.5), zorder=60)
    ax.text(xn, y1 - 0.15 * dy, 'N', ha='center', va='top', fontsize=fs + 0.5, fontweight='bold', zorder=60, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.85))


def orto_5cm(ax, extent, max_px=2200):
    """Le o odm_orthophoto.tif original (5 cm) por janela; reduz com out_shape se a janela superar max_px."""
    x0, y0, x1, y1 = extent
    with rasterio.open(ODM_5CM) as ds:
        win = from_bounds(max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top), ds.transform)
        h, w = int(round(win.height)), int(round(win.width))
        f = max(1, int(np.ceil(max(h, w) / max_px)))
        img = ds.read(window=win, out_shape=(4, h // f, w // f), resampling=Resampling.average)
        tr = ds.window_transform(win)
    hh, ww = img.shape[1], img.shape[2]
    ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
    rgb = np.moveaxis(img[:3], 0, -1).astype(np.float32) / 255.0
    fora = np.array(matplotlib.colors.to_rgb(FORA), dtype=np.float32)
    rgb = np.where((img[3] > 0)[..., None], rgb, fora)
    ax.imshow(rgb, extent=ex, interpolation='bilinear', zorder=1)
    ax.set_facecolor(FORA)
    return ex


def X08(d):
    W, H = 15.0, 20.0
    fig = fig_marca(t('x08_t'), t('x08_s'), W, H)
    rp = d.v4['represa']; r2 = rp['reservatorio_cabeceira_arroio2']; n0 = d.v4['nascentes']['pontos'][0]
    pw, ph = 6.1, 6.1; l1, l2 = 1.45, 1.45 + pw + 1.0; b1 = H - 1.85 - ph; b2 = b1 - 2.15 - ph
    cap_fs = 5.4; cap_dy = 0.5
    # (a) represa
    x0, y0, x1, y1 = d.vaso.bounds; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; hw = max(x1 - x0, y1 - y0) / 2 + 20
    ext = (cx - hw, cy - hw, cx + hw, cy + hw)
    ax = panel_axes(fig, W, H, l1, b1, pw, ph, ext); orto_5cm(ax, ext)
    fb = m13.esp_por(d, 'FBDS'); car = m13.esp_por(d, 'CAR')
    poly_patches(ax, [d.vaso], fc='none', ec=COL['vaso'], lw=1.0, zorder=7)
    poly_patches(ax, [d.represa], fc=COL['agua_o'] + '55', ec=COL['agua_o'], lw=1.2, zorder=8)
    poly_patches(ax, [fb], fc='none', ec=COL['massa'], lw=1.0, ls='--', zorder=9)
    poly_patches(ax, [car], fc='none', ec=COL['car_res'], lw=1.0, ls=(0, (1, 1)), zorder=9)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=0.9, zorder=10)
    dq = rp['alinhamento_dique']
    ax.axvline(dq['dique_x_este_ortofoto'], color='white', lw=0.7, ls=':', zorder=11)
    ax.text(dq['dique_x_este_ortofoto'] - 3, cy + hw - 22, ('dique\n(orto)' if LANG == 'pt' else 'dique\n(orto)'), fontsize=4.6, color='white', ha='right', va='top', zorder=12)
    escala(ax, ext, 50)
    ax.legend([Patch(fc=COL['agua_o'] + '55', ec=COL['agua_o']), Line2D([], [], color=COL['vaso'], lw=1.0), Line2D([], [], color=COL['massa'], ls='--', lw=1.0), Line2D([], [], color=COL['car_res'], ls=(0, (1, 1)), lw=1.0)],
              ['%s ha (22/05/2026)' % fmt(rp['espelho_22_mai_2026_ha'], 3), ('vaso %s ha' % fmt(rp['vaso_indicador_ha'], 3)), 'FBDS 2013 %s ha' % fmt(d.v3['represa']['espelho_por_fonte_ha']['FBDS 2013 (RapidEye 5 m)']),
               'CAR %s ha' % fmt(d.v3['represa']['espelho_por_fonte_ha']['CAR declarado'])], loc='lower right', fontsize=4.6, frameon=True, framealpha=0.85, handlelength=1.5)
    fig.text(l1 / W, (b1 - cap_dy) / H, m4.textwrap.fill(t('p_a').format(a=fmt(rp['espelho_22_mai_2026_ha'], 3), f=fmt(d.v3['represa']['espelho_por_fonte_ha']['FBDS 2013 (RapidEye 5 m)']),
                                                            c=fmt(d.v3['represa']['espelho_por_fonte_ha']['CAR declarado']), v=fmt(rp['vaso_indicador_ha'], 3)), 62), fontsize=cap_fs, va='top', color=GRIS, linespacing=1.2)
    # (b) acude + nascente
    pts = [Point(n0['x'], n0['y'])] + list(d.acude.exterior.coords)
    ux = [p.x if hasattr(p, 'x') else p[0] for p in pts]; uy = [p.y if hasattr(p, 'y') else p[1] for p in pts]
    cx, cy = (min(ux) + max(ux)) / 2, (min(uy) + max(uy)) / 2; hw = max(max(ux) - min(ux), max(uy) - min(uy)) / 2 + 28
    ext = (cx - hw, cy - hw, cx + hw, cy + hw)
    ax = panel_axes(fig, W, H, l2, b1, pw, ph, ext); orto_5cm(ax, ext)
    r2car = d.carx[(d.carx.cod_tema == 'RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO') & (d.carx.relacao == 'propio_G1')]
    small = [p for g in r2car.geometry for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.area < 5000]
    poly_patches(ax, small, fc='none', ec=COL['car_res'], lw=1.0, ls=(0, (1, 1)), zorder=9)
    poly_patches(ax, [d.acude], fc=COL['acude'] + '55', ec=COL['acude'], lw=1.2, zorder=8)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=0.9, zorder=10)
    plot_lines(ax, list(d.eixo.geometry), color=COL['talweg'], lw=0.9, ls=(0, (3, 1.5)), zorder=10)
    ax.scatter([n0['x']], [n0['y']], s=40, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=0.9, zorder=16)
    n1 = d.v4['nascentes']['pontos'][1]
    ax.scatter([n1['x']], [n1['y']], s=30, marker='o', facecolors='none', edgecolors=COL['nasc_prov'], linewidths=1.0, zorder=16)
    ax.text(n1['x'] + 4, n1['y'] + 3, 'dem_1', fontsize=4.6, color='white', zorder=17)
    pa = d.acude.exterior.interpolate(d.acude.exterior.project(Point(n0['x'], n0['y'])))
    ax.plot([n0['x'], pa.x], [n0['y'], pa.y], color='white', lw=0.8, ls='--', zorder=15)
    ax.text((n0['x'] + pa.x) / 2 + 4, (n0['y'] + pa.y) / 2, '%s m' % fmt(n0['dist_agua_aberta_m'], 0), fontsize=5, color='white', fontweight='bold', zorder=17)
    ax.text(n0['x'] + 5, n0['y'] - 6, '306158', fontsize=4.8, color='white', fontweight='bold', zorder=17)
    escala(ax, ext, 25)
    ax.legend([Patch(fc=COL['acude'] + '55', ec=COL['acude']), Line2D([], [], color=COL['car_res'], ls=(0, (1, 1)), lw=1.0), Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=6),
               Line2D([], [], color=COL['fbds'], lw=0.9), Line2D([], [], color=COL['talweg'], lw=0.9, ls=(0, (3, 1.5)))],
              ['%s ha (22/05/2026)' % fmt(r2['area_agua_ha'], 3), 'CAR %s ha' % fmt(r2['area_car_declarada_ha'], 3), ('nascente FBDS' if LANG == 'pt' else 'naciente FBDS'), 'FBDS 2013', ('talvegue DTM' if LANG == 'pt' else 'talweg DTM')],
              loc='upper left', fontsize=4.6, frameon=True, framealpha=0.85, handlelength=1.5)
    fig.text(l2 / W, (b1 - cap_dy) / H, m4.textwrap.fill(t('p_b').format(a=fmt(r2['area_agua_ha'], 3), c=fmt(r2['area_car_declarada_ha'], 3), d=fmt(n0['dist_agua_aberta_m'], 0)), 62), fontsize=cap_fs, va='top', color=GRIS, linespacing=1.2)
    # (c) claro do cauce: vertedouro (unico claro com agua): recorte arroio3_01_M1_espelho
    rec = next(r for r in d.cauce['recortes'] if r['png'] == 'arroio3_01_M1_espelho.png')
    m1 = d.med[(d.med.metodo == 'M1_espelho') & (d.med.arroio == 'Arroio 3 (sul)')]
    m1 = m1.iloc[(m1.geometry.distance(Point(rec['x'], rec['y']))).argmin()]
    hw = 11.0; ext = (rec['x'] - hw, rec['y'] - hw, rec['x'] + hw, rec['y'] + hw)
    ax = panel_axes(fig, W, H, l1, b2, pw, ph, ext); orto_5cm(ax, ext)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=0.9, zorder=10)
    nx, ny = float(m1['nx']) if m1['nx'] is not None else 0.0, float(m1['ny']) if m1['ny'] is not None else 1.0
    if not (abs(nx) + abs(ny) > 0):
        nx, ny = 0.0, 1.0
    e, cv = float(m1['largura_m']), float(m1['calha_veg_m'])
    ax.plot([m1.geometry.x - nx * cv / 2, m1.geometry.x + nx * cv / 2], [m1.geometry.y - ny * cv / 2, m1.geometry.y + ny * cv / 2], color=COL['rec_cult'], lw=1.2, ls='--', zorder=12)
    ax.plot([m1.geometry.x - nx * e / 2, m1.geometry.x + nx * e / 2], [m1.geometry.y - ny * e / 2, m1.geometry.y + ny * e / 2], color=COL['secao'], lw=2.0, zorder=13)
    escala(ax, ext, 5, norte='left')
    ax.legend([Line2D([], [], color=COL['secao'], lw=2.0), Line2D([], [], color=COL['rec_cult'], lw=1.2, ls='--'), Line2D([], [], color=COL['fbds'], lw=0.9)],
              [('espelho %s m' if LANG == 'pt' else 'espejo %s m') % fmt(e, 2), ('calha (veg.) %s m' if LANG == 'pt' else 'cauce (veg.) %s m') % fmt(cv, 1), ('eixo FBDS' if LANG == 'pt' else 'eje FBDS')],
              loc='upper right', fontsize=4.6, frameon=True, framealpha=0.85, handlelength=1.5)
    fig.text(l1 / W, (b2 - cap_dy) / H, m4.textwrap.fill(t('p_c').format(e=fmt(e, 2), c=fmt(cv, 1)), 62), fontsize=cap_fs, va='top', color=GRIS, linespacing=1.2)
    # (d) corredor do Arroio 2 no CHM
    p2 = d.cauce['M3']['Arroio 2 (central)']['pontos'][2]; hw = 90.0
    ext = (p2['x'] - hw, p2['y'] - hw, p2['x'] + hw, p2['y'] + hw)
    ax = panel_axes(fig, W, H, l2, b2, pw, ph, ext)
    with rasterio.open(os.path.join(ORTO, 'chm_hibrido_0_25m.tif')) as ds:
        win = from_bounds(*ext, ds.transform); chm = ds.read(1, window=win); tr = ds.window_transform(win)
        h_, w_ = chm.shape; exr = (tr.c, tr.c + w_ * tr.a, tr.f + h_ * tr.e, tr.f)
    chm = np.ma.masked_less(chm, 0)
    im = ax.imshow(chm, extent=exr, cmap='YlGn', vmin=0, vmax=20, interpolation='nearest', zorder=1); ax.set_facecolor(FORA)
    sec = d.sec[d.sec.arroio == 'Arroio 2 (central)']
    plot_lines(ax, list(sec.geometry), color='white', lw=0.5, alpha=0.8, zorder=8)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=1.2, zorder=10)
    plot_lines(ax, list(d.eixo.geometry), color=COL['talweg'], lw=1.3, ls=(0, (3, 1.5)), zorder=11)
    poly_patches(ax, [d.app4_fbds], fc='none', ec=COL['app_lim'], lw=0.7, ls='--', zorder=9)
    cb = fig.add_axes([(l2 + pw - 1.9) / W, (b2 + 0.62) / H, 1.5 / W, 0.16 / H])
    cbar = fig.colorbar(im, cax=cb, orientation='horizontal'); cbar.ax.tick_params(labelsize=4.2, length=1.5, pad=1); cbar.set_label(t('chm_lbl'), fontsize=4.6, labelpad=1)
    escala(ax, ext, 50)
    ax.legend([Line2D([], [], color=COL['fbds'], lw=1.2), Line2D([], [], color=COL['talweg'], lw=1.3, ls=(0, (3, 1.5))), Line2D([], [], color='white', lw=0.5), Line2D([], [], color=COL['app_lim'], lw=0.7, ls='--')],
              ['FBDS 2013', ('talvegue DTM' if LANG == 'pt' else 'talweg DTM'), ('seções 20 m (0/56 com solo)' if LANG == 'pt' else 'secciones 20 m (0/56 con suelo)'), 'APP 30 m'],
              loc='upper left', fontsize=4.6, frameon=True, framealpha=0.85, handlelength=1.5)
    a2 = d.v4['cursos']['G1 Arroio 2 (central)']
    fig.text(l2 / W, (b2 - cap_dy) / H, m4.textwrap.fill(t('p_d').format(m=fmt(a2['dist_fbds_vs_talweg']['mediana_m'], 0)), 62), fontsize=cap_fs, va='top', color=GRIS, linespacing=1.2)
    # notas
    s = m4.textwrap.fill(t('fonte') + ' · ' + t('notas'), 128)
    fig.text(1.45 / W, 0.5 / H, s, fontsize=5.0, color='#444444', va='bottom', linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
    return fig


def X09(d):
    W, H = 15.0, 17.5
    fig = fig_marca(t('x09_t'), t('x09_s'), W, H)
    ext = (534470.0, 7402870.0, 535270.0, 7403670.0)
    pw = 5.9; ph = pw; l1, l2 = 1.45, 1.45 + pw + 0.95; b = H - 1.75 - ph - 0.4
    # esquerda: S2
    ax = panel_axes(fig, W, H, l1, b, pw, ph, ext)
    x0, y0, x1, y1 = ext
    with rasterio.open(R['rgb']) as ds:
        win = from_bounds(x0, y0, x1, y1, ds.transform); img = ds.read(window=win).astype(np.float32) / 255.0; tr = ds.window_transform(win)
        h_, w_ = img.shape[1], img.shape[2]; exr = (tr.c, tr.c + w_ * tr.a, tr.f + h_ * tr.e, tr.f)
    mask = features.rasterize([(d.prop_u, 1)], out_shape=(h_, w_), transform=tr, fill=0, dtype=np.uint8, all_touched=True)
    rgb = np.moveaxis(np.clip(img * 1.15, 0, 1), 0, -1); fora = np.array(matplotlib.colors.to_rgb(FORA), dtype=np.float32)
    ax.imshow(np.where(mask[..., None] == 1, rgb, fora), extent=exr, interpolation='nearest', zorder=1)
    a, trr = raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), ext, {1: LIMA + '00'}, zorder=5, clip=d.prop_u)
    shp = [s for s, v in features.shapes((a == 1).astype(np.uint8), mask=(a == 1), transform=trr)]
    from shapely.geometry import shape as _shape
    poly_patches(ax, [_shape(s) for s in shp], fc='none', ec=LIMA, lw=0.9, zorder=6)
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), ext, {4: COL['silv'] + 'BB'}, zorder=5, clip=d.prop_u)
    for g in (d.G1, d.G2):
        gpd.GeoSeries([g], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['prop'], lw=1.2, zorder=30)
    patch_agujeros(ax, box(x0 - 50, y0 - 50, x1 + 50, y1 + 50).difference(d.prop_u), fc=FORA, ec='none', lw=0, zorder=25)
    escala(ax, ext, 100)
    ax.set_title(t('x09_a'), fontsize=5.6, color=AZUL, fontweight='bold', pad=3)
    ax.legend([Patch(fc='none', ec=LIMA, lw=0.9), Patch(fc=COL['silv'] + 'BB')], [('floresta nativa RF' if LANG == 'pt' else 'bosque nativo RF'), 'silvicultura RF'], loc='upper left', fontsize=4.4, frameon=True, framealpha=0.9, handlelength=1.4)
    # direita: ortofoto 0,5 m
    ax = panel_axes(fig, W, H, l2, b, pw, ph, ext)
    class _M:  # adaptador minimo para fondo_orto
        pass
    Mm = _M(); Mm.ax = ax; Mm.extent = ext
    fondo_orto(Mm, d)
    a, trr = raster_clases(ax, os.path.join(ORTO, 'vegetacao_ortofoto_0_50m.tif'), ext, {1: LIMA + '00'}, zorder=5, clip=d.prop_u)
    nat = np.isin(a, [1, 2, 3, 9]).astype(np.uint8)
    shp = [s for s, v in features.shapes(nat, mask=nat == 1, transform=trr)]
    poly_patches(ax, [_shape(s) for s in shp if _shape(s).area > 100], fc='none', ec=LIMA, lw=0.6, zorder=6)
    raster_clases(ax, os.path.join(ORTO, 'vegetacao_ortofoto_0_50m.tif'), ext, {6: COL['agua_o']}, zorder=5, clip=d.prop_u)
    for g in (d.G1, d.G2):
        gpd.GeoSeries([g], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['prop'], lw=1.2, zorder=30)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=0.8, zorder=10)
    n0 = d.v4['nascentes']['pontos'][0]
    ax.scatter([n0['x']], [n0['y']], s=26, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=0.7, zorder=16)
    escala(ax, ext, 100)
    ax.set_title(t('x09_b'), fontsize=5.6, color=AZUL, fontweight='bold', pad=3)
    ax.legend([Patch(fc='none', ec=LIMA, lw=0.7), Patch(fc=COL['agua_o']), Line2D([], [], color=COL['fbds'], lw=0.8)], [('arbórea + arbustiva' if LANG == 'pt' else 'arbórea + arbustiva'), ('água 22/05/2026' if LANG == 'pt' else 'agua 22/05/2026'), 'FBDS 2013'],
              loc='upper left', fontsize=4.4, frameon=True, framealpha=0.9, handlelength=1.4)
    # tabela ANTES -> DEPOIS
    keep = t('ad_items')
    rows = [t('tab_x09')]
    for a_ in d.v4['antes_depois']:
        if a_['item'] not in keep:
            continue
        v3 = a_['v3_s2_10m_fbds_dem30']; v4 = a_['v4_ortofoto']; dl = a_['delta']
        nd = 3 if ('eservat' in a_['item'] or 'Represa' in a_['item']) else 2
        f_ = lambda v: (fmt(v, nd) if isinstance(v, (int, float)) and not isinstance(v, bool) else t('ad_txt').get(v, str(v).replace('.', ',')))
        if dl is None:
            sd = '—'
        elif abs(dl) < 0.5 * 10 ** (-nd):
            sd = fmt(0.0, nd)
        else:
            sd = ('+' if dl > 0 else '-') + fmt(abs(dl), nd)
        rows.append([keep[a_['item']], f_(v3), f_(v4), sd])
    tab_h = len(rows) * 0.42
    axt = fig.add_axes([1.45 / W, (b - 0.95 - tab_h) / H, (W - 1.45 - 0.5) / W, tab_h / H]); axt.axis('off')
    tab = axt.table(cellText=rows, colWidths=[0.42, 0.20, 0.20, 0.18], bbox=[0, 0, 1, 1], cellLoc='left')
    tab.auto_set_font_size(False); tab.set_fontsize(6.2)
    for (r_, c_), cell in tab.get_celld().items():
        cell.set_linewidth(0.3); cell.set_edgecolor('#BBBBBB'); cell.PAD = 0.03
        if c_ > 0:
            cell.get_text().set_ha('right')
        if r_ == 0:
            cell.set_facecolor(TEAL); cell.get_text().set_color('white'); cell.get_text().set_fontweight('bold')
        elif r_ % 2 == 0:
            cell.set_facecolor('#F5F7FA')
    fig.text(1.45 / W, (b - 0.95 - tab_h - 0.2) / H, m4.textwrap.fill(t('x09_nota'), 118), fontsize=5.6, color=GRIS, va='top', linespacing=1.25)
    s = m4.textwrap.fill(t('fonte') + ' · ' + t('notas'), 128)
    fig.text(1.45 / W, 0.5 / H, s, fontsize=5.0, color='#444444', va='bottom', linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
    return fig


def guardar(M, nome):
    out_dir = os.path.join(MAPAS_V4, '' if LANG == 'pt' else 'ES')
    os.makedirs(out_dir, exist_ok=True)
    ruta = os.path.join(out_dir, nome + '.png')
    fig = M.fig if hasattr(M, 'fig') else M
    fig.savefig(ruta, dpi=DPI, facecolor='white'); plt.close(fig)
    log('  -> %s' % ruta)


def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='pt', choices=['pt', 'es']); ap.add_argument('--solo', default='')
    a = ap.parse_args(); LANG = a.lang
    m4.LANG = LANG; m8.LANG = LANG; m13.LANG = LANG
    log('=' * 78); log('an_16_mapas_v4 — lang=%s' % LANG); log('=' * 78)
    d = DadosV4()
    quiere = set(a.solo.split(',')) if a.solo else None
    tareas = [('X01_ortofoto_inventario', X01), ('X02_vegetacao_0_5m', X02), ('X03_app_mata_ciliar_v4', X03), ('X04_reserva_legal_v4', X04), ('X05_mapa_car_sicar_v4', X05),
              ('X06_car_declarado_vs_medido_v4', X06), ('X07_gleba2_terra_limpa_v4', X07), ('X08_detalhes_5cm', X08), ('X09_s2_vs_ortofoto', X09)]
    for nome, fn in tareas:
        if quiere and nome.split('_')[0] not in quiere:
            continue
        guardar(fn(d), nome)
    log('an_16 listo')


if __name__ == '__main__':
    main()
