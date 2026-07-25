"""Corrida multi-cliente: una pasada por todos los clientes activos.

    python -m pix_alerta.correr_todos --hasta 2026-04-30
    python -m pix_alerta.correr_todos --cliente HDS --serie serie_HDS.csv

Es lo que va en el cron. Sustituye al patron actual del pipeline de rasteres, donde el
cron procesa dos haciendas fijas de un unico dueño y `check_new` exige que la escena este
presente en AMBAS: con clientes en zonas distintas eso no converge nunca.

DOS PROPIEDADES QUE NO SE NEGOCIAN
1. AISLAMIENTO: cada cliente escribe solo en `<salida>/<clave>/`. Se verifica despues de
   correr, no se confia en que cada modulo se porte bien.
2. UN CLIENTE QUE FALLA NO FRENA A LOS DEMAS. Si la hacienda de uno tiene el GeoJSON roto,
   los otros igual reciben su informe. El fallo se REPORTA, no se traga.

Codigos de salida (mismo contrato que main.py):
    0  = nadie tenia nada nuevo que entregar
    10 = al menos un cliente genero entregable y ninguno fallo
    1  = al menos un cliente fallo (aunque otros hayan entregado)
"""
import argparse
import os
import re
import sys
import traceback
from datetime import date

from . import clientes as cl
from . import main as m


def _resumen(fila):
    est = {0: 'sin novedad', 10: 'ENTREGADO'}.get(fila['rc'], 'FALLO')
    linea = '  %-10s %-28s %-12s' % (fila['cliente'], fila['sitio'][:28], est)
    if fila.get('error'):
        linea += ' :: ' + fila['error'][:90]
    return linea


def correr_cliente(c, args):
    """Corre todos los sitios de un cliente. Devuelve una fila por sitio."""
    filas = []
    destino = c.salida(args.salida)
    os.makedirs(destino, exist_ok=True)
    for s in c.sitios:
        fila = {'cliente': c.clave, 'sitio': s.clave, 'rc': 1, 'error': None}
        try:
            argv = ['--sitio', s.clave, '--hasta', args.hasta, '--salida', destino]
            if args.desde:
                argv += ['--desde', args.desde]
            # K sale del cliente, no de una constante global: es SU capacidad de
            # scouting. Un K prestado de otro cliente corta el ranking donde no va.
            K = args.K if args.K is not None else c.K
            if K:
                argv += ['--K', str(K)]
            if args.serie:
                argv += ['--serie', args.serie]
            fila['rc'] = m.main(argv)
        except SystemExit as e:                 # argparse aborta con SystemExit
            fila['rc'] = 1
            fila['error'] = 'argumentos invalidos (SystemExit %s)' % e.code
        except Exception as e:
            # Se captura a proposito: el objetivo es que los demas clientes corran igual.
            fila['rc'] = 1
            fila['error'] = '%s: %s' % (type(e).__name__, e)
            if args.trazas:
                traceback.print_exc()
        filas.append(fila)
    return filas


# ranking_<SITIO>_<fecha>.csv · lotes_<SITIO>_<fecha>.geojson · serie_<SITIO>.csv
_PREFIJOS = ('ranking_', 'lotes_', 'serie_')
_RE_FECHA = re.compile(r'_\d{4}-\d{2}-\d{2}$')


def sitio_de_archivo(nom):
    """Clave del sitio a partir del nombre del entregable. None si no lo emite el motor.

    OJO: la clave de sitio PUEDE llevar guion bajo (`TEST_A`, `SANTO_ANTONIO`), asi que
    partir por '_' y tomar el segundo pedazo devuelve `TEST` y marca como ajeno un
    archivo propio. Un chequeo de aislamiento que da falsas alarmas se termina apagando,
    y ahi si se filtran datos de verdad. Se saca el prefijo y la fecha del final, y lo
    que queda ES la clave.
    """
    base, ext = os.path.splitext(nom)
    if ext not in ('.csv', '.geojson'):
        return None
    for pref in _PREFIJOS:
        if base.startswith(pref):
            return _RE_FECHA.sub('', base[len(pref):]) or None
    return None


def verificar_aislamiento(clientes, base):
    """Ningun archivo de un cliente puede estar en la carpeta de otro.

    Se comprueba la clave de sitio del nombre del archivo contra los sitios que el
    cliente realmente declara. Es barato y atrapa el error que importa: un entregable
    con los lotes de otro productor.
    """
    problemas = []
    for c in clientes:
        propios = {s.clave for s in c.sitios}
        d = c.salida(base)
        if not os.path.isdir(d):
            continue
        for nom in sorted(os.listdir(d)):
            sitio = sitio_de_archivo(nom)
            if sitio is None:
                continue
            if sitio not in propios:
                problemas.append('%s tiene "%s" (sitio %s), que no es de ninguno de sus '
                                 'sitios (%s)'
                                 % (d, nom, sitio, ', '.join(sorted(propios)) or 'ninguno'))
    return problemas


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — corrida multi-cliente')
    p.add_argument('--cliente', default=None, help='correr solo este (def: todos los activos)')
    p.add_argument('--hasta', default=str(date.today()))
    p.add_argument('--desde', default=None)
    p.add_argument('--K', type=int, default=None, help='pisa el K de todos los clientes')
    p.add_argument('--salida', default='salida')
    p.add_argument('--serie', default=None, help='CSV ya extraido (solo con --cliente)')
    p.add_argument('--carpeta-clientes', default=None)
    p.add_argument('--trazas', action='store_true', help='imprime el traceback completo')
    a = p.parse_args(argv)

    todos = cl.cargar_todos(a.carpeta_clientes)
    cl.registrar_sitios(todos)
    if a.cliente:
        todos = [c for c in todos if c.clave == a.cliente]
        if not todos:
            print('[ERROR] no hay cliente activo con clave %r' % a.cliente)
            return 1
    if not todos:
        print('[NO-OP] no hay clientes activos declarados en la carpeta de clientes.')
        return 0
    if a.serie and len(todos) > 1:
        # Una serie ya extraida pertenece a UN sitio. Reusarla para todos escribiria el
        # ranking de un cliente con los datos de otro.
        print('[ERROR] --serie solo se puede usar junto con --cliente (es de un sitio).')
        return 1

    print('PIX ALERTA — %d cliente(s) activo(s), corte %s' % (len(todos), a.hasta))
    filas = []
    for c in todos:
        print('\n=== %s (%s) — %d sitio(s) ===' % (c.titulo, c.clave, len(c.sitios)))
        filas += correr_cliente(c, a)

    print('\n' + '=' * 72)
    print('RESUMEN')
    for f in filas:
        print(_resumen(f))

    fallos = [f for f in filas if f['rc'] not in (0, 10)]
    entregas = [f for f in filas if f['rc'] == 10]

    problemas = verificar_aislamiento(todos, a.salida)
    if problemas:
        # Esto es mas grave que un fallo de corrida: son datos de un cliente en la
        # carpeta de otro. Se reporta arriba de todo y tiñe la corrida de fallo.
        print('\n[AISLAMIENTO VIOLADO]')
        for pr in problemas:
            print('  ' + pr)

    print('\n%d entregable(s), %d sin novedad, %d fallo(s)'
          % (len(entregas), len(filas) - len(entregas) - len(fallos), len(fallos)))

    if fallos or problemas:
        return 1
    return 10 if entregas else 0


if __name__ == '__main__':
    sys.exit(main())
