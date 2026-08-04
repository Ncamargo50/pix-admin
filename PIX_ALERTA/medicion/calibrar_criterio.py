# -*- coding: utf-8 -*-
"""Tasa de marcado del criterio sobre fechas SIN evento conocido. EL arnés que decide.

POR QUE ESTE ARCHIVO SE ESCRIBIO EL 2026-07-29, Y ES UN HALLAZGO DE AUDITORIA
-----------------------------------------------------------------------------
`criterio.py`, `focos.py` y `config.py` lo citaban como la evidencia que aprobo el
criterio v2 a produccion, con esta tabla en el docstring del modulo:

    lote                v1 mediana   v1 MAXIMO    v2 mediana   v2 MAXIMO
    SANTO_ANTONIO-01       2,11%       9,84%        0,00%       2,17%
    ...

**El archivo nunca existio en el repositorio.** No esta en el historial de git ni en
`.gitignore`. O sea que esos numeros —los que justificaron poner v2 en produccion— no
se podian reproducir. Este arnes los vuelve a poner al alcance.

QUE MIDE, Y QUE NO
------------------
Recorre las escenas limpias de cada lote y usa CADA UNA como si fuera "hoy",
calculando el criterio con las anteriores como linea base. Devuelve que fraccion del
lote marca en cada una.

⚠️ LIMITE QUE HAY QUE DECLARAR: no hay verdad de campo, asi que no se puede afirmar
que esas fechas esten libres de eventos. Lo que se puede decir es:

  · la MEDIANA sobre muchas fechas es un proxy razonable de la tasa de falsa alarma,
    porque la mayoria de las fechas de una campaña normal no tienen evento;
  · el MAXIMO es una COTA SUPERIOR que puede incluir eventos reales, no solo falsas
    alarmas.

Por eso se informan las dos y no un numero solo. Y por eso esto NO reemplaza al mapa
de rendimiento de la cosecha, que sigue siendo la unica validacion que cierra.

    python -m medicion.calibrar_criterio --cliente TRIGO --hasta 2026-07-16
    python -m medicion.calibrar_criterio --cliente TRIGO --hasta 2026-07-16 \\
        --modelos recta,relativa_agrupada

COMO SE LEE EL RESULTADO
------------------------
El criterio declara alfa = 1%. Si la mediana esta muy por encima, marca de mas. Si da
0,00% en todas las fechas, hay que sospechar SORDERA y no buena calibracion: mirar
SD(z) con `medicion/verificar_escala_real.py`. Un criterio que no marca nunca tiene
tasa de falsa alarma perfecta y no sirve para nada.
"""
import argparse
import json
import sys


def fechas_limpias(sitio, geom, hasta, cri):
    """Fechas con escena utilizable en la ventana de base, mas antigua primero."""
    import pandas as pd
    ventana = cri.ventana_de(sitio)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) + pd.Timedelta(days=1))[:10]
    col = cri._coleccion_limpia(geom, desde, fin)
    n = int(col.size().getInfo() or 0)
    if not n:
        return []
    return sorted(set(col.aggregate_array('fecha').getInfo() or []))


def tasa_en_fecha(sitio, geom, fecha, cri, modelo, escala, ajuste=None):
    """Fraccion del lote marcada usando `fecha` como si fuera hoy.

    Devuelve (fraccion, n_pixeles, n_base) o None si esa fecha no es evaluable.
    El conteo de pixeles viaja SIEMPRE con la fraccion: una fraccion calculada sobre
    cero pixeles da 0,000 y parece el mejor resultado posible.
    """
    import ee
    import pandas as pd
    corte = str(pd.Timestamp(fecha) + pd.Timedelta(days=1))[:10]
    try:
        r = cri.evaluar(geom, corte, sitio=sitio, escala=escala, modelo=modelo,
                        ajuste=ajuste)
    except cri.SinBase:
        return None
    except Exception as exc:                      # noqa: BLE001
        return ('averia', '%s: %s' % (type(exc).__name__, str(exc)[:70]), None)
    if str(r['fecha'])[:10] != str(fecha)[:10]:
        # La escena elegida no es la pedida: esta fecha no aporta un punto limpio.
        return None
    red = ee.Reducer.count().combine(ee.Reducer.mean(), '', True)
    d = (r['anomalia'].rename('u').unmask(0, False)
         .reduceRegion(reducer=red, geometry=geom, scale=escala,
                       maxPixels=1e9, bestEffort=False).getInfo())
    nb = (r['n_base'].rename('u').reduceRegion(
        reducer=ee.Reducer.mean(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=False).getInfo())
    n_px = int(d.get('u_count') or 0)
    if n_px < 100:
        return None
    return (float(d.get('u_mean') or 0.0), n_px, nb.get('u'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cliente', default='TRIGO')
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--modelos', default=None,
                    help='coma-separados. Por defecto, todos los de criterio.MODELOS')
    ap.add_argument('--escala', type=int, default=None)
    ap.add_argument('--ejes', default=None,
                    help='par de ejes a medir, coma-separado (ej. NDMI,CIRE). '
                         'Por defecto, los de config.EJES.')
    ap.add_argument('--ajuste', default=None,
                    help="como se ajusta la trayectoria: 'mco' (produccion) o "
                         "'theilsen' (robusto). Por defecto, criterio.AJUSTE.")
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1
    modelos = ([m.strip() for m in a.modelos.split(',') if m.strip()]
               if a.modelos else list(cri.MODELOS))
    # EJES A MEDIR. Cambiar el par es una decision de produccion, asi que tiene que
    # poder MEDIRSE antes de tomarla: `config.EJES` se pisa para toda la corrida del
    # arnes y se declara en el encabezado, para que ningun resultado quede sin decir
    # sobre que par se midio.
    from pix_alerta import config as cfg
    if a.ejes:
        nuevos = tuple(x.strip().upper() for x in a.ejes.split(',') if x.strip())
        from pix_alerta.ranking import SIGNO
        faltan = [e for e in nuevos if e not in SIGNO]
        if faltan:
            print('ranking.SIGNO no declara el sentido de alarma de %s. Sin eso el '
                  'criterio podria marcar los pixeles SANOS.' % faltan)
            return 1
        cfg.EJES = nuevos
    print('EJES medidos: %s' % ' + '.join(cfg.EJES))
    escala = a.escala or cri.ESCALA
    ajuste = a.ajuste or cri.AJUSTE
    if ajuste not in cri.AJUSTES:
        print('ajuste desconocido: %r. Hay: %s' % (ajuste, cri.AJUSTES))
        return 1
    print('alfa declarada por el criterio: %.1f%%   modelos: %s   escala: %d m'
          % (100 * cri.ALFA, ', '.join(modelos), escala))
    print('AJUSTE de trayectoria: %s%s'
          % (ajuste, '   <- NO es el de produccion' if ajuste != cri.AJUSTE else ''))

    resumen = {}
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            geom = fo._geom_lote(s, f)
            fechas = fechas_limpias(s, geom, a.hasta, cri)
            print('\n%s — %d fecha(s) limpia(s): %s'
                  % (lid, len(fechas), ', '.join(x[5:] for x in fechas)))
            for modelo in modelos:
                tasas, detalle = [], []
                for fe in fechas:
                    r = tasa_en_fecha(s, geom, fe, cri, modelo, escala, ajuste)
                    if r is None:
                        continue
                    if r[0] == 'averia':
                        detalle.append('%s AVERIA' % fe[5:])
                        print('    %-18s %s -> %s' % (modelo, fe[5:], r[1]))
                        continue
                    frac, n_px, nb = r
                    tasas.append(frac)
                    detalle.append('%s %.2f%%' % (fe[5:], 100 * frac))
                if not tasas:
                    print('    %-18s sin fechas evaluables' % modelo)
                    continue
                ts = sorted(tasas)
                med = ts[len(ts) // 2]
                print('    %-18s n=%d fechas | MEDIANA %.2f%% | MAXIMO %.2f%% | %s'
                      % (modelo, len(ts), 100 * med, 100 * ts[-1],
                         '  '.join(detalle)))
                resumen.setdefault(modelo, []).append(
                    {'lote': lid, 'n': len(ts), 'mediana': med, 'maximo': ts[-1]})

    print('\n' + '=' * 78)
    print('RESUMEN — alfa declarada %.1f%%' % (100 * cri.ALFA))
    print('%-20s %-20s %5s %10s %10s' % ('modelo', 'lote', 'n', 'MEDIANA', 'MAXIMO'))
    print('-' * 70)
    for modelo, filas in sorted(resumen.items()):
        for r in filas:
            print('%-20s %-20s %5d %9.2f%% %9.2f%%'
                  % (modelo, r['lote'], r['n'], 100 * r['mediana'],
                     100 * r['maximo']))
        peor = max(r['maximo'] for r in filas)
        medm = max(r['mediana'] for r in filas)
        print('%-20s %-20s %5s %9.2f%% %9.2f%%   <- peor lote'
              % ('', '(peor de los lotes)', '', 100 * medm, 100 * peor))
    print("""
OJO AL LEER:
· El MAXIMO puede incluir eventos REALES: no hay verdad de campo para descartarlos.
  Es una cota superior de la falsa alarma, no la falsa alarma.
· Una MEDIANA de 0,00% en todas las fechas NO es un buen resultado por si sola:
  puede ser sordera. Cruzarlo con SD(z) de `medicion/verificar_escala_real.py`.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
