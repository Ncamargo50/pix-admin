# -*- coding: utf-8 -*-
"""ortho_03: talweg real desde el DTM 0,5 m (pysheds: fill, D8, acumulacion) en el
corredor +-60 m del eje FBDS; secciones transversales cada 20 m (60 m, DTM 0,25 m);
fondo, orillas (borda da calha) con reglas reproducibles; ancho bankfull; lineas
de borda; estadisticas por arroio y clase legal.

LIMITES MEDIDOS (ortho_01):
- DTM/DSM terminan en N 7401711: el Arroio 3 (sul, N 7401532-7401712) NO tiene DTM.
- El tramo de 33 m de la G2 (N 7404045-7404059) esta fuera de la ortofoto (N < 7404007).
- Bajo dosel cerrado el DTM del dron ES el dosel (dtm_fonte = 2): la seccion no mide el
  cauce. Solo se aceptan secciones con DTM de suelo (fonte = 1) en los +-6 m centrales.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
import rasterio
from scipy import ndimage as ndi
from shapely.geometry import LineString, Point, Polygon, MultiLineString, shape
from shapely.ops import unary_union, linemerge

log('=' * 78)
log('ortho_03_canais  DTM dron %s' % FECHA_VUELO)
log('=' * 78)
GL = glebas()
COB = cobertura()
H_ORTO = shape(COB['ortofoto']); H_DTM = shape(COB['dtm_dsm'])
tr50, h50, w50, b50 = grilla(0.5)
tr25, h25, w25, b25 = grilla(0.25)
dtm_h50, _ = leer(R('dtm_hibrido.tif', 0.5)); dtm_h50 = dtm_h50[0]
dtm25, _ = leer(R('dtm.tif', 0.25)); dtm25 = dtm25[0]
fonte25, _ = leer(R('dtm_fonte.tif', 0.25), nan=False); fonte25 = fonte25[0]
arb50, _ = leer(R('arboreo_rf_ortofoto.tif', 0.5), nan=False); arb50 = arb50[0].astype(bool)
verificar_arr(dtm_h50, 'dtm_hibrido 0,5', unidades='m')
verificar_arr(dtm25, 'dtm 0,25', unidades='m')

# =====================================================================================
# 1. HIDROLOGIA pysheds sobre el DTM hibrido 0,5 m
# =====================================================================================
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)      # N, NE, E, SE, S, SW, W, NW
DELTA = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
from rasterio.transform import Affine


def hidrologia_pysheds(dem_arr, transform, tag):
    """pysheds: fill_pits, fill_depressions, resolve_flats, D8, acumulacion (celdas).
    NaN -> nodata. Devuelve (FDIR int32, ACC_HA float64)."""
    from pysheds.grid import Grid
    tmp = R('_tmp_%s.tif' % tag)
    from rasterio.crs import CRS
    prof = {'driver': 'GTiff', 'height': dem_arr.shape[0], 'width': dem_arr.shape[1], 'count': 1, 'dtype': 'float32',
            'crs': CRS.from_epsg(EPSG_METRICO), 'transform': transform, 'nodata': NODATA_F, 'compress': 'LZW'}
    with rasterio.open(tmp, 'w', **prof) as d:
        d.write(np.where(np.isfinite(dem_arr), dem_arr, NODATA_F).astype('float32'), 1)
    grid = Grid.from_raster(tmp)
    dem = grid.read_raster(tmp)
    pit = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit)
    inflated = grid.resolve_flats(flooded)
    fdir = grid.flowdir(inflated, dirmap=DIRMAP, nodata_out=np.int64(0))
    acc = grid.accumulation(fdir, dirmap=DIRMAP)
    F = np.asarray(fdir).astype('int32'); A = np.asarray(acc).astype('float64')
    A[~np.isfinite(dem_arr)] = 0
    os.remove(tmp)
    return F, A * 0.25 / 1e4


with Cronometro('pysheds global sobre el DTM hibrido 0,5 m'):
    FDIR, ACC_HA = hidrologia_pysheds(dtm_h50, tr50, 'global')
    verificar_arr(np.where(np.isfinite(dtm_h50), ACC_HA, np.nan), 'acumulacion ha', unidades='ha')
escribir(R('acumulacion_ha.tif', 0.5), ACC_HA.astype('float32'), 0.5, bandas=['acum_ha'],
         tags={'unidad': 'ha', 'nota': 'truncada en el borde del vuelo; cuencas externas NO incluidas'})


def talweg_corredor(corredor_geom, eje_fbds, tag='c'):
    """Talweg = camino de MINIMO COSTO (skimage.graph.route_through_array) entre los dos extremos
    del eje FBDS (dentro de la huella del DTM), restringido al corredor +-60 m, con costo
    1 + 20 x (z - z_min_local[30 m]): el camino sigue el fondo del valle. Probado 2026-09-06:
    pysheds D8 en corredor amurallado se trunca (bajo dosel el DTM hibrido es la envolvente
    del dosel y el flujo se desvia hacia el borde campo/bosque). Devuelve (camino [(r,c)], info).
    La acumulacion se lee del pysheds GLOBAL solo como indicador."""
    from skimage.graph import route_through_array
    m_corr = rasterizar([corredor_geom], 0.5).astype(bool) & np.isfinite(dtm_h50)
    rows, cols = np.where(m_corr)
    r0, r1 = max(rows.min() - 3, 0), min(rows.max() + 4, h50); c0, c1 = max(cols.min() - 3, 0), min(cols.max() + 4, w50)
    sub = dtm_h50[r0:r1, c0:c1]; msub = m_corr[r0:r1, c0:c1]
    subf = np.where(np.isfinite(sub), sub, np.nanmax(sub)).astype('float32')
    zmin = ndi.minimum_filter(subf, size=61)                      # 30 m
    costo = 1.0 + 20.0 * np.clip(subf - zmin, 0, None)
    costo = np.where(msub, costo, 1e6).astype('float64')
    e = eje_fbds.intersection(H_DTM)
    partes = list(e.geoms) if hasattr(e, 'geoms') else [e]
    partes = [g for g in partes if g.length > 5]
    extremos = [Point(partes[0].coords[0]), Point(partes[-1].coords[-1])]
    def celda(pt):
        m = rasterizar([pt.buffer(15)], 0.5).astype(bool)[r0:r1, c0:c1] & msub
        if not m.any():
            c, r = ~tr50 * (pt.x, pt.y); return (int(r) - r0, int(c) - c0)
        z = np.where(m, subf, np.inf)
        return tuple(int(v) for v in np.unravel_index(int(np.argmin(z)), z.shape))
    a, b = celda(extremos[0]), celda(extremos[1])
    idx, cost_tot = route_through_array(costo, a, b, fully_connected=True, geometric=True)
    if subf[a] < subf[b]:
        idx = idx[::-1]
    camino = [(r + r0, c + c0) for r, c in idx]
    info = {'cota_extremos_fbds_m': [round(float(subf[a]), 1), round(float(subf[b]), 1)], 'costo_total': round(float(cost_tot), 1),
            'ventana_px': [int(r1 - r0), int(c1 - c0)], 'metodo': 'minimo costo 1+20*(z-zmin30m), corredor +-60 m'}
    return camino, info


def celdas_a_linea(camino):
    pts = [tr50 * (c + 0.5, r + 0.5) for r, c in camino]
    return LineString(pts[::-1])          # de aguas arriba a aguas abajo


def dist_stats(linea_a, linea_b, paso=5.0):
    if linea_a is None or linea_a.is_empty or linea_b is None or linea_b.is_empty:
        return None
    n = max(2, int(linea_a.length / paso))
    d = np.array([linea_a.interpolate(i / n, normalized=True).distance(linea_b) for i in range(n + 1)])
    return {'mediana_m': round(float(np.median(d)), 1), 'p90_m': round(float(np.percentile(d, 90)), 1),
            'max_m': round(float(d.max()), 1), 'n_pontos': int(n + 1)}


# =====================================================================================
# 2. TALWEG por arroio (corredor +-60 m del eje FBDS, dentro de la huella del DTM)
# =====================================================================================
arr_g1 = cargar('arroios_g1'); arr_g2 = cargar('arroios_g2')
ens = cargar('ensamble')
ARROIOS = [('G1', r) for _, r in arr_g1.iterrows()] + [('G2', r) for _, r in arr_g2.iterrows()]
RES_JSON = {'fecha_vuelo': FECHA_VUELO, 'metodo': {
    'talweg': 'camino de minimo costo (skimage route_through_array, costo 1+20*(z - zmin 30 m)) entre los extremos del eje FBDS dentro del '
              'corredor +-60 m sobre el DTM hibrido 0,5 m; acumulacion pysheds global (fill_pits, fill_depressions, resolve_flats, D8) solo como indicador. '
              'Bajo dosel el DTM es la envolvente inferior del dosel: el talweg ahi es INDICATIVO (linea mas baja del dosel, no del suelo).',
    'secciones': 'cada 20 m sobre el talweg, perpendiculares (tangente suavizada +-10 m), 60 m de largo, muestreo bilineal del DTM dron 0,25 m cada 0,25 m',
    'fondo': 'minimo del perfil en +-8 m del centro',
    'orillas_h': 'nivel = fondo + h; orilla = primer cruce del nivel caminando desde el fondo hacia afuera, a cada lado; h probado = 0,5 y 1,0 m; h_cal = mediana de la incision (quiebre) acotada a [0,5; 1,5]',
    'orillas_quiebre': 'caminando desde el fondo hacia afuera: primer punto con altura >= fondo + 0,3 m donde la pendiente local (ventana 1 m) cae por debajo de 10 % tras haber superado 20 %',
    'validez': 'seccion valida solo si dtm_fonte = 1 (suelo) en el 100 % de los +-6 m centrales y >= 80 % del perfil con dato; bajo dosel (fonte 2) NO se mide',
}}
EIXOS, SECOES, BORDAS, CALHAS = [], [], [], []
PERFILES_PNG = []


def perpendicular(linea, s, ds=10.0):
    p0 = linea.interpolate(max(0, s - ds)); p1 = linea.interpolate(min(linea.length, s + ds))
    tx, ty = p1.x - p0.x, p1.y - p0.y
    n = np.hypot(tx, ty) or 1.0
    return (-ty / n, tx / n)      # normal a la izquierda (mirando aguas abajo)


def muestrear(a, tr, xs, ys, order=1):
    cols, rows = ~tr * (xs, ys)
    return ndi.map_coordinates(np.where(np.isfinite(a), a, np.nan) if a.dtype.kind == 'f' else a,
                               [rows, cols], order=order, mode='constant', cval=np.nan)


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


def orilla_quiebre(z, x, i0, dx=0.25, h_min=0.3, pend_alta=0.20, pend_baja=0.10):
    """Devuelve (x_izq, z_izq, x_der, z_der) o None por lado."""
    win = int(round(1.0 / dx))
    out = []
    for direccion in (-1, 1):
        res = None
        subio = False
        i = i0
        while 0 <= i + direccion * win < len(z):
            j = i + direccion * win
            pend = abs(z[j] - z[i]) / (win * dx)
            if pend >= pend_alta:
                subio = True
            if subio and (z[j] - z[i0]) >= h_min and pend < pend_baja:
                res = (x[j], z[j]); break
            if (z[j] - z[i0]) < -0.05 and abs(x[j] - x[i0]) > 3:   # baja de nuevo: otra depresion, sin quiebre
                break
            i += direccion
        out.append(res)
    return out


for gleba, r in ARROIOS:
    nome = r['nome']; eje_fbds = r.geometry
    key = '%s %s' % (gleba, nome)
    log('\n--- %s (FBDS %.0f m dentro) ---' % (key, eje_fbds.length))
    info = {'gleba': gleba, 'arroio': nome, 'fbds_m': round(eje_fbds.length, 1),
            'cobertura_ortofoto_pct': round(100 * eje_fbds.intersection(H_ORTO).length / eje_fbds.length, 1),
            'cobertura_dtm_pct': round(100 * eje_fbds.intersection(H_DTM).length / eje_fbds.length, 1)}
    if info['cobertura_dtm_pct'] < 10:
        info['estado'] = 'SEM DTM (fora da huella do DSM/DTM do voo): talweg e secoes NAO calculaveis; permanece o eixo FBDS'
        log('  ' + info['estado'])
        RES_JSON[key] = info
        continue
    corredor = eje_fbds.buffer(60).intersection(H_DTM.buffer(-1))
    camino, info_tw = talweg_corredor(corredor, eje_fbds, tag='corr_%s_%d' % (gleba, int(r['n'])))
    info['talweg_corredor'] = info_tw
    if len(camino) < 20:
        info['estado'] = 'talweg nao tracado'
        RES_JSON[key] = info; log('  ' + info['estado']); continue
    talweg = LineString([tr50 * (c + 0.5, r_ + 0.5) for r_, c in camino]).simplify(0.25)
    acc_path = np.array([ACC_HA[r_, c] for r_, c in camino])
    acc_max, acc_min = float(np.nanmax(acc_path)), float(np.nanmin(acc_path))
    fo_path = np.array([fonte25[min(2 * r_ + 1, h25 - 1), min(2 * c + 1, w25 - 1)] for r_, c in camino])
    info['talweg_pct_com_dtm_de_solo'] = round(100.0 * float((fo_path == 1).mean()), 1)
    # sentido: de aguas arriba (menor acc) a aguas abajo; celdas_a_linea ya invierte el camino (que se trazo hacia arriba)
    tal_dentro = talweg.intersection(GL[gleba].buffer(0.5))
    info.update({'talweg_m_total': round(talweg.length, 1), 'talweg_m_dentro_gleba': round(tal_dentro.length, 1),
                 'acc_ha_max_no_talweg': round(acc_max, 2), 'acc_ha_min_no_talweg': round(acc_min, 2),
                 'acc_nota': 'acumulacion pysheds global sobre el DTM hibrido, truncada en el borde del vuelo y desviada bajo dosel: INDICADOR'})
    # distancias eje FBDS <-> talweg DTM, y ensamble 30 m <-> talweg
    e_fb = eje_fbds.intersection(H_DTM)
    info['dist_fbds_vs_talweg'] = dist_stats(e_fb, talweg)
    info['dist_talweg_vs_fbds'] = dist_stats(talweg, eje_fbds)
    ens_i = ens[(ens.gleba == gleba) & (ens.arroio == nome) & (ens.tipo == 'mediana_ensamble')]
    if len(ens_i):
        info['dist_ensamble30m_vs_talweg'] = dist_stats(ens_i.geometry.iloc[0].intersection(H_DTM), talweg)
    log('  talweg %.0f m (dentro %.0f m); acc %.2f -> %.2f ha; FBDS->talweg %s' % (talweg.length, tal_dentro.length, acc_min, acc_max, info['dist_fbds_vs_talweg']))
    EIXOS.append({'gleba': gleba, 'arroio': nome, 'fonte': 'talweg DTM dron 0,5 m (minimo costo no corredor FBDS +-60 m)', 'pct_com_dtm_de_solo': info['talweg_pct_com_dtm_de_solo'], 'comprimento_m': round(talweg.length, 1),
                  'comprimento_dentro_gleba_m': round(tal_dentro.length, 1), 'acc_ha_max': round(acc_max, 2), 'geometry': talweg})

    # ---------------- secciones cada 20 m ----------------
    secs = []
    n_s = int(talweg.length // 20)
    xs_prof = np.arange(-30, 30 + 1e-6, 0.25)
    for k in range(n_s + 1):
        s = min(k * 20.0, talweg.length)
        pc = talweg.interpolate(s)
        nx, ny = perpendicular(talweg, s)
        X = pc.x + xs_prof * nx; Y = pc.y + xs_prof * ny
        z = muestrear(dtm25, tr25, X, Y)
        fo = muestrear(fonte25.astype('float32'), tr25, X, Y, order=0)
        ar = muestrear(arb50.astype('float32'), tr50, X, Y, order=0)
        ok = np.isfinite(z)
        centro = np.abs(xs_prof) <= 6
        pct_dato = 100 * ok.mean()
        pct_dosel_centro = 100 * np.nanmean(np.where(np.isfinite(fo[centro]), fo[centro] == 2, np.nan)) if np.isfinite(fo[centro]).any() else 100.0
        pct_arb_perfil = 100 * np.nanmean(ar) if np.isfinite(ar).any() else np.nan
        valida = (pct_dato >= 80) and (pct_dosel_centro == 0) and ok[centro].all()
        rec = {'gleba': gleba, 'arroio': nome, 'id_secao': k, 's_m': round(s, 1), 'x': round(pc.x, 2), 'y': round(pc.y, 2),
               'pct_com_dado': round(pct_dato, 1), 'pct_dosel_centro': round(pct_dosel_centro, 1), 'pct_arboreo_perfil': round(float(pct_arb_perfil), 1) if np.isfinite(pct_arb_perfil) else None,
               'valida': bool(valida), 'motivo': '' if valida else ('dosel no penetrado (DTM = copa)' if pct_dosel_centro > 0 else 'sin dato en el perfil'),
               'geometry': LineString([(X[0], Y[0]), (X[-1], Y[-1])])}
        if valida:
            zz = z.copy()
            zz[~ok] = np.nan
            zc = np.where(np.abs(xs_prof) <= 8, zz, np.nan)
            i0 = int(np.nanargmin(zc))
            z_f = float(zz[i0])
            zf = np.where(np.isfinite(zz), zz, np.nanmax(zz))
            rec.update({'x_fondo_m': round(float(xs_prof[i0]), 2), 'z_fondo_m': round(z_f, 2)})
            for h in (0.5, 1.0, 1.5):
                xl, xr = orilla_h(zf, xs_prof, i0, h)
                rec['largura_h%s_m' % h] = round(float(xr - xl), 2) if (xl is not None and xr is not None) else None
                rec['xl_h%s' % h] = round(float(xl), 2) if xl is not None else None
                rec['xr_h%s' % h] = round(float(xr), 2) if xr is not None else None
            qi, qd = orilla_quiebre(zf, xs_prof, i0)
            if qi and qd:
                rec.update({'largura_quiebre_m': round(float(qd[0] - qi[0]), 2), 'xl_quiebre': round(float(qi[0]), 2), 'xr_quiebre': round(float(qd[0]), 2),
                            'incisao_m': round(float(min(qi[1], qd[1]) - z_f), 2), 'z_margem_esq_m': round(float(qi[1]), 2), 'z_margem_dir_m': round(float(qd[1]), 2)})
            else:
                rec.update({'largura_quiebre_m': None, 'incisao_m': None})
            rec['perfil_z'] = [round(float(v), 2) if np.isfinite(v) else None for v in zz[::4]]   # cada 1 m
        secs.append(rec)
    n_val = sum(1 for q in secs if q['valida'])
    n_dosel = sum(1 for q in secs if q['motivo'].startswith('dosel'))
    log('  secciones: %d, validas %d, bajo dosel %d, sin dato %d' % (len(secs), n_val, n_dosel, len(secs) - n_val - n_dosel))
    SECOES.extend(secs)

    # ---------------- estadisticas ----------------
    est = {'n_secoes': len(secs), 'n_validas': n_val, 'n_dosel': n_dosel, 'pct_talweg_sob_dosel': round(100.0 * n_dosel / max(len(secs), 1), 1)}
    def q(vals):
        v = np.array([x for x in vals if x is not None and np.isfinite(x)], float)
        if len(v) == 0:
            return None
        return {'n': int(len(v)), 'mediana_m': round(float(np.median(v)), 2), 'p90_m': round(float(np.percentile(v, 90)), 2), 'max_m': round(float(v.max()), 2)}
    inc = q([x.get('incisao_m') for x in secs if x['valida']])
    est['incisao_quiebre'] = inc
    h_cal = min(1.5, max(0.5, inc['mediana_m'])) if inc else 1.0
    h_cal = round(h_cal * 2) / 2.0
    est['h_calibrado_m'] = h_cal
    for h in (0.5, 1.0, 1.5):
        est['largura_h%s' % h] = q([x.get('largura_h%s_m' % h) for x in secs if x['valida']])
    est['largura_quiebre'] = q([x.get('largura_quiebre_m') for x in secs if x['valida']])
    est['largura_bankfull_h_cal'] = est['largura_h%s' % h_cal]
    lb = est['largura_bankfull_h_cal']
    if lb:
        est['classe_legal'] = 'ate 10 m -> APP 30 m' if lb['max_m'] < 10 else 'ATENCAO: alguma secao >= 10 m (verificar)'
        est['n_secoes_ge_10m'] = int(sum(1 for x in secs if x['valida'] and x.get('largura_h%s_m' % h_cal) is not None and x['largura_h%s_m' % h_cal] >= 10))
    else:
        est['classe_legal'] = 'NAO MEDIVEL (sem secoes validas)'
    info['secoes'] = est
    log('  incisao %s | largura h_cal=%.1f %s | quiebre %s | classe %s' % (inc, h_cal, lb, est['largura_quiebre'], est['classe_legal']))

    # ---------------- bordas da calha ----------------
    # semi-anchos por seccion valida (h_cal), interpolados a lo largo del talweg; secciones invalidas -> mediana (extrapolado)
    ss = np.array([x['s_m'] for x in secs], float)
    hl = np.array([(-x['xl_h%s' % h_cal]) if (x['valida'] and x.get('xl_h%s' % h_cal) is not None) else np.nan for x in secs], float)
    hr = np.array([(x['xr_h%s' % h_cal]) if (x['valida'] and x.get('xr_h%s' % h_cal) is not None) else np.nan for x in secs], float)
    # corrimiento del fondo respecto del talweg (el minimo puede no estar en el centro)
    xf = np.array([x.get('x_fondo_m', np.nan) if x['valida'] else np.nan for x in secs], float)
    ok = np.isfinite(hl) & np.isfinite(hr)
    if ok.sum() >= 2 and ok.sum() >= 0.5 * len(secs):
        med_l, med_r = float(np.nanmedian(hl[ok])), float(np.nanmedian(hr[ok]))
        # filtro de mediana (3) sobre las validas para no propagar una seccion rara
        s_ok = ss[ok]; hl_ok = ndi.median_filter(hl[ok], 3, mode='nearest'); hr_ok = ndi.median_filter(hr[ok], 3, mode='nearest'); xf_ok = ndi.median_filter(xf[ok], 3, mode='nearest')
        pasos = np.arange(0, talweg.length + 1e-6, 2.0)
        L_pts, R_pts, extrap = [], [], []
        for s in pasos:
            pc = talweg.interpolate(s); nx, ny = perpendicular(talweg, s)
            # extrapolado si la seccion valida mas cercana esta a > 30 m
            dmin = float(np.min(np.abs(s_ok - s)))
            if dmin <= 30:
                l = float(np.interp(s, s_ok, hl_ok)); rr_ = float(np.interp(s, s_ok, hr_ok)); x0 = float(np.interp(s, s_ok, xf_ok))
            else:
                l, rr_, x0 = med_l, med_r, 0.0
            L_pts.append((pc.x + (x0 - l) * nx, pc.y + (x0 - l) * ny))
            R_pts.append((pc.x + (x0 + rr_) * nx, pc.y + (x0 + rr_) * ny))
            extrap.append(dmin > 30)
        m_ext = 100.0 * np.mean(extrap)
        BORDAS.append({'gleba': gleba, 'arroio': nome, 'lado': 'esquerda', 'h_cal_m': h_cal, 'pct_extrapolado': round(m_ext, 1), 'geometry': LineString(L_pts)})
        BORDAS.append({'gleba': gleba, 'arroio': nome, 'lado': 'direita', 'h_cal_m': h_cal, 'pct_extrapolado': round(m_ext, 1), 'geometry': LineString(R_pts)})
        calha = Polygon(L_pts + R_pts[::-1]).buffer(0)
        CALHAS.append({'gleba': gleba, 'arroio': nome, 'h_cal_m': h_cal, 'largura_mediana_m': round(med_l + med_r, 2), 'pct_extrapolado': round(m_ext, 1),
                       'area_ha': ha(calha), 'geometry': calha})
        info['bordas'] = {'h_cal_m': h_cal, 'semi_largura_esq_mediana_m': round(med_l, 2), 'semi_largura_dir_mediana_m': round(med_r, 2),
                          'pct_extrapolado_sob_dosel': round(m_ext, 1), 'area_calha_ha': ha(calha)}
        log('  bordas: semi-ancho izq %.2f / der %.2f m (mediana), %.0f %% del talweg extrapolado (sin seccion valida a < 30 m)' % (med_l, med_r, m_ext))
    else:
        info['bordas'] = None
        info['bordas_nota'] = 'NAO construidas: menos de 50 %% das secoes com DTM de solo (%d de %d); sob dosel a borda da calha NAO e medivel com este DTM' % (int(ok.sum()), len(secs))
        log('  bordas: NO construidas (%d/%d secciones validas < 50 %%)' % (int(ok.sum()), len(secs)))
    RES_JSON[key] = info

# =====================================================================================
# 3. salidas
# =====================================================================================
def gdf_de(lista):
    if not lista:
        return gpd.GeoDataFrame(geometry=[], crs=CRS_METRICO)
    return gpd.GeoDataFrame([{k: v for k, v in d.items() if k != 'geometry'} for d in lista], geometry=[d['geometry'] for d in lista], crs=CRS_METRICO)

guardar_gdf(gdf_de(EIXOS), R('eixo_dtm_arroios.geojson'))
sec_gdf = gdf_de(SECOES)
if len(sec_gdf):
    sec_gdf['perfil_z'] = sec_gdf['perfil_z'].apply(lambda v: json.dumps(v) if isinstance(v, list) else v) if 'perfil_z' in sec_gdf else None
guardar_gdf(sec_gdf, R('secoes_transversais.geojson'))
guardar_gdf(gdf_de(BORDAS), R('bordas_calha.geojson'))
guardar_gdf(gdf_de(CALHAS), R('calha_poligono.geojson'))
guardar_json(R('ortho_03_canais.json'), RES_JSON)

# perfiles ejemplo (PNG): 4 secciones validas repartidas + 1 bajo dosel para mostrar el problema
with Cronometro('perfiles PNG'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    validas = [s_ for s_ in SECOES if s_['valida'] and s_.get('largura_quiebre_m')]
    if validas:
        idx = np.linspace(0, len(validas) - 1, min(4, len(validas))).astype(int)
        ejemplos = [validas[i] for i in idx]
        dosel = [s_ for s_ in SECOES if s_['motivo'].startswith('dosel')]
        fig, ax = plt.subplots(len(ejemplos) + (1 if dosel else 0), 1, figsize=(11, 3.2 * (len(ejemplos) + 1)))
        ax = np.atleast_1d(ax)
        for a, s_ in zip(ax, ejemplos):
            zz = np.array([np.nan if v is None else v for v in s_['perfil_z']], float)
            xx = np.arange(-30, 30 + 1e-6, 1.0)[:len(zz)]
            a.plot(xx, zz, 'k.-', ms=3)
            a.axvline(s_['x_fondo_m'], color='b', ls=':', label='fondo z=%.2f' % s_['z_fondo_m'])
            for h, col in ((0.5, 'g'), (1.0, 'orange'), (1.5, 'r')):
                if s_.get('xl_h%s' % h) is not None:
                    a.plot([s_['xl_h%s' % h], s_['xr_h%s' % h]], [s_['z_fondo_m'] + h] * 2, col, lw=2, label='h=%.1f: %.1f m' % (h, s_['largura_h%s_m' % h]))
            if s_.get('xl_quiebre') is not None:
                a.plot([s_['xl_quiebre'], s_['xr_quiebre']], [s_['z_margem_esq_m'], s_['z_margem_dir_m']], 'mv', ms=8, label='quiebre: %.1f m, incisao %.2f m' % (s_['largura_quiebre_m'], s_['incisao_m']))
            a.set_title('%s %s - seccion %d (s=%.0f m, x=%.0f y=%.0f) arboreo %.0f %%' % (s_['gleba'], s_['arroio'], s_['id_secao'], s_['s_m'], s_['x'], s_['y'], s_['pct_arboreo_perfil'] or 0))
            a.set_xlabel('distancia al talweg (m), izquierda -> derecha mirando aguas abajo'); a.set_ylabel('cota (m, FABDEM)'); a.legend(fontsize=7); a.grid(alpha=.3)
        if dosel:
            s_ = dosel[len(dosel) // 2]
            pc = Point(s_['x'], s_['y']); a = ax[-1]
            X = np.array(s_['geometry'].coords)
            xs_ = np.linspace(-30, 30, 241); nx = (X[1][0] - X[0][0]) / 60; ny = (X[1][1] - X[0][1]) / 60
            z = muestrear(dtm25, tr25, pc.x + xs_ * nx, pc.y + xs_ * ny)
            a.plot(xs_, z, 'r.-', ms=3); a.set_title('EJEMPLO BAJO DOSEL (no medible): %s seccion %d - el "DTM" es la copa' % (s_['arroio'], s_['id_secao']))
            a.set_xlabel('m'); a.set_ylabel('cota (m)'); a.grid(alpha=.3)
        plt.tight_layout(); plt.savefig(R('_perfiles_ejemplo_ortho_03.png'), dpi=100); plt.close()
        log('  -> _perfiles_ejemplo_ortho_03.png')

# mapa de control
with Cronometro('figura de control'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    hs, _ = leer(R('dtm_hillshade.tif', 0.5), nan=False)
    fig, axs = plt.subplots(1, len(EIXOS) or 1, figsize=(7 * max(len(EIXOS), 1), 9))
    axs = np.atleast_1d(axs)
    for a, e in zip(axs, EIXOS):
        g = e['geometry']; b = g.bounds; cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        semi = max(b[2] - b[0], b[3] - b[1]) / 2 + 60
        c0, r0 = ~tr50 * (cx - semi, cy + semi); c1, r1 = ~tr50 * (cx + semi, cy - semi)
        r0, r1, c0, c1 = [int(max(v, 0)) for v in (r0, r1, c0, c1)]
        a.imshow(hs[0, r0:r1, c0:c1], cmap='gray', extent=[tr50.c + c0 * 0.5, tr50.c + c1 * 0.5, tr50.f - r1 * 0.5, tr50.f - r0 * 0.5])
        for _, rr_ in (arr_g1 if e['gleba'] == 'G1' else arr_g2).iterrows():
            if rr_['nome'] == e['arroio']:
                x, y = rr_.geometry.xy; a.plot(x, y, 'm-', lw=1.5, label='eje FBDS')
        x, y = g.xy; a.plot(x, y, 'c-', lw=1.5, label='talweg DTM')
        for bdd in BORDAS:
            if bdd['arroio'] == e['arroio'] and bdd['gleba'] == e['gleba']:
                x, y = bdd['geometry'].xy; a.plot(x, y, 'y-', lw=0.8)
        for s_ in SECOES:
            if s_['arroio'] == e['arroio'] and s_['gleba'] == e['gleba']:
                x, y = s_['geometry'].xy; a.plot(x, y, 'g-' if s_['valida'] else 'r-', lw=0.5, alpha=0.7)
        a.set_title('%s %s (verde=seccion valida, rojo=dosel/sin dato)' % (e['gleba'], e['arroio']), fontsize=9); a.legend(fontsize=7)
    plt.tight_layout(); plt.savefig(R('_check_ortho_03.png'), dpi=100); plt.close()
    log('  -> _check_ortho_03.png')
log('ortho_03 listo.')
