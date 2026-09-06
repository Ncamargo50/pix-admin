# -*- coding: utf-8 -*-
"""an_08_mapas_interior — mapas V01..V06 SO do interior do perimetro, por gleba.

    python an_08_mapas_interior.py --lang pt   -> 03_MAPAS_V2/*.png
    python an_08_mapas_interior.py --lang es   -> 03_MAPAS_V2/ES/*.png

Regra do cliente: nada fora do perimetro. A imagem Sentinel-2 e mascarada pelo poligono das duas glebas
(exterior cinza claro liso), todas as capas vem ja recortadas por an_07 (gleba_G1_* / gleba_G2_*) e os
numeros rotulados saem de resultados_glebas.json. Reutiliza a classe Mapa e os helpers de an_04_mapas
(grade UTM, norte, escala, coluna de legenda); nenhuma cifra e recalculada aqui.
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, R, CRS_METRICO, leer_json, log   # noqa: E402
import an_04_mapas as m4                                                   # noqa: E402
from an_04_mapas import (Mapa, COL, AZUL, TEAL, LIMA, GRIS, fmt, poly_patches, plot_lines,   # noqa: E402
                         raster_clases, DPI)

import matplotlib                                   # noqa: E402
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402
from matplotlib.patches import Patch               # noqa: E402
import geopandas as gpd                            # noqa: E402
import rasterio                                    # noqa: E402
from rasterio import features                      # noqa: E402
from rasterio.windows import from_bounds           # noqa: E402
from shapely.ops import unary_union                # noqa: E402

MAPAS_V2 = os.path.join(PROYECTO, '03_MAPAS_V2')
FORA = '#EEEEEE'          # exterior do perimetro: cinza muito claro liso
COL.update({'g2': '#FF8C00', 'div': '#FFFFFF', 'talv': '#F97316'})
LANG = 'pt'

TV = {
    'notas': {'pt': 'Cena S2C 29/08/2026 · CRS SIRGAS 2000 / UTM 22S (EPSG:31982) · Hidrografia FBDS/IAT 2013 (1:25.000) · '
                    'SÓ O INTERIOR DO PERÍMETRO (exterior em cinza) · DIAGNÓSTICO PRELIMINAR: não substitui laudo; '
                    'leito regular e nascentes a confirmar em campo (RTK).',
              'es': 'Escena S2C 29/08/2026 · CRS SIRGAS 2000 / UTM 22S (EPSG:31982) · Hidrografía FBDS/IAT 2013 (1:25.000) · '
                    'SOLO EL INTERIOR DEL PERÍMETRO (exterior en gris) · DIAGNÓSTICO PRELIMINAR: no sustituye un laudo; '
                    'leito regular y nascentes a confirmar en campo (RTK).'},
    'g1': {'pt': 'Gleba 1 – {ha} ha', 'es': 'Gleba 1 – {ha} ha'},
    'g2': {'pt': 'Gleba 2 – {ha} ha ({alq} alqueires)', 'es': 'Gleba 2 – {ha} ha ({alq} alqueires)'},
    'lim_g1': {'pt': 'Gleba 1 – imóvel principal ({ha} ha)', 'es': 'Gleba 1 – inmueble principal ({ha} ha)'},
    'lim_g2': {'pt': 'Gleba 2 – "os 6 alqueires" ({ha} ha = {alq} alq.)', 'es': 'Gleba 2 – "los 6 alqueires" ({ha} ha = {alq} alq.)'},
    'div': {'pt': 'Linha de divisão entre glebas', 'es': 'Línea de división entre glebas'},
    'fora': {'pt': 'Fora do perímetro (não avaliado)', 'es': 'Fuera del perímetro (no evaluado)'},
    'legenda': {'pt': 'Legenda', 'es': 'Leyenda'},
    # V01
    'v01_t': {'pt': 'V01 · Vegetação nativa no interior do imóvel', 'es': 'V01 · Vegetación nativa en el interior del inmueble'},
    'v01_s': {'pt': 'Classificação RF 10 m sobre S2 29/08/2026 · só dentro do perímetro · fragmentos com ha por gleba',
              'es': 'Clasificación RF 10 m sobre S2 29/08/2026 · solo dentro del perímetro · fragmentos con ha por gleba'},
    'cl_flor': {'pt': 'Floresta nativa (RF) — G1 {a} ha · G2 {b} ha', 'es': 'Floresta nativa (RF) — G1 {a} ha · G2 {b} ha'},
    'cl_silv': {'pt': 'Silvicultura (RF, incerta) — G1 {a} ha · G2 {b} ha', 'es': 'Silvicultura (RF, incierta) — G1 {a} ha · G2 {b} ha'},
    'cl_agua': {'pt': 'Água (RF) — G1 {a} ha · G2 {b} ha', 'es': 'Agua (RF) — G1 {a} ha · G2 {b} ha'},
    'cl_antr': {'pt': 'Área agrícola / antropizada — G1 {a} ha · G2 {b} ha', 'es': 'Área agrícola / antropizada — G1 {a} ha · G2 {b} ha'},
    'frag': {'pt': 'Fragmento de floresta (id · ha na gleba)', 'es': 'Fragmento de floresta (id · ha en la gleba)'},
    'frag_lbl': {'pt': 'Frag. {id}\n{ha} ha', 'es': 'Frag. {id}\n{ha} ha'},
    'tab_veg': {'pt': ['Gleba', 'Floresta', '% gleba', 'Silvic.', 'Agrícola'], 'es': ['Gleba', 'Floresta', '% gleba', 'Silvic.', 'Agrícola']},
    'v01_nota': {'pt': 'A floresta da ponta norte da Gleba 2 ({g2f} ha) é continuação do fragmento 2 (mata do vizinho, floresta desde 1985). '
                       'O cliente informa que a compra dos 6 alqueires não incluía monte: confirmar em campo / escritura.',
                 'es': 'La floresta de la punta norte de la Gleba 2 ({g2f} ha) es continuación del fragmento 2 (monte del vecino, floresta desde 1985). '
                       'El cliente informa que la compra de los 6 alqueires no incluía monte: confirmar en campo / escritura.'},
    # V02
    'v02_t': {'pt': 'V02 · Hidrografia no interior do imóvel', 'es': 'V02 · Hidrografía en el interior del inmueble'},
    'v02_s': {'pt': "Cursos d'água FBDS/IAT 2013 numerados com comprimento por gleba · nascente · reservatório",
              'es': 'Cursos de agua FBDS/IAT 2013 numerados con longitud por gleba · nascente · reservorio'},
    'arr_lbl': {'pt': 'Arroio {n}\n{m} m', 'es': 'Arroyo {n}\n{m} m'},
    'curso': {'pt': "Curso d'água FBDS (até 10 m) — {km} km no imóvel", 'es': 'Curso de agua FBDS (hasta 10 m) — {km} km en el inmueble'},
    'curso_per': {'pt': 'Trecho que coincide com IBGE BC250 "permanente"', 'es': 'Tramo que coincide con IBGE BC250 "permanente"'},
    'nasc': {'pt': 'Nascente FBDS 2013 (perenidade a confirmar)', 'es': 'Nascente FBDS 2013 (perennidad a confirmar)'},
    'cand': {'pt': 'Candidato DEM a nascente — A VALIDAR', 'es': 'Candidato DEM a nascente — A VALIDAR'},
    'talv': {'pt': 'Talvegue DEM (700 m) — só risco, sem curso nas bases', 'es': 'Talweg DEM (700 m) — solo riesgo, sin curso en las bases'},
    'massa': {'pt': "Reservatório FBDS 2013 (espelho {ha} ha, 1 corpo)", 'es': 'Reservorio FBDS 2013 (espejo {ha} ha, 1 cuerpo)'},
    'agua_rf': {'pt': "Espelho d'água RF 2026 — {ha} ha", 'es': 'Espejo de agua RF 2026 — {ha} ha'},
    'tab_arr': {'pt': ['Curso', 'G1 (m)', 'G2 (m)', 'Tipo'], 'es': ['Curso', 'G1 (m)', 'G2 (m)', 'Tipo']},
    'tipo': {'pt': {'atravessa': 'atravessa', 'nasce na gleba': 'nasce na G1'}, 'es': {'atravessa': 'atraviesa', 'nasce na gleba': 'nace en G1'}},
    'v02_nota': {'pt': 'Arroios 1 e 2 confluem {d} m fora do limite oeste. Arroio 3 está represado (reservatórios FBDS 19083 + 20452 = 1 corpo). '
                       'Gleba 2: só {g2m} m do Arroio 1 na ponta norte; sem nascente nem reservatório.',
                 'es': 'Arroyos 1 y 2 confluyen {d} m fuera del límite oeste. El Arroyo 3 está represado (reservorios FBDS 19083 + 20452 = 1 cuerpo). '
                       'Gleba 2: solo {g2m} m del Arroyo 1 en la punta norte; sin nascente ni reservorio.'},
    # V03
    'v03_t': {'pt': 'V03 · Mata ciliar (APP) por gleba', 'es': 'V03 · Mata ciliar (APP) por gleba'},
    'v03_s': {'pt': 'Lei 12.651/2012 art. 4º: 30 m dos cursos até 10 m + 50 m da nascente · cobertura RF 29/08/2026',
              'es': 'Ley 12.651/2012 art. 4º: 30 m de los cursos hasta 10 m + 50 m de la nascente · cobertura RF 29/08/2026'},
    'app_conf': {'pt': 'APP conforme (vegetação nativa) — G1 {a} · G2 {b} ha', 'es': 'APP conforme (vegetación nativa) — G1 {a} · G2 {b} ha'},
    'app_agua': {'pt': 'APP com água — G1 {a} ha', 'es': 'APP con agua — G1 {a} ha'},
    'app_rec': {'pt': 'APP a recompor — G1 {a} ha · G2 {b} ha', 'es': 'APP a recomponer — G1 {a} ha · G2 {b} ha'},
    'app_silv': {'pt': '   dos quais silvicultura — {a} ha', 'es': '   de los cuales silvicultura — {a} ha'},
    'faixa20': {'pt': 'Faixa PRA-PR (20 m / 15 m) — recompor {a} ha', 'es': 'Faja PRA-PR (20 m / 15 m) — recomponer {a} ha'},
    'reserv_faixa': {'pt': 'Faixa 30 m do reservatório (cenário FBDS/IAT) — +{a} ha a recompor', 'es': 'Faja 30 m del reservorio (escenario FBDS/IAT) — +{a} ha a recomponer'},
    'tab_app': {'pt': ['APP', 'G1 (ha)', 'G2 (ha)'], 'es': ['APP', 'G1 (ha)', 'G2 (ha)']},
    'tab_app_rows': {'pt': ['Exigida (30 / 50 m)', 'Com vegetação', 'Água', 'A recompor', 'Recompor PRA-PR 20 m', 'Exigida cen. FBDS/IAT', 'Recompor cen. FBDS/IAT'],
                     'es': ['Exigida (30 / 50 m)', 'Con vegetación', 'Agua', 'A recomponer', 'Recomponer PRA-PR 20 m', 'Exigida esc. FBDS/IAT', 'Recomponer esc. FBDS/IAT']},
    'v03_ver': {'pt': 'Gleba 1: NÃO CONFORME ({a} ha a recompor) · Gleba 2: CONFORME', 'es': 'Gleba 1: NO CONFORME ({a} ha a recomponer) · Gleba 2: CONFORME'},
    # V04
    'v04_t': {'pt': 'V04 · Reserva Legal por gleba (20%)', 'es': 'V04 · Reserva Legal por gleba (20%)'},
    'v04_s': {'pt': 'Art. 12 (20%) · art. 15 (APP vegetada computa) · RL existente por gleba · proposta só dentro da Gleba 1',
              'es': 'Art. 12 (20%) · art. 15 (APP vegetada computa) · RL existente por gleba · propuesta solo dentro de la Gleba 1'},
    'rl_rem': {'pt': 'Remanescente fora da APP — G1 {a} · G2 {b} ha', 'es': 'Remanente fuera de la APP — G1 {a} · G2 {b} ha'},
    'rl_app': {'pt': 'APP vegetada computável (art. 15) — G1 {a} · G2 {b} ha', 'es': 'APP vegetada computable (art. 15) — G1 {a} · G2 {b} ha'},
    'rl_corr': {'pt': 'Corredor de recomposição proposto (G1) — {a} ha', 'es': 'Corredor de recomposición propuesto (G1) — {a} ha'},
    'rl_lim': {'pt': 'RL proposta recortada à Gleba 1 — {a} ha', 'es': 'RL propuesta recortada a la Gleba 1 — {a} ha'},
    'tab_rl': {'pt': ['Reserva Legal', 'G1 (ha)', 'G2 (ha)'], 'es': ['Reserva Legal', 'G1 (ha)', 'G2 (ha)']},
    'tab_rl_rows': {'pt': ['Exigida (20%)', 'Existente (art. 15)', 'Déficit', 'RL proposta recortada'],
                    'es': ['Exigida (20%)', 'Existente (art. 15)', 'Déficit', 'RL propuesta recortada']},
    'v04_nota': {'pt': 'Gleba 1: NÃO CONFORME (déficit {d1} ha). Gleba 2: existente {e2} ha vs exigida {x2} ha (déficit {d2} ha) — só se a floresta da ponta norte pertencer à gleba. '
                       'A RL proposta recortada à G1 ({p1} ha) fica {f} ha aquém dos {x1} ha: o corredor deve ser ampliado dentro da G1.',
                 'es': 'Gleba 1: NO CONFORME (déficit {d1} ha). Gleba 2: existente {e2} ha vs exigida {x2} ha (déficit {d2} ha) — solo si la floresta de la punta norte pertenece a la gleba. '
                       'La RL propuesta recortada a G1 ({p1} ha) queda {f} ha por debajo de los {x1} ha: el corredor debe ampliarse dentro de G1.'},
    # V05
    'v05_t': {'pt': 'V05 · Uso e cobertura CAR/SICAR por gleba', 'es': 'V05 · Uso y cobertura CAR/SICAR por gleba'},
    'v05_s': {'pt': 'Polígonos sem sobreposição · G1 fecha em {a} ha · G2 fecha em {b} ha · IN MMA 2/2014',
              'es': 'Polígonos sin superposición · G1 cierra en {a} ha · G2 cierra en {b} ha · IN MMA 2/2014'},
    'tab_car': {'pt': ['Classe CAR / subclasse', 'G1', 'G2'], 'es': ['Clase CAR / subclase', 'G1', 'G2']},
    'soma': {'pt': 'Soma', 'es': 'Suma'},
    # V06
    'v06_t': {'pt': 'V06 · Detalhe da Gleba 2 ("os 6 alqueires")', 'es': 'V06 · Detalle de la Gleba 2 ("los 6 alqueires")'},
    'v06_s': {'pt': '{ha} ha = {alq} alqueires paulistas · vegetação, APP e Reserva Legal próprias', 'es': '{ha} ha = {alq} alqueires paulistas · vegetación, APP y Reserva Legal propias'},
    'v06_kpi': {'pt': 'RL exigida {x} ha / existente {e} ha', 'es': 'RL exigida {x} ha / existente {e} ha'},
    'v06_txt': {'pt': ['Para estar na lei a Gleba 2 precisa de {x} ha de vegetação nativa (RL 20%); a APP própria ({app} ha, vegetada) computa dentro dela (art. 15).',
                       'Hoje a imagem mostra {e} ha de floresta na ponta norte (fragmento 2, contínuo com a mata do vizinho): falta {d} ha.',
                       'O cliente afirma que a compra não incluía monte: confirmar em campo e na escritura se essa floresta pertence à gleba. Se não pertencer, a RL exigida ({x} ha) fica integralmente a recompor ou compensar.',
                       'APP: {m} m do Arroio 1 na ponta norte, faixa de 30 m com vegetação nativa ({app} ha): CONFORME. Sem nascente nem reservatório.'],
                'es': ['Para estar en la ley la Gleba 2 necesita {x} ha de vegetación nativa (RL 20%); la APP propia ({app} ha, vegetada) computa dentro de ella (art. 15).',
                       'Hoy la imagen muestra {e} ha de floresta en la punta norte (fragmento 2, continuo con el monte del vecino): faltan {d} ha.',
                       'El cliente afirma que la compra no incluía monte: confirmar en campo y en la escritura si esa floresta pertenece a la gleba. Si no pertenece, la RL exigida ({x} ha) queda íntegramente a recomponer o compensar.',
                       'APP: {m} m del Arroyo 1 en la punta norte, faja de 30 m con vegetación nativa ({app} ha): CONFORME. Sin nascente ni reservorio.']},
}


def t(k):
    return TV[k][LANG]


# ------------------------------------------------------------------ dados ----
class DadosV2:
    def __init__(self):
        self.g = leer_json(os.path.join(ANALISIS, 'resultados_glebas.json'))
        self.res = leer_json(os.path.join(ANALISIS, 'resultados_analisis.json'))
        A = lambda n: gpd.read_file(os.path.join(ANALISIS, n + '.geojson'))
        self.lim = A('gleba_limites')
        self.G1 = self.lim[self.lim.gleba == 'G1'].geometry.iloc[0]
        self.G2 = self.lim[self.lim.gleba == 'G2'].geometry.iloc[0]
        self.prop_u = unary_union([self.G1, self.G2])
        self.car = {u: A('gleba_%s_car' % u) for u in ('G1', 'G2')}
        self.app = {u: A('gleba_%s_app' % u) for u in ('G1', 'G2')}
        self.rl = {u: A('gleba_%s_rl_existente' % u) for u in ('G1', 'G2')}
        self.arr = {u: A('gleba_%s_arroios' % u) for u in ('G1', 'G2')}
        self.flor = {u: A('gleba_%s_floresta' % u) for u in ('G1', 'G2')}
        self.lag = A('gleba_G1_lagoas')
        nasc = A('nascentes_consolidadas')
        self.nasc = nasc[nasc.geometry.within(self.prop_u)]
        talv = A('talvegue_dem_candidatos')
        talv['geometry'] = talv.geometry.intersection(self.prop_u)
        self.talv = talv[~talv.geometry.is_empty]
        rlp = A('RL_proposta'); self.rl_prop_g1 = unary_union(rlp.geometry).intersection(self.G1)
        cor = A('RL_corredor_recomposicao'); self.corr_g1 = unary_union(cor.geometry).intersection(self.G1)
        hidro = A('hidrografia_consolidada')
        fb = hidro[(hidro.fonte == 'FBDS')]
        self.fb_per = fb[fb.regime == 'perene'].geometry.intersection(self.prop_u)
        self.fb_per = self.fb_per[~self.fb_per.is_empty]
        # geometrias de desenho (identicas as de an_04/an_07)
        n_in = nasc[(nasc.fonte == 'FBDS') & nasc.dentro_propriedade]
        self.faixa20 = unary_union([unary_union(fb.geometry).buffer(20), unary_union(n_in.geometry).buffer(15)]).intersection(self.prop_u)
        self.app30 = unary_union([unary_union(fb.geometry).buffer(30), unary_union(n_in.geometry).buffer(50)]).intersection(self.prop_u)
        # a faixa do reservatorio (cenario FBDS/IAT) vem da capa APP de an_07
        fa = self.app['G1'][self.app['G1'].cenario == 'fbds_iat_adicional']
        self.reserv_faixa = unary_union(fa.geometry) if len(fa) else None
        self.g1 = self.g['G1']; self.g2 = self.g['G2']


def extent_interior(d, margen=120):
    x0, y0, x1, y1 = d.prop_u.bounds
    return (x0 - margen, y0 - margen, x1 + margen, y1 + margen)


# ------------------------------------------------------------ base comum -----
def fondo_interior(M, d, gain=1.15):
    """Imagem S2 RGB mascarada ao perimetro: fora = cinza claro liso."""
    x0, y0, x1, y1 = M.extent
    with rasterio.open(R['rgb']) as ds:
        win = from_bounds(max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top), ds.transform)
        img = ds.read(window=win).astype(np.float32) / 255.0
        tr = ds.window_transform(win)
        h, w = img.shape[1], img.shape[2]
        ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
    mask = features.rasterize([(d.prop_u, 1)], out_shape=(h, w), transform=tr, fill=0, dtype=np.uint8, all_touched=True)
    img = np.clip(img * gain, 0, 1)
    rgb = np.moveaxis(img, 0, -1)
    fora = np.array(matplotlib.colors.to_rgb(FORA), dtype=np.float32)
    rgb = np.where(mask[..., None] == 1, rgb, fora)
    M.ax.imshow(rgb, extent=ex, interpolation='nearest', zorder=1)
    M.ax.set_facecolor(FORA)
    # cobertura vetorial do exterior por cima do raster (bordas limpas)
    x0, y0, x1, y1 = M.extent
    from shapely.geometry import box
    ext_poly = box(x0 - 50, y0 - 50, x1 + 50, y1 + 50).difference(d.prop_u)
    patch_agujeros(M.ax, ext_poly, fc=FORA, ec='none', lw=0, zorder=25)


def patch_agujeros(ax, geom, **kw):
    """(Multi)Polygon con agujeros como PathPatch (poly_patches no pinta agujeros)."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    parts = geom.geoms if hasattr(geom, 'geoms') else [geom]
    verts, codes = [], []
    for p in parts:
        if p.geom_type != 'Polygon' or p.is_empty:
            continue
        for ring in [p.exterior] + list(p.interiors):
            xy = np.asarray(ring.coords)
            verts.extend(xy.tolist()); codes.extend([Path.MOVETO] + [Path.LINETO] * (len(xy) - 2) + [Path.CLOSEPOLY])
    if verts:
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def glebas(M, d, rotular=True, lw=1.8, fs=6.0):
    """Limites das duas glebas + linha de divisao + rotulos."""
    ax = M.ax
    for g, col in [(d.G1, COL['prop']), (d.G2, COL['g2'])]:
        gpd.GeoSeries([g], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=lw + 1.0, zorder=30)
        gpd.GeoSeries([g], crs=CRS_METRICO).boundary.plot(ax=ax, color=col, lw=lw, zorder=31)
    if rotular:
        x0, y0, x1, y1 = d.G1.bounds
        ax.text((x0 + x1) / 2 - 20, 7402750, t('g1').format(ha=fmt(d.g1['area_ha'])), fontsize=fs + 0.6, fontweight='bold', color='black',
                ha='center', va='center', rotation=90, zorder=40, bbox=dict(boxstyle='round,pad=0.25', fc=COL['prop'], ec='black', lw=0.5, alpha=0.9))
        x0, y0, x1, y1 = d.G2.bounds
        ax.text((x0 + x1) / 2 + 5, (y0 + y1) / 2 - 60, t('g2').format(ha=fmt(d.g2['area_ha']), alq=fmt(d.g2['alqueires_paulistas'], 1)),
                fontsize=fs, fontweight='bold', color='black', ha='center', va='center', rotation=90, zorder=40,
                bbox=dict(boxstyle='round,pad=0.25', fc=COL['g2'], ec='black', lw=0.5, alpha=0.9))


def leg_glebas(d):
    return ([Line2D([], [], color=COL['prop'], lw=2.2), Line2D([], [], color=COL['g2'], lw=2.2), Patch(fc=FORA, ec='#BBBBBB')],
            [t('lim_g1').format(ha=fmt(d.g1['area_ha'])), t('lim_g2').format(ha=fmt(d.g2['area_ha']), alq=fmt(d.g2['alqueires_paulistas'], 1)), t('fora')])


def novo(d, titulo, sub, leg_min_cm=5.6, extent=None):
    m4.LANG = LANG
    m4.T['notas'] = TV['notas']
    M = Mapa('V', titulo, sub, extent or extent_interior(d), leg_min_cm=leg_min_cm)
    fondo_interior(M, d)
    return M


def arroios(M, d, rotular=True, lw=1.4):
    ax = M.ax
    for u in ('G1', 'G2'):
        d.arr[u].plot(ax=ax, color=COL['fbds'], lw=lw, zorder=11)
    if len(d.fb_per):
        gpd.GeoSeries(list(d.fb_per), crs=CRS_METRICO).plot(ax=ax, color=COL['fbds_perene'], lw=lw + 0.9, zorder=12)
    if rotular:
        off = {1: (-165, 60), 2: (140, 0), 3: (-190, -120)}
        for _, r in d.arr['G1'].iterrows():
            c = r.geometry.interpolate(0.55 if r.n != 3 else 0.35, normalized=True)
            dx_, dy_ = off.get(int(r.n), (0, 0))
            ax.annotate(t('arr_lbl').format(n=r.n, m=fmt(r.comprimento_dentro_m, 0)), xy=(c.x, c.y), xytext=(c.x + dx_, c.y + dy_),
                        fontsize=5.4, ha='center', va='center', zorder=40, color='white', fontweight='bold',
                        arrowprops=dict(arrowstyle='-', lw=0.6, color=COL['fbds']),
                        bbox=dict(boxstyle='round,pad=0.25', fc=COL['fbds'], ec='white', lw=0.5, alpha=0.95))


def nascentes(M, d, ids=True):
    ax = M.ax
    nf = d.nasc[d.nasc.fonte == 'FBDS']
    ax.scatter(nf.geometry.x, nf.geometry.y, s=34, marker='o', c=COL['nasc'], edgecolors='white', linewidths=0.8, zorder=15)
    nd = d.nasc[d.nasc.candidato_dem]
    ax.scatter(nd.geometry.x, nd.geometry.y, s=46, marker='^', c=COL['cand'], edgecolors='black', linewidths=0.6, zorder=16)
    if ids:
        for _, r in nd.iterrows():
            ax.text(r.geometry.x + 28, r.geometry.y, r.id_fonte, fontsize=5.2, va='center', zorder=17,
                    bbox=dict(boxstyle='round,pad=0.12', fc=COL['cand'], ec='none', alpha=0.85))


# ---------------------------------------------------------------- V01 --------
def V01(d):
    M = novo(d, t('v01_t'), t('v01_s'), leg_min_cm=6.0)
    ax = M.ax
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent,
                  {1: COL['floresta'], 2: COL['agua'], 3: COL['antrop'] + 'AA', 4: COL['silv']}, alpha=0.88, zorder=5, clip=d.prop_u)
    for u in ('G1', 'G2'):
        fl = d.flor[u]
        fl.boundary.plot(ax=ax, color='white', lw=1.3, zorder=12)
        fl.boundary.plot(ax=ax, color=LIMA, lw=0.7, zorder=13)
    off = {('G1', 2): (230, -90), ('G1', 13): (150, 40), ('G1', 30): (-20, -190), ('G2', 2): (-250, -30)}
    for u in ('G1', 'G2'):
        for _, r in d.flor[u].iterrows():
            c = r.geometry.representative_point()
            dx_, dy_ = off.get((u, int(r.frag_id)), (0, 0))
            ax.annotate(t('frag_lbl').format(id=r.frag_id, ha=fmt(r.area_dentro_ha)), xy=(c.x, c.y), xytext=(c.x + dx_, c.y + dy_),
                        fontsize=5.4, ha='center', va='center', zorder=41, fontweight='bold',
                        arrowprops=dict(arrowstyle='-', lw=0.6, color='black') if (dx_ or dy_) else None,
                        bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['floresta'], lw=0.7, alpha=0.93))
    glebas(M, d)
    M.grilla(); M.norte_escala()
    v1, v2 = d.g1['vegetacao'], d.g2['vegetacao']
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['floresta']), Patch(fc=COL['silv'], hatch='////', ec='#4E4E00'), Patch(fc=COL['agua']),
                     Patch(fc=COL['antrop'], ec='#BBBBBB'), Patch(fc='none', ec=LIMA, lw=1.5)],
                l + [t('cl_flor').format(a=fmt(v1['floresta_nativa_car_ha']), b=fmt(v2['floresta_nativa_car_ha'])),
                     t('cl_silv').format(a=fmt(v1['silvicultura_ha']), b=fmt(v2['silvicultura_ha'])),
                     t('cl_agua').format(a=fmt(v1['agua_rf_ha']), b=fmt(v2['agua_rf_ha'])),
                     t('cl_antr').format(a=fmt(v1['area_agricola_car_ha']), b=fmt(v2['area_agricola_car_ha'])), t('frag')])
    rows = [t('tab_veg')]
    for u, v in [('G1', v1), ('G2', v2)]:
        rows.append([u, fmt(v['floresta_nativa_car_ha']), fmt(v['pct_da_gleba'], 1) + '%', fmt(v['silvicultura_ha']), fmt(v['area_agricola_car_ha'])])
    M.leg_tabla(rows, col_w=[0.16, 0.22, 0.2, 0.19, 0.23])
    M.leg_texto(t('v01_nota').format(g2f=fmt(v2['floresta_nativa_car_ha'])))
    M.notas()
    return M


# ---------------------------------------------------------------- V02 --------
def V02(d):
    M = novo(d, t('v02_t'), t('v02_s'), leg_min_cm=6.0)
    ax = M.ax
    # espelho RF (CAR reservatorio) e massa FBDS
    res = d.car['G1'][d.car['G1'].classe_car.str.startswith('Reservat')]
    res.plot(ax=ax, fc=COL['agua_s2'], ec='none', alpha=0.9, zorder=9)
    d.lag.boundary.plot(ax=ax, color=COL['massa'], lw=1.2, zorder=13)
    if len(d.talv):
        plot_lines(ax, d.talv.geometry, color=COL['talv'], lw=1.2, ls=(0, (3, 2)), zorder=10)
    arroios(M, d)
    nascentes(M, d)
    c = unary_union(d.lag.geometry).centroid
    lg = d.g1['lagoas']
    ax.annotate(t('massa').format(ha=fmt(lg['espelho_fbds_2013_ha'])).replace(' (', '\n('), xy=(c.x, c.y), xytext=(c.x - 40, c.y - 200),
                fontsize=5.2, ha='center', zorder=40, arrowprops=dict(arrowstyle='-', lw=0.5, color='black'),
                bbox=dict(boxstyle='round,pad=0.2', fc='white', ec=COL['massa'], lw=0.6, alpha=0.92))
    glebas(M, d)
    M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Line2D([], [], color=COL['fbds'], lw=1.6), Line2D([], [], color=COL['fbds_perene'], lw=2.4),
                     Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc'], markeredgecolor='white', ms=6),
                     Line2D([], [], marker='^', color='none', markerfacecolor=COL['cand'], markeredgecolor='black', ms=7),
                     Line2D([], [], color=COL['talv'], lw=1.2, ls=(0, (3, 2))),
                     Patch(fc='none', ec=COL['massa'], lw=1.2), Patch(fc=COL['agua_s2'])],
                l + [t('curso').format(km=fmt(d.g['UNICO']['arroios']['km_dentro'], 3)), t('curso_per'), t('nasc'), t('cand'), t('talv'),
                     t('massa').format(ha=fmt(lg['espelho_fbds_2013_ha'])), t('agua_rf').format(ha=fmt(lg['espelho_rf_2026_ha']))])
    rows = [t('tab_arr')]
    a2 = {r['n']: r for r in d.g2['arroios']['lista']}
    for r in d.g1['arroios']['lista']:
        rows.append([('Arroio' if LANG == 'pt' else 'Arroyo') + ' %d (%s)' % (r['n'], r['posicao']), fmt(r['comprimento_dentro_m'], 0),
                     fmt(a2[r['n']]['comprimento_dentro_m'], 0) if r['n'] in a2 else '0', t('tipo')[r['tipo']] + (' + repr.' if r['represado'] else '')])
    M.leg_tabla(rows, col_w=[0.32, 0.14, 0.14, 0.40])
    M.leg_texto(t('v02_nota').format(d=fmt(d.g['_meta']['confluencia_mais_proxima_do_limite_m'], 0), g2m=fmt(a2[1]['comprimento_dentro_m'], 0)))
    M.notas()
    return M


# ---------------------------------------------------------------- V03 --------
def _app_capas(M, d):
    ax = M.ax
    for u in ('G1', 'G2'):
        a = d.app[u]
        base = a[a.cenario == 'base']
        base[base.situacao == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='none', alpha=0.9, zorder=6)
        base[base.situacao == 'a recompor'].plot(ax=ax, fc=COL['app_rec'], ec='none', alpha=0.9, zorder=6)
        base[base.situacao == 'agua'].plot(ax=ax, fc=COL['app_agua'], ec='none', alpha=0.9, zorder=6)
        rec_u = unary_union(base[base.situacao == 'a recompor'].geometry) if (base.situacao == 'a recompor').any() else None
        if rec_u is not None and not rec_u.is_empty:
            raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent, {4: COL['app_silv']}, zorder=7, clip=rec_u)
    if d.reserv_faixa is not None:
        poly_patches(ax, [d.reserv_faixa], fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8, zorder=8)
    poly_patches(ax, [d.app30], fc='none', ec=COL['app_lim'], lw=0.8, ls='--', zorder=12)
    poly_patches(ax, [d.faixa20], fc='none', ec=COL['faixa20'], lw=0.9, ls=(0, (3, 1.5)), zorder=13)
    arroios(M, d, rotular=False, lw=1.0)
    nascentes(M, d, ids=False)


def V03(d):
    M = novo(d, t('v03_t'), t('v03_s'), leg_min_cm=6.0)
    _app_capas(M, d)
    glebas(M, d)
    M.grilla(); M.norte_escala()
    a1, a2 = d.g1['app'], d.g2['app']
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['app_conf']), Patch(fc=COL['app_agua']), Patch(fc=COL['app_rec']), Patch(fc=COL['app_silv']),
                     Line2D([], [], color=COL['app_lim'], lw=0.9, ls='--'), Line2D([], [], color=COL['faixa20'], lw=1.1, ls=(0, (3, 1.5))),
                     Patch(fc='none', ec=COL['reserv_faixa'], hatch='\\\\\\', lw=0.8), Line2D([], [], color=COL['fbds'], lw=1.0),
                     Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc'], markeredgecolor='white', ms=6)],
                l + [t('app_conf').format(a=fmt(a1['com_vegetacao_nativa_ha']), b=fmt(a2['com_vegetacao_nativa_ha'])),
                     t('app_agua').format(a=fmt(a1['agua_ha'])),
                     t('app_rec').format(a=fmt(a1['a_recompor_ha']), b=fmt(a2['a_recompor_ha'])),
                     t('app_silv').format(a=fmt(a1['a_recompor_silvicultura_ha'])),
                     m4.T['app_lim'][LANG].format(ha=fmt(d.g['UNICO']['app']['exigida_ha'])),
                     t('faixa20').format(a=fmt(a1['cenario_pra_pr_20m']['a_recompor_ha'])),
                     t('reserv_faixa').format(a=fmt(a1['cenario_fbds_iat']['a_recompor_ha'] - a1['a_recompor_ha'])),
                     m4.T['curso'][LANG], t('nasc')])
    rows = [t('tab_app')]
    vals = [('exigida_ha',), ('com_vegetacao_nativa_ha',), ('agua_ha',), ('a_recompor_ha',), ('cenario_pra_pr_20m', 'a_recompor_ha'),
            ('cenario_fbds_iat', 'exigida_ha'), ('cenario_fbds_iat', 'a_recompor_ha')]
    for lab, key in zip(t('tab_app_rows'), vals):
        g = lambda a: a[key[0]] if len(key) == 1 else a[key[0]][key[1]]
        rows.append([lab, fmt(g(a1)), fmt(g(a2))])
    M.leg_tabla(rows, col_w=[0.56, 0.22, 0.22])
    M.leg_texto(t('v03_ver').format(a=fmt(a1['a_recompor_ha'])), bold=True, color=AZUL)
    M.notas()
    return M


# ---------------------------------------------------------------- V04 --------
def V04(d):
    M = novo(d, t('v04_t'), t('v04_s'), leg_min_cm=6.0)
    ax = M.ax
    for u in ('G1', 'G2'):
        r = d.rl[u]
        r[r.classe.str.startswith('remanescente')].plot(ax=ax, fc=COL['rl_rem'], ec='none', alpha=0.9, zorder=6)
        r[r.classe.str.startswith('APP')].plot(ax=ax, fc=COL['rl_app'], ec='none', alpha=0.9, zorder=6)
    poly_patches(ax, [d.corr_g1], fc=COL['rl_corr'] + '99', ec='#3F6B00', hatch='///', lw=0.4, zorder=7)
    gpd.GeoSeries([d.rl_prop_g1], crs=CRS_METRICO).boundary.plot(ax=ax, color='white', lw=2.0, zorder=12)
    gpd.GeoSeries([d.rl_prop_g1], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['rl_lim'], lw=1.2, zorder=13)
    arroios(M, d, rotular=False, lw=0.8)
    glebas(M, d)
    M.grilla(); M.norte_escala()
    r1, r2 = d.g1['reserva_legal'], d.g2['reserva_legal']
    h, l = leg_glebas(d)
    M.leg_titulo(t('legenda'))
    M.leg_items(h + [Patch(fc=COL['rl_rem']), Patch(fc=COL['rl_app']), Patch(fc=COL['rl_corr'], hatch='///', ec='#3F6B00'),
                     Line2D([], [], color=COL['rl_lim'], lw=1.6), Line2D([], [], color=COL['fbds'], lw=0.8)],
                l + [t('rl_rem').format(a=fmt(r1['remanescente_fora_app_ha']), b=fmt(r2['remanescente_fora_app_ha'])),
                     t('rl_app').format(a=fmt(r1['app_com_vegetacao_art15_ha']), b=fmt(r2['app_com_vegetacao_art15_ha'])),
                     t('rl_corr').format(a=fmt(r1['corredor_recomposicao_recortado_ha'])),
                     t('rl_lim').format(a=fmt(r1['rl_proposta_recortada_ha'])), m4.T['curso'][LANG]])
    rows = [t('tab_rl')]
    for lab, key in zip(t('tab_rl_rows'), ['exigida_ha', 'existente_com_app_art15_ha', 'deficit_com_app_art15_ha', 'rl_proposta_recortada_ha']):
        rows.append([lab, fmt(r1[key]), fmt(r2[key]) if key != 'rl_proposta_recortada_ha' else '—'])
    M.leg_tabla(rows, col_w=[0.56, 0.22, 0.22])
    M.leg_texto(t('v04_nota').format(d1=fmt(r1['deficit_com_app_art15_ha']), e2=fmt(r2['existente_com_app_art15_ha']), x2=fmt(r2['exigida_ha']),
                                     d2=fmt(r2['deficit_com_app_art15_ha']), p1=fmt(r1['rl_proposta_recortada_ha']),
                                     f=fmt(-r1['rl_proposta_recortada_vs_exigida_ha']), x1=fmt(r1['exigida_ha'])))
    M.notas()
    return M


# ---------------------------------------------------------------- V05 --------
def V05(d):
    M = novo(d, t('v05_t'), t('v05_s').format(a=fmt(d.g1['mapa_car']['soma_ha']), b=fmt(d.g2['mapa_car']['soma_ha'])), leg_min_cm=6.2)
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
    glebas(M, d)
    M.grilla(); M.norte_escala()
    M.leg_titulo(t('legenda'))
    M.leg_items(handles, labels)
    rows.append([t('soma'), fmt(d.g1['mapa_car']['soma_ha']), fmt(d.g2['mapa_car']['soma_ha'])])
    M.leg_tabla(rows, col_w=[0.58, 0.21, 0.21], bold_last=True)
    M.notas()
    return M


# ---------------------------------------------------------------- V06 --------
def V06(d):
    x0, y0, x1, y1 = d.G2.bounds
    ext = (x0 - 150, y0 - 330, x1 + 150, y1 + 330)
    M = novo(d, t('v06_t'), t('v06_s').format(ha=fmt(d.g2['area_ha']), alq=fmt(d.g2['alqueires_paulistas'], 1)), leg_min_cm=6.2, extent=ext)
    ax = M.ax
    raster_clases(ax, os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'), M.extent,
                  {1: COL['floresta'], 3: COL['antrop'] + '99', 4: COL['silv']}, alpha=0.85, zorder=5, clip=d.G2)
    a = d.app['G2']
    a[a.situacao == 'conforme'].plot(ax=ax, fc=COL['app_conf'], ec='white', lw=0.5, alpha=0.95, zorder=8)
    poly_patches(ax, [d.app30.intersection(d.G2)], fc='none', ec=COL['app_lim'], lw=0.9, ls='--', zorder=12)
    d.arr['G2'].plot(ax=ax, color=COL['fbds'], lw=1.6, zorder=11)
    fl = d.flor['G2']
    fl.boundary.plot(ax=ax, color='white', lw=1.3, zorder=12); fl.boundary.plot(ax=ax, color=LIMA, lw=0.7, zorder=13)
    # so o G1 vizinho como contorno (interior: e do proprio imovel; mas o mapa e da Gleba 2)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=2.4, zorder=30)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['prop'], lw=1.4, zorder=31)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=3.0, zorder=32)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['g2'], lw=2.0, zorder=33)
    # cobrir a Gleba 1 com cinza (mapa so da Gleba 2)
    patch_agujeros(ax, d.G1, fc=FORA + 'DD', ec='none', lw=0, zorder=26)
    r2 = d.g2['reserva_legal']; v2 = d.g2['vegetacao']; a2 = d.g2['app']
    c = unary_union(d.flor['G2'].geometry).representative_point()
    ax.annotate(t('frag_lbl').format(id=2, ha=fmt(v2['floresta_nativa_car_ha'])), xy=(c.x, c.y), xytext=(c.x, c.y - 170), fontsize=5.6,
                ha='center', va='center', zorder=41, fontweight='bold', arrowprops=dict(arrowstyle='-', lw=0.6, color='black'),
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=COL['floresta'], lw=0.7, alpha=0.93))
    ca = unary_union(a.geometry).representative_point()
    ax.annotate('APP %s ha' % fmt(a2['exigida_ha']), xy=(ca.x, ca.y), xytext=(ca.x - 120, ca.y + 30), fontsize=5.4, ha='center', va='center', zorder=41,
                color='white', fontweight='bold', arrowprops=dict(arrowstyle='-', lw=0.6, color=COL['app_conf']),
                bbox=dict(boxstyle='round,pad=0.25', fc=COL['app_conf'], ec='white', lw=0.5, alpha=0.95))
    xm = (x0 + x1) / 2
    ax.text(xm, (y0 + y1) / 2 - 80, t('g2').format(ha=fmt(d.g2['area_ha']), alq=fmt(d.g2['alqueires_paulistas'], 1)), fontsize=6.2, fontweight='bold',
            ha='center', va='center', rotation=90, zorder=40, bbox=dict(boxstyle='round,pad=0.25', fc=COL['g2'], ec='black', lw=0.5, alpha=0.9))
    ax.text(x0 - 75, (y0 + y1) / 2 + 300, t('g1').format(ha=fmt(d.g1['area_ha'])), fontsize=5.4, fontweight='bold', ha='center', va='center', rotation=90, zorder=40,
            bbox=dict(boxstyle='round,pad=0.2', fc=COL['prop'], ec='black', lw=0.4, alpha=0.9))
    M.grilla(250); M.norte_escala(250)
    M.leg_titulo(t('legenda'))
    M.leg_items([Line2D([], [], color=COL['g2'], lw=2.4), Line2D([], [], color=COL['prop'], lw=2.0), Patch(fc=FORA, ec='#BBBBBB'),
                 Patch(fc=COL['floresta']), Patch(fc=COL['silv'], hatch='////', ec='#4E4E00'), Patch(fc=COL['antrop'], ec='#BBBBBB'),
                 Patch(fc=COL['app_conf'], ec='white'), Line2D([], [], color=COL['app_lim'], lw=0.9, ls='--'), Line2D([], [], color=COL['fbds'], lw=1.6)],
                [t('lim_g2').format(ha=fmt(d.g2['area_ha']), alq=fmt(d.g2['alqueires_paulistas'], 1)), t('lim_g1').format(ha=fmt(d.g1['area_ha'])), t('fora'),
                 t('cl_flor').format(a=fmt(v2['floresta_nativa_car_ha']), b='').replace('G1 ', '').replace(' · G2  ha', ''),
                 t('cl_silv').format(a=fmt(v2['silvicultura_ha']), b='').replace('G1 ', '').replace(' · G2  ha', ''),
                 t('cl_antr').format(a=fmt(v2['area_agricola_car_ha']), b='').replace('G1 ', '').replace(' · G2  ha', ''),
                 ('APP conforme (vegetação nativa) — %s ha' if LANG == 'pt' else 'APP conforme (vegetación nativa) — %s ha') % fmt(a2['com_vegetacao_nativa_ha']),
                 m4.T['app_lim'][LANG].format(ha=fmt(a2['exigida_ha'])), m4.T['curso'][LANG]])
    M.leg_texto(t('v06_kpi').format(x=fmt(r2['exigida_ha']), e=fmt(r2['existente_com_app_art15_ha'])), bold=True, color=AZUL, fs=M.fs + 1.0)
    mn = r2['monte_necessario_para_estar_na_lei']
    for s in t('v06_txt'):
        M.leg_texto(s.format(x=fmt(mn['rl_20pct_ha']), app=fmt(mn['app_propria_ha']), e=fmt(mn['hoje_imagem_mostra_ha']), d=fmt(mn['falta_com_art15_ha']),
                             m=fmt(d.g2['arroios']['lista'][0]['comprimento_dentro_m'], 0)))
    M.notas()
    return M


def guardar(M, nome):
    out_dir = os.path.join(MAPAS_V2, '' if LANG == 'pt' else 'ES')
    os.makedirs(out_dir, exist_ok=True)
    ruta = os.path.join(out_dir, nome + '.png')
    M.fig.savefig(ruta, dpi=DPI, facecolor='white')
    plt.close(M.fig)
    log('  -> %s' % ruta)


def main():
    global LANG
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='pt', choices=['pt', 'es'])
    ap.add_argument('--solo', default='')
    a = ap.parse_args()
    LANG = a.lang
    m4.LANG = LANG
    log('=' * 78); log('an_08_mapas_interior — lang=%s' % LANG); log('=' * 78)
    d = DadosV2()
    quiere = set(a.solo.split(',')) if a.solo else None
    tareas = [('V01_vegetacao_nativa_interior', V01), ('V02_hidrografia_interior', V02), ('V03_app_mata_ciliar_interior', V03),
              ('V04_reserva_legal_interior', V04), ('V05_mapa_car_interior', V05), ('V06_gleba2_detalhe', V06)]
    for nome, fn in tareas:
        if quiere and nome.split('_')[0] not in quiere:
            continue
        guardar(fn(d), nome)
    log('an_08 listo')


if __name__ == '__main__':
    main()
