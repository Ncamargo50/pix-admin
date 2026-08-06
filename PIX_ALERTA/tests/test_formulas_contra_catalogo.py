# -*- coding: utf-8 -*-
"""Las formulas del motor, verificadas contra un catalogo externo con DOI.

POR QUE ESTE ARCHIVO EXISTE
---------------------------
Este repositorio tiene un historial de formulas mal citadas, y ninguna la encontro una
revision de codigo — todas aparecieron mirando el resultado:

  · el "NDWI de Gao" que Sentinel-2 **no puede calcular** (Gao usa 1240 nm, y S2 no tiene
    esa banda). Se citaba Gao para lo que en realidad es NDII/NDMI.
  · el PSRI construido con B3 cuando Merzlyak pide 500 nm, que cae en **B2**.
  · el REIP con 700+40 en vez de 705+35.

Una formula mal citada no falla: devuelve un numero plausible que nadie puede refutar sin
volver al paper original. Es el modo de falla mas caro que tiene este proyecto.

EL CATALOGO
-----------
`awesome-spectral-indices` (github.com/awesome-spectral-indices/awesome-spectral-indices),
1.154 estrellas, publicado como paper:

    Montero, D. et al. (2023). "A standardized catalogue of spectral indices to advance
    the use of remote sensing in Earth system research". Scientific Data.
    DOI 10.1038/s41597-023-02096-0

280 indices, cada uno con formula, bandas y **referencia bibliografica**. La copia esta
CONGELADA en `referencias_primarias/catalogos/` a proposito: un test que baja un JSON de
internet en cada corrida es un test que falla cuando se cae la red, y ademas podria cambiar
de resultado sin que nadie tocara el codigo. Se actualiza a mano, como cualquier referencia.

QUE PRUEBA ESTE ARCHIVO, Y QUE NO
---------------------------------
Prueba que la ARITMETICA y las BANDAS del motor coinciden con el catalogo, o que la
diferencia esta **declarada y justificada**. No prueba que el catalogo tenga razon: es una
segunda opinion, no un oraculo. Donde el motor se aparta a proposito, el test exige que la
excepcion este escrita.
"""
import json
import os
import re

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(RAIZ, 'referencias_primarias', 'catalogos')


def _cargar(nombre):
    with open(os.path.join(CAT, nombre), encoding='utf-8') as fh:
        d = json.load(fh)
    return d.get('SpectralIndices', d)


INDICES = _cargar('asi_spectral-indices-dict.json')
BANDAS = _cargar('asi_bands.json')

# Banda del catalogo -> banda de Sentinel-2. Se lee del propio catalogo en vez de
# escribirlo a mano: si el mapeo cambia, el test lo ve.
S2 = {k: (v.get('platforms', {}).get('sentinel2a', {}) or {}).get('band')
      for k, v in BANDAS.items()}


def a_sentinel2(formula):
    """Reescribe la formula del catalogo en bandas de Sentinel-2.

    ⚠️ Con limites de palabra. Una sustitucion ingenua de subcadenas convierte
    `(N - S1)/(N + S1)` en `(B8 - B211)/...` porque la `B` de `B11` tambien se
    reemplaza. Paso al escribir este test.
    """
    return re.sub(r'\b([A-Za-z][A-Za-z0-9]*)\b',
                  lambda m: S2.get(m.group(1)) or m.group(1), formula)


def _norm(f):
    return f.replace(' ', '')


# --- LO QUE EL MOTOR CALCULA, declarado aca para poder contrastarlo -----------
#
# formula tal como esta en `series._indices`, la clave del catalogo, y —cuando el
# motor se aparta a proposito— la justificacion. Sin justificacion, el test falla.
MOTOR = {
    'NDVI': {
        'formula': '(B8 - B4)/(B8 + B4)',
        'catalogo': 'NDVI',
    },
    'PSRI': {
        'formula': '(B4 - B2)/B6',
        'catalogo': 'PSRI',
    },
    'NDMI': {
        'formula': '(B8A - B11)/(B8A + B11)',
        'catalogo': 'NDMI',
        'excepcion': {
            'cambio': ('B8', 'B8A'),
            'por_que': (
                'B8 tiene FWHM de 118 nm (774-891) e integra media meseta NIR; B8A '
                'tiene 20 nm (855-875) y contiene exactamente los 850-865 nm que pide '
                'Hardisky. Ademas B8A es NATIVO de 20 m igual que B11: usar B8 (10 m) '
                'obliga a remuestrear y mete mezcla espectral en los bordes de lote.'),
        },
    },
    'NDRE': {
        'formula': '(B8A - B5)/(B8A + B5)',
        'catalogo': 'NDREI',
        'excepcion': {
            'cambio': ('B8', 'B8A'),
            'por_que': (
                'Mismo motivo que NDMI: B8A es nativo de 20 m igual que B5, asi que el '
                'indice no mezcla resoluciones.'),
        },
    },
    'CIRE': {
        'formula': '(B7 / B5) - 1',
        'catalogo': 'CIRE',
        'excepcion': {
            'cambio': ('B8', 'B7'),
            'por_que': (
                'La formulacion original de Gitelson usa NIR de ~770-800 nm. B7 esta en '
                '782,8 nm y B8 en 832,8: **B7 es mas fiel al paper original**. Ademas B7 '
                'es nativo de 20 m igual que B5. CIRE NO esta en produccion (los ejes son '
                'NDMI y NDRE); la decision queda escrita para el dia que se evalue.'),
        },
    },
}


# --- 1. EL CATALOGO ESTA Y ES EL QUE SE CONGEL0 ------------------------------

def test_el_catalogo_esta_congelado_en_el_repo():
    """Un test que baja un JSON de internet falla cuando se cae la red, y puede
    cambiar de resultado sin que nadie toque el codigo."""
    assert len(INDICES) > 250, 'el catalogo tiene %d indices, se esperaban ~280' % len(INDICES)
    assert len(BANDAS) > 10


def test_el_mapeo_de_bandas_de_sentinel2_es_el_esperado():
    """Si el catalogo cambiara el mapeo, todas las comparaciones de abajo cambiarian
    de significado sin avisar."""
    esperado = {'N': 'B8', 'N2': 'B8A', 'RE1': 'B5', 'RE2': 'B6', 'RE3': 'B7',
                'S1': 'B11', 'R': 'B4', 'B': 'B2', 'G': 'B3'}
    for k, v in esperado.items():
        assert S2.get(k) == v, 'el catalogo mapea %s -> %s, se esperaba %s' % (k, S2.get(k), v)


# --- 2. LAS FORMULAS ---------------------------------------------------------

@pytest.mark.parametrize('nombre', sorted(MOTOR))
def test_la_formula_coincide_o_la_excepcion_esta_declarada(nombre):
    """EL TEST QUE IMPORTA. O el motor calcula lo mismo que el catalogo, o la
    diferencia esta escrita con su razon.

    Si alguien toca una formula sin actualizar la excepcion, esto falla.
    """
    m = MOTOR[nombre]
    clave = m['catalogo']
    assert clave in INDICES, 'el catalogo no tiene %s' % clave
    ref = a_sentinel2(INDICES[clave]['formula'])
    propia = m['formula']

    if _norm(propia) == _norm(ref):
        return                                    # identico, nada que justificar

    exc = m.get('excepcion')
    assert exc, (
        '%s difiere del catalogo y NO declara excepcion.\n'
        '  motor:    %s\n  catalogo: %s' % (nombre, propia, ref))
    de, a = exc['cambio']
    # Aplicando el cambio declarado, tienen que quedar iguales. Asi el test verifica
    # que la excepcion explica TODA la diferencia y no solo una parte.
    assert _norm(propia.replace(a, de)) == _norm(ref), (
        '%s: la excepcion declarada (%s -> %s) no explica toda la diferencia.\n'
        '  motor:    %s\n  catalogo: %s' % (nombre, de, a, propia, ref))
    assert len(exc['por_que']) > 60, (
        '%s: la excepcion tiene que estar JUSTIFICADA, no solo declarada' % nombre)


@pytest.mark.parametrize('nombre', sorted(MOTOR))
def test_cada_indice_del_motor_tiene_referencia_bibliografica(nombre):
    """Sin DOI no hay como refutar una formula. Es el modo de falla que este archivo
    existe para cerrar."""
    ref = INDICES[MOTOR[nombre]['catalogo']].get('reference')
    assert ref and ('doi.org' in ref or 'ntrs.nasa.gov' in ref or 'asprs.org' in ref), (
        '%s no tiene referencia resoluble en el catalogo: %r' % (nombre, ref))


# --- 3. LAS TRAMPAS QUE YA COSTARON CARO -------------------------------------

def test_ndwi_NO_es_ndmi():
    """La confusion que ya paso: NDWI (McFeeters) es (G-N)/(G+N) y mide AGUA
    SUPERFICIAL. El indice de humedad de dosel es NDMI/NDII.

    Y el "NDWI de Gao" usa 1240 nm, que **Sentinel-2 no tiene** (B9=945, B10=1373,
    B11=1614): es literalmente incalculable con S2.
    """
    ndwi = a_sentinel2(INDICES['NDWI']['formula'])
    ndmi = a_sentinel2(INDICES['NDMI']['formula'])
    assert _norm(ndwi) != _norm(ndmi)
    assert 'B3' in ndwi, 'NDWI deberia usar el verde (B3): %s' % ndwi
    assert 'B11' in ndmi, 'NDMI deberia usar el SWIR (B11): %s' % ndmi


def test_psri_usa_el_azul_y_no_el_verde():
    """Merzlyak 1999 pide (R678 - R500)/R750. B3 va de 542 a 577 nm y **no contiene
    500 nm**; B2 (492,4, ancho) si. Usar B3 fue un error real de este repositorio."""
    f = a_sentinel2(INDICES['PSRI']['formula'])
    assert 'B2' in f and 'B3' not in f, 'PSRI deberia usar B2 (azul), no B3: %s' % f


def test_ndmi_y_ndii_son_la_misma_formula():
    """Son el mismo indice con dos nombres, y el catalogo lo confirma. Importa para
    citar bien: NDII es Hardisky 1983, NDMI es Wilson & Sader 2002. Nunca Gao."""
    assert _norm(INDICES['NDMI']['formula']) == _norm(INDICES['NDII']['formula'])


def test_la_referencia_de_ndmi_es_wilson_sader():
    """La cita que este repositorio ya habia establecido, confirmada por una fuente
    externa e independiente."""
    assert '10.1016/S0034-4257(01)00318-2' in INDICES['NDMI']['reference']


def test_kndvi_referencia_camps_valls():
    """El kNDVI que viaja en la serie como banda de archivo."""
    assert '10.1126/sciadv.abc7447' in INDICES['kNDVI']['reference']
