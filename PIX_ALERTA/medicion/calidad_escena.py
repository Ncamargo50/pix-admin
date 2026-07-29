# -*- coding: utf-8 -*-
"""¿Se puede detectar la BRUMA con el puntaje de nube usado como NUMERO?

EL CASO QUE HAY QUE ATRAPAR, Y QUE YA CONOCEMOS
-----------------------------------------------
La escena del 2026-07-05 hizo que SANTO_ANTONIO-01 pareciera derrumbarse: su NDVI paso de
0,928 (06-22) a 0,776 (07-05) y volvio a 0,928 (07-10). Un trigo no hace eso. Era bruma
que sobrevivio a la mascara.

Y sobrevivio a TODO lo que hay hoy:
  · a la mascara de SCL con dilatacion de 80 m,
  · a CloudScore+ con umbral 0,60 aplicado pixel por pixel,
  · a la puerta de cobertura del 70% sobre el lote,
  · y a la conjuncion de dos ejes — porque la bruma baja los dos indices JUNTOS.

Es el mismo modo de falla que produjo los 3 focos de julio que se le reportaron al cliente
y que eran borde de nube.

LA IDEA QUE SE PONE A PRUEBA
----------------------------
Hoy CloudScore+ se usa como DECISION BINARIA: cada pixel pasa o no pasa el umbral 0,60.
Un pixel con bruma leve puede sacar 0,62 y pasar. Si TODO el lote esta con bruma leve,
todos los pixeles pasan y la escena entra como si estuviera limpia.

Pero el puntaje sigue siendo mas bajo que en una escena realmente limpia. Entonces el
**PROMEDIO del puntaje sobre el lote** deberia servir como "calidad de la escena", incluso
cuando el filtro binario no descarta nada.

    python -m medicion.calidad_escena --sitio SANTO_ANTONIO

QUE SE MIDE POR CADA FECHA
--------------------------
  cs_medio     promedio de `cs_cdf` sobre el lote, SIN enmascarar. Es el candidato.
  cs_p10       el decil peor. Una bruma parcial baja esto antes que el promedio.
  frac_pasa    fraccion de pixeles que superan el umbral actual (0,60). Es lo que hoy
               decide, y sirve para mostrar que NO alcanza.
  cob_scl      fraccion valida segun la mascara completa (SCL dilatada + CS+).
  NDVI         para ver la caida junto con la calidad.

COMO SE DECIDE SI LA IDEA SIRVE
-------------------------------
Se fija ANTES de mirar: la idea sirve si `cs_medio` del 2026-07-05 queda **por debajo** de
todas las fechas que sabemos limpias (06-22, 07-10, 07-15), con un margen que se pueda
convertir en umbral. Si queda en el medio, no sirve y hay que ir a la verificacion
temporal.
"""
import argparse
import json
import sys

CS = 'GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED'
# Fechas del caso conocido, para rotularlas en la salida y no confundirse al leer.
CONOCIDAS = {'2026-07-05': 'ARTEFACTO (el campo "se derrumbo" y volvio)',
             '2026-06-22': 'limpia',
             '2026-07-10': 'limpia',
             '2026-07-15': 'limpia (la que usa el motor)'}


def medir(sitio, feat, ini, fin, escala=20):
    """Calidad de escena por fecha sobre UN lote."""
    import ee

    from pix_alerta import config as cfg
    from pix_alerta import focos as fo
    from pix_alerta import series as sr
    geom = fo._geom_lote(sitio, feat)
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterDate(ini, fin).filterBounds(geom).sort('system:time_start'))
    n = int(col.size().getInfo() or 0)
    lista = col.toList(n)
    out = []
    for i in range(n):
        img = ee.Image(lista.get(i))
        cs = sr._cloudscore(img)
        if cs.getInfo() is None:
            continue
        cs = ee.Image(cs).select(cfg.CS_BANDA)
        # SIN enmascarar: se quiere el puntaje crudo sobre todo el lote.
        red = (ee.Reducer.mean().combine(ee.Reducer.percentile([10]), '', True)
               .combine(ee.Reducer.count(), '', True))
        d = cs.rename('cs').reduceRegion(
            reducer=red, geometry=geom, scale=escala, maxPixels=1e9,
            bestEffort=False).getInfo()
        n_px = int(d.get('cs_count') or 0)
        if n_px < 100:
            continue
        pasa = (cs.gte(cfg.CS_UMBRAL).rename('p').reduceRegion(
            ee.Reducer.mean(), geom, escala, maxPixels=int(1e9),
            bestEffort=False).get('p').getInfo())
        cob = (sr._mascara(img).rename('u').unmask(0, False).reduceRegion(
            ee.Reducer.mean(), geom, escala, maxPixels=int(1e9),
            bestEffort=False).get('u').getInfo())
        ndvi = (sr._indices(img).select('NDVI').updateMask(sr._mascara(img))
                .rename('v').reduceRegion(
                    ee.Reducer.median(), geom, escala, maxPixels=int(1e9),
                    bestEffort=False).get('v').getInfo())
        out.append({
            'fecha': ee.Date(img.get('system:time_start'))
                     .format('YYYY-MM-dd').getInfo(),
            'cs_medio': d.get('cs_mean'), 'cs_p10': d.get('cs_p10'),
            'frac_pasa': pasa, 'cob_scl': cob, 'ndvi': ndvi, 'n_px': n_px})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sitio', default='SANTO_ANTONIO')
    ap.add_argument('--desde', default='2026-05-01')
    ap.add_argument('--hasta', default='2026-07-20')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    from pix_alerta import config as cfg
    cl.registrar_sitios(cl.cargar_todos())
    sitio = cfg.SITIOS.get(a.sitio)
    if sitio is None:
        print('no existe el sitio %s' % a.sitio)
        return 1
    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    print('umbral de CloudScore+ en produccion: %.2f  (banda %s)'
          % (cfg.CS_UMBRAL, cfg.CS_BANDA))

    todo = {}
    for f in gj['features']:
        lid = str(f['properties'].get(sitio.campo_id))
        filas = medir(sitio, f, a.desde, a.hasta)
        todo[lid] = filas
        print('\n%s — %d fecha(s) con CloudScore+' % (lid, len(filas)))
        print('%-12s %9s %9s %10s %9s %8s  %s'
              % ('fecha', 'cs_medio', 'cs_p10', 'frac_pasa', 'cob_scl', 'NDVI', 'nota'))
        print('-' * 84)
        for r in filas:
            print('%-12s %9.3f %9.3f %9.0f%% %8.0f%% %8s  %s'
                  % (r['fecha'], r['cs_medio'] or 0, r['cs_p10'] or 0,
                     100 * (r['frac_pasa'] or 0), 100 * (r['cob_scl'] or 0),
                     ('%.3f' % r['ndvi']) if r['ndvi'] is not None else '-',
                     CONOCIDAS.get(r['fecha'], '')))

    # --- el veredicto, con el criterio fijado de antemano --------------------
    print('\n' + '=' * 84)
    print('VEREDICTO: ¿separa `cs_medio` la escena con bruma de las limpias?')
    print('=' * 84)
    limpias = [d for d, t in CONOCIDAS.items() if t.startswith('limpia')]
    for lid, filas in sorted(todo.items()):
        por_fecha = {r['fecha']: r for r in filas}
        art = por_fecha.get('2026-07-05')
        lim = [por_fecha[d]['cs_medio'] for d in limpias
               if d in por_fecha and por_fecha[d]['cs_medio'] is not None]
        if art is None or not lim:
            print('  %-18s sin datos para comparar' % lid)
            continue
        print('  %-18s artefacto %.3f   limpias min %.3f  (margen %+.3f)'
              % (lid, art['cs_medio'], min(lim), min(lim) - art['cs_medio']))
        # y lo mismo con lo que hoy decide, para mostrar si alcanzaba
        pasa_l = [por_fecha[d]['frac_pasa'] for d in limpias if d in por_fecha]
        print('  %-18s   lo que HOY decide: frac_pasa artefacto %.0f%% vs limpias min '
              '%.0f%%' % ('', 100 * (art['frac_pasa'] or 0), 100 * min(pasa_l)))
    print("""
COMO SE LEE
-----------
· Si el margen es POSITIVO y grande, `cs_medio` separa y sirve como filtro de bruma:
  se fija un piso entre el artefacto y la mas baja de las limpias.
· Si el margen es cercano a cero o negativo, NO sirve, y hay que ir a la verificacion de
  plausibilidad temporal (una caida que se recupera no es del cultivo).
· `frac_pasa` es lo que hoy decide. Si en el artefacto es alta, queda demostrado que el
  filtro binario no alcanza — que es lo que se sospecha.

OJO: UN SOLO CASO. Aunque separe, esto es UNA escena artefacto contra tres limpias. Alcanza
para justificar construir el filtro; NO alcanza para fijar el umbral definitivo.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
