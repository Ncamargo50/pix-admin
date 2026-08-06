# -*- coding: utf-8 -*-
"""¿El motor calcula lo mismo que una implementacion independiente? Control cruzado.

POR QUE UN CONTROL CRUZADO Y NO UNA DEPENDENCIA
-----------------------------------------------
`eemont` (davemlz/eemont, 449 estrellas, JOSS doi:10.21105/joss.03168) hace lo mismo que
`series._indices` y `series._mascara`: escala la reflectancia, enmascara nubes y calcula
indices espectrales — usando `awesome-spectral-indices` por debajo.

**No se adopta como dependencia, y la razon no es orgullo.** El camino del motor esta
auditado banda por banda y tiene decisiones que una libreria generica no toma: B8A en vez
de B8 por resolucion nativa, mascara HIBRIDA de SCL dilatada 80 m + CloudScore+ con piso de
calidad de escena, exclusion de SCL 0/2/3. Cambiar codigo auditado por una caja negra
reintroduce el riesgo que ya costo tres focos falsos.

Lo que SI vale es usarlo como **segunda opinion**: si dos implementaciones independientes
dan distinto sobre la misma escena, una de las dos tiene un bug. Este arnes lo mide.

    python -u -m medicion.control_cruzado_eemont --cliente TRIGO --fecha 2026-08-01

QUE ESPERAR, Y COMO LEERLO
--------------------------
Las diferencias NO son todas errores. Hay tres fuentes esperables, y el arnes las separa:

  1. **Bandas distintas a proposito.** El motor usa B8A donde eemont usa B8 (ver
     `tests/test_formulas_contra_catalogo.py`). Eso produce una diferencia REAL y correcta
     en NDMI y NDRE. Se informa aparte y no cuenta como discrepancia.
  2. **Mascara distinta.** eemont enmascara con SCL simple; el motor agrega dilatacion de
     80 m y CloudScore+. Sobre pixeles limpios no deberia importar; cerca de nube si.
  3. **Discrepancia real.** Misma banda, mismo pixel, distinto numero. Eso es un bug de
     alguno de los dos, y es lo que este arnes busca.

Por eso la comparacion se hace sobre **el mismo conjunto de pixeles** —los que el motor
declara validos— y con la formula equivalente banda a banda.

⚠️ Si `eemont` no esta instalado, el arnes lo dice y sale sin fallar. Es una herramienta de
medicion, no una puerta de aceptacion: no puede bloquear la suite ni la corrida de la nube.
"""
import argparse
import json
import sys

# Indices a contrastar y su nombre en el catalogo de awesome-spectral-indices, que es
# el que eemont consume. Solo los que el motor calcula.
PARES = (
    ('NDVI', 'NDVI'),
    ('PSRI', 'PSRI'),
    ('NDMI', 'NDMI'),
    ('NDRE', 'NDREI'),
)
# Indices donde el motor usa B8A y el catalogo B8. La diferencia es esperada y
# declarada; se informa aparte para no confundirla con un bug.
DIFIEREN_POR_BANDA = {'NDMI', 'NDRE'}
# Por encima de esto, dos implementaciones que dicen calcular lo mismo no lo estan
# haciendo. Es holgado a proposito: diferencias de redondeo y de orden de operaciones
# en GEE viven muy por debajo.
TOLERANCIA = 1e-4


def _eemont():
    try:
        import eemont                                    # noqa: F401
        return True
    except ImportError:
        return False


def comparar(sitio, feat, fecha, escala=20):
    """Devuelve filas (indice, media motor, media eemont, |dif| max, n px)."""
    import ee

    from pix_alerta import focos as fo
    from pix_alerta import series as sr

    geom = fo._geom_lote(sitio, feat)
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
           .filterBounds(geom)
           .filterDate(fecha, str(__import__('pandas').Timestamp(fecha)
                                 + __import__('pandas').Timedelta(days=1))[:10]))
    n = int(col.size().getInfo() or 0)
    if not n:
        return None
    img = ee.Image(col.first())

    # --- lado MOTOR: su propio camino, sin tocar nada ---
    valido = sr._mascara(img)
    mio = sr._indices(img).updateMask(valido)

    # --- lado eemont: su camino, sobre la MISMA imagen y los MISMOS pixeles ---
    # `scale()` y `spectralIndices()` son los dos metodos que eemont agrega. Se
    # enmascara con la mascara DEL MOTOR para que la comparacion sea de FORMULA y no
    # de mascara — si se dejara la de eemont, cualquier diferencia seria ambigua.
    suyo = (img.scale()
            .spectralIndices([c for _, c in PARES])
            .updateMask(valido))

    filas = []
    for propio, ajeno in PARES:
        a = mio.select(propio).rename('a')
        b = suyo.select(ajeno).rename('b')
        dif = a.subtract(b).abs().rename('d')
        r = a.addBands(b).addBands(dif).reduceRegion(
            reducer=(ee.Reducer.mean().combine(ee.Reducer.max(), '', True)
                     .combine(ee.Reducer.count(), '', True)),
            geometry=geom, scale=escala, maxPixels=1e9, bestEffort=True).getInfo()
        filas.append({
            'indice': propio,
            'motor': r.get('a_mean'),
            'eemont': r.get('b_mean'),
            'dif_max': r.get('d_max'),
            'n_px': int(r.get('a_count') or 0),
            'esperada': propio in DIFIEREN_POR_BANDA,
        })
    return filas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cliente', default='TRIGO')
    ap.add_argument('--fecha', required=True, help='YYYY-MM-DD de la escena a contrastar')
    ap.add_argument('--escala', type=int, default=20)
    a = ap.parse_args(argv)

    if not _eemont():
        print('eemont no esta instalado. Este arnes es OPCIONAL: instalalo con')
        print('    pip install eemont')
        print('y volve a correr. La suite y la corrida de la nube no lo necesitan.')
        return 0

    from pix_alerta.ee_init import inicializar
    print('[GEE] %s' % inicializar())
    from pix_alerta import clientes as cl
    clientes = cl.cargar_todos()
    cl.registrar_sitios(clientes)
    cliente = next((c for c in clientes if c.clave == a.cliente), None)
    if cliente is None:
        print('no existe el cliente %s' % a.cliente)
        return 1

    print('\nCONTROL CRUZADO — motor contra eemont, escena del %s' % a.fecha)
    print('Ambos sobre los MISMOS pixeles (la mascara del motor), para que la')
    print('comparacion sea de FORMULA y no de mascara.\n')
    print('%-20s %-6s %10s %10s %10s %8s  %s'
          % ('lote', 'indice', 'motor', 'eemont', 'dif max', 'n px', 'veredicto'))
    print('-' * 92)

    discrepancias = 0
    for s in cliente.sitios:
        with open(s.lotes_geojson, encoding='utf-8') as fh:
            gj = json.load(fh)
        for f in gj['features']:
            lid = str(f['properties'].get(s.campo_id))
            try:
                filas = comparar(s, f, a.fecha, a.escala)
            except Exception as exc:                       # noqa: BLE001
                print('%-20s AVERIA %s: %s' % (lid, type(exc).__name__, str(exc)[:50]))
                continue
            if filas is None:
                print('%-20s sin escena en esa fecha' % lid)
                continue
            for r in filas:
                if r['dif_max'] is None:
                    ver = 'sin pixeles'
                elif r['esperada']:
                    ver = 'difiere: B8A vs B8, DECLARADO'
                elif r['dif_max'] <= TOLERANCIA:
                    ver = 'coincide'
                else:
                    ver = '*** DISCREPANCIA ***'
                    discrepancias += 1
                print('%-20s %-6s %10s %10s %10s %8d  %s'
                      % (lid, r['indice'],
                         '%.5f' % r['motor'] if r['motor'] is not None else '-',
                         '%.5f' % r['eemont'] if r['eemont'] is not None else '-',
                         '%.2e' % r['dif_max'] if r['dif_max'] is not None else '-',
                         r['n_px'], ver))
            lid = ''

    print('\n' + '=' * 92)
    if discrepancias:
        print('%d DISCREPANCIA(S). Dos implementaciones independientes que dicen calcular'
              % discrepancias)
        print('lo mismo dan distinto: una de las dos tiene un bug. Hay que resolverlo')
        print('mirando la formula banda por banda, no eligiendo la que mas guste.')
    else:
        print('Sin discrepancias fuera de las declaradas.')
        print('Las diferencias de NDMI y NDRE son REALES y CORRECTAS: el motor usa B8A')
        print('(nativo 20 m, FWHM 20 nm) donde el catalogo usa B8 (10 m, FWHM 118 nm).')
        print('Ver tests/test_formulas_contra_catalogo.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
