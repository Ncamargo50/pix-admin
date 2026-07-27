# -*- coding: utf-8 -*-
"""La distincion que decide si un producto de alerta miente: "no hay nada" vs
"no pude mirar".

MEDIDO 2026-07-27 sobre la campaña de trigo de Santo Antonio / Sao Francisco: 25 y
50 escenas S2 en catalogo, pero solo 16% y 30% de observaciones plenas, y ningun
lote llegando a las 7 que pide el criterio. La corrida terminaba con:

    TRIGO   SANTO_ANTONIO   sin novedad
    TRIGO   SAO_FRANCISCO   sin novedad
    0 entregable(s), 2 sin novedad, 0 fallo(s)

Es decir: el cliente habria leido "sin novedad" todos los dias de la campaña sin
que el motor hubiera evaluado un solo lote. El modo de falla TRANQUILIZA, que es la
peor forma en que puede fallar una alerta — un fallo ruidoso se arregla, uno que
tranquiliza se descubre con el cultivo perdido.

Estas pruebas fijan que los dos casos no puedan volver a salir con el mismo codigo
ni con el mismo rotulo.
"""
import pytest

from pix_alerta import correr_todos as ct
from pix_alerta import main as m


def test_los_codigos_son_distintos():
    """Si comparten valor, ninguna capa de arriba puede distinguirlos."""
    codigos = [m.ENTREGADO, m.SIN_NOVEDAD, m.NO_EVALUABLE, m.FUERA_CAMPANA]
    assert len(set(codigos)) == 4


def test_no_evaluable_no_cuenta_como_fallo():
    """No poder mirar no es un error del programa: no tiene que tumbar la corrida de
    los demas clientes ni pintar el job de rojo."""
    assert m.NO_EVALUABLE in m.NO_FALLO
    assert m.FUERA_CAMPANA in m.NO_FALLO


@pytest.mark.parametrize('rc,esperado', [
    (m.ENTREGADO, 'ENTREGADO'),
    (m.SIN_NOVEDAD, 'sin novedad'),
    (m.NO_EVALUABLE, 'NO EVALUABLE'),
    (m.FUERA_CAMPANA, 'fuera de campana'),
    (7, 'FALLO'),
])
def test_cada_codigo_tiene_su_propio_rotulo(rc, esperado):
    linea = ct._resumen({'cliente': 'X', 'sitio': 'S', 'rc': rc, 'error': None})
    assert esperado in linea


def test_no_evaluable_nunca_se_lee_como_sin_novedad():
    """La prueba que importa: son la misma pantalla para el cliente."""
    ciego = ct._resumen({'cliente': 'TRIGO', 'sitio': 'SANTO_ANTONIO',
                         'rc': m.NO_EVALUABLE, 'error': None})
    assert 'sin novedad' not in ciego


def test_un_codigo_desconocido_es_fallo_y_no_silencio():
    """Si mañana alguien devuelve un codigo nuevo sin declararlo, tiene que verse
    como fallo, no colarse como una corrida tranquila."""
    assert 'FALLO' in ct._resumen({'cliente': 'X', 'sitio': 'S', 'rc': 99,
                                   'error': None})
    assert 99 not in m.NO_FALLO
