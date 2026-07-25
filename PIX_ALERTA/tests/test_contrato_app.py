"""El contrato entre PIX_ALERTA y la app de campo (PIX Scout).

POR QUE ESTE ARCHIVO EXISTE
---------------------------
Los dos lados tenían tests verdes y la cadena igual estaba rota: la app leía el GeoJSON
del motor y mostraba 6 focos con id `F-1`..`F-6` —posicionales, se renumeran en cada
corrida—, el lote como "Lote 1" en vez de `J1_soya`, hacienda "Campo", sin severidad y
sin perímetro. Con ids posicionales **el lazo de retorno no existe**: una validación
registrada hoy no se puede rastrear al lote la semana que viene.

Ningún test unitario lo iba a encontrar, porque el defecto está en la JUNTURA. Estos
tests fijan los nombres de campo que la app efectivamente lee (`js/geojson.js`), que no
son decorativos: son la interfaz.
"""
import json

import pandas as pd
import pytest

from pix_alerta import config as cfg
from pix_alerta.main import _geojson_salida


# Lo que `js/geojson.js` lee de cada foco. Si alguno se cae, el técnico ve otra cosa.
CAMPOS_APP = ('id', 'name', 'etiqueta', 'hacienda', 'fecha_img', 'sev', 'area_ha',
              'estrato', 'status')


class SitioFalso:
    clave = 'TST'
    titulo = 'Hacienda de Prueba'
    campo_id = 'lote'

    def __init__(self, ruta):
        self.lotes_geojson = ruta


def _lotes(tmp_path, ids):
    feats = []
    for i, lid in enumerate(ids):
        x, y = -63.2 + 0.01 * i, -17.8
        feats.append({'type': 'Feature', 'properties': {'lote': lid},
                      'geometry': {'type': 'Polygon', 'coordinates': [[
                          [x, y], [x + .008, y], [x + .008, y + .006],
                          [x, y + .006], [x, y]]]}})
    p = tmp_path / 'lotes.geojson'
    p.write_text(json.dumps({'type': 'FeatureCollection', 'features': feats}),
                 encoding='utf-8')
    return SitioFalso(str(p))


def _rank(ids, estados):
    return pd.DataFrame([
        dict(lote_id=l, orden=i + 1, estado=e, fecha_dato='2026-04-29',
             dias_atras=1, area_ha=12.4, score=2.5 - i * 0.3)
        for i, (l, e) in enumerate(zip(ids, estados))])


def _emitir(tmp_path, ids, estados):
    sitio = _lotes(tmp_path, ids)
    out = tmp_path / 'salida.geojson'
    n = _geojson_salida(sitio, _rank(ids, estados), str(out))
    return n, json.load(open(out, encoding='utf-8'))


def _focos(gj):
    return [f for f in gj['features']
            if (f['properties'].get('tipo') or '') != 'perimetro']


# --- el bug que estaba vivo ---------------------------------------------------
def test_el_id_es_el_lote_no_una_posicion(tmp_path):
    """EL TEST QUE IMPORTA. Con id posicional el lazo de retorno no se puede cerrar."""
    _, gj = _emitir(tmp_path, ['J1_soya', 'A1'], ['ATENCION', 'VIGILANCIA'])
    ids = [f['properties']['id'] for f in _focos(gj)]
    assert ids == ['J1_soya', 'A1']
    assert not any(i.startswith('F-') for i in ids)


def test_el_tecnico_puede_casar_el_lote_con_el_informe(tmp_path):
    """Si el mapa dice "Lote 1" y el informe dice "J1_soya", no sirve de nada."""
    _, gj = _emitir(tmp_path, ['J1_soya'], ['ATENCION'])
    p = _focos(gj)[0]['properties']
    assert p['etiqueta'] == 'J1_soya' and p['name'] == 'J1_soya'


def test_lleva_todos_los_campos_que_lee_la_app(tmp_path):
    _, gj = _emitir(tmp_path, ['L1'], ['ATENCION'])
    p = _focos(gj)[0]['properties']
    faltan = [c for c in CAMPOS_APP if c not in p]
    assert not faltan, 'la app no va a encontrar: %s' % faltan


def test_la_hacienda_no_es_Campo(tmp_path):
    _, gj = _emitir(tmp_path, ['L1'], ['ATENCION'])
    assert _focos(gj)[0]['properties']['hacienda'] == 'Hacienda de Prueba'


def test_hay_severidad_para_los_alertados(tmp_path):
    """Sin `sev`, la app deriva null y todo sale 'sin dato de severidad'."""
    _, gj = _emitir(tmp_path, ['A', 'V', 'S'],
                    ['ATENCION', 'VIGILANCIA', 'SIN SEÑAL'])
    sev = {f['properties']['id']: f['properties']['sev'] for f in _focos(gj)}
    assert sev['A'] == 'alta' and sev['V'] == 'media'
    assert sev['S'] is None       # sin señal no es una severidad, es la ausencia


def test_emite_perimetro_para_encuadrar_el_mapa(tmp_path):
    _, gj = _emitir(tmp_path, ['L1', 'L2'], ['ATENCION', 'VIGILANCIA'])
    per = [f for f in gj['features']
           if f['properties'].get('tipo') == 'perimetro']
    assert len(per) == 1
    assert per[0]['geometry']['type'] in ('Polygon', 'MultiPolygon')


def test_el_perimetro_no_cuenta_como_foco(tmp_path):
    """`_geojson_salida` devuelve la cantidad de FOCOS; contar el perímetro haría que
    el informe declare un lote de más."""
    n, gj = _emitir(tmp_path, ['L1', 'L2'], ['ATENCION', 'VIGILANCIA'])
    assert n == 2 and len(gj['features']) == 3


def test_el_estrato_sigue_viajando_para_el_modo_ciego(tmp_path):
    """La app lo GUARDA y no lo muestra. Si se cae, no hay con qué medir después."""
    _, gj = _emitir(tmp_path, ['L1'], ['ATENCION'])
    assert _focos(gj)[0]['properties']['estrato'] == 'ATENCION'


def test_id_duplicado_sigue_siendo_error(tmp_path):
    sitio = _lotes(tmp_path, ['L1'])
    r = _rank(['L1', 'L1'], ['ATENCION', 'VIGILANCIA'])
    with pytest.raises(RuntimeError, match='duplicado'):
        _geojson_salida(sitio, r, str(tmp_path / 'x.geojson'))
