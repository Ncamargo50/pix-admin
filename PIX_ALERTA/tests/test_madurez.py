# -*- coding: utf-8 -*-
"""Tests de pix_alerta.madurez — anclados en los CASOS MEDIDOS de la auditoria
2026-08-19 (trigo SA/SF + referencia seca de Assai). Sin GEE: numeros fijos.

Si un test de aca falla despues de tocar madurez.py, lo que se rompio es un caso
real que ya paso una vez, no una convencion.
"""
import math
import pytest
from pix_alerta import madurez as mz


# ------------------------------------------------------------------ bruma
# Valores MEDIDOS por unidad y fecha (serie SA/SF 2026, GEE + CloudScore+).
CASOS_BRUMA = [
    # (cs_med, PSRI, B2, es_bruma, etiqueta)
    (0.68, -0.047, 0.185, True,  '26-may SA-01: la bruma que fabrico la emergencia'),
    (0.62, -0.059, 0.186, True,  '26-may SA-02 b1'),
    (0.71, +0.126, 0.192, True,  '26-may b3: cs y B2 disparan aunque PSRI no'),
    (0.77, -0.038, 0.036, True,  '05-jul b1: bruma leve, B2 casi normal'),
    (0.78, -0.032, 0.038, True,  '05-jul b2'),
    (0.91, +0.010, 0.021, False, '31-may limpia con dosel'),
    (0.92, +0.180, 0.065, False, '22-jun limpia'),
    (1.00, +0.259, 0.021, False, '19-ago limpia senescente (PSRI alto NO es bruma)'),
]


@pytest.mark.parametrize('cs, psri, b2, esperado, caso', CASOS_BRUMA,
                         ids=[c[-1][:30] for c in CASOS_BRUMA])
def test_bruma_casos_medidos(cs, psri, b2, esperado, caso):
    es, razon = mz.bruma(cs, psri, b2)
    assert es is esperado, caso
    assert (razon != '') is esperado


def test_bruma_suelo_desnudo_no_es_bruma():
    # PRIMER INTENTO FALLIDO de esta compuerta: B2_MAX=0,06 excluia TODAS las fechas
    # de suelo desnudo (abril-mayo, B2 0,07-0,13). El suelo despejado es brillante en
    # azul y NO es bruma. Este test fija la leccion.
    for b2 in (0.070, 0.096, 0.113, 0.131):
        es, _ = mz.bruma(0.89, +0.30, b2)
        assert not es, 'suelo desnudo despejado (B2 %.3f) no debe excluirse' % b2


def test_bruma_sin_datos_auxiliares_no_excluye():
    # 'no tengo el dato' no puede volverse 'excluido': se declara, no se descarta.
    assert mz.bruma(None, None, None) == (False, '')


def test_filtrar_bruma_separa_y_explica():
    serie = [dict(fecha='2026-05-26', cs_med=0.68, PSRI=-0.047, B2=0.185, CIre=0.97),
             dict(fecha='2026-05-31', cs_med=0.91, PSRI=0.010, B2=0.021, CIre=3.36)]
    limpias, excl = mz.filtrar_bruma(serie)
    assert [x['fecha'] for x in limpias] == ['2026-05-31']
    assert excl[0]['fecha'] == '2026-05-26' and 'cs_med' in excl[0]['razon']


# ------------------------------------------------------------------ factor S2C
# Los 7 pares MEDIDOS (2026-08-19, s06_analisis): (CIre_S2C, interpolacion S2A/B).
PARES_MEDIDOS = [
    dict(fecha='2026-07-10', c=2.41, ref=2.77, ratio=2.41 / 2.77, ancla=('a', 'b')),
    dict(fecha='2026-07-20', c=3.27, ref=4.12, ratio=3.27 / 4.12, ancla=('a', 'b')),
    dict(fecha='2026-07-10', c=3.79, ref=4.67, ratio=3.79 / 4.67, ancla=('a', 'b')),
    dict(fecha='2026-07-10', c=4.05, ref=4.71, ratio=4.05 / 4.71, ancla=('a', 'b')),
    dict(fecha='2026-07-10', c=4.15, ref=5.30, ratio=4.15 / 5.30, ancla=('a', 'b')),
    dict(fecha='2026-07-10', c=4.23, ref=5.41, ratio=4.23 / 5.41, ancla=('a', 'b')),
    dict(fecha='2026-07-10', c=4.34, ref=5.63, ratio=4.34 / 5.63, ancla=('a', 'b')),
]


def test_ajuste_b_reproduce_la_medicion():
    b, propio = mz.ajustar_b(PARES_MEDIDOS)
    assert propio
    assert b == pytest.approx(-0.050, abs=0.005)
    # el modelo reproduce el regimen medido: ~0,78 con dosel cerrado, ~1 sin dosel
    assert mz.r_de(5.0, b) == pytest.approx(0.75, abs=0.03)
    assert mz.r_de(0.0, b) == 1.0
    assert mz.r_de(0.5, b) >= 0.96


def test_ajuste_b_sin_pares_usa_defecto_y_lo_declara():
    b, propio = mz.ajustar_b([], b_defecto=-0.05)
    assert (b, propio) == (-0.05, False)


def test_correccion_consistente_ida_y_vuelta():
    # c_obs = c_ab * r(c_ab): corregir el observado debe devolver c_ab exacto.
    b = -0.05
    for c_ab in (0.3, 0.7, 1.0, 2.0, 3.5, 4.4):
        c_obs = c_ab * mz.r_de(c_ab, b)
        assert mz.corregir_cire(c_obs, 'C', b) == pytest.approx(c_ab, rel=1e-6)


def test_correccion_no_toca_s2a_s2b():
    assert mz.corregir_cire(3.0, 'A', -0.05) == 3.0
    assert mz.corregir_cire(3.0, 'B', -0.05) == 3.0


def test_correccion_menor_que_el_factor_constante_en_cire_bajo():
    # LA LECCION: el factor constante 0,79 inflaba el CIre senescente ~15-20 %.
    # Por nivel, un CIre observado de 0,54 (SA-01, 19-ago) se corrige mucho menos.
    b = -0.05
    corr = mz.corregir_cire(0.54, 'C', b)
    assert corr < 0.54 / 0.79 * 0.90    # bien por debajo de la correccion constante
    assert corr > 0.54                   # pero corrige algo (b<0)


def test_pares_s2c_excluye_subida_rapida():
    # 31-may: anclas 26-may (0,97... pero esa fecha es bruma; usamos un caso sintetico
    # con la misma forma): la serie se multiplica x3 entre anclas -> el par NO vale.
    serie = [dict(fecha='2026-05-26', sat='B', CIre=1.0),
             dict(fecha='2026-05-31', sat='C', CIre=2.43),
             dict(fecha='2026-06-02', sat='A', CIre=3.32)]
    assert mz.pares_s2c(serie) == []
    # meseta: mismo espaciado, sin salto -> el par SI vale
    serie2 = [dict(fecha='2026-07-05', sat='B', CIre=5.25),
              dict(fecha='2026-07-10', sat='C', CIre=4.34),
              dict(fecha='2026-07-15', sat='B', CIre=5.83)]
    p = mz.pares_s2c(serie2)
    assert len(p) == 1 and p[0]['ratio'] == pytest.approx(4.34 / 5.54, abs=0.01)


# ------------------------------------------------------------------ estados
def test_estados_no_prometen_cosecha():
    for k, txt in mz.ESTADOS.items():
        assert 'listo' not in txt.lower()
        assert 'cosech' not in txt.lower()


def test_estado_bandas():
    assert mz.estado(10, 0.01)[1] == 0
    assert mz.estado(10, 0.10)[1] == 1   # PSRI alto: no puede ser 'verde'
    assert mz.estado(30, 0.05)[1] == 1
    assert mz.estado(55, 0.10)[1] == 2
    assert mz.estado(88, 0.26)[1] == 3


def test_estado_final_dos_ejes():
    # cortes de la referencia de Assai (p90 medidos 19-ago): CIre 0,86 · NDMI 0,071
    ref_c, ref_n = 0.86, 0.071
    # SA-01: clorofila agotada (0,54) pero NDMI 0,20 -> NO seco como la referencia
    assert mz.estado_final(0.54, 0.202, ref_c, ref_n) == 'Clorofila agotada, dosel aun humedo'
    # la propia referencia
    assert mz.estado_final(0.70, 0.025, ref_c, ref_n) == mz.SECO_REF
    # b3 verde: sin veredicto de secado
    assert mz.estado_final(3.48, 0.453, ref_c, ref_n) is None


# ------------------------------------------------------------------ inicio
def test_inicio_horquilla_completa():
    # SF: 13-may 0,51 -> 31-may 3,33 (hueco 18 dias, el famoso). La horquilla es
    # [13-may, 31-may]; nada de ± inventado.
    s = [('2026-05-11', 0.43), ('2026-05-13', 0.51), ('2026-05-31', 3.33)]
    ini = mz.inicio_cobertura(s)
    assert ini['desde'] == '2026-05-13' and ini['hasta'] == '2026-05-31'
    assert ini['hueco_dias'] == 18
    assert '2026-05-1' in ini['interp']  # cae dentro de la horquilla


def test_inicio_sin_cruce():
    assert mz.inicio_cobertura([('2026-05-01', 0.2), ('2026-05-06', 0.4)]) is None


# ------------------------------------------------------------------ lote desparejo
def test_desparejo_casos_medidos_19ago():
    import numpy as np
    rng = np.random.default_rng(0)
    # sintetico con la MISMA dispersion medida: uniforme senescente (log-SD ~0,33
    # da p90-p10 ~0,85 = SF-01) vs mezcla 60/40 de dos niveles (b12 1,5 / b3 3,5)
    unif = np.exp(rng.normal(np.log(0.55), 0.33, 2000))
    es, d = mz.desparejo(unif)
    assert not es and d < mz.UMBRAL_DESPAREJO
    mezcla = np.concatenate([np.exp(rng.normal(np.log(1.5), 0.16, 1200)),
                             np.exp(rng.normal(np.log(3.5), 0.16, 800))])
    es, d = mz.desparejo(mezcla)
    assert es and d > mz.UMBRAL_DESPAREJO


def test_desparejo_sin_pixeles_no_inventa():
    assert mz.desparejo([1.0, 2.0, 3.0]) == (False, None)


def test_colapso_de_bloques():
    # 19-ago: b12 ~72 vs b3 ~20 -> NO colapsan; si convergieran (75 vs 70) SI
    assert not mz.colapsar_bloques([72, 20])
    assert mz.colapsar_bloques([75, 70])
    assert not mz.colapsar_bloques([75])          # un solo bloque: nada que colapsar
    assert not mz.colapsar_bloques([None, 40])


# ------------------------------------------------------------------ ventana estimada
# Serie NDMI REAL de SA-01 (medida, sin bruma) + punto 21-ago S2A. Piso = p50 de la
# referencia seca Assai al 19-ago (0,0248); nivel de cruce = piso + 0,03.
SERIE_NDMI_SA01 = [('2026-05-31', 0.3819), ('2026-06-02', 0.4111), ('2026-06-05', 0.4167),
                   ('2026-06-22', 0.5323), ('2026-07-10', 0.5382), ('2026-07-15', 0.5656),
                   ('2026-08-01', 0.5128), ('2026-08-09', 0.4462), ('2026-08-19', 0.204),
                   ('2026-08-21', 0.185)]


def test_ajuste_cruce_caso_medido_sa01():
    # el arnes s13 (21-ago) dio seco(NDMI) 31-ago IC [29-ago..02-sep]
    r = mz.ajuste_cruce(SERIE_NDMI_SA01, piso=0.0248, nivel=0.0548)
    assert r is not None and r['n'] >= 5
    assert '2026-08-29' <= r['fecha'] <= '2026-09-02'
    assert r['ic'] is not None and r['ic'][0] < r['fecha'] < r['ic'][1]


def test_ajuste_cruce_pocos_puntos_no_inventa():
    # <4 puntos post-pico -> None ('no ajustable'), nunca un numero
    assert mz.ajuste_cruce(SERIE_NDMI_SA01[:8], piso=0.0248, nivel=0.0548) is None


def test_ajuste_cruce_horizonte_no_extrapola():
    # caso b2/b3 del 21-ago: serie aun alta y lenta -> el cruce caeria a >30 dias de
    # la ultima escena; eso es extrapolar la cola, no medir -> None
    s = [('2026-07-15', 0.55), ('2026-08-01', 0.53), ('2026-08-09', 0.50),
         ('2026-08-19', 0.46), ('2026-08-21', 0.45)]
    assert mz.ajuste_cruce(s, piso=0.0248, nivel=0.0548) is None


def test_ajuste_cruce_nivel_bajo_piso():
    assert mz.ajuste_cruce(SERIE_NDMI_SA01, piso=0.10, nivel=0.05) is None


def test_ajuste_cruce_recupera_sintetico():
    # logistica conocida + ruido chico: recupera el cruce con error <= 2 dias
    import numpy as np, datetime as dt
    piso, A, tau = 0.03, 0.5, 6.0
    d0 = dt.date(2026, 7, 10); t0 = 30.0
    rng = np.random.default_rng(1)
    fechas = [0, 6, 12, 18, 24, 30, 36, 42]
    s = [((d0 + dt.timedelta(days=t)).isoformat(),
          piso + A / (1 + np.exp((t - t0) / tau)) + rng.normal(0, 0.004)) for t in fechas]
    nivel = 0.06
    verdad = t0 + tau * np.log(A / (nivel - piso) - 1.0)
    r = mz.ajuste_cruce(s, piso=piso, nivel=nivel)
    est = (dt.date.fromisoformat(r['fecha']) - d0).days
    assert abs(est - verdad) <= 2.0


def test_ic_degenerado_no_publica():
    # 4 puntos EXACTOS sobre la logistica (sobreajuste maximo, rmse ~0): el caso de
    # menos confianza jamas sale con mas aplomo — None, no una fecha pelada
    import numpy as np, datetime as dt
    piso, A, tau, t0 = 0.03, 0.5, 6.0, 20.0
    d0 = dt.date(2026, 7, 15)
    s = [((d0 + dt.timedelta(days=t)).isoformat(),
          piso + A / (1 + np.exp((t - t0) / tau))) for t in (0, 8, 16, 24)]
    assert mz.ajuste_cruce(s, piso=piso, nivel=0.06) is None


def test_alcanzado_es_hecho_no_estimacion():
    # ultima medicion ya al nivel: 'alcanzado', nunca una fecha pasada como estimada
    s = SERIE_NDMI_SA01 + [('2026-08-26', 0.05)]
    r = mz.ajuste_cruce(s, piso=0.0248, nivel=0.0548)
    assert r['alcanzado'] and r['fecha'] == '2026-08-26' and r['ic'] is None


def test_sigma_min_ensancha_el_intervalo():
    # el piso de ruido medido (SIGMA_NDMI_ESCENA) debe ENSANCHAR el intervalo del
    # sobreajuste: rotulo RECHAZADO por el validador 21-ago sin esto
    import datetime as dt
    r0 = mz.ajuste_cruce(SERIE_NDMI_SA01, piso=0.0248, nivel=0.0548)
    r1 = mz.ajuste_cruce(SERIE_NDMI_SA01, piso=0.0248, nivel=0.0548,
                         sigma_min=mz.SIGMA_NDMI_ESCENA)
    D = dt.date.fromisoformat
    w0 = (D(r0['ic'][1]) - D(r0['ic'][0])).days
    w1 = (D(r1['ic'][1]) - D(r1['ic'][0])).days
    assert w1 > w0
