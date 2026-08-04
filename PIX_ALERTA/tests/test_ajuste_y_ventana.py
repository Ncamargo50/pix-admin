# -*- coding: utf-8 -*-
"""El ajuste robusto de la trayectoria, y hasta donde se puede fechar un evento.

Dos cambios que se apoyan en literatura, y por lo tanto tienen que apoyarse tambien
en una demostracion propia. Corren sin GEE.
"""
import numpy as np
import pytest

from pix_alerta import criterio as cri


# --- 1. EL AJUSTE ROBUSTO -----------------------------------------------------

def _mco(t, y):
    """Minimos cuadrados: (pendiente, ordenada)."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    p = np.polyfit(t, y, 1)
    return float(p[0]), float(p[1])


def _theilsen(t, y):
    """Mediana de las pendientes de todos los pares, como `ee.Reducer.sensSlope`."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    n = len(t)
    pend = [(y[j] - y[i]) / (t[j] - t[i])
            for i in range(n) for j in range(i + 1, n) if t[j] != t[i]]
    m = float(np.median(pend))
    return m, float(np.median(y - m * t))


def test_el_mco_se_come_el_residuo_de_la_propia_anomalia():
    """LA AFIRMACION QUE JUSTIFICA EL CAMBIO, verificada.

    Mouret et al. 2022 senala que un pixel con anomalia real arrastra la recta de
    MCO hacia si y encoge su propio residuo — el estimador se sabotea justo cuando
    mas importa. Acá se reproduce con una serie de tendencia conocida.

    MEDIDO en GEE con `ee.Reducer.linearFit` y `ee.Reducer.sensSlope` el 2026-08-03,
    sobre esta misma serie: MCO pendiente -0,0215 / ordenada 0,531; Theil-Sen
    -0,010 / 0,500 (los valores verdaderos). Este test replica el resultado en
    numpy para que quede fijado sin depender de una conexion a GEE.
    """
    t = list(range(10))
    y = [0.50, 0.49, 0.48, 0.47, 0.46, 0.45, 0.44, 0.43, 0.42, 0.20]
    PEND_REAL, ORD_REAL = -0.01, 0.50

    m_mco, b_mco = _mco(t, y)
    m_ts, b_ts = _theilsen(t, y)

    # Theil-Sen recupera la verdad; MCO no.
    assert m_ts == pytest.approx(PEND_REAL, abs=1e-9)
    assert b_ts == pytest.approx(ORD_REAL, abs=1e-9)
    assert abs(m_mco - PEND_REAL) > abs(m_ts - PEND_REAL), 'MCO no se desvi0'

    # Y lo que importa de verdad: cuanto residuo queda para detectar.
    res_mco = y[-1] - (b_mco + m_mco * t[-1])
    res_ts = y[-1] - (b_ts + m_ts * t[-1])
    perdido = 1 - abs(res_mco) / abs(res_ts)
    assert perdido > 0.25, (
        'el MCO deberia perder una fraccion apreciable del residuo; perdi0 %.1f%%'
        % (100 * perdido))


def test_theilsen_aguanta_un_tercio_de_observaciones_anomalas():
    """Punto de ruptura ~29%: hasta ~1 de cada 3 puede ser anomalo."""
    t = list(range(12))
    y = [0.50 - 0.01 * i for i in range(12)]
    y = list(y)
    for i in (9, 10, 11):                     # 25% de la serie, contaminada
        y[i] = 0.10
    m_ts, _ = _theilsen(t, y)
    m_mco, _ = _mco(t, y)
    assert m_ts == pytest.approx(-0.01, abs=1e-9), 'Theil-Sen se movi0: %.4f' % m_ts
    assert abs(m_mco - (-0.01)) > 0.01, 'el control (MCO) no se rompi0'


def test_los_dos_ajustes_estan_declarados():
    assert cri.AJUSTE in cri.AJUSTES
    assert 'theilsen' in cri.AJUSTES


def test_el_ajuste_de_produccion_sigue_siendo_mco():
    """La regla de la casa: cambiar produccion exige razon POSITIVA medida.

    Theil-Sen tiene respaldo bibliografico y demostracion numerica, pero cambiar el
    ajuste **invalida la calibracion**: la tasa de falsa alarma se midi0 con MCO. Si
    este test falla, alguien movi0 el default sin correr
    `medicion/calibrar_criterio.py --ajuste theilsen` y `medicion/sensibilidad.py`.
    """
    assert cri.AJUSTE == 'mco', (
        'el ajuste de produccion cambi0 a %r: verificar que la tasa empirica y la '
        'sensibilidad se hayan re-medido con ese ajuste' % cri.AJUSTE)


# --- 2. HASTA DONDE SE PUEDE FECHAR UN EVENTO --------------------------------

def test_dt_max_declarado_y_coherente_con_la_cadencia():
    """El tope tiene que ser mayor que la revisita nominal y menor que el hueco
    maximo medido, o no separa nada."""
    assert isinstance(cri.DT_MAX_DIAS, int)
    assert cri.DT_MAX_DIAS > 10, 'por debajo de dos pasadas, marcaria casi siempre'
    assert cri.DT_MAX_DIAS < 66, 'el hueco maximo medido en Santa Cruz es 66 dias'


def _imprecisa(dt):
    """Replica la regla de `criterio.evaluar`."""
    return bool(dt is not None and dt > cri.DT_MAX_DIAS)


def test_una_escena_reciente_permite_fechar_el_evento():
    assert _imprecisa(5) is False
    assert _imprecisa(cri.DT_MAX_DIAS) is False


def test_un_hueco_largo_obliga_a_acotar_en_vez_de_fechar():
    """Patron Δt_max de Sen4CAP: se degrada la resolucion del producto, no se
    inventa la fecha."""
    assert _imprecisa(cri.DT_MAX_DIAS + 1) is True
    assert _imprecisa(66) is True


def test_sin_escena_previa_no_se_afirma_precision():
    """Sin observacion anterior no hay intervalo, y tampoco hay que fingir uno."""
    assert _imprecisa(None) is False
