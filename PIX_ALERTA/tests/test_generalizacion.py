# -*- coding: utf-8 -*-
"""El motor NO puede estar ajustado al trigo de Santo Antonio y Sao Francisco.

Es una herramienta para varios cultivos y varios clientes. Todo parametro que se
midio sobre UN cultivo tiene que cumplir una de dos condiciones:

  a) DERIVARSE de algo declarado del cultivo (su ciclo, su rango de NDVI, cuantos
     estratos se buscan), o
  b) ser DECLARABLE por sitio, con el default medido a la vista.

Un numero que no cumple ninguna de las dos es un ajuste escondido: funciona en el
cliente donde se midio y falla callado en el siguiente. Estas pruebas son la puerta.
"""
import pytest

from pix_alerta import config as cfg
from pix_alerta import criterio as cri
from pix_alerta import estratos as es
from pix_alerta import focos as fo


class _SitioFalso:
    """Lo minimo que el motor le pide a un sitio. Sin GEE ni red."""

    def __init__(self, cultivo='', ciclo_dias=None, **extra):
        self.cultivo = cultivo
        self.ciclo_dias = ciclo_dias
        for k, v in extra.items():
            setattr(self, k, v)


# --- la ventana de linea base sale del CICLO, no de 75 dias de trigo ----------

def test_la_ventana_de_base_se_adapta_al_ciclo_del_cultivo():
    """75 dias es medio ciclo de trigo. En caña es un quinto del ciclo y en una
    hortaliza de 70 dias se come la campaña entera. Tiene que moverse."""
    trigo = cri.ventana_de(_SitioFalso('trigo'))
    cana = cri.ventana_de(_SitioFalso('cana_de_azucar'))
    assert cana > trigo, 'un cultivo de ciclo largo necesita mas linea base'


def test_la_ventana_declarada_del_sitio_manda_sobre_la_tabla_de_cultivos():
    """El ciclo real lo sabe el cliente. Un trigo de 120 dias no puede mirar la
    misma ventana que uno de 100 solo porque la tabla dice 100."""
    corto = cri.ventana_de(_SitioFalso('trigo', ciclo_dias=100))
    largo = cri.ventana_de(_SitioFalso('trigo', ciclo_dias=160))
    assert largo > corto


def test_la_ventana_esta_acotada_por_arriba_y_por_abajo():
    """Sin cota, un cultivo perenne pediria una base de dos años (fenologia vieja
    metida en la referencia) y uno muy corto pediria 20 dias (no alcanza para
    tener trayectoria)."""
    assert cri.ventana_de(_SitioFalso('', ciclo_dias=20)) >= 40
    assert cri.ventana_de(_SitioFalso('', ciclo_dias=2000)) <= 180


def test_un_cultivo_desconocido_no_rompe_el_motor():
    """Un cliente nuevo puede traer un cultivo que no esta en la tabla. Eso baja a
    un default declarado, no a una excepcion en medio de la corrida nocturna."""
    assert cri.ventana_de(_SitioFalso('quinua_morada')) == cri.VENTANA_BASE_DIAS
    assert cri.ventana_de(None) == cri.VENTANA_BASE_DIAS


# --- los parametros medidos sobre un cultivo son declarables por sitio --------

def test_el_piso_de_escala_y_la_mmu_se_pueden_declarar_por_sitio():
    """El piso de escala se midio sobre TRIGO en Parana y la MMU sobre lotes de
    40-90 ha. Otro cultivo, otra atmosfera u otra escala de trabajo pueden pedir
    otro valor, y tiene que poder decirse en el JSON del cliente."""
    campos = {f.name for f in cfg.Sitio.__dataclass_fields__.values()}
    assert 'sigma_minima' in campos
    assert 'mmu_ha' in campos


def test_el_default_medido_se_usa_cuando_el_sitio_no_declara_nada():
    """Que se pueda declarar no significa que haya que declararlo: un cliente que
    no toca nada tiene que recibir el valor medido, no un None que reviente."""
    s = _SitioFalso('trigo')
    assert cfg.valor_de(s, 'sigma_minima', cri.SIGMA_MINIMA) == cri.SIGMA_MINIMA
    assert cfg.valor_de(s, 'mmu_ha', fo.MMU_HA) == fo.MMU_HA


def test_lo_declarado_por_el_sitio_pisa_al_default():
    s = _SitioFalso('trigo', sigma_minima=0.025, mmu_ha=0.5)
    assert cfg.valor_de(s, 'sigma_minima', cri.SIGMA_MINIMA) == 0.025
    assert cfg.valor_de(s, 'mmu_ha', fo.MMU_HA) == 0.5


def test_un_cero_declarado_a_proposito_se_respeta():
    """Distinto de 'no declarado'. Si alguien pone 0 sabiendo lo que hace, el motor
    no puede sustituirlo en silencio por el default — seria mentirle al operador."""
    s = _SitioFalso('trigo', mmu_ha=0)
    assert cfg.valor_de(s, 'mmu_ha', fo.MMU_HA) == 0


# --- los estratos tampoco pueden estar ajustados al trigo ---------------------

def test_la_puerta_de_coherencia_se_deriva_de_la_nula():
    """El 0,80 que separo los 4 lotes de trigo no vale para 6 pasadas de siembra:
    ahi el azar acierta 1/6 y exigir 0,80 rechazaria bloques reales."""
    assert es.umbral_coherencia(2) > es.umbral_coherencia(6)
    for n in (2, 3, 4, 6, 8):
        assert es.umbral_coherencia(n) > 1.0 / n


def test_el_ndvi_de_referencia_no_es_un_numero_fijo():
    """0,80 es cierre de dosel en trigo. En un cultivo de porte bajo no se alcanza
    nunca y el atraso quedaria sin medir en todos los estratos."""
    assert isinstance(es.FRACCION_REFERENCIA, float)
    assert 0.0 < es.FRACCION_REFERENCIA < 1.0


# --- y queda escrito en el codigo, no solo aca --------------------------------

def _plano(t):
    return ' '.join((t or '').split())


def test_el_codigo_declara_sobre_que_cultivo_se_midio_cada_default():
    """Un default medido sin decir sobre que se midio es indistinguible de un
    numero inventado. El proximo que lo lea tiene que poder juzgarlo."""
    import inspect
    fuente = inspect.getsource(cri)
    assert 'TRIGO' in fuente.upper(), 'el piso de escala no declara su origen'
    assert 'recalibrar' in fuente.lower()
