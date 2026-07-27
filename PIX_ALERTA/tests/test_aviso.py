# -*- coding: utf-8 -*-
"""Puertas del aviso por cliente.

El aviso global unico decia "hubo entrega" sin decir de quien. Con varios clientes
eso obliga a abrir el repositorio para averiguarlo, que es exactamente lo que el
aviso venia a evitar.

Lo que se prueba: el texto y el ENRUTADO. Nunca se manda nada — CallMeBot exige que
cada destinatario autorice al bot y tenga su propia apikey, asi que mandar a un
numero sin su clave se pierde en silencio, que es peor que no avisar.
"""
import importlib.util
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    'avisar', os.path.join(RAIZ, 'scripts', 'avisar.py'))
avisar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(avisar)


class _Cliente:
    def __init__(self, clave='HDS', titulo='Hacienda del Señor', wa=None):
        self.clave, self.titulo = clave, titulo
        self.contacto = {'whatsapp': wa} if wa else {}

    @property
    def whatsapp(self):
        return self.contacto.get('whatsapp') or None


# --- el texto ----------------------------------------------------------------

def test_el_aviso_dice_de_que_cliente_es():
    """Es la razon de existir del cambio: sin el nombre, el aviso no sirve."""
    t = avisar._mensaje(_Cliente(), {'fecha_entrega': '2026-04-29',
                                     'lotes_alertados': 8})
    assert 'Hacienda del Señor' in t
    assert '2026-04-29' in t
    assert '8 lote' in t


def test_avisa_tambien_cuando_no_hay_nada_que_recorrer():
    """Un informe que dice 'no hay nada' conserva la confianza. Callarse deja al
    productor sin saber si el servicio corrio."""
    t = avisar._mensaje(_Cliente(), {'fecha_entrega': '2026-04-29',
                                     'lotes_alertados': 0})
    assert 'Ningun lote fuera de control' in t


def test_sin_conteo_no_inventa_un_numero():
    t = avisar._mensaje(_Cliente(), {'fecha_entrega': '2026-04-29'})
    assert 'entrega nueva' in t
    assert 'lote(s) para recorrer' not in t


def test_sin_meta_no_revienta():
    t = avisar._mensaje(_Cliente(), None)
    assert 'sin fecha' in t


# --- el enrutado -------------------------------------------------------------

def _correr(tmp_path, monkeypatch, clientes, entorno):
    base = tmp_path / 'entregas'
    for c in clientes:
        d = base / c.clave / 'ultimo'
        d.mkdir(parents=True)
        (d / 'META.json').write_text(
            '{"cliente": "%s", "fecha_entrega": "2026-04-29", '
            '"lotes_alertados": 3}' % c.clave, encoding='utf-8')
    monkeypatch.setattr(avisar.cl, 'cargar_todos', lambda **kw: clientes)
    enviados = []
    monkeypatch.setattr(avisar, '_enviar',
                        lambda tel, key, txt, seco=False: (
                            enviados.append((tel, key, txt)) or True))
    for k in ('WHATSAPP_PHONE', 'CALLMEBOT_APIKEY', 'CALLMEBOT_HDS',
              'CALLMEBOT_CERRO'):
        monkeypatch.delenv(k, raising=False)
    for k, v in entorno.items():
        monkeypatch.setenv(k, v)
    avisar.main([str(base)])
    return enviados


def test_con_su_clave_le_llega_directo_al_cliente(tmp_path, monkeypatch):
    env = _correr(tmp_path, monkeypatch, [_Cliente(wa='+59170000000')],
                  {'CALLMEBOT_HDS': 'k-hds'})
    assert len(env) == 1
    tel, key, _ = env[0]
    assert (tel, key) == ('+59170000000', 'k-hds')


def test_sin_su_clave_va_al_admin_con_la_leyenda_de_reenvio(tmp_path, monkeypatch):
    """Nunca se manda al numero del cliente con la clave de otro: CallMeBot lo
    rechaza y el aviso se pierde sin que nadie se entere."""
    env = _correr(tmp_path, monkeypatch, [_Cliente(wa='+59170000000')],
                  {'WHATSAPP_PHONE': '+59111111111', 'CALLMEBOT_APIKEY': 'k-admin'})
    assert len(env) == 1
    tel, key, txt = env[0]
    assert (tel, key) == ('+59111111111', 'k-admin')
    assert 'REENVIAR' in txt and '+59170000000' in txt


def test_cada_cliente_recibe_su_propio_aviso(tmp_path, monkeypatch):
    env = _correr(tmp_path, monkeypatch,
                  [_Cliente('HDS', 'Hacienda del Señor', '+59170000000'),
                   _Cliente('CERRO', 'Cerro Alto', '+59170000001')],
                  {'CALLMEBOT_HDS': 'k1', 'CALLMEBOT_CERRO': 'k2'})
    assert len(env) == 2
    assert {t for t, _, _ in env} == {'+59170000000', '+59170000001'}
    # y cada mensaje nombra a SU cliente, no al otro
    por_tel = {t: txt for t, _, txt in env}
    assert 'Hacienda del Señor' in por_tel['+59170000000']
    assert 'Cerro Alto' in por_tel['+59170000001']
    assert 'Cerro Alto' not in por_tel['+59170000000']


def test_un_cliente_sin_entrega_no_genera_aviso(tmp_path, monkeypatch):
    base = tmp_path / 'entregas'
    base.mkdir()
    monkeypatch.setattr(avisar.cl, 'cargar_todos', lambda **kw: [_Cliente()])
    enviados = []
    monkeypatch.setattr(avisar, '_enviar',
                        lambda *a, **k: enviados.append(a) or True)
    avisar.main([str(base)])
    assert enviados == []


def test_sin_ningun_destino_no_falla_la_corrida(tmp_path, monkeypatch):
    """El entregable ya esta publicado y commiteado: que no se pueda avisar no
    puede marcar la corrida como fallida."""
    env = _correr(tmp_path, monkeypatch, [_Cliente()], {})
    assert env == []
