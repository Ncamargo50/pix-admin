# -*- coding: utf-8 -*-
"""ortho_01: recorte + remuestreo de la ortofoto / DTM / DSM a la grilla comun
(0,25 y 0,50 m, EPSG:31982), CHM, hillshade, pendiente, huella de cobertura y
verificacion de alineacion (ortofoto <-> DSM; ortofoto <-> S2 10 m).

Lectura de los originales SIEMPRE por franjas decimadas (overviews), nunca read().
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import rasterio
from rasterio.enums import Resampling
from scipy import ndimage as ndi

log('=' * 78)
log('ortho_01_preparar  vuelo %s  ->  %s' % (FECHA_VUELO, SALIDA))
log('=' * 78)
PROP = cargar_propiedad()
GL = glebas()
INFO = {'fecha_vuelo': FECHA_VUELO, 'crs_fuente': CRS_FUENTE, 'crs_salida': CRS_METRICO}

# --- grillas ---------------------------------------------------------------------
for res in (0.25, 0.5):
    tr, h, w, b = grilla(res)
    log('grilla %.2f m: %dx%d px, bounds %s' % (res, w, h, b))
    INFO['grilla_%s' % res] = {'width': w, 'height': h, 'bounds': b, 'origen': [tr.c, tr.f]}

# --- metadatos de las fuentes: misma grilla? ----------------------------------------
META = {}
for k, p in (('ortofoto', ORTHO_SRC), ('dsm', DSM_SRC), ('dtm', DTM_SRC)):
    with rasterio.open(p) as s:
        META[k] = {'crs': str(s.crs), 'width': s.width, 'height': s.height, 'res': [s.res[0], s.res[1]],
                   'origen': [s.transform.c, s.transform.f], 'bounds': list(s.bounds), 'nodata': s.nodata,
                   'overviews': s.overviews(1), 'bandas': s.count, 'dtype': s.dtypes[0]}
        log('  %-9s %s %dx%d px res %.7f m origen (%.3f, %.3f) bounds N %.1f..%.1f' % (
            k, s.crs, s.width, s.height, s.res[0], s.transform.c, s.transform.f, s.bounds.bottom, s.bounds.top))
dx = META['dsm']['origen'][0] - META['ortofoto']['origen'][0]
dy = META['dsm']['origen'][1] - META['ortofoto']['origen'][1]
misma = abs(dx) < 1e-3 and abs(dy) < 1e-3 and abs(META['dsm']['res'][0] - META['ortofoto']['res'][0]) < 1e-9
INFO['grilla_dtm_igual_a_ortofoto'] = bool(misma)
INFO['grilla_dtm_vs_ortofoto'] = {'dx_origen_m': round(dx, 3), 'dy_origen_m': round(dy, 3),
                                   'res_orto_m': META['ortofoto']['res'][0], 'res_dtm_m': META['dsm']['res'][0],
                                   'dx_en_px_orto': round(dx / META['ortofoto']['res'][0], 2),
                                   'dy_en_px_orto': round(dy / META['ortofoto']['res'][1], 2),
                                   'extension_sur_dtm_N': META['dsm']['bounds'][1],
                                   'extension_sur_orto_N': META['ortofoto']['bounds'][1]}
log('  DTM/DSM misma grilla que la ortofoto? %s (origen desplazado dx=%.3f m dy=%.3f m; %.2f / %.2f px de la orto)'
    % ('SI' if misma else 'NO', dx, dy, dx / 0.05, dy / 0.05))
log('  DTM/DSM terminan al sur en N=%.1f; la ortofoto llega a N=%.1f; la propiedad baja hasta N=%.1f'
    % (META['dsm']['bounds'][1], META['ortofoto']['bounds'][1], PROP['bounds_31982'][1]))
INFO['fuentes'] = META

# =====================================================================================
# 1. ORTOFOTO RGBA -> 0,25 m -> 0,50 m
# =====================================================================================
with Cronometro('ortofoto -> 0,25 m'):
    arr, tr_s, crs_s = leer_decimado(ORTHO_SRC, [1, 2, 3, 4], factor=5, resampling=Resampling.average, dtype='uint8')
    rgb = a_grilla(arr[:3], tr_s, crs_s, 0.25, Resampling.bilinear, nodata=np.nan, dtype='float32')
    alfa = a_grilla(arr[3], tr_s, crs_s, 0.25, Resampling.nearest, nodata=0, dtype='uint8')[0]
    del arr
    valido25 = alfa >= 200
    rgb = np.where(np.isfinite(rgb) & valido25[None], rgb, 0)
    rgba25 = np.concatenate([np.clip(np.round(rgb), 0, 255).astype('uint8'), (valido25 * 255).astype('uint8')[None]], 0)
    del rgb
    m_prop25 = rasterizar([GL['IMOVEL']], 0.25).astype(bool)
    log('  verificacion RGBA 0,25 m (dentro del imovel):')
    st = {b: verificar_arr(rgba25[i], 'orto_%s' % b, m_prop25) for i, b in enumerate('RGBA')}
    INFO['orto_0_25m_stats_imovel'] = st
    escribir(R('ortofoto_rgba.tif', 0.25), rgba25, 0.25, dtype='uint8', nodata=None,
             bandas=['R', 'G', 'B', 'alpha'], alpha=True)


def promedio_2x2(a, valido):
    """(h,w) -> (h/2,w/2) promediando solo pixeles validos."""
    a = a.astype('float32')
    v = valido.astype('float32')
    s = a[0::2, 0::2] * v[0::2, 0::2] + a[1::2, 0::2] * v[1::2, 0::2] + a[0::2, 1::2] * v[0::2, 1::2] + a[1::2, 1::2] * v[1::2, 1::2]
    n = v[0::2, 0::2] + v[1::2, 0::2] + v[0::2, 1::2] + v[1::2, 1::2]
    with np.errstate(invalid='ignore', divide='ignore'):
        out = s / n
    return out, n


with Cronometro('ortofoto -> 0,50 m (promedio 2x2 del 0,25)'):
    bandas50 = []
    for i in range(3):
        o, n = promedio_2x2(rgba25[i], valido25)
        bandas50.append(o)
    valido50 = n >= 3
    rgba50 = np.stack([np.where(valido50, np.clip(np.round(b), 0, 255), 0).astype('uint8') for b in bandas50]
                      + [(valido50 * 255).astype('uint8')], 0)
    m_prop50 = rasterizar([GL['IMOVEL']], 0.5).astype(bool)
    log('  verificacion RGBA 0,50 m (dentro del imovel):')
    for i, b in enumerate('RGBA'):
        verificar_arr(rgba50[i], 'orto50_%s' % b, m_prop50)
    escribir(R('ortofoto_rgba.tif', 0.5), rgba50, 0.5, dtype='uint8', nodata=None, bandas=['R', 'G', 'B', 'alpha'], alpha=True)

# cobertura de la ortofoto sobre cada gleba
cob = {}
for gname in ('G1', 'G2', 'IMOVEL'):
    m = rasterizar([GL[gname]], 0.25).astype(bool)
    cob[gname] = {'ortofoto_pct': round(100.0 * (valido25 & m).sum() / m.sum(), 2)}
    log('  cobertura ortofoto %s: %.2f %%' % (gname, cob[gname]['ortofoto_pct']))

# =====================================================================================
# 2. DTM / DSM -> 0,25 m (huecos pequenos rellenados) -> 0,50 m
# =====================================================================================
def rellenar_huecos(a, max_px, rotulo):
    """Rellena componentes NaN de <= max_px pixeles con el vecino valido mas cercano.
    Los huecos grandes (y el exterior) quedan NaN."""
    nan = ~np.isfinite(a)
    if not nan.any():
        return a, 0, 0
    lab, n = ndi.label(nan)
    tam = ndi.sum(nan, lab, index=np.arange(1, n + 1))
    chicos = np.zeros(n + 1, bool)
    chicos[1:] = tam <= max_px
    m_rell = chicos[lab]
    if not m_rell.any():
        log('  %s: %d huecos, ninguno <= %d px' % (rotulo, n, max_px))
        return a, 0, 0
    idx = ndi.distance_transform_edt(nan, return_distances=False, return_indices=True)
    out = a.copy()
    out[m_rell] = a[idx[0][m_rell], idx[1][m_rell]]
    log('  %s: %d huecos, %d rellenados (<= %d px, %d px en total); %d grandes quedan NaN'
        % (rotulo, n, int(chicos.sum()), max_px, int(m_rell.sum()), n - int(chicos.sum())))
    return out, int(chicos.sum()), int(m_rell.sum())


ELEV = {}
for k, p in (('dtm', DTM_SRC), ('dsm', DSM_SRC)):
    with Cronometro('%s -> 0,25 m' % k):
        arr, tr_s, crs_s = leer_decimado(p, [1], factor=5, resampling=Resampling.average, dtype='float32')
        a25 = a_grilla(arr[0], tr_s, crs_s, 0.25, Resampling.bilinear, nodata=np.nan)[0]
        del arr
        a25, n_h, px_h = rellenar_huecos(a25, max_px=400, rotulo='%s 0,25 m' % k)   # 400 px = 25 m2
        INFO['%s_huecos_rellenados' % k] = {'n': n_h, 'px': px_h, 'max_px': 400, 'max_m2': 25}
        ELEV[k] = a25
        log('  verificacion %s 0,25 m crudo (imovel):' % k)
        INFO['%s_0_25m_crudo_stats_imovel' % k] = verificar_arr(a25, k + '_crudo', m_prop25, 'm')

valido_dtm25 = np.isfinite(ELEV['dtm']) & np.isfinite(ELEV['dsm'])

# -------------------------------------------------------------------------------------
# 2b. CALIBRACION VERTICAL contra FABDEM y CONFIABILIDAD del DTM bajo dosel
#
# MEDIDO (2026-09-06): el DTM del dron esta ~40 m por debajo de FABDEM/GLO30 y con una
# INCLINACION de ~12 m entre el sur y el norte (sin GCP/RTK: sesgo GNSS + doming). Un
# polinomio de 2do grado en (x,y) ajustado (robusto) sobre suelo abierto explica el
# residuo con MAD ~0,35 m. Se corrige DTM y DSM con ese polinomio (el CHM no cambia).
#
# MEDIDO: bajo dosel cerrado el "DTM" de ODM ES el DSM (fragmento 13: 70 % de los pixeles
# con CHM < 0,5 m; transecto DSM == DTM). Y FABDEM TAMPOCO quito el bosque en estos
# fragmentos (FABDEM - GLO30 ~ -0,3 m dentro de los fragmentos 2 y 13): no existe
# referencia de suelo bajo dosel. Por eso: (i) se clasifica cobertura arborea desde la
# ortofoto + rugosidad del DSM (entrenada con copas de CHM >= 3 m vs suelo abierto);
# (ii) dosel NO penetrado = arboreo & CHM < 1 m -> DTM NO confiable; (iii) DTM HIBRIDO =
# dron donde confiable, e INTERPOLACION lineal desde el suelo visible bajo dosel
# (indicador: pierde la incision del cauce; error esperable de varios metros).
# -------------------------------------------------------------------------------------
with Cronometro('calibracion vertical (FABDEM, robusta) + confiabilidad del DTM'):
    from rasterio.warp import reproject
    tr25, h25, w25, _ = grilla(0.25)
    tr50, h50, w50, _ = grilla(0.5)
    fab50 = np.full((h50, w50), np.nan, 'float32')
    with rasterio.open(os.path.join(DATOS_SAT, 'DEM_FABDEM_AOIdem_30m.tif')) as s:
        reproject(rasterio.band(s, 1), fab50, dst_transform=tr50, dst_crs=CRS_METRICO,
                  resampling=Resampling.bilinear, dst_nodata=np.nan, src_nodata=s.nodata)
    # rasgos a 0,5 m
    dtm50r, _ = promedio_2x2(ELEV['dtm'], np.isfinite(ELEV['dtm']))
    dsm50r, _ = promedio_2x2(ELEV['dsm'], np.isfinite(ELEV['dsm']))
    chm50r = dsm50r - dtm50r
    Rr, Gg, Bb = [rgba50[i].astype('float32') for i in range(3)]
    Lum = 0.299 * Rr + 0.587 * Gg + 0.114 * Bb
    ExG = 2 * Gg - Rr - Bb
    mx = np.maximum(np.maximum(Rr, Gg), Bb); mn = np.minimum(np.minimum(Rr, Gg), Bb)
    Sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).astype('float32')
    def std_local(a, size):
        m1 = ndi.uniform_filter(a, size); m2 = ndi.uniform_filter(a * a, size)
        return np.sqrt(np.maximum(m2 - m1 * m1, 0)).astype('float32')
    TEX9 = std_local(Lum, 9)
    TEX21 = std_local(Lum, 21)
    DSMSTD = std_local(np.where(np.isfinite(dsm50r), dsm50r, 0).astype('float32'), 5)
    val50 = valido50 & np.isfinite(dtm50r) & np.isfinite(dsm50r)
    # --- (i) polinomio robusto sobre suelo SEGURO (abierto, liso, no verde) ---
    abierto = val50 & np.isfinite(fab50) & (chm50r < 0.3) & (DSMSTD < 0.08) & (ExG < 8)
    rr, cc = np.where(abierto)
    rs = np.random.RandomState(0)
    sel = rs.choice(len(rr), min(300000, len(rr)), replace=False)
    rr, cc = rr[sel], cc[sel]
    X0, Y0 = 534870.0, 7402580.0
    def diseno(xk, yk):
        return np.stack([np.ones_like(xk), xk, yk, xk * xk, yk * yk, xk * yk], 1)
    xk = (cc * 0.5 + tr50.c - X0) / 1000.0
    yk = (tr50.f - rr * 0.5 - Y0) / 1000.0
    resid = (dtm50r - fab50)[rr, cc]
    keep = np.ones(len(resid), bool)
    for it in range(4):
        coef, *_ = np.linalg.lstsq(diseno(xk[keep], yk[keep]), resid[keep], rcond=None)
        r2 = resid - diseno(xk, yk) @ coef
        mad = float(np.median(np.abs(r2[keep] - np.median(r2[keep]))))
        keep = np.abs(r2) < 3.0 * 1.4826 * mad
    log('  DTM dron - FABDEM (suelo abierto seguro, n=%d): mediana %.2f m, p10 %.2f, p90 %.2f' % (len(resid), np.median(resid), *np.percentile(resid, [10, 90])))
    log('  polinomio 2do grado robusto (km desde %.0f/%.0f, %d it, %.0f %% retenido): %s ; residuo MAD %.2f m, p10 %.2f p90 %.2f'
        % (X0, Y0, it + 1, 100 * keep.mean(), np.round(coef, 3).tolist(), mad, *np.percentile(r2[keep], [10, 90])))
    INFO['calibracion_vertical'] = {
        'referencia': 'FABDEM v1.2 30 m (EGM2008), bilineal a 0,5 m', 'muestra_n': int(len(resid)), 'muestra_retenida_pct': round(100 * float(keep.mean()), 1),
        'dtm_menos_fabdem_mediana_m': round(float(np.median(resid)), 2),
        'dtm_menos_fabdem_p10_p90_m': [round(float(v), 2) for v in np.percentile(resid, [10, 90])],
        'polinomio_grado2_coef': [round(float(c), 4) for c in coef], 'polinomio_origen': [X0, Y0], 'polinomio_unidad': 'km',
        'residuo_mad_m': round(mad, 2), 'residuo_p10_p90_m': [round(float(v), 2) for v in np.percentile(r2[keep], [10, 90])],
        'lectura': 'el DTM del dron NO tiene datum vertical utilizable (sesgo ~ -40 m e inclinacion S-N ~12 m sin GCP); '
                   'DTM y DSM se corrigen con el polinomio; cotas absolutas quedan referidas a FABDEM/EGM2008 +- %.1f m' % (2 * mad)}
    ccg, rrg = np.meshgrid(np.arange(w25), np.arange(h25))
    xg = (ccg * 0.25 + tr25.c - X0) / 1000.0
    yg = (tr25.f - rrg * 0.25 - Y0) / 1000.0
    corr = (coef[0] + coef[1] * xg + coef[2] * yg + coef[3] * xg * xg + coef[4] * yg * yg + coef[5] * xg * yg).astype('float32')
    del ccg, rrg, xg, yg
    ELEV['dtm'] = ELEV['dtm'] - corr
    ELEV['dsm'] = ELEV['dsm'] - corr
    corr50 = corr[0::2, 0::2]
    dtm50r = dtm50r - corr50; dsm50r = dsm50r - corr50
    del corr, corr50
    # --- (ii) cobertura arborea desde ortofoto + rugosidad DSM (RF; positivos = copas medidas) ---
    from sklearn.ensemble import RandomForestClassifier
    feats = np.stack([Rr, Gg, Bb, Lum, ExG, Sat, TEX9, TEX21, DSMSTD], -1)
    pos = val50 & (chm50r >= 3.0) & (ExG > 5)
    neg = val50 & (chm50r < 0.3) & (DSMSTD < 0.10)
    ip = np.flatnonzero(pos); im = np.flatnonzero(neg)
    ip = rs.choice(ip, min(60000, len(ip)), replace=False); im = rs.choice(im, min(60000, len(im)), replace=False)
    F2 = feats.reshape(-1, feats.shape[-1])
    Xtr = np.concatenate([F2[ip], F2[im]])
    ytr = np.concatenate([np.ones(len(ip)), np.zeros(len(im))])
    rf = RandomForestClassifier(n_estimators=120, min_samples_leaf=20, n_jobs=-1, random_state=0)
    idx_tr = rs.permutation(len(ytr)); n_val = len(ytr) // 5
    rf.fit(Xtr[idx_tr[n_val:]], ytr[idx_tr[n_val:]])
    acc = float((rf.predict(Xtr[idx_tr[:n_val]]) == ytr[idx_tr[:n_val]]).mean())
    prob = np.zeros((h50, w50), 'float32')
    vv = np.flatnonzero(val50 & valido50)
    prob.reshape(-1)[vv] = rf.predict_proba(F2[vv])[:, 1]
    arb = prob > 0.5
    arb = ndi.binary_opening(arb, iterations=1)
    arb = ndi.binary_closing(arb, iterations=2)
    lab, n = ndi.label(arb)
    tam = ndi.sum(arb, lab, np.arange(1, n + 1)) * 0.25
    kp = np.zeros(n + 1, bool); kp[1:] = tam >= 25
    arb = kp[lab]
    imp = dict(zip(['R', 'G', 'B', 'L', 'ExG', 'S', 'TEX9', 'TEX21', 'DSMSTD'], np.round(rf.feature_importances_, 3).tolist()))
    log('  clasificador arboreo (ortofoto+DSM): acc validacion %.3f; importancias %s; arboreo %.2f ha en el imovel'
        % (acc, imp, (arb & m_prop50).sum() * 0.25 / 1e4))
    # --- (iii) dosel no penetrado -> DTM no confiable ---
    arb_fill = ndi.binary_fill_holes(ndi.binary_closing(arb, iterations=4))   # parches de dosel sin huecos de sombra
    dosel50 = arb_fill & (chm50r < 1.0)
    dosel50 = ndi.binary_closing(dosel50, iterations=3)
    dosel50 = ndi.binary_opening(dosel50, iterations=1) & val50
    dosel = np.repeat(np.repeat(dosel50, 2, 0), 2, 1)[:h25, :w25]
    arb_up = np.repeat(np.repeat(arb_fill, 2, 0), 2, 1)[:h25, :w25]
    confiavel = valido_dtm25 & ~dosel
    # anclajes de la interpolacion: todo pixel confiable, INCLUIDOS los claros entre copas (ahi el SMRF
    # de ODM si encontro suelo y es la unica informacion del fondo del valle). Probado (2026-09-06):
    # anclar solo en suelo sin arboles a >2 m de las copas interpola el valle por encima del dosel.
    ancla = confiavel
    ha_dosel = float((dosel & m_prop25).sum()) * 0.0625 / 1e4
    ha_conf = float((confiavel & m_prop25).sum()) * 0.0625 / 1e4
    ha_arb = float((arb & m_prop50).sum()) * 0.25 / 1e4
    log('  DTM NO confiable (dosel no penetrado = arboreo & CHM < 1 m): %.2f ha en el imovel (arboreo total %.2f ha); confiable %.2f ha'
        % (ha_dosel, ha_arb, ha_conf))
    # --- DTM hibrido bajo dosel = envolvente inferior del DSM (apertura gris 15 m) ---
    # Probado (2026-09-06): interpolar desde el suelo visible (con o sin claros como anclaje) deja
    # el "suelo" al nivel del dosel o por encima del valle: el DTM del dron alrededor de las copas
    # ya es una superficie intermedia. La apertura gris toma el punto mas bajo en 7,5 m (claros
    # entre copas): mas cerca del suelo que la copa, sesgo ~pendiente x 7,5 m. INDICADOR.
    VENTANA_APERTURA_M = 15.0
    kpx = int(round(VENTANA_APERTURA_M / 0.25)) | 1
    dsm_fill = np.where(np.isfinite(ELEV['dsm']), ELEV['dsm'], np.nanmax(ELEV['dsm'])).astype('float32')
    envolvente = ndi.grey_opening(dsm_fill, size=(kpx, kpx))
    del dsm_fill
    dtm_hib = np.where(confiavel, ELEV['dtm'], np.minimum(ELEV['dtm'], envolvente)).astype('float32')
    dtm_hib = np.where(valido_dtm25, dtm_hib, np.nan)
    del envolvente
    dif_h = (ELEV['dsm'] - dtm_hib)[dosel & m_prop25]
    log('  DTM hibrido bajo dosel: DSM - DTM_hib p10/50/90 = %.1f / %.1f / %.1f m (altura aparente del dosel; indicador +- varios m)' % tuple(np.nanpercentile(dif_h, [10, 50, 90])))
    fonte = np.zeros((h25, w25), 'uint8')
    fonte[confiavel] = 1
    fonte[dosel] = 2
    INFO['dtm_confiabilidade'] = {'regla': 'arboreo (RF ortofoto+DSM, acc %.3f) & CHM_dron < 1 m -> dosel no penetrado' % acc,
                                  'ha_dosel_imovel': round(ha_dosel, 2), 'ha_arboreo_imovel_0_5m': round(ha_arb, 2), 'ha_confiavel_imovel': round(ha_conf, 2),
                                  'pct_dosel_de_area_com_dtm': round(100 * ha_dosel / (ha_dosel + ha_conf), 1),
                                  'dsm_menos_dtm_hibrido_bajo_dosel_p10_50_90_m': [round(float(v), 1) for v in np.nanpercentile(dif_h, [10, 50, 90])],
                                  'lectura': 'bajo dosel cerrado el DTM fotogrametrico es el propio dosel (CHM ~ 0, canal invisible) y FABDEM tampoco '
                                             'quito el bosque en estos fragmentos: NO hay referencia de suelo bajo dosel. DTM hibrido = envolvente '
                                             'inferior del DSM (apertura gris 15 m) bajo dosel: indicador, NO mide la incision del cauce.'}
    for k in ('dtm', 'dsm'):
        a25 = ELEV[k]
        log('  verificacion %s 0,25 m CALIBRADO (imovel):' % k)
        INFO['%s_0_25m_stats_imovel' % k] = verificar_arr(a25, k, m_prop25, 'm')
        escribir(R('%s.tif' % k, 0.25), a25, 0.25, bandas=[k], tags={'unidad': 'm (calibrado a FABDEM/EGM2008)', 'calibracion': 'polinomio grado 2 vs FABDEM'})
        a50, n = promedio_2x2(a25, np.isfinite(a25))
        a50 = np.where(n >= 2, a50, np.nan)
        ELEV[k + '50'] = a50
        verificar_arr(a50, k + ' 0,50', m_prop50, 'm')
        escribir(R('%s.tif' % k, 0.5), a50, 0.5, bandas=[k], tags={'unidad': 'm (calibrado a FABDEM/EGM2008)'})
    verificar_arr(dtm_hib, 'dtm_hibrido 0,25', m_prop25, 'm')
    escribir(R('dtm_hibrido.tif', 0.25), dtm_hib, 0.25, bandas=['dtm_hibrido'], tags={'unidad': 'm', 'regla': 'dron donde confiable; apertura gris 15 m del DSM bajo dosel (indicador)'})
    h50v, n = promedio_2x2(dtm_hib, np.isfinite(dtm_hib))
    ELEV['dtm_hib50'] = np.where(n >= 2, h50v, np.nan)
    escribir(R('dtm_hibrido.tif', 0.5), ELEV['dtm_hib50'], 0.5, bandas=['dtm_hibrido'], tags={'unidad': 'm'})
    escribir(R('dtm_fonte.tif', 0.25), fonte, 0.25, dtype='uint8', nodata=0, bandas=['fonte'], tags={'leyenda': '1=DTM dron confiable; 2=dosel no penetrado (DTM=DSM), interpolado'})
    f50 = np.where(dosel50, 2, np.where(val50, 1, 0)).astype('uint8')
    escribir(R('dtm_fonte.tif', 0.5), f50, 0.5, dtype='uint8', nodata=0, bandas=['fonte'], tags={'leyenda': '1=DTM dron confiable; 2=dosel no penetrado (DTM=DSM), interpolado'})
    escribir(R('arboreo_rf_ortofoto.tif', 0.5), arb.astype('uint8'), 0.5, dtype='uint8', nodata=None, bandas=['arboreo'],
             tags={'leyenda': '1=cobertura arborea (RF ortofoto+DSM entrenado con copas CHM>=3 m); 0=no'})
    escribir(R('arboreo_prob_ortofoto.tif', 0.5), prob, 0.5, bandas=['prob_arboreo'], tags={'unidad': 'probabilidad 0-1'})
    ELEV['dtm_hib'] = dtm_hib
    ELEV['fonte'] = fonte
    del fab50, feats, F2, prob, dtm50r, dsm50r, chm50r, TEX9, TEX21, DSMSTD, Rr, Gg, Bb, Lum, ExG, Sat

# --- cobertura DTM+DSM por gleba y huellas vectoriales (para los scripts siguientes) ---------
for gname in ('G1', 'G2', 'IMOVEL'):
    m = rasterizar([GL[gname]], 0.25).astype(bool)
    cob[gname]['dtm_dsm_pct'] = round(100.0 * (valido_dtm25 & m).sum() / m.sum(), 2)
    cob[gname]['ortofoto_y_dtm_pct'] = round(100.0 * (valido_dtm25 & valido25 & m).sum() / m.sum(), 2)
    log('  cobertura DTM+DSM %s: %.2f %%  (orto y DTM: %.2f %%)' % (gname, cob[gname]['dtm_dsm_pct'], cob[gname]['ortofoto_y_dtm_pct']))
INFO['cobertura_pct'] = cob

with Cronometro('huellas de cobertura'):
    import geopandas as gpd
    from shapely.ops import unary_union
    from shapely.geometry import mapping
    h_orto = vectorizar(ndi.binary_opening(valido25, iterations=2), 0.25, min_area_m2=100)
    h_dtm = vectorizar(ndi.binary_opening(valido_dtm25, iterations=2), 0.25, min_area_m2=100)
    H_ORTO = unary_union(list(h_orto.geometry)).simplify(0.5)
    H_DTM = unary_union(list(h_dtm.geometry)).simplify(0.5)
    sin_orto = poly_only(GL['IMOVEL'].difference(H_ORTO))
    sin_dtm = poly_only(GL['IMOVEL'].difference(H_DTM))
    hue = gpd.GeoDataFrame({'capa': ['ortofoto', 'dtm_dsm', 'imovel_sem_ortofoto', 'imovel_sem_dtm'],
                            'area_ha': [ha(H_ORTO), ha(H_DTM), ha(sin_orto), ha(sin_dtm)]},
                           geometry=[H_ORTO, H_DTM, sin_orto, sin_dtm], crs=CRS_METRICO)
    guardar_gdf(hue, R('cobertura_vuelo.geojson'))
    sin = {}
    for gname in ('G1', 'G2'):
        so = poly_only(GL[gname].difference(H_ORTO)); sd = poly_only(GL[gname].difference(H_DTM))
        sin[gname] = {'sem_ortofoto_ha': ha(so), 'sem_dtm_ha': ha(sd),
                      'sem_ortofoto_N_min': round(so.bounds[1], 1) if not so.is_empty else None,
                      'sem_dtm_N_max': round(sd.bounds[3], 1) if not sd.is_empty else None}
    INFO['sem_cobertura'] = sin
    log('  sin cobertura: %s' % sin)
    guardar_json(R('cobertura_vuelo.json'), {'ortofoto': mapping(H_ORTO), 'dtm_dsm': mapping(H_DTM),
                                             'imovel_sem_ortofoto': mapping(sin_orto), 'imovel_sem_dtm': mapping(sin_dtm),
                                             'resumen': sin, 'cobertura_pct': cob})

# =====================================================================================
# 3. CHM = DSM - DTM  (recortado a [0, 40] m)
# =====================================================================================
with Cronometro('CHM'):
    for nombre, res, d, t, m in ((('chm', 0.25, ELEV['dsm'], ELEV['dtm'], m_prop25)),
                                 ('chm', 0.5, ELEV['dsm50'], ELEV['dtm50'], m_prop50),
                                 ('chm_hibrido', 0.25, ELEV['dsm'], ELEV['dtm_hib'], m_prop25),
                                 ('chm_hibrido', 0.5, ELEV['dsm50'], ELEV['dtm_hib50'], m_prop50)):
        chm = d - t
        n_neg = int((chm < 0).sum()); n_alto = int((chm > 40).sum())
        chm = np.clip(chm, 0, 40)
        chm = np.where(np.isfinite(d) & np.isfinite(t), chm, np.nan)
        st = verificar_arr(chm, '%s %.2f' % (nombre, res), m, 'm')
        bins = [0, 0.5, 1, 2, 3, 5, 10, 15, 20, 25, 30, 40.01]
        hist, _ = np.histogram(chm[m & np.isfinite(chm)], bins=bins)
        tot = hist.sum()
        hist_pct = {('%g-%g m' % (bins[i], min(bins[i + 1], 40))): round(100.0 * hist[i] / tot, 2) for i in range(len(hist))}
        log('  histograma %s %.2f m (imovel, %% del area con dato): %s' % (nombre, res, hist_pct))
        log('  %s %.2f: %d px < 0 (DSM<DTM, forzados a 0) y %d px > 40 m (recortados)' % (nombre, res, n_neg, n_alto))
        INFO['%s_%s' % (nombre, res)] = {'stats_imovel': st, 'histograma_pct': hist_pct, 'px_negativos': n_neg, 'px_gt40': n_alto,
                                         'ha_con_dato': round(tot * res * res / 1e4, 2)}
        tag = 'DSM - DTM dron, recortado [0,40]; ~0 bajo dosel cerrado (DTM=DSM)' if nombre == 'chm' else \
              'DSM - DTM hibrido (FABDEM bajo dosel), recortado [0,40]; +-2-3 m bajo dosel'
        escribir(R('%s.tif' % nombre, res), chm, res, bandas=[nombre], tags={'unidad': 'm', 'formula': tag})
        if res == 0.5 and nombre == 'chm_hibrido':
            CHM50 = chm
    del ELEV['dtm_hib']

# =====================================================================================
# 4. hillshade + pendiente del DTM HIBRIDO 0,5 m
# =====================================================================================
with Cronometro('hillshade + pendiente (DTM hibrido 0,5 m)'):
    dtm = ELEV['dtm_hib50']
    gy, gx = np.gradient(dtm, 0.5, 0.5)     # gy: hacia abajo en filas = hacia el sur
    pend = np.degrees(np.arctan(np.hypot(gx, gy)))
    az, alt = np.radians(315.0), np.radians(45.0)
    aspect = np.arctan2(-gx, gy)
    slope_r = np.arctan(np.hypot(gx, gy))
    hs = (np.sin(alt) * np.cos(slope_r) + np.cos(alt) * np.sin(slope_r) * np.cos(az - np.pi / 2 - aspect))
    hs = np.clip(np.round(255 * (hs + 1) / 2), 0, 255)
    hs = np.where(np.isfinite(dtm), hs, 0).astype('uint8')
    verificar_arr(pend, 'pendiente', m_prop50, 'grados')
    verificar_arr(hs.astype('float32'), 'hillshade', m_prop50)
    INFO['pendiente_0_5m_stats_imovel'] = verificar_arr(pend, 'pendiente(imovel)', m_prop50, 'grados')
    escribir(R('dtm_pendiente.tif', 0.5), pend, 0.5, bandas=['pendiente_graus'], tags={'unidad': 'graus'})
    escribir(R('dtm_hillshade.tif', 0.5), hs, 0.5, dtype='uint8', nodata=0, bandas=['hillshade'])

# =====================================================================================
# 5. ALINEACION
# =====================================================================================
from skimage.registration import phase_cross_correlation
from skimage.filters import sobel


def lum(rgba):
    r, g, b = [rgba[i].astype('float32') for i in range(3)]
    return 0.299 * r + 0.587 * g + 0.114 * b


def ventana(a, tr, cx, cy, semi):
    """Sub-arreglo cuadrado de semi-lado `semi` m centrado en (cx, cy)."""
    c0, r0 = ~tr * (cx - semi, cy + semi)
    c1, r1 = ~tr * (cx + semi, cy - semi)
    r0, r1, c0, c1 = int(round(r0)), int(round(r1)), int(round(c0)), int(round(c1))
    r0, c0 = max(r0, 0), max(c0, 0)
    return a[r0:r1, c0:c1], (r0, r1, c0, c1)


VENTANAS = {  # 3 objetos identificables (ver _ortho_overview.png de 02_ANALISIS) + apoyo
    'dique_represa': (534990.0, 7401620.0, 150),
    'sede_edificios': (535090.0, 7401460.0, 120),
    'esquina_G1_G2': (535140.0, 7403180.0, 150),
    'nascente_frag13_borde': (534930.0, 7402990.0, 150),
}
VENTANAS_DSM = {  # dentro de la huella del DSM (N > 7401711): bordes de dosel / caminos
    'esquina_G1_G2': (535140.0, 7403180.0, 120),
    'nascente_frag13_borde': (534930.0, 7402990.0, 120),
    'borde_oeste_frag13': (534760.0, 7403300.0, 120),
    'faixa_norte_arroio1': (534850.0, 7403900.0, 90),
}
ALIN = {}

# 5a. ortofoto <-> DSM (a 0,5 m, bordes: sobel de luminancia vs sobel del DSM). Solo hay DSM al norte de N 7401711.
with Cronometro('alineacion ortofoto <-> DSM (bordes, correlacion de fase)'):
    tr50, _, _, _ = grilla(0.5)
    L50 = lum(rgba50)
    L50 = np.where(valido50, L50, np.nan)
    dsm50 = ELEV['dsm50']
    res_dsm = {}
    for nombre, (cx, cy, semi) in VENTANAS_DSM.items():
        a, _ = ventana(L50, tr50, cx, cy, semi)
        b, _ = ventana(dsm50, tr50, cx, cy, semi)
        ok = np.isfinite(a) & np.isfinite(b)
        if ok.mean() < 0.8 or a.size < 10000:
            res_dsm[nombre] = {'estado': 'sin DSM en la ventana (%.0f %% valido)' % (100 * ok.mean())}
            log('  DSM<->orto %-24s sin dato suficiente (%.0f %% valido)' % (nombre, 100 * ok.mean()))
            continue
        ea = sobel(np.where(ok, a, np.nanmean(a[ok])))
        eb = sobel(np.where(ok, b, np.nanmean(b[ok])))
        ea = (ea - ea.mean()) / (ea.std() + 1e-9); eb = (eb - eb.mean()) / (eb.std() + 1e-9)
        sh, err, _ = phase_cross_correlation(ea, eb, upsample_factor=10)
        dxm, dym = float(sh[1] * 0.5), float(-sh[0] * 0.5)    # fila hacia abajo = sur
        res_dsm[nombre] = {'dx_m': round(dxm, 2), 'dy_m': round(dym, 2), 'error': round(float(err), 3),
                           'centro': [cx, cy], 'semi_m': semi}
        log('  DSM<->orto %-24s desplazamiento dx=%+.2f m dy=%+.2f m (err %.3f)' % (nombre, dxm, dym, err))
    ALIN['ortofoto_vs_dsm'] = res_dsm
    ALIN['ortofoto_vs_dsm_nota'] = ('grillas nativas distintas (origenes desplazados %.3f/%.3f m; pixel %.7f vs %.5f m); '
                                    'ambos remuestreados a la grilla comun por georreferencia. Desplazamiento residual medido '
                                    'por correlacion de fase de bordes a 0,5 m.' % (dx, dy, META['ortofoto']['res'][0], META['dsm']['res'][0]))

# 5b. ortofoto <-> S2 RGB 10 m (grilla S2: origen 532980/7405650 multiplo de 10; la grilla comun tambien -> bloques 20x20 de 0,5 m)
with Cronometro('alineacion ortofoto <-> Sentinel-2 RGB 10 m'):
    with rasterio.open(PREV['s2_rgb']) as s2:
        tr10, h10, w10, b10 = grilla(10)
        win = rasterio.windows.from_bounds(*b10, transform=s2.transform)
        s2rgb = s2.read(window=win, out_shape=(3, h10, w10), resampling=Resampling.nearest).astype('float32')
        assert abs(s2.transform.c % 10) < 1e-6 and abs(tr10.c % 10) < 1e-6
    Ls2 = 0.299 * s2rgb[0] + 0.587 * s2rgb[1] + 0.114 * s2rgb[2]
    # ortofoto 0,5 m -> 10 m por promedio de bloques 20x20 (misma grilla: origen multiplo de 10)
    hh, ww = (L50.shape[0] // 20) * 20, (L50.shape[1] // 20) * 20
    Lb = L50[:hh, :ww].reshape(hh // 20, 20, ww // 20, 20)
    vb = valido50[:hh, :ww].reshape(hh // 20, 20, ww // 20, 20)
    with np.errstate(invalid='ignore'):
        L10 = np.nansum(np.where(vb, Lb, 0), axis=(1, 3)) / vb.sum(axis=(1, 3))
    frac = vb.mean(axis=(1, 3))
    L10 = np.where(frac > 0.95, L10, np.nan)
    assert L10.shape == Ls2.shape, (L10.shape, Ls2.shape)
    res_s2 = {}
    for nombre, (cx, cy, semi) in list(VENTANAS.items()) + [('global_imovel', (534870.0, 7402580.0, 1500))]:
        a, _ = ventana(L10, tr10, cx, cy, max(semi, 150))
        b, _ = ventana(Ls2, tr10, cx, cy, max(semi, 150))
        ok = np.isfinite(a) & (b > 0)
        if ok.sum() < 200:
            res_s2[nombre] = {'estado': 'sin dato suficiente'}
            continue
        ea = np.where(ok, a, np.nanmean(a[ok])); eb = np.where(ok, b, np.nanmean(b[ok]))
        ea = (ea - ea.mean()) / (ea.std() + 1e-9); eb = (eb - eb.mean()) / (eb.std() + 1e-9)
        sh, err, _ = phase_cross_correlation(ea, eb, upsample_factor=20)
        dxm, dym = float(sh[1] * 10), float(-sh[0] * 10)
        res_s2[nombre] = {'dx_m': round(dxm, 1), 'dy_m': round(dym, 1), 'error': round(float(err), 3), 'centro': [cx, cy]}
        log('  S2<->orto  %-24s desplazamiento dx=%+.1f m dy=%+.1f m (err %.3f, n=%d px de 10 m)' % (nombre, dxm, dym, err, ok.sum()))
    ALIN['ortofoto_vs_s2_10m'] = res_s2
    ALIN['ortofoto_vs_s2_nota'] = ('luminancia de la ortofoto promediada a la grilla S2 de 10 m vs luminancia S2 RGB 29-ago-2026 '
                                   '(fechas distintas: mayo vs agosto; correlacion de fase con sobremuestreo 20x = 0,5 m). '
                                   'Signo: dx>0 = la S2 esta al ESTE de la ortofoto; dy>0 = al NORTE.')
INFO['alineacion'] = ALIN
INFO['alineacion_fbds'] = 'se mide en ortho_02 (espejo represa vs massa FBDS) y ortho_03 (talweg DTM vs eje FBDS)'

guardar_json(R('ortho_01_info.json'), INFO)

# figura de control
with Cronometro('figura de control'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(16, 14))
    tr50, _, _, b50 = grilla(0.5)
    ext = [b50[0], b50[2], b50[1], b50[3]]
    ax[0].imshow(np.moveaxis(rgba50[:3], 0, -1), extent=ext); ax[0].set_title('ortofoto 0,5 m')
    ax[1].imshow(ELEV['dtm50'], extent=ext, cmap='terrain'); ax[1].set_title('DTM 0,5 m')
    ax[2].imshow(CHM50, extent=ext, cmap='viridis', vmin=0, vmax=25); ax[2].set_title('CHM 0,5 m (0-25 m)')
    ax[3].imshow(hs, extent=ext, cmap='gray'); ax[3].set_title('hillshade')
    for a in ax:
        for gname in ('G1', 'G2'):
            g = GL[gname]
            for p in (g.geoms if hasattr(g, 'geoms') else [g]):
                x, y = p.exterior.xy; a.plot(x, y, 'y-', lw=0.8)
        a.set_xticks([]); a.set_yticks([])
    plt.tight_layout(); plt.savefig(R('_check_ortho_01.png'), dpi=110); plt.close()
    log('  -> _check_ortho_01.png')
log('ortho_01 listo.')
