# -*- coding: utf-8 -*-
"""Regresiones de la auditoria del 2026-07-26.

Cada prueba de acá corresponde a un defecto que EXISTIO, se midio y se corrigio.
Todos tenian el mismo signo: **hacia el resultado tranquilizador**. Por eso el
archivo existe como bloque aparte — si uno vuelve, vuelve la mentira.

La suite estaba en 143 en verde cuando se encontraron los 11 bloqueantes: pasar
los tests no es evidencia de que el producto diga la verdad.
"""
import importlib
import json
import os

import numpy as np
import pandas as pd
import pytest

from pix_alerta import config as cfg
from pix_alerta import ranking as rk


# --- el criterio no puede alertar sobre una referencia que no discrimina -------

def _campo(n_lotes=30, n_fechas=12, semilla=0, cohorte='EST-2025-10-22'):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range('2025-11-01', periods=n_fechas, freq='7D')
    t1 = np.linspace(0.35, 0.20, n_fechas)
    t2 = np.linspace(0.45, 0.25, n_fechas)
    filas = []
    for i in range(n_lotes):
        o1, o2 = rng.normal(0, 0.05), rng.normal(0, 0.04)
        for j, f in enumerate(fechas):
            filas.append({'lote_id': 'L%03d' % i, 'fecha': f, 'area_ha': 50.0,
                          'calidad': 'pleno', 'cohorte': cohorte,
                          cfg.EJES[0]: t1[j] + o1 + rng.normal(0, 0.01),
                          cfg.EJES[1]: t2[j] + o2 + rng.normal(0, 0.012)})
    return pd.DataFrame(filas)


def _deteriorar(df, lote, desde):
    m = (df.lote_id == lote) & (df.fecha >= desde)
    for e in cfg.EJES:
        df.loc[m, e] += rk.SIGNO[e] * (0.07 if e == cfg.EJES[0] else 0.09)
    return df


def test_una_cohorte_sin_ciclo_no_puede_producir_ATENCION():
    """`EST-SIN-CICLO` agrupa lotes cuya emergencia no se pudo ubicar — en HDS son
    90 de 207. Su "trayectoria mediana" mezcla fechas de siembra desconocidas: es
    la configuracion que `cohorte.py` declara MEDIDA COMO CIEGA. Sin esta guarda,
    el lote #1 del producto salia de ahi."""
    df = _deteriorar(_campo(cohorte='EST-SIN-CICLO', semilla=3), 'L004', '2025-12-01')
    r = rk.ranking(rk.ewma(rk.residuos(df)))
    assert (r['estado'] == 'ATENCION').sum() == 0, 'una cohorte sin ciclo alerto'
    assert r.loc[r.lote_id == 'L004', 'estado'].iloc[0] == 'VIGILANCIA'
    assert bool(r.loc[r.lote_id == 'L004', 'referencia_debil'].iloc[0])


def test_una_cohorte_real_si_puede_producir_ATENCION():
    """Control: la degradacion no puede apagar el producto entero."""
    df = _deteriorar(_campo(semilla=4), 'L007', '2025-12-01')
    r = rk.ranking(rk.ewma(rk.residuos(df)))
    assert r.loc[r.lote_id == 'L007', 'estado'].iloc[0] == 'ATENCION'


def test_el_orden_respeta_el_estado_final_no_el_conteo_de_ejes():
    """Un lote degradado a VIGILANCIA seguia figurando PRIMERO, por encima de
    ATENCIONes reales: el informe decia "van ordenados por prioridad" y el primero
    de la lista era el de menor prioridad."""
    df = _deteriorar(_campo(semilla=5), 'L009', '2025-12-01')
    r = rk.ranking(rk.ewma(rk.residuos(df)))
    prio = {'ATENCION': 0, 'VIGILANCIA': 1, 'SIN SEÑAL': 2, 'SIN DATO': 3}
    vals = [prio[e] for e in r['estado']]
    assert vals == sorted(vals), 'el orden no respeta el estado: %s' % r['estado'].tolist()


def test_ATENCION_exige_TODOS_los_ejes_no_dos_cualesquiera():
    """Estaba cableado a `>= 2`: con 3 ejes la conjuncion pasaba a "2 de 3" (mucho
    mas laxa) y con 1 eje ATENCION era inalcanzable, las dos veces en silencio."""
    import inspect
    src = inspect.getsource(rk.ranking)
    assert 'len(cfg.EJES)' in src, 'el umbral de ATENCION sigue cableado'


def test_todo_eje_configurado_declara_su_sentido_de_alarma():
    """El error que el propio archivo llama "el mas caro posible": un eje sin signo
    quedaba en +1 por default y el motor alertaba sobre los lotes SANOS."""
    assert set(cfg.EJES) <= set(rk.SIGNO)
    ejes_reales = ('NDVI', 'NDMI', 'PSRI', 'NDRE', 'CIRE')
    assert set(ejes_reales) <= set(rk.SIGNO), 'series.py calcula ejes sin signo'


def test_un_eje_sin_signo_revienta_al_importar(monkeypatch):
    monkeypatch.setattr(cfg, 'EJES', ('NDMI', 'NO_DECLARADO'))
    with pytest.raises(RuntimeError, match='SIGNO'):
        importlib.reload(rk)
    monkeypatch.undo()
    importlib.reload(rk)


def test_la_sombra_oscura_esta_enmascarada():
    """SCL 2 (DARK_AREA_PIXELS) recibe la sombra de nube que Sen2Cor no clasifico
    como 3. Un dosel en sombra da los DOS ejes en sentido de alarma: es un ATENCION
    fabricado por la iluminacion."""
    assert 2 in cfg.SCL_MALAS and 3 in cfg.SCL_MALAS


# --- el radar no puede afirmar "sin cambio" sobre lo que no midio -------------

def _serie_radar(n_lotes=20, n_fechas=10, semilla=0):
    rng = np.random.default_rng(semilla)
    fechas = pd.date_range('2025-11-01', periods=n_fechas, freq='12D')
    tray = np.linspace(0.35, 0.65, n_fechas)
    return pd.DataFrame([
        {'lote_id': 'L%03d' % i, 'fecha': f, 'area_ha': 30.0,
         'RVI': tray[j] + rng.normal(0, 0.02), 'n_px': 500,
         'calidad': 'pleno', 'orbita': '10-DESCENDING'}
        for i in range(n_lotes) for j, f in enumerate(fechas)])


@pytest.mark.parametrize('caso', ['un_lote', 'una_observacion', 'pocos_pixeles'])
def test_el_radar_declara_sin_dato_en_vez_de_tranquilizar(caso):
    """Cuatro vias medidas daban SIN CAMBIO sobre un vuelco de RVI -0,40."""
    from pix_alerta import radar as rad
    if caso == 'un_lote':
        d = _serie_radar(n_lotes=1)
        lote = 'L000'
    elif caso == 'una_observacion':
        d = _serie_radar(semilla=9)
        d = d[(d.lote_id != 'L003') | (d.fecha == d.fecha.min())]
        lote = 'L003'
    else:
        d = _serie_radar(semilla=7)
        lote = 'L005'
        d.loc[(d.lote_id == lote) & (d.fecha == d.fecha.max()), 'n_px'] = 2
    ult = d.fecha.max()
    d.loc[(d.lote_id == lote) & (d.fecha == ult), 'RVI'] -= 0.40
    est = rad.cambio_estructural(d, str(ult.date()))
    assert est.get(lote, ('AUSENTE', 0))[0] == 'SIN DATO RADAR', (
        '%s: el radar afirmo algo sobre un lote que no pudo medir' % caso)


def test_el_radar_si_detecta_un_evento_real():
    """Control: los minimos no pueden apagar la deteccion."""
    from pix_alerta import radar as rad
    d = _serie_radar(semilla=5)
    ult = d.fecha.max()
    d.loc[(d.lote_id == 'L011') & (d.fecha == ult), 'RVI'] -= 0.40
    assert rad.cambio_estructural(d, str(ult.date()))['L011'][0] == 'CAMBIO'


# --- la validacion no puede devolver un numero halagador ----------------------

def _val(casos):
    filas = []
    for e, N, n, exitos in casos:
        filas += [{'lote_id': '%s%d' % (e[:2], i), 'estrato': e, 'N_estrato': N,
                   'hubo_problema': i < exitos} for i in range(n)]
    return pd.DataFrame(filas)


def test_la_precision_nunca_sale_con_intervalo_de_ancho_cero():
    """Con los N REALES de HDS los estratos alertados se censan, la fpc vale 0 y la
    varianza de diseño da 0: el informe imprimia `50,0% IC95 [50,0-50,0]` sobre
    SEIS observaciones. La precision generaliza, no es un total finito: Wilson."""
    from pix_alerta import validacion as vl
    r = vl.evaluar(_val([('ATENCION', 4, 4, 2), ('VIGILANCIA', 2, 2, 1),
                         ('SIN SEÑAL', 115, 48, 3)]))
    lo, hi = r['precision_ic95']
    assert hi - lo > 0.20, 'IC de ancho %.3f sobre n=%d' % (hi - lo, r['precision_n'])
    assert 0.0 <= lo < r['precision_en_alerta'] < hi <= 1.0


def test_no_es_concluyente_sin_visitar_un_solo_lote_alertado():
    """`_resumen_estratos` omite los estratos con n=0, asi que el minimo nunca los
    veia: con 30 visitas solo en verde salia `concluyente: si` y precision `nan`."""
    from pix_alerta import validacion as vl
    r = vl.evaluar(_val([('SIN SEÑAL', 115, 30, 2)]))
    assert r['concluyente'] is False
    assert r['n_alertados_vistos'] == 0
    assert any('NINGUN LOTE ALERTADO' in a for a in r['avisos'])


def test_la_acumulacion_no_borra_hallazgos_de_una_tanda_previa(tmp_path):
    """El tecnico que vuelve en dos tandas: la segunda BORRABA la primera."""
    from pix_alerta import campana as cp
    m = pd.DataFrame({'lote_id': ['L0', 'L1', 'L2'], 'estrato': ['ATENCION'] * 3,
                      'N_estrato': [3] * 3, 'n_estrato': [3] * 3,
                      'prob_inclusion': [1.0] * 3, 'peso_diseño': [1.0] * 3,
                      'fecha_dato': ['2026-01-10'] * 3})
    cp.agregar(str(tmp_path), 'X', m,
               validaciones=pd.DataFrame({'lote_id': ['L0'], 'hubo_problema': [True]}))
    cp.agregar(str(tmp_path), 'X', m,
               validaciones=pd.DataFrame({'lote_id': ['L1'], 'hubo_problema': [False]}))
    d = cp.cargar(str(tmp_path), 'X').set_index('lote_id')['hubo_problema']
    assert cp._a_booleano(d)['L0'] is np.True_ or cp._a_booleano(d)['L0'] == True
    assert cp._a_booleano(d)['L1'] == False


def test_un_csv_con_unos_y_ceros_no_convierte_los_positivos_en_negativos():
    """Una columna booleana CON algun NA sale del CSV como 1.0/0.0, y la lista
    blanca de strings la convertia entera en False. Medido: 2 positivos -> 0."""
    from pix_alerta import campana as cp
    b = cp._a_booleano(pd.Series([1.0, 0.0, 1.0, np.nan]))
    assert int(b.fillna(False).sum()) == 2
    assert pd.isna(b.iloc[3]), 'no visitado se convirtio en "sin problema"'


def test_no_visitado_nunca_es_sin_problema():
    from pix_alerta import campana as cp
    for v in (None, '', 'nan', np.nan, 'basura'):
        assert pd.isna(cp._a_booleano(pd.Series([v])).iloc[0]), repr(v)


# --- la entrega no puede publicar lo de otro ni callar lo que no pudo leer -----

def test_publicar_da_a_cada_propiedad_su_propia_fecha(tmp_path):
    """Con `max()` global, la hacienda que no emitio hoy DESAPARECIA de `ultimo/`:
    la APK pedia su GeoJSON y recibia 404."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'pu', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'scripts', 'publicar_ultimo.py'))
    pu = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pu)
    d = tmp_path / 'AGRO'
    d.mkdir()
    for nom in ('lotes_AGRO_NORTE_2026-05-02.geojson', 'ranking_AGRO_NORTE_2026-05-02.csv',
                'lotes_AGRO_SUR_2026-04-29.geojson', 'ranking_AGRO_SUR_2026-04-29.csv'):
        (d / nom).write_text('lote_id,estado\nA,ATENCION\n', encoding='utf-8')
    pu.publicar(str(tmp_path))
    pub = sorted(os.listdir(d / 'ultimo'))
    assert 'lotes_AGRO_NORTE.geojson' in pub
    assert 'lotes_AGRO_SUR.geojson' in pub, 'la propiedad que no emitio hoy desaparecio'


def test_el_chequeo_de_aislamiento_mira_tambien_la_carpeta_que_baja_el_telefono(tmp_path):
    """`os.listdir` plano no veia `ultimo/`: se podian plantar archivos de otro
    cliente ahi adentro y el verificador no reportaba nada."""
    from pix_alerta import correr_todos as ct

    class _S:
        clave = 'MIO'

    class _C:
        clave = 'CLI'
        sitios = [_S()]

        def salida(self, base):
            return os.path.join(base, 'CLI')

    d = tmp_path / 'CLI' / 'ultimo'
    d.mkdir(parents=True)
    (d / 'ranking_AJENO_2026-01-01.csv').write_text('x', encoding='utf-8')
    problemas = ct.verificar_aislamiento([_C()], str(tmp_path))
    assert problemas, 'un entregable ajeno dentro de ultimo/ paso desapercibido'


def test_los_nombres_publicados_son_reconocibles_por_el_aislamiento():
    """Dos de los cuatro nombres que se publican eran estructuralmente invisibles
    para `sitio_de_archivo`, incluido el GeoJSON que descarga la APK."""
    from pix_alerta.correr_todos import sitio_de_archivo as f
    for nom in ('lotes_AGRO_NORTE.geojson', 'Informe_AGRO_NORTE.pdf',
                'ranking_AGRO_NORTE.csv', 'focos_AGRO_NORTE.geojson',
                'dimensionamiento_AGRO_NORTE.txt'):
        assert f(nom) == 'AGRO_NORTE', '%s -> %r' % (nom, f(nom))
