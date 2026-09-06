# -*- coding: utf-8 -*-
"""an_14_informe_v3 — parecer tecnico preliminar v3 (marca Pixadvisor, PT e ES).

    python an_14_informe_v3.py --lang pt   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_v3_PT.pdf
    python an_14_informe_v3.py --lang es   -> Diagnostico_APP_RL_Fazenda_Santo_Antonio_v3_ES.pdf

Regra: cada numero sai de 02_ANALISIS/resultados_v3.json (an_12) via o dict V (virgula decimal). Textos em textos_v3.py.
Mapas de 03_MAPAS_V3 (an_13). Ao final: verificacao com PyMuPDF (KPIs, palavras proibidas, glifos WinAnsi, acentos, lusismos, 16-22 paginas).
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, RESULTADOS_JSON, PARAMETROS_LEGALES, ESCENA_ID, leer_json, log   # noqa: E402
from textos_v3 import TXT                                                                                  # noqa: E402

SKILL = r'C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva'
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from pix_branding import Brand, TEAL, LIMA, AZUL, AZUL_D  # noqa: E402
from reportlab.lib.units import cm                        # noqa: E402
from reportlab.platypus import Image, PageBreak, KeepTogether, Spacer, Table, TableStyle  # noqa: E402

LOGO = os.path.join(SKILL, 'assets', 'logo_pix_azulnegro_trim.png')
MAPAS = os.path.join(PROYECTO, '03_MAPAS_V3')
LANG = 'pt'


def t(k):
    return TXT[k][LANG]


def fmt(x, d=2):
    s = f'{float(x):,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


# ------------------------------------------------------------------ cifras ----
def cifras():
    D = leer_json(os.path.join(ANALISIS, 'resultados_v3.json'))
    G = leer_json(os.path.join(ANALISIS, 'resultados_glebas.json'))
    R = leer_json(RESULTADOS_JSON)
    PL = leer_json(PARAMETROS_LEGALES)
    k, A, RL, C, rep, out, veg, g2c = D['kpi'], D['app'], D['reserva_legal'], D['car_existente'], D['represa'], D['outorga'], D['vegetacao'], D['gleba2_cenarios']
    a1 = A['G1']; cur = {c['n']: c for c in D['cursos']['G1']}; cur2 = D['cursos']['G2'][0]
    tb = {r['tema']: r for r in C['tabela']}
    nasc = {n.get('id'): n for n in D['nascentes'] if 'id' in n}
    loc = RL['localizacao_proposta']; f_iat = next(f for f in loc['fragmento_iat_prioridade_A'] if f['fragmento'] == '163756')
    esp = rep['espelho_por_fonte_ha']; cons = RL['variante_conservadora']
    B = g2c['B_imovel_separado_desmembrado_de_maior_4MF']['imovel_de_origem']
    g1 = G['G1']; g2 = G['G2']
    V = dict(
        tot_ha=fmt(k['area_imovel_ha']), g1_ha=fmt(k['area_g1_ha']), g2_ha=fmt(k['area_g2_ha']), g2_alq=fmt(k['g2_alqueires'], 1), mf=str(int(k['mf_ha'])),
        n_mf=fmt(k['n_mf_imovel']), n_mf_g1=fmt(k['n_mf_g1']), n_mf_g2=fmt(k['n_mf_g2']), dist_glebas=fmt(D['imovel']['distancia_entre_glebas_m'], 1), escena_id=ESCENA_ID,
        n_s2=str(rep['n_escenas']['S2_total']), n_s1=str(rep['n_escenas']['S1']),
        # CAR
        car_id=C['cod_imovel'], car_id_curto=C['cod_imovel'][:20] + '…', car_area=fmt(C['area_declarada_ha']), car_cond=C['condicao'].replace('analise', 'análise').replace('notificacao', 'notificação'), car_mf=fmt(C['mod_fiscal_declarado']),
        car_cob=fmt(C['cobertura_g1_pct'], 1), car_solape=fmt(C['solape_com_car_g2_ha']), car_app=fmt(tb['APP']['declarado_ha']), car_app_num=fmt(tb['APP']['declarado_num_area_ha']),
        car_rl=fmt(tb['Reserva Legal averbada']['declarado_ha']), car_veg=fmt(tb['Vegetacao nativa']['declarado_ha']), car_cons=fmt(tb['Area consolidada']['declarado_ha']),
        car_res=fmt(tb['Reservatorio artificial (represa)']['declarado_ha']), car_res2=fmt(tb['Reservatorio na cabeceira do Arroio 2']['declarado_ha']),
        car_g2_id=B['cod_imovel'], car_g2_id_curto=B['cod_imovel'][:20] + '…', car_g2_area=fmt(B['area_ha']), car_g2_mf=fmt(B['mod_fiscal_declarado']), car_g2_cond=B['condicao'].replace('analise', 'análise').replace('notificacao', 'notificação'),
        # APP
        app_un=fmt(k['app_exigivel_imovel_ha']), app_min=fmt(k['app_envolvente_imovel_ha'][0]), app_max=fmt(k['app_envolvente_imovel_ha'][1]),
        app_g1=fmt(k['app_g1_ha']), app_g1_min=fmt(k['app_g1_envolvente_ha'][0]), app_g1_max=fmt(k['app_g1_envolvente_ha'][1]), app_ens=fmt(a1['ensamble_ha']),
        app_g2=fmt(k['app_g2_ha']), app_g2_min=fmt(k['app_g2_envolvente_ha'][0]), app_g2_max=fmt(k['app_g2_envolvente_ha'][1]),
        app_veg_g1=fmt(a1['com_vegetacao_ha']), app_veg_un=fmt(A['imovel']['com_vegetacao_ha']), app_agua=fmt(a1['agua_ha']), app_rec=fmt(a1['a_recompor_ha']),
        app_silv=fmt(a1['a_recompor_silvicultura_ha']), app_pra=fmt(a1['pra_pr']['a_recompor_ha']), app_curso=fmt(a1['curso_ha']), app_curso_un=fmt(G['UNICO']['app']['curso_dagua_ha']),
        app_nasc=fmt(a1['nascente_ha']), pct_conf=fmt(a1['pct_conforme'], 1),
        appF=fmt(a1['cenario_faixa_reservatorio']['app_exigida_g1_ha']), appF_un=fmt(G['UNICO']['app']['cenario_fbds_iat']['exigida_ha']), appF_rec=fmt(a1['cenario_faixa_reservatorio']['a_recompor_g1_ha']),
        faixa_add=fmt(a1['cenario_faixa_reservatorio']['faixa_adicional_ha']), appF_delta=fmt(a1['cenario_faixa_reservatorio']['delta_recompor_ha']),
        arr1_sesgo=fmt(cur[1]['sesgo_ensamble_med_m'], 0), arr1_p90=fmt(cur[1]['sesgo_ensamble_p90_m'], 0), arr1_app=fmt(cur[1]['app30_fbds_ha']), arr1_app_ens=fmt(cur[1]['app30_envolvente_ha'][1]),
        supr_app=fmt(veg['supressao_pos_2008']['app_g1_indicio_ha']), supr_g2=fmt(veg['supressao_pos_2008']['g2_indicio_ha']),
        # RL
        rl_ex=fmt(k['rl_exigida_ha']), rl_g1=fmt(k['rl_parcela_g1_ha']), rl_g2=fmt(k['rl_parcela_g2_ha']), veg=fmt(k['veg_computavel_ha']), veg_min=fmt(RL['vegetacao_computavel_envolvente_ha'][0]),
        veg_max=fmt(RL['vegetacao_computavel_envolvente_ha'][1]), veg_cons=fmt(k['veg_conservador_ha']), veg_cons_min=fmt(cons['envolvente_ha'][0]), veg_cons_max=fmt(cons['envolvente_ha'][1]),
        rl_def=fmt(k['deficit_ha']), rl_def_cons=fmt(k['deficit_conservador_ha']), rem=fmt(RL['remanescente_fora_app_ha']), rem_cons=fmt(RL['remanescente_fora_app_ha'] - (k['veg_computavel_ha'] - k['veg_conservador_ha'])),
        rem_ponta=fmt(G['UNICO']['reserva_legal']['remanescente_fora_app_ha']), veg_ponta=fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_computavel_ha']),
        rl_def_ponta=fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['deficit_ha']), rl_def_sem_app=fmt(RL['sem_computar_app']['deficit_ha']), pct_rl=fmt(RL['pct_atendido'], 1),
        pct_rl_cons=fmt(100 * k['veg_conservador_ha'] / k['rl_exigida_ha'], 1), rlp_g1=fmt(loc['rl_proposta_recortada_g1_ha']), rlp_falta=fmt(loc['falta_para_exigida_ha']), corr=fmt(loc['corredor_g1_ha']),
        f13=fmt(veg['fragmentos_g1'][1]['ha']), f2_g1=fmt(veg['fragmentos_g1'][0]['ha']), f30=fmt(veg['fragmentos_g1'][2]['ha']), g2_flor=fmt(veg['g2_floresta_na_imagem_nao_computada_ha']),
        iat_in=fmt(f_iat['dentro_ha']), iat_g1=fmt(f_iat['em_G1_ha']), veg08_g2=fmt(g2c['C_excecao_art67_origem_ate_4MF_em_2008']['vegetacao_2008_g2_mapbiomas_ha_indicio']),
        ponta_ymin=fmt(D['gleba2_ponta_norte']['y_min_utm'], 0), ponta_ymax=fmt(D['gleba2_ponta_norte']['y_max_utm'], 0),
        pct_flor_g1=fmt(veg['pct_g1'], 1), f13_min='0,57', f13_max='0,87', b11_f13='0,161', g1_silv=fmt(g1['vegetacao']['silvicultura_ha']), g2_silv=fmt(g2['vegetacao']['silvicultura_ha']),
        g1_agua=fmt(g1['vegetacao']['agua_rf_ha']), g1_agri=fmt(g1['vegetacao']['area_agricola_car_ha']), g2_agri=fmt(g2['vegetacao']['area_agricola_car_ha']),
        g1_car_soma=fmt(g1['mapa_car']['soma_ha']), g2_car_soma=fmt(g2['mapa_car']['soma_ha']),
        # represa / outorga
        esp_min=fmt(k['represa_espelho_atual_ha'][0]), esp_max=fmt(k['represa_espelho_atual_ha'][1]), esp_ref=fmt(rep['espelho_referencia_ha']), esp_fbds=fmt(esp['FBDS 2013 (RapidEye 5 m)']),
        esp_wv2=fmt(esp['IAT WorldView-2 2012']), esp_ana=fmt(esp['ANA massa d agua']), esp_50k=fmt(esp['IAT 1:50k Paranacidade']), esp_car=fmt(esp['CAR declarado']), esp_jrc=fmt(esp['JRC max 1984-2021']),
        esp_mb=fmt(esp['MapBiomas agua 2024']), esp_s1_18=fmt(esp['S1 -18 dB mediana 2024-26']), esp_s1_16=fmt(esp['S1 -16 dB mediana 2024-26']), esp_mndwi=fmt(esp['S2 MNDWI 29/08/2026 (seca)']),
        esp_rf=fmt(esp['RF 29/08/2026 (inclui margem umida)']),
        outorga_port=out['nr_portaria'], outorga_venc='08/11/2025', outorga_pub='09/11/2023', outorga_dist=fmt(out['dist_espelho_fbds_m'], 0),
        # cursos / nascentes
        a1=fmt(cur[1]['fbds_m'], 0), a2=fmt(cur[2]['fbds_m'], 0), a3=fmt(cur[3]['fbds_m'], 0), a1_g2=fmt(cur2['fbds_m'], 0),
        a1_otto=fmt(cur[1]['otto_2020_m'], 0), a1_ana=fmt(cur[1]['ana_5k_m'], 0), a1_ibge=fmt(cur[1]['ibge_bc250_m'], 0), a1_ens=fmt(cur[1]['ensamble_dem_m'], 0),
        a2_otto=fmt(cur[2]['otto_2020_m'], 0), a2_ens=fmt(cur[2]['ensamble_dem_m'], 0), a3_otto=fmt(cur[3]['otto_2020_m'], 0), a3_ana=fmt(cur[3]['ana_5k_m'], 0), a3_ibge=fmt(cur[3]['ibge_bc250_m'], 0), a3_ens=fmt(cur[3]['ensamble_dem_m'], 0),
        km_g1=fmt(k['km_cursos_g1'], 3), km_g1_2=fmt(k['km_cursos_g1'], 2), km_otto=fmt(D['cursos']['km_g1_por_fonte']['otto_2020'], 3), km_ana=fmt(D['cursos']['km_g1_por_fonte']['ANA_5k'], 3),
        km_ibge=fmt(D['cursos']['km_g1_por_fonte']['IBGE_BC250'], 3), km_ens=fmt(D['cursos']['km_g1_por_fonte']['ensamble_DEM'], 3), conflu=fmt(D['cursos']['confluencia_m_fora_limite'], 0),
        nasc_x=fmt(nasc['306158']['x_utm'], 1), nasc_y=fmt(nasc['306158']['y_utm'], 1), dem2_z=fmt(nasc['dem_2']['ndmi_seca_z']), talv=fmt(g1['nascentes']['talvegue_dem_risco_ha']),
        oa=fmt(veg['rf']['OA'], 3), kappa=fmt(veg['rf']['kappa'], 3), f1_silv=fmt(veg['rf']['F1_silvicultura'], 2), flor_sem_cons=fmt(veg['rf']['floresta_fora_consenso_ha']), flor_tot=fmt(veg['rf']['floresta_total_ha']),
    )
    HPJ = leer_json(os.path.join(ANALISIS, 'hidrologia_pro', 'resultados_hidrologia_pro.json'))
    V['res2_dist'] = fmt(HPJ['agua']['represa']['reservatorio_car_partes'][1]['dist_nascente_fbds_m'], 0)
    return D, G, V


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


def tabla(B, rows, widths, V, aligns=None, bold_last=False, fs=None):
    data = [[B.P(F(str(c), V), 'CellB' if i == 0 else 'Cell') for c in r] for i, r in enumerate(rows)]
    tb = B.tbl(data, widths, aligns=aligns)
    if bold_last:
        tb.setStyle(TableStyle([('BACKGROUND', (0, -1), (-1, -1), '#EAF6F4')]))
    return tb


def figura(B, nome, caption, V, max_h=16.0 * cm):
    from PIL import Image as PILImage
    ruta = os.path.join(MAPAS, '' if LANG == 'pt' else 'ES', nome + '.png')
    with PILImage.open(ruta) as im:
        ar = im.size[1] / im.size[0]
    w = B.CONTENT_W; h = w * ar
    if h > max_h:
        h = max_h; w = h / ar
    img = Image(ruta, width=w, height=h); img.hAlign = 'CENTER'
    return KeepTogether([img, Spacer(1, 3), B.P('<i>%s</i>' % F(caption, V), 'Note')])


def h2tab(B, titulo, tb, split=False):
    # split=True so para tabelas longas (cabecalho repetido); o resto fica inteiro com o titulo
    if split:
        return [B.P(titulo, 'H2'), tb]
    return [KeepTogether([B.P(titulo, 'H2'), tb])]


def sec_str(B, num, title):
    head = Table([[B.P(str(num), 'SecNum'), B.P(title, 'SecTitle')]], colWidths=[0.95 * cm, B.CONTENT_W - 0.95 * cm])
    head.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, 0), TEAL), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                              ('LEFTPADDING', (0, 0), (0, 0), 0), ('RIGHTPADDING', (0, 0), (0, 0), 0), ('LEFTPADDING', (1, 0), (1, 0), 10),
                              ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6), ('LINEBELOW', (0, 0), (-1, -1), 2, LIMA)]))
    head._toc = '%s.  %s' % (num, title)
    head.spaceBefore = 14; head.spaceAfter = 8
    return head


# ------------------------------------------------------------------ story -----
def construir(D, G, V):
    B = Brand(logo=LOGO, footer_center=t('footer'), hero_h=7.9 * cm)
    Wc = B.CONTENT_W
    story = []
    # capa + ficha + em uma linha
    story += B.cover_filler()
    story += [B.P(t('ficha_h'), 'H1'), B.hr(), B.meta_table([(F(k_, V), F(v_, V)) for k_, v_ in t('ficha')])]
    story += [Spacer(1, 8), B.callout(t('linha_lbl'), F(t('linha'), V))]
    # indice
    toc = B.toc()
    from reportlab.lib.styles import ParagraphStyle
    from pix_branding import GRIS
    toc.levelStyles = [ParagraphStyle('TL0v3', fontName='Helvetica-Bold', fontSize=9.5, textColor=GRIS, leading=14.5, spaceAfter=1)]
    story += [Spacer(1, 8), B.P(t('indice_h'), 'H1'), B.hr(), toc, PageBreak()]
    # resposta direta
    story += [sec_str(B, 'R', t('rd_h')), B.P(F(t('rd_intro'), V))]
    story += [B.kpi_strip([(F(n, V), F(l, V)) for n, l in t('kpi')]), Spacer(1, 8)]
    story += h2tab(B, t('rd_t1_h'), tabla(B, t('rd_t1'), [3.0 * cm, 3.1 * cm, 8.9 * cm], V))
    story += [Spacer(1, 6)] + h2tab(B, F(t('rd_t2_h'), V), tabla(B, t('rd_t2'), [2.6 * cm, 4.2 * cm, 2.3 * cm, 2.6 * cm, 3.3 * cm], V))
    story += [Spacer(1, 4), B.P(F(t('rd_nota'), V), 'Note')]
    # 1 base legal
    b1 = [B.P(F(x, V), 'Bull') for x in t('s1')]
    story += [Spacer(1, 6), KeepTogether([B.sec(1, t('s1_h')), b1[0]])] + b1[1:]
    # 2 CAR
    story += [Spacer(1, 6), KeepTogether([B.sec(2, t('s2_h')), B.P(F(t('s2_intro'), V))])]
    story += h2tab(B, t('s2_t1_h'), tabla(B, t('s2_t1'), [3.3 * cm, 3.2 * cm, 3.7 * cm, 4.8 * cm], V), split=True)
    story += [Spacer(1, 4), B.P(t('s2_ret_h'), 'H2')] + [B.P(F(x, V), 'Bull') for x in t('s2_ret')]
    story += [Spacer(1, 4), figura(B, 'W06_car_declarado_vs_medido', t('w06_cap'), V)]
    # 3 inventario
    story += [Spacer(1, 6), KeepTogether([B.sec(3, t('s3_h')), B.P(F(t('s3_intro'), V))])]
    story += h2tab(B, t('s3_t1_h'), tabla(B, t('s3_t1'), [2.6 * cm, 1.3 * cm, 1.2 * cm, 1.2 * cm, 1.55 * cm, 1.25 * cm, 5.9 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER', 4: 'CENTER', 5: 'CENTER'}, bold_last=True))
    story += [Spacer(1, 4)] + h2tab(B, t('s3_t2_h'), tabla(B, t('s3_t2'), [2.4 * cm, 2.9 * cm, 5.2 * cm, 4.5 * cm], V))
    story += [Spacer(1, 4)] + h2tab(B, t('s3_t3_h'), tabla(B, t('s3_t3'), [4.6 * cm, 1.6 * cm, 6.5 * cm, 2.3 * cm], V, aligns={1: 'CENTER', 3: 'CENTER'}))
    story += [Spacer(1, 4), B.P(F(t('s3_rep'), V), 'Note')]
    story += [Spacer(1, 4)] + h2tab(B, t('s3_t4_h'), tabla(B, t('s3_t4'), [3.4 * cm, 7.4 * cm, 4.2 * cm], V))
    story += [Spacer(1, 4), figura(B, 'W01_vegetacao_nativa', t('w01_cap'), V)]
    story += [Spacer(1, 4), figura(B, 'W02_hidrografia', t('w02_cap'), V)]
    # 4 APP
    story += [Spacer(1, 6), KeepTogether([B.sec(4, t('s4_h')), B.P(F(t('s4_intro'), V))])]
    story += h2tab(B, t('s4_t1_h'), tabla(B, t('s4_t1'), [6.2 * cm, 2.9 * cm, 2.9 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))
    story += [Spacer(1, 4), B.P(F(t('s4_nota'), V), 'Note')]
    story += [Spacer(1, 4), figura(B, 'W03_app_mata_ciliar', t('w03_cap'), V)]
    # 5 RL
    story += [Spacer(1, 6), KeepTogether([B.sec(5, t('s5_h')), B.P(F(t('s5_intro'), V))])]
    story += h2tab(B, t('s5_t1_h'), tabla(B, t('s5_t1'), [5.4 * cm, 3.3 * cm, 3.3 * cm, 3.0 * cm], V, aligns={1: 'CENTER', 2: 'CENTER', 3: 'CENTER'}))
    story += [Spacer(1, 4), B.P(F(t('s5_nota'), V), 'Note'), Spacer(1, 4), B.P(t('s5_loc_h'), 'H2'), B.P(F(t('s5_loc'), V))]
    story += [Spacer(1, 4), figura(B, 'W04_reserva_legal', t('w04_cap'), V)]
    # 6 Gleba 2
    story += [Spacer(1, 6), KeepTogether([B.sec(6, t('s6_h')), B.P(F(t('s6_intro'), V))]), B.P(t('s6_lim_h'), 'H2'), B.callout('Gleba 2', F(t('s6_lim'), V), bg=AZUL_D)]
    story += [Spacer(1, 4), figura(B, 'W07_gleba2_terra_limpa', t('w07_cap'), V)]
    # 7 CAR/SICAR
    story += [Spacer(1, 6), KeepTogether([B.sec(7, t('s7_h')), B.P(F(t('s7_intro'), V))])]
    rows = [t('s7_t1')]
    U = G['UNICO']['mapa_car']['ha']
    c1 = {(r['classe_car'], r['subclasse']): r['area_ha'] for r in G['G1']['mapa_car']['ha']}
    c2 = {(r['classe_car'], r['subclasse']): r['area_ha'] for r in G['G2']['mapa_car']['ha']}
    for u in U:
        kk = (u['classe_car'], u['subclasse'])
        a1_, a2_ = c1.get(kk, 0.0), c2.get(kk, 0.0)
        rows.append([u['classe_car'], t('car_sub')[u['subclasse']], fmt(a1_), fmt(a2_) if a2_ > 0 else '—', fmt(u['area_ha'])])
    rows.append(['<b>%s</b>' % t('soma'), '', '<b>%s</b>' % V['g1_car_soma'], '<b>%s</b>' % V['g2_car_soma'], '<b>%s</b>' % V['tot_ha']])
    story += [Spacer(1, 4), figura(B, 'W05_mapa_car_sicar', t('w05_cap'), V)]
    story += [Spacer(1, 4), tabla(B, rows, [5.6 * cm, 3.0 * cm, 2.1 * cm, 2.1 * cm, 2.2 * cm], V, aligns={2: 'CENTER', 3: 'CENTER', 4: 'CENTER'}, bold_last=True)]
    # 8 metodo
    b8 = [B.P(F(x, V), 'Bull') for x in t('s8_met')]
    story += [Spacer(1, 6), KeepTogether([B.sec(8, t('s8_h')), b8[0]])] + b8[1:]
    story += [Spacer(1, 4)] + h2tab(B, t('s8_gov_h'), tabla(B, t('s8_gov'), [6.0 * cm, 2.7 * cm, 1.7 * cm, 4.6 * cm], V), split=True)
    story += [Spacer(1, 4), B.P(t('s8_inc_h'), 'H2')] + [B.P(F(x, V), 'Bull') for x in t('s8_inc')]
    # 9 proximos passos
    b9 = [B.P(F(x, V), 'Bull') for x in t('s9')]
    story += [Spacer(1, 6), KeepTogether([B.sec(9, t('s9_h')), b9[0]])] + b9[1:]
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
    kpis = ['12,18', '11,96', '14,00', '2,92', '1,63', '31,55', '17,70', '7,24', '13,85', '24,31', '2,71', '2,45', '143,34', '0,83', '1,23', '157,75', '2,04', '523', '951', '564', '0,976',
            V['app_min'], V['app_max'], V['veg_min'], V['veg_max'], V['rlp_g1'], V['rlp_falta'], V['g2_flor'], V['esp_fbds'], V['esp_car'], V['car_app'], V['car_veg'], V['outorga_port']]
    faltan = [x for x in kpis if x not in txt]
    proib = ['Dictame', 'dictame', 'RL existente', 'RL existent', 'mata do vizinho', 'monte del vecino', '194,53', '+1,00 ha', 'IN IAT 64', 'Director Técnico' if LANG == 'pt' else 'Diretor Técnico', 'Precision' if LANG == 'pt' else '']
    proib = [p for p in proib if p and p in txt]
    # "dispensa" so negada
    disp = [m.group(0) for m in re.finditer(r'.{0,80}dispensa.{0,40}', txt, flags=re.I | re.S)]
    disp_mal = [d for d in disp if not re.search(r'n[aã]o se presume|sem presumir|sin presumir|no se presume|s[oó] cabe|solo cabe|n[aã]o depende|no depende', d, flags=re.I)]
    glifos = [g for g in ['■', '\ufffd', '□', '\u25a0'] if g in txt]
    if LANG == 'es':
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cion', 'sion'))
                          and w.lower() not in ('precision', 'decision', 'vision', 'mision', 'version', 'lesion', 'presion', 'sesion')))
        lus = []
        for w in ('leito', 'floresta', 'laudo', 'nascente', 'nascentes', 'talvegue'):
            for m in re.finditer(r'.{0,40}\b%s\b.{0,40}' % w, txt, flags=re.I):
                ctx = m.group(0)
                if w.startswith('nascente') and ('Nascente ou olho' in ctx or '"nascente"' in ctx or 'Nascente ou olho' in txt[max(0, m.start() - 10):m.end() + 40]):
                    continue
                if w == 'floresta' and ('Floresta Estacional' in ctx or 'Florestal' in ctx or 'floresta' in ctx.lower() and 'Estacional' in ctx):
                    continue
                if w == 'floresta' and re.search(r'Floresta Estacional|Código Florestal|florestal', ctx):
                    continue
                lus.append(ctx.strip().replace('\n', ' '))
    else:
        pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cao', 'coes', 'acao'))))
        lus = [m.group(0).strip() for w in ('sesgo', 'ensamble', 'monte del', 'Director') for m in re.finditer(r'.{0,30}\b%s\b.{0,30}' % w, txt)]
    tam = os.path.getsize(pdf)
    ok = not faltan and not proib and not disp_mal and not glifos and not pend and not lus and 16 <= n <= 22
    log('  VERIFICACAO %s: paginas=%d tam=%.1f MB' % (os.path.basename(pdf), n, tam / 1e6))
    log('    KPIs faltantes=%s' % (faltan or 'nenhum'))
    log('    proibidas=%s · dispensa afirmada=%s' % (proib or 'nenhuma', disp_mal[:3] or 'nenhuma'))
    log('    glifos=%s · sem acento=%s · lusismos/hispanismos=%s' % (glifos or 'nenhum', pend[:12] or 'nenhuma', lus[:6] or 'nenhum'))
    log('    => %s' % ('OK' if ok else 'REVISAR'))
    return ok, n, tam


def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument('--lang', default='pt', choices=['pt', 'es'])
    LANG = ap.parse_args().lang
    log('=' * 78); log('an_14_informe_v3 - lang=%s' % LANG); log('=' * 78)
    D, G, V = cifras()
    B, story = construir(D, G, V)
    out = os.path.join(PROYECTO, 'Diagnostico_APP_RL_Fazenda_Santo_Antonio_v3_%s.pdf' % LANG.upper())
    B.build(out, story, cover_title=t('cover_title'), cover_subtitle=t('cover_sub'),
            title='Mata Ciliar e Reserva Legal - Fazenda Santo Antonio (v3)')
    log('  -> %s' % out)
    verificar(out, V)


if __name__ == '__main__':
    main()
