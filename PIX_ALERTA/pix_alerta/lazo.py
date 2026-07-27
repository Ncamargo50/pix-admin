# -*- coding: utf-8 -*-
"""EL LAZO DE RETORNO: lo que el tecnico registro vuelve al motor.

    python -m pix_alerta.lazo --sitio HDS --ronda 2026-11-12 --agregar

Sin esto no hay NINGUN numero propio: la precision del sistema —de los lotes a los
que mando, cuantos tenian problema— es la unica metrica que el producto vende y no
se puede calcular sin que el registro del tecnico vuelva.

POR QUE HACIA FALTA UN MODULO Y NO SOLO LAS CREDENCIALES
--------------------------------------------------------
Auditado 2026-07-26: aunque se pegaran las credenciales, el lazo NO cerraba. La app
manda `focoId`, `estrato`, `lote` y `hallazgo` (texto); `campana.agregar` espera
`lote_id` y `hubo_problema` (booleano). **`hubo_problema` no tenia productor en
ningun lado del repositorio.** Este modulo es el puente, y hace las tres
traducciones que faltaban:

    focoId / lote      ->  lote_id
    hallazgo != 'nada' ->  hubo_problema
    focoIdEstable      ->  se DESCARTA el registro si es False

La tercera es la que mas importa. Un `focoIdEstable=False` significa que la app
cayo a ids POSICIONALES (F-1, F-2...), que se renumeran en cada ronda porque el
orden de visita se baraja: ese registro apunta a un lote distinto cada semana y
meterlo al acumulado contamina la precision con observaciones mal atribuidas. Se
descarta y se cuenta, nunca se adivina.

LA CREDENCIAL QUE HACE FALTA ACA NO ES LA DE LA APP
---------------------------------------------------
La tabla es APPEND-ONLY para `anon` a proposito (`001_scout_validaciones.sql`):
con la anon key —que viaja DENTRO del APK y por lo tanto es publica— se puede
INSERT pero **no SELECT**. Para LEER hace falta la `service_role` key, que es
secreta y vive del lado del servidor. Son credenciales distintas:

    APK  (`PIX_SCOUT/app/js/config.js`)  -> SUPABASE_URL + SUPABASE_ANON_KEY
    motor (variable de entorno / secreto) -> SUPABASE_URL + SUPABASE_SERVICE_KEY

DOS FORMATOS DE CLAVE, LOS DOS VALIDOS
--------------------------------------
Supabase renombro las claves. Los ROLES son los mismos; cambia el rotulo:

    rol           formato nuevo (panel actual)   formato legado ("JWT Keys")
    anon      ->  sb_publishable_...             eyJ... con role=anon
    service   ->  sb_secret_...                  eyJ... con role=service_role

Las dos formas viajan igual en las cabeceras `apikey` y `Authorization`, asi que
este modulo no necesita distinguirlas: solo importa que la de aca sea la SECRETA.

Si se intentara leer con la anon key, PostgREST devuelve una lista VACIA sin error
—RLS niega sin policy— y el motor concluiria "no hubo validaciones" cuando en
realidad no tenia permiso. Por eso `descargar` distingue los dos casos.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

TABLA = 'scout_validaciones'
TIMEOUT = 30
# Lo que la app llama "no encontre nada". Cualquier otra cosa es un hallazgo.
SIN_HALLAZGO = ('nada', 'ninguno', 'sin hallazgo', '', 'none')


def _get(url, service_key, ruta, params):
    q = '%s/rest/v1/%s?%s' % (url.rstrip('/'), ruta, urllib.parse.urlencode(params))
    req = urllib.request.Request(q, headers={
        'apikey': service_key,
        'Authorization': 'Bearer %s' % service_key,
        'Accept': 'application/json',
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode('utf-8'))


def rol_de_clave(clave):
    """Que rol tiene una clave de Supabase: 'anon', 'service_role' o None.

    Es la unica defensa contra el fallo SILENCIOSO del lazo, y hay que hacerla
    ANTES de la consulta. MEDIDO 2026-07-27 contra el proyecto real: con la clave
    PUBLICA, Supabase responde **HTTP 200 con `[]`** — no 401. Autentica bien; RLS
    simplemente no devuelve filas porque la tabla no tiene policy de SELECT para
    `anon`, a proposito. O sea que la rama 401/403 de abajo NUNCA se dispara para
    el error que mas probablemente se cometa, y "no tengo permiso" llega
    indistinguible de "no hubo validaciones".

    Con el formato nuevo el PREFIJO lo dice sin ambiguedad. Con el legado hay que
    leer el claim `role` del JWT (sin validar firma: no se confia en el, solo se
    usa para no creerle a un resultado vacio).
    """
    clave = (clave or '').strip()
    if clave.startswith('sb_publishable_'):
        return 'anon'
    if clave.startswith('sb_secret_'):
        return 'service_role'
    if not clave.startswith('eyJ') or clave.count('.') != 2:
        return None
    import base64
    try:
        cuerpo = clave.split('.')[1]
        cuerpo += '=' * (-len(cuerpo) % 4)
        return json.loads(base64.urlsafe_b64decode(cuerpo)).get('role')
    except Exception:
        return None


def descargar(url, service_key, tabla=TABLA, desde=None, cliente=None):
    """Trae los registros crudos de la tabla. DataFrame vacio si no hay ninguno.

    Falla RUIDOSO si la credencial no alcanza: una lista vacia por falta de permiso
    es indistinguible de "no hubo validaciones", y esa confusion haria que el motor
    reporte una campaña sin datos en vez de un problema de configuracion.
    """
    if not url or not service_key:
        raise ValueError(
            'faltan las credenciales de lectura. La clave PUBLICA (la del APK) NO '
            'sirve para leer: la tabla es append-only para anon (solo INSERT). Hace '
            'falta la clave SECRETA de Supabase —hoy rotulada "Secret key", empieza '
            'con sb_secret_; en proyectos viejos es la "service_role"— en la '
            'variable SUPABASE_SERVICE_KEY.')

    # EL ROL SE VERIFICA ANTES DE CONSULTAR. Con la clave publica el servidor
    # contesta 200 y una lista vacia, asi que despues de la consulta ya no hay forma
    # de distinguir "sin permiso" de "sin validaciones". Ver `rol_de_clave`.
    rol = rol_de_clave(service_key)
    if rol == 'anon':
        raise RuntimeError(
            'la credencial de lectura es la clave PUBLICA (anon / sb_publishable_), '
            'que es la del APK. Con ella la tabla devuelve HTTP 200 y una lista '
            'VACIA —RLS niega sin policy de SELECT— y el motor concluiria "no hubo '
            'validaciones" cuando en realidad no tuvo permiso. Poner la clave '
            'SECRETA ("Secret key" / sb_secret_, o service_role) en '
            'SUPABASE_SERVICE_KEY.')
    if rol is None:
        # No se pudo saber. No se bloquea —puede ser un formato futuro— pero un
        # cero que sale de una credencial sin rol conocido no se puede dar por bueno.
        print('[lazo] AVISO: no pude reconocer el rol de la credencial. Si el '
              'resultado sale en cero, verificar que sea la clave SECRETA antes de '
              'concluir que no hubo validaciones.')

    params = {'select': '*', 'order': 'created.asc', 'limit': '10000'}
    if desde:
        params['created'] = 'gte.%s' % desde
    if cliente:
        params['cliente'] = 'eq.%s' % cliente
    try:
        filas = _get(url, service_key, tabla, params)
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode('utf-8', 'replace')[:300]
        if e.code in (401, 403):
            raise RuntimeError(
                'Supabase rechazo la lectura (HTTP %d). Casi seguro se esta usando '
                'la clave PUBLICA (sb_publishable_ / anon): la tabla no tiene policy '
                'de SELECT para anon a proposito. Usar la SECRETA (sb_secret_ / '
                'service_role).\n  %s' % (e.code, cuerpo))
        raise RuntimeError('Supabase devolvio HTTP %d: %s' % (e.code, cuerpo))
    return pd.DataFrame(filas)


def a_validaciones(crudo, verbose=True):
    """Traduce los registros de la app al formato que espera `campana.agregar`.

    Devuelve (DataFrame con lote_id + hubo_problema, dict de descartes declarados).
    """
    descartes = {'sin_id_estable': 0, 'sin_lote': 0, 'sin_hallazgo_declarado': 0}
    if crudo is None or len(crudo) == 0:
        return pd.DataFrame(columns=['lote_id', 'hubo_problema']), descartes
    d = crudo.copy()

    # 1. Un id POSICIONAL no se puede rastrear: apunta a un lote distinto en cada
    #    ronda. Se descarta, no se adivina.
    if 'focoIdEstable' in d.columns:
        # `v is False` solo reconoce el booleano NATIVO. Una ida y vuelta por CSV
        # convierte la columna en los strings 'True'/'False' y el descarte pasaba a
        # cero SIN AVISAR: los ids posicionales se colaban al acumulado y contaminaban
        # la precision con observaciones mal atribuidas. `campana._a_booleano` ya
        # resuelve exactamente esta trampa (y ademas nunca convierte NA en False).
        from .campana import _a_booleano
        est = _a_booleano(d['focoIdEstable'])
        malos = est.notna() & (est == False)      # noqa: E712 — NA NO es False
        descartes['sin_id_estable'] = int(malos.sum())
        d = d[~malos]

    # 2. lote_id: el id del foco es el del lote en el GeoJSON del motor; `lote` es
    #    el respaldo por si un registro vino de un mapa viejo.
    lid = None
    for col in ('focoId', 'lote'):
        if col in d.columns:
            v = d[col].astype('string').str.strip()
            lid = v if lid is None else lid.fillna(v).replace('', pd.NA).fillna(v)
    if lid is None:
        return pd.DataFrame(columns=['lote_id', 'hubo_problema']), descartes
    d = d.assign(lote_id=lid.replace('', pd.NA))
    descartes['sin_lote'] = int(d['lote_id'].isna().sum())
    d = d[d['lote_id'].notna()]

    # 3. hubo_problema: 'nada' es el registro NEGATIVO, el que mide falsos
    #    positivos. Sin `hallazgo` no se inventa un negativo: se descarta.
    if 'hallazgo' not in d.columns:
        return pd.DataFrame(columns=['lote_id', 'hubo_problema']), descartes
    h = d['hallazgo'].astype('string').str.strip().str.lower()
    sin_declarar = h.isna()
    descartes['sin_hallazgo_declarado'] = int(sin_declarar.sum())
    d = d[~sin_declarar]
    h = h[~sin_declarar]
    d = d.assign(hubo_problema=~h.isin(SIN_HALLAZGO))

    # 4. La tabla es append-only: el mismo lote puede tener varios registros. Se
    #    conserva el ULTIMO por fecha de creacion, que es la lectura vigente.
    if 'created' in d.columns:
        d = d.sort_values('created')
    d = d.drop_duplicates('lote_id', keep='last')

    cols = [c for c in ('lote_id', 'hubo_problema', 'estrato', 'hallazgo',
                        'categoria', 'created', 'registro_a_ciegas', 'tecnico')
            if c in d.columns]
    out = d[cols].reset_index(drop=True)
    if verbose:
        n_pos = int(out['hubo_problema'].sum()) if len(out) else 0
        print('[lazo] %d validacion(es) utilizables · %d con hallazgo · %d sin'
              % (len(out), n_pos, len(out) - n_pos))
        for k, v in descartes.items():
            if v:
                print('  [descartado] %d por %s' % (v, k.replace('_', ' ')))
    return out, descartes


def auditar_ciego(val):
    """Que fraccion de los registros se hizo REALMENTE a ciegas.

    `registro_a_ciegas` lo escribe la app: modo ciego encendido Y estrato nunca
    revelado en pantalla antes de guardar. Si esa fraccion es baja, la campaña no
    mide lo que dice medir — el tecnico que sabe que va a un rojo encuentra algo.
    """
    if 'registro_a_ciegas' not in getattr(val, 'columns', []):
        return {'auditable': False,
                'nota': 'los registros no traen `registro_a_ciegas`: el ciego se '
                        'confia al procedimiento y no se puede auditar.'}
    ok = val['registro_a_ciegas'].apply(lambda v: bool(v) if pd.notna(v) else False)
    return {'auditable': True, 'n': int(len(ok)), 'a_ciegas': int(ok.sum()),
            'fraccion': float(ok.mean()) if len(ok) else float('nan')}


def main(argv=None):
    p = argparse.ArgumentParser(description='PIX ALERTA — lazo de retorno de campo')
    # Solo hace falta para ACUMULAR en una campaña. Bajar y auditar no depende del
    # sitio, y exigirlo obligaba a inventar uno para el uso mas comun —mirar que
    # volvio de campo— en un despliegue con varias propiedades.
    p.add_argument('--sitio', default=None, help='clave del sitio (para --agregar)')
    p.add_argument('--ronda', default=None, help='YYYY-MM-DD de la ronda')
    p.add_argument('--desde', default=None, help='solo registros creados desde esta fecha')
    p.add_argument('--cliente', default=None, help='filtra por el campo `cliente`')
    p.add_argument('--muestra', default=None,
                   help='CSV de la muestra sorteada (para --agregar)')
    p.add_argument('--base', default='salida', help='carpeta de la campaña')
    p.add_argument('--agregar', action='store_true',
                   help='suma la ronda al acumulado de campaña')
    p.add_argument('--csv', default=None, help='guarda las validaciones traducidas')
    p.add_argument('--desde-json', default=None,
                   help='leer de un JSON local en vez de Supabase (para probar)')
    a = p.parse_args(argv)

    if a.desde_json:
        with open(a.desde_json, encoding='utf-8') as fh:
            crudo = pd.DataFrame(json.load(fh))
        print('[lazo] leido de %s (%d registros)' % (a.desde_json, len(crudo)))
    else:
        # El .env local es el que escribe el asistente de credenciales. En la nube
        # no existe y los secretos ya vienen en el entorno, que siempre gana.
        from . import entorno
        entorno.cargar(verbose=True)
        url = os.environ.get('SUPABASE_URL', '').strip()
        key = os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
        try:
            crudo = descargar(url, key, desde=a.desde, cliente=a.cliente)
        except (ValueError, RuntimeError) as e:
            print('[ERROR] %s' % e)
            return 1
        print('[lazo] %d registro(s) en la tabla' % len(crudo))

    val, descartes = a_validaciones(crudo)
    ciego = auditar_ciego(val)
    if ciego.get('auditable'):
        print('[ciego] %d de %d registros a ciegas (%.0f%%)'
              % (ciego['a_ciegas'], ciego['n'], 100 * ciego['fraccion']))
        if ciego['fraccion'] < 0.9:
            print('  [AVISO] menos del 90% se registro a ciegas: el sesgo de '
                  'verificacion vuelve y la precision sale inflada.')
    else:
        print('[ciego] %s' % ciego['nota'])

    if a.csv:
        val.to_csv(a.csv, index=False)
        print('  -> %s' % a.csv)

    if a.agregar:
        if not a.sitio:
            print('[ERROR] --agregar necesita --sitio: el acumulado es por propiedad')
            return 1
        if not a.muestra:
            print('[ERROR] --agregar necesita --muestra (el CSV de la ronda sorteada)')
            return 1
        from . import campana as cp
        muestra = pd.read_csv(a.muestra)
        ruta, n = cp.agregar(a.base, a.sitio, muestra, ronda=a.ronda, validaciones=val)
        print('  -> %s (%d filas acumuladas)' % (ruta, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
