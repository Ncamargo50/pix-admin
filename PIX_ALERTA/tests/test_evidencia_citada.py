# -*- coding: utf-8 -*-
"""La evidencia que el codigo cita TIENE que existir en el repositorio.

POR QUE ESTE TEST EXISTE
------------------------
AUDITADO 2026-07-29. `criterio.py` afirmaba en su docstring:

    "Tasa de marcado sobre fechas SIN evento (...). Arnes:
     `medicion/calibrar_criterio.py`"

seguido de una tabla de tasas por lote que era LA evidencia que justificaba poner el
criterio v2 en produccion. **Ese archivo nunca existio en el repositorio**: no estaba
en el historial de git ni en `.gitignore`. `focos.py` y `config.py` lo citaban tambien.

O sea que el numero central del producto —la tasa de falsa alarma— no se podia
reproducir, y nadie lo iba a notar leyendo el codigo, porque la cita se ve igual sea
el archivo real o no.

Un motor cuyo criterio se justifica con mediciones NECESITA que las mediciones se
puedan volver a correr. Este test es la puerta: si alguien cita un arnes, el arnes
existe. Si el arnes se borra, el test se cae y hay que sacar la cita o traer el
archivo — las dos salidas son honestas; la actual no lo era.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Se revisan los modulos del motor y los documentos que se le muestran a alguien.
# No los tests (pueden citar archivos de ejemplo) ni el pycache.
CARPETAS = ('pix_alerta', 'scripts', 'medicion')
PATRON = re.compile(r'(?:medicion|scripts|tests)/[A-Za-z0-9_]+\.py')


def _fuentes():
    for c in CARPETAS:
        d = os.path.join(RAIZ, c)
        if not os.path.isdir(d):
            continue
        for nom in sorted(os.listdir(d)):
            if nom.endswith('.py'):
                yield os.path.join(d, nom)


def test_todo_arnes_citado_por_el_motor_existe():
    faltan = []
    for ruta in _fuentes():
        with open(ruta, encoding='utf-8') as fh:
            txt = fh.read()
        for cita in sorted(set(PATRON.findall(txt))):
            if not os.path.exists(os.path.join(RAIZ, cita)):
                faltan.append('%s cita %s' % (os.path.relpath(ruta, RAIZ), cita))
    assert not faltan, (
        'el codigo cita evidencia que no esta en el repositorio, asi que no se '
        'puede reproducir:\n  ' + '\n  '.join(faltan))


def test_el_criterio_en_produccion_declara_su_tasa_medida():
    """No alcanza con que el arnes exista: el criterio que corre tiene que decir que
    tasa se le midio y sobre cuantas fechas. Un criterio de alerta sin tasa declarada
    no se le puede entregar a nadie."""
    from pix_alerta import criterio as cri
    d = ' '.join((cri.__doc__ or '').split())
    assert 'calibrar_criterio' in d, 'no dice con que se midio'
    assert 'combinaciones lote-fecha' in d, 'no dice sobre cuantos datos'
    # y tiene que declarar que el maximo puede incluir eventos reales
    assert 'cota superior' in d, (
        'no declara que el maximo no es la falsa alarma sino una cota superior')
