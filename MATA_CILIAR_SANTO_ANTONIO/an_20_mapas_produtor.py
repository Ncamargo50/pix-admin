# -*- coding: utf-8 -*-
"""an_20_mapas_produtor.py — mapas SIMPLIFICADOS para o produtor (pt-BR), P1..P5.

Menos camadas, rótulos grandes, legenda fora do mapa, sem sobreposição de textos.
Nenhuma cifra é recalculada: tudo sai de resultados_v4.json / resultados_v3.json (via DadosV4).
Saída: 03_MAPAS_PRODUTOR/P1..P5 (PNG 250 dpi).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import PROYECTO, CRS_METRICO, log          # noqa: E402
import an_04_mapas as m4                                      # noqa: E402
import an_08_mapas_interior as m8                             # noqa: E402
import an_13_mapas_v3 as m13                                  # noqa: E402
import an_16_mapas_v4 as m16                                  # noqa: E402
from an_04_mapas import COL, AZUL, TEAL, LIMA, GRIS, fmt, poly_patches, plot_lines, raster_clases, DPI, Mapa  # noqa: E402
from an_08_mapas_interior import extent_interior, patch_agujeros, FORA   # noqa: E402
from an_16_mapas_v4 import DadosV4, fondo_orto, fig_marca, panel_axes, escala, orto_5cm, ORTO  # noqa: E402

import matplotlib                                  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt                    # noqa: E402
from matplotlib.lines import Line2D                # noqa: E402
from matplotlib.patches import Patch               # noqa: E402
import geopandas as gpd                            # noqa: E402
from shapely.geometry import Point                 # noqa: E402
from shapely.ops import unary_union                # noqa: E402

OUT = os.path.join(PROYECTO, '03_MAPAS_PRODUTOR')
VERDE = '#2E7D32'; VERDE_CL = '#7FD633'; VERM = '#D32F2F'; AZ = '#1E88E5'; AZ_ESC = '#0D47A1'; LAR = '#F59E0B'
FONTE_A = 'Fundo: foto de drone de 22/05/2026 (faixa norte sem voo: satélite de 29/08/2026)'
FONTE_B = 'Linhas dos arroios: mapa oficial FBDS/IAT 2013 · Diagnóstico preliminar: não é laudo; o técnico de campo e o IAT confirmam.'
FONTE = FONTE_A + ' · ' + FONTE_B


def rotulo(ax, x, y, txt, fc, dx=0, dy=0, fs=8.4, color='white', ec='white', seta=True, ha='center', va='center'):
    """Rótulo grande com caixa e linha-guia (dx, dy em metros)."""
    kw = dict(fontsize=fs, ha=ha, va=va, zorder=45, color=color, fontweight='bold',
              bbox=dict(boxstyle='round,pad=0.3', fc=fc, ec=ec, lw=0.7, alpha=0.96))
    if seta and (dx or dy):
        ax.annotate(txt, xy=(x, y), xytext=(x + dx, y + dy), arrowprops=dict(arrowstyle='-', lw=0.8, color=fc if fc != 'white' else 'black'), **kw)
    else:
        ax.text(x + dx, y + dy, txt, **kw)


def base(d, titulo, sub, extent=None, leg_min_cm=6.6):
    m16.LANG = 'pt'; m4.LANG = 'pt'; m8.LANG = 'pt'
    m4.T['notas'] = {'pt': FONTE_B, 'es': FONTE_B}; m4.T['fonte_s2'] = {'pt': FONTE_A, 'es': FONTE_A}
    M = Mapa('V', titulo, sub, extent or extent_interior(d, 140), leg_min_cm=leg_min_cm)
    M.fs = 9.4                       # legenda maior que nos mapas técnicos (o mapa entra no PDF a ~60-70 %)
    M.fig.texts[0].set_fontsize(14.5); M.fig.texts[1].set_fontsize(7.8)
    fondo_orto(M, d)
    return M


def glebas_grandes(M, d, rotular=True):
    ax = M.ax
    for g, col in [(d.G1, COL['prop']), (d.G2, COL['g2'])]:
        gpd.GeoSeries([g], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=3.0, zorder=30)
        gpd.GeoSeries([g], crs=CRS_METRICO).boundary.plot(ax=ax, color=col, lw=1.9, zorder=31)
    if rotular:
        x0, y0, x1, y1 = d.G1.bounds
        ax.text((x0 + x1) / 2 - 10, 7402350, 'GLEBA 1\n%s ha' % fmt(d.g1['area_ha']), fontsize=8.8, fontweight='bold', color='black',
                ha='center', va='center', zorder=40, bbox=dict(boxstyle='round,pad=0.3', fc=COL['prop'], ec='black', lw=0.6, alpha=0.95))
        x0, y0, x1, y1 = d.G2.bounds
        ax.text((x0 + x1) / 2 + 5, (y0 + y1) / 2 - 40, 'GLEBA 2\n6 alq.', fontsize=7.6, fontweight='bold', color='black',
                ha='center', va='center', zorder=40, bbox=dict(boxstyle='round,pad=0.25', fc=COL['g2'], ec='black', lw=0.6, alpha=0.95))


def leg_glebas(d):
    return ([Line2D([], [], color=COL['prop'], lw=3), Line2D([], [], color=COL['g2'], lw=3), Patch(fc=FORA, ec='#BBBBBB')],
            ['Gleba 1 (%s ha)' % fmt(d.g1['area_ha']), 'Gleba 2, "os 6 alqueires" (%s ha)' % fmt(d.g2['area_ha']), 'Fora da fazenda'])


def nomes_arroios(M, d, cu):
    """Rótulos grandes dos 3 arroios com os metros dentro da fazenda (JSON cursos.fbds_m)."""
    ax = M.ax
    pos = {1: (0.30, -170, 95), 2: (0.62, 175, 40), 3: (0.90, -20, -185)}
    for _, r in d.arr['G1'].iterrows():
        n = int(r.n); f, dx, dy = pos[n]
        c = r.geometry.interpolate(f, normalized=True)
        key = {1: 'G1 Arroio 1 (norte)', 2: 'G1 Arroio 2 (central)', 3: 'G1 Arroio 3 (sul)'}[n]
        rotulo(ax, c.x, c.y, 'Arroio %d\n%s m' % (n, fmt(cu[key]['fbds_m'], 0)), COL['fbds'], dx, dy, fs=8.2)


# ---------------------------------------------------------------- P1 --------
def P1(d):
    k = d.v4['kpi']; rp = d.v4['represa']; cu = d.v4['cursos']; r2 = rp['reservatorio_cabeceira_arroio2']; n0 = d.v4['nascentes']['pontos'][0]
    M = base(d, 'P1 · A fazenda vista de cima', 'Foto de drone 22/05/2026 · %s ha em 2 glebas · 3 arroios · nascente · represa e açude' % fmt(k['area_imovel_ha']))
    ax = M.ax
    poly_patches(ax, [d.represa], fc=AZ, ec='white', lw=0.6, zorder=8)
    poly_patches(ax, [d.acude], fc=AZ_ESC, ec='white', lw=0.6, zorder=8)
    for u in ('G1', 'G2'):
        d.arr[u].plot(ax=ax, color='white', lw=3.2, zorder=10)
        d.arr[u].plot(ax=ax, color=COL['fbds'], lw=1.8, zorder=11)
    nomes_arroios(M, d, cu)
    ax.scatter([n0['x']], [n0['y']], s=70, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=1.2, zorder=16)
    rotulo(ax, n0['x'], n0['y'], 'Nascente\n(provável)', 'white', dx=95, dy=-120, fs=7.8, color=COL['nasc_prov'], ec=COL['nasc_prov'])
    c = d.represa.centroid
    rotulo(ax, c.x, c.y, 'Represa\n%s ha' % fmt(rp['espelho_22_mai_2026_ha']), 'white', dx=150, dy=-215, fs=8.0, color=AZ_ESC, ec=AZ)
    c = d.acude.centroid
    rotulo(ax, c.x, c.y, 'Açude\n%s ha' % fmt(r2['area_agua_ha'], 3), 'white', dx=-175, dy=125, fs=7.6, color=AZ_ESC, ec=AZ_ESC)
    glebas_grandes(M, d); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo('O que tem dentro da fazenda')
    M.leg_items(h + [Line2D([], [], color=COL['fbds'], lw=2.2), Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=8),
                     Patch(fc=AZ, ec='white'), Patch(fc=AZ_ESC, ec='white')],
                l + ['Arroio (córrego) e metros dentro da fazenda', 'Nascente provável (água a %s m; conferir em campo)' % fmt(n0['dist_agua_aberta_m'], 0),
                     'Represa: %s ha de água em 22/05/2026' % fmt(rp['espelho_22_mai_2026_ha']), 'Açude pequeno na cabeceira do Arroio 2: %s ha' % fmt(r2['area_agua_ha'], 3)])
    M.leg_espacio(0.25)
    rows = [['Arroio', 'Metros dentro', 'Largura']]
    for key, n_ in [('G1 Arroio 1 (norte)', 1), ('G1 Arroio 2 (central)', 2), ('G1 Arroio 3 (sul)', 3)]:
        rows.append(['Arroio %d' % n_, fmt(cu[key]['fbds_m'], 0), 'até 10 m*'])
    M.leg_tabla(rows, col_w=[0.34, 0.36, 0.30])
    M.leg_texto('* Largura provável, ainda sem medição: as árvores escondem o leito. Medir com trena e GPS.', fs=8.4)
    M.leg_espacio(0.2)
    v = d.v4['vegetacao']['por_gleba']['IMOVEL']
    cons = {}
    for ln in d.v4['mapa_car_v4']['linhas']:
        if ln['classe_car'].startswith('Area Consolidada'):
            cons[ln['subclasse']] = cons.get(ln['subclasse'], 0.0) + ln['area_ha']
    M.leg_texto('Mata nativa que conta: %s ha · lavoura: cerca de %s ha · pasto: cerca de %s ha · água: %s ha.' % (
        fmt(d.v4['kpi']['veg_computavel_ha'], 1), fmt(cons.get('uso agricola', 0.0), 0), fmt(cons.get('pasto/herbacea', 0.0), 0), fmt(v['agua'], 1)), fs=8.6, bold=True, color=AZUL)
    M.notas()
    return M


# ---------------------------------------------------------------- P2 --------
def P2(d):
    A = d.v4['app']['fbds']['IMOVEL']; P = d.v4['app']['pra']['IMOVEL']; n0 = d.v4['nascentes']['pontos'][0]; rp = d.v4['represa']
    M = base(d, 'P2 · Onde falta mata na beira dos rios', 'APP = faixa de mata exigida pela lei: 30 m ao lado dos arroios e 50 m em volta da nascente')
    ax = M.ax
    c4 = d.car4[d.car4.classe_car.str.startswith('APP')]
    c4[c4.subclasse == 'conforme'].plot(ax=ax, fc=VERDE, ec='none', alpha=0.95, zorder=6)
    c4[c4.subclasse == 'agua'].plot(ax=ax, fc=AZ, ec='none', alpha=0.95, zorder=6)
    c4[c4.subclasse == 'a recompor'].plot(ax=ax, fc=VERM, ec='none', alpha=0.95, zorder=6)
    poly_patches(ax, [d.app4_fbds], fc='none', ec='black', lw=0.9, ls='--', zorder=12)
    poly_patches(ax, [d.represa], fc=AZ, ec='white', lw=0.5, zorder=7)
    for u in ('G1', 'G2'):
        d.arr[u].plot(ax=ax, color=COL['fbds'], lw=0.9, zorder=11)
    ax.scatter([n0['x']], [n0['y']], s=60, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=1.1, zorder=16)
    # rótulos: onde falta plantar (maiores manchas vermelhas)
    rec = c4[c4.subclasse == 'a recompor']
    partes = sorted([p for g in rec.geometry for p in (g.geoms if hasattr(g, 'geoms') else [g])], key=lambda p: -p.area)
    usados = []
    for p in partes[:3]:
        c = p.representative_point()
        if any(c.distance(u) < 250 for u in usados):
            continue
        usados.append(c)
        rotulo(ax, c.x, c.y, 'falta\nplantar', 'white', dx=(190 if c.x < 534900 else -200), dy=(60 if len(usados) % 2 else -60), fs=7.8, color=VERM, ec=VERM)
    rotulo(ax, n0['x'], n0['y'], 'Nascente', 'white', dx=120, dy=-95, fs=7.8, color=COL['nasc_prov'], ec=COL['nasc_prov'])
    glebas_grandes(M, d, rotular=False); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo('Cores do mapa')
    M.leg_items(h + [Patch(fc=VERDE), Patch(fc=AZ), Patch(fc=VERM), Line2D([], [], color='black', lw=1.0, ls='--'), Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=8)],
                l + ['Verde: já tem mata (%s ha)' % fmt(A['com_vegetacao_nativa_ha']), 'Azul: água (%s ha)' % fmt(A['agua_ha']),
                     'Vermelho: falta plantar (%s ha)' % fmt(A['a_recompor_ha']), 'Linha tracejada: faixa que a lei pede (%s ha)' % fmt(A['exigida_ha']), 'Nascente provável'])
    M.leg_espacio(0.25)
    rows = [['Faixa dos rios (APP)', 'ha'], ['A lei pede', fmt(A['exigida_ha'])], ['Já tem mata', fmt(A['com_vegetacao_nativa_ha'])], ['É água', fmt(A['agua_ha'])],
            ['Falta plantar', fmt(A['a_recompor_ha'])], ['Falta plantar (com PRA)', fmt(P['a_recompor_ha'])]]
    M.leg_tabla(rows, col_w=[0.72, 0.28], bold_last=True)
    M.leg_texto('PRA = programa do Paraná que reduz a faixa a 20 m para quem regulariza. Depende da data do CAR.', fs=8.4)
    M.leg_espacio(0.15)
    M.leg_texto('Represa: %s ha (maior que 1 ha). A faixa de mata em volta dela quem define é o IAT, na licença.' % fmt(rp['espelho_22_mai_2026_ha']), fs=8.4)
    M.leg_espacio(0.15)
    M.leg_texto('Falta plantar %s ha de mata na beira dos rios (%s ha se entrar no PRA).' % (fmt(A['a_recompor_ha']), fmt(P['a_recompor_ha'])), fs=8.8, bold=True, color=AZUL)
    M.notas()
    return M


# ---------------------------------------------------------------- P3 --------
def P3(d):
    RL = d.v4['reserva_legal']; pr = RL['principal_mmu_0_05ha_g2_terra_limpa']; co = RL['conservador_sem_fragmento_13']; k = d.v4['kpi']
    loc = d.v3['reserva_legal']['localizacao_proposta']
    f13_ha = next(f['area_poligono_s2_dentro_ha'] for f in d.v4['vegetacao']['fragmentos'] if f['frag_id'] == 13)
    M = base(d, 'P3 · Reserva Legal: o que conta e o que falta', 'Reserva Legal = 20%% da fazenda com mata nativa: %s ha de %s ha' % (fmt(RL['exigida_ha']), fmt(k['area_imovel_ha'])))
    ax = M.ax
    d.rl4.plot(ax=ax, fc=VERDE, ec='none', alpha=0.95, zorder=6)
    poly_patches(ax, [d.f13], fc='none', ec='white', hatch='///', lw=0.0, zorder=8)
    poly_patches(ax, [d.corr_g1], fc=LAR + 'BB', ec='#92400E', hatch='\\\\', lw=0.5, zorder=7)
    poly_patches(ax, list(d.ponta.geometry), fc='none', ec=COL['ponta'], hatch='xx', lw=1.0, zorder=9)
    for u in ('G1', 'G2'):
        d.arr[u].plot(ax=ax, color=COL['fbds'], lw=0.8, zorder=11)
    # rótulos
    c = d.f13.representative_point()
    rotulo(ax, c.x, c.y, 'Mata nova\nna beira do\nArroio 2', 'white', dx=205, dy=-40, fs=7.6, color=VERDE, ec=VERDE)
    cc = d.corr_g1.representative_point()
    rotulo(ax, cc.x, cc.y, 'Onde plantar\nou deixar\nregenerar', 'white', dx=170, dy=-200, fs=7.6, color='#92400E', ec=LAR)
    cp = unary_union(d.ponta.geometry).representative_point()
    rotulo(ax, cp.x, cp.y, 'Ponta norte:\nnão conta', 'white', dx=-250, dy=-110, fs=7.4, color=COL['ponta'], ec=COL['ponta'])
    glebas_grandes(M, d, rotular=False); M.grilla(); M.norte_escala()
    h, l = leg_glebas(d)
    M.leg_titulo('Cores do mapa')
    M.leg_items(h + [Patch(fc=VERDE), Patch(fc=VERDE, hatch='///', ec='white'), Patch(fc=LAR, hatch='\\\\', ec='#92400E'), Patch(fc='none', hatch='xx', ec=COL['ponta'])],
                l + ['Verde: mata que conta hoje (%s ha)' % fmt(pr['vegetacao_computavel_ha']), 'Riscado branco: mata nova em regeneração (%s ha), a confirmar em campo' % fmt(f13_ha),
                     'Laranja: onde plantar ou deixar regenerar (%s ha)' % fmt(loc['corredor_g1_ha']), 'Ponta norte da Gleba 2: mata que não conta (conferir na escritura)'])
    M.leg_espacio(0.25)
    rows = [['Reserva Legal (20%)', 'ha'], ['A lei pede', fmt(RL['exigida_ha'])], ['Mata que conta hoje', fmt(pr['vegetacao_computavel_ha'])], ['Falta', fmt(pr['deficit_ha'])],
            ['Falta (sem a mata nova)', fmt(co['deficit_ha'])]]
    M.leg_tabla(rows, col_w=[0.72, 0.28])
    M.leg_texto('O CAR de hoje declara só %s ha de Reserva Legal.' % fmt(d.v3['kpi']['car_rl_averbada_ha']), fs=8.4)
    M.leg_espacio(0.15)
    M.leg_texto('Faltam %s ha de Reserva Legal. Três caminhos: deixar regenerar, plantar, ou compensar em outra área.' % fmt(pr['deficit_ha']), fs=8.8, bold=True, color=AZUL)
    M.notas()
    return M


# ---------------------------------------------------------------- P4 --------
def P4(d):
    C2 = d.v3['gleba2_cenarios']; k3 = d.v3['kpi']; RL = d.v4['reserva_legal']; g2v = d.v4['vegetacao']['por_gleba']['G2']; g2a = d.v4['app']['fbds']['G2']
    A_ = C2['A_imovel_unico_principal']
    x0, y0, x1, y1 = d.G2.bounds
    ext = (x0 - 170, y0 - 330, x1 + 170, y1 + 330)
    M = base(d, 'P4 · Os 6 alqueires (Gleba 2)', '%s ha comprados como terra limpa · a ponta norte tem mata: conferir na escritura' % fmt(k3['area_g2_ha']), extent=ext, leg_min_cm=6.4)
    ax = M.ax
    raster_clases(ax, os.path.join(ORTO, 'vegetacao_ortofoto_0_50m.tif'), M.extent, {1: VERDE + 'CC', 2: VERDE + 'CC', 9: VERDE + 'CC', 3: VERDE_CL + 'CC', 4: '#FFF176' + '99', 5: '#D7CCC8' + '66'}, zorder=5, clip=d.G2)
    poly_patches(ax, list(d.ponta.geometry), fc='none', ec=COL['ponta'], hatch='xx', lw=1.4, zorder=9)
    d.arr['G2'].plot(ax=ax, color=COL['fbds'], lw=1.8, zorder=11)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=2.6, zorder=30)
    gpd.GeoSeries([d.G1], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['prop'], lw=1.5, zorder=31)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color='black', lw=3.4, zorder=32)
    gpd.GeoSeries([d.G2], crs=CRS_METRICO).boundary.plot(ax=ax, color=COL['g2'], lw=2.2, zorder=33)
    patch_agujeros(ax, d.G1, fc=FORA + 'DD', ec='none', lw=0, zorder=26)
    c = unary_union(d.ponta.geometry).representative_point()
    rotulo(ax, c.x, c.y, 'Ponta norte com mata\n(%s ha): conferir\nna escritura' % fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha']), 'white', dx=-20, dy=-230, fs=8.0, color=COL['ponta'], ec=COL['ponta'])
    xm = (x0 + x1) / 2
    ax.text(xm, (y0 + y1) / 2 - 120, 'GLEBA 2\n%s ha\n= 6 alqueires\n\nterra limpa\n(lavoura)' % fmt(k3['area_g2_ha']), fontsize=8.4, fontweight='bold', ha='center', va='center', zorder=40,
            bbox=dict(boxstyle='round,pad=0.3', fc=COL['g2'], ec='black', lw=0.6, alpha=0.95))
    ax.text(x0 - 85, (y0 + y1) / 2 + 20, 'GLEBA 1', fontsize=7.6, fontweight='bold', ha='center', va='center', rotation=90, zorder=40,
            bbox=dict(boxstyle='round,pad=0.25', fc=COL['prop'], ec='black', lw=0.5, alpha=0.95))
    M.grilla(250); M.norte_escala(250)
    M.leg_titulo('Cores do mapa')
    M.leg_items([Line2D([], [], color=COL['g2'], lw=3), Line2D([], [], color=COL['prop'], lw=2.4), Patch(fc=FORA, ec='#BBBBBB'), Patch(fc='#D7CCC8', ec='#BBBBBB'), Patch(fc=VERDE, hatch='xx', ec=COL['ponta']), Line2D([], [], color=COL['fbds'], lw=2.0)],
                ['Gleba 2, "os 6 alqueires" (%s ha)' % fmt(k3['area_g2_ha']), 'Gleba 1 (%s ha)' % fmt(k3['area_g1_ha']), 'Fora da fazenda', 'Lavoura / terra limpa (%s ha)' % fmt(g2v['solo_cultivo']),
                 'Mata na ponta norte (%s ha): talvez seja do vizinho' % fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha']), 'Arroio 1 (só %s m dentro)' % fmt(C2['app_g2']['curso_m'], 0)])
    M.leg_espacio(0.25)
    rows = [['Conta da Reserva Legal', 'ha'], ['20% da Gleba 2', fmt(A_['rl_parcela_g2_ha'])], ['20% da Gleba 1', fmt(A_['rl_parcela_g1_ha'])], ['Fazenda inteira (20%)', fmt(A_['rl_exigida_imovel_ha'])]]
    M.leg_tabla(rows, col_w=[0.74, 0.26], bold_last=True)
    M.leg_texto('As duas glebas são da mesma dona e ficam coladas: pela regra, é uma fazenda só e um CAR só.', fs=8.4)
    M.leg_espacio(0.12)
    M.leg_texto('A Gleba 2 foi comprada limpa: soma %s ha à Reserva Legal e não traz mata. A Reserva pode ficar toda na Gleba 1.' % fmt(A_['rl_parcela_g2_ha']), fs=8.4)
    M.leg_espacio(0.12)
    M.leg_texto('A ponta norte tem %s ha de mata. Se a escritura mostrar que essa ponta não é da fazenda, ela sai da conta. Se for, a Reserva que falta cai para %s ha.' % (
        fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha']), fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['deficit_ha'])), fs=8.4)
    M.notas()
    return M


# ---------------------------------------------------------------- P5 --------
def P5(d):
    W, H = 15.0, 11.8
    fig = fig_marca('P5 · Represa e nascente de perto', 'Foto de drone de 22/05/2026 a 5 cm por pixel', W, H)
    fig.texts[0].set_fontsize(14.5); fig.texts[1].set_fontsize(7.8)
    rp = d.v4['represa']; r2 = rp['reservatorio_cabeceira_arroio2']; n0 = d.v4['nascentes']['pontos'][0]
    pw, ph = 6.1, 6.1; l1, l2 = 1.45, 1.45 + pw + 1.0; b1 = H - 1.85 - ph
    cap_fs = 7.0; cap_dy = 0.45
    # (a) represa
    x0, y0, x1, y1 = d.vaso.bounds; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; hw = max(x1 - x0, y1 - y0) / 2 + 20
    ext = (cx - hw, cy - hw, cx + hw, cy + hw)
    ax = panel_axes(fig, W, H, l1, b1, pw, ph, ext); orto_5cm(ax, ext)
    poly_patches(ax, [d.represa], fc=AZ + '44', ec=AZ, lw=1.6, zorder=8)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=1.0, zorder=10)
    escala(ax, ext, 50, fs=7)
    ax.legend([Patch(fc=AZ + '44', ec=AZ), Line2D([], [], color=COL['fbds'], lw=1.0)],
              ['água: %s ha' % fmt(rp['espelho_22_mai_2026_ha']), 'Arroio 3 (mapa oficial)'], loc='lower right', fontsize=7, frameon=True, framealpha=0.9, handlelength=1.5)
    fig.text(l1 / W, (b1 - cap_dy) / H, m4.textwrap.fill('(a) Represa: %s ha de água no dia do voo. É maior que 1 ha. A faixa de mata em volta sai da licença do IAT. '
                                                             'A outorga (licença de uso da água) venceu em 08/11/2025: renovar.' % fmt(rp['espelho_22_mai_2026_ha']), 46),
             fontsize=cap_fs, va='top', color=GRIS, linespacing=1.25)
    # (b) açude + nascente
    pts = [Point(n0['x'], n0['y'])] + list(d.acude.exterior.coords)
    ux = [p.x if hasattr(p, 'x') else p[0] for p in pts]; uy = [p.y if hasattr(p, 'y') else p[1] for p in pts]
    cx, cy = (min(ux) + max(ux)) / 2, (min(uy) + max(uy)) / 2; hw = max(max(ux) - min(ux), max(uy) - min(uy)) / 2 + 28
    ext = (cx - hw, cy - hw, cx + hw, cy + hw)
    ax = panel_axes(fig, W, H, l2, b1, pw, ph, ext); orto_5cm(ax, ext)
    poly_patches(ax, [d.acude], fc=AZ_ESC + '55', ec=AZ_ESC, lw=1.6, zorder=8)
    d.arr['G1'].plot(ax=ax, color=COL['fbds'], lw=1.0, zorder=10)
    ax.scatter([n0['x']], [n0['y']], s=70, marker='o', c=COL['nasc_prov'], edgecolors='white', linewidths=1.2, zorder=16)
    pa = d.acude.exterior.interpolate(d.acude.exterior.project(Point(n0['x'], n0['y'])))
    ax.plot([n0['x'], pa.x], [n0['y'], pa.y], color='white', lw=1.0, ls='--', zorder=15)
    ax.text((n0['x'] + pa.x) / 2 + 5, (n0['y'] + pa.y) / 2 + 2, '%s m' % fmt(n0['dist_agua_aberta_m'], 0), fontsize=7, color='white', fontweight='bold', zorder=17,
            bbox=dict(boxstyle='round,pad=0.15', fc='black', ec='none', alpha=0.5))
    escala(ax, ext, 25, fs=7)
    ax.legend([Patch(fc=AZ_ESC + '55', ec=AZ_ESC), Line2D([], [], marker='o', color='none', markerfacecolor=COL['nasc_prov'], markeredgecolor='white', ms=8), Line2D([], [], color=COL['fbds'], lw=1.0)],
              ['açude: %s ha' % fmt(r2['area_agua_ha'], 3), 'nascente (mapa oficial)', 'Arroio 2 (mapa oficial)'], loc='upper left', fontsize=7, frameon=True, framealpha=0.9, handlelength=1.5)
    fig.text(l2 / W, (b1 - cap_dy) / H, m4.textwrap.fill('(b) Cabeceira do Arroio 2: um açude pequeno (%s ha) e, a %s m dele, o ponto da nascente no mapa oficial. '
                                                             'O olho d\'água exato fica escondido no brejo: marcar com GPS em campo.' % (fmt(r2['area_agua_ha'], 3), fmt(n0['dist_agua_aberta_m'], 0)), 46),
             fontsize=cap_fs, va='top', color=GRIS, linespacing=1.25)
    s = m4.textwrap.fill(FONTE, 100)
    fig.text(1.45 / W, 0.95 / H, s, fontsize=6.6, color='#444444', va='bottom', linespacing=1.25, bbox=dict(boxstyle='round,pad=0.4', fc='#F5F7FA', ec='#DCE3EA', lw=0.6))
    return fig


def guardar(M, nome):
    os.makedirs(OUT, exist_ok=True)
    ruta = os.path.join(OUT, nome + '.png')
    fig = M.fig if hasattr(M, 'fig') else M
    fig.savefig(ruta, dpi=DPI, facecolor='white'); plt.close(fig)
    log('  -> %s' % ruta)


def main():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('--solo', default='')
    a = ap.parse_args()
    m16.LANG = 'pt'; m4.LANG = 'pt'; m8.LANG = 'pt'; m13.LANG = 'pt'
    log('=' * 70); log('an_20_mapas_produtor'); log('=' * 70)
    d = DadosV4()
    quiere = set(a.solo.split(',')) if a.solo else None
    for nome, fn in [('P1_fazenda_vista_de_cima', P1), ('P2_falta_mata_beira_rios', P2), ('P3_reserva_legal', P3), ('P4_seis_alqueires', P4), ('P5_represa_nascente_perto', P5)]:
        if quiere and nome.split('_')[0] not in quiere:
            continue
        guardar(fn(d), nome)
    log('an_20 listo')


if __name__ == '__main__':
    main()
