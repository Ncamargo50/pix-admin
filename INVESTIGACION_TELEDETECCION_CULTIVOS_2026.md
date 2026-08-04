# Percepción remota de cultivos — estado del arte 2024-2026

**Investigación Pixadvisor · 3 de agosto de 2026**
Foco: qué se puede analizar REALMENTE en un cultivo con imágenes de satélite, con qué índice, con qué error medido, y qué de lo que circula NO está probado.

---

> ## ⚠️ CORRECCIONES DEL 2026-08-03 — leer ANTES que el resto
>
> Este informe se auditó contra el dato propio (`PIX_ALERTA/AUDITORIA_2026-08-03.md`) y **dos de
> sus recomendaciones no sobrevivieron**. Las dos por la misma causa: el informe confundió *"es
> verdad"* con *"aplica a nuestro motor"*.
>
> **1. kNDVI (§2.5, §9, §11.2) — NO aplica.** La ciencia es correcta, la recomendación era mala.
> Nuestro motor no usa NDVI como eje ni usa umbrales absolutos, así que la saturación no le pega.
> Y MEDIDO: reemplazarlo en la compuerta de dosel corre el umbral efectivo y cambia de lado al
> **1,29% de los píxeles** sin que nadie haya calibrado nada. Donde el informe decía *"reemplazo
> directo, gratis, de una línea de código"*, corresponde leer: **no tocar**.
>
> **2. Sentinel-1D (§1.1, §11.3) — la mejora NO existe sobre nuestros lotes.** El informe decía
> que S1D "restablece la revisita de 6 días" y recomendaba re-medir esperando una mejora. Se
> midió: sobre SA/SF sigue habiendo **una sola órbita**, el hueco mediano pasó de 12 a 11 días y
> el **máximo subió de 12 a 18**. La revisita de 6 días es cierta para la constelación y falsa
> para este punto del planeta.
>
> **Lo que sí se confirmó midiendo:** el radar aporta **+15,4 y +23,1 puntos** de dékadas con
> observación (§2.7) — pero no se puede cosechar en campo chico sin cohorte regional.
>
> El resto del informe no fue refutado. La lección de método está al final de la auditoría.

## 0. Cómo leer este informe

Cada afirmación lleva marca de trazabilidad:

| Marca | Significado |
|---|---|
| **[V]** | Verificado: leí el paper/documento fuente y el número sale de ahí |
| **[S]** | Secundario: viene de resumen de buscador o de la página del editor, NO leí el texto completo |
| **[NO-CITAR]** | Circula en la industria pero no encontré respaldo — no ponerlo en un informe a cliente |

**Regla de oro que atraviesa todo el documento:** casi ningún número absoluto de un índice de vegetación transfiere entre lote, campaña, sensor o variedad. Lo que transfiere es el **orden interno** (quién está peor que quién dentro de una misma población comparable) y la **referencia relativa** (el propio lote contra sí mismo, o contra su cohorte). Esto ya estaba medido en la casa; la literatura 2025-2026 lo refuerza y lo cuantifica (§3).

---

## 1. Qué cambió en la infraestructura de datos (lo que hoy es distinto a 2023)

Esto es lo primero porque cambia qué se puede prometer.

### 1.1 Constelaciones ópticas

- **Sentinel-2C reemplazó operativamente a Sentinel-2A el 21 de enero de 2025.** Desde marzo de 2025, S2A quedó en campaña de extensión complementando excepcionalmente a la constelación nominal S2B+S2C. **[S]**
  → Implicancia directa para nosotros: coincide con lo que ya teníamos MEDIDO en la casa (S2B+S2C cada 5 días sin huecos; S2A no aporta un ciclo regular de 10 días). La literatura oficial de Copernicus confirma el porqué: **S2A ya no es parte de la constelación nominal**.
- **Sentinel-1D** completó comisionamiento y quedó plenamente operativo el **1 de mayo de 2026**; la configuración final restablece la revisita nominal de **6 días** entre S1C y S1D. **[S]**
  → Esto revierte parcialmente el problema que teníamos medido (S1 solo descendente, S1D fuera). Vale re-medir la disponibilidad real de S1 sobre Santa Cruz **después** de mayo 2026.
- **HLS v2.0 (Harmonized Landsat Sentinel-2), julio de 2025**: dataset global de reflectancia superficial armonizada L8/L9 + S2A/B/C, extendido hacia atrás hasta 2013, con **revisita mediana < 1,6 días**. En febrero de 2025 el proyecto liberó además productos de índices de vegetación a 30 m (HLSL30VI, HLSS30VI). **[S]**
  → Es la mejor base pública que existe hoy para series temporales densas. USDA ya lo usa para mapear emergencia a escala de lote en el Corn Belt.

### 1.2 Radar

- **NISAR (NASA-ISRO) lanzado el 30 de julio de 2025.** Banda L + banda S, imagen de casi toda la tierra emergida **cada 12 días**, resolución hasta ~10 m, y un producto global de **humedad de suelo a 200 m** con mínimo dos pasadas cada 12 días (ascendente y descendente). **[S]**
  → Es el primer radar de banda L global, libre y sistemático. Para nosotros importa por penetración de canopia (biomasa de caña, maíz alto) y por humedad de suelo bajo nube.
- **SAOCOM (CONAE, Argentina)**: banda L, productos operativos y gratuitos para el agro pampeano — **mapa de humedad superficial de suelo a 10 m con precisión declarada del 7%**, clasificación de cultivos, e **índice radar de vegetación (RVI)** que sigue el desarrollo bajo nube. También publican un **mapa de incidencia de fusariosis en trigo** en ambientes pampeanos. **[S]**

### 1.3 Hiperespectral

- **PRISMA (ASI) y EnMAP (DLR)** ya entregan recuperación de rasgos de cultivo operativa vía modelos híbridos (transferencia radiativa PROSAIL + machine learning + active learning):
  - PRISMA: contenido de **nitrógeno foliar r² = 0,87 (nRMSE 7,5%)**; clorofila foliar r² = 0,67 (nRMSE 11,7%). **[S]**
  - EnMAP (trigo, 2025): clorofila foliar r = 0,66; carotenoides r = 0,57; **LAI r = 0,88**. **[S]**
  → Dato incómodo y útil: **el nitrógeno foliar se recupera MEJOR que la clorofila** con hiperespectral. Lo contrario de la intuición de la industria.
- **EnMAP + Sentinel-2 combinados** en un transformer de doble flujo (espectral-espacial para el hiperespectral, Swin temporal para la serie S2) mejoran la clasificación jerárquica de tipo de cultivo en **+4,2% de F1 promedio, con pico de +6,3%**. **[S]**
  → El hiperespectral aporta, pero aporta poco frente al costo. La serie temporal multiespectral sigue siendo el caballo de batalla.

### 1.4 Modelos fundacionales geoespaciales (lo verdaderamente nuevo)

- **AlphaEarth Foundations (Google DeepMind, 2025)**: modelo de campo de embeddings, salida de **64 dimensiones a 10 m, anual, 2017-2024**, publicado como dataset consumible directamente por ML clásico — sin paso de inferencia en GPU. Los autores reportan que es el único set de embeddings que supera consistentemente a las aproximaciones de featurización conocidas. **[V, cita]** / **[S, desempeño]**
  Cita: Brown, C.F. et al. (2025). *AlphaEarth Foundations: An embedding field model for accurate and efficient global mapping from sparse label data.* arXiv:2507.22291. https://doi.org/10.48550/arXiv.2507.22291
- Benchmarks independientes 2026 (Stanford/Corteva, "Harvesting AlphaEarth") evalúan AEF en **predicción de rendimiento, mapeo de labranza y de cultivos de cobertura**; es la primera comparación cabeza a cabeza contra features clásicas de teledetección para tareas de producción. **[S]** — no pude leer el PDF, queda pendiente.
- Advertencia crítica encontrada en un benchmark controlado de Prithvi / SpectralGPT / SatMAE sobre segmentación multitemporal de cultivos en 4 estados de EE.UU.: **los tres se degradan abruptamente bajo cambio de distribución regional**, prediciendo solo los cultivos más comunes y omitiendo los raros. **[S]**
  → Traducción operativa: un foundation model entrenado en el Corn Belt **no** se puede soltar sobre Santa Cruz sin verdades de campo locales. Es exactamente el mismo hallazgo que ya teníamos con el modelo RF HDS que no generalizó a Brasil.

### 1.5 Plataformas de procesamiento

- **openEO** se consolidó como la capa estándar: el Copernicus Browser lo adopta como back-end de procesamiento por defecto, Sentinel Hub pasa a ser back-end openEO oficial, y **Google Earth Engine está explorando soportarlo**. **[S]**
  → Relevante para el disparador comercial que ya tenemos identificado (GEE gratuito prohíbe cobrar). **CDSE + openEO es hoy la ruta de salida más realista para procesamiento comercial**, y ESA WorldCereal ya demostró que se puede correr un sistema global de mapeo de cultivos íntegramente sobre esa pila.

---

## 2. Qué se puede analizar REALMENTE — variable por variable

Esta es la respuesta directa a "¿qué efectivamente podemos analizar con los diferentes tipos de índices?".

La estructura correcta no es "índice → diagnóstico". Es:

```
reflectancia → variable BIOFÍSICA (con error medible) → interpretación AGRONÓMICA (con supuestos) → decisión
```

El salto que la industria hace mal es del primer paso al último, saltándose los dos errores del medio.

### 2.1 Clorofila y pigmentos — LO MÁS SÓLIDO

**Qué se mide de verdad:** contenido de clorofila **por unidad de área de canopia** (CCC), no "salud".

| Índice | Bandas S2 | Qué respalda | Evidencia |
|---|---|---|---|
| **CIre** (red-edge chlorophyll index) | B8/B5 − 1 (o B7/B5 − 1) | Estimador **lineal** de clorofila y N de canopia | [S] |
| **CIgreen** | B8/B3 − 1 | Ídem, lineal | [S] |
| **MTCI** | (B6−B5)/(B5−B4) | **El mejor** para clorofila foliar: mayor R² y menor RMSE en los 3 datasets del estudio de referencia | [S] |
| **NDRE** | (B8−B5)/(B8+B5) | El operativo; no satura tan temprano como NDVI | [S] |
| MCARI/OSAVI | B5,B4,B3 + B8,B4 | Corrige efecto suelo y LAI sobre la señal de pigmento | [S] |

**Los tres índices que la literatura señala como estimadores lineales y robustos de clorofila/N de canopia son CIred-edge, CIgreen y MTCI** — no el NDVI. **[S]**

**Límite duro:** clorofila ≠ nitrógeno ≠ salud. Un cultivo con clorosis por anegamiento, por pH, por deficiencia de S, de Mg o de Fe da la misma caída de CIre que uno con hambre de N. **El índice no discrimina la causa; solo dice "menos pigmento por metro cuadrado".**

### 2.2 Nitrógeno — SE PUEDE, PERO SOLO COMO ÍNDICE NUTRICIONAL RELATIVO

Este es el bloque con mejor relación evidencia/valor comercial.

- **Maíz: NNI (índice de nutrición nitrogenada) vs NDRE → R² = 0,79, RMSE = 0,26, MAE = 0,2.** Y NNI derivado directamente del contenido de clorofila de canopia de S2 (CCC_S2) → **R² = 0,76**. **[S]**
- **Cultivos de cobertura de cereales de invierno**: 15 índices S2 evaluados contra **1.627 muestras destructivas (2018-2023)**; los índices de red-edge estiman con exactitud el contenido de N. **[S]** — es de los datasets de calibración más grandes que encontré.
- **Trigo, proteína en grano** (el eslabón que todos quieren y casi nadie entrega):
  - PLS con N foliar en grano acuoso: **R² = 0,74** (nRMSE 5,12%). **[S]**
  - En **antesis** (que es cuando la decisión todavía sirve): UAV multiespectral con red-edge → **R² = 0,42, RMSE 0,18%**; escalado a satélite → **R² = 0,40, RMSE 0,29%**. **[S]**
  - Concentración de N foliar en antesis vs proteína en grano: **r = 0,726**. **[S]**
  → Conclusión honesta: **predecir proteína de trigo por satélite a tiempo de decidir da R² ≈ 0,4.** Sirve para zonificar, no para prometer un número de proteína a un cliente.
- Los índices acumulados a lo largo de varias fechas predicen mejor rendimiento y proteína que una sola fecha. **[S]**

**Cómo se hace bien (y esto es doctrina, no opinión):** con **índice de suficiencia** contra una referencia — sea una franja sobre-fertilizada real, sea una **referencia virtual** tomada como el **percentil 95 del histograma del propio lote/cohorte**. Es exactamente el criterio que ya tenemos implementado en la skill de vigor. **[S]**

**Argentina — N-INTA / Auravant:** algoritmo de prescripción nitrogenada variable desarrollado por INTA, incorporado gratis a Auravant. Detecta diferencias de vigor por satélite y las traduce a variación de requerimiento nutricional, generando prescripción por zona. Desarrollado y validado para **trigo y maíz** en la región pampeana con sensores manuales y montados en máquina. La plataforma reporta 7 M ha monitoreadas y 20.000 usuarios. **[S]**
Un ensayo de INTA Reconquista reporta **reducción de más del 50% del N** sin pérdida de rendimiento, con dron + algoritmo lote a lote. **[S]** — el dato es de prensa institucional, no de paper revisado; **no citarlo como resultado científico** sin conseguir la publicación.

### 2.3 Agua y estrés hídrico — EL BLOQUE MÁS SOBREVENDIDO

Tres caminos distintos, con evidencia muy distinta:

**(a) Índices de humedad de canopia (NDMI, LSWI, NDWI-Gao)**
Miden agua **en la hoja**, mediada por SWIR. Sensibles pero altamente correlacionados con estructura/biomasa. Ya tenemos medido en la casa que NDWI y NDMI llegan a r = 0,998 entre sí y que los 5 índices principales correlacionan 0,97-0,998 espacialmente. **No son ejes independientes.**

**(b) Térmico / CWSI**
Físicamente el más directo (temperatura de canopia = transpiración = estado hídrico). Pero la resolución térmica satelital libre (Landsat 100 m remuestreado a 30 m, ECOSTRESS ~70 m) es demasiado gruesa para el lote comercial, y ya tenemos la conclusión medida: **el térmico y el CWSI/TVDI CIERRAN a escala de lote**. Los estudios 2025 que funcionan lo hacen con **UAV térmico**, no con satélite. **[S]**

**(c) OPTRAM (trapecio óptico) — humedad de suelo sin térmico**
Usa reflectancia SWIR transformada vs NDVI. Rendimiento reportado: **RMSE no sesgado 0,050-0,085 cm³/cm³ y r de 0,10 a 0,70** según sitio. **[S]**
→ Ese rango de r (¡0,10!) es la noticia real: **OPTRAM funciona en algunos sitios y no funciona en otros**, y requiere calibración por tipo de cobertura (estudio 2025 en el Valle Central de California). Para lotes que van de suelo desnudo a canopia densa se recomienda SAVI en lugar de NDVI en el eje.

**(d) Evapotranspiración — OpenET (EE.UU., el estándar de facto)**
Ensamble de 6 modelos de teledetección, **30 m, todo el territorio continental de EE.UU.**, público.
- Exactitud en sitios de cultivo: **MAE 15,8 mm/mes (17% del ET observado medio), sesgo medio −5,3 mm/mes (6%), r² = 0,9.** **[S]**
- Estimación de agua de riego a escala de lote, agregada a la estación: **sesgo 1,6-4,9%, R² 0,53-0,74**. **[S]**
- Evaluación 2024-2025 en alfalfa bajo riego deficitario (20 lotes comerciales, Imperial Valley): bajo riego pleno el error de sesgo medio diario queda **por debajo de 0,5 mm/día**. **[S]**
→ Este es el mejor ejemplo del informe de "qué se puede prometer": ET satelital a escala de lote es un producto **maduro y auditado**. En Sudamérica no existe equivalente operativo — hay hueco de mercado.

### 2.4 Senescencia y madurez

- **PSRI** (relación carotenoides/clorofila) es el índice **más específico** para stay-green: en trigo se identificó como el indicador que mejor diferencia efectos genotípicos, por mayor sensibilidad a cambios de composición pigmentaria y mayor confiabilidad. **[S]**
- Pero el mismo cuerpo de trabajo dice, sin vueltas: **la evaluación visual sigue siendo el gold standard** para cuantificar senescencia foliar en ensayos medianos a grandes, y agregar más features espectrales al PSRI aporta poco. **[S]**
- ARI (antocianinas) y mCRI (carotenoides) existen como proxies pigmentarios, pero necesitan bandas que S2 no tiene bien resueltas.

**Advertencia de casa:** ya tenemos medido que **PSRI como segundo eje era peor que NDRE** (lift 3,7x vs 18,3x). Este informe no cambia eso: PSRI sirve para *seguir la dinámica de senescencia a lo largo del tiempo*, no para *detectar un foco anómalo en una fecha*.

### 2.5 Biomasa, LAI y cobertura

- **Procesador biofísico de SNAP (SL2P)** entrega LAI, FAPAR, FCOVER, Cab y contenido de agua de canopia a partir de S2. Es una red neuronal entrenada sobre PROSAIL, no un índice.
  - Validación en bosques de Norteamérica: los requerimientos de usuario se cumplen en solo **51% de las comparaciones de LAI, 37% de fCOVER y 31% de fAPAR**; **subestima LAI entre 20% y 50% cuando LAI > 2**. **[S]**
  - Corrección empírica de sesgo con datos in situ reduce el error **40% en fCOVER, 57% en fAPAR y 92% en LAI**. **[S]**
  → Es decir: **el producto crudo no sirve para valores absolutos; con 20 puntos de campo pasa a servir.** Es un argumento de venta de muestreo, no un defecto que ocultar.
- **Textura (GLCM) + índices espectrales**: combinar VIs con texturas da los mejores resultados generales (**R² = 0,78**, hasta **0,84** en fases específicas de arroz). Los índices de textura de diferencia normalizada (NDTI) con NIR, red-edge y azul superan a todos los VIs y a las texturas GLCM solas en distintos estadios. **[S]**
  → **Esta es una de las novedades más aprovechables del informe y no la estamos usando.** La textura captura estructura de canopia, que es una dimensión ortogonal a la reflectancia — justo el "segundo eje" que veníamos buscando y que no encontrábamos entre índices espectrales (todos correlacionados 0,97+).
- **kNDVI** (Camps-Valls et al. 2021, *Science Advances*, doi:10.1126/sciadv.abc7447): transformación por kernel del NDVI. Más resistente a saturación, sesgo y ciclos fenológicos complejos; más robusto al ruido; correlaciona mejor que NDVI y NIRv con GPP de torres de flujo y con SIF, en todos los biomas y zonas climáticas evaluados. **[S]**
  → Reemplazo directo, gratis, de una línea de código, para donde hoy usamos NDVI y satura (maíz post-V8, trigo post-encañado).

### 2.6 Fotosíntesis directa — SIF y PRI

**SIF (fluorescencia inducida por el sol)** — el review de referencia es contundente en ambas direcciones:

Cita: Ruehr, S., Pierrat, Z.A., Parazoo, N., Keenan, T.F. (2026). *Harnessing solar-induced fluorescence for on-farm agricultural research and management: recent advances and outstanding needs.* **Environmental Research Letters 21(11):111007.** https://doi.org/10.1088/1748-9326/ae74e2 **[V — leído]**

Lo bueno:
- Relación **lineal** con GPP a escala de lote a ecosistema.
- Mejoras de **50-70% sobre modelos de ciclo de carbono y sobre otros índices de vegetación** en predicción de rendimiento.
- **Detecta estrés hídrico leve ANTES que los índices de vegetación**, que solo cambian bajo estrés más severo.

Lo que mata su uso comercial hoy:
- Resolución de píxel: GOME2 40×40 km, **TROPOMI 3,5×5,5 km**, OCO-2 1,3×2,25 km, OCO-3 2×2 km. FLEX (futuro) ~0,3×0,3 km — **y los propios autores dicen que incluso FLEX sigue siendo demasiado grande para observar dentro del lote**.
- Instrumentación de torre ~USD 50.000; sistemas de imagen **> USD 500.000**; contra ~USD 10.000 para índices convencionales.
- Sin estandarización: metodologías propias de cada laboratorio.
- "SIF y GPP se desacoplan a escalas espaciales y temporales pequeñas" y **puede requerirse calibración específica de sitio antes de transferir modelos de productividad basados en SIF**.

→ **Veredicto: SIF es ciencia excelente y producto comercial inviable a escala de lote, hoy.** Si alguien le vende "SIF para su campo", está vendiendo un píxel de 3,5 × 5,5 km.

**PRI (531/570 nm)**: sensible a xantofilas, proxy de eficiencia de uso de la luz, detecta cambios rápidos de fotosíntesis bajo condiciones desfavorables. **Sentinel-2 no tiene las bandas.** Requiere hiperespectral o sensores dedicados (GCOM-C/SGLI observa PRI y CCI). **[S]**

### 2.7 Estructura y todo-tiempo — SAR

- **RVI (índice radar de vegetación) de SAOCOM**: seguimiento del desarrollo del cultivo **bajo nube**, con mapas de índice de producción para trigo, maíz, soja y girasol construidos sobre un modelo de cultivo que integra la información satelital. **[S]**
- **Caña**: integrar **VOD (vegetation optical depth) de S1 a 10 m con GRVI de S2** da predicción de rendimiento de alta precisión. **[S]**
- **Fenología de papa**: sinergia S1+S2 identifica emergencia, cierre de canopia, floración, inicio de senescencia y momento de cosecha a escala de lote, con uso operativo en casi-tiempo-real. **[S]**
- **Trigo/maíz en Alemania**: S1 sirve para evaluación de fenología a gran escala. **[S]**

---

## 3. "¿Hay rangos óptimos con qué comparar?" — LA RESPUESTA DURA

**No, no existen rangos óptimos absolutos y universales de índices de vegetación por cultivo y estadio.** Lo que existe son tres cosas distintas que se confunden:

1. **Tablas comerciales de clase de color** (EOSDA, OneSoil, etc.). Son cortes de visualización, no umbrales agronómicos. Ya lo tenemos auditado internamente.
2. **Rangos de literatura para un sitio-año-variedad-sensor específico.** Válidos ahí, no fuera.
3. **Referencias relativas**, que sí funcionan: índice de suficiencia contra P95 de la cohorte, NNI, residuo temporal contra la escena limpia anterior, orden interno + control de error (Gi*/FDR).

### La evidencia 2025 de no-transferibilidad

- Un estudio 2025 midió explícitamente la **inconsistencia espacial del umbral**: para NDVI en estadio de crecimiento 1, la brecha entre bloques espaciales del **mismo campo** fue de **35,66 puntos** — es decir, el umbral de decisión aprendido en una mitad del lote **no transfiere a la otra mitad**. **[S — preprint arXiv 2512.21948, no revisado por pares; verificar antes de citar a cliente]**
- Los umbrales de NDVI comúnmente aplicados son "un mal ajuste para regiones áridas": donde el estándar usa uno, **0,15 resultó el valor sensato** para presencia de vegetación. **[S]**
- La **dependencia de escala** complica la transformación de índices entre resoluciones: la transferibilidad de modelos de parámetros de vegetación entre resoluciones está afectada por efectos de agregación no lineales. **[S]**
  → Traducción: un umbral calibrado a 10 m **no es el mismo** a 20 m. Esto conecta con lo que ya corregimos internamente (grilla nativa 20 m para el detector).

**Revisión sistemática global de índices de vegetación (la referencia de cabecera 2025):**
Yan, K., Gao, S., Yan, G., Ma, X., Chen, X., Zhu, P. et al. (2025). *A global systematic review of the remote sensing vegetation indices.* **International Journal of Applied Earth Observation and Geoinformation, 139, 104560.** **[S]**
Analiza la correlación entre **86 índices de vegetación**. Conclusión operativa: el desempeño de un VI depende de la selección de bandas y de la fórmula; un VI ideal equilibra sensibilidad a la vegetación con resistencia a interferencias — **lo que implica que el índice y la calibración óptimos varían con las condiciones locales**.

→ **86 índices con alta correlación mutua no son 86 dimensiones de información.** Es la misma conclusión que ya medimos: los 5 índices principales correlacionan 0,97-0,998 espacialmente. La segunda dimensión de información no está en otro índice — está en el **residuo**, en la **textura**, en el **radar** o en el **tiempo**.

---

## 4. "¿Se toma en cuenta el estadio fenológico?" — SÍ, Y ESE ES EL PROBLEMA

Sí se toma en cuenta, y es imprescindible. Pero el estadio fenológico obtenido **por satélite** tiene un error que casi nadie declara.

**El número clave del informe:**

Zhao, Y., Jiang, R., Brider, J., Chapman, S., Potgieter, A. (2025). *Characterizing wheat and barley growth and phenology using multi-spectral remote sensing for site-specific precision agriculture.* **in silico Plants 7(2), diaf013.** https://doi.org/10.1093/insilicoplants/diaf013 **[V — leído]**

Estimación de estadios de trigo y cebada desde Sentinel-2:

| Estadio | R² | **RMSE (días)** |
|---|---|---|
| Hoja bandera (sitio de validación) | 0,70 | **7,66** |
| Encañado | 0,61 | **8,67** |
| Floración (sitio) | 0,69 | **~10** |
| Floración (escala nacional, 2021) | 0,85 | **13,07** |
| Madurez (nacional 2021) | 0,85 | — |
| Cosecha (nacional 2021) | 0,55 | — |

Limitaciones que declaran los propios autores: 10 m puede ser insuficiente en lotes fragmentados; **el ciclo de 5 días de S2 no acompaña transiciones fenológicas rápidas**; nubes; y la calibración conjunta trigo+cebada no captura diferencias varietales.

**Consecuencia brutal e ineludible:**
> Si comparo un lote contra un "rango óptimo por estadio fenológico", y el estadio lo estimé por satélite con **±8 a 13 días de error**, en trigo eso son **uno o dos estadios completos de diferencia**. El "rango óptimo" queda invalidado por el error de la variable con la que se indexa.

Esto es exactamente el motivo por el que la casa usa **cohorte de siembra** en vez de estadio absoluto: comparar contra pares con la misma fenología real observada, no contra una tabla indexada por un estadio estimado con error de dos semanas.

**Lo que sí se puede hacer con fenología satelital (donde el error de días importa poco):**
- **Fechas de siembra y emergencia**, maíz/soya, EE.UU.: **R² = 0,87, MAE = 2,5 días** para soya; a escala de condado, diferencia absoluta media < 4 días y RMSE < 5 días. **[S]** (Nota: green-up detectado ≠ emergencia; el primero **retrasa** sistemáticamente al segundo.)
- **Momento de máxima sensibilidad para predecir rendimiento**: girasol se predice a **85-105 días** del ciclo, en **floración**, que resultó el momento más sensible. **[S]**
- Trigo: los índices óptimos **cambian con el estadio** — biomasa, pigmentos y humedad antes de encañado; **índices de red-edge después de encañado**. **[S]**

---

## 5. "¿Se pueden detectar distintos cultivos por firma espectral?" — SÍ, PERO NO COMO SE CREE

### 5.1 La corrección conceptual más importante de este informe

**No se distinguen cultivos por "firma espectral" en el sentido de una imagen de una fecha.** Maíz y soya comparten calendario y tienen características espectrales altamente similares, lo que genera confusión de clasificación; determinar el tipo de cultivo desde imágenes de fecha única **sigue siendo un desafío** por la complejidad de la señal intra e inter-lote. Soya y maíz son especialmente inseparables **en llenado temprano de vaina**. **[S]**

Lo que sí discrimina es la **trayectoria temporal** — la forma de la curva a lo largo del ciclo. La firma que separa cultivos es **fenológica, no espectral instantánea**. Las fechas de transición (floración, madurez) son lo que mitiga la variabilidad espectral entre años. **[S]**

### 5.2 Efectividad medida (antecedentes duros)

| Sistema | Qué | Exactitud | Fuente |
|---|---|---|---|
| **USDA CDL 2025** | EE.UU. continental, **10 m** (antes 30 m), publicado 27-feb-2026. Random Forest en GEE (`ee.Classifier.smileRandomForest`), sobre HLS S2 L2A + L8/L9 C2 T1, composites mediana de 10 días de reflectancia y NDVI | Capa de confianza en modo MULTIPROBABILITY. **La confianza NO debe usarse como medida de exactitud** — un píxel puede estar bien clasificado con confianza baja cuando varios cultivos tienen firmas similares | [S] |
| **ICDL (in-season CDL)** | 10 m, junio/julio/agosto, latencia **5 días** | Exactitud de clasificación **0,807 (junio) → 0,984 (agosto)**; exactitud de las etiquetas de entrenamiento 0,825-0,937. **Supera consistentemente al CDL anual** | [S] |
| **ESA WorldCereal** | Global, 10 m, S1+S2, temporadas actualizadas | **Maíz**: exactitud de usuario 85,8%, de productor 75,5%. **Cereales de invierno**: UA 93,6%, PA 77,7%. Fase II amplía a 8 cultivos (girasol, colza, mijo, sorgo, trigo, cebada, centeno, soja) | [S] |
| **Transformer CONUS within-season** | Landsat + S2 HLS, 3 transformers (uno por sensor + uno de fusión) | Mapeo robusto y oportuno dentro de la campaña | [S — no pude leer el paper, ScienceDirect 403] |
| **EnMAP + S2 dual-stream** | Hiperespectral + serie multiespectral, clasificación jerárquica fina | **+4,2% F1 promedio, pico +6,3%** sobre S2 solo | [S] |
| **Mapa Nacional de Cultivos, INTA (Argentina)** | 4ª edición; clasificación supervisada sobre índices de Landsat, con verdades de campo de 28 unidades del INTA, zonificado según el Panorama Agrícola Semanal de la Bolsa de Cereales | Argentina es **uno de los cinco países** con sistema satelital de seguimiento de cultivos extensivos | [S] |
| **EEAOC Tucumán (caña)** | Sentinel-2 (A, B y C) + relevamiento intensivo a campo, enero-mayo, estimación de superficie cosechable y producción para la zafra | Serie desde 1997; primer mapa cañero del país con 3 niveles de producción | [S] |

### 5.3 Qué se necesita para hacerlo (recursos concretos)

**Datos (todos gratuitos):**
- Serie temporal densa: **HLS v2.0** (L8/L9 + S2A/B/C armonizados, < 1,6 días de revisita mediana) o S2 L2A directo.
- Radar para llenar huecos de nube: **S1 GRD** (revisita 6 días desde mayo 2026) o **SAOCOM** en Argentina.
- Etiquetas de referencia: **CDL** (EE.UU.), **EuroCrops** (Europa), **WorldCereal** (global, incluye base de datos de referencia abierta), **Mapa Nacional de Cultivos del INTA** (Argentina). **En Bolivia y en el oriente boliviano NO existe equivalente** — hay que generarlo con relevamiento propio.

**Procesamiento:** GEE (investigación), **CDSE + openEO** (ruta comercial), o descarga + rasterio/xarray local.

**Método mínimo que funciona:**
1. Compuestos por décadas o cada 10 días sobre la ventana del cultivo, con enmascarado de nube agresivo.
2. Features = bandas + índices + métricas de forma de curva (fecha de green-up, de pico, de senescencia, amplitud, integral).
3. Random Forest o transformer temporal.
4. **Verdades de campo locales, obligatorias.** Sin ellas, ni un foundation model generaliza.

**Efectividad esperable en nuestro contexto (Santa Cruz / Bolivia):** 
Con 2-3 fechas bien elegidas y verdades de campo propias, soya vs maíz vs sorgo vs girasol es alcanzable en el rango 85-95% de exactitud global. Sin verdades de campo locales, no.

---

## 6. Qué hay en ARGENTINA (por pedido explícito)

Argentina tiene el ecosistema público de teledetección agrícola más desarrollado de la región, y buena parte es reutilizable.

| Producto | Organismo | Qué entrega | Acceso |
|---|---|---|---|
| **Mapas de humedad superficial de suelo** | CONAE (SAOCOM) | Región pampeana, **10 m, precisión 7%**, seguimiento de la campaña para soja, maíz, trigo y girasol | Catálogo SAOCOM 1 / Geoportal CONAE, libre y gratuito |
| **Clasificación de cultivos SAOCOM** | CONAE | Producto operativo de la constelación | Ídem |
| **Índice Radar de Vegetación (RVI)** | CONAE | Desarrollo del cultivo **bajo nube** | Ídem |
| **Mapas de Índice de Producción** | CONAE + INTA | Trigo, maíz, soja, girasol, sobre modelo de cultivo que integra SAOCOM | Ídem |
| **Mapa de incidencia de fusariosis en trigo** | CONAE/INTA | Zonas de mayor riesgo en ambientes pampeanos | Ídem |
| **Mapa Nacional de Cultivos Extensivos** | INTA (28 unidades) | Clasificación supervisada Landsat + verdades de campo, por campaña | Público |
| **N-INTA** | INTA + Auravant | Prescripción de N variable, trigo y maíz | Gratuito dentro de Auravant |
| **Plataforma de servicios geoespaciales INTA** | INTA | NDVI, SAVI, EVI, zonificación intra-parcela, estimación de LAI | Web |
| **Estimación de superficie y producción de caña** | EEAOC (Tucumán) | Sentinel-2 A/B/C + campo, zafra a zafra | Reporte Agroindustrial |
| **Mapas de rindes a escala predial** | IDECOR (Córdoba) | Soja y maíz, información satelital + geográfica + relevamiento + ML | Público |

**Qué copiar de ellos:** la arquitectura institucional (verdades de campo sistemáticas + producto público + validación por campaña). **Qué NO copiar:** los umbrales — están calibrados para la pampa húmeda, con suelos, variedades y régimen hídrico que no son los de Santa Cruz.

---

## 7. Qué hay en ESTADOS UNIDOS (por pedido explícito)

| Producto | Qué es | Estado 2026 |
|---|---|---|
| **CDL** (USDA-NASS) | Capa nacional de tipo de cultivo | **10 m desde 2025**, RF sobre GEE con HLS |
| **ICDL** | CDL dentro de la campaña, mensual jun-jul-ago | 10 m, **latencia 5 días**, 0,807→0,984 de exactitud |
| **HLS v2.0** (NASA) | Reflectancia armonizada + productos VI | Global, retro a 2013, < 1,6 días |
| **OpenET** | ET a escala de lote, ensamble de 6 modelos | 30 m, EE.UU. continental, r² = 0,9 en cropland |
| **NISAR** | SAR banda L+S | Lanzado 30-jul-2025, humedad de suelo 200 m |
| **Foundation models** | Prithvi (NASA/IBM), AlphaEarth (Google) | Disponibles; degradan bajo cambio regional |

**El patrón norteamericano es claro y es el que hay que leer:** el valor no está en el índice, está en el **producto operativo, validado, con latencia declarada y exactitud publicada**. CDL no publica un índice: publica una capa con matriz de confusión. OpenET no publica NDWI: publica milímetros con MAE declarado.

---

## 8. Los 11 cultivos de la casa — qué está probado y qué no

| Cultivo | Qué está probado por satélite | Qué NO |
|---|---|---|
| **Trigo** | Fenología (±8-13 d), NNI/N por red-edge, biomasa/LAI, roya amarilla (REDSI, OA 85-87%), rendimiento por asimilación en SAFY (mejora >70% en variabilidad espacial), fusariosis por riesgo ambiental (Argentina) | Proteína en grano a tiempo de decidir (R²≈0,4). Rango óptimo absoluto por estadio: **no existe** |
| **Soya / soja** | Fecha de siembra (MAE 2,5 d), mapeo (S1+S2, alta exactitud), rendimiento por asimilación en DSSAT con LAI+LNA, discriminación vs maíz **solo multitemporal** | Separación de maíz en fecha única, sobre todo en llenado temprano de vaina |
| **Maíz** | NNI vs NDRE R²=0,79; rendimiento a nivel condado con ML; PRI sigue eficiencia de uso de radiación bajo secado de suelo (2025); fenología S1 | NDVI satura después de V8 — usar kNDVI/NDRE/CIre |
| **Caña de azúcar** | Superficie y producción (EEAOC, décadas de serie); rendimiento con S1-VOD + S2-GRVI; ~70% de la variación de rendimiento con RF multitemporal S2 en São Paulo; biomasa con SAFY-Sugar | **Pol / sacarosa NO se mide con S2** — ya está medido internamente y la literatura 2025 sigue trabajando sobre biomasa de tallo, no sobre concentración de azúcar |
| **Sorgo** | Biomasa en campos comerciales con fAPAR de S2 + sensores próximos; WorldCereal Fase II lo incorpora | Poca literatura específica; sin tablas por estadio |
| **Girasol** | Rendimiento a 85-105 días, **floración = mejor momento**, RF sobre bandas S2; producto SAOCOM de índice de producción | Ídem sorgo |
| **Papa** | Fenología completa S1+S2 (emergencia, cierre, floración, senescencia, cosecha); rendimiento con NDVI/SAVI + ML | Calidad de tubérculo |
| **Tomate** | Kc desde óptico como fuente confiable para decisiones de riego durante todo el ciclo del tomate de industria; ET, LAI y altura con S2+VENµS; asimilación regional | Calidad de fruto |
| **Pimentón** | Nada específico encontrado. Se extrapola de tomate | Todo lo demás |
| **Palta** | S2 5 años + ERA5-Land + geomorfometría explican variabilidad de rendimiento y calidad (República Dominicana, 2025); añerismo/alternancia con ML sobre NDVI, GNDVI, NDRE, CIG, CIRE, EVI2, LSWI (Limpopo, 2025); estado hídrico con NDWI + sensores de suelo | Escala **por árbol** con satélite: no encontré evidencia. Requiere UAV |
| **Maracuyá** | Nada específico encontrado | Todo |
| *(bonus)* **Chía** | Un estudio satelital grande: la chía consume **13-38% menos agua** que alfalfa, maíz y soja, y asimila **14-20% más carbono por unidad de agua** (Communications Biology, 2024) | Monitoreo operativo, índices calibrados |

---

## 9. Combinaciones de índices: qué agrega información y qué es redundante

Esta sección responde "¿qué combinación de índices según los nuevos hallazgos?" — y la respuesta va contra la corriente comercial.

**Lo que NO agrega:** sumar más índices ópticos de banda ancha. 86 índices revisados, altamente correlacionados entre sí; en nuestros propios lotes, 0,97-0,998 de correlación espacial entre los 5 principales. **Agregar el sexto índice agrega ruido, no información.**

**Lo que SÍ agrega, en orden de relación valor/esfuerzo:**

1. **Tiempo** — residuo contra la escena limpia anterior, no contra la media de temporada. Ya implementado en la casa; la literatura de fenología y de clasificación converge en lo mismo.
2. **Textura (GLCM / NDTI)** — dimensión estructural ortogonal a la reflectancia. NDTI con NIR + red-edge + azul supera a todos los VIs evaluados y a las texturas GLCM solas. Combinado VI+textura: R² 0,78-0,84. **Es el hueco más grande de nuestro pipeline actual.**
3. **Radar (S1/SAOCOM/NISAR)** — estructura y agua bajo nube; VOD para biomasa. Independiente por física, no solo por estadística.
4. **Ángulo (BRDF multi-angular)** — recupera estructura 3D de canopia (distribución de ángulo foliar, altura, porosidad) que **ningún índice de ángulo único puede capturar**. Poco explotado; S2 no lo permite bien, pero conviene tenerlo en el radar.
5. **kNDVI en lugar de NDVI** donde hay saturación. Costo: una línea.
6. **Transformación por kernel / features aprendidas** (foundation models) — solo con verdades de campo locales.

**Combinaciones específicas con respaldo:**
- Clorofila/N: **MTCI o CIre + NDRE**, normalizados por P95 de cohorte → NNI relativo.
- Detección de enfermedad en trigo: **red-edge después de encañado**; biomasa/pigmento/humedad antes.
- Rendimiento de caña: **S1-VOD + S2-GRVI**.
- Riego/no riego: **SAVI + VH de S1** (diferencias pico de 0,48 unidades de SAVI y 2,78 dB en VH); RF con OA 87,8-91,0%.
- Biomasa: **VIs + GLCM**, o mejor, asimilar LAI en un modelo de cultivo (SAFY/DSSAT/APSIM) con filtro de Kalman de ensamble.

---

## 10. Lista NO-CITAR (lo que circula y no aguanta)

1. **"Rangos óptimos de NDVI/NDRE por cultivo y estadio fenológico"** como tabla universal. No existe. Los umbrales no transfieren ni entre mitades del mismo lote (brecha medida de 35,66 puntos).
2. **"NDVI mide la salud del cultivo."** Mide verdor/estructura; satura; confunde biomasa con vigor.
3. **"SIF permite ver el estrés de su lote antes que nadie."** Cierto en física, falso en escala: el mejor píxel operativo hoy es de 1,3 × 2,25 km y el futuro FLEX será ~300 m. Los propios autores del review dicen que ni FLEX sirve dentro del lote.
4. **"El térmico satelital da CWSI a nivel de lote."** Cierra a escala de lote con datos libres. Lo que funciona es UAV térmico.
5. **"Detectamos malezas por satélite."** Sentinel-2 a 10 m es "generalmente insuficiente" para datos a nivel de planta o de rodal; incluso UAV con RGB tiene omisión de malezas del 41-65%.
6. **"El satélite mide el nitrógeno del cultivo."** Mide clorofila de canopia, que se relaciona con N bajo supuestos. NNI relativo sí; kg de N absolutos no.
7. **"La capa de confianza del CDL es su exactitud."** El propio USDA advierte que no debe usarse como medida de exactitud.
8. **"Medimos sacarosa/Pol de caña por Sentinel-2."** Ya estaba en nuestra lista NO-CITAR; nada en 2025-2026 lo cambia.
9. **"El foundation model X generaliza globalmente."** Los benchmarks controlados muestran degradación abrupta bajo cambio de distribución regional, prediciendo solo los cultivos comunes.
10. **"LAI de SNAP es exacto."** Subestima 20-50% cuando LAI > 2; sin corrección con datos in situ no sirve para valores absolutos.
11. **"Reducimos 50% el nitrógeno con satélite (INTA)."** El dato existe pero es de comunicación institucional sobre un ensayo con **dron**, no un paper revisado ni un resultado satelital general.
12. **"Los índices de vegetación son independientes entre sí, por eso combinarlos da robustez."** Correlacionan 0,97-0,998. La conjunción de dos índices ópticos no es una doble verificación.

---

## 11. Qué hacer con esto en Pixadvisor — acciones concretas

**Alta prioridad (cambian resultados, costo bajo):**

1. **Agregar textura (GLCM/NDTI) como segundo eje** del detector de anomalías y del mapa de vigor. Es la única dimensión verdaderamente ortogonal barata que encontré, y la literatura la respalda con R² 0,78-0,84 en biomasa. Hoy nuestro "segundo eje" es otro índice óptico correlacionado.
2. **Sustituir NDVI por kNDVI** donde hay saturación (maíz post-V8, trigo post-encañado, caña cerrada). Cambio de una línea, respaldo en *Science Advances*.
3. **Re-medir la disponibilidad de S1 sobre Santa Cruz después de mayo 2026** — S1D operativo restablece revisita de 6 días. Nuestro número medido de S2∪S1 = 87% puede haber mejorado.
4. **Dejar de indexar por "estadio fenológico" y mantener el criterio de cohorte.** Este informe le pone número al porqué: ±8-13 días de error en la fenología satelital de trigo.

**Media prioridad:**

5. **Evaluar CDSE + openEO como ruta de procesamiento comercial**, ahora que WorldCereal demostró que un sistema global entero corre ahí. Resuelve el problema de licencia de GEE cuando llegue el primer cliente que pague.
6. **Producto de ET a escala de lote**: no existe un OpenET sudamericano. Es hueco de mercado, y la metodología está publicada y auditada.
7. **Para clasificación de cultivos en Bolivia**: no hay etiquetas públicas. El activo defendible es nuestra propia base de verdades de campo — el mismo patrón que hace valioso al CDL y al Mapa Nacional del INTA.

**Baja prioridad / vigilar:**

8. NISAR: cuando los productos estén estabilizados, la humedad de suelo a 200 m y la banda L sobre caña merecen una prueba.
9. Foundation models (AlphaEarth 64-dim, 10 m, ya publicado como dataset): probar como features **complementarias** con verdades de campo propias, nunca como clasificador plug-and-play.

---

## 12. Bibliografía

**Leídas directamente [V]:**
- Ruehr, S., Pierrat, Z.A., Parazoo, N., Keenan, T.F. (2026). Harnessing solar-induced fluorescence for on-farm agricultural research and management: recent advances and outstanding needs. *Environmental Research Letters* 21(11):111007. doi:10.1088/1748-9326/ae74e2
- Zhao, Y., Jiang, R., Brider, J., Chapman, S., Potgieter, A. (2025). Characterizing wheat and barley growth and phenology using multi-spectral remote sensing for site-specific precision agriculture. *in silico Plants* 7(2):diaf013. doi:10.1093/insilicoplants/diaf013
- Brown, C.F. et al. (2025). AlphaEarth Foundations: An embedding field model for accurate and efficient global mapping from sparse label data. arXiv:2507.22291. doi:10.48550/arXiv.2507.22291

**Citas con referencia confirmada, texto no leído [S]:**
- Yan, K., Gao, S., Yan, G., Ma, X., Chen, X., Zhu, P. et al. (2025). A global systematic review of the remote sensing vegetation indices. *International Journal of Applied Earth Observation and Geoinformation* 139:104560.
- Camps-Valls, G. et al. (2021). A unified vegetation index for quantifying the terrestrial biosphere. *Science Advances*. doi:10.1126/sciadv.abc7447 [kNDVI]
- Automated 10-m Resolution In-season Crop-type Data Layer Mapping for Contiguous United States. *Scientific Data* (2026). s41597-026-07099-1
- Robust and timely within-season conterminous United States crop type mapping using Landsat Sentinel-2 time series and the transformer architecture. *Remote Sensing of Environment* (2025). S0034425725003542
- Fine-grained hierarchical crop type classification from integrated hyperspectral EnMAP data and multispectral Sentinel-2 time series. *Remote Sensing of Environment* (2026). S0034425726002956
- Assessing the accuracy of OpenET satellite-based evapotranspiration data. *Nature Water* (2023). s44221-023-00181-7
- Satellite observations indicate that chia uses less water than other crops in warm climates. *Communications Biology* (2024). s42003-024-06841-y
- Multi-dimensional optical remote sensing in agriculture: Spectral, angular, and spatial scaling for crop stress monitoring. *Smart Agricultural Technology* (2025). S2772375525008147
- Wheat yield prediction using integrated optical and radar remote sensing with machine learning across key phenological stages. *Scientific Reports* (2026). s41598-026-41501-7

**Fuentes institucionales:**
- USDA-NASS, Cropland Data Layer Releases y CropScape — nass.usda.gov/Research_and_Science/Cropland/
- NASA HLS — hls.gsfc.nasa.gov/data-products/ y earthdata.nasa.gov
- ESA WorldCereal — esa-worldcereal.org
- Copernicus Data Space Ecosystem / openEO — dataspace.copernicus.eu
- CONAE Argentina, productos SAOCOM para agro — argentina.gob.ar
- INTA, Mapa Nacional de Cultivos y N-INTA — argentina.gob.ar/inta
- EEAOC Tucumán, estimación de superficie y producción de caña — eeaoc.gob.ar
- IDECOR Córdoba, mapas de rindes prediales — idecor.gob.ar

**Marcado explícitamente como no confiable para citar:**
- arXiv:2512.21948, *Interpretable Machine Learning-Derived Spectral Indices for Vegetation Monitoring* — preprint sin revisión por pares; de ahí sale el dato de la brecha de 35,66 puntos.
- Notas de prensa institucional de INTA sobre la reducción del 50% de N con dron.

---

## 13. Pendientes de esta investigación

Lo que quedó sin verificar y por qué:

1. **ScienceDirect devolvió 403** en los cuatro papers clave que quería leer completos (review de índices de Yan, transformer CONUS, EnMAP+S2, multi-dimensional stress). Los números de esos están marcados [S].
2. **Nature devolvió redirección de autenticación** en el paper del ICDL de 10 m y en el de rendimiento de trigo óptico+radar. Los números de exactitud por mes del ICDL (0,807→0,984) vienen del resumen del buscador y **deberían confirmarse antes de usarlos con un cliente**.
3. **El benchmark "Harvesting AlphaEarth"** no se pudo extraer (PDF binario). Es la evidencia más directa sobre si los embeddings sirven para tareas agronómicas reales; vale la pena reintentarlo.
4. **Maracuyá y pimentón**: no encontré literatura satelital específica. Puede que exista en portugués o en repositorios latinoamericanos no indexados por el buscador.
5. **No busqué** en profundidad: detección de compactación, mapeo de rastrojo/labranza, seguros paramétricos, ni fenotipado de mejoramiento.
