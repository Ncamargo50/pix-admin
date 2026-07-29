# -*- coding: utf-8 -*-
"""¿Los focos que se entregan REAPARECEN en la escena siguiente? Es la prueba mas dura.

POR QUE ESTA ES LA MEDICION QUE MAS IMPORTA
-------------------------------------------
Un deterioro del cultivo no se mueve. Si un pedazo de lote esta afectado hoy, en la escena
limpia siguiente —cinco a diez dias despues— sigue estando afectado en el MISMO lugar. Una
mancha que aparece en un lado y a la semana aparece en otro no es una condicion del campo:
es ruido que paso el umbral.

Esta prueba **no necesita verdad de campo**. No dice si el foco es enfermedad o carencia:
dice si es una PROPIEDAD DEL LOTE o un sorteo. Y es una prueba que el motor puede FALLAR,
que es lo que la hace valer.

LO QUE APARECIO AL MEDIRLO POR PRIMERA VEZ
------------------------------------------
Sobre SANTO_ANTONIO-02, con las dos escenas limpias (calidad 0,929 y 0,926):

    2026-07-10   3 focos, 1,20 ha
    2026-07-15   1 foco,  0,44 ha    solape con los de la escena anterior: 0%

Y el solape de la mascara CRUDA entre escenas limpias consecutivas dio 0% y 18%.

Si eso se repite en toda la campana, significa que **lo que el motor marca no persiste**, y
convergeria con lo ya medido: la escala del criterio es 2,7 a 6,5 veces el ruido real, asi
que lo que pasa el umbral es la cola de una distribucion mal escalada.

LAS EXPLICACIONES POSIBLES, PARA NO SACAR LA CONCLUSION FACIL
------------------------------------------------------------
1. **El criterio detecta CAMBIO, no estado.** Un pixel que cayo entre t-1 y t se marca en
   t; si despues se queda abajo, ya no hay cambio nuevo. Pero la referencia es la
   TRAYECTORIA de 72 dias, no la escena anterior: una caida real sigue dando residuo
   negativo durante varias escenas hasta que la linea base la absorba. Con ~9
   observaciones eso no pasa en cinco dias. Asi que esta explicacion no alcanza.
2. **Pixeles marginales que parpadean.** Los que estan justo en el umbral cruzan de un
   lado al otro. Es la razon por la que se mide a nivel de FOCO —despues del filtro de
   mayoria y de la unidad minima— y no de pixel.
3. **Eventos realmente transitorios** (una helada que se recupera, un encharcado). Posible,
   pero no explica que tres focos se conviertan en uno en otro lugar.
4. **Que este marcando ruido.** Es lo que hay que poder descartar, y por eso se mide.

    python -m medicion.persistencia_focos --sitio SANTO_ANTONIO

COMO SE LEE
-----------
· Solape ALTO y sostenido -> lo que se marca es una propiedad del lote. El producto tiene
  sentido y ademas se puede etiquetar «confirmado».
· Solape cercano a CERO en pares de escenas LIMPIAS -> lo que se marca no persiste, y el
  producto esta mandando al tecnico a lugares que cambian entre imagenes.
· Se informa tambien el solape ESPERADO POR AZAR: dos conjuntos de manchas del mismo
  tamano tirados al azar en el lote se solapan en aproximadamente la fraccion que ocupan.
  Si el solape medido no supera claramente ese numero, no hay persistencia.
"""
import argparse
import json
import sys


def focos_en(sitio, feat, fecha, escala=None):
    """Focos usando `fecha` como si fuera hoy. Devuelve (geometria unida, ha, n, fecha)."""
    import ee
    import pandas as pd

    from pix_alerta import focos as fo
    corte = str(pd.Timestamp(fecha) + pd.Timedelta(days=1))[:10]
    r = fo.detectar_lote(sitio, feat, corte)
    if not r.get('fecha_img') or str(r['fecha_img'])[:10] != str(fecha)[:10]:
        return None
    if not r['focos']:
        return {'geom': None, 'ha': 0.0, 'n': 0, 'fecha': r['fecha_img'],
                'pct_util': r.get('pct_util')}
    g = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f['geometry'])) for f in r['focos']]).geometry()
    return {'geom': g, 'ha': r['area_focos_ha'], 'n': len(r['focos']),
            'fecha': r['fecha_img'], 'pct_util': r.get('pct_util')}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sitio', default='SANTO_ANTONIO')
    ap.add_argument('--fechas',
                    default='2026-05-31,2026-06-02,2026-06-05,2026-06-22,'
                            '2026-07-10,2026-07-15')
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
    fechas = [x.strip() for x in a.fechas.split(',') if x.strip()]

    for f in gj['features']:
        lid = str(f['properties'].get(sitio.campo_id))
        area_lote = float(f['properties'].get(sitio.campo_area) or 0)
        geom = fo._geom_lote(sitio, f)
        print('\n' + '=' * 78)
        print('%s   (%.1f ha declaradas)' % (lid, area_lote))
        print('=' * 78)
        print('  %-12s %7s %8s' % ('fecha', 'n focos', 'ha'))
        res = {}
        for fe in fechas:
            try:
                r = focos_en(sitio, f, fe)
            except Exception as e:                       # noqa: BLE001
                print('  %-12s AVERIA %s: %s' % (fe, type(e).__name__, str(e)[:50]))
                continue
            if r is None:
                print('  %-12s (esa fecha no se pudo evaluar)' % fe)
                continue
            res[fe] = r
            print('  %-12s %7d %8.2f' % (fe, r['n'], r['ha']))

        print('\n  PERSISTENCIA entre escenas consecutivas:')
        print('  %-24s %8s %10s %12s' % ('par', 'solape', 'por azar', 'veces el azar'))
        ordenadas = [x for x in fechas if x in res]
        for i in range(1, len(ordenadas)):
            hoy, antes = ordenadas[i], ordenadas[i - 1]
            rh, ra = res[hoy], res[antes]
            if rh['n'] == 0 or ra['n'] == 0:
                print('  %-24s %8s   (uno de los dos no tuvo focos)'
                      % ('%s vs %s' % (hoy[5:], antes[5:]), '-'))
                continue
            try:
                inter = rh['geom'].intersection(ra['geom'], 1).area(1).getInfo() / 1e4
            except Exception as e:                       # noqa: BLE001
                print('  %-24s AVERIA %s' % ('%s vs %s' % (hoy[5:], antes[5:]),
                                             str(e)[:40]))
                continue
            sol = inter / rh['ha'] if rh['ha'] else 0.0
            # Solape esperado si las manchas de hoy cayeran AL AZAR dentro del lote: es
            # la fraccion del lote que ocupaban las manchas de la escena anterior.
            azar = (ra['ha'] / area_lote) if area_lote else 0.0
            veces = (sol / azar) if azar > 0 else float('nan')
            print('  %-24s %7.0f%% %9.1f%% %11.1fx'
                  % ('%s vs %s' % (hoy[5:], antes[5:]), 100 * sol, 100 * azar, veces))
    print("""
COMO SE LEE
-----------
· `por azar` es la fraccion del lote que ocupaban los focos de la escena anterior: si los
  de hoy cayeran al azar, se solaparian aproximadamente en esa proporcion.
· `veces el azar` es lo que decide. Un valor cercano a 1 significa que los focos de hoy
  caen donde caerian tirandolos al azar: NO hay persistencia. Un valor de 10x o mas
  significa que vuelven al mismo lugar.
· OJO con el signo contrario: un solape muy alto tampoco es automaticamente bueno. Podria
  ser una zona estructural (un bajo, un cambio de suelo) que el criterio marca todas las
  semanas y que el productor ya conoce. Eso se separa con la capa de zonas, no con esta.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
