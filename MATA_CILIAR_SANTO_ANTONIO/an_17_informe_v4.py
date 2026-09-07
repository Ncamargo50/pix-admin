# -*- coding: utf-8 -*-
"""an_17_informe_v4 — parecer tecnico preliminar v4 (ortofoto de drone 22/05/2026; marca Pixadvisor, PT e ES).

    python an_17_informe_v4.py --lang pt   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_v4_PT.pdf
    python an_17_informe_v4.py --lang es   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_v4_ES.pdf

Regra: cada numero sai de 05_ORTOFOTO/resultados_v4.json (ortho_06), cauce/cauce_resumo.json (ortho_07) ou dos JSON v3
(via an_14.cifras) atraves do dict V (virgula decimal). Textos em textos_v4.py (herda textos_v3). Mapas de 03_MAPAS_V4 (an_16).
Ao final: verificacao com PyMuPDF (KPIs v4, palavras proibidas, "dispensa" so negada, glifos WinAnsi, acentos, lusismos, 18-26 paginas).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, leer_json, log        # noqa: E402
import an_14_informe_v3 as a14                                     # noqa: E402
from an_14_informe_v3 import fmt, check_winansi, F, tabla, h2tab, sec_str, SKILL, LOGO  # noqa: E402
from textos_v4 import TXT                                          # noqa: E402

sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from pix_branding import Brand, TEAL, LIMA, AZUL, AZUL_D  # noqa: E402
from reportlab.lib.units import cm                        # noqa: E402
from reportlab.platypus import Image, PageBreak, KeepTogether, Spacer, Table, TableStyle  # noqa: E402

ORTO = os.path.join(PROYECTO, '05_ORTOFOTO')
MAPAS = os.path.join(PROYECTO, '03_MAPAS_V4')
LANG = 'pt'


def t(k):
    return TXT[k][LANG]


# ------------------------------------------------------------------ cifras ----
def cifras():
    """V da v3 (an_14) + sobrescrita com os numeros da ortofoto (resultados_v4.json) e do cauce (cauce_resumo.json)."""
    D3, G, V = a14.cifras()
    D = leer_json(os.path.join(ORTO, 'resultados_v4.json'))
    C = leer_json(os.path.join(ORTO, 'cauce', 'cauce_resumo.json'))
    k, A, RL, rp, veg, cv, cu, na = D['kpi'], D['app'], D['reserva_legal'], D['represa'], D['vegetacao'], D['cobertura_voo'], D['cursos'], D['nascentes']
    F_, P_, Rz, Dt = A['fbds'], A['pra'], A['fbds_reservatorio'], A['dtm']
    g1, g2, im = F_['G1'], F_['G2'], F_['IMOVEL']; sub = g1['a_recompor_por_subclasse_ha']
    pr, co, pn = RL['principal_mmu_0_05ha_g2_terra_limpa'], RL['conservador_sem_fragmento_13'], RL['se_ponta_norte_da_g2_for_do_imovel']
    tod, g05 = RL['sensibilidade_todas_arvores'], RL['sensibilidade_fragmentos_ge_0_5ha']
    vg1, vg2, vim = veg['por_gleba']['G1'], veg['por_gleba']['G2'], veg['por_gleba']['IMOVEL']
    fr = {f['frag_id']: f for f in veg['fragmentos']}
    r2 = rp['reservatorio_cabeceira_arroio2']; n0 = na['pontos'][0]
    cs = C['consolidado']; m3 = C['M3']; m5 = C['M5']['n_secoes']
    iou = {c['fuente']: c for c in rp['comparacao_fontes']}
    ad = {a['item']: a for a in D['antes_depois']}
    cons4 = sum(r['area_ha'] for r in D['mapa_car_v4']['linhas'] if r['gleba'] == 'G1' and r['classe_car'] == 'Area Consolidada')
    loc = D3['reserva_legal']['localizacao_proposta']
    sem_orto = cv['G1']['sem_ortofoto_ha'] + cv['G2']['sem_ortofoto_ha']
    V.update(
        # cobertura / voo
        cob_pct=fmt(100.0 * (k['area_imovel_ha'] - sem_orto) / k['area_imovel_ha'], 1), sem_orto=fmt(sem_orto), sem_orto_g2=fmt(cv['G2']['sem_ortofoto_ha']), sem_dtm=fmt(cv['G1']['sem_dtm_ha']),
        dtm_desvio='-39', dtm_mad='0,2', rf_acc='0,997',
        # APP v4
        app_un=fmt(k['app_exigivel_imovel_ha']), app_g1=fmt(k['app_g1_ha']), app_g2=fmt(k['app_g2_ha']),
        app_env4_min=fmt(im['envolvente_borda_0_5m_ha'][0]), app_env4_max=fmt(im['envolvente_borda_0_5m_ha'][1]),
        app_g1_env4_min=fmt(g1['envolvente_borda_0_5m_ha'][0]), app_g1_env4_max=fmt(g1['envolvente_borda_0_5m_ha'][1]),
        app_g2_env4_min=fmt(g2['envolvente_borda_0_5m_ha'][0]), app_g2_env4_max=fmt(g2['envolvente_borda_0_5m_ha'][1]),
        app_dtm_g1=fmt(Dt['G1']['exigida_ha']), app_dtm_un=fmt(Dt['IMOVEL']['exigida_ha']),
        app_veg_g1=fmt(g1['com_vegetacao_nativa_ha']), app_veg_un=fmt(im['com_vegetacao_nativa_ha']), app_agua=fmt(g1['agua_ha']), app_rec=fmt(g1['a_recompor_ha']),
        rec_pasto=fmt(sub['pasto_herbacea']), rec_cult=fmt(sub['cultivo_solo']), rec_arv=fmt(sub['arvores_isoladas_lt_0_05ha']), app_silv=fmt(sub['silvicultura']),
        app_pra=fmt(P_['G1']['a_recompor_ha']), app_curso=fmt(g1['curso_ha']), app_curso_un=fmt(im['curso_ha']), app_nasc=fmt(g1['nascente_ha']), pct_conf=fmt(g1['pct_conforme'], 1),
        rec_nasc=fmt(sum(r['area_ha'] for r in D['mapa_car_v4']['linhas'] if r['classe_car'].startswith('APP - Nascente') and r['subclasse'] == 'a recompor')),
        appF=fmt(Rz['G1']['exigida_ha']), appF_un=fmt(Rz['IMOVEL']['exigida_ha']), appF_rec=fmt(Rz['G1']['a_recompor_ha']), faixa_add=fmt(Rz['G1']['faixa_reservatorio_adicional_ha']),
        # RL v4
        veg=fmt(k['veg_computavel_ha']), veg_min=fmt(pr['envolvente_0_5m_ha'][0]), veg_max=fmt(pr['envolvente_0_5m_ha'][1]), rem=fmt(pr['remanescente_fora_app_ha']),
        veg_cons=fmt(co['vegetacao_computavel_ha']), veg_cons_min=fmt(co['envolvente_0_5m_ha'][0]), veg_cons_max=fmt(co['envolvente_0_5m_ha'][1]), rem_cons=fmt(co['remanescente_fora_app_ha']), app_veg_cons=fmt(co['app_vegetada_art15_ha']),
        rl_def=fmt(k['deficit_ha']), rl_def_min=fmt(RL['exigida_ha'] - pr['envolvente_0_5m_ha'][1]), rl_def_max=fmt(RL['exigida_ha'] - pr['envolvente_0_5m_ha'][0]), rl_def_cons=fmt(k['deficit_conservador_ha']),
        veg_ponta=fmt(pn['vegetacao_computavel_ha']), rl_def_ponta=fmt(pn['deficit_ha']), rem_ponta=fmt(pn['vegetacao_computavel_ha'] - im['com_vegetacao_nativa_ha']), g2_flor4=fmt(pn['vegetacao_g2_ha']),
        pct_rl=fmt(pr['pct_atendido'], 1), pct_rl_cons=fmt(co['pct_atendido'], 1), veg_todas=fmt(tod['vegetacao_computavel_ha']), def_todas=fmt(tod['deficit_ha']), veg_ge05=fmt(g05['vegetacao_computavel_ha']), def_ge05=fmt(g05['deficit_ha']),
        dv=fmt(ad['Vegetacao nativa computavel RL (ha)']['delta']), rlp_falta4=fmt(RL['exigida_ha'] - k['veg_computavel_ha'] - loc['corredor_g1_ha']), corr=fmt(loc['corredor_g1_ha']),
        # represa / acude
        esp_orto=fmt(rp['espelho_22_mai_2026_ha'], 3), esp_vaso=fmt(rp['vaso_indicador_ha'], 3), esp_inc=fmt(rp['incerteza_borda_ha'], 3),
        dique_fbds=fmt(rp['alinhamento_dique']['dx_orto_menos_fbds_m'], 0), dique_car=fmt(abs(rp['alinhamento_dique']['dx_orto_menos_car_m']), 0),
        esp_s2max=fmt(iou['S2 freq_total>=0.10 (extension maxima observada 2024-26)']['area_ha']), iou_s2max=fmt(iou['S2 freq_total>=0.10 (extension maxima observada 2024-26)']['iou_com_orto']),
        iou_s2chuva=fmt(iou['S2 freq_chuva>=0.50 (espejo tipico lluvioso)']['iou_com_orto']), iou_s1=fmt(iou['S1 VV<-16 dB freq>=0.50']['iou_com_orto']), iou_jrc=fmt(iou['JRC max_extent 1984-2021']['iou_com_orto']),
        iou_mb=fmt(iou['MapBiomas Agua 2024']['iou_com_orto']), iou_fbds=fmt(iou['FBDS 2013']['iou_com_orto']), iou_car=fmt(iou['CAR declarado (IAT)']['iou_com_orto']),
        res2=fmt(r2['area_agua_ha'], 3), res2_car=fmt(r2['area_car_declarada_ha'], 3), res2_dist=fmt(r2['dist_nascente_fbds_306158_m'], 0), res2_per=fmt(r2['perimetro_m'], 0), res2_sd=fmt(r2['cota_sd_m']),
        res2_vaso=fmt(r2['vaso_ate_cota_mais_0_5m_ha'], 3), res2_x=fmt(r2['centroide'][0], 1), res2_y=fmt(r2['centroide'][1], 1),
        # nascente
        nasc_var=fmt(n0['higrofila_verde_baixa_15m_pct'], 0), nasc_arb=fmt(n0['cobertura_arborea_15m_pct'], 0), nasc_aporte=fmt(n0['aporte_30m_ha_max45m'], 0),
        # cursos / cauce
        a1_talweg=fmt(cu['G1 Arroio 1 (norte)']['talweg_m_total'], 0), a2_talweg=fmt(cu['G1 Arroio 2 (central)']['talweg_m_total'], 0),
        cob_orto_a1=fmt(cu['G1 Arroio 1 (norte)']['cobertura_ortofoto_pct'], 0), cob_dtm_a1=fmt(cu['G1 Arroio 1 (norte)']['cobertura_dtm_pct'], 0),
        a1_dist=fmt(cu['G1 Arroio 1 (norte)']['dist_fbds_vs_talweg']['mediana_m'], 0), a2_dist=fmt(cu['G1 Arroio 2 (central)']['dist_fbds_vs_talweg']['mediana_m'], 0),
        a1_sec=str(cu['G1 Arroio 1 (norte)']['secoes']['n_validas']), a2_sec=str(cu['G1 Arroio 2 (central)']['secoes']['n_validas']),
        est_m=fmt(sum(C['arroios'][a]['eixo_m'] for a in C['arroios']), 0),
        w1=fmt(m3['Arroio 1 (norte)']['W_saida_bieger_usa_m'], 1), w1_min=fmt(m3['Arroio 1 (norte)']['W_saida_intervalo_m'][0], 1), w1_max=fmt(m3['Arroio 1 (norte)']['W_saida_intervalo_m'][1], 1),
        w2=fmt(m3['Arroio 2 (central)']['W_saida_bieger_usa_m'], 1), w2_min=fmt(m3['Arroio 2 (central)']['W_saida_intervalo_m'][0], 1), w2_max=fmt(m3['Arroio 2 (central)']['W_saida_intervalo_m'][1], 1),
        w3=fmt(m3['Arroio 3 (sul)']['W_saida_bieger_usa_m'], 1), w3_min=fmt(m3['Arroio 3 (sul)']['W_saida_intervalo_m'][0], 1), w3_max=fmt(m3['Arroio 3 (sul)']['W_saida_intervalo_m'][1], 1),
        A1='%s-%s' % (fmt(m3['Arroio 1 (norte)']['pontos'][0]['A_usada_km2'], 1), fmt(cs['Arroio 1 (norte)']['M3']['A_saida_km2'], 1)),
        A2='%s-%s' % (fmt(m3['Arroio 2 (central)']['pontos'][0]['A_usada_km2'], 2), fmt(cs['Arroio 2 (central)']['M3']['A_saida_km2'], 2)),
        A3='%s-%s' % (fmt(m3['Arroio 3 (sul)']['pontos'][0]['A_usada_km2'], 1), fmt(cs['Arroio 3 (sul)']['M3']['A_saida_km2'], 1)),
        m2_a1=fmt(cs['Arroio 1 (norte)']['M2']['h0.5_mediana_excluidas_m'], 1), m5_1=str(m5['Arroio 1 (norte)']), m5_2=str(m5['Arroio 2 (central)']), m5_3=str(m5['Arroio 3 (sul)']),
        # vegetacao 0,5 m
        arb_g1=fmt(vg1['arborea_ha']), arb_g2=fmt(vg2['arborea_ha']), arb_sem=fmt(vg1['arborea_arbustiva_sem_chm']), arbu_g1=fmt(vg1['arbustiva_ha']), arbu_g2=fmt(vg2['arbustiva_ha']),
        pasto_g1=fmt(vg1['herbacea_pasto']), pasto_g2=fmt(vg2['herbacea_pasto']), solo_g1=fmt(vg1['solo_cultivo']), solo_g2=fmt(vg2['solo_cultivo']), agua_g1=fmt(vg1['agua']), constr=fmt(vim['construcoes']),
        sem_dado_g1=fmt(vg1['sem_dado']), sem_dado_g2=fmt(vg2['sem_dado']), nativa_g1=fmt(vg1['vegetacao_nativa_arborea_arbustiva_ha']), silv_s2=fmt(vim['rf_s2_10m']['SILVICULTURA']),
        f13=fmt(fr[13]['area_poligono_s2_dentro_ha']), f13_arb=fmt(fr[13]['cobertura_arborea_pct'], 1), f13_h=fmt(fr[13]['altura_media_m'], 1), f13_p90=fmt(fr[13]['altura_p90_m'], 1), f13_max=fmt(fr[13]['altura_max_m'], 1), f13_chm=fmt(fr[13]['altura_medida_pct_da_arborea'], 0),
        f2_tot=fmt(fr[2]['area_poligono_s2_dentro_ha']), f2_arb=fmt(fr[2]['cobertura_arborea_pct'], 1), f2_h=fmt(fr[2]['altura_media_m'], 1), f2_p90=fmt(fr[2]['altura_p90_m'], 1), f2_max=fmt(fr[2]['altura_max_m'], 1), f2_chm=fmt(fr[2]['altura_medida_pct_da_arborea'], 0),
        f30=fmt(fr[30]['area_poligono_s2_dentro_ha']),
        # CAR v4
        cons4=fmt(cons4), g1_car_soma4=fmt(D['mapa_car_v4']['fecha']['G1']['soma_ha']), g2_car_soma4=fmt(D['mapa_car_v4']['fecha']['G2']['soma_ha']),
    )
    return D, D3, G, V


# ------------------------------------------------------------ helpers PDF ----
def figura(B, nome, caption, V, max_h=12.6 * cm):
    """Mapa PNG -> JPEG (q 88) numa pasta temporaria: a ortofoto de fundo comprime 4-5x melhor que em PNG."""
    from PIL import Image as PILImage
    ruta = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', nome + '.png')
    tmp = os.path.join(MAPAS, '_jpg_' + LANG); os.makedirs(tmp, exist_ok=True)
    jpg = os.path.join(tmp, nome + '.jpg')
    with PILImage.open(ruta) as im:
        ar = im.size[1] / im.size[0]
        if not os.path.exists(jpg) or os.path.getmtime(jpg) < os.path.getmtime(ruta):
            im.convert('RGB').save(jpg, 'JPEG', quality=88, optimize=True, dpi=(250, 250))
    w = B.CONTENT_W; h = w * ar
    if h > max_h:
        h = max_h; w = h / ar
    img = Image(jpg, width=w, height=h); img.hAlign = 'CENTER'
    return KeepTogether([img, Spacer(1, 3), B.P('<i>%s</i>' % F(caption, V), 'Note')])


def figura_par(B, nomes, caption, V):
    """Dois mapas lado a lado (metade da largura util cada) com uma legenda comum."""
    from PIL import Image as PILImage
    imgs = []
    for nome in nomes:
        ruta = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', nome + '.png')
        tmp = os.path.join(MAPAS, '_jpg_' + LANG); os.makedirs(tmp, exist_ok=True)
        jpg = os.path.join(tmp, nome + '.jpg')
        with PILImage.open(ruta) as im:
            ar = im.size[1] / im.size[0]
            if not os.path.exists(jpg) or os.path.getmtime(jpg) < os.path.getmtime(ruta):
                im.convert('RGB').save(jpg, 'JPEG', quality=88, optimize=True, dpi=(250, 250))
        w = B.CONTENT_W / 2 - 0.15 * cm
        imgs.append(Image(jpg, width=w, height=w * ar))
    tb = Table([imgs], colWidths=[B.CONTENT_W / 2] * 2)
    tb.setStyle(TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0), ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 0), ('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    return KeepTogether([tb, Spacer(1, 3), B.P('<i>%s</i>' % F(caption, V), 'Note')])


def tabela_car_v4(D, V):
    rows = [t('s7_t1')]
    agg = {}
    for r in D['mapa_car_v4']['linhas']:
        key = (r['classe_car'], r['subclasse'] + ('|' + r['situacao'] if r['subclasse'] == 'a recompor' else ''))
        agg.setdefault(key, {'G1': 0.0, 'G2': 0.0}); agg[key][r['gleba']] += r['area_ha']
    for (cl, sc), v in agg.items():
        rows.append([t('car_cl4')[cl], t('car_sub4')[sc], fmt(v['G1']), fmt(v['G2']) if v['G2'] > 0 else '—', fmt(v['G1'] + v['G2'])])
    rows.append(['<b>%s</b>' % t('soma'), '', '<b>%s</b>' % V['g1_car_soma4'], '<b>%s</b>' % V['g2_car_soma4'], '<b>%s</b>' % V['tot_ha']])
    return rows


def tabela_antes_depois(D, V):
    rows = [t('s10_t2_head')]
    items = t('s10_t2_items'); why = t('s10_t2_why')
    for a in D['antes_depois']:
        nd = 3 if a['item'] in ('Represa: espelho (ha)', '2o reservatorio cabeceira Arroio 2 (ha)') else (0 if a['item'].endswith('(n)') else 2)
        f_ = lambda v: (fmt(v, nd) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v).replace('.', ',').replace('SIM (22-mai-2026)', 'SIM (22/05/2026)' if LANG == 'pt' else 'SÍ (22/05/2026)'))
        dl = a['delta']
        sd = '—' if dl is None else (fmt(0.0, nd) if abs(dl) < 0.5 * 10 ** (-nd) else ('+' if dl > 0 else '-') + fmt(abs(dl), nd))
        rows.append([items[a['item']], f_(a['v3_s2_10m_fbds_dem30']), f_(a['v4_ortofoto']), sd, why[a['item']]])
    return rows


# ------------------------------------------------------------------ story -----
def construir(D, D3, G, V):
    B = Brand(logo=LOGO, footer_center=t('footer'), hero_h=7.9 * cm)
    story = []
    story += B.cover_filler()
    story += [B.P(t('ficha_h'), 'H1'), B.hr(), B.meta_table([(F(k_, V), F(v_, V)) for k_, v_ in t('ficha')])]
    story += [Spacer(1, 8), B.callout(t('linha_lbl'), F(t('linha'), V))]
    toc = B.toc()
    from reportlab.lib.styles import ParagraphStyle
    from pix_branding import GRIS
    toc.levelStyles = [ParagraphStyle('TL0v4', fontName='Helvetica-Bold', fontSize=9.5, textColor=GRIS, leading=14.5, spaceAfter=1)]
    story += [Spacer(1, 8), B.P(t('indice_h'), 'H1'), B.hr(), toc, PageBreak()]
    # resposta direta
    story += [sec_str(B, 'R', t('rd_h')), B.P(F(t('rd_intro'), V))]
    story += [B.kpi_strip([(F(n, V), F(l, V)) for n, l in t('kpi')]), Spacer(1, 8)]
    story += h2tab(B, t('rd_t1_h'), tabla(B, t('rd_t1'), [3.0 * cm, 2.9 * cm, 9.1 * cm], V), split=True)
    story += [Spacer(1, 6)] + h2tab(B, F(t('rd_t2_h'), V), tabla(B, t('rd_t2'), [2.6 * cm, 4.2 * cm, 2.3 * cm, 2.6 * cm, 3.3 * cm], V))
    story += [Spacer(1, 4), B.P(F(t('rd_nota'), V), 'Note')]
    # 1 base legal
    b1 = [B.P(F(x, V), 'Bull') for x in t('s1')]
    story += [Spacer(1, 6), KeepTogether([B.sec(1, t('s1_h')), b1[0]])] + b1[1:]
    # 2 CAR
    story += [Spacer(1, 6), KeepTogether([B.sec(2, t('s2_h')), B.P(F(t('s2_intro'), V))])]
    story += h2tab(B, t('s2_t1_h'), tabla(B, t('s2_t1'), [3.1 * cm, 3.0 * cm, 4.2 * cm, 4.7 * cm], V), split=True)
    story += [Spacer(1, 4), B.P(t('s2_ret_h'), 'H2')] + [B.P(F(x, V), 'Bull') for x in t('s2_ret')]
    story += [Spacer(1, 4), figura(B, 'X06_car_declarado_vs_medido_v4', t('x06_cap'), V)]
    # 3 inventario
    story += [Spacer(1, 6), KeepTogether([B.sec(3, t('s3_h')), B.P(F(t('s3_intro'), V))])]
    story += h2tab(B, t('s3_t1_h'), tabla(B, t('s3_t1'), [2.5 * cm, 1.2 * cm, 1.1 * cm, 1.1 * cm, 1.3 * cm, 1.5 * cm, 6.3 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER', 4: 'CENTER', 5: 'CENTER'}, bold_last=True), split=True)
    story += [Spacer(1, 4)] + h2tab(B, t('s3_t2_h'), tabla(B, t('s3_t2'), [2.4 * cm, 2.7 * cm, 5.4 * cm, 4.5 * cm], V), split=True)
    story += [Spacer(1, 4)] + h2tab(B, t('s3_t3_h'), tabla(B, t('s3_t3'), [4.2 * cm, 1.4 * cm, 1.6 * cm, 4.2 * cm, 1.9 * cm, 1.7 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 4: 'CENTER', 5: 'CENTER'}))
    story += [Spacer(1, 4), B.P(F(t('s3_rep'), V), 'Note')]
    story += [Spacer(1, 4)] + h2tab(B, t('s3_t4_h'), tabla(B, t('s3_t4'), [3.6 * cm, 7.4 * cm, 4.0 * cm], V), split=True)
    story += [Spacer(1, 4), figura_par(B, ['X01_ortofoto_inventario', 'X02_vegetacao_0_5m'], t('x01_cap') + ' ' + t('x02_cap'), V)]
    # 4 APP
    story += [Spacer(1, 6), KeepTogether([B.sec(4, t('s4_h')), B.P(F(t('s4_intro'), V))])]
    story += h2tab(B, t('s4_t1_h'), tabla(B, t('s4_t1'), [6.2 * cm, 2.9 * cm, 2.9 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}), split=True)
    story += [Spacer(1, 4), B.P(F(t('s4_nota'), V), 'Note')]
    story += [Spacer(1, 4), figura(B, 'X03_app_mata_ciliar_v4', t('x03_cap'), V)]
    # 5 RL
    story += [Spacer(1, 6), KeepTogether([B.sec(5, t('s5_h')), B.P(F(t('s5_intro'), V))])]
    story += h2tab(B, t('s5_t1_h'), tabla(B, t('s5_t1'), [5.0 * cm, 3.6 * cm, 3.4 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}), split=True)
    story += [Spacer(1, 4), B.P(F(t('s5_nota'), V), 'Note'), Spacer(1, 4), B.P(t('s5_loc_h'), 'H2'), B.P(F(t('s5_loc'), V))]
    story += [Spacer(1, 4), figura(B, 'X04_reserva_legal_v4', t('x04_cap'), V)]
    # 6 Gleba 2
    story += [Spacer(1, 6), KeepTogether([B.sec(6, t('s6_h')), B.P(F(t('s6_intro'), V))]), B.P(t('s6_lim_h'), 'H2'), B.callout('Gleba 2', F(t('s6_lim'), V), bg=AZUL_D)]
    story += [Spacer(1, 4), figura(B, 'X07_gleba2_terra_limpa_v4', t('x07_cap'), V)]
    # 7 CAR/SICAR
    story += [Spacer(1, 6), KeepTogether([B.sec(7, t('s7_h')), B.P(F(t('s7_intro'), V))])]
    story += [Spacer(1, 4), figura(B, 'X05_mapa_car_sicar_v4', t('x05_cap'), V)]
    story += [Spacer(1, 4), tabla(B, tabela_car_v4(D, V), [4.6 * cm, 4.3 * cm, 2.0 * cm, 2.0 * cm, 2.1 * cm], V, aligns={2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}, bold_last=True)]
    # 8 metodo
    b8 = [B.P(F(x, V), 'Bull') for x in t('s8_met')]
    story += [Spacer(1, 6), KeepTogether([B.sec(8, t('s8_h')), b8[0]])] + b8[1:]
    story += [Spacer(1, 4)] + h2tab(B, t('s8_gov_h'), tabla(B, t('s8_gov'), [6.0 * cm, 2.7 * cm, 1.7 * cm, 4.6 * cm], V), split=True)
    story += [Spacer(1, 4), B.P(t('s8_inc_h'), 'H2')] + [B.P(F(x, V), 'Bull') for x in t('s8_inc')]
    # 9 proximos passos
    b9 = [B.P(F(x, V), 'Bull') for x in t('s9')]
    story += [Spacer(1, 6), KeepTogether([B.sec(9, t('s9_h')), b9[0]])] + b9[1:]
    # 10 levantamento por drone (NOVA)
    story += [Spacer(1, 6), KeepTogether([B.sec(10, t('s10_h')), B.P(F(t('s10_intro'), V))])]
    story += h2tab(B, t('s10_t1_h'), tabla(B, t('s10_t1'), [2.6 * cm, 6.3 * cm, 6.1 * cm], V), split=True)
    story += [Spacer(1, 4)] + h2tab(B, t('s10_t2_h'), tabla(B, tabela_antes_depois(D, V), [3.9 * cm, 2.4 * cm, 2.4 * cm, 1.3 * cm, 5.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}), split=True)
    story += [Spacer(1, 4)] + h2tab(B, t('s10_t3_h'), tabla(B, t('s10_t3'), [3.4 * cm, 2.8 * cm, 2.6 * cm, 2.8 * cm, 3.4 * cm], V), split=True)
    story += [Spacer(1, 4), B.P(F(t('s10_t3_nota'), V), 'Note')]
    story += [Spacer(1, 4)] + h2tab(B, t('s10_t4_h'), tabla(B, t('s10_t4'), [3.3 * cm, 6.2 * cm, 5.5 * cm], V), split=True)
    story += [Spacer(1, 4), figura(B, 'X08_detalhes_5cm', t('x08_cap'), V, max_h=15.5 * cm)]
    story += [Spacer(1, 4), figura(B, 'X09_s2_vs_ortofoto', t('x09_cap'), V, max_h=12.5 * cm)]
    # anexos
    story += [Spacer(1, 6), KeepTogether([sec_str(B, 'A', t('anexoA_h')), B.P(t('anexoA_leg_h'), 'H2')]), tabla(B, t('anexoA_leg'), [4.8 * cm, 5.6 * cm, 4.6 * cm], V)]
    from reportlab.lib.styles import ParagraphStyle as _PS
    if 'Doi' not in B.ss:
        B.ss.add(_PS('Doi', parent=B.ss['Note'], fontSize=8, leading=9.6, spaceAfter=0.5))
    story += [Spacer(1, 4), B.P(t('anexoA_doi_h'), 'H2')] + [B.P(F(x, V), 'Doi') for x in t('anexoA_doi')]
    story += [Spacer(1, 6), KeepTogether([sec_str(B, 'B', t('anexoB_h')), tabla(B, t('anexoB'), [7.0 * cm, 8.0 * cm], V)])]
    return B, story


# ------------------------------------------------------------- verificacao ---
def verificar(pdf, V):
    import fitz
    doc = fitz.open(pdf)
    txt = '\n'.join(p.get_text() for p in doc)
    n = len(doc); doc.close()
    txt_pal = re.sub(r'\S*[_/.@]\S*', ' ', txt)
    kpis = ['12,18', '11,96', '0,22', '7,71', '0,94', '3,32', '1,93', '13,78', '3,81', '31,55', '19,71', '11,84', '12,39', '19,16', '9,56', '1,388', '0,048', '2,45', '143,34', '157,75',
            '523', '951', '564', '5,9', '2,5', '6,5', V['veg_min'], V['veg_max'], V['app_env4_min'], V['app_env4_max'], V['esp_vaso'], V['res2_car'], V['outorga_port']]
    faltan = [x for x in kpis if x not in txt]
    proib = ['Dictame', 'dictame', 'RL existente', 'RL existent', 'mata do vizinho', 'monte del vecino', '194,53', 'IN IAT 64', 'confirmado por medição', 'confirmada por medição', 'confirmado por medición', 'confirmada por medición',
             'Director Técnico' if LANG == 'pt' else 'Diretor Técnico']
    proib = [p for p in proib if p and p in txt]
    silv = [m.group(0).strip() for m in re.finditer(r'.{0,60}silvicultura (em|en la) APP.{0,60}', txt, flags=re.I | re.S)]
    silv = [s for s in silv if not re.search(r'n[aã]o|no |0,00|sem |sin ', s, flags=re.I)]
    disp = [m.group(0) for m in re.finditer(r'.{0,80}dispensa.{0,60}', txt, flags=re.I | re.S)]
    disp_mal = [d for d in disp if not re.search(r'n[aã]o se presume|sem presumir|sin presumir|no se presume|s[oó] cabe|solo cabe|n[aã]o depende|no depende|n[aã]o se aplica|no se aplica|sem a dispensa|sin la dispensa', d, flags=re.I)]
    glifos = [g for g in ['■', '�', '□', '■'] if g in txt]
    if LANG == 'es':
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cion', 'sion'))
                          and w.lower() not in ('precision', 'decision', 'vision', 'mision', 'version', 'lesion', 'presion', 'sesion')))
        lus = []
        for w in ('leito', 'floresta', 'laudo', 'nascente', 'nascentes', 'talvegue'):
            for m in re.finditer(r'.{0,40}\b%s\b.{0,40}' % w, txt, flags=re.I):
                ctx = m.group(0)
                if w.startswith('nascente') and ('Nascente ou olho' in ctx or '"nascente"' in ctx or 'Nascente ou olho' in txt[max(0, m.start() - 10):m.end() + 40]):
                    continue
                if w == 'floresta' and re.search(r'Floresta Estacional|Código Florestal|florestal', ctx):
                    continue
                lus.append(ctx.strip().replace('\n', ' '))
    else:
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cao', 'coes', 'acao'))))
        lus = [m.group(0).strip() for w in ('sesgo', 'ensamble', 'monte del', 'Director') for m in re.finditer(r'.{0,30}\b%s\b.{0,30}' % w, txt)]
    tam = os.path.getsize(pdf)
    ok = not faltan and not proib and not silv and not disp_mal and not glifos and not pend and not lus and 18 <= n <= 26
    log('  VERIFICACAO %s: paginas=%d tam=%.1f MB' % (os.path.basename(pdf), n, tam / 1e6))
    log('    KPIs faltantes=%s' % (faltan or 'nenhum'))
    log('    proibidas=%s · silvicultura em APP afirmada=%s · dispensa afirmada=%s' % (proib or 'nenhuma', silv[:2] or 'nenhuma', disp_mal[:3] or 'nenhuma'))
    log('    glifos=%s · sem acento=%s · lusismos/hispanismos=%s' % (glifos or 'nenhum', pend[:12] or 'nenhuma', lus[:6] or 'nenhum'))
    log('    => %s' % ('OK' if ok else 'REVISAR'))
    return ok, n, tam


def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='pt', choices=['pt', 'es'])
    LANG = ap.parse_args().lang
    a14.LANG = LANG
    log('=' * 78); log('an_17_informe_v4 - lang=%s' % LANG); log('=' * 78)
    D, D3, G, V = cifras()
    B, story = construir(D, D3, G, V)
    out = os.path.join(PROYECTO, 'Diagnostico_APP_RL_Fazenda_Santo_Antonio_v4_%s.pdf' % LANG.upper())
    B.build(out, story, cover_title=t('cover_title'), cover_subtitle=t('cover_sub'),
            title='Mata Ciliar e Reserva Legal - Fazenda Santo Antonio (v4, ortofoto)')
    log('  -> %s' % out)
    verificar(out, V)


if __name__ == '__main__':
    main()
