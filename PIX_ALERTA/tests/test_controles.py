# -*- coding: utf-8 -*-
"""El punto de control tiene que ser INDISTINGUIBLE del foco, y la clave no viaja.

Si el tecnico puede saber cual punto marco el motor, la validacion mide su expectativa
y no el motor. Es el unico requisito duro de este modulo, y por eso casi todo lo que se
prueba aca es eso.
"""
import json

import pytest

from pix_alerta import controles as ct


class _Sitio:
    clave = 'X'
    titulo = 'Campo de prueba'
    campo_id = 'lote'
    campo_area = 'area_ha'
    cultivo = 'trigo'


def _foco(lote='L1', i=1, z=-3.9):
    """Un foco tal como lo emite `focos.detectar_lote`, con todo lo que revela."""
    return {'type': 'Feature',
            'geometry': {'type': 'Polygon',
                         'coordinates': [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
            'properties': {'id': '%s-F%d' % (lote, i), 'etiqueta': 'F%d' % i,
                           'lote_id': lote, 'orden': i, 'area_ha': 0.44,
                           'z_sev': z, 'z_ndmi': z, 'z_ndre': z - 0.2,
                           'sev': 'alta', 'nivel': 'ATENCION', 'SI': 0.71,
                           'pct_util': 2.19, 'fecha_img': '2026-07-15',
                           'status': 'pending'}}


def _control(lote='L1', i=1):
    return {'type': 'Feature',
            'geometry': {'type': 'Polygon',
                         'coordinates': [[[2, 2], [2, 3], [3, 3], [2, 2]]]},
            'properties': {'lote_id': lote, 'orden': i, 'area_ha': 0.2,
                           'radio_m': 25.2, 'fecha_img': '2026-07-15'}}


def _paquete(n_focos=2, n_ctrl=2):
    return ct.paquete_ciego(
        _Sitio(),
        {'L1': {'focos': [_foco(i=i + 1) for i in range(n_focos)]}},
        {'L1': {'controles': [_control(i=i + 1) for i in range(n_ctrl)]}},
        '2026-07-16')


# --- el ciego -----------------------------------------------------------------

def test_ninguna_propiedad_del_paquete_revela_la_severidad():
    """La app muestra la ficha con lo que venga en `properties`. Si sobrevive `z_sev`,
    `sev` o `nivel`, alcanza con apagar MODO_CIEGO —o con abrir el archivo— para saber
    cual punto marco el motor."""
    gj, _ = _paquete()
    for f in gj['features']:
        p = f['properties']
        if p.get('tipo') == 'perimetro':
            continue
        for k in ct.CAMPOS_QUE_REVELAN:
            if k in ('etiqueta', 'id', 'orden'):
                continue          # se reescriben neutros, se prueban aparte
            assert k not in p, 'sobrevivio %r y revela la clase o la severidad' % k
        assert not [k for k in p if k.startswith('z_')], p


def test_la_etiqueta_no_dice_si_es_foco_o_control():
    """La app muestra `etiqueta` en la ficha (`lote: props.lote || props.etiqueta`).
    Un `F1` junto a un `C1` delata la clase sin que nadie lo note."""
    gj, _ = _paquete()
    etqs = [f['properties']['etiqueta'] for f in gj['features']
            if f['properties'].get('tipo') != 'perimetro']
    assert all(e.startswith('P') for e in etqs), etqs
    assert len(set(etqs)) == len(etqs), 'etiquetas repetidas: no serian rastreables'


def test_el_id_tampoco_lo_dice_y_sigue_siendo_estable():
    """Sin id estable el registro del tecnico no se puede atribuir. Pero el id no puede
    llevar la clase adentro."""
    gj, clave = _paquete()
    ids = [f['properties']['id'] for f in gj['features']
           if f['properties'].get('tipo') != 'perimetro']
    assert all('-P' in i for i in ids)
    assert not [i for i in ids if '-F' in i or '-C' in i]
    assert set(ids) == set(clave['puntos']), 'la clave no cubre todos los puntos'


def test_focos_y_controles_quedan_mezclados_y_no_en_bloques():
    """Si los focos salen todos primero y los controles despues, el orden de recorrida
    delata la clase igual que una etiqueta."""
    gj, clave = _paquete(n_focos=4, n_ctrl=4)
    orden = [clave['puntos'][f['properties']['id']]['clase']
             for f in gj['features']
             if f['properties'].get('tipo') != 'perimetro']
    assert set(orden) == {'foco', 'control'}
    # Con 4 y 4, quedar perfectamente separados en dos bloques seria sospechoso.
    bloques = sum(1 for a, b in zip(orden, orden[1:]) if a != b)
    assert bloques >= 2, 'los puntos salieron casi en bloques por clase: %s' % orden


def test_el_orden_es_reproducible():
    """Dos corridas del mismo dia tienen que mandar al tecnico a los mismos puntos con
    los mismos rotulos, o el experimento no se puede rehacer ni auditar."""
    a, ca = _paquete()
    b, cb = _paquete()
    assert [f['properties']['id'] for f in a['features']] == \
           [f['properties']['id'] for f in b['features']]
    assert ca['puntos'] == cb['puntos']


def test_la_clave_y_el_paquete_se_guardan_en_archivos_distintos(tmp_path):
    """Si viajaran juntos, alcanzaria con abrir el archivo del telefono."""
    gj, clave = _paquete()
    f_gj, f_cl = ct.guardar(str(tmp_path), _Sitio(), '2026-07-16', gj, clave)
    assert f_gj != f_cl
    crudo = open(f_gj, encoding='utf-8').read()
    assert 'control' not in crudo.lower(), 'el paquete de campo menciona la clase'
    assert 'foco' not in crudo.lower()
    assert 'clase' in json.dumps(json.load(open(f_cl, encoding='utf-8')))


def test_el_paquete_declara_que_es_una_ronda_de_validacion():
    """El tecnico tiene que poder distinguir un archivo de validacion de una entrega
    normal — eso NO rompe el ciego, y evita que lo cargue por error."""
    gj, _ = _paquete()
    p = [f['properties'] for f in gj['features']
         if f['properties'].get('tipo') != 'perimetro'][0]
    assert p['campana_validacion'] is True


# --- el analisis --------------------------------------------------------------

def _reg(pid, hallazgo, estable=True, ciegas=True):
    return {'focoId': pid, 'hallazgo': hallazgo, 'focoIdEstable': estable,
            'registro_a_ciegas': ciegas}


def test_no_concluye_con_pocas_observaciones():
    """Con 2 controles no hay nada que decir. Decirlo igual es peor que callarse."""
    _, clave = _paquete()
    ids = list(clave['puntos'])
    r = ct.analizar([clave], [_reg(i, 'roya') for i in ids])
    assert r['concluyente'] is False
    assert 'no se puede concluir' in r['aviso']


def test_descarta_el_registro_que_destapo_la_severidad():
    """La app anota `registro_a_ciegas`. Si el tecnico vio el nivel antes de anotar, el
    ciego se rompio para ese punto y no puede entrar."""
    _, clave = _paquete()
    ids = list(clave['puntos'])
    r = ct.analizar([clave], [_reg(ids[0], 'roya', ciegas=False)])
    assert r['descartes']['destapo_la_severidad'] == 1
    assert r['foco']['n'] + r['control']['n'] == 0


def test_descarta_el_id_posicional():
    """Un id no estable apunta a un punto distinto en cada ronda."""
    _, clave = _paquete()
    ids = list(clave['puntos'])
    r = ct.analizar([clave], [_reg(ids[0], 'roya', estable=False)])
    assert r['descartes']['sin_id_estable'] == 1


def test_un_id_que_no_esta_en_la_clave_no_se_adivina():
    r = ct.analizar([_paquete()[1]], [_reg('OTRO-LOTE-P99', 'roya')])
    assert r['descartes']['id_desconocido'] == 1


def test_avisa_cuando_el_motor_no_supera_al_azar():
    """Es la prueba que el motor PUEDE FALLAR, y por eso vale. Si encontrar algo en un
    foco no es mas probable que en un punto al azar, el motor no agrega nada."""
    _, clave = _paquete(n_focos=6, n_ctrl=6)
    focos = [i for i, d in clave['puntos'].items() if d['clase'] == 'foco']
    ctrls = [i for i, d in clave['puntos'].items() if d['clase'] == 'control']
    # mismo hallazgo en los dos grupos: el motor no discrimina
    regs = ([_reg(i, 'roya') for i in focos[:3]] +
            [_reg(i, 'nada') for i in focos[3:]] +
            [_reg(i, 'roya') for i in ctrls[:3]] +
            [_reg(i, 'nada') for i in ctrls[3:]])
    r = ct.analizar([clave], regs)
    assert r['concluyente'] is True
    assert r['supera_al_azar'] is False
    assert 'NO supera' in r['aviso']


def test_cuenta_bien_cuando_el_motor_si_discrimina():
    _, clave = _paquete(n_focos=6, n_ctrl=6)
    focos = [i for i, d in clave['puntos'].items() if d['clase'] == 'foco']
    ctrls = [i for i, d in clave['puntos'].items() if d['clase'] == 'control']
    regs = ([_reg(i, 'roya') for i in focos] +
            [_reg(i, 'nada') for i in ctrls])
    r = ct.analizar([clave], regs)
    assert r['foco']['tasa'] == 1.0 and r['control']['tasa'] == 0.0
    assert r['supera_al_azar'] is True
    # el IC de Wilson con n=6 NO puede salir de ancho cero
    lo, hi = r['foco']['ic95']
    assert hi - lo > 0.2, 'un IC angosto con n=6 seria falso'


def test_acumula_varias_rondas():
    """El valor es acumulativo: una ronda sola no alcanza y el modulo lo dice."""
    _, c1 = _paquete(n_focos=3, n_ctrl=3)
    gj2, c2 = ct.paquete_ciego(
        _Sitio(), {'L1': {'focos': [_foco(i=i + 1) for i in range(3)]}},
        {'L1': {'controles': [_control(i=i + 1) for i in range(3)]}}, '2026-07-23')
    ids1 = list(c1['puntos'])
    ids2 = list(c2['puntos'])
    r = ct.analizar([c1, c2], [_reg(i, 'nada') for i in ids1 + ids2])
    assert r['foco']['n'] == 6 and r['control']['n'] == 6


# --- el modulo declara sus limites -------------------------------------------

def _plano(t):
    return ' '.join((t or '').split())


def test_declara_por_que_no_se_parean_por_vigor():
    d = _plano(ct.__doc__)
    assert 'sensibilidad aparente' in d.lower() or 'REPRESENTATIVA' in d


def test_declara_que_el_valor_es_acumulativo_y_que_cuesta_caminar():
    d = _plano(ct.__doc__)
    assert 'ACUMULATIVO' in d
    assert 'camina' in d.lower(), 'no declara el costo para el tecnico'


def test_declara_que_no_es_sensibilidad_en_sentido_estricto():
    d = _plano(ct.analizar.__doc__)
    assert 'no es sensibilidad en sentido estricto' in d.lower()


# --- fugas encontradas MIRANDO LA SALIDA REAL, no razonando -------------------

def test_todos_los_puntos_tienen_EL_MISMO_conjunto_de_campos():
    """FUGA REAL del 2026-07-16: el control llevaba `radio_m` y el foco no. Ningun
    campo decia nada por si mismo, pero el CONJUNTO de campos delataba la clase. Una
    lista negra no protege de eso: hay que enumerar lo que viaja."""
    gj, _ = _paquete(n_focos=2, n_ctrl=3)
    juegos = {tuple(sorted(f['properties']))
              for f in gj['features'] if f['properties'].get('tipo') != 'perimetro'}
    assert len(juegos) == 1, 'los puntos no tienen el mismo conjunto de campos: %s' % juegos
    assert set(juegos.pop()) == set(ct.CAMPOS_DEL_PUNTO)


def test_ningun_campo_fuera_de_la_lista_blanca_llega_al_telefono():
    """El foco trae `pct_util`, `ejes`, `fecha_ref`... Si alguno pasa y el control no
    lo tiene, vuelve la fuga por conjunto de campos."""
    f = _foco()
    f['properties'].update({'pct_util': 2.19, 'ejes': 'NDMI+NDRE',
                            'fecha_ref': 'trayectoria', 'inventado': 1})
    gj, _ = ct.paquete_ciego(_Sitio(), {'L1': {'focos': [f]}},
                             {'L1': {'controles': [_control()]}}, '2026-07-16')
    for feat in gj['features']:
        if feat['properties'].get('tipo') == 'perimetro':
            continue
        assert set(feat['properties']) == set(ct.CAMPOS_DEL_PUNTO)


def test_el_area_del_control_sale_de_las_areas_de_los_focos():
    """FUGA REAL: los 4 controles median 0,20 ha y el unico foco 0,441 ha. La app
    muestra `area_ha`, asi que el distinto ERA el foco.

    Y ademas es lo correcto por otra razon: la probabilidad de encontrar algo crece
    con el area recorrida, asi que controles mas chicos sesgan a favor del motor.
    """
    import inspect
    fuente = inspect.getsource(ct.controles_lote)
    assert 'areas_foco' in inspect.signature(ct.controles_lote).parameters
    assert 'areas[i % len(areas)]' in fuente, (
        'el area del control no se toma del conjunto de areas de los focos')


def test_el_area_no_puede_delatar_cuando_hay_focos_de_areas_distintas():
    """Simulacion del caso real: si los controles copian las areas de los focos, el
    conjunto de areas del paquete no separa las dos clases."""
    focos = [_foco(i=1), _foco(i=2)]
    focos[0]['properties']['area_ha'] = 0.44
    focos[1]['properties']['area_ha'] = 0.81
    ctrls = [dict(_control(i=1)), dict(_control(i=2))]
    ctrls[0]['properties'] = dict(ctrls[0]['properties'], area_ha=0.44)
    ctrls[1]['properties'] = dict(ctrls[1]['properties'], area_ha=0.81)
    gj, clave = ct.paquete_ciego(_Sitio(), {'L1': {'focos': focos}},
                                 {'L1': {'controles': ctrls}}, '2026-07-16')
    por_clase = {'foco': set(), 'control': set()}
    for f in gj['features']:
        p = f['properties']
        if p.get('tipo') == 'perimetro':
            continue
        por_clase[clave['puntos'][p['id']]['clase']].add(p['area_ha'])
    assert por_clase['foco'] == por_clase['control'], (
        'el conjunto de areas separa focos de controles: %s' % por_clase)


# --- la GEOMETRIA, que es la tercera fuga (hallada 2026-08-03) ----------------

def _foco_irregular(lote='L1', i=1, area=0.28):
    """Un foco como los que emite de verdad `focos.detectar_lote`: poligono
    vectorizado del raster, forma irregular y numero de vertices arbitrario.

    Los fixtures de arriba usan un triangulo IDENTICO para foco y control, y por eso
    ningun test detectaba la fuga: en la salida real las formas son distintas.
    """
    anillo = [[0.0, 0.0], [0.0007, 0.0002], [0.0009, 0.0011], [0.0004, 0.0016],
              [-0.0002, 0.0013], [-0.0005, 0.0006], [0.0, 0.0]]
    f = _foco(lote=lote, i=i)
    f['geometry'] = {'type': 'Polygon', 'coordinates': [anillo]}
    f['properties']['area_ha'] = area
    return f


def _control_circular(lote='L1', i=1, area=0.28):
    """Un control como los que emite de verdad `controles`: circulo de 24 lados."""
    c = _control(lote=lote, i=i)
    c['geometry'] = ct._circulo(0.01, 0.01, ct._radio_m(area))
    c['properties']['area_ha'] = area
    return c


def _vertices(geom):
    g = geom or {}
    if g.get('type') == 'Polygon':
        return len(g['coordinates'][0])
    if g.get('type') == 'MultiPolygon':
        return len(g['coordinates'][0][0])
    return 1


def test_la_forma_del_poligono_no_puede_delatar_la_clase():
    """LA TERCERA FUGA DEL CIEGO, hallada revisando la salida real del 2026-08-03.

    MEDIDO en `validacion_SAO_FRANCISCO_2026-08-03.geojson`: el foco tenia 15 vertices
    y los cuatro controles tenian 25, porque los controles son circulos generados y los
    focos son poligonos vectorizados del raster.

    Y `PIX_SCOUT/app/js/map.js` DIBUJA ese anillo. El tecnico veia circulos perfectos y
    una mancha irregular: despues de una ronda sabe cual es cual sin la clave.
    """
    focos = [_foco_irregular(i=1)]
    ctrls = [_control_circular(i=1), _control_circular(i=2)]
    gj, clave = ct.paquete_ciego(_Sitio(), {'L1': {'focos': focos}},
                                 {'L1': {'controles': ctrls}}, '2026-07-16')
    por_clase = {'foco': set(), 'control': set()}
    for f in gj['features']:
        p = f['properties']
        if p.get('tipo') == 'perimetro':
            continue
        por_clase[clave['puntos'][p['id']]['clase']].add(_vertices(f['geometry']))
    assert por_clase['foco'] == por_clase['control'], (
        'el numero de vertices separa focos de controles: %s' % por_clase)


def test_todos_los_puntos_del_paquete_tienen_la_misma_forma():
    """Defensa mas fuerte que la anterior: no alcanza con que las clases coincidan,
    TODOS los puntos tienen que ser el mismo tipo de figura. Si un dia hay un solo foco
    y un solo control, dos conjuntos de un elemento coinciden por casualidad."""
    gj, _ = ct.paquete_ciego(
        _Sitio(),
        {'L1': {'focos': [_foco_irregular(i=1, area=0.28),
                          _foco_irregular(i=2, area=0.55)]}},
        {'L1': {'controles': [_control_circular(i=1, area=0.28)]}},
        '2026-07-16')
    v = [_vertices(f['geometry']) for f in gj['features']
         if f['properties'].get('tipo') != 'perimetro']
    assert len(set(v)) == 1, 'los puntos no tienen todos la misma forma: %s' % v


def test_el_punto_uniforme_sigue_cayendo_donde_estaba_el_foco():
    """El ciego no puede costar la ubicacion: el circulo tiene que quedar SOBRE la
    mancha original, o el tecnico camina a otro lado."""
    f = _foco_irregular(i=1, area=0.28)
    gj, clave = ct.paquete_ciego(_Sitio(), {'L1': {'focos': [f]}},
                                 {'L1': {'controles': []}}, '2026-07-16')
    pt = [x for x in gj['features']
          if x['properties'].get('tipo') != 'perimetro'][0]
    cx, cy = ct._centroide(pt['geometry'])
    ox, oy = ct._centroide(f['geometry'])
    # A esta latitud 1e-4 grados son ~11 m; el foco mide decenas de metros.
    assert abs(cx - ox) < 1e-4 and abs(cy - oy) < 1e-4, (
        'el punto uniforme se corrio del foco original')


def test_el_radio_del_circulo_respeta_el_area_declarada():
    """Si el area viaja en `properties`, la figura tiene que ser coherente con ella:
    un circulo cuyo radio no corresponda al area declarada es otra fuga."""
    area = 0.28
    f = _foco_irregular(i=1, area=area)
    gj, _ = ct.paquete_ciego(_Sitio(), {'L1': {'focos': [f]}},
                             {'L1': {'controles': []}}, '2026-07-16')
    pt = [x for x in gj['features']
          if x['properties'].get('tipo') != 'perimetro'][0]
    anillo = pt['geometry']['coordinates'][0]
    cx, cy = ct._centroide(pt['geometry'])
    import math
    r_grados = max(abs(p[1] - cy) for p in anillo)
    r_m = r_grados * 111320.0
    assert r_m == pytest.approx(ct._radio_m(area), rel=0.05)
