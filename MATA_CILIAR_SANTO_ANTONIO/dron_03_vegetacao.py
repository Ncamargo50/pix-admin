# -*- coding: utf-8 -*-
"""dron_03: cobertura vegetal POR INMUEBLE sobre lo recortado (0,25 m), SOLO con la ortofoto y el
DSM/DTM del dron. Clases (uint8):
  1 arborea, altura medida         (CHM >= 3 m)
  2 arborea, dossel fechado        (copa pelo classificador RGB+rugosidade DSM, CHM < 3 m: o DTM do drone nao
                                    penetrou o dossel; altura NAO medida)
  3 arbustiva / regeneracao        (1 <= CHM < 3 m, verde)
  4 herbacea / pasto               (verde, CHM < 1 m)
  5 solo / lavoura / restolho
  6 agua                           (dron_02)
  7 construcoes
  9 arborea (so cor)               (onde NAO ha DSM: so cor + textura, altura desconhecida)
  0 sem cobertura do drone         (nao avaliado)

Silvicultura: NAO se reclassifica; so se marca por componente o "indicio de fileiras regulares" (espectro 2D
do DSM/luminancia, energia em 2-5 m e pico direcional) para confirmar em campo.

Os dois classificadores (RF com DSM; RF so cor) se treinam no proprio imovel se ha copas medidas
(CHM >= 3 m); se nao (6 alqueires: CHM max 0,7 m; ponta norte), reusam o modelo treinado em
Santo Antonio (mesmo voo, mesma camera, mesma data).
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dron_00_comun import *   # noqa: F401,F403
import numpy as np
import geopandas as gpd
from scipy import ndimage as ndi
from shapely.ops import unary_union

cabecera('dron_03_vegetacao')
RES = 0.25
PX_HA = RES * RES / 1e4
NOMBRES = {0: 'sem_cobertura_drone', 1: 'arborea_altura_medida', 2: 'arborea_dossel_fechado', 3: 'arbustiva_regeneracao', 4: 'herbacea_pasto',
           5: 'solo_lavoura', 6: 'agua', 7: 'construcoes', 9: 'arborea_so_cor_sem_dsm'}
ARBOREA = [1, 2, 9]
NATIVA = [1, 2, 3, 9]
MODELOS = {}   # RF treinados em Santo Antonio, reusados
RUTA_MODELOS = os.path.join(SALIDA_RAIZ, 'santo_antonio', 'rf_modelos_dron_03.joblib')
RETRAIN = '--retrain' in sys.argv
SOLO = [a for a in sys.argv[1:] if not a.startswith('-')]


def entrenar(F2, pos, neg, n=60000, seed=0):
    from sklearn.ensemble import RandomForestClassifier
    rs = np.random.RandomState(seed)
    ip = np.flatnonzero(pos); im = np.flatnonzero(neg)
    ip = rs.choice(ip, min(n, len(ip)), replace=False); im = rs.choice(im, min(n, len(im)), replace=False)
    X = np.concatenate([F2[ip], F2[im]]); y = np.concatenate([np.ones(len(ip)), np.zeros(len(im))])
    perm = rs.permutation(len(y)); nv = len(y) // 5
    rf = RandomForestClassifier(n_estimators=100, min_samples_leaf=20, n_jobs=-1, random_state=seed).fit(X[perm[nv:]], y[perm[nv:]])
    acc = float((rf.predict(X[perm[:nv]]) == y[perm[:nv]]).mean())
    return rf, acc, int(len(ip)), int(len(im))


def predecir(rf, F2, idx, chunk=1500000):
    out = np.zeros(len(idx), 'float32')
    for i in range(0, len(idx), chunk):
        out[i:i + chunk] = rf.predict_proba(F2[idx[i:i + chunk]])[:, 1]
    return out


def sieve(cls, valido, min_px):
    from skimage.morphology import remove_small_objects
    out = cls.copy()
    for k in (1, 2, 3, 4, 5, 6, 7, 9):
        m = cls == k
        m2 = remove_small_objects(m, min_px)
        out[m & ~m2] = 0
    huecos = (out == 0) & valido
    if huecos.any() and (out > 0).any():
        # cada hueco toma la clase del pixel clasificado mas cercano (transformada de distancia)
        _, (ir, ic) = ndi.distance_transform_edt(out == 0, return_indices=True)
        out[huecos] = out[ir[huecos], ic[huecos]]
    return out


RESUMO = {}
for imovel in ORDEM_IMOVEIS + ([PONTA_NORTE] if PONTA_NORTE in imoveis() else []):
    if SOLO and imovel not in SOLO:
        continue
    es_ref = imovel == PONTA_NORTE
    log('\n' + '#' * 78)
    log('# %s  (%s, %.3f ha)' % (imovel, IMOVEIS[imovel]['nome'] if not es_ref else 'REFERENCIA: ponta norte removida (NAO e imovel)', area_ha(imovel)))
    log('#' * 78)
    IM = imoveis()[imovel]
    tr, H, W, B = grilla(imovel, RES)
    m_prop = mascara(imovel, RES)
    rgba, _ = leer(R(imovel, 'ortofoto_rgba.tif', RES), nan=False)
    valido = (rgba[3] > 0) & m_prop
    # MEDIDO 2026-09-06: o recorte exato deixa preto (0) fora do poligono e as texturas (TEX9/TEX21/DSMSTD) viram
    # "copa" num anel de ~1 m ao longo de todo o limite (0,22 ha nos 6 alqueires, ~0,7 ha em Santo Antonio).
    # Correcao: antes de calcular texturas, os pixels invalidos tomam o valor do pixel valido mais proximo.
    if (~valido).any() and valido.any():
        _, (ir, ic) = ndi.distance_transform_edt(~valido, return_indices=True)
        for i in range(3):
            rgba[i] = rgba[i][ir, ic]
    Rr, Gg, Bb, L, ExG, S, BR, TEX9 = rasgos_rgb(rgba)
    del rgba, BR
    TEX21 = std_local(L, 21)
    chm, _ = leer(R(imovel, 'chm.tif', RES)); chm = chm[0]
    dsm, _ = leer(R(imovel, 'dsm.tif', RES)); dsm = dsm[0]
    hay = np.isfinite(chm) & valido
    dsm_f = dsm.copy()
    if (~np.isfinite(dsm)).any() and np.isfinite(dsm).any():
        _, (ir, ic) = ndi.distance_transform_edt(~np.isfinite(dsm), return_indices=True)
        dsm_f = dsm[ir, ic]
    DSMSTD = std_local(np.where(np.isfinite(dsm_f), dsm_f, 0).astype('float32'), 9)
    DSMSTD = np.where(np.isfinite(dsm), DSMSTD, 0).astype('float32')
    del dsm_f
    for nombre, a in (('L', L), ('ExG', ExG), ('S', S), ('TEX9', TEX9)):
        verificar_arr(np.where(valido, a, np.nan), nombre, m_prop)
    verificar_arr(chm, 'chm', m_prop, 'm', permitir_vacia=True)
    J = {'imovel': imovel, 'fecha_voo': FECHA_VUELO, 'res_m': RES, 'classes': NOMBRES, 'fonte': 'somente ortofoto + DSM/DTM do drone (sem satelite)'}

    # --- agua (dron_02) ----------------------------------------------------------------------------------
    ruta_agua = R(imovel, 'agua_%s_%s.geojson' % (imovel, FECHA_VUELO))
    if os.path.exists(ruta_agua):
        agua = gpd.read_file(ruta_agua)
        agua = agua[agua.tipo == 'agua_aberta']
        m_agua = rasterizar(imovel, list(agua.geometry), RES).astype(bool) & valido
    else:
        m_agua = np.zeros((H, W), bool)
    log('  agua (dron_02): %.3f ha' % (m_agua.sum() * PX_HA))

    # --- clasificadores ----------------------------------------------------------------------------------
    with Cronometro('classificadores RF (com DSM / so cor)'):
        feats = np.stack([Rr, Gg, Bb, L, ExG, S, TEX9, TEX21, DSMSTD], -1)
        F2 = feats.reshape(-1, feats.shape[-1])
        del feats
        pos = hay & (chm >= 3.0) & (ExG > 5)
        neg_dsm = hay & (chm < 0.3) & (DSMSTD < 0.10)
        n_pos = int(pos.sum())
        if not MODELOS and os.path.exists(RUTA_MODELOS) and not RETRAIN:
            import joblib
            MODELOS.update(joblib.load(RUTA_MODELOS))
            log('  modelos RF cargados de %s (use --retrain para reentrenar)' % os.path.basename(RUTA_MODELOS))
        if n_pos >= 5000 and (imovel == 'santo_antonio' and (RETRAIN or 'dsm' not in MODELOS) or imovel != 'santo_antonio' and 'dsm' not in MODELOS):
            rf_dsm, acc_dsm, npos, nneg = entrenar(F2, pos, neg_dsm)
            rf_cor, acc_cor, _, _ = entrenar(F2[:, :8], pos, hay & (chm < 0.3), seed=1)
            MODELOS['dsm'] = rf_dsm; MODELOS['cor'] = rf_cor
            MODELOS['meta'] = {'treinado_em': imovel, 'acc_val_dsm': round(acc_dsm, 3), 'acc_val_cor': round(acc_cor, 3), 'n_pos': npos, 'n_neg': nneg,
                               'importancias_dsm': dict(zip(['R', 'G', 'B', 'L', 'ExG', 'S', 'TEX9', 'TEX21', 'DSMSTD'], np.round(rf_dsm.feature_importances_, 3).tolist()))}
            import joblib
            joblib.dump(MODELOS, RUTA_MODELOS)
            origem = 'treinado neste imovel (%d copas medidas CHM>=3 m / %d solo)' % (npos, nneg)
            J['rf'] = {'origem': origem} | MODELOS['meta']
        elif 'dsm' in MODELOS:
            rf_dsm, rf_cor = MODELOS['dsm'], MODELOS['cor']
            origem = ('modelo persistido (treinado em %s)' % MODELOS['meta']['treinado_em']) if imovel == MODELOS['meta']['treinado_em'] else                      'sem copas medidas neste imovel (%d px com CHM>=3 m): reusa o RF treinado em %s (mesmo voo)' % (n_pos, MODELOS['meta']['treinado_em'])
            J['rf'] = {'origem': origem} | MODELOS['meta']
        else:
            raise RuntimeError('%s: sem copas para treinar e sem modelo previo' % imovel)
        log('  RF: %s' % origem)
        # arboreo com DSM
        idx = np.flatnonzero(hay)
        prob_dsm = np.zeros((H, W), 'float32')
        if len(idx):
            prob_dsm.reshape(-1)[idx] = predecir(rf_dsm, F2, idx)
        arb = (prob_dsm > 0.5) & hay
        arb = ndi.binary_opening(arb, iterations=1); arb = ndi.binary_closing(arb, iterations=2)
        lab, n = ndi.label(arb)
        if n:
            tam = ndi.sum(arb, lab, np.arange(1, n + 1)) * RES * RES
            kp = np.zeros(n + 1, bool); kp[1:] = tam >= 25
            arb = kp[lab]
        # arboreo so cor onde nao ha DSM
        sin_dsm = valido & ~hay
        prob_cor = np.zeros((H, W), 'float32')
        idx2 = np.flatnonzero(sin_dsm)
        if len(idx2):
            prob_cor.reshape(-1)[idx2] = predecir(rf_cor, F2[:, :8], idx2)
        arb_sul = (prob_cor > 0.5) & sin_dsm
        arb_sul = ndi.binary_opening(arb_sul, iterations=1); arb_sul = ndi.binary_closing(arb_sul, iterations=2)
        # filtro por componente SEM satelite: compacto + textura de copas, ou apoiado no arboreo com DSM (<= 10 m)
        arb_dil = ndi.binary_dilation(arb, iterations=int(10 / RES)) if arb.any() else np.zeros((H, W), bool)
        lab_s, n_s = ndi.label(arb_sul)
        keep = np.zeros(n_s + 1, bool); desc_ha = 0.0; desc = []
        for k in range(1, n_s + 1):
            m = lab_s == k
            a_ha = m.sum() * PX_HA
            rows_, cols_ = np.where(m)
            hbb, wbb = int(np.ptp(rows_)) + 1, int(np.ptp(cols_)) + 1
            comp = m.sum() / float(hbb * wbb); elong = max(hbb, wbb) / max(min(hbb, wbb), 1)
            tex = float(TEX9[m].mean()); apoio = float(arb_dil[m].mean())
            L10 = float(np.percentile(L[m], 10)); exg = float(ExG[m].mean()); s_m = float(S[m].mean())
            d_lim = float(IM.exterior.distance(__import__('shapely').geometry.Point(tr.c + cols_.mean() * RES, tr.f + rows_.mean() * tr.e))) if hasattr(IM, 'exterior') else float(IM.boundary.distance(__import__('shapely').geometry.Point(tr.c + cols_.mean() * RES, tr.f + rows_.mean() * tr.e)))
            # largura maxima = 2 x raio maximo inscrito (transformada de distancia): separa a faixa estreita da rodovia (< 12 m)
            r0_, r1_, c0_, c1_ = rows_.min(), rows_.max() + 1, cols_.min(), cols_.max() + 1
            largura = 2.0 * float(ndi.distance_transform_edt(np.pad(m[r0_:r1_, c0_:c1_], 1)).max()) * RES
            if apoio >= 0.3 or (a_ha >= 0.05 and tex >= 12 and largura >= 12.0):
                keep[k] = True
            else:
                desc_ha += a_ha
            if a_ha >= 0.02:
                desc.append({'mantido': bool(keep[k]), 'area_ha': round(a_ha, 3), 'x': round(float(tr.c + cols_.mean() * RES), 1), 'y': round(float(tr.f + rows_.mean() * tr.e), 1), 'compacidade_bbox': round(comp, 2), 'elongacao_bbox': round(elong, 1), 'largura_max_m': round(largura, 1), 'tex': round(tex, 1), 'L_p10': round(L10, 1), 'ExG': round(exg, 1), 'S': round(s_m, 3), 'apoio_dsm': round(apoio, 2), 'dist_limite_m': round(d_lim, 1)})
                log('    comp sem DSM %s %.3f ha (%.0f, %.0f) largura %.1f m comp %.2f elong %.1f tex %.1f L10 %.0f ExG %.1f apoio %.2f dist_lim %.0f' % ('KEEP' if keep[k] else 'drop', a_ha, tr.c + cols_.mean() * RES, tr.f + rows_.mean() * tr.e, largura, comp, elong, tex, L10, exg, apoio, d_lim))
        arb_sul = keep[lab_s]
        J['rf']['sem_dsm'] = {'ha_sem_dsm_no_imovel': round(sin_dsm.sum() * PX_HA, 3), 'arboreo_so_cor_ha': round((arb_sul & m_prop).sum() * PX_HA, 3),
                              'descartado_por_forma_ha': round(desc_ha, 3), 'componentes_ge_0_02ha': desc[:60],
                              'regra': 'componente aceito se >= 30 % a <= 10 m do arboreo com DSM, ou se >= 0,05 ha, com textura de copas (TEX9 >= 12) e largura maxima >= 12 m (a faixa verde da rodovia do limite sul e estreita, < 12 m)'}
        log('  arboreo com DSM: %.3f ha; so cor (sem DSM): %.3f ha (descartado por forma %.3f ha)' % ((arb & m_prop).sum() * PX_HA, (arb_sul & m_prop).sum() * PX_HA, desc_ha))
        del F2, prob_dsm, prob_cor

    # --- clasificacion ----------------------------------------------------------------------------------------
    with Cronometro('classificacao'):
        cls = np.zeros((H, W), 'uint8')
        verde = ExG > 12
        techo = valido & (((L > 185) & (S < 0.35) & (TEX9 < 8)) | (hay & (chm >= 2.5) & (ExG < 5) & (S < 0.35)))
        techo = ndi.binary_opening(techo, iterations=2); techo = ndi.binary_closing(techo, iterations=2)
        lab, n = ndi.label(techo)
        if n:
            tam = ndi.sum(techo, lab, np.arange(1, n + 1)) * RES * RES
            kp = np.zeros(n + 1, bool); kp[1:] = tam >= 20
            techo = kp[lab]
        z = hay
        cls[z & ~verde] = 5
        cls[z & verde & (chm < 1)] = 4
        cls[z & verde & (chm >= 1) & (chm < 3)] = 3
        cls[z & arb & (chm >= 1) & (chm < 3)] = 3
        cls[z & arb & (chm < 1)] = 2
        cls[z & (chm >= 3) & (arb | verde)] = 1
        zs = sin_dsm
        cls[zs & ~verde] = 5
        cls[zs & verde] = 4
        cls[zs & arb_sul] = 9
        cls[techo & ~arb & ~arb_sul] = 7
        cls[m_agua] = 6
        cls[~valido] = 0
        cls = sieve(cls, valido, 400)   # MMU 25 m2 = 400 px de 0,25 m
        cls[~valido] = 0

    # --- indicio de silvicultura por componente (so marca) ---------------------------------------------------
    with Cronometro('indicio de fileiras (silvicultura) por componente'):
        lab, n = ndi.label(ndi.binary_closing(np.isin(cls, ARBOREA), iterations=2))
        SILV = []
        for k in range(1, n + 1):
            m = lab == k
            if m.sum() * RES * RES < 1000:
                continue
            rows, cols = np.where(m)
            r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
            sub_m = m[r0:r1, c0:c1]
            src = dsm if np.isfinite(dsm[m]).mean() > 0.5 else L
            a = np.where(sub_m & np.isfinite(src[r0:r1, c0:c1]), src[r0:r1, c0:c1], np.nan)
            a = a - np.nanmean(a); a = np.where(np.isfinite(a), a, 0)
            a = a - ndi.gaussian_filter(a, 40)
            Fp = np.abs(np.fft.fftshift(np.fft.fft2(a * sub_m))) ** 2
            fy = np.fft.fftshift(np.fft.fftfreq(a.shape[0], RES)); fx = np.fft.fftshift(np.fft.fftfreq(a.shape[1], RES))
            FX, FY = np.meshgrid(fx, fy); fr = np.hypot(FX, FY)
            banda = (fr >= 1 / 5.0) & (fr <= 1 / 2.0); resto = fr > 1 / 40.0
            e = float(Fp[banda].sum() / (Fp[resto].sum() + 1e-9)); pico = float(Fp[banda].max() / (Fp[banda].mean() + 1e-9))
            cv = float(np.nanstd(chm[m]) / (np.nanmean(chm[m]) + 1e-6)) if np.isfinite(chm[m]).any() else None
            ind = bool(pico >= 60 and e >= 0.35 and (cv is None or cv < 0.35))
            SILV.append({'id': k, 'area_ha': round(m.sum() * PX_HA, 3), 'x': round(float(tr.c + cols.mean() * RES), 1), 'y': round(float(tr.f + rows.mean() * tr.e), 1),
                         'frac_energia_2_5m': round(e, 3), 'pico_direcional': round(pico, 1), 'cv_chm': round(cv, 2) if cv is not None else None, 'indicio_fileiras': ind})
        J['silvicultura'] = {'componentes_ge_0_1ha': SILV, 'com_indicio': [c for c in SILV if c['indicio_fileiras']],
                             'regra': 'indicio se pico direcional >= 60 e energia 2-5 m >= 0,35 e cv(CHM) < 0,35 (limiares fixos; natural medido: pico 18-34, energia 0,08-0,28). Nao reclassifica: confirmar em campo.'}
        log('  componentes arboreos >= 0,1 ha: %d; com indicio de fileiras: %d' % (len(SILV), len(J['silvicultura']['com_indicio'])))

    escribir(imovel, R(imovel, 'vegetacao_%s.tif' % imovel, RES), cls, RES, dtype='uint8', nodata=0, bandas=['classe'],
             tags={'legenda': json.dumps(NOMBRES), 'mmu': '25 m2', 'fecha': FECHA_VUELO})

    # --- tabla por inmueble -----------------------------------------------------------------------------------------
    t = {NOMBRES[k]: round(((cls == k) & m_prop).sum() * PX_HA, 3) for k in NOMBRES}
    t['total_ha'] = round(m_prop.sum() * PX_HA, 3)
    t['arborea_ha'] = round(sum(t[NOMBRES[k]] for k in ARBOREA), 3)
    t['arbustiva_ha'] = t['arbustiva_regeneracao']
    t['vegetacao_nativa_arborea_arbustiva_ha'] = round(sum(t[NOMBRES[k]] for k in NATIVA), 3)
    t['pasto_ha'] = t['herbacea_pasto']; t['lavoura_solo_ha'] = t['solo_lavoura']; t['agua_ha'] = t['agua']
    soma = sum(t[NOMBRES[k]] for k in NOMBRES)
    t['fecha_soma_vs_area'] = round(soma - t['total_ha'], 3)
    assert abs(soma - t['total_ha']) < 0.02, (soma, t['total_ha'])
    J['tabela_ha'] = t
    log('  %s: %s' % (imovel, {k: v for k, v in t.items()}))

    # --- vectores: vegetacao nativa por componente (com alturas) e uso do solo dissolvido --------------------------------
    with Cronometro('vetores'):
        nat = np.isin(cls, NATIVA)
        gdf = vectorizar(imovel, nat, RES, min_area_m2=25)
        rows = []
        for i, r in gdf.iterrows():
            gi = r.geometry
            m = rasterizar(imovel, [gi], RES).astype(bool)
            vals, cnt = np.unique(cls[m], return_counts=True)
            dom = int(vals[np.argmax(cnt)]) if len(vals) else 0
            med = m & hay & (chm >= 1)
            d = {'classe_dominante': NOMBRES.get(dom, ''), 'sem_dsm': bool(dom == 9), 'area_dentro_imovel_ha': round(ha(gi.intersection(IM)), 4),
                 'pct_altura_medida': round(100.0 * med.sum() / max(m.sum(), 1), 1),
                 'altura_p50_m': round(float(np.percentile(chm[med], 50)), 1) if med.sum() > 50 else None,
                 'altura_p90_m': round(float(np.percentile(chm[med], 90)), 1) if med.sum() > 50 else None,
                 'altura_max_m': round(float(chm[med].max()), 1) if med.sum() > 50 else None,
                 'ha_por_classe': {NOMBRES[k]: round(((cls == k) & m).sum() * PX_HA, 4) for k in NATIVA if ((cls == k) & m).any()}}
            rows.append(d)
        for c in ('classe_dominante', 'sem_dsm', 'area_dentro_imovel_ha', 'pct_altura_medida', 'altura_p50_m', 'altura_p90_m', 'altura_max_m', 'ha_por_classe'):
            gdf[c] = [d[c] for d in rows]
        gdf['imovel'] = imovel; gdf['fecha'] = FECHA_VUELO
        guardar_gdf(gdf, R(imovel, 'vegetacao_nativa_%s.geojson' % imovel))
        J['vegetacao_nativa_poligonos'] = {'n': int(len(gdf)), 'ha_dentro_imovel': round(float(gdf.area_dentro_imovel_ha.sum()), 3) if len(gdf) else 0.0,
                                           'ha_componentes_ge_0_05ha': round(float(gdf[gdf.area_ha >= 0.05].area_dentro_imovel_ha.sum()), 3) if len(gdf) else 0.0,
                                           'ha_componentes_ge_0_5ha': round(float(gdf[gdf.area_ha >= 0.5].area_dentro_imovel_ha.sum()), 3) if len(gdf) else 0.0,
                                           'fragmentos_ge_0_5ha': [{k: v for k, v in d.items() if k != 'ha_por_classe'} | {'area_ha': float(a)} for d, a in zip(rows, gdf.area_ha) if a >= 0.5]}
        partes = []
        for k, nm in NOMBRES.items():
            if k == 0:
                continue
            g = vectorizar(imovel, cls == k, RES, min_area_m2=1.0, campos={'classe_id': k, 'classe': nm})
            if len(g):
                partes.append(g)
        if not valido.all() and (m_prop & ~valido).any():
            g = vectorizar(imovel, m_prop & ~valido, RES, min_area_m2=1.0, campos={'classe_id': 0, 'classe': NOMBRES[0]})
            partes.append(g)
        import pandas as pd
        uso = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=CRS_METRICO)
        uso = uso.dissolve(by='classe', aggfunc={'classe_id': 'first'}).reset_index()
        uso['area_ha'] = [ha(g.intersection(IM)) for g in uso.geometry]
        uso['imovel'] = imovel; uso['fecha'] = FECHA_VUELO
        guardar_gdf(uso, R(imovel, 'uso_solo_%s.geojson' % imovel))
        s_uso = float(uso.area_ha.sum())
        J['uso_solo_fecha'] = {'soma_ha': round(s_uso, 3), 'area_imovel_ha': area_ha(imovel), 'diferenca_ha': round(s_uso - area_ha(imovel), 3)}
        log('  uso do solo dissolvido: soma %.3f ha vs imovel %.3f (dif %.3f)' % (s_uso, area_ha(imovel), s_uso - area_ha(imovel)))
        assert abs(s_uso - area_ha(imovel)) < 0.02
    guardar_json(R(imovel, 'dron_03_vegetacao.json'), J)
    RESUMO[imovel] = t

    with Cronometro('figura'):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        cm = ListedColormap(['white', '#1b5e20', '#004d40', '#7cb342', '#c5e1a5', '#d7ccc8', '#1e88e5', '#e53935', '#ffffff', '#33691e'])
        rgba, _ = leer(R(imovel, 'ortofoto_rgba.tif', RES), nan=False)
        fig, ax = plt.subplots(1, 2, figsize=(10, 14))
        ext = [B[0], B[2], B[1], B[3]]
        ax[0].imshow(np.moveaxis(rgba[:3], 0, -1), extent=ext); ax[0].set_title('ortofoto %s' % FECHA_VUELO)
        ax[1].imshow(cls, cmap=cm, vmin=0, vmax=9, extent=ext, interpolation='nearest'); ax[1].set_title('classes 0,25 m %s' % imovel)
        for a in ax:
            for p in (IM.geoms if hasattr(IM, 'geoms') else [IM]):
                x, y = p.exterior.xy; a.plot(x, y, 'k-', lw=0.6)
            a.set_xticks([]); a.set_yticks([])
        plt.tight_layout(); plt.savefig(R(imovel, '_check_dron_03.png'), dpi=90); plt.close()
        log('  -> _check_dron_03.png')
    del Rr, Gg, Bb, L, ExG, S, TEX9, TEX21, chm, dsm, DSMSTD, cls

guardar_json(os.path.join(SALIDA_RAIZ, 'dron_03_resumo_vegetacao.json'), RESUMO)
log('dron_03 listo.')
