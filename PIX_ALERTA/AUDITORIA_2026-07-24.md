# PIX ALERTA — Auditoría de construcción

Fecha: 2026-07-24. Audita `ESPECIFICACION.md` contra el código y los datos que realmente existen.
Todo lo que dice "medido" se midió con los scripts de `medicion/`, sobre escenas reales de Santa Cruz.

---

## Resumen en cinco frases

1. El motor v7 no vive en la skill: la skill despacha v6. El v7 real está en
   `C:\Users\Usuario\Desktop\PIXADVISOR_Sync\repo\` y corre en producción desde el 19-jul.
2. El entregable que la especificación define como el producto —la lista ordenada de lotes a
   visitar— no tiene una sola línea de código detrás: la entidad "lote" no existe en el motor.
3. El gatillo estadístico que se presenta como la ventaja competitiva marca **~30% de la superficie
   siempre**, y estratificar por zona de suelo no lo cambia. Es una cuota, que es exactamente lo que
   la Decisión 3 prohíbe.
4. No existe **ni un solo registro** de plaga o enfermedad observada en campo, ni **una sola** fecha
   de siembra. Sin el primero no hay nada que validar; sin el segundo el Paso 2 no es implementable.
5. La disponibilidad óptica a escala de lote es **48% de las dekadas**. La cadencia de 10 días con
   producto pleno se rompe una vez de cada dos.

---

## 1. Paso 0 — disponibilidad real de imagen (la pregunta abierta nº 1, ya respondida)

Medido con `medicion/paso0_disponibilidad.py` y `paso0_lote_y_mes.py`: 5 campañas de verano
(1-oct a 30-abr), 110 dekadas, zona este de Santa Cruz. Escena "útil" = ≥80% de píxeles válidos
tras descartar nube **y sombra** (SCL 3, 8, 9, 10).

| Unidad | Dekadas con escena útil |
|---|---|
| Lote de ~100 ha | **53/110 = 48,2%** |
| AOI de ~700 km² | 39/110 = 35,5% |

Por campaña, a escala de AOI: 45,5% · 40,9% · 31,8% · 31,8% · 27,3% (2021/22 → 2025/26).

Por mes, a escala de lote: oct 55% · nov 60% · **dic 40%** · ene 60% · **feb 33%** · mar 47% · abr 40%.

Complemento con radar y con óptica parcial:

| Fuente | Cobertura de dekadas |
|---|---|
| S2 ≥80% útil | 48,2% |
| S2 parcial (40-80%) | +10,9% |
| S1 disponible | 69,1% |
| **S2 ≥80% ∪ S1** | **87,3%** |

**Lectura.** La escalera de tres estados que el pipeline ya tiene (informe pleno / boletín radar /
no-op) no es un parche: es obligatoria. Y el producto degradado no es el caso raro, es el 52% de
las entregas. Febrero es el peor mes y es plena presión de plagas.

---

## 2. El hallazgo que obliga a repensar el criterio

### El gatillo Gi\* + FDR marca ~30% del campo, pase lo que pase

Medido con `medicion/gi_escala.py`, `cadena_v7_real.py` y `gi_nulo_y_estratos.py` sobre una escena
S2 real sin nubes (2026-01-06, T20KNF), 2.779 ha de dosel, unidades de 20 m, Gi\* con 999
permutaciones condicionales y FDR de Benjamini-Hochberg a α=0,05 — el mismo criterio del motor:

| Configuración | Superficie marcada como coldspot |
|---|---|
| Campo real, sin estratificar | **33,3%** |
| Campo real, estratificado en 3 zonas de suelo | **30,3%** |
| Test a 10 m / 20 m / 30 m | 35,0% / 34,1% / 37,1% |
| **Control: los mismos valores barajados en el espacio** | **0,0%** |

El control nulo es la prueba de que **la implementación es correcta**: bajo aleatoriedad espacial
completa el test no marca nada. El problema no es el código, es la pregunta.

Gi\* contrasta contra la hipótesis nula de aleatoriedad espacial. Esa hipótesis es **falsa por
construcción en cualquier lote agrícola**: siempre hay suelo, siempre hay topografía, siempre hay
gradiente de siembra. Rechazarla no informa nada. La tasa de rechazo no la fija la enfermedad: la
fija la fuerza de la autocorrelación. Por eso estratificar por suelo casi no la mueve.

Es exactamente lo que la propia especificación advierte citando a Efron (`10.1198/016214506000001211`),
pero medido: el motor que se construyó para no usar cuantiles produce **una cuota del 30%**.

### Qué está realmente decidiendo el color

Reproduciendo la cadena completa (`cadena_v7_real.py`), la superficie total marcada es 28,1% y
**no depende del Mahalanobis** — el Mahalanobis solo reparte ese 28% entre Prioritario y Vigilancia.
Y ese reparto es frágil:

| Features del Mahalanobis | Prioritario | Vigilancia |
|---|---|---|
| 7 índices (motor v7 actual), χ² df=7 | 3,2% (113 ha) | 24,9% (881 ha) |
| 2 ejes (Decisión 1 de la spec), χ² df=2 | 21,9% (772 ha) | 6,3% (221 ha) |

Cambiar los grados de libertad mueve la superficie roja de 113 a 772 ha sobre el mismo campo, el
mismo día. La selectividad del producto está gobernada por un parámetro que nadie validó.

### La Decisión 1 está confirmada, y el motor la incumple

Medido con `medicion/dimensionalidad_indices.py` sobre 4.656 píxeles de dosel de la misma escena,
para los 7 índices que el motor mete en el Mahalanobis:

- PC1 = 69,7%, PC1+PC2 = 90,4%
- Número efectivo de índices independientes: **2,40** (entropía) / **1,87** (participation ratio)
- Correlaciones: CIre–NDRE 0,97 · CIre–REDSI 0,98 · TCARI/OSAVI–MCARI 0,95

Hay dos bloques, no siete. El motor evalúa χ² con df=7 sobre una dimensionalidad efectiva de ~2:
el umbral está inflado y la métrica cuenta la misma información cinco veces.

---

## 3. Estado real de los cinco activos que la spec manda reutilizar

### 3.1 Motor de anomalías — parcialmente conforme, y no está donde dice

La skill `deteccion-anomalias-cultivos-satelital` despacha **v6** (`scripts/anomaly_engine.py:2`); el
v7 nunca se portó (la propia skill lo dice: *"portar aca cuando se actualice"*). Prueba dura: la
skill exige una máscara con BSI pero su `disease_indices.py` no calcula BSI.

De los 8 pasos:

| Paso | Estado |
|---|---|
| 1 Máscara | **Mal.** Solo Cloud Score+ ≥0,60. **Sin clase de sombra** en el camino de producción (SCL está en un fallback opt-in). Sin dilatación. Buffer negativo de 10 m, no 5. Descarte por hacienda entera, no por lote |
| 2 Estratificación | **Mal.** `if/else` entre zona de suelo **o** cohorte — nunca cruzadas. Y ningún script genera el ráster de cohorte: es un binario precocido |
| 3 Magnitud | **Bien en forma, mal en eje.** SI vs P95, continuo, sin umbral — pero el P95 es de la zona de suelo, no de la cohorte |
| 4 Agrupamiento | **Lo mejor construido.** Permutación condicional real, FDR adaptativo, α declarado, barrido de sensibilidad. Falla en la escala (testea a 10 m) — y, según §2, la escala no es su problema principal |
| 5 Persistencia | **No existe.** Lo que llama "eje temporal" es una razón de una fecha contra la media de la temporada, con umbral fijo 0,93 hardcodeado. Sin EWMA, sin tiempo térmico. Además la ventana de referencia **incluye la fecha analizada**: el píxel enfermo contamina su propio baseline |
| 6 Prior meteo | No existe |
| 7 Salida | **No existe la que importa.** Sin probabilidad posterior, sin prevalencia. Y **sin ranking de lotes**: `grep -i lote` sobre el repo de producción da cero |
| 8 Validación | No existe |

Bordadura: el motor hace lo contrario de lo que pide la spec — la erosiona como "principal fuente de
falsos positivos".

Umbrales absolutos vivos en un motor que declara no tener ninguno: `CANOPY=0.50`, `BSI_SOIL=0.05`,
`NDRE_MIN=0.15`, `TEMP_DECL=0.93`. El comentario del código lo admite: *"cutoffs anclados al dato
real SA/SF 2026-07-15"* — calibrados contra una escena, de un cultivo, de dos haciendas.

### 3.2 Pipeline en nube — la ingeniería está bien, la escalabilidad no

Lo bueno, y hay que conservarlo: escalera de 3 estados con contrato de exit codes (0 no-op / 10
entregable / 1 error), idempotencia por estado versionado en git sin base de datos, `ee_init.py`
limpio con cuenta de servicio, aviso WhatsApp que degrada sin romper, determinismo con semillas
fijas. Corre estable, 8 corridas verdes seguidas.

Lo que bloquea:

- **El repo no puede arrancar una hacienda nueva por sí solo.** Los rásters `ambientes.tif` y
  `strata.tif` que definen la grilla y el área útil **no los escribe ningún script**: vienen de otro
  proyecto y están commiteados como binarios opacos. Este es el cuello de botella real, más que el
  hardcode.
- Diccionarios de haciendas duplicados en 3 archivos; cultivo "trigo" literal en 6 sitios; fechas de
  campaña 2026 hardcodeadas en el `.py`.
- Las geometrías son **un polígono por hacienda, sin atributos**. No hay lotes.
- Los IDs de foco se **renumeran en cada corrida** (`P1..Pn` ordenados por severidad). El P3 de hoy
  no es el P3 de la escena anterior: no hay identidad que seguir en el tiempo.
- `history.json` guarda 4 números agregados por hacienda. No hay serie por lote. **No se puede
  reconstruir la trayectoria de nada.**

Tres defectos activos que conviene arreglar aunque no se construya PIX ALERTA:

1. `history.json` quedó inconsistente con el baseline re-sembrado (SA 4,70 vs 3,16 ha; SF 3,85 vs
   0,99 ha). El primer informe óptico dibujará una caída que es cambio de método, no agronomía.
2. `check_new` toma solo `max(escenas)`: si el cron se cae y aparecen una limpia y una nublada, la
   limpia **se pierde para siempre**. No hay `--force` ni `--date`.
3. El PDF del cliente describe *"estrato de siembra"* y *"P95 de la cohorte"* — método que el motor
   ya no usa desde el rediseño del 22-jul.

Costo real de generalizar: sacar nombres a un JSON ≈ 1 día; escribir el bootstrap de máscaras
≈ 2-3 días; **re-anclar los umbrales por cultivo ≈ 1-2 semanas de campaña por cultivo**, que es
tiempo agronómico, no de programación.

### 3.3 El lazo de retorno — la spec se equivoca: ya existe al 65%, y en otra app

`ESPECIFICACION.md` §3 dice *"hoy nada captura qué encontró el técnico"* y apunta a
`pix-muestreo-apk`. Las dos cosas son incorrectas.

**PIX_SCOUT ya es una APK firmada y distribuible** (`pix-scout-v1.0.3.apk`, 2,4 MB,
`network.pixadvisor.scout`) con PWA offline, IndexedDB, cola de sync idempotente y foto obligatoria.

| Campo del esquema §3 | PIX_SCOUT | pix-muestreo-apk |
|---|---|---|
| `punto_id` estable | Existe pero **colisiona** (50 de 101 duplicados) | No (autoincremental local) |
| `lote_id` | Disponible, no se guarda | Sí |
| `fecha_visita` | Sí | Sí |
| `estrato_asignado` oculto | **No — y muestra la severidad** | n/a |
| `hallazgo` | Parcial, **sin opción "nada"** | No |
| `especie` (vocabulario controlado) | **Sí: 123 fichas, 7 cultivos** | No |
| `severidad` | Ordinal subjetivo, no escala MIP | No |
| `conteo` | **No existe** | No |
| `supera_umbral` | Autodeclarado, **no calculado** | No |
| `foto` | **Sí, obligatoria** | Código sí, apagada y no se sube |
| `observacion` | No | Sí |

Los 123 registros del banco de fichas son sólidos y sirven **tal cual** como vocabulario controlado.
Pero los 26 umbrales MIP con fuente citable son **prosa libre**, no valores: una sola ficha mete tres
umbrales, dos unidades y una condición fenológica en un string. `supera_umbral` hoy no es calculable;
es un botón que aprieta el técnico.

Y hay dos conflictos de fondo, no campos que falten:

- **La app viola la regla no negociable por diseño.** Su pantalla principal es la lista *"Ordenados
  por severidad (Gi\* + FDR)"*, con chips de severidad, mapa por color y la pregunta *"¿Coincide con
  el aviso del satélite?"*. Cumplir §3 y §4 exige un modo de captura distinto, no ocultar un campo.
- **No se puede registrar "no había nada".** Sin registro negativo no hay falsos negativos, y §4
  exige muestrear el estrato verde precisamente para eso.

`pix-muestreo-apk` está al ~15% y en peor posición: formulario hardcodeado campo por campo (≈28
ediciones para los 7 campos nuevos), sin ID estable, sin vocabulario, foto desactivada a propósito.

### 3.4 Piezas estadísticas ya escritas y reutilizables

- FCM + FPI/NCE con autotest que verifica la orientación del índice contra el paper (skill de vigor).
- Gi\* + FDR adaptativo + Mahalanobis-MCD con α declarado (motor de anomalías).
- Z robusto por MAD, media local enmascarada, vectorización con MMU.
- **`prioridad_muestreo.py` del proyecto de caña es el módulo mejor construido del workspace**: Z con
  piso de SD en vez de gate, bootstrap que propaga la incertidumbre del denominador, anclaje absoluto
  capaz de devolver "no pasa nada", diagnóstico de colinealidad previo. Opera sobre DataFrame, sin
  credenciales. **No lo importa nadie**: el CSV lo sigue produciendo la versión con cuartiles vivos.
- Descarga por tiles + merge para el límite de 48 MB (`_serroalto_s2_tif_tiled.py`).

No existe en ningún lado: EWMA, CUSUM o cualquier carta de control; grados-día por cultivo; detección
de cambio sobre series; estado persistente por unidad para disparar avisos.

---

## 4. Los datos — el bloqueo más duro, y no es de software

### Fecha de siembra: cero registros

Búsqueda exhaustiva en workspace y archivo. Los únicos aciertos son esquemas vacíos y un fallback
inventado (`planting_date = field.get('plantingDate', '2025-11-15')`). La plantilla
`plantilla_datos_hacienda.csv` existe desde hace meses, dice en su propio encabezado que estas
variables predicen mejor que cualquier índice satelital, **y está vacía**.

→ **El Paso 2 no es implementable hoy.** La cohorte no se puede declarar. Se puede *estimar* por
quiebre de la serie NDVI (el clasificador ya calcula `n_drops` y `months_since_drop`), y hay que
rotularla como estimada.

### Observaciones de plaga o enfermedad: cero registros

Ni una sola observación georreferenciada en toda la cartera. El campo `Notas` del único muestreo real
de campo (20 puntos, 2026-05-15) está vacío en las 20 filas.

→ **No hay nada contra qué validar ni calibrar.** Precisión@K, PR-AUC y prevalencia son, hoy,
métricas sin numerador.

### Lo que sí hay

| Activo | Detalle |
|---|---|
| **HDS** | **220 lotes con ID estable único**, 4.943 ha, EPSG:4326 |
| **HDS — serie NDVI** | **3.094 filas = 221 lotes × 14 meses (2025-03 → 2026-04)**. El `lote_id` cruza 220/221 con el maestro. **Única base histórica del proyecto** |
| HDS — zonas de manejo | ~110 lotes zonificados, CSV + GeoJSON por lote |
| Cerro Alto | 37 lotes base / 66 divisiones, 168 zonas de ambiente por color de suelo. **Cero historia temporal** |
| Alto Tacuarí | 61 + 17 lotes con ID |
| Santo Antonio / Sao Francisco | **1 perímetro / ninguno.** Las dos haciendas del pipeline en producción no tienen lotes |
| Campo Verde | 900 ha declaradas, **cero geometrías** |
| `pixadvisor_lots.db` | Esquema SQLite ya diseñado (`crop`, `mean_ndvi`, `temporal_stability`, versionado, `lot_history`). **3 filas de demo.** Conviene reutilizarlo en vez de inventar otro |

Análisis de laboratorio: 28 de suelo y ~138 foliares, **ninguno georreferenciado**. No hay un solo
dataset punto↔resultado unible.

---

## 5. Consecuencias para la especificación

Lo que hay que corregir en `ESPECIFICACION.md`:

1. **§3 y §6** — PIX_SCOUT debe ser la primera fila de la tabla de activos. La frase *"hoy nada
   captura qué encontró el técnico"* es falsa; lo correcto es que lo capturado **no es reproducible**
   (umbral no calculado, sin conteo) **ni válido para medir** (sin registro negativo, sin ciego, ID
   colisionado).
2. **§11 pregunta 1 — respondida:** 48% a escala de lote, 35% a escala de AOI. Ya no es una pregunta.
3. **§2 Paso 2 — no implementable:** no existe fecha de siembra. Hay que degradar a cohorte estimada
   por satélite y declararlo, o conseguir el dato.
4. **§2 Paso 4 — el criterio necesita reformularse.** No por un defecto de implementación, sino
   porque la hipótesis nula espacial es falsa por construcción y produce una cuota del 30%.
5. **Decisión 1 confirmada y no aplicada:** dimensionalidad efectiva ~2 contra df=7 en producción.
6. **§6** — el motor v7 no está en la skill. Y el pipeline no puede arrancar una hacienda nueva sin
   un bootstrap que no existe.

---

## 6. Scripts de esta auditoría

En `medicion/`, todos ejecutables y reproducibles (semillas fijas):

| Script | Qué mide |
|---|---|
| `paso0_disponibilidad.py` | Dekadas con escena útil por campaña, escala AOI |
| `paso0_lote_y_mes.py` | Lo mismo a escala de lote y desglosado por mes |
| `dimensionalidad_indices.py` | PCA y nº efectivo de índices independientes de las 7 features |
| `gi_escala.py` | Gi\*+FDR a 10 / 20 / 30 m |
| `cadena_v7_real.py` | Cadena completa coldspot ∩ Mahalanobis, df=7 vs df=2 |
| `gi_nulo_y_estratos.py` | Control nulo con valores barajados + efecto de estratificar |

---

## 12. Segunda pasada (revisión de punta a punta, misma fecha)

Cinco auditorías paralelas + batería de prueba y contraprueba. ~60 defectos, corregidos
salvo lo que se lista al final.

### Contrapruebas del motor, sobre la escena real del 15/07

| Prueba | Resultado | Qué prueba |
|---|---|---|
| CT1 · escena contra sí misma | **0,0%** | el motor no inventa estructura |
| CT2 · residuo barajado en el espacio | **0,0%** | bajo aleatoriedad espacial no marca nada |
| CT3 · **tiempo invertido** | ver abajo | si la señal es direccional |

**CT3 destapó el defecto de fondo.** Analizando el 10/07 con el 15/07 como referencia
(o sea, mirando hacia atrás):

| Capa | Hacia adelante | Hacia atrás |
|---|---|---|
| Prioritario | 0,63 ha | **0,00 ha** |
| Vigilancia (antes del arreglo) | 12,31 ha | **12,50 ha** |
| Vigilancia (después) | 4,72 ha | 2,35 ha |

Una capa que marca lo mismo en las dos direcciones no es evidencia de deterioro: es la
heterogeneidad normal entre dos escenas. Vigilancia no exigía declive. Corregido.

### Límite de detección medido (fixture con anomalía inyectada)

| Área inyectada | Magnitud | Detectado prioritario | Falso positivo en el campo sano |
|---|---|---|---|
| 10,2 ha | 100% | 10,00 ha | 0,00 ha |
| 4,5 ha | 100% | 1,94 ha | 0,00 ha |
| 2,0 ha | 100% | 1,64 ha | 0,00 ha |
| **0,8 ha** | 100% | **0,00 ha** | 0,00 ha |
| 10,2 ha | 60% | 1,84 ha | 0,00 ha |
| 10,2 ha | **25%** | **0,00 ha** | 0,00 ha |

**Piso de detección: ~2 ha a magnitud plena, ~10 ha a 40% de magnitud.** Cero falsos
positivos en las ocho configuraciones.

### El estimador de escala de PIX ALERTA — cuatro versiones

Objetivo: SD(z) ≈ 1 bajo la nula. Medido sobre la campaña real de HDS.

| Estimador | SD del z | Por qué falla |
|---|---|---|
| MAD del propio lote | — | el denominador elige el ranking |
| Rango móvil ÷ √2 | **2,9** | supone independencia temporal; el ρ real es 0,73 |
| Dispersión marginal de fase I | **2,9** | la heterogeneidad **crece** en la campaña |
| **MAD transversal entre lotes, por fecha** | **1,17** | — |

El control nulo también estaba ciego: permutar identidades dentro de cada fecha dejaba
cada serie iid, o sea destruía la autocorrelación que importaba, y reportaba ~0% pasara lo
que pasara. Ahora usa rotación circular. Resultado real: **0–3,6% marcado contra un nulo
de 1,1%** — discriminación débil, y sin dato de campo no se puede saber si es porque la
campaña estuvo tranquila o porque el criterio quedó poco sensible.

### Coherencia operativa — lo que hay que decidir

Sobre la corrida real de Santo Antonio (125 ha de área útil):

- **20 focos** (5 prioritarios + 15 de vigilancia), 5,35 ha = 4,3% de la superficie.
- **15 de los 20 miden menos de 0,25 ha** (50×50 m). Mediana: 34 m de lado en prioritario,
  43 m en vigilancia.
- AAPRESID recomienda **1 estación cada 10-15 ha** → para 125 ha son 8-12 estaciones.
  El motor entrega **2× esa densidad**.

Y hay una incoherencia interna: el test espacial corre a **10 m** (la especificación pide
agregar a 20-30 m antes de testear) mientras la MMU de vectorización es `MIN_HA = 0.05` =
**5 píxeles de 10 m**. Si el test se agregara a 20-30 m como corresponde, esos 500 m²
serían 1,2 unidades — por debajo de cualquier MMU razonable. **Las dos decisiones hay que
tomarlas juntas**: agregar el test a 20-30 m y subir la MMU a ~0,2-0,3 ha.

### Cadena completa verificada de punta a punta

20 focos emitidos por el pipeline → 20 cargados por la app → 20 en el registro guardado,
**todos con `focoIdEstable: true`**, con `estrato` y `fechaImg`. El perímetro viaja en el
mismo archivo (2 anillos) y la app lo usa para encuadrar el mapa. El ID sobrevive el viaje.
