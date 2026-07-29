# -*- coding: utf-8 -*-
"""Estratos de siembra: la referencia de «sano» que NO estaba dentro del lote.

Encontrado el 2026-07-29 mirando la imagen del 31/05 de Santo Antonio-02: el lote
esta sembrado en TRES pasadas y los bloques se ven a simple vista. **Ninguno de los
dos criterios del motor lo habria detectado** — no hubo cambio brusco (el criterio
temporal no marca) y dentro de cada bloque todos los pixeles estan igual de
atrasados entre si (el espacial tampoco).

MEDIDO sobre los 4 lotes:

    SANTO_ANTONIO-02   coherencia 0,93  -> 3 estratos de 39,0 / 37,5 / 38,7 ha
                       atrasos: 0 / 12,0 / 36,9 dias   (declarado: 0 / 3 / 9)
    SANTO_ANTONIO-01   coherencia 0,69  -> SIN estratos
    SAO_FRANCISCO-01   coherencia 0,78  -> SIN estratos
    SAO_FRANCISCO-02   coherencia 0,73  -> SIN estratos

Que RECHACE tres de cuatro es la parte que mas importa: un metodo que siempre
encuentra tres bloques no sirve para nada.
"""
import pytest

from pix_alerta import estratos as es


# --- el contraste, que es el producto -----------------------------------------

def test_el_contraste_devuelve_la_diferencia_entre_medido_y_declarado():
    """La diferencia ES el producto: dice cuanto mas tardo el bloque en implantarse
    de lo que su fecha de siembra explica."""
    medido = {3: {'atraso_dias': 0.0}, 2: {'atraso_dias': 12.0},
              1: {'atraso_dias': 36.9}}
    c = es.contraste(medido, {3: 0, 2: 3, 1: 9})
    assert c[3]['diferencia'] == 0.0
    assert c[2]['diferencia'] == 9.0
    assert c[1]['diferencia'] == 27.9        # el caso real de Santo Antonio-02


def test_sin_dato_declarado_no_se_inventa_una_diferencia():
    """Si el cliente no declaro la fecha de ese bloque, la diferencia es None. No se
    supone cero, que equivaldria a afirmar que no hay anomalia."""
    c = es.contraste({1: {'atraso_dias': 30.0}}, {})
    assert c[1]['diferencia'] is None
    assert c[1]['medido'] == 30.0


def test_sin_medicion_tampoco_se_inventa():
    c = es.contraste({1: {'atraso_dias': None}}, {1: 9})
    assert c[1]['diferencia'] is None


# --- la puerta que evita inventar estratos ------------------------------------

def test_la_coherencia_minima_es_exigente():
    """Con 3 estratos, una clasificacion al azar da coherencia ~0,33. El umbral
    tiene que estar MUY por encima de eso o cualquier ruido pasa.

    Medido: los tres lotes de una sola siembra dieron 0,69 / 0,78 / 0,73 y el lote
    con tres pasadas reales dio 0,93. Para n=3 el umbral cae en 0,80 y los separa
    con margen."""
    u3 = es.umbral_coherencia(3)
    assert u3 >= 0.75, 'demasiado permisivo: entraria ruido'
    assert u3 <= 0.90, 'demasiado estricto: rechazaria bloques reales'
    # queda por encima de los tres lotes sin estratos y por debajo del que si tiene
    assert 0.78 < u3 < 0.93


def test_el_umbral_de_coherencia_sale_de_la_nula_no_de_un_cultivo():
    """El umbral NO puede ser un numero fijo ajustado a los 4 lotes de trigo: el
    motor tiene que servir para otros cultivos y para otra cantidad de pasadas.

    Se deriva de la nula: con `n` estratos, clasificar al azar acierta 1/n. El
    umbral se pone a `FACTOR_COHERENCIA` del camino entre esa nula y el 1,0."""
    # siempre MUY por encima de lo que da el azar
    for n in (2, 3, 4, 5, 8):
        assert es.umbral_coherencia(n) > 1.0 / n + 0.3, n
        assert es.umbral_coherencia(n) < 1.0
    # con mas estratos la nula baja, asi que el umbral tambien puede bajar: exigir
    # 0,85 con 8 bloques seria absurdo cuando el azar da 0,125
    assert es.umbral_coherencia(2) > es.umbral_coherencia(5)


def test_el_ndvi_de_referencia_sale_del_rango_observado_del_propio_cultivo():
    """El atraso se mide por el dia en que cada estrato ALCANZA un NDVI. Ese nivel
    NO puede ser fijo: 0,80 es cierre de dosel en trigo, pero es inalcanzable en un
    cultivo de porte bajo y esta saturado en caña. Se toma una fraccion del rango
    que el propio lote recorrio en la ventana, que es una medida del cultivo real.

    Tiene que caer lejos de los dos extremos: pegado al minimo mide emergencia (muy
    ruidosa) y pegado al maximo cae en saturacion, donde todos los estratos llegan
    casi juntos y el atraso se aplasta."""
    assert 0.5 <= es.FRACCION_REFERENCIA <= 0.85
    # sobre el rango real medido en trigo (0,15 -> 0,90) cae donde tiene que caer
    ref = 0.15 + es.FRACCION_REFERENCIA * (0.90 - 0.15)
    assert 0.6 <= ref <= 0.85


# --- el orden de los estratos -------------------------------------------------

def _plano(t):
    """Texto sin saltos de linea, para que un `wrap` no rompa una prueba de prosa."""
    return ' '.join((t or '').split())


def test_el_estrato_1_es_el_mas_atrasado():
    """Convencion fijada: 1 = mas atrasado, n = mas adelantado. El informe y el
    contraste dependen de ella; invertirla daria el atraso al reves."""
    assert 'estrato 1 es el MAS ATRASADO' in _plano(es.segmentar.__doc__)


def test_el_modulo_declara_que_puede_no_haber_estratos():
    """Un lote sembrado de una sola vez NO tiene estratos, y el modulo tiene que
    decirlo en vez de partirlo en tres igual. Es la propiedad que se verifico a
    campo: de 4 lotes, 3 fueron RECHAZADOS por coherencia."""
    d = _plano(es.__doc__)
    assert 'no hay estratos que encontrar' in d
    assert 'en vez de inventar tres' in d
