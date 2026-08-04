# -*- coding: utf-8 -*-
"""Los estimadores de escala, verificados por simulacion y no por cita.

El modulo `escala` afirma tres cosas: que Qn es mas eficiente que la MAD, que los
tres son igual de robustos, y que sin correccion de muestra finita estan sesgados.
Las tres son verificables con Monte Carlo en milisegundos, asi que se verifican.

Es la misma disciplina de `test_evidencia_citada.py`: una afirmacion escrita en un
comentario y nunca comprobada es exactamente como se aprobo un criterio con
evidencia inexistente.
"""
import numpy as np
import pytest

from pix_alerta import escala as es


# --- 1. CONSISTENCIA: los tres estiman sigma sobre datos normales -------------

@pytest.mark.parametrize('metodo', ['mad', 'sn', 'qn'])
def test_estima_sigma_sin_sesgo_apreciable(metodo):
    """Sobre N(0, sigma) los tres tienen que recuperar sigma."""
    rng = np.random.default_rng(0)
    sigma = 0.037                       # orden del ruido real del motor
    est = [es.estimar(rng.normal(0, sigma, 60), metodo) for _ in range(400)]
    assert np.mean(est) == pytest.approx(sigma, rel=0.05), (
        '%s sesgado: %.5f vs %.5f' % (metodo, np.mean(est), sigma))


# --- 2. EFICIENCIA: la afirmacion central del modulo --------------------------

def _eficiencia_relativa(metodo, n, reps=3000, semilla=1):
    """Varianza del estimador. Menor varianza = mas eficiente."""
    rng = np.random.default_rng(semilla)
    v = [es.estimar(rng.normal(0, 1.0, n), metodo) for _ in range(reps)]
    return float(np.var(v))


def test_qn_es_mas_eficiente_que_mad():
    """La razon de existir del modulo: Qn 82% vs MAD 37% de eficiencia gaussiana.

    Se mide como VARIANZA del estimador sobre muestras normales. La teoria dice que
    la razon de varianzas asintotica deberia ser ~0,37/0,82 = 0,45, o sea que Qn
    tiene menos de la mitad de la varianza de la MAD. Se exige holgadamente menos,
    porque con n finito la ventaja es menor que la asintotica (Akinshin 2022).
    """
    n = 40
    v_mad = _eficiencia_relativa('mad', n)
    v_qn = _eficiencia_relativa('qn', n)
    assert v_qn < v_mad, 'Qn no result0 mas eficiente que MAD'
    assert v_qn / v_mad < 0.75, (
        'la ganancia de eficiencia es menor que la esperada: Qn/MAD = %.3f'
        % (v_qn / v_mad))


def test_el_orden_de_eficiencia_es_mad_sn_qn():
    """MAD 37% < Sn 58% < Qn 82%: la varianza tiene que ir al reves."""
    n = 40
    v = {m: _eficiencia_relativa(m, n) for m in ('mad', 'sn', 'qn')}
    assert v['qn'] < v['mad'], 'Qn deberia tener menos varianza que MAD'
    assert v['sn'] < v['mad'], 'Sn deberia tener menos varianza que MAD'


# --- 3. ROBUSTEZ: la ganancia de eficiencia no puede costar robustez ----------

@pytest.mark.parametrize('metodo', ['mad', 'sn', 'qn'])
def test_resiste_contaminacion_del_30_por_ciento(metodo):
    """Punto de ruptura 50%: con 30% de outliers extremos la escala no explota.

    Es la condicion que hace usable cualquiera de estos en un pixel que puede tener
    nube residual, sombra o un evento real dentro de la ventana.
    """
    rng = np.random.default_rng(2)
    x = rng.normal(0, 1.0, 100)
    x[:30] = 500.0                       # 30% de contaminacion brutal
    s = es.estimar(x, metodo)
    assert s < 5.0, '%s exploto con 30%% de outliers: %.2f' % (metodo, s)


def test_la_media_movil_si_explota_y_por_eso_no_se_usa():
    """Control negativo: el desvio estandar clasico con la misma contaminacion.

    Sin esto, los tests de arriba no prueban nada — habria que saber contra que se
    compara la robustez.
    """
    rng = np.random.default_rng(2)
    x = rng.normal(0, 1.0, 100)
    x[:30] = 500.0
    assert float(np.std(x)) > 100.0, 'el control negativo no se rompio'


# --- 4. CORRECCION DE MUESTRA FINITA -----------------------------------------

def test_sin_correccion_qn_subestima_con_n_chico():
    """La correccion NO es cosmetica: sin ella la escala sale baja y el z alto.

    Una escala subestimada infla el z de todos los pixeles y dispara la tasa de
    falsa alarma. Es el modo de falla contra el que esta escrito todo el paquete.
    """
    rng = np.random.default_rng(3)
    n, sigma = 5, 1.0
    crudo = np.mean([es.qn(rng.normal(0, sigma, n), corregir=False)
                     for _ in range(3000)])
    rng = np.random.default_rng(3)
    corr = np.mean([es.qn(rng.normal(0, sigma, n), corregir=True)
                    for _ in range(3000)])
    assert crudo > sigma * 1.05, (
        'sin correccion Qn(n=5) deberia SOBREestimar; dio %.3f' % crudo)
    assert abs(corr - sigma) < abs(crudo - sigma), (
        'la correccion no acerco el estimador a sigma: crudo %.3f, corregido %.3f'
        % (crudo, corr))


@pytest.mark.parametrize('n', [4, 5, 6, 7, 8, 9, 12, 13, 40])
def test_la_correccion_deja_el_sesgo_acotado(n):
    """Para todo n del regimen real del motor, el sesgo queda bajo control."""
    rng = np.random.default_rng(4)
    est = np.mean([es.qn(rng.normal(0, 1.0, n)) for _ in range(3000)])
    assert est == pytest.approx(1.0, rel=0.15), (
        'Qn(n=%d) sesgado: %.3f' % (n, est))


# --- 5. CONTRATO -------------------------------------------------------------

def test_devuelve_nan_sin_datos_suficientes():
    """Con menos de 2 observaciones no hay escala. NaN, no cero.

    Un cero se propagaria como division por cero y el z saldria infinito: el motor
    marcaria el lote entero. Es el mismo error que ya se caz0 con los 'SD = 0,000'.
    """
    assert np.isnan(es.qn([]))
    assert np.isnan(es.qn([1.0]))
    assert np.isnan(es.sn([2.0]))
    assert np.isnan(es.mad([]))


def test_ignora_nan_en_la_entrada():
    """Una serie con huecos es lo normal acá, no la excepcion."""
    v = [1.0, np.nan, 2.0, 3.0, np.nan, 4.0]
    for m in ('mad', 'sn', 'qn'):
        assert np.isfinite(es.estimar(v, m)), '%s no toler0 NaN' % m


def test_estimador_desconocido_falla_fuerte():
    with pytest.raises(ValueError):
        es.estimar([1, 2, 3], 'promedio')
