# -*- coding: utf-8 -*-
"""Piezas compartidas de la etapa DRON POR IMOVEL (dron_01..dron_04).

    from dron_00_comun import *

REGLAS DEL CLIENTE (2026-09-06) que mandan sobre todo lo anterior:
 1. DOS INMUEBLES SEPARADOS, segun los 2 poligonos de Mapeo_de_Area_Nativa.geojson (EPSG:31982):
      - poligono grande  -> 'santo_antonio'  "Fazenda Santo Antonio" (144,21 ha)
      - poligono chico   -> 'seis_alqueires' "Area dos 6 alqueires" (13,54 ha = 5,6 alq. paulistas)
    Todo se calcula por inmueble; NADA se suma entre ellos.
 2. SOLO IMAGEN DE DRON (22-mai-2026, ODM). Nada de Sentinel-2 ni de productos satelitales para
    medir: ni cobertura, ni agua, ni DEM de calibracion (el DTM/DSM se usan en el datum del vuelo,
    sin correccion FABDEM). Donde el dron no cubre se reporta "sem cobertura do drone: nao avaliado".
    Los ejes de los arroios y la nascente son datos oficiales (FBDS/IAT): se usan como REFERENCIA
    del eje (bajo dosel el dron no ve el cauce), y se dice.
 3. Cruce con CAR (replica SICAR en el IAT) y outorga SIGARH, re-consultados HOY (dron_04).

GRILLA POR INMUEBLE: bbox del poligono + 10 m, origen alineado a 10 m; pixel 0,10 m y 0,25 m
(la de 0,25 anida en la de 0,10 porque 10 m es multiplo de ambas). Mascara EXACTA del poligono
(all_touched=False), sin buffer: fuera del poligono todo es nodata.

Los rasteres originales (2,3 GB / 1,1 GB) se leen por FRANJAS con out_shape (GDAL usa los
overviews) y se escriben franja a franja: nunca un read() completo.
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
                   leer_json, guardar_json, log)
# 2026-09-07: o cliente corrigiu o poligono dos 6 alqueires (alargado a leste ate 5,8 alqueires = 14,036 ha);
# o arquivo original esta bloqueado por outro programa -> a cadeia usa a copia v2.
PROPIEDAD_GEOJSON = os.path.join(PROYECTO, 'Mapeo_de_Area_Nativa_v2_5.8alq.geojson')

HOY = '2026-09-06'
FECHA_VUELO = '2026-05-22'
CRS_FUENTE = 'EPSG:32722'      # WGS84/UTM 22S del ODM; verificado 32722 -> 31982 = 0,0 m: se ETIQUETA 31982
NODATA_F = -9999.0

# --- rutas -----------------------------------------------------------------------------------
DRONE = r'D:\PIXADVISOR\Vuelos-Drone\Ortofoto-S.A'
ORTHO_SRC = os.path.join(DRONE, 'odm_orthophoto.tif')
DSM_SRC = os.path.join(DRONE, 'dsm.tif')
DTM_SRC = os.path.join(DRONE, 'dtm.tif')
ANALISIS = os.path.join(PROYECTO, '02_ANALISIS')
HIDRO_PRO = os.path.join(ANALISIS, 'hidrologia_pro')
SALIDA_RAIZ = os.path.join(PROYECTO, '06_DRONE_POR_IMOVEL')
LEGISLACION = os.path.join(CODIGO, 'legislacion')
PARAMETROS_LEGALES = os.path.join(LEGISLACION, 'parametros_legales.json')
DATOS_EXT = os.path.join(CODIGO, 'datos_externos')
GOV_PRO = os.path.join(DATOS_EXT, 'gov_pro')

# datos OFICIALES de referencia (gobierno). Ninguno es satelite propio: son cartografia oficial.
OFICIAL = {
    'hidro': os.path.join(ANALISIS, 'hidrografia_consolidada.geojson'),      # FBDS/IAT 1:25.000 (eje de los arroios)
    'nascentes': os.path.join(ANALISIS, 'nascentes_consolidadas.geojson'),   # FBDS 306158
    'massas_fbds': os.path.join(DATOS_EXT, 'IAT_FBDS_massas_dagua.geojson'), # FBDS 2013 (solo para LOCALIZAR la represa)
    'car': os.path.join(HIDRO_PRO, 'CAR_propriedade_e_vizinhos.geojson'),    # CAR (replica IAT, bajada 2026-09-06)
    'outorgas': os.path.join(GOV_PRO, 'IAT_outorgas_sigarh.geojson'),
}

IMOVEIS = {
    'santo_antonio': {'nome': 'Fazenda Santo Antonio', 'rotulo': 'Fazenda Santo Antônio', 'area_esperada_ha': 144.21,
                      'car': 'PR-4124301-F127CD1E73FA4B9DB4FA0CC2B3FC1E14', 'car_relacao': 'CAR do proprio imovel'},
    'seis_alqueires': {'nome': 'Area dos 6 alqueires', 'rotulo': 'Área dos 6 alqueires', 'area_esperada_ha': 14.036,
                       'car': 'PR-4124301-5223911747FD4B878118F1823D609DD6', 'car_relacao': 'CAR de ORIGEM (imovel maior de 94 ha do qual foi desmembrada)'},
}
# MEDIDO 2026-09-06 23:10: el cliente EDITO el poligono chico en Mapeo_de_Area_Nativa.geojson y le quito la
# punta norte (2,294 ha, N > 7403886): el poligono del archivo mide 11,255 ha (4,65 alq.), no los 13,54 ha
# (5,6 alq.) del pedido. El archivo MANDA para la geometria; los 13,54 ha se reportan como "area informada
# pelo cliente" y la punta norte (poligono anterior - poligono actual) como "a conferir na escritura".
AREA_INFORMADA_CLIENTE = {'santo_antonio': 144.21, 'seis_alqueires': 14.04}   # 2026-09-07: 5,8 alqueires (cliente)
POLIGONO_ANTERIOR_G2 = os.path.join(ANALISIS, 'gleba_limites.geojson')   # G2 = 13,538 ha (version 13:41)
ORDEM_IMOVEIS = ['santo_antonio', 'seis_alqueires']
PONTA_NORTE = 'ponta_norte_ref'    # pseudo-inmueble de REFERENCIA (fuera de los dos inmuebles): la punta removida
ALQUEIRE_PAULISTA_HA = 2.42


def salida(imovel, nombre=None):
    d = os.path.join(SALIDA_RAIZ, 'seis_alqueires', 'ponta_norte_referencia') if imovel == PONTA_NORTE else os.path.join(SALIDA_RAIZ, imovel)
    os.makedirs(d, exist_ok=True)
    return d if nombre is None else os.path.join(d, nombre)


def R(imovel, nombre, res=None):
    """Ruta de un producto del inmueble; `res` agrega el sufijo _0_10m / _0_25m."""
    if res is None:
        return salida(imovel, nombre)
    suf = {0.1: '0_10m', 0.25: '0_25m', 0.5: '0_50m'}[res]
    base, ext = os.path.splitext(nombre)
    return salida(imovel, '%s_%s%s' % (base, suf, ext))


# --- los dos inmuebles ------------------------------------------------------------------------
_IMOVEIS_CACHE = None


def imoveis():
    """dict imovel -> shapely (31982). El grande es Santo Antonio, el chico los 6 alqueires."""
    global _IMOVEIS_CACHE
    if _IMOVEIS_CACHE is not None:
        return _IMOVEIS_CACHE
    import shapely
    from shapely.geometry import shape
    gj = leer_json(PROPIEDAD_GEOJSON)
    crs_decl = (gj.get('crs') or {}).get('properties', {}).get('name', '')
    if str(EPSG_METRICO) not in crs_decl:
        raise RuntimeError('El GeoJSON declara CRS "%s"; se esperaba EPSG:%d' % (crs_decl, EPSG_METRICO))
    geoms = [shapely.force_2d(shape(f['geometry'])).buffer(0) for f in gj['features']]
    if len(geoms) != 2:
        raise RuntimeError('se esperaban 2 poligonos (2 inmuebles), hay %d' % len(geoms))
    geoms.sort(key=lambda g: -g.area)
    out = {'santo_antonio': geoms[0], 'seis_alqueires': geoms[1]}
    for k, g in out.items():
        a = g.area / 1e4
        if abs(a - IMOVEIS[k]['area_esperada_ha']) > 0.05:
            log('  AVISO %s: o poligono do GeoJSON mede %.3f ha e o pedido diz %.2f ha: MANDA O ARQUIVO; '
                'a diferenca se reporta explicitamente' % (k, a, IMOVEIS[k]['area_esperada_ha']))
        if g.intersects(out['santo_antonio']) and k != 'santo_antonio' and g.intersection(out['santo_antonio']).area > 1:
            raise RuntimeError('los dos inmuebles se solapan %.1f m2' % g.intersection(out['santo_antonio']).area)
    _IMOVEIS_CACHE = out
    # pseudo-inmueble de referencia: la punta norte que el cliente quito de los 6 alqueires (NO es inmueble)
    try:
        out[PONTA_NORTE] = _ponta_norte(out['seis_alqueires'])
    except Exception as e:   # noqa: BLE001
        log('  AVISO: no se pudo construir la punta norte de referencia: %s' % e)
    return out


def _ponta_norte(g2_actual):
    import geopandas as gpd
    g = gpd.read_file(POLIGONO_ANTERIOR_G2)
    if g.crs is None or g.crs.to_epsg() != EPSG_METRICO:
        g = g.to_crs(CRS_METRICO)
    ant = g[g.gleba.astype(str) == 'G2'].geometry.iloc[0].buffer(0)
    return poly_only(ant.difference(g2_actual)).buffer(0)


def area_ha(imovel):
    return round(imoveis()[imovel].area / 1e4, 3)


def ponta_norte_removida():
    """Poligono anterior de los 6 alqueires (13,54 ha, gleba_limites.geojson) MENOS el poligono actual:
    la punta norte que el cliente quito del inmueble (2,29 ha). Se reporta aparte, no se computa."""
    return imoveis()[PONTA_NORTE]


# --- grilla por inmueble ----------------------------------------------------------------------------
MARGEN_M = 10
ALINEACION_M = 10


def grilla(imovel, res):
    """(transform, height, width, bounds) de la grilla del inmueble a resolucion `res`."""
    from rasterio.transform import from_origin
    x0, y0, x1, y1 = imoveis()[imovel].bounds
    x0 = np.floor((x0 - MARGEN_M) / ALINEACION_M) * ALINEACION_M
    y0 = np.floor((y0 - MARGEN_M) / ALINEACION_M) * ALINEACION_M
    x1 = np.ceil((x1 + MARGEN_M) / ALINEACION_M) * ALINEACION_M
    y1 = np.ceil((y1 + MARGEN_M) / ALINEACION_M) * ALINEACION_M
    w = int(round((x1 - x0) / res))
    h = int(round((y1 - y0) / res))
    return from_origin(x0, y1, res, res), h, w, (float(x0), float(y0), float(x1), float(y1))


def rasterizar(imovel, geoms, res, valor=1, all_touched=False, dtype='uint8'):
    from rasterio.features import rasterize
    tr, h, w, _ = grilla(imovel, res)
    if not isinstance(geoms, (list, tuple)):
        geoms = [geoms]
    shp = [g if isinstance(g, tuple) else (g, valor) for g in geoms]
    shp = [(g, v) for g, v in shp if g is not None and not g.is_empty]
    if not shp:
        return np.zeros((h, w), dtype=dtype)
    return rasterize(shp, out_shape=(h, w), transform=tr, fill=0, dtype=dtype, all_touched=all_touched)


def mascara(imovel, res):
    """Mascara EXACTA del poligono del inmueble (bool 2D), sin buffer."""
    return rasterizar(imovel, [imoveis()[imovel]], res).astype(bool)


# --- lectura por franjas de las fuentes 5 cm --------------------------------------------------------------
def abrir_fuente(src_path):
    import rasterio
    return rasterio.open(src_path)


def leer_ventana_decimada(src, bounds, factor, bandas, resampling, dtype='float32'):
    """Lee de `src` (abierto) la ventana que cubre `bounds` (31982 == 32722), decimada por `factor`
    (entero) con out_shape (GDAL usa el overview mas cercano). Devuelve (arr (nb,h,w), transform)
    o (None, None) si la ventana no toca la fuente. Con dtype float el nodata sale como NaN."""
    from rasterio.windows import Window, from_bounds
    x0, y0, x1, y1 = bounds
    sx0, sy0, sx1, sy1 = src.bounds
    ix0, iy0, ix1, iy1 = max(x0, sx0), max(y0, sy0), min(x1, sx1), min(y1, sy1)
    if ix1 <= ix0 or iy1 <= iy0:
        return None, None
    win = from_bounds(ix0, iy0, ix1, iy1, src.transform)
    c0 = int(np.floor(win.col_off / factor)) * factor
    r0 = int(np.floor(win.row_off / factor)) * factor
    c1 = int(np.ceil((win.col_off + win.width) / factor)) * factor
    r1 = int(np.ceil((win.row_off + win.height) / factor)) * factor
    c0, r0 = max(c0, 0), max(r0, 0)
    c1, r1 = min(c1, src.width), min(r1, src.height)
    if c1 <= c0 or r1 <= r0:
        return None, None
    w_out, h_out = (c1 - c0) // factor, (r1 - r0) // factor
    if w_out <= 0 or h_out <= 0:
        return None, None
    win = Window(c0, r0, w_out * factor, h_out * factor)
    nd = src.nodata
    a = src.read(bandas, window=win, out_shape=(len(bandas), h_out, w_out), resampling=resampling,
                 masked=(nd is not None))
    if nd is not None:
        a = np.ma.filled(a.astype('float32'), np.nan)
    a = a.astype(dtype)
    from rasterio.transform import Affine
    tr = src.window_transform(win) * Affine.scale(factor, factor)
    return a, tr


def reproyectar_a(imovel, arr, tr_src, res, resampling, nodata=np.nan, dtype='float32', filas=None):
    """Reproyecta (nb,h,w) o (h,w) de la fuente (tratada como 31982: dx 32722->31982 = 0,0 m
    verificado) a la grilla del inmueble; `filas=(r0,r1)` limita a una franja de la grilla."""
    from rasterio.warp import reproject
    from rasterio.crs import CRS
    from rasterio.transform import from_origin
    tr, h, w, _ = grilla(imovel, res)
    if filas is not None:
        r0, r1 = filas
        tr = from_origin(tr.c, tr.f + r0 * tr.e, res, res)
        h = r1 - r0
    a = np.asarray(arr)
    if a.ndim == 2:
        a = a[None]
    dst = np.full((a.shape[0], h, w), nodata, dtype=dtype)
    crs = CRS.from_epsg(EPSG_METRICO)
    for i in range(a.shape[0]):
        src_i = a[i]
        src_nd = np.nan if np.issubdtype(src_i.dtype, np.floating) else None
        reproject(src_i, dst[i], src_transform=tr_src, src_crs=crs, src_nodata=src_nd,
                  dst_transform=tr, dst_crs=crs, dst_nodata=nodata, resampling=resampling, num_threads=4)
    return dst


# --- escritura / lectura de productos ---------------------------------------------------------------------
def perfil(imovel, res, count, dtype, nodata):
    import rasterio
    from rasterio.crs import CRS
    tr, h, w, _ = grilla(imovel, res)
    return {'driver': 'GTiff', 'height': h, 'width': w, 'count': count, 'dtype': dtype,
            'crs': CRS.from_epsg(EPSG_METRICO), 'transform': tr, 'compress': 'DEFLATE',
            'predictor': 2 if dtype == 'float32' else 1, 'tiled': True, 'blockxsize': 512,
            'blockysize': 512, 'nodata': nodata, 'BIGTIFF': 'IF_SAFER'}


def abrir_salida(imovel, ruta, res, count, dtype, nodata, bandas=None, alpha=False, tags=None):
    """Abre un GeoTIFF de salida en la grilla del inmueble para escribir por franjas."""
    import rasterio
    from rasterio.enums import ColorInterp
    if os.path.exists(ruta):
        os.remove(ruta)
    dst = rasterio.open(ruta, 'w', **perfil(imovel, res, count, dtype, nodata))
    if bandas:
        for i, b in enumerate(bandas, 1):
            dst.set_band_description(i, b)
    if alpha and count == 4:
        dst.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue, ColorInterp.alpha]
    dst.update_tags(fuente='voo drone %s ODM, EPSG:32722 == EPSG:31982 (dx=0,0 m)' % FECHA_VUELO,
                    crs_etiqueta=CRS_METRICO, imovel=IMOVEIS.get(imovel, {}).get('nome', 'ponta norte removida (referencia)'),
                    mascara='poligono exato do imovel (sem buffer); fora = nodata', **(tags or {}))
    return dst


def cerrar_salida(dst, ruta, res, overviews=True, dtype='float32'):
    from rasterio.enums import Resampling
    if overviews:
        dst.build_overviews([2, 4, 8, 16], Resampling.average if dtype == 'float32' else Resampling.nearest)
    w, h = dst.width, dst.height
    dst.close()
    log('  escrito %s (%.1f MB, %dx%d px, %.2f m)' % (os.path.basename(ruta), os.path.getsize(ruta) / 1e6, w, h, res))


def escribir(imovel, ruta, arr, res, dtype='float32', nodata=NODATA_F, bandas=None, tags=None, alpha=False, overviews=True):
    """Escribe un arreglo completo (nb,h,w) o (h,w) en la grilla del inmueble."""
    tr, h, w, _ = grilla(imovel, res)
    a = np.asarray(arr)
    if a.ndim == 2:
        a = a[None]
    assert a.shape[1:] == (h, w), (a.shape, (h, w))
    if np.issubdtype(a.dtype, np.floating) and nodata is not None:
        a = np.where(np.isfinite(a), a, nodata)
    dst = abrir_salida(imovel, ruta, res, a.shape[0], dtype, nodata, bandas, alpha, tags)
    dst.write(a.astype(dtype))
    cerrar_salida(dst, ruta, res, overviews, dtype)
    return ruta


def leer(ruta, banda=None, nan=True):
    """Lee un producto por inmueble completo. float -> NaN en nodata."""
    import rasterio
    with rasterio.open(ruta) as src:
        a = src.read(banda) if banda else src.read()
        nd = src.nodata
        if nan and np.issubdtype(a.dtype, np.floating) and nd is not None:
            a = np.where(a == nd, np.nan, a)
        return a, src.transform


def verificar_arr(a, nombre, mascara_=None, unidades='', permitir_vacia=False):
    """min/max/media/%nodata de un arreglo 2D. Falla si esta vacio o degenerado (salvo permitir_vacia)."""
    a = np.asarray(a)
    if a.ndim == 3:
        return [verificar_arr(a[i], '%s[b%d]' % (nombre, i + 1), mascara_, unidades, permitir_vacia) for i in range(a.shape[0])]
    if np.issubdtype(a.dtype, np.floating):
        valido = np.isfinite(a) & (a != NODATA_F)
    else:
        valido = np.ones(a.shape, bool)
    if mascara_ is not None:
        tot = int(mascara_.sum())
        valido = valido & mascara_
    else:
        tot = int(a.size)
    n = int(valido.sum())
    if n == 0:
        if permitir_vacia:
            log('    %-30s n=0 (VACIA: sem dado nesta area)' % nombre)
            return {'n': 0, 'min': None, 'max': None, 'media': None, 'pct_nodata': 100.0}
        raise RuntimeError('capa %s VACIA (n=0)' % nombre)
    v = a[valido].astype('float64')
    mn, mx, me = float(v.min()), float(v.max()), float(v.mean())
    pct_nd = 100.0 * (1 - n / tot) if tot else 0.0
    aviso = '  <-- DEGENERADA' if mx == mn else ''
    log('    %-30s n=%-10d min=%10.3f max=%10.3f media=%10.3f nodata=%5.1f%% %s%s'
        % (nombre, n, mn, mx, me, pct_nd, unidades, aviso))
    if mx == mn and not permitir_vacia:
        raise RuntimeError('capa %s degenerada (min == max == %s)' % (nombre, mn))
    return {'n': n, 'min': round(mn, 4), 'max': round(mx, 4), 'media': round(me, 4), 'pct_nodata': round(pct_nd, 2)}


# --- vectores -----------------------------------------------------------------------------------------------
def vectorizar(imovel, mask, res, min_area_m2=0.0, campos=None):
    """bool 2D -> GeoDataFrame de poligonos (31982)."""
    import geopandas as gpd
    from rasterio.features import shapes
    from shapely.geometry import shape
    tr, h, w, _ = grilla(imovel, res)
    m = mask.astype('uint8')
    polys = [shape(g) for g, v in shapes(m, mask=m.astype(bool), transform=tr, connectivity=8) if v == 1]
    polys = [p for p in polys if p.area >= min_area_m2]
    gdf = gpd.GeoDataFrame({'area_ha': [round(p.area / 1e4, 4) for p in polys]}, geometry=polys, crs=CRS_METRICO)
    for k, v in (campos or {}).items():
        gdf[k] = v
    return gdf


def guardar_gdf(gdf, ruta, wgs84=True):
    """GeoJSON en 31982 (etiqueta) + copia _wgs84 para QGIS/Google Earth."""
    g = gdf.copy()
    r84 = ruta.replace('.geojson', '_wgs84.geojson')
    if len(g) == 0:
        for r_ in (ruta, r84):
            if os.path.exists(r_):
                os.remove(r_)
        log('  AVISO: %s sin registros (no se escribe)' % os.path.basename(ruta))
        return
    for c in g.columns:
        if c != 'geometry' and g[c].dtype == object:
            g[c] = g[c].apply(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
    for r_ in (ruta, r84):
        if os.path.exists(r_):
            os.remove(r_)
    g.to_file(ruta, driver='GeoJSON')
    if wgs84:
        g.to_crs('EPSG:4326').to_file(r84, driver='GeoJSON')
    log('  -> %s (%d registros)' % (os.path.basename(ruta), len(g)))


def cargar_oficial(nombre):
    import geopandas as gpd
    g = gpd.read_file(OFICIAL[nombre])
    if g.crs is None or g.crs.to_epsg() != EPSG_METRICO:
        g = g.to_crs(CRS_METRICO)
    return g


def poly_only(g):
    from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
    from shapely.ops import unary_union
    if g is None or g.is_empty:
        return Polygon()
    if isinstance(g, (Polygon, MultiPolygon)):
        return g
    if isinstance(g, GeometryCollection):
        partes = [x for x in g.geoms if isinstance(x, (Polygon, MultiPolygon))]
        return unary_union(partes) if partes else Polygon()
    return Polygon()


def ha(g, dec=3):
    return round(poly_only(g).area / 1e4, dec)


def no_vazio(g):
    """GEOS revienta con overlays sobre geometria VACIA: marcador de 0,0003 m2 lejos del area."""
    from shapely.geometry import Point
    return g if (g is not None and not g.is_empty) else Point(0, 0).buffer(0.01)


def std_local(a, size):
    from scipy import ndimage as ndi
    m1 = ndi.uniform_filter(a, size)
    m2 = ndi.uniform_filter(a * a, size)
    return np.sqrt(np.maximum(m2 - m1 * m1, 0)).astype('float32')


def rasgos_rgb(rgba):
    """L, ExG, S, BR, TEX9 (std local 9 px de L) de un RGBA uint8 (4,h,w)."""
    Rr, Gg, Bb = [rgba[i].astype('float32') for i in range(3)]
    L = 0.299 * Rr + 0.587 * Gg + 0.114 * Bb
    ExG = 2 * Gg - Rr - Bb
    mx = np.maximum(np.maximum(Rr, Gg), Bb)
    mn = np.minimum(np.minimum(Rr, Gg), Bb)
    S = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).astype('float32')
    BR = ((Bb - Rr) / np.maximum(Bb + Rr, 1)).astype('float32')
    TEX9 = std_local(L, 9)
    return Rr, Gg, Bb, L, ExG, S, BR, TEX9


# --- recortes por inmueble desde las fuentes 5 cm (usados por dron_01 y por la referencia de la punta norte) ---
FRANJA_M = 100.0


def recortar_ortofoto(imovel, res, factor):
    """RGBA uint8 a `res` desde la ortofoto 5 cm, por franjas; alpha 0 fuera del poligono o sin dato."""
    from rasterio.enums import Resampling
    tr, H, W, B = grilla(imovel, res)
    m = mascara(imovel, res)
    ruta = R(imovel, 'ortofoto_rgba.tif', res)
    dst = abrir_salida(imovel, ruta, res, 4, 'uint8', None, bandas=['R', 'G', 'B', 'alpha'], alpha=True,
                       tags={'pixel_m': str(res), 'decimacion': 'average x%d desde 5 cm' % factor})
    filas_franja = int(round(FRANJA_M / res))
    acc = {b: {'n': 0, 'sum': 0.0, 'min': 255, 'max': 0} for b in 'RGB'}
    n_valido = 0
    n_franjas = 0
    with abrir_fuente(ORTHO_SRC) as src:
        r0 = 0
        while r0 < H:
            r1 = min(H, r0 + filas_franja)
            y1 = tr.f + r0 * tr.e
            y0 = tr.f + r1 * tr.e
            bounds = (B[0] - 1, y0 - 1, B[2] + 1, y1 + 1)
            a, tr_s = leer_ventana_decimada(src, bounds, factor, [1, 2, 3, 4], Resampling.average, dtype='float32')
            franja = np.zeros((4, r1 - r0, W), 'uint8')
            if a is not None:
                rp = reproyectar_a(imovel, a, tr_s, res, Resampling.bilinear, nodata=np.nan, dtype='float32', filas=(r0, r1))
                valido = np.isfinite(rp[3]) & (rp[3] >= 200) & m[r0:r1]
                for i in range(3):
                    franja[i] = np.where(valido, np.clip(np.round(np.where(np.isfinite(rp[i]), rp[i], 0)), 0, 255), 0).astype('uint8')
                franja[3] = (valido * 255).astype('uint8')
                for i, b in enumerate('RGB'):
                    v = franja[i][valido]
                    if v.size:
                        acc[b]['n'] += int(v.size); acc[b]['sum'] += float(v.sum())
                        acc[b]['min'] = min(acc[b]['min'], int(v.min())); acc[b]['max'] = max(acc[b]['max'], int(v.max()))
                n_valido += int(valido.sum())
            dst.write(franja, window=((r0, r1), (0, W)))
            r0 = r1
            n_franjas += 1
    cerrar_salida(dst, ruta, res, overviews=True, dtype='uint8')
    st = {b: {'n': acc[b]['n'], 'min': acc[b]['min'], 'max': acc[b]['max'],
              'media': round(acc[b]['sum'] / max(acc[b]['n'], 1), 2)} for b in 'RGB'}
    for b in 'RGB':
        if st[b]['n'] == 0 or st[b]['min'] == st[b]['max']:
            raise RuntimeError('%s ortofoto %.2f m banda %s vacia o degenerada: %s' % (imovel, res, b, st[b]))
        log('    orto_%s %.2f m  n=%-10d min=%3d max=%3d media=%.2f' % (b, res, st[b]['n'], st[b]['min'], st[b]['max'], st[b]['media']))
    log('  %d franjas; cobertura ortofoto %.2f m: %.3f ha de %.3f (%.2f %%)' % (n_franjas, res, n_valido * res * res / 1e4, m.sum() * res * res / 1e4, 100.0 * n_valido / max(m.sum(), 1)))
    return st, n_valido * res * res / 1e4


def recortar_elevacion(imovel, src_path, res, factor):
    """DSM o DTM float32 a `res`, mascara exacta; devuelve el arreglo (h,w) con NaN fuera / sin dato."""
    from rasterio.enums import Resampling
    tr, H, W, B = grilla(imovel, res)
    m = mascara(imovel, res)
    out = np.full((H, W), np.nan, 'float32')
    filas_franja = int(round(400.0 / res))
    with abrir_fuente(src_path) as src:
        r0 = 0
        while r0 < H:
            r1 = min(H, r0 + filas_franja)
            y1 = tr.f + r0 * tr.e
            y0 = tr.f + r1 * tr.e
            a, tr_s = leer_ventana_decimada(src, (B[0] - 1, y0 - 1, B[2] + 1, y1 + 1), factor, [1], Resampling.average, dtype='float32')
            if a is not None:
                rp = reproyectar_a(imovel, a, tr_s, res, Resampling.bilinear, nodata=np.nan, dtype='float32', filas=(r0, r1))[0]
                out[r0:r1] = np.where(m[r0:r1], rp, np.nan)
            r0 = r1
    return out


class Cronometro:
    def __init__(self, rotulo):
        self.r = rotulo

    def __enter__(self):
        self.t = time.time()
        log('[%s]' % self.r)
        return self

    def __exit__(self, *a):
        log('  (%s: %.0f s)' % (self.r, time.time() - self.t))


def cabecera(script):
    log('=' * 78)
    log('%s  voo %s  ->  %s' % (script, FECHA_VUELO, SALIDA_RAIZ))
    log('=' * 78)
    for k in ORDEM_IMOVEIS:
        log('  %-15s %-28s %8.3f ha  CAR %s' % (k, IMOVEIS[k]['nome'], area_ha(k), IMOVEIS[k]['car']))
    if PONTA_NORTE in imoveis():
        log('  %-15s %-28s %8.3f ha  (REFERENCIA: punta norte removida do poligono dos 6 alqueires; NAO e inmueble)'
            % (PONTA_NORTE, 'ponta norte (a conferir)', area_ha(PONTA_NORTE)))
