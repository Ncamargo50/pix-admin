"""Autenticacion contra Earth Engine, en la PC y en la nube.

Existe porque la PRIMERA CORRIDA REAL en GitHub Actions murio en este punto: el motor
llamaba a `ee.Initialize()` a secas, que anda en la maquina del usuario porque tiene su
credencial personal, pero en un runner no hay ninguna. El error que daba —"Please
authorize access to your Earth Engine account by running earthengine authenticate"— no
dice nada util sobre la causa, y todo pasaba en local, incluido el chequeo de arranque.
"""
import json
import sys
import types

import pytest

from pix_alerta import ee_init


class EEFalso(types.ModuleType):
    """Un ee de mentira para probar la eleccion de credencial sin tocar la red."""
    def __init__(self, falla_local=False):
        super().__init__('ee')
        self.falla_local = falla_local
        self.usado = None

    def ServiceAccountCredentials(self, correo, key):
        return ('sa', correo, key)

    def Initialize(self, cred=None):
        if cred is None:
            if self.falla_local:
                raise Exception('Please authorize access to your Earth Engine account')
            self.usado = 'local'
        else:
            self.usado = cred


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setattr(ee_init, '_LISTO', False)
    monkeypatch.delenv('GEE_SA_KEY', raising=False)


def _clave(tmp_path, correo='robot@proyecto.iam.gserviceaccount.com'):
    p = tmp_path / 'sa.json'
    p.write_text(json.dumps({'type': 'service_account', 'client_email': correo,
                             'private_key': 'x'}), encoding='utf-8')
    return str(p)


def test_en_la_nube_usa_la_cuenta_de_servicio(tmp_path, monkeypatch):
    """EL CASO QUE FALLO. Con GEE_SA_KEY puesto, NO se usa la credencial personal."""
    ee = EEFalso()
    monkeypatch.setitem(sys.modules, 'ee', ee)
    monkeypatch.setenv('GEE_SA_KEY', _clave(tmp_path))
    modo = ee_init.inicializar()
    assert 'cuenta de servicio' in modo and 'robot@' in modo
    assert ee.usado[0] == 'sa'


def test_en_la_PC_usa_la_credencial_local(monkeypatch):
    ee = EEFalso()
    monkeypatch.setitem(sys.modules, 'ee', ee)
    assert ee_init.inicializar() == 'credencial local del usuario'
    assert ee.usado == 'local'


def test_no_se_cae_en_silencio_a_la_credencial_local(tmp_path, monkeypatch):
    """Si la cuenta de servicio esta declarada pero rota, hay que decirlo. Caer a la
    local disimula el problema en la PC y vuelve a fallar en la nube."""
    ee = EEFalso()
    monkeypatch.setitem(sys.modules, 'ee', ee)
    p = tmp_path / 'roto.json'
    p.write_text('{"type":"service_account"}', encoding='utf-8')   # sin client_email
    monkeypatch.setenv('GEE_SA_KEY', str(p))
    with pytest.raises(RuntimeError, match='client_email'):
        ee_init.inicializar()
    assert ee.usado is None


def test_avisa_si_la_clave_no_existe(monkeypatch):
    ee = EEFalso()
    monkeypatch.setitem(sys.modules, 'ee', ee)
    monkeypatch.setenv('GEE_SA_KEY', '/no/existe/sa.json')
    with pytest.raises(RuntimeError, match='no existe'):
        ee_init.inicializar()


def test_el_error_dice_QUE_hacer(monkeypatch):
    """El mensaje original de Earth Engine no distingue PC de nube."""
    ee = EEFalso(falla_local=True)
    monkeypatch.setitem(sys.modules, 'ee', ee)
    with pytest.raises(RuntimeError) as e:
        ee_init.inicializar()
    txt = str(e.value)
    assert 'earthengine authenticate' in txt and 'GEE_SA_JSON' in txt
