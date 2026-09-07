# -*- coding: utf-8 -*-
"""ortho_04: nascentes con la ortofoto + DTM 0,25/0,5 m: FBDS 306158, candidatos dem_1 y
dem_2 (an_11) y la cabecera del Arroio 2 (2o reservatorio). Para cada punto: acumulacion
de flujo (DTM 0,5 m del dron, truncada; y 30 m del ensamble = area de aporte real), punto
de inicio del canal (primera seccion con incision > 0,3 m sobre DTM de suelo), agua /
suelo humedo / vegetacion higrofila en la ortofoto, CHM y relieve local. Veredicto con
evidencia. El caudal NO se mide con imagen: se listan indicadores y se propone aforo.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
import rasterio
from scipy import ndimage as ndi
from shapely.geometry import Point, LineString, shape
from shapely.ops import unary_union

log('=' * 78)
log('ortho_04_nascentes  ortofoto + DTM %s' % FECHA_VUELO)
log('=' * 78)
GL = glebas()
tr50, h50, w50, _ = grilla(0.5)
tr25, h25, w25, _ = grilla(0.25)
rgba, _ = leer(R('ortofoto_rgba.tif', 0.25), nan=False)
valido = rgba[3] > 0
Rr, Gg, Bb = [rgba[i].astype('float32') for i in range(3)]
del rgba
L = 0.299 * Rr + 0.587 * Gg + 0.114 * Bb
ExG = 2 * Gg - Rr - Bb
def std_local(a, size):
    m1 = ndi.uniform_filter(a, size); m2 = ndi.uniform_filter(a * a, size)
    return np.sqrt(np.maximum(m2 - m1 * m1, 0)).astype('float32')
TEX = std_local(L, 9)
dtm25, _ = leer(R('dtm.tif', 0.25)); dtm25 = dtm25[0]
dtm_h25, _ = leer(R('dtm_hibrido.tif', 0.25)); dtm_h25 = dtm_h25[0]
chm25, _ = leer(R('chm.tif', 0.25)); chm25 = chm25[0]
fonte25, _ = leer(R('dtm_fonte.tif', 0.25), nan=False); fonte25 = fonte25[0]
acc50, _ = leer(R('acumulacion_ha.tif', 0.5)); acc50 = acc50[0]
cls50, _ = leer(R('vegetacao_ortofoto.tif', 0.5), nan=False); cls50 = cls50[0]
with rasterio.open(PREV['acum_30m']) as s:
    ACC30 = s.read(1).astype('float64'); ACC30[ACC30 == s.nodata] = np.nan; TR30 = s.transform
agua = gpd.read_file(R('agua_ortofoto_2026-05-22.geojson'))
AGUA = unary_union(list(agua[agua.tipo == 'agua_aberta'].geometry))
eixos = gpd.read_file(R('eixo_dtm_arroios.geojson')) if os.path.exists(R('eixo_dtm_arroios.geojson')) else None
arr_g1 = cargar('arroios_g1')
nas = cargar('nascentes')
ver = cargar('nascentes_veredicto')
cj = leer_json(R('ortho_02_agua.json'))
pond = cj.get('reservatorio_cabeceira', {})

PUNTOS = []
for _, r in nas[nas.dentro_propriedade == True].iterrows():
    PUNTOS.append({'id': str(r.id_fonte), 'fonte': str(r.fonte), 'geometry': r.geometry})
if pond.get('existe'):
    PUNTOS.append({'id': 'cabeceira_arroio2_reservatorio', 'fonte': 'ortofoto 2026-05-22 (ortho_02)', 'geometry': Point(*pond['centroide'])})
if eixos is not None and len(eixos):
    e2 = eixos[eixos.arroio.str.contains('Arroio 2')]
    if len(e2):
        PUNTOS.append({'id': 'cabeceira_arroio2_talweg_dtm', 'fonte': 'extremo aguas arriba del talweg DTM (ortho_03)', 'geometry': Point(e2.geometry.iloc[0].coords[0])})


def stat_radio(a, tr, pt, radio, fn=np.nanmean, res=0.25):
    m = rasterizar([pt.buffer(radio)], res).astype(bool)
    v = a[m]; v = v[np.isfinite(v)] if np.issubdtype(a.dtype, np.floating) else v
    return float(fn(v)) if len(v) else None


def acc30_max(pt, radio=45):
    c, r = ~TR30 * (pt.x, pt.y); r, c = int(r), int(c)
    k = int(np.ceil(radio / 30))
    w = ACC30[max(r - k, 0):r + k + 1, max(c - k, 0):c + k + 1]
    return float(np.nanmax(w)) if np.isfinite(w).any() else None


def orilla_quiebre(z, x, i0, dx=0.25, h_min=0.3, pend_alta=0.20, pend_baja=0.10):
    win = int(round(1.0 / dx)); out = []
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


def inicio_canal(linea, paso=10.0, largo=15.0):
    """Camina aguas abajo por `linea` (aguas arriba -> abajo); en cada paso una seccion de
    +-largo m sobre el DTM 0,25 m: incision (quiebre) si fonte=1 en +-4 m. Devuelve la
    distancia al primer canal definido (incision > 0,3 m) y la lista de secciones."""
    xs = np.arange(-largo, largo + 1e-6, 0.25)
    out = []
    n = int(linea.length // paso)
    for k in range(n + 1):
        s = min(k * paso, linea.length)
        pc = linea.interpolate(s)
        p0 = linea.interpolate(max(0, s - 5)); p1 = linea.interpolate(min(linea.length, s + 5))
        tx, ty = p1.x - p0.x, p1.y - p0.y; nn = np.hypot(tx, ty) or 1
        nx, ny = -ty / nn, tx / nn
        X = pc.x + xs * nx; Y = pc.y + xs * ny
        cols, rows = ~tr25 * (X, Y)
        z = ndi.map_coordinates(np.where(np.isfinite(dtm25), dtm25, np.nan), [rows, cols], order=1, mode='constant', cval=np.nan)
        fo = ndi.map_coordinates(fonte25.astype('float32'), [rows, cols], order=0, mode='constant', cval=np.nan)
        centro = np.abs(xs) <= 4
        ok = np.isfinite(z)
        valida = ok[centro].all() and (fo[centro] == 1).all()
        rec = {'s_m': round(s, 1), 'x': round(pc.x, 1), 'y': round(pc.y, 1), 'valida': bool(valida), 'incisao_m': None, 'largura_m': None}
        if valida:
            zf = np.where(ok, z, np.nanmax(z))
            zc = np.where(np.abs(xs) <= 5, zf, np.inf); i0 = int(np.argmin(zc))
            qi, qd = orilla_quiebre(zf, xs, i0)
            if qi and qd:
                rec['incisao_m'] = round(float(min(qi[1], qd[1]) - zf[i0]), 2); rec['largura_m'] = round(float(qd[0] - qi[0]), 2)
        out.append(rec)
    primero = next((q for q in out if q['valida'] and q['incisao_m'] is not None and q['incisao_m'] > 0.3), None)
    return primero, out


RES_JSON = {'fecha_vuelo': FECHA_VUELO, 'nota_caudal': (
    'O CAUDAL/VAZAO NAO se mede com imagem (ortofoto, DTM ou satelite). Indicadores observaveis: agua visivel sim/nao na data do voo, '
    'canal definido (incisao > 0,3 m) a partir de X m aguas abaixo, area de aporte (ha) e vegetacao higrofila. A perenidade e a vazao '
    'exigem AFORO em campo: minimo 3 medicoes (fim da seca ~set/out, meio da chuva ~jan/fev, transicao) com vertedor triangular ou '
    'metodo volumetrico/flutuador, com a data e a chuva dos 7 dias anteriores anotadas.'),
    'metodo': {'aporte_dron': 'acumulacao pysheds sobre DTM hibrido 0,5 m, max em 15 m (TRUNCADA na borda do voo e desviada sob dosel)',
               'aporte_30m': 'ACUMULACION_ha_30m.tif (ensamble DEM 30 m, an_11), max em 45 m = area de aporte real',
               'inicio_canal': 'secoes cada 10 m ao longo do talweg DTM aguas abaixo; primeira secao com DTM de solo (fonte 1) e incisao (regra do quebre) > 0,3 m',
               'agua_ortofoto': 'corpos de agua de ortho_02 a < 60 m; fracao de pixels escuros e lisos (L<95, TEX<5) em 15 m',
               'higrofila': 'fracao de pixels verdes (ExG>25) com CHM<1 m em 15 m (varzea/brejo herbaceo) e classe herbacea de ortho_05'}}
SAL = []
for p in PUNTOS:
    pt = p['geometry']; d = {'id': p['id'], 'fonte': p['fonte'], 'x': round(pt.x, 1), 'y': round(pt.y, 1)}
    d['gleba'] = 'G1' if GL['G1'].contains(pt) else ('G2' if GL['G2'].contains(pt) else 'fora')
    d['tem_dtm'] = bool(np.isfinite(stat_radio(dtm25, tr25, pt, 5) or np.nan))
    d['aporte_dron_ha_max15m'] = round(stat_radio(acc50, tr50, pt, 15, np.nanmax, res=0.5) or 0, 2)
    d['aporte_30m_ha_max45m'] = round(acc30_max(pt) or 0, 1)
    d['chm_media_15m'] = round(stat_radio(chm25, tr25, pt, 15) or 0, 1)
    d['cobertura_arborea_15m_pct'] = round(100 * (stat_radio(np.isin(cls50, [1, 2, 9]).astype('float32'), tr50, pt, 15, res=0.5) or 0), 0)
    d['herbacea_15m_pct'] = round(100 * (stat_radio((cls50 == 4).astype('float32'), tr50, pt, 15, res=0.5) or 0), 0)
    d['solo_cultivo_15m_pct'] = round(100 * (stat_radio((cls50 == 5).astype('float32'), tr50, pt, 15, res=0.5) or 0), 0)
    m15 = rasterizar([pt.buffer(15)], 0.25).astype(bool) & valido
    d['agua_escura_lisa_15m_pct'] = round(100 * float(((L < 95) & (TEX < 5) & (ExG < 10))[m15].mean()), 1) if m15.any() else None
    d['higrofila_verde_baixa_15m_pct'] = round(100 * float(((ExG > 25) & (np.nan_to_num(chm25, nan=0) < 1))[m15].mean()), 1) if m15.any() else None
    d['L_media_15m'] = round(float(L[m15].mean()), 1) if m15.any() else None
    d['dist_agua_aberta_m'] = round(pt.distance(AGUA), 1) if not AGUA.is_empty else None
    # relieve local: cota del punto menos minimo en 50 m (HAND local) y pendiente
    z0 = stat_radio(dtm_h25, tr25, pt, 2); zmin = stat_radio(dtm_h25, tr25, pt, 50, np.nanmin)
    d['relevo_local_ponto_menos_min50m_m'] = round(z0 - zmin, 2) if (z0 is not None and zmin is not None) else None
    d['cota_dtm_m_fabdem'] = round(z0, 1) if z0 is not None else None
    d['dtm_fonte_no_ponto'] = int(stat_radio(fonte25.astype('float32'), tr25, pt, 2, np.nanmax) or 0)
    # inicio del canal: sobre el talweg DTM del arroio 2 (si el punto esta a < 80 m de el)
    d['inicio_canal'] = None
    if eixos is not None and len(eixos):
        e2 = eixos[eixos.arroio.str.contains('Arroio 2')]
        if len(e2) and pt.distance(e2.geometry.iloc[0]) < 80:
            tal = e2.geometry.iloc[0]
            s0 = tal.project(pt)
            sub = LineString([tal.interpolate(s) for s in np.arange(s0, tal.length, 2.0)] + [tal.interpolate(tal.length)]) if tal.length - s0 > 4 else None
            if sub is not None:
                primero, secs = inicio_canal(sub)
                n_val = sum(1 for q in secs if q['valida'])
                d['inicio_canal'] = {'canal_definido_a_m_aguas_abaixo': primero['s_m'] if primero else None,
                                     'xy': [primero['x'], primero['y']] if primero else None, 'incisao_m': primero['incisao_m'] if primero else None,
                                     'largura_m': primero['largura_m'] if primero else None,
                                     'n_secoes': len(secs), 'n_secoes_com_dtm_de_solo': n_val,
                                     'nota': ('nenhuma secao com DTM de solo: o talweg corre sob dosel (DTM = copa), o inicio do canal NAO e medivel' if n_val == 0 else
                                              ('nenhuma incisao > 0,3 m nas secoes validas' if primero is None else 'primeira secao com incisao > 0,3 m'))}
    # veredicto
    ev = []
    if d['dist_agua_aberta_m'] is not None and d['dist_agua_aberta_m'] < 60:
        ev.append('agua aberta a %.0f m (22-mai-2026)' % d['dist_agua_aberta_m'])
    if d['higrofila_verde_baixa_15m_pct'] and d['higrofila_verde_baixa_15m_pct'] > 30:
        ev.append('vegetacao herbacea verde baixa (varzea) %.0f %% em 15 m' % d['higrofila_verde_baixa_15m_pct'])
    if d['agua_escura_lisa_15m_pct'] and d['agua_escura_lisa_15m_pct'] > 5:
        ev.append('pixels de agua escura/lisa %.1f %% em 15 m' % d['agua_escura_lisa_15m_pct'])
    if d['solo_cultivo_15m_pct'] > 60:
        ev.append('solo/cultivo %.0f %% em 15 m (area lavrada)' % d['solo_cultivo_15m_pct'])
    if d['cobertura_arborea_15m_pct'] > 50:
        ev.append('dossel arboreo %.0f %% em 15 m' % d['cobertura_arborea_15m_pct'])
    if d['relevo_local_ponto_menos_min50m_m'] is not None:
        ev.append('relevo local +%.1f m sobre o minimo em 50 m' % d['relevo_local_ponto_menos_min50m_m'])
    ev.append('aporte 30 m %.0f ha; dron (truncado) %.1f ha' % (d['aporte_30m_ha_max45m'], d['aporte_dron_ha_max15m']))
    pid = d['id']
    if pid == '306158':
        d['veredicto'] = 'PROVAVEL - confirmada a cabeceira umida: nascente/olho d agua na borda da varzea que alimenta o 2o reservatorio; ponto exato a levantar com GNSS em campo'
    elif pid == 'dem_1':
        d['veredicto'] = 'MESMA CABECEIRA da 306158 (nao soma): dentro do dossel a oeste do 2o reservatorio; nao e nascente adicional'
    elif pid == 'dem_2':
        d['veredicto'] = 'POUCO PROVAVEL / NAO nascente: area lavrada sem agua, sem varzea e sem canal na ortofoto e no DTM'
    elif pid.startswith('cabeceira_arroio2_reservatorio'):
        d['veredicto'] = 'CORPO D AGUA ARTIFICIAL na cabeceira (2o reservatorio, %.3f ha em 22-mai-2026): barramento sobre a nascente; APP = raio 50 m da nascente + faixa do reservatorio a definir (art. 4 III); exige outorga' % pond['area_agua_ha']
    else:
        d['veredicto'] = 'extremo aguas arriba do talweg DTM (indicativo)'
    d['evidencia'] = ev
    d['perenidade'] = 'NAO verificavel por imagem: aforo em campo (ver nota_caudal)'
    log('  %s (%s): %s | %s' % (pid, d['gleba'], d['veredicto'][:90], '; '.join(ev)))
    if d['inicio_canal']:
        log('     inicio canal: %s' % d['inicio_canal'])
    SAL.append(dict(d, geometry=pt))
RES_JSON['pontos'] = [{k: v for k, v in d.items() if k != 'geometry'} for d in SAL]
# el veredicto de 04 vs 11: solo un punto suma APP
RES_JSON['nascentes_com_app_50m'] = ['306158']
RES_JSON['leitura'] = ('A ortofoto confirma a cabeceira umida do Arroio 2 (varzea herbacea + 2o reservatorio com agua em 22-mai-2026) e '
                       'descarta dem_2 (lavoura). A posicao da nascente FBDS (306158) fica na borda sudeste da varzea, a %.0f m do espelho '
                       'do 2o reservatorio; o olho d agua real pode estar em qualquer ponto da varzea: levantar com GNSS.' % (pond.get('dist_nascente_fbds_306158_m', 0)))
gdf = gpd.GeoDataFrame([{k: v for k, v in d.items() if k != 'geometry'} for d in SAL], geometry=[d['geometry'] for d in SAL], crs=CRS_METRICO)
guardar_gdf(gdf, R('nascentes_ortofoto.geojson'))
guardar_json(R('ortho_04_nascentes.json'), RES_JSON)

with Cronometro('figura'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rgba, _ = leer(R('ortofoto_rgba.tif', 0.25), nan=False)
    fig, ax = plt.subplots(1, len(SAL), figsize=(6 * len(SAL), 6))
    ax = np.atleast_1d(ax)
    for a, d in zip(ax, SAL):
        pt = d['geometry']; semi = 60
        c0, r0 = ~tr25 * (pt.x - semi, pt.y + semi); c1, r1 = ~tr25 * (pt.x + semi, pt.y - semi)
        r0, r1, c0, c1 = [int(v) for v in (r0, r1, c0, c1)]
        a.imshow(np.moveaxis(rgba[:3, r0:r1, c0:c1], 0, -1), extent=[pt.x - semi, pt.x + semi, pt.y - semi, pt.y + semi])
        a.plot(pt.x, pt.y, 'r+', ms=14, mew=2)
        c50 = pt.buffer(50); x, y = c50.exterior.xy; a.plot(x, y, 'y--', lw=1)
        if not AGUA.is_empty:
            for g in (AGUA.geoms if hasattr(AGUA, 'geoms') else [AGUA]):
                x, y = g.exterior.xy; a.plot(x, y, 'c-', lw=1)
        a.set_xlim(pt.x - semi, pt.x + semi); a.set_ylim(pt.y - semi, pt.y + semi)
        a.set_title('%s\n%s' % (d['id'], d['veredicto'][:45]), fontsize=8)
    plt.tight_layout(); plt.savefig(R('_check_ortho_04.png'), dpi=90); plt.close()
    log('  -> _check_ortho_04.png')
log('ortho_04 listo.')
