# -*- coding: utf-8 -*-
"""¿Hay un par de ejes MEJOR que NDMI+NDRE para el acercamiento intra-lote?

    python medicion/comparar_ejes_acercamiento.py --sitio SANTO_ANTONIO

POR QUE ESTA MEDICION Y NO UNA REVISION BIBLIOGRAFICA
------------------------------------------------------
La pregunta «¿no habrá un método mejor?» no se contesta leyendo papers: se contesta
midiendo sobre ESTE campo, con ESTAS fechas. La regla del proyecto es medición
primero, detector después.

Y hay un límite físico que ninguna cita cambia: **un índice nuevo sobre las mismas
bandas no agrega información, agrega correlación.** La dimensionalidad efectiva de
la reflectancia vegetal es de 3 a 5 factores; Sentinel-2 tiene 4 bandas útiles de
borde rojo/NIR/SWIR sobre dosel. Así que la pregunta medible no es «¿qué índice es
mejor?» sino:

    ¿Los dos ejes que exigimos juntos están midiendo COSAS DISTINTAS,
    o es el mismo dato dos veces con otro nombre?

Si la correlación entre los residuos de los dos ejes es 0,95, la conjunción no
filtra nada: es un solo eje disfrazado de dos, y el porcentaje que se le reporta al
cliente está sostenido por un umbral, no por evidencia independiente.

QUE MIDE
--------
Sobre los pares de fechas REALES de cada lote:

1. **Correlación entre residuos** de cada par de ejes candidatos. Es la pregunta
   decisiva: si es alta, cambiar de eje no cambia nada.
2. **Fracción de área marcada** por cada par, con el mismo Z_FOCO y la misma MMU.
   Un par que marca lo mismo en todos los lotes y todas las fechas es una CUOTA.
3. **Variación entre fechas y lotes.** Un criterio que discrimina tiene que dar
   números distintos en campos distintos; uno que siempre da lo mismo está midiendo
   su propio umbral.

LO QUE ESTA MEDICION **NO** PUEDE CONTESTAR, y hay que decirlo
--------------------------------------------------------------
Cuál par ACIERTA más. Para eso hace falta verdad de campo —qué había realmente en
cada mancha— y hoy hay CERO validaciones registradas. Sin eso se puede medir si dos
ejes son redundantes y si un criterio es una cuota, que es mucho, pero no se puede
medir la puntería. Cualquiera que ofrezca lo segundo sin datos de campo está
estimando.
"""
import argparse
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Candidatos calculables con Sentinel-2 sobre dosel. Todos ya existen en
# `series._indices`; acá sólo se comparan.
CANDIDATOS = ('NDMI', 'NDRE', 'CIRE', 'PSRI', 'NDVI')


def _z(delta, geom, banda, fo):
    return fo._z_robusto(delta, geom, banda)


def medir_lote(sitio, feat, hasta, fo, cfg, ee):
    """Devuelve dict con correlaciones y fracción marcada por par de ejes."""
    import pandas as pd

    lid = str(feat['properties'].get(sitio.campo_id))
    geom = fo._geom_lote(sitio, feat)
    desde = str(pd.Timestamp(hasta) - pd.Timedelta(days=fo.VENTANA_DIAS))[:10]
    try:
        escenas = fo._cobertura_por_escena(geom, desde, hasta)
        act, ref = fo._par_de_fechas(escenas, hasta)
    except fo.SinPar as e:
        return {'lote': lid, 'nota': str(e)}

    ia = fo._imagen_util(act[1], geom)
    ir = fo._imagen_util(ref[1], geom)
    # Los índices se piden TODOS, no sólo los de cfg.EJES.
    import ee as _ee
    del _ee

    def util(idx_escena):
        img = ee.Image(ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                       .filter(ee.Filter.eq('system:index', idx_escena)).first())
        from pix_alerta import series as sr
        valido = sr._mascara(img)
        ejes = sr._indices(img)
        fvc = sr._fvc(ejes.select('NDVI').updateMask(valido), geom, fo.ESCALA)
        m = valido.And(fvc.gte(cfg.FVC_MINIMA))
        return ejes.select(list(CANDIDATOS)).updateMask(m)

    del ia, ir
    delta = util(act[1]).subtract(util(ref[1]))
    zs = {e: _z(delta, geom, e, fo) for e in CANDIDATOS}

    # --- 1. correlación entre residuos, sobre el propio lote ------------------
    pila = ee.Image.cat([zs[e].rename(e) for e in CANDIDATOS])
    cors = {}
    for a, b in itertools.combinations(CANDIDATOS, 2):
        try:
            c = pila.select([a, b]).reduceRegion(
                reducer=ee.Reducer.pearsonsCorrelation(), geometry=geom,
                scale=fo.ESCALA, maxPixels=1e9, bestEffort=True).get('correlation')
            cors['%s~%s' % (a, b)] = c
        except Exception:
            cors['%s~%s' % (a, b)] = None

    # --- 2. fracción marcada por cada par ------------------------------------
    from pix_alerta.ranking import SIGNO
    total = ee.Image(1).updateMask(zs[CANDIDATOS[0]].mask()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=geom, scale=fo.ESCALA,
        maxPixels=1e9, bestEffort=True).values().get(0)
    fracs = {}
    for a, b in itertools.combinations(CANDIDATOS, 2):
        cond = (zs[a].multiply(SIGNO[a]).gte(fo.Z_FOCO)
                .And(zs[b].multiply(SIGNO[b]).gte(fo.Z_FOCO)))
        n = cond.selfMask().reduceRegion(
            reducer=ee.Reducer.count(), geometry=geom, scale=fo.ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0)
        fracs['%s+%s' % (a, b)] = n
    # Y cada eje SOLO, para ver cuánto aporta realmente la conjunción.
    solos = {}
    for a in CANDIDATOS:
        n = zs[a].multiply(SIGNO[a]).gte(fo.Z_FOCO).selfMask().reduceRegion(
            reducer=ee.Reducer.count(), geometry=geom, scale=fo.ESCALA,
            maxPixels=1e9, bestEffort=True).values().get(0)
        solos[a] = n

    r = ee.Dictionary({'cor': ee.Dictionary(cors), 'par': ee.Dictionary(fracs),
                       'solo': ee.Dictionary(solos), 'total': total}).getInfo()
    tot = float(r.get('total') or 0) or 1.0
    return {
        'lote': lid, 'fecha': act[0], 'ref': ref[0], 'px_utiles': int(tot),
        'cor': {k: (round(v, 3) if v is not None else None)
                for k, v in (r.get('cor') or {}).items()},
        'par_pct': {k: round(100.0 * (v or 0) / tot, 3)
                    for k, v in (r.get('par') or {}).items()},
        'solo_pct': {k: round(100.0 * (v or 0) / tot, 3)
                     for k, v in (r.get('solo') or {}).items()},
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--sitio', action='append', required=True)
    p.add_argument('--hasta', default='2026-07-27')
    p.add_argument('--salida', default='medicion/ejes_acercamiento.json')
    a = p.parse_args(argv)

    import ee
    from pix_alerta import clientes as cl, config as cfg, focos as fo
    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    cs = cl.cargar_todos(solo_activos=False)
    cl.registrar_sitios(cs)

    out = []
    for clave in a.sitio:
        sitio = cfg.SITIOS[clave]
        with open(sitio.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for feat in gj['features']:
            r = medir_lote(sitio, feat, a.hasta, fo, cfg, ee)
            r['sitio'] = clave
            out.append(r)
            print('  %-18s %s' % (r['lote'], r.get('nota') or
                                  ('%s vs %s · %d px' % (r['fecha'], r['ref'],
                                                         r['px_utiles']))))
    with open(a.salida, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print('\n-> %s' % a.salida)
    return 0


if __name__ == '__main__':
    sys.exit(main())
