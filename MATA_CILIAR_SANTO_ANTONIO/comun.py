# -*- coding: utf-8 -*-
"""Piezas compartidas por los scripts gee_0X de MATA_CILIAR_SANTO_ANTONIO.

    from comun import *

QUE HAY ACA
-----------
- Rutas del proyecto (codigo y datos).
- La propiedad como shapely en EPSG:31982 (SIRGAS 2000 / UTM 22S) y los dos AOI
  (+1500 m para todo, +3000 m para el DEM), con el bbox ALINEADO a multiplos de
  90 m (mcm de 10/30/90): el origen es multiplo de 10 y las capas de 30 y 90 m
  anidan exactamente en el grid de 10 m; se apilan sin remuestrear.
- `descargar_geotiff`: getDownloadURL con crs+crs_transform fijos, tileado si
  la pieza excede el limite de ~48 MB, union con rasterio.merge, reescritura
  con nombres de banda, nodata y LZW.
- `verificar_raster`: n, min, max, media y % nodata de CADA banda. Se llama
  despues de cada descarga. Una capa degenerada (min ~ max) se avisa fuerte.
- `safe_getInfo`: todo getInfo con timeout; un getInfo colgado no se nota.

CONVENCIONES QUE VIENEN DE PIX_ALERTA
-------------------------------------
- `unmask(valor, False)`: el default sameFootprint=True no rellena fuera de la
  huella del granulo y la cobertura sale inflada (medido: astilla del 8,2% con
  cobertura reportada 0,972). Aca la huella se mide EXPLICITAMENTE con la
  mascara del granulo rellenada con False.
- Ningun urlretrieve: urlopen(timeout=...).
"""
import concurrent.futures as _fut
import io
import json
import os
import time
import urllib.request
import warnings
import zipfile

import numpy as np

warnings.filterwarnings('ignore', category=DeprecationWarning)

# --- rutas -----------------------------------------------------------------
CODIGO = os.path.dirname(os.path.abspath(__file__))
PROYECTO = os.path.join(os.path.expanduser('~'), 'Desktop',
                        'Proyecto-Mata_Siliar-Fazenda_Santo_Antonio')
SALIDA = os.path.join(PROYECTO, '01_DATOS_SATELITE')
PROPIEDAD_GEOJSON = os.path.join(PROYECTO, 'Mapeo_de_Area_Nativa.geojson')

EPSG_METRICO = 31982          # SIRGAS 2000 / UTM 22S: todo lo metrico va aca
CRS_METRICO = 'EPSG:%d' % EPSG_METRICO
PROYECTO_GEE = 'ee-gisagronomico'
EXPANSION_AOI_M = 1500        # cursos de agua que generan APP pueden nacer afuera
EXPANSION_DEM_M = 3000        # cuenca aguas arriba para acumulacion de flujo
GRID_M = 10                   # requisito: origen multiplo de 10 m
ALINEACION_M = 90             # bbox alineado a 90 = mcm(10, 30, 90). MEDIDO 2026-09-06:
                              # getDownloadURL ancla el grid en multiplos de la ESCALA desde
                              # el origen 0 e ignora la traslacion de crs_transform; con un
                              # bbox multiplo de 10 las capas de 30/90 m volvian corridas
                              # 10-20 m. Con 90 todas anidan en el grid de 10 m.
TIMEOUT_GETINFO = 180
TIMEOUT_DESCARGA = 300
LIMITE_DESCARGA_BYTES = 50331648   # 48 MB duros de getDownloadURL (medido)
NODATA_FLOAT = -9999.0

HOY = '2026-09-06'


def log(msg=''):
    print(msg, flush=True)


def guardar_json(ruta, obj):
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    log('  -> %s' % ruta)


def leer_json(ruta):
    with open(ruta, encoding='utf-8') as fh:
        return json.load(fh)


# --- Earth Engine -----------------------------------------------------------
_EE_LISTO = False


def inicializar_ee():
    global _EE_LISTO
    import ee
    if not _EE_LISTO:
        ee.Initialize(project=PROYECTO_GEE)
        _EE_LISTO = True
    return ee


def safe_getInfo(obj, timeout=TIMEOUT_GETINFO, descripcion='getInfo'):
    """getInfo con timeout real. Un getInfo colgado no falla: se queda mudo."""
    ex = _fut.ThreadPoolExecutor(max_workers=1)
    fut = ex.submit(obj.getInfo)
    try:
        return fut.result(timeout=timeout)
    except _fut.TimeoutError:
        raise TimeoutError('%s: sin respuesta de GEE en %d s' % (descripcion, timeout))
    finally:
        ex.shutdown(wait=False)


# --- geometria de la propiedad y AOI ----------------------------------------

def _alinear_bbox(bounds, margen_m, grid=ALINEACION_M):
    """Expande el bbox hacia afuera hasta multiplos de `grid` (90 m; ver ALINEACION_M)."""
    x0, y0, x1, y1 = bounds
    x0 = np.floor((x0 - margen_m) / grid) * grid
    y0 = np.floor((y0 - margen_m) / grid) * grid
    x1 = np.ceil((x1 + margen_m) / grid) * grid
    y1 = np.ceil((y1 + margen_m) / grid) * grid
    return (float(x0), float(y0), float(x1), float(y1))


def cargar_propiedad():
    """Devuelve dict con la propiedad en 31982 y los dos AOI alineados.

    Fuerza 2D (shapely.force_2d) por si el GeoJSON trajera Z. Verifica el CRS
    declarado en el archivo: si no dice 31982, revienta — reproyectar a ciegas
    un archivo en otro CRS daria coordenadas validas en el lugar equivocado.
    """
    import shapely
    from shapely.geometry import shape
    from shapely.ops import unary_union
    gj = leer_json(PROPIEDAD_GEOJSON)
    crs_decl = (gj.get('crs') or {}).get('properties', {}).get('name', '')
    if str(EPSG_METRICO) not in crs_decl:
        raise RuntimeError('El GeoJSON declara CRS "%s"; se esperaba EPSG:%d'
                           % (crs_decl, EPSG_METRICO))
    geoms = [shapely.force_2d(shape(f['geometry'])) for f in gj['features']]
    for g in geoms:
        if not g.is_valid:
            raise RuntimeError('geometria invalida en el GeoJSON: %s'
                               % shapely.validation.explain_validity(g))
    prop = unary_union(geoms)
    area_ha = prop.area / 1e4
    if not (150 < area_ha < 165):
        raise RuntimeError('area de la propiedad %.2f ha, se esperaban ~157,75 ha: '
                           'el CRS o la geometria no son los que se creia' % area_ha)
    b = prop.bounds
    return {
        'geom': prop,
        'n_poligonos': len(geoms),
        'area_ha': area_ha,
        'bounds_31982': b,
        'aoi_31982': _alinear_bbox(b, EXPANSION_AOI_M),
        'aoi_dem_31982': _alinear_bbox(b, EXPANSION_DEM_M),
    }


def a_wgs84(geom_31982):
    from pyproj import Transformer
    from shapely.ops import transform
    t = Transformer.from_crs(CRS_METRICO, 'EPSG:4326', always_xy=True)
    return transform(t.transform, geom_31982)


def ee_geom(geom_31982):
    """shapely 31982 -> ee.Geometry en WGS84 (planar, sin geodesicas)."""
    ee = inicializar_ee()
    from shapely.geometry import mapping
    return ee.Geometry(mapping(a_wgs84(geom_31982)), 'EPSG:4326', False)


def ee_bbox(bbox_31982):
    """bbox (x0,y0,x1,y1) en 31982 -> ee.Geometry.Rectangle expresado en 31982."""
    ee = inicializar_ee()
    x0, y0, x1, y1 = bbox_31982
    return ee.Geometry.Rectangle([x0, y0, x1, y1], CRS_METRICO, False)


def describir_aoi(p):
    x0, y0, x1, y1 = p['aoi_31982']
    log('Propiedad: %d poligonos, %.2f ha, bounds 31982 = %s'
        % (p['n_poligonos'], p['area_ha'], tuple(round(v, 1) for v in p['bounds_31982'])))
    log('AOI (+%d m, alineado a %d m): x %.0f..%.0f  y %.0f..%.0f  (%.2f x %.2f km)'
        % (EXPANSION_AOI_M, ALINEACION_M, x0, x1, y0, y1, (x1 - x0) / 1e3, (y1 - y0) / 1e3))
    x0, y0, x1, y1 = p['aoi_dem_31982']
    log('AOI DEM (+%d m): x %.0f..%.0f  y %.0f..%.0f  (%.2f x %.2f km)'
        % (EXPANSION_DEM_M, x0, x1, y0, y1, (x1 - x0) / 1e3, (y1 - y0) / 1e3))


# --- descarga ----------------------------------------------------------------

def _bajar_url(url, timeout=TIMEOUT_DESCARGA):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        data = r.read()
    if data[:2] == b'PK':                       # algunos vienen zip
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            nombres = [n for n in z.namelist() if n.lower().endswith('.tif')]
            if len(nombres) != 1:
                raise RuntimeError('zip con %d tif: %s' % (len(nombres), nombres))
            data = z.read(nombres[0])
    if data[:4] not in (b'II*\x00', b'MM\x00*'):
        raise RuntimeError('la respuesta no es un GeoTIFF (primeros bytes %r)' % data[:16])
    return data


def _grid_tiles(bbox, escala, bytes_por_pixel, limite=LIMITE_DESCARGA_BYTES * 0.8):
    """Parte el bbox en N x N tiles alineados al grid para no pasar el limite."""
    x0, y0, x1, y1 = bbox
    w = int(round((x1 - x0) / escala))
    h = int(round((y1 - y0) / escala))
    est = w * h * bytes_por_pixel
    n = int(np.ceil(np.sqrt(est / limite))) if est > limite else 1
    n = max(1, n)
    tiles = []
    for i in range(n):
        for j in range(n):
            tx0 = x0 + np.floor(w * i / n) * escala
            tx1 = x0 + np.floor(w * (i + 1) / n) * escala
            ty0 = y0 + np.floor(h * j / n) * escala
            ty1 = y0 + np.floor(h * (j + 1) / n) * escala
            if tx1 > tx0 and ty1 > ty0:
                tiles.append((tx0, ty0, tx1, ty1))
    return tiles, est


def descargar_geotiff(imagen, bbox_31982, escala, destino, bandas, dtype='float32',
                      nodata=NODATA_FLOAT, descripcion=None, reintentos=3):
    """Baja `imagen` (ee.Image) recortada a bbox, en EPSG:31982 con transformada
    alineada al grid, y la escribe como GeoTIFF con nombres de banda y nodata.

    El origen del bbox ya es multiplo de 10 (ver _alinear_bbox); con `escala`
    de 10/30/90 la transformada [esc,0,x0,0,-esc,y1] deja todo apilable.
    Los pixeles enmascarados se rellenan con `nodata` ANTES de bajar
    (`unmask(nodata, False)`): asi el archivo trae un valor explicito, no un
    0 que se confunda con dato.
    """
    import rasterio
    from rasterio.merge import merge
    from rasterio.transform import from_origin
    ee = inicializar_ee()
    x0, y0, x1, y1 = bbox_31982
    for v in (x0, y0, x1, y1):
        if abs(v / GRID_M - round(v / GRID_M)) > 1e-6:
            raise ValueError('bbox no alineado a %d m: %s' % (GRID_M, bbox_31982))
    img = imagen.select(bandas)
    if nodata is not None:
        img = img.unmask(nodata, False)
    caster = {'float32': 'toFloat', 'uint8': 'toUint8', 'int16': 'toInt16',
              'uint16': 'toUint16', 'int32': 'toInt32'}[dtype]
    img = getattr(img, caster)()
    bpp = {'float32': 4, 'uint8': 1, 'int16': 2, 'uint16': 2, 'int32': 4}[dtype] * len(bandas)
    tiles, est = _grid_tiles(bbox_31982, escala, bpp)
    log('  descarga %s: %d banda(s) a %d m, ~%.1f MB estimados, %d tile(s)'
        % (descripcion or os.path.basename(destino), len(bandas), escala, est / 1e6, len(tiles)))
    piezas = []
    for k, (tx0, ty0, tx1, ty1) in enumerate(tiles):
        params = {
            'region': ee.Geometry.Rectangle([tx0, ty0, tx1, ty1], CRS_METRICO, False),
            'crs': CRS_METRICO,
            'crs_transform': [escala, 0, tx0, 0, -escala, ty1],
            'format': 'GEO_TIFF',
        }
        ultimo = None
        for intento in range(1, reintentos + 1):
            try:
                url = img.getDownloadURL(params)
                data = _bajar_url(url)
                break
            except Exception as e:            # noqa: BLE001 — se reintenta y se declara
                ultimo = e
                log('    tile %d intento %d fallo: %s: %s'
                    % (k, intento, type(e).__name__, str(e)[:160]))
                time.sleep(5 * intento)
        else:
            raise RuntimeError('tile %d no bajo tras %d intentos: %s' % (k, reintentos, ultimo))
        piezas.append(rasterio.MemoryFile(data))
        log('    tile %d/%d: %.1f MB' % (k + 1, len(tiles), len(data) / 1e6))

    srcs = [m.open() for m in piezas]
    if len(srcs) == 1:
        arr = srcs[0].read()
        transform = srcs[0].transform
    else:
        arr, transform = merge(srcs, nodata=nodata)
    crs = srcs[0].crs
    for s in srcs:
        s.close()
    for m in piezas:
        m.close()

    # La transformada que GEE devuelve debe coincidir con la pedida.
    esperada = from_origin(x0, y1, escala, escala)
    if any(abs(a - b) > 1e-3 for a, b in zip(transform[:6], esperada[:6])):
        raise RuntimeError('transformada devuelta %s != pedida %s' % (transform, esperada))
    if crs is None or crs.to_epsg() != EPSG_METRICO:
        raise RuntimeError('CRS devuelto %s != %s' % (crs, CRS_METRICO))
    if arr.shape[0] != len(bandas):
        raise RuntimeError('%d bandas devueltas, %d pedidas' % (arr.shape[0], len(bandas)))

    arr = arr.astype(dtype)
    perfil = {
        'driver': 'GTiff', 'height': arr.shape[1], 'width': arr.shape[2],
        'count': arr.shape[0], 'dtype': dtype, 'crs': crs, 'transform': transform,
        'compress': 'LZW', 'nodata': nodata, 'tiled': False,
    }
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with rasterio.open(destino, 'w', **perfil) as dst:
        dst.write(arr)
        for i, b in enumerate(bandas, 1):
            dst.set_band_description(i, b)
        dst.update_tags(bandas=','.join(bandas), fuente='Google Earth Engine',
                        proyecto='Mata ciliar Fazenda Santo Antonio')
    log('  escrito %s (%.1f MB, %dx%d px)' % (destino, os.path.getsize(destino) / 1e6,
                                               arr.shape[2], arr.shape[1]))
    return destino


def escribir_geotiff(destino, arr, transform, bandas, dtype='float32', nodata=NODATA_FLOAT,
                     tags=None, photometric=None):
    """Escribe un arreglo (bandas, filas, cols) ya en el grid 31982."""
    import rasterio
    from rasterio.crs import CRS
    arr = np.asarray(arr)
    if arr.ndim == 2:
        arr = arr[None]
    perfil = {
        'driver': 'GTiff', 'height': arr.shape[1], 'width': arr.shape[2],
        'count': arr.shape[0], 'dtype': dtype, 'crs': CRS.from_epsg(EPSG_METRICO),
        'transform': transform, 'compress': 'LZW', 'nodata': nodata,
    }
    if photometric:
        perfil['photometric'] = photometric
    with rasterio.open(destino, 'w', **perfil) as dst:
        dst.write(arr.astype(dtype))
        for i, b in enumerate(bandas, 1):
            dst.set_band_description(i, b)
        dst.update_tags(bandas=','.join(bandas), **(tags or {}))
    log('  escrito %s (%.1f MB)' % (destino, os.path.getsize(destino) / 1e6))
    return destino


# --- verificacion de rangos --------------------------------------------------

def verificar_raster(ruta, mascara=None, rotulo=None):
    """Imprime n, min, max, media, %nodata por banda. Devuelve dict por banda.

    `mascara` (bool 2D) restringe la estadistica a una region (p.ej. la
    propiedad). Regla de la casa: si min ~ max la capa esta degenerada y se
    avisa; no se decide aca si es error, pero no pasa callado.
    """
    import rasterio
    stats = {}
    with rasterio.open(ruta) as src:
        nombres = [d or 'b%d' % (i + 1) for i, d in enumerate(src.descriptions)]
        nd = src.nodata
        log('  %s  [%s, %d bandas, %dx%d, res %.1f m, nodata=%s]'
            % (rotulo or os.path.basename(ruta), src.crs, src.count, src.width, src.height,
               src.res[0], nd))
        for i, nombre in enumerate(nombres, 1):
            a = src.read(i).astype('float64')
            valido = np.isfinite(a)
            if nd is not None:
                valido &= (a != nd)
            if mascara is not None:
                valido &= mascara
            n_tot = int(valido.size if mascara is None else mascara.sum())
            n = int(valido.sum())
            pct_nd = 100.0 * (1 - n / n_tot) if n_tot else 100.0
            if n == 0:
                log('    %-14s n=0  TODO NODATA' % nombre)
                stats[nombre] = {'n': 0, 'min': None, 'max': None, 'media': None,
                                 'pct_nodata': pct_nd, 'degenerada': True}
                continue
            v = a[valido]
            mn, mx, me = float(v.min()), float(v.max()), float(v.mean())
            aviso = ''
            if mx == mn or (mx - mn) < 0.01 * abs(me):
                aviso = '   <-- DEGENERADA (min ~ max)'
            log('    %-14s n=%-8d min=%10.4f max=%10.4f media=%10.4f nodata=%5.1f%%%s'
                % (nombre, n, mn, mx, me, pct_nd, aviso))
            stats[nombre] = {'n': n, 'min': mn, 'max': mx, 'media': me,
                             'pct_nodata': round(pct_nd, 2), 'degenerada': bool(aviso)}
    return stats


def mascara_propiedad(ruta_raster, geom_31982):
    """Rasteriza la propiedad sobre el grid de `ruta_raster` (bool 2D)."""
    import rasterio
    from rasterio.features import rasterize
    with rasterio.open(ruta_raster) as src:
        m = rasterize([(geom_31982, 1)], out_shape=(src.height, src.width),
                      transform=src.transform, fill=0, dtype='uint8', all_touched=False)
    return m.astype(bool)
