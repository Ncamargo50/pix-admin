# -*- coding: utf-8 -*-
"""an_09_informe_v2 — dictame tecnico preliminar POR GLEBA (marca Pixadvisor, PT e ES).

    python an_09_informe_v2.py --lang pt   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_v2_PT.pdf
    python an_09_informe_v2.py --lang es   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_v2_ES.pdf

Regra: cada numero sai de 02_ANALISIS/resultados_glebas.json (por gleba) ou de resultados_analisis.json
(totais auditados) via o dict V (coma decimal). Textos em textos_v2.py. Mapas de 03_MAPAS_V2.
Ao final: verificacao com PyMuPDF (KPIs por gleba, glifos, acentos, paginas 10-18).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, RESULTADOS_JSON, PARAMETROS_LEGALES, leer_json, log  # noqa: E402
from textos_v2 import TXT                                                                       # noqa: E402

SKILL = r'C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva'
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from pix_branding import Brand, TEAL, LIMA, AZUL, AZUL_D  # noqa: E402
from reportlab.lib.units import cm                        # noqa: E402
from reportlab.platypus import Image, PageBreak, KeepTogether, Spacer, Table, TableStyle  # noqa: E402

LOGO = os.path.join(SKILL, 'assets', 'logo_pix_azulnegro_trim.png')
MAPAS = os.path.join(PROYECTO, '03_MAPAS_V2')
LANG = 'pt'


def t(k):
    return TXT[k][LANG]


def fmt(x, d=2):
    s = f'{float(x):,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


# ------------------------------------------------------------------ cifras ----
def cifras():
    G = leer_json(os.path.join(ANALISIS, 'resultados_glebas.json'))
    R = leer_json(RESULTADOS_JSON)
    PL = leer_json(PARAMETROS_LEGALES)
    S = leer_json(os.path.join(ANALISIS, 'serie_ndvi_fragmentos_24m.json'))
    g1, g2, un = G['G1'], G['G2'], G['UNICO']
    L, H, VG = R['legal'], R['hidrografia'], R['vegetacao']
    A = L['app_total_exigivel']; RL = L['reserva_legal']; C = L['area_consolidada_app']; cob = VG['cobertura_propriedade']
    arr1 = {a['n']: a for a in g1['arroios']['lista']}; arr2 = {a['n']: a for a in g2['arroios']['lista']}
    f13 = [r['frag13_ribeira'] for r in S['serie']]
    mn = g2['reserva_legal']['monte_necessario_para_estar_na_lei']

    def blk(p, d):
        a, r, v = d['app'], d['reserva_legal'], d['vegetacao']
        return {
            p + '_ha': fmt(d['area_ha']), p + '_alq': fmt(d['alqueires_paulistas'], 1),
            p + '_app': fmt(a['exigida_ha']), p + '_app_curso': fmt(a['curso_dagua_ha']), p + '_app_nasc': fmt(a['nascente_ha']),
            p + '_app_veg': fmt(a['com_vegetacao_nativa_ha']), p + '_app_agua': fmt(a['agua_ha']), p + '_app_rec': fmt(a['a_recompor_ha']),
            p + '_app_silv': fmt(a['a_recompor_silvicultura_ha']), p + '_pct': fmt(a['pct_conforme'] or 0, 1),
            p + '_pra': fmt(a['cenario_pra_pr_20m']['a_recompor_ha']), p + '_appF': fmt(a['cenario_fbds_iat']['exigida_ha']),
            p + '_appF_rec': fmt(a['cenario_fbds_iat']['a_recompor_ha']),
            p + '_appF_add': fmt(a['cenario_fbds_iat']['a_recompor_ha'] - a['a_recompor_ha']),
            p + '_rl_ex': fmt(r['exigida_ha']), p + '_rem': fmt(r['remanescente_fora_app_ha']), p + '_rl_exist': fmt(r['existente_com_app_art15_ha']),
            p + '_rl_def': fmt(r['deficit_com_app_art15_ha']), p + '_rl_def_sem': fmt(r['deficit_sem_app_ha']), p + '_rl_pct': fmt(r['pct_atendido'], 1),
            p + '_flor': fmt(v['floresta_nativa_car_ha']), p + '_pct_flor': fmt(v['pct_da_gleba'], 1), p + '_silv': fmt(v['silvicultura_ha']),
            p + '_agua': fmt(v['agua_rf_ha']), p + '_agri': fmt(v['area_agricola_car_ha']),
            p + '_car_soma': fmt(d['mapa_car']['soma_ha']),
        }
    V = {}
    V.update(blk('g1', g1)); V.update(blk('g2', g2)); V.update(blk('un', un))
    V.update(dict(
        tot_ha=fmt(L['imovel_ha']), mf=str(PL['modulo_fiscal_ha']), n_mf=fmt(PL['n_modulos']), escena_id=R['_meta']['escena'],
        n_arr_g1=str(g1['arroios']['n']), n_arr_g2=str(g2['arroios']['n']), km_g1=fmt(g1['arroios']['km_dentro'], 3), km_g2=fmt(g2['arroios']['km_dentro'], 3),
        km_un=fmt(un['arroios']['km_dentro'], 3),
        a1_g1=fmt(arr1[1]['comprimento_dentro_m'], 0), a1_g2=fmt(arr2[1]['comprimento_dentro_m'], 0), a2_g1=fmt(arr1[2]['comprimento_dentro_m'], 0),
        a3_g1=fmt(arr1[3]['comprimento_dentro_m'], 0), a3_per=fmt(arr1[3]['regime_coincide_ibge_perene_m'], 0),
        conflu_m=fmt(G['_meta']['confluencia_mais_proxima_do_limite_m'], 0), dist_glebas=fmt(G['_meta']['distancia_entre_glebas_m'], 1),
        esp_fbds=fmt(g1['lagoas']['espelho_fbds_2013_ha']), esp_rf=fmt(g1['lagoas']['espelho_rf_2026_ha']), esp_mndwi=fmt(g1['lagoas']['espelho_mndwi_2026_ha']),
        esp_jrc=fmt(g1['lagoas']['espelho_jrc_max_extent_ha']),
        g2_hoje=fmt(mn['hoje_imagem_mostra_ha']), g2_min_sem=fmt(mn['minimo_vegetacao_nativa_sem_art15_ha']),
        rl_prop_tot=fmt(RL['proposta']['ha']), rl_prop_g1=fmt(g1['reserva_legal']['rl_proposta_recortada_ha']),
        rl_prop_g2=fmt(g2['reserva_legal']['rl_proposta_recortada_ha']), rl_prop_falta=fmt(-g1['reserva_legal']['rl_proposta_recortada_vs_exigida_ha']),
        corr_g1=fmt(g1['reserva_legal']['corredor_recomposicao_recortado_ha']),
        supr08=fmt(VG['mudanca_2008_2025']['supressao_pos2008_confirmada_ha']), cand_add=fmt(L['app_nascente']['candidatas_dem']['ha_adicional_fora_app_exigivel']),
        talv=fmt(g1['nascentes']['talvegue_dem_risco_ha']), car_viz=fmt(H['fontes']['CAR_vizinhos_hidro_pol']['sobreposicao_imoveis'][0]['ha_dentro_propriedade']),
        oa=fmt(VG['rf']['OA'], 3), kappa=fmt(VG['rf']['kappa'], 3), f1_silv=fmt(VG['rf']['F1']['SILVICULTURA'], 2),
        med_dem=fmt(H['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_mediana_m'], 1),
        p90_dem=fmt(H['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_p90_m'], 1),
        app_min=fmt(A['ha_min']), app_max=fmt(A['ha_max']), flor_min=fmt(cob['floresta_min_ha']), flor_max=fmt(cob['floresta_max_ha']),
        f13_min=fmt(min(f13)), f13_max=fmt(max(f13)),
    ))
    return G, R, V


# ------------------------------------------------------------ helpers PDF ----
def check_winansi(s, donde=''):
    bad = set()
    for ch in re.sub(r'<[^>]+>', '', s):
        try:
            ch.encode('cp1252')
        except UnicodeEncodeError:
            bad.add(ch)
    if bad:
        raise ValueError('glifos fora de WinAnsi %r em %s: %s' % (sorted(bad), donde, s[:80]))


def F(s, V):
    out = s.format_map(V)
    check_winansi(out, s[:30])
    return out


def tabla(B, rows, widths, V, aligns=None, bold_last=False):
    data = [[B.P(F(str(c), V), 'CellB' if i == 0 else 'Cell') for c in r] for i, r in enumerate(rows)]
    tb = B.tbl(data, widths, aligns=aligns)
    if bold_last:
        tb.setStyle(TableStyle([('BACKGROUND', (0, -1), (-1, -1), '#EAF6F4')]))
    return tb


def figura(B, nome, caption, V, max_h=21.0 * cm):
    from PIL import Image as PILImage
    ruta = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', nome + '.png')
    with PILImage.open(ruta) as im:
        ar = im.size[1] / im.size[0]
    w = B.CONTENT_W; h = w * ar
    if h > max_h:
        h = max_h; w = h / ar
    img = Image(ruta, width=w, height=h); img.hAlign = 'CENTER'
    return KeepTogether([img, Spacer(1, 3), B.P('<i>%s</i>' % F(caption, V), 'Note')])


def h2tab(B, titulo, tb):
    return KeepTogether([B.P(titulo, 'H2'), tb])


def sec_str(B, num, title):
    head = Table([[B.P(str(num), 'SecNum'), B.P(title, 'SecTitle')]], colWidths=[0.95 * cm, B.CONTENT_W - 0.95 * cm])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), TEAL), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                              ('LEFTPADDING', (0, 0), (0, 0), 0), ('RIGHTPADDING', (0, 0), (0, 0), 0), ('LEFTPADDING', (1, 0), (1, 0), 10),
                              ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LINEBELOW', (0, 0), (-1, -1), 2, LIMA)]))
    head.spaceBefore = 14; head.spaceAfter = 8
    return head


# ------------------------------------------------------------------ story -----
def construir(G, R, V):
    B = Brand(logo=LOGO, footer_center=t('footer'), hero_h=7.9 * cm)
    W = B.CONTENT_W
    story = []
    # capa + ficha + em uma linha
    story += B.cover_filler()
    story += [B.P(t('ficha_h'), 'H1'), B.hr(), B.meta_table([(F(k, V), F(v, V)) for k, v in t('ficha')])]
    story += [Spacer(1, 8), B.callout(t('linha_lbl'), F(t('linha'), V)), PageBreak()]
    # 1 resposta direta
    story += [B.sec(1, t('s1_h')), B.P(F(t('s1_intro'), V))]
    story += [B.kpi_strip([(F(n, V).replace(' ha', ''), 'ha · ' + F(l, V)) for n, l in t('kpi')]), Spacer(1, 10)]
    story += [h2tab(B, t('s1_t1_h'), tabla(B, t('s1_t1'), [2.5 * cm, 2.9 * cm, 2.9 * cm, 6.7 * cm], V))]
    story += [Spacer(1, 4), B.P(F(t('s1_nota'), V), 'Note')]
    # 2 inventario
    story += [PageBreak(), B.sec(2, t('s2_h')), B.P(F(t('s2_intro'), V))]
    story += [h2tab(B, t('s2_t1_h'), tabla(B, t('s2_t1'), [4.2 * cm, 6.4 * cm, 4.4 * cm], V))]
    story += [Spacer(1, 4), B.P(F(t('s2_nota'), V), 'Note')]
    story += [PageBreak(), figura(B, 'V01_vegetacao_nativa_interior', t('v01_cap'), V)]
    story += [PageBreak(), figura(B, 'V02_hidrografia_interior', t('v02_cap'), V)]
    # 3 APP
    story += [PageBreak(), B.sec(3, t('s3_h')), B.P(t('s3_base_h'), 'H2')] + [B.P(F(x, V), 'Bull') for x in t('s3_base')]
    story += [h2tab(B, t('s3_t1_h'), tabla(B, t('s3_t1'), [6.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))]
    story += [Spacer(1, 4), B.P(F(t('s3_nota'), V), 'Note')]
    story += [PageBreak(), figura(B, 'V03_app_mata_ciliar_interior', t('v03_cap'), V)]
    # 4 RL
    story += [PageBreak(), B.sec(4, t('s4_h')), B.P(F(t('s4_base'), V))]
    story += [h2tab(B, t('s4_t1_h'), tabla(B, t('s4_t1'), [6.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))]
    story += [Spacer(1, 8), B.callout(t('g2_lbl'), F(t('g2_call'), V), bg=AZUL_D)]
    story += [Spacer(1, 6), B.P(t('s4_prop_h'), 'H2'), B.P(F(t('s4_prop'), V))]
    story += [PageBreak(), figura(B, 'V04_reserva_legal_interior', t('v04_cap'), V)]
    story += [PageBreak(), figura(B, 'V06_gleba2_detalhe', t('v06_cap'), V)]
    # 5 CAR
    story += [PageBreak(), B.sec(5, t('s5_h')), B.P(F(t('s5_intro'), V))]
    rows = [t('s5_t1')]
    U = R['legal']['mapa_uso_car']['ha']
    c1 = {(r['classe_car'], r['subclasse']): r['area_ha'] for r in G['G1']['mapa_car']['ha']}
    c2 = {(r['classe_car'], r['subclasse']): r['area_ha'] for r in G['G2']['mapa_car']['ha']}
    for u in U:
        k = (u['classe_car'], u['subclasse'])
        a1, a2 = c1.get(k, 0.0), c2.get(k, 0.0)
        rows.append([u['classe_car'], t('car_sub')[u['subclasse']], fmt(a1), fmt(a2) if a2 > 0 else '—', fmt(a1 + a2)])
    rows.append(['<b>%s</b>' % t('soma'), '', '<b>%s</b>' % V['g1_car_soma'], '<b>%s</b>' % V['g2_car_soma'], '<b>%s</b>' % V['tot_ha']])
    story += [Spacer(1, 4), tabla(B, rows, [5.6 * cm, 3.0 * cm, 2.1 * cm, 2.1 * cm, 2.2 * cm], V, aligns={2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}, bold_last=True)]
    story += [PageBreak(), figura(B, 'V05_mapa_car_interior', t('v05_cap'), V)]
    # 6 metodo
    story += [PageBreak(), B.sec(6, t('s6_h'))] + [B.P(F(x, V), 'Bull') for x in t('s6_met')]
    story += [Spacer(1, 6), B.callout(t('alcance_lbl'), F(t('alcance'), V))]
    story += [B.P(t('s6_lim_h'), 'H2')] + [B.P(F(x, V), 'Bull') for x in t('s6_lim')]
    # anexo
    story += [PageBreak(), sec_str(B, 'A', t('anexo_h')), B.P(t('anexo_leg_h'), 'H2'), tabla(B, t('anexo_leg'), [4.6 * cm, 4.8 * cm, 5.6 * cm], V)]
    story += [B.P(t('anexo_arq_h'), 'H2'), tabla(B, t('anexo_arq'), [7.2 * cm, 7.8 * cm], V)]
    return B, story


# ------------------------------------------------------------- verificacao ---
def verificar(pdf, V):
    import fitz
    doc = fitz.open(pdf)
    txt = '\n'.join(p.get_text() for p in doc)
    n = len(doc); doc.close()
    txt_pal = re.sub(r'\S*[_/.]\S*', ' ', txt)
    kpis = [V[k] for k in ('g1_ha', 'g2_ha', 'g1_rl_ex', 'g2_rl_ex', 'g1_rl_exist', 'g2_rl_exist', 'g1_rl_def', 'g2_rl_def',
                            'g1_app', 'g2_app', 'g1_app_rec', 'g1_pra', 'g1_appF_rec', 'un_rl_def', 'tot_ha', 'a1_g1', 'a2_g1', 'a3_g1', 'a1_g2',
                            'esp_fbds', 'rl_prop_g1', 'g2_hoje')]
    faltan = [k for k in kpis if k not in txt]
    glifos = [g for g in ['■', '\ufffd', '□', '\u25a0'] if g in txt]
    if LANG == 'es':
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cion', 'sion'))
                          and w.lower() not in ('precision', 'decision', 'vision', 'mision', 'version', 'lesion', 'presion', 'sesion')))
    else:
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cao', 'coes', 'acao'))))
    tam = os.path.getsize(pdf)
    ok = not faltan and not glifos and not pend and 10 <= n <= 18
    log('  VERIFICACAO %s: paginas=%d tam=%.1f MB KPIs faltantes=%s glifos=%s sem_acento=%s => %s' % (
        os.path.basename(pdf), n, tam / 1e6, faltan or 'nenhum', glifos or 'nenhum', pend[:12] or 'nenhuma', 'OK' if ok else 'REVISAR'))
    return ok, n, tam


def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='pt', choices=['pt', 'es'])
    LANG = ap.parse_args().lang
    log('=' * 78); log('an_09_informe_v2 — lang=%s' % LANG); log('=' * 78)
    G, R, V = cifras()
    B, story = construir(G, R, V)
    out = os.path.join(PROYECTO, 'Diagnostico_APP_RL_Fazenda_Santo_Antonio_v2_%s.pdf' % LANG.upper())
    B.build(out, story, cover_title=t('cover_title'), cover_subtitle=t('cover_sub'),
            title='Mata Ciliar e Reserva Legal por Gleba — Fazenda Santo Antônio (v2)')
    log('  -> %s' % out)
    verificar(out, V)


if __name__ == '__main__':
    main()
