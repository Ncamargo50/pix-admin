# -*- coding: utf-8 -*-
"""¿Cuánto de la correlación entre los dos ejes es física y cuánto es la banda compartida?

DE DONDE SALE ESTA PREGUNTA
---------------------------
De la revisión de literatura israelí del 2026-07-29 (`INVESTIGACION_ISRAEL_2026-07-29.md`).
Herrmann, Karnieli, Bonfil, Cohen & Alchanatis (2010, *IJRS* 31(19):5127-5143) miden que
los índices VNIR correlacionan entre sí |r| = 0,58-0,92, los basados en SWIR 1510 nm
|r| = 0,87-0,99, y **entre los dos grupos |r| = 0,00-0,22**. O sea que existe un segundo
eje realmente independiente, y está en el SWIR.

Este motor usa NDMI (SWIR) + NDRE (red-edge), que es la arquitectura correcta. Pero:

    NDMI = (B8A - B11) / (B8A + B11)
    NDRE = (B8A - B5)  / (B8A + B5)

**COMPARTEN B8A.** Una banda en común induce correlación que no es del cultivo: es de la
construcción del índice. Si B8A tiene ruido —y lo tiene: atmósfera residual, BRDF,
remuestreo— ese ruido entra a los dos índices con el mismo signo en el numerador y en el
denominador, y los correlaciona sin que pase nada en el campo.

Y encaja con una medición propia que estaba SIN EXPLICAR. En `config.py` quedó escrito:

    "CIre queda como alternativa legitima: es el MENOS correlacionado con NDMI (0,72
     contra 0,82), o sea el que mas evidencia independiente aporta."

y se eligió NDRE "por ROBUSTEZ, no por la medicion". CIre = B7/B5 - 1 **no toca B8A**.
Ahora hay un mecanismo que explica ese 0,72 contra 0,82: no es que CIre sea mejor índice,
es que no comparte banda.

QUE MIDE ESTE ARNES
-------------------
La correlación entre los RESIDUOS TEMPORALES de tres pares, sobre los lotes reales:

    NDMI + NDRE     comparten B8A          <- el par en produccion
    NDMI + CIRE     no comparten nada      <- el candidato
    NDMI + PSRI     no comparten nada      <- el par viejo, para referencia

Se mide sobre RESIDUOS y no sobre los índices crudos, porque es la correlación de los
residuos la que entra en la Mahalanobis. Ya se sabe que los índices crudos correlacionan
0,97-0,998 espacialmente entre sí (son biomasa con varios nombres); eso no es lo que
importa acá.

POR QUE IMPORTA EL NUMERO
-------------------------
Con dos ejes de correlación rho, la Mahalanobis tiene una dimensión efectiva que cae a 1
cuando rho -> 1. Con rho = 0,94 —lo medido en el lote que alertó— los dos ejes son
prácticamente el mismo eje, y exigir que los dos se muevan juntos no agrega la evidencia
que el diseño promete. Bajar rho es aumentar la evidencia independiente.

    python -m medicion.banda_compartida --hasta 2026-07-16

LO QUE ESTA MEDICION NO DECIDE
------------------------------
Que un par tenga menor correlación NO lo convierte en mejor par. La decisión de cambiar
`config.EJES` exige además medir la TASA EMPIRICA sobre fechas sin evento con el par
nuevo (`medicion/calibrar_criterio.py`) y el lift contra la nula sintética
(`medicion/comparar_ejes.py`). Este arnés aporta UNA de las tres cosas, y la más barata.
"""
import argparse
import json
import sys

PARES = (('NDMI', 'NDRE'), ('NDMI', 'CIRE'), ('NDMI', 'PSRI'))
# Banda que cada indice comparte con NDMI, para que la tabla se explique sola.
COMPARTE = {'NDRE': 'B8A', 'CIRE': '(ninguna)', 'PSRI': '(ninguna)'}


def rho_residuos(sitio, feat, hasta, ejes, escala=None):
    """Correlacion de los residuos temporales de `ejes`, agrupada sobre el lote.

    Se calcula igual que la que usa el criterio candidato: residuos contra la recta
    ajustada por pixel, recortados en 3 sigmas para que una nube residual no domine, y
    los productos cruzados sumados sobre todo el lote.
    """
    import ee
    import pandas as pd

    from pix_alerta import config as cfg
    from pix_alerta import criterio as cri
    from pix_alerta import focos as fo
    escala = escala or cri.ESCALA
    geom = fo._geom_lote(sitio, feat)
    ventana = cri.ventana_de(sitio)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=ventana))[:10]
    fin = str(pd.Timestamp(hasta) - pd.Timedelta(days=1))[:10]
    # `_coleccion_limpia` selecciona SOLO las bandas de `cfg.EJES` + NDVI, asi que para
    # medir un par que no esta en produccion hay que declararlo. Se hace pisando
    # `cfg.EJES` alrededor de la llamada —y restaurandolo en `finally`— para correr por
    # EL MISMO camino de produccion (misma mascara, misma cobertura, mismo dedup por
    # fecha) y no por una copia que podria divergir.
    _antes = cfg.EJES
    try:
        cfg.EJES = tuple(ejes)
        base = cri._coleccion_limpia(geom, desde, fin)
        n = int(base.size().getInfo() or 0)
    finally:
        cfg.EJES = _antes
    if n < cri.MIN_BASE:
        return None
    dia0 = ee.Date(desde).millis()
    e0, e1 = ejes

    def _con_t(img):
        img = ee.Image(img)
        t = ee.Image(ee.Date(img.get('system:time_start')).millis()
                     .subtract(dia0).divide(86400000)).float().rename('t')
        return (t.addBands(img.select([e0, e1]))
                .updateMask(img.select(e0).mask()))

    con_t = base.map(_con_t)
    pend, orden = {}, {}
    for e in (e0, e1):
        fit = con_t.select(['t', e]).reduce(ee.Reducer.linearFit())
        pend[e], orden[e] = fit.select('scale'), fit.select('offset')

    def _resid(img):
        img = ee.Image(img)
        t = (ee.Number(ee.Date(img.get('system:time_start')).millis())
             .subtract(dia0).divide(86400000))
        cap = []
        for e in (e0, e1):
            esp = orden[e].add(pend[e].multiply(ee.Image(ee.Number(t))))
            cap.append(img.select(e).subtract(esp).rename(e))
        return ee.Image.cat(cap).updateMask(img.select(e0).mask())

    res = base.map(_resid)
    mad = res.map(lambda i: ee.Image(i).abs()).median().multiply(1.4826)
    corte = mad.max(ee.Image.constant(1e-4)).multiply(3.0)
    rec = res.map(lambda i: ee.Image(i).max(corte.multiply(-1)).min(corte))
    s11 = rec.map(lambda i: ee.Image(i).select(e0).pow(2).rename('a')).sum()
    s22 = rec.map(lambda i: ee.Image(i).select(e1).pow(2).rename('b')).sum()
    s12 = rec.map(lambda i: ee.Image(i).select(e0)
                  .multiply(ee.Image(i).select(e1)).rename('c')).sum()
    tot = s11.addBands(s22).addBands(s12).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=True).getInfo()
    a, b, c = (tot.get('a') or 0), (tot.get('b') or 0), (tot.get('c') or 0)
    if a <= 0 or b <= 0:
        return None
    return {'rho': c / (a * b) ** 0.5, 'n_base': n}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--hasta', required=True)
    ap.add_argument('--cliente', default='TRIGO')
    a = ap.parse_args(argv)

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    print('\nCORRELACION DE RESIDUOS TEMPORALES entre los dos ejes.')
    print('Mas cerca de 1 = los dos ejes dicen lo mismo = menos evidencia'
          ' independiente.\n')
    print('%-20s %-14s %-12s %8s %7s' % ('lote', 'par', 'comparte', 'rho',
                                         'n_base'))
    print('-' * 66)
    acum = {}
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            for par in PARES:
                try:
                    r = rho_residuos(s, f, a.hasta, par)
                except Exception as exc:            # noqa: BLE001
                    print('%-20s %-14s AVERIA %s: %s'
                          % (lid, '+'.join(par), type(exc).__name__, str(exc)[:40]))
                    continue
                if r is None:
                    print('%-20s %-14s sin datos suficientes' % (lid, '+'.join(par)))
                    continue
                print('%-20s %-14s %-12s %8.3f %7d'
                      % (lid, '+'.join(par), COMPARTE[par[1]], r['rho'], r['n_base']))
                acum.setdefault(par, []).append(r['rho'])
    print('\n' + '=' * 66)
    print('%-14s %-12s %8s %8s %8s' % ('par', 'comparte', 'media', 'min', 'max'))
    print('-' * 54)
    for par, v in sorted(acum.items(), key=lambda x: sum(x[1]) / len(x[1])):
        print('%-14s %-12s %8.3f %8.3f %8.3f'
              % ('+'.join(par), COMPARTE[par[1]], sum(v) / len(v), min(v), max(v)))
    print("""
COMO SE LEE
-----------
Si el par que COMPARTE B8A tiene una correlacion sistematicamente mas alta que los que
no comparten nada, parte de esa correlacion es de construccion y no del cultivo — y
cambiar de segundo eje aumenta la evidencia independiente por una razon entendida.

Si las tres correlaciones salen parecidas, la banda compartida NO explica nada y la
correlacion es fisica: los indices miden biomasa con distintos nombres, que es lo que ya
se habia medido espacialmente. En ese caso NO hay nada que ganar cambiando de eje.

Y en cualquier caso, esto NO alcanza para cambiar `config.EJES`: falta la tasa empirica
sobre fechas sin evento y el lift contra la nula sintetica.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
