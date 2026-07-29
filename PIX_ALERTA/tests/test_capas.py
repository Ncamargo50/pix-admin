# -*- coding: utf-8 -*-
"""Las capas de contexto no pueden disfrazarse de alerta.

Es la propiedad que justifica que existan por separado. Si una zona estructural
llega al tecnico con severidad y numero de recorrida, el producto miente: lo manda a
caminar hoy una mancha de suelo que esta ahi desde hace tres campañas.
"""
import json

import pytest

from pix_alerta import capas as cp


class _Sitio:
    clave = 'X'
    titulo = 'Campo de prueba'
    campo_id = 'lote'
    campo_area = 'area_ha'
    cultivo = 'trigo'
    siembras = ()


def _zona(lote='L1', i=1, area=0.5, z=-3.2):
    return {'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1],
                                                             [1, 1], [0, 0]]]},
            'properties': {'tipo': 'zona', 'id': '%s-Z%d' % (lote, i),
                           'etiqueta': 'Z%d' % i, 'lote_id': lote,
                           'area_ha': area, 'pct_lote': 1.2,
                           'deficit_z': abs(z), 'clase': 'zona a investigar'}}


def _estrato(lote='L1', k=1, dif=27.9):
    return {'type': 'Feature',
            'geometry': {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1],
                                                             [1, 1], [0, 0]]]},
            'properties': {'tipo': 'estrato', 'id': '%s-B%d' % (lote, k),
                           'etiqueta': 'B%d' % k, 'lote_id': lote, 'estrato': k,
                           'area_ha': 39.0, 'atraso_medido_dias': 36.9,
                           'atraso_declarado_dias': 9, 'diferencia_dias': dif}}


# --- la separacion con la app -------------------------------------------------

def test_ninguna_feature_de_contexto_puede_pasar_por_foco_en_la_app():
    """PIX Scout trata como FOCO todo lo que no sea perimetro. Mientras la app
    firmada no sepa ignorar estas capas, no pueden ir en el mismo archivo — y este
    modulo tiene que producir su PROPIO paquete, no mezclarse con el de focos."""
    g = cp.a_geojson(_Sitio(), {'L1': {'zonas': [_zona()]}},
                     {'L1': {'estratos': [_estrato()]}})
    tipos = {f['properties']['tipo'] for f in g['features']}
    assert tipos == {'zona', 'estrato'}
    for f in g['features']:
        p = f['properties']
        assert p['capa'] == 'contexto', 'sin esta marca no se pueden separar'
        # Lo que la app usa para armar el recorrido. Nada de esto puede existir aca.
        assert 'sev' not in p, 'una zona con severidad se convierte en alerta'
        assert 'z_sev' not in p
        assert 'status' not in p


def test_el_geojson_de_contexto_no_es_el_de_la_app():
    """Se comprueba contra el modulo real: los dos paquetes tienen que diferir en
    el `tipo` de sus features, no solo en el nombre del archivo."""
    from pix_alerta import focos as fo
    foco = {'type': 'Feature', 'geometry': _zona()['geometry'],
            'properties': {'etiqueta': 'F1', 'z_sev': -3.5, 'area_ha': 0.4}}
    app = fo.a_geojson(_Sitio(), {'L1': {'focos': [foco]}})
    ctx = cp.a_geojson(_Sitio(), {'L1': {'zonas': [_zona()]}})
    assert all('tipo' not in f['properties'] for f in app['features'])
    assert all(f['properties'].get('tipo') for f in ctx['features'])


def test_el_perimetro_sigue_siendo_perimetro_en_las_dos_capas():
    per = {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 2], [2, 2], [0, 0]]]}
    g = cp.a_geojson(_Sitio(), {}, {}, perimetro=per)
    assert g['features'][0]['properties']['tipo'] == 'perimetro'


# --- el lenguaje es parte del contrato ----------------------------------------

def test_una_zona_se_entrega_como_zona_a_investigar_y_no_como_alerta():
    z = _zona()
    g = cp.a_geojson(_Sitio(), {'L1': {'zonas': [z]}})
    p = g['features'][0]['properties']
    assert p['clase'] == 'zona a investigar'
    assert 'alerta' not in json.dumps(p, ensure_ascii=False).lower()


def test_el_modulo_declara_por_que_va_en_archivo_aparte():
    """El proximo que lo lea tiene que entender que es una decision de contrato con
    una app ya firmada, no un olvido — o lo va a 'arreglar' mezclandolo."""
    d = ' '.join((cp.__doc__ or '').split())
    assert 'isPerimeter' in d
    assert 'v1.0.11' in d, 'no dice contra que version de la app se decidio'


# --- el resumen, que es lo que se imprime y va al informe ---------------------

def test_el_resumen_cuenta_zonas_y_hectareas():
    r = cp.resumen({'L1': {'zonas': [_zona(area=0.5), _zona(i=2, area=0.4)],
                           'area_zonas_ha': 0.9},
                    'L2': {'zonas': [], 'area_zonas_ha': 0.0}}, {})
    assert r['n_zonas'] == 2
    assert r['area_zonas_ha'] == 0.9


def test_solo_entran_al_resumen_los_bloques_por_encima_de_la_cadencia():
    """Una diferencia menor que la cadencia de observacion no se distingue del
    muestreo temporal. Informarla seria inventar precision que el satelite no da."""
    est = {'L1': {'lote_id': 'L1', 'sin_estratos': False, 'contraste': {
        3: {'medido': 0.0, 'declarado': 0, 'diferencia': 0.0},
        2: {'medido': 12.0, 'declarado': 3, 'diferencia': 9.0},
        1: {'medido': 36.9, 'declarado': 9, 'diferencia': 27.9}}}}
    r = cp.resumen({}, est)
    assert r['lotes_con_estratos'] == 1
    dif = [b['diferencia_dias'] for b in r['bloques_en_atencion']]
    assert dif == [27.9], 'el de 9,0 dias esta por debajo de la cadencia util'


def test_un_lote_sin_estratos_no_cuenta_como_lote_con_estratos():
    """3 de cada 4 lotes medidos NO tienen estratos, y eso es un resultado correcto.
    Contarlos inflaria el producto."""
    r = cp.resumen({}, {'L1': {'lote_id': 'L1', 'sin_estratos': True,
                               'contraste': {}}})
    assert r['lotes_con_estratos'] == 0
    assert r['bloques_en_atencion'] == []


def test_una_diferencia_sin_dato_declarado_no_entra():
    """Sin fecha declarada no hay contraste. Suponer cero afirmaria que no hay
    anomalia, que es justo lo que no se sabe."""
    r = cp.resumen({}, {'L1': {'lote_id': 'L1', 'sin_estratos': False,
                               'contraste': {1: {'medido': 30.0,
                                                 'declarado': None,
                                                 'diferencia': None}}}})
    assert r['bloques_en_atencion'] == []


# --- la seccion del informe ---------------------------------------------------

def test_la_seccion_de_contexto_se_omite_cuando_no_hay_nada_que_decir():
    """Una seccion que aparece siempre diciendo 'no se encontro nada' se vuelve
    invisible, y ademas ocupa la pagina que necesita lo que si importa."""
    from pix_alerta import informe_focos as inf
    st = []
    n = inf._seccion_contexto(None, st, 3, None)
    assert (n, st) == (3, [])
    n = inf._seccion_contexto(None, st, 3, {'resumen': {'n_zonas': 0,
                                                        'bloques_en_atencion': []}})
    assert (n, st) == (3, [])


def test_la_seccion_de_contexto_nunca_usa_la_palabra_alerta():
    """El unico producto que exige recorrida inmediata es el foco. Si esta seccion
    dice 'alerta', el tecnico sale hoy a caminar una zona estructural."""
    import inspect

    from pix_alerta import informe_focos as inf
    cuerpo = inspect.getsource(inf._seccion_contexto)
    # Se admite la unica mencion valida: la que declara que esto NO es una alerta.
    menciones = [l for l in cuerpo.lower().split('\n') if 'alerta' in l]
    assert all('no es una' in l or 'no es alerta' in l for l in menciones), menciones


# --- una averia NO es un resultado -------------------------------------------

def test_un_lote_donde_el_analisis_fallo_no_cuenta_como_lote_sin_bloques():
    """`sin_estratos` tiene TRES estados y hay que respetarlos: True = una sola
    siembra, False = hay bloques, None = se rompio. Confundir None con True hace que
    una averia se lea como el resultado tranquilizador."""
    r = cp.resumen({}, {'L1': {'lote_id': 'L1', 'sin_estratos': None,
                               'error': 'TypeError: x', 'contraste': {}}})
    assert r['lotes_con_estratos'] == 0, 'una averia no es un lote CON bloques'
    assert r['lotes_con_averia'] == 1, 'la averia tiene que quedar a la vista'


def test_el_analisis_de_estratos_devuelve_averia_y_no_none():
    """Paso en produccion: un TypeError dejo al unico lote con tres bloques
    reportado como lote de una sola siembra. El contrato tiene que impedirlo."""
    from pix_alerta import estratos as es

    class _S:
        campo_id = 'lote'
        cultivo = 'trigo'
        ciclo_dias = 120
        siembras = ('2026-04-26', '2026-04-29', '2026-05-05')

    feat = {'properties': {'lote': 'L1'}}
    # Sin geometria valida el analisis revienta adentro: es exactamente el caso.
    d = es.analizar(_S(), feat, '2026-07-16', geom=object())
    assert d is not None, 'una averia devuelta como None se lee como "sin bloques"'
    assert d.get('averia') is True
    assert d.get('error')


def test_el_contraste_no_revienta_con_una_clave_de_texto():
    """Regresion del TypeError: el dict de desfase mezclaba claves int con una de
    texto y `sorted` comparaba int con str. Aunque el origen ya esta arreglado, el
    consumidor no puede volver a caerse por un dato accesorio."""
    from pix_alerta import estratos as es
    c = es.contraste({1: {'atraso_dias': 30.0}, '_ndvi_ref': 0.71}, {1: 9})
    assert set(c) == {1}
    assert c[1]['diferencia'] == 21.0


# --- el umbral no se elige por la salida que produce --------------------------

def test_la_unidad_minima_de_zona_no_se_bajo_para_fabricar_salida():
    """MEDIDO: en los 4 lotes de trigo x 5 fechas la zona mas grande fue 0,16 ha, o
    sea cuatro pixeles. La tentacion es bajar el umbral hasta que salga algo; es
    justo el error que este motor viene corrigiendo. Un umbral por debajo de lo que
    se puede caminar convierte grumos de ruido en 'zonas de manejo'."""
    from pix_alerta import criterio as cri
    assert cri.MMU_ZONA_HA >= 0.25, (
        'con menos de eso se entregan manchas de pocos pixeles como zonas de manejo')


def test_la_capa_declara_que_hoy_esta_muda_y_por_que():
    """Una capa conectada que nunca entrega y no lo dice es peor que no tenerla: el
    proximo que la lea va a suponer que funciona y que el campo esta perfecto."""
    d = ' '.join((cp.__doc__ or '').split())
    import inspect
    fuente = inspect.getsource(cp)
    assert '4 de 20' in fuente, 'no esta la medicion que respalda la afirmacion'
    assert '0,16 ha' in fuente
    assert 'barrer_zonas' in fuente, 'no dice como rehacer la medicion'


def test_sin_escena_no_es_ni_averia_ni_ausencia_de_zonas():
    """Tercer estado. Sin el, una fecha sin pasada del satelite salia como
    `EEException: Image.constant`, o sea como si el servicio se hubiera roto."""
    from pix_alerta import criterio as cri
    assert issubclass(cri.SinEscena, Exception)
    import inspect
    fuente = inspect.getsource(cp.zonas_lote)
    assert 'SinEscena' in fuente, 'capas no distingue el caso'
    assert 'sin_escena' in fuente
