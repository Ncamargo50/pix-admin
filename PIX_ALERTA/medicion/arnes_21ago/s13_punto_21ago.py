# -*- coding: utf-8 -*-
"""PASO 13 v10. PUNTO NUEVO 21-ago-2026 (Sentinel-2A REAL, nube 0,04 %) + VALIDACION.

La escena del 21-ago es S2A: entra SIN correccion de nivel (el factor r(c) solo se
aplica a S2C). Es la primera medicion post-19-ago y sirve de test del ajuste
logistico publicado ese dia:

  1. baja el punto 21-ago por unidad (SA-01, b1, b2, b3, SF-01, SF-02) y para la
     referencia seca Assai, con compuerta CS+/SCL y control de bruma (B2/PSRI);
  2. CONSISTENCIA (no "validacion": el validador 21-ago mostro que una recta por los
     ultimos 2 puntos pasa casi igual a 2 dias, y que el eje CIre FALLA esta prueba):
     predice el 21-ago con el ajuste HECHO SOLO CON DATOS <= 19-ago y compara contra
     lo medido (error en unidades del indice y en RMSE del ajuste);
  3. re-ajusta la logistica CON el punto nuevo -> fechas de cruce actualizadas
     (CIre 1,0 y "seco como la referencia" por NDMI) con IC bootstrap;
  4. eje B11 crudo INTRA-escena (d' 10,5x medido, s12): unidad vs Assai en la
     MISMA escena del 21-ago — el unico uso valido de B11 crudo.

Salidas: GEE/punto_21ago.json, GEE/ajuste_logistico_21ago.json,
         PIX_ALERTA/medicion/trayectorias_21ago_SASF.png
"""
import os, json, datetime as dt, numpy as np
import ee
from scipy.optimize import curve_fit
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator

HERE = os.path.dirname(os.path.abspath(__file__)); GEE = os.path.join(HERE, 'GEE')
MED = r"D:/PIXADVISOR_AGENT_WORKSPACE/PIX_ALERTA/medicion"
import sys
sys.path.insert(0, r"D:/PIXADVISOR_AGENT_WORKSPACE/PIX_ALERTA")
from pix_alerta import madurez as mz     # compuerta de bruma UNICA (no duplicar umbrales)
A_ = json.load(open(os.path.join(GEE, 'analisis_19ago.json'), encoding='utf-8'))
REF = json.load(open(os.path.join(GEE, 'referencia_seca_assai.json'), encoding='utf-8'))
UNI = json.load(open(os.path.join(GEE, 'unidades.geojson'), encoding='utf-8'))
GREF = json.load(open(os.path.join(GEE, 'ref_trigo_seco_assai.geojson'), encoding='utf-8'))
R = A_['unidades']

D0 = dt.date(2026, 4, 1)
F = lambda s: (dt.date.fromisoformat(s) - D0).days
FD = lambda d: (D0 + dt.timedelta(days=float(d))).isoformat()
T21 = F('2026-08-21')

PISO_CIRE = REF['ref19']['CIre']['p50']     # 0,70 (mismo piso que s11: comparable)
PISO_NDMI = REF['ref19']['NDMI']['p50']     # 0,025
NIVEL_CIRE = 1.0

_f2d = lambda c: c[:2] if isinstance(c[0], (int, float)) else [_f2d(x) for x in c]

# unidades.geojson y ref_trigo_seco_assai.geojson estan en UTM 22S (EPSG:32722):
# hay que llevarlos a lon/lat o filterBounds no filtra nada (9964 escenas/dia).
from pyproj import Transformer
_TR = Transformer.from_crs('EPSG:32722', 'EPSG:4326', always_xy=True)
def _a4326(c):
    if isinstance(c[0], (int, float)):
        x, y = _TR.transform(c[0], c[1])
        return [x, y]
    return [_a4326(v) for v in c]

# ---------------- 1) punto 21-ago desde GEE ----------------
ee.Initialize(project='ee-gisagronomico')
CS = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')


def medir(geom_json, nombre):
    geom = ee.Geometry(dict(type=geom_json['type'],
                            coordinates=_a4326(_f2d(geom_json['coordinates']))))
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geom)
           .filterDate('2026-08-21', '2026-08-22').linkCollection(CS, ['cs_cdf']))
    n = col.size().getInfo()
    if n == 0:
        return None
    im0 = ee.Image(col.median())         # solo para medir cs_med del dia
    cs_med = im0.select('cs_cdf').reduceRegion(
        ee.Reducer.median(), geom, 20, maxPixels=1e9).getInfo().get('cs_cdf')
    # mascara POR IMAGEN antes del compuesto: la mediana de SCL entre 2 granulos
    # (p.ej. clases 4 y 9 -> 6,5) no es ninguna clase y tiraria pixeles validos
    def _mk(imx):
        cs_ok = imx.select('cs_cdf').gte(0.6)
        scl_ok = imx.select('SCL').eq(4).Or(imx.select('SCL').eq(5))
        return imx.updateMask(cs_ok.unmask(scl_ok))
    im = ee.Image(col.map(_mk).median())
    mascara = 'CS+' if cs_med is not None else 'SCL (CS+ tardio)'
    m = im.select('B4').mask()
    b = lambda k: im.select(k).divide(10000)
    iv = ee.Image.cat(
        b('B7').divide(b('B5').max(1e-6)).subtract(1).rename('CIre'),
        b('B4').subtract(b('B2')).divide(b('B6')).rename('PSRI'),
        b('B8A').subtract(b('B5')).divide(b('B8A').add(b('B5'))).rename('NDRE'),
        b('B8').subtract(b('B4')).divide(b('B8').add(b('B4'))).rename('NDVI'),
        b('B8A').subtract(b('B11')).divide(b('B8A').add(b('B11'))).rename('NDMI'),
        b('B2').rename('B2'), b('B11').rename('B11'), b('B12').rename('B12')).updateMask(m)
    clara = im.select('B4').updateMask(m).mask().reduceRegion(
        ee.Reducer.mean(), geom, 20, maxPixels=1e9).getInfo().get('B4') or 0
    q = iv.reduceRegion(ee.Reducer.percentile([10, 50, 90]), geom, 20, maxPixels=1e9).getInfo()
    if q.get('CIre_p50') is None:
        return None
    out = dict(fecha='2026-08-21', sat='A', mascara=mascara,
               cs_med=round(cs_med, 3) if cs_med is not None else None,
               clara=round(clara, 3))
    for k in ['CIre', 'PSRI', 'NDRE', 'NDVI', 'NDMI', 'B2', 'B11', 'B12']:
        out[k] = round(q[f'{k}_p50'], 4)
        out[f'{k}_p10'] = round(q[f'{k}_p10'], 4); out[f'{k}_p90'] = round(q[f'{k}_p90'], 4)
    # compuerta de bruma UNICA del modulo de produccion (caso 26-may)
    out['bruma'] = mz.bruma(out['cs_med'], out['PSRI'], out['B2'])[0]
    print('%-16s CIre %.3f  PSRI %+.3f  NDMI %+.3f  B11 %.3f  B2 %.3f  cs %.2f  clara %.2f %s'
          % (nombre, out['CIre'], out['PSRI'], out['NDMI'], out['B11'], out['B2'],
             out['cs_med'] or -1, out['clara'], 'BRUMA!' if out['bruma'] else ''))
    return out


print('=' * 100)
print('PUNTO 21-AGO-2026 (S2A, sin correccion de nivel)')
print('=' * 100)
P21 = {}
for ft in UNI['features']:
    k = ft['properties']['unidad']
    P21[k] = medir(ft['geometry'], k)
P21['REF Assai'] = medir(GREF['features'][0]['geometry'], 'REF Assai')

# ---------------- 2/3) logistica: validar y re-ajustar ----------------
def logistica(t, A, t0, tau, C):
    return C + A / (1.0 + np.exp((t - t0) / tau))


def ajustar(ts, ys, piso, n_boot=400, seed=0):
    ts, ys = np.asarray(ts, float), np.asarray(ys, float)
    if len(ts) < 4:
        return None
    try:
        p, _ = curve_fit(lambda t, A, t0, tau: logistica(t, A, t0, tau, piso),
                         ts, ys, p0=[ys.max() - piso, ts.mean(), 8.0],
                         bounds=([0.1, ts.min() - 40, 1.5], [12, ts.max() + 60, 40]), maxfev=20000)
    except Exception:
        return None
    resid = ys - logistica(ts, *p, piso)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        yb = logistica(ts, *p, piso) + rng.choice(resid, len(resid), replace=True)
        try:
            pb, _ = curve_fit(lambda t, A, t0, tau: logistica(t, A, t0, tau, piso),
                              ts, yb, p0=p, bounds=([0.1, ts.min() - 40, 1.5],
                                                    [12, ts.max() + 60, 40]), maxfev=5000)
            boots.append(pb)
        except Exception:
            pass

    def cruce(nivel):
        def solve(pp):
            A, t0, tau = pp
            if nivel <= piso or A <= (nivel - piso):
                return None
            return t0 + tau * np.log(A / (nivel - piso) - 1.0)
        c0 = solve(p)
        if c0 is None:
            return None
        cs = [c for c in (solve(pb) for pb in boots) if c is not None]
        if len(cs) < 50:
            return dict(dia=c0, ic=None)
        return dict(dia=c0, ic=(float(np.percentile(cs, 2.5)), float(np.percentile(cs, 97.5))))
    return dict(p=p, piso=piso, rmse=float(np.sqrt(np.mean(resid ** 2))), n=len(ts), cruce=cruce)


def post_pico(pts):
    j = int(np.argmax([y for _, y in pts]))
    return pts[j:]


print()
print('=' * 100)
print('VALIDACION: prediccion del ajuste <=19-ago vs medido 21-ago  ·  luego RE-AJUSTE con el punto nuevo')
print('=' * 100)
OUT = {}
series_plot = {}
for k, r in sorted(R.items(), key=lambda z: -z[1]['avance']):
    p = P21.get(k)
    fila = dict(unidad=k)
    pts_c = [(F(x['fecha']), x['CIre_corr']) for x in r['serie']]
    pts_n = [(F(x['fecha']), x['NDMI']) for x in r['serie'] if x.get('NDMI') is not None]
    # -- validacion (ajuste sin el 21-ago = replica s11) --
    ac0 = ajustar(*zip(*post_pico(pts_c)), piso=PISO_CIRE * 0.8)
    an0 = ajustar(*zip(*post_pico(pts_n)), piso=PISO_NDMI)
    if p and not p['bruma']:
        if ac0:
            pred = float(logistica(T21, *ac0['p'], PISO_CIRE * 0.8))
            fila['val_cire'] = dict(pred=round(pred, 3), medido=p['CIre'],
                                    delta=round(p['CIre'] - pred, 3),
                                    en_rmse=round(abs(p['CIre'] - pred) / max(ac0['rmse'], 1e-6), 2))
        if an0:
            pred = float(logistica(T21, *an0['p'], PISO_NDMI))
            fila['val_ndmi'] = dict(pred=round(pred, 3), medido=p['NDMI'],
                                    delta=round(p['NDMI'] - pred, 3),
                                    en_rmse=round(abs(p['NDMI'] - pred) / max(an0['rmse'], 1e-6), 2))
        # -- re-ajuste con el punto nuevo (S2A: CIre_corr = CIre) --
        pts_c = pts_c + [(T21, p['CIre'])]
        pts_n = pts_n + [(T21, p['NDMI'])]
    ac = ajustar(*zip(*post_pico(pts_c)), piso=PISO_CIRE * 0.8)
    an = ajustar(*zip(*post_pico(pts_n)), piso=PISO_NDMI)
    if ac:
        c1 = ac['cruce'](NIVEL_CIRE)
        fila['cire_rmse'] = round(ac['rmse'], 3); fila['n_post_pico'] = ac['n']
        if c1:
            fila['cruce_cire1'] = FD(c1['dia'])
            fila['cruce_cire1_ic'] = [FD(c1['ic'][0]), FD(c1['ic'][1])] if c1['ic'] else None
    if an:
        c2 = an['cruce'](PISO_NDMI + 0.03)
        if c2:
            fila['seco_ndmi'] = FD(c2['dia'])
            fila['seco_ndmi_ic'] = [FD(c2['ic'][0]), FD(c2['ic'][1])] if c2['ic'] else None
    # -- eje 2 en el dato del 21 (sin modelo): ya cruzo? --
    if p and not p['bruma']:
        ref21 = P21.get('REF Assai')
        if ref21 and not ref21['bruma'] and ref21['clara'] >= 0.85:
            fila['seco_hoy'] = bool(p['CIre'] <= ref21['CIre_p90'] and p['NDMI'] <= ref21['NDMI_p90'])
            fila['b11_delta_ref'] = round(p['B11'] - ref21['B11'], 4)
    OUT[k] = fila
    series_plot[k] = dict(pts_c=pts_c, pts_n=pts_n, ac=ac, an=an)
    vc = fila.get('val_cire'); vn = fila.get('val_ndmi')
    print('%-15s' % k)
    if vc:
        print('   CIre  pred %.2f  medido %.2f  (delta %+.2f = %.1fx rmse)'
              % (vc['pred'], vc['medido'], vc['delta'], vc['en_rmse']))
    if vn:
        print('   NDMI  pred %+.3f medido %+.3f (delta %+.3f = %.1fx rmse)'
              % (vn['pred'], vn['medido'], vn['delta'], vn['en_rmse']))
    print('   cruce CIre1: %s %s | seco(NDMI): %s %s | seco HOY(2 ejes vs ref21): %s | B11-ref %+0.3f'
          % (fila.get('cruce_cire1', '-'),
             ('IC ' + '..'.join(x[5:] for x in fila['cruce_cire1_ic'])) if fila.get('cruce_cire1_ic') else '',
             fila.get('seco_ndmi', '-'),
             ('IC ' + '..'.join(x[5:] for x in fila['seco_ndmi_ic'])) if fila.get('seco_ndmi_ic') else '',
             fila.get('seco_hoy', '?'), fila.get('b11_delta_ref', float('nan'))))

json.dump(dict(fecha='2026-08-21', escena='S2A T22KEV 21-ago (GEE)', solo_medicion=True,
               punto=P21),
          open(os.path.join(GEE, 'punto_21ago.json'), 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)
json.dump(dict(solo_medicion=True,
               nota=('ARNES DE MEDICION, no fuente del entregable: los numeros del cliente '
                     'salen de orden_cosecha.py (geometrias del catalogo + piso medido en la '
                     'corrida + guardas de publicacion de madurez.ajuste_cruce). Los cruce_cire1 '
                     'llevan SESGO conocido: la validacion del 21-ago midio que la logistica '
                     'sobre-predice CIre 0,15-0,38 (la clorofila cae mas rapido que la cola); '
                     'ninguna fecha de este JSON se publica sin pasar por madurez.ajuste_cruce.'),
               piso_cire=PISO_CIRE, piso_ndmi=PISO_NDMI, nivel_cire=NIVEL_CIRE, unidades=OUT),
          open(os.path.join(GEE, 'ajuste_logistico_21ago.json'), 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)

# ---------------- 4) grafico de trayectorias con ajustes ----------------
fig, axs = plt.subplots(1, 2, figsize=(13.5, 5.4))
cmap = plt.get_cmap('tab10')
tg = np.linspace(F('2026-06-15'), F('2026-09-20'), 300)
dg = [D0 + dt.timedelta(days=float(x)) for x in tg]
for j, (k, sp) in enumerate(series_plot.items()):
    col = cmap(j % 10)
    for ax, key, ajk, nivel, tit in [(axs[0], 'pts_c', 'ac', NIVEL_CIRE, 'CIre'),
                                     (axs[1], 'pts_n', 'an', PISO_NDMI + 0.03, 'NDMI')]:
        pts = sp[key]
        dd = [D0 + dt.timedelta(days=t) for t, _ in pts]
        ax.plot(dd, [y for _, y in pts], 'o', ms=4.5, color=col)
        aj = sp[ajk]
        if aj:
            ax.plot(dg, logistica(tg, *aj['p'], aj['piso']), '-', lw=1.4, color=col,
                    label=k if ax is axs[0] else None)
ref21 = P21.get('REF Assai')
for ax, nivel, txt in [(axs[0], NIVEL_CIRE, 'CIre 1,0 (~17 d pre-cosecha, banco Parana)'),
                       (axs[1], PISO_NDMI + 0.03, 'seco como la referencia (piso Assai +0,03)')]:
    ax.axhline(nivel, color='k', ls=':', lw=1.1)
    ax.text(dt.date(2026, 6, 17), nivel, ' ' + txt, fontsize=7.5, va='bottom')
    ax.axvline(dt.date(2026, 8, 21), color='#CC0000', ls='--', lw=1.0, alpha=0.6)
    ax.xaxis.set_major_locator(MonthLocator()); ax.xaxis.set_major_formatter(DateFormatter('%b'))
    ax.grid(alpha=0.25)
if ref21:
    axs[0].plot(dt.date(2026, 8, 21), ref21['CIre'], '*', ms=13, color='#8B4513', zorder=6)
    axs[1].plot(dt.date(2026, 8, 21), ref21['NDMI'], '*', ms=13, color='#8B4513', zorder=6,
                label='REF Assai 21-ago')
axs[0].set_title('CIre (escala S2A/B) — clorofila'); axs[1].set_title('NDMI — agua del dosel')
axs[0].legend(fontsize=8, loc='upper right'); axs[1].legend(fontsize=8, loc='upper right')
fig.suptitle('Trigo SA + SF — trayectorias de senescencia con ajuste logistico · punto nuevo 21-ago (S2A) en rojo',
             fontsize=12, fontweight='bold')
plt.tight_layout()
out_png = os.path.join(MED, 'trayectorias_21ago_SASF.png')
plt.savefig(out_png, dpi=150, bbox_inches='tight'); plt.close()
print('\nOK -> GEE/punto_21ago.json · GEE/ajuste_logistico_21ago.json ·', out_png)
