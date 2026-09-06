# -*- coding: utf-8 -*-
"""an_02_vegetacion.py — vegetacion nativa a 10 m (S2 2026-08-29, Random Forest).

1. Features por pixel: 10 reflectancias S2 + 6 indices + GLCM 5x5 sobre NDVI 8-bit
   (contraste, homogeneidad) + HAND (30 m -> 10 m bilineal). SCL invalida excluida.
2. Etiquetas por CONSENSO de MapBiomas col11 2025 (10 m nearest), Dynamic World
   (moda 12 m) y ESA WorldCover 2021, erosionadas 1 px; <= 5000 px por clase.
3. RF 300 arboles balanceado; validacion GroupKFold 5 por bloques de 500 m.
   Post-proceso: moda 3x3 + MMU 0,05 ha en floresta. Raster + vector.
4. Cambio 2008 -> 2025 (MapBiomas 30 m) dentro de la propiedad + Hansen lossyear.
5. ha por clase dentro de la propiedad: RF vs MB vs DW vs WC vs FBDS 2013 + incertidumbre.
6. Fragmentos de floresta >= 0,5 ha: indicadores DESCRIPTIVOS (estagio requer campo).

Nota sobre "12 bandas": el GeoTIFF trae 10 reflectancias + SCL + cs_cdf. SCL es
una clasificacion (fuga de etiqueta) y cs_cdf una probabilidad de nube: no entran
como predictores.
"""
import os
import time

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import ndimage as ndi
from shapely.ops import unary_union
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import confusion_matrix, f1_score, accuracy_score, cohen_kappa_score

from an_00_config import *  # noqa: F401,F403

T0 = time.time()
titulo('an_02_vegetacion — vegetacion nativa a 10 m  (%s)' % FECHA_ESCENA)
rng = np.random.default_rng(P['semilla'])
prop = propiedad()
PROP = prop['geom']
RES = {'fecha_escena': FECHA_ESCENA}

# ==============================================================================
# 1. Features
# ==============================================================================
titulo('1. Features por pixel de 10 m')
s2, prof10 = leer_raster(R['s2'])
idx, _ = leer_raster(R['indices'])
scl = s2['SCL'].astype(np.uint8)
valido = ~np.isin(scl, list(SCL_INVALIDA))
REFL = ['B2', 'B3', 'B4', 'B8', 'B5', 'B6', 'B7', 'B8A', 'B11', 'B12']
IND = ['NDVI', 'NDWI', 'MNDWI', 'NDMI', 'AWEInsh', 'NDRE']
for b in REFL:
    valido &= np.isfinite(s2[b])
    verificar_rango(b, np.where(valido, s2[b], np.nan), 0, 1.2)
for b in IND:
    valido &= np.isfinite(idx[b])
    verificar_rango(b, np.where(valido, idx[b], np.nan), -5, 5)
log('  pixeles validos (SCL fuera de %s): %d de %d (%.2f%%)'
    % (sorted(SCL_INVALIDA), int(valido.sum()), valido.size, 100 * valido.mean()))
log('  SCL en el AOI: %s' % dict(zip(*[a.tolist() for a in np.unique(scl, return_counts=True)])))


def glcm_5x5(img, niveles=256):
    """Contraste y homogeneidad de la GLCM simetrica 5x5 (Haralick 1973) calculadas
    de forma exacta sobre los pares de vecinos (4 direcciones, distancia 1):
      contraste    = media_pares (i-j)^2
      homogeneidad = media_pares 1/(1+(i-j)^2)
    img: float en [-1,1] -> cuantizado a `niveles` (8 bits)."""
    q = np.clip(np.round((np.nan_to_num(img, nan=-1) + 1) / 2 * (niveles - 1)), 0, niveles - 1).astype(np.float32)
    con = np.zeros_like(q); hom = np.zeros_like(q)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        sh = np.roll(np.roll(q, dy, axis=0), dx, axis=1)
        d2 = (q - sh) ** 2
        con += ndi.uniform_filter(d2, 5, mode='reflect')
        hom += ndi.uniform_filter(1.0 / (1.0 + d2), 5, mode='reflect')
    return con / 4.0, hom / 4.0


glcm_con, glcm_hom = glcm_5x5(idx['NDVI'])
verificar_rango('GLCM contraste', np.where(valido, glcm_con, np.nan), 0)
verificar_rango('GLCM homogeneidad', np.where(valido, glcm_hom, np.nan), 0, 1)
hand10 = remuestrear_a(os.path.join(ANALISIS, 'HAND_30m.tif'), prof10, banda=1, metodo='bilinear')
hand10 = np.where(np.isfinite(hand10) & (hand10 >= 0), hand10, np.nanmax(np.where(hand10 >= 0, hand10, np.nan)))
verificar_rango('HAND 10 m', hand10, 0, 300)

FEATS = REFL + IND + ['GLCM_con', 'GLCM_hom', 'HAND']
X_all = np.stack([s2[b] for b in REFL] + [idx[b] for b in IND] + [glcm_con, glcm_hom, hand10], axis=-1).astype(np.float32)
H, W = valido.shape
log('  matriz de features: %s (%d variables)' % (X_all.shape, len(FEATS)))

# ==============================================================================
# 2. Etiquetas por consenso
# ==============================================================================
titulo('2. Etiquetas por consenso MapBiomas 2025 x Dynamic World x WorldCover 2021')
mb10, _ = leer_raster(R['mb_10m']); mb10 = mb10['classification_2025']
dw, _ = leer_raster(R['dw']); dw_lab, dw_n = dw['label_moda'], dw['n_obs']
wc, _ = leer_raster(R['wc']); wc = wc['Map']
for nombre, a, ley in (('MapBiomas 2025', mb10, MB), ('DynamicWorld', dw_lab, DW), ('WorldCover', wc, WC)):
    u, c = np.unique(a[valido], return_counts=True)
    log('  %-15s %s' % (nombre, {ley.get(int(k), int(k)): int(v) for k, v in zip(u, c)}))

cons = {
    1: np.isin(mb10, list(MB_FLORESTA)) & (dw_lab == 1) & (wc == 10),
    2: np.isin(mb10, list(MB_AGUA)) & (dw_lab == 0) & (wc == 80),
    3: np.isin(mb10, list(MB_ANTROPIZADO)) & np.isin(dw_lab, [2, 4, 6, 7]) & np.isin(wc, [30, 40, 50, 60]),
    4: np.isin(mb10, list(MB_SILVICULTURA)) & (dw_lab == 1),
    5: np.isin(mb10, list(MB_HERBACEO_NATIVO)) & np.isin(dw_lab, [2, 3]),
}
consenso_any = np.zeros_like(valido)
clases_usadas = {}
for c, m in cons.items():
    m &= valido
    consenso_any |= m
    n_bruto = int(m.sum())
    m_er = ndi.binary_erosion(m, structure=np.ones((3, 3)))
    n_er = int(m_er.sum())
    ok = n_er >= P['min_px_clase']
    log('  %-26s consenso %6d px, erosionado 1 px %6d px -> %s' % (CLASES_RF[c], n_bruto, n_er, 'USADA' if ok else 'OMITIDA (<%d px)' % P['min_px_clase']))
    if ok:
        clases_usadas[c] = m_er
if 4 not in clases_usadas:
    log('  !! No hay silvicultura suficiente en el AOI (MB 9 & DW trees < %d px): sin clase SILVICULTURA' % P['min_px_clase'])
if 5 not in clases_usadas:
    log('  !! Sin clase de vegetacao herbacea nativa (MB 11/12 & DW grass/flooded < %d px)' % P['min_px_clase'])
# consenso: cobertura del AOI etiquetada
etiq_total = sum(int(m.sum()) for m in clases_usadas.values())
log('  pixeles etiquetados (consenso) = %d = %.1f%% del AOI valido' % (etiq_total, 100 * etiq_total / valido.sum()))

# bloques espaciales de 500 m
rows, cols = np.indices((H, W))
T = prof10['transform']
xs = T.c + (cols + 0.5) * T.a
ys = T.f + (rows + 0.5) * T.e
bloque = (np.floor(xs / P['bloque_cv_m']).astype(int) * 100000 + np.floor(ys / P['bloque_cv_m']).astype(int))

Xs, ys_, gs = [], [], []
for c, m in clases_usadas.items():
    ii = np.flatnonzero(m.ravel())
    # muestreo estratificado por bloque: cuota proporcional por bloque, hasta max_muestras_clase
    if len(ii) > P['max_muestras_clase']:
        bl = bloque.ravel()[ii]
        ub, inv = np.unique(bl, return_inverse=True)
        cuota = np.maximum(1, np.round(np.bincount(inv) / len(ii) * P['max_muestras_clase'])).astype(int)
        sel = []
        for b_i in range(len(ub)):
            cand = ii[inv == b_i]
            sel.extend(rng.choice(cand, size=min(cuota[b_i], len(cand)), replace=False).tolist())
        ii = np.array(sel)
    Xs.append(X_all.reshape(-1, len(FEATS))[ii]); ys_.append(np.full(len(ii), c)); gs.append(bloque.ravel()[ii])
    log('  clase %-26s muestras %5d en %3d bloques' % (CLASES_RF[c], len(ii), len(np.unique(bloque.ravel()[ii]))))
X = np.vstack(Xs); y = np.concatenate(ys_); g = np.concatenate(gs)

# ==============================================================================
# 3. Random Forest + validacion espacial
# ==============================================================================
titulo('3. Random Forest (%d arboles, balanced) — GroupKFold 5 por bloques de %d m' % (P['rf_arboles'], P['bloque_cv_m']))
labels = sorted(clases_usadas)
nombres = [CLASES_RF[c] for c in labels]
gkf = GroupKFold(n_splits=5)
y_pred_cv = np.zeros_like(y)
for k, (tr, te) in enumerate(gkf.split(X, y, g)):
    rf = RandomForestClassifier(n_estimators=P['rf_arboles'], class_weight='balanced', n_jobs=-1,
                                random_state=P['semilla'], max_features='sqrt')
    rf.fit(X[tr], y[tr])
    y_pred_cv[te] = rf.predict(X[te])
    log('  fold %d: train %d / test %d bloques-test %d  OA %.3f' % (k + 1, len(tr), len(te), len(np.unique(g[te])), accuracy_score(y[te], y_pred_cv[te])))
cm = confusion_matrix(y, y_pred_cv, labels=labels)
oa = accuracy_score(y, y_pred_cv)
f1 = f1_score(y, y_pred_cv, labels=labels, average=None)
kappa = cohen_kappa_score(y, y_pred_cv)
log('  Matriz de confusion (filas = referencia, columnas = prediccion):')
log('  %-26s ' % '' + ' '.join('%8s' % n[:8] for n in nombres))
for i, n in enumerate(nombres):
    log('  %-26s ' % n + ' '.join('%8d' % v for v in cm[i]))
log('  OA (CV espacial) = %.4f   kappa = %.4f' % (oa, kappa))
for n, f in zip(nombres, f1):
    log('  F1 %-26s = %.4f' % (n, f))
# modelo final
rf = RandomForestClassifier(n_estimators=P['rf_arboles'], class_weight='balanced', n_jobs=-1,
                            random_state=P['semilla'], max_features='sqrt', oob_score=True)
rf.fit(X, y)
imp = sorted(zip(FEATS, rf.feature_importances_), key=lambda t: -t[1])
log('  OOB score (no espacial, optimista) = %.4f' % rf.oob_score_)
log('  importancias top-10: ' + ', '.join('%s %.3f' % (f, v) for f, v in imp[:10]))
prod_acc = (np.diag(cm) / np.maximum(cm.sum(axis=1), 1)).round(4)
user_acc = (np.diag(cm) / np.maximum(cm.sum(axis=0), 1)).round(4)
RES['rf'] = {'n_arboles': P['rf_arboles'], 'class_weight': 'balanced', 'max_features': 'sqrt',
             'validacion': 'GroupKFold 5, bloques %d m' % P['bloque_cv_m'], 'n_muestras': int(len(y)),
             'muestras_por_clase': {CLASES_RF[c]: int((y == c).sum()) for c in labels},
             'clases': nombres, 'matriz_confusion': cm.tolist(), 'OA': round(float(oa), 4), 'kappa': round(float(kappa), 4),
             'F1': {n: round(float(f), 4) for n, f in zip(nombres, f1)},
             'productor_acc': dict(zip(nombres, prod_acc.tolist())), 'usuario_acc': dict(zip(nombres, user_acc.tolist())),
             'oob_score': round(float(rf.oob_score_), 4), 'importancias_top10': [(f, round(float(v), 4)) for f, v in imp[:10]],
             'features': FEATS, 'clases_omitidas': [CLASES_RF[c] for c in CLASES_RF if c not in clases_usadas],
             'aviso': 'etiquetas = consenso de 3 productos globales (no verdad de campo); OA mide acuerdo con ese consenso'}

# prediccion del AOI
Xv = X_all.reshape(-1, len(FEATS))[valido.ravel()]
proba = rf.predict_proba(Xv)
pred = np.zeros(H * W, dtype=np.uint8)
pred[valido.ravel()] = np.array(rf.classes_)[proba.argmax(axis=1)]
pred = pred.reshape(H, W)
prob_fl = np.full(H * W, np.nan, dtype=np.float32)
if 1 in rf.classes_:
    prob_fl[valido.ravel()] = proba[:, list(rf.classes_).index(1)]
prob_fl = prob_fl.reshape(H, W)


def filtro_moda(a, clases, valido):
    """Moda 3x3 por conteo de clase (rapido, sin generic_filter)."""
    counts = np.stack([ndi.uniform_filter((a == c).astype(np.float32), 3, mode='nearest') for c in clases])
    out = np.array(clases, dtype=np.uint8)[counts.argmax(axis=0)]
    return np.where(valido, out, 0).astype(np.uint8)


pred_pp = filtro_moda(pred, labels, valido)
# MMU en floresta: parches < 5 px pasan a la 2a clase mas probable
mmu_px = int(round(P['mmu_floresta_ha'] * 1e4 / P['pixel_s2_m'] ** 2))
lab, n = ndi.label(pred_pp == 1, structure=np.ones((3, 3)))
tam = ndi.sum(pred_pp == 1, lab, index=np.arange(1, n + 1))
chicos = np.isin(lab, np.arange(1, n + 1)[tam < mmu_px])
if chicos.any() and 1 in rf.classes_:
    pr = np.full((H * W, len(rf.classes_)), np.nan, dtype=np.float32); pr[valido.ravel()] = proba
    pr = pr.reshape(H, W, -1)
    pr[..., list(rf.classes_).index(1)] = -1
    pred_pp[chicos] = np.array(rf.classes_)[pr[chicos].argmax(axis=1)]
log('  post-proceso: moda 3x3; %d parches de floresta < %d px reasignados (MMU %.2f ha)' % (int((tam < mmu_px).sum()), mmu_px, P['mmu_floresta_ha']))
u, c = np.unique(pred_pp[valido], return_counts=True)
log('  clases predichas en el AOI: %s' % {CLASES_RF[int(k)]: '%.1f ha' % (v / 100) for k, v in zip(u, c)})
tags = {'clases': ';'.join('%d=%s' % (k, v) for k, v in CLASES_RF.items() if k in clases_usadas), 'nodata': '0 = SCL invalida',
        'escena': ESCENA_ID, 'modelo': 'RF %d arboles, OA CV espacial %.3f' % (P['rf_arboles'], oa),
        'postproceso': 'moda 3x3 + MMU %d px floresta' % mmu_px}
guardar_raster(os.path.join(ANALISIS, 'vegetacao_10m_%s.tif' % FECHA_ESCENA), pred_pp, prof10, nodata=0, tags=tags, descripciones=['classe'])
guardar_raster(os.path.join(ANALISIS, 'prob_floresta_nativa_10m.tif'), np.nan_to_num(prob_fl, nan=-1).astype(np.float32), prof10, nodata=-1,
               tags={'nota': 'probabilidad RF de FLORESTA_NATIVA'}, descripciones=['p_floresta'])
guardar_raster(os.path.join(ANALISIS, 'glcm_ndvi_5x5_10m.tif'), np.stack([glcm_con, glcm_hom]).astype(np.float32), prof10, nodata=None,
               descripciones=['contraste', 'homogeneidade'])

veg = vectorizar(pred_pp, prof10, 'classe_id')
veg['classe'] = veg['classe_id'].map(CLASES_RF)
veg['area_ha'] = (veg.geometry.area / 1e4).round(4)
veg['area_dentro_propriedade_ha'] = (veg.geometry.intersection(PROP).area / 1e4).round(4)
veg['intersecta_propriedade'] = veg['area_dentro_propriedade_ha'] > 0
guardar_vector(veg, 'vegetacao_nativa_10m')

# ==============================================================================
# 4. Cambio 2008 -> 2025 (MapBiomas 30 m) + Hansen
# ==============================================================================
titulo('4. Cambio MapBiomas 2008 -> 2025 dentro de la propiedad; Hansen lossyear')
mbh, prof30 = leer_raster(R['mb_hist'])
m25, m08, m85 = mbh['classification_2025'], mbh['classification_2008'], mbh['classification_1985']
fl25, fl08, fl85 = np.isin(m25, list(MB_FLORESTA)), np.isin(m08, list(MB_FLORESTA)), np.isin(m85, list(MB_FLORESTA))
ag25, ag08 = np.isin(m25, list(MB_AGUA)), np.isin(m08, list(MB_AGUA))
cambio = np.zeros(m25.shape, dtype=np.uint8)
cambio[fl08 & fl25] = 1          # floresta estavel
cambio[fl08 & ~fl25] = 2         # supressao pos-2008 (NAO consolidavel)
cambio[~fl08 & fl25] = 3         # regeneracao
cambio[~fl08 & ~fl25 & ~ag08 & ~ag25] = 4   # antropico estavel
cambio[ag25 | ag08] = 5          # agua (2008 ou 2025)
NOM_CAMBIO = {1: 'floresta_estavel_2008_2025', 2: 'supressao_pos_2008', 3: 'regeneracao_pos_2008', 4: 'antropico_estavel', 5: 'agua'}
cam_v = vectorizar(cambio, prof30, 'cambio_id')
cam_v['classe'] = cam_v['cambio_id'].map(NOM_CAMBIO)
cam_v['geometry'] = cam_v.geometry.intersection(PROP)
cam_v = cam_v[~cam_v.geometry.is_empty].explode(index_parts=False).reset_index(drop=True)
cam_v['area_ha'] = (cam_v.geometry.area / 1e4).round(4)
cam_v['mb_2025'] = None
cam_v['mb_2008'] = None
tab_cambio = cam_v.groupby('classe')['area_ha'].sum().round(2).to_dict()
log('  cambio 2008->2025 dentro de la propiedad (ha): %s   suma %.2f' % (tab_cambio, sum(tab_cambio.values())))
# Hansen
hs, _ = leer_raster(R['hansen'])
loss = hs['lossyear']; tc2000 = hs['treecover2000']; gain = hs['gain']
prop30 = rasterizar([PROP], prof30) > 0
prop30_100 = rasterizar([PROP.buffer(100)], prof30) > 0
han = {}
for nombre, m in (('dentro', prop30), ('prop_100m', prop30_100)):
    u, c = np.unique(loss[m & (loss > 0)], return_counts=True)
    han[nombre] = {'ha_perda_por_ano': {2000 + int(k): round(float(v) * 0.09, 2) for k, v in zip(u, c)},
                   'ha_perda_total_2001_2025': round(float((loss[m] > 0).sum()) * 0.09, 2),
                   'ha_perda_pos_2008': round(float(((loss[m] > 8)).sum()) * 0.09, 2),
                   'ha_treecover2000_gt30': round(float((tc2000[m] > 30).sum()) * 0.09, 2),
                   'ha_gain_2000_2012': round(float((gain[m] > 0).sum()) * 0.09, 2)}
    log('  Hansen %-10s perda total %.2f ha (pos-2008: %.2f ha); por ano %s' % (nombre, han[nombre]['ha_perda_total_2001_2025'], han[nombre]['ha_perda_pos_2008'], han[nombre]['ha_perda_por_ano']))
# supressao pos-2008 cruzada con Hansen loss > 2008
sup = cam_v[cam_v.classe == 'supressao_pos_2008']
loss_pos08 = vectorizar(((loss > 8) & prop30).astype(np.uint8), prof30, 'loss')
LOSS08 = unary_union(list(loss_pos08.geometry)) if len(loss_pos08) else None
sup_han = sup.geometry.intersection(LOSS08).area.sum() / 1e4 if LOSS08 is not None and len(sup) else 0.0
log('  supressao pos-2008 (MB) confirmada por Hansen loss>2008: %.2f de %.2f ha' % (sup_han, sup['area_ha'].sum()))
# "supressao" MapBiomas 30 m que em 2026 e floresta no RF 10 m e sem perda Hansen = artefato de borda (30 m vs 10 m),
# nao supressao. Confirmada = parte que NAO e floresta RF 2026 e/ou tem Hansen loss > 2008.
SUP_U = unary_union(list(sup.geometry)) if len(sup) else None
FL_RF = unary_union(list(veg[veg.classe == 'FLORESTA_NATIVA'].geometry)) if (veg.classe == 'FLORESTA_NATIVA').any() else None
sup_fl_rf = (SUP_U.intersection(FL_RF).area / 1e4) if (SUP_U is not None and FL_RF is not None) else 0.0
sup_conf_g = None
if SUP_U is not None:
    sup_conf_g = SUP_U.difference(FL_RF) if FL_RF is not None else SUP_U
    if LOSS08 is not None:
        sup_conf_g = unary_union([sup_conf_g, SUP_U.intersection(LOSS08)])
sup_conf = sup_conf_g.area / 1e4 if sup_conf_g is not None else 0.0
log('  supressao pos-2008 bruta %.2f ha: %.2f ha sao floresta RF em 2026 (artefato MapBiomas 30 m); CONFIRMADA (nao floresta RF 2026 e/ou Hansen loss) %.2f ha'
    % (sup['area_ha'].sum(), sup_fl_rf, sup_conf))
cam_v['nota'] = cam_v['classe'].map({'supressao_pos_2008': 'floresta em 2008 e nao-floresta em 2025 (MapBiomas 30 m): NAO consolidavel, verificar',
                                    'regeneracao_pos_2008': 'nao-floresta em 2008 e floresta em 2025', 'floresta_estavel_2008_2025': 'floresta em ambas as datas',
                                    'antropico_estavel': 'uso antropico em ambas as datas', 'agua': 'agua em 2008 ou 2025'})
guardar_vector(cam_v.drop(columns=['mb_2025', 'mb_2008']), 'mudanca_2008_2025')
RES['mudanca_2008_2025'] = {'fonte': 'MapBiomas col11 30 m; corte legal 22/07/2008', 'ha_por_classe': tab_cambio,
                           'supressao_pos_2008_confirmada_hansen_ha': round(float(sup_han), 2),
                           'supressao_pos2008_bruta_ha': round(float(sup['area_ha'].sum()), 2),
                           'supressao_pos2008_floresta_rf_2026_ha': round(float(sup_fl_rf), 2),
                           'supressao_pos2008_confirmada_ha': round(float(sup_conf), 2),
                           'nota_supressao': 'bruta = MapBiomas 30 m floresta 2008 / nao-floresta 2025; a parte que e floresta RF 10 m em 2026 e sem Hansen loss e '
                                             'artefato de borda (indicio nao confirmado); confirmada = nao floresta RF 2026 e/ou Hansen loss > 2008',
                           'hansen': han}

# ==============================================================================
# 5. ha por clase dentro de la propiedad: RF vs MB vs DW vs WC vs FBDS 2013
# ==============================================================================
titulo('5. Cobertura dentro de la propiedad por fuente')
prop10 = rasterizar([PROP], prof10) > 0
n_prop10 = int(prop10.sum())
log('  propiedad en el grid de 10 m: %d px = %.2f ha (vector %.2f ha)' % (n_prop10, n_prop10 / 100, prop['area_ha']))


def tabla_px(a, ley, m=prop10):
    u, c = np.unique(a[m], return_counts=True)
    return {str(ley.get(int(k), int(k))): round(float(v) / 100, 2) for k, v in zip(u, c)}


comp = {'RF_10m': tabla_px(pred_pp, {**CLASES_RF, 0: 'sem_dado'}),
        'MapBiomas_2025_10m': tabla_px(mb10, MB), 'DynamicWorld_moda12m': tabla_px(dw_lab, DW),
        'WorldCover_2021': tabla_px(wc, WC)}
mb30 = rasterizar([PROP], prof30) > 0
comp['MapBiomas_2025_30m'] = {str(MB.get(int(k), int(k))): round(float(v) * 0.09, 2) for k, v in zip(*np.unique(m25[mb30], return_counts=True))}
uso13 = leer_vector('fbds_uso2013', PROP)
uso13['classe'] = uso13['classe_uso'].map(sin_acentos)
comp['FBDS_uso_2013'] = uso13.assign(a=uso13.geometry.area / 1e4).groupby('classe')['a'].sum().round(2).to_dict()
for k, v in comp.items():
    log('  %-22s %s' % (k, v))
# incertidumbre floresta: perimetro x 10 m / 2
fl_prop = veg[veg.classe == 'FLORESTA_NATIVA'].geometry.intersection(PROP)
fl_prop = fl_prop[~fl_prop.is_empty]
fl_u = unary_union(list(fl_prop))
per = fl_u.length
a_fl = fl_u.area / 1e4
banda = per * P['pixel_s2_m'] / 2 / 1e4
log('  floresta RF dentro: %.2f ha; perimetro %.0f m; banda +-%.2f ha  => [%.2f ; %.2f]' % (a_fl, per, banda, a_fl - banda, a_fl + banda))
# exatidao medida SO sobre pixeles de consenso: a floresta RF fora do consenso nao tem exatidao medida
fl_prop_px = (pred_pp == 1) & prop10
sem_cons = fl_prop_px & ~consenso_any
n_sem_cons_prop = int((prop10 & ~consenso_any & valido).sum())
p_sem = float(np.nanmean(prob_fl[sem_cons])) if sem_cons.any() else float('nan')
p_com = float(np.nanmean(prob_fl[fl_prop_px & consenso_any])) if (fl_prop_px & consenso_any).any() else float('nan')
log('  imovel: %.2f ha sem consenso dos 3 produtos (%.0f%%); floresta RF fora do consenso %.2f de %.2f ha (p_floresta media %.2f vs %.2f no consenso)'
    % (n_sem_cons_prop / 100, 100 * n_sem_cons_prop / max(n_prop10, 1), sem_cons.sum() / 100, fl_prop_px.sum() / 100, p_sem, p_com))
RES['rf']['ha_propriedade_sem_consenso'] = round(n_sem_cons_prop / 100, 2)
RES['rf']['pct_propriedade_sem_consenso'] = round(100 * n_sem_cons_prop / max(n_prop10, 1), 1)
RES['rf']['floresta_ha_sem_consenso'] = round(float(sem_cons.sum()) / 100, 2)
RES['rf']['floresta_ha_total_propriedade'] = round(float(fl_prop_px.sum()) / 100, 2)
RES['rf']['prob_floresta_media_sem_consenso'] = round(p_sem, 3)
RES['rf']['prob_floresta_media_com_consenso'] = round(p_com, 3)
RES['rf']['aviso_exatidao'] = ('OA/F1 medidos SO sobre pixeles onde MapBiomas, Dynamic World e WorldCover concordam; %.2f das %.2f ha de floresta do imovel '
                               'estao fora desse consenso (faixa ciliar norte + bordas) e NAO tem exatidao medida (p_floresta media %.2f)'
                               % (sem_cons.sum() / 100, fl_prop_px.sum() / 100, p_sem))
RES['cobertura_propriedade'] = {'por_fonte_ha': comp, 'floresta_rf_ha': round(a_fl, 2), 'floresta_perimetro_m': round(per),
                                'floresta_incerteza_ha': round(banda, 2), 'floresta_min_ha': round(a_fl - banda, 2), 'floresta_max_ha': round(a_fl + banda, 2),
                                'nota': 'incerteza = perimetro x 10 m / 2 (1 px de borda); inclui borda com o limite do imovel (conservador)'}

# ==============================================================================
# 6. Fragmentos de floresta >= 0,5 ha — indicadores descriptivos
# ==============================================================================
titulo('6. Fragmentos de floresta >= %.1f ha (indicativo, requer campo)' % P['fragmento_min_ha'])
lab, n = ndi.label(pred_pp == 1, structure=np.ones((3, 3)))
frag_v = vectorizar(lab.astype(np.int32), prof10, 'frag_id')
frag_v = frag_v.dissolve(by='frag_id', as_index=False)
frag_v['area_ha'] = (frag_v.geometry.area / 1e4).round(3)
frag_v['area_dentro_propriedade_ha'] = (frag_v.geometry.intersection(PROP).area / 1e4).round(3)
frag_v = frag_v[(frag_v.area_ha >= P['fragmento_min_ha']) & (frag_v.area_dentro_propriedade_ha > 0)].copy()
mb85_10 = remuestrear_a(R['mb_hist'], prof10, banda=3, metodo='nearest')
mb08_10 = remuestrear_a(R['mb_hist'], prof10, banda=2, metodo='nearest')
# referencias espectrais no AOI (mesma cena): pastagem = MB 15 & DW grass; cafe = MB 46; cultivo verde = MB 39/41 & NDVI > 0,6
b11 = s2['B11']
m_past = valido & (mb10 == 15) & (dw_lab == 2)
m_cafe = valido & (mb10 == 46)
m_cult = valido & np.isin(mb10, [39, 41]) & (idx['NDVI'] > 0.6)
REF = {}
for nome, mm in (('pastagem', m_past), ('cafe', m_cafe), ('cultivo_verde', m_cult)):
    if mm.sum() >= 30:
        REF[nome] = {'n_px': int(mm.sum()), 'b11_media': round(float(np.nanmean(b11[mm])), 3), 'b11_sd': round(float(np.nanstd(b11[mm])), 3),
                     'b11_p5': round(float(np.nanpercentile(b11[mm], 5)), 3), 'b11_p95': round(float(np.nanpercentile(b11[mm], 95)), 3),
                     'glcm_contraste_medio': round(float(np.nanmean(glcm_con[mm])), 1), 'ndvi_medio': round(float(np.nanmean(idx['NDVI'][mm])), 3)}
    else:
        REF[nome] = {'n_px': int(mm.sum()), 'nota': 'sem pixeles suficientes no AOI'}
    log('  referencia %-14s %s' % (nome, REF[nome]))
filas = []
for r in frag_v.itertuples():
    m = lab == r.frag_id
    nucleo = ndi.binary_erosion(m, structure=np.ones((3, 3)), iterations=2)
    borda = m & ~nucleo
    p_lt05 = m & (np.nan_to_num(prob_fl, nan=0) < 0.5)
    ev = {'b11_medio': round(float(np.nanmean(b11[m])), 3), 'b11_sd': round(float(np.nanstd(b11[m])), 3),
          'frac_b11_abaixo_p5_pastagem': (round(float(np.mean(b11[m] < REF['pastagem']['b11_p5'])), 2) if 'b11_p5' in REF['pastagem'] else None),
          'frac_dw_trees': round(float(np.mean(dw_lab[m] == 1)), 2), 'frac_dw_crops': round(float(np.mean(dw_lab[m] == 4)), 2),
          'frac_mb_2025_floresta': round(float(np.isin(mb10[m], list(MB_FLORESTA)).mean()), 2),
          'frac_mb_2025_soja': round(float(np.mean(mb10[m] == 39)), 2),
          'nucleo_ha': round(float(nucleo.sum()) / 100, 2), 'nucleo_prob_floresta_media': round(float(np.nanmean(prob_fl[nucleo])), 3) if nucleo.any() else None,
          'borda_ha': round(float(borda.sum()) / 100, 2), 'borda_prob_floresta_media': round(float(np.nanmean(prob_fl[borda])), 3) if borda.any() else None,
          'ha_prob_floresta_lt_05': round(float(p_lt05.sum()) / 100, 2),
          'frac_hansen_treecover2000_gt30': None}
    filas.append({'frag_id': int(r.frag_id), 'area_ha': r.area_ha, 'area_dentro_propriedade_ha': r.area_dentro_propriedade_ha, **ev,
                  'ndvi_medio': round(float(np.nanmean(idx['NDVI'][m])), 3), 'ndre_medio': round(float(np.nanmean(idx['NDRE'][m])), 3),
                  'ndmi_medio': round(float(np.nanmean(idx['NDMI'][m])), 3),
                  'glcm_contraste_medio': round(float(np.nanmean(glcm_con[m])), 1), 'glcm_homog_media': round(float(np.nanmean(glcm_hom[m])), 3),
                  'prob_floresta_media': round(float(np.nanmean(prob_fl[m])), 3),
                  'frac_floresta_mb_1985': round(float(np.isin(mb85_10[m], list(MB_FLORESTA)).mean()), 2),
                  'frac_floresta_mb_2008': round(float(np.isin(mb08_10[m], list(MB_FLORESTA)).mean()), 2),
                  'hand_medio_m': round(float(np.nanmean(hand10[m])), 1)})
tc00_10 = remuestrear_a(R['hansen'], prof10, banda=1, metodo='nearest')
for f_ in filas:
    m = lab == f_['frag_id']
    f_['frac_hansen_treecover2000_gt30'] = round(float(np.mean(np.nan_to_num(tc00_10[m], nan=0) > 30)), 2)
ft = pd.DataFrame(filas)
ft['persistencia'] = np.select([(ft.frac_floresta_mb_1985 >= 0.5) & (ft.frac_floresta_mb_2008 >= 0.5), ft.frac_floresta_mb_2008 >= 0.5],
                               ['floresta desde 1985 (>=40 anos): indicio de vegetacao mais antiga', 'floresta desde 2008 (>=17 anos)'],
                               'regeneracao recente ou nao-floresta em 2008')
ft['estagio_sucessional'] = 'NAO DETERMINADO POR SATELITE — indicativo, requer inventario de campo (CONAMA 2/1994: DAP, area basal, estratos)'
frag_v = frag_v.merge(ft, on=['frag_id', 'area_ha', 'area_dentro_propriedade_ha'])
guardar_vector(frag_v, 'fragmentos_floresta')
for r in frag_v.sort_values('area_dentro_propriedade_ha', ascending=False).itertuples():
    log('  frag %3d  %6.2f ha (dentro %6.2f)  NDVI %.3f  NDRE %.3f  con %.0f  hom %.3f  MB85 %.2f  MB08 %.2f  -> %s'
        % (r.frag_id, r.area_ha, r.area_dentro_propriedade_ha, r.ndvi_medio, r.ndre_medio, r.glcm_contraste_medio, r.glcm_homog_media,
           r.frac_floresta_mb_1985, r.frac_floresta_mb_2008, r.persistencia))
# serie NDVI 24 meses (gee_04, se existir): so se cita a conclusao ja calculada
serie_p = os.path.join(ANALISIS, 'serie_ndvi_fragmentos_24m.json')
serie_conc = leer_json(serie_p).get('conclusion') if os.path.exists(serie_p) else None
for r in frag_v.itertuples():
    log('  frag %3d  B11 %.3f+-%.3f (%.0f%% abaixo do p5 pastagem)  DW trees %.0f%%  MB25 floresta %.0f%%  nucleo %.2f ha p=%.2f  borda %.2f ha p=%.2f  p<0,5: %.2f ha  Hansen tc2000>30: %.0f%%'
        % (r.frag_id, r.b11_medio, r.b11_sd, 100 * (r.frac_b11_abaixo_p5_pastagem or 0), 100 * r.frac_dw_trees, 100 * r.frac_mb_2025_floresta,
           r.nucleo_ha, r.nucleo_prob_floresta_media or 0, r.borda_ha, r.borda_prob_floresta_media or 0, r.ha_prob_floresta_lt_05, 100 * r.frac_hansen_treecover2000_gt30))
RES['fragmentos'] = {'n': len(frag_v), 'min_ha': P['fragmento_min_ha'],
                     'lista': [{k: (v.item() if hasattr(v, 'item') else v) for k, v in row.items() if k != 'geometry'} for _, row in frag_v.iterrows()],
                     'referencias_espectrais_aoi': REF,
                     'serie_ndvi_24m_conclusao': serie_conc,
                     'nota_evidencia': 'B11 (SWIR) separa arboreo de pastagem/graminea (dossel arboreo retem mais agua -> B11 baixo); textura GLCM separa de cafe em fileiras; '
                                       'DW trees (moda 12 m) = concordancia externa; nucleo = erosao 2 px (20 m); borda = resto; p<0,5 = pixeles incertos do RF',
                     'aviso': 'estagio sucessional NAO se determina por satelite; indicadores descritivos apenas'}
actualizar_resultados('vegetacao', RES)
log('an_02 listo en %.0f s' % (time.time() - T0))
