# -*- coding: utf-8 -*-
"""an_19_resumo_produtor.py — RESUMO PARA O PRODUTOR (pt-BR, 6-10 páginas, A4) do diagnóstico APP / Reserva Legal
da Fazenda Santo Antônio. Textos em textos_produtor.py; números SÓ dos JSON (resultados_v4 / resultados_v3 / cauce_resumo);
mapas simplificados de an_20 (03_MAPAS_PRODUTOR/P1..P5).

Ao final: (a) verificação com PyMuPDF (números presentes, palavras proibidas, glifos WinAnsi, acentos, hispanismos, 6-10 páginas);
(b) renderiza todas as páginas a PNG (dpi 75) em 02_ANALISIS/_resumo_produtor_pXX.png para revisão visual (sem texto sobreposto).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an_00_config import ANALISIS, PROYECTO, leer_json, log      # noqa: E402
from textos_produtor import TXT                                  # noqa: E402

SKILL = r'C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva'
sys.path.insert(0, os.path.join(SKILL, 'scripts'))
from pix_branding import Brand, TEAL, LIMA, AZUL, AZUL_D, GRIS_CLR   # noqa: E402
from reportlab.lib.units import cm                                  # noqa: E402
from reportlab.lib.colors import HexColor, white                    # noqa: E402
from reportlab.platypus import Image, PageBreak, KeepTogether, Spacer, Table, TableStyle  # noqa: E402

LOGO = os.path.join(SKILL, 'assets', 'logo_pix_azulnegro_trim.png')
ORTO = os.path.join(PROYECTO, '05_ORTOFOTO')
MAPAS = os.path.join(PROYECTO, '03_MAPAS_PRODUTOR')
OUT = os.path.join(PROYECTO, 'Resumo_Produtor_APP_Reserva_Legal_Santo_Antonio.pdf')
VERM = HexColor('#B91C1C'); AMB = HexColor('#B45309')


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


# ------------------------------------------------------------------ cifras ----
def cifras():
    v4 = leer_json(os.path.join(ORTO, 'resultados_v4.json'))
    v3 = leer_json(os.path.join(ANALISIS, 'resultados_v3.json'))
    k = v4['kpi']; RL = v4['reserva_legal']; pr = RL['principal_mmu_0_05ha_g2_terra_limpa']; co = RL['conservador_sem_fragmento_13']
    A = v4['app']['fbds']['IMOVEL']; P = v4['app']['pra']['IMOVEL']; rp = v4['represa']; r2 = rp['reservatorio_cabeceira_arroio2']
    cu = v4['cursos']; n0 = v4['nascentes']['pontos'][0]; car = v3['car_existente']; C2 = v3['gleba2_cenarios']['A_imovel_unico_principal']
    f13 = next(f for f in v4['vegetacao']['fragmentos'] if f['frag_id'] == 13)
    cons = {}
    for ln in v4['mapa_car_v4']['linhas']:
        if ln['classe_car'].startswith('Area Consolidada'):
            cons[ln['subclasse']] = cons.get(ln['subclasse'], 0.0) + ln['area_ha']
    cv = v4['cobertura_voo']; sem = cv['G1']['sem_ortofoto_ha'] + cv['G2']['sem_ortofoto_ha']
    tab = {r['tema']: r for r in car['tabela']}
    V = dict(
        area=fmt(k['area_imovel_ha']), mf=fmt(v4['imovel']['n_mf'], 1), mf_ha=fmt(v4['imovel']['mf_ha'], 0),
        g1=fmt(v3['kpi']['area_g1_ha']), g2=fmt(v3['kpi']['area_g2_ha']), g2_alq=fmt(v3['kpi']['g2_alqueires'], 1),
        cob_pct=fmt(100.0 * (k['area_imovel_ha'] - sem) / k['area_imovel_ha'], 1),
        app_exig=fmt(A['exigida_ha']), app_veg=fmt(A['com_vegetacao_nativa_ha']), app_agua=fmt(A['agua_ha']), app_rec=fmt(A['a_recompor_ha']), app_pra=fmt(P['a_recompor_ha']),
        rl_exig=fmt(RL['exigida_ha']), rl_veg=fmt(pr['vegetacao_computavel_ha']), rl_def=fmt(pr['deficit_ha']), rl_def_cons=fmt(co['deficit_ha']),
        rl_def_ponta=fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['deficit_ha']), ponta=fmt(RL['se_ponta_norte_da_g2_for_do_imovel']['vegetacao_g2_ha']),
        g1_rl=fmt(C2['rl_parcela_g1_ha']), g2_rl=fmt(C2['rl_parcela_g2_ha']),
        represa=fmt(rp['espelho_22_mai_2026_ha']), acude=fmt(r2['area_agua_ha'], 3), outorga_venc='08/11/2025', nasc_dist=fmt(n0['dist_agua_aberta_m'], 0),
        a1=fmt(cu['G1 Arroio 1 (norte)']['fbds_m'], 0), a2=fmt(cu['G1 Arroio 2 (central)']['fbds_m'], 0), a3=fmt(cu['G1 Arroio 3 (sul)']['fbds_m'], 0),
        lavoura=fmt(cons.get('uso agricola', 0.0), 0), pasto=fmt(cons.get('pasto/herbacea', 0.0), 0),
        car_cod=car['cod_imovel'][:20] + '...', car_area=fmt(car['area_declarada_ha']), car_rl=fmt(tab['Reserva Legal averbada']['declarado_ha']),
        car_veg=fmt(tab['Vegetacao nativa']['declarado_ha']), car_represa=fmt(tab['Reservatorio artificial (represa)']['declarado_ha']),
        car_acude=fmt(r2['area_car_declarada_ha']),
        f13=fmt(f13['area_poligono_s2_dentro_ha']), f13_h50=fmt(f13['altura_p50_m'], 0), f13_h90=fmt(f13['altura_p90_m'], 0),
    )
    # coerência (dos JSON, não do texto)
    assert abs(v3['kpi']['area_g1_ha'] + v3['kpi']['area_g2_ha'] - k['area_imovel_ha']) < 0.011
    assert abs(C2['rl_parcela_g1_ha'] + C2['rl_parcela_g2_ha'] - RL['exigida_ha']) < 0.011
    assert abs(RL['exigida_ha'] - pr['vegetacao_computavel_ha'] - pr['deficit_ha']) < 0.011
    assert v3['outorga']['dt_vencimento'] == '2025-11-08' and v3['outorga']['vencida']
    assert rp['ge_1ha'] is True
    return V


# ------------------------------------------------------------------ helpers ---
def tabla(B, rows, widths, V, aligns=None, bold_last=False):
    data = [[B.P(F(str(c), V), 'CellB' if i == 0 else 'Cell') for c in r] for i, r in enumerate(rows)]
    tb = B.tbl(data, widths, aligns=aligns)
    if bold_last:
        tb.setStyle(TableStyle([('BACKGROUND', (0, -1), (-1, -1), HexColor('#EAF6F4'))]))
    return tb


def veredito(B, titulo, txt, cor):
    t = Table([[B.P(titulo, 'H2'), B.P('<b>%s</b>' % txt, 'CellB')]], colWidths=[B.CONTENT_W - 4.6 * cm, 4.6 * cm])
    t.setStyle(TableStyle([('BACKGROUND', (1, 0), (1, 0), cor), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                           ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('LEFTPADDING', (0, 0), (0, 0), 0)]))
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
    st = []
    st += B.cover_filler()
    st += [B.P(F(t('h1'), V), 'H1'), B.P(F(t('h1_sub'), V), 'Note'), B.hr()]
    st += [B.meta_table([(k, F(v, V)) for k, v in t('ficha')]), Spacer(1, 10)]
    st += [B.callout('Em uma frase', F(t('em_uma_frase'), V))]
    # 1
    st += [PageBreak(), B.sec(1, t('s1')), B.P(F(t('s1_intro'), V), 'Body'), Spacer(1, 4)]
    st += [B.kpi_strip([(F(n, V), F(l, V)) for n, l in t('kpi')]), Spacer(1, 6)]
    w3 = [B.CONTENT_W / 3] * 3
    for titulo, ver, lei, tem, falta in t('itens'):
        cor = VERM if 'NÃO' in ver else AMB
        st += [KeepTogether([veredito(B, F(titulo, V), ver, cor), tabla(B, [t('tab_hdr'), [lei, tem, falta]], w3, V)]), Spacer(1, 6)]
    # 2
    st += [PageBreak(), B.sec(2, t('s2')), B.P(F(t('s2_intro'), V), 'Body')]
    st += [tabla(B, [t('inv_hdr')] + list(t('inv')), [4.6 * cm, B.CONTENT_W - 4.6 * cm], V), Spacer(1, 8)]
    st += [figura(B, 'P1_fazenda_vista_de_cima', t('p1_cap'), V, max_h=13.8 * cm)]
    # 3
    st += [PageBreak(), B.sec(3, t('s3'))]
    st += [B.P(F(s, V), 'Body') for s in t('s3_txt')]
    st += [tabla(B, [t('app_hdr')] + list(t('app_tab')), [B.CONTENT_W - 3 * cm, 3 * cm], V, aligns={1: 'RIGHT'}, bold_last=True), Spacer(1, 6)]
    st += [figura(B, 'P2_falta_mata_beira_rios', t('p2_cap'), V, max_h=13.2 * cm)]
    # 4
    st += [PageBreak(), B.sec(4, t('s4'))]
    st += [B.P(F(s, V), 'Body') for s in t('s4_txt')]
    st += [tabla(B, [t('rl_hdr')] + list(t('rl_tab')), [B.CONTENT_W - 3 * cm, 3 * cm], V, aligns={1: 'RIGHT'}), Spacer(1, 6)]
    st += [figura(B, 'P3_reserva_legal', t('p3_cap'), V, max_h=13.4 * cm)]
    # 5
    st += [PageBreak(), B.sec(5, t('s5'))]
    st += [B.P(F(s, V), 'Body') for s in t('s5_txt')]
    st += [Spacer(1, 4), figura(B, 'P4_seis_alqueires', t('p4_cap'), V, max_h=16.0 * cm)]
    # 6
    st += [PageBreak(), B.sec(6, t('s6'))]
    st += [B.P(F(s, V), 'Body') for s in t('s6_txt')]
    st += [tabla(B, [t('car_hdr')] + list(t('car_tab')), [3.6 * cm, 3.6 * cm, B.CONTENT_W - 7.2 * cm], V), Spacer(1, 6)]
    st += [B.P(F(t('s6_fim'), V), 'Body')]
    # 7
    st += [Spacer(1, 4), B.sec(7, t('s7'))]
    st += [B.P(F(s, V), 'Body') for s in t('s7_txt')]
    st += [PageBreak(), figura(B, 'P5_represa_nascente_perto', t('p5_cap'), V, max_h=13.0 * cm), Spacer(1, 10)]
    st += [B.callout('O que este resumo NÃO é', F(t('nao_e'), V), bg=AZUL_D)]
    # 8
    st += [PageBreak(), B.sec(8, t('s8')), B.P(F(t('s8_intro'), V), 'Body')]
    st += [tabla(B, [t('passos_hdr')] + list(t('passos')), [6.4 * cm, 3.6 * cm, B.CONTENT_W - 10.0 * cm], V), Spacer(1, 10)]
    st += [B.P(F(t('contato'), V), 'Note')]
    return st


# ------------------------------------------------------------------ verificar --
def verificar(pdf, V):
    import fitz
    doc = fitz.open(pdf)
    txt = '\n'.join(p.get_text() for p in doc)
    n = len(doc)
    txt_pal = re.sub(r'\S*[_/.@]\S*', ' ', txt)
    kpis = [V[k] for k in ('area', 'g1', 'g2', 'g2_alq', 'mf', 'app_exig', 'app_veg', 'app_agua', 'app_rec', 'app_pra', 'rl_exig', 'rl_veg', 'rl_def', 'rl_def_cons',
                           'rl_def_ponta', 'ponta', 'g1_rl', 'g2_rl', 'represa', 'acude', 'a1', 'a2', 'a3', 'car_rl', 'car_veg', 'car_represa', 'car_area', 'f13')] + ['08/11/2025', '22/05/2026', '29/08/2026']
    faltan = [x for x in kpis if x not in txt]
    proib = {}
    for w in ('dispensa', 'RF', 'CHM', 'MNDWI', 'envolvente', 'consenso', 'hacienda', 'arroyo', 'laguna', 'cauce', 'naciente', 'bosque', 'talweg', 'talvegue', 'FBDS', 'DTM', 'DSM',
              'art. 61-A', 'art. 12', 'art. 66', 'art. 67', 'Dictame', 'RL existente', 'mata do vizinho', 'confirmado por medição', 'dispensada', 'confirmada por medição'):
        pat = r'\b%s\b' % re.escape(w) if w.isalpha() else re.escape(w)
        hits = [m.group(0).strip().replace('\n', ' ') for m in re.finditer(r'.{0,30}%s.{0,30}' % pat, txt, flags=re.S)]
        if hits:
            proib[w] = hits[:3]
    laudo = [m.group(0).replace('\n', ' ') for m in re.finditer(r'.{0,25}\blaudo\b.{0,10}', txt, flags=re.I | re.S)]
    laudo_mal = [s for s in laudo if not re.search(r'n[aã]o (é|e|constitui|substitui)( um)? laudo', s, flags=re.I)]
    glifos = [g for g in ['■', '�', '□'] if g in txt]
    pend = sorted(set(w for w in re.findall(r'[A-Za-z]{5,}', txt_pal) if w.lower().endswith(('cao', 'coes', 'acao', 'oes'))
                      and w.lower() not in ('shoes',)))
    tam = os.path.getsize(pdf)
    ok = not faltan and not proib and not laudo_mal and not glifos and not pend and 6 <= n <= 10
    log('  VERIFICACAO %s: paginas=%d tam=%.2f MB' % (os.path.basename(pdf), n, tam / 1e6))
    log('    numeros faltantes=%s' % (faltan or 'nenhum'))
    log('    proibidas=%s' % (proib or 'nenhuma'))
    log('    laudo fora de negacao=%s · glifos=%s · sem acento=%s' % (laudo_mal or 'nenhum', glifos or 'nenhum', pend[:12] or 'nenhuma'))
    log('    => %s' % ('OK' if ok else 'REVISAR'))
    # render de todas as paginas para revisao visual
    for i, p in enumerate(doc):
        pix = p.get_pixmap(dpi=75)
        pix.save(os.path.join(ANALISIS, '_resumo_produtor_p%02d.png' % (i + 1)))
    doc.close()
    return ok, n, tam


def main():
    log('=' * 70); log('an_19_resumo_produtor'); log('=' * 70)
    V = cifras()
    B = Brand(logo=LOGO, footer_center=TXT['footer'], hero_h=7.4 * cm)
    st = story(B, V)
    B.build(OUT, st, cover_title=TXT['cover_title'], cover_subtitle=TXT['cover_sub'], title='Resumo para o produtor - Mata ciliar e Reserva Legal - Fazenda Santo Antonio')
    log('PDF -> %s' % OUT)
    verificar(OUT, V)


if __name__ == '__main__':
    main()
