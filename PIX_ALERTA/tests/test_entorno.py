# -*- coding: utf-8 -*-
"""Carga del `.env`: el modulo que decide CON QUE CREDENCIAL corre el motor.

Auditado 2026-07-27: era el único módulo nuevo sin una sola prueba, y decide algo
que, si sale mal, hace que el motor lea otro proyecto y reporte "no hubo
validaciones" sin que nada falle.
"""
import os

from pix_alerta import entorno


def _env(tmp_path, texto, encoding='utf-8'):
    p = tmp_path / '.env'
    p.write_text(texto, encoding=encoding)
    return str(p)


def test_carga_lo_que_no_esta_en_el_entorno(tmp_path, monkeypatch):
    monkeypatch.delenv('PIX_TEST_A', raising=False)
    puestas = entorno.cargar(_env(tmp_path, 'PIX_TEST_A=uno\n'))
    assert puestas == ['PIX_TEST_A']
    assert os.environ['PIX_TEST_A'] == 'uno'


def test_el_entorno_REAL_gana_sobre_el_archivo(tmp_path, monkeypatch):
    """En la nube las credenciales llegan como secretos de GitHub, ya en el entorno.
    Si el archivo pisara, un `.env` viejo apuntaria el motor a otro proyecto."""
    monkeypatch.setenv('PIX_TEST_B', 'el-del-entorno')
    entorno.cargar(_env(tmp_path, 'PIX_TEST_B=el-del-archivo\n'))
    assert os.environ['PIX_TEST_B'] == 'el-del-entorno'


def test_lo_que_se_salteo_SE_DICE(tmp_path, monkeypatch, capsys):
    """El escenario que costaba una campaña: el usuario tiene una clave vieja
    exportada, corre el asistente —que escribe la nueva y la prueba pasandola
    directo, asi que dice "ANDUVO"— y despues el motor carga el entorno, gana la
    vieja, y lee OTRO proyecto. Callarlo lo hacia indetectable."""
    monkeypatch.setenv('SUPABASE_SERVICE_KEY', 'la-vieja')
    entorno.cargar(_env(tmp_path, 'SUPABASE_SERVICE_KEY=la-nueva\n'))
    salida = capsys.readouterr().out
    assert 'SUPABASE_SERVICE_KEY' in salida
    assert 'GANAN' in salida
    assert 'la-vieja' not in salida and 'la-nueva' not in salida   # nunca el valor


def test_una_variable_vacia_cuenta_como_no_puesta(tmp_path, monkeypatch):
    monkeypatch.setenv('PIX_TEST_C', '   ')
    entorno.cargar(_env(tmp_path, 'PIX_TEST_C=valor\n'))
    assert os.environ['PIX_TEST_C'] == 'valor'


def test_un_valor_con_igual_sobrevive_entero(tmp_path, monkeypatch):
    """Las claves y las URLs con query llevan `=`. Cortar en el ultimo las rompe."""
    monkeypatch.delenv('PIX_TEST_D', raising=False)
    entorno.cargar(_env(tmp_path, 'PIX_TEST_D=abc=def==\n'))
    assert os.environ['PIX_TEST_D'] == 'abc=def=='


def test_export_y_comillas(tmp_path, monkeypatch):
    """`export FOO=bar` producia la clave 'export FOO': se seteaba y no la leia nadie."""
    for k in ('PIX_TEST_E', 'PIX_TEST_F'):
        monkeypatch.delenv(k, raising=False)
    entorno.cargar(_env(tmp_path, 'export PIX_TEST_E=uno\nPIX_TEST_F="dos"\n'))
    assert os.environ['PIX_TEST_E'] == 'uno'
    assert os.environ['PIX_TEST_F'] == 'dos'


def test_un_env_con_BOM_se_lee_igual(tmp_path, monkeypatch):
    """Un `.env` regrabado con el Bloc de notas queda con BOM y la primera clave
    pasaba a llamarse '﻿SUPABASE_URL'."""
    monkeypatch.delenv('PIX_TEST_G', raising=False)
    entorno.cargar(_env(tmp_path, 'PIX_TEST_G=uno\n', encoding='utf-8-sig'))
    assert os.environ['PIX_TEST_G'] == 'uno'


def test_comentarios_y_lineas_vacias_no_rompen(tmp_path, monkeypatch):
    monkeypatch.delenv('PIX_TEST_H', raising=False)
    entorno.cargar(_env(tmp_path, '# comentario\n\nPIX_TEST_H=uno\nbasura sin igual\n'))
    assert os.environ['PIX_TEST_H'] == 'uno'


def test_sin_archivo_no_falla(tmp_path):
    assert entorno.cargar(str(tmp_path / 'no_existe.env')) == []
