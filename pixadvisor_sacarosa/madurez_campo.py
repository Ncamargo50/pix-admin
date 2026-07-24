# -*- coding: utf-8 -*-
"""
Madurez de cana medida EN CAMPO — indice de maduracion y conversion CONSECANA.

Este modulo contiene la parte del sistema que SI decide la cosecha. El satelite
prioriza donde y cuando muestrear; el refractometro decide si se corta.
Ninguna fuente institucional que se pudo verificar (SASRI, ESALQ/Copersucar,
CONSECANA) decide el orden de corte con satelite.

Sin dependencias: Python puro, para poder correr en el celular, en el Excel de
campo o en el servidor sin instalar nada.

TRES CORRECCIONES QUE SALIERON DE LAS FUENTES OFICIALES (2026-07-24)
====================================================================

1. CONSECANA NO ES UN PROTOCOLO DE CAMPO.
   Es la norma de PAGO POR CALIDAD EN RECEPCION: muestrea la carga del camion
   en la balanza del ingenio con sonda mecanica (muestra final no inferior a
   10 kg), no el talhao. En sus 87 paginas la palabra "maturidade" aparece 0
   veces y "refratometro de campo" 0 veces. Llamar "protocolo CONSECANA" a un
   muestreo de campo es incorrecto.
   Fuente: CONSECANA-SP, Anexo I — Normas Operacionais de Determinacao da
   Qualidade da Cana-de-Acucar, actualizado 12/08/2024, 87 pp.

2. LOS COEFICIENTES DE ATR QUE CIRCULAN ESTAN DESACTUALIZADOS.
   Casi todos los blogs y varios papers usan ATR = 9,5263*PC + 9,05*AR, que
   corresponde a perdidas industriales del 9,5% (factor 0,905) del manual de
   2012. El Anexo I vigente usa factor 0,915 -> ATR = 9,6316*PC + 9,15*ARC.
   Usar los viejos SUBESTIMA el ATR alrededor de 1,1%.

3. EL 85% DEL IM NO ES EL 85% DE SASRI.
   El IM brasileno es una RAZON DE BRIX (ponta/base). La pureza de SASRI es
   100*Pol/Brix, una magnitud distinta que casualmente comparte el numero 85.
   Citar el umbral de SASRI como respaldo del IM es un error de credibilidad.
   Ademas, con los umbrales de Stupiello & Germek, IM = 0,85 es "EM MATURACAO",
   no "madura": madura es >= 0,90.
"""
from __future__ import annotations

__all__ = [
    "indice_maturacao", "clasificar_im", "UMBRALES_IM", "DEFINICION_PUNTOS",
    "n_tallos_recomendado", "pureza_aparente", "ar_caldo", "fibra_desde_pbu",
    "coeficiente_c", "pol_cana", "brix_cana", "ar_cana", "atr_consecana",
    "BRIX_MIN", "BRIX_MAX",
]

# Rango fisico de una lectura de Brix en jugo de cana con refractometro de
# campo (escala tipica 0-32 °Brix).
BRIX_MIN, BRIX_MAX = 6.0, 30.0


# ════════════════════════════════════════════════════════════════════════════
# INDICE DE MATURACAO (IM) — metodo brasileno del refractometro
# ════════════════════════════════════════════════════════════════════════════

DEFINICION_PUNTOS = {
    "ponteiro": ("Entrenudo perteneciente a la ULTIMA HOJA cuya vaina se "
                 "desprende facilmente."),
    "base": "TERCER o CUARTO entrenudo por encima del nivel del suelo.",
}

# Umbrales atribuidos a Stupiello & Germek (1975), transcritos del material
# docente de E. Lazarini, UNESP/FEIS, "Sistemas de determinacao da maturacao
# da cana-de-acucar".
#
# HONESTIDAD SOBRE LA FUENTE: la referencia primaria de 1975 no pudo
# localizarse; se cita el material docente que la transcribe, que es
# universitario pero no revisado por pares. La propia fuente deja un HUECO
# entre 0,85 y 0,90 sin clasificar — no se inventa un relleno: ese rango se
# devuelve explicitamente como zona de transicion.
UMBRALES_IM = {
    "verde":        (None, 0.60),
    "em_maturacao": (0.60, 0.85),
    "transicion":   (0.85, 0.90),   # hueco real de la fuente, declarado
    "madura":       (0.90, 1.00),
    "declinio":     (1.00, None),   # inversion de la sacarosa
}


def indice_maturacao(brix_ponteiro: float, brix_base: float,
                     en_porcentaje: bool = False):
    """Indice de Maturacao IM = Brix(ponteiro) / Brix(base).

    Args:
        brix_ponteiro: °Brix del entrenudo de la ultima hoja de vaina despegable.
        brix_base: °Brix del 3er-4to entrenudo sobre el suelo.
        en_porcentaje: si True devuelve IM*100 (la convencion "CMI" del
            pipeline). El valor es el mismo indice; solo cambia la escala.

    Devuelve None si alguna lectura falta o esta fuera del rango del
    instrumento — una lectura imposible no debe propagarse como dato.
    """
    for v in (brix_ponteiro, brix_base):
        if v is None:
            return None
        if not (BRIX_MIN <= v <= BRIX_MAX):
            return None
    if brix_base <= 0:
        return None
    im = brix_ponteiro / brix_base
    return im * 100.0 if en_porcentaje else im


def clasificar_im(im: float, en_porcentaje: bool = False) -> str:
    """Clasifica el IM segun Stupiello & Germek. Devuelve la clase textual.

    Nota: 'transicion' es un rango que la fuente NO clasifica. Se devuelve tal
    cual en vez de forzarlo a 'madura', que es lo que hacia el umbral >=85 del
    pipeline anterior.
    """
    if im is None:
        return "sin_dato"
    v = im / 100.0 if en_porcentaje else im
    if v < 0.60:
        return "verde"
    if v < 0.85:
        return "em_maturacao"
    if v < 0.90:
        return "transicion"
    if v < 1.00:
        return "madura"
    return "declinio_inversao"


def n_tallos_recomendado(area_ha: float, metodo: str = "sasri") -> int:
    """Numero de tallos a muestrear por lote.

    metodo='sasri': SASRI Information Sheet 4.7 (van Heerden, jun-2021).
        Textual: minimo 3 tallos; lotes < 2 ha -> 2-3 juegos de 3 (6-9);
        lotes de 2-10 ha -> 4 juegos de 3 (12); lotes > 10 ha -> 18 o 24.
        "There should be no need to sample more than 24 stalks per field."
        Los 3 tallos de cada posicion se toman en lineas distintas y a
        AL MENOS 5 m del borde del lote.
    metodo='brasil': 10 tallos por hectarea al azar (Lazarini, UNESP/FEIS),
        sobre area homogenea en variedad, edad, suelo y fertilizacion.
        Escala mal en lotes grandes: 47 ha darian 470 tallos.
    """
    if metodo == "brasil":
        return max(10, int(round(10 * area_ha)))
    if area_ha < 2:
        return 9
    if area_ha <= 10:
        return 12
    return 24


# ════════════════════════════════════════════════════════════════════════════
# CONSECANA-SP — conversion oficial de laboratorio (Anexo I, 12/08/2024)
# ════════════════════════════════════════════════════════════════════════════
# Transcritas literalmente de la seccion 4 del Anexo I vigente.
# S = leitura sacarimetrica del caldo clarificado (Pol del caldo, °Z a 20 °C)
# B = Brix del caldo (refractometro digital, corregido a 20 °C)
# PBU = peso del bolo humedo de la prensa hidraulica (500 +- 0,5 g de cana
#       preparada, 24,5 +- 0,2 MPa durante 1 min)

def pureza_aparente(pol_caldo: float, brix_caldo: float) -> float:
    """Q = 100 * S / B.

    OJO: circula invertida (brix/pol) en material docente. La oficial es
    100 * Pol / Brix.
    """
    if brix_caldo <= 0:
        raise ValueError("Brix del caldo debe ser > 0")
    return 100.0 * pol_caldo / brix_caldo


def ar_caldo(pureza: float) -> float:
    """Azucares reductores del caldo: AR = 3,641 - 0,0343 * Q."""
    return 3.641 - 0.0343 * pureza


def fibra_desde_pbu(pbu_g: float) -> float:
    """Fibra: F = 0,08 * PBU + 0,876."""
    return 0.08 * pbu_g + 0.876


def coeficiente_c(fibra: float) -> float:
    """Coeficiente C = 1,0313 - 0,00575 * F."""
    return 1.0313 - 0.00575 * fibra


def pol_cana(pol_caldo: float, fibra: float) -> float:
    """PC = S * (1 - 0,01 * F) * C."""
    return pol_caldo * (1 - 0.01 * fibra) * coeficiente_c(fibra)


def brix_cana(brix_caldo: float, fibra: float) -> float:
    """BC = B * (1 - 0,01 * F).  No lleva el coeficiente C."""
    return brix_caldo * (1 - 0.01 * fibra)


def ar_cana(ar_caldo_val: float, fibra: float) -> float:
    """ARC = AR * (1 - 0,01 * F) * C."""
    return ar_caldo_val * (1 - 0.01 * fibra) * coeficiente_c(fibra)


def atr_consecana(pol_caldo: float, brix_caldo: float, pbu_g: float) -> dict:
    """Azucar Total Recuperavel (kg/t) por la norma vigente.

        ATR = 10 * PC * 1,05263 * 0,915 + 10 * ARC * 0,915
            = 9,6316 * PC + 9,15 * ARC

    El 0,915 corresponde a las perdidas del proceso industrial de la version
    vigente (12/08/2024). El manual de 2012 usaba 0,905, de donde salen los
    coeficientes viejos 9,52603 / 9,05 que aun circulan; usarlos subestima el
    ATR ~1,1%. El 1,05263 es el factor estequiometrico sacarosa -> azucares
    reductores.

    Devuelve el desglose completo para que el calculo sea auditable.
    """
    q = pureza_aparente(pol_caldo, brix_caldo)
    ar = ar_caldo(q)
    f = fibra_desde_pbu(pbu_g)
    pc = pol_cana(pol_caldo, f)
    bc = brix_cana(brix_caldo, f)
    arc = ar_cana(ar, f)
    atr = 9.6316 * pc + 9.15 * arc
    return {
        "pureza_Q": q, "AR_caldo": ar, "fibra_F": f, "coef_C": coeficiente_c(f),
        "PC_pol_cana": pc, "BC_brix_cana": bc, "ARC_ar_cana": arc,
        "ATR_kg_por_t": atr,
    }
