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

Uso:
    python orden_cosecha.py SA_SF 2026-08-01
Producto RELATIVO: ordena lotes por madurez. No da fecha de cosecha.
"""
import ee, json, sys, os, datetime, numpy as np, requests
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.dates import DateFormatter, MonthLocator, date2num
import rasterio
from rasterio.io import MemoryFile

RAIZ   = r"D:/PIXADVISOR_AGENT_WORKSPACE/PIX_ALERTA"
LOTES  = f"{RAIZ}/lotes"
MED    = f"{RAIZ}/medicion"
SALIDA = f"{RAIZ}/salida"
SKILL  = r"C:/Users/Usuario/.claude/skills/pixadvisor-propuesta-ejecutiva"
sys.path.insert(0, RAIZ)
sys.path.insert(0, f"{SKILL}/scripts")
from pix_alerta import madurez as mz
from pix_branding import Brand
from reportlab.platypus import PageBreak, Image
from reportlab.lib.units import cm

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

ee.Initialize(project='ee-gisagronomico')
CS = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
_f2d = lambda c: c[:2] if isinstance(c[0], (int, float)) else [_f2d(x) for x in c]


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


# ---------- render ----------
CMAP = plt.get_cmap('RdYlGn'); VMIN, VMAX = 0.2, 5.3
COL_RK = {0: '#1B7A1B', 1: '#7FD633', 2: '#B8860B', 3: '#CC0000'}


def cinta(lotes_ord, fecha, out):
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
    ax.xaxis_date(); ax.xaxis.set_major_locator(MonthLocator()); ax.xaxis.set_major_formatter(DateFormatter('%b'))
    ax.axvline(date2num(datetime.date.fromisoformat(fecha)), color='k', ls=':', lw=1.2)
    ax.set_title('Madurez del trigo por lote (CIre en escala S2A/B) — verde = en llenado · rojo = clorofila agotada',
                 fontsize=12, fontweight='bold')
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.035); cb.set_ticks([0.35, 1.6, 3.2, 5.0])
    cb.set_ticklabels(['Clor. agotada', 'Madurando', 'Verde', 'Pleno']); cb.ax.tick_params(labelsize=8)
    plt.tight_layout(); plt.savefig(out, dpi=140, bbox_inches='tight'); plt.close()


def gantt_ventanas(filas, fecha, out):
    """El grafico de DECISION: calendario con una barra por unidad = IC 95 % de la
    ventana estimada 'seco como la referencia', punto = estimacion central, linea
    punteada = fecha de analisis. Unidad sin ventana publicable -> rotulo explicito
    (nunca una barra inventada)."""
    f0 = datetime.date.fromisoformat(fecha)
    fig, ax = plt.subplots(figsize=(11, 0.66 * len(filas) + 1.9))
    xmin = f0 - datetime.timedelta(2); xmax = f0 + datetime.timedelta(14)
    for y, r in enumerate(filas[::-1]):
        v = r.get('ventana')
        if v and v.get('alcanzado'):
            fc = datetime.date.fromisoformat(v['fecha'])
            ax.plot(date2num(fc), y, '*', color=LIMA, ms=14, mec='#3A6B12', zorder=4)
            ax.annotate('alcanzado (%s)' % _dm(v['fecha']), (date2num(fc), y + 0.32),
                        ha='center', fontsize=9, fontweight='bold', color='#3A6B12')
        elif v and v.get('ic'):
            fc = datetime.date.fromisoformat(v['fecha'])
            a = datetime.date.fromisoformat(v['ic'][0])
            b_ = datetime.date.fromisoformat(v['ic'][1])
            ax.barh(y, max((b_ - a).days, 0.5), left=date2num(a), height=0.46,
                    color=TEAL, alpha=0.8, edgecolor='none', zorder=3)
            xmax = max(xmax, b_ + datetime.timedelta(4))
            ax.plot(date2num(fc), y, 'o', color='#083D3A', ms=7, zorder=4)
            ax.annotate(_dm(v['fecha']), (date2num(fc), y + 0.32), ha='center',
                        fontsize=9, fontweight='bold', color='#083D3A')
            xmax = max(xmax, fc + datetime.timedelta(5))
        else:
            ax.annotate('sin estimación publicable (serie no ajustable o cruce a >30 días)',
                        (date2num(f0 + datetime.timedelta(1)), y), va='center',
                        fontsize=8.5, color='#8A8A8A', style='italic')
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([f"{r['id']}  ({r['area']:.0f} ha)" for r in filas[::-1]], fontsize=10)
    ax.axvline(date2num(f0), color='#CC0000', ls='--', lw=1.2)
    ax.annotate(' análisis %s' % _dm(f0.isoformat()), (date2num(f0), len(filas) - 0.42),
                fontsize=8.5, color='#CC0000')
    ax.set_xlim(date2num(xmin), date2num(xmax)); ax.set_ylim(-0.6, len(filas) - 0.25)
    from matplotlib.ticker import FuncFormatter
    from matplotlib.dates import num2date
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(FuncFormatter(
        lambda x, _: _dm(num2date(x).date().isoformat())))
    ax.grid(axis='x', alpha=0.3); ax.set_axisbelow(True)
    for sp in ('top', 'right', 'left'):
        ax.spines[sp].set_visible(False)
    ax.set_title('Ventana estimada "seco como la referencia" — estado espectral, no fecha de cosecha',
                 fontsize=12, fontweight='bold', loc='left')
    plt.tight_layout(); plt.savefig(out, dpi=150, bbox_inches='tight'); plt.close()


def trayectorias_ndmi(unis, nivel, fecha, out):
    """La EVIDENCIA de las ventanas: puntos NDMI medidos por unidad + curva del
    ajuste logistico (piso anclado en la referencia seca) + nivel de cruce."""
    fig, ax = plt.subplots(figsize=(11, 5.0))
    cmap = plt.get_cmap('tab10')
    f0 = datetime.date.fromisoformat(fecha)
    for j, u in enumerate(unis):
        col = cmap(j % 10)
        pts = [(datetime.date.fromisoformat(p['fecha']), p['NDMI'])
               for p in u['serie'] if p.get('NDMI') is not None]
        ax.plot([d for d, _ in pts], [v for _, v in pts], 'o', ms=4.5, color=col)
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
            ax.plot([], [], 'o-', color=col, label=u['id'] + ' (nivel alcanzado)')
        else:
            ax.plot([], [], 'o-', color=col, label=u['id'] + ' (sin ajuste publicable)')
    ax.axhline(nivel, color='k', ls=':', lw=1.2)
    ax.annotate('  nivel de la referencia seca declarada (NDMI p90)', (date2num(f0 - datetime.timedelta(55)), nivel),
                fontsize=8.5, va='bottom')
    ax.axvline(date2num(f0), color='#CC0000', ls='--', lw=1.0, alpha=0.7)
    ax.set_xlim(date2num(datetime.date(int(fecha[:4]), 6, 1)), date2num(f0 + datetime.timedelta(28)))
    ax.xaxis_date(); ax.xaxis.set_major_locator(MonthLocator()); ax.xaxis.set_major_formatter(DateFormatter('%b'))
    ax.grid(alpha=0.25); ax.set_ylabel('NDMI (agua del dosel)')
    ax.legend(fontsize=8.5, loc='upper right', ncol=2)
    ax.set_title('Agua del dosel (NDMI): trayectoria medida y ajuste con piso en la referencia seca',
                 fontsize=12, fontweight='bold', loc='left')
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


TEAL, LIMA = '#0D9488', '#7FD633'
# fechas SIEMPRE dia-mes con nombre ('29-ago'): '09-01' se lee 9 de enero en pt-BR
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
_dm = lambda iso: f"{int(iso[8:10]):02d}-{MESES[int(iso[5:7]) - 1]}"


def _anillos(ring):
    """Lista de anillos [(x,y)...] tolerante a Polygon/MultiPolygon."""
    if isinstance(ring[0][0], (int, float)):
        return [ring]
    if isinstance(ring[0][0][0], (int, float)):
        return ring
    return [rr for parte in ring for rr in _anillos(parte)]


def mapas(lotes_ord, fecha, out, key='raster', cmap=None, vmin=0.3, vmax=VMAX,
          cticks=(0.5, 1.6, 3.2, 5.0),
          clabels=('Clor. agotada', 'Madurando', 'Verde', 'Pleno'),
          suptit=None, ref_marca=None):
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
            ax.annotate('%s · %.0f %%' % (bq['nombre'].split(' (')[0], bq['prog']),
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
        av_txt = ('%.0f-%.0f %%' % r['prog_rango']) if mezclado else ('%.0f %%' % r['prog'])
        ax.set_title(' %s  ·  %.0f ha  ·  avance %s ' % (r['id'], r['area'], av_txt),
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
    fig.suptitle(suptit or ('Madurez dentro de cada lote · %s · CIre, superficie suavizada (~30 m) para lectura'
                            % fecha), fontsize=12.5, fontweight='bold', color='#0D9488', y=0.975)
    plt.savefig(out, dpi=170, bbox_inches='tight', facecolor='white'); plt.close()


# ---------- main ----------
def run(hkey, fecha):
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
        r['area'] = round(r['geom'].area(1).getInfo() / 1e4, 1)
        r['bloques'] = []
        if r['id'] in bloques_cfg and os.path.exists(bloques_cfg[r['id']]):
            for ft in json.load(open(bloques_cfg[r['id']], encoding='utf-8'))['features']:
                gb = ft['geometry']
                geob = ee.Geometry(dict(type=gb['type'], coordinates=_f2d(gb['coordinates'])))
                sb = trayectoria(geob, f"{yr}-04-15", fin)
                sbl, exb = mz.filtrar_bruma(sb)
                excluidas_todas += [dict(lote=ft['properties']['bloque_id'], **e) for e in exb]
                r['bloques'].append(dict(id=ft['properties']['bloque_id'],
                                         nombre=ft['properties'].get('nombre', ft['properties']['bloque_id']),
                                         ring=_f2d(gb['coordinates']),
                                         serie=sbl, area=round(geob.area(1).getInfo() / 1e4, 1)))

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
            u['ventana'] = mz.ajuste_cruce(
                [(p['fecha'], p['NDMI']) for p in u['serie']],
                piso=ref['ndmi_p50'], nivel=ref['ndmi_p90'],
                sigma_min=mz.SIGMA_NDMI_ESCENA)
        u['inicio'] = mz.inicio_cobertura([(p['fecha'], p['cire_corr']) for p in u['serie']])

    for r in lotes:
        evaluar(r)
        for bq in r['bloques']:
            evaluar(bq)
        # colapso de DISPLAY: si los bloques convergieron se reporta una sola fila
        # (la geometria del catalogo no se toca: la fecha de siembra es un hecho).
        r['colapsado'] = mz.colapsar_bloques([bq['prog'] for bq in r['bloques']]) if r['bloques'] else False
        r['raster'] = raster_cire(r['geom'], fecha)
        r['raster_ndmi'] = raster_indice(r['geom'], fecha, 'NDMI')
        r['rgb'] = raster_rgb(r['geom'], fecha)
        # bandera universal de lote DESPAREJO (log CIre p90-p10 de la escena; umbral
        # medido contra los lotes uniformes de la flota SA/SF). LIMITE declarado: es
        # una bandera DE UNA ESCENA; cuando las trayectorias se cruzan (caso 01-ago)
        # no ve la mezcla — la particion declarada si.
        # el umbral de desparejo se calibro sobre INTERIOR (sin borde): erosionar
        # 2 px de 10 m (= 20 m) antes de medir, o el borde dispara la bandera solo.
        from scipy.ndimage import binary_erosion as _be
        _a = r['raster'][0]
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

    png_cinta = f"{MED}/cinta_orden_cosecha_{hkey}.png"
    png_mapas = f"{MED}/mapas_madurez_{hkey}.png"
    png_ndmi = f"{MED}/mapas_agua_{hkey}.png"
    png_gantt = f"{MED}/ventanas_secado_{hkey}.png"
    png_tray = f"{MED}/trayectoria_agua_{hkey}.png"
    cinta(orden, fecha, png_cinta); mapas(orden, fecha, png_mapas)
    mapas(orden, fecha, png_ndmi, key='raster_ndmi', cmap=plt.get_cmap('BrBG'),
          vmin=0.0, vmax=0.5, cticks=(0.04, 0.18, 0.32, 0.46),
          clabels=('Seco', 'Secándose', 'Húmedo', 'Muy húmedo'),
          suptit='Agua del dosel por lote · %s · NDMI, superficie suavizada (~30 m) para lectura' % fecha,
          ref_marca=(ref['ndmi_p90'], 'ref. seca') if ref else None)
    # unidades del gantt/trayectorias = las mismas filas que la tabla: lote entero,
    # o sus sectores si esta DESPAREJO (el numero accionable vive en las sub-filas)
    filas_g, unis_t = [], []
    for r in orden:
        mezclado = bool(r['bloques']) and not r['colapsado']
        if mezclado:
            for bq in sorted(r['bloques'], key=lambda x: -x['prog']):
                nom = f"{r['id']} · {bq['nombre'].split(' (')[0]}"
                filas_g.append(dict(id=nom, area=bq['area'], ventana=bq.get('ventana')))
                unis_t.append(dict(id=nom, serie=bq['serie'], ventana=bq.get('ventana')))
        else:
            filas_g.append(dict(id=r['id'], area=r['area'], ventana=r.get('ventana')))
            unis_t.append(dict(id=r['id'], serie=r['serie'], ventana=r.get('ventana')))
    n_gantt = len(filas_g)
    if ref:
        gantt_ventanas(filas_g, fecha, png_gantt)
        trayectorias_ndmi(unis_t, ref['ndmi_p90'], fecha, png_tray)

    B = Brand(logo=f"{SKILL}/assets/logo_pix_azulnegro_trim.png",
              footer_center=f"{cfg['nombre']} · Orden de madurez {yr}")
    tot = round(sum(r['area'] for r in lotes), 1)
    agot = sum(1 for r in lotes if r['rk'] == 3)
    prim = orden[0]['id']
    st = []
    st += B.cover_filler()
    st += [B.P("Ficha", "H1"), B.hr()]
    st += [B.meta_table([("Cliente", cfg['nombre']), ("Lotes", f"{len(lotes)}  ·  {tot} ha"),
                         ("Análisis", f"Sentinel-2 · {fecha}"),
                         ("Producto", "Orden relativo de madurez (no es fecha de cosecha)")])]
    st += [B.callout("Situación", f"Lotes con clorofila agotada: {agot}. Más avanzado: {prim}. "
                     f"La humedad de grano y el PH se miden a campo.")]
    st += [PageBreak()]
    st += [B.P("Resumen", "H1"), B.hr()]
    st += [B.kpi_strip([(f"{len(lotes)}", "lotes"), (f"{tot:.0f}", "ha"),
                        (f"{agot}", "clorofila agotada"), (prim, "más avanzado")])]
    st += [Image(png_cinta, width=15 * cm, height=min(9 * cm, 15 * cm * (0.62 * len(lotes) + 1.6) / 11))]
    st += [B.P("Verde = en llenado · rojo = clorofila agotada. Línea punteada = fecha de análisis. "
               "CIre de S2C llevado a escala S2A/B (factor por nivel).", "Note")]
    st += [B.sec(1, "Orden de madurez")]

    def _vent(u):
        v = u.get('ventana')
        if not v:
            return "-"
        if v.get('alcanzado'):
            return "alcanzado"
        if v['ic']:
            return f"{_dm(v['ic'][0])}..{_dm(v['ic'][1])}"
        return "-"      # sin intervalo no se publica fecha (auditoria 21-ago)

    _co = lambda x: f"{x:.2f}".replace('.', ',')      # coma decimal en todo el documento
    tab = [["#", "Lote / Sector", "Área", "Estado", "Avance", "NDMI", "Seco como ref. (est.)"]]
    for k, r in enumerate(orden, 1):
        mezclado = bool(r['bloques']) and not r['colapsado']
        # REGLA (consulta a dos agentes, 2026-08-19): un lote con bandera NO lleva
        # promedio — un rango o nada. El numero accionable vive en las sub-filas.
        av = (f"{r['prog_rango'][0]:.0f}-{r['prog_rango'][1]:.0f}%" if mezclado
              else f"{r['prog']:.0f}%")
        est = (r['estado'].replace('Clorofila agotada, dosel aun humedo', 'Clor. agotada, aun humedo')
                          .replace('DESPAREJO - %d plantios, ver sectores' % len(r['bloques']), 'DESPAREJO: ver sectores'))
        # 'ver sectores' y no '-': el '-' queda reservado para 'no ajustable /
        # no se extrapola' — dos significados nunca viajan con el mismo simbolo
        tab.append([str(k), r['id'], f"{r['area']:.0f} ha", est, av,
                    _co(r['ndmi']), "ver sectores" if mezclado else _vent(r)])
        if mezclado:
            for bq in sorted(r['bloques'], key=lambda x: -x['prog']):
                tab.append(["", "   - " + bq['nombre'], f"{bq['area']:.0f} ha",
                            bq['estado'].replace('Clorofila agotada, dosel aun humedo', 'Clor. agotada, aun humedo'),
                            f"{bq['prog']:.0f}%", _co(bq['ndmi']), _vent(bq)])
        elif r['colapsado']:
            tab.append(["", "   - bloques convergieron: se reportan juntos", "", "", "", "", ""])
    st += [B.tbl(tab, [0.7 * cm, 3.7 * cm, 1.4 * cm, 4.3 * cm, 1.5 * cm, 1.1 * cm, 3.1 * cm])]
    if any(r['bloques'] for r in lotes):
        st += [B.P("Sectores: pasadas y fechas de siembra declaradas por el cliente; el límite entre "
                   "sectores está estimado por satélite (NDVI may-jul), es fijo durante la campaña y no es "
                   "catastral (±10-20 m). Las pasadas del 26 y 29-abr no se distinguen en madurez y se "
                   "reportan como un solo sector. Cada sector se mide contra su PROPIO pico. "
                   "El orden del lote lo fija su sector más avanzado.", "Note")]
    if ref:
        ndmi90_txt = f"{ref['ndmi_p90']:.3f}".replace('.', ',')
        st += [B.P(f"Referencia seca declarada por el cliente: CIre ≤ {_co(ref['cire_p90'])} y "
                   f"NDMI ≤ {ndmi90_txt}. "
                   "'Seco como la referencia' exige los dos ejes: cuando la clorofila toca piso, "
                   "el que separa es el agua del dosel (NDMI).", "Note")]
        st += [B.P("'Seco como ref. (est.)' = ventana estimada en que el lote alcanza el nivel de "
                   "agua de dosel de la referencia seca (NDMI ≤ p90 de la referencia, el mismo "
                   "umbral del estado), por ajuste de la trayectoria NDMI con piso anclado en la "
                   "referencia, medido en el compuesto ±5 días de la fecha de análisis. El "
                   "intervalo usa la repetibilidad medida del NDMI (0,021); cobertura simulada "
                   "~90 % en el régimen publicable. Es una fecha de estado espectral, no de "
                   "cosecha: la humedad de grano y el PH se miden a campo. La ventana asume la "
                   "trayectoria de secado observada: lluvia re-humedece el dosel y la corre hacia "
                   "adelante; se recalcula con cada escena limpia (~5 días). '-' = serie aún no "
                   "ajustable o cruce a más de 30 días (no se extrapola). 'alcanzado' = la última "
                   "medición ya está al nivel de la referencia.", "Note")]
        st += [B.P("Control de consistencia (21-ago-2026): el ajuste construido solo con datos al "
                   "19-ago reprodujo el NDMI de la escena siguiente con error ≤ 0,021. Es una "
                   "verificación a 2 días, no una validación de la fecha extrapolada; el eje CIre "
                   "no pasó la misma prueba y por eso las fechas se estiman solo sobre el agua.", "Note")]
        # linea B11 intra-escena, calculada EN ESTA corrida: sostiene 'aun humedo'
        b11s = [u['b11'] for r0 in lotes for u in ([r0] + r0['bloques']) if u.get('b11') is not None]
        if b11s and ref.get('b11_p50') is not None:
            dmin = ref['b11_p50'] - max(b11s); dmax = ref['b11_p50'] - min(b11s)
            if dmin > 0:
                st += [B.P(f"En la escena del análisis, la banda B11 (agua) de todas las unidades "
                           f"quedó {_co(dmin)}-{_co(dmax)} por debajo de la referencia seca: "
                           "ningún dosel alcanzó su estado.", "Note")]
    elif cfg.get('referencia_seca'):
        # 'no pude mirar' nunca viaja como 'sin novedad': la columna queda en '-'
        # y esta nota dice POR QUE (referencia nublada/brumosa en toda la ventana)
        st += [B.P("Referencia seca declarada pero SIN escena limpia en ±5 días de la fecha de "
                   "análisis: el eje de agua y la columna 'Seco como ref. (est.)' NO SON "
                   "EVALUABLES en esta corrida. Se reintenta en el próximo paso satelital.", "Note")]
    if excluidas_todas:
        st += [B.P("Fechas excluidas por bruma (cs mediana < 0,80, PSRI < −0,02 o B2 > 0,15): "
                   + " · ".join(sorted({f"{e['fecha']} ({e['lote']})" for e in excluidas_todas})), "Note")]
    if ref:
        st += [B.sec(2, "Ventana estimada de secado")]
        st += [Image(png_gantt, width=15 * cm,
                     height=min(9 * cm, 15 * cm * (0.66 * n_gantt + 1.9) / 11))]
        st += [B.P("Barra = intervalo de confianza 95 % · punto = estimación central · línea roja = "
                   "fecha de análisis. Estado espectral, no fecha de cosecha.", "Note")]
        st += [Image(png_tray, width=15 * cm, height=15 * cm * 5.0 / 11)]
        st += [B.P("Puntos = NDMI medido por escena (sin bruma) · curva = ajuste logístico con piso "
                   "en la referencia seca · punteada = nivel de cruce.", "Note")]
    sec_m = 3 if ref else 2
    st += [B.sec(sec_m, "Mapas por lote: madurez y agua del dosel")]
    st += [Image(png_mapas, width=15 * cm, height=15 * cm * 0.4 * ((len(lotes) + 1) // 2))]
    st += [B.P("CIre (clorofila): rojo = clorofila agotada. Ordena la madurez general.", "Note")]
    st += [Image(png_ndmi, width=15 * cm, height=15 * cm * 0.4 * ((len(lotes) + 1) // 2))]
    st += [B.P("NDMI (agua del dosel): marrón = más seco, azul-verde = más húmedo. DENTRO de cada "
               "lote, los sectores marrones se secan primero: por ahí empezar el muestreo de "
               "humedad de grano.", "Note")]
    st += [PageBreak()]
    st += [B.sec(sec_m + 1, "Método y alcance")]
    st += [B.P("Madurez por caída del CIre respecto del pico propio (pico solo con escenas S2A/B; "
               "S2C corregido por nivel). Compuerta de bruma por lote y fecha. Producto RELATIVO: "
               "ordena lotes para priorizar el muestreo de humedad de grano. La columna 'Seco como "
               "ref. (est.)' es la fecha estimada de un estado espectral (agua de dosel al nivel de "
               "la referencia seca declarada), no una fecha de cosecha: la ventana de trilla la "
               "fijan la humedad de grano y el PH medidos a campo.", "Body")]
    st += [B.callout("Acción", f"Medir humedad de grano y PH empezando por {prim}. "
                     "Reevaluar en el próximo paso satelital limpio (~5 días).")]
    out_pdf = f"{SALIDA}/Entregable_Orden_Madurez_{hkey}_{fecha}.pdf"
    B.build(out_pdf, st, cover_title="Orden de madurez — Trigo",
            cover_subtitle=f"{cfg['nombre']} · Seguimiento satelital · {yr}")
    print("PDF ->", out_pdf)
    return out_pdf


if __name__ == "__main__":
    hkey = sys.argv[1] if len(sys.argv) > 1 else 'SA_SF'
    fecha = sys.argv[2] if len(sys.argv) > 2 else datetime.date.today().isoformat()
    if hkey not in HACIENDAS:
        sys.exit(f"Hacienda '{hkey}' no esta en HACIENDAS. Opciones: {list(HACIENDAS)}")
    run(hkey, fecha)
