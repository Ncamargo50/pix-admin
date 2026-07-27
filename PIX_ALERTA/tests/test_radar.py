# -*- coding: utf-8 -*-
"""Puertas de la continuidad por radar.

El radar existe por UNA medicion: el poder de discriminacion del motor sigue a la
COBERTURA, no al indice. Misma configuracion, distinto año: 16,0% de observaciones
opticas plenas dio lift 36x; 11,8% dio 6,7x. Cambiar de indice compro ~2x; la
disponibilidad de imagen vale ~5x.

Lo que se prueba acá es la logica de decision, no el algebra de bandas.
"""
import numpy as np
import pandas as pd
import pytest

from pix_alerta import radar as rad


def serie_radar(n_lotes=20, n_fechas=10, semilla=0, desde='2025-11-01'):
    """Campaña sin eventos: todos los lotes siguen la misma trayectoria de RVI."""
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range(desde, periods=n_fechas, freq='12D')   # revisita real
    tray = np.linspace(0.35, 0.65, n_fechas)                      # crece la biomasa
    filas = []
    for i in range(n_lotes):
        off = rng.normal(0, 0.02)
        for j, f in enumerate(fechas):
            filas.append({'lote_id': 'L%03d' % i, 'fecha': f, 'area_ha': 30.0,
                          'RVI': tray[j] + off + rng.normal(0, 0.01),
                          'n_px': 500, 'calidad': 'pleno', 'orbita': '10-DESCENDING'})
    return pd.DataFrame(filas)


# --- que el radar sepa decir "no vi nada" ------------------------------------

def test_sin_evento_no_marca_cambio():
    """Si marcara siempre seria una cuota, igual que el criterio optico."""
    est = rad.cambio_estructural(serie_radar(), '2025-12-25')
    v = [e for e, _ in est.values()]
    assert v.count('CAMBIO') == 0, 'marco cambio sobre una campaña sin eventos'
    assert v.count('SIN CAMBIO') == len(v)


def test_detecta_una_caida_abrupta():
    """Vuelco, cosecha o anegamiento: el radar SI ve eso."""
    df = serie_radar(semilla=1)
    ult = df.fecha.max()
    df.loc[(df.lote_id == 'L007') & (df.fecha == ult), 'RVI'] -= 0.25
    est = rad.cambio_estructural(df, str(ult.date()))
    assert est['L007'][0] == 'CAMBIO'


def test_detecta_tambien_una_subida_abrupta():
    """El anegamiento SUBE la retrodispersion. Mirar solo caidas lo perderia."""
    df = serie_radar(semilla=2)
    ult = df.fecha.max()
    df.loc[(df.lote_id == 'L011') & (df.fecha == ult), 'RVI'] += 0.25
    est = rad.cambio_estructural(df, str(ult.date()))
    assert est['L011'][0] == 'CAMBIO'


def test_un_desnivel_constante_no_es_un_cambio():
    """Un lote siempre mas rugoso que el resto no cambio: es como es."""
    df = serie_radar(semilla=3)
    df.loc[df.lote_id == 'L004', 'RVI'] += 0.10      # constante toda la campaña
    est = rad.cambio_estructural(df, str(df.fecha.max().date()))
    assert est['L004'][0] == 'SIN CAMBIO'


def test_dato_viejo_se_declara_no_se_arrastra():
    """Con revisita de 12 dias un lote puede quedar sin pasada util. Arrastrar el
    ultimo estado seria afirmar algo que no se miro."""
    df = serie_radar(semilla=4)
    est = rad.cambio_estructural(df, '2026-04-01')   # muy posterior a la serie
    assert all(e == 'SIN DATO RADAR' for e, _ in est.values())


def test_sin_serie_no_inventa_nada():
    assert rad.cambio_estructural(pd.DataFrame(), '2026-01-01') == {}
    assert rad.cambio_estructural(None, '2026-01-01') == {}


def test_el_resumen_cuenta_las_tres_categorias():
    df = serie_radar(semilla=5)
    ult = df.fecha.max()
    df.loc[(df.lote_id == 'L002') & (df.fecha == ult), 'RVI'] -= 0.3
    r = rad.resumen(rad.cambio_estructural(df, str(ult.date())))
    assert r['total'] == 20
    assert r['cambio'] == 1
    assert r['cambio'] + r['sin_cambio'] + r['sin_dato'] == r['total']


def test_resumen_vacio_si_no_hubo_radar():
    assert rad.resumen({}) is None


# --- parametros declarados ---------------------------------------------------

def test_el_umbral_del_radar_es_mas_exigente_que_el_optico():
    """El radar solo puede hablar de eventos gruesos. Con el umbral optico marcaria
    ruido de speckle y de humedad de suelo como si fuera cultivo."""
    from pix_alerta import ranking as rk
    assert rad.Z_CAMBIO > rk.L_CONTROL - 0.5


def test_una_orbita_sola_no_hace_serie():
    """Mezclar orbitas cambia el angulo de vista: el lote cambia de retrodispersion
    por la geometria, no por el cultivo. Medido sobre HDS: 9 pasadas en 4 meses de
    UNA sola orbita relativa."""
    assert rad.MIN_ESCENAS_ORBITA >= 5


def test_el_radar_no_es_un_eje_del_criterio_optico():
    """Meterlo en el mismo EWMA mezclaria estructura con pigmentos. El radar NO
    detecta enfermedad; sirve para continuidad y eventos gruesos."""
    from pix_alerta import config as cfg
    assert 'RVI' not in cfg.EJES
    assert 'VV_lin' not in cfg.EJES and 'VH_lin' not in cfg.EJES
