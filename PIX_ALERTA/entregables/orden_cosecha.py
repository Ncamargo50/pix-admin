# -*- coding: utf-8 -*-
"""Entregable Pixadvisor — 'Ventana y orden de madurez' por hacienda.

v2 (2026-08-19, post-auditoria de tres agentes). Cambios de fondo:
  · compuerta de BRUMA por lote y fecha (pix_alerta.madurez.bruma) — el caso 26-may
  · CIre de S2C llevado a escala S2A/B con factor POR NIVEL r(c)=1+b*c, b ajustado
    dentro de la propia serie (madurez.pares_s2c / ajustar_b / corregir_cire)
  · pico calculado SOLO sobre escenas S2A/B
  · la clase "Listo / cosechado" NO existe mas: la clase final es "clorofila agotada";
    con lote de REFERENCIA SECA declarado se agrega el eje de AGUA (NDMI) y el estado
    "seco como la referencia". La humedad de grano y el PH se miden a campo.
  · "inicio de cobertura" (cruce CIre 1,0) reportado con su horquilla completa.

v4 (2026-08-21, tras auditoria de 3 agentes): columna "Seco como ref. (est.)" —
ventana estimada del cruce del NDMI al nivel p90 de la referencia seca (el MISMO
umbral que estado_final), por ajuste logistico con piso anclado (madurez.ajuste_cruce,
sigma_min = repetibilidad medida 0,021; cobertura SIMULADA del intervalo ~91 % en el
regimen publicable). La escena del 21-ago fue una verificacion de CONSISTENCIA a
2 dias (error NDMI <=0,021; una recta tambien pasa; el eje CIre la fallo) — NO valida
la fecha extrapolada; sin verdad de campo la exactitud fisica sigue sin medir. No se
publica: cruce o extremo del intervalo a >30 d de la ultima escena, <4 puntos
post-pico, bootstrap inestable o intervalo degenerado. Graficos: gantt de ventanas,
trayectorias NDMI con ajuste, mapas de agua (NDMI) junto a los de CIre.

v5 (2026-08-23): MEDICION separada de RENDER.
  · run() persiste salida/resultados_{hkey}_{fecha}.json (todo lo que el PDF
    necesita) + salida/rasteres_{hkey}_{fecha}.npz (rasteres de los mapas), y
    renderiza el PDF en ESPANOL y en PORTUGUES BRASILENO en la misma corrida
    (mismo JSON: los numeros son identicos por construccion).
  · render_pdf(resultados, idioma) y render_graficos(...) arman todo el producto
    desde ese JSON sin tocar GEE. Re-render:
        python orden_cosecha.py --render salida/resultados_SA_SF_2026-08-21.json pt
  · nivel PRO: columna de decision destacada, chips de color por estado, figuras
    numeradas, leyenda "como leer", fecha de escena en el titulo de seccion,
    contacto corporativo, pie de pagina sin colision, fechas dia-mes en todo el
    documento (PT usa 'set', no 'sep').

Uso:
    python orden_cosecha.py SA_SF 2026-08-01
Producto RELATIVO: ordena lotes por madurez. No da fecha de cosecha.
"""
import ee, json, sys, os, datetime, numpy as np, requests
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.dates import DateFormatter, MonthLocator, date2num, num2date
from matplotlib.ticker import FuncFormatter
import rasterio
from rasterio.io import MemoryFile

# RAIZ derivada de __file__: el workspace vivio en D:\ y ahora en C:\ — un
# hardcode de disco ya costo una sesion entera (30-ago)
RAIZ   = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
LOTES  = f"{RAIZ}/lotes"
MED    = f"{RAIZ}/medicion"
SALIDA = f"{RAIZ}/salida"
SKILL  = r"C:/Users/Usuario/.claude/skills/pixadvisor-propuesta-ejecutiva"
sys.path.insert(0, RAIZ)
sys.path.insert(0, f"{SKILL}/scripts")
from pix_alerta import madurez as mz
from pix_branding import Brand, TEAL as B_TEAL, LIMA_PALE, GRIS, GRIS_MED
from reportlab.platypus import PageBreak, Image, KeepTogether
from reportlab.platypus import TableStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor

# contacto corporativo: en TODO documento Pixadvisor (regla de la casa)
CONTACTO = "nilton.camargo@pixadvisor.network · +591 721 49171"

# ---------- catalogo de haciendas ----------
# fuentes: [(prefijo, geojson)] · referencia_seca (opcional): geojson de un lote que el
# cliente declara SECO — habilita el eje de agua y el estado "seco como la referencia".
HACIENDAS = {
    'SA_SF': dict(nombre="Trigo Santo Antonio + Sao Francisco",
                  fuentes=[("SA", f"{LOTES}/santo_antonio.geojson"),
                           ("SF", f"{LOTES}/sao_francisco.geojson")],
                  referencia_seca=f"{LOTES}/ref_trigo_seco_assai.geojson",
                  # PARTICION DECLARADA (opt-in; disenio consultado con dos agentes,
                  # 2026-08-19): solo para lotes cuyo cliente declaro pasadas de
                  # siembra. Geojson CONGELADO en catalogo (ids explicitos en
                  # properties.bloque_id); el numero de bloques lo fija la
                  # SEPARABILIDAD medida (SA-02: 3 pasadas declaradas -> 2 bloques,
                  # b1-b2 no separables, IC de la diferencia incluye 0); cada bloque
                  # corre su serie con su PROPIO pico (el pico del lote mezclado no
                  # es el pico de ningun plantio).
                  bloques={'SA-02': f"{LOTES}/bloques_santo_antonio_02.geojson"}),
}

CS = None   # CloudScore+ (se inicializa en _ee_init: el modo --render no toca GEE)
_f2d = lambda c: c[:2] if isinstance(c[0], (int, float)) else [_f2d(x) for x in c]


def _ee_init():
    global CS
    if CS is None:
        ee.Initialize(project='ee-gisagronomico')
        CS = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')


def cargar_lotes(fuentes):
    out = []
    for pref, path in fuentes:
        feats = json.load(open(path, encoding='utf-8'))['features']
        for k, ft in enumerate(feats, 1):
            g = ft['geometry']; ring = _f2d(g['coordinates'])
            geom = ee.Geometry(dict(type=g['type'], coordinates=ring))
            out.append(dict(id=f"{pref}-{k:02d}", geom=geom, ring=ring))
    return out


def _cire(img):
    b = lambda n: img.select(n).divide(10000)
    return b('B7').divide(b('B5').max(1e-6)).subtract(1).rename('CIRE')


def _indices(img):
    b = lambda n: img.select(n).divide(10000)
    return ee.Image.cat(
        b('B8').subtract(b('B4')).divide(b('B8').add(b('B4'))).rename('NDVI'),
        b('B4').subtract(b('B2')).divide(b('B6')).rename('PSRI'),
        b('B8A').subtract(b('B11')).divide(b('B8A').add(b('B11'))).rename('NDMI'),
        b('B2').rename('B2'),
        b('B11').rename('B11'),   # eje de agua INTRA-escena (d' 10,5x medido 19-ago);
                                  # solo vale contra la referencia en la misma escena
        _cire(img))


def trayectoria(geom, ini, fin):
    """Serie por lote con lo que la compuerta y la correccion necesitan:
    satelite, cs mediana, B2, PSRI, NDMI ademas de CIre/NDVI."""
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geom)
           .filterDate(ini, fin).linkCollection(CS, ['cs_cdf']))
    pts = []
    for i, sat in zip(col.aggregate_array('system:index').getInfo(),
                      col.aggregate_array('SPACECRAFT_NAME').getInfo()):
        im = ee.Image(col.filter(ee.Filter.eq('system:index', i)).first())
        # CloudScore+ entra en GEE HORAS despues que la escena S2: para la escena mas
        # fresca `cs_cdf` viaja como banda 100 % enmascarada y la mascara lo tira TODO
        # en silencio ('no pude mirar' disfrazado de nada). Respaldo DECLARADO: si la
        # mediana de cs_cdf es null, se enmascara por SCL (4/5) y la proteccion contra
        # bruma queda a cargo de la compuerta B2/PSRI de madurez.filtrar_bruma, que se
        # calibro exactamente para eso (caso 26-may).
        q0 = im.select('cs_cdf').reduceRegion(
            ee.Reducer.median(), geom, 20, maxPixels=1e9).getInfo().get('cs_cdf')
        if q0 is None:
            m = im.select('SCL').eq(4).Or(im.select('SCL').eq(5))
            mascara = 'SCL (CloudScore+ aun no disponible)'
        else:
            m = im.select('cs_cdf').gte(0.6)
            mascara = 'CS+'
        iv = _indices(im).updateMask(m)
        d = ee.Dictionary({
            't': im.get('system:time_start'),
            'c': im.select('B4').updateMask(m).mask().reduceRegion(
                ee.Reducer.mean(), geom, 20, maxPixels=1e9).get('B4'),
            'r': iv.reduceRegion(ee.Reducer.median(), geom, 20, maxPixels=1e9),
        }).getInfo()
        r = d.get('r') or {}
        if d['c'] and d['c'] > 0.85 and r.get('CIRE') is not None:
            pts.append(dict(
                fecha=datetime.datetime.fromtimestamp(
                    d['t'] / 1000, datetime.timezone.utc).strftime('%Y-%m-%d'),
                sat=sat[-1], cs_med=round(q0, 3) if q0 is not None else None,
                mascara=mascara,
                CIre=round(r['CIRE'], 3), PSRI=round(r['PSRI'], 4),
                NDMI=round(r['NDMI'], 4), NDVI=round(r['NDVI'], 3),
                B2=round(r['B2'], 4), B11=round(r['B11'], 4)))
    return sorted(pts, key=lambda x: x['fecha'])


def trayectoria_landsat(geom, ini, fin):
    """Puntos Landsat 8/9 SOLO para el eje de AGUA (NDMI + NDVI + B2): sin red-edge
    no hay CIre, asi que jamas tocan pico/avance/estado. Compuertas: QA_PIXEL
    (nube bit 3, sombra 4, cirro 2), cobertura >= 0.85 y B2 <= 0.15 (anti-bruma,
    mismo corte que madurez.bruma; Landsat no tiene CloudScore+ ni PSRI con B6
    red-edge, el azul es la firma que queda)."""
    col = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
           .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
           .filterBounds(geom).filterDate(ini, fin))
    pts = []
    for i in col.aggregate_array('system:index').getInfo():
        im = ee.Image(col.filter(ee.Filter.eq('system:index', i)).first())
        qa = im.select('QA_PIXEL').toInt()
        m = (qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
             .And(qa.bitwiseAnd(1 << 2).eq(0)))
        sr = lambda b: im.select(b).multiply(0.0000275).add(-0.2)
        iv = ee.Image.cat(
            sr('SR_B5').subtract(sr('SR_B6')).divide(sr('SR_B5').add(sr('SR_B6'))).rename('NDMI'),
            sr('SR_B5').subtract(sr('SR_B4')).divide(sr('SR_B5').add(sr('SR_B4'))).rename('NDVI'),
            sr('SR_B2').rename('B2')).updateMask(m)
        d = ee.Dictionary({
            't': im.get('system:time_start'),
            's': im.get('SPACECRAFT_ID'),
            'c': im.select('SR_B4').updateMask(m).mask().reduceRegion(
                ee.Reducer.mean(), geom, 30, maxPixels=1e9).get('SR_B4'),
            'r': iv.reduceRegion(ee.Reducer.median(), geom, 30, maxPixels=1e9),
        }).getInfo()
        r = d.get('r') or {}
        if (d['c'] and d['c'] > 0.85 and r.get('NDMI') is not None
                and r.get('B2') is not None and r['B2'] <= mz.B2_MAX):
            pts.append(dict(
                fecha=datetime.datetime.fromtimestamp(
                    d['t'] / 1000, datetime.timezone.utc).strftime('%Y-%m-%d'),
                sat='L9' if str(d.get('s', '')).endswith('9') else 'L8',
                NDMI=round(r['NDMI'], 4), NDVI=round(r['NDVI'], 3),
                B2=round(r['B2'], 4)))
    return sorted(pts, key=lambda x: x['fecha'])


def cortes_referencia(geom, fecha):
    """p50/p90 de CIre y NDMI de la referencia seca en el compuesto limpio ~fecha.

    Con compuerta de BRUMA por escena (auditoria 21-ago): CloudScore+ dejo pasar la
    bruma del 26-may — si la unica escena de la ventana ±5 dias es brumosa, el piso
    de TODO el producto sale corrido. Cada escena se somete a mz.bruma() sobre el
    poligono de la referencia antes de entrar al compuesto."""
    d = datetime.date.fromisoformat(fecha)
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geom)
           .filterDate((d - datetime.timedelta(5)).isoformat(),
                       (d + datetime.timedelta(5)).isoformat())
           .linkCollection(CS, ['cs_cdf']))
    limpias = []
    for i in col.aggregate_array('system:index').getInfo():
        im = ee.Image(col.filter(ee.Filter.eq('system:index', i)).first())
        q = ee.Image.cat(im.select('cs_cdf'),
                         _indices(im).select(['PSRI', 'B2'])).reduceRegion(
            ee.Reducer.median(), geom, 20, maxPixels=1e9).getInfo()
        es, _rz = mz.bruma(q.get('cs_cdf'), q.get('PSRI'), q.get('B2'))
        if not es and q.get('B2') is not None:
            limpias.append(i)
    if not limpias:
        return None
    col = (col.filter(ee.Filter.inList('system:index', limpias))
           .map(lambda im: im.updateMask(
               im.select('cs_cdf').gte(0.6).unmask(
                   im.select('SCL').eq(4).Or(im.select('SCL').eq(5))))))
    img = _indices(col.median())
    q = img.select(['CIRE', 'NDMI', 'B11']).reduceRegion(
        ee.Reducer.percentile([50, 90]), geom, 20, maxPixels=1e9).getInfo()
    if q.get('CIRE_p90') is None:
        return None
    return dict(cire_p50=q['CIRE_p50'], cire_p90=q['CIRE_p90'],
                ndmi_p50=q['NDMI_p50'], ndmi_p90=q['NDMI_p90'],
                b11_p50=q['B11_p50'])


def raster_rgb(geom, fecha):
    """Fondo RGB (compuesto ±3 dias, sin mascara: el fondo se ve entero) con 300 m
    de contexto alrededor del lote."""
    d = datetime.date.fromisoformat(fecha)
    ini = (d - datetime.timedelta(3)).isoformat(); fin = (d + datetime.timedelta(3)).isoformat()
    reg = geom.buffer(600, 10)
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geom)
           .filterDate(ini, fin))
    img = col.median().select(['B4', 'B3', 'B2']).divide(10000).toFloat().clip(reg)
    url = img.getDownloadURL({'region': reg, 'scale': 10, 'format': 'GEO_TIFF', 'filePerBand': False})
    with MemoryFile(requests.get(url).content) as mf, mf.open() as ds:
        a = ds.read().astype(float); b = ds.bounds
    a = np.where(np.isfinite(a), a, 0)
    img_ = np.clip(a / 0.28, 0, 1) ** (1 / 1.7)          # estiramiento + gamma
    val = (a.sum(0) > 0).astype(float)
    rgba = np.dstack([img_[0], img_[1], img_[2], val])
    return rgba, [b.left, b.right, b.bottom, b.top]


def raster_indice(geom, fecha, banda='CIRE'):
    d = datetime.date.fromisoformat(fecha)
    ini = (d - datetime.timedelta(3)).isoformat(); fin = (d + datetime.timedelta(3)).isoformat()
    # donde CloudScore+ existe decide CS+; donde aun no llego (banda enmascarada),
    # decide SCL 4/5 — mismo respaldo declarado que en trayectoria(). Sin esto el
    # mapa de la escena mas fresca sale VACIO en silencio.
    def _m(im):
        cs_ok = im.select('cs_cdf').gte(0.55)
        scl_ok = im.select('SCL').eq(4).Or(im.select('SCL').eq(5))
        return im.updateMask(cs_ok.unmask(scl_ok))
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geom)
           .filterDate(ini, fin).linkCollection(CS, ['cs_cdf'])
           .map(_m))
    img = _indices(col.median()).select(banda).clip(geom)
    url = img.getDownloadURL({'region': geom, 'scale': 10, 'format': 'GEO_TIFF'})
    with MemoryFile(requests.get(url).content) as mf, mf.open() as ds:
        a = ds.read(1, masked=True).astype(float).filled(np.nan); b = ds.bounds
    return a, [b.left, b.right, b.bottom, b.top]


def raster_cire(geom, fecha):
    return raster_indice(geom, fecha, 'CIRE')


# ---------- textos por idioma (los NUMEROS salen del mismo JSON: identicos) ----------
TEAL, LIMA = '#0D9488', '#7FD633'
# fechas SIEMPRE dia-mes con nombre ('29-ago'): '09-01' se lee 9 de enero en pt-BR
MESES    = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
MESES_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']


def _dm(iso, meses=MESES):
    return f"{int(iso[8:10]):02d}-{meses[int(iso[5:7]) - 1]}"


TXT = {
 'es': dict(
    meses=MESES,
    figura="Figura",
    footer="Orden de madurez %s · Trigo",
    cover_title="Orden de madurez — Trigo",
    cover_sub="%s · Análisis satelital del %s",
    ficha="Ficha", cliente="Cliente", lotes_k="Lotes", analisis_k="Análisis",
    producto_k="Producto", contacto_k="Contacto",
    analisis_v="Sentinel-2 (+ Landsat 8/9 en el eje de agua) · escena del %s",
    producto_v="Orden relativo de madurez (no es fecha de cosecha)",
    situacion="Situación",
    situacion_txt="Lotes con clorofila agotada: %d. Más avanzado: %s. "
                  "La humedad de grano y el PH (peso hectolítrico) se miden a campo.",
    comoleer="Cómo leer este documento",
    ley_col=("Estado", "Significado"),
    leyenda=[("#1B7A1B", "Verde (&lt;15 %)", "En llenado; sin caída relevante del CIre."),
             ("#7FD633", "Caída inicial (15-40 %)", "La senescencia comenzó."),
             ("#B8860B", "Caída avanzada (40-70 %)", "Senescencia dominante."),
             ("#CC0000", "Clorofila agotada (≥70 %)", "CIre en piso; el eje que separa pasa a ser el agua del dosel (NDMI)."),
             ("#8B5A2B", "Seco como la referencia", "CIre y NDMI al nivel de la referencia seca declarada por el cliente.")],
    ley_simbolos="Símbolos de la tabla: '-' = serie aún no ajustable o cruce a más de 30 días "
                 "(no se extrapola) · 'alcanzado' = la última medición ya está al nivel de la "
                 "referencia · 'ver sectores' = lote desparejo: el número accionable vive en las sub-filas.",
    resumen="Resumen",
    kpi=("lotes", "ha", "clorofila agotada", "más avanzado"),
    cinta_cap="Verde = en llenado · rojo = clorofila agotada. Línea punteada = fecha de análisis. "
              "CIre de S2C llevado a escala S2A/B (factor por nivel).",
    sec1="Orden de madurez — escena del %s",
    cols=("#", "Lote / Sector", "Área", "Estado", "Avance", "NDMI", "Seco como ref. (est.)"),
    desparejo_fila="DESPAREJO: ver sectores",
    ver_sectores="ver sectores", alcanzado="alcanzado",
    convergieron="   - bloques convergieron: se reportan juntos",
    nota_sectores="Sectores: pasadas y fechas de siembra declaradas por el cliente; el límite entre "
                  "sectores está estimado por satélite (NDVI may-jul), es fijo durante la campaña y no es "
                  "catastral (±10-20 m). Las pasadas del 26 y 29-abr no se distinguen en madurez y se "
                  "reportan como un solo sector. Cada sector se mide contra su PROPIO pico. "
                  "El orden del lote lo fija su sector más avanzado.",
    nota_ref="Referencia seca declarada por el cliente: CIre ≤ %s y NDMI ≤ %s. "
             "'Seco como la referencia' exige los dos ejes: cuando la clorofila toca piso, "
             "el que separa es el agua del dosel (NDMI).",
    nota_ventana="'Seco como ref. (est.)' = ventana estimada en que el lote alcanza el nivel de "
                 "agua de dosel de la referencia seca (NDMI ≤ p90 de la referencia, el mismo "
                 "umbral del estado), por ajuste de la trayectoria NDMI con piso anclado en la "
                 "referencia, medido en el compuesto ±5 días de la fecha de análisis. El "
                 "intervalo usa la repetibilidad medida del NDMI (0,021); cobertura simulada "
                 "~90 % en el régimen publicable. Es una fecha de estado espectral, no de "
                 "cosecha: la humedad de grano y el PH (peso hectolítrico) se miden a campo. "
                 "La ventana asume la trayectoria de secado observada: lluvia re-humedece el "
                 "dosel y la corre hacia adelante; se recalcula con cada escena limpia (~5 "
                 "días). '-' = serie aún no ajustable o cruce a más de 30 días (no se "
                 "extrapola). 'alcanzado' = la última medición ya está al nivel de la referencia.",
    nota_control="Control de consistencia (21-ago-2026): el ajuste construido solo con datos al "
                 "19-ago reprodujo el NDMI de la escena siguiente con error ≤ 0,021. Es una "
                 "verificación a 2 días, no una validación de la fecha extrapolada; el eje CIre "
                 "no pasó la misma prueba y por eso las fechas se estiman solo sobre el agua.",
    nota_b11="En la escena del análisis, la banda B11 (agua) de todas las unidades "
             "quedó %s-%s por debajo de la referencia seca: ningún dosel alcanzó su estado.",
    nota_no_eval="Referencia seca declarada pero SIN escena limpia en ±5 días de la fecha de "
                 "análisis: el eje de agua y la columna 'Seco como ref. (est.)' NO SON "
                 "EVALUABLES en esta corrida. Se reintenta en el próximo paso satelital.",
    nota_bruma="Fechas excluidas por bruma (cs mediana < 0,80, PSRI < −0,02 o B2 > 0,15): ",
    sec2="Ventana estimada de secado",
    gantt_cap="Barra = intervalo de la estimación (cobertura simulada ~90 %) · punto = estimación central · línea roja = "
              "fecha de análisis. Estado espectral, no fecha de cosecha.",
    tray_cap="Círculos = NDMI Sentinel-2 · triángulos = Landsat 8/9 (offset +0,02 medido, ya "
             "corregido) · curva = ajuste logístico con piso en la referencia seca · "
             "punteada = nivel de cruce.",
    sec3="Mapas por lote: madurez y agua del dosel",
    mapa_cire_cap="CIre (clorofila): rojo = clorofila agotada. Ordena la madurez general.",
    mapa_ndmi_cap="NDMI (agua del dosel): marrón = más seco, azul-verde = más húmedo. DENTRO de cada "
                  "lote, los sectores marrones se secan primero: por ahí empezar el muestreo de "
                  "humedad de grano.",
    mapa_zonas_cap="Proximidad en 5 zonas con hectareas por clase: el nivel trillable es el p90 de la referencia seca de esta corrida (medido a campo 29-ago: ~18 % de humedad al alcanzarlo = inicio de ventana de trilla, PH 78; la zona cerca midio 23 %). Los dias asumen la tasa de secado medida y sin lluvia. La barra de cada lote dice cuantas hectareas entran esta semana y cuantas despues.",
    sec4="Método y alcance",
    metodo="Madurez por caída del CIre respecto del pico propio (pico solo con escenas S2A/B; "
           "S2C corregido por nivel). Compuerta de bruma por lote y fecha. Producto RELATIVO: "
           "ordena lotes para priorizar el muestreo de humedad de grano. La columna 'Seco como "
           "ref. (est.)' es la fecha estimada de un estado espectral (agua de dosel al nivel de "
           "la referencia seca declarada), no una fecha de cosecha: la ventana de trilla la "
           "fijan la humedad de grano y el PH (peso hectolítrico) medidos a campo. El eje de agua (NDMI) suma escenas Landsat 8/9 (SWIR equivalente; offset +0,02 medido en 12 pares mismo día y corregido) para asegurar cadencia cerca de la ventana.",
    prox="Próximo paso",
    prox_txt="Medir humedad de grano y PH (peso hectolítrico) empezando por %s. Reevaluar en el "
             "próximo paso satelital limpio (~5 días). Contacto: " + CONTACTO + ".",
    # --- graficos ---
    g_cinta_tit="Madurez del trigo por lote (CIre en escala S2A/B) — verde = en llenado · rojo = clorofila agotada",
    g_cinta_labels=('Clor. agotada', 'Madurando', 'Verde', 'Pleno'),
    g_gantt_tit='Ventana estimada "seco como la referencia" — estado espectral, no fecha de cosecha',
    g_gantt_sin='sin estimación publicable (serie no ajustable o cruce a >30 días)',
    g_gantt_alc='alcanzado (%s)',
    g_gantt_ana=' análisis %s',
    g_tray_tit='Agua del dosel (NDMI): trayectoria medida y ajuste con piso en la referencia seca',
    g_tray_yl='NDMI (agua del dosel)',
    g_tray_nivel='  nivel de la referencia seca declarada (NDMI p90)',
    g_tray_alc=' (nivel alcanzado)',
    g_tray_sin=' (sin ajuste publicable)',
    g_mapa_tit='Madurez dentro de cada lote · %s · CIre, superficie suavizada (~30 m) para lectura',
    g_agua_tit='Agua del dosel por lote · %s · NDMI, superficie suavizada (~30 m) para lectura',
    g_agua_labels=('Seco', 'Secándose', 'Húmedo', 'Muy húmedo'),
    g_ref_marca='ref. seca', g_avance='avance',
 ),
 'pt': dict(
    meses=MESES_PT,
    figura="Figura",
    footer="Ordem de maturação %s · Trigo",
    cover_title="Ordem de maturação — Trigo",
    cover_sub="%s · Análise por satélite de %s",
    ficha="Ficha", cliente="Cliente", lotes_k="Talhões", analisis_k="Análise",
    producto_k="Produto", contacto_k="Contato",
    analisis_v="Sentinel-2 (+ Landsat 8/9 no eixo de água) · cena de %s",
    producto_v="Ordem relativa de maturação (não é data de colheita)",
    situacion="Situação",
    situacion_txt="Talhões com clorofila esgotada: %d. Mais avançado: %s. "
                  "A umidade do grão e o PH (peso hectolítrico) se medem no campo.",
    comoleer="Como ler este documento",
    ley_col=("Estado", "Significado"),
    leyenda=[("#1B7A1B", "Verde (&lt;15 %)", "Em enchimento; sem queda relevante do CIre."),
             ("#7FD633", "Queda inicial (15-40 %)", "A senescência começou."),
             ("#B8860B", "Queda avançada (40-70 %)", "Senescência dominante."),
             ("#CC0000", "Clorofila esgotada (≥70 %)", "CIre no piso; o eixo que separa passa a ser a água do dossel (NDMI)."),
             ("#8B5A2B", "Seca como a referência", "CIre e NDMI no nível da referência seca declarada pelo cliente.")],
    ley_simbolos="Símbolos da tabela: '-' = série ainda não ajustável ou cruzamento a mais de 30 dias "
                 "(não se extrapola) · 'atingido' = a última medição já está no nível da "
                 "referência · 'ver setores' = talhão desuniforme: o número acionável vive nas sublinhas.",
    resumen="Resumo",
    kpi=("talhões", "ha", "clorofila esgotada", "mais avançado"),
    cinta_cap="Verde = em enchimento · vermelho = clorofila esgotada. Linha pontilhada = data de "
              "análise. CIre do S2C levado à escala S2A/B (fator por nível).",
    sec1="Ordem de maturação — cena de %s",
    cols=("#", "Talhão / Setor", "Área", "Estado", "Avanço", "NDMI", "Seco como a referência (est.)"),
    desparejo_fila="DESUNIFORME: ver setores",
    ver_sectores="ver setores", alcanzado="atingido",
    convergieron="   - blocos convergiram: reportados juntos",
    nota_sectores="Setores: passadas e datas de semeadura declaradas pelo cliente; o limite entre "
                  "setores foi estimado por satélite (NDVI mai-jul), é fixo durante a safra e não é "
                  "cadastral (±10-20 m). As passadas de 26 e 29-abr não se distinguem em maturação e "
                  "são reportadas como um único setor. Cada setor é medido contra o seu PRÓPRIO pico. "
                  "A ordem do talhão é definida pelo seu setor mais avançado.",
    nota_ref="Referência seca declarada pelo cliente: CIre ≤ %s e NDMI ≤ %s. "
             "'Seca como a referência' exige os dois eixos: quando a clorofila toca o piso, "
             "o que separa é a água do dossel (NDMI).",
    nota_ventana="'Seco como a referência (est.)' = janela estimada em que o talhão atinge o nível "
                 "de água do dossel da referência seca (NDMI ≤ p90 da referência, o mesmo limiar "
                 "do estado), por ajuste da trajetória do NDMI com piso ancorado na referência, "
                 "medida no composto ±5 dias da data de análise. O intervalo usa a repetibilidade "
                 "medida do NDMI (0,021); cobertura simulada ~90 % no regime publicável. É uma "
                 "data de estado espectral, NÃO uma data de colheita: a umidade do grão e o PH "
                 "(peso hectolítrico) se medem no campo. A janela assume a trajetória de secagem "
                 "observada: chuva re-umedece o dossel e empurra a janela para a frente; "
                 "recalcula-se a cada cena limpa (~5 dias). '-' = série ainda não ajustável ou "
                 "cruzamento a mais de 30 dias (não se extrapola). 'atingido' = a última medição "
                 "já está no nível da referência.",
    nota_control="Controle de consistência (21-ago-2026): o ajuste construído somente com dados "
                 "até 19-ago reproduziu o NDMI da cena seguinte com erro ≤ 0,021. É uma "
                 "verificação a 2 dias, não uma validação da data extrapolada; o eixo CIre não "
                 "passou na mesma prova e por isso as datas se estimam somente sobre a água.",
    nota_b11="Na cena da análise, a banda B11 (água) de todas as unidades ficou %s-%s abaixo "
             "da referência seca: nenhum dossel atingiu o seu estado.",
    nota_no_eval="Referência seca declarada mas SEM cena limpa em ±5 dias da data de análise: "
                 "o eixo de água e a coluna 'Seco como a referência (est.)' NÃO SÃO AVALIÁVEIS "
                 "nesta rodada. Nova tentativa no próximo passe do satélite.",
    nota_bruma="Datas excluídas por bruma/névoa seca (cs mediana < 0,80, PSRI < −0,02 ou B2 > 0,15): ",
    sec2="Janela estimada de secagem",
    gantt_cap="Barra = intervalo da estimativa (cobertura simulada ~90 %) · ponto = estimativa central · linha vermelha = "
              "data de análise. Estado espectral, não data de colheita.",
    tray_cap="Círculos = NDMI Sentinel-2 · triângulos = Landsat 8/9 (offset +0,02 medido, já "
             "corrigido) · curva = ajuste logístico com piso na referência seca · "
             "pontilhada = nível de cruzamento.",
    sec3="Mapas por talhão: maturação e água do dossel",
    mapa_cire_cap="CIre (clorofila): vermelho = clorofila esgotada. Ordena a maturação geral.",
    mapa_ndmi_cap="NDMI (água do dossel): marrom = mais seco, azul-esverdeado = mais úmido. DENTRO "
                  "de cada talhão, os setores marrons secam primeiro: por aí começar a amostragem "
                  "de umidade do grão.",
    mapa_zonas_cap="Proximidade em 5 zonas com hectares por classe: o nivel trilhavel e o p90 da referencia seca desta rodada (medido no campo 29-ago: ~18 % de umidade ao atingi-lo = inicio da janela de trilha, PH 78; a zona perto mediu 23 %). Os dias assumem a taxa de secagem medida e sem chuva. A barra de cada talhao diz quantos hectares entram nesta semana e quantos depois.",
    sec4="Método e alcance",
    metodo="Maturação pela queda do CIre em relação ao pico próprio (pico somente com cenas "
           "S2A/B; S2C corrigido por nível). Comporta de bruma/névoa seca por talhão e data. "
           "Produto RELATIVO: ordena talhões para priorizar a amostragem de umidade do grão. "
           "A coluna 'Seco como a referência (est.)' é a data estimada de um estado espectral "
           "(água do dossel no nível da referência seca declarada), não uma data de colheita: "
           "a janela de trilha é definida pela umidade do grão e pelo PH (peso hectolítrico) "
           "medidos no campo. O eixo de água (NDMI) soma cenas Landsat 8/9 (SWIR equivalente; offset +0,02 medido em 12 pares no mesmo dia e corrigido) para garantir cadência perto da janela.",
    prox="Próximo passo",
    prox_txt="Medir umidade do grão e PH (peso hectolítrico) começando por %s. Reavaliar no "
             "próximo passe limpo do satélite (~5 dias). Contato: " + CONTACTO + ".",
    # --- graficos ---
    g_cinta_tit="Maturação do trigo por talhão (CIre na escala S2A/B) — verde = em enchimento · vermelho = clorofila esgotada",
    g_cinta_labels=('Clor. esgotada', 'Amadurecendo', 'Verde', 'Pleno'),
    g_gantt_tit='Janela estimada "seca como a referência" — estado espectral, não data de colheita',
    g_gantt_sin='sem estimativa publicável (série não ajustável ou cruzamento a >30 dias)',
    g_gantt_alc='atingido (%s)',
    g_gantt_ana=' análise %s',
    g_tray_tit='Água do dossel (NDMI): trajetória medida e ajuste com piso na referência seca',
    g_tray_yl='NDMI (água do dossel)',
    g_tray_nivel='  nível da referência seca declarada (NDMI p90)',
    g_tray_alc=' (nível atingido)',
    g_tray_sin=' (sem ajuste publicável)',
    g_mapa_tit='Maturação dentro de cada talhão · %s · CIre, superfície suavizada (~30 m) para leitura',
    g_agua_tit='Água do dossel por talhão · %s · NDMI, superfície suavizada (~30 m) para leitura',
    g_agua_labels=('Seco', 'Secando', 'Úmido', 'Muito úmido'),
    g_ref_marca='ref. seca', g_avance='avanço',
 ),
}

# estados de madurez.py (es) -> pt-BR fiel; y acentuacion para display en es
_EST_PT = [
    ('Clorofila agotada, dosel aun humedo', 'Clorofila esgotada, dossel ainda úmido'),
    ('Clorofila agotada (>=70 %)', 'Clorofila esgotada (>=70 %)'),
    ('Caida avanzada (40-70 %)', 'Queda avançada (40-70 %)'),
    ('Caida inicial (15-40 %)', 'Queda inicial (15-40 %)'),
    ('Seco como la referencia', 'Seca como a referência'),
    ('desparejo, ver mapa', 'desuniforme, ver mapa'),
    ('Sector', 'Setor'),
]
_EST_ES = [
    ('Clorofila agotada, dosel aun humedo', 'Clorofila agotada, dosel aún húmedo'),
    ('Caida avanzada', 'Caída avanzada'),
    ('Caida inicial', 'Caída inicial'),
]
# forma corta para la celda de la tabla
_EST_CORTO = {
    'es': ('Clorofila agotada, dosel aún húmedo', 'Clor. agotada, aún húmedo'),
    'pt': ('Clorofila esgotada, dossel ainda úmido', 'Clor. esgotada, ainda úmido'),
}


def traducir_estado(txt, idioma):
    for a, b in (_EST_PT if idioma == 'pt' else _EST_ES):
        txt = txt.replace(a, b)
    return txt


def _nombre_display(nombre, idioma):
    """Nombre del cliente para portada/textos ('Sao Francisco' lleva tilde en pt)."""
    if idioma == 'pt':
        return nombre.replace('Sao Francisco', 'São Francisco')
    return nombre


# ---------- render de graficos ----------
CMAP = plt.get_cmap('RdYlGn'); VMIN, VMAX = 0.2, 5.3
COL_RK = {0: '#1B7A1B', 1: '#7FD633', 2: '#B8860B', 3: '#CC0000'}


def _fmt_mes(meses):
    return FuncFormatter(lambda x, _: meses[num2date(x).month - 1])


def cinta(lotes_ord, fecha, out, T):
    meses = T['meses']
    d0, d1 = datetime.date(int(fecha[:4]), 5, 1), datetime.date.fromisoformat(fecha) + datetime.timedelta(3)
    days = [d0 + datetime.timedelta(n) for n in range((d1 - d0).days + 1)]
    xn = np.array([date2num(x) for x in days])
    grid = np.full((len(lotes_ord), len(days)), np.nan)
    for i, r in enumerate(lotes_ord):
        dd = [date2num(datetime.date.fromisoformat(p['fecha'])) for p in r['serie']]
        vv = [p['cire_corr'] for p in r['serie']]
        if len(dd) < 2:
            continue
        m = (xn >= dd[0]) & (xn <= dd[-1]); grid[i, m] = np.interp(xn[m], dd, vv)
    fig, ax = plt.subplots(figsize=(11, 0.62 * len(lotes_ord) + 1.6))
    im = ax.imshow(grid, aspect='auto', cmap=CMAP, vmin=VMIN, vmax=VMAX,
                   extent=[xn[0], xn[-1], len(lotes_ord) - 0.5, -0.5], interpolation='bilinear')
    ax.set_yticks(range(len(lotes_ord)))
    ax.set_yticklabels([f"{r['id']}  ({r['area']:.0f} ha)" for r in lotes_ord], fontsize=10)
    ax.xaxis_date(); ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(_fmt_mes(meses))
    ax.axvline(date2num(datetime.date.fromisoformat(fecha)), color='k', ls=':', lw=1.2)
    ax.set_title(T['g_cinta_tit'], fontsize=12, fontweight='bold')
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.035); cb.set_ticks([0.35, 1.6, 3.2, 5.0])
    cb.set_ticklabels(list(T['g_cinta_labels'])); cb.ax.tick_params(labelsize=8)
    plt.tight_layout(); plt.savefig(out, dpi=140, bbox_inches='tight'); plt.close()


def gantt_ventanas(filas, fecha, out, T):
    """El grafico de DECISION: calendario con una barra por unidad = intervalo (cobertura simulada ~90 %) de la
    ventana estimada 'seco como la referencia', punto = estimacion central, linea
    punteada = fecha de analisis. Unidad sin ventana publicable -> rotulo explicito
    (nunca una barra inventada)."""
    meses = T['meses']; dm = lambda iso: _dm(iso, meses)
    f0 = datetime.date.fromisoformat(fecha)
    fig, ax = plt.subplots(figsize=(11, 0.66 * len(filas) + 1.9))
    xmin = f0 - datetime.timedelta(2); xmax = f0 + datetime.timedelta(14)
    for y, r in enumerate(filas[::-1]):
        v = r.get('ventana')
        if v and v.get('alcanzado'):
            fc = datetime.date.fromisoformat(v['fecha'])
            ax.plot(date2num(fc), y, '*', color=LIMA, ms=14, mec='#3A6B12', zorder=4)
            ax.annotate(T['g_gantt_alc'] % dm(v['fecha']), (date2num(fc), y + 0.32),
                        ha='center', fontsize=9, fontweight='bold', color='#3A6B12')
        elif v and v.get('ic'):
            fc = datetime.date.fromisoformat(v['fecha'])
            a = datetime.date.fromisoformat(v['ic'][0])
            b_ = datetime.date.fromisoformat(v['ic'][1])
            ax.barh(y, max((b_ - a).days, 0.5), left=date2num(a), height=0.46,
                    color=TEAL, alpha=0.8, edgecolor='none', zorder=3)
            xmax = max(xmax, b_ + datetime.timedelta(4))
            ax.plot(date2num(fc), y, 'o', color='#083D3A', ms=7, zorder=4)
            ax.annotate(dm(v['fecha']), (date2num(fc), y + 0.32), ha='center',
                        fontsize=9, fontweight='bold', color='#083D3A')
            xmax = max(xmax, fc + datetime.timedelta(5))
        else:
            ax.annotate(T['g_gantt_sin'],
                        (date2num(f0 + datetime.timedelta(1)), y), va='center',
                        fontsize=8.5, color='#8A8A8A', style='italic')
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([f"{r['id']}  ({r['area']:.0f} ha)" for r in filas[::-1]], fontsize=10)
    ax.axvline(date2num(f0), color='#CC0000', ls='--', lw=1.2)
    ax.annotate(T['g_gantt_ana'] % dm(f0.isoformat()), (date2num(f0), len(filas) - 0.42),
                fontsize=8.5, color='#CC0000')
    ax.set_xlim(date2num(xmin), date2num(xmax)); ax.set_ylim(-0.6, len(filas) - 0.25)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda x, _: dm(num2date(x).date().isoformat())))
    ax.grid(axis='x', alpha=0.3); ax.set_axisbelow(True)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.set_title(T['g_gantt_tit'], fontsize=12, fontweight='bold', loc='left')
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()


def trayectorias_ndmi(unis, nivel, fecha, out, T):
    """La EVIDENCIA de las ventanas: puntos NDMI medidos por unidad + curva del
    ajuste logistico (piso anclado en la referencia seca) + nivel de cruce."""
    meses = T['meses']
    fig, ax = plt.subplots(figsize=(11, 5.0))
    cmap = plt.get_cmap('tab10')
    f0 = datetime.date.fromisoformat(fecha)
    for j, u in enumerate(unis):
        col = cmap(j % 10)
        # serie de agua fusionada si existe (S2 circulos, Landsat triangulos)
        fuente = u.get('serie_agua') or u['serie']
        pts_s2 = [(datetime.date.fromisoformat(p['fecha']), p['NDMI'])
                  for p in fuente if p.get('NDMI') is not None
                  and p.get('src', 'S2') == 'S2']
        pts_l = [(datetime.date.fromisoformat(p['fecha']), p['NDMI'])
                 for p in fuente if p.get('NDMI') is not None
                 and p.get('src', 'S2') != 'S2']
        ax.plot([d for d, _ in pts_s2], [v for _, v in pts_s2], 'o', ms=4.5, color=col)
        if pts_l:
            ax.plot([d for d, _ in pts_l], [v for _, v in pts_l], '^', ms=5.5,
                    color=col, markeredgecolor='white', markeredgewidth=0.6)
        v = u.get('ventana')
        if v and v.get('params'):
            pp = v['params']
            d0 = datetime.date.fromisoformat(pp['d0'])
            t = np.linspace(0, (f0 - d0).days + 26, 240)
            y = pp['piso'] + pp['A'] / (1 + np.exp((t - pp['t0']) / pp['tau']))
            # datetime (no date): date+timedelta trunca a dias enteros y la curva
            # sale escalonada
            d0t = datetime.datetime(d0.year, d0.month, d0.day)
            ax.plot([d0t + datetime.timedelta(days=float(x)) for x in t], y,
                    '-', lw=1.6, color=col, label=u['id'])
        elif v and v.get('alcanzado'):
            ax.plot([], [], 'o-', color=col, label=u['id'] + T['g_tray_alc'])
        else:
            ax.plot([], [], 'o-', color=col, label=u['id'] + T['g_tray_sin'])
    ax.axhline(nivel, color='k', ls=':', lw=1.2)
    ax.annotate(T['g_tray_nivel'], (date2num(f0 - datetime.timedelta(55)), nivel),
                fontsize=8.5, va='bottom')
    ax.axvline(date2num(f0), color='#CC0000', ls='--', lw=1.0, alpha=0.7)
    ax.set_xlim(date2num(datetime.date(int(fecha[:4]), 6, 1)), date2num(f0 + datetime.timedelta(28)))
    ax.xaxis_date(); ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(_fmt_mes(meses))
    ax.grid(alpha=0.25); ax.set_ylabel(T['g_tray_yl'])
    ax.legend(fontsize=8.5, loc='upper right', ncol=2)
    ax.set_title(T['g_tray_tit'], fontsize=12, fontweight='bold', loc='left')
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()


def _suave(a, sigma=2.0, zoom=3):
    """Suavizado PARA LECTURA del mapa (NaN-aware + sobremuestreo bilineal).
    Los numeros de la tabla salen de la serie por lote, no de este raster."""
    from scipy.ndimage import gaussian_filter, zoom as _zm
    fin = np.isfinite(a)
    num = gaussian_filter(np.where(fin, a, 0.0), sigma, mode='nearest')
    den = gaussian_filter(fin.astype('float64'), sigma, mode='nearest')
    sm = np.where(den > 0.35, num / np.maximum(den, 1e-9), np.nan)
    big = _zm(np.where(np.isfinite(sm), sm, 0.0), zoom, order=1)
    wbig = _zm(np.isfinite(sm).astype('float64'), zoom, order=1)
    return np.where(wbig > 0.5, big, np.nan)


def _anillos(ring):
    """Lista de anillos [(x,y)...] tolerante a Polygon/MultiPolygon."""
    if isinstance(ring[0][0], (int, float)):
        return [ring]
    if isinstance(ring[0][0][0], (int, float)):
        return ring
    return [rr for parte in ring for rr in _anillos(parte)]


def mapas(lotes_ord, fecha, out, T, key='raster', cmap=None, vmin=0.3, vmax=VMAX,
          cticks=(0.5, 1.6, 3.2, 5.0), clabels=None, suptit=None, ref_marca=None,
          idioma='es'):
    """Mapa cartografico por lote: fondo satelital real + indice suavizado recortado
    al lote + escala + norte + chip de estado. Aspecto corregido por latitud.
    Por defecto renderiza CIre (key='raster'); con key/cmap/cticks se reusa para el
    eje de AGUA (NDMI). ref_marca=(valor, texto) marca el nivel de la referencia
    seca sobre la barra de color."""
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    from matplotlib_scalebar.scalebar import ScaleBar
    import matplotlib.patheffects as pe
    cmap = cmap or CMAP
    clabels = clabels or T['g_cinta_labels']
    n = len(lotes_ord); cols = 2; rows = (n + 1) // 2
    fig, axs = plt.subplots(rows, cols, figsize=(11.5, 5.1 * rows), facecolor='white')
    axs = np.atleast_1d(axs).ravel()
    im = None
    for ax, r in zip(axs, lotes_ord):
        rgba, extf = r['rgb']
        lat = (extf[2] + extf[3]) / 2
        ax.imshow(rgba, extent=extf, origin='upper', zorder=0)
        a, ext = r[key]
        im = ax.imshow(np.ma.masked_invalid(_suave(a)), extent=ext, origin='upper',
                       cmap=cmap, vmin=vmin, vmax=vmax, interpolation='bilinear',
                       zorder=2, alpha=0.94)
        anillos = _anillos(r['ring'])
        # recorte exacto del indice al poligono del lote
        recorte = Path.make_compound_path(*[Path(np.asarray(rr)) for rr in anillos])
        im.set_clip_path(PathPatch(recorte, transform=ax.transData))
        for rr in anillos:
            xy = np.asarray(rr)
            ax.plot(xy[:, 0], xy[:, 1], color='white', lw=2.2, zorder=4)
            ax.plot(xy[:, 0], xy[:, 1], color='#1a1a1a', lw=0.9, zorder=5)
        # sectores declarados: limite punteado + rotulo
        for bq in r.get('bloques', []):
            for rr in _anillos(bq['ring']):
                xy = np.asarray(rr)
                ax.plot(xy[:, 0], xy[:, 1], color='white', lw=1.3, ls=(0, (4, 3)), zorder=5)
            from shapely.geometry import Polygon as ShPoly
            try:
                polys = [ShPoly(rr) for rr in _anillos(bq['ring'])]
                mayor = max(polys, key=lambda p: p.area)      # el anillo grande, no un fragmento
                pt = mayor.representative_point(); px, py = pt.x, pt.y
            except Exception:
                xs = [p[0] for rr in _anillos(bq['ring']) for p in rr]
                ys = [p[1] for rr in _anillos(bq['ring']) for p in rr]
                px, py = float(np.mean(xs)), float(np.mean(ys))
            nom_bq = traducir_estado(bq['nombre'].split(' (')[0], idioma)
            ax.annotate('%s · %.0f %%' % (nom_bq, bq['prog']),
                        (px, py), ha='center', va='center',
                        fontsize=9, fontweight='bold', color='white', zorder=7,
                        path_effects=[pe.withStroke(linewidth=2.8, foreground='#000000A0')])
        xs_all = [p[0] for rr in anillos for p in rr]; ys_all = [p[1] for rr in anillos for p in rr]
        mx = 260 / (111320 * np.cos(np.radians(lat))); my = 260 / 110540
        ax.set_xlim(max(extf[0], min(xs_all) - mx), min(extf[1], max(xs_all) + mx))
        ax.set_ylim(max(extf[2], min(ys_all) - my), min(extf[3], max(ys_all) + my))
        ax.set_aspect(1.0 / np.cos(np.radians(lat)))
        ax.set_facecolor('#E8EDEA')
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_edgecolor('#DDE3E1'); sp.set_linewidth(1.0)
        # titulo-banda del panel
        mezclado = bool(r.get('bloques')) and not r.get('colapsado')
        av_txt = ('%.0f-%.0f %%' % tuple(r['prog_rango'])) if mezclado else ('%.0f %%' % r['prog'])
        ax.set_title(' %s  ·  %.0f ha  ·  %s %s ' % (r['id'], r['area'], T['g_avance'], av_txt),
                     fontsize=11, fontweight='bold', color='white', loc='left',
                     bbox=dict(boxstyle='square,pad=0.42', fc=TEAL, ec='none'), pad=7)
        # escala y norte
        ax.add_artist(ScaleBar(111320 * np.cos(np.radians(lat)), units='m',
                               location='lower left', box_alpha=0.85, length_fraction=0.22,
                               font_properties={'size': 8}))
        ax.plot([0.955], [0.945], marker='^', markersize=11, color='white',
                markeredgecolor='#333333', markeredgewidth=0.8,
                transform=ax.transAxes, zorder=8, clip_on=False)
        ax.text(0.955, 0.90, 'N', transform=ax.transAxes, ha='center', va='top',
                fontsize=10.5, fontweight='bold', color='white', zorder=8,
                path_effects=[pe.withStroke(linewidth=2.4, foreground='#00000090')])
    for ax in axs[n:]:
        ax.axis('off')
    fig.subplots_adjust(left=0.03, right=0.97, top=0.93, bottom=0.10, wspace=0.06, hspace=0.16)
    cax = fig.add_axes([0.25, 0.050, 0.50, 0.022])
    cb = fig.colorbar(im, cax=cax, orientation='horizontal')
    cb.set_ticks(list(cticks))
    cb.set_ticklabels(list(clabels))
    cb.ax.tick_params(labelsize=9.5, length=0)
    cb.outline.set_edgecolor('#DDE3E1')
    if ref_marca:
        val, txt = ref_marca
        cb.ax.axvline(val, color='#1a1a1a', lw=1.6)
        cb.ax.annotate(txt, (val, 1.15), xycoords=('data', 'axes fraction'),
                       ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    fig.suptitle(suptit, fontsize=12.5, fontweight='bold', color='#0D9488', y=0.975)
    plt.savefig(out, dpi=170, bbox_inches='tight', facecolor='white'); plt.close()


# ---------- persistencia MEDICION <-> RENDER ----------
_CLAVES_UNIDAD = ('id', 'area', 'fecha', 'cire', 'cire_corr', 'pico', 'psri', 'ndmi',
                  'ndvi', 'b11', 'prog', 'rk', 'estado', 'ventana', 'inicio', 'serie',
                  'serie_agua')


def _np2py(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"no serializable: {type(o)}")


def _pack_unidad(u):
    d = {k: u.get(k) for k in _CLAVES_UNIDAD}
    return d


def empaquetar(hkey, fecha, cfg, orden, ref, excluidas, b, propio, n_pares):
    lotes_out = []
    for r in orden:
        d = _pack_unidad(r)
        d.update(ring=r['ring'], desparejo=bool(r['desparejo']),
                 dispersion=r['dispersion'], colapsado=bool(r['colapsado']),
                 prog_rango=list(r['prog_rango']) if 'prog_rango' in r else None,
                 prog_orden=r['prog_orden'],
                 bloques=[dict(_pack_unidad(bq), ring=bq['ring'], nombre=bq['nombre'])
                          for bq in r['bloques']])
        lotes_out.append(d)
    return dict(hkey=hkey, fecha=fecha, nombre=cfg['nombre'],
                referencia_declarada=bool(cfg.get('referencia_seca')),
                ref=ref, excluidas=excluidas,
                factor=dict(b=b, propio=bool(propio), pares=n_pares),
                lotes=lotes_out)


def guardar_resultados(res, rasters):
    jpath = f"{SALIDA}/resultados_{res['hkey']}_{res['fecha']}.json"
    npath = f"{SALIDA}/rasteres_{res['hkey']}_{res['fecha']}.npz"
    res['npz'] = npath
    arrs = {}
    for lid, d in rasters.items():
        for k in ('cire', 'ndmi', 'rgb'):
            a, ext = d[k]
            arrs[f"{lid}|{k}"] = a
            arrs[f"{lid}|{k}_ext"] = np.asarray(ext, float)
    np.savez_compressed(npath, **arrs)
    with open(jpath, 'w', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=1, default=_np2py)
    print("resultados ->", jpath)
    print("rasteres   ->", npath)
    return jpath


def cargar_resultados(jpath):
    res = json.load(open(jpath, encoding='utf-8'))
    z = np.load(res['npz'])
    rasters = {}
    for r in res['lotes']:
        lid = r['id']
        rasters[lid] = {k: (z[f"{lid}|{k}"], list(z[f"{lid}|{k}_ext"])) for k in ('cire', 'ndmi', 'rgb')}
    return res, rasters


def _filas_gantt(res, idioma):
    """Unidades del gantt/trayectorias = las mismas filas que la tabla: lote entero,
    o sus sectores si esta DESPAREJO (el numero accionable vive en las sub-filas)."""
    filas, unis = [], []
    for r in res['lotes']:
        mezclado = bool(r['bloques']) and not r['colapsado']
        if mezclado:
            for bq in sorted(r['bloques'], key=lambda x: -x['prog']):
                nom = f"{r['id']} · {traducir_estado(bq['nombre'].split(' (')[0], idioma)}"
                filas.append(dict(id=nom, area=bq['area'], ventana=bq.get('ventana')))
                unis.append(dict(id=nom, serie=bq['serie'],
                                 serie_agua=bq.get('serie_agua'), ventana=bq.get('ventana')))
        else:
            filas.append(dict(id=r['id'], area=r['area'], ventana=r.get('ventana')))
            unis.append(dict(id=r['id'], serie=r['serie'],
                             serie_agua=r.get('serie_agua'), ventana=r.get('ventana')))
    return filas, unis


def render_graficos(res, rasters, idioma):
    """Genera los 4-5 PNGs del entregable en el idioma pedido (sufijo _pt).
    Todo sale del JSON + npz: sin GEE."""
    T = TXT[idioma]
    hkey, fecha = res['hkey'], res['fecha']
    suf = '' if idioma == 'es' else '_pt'
    dmy = f"{_dm(fecha, T['meses'])}-{fecha[:4]}"
    lotes = []
    for r in res['lotes']:
        d = dict(r)
        d['raster'] = rasters[r['id']]['cire']
        d['raster_ndmi'] = rasters[r['id']]['ndmi']
        d['rgb'] = rasters[r['id']]['rgb']
        lotes.append(d)
    pngs = dict(
        cinta=f"{MED}/cinta_orden_cosecha_{hkey}{suf}.png",
        mapas=f"{MED}/mapas_madurez_{hkey}{suf}.png",
        ndmi=f"{MED}/mapas_agua_{hkey}{suf}.png",
        gantt=f"{MED}/ventanas_secado_{hkey}{suf}.png",
        tray=f"{MED}/trayectoria_agua_{hkey}{suf}.png")
    cinta(lotes, fecha, pngs['cinta'], T)
    ref = res['ref']
    mapas(lotes, fecha, pngs['mapas'], T, suptit=T['g_mapa_tit'] % dmy, idioma=idioma)
    mapas(lotes, fecha, pngs['ndmi'], T, key='raster_ndmi', cmap=plt.get_cmap('BrBG'),
          vmin=0.0, vmax=0.5, cticks=(0.04, 0.18, 0.32, 0.46),
          clabels=T['g_agua_labels'], suptit=T['g_agua_tit'] % dmy,
          ref_marca=(ref['ndmi_p90'], T['g_ref_marca']) if ref else None, idioma=idioma)
    if ref:
        filas_g, unis_t = _filas_gantt(res, idioma)
        gantt_ventanas(filas_g, fecha, pngs['gantt'], T)
        trayectorias_ndmi(unis_t, ref['ndmi_p90'], fecha, pngs['tray'], T)
        # mapa de PROXIMIDAD en 5 zonas con hectareas (necesita la referencia:
        # el nivel 'trillable' es su p90). Mismo JSON+npz, sin GEE.
        from zonas_proximidad import render as _zonas_render
        pngs['zonas'] = f"{MED}/zonas_proximidad_{hkey}{suf}.png"
        z_arrays = {}
        for lid, d in rasters.items():
            for k in ('ndmi', 'rgb'):
                z_arrays[f'{lid}|{k}'], z_arrays[f'{lid}|{k}_ext'] = d[k]
        _zonas_render(res, z_arrays, pngs['zonas'], idioma)
    return pngs


# ---------- render del PDF ----------
def _img_ajustada(path, width=15 * cm, max_h=18.5 * cm):
    """Image con la RELACION DE ASPECTO REAL del PNG (la altura fija de v4
    achataba los mapas) y tope de alto para no desbordar la pagina."""
    from PIL import Image as _PIL
    w, h = _PIL.open(path).size
    ih = width * h / w
    if ih > max_h:
        width = width * max_h / ih
        ih = max_h
    return Image(path, width=width, height=ih)


def _chip_color(estado, rk, mezclado=False):
    if mezclado:
        return '#8A8A8A'
    if estado.startswith('Sec'):        # 'Seco como la referencia' / 'Seca como a referência'
        return '#8B5A2B'
    return COL_RK.get(rk, '#8A8A8A')


def render_pdf(res, idioma, pngs=None):
    """Arma el PDF de marca desde el dict de resultados (sin GEE)."""
    T = TXT[idioma]
    meses = T['meses']; dm = lambda iso: _dm(iso, meses)
    hkey, fecha, yr = res['hkey'], res['fecha'], res['fecha'][:4]
    dmy = f"{dm(fecha)}-{yr}"
    suf = '' if idioma == 'es' else '_pt'
    if pngs is None:
        pngs = dict(cinta=f"{MED}/cinta_orden_cosecha_{hkey}{suf}.png",
                    mapas=f"{MED}/mapas_madurez_{hkey}{suf}.png",
                    ndmi=f"{MED}/mapas_agua_{hkey}{suf}.png",
                    gantt=f"{MED}/ventanas_secado_{hkey}{suf}.png",
                    tray=f"{MED}/trayectoria_agua_{hkey}{suf}.png")
    lotes = res['lotes']; ref = res['ref']; excluidas = res['excluidas']
    nombre = _nombre_display(res['nombre'], idioma)
    nombre_corto = nombre.replace('Trigo ', '', 1)
    B = Brand(logo=f"{SKILL}/assets/logo_pix_azulnegro_trim.png",
              footer_center=T['footer'] % yr)
    _co = lambda x: f"{x:.2f}".replace('.', ',')      # coma decimal en todo el documento
    _co1 = lambda x: f"{x:.1f}".replace('.', ',')
    tot = round(sum(r['area'] for r in lotes), 1)
    agot = sum(1 for r in lotes if r['rk'] == 3)
    prim = lotes[0]['id']
    nfig = [0]

    def figcap(txt):
        nfig[0] += 1
        return B.P(f"<b><font color='{TEAL}'>{T['figura']} {nfig[0]}.</font></b>  {txt}", "Note")

    def estado_display(u, corto=True):
        est = traducir_estado(u, idioma)
        if corto:
            a, b_ = _EST_CORTO[idioma]
            est = est.replace(a, b_)
        return est

    st = []
    # ---- pagina 1: ficha + situacion + leyenda ----
    st += B.cover_filler()
    st += [B.P(T['ficha'], "H1"), B.hr()]
    st += [B.meta_table([
        (T['cliente'], nombre),
        (T['lotes_k'], f"{len(lotes)}  ·  {_co1(tot)} ha"),
        (T['analisis_k'], T['analisis_v'] % dmy),
        (T['producto_k'], T['producto_v']),
        (T['contacto_k'], CONTACTO)])]
    st += [B.callout(T['situacion'], T['situacion_txt'] % (agot, prim))]
    st += [B.P(T['comoleer'], "H2")]
    ley = [[B.P(f"<b>{T['ley_col'][0]}</b>", "Cell"), B.P(f"<b>{T['ley_col'][1]}</b>", "Cell")]]
    for color, nom, desc in T['leyenda']:
        ley.append([B.P(f"<font color='{color}' size='11'>&bull;</font>  {nom}", "Cell"),
                    B.P(desc, "Cell")])
    tl = B.tbl(ley, [5.4 * cm, 9.6 * cm], header=False)
    tl.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), HexColor("#EAF6F4"))]))
    st += [tl]
    st += [B.P(T['ley_simbolos'], "Note")]
    st += [PageBreak()]

    # ---- resumen + cinta ----
    st += [B.P(T['resumen'], "H1"), B.hr()]
    st += [B.kpi_strip([(f"{len(lotes)}", T['kpi'][0]), (f"{tot:.0f}", T['kpi'][1]),
                        (f"{agot}", T['kpi'][2]), (prim, T['kpi'][3])])]
    st += [KeepTogether([_img_ajustada(pngs['cinta']), figcap(T['cinta_cap'])])]

    # ---- seccion 1: tabla de decision ----
    st += [B.sec(1, T['sec1'] % dmy)]

    def _vent(u):
        v = u.get('ventana')
        if not v:
            return "-"
        if v.get('alcanzado'):
            return T['alcanzado']
        if v['ic']:
            return f"{dm(v['ic'][0])}..{dm(v['ic'][1])}"
        return "-"      # sin intervalo no se publica fecha (auditoria 21-ago)

    tab = [[B.P(c, "CellB") for c in T['cols']]]
    estilos_extra = []
    for k, r in enumerate(lotes, 1):
        mezclado = bool(r['bloques']) and not r['colapsado']
        # REGLA (consulta a dos agentes, 2026-08-19): un lote con bandera NO lleva
        # promedio — un rango o nada. El numero accionable vive en las sub-filas.
        av = (f"{r['prog_rango'][0]:.0f}-{r['prog_rango'][1]:.0f}%" if mezclado
              else f"{r['prog']:.0f}%")
        if mezclado:
            est_txt = T['desparejo_fila']
        else:
            est_txt = estado_display(r['estado'])
        chip = _chip_color(est_txt, r['rk'], mezclado)
        est_p = B.P(f"<font color='{chip}' size='11'>&bull;</font> {est_txt}", "Cell")
        # 'ver sectores' y no '-': el '-' queda reservado para 'no ajustable /
        # no se extrapola' — dos significados nunca viajan con el mismo simbolo
        tab.append([str(k), r['id'], f"{r['area']:.0f} ha", est_p, av,
                    _co(r['ndmi']), T['ver_sectores'] if mezclado else _vent(r)])
        if mezclado:
            for bq in sorted(r['bloques'], key=lambda x: -x['prog']):
                est_b = estado_display(bq['estado'])
                chip_b = _chip_color(est_b, bq['rk'])
                tab.append(["", "   - " + traducir_estado(bq['nombre'], idioma),
                            f"{bq['area']:.0f} ha",
                            B.P(f"<font color='{chip_b}' size='11'>&bull;</font> {est_b}", "Cell"),
                            f"{bq['prog']:.0f}%", _co(bq['ndmi']), _vent(bq)])
        elif r['colapsado']:
            tab.append(["", T['convergieron'], "", "", "", "", ""])
    t = B.tbl(tab, [0.6 * cm, 3.4 * cm, 1.2 * cm, 4.2 * cm, 1.7 * cm, 1.25 * cm, 3.45 * cm],
              aligns={0: 'CENTER', 2: 'RIGHT', 4: 'CENTER', 5: 'CENTER', 6: 'CENTER'})
    # columna de DECISION destacada: fondo lima palido + negrita (pintada despues de
    # ROWBACKGROUNDS, asi gana en todas las filas)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), GRIS),
        ("BACKGROUND", (6, 1), (6, -1), LIMA_PALE),
        ("FONTNAME", (6, 1), (6, -1), "Helvetica-Bold"),
        ("LINEBEFORE", (6, 0), (6, -1), 1.2, HexColor("#7FD633")),
    ]))
    st += [t]

    # ---- notas de salvaguarda (auditadas: sobreviven identicas en ambos idiomas) ----
    if any(r['bloques'] for r in lotes):
        st += [B.P(T['nota_sectores'], "Note")]
    if ref:
        st += [B.P(T['nota_ref'] % (_co(ref['cire_p90']),
                                    f"{ref['ndmi_p90']:.3f}".replace('.', ',')), "Note")]
        st += [B.P(T['nota_ventana'], "Note")]
        st += [B.P(T['nota_control'], "Note")]
        # linea B11 intra-escena, calculada EN ESTA corrida: sostiene 'aun humedo'
        b11s = [u['b11'] for r0 in lotes for u in ([r0] + r0['bloques']) if u.get('b11') is not None]
        if b11s and ref.get('b11_p50') is not None:
            dmin = ref['b11_p50'] - max(b11s); dmax = ref['b11_p50'] - min(b11s)
            if dmin > 0:
                st += [B.P(T['nota_b11'] % (_co(dmin), _co(dmax)), "Note")]
    elif res.get('referencia_declarada'):
        # 'no pude mirar' nunca viaja como 'sin novedad': la columna queda en '-'
        # y esta nota dice POR QUE (referencia nublada/brumosa en toda la ventana)
        st += [B.P(T['nota_no_eval'], "Note")]
    if excluidas:
        vistos = sorted({(e['fecha'], e['lote']) for e in excluidas})
        st += [B.P(T['nota_bruma'] + " · ".join(f"{dm(f)} ({l})" for f, l in vistos), "Note")]

    # ---- seccion 2: ventana de secado ----
    if ref:
        st += [B.sec(2, T['sec2'])]
        st += [KeepTogether([_img_ajustada(pngs['gantt']), figcap(T['gantt_cap'])])]
        st += [KeepTogether([_img_ajustada(pngs['tray']), figcap(T['tray_cap'])])]
    sec_m = 3 if ref else 2

    # ---- seccion 3: mapas ----
    st += [B.sec(sec_m, T['sec3'])]
    st += [KeepTogether([_img_ajustada(pngs['mapas'], max_h=17.5 * cm), figcap(T['mapa_cire_cap'])])]
    st += [KeepTogether([_img_ajustada(pngs['ndmi'], max_h=17.5 * cm), figcap(T['mapa_ndmi_cap'])])]
    if pngs.get('zonas'):
        st += [KeepTogether([_img_ajustada(pngs['zonas'], max_h=17.5 * cm),
                             figcap(T['mapa_zonas_cap'])])]

    # ---- seccion final: metodo + proximo paso (fluye: sin pagina semivacia) ----
    st += [KeepTogether([B.sec(sec_m + 1, T['sec4']),
                         B.P(T['metodo'], "Body"),
                         B.callout(T['prox'], T['prox_txt'] % prim)])]

    sufpdf = '' if idioma == 'es' else '_PT'
    out_pdf = f"{SALIDA}/Entregable_Orden_Madurez_{hkey}_{fecha}{sufpdf}.pdf"
    B.build(out_pdf, st, cover_title=T['cover_title'],
            cover_subtitle=T['cover_sub'] % (nombre_corto, dmy))
    print("PDF ->", out_pdf)
    return out_pdf


# ---------- main ----------
def run(hkey, fecha):
    _ee_init()
    cfg = HACIENDAS[hkey]
    yr = fecha[:4]
    lotes = cargar_lotes(cfg['fuentes'])
    fin = (datetime.date.fromisoformat(fecha) + datetime.timedelta(3)).isoformat()

    # 1) series con compuerta de bruma (lotes y, si estan declarados, bloques)
    bloques_cfg = cfg.get('bloques') or {}
    excluidas_todas = []
    for r in lotes:
        serie = trayectoria(r['geom'], f"{yr}-04-15", fin)
        r['serie_cruda'] = serie
        r['serie'], excl = mz.filtrar_bruma(serie)
        excluidas_todas += [dict(lote=r['id'], **e) for e in excl]
        # Landsat 8/9: refuerza SOLO el eje de agua (offset medido, madurez.fusionar_agua)
        sl = trayectoria_landsat(r['geom'], f"{yr}-04-15", fin)
        r['serie_agua'] = mz.fusionar_agua(
            [(p['fecha'], p['NDMI']) for p in r['serie']],
            [(p['fecha'], p['NDMI'], p['sat']) for p in sl])
        print('%s: %d escenas S2 + %d Landsat en el eje de agua' % (r['id'], len(r['serie']), len(sl)))
        r['area'] = round(r['geom'].area(1).getInfo() / 1e4, 1)
        r['bloques'] = []
        if r['id'] in bloques_cfg and os.path.exists(bloques_cfg[r['id']]):
            for ft in json.load(open(bloques_cfg[r['id']], encoding='utf-8'))['features']:
                gb = ft['geometry']
                geob = ee.Geometry(dict(type=gb['type'], coordinates=_f2d(gb['coordinates'])))
                sb = trayectoria(geob, f"{yr}-04-15", fin)
                sbl, exb = mz.filtrar_bruma(sb)
                excluidas_todas += [dict(lote=ft['properties']['bloque_id'], **e) for e in exb]
                slb = trayectoria_landsat(geob, f"{yr}-04-15", fin)
                r['bloques'].append(dict(id=ft['properties']['bloque_id'],
                                         nombre=ft['properties'].get('nombre', ft['properties']['bloque_id']),
                                         ring=_f2d(gb['coordinates']),
                                         serie=sbl,
                                         serie_agua=mz.fusionar_agua(
                                             [(p['fecha'], p['NDMI']) for p in sbl],
                                             [(p['fecha'], p['NDMI'], p['sat']) for p in slb]),
                                         area=round(geob.area(1).getInfo() / 1e4, 1)))

    # 2) factor S2C por nivel, ajustado con TODOS los lotes y bloques de la corrida
    pares = []
    for r in lotes:
        pares += mz.pares_s2c(r['serie'])
        for bq in r['bloques']:
            pares += mz.pares_s2c(bq['serie'])
    b, propio = mz.ajustar_b(pares)
    print('factor S2C: r(c)=1%+.4f*c  (%d pares%s)' % (b, len(pares), '' if propio else ', DEFECTO medido SA/SF'))

    # 3) referencia seca (opcional)
    ref = None
    if cfg.get('referencia_seca') and os.path.exists(cfg['referencia_seca']):
        gref = json.load(open(cfg['referencia_seca'], encoding='utf-8'))['features'][0]['geometry']
        ref = cortes_referencia(ee.Geometry(dict(type=gref['type'], coordinates=_f2d(gref['coordinates']))), fecha)
        if ref:
            print('referencia seca: CIre p90 %.2f · NDMI p90 %.3f' % (ref['cire_p90'], ref['ndmi_p90']))

    # 4) estado por unidad (lote o bloque): PICO PROPIO siempre
    def evaluar(u):
        for p in u['serie']:
            p['cire_corr'] = round(mz.corregir_cire(p['CIre'], p['sat'], b), 3)
        ab = [p for p in u['serie'] if p['sat'] in ('A', 'B')]
        pico = max(ab or u['serie'], key=lambda p: p['cire_corr'])
        cur = u['serie'][-1]
        u['pico'] = pico['cire_corr']; u['fecha'] = cur['fecha']
        u['cire'] = cur['CIre']; u['cire_corr'] = cur['cire_corr']
        u['psri'] = cur['PSRI']; u['ndmi'] = cur['NDMI']; u['ndvi'] = cur['NDVI']
        u['b11'] = cur.get('B11')
        u['prog'] = round(100 * (1 - cur['cire_corr'] / u['pico']), 0)
        u['estado'], u['rk'] = mz.estado(u['prog'], u['psri'])
        u['ventana'] = None
        if ref:
            fino = mz.estado_final(cur['cire_corr'], cur['NDMI'], ref['cire_p90'], ref['ndmi_p90'])
            if fino:
                u['estado'] = fino
            # VENTANA ESTIMADA "seco como la referencia": ajuste logistico del NDMI
            # post-pico con piso anclado en la referencia seca (madurez.ajuste_cruce;
            # validado 21-ago: el ajuste <=19-ago predijo el 21-ago con error
            # +0,002..+0,021). None = 'no ajustable' o cruce a >30 d: no se publica.
            # NIVEL = ndmi_p90 de la referencia — EL MISMO umbral que estado_final
            # (auditoria 21-ago: dos umbrales de 'seco' en el mismo PDF no se pueden
            # reconciliar; el +0,03 anterior no estaba rastreado a ninguna medicion).
            # sigma_min = repetibilidad escena-a-escena MEDIDA del NDMI: sin ese piso
            # el intervalo cubre ~60-79 % y fue RECHAZADO por el validador (21-ago).
            # la serie de agua fusiona S2 + Landsat 8/9 (offset medido +0,02 ya
            # restado en fusionar_agua); si no hay fusion, cae a la serie S2 sola
            agua = u.get('serie_agua') or [dict(fecha=p['fecha'], NDMI=p['NDMI'])
                                           for p in u['serie']]
            u['ventana'] = mz.ajuste_cruce(
                [(p['fecha'], p['NDMI']) for p in agua],
                piso=ref['ndmi_p50'], nivel=ref['ndmi_p90'],
                sigma_min=mz.SIGMA_NDMI_ESCENA)
        u['inicio'] = mz.inicio_cobertura([(p['fecha'], p['cire_corr']) for p in u['serie']])

    rasters = {}
    for r in lotes:
        evaluar(r)
        for bq in r['bloques']:
            evaluar(bq)
        # colapso de DISPLAY: si los bloques convergieron se reporta una sola fila
        # (la geometria del catalogo no se toca: la fecha de siembra es un hecho).
        r['colapsado'] = mz.colapsar_bloques([bq['prog'] for bq in r['bloques']]) if r['bloques'] else False
        ras_cire = raster_cire(r['geom'], fecha)
        ras_ndmi = raster_indice(r['geom'], fecha, 'NDMI')
        ras_rgb = raster_rgb(r['geom'], fecha)
        rasters[r['id']] = dict(cire=ras_cire, ndmi=ras_ndmi, rgb=ras_rgb)
        # bandera universal de lote DESPAREJO (log CIre p90-p10 de la escena; umbral
        # medido contra los lotes uniformes de la flota SA/SF). LIMITE declarado: es
        # una bandera DE UNA ESCENA; cuando las trayectorias se cruzan (caso 01-ago)
        # no ve la mezcla — la particion declarada si.
        # el umbral de desparejo se calibro sobre INTERIOR (sin borde): erosionar
        # 2 px de 10 m (= 20 m) antes de medir, o el borde dispara la bandera solo.
        from scipy.ndimage import binary_erosion as _be
        _a = ras_cire[0]
        _fin = _be(np.isfinite(_a), np.ones((5, 5)))
        r['desparejo'], r['dispersion'] = mz.desparejo(_a[_fin])
        mezclado = bool(r['bloques']) and not r['colapsado']
        if mezclado:
            pr = [bq['prog'] for bq in r['bloques']]
            r['prog_rango'] = (min(pr), max(pr))
            r['prog_orden'] = max(pr)          # la prioridad la fija el bloque mas avanzado
            r['estado'] = 'DESPAREJO - %d plantios, ver sectores' % len(r['bloques'])
        elif r['desparejo']:
            r['prog_orden'] = r['prog']
            r['estado'] = r['estado'] + ' | desparejo, ver mapa'
        else:
            r['prog_orden'] = r['prog']
        def _vtxt(u):
            v = u.get('ventana')
            if not v:
                return '-'
            if v.get('alcanzado'):
                return 'alcanzado'
            return f"{v['ic'][0]}..{v['ic'][1]}" if v['ic'] else '-'
        print(f"{r['id']:6s} {r['area']:6.1f}ha  CIre={r['cire']:.2f} (corr {r['cire_corr']:.2f}) "
              f"NDMI={r['ndmi']:.3f} avance={r['prog']:.0f}%  disp={r['dispersion']}  "
              f"seco_est={_vtxt(r)}  {r['estado']}")
        for bq in r['bloques']:
            print(f"   sub {bq['id']:10s} {bq['area']:5.1f}ha  CIre={bq['cire']:.2f} (corr {bq['cire_corr']:.2f}) "
                  f"NDMI={bq['ndmi']:.3f} pico={bq['pico']:.1f} avance={bq['prog']:.0f}%  "
                  f"seco_est={_vtxt(bq)}  {bq['estado']}")
    orden = sorted(lotes, key=lambda r: -r['prog_orden'])

    # 5) MEDICION lista: persistir y renderizar (es + pt) desde el mismo JSON
    res = empaquetar(hkey, fecha, cfg, orden, ref, excluidas_todas, b, propio, len(pares))
    # JSON round-trip antes de renderizar: el render de ESTA corrida usa exactamente
    # lo mismo que veria un --render posterior (ninguna divergencia silenciosa).
    jpath = guardar_resultados(res, rasters)
    res, rasters = cargar_resultados(jpath)
    salidas = []
    for idioma in ('es', 'pt'):
        pngs = render_graficos(res, rasters, idioma)
        salidas.append(render_pdf(res, idioma, pngs))
    return salidas


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--render':
        # re-render sin GEE: python orden_cosecha.py --render salida/resultados_X.json [es|pt]
        jpath = sys.argv[2]
        idiomas = [sys.argv[3]] if len(sys.argv) > 3 else ['es', 'pt']
        res, rasters = cargar_resultados(jpath)
        for idioma in idiomas:
            if idioma not in TXT:
                sys.exit(f"Idioma '{idioma}' no soportado. Opciones: {list(TXT)}")
            pngs = render_graficos(res, rasters, idioma)
            render_pdf(res, idioma, pngs)
        sys.exit(0)
    hkey = sys.argv[1] if len(sys.argv) > 1 else 'SA_SF'
    fecha = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat()
    if hkey not in HACIENDAS:
        sys.exit(f"Hacienda '{hkey}' no esta en HACIENDAS. Opciones: {list(HACIENDAS)}")
    run(hkey, fecha)
