# -*- coding: utf-8 -*-
"""dron_01: recorte de la ortofoto (RGBA, 0,10 y 0,25 m), DSM, DTM y CHM (0,25 m) POR INMUEBLE,
con la mascara EXACTA del poligono de cada inmueble (sin buffer). Verifica rangos y reporta
hectareas cubiertas / sin cobertura del dron por inmueble (ortofoto y DSM/DTM por separado).

Fuente: voo 22-mai-2026 (ODM), EPSG:32722 == EPSG:31982 (dx 0,0 m verificado). Los rasteres de
5 cm se leen por franjas con out_shape (overviews) y se escriben franja a franja.

SIN CALIBRACION SATELITAL: DSM/DTM quedan en el datum del vuelo (ODM sin GCP/RTK): las cotas
son RELATIVAS (sirven para CHM = DSM - DTM y para planitud del agua), no absolutas.

Cobertura medida (log_ortho_01): ortofoto N 7401016,7..7404007,0; DSM/DTM N 7401710,2..7404022,5.
Todo lo que el dron no cubre se reporta como "sem cobertura do drone: nao avaliado".
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dron_00_comun import *   # noqa: F401,F403
import numpy as np
from rasterio.enums import Resampling

cabecera('dron_01_recorte')
RESUMO = {}
SOLO = [a for a in sys.argv[1:] if not a.startswith('-')]   # p.ej. `python dron_01_recorte.py ponta_norte_ref`
for imovel in ORDEM_IMOVEIS + ([PONTA_NORTE] if PONTA_NORTE in imoveis() else []):
    if SOLO and imovel not in SOLO:
        continue
    log('\n' + '#' * 78)
    log('# %s  (%s, %.3f ha)' % (imovel, IMOVEIS[imovel]['nome'] if imovel in IMOVEIS else 'REFERENCIA: ponta norte removida, NAO e inmueble', area_ha(imovel)))
    log('#' * 78)
    tr25, H25, W25, B25 = grilla(imovel, 0.25)
    tr10, H10, W10, B10 = grilla(imovel, 0.10)
    log('  grilla 0,10 m: %dx%d px; grilla 0,25 m: %dx%d px; bounds %s' % (W10, H10, W25, H25, B25))
    INFO = {'imovel': imovel, 'nome': IMOVEIS[imovel]['nome'] if imovel in IMOVEIS else 'ponta norte removida (referencia, a conferir na escritura)', 'area_ha': area_ha(imovel), 'fecha_voo': FECHA_VUELO, 'crs': CRS_METRICO,
            'grilla_0_25m': {'w': W25, 'h': H25, 'bounds': B25}, 'grilla_0_10m': {'w': W10, 'h': H10, 'bounds': B10},
            'mascara': 'poligono exato do imovel (all_touched=False), sem buffer', 'datum_vertical': 'datum do voo (ODM, sem GCP/RTK): cotas RELATIVAS, sem calibracao satelital'}
    m25 = mascara(imovel, 0.25)
    A_IM = m25.sum() * 0.25 * 0.25 / 1e4

    with Cronometro('ortofoto -> 0,10 m'):
        st10, ha10 = recortar_ortofoto(imovel, 0.10, 2)
    with Cronometro('ortofoto -> 0,25 m'):
        st25, ha25 = recortar_ortofoto(imovel, 0.25, 5)
    INFO['ortofoto_stats'] = {'0_10m': st10, '0_25m': st25}

    with Cronometro('DSM / DTM / CHM -> 0,25 m'):
        dsm = recortar_elevacion(imovel, DSM_SRC, 0.25, 5)
        dtm = recortar_elevacion(imovel, DTM_SRC, 0.25, 5)
        hay = np.isfinite(dsm) & np.isfinite(dtm)
        dsm = np.where(hay, dsm, np.nan); dtm = np.where(hay, dtm, np.nan)
        INFO['dsm_stats'] = verificar_arr(dsm, 'dsm 0,25 m (datum voo)', m25, 'm', permitir_vacia=True)
        INFO['dtm_stats'] = verificar_arr(dtm, 'dtm 0,25 m (datum voo)', m25, 'm', permitir_vacia=True)
        chm = np.where(hay, np.clip(dsm - dtm, 0, 40), np.nan).astype('float32')
        n_neg = int((hay & ((dsm - dtm) < 0)).sum()); n_alto = int((hay & ((dsm - dtm) > 40)).sum())
        INFO['chm_stats'] = verificar_arr(chm, 'chm 0,25 m', m25, 'm', permitir_vacia=True)
        INFO['chm_nota'] = 'CHM = DSM - DTM do voo, recortado a [0, 40] m: %d px < 0 forcados a 0, %d px > 40 m' % (n_neg, n_alto)
        if INFO['chm_stats']['n']:
            v = chm[hay & m25]
            INFO['chm_histograma_pct'] = {k: round(100.0 * float(((v >= a) & (v < b)).mean()), 2) for k, (a, b) in
                                          {'0-0.5': (0, 0.5), '0.5-1': (0.5, 1), '1-3': (1, 3), '3-5': (3, 5), '5-10': (5, 10), '10-15': (10, 15), '15-25': (15, 25), '25-40': (25, 40.01)}.items()}
            log('    histograma CHM (%% da area com dado): %s' % INFO['chm_histograma_pct'])
        escribir(imovel, R(imovel, 'dsm.tif', 0.25), dsm, 0.25, bandas=['dsm_m'], tags={'datum': 'voo ODM, relativo'})
        escribir(imovel, R(imovel, 'dtm.tif', 0.25), dtm, 0.25, bandas=['dtm_m'], tags={'datum': 'voo ODM, relativo'})
        escribir(imovel, R(imovel, 'chm.tif', 0.25), chm, 0.25, bandas=['chm_m'], tags={'definicao': 'DSM - DTM, [0,40] m'})

    with Cronometro('cobertura do drone'):
        rgba, _ = leer(R(imovel, 'ortofoto_rgba.tif', 0.25), nan=False)
        val = rgba[3] > 0
        del rgba
        com_o = val & m25; sem_o = m25 & ~val
        com_d = hay & m25; sem_d = m25 & ~hay
        px = 0.25 * 0.25 / 1e4
        def n_lim(mask, cual):
            if not mask.any():
                return None
            rows = np.where(mask.any(1))[0]
            ys = tr25.f + (rows + 0.5) * tr25.e
            return round(float(ys.min() if cual == 'min' else ys.max()), 1)
        cob = {'area_imovel_ha': round(A_IM, 3),
               'ortofoto': {'com_cobertura_ha': round(com_o.sum() * px, 3), 'sem_cobertura_ha': round(sem_o.sum() * px, 3),
                            'pct_coberto': round(100.0 * com_o.sum() / m25.sum(), 2), 'N_min_com_dado': n_lim(com_o, 'min'), 'N_max_com_dado': n_lim(com_o, 'max'),
                            'sem_cobertura_N_min': n_lim(sem_o, 'min')},
               'dsm_dtm': {'com_cobertura_ha': round(com_d.sum() * px, 3), 'sem_cobertura_ha': round(sem_d.sum() * px, 3),
                           'pct_coberto': round(100.0 * com_d.sum() / m25.sum(), 2), 'N_min_com_dado': n_lim(com_d, 'min'), 'N_max_com_dado': n_lim(com_d, 'max'),
                           'sem_cobertura_N_max_sul': n_lim(sem_d & (np.arange(H25)[:, None] > H25 // 2), 'max'), 'sem_cobertura_N_min_norte': n_lim(sem_d & (np.arange(H25)[:, None] < H25 // 2), 'min')},
               'ortofoto_e_dsm_ha': round((com_o & com_d).sum() * px, 3),
               'ortofoto_sem_dsm_ha': round((com_o & ~com_d).sum() * px, 3),
               'regra': 'sem cobertura do drone = NAO AVALIADO (nao se preenche com satelite)'}
        for k in ('ortofoto', 'dsm_dtm'):
            s = cob[k]['com_cobertura_ha'] + cob[k]['sem_cobertura_ha']
            assert abs(s - A_IM) < 0.002, (k, s, A_IM)
        INFO['cobertura'] = cob
        log('  ortofoto: com %.3f ha / sem %.3f ha (%.2f %%); DSM/DTM: com %.3f / sem %.3f (%.2f %%); orto sem DSM %.3f ha'
            % (cob['ortofoto']['com_cobertura_ha'], cob['ortofoto']['sem_cobertura_ha'], cob['ortofoto']['pct_coberto'],
               cob['dsm_dtm']['com_cobertura_ha'], cob['dsm_dtm']['sem_cobertura_ha'], cob['dsm_dtm']['pct_coberto'], cob['ortofoto_sem_dsm_ha']))
        import geopandas as gpd
        import pandas as pd
        partes = []
        for nome, mk in (('sem_ortofoto', sem_o), ('sem_dsm_dtm', sem_d), ('com_ortofoto', com_o), ('com_dsm_dtm', com_d)):
            g = vectorizar(imovel, mk, 0.25, min_area_m2=1.0, campos={'cobertura': nome})
            if len(g):
                partes.append(g)
        gdf = gpd.GeoDataFrame(pd.concat(partes, ignore_index=True), crs=CRS_METRICO)
        gdf['imovel'] = imovel; gdf['fecha_voo'] = FECHA_VUELO
        gdf['nota'] = gdf.cobertura.map({'sem_ortofoto': 'sem cobertura do drone: nao avaliado', 'sem_dsm_dtm': 'sem DSM/DTM do drone: altura/cota nao avaliadas',
                                         'com_ortofoto': 'ortofoto 5 cm disponivel', 'com_dsm_dtm': 'DSM/DTM 5 cm disponiveis'})
        guardar_gdf(gdf, R(imovel, 'cobertura_drone_%s.geojson' % imovel))
        # huellas como geometrias para los scripts siguientes
        from shapely.geometry import mapping
        from shapely.ops import unary_union
        INFO['huellas'] = {k: mapping(unary_union(list(gdf[gdf.cobertura == k].geometry))) if (gdf.cobertura == k).any() else None
                           for k in ('com_ortofoto', 'com_dsm_dtm', 'sem_ortofoto', 'sem_dsm_dtm')}
    guardar_json(R(imovel, 'dron_01_recorte.json'), INFO)
    RESUMO[imovel] = {'area_ha': INFO['area_ha'], 'cobertura': {k: v for k, v in cob.items()}}
    del dsm, dtm, chm, hay, val, m25

if not SOLO:
    guardar_json(os.path.join(SALIDA_RAIZ, 'dron_01_resumo_cobertura.json'), RESUMO)
log('dron_01 listo.')
