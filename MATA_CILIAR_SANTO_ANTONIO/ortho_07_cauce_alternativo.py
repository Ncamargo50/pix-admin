# -*- coding: utf-8 -*-
"""ortho_07: LARGURA DA CALHA DO LEITO REGULAR (Lei 12.651 art. 4o I, umbral 10 m) por
METODOS ALTERNATIVOS, porque bajo dosel cerrado el DTM fotogrametrico del dron es la copa
(ortho_03: Arroio 1 = 3 de 26 secciones con suelo; Arroio 2 = 0 de 56; Arroio 3 sin DSM/DTM).

M1  claros del dosel en la ortofoto 5 cm: agua / leito humedo por color+textura (rasgos de
    ortho_02: L, ExG, S, BR, TEX), componentes lineales >= 3 m; ancho = 2 x EDT sobre el
    esqueleto (espejo) y borde de vegetacion herbacea por perfil de ExG (calha_veg).
M2  suelo visible DSM-DTM: estaciones cada 2 m donde CHM < 0,5 m y dtm_fonte = 1 (suelo);
    perfil DTM 5 cm (lectura por ventana del dtm.tif original) +-15 m; regla bankfull de
    ortho_03 (fondo + h, h = 0,5 / 1,0; quiebre de pendiente); exige minimo local transversal.
M3  geometria hidraulica regional W = a A^b con A (km2) de la acumulacion local (30 m, ensamble
    5 DEM) y del otto IAT 2020 / ANA BHO (nuareamont); coeficientes VERIFICADOS (ver REFS).
M4  atributos oficiales: IBGE BC250 larguramedia/regime, clase FBDS (<= 10 m), ANA BHO 5k, CAR.
M5  protocolo de campo (cinta/GNSS) para cerrar el numero con validez administrativa.

NO modifica archivos existentes. Salidas nuevas en 05_ORTOFOTO/cauce/.
"""
import os
import sys
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comun as _comun
import ortho_00_comun as _oc
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.windows import from_bounds, Window
from rasterio.features import rasterize as _rasterize
from scipy import ndimage as ndi
from shapely.geometry import LineString, Point, Polygon, MultiLineString, shape, box
from shapely.ops import unary_union, linemerge

CAUCE = os.path.join(SALIDA, 'cauce')
RECORTES = os.path.join(CAUCE, 'cauce_recortes')
os.makedirs(RECORTES, exist_ok=True)
for _f in os.listdir(RECORTES):          # recortes de corridas anteriores fuera: la carpeta refleja SOLO esta corrida
    os.remove(os.path.join(RECORTES, _f))
_LOGF = open(os.path.join(CAUCE, 'log_ortho_07.txt'), 'w', encoding='utf-8')


def log(msg=''):
    print(msg, flush=True)
    _LOGF.write(str(msg) + '\n'); _LOGF.flush()


_comun.log = log; _oc.log = log     # los helpers de ortho_00_comun (verificar_arr, escribir...) tambien escriben al log

log('=' * 78)
log('ortho_07_cauce_alternativo  ortofoto/DSM/DTM dron %s' % FECHA_VUELO)
log('=' * 78)

# =====================================================================================
# 0. PARAMETROS (todo lo que decide una medicion esta aca y va al JSON)
# =====================================================================================
PASO_M = 2.0                 # estaciones cada 2 m
CORREDOR_M = {'Arroio 1 (norte)': 40.0, 'Arroio 2 (central)': 40.0, 'Arroio 3 (sul)': 50.0}   # A3: eje FBDS (p90 FBDS-talweg = 44 m)
RES_ORTO = 0.05
M1 = {'L_max': 150.0, 'ExG_max': 8.0, 'ExG_min': -25.0, 'TEX_max': 5.0, 'TEX_win_px': 21, 'BR_min': -0.20, 'BR_max': 0.06, 'S_max': 0.50, 'dist_represa_vertedouro_m': 60.0,
      'abrir_it': 2, 'cerrar_it': 2, 'area_min_m2': 0.5, 'comprimento_min_m': 3.0, 'comprimento_alta_m': 5.0,
      'dist_eixo_max_m': None, 'alinhamento_min_cos': 0.70, 'dsm_std_plano_m': 0.15,
      'calha_ExG_veg': 20.0, 'calha_TEX_veg': 12.0, 'calha_suav_m': 1.0, 'calha_max_m': 20.0,
      'nota': 'rasgos de ortho_02 (agua represa: L 130, ExG -7,5, BR -0,10, TEX baja; reservatorio cabecera: L 69, ExG -7,7, BR -0,09). '
              'Sombras son azuladas (BR > 0): BR_max = 0,06 las excluye. El leito humedo (marron oscuro, ExG < 0) cuenta como espejo/leito. '
              'MEDIDO en la 1a corrida: el suelo rojo desnudo (Terra Roxa: ExG -40..-57, BR -0,26..-0,29, L 90-125, TEX < 5) pasaba como agua en las huellas de una estrada; '
              'ExG_min = -25 y BR_min = -0,20 lo excluyen (agua real medida: ExG -2..-8, BR -0,10..+0,02). Componentes a < 60 m de la represa = vertedouro/saida (artificial): NO cuentan para la calha natural.'}
M2 = {'chm_max_m': 0.5, 'semi_centro_m': 3.0, 'perfil_semi_m': 15.0, 'dx': 0.05, 'fondo_semi_m': 8.0, 'canal_h_min_m': 0.30, 'dist_borda_huella_min_m': 20.0, 'arboreo_bosque_pct': 50.0,
      'h_bankfull': [0.5, 1.0], 'quiebre': {'h_min': 0.3, 'pend_alta': 0.20, 'pend_baja': 0.10, 'win_m': 1.0},
      'arboreo_min_pct': 20.0, 'nota': 'regla de secciones de ortho_03 aplicada al DTM ORIGINAL 5 cm; exige dtm_fonte = 1 en +-3 m y CHM < 0,5 m; '
                                       'minimo local transversal = ambos lados suben >= 0,30 m dentro de 8 m. MEDIDO en la 1a corrida: las secciones "validas" caian (i) a < 20 m del borde de la huella del DTM '
                                       '(artefacto de borde, 11-18 m) y (ii) en el campo cosechado pegado al bosque (el talweg de ortho_03 bajo dosel se desvia al borde campo-floresta). '
                                       'Por eso: se exige >= 20 m al borde de la huella y se clasifica el perfil por % arboreo: >= 50 bosque (cuenta), 20-50 borda campo-floresta (NO cuenta), < 20 campo (NO cuenta).'}
M3_CURVAS = {
    'bieger2015_usa': {'a': 2.70, 'b': 0.352, 'r2': 0.66, 'see_log10': 0.24, 'n': 1279, 'unidades': 'W m, A km2',
                       'ref': 'Bieger, Rathjens, Allen & Arnold (2015) JAWRA 51(3):842-858, Tabla 3, modelo nacional EUA. DOI 10.1111/jawr.12282 (VERIFICADO)'},
    'bieger2015_ahi': {'a': 3.12, 'b': 0.415, 'r2': 0.87, 'see_log10': 0.12, 'n': 377, 'unidades': 'W m, A km2',
                       'ref': 'idem, Appalachian Highlands (humedo, forestal): analogo climatico mas cercano dentro del set; DOI 10.1111/jawr.12282 (VERIFICADO)'},
}
M3_ENVOLVENTE = {'fernandez2004_oeste_pr': {'A_km2': [1.11, 9.70], 'W_mp_m': [3.06, 8.48], 'n': 8, 'r2_W_vs_A': 0.11,
                                             'ref': 'Fernandez, O.V.Q. (2004) Relacoes da geometria hidraulica em nivel de margens plenas nos corregos de Marechal Candido Rondon, oeste do Parana. Geosul 19(37). '
                                                    'SIN DOI (revista sin DOI en 2004; PDF verificado en periodicos.ufsc.br). 8 secoes, corregos de 2a ordem, W_mp medida 3,06-8,48 m para A 1,1-9,7 km2. '
                                                    'R2 0,11: NO sirve como curva; sirve como ENVOLVENTE empirica regional.'}}
M3_NO_APLICADAS = [
    'Moody & Troutman (2002) ESPL 27(12):1251-1266, DOI 10.1002/esp.403 (VERIFICADO): W = 7,2 Q^0,5 exige VAZAO; sin Q de margens plenas medida no se aplica (queda para M5 / estacion).',
    'Grison & Kobiyama (2011) RBRH 16(2):111-131, DOI 10.21168/rbrh.v16n2.p111-131 (VERIFICADO): Q margens plenas (Tr 1,58 a) vs area em 448 estacoes do PR; el resumen no da la ecuacion de LARGURA: no aplicada.',
    'Fernandez (s/d) "Curvas de la geometria hidraulica regional para rios del estado de Parana": A 969-12.124 km2, fuera de rango (aqui 0,1-13 km2) y texto no accesible: NO VERIFICADO, no aplicada.',
    'Wilkerson et al. (2014) WRR 50:919-936, DOI 10.1002/2013WR013916 (VERIFICADO): W = alfa A^beta por ecorregion EUA, beta 0,22-0,38; coeficientes no extraidos del texto completo: solo como contexto del exponente.',
    'Andrews (1984) GSA Bull 95(3):371-378, DOI 10.1130/0016-7606(1984)95<371:BEAHGO>2.0.CO;2 (VERIFICADO): rios de grava de Colorado, no transferible.',
]

# =====================================================================================
# 1. INSUMOS
# =====================================================================================
GL = glebas()
IMOVEL = GL['IMOVEL']
COB = cobertura()
H_ORTO = shape(COB['ortofoto']); H_DTM = shape(COB['dtm_dsm'])
tr25, h25, w25, b25 = grilla(0.25)
tr50, h50, w50, b50 = grilla(0.5)
with Cronometro('capas 0,25 / 0,5 m'):
    chm25, _ = leer(R('chm_hibrido.tif', 0.25)); chm25 = chm25[0]
    fonte25, _ = leer(R('dtm_fonte.tif', 0.25), nan=False); fonte25 = fonte25[0]
    dsm25, _ = leer(R('dsm.tif', 0.25)); dsm25 = dsm25[0]
    arb50, _ = leer(R('arboreo_rf_ortofoto.tif', 0.5), nan=False); arb50 = arb50[0].astype('float32')
    VERIF = {}
    VERIF['chm_hibrido_0_25m'] = verificar_arr(chm25, 'chm_hibrido 0,25', unidades='m')
    VERIF['dtm_fonte_0_25m'] = verificar_arr(fonte25.astype('float32'), 'dtm_fonte 0,25 (1 suelo, 2 dosel)')
    VERIF['dsm_0_25m'] = verificar_arr(dsm25, 'dsm 0,25', unidades='m')
    VERIF['arboreo_rf_0_50m'] = verificar_arr(arb50, 'arboreo_rf 0,5 (0/1)')

eixos = gpd.read_file(R('eixo_dtm_arroios.geojson'))
arr_g1 = cargar('arroios_g1')
agua = gpd.read_file(R('agua_ortofoto_%s.geojson' % FECHA_VUELO))
REPRESA = unary_union(list(agua[agua.corpo.isin(['represa_principal', 'represa_vaso_indicador'])].geometry))
RESERV_CAB = unary_union(list(agua[agua.corpo.isin(['reservatorio_cabeceira_arroio2', 'reservatorio_cabeceira_vaso'])].geometry))

ARROIOS = []
for _, r in arr_g1.iterrows():
    nome = r['nome']
    e = eixos[eixos.arroio == nome]
    if len(e):
        eje = e.geometry.iloc[0]; fuente = 'talweg DTM dron (ortho_03)'
    else:
        eje = r.geometry; fuente = 'eixo FBDS (sem DTM)'
    if eje.geom_type == 'MultiLineString':
        eje = linemerge(eje)
        if eje.geom_type == 'MultiLineString':
            eje = max(eje.geoms, key=lambda g: g.length)
    ARROIOS.append({'nome': nome, 'n': int(r['n']), 'eje': eje, 'fuente_eje': fuente, 'fbds': r.geometry, 'fbds_ids': r['fbds_ids']})
    log('  %s: eje %s, %.0f m' % (nome, fuente, eje.length))


# =====================================================================================
# 2. HELPERS
# =====================================================================================
def perpendicular(linea, s, ds=10.0):
    p0 = linea.interpolate(max(0, s - ds)); p1 = linea.interpolate(min(linea.length, s + ds))
    tx, ty = p1.x - p0.x, p1.y - p0.y
    n = np.hypot(tx, ty) or 1.0
    return (-ty / n, tx / n), (tx / n, ty / n)      # normal (izq mirando aguas abajo), tangente


def muestrear(a, tr, xs, ys, order=1):
    cols, rows = ~tr * (xs, ys)
    return ndi.map_coordinates(a, [rows, cols], order=order, mode='constant', cval=np.nan)


def orilla_h(z, x, i0, h):
    nivel = z[i0] + h
    xl = xr = None
    for i in range(i0, -1, -1):
        if z[i] >= nivel:
            xl = np.interp(nivel, [z[i + 1], z[i]], [x[i + 1], x[i]]) if i + 1 < len(z) and z[i] != z[i + 1] else x[i]
            break
    for i in range(i0, len(z)):
        if z[i] >= nivel:
            xr = np.interp(nivel, [z[i - 1], z[i]], [x[i - 1], x[i]]) if i - 1 >= 0 and z[i] != z[i - 1] else x[i]
            break
    return xl, xr


def orilla_quiebre(z, x, i0, dx, h_min=0.3, pend_alta=0.20, pend_baja=0.10, win_m=1.0):
    win = int(round(win_m / dx))
    out = []
    for direccion in (-1, 1):
        res = None; subio = False; i = i0
        while 0 <= i + direccion * win < len(z):
            j = i + direccion * win
            pend = abs(z[j] - z[i]) / (win * dx)
            if pend >= pend_alta:
                subio = True
            if subio and (z[j] - z[i0]) >= h_min and pend < pend_baja:
                res = (x[j], z[j]); break
            if (z[j] - z[i0]) < -0.05 and abs(x[j] - x[i0]) > 3:
                break
            i += direccion
        out.append(res)
    return out


def q_stats(vals):
    v = np.array([x for x in vals if x is not None and np.isfinite(x)], float)
    if len(v) == 0:
        return {'n': 0}
    return {'n': int(len(v)), 'mediana_m': round(float(np.median(v)), 2), 'p90_m': round(float(np.percentile(v, 90)), 2),
            'max_m': round(float(v.max()), 2), 'min_m': round(float(v.min()), 2)}


def std_local(a, size):
    m1 = ndi.uniform_filter(a, size); m2 = ndi.uniform_filter(a * a, size)
    return np.sqrt(np.maximum(m2 - m1 * m1, 0))


def leer_ventana(src, bounds, bandas=None):
    """Lectura por ventana (bounds en 31982 == 32722) del raster original a resolucion nativa."""
    win = from_bounds(*bounds, transform=src.transform)
    win = Window(int(math.floor(win.col_off)), int(math.floor(win.row_off)), int(math.ceil(win.width)) + 1, int(math.ceil(win.height)) + 1)
    a = src.read(bandas, window=win, boundless=True, fill_value=(0 if src.nodata is None else src.nodata))
    return a, src.window_transform(win)


def rasterizar_en(geoms, shape_, tr):
    return _rasterize([(g, 1) for g in geoms if g is not None and not g.is_empty], out_shape=shape_, transform=tr, fill=0, dtype='uint8').astype(bool)


# =====================================================================================
# 3. M1 + M2 por arroio (barrido por bloques de 25 estaciones = 50 m de eje)
# =====================================================================================
MEDICIONES = []      # puntos (todas las mediciones de todos los metodos)
RESUMO = {'fecha_vuelo': FECHA_VUELO, 'parametros': {'paso_m': PASO_M, 'corredor_m': CORREDOR_M, 'M1': M1, 'M2': M2, 'M3_curvas': M3_CURVAS,
                                                       'M3_envolvente': M3_ENVOLVENTE, 'M3_no_aplicadas': M3_NO_APLICADAS},
          'verificacion_capas': VERIF, 'arroios': {}}
src_orto = rasterio.open(ORTHO_SRC)
src_dtm = rasterio.open(DTM_SRC)
src_dsm = rasterio.open(DSM_SRC)
VERIF['odm_orthophoto_5cm'] = {'res_m': [round(src_orto.res[0], 4), round(src_orto.res[1], 4)], 'bandas': src_orto.count, 'dtype': src_orto.dtypes[0], 'bounds': [round(v, 1) for v in src_orto.bounds]}
VERIF['dtm_5cm'] = {'res_m': round(src_dtm.res[0], 4), 'nodata': src_dtm.nodata, 'bounds': [round(v, 1) for v in src_dtm.bounds]}
_verif_tiles = {'L': [], 'ExG': [], 'BR': [], 'TEX': [], 'alpha_pct': []}
_verif_dtm = []

from skimage.measure import label as sk_label, regionprops
from skimage.morphology import skeletonize

for A in ARROIOS:
    nome, eje = A['nome'], A['eje']
    corr = CORREDOR_M[nome]
    key = nome
    log('\n--- %s (%s, %.0f m, corredor +-%.0f m) ---' % (nome, A['fuente_eje'], eje.length, corr))
    excl = REPRESA.buffer(10) if 'Arroio 3' in nome else RESERV_CAB.buffer(5)
    n_est = int(eje.length // PASO_M) + 1
    ss = np.arange(n_est) * PASO_M
    m1_comp = []          # componentes de agua aceptadas
    m2_secs = []          # secciones M2
    n_est_total = n_est; n_est_excl = 0; n_est_sin_orto = 0; n_est_cand_m2 = 0; n_est_m2_sin_canal = 0; n_est_m2_borda_huella = 0
    B_DTM = H_DTM.boundary; B_ORTO = H_ORTO.boundary
    tiles = [ss[i:i + 25] for i in range(0, n_est, 25)]
    for it, sblk in enumerate(tiles):
        pts = [eje.interpolate(s) for s in sblk]
        seg = LineString([(p.x, p.y) for p in pts]) if len(pts) > 1 else pts[0]
        bb = seg.buffer(corr + 4).bounds
        tile = box(*bb)
        if not tile.intersects(H_ORTO):
            n_est_sin_orto += len(sblk); continue
        rgba, trt = leer_ventana(src_orto, bb)
        alpha = rgba[3] > 0
        if alpha.mean() < 0.02:
            n_est_sin_orto += len(sblk); continue
        Rr, Gg, Bb = [rgba[i].astype('float32') for i in range(3)]
        L = 0.299 * Rr + 0.587 * Gg + 0.114 * Bb
        ExG = 2 * Gg - Rr - Bb
        mx = np.maximum(np.maximum(Rr, Gg), Bb); mn = np.minimum(np.minimum(Rr, Gg), Bb)
        S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).astype('float32')
        BR = ((Bb - Rr) / np.maximum(Bb + Rr, 1)).astype('float32')
        TEX = std_local(L, M1['TEX_win_px'])
        del Rr, Gg, Bb, mx, mn
        if it % 6 == 0:      # verificacion de rangos del tile (muestra)
            va = alpha
            _verif_tiles['L'].append((float(L[va].min()), float(L[va].max()), float(L[va].mean())))
            _verif_tiles['ExG'].append((float(ExG[va].min()), float(ExG[va].max()), float(ExG[va].mean())))
            _verif_tiles['BR'].append((float(BR[va].min()), float(BR[va].max()), float(BR[va].mean())))
            _verif_tiles['TEX'].append((float(TEX[va].min()), float(TEX[va].max()), float(TEX[va].mean())))
            _verif_tiles['alpha_pct'].append(float(100 * va.mean()))
        # --- M1: mascara de agua / leito humedo en el corredor ---
        m_corr = rasterizar_en([seg.buffer(corr)], L.shape, trt)
        m_excl = rasterizar_en([excl], L.shape, trt) if not excl.is_empty else np.zeros(L.shape, bool)
        aguam = alpha & m_corr & ~m_excl & (L < M1['L_max']) & (ExG < M1['ExG_max']) & (ExG > M1['ExG_min']) & (TEX < M1['TEX_max']) & (BR > M1['BR_min']) & (BR < M1['BR_max']) & (S < M1['S_max'])
        aguam = ndi.binary_opening(aguam, iterations=M1['abrir_it'])
        aguam = ndi.binary_closing(aguam, iterations=M1['cerrar_it'])
        lab = sk_label(aguam, connectivity=2)
        if lab.max() > 0:
            edt = ndi.distance_transform_edt(aguam)
            for rp in regionprops(lab):
                area_m2 = rp.area * RES_ORTO ** 2
                if area_m2 < M1['area_min_m2']:
                    continue
                comp_m = rp.major_axis_length * RES_ORTO
                if comp_m < M1['comprimento_min_m']:
                    continue
                sl = rp.slice
                sub = (lab[sl] == rp.label)
                skel = skeletonize(sub)
                if skel.sum() < 3:
                    continue
                e_sk = edt[sl][skel]
                w_med = 2 * float(np.median(e_sk)) * RES_ORTO; w_p90 = 2 * float(np.percentile(e_sk, 90)) * RES_ORTO; w_max = 2 * float(e_sk.max()) * RES_ORTO
                long_skel = float(skel.sum()) * RES_ORTO
                comp_m = max(comp_m, long_skel)
                # punto de medicion: pixel del esqueleto mas cercano al centroide
                rr, cc = np.where(skel)
                cy, cx = rp.centroid
                k = int(np.argmin((rr + sl[0].start - cy) ** 2 + (cc + sl[1].start - cx) ** 2))
                prow, pcol = rr[k] + sl[0].start, cc[k] + sl[1].start
                px, py = trt * (pcol + 0.5, prow + 0.5)
                pt = Point(px, py)
                d_eje = pt.distance(eje)
                if d_eje > corr:
                    continue
                # orientacion del componente vs tangente del eje
                th = rp.orientation
                vdx, vdy = math.sin(th), -math.cos(th)
                s_near = eje.project(pt)
                (nx, ny), (tx, ty) = perpendicular(eje, s_near)
                alin = abs(vdx * tx + vdy * ty)
                # DSM plano (0,25 m) sobre el componente
                cols_c, rows_c = ~tr25 * (px, py)
                r0, c0 = int(rows_c), int(cols_c)
                dsm_std = None; chm_med = None
                if 0 <= r0 < h25 and 0 <= c0 < w25:
                    win = dsm25[max(r0 - 4, 0):r0 + 5, max(c0 - 4, 0):c0 + 5]
                    if np.isfinite(win).sum() >= 10:
                        dsm_std = float(np.nanstd(win))
                    winc = chm25[max(r0 - 8, 0):r0 + 9, max(c0 - 8, 0):c0 + 9]
                    if np.isfinite(winc).any():
                        chm_med = float(np.nanmedian(winc))
                # calha por vegetacion: perfil perpendicular al componente, +-20 m, en el tile
                pnx, pny = -vdy, vdx
                xs_c = np.arange(-M1['calha_max_m'], M1['calha_max_m'] + 1e-6, RES_ORTO)
                Xc = px + xs_c * pnx; Yc = py + xs_c * pny
                exg_p = muestrear(ExG, trt, Xc, Yc); tex_p = muestrear(TEX, trt, Xc, Yc); ag_p = muestrear(aguam.astype('float32'), trt, Xc, Yc, order=0)
                al_p = muestrear(alpha.astype('float32'), trt, Xc, Yc, order=0)
                k_s = int(round(M1['calha_suav_m'] / RES_ORTO))
                exg_s = ndi.uniform_filter1d(np.where(np.isfinite(exg_p), exg_p, 0), k_s); tex_s = ndi.uniform_filter1d(np.where(np.isfinite(tex_p), tex_p, 0), k_s)
                i0 = len(xs_c) // 2
                calha = None; xl = xr = None
                bordes = []
                for direccion in (-1, 1):
                    i = i0; res = None
                    # salir del agua
                    while 0 <= i < len(xs_c) and ag_p[i] == 1:
                        i += direccion
                    while 0 <= i < len(xs_c):
                        if not np.isfinite(al_p[i]) or al_p[i] == 0:
                            break
                        if exg_s[i] > M1['calha_ExG_veg'] or tex_s[i] > M1['calha_TEX_veg']:
                            res = xs_c[i]; break
                        i += direccion
                    bordes.append(res)
                if bordes[0] is not None and bordes[1] is not None:
                    xl, xr = bordes; calha = float(xr - xl)
                # calidad
                plano = (dsm_std is not None and dsm_std < M1['dsm_std_plano_m'])
                if alin >= M1['alinhamento_min_cos'] and comp_m >= M1['comprimento_alta_m'] and (plano or dsm_std is None) and d_eje <= 25:
                    qual = 'alta'
                elif comp_m >= M1['comprimento_min_m']:
                    qual = 'media'
                else:
                    continue
                if dsm_std is not None and dsm_std >= 0.5:
                    qual = 'baixa'      # superficie rugosa: sombra/suelo, no lamina
                contexto = ''
                if not REPRESA.is_empty and pt.distance(REPRESA) < M1['dist_represa_vertedouro_m']:
                    contexto = 'vertedouro/saida da represa (poca artificial a jusante do dique): NAO e a calha natural'
                elif not RESERV_CAB.is_empty and pt.distance(RESERV_CAB) < 30:
                    contexto = 'reservatorio da cabeceira (artificial)'
                Lm = float(L[sl][sub].mean()); Em = float(ExG[sl][sub].mean()); Bm = float(BR[sl][sub].mean()); Tm = float(TEX[sl][sub].mean())
                m1_comp.append({'arroio': nome, 'metodo': 'M1_espelho', 'x': round(px, 2), 'y': round(py, 2), 's_m': round(float(s_near), 1),
                                'largura_m': round(w_med, 2), 'largura_p90_m': round(w_p90, 2), 'largura_max_m': round(w_max, 2), 'comprimento_m': round(comp_m, 1),
                                'area_m2': round(area_m2, 2), 'dist_eixo_m': round(d_eje, 1), 'alinhamento_cos': round(alin, 2), 'dsm_std_m': round(dsm_std, 3) if dsm_std is not None else None,
                                'chm_m': round(chm_med, 2) if chm_med is not None else None, 'L': round(Lm, 1), 'ExG': round(Em, 1), 'BR': round(Bm, 3), 'TEX': round(Tm, 2),
                                'calha_veg_m': round(calha, 2) if calha is not None else None, 'calha_xl': round(float(xl), 2) if xl is not None else None,
                                'calha_xr': round(float(xr), 2) if xr is not None else None, 'dir_perp': [round(pnx, 4), round(pny, 4)], 'qualidade': qual, 'contexto': contexto, 'tile': it})
        # --- M2: estaciones con suelo visible (solo donde hay DTM) ---
        if not tile.intersects(H_DTM):
            continue
        xs_p = np.arange(-M2['perfil_semi_m'], M2['perfil_semi_m'] + 1e-6, 0.25)
        for s in sblk:
            pc = eje.interpolate(s)
            if not H_DTM.contains(pc):
                continue
            if pc.distance(B_DTM) < M2['dist_borda_huella_min_m'] or pc.distance(B_ORTO) < M2['dist_borda_huella_min_m']:
                n_est_m2_borda_huella += 1; continue
            (nx, ny), (tx, ty) = perpendicular(eje, s)
            X = pc.x + xs_p * nx; Y = pc.y + xs_p * ny
            fo = muestrear(fonte25.astype('float32'), tr25, X, Y, order=0)
            ch = muestrear(chm25, tr25, X, Y)
            centro = np.abs(xs_p) <= M2['semi_centro_m']
            if not (np.all(fo[centro] == 1) and np.isfinite(ch[centro]).all() and np.nanmedian(ch[centro]) < M2['chm_max_m']):
                continue
            n_est_cand_m2 += 1
            # perfil DTM 5 cm (ventana del original)
            semi = M2['perfil_semi_m'] + 1
            z_win, trd = leer_ventana(src_dtm, (pc.x - semi, pc.y - semi, pc.x + semi, pc.y + semi), [1])
            z_win = np.where(z_win[0] == src_dtm.nodata, np.nan, z_win[0]).astype('float32')
            if np.isfinite(z_win).mean() < 0.5:
                continue
            if len(_verif_dtm) < 40:
                _verif_dtm.append((float(np.nanmin(z_win)), float(np.nanmax(z_win))))
            xs5 = np.arange(-M2['perfil_semi_m'], M2['perfil_semi_m'] + 1e-6, M2['dx'])
            z = muestrear(z_win, trd, pc.x + xs5 * nx, pc.y + xs5 * ny)
            ok = np.isfinite(z)
            if ok.mean() < 0.8 or not ok[np.abs(xs5) <= M2['semi_centro_m']].all():
                continue
            zz = ndi.median_filter(np.where(ok, z, np.nanmax(z)), 5)
            zc = np.where(np.abs(xs5) <= M2['fondo_semi_m'], zz, np.inf)
            i0 = int(np.argmin(zc)); z_f = float(zz[i0])
            izq = zz[(xs5 < xs5[i0]) & (xs5 >= xs5[i0] - 8)]; der = zz[(xs5 > xs5[i0]) & (xs5 <= xs5[i0] + 8)]
            canal = len(izq) > 0 and len(der) > 0 and (izq.max() - z_f) >= M2['canal_h_min_m'] and (der.max() - z_f) >= M2['canal_h_min_m']
            arbp = muestrear(arb50, tr50, X, Y, order=0)
            pct_arb = float(100 * np.nanmean(arbp)) if np.isfinite(arbp).any() else float('nan')
            rec = {'arroio': nome, 'metodo': 'M2_secao', 'x': round(pc.x, 2), 'y': round(pc.y, 2), 's_m': round(float(s), 1), 'x_fondo_m': round(float(xs5[i0]), 2), 'z_fondo_m': round(z_f, 2),
                   'chm_centro_m': round(float(np.nanmedian(ch[centro])), 2), 'pct_arboreo_perfil': round(pct_arb, 1) if np.isfinite(pct_arb) else None,
                   'minimo_local': bool(canal), 'nx': round(nx, 4), 'ny': round(ny, 4)}
            if not canal:
                n_est_m2_sin_canal += 1
                rec['valida'] = False; rec['motivo'] = 'sin minimo local transversal (no es canal: plano/ladera)'
                m2_secs.append(rec); continue
            for h in M2['h_bankfull']:
                xl, xr = orilla_h(zz, xs5, i0, h)
                rec['largura_h%s_m' % h] = round(float(xr - xl), 2) if (xl is not None and xr is not None) else None
                rec['xl_h%s' % h] = round(float(xl), 2) if xl is not None else None; rec['xr_h%s' % h] = round(float(xr), 2) if xr is not None else None
            qi, qd = orilla_quiebre(zz, xs5, i0, M2['dx'], **{k: v for k, v in M2['quiebre'].items() if k != 'win_m'}, win_m=M2['quiebre']['win_m'])
            if qi and qd:
                rec.update({'largura_quiebre_m': round(float(qd[0] - qi[0]), 2), 'incisao_m': round(float(min(qi[1], qd[1]) - z_f), 2)})
            else:
                rec.update({'largura_quiebre_m': None, 'incisao_m': None})
            rec['valida'] = rec.get('largura_h0.5_m') is not None
            rec['motivo'] = '' if rec['valida'] else 'orilla h=0,5 fuera del perfil +-15 m'
            pa = rec['pct_arboreo_perfil']
            if pa is None or pa >= M2['arboreo_bosque_pct']:
                rec['cobertura'] = 'bosque'
            elif pa >= M2['arboreo_min_pct']:
                rec['cobertura'] = 'borda'; rec['aviso'] = 'borda campo-floresta (%d %% arboreo): o talweg de ortho_03 sob dossel desvia-se para o campo; a secao mede o terraco/borda, NAO o arroio' % pa
            else:
                rec['cobertura'] = 'campo'; rec['aviso'] = 'campo aberto (< %d %% arboreo no perfil): dreno/terraco agricola, NAO o arroio' % M2['arboreo_min_pct']
            rec['perfil_z_1m'] = [round(float(v), 2) for v in zz[::20]]
            m2_secs.append(rec)
    # --- dedupe M1 (componentes cortadas por el solape de tiles) ---
    m1_comp.sort(key=lambda d: -d['comprimento_m'])
    keep = []
    for d in m1_comp:
        if all(np.hypot(d['x'] - k['x'], d['y'] - k['y']) > 3.0 for k in keep):
            keep.append(d)
    m1_comp = sorted(keep, key=lambda d: d['s_m'])
    m1_ok = [d for d in m1_comp if d['qualidade'] in ('alta', 'media') and not d['contexto']]
    m1_art = [d for d in m1_comp if d['qualidade'] in ('alta', 'media') and d['contexto']]
    m2_val = [d for d in m2_secs if d['valida']]
    m2_val_bosque = [d for d in m2_val if d.get('aviso') is None]
    log('  M1: %d componentes agua/leito (alta %d, media %d, baixa %d); estaciones %d (sin ortofoto %d)' % (
        len(m1_comp), sum(d['qualidade'] == 'alta' for d in m1_comp), sum(d['qualidade'] == 'media' for d in m1_comp), sum(d['qualidade'] == 'baixa' for d in m1_comp), n_est_total, n_est_sin_orto))
    for d in (m1_ok + m1_art)[:14]:
        log('     s=%5.0f m  x=%.1f y=%.1f  espelho %.2f m (max %.2f) comp %.1f m  calha_veg %s  q=%s  dsm_std %s  L %.0f ExG %.0f BR %.2f %s' % (
            d['s_m'], d['x'], d['y'], d['largura_m'], d['largura_max_m'], d['comprimento_m'], d['calha_veg_m'], d['qualidade'], d['dsm_std_m'], d['L'], d['ExG'], d['BR'], ('[' + d['contexto'][:30] + ']') if d['contexto'] else ''))
    log('  M2: estaciones candidatas (suelo+CHM<0,5) %d, validas %d (bosque %d, borda/campo %d), sin minimo local %d, descartadas por borde de huella %d' % (
        n_est_cand_m2, len(m2_val), len(m2_val_bosque), len(m2_val) - len(m2_val_bosque), n_est_m2_sin_canal, n_est_m2_borda_huella))
    for d in m2_val:
        log('     s=%5.0f m  x=%.1f y=%.1f  h0,5 %s  h1,0 %s  quiebre %s  arboreo %s%%  %s' % (d['s_m'], d['x'], d['y'], d.get('largura_h0.5_m'), d.get('largura_h1.0_m'), d.get('largura_quiebre_m'), d['pct_arboreo_perfil'], d['cobertura']))
    est = {'eixo': A['fuente_eje'], 'eixo_m': round(eje.length, 1), 'estacoes': n_est_total, 'estacoes_sem_ortofoto': n_est_sin_orto,
           'M1': {'n_componentes': len(m1_comp), 'n_alta': sum(d['qualidade'] == 'alta' for d in m1_comp), 'n_media': sum(d['qualidade'] == 'media' for d in m1_comp),
                  'n_baixa_descartadas': sum(d['qualidade'] == 'baixa' for d in m1_comp), 'n_artificiais_excluidas': len(m1_art),
                  'artificiais': [{'x': d['x'], 'y': d['y'], 'espelho_m': d['largura_m'], 'espelho_max_m': d['largura_max_m'], 'calha_veg_m': d['calha_veg_m'], 'contexto': d['contexto']} for d in m1_art],
                  'espelho_alta_media': q_stats([d['largura_m'] for d in m1_ok]), 'espelho_alta': q_stats([d['largura_m'] for d in m1_ok if d['qualidade'] == 'alta']),
                  'espelho_max_por_componente': q_stats([d['largura_max_m'] for d in m1_ok]),
                  'calha_veg': q_stats([d['calha_veg_m'] for d in m1_ok]), 'comprimento_visivel_total_m': round(sum(d['comprimento_m'] for d in m1_ok), 1),
                  'n_ge_10m_espelho': int(sum(1 for d in m1_ok if d['largura_m'] >= 10)), 'n_ge_10m_calha_veg': int(sum(1 for d in m1_ok if d['calha_veg_m'] is not None and d['calha_veg_m'] >= 10))},
           'M2': {'n_candidatas': n_est_cand_m2, 'n_validas': len(m2_val), 'n_validas_bosque': len(m2_val_bosque), 'n_sem_minimo_local': n_est_m2_sin_canal, 'n_descartadas_borda_huella': n_est_m2_borda_huella,
                  'largura_h0.5': q_stats([d.get('largura_h0.5_m') for d in m2_val]), 'largura_h1.0': q_stats([d.get('largura_h1.0_m') for d in m2_val]),
                  'largura_quiebre': q_stats([d.get('largura_quiebre_m') for d in m2_val]), 'incisao': q_stats([d.get('incisao_m') for d in m2_val]),
                  'largura_h0.5_bosque': q_stats([d.get('largura_h0.5_m') for d in m2_val_bosque]), 'largura_h1.0_bosque': q_stats([d.get('largura_h1.0_m') for d in m2_val_bosque]),
                  'n_ge_10m_h0.5': int(sum(1 for d in m2_val if d.get('largura_h0.5_m') is not None and d['largura_h0.5_m'] >= 10)),
                  'n_ge_10m_h1.0': int(sum(1 for d in m2_val if d.get('largura_h1.0_m') is not None and d['largura_h1.0_m'] >= 10)),
                  'nota': 'sem DTM' if not H_DTM.intersects(eje) else ''}}
    RESUMO['arroios'][key] = est
    MEDICIONES.extend(m1_comp); MEDICIONES.extend(m2_secs)

RESUMO['verificacion_capas']['ortofoto_tiles_5cm'] = {k: ([round(float(np.min([t[0] for t in v])), 2), round(float(np.max([t[1] for t in v])), 2), round(float(np.mean([t[2] for t in v])), 2)] if (v and k != 'alpha_pct') else (round(float(np.mean(v)), 1) if v else None)) for k, v in _verif_tiles.items()}
RESUMO['verificacion_capas']['dtm_5cm_ventanas'] = {'n_ventanas': len(_verif_dtm), 'z_min': round(min(v[0] for v in _verif_dtm), 2) if _verif_dtm else None, 'z_max': round(max(v[1] for v in _verif_dtm), 2) if _verif_dtm else None,
                                                     'nota': 'dtm.tif ORIGINAL de ODM (sin la correccion vertical polinomica de ortho_01 hacia FABDEM: ~ +20-25 m): las larguras son RELATIVAS al fondo y no dependen del datum'}
log('\n  verificacion tiles 5 cm [min, max, media]: %s' % RESUMO['verificacion_capas']['ortofoto_tiles_5cm'])
log('  verificacion DTM 5 cm: %s' % RESUMO['verificacion_capas']['dtm_5cm_ventanas'])

# =====================================================================================
# 4. M3 geometria hidraulica regional
# =====================================================================================
with Cronometro('M3 geometria hidraulica'):
    D_EXT = os.path.join(CODIGO, 'datos_externos')
    otto = gpd.read_file(os.path.join(D_EXT, 'IAT_otto_trecho_drenagem_2020.geojson')).to_crs(CRS_METRICO)
    ana5 = gpd.read_file(os.path.join(D_EXT, 'ANA_BHO2017_5k_trecho_drenagem.geojson')).to_crs(CRS_METRICO)
    with rasterio.open(PREV['acum_30m']) as sa:
        acc = sa.read(1).astype('float64'); acc[acc == sa.nodata] = np.nan; tra = sa.transform
        RESUMO['verificacion_capas']['acumulacion_30m'] = verificar_arr(acc, 'ACUMULACION_ha_30m', unidades='ha')
        RESUMO['verificacion_capas']['acumulacion_30m']['nota'] = 'ensamble 5 DEM, AOI = propiedad + 3000 m: cuencas mayores a ese radio quedan TRUNCADAS (comparar con otto/ANA)'

    def acc_km2(pt, radio=45.0):
        c, r = ~tra * (pt.x, pt.y); r, c = int(r), int(c)
        k = int(math.ceil(radio / 30))
        win = acc[max(r - k, 0):r + k + 1, max(c - k, 0):c + k + 1]
        return float(np.nanmax(win)) / 100.0 if np.isfinite(win).any() else None

    def trecho_mas_solapado(gdf, eje, campo_area, campo_id, buf=60):
        b = eje.buffer(buf)
        best, bl = None, 0.0
        for _, r in gdf.iterrows():
            l = r.geometry.intersection(b).length
            if l > bl:
                bl, best = l, r
        if best is None or bl < 30:
            return None
        fin = Point(best.geometry.coords[-1]) if best.geometry.geom_type == 'LineString' else Point(list(best.geometry.geoms)[-1].coords[-1])
        return {campo_id: str(best[campo_id]), 'nuareamont_km2': round(float(best[campo_area]), 3), 'solape_m': round(bl, 1),
                'dist_fim_trecho_m': round(fin.distance(Point(eje.coords[-1])), 1), 'fim_trecho_xy': [round(fin.x, 1), round(fin.y, 1)]}

    M3 = {}
    for A in ARROIOS:
        nome, eje = A['nome'], A['eje']
        eje_in = eje.intersection(IMOVEL.buffer(1))
        if eje_in.geom_type != 'LineString':
            eje_in = max(eje_in.geoms, key=lambda g: g.length) if hasattr(eje_in, 'geoms') else eje
        # sentido aguas abajo: extremo de mayor acumulacion
        a0, a1 = acc_km2(Point(eje_in.coords[0])), acc_km2(Point(eje_in.coords[-1]))
        if (a0 or 0) > (a1 or 0):
            eje_in = LineString(list(eje_in.coords)[::-1])
        ot = trecho_mas_solapado(otto, eje_in, 'nuareamont', 'cotrecho')
        an = trecho_mas_solapado(ana5, eje_in, 'NUAREAMONT', 'COTRECHO')
        ot_cont = None
        if ot:
            rr_ = otto[otto.cotrecho.astype(str) == ot['cotrecho']].iloc[0]
            ot.update({'nuareacont_km2': round(float(rr_['nuareacont']), 3), 'nustrahler': int(rr_['nustrahler']), 'nucomptrec_km': round(float(rr_['nucomptrec']), 3), 'noriocomp': str(rr_.get('noriocomp') or '')})
        pontos = []
        for f, rot in ((0.0, 'cabeceira/entrada'), (0.25, '1/4'), (0.5, '1/2'), (0.75, '3/4'), (1.0, 'saida do imovel')):
            p = eje_in.interpolate(f, normalized=True)
            a_loc = acc_km2(p)
            rec = {'posicao': rot, 'frac': f, 'x': round(p.x, 1), 'y': round(p.y, 1), 'A_local_km2': round(a_loc, 3) if a_loc is not None else None}
            # A oficial: en la salida se usa nuareamont del trecho (si el trecho termina cerca); en puntos interiores solo la local
            A_use = a_loc
            if f == 1.0 and ot:
                rec['A_otto_nuareamont_km2'] = ot['nuareamont_km2']; rec['dist_fim_trecho_otto_m'] = ot['dist_fim_trecho_m']
                # nuareamont vale en el FIN del trecho; se descuenta pro-rata la contribucion propia del trecho (nuareacont) aguas abajo de la salida
                frac = min(1.0, ot['dist_fim_trecho_m'] / max(ot['nucomptrec_km'] * 1000.0, 1.0))
                A_adj = ot['nuareamont_km2'] - ot['nuareacont_km2'] * frac
                rec['A_otto_ajustada_saida_km2'] = round(A_adj, 3)
                if a_loc is not None and a_loc > 1.5 * A_adj:
                    # la ventana de 45 m de la acumulacion 30 m tomo un curso VECINO mayor (medido: Arroio 2 en la confluencia con el Arroio 1: 5,7 vs 0,87 km2)
                    A_use = A_adj; rec['A_min_km2'] = round(A_adj, 3)
                    rec['A_fonte'] = 'otto nuareamont ajustada = %.2f (acumulacao local %.2f DESCARTADA: > 1,5x, contaminada por curso vizinho na confluencia)' % (A_adj, a_loc)
                else:
                    rec['A_min_km2'] = round(min(a_loc, A_adj), 3) if a_loc is not None else round(A_adj, 3)
                    A_use = max(a_loc or 0, A_adj)
                    rec['A_fonte'] = 'CONSERVADOR: max(acumulacao local 30 m = %.2f [AOI +3 km, pode estar truncada], otto nuareamont ajustada = %.2f)' % (a_loc or 0, A_adj)
            else:
                rec['A_min_km2'] = round(a_loc, 3) if a_loc is not None else None
                rec['A_fonte'] = 'acumulacao local 30 m (ensamble 5 DEM)'
            rec['A_usada_km2'] = round(A_use, 3) if A_use else None
            if A_use:
                A_lo = rec['A_min_km2'] or A_use
                for ck, cv in M3_CURVAS.items():
                    W = cv['a'] * A_use ** cv['b']; W_lo = cv['a'] * A_lo ** cv['b']; fct = 10 ** cv['see_log10']
                    rec['W_%s_m' % ck] = round(W, 2); rec['W_%s_int_m' % ck] = [round(W_lo / fct, 2), round(W * fct, 2)]
                rec['extrapolacao'] = A_use < 0.5
            pontos.append(rec)
            MEDICIONES.append({'arroio': nome, 'metodo': 'M3_estimativa', 'x': rec['x'], 'y': rec['y'], 's_m': round(eje.project(p), 1), 'posicao': rot,
                               'A_km2': rec['A_usada_km2'], 'largura_m': rec.get('W_bieger2015_usa_m'), 'largura_int_m': rec.get('W_bieger2015_usa_int_m'),
                               'largura_ahi_m': rec.get('W_bieger2015_ahi_m'), 'qualidade': 'estimativa', 'extrapolacao': rec.get('extrapolacao')})
        Wsal = pontos[-1].get('W_bieger2015_usa_m'); Wint = pontos[-1].get('W_bieger2015_usa_int_m')
        env = M3_ENVOLVENTE['fernandez2004_oeste_pr']
        A_sal = pontos[-1]['A_usada_km2']
        M3[nome] = {'pontos': pontos, 'otto_iat_2020': ot, 'ana_bho_5k': an,
                    'W_saida_bieger_usa_m': Wsal, 'W_saida_intervalo_m': Wint, 'W_saida_bieger_ahi_m': pontos[-1].get('W_bieger2015_ahi_m'),
                    'fernandez2004_comparavel': (A_sal is not None and env['A_km2'][0] <= A_sal <= env['A_km2'][1] * 1.4),
                    'categoria': ('suporta_le_10m' if (Wint and Wint[1] < 10) else ('compativel_le_10m' if (Wsal and Wsal < 10) else 'alerta_ge_10m')) if Wsal else 'sem_dados',
                    'leitura': ('ESTIMATIVA (nao medicao): W central %.1f m, intervalo %.1f-%.1f m (SEE 0,24 log10 = fator 1,74, A entre local e otto ajustada); ' % (Wsal, Wint[0], Wint[1]) if Wsal else 'sem area de aporte: nao estimavel; ') +
                               ('limite superior do intervalo %s 10 m' % ('<' if (Wint and Wint[1] < 10) else '>=') if Wint else '')}
        log('  M3 %s: A saida %s km2 (otto %s, ANA %s) -> W %s m [%s]  | AHI %s m' % (nome, A_sal, ot and ot['nuareamont_km2'], an and an['nuareamont_km2'], Wsal, Wint, pontos[-1].get('W_bieger2015_ahi_m')))
        for p_ in pontos:
            log('     %-18s A_local %s km2  A_usada %s  W_usa %s [%s]' % (p_['posicao'], p_['A_local_km2'], p_['A_usada_km2'], p_.get('W_bieger2015_usa_m'), p_.get('W_bieger2015_usa_int_m')))
    RESUMO['M3'] = M3

# =====================================================================================
# 5. M4 atributos oficiales
# =====================================================================================
with Cronometro('M4 atributos oficiais'):
    ibge = gpd.read_file(os.path.join(D_EXT, 'IBGE_BC250_trecho_drenagem.geojson')).to_crs(CRS_METRICO)
    fbds = gpd.read_file(os.path.join(D_EXT, 'IAT_FBDS_rios_ate10m.geojson')).to_crs(CRS_METRICO)
    res_hp = leer_json(PREV['resultados_hidro'])
    car_decl = res_hp.get('car', {}).get('declarado_por_tema', {})
    M4 = {'ana_bho_5k_atributos': [c for c in ana5.columns if c != 'geometry'],
          'ana_bho_5k_tem_largura': any('LARG' in c.upper() for c in ana5.columns),
          'otto_iat_2020_tem_largura': any('larg' in c.lower() for c in otto.columns),
          'car_hidro_declarada': {k: v.get('hidro_RIO_ATE_10') for k, v in car_decl.items()}}
    for A in ARROIOS:
        nome, eje = A['nome'], A['eje']
        b = eje.buffer(120)
        ib = []
        for _, r in ibge.iterrows():
            l = r.geometry.intersection(b).length
            if l >= 50:
                ib.append({'id': str(r['id']), 'nome': r.get('nome'), 'larguramedia': r.get('larguramedia'), 'regime': r.get('regime'), 'tipotrechodrenagem': r.get('tipotrechodrenagem'),
                           'encoberto': r.get('encoberto'), 'solape_m': round(l, 1)})
        ib.sort(key=lambda d: -d['solape_m'])
        ids = [s.strip() for s in str(A['fbds_ids']).split(',')]
        fb = fbds[fbds.objectid.astype(str).isin(ids)]
        M4[nome] = {'ibge_bc250': ib[:2], 'ibge_larguramedia': (ib[0]['larguramedia'] if ib else None) or 'nao informado (None)',
                    'fbds_iat': [{'objectid': str(r.objectid), 'classe': r.hidrografia, 'comprimento_km': float(r.comprimento_km), 'municipio': r.municipio} for _, r in fb.iterrows()],
                    'fbds_classe': 'curso d agua (0 - 10 m), mapeado 1:25.000 sobre RapidEye 5 m (2013)' if len(fb) else 'sem correspondencia',
                    'otto_ana': {'otto': M3[nome]['otto_iat_2020'], 'ana5k': M3[nome]['ana_bho_5k'], 'largura': 'nenhuma das duas bases traz atributo de largura'}}
        log('  M4 %s: BC250 %s | FBDS %s' % (nome, [(d['nome'], d['larguramedia'], d['regime']) for d in ib[:2]], [d['classe'] for d in M4[nome]['fbds_iat']]))
    RESUMO['M4'] = M4

# =====================================================================================
# 6. M5 protocolo de campo
# =====================================================================================
RESUMO['M5'] = {
    'objetivo': 'fechar a largura da calha do leito regular (art. 4o I, Lei 12.651/2012; leito regular = art. 3o XIX: calha por onde correm regularmente as aguas do curso durante o ano) com validade administrativa',
    'equipamento': ['trena de 30 m ou distanciometro laser', 'GNSS RTK/PPK (SIRGAS 2000, UTM 22S) ou GNSS L1/L5 com pos-processamento; erro <= 0,5 m', 'nivel de mangueira ou clinometro para o desnivel margem-fundo', 'estaca/vara graduada; camera com data'],
    'n_secoes': {'Arroio 1 (norte)': 8, 'Arroio 2 (central)': 10, 'Arroio 3 (sul)': 8},
    'onde': 'a cada ~60-100 m do eixo dentro do imovel, incluindo obrigatoriamente: entrada e saida do imovel, o trecho de maior largura sugerido por M1/M2 (pontos >= 8 m), 1 secao a 30-50 m a jusante da nascente (Arroio 2) e, no Arroio 3, 2 secoes a montante e 2 a jusante da represa (nunca dentro do vaso).',
    'o_que_medir_por_secao': ['largura da calha do leito regular (borda a borda do barranco/ruptura de declive que contem o escoamento regular, NAO a lamina do dia)',
                              'largura da lamina de agua no dia e profundidade maxima no dia', 'altura do barranco (fundo -> ruptura de declive) em cada margem',
                              'coordenadas GNSS das duas bordas (nao so do centro)', 'presenca/ausencia de agua corrente; marcas de cheia (detritos, linha de lama)', 'foto a montante e a jusante com escala'],
    'regra_decisao': 'largura legal por curso = MAIOR largura de calha do leito regular medida em secao valida dentro do imovel (a APP e por curso, art. 4o I). Se alguma secao >= 10 m: repetir a secao com 2 medicoes independentes e estender a APP para 50 m NAQUELE curso. Secoes em vaso de represa, terraco agricola ou dreno nao contam.',
    'epoca': 'periodo de aguas medias (nao apos chuva > 30 mm/48 h, nao em estiagem severa); registrar a data e a chuva dos 3 dias anteriores',
    'entregavel': 'planilha (id, x, y, largura_calha, largura_lamina, prof, alt_barranco_E/D, agua, obs, foto) + shapefile das secoes; anexar ao laudo tecnico com ART/TRT.'
}

# =====================================================================================
# 7. CONSOLIDACION y conclusion legal
# =====================================================================================
CONS = {}
for A in ARROIOS:
    nome = A['nome']; e = RESUMO['arroios'][nome]; m3 = M3[nome]; m4 = M4[nome]
    m1 = e['M1']; m2 = e['M2']
    metodos_con_datos = []; suportam = []; alertas = []
    # M1: usa calha_veg si n >= 3 (contiene el espejo), si no espejo como COTA INFERIOR
    if m1['calha_veg'].get('n', 0) >= 3:
        metodos_con_datos.append('M1'); (suportam if m1['calha_veg']['p90_m'] < 10 else alertas).append('M1 calha_veg p90 %.1f m' % m1['calha_veg']['p90_m'])
    elif m1['espelho_alta_media'].get('n', 0) >= 3:
        metodos_con_datos.append('M1 (so espelho: cota inferior)'); (suportam if m1['espelho_alta_media']['p90_m'] < 10 else alertas).append('M1 espelho p90 %.1f m (cota inferior da calha)' % m1['espelho_alta_media']['p90_m'])
    excluidos = []
    if m2['largura_h0.5_bosque'].get('n', 0) >= 5:
        metodos_con_datos.append('M2'); (suportam if m2['largura_h0.5_bosque']['p90_m'] < 10 else alertas).append('M2 h=0,5 (bosque) p90 %.1f m' % m2['largura_h0.5_bosque']['p90_m'])
    elif m2['largura_h0.5'].get('n', 0) > 0:
        excluidos.append('M2: %d secoes validas mas TODAS em borda campo-floresta/campo (h=0,5 mediana %.1f m): medem o terraco/borda, nao o arroio -> NAO contam' % (m2['largura_h0.5']['n'], m2['largura_h0.5']['mediana_m']))
    if m1['n_artificiais_excluidas']:
        excluidos.append('M1: %d componentes de agua so no vertedouro/saida da represa (artificial) -> NAO contam' % m1['n_artificiais_excluidas'])
    compat = []
    if m3['W_saida_intervalo_m']:
        metodos_con_datos.append('M3 (estimativa)')
        txt = 'M3 W %.1f m [%.1f-%.1f] na saida (estimativa)' % (m3['W_saida_bieger_usa_m'], *m3['W_saida_intervalo_m'])
        {'suporta_le_10m': suportam, 'compativel_le_10m': compat, 'alerta_ge_10m': alertas}[m3['categoria']].append(txt)
    metodos_con_datos.append('M4 (oficial)'); suportam.append('M4 FBDS classe 0-10 m (1:25.000); BC250 larguramedia %s' % m4['ibge_larguramedia'])
    pts_ge10 = [d for d in MEDICIONES if d['arroio'] == nome and d['metodo'] in ('M1_espelho', 'M2_secao') and d.get('qualidade', 'x') != 'baixa' and not d.get('contexto') and not d.get('aviso')
                and ((d.get('largura_m') or 0) >= 10 or (d.get('largura_h0.5_m') or 0) >= 10 or (d.get('calha_veg_m') or 0) >= 10)]
    pts_ge10_excl = [{'metodo': d['metodo'], 'x': float(d['x']), 'y': float(d['y']), 'largura_m': d.get('largura_m') or d.get('largura_h0.5_m'), 'calha_veg_m': d.get('calha_veg_m'), 'motivo_exclusao': d.get('contexto') or d.get('aviso')}
                     for d in MEDICIONES if d['arroio'] == nome and d['metodo'] in ('M1_espelho', 'M2_secao') and (d.get('contexto') or d.get('aviso'))
                     and ((d.get('largura_m') or 0) >= 10 or (d.get('largura_h0.5_m') or 0) >= 10 or (d.get('calha_veg_m') or 0) >= 10)]
    pts_ge10 = [{'metodo': d['metodo'], 'x': float(d['x']), 'y': float(d['y']), 'largura_m': d.get('largura_m') or d.get('largura_h0.5_m'), 'calha_veg_m': d.get('calha_veg_m'),
                 'aviso': d.get('aviso') or ('' if d['metodo'] == 'M2_secao' else 'espelho/leito %.1f m' % (d.get('largura_m') or 0))} for d in pts_ge10 if d.get('valida', True)]
    # rango consolidado: min = menor mediana medida; max = mayor entre p90 medidos y techo M3
    medidos = [m1['calha_veg'].get('mediana_m'), m1['espelho_alta_media'].get('mediana_m'), m2['largura_h0.5_bosque'].get('mediana_m')]
    medidos = [v for v in medidos if v is not None]
    p90s = [m1['calha_veg'].get('p90_m'), m2['largura_h0.5_bosque'].get('p90_m')]
    p90s = [v for v in p90s if v is not None]
    techo = max(p90s + ([m3['W_saida_intervalo_m'][1]] if m3['W_saida_intervalo_m'] else []))
    piso = min(medidos + ([m3['W_saida_intervalo_m'][0]] if m3['W_saida_intervalo_m'] else []))
    diretos = [m for m in metodos_con_datos if m in ('M1', 'M2')]     # medicao direta valida (nao cota inferior, nao campo aberto)
    if alertas:
        concl = 'NAO CONCLUSIVO: %s -> exige M5 (campo)' % '; '.join(alertas)
    elif diretos and len(suportam) >= 2:
        concl = '<= 10 m CONFIRMADO por %d metodos independentes (%s), com medicao direta (%s)' % (len(suportam), ', '.join(m.split(' ')[0] for m in metodos_con_datos), ', '.join(diretos))
    else:
        concl = '<= 10 m PROVAVEL mas NAO CONFIRMADO por medicao: apoiado por M4 (oficial) e %s; sem medicao direta valida na ortofoto/DTM -> exige M5 (campo)' % (
            ('M3 compativel [%s]' % compat[0]) if compat else ('M3 suporta' if any(s.startswith('M3') for s in suportam) else 'sem M3'))
    CONS[nome] = {'M1': {'n': m1['espelho_alta_media'].get('n', 0), 'espelho_mediana_m': m1['espelho_alta_media'].get('mediana_m'), 'espelho_p90_m': m1['espelho_alta_media'].get('p90_m'),
                         'espelho_max_m': m1['espelho_alta_media'].get('max_m'), 'calha_veg_n': m1['calha_veg'].get('n', 0), 'calha_veg_mediana_m': m1['calha_veg'].get('mediana_m'), 'calha_veg_p90_m': m1['calha_veg'].get('p90_m'),
                         'comprimento_visivel_m': m1['comprimento_visivel_total_m']},
                  'M2': {'n_bosque': m2['largura_h0.5_bosque'].get('n', 0), 'h0.5_mediana_m': m2['largura_h0.5_bosque'].get('mediana_m'), 'h0.5_p90_m': m2['largura_h0.5_bosque'].get('p90_m'),
                         'h1.0_mediana_m': m2['largura_h1.0_bosque'].get('mediana_m'), 'h1.0_p90_m': m2['largura_h1.0_bosque'].get('p90_m'),
                         'n_excluidas_borda_campo': m2['largura_h0.5'].get('n', 0) - m2['largura_h0.5_bosque'].get('n', 0), 'h0.5_mediana_excluidas_m': m2['largura_h0.5'].get('mediana_m') if m2['largura_h0.5'].get('n', 0) > m2['largura_h0.5_bosque'].get('n', 0) else None,
                         'n_descartadas_borda_huella': m2['n_descartadas_borda_huella']},
                  'M3': {'W_m': m3['W_saida_bieger_usa_m'], 'intervalo_m': m3['W_saida_intervalo_m'], 'A_saida_km2': m3['pontos'][-1]['A_usada_km2']},
                  'M4': {'fbds': '0-10 m', 'bc250_larguramedia': m4['ibge_larguramedia'], 'bc250_regime': (m4['ibge_bc250'][0]['regime'] if m4['ibge_bc250'] else None)},
                  'rango_consolidado_m': [round(piso, 1), round(techo, 1)], 'metodos_com_dados': metodos_con_datos, 'suportam_le_10m': suportam, 'compativeis': compat, 'alertas_ge_10m': alertas, 'excluidos': excluidos,
                  'pontos_ge_10m': pts_ge10, 'pontos_ge_10m_excluidos': pts_ge10_excl, 'conclusao_legal': concl}
    log('\n  CONSOLIDADO %s: rango %s m | %s' % (nome, CONS[nome]['rango_consolidado_m'], concl))
    for p_ in pts_ge10:
        log('     >= 10 m: %s' % p_)
RESUMO['consolidado'] = CONS

# =====================================================================================
# 8. SALIDAS: geojson, json, recortes PNG, figura de control
# =====================================================================================
gdf = gpd.GeoDataFrame([{k: v for k, v in d.items() if k != 'geometry'} for d in MEDICIONES], geometry=[Point(d['x'], d['y']) for d in MEDICIONES], crs=CRS_METRICO)
guardar_gdf(gdf, os.path.join(CAUCE, 'cauce_medicoes.geojson'))
guardar_json(os.path.join(CAUCE, 'cauce_resumo.json'), RESUMO)

with Cronometro('recortes PNG 20x20 m a 5 cm'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    RESUMO['recortes'] = []
    for A in ARROIOS:
        nome = A['nome']
        cand = [d for d in MEDICIONES if d['arroio'] == nome and d['metodo'] == 'M1_espelho' and d['qualidade'] in ('alta', 'media')]
        cand.sort(key=lambda d: (bool(d['contexto']), d['qualidade'] != 'alta', -d['comprimento_m']))
        sel = []
        for d in cand:
            if all(abs(d['s_m'] - s_['s_m']) > 20 for s_ in sel):
                sel.append(d)
            if len(sel) >= 6:
                break
        if len(sel) < 3:      # completar con secciones M2 validas o, si no hay nada, con estaciones del eje bajo dosel (para mostrar el problema)
            m2c = [d for d in MEDICIONES if d['arroio'] == nome and d['metodo'] == 'M2_secao' and d.get('valida')]
            m2c.sort(key=lambda d: d.get('aviso') is not None)
            for d in m2c:
                if len(sel) >= 4:
                    break
                if all(np.hypot(d['x'] - s_['x'], d['y'] - s_['y']) > 20 for s_ in sel):
                    sel.append(d)
        if len(sel) < 3 or not any(d['metodo'] == 'M1_espelho' and not d.get('contexto') for d in sel):
            n_eixo = 0
            for f in (0.3, 0.6, 0.15, 0.45, 0.75, 0.9):        # fuera de la represa / reservatorio (el eje FBDS del Arroio 3 cruza el espejo)
                p = A['eje'].interpolate(f, normalized=True)
                if p.distance(REPRESA) < 25 or p.distance(RESERV_CAB) < 25:
                    continue
                sel.append({'arroio': nome, 'metodo': 'eixo_sob_dossel', 'x': p.x, 'y': p.y, 's_m': round(f * A['eje'].length, 1), 'largura_m': None, 'qualidade': 'n/a'})
                n_eixo += 1
                if n_eixo >= 2:
                    break
        for k, d in enumerate(sel):
            bb = (d['x'] - 10, d['y'] - 10, d['x'] + 10, d['y'] + 10)
            rgba, trt = leer_ventana(src_orto, bb)
            img = np.moveaxis(rgba[:3], 0, -1)
            ext = [trt.c, trt.c + trt.a * rgba.shape[2], trt.f + trt.e * rgba.shape[1], trt.f]
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.imshow(img, extent=ext)
            ex, ey = A['eje'].xy; ax.plot(ex, ey, 'c-', lw=1, alpha=0.8, label='eixo (%s)' % ('talweg DTM' if 'talweg' in A['fuente_eje'] else 'FBDS'))
            tit = '%s  s=%.0f m  (%.1f, %.1f)' % (nome, d['s_m'], d['x'], d['y'])
            if d['metodo'] == 'M1_espelho':
                pnx, pny = d['dir_perp']; w = d['largura_m'] / 2
                ax.plot([d['x'] - w * pnx, d['x'] + w * pnx], [d['y'] - w * pny, d['y'] + w * pny], 'y-', lw=3, label='espelho/leito %.2f m' % d['largura_m'])
                if d['calha_veg_m'] is not None:
                    ax.plot([d['x'] + d['calha_xl'] * pnx, d['x'] + d['calha_xr'] * pnx], [d['y'] + d['calha_xl'] * pny, d['y'] + d['calha_xr'] * pny], 'r--', lw=1.5, label='calha (veg) %.1f m' % d['calha_veg_m'])
                tit += '\nM1 %s | comp. visivel %.1f m | dsm_std %s%s' % (d['qualidade'], d['comprimento_m'], d['dsm_std_m'], ('\n' + d['contexto'][:60]) if d['contexto'] else '')
            elif d['metodo'] == 'M2_secao':
                nx, ny = d['nx'], d['ny']; xl, xr = d['xl_h0.5'], d['xr_h0.5']
                ax.plot([d['x'] + xl * nx, d['x'] + xr * nx], [d['y'] + xl * ny, d['y'] + xr * ny], 'y-', lw=3, label='M2 h=0,5: %.1f m' % d['largura_h0.5_m'])
                if d.get('largura_h1.0_m'):
                    ax.plot([d['x'] + d['xl_h1.0'] * nx, d['x'] + d['xr_h1.0'] * nx], [d['y'] + d['xl_h1.0'] * ny, d['y'] + d['xr_h1.0'] * ny], 'r--', lw=1.5, label='h=1,0: %.1f m' % d['largura_h1.0_m'])
                tit += '\nM2 secao DTM 5 cm (%s)%s' % (d['cobertura'], ('\n' + d['aviso'][:70]) if d.get('aviso') else '')
            else:
                tit += '\nEIXO SOB DOSSEL FECHADO: cauce invisivel na ortofoto (nada a medir)'
            ax.set_xlim(bb[0], bb[2]); ax.set_ylim(bb[1], bb[3]); ax.set_title(tit, fontsize=8); ax.legend(fontsize=7, loc='lower left')
            ax.set_xlabel('E (m) SIRGAS 2000 UTM 22S'); ax.set_ylabel('N (m)'); ax.tick_params(labelsize=6)
            fn = os.path.join(RECORTES, 'arroio%d_%02d_%s.png' % (A['n'], k + 1, d['metodo']))
            plt.tight_layout(); plt.savefig(fn, dpi=100); plt.close()
            RESUMO['recortes'].append({'arroio': nome, 'png': os.path.basename(fn), 'metodo': d['metodo'], 'x': round(d['x'], 1), 'y': round(d['y'], 1), 'largura_m': d.get('largura_m') or d.get('largura_h0.5_m')})
        log('  %s: %d recortes' % (nome, len(sel)))
    guardar_json(os.path.join(CAUCE, 'cauce_resumo.json'), RESUMO)

with Cronometro('figura de control'):
    orto25, _ = leer(R('ortofoto_rgba.tif', 0.25), nan=False)
    fig, axs = plt.subplots(1, 3, figsize=(21, 9))
    for a, A in zip(axs, ARROIOS):
        g = A['eje']; b = g.bounds; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        semi = max(b[2] - b[0], b[3] - b[1]) / 2 + 60
        c0, r0 = ~tr25 * (cx - semi, cy + semi); c1, r1 = ~tr25 * (cx + semi, cy - semi)
        r0, r1, c0, c1 = [int(max(v, 0)) for v in (r0, r1, c0, c1)]; r1 = min(r1, h25); c1 = min(c1, w25)
        a.imshow(np.moveaxis(orto25[:3, r0:r1, c0:c1], 0, -1), extent=[tr25.c + c0 * 0.25, tr25.c + c1 * 0.25, tr25.f - r1 * 0.25, tr25.f - r0 * 0.25])
        x, y = g.xy; a.plot(x, y, 'c-', lw=1, label='eixo')
        for d in MEDICIONES:
            if d['arroio'] != A['nome']:
                continue
            if d['metodo'] == 'M1_espelho' and d['qualidade'] != 'baixa':
                a.plot(d['x'], d['y'], 'o' if not d['contexto'] else 'x', color='yellow' if d['qualidade'] == 'alta' else 'orange', ms=5, mec='k')
            elif d['metodo'] == 'M2_secao' and d.get('valida'):
                a.plot(d['x'], d['y'], 's', color='lime' if d['cobertura'] == 'bosque' else 'red', ms=3)
            elif d['metodo'] == 'M3_estimativa':
                a.plot(d['x'], d['y'], '^', color='magenta', ms=8, mec='k'); a.text(d['x'] + 5, d['y'], '%.1f km2\nW~%s m' % (d['A_km2'] or 0, d['largura_m']), fontsize=6, color='magenta')
        a.set_title('%s: M1 amarelo(alta)/laranja(media), M2 verde(bosque)/vermelho(campo), M3 magenta' % A['nome'], fontsize=8); a.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(os.path.join(CAUCE, '_check_ortho_07.png'), dpi=90); plt.close()
    log('  -> _check_ortho_07.png')

src_orto.close(); src_dtm.close(); src_dsm.close()
log('\northo_07 listo.')
_LOGF.close()
