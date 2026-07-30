# -*- coding: utf-8 -*-
"""El candidato se recalibro y quedo RECHAZADO. Y produccion quedo validada.

Este archivo fija los dos resultados para que nadie los vuelva a medir desde cero ni
encienda el candidato pensando que solo faltaba calibrarlo.

PASO 1 — igualar la tasa sobre fechas sin evento (`medicion/recalibrar.py`):

    modelo                  umbral   MEDIANA peor   MAXIMO peor
    recta (produccion)        9,21       0,31%         2,21%
    relativa_agrupada        27,00       0,24%         1,51%

PASO 2 — a tasa igualada, cual marca cosas que PERSISTEN:

    recta                 1,14 a 2,15% marcado   16,4x a 42,7x el azar   (4 lotes)
    relativa_agrupada     0,06% marcado          no computable

A la tasa que hace falta para no marcar de mas, el candidato deja de marcar.
"""
import pytest

from pix_alerta import criterio as cri


def _plano(t):
    return ' '.join((t or '').split())


def test_el_modelo_en_produccion_sigue_siendo_recta():
    """El candidato quedo rechazado por medicion, no por olvido. Si alguien cambia el
    default, este test se cae y tiene que explicar con que evidencia."""
    assert cri.MODELO == 'recta'


def test_el_candidato_sigue_disponible_para_poder_re_medirlo():
    """Rechazado no es borrado: el codigo documenta el intento y el arnes sirve para el
    proximo candidato."""
    assert 'relativa_agrupada' in cri.MODELOS


def test_queda_escrito_que_el_candidato_se_recalibro_y_por_que_se_rechazo():
    d = _plano(cri.__doc__)
    assert 'RECHAZADO' in d
    assert '27,00' in d, 'no esta el umbral al que hubo que llevarlo'
    assert 'deja de marcar' in d


def test_queda_escrita_la_persistencia_medida_de_produccion():
    """Es la validacion mas fuerte que tiene el motor hoy y no necesita verdad de campo.
    Si se pierde del docstring, la proxima auditoria la vuelve a medir desde cero."""
    d = _plano(cri.__doc__)
    assert '30,8x' in d
    for x in ('42,7x', '36,8x', '16,4x', '27,1x'):
        assert x in d, 'falta la persistencia de un lote: %s' % x


def test_queda_corregida_la_conclusion_apresurada_sobre_la_sordera():
    """Las mediciones de SD(z) y de sigma siguen siendo ciertas; lo que estaba apresurado
    era concluir de ahi que el motor fuera sordo. El modelo con las tripas arregladas
    produce PEOR salida. Si no queda escrito, se vuelve a intentar el mismo cambio."""
    d = _plano(cri.__doc__)
    assert 'NO predice la calidad de la salida' in d
    assert 'CONSERVADOR' in d


def test_se_declara_que_la_sensibilidad_sigue_sin_medir():
    """La persistencia dice que lo marcado es real; NO dice cuanto real deja pasar. Esa
    distincion es la que evita vender puntería que no esta medida."""
    d = _plano(cri.__doc__)
    assert 'SIN medir es la SENSIBILIDAD' in d
    assert 'controles.py' in d, 'no dice con que se va a medir'
