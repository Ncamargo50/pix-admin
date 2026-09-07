# -*- coding: utf-8 -*-
"""ortho_05: clasificacion de cobertura a 0,5 m con CHM + color (ortofoto 22-mai-2026).

Clases (uint8):
 1 arborea, altura medida (CHM dron >= 3 m)
 2 arborea, dosel fechado (copa clasificada, CHM < 1 m: el DTM del dron no penetro; altura NO medida)
 3 arbustiva / regeneracao (1 <= CHM < 3 m, verde)
 4 herbacea / pasto (verde, CHM < 1 m)
 5 solo / cultivo / restolho
 6 agua (ortho_02)
 7 construcoes
 8 silvicultura (hileras regulares) - separada de la arborea
 9 arborea/arbustiva SEM CHM (faixa sul N < 7401711: so cor+textura, altura desconhecida)

LIMITES MEDIDOS: (a) sem DSM/DTM ao sul de N 7401711 (represa, Arroio 3, fragmento 30); (b) sob dosel
fechado o CHM do dron e ~0 (DTM = DSM): a altura so se mede nas copas/bordas onde o SMRF achou solo.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortho_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.warp import reproject
from rasterio.enums import Resampling
from scipy import ndimage as ndi
from shapely.geometry import shape
from shapely.ops import unary_union

log('=' * 78)
log('ortho_05_vegetacao  ortofoto %s  (0,5 m)' % FECHA_VUELO)
log('=' * 78)
RES = 0.5
tr, H, W, B = grilla(RES)
GL = glebas()
COB = cobertura()
H_DTM = shape(COB['dtm_dsm'])
rgba, _ = leer(R('ortofoto_rgba.tif', RES), nan=False)
valido = rgba[3] > 0
Rr, Gg, Bb = [rgba[i].astype('float32') for i in range(3)]
del rgba
chm, _ = leer(R('chm.tif', RES)); chm = chm[0]
chm_h, _ = leer(R('chm_hibrido.tif', RES)); chm_h = chm_h[0]
dsm, _ = leer(R('dsm.tif', RES)); dsm = dsm[0]
fonte, _ = leer(R('dtm_fonte.tif', RES), nan=False); fonte = fonte[0]
arb, _ = leer(R('arboreo_rf_ortofoto.tif', RES), nan=False); arb = arb[0].astype(bool)
prob_arb, _ = leer(R('arboreo_prob_ortofoto.tif', RES)); prob_arb = prob_arb[0]
hay_chm = np.isfinite(chm)
m_prop = rasterizar([GL['IMOVEL']], RES).astype(bool)
m_g = {g: rasterizar([GL[g]], RES).astype(bool) for g in ('G1', 'G2')}

# --- rasgos de color -------------------------------------------------------------------
L = 0.299 * Rr + 0.587 * Gg + 0.114 * Bb
ExG = 2 * Gg - Rr - Bb
mx = np.maximum(np.maximum(Rr, Gg), Bb); mn = np.minimum(np.minimum(Rr, Gg), Bb)
S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).astype('float32')
def std_local(a, size):
    m1 = ndi.uniform_filter(a, size); m2 = ndi.uniform_filter(a * a, size)
    return np.sqrt(np.maximum(m2 - m1 * m1, 0)).astype('float32')
TEX9 = std_local(L, 9); TEX21 = std_local(L, 21)
for nombre, a in (('L', L), ('ExG', ExG), ('S', S), ('TEX9', TEX9)):
    verificar_arr(np.where(valido, a, np.nan), nombre, m_prop)
verificar_arr(chm, 'chm', m_prop, 'm')

# --- RF S2 10 m (previo) en la grilla 0,5 m --------------------------------------------
with rasterio.open(PREV['veg_10m_tif']) as s:
    rf10 = np.zeros((H, W), 'uint8')
    reproject(rasterio.band(s, 1), rf10, dst_transform=tr, dst_crs=CRS_METRICO, resampling=Resampling.nearest)
RF_NOMBRES = {1: 'FLORESTA_NATIVA', 2: 'AGUA', 3: 'AREA_ANTROPIZADA', 4: 'SILVICULTURA', 5: 'VEG_HERBACEA_NATIVA'}

# --- agua (ortho_02) -----------------------------------------------------------------------
agua = gpd.read_file(R('agua_ortofoto_2026-05-22.geojson'))
agua_conf = agua[(agua.tipo == 'agua_aberta') | ((agua.tipo == 'candidato') & (agua.dsm_disponivel == True) & (agua.area_ha >= 0.03))]
m_agua = rasterizar(list(agua_conf.geometry), RES).astype(bool)
log('  agua rasterizada: %.3f ha (%d cuerpos)' % (m_agua.sum() * RES * RES / 1e4, len(agua_conf)))

# =====================================================================================
# 1. cobertura arborea en la faixa SUL sin DSM: RF solo color/textura (entrenado en el norte)
# =====================================================================================
with Cronometro('RF color/textura para la faixa sin CHM'):
    from sklearn.ensemble import RandomForestClassifier
    feats = np.stack([Rr, Gg, Bb, L, ExG, S, TEX9, TEX21], -1)
    F2 = feats.reshape(-1, feats.shape[-1])
    rs = np.random.RandomState(1)
    pos = valido & hay_chm & (chm >= 3) & (ExG > 5)
    neg = valido & hay_chm & (chm < 0.3) & ~arb
    ip = rs.choice(np.flatnonzero(pos), 50000, replace=False); im = rs.choice(np.flatnonzero(neg), 50000, replace=False)
    X = np.concatenate([F2[ip], F2[im]]); y = np.concatenate([np.ones(len(ip)), np.zeros(len(im))])
    perm = rs.permutation(len(y)); nv = len(y) // 5
    rf = RandomForestClassifier(n_estimators=120, min_samples_leaf=20, n_jobs=-1, random_state=1).fit(X[perm[nv:]], y[perm[nv:]])
    acc = float((rf.predict(X[perm[:nv]]) == y[perm[:nv]]).mean())
    sin_chm = valido & ~hay_chm
    prob_sul = np.zeros((H, W), 'float32')
    idx = np.flatnonzero(sin_chm)
    if len(idx):
        prob_sul.reshape(-1)[idx] = rf.predict_proba(F2[idx])[:, 1]
    arb_sul = (prob_sul > 0.5) & sin_chm
    arb_sul = ndi.binary_opening(arb_sul, iterations=1); arb_sul = ndi.binary_closing(arb_sul, iterations=2)
    # PROBADO 2026-09-06: sin CHM el RF de color marca como "arboreo" la faja verde de la rodovia del limite sur
    # (y sus marcas viales daban periodicidad de "silvicultura"). Filtro por componente: se conserva si esta
    # apoyado en floresta del RF S2 (dilatada 10 m) o si es compacto (area/hull >= 0,4), >= 0,05 ha y con textura de copas.
    rf_fl_dil = ndi.binary_dilation(rf10 == 1, iterations=20)
    lab_s, n_s = ndi.label(arb_sul)
    keep = np.zeros(n_s + 1, bool)
    descartados_ha = 0.0
    for k in range(1, n_s + 1):
        m = lab_s == k
        a_ha = m.sum() * RES * RES / 1e4
        fr_fl = float(rf_fl_dil[m].mean())
        rows_, cols_ = np.where(m)
        # compacidad aproximada: area / area del bbox rotado ~ usamos area / (bbox area) y elongacion del bbox
        hbb, wbb = int(np.ptp(rows_)) + 1, int(np.ptp(cols_)) + 1
        comp = m.sum() / float(hbb * wbb)
        elong = max(hbb, wbb) / max(min(hbb, wbb), 1)
        tex = float(TEX9[m].mean())
        if fr_fl >= 0.3 or (a_ha >= 0.05 and comp >= 0.4 and elong < 4 and tex >= 12):
            keep[k] = True
        else:
            descartados_ha += a_ha
    arb_sul = keep[lab_s]
    log('  faixa sin CHM: %d componentes, %.2f ha descartados por forma/apoyo (rodovia, faixas lineales)' % (n_s, descartados_ha))
    # control: el mismo RF color aplicado en el norte vs el clasificador con DSM
    pred_norte = np.zeros((H, W), bool)
    idn = np.flatnonzero(valido & hay_chm)
    sel = rs.choice(idn, min(2000000, len(idn)), replace=False)
    pn = rf.predict_proba(F2[sel])[:, 1] > 0.5
    concord = float((pn == arb.reshape(-1)[sel]).mean())
    log('  RF color/textura: acc %.3f; concordancia con el clasificador DSM en el norte %.3f; arboreo en la faixa sin CHM: %.2f ha'
        % (acc, concord, (arb_sul & m_prop).sum() * RES * RES / 1e4))
    del feats, F2

# =====================================================================================
# 2. clasificacion
# =====================================================================================
with Cronometro('clasificacion'):
    cls = np.zeros((H, W), 'uint8')
    verde = ExG > 12
    # construcoes: brillantes y lisas (techos) o altas y no verdes con DSM
    techo = valido & (((L > 185) & (S < 0.35) & (TEX9 < 8)) | (hay_chm & (chm >= 2.5) & (ExG < 5) & (S < 0.35)))
    techo = ndi.binary_opening(techo, iterations=2); techo = ndi.binary_closing(techo, iterations=2)
    lab, n = ndi.label(techo)
    if n:
        tam = ndi.sum(techo, lab, np.arange(1, n + 1)) * RES * RES
        kp = np.zeros(n + 1, bool); kp[1:] = tam >= 20
        techo = kp[lab]
    # zona con CHM
    z = valido & hay_chm
    cls[z & ~verde] = 5
    cls[z & verde & (chm < 1)] = 4
    cls[z & verde & (chm >= 1) & (chm < 3) & ~arb] = 3
    cls[z & arb & (chm >= 1) & (chm < 3)] = 3
    cls[z & arb & (chm < 1)] = 2
    cls[z & (chm >= 3) & (arb | verde)] = 1
    # zona sin CHM (sur): color + RF color
    zs = valido & ~hay_chm
    cls[zs & ~verde] = 5
    cls[zs & verde] = 4
    cls[zs & arb_sul] = 9
    cls[techo & ~arb & ~arb_sul] = 7
    cls[m_agua] = 6
    cls[~valido] = 0
    # sieve MMU 25 m2 = 100 px
    from skimage.morphology import remove_small_objects
    out = cls.copy()
    for k in (1, 2, 3, 4, 5, 6, 7, 9):
        m = cls == k
        m2 = remove_small_objects(m, 100)
        out[m & ~m2] = 0
    # rellenar lo eliminado con la clase vecina mayoritaria (moda en 3x3 iterada)
    huecos = (out == 0) & valido
    for _ in range(6):
        if not huecos.any():
            break
        from scipy.stats import mode
        vec = np.stack([np.roll(np.roll(out, dr, 0), dc, 1) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)], 0)
        vec = np.where(vec == 0, 255, vec)
        md = mode(vec, axis=0, keepdims=False).mode
        rell = huecos & (md != 255)
        out[rell] = md[rell]
        huecos = (out == 0) & valido
    cls = out
    NOMBRES = {1: 'arborea_altura_medida', 2: 'arborea_dosel_fechado', 3: 'arbustiva_regeneracao', 4: 'herbacea_pasto',
               5: 'solo_cultivo', 6: 'agua', 7: 'construcoes', 8: 'silvicultura', 9: 'arborea_arbustiva_sem_chm'}

# =====================================================================================
# 3. silvicultura: hileras regulares + altura homogenea (espectro 2D del CHM/DSM)
# =====================================================================================
with Cronometro('silvicultura (periodicidad)'):
    arboreo_all = np.isin(cls, [1, 2, 3, 9])
    lab, n = ndi.label(ndi.binary_closing(np.isin(cls, [1, 2, 9]), iterations=2))
    silv_rf10 = rf10 == 4
    comps = []
    for k in range(1, n + 1):
        m = lab == k
        a_m2 = m.sum() * RES * RES
        if a_m2 < 1000:
            continue
        rows, cols = np.where(m)
        r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
        sub_m = m[r0:r1, c0:c1]
        src = dsm if np.isfinite(dsm[m]).mean() > 0.5 else L
        a = np.where(sub_m & np.isfinite(src[r0:r1, c0:c1]), src[r0:r1, c0:c1], np.nan)
        a = a - np.nanmean(a)
        a = np.where(np.isfinite(a), a, 0)
        # quitar tendencia (pendiente) con un filtro gaussiano 10 m
        a = a - ndi.gaussian_filter(a, 20)
        Fp = np.abs(np.fft.fftshift(np.fft.fft2(a * sub_m))) ** 2
        fy = np.fft.fftshift(np.fft.fftfreq(a.shape[0], RES)); fx = np.fft.fftshift(np.fft.fftfreq(a.shape[1], RES))
        FX, FY = np.meshgrid(fx, fy)
        fr = np.hypot(FX, FY)
        banda = (fr >= 1 / 5.0) & (fr <= 1 / 2.0)     # longitudes de onda 2-5 m (espaciamiento tipico de eucalipto)
        resto = fr > 1 / 40.0
        e_banda = Fp[banda].sum(); e_tot = Fp[resto].sum() + 1e-9
        # pico direccional: maximo del espectro en la banda vs media de la banda
        pico = Fp[banda].max() / (Fp[banda].mean() + 1e-9)
        cv = float(np.nanstd(chm[m]) / (np.nanmean(chm[m]) + 1e-6)) if np.isfinite(chm[m]).any() else None
        fr_rf = float(silv_rf10[m].mean())
        comps.append({'id': k, 'area_ha': round(a_m2 / 1e4, 3), 'x': round(float(cols.mean() * RES + tr.c), 1), 'y': round(float(tr.f - rows.mean() * RES), 1),
                      'frac_energia_2_5m': round(float(e_banda / e_tot), 3), 'pico_direccional': round(float(pico), 1),
                      'cv_chm': round(cv, 2) if cv is not None else None, 'frac_rf_s2_silvicultura': round(fr_rf, 2), 'mask': m})
    comps.sort(key=lambda d: -d['pico_direccional'])
    ref = [c for c in comps if c['frac_rf_s2_silvicultura'] >= 0.5]
    umbral_pico = min(c['pico_direccional'] for c in ref) * 0.9 if ref else np.inf
    umbral_frac = min(c['frac_energia_2_5m'] for c in ref) * 0.9 if ref else np.inf
    log('  componentes arboreos >= 0,1 ha: %d; con RF-S2 silvicultura >= 50 %%: %d; umbrales (pico %.1f, frac %.3f)' % (len(comps), len(ref), umbral_pico, umbral_frac))
    for c in comps[:15]:
        log('    comp %3d %.3f ha (%.0f, %.0f) frac2-5m %.3f pico %.1f cv %s rfS2silv %.2f' % (c['id'], c['area_ha'], c['x'], c['y'], c['frac_energia_2_5m'], c['pico_direccional'], c['cv_chm'], c['frac_rf_s2_silvicultura']))
    silv = np.zeros((H, W), bool)
    SILV = []
    for c in comps:
        es = c['frac_rf_s2_silvicultura'] >= 0.5 or (c['pico_direccional'] >= umbral_pico and c['frac_energia_2_5m'] >= umbral_frac and (c['cv_chm'] is None or c['cv_chm'] < 0.35))
        if es:
            silv |= c['mask']
            SILV.append({k: v for k, v in c.items() if k != 'mask'})
    cls[silv & np.isin(cls, [1, 2, 3, 9])] = 8
    log('  silvicultura: %d componentes, %.2f ha en el imovel (RF S2 10 m: %.2f ha)' % (len(SILV), (silv & m_prop).sum() * RES * RES / 1e4, (silv_rf10 & m_prop).sum() * RES * RES / 1e4))
    for c in comps:
        del c['mask']

escribir(R('vegetacao_ortofoto.tif', 0.5), cls, 0.5, dtype='uint8', nodata=0, bandas=['classe'],
         tags={'leyenda': json.dumps(NOMBRES), 'mmu': '25 m2', 'fecha': FECHA_VUELO})

# =====================================================================================
# 4. tablas por gleba, comparacion con RF S2, fragmentos
# =====================================================================================
RES_JSON = {'fecha_vuelo': FECHA_VUELO, 'res_m': RES, 'classes': NOMBRES, 'silvicultura_componentes': SILV,
            'silvicultura_metodo': 'espectro 2D del DSM (o luminancia) sin tendencia: energia en 2-5 m y pico direccional; referencia = componentes con RF S2 silvicultura >= 50 %; cv del CHM < 0,35',
            'rf_color_sem_chm': {'acc': round(acc, 3), 'concordancia_norte': round(concord, 3)}}
def tabla(mask):
    d = {}
    for k, nm in NOMBRES.items():
        d[nm] = round(((cls == k) & mask).sum() * RES * RES / 1e4, 3)
    d['sem_dado'] = round(((cls == 0) & mask).sum() * RES * RES / 1e4, 3)
    d['total_ha'] = round(mask.sum() * RES * RES / 1e4, 3)
    return d
por_gleba = {}
for g in ('G1', 'G2', 'IMOVEL'):
    m = m_prop if g == 'IMOVEL' else m_g[g]
    t = tabla(m)
    t['vegetacao_nativa_arborea_arbustiva_ha'] = round(t['arborea_altura_medida'] + t['arborea_dosel_fechado'] + t['arbustiva_regeneracao'] + t['arborea_arbustiva_sem_chm'], 3)
    t['arborea_ha'] = round(t['arborea_altura_medida'] + t['arborea_dosel_fechado'] + t['arborea_arbustiva_sem_chm'], 3)
    t['arbustiva_ha'] = t['arbustiva_regeneracao']
    # RF S2 10 m en la misma mascara
    t['rf_s2_10m'] = {nm: round(((rf10 == k) & m).sum() * RES * RES / 1e4, 3) for k, nm in RF_NOMBRES.items()}
    # cruce S2 floresta vs ortofoto
    fl = (rf10 == 1) & m
    t['s2_floresta_por_classe_orto_ha'] = {nm: round(((cls == k) & fl).sum() * RES * RES / 1e4, 3) for k, nm in NOMBRES.items()}
    nat = np.isin(cls, [1, 2, 3, 9]) & m
    t['orto_nativa_por_classe_s2_ha'] = {nm: round(((rf10 == k) & nat).sum() * RES * RES / 1e4, 3) for k, nm in RF_NOMBRES.items()}
    por_gleba[g] = t
    log('  %s: %s' % (g, {k: v for k, v in t.items() if not isinstance(v, dict)}))
RES_JSON['por_gleba'] = por_gleba

# fragmentos (RF S2) -> alturas medidas, cobertura, indicador de estagio
CONAMA = {'inicial': 'dossel ate 10 m', 'medio': 'dossel 8-17 m', 'avancado': 'dossel > 15 m (texto par. 3) / >= 30 (anexo)'}
def estagio_por_altura(p90, media):
    if p90 is None:
        return 'NAO MEDIVEL (sem CHM)'
    if p90 > 15:
        return 'indicador AVANCADO por altura (>15 m) - so indicador; DAP/area basal/estratos exigem campo'
    if p90 >= 8:
        return 'indicador MEDIO por altura (8-17 m) - so indicador; DAP/area basal/estratos exigem campo'
    return 'indicador INICIAL por altura (<= 10 m) - so indicador; DAP/area basal/estratos exigem campo'
frag = cargar('fragmentos')
FRAGS = []
for _, f in frag.iterrows():
    g = poly_only(f.geometry.intersection(GL['IMOVEL']))
    if g.is_empty:
        continue
    m = rasterizar([g], RES).astype(bool)
    d = {'frag_id': int(f.frag_id), 'area_poligono_s2_dentro_ha': ha(g), 'com_chm_pct': round(100 * (m & hay_chm).sum() / m.sum(), 1)}
    d.update({'orto_' + k: v for k, v in tabla(m).items() if k in ('arborea_altura_medida', 'arborea_dosel_fechado', 'arbustiva_regeneracao', 'herbacea_pasto', 'solo_cultivo', 'agua', 'silvicultura', 'arborea_arbustiva_sem_chm')})
    arbm = m & np.isin(cls, [1, 2, 9])
    d['cobertura_arborea_pct'] = round(100 * arbm.sum() / m.sum(), 1)
    medida = arbm & hay_chm & (fonte == 1) & (chm >= 1)
    d['altura_medida_pct_da_arborea'] = round(100 * medida.sum() / max(arbm.sum(), 1), 1)
    if medida.sum() > 100:
        v = chm[medida]
        d['altura_media_m'] = round(float(v.mean()), 1); d['altura_p50_m'] = round(float(np.percentile(v, 50)), 1); d['altura_p90_m'] = round(float(np.percentile(v, 90)), 1); d['altura_max_m'] = round(float(v.max()), 1)
    else:
        d['altura_media_m'] = d['altura_p50_m'] = d['altura_p90_m'] = None
    fech = arbm & (fonte == 2)
    if fech.sum() > 100:
        v = chm_h[fech]; v = v[np.isfinite(v)]
        d['dosel_fechado_pct_da_arborea'] = round(100 * fech.sum() / max(arbm.sum(), 1), 1)
        d['dosel_fechado_altura_indicador_p50_p90_m'] = [round(float(np.percentile(v, 50)), 1), round(float(np.percentile(v, 90)), 1)]
        d['dosel_fechado_nota'] = 'altura sobre a envolvente inferior do dossel (abertura 15 m): SUBESTIMA; a altura real do dossel fechado NAO foi medida'
    d['estagio_indicador_altura'] = estagio_por_altura(d['altura_p90_m'], d['altura_media_m'])
    d['conama_2_1994_parametros'] = CONAMA
    FRAGS.append(d)
    log('  fragmento %d: %s' % (d['frag_id'], {k: v for k, v in d.items() if k not in ('conama_2_1994_parametros',)}))
RES_JSON['fragmentos'] = FRAGS

# =====================================================================================
# 5. vectores de vegetacao nativa (arborea + arbustiva, sin silvicultura) por gleba / fragmento
# =====================================================================================
with Cronometro('vectores'):
    nat = np.isin(cls, [1, 2, 3, 9])
    gdf = vectorizar(nat, RES, min_area_m2=25)
    gdf['classe_dominante'] = ''
    gdf['gleba'] = ''
    gdf['frag_id_s2'] = None
    gdf['sem_chm'] = False
    fr_geoms = {int(f.frag_id): f.geometry for _, f in frag.iterrows()}
    rows = []
    for i, r in gdf.iterrows():
        gi = r.geometry
        m = rasterizar([gi], RES).astype(bool)
        vals, cnt = np.unique(cls[m], return_counts=True)
        dom = int(vals[np.argmax(cnt)]) if len(vals) else 0
        gl = 'G1' if gi.intersection(GL['G1']).area > gi.intersection(GL['G2']).area else ('G2' if gi.intersects(GL['G2']) else 'fora')
        fid = None
        for k, fg in fr_geoms.items():
            if gi.intersection(fg).area > 0.5 * gi.area:
                fid = k; break
        rows.append((NOMBRES.get(dom, ''), gl, fid, bool(dom == 9), round(ha(gi.intersection(GL['IMOVEL'])), 4)))
    gdf['classe_dominante'] = [x[0] for x in rows]; gdf['gleba'] = [x[1] for x in rows]; gdf['frag_id_s2'] = [x[2] for x in rows]
    gdf['sem_chm'] = [x[3] for x in rows]; gdf['area_dentro_imovel_ha'] = [x[4] for x in rows]
    gdf['fecha'] = FECHA_VUELO
    guardar_gdf(gdf, R('vegetacao_nativa_ortofoto.geojson'))
    RES_JSON['vegetacao_nativa_poligonos'] = {'n': int(len(gdf)), 'ha_dentro_imovel': round(float(gdf.area_dentro_imovel_ha.sum()), 3),
                                              'ha_dentro_imovel_componentes_ge_0_05ha': round(float(gdf[gdf.area_ha >= 0.05].area_dentro_imovel_ha.sum()), 3)}
    silv_gdf = vectorizar(cls == 8, RES, min_area_m2=25)
    if len(silv_gdf):
        guardar_gdf(silv_gdf, R('silvicultura_ortofoto.geojson'))
guardar_json(R('ortho_05_vegetacao.json'), RES_JSON)

with Cronometro('figura'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    cm = ListedColormap(['white', '#1b5e20', '#004d40', '#7cb342', '#c5e1a5', '#d7ccc8', '#1e88e5', '#e53935', '#8e24aa', '#33691e'])
    fig, ax = plt.subplots(1, 2, figsize=(12, 14))
    ext = [B[0], B[2], B[1], B[3]]
    ax[0].imshow(cls, cmap=cm, vmin=0, vmax=9, extent=ext, interpolation='nearest'); ax[0].set_title('clases ortofoto 0,5 m')
    ax[1].imshow(rf10, cmap=ListedColormap(['white', '#1b5e20', '#1e88e5', '#d7ccc8', '#8e24aa', '#c5e1a5']), vmin=0, vmax=5, extent=ext, interpolation='nearest'); ax[1].set_title('RF S2 10 m (29-ago-2026)')
    for a in ax:
        for g in ('G1', 'G2'):
            for p in (GL[g].geoms if hasattr(GL[g], 'geoms') else [GL[g]]):
                x, y = p.exterior.xy; a.plot(x, y, 'k-', lw=0.6)
        a.set_xticks([]); a.set_yticks([])
    plt.tight_layout(); plt.savefig(R('_check_ortho_05.png'), dpi=100); plt.close()
    log('  -> _check_ortho_05.png')
log('ortho_05 listo.')
