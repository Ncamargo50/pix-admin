# -*- coding: utf-8 -*-
"""Lee el `.env` local y lo pone en el entorno. Sin dependencias.

POR QUE EXISTE
--------------
2026-07-27: el asistente de credenciales escribia `PIX_ALERTA/.env` y **nadie lo
leia**. El usuario terminaba el asistente, veia "OK", corria el motor y el motor
seguia diciendo que faltaba la credencial. Peor que un error: parece que la
herramienta esta rota justo despues de configurarla bien.

LA REGLA QUE IMPORTA: **el entorno real GANA sobre el archivo.**
En la nube las credenciales llegan como secretos de GitHub, ya en el entorno. Si el
archivo pisara al entorno, un `.env` viejo que alguien dejo en el runner —o en su
maquina— apuntaria el motor a otro proyecto sin que nadie se entere. El archivo es
la comodidad local; el entorno es la fuente de verdad.
"""
import os

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(_RAIZ, '.env')


def cargar(ruta=None, verbose=False):
    """Carga el .env sin pisar lo que ya este en el entorno.

    Devuelve la lista de nombres que efectivamente se cargaron del archivo.
    """
    ruta = ruta or RUTA
    puestas, salteadas = [], []
    if not os.path.exists(ruta):
        return puestas
    try:
        # utf-8-sig: un .env regrabado con el Bloc de notas queda con BOM y la
        # primera clave pasaria a llamarse '﻿SUPABASE_URL', que no la lee nadie.
        with open(ruta, encoding='utf-8-sig') as fh:
            lineas = fh.read().splitlines()
    except OSError:
        return puestas
    for l in lineas:
        l = l.strip()
        if not l or l.startswith('#') or '=' not in l:
            continue
        k, _, v = l.partition('=')
        k = k.strip()
        # `export FOO=bar` producia la clave 'export FOO': se setea y no la lee nadie.
        if k.startswith('export '):
            k = k[len('export '):].strip()
        v = v.strip().strip('"').strip("'")
        if not k or not v:
            continue
        if os.environ.get(k, '').strip():
            salteadas.append(k)   # el entorno real manda: ver la nota de arriba
            continue
        os.environ[k] = v
        puestas.append(k)
    if verbose and puestas:
        # Los NOMBRES, nunca los valores.
        print('[entorno] cargado de .env: %s' % ', '.join(puestas))
    if salteadas:
        # LO QUE SE SALTEO TAMBIEN SE DICE. Silenciarlo permitia este escenario: el
        # usuario tiene una SUPABASE_SERVICE_KEY vieja exportada, corre el asistente
        # —que escribe la NUEVA en el .env y la prueba pasandola directo, asi que
        # imprime "ANDUVO"— y despues el motor carga el entorno, gana la vieja, y lee
        # OTRO proyecto. El asistente dice OK y el motor usa otra credencial.
        print('[entorno] AVISO: ya estaban en el entorno y GANAN sobre el .env: %s'
              % ', '.join(salteadas))
    return puestas
