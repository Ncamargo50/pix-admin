# -*- coding: utf-8 -*-
"""COHORTE REGIONAL: comparar el campo del cliente contra los lotes vecinos.

PARA QUE SIRVE, Y QUE HUECO CIERRA
----------------------------------
El criterio del motor compara cada pixel contra SU PROPIA historia dentro del lote. Eso
lo deja estructuralmente **ciego a un evento que afecte al lote entero** —una helada, un
deficit hidrico general, una roya avanzada— porque si todos los pixeles caen juntos, la
referencia cae con ellos.

El arreglo estandar es comparar entre lotes, pero eso pide >= 8 lotes y este cliente
tiene 2 y nunca va a tener mas. La salida es esta: construir la cohorte con los lotes
**de los vecinos**, sacados de la imagen, no del inventario del cliente.

COMO SE IDENTIFICA EL TRIGO, Y POR QUE NO POR FIRMA ESPECTRAL DE UNA FECHA
-------------------------------------------------------------------------
Una firma espectral de UNA fecha no separa trigo de otras coberturas verdes: en julio un
trigo en llenado, una pastura y un monte tienen NDVI parecido. Lo que SI separa es la
FENOLOGIA INVERTIDA. En Parana, en julio, no hay cultivo de verano creciendo (la soja se
cosecho en febrero-marzo y el maiz de segunda en junio-julio). Entonces:

    lo que en ABRIL estaba desnudo y en JULIO esta pleno = cereal de invierno

MEDIDO sobre el radio de 10 km de Santo Antonio (31.041 ha), compuestos de mediana:

    cobertura                abril    mayo    junio   julio   AMPLITUD jul-abr
    SANTO_ANTONIO-01 (trigo) 0,189    0,298   0,904   0,928       0,728
    SANTO_ANTONIO-02 (trigo) 0,236    0,197   0,725   0,918       0,662
    mediana del paisaje      0,652    0,707   0,816   0,863       0,098

La mediana del paisaje NO CAMBIA (amplitud 0,098): es monte, pastura y rastrojo. El trigo
conocido salta 0,66-0,73. La amplitud es el discriminador, y esta validado contra los dos
lotes de los que SI sabemos que son trigo.

⚠️ DOS LIMITES QUE HAY QUE DECLARAR, Y EL SEGUNDO ES SERIO
----------------------------------------------------------
1. **NO es "trigo": es "cereal de invierno o cobertura de invierno".** Avena, cebada,
   triticale y un nabo forrajero tienen la MISMA fenologia y Sentinel-2 no los separa.
   Se podrian separar por la senescencia de la cosecha (el trigo se seca en agosto, una
   cobertura no), pero eso exige imagenes que en julio todavia no existen. La cohorte se
   informa como lo que es.

2. **SESGO DE SELECCION: un trigo que FALLO no entra en la cohorte.** El criterio pide
   amplitud alta, o sea que exige haber crecido. Un lote vecino con mala implantacion
   tiene amplitud baja y queda AFUERA. Entonces la cohorte es una referencia de "trigo
   que emergio y crecio", no de "trigo sembrado", y por construccion esta sesgada hacia
   arriba. **Comparar contra ella hace que el campo del cliente se vea PEOR de lo que
   se veria contra la poblacion real.** Es el lado conservador del error —preferible a
   tranquilizar— pero al informar hay que decirlo.
   Se atenua con un umbral de amplitud PERMISIVO (`AMP_MINIMA`), a costa de admitir
   alguna cobertura que no es cereal.

    python -m medicion.cohorte_regional --sitio SANTO_ANTONIO --hasta 2026-07-16
"""
import argparse
import json
import sys

# --- parametros del enmascarado, todos justificados ---------------------------
RADIO_M = 10000
# NDVI MAXIMO en la ventana de siembra. Los dos lotes de trigo conocidos dieron 0,189 y
# 0,236 (suelo con rastrojo). 0,45 deja margen amplio para un lote con mas rastrojo o con
# una cobertura que no se seco del todo, sin admitir monte ni pastura (p50 del paisaje en
# abril = 0,652).
NDVI_ABRIL_MAX = 0.45
# NDVI MINIMO en la ventana de pleno. Se pone BAJO a proposito: si se exigiera el 0,92 de
# los lotes del cliente, la cohorte quedaria formada SOLO por los mejores lotes de la
# region y el campo del cliente se veria mal por construccion.
NDVI_JULIO_MIN = 0.55
# AMPLITUD MINIMA. Los dos lotes de trigo dieron 0,662 y 0,728; el p75 del paisaje es
# 0,605 y el p50 es 0,098. Se toma 0,40 —bastante por debajo del trigo conocido— para
# que entren tambien lotes vecinos que crecieron menos. Ver el limite 2 de arriba.
AMP_MINIMA = 0.40
# AREA MINIMA de un lote vecino, en ha. Por debajo de esto no es un lote: es un borde, un
# camino o una franja. Los lotes del cliente son de 18 y 120 ha.
AREA_MINIMA_HA = 5.0
# ⚠️ DEFECTO 1, ENCONTRADO EN LA PRIMERA CORRIDA REAL: las componentes conectadas de la
# mascara NO son lotes. Lotes vecinos de trigo que se tocan se fusionan en una sola
# componente, y salio una de **2.074 ha** — que no es un lote, es una region. Su mediana
# es un promedio regional y pesa lo mismo en la cohorte que un lote de 5 ha, asi que la
# distribucion de percentiles queda distorsionada.
#
# La unidad correcta es una GRILLA de celdas de tamano COMPARABLE a los lotes del
# cliente (18 y 120 ha). Se toman celdas de `LADO_CELDA_M` y se conservan las que tienen
# al menos `FRACCION_CEREAL_CELDA` de cereal: asi cada unidad de la cohorte es un pedazo
# de campo del mismo orden que el lote que se quiere comparar, y no hay fusion posible.
UNIDAD = 'grilla'                 # 'grilla' (correcto) o 'componentes' (el defecto)
LADO_CELDA_M = 500                # 25 ha por celda
FRACCION_CEREAL_CELDA = 0.70      # la celda tiene que ser mayoritariamente cereal
# Cuantas unidades como maximo. Es un tope de COSTO de la medicion, no un criterio.
# MEDIDO: con celdas de 500 m y >= 70% de cereal salen 255 celdas (6.375 ha) en el radio
# de 10 km, asi que 300 las deja entrar todas y no trunca la cohorte en silencio.
MAX_LOTES = 300
ESCALA = 20
# ⚠️ DEFECTO 2, Y ES EL GRAVE. En la primera corrida se dejo entrar la escena del
# 2026-07-05 con 79% de cobertura sobre el AOI, y **la cohorte fabrico un derrumbe**:
#
#     fecha      cobertura AOI    SANTO_ANTONIO-01 NDVI    percentil en la cohorte
#     2026-06-22      75%               0,928                    p100
#     2026-07-05      79%               0,776                    p23     <- artefacto
#     2026-07-10     100%               0,928                    p93
#     2026-07-15     100%               0,928                    p93
#
# Un trigo NO pierde 0,15 de NDVI y lo recupera en cinco dias. Era bruma sobre el campo
# del cliente que sobrevivio a la mascara. Con la cohorte cruda eso se habria informado
# como "el campo se derrumbo respecto de la region", que es una alarma inventada.
#
# La cohorte necesita la MISMA exigencia de cobertura que el criterio (0,70), y ademas
# medida SOBRE EL LOTE DEL CLIENTE y no solo sobre el AOI: el AOI puede estar limpio en
# promedio y el lote tapado.
COB_MINIMA_AOI = 0.70
# Cobertura minima sobre el LOTE DEL CLIENTE. Es la que faltaba: el 2026-07-05 tenia 79%
# sobre el AOI y aun asi el lote estaba afectado.
COB_MINIMA_LOTE = 0.70
# INCOHERENCIA ENTRE EJES como firma de artefacto. Los residuos de los dos ejes
# correlacionan 0,94-0,98 (medido), asi que un estres real los mueve JUNTOS. Cuando el
# NDVI cae y los ejes no, no es el cultivo. Observado el 2026-07-05: NDVI en p23 con NDMI
# en p56 y NDRE en p49 — una separacion de 33 puntos, contra 6 y 7 en las dos fechas
# limpias. ⚠️ SON TRES FECHAS: es un CANDIDATO a regla, no una regla calibrada.
DESACUERDO_PERCENTIL = 25


def _compuesto_ndvi(aoi, ini, fin):
    import ee

    from pix_alerta import series as sr
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(ini, fin).filterBounds(aoi))
    return col.map(lambda i: (sr._indices(ee.Image(i)).select('NDVI')
                              .updateMask(sr._mascara(ee.Image(i))))).median()


def mascara_cereal(aoi, siembra_ini, siembra_fin, pleno_ini, pleno_fin):
    """Mascara de cereal/cobertura de invierno por FENOLOGIA INVERTIDA."""
    abril = _compuesto_ndvi(aoi, siembra_ini, siembra_fin).rename('abr')
    julio = _compuesto_ndvi(aoi, pleno_ini, pleno_fin).rename('jul')
    amp = julio.subtract(abril).rename('amp')
    m = (abril.lte(NDVI_ABRIL_MAX)
         .And(julio.gte(NDVI_JULIO_MIN))
         .And(amp.gte(AMP_MINIMA)))
    return m.rename('cereal').selfMask(), abril, julio, amp


def celdas_vecinas(aoi, mascara, propio, escala=ESCALA, epsg='EPSG:31982'):
    """Unidades de comparacion de tamano FIJO, sobre la mascara de cereal.

    Cada celda es un cuadrado de `LADO_CELDA_M` que tiene que estar cubierto en al menos
    `FRACCION_CEREAL_CELDA` por la mascara. Es la unidad correcta: comparable en tamano
    al lote del cliente, y sin la fusion que arruinaba las componentes conectadas.
    """
    import ee
    grilla = aoi.coveringGrid(ee.Projection(epsg), LADO_CELDA_M)
    frac = mascara.unmask(0, False).rename('f')
    # `reduceRegions` nombra la salida segun el REDUCTOR (`mean`), no segun la banda.
    # Con `filter(gte('f', ...))` se descartaba TODO en silencio: la cohorte salia
    # vacia y el arnes decia "cohorte demasiado chica" en vez de "el filtro no
    # encuentra la propiedad". `setOutputs` fija el nombre y saca la ambiguedad.
    con = frac.reduceRegions(collection=grilla,
                             reducer=ee.Reducer.mean().setOutputs(['f']),
                             scale=escala, tileScale=4)
    con = con.filter(ee.Filter.gte('f', FRACCION_CEREAL_CELDA))
    con = con.map(lambda x: x.set('area_ha', x.geometry().area(1).divide(1e4)))
    # fuera lo que toque el campo del cliente: la cohorte es de VECINOS
    con = con.filter(ee.Filter.bounds(propio).Not())
    return con.limit(MAX_LOTES)


def lotes_vecinos(aoi, mascara, propio, escala=ESCALA):
    """Pseudo-lotes: componentes conectadas de la mascara, >= AREA_MINIMA_HA.

    Se excluye lo que toque el campo del cliente: la cohorte tiene que ser de VECINOS, o
    se estaria comparando el campo contra si mismo.
    """
    import ee
    proj = mascara.projection().atScale(escala)
    limpio = (mascara.focalMode(1.5, 'square', 'pixels').reproject(proj)
              .selfMask().toInt().rename('c'))
    vec = limpio.addBands(ee.Image.pixelArea().rename('m2')).reduceToVectors(
        reducer=ee.Reducer.sum(), geometry=aoi, scale=escala,
        geometryType='polygon', eightConnected=True, labelProperty='c',
        maxPixels=1e9, bestEffort=True)
    vec = (vec.map(lambda f: f.set('area_ha', f.geometry().area(1).divide(1e4)))
              .filter(ee.Filter.gte('area_ha', AREA_MINIMA_HA)))
    # fuera lo que toque el campo del cliente
    vec = vec.filter(ee.Filter.bounds(propio).Not())
    return vec.sort('area_ha', False).limit(MAX_LOTES)


def fechas_utiles(aoi, ini, fin, escala=60, lotes=None):
    """Fechas con cobertura suficiente SOBRE EL AOI *Y* sobre el lote del cliente.

    Las dos condiciones, porque el AOI puede estar limpio en promedio y el lote tapado —
    que es exactamente lo que paso el 2026-07-05 y fabrico un derrumbe. Ver
    `COB_MINIMA_LOTE`.
    """
    import ee

    from pix_alerta import series as sr
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(ini, fin).filterBounds(aoi))
    n = int(col.size().getInfo() or 0)
    if not n:
        return []
    lista = col.sort('system:time_start').toList(n)
    out = {}
    for i in range(n):
        img = ee.Image(lista.get(i))
        cob = (sr._mascara(img).rename('u').unmask(0, False).reduceRegion(
            ee.Reducer.mean(), aoi, escala, maxPixels=int(1e9),
            bestEffort=True).get('u'))
        f = ee.Date(img.get('system:time_start')).format('YYYY-MM-dd')
        pedido = {'f': f, 'c': ee.Algorithms.If(cob, cob, 0)}
        if lotes is not None:
            cl_ = (sr._mascara(img).rename('u').unmask(0, False).reduceRegion(
                ee.Reducer.mean(), lotes, ESCALA, maxPixels=int(1e9),
                bestEffort=True).get('u'))
            pedido['l'] = ee.Algorithms.If(cl_, cl_, 0)
        d = ee.Dictionary(pedido).getInfo()
        cob_lote = d.get('l', 1.0)
        if cob_lote < COB_MINIMA_LOTE:
            print('   %s DESCARTADA: cobertura sobre el lote del cliente %.0f%% '
                  '(minimo %.0f%%)' % (d['f'], 100 * cob_lote, 100 * COB_MINIMA_LOTE))
            continue
        # una fecha puede venir en dos granulos: se guarda el de MEJOR cobertura
        if d['c'] >= COB_MINIMA_AOI and d['c'] > out.get(d['f'], 0):
            out[d['f']] = d['c']
    return sorted(out.items())


def serie_por_lote(fc, fecha, ejes, escala=ESCALA):
    """Mediana de cada eje por lote en `fecha`. Un solo viaje a GEE."""
    import ee

    from pix_alerta import series as sr
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(fecha, ee.Date(fecha).advance(1, 'day')))
    img = ee.Image(col.sort('CLOUDY_PIXEL_PERCENTAGE').mosaic())
    idx = sr._indices(img).select(ejes).updateMask(sr._mascara(img))
    red = ee.Reducer.median().forEachBand(idx)
    return idx.reduceRegions(collection=fc, reducer=red, scale=escala,
                             tileScale=4).getInfo()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sitio', default='SANTO_ANTONIO')
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--radio', type=int, default=RADIO_M)
    ap.add_argument('--salida', default=None, help='geojson de los lotes vecinos')
    a = ap.parse_args(argv)

    import ee

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import config as cfg
    from pix_alerta import focos as fo
    cl.registrar_sitios(cl.cargar_todos())
    sitio = cfg.SITIOS.get(a.sitio)
    if sitio is None:
        print('no existe el sitio %s' % a.sitio)
        return 1
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    geoms = {str(f['properties'].get(sitio.campo_id)): fo._geom_lote(sitio, f)
             for f in gj['features']}
    propio = ee.Geometry.MultiPolygon([g.coordinates() for g in geoms.values()])
    aoi = propio.centroid(1).buffer(a.radio)
    print('AOI: radio %d m, %.0f ha' % (a.radio, aoi.area(1).getInfo() / 1e4))

    # ventanas: siembra declarada del sitio, y el pleno alrededor de `hasta`
    import pandas as pd
    siembra = sitio.siembra or str(pd.Timestamp(a.hasta) - pd.Timedelta(days=90))[:10]
    s_ini = str(pd.Timestamp(siembra) - pd.Timedelta(days=11))[:10]
    s_fin = str(pd.Timestamp(siembra) + pd.Timedelta(days=7))[:10]
    p_ini = str(pd.Timestamp(a.hasta) - pd.Timedelta(days=8))[:10]
    p_fin = str(pd.Timestamp(a.hasta) + pd.Timedelta(days=6))[:10]
    print('ventana de siembra: %s a %s   |   ventana de pleno: %s a %s'
          % (s_ini, s_fin, p_ini, p_fin))

    m, abril, julio, amp = mascara_cereal(aoi, s_ini, s_fin, p_ini, p_fin)
    ha = (m.multiply(ee.Image.pixelArea()).reduceRegion(
        ee.Reducer.sum(), aoi, ESCALA, maxPixels=int(1e9),
        bestEffort=True).get('cereal').getInfo() or 0) / 1e4
    print('\nsuperficie clasificada como cereal/cobertura de invierno: %.0f ha '
          '(%.1f%% del AOI)' % (ha, 100 * ha / (aoi.area(1).getInfo() / 1e4)))
    print('   reglas: NDVI(siembra) <= %.2f  Y  NDVI(pleno) >= %.2f  Y  amplitud >= %.2f'
          % (NDVI_ABRIL_MAX, NDVI_JULIO_MIN, AMP_MINIMA))

    if UNIDAD == 'grilla':
        fc = celdas_vecinas(aoi, m, propio)
        etq = 'celdas de %d x %d m con >= %.0f%% de cereal' % (
            LADO_CELDA_M, LADO_CELDA_M, 100 * FRACCION_CEREAL_CELDA)
    else:
        fc = lotes_vecinos(aoi, m, propio)
        etq = 'componentes conectadas >= %.0f ha (OJO: se fusionan)' % AREA_MINIMA_HA
    info = fc.getInfo()
    vecinos = info.get('features', [])
    print('unidades de cohorte: %s -> %d' % (etq, len(vecinos)))
    if len(vecinos) < 8:
        print('   OJO: con menos de 8 la cohorte no sostiene una comparacion.')
    areas = sorted((f['properties'].get('area_ha') or 0) for f in vecinos)
    if areas:
        print('   area: min %.1f  p50 %.1f  max %.1f ha  |  total %.0f ha'
              % (areas[0], areas[len(areas) // 2], areas[-1], sum(areas)))

    if a.salida:
        with open(a.salida, 'w', encoding='utf-8') as fh:
            json.dump(info, fh, ensure_ascii=False)
        print('   -> %s' % a.salida)

    # --- serie comparativa ---------------------------------------------------
    campana = (sitio.campanas or {}).get(
        sorted(sitio.campanas or {'x': None})[0], (siembra, a.hasta))
    fechas = fechas_utiles(aoi, campana[0], a.hasta, lotes=propio)
    print('\nfechas con >= %.0f%% de pixel valido sobre el AOI: %d'
          % (100 * COB_MINIMA_AOI, len(fechas)))
    for f, c in fechas:
        print('   %s  cobertura %.0f%%' % (f, 100 * c))
    if not fechas:
        print('sin fechas utiles: no hay serie que comparar')
        return 1

    ejes = list(cfg.EJES) + ['NDVI']
    # el campo del cliente entra como features mas, para medirlo con el MISMO codigo
    propios = ee.FeatureCollection([
        ee.Feature(g, {'lote': lid, 'propio': 1}) for lid, g in sorted(geoms.items())])
    todo = fc.map(lambda f: f.set('lote', ee.String('vec_').cat(
        ee.Number(f.get('area_ha')).format('%.0f')), 'propio', 0)).merge(propios)

    print('\n' + '=' * 78)
    print('COMPARACION: el campo del cliente contra la cohorte de vecinos')
    print('=' * 78)
    filas = {}
    for f, _c in fechas:
        try:
            r = serie_por_lote(todo, f, ejes)
        except Exception as exc:                        # noqa: BLE001
            print('%s AVERIA %s: %s' % (f, type(exc).__name__, str(exc)[:60]))
            continue
        coh, mio = {e: [] for e in ejes}, {}
        for ft in r.get('features', []):
            p = ft['properties']
            if p.get('propio'):
                mio[p['lote']] = {e: p.get(e) for e in ejes}
            else:
                for e in ejes:
                    if p.get(e) is not None:
                        coh[e].append(p[e])
        filas[f] = {'cohorte': coh, 'propio': mio}
        n_coh = len(coh[ejes[0]])
        print('\n%s   cohorte n=%d' % (f, n_coh))
        if n_coh < 8:
            print('   cohorte demasiado chica en esta fecha')
            continue
        for e in ejes:
            v = sorted(x for x in coh[e] if x is not None)
            if len(v) < 8:
                continue
            p10, p50, p90 = v[len(v) // 10], v[len(v) // 2], v[-max(len(v) // 10, 1)]
            linea = '   %-5s cohorte p10 %6.3f  p50 %6.3f  p90 %6.3f  |' % (
                e, p10, p50, p90)
            for lid in sorted(mio):
                x = mio[lid].get(e)
                if x is None:
                    linea += '  %s: -' % lid[-2:]
                    continue
                # posicion percentil dentro de la cohorte
                pos = 100.0 * sum(1 for y in v if y < x) / len(v)
                linea += '  %s: %.3f (p%02.0f)' % (lid[-2:], x, pos)
            print(linea)
    print("""
COMO SE LEE, Y QUE NO SE PUEDE CONCLUIR
---------------------------------------
· `p10 p50 p90` es la distribucion de los lotes VECINOS en esa fecha. La posicion
  percentil del lote del cliente dice donde cae dentro de sus vecinos.
· Caer bajo en la cohorte NO prueba un problema: los vecinos pueden ser otra variedad,
  otra fecha de siembra u otro cultivo de invierno. Lo que SI aporta es la direccion:
  si el campo del cliente cae SIEMPRE abajo, hay algo del campo; si cae con la cohorte,
  lo que pasa es regional (clima) y no de manejo.
· La cohorte esta SESGADA HACIA ARRIBA por construccion: un trigo vecino que fallo tiene
  amplitud baja y no entro. Ver el limite 2 en la cabecera del modulo.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
