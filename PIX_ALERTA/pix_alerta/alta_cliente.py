"""Alta de cliente: subir la propiedad y los lotes, y que quede listo para la nube.

    python -m pix_alerta.alta_cliente --clave CERRO --titulo "Cerro Alto" \
        --lotes "C:/.../lotes.kmz" --campo-id lote --cultivo soya \
        --campana 2026/2027 2026-10-01 2027-04-30 --K 10 --epsg EPSG:31981

Es lo unico que hace el administrador. Despues de esto la maquina corre sola.

QUE HACE
--------
1. Lee el archivo de lotes (KMZ, KML, SHP, GeoJSON o GPKG — lo que el cliente mande).
2. Lo VALIDA. Un GeoJSON que entra roto no falla acá: falla dentro de la corrida
   programada, tres semanas despues, cuando nadie esta mirando.
3. Lo normaliza a GeoJSON WGS84 y lo guarda dentro del repo, para que la nube lo tenga.
4. Escribe `clientes/<CLAVE>.json`.

LO QUE RECHAZA A PROPOSITO
--------------------------
IDs de lote repetidos o vacios (sin id estable no hay lazo de retorno), geometrias
invalidas o vacias, y areas absurdas. Todo eso se puede arreglar en 5 minutos ahora y
cuesta una campaña si se descubre en enero.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

CLAVE_OK = re.compile(r'^[A-Z][A-Z0-9_]{1,15}$')
CULTIVOS = ('soya', 'trigo', 'maiz', 'sorgo', 'girasol', 'cana_de_azucar', 'pastura')
# Un lote de menos de media hectarea casi siempre es un drenaje o una astilla del
# dibujo, no una unidad de manejo. Uno de mas de 2.000 ha es un bloque sin dividir.
AREA_MIN_HA, AREA_MAX_HA = 0.5, 2000.0


def _sin_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                   if unicodedata.category(c) != 'Mn')


def leer_lotes(ruta, campo_id, epsg_metrico):
    """Lee cualquier formato vectorial y devuelve (GeoJSON WGS84, informe de validacion)."""
    try:
        import geopandas as gpd
    except ImportError:
        raise SystemExit('[ERROR] hace falta geopandas para leer el archivo de lotes.\n'
                         '        pip install geopandas')
    if not os.path.exists(ruta):
        raise SystemExit('[ERROR] no existe el archivo: %s' % ruta)

    try:
        g = gpd.read_file(ruta)
    except Exception as e:
        raise SystemExit('[ERROR] no se pudo leer %s\n        %s' % (ruta, e))

    problemas, avisos = [], []
    if g.empty:
        problemas.append('el archivo no tiene ni una geometria')
        return None, (problemas, avisos, None)

    if campo_id not in g.columns:
        raise SystemExit(
            '[ERROR] el archivo no tiene la columna "%s".\n'
            '        Columnas disponibles: %s\n'
            '        Elegi una con --campo-id.' % (campo_id, ', '.join(map(str, g.columns))))

    if g.crs is None:
        # Sin CRS no se puede reproyectar ni medir. Suponerlo es adivinar.
        problemas.append('el archivo no declara sistema de coordenadas (CRS)')
        return None, (problemas, avisos, None)

    # --- ids ---
    ids = g[campo_id].astype(str).str.strip()
    vacios = int((ids.isin(('', 'nan', 'None', '<NA>'))).sum())
    if vacios:
        problemas.append('%d lote(s) sin id en la columna "%s"' % (vacios, campo_id))
    dup = ids[ids.duplicated(keep=False)]
    if len(dup):
        # Sin id unico y estable no hay forma de rastrear una validacion al lote.
        problemas.append('%d lote(s) con id REPETIDO (%s). El id tiene que ser unico: '
                         'sin eso no se puede cerrar el lazo de retorno.'
                         % (len(dup), ', '.join(sorted(set(dup))[:5])))

    # --- geometrias ---
    nulas = int(g.geometry.isna().sum())
    if nulas:
        problemas.append('%d geometria(s) nula(s)' % nulas)
    g = g[~g.geometry.isna()].copy()
    invalidas = int((~g.geometry.is_valid).sum())
    if invalidas:
        g['geometry'] = g.geometry.buffer(0)      # arreglo estandar de auto-interseccion
        avisos.append('%d geometria(s) invalida(s) reparadas con buffer(0)' % invalidas)
    tipos = set(g.geom_type.unique())
    if not tipos <= {'Polygon', 'MultiPolygon'}:
        problemas.append('hay geometrias que no son poligonos: %s'
                         % ', '.join(sorted(tipos - {'Polygon', 'MultiPolygon'})))

    # --- areas, medidas en metros ---
    try:
        areas = g.to_crs(epsg_metrico).area / 1e4
    except Exception as e:
        problemas.append('no se pudo reproyectar a %s: %s' % (epsg_metrico, e))
        return None, (problemas, avisos, None)
    chicos = int((areas < AREA_MIN_HA).sum())
    grandes = int((areas > AREA_MAX_HA).sum())
    if chicos:
        avisos.append('%d lote(s) de menos de %.1f ha: suelen ser drenajes o astillas '
                      'del dibujo, no unidades de manejo. Revisar.' % (chicos, AREA_MIN_HA))
    if grandes:
        avisos.append('%d lote(s) de mas de %.0f ha: probablemente sean bloques sin '
                      'dividir.' % (grandes, AREA_MAX_HA))

    g = g.to_crs('EPSG:4326')
    g['area_ha'] = areas.round(2).values
    g[campo_id] = ids.values[:len(g)] if len(ids) == len(g) else g[campo_id].astype(str)

    resumen = dict(n=len(g), ha=float(areas.sum()),
                   crs_origen=str(g.crs), bbox=[round(v, 5) for v in g.total_bounds])
    salida = json.loads(g[[campo_id, 'area_ha', 'geometry']].to_json())
    return salida, (problemas, avisos, resumen)


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — alta de cliente')
    p.add_argument('--clave', required=True, help='identificador corto, MAYUSCULAS (ej. CERRO)')
    p.add_argument('--titulo', required=True, help='nombre del cliente para el informe')
    p.add_argument('--lotes', required=True, help='archivo de lotes (kmz/kml/shp/geojson/gpkg)')
    p.add_argument('--campo-id', default='lote', help='columna con el id del lote')
    p.add_argument('--cultivo', default='soya', choices=CULTIVOS)
    p.add_argument('--epsg', default='EPSG:32720', help='CRS metrico de la zona')
    p.add_argument('--campana', nargs=3, action='append', metavar=('NOMBRE', 'DESDE', 'HASTA'),
                   help='ej. --campana 2026/2027 2026-10-01 2027-04-30 (repetible)')
    p.add_argument('--K', type=int, default=None, help='lotes que el cliente puede caminar por ronda')
    p.add_argument('--avisar', default='', help='telefono o canal para el aviso')
    p.add_argument('--raiz', default=None, help='raiz del repo (def: la del paquete)')
    p.add_argument('--forzar', action='store_true', help='sobrescribe un cliente existente')
    a = p.parse_args(argv)

    if not CLAVE_OK.match(a.clave):
        raise SystemExit('[ERROR] --clave debe ser MAYUSCULAS, 2-16 caracteres, sin '
                         'espacios ni tildes (ej. CERRO, SAN_JOSE). Da nombre a la '
                         'carpeta de salida del cliente.')
    raiz = a.raiz or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dir_cli = os.path.join(raiz, 'clientes')
    dir_lot = os.path.join(raiz, 'lotes')
    os.makedirs(dir_cli, exist_ok=True)
    os.makedirs(dir_lot, exist_ok=True)
    destino_json = os.path.join(dir_cli, '%s.json' % a.clave)
    if os.path.exists(destino_json) and not a.forzar:
        raise SystemExit('[ERROR] ya existe %s. Usa --forzar para reemplazarlo.' % destino_json)

    print('Leyendo %s ...' % a.lotes)
    gj, (problemas, avisos, resumen) = leer_lotes(a.lotes, a.campo_id, a.epsg)

    if problemas:
        print('\n[RECHAZADO] el archivo de lotes tiene problemas que hay que arreglar:')
        for x in problemas:
            print('   - ' + x)
        print('\nNo se dio de alta el cliente. Estos errores no fallan ahora: fallan')
        print('dentro de la corrida programada, semanas despues, sin nadie mirando.')
        return 1

    for x in avisos:
        print('   [aviso] ' + x)

    ruta_lotes = os.path.join(dir_lot, '%s.geojson' % a.clave.lower())
    with open(ruta_lotes, 'w', encoding='utf-8') as fh:
        json.dump(gj, fh, ensure_ascii=False)

    campanas = {}
    for nom, d1, d2 in (a.campana or []):
        campanas[nom] = [d1, d2]
    if not campanas:
        print('\n   [aviso] sin campañas declaradas: el motor va a correr todo el año.')
        print('           Fuera de campaña no distingue cosecha de deterioro (en madurez')
        print('           el dosel se seca y senesce, que es la firma que busca).')

    cliente = {
        'clave': a.clave,
        'titulo': a.titulo,
        'activo': True,
        'sitios': [{
            'clave': '%s_PRINCIPAL' % a.clave,
            'titulo': a.titulo,
            'lotes_geojson': '../lotes/%s.geojson' % a.clave.lower(),
            'campo_id': a.campo_id,
            'cultivo': a.cultivo,
            'epsg_metrico': a.epsg,
            'campanas': campanas,
        }],
        'entrega': {'cadencia_dias': 10},
        'marca': {'nombre': a.titulo},
    }
    if a.K:
        cliente['K'] = a.K
    if a.avisar:
        cliente['entrega']['avisar'] = a.avisar
    with open(destino_json, 'w', encoding='utf-8') as fh:
        json.dump(cliente, fh, ensure_ascii=False, indent=2)

    # Se relee con el loader real: si el archivo que acabo de escribir no pasa su
    # propia validacion, mejor enterarse ahora que en el primer cron.
    sys.path.insert(0, raiz)
    from pix_alerta import clientes as cl
    try:
        c = [x for x in cl.cargar_todos(dir_cli, solo_activos=False) if x.clave == a.clave][0]
    except Exception as e:
        raise SystemExit('[ERROR] el cliente quedo mal escrito: %s' % e)

    print('\n' + '=' * 64)
    print('ALTA OK — %s (%s)' % (c.titulo, c.clave))
    print('=' * 64)
    print('  lotes            : %d  ·  %.1f ha' % (resumen['n'], resumen['ha']))
    print('  cultivo          : %s' % a.cultivo)
    print('  campañas         : %s' % (', '.join(campanas) or 'ninguna declarada'))
    print('  K (scouting)     : %s' % (a.K or 'sin declarar'))
    print('  lotes guardados  : %s' % ruta_lotes)
    print('  cliente          : %s' % destino_json)
    print('\nSiguiente paso: commitear y pushear. La corrida programada lo toma sola.')
    print('  git add clientes lotes && git commit -m "alta %s" && git push' % a.clave)
    return 0


if __name__ == '__main__':
    sys.exit(main())
