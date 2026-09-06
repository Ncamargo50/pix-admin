# -*- coding: utf-8 -*-
"""an_05_informe — relatorio PDF de diagnostico APP / RL / vegetacao nativa (marca Pixadvisor).

    python an_05_informe.py --lang pt   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_PT.pdf
    python an_05_informe.py --lang es   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_ES.pdf

Regla: cada numero del PDF sale de 02_ANALISIS/resultados_analisis.json, de
legislacion/parametros_legales.json o de serie_ndvi_fragmentos_24m.json, via el dict V
(cifras ya formateadas con coma decimal). Los textos viven en textos_informe.py.
Al final se extrae el texto con PyMuPDF y se comprueban KPIs, glifos y paginas.
"""
import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, RESULTADOS_JSON, PARAMETROS_LEGALES, leer_json, log  # noqa: E402
from textos_informe import TXT                                                                  # noqa: E402

SKILL = r'C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva'
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from pix_branding import Brand, TEAL, LIMA, AZUL, GRIS_MED  # noqa: E402
from reportlab.lib.units import cm                          # noqa: E402
from reportlab.platypus import Image, PageBreak, KeepTogether, Spacer, Table, TableStyle  # noqa: E402
from reportlab.lib.styles import ParagraphStyle             # noqa: E402

LOGO = os.path.join(SKILL, 'assets', 'logo_pix_azulnegro_trim.png')
MAPAS = os.path.join(PROYECTO, '03_MAPAS')
LANG = 'pt'


def t(k):
    return TXT[k][LANG]


def fmt(x, d=2):
    s = f'{float(x):,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


# ------------------------------------------------------------------ cifras ----
def cifras():
    R = leer_json(RESULTADOS_JSON)
    PL = leer_json(PARAMETROS_LEGALES)
    S = leer_json(os.path.join(ANALISIS, 'serie_ndvi_fragmentos_24m.json'))
    H, Vg, L = R['hidrografia'], R['vegetacao'], R['legal']
    A, C, RL, P = L['app_total_exigivel'], L['area_consolidada_app'], L['reserva_legal'], L['reserva_legal']['proposta']
    rf = Vg['rf']; cob = Vg['cobertura_propriedade']; pf = cob['por_fonte_ha']; mud = Vg['mudanca_2008_2025']
    r1, r2 = L['reservatorio_artificial']['lista']
    tf = H['tabla_fontes_propriedade']; des = H['desacordo_fontes_vs_fbds']
    f = {x['frag_id']: x for x in Vg['fragmentos']['lista']}
    ser = S['serie']
    f13 = [r['frag13_ribeira'] for r in ser]; f2 = [r['frag2_mata_antiga'] for r in ser]
    V = dict(
        imovel_ha=fmt(L['imovel_ha']), pol1=fmt(PL['poligonos_ha'][0]), pol2=fmt(PL['poligonos_ha'][1]),
        mf=str(PL['modulo_fiscal_ha']), n_mf=fmt(PL['n_modulos']), escena_data='29/08/2026', escena_id=R['_meta']['escena'],
        app_ha=fmt(A['ha']), app_min=fmt(A['ha_min']), app_max=fmt(A['ha_max']), app_veg=fmt(A['com_vegetacao_nativa_ha']),
        app_agua=fmt(A['agua_ha']), app_rec=fmt(A['sem_vegetacao_ha']), app_silv=fmt(A['sem_vegetacao_silvicultura_ha']),
        pct_conf=fmt(A['pct_conforme'], 1), pct_conf_agua=fmt(A['pct_conforme_incl_agua'], 1),
        app_curso=fmt(L['app_curso_dagua_ate10m']['ha']), app_curso_min=fmt(L['app_curso_dagua_ate10m']['ha_min_20m']),
        app_curso_max=fmt(L['app_curso_dagua_ate10m']['ha_max_43m']), app_curso_borda=fmt(L['app_curso_dagua_ate10m']['ha_borda_calha_33m']),
        dem_ctrl=fmt(L['app_curso_dagua_ate10m']['controle_dem_ha']), iou=fmt(L['app_curso_dagua_ate10m']['iou_fbds_dem'], 2),
        app_nasc=fmt(L['app_nascente']['ha']), app_nasc_min=fmt(L['app_nascente']['ha_min_40m']), app_nasc_max=fmt(L['app_nascente']['ha_max_60m']),
        cand_app=fmt(L['app_nascente']['candidatas_dem']['ha_app_50m']), cand_add=fmt(L['app_nascente']['candidatas_dem']['ha_adicional_fora_app_exigivel']),
        consol=fmt(C['consolidada_elegivel_61A_ha']), supr08=fmt(C['supressao_pos_2008_ha']),
        cenA=fmt(C['cenario_A_integral_ha']), cenA_min=fmt(C['cenario_A_min_ha']), cenA_max=fmt(C['cenario_A_max_ha']),
        cenB=fmt(C['cenario_B_pra_ha']), cenB_borda=fmt(C['cenario_B_pra_borda_calha_23m_ha']), cenB_cons=fmt(C['cenario_B_consolidada_na_faixa_ha']),
        cenB_exc=fmt(C['cenario_B_excedente_mantido_ha']),
        floresta2013=fmt(A['fbds_2013']['floresta_2013_dentro_da_nossa_app_ha']), app_fbds2013=fmt(A['fbds_2013']['app_hidrica_fbds_dentro_ha']),
        rl_ex=fmt(RL['exigida_ha']), rl_rem=fmt(RL['remanescente_fora_app_ha']), rl_disp_sem=fmt(RL['disponivel_sem_app_ha']),
        rl_disp_com=fmt(RL['disponivel_com_app_art15_ha']), rl_def_sem=fmt(RL['deficit_sem_app_ha']), rl_def_com=fmt(RL['deficit_com_app_art15_ha']),
        rl_cons_rem=fmt(RL['variante_conservadora_floresta_com_historico']['remanescente_fora_app_ha']),
        rl_cons_app=fmt(RL['variante_conservadora_floresta_com_historico']['app_com_vegetacao_ha']),
        rl_cons_def=fmt(RL['variante_conservadora_floresta_com_historico']['deficit_com_app_art15_ha']),
        rl_prop=fmt(P['ha']), rl_prop_app=fmt(P['app_incluida_ha']), rl_prop_app_veg=fmt(P['app_vegetada_ha']),
        rl_prop_app_rec=fmt(P['app_a_recompor_incluida_ha']), rl_corr=fmt(P['corredor_recomposicao_ha']),
        flor_rf=fmt(cob['floresta_rf_ha']), flor_inc=fmt(cob['floresta_incerteza_ha']), flor_min=fmt(cob['floresta_min_ha']), flor_max=fmt(cob['floresta_max_ha']),
        km_fbds=fmt(tf['FBDS']['km_dentro_propriedade']), km_otto=fmt(tf['otto']['km_dentro_propriedade'], 3), km_ana=fmt(tf['ANA']['km_dentro_propriedade'], 3),
        km_ibge=fmt(tf['IBGE']['km_dentro_propriedade'], 3), km_dem=fmt(tf['DEM']['km_dentro_propriedade'], 3),
        dif_otto=fmt(des['otto']['dif_vs_fbds_km'], 3), dif_ana=fmt(des['ANA']['dif_vs_fbds_km'], 3), dif_ibge=fmt(des['IBGE']['dif_vs_fbds_km'], 3),
        dif_dem='+' + fmt(des['DEM']['dif_vs_fbds_km'], 3),
        km_perene=fmt(H['regime']['km_fbds_dentro_perene']), km_nc=fmt(H['regime']['km_fbds_dentro_nao_classificado']),
        med_dem=fmt(H['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_mediana_m'], 1),
        p90_dem=fmt(H['dem']['consistencia_fbds_vs_dem_global_propriedade']['dist_p90_m'], 1),
        pct30=fmt(H['dem']['consistencia_fbds_vs_dem_global_propriedade']['pct_dentro_30m'], 1),
        r1_fbds=fmt(r1['espelho_fbds_2013_ha']), r1_mndwi=fmt(r1['espelho_s2_mndwi_2026_ha']), r1_rf=fmt(r1['espelho_rf_agua_2026_ha']),
        r1_jrc=fmt(r1['jrc_occurrence_media'], 1), r1_c30=fmt(r1['cenario_30m_ha']), r1_add=fmt(r1['cenario_30m_adicional_fora_app_ha']),
        r2_fbds=fmt(r2['espelho_fbds_2013_ha']), r2_mndwi=fmt(r2['espelho_s2_mndwi_2026_ha']), r2_rf=fmt(r2['espelho_rf_agua_2026_ha']),
        r2_jrc=fmt(r2['jrc_occurrence_media'], 1), r2_c30=fmt(r2['cenario_30m_ha']), r2_add=fmt(r2['cenario_30m_adicional_fora_app_ha']),
        res_add30=fmt(L['reservatorio_artificial']['cenario_30m_adicional_fora_app_total_ha']),
        oa=fmt(rf['OA'], 3), kappa=fmt(rf['kappa'], 3), n_tot=fmt(rf['n_muestras'], 0),
        n_flor=fmt(rf['muestras_por_clase']['FLORESTA_NATIVA'], 0), n_agua=fmt(rf['muestras_por_clase']['AGUA'], 0),
        n_antr=fmt(rf['muestras_por_clase']['AREA_ANTROPIZADA'], 0), n_silv=fmt(rf['muestras_por_clase']['SILVICULTURA'], 0),
        f1_flor=fmt(rf['F1']['FLORESTA_NATIVA'], 3), f1_agua=fmt(rf['F1']['AGUA'], 3), f1_antr=fmt(rf['F1']['AREA_ANTROPIZADA'], 3), f1_silv=fmt(rf['F1']['SILVICULTURA'], 2),
        pa_flor=fmt(rf['productor_acc']['FLORESTA_NATIVA'], 3), pa_agua=fmt(rf['productor_acc']['AGUA'], 3), pa_antr=fmt(rf['productor_acc']['AREA_ANTROPIZADA'], 3), pa_silv=fmt(rf['productor_acc']['SILVICULTURA'], 3),
        ua_flor=fmt(rf['usuario_acc']['FLORESTA_NATIVA'], 3), ua_agua=fmt(rf['usuario_acc']['AGUA'], 3), ua_antr=fmt(rf['usuario_acc']['AREA_ANTROPIZADA'], 3), ua_silv=fmt(rf['usuario_acc']['SILVICULTURA'], 3),
        rf_flor=fmt(pf['RF_10m']['FLORESTA_NATIVA']), rf_agua=fmt(pf['RF_10m']['AGUA']), rf_antr=fmt(pf['RF_10m']['AREA_ANTROPIZADA']), rf_silv=fmt(pf['RF_10m']['SILVICULTURA']),
        mb_ff=fmt(pf['MapBiomas_2025_10m']['Formacao Florestal']), mb_rio=fmt(pf['MapBiomas_2025_10m']['Rio, Lago e Oceano']),
        mb_soja=fmt(pf['MapBiomas_2025_10m']['Soja']), mb_mos=fmt(pf['MapBiomas_2025_10m']['Mosaico de Usos']),
        dw_trees=fmt(pf['DynamicWorld_moda12m']['trees']), dw_water=fmt(pf['DynamicWorld_moda12m']['water']), dw_crops=fmt(pf['DynamicWorld_moda12m']['crops']),
        dw_grass=fmt(pf['DynamicWorld_moda12m']['grass']), dw_built=fmt(pf['DynamicWorld_moda12m']['built']),
        wc_tree=fmt(pf['WorldCover_2021']['Tree cover']), wc_water=fmt(pf['WorldCover_2021']['Permanent water bodies']), wc_crop=fmt(pf['WorldCover_2021']['Cropland']),
        wc_grass=fmt(pf['WorldCover_2021']['Grassland']), wc_built=fmt(pf['WorldCover_2021']['Built-up']),
        fbds_ff=fmt(pf['FBDS_uso_2013']['formacao florestal']), fbds_agua=fmt(pf['FBDS_uso_2013']['agua']), fbds_antr=fmt(pf['FBDS_uso_2013']['area antropizada']),
        mud_persist=fmt(mud['ha_por_classe']['floresta_estavel_2008_2025']), mud_regen=fmt(mud['ha_por_classe']['regeneracao_pos_2008']),
        mud_supr=fmt(mud['ha_por_classe']['supressao_pos_2008']), mud_agua=fmt(mud['ha_por_classe']['agua']), mud_antr=fmt(mud['ha_por_classe']['antropico_estavel']),
        hansen_tot=fmt(mud['hansen']['dentro']['ha_perda_total_2001_2025']), hansen_pos=fmt(mud['hansen']['dentro']['ha_perda_pos_2008']),
        f13_ha=fmt(f[13]['area_dentro_propriedade_ha']), f13_con=fmt(f[13]['glcm_contraste_medio'], 1), f2_con=fmt(f[2]['glcm_contraste_medio'], 1),
        f13_prob=fmt(f[13]['prob_floresta_media'], 2),
        f13_min=fmt(min(f13)), f13_max=fmt(max(f13)), f2_min=fmt(min(f2)), f2_max=fmt(max(f2)),
    )
    return R, PL, V


# ------------------------------------------------------------ helpers PDF ----
def check_winansi(s, donde=''):
    bad = set()
    for ch in re.sub(r'<[^>]+>', '', s):
        try:
            ch.encode('cp1252')
        except UnicodeEncodeError:
            bad.add(ch)
    if bad:
        raise ValueError('glifos fuera de WinAnsi %r en %s: %s' % (sorted(bad), donde, s[:80]))


def F(s, V):
    """Rellena placeholders y verifica glifos."""
    out = s.format_map(V)
    check_winansi(out, s[:30])
    return out


def sec_str(B, num, title):
    """Encabezado de seccion con numero alfanumerico (anexos); entra al TOC."""
    from reportlab.platypus import Paragraph
    head = Table([[B.P(str(num), 'SecNum'), B.P(title, 'SecTitle')]], colWidths=[0.95 * cm, B.CONTENT_W - 0.95 * cm])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), TEAL), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                              ('ALIGN', (0, 0), (0, 0), 'CENTER'), ('LEFTPADDING', (0, 0), (0, 0), 0), ('RIGHTPADDING', (0, 0), (0, 0), 0),
                              ('LEFTPADDING', (1, 0), (1, 0), 10), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                              ('LINEBELOW', (0, 0), (-1, -1), 2, LIMA)]))
    head._toc = '%s.  %s' % (num, title)
    head.spaceBefore = 14; head.spaceAfter = 8
    return head


def tabla(B, rows, widths, V, aligns=None, fs=None):
    data = []
    for i, r in enumerate(rows):
        st = 'CellB' if i == 0 else 'Cell'
        data.append([B.P(F(str(c), V), st) for c in r])
    tb = B.tbl(data, widths, aligns=aligns)
    return tb


def figura(B, nome, caption, V, max_h=21.3 * cm, w=None, sub=''):
    from PIL import Image as PILImage
    ruta = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', sub, nome + '.png')
    with PILImage.open(ruta) as im:
        ar = im.size[1] / im.size[0]
    w = w or B.CONTENT_W
    h = w * ar
    if h > max_h:
        h = max_h; w = h / ar
    img = Image(ruta, width=w, height=h)
    img.hAlign = 'CENTER'
    return KeepTogether([img, Spacer(1, 3), B.P('<i>%s</i>' % F(caption, V), 'Note')])


def figuras_lado(B, nomes, captions, V, w_each=7.3 * cm):
    """Dos figuras lado a lado (detalles norte / sur) con su leyenda debajo."""
    from PIL import Image as PILImage
    imgs, caps = [], []
    for nome, cap in zip(nomes, captions):
        ruta = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', nome + '.png')
        with PILImage.open(ruta) as im:
            ar = im.size[1] / im.size[0]
        imgs.append(Image(ruta, width=w_each, height=w_each * ar))
        caps.append(B.P('<i>%s</i>' % F(cap, V), 'Note'))
    tb = Table([imgs, caps], colWidths=[w_each + 0.2 * cm] * len(imgs))
    tb.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 2), ('RIGHTPADDING', (0, 0), (-1, -1), 2)]))
    return KeepTogether([tb])


def h2tab(B, titulo, tb):
    """Subtitulo + tabla que no se separan (evita H2 huerfano al pie de pagina)."""
    return KeepTogether([B.P(titulo, 'H2'), tb])


def bullets(B, items, V):
    return [B.P(F(x, V), 'Bull') for x in items]


# ------------------------------------------------------------------ story -----
def construir(R, PL, V):
    B = Brand(logo=LOGO, footer_center=t('footer'), hero_h=8.7 * cm)
    W = B.CONTENT_W
    story = []
    story += B.cover_filler()
    story += [B.P(t('ficha_h'), 'H1'), B.hr()]
    story += [B.meta_table([(F(k, V), F(v, V)) for k, v in t('ficha')])]
    story += [Spacer(1, 6), B.callout(t('linha_lbl'), F(t('linha'), V)), PageBreak()]
    # indice
    story += [B.P(t('toc_h'), 'H1'), B.hr(), B.toc(), PageBreak()]
    # resumo executivo
    story += [B.P(t('resumo_h'), 'H1'), B.hr()]
    # el numero grande no lleva unidad (no cabe en la tarjeta): la unidad pasa a la etiqueta
    story += [B.kpi_strip([(F(n, V).replace(' ha', '').replace('%', ''), ('ha · ' if 'ha' in n else '% · ') + F(l, V)) for n, l in t('kpi')]), Spacer(1, 12)]
    story += [figura(B, 'M01_localizacao', t('m01_cap'), V, max_h=16.5 * cm)]
    story += [B.P(t('achados_h'), 'H2')] + bullets(B, t('achados'), V)
    story += [Spacer(1, 8), B.callout(t('reco_lbl'), F(t('reco'), V))]
    # 1 base legal
    story += [B.sec(1, t('s1_h')), B.P(F(t('s1_intro'), V))]
    story += [h2tab(B, t('s1_t1_h'), tabla(B, t('s1_t1'), [5.4 * cm, 3.6 * cm, 6.0 * cm], V))]
    story += [h2tab(B, t('s1_t2_h'), tabla(B, t('s1_t2'), [3.4 * cm, 6.1 * cm, 5.5 * cm], V))]
    story += [Spacer(1, 6), B.P(F(t('s1_aviso'), V), 'Note')]
    # 2 dados e metodo
    story += [KeepTogether([B.sec(2, t('s2_h')), h2tab(B, t('s2_t1_h'), tabla(B, t('s2_t1'), [5.2 * cm, 6.0 * cm, 3.8 * cm], V))])]
    story += [B.P(t('s2_pipe_h'), 'H2')] + [B.P(F(x, V)) for x in t('s2_pipe')]
    story += [h2tab(B, t('s2_rf_h'), tabla(B, t('s2_rf'), [3.4 * cm, 2.2 * cm, 3.4 * cm, 3.0 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}))]
    story += [Spacer(1, 4), B.P(F(t('s2_rf_nota'), V), 'Note')]
    story += [B.P(t('s2_ndvi_h'), 'H2'), B.P(F(t('s2_ndvi'), V)), figura(B, 'G01_serie_ndvi', t('g01_cap'), V)]
    story += [h2tab(B, t('s2_inc_h'), tabla(B, t('s2_inc'), [3.2 * cm, 3.4 * cm, 3.6 * cm, 4.8 * cm], V))]
    story += [Spacer(1, 8), B.callout(t('alcance_lbl'), F(t('alcance'), V))]
    # 3 hidrografia
    story += [PageBreak(), B.sec(3, t('s3_h')), B.P(F(t('s3_intro'), V)), figura(B, 'M02_hidrografia', t('m02_cap'), V, max_h=16.8 * cm)]
    story += [h2tab(B, t('s3_t1_h'), tabla(B, t('s3_t1'), [4.6 * cm, 2.2 * cm, 1.6 * cm, 2.6 * cm, 4.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))]
    story += [Spacer(1, 4), B.P(F(t('s3_consist'), V))]
    story += [B.P(t('s3_nasc_h'), 'H2'), B.P(F(t('s3_nasc'), V))]
    story += [h2tab(B, t('s3_res_h'), tabla(B, t('s3_res'), [2.6 * cm, 1.7 * cm, 1.9 * cm, 1.8 * cm, 1.7 * cm, 2.8 * cm, 2.5 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}))]
    story += [Spacer(1, 4), B.P(F(t('s3_res_nota'), V), 'Note')]
    # 4 vegetacao
    story += [PageBreak(), B.sec(4, t('s4_h')), figura(B, 'M03_vegetacao_nativa_10m', t('m03_cap'), V, max_h=17.5 * cm)]
    story += [h2tab(B, t('s4_t1_h'), tabla(B, t('s4_t1'), [3.6 * cm, 2.6 * cm, 1.8 * cm, 3.0 * cm, 4.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER'}))]
    story += [Spacer(1, 4), B.P(F(t('s4_t1_nota'), V), 'Note')]
    frows = list(t('s4_t2'))
    for fr in R['vegetacao']['fragmentos']['lista']:
        frows.append([str(fr['frag_id']), fmt(fr['area_ha']), fmt(fr['area_dentro_propriedade_ha']), fmt(fr['ndvi_medio'], 3), fmt(fr['ndre_medio'], 3),
                      fmt(fr['prob_floresta_media'], 2), '%s%% / %s%%' % (fmt(100 * fr['frac_floresta_mb_1985'], 0), fmt(100 * fr['frac_floresta_mb_2008'], 0)),
                      fmt(fr['hand_medio_m'], 1) + ' m', t('persist')[fr['frag_id']]])
    story += [h2tab(B, t('s4_t2_h'), tabla(B, frows, [0.9 * cm, 1.4 * cm, 1.5 * cm, 1.2 * cm, 1.2 * cm, 1.4 * cm, 1.8 * cm, 1.2 * cm, 4.4 * cm], V, aligns={i: 'CENTER' for i in range(8)}))]
    story += [Spacer(1, 6), B.P(F(t('s4_frag13'), V))]
    story += [figura(B, 'M04_mudanca_2008_2025', t('m04_cap'), V, max_h=13.5 * cm), Spacer(1, 4), B.P(F(t('s4_mud'), V))]
    # 5 APP
    story += [PageBreak(), B.sec(5, t('s5_h')), B.P(F(t('s5_intro'), V)), figura(B, 'M05_app_conformidade', t('m05_cap'), V, max_h=17.0 * cm)]
    story += [figuras_lado(B, ['M05b_detalhe_norte', 'M05c_detalhe_sul'], [t('m05b_cap'), t('m05c_cap')], V)]
    story += [h2tab(B, t('s5_t1_h'), tabla(B, t('s5_t1'), [4.6 * cm, 2.0 * cm, 8.4 * cm], V, aligns={1: 'CENTER'}))]
    story += [h2tab(B, t('s5_t2_h'), tabla(B, t('s5_t2'), [3.0 * cm, 3.4 * cm, 4.4 * cm, 4.2 * cm], V))]
    story += [Spacer(1, 4), B.P(F(t('s5_nota'), V), 'Note')]
    # 6 RL
    story += [PageBreak(), B.sec(6, t('s6_h')), figura(B, 'M06_reserva_legal_proposta', t('m06_cap'), V, max_h=17.0 * cm)]
    story += [h2tab(B, t('s6_t1_h'), tabla(B, t('s6_t1'), [5.6 * cm, 2.2 * cm, 7.2 * cm], V, aligns={1: 'CENTER'}))]
    story += [Spacer(1, 4), B.P(F(t('s6_prop'), V))]
    story += [B.P(t('s6_alt_h'), 'H2')] + bullets(B, t('s6_alt'), V) + [Spacer(1, 4), B.P(F(t('s6_serv'), V), 'Note')]
    # 7 CAR
    story += [PageBreak(), B.sec(7, t('s7_h')), B.P(F(t('s7_intro'), V)), figura(B, 'M07_mapa_uso_car', t('m07_cap'), V, max_h=17.0 * cm)]
    crows = list(t('s7_t1'))
    U = R['legal']['mapa_uso_car']
    for u in U['ha']:
        crows.append([u['classe_car'], t('car_sub')[u['subclasse']], t('car_sit')[u['situacao']], fmt(u['area_ha']), t('car_nota').get(u['nota'], u['nota'])])
    crows.append(['<b>%s</b>' % t('soma'), '', '', '<b>%s</b>' % fmt(U['soma_ha']), ''])
    story += [Spacer(1, 6), tabla(B, crows, [4.6 * cm, 2.4 * cm, 2.6 * cm, 1.4 * cm, 4.0 * cm], V, aligns={3: 'CENTER'})]
    # 8 limitacoes
    story += [KeepTogether([B.sec(8, t('s8_h')), B.P(t('s8_lim_h'), 'H2')] + bullets(B, t('s8_lim'), V)[:2])] + bullets(B, t('s8_lim'), V)[2:]
    story += [h2tab(B, t('s8_plan_h'), tabla(B, t('s8_plan'), [1.1 * cm, 8.0 * cm, 5.9 * cm], V, aligns={0: 'CENTER'}))]
    # anexos
    story += [KeepTogether([sec_str(B, 'A', t('anexoA_h')), B.P(t('anexoA_leg_h'), 'H2'), tabla(B, t('anexoA_leg')[:3], [4.6 * cm, 4.4 * cm, 6.0 * cm], V)]), tabla(B, [t('anexoA_leg')[0]] + t('anexoA_leg')[3:], [4.6 * cm, 4.4 * cm, 6.0 * cm], V)]
    story += [B.P(t('anexoA_sci_h'), 'H2')] + [B.P('%d. %s' % (i + 1, x), 'Note') for i, x in enumerate(t('anexoA_sci'))]
    story += [KeepTogether([sec_str(B, 'B', t('anexoB_h')), B.P(F(t('anexoB_intro'), V)), tabla(B, t('anexoB')[:3], [6.0 * cm, 9.0 * cm], V)]), tabla(B, [t('anexoB')[0]] + t('anexoB')[3:], [6.0 * cm, 9.0 * cm], V)]
    return B, story


# ------------------------------------------------------------- verificacion ---
def verificar(pdf):
    import fitz
    doc = fitz.open(pdf)
    txt = '\n'.join(p.get_text() for p in doc)
    n = len(doc); doc.close()
    txt_pal = re.sub(r'\S*[_/.]\S*', ' ', txt)   # URLs, rutas y nombres de archivo no cuentan para las tildes
    kpis = ['12,18', '8,10', '2,92', '1,63', '31,55', '20,38', '11,17', '157,75', '2,07 km', '0,976']
    faltan = [k for k in kpis if k not in txt]
    glifos = [g for g in ['■', '\ufffd', '□', '\u25a0'] if g in txt]
    # palabras sin tilde tipicas (ES) / -cao sin til (PT)
    if LANG == 'es':
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cion', 'sion'))
                          and w.lower() not in ('precision', 'decision', 'vision', 'mision', 'version', 'lesion', 'presion', 'sesion')))
    else:
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cao', 'coes', 'acao'))))
    tam = os.path.getsize(pdf)
    ok = not faltan and not glifos and not pend and 14 <= n <= 24
    log('  VERIFICACION %s: paginas=%d tam=%.1f MB KPIs faltantes=%s glifos=%s sin_tilde=%s => %s' % (
        os.path.basename(pdf), n, tam / 1e6, faltan or 'ninguno', glifos or 'ninguno', pend[:12] or 'ninguna', 'OK' if ok else 'REVISAR'))
    return ok, n, tam


def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='pt', choices=['pt', 'es'])
    LANG = ap.parse_args().lang
    log('=' * 78); log('an_05_informe — lang=%s' % LANG); log('=' * 78)
    R, PL, V = cifras()
    B, story = construir(R, PL, V)
    out = os.path.join(PROYECTO, 'Diagnostico_APP_RL_Fazenda_Santo_Antonio_%s.pdf' % LANG.upper())
    B.build(out, story, cover_title=t('cover_title'), cover_subtitle=t('cover_sub'),
            title='Diagnóstico APP / RL — Fazenda Santo Antônio')
    log('  -> %s' % out)
    verificar(out)


if __name__ == '__main__':
    main()
