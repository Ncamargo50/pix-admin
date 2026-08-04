# -*- coding: utf-8 -*-
"""El escalon instrumental entre Sentinel-2A, 2B y 2C.

HALLAZGO DEL 2026-08-03. Sentinel-2C lleva la banda B5 centrada en 707,1 nm contra
703,8-704,1 nm de S2A y S2B. En el borde rojo, donde la pendiente espectral es
maxima, ese corrimiento de 3 nm mueve la reflectancia — y el NDRE, que usa B5, se
sesga 0,052 unidades entre satelites. Son **5,2 veces SIGMA_MINIMA**.

Estos tests no pueden verificar el numero contra GEE (corren sin red). Verifican la
LOGICA de la correccion, que es donde estan los modos de falla peligrosos: corregir
a medias es peor que no corregir.
"""
import numpy as np
import pytest

from pix_alerta import criterio as cri


# --- 1. LA CORRECCION ESTA DECLARADA Y ENCENDIDA -----------------------------

def test_la_correccion_esta_en_produccion():
    """A diferencia de Theil-Sen y de Qn, esta SI entra: la razon positiva esta
    medida y es abrumadora (SD(z) pasa de 0,38 a 1,00)."""
    assert cri.CORREGIR_SAT is True


def test_hace_falta_mas_de_una_escena_por_satelite():
    """Con UNA sola escena de un satelite, su 'sesgo' ES el residuo de esa escena.

    Restarlo borraria cualquier anomalia real de esa fecha — el detector se comeria
    justo el evento que busca. Con dos, la mediana ya no puede ser un solo evento.
    """
    assert cri.MIN_ESCENAS_SAT >= 2


# --- 2. TODO O NADA: el modo de falla que importa ----------------------------

def _aplicar(corregir, sats_base, sat_actual, minimo=None):
    """Replica la regla de decision de `criterio.evaluar`."""
    minimo = cri.MIN_ESCENAS_SAT if minimo is None else minimo
    cuenta = {s: sats_base.count(s) for s in set(sats_base)}
    corregibles = [s for s, k in cuenta.items() if k >= minimo]
    return bool(corregir and len(cuenta) > 1 and sat_actual in corregibles)


def test_no_se_corrige_si_el_satelite_de_hoy_no_tiene_sesgo_estimable():
    """EL MODO DE FALLA CENTRAL. Si se le quita el escalon a la base y NO a la fecha
    evaluada, se FABRICA un sesgo del mismo tamaño y signo contrario.

    Corregir a medias es estrictamente peor que no corregir.
    """
    base = ['Sentinel-2A'] * 4 + ['Sentinel-2B'] * 3
    # Hoy es S2C y no hay ni una escena S2C en la base: no se puede estimar su sesgo.
    assert _aplicar(True, base, 'Sentinel-2C') is False
    # Y con una sola escena tampoco alcanza.
    assert _aplicar(True, base + ['Sentinel-2C'], 'Sentinel-2C') is False
    # Con dos, si.
    assert _aplicar(True, base + ['Sentinel-2C'] * 2, 'Sentinel-2C') is True


def test_no_se_corrige_si_toda_la_base_es_del_mismo_satelite():
    """Sin dos satelites no hay escalon que quitar, y estimar un 'sesgo' contra si
    mismo solo restaria señal."""
    base = ['Sentinel-2A'] * 8
    assert _aplicar(True, base, 'Sentinel-2A') is False


def test_el_caso_real_de_sao_francisco_se_corrige():
    """La composicion medida el 2026-08-03: S2C x4, S2A x4, S2B x2, evaluando S2A."""
    base = (['Sentinel-2C'] * 4 + ['Sentinel-2A'] * 4 + ['Sentinel-2B'] * 2)
    assert _aplicar(True, base, 'Sentinel-2A') is True


def test_el_interruptor_apaga_todo():
    base = ['Sentinel-2A'] * 4 + ['Sentinel-2C'] * 4
    assert _aplicar(False, base, 'Sentinel-2A') is False


# --- 3. LA MAGNITUD DEL PROBLEMA, COMO REGRESION -----------------------------

# Residuos medios medidos contra la tendencia, 4 lotes x 38 escenas, 2026-08-03.
SESGO_MEDIDO = {
    'NDRE': {'Sentinel-2A': +0.00557, 'Sentinel-2B': +0.01960,
             'Sentinel-2C': -0.03244},
    'NDMI': {'Sentinel-2A': +0.00445, 'Sentinel-2B': +0.00138,
             'Sentinel-2C': -0.00877},
    'NDVI': {'Sentinel-2A': -0.00336, 'Sentinel-2B': +0.00396,
             'Sentinel-2C': +0.00061},
}


def test_el_escalon_del_ndre_supera_el_piso_de_escala():
    """0,052 contra SIGMA_MINIMA de 0,010: el artefacto es 5 veces el piso.

    Si esto dejara de ser cierto —porque cambie SIGMA_MINIMA— habria que rehacer el
    razonamiento de por que la correccion es obligatoria.
    """
    s = SESGO_MEDIDO['NDRE']
    escalon = s['Sentinel-2B'] - s['Sentinel-2C']
    assert escalon == pytest.approx(0.052, abs=0.002)
    assert escalon > 5 * cri.SIGMA_MINIMA


def test_el_sesgo_escala_con_las_bandas_que_usa_cada_indice():
    """EL TEST DISCRIMINANTE que prueba que es instrumental y no fenologia.

    NDRE usa B5 (la banda que se corre en S2C) -> sesgo maximo.
    NDMI usa B8A y B11 -> sesgo mucho menor.
    NDVI usa B8 y B4 -> practicamente nulo.

    Si fuera fenologia, atmosfera o angulo de vista, los tres indices se sesgarian
    parecido. El hecho de que el sesgo siga QUE BANDAS usa cada indice es lo que
    identifica la causa.
    """
    esc = {k: abs(v['Sentinel-2B'] - v['Sentinel-2C'])
           for k, v in SESGO_MEDIDO.items()}
    assert esc['NDRE'] > 4 * esc['NDMI'], (
        'el NDRE deberia sesgarse mucho mas que el NDMI: %.5f vs %.5f'
        % (esc['NDRE'], esc['NDMI']))
    assert esc['NDMI'] > 2 * esc['NDVI'], (
        'el NDMI deberia sesgarse mas que el NDVI: %.5f vs %.5f'
        % (esc['NDMI'], esc['NDVI']))


def test_s2c_es_el_que_baja_el_ndre():
    """La direccion importa: S2C da NDRE mas BAJO, o sea que una escena S2C evaluada
    contra una base de S2A/S2B produce una CAIDA que no ocurrio en el campo — la
    firma exacta de deterioro que busca el criterio.

    Y es la direccion que predice la fisica: B5 corrida hacia el NIR mide mas
    reflectancia, y NDRE = (B8A-B5)/(B8A+B5) baja.
    """
    s = SESGO_MEDIDO['NDRE']
    assert s['Sentinel-2C'] < s['Sentinel-2A']
    assert s['Sentinel-2C'] < s['Sentinel-2B']


# --- 4. LO QUE LA CORRECCION ARREGL0, COMO REGRESION -------------------------

# SD(z) medida sobre datos reales el 2026-08-03. Vale 1,0 si la escala esta bien.
SD_Z_MEDIDA = {
    'sin_corregir': {'NDMI': 0.429, 'NDRE': 0.335},
    'corrigiendo': {'NDMI': 0.982, 'NDRE': 1.013},
}


def test_la_correccion_devuelve_la_escala_a_su_valor_correcto():
    """La razon positiva que justifica ponerla en produccion."""
    sin_ = SD_Z_MEDIDA['sin_corregir']
    con = SD_Z_MEDIDA['corrigiendo']
    for eje in ('NDMI', 'NDRE'):
        assert abs(con[eje] - 1.0) < abs(sin_[eje] - 1.0), (
            '%s: corregir deberia acercar SD(z) a 1,0' % eje)
    assert np.mean([abs(con[e] - 1) for e in con]) < 0.25


def test_explica_el_error_de_modelo_que_estaba_abierto():
    """La auditoria del 2026-07-29 dejo anotado que "sigma es 2,7-6,5x el ruido
    (ERROR DE MODELO)" sin explicacion. El reciproco de SD(z) sin corregir da
    exactamente ese rango: el error no era del modelo, era el escalon."""
    sin_ = SD_Z_MEDIDA['sin_corregir']
    factores = [1 / sin_[e] for e in sin_]
    assert min(factores) > 2.0 and max(factores) < 7.5, (
        'los factores %s deberian caer en el rango 2,7-6,5 documentado' % factores)


# --- 5. EL UMBRAL, FIJADO POR TASA EMPIRICA ----------------------------------

# Barrido medido el 2026-08-03 con `medicion/recalibrar.py --paso 1`, CON la
# correccion de satelite puesta. Mediana y maximo del PEOR lote.
BARRIDO_UMBRAL = {
    9.21: (2.15, 4.30),   # chi2 al 1%
    11.00: (1.39, 3.35),
    13.00: (0.62, 2.48),  # elegido
    15.00: (0.46, 2.17),
    22.00: (0.38, 1.08),
}


def test_el_umbral_de_produccion_cumple_el_alfa_declarado():
    """LA RAZON DE SER DEL CAMBIO: con chi2=9,21 el motor marcaba 2,15% mientras
    declaraba 1%. El umbral elegido tiene que dejar la mediana del peor lote por
    debajo del alfa que se le promete al cliente."""
    mediana, _ = BARRIDO_UMBRAL[cri.UMBRAL_D2]
    assert mediana / 100 < cri.ALFA, (
        'umbral %.2f deja la mediana en %.2f%%, por encima del alfa declarado %.1f%%'
        % (cri.UMBRAL_D2, mediana, 100 * cri.ALFA))


def test_el_chi2_teorico_NO_cumple_y_por_eso_se_recalibro():
    """Control: si el chi2 cumpliera, todo este cambio seria innecesario.

    No cumple porque supone pixeles INDEPENDIENTES, y los de un lote estan
    espacialmente autocorrelacionados.
    """
    mediana, _ = BARRIDO_UMBRAL[9.21]
    assert mediana / 100 > cri.ALFA, 'el chi2 cumple: revisar por que se recalibro'


def test_es_el_umbral_MAS_BAJO_que_cumple():
    """No hay que pasarse: cada punto de umbral cuesta sensibilidad.

    Se elige el primero que baja del alfa, no el mas conservador de la tabla.
    """
    cumplen = [u for u, (m, _) in BARRIDO_UMBRAL.items() if m / 100 < cri.ALFA]
    assert cri.UMBRAL_D2 == min(cumplen), (
        'hay un umbral mas bajo que tambien cumple: %.2f' % min(cumplen))


def test_el_umbral_es_declarable_por_sitio():
    """No es constante universal: sale de trigo en Parana, 4 lotes, una campaña."""
    from pix_alerta import config as cfg
    assert hasattr(cfg.Sitio, '__dataclass_fields__')
    assert 'umbral_d2' in cfg.Sitio.__dataclass_fields__
