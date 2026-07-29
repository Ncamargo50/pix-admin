# -*- coding: utf-8 -*-
"""¿Que modelo de trayectoria describe al cultivo? Medido sobre los lotes reales.

EL PROBLEMA QUE VIENE A RESOLVER, YA MEDIDO
-------------------------------------------
La escala del criterio sale de la MAD de los residuos contra una RECTA ajustada sobre
la ventana de base. Sobre los 4 lotes de trigo, al 2026-07-16:

    lote               eje    sigma del ajuste   ruido de corto plazo   razon
    SANTO_ANTONIO-01   NDMI       0,1784               0,0598           3,0 x
    SANTO_ANTONIO-01   NDRE       0,1569               0,0241           6,5 x
    SANTO_ANTONIO-02   NDMI       0,1187               0,0447           2,7 x
    SANTO_ANTONIO-02   NDRE       0,1097               0,0349           3,1 x
    SAO_FRANCISCO-01   NDMI       0,1527               0,0428           3,6 x
    SAO_FRANCISCO-01   NDRE       0,1460               0,0256           5,7 x
    SAO_FRANCISCO-02   NDMI       0,1707               0,0452           3,8 x
    SAO_FRANCISCO-02   NDRE       0,1491               0,0261           5,7 x

(el ruido de corto plazo se estima con diferencias entre escenas consecutivas, que
son casi inmunes a una tendencia suave — ver `verificar_escala_real.ruido_corto`)

O sea que entre el 63% y el 85% de la varianza que el criterio llama "ruido" es
ERROR DEL MODELO: la recta no describe al trigo entre emergencia y llenado de grano.
Consecuencias medidas, las dos malas:

  · SD(z) va de 0,31 a 1,24 entre lotes del MISMO campo el MISMO dia -> el umbral no
    significa lo mismo en cada lote. Es el defecto que v2 decia venir a corregir de
    v1 (donde iba de 0,38 a 1,56).
  · la media de z da -0,70 a -0,86 -> no es dispersion, es SESGO: la recta extrapola
    hacia arriba mientras el cultivo se aplana, asi que TODO el lote cae por debajo.

Y NO SE ARREGLA BAJANDO SIGMA: con el numerador sesgado y un sigma 3 veces menor,
la media de z pasaria a -2,5 y se marcaria el lote entero. Hay que arreglar el MODELO.

QUE COMPARA ESTE ARNES
----------------------
Tres candidatos, todos sobre los mismos datos reales:

  1. RECTA               lo que hay hoy.
  2. CUADRATICA          agrega curvatura. Cuesta un grado de libertad mas (con 8-9
                         escenas quedan 5-6), y captura el aplanamiento.
  3. RECTA RELATIVA AL LOTE   al residuo de cada fecha se le resta la MEDIANA
                         ESPACIAL del residuo de esa fecha. Absorbe cualquier error
                         de modelo COMPARTIDO —fenologia, clima, calibracion del
                         sensor ese dia— porque todos los pixeles del lote lo tienen
                         igual. Precio que hay que declarar: queda CIEGO a un evento
                         uniforme sobre todo el lote.

CRITERIOS DE DECISION, fijados antes de mirar:
  · `razon` -> 1      el modelo describe la trayectoria; sigma pasa a ser ruido.
  · `media(z)` -> 0   no hay sesgo sistematico.
  · `SD(z)` -> 1 y PARECIDO ENTRE LOTES: es lo que hace que el umbral signifique lo
                mismo en todos los lotes, que es la unica forma de tener un alfa
                comparable.

    python -m medicion.comparar_trayectoria --hasta 2026-07-16
"""
import argparse
import json
import sys

MODELOS = ('recta', 'cuadratica', 'recta_relativa', 'cuadratica_relativa',
           'relativa_agrupada')
# `relativa_agrupada` = recta + centrado por la mediana del lote en cada fecha +
# escala AGRUPADA entre pixeles. Es el compuesto que sale de las dos mediciones:
# el centrado arregla la razon (3,3 -> 1,1) y el agrupado tiene que arreglar el
# rango de SD(z) (0,85 - 2,74 con la escala por pixel).


def _bandas_t(img, dia0, ejes, grado):
    """[1, t, t^2...] + los ejes, todo enmascarado igual que el eje 0."""
    import ee
    img = ee.Image(img)
    t = (ee.Number(ee.Date(img.get('system:time_start')).millis())
         .subtract(dia0).divide(86400000))
    cap = [ee.Image(1).rename('c0'), ee.Image(ee.Number(t)).float().rename('c1')]
    if grado >= 2:
        cap.append(ee.Image(ee.Number(t).pow(2)).float().rename('c2'))
    cap.append(img.select(ejes))
    return (ee.Image.cat(cap)
            .updateMask(img.select(ejes[0]).mask())
            .set('t', t)
            .copyProperties(img, ['system:time_start', 'fecha']))


def _ajustar(base, dia0, ejes, grado):
    """Coeficientes por pixel de un ajuste de grado `grado` (1=recta, 2=cuadratica).

    Devuelve una funcion `esperado(eje, t)` que da la imagen del valor esperado.
    """
    import ee
    nx = grado + 1
    cols = ['c%d' % i for i in range(nx)]
    con = base.map(lambda i: _bandas_t(i, dia0, ejes, grado))
    coef = {}
    for e in ejes:
        fit = con.select(cols + [e]).reduce(
            ee.Reducer.linearRegression(numX=nx, numY=1))
        # 'coefficients' es un array nx x 1
        c = fit.select('coefficients').arrayProject([0]).arrayFlatten([cols])
        coef[e] = c

    def esperado(e, t):
        img = coef[e].select('c0')
        img = img.add(coef[e].select('c1').multiply(ee.Image(ee.Number(t))))
        if grado >= 2:
            img = img.add(coef[e].select('c2')
                          .multiply(ee.Image(ee.Number(t).pow(2))))
        return img.rename(e)

    return esperado


def _stats(img, geom, escala, nom='u'):
    import ee
    red = (ee.Reducer.count().combine(ee.Reducer.mean(), '', True)
           .combine(ee.Reducer.stdDev(), '', True))
    return img.rename(nom).reduceRegion(
        reducer=red, geometry=geom, scale=escala, maxPixels=1e9,
        bestEffort=False).getInfo()


def evaluar_modelo(sitio, feat, hasta, modelo, escala=None):
    """sigma, razon contra el ruido corto, media(z) y SD(z) para un modelo."""
    import ee
    import pandas as pd

    from pix_alerta import config as cfg
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    escala = escala or cri.ESCALA
    ejes = list(cfg.EJES)
    geom = fo._geom_lote(sitio, feat)
    ventana = cri.ventana_de(sitio)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]
    base = cri._coleccion_limpia(geom, desde, fin)
    n = int(base.size().getInfo() or 0)
    if n < 5:
        return None
    dia0 = ee.Date(desde).millis()

    # la escena a evaluar: la mas reciente con cobertura, igual que en produccion
    cand = cri._coleccion_limpia(
        geom, str(pd.Timestamp(hasta) - pd.Timedelta(days=cri.VENTANA_ACTUAL_DIAS))[:10],
        str(pd.Timestamp(hasta) + pd.Timedelta(days=1))[:10])

    def _cob(img):
        img = ee.Image(img)
        c = (img.select(ejes[0]).mask().unmask(0, False).reduceRegion(
            ee.Reducer.mean(), geom, escala, maxPixels=int(1e9),
            bestEffort=True).values().get(0))
        return img.set('cob', ee.Algorithms.If(c, c, 0))

    cand = cand.map(_cob).filter(ee.Filter.gte('cob', cri.COB_MINIMA_ACTUAL))
    if not cand.size().getInfo():
        return None
    actual = ee.Image(cand.sort('system:time_start', False).first())
    t_act = (ee.Number(ee.Date(actual.get('system:time_start')).millis())
             .subtract(dia0).divide(86400000))

    grado = 2 if modelo.startswith('cuadratica') else 1
    relativa = modelo.endswith('_relativa') or modelo == 'relativa_agrupada'
    esperado = _ajustar(base, dia0, ejes, grado)

    def _res(img):
        img = ee.Image(img)
        t = (ee.Number(ee.Date(img.get('system:time_start')).millis())
             .subtract(dia0).divide(86400000))
        cap = [img.select(e).subtract(esperado(e, t)).rename(e) for e in ejes]
        return (ee.Image.cat(cap).updateMask(img.select(ejes[0]).mask())
                .copyProperties(img, ['system:time_start']))

    res = base.map(_res)

    if relativa:
        # A cada fecha se le resta la MEDIANA ESPACIAL de su residuo. Lo que queda es
        # "cuanto se aparta este pixel de lo que hizo el lote ese dia".
        def _centrar(img):
            img = ee.Image(img)
            m = img.reduceRegion(ee.Reducer.median(), geom, escala,
                                 maxPixels=int(1e9), bestEffort=True)
            corr = ee.Image.cat([
                ee.Image.constant(ee.Number(
                    ee.Algorithms.If(m.get(e), m.get(e), 0))).rename(e)
                for e in ejes])
            return img.subtract(corr).copyProperties(img, ['system:time_start'])

        res = res.map(_centrar)

    sigma_px = res.map(lambda i: ee.Image(i).abs()).median().multiply(1.4826)
    if modelo == 'relativa_agrupada':
        # ESCALA AGRUPADA: se juntan los cuadrados de los residuos de TODOS los
        # pixeles del lote (miles x n fechas) en vez de 8-9 por pixel, con los
        # grados de libertad correctos. Se recorta antes en 3 sigmas para que una
        # nube residual no infle la escala de todo el lote.
        corte = sigma_px.max(ee.Image.constant(cri.SIGMA_MINIMA)).multiply(3.0)
        rec = res.map(lambda i: ee.Image(i).max(corte.multiply(-1)).min(corte))
        ss = rec.map(lambda i: ee.Image(i).pow(2)).sum()
        nobs = base.select([ejes[0]]).count()
        gl = nobs.subtract(2).max(1).rename('gl').updateMask(ss.select(0).mask())
        tot = ss.addBands(gl).reduceRegion(
            ee.Reducer.sum(), geom, escala, maxPixels=int(1e9), bestEffort=True)
        gtot = ee.Number(tot.get('gl')).max(1)
        sigma = ee.Image.cat([
            ee.Image.constant(ee.Number(tot.get(e)).divide(gtot).sqrt()
                              .divide(0.9975)).rename(e) for e in ejes])
    else:
        sigma = sigma_px

    # ruido de corto plazo, INDEPENDIENTE del modelo: diferencias consecutivas
    lista = base.sort('system:time_start').toList(n)
    difs = [ee.Image(lista.get(i)).select(ejes)
            .subtract(ee.Image(lista.get(i - 1)).select(ejes)).divide(2 ** 0.5)
            for i in range(1, n)]
    dcol = ee.ImageCollection(difs)
    dmed = dcol.median()
    sig_dif = (dcol.map(lambda i: ee.Image(i).subtract(dmed).abs())
               .median().multiply(1.4826))

    r_act = ee.Image.cat(
        [actual.select(e).subtract(esperado(e, t_act)).rename(e) for e in ejes])
    if relativa:
        m = r_act.reduceRegion(ee.Reducer.median(), geom, escala,
                               maxPixels=int(1e9), bestEffort=True)
        corr = ee.Image.cat([
            ee.Image.constant(ee.Number(
                ee.Algorithms.If(m.get(e), m.get(e), 0))).rename(e)
            for e in ejes])
        r_act = r_act.subtract(corr)

    out = {'n_base': n, 'fecha': actual.get('fecha').getInfo()}
    for e in ejes:
        sg = sigma.select(e).max(cri.SIGMA_MINIMA)
        z = r_act.select(e).divide(sg)
        s = _stats(z, geom, escala)
        _md = z.rename('u').reduceRegion(ee.Reducer.median(), geom, escala,
                                         maxPixels=int(1e9),
                                         bestEffort=False).getInfo()
        a = _stats(sigma.select(e), geom, escala)
        b = _stats(sig_dif.select(e), geom, escala)
        sa = a.get('u_mean') or 0.0
        sd = b.get('u_mean') or 0.0
        out[e] = {'n_px': int(s.get('u_count') or 0),
                  'sigma': sa, 'sigma_dif': sd,
                  'razon': (sa / sd) if sd else None,
                  'media_z': s.get('u_mean'), 'sd_z': s.get('u_stdDev'),
                  'mediana_z': _md.get('u')}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--cliente', default='TRIGO')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import config as cfg
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    print('\n%-20s %-6s %-16s %8s %8s %6s %8s %7s'
          % ('lote', 'eje', 'modelo', 'sigma', 'sig_dif', 'razon', 'media(z)',
             'SD(z)'))
    print('-' * 92)
    acum = {}
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            for modelo in MODELOS:
                try:
                    r = evaluar_modelo(s, f, a.hasta, modelo)
                except Exception as exc:            # noqa: BLE001
                    print('%-20s %-6s %-16s  AVERIA %s: %s'
                          % (lid, '-', modelo, type(exc).__name__, str(exc)[:50]))
                    continue
                if r is None:
                    print('%-20s %-6s %-16s  sin datos suficientes'
                          % (lid, '-', modelo))
                    continue
                for e in cfg.EJES:
                    d = r[e]
                    print('%-20s %-6s %-16s %8.4f %8.4f %6.1f %8.3f %7.3f'
                          % (lid, e, modelo, d['sigma'], d['sigma_dif'],
                             d['razon'] or 0, d['media_z'] or 0, d['sd_z'] or 0))
                    acum.setdefault((modelo, e), []).append(d)
    print('\n' + '=' * 92)
    print('PROMEDIOS SOBRE LOS LOTES  (razon->1, media(z)->0, SD(z)->1 y parejo)')
    print('%-22s %-6s %7s %9s %10s %8s %14s'
          % ('modelo', 'eje', 'razon', 'media(z)', 'mediana(z)', 'SD(z)',
             'SD(z) min-max'))
    print('-' * 70)
    for (modelo, e), v in sorted(acum.items()):
        rz = [x['razon'] for x in v if x['razon']]
        mz = [x['media_z'] for x in v if x['media_z'] is not None]
        sz = [x['sd_z'] for x in v if x['sd_z'] is not None]
        if not sz:
            continue
        dz = [x['mediana_z'] for x in v if x.get('mediana_z') is not None]
        print('%-22s %-6s %7.1f %9.3f %10.3f %8.3f %14s'
              % (modelo, e, sum(rz) / len(rz) if rz else 0,
                 sum(mz) / len(mz) if mz else 0,
                 sum(dz) / len(dz) if dz else 0, sum(sz) / len(sz),
                 '%.2f - %.2f' % (min(sz), max(sz))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
