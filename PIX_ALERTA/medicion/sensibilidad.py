# -*- coding: utf-8 -*-
"""SENSIBILIDAD: ¿cuál es la anomalía MÁS CHICA que el motor detecta?

QUE SE PUEDE MEDIR SIN VERDAD DE CAMPO, Y QUE NO
------------------------------------------------
La sensibilidad de verdad —de los problemas REALES del campo, cuantos ve— **no se puede
medir sin verdad de campo**. Para eso estan los puntos de control que camina el tecnico
(`pix_alerta/controles.py`), y hacen falta unas diez rondas.

Lo que SI se puede medir hoy, y es riguroso, es la **ANOMALIA MINIMA DETECTABLE**: se
inyecta en la imagen REAL una caida sintetica de magnitud y tamano conocidos, y se mide que
fraccion detecta el criterio. Contesta la pregunta que el cliente hace de verdad:

    «una caida de tanto en la humedad del dosel, sobre tantas hectareas, ¿la ves?»

Es una medicion de POTENCIA del detector, no de utilidad agronomica. Un evento real puede
ser mas sutil o mas ruidoso que una caida limpia inyectada. Pero fija el PISO: por debajo
de la magnitud minima detectable, el motor no va a ver nada, y eso hay que saberlo antes de
prometer algo.

COMO SE INYECTA, Y POR QUE ASI
------------------------------
Se resta una constante a los dos ejes DENTRO de un circulo, y SOLO en la escena evaluada —
no en la linea base. Asi es como se ve un evento nuevo: la trayectoria del pixel viene
normal y la ultima observacion cae.

La magnitud se expresa en MULTIPLOS DEL RUIDO REAL de cada eje, medido con diferencias
entre escenas consecutivas sobre estos mismos lotes (`verificar_escala_real.ruido_corto`):

    NDMI   ruido de corto plazo  0,043 a 0,060      -> se usa 0,045
    NDRE   ruido de corto plazo  0,024 a 0,035      -> se usa 0,030

Expresarlo en multiplos del ruido es lo unico que hace comparable el numero entre ejes y
entre campanas; en unidades del indice, «0,05 de NDMI» no significa nada por si solo.

TRES COSAS QUE SE MIDEN POR CADA CASO
-------------------------------------
  marcado_en_el_parche   fraccion del parche inyectado que el criterio marca
  ha_marcadas            cuantas hectareas de ese parche quedan marcadas
  reportable             si esas hectareas superan la unidad minima de mapeo (0,20 ha),
                         que es lo que decide si el foco LLEGA al cliente

La ultima es la que importa: marcar 3 pixeles de un parche de 2 ha no le sirve a nadie.

EL CONTROL, QUE ES OBLIGATORIO
------------------------------
Se corre tambien con inyeccion CERO. Lo que marque ahi es falso positivo dentro del mismo
parche, y hay que restarlo mentalmente de todo lo demas. Sin ese control, la "deteccion" de
la magnitud mas chica podria ser simplemente la tasa de falsa alarma.

LIMITE DECLARADO: se inyectan tres parches por corrida para ahorrar viajes a GEE, y
suman ~2,5% del lote. La matriz de la Mahalanobis se estima espacialmente sobre el lote,
asi que los parches se contaminan un poco entre si — inflan levemente la covarianza y por
lo tanto SUBESTIMAN la deteccion. El numero que sale es una cota inferior.

LO QUE APARECIO AL MEDIRLO, Y CAMBIA COMO HAY QUE INFORMARLO
-----------------------------------------------------------
La misma caida inyectada da respuestas que difieren TREINTA VECES segun donde caiga:

    parche      inyeccion    z_NDMI     d2      (umbral d2 = 9,21)
    0,25 ha       0,225      -1,69     6,65
    0,75 ha       0,225      -3,02    14,44     <- detectado
    2,00 ha       0,225      -0,93     0,43     <- invisible

Se verifico que la inyeccion llega igual a los tres (0,2250 exacto) y que los tres son
100% evaluables. La causa es otra: **SIGMA VARIA 6,1 VECES DENTRO DEL MISMO LOTE**
(p5 = 0,031, p50 = 0,146, p95 = 0,186 en NDMI). Y sigma es lo que divide al residuo.

Eso es consecuencia directa de algo ya medido: sigma no mide ruido, mide sobre todo el
ERROR DEL MODELO de la recta ajustada (2,7 a 6,5 veces el ruido de corto plazo). Ese error
es grande donde la trayectoria del pixel se aparta mas de una recta, y chico donde no — y
esa geografia no tiene nada que ver con la sanidad del cultivo.

**Entonces la sensibilidad del motor no es uniforme dentro del lote.** Informar un solo
numero seria falso. Por eso este arnes ESTRATIFICA por sigma local y da la curva en cada
estrato.

EL RESULTADO, MEDIDO — SANTO_ANTONIO-02, escena 2026-07-15, parche de 0,75 ha
------------------------------------------------------------------------------
Fraccion del parche que el criterio marca, y si eso supera la unidad minima de mapeo
(0,20 ha), que es lo que decide si el foco LLEGA al cliente:

    caida            sigma BAJO        sigma MEDIO       sigma ALTO
    CONTROL (0)       0%   no           0%   no           0%   no
    1 x ruido         0%   no           0%   no           0%   no
    2 x ruido         0%   no          19%  0,15 ha no    5%  0,04 ha no
    3 x ruido         4%   no          36%  0,27 ha SI   18%  0,14 ha no
    5 x ruido        34%  0,25 ha SI   47%  0,35 ha SI   27%  0,20 ha SI

LO QUE ESTO DICE, EN CRISTIANO:
  · por debajo de 2 veces el ruido, el motor NO VE NADA en ninguna parte del lote;
  · 3 veces el ruido llega al cliente en 1 de 3 zonas;
  · 5 veces el ruido llega en las 3.

Y el CONTROL da 0% en los tres estratos, asi que ninguno de esos numeros esta inflado por
falsa alarma de fondo.

EN UNIDADES QUE SE ENTIENDAN: 5 veces el ruido de NDMI son 0,225 unidades del indice.
El NDMI de este trigo en llenado ronda 0,50, asi que es una caida de ~45% del agua del
dosel. Tres veces el ruido son ~27%. **O sea que el motor reporta con seguridad un daño
SEVERO sobre al menos 0,75 ha, y por debajo de eso depende de donde caiga.**

DOS COSAS QUE NO SE PUEDEN CONCLUIR DE ACA:
1. Que el motor no sirva. Un daño real no es una caida uniforme de una sola escena: crece,
   persiste y se concentra. MEDIDO aparte: el foco real que se entrego el 2026-07-15 ya
   estaba en la escena anterior en el 81,8% de su superficie (30 veces el azar). Los
   eventos reales acumulan evidencia entre escenas; la inyeccion de una sola fecha no.
2. Que esto sea la sensibilidad a problemas de campo. Es la POTENCIA del detector frente a
   una caida limpia. La sensibilidad real la miden los puntos de control a campo.

    python -m medicion.sensibilidad --sitio SANTO_ANTONIO --lote SANTO_ANTONIO-02
"""
import argparse
import json
import math
import sys

# Ruido de corto plazo por eje, MEDIDO sobre estos lotes con diferencias consecutivas.
RUIDO = {'NDMI': 0.045, 'NDRE': 0.030}
# Magnitudes a probar, en multiplos del ruido. El 0 es el control obligatorio.
MULTIPLOS = (0.0, 1.0, 2.0, 3.0, 5.0)
# Tamanos de parche en ha. El mas chico esta apenas por encima de la unidad minima de
# mapeo (0,20 ha) y el mas grande es lo que ya seria una mancha grande en un lote.
AREAS_HA = (0.25, 0.75, 2.0)
# Tamano del parche cuando se estratifica por sigma: se usa UNO solo, igual en los tres
# estratos, para que la unica cosa que cambie entre ellos sea sigma. 0,75 ha esta bien por
# encima de la unidad minima de mapeo (0,20 ha), asi que un parche detectado del todo si
# llegaria al cliente.
AREA_PARCHE_HA = 0.75
SEMILLA = 20260729


def _circulo(lon, lat, radio_m, lados=32):
    import ee
    dlat = radio_m / 111320.0
    dlon = radio_m / (111320.0 * max(math.cos(math.radians(lat)), 1e-6))
    anillo = [[lon + dlon * math.cos(2 * math.pi * k / lados),
               lat + dlat * math.sin(2 * math.pi * k / lados)]
              for k in range(lados + 1)]
    return ee.Geometry.Polygon([anillo])


def sitios_de_parches(geom, evaluada, escala, n, radios):
    """`n` posiciones dentro del area evaluable, separadas, con semilla fija."""
    import ee
    pts = evaluada.selfMask().rename('c').sample(
        region=geom, scale=escala, numPixels=400, seed=SEMILLA,
        geometries=True, dropNulls=True)
    info = pts.limit(400).getInfo().get('features', [])
    out, usados = [], []
    sep = 2.5 * max(radios)
    for f in info:
        c = (f.get('geometry') or {}).get('coordinates')
        if not c or len(c) < 2:
            continue
        lon, lat = c[0], c[1]
        choca = False
        for (ol, oa) in usados:
            dy = (lat - oa) * 111320.0
            dx = (lon - ol) * 111320.0 * math.cos(math.radians(lat))
            if math.hypot(dx, dy) < sep:
                choca = True
                break
        if choca:
            continue
        usados.append((lon, lat))
        out.append((lon, lat))
        if len(out) >= n:
            break
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sitio', default='SANTO_ANTONIO')
    ap.add_argument('--lote', default=None)
    ap.add_argument('--hasta', default='2026-07-16')
    a = ap.parse_args(argv)

    import ee

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
    ejes = list(cfg.EJES)
    escala = cri.ESCALA
    mmu = cfg.valor_de(sitio, 'mmu_ha', fo.MMU_HA)
    print('ruido de corto plazo usado: %s' % {e: RUIDO[e] for e in ejes})
    print('unidad minima de mapeo: %.2f ha  (lo que decide si el foco llega al cliente)'
          % mmu)

    with open(sitio.lotes_geojson, encoding='utf-8') as fh:
        gj = json.load(fh)
    for f in gj['features']:
        lid = str(f['properties'].get(sitio.campo_id))
        if a.lote and a.lote != lid:
            continue
        geom = fo._geom_lote(sitio, f)
        area_lote = float(f['properties'].get(sitio.campo_area) or 0)
        print('\n' + '=' * 82)
        print('%s   (%.1f ha)' % (lid, area_lote))
        print('=' * 82)
        try:
            r0 = cri.evaluar(geom, a.hasta, sitio=sitio, escala=escala)
        except cri.SinBase as e:
            print('  sin escena utilizable: %s' % e)
            continue
        print('  escena evaluada: %s' % r0['fecha'])

        # ESTRATIFICAR POR SIGMA LOCAL. Un parche del MISMO tamano en cada tercil de
        # sigma: es la unica forma de que la curva de sensibilidad se pueda leer, porque
        # sigma varia 6 veces dentro del lote y es lo que divide al residuo.
        sig = r0['sigma'].select(ejes[0])
        _q = sig.rename('v').reduceRegion(
            reducer=ee.Reducer.percentile([33, 67]), geometry=geom, scale=escala,
            maxPixels=1e9, bestEffort=False).getInfo()
        _vals = sorted(v for v in _q.values() if isinstance(v, (int, float)))
        if len(_vals) < 2:
            print('  no se pudo estratificar por sigma')
            continue
        c33, c67 = _vals[0], _vals[1]
        rad = math.sqrt(AREA_PARCHE_HA * 1e4 / math.pi)
        estratos = [('sigma BAJO  (< p33)', sig.lt(c33)),
                    ('sigma MEDIO (p33-p67)', sig.gte(c33).And(sig.lt(c67))),
                    ('sigma ALTO  (> p67)', sig.gte(c67))]
        parches, etiquetas = [], []
        for nom, cond in estratos:
            pos = sitios_de_parches(geom, r0['anomalia'].mask().And(cond),
                                    escala, 1, [rad])
            if not pos:
                print('  sin lugar para un parche en %s' % nom)
                continue
            parches.append((_circulo(pos[0][0], pos[0][1], rad), AREA_PARCHE_HA))
            etiquetas.append(nom)
        if len(parches) < 2:
            print('  no se pudieron colocar parches en al menos dos estratos')
            continue
        print('  sigma del lote: p33 %.4f  p67 %.4f   (ruido real %s = %.3f)'
              % (c33, c67, ejes[0], RUIDO[ejes[0]]))
        print('  %d parches de %.2f ha, uno por estrato de sigma  (%.1f%% del lote)'
              % (len(parches), AREA_PARCHE_HA,
                 100 * len(parches) * AREA_PARCHE_HA / area_lote if area_lote else 0))

        # CUANTO DE CADA PARCHE ES SIQUIERA EVALUABLE. Sin esto, un parche que cae
        # medio afuera del lote o sobre area enmascarada da 0% de deteccion y parece
        # que el criterio no lo vio, cuando en realidad no habia donde verlo. Es la
        # misma regla que ya salvo otras mediciones: contar pixeles ANTES de creer un
        # porcentaje.
        fc0 = ee.FeatureCollection([ee.Feature(g, {'i': k})
                                    for k, (g, _ha) in enumerate(parches)])
        d0 = (r0['anomalia'].mask().rename('ev').unmask(0, False).addBands(
            sig.rename('sg')).reduceRegions(
            collection=fc0, reducer=ee.Reducer.mean(),
            scale=escala, tileScale=4).getInfo())
        info = {int(x['properties']['i']): x['properties']
                for x in d0.get('features', [])}
        print('\n  %-24s %10s %12s %12s'
              % ('estrato', 'sigma', 'veces ruido', 'evaluable'))
        for k, nom in enumerate(etiquetas):
            p = info.get(k, {})
            sgv = float(p.get('sg') or 0.0)
            ev = float(p.get('ev') or 0.0)
            aviso = '' if ev >= 0.8 else '  <- POCO EVALUABLE'
            print('  %-24s %10.4f %11.1fx %11.0f%%%s'
                  % (nom, sgv, sgv / RUIDO[ejes[0]] if sgv else 0, 100 * ev, aviso))

        print('\n  %-14s %-24s %-11s %-11s %-11s'
              % ('caida', 'estrato', 'del parche', 'ha marcadas', 'llega al cliente'))
        print('  ' + '-' * 76)
        for mult in MULTIPLOS:
            iny = None
            if mult > 0:
                capas = []
                for e in ejes:
                    img = ee.Image(0).rename(e)
                    for g, _ha in parches:
                        img = img.where(ee.Image(0).clip(g).mask(),
                                        RUIDO[e] * mult)
                    capas.append(img)
                iny = ee.Image.cat(capas)
            try:
                r = cri.evaluar(geom, a.hasta, sitio=sitio, escala=escala,
                                inyeccion=iny)
            except Exception as exc:                     # noqa: BLE001
                print('  %-14s AVERIA %s: %s'
                      % ('%.0f x ruido' % mult, type(exc).__name__, str(exc)[:40]))
                continue
            m = r['anomalia'].unmask(0, False)
            d = m.rename('p').reduceRegions(
                collection=fc0, reducer=ee.Reducer.mean().setOutputs(['p']),
                scale=escala, tileScale=4).getInfo()
            por_i = {int(x['properties']['i']): float(x['properties'].get('p') or 0.0)
                     for x in d.get('features', [])}
            etq = 'CONTROL (sin caida)' if mult == 0 else '%.0f x ruido' % mult
            for k, nom in enumerate(etiquetas):
                pp = por_i.get(k, 0.0)
                ha_m = pp * AREA_PARCHE_HA
                print('  %-14s %-24s %10.0f%% %10.2f  %s'
                      % (etq if k == 0 else '', nom, 100 * pp, ha_m,
                         'SI' if ha_m >= mmu else 'no'))
            print('  ' + '-' * 76)
    print("""
COMO SE LEE
-----------
· La columna que decide es la ultima: si las hectareas marcadas del parche no superan la
  unidad minima de mapeo, el foco NO llega al cliente aunque el criterio haya marcado algo.
· El CONTROL (sin caida) es la falsa alarma dentro del mismo parche. Todo lo demas hay que
  leerlo por encima de ese piso.
· `x ruido` es la caida en multiplos del ruido de corto plazo real del indice. Es la unica
  forma de que el numero sea comparable entre ejes y entre campanas.
· El resultado es una COTA INFERIOR: los tres parches se contaminan un poco entre si a
  traves de la covarianza espacial, lo que subestima la deteccion.

ESTO NO ES LA SENSIBILIDAD A PROBLEMAS REALES. Es la potencia del detector frente a una
caida limpia. Un problema real puede ser mas gradual, mas ruidoso o afectar un solo eje.
La sensibilidad real la miden los puntos de control a campo.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
