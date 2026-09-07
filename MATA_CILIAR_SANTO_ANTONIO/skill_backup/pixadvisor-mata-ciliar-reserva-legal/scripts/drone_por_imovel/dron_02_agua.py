# -*- coding: utf-8 -*-
"""dron_02: agua abierta POR INMUEBLE sobre la ortofoto recortada (0,25 m): represa, acude
(reservatorio da cabeceira do Arroio 2) e lagoas menores. Area (3 decimales), n, cota DSM
(datum del vuelo) donde hay DSM; represa >= 1 ha si/no (22-mai-2026).

SOLO DRON: la semilla de la represa sale de la propia ortofoto (lamina lisa, no verde, no
azulada de sombra, no roja de suelo) y NO de Sentinel-2. Los datos oficiales se usan solo como
REFERENCIA de localizacion: massa d'agua FBDS 2013 (para decir si la lamina detectada es la
represa cartografiada) y nascente FBDS 306158 (ventana de busqueda del acude de cabecera).

Rasgos calibrados en la ortofoto (ortho_02/ortho_07, MEDIDO): agua de la represa L~130, ExG~-7,5,
BR~-0,10, TEX<1; agua oscura del acude L~69; sombras BR>0 (azuladas); suelo rojo desnudo
ExG -40..-57, BR -0,26..-0,29 (se excluye con ExG_min -25 y BR_min -0,20).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dron_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
from scipy import ndimage as ndi
from shapely.geometry import Point
from shapely.ops import unary_union
from rasterio import features

cabecera('dron_02_agua')
RES = 0.25
MASSAS = cargar_oficial('massas_fbds')
NASC = cargar_oficial('nascentes')
P_NASC = NASC[NASC.id_fonte.astype(str) == '306158'].geometry.iloc[0]
MAHAL_MAX = 16.27   # chi2(3) 0,999



def lamina_kmeans_10cm(seed_geom, imovel_geom, pad_m=80.0, f=2):
    """Lamina de agua da represa a 10 cm (ortofoto original, so drone): k-means 8 grupos sobre
    (R,G,B,S,ExG,log tex) na janela seed+pad; agua = grupos com >= 8 % da semente + grupos lisos e nao
    verdes; componente conectada a semente; abertura 3 px, fechamento 5 px, preenchimento de furos.
    Devolve (poligono EPSG:31982 recortado ao imovel, stats)."""
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio import features as rfeat
    from skimage.color import rgb2hsv
    from skimage.filters import sobel
    from sklearn.cluster import MiniBatchKMeans
    from shapely.geometry import shape as _shape
    x0, y0, x1, y1 = seed_geom.buffer(pad_m).bounds
    with rasterio.open(ORTHO_SRC) as src:
        x0, y0 = max(x0, src.bounds.left), max(y0, src.bounds.bottom); x1, y1 = min(x1, src.bounds.right), min(y1, src.bounds.top)
        w = from_bounds(x0, y0, x1, y1, src.transform); Hh, Ww = int(w.height // f), int(w.width // f)
        rgb = src.read([1, 2, 3], window=w, out_shape=(3, Hh, Ww)).astype('float32') / 255.0
        al = src.read(4, window=w, out_shape=(Hh, Ww))
    trw = rasterio.transform.from_bounds(x0, y0, x1, y1, Ww, Hh); px = (x1 - x0) / Ww
    Rf, Gf, Bf = rgb; hsv = rgb2hsv(np.dstack(rgb)); Sf = hsv[..., 1]
    exg = 2 * Gf - Rf - Bf; gray = 0.299 * Rf + 0.587 * Gf + 0.114 * Bf
    tex = ndi.uniform_filter(sobel(gray), 15)
    F = np.dstack([Rf, Gf, Bf, Sf, exg, np.log1p(tex * 50)]).reshape(-1, 6)
    km = MiniBatchKMeans(n_clusters=8, random_state=0, batch_size=20000).fit(F[::7])
    labk = km.predict(F).reshape(Hh, Ww)
    seedm = rfeat.rasterize([(seed_geom.buffer(-5.0) if seed_geom.buffer(-5.0).area > 100 else seed_geom, 1)], out_shape=(Hh, Ww), transform=trw).astype(bool)
    frac = [float((labk[seedm] == c).mean()) for c in range(8)]
    tex_c = [float(tex[labk == c].mean()) if (labk == c).any() else np.inf for c in range(8)]
    exg_c = [float(exg[labk == c].mean()) if (labk == c).any() else 9 for c in range(8)]
    tmed = float(np.median([t for t in tex_c if np.isfinite(t)]))
    water = {c for c in range(8) if frac[c] >= 0.08} | {c for c in range(8) if exg_c[c] < 0.04 and tex_c[c] < tmed}
    wm = np.isin(labk, list(water)) & (al > 0)
    wm = ndi.binary_opening(wm, iterations=3); wm = ndi.binary_closing(wm, iterations=5)
    lbl, _ = ndi.label(wm); ids = np.unique(lbl[seedm]); ids = ids[ids > 0]
    comp = ndi.binary_fill_holes(np.isin(lbl, ids))
    polys = [_shape(g) for g, v in rfeat.shapes(comp.astype('uint8'), mask=comp, transform=trw) if v == 1]
    poly = max(polys, key=lambda q: q.area).simplify(0.2).buffer(0).intersection(imovel_geom)
    st = {'res_m': round(px, 3), 'grupos_agua': sorted(int(c) for c in water), 'fracao_semente': [round(x, 2) for x in frac],
          'area_ha_janela': round(float(comp.sum()) * px * px / 1e4, 3), 'area_ha_no_imovel': round(poly.area / 1e4, 3)}
    return poly, st

def limpiar(mask, cerrar=4, abrir=2, min_m2=20):
    m = ndi.binary_closing(mask, iterations=cerrar)
    m = ndi.binary_fill_holes(m)
    m = ndi.binary_opening(m, iterations=abrir)
    lab, n = ndi.label(m)
    if n == 0:
        return m
    tam = ndi.sum(m, lab, np.arange(1, n + 1)) * RES * RES
    keep = np.zeros(n + 1, bool); keep[1:] = tam >= min_m2
    return keep[lab]


RESUMO = {}
for imovel in ORDEM_IMOVEIS:
    log('\n' + '#' * 78)
    log('# %s  (%s, %.3f ha)' % (imovel, IMOVEIS[imovel]['nome'], area_ha(imovel)))
    log('#' * 78)
    IM = imoveis()[imovel]
    tr, H, W, B = grilla(imovel, RES)
    m_prop = mascara(imovel, RES)
    rgba, _ = leer(R(imovel, 'ortofoto_rgba.tif', RES), nan=False)
    valido = (rgba[3] > 0) & m_prop
    Rr, Gg, Bb, L, ExG, S, BR, TEX = rasgos_rgb(rgba)
    del rgba
    dsm, _ = leer(R(imovel, 'dsm.tif', RES)); dsm = dsm[0]
    chm, _ = leer(R(imovel, 'chm.tif', RES)); chm = chm[0]
    hay_dsm = np.isfinite(dsm)
    DSM_STD = np.where(hay_dsm, std_local(np.where(hay_dsm, dsm, 0).astype('float32'), 9), np.nan)
    for nombre, a in (('L', L), ('ExG', ExG), ('S', S), ('BR', BR), ('TEX9', TEX)):
        verificar_arr(np.where(valido, a, np.nan), nombre, m_prop)
    verificar_arr(DSM_STD, 'DSM_std_9px', m_prop, 'm', permitir_vacia=True)

    def mahalanobis_rgb(seed):
        X = np.stack([Rr[seed], Gg[seed], Bb[seed]], 1).astype('float64')
        mu = X.mean(0); cov = np.cov(X.T) + np.eye(3) * 4.0
        icov = np.linalg.inv(cov)
        D = np.stack([Rr - mu[0], Gg - mu[1], Bb - mu[2]], -1)
        return np.einsum('...i,ij,...j->...', D, icov, D), mu

    def stats_en(mask, nombre):
        d = {'n_px': int(mask.sum()), 'area_ha': round(mask.sum() * RES * RES / 1e4, 3),
             'L_media': round(float(L[mask].mean()), 1), 'ExG_media': round(float(ExG[mask].mean()), 1),
             'S_media': round(float(S[mask].mean()), 3), 'BR_media': round(float(BR[mask].mean()), 3), 'TEX_media': round(float(TEX[mask].mean()), 2)}
        if (hay_dsm & mask).any():
            d['dsm_std_9px_mediana_m'] = round(float(np.nanmedian(DSM_STD[mask & hay_dsm])), 3)
            d['chm_mediana_m'] = round(float(np.nanmedian(chm[mask & hay_dsm])), 2)
            d['cota_dsm_mediana_m_datum_voo'] = round(float(np.nanmedian(dsm[mask & hay_dsm])), 2)
            d['cota_dsm_sd_m'] = round(float(np.nanstd(dsm[mask & hay_dsm])), 2)
            d['pct_com_dsm'] = round(100.0 * (mask & hay_dsm).sum() / mask.sum(), 1)
        else:
            d['pct_com_dsm'] = 0.0
        log('  %s: %s' % (nombre, d))
        return d

    CUERPOS = []
    J = {'imovel': imovel, 'fecha_voo': FECHA_VUELO, 'res_m': RES, 'fonte': 'somente ortofoto/DSM do drone; FBDS/nascente so como referencia de localizacao',
         'cota_nota': 'cotas no datum do voo (ODM sem GCP/RTK): RELATIVAS, sem calibracao satelital'}

    # =========================================================================================
    # 1. semilla de lamina desde la propia ortofoto (sin S2): lisa, no verde, no sombra, no suelo rojo
    # =========================================================================================
    with Cronometro('candidatos a lamina (semilla propia)'):
        liso = valido & (TEX < 2.5) & (ExG < 5) & (ExG > -25) & (BR > -0.20) & (BR < 0.10) & (L > 60) & (L < 200) & (S < 0.45)
        plano = hay_dsm & (DSM_STD < 0.12) & (chm < 0.5)
        liso = liso & (plano | ~hay_dsm)
        liso = limpiar(liso, cerrar=3, abrir=3, min_m2=100)
        lab, n = ndi.label(liso)
        cands = []
        for k in range(1, n + 1):
            mk = lab == k
            a_ha = mk.sum() * RES * RES / 1e4
            if a_ha < 0.05:
                continue
            rows, cols = np.where(mk)
            cx = float(tr.c + (cols.mean() + 0.5) * RES); cy = float(tr.f + (rows.mean() + 0.5) * tr.e)
            d_massa = float(min(g.distance(Point(cx, cy)) for g in MASSAS.geometry)) if len(MASSAS) else None
            cands.append({'k': k, 'area_ha': round(a_ha, 3), 'x': round(cx, 1), 'y': round(cy, 1), 'L': round(float(L[mk].mean()), 1),
                          'ExG': round(float(ExG[mk].mean()), 1), 'BR': round(float(BR[mk].mean()), 3), 'TEX': round(float(TEX[mk].mean()), 2),
                          'com_dsm': bool((mk & hay_dsm).any()), 'dist_massa_fbds_m': round(d_massa, 1) if d_massa is not None else None})
        cands.sort(key=lambda d: -d['area_ha'])
        J['semillas_candidatas'] = cands[:15]
        log('  semillas >= 0,05 ha: %d -> %s' % (len(cands), [(c['area_ha'], c['x'], c['y'], c['dist_massa_fbds_m']) for c in cands[:8]]))

    # =========================================================================================
    # 2. REPRESA: mayor semilla >= 0,3 ha, crecida por color (Mahalanobis RGB) conectada
    # =========================================================================================
    G_REP = None
    with Cronometro('represa'):
        sem = [c for c in cands if c['area_ha'] >= 0.3]
        if sem:
            c0 = sem[0]
            seed = ndi.binary_erosion(lab == c0['k'], iterations=int(3 / RES))
            if seed.sum() < 100:
                seed = lab == c0['k']
            win = ndi.binary_dilation(lab == c0['k'], iterations=int(150 / RES)) & valido
            md2, mu = mahalanobis_rgb(seed)
            tex_lim = max(4.0, float(np.percentile(TEX[seed], 98)) * 1.5)
            # --- v6 (2026-09-07): o crescimento Mahalanobis RGB ficava CURTO na orla rasa e turva (1,459 ha).
            # Metodo validado a olho sobre a ortofoto a 10 cm (ver _check_represa_v6.png): k-means em
            # (R,G,B,S,ExG,log textura) na janela da represa, agua = grupos que dominam a semente (>= 8 %)
            # + grupos lisos nao verdes; crescimento conectado a semente; fechamento morfologico 0,5 m.
            seed_geom = unary_union(list(vectorizar(imovel, seed, RES, min_area_m2=20).geometry)).buffer(0)
            G_REP6, st6 = lamina_kmeans_10cm(seed_geom, IM)
            agua_rep = features.rasterize([(G_REP6, 1)], out_shape=(H, W), transform=tr).astype(bool) & valido
            log('  k-means 10 cm: %s' % st6)
            st = stats_en(agua_rep, 'represa agua 22-mai-2026')
            g_rep = vectorizar(imovel, agua_rep, RES, min_area_m2=20)
            G_REP = unary_union(list(g_rep.geometry)).buffer(0)
            # vaso indicador: faixa sem vegetacao contigua (<= 25 m)
            sin_veg = win & (ExG < 12) & (L < 200)
            ring = ndi.binary_dilation(agua_rep, iterations=int(25 / RES)) & sin_veg
            vaso = limpiar(agua_rep | ring, cerrar=6, abrir=3, min_m2=50)
            lab3, _ = ndi.label(vaso); ids3 = np.unique(lab3[agua_rep]); ids3 = ids3[ids3 > 0]
            vaso = ndi.binary_fill_holes(np.isin(lab3, ids3))
            st_vaso = stats_en(vaso, 'represa: agua + faixa sem vegetacao (vaso indicador)')
            g_vaso = vectorizar(imovel, vaso, RES, min_area_m2=50)
            G_VASO = unary_union(list(g_vaso.geometry)).buffer(0)
            d_massa = float(min(g.distance(G_REP) for g in MASSAS.geometry)) if len(MASSAS) else None
            massa_int = [{'massa_id': int(r.get('objectid', 0) or 0), 'area_fbds_ha': round(r.geometry.area / 1e4, 3), 'intersecao_ha': ha(r.geometry.intersection(G_REP)),
                          'iou': round(ha(r.geometry.intersection(G_REP)) / max(ha(r.geometry.union(G_REP)), 1e-6), 3)} for _, r in MASSAS.iterrows() if r.geometry.intersects(G_REP)]
            area_rep = ha(G_REP)
            J['represa'] = {'existe': True, 'area_agua_ha': area_rep, 'perimetro_m': round(G_REP.length, 1), 'n_poligonos': int(len(g_rep)),
                            'incerteza_borda_ha': round(G_REP.length * RES / 1e4, 3), 'ge_1ha_22_mai_2026': bool(area_rep >= 1.0),
                            'cota_dsm_m_datum_voo': st.get('cota_dsm_mediana_m_datum_voo'), 'pct_com_dsm': st['pct_com_dsm'],
                            'cota_nota': ('sem DSM sobre a represa (DSM/DTM do voo terminam em N 7401711)' if st['pct_com_dsm'] == 0 else 'cota no datum do voo, relativa'),
                            'vaso_indicador_ha': ha(G_VASO), 'semente': {k: v for k, v in c0.items() if k != 'k'}, 'cor_media_RGB_semente': [round(float(v), 1) for v in mu],
                            'metodo': 'semente = maior lamina lisa nao verde da propria ortofoto; k-means RGB+S+ExG+textura (8 grupos) conectado a semente, fechamento 0,5 m; sem satelite',
                            'referencia_fbds_2013': {'dist_massa_mais_proxima_m': round(d_massa, 1) if d_massa is not None else None, 'massas_que_intersectam': massa_int,
                                                     'nota': 'a massa FBDS 2013 (RapidEye) NAO foi usada para medir: so confirma que a lamina detectada e a represa cartografiada'},
                            'stats_agua': st, 'stats_vaso': st_vaso}
            log('  REPRESA %s: %.3f ha (%s 1 ha); vaso indicador %.3f ha; massa FBDS a %.1f m' % (imovel, area_rep, '>=' if area_rep >= 1 else '<', ha(G_VASO), d_massa if d_massa is not None else -1))
            CUERPOS.append({'corpo': 'represa_principal', 'nome': 'Represa (barramento do Ribeirao do Salto / Arroio 3)', 'tipo': 'agua_aberta', 'area_ha': area_rep,
                            'cota_dsm_m': st.get('cota_dsm_mediana_m_datum_voo'), 'dsm_disponivel': bool(st['pct_com_dsm'] > 0), 'metodo': 'k-means 10 cm (v6), semente propria', 'geometry': G_REP})
            CUERPOS.append({'corpo': 'represa_vaso_indicador', 'nome': 'Represa: agua + faixa de deplecionamento sem vegetacao (indicador)', 'tipo': 'vaso_indicador', 'area_ha': ha(G_VASO),
                            'cota_dsm_m': None, 'dsm_disponivel': False, 'metodo': 'agua U faixa ExG<12 contigua <= 25 m', 'geometry': G_VASO})
        else:
            J['represa'] = {'existe': False, 'nota': 'nenhuma lamina lisa nao verde >= 0,3 ha no imovel'}
            log('  represa: NAO ha lamina >= 0,3 ha em %s' % imovel)

    # =========================================================================================
    # 3. ACUDE DA CABECEIRA (nascente FBDS 306158 como referencia de localizacao): oscuro, liso, DSM plano
    # =========================================================================================
    with Cronometro('acude da cabeceira (nascente 306158)'):
        G_POND = None
        if IM.distance(P_NASC) < 150:
            win2 = rasterizar(imovel, [P_NASC.buffer(150)], RES).astype(bool) & valido
            oscuro = win2 & (L < 95) & (TEX < 5) & (ExG < 10) & (S < 0.45) & (BR > -0.20)
            cand2 = limpiar(oscuro & (plano | ~hay_dsm), cerrar=3, abrir=2, min_m2=20)
            if G_REP is not None:
                cand2 &= ~rasterizar(imovel, [G_REP.buffer(5)], RES).astype(bool)
            lab4, n4 = ndi.label(cand2)
            if n4:
                tam = ndi.sum(cand2, lab4, np.arange(1, n4 + 1)) * RES * RES
                k = int(np.argmax(tam)) + 1
                agua_pond = lab4 == k
                st2 = stats_en(agua_pond, 'acude da cabeceira (agua)')
                g_pond = vectorizar(imovel, agua_pond, RES, min_area_m2=20)
                G_POND = unary_union(list(g_pond.geometry)).buffer(0)
                d = {'existe': True, 'area_agua_ha': ha(G_POND), 'perimetro_m': round(G_POND.length, 1), 'centroide': [round(G_POND.centroid.x, 1), round(G_POND.centroid.y, 1)],
                     'dist_nascente_fbds_306158_m': round(G_POND.distance(P_NASC), 1), 'cota_dsm_m_datum_voo': st2.get('cota_dsm_mediana_m_datum_voo'), 'cota_sd_m': st2.get('cota_dsm_sd_m'),
                     'stats': st2, 'leitura': 'lamina escura, lisa e plana no DSM na cabeceira do Arroio 2: acude declarado no CAR (0,147 ha) EXISTE, menor que o declarado'}
                if hay_dsm[agua_pond].any():
                    dtm, _ = leer(R(imovel, 'dtm.tif', RES)); dtm = dtm[0]
                    cota = float(np.nanmedian(dsm[agua_pond & hay_dsm]))
                    vaso2 = win2 & np.isfinite(dtm) & (dtm <= cota + 0.5)
                    lab5, _ = ndi.label(vaso2); ids5 = np.unique(lab5[agua_pond]); ids5 = ids5[ids5 > 0]
                    vaso2 = np.isin(lab5, ids5)
                    g_v2 = vectorizar(imovel, vaso2, RES, min_area_m2=20)
                    if len(g_v2):
                        G_V2 = unary_union(list(g_v2.geometry)).buffer(0)
                        d['vaso_ate_cota_mais_0_5m_ha'] = ha(G_V2)
                        CUERPOS.append({'corpo': 'acude_cabeceira_vaso', 'nome': 'Acude da cabeceira: vaso ate cota do espelho + 0,5 m (DTM do voo)', 'tipo': 'vaso_indicador', 'area_ha': ha(G_V2),
                                        'cota_dsm_m': round(cota + 0.5, 2), 'dsm_disponivel': True, 'metodo': 'DTM <= cota + 0,5 m conectado', 'geometry': G_V2})
                    del dtm
                J['acude_cabeceira'] = d
                log('  ACUDE cabeceira: %.3f ha a %.0f m da nascente FBDS; cota DSM (voo) %s' % (ha(G_POND), G_POND.distance(P_NASC), st2.get('cota_dsm_mediana_m_datum_voo')))
                CUERPOS.append({'corpo': 'acude_cabeceira_arroio2', 'nome': 'Acude da cabeceira do Arroio 2 (CAR declara 0,147 ha)', 'tipo': 'agua_aberta', 'area_ha': ha(G_POND),
                                'cota_dsm_m': st2.get('cota_dsm_mediana_m_datum_voo'), 'dsm_disponivel': bool(st2['pct_com_dsm'] > 0), 'metodo': 'cor escura + textura baixa + DSM plano', 'geometry': G_POND})
            else:
                J['acude_cabeceira'] = {'existe': False, 'nota': 'sem lamina escura e plana em 150 m da nascente FBDS 306158'}
        else:
            J['acude_cabeceira'] = {'existe': False, 'nota': 'a nascente FBDS 306158 esta a %.0f m deste imovel: nao se aplica' % IM.distance(P_NASC)}
            log('  acude cabeceira: nascente 306158 a %.0f m do imovel: nao se aplica' % IM.distance(P_NASC))

    # =========================================================================================
    # 4. LAGOAS MENORES: barrido general no imovel
    # =========================================================================================
    with Cronometro('lagoas menores (barrido)'):
        ya = np.zeros((H, W), bool)
        for c in CUERPOS:
            if c['tipo'] == 'agua_aberta':
                ya |= rasterizar(imovel, [c['geometry'].buffer(5)], RES).astype(bool)
        gen = valido & (TEX < 4.5) & (ExG < 10) & (ExG > -25) & (L < 170) & (S < 0.40) & (BR > -0.20)
        gen_plano = valido & hay_dsm & (DSM_STD < 0.08) & (TEX < 3.0) & (L < 120) & (chm < 0.3)
        if G_REP is not None:
            gen |= valido & (md2 < MAHAL_MAX) & (TEX < tex_lim) & (BR > -0.20)
        gen = limpiar((gen | gen_plano) & ~ya, cerrar=3, abrir=3, min_m2=100)
        gen = gen & ((hay_dsm & (DSM_STD < 0.15) & (chm < 0.5)) | (~hay_dsm & (L < 80)))
        gen = limpiar(gen, cerrar=2, abrir=2, min_m2=100)
        lab6, n6 = ndi.label(gen)
        otros = []
        for k in range(1, n6 + 1):
            mk = lab6 == k
            if mk.sum() * RES * RES < 100:
                continue
            g = vectorizar(imovel, mk, RES, min_area_m2=50)
            if not len(g):
                continue
            G = unary_union(list(g.geometry)).buffer(0)
            comp = G.area / max(G.convex_hull.area, 1)
            com_dsm = bool((mk & hay_dsm).any())
            d = {'area_ha': ha(G), 'x': round(G.centroid.x, 1), 'y': round(G.centroid.y, 1), 'L': round(float(L[mk].mean()), 1), 'TEX': round(float(TEX[mk].mean()), 2),
                 'ExG': round(float(ExG[mk].mean()), 1), 'BR': round(float(BR[mk].mean()), 3), 'compacidade': round(comp, 2), 'com_dsm': com_dsm,
                 'cota_dsm_m_datum_voo': (round(float(np.nanmedian(dsm[mk & hay_dsm])), 2) if com_dsm else None)}
            confirmada = com_dsm and d['area_ha'] >= 0.03 and comp >= 0.5
            d['classe'] = 'lagoa_menor' if confirmada else 'candidato_a_verificar'
            d['leitura'] = ('lamina plana no DSM, compacta, >= 0,03 ha: lagoa menor' if confirmada else
                            'candidato (sem DSM, ou < 0,03 ha, ou pouco compacto): verificar em campo')
            otros.append(d)
            CUERPOS.append({'corpo': '%s_%02d' % ('lagoa' if confirmada else 'candidato', len(otros)), 'nome': 'lagoa menor %d' % len(otros) if confirmada else 'lamina candidata %d' % len(otros),
                            'tipo': 'agua_aberta' if confirmada else 'candidato', 'area_ha': ha(G), 'cota_dsm_m': d['cota_dsm_m_datum_voo'], 'dsm_disponivel': com_dsm,
                            'metodo': 'barrido generico', 'geometry': G})
        otros.sort(key=lambda d: -d['area_ha'])
        J['lagoas_menores'] = {'confirmadas': [o for o in otros if o['classe'] == 'lagoa_menor'], 'candidatos': [o for o in otros if o['classe'] != 'lagoa_menor']}
        log('  lagoas menores confirmadas: %d (%.3f ha); candidatos: %d' % (len(J['lagoas_menores']['confirmadas']), sum(o['area_ha'] for o in J['lagoas_menores']['confirmadas']), len(J['lagoas_menores']['candidatos'])))

    # --- resumen por inmueble ----------------------------------------------------------------------
    abertas = [c for c in CUERPOS if c['tipo'] == 'agua_aberta']
    tot = ha(unary_union([c['geometry'] for c in abertas]).intersection(IM)) if abertas else 0.0
    J['resumo'] = {'agua_aberta_total_ha': tot, 'n_corpos': len(abertas),
                   'represa_ha': J['represa'].get('area_agua_ha', 0.0), 'represa_ge_1ha': J['represa'].get('ge_1ha_22_mai_2026', False),
                   'acude_cabeceira_ha': J['acude_cabeceira'].get('area_agua_ha', 0.0),
                   'lagoas_menores_ha': round(sum(o['area_ha'] for o in J['lagoas_menores']['confirmadas']), 3),
                   'n_lagoas_menores': len(J['lagoas_menores']['confirmadas'])}
    log('  AGUA %s: total %.3f ha em %d corpos (represa %.3f, acude %.3f, lagoas %.3f)' % (imovel, tot, len(abertas), J['resumo']['represa_ha'], J['resumo']['acude_cabeceira_ha'], J['resumo']['lagoas_menores_ha']))
    if CUERPOS:
        gdf = gpd.GeoDataFrame([{k: v for k, v in c.items() if k != 'geometry'} for c in CUERPOS], geometry=[c['geometry'] for c in CUERPOS], crs=CRS_METRICO)
        gdf['imovel'] = imovel; gdf['fecha'] = FECHA_VUELO; gdf['crs'] = CRS_METRICO
        gdf['area_dentro_imovel_ha'] = [ha(g.intersection(IM)) for g in gdf.geometry]
        guardar_gdf(gdf, R(imovel, 'agua_%s_%s.geojson' % (imovel, FECHA_VUELO)))
    else:
        log('  (sem corpos d agua em %s: nenhum vetor escrito)' % imovel)
    guardar_json(R(imovel, 'dron_02_agua.json'), J)
    RESUMO[imovel] = J['resumo']

    # --- figura de control -----------------------------------------------------------------------------
    if G_REP is not None or G_POND is not None:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        rgba, _ = leer(R(imovel, 'ortofoto_rgba.tif', RES), nan=False)
        def panel(ax, cx, cy, semi, geoms, titulo):
            c0_, r0_ = ~tr * (cx - semi, cy + semi); c1_, r1_ = ~tr * (cx + semi, cy - semi)
            r0_, r1_, c0_, c1_ = [max(0, int(v)) for v in (r0_, r1_, c0_, c1_)]
            r1_, c1_ = min(H, r1_), min(W, c1_)
            ax.imshow(np.moveaxis(rgba[:3, r0_:r1_, c0_:c1_], 0, -1), extent=[tr.c + c0_ * RES, tr.c + c1_ * RES, tr.f + r1_ * tr.e, tr.f + r0_ * tr.e])
            for g, col, lab_ in geoms:
                if g is None or g.is_empty:
                    continue
                for p in (g.geoms if hasattr(g, 'geoms') else [g]):
                    x, y = p.exterior.xy; ax.plot(x, y, col, lw=1.2, label=lab_); lab_ = None
            ax.set_xlim(cx - semi, cx + semi); ax.set_ylim(cy - semi, cy + semi)
            ax.set_title(titulo); ax.legend(loc='lower left', fontsize=7)
        fig, ax = plt.subplots(1, 2, figsize=(16, 9))
        if G_REP is not None:
            panel(ax[0], G_REP.centroid.x, G_REP.centroid.y, 220, [(G_REP, 'c-', 'agua %.3f ha' % ha(G_REP)), (G_VASO, 'y-', 'vaso indicador %.3f ha' % ha(G_VASO)),
                                                                  (unary_union([g for g in MASSAS.geometry if g.distance(G_REP) < 300]), 'm-', 'massa FBDS 2013 (referencia)')], 'represa %s' % imovel)
        if G_POND is not None:
            panel(ax[1], G_POND.centroid.x, G_POND.centroid.y, 90, [(G_POND, 'c-', 'acude %.3f ha' % ha(G_POND)), (P_NASC.buffer(3), 'r-', 'nascente FBDS 306158')], 'acude da cabeceira')
        plt.tight_layout(); plt.savefig(R(imovel, '_check_dron_02.png'), dpi=100); plt.close()
        log('  -> _check_dron_02.png')
    del Rr, Gg, Bb, L, ExG, S, BR, TEX, dsm, chm, DSM_STD

guardar_json(os.path.join(SALIDA_RAIZ, 'dron_02_resumo_agua.json'), RESUMO)
log('dron_02 listo.')
