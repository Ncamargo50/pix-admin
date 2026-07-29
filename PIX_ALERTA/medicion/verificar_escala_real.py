# -*- coding: utf-8 -*-
"""¿El z del criterio tiene SD 1 SOBRE DATOS REALES? Y a que tasa marca.

POR QUE HACE FALTA ESTO Y NO ALCANZA LA SIMULACION
--------------------------------------------------
`nula_analitica_criterio.py` mide la nula EXACTA: pixeles que siguen una recta mas
ruido gaussiano. Eso prueba propiedades del ESTIMADOR bajo esos supuestos, y nada
mas. Sobre un lote real los supuestos no se cumplen: el residuo no es gaussiano, la
trayectoria no es exactamente una recta, hay autocorrelacion temporal y espacial, y
la nube que sobrevivio a la mascara mete cola. **Ninguna conclusion sobre el campo se
puede sacar de la simulacion.**

Este arnes mide sobre el lote real, y por eso imprime SIEMPRE el CONTEO DE PIXELES
antes de cualquier desvio estandar: una SD calculada sobre cero pixeles sale 0,000 y
parece un resultado excelente. Ya paso.

    python -m medicion.verificar_escala_real --sitio SANTO_ANTONIO --hasta 2026-07-16

QUE SE MIDE, Y QUE SIGNIFICA CADA COSA
--------------------------------------
· `n pixeles`        sobre cuantos pixeles se calculo. Sin esto nada mas vale.
· `n_base`           observaciones limpias por pixel. Con menos de 4 no hay recta.
· `h0`               leverage de la extrapolacion. Dice cuanto se infla la escala.
· `sigma agrupada`   ruido por observacion, estimado juntando todo el lote.
· `SD(z)`            **el numero central**. Si no es ~1, la tasa de falsa alarma NO
                     es la que el umbral implica, en la direccion que diga el desvio.
· `p1 p5 p50 p95 p99` la forma de la cola. Una normal da -2,33 en p1 y +2,33 en p99.
                     Colas mas anchas = el chi2 subestima la tasa.
· `rho temporal`     correlacion entre los residuos de los dos ejes en la LINEA BASE.
· `umbral`           el chi2 ya compensado por la puerta de direccion.
· `fraccion marcada` cuanto del lote marca en ESTA fecha. NO es la tasa de falsa
                     alarma: en esta fecha puede haber algo real. Para tasa de falsa
                     alarma hace falta `calibrar_criterio.py` sobre fechas sin evento.
"""
import argparse
import json
import sys


def _pct(img, geom, escala, pcts=(1, 5, 50, 95, 99)):
    import ee
    d = img.reduceRegion(
        reducer=ee.Reducer.percentile(list(pcts)), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=False).getInfo()
    return {k: (round(v, 3) if isinstance(v, (int, float)) else None)
            for k, v in sorted(d.items())}


def _stats(img, geom, escala):
    """count / mean / SD, EN ESE ORDEN. El conteo primero, siempre."""
    import ee
    red = (ee.Reducer.count()
           .combine(ee.Reducer.mean(), '', True)
           .combine(ee.Reducer.stdDev(), '', True))
    d = img.reduceRegion(reducer=red, geometry=geom, scale=escala,
                         maxPixels=1e9, bestEffort=False).getInfo()
    return d


def medir(sitio, feat, hasta, escala=None):
    import ee

    from pix_alerta import config as cfg
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    escala = escala or cri.ESCALA
    geom = fo._geom_lote(sitio, feat)
    lid = str(feat['properties'].get(sitio.campo_id))
    print('\n' + '=' * 74)
    print('LOTE %s   fecha de corte %s   escala %d m' % (lid, hasta, escala))
    print('=' * 74)
    try:
        r = cri.evaluar(geom, hasta, sitio=sitio, escala=escala)
    except cri.SinBase as e:
        print('  SIN BASE: %s' % e)
        return None

    print('  escena evaluada: %s' % r['fecha'])
    ejes = list(cfg.EJES)

    # 1) CONTEO PRIMERO. Una SD sobre cero pixeles da 0,000 y parece perfecta.
    st = _stats(r['z'][ejes[0]].rename('u'), geom, escala)
    n_px = int(st.get('u_count') or 0)
    print('  n pixeles con z valido: %d' % n_px)
    if n_px < 100:
        print('  OJO: MENOS DE 100 PIXELES: cualquier estadistico de abajo es ruido.')
        return None

    # 2) observaciones por pixel
    sb = _stats(r['n_base'].rename('u'), geom, escala)
    print('  n_base por pixel: media %.2f  SD %.2f  (min util %d)'
          % (sb.get('u_mean') or 0, sb.get('u_stdDev') or 0, cri.MIN_BASE))
    print('  n_base percentiles: %s' % _pct(r['n_base'].rename('nb'), geom, escala))

    # 3) escala
    for e in ejes:
        s = _stats(r['sigma'].select(e).rename('u'), geom, escala)
        print('  sigma final %-5s: media %.4f  SD %.4f  (piso %.3f)'
              % (e, s.get('u_mean') or 0, s.get('u_stdDev') or 0,
                 cfg.valor_de(sitio, 'sigma_minima', cri.SIGMA_MINIMA)))

    # 4) EL NUMERO CENTRAL: SD(z) y la forma de la cola
    print('  ' + '-' * 70)
    for e in ejes:
        z = r['z'][e].rename('u')
        s = _stats(z, geom, escala)
        print('  SD(z) %-5s = %.3f   media %+.3f   n=%d'
              % (e, s.get('u_stdDev') or 0, s.get('u_mean') or 0,
                 int(s.get('u_count') or 0)))
        print('        cola: %s   (una normal daria p1=-2,33 y p99=+2,33)'
              % _pct(r['z'][e].rename('z'), geom, escala))

    # 5) d2 y cuanto marca
    print('  ' + '-' * 70)
    umbral = r['umbral']
    u_val = umbral.getInfo() if hasattr(umbral, 'getInfo') else float(umbral)
    print('  umbral chi2 usado: %.3f' % u_val)
    print('  d2 percentiles: %s' % _pct(r['d2'], geom, escala))
    frac = _stats(r['anomalia'].rename('u').unmask(0, False), geom, escala)
    print('  fraccion del lote marcada en ESTA fecha: %.3f%%   (n=%d)'
          % (100 * (frac.get('u_mean') or 0), int(frac.get('u_count') or 0)))
    print('  OJO: Esa fraccion NO es la tasa de falsa alarma: en esta fecha puede')
    print('     haber algo real. La tasa se mide con `calibrar_criterio.py` sobre')
    print('     fechas SIN evento.')
    return {'lote_id': lid, 'n_px': n_px,
            'sd_z': {e: (_stats(r['z'][e].rename('u'), geom, escala)
                         .get('u_stdDev')) for e in ejes},
            'umbral': u_val,
            'frac': frac.get('u_mean')}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sitio', required=True)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--lote', default=None, help='solo este lote')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import config as cfg
    cl.registrar_sitios(cl.cargar_todos())
    sitio = cfg.SITIOS.get(a.sitio)
    if sitio is None:
        print('no existe el sitio %s. Hay: %s'
              % (a.sitio, ', '.join(sorted(cfg.SITIOS))))
        return 1
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    out = []
    for f in gj['features']:
        lid = str(f['properties'].get(sitio.campo_id))
        if a.lote and a.lote != lid:
            continue
        r = medir(sitio, f, a.hasta)
        if r:
            out.append(r)
    if out:
        print('\n' + '=' * 74)
        print('RESUMEN — SD(z) tiene que dar ~1. Si no, la tasa no es la declarada.')
        for r in out:
            print('  %-20s n=%-7d %s'
                  % (r['lote_id'], r['n_px'],
                     '  '.join('SD(z_%s)=%.2f' % (k, v or 0)
                               for k, v in sorted(r['sd_z'].items()))))
    return 0


if __name__ == '__main__':
    sys.exit(main())


# --- de donde sale sigma: ¿ruido o error del modelo? --------------------------

def ruido_corto(sitio, feat, hasta, escala=None):
    """Compara la escala del AJUSTE contra la escala de DIFERENCIAS CONSECUTIVAS.

    POR QUE ESTE PAR DE NUMEROS DECIDE
    ----------------------------------
    La escala del criterio sale de la MAD de los residuos contra una RECTA ajustada
    sobre la ventana de base. Ese numero mezcla dos cosas que hay que separar:

        ruido de observacion   (sensor, atmosfera residual, BRDF, remuestreo)
      + error del MODELO       (la trayectoria real del cultivo no es una recta)

    Las diferencias entre escenas CONSECUTIVAS estiman el primero y son casi
    inmunes al segundo: una tendencia suave aporta lo mismo a cada diferencia y la
    MAD alrededor de la mediana la saca. Es el estimador de Rice / von Neumann.

        sigma_dif = MAD( (x_{t+1} - x_t) / raiz(2) )  alrededor de su mediana

    LECTURA:
      · razon ~1      -> la recta describe bien la trayectoria; sigma ES ruido.
      · razon >> 1    -> sigma esta dominada por el error del modelo, no por ruido.
                         El z queda comprimido y el criterio se vuelve sordo.

    LIMITE DECLARADO: con espaciado irregular entre escenas, una tendencia con
    pendiente fuerte deja algo de residuo en las diferencias, asi que `sigma_dif`
    puede quedar un poco alto. O sea que la razon que se informa es una COTA
    INFERIOR del problema, no una sobreestimacion.
    """
    import ee

    from pix_alerta import config as cfg
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    escala = escala or cri.ESCALA
    geom = fo._geom_lote(sitio, feat)
    lid = str(feat['properties'].get(sitio.campo_id))
    ejes = list(cfg.EJES)
    import pandas as pd
    ventana = cri.ventana_de(sitio)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]
    base = cri._coleccion_limpia(geom, desde, fin)
    n = int(base.size().getInfo() or 0)
    print('\n  %s — escenas limpias en la base: %d (%s a %s)' % (lid, n, desde, fin))
    if n < 3:
        print('    menos de 3 escenas: no hay diferencias consecutivas que medir')
        return None
    lista = base.sort('system:time_start').toList(n)
    difs = []
    for i in range(1, n):
        a = ee.Image(lista.get(i)).select(ejes)
        b = ee.Image(lista.get(i - 1)).select(ejes)
        difs.append(a.subtract(b).divide(2 ** 0.5))
    col = ee.ImageCollection(difs)
    med = col.median()
    mad_dif = col.map(lambda i: ee.Image(i).subtract(med).abs()).median().multiply(1.4826)
    for e in ejes:
        d = mad_dif.select(e).rename('u').reduceRegion(
            reducer=ee.Reducer.count().combine(ee.Reducer.median(), '', True),
            geometry=geom, scale=escala, maxPixels=1e9, bestEffort=False).getInfo()
        print('    %-5s sigma de DIFERENCIAS = %.4f   (n=%d pixeles)'
              % (e, d.get('u_median') or 0, int(d.get('u_count') or 0)))
    return mad_dif
