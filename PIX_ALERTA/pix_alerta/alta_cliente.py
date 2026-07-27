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
# La clave de PROPIEDAD puede ser mas larga que la de cliente: nombra entregables
# (`ranking_<SITIO>_<fecha>.csv`), no carpetas, y recortarla de mas hace que dos
# haciendas distintas caigan en la misma clave.
SITIO_CLAVE_OK = re.compile(r'^[A-Z][A-Z0-9_]{1,31}$')
CULTIVOS = ('soya', 'trigo', 'maiz', 'sorgo', 'girasol', 'cana_de_azucar', 'pastura')
# Un lote de menos de media hectarea casi siempre es un drenaje o una astilla del
# dibujo, no una unidad de manejo. Uno de mas de 2.000 ha es un bloque sin dividir.
AREA_MIN_HA, AREA_MAX_HA = 0.5, 2000.0
# Minimo de lotes para que la mediana de cohorte describa algo. Es el MIN_LOTES_COHORTE
# del criterio: por debajo, el motor corre y no emite.
MIN_LOTES_UTIL = 8


def _sin_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s))
                   if unicodedata.category(c) != 'Mn')


def _slug(s, largo=24):
    """Nombre de propiedad -> pedazo de clave. 'Santo Antonio' -> 'SANTO_ANTONIO'.

    Si el recorte hace que dos haciendas caigan en la misma clave, NO se resuelve
    solo: el alta rechaza el duplicado y pide `--sitio-clave`. Silenciar eso seria
    mezclar dos campos en un mismo entregable.
    """
    t = _sin_tildes(s).upper()
    t = re.sub(r'[^A-Z0-9]+', '_', t).strip('_')
    return (t[:largo].rstrip('_') or 'SITIO')


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
    # El criterio compara cada lote contra la MEDIANA DE SU COHORTE. Con pocos lotes esa
    # mediana no describe nada y el motor no emite: el cliente correria un mes entero
    # recibiendo entregas vacias. Mejor saberlo ahora que en la tercera semana.
    if len(g) < MIN_LOTES_UTIL:
        avisos.append(
            'SOLO %d lote(s). El criterio compara cada lote contra la mediana de su '
            'cohorte y necesita al menos %d para que esa mediana signifique algo: con '
            'menos, la maquina va a correr y NO va a emitir ranking. Para un campo de '
            'esta escala el producto adecuado es el motor de rasteres, no el ranking '
            'de lotes.' % (len(g), MIN_LOTES_UTIL))

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
    # Alternativa a --campana: el tecnico sabe CUANDO SEMBRO, no entre que fechas
    # conviene mirar. La ventana sale del ciclo del cultivo (ver ciclos.py).
    p.add_argument('--siembra', default='', metavar='YYYY-MM-DD',
                   help='fecha de siembra: deriva la ventana con el ciclo del cultivo')
    p.add_argument('--ciclo-dias', type=int, default=None,
                   help='dias de ciclo, si el cultivar no es el tipico')
    p.add_argument('--K', type=int, default=None, help='lotes que el cliente puede caminar por ronda')
    p.add_argument('--avisar', default='', help='telefono o canal para el aviso')
    # A quien se le entrega. El whatsapp es operativo: es el numero al que el cron
    # manda el aviso de ESTE cliente.
    p.add_argument('--contacto', default='', help='nombre de la persona de contacto')
    p.add_argument('--whatsapp', default='', help='numero en formato internacional')
    p.add_argument('--email', default='', help='correo del contacto')
    p.add_argument('--documento', default='', help='CNPJ / NIT / documento fiscal')
    # El inventario de lotes casi siempre trae unidades que NO son cultivo. Sin este
    # filtro el ranking manda al tecnico al monte o a la pista de aterrizaje: paso de
    # verdad, "PISTA" (2,78 ha) salio PRIMERA en la corrida del 2026-05-06.
    p.add_argument('--unidades', default='', help='CSV que clasifica cada lote')
    p.add_argument('--excluir', nargs='*', default=[],
                   help='categorias a excluir del CSV (ej. MONTE_FOREST PASTO_O_COBERTURA)')
    p.add_argument('--raiz', default=None, help='raiz del repo (def: la del paquete)')
    # Una propiedad (hacienda) del cliente. Un cliente puede tener varias, cada una
    # con su archivo de lotes, su cultivo y su siembra.
    p.add_argument('--propiedad', default='',
                   help='nombre de la hacienda (def: el nombre del cliente)')
    p.add_argument('--sitio-clave', default='',
                   help='clave de la propiedad (def: derivada del nombre)')
    p.add_argument('--reemplazar-propiedad', action='store_true',
                   help='pisa SOLO esta propiedad, conserva las demas del cliente')
    p.add_argument('--forzar', action='store_true',
                   help='REEMPLAZA el cliente entero, con todas sus propiedades')
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

    # --- que hacemos si el cliente ya existe ------------------------------------
    # El orden importa: primero se verifica de QUIEN es la clave. Si se valida antes
    # el nombre de la propiedad, un intento de reusar la clave de otro cliente falla
    # por el motivo equivocado y el operador no se entera del choque real.
    previo = None
    if os.path.exists(destino_json) and not a.forzar:
        with open(destino_json, encoding='utf-8') as fh:
            previo = json.load(fh)
        # Reusar la clave de OTRO cliente mezclaria dos carteras en una carpeta. Es
        # el mismo tipo de error que persigue el chequeo de aislamiento, y hay que
        # cazarlo acá, no cuando el informe llegue al productor equivocado.
        if previo.get('titulo') and previo['titulo'] != a.titulo:
            raise SystemExit(
                '[ERROR] la clave %s ya es de "%s" y vos mandaste "%s".\n'
                '        Si son el mismo cliente, usa el nombre que ya tiene.\n'
                '        Si son clientes distintos, elegi otra clave.'
                % (a.clave, previo['titulo'], a.titulo))

    propiedad = a.propiedad or a.titulo
    sitio_clave = a.sitio_clave or '%s_%s' % (a.clave, _slug(propiedad))
    if not SITIO_CLAVE_OK.match(sitio_clave):
        raise SystemExit('[ERROR] la clave de propiedad "%s" no sirve: tiene que ser '
                         'MAYUSCULAS, 2-32 caracteres, sin espacios ni tildes. Pasala '
                         'a mano con --sitio-clave.' % sitio_clave)

    if previo is not None:
        ya = [s.get('clave') for s in previo.get('sitios', [])]
        if sitio_clave in ya and not a.reemplazar_propiedad:
            raise SystemExit(
                '[ERROR] %s ya tiene la propiedad "%s".\n'
                '        Para actualizarla: --reemplazar-propiedad\n'
                '        Para agregar otra distinta: --propiedad "Nombre de la otra"'
                % (a.clave, sitio_clave))

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

    # El CSV de clasificacion se copia al repo: en la nube no existe el Escritorio.
    ruta_unidades = ''
    if a.unidades:
        if not os.path.exists(a.unidades):
            raise SystemExit('[ERROR] no existe el CSV de unidades: %s' % a.unidades)
        import shutil
        # Por PROPIEDAD, no por cliente: con el nombre del cliente, la segunda
        # hacienda le pisaba los lotes a la primera y el cliente quedaba corriendo
        # dos veces sobre el mismo campo sin que nada fallara.
        ruta_unidades = os.path.join(dir_lot, '%s_unidades.csv' % sitio_clave.lower())
        shutil.copy2(a.unidades, ruta_unidades)

    ruta_lotes = os.path.join(dir_lot, '%s.geojson' % sitio_clave.lower())
    with open(ruta_lotes, 'w', encoding='utf-8') as fh:
        json.dump(gj, fh, ensure_ascii=False)

    campanas = {}
    for nom, d1, d2 in (a.campana or []):
        campanas[nom] = [d1, d2]
    # La siembra deriva la ventana. Una campaña escrita a mano gana: puede reflejar
    # algo que el cliente sabe y la tabla de ciclos no.
    if not campanas and a.siembra:
        from pix_alerta import ciclos
        try:
            campanas = {k: list(v) for k, v in ciclos.campanas_desde_siembra(
                a.cultivo, a.siembra, a.ciclo_dias).items()}
        except ValueError as e:
            raise SystemExit('[ERROR] %s' % e)
        print('\n   ' + ciclos.describir(a.cultivo, a.siembra, a.ciclo_dias))
    if not campanas:
        print('\n   [aviso] sin campañas declaradas: el motor va a correr todo el año.')
        print('           Fuera de campaña no distingue cosecha de deterioro (en madurez')
        print('           el dosel se seca y senesce, que es la firma que busca).')

    sitio = {
        'clave': sitio_clave,
        'titulo': propiedad,
        'lotes_geojson': '../lotes/%s.geojson' % sitio_clave.lower(),
        'campo_id': a.campo_id,
        'cultivo': a.cultivo,
        'epsg_metrico': a.epsg,
        'campanas': campanas,
    }
    if a.siembra:
        # Se guarda ademas de la ventana: la proxima campaña se re-deriva con solo
        # cambiar esta fecha, y el informe puede decir de que siembra habla.
        sitio['siembra'] = a.siembra
    if a.ciclo_dias:
        sitio['ciclo_dias'] = a.ciclo_dias
    if ruta_unidades:
        sitio['unidades_csv'] = '../lotes/%s_unidades.csv' % sitio_clave.lower()
        sitio['categorias_excluidas'] = list(a.excluir)
        if not a.excluir:
            print('   [aviso] se paso --unidades sin --excluir: el filtro no descarta nada.')

    if previo is not None:
        # AGREGAR una propiedad a un cliente que ya existe. Se parte de la ficha
        # guardada para no perder las otras haciendas ni los datos de contacto que
        # este alta no trae.
        cliente = dict(previo)
        sitios = [s for s in cliente.get('sitios', [])
                  if s.get('clave') != sitio_clave]
        n_antes = len(cliente.get('sitios', []))
        sitios.append(sitio)
        cliente['sitios'] = sitios
        accion = ('PROPIEDAD REEMPLAZADA' if len(sitios) == n_antes
                  else 'PROPIEDAD AGREGADA')
    else:
        cliente = {
            'clave': a.clave,
            'titulo': a.titulo,
            'activo': True,
            'sitios': [sitio],
            'entrega': {'cadencia_dias': 10},
            'marca': {'nombre': a.titulo},
        }
        accion = 'ALTA OK'
    # Lo que este alta trae explicitamente actualiza; lo que no viene, no se pisa.
    if a.K:
        cliente['K'] = a.K
    if a.avisar:
        cliente.setdefault('entrega', {})['avisar'] = a.avisar
    contacto = {k: v for k, v in (
        ('nombre', a.contacto), ('whatsapp', a.whatsapp),
        ('email', a.email), ('documento', a.documento)) if v}
    if contacto:
        cliente['contacto'] = dict(cliente.get('contacto', {}), **contacto)
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
    print('%s — %s (%s)' % (accion, c.titulo, c.clave))
    print('=' * 64)
    print('  propiedad        : %s (%s)' % (propiedad, sitio_clave))
    print('  lotes            : %d  ·  %.1f ha' % (resumen['n'], resumen['ha']))
    print('  cultivo          : %s' % a.cultivo)
    print('  campañas         : %s' % (', '.join(campanas) or 'ninguna declarada'))
    print('  K (scouting)     : %s' % (a.K or 'sin declarar'))
    print('  lotes guardados  : %s' % ruta_lotes)
    if len(c.sitios) > 1:
        print('\n  %s tiene ahora %d propiedades:' % (c.clave, len(c.sitios)))
        for s in c.sitios:
            print('    · %-22s %-14s %s' % (s.titulo, s.clave, s.cultivo or '-'))
    print('  cliente          : %s' % destino_json)
    print('\nSiguiente paso: commitear y pushear. La corrida programada lo toma sola.')
    print('  git add clientes lotes && git commit -m "alta %s" && git push' % a.clave)
    return 0


if __name__ == '__main__':
    sys.exit(main())
