# -*- coding: utf-8 -*-
"""La persistencia del foco: tres estados, y el tercero no puede confundirse.

LO QUE ESTA MEDIDO
------------------
El foco de 0,44 ha entregado el 2026-07-15 en SANTO_ANTONIO-02 ya estaba marcado en la
escena del 2026-07-10 en el 81,8% de su superficie, contra un 2,72% esperado por azar:
**30 veces el azar**. No es ruido — ya estaba, por debajo del tamano reportable.

Y una conclusion equivocada que costo corregir: comparar los POLIGONOS entregados de una
fecha contra los de la anterior dio 0% de solape, y parecia decir que el motor marcaba
ruido. Era la pregunta equivocada: un foco entregado es lo que sobrevivio a la unidad
minima de mapeo, asi que preguntaba «¿ya era REPORTABLE?» y no «¿ya ESTABA?».
"""
import pytest

from pix_alerta import focos as fo


def _plano(t):
    return ' '.join((t or '').split())


def test_hay_tres_estados_y_no_evaluable_no_es_sin_confirmar():
    """Es la regla del motor: 'no pude mirar' nunca comparte rotulo con 'no hay'. Aca:
    si no existe escena anterior utilizable, no se sabe — y eso no es 'sin confirmar'."""
    import inspect
    fuente = inspect.getsource(fo)
    for estado in ("'persistente'", "'sin_confirmar'", "'no_evaluable'"):
        assert estado in fuente, 'falta el estado %s' % estado
    d = _plano(fuente)
    assert "'no se sabe' no comparte rotulo con 'no'" in d


def test_sin_confirmar_no_significa_falso():
    """Un evento REAL Y NUEVO tampoco estaba en la escena anterior. Si el informe o el
    codigo trataran 'sin_confirmar' como 'descartado', el motor perderia justamente los
    eventos nuevos, que son los que hay que ver."""
    import inspect
    d = _plano(inspect.getsource(fo))
    assert 'NO significa falso' in d
    assert 'un evento nuevo tampoco estaba' in d


def test_es_etiqueta_y_no_filtro_y_dice_por_que():
    """Filtrar por persistencia agregaria un retraso de una imagen a TODA alerta real."""
    import inspect
    d = _plano(inspect.getsource(fo))
    assert 'ETIQUETA Y NO FILTRO' in d.upper()
    assert 'retraso de una imagen' in d


def test_el_azar_es_la_referencia_y_no_un_umbral_inventado():
    """Un solape del 80% no dice nada por si solo: hay que compararlo con el solape que
    daria tirar los focos al azar, que es la fraccion del area que ya estaba marcada."""
    import inspect
    fuente = inspect.getsource(fo._persistencia)
    assert 'reduceRegion' in fuente
    d = _plano(inspect.getsource(fo))
    assert 'se solaparian aproximadamente en esa proporcion' in d
    assert fo.FACTOR_PERSISTENCIA >= 2.0, (
        'con un factor menor a 2 el azar se confunde con persistencia')


def test_queda_registrada_la_conclusion_equivocada_y_por_que_lo_era():
    """Si no queda escrito, el proximo que compare poligono contra poligono va a volver a
    concluir que el motor marca ruido."""
    import inspect
    d = _plano(inspect.getsource(fo))
    assert '0% de solape' in d
    assert 'ya era REPORTABLE' in d
    assert '30 VECES EL AZAR' in d.upper()


def test_solo_se_calcula_cuando_hay_focos():
    """Sin focos no hay nada que confirmar, y cuesta una evaluacion extra del criterio.
    En la mayoria de las corridas no hay ninguno."""
    assert fo._persistencia(None, None, '2026-07-15', []) == (None, None, None)
