# -*- coding: utf-8 -*-
"""Mapas de foco con IMAGEN SATELITAL REAL de fondo.

POR QUE EXISTE
--------------
El informe dibujaba el lote como un contorno gris vectorial con los focos rellenos
al lado. Tecnicamente correcto y visualmente inservible: el tecnico no tiene NINGUNA
referencia del terreno para ubicarse. No ve donde esta la entrada, ni el camino, ni
la cabecera, ni la mancha de suelo que explica el foco. Un poligono flotando en
blanco no le dice a donde caminar.

Lo que se necesita es lo que hace cualquier producto serio del rubro: la foto real
del lote, en color natural, de la MISMA fecha que disparo la alerta, con el foco
marcado encima de forma que se lea sobre cualquier fondo.

DECISIONES DE DISENO Y POR QUE
-------------------------------
· **Color natural (B4,B3,B2), no falso color.** El tecnico reconoce el terreno: el
  camino es camino, el monte es monte. En falso color tiene que traducir.
· **La imagen es de la MISMA escena que disparo el foco**, no un mosaico reciente
  ni una base de Esri. Si el mapa mostrara otra fecha, el tecnico veria un campo que
  no es el que se analizo — y con un cultivo que cambia cada semana, eso es mentir.
· **Foco en contorno grueso + halo oscuro, sin relleno.** El relleno tapa justo lo
  que hay que ver. El halo hace que el contorno se lea igual sobre suelo claro que
  sobre dosel oscuro; un color solo siempre desaparece sobre algun fondo.
· **Dos escalas.** Un mapa de contexto con TODO el lote y donde caen los focos, y
  un acercamiento por foco. Con un solo mapa del lote entero, un foco de 0,28 ha en
  120 ha es un punto invisible.
· **Coordenadas del centro de cada foco**, en grados decimales. Es lo que se teclea
  en el GPS del celular si el GeoJSON no abre.

LIMITE HONESTO: el `thumbURL` de Earth Engine devuelve como maximo 1280 px de lado.
Para un lote de 120 ha eso da ~1 m/px, mas que suficiente para ubicarse, pero NO es
una imagen de 10 m remuestreada a resolucion util: sigue siendo Sentinel-2 y el
detalle fino que se ve es interpolacion.
"""
import io
import math
import os
import urllib.request

# Bandas de color natural y el estiramiento. Los percentiles se calculan sobre la
# PROPIA escena recortada al lote: un estiramiento fijo deja las escenas de invierno
# lavadas y las de verano quemadas, y el tecnico ve dos campos distintos cada mes.
RGB = ['B4', 'B3', 'B2']
P_BAJO, P_ALTO = 2, 98
MAX_PX = 1280             # tope de getThumbURL
TIMEOUT = 60


def _estiramiento(img, geom, escala=10):
    """Percentiles de la escena recortada al lote, por banda."""
    import ee
    st = img.select(RGB).reduceRegion(
        reducer=ee.Reducer.percentile([P_BAJO, P_ALTO]),
        geometry=geom, scale=escala, maxPixels=1e9, bestEffort=True).getInfo() or {}
    mins, maxs = [], []
    for b in RGB:
        lo = st.get('%s_p%d' % (b, P_BAJO))
        hi = st.get('%s_p%d' % (b, P_ALTO))
        # Si la banda vino vacia (todo enmascarado) se cae a un rango razonable de
        # reflectancia BOA en vez de romper: un mapa feo es mejor que sin mapa.
        mins.append(0.0 if lo is None else float(lo))
        maxs.append(0.30 if hi is None else max(float(hi), (lo or 0) + 1e-4))
    return mins, maxs


def _marco(geom, margen=0.12):
    """Rectangulo que encuadra la geometria con un margen, en grados.

    Devuelve (oeste, sur, este, norte). El margen da contexto: un foco pegado al
    borde del recorte no deja ver de que lado del lote esta.
    """
    import ee
    c = ee.Geometry(geom).bounds(maxError=1).coordinates().getInfo()[0]
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]
    w, e, s, n = min(xs), max(xs), min(ys), max(ys)
    dx, dy = (e - w) * margen, (n - s) * margen
    d = max(dx, dy)
    return w - d, s - d, e + d, n + d


def fondo_rgb(idx_escena, geom, margen=0.12, max_px=MAX_PX):
    """PNG en color natural de la escena `idx_escena` recortado al marco de `geom`.

    Devuelve (bytes_png, (oeste, sur, este, norte)) o (None, marco) si no se pudo.
    Nunca lanza: un mapa sin fondo se degrada al dibujo vectorial, no rompe la
    entrega.
    """
    try:
        import ee
        img = ee.Image(ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filter(ee.Filter.eq('system:index', idx_escena)).first())
        marco = _marco(geom, margen)
        # Los percentiles se calculan sobre EL RECORTE QUE SE DIBUJA, no sobre la
        # geometria original: en el mapa de detalle —300 m alrededor de un foco— un
        # estiramiento calculado sobre las 119 ha del lote dejaba el acercamiento
        # oscuro y plano, porque el rango lo fijaban pixeles que no estan a la vista.
        w0, s0, e0, n0 = marco
        region = ee.Geometry.Rectangle([w0, s0, e0, n0], None, False)
        mins, maxs = _estiramiento(img, region)
        w, s, e, n = marco
        # Proporcion real del recorte para que la imagen no salga estirada. A esta
        # latitud un grado de longitud mide menos que uno de latitud.
        lat = math.radians((s + n) / 2.0)
        ancho_m = (e - w) * math.cos(lat)
        alto_m = (n - s)
        if ancho_m >= alto_m:
            px_w = max_px
            px_h = max(1, int(round(max_px * alto_m / ancho_m)))
        else:
            px_h = max_px
            px_w = max(1, int(round(max_px * ancho_m / alto_m)))
        url = img.select(RGB).getThumbURL({
            'min': mins, 'max': maxs, 'gamma': 1.15,
            'region': [[w, s], [e, s], [e, n], [w, n]],
            'dimensions': '%dx%d' % (px_w, px_h),
            'format': 'png',
        })
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.read(), marco
    except Exception as e:                      # noqa: BLE001 — se declara y degrada
        print('  [mapa] sin fondo satelital (%s: %s)'
              % (type(e).__name__, str(e)[:90]))
        try:
            return None, _marco(geom, margen)
        except Exception:
            return None, None


# --- proyeccion simple del marco a pixeles del dibujo -------------------------

class Encuadre:
    """Convierte lon/lat -> coordenadas de dibujo dentro de un rectangulo dado.

    Es una equirectangular local con correccion de coseno de latitud: sobre un lote
    de pocos km el error es despreciable y evita meter una dependencia de proyeccion
    solo para dibujar un mapa de 8 cm.
    """

    def __init__(self, marco, ancho, alto):
        self.w, self.s, self.e, self.n = marco
        self.k = math.cos(math.radians((self.s + self.n) / 2.0))
        dx = (self.e - self.w) * self.k
        dy = (self.n - self.s)
        # Escala UNICA para los dos ejes: si se escalaran por separado, un lote
        # alargado saldria deformado y las distancias del mapa mentirian.
        self.esc = min(ancho / dx, alto / dy) if dx > 0 and dy > 0 else 1.0
        self.ancho_dib = dx * self.esc
        self.alto_dib = dy * self.esc
        self.ox = (ancho - self.ancho_dib) / 2.0
        self.oy = (alto - self.alto_dib) / 2.0

    def xy(self, lon, lat):
        return (self.ox + (lon - self.w) * self.k * self.esc,
                self.oy + (lat - self.s) * self.esc)

    def metros_por_unidad(self):
        """Cuantos metros de terreno mide una unidad de dibujo. Para la barra."""
        grados_por_unidad = 1.0 / self.esc
        return grados_por_unidad * 111320.0


def anillos(geom):
    """Lista de anillos [(lon,lat), ...] de un Polygon o MultiPolygon GeoJSON.

    Descarta la Z. Los KML/KMZ que exporta el cliente traen los vertices con altura
    (lon, lat, 0) y el dibujo espera pares; sin esto reventaba con "too many values
    to unpack" justo en los lotes que vienen del campo, que son todos.
    """
    if not geom:
        return []

    def _2d(anillo):
        return [(float(p[0]), float(p[1])) for p in anillo if len(p) >= 2]

    t = geom.get('type')
    if t == 'Polygon':
        return [_2d(a) for a in geom['coordinates']]
    if t == 'MultiPolygon':
        out = []
        for p in geom['coordinates']:
            out.extend(_2d(a) for a in p)
        return out
    return []


def centro(geom):
    """Centroide aproximado (promedio de vertices del anillo exterior)."""
    a = anillos(geom)
    if not a:
        return None
    ext = a[0]
    if not ext:
        return None
    return (sum(p[0] for p in ext) / len(ext), sum(p[1] for p in ext) / len(ext))


def encajar(marco, ancho_max, alto_max):
    """Medidas del recuadro que MEJOR aprovechan el espacio para ese marco.

    Sin esto, un lote alargado —los de trigo son angostos y largos— dibujado en un
    recuadro apaisado deja dos franjas blancas enormes a los costados y la foto
    queda del ancho de un dedo. El mapa se adapta a la forma del campo, no al reves.
    Nunca deforma: la escala sigue siendo unica para los dos ejes.
    """
    w, s, e, n = marco
    k = math.cos(math.radians((s + n) / 2.0))
    dx = max((e - w) * k, 1e-9)
    dy = max(n - s, 1e-9)
    esc = min(ancho_max / dx, alto_max / dy)
    return dx * esc, dy * esc


def marco_de(geoms, margen=0.35, minimo_m=140.0):
    """Marco que encuadra varias geometrias, con un tamaño MINIMO.

    El minimo evita el acercamiento inutil: un foco de 0,28 ha encuadrado justo
    llena la imagen de una mancha y no se ve NADA alrededor — ni el borde del lote,
    ni la cabecera, ni por donde se entra. Sin contexto el mapa no orienta.
    """
    pts = []
    for g in geoms:
        for a in anillos(g):
            pts.extend(a)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w, e, s, n = min(xs), max(xs), min(ys), max(ys)
    dx, dy = (e - w) * margen, (n - s) * margen
    d = max(dx, dy)
    w, e, s, n = w - d, e + d, s - d, n + d
    # Piso en metros
    lat = math.radians((s + n) / 2.0)
    grados_min = minimo_m / 111320.0
    if (e - w) * math.cos(lat) < grados_min:
        cx = (e + w) / 2.0
        media = grados_min / max(math.cos(lat), 1e-6) / 2.0
        w, e = cx - media, cx + media
    if (n - s) < grados_min:
        cy = (n + s) / 2.0
        s, n = cy - grados_min / 2.0, cy + grados_min / 2.0
    return w, s, e, n


# --- dibujo -------------------------------------------------------------------
# Colores del mapa. NO son los de la marca: un mapa se lee sobre la foto, y ahi lo
# unico que manda es el contraste contra verde de dosel y contra suelo claro.
FOCO_TRAZO = (1.0, 0.85, 0.10)      # amarillo: se lee sobre verde Y sobre suelo
FOCO_HALO = (0.05, 0.05, 0.05)      # halo oscuro debajo del trazo
LOTE_TRAZO = (1.0, 1.0, 1.0)        # blanco
TEXTO = (1.0, 1.0, 1.0)


def _rgb(t):
    from reportlab.lib import colors
    return colors.Color(*t)


def _recortar(pts, xmin, ymin, xmax, ymax):
    """Sutherland-Hodgman: recorta un poligono al rectangulo del mapa.

    HACE FALTA: un `Drawing` de reportlab **no recorta**. Lo que cae fuera del
    recuadro se dibuja igual, sobre el resto de la pagina. Con el mapa de detalle
    —encuadrado a 300 m alrededor de un foco— el borde del lote de 119 ha se
    dibujaba entero y cruzaba la hoja de punta a punta con lineas negras.
    """
    def dentro(p, borde):
        x, y = p
        return {0: x >= xmin, 1: x <= xmax, 2: y >= ymin, 3: y <= ymax}[borde]

    def corte(a, b, borde):
        (x1, y1), (x2, y2) = a, b
        if borde in (0, 1):
            xb = xmin if borde == 0 else xmax
            t = (xb - x1) / (x2 - x1) if x2 != x1 else 0.0
            return (xb, y1 + t * (y2 - y1))
        yb = ymin if borde == 2 else ymax
        t = (yb - y1) / (y2 - y1) if y2 != y1 else 0.0
        return (x1 + t * (x2 - x1), yb)

    salida = list(pts)
    for borde in range(4):
        if not salida:
            return []
        entrada, salida = salida, []
        ant = entrada[-1]
        for act in entrada:
            if dentro(act, borde):
                if not dentro(ant, borde):
                    salida.append(corte(ant, act, borde))
                salida.append(act)
            elif dentro(ant, borde):
                salida.append(corte(ant, act, borde))
            ant = act
    return salida


def _poli(anillo, enc, ancho=None, alto=None, **kw):
    """Poligono en coordenadas de dibujo, recortado al recuadro si se dan medidas.

    Devuelve None si queda enteramente afuera (para no agregar figuras vacias).
    """
    from reportlab.graphics.shapes import Polygon
    pts = [enc.xy(lon, lat) for lon, lat in anillo]
    if ancho is not None and alto is not None:
        # Un pelo de margen para que el trazo grueso no se corte justo en el filo.
        pts = _recortar(pts, -1, -1, ancho + 1, alto + 1)
    if len(pts) < 3:
        return None
    plano = []
    for x, y in pts:
        plano.extend([x, y])
    return Polygon(plano, **kw)


def _barra_escala(d, enc, ancho, alto, margen=6):
    """Barra de escala con un numero redondo de metros."""
    from reportlab.graphics.shapes import Rect, String
    m_por_u = enc.metros_por_unidad()
    objetivo = ancho * 0.26 * m_por_u           # ~26% del ancho del mapa
    escalones = (10, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000)
    paso = escalones[0]
    for e in escalones:                         # el MAYOR que entra en el objetivo
        if e <= objetivo:
            paso = e
    largo = paso / m_por_u
    etiqueta = '%d m' % paso if paso < 1000 else '%.1f km' % (paso / 1000.0)
    x0, y0 = margen + 2, margen + 2
    # El recuadro oscuro cubre la barra Y la etiqueta: antes solo cubria la barra y
    # el texto quedaba encima de la foto, ilegible o cortado ("0 km" por "1.0 km").
    ancho_txt = len(etiqueta) * 3.9 + 6
    d.add(Rect(x0 - 3, y0 - 2, largo + ancho_txt, 12, rx=2, ry=2,
               fillColor=_rgb((0, 0, 0)), strokeColor=None, fillOpacity=0.5))
    d.add(Rect(x0, y0 + 3.4, largo, 3.2, fillColor=_rgb(TEXTO),
               strokeColor=_rgb(FOCO_HALO), strokeWidth=0.4))
    d.add(String(x0 + largo + 5, y0 + 3.2, etiqueta,
                 fontName='Helvetica-Bold', fontSize=6.4, fillColor=_rgb(TEXTO)))


def _norte(d, ancho, alto, margen=6):
    from reportlab.graphics.shapes import Polygon, Rect, String
    x, y = ancho - margen - 9, alto - margen - 18
    d.add(Rect(x - 5, y - 3, 19, 22, fillColor=_rgb((0, 0, 0)), strokeColor=None,
               fillOpacity=0.45))
    d.add(Polygon([x + 4.5, y + 14, x + 1, y + 3, x + 4.5, y + 5.5, x + 8, y + 3],
                  fillColor=_rgb(TEXTO), strokeColor=_rgb(FOCO_HALO),
                  strokeWidth=0.4))
    d.add(String(x + 4.5, y + 15.5, 'N', fontName='Helvetica-Bold', fontSize=6.5,
                 fillColor=_rgb(TEXTO), textAnchor='middle'))


def dibujar(marco, png, geom_lote, focos, ancho, alto, etiquetas=True,
            radio_min=0.0, _cache={}):
    """Mapa: foto satelital de fondo + borde del lote + focos marcados.

    `focos` es una lista de (etiqueta, geometria GeoJSON). Devuelve un Drawing de
    reportlab listo para meter en el `story`.
    """
    from reportlab.graphics.shapes import Drawing, Image, Rect, String
    d = Drawing(ancho, alto)
    enc = Encuadre(marco, ancho, alto)

    # Fondo. El PNG se escribe a disco porque `shapes.Image` quiere una ruta; se
    # cachea por contenido para no repetir el archivo en cada foco del mismo lote.
    if png:
        import hashlib
        import tempfile
        h = hashlib.sha1(png).hexdigest()[:16]
        ruta = _cache.get(h)
        if not ruta or not os.path.exists(ruta):
            ruta = os.path.join(tempfile.gettempdir(), 'pixmapa_%s.png' % h)
            with open(ruta, 'wb') as fh:
                fh.write(png)
            _cache[h] = ruta
        d.add(Image(enc.ox, enc.oy, enc.ancho_dib, enc.alto_dib, ruta))
    else:
        d.add(Rect(0, 0, ancho, alto, fillColor=_rgb((0.93, 0.95, 0.96)),
                   strokeColor=None))

    # Borde del lote: linea blanca con halo oscuro debajo, para que se lea tanto
    # sobre dosel verde como sobre suelo claro.
    for a in anillos(geom_lote):
        for kw in ({'strokeColor': _rgb(FOCO_HALO), 'strokeWidth': 2.6},
                   {'strokeColor': _rgb(LOTE_TRAZO), 'strokeWidth': 1.1}):
            pol = _poli(a, enc, ancho, alto, fillColor=None, strokeLineJoin=1, **kw)
            if pol is not None:
                d.add(pol)

    # Focos: SIN relleno. El relleno tapa justo lo que el tecnico tiene que ver.
    for etq, g in focos:
        for a in anillos(g):
            for kw in ({'strokeColor': _rgb(FOCO_HALO), 'strokeWidth': 3.4},
                       {'strokeColor': _rgb(FOCO_TRAZO), 'strokeWidth': 1.7}):
                pol = _poli(a, enc, ancho, alto, fillColor=None,
                            strokeLineJoin=1, **kw)
                if pol is not None:
                    d.add(pol)
        c = centro(g)
        if c and radio_min:
            # ANILLO LOCALIZADOR. A escala de lote, un foco de 0,28 ha mide menos de
            # 2 mm en el papel: el contorno existe pero no se ve. El anillo dice
            # "aca hay algo" sin tapar la imagen, y desaparece solo en el mapa de
            # detalle, donde el foco ya se ve por si mismo.
            from reportlab.graphics.shapes import Circle
            x, y = enc.xy(*c)
            if 0 <= x <= ancho and 0 <= y <= alto:
                d.add(Circle(x, y, radio_min + 1.1, fillColor=None,
                             strokeColor=_rgb(FOCO_HALO), strokeWidth=2.2))
                d.add(Circle(x, y, radio_min, fillColor=None,
                             strokeColor=_rgb(FOCO_TRAZO), strokeWidth=1.3))
        if etiquetas:
            if c:
                x, y = enc.xy(*c)
                r = 7.0
                d.add(Rect(x - r, y - r * 0.62, r * 2, r * 1.24, rx=3, ry=3,
                           fillColor=_rgb(FOCO_HALO), strokeColor=_rgb(FOCO_TRAZO),
                           strokeWidth=0.9, fillOpacity=0.85))
                d.add(String(x, y - 2.6, etq, fontName='Helvetica-Bold',
                             fontSize=7.2, fillColor=_rgb(FOCO_TRAZO),
                             textAnchor='middle'))

    _barra_escala(d, enc, ancho, alto)
    _norte(d, ancho, alto)
    d.add(Rect(0, 0, ancho, alto, fillColor=None,
               strokeColor=_rgb((0.55, 0.60, 0.65)), strokeWidth=0.7))
    return d
