# -*- coding: utf-8 -*-
"""Paso 3: capas auxiliares (DEM, hidrologia, uso del suelo) recortadas al AOI.

    python gee_03_descarga_auxiliares.py

Cada capa se baja dentro de su propio try/except: si un asset no existe o no
se puede leer, se registra el error en `inventario_datos.json` con estado
'fallo' y se sigue con la siguiente. NO se inventan IDs: los que no existen
se sondearon antes (2026-09-06) y se anotan abajo.

IDs VERIFICADOS EN ESTA MAQUINA (2026-09-06)
- COPERNICUS/DEM/GLO30            existe pero esta DEPRECADO; sucesor
  COPERNICUS/DEM/GLO30_2024_1     se usa el sucesor, respaldo el viejo.
- projects/sat-io/open-datasets/FABDEM   accesible (ImageCollection, banda b1).
- NASADEM_HGT/001                 NO existe con ese ID; el real es NASA/NASADEM_HGT/001.
- JRC/GSW1_4/GlobalSurfaceWater   ok.
- MapBiomas: la ruta pedida collection10/mapbiomas_collection100_integration_v1
  NO existe. Lo que hay (listado con ee.data.listAssets):
    collection9/mapbiomas_collection90_integration_v1          1985..2023
    collection10/mapbiomas_brazil_collection10_integration_v2   1985..2024
    collection11/mapbiomas_brazil_collection11_coverage_v3      1985..2025
  Se usa la MAS RECIENTE (collection11, 2025) para 2025/2008/1985 y se baja
  ademas collection10 2024 a 30 m como contraste de leyenda entre colecciones.
- GOOGLE/DYNAMICWORLD/V1, ESA/WorldCover/v200   ok.
- UMD/hansen/global_forest_change_2024_v1_12   existe pero DEPRECADO; sucesor
  UMD/hansen/global_forest_change_2025_v1_13   se usa el sucesor (lossyear hasta 25).
- MERIT/Hydro/v1_0_1, WWF/HydroSHEDS/v1/FreeFlowingRivers   ok.

REMUESTREO
- DEM (GLO30, FABDEM, NASADEM): fuente en 1 arc-sec WGS84; a 30 m UTM se
  reproyecta con bilineal (nearest a 30 m sobre celdas de ~28x30 m deja
  escalones); la version de 10 m es bicubica y es SOLO cartografica.
- Categoricas (MapBiomas, DW, WorldCover, Hansen, GSW, SCL): vecino mas cercano.
- MERIT Hydro: 3 arc-sec (~90 m); se baja a 90 m bilineal (upa, hnd son continuas).

NODATA
- float: -9999. uint8 categoricas: 0 cuando el dataset ya usa 0 como "no
  observado" (MapBiomas, WorldCover), 255 en el resto.
- JRC occurrence viene ENMASCARADO donde nunca hubo agua; se rellena con 0
  (`unmask(0, False)`) porque ahi 0% de ocurrencia es el valor fisico, y se
  declara en el inventario. No es el unmask(0) de cobertura que prohibe la regla.
"""
import datetime as dt
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from comun import (HOY, NODATA_FLOAT, SALIDA, a_wgs84, cargar_propiedad, descargar_geotiff,
                   describir_aoi, ee_bbox, guardar_json, inicializar_ee, log, mascara_propiedad,
                   safe_getInfo, verificar_raster)

MAPBIOMAS = {
    'col11': ('projects/mapbiomas-public/assets/brazil/lulc/collection11/'
              'mapbiomas_brazil_collection11_coverage_v3'),
    'col10': ('projects/mapbiomas-public/assets/brazil/lulc/collection10/'
              'mapbiomas_brazil_collection10_integration_v2'),
    'col9': ('projects/mapbiomas-public/assets/brazil/lulc/collection9/'
             'mapbiomas_collection90_integration_v1'),
}
LEYENDA_MAPBIOMAS = {
    0: 'Nao observado', 1: 'Floresta', 3: 'Formacao Florestal', 4: 'Formacao Savanica',
    5: 'Mangue', 6: 'Floresta Alagavel', 49: 'Restinga Arborea',
    10: 'Vegetacao Herbacea e Arbustiva', 11: 'Campo Alagado e Area Pantanosa',
    12: 'Formacao Campestre', 32: 'Apicum', 29: 'Afloramento Rochoso', 50: 'Restinga Herbacea',
    14: 'Agropecuaria', 15: 'Pastagem', 18: 'Agricultura', 19: 'Lavoura Temporaria',
    39: 'Soja', 20: 'Cana', 40: 'Arroz', 62: 'Algodao', 41: 'Outras Lavouras Temporarias',
    36: 'Lavoura Perene', 46: 'Cafe', 47: 'Citrus', 35: 'Dende', 48: 'Outras Lavouras Perenes',
    9: 'Silvicultura', 21: 'Mosaico de Usos', 22: 'Area nao Vegetada',
    23: 'Praia, Duna e Areal', 24: 'Area Urbanizada', 30: 'Mineracao',
    25: 'Outras Areas nao Vegetadas', 26: "Corpo D'agua", 33: 'Rio, Lago e Oceano',
    31: 'Aquicultura', 27: 'Nao observado',
}
LEYENDA_DW = {0: 'water', 1: 'trees', 2: 'grass', 3: 'flooded_vegetation', 4: 'crops',
              5: 'shrub_and_scrub', 6: 'built', 7: 'bare', 8: 'snow_and_ice'}
LEYENDA_WORLDCOVER = {10: 'Tree cover', 20: 'Shrubland', 30: 'Grassland', 40: 'Cropland',
                      50: 'Built-up', 60: 'Bare/sparse', 70: 'Snow/ice', 80: 'Water',
                      90: 'Herbaceous wetland', 95: 'Mangroves', 100: 'Moss/lichen'}

INVENTARIO = []


def registrar(nombre, dataset, archivo=None, resolucion=None, bandas=None, version=None,
              nota=None, stats=None, error=None, aoi=None):
    degeneradas = [b for b, v in (stats or {}).items()
                   if isinstance(v, dict) and v.get('degenerada')]
    if degeneradas and not error:
        error = 'capa degenerada (min ~ max) en banda(s) %s' % degeneradas
    fila = {
        'capa': nombre, 'dataset_id': dataset, 'archivo': archivo,
        'resolucion_m': resolucion, 'crs': 'EPSG:31982', 'bandas': bandas,
        'version_fecha': version, 'aoi': aoi, 'nota': nota,
        'estado': 'fallo' if error else 'ok',
        'error': error, 'rangos': stats,
    }
    INVENTARIO.append(fila)
    if error:
        log('  FALLO %s: %s' % (nombre, error))
    return fila


def exigir_no_degenerada(stats, rotulo):
    malas = [b for b, v in stats.items() if v.get('degenerada')]
    if malas:
        raise RuntimeError('%s degenerada en %s: un DEM constante no es un DEM' % (rotulo, malas))


def capa(nombre, fn):
    """Corre fn() y registra el fallo sin tumbar el resto."""
    log('')
    log('--- %s ---' % nombre)
    try:
        fn()
    except Exception as e:                      # noqa: BLE001 — se declara y se sigue
        registrar(nombre, '?', error='%s: %s' % (type(e).__name__, str(e)[:300]))


def histograma_clases(ruta, leyenda, mascara=None, rotulo=''):
    """Cuenta clases y las convierte a ha con el tamano real del pixel."""
    import rasterio
    with rasterio.open(ruta) as src:
        a = src.read(1)
        px_ha = abs(src.res[0] * src.res[1]) / 1e4
        nd = src.nodata
    sel = np.ones(a.shape, bool) if mascara is None else mascara
    v = a[sel]
    vals, cnt = np.unique(v, return_counts=True)
    total_ha = float(v.size * px_ha)
    log('  Histograma %s (%.2f ha, pixel %.2f ha):' % (rotulo, total_ha, px_ha))
    out = {}
    for k, c in sorted(zip(vals.tolist(), cnt.tolist()), key=lambda t: -t[1]):
        ha = c * px_ha
        etiqueta = leyenda.get(int(k), 'CLASE %d NO ESTA EN LA LEYENDA' % k)
        if nd is not None and k == nd:
            etiqueta += ' (nodata)'
        log('    %3d %-34s %9.2f ha  %5.1f%%' % (k, etiqueta, ha, 100.0 * c / v.size))
        out[str(int(k))] = {'clase': etiqueta, 'ha': round(ha, 2), 'pct': round(100.0 * c / v.size, 2)}
    desconocidas = [int(k) for k in vals if int(k) not in leyenda]
    if desconocidas:
        log('  AVISO: clases fuera de la leyenda: %s' % desconocidas)
    return out


def main():
    log('=== gee_03_descarga_auxiliares (%s) ===' % HOY)
    p = cargar_propiedad()
    describir_aoi(p)
    ee = inicializar_ee()
    aoi = p['aoi_31982']
    aoi_dem = p['aoi_dem_31982']
    g_aoi = ee_bbox(aoi)
    g_dem = ee_bbox(aoi_dem)
    os.makedirs(SALIDA, exist_ok=True)
    R = {}   # rutas por nombre para los histogramas

    # ---------------------------------------------------------------- DEM ----
    def glo30():
        ids = ['COPERNICUS/DEM/GLO30_2024_1', 'COPERNICUS/DEM/GLO30']
        ultimo = None
        for aid in ids:
            try:
                col = ee.ImageCollection(aid).filterBounds(g_dem).select('DEM')
                n = safe_getInfo(col.size(), descripcion=aid)
                if n == 0:
                    raise RuntimeError('0 granulos sobre el AOI')
                log('  %s: %d granulo(s)' % (aid, n))
                # resample() va en CADA imagen, antes del mosaic(): un compuesto tiene
                # proyeccion por defecto de 1 grado y resample() sobre el compuesto devuelve
                # UN solo valor para todo el AOI. MEDIDO 2026-09-06: 766,41 m constante.
                dem_bil = col.map(lambda im: im.resample('bilinear')).mosaic().rename('DEM')
                dem_bic = col.map(lambda im: im.resample('bicubic')).mosaic().rename('DEM')
                r30 = os.path.join(SALIDA, 'DEM_GLO30_AOIdem_30m.tif')
                descargar_geotiff(dem_bil, aoi_dem, 30, r30, ['DEM'])
                st = verificar_raster(r30)
                exigir_no_degenerada(st, 'GLO30 30 m')
                registrar('DEM GLO30 30 m', aid, r30, 30, ['DEM'], 'mosaico 2024_1' if '2024' in aid else 'GLO30 (deprecado)',
                          'bilineal desde 1 arc-sec', st, aoi='dem+3000')
                r10 = os.path.join(SALIDA, 'DEM_GLO30_AOIdem_10m_bicubico.tif')
                descargar_geotiff(dem_bic, aoi_dem, 10, r10, ['DEM'])
                st = verificar_raster(r10)
                exigir_no_degenerada(st, 'GLO30 10 m')
                registrar('DEM GLO30 10 m bicubico', aid, r10, 10, ['DEM'], None,
                          'SOLO cartografico: bicubico desde 30 m no agrega informacion', st, aoi='dem+3000')
                return
            except Exception as e:              # noqa: BLE001
                ultimo = e
                log('  %s no sirvio: %s' % (aid, str(e)[:160]))
        raise RuntimeError('ningun GLO30 accesible: %s' % ultimo)
    capa('DEM Copernicus GLO30', glo30)

    def fabdem():
        aid = 'projects/sat-io/open-datasets/FABDEM'
        col = ee.ImageCollection(aid).filterBounds(g_dem)
        n = safe_getInfo(col.size(), descripcion=aid)
        if n == 0:
            raise RuntimeError('0 granulos sobre el AOI')
        img = col.map(lambda im: im.resample('bilinear')).mosaic().select(['b1'], ['FABDEM'])
        r = os.path.join(SALIDA, 'DEM_FABDEM_AOIdem_30m.tif')
        descargar_geotiff(img, aoi_dem, 30, r, ['FABDEM'])
        st = verificar_raster(r)
        exigir_no_degenerada(st, 'FABDEM')
        registrar('DEM FABDEM 30 m', aid, r, 30, ['FABDEM'], 'v1-2 (Hawker 2022)',
                  'GLO30 sin edificios ni arboles; bilineal', st, aoi='dem+3000')
    capa('DEM FABDEM', fabdem)

    def nasadem():
        aid = 'NASA/NASADEM_HGT/001'
        img = ee.Image(aid).select(['elevation'], ['NASADEM'])
        r = os.path.join(SALIDA, 'DEM_NASADEM_AOIdem_30m.tif')
        descargar_geotiff(img.resample('bilinear'), aoi_dem, 30, r, ['NASADEM'])
        st = verificar_raster(r)
        exigir_no_degenerada(st, 'NASADEM')
        registrar('DEM NASADEM 30 m', aid, r, 30, ['NASADEM'], '001',
                  'el ID pedido NASADEM_HGT/001 no existe; el real lleva prefijo NASA/', st, aoi='dem+3000')
    capa('DEM NASADEM', nasadem)

    # ---------------------------------------------------------- hidrologia ----
    def gsw():
        aid = 'JRC/GSW1_4/GlobalSurfaceWater'
        img = ee.Image(aid)
        occ = img.select('occurrence').unmask(0, False)     # enmascarado = nunca agua = 0%
        ext = img.select('max_extent').unmask(0, False)
        r = os.path.join(SALIDA, 'AGUA_JRC_GSW_AOI_30m.tif')
        descargar_geotiff(occ.addBands(ext), aoi, 30, r, ['occurrence', 'max_extent'],
                          dtype='uint8', nodata=255)
        st = verificar_raster(r)
        registrar('JRC Global Surface Water 30 m', aid, r, 30, ['occurrence', 'max_extent'],
                  'v1.4 (1984-2021)', 'occurrence 0-100 %; enmascarado rellenado con 0 = nunca agua', st, aoi='aoi+1500')
    capa('JRC GSW', gsw)

    def merit():
        aid = 'MERIT/Hydro/v1_0_1'
        img = ee.Image(aid).select(['upa', 'hnd'])
        r = os.path.join(SALIDA, 'HIDRO_MERIT_upa_hnd_AOIdem_90m.tif')
        descargar_geotiff(img.resample('bilinear'), aoi_dem, 90, r, ['upa', 'hnd'])
        st = verificar_raster(r)
        registrar('MERIT Hydro upa/hnd 90 m', aid, r, 90, ['upa', 'hnd'], 'v1.0.1',
                  'upa = area de drenaje aguas arriba (km2); hnd = HAND (m). bilineal desde 3 arc-sec', st, aoi='dem+3000')
    capa('MERIT Hydro', merit)

    def hydrosheds():
        aid = 'WWF/HydroSHEDS/v1/FreeFlowingRivers'
        fc =ee.FeatureCollection(aid).filterBounds(ee_bbox(aoi_dem))
        info = safe_getInfo(fc, descripcion=aid)
        n = len(info.get('features', []))
        log('  %d feature(s) de FreeFlowingRivers en el AOI DEM' % n)
        if n == 0:
            registrar('HydroSHEDS FreeFlowingRivers', aid, None, None, None, 'v1',
                      'sin features dentro del AOI ampliado (3000 m)', None, aoi='dem+3000')
            return
        r = os.path.join(SALIDA, 'HIDRO_HydroSHEDS_FFR_AOIdem_wgs84.geojson')
        info['name'] = 'HydroSHEDS_FFR_AOIdem'
        info['crs'] = {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}}
        guardar_json(r, info)
        # Version metrica: mismas features reproyectadas a 31982.
        from pyproj import Transformer
        from shapely.geometry import shape, mapping
        from shapely.ops import transform
        t = Transformer.from_crs('EPSG:4326', 'EPSG:31982', always_xy=True)
        feats31982 = []
        for f in info['features']:
            g = transform(t.transform, shape(f['geometry']))
            feats31982.append({'type': 'Feature', 'properties': f['properties'], 'geometry': mapping(g)})
        r2 = os.path.join(SALIDA, 'HIDRO_HydroSHEDS_FFR_AOIdem_31982.geojson')
        guardar_json(r2, {'type': 'FeatureCollection', 'name': 'HydroSHEDS_FFR_AOIdem_31982',
                          'crs': {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:EPSG::31982'}},
                          'features': feats31982})
        nombres = [f['properties'].get('RIV_ORD') for f in info['features']]
        registrar('HydroSHEDS FreeFlowingRivers', aid, r, None, None, 'v1',
                  '%d tramos; ordenes %s; tambien en 31982: %s' % (n, nombres, os.path.basename(r2)),
                  {'n_features': n}, aoi='dem+3000')
    capa('HydroSHEDS FFR', hydrosheds)

    # ------------------------------------------------------ uso del suelo ----
    def mapbiomas():
        # La mas reciente que exista, en orden: col11 (2025) > col10 (2024) > col9 (2023)
        candidatos = [('col11', 'classification_2025'), ('col10', 'classification_2024'),
                      ('col9', 'classification_2023')]
        elegido = None
        for clave, banda in candidatos:
            try:
                bn = safe_getInfo(ee.Image(MAPBIOMAS[clave]).bandNames(), descripcion=clave)
                if banda in bn:
                    elegido = (clave, banda)
                    break
                log('  %s existe pero no tiene %s' % (clave, banda))
            except Exception as e:              # noqa: BLE001
                log('  %s no accesible: %s' % (clave, str(e)[:120]))
        if elegido is None:
            raise RuntimeError('ninguna coleccion MapBiomas accesible')
        clave, banda_reciente = elegido
        aid = MAPBIOMAS[clave]
        anio = banda_reciente[-4:]
        log('  usando %s (%s)' % (aid, banda_reciente))
        img = ee.Image(aid)
        bandas = [banda_reciente, 'classification_2008', 'classification_1985']
        r30 = os.path.join(SALIDA, 'LULC_MAPBIOMAS_%s_%s_2008_1985_AOI_30m.tif' % (clave, anio))
        descargar_geotiff(img.select(bandas), aoi, 30, r30, bandas, dtype='uint8', nodata=0)
        st = verificar_raster(r30)
        registrar('MapBiomas %s/2008/1985 30 m' % anio, aid, r30, 30, bandas, clave,
                  '2008 = ano de corte legal (22/07/2008, area rural consolidada); 0 = nao observado',
                  st, aoi='aoi+1500')
        R['mb30'] = r30
        r10 = os.path.join(SALIDA, 'LULC_MAPBIOMAS_%s_%s_AOI_10m_nearest.tif' % (clave, anio))
        descargar_geotiff(img.select([banda_reciente]), aoi, 10, r10, [banda_reciente],
                          dtype='uint8', nodata=0)
        st = verificar_raster(r10)
        registrar('MapBiomas %s 10 m nearest' % anio, aid, r10, 10, [banda_reciente], clave,
                  'vecino mas cercano desde 30 m: no agrega detalle, solo alinea al grid de 10 m', st, aoi='aoi+1500')
        R['mb10'] = r10
        R['mb_anio'] = anio
        # Contraste entre colecciones: col10 2024 si la principal fue col11.
        if clave == 'col11':
            aid10 = MAPBIOMAS['col10']
            rc = os.path.join(SALIDA, 'LULC_MAPBIOMAS_col10_2024_AOI_30m.tif')
            descargar_geotiff(ee.Image(aid10).select(['classification_2024']), aoi, 30, rc,
                              ['classification_2024'], dtype='uint8', nodata=0)
            st = verificar_raster(rc)
            registrar('MapBiomas col10 2024 30 m (contraste)', aid10, rc, 30, ['classification_2024'], 'col10 v2',
                      'para comparar leyenda/consistencia entre colecciones 10 y 11', st, aoi='aoi+1500')
            R['mb_col10'] = rc
    capa('MapBiomas', mapbiomas)

    def dynamic_world():
        aid = 'GOOGLE/DYNAMICWORLD/V1'
        hasta = dt.date.fromisoformat(HOY) + dt.timedelta(days=1)
        desde = hasta - dt.timedelta(days=366)
        col = ee.ImageCollection(aid).filterBounds(g_aoi).filterDate(str(desde), str(hasta)).select('label')
        n = safe_getInfo(col.size(), descripcion=aid)
        log('  %d imagenes DW entre %s y %s' % (n, desde, hasta))
        if n == 0:
            raise RuntimeError('0 imagenes Dynamic World en 12 meses')
        moda = col.reduce(ee.Reducer.mode()).rename('label_moda')
        cuenta = col.count().rename('n_obs')
        r = os.path.join(SALIDA, 'LULC_DYNAMICWORLD_moda12m_AOI_10m.tif')
        descargar_geotiff(moda.addBands(cuenta), aoi, 10, r, ['label_moda', 'n_obs'], dtype='uint8', nodata=255)
        st = verificar_raster(r)
        registrar('Dynamic World moda 12 meses 10 m', aid, r, 10, ['label_moda', 'n_obs'],
                  '%s..%s (%d imagenes)' % (desde, hasta, n),
                  'moda de label por pixel; n_obs = observaciones validas por pixel', st, aoi='aoi+1500')
        R['dw'] = r
    capa('Dynamic World', dynamic_world)

    def worldcover():
        aid = 'ESA/WorldCover/v200'
        img = ee.ImageCollection(aid).first().select('Map')
        r = os.path.join(SALIDA, 'LULC_ESA_WORLDCOVER_2021_AOI_10m.tif')
        descargar_geotiff(img, aoi, 10, r, ['Map'], dtype='uint8', nodata=0)
        st = verificar_raster(r)
        registrar('ESA WorldCover v200 10 m', aid, r, 10, ['Map'], 'v200 (ano 2021)', None, st, aoi='aoi+1500')
        R['wc'] = r
    capa('ESA WorldCover', worldcover)

    def hansen():
        ids = ['UMD/hansen/global_forest_change_2025_v1_13',
               'UMD/hansen/global_forest_change_2024_v1_12',
               'UMD/hansen/global_forest_change_2023_v1_11']
        ultimo = None
        for aid in ids:
            try:
                base = ee.Image(aid)
                safe_getInfo(base.bandNames(), descripcion=aid)
                # lossyear viene ENMASCARADO donde no hubo perdida (medido: 99% del AOI);
                # ahi el valor fisico es 0 = sin perdida, no nodata.
                img = (base.select(['treecover2000', 'gain'])
                       .addBands(base.select('lossyear').unmask(0, False))
                       .select(['treecover2000', 'lossyear', 'gain']))
                anio_gfc = aid.split('_')[-3]        # ..._2025_v1_13 -> 2025
                r = os.path.join(SALIDA, 'BOSQUE_HANSEN_GFC_%s_AOI_30m.tif' % anio_gfc)
                descargar_geotiff(img, aoi, 30, r, ['treecover2000', 'lossyear', 'gain'], dtype='uint8', nodata=255)
                st = verificar_raster(r)
                registrar('Hansen GFC 30 m', aid, r, 30, ['treecover2000', 'lossyear', 'gain'], aid.split('/')[-1],
                          'treecover2000 en %; lossyear 0 = sin perdida (enmascarado rellenado con 0), 1..N = 2000+N; gain 2000-2012', st, aoi='aoi+1500')
                return
            except Exception as e:              # noqa: BLE001
                ultimo = e
                log('  %s no sirvio: %s' % (aid, str(e)[:160]))
        raise RuntimeError('ningun Hansen accesible: %s' % ultimo)
    capa('Hansen GFC', hansen)

    # ------------------------------------------------------- histogramas ----
    log('')
    log('=== Histogramas de clases ===')
    hist = {}
    if 'mb10' in R:
        m = mascara_propiedad(R['mb10'], p['geom'])
        hist['mapbiomas_%s_propiedad_10m' % R['mb_anio']] = histograma_clases(
            R['mb10'], LEYENDA_MAPBIOMAS, m, 'MapBiomas %s DENTRO DE LA PROPIEDAD (10 m nearest)' % R['mb_anio'])
        hist['mapbiomas_%s_aoi_10m' % R['mb_anio']] = histograma_clases(
            R['mb10'], LEYENDA_MAPBIOMAS, None, 'MapBiomas %s en el AOI' % R['mb_anio'])
    if 'mb30' in R:
        import rasterio
        m30 = mascara_propiedad(R['mb30'], p['geom'])
        with rasterio.open(R['mb30']) as src:
            descr = list(src.descriptions)
        for i, d in enumerate(descr):
            # una banda por vez: escribimos un raster temporal en memoria? no: reusamos leyendo la banda i
            with rasterio.open(R['mb30']) as src:
                a = src.read(i + 1)
            v = a[m30]
            vals, cnt = np.unique(v, return_counts=True)
            log('  MapBiomas %s dentro de la propiedad (30 m, %.2f ha):' % (d, v.size * 0.09))
            hist['mapbiomas_%s_propiedad_30m' % d[-4:]] = {}
            for k, c in sorted(zip(vals.tolist(), cnt.tolist()), key=lambda t: -t[1]):
                log('    %3d %-34s %9.2f ha  %5.1f%%' % (k, LEYENDA_MAPBIOMAS.get(int(k), '?'), c * 0.09, 100.0 * c / v.size))
                hist['mapbiomas_%s_propiedad_30m' % d[-4:]][str(int(k))] = {
                    'clase': LEYENDA_MAPBIOMAS.get(int(k), '?'), 'ha': round(c * 0.09, 2)}
    if 'mb_col10' in R:
        m30 = mascara_propiedad(R['mb_col10'], p['geom'])
        hist['mapbiomas_col10_2024_propiedad_30m'] = histograma_clases(
            R['mb_col10'], LEYENDA_MAPBIOMAS, m30, 'MapBiomas col10 2024 dentro de la propiedad (30 m)')
    if 'dw' in R:
        m = mascara_propiedad(R['dw'], p['geom'])
        hist['dynamicworld_propiedad'] = histograma_clases(R['dw'], LEYENDA_DW, m, 'Dynamic World moda dentro de la propiedad')
    if 'wc' in R:
        m = mascara_propiedad(R['wc'], p['geom'])
        hist['worldcover_propiedad'] = histograma_clases(R['wc'], LEYENDA_WORLDCOVER, m, 'WorldCover dentro de la propiedad')

    # ---------------------------------------------------------- inventario ----
    fallos = [f for f in INVENTARIO if f['estado'] == 'fallo']
    log('')
    log('=== Inventario: %d capas, %d fallo(s) ===' % (len(INVENTARIO), len(fallos)))
    for f in fallos:
        log('  FALLO %s: %s' % (f['capa'], f['error']))
    guardar_json(os.path.join(SALIDA, 'inventario_datos.json'), {
        'fecha_descarga': HOY, 'crs': 'EPSG:31982', 'grid_alineado_m': 10,
        'aoi_31982': aoi, 'aoi_dem_31982': aoi_dem,
        'propiedad_ha_31982': p['area_ha'],
        'capas': INVENTARIO, 'histogramas': hist,
        'leyenda_mapbiomas': {str(k): v for k, v in LEYENDA_MAPBIOMAS.items()},
    })
    if fallos:
        log('SALIDA CON FALLAS: %d capa(s) no usable(s); ver inventario_datos.json' % len(fallos))
        sys.exit(1)


if __name__ == '__main__':
    main()
