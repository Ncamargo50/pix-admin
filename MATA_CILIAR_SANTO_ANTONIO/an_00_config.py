# -*- coding: utf-8 -*-
"""Rutas, parametros y helpers compartidos por la etapa de ANALISIS (an_01..an_03).

    from an_00_config import *

Todo lo metrico va en EPSG:31982 (SIRGAS 2000 / UTM 22S). Cada script escribe
en 02_ANALISIS/ y actualiza (por clave, sin pisar lo ajeno) el archivo
`resultados_analisis.json`, que es la unica fuente de cifras del informe.
"""
import json
import os
import sys
import unicodedata
import warnings

import numpy as np

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

# comun.py (no se toca): propiedad, AOI alineado, rutas del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import (CODIGO, PROYECTO, SALIDA as DATOS_SAT, PROPIEDAD_GEOJSON,   # noqa: E402
                   EPSG_METRICO, CRS_METRICO, cargar_propiedad, leer_json,
                   guardar_json, log)

DATOS_EXT = os.path.join(CODIGO, 'datos_externos')
LEGISLACION = os.path.join(CODIGO, 'legislacion')
ANALISIS = os.path.join(PROYECTO, '02_ANALISIS')
os.makedirs(ANALISIS, exist_ok=True)
RESULTADOS_JSON = os.path.join(ANALISIS, 'resultados_analisis.json')

CRS_WGS84 = 'EPSG:4326'
FECHA_ESCENA = '2026-08-29'
ESCENA_ID = '20260829T133141_20260829T133143_T22KEV'

# --- rasteres satelitales -----------------------------------------------------
R = {
    's2': os.path.join(DATOS_SAT, 'S2_2026-08-29_AOI_10m.tif'),
    'indices': os.path.join(DATOS_SAT, 'S2_2026-08-29_INDICES_10m.tif'),
    'rgb': os.path.join(DATOS_SAT, 'S2_2026-08-29_RGB.tif'),
    'scl': os.path.join(DATOS_SAT, 'S2_2026-08-29_SCL_10m.tif'),
    'dem': os.path.join(DATOS_SAT, 'DEM_GLO30_AOIdem_30m.tif'),
    'dem_nasa': os.path.join(DATOS_SAT, 'DEM_NASADEM_AOIdem_30m.tif'),
    'merit': os.path.join(DATOS_SAT, 'HIDRO_MERIT_upa_hnd_AOIdem_90m.tif'),
    'jrc': os.path.join(DATOS_SAT, 'AGUA_JRC_GSW_AOI_30m.tif'),
    'mb_hist': os.path.join(DATOS_SAT, 'LULC_MAPBIOMAS_col11_2025_2008_1985_AOI_30m.tif'),
    'mb_10m': os.path.join(DATOS_SAT, 'LULC_MAPBIOMAS_col11_2025_AOI_10m_nearest.tif'),
    'dw': os.path.join(DATOS_SAT, 'LULC_DYNAMICWORLD_moda12m_AOI_10m.tif'),
    'wc': os.path.join(DATOS_SAT, 'LULC_ESA_WORLDCOVER_2021_AOI_10m.tif'),
    'hansen': os.path.join(DATOS_SAT, 'BOSQUE_HANSEN_GFC_2025_AOI_30m.tif'),
}

# --- vectores oficiales (EPSG:4326 en disco) ----------------------------------
V = {
    'fbds_rios': os.path.join(DATOS_EXT, 'IAT_FBDS_rios_ate10m.geojson'),
    'fbds_nascentes': os.path.join(DATOS_EXT, 'IAT_FBDS_nascentes.geojson'),
    'fbds_massas': os.path.join(DATOS_EXT, 'IAT_FBDS_massas_dagua.geojson'),
    'fbds_rios_pol': os.path.join(DATOS_EXT, 'IAT_FBDS_rios_acima10m_pol.geojson'),
    'fbds_app': os.path.join(DATOS_EXT, 'IAT_FBDS_app_hidrica.geojson'),
    'fbds_app_uso': os.path.join(DATOS_EXT, 'IAT_FBDS_app_uso.geojson'),
    'fbds_uso2013': os.path.join(DATOS_EXT, 'IAT_FBDS_uso_cobertura_2013.geojson'),
    'otto': os.path.join(DATOS_EXT, 'IAT_otto_trecho_drenagem_2020.geojson'),
    'ana': os.path.join(DATOS_EXT, 'ANA_BHO2017_5k_trecho_drenagem.geojson'),
    'ibge': os.path.join(DATOS_EXT, 'IBGE_BC250_trecho_drenagem.geojson'),
    'car_vecinos': os.path.join(DATOS_EXT, 'PR_geoserver_car_hidrografia_pol.geojson'),
}
PARAMETROS_LEGALES = os.path.join(LEGISLACION, 'parametros_legales.json')

# --- parametros del analisis ---------------------------------------------------
P = {
    'margen_aoi_hidro_m': 500,          # recorte de hidrografia: propiedad + 500 m
    'umbrales_aporte_ha': [5, 10, 20],  # umbral de area de aporte para la red DEM
    'pixel_dem_m': 30,
    'pixel_s2_m': 10,
    'sieve_agua_px': 3,
    'ndvi_max_agua': 0.30,
    'tol_regime_m': 30,                 # coincidencia tramo FBDS ~ IBGE BC250
    'dist_nascente_dem_m': 60,          # candidato DEM sin nascente FBDS a < 60 m
    'margen_cabeceras_m': 100,
    'app_curso_m': 30,
    'app_nascente_m': 50,
    'pra_curso_m': 20,                  # Lei PR 18.295/2014 art. 17 par. 2 (4-10 MF)
    'pra_nascente_m': 15,
    'media_anchura_curso_m': 3,         # semi-anchura tipica de cursos de 1a-2a orden
    'incert_pos_m': 10,                 # 1 px S2
    'reservatorio_faixa_ref_m': 30,     # escenario de referencia (continuidad del curso)
    'reservatorio_dispensa_ha': 1.0,    # art. 4 par. 4
    'mmu_floresta_ha': 0.05,
    'fragmento_min_ha': 0.5,
    'bloque_cv_m': 500,
    'max_muestras_clase': 5000,
    'min_px_clase': 200,
    'rf_arboles': 300,
    'semilla': 42,
}

# --- leyendas ------------------------------------------------------------------
MB = {3: 'Formacao Florestal', 9: 'Silvicultura', 11: 'Campo Alagado', 12: 'Formacao Campestre',
      15: 'Pastagem', 20: 'Cana', 21: 'Mosaico de Usos', 24: 'Area Urbanizada',
      25: 'Outras Areas nao Vegetadas', 33: 'Rio, Lago e Oceano', 36: 'Lavoura Perene',
      39: 'Soja', 41: 'Outras Lavouras Temporarias', 46: 'Cafe', 48: 'Outras Lavouras Perenes'}
MB_FLORESTA = {3}
MB_AGUA = {33}
MB_SILVICULTURA = {9}
MB_ANTROPIZADO = {39, 41, 21, 15, 20, 48, 36, 46, 24, 25}
MB_HERBACEO_NATIVO = {11, 12}
DW = {0: 'water', 1: 'trees', 2: 'grass', 3: 'flooded_vegetation', 4: 'crops',
      5: 'shrub_and_scrub', 6: 'built', 7: 'bare', 8: 'snow_and_ice'}
WC = {10: 'Tree cover', 20: 'Shrubland', 30: 'Grassland', 40: 'Cropland', 50: 'Built-up',
      60: 'Bare', 80: 'Permanent water bodies', 90: 'Herbaceous wetland'}
SCL_INVALIDA = {0, 1, 2, 3, 8, 9, 10, 11}   # nodata, saturado, oscuro, sombra, nube, cirro, nieve

# clases del RF (uint8)
CLASES_RF = {1: 'FLORESTA_NATIVA', 2: 'AGUA', 3: 'AREA_ANTROPIZADA',
             4: 'SILVICULTURA', 5: 'VEGETACAO_HERBACEA_NATIVA'}


# --- helpers -------------------------------------------------------------------
def sin_acentos(s):
    if s is None:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s))
                   if not unicodedata.combining(c)).lower().strip()


def ha(area_m2):
    return round(float(area_m2) / 1e4, 2)


def km(long_m):
    return round(float(long_m) / 1e3, 3)


def propiedad():
    """dict de comun.cargar_propiedad + GeoDataFrame en 31982."""
    import geopandas as gpd
    p = cargar_propiedad()
    p['gdf'] = gpd.GeoDataFrame({'nome': ['Fazenda Santo Antonio']},
                                geometry=[p['geom']], crs=CRS_METRICO)
    return p


def leer_vector(clave, recorte=None, explotar=True):
    """Lee un GeoJSON de datos_externos, lo reproyecta a 31982 y (opcional) lo recorta."""
    import geopandas as gpd
    g = gpd.read_file(V[clave])
    if g.crs is None:
        g = g.set_crs(CRS_WGS84)
    import shapely
    # partes con vertices basura (visto en CAR WFS: lon -144, lat 4): se descartan ANTES de
    # reproyectar, porque en UTM se vuelven NaN y rompen toda operacion topologica
    g = g.explode(index_parts=False).reset_index(drop=True)
    g['geometry'] = shapely.force_2d(g.geometry.values)
    bx = g.geometry.bounds
    fuera = (bx.minx < -54) | (bx.maxx > -47) | (bx.miny < -27) | (bx.maxy > -20)
    if fuera.any():
        log('  [%s] %d parte(s) con vertices fuera de Parana (basura WFS) descartadas' % (clave, int(fuera.sum())))
        g = g[~fuera].copy()
    g = g.to_crs(CRS_METRICO)
    inval = ~g.geometry.is_valid
    if inval.any():
        log('  [%s] %d geometria(s) invalida(s) reparada(s) con make_valid' % (clave, int(inval.sum())))
        g.loc[inval, 'geometry'] = g.loc[inval, 'geometry'].make_valid()
    if explotar:
        g = g.explode(index_parts=False).reset_index(drop=True)
    g = g[~g.geometry.is_empty & g.geometry.notna()].copy()
    if recorte is not None:
        g = g[g.intersects(recorte)].copy()
        g['geometry'] = g.geometry.intersection(recorte)
        g = g[~g.geometry.is_empty].copy()
        if explotar:
            g = g.explode(index_parts=False).reset_index(drop=True)
    return g.reset_index(drop=True)


def guardar_vector(gdf, nombre):
    """Guarda `nombre.geojson` (31982) y `nombre_wgs84.geojson` en 02_ANALISIS."""
    import geopandas as gpd
    gdf = gpd.GeoDataFrame(gdf, geometry='geometry', crs=CRS_METRICO)
    # GeoJSON no admite objetos raros: todo a str/num/bool
    for c in gdf.columns:
        if c == 'geometry':
            continue
        if gdf[c].dtype == object:
            gdf[c] = gdf[c].map(lambda v: v if isinstance(v, (str, int, float, bool)) or v is None
                                else str(v))
        elif str(gdf[c].dtype).startswith('float'):
            gdf[c] = gdf[c].astype(float)
    ruta = os.path.join(ANALISIS, nombre + '.geojson')
    ruta_w = os.path.join(ANALISIS, nombre + '_wgs84.geojson')
    for r in (ruta, ruta_w):
        if os.path.exists(r):
            os.remove(r)
    gdf.to_file(ruta, driver='GeoJSON')
    gdf.to_crs(CRS_WGS84).to_file(ruta_w, driver='GeoJSON')
    log('  -> %s (%d feats)' % (ruta, len(gdf)))
    return ruta


def leer_raster(ruta, bandas=None):
    """Devuelve (dict banda->array float o uint, profile). nodata -> NaN en float."""
    import rasterio
    with rasterio.open(ruta) as ds:
        prof = ds.profile.copy()
        descs = list(ds.descriptions)
        out = {}
        for i, d in enumerate(descs, start=1):
            if bandas is not None and d not in bandas:
                continue
            a = ds.read(i)
            if np.issubdtype(a.dtype, np.floating) and ds.nodata is not None:
                a = a.astype(np.float32)
                a[a == ds.nodata] = np.nan
            out[d] = a
    return out, prof


def guardar_raster(ruta, arr, perfil_ref, nodata=None, tags=None, descripciones=None):
    """Escribe GeoTIFF LZW con el grid del perfil de referencia."""
    import rasterio
    arr = np.asarray(arr)
    if arr.ndim == 2:
        arr = arr[None]
    prof = perfil_ref.copy()
    prof.update(count=arr.shape[0], dtype=arr.dtype, compress='lzw', tiled=False,
                nodata=nodata, driver='GTiff')
    prof.pop('blockxsize', None); prof.pop('blockysize', None)
    with rasterio.open(ruta, 'w', **prof) as ds:
        ds.write(arr)
        if tags:
            ds.update_tags(**{k: str(v) for k, v in tags.items()})
        if descripciones:
            for i, d in enumerate(descripciones, start=1):
                ds.set_band_description(i, d)
    log('  -> %s %s' % (ruta, arr.shape))


def rasterizar(geoms, perfil, valor=1, fill=0, all_touched=False, dtype=np.uint8):
    from rasterio import features
    shapes = [(g, valor) for g in geoms if g is not None and not g.is_empty]
    if not shapes:
        return np.full((perfil['height'], perfil['width']), fill, dtype=dtype)
    return features.rasterize(shapes, out_shape=(perfil['height'], perfil['width']),
                              transform=perfil['transform'], fill=fill,
                              all_touched=all_touched, dtype=dtype)


def vectorizar(mascara, perfil, campo='valor'):
    """Poligoniza una mascara/clase raster (int) -> GeoDataFrame 31982 con `campo`."""
    import geopandas as gpd
    from rasterio import features
    from shapely.geometry import shape
    geoms, vals = [], []
    for geom, v in features.shapes(mascara.astype(np.int32), mask=mascara > 0,
                                   transform=perfil['transform']):
        geoms.append(shape(geom)); vals.append(int(v))
    return gpd.GeoDataFrame({campo: vals}, geometry=geoms, crs=CRS_METRICO)


def remuestrear_a(ruta_src, perfil_dst, banda=1, metodo='nearest'):
    """Reproyecta/remuestrea una banda de `ruta_src` al grid de `perfil_dst`."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    with rasterio.open(ruta_src) as src:
        a = src.read(banda)
        dtype = np.float32 if metodo != 'nearest' else a.dtype
        dst = np.full((perfil_dst['height'], perfil_dst['width']),
                      src.nodata if src.nodata is not None else 0, dtype=dtype)
        reproject(a.astype(dtype), dst, src_transform=src.transform, src_crs=src.crs,
                  src_nodata=src.nodata, dst_transform=perfil_dst['transform'],
                  dst_crs=perfil_dst['crs'], dst_nodata=src.nodata,
                  resampling=getattr(Resampling, metodo))
        if np.issubdtype(dst.dtype, np.floating) and src.nodata is not None:
            dst[dst == src.nodata] = np.nan
    return dst


def verificar_rango(nombre, arr, minimo=None, maximo=None):
    """Regla del proyecto: imprimir min/max/media de cada capa y avisar fuerte si sale de rango."""
    a = np.asarray(arr, dtype=np.float64)
    v = a[np.isfinite(a)]
    if v.size == 0:
        log('  [RANGO] %-28s VACIA' % nombre); return
    mn, mx, me = float(v.min()), float(v.max()), float(v.mean())
    aviso = ''
    if minimo is not None and mn < minimo:
        aviso += ' << MIN %.3f < %.3f' % (mn, minimo)
    if maximo is not None and mx > maximo:
        aviso += ' << MAX %.3f > %.3f' % (mx, maximo)
    if mn == mx:
        aviso += ' << DEGENERADA'
    log('  [RANGO] %-28s n=%-8d min=%-10.4f max=%-10.4f media=%-10.4f nan=%.1f%%%s'
        % (nombre, v.size, mn, mx, me, 100 * (1 - v.size / a.size), aviso))


def actualizar_resultados(clave, valor):
    """Escribe `clave` en resultados_analisis.json sin tocar las demas claves."""
    res = leer_json(RESULTADOS_JSON) if os.path.exists(RESULTADOS_JSON) else {}
    res[clave] = valor
    res['_meta'] = {'crs': CRS_METRICO, 'escena': ESCENA_ID, 'fecha_escena': FECHA_ESCENA,
                    'generado': __import__('datetime').date.today().isoformat()}
    guardar_json(RESULTADOS_JSON, _limpio(res))


def _limpio(o):
    """numpy -> tipos nativos para json."""
    if isinstance(o, dict):
        return {str(k): _limpio(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_limpio(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if not np.isfinite(o) else float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, float) and not np.isfinite(o):
        return None
    return o


def titulo(t):
    log(); log('=' * 78); log(t); log('=' * 78)
