"""Hace importable `pix_alerta` sin depender del directorio desde el que se invoque.

Sin esto, `pytest tests/` solo funciona parado dentro de PIX_ALERTA: desde la raiz del
workspace falla con ModuleNotFound. Un cron o un CI que corra desde otra carpeta veria las
puertas de aceptacion como un error de importacion, que es indistinguible de "no hay tests".
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
