"""Puertas del ciclo de cultivo y de la ficha de cliente.

La ventana de monitoreo decide en que fechas el motor emite. Si sale mal, o el
cliente no recibe nada durante media campaña, o recibe un rojo en plena cosecha
que es senescencia normal.
"""
import json
import os
import tempfile

import pytest

from pix_alerta import ciclos
from pix_alerta import clientes as cl


# --- ventana derivada de la siembra -------------------------------------------

def test_la_ventana_arranca_el_dia_de_la_siembra():
    """El estimador de cohorte necesita ver la emergencia: recortar el inicio dejo
    188 de 207 lotes sin ciclo."""
    ini, _ = ciclos.ventana('soya', '2025-10-15')
    assert ini == '2025-10-15'


def test_la_ventana_termina_al_cerrar_el_ciclo():
    """Sin cablear el numero: lo que se fija es que el fin sale de la TABLA, no que
    la tabla diga 140. El valor operativo cambio a 95 el 2026-07-27 (extremo corto
    del rango) y un test que congela la constante convierte una decision agronomica
    en un test roto."""
    from datetime import date, timedelta
    dias = ciclos.CICLOS['soya'][0]
    ini, fin = ciclos.ventana('soya', '2025-10-15')
    esperado = date(2025, 10, 15) + timedelta(days=dias + ciclos.MARGEN_FIN_DIAS)
    assert fin == esperado.isoformat()


def test_el_operativo_es_el_extremo_CORTO_del_rango_observado():
    """Pasarse de la madurez no agrega fechas inocuas: NDMI y NDRE bajando a la vez
    ES la firma de senescencia, o sea el criterio de foco. Una cosecha parcial da un
    "foco" garantizado de decenas de hectareas. Errar corto pierde el final del
    ciclo; errar largo INVENTA alertas. No es simetrico."""
    for cultivo, (oper, (lo, hi), _n) in ciclos.CICLOS.items():
        if lo == hi:                      # perenne: no hay extremo que elegir
            continue
        assert oper == lo, (
            '%s declara %d dias operativos sobre un rango (%d, %d): el operativo '
            'tiene que ser el extremo corto' % (cultivo, oper, lo, hi))


def test_el_ciclo_declarado_por_sitio_le_gana_al_de_la_tabla():
    """El cultivar lo sabe el cliente; la tabla es solo un default operativo."""
    _, fin_def = ciclos.ventana('soya', '2025-10-15')
    _, fin_ovr = ciclos.ventana('soya', '2025-10-15', override=200)
    assert fin_ovr > fin_def
    assert fin_ovr == '2026-05-03'


def test_cultivo_desconocido_falla_ruidoso():
    with pytest.raises(ValueError, match='desconocido'):
        ciclos.ventana('quinua', '2025-10-15')


def test_ciclo_absurdo_se_rechaza():
    with pytest.raises(ValueError):
        ciclos.ventana('soya', '2025-10-15', override=5)


def test_la_etiqueta_de_campana_cruza_el_anio_cuando_corresponde():
    assert ciclos.etiqueta_campana('soya', '2025-10-15') == '2025/2026'
    assert ciclos.etiqueta_campana('trigo', '2026-05-01') == '2026'


def test_todos_los_cultivos_de_la_app_tienen_ciclo():
    """Si un cultivo esta en el selector y no en la tabla, el alta revienta."""
    from pix_alerta.alta_cliente import CULTIVOS
    faltan = [c for c in CULTIVOS if c not in ciclos.CICLOS]
    assert not faltan, 'sin ciclo declarado: %s' % faltan


def test_el_operativo_cae_dentro_del_rango_observado():
    for c, (op, (lo, hi), _) in ciclos.CICLOS.items():
        assert lo <= op <= hi, '%s: operativo %d fuera de (%d, %d)' % (c, op, lo, hi)


def test_avisa_cuando_el_ciclo_no_se_puede_dar_por_defecto():
    """Caña planta y soca no comparten ciclo: callarlo seria inventar la ventana."""
    txt = ciclos.describir('cana_de_azucar', '2025-06-01')
    assert 'declararlo por sitio' in txt
    assert 'declararlo por sitio' not in ciclos.describir('soya', '2025-10-15')


def test_dias_restantes_negativos_si_la_campana_cerro():
    assert ciclos.dias_restantes('soya', '2025-10-15', hoy='2026-07-26') < 0
    assert ciclos.dias_restantes('soya', '2025-10-15', hoy='2025-12-01') > 0


# --- la ficha del cliente -----------------------------------------------------

def _cliente(tmp, **kw):
    d = {'clave': 'TEST', 'titulo': 'Prueba',
         'sitios': [{'clave': 'S1', 'titulo': 'Sitio 1',
                     'lotes_geojson': 'x.geojson', 'campo_id': 'lote'}]}
    d.update(kw)
    ruta = os.path.join(tmp, 'TEST.json')
    with open(ruta, 'w', encoding='utf-8') as fh:
        json.dump(d, fh)
    return ruta


def test_la_ventana_se_deriva_de_la_siembra_en_el_json():
    with tempfile.TemporaryDirectory() as t:
        r = _cliente(t, sitios=[{'clave': 'S1', 'titulo': 'Sitio 1',
                                 'lotes_geojson': 'x.geojson', 'campo_id': 'lote',
                                 'cultivo': 'soya', 'siembra': '2025-10-15'}])
        c = cl.cargar(r)
        assert c.sitios[0].campanas == {
        '2025/2026': ('2025-10-15', ciclos.ventana('soya', '2025-10-15')[1])}


def test_una_campana_escrita_a_mano_le_gana_a_la_derivada():
    """Puede reflejar algo que el cliente sabe y la tabla de ciclos no."""
    with tempfile.TemporaryDirectory() as t:
        r = _cliente(t, sitios=[{'clave': 'S1', 'titulo': 'Sitio 1',
                                 'lotes_geojson': 'x.geojson', 'campo_id': 'lote',
                                 'cultivo': 'soya', 'siembra': '2025-10-15',
                                 'campanas': {'2025/2026': ['2025-11-01',
                                                            '2026-02-01']}}])
        c = cl.cargar(r)
        assert c.sitios[0].campanas['2025/2026'] == ('2025-11-01', '2026-02-01')


def test_siembra_sin_cultivo_no_puede_derivar_nada():
    with tempfile.TemporaryDirectory() as t:
        r = _cliente(t, sitios=[{'clave': 'S1', 'titulo': 'Sitio 1',
                                 'lotes_geojson': 'x.geojson', 'campo_id': 'lote',
                                 'siembra': '2025-10-15'}])
        with pytest.raises(ValueError, match='cultivo'):
            cl.cargar(r)


def test_el_whatsapp_del_cliente_llega_al_objeto():
    with tempfile.TemporaryDirectory() as t:
        r = _cliente(t, contacto={'nombre': 'Marcelo',
                                  'whatsapp': '+591 7000-0000'})
        c = cl.cargar(r)
        assert c.whatsapp == '+59170000000'      # normalizado
        assert c.contacto['nombre'] == 'Marcelo'


def test_sin_contacto_el_whatsapp_es_none_y_no_revienta():
    with tempfile.TemporaryDirectory() as t:
        assert cl.cargar(_cliente(t)).whatsapp is None


def test_un_typo_en_contacto_no_pasa_callado():
    """'wathsapp' dejaria al cliente sin aviso y sin error."""
    with tempfile.TemporaryDirectory() as t:
        r = _cliente(t, contacto={'wathsapp': '+59170000000'})
        with pytest.raises(ValueError, match='desconocidos'):
            cl.cargar(r)


def test_un_whatsapp_que_no_es_numero_se_rechaza():
    with tempfile.TemporaryDirectory() as t:
        r = _cliente(t, contacto={'whatsapp': 'mandale por el grupo'})
        with pytest.raises(ValueError, match='formato internacional'):
            cl.cargar(r)
