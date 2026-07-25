"""Acumulacion de la campaña ronda por ronda.

Existe porque una sola ronda no alcanza: con los ~6 lotes alertados que tiene HDS a una
fecha, el IC de la precision es de ±44 puntos y la campaña entera produciria un numero
inservible. El valor se junta acumulando.
"""
import numpy as np
import pandas as pd

from pix_alerta import campana as cp


def ronda(fecha, n_at=4, n_vi=2, n_ss=20, N_at=6, N_vi=4, N_ss=180, tasas=None):
    """Una muestra sorteada de una ronda, con o sin los hallazgos del tecnico."""
    tasas = tasas or {}
    rng = np.random.default_rng(abs(hash(fecha)) % 2**31)
    filas = []
    for est, n, N in (('ATENCION', n_at, N_at), ('VIGILANCIA', n_vi, N_vi),
                      ('SIN SEÑAL', n_ss, N_ss)):
        for i in range(n):
            f = dict(lote_id='L%02d' % (i + {'ATENCION': 0, 'VIGILANCIA': 40,
                                             'SIN SEÑAL': 80}[est]),
                     estrato=est, N_estrato=N, n_estrato=n,
                     prob_inclusion=n / N, peso_diseño=N / n, fecha_dato=fecha)
            if est in tasas:
                f['hubo_problema'] = bool(rng.random() < tasas[est])
            filas.append(f)
    return pd.DataFrame(filas)


TASAS = {'ATENCION': 0.7, 'VIGILANCIA': 0.4, 'SIN SEÑAL': 0.05}


# --- lo que resuelve --------------------------------------------------------
def test_acumular_junta_alertados_entre_rondas(tmp_path):
    """EL PUNTO. Una ronda da 6 alertados; ocho rondas dan ~48, que es donde el
    numero empieza a significar algo."""
    base = str(tmp_path)
    for i in range(8):
        cp.agregar(base, 'HDS', ronda('2026-11-%02d' % (1 + i), tasas=TASAS))
    acum = cp.cargar(base, 'HDS')
    d, meta = cp.agrupar(acum)
    alert = d[d['estrato'].isin(('ATENCION', 'VIGILANCIA'))]
    assert meta['rondas'] == 8
    assert len(alert) == 8 * 6


def test_el_N_del_estrato_suma_entre_rondas(tmp_path):
    """Cada ronda es una muestra independiente: los tamaños se suman, no se pisan.
    Si se tomara el N de una sola ronda, el peso de diseño quedaria mal y la
    prevalencia estimada saldria sesgada."""
    base = str(tmp_path)
    cp.agregar(base, 'HDS', ronda('2026-11-01', N_at=6, tasas=TASAS))
    cp.agregar(base, 'HDS', ronda('2026-11-11', N_at=10, tasas=TASAS))
    d, _ = cp.agrupar(cp.cargar(base, 'HDS'))
    assert d[d.estrato == 'ATENCION']['N_estrato'].iloc[0] == 16


# --- operacion real ---------------------------------------------------------
def test_se_puede_sortear_ahora_y_completar_cuando_el_tecnico_vuelve(tmp_path):
    """Es el flujo real: la muestra se sortea el lunes y los hallazgos llegan el jueves."""
    base = str(tmp_path)
    m = ronda('2026-11-01')                       # sin hallazgos
    cp.agregar(base, 'HDS', m)
    d, meta = cp.agrupar(cp.cargar(base, 'HDS'))
    assert d.empty and meta['pendientes'] == 26

    vals = pd.DataFrame({'lote_id': m['lote_id'], 'hubo_problema': True})
    cp.agregar(base, 'HDS', m, ronda='2026-11-01', validaciones=vals)
    d, meta = cp.agrupar(cp.cargar(base, 'HDS'))
    assert meta['pendientes'] == 0 and meta['visitados'] == 26


def test_reagregar_una_ronda_no_la_duplica(tmp_path):
    """Completar los hallazgos de una ronda ya cargada es la operacion normal."""
    base = str(tmp_path)
    m = ronda('2026-11-01', tasas=TASAS)
    cp.agregar(base, 'HDS', m, ronda='R1')
    _, n = cp.agregar(base, 'HDS', m, ronda='R1')
    assert n == len(m)


def test_el_informe_dice_cuanto_vale_el_numero(tmp_path):
    """Sin esto se leen 12 visitas como si fueran 60."""
    base = str(tmp_path)
    cp.agregar(base, 'HDS', ronda('2026-11-01', tasas=TASAS))
    txt = cp.informe(base, 'HDS')
    assert 'NO alcanza para concluir' in txt or '±' in txt
    for _ in range(9):
        cp.agregar(base, 'HDS', ronda('2026-12-%02d' % (1 + _), tasas=TASAS))
    txt = cp.informe(base, 'HDS')
    assert 'utilizable' in txt or '±13' in txt


def test_advierte_que_la_unidad_es_lote_ronda(tmp_path):
    """Un lote alertado en dos rondas cuenta dos veces. Es correcto, pero invita a
    leer los totales como si fueran lotes distintos."""
    base = str(tmp_path)
    cp.agregar(base, 'HDS', ronda('2026-11-01', tasas=TASAS))
    cp.agregar(base, 'HDS', ronda('2026-11-11', tasas=TASAS))
    txt = cp.informe(base, 'HDS')
    assert 'lote, ronda' in txt and 'Lotes distintos' in txt


def test_sin_rondas_no_inventa_un_resultado(tmp_path):
    assert 'Sin rondas' in cp.informe(str(tmp_path), 'HDS')
