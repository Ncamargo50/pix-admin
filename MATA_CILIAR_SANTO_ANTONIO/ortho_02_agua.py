# -*- coding: utf-8 -*-
"""ortho_02: agua abierta a 0,25 m (represa, 2o reservatorio de la cabecera del
arroio 2, cualquier otra lamina) desde color + textura de la ortofoto y, donde hay
DSM (N > 7401711), superficie plana del DSM y CHM ~ 0.

LIMITE MEDIDO: el DSM/DTM del vuelo termina en N 7401711 -> la represa (N 7401545-
7401694) NO tiene DSM: su espejo sale solo de color+textura; cota del espejo y
"espelho maximo potencial" por DTM NO son calculables ahi. Se da en cambio el
indicador fotointerpretado agua + faixa de deplecionamento sin vegetacion.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
from scipy import ndimage as ndi
from shapely.geometry import Point, box
from shapely.ops import unary_union

log('=' * 78)
log('ortho_02_agua  ortofoto %s' % FECHA_VUELO)
log('=' * 78)
GL = glebas()
RES = 0.25
tr, H, W, B = grilla(RES)
rgba, _ = leer(R('ortofoto_rgba.tif', RES), nan=False)
valido = rgba[3] > 0
Rr, Gg, Bb = [rgba[i].astype('float32') for i in range(3)]
del rgba
dsm, _ = leer(R('dsm.tif', RES)); dsm = dsm[0]
chm, _ = leer(R('chm.tif', RES)); chm = chm[0]
hay_dsm = np.isfinite(dsm)
m_prop = rasterizar([GL['IMOVEL']], RES).astype(bool)
m_aoi = rasterizar([GL['IMOVEL'].buffer(40)], RES).astype(bool)

# --- rasgos --------------------------------------------------------------------------
with Cronometro('rasgos de color y textura'):
    L = 0.299 * Rr + 0.587 * Gg + 0.114 * Bb
    ExG = 2 * Gg - Rr - Bb
    mx = np.maximum(np.maximum(Rr, Gg), Bb); mn = np.minimum(np.minimum(Rr, Gg), Bb)
    S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    BR = (Bb - Rr) / np.maximum(Bb + Rr, 1)
    def std_local(a, size):
        m1 = ndi.uniform_filter(a, size); m2 = ndi.uniform_filter(a * a, size)
        return np.sqrt(np.maximum(m2 - m1 * m1, 0))
    TEX = std_local(L, 9)                       # 2,25 m
    dsm_f = np.where(hay_dsm, dsm, 0).astype('float32')
    DSM_STD = np.where(hay_dsm, std_local(dsm_f, 9), np.nan)
    for nombre, a in (('L', L), ('ExG', ExG), ('S', S), ('BR', BR), ('TEX', TEX)):
        verificar_arr(np.where(valido, a, np.nan), nombre, m_prop)
    verificar_arr(DSM_STD, 'DSM_std_9px', m_prop, 'm')


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


def mahalanobis_rgb(seed):
    X = np.stack([Rr[seed], Gg[seed], Bb[seed]], 1).astype('float64')
    mu = X.mean(0); cov = np.cov(X.T) + np.eye(3) * 4.0
    icov = np.linalg.inv(cov)
    D = np.stack([Rr - mu[0], Gg - mu[1], Bb - mu[2]], -1)
    md2 = np.einsum('...i,ij,...j->...', D, icov, D)
    return md2, mu, cov


def stats_en(mask, nombre):
    d = {'n_px': int(mask.sum()), 'area_ha': round(mask.sum() * RES * RES / 1e4, 3),
         'L_media': round(float(L[mask].mean()), 1), 'ExG_media': round(float(ExG[mask].mean()), 1),
         'S_media': round(float(S[mask].mean()), 3), 'BR_media': round(float(BR[mask].mean()), 3),
         'TEX_media': round(float(TEX[mask].mean()), 2)}
    if (hay_dsm & mask).any():
        d['dsm_std_9px_mediana_m'] = round(float(np.nanmedian(DSM_STD[mask & hay_dsm])), 3)
        d['chm_mediana_m'] = round(float(np.nanmedian(chm[mask & hay_dsm])), 2)
        d['cota_dsm_mediana_m'] = round(float(np.nanmedian(dsm[mask & hay_dsm])), 2)
        d['pct_com_dsm'] = round(100.0 * (mask & hay_dsm).sum() / mask.sum(), 1)
    else:
        d['pct_com_dsm'] = 0.0
    log('  %s: %s' % (nombre, d))
    return d


CUERPOS = []
RES_JSON = {'fecha_vuelo': FECHA_VUELO, 'res_m': RES, 'metodo': {}}

# =====================================================================================
# 1. REPRESA PRINCIPAL (Arroio 3 = Ribeirao do Salto). Sin DSM: color + textura, semilla
#    = espejo tipico lluvioso S2 (freq_chuva >= 0,5) erosionado 10 m.
# =====================================================================================
with Cronometro('represa principal'):
    esp = cargar('represa_espelhos')
    massas = cargar('massas')
    FB = unary_union(list(massas.geometry))
    seed_poly = esp[esp.fuente.str.contains('freq_chuva')].geometry.iloc[0].buffer(-10)
    if seed_poly.is_empty:
        seed_poly = FB.buffer(-25)
    ventana = FB.buffer(120)
    m_win = rasterizar([ventana], RES).astype(bool) & valido
    seed = rasterizar([seed_poly], RES).astype(bool) & valido & (TEX < 6)
    log('  semilla represa: %d px (%.3f ha), L %.1f  TEX %.2f  ExG %.1f' % (seed.sum(), seed.sum() * RES * RES / 1e4, L[seed].mean(), TEX[seed].mean(), ExG[seed].mean()))
    md2, mu, cov = mahalanobis_rgb(seed)
    tex_lim = max(4.0, float(np.percentile(TEX[seed], 98)) * 1.5)
    cand = m_win & (md2 < 16.27) & (TEX < tex_lim) & (ExG < float(np.percentile(ExG[seed], 99)) + 8)
    cand = limpiar(cand, cerrar=4, abrir=2, min_m2=20)
    lab, n = ndi.label(cand)
    ids = np.unique(lab[seed & cand]); ids = ids[ids > 0]
    agua_rep = np.isin(lab, ids)
    agua_rep = ndi.binary_fill_holes(agua_rep)
    st = stats_en(agua_rep, 'represa agua 22-may-2026')
    RES_JSON['metodo']['represa'] = {'semilla': 'S2 freq_chuva>=0,5 erosionada 10 m', 'color_mu_RGB': [round(float(v), 1) for v in mu],
                                     'mahalanobis2_max': 16.27, 'tex_max_DN': round(tex_lim, 2), 'crecimiento': 'componentes conectadas a la semilla',
                                     'dsm': 'NO disponible (DSM termina en N 7401711)'}
    # faixa de deplecionamento: sin vegetacion, contigua al agua, dentro de la ventana -> "espelho maximo potencial" (indicador)
    sin_veg = m_win & valido & (ExG < 12) & (L < 200)
    ring = ndi.binary_dilation(agua_rep, iterations=int(25 / RES)) & sin_veg
    vaso = limpiar(agua_rep | ring, cerrar=6, abrir=3, min_m2=50)
    lab2, _ = ndi.label(vaso)
    ids2 = np.unique(lab2[agua_rep]); ids2 = ids2[ids2 > 0]
    vaso = np.isin(lab2, ids2)
    vaso = ndi.binary_fill_holes(vaso)
    # el vaso no puede pasar el dique (limite este de la massa FBDS + 15 m) ni salir de FBDS+40
    vaso &= rasterizar([FB.buffer(15)], RES).astype(bool)   # no pasar el dique ni la faja mas alla de FBDS + 15 m
    st_vaso = stats_en(vaso, 'represa agua + faixa sem vegetacao (vaso indicador)')
    g_rep = vectorizar(agua_rep, RES, min_area_m2=20)
    G_REP = unary_union(list(g_rep.geometry))
    g_vaso = vectorizar(vaso, RES, min_area_m2=50)
    G_VASO = unary_union(list(g_vaso.geometry))
    # comparacion con las fuentes previas
    comp = []
    for _, r in esp.iterrows():
        gi = r.geometry
        inter = ha(gi.intersection(G_REP))
        comp.append({'fuente': r.fuente, 'area_ha': round(float(r.area_ha), 3), 'intersecao_com_orto_ha': inter,
                     'iou_com_orto': round(inter / ha(gi.union(G_REP)), 3) if not gi.union(G_REP).is_empty else None})
    comp.append({'fuente': 'ORTOFOTO 22-mai-2026 (agua)', 'area_ha': ha(G_REP), 'intersecao_com_orto_ha': ha(G_REP), 'iou_com_orto': 1.0})
    comp.append({'fuente': 'ORTOFOTO 22-mai-2026 (agua + faixa sem vegetacao = vaso indicador)', 'area_ha': ha(G_VASO)})
    # alineacion con FBDS: borde este (dique) y borde sur/norte en la faja central
    def borde_este(g, y0, y1):
        c = g.intersection(box(g.bounds[0] - 1, y0, g.bounds[2] + 1, y1))
        return c.bounds[2] if not c.is_empty else None
    yc = (G_REP.bounds[1] + G_REP.bounds[3]) / 2
    xe_o = borde_este(G_REP, yc - 15, yc + 15); xe_f = borde_este(FB, yc - 15, yc + 15)
    xe_c = None
    car = cargar('car')
    car_res = car[(car.cod_tema.astype(str).str.contains('RESERVATORIO')) & (car.relacao == 'propio_G1')]
    if len(car_res):
        CARR = unary_union(list(car_res.geometry))
        CARR_rep = poly_only(CARR.intersection(FB.buffer(60)))
        xe_c = borde_este(CARR_rep, yc - 15, yc + 15)
    alin = {'dique_x_este_ortofoto': round(xe_o, 1) if xe_o else None, 'dique_x_este_fbds_2013': round(xe_f, 1) if xe_f else None,
            'dique_x_este_car': round(xe_c, 1) if xe_c else None,
            'dx_orto_menos_fbds_m': round(xe_o - xe_f, 1) if (xe_o and xe_f) else None,
            'dx_orto_menos_car_m': round(xe_o - xe_c, 1) if (xe_o and xe_c) else None,
            'centroide_orto': [round(G_REP.centroid.x, 1), round(G_REP.centroid.y, 1)],
            'centroide_fbds': [round(FB.centroid.x, 1), round(FB.centroid.y, 1)],
            'nota': 'el borde este del espejo es el dique (fijo): la diferencia de x mide el desplazamiento ortofoto<->FBDS/CAR; '
                    'el centroide cambia con el nivel y no sirve de control'}
    log('  alineacion dique: %s' % alin)
    area_rep = ha(G_REP)
    ge1 = area_rep >= 1.0
    RES_JSON['represa'] = {
        'area_agua_ha': area_rep, 'perimetro_m': round(G_REP.length, 1),
        'incerteza_borda_ha': round(G_REP.length * RES / 1e4, 3),
        'incerteza_nota': '1 px de borde a 0,25 m = perimetro x 0,25 m; la incertidumbre real es el NIVEL del dia (22-mai-2026, fin de otono)',
        'ge_1ha_22_mai_2026': bool(ge1), 'cota_espelho_m': None, 'cota_nota': 'sin DSM sobre la represa (DSM termina en N 7401711)',
        'vaso_indicador_ha': ha(G_VASO), 'espelho_maximo_potencial_por_dtm_ha': None,
        'espelho_maximo_nota': 'sin DTM sobre la represa: el vaso a cota de vertedero NO es calculable; el indicador es agua + faixa sin vegetacion contigua',
        'comparacao_fontes': comp, 'alinhamento_dique': alin, 'stats_agua': st, 'stats_vaso': st_vaso,
        'dentro_G1_ha': ha(G_REP.intersection(GL['G1'])),
    }
    log('  REPRESA 22-mai-2026: %.3f ha (%s 1 ha); vaso indicador %.3f ha' % (area_rep, '>=' if ge1 else '<', ha(G_VASO)))
    CUERPOS.append({'corpo': 'represa_principal', 'nome': 'Represa do Ribeirao do Salto (Arroio 3)', 'tipo': 'agua_aberta',
                    'area_ha': area_rep, 'cota_dsm_m': None, 'dsm_disponivel': False, 'metodo': 'cor+textura (semente S2), sem DSM',
                    'geometry': G_REP})
    CUERPOS.append({'corpo': 'represa_vaso_indicador', 'nome': 'Represa: agua + faixa de deplecionamento sem vegetacao', 'tipo': 'vaso_indicador',
                    'area_ha': ha(G_VASO), 'cota_dsm_m': None, 'dsm_disponivel': False, 'metodo': 'agua U (ExG<12 contiguo, <=25 m)',
                    'geometry': G_VASO})

# =====================================================================================
# 2. CABECERA DEL ARROIO 2: 2o reservatorio declarado (CAR 0,15 ha). Con DSM.
# =====================================================================================
with Cronometro('2o reservatorio (cabecera arroio 2)'):
    nas = cargar('nascentes')
    p_nas = nas[nas.id_fonte.astype(str) == '306158'].geometry.iloc[0]
    car_small = None
    if len(car_res):
        partes = [g for g in (CARR.geoms if hasattr(CARR, 'geoms') else [CARR]) if g.distance(p_nas) < 150]
        if partes:
            car_small = unary_union(partes)
            log('  CAR: reservatorio declarado en la cabecera: %.3f ha, centroide %s' % (ha(car_small), [round(car_small.centroid.x), round(car_small.centroid.y)]))
    ventana2 = p_nas.buffer(150)
    m_win2 = rasterizar([ventana2], RES).astype(bool) & valido
    # agua oscura y lisa; con DSM plano donde hay DSM
    oscuro = m_win2 & (L < 95) & (TEX < 5) & (ExG < 10) & (S < 0.45)
    plano = hay_dsm & (DSM_STD < 0.12) & (chm < 0.5)
    cand2 = limpiar(oscuro & (plano | ~hay_dsm), cerrar=3, abrir=2, min_m2=20)
    lab, n = ndi.label(cand2)
    if n:
        tam = ndi.sum(cand2, lab, np.arange(1, n + 1)) * RES * RES
        k = int(np.argmax(tam)) + 1
        agua_pond = lab == k
        st2 = stats_en(agua_pond, '2o reservatorio (agua)')
        g_pond = vectorizar(agua_pond, RES, min_area_m2=20)
        G_POND = unary_union(list(g_pond.geometry))
        # cota del espejo y "vaso" a esa cota + 0,5 m sobre el DTM hibrido (faixa de varzea)
        dtm_h, _ = leer(R('dtm_hibrido.tif', RES)); dtm_h = dtm_h[0]
        cota = float(np.nanmedian(dsm[agua_pond & hay_dsm]))
        cota_sd = float(np.nanstd(dsm[agua_pond & hay_dsm]))
        vaso2 = m_win2 & np.isfinite(dtm_h) & (dtm_h <= cota + 0.5)
        lab3, _ = ndi.label(vaso2)
        ids3 = np.unique(lab3[agua_pond]); ids3 = ids3[ids3 > 0]
        vaso2 = np.isin(lab3, ids3)
        g_v2 = vectorizar(vaso2, RES, min_area_m2=20)
        G_V2 = unary_union(list(g_v2.geometry)) if len(g_v2) else None
        RES_JSON['reservatorio_cabeceira'] = {
            'existe': True, 'area_agua_ha': ha(G_POND), 'perimetro_m': round(G_POND.length, 1),
            'centroide': [round(G_POND.centroid.x, 1), round(G_POND.centroid.y, 1)],
            'dist_nascente_fbds_306158_m': round(G_POND.distance(p_nas), 1),
            'cota_espelho_dsm_m': round(cota, 2), 'cota_sd_m': round(cota_sd, 2),
            'cota_nota': 'datum calibrado a FABDEM (EGM2008) +- ~0,7 m; el sd del DSM sobre el agua mide la planitud',
            'area_car_declarada_ha': ha(car_small) if car_small is not None else None,
            'iou_com_car': (round(ha(G_POND.intersection(car_small)) / ha(G_POND.union(car_small)), 3) if car_small is not None else None),
            'vaso_ate_cota_mais_0_5m_ha': ha(G_V2) if G_V2 is not None else None,
            'stats': st2,
            'leitura': 'lamina de agua oscura, plana en el DSM, en la cabecera del Arroio 2 rodeada de vegetacion higrofila: el 2o reservatorio declarado EXISTE',
        }
        log('  2o RESERVATORIO: %.3f ha, cota DSM %.2f m (sd %.2f), a %.0f m de la nascente FBDS; CAR declarado %s ha'
            % (ha(G_POND), cota, cota_sd, G_POND.distance(p_nas), ha(car_small) if car_small is not None else '-'))
        CUERPOS.append({'corpo': 'reservatorio_cabeceira_arroio2', 'nome': '2o reservatorio (cabeceira do Arroio 2, CAR 0,15 ha)', 'tipo': 'agua_aberta',
                        'area_ha': ha(G_POND), 'cota_dsm_m': round(cota, 2), 'dsm_disponivel': True,
                        'metodo': 'cor escura + textura baixa + DSM plano (std<0,12 m) + CHM<0,5', 'geometry': G_POND})
        if G_V2 is not None:
            CUERPOS.append({'corpo': 'reservatorio_cabeceira_vaso', 'nome': '2o reservatorio: vaso ate cota do espelho + 0,5 m (DTM hibrido)', 'tipo': 'vaso_indicador',
                            'area_ha': ha(G_V2), 'cota_dsm_m': round(cota + 0.5, 2), 'dsm_disponivel': True, 'metodo': 'DTM <= cota + 0,5 m conectado', 'geometry': G_V2})
    else:
        RES_JSON['reservatorio_cabeceira'] = {'existe': False, 'nota': 'sin lamina oscura y plana en 150 m de la nascente FBDS'}
        log('  2o reservatorio: NO detectado')

# =====================================================================================
# 3. BARRIDO GENERAL: cualquier otra lamina en el imovel + 40 m
# =====================================================================================
with Cronometro('barrido general de laminas'):
    ya = np.zeros((H, W), bool)
    for c in CUERPOS:
        if c['tipo'] == 'agua_aberta':
            ya |= rasterizar([c['geometry'].buffer(5)], RES).astype(bool)
    gen = m_aoi & valido & (TEX < 4.5) & (ExG < 10) & (L < 170) & (S < 0.40)
    gen_turbio = m_aoi & valido & (md2 < 16.27) & (TEX < tex_lim)
    # lamina VERDE (algas/lentejas: ExG alto) o de cualquier color: DSM perfectamente plano, sin dosel, muy lisa y no brillante
    gen_plano = m_aoi & valido & hay_dsm & (DSM_STD < 0.08) & (TEX < 3.0) & (L < 120) & (chm < 0.3)
    gen = limpiar((gen | gen_turbio | gen_plano) & ~ya, cerrar=3, abrir=3, min_m2=100)
    # con DSM: exigir plano y sin dosel; sin DSM: exigir el color de la represa (turbio) o muy oscuro
    gen = gen & ((hay_dsm & (DSM_STD < 0.15) & (chm < 0.5)) | (~hay_dsm & ((md2 < 9.0) | (L < 80))))
    gen = limpiar(gen, cerrar=2, abrir=2, min_m2=100)
    lab, n = ndi.label(gen)
    otros = []
    for k in range(1, n + 1):
        m = lab == k
        a_m2 = m.sum() * RES * RES
        if a_m2 < 100:
            continue
        g = vectorizar(m, RES, min_area_m2=50)
        if not len(g):
            continue
        G = unary_union(list(g.geometry))
        comp = G.area / max(G.convex_hull.area, 1)
        d = {'area_ha': ha(G), 'x': round(G.centroid.x, 1), 'y': round(G.centroid.y, 1), 'L': round(float(L[m].mean()), 1),
             'TEX': round(float(TEX[m].mean()), 2), 'ExG': round(float(ExG[m].mean()), 1), 'compacidade': round(comp, 2),
             'com_dsm': bool((m & hay_dsm).any()), 'gleba': 'G2' if G.intersects(GL['G2']) else ('G1' if G.intersects(GL['G1']) else 'fora')}
        d['leitura'] = 'candidato a lamina (verificar): ' + ('DSM plano' if d['com_dsm'] else 'sin DSM, solo color')
        otros.append(d)
        CUERPOS.append({'corpo': 'candidato_%02d' % len(otros), 'nome': 'lamina candidata %d' % len(otros), 'tipo': 'candidato',
                        'area_ha': ha(G), 'cota_dsm_m': (round(float(np.nanmedian(dsm[m & hay_dsm])), 2) if d['com_dsm'] else None),
                        'dsm_disponivel': d['com_dsm'], 'metodo': 'barrido generico', 'geometry': G})
    otros.sort(key=lambda d: -d['area_ha'])
    RES_JSON['outras_laminas_candidatas'] = otros
    log('  otras laminas candidatas >= 100 m2: %d -> %s' % (len(otros), [(o['area_ha'], o['x'], o['y'], o['gleba']) for o in otros[:12]]))

# =====================================================================================
# salidas
# =====================================================================================
gdf = gpd.GeoDataFrame([{k: v for k, v in c.items() if k != 'geometry'} for c in CUERPOS],
                       geometry=[c['geometry'] for c in CUERPOS], crs=CRS_METRICO)
gdf['fecha'] = FECHA_VUELO
gdf['crs'] = CRS_METRICO
guardar_gdf(gdf, R('agua_ortofoto_2026-05-22.geojson'))
guardar_json(R('ortho_02_agua.json'), RES_JSON)

with Cronometro('figura de control'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rgba, _ = leer(R('ortofoto_rgba.tif', RES), nan=False)
    def panel(ax, cx, cy, semi, geoms, titulo):
        c0, r0 = ~tr * (cx - semi, cy + semi); c1, r1 = ~tr * (cx + semi, cy - semi)
        r0, r1, c0, c1 = [int(v) for v in (r0, r1, c0, c1)]
        ax.imshow(np.moveaxis(rgba[:3, r0:r1, c0:c1], 0, -1), extent=[cx - semi, cx + semi, cy - semi, cy + semi])
        for g, col, lab in geoms:
            if g is None or g.is_empty:
                continue
            for p in (g.geoms if hasattr(g, 'geoms') else [g]):
                x, y = p.exterior.xy; ax.plot(x, y, col, lw=1.2, label=lab); lab = None
        ax.set_title(titulo); ax.legend(loc='lower left', fontsize=7)
    fig, ax = plt.subplots(1, 2, figsize=(16, 9))
    panel(ax[0], G_REP.centroid.x, G_REP.centroid.y, 200,
          [(G_REP, 'c-', 'agua 22-mai-2026 %.3f ha' % ha(G_REP)), (G_VASO, 'y-', 'vaso indicador %.3f ha' % ha(G_VASO)),
           (FB, 'm-', 'FBDS 2013 1,95 ha')], 'represa')
    if RES_JSON['reservatorio_cabeceira'].get('existe'):
        panel(ax[1], G_POND.centroid.x, G_POND.centroid.y, 90,
              [(G_POND, 'c-', 'agua %.3f ha' % ha(G_POND)), (G_V2, 'y-', 'vaso cota+0,5 m'), (car_small, 'm-', 'CAR declarado'), (p_nas.buffer(3), 'r-', 'nascente FBDS')],
              '2o reservatorio (cabeceira arroio 2)')
    plt.tight_layout(); plt.savefig(R('_check_ortho_02.png'), dpi=100); plt.close()
    log('  -> _check_ortho_02.png')
log('ortho_02 listo.')
