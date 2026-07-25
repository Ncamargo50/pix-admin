"""Puertas de la capa multi-cliente.

La que manda es el AISLAMIENTO: un entregable de un cliente en la carpeta de otro no es
un bug de formato, es mandarle a un productor los lotes de su vecino. Y la segunda es que
un cliente roto no puede dejar sin informe a los demas.
"""
import json
import os

import pytest

from pix_alerta import clientes as cl
from pix_alerta import config as cfg


SITIO_OK = {
    'clave': 'TEST_A', 'titulo': 'Sitio A',
    'lotes_geojson': 'lotes/a.geojson', 'campo_id': 'lote',
    'epsg_metrico': 'EPSG:32720',
    'campanas': {'2025/2026': ['2025-10-01', '2026-04-30']},
}


def escribir(tmp, nombre, d):
    p = tmp / nombre
    p.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
    return str(p)


def cliente_min(clave='CA', **kw):
    d = {'clave': clave, 'titulo': 'Cliente ' + clave, 'sitios': [dict(SITIO_OK)]}
    d.update(kw)
    return d


# --- alta de cliente sin tocar codigo ----------------------------------------
def test_alta_de_cliente_es_un_archivo(tmp_path):
    """El requisito del plan: dar de alta un cliente NO debe requerir editar .py."""
    escribir(tmp_path, 'CA.json', cliente_min('CA'))
    cs = cl.cargar_todos(str(tmp_path))
    assert [c.clave for c in cs] == ['CA']
    assert cs[0].sitios[0].clave == 'TEST_A'


def test_rutas_relativas_al_archivo_del_cliente(tmp_path):
    """Un cliente debe ser una carpeta portable, no rutas del Escritorio de alguien."""
    escribir(tmp_path, 'CA.json', cliente_min('CA'))
    s = cl.cargar_todos(str(tmp_path))[0].sitios[0]
    assert os.path.isabs(s.lotes_geojson)
    assert s.lotes_geojson.endswith(os.path.join('lotes', 'a.geojson'))
    assert str(tmp_path) in s.lotes_geojson


# --- aislamiento entre clientes ----------------------------------------------
def test_cada_cliente_escribe_en_su_carpeta(tmp_path):
    escribir(tmp_path, 'CA.json', cliente_min('CA'))
    c = cl.cargar_todos(str(tmp_path))[0]
    assert c.salida('/base') == os.path.join('/base', 'CA')


def test_clave_de_cliente_repetida_es_error(tmp_path):
    """Dos clientes con la misma clave comparten carpeta: el informe de uno pisa al otro."""
    escribir(tmp_path, 'uno.json', cliente_min('CA'))
    dos = cliente_min('CA')
    dos['sitios'][0]['clave'] = 'TEST_B'
    escribir(tmp_path, 'dos.json', dos)
    with pytest.raises(ValueError, match='repetida'):
        cl.cargar_todos(str(tmp_path))


def test_clave_de_sitio_con_guion_bajo_se_lee_bien():
    """El bug que atrapo esta suite: partir el nombre por '_' devolvia 'TEST' para
    'ranking_TEST_A_2026-04-30.csv' y marcaba como ajeno un archivo propio. Un chequeo
    con falsas alarmas se termina apagando, y ahi si se filtran datos."""
    from pix_alerta.correr_todos import sitio_de_archivo as f
    assert f('ranking_TEST_A_2026-04-30.csv') == 'TEST_A'
    assert f('lotes_SANTO_ANTONIO_2026-04-30.geojson') == 'SANTO_ANTONIO'
    assert f('serie_HDS.csv') == 'HDS'
    assert f('ranking_HDS_2026-04-30.csv') == 'HDS'
    assert f('_stats.json') is None          # no lo emite el motor
    assert f('informe.pdf') is None


def test_detecta_entregable_de_otro_cliente(tmp_path):
    """La verificacion no confia en que cada modulo escriba donde debe: mira la carpeta."""
    from pix_alerta import correr_todos as ct
    escribir(tmp_path, 'CA.json', cliente_min('CA'))
    c = cl.cargar_todos(str(tmp_path))[0]
    base = tmp_path / 'salida'
    d = base / 'CA'
    d.mkdir(parents=True)
    (d / 'ranking_TEST_A_2026-04-30.csv').write_text('ok', encoding='utf-8')
    assert ct.verificar_aislamiento([c], str(base)) == []
    # ahora aparece el ranking de un sitio que NO es suyo
    (d / 'ranking_OTROSITIO_2026-04-30.csv').write_text('fuga', encoding='utf-8')
    problemas = ct.verificar_aislamiento([c], str(base))
    assert len(problemas) == 1 and 'OTROSITIO' in problemas[0]


# --- un cliente roto no puede tapar a los demas ------------------------------
def test_cliente_ilegible_no_se_saltea_en_silencio(tmp_path):
    """Saltear un cliente roto = dejarlo sin informe y que nadie se entere."""
    escribir(tmp_path, 'CA.json', cliente_min('CA'))
    (tmp_path / 'roto.json').write_text('{esto no es json', encoding='utf-8')
    with pytest.raises(ValueError, match='mal declarados'):
        cl.cargar_todos(str(tmp_path))


def test_un_sitio_que_falla_no_frena_a_los_demas(tmp_path, monkeypatch):
    from pix_alerta import correr_todos as ct
    d = cliente_min('CA')
    d['sitios'].append(dict(SITIO_OK, clave='TEST_B', titulo='Sitio B'))
    escribir(tmp_path, 'CA.json', d)
    c = cl.cargar_todos(str(tmp_path))[0]

    def falso_main(argv):
        if 'TEST_A' in argv:
            raise RuntimeError('GeoJSON ilegible')
        return 10

    monkeypatch.setattr(ct.m, 'main', falso_main)
    args = type('A', (), {'salida': str(tmp_path / 'out'), 'hasta': '2026-04-30',
                          'desde': None, 'K': None, 'serie': None, 'trazas': False})()
    filas = ct.correr_cliente(c, args)
    assert len(filas) == 2
    malo = [f for f in filas if f['sitio'] == 'TEST_A'][0]
    bueno = [f for f in filas if f['sitio'] == 'TEST_B'][0]
    assert malo['rc'] == 1 and 'GeoJSON ilegible' in malo['error']
    assert bueno['rc'] == 10          # el otro entrego igual


# --- validacion: fallar ruidoso antes de correr ------------------------------
def test_typo_en_campo_de_sitio_es_error(tmp_path):
    """'epsg' en vez de 'epsg_metrico' se aceptaria callado y proyectaria mal."""
    d = cliente_min('CA')
    d['sitios'][0]['epsg'] = 'EPSG:32721'
    escribir(tmp_path, 'CA.json', d)
    with pytest.raises(ValueError, match='desconocidos'):
        cl.cargar_todos(str(tmp_path))


def test_sitios_ref_inexistente_es_error(tmp_path):
    escribir(tmp_path, 'CA.json', {'clave': 'CA', 'titulo': 'x', 'sitios_ref': ['NO_EXISTE']})
    with pytest.raises(ValueError, match='no existe'):
        cl.cargar_todos(str(tmp_path))


def test_cliente_sin_sitios_es_error(tmp_path):
    escribir(tmp_path, 'CA.json', {'clave': 'CA', 'titulo': 'x'})
    with pytest.raises(ValueError, match='ningun sitio'):
        cl.cargar_todos(str(tmp_path))


def test_K_invalido_es_error(tmp_path):
    """K es la capacidad real de scouting: con K malo el corte del ranking no significa nada."""
    escribir(tmp_path, 'CA.json', cliente_min('CA', K=0))
    with pytest.raises(ValueError, match='K debe ser'):
        cl.cargar_todos(str(tmp_path))


def test_inactivo_no_corre(tmp_path):
    escribir(tmp_path, 'CA.json', cliente_min('CA', activo=False))
    assert cl.cargar_todos(str(tmp_path)) == []
    assert len(cl.cargar_todos(str(tmp_path), solo_activos=False)) == 1


def test_sitio_de_cliente_no_pisa_uno_ya_definido(tmp_path):
    """Si dos clientes declaran la misma clave de sitio, se falla en vez de resolver
    por orden de lectura del directorio."""
    d = cliente_min('CA')
    d['sitios'][0]['clave'] = 'HDS'          # choca con el HDS de config.py
    escribir(tmp_path, 'CA.json', d)
    cs = cl.cargar_todos(str(tmp_path))
    with pytest.raises(ValueError, match='choca'):
        cl.registrar_sitios(cs)


# --- el cliente real declarado en el repo ------------------------------------
def test_cliente_HDS_del_repo_carga():
    cs = cl.cargar_todos()
    hds = [c for c in cs if c.clave == 'HDS']
    assert hds, 'no se pudo cargar clientes/HDS.json'
    c = hds[0]
    assert c.K == 10
    assert [s.clave for s in c.sitios] == ['HDS']
    assert c.sitios[0] is cfg.SITIOS['HDS']   # reusa el sitio, no lo duplica
