# -*- coding: utf-8 -*-
"""Asistente para encender el lazo de retorno. Te va pidiendo lo que hace falta.

    python scripts/configurar_lazo.py

QUE HACE POR VOS
----------------
· Abre la pagina exacta de Supabase donde estan las tres cosas que hay que copiar.
· Te las pide de a una, explicando cual es cual y como se distinguen.
· Verifica el FORMATO antes de escribir nada (una clave pegada de mas o de menos
  no se descubre tres semanas despues, cuando el tecnico ya salio a campo).
· Escribe la URL y la anon key en `PIX_SCOUT/app/js/config.js`, dejando una copia
  de seguridad del archivo anterior.
· Guarda la service_role key en un `.env` LOCAL que no se sube al repositorio, y
  se asegura de que este en el `.gitignore`.
· Prueba la conexion de verdad contra tu tabla y te dice si anduvo.

LO QUE NO HACE Y NO PUEDE HACER
-------------------------------
Pegar las claves por vos. Las tenes que copiar de tu cuenta de Supabase; el
asistente nunca las muestra en pantalla ni las escribe en ningun log.
"""
import os
import re
import shutil
import sys
import webbrowser

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WS = os.path.dirname(RAIZ)
CONFIG_JS = os.path.join(WS, 'PIX_SCOUT', 'app', 'js', 'config.js')
SQL = os.path.join(WS, 'PIX_SCOUT', 'backend', '001_scout_validaciones.sql')
ENV = os.path.join(RAIZ, '.env')
GITIGNORE = os.path.join(RAIZ, '.gitignore')

RE_URL = re.compile(r'^https://[a-z0-9-]+\.supabase\.co/?$')

# HAY DOS FORMATOS DE CLAVE Y HAY QUE ACEPTAR LOS DOS.
#
#   FORMATO NUEVO (el que muestra hoy el panel, seccion "API Keys"):
#       sb_publishable_...   <- publica, va en el APK   (reemplaza a "anon")
#       sb_secret_...        <- SECRETA, solo servidor  (reemplaza a "service_role")
#     Ventaja: el PREFIJO dice sin ambiguedad cual es cual. Es la mejor
#     verificacion posible contra el error que rompe el lazo en silencio.
#
#   FORMATO LEGADO (seccion "JWT Keys", proyectos viejos):
#       eyJ...  <- JWT de tres bloques; el ROL va adentro, hay que decodificarlo.
#
# Los dos funcionan igual contra PostgREST (cabeceras `apikey` y `Authorization`).
RE_JWT = re.compile(r'^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$')
RE_PUBLICA = re.compile(r'^sb_publishable_[A-Za-z0-9_-]{20,}$')
RE_SECRETA = re.compile(r'^sb_secret_[A-Za-z0-9_-]{20,}$')


# La consola de Windows no siempre es UTF-8, y un acento en un cartel no puede ser
# el motivo de que muera el unico camino guiado para encender el lazo.
for _f in (sys.stdout, sys.stderr):
    try:
        _f.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def _t(msg=''):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode(), flush=True)


def _titulo(n, txt):
    _t()
    _t('=' * 68)
    _t('PASO %d — %s' % (n, txt))
    _t('=' * 68)


def _portapapeles():
    """Lee el portapapeles. Devuelve '' si no se puede.

    Es EL camino, no una comodidad. Pegar una clave de 60 caracteres en una
    terminal es donde se traba el que no es programador: en la consola de Windows
    Ctrl+V no siempre anda, el clic derecho pega o no segun la configuracion, y un
    caracter de mas o de menos no se descubre hasta que el tecnico ya salio a
    campo. Al lado de cada clave, Supabase tiene un boton de copiar: con esto,
    apretar ese boton y volver aca es todo el trabajo.
    """
    try:                                    # sin dependencias, va en cualquier lado
        import tkinter
        r = tkinter.Tk()
        r.withdraw()
        v = r.clipboard_get()
        r.destroy()
        return (v or '').strip()
    except Exception:
        pass
    import subprocess
    for cmd in (['powershell', '-NoProfile', '-Command', 'Get-Clipboard'],
                ['pbpaste'], ['xclip', '-selection', 'clipboard', '-o'],
                ['wl-paste']):
        try:
            s = subprocess.run(cmd, capture_output=True, timeout=10)
            if s.returncode == 0:
                return s.stdout.decode('utf-8', 'replace').strip()
        except Exception:
            continue
    return ''


def _pedir(rotulo, validar, ayuda, secreta=True):
    """Pide un valor hasta que tenga la forma correcta. Nunca lo imprime.

    Dos caminos: copiar en Supabase y apretar Enter (el recomendado), o pegar a
    mano. En los dos casos se valida la FORMA antes de escribir nada.
    """
    _t()
    _t('  %s' % rotulo)
    _t('  %s' % ayuda)
    _t('  -> Apreta el boton de COPIAR al lado del valor en Supabase, volve aca y')
    _t('     apreta ENTER. Si preferis, pegalo a mano y despues Enter.')
    while True:
        _t()
        v = input('  [Enter para leer lo copiado]: ').strip().strip('"').strip("'")
        origen = 'pegado a mano'
        if not v:
            v = _portapapeles()
            origen = 'leido del portapapeles'
            if not v:
                _t('  El portapapeles esta vacio. Volve a Supabase, apreta COPIAR y')
                _t('  volve aca. (Para cortar el asistente: Ctrl+C)')
                continue
        ok, motivo = validar(v)
        if ok:
            _t('  OK — %d caracteres, formato correcto (%s).' % (len(v), origen))
            return v
        _t('  ESO NO PARECE LO CORRECTO: %s' % motivo)
        _t('  (%s)' % origen)


def _val_url(v):
    if RE_URL.match(v):
        return True, ''
    if v.startswith('eyJ'):
        return False, 'pegaste una CLAVE, no la URL.'
    return False, 'tiene que ser algo como https://abcdefgh.supabase.co'


def _val_publica(v):
    if RE_PUBLICA.match(v) or RE_JWT.match(v):
        return True, ''
    if v.startswith('http'):
        return False, 'pegaste la URL, no una clave.'
    if v.startswith('sb_secret_'):
        return False, ('esa es la clave SECRETA, y va en el otro paso. Acá va la '
                       'que dice "Publishable key".')
    if v.startswith('sbp_'):
        return False, 'eso es un "personal access token", no la clave del proyecto.'
    return False, 'tiene que empezar con "sb_publishable_" (o "eyJ" si es un proyecto viejo).'


def _val_secreta(v):
    if RE_SECRETA.match(v) or RE_JWT.match(v):
        return True, ''
    if v.startswith('http'):
        return False, 'pegaste la URL, no una clave.'
    if v.startswith('sb_publishable_'):
        return False, ('esa es la clave PUBLICA, la del paso anterior. Acá va la de '
                       'la seccion "Secret keys", la que esta tapada con puntitos.')
    if v.startswith('sbp_'):
        return False, 'eso es un "personal access token", no la clave del proyecto.'
    return False, 'tiene que empezar con "sb_secret_" (o "eyJ" si es un proyecto viejo).'


def _rol(v):
    """Que rol tiene la clave. Por PREFIJO si es formato nuevo, decodificando el
    JWT si es del legado. None si no se puede saber."""
    if RE_PUBLICA.match(v):
        return 'anon'
    if RE_SECRETA.match(v):
        return 'service_role'
    return _rol_del_jwt(v)


def _rol_del_jwt(v):
    """Lee el ROL que declara el propio JWT, sin validar firma ni mostrar nada.

    Es lo que evita el error que rompe el lazo en silencio: pegar la anon key
    donde va la service_role. Con la anon, leer devuelve una lista VACIA sin
    error y el motor concluye "no hubo validaciones".
    """
    import base64
    import json
    try:
        cuerpo = v.split('.')[1]
        cuerpo += '=' * (-len(cuerpo) % 4)
        return json.loads(base64.urlsafe_b64decode(cuerpo)).get('role')
    except Exception:
        return None


def _url_del_config():
    """La URL que ya este escrita en el config del APK, si la hay.

    Es publica (esta dentro del APK de todos modos) y no cambia nunca, asi que
    volver a pedirla solo agrega un paso donde el usuario se puede trabar."""
    try:
        with open(CONFIG_JS, encoding='utf-8') as fh:
            m = re.search("SUPABASE_URL:" + r"\s*" + "'([^']*)'", fh.read())
        return m.group(1).strip() if m else ''
    except Exception:
        return ''


def _escribir_config(url, anon):
    if not os.path.exists(CONFIG_JS):
        _t('  [ERROR] no encuentro %s' % CONFIG_JS)
        return False
    with open(CONFIG_JS, encoding='utf-8') as fh:
        s = fh.read()
    shutil.copy2(CONFIG_JS, CONFIG_JS + '.bak')
    s = re.sub(r"(SUPABASE_URL:\s*)'[^']*'", lambda m: m.group(1) + "'%s'" % url, s, 1)
    s = re.sub(r"(SUPABASE_ANON_KEY:\s*)'[^']*'",
               lambda m: m.group(1) + "'%s'" % anon, s, 1)
    with open(CONFIG_JS, 'w', encoding='utf-8') as fh:
        fh.write(s)
    return True


def _escribir_env(url, service):
    lineas = []
    if os.path.exists(ENV):
        with open(ENV, encoding='utf-8') as fh:
            lineas = [l for l in fh.read().splitlines()
                      if not l.startswith(('SUPABASE_URL=', 'SUPABASE_SERVICE_KEY='))]
    lineas += ['SUPABASE_URL=%s' % url, 'SUPABASE_SERVICE_KEY=%s' % service]
    with open(ENV, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lineas) + '\n')
    # El .env NO puede terminar en el repositorio.
    ign = ''
    if os.path.exists(GITIGNORE):
        with open(GITIGNORE, encoding='utf-8') as fh:
            ign = fh.read()
    if '.env' not in ign.split():
        with open(GITIGNORE, 'a', encoding='utf-8') as fh:
            fh.write('\n# credenciales locales: NUNCA al repositorio\n.env\n')


def _probar(url, service):
    sys.path.insert(0, RAIZ)
    from pix_alerta import lazo
    try:
        d = lazo.descargar(url, service)
    except Exception as e:
        _t('  NO ANDUVO: %s' % str(e).split('\n')[0])
        return False
    _t('  ANDUVO. La tabla tiene %d registro(s).' % len(d))
    if len(d) == 0:
        # `descargar` ya rechaza la clave publica por su ROL, asi que un cero que
        # llega hasta aca es un cero de verdad. Antes no: con la publica el servidor
        # contesta 200 y una lista vacia, y este mismo cartel decia "cero esta BIEN".
        _t('  (cero esta BIEN: la credencial es la SECRETA y la tabla esta vacia)')
    return True


def main():
    _t()
    _t('ASISTENTE DEL LAZO DE RETORNO')
    _t('Vas a copiar tres cosas de Supabase. Yo las escribo donde van.')
    _t('Nunca las muestro en pantalla ni las guardo en ningun log.')

    # --- 1. la tabla ---------------------------------------------------------
    _titulo(1, 'Crear la tabla en Supabase')
    _t('  Abro tu panel de Supabase en el navegador.')
    _t('  1. Entra a tu proyecto (o crea uno gratis si todavia no tenes).')
    _t('  2. En el menu de la izquierda: SQL Editor -> New query.')
    _t('  3. Abri este archivo, copialo ENTERO y pegalo ahi:')
    _t('       %s' % SQL)
    _t('  4. Apreta RUN.')
    _t()
    _t('  Si ya lo corriste antes, corrlo igual: no rompe nada.')
    try:
        webbrowser.open('https://supabase.com/dashboard/projects')
    except Exception:
        pass
    input('\n  Cuando la tabla este creada, apreta ENTER... ')

    # --- 2. los valores ------------------------------------------------------
    _titulo(2, 'Copiar las tres cosas')
    _t('  En Supabase: el engranaje (Project Settings) -> API Keys.')
    _t('  Ahi hay tres cosas que necesito, y son distintas entre si:')
    _t()
    _t('    a) Project URL       -> algo como https://abcdefgh.supabase.co')
    _t('    b) Publishable key   -> empieza con sb_publishable_')
    _t('                            Va DENTRO del APK: no es secreta.')
    _t('    c) Secret key        -> empieza con sb_secret_, esta tapada con puntitos')
    _t('                            (hay un ojito para revelarla). ES SECRETA.')
    _t()
    _t('  OJO con b) y c): son parecidas y estan una debajo de la otra. Si las')
    _t('  confundis, el tecnico registra pero el motor no puede leer, y la')
    _t('  campaña termina sin un solo numero. Yo lo verifico, no te preocupes.')
    _t()
    _t('  Si tu proyecto es viejo y no ves esos rotulos, mira "JWT Keys": ahi las')
    _t('  mismas dos claves se llaman "anon" y "service_role". Sirven igual.')

    # Si la URL ya esta en el config, no la volvemos a pedir: es publica, no
    # cambia nunca, y cada paso que se le pide al usuario es un paso donde se traba.
    url = (_url_del_config() or '').rstrip('/')
    if url and _val_url(url)[0]:
        _t()
        _t('  a) Project URL — ya estaba cargada, no hace falta copiarla:')
        _t('       %s' % url)
    else:
        url = _pedir('a) Project URL', _val_url,
                     'Copiala del campo "Project URL", arriba de todo.').rstrip('/')

    anon = _pedir('b) Publishable key (la publica)', _val_publica,
                  'Esta en la seccion "Publishable key" y empieza con sb_publishable_')
    rol = _rol(anon)
    if rol and rol != 'anon':
        _t('  OJO: esa clave dice ser "%s", no la publica. Buscá la que dice'
           % rol)
        _t('  "Publishable key" (o "anon" si tu proyecto es de los viejos).')
        if input('  Seguir igual? (escribi SI): ').strip().upper() != 'SI':
            return 1

    service = _pedir('c) Secret key (la secreta)', _val_secreta,
                     'Esta en la seccion "Secret keys", tapada con puntitos: hay que '
                     'apretar el ojito para verla. Empieza con sb_secret_')
    rol = _rol(service)
    if rol and rol != 'service_role':
        _t('  ESA NO ES LA SECRETA: dice ser "%s".' % rol)
        _t('  Es EL error que rompe el lazo en silencio. Volve a Supabase, a la')
        _t('  seccion "Secret keys", y apreta el ojito para revelarla antes de')
        _t('  copiarla. (En proyectos viejos: la fila "service_role" -> "Reveal").')
        return 1
    if service == anon:
        _t('\n  Pegaste la MISMA clave dos veces. Tienen que ser distintas.')
        return 1

    # --- 3. escribir ---------------------------------------------------------
    _titulo(3, 'Escribiendo donde va cada una')
    if not _escribir_config(url, anon):
        return 1
    _t('  OK  PIX_SCOUT/app/js/config.js   (URL + clave publica)')
    _t('      copia de seguridad en config.js.bak')
    _escribir_env(url, service)
    _t('  OK  PIX_ALERTA/.env              (la SECRETA, y ya esta en .gitignore)')

    # --- 4. probar -----------------------------------------------------------
    _titulo(4, 'Probando la conexion de verdad')
    ok = _probar(url, service)

    # --- 5. lo que queda -----------------------------------------------------
    _titulo(5, 'Lo unico que queda, y lo haces desde el navegador')
    _t('  Para que la NUBE tambien pueda leer, hay que cargar la clave SECRETA')
    _t('  como secreto del repositorio. Te abro la pagina:')
    _t()
    _t('    Settings -> Secrets and variables -> Actions -> New repository secret')
    _t('      Name:   SUPABASE_SERVICE_KEY')
    _t('      Secret: la misma clave c) que acabas de pegar')
    _t()
    try:
        webbrowser.open(
            'https://github.com/Ncamargo50/pixadvisor-monitor/settings/secrets/actions')
    except Exception:
        pass
    _t('  Y agregar tambien SUPABASE_URL con el valor a).')
    _t()
    _t('=' * 68)
    _t('LISTO' if ok else 'ESCRITO, pero la prueba de conexion fallo (ver arriba)')
    _t('=' * 68)
    _t()
    _t('  Para comprobar todo:   python scripts/verificar_setup.py')
    _t()
    _t('  OJO: ANTES de la primera ronda de validacion hay que encender MODO_CIEGO')
    _t('    en config.js. Si el tecnico ve que va a un rojo, encuentra algo, y el')
    _t('    numero que salga no vale nada. Avisame y lo enciendo yo.')
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n\nCortado. No se escribio nada.')
        sys.exit(1)
