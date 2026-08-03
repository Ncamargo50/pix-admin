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


CS_PLUS = 'GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED'

# Bandas de dosel que `_indices` produce y que viajan en la serie. Es un CONTRATO, no
# una lista de conveniencia: un indice que se calcula pero no entra aca no existe para
# ningun arnes de medicion, y medirlo obliga a reextraer la campaña entera.
# KNDVI, TEXNIR y NDTX estan como CANDIDATOS medibles, no como ejes de produccion.
BANDAS_TEXTURA = ('TEXNIR', 'NDTX')
BANDAS_DOSEL = (('NDVI', 'NDMI', 'PSRI', 'NDRE', 'CIRE', 'FVC', 'KNDVI')
                + BANDAS_TEXTURA)
COLS_SERIE = (('lote_id', 'fecha', 'area_ha', 'cobertura', 'n_px', 'calidad')
              + BANDAS_DOSEL)


def _cloudscore(img):
    """Banda `cs_cdf` de CloudScore+ para ESTA escena, o None si no esta.

    POR QUE SE AGREGA (2026-07-29)
    ------------------------------
    SCL marca el NUCLEO opaco de la nube. El cirro delgado y la bruma peri-nube
    quedan rotulados como vegetacion con reflectancia deprimida — que es
    exactamente la firma que busca el criterio (NDMI y NDRE bajando juntos).
    MEDIDO ese dia: los 3 focos que se le reportaron al cliente estaban a 19-70 m
    del borde de la mascara y desaparecian al dilatar. Eran nube, no daño.

    CloudScore+ SI modela nube fina, bruma y cirro, y su score sale de un modelo
    entrenado con datos de alta resolucion. Evaluacion independiente: 89,4% de
    pixeles limpios contra 80,8% de s2cloudless.

    HIBRIDO A PROPOSITO: CloudScore+ como score principal Y SCL dilatada como veto
    duro. CloudScore+ da *usabilidad*, no clasifica sombra semanticamente; SCL clase
    3 (CLOUD_SHADOW) si, y la sombra es el artefacto que mas se parece a un foco.
    Ninguno de los dos solo alcanza.
    """
    return (ee.ImageCollection(CS_PLUS)
            .filter(ee.Filter.eq('system:index', img.get('system:index')))
            .first())


def _mascara(img):
    """Nube Y SOMBRA. Devuelve banda booleana de pixel valido.

    Dos filtros que se suman, no se reemplazan (ver `_cloudscore`):
      · SCL dilatada  -> veto duro, y es lo unico que ve la SOMBRA
      · CloudScore+   -> nube fina, bruma y cirro, que es el agujero de SCL
    """
    scl = img.select('SCL')
    mala = scl.remap(cfg.SCL_MALAS, [1] * len(cfg.SCL_MALAS), 0)
    # Dilatar: el borde de una nube contamina mucho mas alla de su clase.
    mala = mala.focalMax(cfg.DILATAR_NUBE_PX, 'square', 'pixels')
    valido = mala.Not()
    if getattr(cfg, 'USAR_CLOUDSCORE', True):
        cs = _cloudscore(img)
        # Si la escena no tiene CloudScore+ (hay huecos en el archivo) se sigue con
        # SCL sola en vez de enmascarar todo: degradar, no romper. El `If` resuelve
        # del lado del servidor, asi que no cuesta un getInfo por escena.
        limpio_cs = ee.Image(ee.Algorithms.If(
            cs, ee.Image(cs).select(cfg.CS_BANDA).gte(cfg.CS_UMBRAL),
            ee.Image(1)))
        valido = valido.And(limpio_cs)
    return valido.rename('valido')


# --- TEXTURA: el unico candidato a segundo eje que NO es un indice espectral -----
#
# POR QUE SE AGREGA (2026-08-03)
# ------------------------------
# El motor tiene un problema medido y sin solucion desde hace tres iteraciones: los
# residuos temporales de los dos ejes de produccion correlacionan rho = 0,969
# (`medicion/banda_compartida.py`), o sea que el segundo eje aporta apenas el 6,1% de
# varianza independiente. Se midieron PSRI (0,927) y CIre (0,830) como reemplazo y
# ninguno decidio, porque **los tres son indices espectrales y los tres siguen la
# biomasa**. Cambiar de indice ya se midio que compra ~2x; es el techo de esa via.
#
# La textura no es reflectancia: es la ORGANIZACION ESPACIAL de la reflectancia dentro
# de una vecindad. Es ortogonal por FISICA, no por estadistica — que es exactamente la
# propiedad que ningun par de indices logro tener. La literatura la respalda: VIs +
# textura llega a R2 0,78-0,84 en biomasa, y los indices de textura de diferencia
# normalizada superan a todos los VIs evaluados Y a las texturas GLCM sueltas
# (`../INVESTIGACION_TELEDETECCION_CULTIVOS_2026.md` §2.5).
#
# ⚠️ ESTO ES UN CANDIDATO, NO PRODUCCION. Se calcula y viaja en la serie para que se
# pueda MEDIR con los tres arneses que ya existen. La regla de `config.py` no cambia:
# mover `EJES` exige una razon POSITIVA — correlacion de residuos mas baja, lift contra
# la nula sintetica, y tasa empirica sobre fechas sin evento. Si empata, no se cambia.
#
# LIMITES QUE HAY QUE DECLARAR ANTES DE MEDIR
# -------------------------------------------
# 1. **La textura sube en el borde de nube.** Un pixel a medio enmascarar es el vecino
#    de uno enmascarado, y esa discontinuidad es contraste puro. Por eso `_indices`
#    aplica la mascara DESPUES: la textura se calcula sobre la escena y recien ahi se
#    censura. Si la dilatacion de nube (80 m = 4 px) no alcanza, este eje va a marcar
#    bordes de nube — el mismo modo de falla que ya costo tres focos falsos.
# 2. **La textura sube en el borde del lote** por mezcla espectral. El buffer negativo
#    de 5 m NO alcanza para una ventana de 3x3 a 20 m (60 m): un pixel a 30 m del borde
#    todavia tiene vecinos de afuera. Es un sesgo conocido y hay que mirarlo.
# 3. **Depende de la cuantizacion.** El contraste GLCM no es invariante al numero de
#    niveles. Se fija en 8 bits sobre un rango de reflectancia FIJO y declarado, para
#    que el numero sea comparable entre escenas. Un reescalado por escena —lo que hace
#    casi todo el mundo— haria que el contraste dependa de si ese dia habia nube.
# 4. **No mide lo mismo a otra escala.** A 20 m con ventana 3x3 la textura habla de
#    heterogeneidad a 60 m. A 10 m seria otra variable con el mismo nombre.
# 5. ⚠️ **DILATA EL FOCO, Y ESTA MEDIDO.** Toda medida de ventana contamina a los
#    vecinos: un pixel anomalo altera la textura de los 8 que lo rodean. Cuantificado
#    con la MMU real del motor (`tests/test_textura_y_kndvi.py`):
#
#        foco real de  5 px (0,20 ha, la MMU exacta) -> 21 px afectados (0,84 ha)  x4,2
#        foco real de 12 px (0,48 ha)                -> 30 px afectados (1,20 ha)  x2,5
#
#    CONSECUENCIA OPERATIVA, y hay que separarla en dos:
#      · para **DETECTAR** ("¿hay algo raro en este sector?") la dilatacion no invalida
#        nada: el foco sigue estando adentro de la mancha marcada;
#      · para **DELIMITAR** ("¿de cuantas hectareas es?") la textura NO SIRVE. El area
#        que se le informa al cliente y la MMU de 0,20 ha tienen que seguir saliendo de
#        los ejes ESPECTRALES. Si algun dia la textura entra al criterio, la
#        vectorizacion del foco no puede salir de ella.
GLCM_VENTANA_PX = 1        # radio: 1 => ventana 3x3 => 60 m a escala 20 m
GLCM_NIVELES = 255         # cuantizacion a 8 bits
# Rango de reflectancia sobre el que se cuantiza, en unidades de reflectancia (0-1).
# FIJO a proposito (ver limite 3). 0,60 cubre NIR de dosel pleno sin recortar.
GLCM_REF_MAX = 0.60


def _glcm_contraste(img, banda):
    """Contraste GLCM de una banda, cuantizada a 8 bits sobre un rango FIJO.

    El contraste es sum_ij (i-j)^2 * p(i,j): pesa las transiciones de nivel entre
    vecinos por el cuadrado del salto. Es alto donde el dosel es heterogeneo a la
    escala de la ventana —calvas, fallas de siembra, daño en parches— y bajo donde es
    parejo, tenga el vigor que tenga. Un lote uniformemente pobre da contraste BAJO:
    por eso no es "otro indice de vigor".
    """
    ref = img.select(banda).divide(10000)
    q = (ref.clamp(0, GLCM_REF_MAX).divide(GLCM_REF_MAX)
         .multiply(GLCM_NIVELES).round().toUint8())
    # glcmTexture devuelve ~18 bandas con sufijo (`B8A_asm`, `B8A_contrast`, ...);
    # se toma solo el contraste.
    #
    # ⚠️ GOTCHA DE GEE, encontrado con la escena real T22KDV del 2026-07-15: **Earth
    # Engine RECHAZA los nombres de banda que empiezan con guion bajo.** Renombrar a
    # '_c' revienta con `Image.select: Invalid band name: '_c'` — y no falla al
    # construir el grafo, falla recien en el `getInfo`, o sea en produccion y no en el
    # editor. El nombre tiene que empezar con letra.
    return (q.glcmTexture(size=GLCM_VENTANA_PX)
            .select([banda + '_contrast'], ['CONTRASTE']))


def _textura(img):
    """Bandas de textura candidatas: TEXNIR y NDTX.

    TEXNIR — contraste GLCM en B8A (NIR estrecho, nativo de 20 m). Es la heterogeneidad
    estructural del dosel.

    NDTX — diferencia normalizada entre el contraste de B8A y el de B5 (borde rojo,
    tambien nativo de 20 m):

        NDTX = (C_B8A - C_B5) / (C_B8A + C_B5)

    ⚠️ NOMBRE: **NDTX, no NDTI.** La sigla NDTI ya esta tomada por el *Normalized
    Difference Tillage Index* (SWIR1-SWIR2, van Deventer et al. 1997), que mide
    rastrojo y no tiene nada que ver con textura. Usar NDTI aca seria fabricar la misma
    colision de nomenclatura que este repositorio ya documenta para NDWI/NDMI.

    POR QUE NORMALIZAR EN VEZ DE USAR EL CONTRASTE CRUDO: el contraste absoluto escala
    con el brillo de la escena y con la atmosfera. La diferencia normalizada entre dos
    bandas de la MISMA escena cancela la parte comun, igual que hace un indice
    espectral con la iluminacion.

    Las dos bandas se calculan SIN mascara; el enmascarado lo aplica quien las use
    (ver limite 1 del bloque de arriba).
    """
    c_nir = _glcm_contraste(img, 'B8A')
    c_re = _glcm_contraste(img, 'B5')
    texnir = c_nir.rename('TEXNIR')
    ndtx = (c_nir.subtract(c_re)
            .divide(c_nir.add(c_re).max(1e-6)).rename('NDTX'))
    return texnir.addBands(ndtx)


def _hace_falta_textura(con_textura=None):
    """¿Hay que pagar el GLCM en esta llamada?

    ⚠️ NO ES COSMETICO. `glcmTexture` construye una matriz de co-ocurrencia por pixel
    y es de lejos lo mas caro de `_indices`. El criterio lo llama una vez por escena y
    por lote, y despues descarta todo lo que no esta en `cfg.EJES`: calcular textura
    ahi seria pagar el costo mas alto del modulo para tirar el resultado, en el camino
    CALIENTE que corre dos veces por dia en la nube.

    Por defecto se calcula solo si alguna banda de textura esta declarada como eje —
    que es justo lo que hacen los arneses de medicion cuando pisan `cfg.EJES`.
    `con_textura=True` la fuerza (extraccion de archivo); `False` la apaga.
    """
    if con_textura is not None:
        return bool(con_textura)
    return any(b in cfg.EJES for b in BANDAS_TEXTURA)


def _indices(img, con_textura=None):
    """Los ejes de dosel candidatos + NDVI para la compuerta de vegetacion.

    Cuales de estos ENTRAN al criterio lo decide `cfg.EJES`, no este modulo. Se
    calculan todos porque la eleccion del par de ejes es una decision medible
    (ver `medicion/comparar_ejes.py`) y para medirla hacen falta en la serie.

    La textura es la excepcion y se decide aparte (ver `_hace_falta_textura`): es la
    unica cuyo costo justifica no calcularla siempre.
    """
    b = lambda n: img.select(n).divide(10000)
    B2, B4, B5, B6, B7, B8, B8A, B11 = (b('B2'), b('B4'), b('B5'), b('B6'),
                                        b('B7'), b('B8'), b('B8A'), b('B11'))
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
    # CANDIDATOS DE BORDE ROJO, para comparar contra PSRI como segundo eje.
    # Los dos son NATIVOS de 20 m (B5=705, B7=783, B8A=865), asi que no mezclan
    # resoluciones. El PSRI si: combina B2 y B4 (10 m) con B6 (20 m), y ademas usa
    # la banda azul, la de peor relacion senal-ruido sobre vegetacion y la mas
    # afectada por la atmosfera. Cual de los tres queda es una MEDICION, no un gusto.
    ndre = B8A.subtract(B5).divide(B8A.add(B5)).rename('NDRE')
    cire = B7.divide(B5.max(1e-6)).subtract(1).rename('CIRE')
    # kNDVI. Camps-Valls et al. 2021 (10.1126/sciadv.abc7447), ec. 6: con la longitud
    # de escala sigma = (NIR + Rojo)/2 —la que el propio paper recomienda como opcion
    # practica— el kernel RBF colapsa a kNDVI = tanh(NDVI^2), sin parametros libres.
    #
    # QUE COMPRA: NO satura donde NDVI satura (dosel cerrado). El paper lo mide contra
    # GPP de torres de flujo y contra SIF en todos los biomas y zonas climaticas, y le
    # gana a NDVI y a NIRv en las dos.
    #
    # QUE **NO** COMPRA EN ESTE MOTOR, Y ES CASI TODO. Auditado 2026-08-03, y la
    # conclusion es que kNDVI **no aporta nada aca**. Tres razones, en orden de peso:
    #
    # 1. **NDVI no es un eje del criterio.** Los ejes son NDMI y NDRE. El NDVI solo se
    #    usa para la compuerta de dosel. Un reemplazo del NDVI no toca la deteccion.
    #
    # 2. **La saturacion del NDVI no le pega a este motor.** El motor NUNCA usa valores
    #    absolutos: compara cada pixel contra su PROPIA trayectoria y contra su cohorte.
    #    La saturacion arruina los umbrales absolutos —que es contra lo que kNDVI se
    #    propuso— y este criterio no tiene ninguno.
    #
    # 3. ⚠️ **USARLO EN LA COMPUERTA SERIA UN CAMBIO NO CALIBRADO, NO UNA MEJORA.**
    #    MEDIDO sobre 20.000 pixeles sinteticos de trigo: la correlacion de RANGOS entre
    #    NDVI y kNDVI es 1,000000 —o sea que el orden es identico— pero FVC no es
    #    invariante a transformaciones monotonas NO LINEALES, asi que el umbral efectivo
    #    se corre: **1,29% de los pixeles cambian de lado de la compuerta**, y el NDVI
    #    equivalente al corte pasa de 0,6465 a 0,6510. Mover el umbral 1,29% sin ninguna
    #    razon positiva es exactamente lo que `config.py` prohibe.
    #
    # QUEDA COMO BANDA DE ARCHIVO, no como mejora: viaja en la serie para que se pueda
    # graficar y comparar, y por si algun dia el motor trabaja con umbrales absolutos o
    # con un cultivo de dosel muy cerrado. **No entra al criterio ni a la compuerta.**
    kndvi = ndvi.pow(2).tanh().rename('KNDVI')
    out = (ndvi.addBands(ndmi).addBands(psri).addBands(ndre).addBands(cire)
           .addBands(kndvi))
    if _hace_falta_textura(con_textura):
        out = out.addBands(_textura(img))
    return out


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


def extraer(sitio, ini, fin, escala=20, verbose=True, con_textura=False):
    """Devuelve el DataFrame largo (lote_id, fecha, NDVI, NDMI, PSRI, calidad...).

    `escala=20` no es una concesion: el test espacial pide agregar a 20-30 m antes
    de testear, y a 20 m un lote de 200 ha sigue teniendo ~5.000 unidades.

    `con_textura=False` por defecto Y A PROPOSITO: el GLCM es lo mas caro del modulo
    (ver `_hace_falta_textura`) y retrollenar tres campañas de 220 lotes con textura
    encendida es una corrida de otra magnitud. Se prende cuando la extraccion es PARA
    medir textura, no como default.
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
        idx = _indices(img, con_textura=con_textura)
        # Los extremos del FVC se anclan SOLO sobre pixel limpio: calcularlos
        # sobre la escena completa los ancla en la nube y la compuerta se rompe.
        fvc = _fvc(idx.select('NDVI').updateMask(valido), aoi, escala)
        # Dosel util = pixel limpio Y con cobertura vegetal suficiente.
        util = valido.And(fvc.gte(cfg.FVC_MINIMA)).rename('util')
        campos = idx.addBands(fvc).updateMask(util)
        # cobertura = fraccion del lote con observacion utilizable
        # `unmask(0, False)`: sin el segundo argumento el relleno respeta la huella
        # del granulo (sameFootprint=True), asi que los pixeles del lote que caen en
        # otro tile quedan FUERA DEL DENOMINADOR y la cobertura sale inflada en todo
        # lote que cruce un borde MGRS. Es la columna que decide `calidad` (pleno /
        # parcial), o sea que entra en el % de observaciones plenas del informe.
        pila = campos.addBands(util.unmask(0, False).rename('cob'))
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
    df = df.rename(columns={f'{b}_mean': b for b in BANDAS_DOSEL})
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
    df = df[[c for c in COLS_SERIE if c in df.columns]]
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
