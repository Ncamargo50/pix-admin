# -*- coding: utf-8 -*-
"""Puertas del envio de la app. Se leen sobre el JS, porque ahi no hay suite.

POR QUE EXISTE
--------------
2026-07-27, MEDIDO contra el proyecto Supabase real: la app mandaba
`?on_conflict=id` + `Prefer: resolution=ignore-duplicates`, y **el 100% de los POST
daba 401 / 42501** ("new row violates row-level security policy"). Ese Prefer manda
a PostgREST por el camino de UPSERT, y un `ON CONFLICT` necesita mirar la fila en
conflicto — o sea, policy de SELECT. La tabla no tiene SELECT para `anon` A
PROPOSITO, porque la clave viaja dentro del APK.

El sintoma era el peor posible: el tecnico ve "guardado offline", la cola no se
vacia NUNCA, y la campaña termina sin un solo dato de retorno creyendo que no hubo
validaciones. No hay ningun error visible en el telefono.

El razonamiento del comentario original —"reenviar tras un timeout debe ser no-op"—
era CORRECTO; lo que estaba mal era el mecanismo. La idempotencia se resuelve donde
corresponde: aceptando el 23505 del servidor, que significa "ya la tengo".

Estas pruebas fijan las dos mitades y que las dos copias del archivo no se separen.
"""
import os
import re

import pytest

_WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COPIAS = [
    os.path.join(_WS, 'PIX_SCOUT', 'app', 'js', 'store.js'),
    os.path.join(_WS, 'PIX_SCOUT', 'pix-scout-apk', 'app', 'src', 'main', 'assets',
                 'js', 'store.js'),
]
EXISTENTES = [p for p in COPIAS if os.path.exists(p)]


def _leer(p):
    with open(p, encoding='utf-8') as fh:
        return fh.read()


def _sin_comentarios(s):
    """El codigo, sin los `//`. El comentario que explica POR QUE se saco el upsert
    nombra `ignore-duplicates`, y esa explicacion tiene que poder quedar escrita sin
    que la prueba la confunda con el bug."""
    return re.sub(r'//[^\n]*', '', s)


@pytest.mark.parametrize('ruta', EXISTENTES, ids=lambda p: os.path.basename(
    os.path.dirname(os.path.dirname(p))))
def test_no_vuelve_el_upsert_que_rls_niega(ruta):
    """`ignore-duplicates` contra una tabla append-only da 401 en TODOS los envios."""
    s = _sin_comentarios(_leer(ruta))
    assert 'resolution=ignore-duplicates' not in s
    assert 'merge-duplicates' not in s
    assert 'on_conflict' not in s


@pytest.mark.parametrize('ruta', EXISTENTES, ids=lambda p: os.path.basename(
    os.path.dirname(os.path.dirname(p))))
def test_el_reintento_de_una_fila_ya_guardada_se_da_por_sincronizada(ruta):
    """409/23505 = el servidor YA la tiene. Pasa cuando el POST llego pero la
    respuesta se perdio (el celular cambiando de antena al salir del lote). Tratarlo
    como error deja la fila reintentandose para siempre."""
    s = _sin_comentarios(_leer(ruta))
    m = re.search(r'r\.status\s*===\s*409[^\n]*23505[^\n]*markSynced', s)
    assert m, 'falta la rama que acepta el duplicado como envio exitoso'


def test_las_dos_copias_del_archivo_son_iguales():
    """El APK sirve su propia copia de los assets. Si se arregla una sola, el
    tecnico en campo sigue con el bug y en el navegador todo se ve bien."""
    if len(EXISTENTES) < 2:
        pytest.skip('solo hay una copia de store.js')
    a, b = (_leer(p) for p in EXISTENTES[:2])
    assert a == b, 'store.js del web y del APK se separaron'


def test_la_app_no_lleva_la_clave_secreta():
    """La secreta da acceso privilegiado. Dentro del APK es publica de hecho:
    cualquiera que instale la app se la puede sacar."""
    for p in [q for q in (os.path.join(os.path.dirname(os.path.dirname(r)),
                                       'config.js') for r in EXISTENTES)
              if os.path.exists(q)]:
        s = _leer(p)
        assert 'sb_secret_' not in s, '%s lleva la clave SECRETA' % p
        assert 'service_role' not in re.sub(r'//[^\n]*', '', s), \
            '%s lleva una clave service_role' % p
