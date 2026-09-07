# -*- coding: utf-8 -*-
"""Piezas compartidas de la etapa ORTOFOTO (ortho_01..ortho_06).

    from ortho_00_comun import *

Insumos: vuelo dron 22-may-2026 (ODM 3.7.4) en EPSG:32722 (WGS84/UTM 22S).
Verificado por el usuario: desplazamiento 32722 -> 31982 (SIRGAS 2000/UTM 22S)
= 0,0 m; todas las salidas se ETIQUETAN en EPSG:31982.

GRILLA COMUN: bbox de la propiedad + 40 m, origen alineado a 10 m, pixel 0,25 m
y 0,50 m (la de 0,50 anida exactamente en la de 0,25). Todo raster derivado se
escribe en esa grilla, asi las capas se apilan sin remuestrear.

REGLA DE LA CASA: los rasteres originales (2,3 GB / 1,1 GB) NUNCA se leen con
read() completo: se leen por franjas con out_shape (GDAL usa los overviews).
Cada capa que se escribe pasa por `verificar_arr`: min/max/media/%nodata y
falla si esta vacia.
"""
import json
import os
import sys
import time
import warnings

import numpy as np

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import (CODIGO, PROYECTO, PROPIEDAD_GEOJSON, EPSG_METRICO, CRS_METRICO,   # noqa: E402
                   cargar_propiedad, leer_json, guardar_json, log, HOY)

# --- rutas -------------------------------------------------------------------
DRONE = r'D:\PIXADVISOR\Vuelos-Drone\Ortofoto-S.A'
ORTHO_SRC = os.path.join(DRONE, 'odm_orthophoto.tif')
DSM_SRC = os.path.join(DRONE, 'dsm.tif')
DTM_SRC = os.path.join(DRONE, 'dtm.tif')
ANALISIS = os.path.join(PROYECTO, '02_ANALISIS')
HIDRO_PRO = os.path.join(ANALISIS, 'hidrologia_pro')
DATOS_SAT = os.path.join(PROYECTO, '01_DATOS_SATELITE')
SALIDA = os.path.join(PROYECTO, '05_ORTOFOTO')
os.makedirs(SALIDA, exist_ok=True)
LEGISLACION = os.path.join(CODIGO, 'legislacion')
PARAMETROS_LEGALES = os.path.join(LEGISLACION, 'parametros_legales.json')

FECHA_VUELO = '2026-05-22'
FECHA_S2 = '2026-08-29'
CRS_FUENTE = 'EPSG:32722'
NODATA_F = -9999.0

# --- capas previas (02_ANALISIS) ----------------------------------------------
PREV = {
    'glebas': os.path.join(ANALISIS, 'gleba_limites.geojson'),
    'hidro': os.path.join(ANALISIS, 'hidrografia_consolidada.geojson'),
    'arroios_g1': os.path.join(ANALISIS, 'gleba_G1_arroios.geojson'),
    'arroios_g2': os.path.join(ANALISIS, 'gleba_G2_arroios.geojson'),
    'nascentes': os.path.join(ANALISIS, 'nascentes_consolidadas.geojson'),
    'nascentes_veredicto': os.path.join(HIDRO_PRO, 'nascentes_veredicto.geojson'),
    'massas': os.path.join(ANALISIS, 'massas_dagua_propriedade.geojson'),
    'represa_espelhos': os.path.join(ANALISIS, 'v3_represa_espelhos.geojson'),
    'fragmentos': os.path.join(ANALISIS, 'fragmentos_floresta.geojson'),
    'veg_10m_tif': os.path.join(ANALISIS, 'vegetacao_10m_2026-08-29.tif'),
    'veg_10m': os.path.join(ANALISIS, 'vegetacao_nativa_10m.geojson'),
    'mapa_car': os.path.join(ANALISIS, 'mapa_uso_car.geojson'),
    'car': os.path.join(HIDRO_PRO, 'CAR_propriedade_e_vizinhos.geojson'),
    'ensamble': os.path.join(HIDRO_PRO, 'hidro_ensamble_mediana_por_arroio.geojson'),
    'acum_30m': os.path.join(ANALISIS, 'ACUMULACION_ha_30m.tif'),
    'resultados_v3': os.path.join(ANALISIS, 'resultados_v3.json'),
    'resultados_glebas': os.path.join(ANALISIS, 'resultados_glebas.json'),
    'resultados_hidro': os.path.join(HIDRO_PRO, 'resultados_hidrologia_pro.json'),
    'app_g1': os.path.join(ANALISIS, 'gleba_G1_app.geojson'),
    'app_g2': os.path.join(ANALISIS, 'gleba_G2_app.geojson'),
    'rl_proposta': os.path.join(ANALISIS, 'v3_RL_proposta.geojson'),
    's2_rgb': os.path.join(DATOS_SAT, 'S2_2026-08-29_RGB.tif'),
}

# --- productos de esta etapa ----------------------------------------------------
def R(nombre, res=None):
    """Ruta de un producto en 05_ORTOFOTO; `res` agrega el sufijo _0_25m / _0_50m."""
    if res is None:
        return os.path.join(SALIDA, nombre)
    suf = {0.25: '0_25m', 0.5: '0_50m', 0.05: '0_05m', 10: '10m'}[res]
    base, ext = os.path.splitext(nombre)
    return os.path.join(SALIDA, '%s_%s%s' % (base, suf, ext))


# --- grilla comun -----------------------------------------------------------------
MARGEN_M = 40
ALINEACION_M = 10


def grilla(res):
    """(transform, height, width, bounds) de la grilla comun a resolucion `res`."""
    from rasterio.transform import from_origin
    p = cargar_propiedad()
    x0, y0, x1, y1 = p['bounds_31982']
    x0 = np.floor((x0 - MARGEN_M) / ALINEACION_M) * ALINEACION_M
    y0 = np.floor((y0 - MARGEN_M) / ALINEACION_M) * ALINEACION_M
    x1 = np.ceil((x1 + MARGEN_M) / ALINEACION_M) * ALINEACION_M
    y1 = np.ceil((y1 + MARGEN_M) / ALINEACION_M) * ALINEACION_M
    w = int(round((x1 - x0) / res))
    h = int(round((y1 - y0) / res))
    return from_origin(x0, y1, res, res), h, w, (float(x0), float(y0), float(x1), float(y1))


# --- lectura por franjas con overviews -------------------------------------------------
def leer_decimado(src_path, bandas, factor, resampling, filas_franja=4096, dtype='float32'):
    """Lee `src_path` decimado por `factor` (entero), por franjas de filas, con
    el remuestreo pedido. GDAL resuelve cada franja con el overview mas cercano.
    Devuelve (array (nb, H/f, W/f), transform decimado, crs). Con dtype float el
    nodata de la fuente sale como NaN."""
    import rasterio
    from rasterio.windows import Window
    with rasterio.open(src_path) as src:
        H, W = src.height, src.width
        h_out, w_out = H // factor, W // factor
        es_float = np.issubdtype(np.dtype(dtype), np.floating)
        out = np.full((len(bandas), h_out, w_out), np.nan if es_float else 0, dtype=dtype)
        nd = src.nodata
        r0 = 0
        n_franjas = 0
        while r0 < h_out:
            r1 = min(h_out, r0 + filas_franja)
            win = Window(0, r0 * factor, w_out * factor, (r1 - r0) * factor)
            a = src.read(bandas, window=win, out_shape=(len(bandas), r1 - r0, w_out),
                         resampling=resampling, masked=(nd is not None))
            if nd is not None:
                a = np.ma.filled(a.astype('float32'), np.nan)
            out[:, r0:r1, :] = a.astype(dtype)
            r0 = r1
            n_franjas += 1
        log('  leido %s por %d franjas, factor %d -> %dx%d px' % (os.path.basename(src_path), n_franjas, factor, w_out, h_out))
        tr = src.transform * src.transform.scale(factor, factor)
        return out, tr, src.crs


def a_grilla(arr, tr_src, crs_src, res, resampling, nodata=np.nan, dtype='float32'):
    """Reproyecta un arreglo (nb,h,w) o (h,w) a la grilla comun (EPSG:31982)."""
    import rasterio
    from rasterio.warp import reproject
    from rasterio.crs import CRS
    tr, h, w, _ = grilla(res)
    a = np.asarray(arr)
    if a.ndim == 2:
        a = a[None]
    dst = np.full((a.shape[0], h, w), nodata, dtype=dtype)
    for i in range(a.shape[0]):
        src_i = a[i].astype('float32') if dtype == 'float32' else a[i]
        src_nd = np.nan if np.issubdtype(src_i.dtype, np.floating) else None
        reproject(src_i, dst[i], src_transform=tr_src, src_crs=crs_src,
                  src_nodata=src_nd, dst_transform=tr, dst_crs=CRS.from_epsg(EPSG_METRICO),
                  dst_nodata=nodata, resampling=resampling, num_threads=4)
    return dst


# --- escritura / lectura de productos -----------------------------------------------------
def escribir(ruta, arr, res, dtype='float32', nodata=NODATA_F, bandas=None, tags=None,
             alpha=False, overviews=True):
    import rasterio
    from rasterio.crs import CRS
    from rasterio.enums import ColorInterp, Resampling
    tr, h, w, _ = grilla(res)
    a = np.asarray(arr)
    if a.ndim == 2:
        a = a[None]
    assert a.shape[1:] == (h, w), (a.shape, (h, w))
    if np.issubdtype(a.dtype, np.floating) and nodata is not None:
        a = np.where(np.isfinite(a), a, nodata)
    perfil = {'driver': 'GTiff', 'height': h, 'width': w, 'count': a.shape[0], 'dtype': dtype,
              'crs': CRS.from_epsg(EPSG_METRICO), 'transform': tr, 'compress': 'DEFLATE',
              'predictor': 2 if dtype == 'float32' else 1, 'tiled': True, 'blockxsize': 512,
              'blockysize': 512, 'nodata': nodata, 'BIGTIFF': 'IF_SAFER'}
    with rasterio.open(ruta, 'w', **perfil) as dst:
        dst.write(a.astype(dtype))
        if bandas:
            for i, b in enumerate(bandas, 1):
                dst.set_band_description(i, b)
        if alpha and a.shape[0] == 4:
            dst.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue, ColorInterp.alpha]
        dst.update_tags(fuente='vuelo dron %s ODM 3.7.4, EPSG:32722 == EPSG:31982 (dx=0,0 m)' % FECHA_VUELO,
                        crs_etiqueta=CRS_METRICO, **(tags or {}))
        if overviews:
            dst.build_overviews([2, 4, 8, 16], Resampling.average if dtype == 'float32' else Resampling.nearest)
    log('  escrito %s (%.1f MB, %dx%d px, %.2f m)' % (os.path.basename(ruta), os.path.getsize(ruta) / 1e6, w, h, res))
    return ruta


def leer(ruta, banda=None, nan=True):
    """Lee un producto de 05_ORTOFOTO completo (son <= 40 Mpx). float -> NaN en nodata."""
    import rasterio
    with rasterio.open(ruta) as src:
        a = src.read(banda) if banda else src.read()
        nd = src.nodata
        if nan and np.issubdtype(a.dtype, np.floating) and nd is not None:
            a = np.where(a == nd, np.nan, a)
        return a, src.transform


def verificar_arr(a, nombre, mascara=None, unidades=''):
    """min/max/media/%nodata de un arreglo 2D. Falla si esta vacio o degenerado."""
    a = np.asarray(a)
    if a.ndim == 3:
        for i in range(a.shape[0]):
            verificar_arr(a[i], '%s[b%d]' % (nombre, i + 1), mascara, unidades)
        return
    if np.issubdtype(a.dtype, np.floating):
        valido = np.isfinite(a) & (a != NODATA_F)
    else:
        valido = np.ones(a.shape, bool)
    if mascara is not None:
        tot = int(mascara.sum())
        valido = valido & mascara
    else:
        tot = int(a.size)
    n = int(valido.sum())
    if n == 0:
        raise RuntimeError('capa %s VACIA (n=0)' % nombre)
    v = a[valido].astype('float64')
    mn, mx, me = float(v.min()), float(v.max()), float(v.mean())
    pct_nd = 100.0 * (1 - n / tot)
    aviso = '  <-- DEGENERADA' if mx == mn else ''
    log('    %-28s n=%-10d min=%10.3f max=%10.3f media=%10.3f nodata=%5.1f%% %s%s'
        % (nombre, n, mn, mx, me, pct_nd, unidades, aviso))
    if mx == mn:
        raise RuntimeError('capa %s degenerada (min == max == %s)' % (nombre, mn))
    return {'n': n, 'min': round(mn, 4), 'max': round(mx, 4), 'media': round(me, 4), 'pct_nodata': round(pct_nd, 2)}


def rasterizar(geoms, res, valor=1, all_touched=False, dtype='uint8'):
    from rasterio.features import rasterize
    tr, h, w, _ = grilla(res)
    if not isinstance(geoms, (list, tuple)):
        geoms = [geoms]
    shp = [g if isinstance(g, tuple) else (g, valor) for g in geoms]
    shp = [(g, v) for g, v in shp if g is not None and not g.is_empty]
    if not shp:
        return np.zeros((h, w), dtype=dtype)
    return rasterize(shp, out_shape=(h, w), transform=tr, fill=0, dtype=dtype, all_touched=all_touched)


def vectorizar(mask, res, min_area_m2=0.0, campos=None):
    """bool 2D -> GeoDataFrame de poligonos (31982), sin huecos pequenos."""
    import geopandas as gpd
    from rasterio.features import shapes
    from shapely.geometry import shape
    tr, h, w, _ = grilla(res)
    m = mask.astype('uint8')
    polys = [shape(g) for g, v in shapes(m, mask=m.astype(bool), transform=tr, connectivity=8) if v == 1]
    polys = [p for p in polys if p.area >= min_area_m2]
    gdf = gpd.GeoDataFrame({'area_ha': [round(p.area / 1e4, 4) for p in polys]}, geometry=polys, crs=CRS_METRICO)
    for k, v in (campos or {}).items():
        gdf[k] = v
    return gdf


def guardar_gdf(gdf, ruta):
    """GeoJSON en 31982 (etiqueta) + copia _wgs84 para QGIS/Google Earth."""
    import geopandas as gpd
    if len(gdf) == 0:
        for r_ in (ruta, ruta.replace('.geojson', '_wgs84.geojson')):
            if os.path.exists(r_):
                os.remove(r_)
        log('  AVISO: %s sin registros (no se escribe; archivo anterior borrado)' % os.path.basename(ruta))
        return
    g = gdf.copy()
    for c in g.columns:
        if c != 'geometry' and g[c].dtype == object:
            g[c] = g[c].apply(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
    if os.path.exists(ruta):
        os.remove(ruta)
    g.to_file(ruta, driver='GeoJSON')
    r84 = ruta.replace('.geojson', '_wgs84.geojson')
    if os.path.exists(r84):
        os.remove(r84)
    g.to_crs('EPSG:4326').to_file(r84, driver='GeoJSON')
    log('  -> %s (%d registros)' % (os.path.basename(ruta), len(g)))


def cargar(nombre):
    import geopandas as gpd
    g = gpd.read_file(PREV[nombre])
    if g.crs is None or g.crs.to_epsg() != EPSG_METRICO:
        g = g.to_crs(CRS_METRICO)
    return g


def glebas():
    """dict {'G1': geom, 'G2': geom, 'IMOVEL': union} en 31982."""
    from shapely.ops import unary_union
    g = cargar('glebas')
    d = {str(r.gleba): r.geometry for _, r in g.iterrows()}
    d['IMOVEL'] = unary_union(list(d.values()))
    return d


def poly_only(g):
    from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
    from shapely.ops import unary_union
    if g is None or g.is_empty:
        return Polygon()
    if isinstance(g, (Polygon, MultiPolygon)):
        return g
    if isinstance(g, GeometryCollection):
        return unary_union([x for x in g.geoms if isinstance(x, (Polygon, MultiPolygon))]) if any(
            isinstance(x, (Polygon, MultiPolygon)) for x in g.geoms) else Polygon()
    return Polygon()


def ha(g, dec=3):
    return round(poly_only(g).area / 1e4, dec)


def cobertura():
    """Huella de datos del vuelo (de ortho_01): dict con poligonos de ortofoto y DTM."""
    ruta = R('cobertura_vuelo.json')
    return leer_json(ruta) if os.path.exists(ruta) else None


class Cronometro:
    def __init__(self, rotulo):
        self.r = rotulo
    def __enter__(self):
        self.t = time.time(); log('[%s]' % self.r); return self
    def __exit__(self, *a):
        log('  (%s: %.0f s)' % (self.r, time.time() - self.t))
