---
name: teledeteccion-monitoreo-cultivos
description: >
  Skill PRO de teledeteccion y sensoriamiento remoto aplicados a monitoreo de cultivos
  y agricultura de precision. Cubre: Sentinel-2 bandas e indices por etapa fenologica,
  series temporales NDVI/NDRE/LAI/fAPAR, deteccion de estres hidrico (CWSI, termica,
  NDMI), estres nutricional (N via NDRE/MTCI/CCCI), deteccion temprana de enfermedades
  y plagas, SIF fluorescencia solar, SAR Sentinel-1 fusion optico-radar, asimilacion
  de datos en modelos de cultivo (DSSAT/APSIM), prediccion de rendimiento, sistemas
  operacionales (USDA CDL/CropScape, Copernicus), tecnologias Israel (Taranis, CropX,
  SeeTree, Volcani), GEE scripts completos, y flujos de trabajo end-to-end.

  USAR cuando el usuario mencione: monitoreo de cultivos, seguimiento fenologico,
  series temporales satelite, estres hidrico, estres nutricional, deteccion enfermedades,
  prediccion rendimiento, CWSI, SIF fluorescencia, asimilacion datos, DSSAT LAI,
  alertas tempranas, prescripcion variable, crop monitoring, phenology tracking,
  Sentinel-2 time series, crop health, early warning, yield prediction.
---

# Teledeteccion y Monitoreo de Cultivos — Skill PRO

> **Rol**: Especialista en Percepcion Remota Agricola + Agronomo Senior + Data Scientist
> **Nivel**: Expert / Research-grade (papers 2024-2026)
> **Stack**: Sentinel-2/1, Landsat, MODIS, TROPOMI, GEE, Python, DSSAT/APSIM

---

## TABLA DE CONTENIDOS

| # | Modulo | Trigger |
|---|--------|---------|
| 1 | [Sentinel-2 para Monitoreo de Cultivos](#1-sentinel-2-para-monitoreo-de-cultivos) | "Sentinel-2", "bandas", "resolucion" |
| 2 | [Indices por Etapa Fenologica](#2-indices-de-vegetacion-por-etapa-fenologica) | "indice", "fenologia", "NDVI", "NDRE" |
| 3 | [Series Temporales y Fenologia](#3-series-temporales-y-seguimiento-fenologico) | "serie temporal", "time series", "fenologia" |
| 4 | [Deteccion de Estres Hidrico](#4-deteccion-de-estres-hidrico) | "estres hidrico", "CWSI", "riego", "sequia" |
| 5 | [Estres Nutricional y Fertilizacion Variable](#5-estres-nutricional-y-fertilizacion-variable) | "nitrogeno", "NDRE", "VRT", "fertilizacion" |
| 6 | [Deteccion de Enfermedades y Plagas](#6-deteccion-temprana-de-enfermedades-y-plagas) | "enfermedad", "plaga", "alerta temprana" |
| 7 | [SIF Fluorescencia Solar](#7-sif-fluorescencia-solar-inducida) | "SIF", "fluorescencia", "GPP", "fotosintesis" |
| 8 | [Fusion SAR + Optico](#8-fusion-sar-optico-monitoreo-all-weather) | "SAR", "Sentinel-1", "nubes", "radar" |
| 9 | [Prediccion de Rendimiento](#9-prediccion-de-rendimiento) | "yield", "rendimiento", "prediccion", "forecast" |
| 10 | [Asimilacion en Modelos de Cultivo](#10-asimilacion-de-datos-en-modelos-de-cultivo) | "DSSAT", "APSIM", "LAI asimilacion" |
| 11 | [Sistemas Operacionales Globales](#11-sistemas-operacionales-globales) | "USDA", "CropScape", "CDL", "Copernicus" |
| 12 | [Tecnologias Israel y Referentes](#12-tecnologias-israel-y-referentes-mundiales) | "Taranis", "CropX", "Israel", "agritech" |
| 13 | [GEE Scripts Completos](#13-gee-scripts-de-monitoreo) | "GEE", "script", "codigo", "monitoreo GEE" |
| 14 | [Flujo End-to-End](#14-flujo-de-trabajo-end-to-end) | "flujo completo", "pipeline", "workflow" |

---

## 1. SENTINEL-2 PARA MONITOREO DE CULTIVOS

### 1.1 Bandas y Resoluciones

```
SENTINEL-2A/2B (ESA) — Revisita: 5 dias (constelacion)

Banda | Longitud (nm) | Resolucion | Aplicacion Agricola
------|---------------|------------|--------------------
B2   | 490 (Blue)    | 10m       | Atmosfera, EVI denominador
B3   | 560 (Green)   | 10m       | GNDVI, clorofila, vigor
B4   | 665 (Red)     | 10m       | NDVI, absorcion clorofila
B5   | 705 (RE1)     | 20m       | NDRE, MTCI, red-edge inflexion
B6   | 740 (RE2)     | 20m       | CIre, S2REP, clorofila densa
B7   | 783 (RE3)     | 20m       | IRECI, LAI proxy
B8   | 842 (NIR)     | 10m       | NDVI, estructura canopy, biomasa
B8A  | 865 (NIR-n)   | 20m       | NDRE (B8A vs B5), NDMI
B11  | 1610 (SWIR1)  | 20m       | NDMI humedad, NBR2 rastrojo
B12  | 2190 (SWIR2)  | 20m       | NBR2, contenido agua tejidos
```

### 1.2 Ventaja Red-Edge (B5-B7) para Agricultura

Las 3 bandas red-edge (705, 740, 783 nm) son EXCLUSIVAS de Sentinel-2 vs Landsat.
Permiten detectar cambios de clorofila y N que NDVI convencional NO captura:

```
NDVI satura en LAI > 3-4 (dosel cerrado)
NDRE sigue diferenciando hasta LAI > 7
MTCI es LINEAL con contenido de clorofila
S2REP indica posicion exacta del punto de inflexion red-edge (710-730 nm)
```

Esto es critico para cultivos de alta biomasa: cana, maiz, arroz, trigo en fase avanzada.

### 1.3 Mascaras de Nubes (SCL)

```javascript
// GEE: Mascara SCL (Scene Classification Layer) — Sentinel-2 SR
function maskS2clouds(image) {
  var scl = image.select('SCL');
  var mask = scl.neq(0).and(scl.neq(1)).and(scl.neq(3))
    .and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  return image.updateMask(mask);
}

// Clases SCL:
// 0: No data | 1: Saturado | 3: Sombra nube
// 4: Vegetacion | 5: Suelo desnudo | 6: Agua
// 8: Nube media | 9: Nube alta | 10: Cirrus | 11: Nieve
```

---

## 2. INDICES DE VEGETACION POR ETAPA FENOLOGICA

### 2.1 Tabla de Indices y Formulas Sentinel-2

```
Indice    | Formula                                    | Rango    | Uso Principal
----------|--------------------------------------------|---------|--------------
NDVI      | (B8-B4)/(B8+B4)                           | -1 a 1  | Vigor general, referencia
NDRE      | (B8A-B5)/(B8A+B5)                         | -1 a 1  | Clorofila/N, no satura
EVI       | 2.5*(B8-B4)/(B8+6*B4-7.5*B2+1)           | -1 a 1  | Alta biomasa, correccion atm.
SAVI      | 1.5*(B8-B4)/(B8+B4+0.5)                   | -1 a 1  | Suelo expuesto, cobertura baja
MSAVI2    | (2*B8+1-sqrt((2*B8+1)^2-8*(B8-B4)))/2     | 0 a 1   | Auto-ajuste L, plantio
kNDVI     | tanh(NDVI^2)                               | 0 a 1   | Anti-saturacion LAI>4
GNDVI     | (B8-B3)/(B8+B3)                            | -1 a 1  | Clorofila, moderada-alta LAI
OSAVI     | 1.16*(B8-B4)/(B8+B4+0.16)                 | 0 a 1   | SAVI optimizado, L=0.16
MTCI      | (B6-B5)/(B5-B4)                            | 0 a 6+  | Clorofila LINEAL, no satura
S2REP     | 705+35*((B4+B7)/2-B5)/(B6-B5)             | 710-730 | Posicion red-edge (nm)
IRECI     | (B7-B4)/(B5/B6)                            | 0 a 10  | LAI, clorofila biofisica
CCCI      | NDRE/NDVI                                  | 0 a 2+  | Contenido clorofila dosel, proxy N
CIre      | B8A/B6 - 1                                 | 0 a 5+  | Clorofila red-edge alternativo
RENDVI    | (B6-B5)/(B6+B5)                            | -1 a 1  | Red-edge estrecho, sensible a N
NDMI      | (B8A-B11)/(B8A+B11)                        | -1 a 1  | Humedad foliar/vegetal
NBR2      | (B11-B12)/(B11+B12)                        | -1 a 1  | Rastrojo, estres hidrico SWIR
MSI       | B11/B8A                                    | 0 a 3+  | Estres hidrico (inverso NDMI)
BSI       | (B11+B4-B8-B2)/(B11+B4+B8+B2)             | -1 a 1  | Suelo desnudo, SOC
PSRI      | (B4-B3)/B6                                 | -1 a 1  | Senescencia, carotenoides
EVI2      | 2.5*(B8-B4)/(B8+2.4*B4+1)                 | -1 a 1  | EVI sin banda azul
```

### 2.2 Seleccion de Indices por Etapa Fenologica

```
ETAPA FENOLOGICA           | INDICES PRIMARIOS          | RAZON
---------------------------|---------------------------|------
Emergencia / Plantio       | MSAVI2, OSAVI, BSI, SAVI  | Suelo dominante, cobertura <30%
Macollaje / Desarrollo     | NDRE, MTCI, CCCI, GNDVI   | Discriminacion N, clorofila
Cierre de canopy           | NDRE, kNDVI, S2REP, EVI   | NDVI comienza a saturar
Maxima biomasa             | kNDVI, MTCI, S2REP, IRECI | NDVI saturado, red-edge critico
Floracion / Fructificacion | NDRE, EVI, NDMI, CCCI     | Estado hidrico + nutricional
Maduracion / Senescencia   | NDMI, PSRI, NBR2, MSI     | Humedad, degradacion clorofila
Post-cosecha / Rastrojo    | BSI, NBR2, MSAVI2         | Residuos, suelo expuesto
```

### 2.3 Indices por Cultivo (Produccion)

```
CULTIVO         | Indices Principales               | Ventana Optima
----------------|-----------------------------------|---------------
Cana de azucar  | NDRE, MTCI, kNDVI, S2REP, CCCI   | Mayo-Sept (elongacion)
Soja            | NDVI, NDRE, OSAVI, CCCI, NDMI     | Ene-Abr (R3-R6)
Maiz / Sorgo    | kNDVI, NDRE, EVI, MTCI, S2REP     | Ene-Abr (VT-R1)
Trigo / Cebada  | NDVI, NDRE, GNDVI, LAI            | Jul-Oct (encañazon-llenado)
Arroz           | NDVI, NDRE, EVI, LSWI             | Dic-Abr (macollaje-floracion)
Girasol         | NDVI, NDRE, EVI2, NDMI, NBR2      | Feb-May (R1-R4)
Horticolas      | NDVI, GNDVI, OSAVI, BSI           | Variable (parcelas pequeñas)
Frutales        | NDVI, kNDVI, NDRE, NDMI, S2REP    | Todo el año (perenne)
```

---

## 3. SERIES TEMPORALES Y SEGUIMIENTO FENOLOGICO

### 3.1 Construccion de Serie Temporal NDVI/NDRE

```javascript
// GEE: Serie temporal multi-indice para un lote
var geometry = ee.Geometry.Polygon([...]);
var start = '2024-01-01';
var end = '2026-03-29';

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(geometry)
  .filterDate(start, end)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .map(function(img) {
    var ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI');
    var ndre = img.normalizedDifference(['B8A', 'B5']).rename('NDRE');
    var evi = img.expression(
      '2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))',
      {NIR: img.select('B8'), RED: img.select('B4'), BLUE: img.select('B2')}
    ).rename('EVI');
    var ndmi = img.normalizedDifference(['B8A', 'B11']).rename('NDMI');
    return img.addBands([ndvi, ndre, evi, ndmi])
      .copyProperties(img, ['system:time_start']);
  });

// Extraer valores medios por fecha
var timeSeries = s2.map(function(img) {
  var stats = img.select(['NDVI', 'NDRE', 'EVI', 'NDMI'])
    .reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: geometry,
      scale: 10,
      bestEffort: true
    });
  return ee.Feature(null, stats).set('date', img.date().format('YYYY-MM-dd'));
});

Export.table.toDrive({
  collection: timeSeries,
  description: 'serie_temporal_indices',
  fileFormat: 'CSV'
});
```

### 3.2 Deteccion de Etapas Fenologicas desde Serie Temporal

```
ETAPA              | Señal en NDVI/NDRE                    | Deteccion
-------------------|---------------------------------------|----------
Emergencia         | NDVI cruza 0.15 ascendente            | Threshold crossing
Cierre canopy      | NDVI > 0.6 estable                    | Plateau detection
Maxima biomasa     | Pico de NDVI (derivada = 0)           | Local maximum
Inicio senescencia | NDVI desciende >10% desde pico        | Slope change
Madurez fisiologica| NDRE cae mientras PSRI sube           | Crossover detection
Cosecha            | Caida abrupta NDVI >50% en <15 dias   | Breakpoint detection
```

### 3.3 Suavizado y Gap-Filling

```
Metodo                | Descripcion                           | Precision
----------------------|---------------------------------------|----------
Savitzky-Golay        | Filtro polinomico local               | R2=0.92
Whittaker smoother    | Penalizacion de suavidad adaptativa   | R2=0.94
Gaussian Process (GP) | Regresion bayesiana no-parametrica     | R2=0.96
HANTS                 | Harmonic Analysis of Time Series      | R2=0.91
S1+S2 fusion          | SAR llena gaps opticos por nubes      | Mejor cobertura
```

---

## 4. DETECCION DE ESTRES HIDRICO

### 4.1 Indices de Estres Hidrico desde Sentinel-2

```
Indice | Formula                    | Deteccion
-------|----------------------------|----------
NDMI   | (B8A-B11)/(B8A+B11)       | Contenido agua foliar (-0.2 = seco, 0.5 = humedo)
MSI    | B11/B8A                    | Estres hidrico (alto = mas estres)
NBR2   | (B11-B12)/(B11+B12)       | Agua en tejidos + rastrojo
NMDI   | (B8A-B11+B12)/(B8A+B11-B12)| Diferencia de humedad normalizada
```

### 4.2 CWSI — Crop Water Stress Index (Termica)

```
CWSI = (Tc - Twet) / (Tdry - Twet)

Donde:
  Tc   = Temperatura canopy (sensor termico: Landsat B10, drones, ECOStress)
  Twet = Temperatura referencia con riego optimo
  Tdry = Temperatura referencia sin transpiracion

Rango: 0 (sin estres) a 1 (estres maximo)
Umbral: CWSI > 0.4 → riego urgente
Fuentes satelite: ECOSTRESS (70m), Landsat-8/9 TIRS (100m), ASTER (90m)
Futuro: TRISHNA (ESA/ISRO, 50m, 2026+), SBG (NASA, 60m)
```

### 4.3 Evapotranspiracion Satelital (ET)

```
Modelos operacionales:
- METRIC/SEBAL: Balance energetico superficial, ET pixel-by-pixel
- SSEBop: Simplified Surface Energy Balance, MODIS+Landsat
- OpenET: Plataforma multi-modelo, EE.UU., 30m resolucion
- TSEB: Two-Source Energy Balance (suelo + vegetacion separados)

ET = Rn - G - H   (balance energetico)
Donde: Rn=radiacion neta, G=flujo suelo, H=calor sensible, ET=latente
```

---

## 5. ESTRES NUTRICIONAL Y FERTILIZACION VARIABLE

### 5.1 Deteccion de Deficiencia de Nitrogeno

```
Indice  | Sensibilidad a N | Saturacion | Precision (R2)
--------|-----------------|-----------|---------------
NDRE    | Alta             | LAI > 7   | 0.78-0.88
MTCI    | Muy alta (lineal)| No satura | 0.82-0.90
CCCI    | Alta (normalizado)| No satura | 0.75-0.85
CIre    | Alta             | LAI > 6   | 0.72-0.80
NDVI    | Baja (satura)    | LAI > 3-4 | 0.45-0.60
```

**NDRE explica hasta 88% de la variacion en N foliar** (mejor que NDVI que solo explica ~50%).

### 5.2 Mapas VRT (Variable Rate Technology) desde Satelite

```
Flujo: Imagen S2 → Calcular NDRE → Clasificar zonas → Prescripcion VRT

1. Adquirir imagen Sentinel-2 (10-15 dias despues de fertilizacion base)
2. Calcular NDRE por pixel (20m resolucion nativa, sharpened a 10m)
3. Clasificar en 3-5 zonas de vigor:
   NDRE < 0.25 → Zona critica (dosis alta N)
   NDRE 0.25-0.40 → Zona baja (dosis media-alta)
   NDRE 0.40-0.55 → Zona media (dosis estandar)
   NDRE > 0.55 → Zona alta (reducir dosis)
4. Asignar dosis N por zona segun curva de respuesta del cultivo
5. Exportar shapefile/ISOBUS para aplicador de tasa variable

Resultado tipico: reduccion 10-15% de N total sin afectar rendimiento
```

### 5.3 GEE Script: Mapa NDRE para Prescripcion

```javascript
// GEE: Mapa NDRE + clasificacion para VRT
var lote = ee.Geometry.Polygon([...]);
var fecha = '2026-02-15';

var img = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(lote)
  .filterDate(ee.Date(fecha).advance(-10, 'day'), ee.Date(fecha).advance(10, 'day'))
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
  .map(maskS2clouds)
  .median()
  .clip(lote);

var ndre = img.normalizedDifference(['B8A', 'B5']).rename('NDRE');

// Clasificar en zonas VRT
var zonas = ee.Image(0)
  .where(ndre.lt(0.25), 1)    // Critica
  .where(ndre.gte(0.25).and(ndre.lt(0.40)), 2)  // Baja
  .where(ndre.gte(0.40).and(ndre.lt(0.55)), 3)  // Media
  .where(ndre.gte(0.55), 4)   // Alta
  .rename('VRT_zone');

Export.image.toDrive({
  image: zonas,
  description: 'VRT_NDRE_zonas',
  region: lote,
  scale: 10,
  crs: 'EPSG:4326'
});
```

---

## 6. DETECCION TEMPRANA DE ENFERMEDADES Y PLAGAS

### 6.1 Firmas Espectrales de Estres Biotico

```
Tipo Estres          | Bandas Afectadas           | Indice Clave
---------------------|---------------------------|-------------
Roya (hongo)         | B5 baja, B4 sube, B3 sube | PRI, NDRE caida
Cercospora           | B6-B7 bajan, B11 sube     | CIre, NDMI
Virus (mosaico)      | B3 sube (amarillamiento)  | GNDVI, YI
Nematodos (raiz)     | NDVI baja local, parches  | NDVI anomalia
Insectos (defoliacion)| B8 baja (menos foliar)   | LAI, EVI caida
Bacterias (marchitez) | B11 sube (deshidratacion) | NDMI, MSI
```

### 6.2 Sistema de Alerta Temprana

```
Pipeline de deteccion:
1. Serie temporal NDVI/NDRE historica (3+ anos) → baseline por pixel
2. Imagen actual → calcular anomalia: Z = (actual - media) / stddev
3. Threshold: |Z| > 2.0 → anomalia significativa
4. Clustering espacial: agrupar pixeles anomalos contiguos
5. Clasificacion: comparar patron con firmas conocidas
6. Alerta: generar reporte con ubicacion, area, severidad

Tecnologias:
- Sentinel-2 (5 dias revisita) → deteccion visual
- Sentinel-1 SAR (6 dias) → deteccion estructural (marchitez)
- Drones multiespectral → confirmacion a <1cm/px
- Taranis (Israel): 0.3mm/px aereo + TF/ML → deteccion nivel hoja
```

### 6.3 Deteccion Temprana con Hiperespectral (2025+)

```
Plataforma       | Resolucion | Bandas   | Capacidad
-----------------|-----------|---------|----------
EnMAP (DLR)      | 30m       | 232     | Componentes bioquimicos
PRISMA (ASI)     | 30m       | 250     | Clorofila, carotenoides, agua
FLEX (ESA, 2026) | 300m      | SIF     | Fotosintesis directa
Drones HSI       | <1cm      | 200-400 | Deteccion pre-sintomatica

HSI detecta enfermedades 7-14 dias ANTES de que aparezcan sintomas visibles.
~50% de granjas usando IA para deteccion reportan menor uso de pesticidas.
```

---

## 7. SIF — FLUORESCENCIA SOLAR INDUCIDA

### 7.1 Concepto

```
SIF = señal luminosa emitida por la clorofila durante la fotosintesis
     (680-740 nm, ~1-5% de la luz absorbida)

Ventaja vs NDVI:
- NDVI mide ESTRUCTURA del canopy (cuanta hoja hay)
- SIF mide FUNCION fotosintetica real (cuanto esta trabajando la planta)
- SIF detecta estres ANTES de que cambie la estructura (NDVI)
```

### 7.2 Plataformas Satelitales SIF

```
Plataforma | Resolucion  | Revisita | Estado
-----------|------------|---------|-------
TROPOMI    | 7x3.5 km  | Diario  | Operacional (desde 2018)
OCO-2/3    | 1.25x2.25 km| 16 dias| Operacional
FLEX (ESA) | 300m       | 2-3 dias| Lanzamiento 2026
GOSAT-2    | 10 km      | 3 dias  | Operacional

Downscaling: TROPOMI SIF → 500m con ML (TroDSIF dataset)
```

### 7.3 SIF y Productividad Agricola

```
SIF correlaciona fuertemente con GPP (Gross Primary Production):
- Maiz: R2 = 0.89 (TROPOMI SIF vs GPP)
- Soja: R2 = 0.86 (county-level)
- SIF detecta estres hidrico 2-5 dias antes que NDVI
- SIF captura variabilidad diurna de fotosintesis
```

---

## 8. FUSION SAR + OPTICO — MONITOREO ALL-WEATHER

### 8.1 Sentinel-1 SAR para Agricultura

```
Sentinel-1 (C-band SAR, 5.4 GHz):
- Penetra nubes, funciona dia/noche
- Polarizaciones: VV (vertical-vertical), VH (vertical-horizontal)
- Resolucion: 10m (IW mode)
- Revisita: 6 dias (constelacion)

Indices SAR:
RVI = 4*VH / (VV+VH)     → Rango 0-1, vegetacion densa
DpRVI = sqrt(1-m) * RVI   → Biomasa, agua vegetal, fenologia
VH/VV ratio               → Estructura canopy
```

### 8.2 Estrategia de Fusion

```
OPTICO (Sentinel-2):
  Mejor para: emergencia, cierre canopy, senescencia, clorofila
  Limitacion: nubes bloquean señal

SAR (Sentinel-1):
  Mejor para: floracion, biomasa estructural, periodos nublados, cosecha
  Limitacion: no mide clorofila directamente

FUSION S1+S2:
  - Transformer S1+S2 → GAI retrieval R2=0.88
  - Clasificacion fusionada → 94% OA
  - SAR adelanta deteccion de soja en ~20 dias
  - NDVI time series con gap-filling SAR: cobertura >95% temporal
```

### 8.3 GEE: Fusion S1+S2

```javascript
// GEE: Serie temporal fusionada S1+S2
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(geometry).filterDate(start, end)
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .select(['VV', 'VH']);

// RVI radar
var s1rvi = s1.map(function(img) {
  var vv = ee.Image(10).pow(img.select('VV').divide(10));
  var vh = ee.Image(10).pow(img.select('VH').divide(10));
  return vh.multiply(4).divide(vv.add(vh)).rename('RVI')
    .copyProperties(img, ['system:time_start']);
});

// Combinar NDVI optico + RVI radar en una sola serie
var combined = s2ndvi.merge(s1rvi).sort('system:time_start');
```

---

## 9. PREDICCION DE RENDIMIENTO

### 9.1 Modelos ML con Satelite (2025)

```
Modelo                | R2   | nRMSE | Datos
----------------------|------|-------|------
Random Forest         | 0.91 | 10.2% | S1+S2 multi-temporal
TCN (Temporal Conv.)  | 0.93 | 8.5%  | S2 time series
LSTM                  | 0.87 | 12.1% | S2 + meteo
CNN + LSTM            | 0.90 | 9.8%  | S2 multi-temporal + DEM
Hybrid CGM-ML (DSSAT) | 0.94 | 7.2%  | S2 LAI asimilado
```

### 9.2 Variables Predictoras Clave

```
Prioridad | Variable              | Fuente
----------|----------------------|--------
1         | NDVI time series     | Sentinel-2
2         | GNDVI / LAI peak     | Sentinel-2
3         | NDRE acumulado       | Sentinel-2
4         | Precipitacion        | ERA5 / CHIRPS
5         | Temperatura media    | ERA5
6         | VH SAR backscatter   | Sentinel-1
7         | NDMI stress events   | Sentinel-2
8         | Elevacion / TWI      | DEM Copernicus
```

### 9.3 Ventanas de Prediccion Optimas

```
Cultivo | Ventana Critica        | Meses antes cosecha | Predictor clave
--------|------------------------|--------------------|-----------------
Trigo   | Encañazon-espigado     | 2-3 meses          | GNDVI, LAI
Maiz    | V12-R1 (pre-floracion) | 2-3 meses          | kNDVI, EVI
Soja    | R3-R5 (llenado)        | 1-2 meses          | NDVI, NDRE
Cana    | Gran crecimiento       | 3-4 meses          | NDRE, MTCI
Arroz   | Floracion-llenado      | 1-2 meses          | EVI, LSWI
```

---

## 10. ASIMILACION DE DATOS EN MODELOS DE CULTIVO

### 10.1 Flujo de Asimilacion

```
                  Sentinel-2
                     |
              LAI retrieval (S2 → LAI via SNAP/PROSAIL)
                     |
              +------v------+
              | Asimilacion  |  (EnKF, 4DVar, GLUE, MCMC)
              +------+------+
                     |
    +----------------v----------------+
    |    Modelo de Cultivo (DSSAT)    |
    |    CERES-Maize / CROPGRO-Soya  |
    +----------------+----------------+
                     |
              Rendimiento predicho
              (error < 5% vs medido)
```

### 10.2 Resultados de Asimilacion (2025-2026)

```
Modelo | Variable Asimilada | Cultivo | Reduccion Error
-------|-------------------|---------|----------------
DSSAT  | LAI + LNA         | Soja    | 40-52% → 5%
DSSAT  | LAI (drone)       | Algodon | 40% → 5%
APSIM  | LAI + SM           | Trigo   | 35% → 8%
WOFOST | LAI (S2)          | Maiz    | 25% → 10%
SAFY   | fAPAR (S2)        | Trigo   | 30% → 7%
```

---

## 11. SISTEMAS OPERACIONALES GLOBALES

### 11.1 USDA CropScape / CDL (Estados Unidos)

```
Sistema: Cropland Data Layer (CDL) — USDA NASS
URL: https://nassgeodata.gmu.edu/CropScape/
Resolucion: 10m (desde 2024, antes 30m)
Cobertura: EE.UU. continental
Actualizacion: Anual (release Feb siguiente)
Clasificador: Random Forest en GEE (desde 2024)
Clases: >100 tipos de cultivo
Acceso: Gratuito, descarga via CropScape o GEE
```

### 11.2 Copernicus (Europa)

```
HR-VPP: High Resolution Vegetation Phenology & Productivity
  - 10m resolucion (Sentinel-2)
  - Fenologia: SOS, POS, EOS, LOS (inicio/pico/fin temporada)
  - Productividad: TPROD, SPROD (total y estacional)
  - Cobertura: Pan-Europa

Crop Monitoring (MARS/JRC):
  - Boletines cada 10 dias
  - Prediccion rendimiento por cultivo/pais
  - Modelos: WOFOST + satelite + meteo
```

### 11.3 Otros Sistemas

```
Sistema         | Pais/Region  | Especializacion
----------------|-------------|----------------
GeoGLAM/AMIS    | Global      | Seguridad alimentaria, G20
GEOGLAM Crop Monitor | Global | Alertas tempranas cultivos
FEWS NET        | Africa/Asia | Hambruna y sequia
CONAB (Brasil)  | Brasil      | Safra estimaciones
JRC MARS        | Europa      | Rendimiento por cultivo
CSIRO/BOM       | Australia   | Sequía y rendimiento
```

---

## 12. TECNOLOGIAS ISRAEL Y REFERENTES MUNDIALES

### 12.1 Empresas AgriTech Israel (Lideres Teledeteccion)

```
Empresa     | Tecnologia                         | Escala        | Diferenciador
------------|-----------------------------------|--------------|---------------
Taranis     | Imagenes 0.3mm/px avion + ML       | 20M+ acres   | 500M+ datapoints, deteccion hoja
CropX       | Sensores suelo + satelite + weather | Global       | Microclima, fusion multi-dato
SupPlant    | Sensores planta + IA irrigacion     | Global       | Riego personalizado sin sensores
SeeTree     | ML por arbol individual, drones     | 500M+ arboles| Citrus, palta, palma
Prospera    | Computer vision in-field            | Global       | Deteccion temprana estres
Phytech     | Sensores fisiologicos planta        | Global       | Monitoreo tiempo real
```

### 12.2 Volcani Center (Israel)

```
Agricultural Research Organization (ARO):
- 200 cientificos, 75% de investigacion agricola de Israel
- Depto. Sensing & Mechanical Systems: UAV RS, termica, NIR, GIS
- Investigacion: crop mapping S2, fusion hiperespectral EnMAP+PRISMA
- Papers recientes: estimacion parametros cultivo fusionando EnMAP+S2

TECHNION: CEAR Lab — robots aereos/terrestres en huertos
HEBREW UNIVERSITY: Fenotipado remoto, analisis espectral
```

### 12.3 Referentes USA

```
Institucion         | Especializacion
--------------------|--------------------
NASA ACRES          | Capacitacion RS agricola, ARSET
USDA ARS            | Investigacion agricola, sensores proximales
University of Maryland | Crop monitoring global, GLAM
University of Nebraska | Irrigacion, ET, crop modeling
Michigan State       | Crop classification, deep learning
Iowa State           | Precision agriculture, N management
```

---

## 13. GEE SCRIPTS DE MONITOREO

### 13.1 Script Completo: Dashboard de Monitoreo por Lote

```javascript
// ===== PIXADVISOR: Monitoreo de Cultivo — GEE Script Completo =====
// Input: poligono del lote, rango de fechas
// Output: serie temporal multi-indice + mapa de vigor + anomalias

var lote = ee.Geometry.Polygon([
  [-63.18, -17.78], [-63.17, -17.78],
  [-63.17, -17.77], [-63.18, -17.77],
  [-63.18, -17.78]
]);

var startDate = '2025-01-01';
var endDate = '2026-03-29';

// 1. Coleccion filtrada y enmascarada
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(lote)
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds);

// 2. Calcular indices
var withIndices = s2.map(function(img) {
  var b4 = img.select('B4').divide(10000);
  var b5 = img.select('B5').divide(10000);
  var b6 = img.select('B6').divide(10000);
  var b8 = img.select('B8').divide(10000);
  var b8a = img.select('B8A').divide(10000);
  var b11 = img.select('B11').divide(10000);

  var ndvi = b8.subtract(b4).divide(b8.add(b4)).rename('NDVI');
  var ndre = b8a.subtract(b5).divide(b8a.add(b5)).rename('NDRE');
  var ndmi = b8a.subtract(b11).divide(b8a.add(b11)).rename('NDMI');
  var mtci = b6.subtract(b5).divide(b5.subtract(b4).max(0.001)).rename('MTCI');

  return img.addBands([ndvi, ndre, ndmi, mtci])
    .copyProperties(img, ['system:time_start']);
});

// 3. Serie temporal
var ts = withIndices.map(function(img) {
  var means = img.select(['NDVI','NDRE','NDMI','MTCI'])
    .reduceRegion({reducer: ee.Reducer.mean(), geometry: lote, scale: 10, bestEffort: true});
  return ee.Feature(null, means)
    .set('date', img.date().format('YYYY-MM-dd'))
    .set('system:time_start', img.get('system:time_start'));
});

// 4. Mapa de vigor actual (ultimo mes)
var recent = withIndices.filterDate(
  ee.Date(endDate).advance(-30, 'day'), endDate
).median().clip(lote);

// 5. Anomalia: comparar ultimo mes vs historico
var historico = withIndices.filterDate(
  ee.Date(startDate), ee.Date(endDate).advance(-30, 'day')
);
var meanHist = historico.select('NDVI').mean();
var stdHist = historico.select('NDVI').reduce(ee.Reducer.stdDev());
var anomalia = recent.select('NDVI').subtract(meanHist)
  .divide(stdHist.max(0.01)).rename('anomalia_z');

// Visualizar
Map.centerObject(lote, 15);
Map.addLayer(recent.select('NDVI'), {min: 0, max: 0.9, palette: ['red','yellow','green']}, 'NDVI actual');
Map.addLayer(anomalia, {min: -3, max: 3, palette: ['red','white','blue']}, 'Anomalia Z-score');

// Exportar
Export.table.toDrive({collection: ts, description: 'monitoreo_serie_temporal', fileFormat: 'CSV'});
Export.image.toDrive({image: anomalia, description: 'mapa_anomalia', region: lote, scale: 10});
```

---

## 14. FLUJO DE TRABAJO END-TO-END

### 14.1 Pipeline Completo de Monitoreo

```
SEMANA 1-2: CONFIGURACION
  └─ Definir poligonos de lotes (GeoJSON/KML)
  └─ Configurar coleccion S2 + S1 en GEE
  └─ Definir calendario fenologico del cultivo

CADA 5 DIAS: MONITOREO AUTOMATICO
  └─ Descargar ultima imagen S2 disponible
  └─ Calcular indices (NDVI, NDRE, NDMI, MTCI, EVI)
  └─ Actualizar serie temporal
  └─ Comparar con baseline historico → Z-score
  └─ Clasificar: Normal / Alerta / Critico
  └─ Generar mapa de vigor + anomalias

MENSUAL: ANALISIS PROFUNDO
  └─ Mapa de estres hidrico (NDMI + CWSI si termica disponible)
  └─ Mapa de estres nutricional (NDRE → zonas VRT)
  └─ Deteccion de anomalias espaciales (clusters)
  └─ Comparacion inter-lotes (ranking)

ESTACIONAL: PREDICCION
  └─ Asimilar LAI en modelo DSSAT/APSIM
  └─ Predecir rendimiento con ML (RF/TCN)
  └─ Generar reporte de productividad por zona

POST-COSECHA: EVALUACION
  └─ Comparar rendimiento predicho vs real
  └─ Calibrar modelos para proxima temporada
  └─ Generar zonas de manejo para siguiente ciclo
```

---

*Skill creado: 2026-03-29 | v1.0 | Basado en: ESA Sentinel Hub, USDA NASS CropScape, Copernicus HR-VPP, NASA ACRES/OCO-2, TROPOMI SIF, Volcani/ARO Israel, Taranis, CropX, MDPI Remote Sensing 2023-2026, Frontiers Agronomy, ScienceDirect crop monitoring reviews 2025, Nature Scientific Data, IEEE Xplore, GEE documentation*

Sources:
- [Sentinel-2 Crop Maps Israel (MDPI)](https://www.mdpi.com/2072-4292/13/17/3488)
- [EnMAP+S2 Fusion Crop Traits](https://www.tandfonline.com/doi/abs/10.1080/01431161.2026.2612849)
- [Sentinel-2 Precision Agriculture Features](https://www.mdpi.com/2073-4395/10/5/641)
- [Potato Phenology S1+S2 Synergy](https://www.mdpi.com/2072-4292/17/14/2336)
- [Sentinel-2 LAI fAPAR Bulgaria](https://www.tandfonline.com/doi/full/10.1080/22797254.2020.1839359)
- [NDVI Time Series Fusion S1+S2](https://www.sciencedirect.com/science/article/abs/pii/S0168169923007767)
- [Crop Disease Detection Review (ScienceDirect 2025)](https://www.sciencedirect.com/science/article/pii/S2095809925006769)
- [Hyperspectral Imaging Agriculture 2025](https://farmonaut.com/remote-sensing/hyperspectral-imaging-in-agriculture-market-2025-advances)
- [AI Crop Yield Sentinel-2 Survey](https://www.mdpi.com/2071-1050/16/18/8277)
- [DSSAT LAI Assimilation Soybean](https://www.mdpi.com/2072-4292/18/3/443)
- [DSSAT Crop Modeling Ecosystem](https://dssat.net/wp-content/uploads/2025/04/The-DSSAT-Crop-Modeling-Ecosystem.pdf)
- [USDA CDL 10m Resolution](https://www.nature.com/articles/s41597-026-07099-1)
- [TROPOMI SIF Downscaled 500m](https://www.nature.com/articles/s41597-024-04325-6)
- [OCO-2 SIF Photosynthesis](https://www.science.org/doi/10.1126/science.aam5747)
- [NDRE vs NDVI for N Management](https://eos.com/blog/ndvi-vs-ndre/)
- [CWSI Sugarcane Irrigation](https://www.researchgate.net/publication/316914436)
- [Deep Learning Crop Monitoring Review](https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1636898/full)
