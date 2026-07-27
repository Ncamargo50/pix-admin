"""Puertas del alta multicliente / multipropiedad.

El motor SIEMPRE soporto varios sitios por cliente (`clientes.py` los carga y
`correr_todos.py` los recorre). El que no lo soportaba era el ALTA: escribia
`sitios: [uno solo]` con clave fija y el panel mandaba `--forzar` siempre, asi que
dar de alta la segunda hacienda de un cliente le BORRABA la primera — la ficha y
tambien el archivo de lotes, que se llamaba por cliente y no por propiedad.

Nada fallaba: el cliente quedaba corriendo dos veces sobre el mismo campo.
"""
import json
import os

import pytest

from pix_alerta import alta_cliente as ac
from pix_alerta import clientes as cl


# --- derivacion de la clave de propiedad --------------------------------------

def _fin(cultivo, siembra):
    """Fin de ventana derivado de la TABLA, no cableado. El valor operativo de cada
    cultivo cambia cuando cambia la evidencia (2026-07-27: pasaron al extremo corto
    del rango observado); un test que congela la fecha convierte una decision
    agronomica en un test roto."""
    from pix_alerta import ciclos
    return ciclos.ventana(cultivo, siembra)[1]


def test_el_nombre_de_la_propiedad_da_la_clave():
    assert ac._slug('Los Angeles') == 'LOS_ANGELES'
    assert ac._slug('Santo Antônio') == 'SANTO_ANTONIO'
    assert ac._slug('São Francisco') == 'SAO_FRANCISCO'


def test_la_clave_de_propiedad_no_lleva_tildes_ni_simbolos():
    assert ac._slug('Estancia "La Ñata" #2') == 'ESTANCIA_LA_NATA_2'


def test_un_nombre_impronunciable_no_deja_la_clave_vacia():
    assert ac._slug('...') == 'SITIO'


def test_la_clave_de_propiedad_admite_mas_largo_que_la_de_cliente():
    """Nombra entregables, no carpetas. Recortarla de mas hace que dos haciendas
    distintas caigan en la misma clave y se mezclen los informes."""
    assert ac.SITIO_CLAVE_OK.match('CERRO_SANTO_ANTONIO')
    assert not ac.CLAVE_OK.match('CERRO_SANTO_ANTONIO')     # 19 > 16


# --- el alta acumula propiedades ----------------------------------------------

@pytest.fixture
def repo(tmp_path):
    os.makedirs(tmp_path / 'clientes', exist_ok=True)
    os.makedirs(tmp_path / 'lotes', exist_ok=True)
    return tmp_path


@pytest.fixture
def lotes(tmp_path):
    """GeoJSON minimo valido: 2 lotes cuadrados."""
    gj = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'lote': 'L%d' % i},
         'geometry': {'type': 'Polygon', 'coordinates': [[
             [-63.0 + i * 0.01, -17.0], [-63.0 + i * 0.01, -16.99],
             [-62.99 + i * 0.01, -16.99], [-62.99 + i * 0.01, -17.0],
             [-63.0 + i * 0.01, -17.0]]]}}
        for i in (1, 2)]}
    ruta = tmp_path / 'lotes_in.geojson'
    ruta.write_text(json.dumps(gj), encoding='utf-8')
    return str(ruta)


def _alta(repo, lotes, **kw):
    argv = ['--raiz', str(repo), '--lotes', lotes]
    for k, v in kw.items():
        if v is True:
            argv.append('--' + k.replace('_', '-'))
        elif v not in (None, False):
            argv += ['--' + k.replace('_', '-'), str(v)]
    return ac.main(argv)


def _ficha(repo, clave='CERRO'):
    with open(repo / 'clientes' / ('%s.json' % clave), encoding='utf-8') as fh:
        return json.load(fh)


def test_la_segunda_propiedad_se_agrega_y_no_pisa_la_primera(repo, lotes):
    """ESTE es el bug que motiva el archivo."""
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Los Angeles',
          cultivo='soya', siembra='2026-10-15')
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
          cultivo='maiz', siembra='2027-01-10')
    d = _ficha(repo)
    assert len(d['sitios']) == 2
    assert {s['cultivo'] for s in d['sitios']} == {'soya', 'maiz'}


def test_cada_propiedad_guarda_su_propio_archivo_de_lotes(repo, lotes):
    """Se llamaba por cliente: la 2da hacienda le sobreescribia los lotes a la 1ra
    y el cliente terminaba monitoreando dos veces el mismo campo."""
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Los Angeles',
          cultivo='soya', siembra='2026-10-15')
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
          cultivo='maiz', siembra='2027-01-10')
    archivos = sorted(os.listdir(repo / 'lotes'))
    assert 'cerro_los_angeles.geojson' in archivos
    assert 'cerro_san_rafael.geojson' in archivos
    rutas = {s['lotes_geojson'] for s in _ficha(repo)['sitios']}
    assert len(rutas) == 2, 'dos propiedades apuntando al mismo archivo'


def test_cada_propiedad_tiene_su_cultivo_y_su_ventana(repo, lotes):
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Los Angeles',
          cultivo='soya', siembra='2026-10-15')
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
          cultivo='trigo', siembra='2027-05-01')
    c = cl.cargar(str(repo / 'clientes' / 'CERRO.json'))
    por_clave = {s.clave: s for s in c.sitios}
    assert por_clave['CERRO_LOS_ANGELES'].campanas['2026/2027'] == ('2026-10-15',
                                                                   _fin('soya', '2026-10-15'))
    assert por_clave['CERRO_SAN_RAFAEL'].campanas['2027'] == ('2027-05-01',
                                                              _fin('trigo', '2027-05-01'))


def test_repetir_una_propiedad_se_rechaza(repo, lotes):
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
          cultivo='maiz', siembra='2027-01-10')
    with pytest.raises(SystemExit, match='ya tiene la propiedad'):
        _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
              cultivo='maiz', siembra='2027-01-10')


def test_reemplazar_una_propiedad_conserva_las_demas(repo, lotes):
    for prop, cul in (('Los Angeles', 'soya'), ('San Rafael', 'maiz')):
        _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad=prop,
              cultivo=cul, siembra='2026-10-15')
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
          cultivo='sorgo', siembra='2027-02-01', reemplazar_propiedad=True)
    d = _ficha(repo)
    assert len(d['sitios']) == 2
    por = {s['titulo']: s['cultivo'] for s in d['sitios']}
    assert por == {'Los Angeles': 'soya', 'San Rafael': 'sorgo'}


def test_agregar_propiedad_no_borra_el_contacto_del_cliente(repo, lotes):
    """El alta de la 2da hacienda no trae los datos de contacto: si partiera de
    cero, el cliente se quedaria sin el numero al que se le avisa."""
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Los Angeles',
          cultivo='soya', siembra='2026-10-15', contacto='Marcelo',
          whatsapp='+59170000000', K=12)
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='San Rafael',
          cultivo='maiz', siembra='2027-01-10')
    c = cl.cargar(str(repo / 'clientes' / 'CERRO.json'))
    assert c.whatsapp == '+59170000000'
    assert c.contacto['nombre'] == 'Marcelo'
    assert c.K == 12


def test_reusar_la_clave_de_otro_cliente_se_rechaza(repo, lotes):
    """Dos clientes con la misma clave comparten carpeta de salida: es mandarle a
    un productor los datos de su vecino."""
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Los Angeles',
          cultivo='soya', siembra='2026-10-15')
    with pytest.raises(SystemExit, match='ya es de'):
        _alta(repo, lotes, clave='CERRO', titulo='Estancia Vecina',
              cultivo='soya', siembra='2026-10-15')


def test_forzar_sigue_reemplazando_al_cliente_entero(repo, lotes):
    """Es la salida para empezar de nuevo, y tiene que seguir estando — pero como
    bandera explicita, no como default del panel."""
    for prop in ('Los Angeles', 'San Rafael'):
        _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad=prop,
              cultivo='soya', siembra='2026-10-15')
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Unica',
          cultivo='soya', siembra='2026-10-15', forzar=True)
    assert len(_ficha(repo)['sitios']) == 1


def test_clientes_distintos_no_se_mezclan(repo, lotes):
    _alta(repo, lotes, clave='CERRO', titulo='Cerro Alto', propiedad='Los Angeles',
          cultivo='soya', siembra='2026-10-15')
    _alta(repo, lotes, clave='VECINA', titulo='Estancia Vecina',
          propiedad='Campo Norte', cultivo='maiz', siembra='2026-11-01')
    todos = cl.cargar_todos(str(repo / 'clientes'), solo_activos=False)
    assert {c.clave for c in todos} == {'CERRO', 'VECINA'}
    # y cada uno escribe en SU carpeta
    assert todos[0].salida('sal') != todos[1].salida('sal')
