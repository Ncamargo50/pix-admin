# -*- coding: utf-8 -*-
"""Puertas del asistente de credenciales.

POR QUE EXISTE ESTE ARCHIVO
---------------------------
2026-07-27: el asistente rechazaba las claves reales del usuario. Validaba SOLO el
formato legado (`eyJ...`, JWT de tres bloques) y Supabase ya entrega el formato
nuevo (`sb_publishable_...` / `sb_secret_...`). El unico camino guiado para encender
el lazo estaba cerrado, y el sintoma —"ESO NO PARECE LO CORRECTO"— apunta al usuario
en vez de al validador, que es la peor forma de fallar.

Lo que estas pruebas fijan es que el asistente acepte LOS DOS formatos y siga
distinguiendo cual es cual, porque esa distincion es lo que evita el error que rompe
el lazo EN SILENCIO: con la clave publica, leer devuelve una lista vacia sin error y
el motor concluye "no hubo validaciones" cuando en realidad no tenia permiso.
"""
import importlib.util
import os

import pytest

_RUTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     'scripts', 'configurar_lazo.py')
_spec = importlib.util.spec_from_file_location('configurar_lazo', _RUTA)
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)

# Valores con la FORMA de los reales, sin ningun secreto adentro.
PUB_NUEVA = 'sb_publishable_' + 'A1b2C3d4E5f6G7h8J9k0'
SEC_NUEVA = 'sb_secret_' + 'Z9y8X7w6V5u4T3s2R1q0'
PUB_VIEJA = 'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.firma'          # role=anon
SEC_VIEJA = 'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.firma'  # service_role


# --- el formato nuevo, que es el que muestra el panel hoy ---------------------

@pytest.mark.parametrize('clave', [PUB_NUEVA, PUB_VIEJA])
def test_acepta_la_publica_en_los_dos_formatos(clave):
    ok, motivo = cl._val_publica(clave)
    assert ok, motivo


@pytest.mark.parametrize('clave', [SEC_NUEVA, SEC_VIEJA])
def test_acepta_la_secreta_en_los_dos_formatos(clave):
    ok, motivo = cl._val_secreta(clave)
    assert ok, motivo


# --- la confusion que rompe el lazo en silencio -------------------------------

def test_la_secreta_donde_va_la_publica_se_rechaza():
    """Poner la SECRETA dentro del APK la publica al mundo: cualquiera que instale
    la app puede leer y borrar la tabla entera."""
    ok, motivo = cl._val_publica(SEC_NUEVA)
    assert not ok and 'SECRETA' in motivo


def test_la_publica_donde_va_la_secreta_se_rechaza():
    """Es el error caro: no falla: leer devuelve vacio y el motor cree que no hubo
    validaciones."""
    ok, motivo = cl._val_secreta(PUB_NUEVA)
    assert not ok and 'PUBLICA' in motivo


def test_el_rol_se_deduce_del_prefijo_sin_decodificar_nada():
    """Con el formato nuevo el prefijo ya dice el rol, y eso es MAS confiable que
    decodificar el JWT: no depende de que el payload traiga el claim."""
    assert cl._rol(PUB_NUEVA) == 'anon'
    assert cl._rol(SEC_NUEVA) == 'service_role'


def test_el_rol_del_formato_legado_se_sigue_leyendo_del_jwt():
    assert cl._rol(PUB_VIEJA) == 'anon'
    assert cl._rol(SEC_VIEJA) == 'service_role'


# --- los otros pegados equivocados --------------------------------------------

def test_la_url_pegada_como_clave_se_rechaza():
    for f in (cl._val_publica, cl._val_secreta):
        ok, motivo = f('https://fnoocboaupjmxpkhdnij.supabase.co')
        assert not ok and 'URL' in motivo


def test_el_token_personal_no_es_la_clave_del_proyecto():
    """`sbp_` es un personal access token de la CUENTA, no del proyecto. Se parece
    lo suficiente como para pegarlo por error."""
    for f in (cl._val_publica, cl._val_secreta):
        ok, motivo = f('sbp_' + '0123456789abcdef0123456789abcdef01234567')
        assert not ok and 'personal' in motivo


def test_la_clave_pegada_como_url_se_rechaza():
    ok, motivo = cl._val_url(PUB_VIEJA)
    assert not ok and 'CLAVE' in motivo


def test_la_url_del_proyecto_se_acepta():
    ok, _ = cl._val_url('https://fnoocboaupjmxpkhdnij.supabase.co')
    assert ok
