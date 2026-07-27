# -*- coding: utf-8 -*-
"""Modo campo chico: el producto que aplica cuando no hay cohorte.

POR QUE EXISTE
--------------
El ranking compara cada lote contra la mediana de su cohorte y pide >= 8 lotes.
Santo Antonio y Sao Francisco en trigo tienen DOS lotes cada uno: no tienen cohorte
y nunca la van a tener. Sin este modo, ese cliente recibia `NO EVALUABLE` todos los
dias de la campaña — correcto pero inutil.

El acercamiento no necesita cohorte: compara cada pixel contra el mismo lote en la
escena limpia anterior.

LA TRAMPA QUE ESTAS PRUEBAS CUIDAN
----------------------------------
`focos.detectar_lote` escribe `nota` en DOS situaciones opuestas:

    a) no consiguio par de escenas          -> NO se pudo mirar
    b) miro y no hay focos sobre la MMU     -> se miro, y esta limpio

Clasificar por `nota` mezcla las dos. Paso: Sao Francisco salio `NO EVALUABLE`
cuando sus dos lotes se habian mirado el 2026-07-15 y estaban limpios. El
discriminador correcto es `fecha_img`: si hay fecha, hubo par y hubo mirada.
"""
import json

import pytest

from pix_alerta import config as cfg
from pix_alerta import main as m


class _Args:
    def __init__(self, salida):
        self.salida = str(salida)
        self.hasta = '2026-07-27'
        self.solo_focos = True


def _sitio(tmp_path):
    gj = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'lote': 'L1'},
         'geometry': {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1], [1, 1], [0, 0]]]}},
        {'type': 'Feature', 'properties': {'lote': 'L2'},
         'geometry': {'type': 'Polygon', 'coordinates': [[[2, 2], [2, 3], [3, 3], [2, 2]]]}},
    ]}
    p = tmp_path / 'lotes.geojson'
    p.write_text(json.dumps(gj), encoding='utf-8')
    return cfg.Sitio(clave='CHICO', titulo='Campo chico', lotes_geojson=str(p),
                     campo_id='lote', cultivo='trigo', solo_focos=True)


def _resultado(fecha_img=None, focos=(), nota=None, ha=100.0, error=None):
    return {'focos': list(focos), 'area_focos_ha': 0.42 * len(focos),
            'pct_lote': 0.0, 'pct_util': 1.1, 'area_util_ha': ha / 2,
            'area_lote_ha': ha, 'fecha_img': fecha_img, 'error': error,
            'fecha_ref': '2026-07-10' if fecha_img else None, 'nota': nota}


def _correr(monkeypatch, tmp_path, por_lote):
    from pix_alerta import focos as fo
    monkeypatch.setattr(fo, 'detectar', lambda *a, **k: por_lote)
    monkeypatch.setattr(fo, 'a_geojson',
                        lambda *a, **k: {'type': 'FeatureCollection', 'features': []})
    monkeypatch.setattr('pix_alerta.ee_init.inicializar', lambda: 'test')
    return m._entregar_acercamiento(_sitio(tmp_path), _Args(tmp_path))


NOTA_LIMPIO = ('Sin focos sobre la unidad minima de 0.20 ha: el lote salio de '
               'control por su promedio, el deterioro no esta concentrado.')


def test_mirado_y_limpio_es_SIN_NOVEDAD_aunque_traiga_nota(monkeypatch, tmp_path):
    """El caso que se clasificaba mal. Los dos lotes se miraron el 15 de julio."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(fecha_img='2026-07-15', nota=NOTA_LIMPIO),
        'L2': _resultado(fecha_img='2026-07-15', nota=NOTA_LIMPIO)})
    assert rc == m.SIN_NOVEDAD
    assert rc != m.NO_EVALUABLE


def test_sin_par_de_escenas_es_NO_EVALUABLE(monkeypatch, tmp_path):
    """Sin fecha de imagen no hubo par: no se pudo mirar, y no se puede decir que
    el campo este tranquilo."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(nota='Sin acercamiento: no hay par de fechas.'),
        'L2': _resultado(nota='Sin acercamiento: no hay par de fechas.')})
    assert rc == m.NO_EVALUABLE


def test_con_focos_entrega(monkeypatch, tmp_path):
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(fecha_img='2026-07-20', focos=[{'x': 1}, {'x': 2}]),
        'L2': _resultado(fecha_img='2026-07-15', nota=NOTA_LIMPIO)})
    assert rc == m.ENTREGADO


def test_ceguera_parcial_grande_NO_puede_decir_que_el_campo_esta_limpio(
        monkeypatch, tmp_path):
    """"Al menos un lote mirado" NO alcanza, y con dos lotes por sitio menos todavia.

    En Santo Antonio los lotes son 18,1 ha y 120,4 ha: mirar el chico y perder el
    grande deja el 87% del campo sin observar. Decir SIN_NOVEDAD ahi es afirmar algo
    sobre un campo que en su mayor parte no se vio. Se pondera por AREA."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(ha=120.4, nota='Sin acercamiento: no hay par de fechas.'),
        'L2': _resultado(ha=18.1, fecha_img='2026-07-15', nota=NOTA_LIMPIO)})
    assert rc == m.NO_EVALUABLE


def test_ceguera_parcial_chica_si_deja_afirmar_que_esta_limpio(monkeypatch, tmp_path):
    """El umbral no puede ser tan estricto que nunca entregue: con la mayor parte del
    area mirada, "sin novedad" es una afirmacion sostenible."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(ha=5.0, nota='Sin acercamiento: no hay par de fechas.'),
        'L2': _resultado(ha=120.0, fecha_img='2026-07-15', nota=NOTA_LIMPIO)})
    assert rc == m.SIN_NOVEDAD


def test_con_focos_se_entrega_aunque_falte_area_por_mirar(monkeypatch, tmp_path):
    """Encontrar algo en la parte que SI se vio es un resultado valido. Lo que no se
    puede afirmar es la ausencia."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(ha=120.4, nota='Sin acercamiento: no hay par de fechas.'),
        'L2': _resultado(ha=18.1, fecha_img='2026-07-20', focos=[{'x': 1}])})
    assert rc == m.ENTREGADO


def test_una_averia_total_es_FALLO_no_NO_EVALUABLE(monkeypatch, tmp_path):
    """Si TODOS los lotes cayeron por excepcion (cuota de GEE, timeout), el sitio no
    es "no evaluable por nubes": esta roto. NO_EVALUABLE esta en NO_FALLO, asi que
    una averia persistente no despertaria a nadie — y para un cliente `solo_focos`
    este es el UNICO producto."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(error='EEException', nota='Acercamiento no disponible (EEException).'),
        'L2': _resultado(error='EEException', nota='Acercamiento no disponible (EEException).')})
    assert rc not in m.NO_FALLO


def test_sin_par_de_escenas_no_es_averia(monkeypatch, tmp_path):
    """Nubes persistentes no son un fallo del programa: es el clima."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(nota='Sin acercamiento: no hay par de fechas.'),
        'L2': _resultado(nota='Sin acercamiento: no hay par de fechas.')})
    assert rc == m.NO_EVALUABLE


def test_un_campo_id_mal_escrito_no_entrega_focos_irrastreables(monkeypatch, tmp_path):
    """Con `campo_id` que no matchea, los lotes colapsaban en la clave 'None', se
    evaluaba uno solo y se devolvia ENTREGADO con focos rotulados 'None-F1'. Sin id
    estable no hay lazo de retorno: lo que registre el tecnico no se puede atribuir."""
    from pix_alerta import focos as fo
    monkeypatch.setattr(fo, 'detectar',
                        lambda *a, **k: {'None': _resultado(fecha_img='2026-07-20',
                                                            focos=[{'x': 1}])})
    monkeypatch.setattr(fo, 'a_geojson',
                        lambda *a, **k: {'type': 'FeatureCollection', 'features': []})
    monkeypatch.setattr('pix_alerta.ee_init.inicializar', lambda: 'test')
    s = _sitio(tmp_path)
    s.campo_id = 'no_existe_esta_columna'
    rc = m._entregar_acercamiento(s, _Args(tmp_path))
    assert rc not in m.NO_FALLO


def test_el_sitio_declara_el_modo_y_no_hace_falta_la_bandera(tmp_path):
    """El cron llama a `correr_todos`, no a `main`: si el modo dependiera solo de
    la bandera de linea de comandos, en la nube no se aplicaria nunca."""
    s = _sitio(tmp_path)
    assert s.solo_focos is True
    assert cfg.Sitio(clave='X', titulo='X', lotes_geojson='x',
                     campo_id='lote').solo_focos is False


def test_una_escena_vieja_no_sirve_para_hablar_de_hoy(monkeypatch, tmp_path):
    """`focos.VENTANA_DIAS` busca 90 dias hacia atras: con nubes persistentes el
    motor seguia formando un par de hace 50 dias y devolviendo SIN_NOVEDAD. El
    ranking ya declara SIN DATO pasados CADUCIDAD_DIAS; aca no habia equivalente."""
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(ha=100.0, fecha_img='2026-05-20', nota=NOTA_LIMPIO),
        'L2': _resultado(ha=100.0, fecha_img='2026-05-20', nota=NOTA_LIMPIO)})
    assert rc == m.NO_EVALUABLE


def test_una_escena_reciente_si_sirve(monkeypatch, tmp_path):
    rc = _correr(monkeypatch, tmp_path, {
        'L1': _resultado(ha=100.0, fecha_img='2026-07-20', nota=NOTA_LIMPIO),
        'L2': _resultado(ha=100.0, fecha_img='2026-07-15', nota=NOTA_LIMPIO)})
    assert rc == m.SIN_NOVEDAD
