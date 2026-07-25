# -*- coding: utf-8 -*-
"""Propuesta de UNA PÁGINA de Pixadvisor Monitor.

    python _build_propuesta_monitor.py --cliente HDS

Es el documento con el que se convierte el primer cliente que paga. Cabe en una carilla
a propósito: el productor la lee entera de pie, en el galpón.

QUÉ TIENE Y POR QUÉ
-------------------
1. El ahorro de Embrapa ADELANTE. Lo que se vende no es "detecto la plaga por satélite"
   —insostenible, se cae en la primera campaña— sino "hago que el MIP sea aplicable en
   tus 200 lotes". El respaldo es de Embrapa, no de Pixadvisor.
2. Lo que NO se promete, POR ESCRITO y en la misma carilla. Es lo único que hace
   defendible todo lo demás, y ninguno de los 15 competidores revisados lo publica.
3. El hueco máximo de nubes como número, no como letra chica.

MONEDA: sale del país del cliente. HDS está en Santa Cruz (UTM 20S) → se cotiza en USD
y se cobra en Bs por BISA. Cotizar en R$ con Pix Automático sería para clientes de
Brasil. Con el tipo de cambio liberado (jun-2026) se cotiza en USD y se convierte al
día del pago, para no comerse la variación.
"""
import argparse
import os
import sys

from reportlab.lib.units import cm
from reportlab.platypus import Spacer

SKILL = r"C:\Users\Usuario\.claude\skills\pixadvisor-propuesta-ejecutiva"
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from pix_branding import Brand, AZUL, TEAL, LIMA  # noqa: E402


# --- Clientes -----------------------------------------------------------------
# REGLA: ningún número de este documento puede ser inventado. La propuesta dice que el
# hueco de nubes "va en el contrato como número"; si ese número es un supuesto, la frase
# es una mentira y el cliente la va a cobrar. `lotes` y `hueco_dias` tienen que salir de
# una medición real, y `fuente` dice de cuál.
#
# Los campos en None se toman como NO VERIFICADOS y el script se niega a emitir.
# Pasó de verdad al armar esto: la entrada de Cerro Alto salió con 66 lotes (son 37),
# "Paraná" sin confirmar y 45 días de hueco (el medido para Cascavel PR es 35).
CLIENTES = {
    "HDS": dict(
        nombre="Hacienda del Señor",
        pais="Bolivia",
        zona="Santa Cruz",
        lotes=207,                 # PIX_ALERTA, campaña 2025/26: 207 lotes de cultivo
        cultivo="soya y verano",
        moneda="USD",
        precio_mes=300,
        # Los datos bancarios NO van en la propuesta: van en la factura. Acá solo la
        # estructura del precio, que es lo que el productor necesita para decidir.
        cobro="Cotizado en USD, pagadero en bolivianos al cambio del día.",
        hueco_dias=66,             # DISPONIBILIDAD_MULTISITIO: peor caso Santa Cruz
        fuente="lotes: serie PIX_ALERTA 2025/26 · hueco: DISPONIBILIDAD_MULTISITIO.md",
    ),
    "CERRO": dict(
        nombre="Cerro Alto",
        pais="Brasil",
        zona=None,                 # FALTA: el CRS es SIRGAS UTM 21S, pero el estado no
        #                            está confirmado en ninguna nota. NO inventarlo.
        lotes=37,                  # verificado: 37 lotes / 1.871,5 ha brutas / 1.782,8 útiles
        cultivo="soya 2026/27",
        moneda="R$",
        precio_mes=1800,
        cobro="Débito recurrente por Pix Automático, sin recargo.",
        hueco_dias=None,           # FALTA: medir sobre SU AOI. Los medidos son de otros
        #                            sitios (Cascavel PR 35 d, Maracajú MS 70 d) y no
        #                            transfieren sin saber dónde está el campo.
        fuente="lotes: _serroalto_recompute_final.py (2026-06-24)",
    ),
}

OBLIGATORIOS = ("nombre", "pais", "zona", "lotes", "cultivo", "moneda",
                "precio_mes", "cobro", "hueco_dias")


def verificar(clave, c):
    """Se niega a emitir con datos sin verificar. Un dato inventado en una propuesta
    comercial no es un bug de formato: es lo que hace que el cliente deje de creerte."""
    faltan = [k for k in OBLIGATORIOS if c.get(k) in (None, "")]
    if faltan:
        raise SystemExit(
            "[ERROR] el cliente %s tiene datos SIN VERIFICAR: %s\n"
            "        Esta propuesta afirma que el hueco de nubes 'va en el contrato como\n"
            "        número'. Con un número supuesto, esa frase es falsa.\n"
            "        Completar en CLIENTES tras medirlos, y anotar la fuente."
            % (clave, ", ".join(faltan)))


def construir(c, salida):
    B = Brand(
        logo=os.path.join(SKILL, "assets", "logo_pix_azulnegro_trim.png"),
        footer_center="%s · Pixadvisor Monitor · 2026" % c["nombre"],
        # Hero corto: en una carilla, los 9,6 cm del default dejaban 2,5 cm de degradado
        # vacio bajo el subtitulo y empujaban el cierre a una segunda pagina.
        hero_h=7.3 * cm,
    )
    m = c["moneda"]
    S = []
    S += B.cover_filler()          # se calcula solo del alto del hero

    S += [B.P("<b>Cada 10 días recibís los lotes que conviene caminar esta semana, en "
              "orden de prioridad.</b> No reemplaza al agrónomo: le dice por dónde "
              "empezar.", "Body")]
    S += [Spacer(1, 0.16 * cm)]

    # El argumento no es de Pixadvisor: es de Embrapa. Por eso va con la fuente.
    # El ahorro se muestra en la moneda del cliente: "R$ 270" no le dice nada a un
    # productor boliviano, y el numero es lo que tiene que quedar.
    ahorro = "R$ 270" if m == "R$" else "USD 49"
    S += [B.kpi_strip([
        (ahorro, "de ahorro <b>por hectárea</b><br/>decidiendo por umbral"),
        ("1,02", "aplicaciones con MIP<br/><b>contra 3,36</b> sin MIP"),
        ("33%", "de adopción real<br/>aunque el 76% lo conoce"),
    ])]
    conv = ("" if m == "R$" else " (≈ USD 49 al cambio de R$ 5,5/USD)")
    S += [B.P("Embrapa Soja + IDR-Paraná 2024/25 (n = 119), medido en R$ 270,16/ha%s. El "
              "ahorro sale de <b>no aplicar por calendario</b>, sin perder "
              "productividad. El MIP funciona: falta tiempo para recorrer %d lotes."
              % (conv, c["lotes"]), "Note")]
    S += [Spacer(1, 0.20 * cm)]

    S += [B.P("Qué recibe %s" % c["nombre"], "H2")]
    S += [B.meta_table([
        ("Cada 10 días", "Los lotes ordenados por prioridad, con la fecha de la última "
                         "imagen válida de cada uno."),
        ("En el celular", "App que navega al lote, guía el diagnóstico y registra lo "
                          "hallado, <b>incluido “fui y no había nada”</b>."),
        ("Siempre", "Si no hubo imagen limpia, el informe lo dice. Nunca se inventa un "
                    "rojo con una escena nublada."),
    ])]
    S += [Spacer(1, 0.20 * cm)]

    S += [B.P("Lo que este servicio NO hace", "H2")]
    S += [B.P(
        "Va por escrito, porque es lo que lo hace confiable. "
        "<b>No identifica la plaga ni la enfermedad</b>: el satélite no dice la causa, "
        "la confirma el técnico. <b>No detecta chinches</b> ni <b>roya asiática</b> a "
        "escala de lote —hay evidencia publicada—, y <b>no ve el daño antes de que sea "
        "visible</b>. Con nubes puede haber huecos: el peor medido en %s es de "
        "<b>%d días</b>, y va en el contrato como número."
        % (c["zona"], c["hueco_dias"]), "Body")]
    S += [Spacer(1, 0.20 * cm)]

    S += [B.P("Inversión", "H2")]
    precio = "%s %s" % (m, "{:,.0f}".format(c["precio_mes"]).replace(",", "."))
    S += [B.tbl([
        [B.P("Concepto", "CellB"), B.P("Detalle", "CellB"), B.P("Mensual", "CellB")],
        [B.P("Pixadvisor Monitor", "CellBold"),
         B.P("%d lotes · %s · sin costo de alta" % (c["lotes"], c["cultivo"]), "Cell"),
         B.P("<b>%s</b>" % precio, "Cell")],
    ], [4.3 * cm, 7.7 * cm, 3.0 * cm], aligns={2: "CENTER"})]
    S += [B.P("Por campaña, sin permanencia: se corta al final de cualquier mes. %s"
              % c["cobro"], "Note")]
    S += [Spacer(1, 0.20 * cm)]

    S += [B.callout(
        "Próximo paso",
        "Mandanos el archivo de lotes y la planilla de siembra: en una semana tenés el "
        "primer informe de tu campo, sin cargo.")]

    # Margen inferior ajustado: es una carilla sola, no hay pagina siguiente que cuidar.
    B.build(salida, S,
            cover_title="Pixadvisor Monitor",
            cover_subtitle="%s · %s, %s" % (c["nombre"], c["zona"], c["pais"]),
            bottomMargin=1.45 * cm)

    # UNA CARILLA es un requisito, no una preferencia: la propuesta se lee de pie en el
    # galpon. Si crece, se avisa en vez de entregar dos paginas sin que nadie lo note.
    try:
        import fitz
        n = fitz.open(salida).page_count
        if n != 1:
            print("[AVISO] la propuesta salio en %d paginas. Recortar texto." % n)
    except ImportError:
        pass
    return salida


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cliente", default="HDS", choices=sorted(CLIENTES))
    p.add_argument("--salida", default=None)
    a = p.parse_args()
    c = CLIENTES[a.cliente]
    verificar(a.cliente, c)
    out = a.salida or "Propuesta_Pixadvisor_Monitor_%s.pdf" % a.cliente
    construir(c, out)
    print("OK ->", out)


if __name__ == "__main__":
    main()
