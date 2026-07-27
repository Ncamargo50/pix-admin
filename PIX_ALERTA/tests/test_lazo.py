# -*- coding: utf-8 -*-
"""Puertas del lazo de retorno.

Es la pieza sin la cual NO HAY NINGUN NUMERO PROPIO. Auditado 2026-07-26: aunque
se pegaran las credenciales, el lazo no cerraba — la app manda `focoId`/`hallazgo`
y el motor espera `lote_id`/`hubo_problema`, y **`hubo_problema` no tenia productor
en ningun lado del repositorio**.
"""
import json

import pandas as pd
import pytest

from pix_alerta import lazo


def _crudo(**kw):
    base = {'id': 'r1', 'created': '2026-11-12T10:00:00Z', 'focoId': 'J1_soya',
            'focoIdEstable': True, 'estrato': 'ATENCION', 'hacienda': 'HDS',
            'lote': 'J1_soya', 'hallazgo': 'nada', 'registro_a_ciegas': True}
    base.update(kw)
    return base


# --- las tres traducciones que faltaban ---------------------------------------

def test_nada_es_el_registro_negativo_no_un_dato_faltante():
    """'nada' mide los FALSOS POSITIVOS: es la mitad del valor de la campaña."""
    v, _ = lazo.a_validaciones(pd.DataFrame([_crudo(hallazgo='nada')]), verbose=False)
    assert len(v) == 1
    assert v['hubo_problema'].iloc[0] == False


def test_cualquier_hallazgo_distinto_de_nada_es_un_problema():
    v, _ = lazo.a_validaciones(
        pd.DataFrame([_crudo(id='a', focoId='L1', hallazgo='roya'),
                      _crudo(id='b', focoId='L2', hallazgo='Spodoptera')]),
        verbose=False)
    assert list(v['hubo_problema']) == [True, True]


def test_el_foco_id_se_convierte_en_lote_id():
    v, _ = lazo.a_validaciones(pd.DataFrame([_crudo()]), verbose=False)
    assert v['lote_id'].iloc[0] == 'J1_soya'


def test_sin_hallazgo_declarado_no_se_inventa_un_negativo():
    """Un registro sin `hallazgo` no es "no habia nada": es un registro incompleto.
    Contarlo como negativo inflaria la precision del sistema."""
    v, d = lazo.a_validaciones(pd.DataFrame([_crudo(hallazgo=None)]), verbose=False)
    assert len(v) == 0
    assert d['sin_hallazgo_declarado'] == 1


# --- lo que hace que el numero sea rastreable ---------------------------------

def test_un_id_posicional_se_descarta_no_se_adivina():
    """`focoIdEstable=False` significa que la app cayo a ids F-1, F-2..., que se
    renumeran en cada ronda porque el orden de visita se baraja. Ese registro
    apunta a un lote distinto cada semana: meterlo contamina la precision."""
    v, d = lazo.a_validaciones(
        pd.DataFrame([_crudo(focoId='F-3', focoIdEstable=False, hallazgo='roya')]),
        verbose=False)
    assert len(v) == 0
    assert d['sin_id_estable'] == 1


def test_los_descartes_se_cuentan_y_se_declaran():
    v, d = lazo.a_validaciones(pd.DataFrame([
        _crudo(id='a', focoId='L1', hallazgo='roya'),
        _crudo(id='b', focoId='F-2', focoIdEstable=False, hallazgo='roya'),
        _crudo(id='c', focoId=None, lote=None, hallazgo='roya'),
    ]), verbose=False)
    assert len(v) == 1
    assert d['sin_id_estable'] == 1 and d['sin_lote'] == 1


def test_la_tabla_es_append_only_y_gana_el_registro_MAS_NUEVO():
    """El tecnico puede registrar dos veces el mismo lote. La lectura vigente es
    la ultima, no la primera ni una arbitraria."""
    v, _ = lazo.a_validaciones(pd.DataFrame([
        _crudo(id='a', created='2026-11-12T09:00:00Z', hallazgo='nada'),
        _crudo(id='b', created='2026-11-12T15:00:00Z', hallazgo='roya'),
    ]), verbose=False)
    assert len(v) == 1
    assert v['hubo_problema'].iloc[0] == True


def test_sin_registros_devuelve_vacio_con_las_columnas_correctas():
    v, d = lazo.a_validaciones(pd.DataFrame(), verbose=False)
    assert list(v.columns) == ['lote_id', 'hubo_problema']
    assert len(v) == 0


# --- la credencial correcta ---------------------------------------------------

def test_leer_sin_credencial_falla_ruidoso():
    """Una lista vacia por falta de permiso es indistinguible de "no hubo
    validaciones", y esa confusion haria reportar una campaña sin datos en vez de
    un problema de configuracion."""
    with pytest.raises(ValueError, match='service_role'):
        lazo.descargar('', '', desde=None)
    with pytest.raises(ValueError, match='service_role'):
        lazo.descargar('https://x.supabase.co', '', desde=None)


def test_el_mensaje_distingue_la_publica_de_la_secreta():
    """Son credenciales distintas y la confusion es el error esperable: la publica
    es la que el usuario ya tiene a mano, porque va dentro del APK.

    El mensaje tiene que nombrar la clave correcta CON EL ROTULO QUE EL USUARIO VE
    HOY en el panel. Supabase renombro las claves (`sb_publishable_`/`sb_secret_`);
    un mensaje que solo hable de "anon" y "service_role" manda a buscar dos rotulos
    que ya no estan en pantalla."""
    try:
        lazo.descargar('https://x.supabase.co', '', desde=None)
    except ValueError as e:
        m = str(e)
        assert 'PUBLICA' in m and 'SECRETA' in m
        assert 'sb_secret_' in m and 'service_role' in m  # rotulo nuevo Y viejo


# --- auditoria del ciego ------------------------------------------------------

def test_se_puede_auditar_que_fraccion_se_registro_a_ciegas():
    v = pd.DataFrame({'lote_id': ['a', 'b', 'c', 'd'],
                      'hubo_problema': [True] * 4,
                      'registro_a_ciegas': [True, True, False, None]})
    r = lazo.auditar_ciego(v)
    assert r['auditable'] and r['a_ciegas'] == 2 and r['n'] == 4
    assert abs(r['fraccion'] - 0.5) < 1e-9


def test_sin_la_marca_de_ciego_se_declara_que_no_es_auditable():
    r = lazo.auditar_ciego(pd.DataFrame({'lote_id': ['a'], 'hubo_problema': [True]}))
    assert r['auditable'] is False and 'procedimiento' in r['nota']


# --- de punta a punta, sin red ------------------------------------------------

def test_el_lazo_cierra_contra_campana(tmp_path):
    """La prueba que importa: del registro del tecnico al acumulado de campaña."""
    from pix_alerta import campana as cp
    registros = [_crudo(id='r%d' % i, focoId='L%d' % i,
                        hallazgo='roya' if i < 2 else 'nada') for i in range(4)]
    p = tmp_path / 'crudo.json'
    p.write_text(json.dumps(registros), encoding='utf-8')

    muestra = pd.DataFrame({'lote_id': ['L0', 'L1', 'L2', 'L3'],
                            'estrato': ['ATENCION'] * 2 + ['SIN SEÑAL'] * 2,
                            'N_estrato': [4, 4, 100, 100], 'n_estrato': [2, 2, 2, 2],
                            'prob_inclusion': [1.0, 1.0, 0.02, 0.02],
                            'peso_diseño': [1.0, 1.0, 50.0, 50.0],
                            'fecha_dato': ['2026-11-12'] * 4})
    m = tmp_path / 'muestra.csv'
    muestra.to_csv(m, index=False)

    rc = lazo.main(['--sitio', 'HDS', '--ronda', '2026-11-12', '--agregar',
                    '--desde-json', str(p), '--muestra', str(m),
                    '--base', str(tmp_path)])
    assert rc == 0
    acum = cp.cargar(str(tmp_path), 'HDS')
    assert len(acum) == 4
    b = cp._a_booleano(acum.set_index('lote_id')['hubo_problema'])
    assert bool(b['L0']) and bool(b['L1'])
    assert not bool(b['L2']) and not bool(b['L3'])


# --- el rol de la credencial: el fallo que sale HTTP 200 ----------------------

def test_el_rol_se_reconoce_en_los_dos_formatos():
    """Con el formato nuevo el prefijo lo dice; con el legado hay que abrir el JWT."""
    assert lazo.rol_de_clave('sb_publishable_' + 'A' * 20) == 'anon'
    assert lazo.rol_de_clave('sb_secret_' + 'B' * 20) == 'service_role'
    # payload {"role":"anon"} y {"role":"service_role"}
    assert lazo.rol_de_clave(
        'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoiYW5vbiJ9.f') == 'anon'
    assert lazo.rol_de_clave(
        'eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.f') == 'service_role'
    assert lazo.rol_de_clave('cualquier-cosa') is None
    assert lazo.rol_de_clave('') is None


def test_leer_con_la_clave_PUBLICA_falla_antes_de_consultar():
    """EL fallo silencioso del lazo, medido 2026-07-27 contra el proyecto real: con
    la clave publica Supabase responde **HTTP 200 con `[]`**, no 401 — autentica bien
    y RLS simplemente no devuelve filas. O sea que la rama 401/403 NUNCA se dispara
    para el error mas probable, y "no tengo permiso" llegaba indistinguible de "no
    hubo validaciones". Por eso el rol se verifica ANTES de consultar."""
    with pytest.raises(RuntimeError, match='PUBLICA'):
        lazo.descargar('https://x.supabase.co', 'sb_publishable_' + 'A' * 30)


def test_el_descarte_de_ids_posicionales_sobrevive_a_un_csv():
    """`v is False` solo reconoce el booleano nativo; una ida y vuelta por CSV deja
    los strings 'True'/'False' y el descarte se iba a cero SIN AVISAR, contaminando
    la precision acumulada con observaciones mal atribuidas."""
    for valor_malo, valor_bueno in (('False', 'True'), ('false', 'true'),
                                    (False, True)):
        v, d = lazo.a_validaciones(pd.DataFrame([
            _crudo(id='a', focoId='L1', focoIdEstable=valor_bueno, hallazgo='roya'),
            _crudo(id='b', focoId='F-2', focoIdEstable=valor_malo, hallazgo='roya'),
        ]), verbose=False)
        assert d['sin_id_estable'] == 1, 'no descarto con %r' % valor_malo
        assert list(v['lote_id']) == ['L1']
