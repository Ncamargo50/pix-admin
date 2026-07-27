# -*- coding: utf-8 -*-
"""Toma UNA clave del portapapeles y la escribe donde va. Sin preguntar nada.

    python scripts/tomar_clave.py --publica     # -> PIX_SCOUT/app/js/config.js
    python scripts/tomar_clave.py --secreta     # -> PIX_ALERTA/.env  (gitignored)

POR QUE EXISTE, SI YA ESTA `configurar_lazo.py`
-----------------------------------------------
El asistente es interactivo: pregunta, espera Enter, guia. Eso sirve cuando el que
lo corre puede seguirlo. Esta version hace UN paso y termina, para el caso en que
otro (una persona ayudando por encima del hombro, o un agente) aprieta el boton
"copiar" en el panel de Supabase y despues corre esto.

LA PROPIEDAD QUE IMPORTA: **la clave nunca se imprime.** Ni entera ni en pedazos.
Lo unico que sale por pantalla es el rol detectado, la cantidad de caracteres y
donde se escribio. Asi, quien esta mirando la pantalla —o el registro de una
sesion— no termina con el secreto delante.

Sale 0 si escribio, 1 si no. Nunca escribe si el rol no es el que se pidio: pegar
la publica donde va la secreta es el error que rompe el lazo EN SILENCIO (leer
devuelve una lista vacia sin error, y el motor concluye "no hubo validaciones").
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'scripts'))

import configurar_lazo as cl  # noqa: E402  (comparte validadores: una sola verdad)


def main(argv=None):
    p = argparse.ArgumentParser(description='toma una clave del portapapeles')
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--publica', action='store_true',
                   help='Publishable key / anon -> config.js del APK')
    g.add_argument('--secreta', action='store_true',
                   help='Secret key / service_role -> .env del motor')
    p.add_argument('--url', default=None,
                   help='URL del proyecto (por defecto, la que ya este en config.js)')
    a = p.parse_args(argv)

    url = (a.url or cl._url_del_config() or '').rstrip('/')
    if not cl._val_url(url)[0]:
        print('[ERROR] no tengo la URL del proyecto y no esta en config.js.')
        print('        pasala con --url https://xxxx.supabase.co')
        return 1

    v = cl._portapapeles()
    if not v:
        print('[ERROR] el portapapeles esta vacio.')
        print('        Apreta el boton de copiar al lado de la clave en Supabase.')
        return 1

    quiero = 'anon' if a.publica else 'service_role'
    valida = cl._val_publica if a.publica else cl._val_secreta
    ok, motivo = valida(v)
    if not ok:
        print('[ERROR] lo que hay en el portapapeles no es la clave que pedi: %s' % motivo)
        return 1
    rol = cl._rol(v)
    if rol and rol != quiero:
        print('[ERROR] esa clave es "%s" y yo esperaba "%s". No escribo nada.'
              % (rol, quiero))
        return 1

    if a.publica:
        if not cl._escribir_config(url, v):
            return 1
        print('[OK] clave publica (%s, %d caracteres) escrita en:' % (rol or '?', len(v)))
        print('     %s' % cl.CONFIG_JS)
        print('     copia de seguridad: config.js.bak')
    else:
        cl._escribir_env(url, v)
        print('[OK] clave SECRETA (%s, %d caracteres) escrita en:' % (rol or '?', len(v)))
        print('     %s   (ya esta en .gitignore)' % cl.ENV)
        print('     NO se imprime, no va al repositorio y no va al APK.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
