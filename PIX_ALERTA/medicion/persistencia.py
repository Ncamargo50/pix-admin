# -*- coding: utf-8 -*-
"""¿Sirve la PERSISTENCIA para separar la bruma del daño real?

LA IDEA
-------
Una anomalia del cultivo no aparece y desaparece: si un pedazo de lote se deterioro, en la
escena siguiente sigue deteriorado. Una bruma, en cambio, esta en UNA imagen y no en la
otra. Entonces:

    marcado en la escena de hoy Y TAMBIEN en la escena limpia anterior  ->  persistente
    marcado SOLO en la escena de hoy                                    ->  sin confirmar

EL PROBLEMA QUE ESTO NO RESUELVE, Y HAY QUE DECIRLO DE ENTRADA
--------------------------------------------------------------
Un evento REAL Y NUEVO tambien aparece solo en la escena de hoy. Asi que la persistencia
**no distingue bruma de evento nuevo**: distingue *confirmado* de *sin confirmar*. Usarla
como filtro duro convertiria el motor en un detector de anomalias viejas y le agregaria un
retraso de una imagen —5 a 10 dias— a TODA alerta real.

Por eso lo que se mide aca es si la persistencia sirve como **etiqueta** («confirmado» /
«a confirmar»), no como filtro.

EL CASO CONOCIDO CONTRA EL QUE SE PRUEBA
----------------------------------------
    2026-07-05  bruma medida: el NDVI del lote cayo 0,15 y volvio en la escena siguiente.
                Con el filtro binario de nube paso, y en SANTO_ANTONIO-02 marco 1,86%.
    2026-07-15  escena limpia: 1 foco de 0,44 ha, el que se le reporto al cliente.

Si la regla sirve, lo marcado el 07-05 NO deberia solaparse con lo marcado en la escena
limpia anterior, y el foco del 07-15 SI deberia estar tambien el 07-10.

    python -m medicion.persistencia --sitio SANTO_ANTONIO

⚠️ La escena del 07-05 hoy la rechaza la puerta de calidad (`CS_MEDIO_MINIMO`). Para poder
medirla, este arnes BAJA ese piso a proposito y lo dice en la salida. No se toca produccion.
"""
import argparse
import json
import sys


def _escenas_limpias(sitio, geom, hasta, cri, n=3):
    """Las ultimas `n` fechas que el criterio aceptaria, mas reciente primero."""
    import pandas as pd
    fechas, corte = [], str(hasta)
    for _ in range(n + 2):
        try:
            r = cri.evaluar(geom, corte, sitio=sitio)
        except cri.SinBase:
            break
        except Exception:                                # noqa: BLE001
            break
        f = str(r['fecha'])[:10]
        if f in fechas:
            break
        fechas.append(f)
        corte = str(pd.Timestamp(f))[:10]                # excluye esa fecha y anteriores
        if len(fechas) >= n:
            break
    return fechas


def anomalia_en(sitio, geom, fecha, cri, escala=None):
    """Mascara de anomalia usando `fecha` como si fuera hoy, y su fraccion."""
    import ee
    import pandas as pd
    escala = escala or cri.ESCALA
    corte = str(pd.Timestamp(fecha) + pd.Timedelta(days=1))[:10]
    r = cri.evaluar(geom, corte, sitio=sitio, escala=escala)
    if str(r['fecha'])[:10] != str(fecha)[:10]:
        return None
    m = r['anomalia'].rename('a')
    red = ee.Reducer.count().combine(ee.Reducer.mean(), '', True)
    d = m.unmask(0, False).reduceRegion(
        reducer=red, geometry=geom, scale=escala, maxPixels=1e9,
        bestEffort=False).getInfo()
    q = r.get('cs_medio')
    q = q.getInfo() if hasattr(q, 'getInfo') else q
    return {'mascara': m, 'frac': d.get('a_mean') or 0.0,
            'n_px': int(d.get('a_count') or 0), 'cs_medio': q}


def solape(m_hoy, m_antes, geom, escala):
    """Que fraccion de lo marcado HOY tambien estaba marcado ANTES."""
    import ee
    hoy = m_hoy.unmask(0, False)
    antes = m_antes.unmask(0, False)
    d = (hoy.rename('h').addBands(hoy.And(antes).rename('i'))
         .reduceRegion(reducer=ee.Reducer.sum(), geometry=geom, scale=escala,
                       maxPixels=1e9, bestEffort=False).getInfo())
    h, i = (d.get('h') or 0), (d.get('i') or 0)
    return (i / h) if h else None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sitio', default='SANTO_ANTONIO')
    ap.add_argument('--fechas', default='2026-07-05,2026-07-10,2026-07-15')
    ap.add_argument('--piso-calidad', type=float, default=0.50,
                    help='se BAJA a proposito para poder medir la escena con bruma')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import config as cfg
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    cl.registrar_sitios(cl.cargar_todos())
    sitio = cfg.SITIOS.get(a.sitio)
    if sitio is None:
        print('no existe el sitio %s' % a.sitio)
        return 1

    print('OJO: se baja el piso de calidad de escena de %.2f a %.2f SOLO en este arnes, '
          'para poder\n     medir la escena con bruma que produccion ya rechaza.'
          % (cfg.CS_MEDIO_MINIMO, a.piso_calidad))
    cfg.CS_MEDIO_MINIMO = a.piso_calidad

    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    fechas = [x.strip() for x in a.fechas.split(',') if x.strip()]

    for f in gj['features']:
        lid = str(f['properties'].get(sitio.campo_id))
        geom = fo._geom_lote(sitio, f)
        print('\n' + '=' * 78)
        print('%s' % lid)
        print('=' * 78)
        cache = {}
        for fe in fechas:
            try:
                cache[fe] = anomalia_en(sitio, geom, fe, cri)
            except cri.SinBase as e:
                print('  %s  sin escena utilizable: %s' % (fe, str(e)[:60]))
                cache[fe] = None
            except Exception as e:                       # noqa: BLE001
                print('  %s  AVERIA %s: %s' % (fe, type(e).__name__, str(e)[:60]))
                cache[fe] = None
        print('  %-12s %9s %8s %10s' % ('fecha', 'calidad', 'marcado', 'n px'))
        for fe in fechas:
            r = cache.get(fe)
            if r is None:
                print('  %-12s %9s %8s %10s' % (fe, '-', '-', '-'))
                continue
            print('  %-12s %9.3f %7.2f%% %10d'
                  % (fe, r['cs_medio'] if r['cs_medio'] is not None else -1,
                     100 * r['frac'], r['n_px']))

        # --- la medicion que decide: solape con la escena limpia ANTERIOR ----
        print('\n  SOLAPE de lo marcado con la escena limpia anterior:')
        for i in range(1, len(fechas)):
            hoy, antes = fechas[i], fechas[i - 1]
            rh, ra = cache.get(hoy), cache.get(antes)
            if not rh or not ra:
                continue
            if rh['frac'] <= 0:
                print('    %s: no marco nada, no hay nada que confirmar' % hoy)
                continue
            s = solape(rh['mascara'], ra['mascara'], geom, cri.ESCALA)
            print('    %s contra %s -> %s de lo marcado hoy tambien estaba antes'
                  % (hoy, antes,
                     ('%.0f%%' % (100 * s)) if s is not None else 'sin dato'))
    print("""
COMO SE LEE
-----------
· Si lo marcado en la fecha con BRUMA tiene solape BAJO con la escena limpia anterior, y
  lo marcado en la fecha LIMPIA tiene solape ALTO, la persistencia sirve como etiqueta.
· Si los dos dan parecido, no sirve: no separa bruma de daño.
· Un solape bajo NO prueba bruma. Tambien lo da un evento real y nuevo. Por eso esto
  etiqueta «a confirmar», no «descartado».""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
