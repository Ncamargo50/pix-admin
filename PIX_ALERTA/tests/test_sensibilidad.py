# -*- coding: utf-8 -*-
"""La potencia del detector, medida — y el limite que hay que declarar al cliente.

Inyectando caidas sinteticas de magnitud conocida en la imagen REAL, sobre un parche de
0,75 ha en SANTO_ANTONIO-02 (`medicion/sensibilidad.py`):

    caida            sigma BAJO        sigma MEDIO       sigma ALTO
    CONTROL (0)       0%   no           0%   no           0%   no
    2 x ruido         0%   no          19%  0,15 ha no    5%  0,04 ha no
    3 x ruido         4%   no          36%  0,27 ha SI   18%  0,14 ha no
    5 x ruido        34%  0,25 ha SI   47%  0,35 ha SI   27%  0,20 ha SI

Y la sensibilidad NO es uniforme dentro del lote: sigma varia 6,1 veces, y sigma es lo que
divide al residuo.
"""
import pytest

from pix_alerta import criterio as cri


def _plano(t):
    return ' '.join((t or '').split())


def test_la_potencia_del_detector_esta_declarada_con_numeros():
    """Un producto de alerta sin potencia declarada no se puede ofrecer: el cliente no
    sabe que tamano de problema espera que se vea."""
    d = _plano(cri.__doc__)
    assert 'POTENCIA DEL DETECTOR' in d.upper()
    assert '2 x ruido' in d and '5 x ruido' in d
    assert 'no ve nada' in d


def test_se_declara_que_la_sensibilidad_NO_es_uniforme_dentro_del_lote():
    """Es el limite mas importante para el cliente: hay partes del lote donde el motor es
    mas sordo, y no por el cultivo. Si no queda escrito, se vende una puntería pareja que
    no existe."""
    d = _plano(cri.__doc__)
    assert 'NO ES UNIFORME DENTRO DEL LOTE' in d.upper()
    assert '6,1 VECES' in d.upper()
    assert 'no tiene nada que ver con la sanidad del cultivo' in d


def test_se_distingue_potencia_del_detector_de_sensibilidad_a_problemas_reales():
    """Son dos cosas distintas y confundirlas seria vender una validacion que no existe.
    La inyeccion mide la potencia frente a una caida limpia; la sensibilidad real la
    miden los puntos de control a campo."""
    d = _plano(cri.__doc__)
    assert 'SENSIBILIDAD A PROBLEMAS REALES' in d.upper()
    assert 'controles.py' in d


def test_el_arnes_declara_que_un_evento_real_acumula_evidencia():
    """Una inyeccion de una sola fecha SUBESTIMA lo que el motor logra con un evento real,
    que crece y persiste. Sin esta aclaracion, la tabla se lee como si el motor fuera peor
    de lo que es."""
    import importlib
    m = importlib.import_module('medicion.sensibilidad')
    d = _plano(m.__doc__)
    assert '81,8%' in d, 'no cita la persistencia del foco real'
    assert 'acumulan evidencia' in d


def test_el_control_sin_inyeccion_es_obligatorio():
    """Sin el control, la deteccion de la magnitud mas chica podria ser simplemente la
    tasa de falsa alarma."""
    import importlib
    m = importlib.import_module('medicion.sensibilidad')
    assert 0.0 in m.MULTIPLOS, 'falta el control con inyeccion cero'
    d = _plano(m.__doc__)
    assert 'CONTROL, QUE ES OBLIGATORIO' in d.upper()


def test_la_magnitud_se_expresa_en_multiplos_del_ruido_real():
    """En unidades del indice, «0,05 de NDMI» no significa nada. En multiplos del ruido
    medido es comparable entre ejes y entre campanas."""
    import importlib
    m = importlib.import_module('medicion.sensibilidad')
    assert set(m.RUIDO) >= {'NDMI', 'NDRE'}
    assert 0.03 < m.RUIDO['NDMI'] < 0.07, 'el ruido de NDMI medido fue 0,043 a 0,060'
    assert 0.02 < m.RUIDO['NDRE'] < 0.05
