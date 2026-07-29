# Investigación israelí aplicada a PIX_ALERTA — 2026-07-29

Revisión de la literatura de los grupos israelíes de teledetección agrícola, hecha para
juzgar la metodología de este motor: qué respalda, qué contradice y qué no aplica.

**Regla de la revisión:** cada referencia va con autores, año, revista y DOI verificados
contra al menos dos fuentes. Lo que no se pudo verificar está marcado **NO VERIFICADO**
y no se usa para justificar nada. Se distingue lo **leído** de lo **inferido**.

Grupos cubiertos: Remote Sensing Laboratory de Ben-Gurion University (Karnieli),
Rozenstein Lab del Volcani Center / ARO, y Paz-Kagan / Ben-Dor.

---

## 1. Lo que RESPALDA decisiones ya tomadas

### 1.1 El red-edge como segundo eje — respaldo externo e independiente

El grupo de Rozenstein estima el coeficiente de cultivo Kc de FAO-56 desde índices
espectrales y lo valida contra **ET medida con torre de covarianza de vórtices**. El
índice que mejor lo predice **no es NDVI: son los de red-edge** (MTCI, REP, S2REP), con
Kc R² > 0,91 en algodón sobre dos temporadas.

> Rozenstein, Haymann, Kaplan & Tanny (2019). *Agricultural Water Management* 223:105715.
> doi:10.1016/j.agwat.2019.105715

**Qué cambia:** nada, y eso es lo valioso. La elección de NDRE como segundo eje se había
hecho midiendo sobre tres campañas de caña (`config.EJES`). Ahora tiene respaldo externo
con otra metodología, otro cultivo y otra verdad de campo.

### 1.2 En dosel cerrado la pendiente se anula — respalda trabajar sobre residuos

Karnieli et al. citan (Moran et al. 1994) que la pendiente del espacio
Temperatura–NDVI existe con cobertura **rala** y **deja de ser significativa en dosel
cerrado**.

> Karnieli, Agam, Pinker, Anderson, Imhoff, Gutman, Panov & Goldberg (2010).
> *Journal of Climate* 23(3):618–633. doi:10.1175/2009JCLI2900.1

**Qué cambia:** nada. Es el análogo de la saturación del NDVI y de la compuerta FVC del
motor, y refuerza la decisión de trabajar sobre **residuos** y no sobre el índice crudo.

### 1.3 Serie temporal para zonificar, no una escena

La delimitación de zonas de manejo con campañas repetidas a lo largo de la temporada, con
zonas que **cambian dentro de la campaña**, y con las variables partidas en dos familias
declaradas: **constantes** (elevación, pendiente, orientación) y **no constantes** (N de
canopia, altura).

> Termin, Linker, Baram, Raveh, Ohana-Levi & Paz-Kagan (2023).
> *Precision Agriculture* 24(4):1570–1592. doi:10.1007/s11119-023-10008-w

**Qué cambia:** nada estructural — es exactamente la metodología de dos capas ya
aprobada (estratos/terreno = constante; residuo temporal = no constante). Lo que aporta
es el criterio de aceptación: **continuidad espacial y mínima fragmentación**, que es lo
que el motor ya hace con el filtro de mayoría y la unidad mínima de mapeo.

### 1.4 Validar contra mapa de rendimiento, y con qué esperar

Predicción de rendimiento **intra-lote** en trigo asimilando S2 + PlanetScope en un
modelo de cultivo, validada contra el **mapa de rendimiento de la cosechadora**:
**R² = 0,45**, que los propios autores declaran moderado.

> Manivasagam, Sadeh, Kaplan, Bonfil & Rozenstein (2021).
> *Remote Sensing* 13(12):2395. doi:10.3390/rs13122395

**Qué cambia:** fija la expectativa. Si una validación de este motor contra rendimiento
diera R² mucho más alto que 0,45, hay que sospechar del procedimiento antes de festejar.

---

### 1.5 Dos ejes: hay respaldo publicado, pero el par ortogonal no es el que se supone

El resultado más concreto de toda la revisión. Sobre papa, dos campañas, con nitrógeno
medido por Kjeldahl, se mide la matriz de correlación entre índices:

| grupo | correlación **dentro** del grupo |
|---|---|
| índices VNIR (TCARI, MCARI, TCARI/OSAVI, CCCI, NDNI) | \|r\| = 0,58 – 0,92 |
| índices basados en SWIR 1510 nm | \|r\| = 0,87 – 0,99 |
| **entre los dos grupos** | **\|r\| = 0,00 – 0,22** |

Casos extremos: TCARI contra TCARI₁₅₁₀ dio r = 0,01; MCARI contra MCARI₁₅₁₀, r = 0,04.

> Herrmann, Karnieli, Bonfil, Cohen & Alchanatis (2010).
> *International Journal of Remote Sensing* 31(19):5127–5143.
> doi:10.1080/01431160903283892

**Qué respalda:** es el mejor argumento publicado a favor de una arquitectura de **dos
ejes VNIR × SWIR**, que es exactamente la de este motor (NDRE red-edge × NDMI con B11).
La dimensión independiente existe y está medida.

**Qué advierte, y es lo importante:** el eje ortogonal que ellos midieron está en
**1510 nm**, y **Sentinel-2 no tiene esa banda** — B11 está en ~1610 nm con ~90 nm de
ancho. Su R² = 0,59 para nitrógeno **no transfiere a NDMI**.

**Y una consecuencia que sí se puede medir acá:** NDMI = (B8A−B11)/(B8A+B11) y
NDRE = (B8A−B5)/(B8A+B5) **comparten B8A**. Compartir una banda induce correlación que
no es física, es de construcción. Eso encaja con una medición propia que estaba sin
explicar: CIre —que usa B7/B5 y **no** toca B8A— resultó el **menos correlacionado con
NDMI (0,72 contra 0,82)**, y en su momento se eligió NDRE «por robustez, no por la
medición». Ahora hay un mecanismo que explica ese 0,72 contra 0,82.

**Pendiente concreto:** medir la correlación de los residuos para NDMI+NDRE contra
NDMI+CIre sobre los lotes reales. Si CIre da una correlación materialmente menor, el
segundo eje aporta más evidencia independiente por una razón entendida.

### 1.6 Esperar que NDRE se comporte como biomasa — y no es un defecto

En el mismo cuerpo de trabajo, la región del red-edge resulta la más importante **como
mejor medidor de LAI**: no es un eje independiente de la biomasa, es un medidor de
biomasa que se satura más tarde. REIP contra LAI en trigo dio r = 0,91, contra 0,78 del
NDVI lineal y 0,86 del NDVI exponencial.

> Herrmann, Pimstein, Karnieli, Cohen, Alchanatis & Bonfil (2011).
> *Remote Sensing of Environment* 115(8):2141–2151. doi:10.1016/j.rse.2011.04.018

**Qué cambia:** la correlación medida de +0,94 entre los residuos de NDMI y NDRE en el
lote que alertó **es compatible con la literatura y no es un error del motor**. Pero
tiene una consecuencia que hay que declarar: con ρ ≈ 0,94 entre los dos ejes, la
Mahalanobis de dos ejes es **efectivamente de uno**. El tope `RHO_TOPE = 0,95` existe
justamente para que la matriz no se vuelva singular.

Y un matiz que rompe el relato fácil: al mezclar los dos cultivos, un **NDVI
logarítmico** (r = 0,87–0,88) le ganó al REIP (0,75–0,78). La ventaja del red-edge **no
es universal**.

### 1.7 El NDVI se muere por encima de LAI 2 — como compuerta sirve, como número no

Medido: la sensibilidad del NDVI al LAI cae por encima de **LAI = 2**. Y en 21 de 21
casos el ajuste exponencial NDVI→LAI exigía NDVI > 1 dentro del rango medido, o sea que
matemáticamente el NDVI no puede predecir LAI altos.

> Herrmann et al. (2011), citado arriba.

**Qué cambia:** el motor usa NDVI en dos lugares y las consecuencias son distintas.
Como **compuerta FVC binaria** («¿este píxel alguna vez fue cultivo?») sigue siendo
válido. Pero `criterio.zonas` **regresa cada índice contra NDVI espacialmente** para
sacar el «porte esperado»: en dosel cerrado, con el NDVI saturado, esa regresión corre
contra una variable sin gradiente. **Es una posible explicación —medible— de por qué la
capa de zonas está muda.** Queda como pendiente medible, no como conclusión.

### 1.8 Recalibrar por campaña no es opcional

Mismo índice, mismo cultivo, mismo sitio, dos campañas: NDVI lineal contra LAI dio
r = **0,16 (no significativo)** en una campaña y **0,70** en la otra. En papa el REIP
pasó de 0,85 a 0,53. Y en otro trabajo, con el mismo campo y el mismo cultivar, los
modelos en estadio vegetativo resultaron **distintos para cada campaña**; sólo en llenado
hubo una relación única.

> Herrmann et al. (2011) y Cohen, Alchanatis, Zusman, Dar, Bonfil, Karnieli et al.
> (2010). *Precision Agriculture* 11:520–537. doi:10.1007/s11119-009-9147-8

**Qué respalda:** directamente la decisión de calibrar por **tasa empírica** y de usar
referencias relativas a la cohorte en vez de umbrales absolutos.

## 2. Lo que ADVIERTE, y hay que incorporar como disciplina

### 2.1 Nunca asumir el signo de una relación — medirlo por fecha

El resultado más fuerte de la revisión. Sobre un transecto de Norteamérica y 21 años, el
signo de la correlación LST–NDVI **se invierte según la época**: al inicio de temporada
resultó positiva en el 60% del dominio y negativa en sólo el 15%; en media temporada,
negativa en el 57% (y en cultivos, negativa en el 80%). El factor dominante cambia de
estación: radiación al principio y al final, temperatura del aire en pleno verano. Los
autores concluyen que hay que **restringir** el uso a las áreas y períodos donde la
correlación negativa se **observe**.

> Karnieli et al. (2010), citado arriba.

**Qué cambia acá:** el `SIGNO` del motor está cableado por eje
(`ranking.SIGNO`), con una guarda que revienta al importar si un eje no declara su
sentido. Eso protege contra el olvido, no contra la inversión. Dos atenuantes medidos:

- el signo se aplica al **residuo contra la trayectoria del propio píxel**, no al índice
  crudo, así que la caída natural por fenología no lo activa;
- se midió que los residuos de NDMI y NDRE correlacionan **+0,94** en el lote que alertó,
  o sea que los dos ejes se mueven juntos y la puerta de dirección no se contradice.

**Pendiente declarado:** no está medido si esa correlación entre residuos se mantiene
positiva en TODOS los estadios. Es una medición acotada y vale hacerla.

### 2.2 Los índices de validación de agrupamiento siempre encuentran un óptimo

Calinski-Harabasz, ancho de silueta, FPI y NCE son índices de **cohesión de particiones**:
devuelven un óptimo incluso sobre ruido. No sustituyen la calibración por tasa empírica.

**Qué cambia:** nada, y confirma la decisión ya registrada de no usar cuantiles ni
índices de partición como criterio de zonas.

### 2.3 El número de zonas es artefacto de escala tanto como señal

Con Landsat 8 a 30 m salían 9 grupos, y con PlanetScope a 3,7 m sólo 3, sobre los mismos
cultivos. Y se declara 3–4 clases como compromiso operativo.

> Kaya, Ferhatoglu & Başayığıt (2025). *AgriEngineering* 7(4):92.
> doi:10.3390/agriengineering7040092
> — ⚠️ **NO es de los grupos israelíes.** Se cita sólo por este número.

**Qué cambia:** nada hoy (la capa de zonas está muda por diseño y el umbral no se bajó),
pero es un argumento medido a favor de no aumentar el número de zonas.

---

## 3. Lo que NO APLICA, y por qué — para no perseguirlo

### 3.1 El térmico y el CWSI no sirven a esta escala con datos gratuitos

Es la conclusión más útil de la revisión, porque **cierra un camino** que parecía
prometedor:

- Afinando Sentinel-3 térmico de 1000 m a 60 m con Sentinel-2, el error medio absoluto
  queda del orden de **1 °C**, y **crece** cuanto más fino se quiere el resultado. El
  piso que el propio grupo reivindica es **60 m**, no 20 m, y sólo con afinado.
  > Huryna, Cohen, Karnieli, Panov, Kustas & Agam (2019).
  > *Remote Sensing* 11(19):2304. doi:10.3390/rs11192304
- A escala de lote se midieron errores de temperatura de **0,25 a 3,11 °C**.
  > Lacerda, Cohen, Snider et al. (2021). *Remote Sensing* 13(6):1155.
  > doi:10.3390/rs13061155 — ⚠️ no es del grupo de Karnieli; el nexo es Yafit Cohen.
- Un CWSI necesita distinguir de décimas a pocos grados entre dosel estresado y de
  referencia: **el error del dato es del tamaño de la señal**. No es un problema de
  código, es de física del sensor.
- Y el **CWSI analítico está descalificado por el propio grupo**: no siguió la dinámica
  ni diurna ni de estrés/recuperación. Sólo funcionó el **empírico**, que exige líneas
  base medidas en el sitio — instrumentación de campo o dron térmico.
  > Agam, Cohen, Berni, Alchanatis, Kool, Dag, Yermiyahu & Ben-Gal (2013).
  > *Agricultural Water Management* 118:79–86. doi:10.1016/j.agwat.2012.12.004

**Conclusión operativa:** no perseguir térmico satelital gratuito para detección de focos
intra-lote. Un lote de 18 ha es ~0,18 km²: menos del 20% de un píxel de Sentinel-3.

### 3.2 El espacio Temperatura–NDVI / TVDI no es transferible a escala de lote

El trabajo canónico está medido a **8 km** con compuestos de 21 años. El triángulo
necesita **todo el gradiente de cobertura y humedad dentro de la escena** para definir
los bordes seco y húmedo. Dentro de un lote de trigo homogéneo ese gradiente no existe:
el triángulo se degenera y los bordes los define el ruido. **Sería exactamente la cuota
disfrazada de detección que este motor ya midió y rechazó en otra capa.**

### 3.3 El pipeline Kc → ET completo no es aplicable acá

Requiere **torre de covarianza de vórtices** para calibrar, y **riego** para que la
lámina en milímetros sea una decisión ejecutable. Los lotes de este motor son de secano o
de riego no controlado, y no hay torre de flujo.

Y hay una diferencia de fondo que conviene tener clara: ese grupo elige **calibración
absoluta** (Kc contra ET medida) y no referencia relativa, **porque su salida es una
lámina de riego en milímetros**. Un residuo relativo no se convierte en milímetros. No es
una contradicción con este motor: es que resuelven otro problema. Si la decisión es
«cuánto riego», absoluto; si es «a qué lote camino hoy», relativo.

### 3.4 VENµS no es una opción

Es una misión de cobertura por sitios seleccionados, centrada en Israel. Su papel en los
trabajos de fusión es irremplazable y **no tiene sustituto libre en Bolivia ni Brasil**.

### 3.5 La vía de espectroscopía de suelo para separar suelo de cultivo

Índice espectral de calidad de suelo con R² 0,84 (Israel) y 0,78 (Alemania), pero con
**hiperespectral aeroportado y suelo desnudo**.

> Paz-Kagan, Zaady, Salbach, Schmidt, Lausch, Zacharias, Notesco, Ben-Dor & Karnieli
> (2015). *Remote Sensing* 7(11):15748–15781. doi:10.3390/rs71115748

Con Sentinel-2 multiespectral y dosel cerrado no es reproducible. **Esos R² no se pueden
invocar como respaldo de una capa de suelo derivada de S2.**

---

## 4. Oportunidad concreta, documentada y NO implementada

**Radar: normalizar por el ángulo de incidencia local para ganar fechas.**

Normalizar la retrodispersión por el ángulo de incidencia local mejora R² entre +0,017 y
+0,668 y el RMSE entre 5% y 52%, en trigo, tomate y algodón — y **le gana al RVI**, el
índice de vegetación radar de doble polarización.

> Kaplan, Fine, Lukyanov, Manivasagam, Tanny & Rozenstein (2021).
> *Land* 10(7):680. doi:10.3390/land10070680

Y el aporte del radar es de **cadencia, no de exactitud**: Sentinel-1 solo resultó peor
que Sentinel-2 solo (Kc R² 0,79 contra 0,88; LAI 0,67 contra 0,97).

> Kaplan, Fine, Lukyanov, Malachy, Tanny & Rozenstein (2023).
> *Agricultural Water Management*, doi:10.1016/j.agwat.2022.108056

**Estado en este motor:** `pix_alerta/radar.py` usa **RVI** y resuelve el problema de la
geometría de vista por otro camino — elige **una sola órbita relativa** y lo declara,
justamente porque mezclar órbitas cambia la retrodispersión por el ángulo y no por el
cultivo. Con una sola órbita y un lote chico, el ángulo es casi constante y normalizar
compra poco.

**Dónde estaría el valor:** normalizar por ángulo permitiría **usar varias órbitas** y
por lo tanto más fechas, que es el cuello de botella medido (S1 da 9 pasadas en 4 meses
con una órbita). No se implementó porque (a) el radar no corre en el camino de campo
chico, que es el producto de este cliente, y (b) exigiría su propia validación.

---

## 5. Lo que NADIE publicó, y conviene no afirmar

- **No existe un número de "días de anticipación" del térmico sobre el óptico.** La
  afirmación aparece como introducción cualitativa en la literatura térmica, sin
  cuantificar, y no se pudo atribuir a ningún trabajo con número. Si aparece en material
  comercial, no tiene respaldo citable.
- **Ninguno de los trabajos revisados reporta tasa de falsa alarma ni control de error
  espacial** para detección de anomalías. Sus métricas son R² y RMSE contra verdad de
  campo. **No se puede citar este cuerpo de trabajo como aval del criterio de focos** —
  no aborda ese problema.
- **«NDRE detecta 1–2 semanas antes que el NDVI» NO tiene respaldo.** Apareció en un
  blog comercial sin cita primaria. No usar.
- **No hay evidencia de que el red-edge preceda a los índices de humedad.** En el único
  trabajo pre-sintomático leído, las bandas de agua (~970, 1380 y 1890 nm) estaban entre
  las más importantes en la fase latente, o sea **simultáneas** con el red-edge, no
  después. Si el motor asumiera ese orden, sería una hipótesis sin respaldo — no lo
  asume: exige que los dos ejes se muevan juntos.
- **La detección pre-sintomática publicada es de 2 a 4 días, con más del 80% de
  exactitud, pero a nivel de HOJA, con espectrómetro de contacto de rango completo y bajo
  inoculación controlada.** No es la exactitud esperable de un foco satelital a 20 m.
  > Gold, Townsend, Chlus, Herrmann, Couture, Larson & Gevens (2020).
  > *Remote Sensing* 12(2):286. doi:10.3390/rs12020286
  **Es el hallazgo que más protege el discurso comercial: no prometer detección
  pre-sintomática.**
- **No se encontró un tamaño mínimo de zona en hectáreas** atribuible a estos autores. Si
  el informe al cliente necesita un mínimo, sale de la medición propia.
- **No se encontró prueba de estabilidad interanual de zonas** con cifras verificables.

---

### 3.6 El ancho de banda de Sentinel-2 no es el cuello de botella

Comparando índices calculados con espectro continuo contra los mismos índices calculados
con las bandas de Sentinel-2 remuestreadas: **r > 0,99**. Y el modelo PLS de LAI dio
0,93 con espectro continuo contra 0,92 con bandas S2.

> Herrmann et al. (2011), citado arriba.

**Qué significa:** si este motor falla, no es por el ancho de las bandas. Lo que degrada
es todo lo demás — atmósfera, píxel mixto, BRDF, nube fina — y eso es donde vale invertir.

⚠️ Con una advertencia: el «Sentinel-2» de ese trabajo es **espectro de campo
remuestreado, no imagen satelital**. No hay validación con S2 real ahí.

## 6. Saldo

La revisión **no cambió el diseño del motor**. Confirmó tres decisiones (red-edge como
segundo eje, trabajar sobre residuos, serie temporal para zonificar), cerró un camino que
parecía prometedor (térmico y CWSI a esta escala con datos gratuitos), fijó una
expectativa cuantitativa para la validación contra rendimiento (R² ~0,45 intra-lote), y
dejó una oportunidad acotada en radar que no se implementó y se declara como pendiente.

La advertencia metodológica más valiosa —no asumir el signo de una relación, medirlo por
fecha y restringir el dominio de validez— es la misma disciplina que este motor ya viene
aplicando, y deja un pendiente concreto: verificar que la correlación entre los residuos
de los dos ejes se mantenga positiva en todos los estadios, no sólo en el que se midió.
