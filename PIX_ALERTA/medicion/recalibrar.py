# -*- coding: utf-8 -*-
"""Recalibrar el umbral del criterio por TASA EMPIRICA, y decidir con qué queda mejor.

POR QUE HAY QUE RECALIBRAR Y NO ALCANZA EL chi2
-----------------------------------------------
El umbral del criterio sale del cuantil de una chi2 con 2 grados de libertad, que supone
SD(z) = 1. Eso NO se cumple. Medido sobre los 4 lotes reales
(`medicion/comparar_trayectoria.py`):

    modelo               razon sigma/ruido   mediana(z)   SD(z) y su rango
    recta (produccion)       3,3 y 5,0       -0,85       0,50  (0,19 a 1,30)
    relativa_agrupada        1,1 y 1,4       -0,01       1,23  (0,86 a 1,54)

El candidato arregla las tripas —la escala pasa a medir ruido y el sesgo desaparece— pero
con SD(z) = 1,2 el cuantil chi2 infla la cola y marca 3 a 4 veces mas. Por eso antes se
dejo APAGADO: no se enciende algo que empeora el unico numero que se le entrega al cliente.

La salida no es volver al chi2: es fijar el umbral por la TASA EMPIRICA sobre fechas sin
evento, que es el estandar que este proyecto ya adopto y esta escrito en
`feedback_calibrar_por_tasa_no_por_SD`.

LO QUE ESTE ARNES HACE, EN DOS PASOS
------------------------------------
PASO 1 — CALIBRAR. Para cada modelo, barre umbrales de d2 y mide la fraccion marcada en
cada fecha sin evento de cada lote. Devuelve el umbral que iguala la tasa objetivo. El
barrido es barato: d2 se calcula UNA vez por lote y fecha, y todos los umbrales se evaluan
en la misma pasada.

PASO 2 — DECIDIR, y esta es la parte que importa. Igualar la tasa de falsa alarma no
alcanza: si los dos criterios marcan lo mismo, cambiar no compra nada. Hay que ver cual
marca COSAS MEJORES a igual tasa. Sin verdad de campo la unica medida disponible es la
PERSISTENCIA: un criterio que marca condiciones reales del lote marca cosas que siguen ahi
en la escena siguiente; uno que marca ruido, no.

    persistencia = fraccion de lo marcado hoy que TAMBIEN estaba marcado en la escena
                   limpia anterior, dividida por lo que daria el azar

Es una medida que el criterio puede FALLAR, y por eso vale.

⚠️ LIMITE DECLARADO: las fechas de la linea base no estan garantizadas libres de eventos.
La MEDIANA sobre muchas fechas es un proxy razonable de la tasa de falsa alarma; el MAXIMO
es una cota superior que puede incluir eventos reales.

    python -m medicion.recalibrar --cliente TRIGO --hasta 2026-07-16
"""
import argparse
import json
import sys

# Umbrales de d2 a barrer. Se cubre desde bastante por debajo del chi2 al 5% (5,99) hasta
# bien por encima del chi2 al 1% (9,21), para que el objetivo caiga adentro sea cual sea
# la escala real del z.
UMBRALES = (4.0, 5.0, 6.0, 7.0, 8.0, 9.21, 11.0, 13.0, 15.0, 18.0, 22.0, 27.0)


def tasas_en_fecha(sitio, geom, fecha, modelo, cri, escala, umbrales=UMBRALES):
    """Fraccion marcada para TODOS los umbrales, en una sola pasada de GEE."""
    import ee
    import pandas as pd
    corte = str(pd.Timestamp(fecha) + pd.Timedelta(days=1))[:10]
    try:
        r = cri.evaluar(geom, corte, sitio=sitio, escala=escala, modelo=modelo)
    except cri.SinBase:
        return None
    if str(r['fecha'])[:10] != str(fecha)[:10]:
        return None
    d2, direc = r['d2'], r['direccion']
    # una banda por umbral: la reduccion se hace una sola vez
    img = None
    for u in umbrales:
        b = (d2.gte(u).And(direc).And(r['n_base'].gte(cri.MIN_BASE))
             .rename('u%d' % int(round(u * 100))).unmask(0, False))
        img = b if img is None else img.addBands(b)
    d = img.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
                         maxPixels=1e9, bestEffort=False).getInfo()
    return {u: d.get('u%d' % int(round(u * 100))) for u in umbrales}


def persistencia_en(sitio, feat, fecha, modelo, umbral, cri, escala):
    """Persistencia de lo marcado hoy contra la escena limpia anterior, y el azar."""
    import ee
    import pandas as pd

    from pix_alerta import focos as fo
    geom = fo._geom_lote(sitio, feat)
    corte = str(pd.Timestamp(fecha) + pd.Timedelta(days=1))[:10]
    try:
        hoy = cri.evaluar(geom, corte, sitio=sitio, escala=escala, modelo=modelo,
                          umbral=umbral)
        antes = cri.evaluar(geom, str(pd.Timestamp(fecha) - pd.Timedelta(days=1))[:10],
                            sitio=sitio, escala=escala, modelo=modelo, umbral=umbral)
    except cri.SinBase:
        return None
    if str(hoy['fecha'])[:10] != str(fecha)[:10]:
        return None
    if str(antes['fecha'])[:10] >= str(fecha)[:10]:
        return None
    mh = hoy['anomalia'].unmask(0, False)
    ma = antes['anomalia'].unmask(0, False)
    d = (mh.rename('h').addBands(mh.And(ma).rename('i')).addBands(ma.rename('a'))
         .reduceRegion(reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
                       maxPixels=1e9, bestEffort=False).getInfo())
    h, i, azar = (d.get('h') or 0), (d.get('i') or 0), (d.get('a') or 0)
    if h <= 0:
        return None
    sol = i / h
    return {'frac_hoy': h, 'solape': sol, 'azar': azar,
            'veces': (sol / azar) if azar > 0 else None,
            'fecha_anterior': str(antes['fecha'])[:10]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cliente', default='TRIGO')
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--sitio', default=None,
                    help='un solo sitio, para que la corrida entre en el tiempo')
    ap.add_argument('--paso', type=int, default=0, choices=(0, 1, 2),
                    help='1 = solo el barrido de umbrales, 2 = solo la persistencia')
    ap.add_argument('--umbrales', default=None, help='coma-separados, para el paso 2')
    ap.add_argument('--fechas-persistencia', type=int, default=2)
    ap.add_argument('--objetivo', type=float, default=None,
                    help='mediana objetivo. Por defecto, la que da el modelo recta.')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    from medicion.calibrar_criterio import fechas_limpias
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1
    escala = cri.ESCALA
    lotes = []
    for s in cliente.sitios:
        if a.sitio and s.clave != a.sitio:
            continue
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lotes.append((s, f, str(f['properties'].get(s.campo_id))))

    # ---------------- PASO 1: barrido de umbrales -------------------------
    print('\n' + '=' * 80)
    print('PASO 1 — TASA sobre fechas sin evento, por umbral de d2')
    print('=' * 80)
    crudo = {}
    if a.paso == 2:
        pares = [x.strip() for x in (a.umbrales or '').split(',') if x.strip()]
        elegido = {m: float(u) for m, u in zip(cri.MODELOS, pares)}
        print('PASO 2 con los umbrales calibrados en el paso 1: %s' % elegido)
        _paso2(cri, fo, lotes, elegido, escala, a, fechas_limpias, {})
        return 0
    for modelo in cri.MODELOS:
        crudo[modelo] = {}
        for s, f, lid in lotes:
            geom = fo._geom_lote(s, f)
            fechas = fechas_limpias(s, geom, a.hasta, cri)
            filas = []
            for fe in fechas:
                try:
                    t = tasas_en_fecha(s, geom, fe, modelo, cri, escala)
                except Exception as exc:                 # noqa: BLE001
                    print('  %-18s %-18s %s AVERIA %s'
                          % (lid, modelo, fe, str(exc)[:40]))
                    continue
                if t:
                    filas.append(t)
            crudo[modelo][lid] = filas
            print('  %-18s %-18s %d fecha(s) evaluada(s)' % (lid, modelo, len(filas)))

    def resumen(modelo, u):
        med, mx = [], []
        for lid, filas in crudo[modelo].items():
            v = sorted((x.get(u) or 0.0) for x in filas)
            if not v:
                continue
            med.append(v[len(v) // 2])
            mx.append(v[-1])
        return (max(med) if med else None), (max(mx) if mx else None)

    print('\n%-20s %8s %12s %12s' % ('modelo', 'umbral', 'MEDIANA peor', 'MAXIMO peor'))
    print('-' * 56)
    tabla = {}
    for modelo in cri.MODELOS:
        for u in UMBRALES:
            m, x = resumen(modelo, u)
            if m is None:
                continue
            tabla[(modelo, u)] = (m, x)
            marca = ' <- chi2 al 1%' if abs(u - 9.21) < 0.01 else ''
            print('%-20s %8.2f %11.2f%% %11.2f%%%s'
                  % (modelo, u, 100 * m, 100 * x, marca))
        print()

    # objetivo: la mediana que da hoy produccion con su umbral actual
    base = tabla.get(('recta', 9.21))
    objetivo = a.objetivo if a.objetivo is not None else (base[0] if base else 0.01)
    print('OBJETIVO de mediana (peor lote): %.2f%%  %s'
          % (100 * objetivo,
             '(la que da hoy produccion)' if a.objetivo is None else '(pedido)'))

    elegido = {}
    for modelo in cri.MODELOS:
        cand = [(u, v) for (m, u), v in tabla.items() if m == modelo]
        cand.sort()
        # el umbral MAS BAJO que ya cumple el objetivo: el mas bajo que cumple es el mas
        # sensible, y bajar mas seria pasarse de la tasa acordada.
        ok = [u for u, (med, _mx) in cand if med <= objetivo]
        elegido[modelo] = min(ok) if ok else None
        if elegido[modelo] is None:
            print('  %-20s ningun umbral del barrido llega al objetivo' % modelo)
        else:
            med, mx = tabla[(modelo, elegido[modelo])]
            print('  %-20s umbral %.2f -> mediana %.2f%%  maximo %.2f%%'
                  % (modelo, elegido[modelo], 100 * med, 100 * mx))

    if a.paso == 1:
        print('\n(paso 1 solamente. Para el paso 2:  --paso 2 --umbrales %s)'
              % ','.join(('%.2f' % elegido[m]) if elegido.get(m) else '9.21'
                         for m in cri.MODELOS))
        return 0
    _paso2(cri, fo, lotes, elegido, escala, a, fechas_limpias, tabla)
    return 0


def _paso2(cri, fo, lotes, elegido, escala, a, fechas_limpias, tabla):
    # ---------------- PASO 2: persistencia a tasa igualada ----------------
    print('\n' + '=' * 80)
    print('PASO 2 — A IGUAL TASA, ¿cual marca cosas que PERSISTEN?')
    print('=' * 80)
    print('Sin verdad de campo, la persistencia es la unica medida de calidad: lo que es')
    print('del lote sigue ahi la semana siguiente; el ruido se mueve.\n')
    print('%-20s %-18s %-12s %8s %8s %9s'
          % ('modelo', 'lote', 'fecha', 'marcado', 'azar', 'veces azar'))
    print('-' * 80)
    resu = {}
    for modelo in cri.MODELOS:
        u = elegido.get(modelo)
        if u is None:
            continue
        vals = []
        for s, f, lid in lotes:
            geom = fo._geom_lote(s, f)
            for fe in fechas_limpias(s, geom, a.hasta, cri)[-a.fechas_persistencia:]:
                try:
                    r = persistencia_en(s, f, fe, modelo, u, cri, escala)
                except Exception as exc:                 # noqa: BLE001
                    continue
                if not r:
                    continue
                vals.append(r['veces'])
                print('%-20s %-18s %-12s %7.2f%% %7.2f%% %8s'
                      % (modelo, lid, fe, 100 * r['frac_hoy'], 100 * r['azar'],
                         ('%.1fx' % r['veces']) if r['veces'] else '-'))
        v = [x for x in vals if x]
        resu[modelo] = (sum(v) / len(v), len(v)) if v else (None, 0)

    print('\n' + '=' * 80)
    print('VEREDICTO')
    print('=' * 80)
    for modelo in cri.MODELOS:
        u = elegido.get(modelo)
        med = tabla.get((modelo, u), (None, None))[0] if u else None
        p, n = resu.get(modelo, (None, 0))
        print('  %-20s umbral %s  mediana %s  persistencia media %s  (n=%d)'
              % (modelo,
                 ('%.2f' % u) if u else '-',
                 ('%.2f%%' % (100 * med)) if med is not None else '-',
                 ('%.1fx el azar' % p) if p else '-', n))
    print("""
COMO SE DECIDE
--------------
Se cambia de modelo SOLO si, con la tasa de falsa alarma IGUALADA, el candidato marca
cosas mas persistentes. Si empatan, no hay razon positiva para cambiar y se queda el que
esta — cambiar un parametro de produccion sin ganancia medida es riesgo gratis.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
