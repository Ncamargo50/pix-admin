# -*- coding: utf-8 -*-
"""Probar CUALQUIERA de los 280 indices del catalogo como eje candidato, sin escribirlo.

EL PROBLEMA QUE RESUELVE
------------------------
Medir si un indice sirve como segundo eje exige hoy tres pasos manuales: escribir su
formula en `series._indices`, declararle el signo de alarma en `ranking.SIGNO`, y recien
ahi correr el arnes. Eso son minutos de trabajo y, sobre todo, **una oportunidad de
transcribir mal la formula** — que es el error mas caro que tiene este repositorio y el
motivo por el que existe `tests/test_formulas_contra_catalogo.py`.

Este modulo genera la banda a partir del catalogo congelado en
`referencias_primarias/catalogos/`, el mismo que audita las formulas de produccion. La
formula que se prueba es la publicada, con su DOI, no una transcripcion.

    python -u -m medicion.indice_candidato --listar red-edge
    python -u -m medicion.indice_candidato --indice NDREI --fecha 2026-08-01

QUE **NO** HACE, Y ES A PROPOSITO
---------------------------------
No mete nada en produccion. Calcula la banda y mide su correlacion con el eje de vigor
sobre los lotes reales — que es la PRIMERA de las tres patas que la casa exige para mover
`config.EJES`. Las otras dos (tasa empirica sobre fechas sin evento, y lift contra la nula
sintetica) siguen siendo `medicion/calibrar_criterio.py` y `medicion/comparar_ejes.py`.

Y sigue valiendo lo que ya se midio: **no existe un segundo eje optico independiente**.
Los 280 indices del catalogo proyectan el mismo modo dominante del dosel. Este modulo sirve
para verificarlo rapido sobre un candidato nuevo, no para esperar un milagro.
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(RAIZ, 'referencias_primarias', 'catalogos')


def _cargar(nombre):
    with open(os.path.join(CAT, nombre), encoding='utf-8') as fh:
        d = json.load(fh)
    return d.get('SpectralIndices', d)


INDICES = _cargar('asi_spectral-indices-dict.json')
BANDAS = _cargar('asi_bands.json')
S2 = {k: (v.get('platforms', {}).get('sentinel2a', {}) or {}).get('band')
      for k, v in BANDAS.items()}

# Bandas del catalogo que Sentinel-2 NO puede dar. Un indice que las use es
# incalculable acá, y decirlo temprano evita perder una corrida entera.
SIN_S2 = {k for k, v in S2.items() if not v}

# Constantes del catalogo (gamma, L, etc.). Se resuelven con su valor por defecto.
try:
    _CONST = _cargar('asi_constants.json')
except FileNotFoundError:
    _CONST = {}


def calculable(clave):
    """(True, '') si el indice se puede armar con Sentinel-2; (False, motivo) si no."""
    d = INDICES.get(clave)
    if d is None:
        return False, 'no esta en el catalogo'
    faltan = [b for b in d.get('bands', []) if b in SIN_S2 or b not in S2]
    # Las constantes no son bandas: se separan.
    faltan = [b for b in faltan if b not in _CONST]
    if faltan:
        return False, 'Sentinel-2 no tiene %s' % ', '.join(faltan)
    return True, ''


def a_expresion(clave):
    """Formula del catalogo reescrita en nombres de banda de Sentinel-2.

    ⚠️ Sustitucion con LIMITES DE PALABRA. La version ingenua convierte
    `(N - S1)/(N + S1)` en `(B8 - B211)/...` porque la `B` de `B11` tambien se
    reemplaza. Es el mismo cuidado que en `tests/test_formulas_contra_catalogo.py`.
    """
    f = INDICES[clave]['formula']
    return re.sub(r'\b([A-Za-z][A-Za-z0-9]*)\b',
                  lambda m: S2.get(m.group(1)) or m.group(1), f)


def banda_ee(img, clave):
    """Imagen de una banda con el indice `clave`, calculada sobre reflectancia 0-1."""
    import ee
    ok, motivo = calculable(clave)
    if not ok:
        raise ValueError('%s no es calculable con Sentinel-2: %s' % (clave, motivo))
    usadas = sorted({b for b in re.findall(r'\bB\d+A?\b', a_expresion(clave))})
    dic = {b: img.select(b).divide(10000) for b in usadas}
    for c, v in _CONST.items():
        if re.search(r'\b%s\b' % re.escape(c), INDICES[clave]['formula']):
            dic[c] = ee.Image.constant(v.get('default'))
    return img.expression(a_expresion(clave), dic).rename(clave)


def correlacion_con_vigor(sitio, feat, fecha, clave, eje='NDMI', escala=20):
    """|r| espacial del candidato contra el eje de vigor, sobre pixel limpio.

    Es una correlacion ESPACIAL de una fecha, no de residuos temporales — que es la
    que de verdad entra en la Mahalanobis. Sirve como criba rapida: un candidato que
    ya correlaciona 0,97 espacialmente no vale la pena medirlo en residuos.
    """
    import ee

    from pix_alerta import focos as fo
    from pix_alerta import series as sr
    geom = fo._geom_lote(sitio, feat)
    import pandas as pd
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(geom)
           .filterDate(fecha, str(pd.Timestamp(fecha) + pd.Timedelta(days=1))[:10]))
    if not int(col.size().getInfo() or 0):
        return None
    img = ee.Image(col.first())
    valido = sr._mascara(img)
    cand = banda_ee(img, clave).updateMask(valido).rename('a')
    base = sr._indices(img).select(eje).updateMask(valido).rename('b')
    r = cand.addBands(base).reduceRegion(
        reducer=ee.Reducer.pearsonsCorrelation(), geometry=geom, scale=escala,
        maxPixels=1e9, bestEffort=True).getInfo()
    return r.get('correlation')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--listar', default=None, metavar='TEXTO',
                    help='lista los indices del catalogo que mencionen TEXTO')
    ap.add_argument('--indice', default=None, help='clave del catalogo (ej. NDREI)')
    ap.add_argument('--fecha', default=None, help='YYYY-MM-DD de la escena')
    ap.add_argument('--cliente', default='TRIGO')
    ap.add_argument('--eje', default='NDMI', help='eje de vigor contra el que medir')
    a = ap.parse_args(argv)

    if a.listar:
        t = a.listar.lower()
        print('Indices del catalogo que mencionan %r y son calculables con S2:\n' % a.listar)
        print('%-12s %-34s %s' % ('clave', 'formula (S2)', 'nombre'))
        print('-' * 92)
        for k in sorted(INDICES):
            d = INDICES[k]
            texto = ' '.join(str(d.get(x, '')) for x in
                             ('long_name', 'application_domain', 'formula')).lower()
            if t not in texto and t not in k.lower():
                continue
            ok, motivo = calculable(k)
            print('%-12s %-34s %s' % (k, a_expresion(k) if ok else '(%s)' % motivo,
                                      (d.get('long_name') or '')[:34]))
        return 0

    if not a.indice:
        print('hace falta --indice o --listar. Ver --help')
        return 1

    ok, motivo = calculable(a.indice)
    d = INDICES.get(a.indice) or {}
    print('\n%s — %s' % (a.indice, d.get('long_name', '?')))
    print('  formula catalogo : %s' % d.get('formula'))
    print('  sobre Sentinel-2 : %s' % (a_expresion(a.indice) if ok else 'NO CALCULABLE'))
    print('  referencia       : %s' % d.get('reference'))
    if not ok:
        print('\n  ⛔ %s' % motivo)
        return 0
    if not a.fecha:
        print('\n  (agrega --fecha YYYY-MM-DD para medir su correlacion con el vigor)')
        return 0

    from pix_alerta.ee_init import inicializar
    print('\n[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    print('\nCORRELACION ESPACIAL contra %s, escena del %s' % (a.eje, a.fecha))
    print('%-22s %10s  %s' % ('lote', '|r|', 'lectura'))
    print('-' * 60)
    vals = []
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            try:
                r = correlacion_con_vigor(s, f, a.fecha, a.indice, a.eje)
            except Exception as exc:                       # noqa: BLE001
                print('%-22s AVERIA %s' % (lid, str(exc)[:40]))
                continue
            if r is None:
                print('%-22s sin escena' % lid)
                continue
            vals.append(abs(r))
            lectura = ('redundante' if abs(r) > 0.90 else
                       'parcialmente redundante' if abs(r) > 0.70 else
                       'candidato: medir en RESIDUOS')
            print('%-22s %+10.3f  %s' % (lid, r, lectura))
    if vals:
        m = sum(vals) / len(vals)
        print('\n|r| medio: %.3f   varianza independiente: %.1f%%' % (m, 100 * (1 - m ** 2)))
        print("""
COMO SEGUIR
-----------
Esto es una CRIBA espacial de una fecha, no la medicion que decide. Si |r| queda por
debajo de 0,70, el candidato merece medirse en RESIDUOS TEMPORALES —que es lo que entra
en la Mahalanobis— con `medicion/textura_como_eje.py`, y despues las otras dos patas:
tasa empirica y lift contra la nula sintetica.

Y sigue en pie lo ya medido: los residuos de NDMI y NDRE correlacionan 0,969, y la
literatura dice que el dosel tiene un solo modo optico dominante. Un |r| espacial bajo
sobre una fecha puede ser ruido, no informacion.""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
