# -*- coding: utf-8 -*-
"""La bruma que pasa el filtro binario de nube. Caso medido, no hipotetico.

EL CASO
-------
El 2026-07-05, sobre SANTO_ANTONIO-02, el 96% de los pixeles paso el umbral binario de
CloudScore+ (0,60), la escena entro como limpia, y el lote parecio derrumbarse:

    NDVI: 0,928 (06-22)  ->  0,776 (07-05)  ->  0,928 (07-10)  ->  0,928 (07-15)

Un trigo no pierde 0,15 de NDVI y lo recupera en cinco dias. Era bruma.

Y sobrevivio a TODAS las defensas que habia:
  · SCL con dilatacion de 80 m,
  · CloudScore+ por pixel con umbral 0,60,
  · la puerta de cobertura del 70% sobre el lote,
  · y la conjuncion de dos ejes — porque **la bruma baja los dos indices JUNTOS**.

Ese ultimo punto es el que mas importa y contradice lo que el informe le dice al cliente:
la conjuncion de ejes protege contra ruido independiente del sensor, NO contra
contaminacion atmosferica.

LA DEFENSA QUE SE AGREGO
------------------------
Usar el puntaje de CloudScore+ como NUMERO y no como si/no: el promedio de `cs_cdf` sobre
el lote es la "calidad de la escena". MEDIDO sobre las 7 fechas que pasaban la puerta de
cobertura (`medicion/calidad_escena.py`):

    05-31 0,911   06-02 0,916   06-05 0,917   06-22 0,918   07-10 0,929   07-15 0,926
    07-05 0,797   <- LA UNICA por debajo de 0,90, y es el artefacto
"""
import pytest

from pix_alerta import config as cfg

# Los dos numeros que acotan el umbral, medidos.
CALIDAD_ARTEFACTO = 0.797
CALIDAD_LIMPIA_MAS_BAJA = 0.911


def test_el_piso_de_calidad_separa_el_artefacto_de_las_limpias():
    """El umbral tiene que caer ENTRE el artefacto y la escena limpia mas baja. Fuera de
    ese hueco no sirve: mas abajo deja pasar la bruma, mas arriba tira escenas buenas."""
    assert CALIDAD_ARTEFACTO < cfg.CS_MEDIO_MINIMO < CALIDAD_LIMPIA_MAS_BAJA, (
        'CS_MEDIO_MINIMO=%.3f queda fuera del hueco medido (%.3f a %.3f)'
        % (cfg.CS_MEDIO_MINIMO, CALIDAD_ARTEFACTO, CALIDAD_LIMPIA_MAS_BAJA))


def test_no_se_pierde_ninguna_escena_limpia_de_la_campana():
    """Las seis fechas limpias que pasaban la puerta de cobertura tienen que seguir
    pasando. Un filtro de bruma que tira escenas buenas cuesta mas de lo que ahorra: con
    48% de dekadas utiles medido, cada escena vale."""
    limpias = (0.911, 0.916, 0.917, 0.918, 0.929, 0.926)
    perdidas = [q for q in limpias if q < cfg.CS_MEDIO_MINIMO]
    assert not perdidas, 'el piso tira escenas limpias: %s' % perdidas


def test_el_piso_es_declarable_por_sitio():
    """En una region mas brumosa el mismo piso puede rechazar casi todo. Tiene que poder
    declararse por cliente, con el default medido a la vista."""
    campos = set(cfg.Sitio.__dataclass_fields__)
    assert 'cs_medio_minimo' in campos


def test_el_default_medido_se_usa_cuando_el_sitio_no_declara_nada():
    class _S:
        cs_medio_minimo = None
    assert cfg.valor_de(_S(), 'cs_medio_minimo',
                        cfg.CS_MEDIO_MINIMO) == cfg.CS_MEDIO_MINIMO


def test_el_criterio_aplica_la_puerta_y_declara_la_calidad_elegida():
    """No alcanza con filtrar: el resultado tiene que decir con QUE calidad se acepto la
    escena, o no se puede auditar por que se acepto."""
    import inspect

    from pix_alerta import criterio as cri
    fuente = inspect.getsource(cri.evaluar)
    assert 'cs_medio' in fuente, 'el criterio no evalua la calidad de la escena'
    assert "cfg.valor_de(sitio, 'cs_medio_minimo'" in fuente, (
        'la puerta no respeta el valor declarado por el sitio')
    assert "'cs_medio': actual.get('cs_medio')" in fuente, (
        'la calidad de la escena elegida no viaja en el resultado')


def test_sin_cloudscore_no_se_descarta_la_escena():
    """CloudScore+ tiene huecos en el archivo. Sin ese dato auxiliar no se puede juzgar la
    calidad, y descartar la escena por eso seria confundir 'no se pudo medir la calidad'
    con 'la escena es mala' — el modo de falla que este motor tiene prohibido."""
    import inspect

    from pix_alerta import criterio as cri
    fuente = inspect.getsource(cri.evaluar)
    assert 'ee.Algorithms.If(' in fuente and 'cs,' in fuente
    d = ' '.join(inspect.getsource(cri).split())
    assert 'se deja pasar y se declara' in d, (
        'no declara que sin CloudScore+ la escena pasa en vez de descartarse')


def test_queda_escrito_que_la_conjuncion_de_ejes_no_protege_de_la_bruma():
    """Es el hallazgo que contradice lo que el informe le dice al cliente. Si no queda
    escrito en el codigo, el proximo que lea el informe va a creer que la conjuncion es
    una defensa contra nube fina, y no lo es."""
    import inspect

    from pix_alerta import criterio as cri
    d = ' '.join(inspect.getsource(cri).split())
    assert 'la bruma baja los DOS indices juntos' in d
    assert 'no protege contra' in d
