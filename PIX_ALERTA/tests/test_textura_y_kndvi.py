# -*- coding: utf-8 -*-
"""Los candidatos nuevos de eje: kNDVI y las dos bandas de textura.

Corren sin GEE. Lo que se prueba NO es que Earth Engine calcule bien —eso no se puede
probar aca— sino las tres cosas que si se pueden romper desde este repositorio y que
serian silenciosas:

  1. que un indice se calcule y NO viaje en la serie (existe pero es inmedible);
  2. que un eje candidato no declare su SIGNO de alarma (el motor marcaria los sanos);
  3. que la AFIRMACION que justifica un signo sea falsa.

La tercera es la que este repositorio ya aprendio a testear por las malas
(`test_evidencia_citada.py`): una afirmacion escrita en un comentario y nunca
verificada es exactamente como se aprobo un criterio con evidencia inexistente.
"""
import numpy as np
import pytest

from pix_alerta import config as cfg
from pix_alerta import ranking as rk
from pix_alerta import series as sr


# --- 1. CONTRATO: lo que se calcula tiene que viajar --------------------------

def test_bandas_nuevas_viajan_en_la_serie():
    """KNDVI, TEXNIR y NDTX estan en el contrato de columnas de la serie.

    Sin esto se calculan en cada escena —costando cuota de GEE— y despues no aparecen
    en la tabla, asi que ningun arnes de medicion puede verlos.
    """
    for banda in ('KNDVI', 'TEXNIR', 'NDTX'):
        assert banda in sr.BANDAS_DOSEL, '%s no esta en BANDAS_DOSEL' % banda
        assert banda in sr.COLS_SERIE, '%s no viaja en la serie' % banda


def test_cols_serie_contiene_las_llaves():
    """La serie sin lote_id, fecha o calidad no es una serie."""
    for c in ('lote_id', 'fecha', 'calidad', 'cobertura'):
        assert c in sr.COLS_SERIE


# --- 2. SIGNO: ningun eje candidato sin sentido de alarma declarado -----------

def test_todo_candidato_declara_signo():
    """Cualquier banda de dosel usable como eje tiene signo en ranking.SIGNO.

    `ranking` ya crashea al importar si `cfg.EJES` trae un eje sin signo. Esto es la
    puerta de ANTES: que el signo este declarado desde que la banda existe, para que
    probar un eje candidato no exija tocar dos archivos y arriesgarse a olvidar uno.
    FVC queda afuera: es la compuerta de dosel, no un eje.
    """
    faltan = [b for b in sr.BANDAS_DOSEL
              if b != 'FVC' and b not in rk.SIGNO]
    assert not faltan, 'sin signo declarado: %s' % faltan


def test_signos_son_mas_uno_o_menos_uno():
    for eje, s in rk.SIGNO.items():
        assert s in (+1, -1), '%s tiene signo %r' % (eje, s)


def test_ejes_de_produccion_siguen_siendo_espectrales():
    """Los candidatos NO estan en produccion.

    La regla de `config.py` es que mover `EJES` exige una razon POSITIVA medida.
    Agregar bandas candidatas a la serie no es esa razon. Si este test falla, alguien
    puso textura en produccion sin las tres mediciones: la de independencia
    (`medicion/textura_como_eje.py`), la tasa empirica sobre fechas sin evento y el
    lift contra la nula sintetica.
    """
    assert set(cfg.EJES).isdisjoint({'TEXNIR', 'NDTX', 'KNDVI'}), (
        'hay un eje candidato en produccion: %s. Ver medicion/textura_como_eje.py '
        'antes de hacer esto.' % (set(cfg.EJES) & {'TEXNIR', 'NDTX', 'KNDVI'}))


# --- 3. LA AFIRMACION QUE JUSTIFICA EL SIGNO DE kNDVI -------------------------

def _kndvi(ndvi):
    """La forma que usa `series._indices`: tanh(NDVI^2)."""
    return np.tanh(np.asarray(ndvi, dtype=float) ** 2)


def test_kndvi_es_monotono_creciente_sobre_ndvi_positivo():
    """La afirmacion que justifica SIGNO['KNDVI'] = -1.

    `series._indices` declara que kNDVI es una transformacion monotona creciente de
    NDVI sobre NDVI>=0, y de ahi que su alarma sea el valor bajo igual que NDVI. Si
    fuera falso, el signo estaria mal y el motor marcaria los lotes sanos.
    """
    ndvi = np.linspace(0.0, 1.0, 501)
    k = _kndvi(ndvi)
    assert np.all(np.diff(k) > 0), 'kNDVI no es estrictamente creciente en NDVI>=0'


def test_kndvi_no_es_monotono_sobre_ndvi_negativo():
    """El limite del que hay que acordarse: sobre NDVI<0 la monotonia se INVIERTE.

    tanh(x^2) es PAR, asi que para NDVI negativo kNDVI vuelve a crecer. En dosel eso no
    pasa —la compuerta de FVC ya excluye suelo desnudo y agua— pero si algun dia se
    usara kNDVI sin compuerta, el signo dejaria de valer. Se deja como test para que el
    limite este escrito y no se descubra en campo.
    """
    ndvi = np.linspace(-1.0, 1.0, 501)
    k = _kndvi(ndvi)
    assert not np.all(np.diff(k) > 0)


def test_kndvi_no_satura_donde_ndvi_satura():
    """La razon de existir de kNDVI, como propiedad verificable.

    Entre NDVI 0,80 y 0,95 —dosel cerrado, donde el NDVI se aplana— kNDVI tiene que
    conservar MAS resolucion relativa que el propio NDVI. Se compara el cambio
    relativo de cada uno sobre el mismo tramo.
    """
    a, b = 0.80, 0.95
    rel_ndvi = (b - a) / a
    ka, kb = float(_kndvi(a)), float(_kndvi(b))
    rel_k = (kb - ka) / ka
    assert rel_k > rel_ndvi, (
        'kNDVI no aporta resolucion en dosel cerrado: rel_k=%.4f rel_ndvi=%.4f'
        % (rel_k, rel_ndvi))


def _fvc(x, umbral=None):
    """La compuerta tal como la calcula `series._fvc`: lineal entre p2 y p98."""
    p2, p98 = np.percentile(x, [2, 98])
    f = np.clip((x - p2) / max(p98 - p2, 1e-6), 0, 1)
    return f if umbral is None else f >= umbral


def test_kndvi_NO_es_invariante_en_la_compuerta_de_dosel():
    """AUDITADO 2026-08-03: la afirmacion "kNDVI sirve para la compuerta" era FALSA.

    El orden de los pixeles es identico (correlacion de rangos 1,000000), pero FVC no
    es invariante a transformaciones monotonas NO LINEALES: normaliza entre percentiles
    y despues CORTA en un valor. Reemplazar NDVI por kNDVI en la compuerta corre el
    umbral efectivo sin ninguna razon positiva.

    Este test existe para que la afirmacion no vuelva. Si alguien cambia la compuerta a
    kNDVI "porque no satura", esto le muestra el costo: pixeles que cambian de lado sin
    que nadie haya calibrado nada.
    """
    rng = np.random.default_rng(0)
    ndvi = np.clip(rng.normal(0.72, 0.12, 20000), 0, 0.97)
    k = _kndvi(ndvi)

    # 1. el orden SI se preserva
    r_ndvi = np.argsort(np.argsort(ndvi))
    r_k = np.argsort(np.argsort(k))
    assert np.corrcoef(r_ndvi, r_k)[0, 1] == pytest.approx(1.0, abs=1e-9)

    # 2. pero la compuerta NO da lo mismo
    pasa_n = _fvc(ndvi, cfg.FVC_MINIMA)
    pasa_k = _fvc(k, cfg.FVC_MINIMA)
    difieren = np.logical_xor(pasa_n, pasa_k).mean()
    assert difieren > 0, ('si esto da 0 la compuerta se volvio invariante y hay que '
                          'rehacer el razonamiento de series._indices')
    # Se fija el orden de magnitud medido (~1,3%), no el valor exacto.
    assert difieren < 0.05


def _dilatar(m, r=1):
    """Vecindad cuadrada de radio r, sin depender de scipy."""
    out = np.zeros_like(m)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return out


def test_la_textura_dilata_el_foco_y_por_eso_no_puede_delimitar():
    """MEDIDO: un foco del tamaño exacto de la MMU se infla 4,2 veces.

    Toda medida de ventana contamina a los vecinos. Con GLCM 3x3 a 20 m, un pixel
    anomalo altera la textura de los 8 que lo rodean.

    Lo que este test PROTEGE: que a nadie se le ocurra vectorizar el foco —el poligono
    y las hectareas que se le informan al cliente— a partir de la textura. Detectar si,
    delimitar no.
    """
    px_m2 = 20 * 20
    lote = np.zeros((60, 60), bool)
    lote[30:31, 30:35] = True                      # 5 px = 0,20 ha = la MMU exacta
    area_real = lote.sum() * px_m2 / 1e4
    assert area_real == pytest.approx(0.20)

    afectado = _dilatar(lote, sr.GLCM_VENTANA_PX)
    factor = afectado.sum() / lote.sum()
    assert factor > 2.0, ('la textura ya no dilata: si la ventana cambio, rehacer el '
                          'limite 5 de series._textura')
    # A la MMU exacta el factor medido fue 4,2. Se deja holgura por si cambia la ventana.
    assert factor == pytest.approx(4.2, abs=1.0)


# --- 4. LA LOGICA DE SIGNO DEL ARNES DE TEXTURA ------------------------------

def test_signo_implicado_invierte_respecto_del_primer_eje():
    """El primer eje (NDMI) alarma en el valor BAJO; la implicacion sale de ahi.

    rho > 0 entre residuos => el candidato baja cuando NDMI baja => alarma baja => -1
    rho < 0                => el candidato sube cuando NDMI baja => alarma alta => +1
    """
    from medicion.textura_como_eje import signo_implicado
    assert signo_implicado(+0.80)[0] == -1
    assert signo_implicado(-0.80)[0] == +1
    assert signo_implicado(-0.80)[1] == pytest.approx(0.80)


def test_primer_eje_alarma_en_valor_bajo():
    """`signo_implicado` supone que cfg.EJES[0] tiene SIGNO -1. Si cambia, se rompe.

    Es un supuesto que hoy es cierto (NDMI = -1) y que esta cableado en el
    razonamiento del arnes. Si algun dia el primer eje pasa a ser uno que alarma alto
    —PSRI, por ejemplo— la implicacion de signo se invierte y hay que corregir
    `medicion/textura_como_eje.signo_implicado` ANTES de volver a usarla.
    """
    assert rk.SIGNO[cfg.EJES[0]] == -1, (
        'el primer eje ya no alarma en el valor bajo: revisar signo_implicado()')


# --- 5. CUANTIZACION DE LA TEXTURA -------------------------------------------

def test_cuantizacion_de_textura_es_fija_y_declarada():
    """El contraste GLCM no es invariante a la cuantizacion.

    Si el rango se reescalara por escena, el contraste de un dia nublado no seria
    comparable con el de un dia limpio, y la serie temporal de textura mediria el
    clima en vez del cultivo. Los tres parametros tienen que ser constantes de modulo.
    """
    assert isinstance(sr.GLCM_NIVELES, int) and sr.GLCM_NIVELES > 1
    assert isinstance(sr.GLCM_VENTANA_PX, int) and sr.GLCM_VENTANA_PX >= 1
    assert 0 < sr.GLCM_REF_MAX <= 1.0, 'el rango se declara en reflectancia (0-1)'


def test_textura_no_se_calcula_en_el_camino_caliente():
    """El GLCM NO se paga cuando ningun eje de textura esta declarado.

    ⚠️ ES UN TEST DE COSTO, Y ESO NO LO HACE MENOS IMPORTANTE. El criterio llama a
    `_indices` una vez por escena y por lote, dos veces por dia en la nube, y despues
    descarta todo lo que no esta en `cfg.EJES`. Calcular la matriz de co-ocurrencia
    para tirarla es la clase de derroche que no falla —simplemente hace que la corrida
    se ponga lenta o choque contra los limites de GEE— y que por eso nadie descubre.
    """
    assert sr._hace_falta_textura() is False, (
        'con EJES=%s la textura no deberia calcularse' % (cfg.EJES,))


def test_textura_se_calcula_cuando_se_la_declara_como_eje():
    """Y el arnes de medicion la consigue solo con pisar cfg.EJES."""
    antes = cfg.EJES
    try:
        cfg.EJES = ('NDMI', 'TEXNIR')
        assert sr._hace_falta_textura() is True
    finally:
        cfg.EJES = antes
    assert sr._hace_falta_textura() is False, 'no se restauro cfg.EJES'


def test_textura_forzada_y_apagada_a_mano():
    """El override explicito gana sobre la deteccion automatica, en los dos sentidos."""
    assert sr._hace_falta_textura(True) is True
    assert sr._hace_falta_textura(False) is False


def test_ventana_de_textura_es_mas_chica_que_un_lote():
    """Una ventana que se come el lote entero no mide heterogeneidad interna.

    Con ventana de radio r a escala `escala`, el lado es (2r+1)*escala metros. Se exige
    que quede holgadamente por debajo del lado de un lote chico (~100 m para 1 ha).
    """
    lado_m = (2 * sr.GLCM_VENTANA_PX + 1) * 20
    assert lado_m <= 100, 'ventana de %d m: demasiado grande para textura intra-lote' % lado_m
