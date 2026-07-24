# -*- coding: utf-8 -*-
"""
Indices de dosel para cana de azucar — Sentinel-2. Version auditada 2026-07-24.

QUE HACE ESTE MODULO Y QUE NO
=============================
Calcula el estado del DOSEL (hojas). NO estima sacarosa.

La sacarosa se acumula en los ENTRENUDOS DEL TALLO. Ningun sensor optico
satelital ve el tallo: ve hojas. La cadena causal es indirecta y con fugas:
    senal de dosel -> estado hidrico / senescencia -> disparadores de
    maduracion -> particion fuente-sumidero -> sacarosa en el tallo
Inman-Bamber et al. (2011) titulan su trabajo con la conclusion: la acumulacion
de sacarosa en los tallos NO limita la fotosintesis ni la produccion de
biomasa — es decir, fuente (dosel) y sumidero (tallo) estan parcialmente
DESACOPLADOS. Un dosel vigoroso no implica un tallo cargado, y uno senescente
tampoco.
  Inman-Bamber, Jackson & Hewitt (2011), Crop & Pasture Science.
    DOI 10.1071/CP11128
  Inman-Bamber, Bonnett, Spillman, Hewitt & Xu (2009), source-sink.
    DOI 10.1071/CP08272
  Inman-Bamber (2004), water stress criteria for irrigation and drying off,
    Field Crops Research. DOI 10.1016/j.fcr.2004.01.018

NO EXISTE modelo publicado de Pol/Brix/sacarosa absoluta solo con Sentinel-2.
Dos revisiones sistematicas lo confirman por omision — ninguna tiene siquiera
categoria de "calidad/sacarosa":
  de Franca e Silva et al. (2024), Remote Sensing 16(5):863, 72 papers
    revisados (PRISMA). DOI 10.3390/rs16050863
  Som-ard et al. (2021), Remote Sensing 13(20):4040, 107 papers en mapeo (52),
    anomalias (11), salud (14), rendimiento (30). DOI 10.3390/rs13204040

Techo real de S2 en cana, incluso para variables MAS FACILES que la sacarosa
(Hajeb et al. 2023, n=136 ESUs, Iran, DOI 10.1016/j.jag.2022.103168):
    LAI R2=0.42 · humedad de vaina R2=0.42 · clorofila R2=0.27 · N foliar R2=0.12
Si S2 apenas explica el 42% del LAI, exigirle la sacarosa del tallo no tiene base.

LO QUE SI ES DEFENDIBLE con Sentinel-2 en cana:
  - Mapeo de area y clasificacion de cobertura (la aplicacion mas madura).
  - Rendimiento de BIOMASA (t/ha): R2=0.84 con S2 en Etiopia sobre ~10.000 ha
    (Dimov et al. 2022, DOI 10.1016/j.atech.2022.100046).
  - Zonificacion RELATIVA de vigor dentro del lote.
  - Priorizar DONDE y CUANDO muestrear con refractometro.
El producto honesto es el ORDEN DE MUESTREO, no el °Pol.

POR QUE SOLO DOS INDICES
========================
Medido sobre los 131 lotes de Hacienda del Senor (2026-05-15), los cuatro
indices que el motor anterior trataba como cuatro evidencias independientes
son UNA SOLA:
    correlacion NDWI-NDMI = 0.998   (difieren solo en B8 vs B8A, dos NIR
                                     contiguos: es el mismo indice)
    correlacion NDWI-CIRE = 0.899   NDWI-PSRI = -0.866
    PCA: PC1 = 92.5% de la varianza
    numero efectivo de indices independientes = 1.17 de 4
Ponderar copias del mismo numero no puede cambiar el orden: los pesos del
composite anterior eran decoracion. Se conservan dos ejes:
    NDMI  -> estado hidrico del dosel   (el eje dominante, PC1)
    PSRI  -> senescencia / pigmentos    (el unico aporte independiente, PC2 4.4%)
Se descartan NDWI (duplicado exacto de NDMI) y CIRE (r=0.90 con NDMI, sin
validacion publicada contra calidad de jugo en cana, y cita no verificada).

ADVERTENCIA DE TRAZABILIDAD — el "NDWI de Gao" NO se puede calcular con S2
=========================================================================
Gao (1996) define NDWI = (rho_0.86um - rho_1.24um)/(rho_0.86um + rho_1.24um).
  Gao (1996), Remote Sensing of Environment 58(3):257-266.
    DOI 10.1016/S0034-4257(96)00067-3
Sentinel-2 MSI **NO tiene banda en 1.24 um**: salta de B9 (945 nm) a B10
(1375 nm, cirros) y B11 (1610 nm). El NDWI de Gao es INCALCULABLE con S2
(Landsat-8/9 tampoco lo tiene; MODIS si, banda 5).
Lo que se obtiene con (B8A - B11)/(B8A + B11) es el NDII/NDMI, y su cita
correcta es Hardisky/Wilson & Sader — NUNCA Gao. Atribuirlo a Gao es un error
de trazabilidad que un revisor detecta de inmediato.

Ojo tambien con el tercer "NDWI": McFeeters (1996), (Verde-NIR)/(Verde+NIR),
DOI 10.1080/01431169608948714, disenado para delimitar CUERPOS DE AGUA. Las
camaras UAV (MicaSense, DJI P4M) no tienen SWIR, asi que el "NDWI" de los
papers de dron es forzosamente el de McFeeters: un indice de verdor invertido,
casi colineal con el GNDVI. No es evidencia de que la humedad del dosel
prediga sacarosa.
"""
from __future__ import annotations

import ee

__all__ = [
    "BANDAS", "add_indices_dosel", "mask_scl", "escalar_sr",
    "IndiceInfo", "CATALOGO", "resumen_citas",
]

# Piso anti-division-por-cero. La regla del proyecto pide 0.001, no 1e-6:
# S2 L2A SI produce reflectancias negativas sobre sombra y agua, y con un piso
# de 1e-6 un cociente estalla a decenas de miles sin lanzar NaN — el pixel
# entra crudo al promedio del lote y arrastra la media. Los .clamp() a rango
# fisico son la red de seguridad real.
FLOOR = 0.001

BANDAS = ("NDMI", "PSRI")


class IndiceInfo:
    """Ficha de un indice: definicion, cita verificada y limites de uso."""

    def __init__(self, nombre, formula, bandas_s2, cita, doi, valida_para,
                 advertencia=""):
        self.nombre = nombre
        self.formula = formula
        self.bandas_s2 = bandas_s2
        self.cita = cita
        self.doi = doi
        self.valida_para = valida_para
        self.advertencia = advertencia

    def __repr__(self):
        return f"<IndiceInfo {self.nombre} ({self.bandas_s2})>"


CATALOGO = {
    "NDMI": IndiceInfo(
        nombre="NDMI / NDII — indice de humedad NIR-SWIR",
        formula="(B8A - B11) / (B8A + B11)",
        bandas_s2="B8A (865 nm), B11 (1610 nm)",
        cita=("Hardisky, Klemas & Smart (1983), Photogrammetric Engineering & "
              "Remote Sensing 49(1):77-83 (articulo pre-DOI, citar SIN DOI). "
              "Formulacion equivalente en Landsat: Wilson & Sader (2002), "
              "Remote Sensing of Environment 80(3):385-396."),
        doi="10.1016/S0034-4257(01)00318-2",   # Wilson & Sader 2002 (verificado)
        valida_para=("Estado hidrico del dosel. El deficit hidrico y la baja "
                     "temperatura son los motores reconocidos de la maduracion "
                     "natural (SASRI IS 4.7 y IS 12.1; Beauclair, ESALQ 2004), "
                     "por lo que este eje es un PROXY del disparador, no de la "
                     "sacarosa."),
        advertencia=("NO es el NDWI de Gao (1996): ese exige 1.24 um, banda que "
                     "Sentinel-2 no tiene. No atribuir a Gao."),
    ),
    "PSRI": IndiceInfo(
        nombre="PSRI — Plant Senescence Reflectance Index",
        formula="(B4 - B2) / B6",
        bandas_s2="B4 (665 nm), B2 (490 nm), B6 (740 nm)",
        cita=("Merzlyak, Gitelson, Chivkunova & Rakitin (1999), "
              "Physiologia Plantarum 106:135-141."),
        doi="10.1034/j.1399-3054.1999.106119.x",   # verificado
        valida_para=("Senescencia foliar y cambio de pigmentos. Unico eje con "
                     "aporte independiente del hidrico en los datos de HDS "
                     "(PC2, 4.4% de la varianza)."),
        advertencia=("El numerador usa el AZUL B2, no el verde. Es el error "
                     "clasico al adaptar Merzlyak a Sentinel-2."),
    ),
}


def resumen_citas() -> str:
    """Texto de citas para el pie de cada entregable. Solo DOIs verificados."""
    lineas = ["Indices de dosel empleados:"]
    for k in BANDAS:
        i = CATALOGO[k]
        lineas.append(f"  - {i.nombre}: {i.formula} [{i.bandas_s2}]")
        lineas.append(f"      {i.cita}")
        if i.doi:
            lineas.append(f"      DOI {i.doi}")
        if i.advertencia:
            lineas.append(f"      NOTA: {i.advertencia}")
    lineas.append("")
    lineas.append("Datos: Contains modified Copernicus Sentinel data [ano].")
    lineas.append("Estos indices describen el DOSEL. No estiman Pol, Brix ni ATR.")
    return "\n".join(lineas)


def mask_scl(img: "ee.Image") -> "ee.Image":
    """Mascara de nube por Scene Classification Layer.

    Conserva 4 (vegetacion) y 5 (suelo desnudo). NO conserva 7 (unclassified),
    que mezcla pixeles ruidosos, ni 6 (agua): dejar pasar agua a un indice de
    humedad de dosel contamina la media del lote con encharcamientos.
    """
    scl = img.select("SCL")
    return img.updateMask(scl.eq(4).Or(scl.eq(5)))


def escalar_sr(img: "ee.Image") -> "ee.Image":
    """Escala reflectancia S2 L2A de enteros a 0-1."""
    return img.divide(10000).copyProperties(img, img.propertyNames())


def add_indices_dosel(img: "ee.Image") -> "ee.Image":
    """Agrega NDMI y PSRI a una imagen S2 con reflectancia YA escalada a 0-1.

    Cada indice lleva piso anti-division-por-cero y clamp a su rango fisico.
    El clamp es lo que impide que una reflectancia negativa sobre sombra
    produzca un valor plausible-pero-falso que arrastre la media del lote.
    """
    b2  = img.select("B2")
    b4  = img.select("B4")
    b6  = img.select("B6")
    b8a = img.select("B8A")
    b11 = img.select("B11")

    ndmi = (b8a.subtract(b11)
            .divide(b8a.add(b11).max(FLOOR))
            .clamp(-1, 1)
            .rename("NDMI"))

    # Denominador = banda cruda B6, no una suma: aqui el piso es imprescindible.
    psri = (b4.subtract(b2)
            .divide(b6.max(0.01))
            .clamp(-1, 1)
            .rename("PSRI"))

    return img.addBands([ndmi, psri])
