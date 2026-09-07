# -*- coding: utf-8 -*-
"""dron_05_mapas_v5.py — mapas para o produtor (pt-BR), versão 5: DOIS IMÓVEIS SEPARADOS, só drone.

    python dron_05_mapas_v5.py [--solo SA1,AL2]

Saída: 06_DRONE_POR_IMOVEL/mapas/SA1..SA5, AL1..AL2 (PNG 250 dpi).

Regras (cliente 2026-09-06):
  * fundo = SOMENTE a ortofoto do drone recortada pelo polígono do imóvel (fora do polígono: cinza liso);
  * onde o drone não cobriu: hachurado "sem foto do drone: não avaliado" (nunca satélite);
  * nada se soma entre os dois imóveis;
  * NENHUM número é recalculado aqui: tudo sai de resultados_v5.json (por imóvel). As únicas geometrias
    derivadas são de DESENHO: o contorno da faixa de 20 m (união dos polígonos do PRA já calculados) e a
    faixa "sugestão de onde plantar" (buffer da mata existente até somar o déficit que falta) — a faixa é
    uma sugestão de localização, não uma cifra do relatório;
  * comprimento dos arroios = eixo oficial (mapa do governo) recortado pelo polígono (medição direta).
"""
import argparse
import os
import sys
import textwrap

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dron_00_comun import (SALIDA_RAIZ, R, imoveis, PONTA_NORTE, OFICIAL, ORTHO_SRC, CRS_METRICO,   # noqa: E402
                           leer_json, log, HOY)
import an_04_mapas as m4                                                                       # noqa: E402
from an_04_mapas import Mapa, COL, AZUL, TEAL, LIMA, GRIS, fmt, fmt_utm, poly_patches, DPI    # noqa: E402
from an_08_mapas_interior import patch_agujeros, FORA                                          # noqa: E402

import matplotlib                                   # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402
from matplotlib.patches import Patch               # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator   # noqa: E402
import geopandas as gpd                            # noqa: E402
import rasterio                                    # noqa: E402
from rasterio import features                      # noqa: E402
from rasterio.enums import Resampling              # noqa: E402
from rasterio.windows import from_bounds           # noqa: E402
from shapely.geometry import box, Point            # noqa: E402
from shapely.ops import unary_union                # noqa: E402

OUT = os.path.join(SALIDA_RAIZ, 'mapas')
DATA_DOC = '07/09/2026'
VERDE = '#2E7D32'; VERDE_CL = '#8BC34A'; VERM = '#D32F2F'; AZ = '#1E88E5'; AZ_ESC = '#0D47A1'; LAR = '#F59E0B'
ROXO = '#7E22CE'; SEMCOB = '#D9D9D9'; NASC = '#FF6F00'; PONTA = '#B91C1C'; AMARELO = COL['prop']
FONTE_A = 'Fundo: foto de drone de 22/05/2026 recortada pelo contorno do imóvel (fora: cinza)'
FONTE_B = 'Arroios e nascente: mapa oficial do governo · Não é laudo: o IAT valida.'
m4.T['marca'] = {'pt': 'Pixadvisor Agricultura de Precisão · Eng. Agr. Nilton Camargo · %s' % DATA_DOC, 'es': ''}
m4.T['fonte_s2'] = {'pt': FONTE_A, 'es': FONTE_A}
m4.T['notas'] = {'pt': FONTE_B, 'es': FONTE_B}
m4.LANG = 'pt'


# ------------------------------------------------------------------ dados ----
class D5:
    def __init__(self):
        self.res = leer_json(os.path.join(SALIDA_RAIZ, 'resultados_v5.json'))
        self.sa = self.res['santo_antonio']; self.al = self.res['seis_alqueires']
        im = imoveis()
        self.SA = im['santo_antonio']; self.AL = im['seis_alqueires']; self.PN = im[PONTA_NORTE]
        s = 'santo_antonio'
        rd = lambda n: gpd.read_file(R(s, n))
        self.app = rd('app_v5_santo_antonio.geojson')
        self.car5 = rd('mapa_uso_car_v5_santo_antonio.geojson')
        self.rl = rd('rl_vegetacao_computavel_v5_santo_antonio.geojson')
        self.agua = rd('agua_santo_antonio_2026-05-22.geojson')
        self.cob = rd('cobertura_drone_santo_antonio.geojson')
        self.cardec = rd('car_declarado_dentro_santo_antonio_2026-09-06.geojson')
        self.vn = rd('vegetacao_nativa_santo_antonio.geojson')
        self.uso = rd('uso_solo_santo_antonio.geojson')
        self.cob_al = gpd.read_file(R('seis_alqueires', 'cobertura_drone_seis_alqueires.geojson'))
        # água (drone 22/05/2026)
        ag = self.agua
        self.represa = ag[ag.corpo == 'represa_principal'].geometry.iloc[0]
        self.acude = ag[ag.corpo == 'acude_cabeceira_arroio2'].geometry.iloc[0]
        self.lagoas = list(ag[ag.corpo.isin(['lagoa_01', 'lagoa_02'])].geometry)
        self.sem_cob = unary_union(self.cob[self.cob.cobertura == 'sem_ortofoto'].geometry)
        # eixo oficial dos arroios (mapa do governo), recortado ao polígono do imóvel
        hid = gpd.read_file(OFICIAL['hidro']); hid = hid[hid.fonte == 'FBDS']
        ids = {1: ['647524'], 2: ['647525'], 3: ['617192', '647547']}       # norte / central / sul (Ribeirão do Salto)
        self.arr = {}
        for n, lst in ids.items():
            g = unary_union(hid[hid.id_fonte.astype(str).isin(lst)].geometry).intersection(self.SA)
            self.arr[n] = g
            log('  Arroio %d (oficial %s): %.1f m dentro do polígono' % (n, '+'.join(lst), g.length))
        nas = gpd.read_file(OFICIAL['nascentes'])
        self.nasc = nas[nas.id_fonte.astype(str) == '306158'].geometry.iloc[0]
        self.nasc_acude_m = self.nasc.distance(self.acude)
        log('  nascente 306158: %.1f m do açude' % self.nasc_acude_m)
        # APP legal (30 m / 50 m) por situação
        A = self.app[self.app.variante == 'legal_30m_nascente_50m']
        self.app_conf = unary_union(A[A.situacao == 'conforme'].geometry)
        self.app_agua = unary_union(A[A.situacao == 'agua'].geometry)
        self.app_rec = unary_union(A[A.situacao == 'recompor'].geometry)
        self.app_sem = unary_union(A[A.situacao.str.startswith('sem cobertura')].geometry)
        self.app_all = unary_union(A.geometry)
        self.pra_all = unary_union(self.app[self.app.variante == 'pra_20m_nascente_15m'].geometry)
        self.mata_rl = unary_union(self.rl.geometry)
        self._sugestao = None

    def sugestao_rl(self):
        """Faixa SUGERIDA para plantar a Reserva Legal que falta, sobre o PASTO junto à mata existente (só desenho).
        Área-alvo = déficit da RL - APP a recompor (a APP recomposta também conta, art. 15: observação do JSON).
        Só contam manchas >= 0,25 ha (evita migalhas)."""
        if self._sugestao is not None:
            return self._sugestao
        k = self.sa['kpi']
        alvo = k['rl_deficit_ha'] - k['app_a_recompor_ha']
        con = unary_union(self.uso[self.uso.classe == 'construcoes'].geometry)
        agua = unary_union(self.agua[self.agua.tipo == 'agua_aberta'].geometry)
        pasto = unary_union(self.uso[self.uso.classe == 'herbacea_pasto'].geometry).simplify(1).buffer(0)
        livre = self.SA.difference(self.mata_rl).difference(self.app_all).difference(agua).difference(self.sem_cob).difference(con)
        livre = livre.simplify(1).buffer(0).intersection(pasto).buffer(0)
        base = unary_union(self.vn[self.vn.area_dentro_imovel_ha >= 0.5].geometry)
        base = base.simplify(1).buffer(0)

        def faixa(w):
            r = base.buffer(w).buffer(-0.6 * w).buffer(0.6 * w).intersection(livre).buffer(0)
            partes = [p for p in (r.geoms if hasattr(r, 'geoms') else [r]) if p.area >= 2500]
            return unary_union(partes) if partes else r.buffer(0)
        lo, hi = 0.0, 200.0
        for _ in range(14):
            w = (lo + hi) / 2
            if faixa(w).area / 1e4 < alvo:
                lo = w
            else:
                hi = w
        ring = faixa(hi)
        self._sugestao = (ring, hi, ring.area / 1e4, alvo)
        log('  sugestão RL: faixa de %.0f m sobre o pasto junto à mata (>= 0,5 ha): %.2f ha (alvo %.2f = %.2f - %.2f)' % (hi, ring.area / 1e4, alvo, k['rl_deficit_ha'], k['app_a_recompor_ha']))
        return self._sugestao


# ------------------------------------------------------------------ base -----
def rotulo(ax, x, y, txt, fc, dx=0, dy=0, fs=8.0, color='white', ec='white', ha='center', va='center', lw_seta=0.9):
    kw = dict(fontsize=fs, ha=ha, va=va, zorder=45, color=color, fontweight='bold', linespacing=1.15,
              bbox=dict(boxstyle='round,pad=0.3', fc=fc, ec=ec, lw=0.7, alpha=0.97))
    if dx or dy:
        ax.annotate(txt, xy=(x, y), xytext=(x + dx, y + dy),
                    arrowprops=dict(arrowstyle='-', lw=lw_seta, color=(fc if fc != 'white' else color), shrinkA=0, shrinkB=1), **kw)
    else:
        ax.text(x, y, txt, **kw)


def extent_de(geom, mx, my):
    x0, y0, x1, y1 = geom.bounds
    return (x0 - mx, y0 - my, x1 + mx, y1 + my)


def borda_x(geom, y, lado, afast=125):
    """x do rótulo na margem cinza: borda do polígono na altura y, afastada `afast` m."""
    from shapely.geometry import LineString
    x0, y0, x1, y1 = geom.bounds
    y = min(max(y, y0 + 1), y1 - 1)
    sec = geom.intersection(LineString([(x0 - 1, y), (x1 + 1, y)]))
    if sec.is_empty:
        return (x0 - afast) if lado == 'l' else (x1 + afast)
    bx0, _, bx1, _ = sec.bounds
    return (bx0 - afast) if lado == 'l' else (bx1 + afast)


class Rotulador:
    """Coloca rótulos nas margens cinza (esquerda/direita), sem sobreposição vertical (separação mínima)."""

    def __init__(self, ax, geom, extent, sep=230):
        self.ax, self.geom, self.ext, self.sep = ax, geom, extent, sep
        self.usados = {'l': [], 'r': []}

    def put(self, alvo, txt, color, lado=None, y=None, fs=7.4, fc='white', ec=None, afast=125):
        c = alvo.representative_point() if hasattr(alvo, 'representative_point') and alvo.geom_type != 'Point' else alvo
        gx0, gy0, gx1, gy1 = self.geom.bounds
        if lado is None:
            lado = 'l' if (c.x - borda_x(self.geom, c.y, 'l', 0)) < (borda_x(self.geom, c.y, 'r', 0) - c.x) else 'r'
        y = c.y if y is None else y
        y = min(max(y, self.ext[1] + 150), self.ext[3] - 150)
        k = 0; y0 = y
        while any(abs(y - u) < self.sep for u in self.usados[lado]) and k < 12:
            k += 1
            y = y0 + self.sep * ((k + 1) // 2) * (1 if k % 2 else -1)
            y = min(max(y, self.ext[1] + 150), self.ext[3] - 150)
        self.usados[lado].append(y)
        x = borda_x(self.geom, y, lado, afast)
        rotulo(self.ax, c.x, c.y, txt, fc, dx=x - c.x, dy=y - c.y, fs=fs, color=color, ec=ec or color)
        return x, y


def fondo(M, geom, ruta_orto, gain=1.0):
    """Ortofoto RGBA do imóvel; alpha 0 dentro do polígono = sem foto (cinza claro); fora do polígono = FORA."""
    x0, y0, x1, y1 = M.extent
    with rasterio.open(ruta_orto) as ds:
        bx0, by0, bx1, by1 = max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top)
        win = from_bounds(bx0, by0, bx1, by1, ds.transform)
        img = ds.read(window=win)
        tr = ds.window_transform(win)
    h, w = img.shape[1], img.shape[2]
    ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
    rgb = np.clip(np.moveaxis(img[:3], 0, -1).astype(np.float32) / 255.0 * gain, 0, 1)
    alpha = img[3] > 0
    sem = np.array(matplotlib.colors.to_rgb(SEMCOB), dtype=np.float32)
    rgb = np.where(alpha[..., None], rgb, sem)
    M.ax.imshow(rgb, extent=ex, interpolation='nearest', zorder=1)
    M.ax.set_facecolor(FORA)
    ext_poly = box(x0 - 50, y0 - 50, x1 + 50, y1 + 50).difference(geom)
    patch_agujeros(M.ax, ext_poly, fc=FORA, ec='none', lw=0, zorder=25)


def contorno(ax, geom, cor='black', lw=0.8, zorder=30, ls='-'):
    # Pedido do cliente (07/09/2026): perimetro FINO e PRETO, sem halo.
    gs = gpd.GeoSeries([geom], crs=CRS_METRICO).boundary
    gs.plot(ax=ax, color='black', lw=0.8, zorder=zorder + 1, ls=ls)


def hachura_sem_cob(ax, geom, zorder=9):
    if geom is None or geom.is_empty:
        return
    poly_patches(ax, [geom], fc=SEMCOB, ec='#777777', hatch='////', lw=0.4, zorder=zorder)


def base_sa(d, titulo, sub, leg_min_cm=6.0):
    M = Mapa('V', titulo, sub, extent_de(d.SA, 250, 130), leg_min_cm=leg_min_cm)
    M.fs = 9.2
    M.fig.texts[0].set_fontsize(14.0); M.fig.texts[1].set_fontsize(7.6)
    fondo(M, d.SA, R('santo_antonio', 'ortofoto_rgba_0_25m.tif'))
    return M


def arroios(M, d, lw=1.6, branco=True):
    for n, g in d.arr.items():
        if branco:
            gpd.GeoSeries([g], crs=CRS_METRICO).plot(ax=M.ax, color='white', lw=lw + 1.6, zorder=10)
        gpd.GeoSeries([g], crs=CRS_METRICO).plot(ax=M.ax, color=COL['fbds'], lw=lw, zorder=11)


def nomes_arroios(Rt, d, fs=7.8):
    """Rótulos dos 3 arroios com os metros dentro do imóvel, na margem cinza da esquerda."""
    pos = {1: (0.35, 7403905), 2: (0.45, 7403330), 3: (0.30, 7401500)}
    for n, g in d.arr.items():
        f, yl = pos[n]
        c = g.interpolate(f, normalized=True) if g.geom_type == 'LineString' else min(g.geoms, key=lambda p: -p.length).interpolate(f, normalized=True)
        Rt.put(c, ('Arroio %d' + chr(10) + '%s m') % (n, fmt(g.length, 0)), 'white', lado='l', y=yl, fs=fs, fc=COL['fbds'])


def leg_imovel_sa(d):
    return ([Line2D([], [], color='black', lw=1.0), Patch(fc=FORA, ec='#BBBBBB'), Patch(fc=SEMCOB, ec='#777777', hatch='////')],
            ['Fazenda Santo Antônio (%s ha)' % fmt(d.sa['area_poligono_ha']), 'Fora da fazenda', 'Sem foto do drone: não avaliado (%s ha)' % fmt(d.sa['kpi']['sem_cobertura_ha'])])


# ------------------------------------------------------------------ SA1 ------
def SA1(d):
    k = d.sa['kpi']; v = d.sa['vegetacao_ha']; ag = d.sa['agua']
    M = base_sa(d, 'SA1 · A fazenda vista pelo drone', 'Fazenda Santo Antônio · %s ha · drone de 22/05/2026 · 3 arroios, nascente, represa e açude' % fmt(k['area_poligono_ha']))
    ax = M.ax; Rt = Rotulador(ax, d.SA, M.extent)
    hachura_sem_cob(ax, d.sem_cob)
    poly_patches(ax, [d.represa], fc=AZ, ec='white', lw=0.6, zorder=8)
    poly_patches(ax, [d.acude], fc=AZ_ESC, ec='white', lw=0.6, zorder=8)
    poly_patches(ax, d.lagoas, fc=AZ, ec='white', lw=0.5, zorder=8)
    arroios(M, d)
    nomes_arroios(Rt, d)
    ax.scatter([d.nasc.x], [d.nasc.y], s=75, marker='o', c=NASC, edgecolors='white', linewidths=1.2, zorder=16)
    Rt.put(d.nasc, 'Nascente', NASC, lado='r', y=7402840, fs=7.8)
    Rt.put(d.acude, 'Açude\n%s ha' % fmt(ag['acude_cabeceira_ha'], 3), AZ_ESC, lado='r', y=7403090, fs=7.6)
    Rt.put(unary_union(d.lagoas), '2 lagoas\n%s ha' % fmt(ag['lagoas_menores_ha']), AZ_ESC, lado='r', y=7403340, fs=7.4, ec=AZ)
    Rt.put(d.represa, 'Represa\n%s ha' % fmt(ag['represa_ha']), AZ_ESC, lado='r', y=7401760, fs=7.8, ec=AZ)
    if not d.sem_cob.is_empty:
        Rt.put(d.sem_cob, 'Sem foto\ndo drone', '#555555', lado='l', y=7404120, fs=7.2, ec='#777777')
    ax.text(534830, 7402380, 'Fazenda\nSanto Antônio\n%s ha' % fmt(k['area_poligono_ha']), fontsize=8.0, fontweight='bold', color='black', ha='center', va='center', zorder=40,
            bbox=dict(boxstyle='round,pad=0.3', fc=AMARELO, ec='black', lw=0.6, alpha=0.95))
    contorno(ax, d.SA); M.grilla(); M.norte_escala()
    h, l = leg_imovel_sa(d)
    M.leg_titulo('O que tem dentro da fazenda')
    M.leg_items(h + [Line2D([], [], color=COL['fbds'], lw=2.2), Line2D([], [], marker='o', color='none', markerfacecolor=NASC, markeredgecolor='white', ms=8),
                     Patch(fc=AZ, ec='white'), Patch(fc=AZ_ESC, ec='white')],
                l + ['Arroio (córrego): linha do mapa oficial, com os metros dentro da fazenda', 'Nascente (mapa oficial): água a %s m; conferir em campo' % fmt(d.nasc_acude_m, 0),
                     'Represa: %s ha de água em 22/05/2026' % fmt(ag['represa_ha']), 'Açude na cabeceira do Arroio 2: %s ha' % fmt(ag['acude_cabeceira_ha'], 3)])
    M.leg_espacio(0.15)
    rows = [['Arroio', 'Metros dentro', 'Largura']]
    for n in (1, 2, 3):
        rows.append(['Arroio %d' % n, fmt(d.arr[n].length, 0), 'até 10 m*'])
    M.leg_tabla(rows, col_w=[0.34, 0.36, 0.30])
    M.leg_texto('* Largura provável, sem medição: as árvores escondem o leito. Medir com trena e GPS.', fs=8.0)
    M.leg_espacio(0.1)
    rows = [['O que existe', 'ha'], ['Mata (árvores)', fmt(v['arborea_ha'])], ['Arbustos em regeneração', fmt(v['arbustiva_ha'])], ['Pasto', fmt(v['pasto_ha'])],
            ['Lavoura e solo', fmt(v['lavoura_solo_ha'])], ['Água', fmt(v['agua_ha'])], ['Sem foto do drone', fmt(v['sem_cobertura_drone'])]]
    M.leg_tabla(rows, col_w=[0.72, 0.28])
    M.leg_texto('O drone fotografou %s dos %s ha. A faixa sem foto fica "não avaliada": nada é preenchido com satélite.' % (
        fmt(k['cobertura_ortofoto_ha']), fmt(k['area_poligono_ha'])), fs=8.4, bold=True, color=AZUL)
    M.notas()
    return M


# ------------------------------------------------------------------ SA2 ------
def SA2(d):
    A = d.sa['app']['legal_30m_nascente_50m']; P = d.sa['app']['pra_20m_nascente_15m']; Rz = d.sa['app']['legal_mais_faixa_reservatorio_30m']; ag = d.sa['agua']
    M = base_sa(d, 'SA2 · Mata na beira dos rios (APP)', 'APP = faixa de mata que a lei exige: 30 m de cada lado dos arroios e 50 m em volta da nascente')
    ax = M.ax; Rt = Rotulador(ax, d.SA, M.extent)
    hachura_sem_cob(ax, d.sem_cob, zorder=5)
    poly_patches(ax, [d.app_conf], fc=VERDE, ec='none', zorder=6)
    poly_patches(ax, [d.app_agua], fc=AZ, ec='none', zorder=6)
    poly_patches(ax, [d.app_rec], fc=VERM, ec='none', zorder=7)
    poly_patches(ax, [d.app_sem], fc='#9E9E9E', ec='none', zorder=6)
    poly_patches(ax, [d.represa], fc=AZ + '99', ec=AZ_ESC, lw=0.8, zorder=7)
    gpd.GeoSeries([d.app_all], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=0.7, ls='--', zorder=12)
    gpd.GeoSeries([d.pra_all], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['faixa20'], lw=0.7, zorder=13)
    arroios(M, d, lw=0.8, branco=False)
    ax.scatter([d.nasc.x], [d.nasc.y], s=55, marker='o', c=NASC, edgecolors='white', linewidths=1.0, zorder=16)
    Rt.put(d.nasc, 'Nascente:\n50 m em volta', NASC, lado='r', fs=7.4)
    Rt.put(d.represa, 'Represa %s ha:\nfaixa a definir\npelo IAT' % fmt(ag['represa_ha']), AZ_ESC, lado='r', fs=7.2, ec=AZ)
    partes = sorted([p for p in (d.app_rec.geoms if hasattr(d.app_rec, 'geoms') else [d.app_rec])], key=lambda p: -p.area)
    for p in partes[:4]:
        Rt.put(p, 'falta\nplantar', VERM, fs=7.6)
    contorno(ax, d.SA, lw=1.6); M.grilla(); M.norte_escala()
    h, l = leg_imovel_sa(d)
    M.leg_titulo('Cores do mapa')
    M.leg_items(h[:2] + [Patch(fc=VERDE), Patch(fc=AZ), Patch(fc=VERM), Patch(fc='#9E9E9E'), Line2D([], [], color='black', lw=1.0, ls='--'), Line2D([], [], color=COL['faixa20'], lw=1.2),
                         Line2D([], [], marker='o', color='none', markerfacecolor=NASC, markeredgecolor='white', ms=8)],
                l[:2] + ['Já tem mata (%s ha)' % fmt(A['com_vegetacao_nativa_ha']), 'Água (%s ha)' % fmt(A['agua_ha']), 'Falta plantar (%s ha)' % fmt(A['a_recompor_ha']),
                         'Sem foto do drone: não avaliado (%s ha)' % fmt(A['sem_cobertura_drone_nao_avaliado_ha']),
                         'Faixa que a lei pede: 30 m + 50 m', 'Faixa de 20 m do PRA', 'Nascente (mapa oficial)'])
    M.leg_espacio(0.15)
    rows = [['Beira dos rios (APP)', 'ha'], ['A lei pede (30 m + 50 m)', fmt(A['exigida_ha'])], ['Já tem mata', fmt(A['com_vegetacao_nativa_ha'])], ['É água', fmt(A['agua_ha'])],
            ['Não avaliado (sem foto)', fmt(A['sem_cobertura_drone_nao_avaliado_ha'])], ['Falta plantar', fmt(A['a_recompor_ha'])], ['Falta, se entrar no PRA', fmt(P['a_recompor_ha'])]]
    M.leg_tabla(rows, col_w=[0.70, 0.30], bold_last=True)
    M.leg_texto('PRA = programa do Paraná para quem regulariza: a faixa cai para 20 m nos arroios e 15 m na nascente (%s ha no total). Depende da data do CAR.' % fmt(P['exigida_ha']), fs=8.0)
    M.leg_espacio(0.1)
    M.leg_texto('Represa: %s ha de água (mais de 1 ha). A faixa em volta dela é o IAT que define. Se pedir 30 m, a faixa exigida sobe para %s ha e o que falta, para %s ha.' % (
        fmt(ag['represa_ha']), fmt(Rz['exigida_ha']), fmt(Rz['a_recompor_ha'])), fs=8.0)
    M.leg_espacio(0.1)
    M.leg_texto('Falta plantar %s ha de mata na beira dos rios (%s ha se entrar no PRA).' % (fmt(A['a_recompor_ha']), fmt(P['a_recompor_ha'])), fs=8.4, bold=True, color=AZUL)
    M.notas()
    return M


# ------------------------------------------------------------------ SA3 ------
def SA3(d):
    RL = d.sa['reserva_legal']; k = d.sa['kpi']; car = d.sa['cruzamento_car']['declarado_no_car_inteiro']
    ring, w_m, ring_ha, alvo = d.sugestao_rl()
    M = base_sa(d, 'SA3 · Reserva Legal: o que conta e o que falta', 'Reserva Legal = 20%% da fazenda com mata nativa: %s ha de %s ha' % (fmt(RL['exigida_ha']), fmt(k['area_poligono_ha'])))
    ax = M.ax; Rt = Rotulador(ax, d.SA, M.extent)
    hachura_sem_cob(ax, d.sem_cob, zorder=5)
    poly_patches(ax, [d.mata_rl], fc=VERDE, ec='none', zorder=6)
    poly_patches(ax, [d.app_rec], fc=VERM, ec='none', zorder=7)
    poly_patches(ax, [ring], fc=LAR + 'CC', ec='#92400E', hatch='\\\\', lw=0.5, zorder=7)
    arroios(M, d, lw=0.8, branco=False)
    big = max((p for p in (d.mata_rl.geoms if hasattr(d.mata_rl, 'geoms') else [d.mata_rl])), key=lambda p: p.area)
    Rt.put(big, 'Mata que\nconta', VERDE, lado='l', fs=7.8)
    partes = sorted((p for p in (ring.geoms if hasattr(ring, 'geoms') else [ring])), key=lambda p: -p.area)
    for p in partes[:3]:
        Rt.put(p, 'Sugestão:\nplantar aqui,\njunto à mata', '#92400E', fs=7.2, ec=LAR)
    rec = sorted((p for p in (d.app_rec.geoms if hasattr(d.app_rec, 'geoms') else [d.app_rec])), key=lambda p: -p.area)
    for p in rec[:2]:
        Rt.put(p, 'Beira do rio\na plantar:\ntambém conta', VERM, fs=7.0)
    contorno(ax, d.SA, lw=1.6); M.grilla(); M.norte_escala()
    h, l = leg_imovel_sa(d)
    M.leg_titulo('Cores do mapa')
    M.leg_items(h + [Patch(fc=VERDE), Patch(fc=VERM), Patch(fc=LAR, hatch='\\\\', ec='#92400E')],
                l + ['Mata que conta hoje (%s ha), dentro e fora da beira dos rios' % fmt(RL['vegetacao_computavel_ha']),
                     'Beira dos rios a plantar (%s ha): plantada, também conta' % fmt(k['app_a_recompor_ha']),
                     'Sugestão de onde plantar o resto (%s ha): pasto junto à mata, faixa de uns %s m' % (fmt(ring_ha), fmt(w_m, 0))])
    M.leg_espacio(0.15)
    rows = [['Reserva Legal (20%)', 'ha'], ['A lei pede', fmt(RL['exigida_ha'])], ['Mata que conta hoje', fmt(RL['vegetacao_computavel_ha'])], ['Falta', fmt(RL['deficit_ha'])],
            ['Atendido hoje', '%s %%' % fmt(RL['pct_atendido'], 1)], ['O CAR declara hoje', fmt(car['reserva_legal_ha'])]]
    M.leg_tabla(rows, col_w=[0.70, 0.30])
    M.leg_texto('Árvores isoladas com menos de 0,05 ha (%s ha) não contam. A faixa sem foto (%s ha) não soma nem desconta.' % (
        fmt(RL['medido_drone']['arvores_isoladas_nao_computadas_ha']), fmt(RL['medido_drone']['sem_cobertura_drone_nao_avaliado_ha'])), fs=8.0)
    M.leg_espacio(0.1)
    M.leg_texto('A faixa laranja é só uma ideia de lugar: o desenho final é definido com o IAT. Três caminhos, que se combinam: plantar, deixar regenerar ou compensar em outra área.', fs=8.0)
    M.leg_espacio(0.1)
    M.leg_texto('Faltam %s ha de Reserva Legal (%s %% já atendido).' % (fmt(RL['deficit_ha']), fmt(RL['pct_atendido'], 1)), fs=8.4, bold=True, color=AZUL)
    M.notas()
    return M


# ------------------------------------------------------------------ SA4 ------
STATUS_PT = {'Aguardando analise': 'Aguardando análise', 'Analisado, aguardando atendimento a notificacao': 'Analisado, aguardando atendimento à notificação'}


def SA4(d):
    cz = d.sa['cruzamento_car']; dec = cz['declarado_no_car_inteiro']; med = cz['medido_drone_v5']; st = cz['status_atual']; RL = d.sa['reserva_legal']
    status = STATUS_PT.get(st['des_condic'], st['des_condic'])
    cd = d.cardec
    g_rl = unary_union(cd[cd.cod_tema == 'ARL_AVERBADA'].geometry).intersection(d.SA)
    g_res = unary_union(cd[cd.cod_tema == 'RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO'].geometry).intersection(d.SA)
    g_veg = unary_union(cd[cd.cod_tema == 'VEGETACAO_NATIVA'].geometry).intersection(d.SA)
    M = base_sa(d, 'SA4 · O que o CAR declara e o que o drone mostra', 'CAR = cadastro ambiental da fazenda no governo · situação em 06/09/2026: "%s"' % status)
    M.fig.texts[0].set_fontsize(12.6)
    ax = M.ax; Rt = Rotulador(ax, d.SA, M.extent)
    hachura_sem_cob(ax, d.sem_cob, zorder=5)
    poly_patches(ax, [unary_union(d.vn.geometry)], fc=VERDE_CL + 'B3', ec='none', zorder=6)
    poly_patches(ax, [d.represa, d.acude] + d.lagoas, fc=AZ + 'B3', ec='none', zorder=6)
    poly_patches(ax, [g_veg], fc='none', ec='#1B5E20', hatch='////', lw=1.2, zorder=8)
    poly_patches(ax, [g_res], fc='none', ec=AZ_ESC, hatch='xx', lw=1.2, zorder=8)
    poly_patches(ax, [g_rl], fc=ROXO + '55', ec=ROXO, hatch='\\\\', lw=1.4, zorder=9)
    arroios(M, d, lw=0.8, branco=False)
    big = max((p for p in (d.mata_rl.geoms if hasattr(d.mata_rl, 'geoms') else [d.mata_rl])), key=lambda p: p.area)
    Rt.put(big, 'Drone: mata\n%s ha' % fmt(med['vegetacao_nativa_ha']), VERDE, lado='l', fs=7.4)
    rlp = sorted((p for p in (g_rl.geoms if hasattr(g_rl, 'geoms') else [g_rl])), key=lambda p: -p.area)
    Rt.put(rlp[0], 'CAR: Reserva\nLegal %s ha' % fmt(dec['reserva_legal_ha']), ROXO, lado='l', fs=7.4)
    vgp = sorted((p for p in (g_veg.geoms if hasattr(g_veg, 'geoms') else [g_veg])), key=lambda p: -p.area)
    Rt.put(vgp[0], 'CAR: mata\n%s ha' % fmt(dec['vegetacao_nativa_ha']), '#1B5E20', lado='r', fs=7.4)
    Rt.put(g_res, 'CAR: represa\n%s ha' % fmt(dec['reservatorios_geom_ha']), AZ_ESC, lado='r', fs=7.4)
    Rt.put(d.represa, 'Drone: água\n%s ha' % fmt(d.sa['agua']['represa_ha']), AZ_ESC, lado='l', y=7401450, fs=7.4, ec=AZ)
    contorno(ax, d.SA, lw=1.6); M.grilla(); M.norte_escala()
    h, l = leg_imovel_sa(d)
    M.leg_titulo('Cores do mapa')
    M.leg_items(h[:2] + [Patch(fc=VERDE_CL), Patch(fc=AZ), Patch(fc=ROXO + '55', ec=ROXO, hatch='\\\\'), Patch(fc='none', ec='#1B5E20', hatch='////'), Patch(fc='none', ec=AZ_ESC, hatch='xx')],
                l[:2] + ['Mata vista pelo drone (%s ha)' % fmt(med['vegetacao_nativa_ha']), 'Água vista pelo drone (%s ha)' % fmt(med['reservatorios_agua_aberta_ha']),
                         'Reserva Legal que o CAR declara (%s ha)' % fmt(dec['reserva_legal_ha']), 'Mata que o CAR declara (%s ha)' % fmt(dec['vegetacao_nativa_ha']),
                         'Represa que o CAR declara (%s ha)' % fmt(dec['reservatorios_geom_ha'])])
    M.leg_espacio(0.15)
    rows = [['Tema (ha)', 'CAR', 'Drone'],
            ['Área do imóvel', fmt(dec['area_imovel_ha']), fmt(med['area_poligono_ha'])],
            ['Reserva Legal', fmt(dec['reserva_legal_ha']), '%s*' % fmt(RL['exigida_ha'])],
            ['Mata nativa', fmt(dec['vegetacao_nativa_ha']), fmt(med['vegetacao_nativa_ha'])],
            ['Beira dos rios', fmt(dec['app_total_ha']), '%s*' % fmt(med['app_exigida_30m_50m_ha'])],
            ['Represa e lagoas', fmt(dec['reservatorios_geom_ha']), fmt(med['reservatorios_agua_aberta_ha'])],
            ['Área de uso', fmt(cz['declarado_DENTRO_do_poligono_deste_imovel_ha']['area_consolidada']), fmt(med['area_antropizada_pasto_lavoura_construcoes_ha'])]]
    M.leg_tabla(rows, col_w=[0.46, 0.25, 0.29])
    M.leg_texto('* o que a lei pede (o drone mede %s ha de mata que conta e %s ha de beira com mata).' % (fmt(RL['vegetacao_computavel_ha']), fmt(med['app_com_vegetacao_ha'])), fs=7.8)
    M.leg_espacio(0.08)
    M.leg_texto('CAR em 06/09/2026: "%s" (dados publicados pelo governo: SICAR de 25/01/2024). Declara pouca mata e pouca Reserva Legal: cabe retificar.' % status, fs=8.0)
    M.leg_espacio(0.08)
    o = d.sa['outorga_sigarh']
    M.leg_texto('Outorga da represa (licença de uso da água) %s: "%s", vencida em 08/11/2025. Renovar.' % (o['nr_portaria'], o['status'].lower()), fs=8.0)
    M.leg_espacio(0.08)
    M.leg_texto('O CAR precisa ser corrigido com a mata real e a Reserva Legal exigida.', fs=8.4, bold=True, color=AZUL)
    M.notas()
    return M


# ------------------------------------------------------------------ SA5 ------
def fig_marca(titulo, sub, W=15.0, H=22.0):
    fig = plt.figure(figsize=(W / 2.54, H / 2.54))
    fig.text(1.45 / W, 1 - 0.45 / H, titulo, fontsize=14.0, fontweight='bold', color=AZUL, va='top')
    fig.text(1.45 / W, 1 - 1.05 / H, sub, fontsize=7.6, color='#444444', va='top')
    fig.add_artist(plt.Line2D([1.45 / W, 1 - 0.4 / W], [1 - 1.43 / H] * 2, color=TEAL, lw=1.4))
    fig.add_artist(plt.Line2D([1 - 3.5 / W, 1 - 0.4 / W], [1 - 1.43 / H] * 2, color=LIMA, lw=1.4))
    fig.text(1 - 0.4 / W, 0.22 / H, m4.T['marca']['pt'], fontsize=5.8, color='#666666', ha='right', va='bottom')
    return fig


def panel_axes(fig, W, H, l, b, w, h, extent):
    ax = fig.add_axes([l / W, b / H, w / W, h / H])
    x0, y0, x1, y1 = extent
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
    ax.tick_params(labelsize=4.6, length=1.5, pad=1)
    ax.xaxis.set_major_locator(MaxNLocator(4)); ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(FuncFormatter(fmt_utm)); ax.yaxis.set_major_formatter(FuncFormatter(fmt_utm))
    for lab in ax.get_yticklabels():
        lab.set_rotation(90); lab.set_va('center')
    for s in ax.spines.values():
        s.set_linewidth(0.6)
    return ax


def escala(ax, extent, bar_m, fs=5.5):
    x0, y0, x1, y1 = extent; dx, dy = x1 - x0, y1 - y0
    xs, ys = x0 + 0.05 * dx, y0 + 0.04 * dy; hb = 0.012 * dy
    for i in range(2):
        ax.add_patch(plt.Rectangle((xs + i * bar_m / 2, ys), bar_m / 2, hb, fc='white' if i else 'black', ec='black', lw=0.5, zorder=60))
    ax.text(xs + bar_m / 2, ys + hb * 1.5, '%s m' % fmt(bar_m, 0), ha='center', va='bottom', fontsize=fs, zorder=60, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.8))
    xn = x1 - 0.07 * dx
    ax.annotate('', xy=(xn, y1 - 0.04 * dy), xytext=(xn, y1 - 0.14 * dy), arrowprops=dict(facecolor='white', edgecolor='black', width=2, headwidth=6, headlength=5, lw=0.5), zorder=60)
    ax.text(xn, y1 - 0.15 * dy, 'N', ha='center', va='top', fontsize=fs + 0.5, fontweight='bold', zorder=60, bbox=dict(boxstyle='round,pad=0.1', fc='white', ec='none', alpha=0.85))


def orto_5cm(ax, extent, geom, max_px=2200):
    """Ortofoto original de 5 cm (voo ODM) por janela, recortada pelo polígono do imóvel (fora: cinza)."""
    x0, y0, x1, y1 = extent
    with rasterio.open(ORTHO_SRC) as ds:
        win = from_bounds(max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top), ds.transform)
        h, w = int(round(win.height)), int(round(win.width))
        f = max(1, int(np.ceil(max(h, w) / max_px)))
        img = ds.read(window=win, out_shape=(4, h // f, w // f), resampling=Resampling.average)
        tr = ds.window_transform(win)
    hh, ww = img.shape[1], img.shape[2]
    ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
    from rasterio.transform import Affine
    tr2 = tr * Affine.scale(w / ww, h / hh)
    mask = features.rasterize([(geom, 1)], out_shape=(hh, ww), transform=tr2, fill=0, dtype=np.uint8, all_touched=True)
    rgb = np.moveaxis(img[:3], 0, -1).astype(np.float32) / 255.0
    fora = np.array(matplotlib.colors.to_rgb(FORA), dtype=np.float32)
    rgb = np.where(((img[3] > 0) & (mask == 1))[..., None], rgb, fora)
    ax.imshow(rgb, extent=ex, interpolation='bilinear', zorder=1)
    ax.set_facecolor(FORA)
    return ex


def SA5(d):
    W, H = 15.0, 12.2
    ag = d.sa['agua']; o = d.sa['outorga_sigarh']
    fig = fig_marca('SA5 · Represa, açude e nascente de perto', 'Foto de drone de 22/05/2026 a 5 cm por pixel, recortada pelo contorno da fazenda', W, H)
    pw, ph = 6.1, 6.1; l1, l2 = 1.45, 1.45 + pw + 1.0; b1 = H - 1.85 - ph
    cap_fs = 7.0; cap_dy = 0.45
    # (a) represa
    x0, y0, x1, y1 = d.represa.bounds; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; hw = max(x1 - x0, y1 - y0) / 2 + 25
    ext = (cx - hw, cy - hw, cx + hw, cy + hw)
    ax = panel_axes(fig, W, H, l1, b1, pw, ph, ext); orto_5cm(ax, ext, d.SA)
    poly_patches(ax, [d.represa], fc=AZ + '44', ec=AZ, lw=1.6, zorder=8)
    gpd.GeoSeries([d.arr[3]], crs=CRS_METRICO).plot(ax=ax, color=COL['fbds'], lw=1.0, zorder=10)
    contorno(ax, d.SA, lw=1.2, zorder=20)
    escala(ax, ext, 50)
    ax.legend([Patch(fc=AZ + '44', ec=AZ), Line2D([], [], color=COL['fbds'], lw=1.0)], ['água: %s ha' % fmt(ag['represa_ha']), 'Arroio 3 (mapa oficial)'],
              loc='lower right', fontsize=6.5, frameon=True, framealpha=0.9, handlelength=1.5)
    fig.text(l1 / W, (b1 - cap_dy) / H, textwrap.fill('(a) Represa no Arroio 3 (Ribeirão do Salto): %s ha de água no dia do voo, maior que 1 ha. A faixa de mata em volta é definida pelo IAT. '
                                                        'A outorga (licença de uso da água) está "%s" e venceu em 08/11/2025: renovar.' % (fmt(ag['represa_ha']), o['status'].lower()), 46),
             fontsize=cap_fs, va='top', color=GRIS, linespacing=1.25)
    # (b) açude + nascente
    pts = [d.nasc] + [Point(c) for c in d.acude.exterior.coords]
    ux = [p.x for p in pts]; uy = [p.y for p in pts]
    cx, cy = (min(ux) + max(ux)) / 2, (min(uy) + max(uy)) / 2; hw = max(max(ux) - min(ux), max(uy) - min(uy)) / 2 + 28
    ext = (cx - hw, cy - hw, cx + hw, cy + hw)
    ax = panel_axes(fig, W, H, l2, b1, pw, ph, ext); orto_5cm(ax, ext, d.SA)
    poly_patches(ax, [d.acude], fc=AZ_ESC + '55', ec=AZ_ESC, lw=1.6, zorder=8)
    gpd.GeoSeries([d.arr[2]], crs=CRS_METRICO).plot(ax=ax, color=COL['fbds'], lw=1.0, zorder=10)
    ax.scatter([d.nasc.x], [d.nasc.y], s=70, marker='o', c=NASC, edgecolors='white', linewidths=1.2, zorder=16)
    pa = d.acude.exterior.interpolate(d.acude.exterior.project(d.nasc))
    ax.plot([d.nasc.x, pa.x], [d.nasc.y, pa.y], color='white', lw=1.0, ls='--', zorder=15)
    ax.text((d.nasc.x + pa.x) / 2 + 6, (d.nasc.y + pa.y) / 2 + 2, '%s m' % fmt(d.nasc_acude_m, 0), fontsize=7, color='white', fontweight='bold', zorder=17,
            bbox=dict(boxstyle='round,pad=0.15', fc='black', ec='none', alpha=0.55))
    escala(ax, ext, 25)
    ax.legend([Patch(fc=AZ_ESC + '55', ec=AZ_ESC), Line2D([], [], marker='o', color='none', markerfacecolor=NASC, markeredgecolor='white', ms=8), Line2D([], [], color=COL['fbds'], lw=1.0)],
              ['açude: %s ha' % fmt(ag['acude_cabeceira_ha'], 3), 'nascente (mapa oficial)', 'Arroio 2 (mapa oficial)'], loc='upper left', fontsize=6.5, frameon=True, framealpha=0.9, handlelength=1.5)
    fig.text(l2 / W, (b1 - cap_dy) / H, textwrap.fill('(b) Cabeceira do Arroio 2: açude pequeno (%s ha; o CAR declara 0,147 ha) e, a %s m dele, o ponto da nascente do mapa oficial. '
                                                        'O olho d\'água exato fica escondido no brejo: marcar com GPS em campo.' % (fmt(ag['acude_cabeceira_ha'], 3), fmt(d.nasc_acude_m, 0)), 46),
             fontsize=cap_fs, va='top', color=GRIS, linespacing=1.25)
    s = textwrap.fill(FONTE_A + ' · ' + FONTE_B, 105)
    fig.text(1.45 / W, 0.85 / H, s, fontsize=6.4, color='#444444', va='bottom', linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
    return fig


# ------------------------------------------------------------------ AL1 ------
def AL1(d):
    k = d.al['kpi']; v = d.al['vegetacao_ha']; pn = d.al['reserva_legal']['ponta_norte_a_conferir']
    ext = extent_de(d.AL, 150, 90)
    M = Mapa('V', 'AL1 · Os 6 alqueires vistos pelo drone', 'Polígono de %s ha (%s alqueires) · foto de drone de 22/05/2026 · comprada como terra limpa' % (
        fmt(k['area_poligono_ha']), fmt(d.al['alqueires_paulistas_poligono'])), ext, leg_min_cm=6.2, notas_abajo=True)
    M.fs = 9.2; M.fig.texts[0].set_fontsize(14.0); M.fig.texts[1].set_fontsize(7.6)
    fondo(M, d.AL, R('seis_alqueires', 'ortofoto_rgba_0_25m.tif'))
    ax = M.ax
    x0, y0, x1, y1 = d.AL.bounds
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 - 60, 'Área dos\n6 alqueires\n%s ha\n= %s alq.\n\nterra limpa\n(lavoura)' % (fmt(k['area_poligono_ha']), fmt(d.al['alqueires_paulistas_poligono'])),
            fontsize=7.8, fontweight='bold', ha='center', va='center', zorder=40, bbox=dict(boxstyle='round,pad=0.3', fc=AMARELO, ec='black', lw=0.6, alpha=0.95))
    contorno(ax, d.AL, lw=2.2); M.grilla(250); M.norte_escala(250)
    M.leg_titulo('O que o drone mostra')
    M.leg_items([Line2D([], [], color='black', lw=1.0), Patch(fc=FORA, ec='#BBBBBB')],
                ['Área dos 6 alqueires: polígono de %s ha' % fmt(k['area_poligono_ha']), 'Fora do polígono'])
    M.leg_espacio(0.15)
    rows = [['O que existe', 'ha'], ['Lavoura e solo', fmt(v['lavoura_solo_ha'])], ['Pasto', fmt(v['pasto_ha'], 3)], ['Mata (árvores)', fmt(v['arborea_ha'], 3)], ['Água', fmt(v['agua_ha'])],
            ['Arroio ou nascente dentro', '0'], ['Sem foto do drone', fmt(v['sem_cobertura_drone'])], ['Total do polígono', fmt(v['total_ha'])]]
    M.leg_tabla(rows, col_w=[0.72, 0.28], bold_last=True)
    M.leg_texto('O drone cobriu 100% do polígono. Não há arroio, nascente nem água dentro dele: não há beira de rio (APP) a plantar aqui.', fs=8.0)
    M.leg_espacio(0.1)
    M.leg_texto('A mata que fica ao norte deste polígono não faz parte desta compra e não entra nesta conta.', fs=8.0)
    M.leg_espacio(0.1)
    M.leg_texto('Terra limpa confirmada: %s ha de lavoura em %s ha.' % (fmt(v['lavoura_solo_ha']), fmt(v['total_ha'])), fs=8.4, bold=True, color=AZUL)
    txt = textwrap.fill(FONTE_A + ' · ' + FONTE_B, 96)
    M.fig.text(1.45 / M.W, 0.78 / M.H, txt, fontsize=7.0, color='#444444', va='bottom', linespacing=1.25,
               bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
    return M


# ------------------------------------------------------------------ AL2 ------
def AL2(d):
    RL = d.al['reserva_legal']; k = d.al['kpi']; cz = d.al['cruzamento_car']
    W, H = 15.0, 11.9
    fig = fig_marca('AL2 · Reserva Legal que falta nos 6 alqueires', 'Reserva Legal = 20%% do imóvel com mata nativa · 20%% de %s ha = %s ha · hoje: 0 ha de mata' % (
        fmt(k['area_poligono_ha']), fmt(RL['exigida_ha'])), W, H)
    # mapa pequeno à esquerda
    ext = extent_de(d.AL, 120, 60); x0, y0, x1, y1 = ext
    ph = 7.3; pw = ph * (x1 - x0) / (y1 - y0); l1 = 1.45; b1 = H - 1.75 - ph
    ax = panel_axes(fig, W, H, l1, b1, pw, ph, ext)
    with rasterio.open(R('seis_alqueires', 'ortofoto_rgba_0_25m.tif')) as ds:
        win = from_bounds(max(x0, ds.bounds.left), max(y0, ds.bounds.bottom), min(x1, ds.bounds.right), min(y1, ds.bounds.top), ds.transform)
        img = ds.read(window=win); tr = ds.window_transform(win)
    h, w = img.shape[1], img.shape[2]; ex = (tr.c, tr.c + w * tr.a, tr.f + h * tr.e, tr.f)
    rgb = np.moveaxis(img[:3], 0, -1).astype(np.float32) / 255.0
    fora = np.array(matplotlib.colors.to_rgb(FORA), dtype=np.float32)
    rgb = np.where((img[3] > 0)[..., None], rgb, fora)
    ax.imshow(rgb, extent=ex, interpolation='nearest', zorder=1); ax.set_facecolor(FORA)
    poly_patches(ax, [d.AL], fc=LAR + '77', ec='#92400E', hatch='\\\\', lw=0.5, zorder=6)
    contorno(ax, d.AL, lw=1.6, zorder=20)
    escala(ax, ext, 100)
    ax.text((d.AL.bounds[0] + d.AL.bounds[2]) / 2, (d.AL.bounds[1] + d.AL.bounds[3]) / 2, '%s ha\na definir\nem qualquer\nparte do\npolígono' % fmt(RL['exigida_ha']), fontsize=7.4, fontweight='bold',
            ha='center', va='center', zorder=40, bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#92400E', lw=0.8, alpha=0.95))
    # KPI + tabela à direita
    lx = l1 + pw + 1.1; lw_cm = W - lx - 0.5
    axl = fig.add_axes([lx / W, b1 / H, lw_cm / W, ph / H]); axl.axis('off')
    axl.text(0, 1.0, 'Falta plantar ou compensar', fontsize=10.4, fontweight='bold', color=AZUL, va='top', transform=axl.transAxes)
    axl.text(0, 0.91, '%s ha' % fmt(RL['exigida_ha']), fontsize=30, fontweight='bold', color=AZUL, va='top', transform=axl.transAxes)
    axl.text(0, 0.72, 'de Reserva Legal (toda: hoje há 0 ha de mata)', fontsize=8.6, color=GRIS, va='top', transform=axl.transAxes)
    rows = [['Reserva Legal (20%)', 'ha'], ['A lei pede (20%% de %s ha)' % fmt(k['area_poligono_ha']), fmt(RL['exigida_ha'])],
            ['Mata que conta hoje', fmt(RL['vegetacao_computavel_ha'])], ['Falta', fmt(RL['deficit_ha'])], ['Beira de rio (APP) a plantar', fmt(k['app_a_recompor_ha'])],
            ['O CAR de origem declara aqui', fmt(cz['declarado_DENTRO_do_poligono_deste_imovel_ha']['reserva_legal'])]]
    n = len(rows); rh = 0.36 / ph; hh = n * rh
    tab = axl.table(cellText=rows, colWidths=[0.74, 0.26], bbox=[0, 0.66 - hh, 1, hh], cellLoc='left')
    tab.auto_set_font_size(False); tab.set_fontsize(8.6)
    for (r, c), cell in tab.get_celld().items():
        cell.set_linewidth(0.3); cell.set_edgecolor('#BBBBBB'); cell.PAD = 0.03
        if c > 0:
            cell.get_text().set_ha('right')
        if r == 0:
            cell.set_facecolor(TEAL); cell.get_text().set_color('white'); cell.get_text().set_fontweight('bold')
        elif r == 4:
            cell.set_facecolor('#EAF6F4'); cell.get_text().set_fontweight('bold')
        elif r % 2 == 0:
            cell.set_facecolor('#F5F7FA')
    y = 0.66 - hh - 0.05
    s = textwrap.fill('Por que 20%% mesmo sendo pequena: a área veio de um imóvel de %s ha (%s módulos fiscais), e a lei manda manter os 20%% quando se desmembra um imóvel maior que 4 módulos. '
                      'A regra que reduz a Reserva Legal só vale se o imóvel de origem tivesse até 4 módulos em 2008.' % (
                          fmt(cz['declarado_no_car_inteiro']['area_imovel_ha']), fmt(cz['status_atual']['mod_fiscal_declarado'], 1)), 52)
    axl.text(0, y, s, fontsize=7.8, color=GRIS, va='top', transform=axl.transAxes, linespacing=1.25)
    s = FONTE_A + ' · Laranja: a Reserva Legal pode ficar em qualquer parte do polígono, ou ser compensada em outra área com mata no mesmo bioma. Diagnóstico preliminar: não é laudo; o IAT valida.'
    fig.text(1.45 / W, 0.85 / H, textwrap.fill(s, 105), fontsize=6.4, color='#444444', va='bottom', linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
    return fig


# ------------------------------------------------------------------ main -----
def guardar(M, nome):
    os.makedirs(OUT, exist_ok=True)
    ruta = os.path.join(OUT, nome + '.png')
    fig = M.fig if hasattr(M, 'fig') else M
    fig.savefig(ruta, dpi=DPI, facecolor='white'); plt.close(fig)
    log('  -> %s' % ruta)


MAPAS = [('SA1_fazenda_vista_pelo_drone', SA1), ('SA2_mata_beira_rios_app', SA2), ('SA3_reserva_legal', SA3), ('SA4_car_vs_drone', SA4),
         ('SA5_represa_acude_nascente_perto', SA5), ('AL1_seis_alqueires_drone', AL1), ('AL2_reserva_legal_seis_alqueires', AL2)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--solo', default='')
    a = ap.parse_args()
    log('=' * 70); log('dron_05_mapas_v5  (hoje %s; documento %s)' % (HOY, DATA_DOC)); log('=' * 70)
    d = D5()
    quer = set(a.solo.split(',')) if a.solo else None
    for nome, fn in MAPAS:
        if quer and nome.split('_')[0] not in quer:
            continue
        guardar(fn(d), nome)
    log('dron_05 listo')


if __name__ == '__main__':
    main()
