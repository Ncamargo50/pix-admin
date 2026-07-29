# -*- coding: utf-8 -*-
"""El sistema de marca tiene que viajar DENTRO del repositorio.

MEDIDO 2026-07-29: `informe_focos` leia `pix_branding` de
`~/.claude/skills/pixadvisor-propuesta-ejecutiva`. En la maquina del usuario andaba
perfecto; en el runner de GitHub —una maquina Linux vacia— esa carpeta no existe,
`HAY_MARCA` daba False y el informe caia al formato simple SIN AVISAR. El PDF local
pesaba 297 KB con la foto satelital y el que publicaba la nube 9,5 KB sin nada.

Es la misma familia de falla que ya mordio antes: algo que depende del Escritorio
del usuario y que en la nube no esta. Por eso `test_clientes` ya exige que los
insumos de los clientes vivan dentro del repo; esto lo extiende al informe.
"""
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCA = os.path.join(RAIZ, 'marca')


def test_el_modulo_de_marca_esta_en_el_repo():
    assert os.path.exists(os.path.join(MARCA, 'pix_branding.py')), (
        'falta PIX_ALERTA/marca/pix_branding.py: en la nube el informe sale sin marca')


def test_el_logo_esta_en_el_repo():
    logos = [f for f in os.listdir(MARCA)] if os.path.isdir(MARCA) else []
    assert any(f.endswith('.png') for f in logos), (
        'falta el logo en PIX_ALERTA/marca/: la portada sale sin el')


def test_el_informe_encuentra_la_marca_sin_la_carpeta_del_usuario(monkeypatch):
    """Simula el runner: sin `~/.claude/skills`, la marca tiene que seguir estando."""
    monkeypatch.setenv('HOME', os.path.join(RAIZ, 'no_existe_este_home'))
    monkeypatch.setenv('USERPROFILE', os.path.join(RAIZ, 'no_existe_este_home'))
    import importlib

    from pix_alerta import informe_focos
    importlib.reload(informe_focos)
    assert informe_focos.HAY_MARCA, (
        'sin la carpeta del usuario el informe pierde la marca: en la nube saldria '
        'el formato simple')


def test_la_ruta_de_assets_apunta_a_donde_esta_el_logo():
    from pix_alerta import informe_focos
    if not informe_focos.HAY_MARCA:
        pytest.skip('sin reportlab/marca en este entorno')
    hay = [f for f in os.listdir(informe_focos._ASSETS)
           if f.endswith('.png')] if os.path.isdir(informe_focos._ASSETS) else []
    assert hay, 'los assets apuntan a una carpeta sin logo'
