---
name: gis-precision-agro
description: >
  Super skill profesional de GIS para Agricultura de Precisión. Cubre zonas de manejo
  (Ambientes Productivos), Unidades de Gestión Individual (UGDs), índices de vegetación
  específicos por cultivo y etapa fenológica, identificación de cultivos por firma
  espectral, detección de malezas con algoritmos modernos, detección de fallas de
  plantio, y restitución de líneas en caña de azúcar.
  
  USAR cuando el usuario mencione: zonas de manejo, UGDs, ambientes productivos,
  índices de vegetación NDVI/NDRE/EVI/SAVI/MSAVI/kNDVI/MCARI/IRECI, firma espectral,
  clasificación de cultivos, detectar malezas, fallas de plantio, restitución de
  líneas de caña, segmentación SNIC, score compuesto, análisis de estabilidad temporal,
  Sentinel-2, Sentinel-1 SAR, RVI radar, fusion SAR-óptico, GEE Google Earth Engine,
  scripts Python GIS, shapefile, geopandas, rasterio, orthomosaic drones, detección
  de gaps, tasas de replantio, foundation models Prithvi AgriFM Clay SAM, kNDVI,
  CWSI estrés hídrico, térmica, suelo remoto BSI SOC, SIF fluorescencia, VRT
  prescripción, o cualquier tarea avanzada de percepción remota agrícola.
---

# 🛰️ GIS Agricultura de Precisión — Super Skill PRO

> **Rol**: Ingeniero GIS + Agrónomo Senior + Especialista en Percepción Remota Agrícola
> **Nivel**: Expert / Research-grade methodology  
> **Stack**: Python (GEE, geopandas, rasterio, scikit-learn, scipy), QGIS, Sentinel-2, UAV multispectral

---

## 📚 TABLA DE CONTENIDOS

Este skill se organiza en módulos. Leer la sección relevante:

| # | Módulo | Trigger principal |
|---|--------|-------------------|
| 1 | [Zonas de Manejo y UGDs](#1-zonas-de-manejo-y-ugds) | "zonas de manejo", "ambientes productivos", "UGD" |
| 2 | [Índices de Vegetación por Cultivo/Fenología](#2-índices-de-vegetación-por-cultivo-y-etapa-fenológica) | "índice", "NDVI", "NDRE", "qué índice usar" |
| 3 | [Firmas Espectrales e Identificación de Cultivos](#3-firmas-espectrales-e-identificación-de-cultivos) | "firma espectral", "identificar cultivo", "clasificar" |
| 4 | [Detección de Malezas](#4-detección-de-malezas) | "maleza", "weed", "herbicida sitio-específico" |
| 5 | [Fallas de Plantio y Restitución Caña](#5-fallas-de-plantio-y-restitución-de-líneas-caña-de-azúcar) | "falla", "gap", "restitución", "stand" |
| 6 | [GEE — Flujos de trabajo](#6-google-earth-engine--flujos-de-trabajo) | "GEE", "Earth Engine", "Sentinel-2 script" |
| 7 | [Salidas y Formatos](#7-salidas-y-formatos-gis) | "exportar", "shapefile", "mapa" |
| 8 | [Índices Avanzados 2025+](#8-índices-avanzados-2025) | "kNDVI", "MCARI", "IRECI", "PRI", "BSI", "SMI" |
| 9 | [SAR Sentinel-1 y Fusión](#9-sar-sentinel-1-y-fusión-óptico-radar) | "SAR", "Sentinel-1", "RVI radar", "fusión" |
| 10 | [Foundation Models e IA](#10-foundation-models-e-ia-para-agricultura) | "Prithvi", "AgriFM", "SAM", "ViT", "deep learning" |
| 11 | [Teledetección Suelo, Rendimiento y Estrés](#11-teledetección-suelo-rendimiento-y-estrés) | "SOC", "CWSI", "SIF", "yield", "nutriente" |
| 12 | [Tecnologías Israel y Referentes Globales](#12-tecnologías-israel-y-referentes-globales) | "Taranis", "CropX", "SeeTree", "Israel agritech" |

---

## 1. ZONAS DE MANEJO Y UGDs

### 1.1 Definiciones Operativas

| Concepto | Definición práctica | Escala típica |
|----------|--------------------|--------------------|
| **Ambiente Productivo** | Unidad espacial homogénea en rendimiento histórico, suelo y topografía | 3–20 ha |
| **Zona de Manejo** | Subzona dentro de un lote con manejo diferenciado (fertilización VRT, muestreo) | 1–10 ha |
| **UGD** (Unidad de Gestión Individual) | Zona de mayor resolución: cada punto/subzona con ID único para seguimiento multitemporal | 0.5–3 ha |

### 1.2 Metodología de Zonificación — Score Compuesto Ponderado

#### Variables de entrada (capas)
```
CAPA               FORMULA                                      PESO RECOMENDADO
─────────────────────────────────────────────────────────────────────────────────
NDVI mediana       (B8-B4)/(B8+B4)                              0.25 (vigor largo plazo)
NDRE mediana       (B8-B5)/(B8+B5)                              0.15 (clorofila/N)
Estabilidad NDVI   1 - desvio_std_NDVI_normalizado              0.15 (consistencia)
TWI                ln(acc * cellsize / tan(slope + 0.001))      0.10 (humedad)
Flujo (inv.)       1 - flow_accum_normalizado                   0.10 (drenaje)
Pendiente (inv.)   1 - slope_normalizado                        0.10 (laboreo)
Elevación rel.     elevacion_relativa_dentro_lote               0.05
Dist. drenaje      distancia_a_linea_drenaje_normalizada        0.10
─────────────────────────────────────────────────────────────────────────────────
TOTAL                                                           1.00
```

#### Regla de número de zonas por área
```python
def get_num_zones(area_ha, config_zones=4):
    if area_ha < 10:    min_zones = 2
    elif area_ha < 30:  min_zones = 3
    elif area_ha < 60:  min_zones = 4
    elif area_ha < 100: min_zones = 4
    else:               min_zones = 5
    return max(min_zones, config_zones)
```

#### Clasificación por percentiles
```python
# 4 zonas (el caso más común)
cuts = np.percentile(score[mask], [25, 50, 75])
zonas = np.digitize(score, cuts) + 1
# Resultado: Zona 1=Baja, 2=Media-Baja, 3=Media-Alta, 4=Alta
```

### 1.3 Atributos obligatorios de salida (shapefile de zonas)

```
zona          : int   (1..N)
clase         : str   ("Baja" | "Media-Baja" | "Media-Alta" | "Alta")
area_ha       : float
porcentaje    : float (% del lote)
ndvi_prom     : float
ndre_prom     : float
twi_prom      : float
elevacion_prom: float
pendiente_prom: float
score_prom    : float
```

### 1.4 Puntos de Muestreo — Farthest Point Sampling (FPS)

**NO usar centroide simple.** Algoritmo correcto:

```python
def farthest_point_sampling(polygon, n_points, seed_point=None):
    """Maximiza cobertura espacial dentro del polígono."""
    # 1. Generar candidatos en grilla
    spacing = math.sqrt(polygon.area / 50)
    candidates = grid_points_in_polygon(polygon, spacing)
    
    # 2. Punto inicial = representative_point()
    selected = [seed_point or polygon.representative_point()]
    
    # 3. Cada siguiente = max distancia mínima a ya seleccionados
    while len(selected) < n_points:
        dists = [min(p.distance(s) for s in selected) for p in candidates]
        next_pt = candidates[np.argmax(dists)]
        selected.append(next_pt)
        candidates.remove(next_pt)
    
    return selected
```

**Regla de densidad de muestreo:**
- Zona < 3 ha → 1 principal + 5 submuestras
- Zona 3–10 ha → 1 principal + 7 submuestras
- Zona 10–20 ha → 1 principal + 10 submuestras
- Zona > 20 ha → 2 principales + 8 submuestras c/u

**Nomenclatura:** `{PREFIJO}-Z{zona}-P{n}` (principal) / `{PREFIJO}-Z{zona}-S{n}` (submuestra)

---

## 2. ÍNDICES DE VEGETACIÓN POR CULTIVO Y ETAPA FENOLÓGICA

### 2.1 Tabla Maestra de Índices

| Índice | Fórmula (Sentinel-2) | Rango útil | Mejor uso |
|--------|----------------------|------------|-----------|
| **NDVI** | (B8-B4)/(B8+B4) | -1 a 1 | Vigor general, emergencia–madurez |
| **NDRE** | (B8-B5)/(B8+B5) | -1 a 1 | Clorofila/N, media-tardía del ciclo |
| **GNDVI** | (B8-B3)/(B8+B3) | -1 a 1 | Clorofila, canopeo cerrado |
| **EVI** | 2.5*(B8-B4)/(B8+6*B4-7.5*B2+1) | -1 a 1 | Canopeos densos (LAI alto) |
| **SAVI** | 1.5*(B8-B4)/(B8+B4+0.5) | -1 a 1 | Suelo expuesto parcial |
| **MSAVI2** | 0.5*(2*B8+1 - sqrt((2*B8+1)²-8*(B8-B4))) | -1 a 1 | **Emergencia, suelo expuesto** |
| **NDWI** | (B3-B8)/(B3+B8) | -1 a 1 | Agua libre, humedad suelo |
| **NDMI** | (B8A-B11)/(B8A+B11) | -1 a 1 | Estrés hídrico del canopeo |
| **LSWI** | (B8A-B11)/(B8A+B11) | -1 a 1 | Agua foliar, floración/encañado |
| **CIre** | (B8/B5)-1 | 0 a 10 | Clorofila Red-Edge, macollamiento |
| **NDVI705** | (B6-B5)/(B6+B5) | -1 a 1 | Cultivos con canopeo denso |
| **PSRI** | (B4-B2)/B6 | varies | Senescencia, madurez/cosecha |

> **Fuentes**: Auravant (2024), Alabama Ext. (2025), Remote Sensing MDPI rev. (2023), GEE catalog

### 2.2 Selección por CULTIVO y ETAPA

#### 🌾 CAÑA DE AZÚCAR

| Etapa fenológica | Días aprox. | Índices prioritarios | Alerta |
|-----------------|-------------|----------------------|--------|
| Brotación/Emergencia | 0–30 DAP | **MSAVI2**, NDVI | Fallas de plantio |
| Macollamiento/Ahijamiento | 30–120 DAP | **NDRE**, CIre, NDVI | Deficiencia N |
| Elongación/Grand Growth | 120–270 DAP | **NDVI**, EVI, **NDMI** | Estrés hídrico |
| Maduración/Ripening | 270–360 DAP | **PSRI**, NDVI dec. | Timing cosecha |
| Ratoon (rebrote) | 0–60 DAR | **MSAVI2**, NDRE | Densidad stand |

**Firma espectral caña vs competidores (Sentinel-2):**
- Caña en grand growth: NDVI 0.75–0.90, EVI alto, NDMI alto (0.4–0.7)
- Soja competidora: NDVI similar pero NDRE más bajo
- Maíz: mayor reflectancia en B11 (SWIR) en etapa reproductiva
- **Diferenciador clave**: EVI + NDMI + Blue band (B2) en sept-oct para caña

#### 🌱 SOJA

| Etapa | BBCH/V-R | Índices prioritarios |
|-------|----------|----------------------|
| Emergencia-VE | V0–V1 | MSAVI2, NDVI |
| Vegetativo | V2–V6 | NDVI, SAVI |
| Inicio Reproducción | R1–R2 | **NDRE**, NDVI, EVI |
| Llenado | R3–R6 | NDRE, **NDVI**, NDWI |
| Madurez | R7–R8 | PSRI, NDVI declinante |

#### 🌽 MAÍZ / SORGO

| Etapa | Código | Índices prioritarios |
|-------|--------|----------------------|
| Emergencia | VE | MSAVI2 |
| 3–7 hojas | V3–V7 | NDVI, **CIre** |
| Encañado | V8+ | NDVI, **LSWI**, EVI |
| Floración/Silking | VT/R1 | NDRE, **LSWI** |
| Llenado de grano | R2–R5 | NDVI, NDMI |
| Madurez | R6 | PSRI |

> Referencia científica: Wei et al. (Sentinel-2, 2024) — maíz vs soja se diferencian mejor en **7-hojas** (maíz) / floración (soja), usando NDRE + NDVI combinados.

#### 🌻 GIRASOL / CHÍA / CULTIVOS OLEAGINOSOS

| Etapa | Índices |
|-------|---------|
| Vegetativo | NDVI, SAVI |
| Botón/Floración | **NDRE**, EVI |
| Llenado | NDVI, NDMI |
| Madurez | PSRI, NDVI dec. |

#### 🍅 TOMATE / PIMENTÓN / PAPA (Hortalizas)

| Etapa | Índices prioritarios |
|-------|----------------------|
| Trasplante-prendimiento | MSAVI2, NDVI |
| Desarrollo vegetativo | NDVI, GNDVI |
| Floración-cuaja | **NDRE**, NDVI |
| Llenado-cosecha | NDMI (estrés hídrico), NDVI |

#### 🥑 PALTA / MARACUYÁ (Perennes)

| Aplicación | Índice |
|------------|--------|
| Vigor general | NDVI, GNDVI |
| Estado nutritivo N | NDRE, CIre |
| Estrés hídrico | NDMI, CWSI (thermal) |
| Senescencia/enfermedad | PSRI |

### 2.3 Combinaciones Multíndice por Objetivo

```python
# OBJETIVO: Detección de deficiencia de N (cualquier cultivo)
indices_N = ["NDRE", "CIre", "GNDVI"]  # orden de prioridad

# OBJETIVO: Estrés hídrico
indices_agua = ["NDMI", "LSWI", "NDWI"]

# OBJETIVO: Identificación de cultivo (clasificación)
indices_clasif = ["NDVI", "NDRE", "EVI", "NDMI"]  # + SAR VH/VV si disponible

# OBJETIVO: Detección de maleza
indices_maleza = ["NDVI", "ExG", "MSAVI2"]  # + RGB (ExG = 2G-R-B)

# OBJETIVO: Timing de cosecha caña
indices_cosecha = ["PSRI", "NDVI_temporal", "NDMI"]
```

---

## 3. FIRMAS ESPECTRALES E IDENTIFICACIÓN DE CULTIVOS

### 3.1 Firma Espectral por Cultivo (Sentinel-2 — Reflectancias relativas)

```
BANDA    λ(nm)   CAÑA    SOJA    MAÍZ    GIRASOL  PASTO
─────────────────────────────────────────────────────────────
B2 Blue  490     bajo    bajo    bajo    bajo      bajo
B3 Green 560     medio   medio   medio   medio     medio
B4 Red   665     muy bajo muy bajo muy bajo muy bajo  bajo
B5 RE1   705     medio   medio-alto medio  medio    medio
B6 RE2   740     alto    alto    alto    alto      alto
B7 RE3   783     alto    alto    alto    alto      alto
B8 NIR   842     muy alto muy alto muy alto muy alto  alto
B8A RE4  865     muy alto muy alto muy alto muy alto  alto
B11 SWIR1 1610   bajo-medio medio bajo   bajo      bajo
B12 SWIR2 2190   muy bajo bajo   muy bajo muy bajo  muy bajo
```

**Diferenciadores clave entre cultivos similares:**
- **Caña vs Soja**: B11 (SWIR1) — caña tiene menor reflectancia SWIR durante grand growth
- **Maíz vs Soja**: NDRE más alto en soja; B11 más alto en maíz en reproductivo
- **Pasto vs Caña**: menor NIR/Red Edge en pasto; NDVI < 0.65 usualmente
- **Caña vs Pasto/Brachiaria**: series temporales — caña tiene curva NDVI más sostenida (no estacional corta)

### 3.2 Clasificadores Recomendados por Escenario

| Escenario | Clasificador | Precisión típica | Notes |
|-----------|-------------|-----------------|-------|
| 2–4 cultivos, datos suficientes | **Random Forest** | 85–93% | Robusto, interpreta features |
| Clasificación con pocos datos | **SVM** | 80–88% | Bueno con pocas muestras |
| Múltiples cultivos, deep data | **U-Net / A2SegNet** | 88–95% | Requiere GPU y datos |
| Clasificación temprana en temporada | **RF + serie temporal** | 80–90% | Incluir todas las fechas posibles |
| Caña específicamente | **SVM + RF ensemble** | 83–93% | Combinar NDVI+NDMI+EVI |

### 3.3 Flujo de Clasificación de Cultivos — GEE

```javascript
// ── 1. CARGAR DATOS ────────────────────────────────────────────────
var collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
  .map(maskS2clouds);

// ── 2. CALCULAR ÍNDICES (COMPUESTO MULTITEMPORAL) ──────────────────
function calcIndices(img) {
  var ndvi = img.normalizedDifference(['B8','B4']).rename('NDVI');
  var ndre = img.normalizedDifference(['B8','B5']).rename('NDRE');
  var evi  = img.expression(
    '2.5*((NIR-RED)/(NIR+6*RED-7.5*BLUE+1))',
    {NIR:img.select('B8'),RED:img.select('B4'),BLUE:img.select('B2')}
  ).rename('EVI');
  var ndmi = img.normalizedDifference(['B8A','B11']).rename('NDMI');
  return img.addBands([ndvi, ndre, evi, ndmi]);
}

// ── 3. COMPOSITE MEDIANAS POR PERÍODO FENOLÓGICO ──────────────────
// Período de crecimiento activo (máx discriminación espectral)
var composite = collection.map(calcIndices).median()
  .select(['B2','B3','B4','B5','B6','B8','B8A','B11','NDVI','NDRE','EVI','NDMI']);

// ── 4. MUESTRAS DE ENTRENAMIENTO ──────────────────────────────────
// Punto: añadir propiedad 'clase' (1=caña, 2=soja, 3=maiz, 4=pasto...)
var training = composite.sampleRegions({
  collection: trainingPoints,
  properties: ['clase'],
  scale: 10
});

// ── 5. CLASIFICADOR RF ─────────────────────────────────────────────
var classifier = ee.Classifier.smileRandomForest(100)
  .train(training, 'clase', composite.bandNames());

var classified = composite.classify(classifier);
```

### 3.4 Validación y Métricas

```python
from sklearn.metrics import classification_report, confusion_matrix

# Siempre reportar:
print(classification_report(y_true, y_pred, 
      target_names=['caña','soja','maíz','pasto','suelo']))
# Métricas clave: Precision, Recall, F1-Score, Kappa
# Umbral de calidad mínimo: Kappa > 0.75, OA > 85%
```

---

## 4. DETECCIÓN DE MALEZAS

### 4.1 Algoritmos por Tipo de Sensor y Escala

| Sensor | GSD | Algoritmo recomendado | Precisión típica |
|--------|-----|----------------------|-----------------|
| RGB UAV | 1–5 cm | **YOLOv8** (detección) / **U-Net** (segmentación) | F1 75–90% |
| Multispectral UAV | 5–20 cm | **U-Net + NDVI mask** | F1 80–90% |
| Multispectral UAV | 20–50 cm | U-Net, SegFormer | F1 70–85% |
| Sentinel-2 (10m) | 10 m | RF sobre índices + textura | Detección de infestación (no planta individual) |

> Referencia: Zhang et al., Agronomy 2024; MDPI Drones 2023; ScienceDirect 2025

### 4.2 Índices de Vegetación para Maleza

```python
# Índices que maximizan separación maleza-cultivo:

# ExG (Excess Green) — para RGB: separa vegetación de suelo
ExG = 2*G - R - B  # rango -255 a 510 (normalizar)

# ExGR (ExG - ExR):
ExGR = (2*G - R - B) - (1.4*R - G)

# VARI (Visible Atmospherically Resistant Index) — RGB
VARI = (G - R) / (G + R - B)

# NGRDI (Normalized Green-Red Difference Index)
NGRDI = (G - R) / (G + R)

# Para multispectral:
# NDVI bajo del cultivo en emergencia → maleza más vigorosa visualmente resaltable
# ExGR + NDVI combination → mejor separación cultivo/maleza temprana
```

### 4.3 Flujo Operativo de Detección de Malezas

```
1. ADQUISICIÓN
   ├── Altura vuelo: 10–30 m (GSD 0.5–2 cm)
   ├── Solapamiento: 80% frontal y lateral
   ├── Hora: evitar 11:00-14:00 (sombras, saturación)
   └── Sensor: RGB o MS (MicaSense RedEdge / Parrot Sequoia)

2. PREPROCESAMIENTO
   ├── Ortomosaico: Pix4D / OpenDroneMap
   ├── Corrección radiométrica (si MS)
   ├── Cálculo de índices (NDVI, ExG, ExGR)
   └── Máscara de vegetación (umbral NDVI > 0.2)

3. SEGMENTACIÓN Y CLASIFICACIÓN
   ├── Segmentar por líneas de cultivo (Hough Transform / GA+Radon)
   ├── Dentro de línea: cultivo
   ├── Entre líneas (entresurco): maleza candidata
   ├── Clasificar con U-Net (entrenado localmente o transfer learning)
   └── Post-procesar: eliminar ruido (área < umbral_min)

4. MAPA DE PRESCRIPCIÓN
   ├── Densidad de maleza por píxel → reclasificar en zonas (Alta/Media/Baja)
   ├── Generar shapefile de zonas con atributo densidad
   └── Exportar como prescription map para aplicadora VRT
```

### 4.4 Malezas Comunes por Cultivo — Características Espectrales

| Maleza | Cultivo | Diferenciador espectral |
|--------|---------|-------------------------|
| **Brachiaria** | Caña, Soja | Reflectancia NIR más baja que caña; NDVI < 0.65 en temporada seca |
| **Cyperus** (junco) | Arroz, Maíz | NDRE bajo; B11 (SWIR) característico |
| **Euphorbia** | Soja, Maíz | Hoja más brillante (mayor reflectancia verde) |
| **Amaranthus** | Maíz, Soja | Textura canopeo más rugosa en imagen |
| **Digitaria** | Caña | Altura canopeo diferente → textura rugosidad |

---

## 5. FALLAS DE PLANTIO Y RESTITUCIÓN DE LÍNEAS (CAÑA DE AZÚCAR)

### 5.1 Definición de Falla (Gap)

Según **metodología Stolf** (referencia estándar Brasil):
```
Gap = distancia entre plantas > 1.5× espaciamiento estándar
Gap pequeño: 0.5–1.0 m
Gap mediano: 1.0–3.0 m  
Gap grande: > 3.0 m

% de falhas = Σ(comprimento_gaps) / comprimento_total × 100

Categorización:
< 5%   → Normal, no requiere replantio
5–10%  → Moderado, evaluar replantio selectivo
10–20% → Grave, replantio obligatorio
> 20%  → Muy grave, considerar replantio total
```

### 5.2 Detección de Líneas de Caña — Algoritmos

#### Opción A: Radon Transform + Algoritmo Genético (Silva et al., 2021)
```
1. Preprocesar: ortomosaico RGB, threshold por ExG
2. Radon Transform: detectar ángulo dominante de las líneas
3. Algoritmo Genético: optimizar parámetros de segmentación
4. Output: líneas detectadas como geometrías en imagen
Precisión: ~85% en caña bien establecida
Ventaja: robusto a variaciones de iluminación
```

#### Opción B: Hough Transform (clásico, GSD < 5 cm)
```python
import cv2
import numpy as np

def detect_sugarcane_rows(ortho_path, spacing_m, gsd_m):
    img = cv2.imread(ortho_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Calcular ExG
    b, g, r = cv2.split(img.astype(float))
    exg = 2*g - r - b
    exg_norm = ((exg - exg.min()) / (exg.max() - exg.min()) * 255).astype(np.uint8)
    
    # Threshold y edge
    _, thresh = cv2.threshold(exg_norm, 50, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(thresh, 50, 150)
    
    # Hough probabilístico
    spacing_px = int(spacing_m / gsd_m)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                             threshold=spacing_px//2,
                             minLineLength=spacing_px,
                             maxLineGap=spacing_px//4)
    return lines
```

#### Opción C: Deep Learning CrowNet / U-Net (estado del arte)
```
Input: ortomosaico RGB o MS (512×512 tiles)
Modelo: U-Net con EfficientNetB0 backbone (mejor F1 en literatura)
Output: máscara binaria líneas vs entresurco
Post-proceso: esqueletización → líneas → detección de gaps
Precisión reportada: F1 ~ 88% (similar a sensores MS premium)
```

### 5.3 Algoritmo Completo de Restitución

```python
# ─── PIPELINE DETECCIÓN FALLAS Y RESTITUCIÓN CAÑA ──────────────────

def detect_gaps_and_generate_replanting(
    orthomosaic_path,
    field_boundary_shp,
    row_spacing_m,      # espacio entre líneas (e.g. 1.4 m)
    expected_spacing_m, # espacio entre plantas (e.g. 0.5 m)
    gsd_m               # resolución del ortomosaico
):
    # PASO 1: Detección de líneas
    rows = detect_rows_hough_or_deeplearning(orthomosaic_path, row_spacing_m, gsd_m)
    
    # PASO 2: Perfil de vegetación a lo largo de cada línea
    for row in rows:
        profile = extract_ndvi_profile_along_line(row, orthomosaic_path)
        
        # PASO 3: Detectar gaps (NDVI < threshold por > N píxeles)
        threshold_ndvi = 0.25  # calibrar por cultivo/etapa
        min_gap_px = int(1.5 * expected_spacing_m / gsd_m)
        gaps = find_gaps_in_profile(profile, threshold_ndvi, min_gap_px)
        
        # PASO 4: Clasificar gap por tamaño
        for gap in gaps:
            gap_length_m = gap.length_px * gsd_m
            gap.category = classify_gap(gap_length_m)
            
    # PASO 5: Calcular % falla por lote y zona
    metrics = calculate_gap_metrics(rows, field_boundary_shp)
    
    # PASO 6: Generar mapa de prescripción de replantio
    replanting_map = generate_replanting_shapefile(gaps, metrics)
    
    return replanting_map, metrics
```

### 5.4 Outputs del Análisis de Fallas

```
ARCHIVOS GENERADOS:
├── gaps_detectados.shp          (geometrías de cada gap con atributos)
├── lineas_caña.shp              (líneas detectadas)
├── mapa_densidad_fallas.tif     (raster continuo 0-100%)
├── zonas_replantio.shp          (zonas prioritarias para replantio)
└── reporte_fallas.csv

ATRIBUTOS gaps_detectados.shp:
id_gap, id_linea, longitud_m, categoria, lat, lon, requiere_replantio (bool)

REPORTE ESTADÍSTICO:
- % falla total del lote
- % falla por zona de manejo
- Metros lineales totales de gaps
- Distribución por categoría (pequeño/mediano/grande)
- Recomendación: Replantio / No replantio / Evaluación campo
```

### 5.5 Sensor Óptimo por Etapa (Caña)

| Etapa | GSD necesario | Sensor | Plataforma | Timing |
|-------|--------------|--------|-----------|--------|
| Brotación (0-30 DAP) | < 5 cm | RGB | UAV | 30-40 DAP |
| Macollamiento (30-90 DAP) | 5–15 cm | RGB o MS | UAV | 60-90 DAP |
| Establecido (> 90 DAP) | < 3 cm ideal | RGB + MS | UAV | Antes de cierre |
| Ratoon | < 5 cm | RGB o MS | UAV | 30-60 DAR |

---

## 6. GOOGLE EARTH ENGINE — FLUJOS DE TRABAJO

### 6.1 Descarga Optimizada Multi-Lote (batch)

```javascript
// ── ESTRATEGIA: Descarga ÚNICA para hacienda completa ──────────────
// Calcular bbox de todos los lotes + 500m buffer
// Descargar 1 sola vez → recortar por lote en local

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(hacienda_bbox)
  .filterDate(startDate, endDate)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15))
  .map(function(img) {
    // Máscara SCL (valores problemáticos: 3,8,9,10,11)
    var scl = img.select('SCL');
    var mask = scl.neq(3).and(scl.neq(8)).and(scl.neq(9))
                  .and(scl.neq(10)).and(scl.neq(11));
    return img.updateMask(mask).divide(10000)
              .copyProperties(img, ['system:time_start']);
  });

// Si < 12 imágenes, subir umbral a 30%
var count = s2.size().getInfo();
if (count < 12) {
  s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(hacienda_bbox).filterDate(startDate, endDate)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
    .map(maskAndScale);
}
```

### 6.2 RGB Color Natural — Stretch Correcto

```python
# CRÍTICO: NO dejar píxeles negros/nodata → reemplazar con blanco
import numpy as np

def stretch_to_uint8(band, nodata_val=0):
    valid = band[band > nodata_val]
    p2  = np.percentile(valid, 2)
    p98 = np.percentile(valid, 98)
    stretched = np.clip((band - p2) / (p98 - p2) * 255, 0, 255)
    stretched[band <= nodata_val] = 255  # nodata → blanco
    return stretched.astype(np.uint8)

# Usar SIEMPRE buffer 100m extra al recortar RGB (evitar bordes negros)
```

### 6.3 DEM y Hidrología

```python
# DEM: COPERNICUS/DEM/GLO30 (resolución nativa: 30m)
# Remuestrear a 10m con bilineal para análisis hidrológico

def calcular_hidrologia(dem_10m):
    # TWI = ln(acc * cellsize / tan(slope_rad + epsilon))
    slope_deg = calcular_pendiente(dem_10m)
    slope_rad = np.deg2rad(slope_deg)
    acc = calcular_flow_accumulation(dem_10m)  # D8
    twi = np.log(acc * 10 / np.tan(slope_rad + 0.001))
    
    # Líneas de drenaje: acc > percentil 95
    drain_threshold = np.percentile(acc, 95)
    drainage_lines = acc > drain_threshold
    
    return twi, drainage_lines, slope_deg
```

---

## 7. SALIDAS Y FORMATOS GIS

### 7.1 Estructura de Archivos por Lote

```
{CLIENTE}/{LOTE}/PRO/
├── VECTORES/
│   ├── zonas_manejo_{lote}.shp        (+ .dbf .prj .shx)
│   ├── zonas_manejo_{lote}.geojson
│   ├── puntos_muestreo_{lote}.shp
│   ├── puntos_muestreo_{lote}.kml
│   ├── lineas_drenaje_{lote}.shp
│   └── gaps_caña_{lote}.shp           (si aplica)
├── RASTERS/
│   ├── ndvi_mediana.tif
│   ├── ndre_mediana.tif
│   ├── ndvi_desvio.tif                (estabilidad)
│   ├── score_compuesto.tif
│   ├── zonas_raster.tif
│   ├── dem_10m.tif
│   ├── twi.tif
│   ├── hillshade.tif
│   └── rgb_sentinel2.tif              (uint8, stretch 2-98%)
├── MAPAS/
│   ├── mapa_zonas_manejo.png          (A3, 300 dpi)
│   ├── mapa_ndvi_multitemporal.png
│   ├── mapa_estabilidad.png
│   ├── mapa_elevacion.png
│   ├── mapa_hidrologia.png
│   ├── mapa_muestreo.png
│   └── mapa_fallas_caña.png           (si aplica)
└── TABLAS/
    ├── estadisticas_zonas.csv
    └── puntos_muestreo.csv
```

### 7.2 CRS Obligatorio

```python
# Siempre usar CRS proyectado (métricas), NO geographic
# Bolivia: EPSG:32720 (UTM 20S) o EPSG:32719 (UTM 19S) según ubicación
# Brasil: EPSG:31981-31985 (SIRGAS 2000 UTM)
# Argentina: EPSG:22182-22185 (POSGAR 98)
# Verificar siempre: gdf.crs.to_epsg()
```

### 7.3 Estándares de Mapas Profesionales

```
Tamaño: A3 landscape (16.54 × 11.69 pulgadas), 300 DPI
Elementos obligatorios:
  ✓ Norte (flecha N)
  ✓ Escala (barra gráfica + texto)
  ✓ Coordenadas UTM (grilla o texto en bordes)
  ✓ Leyenda con áreas (ha) y porcentajes
  ✓ Cuadro de info: Cliente / Lote / Área / Fecha análisis / CRS
  ✓ Logo/firma: "PIXADVISOR — Agricultura de Precisión"
  ✓ RGB Sentinel-2 como fondo (uint8, nodata=blanco)

Paleta de colores estándar para zonas:
  Zona Baja (1):      #CC0000  (rojo)
  Zona Media-Baja (2):#FF8C00  (naranja)
  Zona Media-Alta (3):#FFD700  (amarillo)
  Zona Alta (4):      #228B22  (verde)
  Zona Muy Alta (5):  #006400  (verde oscuro)
  Transparencia zonas: 50% sobre RGB
```

---

## 8. REGLAS DE CALIDAD Y SEGURIDAD GIS

### 8.1 Validaciones Obligatorias
```python
# 1. Verificar que zonas no tengan geometrías inválidas
assert gdf.is_valid.all(), "GEOMETRÍAS INVÁLIDAS — fix con buffer(0)"

# 2. Verificar CRS antes de operaciones espaciales
assert gdf_a.crs == gdf_b.crs, "CRS DISTINTOS — reproyectar primero"

# 3. Verificar que suma de pesos = 1.0
assert abs(sum(pesos.values()) - 1.0) < 0.001, "PESOS NO SUMAN 1.0"

# 4. Verificar área mínima de polígonos (eliminar sliver polygons)
gdf = gdf[gdf.area >= (area_minima_ha * 10000)]

# 5. Número imágenes satelitales (suficiencia estadística)
assert n_images >= 8, f"POCAS IMÁGENES ({n_images}) — subir umbral de nubes"
```

### 8.2 Manejo de Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `griddata cubic` falla | Puntos no suficientes | Cambiar a `method='linear'` |
| RGB fondo negro | Nodata = 0, no reemplazado | `stretched[band<=0] = 255` |
| Zonas < área mínima | Fragmentación post-clasificación | `buffer(20).buffer(-20)` + filtrar área |
| GEE timeout | Export muy grande | Reducir resolución o dividir AOI |
| < 12 imágenes S2 | Área nublada | Subir umbral nubes a 30% |

---

---

## 8. ÍNDICES AVANZADOS 2025+

### 8.1 kNDVI — Kernel NDVI (anti-saturación)

```
kNDVI = tanh(NDVI²)

# Forma completa con kernel RBF:
sigma = 0.5 * (NIR + RED)
kNDVI = exp(-((NIR - RED)² / (2 * sigma²)))
```

**Ventaja**: Supera la saturación de NDVI en canopeos densos (LAI > 4). Captura scattering múltiple. Retención en feature selection para mapeo jerárquico S1+S2. SHAP lo identifica como factor clave para predicción de rendimiento en arroz.

**Sentinel-2**: `kNDVI = tanh(((B8-B4)/(B8+B4))^2)`

### 8.2 IRECI — Inverted Red-Edge Chlorophyll Index

```
IRECI = (B7 - B4) / (B5 / B6)
```

Retrieval de clorofila y variables biofísicas (LAI, fAPAR). Más robusto que NDRE para alta biomasa.

### 8.3 S2REP — Sentinel-2 Red-Edge Position

```
S2REP = 705 + 35 * ((B4 + B7)/2 - B5) / (B6 - B5)
```

Posición del punto de inflexión red-edge (nm). Valores más altos = mayor contenido de clorofila. Rango típico: 710-730 nm para cultivos sanos.

### 8.4 MCARI — Modified Chlorophyll Absorption Ratio Index

```
MCARI = [(B5 - B4) - 0.2 * (B5 - B3)] * (B5 / B4)
TCARI = 3 * [(B5 - B4) - 0.2 * (B5 - B3) * (B5 / B4)]

# Mejor combinación (elimina efecto suelo):
TCARI_OSAVI = TCARI / OSAVI
```

R² = 0.81 para estimación de clorofila. No afectado por iluminación ni fondo de suelo.

### 8.5 PRI — Photochemical Reflectance Index

```
PRI = (R531 - R570) / (R531 + R570)
# Sentinel-2 aproximación: (B3_green - B4_red) / (B3 + B4) [proxy]
```

Mide ciclo de xantofilas — actividad fotosintética en **tiempo real**. Detecta estrés antes que NDVI.

### 8.6 BSI — Bare Soil Index

```
BSI = ((B11 + B4) - (B8 + B2)) / ((B11 + B4) + (B8 + B2))
```

Umbrales para composite de suelo desnudo: NDVI < 0.06, NBR2 < 0.05, BSI > 0.10. Fundamental para mapeo de carbono orgánico del suelo (SOC).

### 8.7 SMI — Soil Moisture Index

```
SMI = (LSTmax - LST) / (LSTmax - LSTmin)
# Método triángulo LST-NDVI para humedad superficial
```

### 8.8 Otros Índices Nuevos (2025)

| Índice | Fórmula | Uso |
|--------|---------|-----|
| **OSAVI** | ((NIR-RED)/(NIR+RED+0.16))*(1.16) | SAVI optimizado, L=0.16 |
| **BVI** | Red-edge + NIR/SWIR ratio | Degradación de ecosistemas, browning |
| **PPI** | Plant Phenology Index (resistente a saturación) | Monitoreo fenológico continuo |
| **NDVI3RE** | Usa las 3 bandas red-edge simultáneamente | Mayor discriminación de clorofila |

---

## 9. SAR SENTINEL-1 Y FUSIÓN ÓPTICO-RADAR

### 9.1 Radar Vegetation Index (RVI) — Sentinel-1

```javascript
// RVI para dual-pol (VV+VH) — Sentinel-1 GRD
var VH = img.select('VH');
var VV = img.select('VV');
var RVI = VH.multiply(4).divide(VV.add(VH));
// Rango: 0 (suelo desnudo) a 1 (vegetación densa)
```

**Ventaja**: Funciona con nubes, día/noche. Complementa óptico en temporadas lluviosas.

### 9.2 DpRVI — Dual-Polarimetric Radar Vegetation Index

```python
# Descomposición de eigenvalores de la matriz de covarianza 2x2
q = sigma_VH / sigma_VV
m = (1 - q) / (1 + q)  # grado de polarización
DpRVI = sqrt(1 - m) * (4 * sigma_VH) / (sigma_VV + sigma_VH)
```

Correlacionado con PAI (Plant Area Index), contenido de agua vegetal y biomasa seca en todas las etapas fenológicas.

### 9.3 Fusión SAR + Óptico (Sentinel-1 + Sentinel-2)

```
ESTRATEGIA DE FUSIÓN RECOMENDADA:
┌──────────────────────────────────────────────────┐
│  Sentinel-2 (óptico)  →  Emergencia, cierre,     │
│                          senescencia              │
│  Sentinel-1 (SAR)     →  Floración, cosecha,     │
│                          períodos nublados        │
│  FUSIÓN                →  Monitoreo continuo      │
│                          all-weather              │
└──────────────────────────────────────────────────┘

Resultados publicados (ESA 2025):
- Transformer S1+S2 → GAI retrieval R²=0.88, RMSE=0.71
- Fusión jerárquica → 94% OA land cover, 95% trigo, 81% 13 cultivos
- SAR adelanta Earliest Identifiable Time en ~20 días para soja
```

### 9.4 Clasificación Temporal SAR

| Modelo | Arquitectura | Precisión | Ventaja |
|--------|-------------|-----------|---------|
| TCN+Attention | Temporal Conv. + atención | 85.7% | Mejor overall, paralelo |
| LSTM | Recurrente | 83.4% | Bueno con series largas |
| Bi-GRU | Bidireccional | 84.1% | Balance vel/precisión |
| SITSMamba | CNN+Mamba (SSM) | 91.0% | Complejidad lineal |

---

## 10. FOUNDATION MODELS E IA PARA AGRICULTURA

### 10.1 Prithvi-EO-2.0 (NASA/IBM, Dic 2024)

```
Arquitectura: ViT-L (300M params) / ViT-H (600M params)
Preentrenamiento: MAE sobre 4.2M muestras HLS V2 (30m)
Bandas: Blue, Green, Red, Narrow NIR, SWIR1, SWIR2
Embeddings: 3D spatiotemporal + 2D sin/cos location
Supera: Prithvi-1 en +8%, supera 6 otros modelos geoespaciales
Tasks: clasificación cultivos, mapeo inundaciones, burn scars
Acceso: huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-300M
Fine-tune: IBM TerraTorch (open-source)
```

### 10.2 AgriFM (2025 — Específico Agricultura)

```
Arquitectura: Modified Video Swin Transformer
Preentrenamiento: 25M+ imágenes (MODIS, Landsat-8/9, Sentinel-2)
Tasks: mapeo agrícola, límites de parcela, LULC, cultivos específicos
Ventaja: temporal-spatial downsampling sincronizado
GitHub: github.com/flyakon/AgriFM
```

### 10.3 Clay Foundation Model (Development Seed)

```
Arquitectura: ViT + MAE (self-supervised)
Ventaja: multi-fuente, multi-resolución, meta-learner
Tasks: biomasa, acuicultura, land cover, deforestación
Deploy: Amazon SageMaker / HuggingFace
```

### 10.4 SAM (Segment Anything) en Agricultura

| Aplicación | Modelo | Resultado |
|-----------|--------|-----------|
| Límites de parcela | SAM + S2 estacional | IoU = 0.86 (32M ha) |
| Enfermedad cultivos | ASA (Agricultural SAM Adapter) | Zero-shot segmentación |
| Anotación campo | ARAMSAM (SAM 1+2) | Aceleración 10x |

**Limitación**: SAM estándar funciona mal en agricultura — requiere adaptación de dominio (ASA).

### 10.5 Vision Transformers (ViT) para Cultivos

```
ViT Crop Classification:  94.6% accuracy, kappa=0.91
vs CNN baseline:          89.2% accuracy
Ventaja: auto-atención captura dependencias espaciales de largo alcance
         Mejor separación de cultivos espectralmente similares (trigo vs cebada)

Variantes agrícolas:
- MSViT: multi-branch óptico + SAR time series
- PVM: Phenology-aware ViT con calendarios de crecimiento (F1=74.8%)
- TSViT: Temporal-Spatial ViT para SITS
```

### 10.6 Self-Supervised Learning (SSL)

**Hallazgo clave (2025)**: SSL supera al mejor modelo supervisado usando solo **5% de datos etiquetados**. Probado en 10 clases de cultivo (LUCAS dataset). Esto habilita clasificación en regiones con pocos datos de entrenamiento.

---

## 11. TELEDETECCIÓN SUELO, RENDIMIENTO Y ESTRÉS

### 11.1 Carbono Orgánico del Suelo (SOC) desde Satélite

```
Mejor approach: maxBSI composite + Regresión Lineal (R²=0.52)
1. Crear composite de suelo desnudo: NDVI<0.06, NBR2<0.05, BSI>0.10
2. Extraer bandas B2-B12 en píxeles de suelo desnudo
3. RF/SVR sobre reflectancias → SOC predicho
4. Agregar textura GLCM mejora significativamente
Complementar con: SoilGrids API (rest.isric.org) — 250m, 14 propiedades, 6 profundidades
```

### 11.2 CWSI — Crop Water Stress Index (Térmico)

```
CWSI = (Tc - Twet) / (Tdry - Twet)

Tc   = temperatura canopeo observada (sensor térmico)
Twet = referencia canopeo transpirando 100% (boundary húmedo)
Tdry = referencia sin transpiración (boundary seco)

R² > 0.85 vs potencial hídrico del tallo (validado con drones)

Métodos de cálculo:
1. Empírico con baseline desarrollada (CWSI-EB1) — más práctico
2. Teórico con resistencia aerodinámica (CWSI-Th1) — más preciso
3. UAV + Penman-Monteith para CWSI diario

Mejor fase de medición: llenado de grano
```

### 11.3 SIF — Solar Induced Fluorescence

```
SIF detecta estrés hídrico 1-2 MESES antes que indicadores tradicionales
Fuentes:
- ECOSTRESS (ISS): 70m resolución, 1-5 días revisita
- TROPOMI: global daily, 7km
- Próximo: ESA FLEX mission (alta resolución SIF dedicada)

Aplicación: alerta temprana sequía, eficiencia fotosintética real-time
```

### 11.4 Predicción de Rendimiento

```
Mejores modelos:
- Random Forest:  R²=0.91, nRMSE=10.2% (trigo, Sentinel-2)
- TCN temporal:   Supera ML clásico en series temporales
- Híbrido CGM-ML: Combina modelos de crecimiento + machine learning

Mejores índices predictores:
- GNDVI + LAI: más confiables para trigo
- NDRE: cultivos sensibles a nitrógeno
- EVI: corrige saturación de NDVI en alta biomasa
- kNDVI: retención en SHAP analysis para arroz
```

### 11.5 Detección de Deficiencia de Nutrientes

```
NITRÓGENO:
- NDRE detecta deficiencia N 1-2 semanas antes que NDVI
- MTCI sensible a alta clorofila: MTCI = (B6 - B5) / (B5 - B4)
- Fertirrigación guiada por satélite redujo input N en 23%

FÓSFORO / POTASIO:
- Requiere datos hiperespectrales (517-2269nm para P, 519-2058nm para K)
- Limitada factibilidad solo con Sentinel-2
- Complementar con análisis de suelo + interpolación espacial

PRESCRIPCIÓN VRT (Tasa Variable):
- NFOA algorithm: RF→GNC prediction + NDRE sufficiency index → mapa N variable
- FCM clustering: más usado para delineación de zonas + PCA/t-SNE
- Estabilidad temporal: multi-year NDVI composites (mean, SD, CV) + FPI/NCE
```

---

## 12. TECNOLOGÍAS ISRAEL Y REFERENTES GLOBALES

### 12.1 Empresas AgriTech Israel (Líderes en Teledetección)

| Empresa | Tecnología | Escala | Diferenciador |
|---------|-----------|--------|---------------|
| **Taranis** (Tel Aviv) | Imágenes 0.3mm/px desde avión + TF/ML | 20M+ acres | 500M+ datapoints, detección nivel hoja |
| **CropX** (Tel Aviv) | Sensores suelo + satélite + weather | Global | Strato 1 microclima, fusión multi-dato |
| **SupPlant** (Afula) | Sensores planta + IA irrigación | Global | Irrigación diaria personalizada sin sensores |
| **SeeTree** (Tel Aviv) | ML por árbol individual, drones | 500M+ árboles | Citrus, palta, palma |
| **Prospera/Valmont** | Computer vision in-field | Global | Detección temprana estrés/enfermedad |
| **Phytech** | Sensores fisiológicos de planta | Global | Monitoreo en tiempo real del estado de la planta |

### 12.2 Instituciones de Investigación Israel

```
VOLCANI CENTER (Agricultural Research Organization):
- 200 científicos, 75% de investigación agrícola de Israel
- Depto. Sensing & Mechanical Systems: UAV RS, térmica, NIR, Raman, GIS
- Nanotecnología para sensores agrícolas

TECHNION (Israel Institute of Technology):
- CEAR Lab: robots aéreos-terrestres en huertos, drones para escaneo de árboles
- Precision Agriculture group: sensores para cultivos especiales

HEBREW UNIVERSITY:
- Plant Sciences & Genetics: fenotipado remoto, análisis espectral
```

### 12.3 Ecosistema Israel en Números (2026)

```
390 startups agritech | 176 financiadas | 65 Series A+
$1.66B+ levantados en la última década
Tendencia 2026: IA + IoT + SAR + hiperespectral + foundation models
para analítica predictiva a nivel de lote
```

---

*Skill actualizado: 2026-03-28 | v2.0 | Basado en: Remote Sensing MDPI (2023-2025), Zhang et al. Agronomy 2024, Alabama Ext. 2025, Auravant 2024, Silva et al. 2021, Frontiers Agronomy 2025, NASA Prithvi-EO-2.0 (arXiv 2024), AgriFM (RSE 2025), ESA Science Hub 2025, Volcani Center, Technion, Taranis, CropX, SupPlant, SeeTree, IPL-UV kNDVI, Sentinel Hub Custom Scripts, ScienceDirect crop monitoring reviews 2025*
