"""Puertas del acercamiento intra-lote.

Lo que se prueba aca es la logica que decide QUE par de fechas se compara y COMO
sale el entregable — no el algebra de bandas, que vive en Earth Engine. Esa parte
la cubre `focos.control_nulo()` corriendo contra datos reales.

El par de fechas es lo mas delicado del modulo: si la referencia se elige mal, el
porcentaje que se le entrega al cliente mide otra cosa (fenologia, no daño).
"""
import pytest

from pix_alerta import focos as fc


# --- eleccion del par (actual, referencia) ------------------------------------

def _esc(*trios):
    """Atajo: ('2026-01-10', 'idx', 0.95) -> tupla de escena."""
    return list(trios)


def test_toma_las_dos_limpias_mas_recientes():
    esc = _esc(('2026-01-01', 'a', 0.95), ('2026-01-11', 'b', 0.92),
               ('2026-01-21', 'c', 0.90))
    act, ref = fc._par_de_fechas(esc, '2026-01-31')
    assert act[0] == '2026-01-21'
    assert ref[0] == '2026-01-11'


def test_descarta_escenas_por_debajo_de_cobertura_plena():
    """Una escena parcial no puede ser referencia: el delta mediria la nube."""
    esc = _esc(('2026-01-01', 'a', 0.95), ('2026-01-11', 'b', 0.30),
               ('2026-01-21', 'c', 0.90))
    act, ref = fc._par_de_fechas(esc, '2026-01-31')
    assert act[0] == '2026-01-21'
    assert ref[0] == '2026-01-01'      # salteo la del 11, que era parcial


def test_ignora_escenas_posteriores_al_corte():
    """El informe del 15 no puede usar una imagen del 20: seria mirar el futuro."""
    esc = _esc(('2026-01-01', 'a', 0.95), ('2026-01-11', 'b', 0.93),
               ('2026-01-25', 'c', 0.99))
    act, _ = fc._par_de_fechas(esc, '2026-01-15')
    assert act[0] == '2026-01-11'


def test_rechaza_referencia_demasiado_pegada():
    """Por debajo de la revisita no hay dos observaciones independientes."""
    esc = _esc(('2026-01-10', 'a', 0.95), ('2026-01-12', 'b', 0.95))
    with pytest.raises(fc.SinPar):
        fc._par_de_fechas(esc, '2026-01-31')


def test_rechaza_referencia_demasiado_vieja():
    """Mas alla de la ventana se compara contra otra fenologia, no contra el lote."""
    esc = _esc(('2026-01-01', 'a', 0.95), ('2026-03-20', 'b', 0.95))
    with pytest.raises(fc.SinPar):
        fc._par_de_fechas(esc, '2026-03-31')


def test_sin_dos_escenas_limpias_no_inventa_par():
    esc = _esc(('2026-01-21', 'c', 0.90))
    with pytest.raises(fc.SinPar):
        fc._par_de_fechas(esc, '2026-01-31')


def test_elige_la_referencia_mas_cercana_dentro_de_la_ventana():
    """Entre dos candidatas validas gana la mas proxima: menos deriva fenologica."""
    esc = _esc(('2026-01-05', 'a', 0.95), ('2026-01-20', 'b', 0.95),
               ('2026-01-30', 'c', 0.95))
    act, ref = fc._par_de_fechas(esc, '2026-02-01')
    assert (act[0], ref[0]) == ('2026-01-30', '2026-01-20')


# --- entregable para la app ---------------------------------------------------

class _Sitio:
    clave = 'TEST'
    titulo = 'Hacienda de Prueba'
    cultivo = 'soya'


def _resultado(lote='J1', z=-3.4, area=1.5, pct=3.0):
    return {lote: {
        'lote_id': lote, 'area_focos_ha': area, 'pct_lote': pct,
        'fecha_img': '2026-01-21', 'fecha_ref': '2026-01-11', 'nota': None,
        'focos': [{
            'type': 'Feature',
            'geometry': {'type': 'Polygon',
                         'coordinates': [[[0, 0], [0, 1], [1, 1], [0, 0]]]},
            'properties': {'id': '%s-F1' % lote, 'etiqueta': 'F1',
                           'lote_id': lote, 'orden': 1, 'area_ha': area,
                           'pct_lote': pct, 'z_sev': z, 'z_ndmi': z, 'z_ndre': -2.8,
                           'fecha_img': '2026-01-21', 'fecha_ref': '2026-01-11',
                           'status': 'pending'}}]}}


def test_el_perimetro_va_primero_y_no_es_un_foco():
    """La app lo usa de marco; si lo listara como foco mandaria al tecnico al borde."""
    per = {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 2], [2, 2], [0, 0]]]}
    gj = fc.a_geojson(_Sitio(), _resultado(), perimetro=per)
    assert gj['features'][0]['properties']['tipo'] == 'perimetro'
    assert all(f['properties'].get('tipo') != 'perimetro'
               for f in gj['features'][1:])


def test_sin_perimetro_igual_entrega_los_focos():
    """Falta de marco es degradacion, no motivo para no entregar."""
    gj = fc.a_geojson(_Sitio(), _resultado())
    assert len(gj['features']) == 1
    assert gj['features'][0]['properties']['etiqueta'] == 'F1'


def test_lleva_los_campos_que_la_app_necesita_para_el_lazo():
    """`id` y `lote_id` anclan la validacion: sin ellos no hay precision medible."""
    gj = fc.a_geojson(_Sitio(), _resultado())
    p = gj['features'][0]['properties']
    for campo in ('id', 'lote_id', 'etiqueta', 'hacienda', 'cultivo',
                  'sev', 'area_ha', 'pct_lote', 'fecha_img', 'status'):
        assert campo in p, 'falta %s: la app lo lee' % campo
    assert p['hacienda'] == 'Hacienda de Prueba'
    assert p['cultivo'] == 'soya'
    assert p['status'] == 'pending'


def test_severidad_alta_solo_con_apartamiento_grande():
    alta = fc.a_geojson(_Sitio(), _resultado(z=-3.4))
    media = fc.a_geojson(_Sitio(), _resultado(z=-2.2))
    assert alta['features'][0]['properties']['sev'] == 'alta'
    assert media['features'][0]['properties']['sev'] == 'media'


def test_un_lote_sin_focos_no_aporta_features():
    """'Sin focos' es un resultado valido y tiene que poder viajar vacio."""
    r = {'J2': {'lote_id': 'J2', 'focos': [], 'area_focos_ha': 0.0,
                'pct_lote': 0.0, 'fecha_img': '2026-01-21',
                'fecha_ref': '2026-01-11', 'nota': 'Sin focos sobre la MMU.'}}
    gj = fc.a_geojson(_Sitio(), r)
    assert gj['features'] == []


def test_ids_de_foco_unicos_entre_lotes():
    """Dos lotes distintos no pueden emitir el mismo id o el lazo se cruza."""
    r = {}
    r.update(_resultado('J1'))
    r.update(_resultado('J2'))
    gj = fc.a_geojson(_Sitio(), r)
    ids = [f['properties']['id'] for f in gj['features']]
    assert len(ids) == len(set(ids))


# --- parametros declarados ----------------------------------------------------

def test_la_conjuncion_es_mas_exigente_que_un_corte_simple():
    """Justifica el AND. OJO: el alfa^2 es la COTA OPTIMISTA, no la real.

    Medido sobre HDS, los residuos de los dos ejes correlacionan entre 0,79 y 0,90,
    asi que la conjuncion filtra MENOS que bajo independencia. La tasa verdadera la
    mide `focos.control_nulo`; esta prueba solo fija que el AND es estrictamente mas
    exigente que un corte simple, que es lo unico deducible sin medir.
    """
    from math import erf, sqrt
    phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
    corte_simple = phi(-1.3)
    una_cola = phi(-fc.Z_FOCO)
    assert corte_simple > 0.09
    assert una_cola < corte_simple      # ya un solo eje a 2 sigma es mas exigente


def test_la_referencia_nunca_es_la_media_de_la_temporada():
    """Regla medida: la media de temporada infla el area marcada varias veces."""
    assert fc.MAX_REF_DIAS <= 60
    assert fc.MIN_GAP_DIAS >= 5


def test_la_mmu_descarta_focos_de_uno_o_dos_pixeles():
    """A 20 m un pixel son 0,04 ha: la MMU tiene que pedir varios conectados."""
    px_ha = (fc.ESCALA ** 2) / 1e4
    assert fc.MMU_HA / px_ha >= 4


# --- el entregable nuevo entra al chequeo de aislamiento ----------------------

def test_los_focos_y_el_informe_no_escapan_al_chequeo_de_aislamiento():
    """Un prefijo que falta no da error: el archivo simplemente deja de mirarse, y
    un entregable en la carpeta del cliente equivocado pasa sin que nadie lo vea.
    Le paso a `focos_` al sumarse el acercamiento y a `Informe_` desde siempre."""
    from pix_alerta.correr_todos import sitio_de_archivo as f
    assert f('focos_HDS_2026-01-31.geojson') == 'HDS'
    assert f('Informe_HDS_2026-01-31.pdf') == 'HDS'
    # y sigue sin confundirse con claves que llevan guion bajo
    assert f('focos_TEST_A_2026-04-30.geojson') == 'TEST_A'
    # lo que no es entregable del motor se ignora, no se inventa un sitio
    assert f('TABLERO.html') is None
