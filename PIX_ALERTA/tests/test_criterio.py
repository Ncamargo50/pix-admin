"""Las puertas de aceptacion, como tests. Corren sin GEE, con datos sinteticos.

    python -m pytest tests/ -v

Cada test es una puerta de PLAN_A_PRODUCCION.md §2. Si uno falla, el criterio no
sale a campo.
"""
import numpy as np
import pandas as pd
import pytest

from pix_alerta import config as cfg
from pix_alerta import ranking as rk

# Las puertas NO dependen de que ejes esten configurados: se fabrican los que
# declara `cfg.EJES` y el deterioro se aplica en la direccion que dice `rk.SIGNO`.
# Cablear PSRI acá hizo que cambiar de segundo eje rompiera 14 pruebas que no
# tenian nada que ver con el cambio.
EJE2 = cfg.EJES[1]
S2 = rk.SIGNO.get(EJE2, 1)

# eje -> (valor al inicio de campaña, al final, ruido, magnitud de deterioro).
# El "final" va SIEMPRE hacia la senescencia, o sea en el sentido de alarma.
ESCALAS = {
    'PSRI': (0.02, 0.08, 0.003, 0.020),
    'NDRE': (0.45, 0.25, 0.012, 0.080),
    'CIRE': (3.00, 1.50, 0.100, 0.600),
}
LO2, HI2, RUIDO2, DET2 = ESCALAS.get(EJE2, (0.02, 0.08, 0.003, 0.020))
DET_NDMI = 0.060


def campo_sintetico(n_lotes=60, n_fechas=14, semilla=0, offsets=True):
    """Campaña sana: trayectoria fenologica comun + desnivel propio de cada lote.

    El desnivel es lo que distingue variedades, edades y suelos. Un criterio
    correcto NO debe marcarlo: no es un cambio, es como es ese lote.
    """
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range('2025-11-01', periods=n_fechas, freq='7D')
    # el dosel se seca y senesce a lo largo de la campaña, igual para todos
    tray_ndmi = np.linspace(0.35, 0.20, n_fechas)
    tray_2 = np.linspace(LO2, HI2, n_fechas)
    filas = []
    for i in range(n_lotes):
        off_n = rng.normal(0, 0.05) if offsets else 0.0
        off_2 = rng.normal(0, RUIDO2 * 3.3) if offsets else 0.0
        for j, f in enumerate(fechas):
            filas.append({
                'lote_id': f'L{i:03d}', 'fecha': f, 'area_ha': 50.0,
                'calidad': 'pleno',
                'NDMI': tray_ndmi[j] + off_n + rng.normal(0, 0.01),
                EJE2: tray_2[j] + off_2 + rng.normal(0, RUIDO2),
            })
    return pd.DataFrame(filas)


def deteriorar(df, m, k=1.0):
    """Empuja los dos ejes en la direccion de alarma que declara `rk.SIGNO`."""
    df.loc[m, 'NDMI'] += rk.SIGNO['NDMI'] * DET_NDMI * k
    df.loc[m, EJE2] += S2 * DET2 * k
    return df


def evaluar(df):
    car = rk.ewma(rk.residuos(df))
    return rk.ranking(car)


# --- Puerta 2.1 -------------------------------------------------------------
def test_control_nulo_cerca_de_alfa():
    """Sobre una campaña sana el criterio debe marcar poco, no un 30% fijo."""
    r = evaluar(campo_sintetico())
    tasa = (r['estado'] != 'SIN SEÑAL').mean()
    assert tasa < 0.10, f'tasa de alarma {tasa:.1%} sobre campo sano'


def test_desnivel_propio_no_se_marca():
    """El defecto que hace que la nula temporal degenere en espacial.

    Un lote consistentemente mas seco que el resto (otra variedad, otro suelo) no
    puede quedar marcado: no cambio, siempre fue asi.
    """
    df = campo_sintetico(offsets=False)
    df.loc[df.lote_id == 'L007', 'NDMI'] -= 0.08     # desnivel grande y CONSTANTE
    r = evaluar(df)
    est = r.loc[r.lote_id == 'L007', 'estado'].iloc[0]
    assert est == 'SIN SEÑAL', f'un desnivel constante quedo marcado como {est}'


# --- Puerta 2.2 -------------------------------------------------------------
def test_no_es_una_cuota():
    """La fraccion marcada tiene que depender de lo que pasa, no ser constante."""
    sano = (evaluar(campo_sintetico(semilla=1))['estado'] != 'SIN SEÑAL').mean()
    df = campo_sintetico(semilla=1)
    afectados = [f'L{i:03d}' for i in range(10)]
    m = df.lote_id.isin(afectados) & (df.fecha >= '2025-12-15')
    deteriorar(df, m)
    enfermo = (evaluar(df)['estado'] != 'SIN SEÑAL').mean()
    assert enfermo > sano + 0.05, (
        f'campo sano {sano:.1%} vs afectado {enfermo:.1%}: la fraccion no responde')


# --- Puerta 2.3 -------------------------------------------------------------
def test_puede_decir_que_no_pasa_nada():
    """Sin esto el producto es un cuantil: siempre habria a donde mandar gente."""
    r = evaluar(campo_sintetico(semilla=3))
    assert (r['estado'] == 'SIN SEÑAL').sum() > 0.85 * len(r)


# --- Sensibilidad: si no detecta nada, tampoco sirve -------------------------
def test_detecta_un_deterioro_real():
    df = campo_sintetico(semilla=2)
    m = (df.lote_id == 'L042') & (df.fecha >= '2025-12-01')
    deteriorar(df, m, k=1.17)      # se seca y pierde pigmento, sostenido
    r = evaluar(df)
    fila = r.loc[r.lote_id == 'L042'].iloc[0]
    assert fila['estado'] == 'ATENCION', f"L042 quedo en {fila['estado']}"
    assert fila['orden'] <= 5, f"L042 salio en el puesto {fila['orden']}"


def test_signo_fisiologico():
    """Un dosel MAS humedo que lo esperado no es una alerta de plaga."""
    df = campo_sintetico(semilla=4)
    m = (df.lote_id == 'L011') & (df.fecha >= '2025-12-01')
    df.loc[m, 'NDMI'] -= rk.SIGNO['NDMI'] * 0.07   # sentido CONTRARIO al deterioro
    r = evaluar(df)
    assert r.loc[r.lote_id == 'L011', 'estado'].iloc[0] == 'SIN SEÑAL'


# --- Puerta 2.4 -------------------------------------------------------------
def test_estabilidad_de_parametros():
    """Mover lambda +-50% debe conservar la mayoria del top-K."""
    df = campo_sintetico(semilla=5)
    m = df.lote_id.isin([f'L{i:03d}' for i in range(8)]) & (df.fecha >= '2025-12-01')
    deteriorar(df, m)
    res = rk.residuos(df)
    base = set(rk.ranking(rk.ewma(res, lam=rk.LAMBDA_EWMA)).head(10).lote_id)
    for lam in (rk.LAMBDA_EWMA * 0.5, rk.LAMBDA_EWMA * 1.5):
        otro = set(rk.ranking(rk.ewma(res, lam=lam)).head(10).lote_id)
        comun = len(base & otro) / len(base)
        assert comun >= 0.7, f'lambda={lam:.2f} conserva solo {comun:.0%} del top-10'


# --- Puerta 2.5 -------------------------------------------------------------
def test_reproducible():
    df = campo_sintetico(semilla=6)
    a = evaluar(df)
    b = evaluar(df)
    pd.testing.assert_frame_equal(a, b)


# --- Serie insuficiente: no se inventa un resultado --------------------------
def test_la_alerta_se_resuelve():
    """Un lote que se deteriora y se recupera no puede quedar marcado para siempre.

    Sin reinicio de la carta, la lista solo crece: medido sobre la campaña de HDS,
    14,1% en diciembre -> 22,6% en abril, monotono.
    """
    df = campo_sintetico(n_fechas=20, semilla=7)
    m = (df.lote_id == 'L003') & (df.fecha >= '2025-11-22') & (df.fecha < '2025-12-20')
    deteriorar(df, m, k=1.17)
    car = rk.ewma(rk.residuos(df))
    durante = rk.ranking(car, fecha='2025-12-13')
    despues = rk.ranking(car, fecha='2026-03-14')
    assert durante.loc[durante.lote_id == 'L003', 'estado'].iloc[0] != 'SIN SEÑAL'
    assert despues.loc[despues.lote_id == 'L003', 'estado'].iloc[0] == 'SIN SEÑAL'


def test_K_no_es_una_cuota_a_llenar():
    """K es el techo de capacidad de scouting, no una lista que haya que completar.

    Sin esto, el criterio sabe decir "no pasa nada" pero el entregable manda al
    técnico a K lotes igual, reintroduciendo la cuota en el último paso.
    """
    car = rk.ewma(rk.residuos(campo_sintetico(semilla=9)))
    r = rk.ranking(car, K=10)
    assert len(r) < 10, f'campo sano y aun asi se entregaron {len(r)} lotes'
    assert not (r['estado'] == 'SIN SEÑAL').any()


def test_dato_viejo_no_es_alerta():
    """Con 48% de dekadas sin escena util, arrastrar un estado viejo es afirmar
    algo que no se miro."""
    df = campo_sintetico(semilla=8)
    car = rk.ewma(rk.residuos(df))
    tarde = pd.Timestamp(df.fecha.max()) + pd.Timedelta(days=rk.CADUCIDAD_DIAS + 10)
    r = rk.ranking(car, fecha=tarde)
    assert (r['estado'] == 'SIN DATO').all()


def test_la_ventana_arranca_con_la_campana():
    """Lo encontro la primera corrida real contra Earth Engine, no un test sintetico.

    Con la ventana por defecto de 150 dias, una corrida al 30-abr arranca el 1-dic: a
    mitad de campaña, con los lotes ya emergidos. El estimador de cohorte necesita la
    RAMA ASCENDENTE del NDVI para ubicar la emergencia, asi que mando 188 de 207 lotes a
    EST-SIN-CICLO y el ranking salio con CERO lotes. Arrancando con la campaña: 90 sin
    ciclo y 9 alertados.
    """
    class S:
        campanas = {'2025/2026': ('2025-10-01', '2026-04-30'),
                    '2024/2025': ('2024-10-01', '2025-04-30')}
    assert rk.inicio_de_campana('2026-04-30', S()) == '2025-10-01'
    assert rk.inicio_de_campana('2025-11-15', S()) == '2025-10-01'
    assert rk.inicio_de_campana('2025-03-01', S()) == '2024-10-01'
    # fuera de toda campaña no se inventa un inicio: quien llame decide que hacer
    assert rk.inicio_de_campana('2026-07-15', S()) is None

    class SinCampanas:
        campanas = {}
    assert rk.inicio_de_campana('2026-04-30', SinCampanas()) is None


def test_serie_corta_no_produce_ranking():
    df = campo_sintetico(n_fechas=2)
    assert rk.ewma(rk.residuos(df)).empty


def test_cohorte_chica_se_descarta():
    """Con pocos lotes la mediana de la cohorte no significa nada."""
    df = campo_sintetico(n_lotes=rk.MIN_LOTES_COHORTE - 2)
    assert rk.residuos(df).empty


# --- Puerta 0.1: la cohorte estimada nunca se presenta como declarada ---------
def test_cohorte_estimada_no_se_rotula_declarada():
    """El entregable debe decir de donde salio la cohorte.

    `cohorte.py` rotula SIEMPRE `EST-<fecha>` porque no hay ni una fecha de siembra
    declarada en la cartera. La version anterior comparaba contra 'unica' y le ponia
    'declarada' a todo lo demas: el CSV entregado afirmaba tener fechas de siembra
    que no existen. Sin este test el error es invisible, porque el ranking sale igual.
    """
    df = campo_sintetico(semilla=11)
    df['cohorte'] = 'EST-2025-10-22'          # lo que produce el estimador real
    r = evaluar(df)
    assert (r['cohorte_origen'] == 'ESTIMADA-FENOLOGIA').all(), \
        'una cohorte EST-* se esta rotulando como declarada'

    sin_ciclo = campo_sintetico(semilla=12)
    sin_ciclo['cohorte'] = 'EST-SIN-CICLO'
    assert (evaluar(sin_ciclo)['cohorte_origen'] == 'ESTIMADA-SIN-CICLO').all()

    # y el dia que exista la planilla de siembra, esa si es declarada
    declarada = campo_sintetico(semilla=13)
    declarada['cohorte'] = '2025-10-22'       # sin prefijo EST- = fecha del cliente
    assert (evaluar(declarada)['cohorte_origen'] == 'declarada').all()


# --- Puerta 2.1, version corregida ------------------------------------------
def test_la_nula_evalua_los_mismos_lotes_que_el_dato_real():
    """El defecto que invalidaba la puerta: la nula perdia el 70% de las
    observaciones y se medía sobre 3 lotes mientras el real se medía sobre 96."""
    df = campo_sintetico(semilla=11)
    n_real = len(rk.ranking(rk.ewma(rk.residuos(df))))
    assert n_real > 0
    # La nula sintetica conserva fechas, calidad y soporte, asi que tiene que poder
    # producir una tasa sobre la misma poblacion en vez de quedarse sin lotes.
    tasa = rk.control_nulo(df, n_rep=3)
    assert np.isfinite(tasa), 'la nula se quedo sin lotes que evaluar'


def test_la_nula_marca_poco_sobre_un_mundo_sin_senal():
    """Si la puerta no puede reprobar no es una puerta; si marca mucho, tampoco
    sirve. Con una carta a L=3 sigma la falsa alarma tiene que ser chica."""
    tasa = rk.control_nulo(campo_sintetico(semilla=12), n_rep=5)
    assert tasa < 0.05, f'falsa alarma {tasa:.1%} sobre una nula construida sin señal'


def test_la_nula_no_conserva_el_episodio():
    """Una rotacion circular movia el episodio de fecha pero lo conservaba, asi que
    el EWMA lo seguia viendo. La nula sintetica no puede contener episodios."""
    df = campo_sintetico(semilla=13)
    m = df.lote_id.isin([f'L{i:03d}' for i in range(15)]) & (df.fecha >= '2025-12-01')
    deteriorar(df, m, k=1.5)
    real = (rk.ranking(rk.ewma(rk.residuos(df)))['estado'] != 'SIN SEÑAL').mean()
    nula = rk.control_nulo(df, n_rep=5)
    assert real > nula, f'real {real:.1%} no supera a la nula {nula:.1%}'


def test_el_ruido_de_la_nula_cae_en_las_filas_DEL_LOTE_que_lo_genero(monkeypatch):
    """Bug real encontrado en auditoria, y la prueba que lo caza.

    El ruido AR(1) se construia recorriendo los lotes, pero se asignaba con el
    indice global ordenado por FECHA: la observacion i-esima de un lote caia en la
    i-esima fila cronologica de TODA la tabla. Eso destruye la autocorrelacion
    intra-lote —justo lo que esta nula debe preservar— y la puerta devolvia
    0,0000% pasara lo que pasara. Medido sobre HDS: 0,0000% con el bug, 0,30%
    corregido.

    No se testea la TASA (con datos sinteticos limpios da ~0 legitimamente y la
    prueba seria ciega): se testea el MECANISMO. Se inyecta ruido en un solo lote y
    se verifica que solo ESE lote se aparta.
    """
    df = campo_sintetico(n_lotes=8, n_fechas=10, semilla=31)
    lotes = sorted(df.lote_id.unique())
    marcado = lotes[3]                      # el unico que va a recibir ruido

    llamadas = {'n': 0}

    def _ar1_falso(n, sigma, rho, rng):
        # Dos llamadas por lote (un eje cada una), en orden de lote_id.
        idx_lote = llamadas['n'] // 2
        llamadas['n'] += 1
        # Grande a proposito: control_nulo lo multiplica por la escala
        # estimada del residuo (~0,01), asi que 1e6 llega como ~1e4.
        return np.full(n, 1e6 if lotes[idx_lote] == marcado else 0.0)

    capturado = {}

    def _residuos_falso(d, ejes=None, **kw):
        capturado['df'] = d.copy()
        # Vacio PERO con las columnas que espera `ewma`: corta la corrida sin
        # simular una condicion que no ocurre en la realidad.
        return pd.DataFrame(columns=['lote_id', 'fecha', 'eje', 'z'])

    monkeypatch.setattr(rk, '_ar1', _ar1_falso)
    monkeypatch.setattr(rk, 'residuos', _residuos_falso)
    rk.control_nulo(df, n_rep=1)

    d = capturado['df']
    eje = cfg.EJES[0]
    med = d.groupby('fecha')[eje].transform('median')
    aparta = d.loc[(d[eje] - med).abs() > 100, 'lote_id'].unique()
    assert set(aparta) == {marcado}, (
        'el ruido de %s aparecio en %s: se esta asignando por orden de fecha y no '
        'por lote' % (marcado, sorted(aparta)))
