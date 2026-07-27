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


# Un rotulo por codigo. "NO EVALUABLE" tiene que LEERSE distinto de "sin novedad":
# son la misma pantalla para el cliente y significan lo contrario.
_ROTULO = {m.ENTREGADO: 'ENTREGADO', m.SIN_NOVEDAD: 'sin novedad',
           m.NO_EVALUABLE: 'NO EVALUABLE', m.FUERA_CAMPANA: 'fuera de campana'}


def _resumen(fila):
    est = _ROTULO.get(fila['rc'], 'FALLO')
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
            # Sin esto no habia forma de apagar el acercamiento ni el radar en la
            # nube: el cron llama a correr_todos, no a main, y ambos suman llamadas
            # a Earth Engine y tiempo de job en cada corrida.
            if getattr(args, 'sin_focos', False):
                argv += ['--sin-focos']
            if getattr(args, 'sin_radar', False):
                argv += ['--sin-radar']
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
# focos_<SITIO>_<fecha>.geojson · Informe_<SITIO>_<fecha>.pdf
#
# TODO entregable tiene que estar en esta lista. Un prefijo que falta no da error:
# `sitio_de_archivo` devuelve None, el archivo queda FUERA del chequeo de aislamiento
# y un entregable en la carpeta del cliente equivocado pasa sin que nadie lo vea. Es
# lo que le paso a `focos_` cuando se sumo el acercamiento.
_PREFIJOS = ('ranking_', 'lotes_', 'serie_', 'focos_', 'Informe_',
             'muestra_', 'campana_', 'dimensionamiento_')
_EXTENSIONES = ('.csv', '.geojson', '.pdf', '.txt')
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
    if ext not in _EXTENSIONES:
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
        # RECURSIVO. `os.listdir` plano no veia `ultimo/`, que es justo la carpeta
        # que descarga el telefono: se podian plantar tres archivos de otro cliente
        # ahi adentro y el verificador no reportaba nada.
        for raiz, _dirs, noms in os.walk(d):
            for nom in sorted(noms):
                sitio = sitio_de_archivo(nom)
                if sitio is None:
                    continue
                if sitio not in propios:
                    rel = os.path.relpath(os.path.join(raiz, nom), d)
                    problemas.append('%s tiene "%s" (sitio %s), que no es de ninguno '
                                     'de sus sitios (%s)'
                                     % (d, rel, sitio,
                                        ', '.join(sorted(propios)) or 'ninguno'))
    return problemas


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — corrida multi-cliente')
    p.add_argument('--cliente', default=None, help='correr solo este (def: todos los activos)')
    p.add_argument('--hasta', default=str(date.today()))
    p.add_argument('--desde', default=None)
    p.add_argument('--K', type=int, default=None, help='pisa el K de todos los clientes')
    p.add_argument('--salida', default='salida')
    p.add_argument('--sin-focos', action='store_true',
                   help='no corre el acercamiento intra-lote en ningun cliente')
    p.add_argument('--sin-radar', action='store_true',
                   help='no consulta Sentinel-1 en ningun cliente')
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

    fallos = [f for f in filas if f['rc'] not in m.NO_FALLO]
    entregas = [f for f in filas if f['rc'] == m.ENTREGADO]
    ciegos = [f for f in filas if f['rc'] == m.NO_EVALUABLE]

    problemas = verificar_aislamiento(todos, a.salida)
    if problemas:
        # Esto es mas grave que un fallo de corrida: son datos de un cliente en la
        # carpeta de otro. Se reporta arriba de todo y tiñe la corrida de fallo.
        print('\n[AISLAMIENTO VIOLADO]')
        for pr in problemas:
            print('  ' + pr)

    sin_nov = len(filas) - len(entregas) - len(fallos) - len(ciegos)
    print('\n%d entregable(s), %d sin novedad, %d NO EVALUABLE(S), %d fallo(s)'
          % (len(entregas), sin_nov, len(ciegos), len(fallos)))
    if ciegos:
        # Que no pase inadvertido en el log: un sitio que no se pudo evaluar no es un
        # sitio tranquilo. Si esto se repite ronda tras ronda, el cliente esta pagando
        # por un monitoreo que no lo esta mirando.
        print('\n[NO EVALUABLE] el motor NO pudo mirar estos sitios. No es que esten '
              'sin novedad:')
        for f in ciegos:
            print('  · %s / %s' % (f['cliente'], f['sitio']))
        print('  Sin escenas utiles no hay criterio que calcular. Si se repite, '
              'revisar la ventana de campaña y la nubosidad de la zona.')

    if fallos or problemas:
        return 1
    if entregas:
        return m.ENTREGADO
    # NO_EVALUABLE TIENE QUE CRUZAR EL BORDE DEL PROCESO.
    # El codigo de salida es lo unico que ve la maquina: el bloque `[NO EVALUABLE]`
    # de arriba se imprime en un log que nadie abre si el job sale verde. Devolver 0
    # aca fundia otra vez los dos estados que `main` acababa de separar —una capa mas
    # afuera— y el workflow (`RC != '10' && RC != '0'`) daba el job por bueno.
    # Auditado 2026-07-27.
    if ciegos:
        return m.NO_EVALUABLE
    return 0


if __name__ == '__main__':
    sys.exit(main())
