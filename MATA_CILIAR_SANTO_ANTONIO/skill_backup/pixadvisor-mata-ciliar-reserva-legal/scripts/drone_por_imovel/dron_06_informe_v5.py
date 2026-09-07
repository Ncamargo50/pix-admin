# -*- coding: utf-8 -*-
"""dron_06_informe_v5.py — RELATÓRIO FINAL v5 (pt-BR, 10-14 páginas, A4): mata ciliar (APP) e Reserva Legal,
Fazenda Santo Antônio e Área dos 6 alqueires, DOIS capítulos separados (nada se soma).

Textos: textos_v5.py. Números: SÓ de 06_DRONE_POR_IMOVEL/resultados_v5.json (dron_04). Mapas: dron_05 (06_DRONE_POR_IMOVEL/mapas).
Saída: Relatorio_Final_APP_Reserva_Legal_Santo_Antonio_e_6_Alqueires.pdf (raiz do projeto).

Ao final: (a) verificação com PyMuPDF (números-chave presentes, palavras proibidas, "laudo" só negado, glifos WinAnsi,
acentos, espanhol, 10-14 páginas); (b) render de todas as páginas a PNG (70 dpi) em 06_DRONE_POR_IMOVEL/_relatorio_v5_pXX.png.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dron_00_comun import SALIDA_RAIZ, PROYECTO, leer_json, log      # noqa: E402
from textos_v5 import TXT                                          # noqa: E402

SKILL = r'C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva'
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from pix_branding import Brand, TEAL, LIMA, AZUL, AZUL_D, GRIS_CLR   # noqa: E402
from reportlab.lib.units import cm                                  # noqa: E402
from reportlab.lib.colors import HexColor, white                    # noqa: E402
from reportlab.platypus import Image, PageBreak, KeepTogether, Spacer, Table, TableStyle  # noqa: E402

LOGO = os.path.join(SKILL, 'assets', 'logo_pix_azulnegro_trim.png')
MAPAS = os.path.join(SALIDA_RAIZ, 'mapas')
OUT = os.path.join(PROYECTO, 'Relatorio_Final_APP_Reserva_Legal_Santo_Antonio_e_6_Alqueires.pdf')
VERM = HexColor('#B91C1C'); AMB = HexColor('#B45309'); VERDE = HexColor('#2E7D32')
STATUS_PT = {'Aguardando analise': 'Aguardando análise', 'Analisado, aguardando atendimento a notificacao': 'Analisado, aguardando atendimento à notificação'}


def fmt(x, d=2):
    s = f'{float(x):,.{d}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')


def check_winansi(s, donde=''):
    bad = set()
    for ch in re.sub(r'<[^>]+>', '', s):
        try:
            ch.encode('cp1252')
        except UnicodeEncodeError:
            bad.add(ch)
    if bad:
        raise ValueError('Glifo fora de WinAnsi %r em: %s' % (bad, donde))


def F(s, V):
    out = s.format_map(V)
    check_winansi(out, s[:40])
    return out


def data_br(iso):
    y, m, d = iso.split('-')
    return '%s/%s/%s' % (d, m, y)


# ------------------------------------------------------------------ cifras ----
def cifras():
    res = leer_json(os.path.join(SALIDA_RAIZ, 'resultados_v5.json'))
    sa = res['santo_antonio']; al = res['seis_alqueires']
    k = sa['kpi']; ag = sa['agua']; v = sa['vegetacao_ha']; A = sa['app']['legal_30m_nascente_50m']; P = sa['app']['pra_20m_nascente_15m']
    Rz = sa['app']['legal_mais_faixa_reservatorio_30m']; RL = sa['reserva_legal']; cz = sa['cruzamento_car']; dec = cz['declarado_no_car_inteiro']
    med = cz['medido_drone_v5']; st = cz['status_atual']; o = sa['outorga_sigarh']
    ak = al['kpi']; av = al['vegetacao_ha']; aRL = al['reserva_legal']; acz = al['cruzamento_car']; adec = acz['declarado_no_car_inteiro']; ast = acz['status_atual']
    pn = aRL['ponta_norte_a_conferir']
    # comprimento dos arroios: eixo oficial recortado pelo polígono (medição direta, ver dron_05)
    import geopandas as gpd
    from shapely.ops import unary_union
    from dron_00_comun import imoveis, OFICIAL
    SA = imoveis()['santo_antonio']
    hid = gpd.read_file(OFICIAL['hidro']); hid = hid[hid.fonte == 'FBDS']
    arr = {n: unary_union(hid[hid.id_fonte.astype(str).isin(ids)].geometry).intersection(SA).length for n, ids in {1: ['647524'], 2: ['647525'], 3: ['617192', '647547']}.items()}
    nas = gpd.read_file(OFICIAL['nascentes']); nasc = nas[nas.id_fonte.astype(str) == '306158'].geometry.iloc[0]
    agua = gpd.read_file(os.path.join(SALIDA_RAIZ, 'santo_antonio', 'agua_santo_antonio_2026-05-22.geojson'))
    nasc_dist = nasc.distance(agua[agua.corpo == 'acude_cabeceira_arroio2'].geometry.iloc[0])
    sicar = re.search(r'SICAR (\d{2}/\d{2}/\d{4})', res['_meta']['replica_sicar_iat_data_dos_dados']).group(1)
    V = dict(
        sa_area=fmt(sa['area_poligono_ha']), sa_alq=fmt(sa['alqueires_paulistas_poligono']), sa_mf=fmt(sa['modulos_fiscais'], 1), mf_ha=fmt(sa['mf_ha'], 0),
        al_area=fmt(al['area_poligono_ha']), al_alq=fmt(al['alqueires_paulistas_poligono']), al_inf=fmt(al['area_informada_cliente_ha']),
        cob=fmt(k['cobertura_ortofoto_ha']), sem_cob=fmt(k['sem_cobertura_ha']),
        represa=fmt(ag['represa_ha']), represa_3=fmt(ag['represa_ha'], 3), acude=fmt(ag['acude_cabeceira_ha'], 3), lagoas=fmt(ag['lagoas_menores_ha']),
        car_acude='0,147', nasc_dist=fmt(nasc_dist, 0),
        arborea=fmt(v['arborea_ha']), arbustiva=fmt(v['arbustiva_ha']), pasto=fmt(v['pasto_ha']), lavoura=fmt(v['lavoura_solo_ha']),
        a1=fmt(arr[1], 0), a2=fmt(arr[2], 0), a3=fmt(arr[3], 0),
        app_exig=fmt(A['exigida_ha']), app_veg=fmt(A['com_vegetacao_nativa_ha']), app_agua=fmt(A['agua_ha']), app_rec=fmt(A['a_recompor_ha']), app_sem=fmt(A['sem_cobertura_drone_nao_avaliado_ha']),
        app_rec_lav=fmt(A['a_recompor_por_subclasse_ha']['lavoura_solo']), app_rec_pasto=fmt(A['a_recompor_por_subclasse_ha']['pasto_herbacea']),
        app_pra=fmt(P['a_recompor_ha']), pra_exig=fmt(P['exigida_ha']), rz_exig=fmt(Rz['exigida_ha']), rz_rec=fmt(Rz['a_recompor_ha']),
        rl_exig=fmt(RL['exigida_ha']), rl_veg=fmt(RL['vegetacao_computavel_ha']), rl_def=fmt(RL['deficit_ha']), rl_pct=fmt(RL['pct_atendido'], 1),
        rl_isol=fmt(RL['medido_drone']['arvores_isoladas_nao_computadas_ha']), rl_resto=fmt(RL['deficit_ha'] - A['a_recompor_ha']),
        rl_etapa=fmt(RL['regularizacao_art66']['cronograma_recomposicao_1_10_a_cada_2_anos'][0]['ha_acumulado_minimo']),
        car_cod=cz['car'][:23] + '...', car_status=STATUS_PT.get(st['des_condic'], st['des_condic']), sicar_data=sicar,
        car_area=fmt(dec['area_imovel_ha']), car_rl=fmt(dec['reserva_legal_ha']), car_veg=fmt(dec['vegetacao_nativa_ha']), car_app=fmt(dec['app_total_ha']),
        car_res=fmt(dec['reservatorios_geom_ha']), car_cons=fmt(cz['declarado_DENTRO_do_poligono_deste_imovel_ha']['area_consolidada']),
        med_veg=fmt(med['vegetacao_nativa_ha']), med_agua=fmt(med['reservatorios_agua_aberta_ha']), med_cons=fmt(med['area_antropizada_pasto_lavoura_construcoes_ha']),
        outorga_n=o['nr_portaria'], outorga_venc=data_br(o['vencimento']), outorga_pub=data_br(o['publicacao']),
        al_lav=fmt(av['lavoura_solo_ha']), al_pasto=fmt(av['pasto_ha'], 3), al_mata=fmt(av['arborea_ha'], 3),
        al_rl=fmt(aRL['exigida_ha']), al_veg=fmt(aRL['vegetacao_computavel_ha']),
        al_etapa=fmt(aRL['regularizacao_art66']['cronograma_recomposicao_1_10_a_cada_2_anos'][0]['ha_acumulado_minimo']),
        rl_soma=fmt(RL['exigida_ha'] + aRL['exigida_ha']),
        al_car_cod=acz['car'][:23] + '...', al_car_area=fmt(adec['area_imovel_ha']), al_car_mf=fmt(ast['mod_fiscal_declarado'], 1),
        al_car_status=STATUS_PT.get(ast['des_condic'], ast['des_condic']),
        ponta=fmt(pn['area_ha']), ponta_mata=fmt(pn['mata_medida_ha']), ponta_sem=fmt(pn['sem_cobertura_drone_ha']),
    )
    # coerência (dos JSON, não do texto)
    assert abs(RL['exigida_ha'] - RL['vegetacao_computavel_ha'] - RL['deficit_ha']) < 0.011
    assert abs(A['exigida_ha'] - A['com_vegetacao_nativa_ha'] - A['agua_ha'] - A['a_recompor_ha'] - A['sem_cobertura_drone_nao_avaliado_ha']) < 0.011
    assert o['vencimento'] == '2025-11-08' and o['vencida_em_2026-09-06'] and o['status'] == 'IRREGULAR'
    assert ag['represa_ge_1ha'] is True
    assert abs(arr[1] - 522.8) < 1 and abs(arr[2] - 950.7) < 1 and abs(arr[3] - 564.1) < 1
    assert aRL['vegetacao_computavel_ha'] == 0.0 and al['app']['legal_30m_nascente_50m']['exigida_ha'] == 0.0
    assert res['_meta']['nota_soma'].startswith('os dois imoveis NAO se somam')
    log('  cifras: %d chaves' % len(V))
    return V


# ------------------------------------------------------------------ helpers ---
def tabla(B, rows, widths, V, aligns=None, bold_last=False):
    data = [[B.P(F(str(c), V), 'CellB' if i == 0 else 'Cell') for c in r] for i, r in enumerate(rows)]
    tb = B.tbl(data, widths, aligns=aligns)
    if bold_last:
        tb.setStyle(TableStyle([('BACKGROUND', (0, -1), (-1, -1), HexColor('#EAF6F4'))]))
    return tb


def cor_veredito(v):
    if v.startswith('NÃO ESTÁ') or v.startswith('PRECISA'):
        return '#B91C1C' if v.startswith('NÃO ESTÁ') else '#B45309'
    return '#2E7D32'


def celda_veredito(B, s, V):
    ver, txt = s.split('|', 1)
    return B.P('<b><font color="%s">%s</font></b><br/>%s' % (cor_veredito(ver), F(ver, V), F(txt, V)), 'Cell')


def tabla_resposta(B, V):
    hdr = [B.P(c, 'CellB') for c in TXT['resp_hdr']]
    data = [hdr]
    for perg, sa, al in TXT['resp']:
        data.append([B.P('<b>%s</b>' % F(perg, V), 'Cell'), celda_veredito(B, sa, V), celda_veredito(B, al, V)])
    w = [3.4 * cm, (B.CONTENT_W - 3.4 * cm) / 2, (B.CONTENT_W - 3.4 * cm) / 2]
    tb = B.tbl(data, w)
    tb.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    return tb


def capitulo(B, txt):
    t = Table([[B.P(txt, 'SecTitle')]], colWidths=[B.CONTENT_W])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), GRIS_CLR), ('LINEBEFORE', (0, 0), (0, 0), 5, TEAL), ('LINEBELOW', (0, 0), (-1, -1), 2, LIMA),
                           ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8), ('LEFTPADDING', (0, 0), (-1, -1), 12)]))
    t._toc = txt
    t.spaceAfter = 10
    return t


def figura(B, nome, caption, V, max_h=18.0 * cm):
    from PIL import Image as PILImage
    ruta = os.path.join(MAPAS, nome + '.png')
    tmp = os.path.join(MAPAS, '_jpg'); os.makedirs(tmp, exist_ok=True)
    jpg = os.path.join(tmp, nome + '.jpg')
    with PILImage.open(ruta) as im:
        ar = im.size[1] / im.size[0]
        if not os.path.exists(jpg) or os.path.getmtime(jpg) < os.path.getmtime(ruta):
            im.convert('RGB').save(jpg, 'JPEG', quality=88, optimize=True, dpi=(250, 250))
    w = B.CONTENT_W; h = w * ar
    if h > max_h:
        h = max_h; w = h / ar
    img = Image(jpg, width=w, height=h); img.hAlign = 'CENTER'
    return KeepTogether([img, Spacer(1, 3), B.P(F(caption, V), 'Note')])


# ------------------------------------------------------------------ story -----
def story(B, V):
    t = lambda k: TXT[k]
    P = lambda s: B.P(F(s, V), 'Body')
    st = []
    # capa + ficha + em uma frase
    st += B.cover_filler()
    st += [B.P(F(t('h1'), V), 'H1'), B.P(F(t('h1_sub'), V), 'Note'), B.hr()]
    st += [B.meta_table([(k, F(v, V)) for k, v in t('ficha')]), Spacer(1, 10)]
    st += [B.callout('Em uma frase', F(t('em_uma_frase'), V))]
    # resposta curta
    st += [PageBreak(), B.sec(1, t('s_resp')), P(t('s_resp_intro')), Spacer(1, 2)]
    st += [B.P(F(t('kpi_sa_titulo'), V), 'H2'), B.kpi_strip([(F(n, V), F(l, V)) for n, l in t('kpi_sa')]), Spacer(1, 4)]
    st += [B.P(F(t('kpi_al_titulo'), V), 'H2'), B.kpi_strip([(F(n, V), F(l, V)) for n, l in t('kpi_al')]), Spacer(1, 8)]
    st += [tabla_resposta(B, V)]
    # ---------------- capítulo 1
    st += [PageBreak(), capitulo(B, 'Capítulo 1 · ' + F(t('cap1'), V))]
    st += [B.sec(2, t('s1'))] + [P(s) for s in t('s1_txt')]
    st += [tabla(B, [t('inv_hdr')] + list(t('inv')), [4.0 * cm, B.CONTENT_W - 4.0 * cm], V), Spacer(1, 6)]
    st += [B.sec(3, t('s2'))] + [P(s) for s in t('s2_txt')]
    st += [tabla(B, [t('app_hdr')] + list(t('app_tab')), [B.CONTENT_W - 2.6 * cm, 2.6 * cm], V, aligns={1: 'RIGHT'}, bold_last=False)]
    st += [PageBreak(), figura(B, 'SA1_fazenda_vista_pelo_drone', t('sa1_cap'), V, max_h=21.0 * cm)]
    st += [PageBreak(), figura(B, 'SA2_mata_beira_rios_app', t('sa2_cap'), V, max_h=21.0 * cm)]
    st += [PageBreak(), B.sec(4, t('s3'))] + [P(s) for s in t('s3_txt')]
    st += [tabla(B, [t('rl_hdr')] + list(t('rl_tab')), [B.CONTENT_W - 2.6 * cm, 2.6 * cm], V, aligns={1: 'RIGHT'}), Spacer(1, 6)]
    st += [B.sec(5, t('s4'))] + [P(s) for s in t('s4_txt')]
    st += [tabla(B, [t('car_hdr')] + list(t('car_tab')), [3.8 * cm, 3.2 * cm, B.CONTENT_W - 7.0 * cm], V), Spacer(1, 4)]
    st += [P(s) for s in t('s4_fim')]
    st += [PageBreak(), figura(B, 'SA3_reserva_legal', t('sa3_cap'), V, max_h=21.0 * cm)]
    st += [PageBreak(), figura(B, 'SA4_car_vs_drone', t('sa4_cap'), V, max_h=21.0 * cm)]
    st += [PageBreak(), B.sec(6, t('s5'))] + [P(s) for s in t('s5_txt')]
    st += [Spacer(1, 4), figura(B, 'SA5_represa_acude_nascente_perto', t('sa5_cap'), V, max_h=13.0 * cm)]
    # ---------------- capítulo 2
    st += [PageBreak(), capitulo(B, 'Capítulo 2 · ' + F(t('cap2'), V))]
    st += [B.sec(7, t('s6'))] + [P(s) for s in t('s6_txt')]
    st += [figura(B, 'AL1_seis_alqueires_drone', t('al1_cap'), V, max_h=14.6 * cm)]
    st += [PageBreak(), B.sec(8, F(t('s7'), V))] + [P(s) for s in t('s7_txt')]
    st += [tabla(B, [t('al_rl_hdr')] + list(t('al_rl_tab')), [B.CONTENT_W - 2.6 * cm, 2.6 * cm], V, aligns={1: 'RIGHT'}), Spacer(1, 6)]
    st += [figura(B, 'AL2_reserva_legal_seis_alqueires', t('al2_cap'), V, max_h=9.2 * cm)]
    st += [PageBreak(), B.sec(9, t('s8'))] + [P(s) for s in t('s8_txt')]
    # ---------------- capítulo 3
    st += [Spacer(1, 6), capitulo(B, 'Capítulo 3 · ' + t('cap3')), P(t('s9_intro'))]
    st += [B.P(F(t('kpi_sa_titulo'), V), 'H2'), tabla(B, [t('passos_hdr')] + list(t('passos_sa')), [6.2 * cm, 3.4 * cm, B.CONTENT_W - 9.6 * cm], V), Spacer(1, 6)]
    st += [KeepTogether([B.P(F(t('kpi_al_titulo'), V), 'H2'), tabla(B, [t('passos_hdr')] + list(t('passos_al')), [6.2 * cm, 3.4 * cm, B.CONTENT_W - 9.6 * cm], V)]), Spacer(1, 6)]
    st += [B.sec(10, t('s10'))] + [P(s) for s in t('s10_txt')]
    st += [Spacer(1, 6), B.callout('O que este relatório NÃO é', F(t('nao_e'), V), bg=AZUL_D), Spacer(1, 10), B.P(F(t('contato'), V), 'Note')]
    return st


# ------------------------------------------------------------------ verificar --
def verificar(pdf, V):
    import fitz
    doc = fitz.open(pdf)
    txt = '\n'.join(p.get_text() for p in doc)
    n = len(doc)
    txt_pal = re.sub(r'\S*[_/.@]\S*', ' ', txt)
    kpis = [V[k] for k in ('sa_area', 'al_area', 'represa_3', 'acude', 'app_exig', 'app_veg', 'app_rec', 'app_pra', 'rl_exig', 'rl_veg', 'rl_def', 'car_rl', 'al_rl',
                           'a1', 'a2', 'a3', 'rz_exig', 'rz_rec', 'car_veg', 'car_area', 'med_veg', 'al_alq', 'rl_soma', 'outorga_n')] + \
        ['08/11/2025', '25/01/2024', '22/05/2026', '06/09/2026', '07/09/2026']
    faltan = [x for x in kpis if x not in txt]
    proib = {}
    for w in ('dispensa', 'dispensada', 'RF', 'CHM', 'MNDWI', 'FBDS', 'DTM', 'DSM', 'envolvente', 'consenso', 'talvegue', 'talweg', 'hacienda', 'arroyo', 'laguna', 'cauce',
              'naciente', 'bosque', 'Sentinel', 'satélite de', 'Gleba', 'gleba', 'del ', ' con ', ' una ', ' las ', ' los ', ' el ', ' y ', 'también', 'hasta', 'pero '):
        pat = r'\b%s\b' % re.escape(w) if w.strip().isalpha() and w == w.strip() else re.escape(w)
        hits = [m.group(0).strip().replace('\n', ' ') for m in re.finditer(r'.{0,30}%s.{0,30}' % pat, txt, flags=re.S)]
        if hits:
            proib[w] = hits[:3]
    laudo = [m.group(0).replace('\n', ' ') for m in re.finditer(r'.{0,25}\blaudo\b.{0,10}', txt, flags=re.I | re.S)]
    laudo_mal = [s for s in laudo if not re.search(r'n[aã]o (é|e|constitui|substitui)( um)? laudo', s, flags=re.I)]
    glifos = [g for g in ['■', '�', '□', '≥', '≤', '→'] if g in txt]
    pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cao', 'coes', 'acao', 'oes')) and w.lower() not in ('shoes',)))
    tam = os.path.getsize(pdf)
    ok = not faltan and not proib and not laudo_mal and not glifos and not pend and 10 <= n <= 14
    log('  VERIFICACAO %s: paginas=%d tam=%.2f MB' % (os.path.basename(pdf), n, tam / 1e6))
    log('    numeros faltantes=%s' % (faltan or 'nenhum'))
    log('    proibidas=%s' % (proib or 'nenhuma'))
    log('    laudo fora de negacao=%s · glifos=%s · sem acento=%s' % (laudo_mal or 'nenhum', glifos or 'nenhum', pend[:12] or 'nenhuma'))
    log('    => %s' % ('OK' if ok else 'REVISAR'))
    for f in os.listdir(SALIDA_RAIZ):
        if f.startswith('_relatorio_v5_p'):
            os.remove(os.path.join(SALIDA_RAIZ, f))
    for i, p in enumerate(doc):
        pix = p.get_pixmap(dpi=70)
        pix.save(os.path.join(SALIDA_RAIZ, '_relatorio_v5_p%02d.png' % (i + 1)))
    doc.close()
    return ok, n, tam


def main():
    log('=' * 70); log('dron_06_informe_v5'); log('=' * 70)
    V = cifras()
    B = Brand(logo=LOGO, footer_left='PIXADVISOR  ·  Agricultura de Precisão', footer_center=TXT['footer'], hero_h=7.4 * cm)
    st = story(B, V)
    B.build(OUT, st, cover_title=TXT['cover_title'], cover_subtitle=TXT['cover_sub'],
            title='Mata ciliar e Reserva Legal - Fazenda Santo Antonio e Area dos 6 alqueires - relatorio final')
    log('PDF -> %s' % OUT)
    verificar(OUT, V)


if __name__ == '__main__':
    main()
