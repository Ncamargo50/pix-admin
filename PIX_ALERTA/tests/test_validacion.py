"""Puertas 4.1, 4.2 y 4.4 — el diseño de la campaña de validacion.

La que manda es que el SESGO DE VERIFICACION no pase desapercibido: si el tecnico solo
va a los rojos, el sistema parece excelente y el numero final no significa nada. Esa
trampa tiene que hacer ruido sola, sin que nadie se acuerde de mirarla.
"""
import numpy as np
import pandas as pd
import pytest

from pix_alerta import muestreo as ms
from pix_alerta import validacion as vl


def poblacion(n_at=20, n_vi=40, n_sin=440, semilla=0):
    """Campo tipico: pocos alertados, muchisimos sin señal."""
    rng = np.random.default_rng(semilla)
    filas = []
    for e, k in (('ATENCION', n_at), ('VIGILANCIA', n_vi), ('SIN SEÑAL', n_sin)):
        for i in range(k):
            filas.append(dict(lote_id='%s-%03d' % (e[:2], i), estado=e,
                              score=float(rng.normal({'ATENCION': 3, 'VIGILANCIA': 1.5}.get(e, 0), 1)),
                              area_ha=50.0))
    return pd.DataFrame(filas)


def campo(muestra, tasas, semilla=0):
    """Simula lo que el tecnico encontro, con la tasa real de cada estrato."""
    rng = np.random.default_rng(semilla)
    d = muestra.copy()
    d['hubo_problema'] = [rng.random() < tasas[e] for e in d['estrato']]
    return d


# --- Puerta 4.1: estratos CON VERDE y probabilidades guardadas ----------------
def test_el_sorteo_incluye_verde():
    m = ms.sortear(poblacion(), n_por_estrato={'ATENCION': 10, 'VIGILANCIA': 10, 'SIN SEÑAL': 10})
    assert set(m['estrato']) == set(ms.ESTRATOS)


def test_guarda_probabilidad_de_inclusion():
    """Sin esto el sobremuestreo del rojo sesga toda estimacion poblacional."""
    m = ms.sortear(poblacion(n_at=20, n_sin=440),
                   n_por_estrato={'ATENCION': 10, 'VIGILANCIA': 10, 'SIN SEÑAL': 10})
    at = m[m['estrato'] == 'ATENCION'].iloc[0]
    si = m[m['estrato'] == 'SIN SEÑAL'].iloc[0]
    assert at['prob_inclusion'] == pytest.approx(10 / 20)
    assert si['prob_inclusion'] == pytest.approx(10 / 440)
    # el rojo esta MUY sobremuestreado, y por eso hace falta el peso
    assert si['peso_diseño'] > at['peso_diseño'] * 10


def test_sin_dato_no_es_un_estrato():
    """'SIN DATO' es ausencia de observacion, no un veredicto. Mezclarlos seria
    confundir 'no mire' con 'mire y no habia nada'."""
    p = poblacion()
    p.loc[p.index[:5], 'estado'] = 'SIN DATO'
    m = ms.sortear(p, n_por_estrato={e: 5 for e in ms.ESTRATOS})
    assert 'SIN DATO' not in set(m['estrato'])


def test_el_orden_de_visita_no_revela_el_estrato():
    """Si el tecnico recorre primero todos los rojos, el orden le canta el estrato."""
    m = ms.sortear(poblacion(), n_por_estrato={e: 15 for e in ms.ESTRATOS}, semilla=3)
    primeros = list(m.sort_values('orden_visita')['estrato'].head(15))
    assert len(set(primeros)) > 1, 'los primeros 15 son todos del mismo estrato'


def test_ninguna_propiedad_del_geojson_ciego_separa_los_estratos(tmp_path):
    """El ciego se prueba por SEPARABILIDAD, no por nombres de campo.

    La version anterior de este test CERTIFICABA LA FUGA: exigia que
    `_estrato_oculto` viajara, con el argumento de que el nombre no se pinta. Pero
    el archivo se abre en QGIS, en un visor o en el Bloc de notas. Y peor: viajaban
    `prob_inclusion` y `peso_diseño`, que son funcion DETERMINISTA del estrato
    (n_h/N_h) — separaban perfectamente aunque se borrara el campo del estrato, y
    el MODO_CIEGO de la APK no conoce ninguna de las tres claves.

    Lo que hay que verificar es que, agrupando por el estrato REAL, ninguna
    propiedad del archivo tenga rangos disjuntos entre grupos.
    """
    import json
    m = ms.sortear(poblacion(), n_por_estrato={e: 3 for e in ms.ESTRATOS})
    geoms = {lid: {'type': 'Point', 'coordinates': [0, 0]} for lid in m['lote_id']}
    p = tmp_path / 'ciego.geojson'
    ms.a_geojson_ciego(m, geoms, str(p))
    gj = json.load(open(p, encoding='utf-8'))
    real = dict(zip(m['lote_id'].astype(str), m['estrato']))

    porestrato = {}
    for f in gj['features']:
        pr = f['properties']
        e = real[str(pr['lote_id'])]
        porestrato.setdefault(e, []).append(pr)

    # Ninguna propiedad NUMERICA puede tener rangos disjuntos entre estratos, y
    # ninguna propiedad de texto puede tomar valores distintos segun el estrato.
    claves = set().union(*[set(d[0]) for d in porestrato.values()])
    claves -= {'lote_id', 'id', 'name', 'lote', 'etiqueta', 'orden'}   # identidad
    for k in claves:
        vals = {e: [pr.get(k) for pr in lst] for e, lst in porestrato.items()}
        nums = {e: [v for v in vs if isinstance(v, (int, float))
                    and not isinstance(v, bool)] for e, vs in vals.items()}
        if all(nums.values()):
            rangos = {e: (min(v), max(v)) for e, v in nums.items()}
            ordenados = sorted(rangos.values())
            for a, b in zip(ordenados, ordenados[1:]):
                assert not (a[1] < b[0]), (
                    'la propiedad %r tiene rangos disjuntos entre estratos: %s. '
                    'Separa el ciego.' % (k, rangos))
        distintos = {tuple(sorted(map(str, set(vs)))) for vs in vals.values()}
        assert len(distintos) == 1, (
            'la propiedad %r toma valores distintos segun el estrato (%s): '
            'separa el ciego.' % (k, {e: sorted(set(map(str, vs)))
                                      for e, vs in vals.items()}))


def test_el_geojson_ciego_trae_las_claves_que_la_app_devuelve(tmp_path):
    """Sin `id` y `lote`, PIX Scout cae a ids POSICIONALES F-1..F-n que se
    renumeran en cada ronda (el orden de visita se baraja). La validacion
    registrada hoy no se podria rastrear al lote la semana que viene, y sin eso no
    hay precision medible: el lazo de retorno no cierra."""
    import json
    m = ms.sortear(poblacion(), n_por_estrato={e: 3 for e in ms.ESTRATOS})
    geoms = {lid: {'type': 'Point', 'coordinates': [0, 0]} for lid in m['lote_id']}
    p = tmp_path / 'ciego.geojson'
    ms.a_geojson_ciego(m, geoms, str(p))
    props = json.load(open(p, encoding='utf-8'))['features'][0]['properties']
    for k in ('id', 'name', 'lote', 'lote_id', 'estrato', 'status'):
        assert k in props, 'falta %r: la app lo lee y lo devuelve' % k
    # `estrato` viaja VACIO: la app lo guarda y lo devuelve, sin poder mostrarlo.
    assert props['estrato'] is None
    assert props['id'] == props['lote_id']


# --- Puerta 4.2: n calculado, no adivinado -----------------------------------
def test_n_crece_cuando_se_pide_mas_precision():
    n1 = ms.n_para_proporcion(0.30, semiancho=0.10)
    n2 = ms.n_para_proporcion(0.30, semiancho=0.05)
    assert n2 > n1 * 3


def test_correccion_por_poblacion_finita():
    assert ms.n_para_proporcion(0.5, 0.10, N=50) < ms.n_para_proporcion(0.5, 0.10)


def test_avisa_cuando_el_IC_es_mas_ancho_que_la_prevalencia():
    """Estimar 5% con +-10 puntos no distingue 'funciona' de 'no funciona'."""
    _, ver = ms.dimensionar({e: 200 for e in ms.ESTRATOS}, p_esperada=0.05, semiancho=0.10)
    assert any('MAS ANCHO' in a for a in ver['avisos'])


def test_avisa_cuando_no_alcanza_la_capacidad_del_cliente():
    """La pregunta real no es 'cuantos', es si el cliente puede pagarlo en el año."""
    _, ver = ms.dimensionar({e: 500 for e in ms.ESTRATOS}, p_esperada=0.30,
                            semiancho=0.05, K_por_ronda=10, rondas_disponibles=20)
    assert ver['alcanza'] is False
    assert any('NO ALCANZA' in a for a in ver['avisos'])


# --- Puerta 4.4: metricas correctas ------------------------------------------
def test_sin_verde_el_resultado_NO_es_concluyente():
    """EL TEST QUE IMPORTA. Visitar solo los rojos da precision alta por construccion."""
    m = ms.sortear(poblacion(), n_por_estrato={'ATENCION': 15, 'VIGILANCIA': 15})
    v = campo(m, {'ATENCION': 0.8, 'VIGILANCIA': 0.5, 'SIN SEÑAL': 0.05})
    r = vl.evaluar(v)
    assert r['concluyente'] is False
    assert any('VERDE' in a for a in r['avisos'])


def test_la_prevalencia_no_se_infla_con_el_sobremuestreo():
    """Sin pesos de diseño, la prevalencia estimada seria la del rojo, no la del campo."""
    pob = poblacion(n_at=20, n_vi=40, n_sin=440)
    m = ms.sortear(pob, n_por_estrato={'ATENCION': 20, 'VIGILANCIA': 20, 'SIN SEÑAL': 40}, semilla=1)
    tasas = {'ATENCION': 0.80, 'VIGILANCIA': 0.40, 'SIN SEÑAL': 0.05}
    v = campo(m, tasas, semilla=1)
    r = vl.evaluar(v)
    # prevalencia real ponderada por N: (20*.8 + 40*.4 + 440*.05)/500 = 0,0928
    esperada = (20 * .8 + 40 * .4 + 440 * .05) / 500
    assert abs(r['prevalencia'] - esperada) < 0.06
    # el promedio INGENUO de la muestra estaria muy por encima
    ingenua = v['hubo_problema'].mean()
    assert ingenua > r['prevalencia'] + 0.15


def test_avisa_si_el_mapa_no_rinde_mas_que_ir_al_azar():
    """Un resultado en contra es un resultado valido y tiene que decirse."""
    pob = poblacion()
    m = ms.sortear(pob, n_por_estrato={'ATENCION': 20, 'VIGILANCIA': 20, 'SIN SEÑAL': 40}, semilla=2)
    v = campo(m, {'ATENCION': 0.10, 'VIGILANCIA': 0.10, 'SIN SEÑAL': 0.10}, semilla=2)
    r = vl.evaluar(v)
    assert any('NO supera' in a for a in r['avisos'])
    assert r['lift'] < 1.2


def test_lift_alto_cuando_el_sistema_funciona():
    pob = poblacion()
    m = ms.sortear(pob, n_por_estrato={'ATENCION': 20, 'VIGILANCIA': 20, 'SIN SEÑAL': 40}, semilla=4)
    v = campo(m, {'ATENCION': 0.85, 'VIGILANCIA': 0.45, 'SIN SEÑAL': 0.03}, semilla=4)
    r = vl.evaluar(v)
    assert r['lift'] > 3
    assert r['concluyente'] is True


def test_el_CLI_se_niega_a_sortear_sin_verde(tmp_path, capsys):
    """Bug real encontrado al probar con datos de HDS: `main.py --K` recorta el ranking
    a los lotes que salen de control, asi que el CSV NO tiene estrato verde. El CLI
    emitia igual una muestra 100% roja — el sesgo de verificacion que todo esto evita."""
    from pix_alerta import disenar_muestra as dm
    recortado = poblacion(n_at=4, n_vi=2, n_sin=0)      # tal cual sale con --K
    p = tmp_path / 'ranking_cortado.csv'
    recortado.to_csv(p, index=False)
    rc = dm.main(['--ranking', str(p), '--sitio', 'HDS', '--salida', str(tmp_path)])
    assert rc == 1
    out = capsys.readouterr().out
    assert 'SIN SEÑAL' in out and 'SESGO DE VERIFICACION' in out
    assert not list(tmp_path.glob('muestra_*.csv')), 'no debe emitir muestra'


def test_el_CLI_sortea_cuando_el_ranking_esta_completo(tmp_path):
    from pix_alerta import disenar_muestra as dm
    completo = poblacion(n_at=10, n_vi=7, n_sin=190)
    p = tmp_path / 'ranking_completo.csv'
    completo.to_csv(p, index=False)
    rc = dm.main(['--ranking', str(p), '--prevalencia', '0.30', '--semiancho', '0.10',
                  '--salida', str(tmp_path)])
    assert rc == 10
    m = pd.read_csv(list(tmp_path.glob('muestra_*.csv'))[0])
    assert set(m['estrato']) == set(ms.ESTRATOS)
    assert (m['prob_inclusion'] > 0).all()


def test_no_existe_exactitud_global():
    """La Puerta 4.4 dice 'NUNCA exactitud global': no debe haber forma de pedirla."""
    assert not hasattr(vl, 'exactitud_global')
    assert not hasattr(vl, 'accuracy')


def test_pr_auc_ponderada_no_se_define_con_una_sola_clase():
    """Devolver 0,5 cuando no hay ambas clases seria inventar un resultado."""
    pob = poblacion()
    m = ms.sortear(pob, n_por_estrato={e: 10 for e in ms.ESTRATOS})
    v = m.copy(); v['hubo_problema'] = False
    auc, _ = vl.pr_auc(v)
    assert np.isnan(auc)


def test_pr_auc_mejor_que_azar_cuando_el_score_ordena():
    pob = poblacion()
    m = ms.sortear(pob, n_por_estrato={'ATENCION': 20, 'VIGILANCIA': 20, 'SIN SEÑAL': 40}, semilla=5)
    v = campo(m, {'ATENCION': 0.85, 'VIGILANCIA': 0.45, 'SIN SEÑAL': 0.03}, semilla=5)
    auc, curva = vl.pr_auc(v)
    assert np.isfinite(auc) and 0 < auc <= 1
    assert len(curva) == len(v)


def test_el_informe_declara_siempre_la_prevalencia():
    """Una precision sin la prevalencia al lado no se puede interpretar."""
    pob = poblacion()
    m = ms.sortear(pob, n_por_estrato={'ATENCION': 20, 'VIGILANCIA': 20, 'SIN SEÑAL': 40}, semilla=6)
    v = campo(m, {'ATENCION': 0.8, 'VIGILANCIA': 0.4, 'SIN SEÑAL': 0.05}, semilla=6)
    txt = vl.informe(vl.evaluar(v))
    assert 'Prevalencia del campo' in txt
    assert 'exactitud global' in txt          # se declara por que NO esta
