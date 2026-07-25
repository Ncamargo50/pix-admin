"""Columna vertebral de PIX ALERTA: la tabla de serie temporal por LOTE y por FECHA.

Una fila por (lote, fecha). Sin rasteres, sin descargas: `reduceRegions` devuelve
una tabla. Es lo que hace posible el eje temporal —la unica via de especificidad
demostrada con bandas anchas— y lo que se archiva para la validacion.

La entidad "lote" no existe en el motor actual; el ranking de lotes es el producto.
"""
import json
import ee
import pandas as pd

from . import config as cfg


def _mascara(img):
    """Nube Y SOMBRA por SCL, dilatada. Devuelve banda booleana de pixel valido."""
    scl = img.select('SCL')
    mala = scl.remap(cfg.SCL_MALAS, [1] * len(cfg.SCL_MALAS), 0)
    # Dilatar: el borde de una nube contamina mucho mas alla de su clase.
    mala = mala.focalMax(cfg.DILATAR_NUBE_PX, 'square', 'pixels')
    return mala.Not().rename('valido')


def _indices(img):
    """Los dos ejes de dosel + NDVI para la compuerta de vegetacion."""
    b = lambda n: img.select(n).divide(10000)
    B2, B4, B6, B8, B8A, B11 = b('B2'), b('B4'), b('B6'), b('B8'), b('B8A'), b('B11')
    ndvi = B8.subtract(B4).divide(B8.add(B4)).rename('NDVI')
    # HUMEDAD DE DOSEL. Es NDMI/NDII, NO el "NDWI de Gao": Gao (1996) usa 1240 nm y
    # Sentinel-2 NO TIENE esa banda (B9=945, B10=1373, B11=1614), asi que su NDWI es
    # literalmente incalculable con S2. Citar Hardisky, Klemas & Smart 1983 (NDII, sin
    # DOI, articulo pre-DOI) o Wilson & Sader 2002 (10.1016/S0034-4257(01)00318-2).
    # NUNCA citar Gao para esto, aunque Sentinel Hub lo haga en su propio script.
    #
    # B8A y no B8: B8 tiene FWHM de 118 nm (774-891) e integra media meseta NIR; B8A
    # tiene 20 nm (855-875) y contiene exactamente los 850-865 nm que pide Hardisky.
    # Ademas B8A es nativo de 20 m igual que B11: usar B8 (10 m) obliga a remuestrear
    # una de las dos y mete mezcla espectral en los bordes de lote. El pipeline de
    # produccion ya usaba B8A; esto alinea los dos motores.
    ndmi = B8A.subtract(B11).divide(B8A.add(B11)).rename('NDMI')
    # SENESCENCIA. Merzlyak et al. 1999 (10.1034/j.1399-3054.1999.106119.x):
    # (R678 - R500)/R750. Con S2: B4 (665) - B2 (493, contiene 500) / B6 (740).
    # B2 y no B3: B3 va de 542 a 577 nm y NO contiene 500 nm.
    psri = B4.subtract(B2).divide(B6).rename('PSRI')
    return ndvi.addBands(ndmi).addBands(psri)


def _fvc(ndvi, geom, escala=20):
    """Cobertura vegetal fraccional por linea empirica sobre la PROPIA escena.

    Se anclan suelo y vegetacion plena en p2/p98 de la escena en vez de usar
    constantes: un umbral absoluto de NDVI no transfiere entre sitios ni cultivares.
    La incertidumbre real de FVC en campo es RMSE ~0,17, no el 0,04 teorico.
    """
    q = ndvi.reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]), geometry=geom,
        scale=escala * 5, maxPixels=1e9, bestEffort=True)
    # Una escena integramente nublada deja los percentiles en null: hay que
    # devolver FVC=0 (nada utilizable), no propagar el null ni reventar.
    lo = ee.Number(ee.Algorithms.If(q.get('NDVI_p2'), q.get('NDVI_p2'), 0))
    hi = ee.Number(ee.Algorithms.If(q.get('NDVI_p98'), q.get('NDVI_p98'), 0))
    rango = hi.subtract(lo).max(1e-6)          # guard div/0
    return (ndvi.unmask(0).subtract(lo).divide(rango)
            .clamp(0, 1).rename('FVC'))


def _sin_z(coords):
    """Los GeoJSON exportados por QGIS traen Z=0; EE rechaza la geometria 3D."""
    if isinstance(coords[0], (int, float)):
        return list(coords[:2])
    return [_sin_z(c) for c in coords]


def _lotes_ee(sitio):
    """Lotes con buffer negativo, como FeatureCollection de EE."""
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    validas = cfg.unidades_validas(sitio)
    feats = []
    descartadas = 0
    for f in gj['features']:
        pid = f['properties'].get(sitio.campo_id)
        if pid is None:
            continue
        if validas is not None and str(pid) not in validas:
            descartadas += 1      # pista, monte, camino, o sin clasificar
            continue
        geom = {'type': f['geometry']['type'],
                'coordinates': _sin_z(f['geometry']['coordinates'])}
        g = ee.Geometry(geom, geodesic=False)
        # Buffer negativo: descarta pixeles de borde mixtos. 5 m, no 10.
        g = g.buffer(-sitio.buffer_negativo_m, maxError=1)
        feats.append(ee.Feature(g, {
            'lote_id': str(pid),
            'area_ha': f['properties'].get(sitio.campo_area, 0) or 0,
        }))
    if descartadas:
        print(f'[{sitio.clave}] {descartadas} unidades descartadas por no ser '
              f'cultivo o no estar clasificadas; quedan {len(feats)}')
    return ee.FeatureCollection(feats)


def extraer(sitio, ini, fin, escala=20, verbose=True):
    """Devuelve el DataFrame largo (lote_id, fecha, NDVI, NDMI, PSRI, calidad...).

    `escala=20` no es una concesion: el test espacial pide agregar a 20-30 m antes
    de testear, y a 20 m un lote de 200 ha sigue teniendo ~5.000 unidades.
    """
    lotes = _lotes_ee(sitio)
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(ini, fin)
           .filterBounds(lotes.geometry().bounds()))
    fechas = col.aggregate_array('system:time_start').getInfo()
    n_esc = len(fechas)
    if verbose:
        print(f'[{sitio.clave}] {ini} .. {fin}: {n_esc} escenas S2 en catalogo')
    if n_esc == 0:
        return pd.DataFrame()

    aoi = lotes.geometry()
    n_lotes = lotes.size().getInfo()

    def por_escena(img):
        img = ee.Image(img)
        valido = _mascara(img)
        idx = _indices(img)
        # Los extremos del FVC se anclan SOLO sobre pixel limpio: calcularlos
        # sobre la escena completa los ancla en la nube y la compuerta se rompe.
        fvc = _fvc(idx.select('NDVI').updateMask(valido), aoi, escala)
        # Dosel util = pixel limpio Y con cobertura vegetal suficiente.
        util = valido.And(fvc.gte(cfg.FVC_MINIMA)).rename('util')
        campos = idx.addBands(fvc).updateMask(util)
        # cobertura = fraccion del lote con observacion utilizable
        pila = campos.addBands(util.unmask(0).rename('cob'))
        stats = pila.reduceRegions(
            collection=lotes,
            reducer=ee.Reducer.mean().combine(ee.Reducer.count(), '', True),
            scale=escala, tileScale=4)
        d = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        return stats.map(lambda f: f.set('fecha', d).setGeometry(None))

    # getInfo aborta pasados 5.000 elementos. Se consulta por bloques de escenas
    # para que retrollenar campañas enteras sea posible sin exportar a Drive.
    por_bloque = max(1, 4500 // max(n_lotes, 1))
    lista = col.toList(n_esc)
    filas = []
    for i in range(0, n_esc, por_bloque):
        sub = ee.ImageCollection(lista.slice(i, min(i + por_bloque, n_esc)))
        trozo = sub.map(por_escena).flatten().getInfo()['features']
        filas.extend(f['properties'] for f in trozo)
        if verbose:
            print(f'  escenas {i+1}-{min(i+por_bloque, n_esc)}/{n_esc}: '
                  f'{len(filas)} filas', flush=True)
    df = pd.DataFrame(filas)
    if df.empty:
        return df

    # reduceRegions devuelve <banda>_mean / <banda>_count
    df = df.rename(columns={f'{b}_mean': b for b in
                            ('NDVI', 'NDMI', 'PSRI', 'FVC')})
    # n_px = pixeles LIMPIOS. `cob` esta unmask(0), asi que `cob_count` cuenta todo
    # el footprint del lote: era constante a lo largo de la campaña (corr con
    # cobertura = -0,016) y el filtro de MIN_PIXELES descartaba 0 de 2.537 filas.
    # `NDMI_count` si cuenta solo los pixeles que sobrevivieron a la mascara.
    df = df.rename(columns={'cob_mean': 'cobertura'})
    if 'NDMI_count' in df.columns:
        df['n_px'] = df['NDMI_count']
    else:
        df['n_px'] = df.get('cob_count')
    if 'cobertura' not in df.columns:
        raise RuntimeError('reduceRegions no devolvio la banda de cobertura')
    df['cobertura'] = pd.to_numeric(df['cobertura'], errors='coerce').fillna(0.0)
    df['calidad'] = pd.cut(
        df['cobertura'], [-0.01, cfg.UMBRAL_PARCIAL, cfg.UMBRAL_PLENO, 1.01],
        labels=['descartado', 'parcial', 'pleno'])
    df['fecha'] = pd.to_datetime(df['fecha'])
    cols = ['lote_id', 'fecha', 'area_ha', 'cobertura', 'n_px', 'calidad',
            'NDVI', 'NDMI', 'PSRI', 'FVC']
    df = df[[c for c in cols if c in df.columns]]
    # Un lote puede caer en dos tiles MGRS y aparecer dos veces la misma fecha.
    # Se conserva la observacion con mejor cobertura, no la ultima que llego.
    df = (df.sort_values(['lote_id', 'fecha', 'cobertura'])
            .drop_duplicates(['lote_id', 'fecha'], keep='last')
            .sort_values(['lote_id', 'fecha']))
    if verbose:
        n = len(df)
        pl = (df['calidad'] == 'pleno').mean()
        print(f'[{sitio.clave}] {n} filas | {df.lote_id.nunique()} lotes | '
              f'{pl*100:.1f}% de observaciones plenas')
    return df.reset_index(drop=True)
