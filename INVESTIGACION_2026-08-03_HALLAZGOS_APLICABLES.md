# Investigación dirigida — qué es aplicable al motor, medido

**3 de agosto de 2026.** Cinco frentes en paralelo (India, EE.UU., Argentina ×3) más medición propia sobre
los lotes reales del cliente TRIGO.

A diferencia del informe general de estado del arte, este documento parte del **problema concreto del
motor** y solo retiene lo que lo toca:

| # | Problema del motor | Estado tras esta investigación |
|---|---|---|
| **P1** | Los 2 ejes correlacionan ρ = 0,969 → 6,1% de varianza independiente | 🟢 **Candidato encontrado y medido sobre lotes propios** |
| **P2** | Campo chico: 2-4 lotes, sin cohorte | 🟡 Marco estadístico identificado; sin solución directa |
| **P3** | 48% de dékadas con imagen útil | 🔴 **Decisión: NO rellenar.** Confirmado por 5 estudios |

---

## P1 — EL SEGUNDO EJE: entropía polarimétrica dual-pol

### La evidencia externa

**Demirci, A.E.F. & Sunar, F. (2026).** *Overcoming Optical Gaps: Evaluating SAR–Optical Consistency for
Cotton Phenology.* ISPRS Archives XLVIII-4/W18-2025:89-94.
DOI 10.5194/isprs-archives-XLVIII-4-W18-2025-89-2026. Algodón, 11 lotes, **n = 240 pares S1/S2 apareados ±2 días**.

| Variable SAR | r con óptico | Veredicto |
|---|---|---|
| Retrodispersión VH | **0,930** NDVI · 0,928 ARVI · 0,924 EVI | REDUNDANTE |
| Stokes g₀ (potencia total) | 0,933 NDWI | REDUNDANTE |
| Cociente VH/VV | 0,339 EVI · 0,330 NDRE | mayormente redundante |
| **Entropía H** | **0,115 GCI · 0,012 NDVI · 0,015 NDWI** | **ORTOGONAL** |
| **Alpha α** | **0,112 GCI · 0,020 EVI** | **ORTOGONAL** |

Los autores: los parámetros de descomposición *"codifican procesos de dispersión en gran medida
ortogonales a las señales ópticas dirigidas por clorofila o agua"*.

**Confirmación en trigo indio:** Singh, S. et al. (2022), *Int. J. Remote Sensing* 43(19-24):6921-6935,
DOI 10.1080/01431161.2022.2150098. IIT-BHU Varanasi. **DpRVI (S1) → LAI: R² = 0,822.** Sentinel-2 TOA:
R² = 0,816. Misma exactitud desde física completamente distinta, sin nubes.

**Definición** (Mandal, D. et al. 2020, *Remote Sensing of Environment* 247:111954,
DOI 10.1016/j.rse.2020.111954), sobre la matriz C2 con autovalores λ₁ ≥ λ₂:

```
m     = (λ1 − λ2)/(λ1 + λ2)      grado de polarización
β     = λ1/(λ1 + λ2)             grado de dominancia
DpRVI = 1 − m·β                  rango 0-1
```

### 🔬 La medición propia — y el hallazgo técnico que la condiciona

**Primero, la trampa que casi me lleva puesto.** La entropía de Cloude-Pottier necesita la matriz de
covarianza C2 **completa**, y sus elementos fuera de la diagonal requieren la **fase relativa** entre VV y
VH. Verificado en GEE:

```
COPERNICUS/S1_GRD  → bandas: ['VV', 'VH', 'angle']   ← amplitudes detectadas, SIN FASE
COPERNICUS/S1_SLC  → NO EXISTE en Earth Engine
```

**La entropía verdadera no es computable con los datos disponibles.** Lo único posible desde GRD es la
versión que asume **C2 diagonal**, donde λ₁ = max(VV,VH) y λ₂ = min(VV,VH) — es decir, una función solo
del cociente VV/VH.

**Medido sobre SÃO FRANCISCO** (S1 del 2026-07-25 vs S2 del 2026-08-01, píxel a píxel a 20 m sobre los
lotes reales):

| Descriptor SAR | r NDVI | r NDMI | r NDRE |
|---|---|---|---|
| **Entropía H** (diagonal) | **−0,012** | **0,009** | **0,005** |
| **DpRVI** | −0,020 | 0,002 | −0,001 |
| VH/VV | −0,028 | −0,002 | −0,004 |

Los números replican el orden de magnitud del estudio turco (0,012-0,115). **Contra ρ = 0,969 del par
actual, esto es otra escala de independencia.**

### ⚠️ Por qué NO alcanza para adoptarlo, y qué falta

Cuatro reservas, en orden de gravedad:

1. **Correlación ~0 puede ser información independiente O puede ser speckle puro.** El SAR tiene ruido
   multiplicativo fuerte; a nivel de píxel individual el speckle destruye cualquier correlación. Que
   VH/VV también diera ~0 acá —cuando el estudio turco le midió 0,339— es exactamente el síntoma de que
   **el speckle está dominando mi medición**. Baja correlación es **necesaria pero no suficiente**.
2. **Medí correlación ESPACIAL de una fecha, no de RESIDUOS TEMPORALES.** El criterio del motor opera
   sobre residuos contra la trayectoria del propio píxel. La comparación válida contra el 0,969 es la de
   residuos, y esa no está hecha.
3. **La evidencia externa total son ~25 lotes**, tres estudios de una sola temporada y un solo sitio cada
   uno, con correlación descriptiva en muestra. Y uno de ellos (Habeebulla et al. 2026, *AUC Geographica*
   61(2):241-255, DOI 10.14712/23361980.2026.6) mide **R² predictivo de 6,9×10⁻⁵ lineal y 2,6×10⁻⁴ con
   Random Forest**: ortogonal sí, informativo no demostrado.
4. **Los índices radar entre sí correlacionan r > 0,90** — el mismo problema que los cinco ópticos. Entra
   **uno solo**, no tres.

**Trampa adicional a evitar** (Mandal, D. 2024, InGARSS, DOI 10.1109/INGARSS61818.2024.10984422): las
descomposiciones de **potencia de dispersión** portadas de compact-pol a VV-VH son **ambiguas** sin la
fase co-pol — no separan triedro de diedro. Usar cantidades basadas en **autovalores** (H, α, DpRVI), no
descomposiciones de potencia.

### Lo que hay que hacer antes de tocar `config.EJES`

El mismo protocolo de tres patas que la casa ya exige, sin excepciones:

1. `medicion/textura_como_eje.py` adaptado → |ρ| de **residuos temporales** H vs NDMI
2. `medicion/calibrar_criterio.py --ejes NDMI,H` → tasa empírica sobre fechas sin evento
3. `medicion/comparar_ejes.py` → lift contra la nula sintética sobre las 3 campañas de HDS

Si el lift no supera al par actual, **no se cambia**.

---

## P2 — CAMPO CHICO: la India tiene la regla escrita, y va en contra

**YES-TECH Manual for Implementation**, Mahalanobis National Crop Forecast Centre, DA&FW India, enero
2023. MNCFC exige **≥ 4 Unidades de Seguro contiguas por estrato**. Justificación textual: 4 UI × 4 años =
16 escenarios, mientras que *"si cada UI se trata como entidad discreta/independiente, hay solo cuatro
escenarios, y una base tan limitada no puede representar la variabilidad total de respuestas del cultivo,
llevando a pesos sesgados"*.

**Ese es el planteo operativo indio del problema de cohorte, y aplica literalmente a la matriz de
covarianza 2×2 y a la escala MAD con 2-4 lotes.**

### Aritmética que acota todo

A **20 m** — resolución **nativa** de B5, B6, B7, B8A, B11 (o sea de NDRE, NDMI y PSRI):

| Lote | píxeles a 20 m | tras erosionar 1 píxel de borde |
|---|---|---|
| 1,0 ha | 25 | ~9 |
| 0,5 ha | 12 | **~4** |

Cualquier estadístico espacial intra-lote en 0,5 ha corre con **grados de libertad de un dígito**.
(Los lotes de TRIGO son de 40-90 ha, así que esto no muerde hoy — pero fija el piso del producto.)

### El marco estadístico correcto, y es argentino

**Paccioretti, P.; Bruno, C.; Giannini Kurina, F.; Córdoba, M.; Bullock, D.S.; Balzarini, M. (2021).**
*Statistical models of yield in on-farm precision experimentation.* **Agronomy Journal 113(6):4916-4929.**
DOI 10.1002/agj2.20833.

Sobre **8 experimentos on-farm** compara regresión lineal con errores espacialmente correlacionados,
bayesiano con efectos aleatorios de sitio, y random forest con kriging de residuos. Los tres resultan
indistinguibles en varianza explicada media, pero **el bayesiano tiene menor incertidumbre predictiva que
el RF** y mejor exactitud sitio-específica que la regresión lineal.

Con pocas unidades, el **modelo jerárquico bayesiano con estructura espacial** es el que entrega
incertidumbre honesta. No es teledetección, pero es el marco correcto.

### Techos honestos de desempeño — para no prometer de más

**Joshi, A.; Bishop, T.; Weaver, T.; Deo, R.; Filippi, P. (2026).** *Detecting cotton Verticillium wilt
within and across multiple fields with Sentinel-2 imagery and machine learning.* **Agronomy Journal 118.**
DOI 10.1002/agj2.70485. 7 fincas australianas.

> **Dentro del lote (interpolación): OA media = 0,63. Entre lotes (extrapolación): 0,58.**
> Y el mejor predictor fue un covariable **no satelital** (conteo de inóculo pre-siembra).

**Regla operativa: si el Mahalanobis de 2 ejes reporta algo por encima de ~0,65 contra verdad de campo
real, sospechar fuga antes de festejar.**

### El modo de falla dominante, cuantificado

**Huang, X.; Vrieling, A.; Dou, Y.; Li, X.; Nelson, A. (2025).** *Int. J. Appl. Earth Obs. Geoinf.*
139:104559. DOI 10.1016/j.jag.2025.104559.

F1 por tamaño de lote × estrés hídrico (maíz/soya):

| | sin estrés | estresado |
|---|---|---|
| Lote grande | 0,89 / 0,85 | 0,82 / 0,59 |
| Lote chico | 0,85 / 0,68 | **0,77 / 0,37** |

> **El estrés degrada la misma señal que se usa para detectarlo.** El error dominante van a ser **falsos
> negativos en exactamente los lotes que pagan por marcar**, no falsas alarmas.

Esto reorienta la calibración: el motor está calibrado contra falsa alarma (0,00% mediana), pero el
riesgo real está del otro lado.

---

## P3 — NUBES: la decisión es NO RELLENAR, y ahora está fundamentada

**Ningún paper 2023-2026 valida reconstrucción SAR→óptico a escala de residuo/anomalía.** Todos los R² de
titular se calculan sobre la curva fenológica completa: son escala-tendencia.

**La aritmética que lo cierra:** amplitud estacional de NDVI ≈ 0,70, SD ≈ 0,25. Como R² = 1 − (RMSE/SD)²,
un **RMSE de 0,075 da R² ≈ 0,91 automáticamente, con cero habilidad de anomalía**. El residuo por píxel
del motor es σ ≈ 0,010-0,020 (`SIGMA_MINIMA = 0,010`) y una anomalía accionable es 2-4σ ≈ 0,02-0,08.

| Estudio | RMSE/MAE en NDVI | vs la anomalía del motor |
|---|---|---|
| Chen, Y. et al. (2024) BRIOS, DOI 10.1080/17538947.2024.2407941 | RMSE 0,075 (R 0,97) | **1-4× mayor** |
| Mohite, J.D. et al. (2020), DOI 10.5194/isprs-archives-XLIII-B3-2020-1379-2020 | arroz RMSE 0,08 | **2-4× mayor** |
| Ayari, E. et al. (2024), DOI 10.1080/15481603.2024.2357878 | RMSE 0,12-0,19 | **4-10× mayor** |
| Tsardanidis, I. et al. (2025), DOI 10.1016/j.compag.2024.109732 | MAE 0,024 (el mejor) | ≈ igual |

**El número más demoledor:** Defonte, V. et al. (2026), arXiv:2605.04239 — modelo generativo profundo
multimodal S1+S2 da MAE 0,016 / RMSE 0,025, contra **interpolación lineal simple MAE 0,018 / RMSE 0,030**.
Ablación: multimodal 0,020 vs solo-óptico 0,023 → **el SAR compra 0,003 de reflectancia, ~13%**.

> Si una recta entre dos fechas limpias es casi tan buena, los modelos reproducen la **tendencia**, no la
> **desviación**. **El ajuste lineal por píxel que el motor ya hace extrae lo mismo que la fusión SAR.**

Y peor: Ayari et al. tuvo que **partir la temporada en espigazón** porque la relación S1↔NDVI **invierte
de signo** por dispersión de volumen. No es una función estable dentro de una ventana de 120 días.

**Arquitectura confirmada:** correr solo sobre fechas S2 genuinamente limpias, declarar el resto
**no-evaluable** con conteo explícito, y si se usa S1 que sea como **eje de confirmación independiente en
su propia escala**, nunca como NDVI sintético metido en el ajuste. Es exactamente lo que el motor ya hace.

### El costo de rellenar, MEDIDO en detección de eventos

**Tsardanidis, I. et al. (2025).** *Comput. Electron. Agric.* 230:109732. Tabla 5, detección de corte de
pastura con dos algoritmos independientes:

| Algoritmo | Relleno | Recall | Precisión | F1 |
|---|---|---|---|---|
| MDA I | ninguno | **0,755** | 0,717 | 0,736 |
| MDA I | lineal | 0,719 | 0,800 | 0,757 |
| MDA II | ninguno | **0,762** | 0,730 | **0,746** |
| MDA II | lineal | **0,635** | 0,843 | **0,724** |

> **La interpolación lineal costó 12,7 puntos de recall — un evento real de cada ocho desaparece.**
> Y en MDA II el F1 con relleno quedó **peor** que sin rellenar nada.

Y el redireccionamiento de la inversión: los autores atribuyen la ganancia de precisión no a rellenar sino
a *"the SF model's ability to correct cloudy observations"*. **La plata está en la máscara de nubes, no en
el relleno** — coincide exactamente con los tres focos falsos que ya costaron una entrega acá.

**Los suavizadores están diseñados para borrar la anomalía**, y no es interpretación:
- **Chen, J. et al. (2004)**, *RSE* 91(3-4):332-344, DOI 10.1016/S0034-4257(04)00080-X — el Savitzky-Golay
  más citado **itera hasta converger a la envolvente SUPERIOR**, porque asume que toda depresión es
  atmósfera. Estructuralmente ciego a una caída real. **PROHIBIR.**
- **Kandasamy, S. et al. (2013)**, *Biogeosciences* 10:4055-4071 — el preprocesamiento estándar borra como
  outlier *"values that are substantially different from both their left- and right-hand neighbors"*: **borra
  justo el objeto que se busca**. Y se degrada rápido con >20% de faltantes; acá hay 52%.
- **Garioud, A. et al. (2021)**, *RSE* 263:112419, apéndice C — con un hueco de ~1 mes sobre un corte total
  de biomasa, interpolación lineal y Whittaker produjeron *"a gradual but not significant decrease,
  preventing abrupt change detection"*. **No la atenuaron: la eliminaron.**

### Un detector que MEJORA cuando le sacan datos

**Awty-Carroll, K., Bunting, P., Hardy, A., Bell, G. (2019).** *Remote Sensing* 11(23):2779.
DOI 10.3390/rs11232779. **151.200 series simuladas con verdad conocida.** Acierto en la fecha real del
cambio: **EWMACD 76,6%**, CCDC 51,8%. Y la frase decisiva: *"All methods showed some decrease in
performance with increased noise and missing data, **apart from BFAST Monitor which improved when data
were removed**."*

⚠️ **Calibración honesta del mismo linaje:** contra verdad-terreno real en vez de simulada, EWMACD da
**comisión 39,9%, omisión 65,2%, F1 = 0,13** (Bright, B.C. et al. 2017, *Forests* 8(9):304,
DOI 10.3390/f8090304). En disturbios sutiles la omisión es del 65-70%. No es bala de plata.

---

## Hallazgos que cambian el criterio, no solo el catálogo

### 1. El ajuste por MCO se sabotea a sí mismo

**Mouret, F. et al. (2022).** *Comput. Electron. Agric.* **198**:106983. DOI 10.1016/j.compag.2022.106983.

Su método es de cohorte y no aplica, **pero el patrón de diseño sí**: un píxel con anomalía real en el día
90 **arrastra la recta de mínimos cuadrados hacia sí y encoge su propio residuo**. El motor ajusta una
recta por píxel con MCO sobre 120 días — tiene exactamente ese problema.

**Acción: Theil-Sen o Huber en vez de MCO.** Es un cambio acotado con efecto directo en sensibilidad.

### 2. Dos ejes físicamente distintos separan enfermedad de deficiencia de N

**Shi, Y.; Han, L.; González-Moreno, P.; Dancey, D.; Huang, W. et al. (2023).** *Frontiers in Plant
Science* 14. DOI 10.3389/fpls.2023.1250844. Parcelas ~10×10 m apareadas al píxel S2, **validación
independiente en sitios y años separados**: OA 91,14-95,13%, kappa 0,847-0,891.

Separa roya de deficiencia de nitrógeno combinando un eje **estructural** (LAI vía WDVI) con uno de
**pigmentos** (TCARI/OSAVI). **El poder discriminante vino de hacer los dos ejes físicamente distintos, no
de encontrar un índice mejor.** Es el problema ρ = 0,969 resuelto por construcción.

⚠️ Pero ojo con TCARI/OSAVI: la evidencia argentina a escala de píxel lo desaconseja (ver abajo).

### 3. El tiempo térmico le gana al calendario

**Duan, K.; Vrieling, A.; Schlund, M.; Nidumolu, U.B.; Ratcliff, C.; Collings, S. (2024).** *ISPRS J.
Photogramm. Remote Sens.* 213:33-52. DOI 10.1016/j.isprsjprs.2024.05.021. EVI2 re-indexado sobre eje de
**tiempo térmico** en vez de fecha calendario; desviación respecto del esperado dentro de ventanas
fenológicas, a nivel **sub-lote**. **R² = 0,83 trigo, 0,91 cebada**, ~2 meses antes de cosecha.

⚠️ **No verificado** si el "esperado" sale de la historia del propio lote o de una envolvente poblacional.
Si es poblacional, no aplica. **Pendiente de resolver a mano** (es CC-BY).

**Lo que sí aplica igual:** la ventana de 120 días **calendario** del motor es el punto débil. Con siembra
extendida 9 días en Santo Antonio y madurez asincrónica, una recta sobre días calendario absorbe estrés
real en la pendiente.

### 4. La regla de máscara asimétrica de India

YES-TECH: **error de comisión < 10%, omisión tolerada hasta 20%**. Vale copiarla para que la covarianza se
estime sobre píxeles de cultivo inequívocos.

---

## Evidencia argentina a escala de píxel — respalda los dos ejes actuales

**Ovando, G. et al. (2021).** *Agriscientia* 38(2). DOI 10.31047/1668.298x.v38.n2.25148. Un lote de 48 ha,
**48.788 puntos de monitor de rendimiento**, kriging a grilla de 10×10 m. **Escala píxel, intra-lote.**

| Índice | \|r\| | R² aprox |
|---|---|---|
| **B8 − B12** (NIR − SWIR2) | **0,726** | **≈0,53** |
| B8/B11 | 0,611 | ≈0,37 |
| **NDMI** (B8/B11 normalizado) | 0,605 | ≈0,37 |
| **NDVI** | **0,436** | **≈0,19** |

**El SWIR le gana claramente al NDVI dentro del lote.** Respalda NDMI como primer eje.

**Marini, F. et al. (2026).** *Revista de Teledetección* (AET). DOI 10.4995/raet.2026.25177. 7 parcelas,
**88.929 mediciones de monitor**, 9 fechas, clasificación en 3 clases por píxel:

- **NDRE y NDVI red-edge: A > 86%** — los mejores
- NDWI 84,9% · SAVI 84,1% · EVI 82,3%
- **MCARI, TCARI, PRI, CI Green: 82,2-83,8%** — los peores

**El red-edge ganó; los biofísicos tipo TCARI/MCARI quedaron últimos.** Respalda NDRE como segundo eje y
**desaconseja volver a TCARI/OSAVI**, pese a Shi et al. 2023.

**Y el dato que respalda decir "no evaluable":** cuando Marini bajó el número de fechas, el modelo cayó de
A > 86% a **73% con Kappa < 0,5, declarado no confiable por los propios autores**. Con 48% de dékadas
útiles, ese es el régimen. **Es evidencia publicada de por qué el motor a veces debe callar.**

**El argumento de escala, con cita:** **Menendez-Coccoz, M. et al. (2025).** *Agronomy Journal*
117(3):e70089. DOI 10.1002/agj2.70089. Mismos datos, mismo modelo: **16% de error a nivel de lote, 4% a
nivel regional.** Es la demostración revisada por pares de que **agregar espacialmente infla la precisión
aparente**. Ningún R² departamental respalda nada intra-lote.

---

## 🇦🇷 Lo que sí sirve de Argentina (barrido de actas CAI/JAIIO + repositorio INTA)

Revisadas **81 contribuciones** de CAI 2022-2025 más el repositorio INTA vía el cosechador oficial del
Estado (SNRD). Tres piezas útiles y un hallazgo negativo contundente.

### 1. Tus ejes exactos, validados intra-lote en Argentina

**D'Amico, M.B.; Marini, F.; Calandrini, G.; Renzi Pugni, J.P.; Chantre, G.R. (2024).** *Factibilidad de
predecir el nivel de rendimiento de Vicia villosa utilizando distintos índices de vegetación satelitales.*
**Memorias de las JAIIO 10(3):15-26** (CAI 2024). [ACTAS CON ARBITRAJE]

Los índices evaluados incluyen **NDVI red-edge = (B8−B5)/(B8+B5)** y **SR = B8/B11** — o sea, un índice de
borde rojo sobre B5 (el NDRE del motor) y una razón NIR/SWIR (primo directo del NDMI), evaluados sobre
**variabilidad dentro del lote** ("manchones", distribución no homogénea por área).

| | |
|---|---|
| Exactitud global | **82-86%**, kappa ≈ **0,70** |
| Mejor índice individual | LAI SeLi: 86%, kappa 0,72 |
| **Fechas necesarias** | **5 fechas alcanzan** (incluso 4). Con 3 o 2 se cae |

> **El hallazgo operativo: 5 fechas alcanzan.** El 48% de dékadas útiles del motor **no es fatal** — es un
> régimen con el que otros ya trabajan y publican. Es el único trabajo argentino con los mismos ejes, a
> escala de manchón intra-lote, con número.

### 2. La munición argentina contra la "exactitud global"

**Barrionuevo, N.; Havrylenko, S.; Sepulcri, M.; Casella, A.; Espíndola, G. (2025).** *Detección
automática del riego por pivote central…* **Memorias de las JAIIO 11(3):15-28** (CAI 2025). INTA Instituto
de Clima y Agua. Versión revisada: *SADIO Electronic Journal*, DOI 10.24215/15146774e103.

| Métrica | Valor |
|---|---|
| **Exactitud global** | **98,31%** |
| **Sensibilidad** | **58,28%** |
| Especificidad | 99,96% |
| **Tasa de falsos negativos** | **41,72%** |
| F1 | 73,20% |

> **Exactitud global del 98,3% perdiéndose el 42% de los objetos reales.** Es un caso publicado, argentino,
> de INTA, con la tabla completa, de por qué **la exactitud global es una cuota disfrazada cuando la clase
> positiva es rara**. Es exactamente el argumento para reportar tasa de falsa alarma y precisión@K en vez
> de exactitud — y ahora tiene cita nacional.

### 3. Campo chico, medido: por debajo de 30 muestras el modelo local se degrada

**García Seleme, Paccioretti, Balzarini, Córdoba (2025).** *Mapeo de materia orgánica a escala de lote…*
**Memorias de las JAIIO 11(3):1-14.** Siete lotes en Córdoba y Santiago del Estero, algunos con n = 17.

Textual: *"los modelos de predicción local **pierden capacidad predictiva cuando la cantidad de muestras
del lote es baja (< 30)**, sin importar el método"*.

→ Es la evidencia argentina del dilema del cliente de 2-4 lotes. Y **refuerza la arquitectura del motor**:
la serie temporal por píxel entrega las N observaciones que la cohorte espacial no puede dar.

### 4. Un protocolo de validación a campo, publicado

**Gentili, J. et al. (2023).** VII Congreso de la Red Argentina de Salinidad. Estratificaron un lote de
soya por índices satelitales y dispusieron las unidades experimentales **en los límites entre manchones, de
a tres, perpendiculares al borde y separadas 1 m**, formando un gradiente.

→ **Muestrear cruzando el borde del manchón, no dentro.** Directamente aplicable a los puntos de control a
ciegas. (Resumen de congreso, sin números.)

### ⚠️ El paper que parece contradecir "no rellenar" — y por qué no lo hace

**Caballero, G.; Pezzola, A.; Winschel, C.; ... Verrelst, J. (2023).** *Synergy of Sentinel-1 and
Sentinel-2 Time Series for Cloud-Free Vegetation Water Content Mapping with Multi-Output Gaussian
Processes.* **Remote Sensing 15(7):1822.** DOI 10.3390/rs15071822. INTA Hilario Ascasubi + Univ. València.

Borrando **todas** las escenas S2 de septiembre a diciembre y reconstruyendo píxel a píxel:
**R̄² = 0,95 (2020) y 0,96 (2021)**, NRMSE 10,1-16,1%. Trigo de invierno argentino, 2 campañas.

**Por qué no contradice la decisión de no rellenar — tres razones:**

1. **Mide la curva, no la anomalía.** Es exactamente el patrón que ya está documentado arriba: con SD
   estacional grande, un R² de 0,95 sale casi automáticamente sin ninguna habilidad de detectar una
   desviación. Reconstruye el ciclo fenológico; nadie midió si conserva un foco.
2. **El sitio elegido tiene poca nubosidad** — valle irrigado semiárido del sur bonaerense. Se probó donde
   el problema es menor que acá.
3. **Es riego, no secano subtropical.** La dinámica de agua está controlada.

**Lo que sí vale:** es la referencia argentina revisada por pares para la sinergia S1+S2 en **trigo**, y
si algún día se construye una capa de contenido de agua de dosel —no un gatillo de anomalía— este es el
método y el número de referencia.

### Hallazgo negativo que vale como posicionamiento

En **81 contribuciones de CAI (2022-2025)** más el repositorio INTA más OpenAlex con filiación INTA:

- **Cero trabajos de detección de anomalías intra-lote por trayectoria del propio píxel.**
- **Cero detección satelital de enfermedad a escala intra-lote con exactitud reportada**, en ningún cultivo.
- **La Argentina subtropical (NOA/NEA) no tiene teledetección de cultivos publicada con validación.** Lo
  único que la cubre usa Landsat/MODIS y no reporta exactitud.
- **El propio Mapa Nacional de Cultivos del INTA documenta que pierde exactitud hacia el norte**, *"asociado
  a eventos de sequía y altas temperaturas"*. Es el argumento de no-transferencia al subtrópico **firmado
  por INTA**.

---

## ❌ CORRECCIONES a mi propia investigación anterior

### C1 — SAOCOM: el producto no existe sobre los lotes del cliente

Le informé al usuario *"humedad de suelo a 10 m con precisión del 7%"*. **Eso salió de una nota de prensa
y es falso.** Verificado contra la documentación técnica de CONAE:

| Afirmación | Realidad documentada |
|---|---|
| "10 m" | Es la resolución de la **imagen SAR StripMap**, no del producto. El metadato ISO del propio producto declara *"resolución de pixel de **3,5 km**"* |
| "mide humedad" | SAOCOM ve **5 cm nominales**. Todo lo demás es **DSSAT** (modelo de cultivo) corrido a paso diario con asimilación EnKF y kriging encima |
| "validado" | El MSMKR que se distribuye solo tiene **intercomparación con SMAP L4**: R² = 0,46, pendiente 0,63. El producto PSM declara por escrito que **no se puede validar** |
| disponible | **Bounding box: lon [−68,30, −56,66] × lat [−41,03, −27,99]** — cinco provincias argentinas. **Paraná y Santa Cruz están FUERA.** No es licencia: el producto **no se genera ahí** |
| descargable | Login + **reCAPTCHA**. Un cron de GitHub Actions no lo baja |

Y CONAE lo dice explícitamente: *"Lotes muy próximos podrían dar resultados equivalentes."* Dos lotes
vecinos reciben el mismo valor por construcción.

**Mapa de fusariosis: [PRODUCTO SIN VALIDACIÓN PUBLICADA].** Cero números en la especificación técnica,
cero papers, y la referencia base (Moschini et al. 2016) **tiene la URL caída en la propia documentación
de CONAE**.

### C2 — N-INTA / Auravant: no hay ciencia detrás

Lo presenté como "validado en la región pampeana". **Sale de notas de prensa.** La ficha institucional no
cita publicación, ni ensayos, ni R². El centro de ayuda remite a "papers" en **enlaces de Google Drive**.
Toda la obra indexada del responsable es sobre nitrógeno en **maíz**; ninguno valida el algoritmo satelital
de trigo. Usa **NDVI** (no red-edge) en Z3.1.

---

## 🟢 La línea nueva: riesgo epidemiológico climático

El satélite no ve la roya ni la fusariosis. **El clima que las fabrica sí se calcula** — y no necesita
imagen óptica ni cohorte, o sea que esquiva P2 y P3 de golpe.

**La epidemiología está publicada y parametrizada:**
- **Roya asiática** (Alves et al. 2006; Del Ponte et al., Brasil): temperatura óptima **15-25 °C**, mojado
  foliar **mínimo 6 h**, eficiencia creciente con 10-12 h. Modelos empíricos con lluvia explican
  **85-93% de la variación** de severidad.
- **Fusariosis** (Moschini, INTA Clima y Agua): mojado de espiga por lluvia + humedad alta en torno a
  antesis. Publicado desde 1996, con predicción retrospectiva **1932-2013** en Paraná y Pergamino.
  **Argentina lleva 30 años haciendo exactamente esto.**

**El mojado foliar se estima sin sensor de campo:** Random Forest sobre ERA5 da **exactitud horaria 83%,
precisión 78,2%, MAE diario 2,8 h, RMSE 4 h** — supera a MERRA2 y a modelos de HR observada.

**Verificado en la infraestructura propia (GEE):**
```
ECMWF/ERA5_LAND/HOURLY → 168 imágenes en 7 días sobre São Francisco (horario completo)
bandas: temperature_2m, dewpoint_temperature_2m, viento, presión, precipitación
T=20,3 °C · Td=16,4 °C → HR=78% (Magnus)
LATENCIA MEDIDA: última imagen 2026-07-28 → 6 días de retraso
```

**Límite declarado:** 6 días de latencia. Sirve para riesgo **acumulado retrospectivo**, no para alerta en
tiempo real.

**Verdad de campo externa y gratuita:** el **Consórcio Antiferrugem** (Embrapa, ~100 laboratorios) publica
ocurrencias confirmadas en tiempo real. Zafra 2025/26: **144 registros, 88-110 en Paraná** — donde están
Santo Antonio y São Francisco.

---

## Lista NO-CITAR ampliada

Además de la lista anterior:

1. **"Humedad de suelo SAOCOM a 10 m"** — el metadato ISO de CONAE dice 3,5 km.
2. **"El radar mide la humedad"** — lo que llega es DSSAT con EnKF y kriging.
3. **"Mapa de fusariosis SAOCOM validado"** — cero métricas publicadas.
4. **"N-INTA validado"** — sin publicación revisada por pares.
5. **"MNC tiene 92% de exactitud"** — la global está dominada por "no agrícola" (0,99). **Sorgo: 0,11.
   Girasol: 0,40.** Y la validación 60/40 parte polígonos, no sitios: sesgo optimista.
6. **95,17%** (James et al. 2025, ASIANCON) — **las etiquetas las fabricó un Isolation Forest**. Circular.
7. **89,4%** (Seralathan & Edward 2025, *Sci Rep*) — split aleatorio de píxeles **dentro de los mismos 10
   lotes de la misma campaña**. Autocorrelación espacial.
8. **R² = 0,91 intra-lote** (Gavilán et al. 2023) — **n no declarado**, ajuste polinómico, una campaña.
9. **Karnal bunt por satélite** — cero papers en cualquier país. No hay mecanismo físico.
10. **Roya asiática por satélite** — el paper insignia (Negrisoli et al. 2022, *Agronomy Journal*
    114(6):3246) son **hojas cortadas medidas en laboratorio con espectrofotómetro**.

---

## Negativos limpios (valen tanto como los hallazgos)

- **No existe ningún estudio que compare scouting dirigido por satélite contra scouting sistemático** y
  mida problemas encontrados por hora. Ni en EE.UU., ni en ningún lado, ni antes de 2022.
- **Ningún paper de teledetección agrícola reporta una tasa de falsa alarma empírica** para un detector
  tipo SPC. Todos publican alfa nominal. **El motor ya la tiene medida.**
- **Ningún programa operativo indio** hace detección de anomalías por píxel contra la historia del propio
  píxel. No hay ajuste de tendencia por píxel, ni estandarización robusta de residuo temporal, ni
  Mahalanobis contra χ², ni FDR en ningún documento operativo indio. **Todo agrega antes de testear.**
- **Ningún paper valida el paquete completo** "tendencia por píxel sobre ~120 d → residuo → MAD →
  Mahalanobis 2 ejes vs χ²". Las piezas existen sueltas. **El motor no está replicando a nadie.**
- **RX / Reed-Xiaoli** (que es exactamente Mahalanobis sobre el vector espectral) está consolidado en
  hiperespectral, **pero no aplicado a residuos temporales de cultivo en S2.** Hueco disponible.
- **El LART/IFEVA argentino no trabaja en anomalía intra-lote.** El nicho del motor no está cubierto por
  el grupo argentino de referencia.
- **Chinches: sigue sin detectarse** (Iost Filho et al. 2022, *Agronomy* 12(7):1516) — diferencia
  espectral mínima incluso con 10 insectos/planta.

---

## 🏛️ El precedente operativo europeo hace lo mismo que este motor

**De Vroey, M.; de Vendictis, L.; Zavagli, M.; Bontemps, S.; Heymans, D.; Radoux, J.; Koetz, B.;
Defourny, P. (2022).** *RSE* 280:113145. DOI 10.1016/j.rse.2022.113145. **Sen4CAP**, el sistema de la
Comisión Europea para control de la PAC.

Arquitectura: compara cada observación contra **la última observación libre de nube**, umbral absoluto,
**sin suavizado, sin relleno, sin ajuste de curva**. En S1: CFAR sobre el residuo de un ajuste lineal a las
6 fechas previas, con **PFA = 3,0 × 10⁻⁷ declarada**. Muestreo "no-touch" (solo píxeles enteramente
interiores al polígono). Corrección atmosférica MAJA, elegida explícitamente sobre Sen2Cor.

**Es, estructuralmente, este motor.** Y trae dos números que cambian decisiones:

| Configuración | Precisión |
|---|---|
| **S2 solo** | **59%** |
| S1 solo | 45% |
| S2 + S1 combinado | **44%** |

Y **54% de los falsos positivos vinieron de S1 solo**.

> **El óptico solo es MÁS PRECISO que la combinación con radar. Confirma no agregar S1 al gatillo** —
> y refuerza que la decisión de no conectar el radar a `solo_focos` fue correcta por una segunda razón
> independiente de la cohorte.

**El patrón adoptable — Δt_max = 60 días:** cuando la brecha entre observaciones limpias excede el tope,
Sen4CAP **degrada la salida a un intervalo de fechas en lugar de una fecha**. Cambia la resolución del
producto en vez de inventar el dato. Es la formalización operativa de "no pude mirar" ≠ "no hay nada".
**Los huecos acá llegan a 66 días.**

---

## 📉 Dos límites que hay que decirle al cliente ANTES de vender

Los dos están medidos y son del mismo tipo: **cuando el problema es grande, el método deja de verlo.**

**1. La referencia interna del propio lote desaparece si todo el lote está afectado.**
Holland, K.H. & Schepers, J.S. (2013), *Precision Agriculture* 14:71-85, DOI 10.1007/s11119-012-9301-6 —
el P95 del propio histograma como referencia virtual tiene un **sesgo medido de 3-5%** contra una franja
N-rich real. Pero si el evento afecta al lote entero, el P95 se mueve con él y **la anomalía desaparece
por construcción**. Un umbral relativo al propio lote **solo detecta heterogeneidad**.

**2. La covariable meteorológica explica menos de la mitad.**
RESTREND (regresar el índice sobre la lluvia y quedarse con el residuo) da **R² 0,38-0,45**
(Chen, H. et al. 2018, *Sensors* 18(11):3676). Y Wessels, K.J. et al. (2012), *RSE* 125:10-22,
DOI 10.1016/j.rse.2012.06.022: **una intensidad de degradación ≥20% rompe la relación índice-lluvia**.

→ Quien prometa que ERA5 o CHIRPS "remueven el efecto común" promete algo que la literatura no sostiene.
Sirven para responder *"¿llovió sobre todos?"*, **nunca** *"¿dónde?"* — ERA5-Land es ~9 km, CHIRPS ~5 km.

**Y el que invalida cualquier α declarado a priori:**
Jensen, W.A.; Jones-Farmer, L.A.; Champ, C.W.; Woodall, W.H. (2006), *J. Quality Technology* 38(4),
DOI 10.1080/00224065.2006.11918623 — cuando los límites de control se estiman con pocas muestras de Fase I,
**el ARL0 real colapsa muy por debajo del nominal**. Con 2-4 lotes, **cualquier alfa declarado a priori es
ficción**. Refuerza la regla ya escrita acá de calibrar por tasa empírica y no por SD(z)=1.

---

## Acciones, por relación valor/esfuerzo

| # | Acción | Esfuerzo | Respaldo |
|---|---|---|---|
| **1** | **MAD → Qn** (Rousseeuw-Croux) en la escala robusta | **Una línea** | Eficiencia gaussiana **37% → 82%**, mismo punto de ruptura 50%, O(n log n). Con factores de muestra finita de Akinshin 2022 |
| **2** | **Theil-Sen o Huber en vez de MCO** en el ajuste de trayectoria | Bajo | Mouret 2022 — la anomalía arrastra la recta y encoge su propio residuo |
| **3** | **Δt_max: degradar a intervalo de fechas** cuando el hueco supera el tope | Bajo | Sen4CAP usa 60 d; acá hay huecos de 66 |
| **4** | **Capa de riesgo epidemiológico** desde ERA5-Land | Medio | Alves/Del Ponte/Moschini; ERA5 verificado en GEE |
| **5** | **Medir entropía dual-pol como 2do eje** con el protocolo de 3 patas | Medio | r = 0,005-0,012 medido sobre lotes propios |
| **6** | **Medir el aporte de Landsat lote por lote** vía STAC antes de adoptarlo | Bajo | Depende del sidelap WRS: Santa Cruz +92%, Paraná +36% sin cerrar huecos |
| **7** | Máscara asimétrica (comisión <10%, omisión ≤20%) para estimar covarianza | Bajo | YES-TECH India |
| **8** | Declarar el techo de 0,63 OA como benchmark de auditoría propia | Nulo | Joshi 2026 |
| — | ~~Rellenar huecos de nube~~ | — | **Descartado por 3 vías**: −12,7 pts de recall; Whittaker elimina el evento; BFAST mejora al quitar datos |
| — | ~~Agregar S1 al gatillo~~ | — | **Descartado**: Sen4CAP mide precisión 59% con S2 solo vs 44% combinado |
| — | ~~Productos SAOCOM de CONAE~~ | — | **Descartado**: no se generan sobre Paraná ni Santa Cruz |

### Si se adopta Landsat, cuál es el costo

**Skakun, S. et al. (2021).** *Remote Sensing* 13(5):872. DOI 10.3390/rs13050872. Variabilidad intra-lote
de rendimiento explicada según resolución: **3 m → 100% · 10 m → 86% · 20 m → 72% · 30 m → 59%.**

Pasar de la grilla nativa de 20 m a 30 m cuesta **13 puntos** de variabilidad explicada y **duplica el área
del foco mínimo 3×3: de 0,36 ha a 0,81 ha**. Y **Landsat OLI no tiene red-edge** — en cada fecha Landsat el
segundo eje del motor (NDRE, lift 18,3×) simplemente no existe. **Canal paralelo con su propia línea base,
que solo pueda confirmar o degradar a "no evaluable", nunca disparar solo.**

### Métodos que valen probar, con validación propia

- **EWMACD / control chart sobre residuos armónicos por píxel** — el control es la propia historia, **sin
  cohorte**. 76,6% de acierto en fecha con verdad simulada, pero omisión 65-70% contra verdad real.
- **JUST / ALLSSA** (Ghaderpour, E. & Vujadinovic, T. 2020, *Remote Sensing* 12(23):4001,
  DOI 10.3390/rs12234001) — **maneja el muestreo irregular con pesos en vez de regularizarlo rellenando**;
  supera a BFAST y *"does not require any interpolation"*. Gratis, CPU.
- **CausalImpact / BSTS** (Brodersen, K.H. et al. 2015, *Annals of Applied Statistics* 9(1):247-274,
  DOI 10.1214/14-aoas788) — construye el contrafáctico con **covariables contemporáneas** cuando no hay
  grupo control. Es la maquinaria correcta para campo chico. ⚠️ **Sin aplicación publicada a anomalía
  intra-lote satelital**: el traslado sería original y hay que validarlo con la nula sintética existente.

---

## Pendientes de verificar a mano

1. **Duan et al. 2024** (ISPRS J 213:33-52) — ¿la trayectoria esperada es del propio lote o poblacional?
   Es CC-BY, se consigue. Decide si el tiempo térmico aplica.
2. **Ribeiro et al. 2024** (*Crop Protection* 177:106557) — **91% exactitud, 85,7% sensibilidad, 93,3%
   especificidad** sobre S2 en campos comerciales, clasificando por umbral económico. Es el precedente
   publicado de la tesis del motor. Conseguí los números pero no el texto (PDF abierto en UMN da 403).
3. **Karthikeyan et al. (2022)**, DOI 10.1007/s12524-022-01523-w — revisión india canónica sobre la brecha
   de escala en smallholder. De pago.
