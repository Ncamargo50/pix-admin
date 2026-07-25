# -*- coding: utf-8 -*-
"""Chequeo de puesta en marcha: que falta para que la maquina funcione sola.

    python scripts/verificar_setup.py

Contesta una sola pregunta: **si el cron corriera ahora, entregaria?** Revisa cada
eslabon por separado y dice cual esta roto y como se arregla, en vez de dejar que la
corrida programada falle a las 7 de la mañana sin nadie mirando.

Sale con 0 si todo lo BLOQUEANTE esta, 1 si falta algo.
"""
import importlib
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

OK, FALTA, AVISO = 'OK   ', 'FALTA', 'aviso'
_r = []


def chk(estado, titulo, detalle='', arreglo=''):
    _r.append((estado, titulo, detalle, arreglo))


def dependencias():
    faltan = []
    for m, pip in (('ee', 'earthengine-api'), ('geopandas', 'geopandas'),
                   ('shapely', 'shapely'), ('pandas', 'pandas'),
                   ('reportlab', 'reportlab')):
        try:
            importlib.import_module(m)
        except ImportError:
            faltan.append(pip)
    if faltan:
        chk(FALTA, 'Dependencias de Python', 'no estan: %s' % ', '.join(faltan),
            'pip install -r requirements.txt')
    else:
        chk(OK, 'Dependencias de Python')


def earth_engine():
    """Lo que mas cuesta diagnosticar despues: sin esto no hay imagenes, y punto."""
    key = os.environ.get('GEE_SA_KEY')
    try:
        import ee
    except ImportError:
        return chk(FALTA, 'Earth Engine', 'falta earthengine-api')
    try:
        if key and os.path.exists(key):
            with open(key, encoding='utf-8') as fh:
                sa = json.load(fh)['client_email']
            ee.Initialize(ee.ServiceAccountCredentials(sa, key))
            chk(OK, 'Earth Engine', 'cuenta de servicio %s' % sa)
        else:
            ee.Initialize()
            chk(OK, 'Earth Engine', 'credencial local del usuario')
            if not key:
                chk(AVISO, 'Credencial de servicio para la nube',
                    'aca funciona con tu credencial personal, pero el runner de GitHub '
                    'necesita el secreto GEE_SA_JSON',
                    'cargar GEE_SA_JSON en Settings > Secrets > Actions')
    except Exception as e:
        chk(FALTA, 'Earth Engine', '%s: %s' % (type(e).__name__, str(e)[:90]),
            'revisar la cuenta de servicio y que el proyecto tenga GEE habilitado')


def clientes():
    from pix_alerta import clientes as cl
    try:
        cs = cl.cargar_todos()
    except Exception as e:
        return chk(FALTA, 'Clientes declarados', str(e)[:140],
                   'corregir el archivo del cliente en clientes/')
    if not cs:
        return chk(FALTA, 'Clientes declarados', 'no hay ninguno activo',
                   'python -m pix_alerta.alta_cliente --clave ... (ver NUBE.md)')
    chk(OK, 'Clientes declarados', '%d activo(s): %s'
        % (len(cs), ', '.join(c.clave for c in cs)))

    for c in cs:
        if not c.K:
            chk(AVISO, 'K de %s' % c.clave,
                'sin declarar: el ranking no se corta por capacidad de scouting',
                'agregar "K": <n> en clientes/%s.json' % c.clave)
        for s in c.sitios:
            if not os.path.exists(s.lotes_geojson):
                chk(FALTA, 'Lotes de %s' % s.clave,
                    'no existe %s' % s.lotes_geojson,
                    'volver a dar de alta el cliente')
                continue
            try:
                with open(s.lotes_geojson, encoding='utf-8') as fh:
                    gj = json.load(fh)
                ids = [str((f.get('properties') or {}).get(s.campo_id))
                       for f in gj.get('features', [])]
                dup = {i for i in ids if ids.count(i) > 1}
                if dup:
                    chk(FALTA, 'Lotes de %s' % s.clave,
                        'ids repetidos: %s' % ', '.join(sorted(dup)[:4]),
                        'sin id unico no se puede rastrear lo que registra el tecnico')
                else:
                    chk(OK, 'Lotes de %s' % s.clave, '%d lotes' % len(ids))
            except Exception as e:
                chk(FALTA, 'Lotes de %s' % s.clave, str(e)[:100])
            if not s.campanas:
                chk(AVISO, 'Campañas de %s' % s.clave,
                    'sin declarar: el motor va a correr todo el año, y fuera de campaña '
                    'no distingue cosecha de deterioro')


def nube():
    wf = os.path.join(RAIZ, '.github', 'workflows', 'monitor.yml')
    chk(OK if os.path.exists(wf) else FALTA, 'Workflow de la nube',
        'monitor.yml' if os.path.exists(wf) else 'no existe',
        '' if os.path.exists(wf) else 'ver NUBE.md')
    req = os.path.join(RAIZ, 'requirements.txt')
    chk(OK if os.path.exists(req) else FALTA, 'requirements.txt')


def app_de_campo():
    """La app es el otro extremo: sin esto el tecnico no recibe nada y nada vuelve."""
    cfgjs = os.path.abspath(os.path.join(RAIZ, '..', 'PIX_SCOUT', 'app', 'js', 'config.js'))
    if not os.path.exists(cfgjs):
        return chk(AVISO, 'App de campo', 'no se encontro PIX_SCOUT/app/js/config.js')
    s = open(cfgjs, encoding='utf-8').read()
    def val(k):
        import re
        m = re.search(k + r":\s*'([^']*)'", s)
        return m.group(1) if m else None
    if val('FOCOS_ENDPOINT'):
        chk(OK, 'La app baja los focos sola', val('FOCOS_ENDPOINT')[:60])
    else:
        chk(FALTA, 'La app baja los focos sola', 'FOCOS_ENDPOINT vacio',
            'apuntarlo a entregas/{campo}/ultimo y recompilar el APK (ver NUBE.md)')
    if val('SUPABASE_URL'):
        chk(OK, 'Lo que registra el tecnico vuelve al servidor')
    else:
        chk(FALTA, 'Lo que registra el tecnico vuelve al servidor',
            'SUPABASE_URL vacio: las validaciones quedan en el telefono',
            'correr backend/001_scout_validaciones.sql y pegar las 2 credenciales')
    if 'MODO_CIEGO: false' in s:
        chk(AVISO, 'Modo ciego',
            'apagado. Encenderlo para la campaña de validacion: si el tecnico sabe que '
            'va a un rojo, encuentra algo')


def main():
    print('=' * 70)
    print('PIXADVISOR MONITOR — chequeo de puesta en marcha')
    print('=' * 70)
    for f in (dependencias, earth_engine, clientes, nube, app_de_campo):
        try:
            f()
        except Exception as e:
            chk(FALTA, f.__name__, '%s: %s' % (type(e).__name__, str(e)[:90]))

    print()
    for estado, titulo, detalle, arreglo in _r:
        marca = {OK: '  [OK]   ', FALTA: '  [FALTA]', AVISO: '  [aviso]'}[estado]
        print('%s %s%s' % (marca, titulo, (' — ' + detalle) if detalle else ''))
        if arreglo:
            print('           -> %s' % arreglo)

    faltan = [x for x in _r if x[0] == FALTA]
    avisos = [x for x in _r if x[0] == AVISO]
    print()
    print('-' * 70)
    if faltan:
        print('NO esta lista: %d cosa(s) bloqueante(s).' % len(faltan))
    else:
        print('La maquina puede correr. %d aviso(s) no bloqueante(s).' % len(avisos))
    return 1 if faltan else 0


if __name__ == '__main__':
    sys.exit(main())
