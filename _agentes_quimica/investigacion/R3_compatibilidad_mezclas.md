# R3 — COMPATIBILIDAD DE MEZCLAS LÍQUIDAS
## Fertilizante × fertilizante y fertilizante × agroquímico

**Dossier de investigación verificado**
Fecha: 2026-08-16
Ámbito: soluciones madre de fertirriego, caldos foliares y mezclas en tanque de pulverización.

---

## 0. CÓMO LEER ESTE DOCUMENTO

### 0.1 Clasificación de evidencia

Cada afirmación de este dossier lleva una etiqueta. La distinción es obligatoria porque en compatibilidad de caldos conviven tres cosas muy distintas que la literatura comercial mezcla sin avisar:

| Etiqueta | Significado |
|---|---|
| **[MED]** | **MEDIDO / PUBLICADO.** Dato experimental o constante termodinámica tabulada, con fuente recuperable. |
| **[CALC]** | **CÁLCULO PROPIO** hecho en este dossier a partir de constantes **[MED]**. Los supuestos están declarados y el cálculo es reproducible. No es un dato experimental. |
| **[PRAC]** | **PRÁCTICA RECOMENDADA** por una institución o fabricante, **sin ensayo publicado** que la respalde en la fuente consultada. Es criterio profesional, no evidencia. |
| **[NV]** | **NO VERIFICADO.** Se conoce la afirmación pero no se pudo recuperar la fuente primaria en esta sesión. Va en la tabla del §10. |

> **Regla del dossier:** una etiqueta **[PRAC]** nunca se presenta como si fuera **[MED]**. Buena parte del corpus de "orden de mezcla" del mundo es **[PRAC]** — es criterio acumulado de la industria, funciona, y no está publicado como ensayo. Decirlo no lo debilita; ocultarlo sí.

### 0.2 Limitación de sesión declarada

- Las búsquedas web se agotaron (200/200) y varias descargas fallaron por red (`ECONNRESET`) o por política de dominio. Los ítems que quedaron sin fuente primaria recuperada están en **§10 (NO VERIFICADO)** y **no** se usan para sostener ninguna conclusión operativa.
- Tres PDF institucionales (Embrapa Documentos 437, UADA FSA-2166, UGA Tank Mixing) se descargaron pero **no se pudo extraer su texto** en este entorno. Lo que se cita de ellos proviene de resúmenes secundarios y está marcado como tal.

---

## 1. EL FUNDAMENTO: POR QUÉ PRECIPITA UNA MEZCLA

Todo este dossier se apoya en una sola desigualdad. Vale la pena escribirla antes que nada, porque explica el 90 % de los fracasos de tanque y hace innecesario memorizar matrices.

Para una sal poco soluble AₘBₙ:

$$\text{PI} = [A]^m[B]^n \qquad\text{vs.}\qquad K_{sp}$$

$$\text{SI} = \log_{10}\!\left(\frac{\text{PI}}{K_{sp}}\right)$$

- **SI < 0** → subsaturado. No precipita. La sal se disuelve.
- **SI = 0** → equilibrio.
- **SI > 0** → **sobresaturado. Precipita** (con la reserva cinética del §1.3).

### 1.1 La consecuencia que decide toda la operación

El producto iónico **escala con la potencia (m+n) del factor de concentración**. Para un par 2:2 como Ca²⁺/SO₄²⁻ eso significa que **concentrar 100× multiplica el PI por 10 000×** y desplaza el SI en **+4 unidades**.

> **Esta es la razón cuantitativa —no cualitativa— de los tanques A/B.** El mismo par de fertilizantes que es perfectamente estable en el caldo diluido de campo está 10 000 veces más sobresaturado en la solución madre. La incompatibilidad **no es una propiedad del par de productos: es una propiedad del par de productos a una concentración dada.** Cualquier "matriz de compatibilidad" que no declare la concentración a la que aplica es inutilizable. **[CALC]**

### 1.2 Tabla maestra de constantes de solubilidad (25 °C)

Se presentan **dos compilaciones independientes** deliberadamente. La divergencia entre ellas es un dato, no un defecto: para los hidróxidos el Ksp depende de **qué fase sólida** se considera (amorfa recién precipitada vs. cristalina envejecida), y esa elección mueve el valor uno o dos órdenes de magnitud.

| Sólido | Fórmula | pKsp — Fuente A | Ksp — Fuente A | Ksp — Fuente B | Coincidencia |
|---|---|---|---|---|---|
| Yeso | CaSO₄·2H₂O | 4,58 | 2,63 × 10⁻⁵ | 2 × 10⁻⁵ (CaSO₄) | Excelente |
| Anhidrita | CaSO₄ | 4,36 | 4,37 × 10⁻⁵ | — | — |
| Calcita | CaCO₃ | 8,48 | 3,31 × 10⁻⁹ | 8,7 × 10⁻⁹ | Factor 2,6 |
| Brushita (DCPD) | CaHPO₄·2H₂O | 6,61 | 2,45 × 10⁻⁷ | no listado | — |
| Fosfato tricálcico | Ca₃(PO₄)₂ | — | — | 1 × 10⁻²⁵ | — |
| Hidroxiapatita | Ca₅(PO₄)₃OH | 54,45 | 3,55 × 10⁻⁵⁵ | — | — |
| **Estruvita** | **MgNH₄PO₄·6H₂O** | **13,17** | **6,76 × 10⁻¹⁴** | — | ver §1.2.1 |
| Fosfato de magnesio | Mg₃(PO₄)₂ | — | — | 4 × 10⁻²⁵ | — |
| Fe(OH)₃ amorfo | Fe(OH)₃ | 37,08 | 8,32 × 10⁻³⁸ | 6 × 10⁻³⁸ | Excelente |
| Fe(OH)₂ | Fe(OH)₂ | 14,08 | 8,32 × 10⁻¹⁵ | 2 × 10⁻¹⁵ | Factor 4 |
| Mn(OH)₂ | Mn(OH)₂ | 12,78 | 1,66 × 10⁻¹³ | 2 × 10⁻¹³ | Excelente |
| Zn(OH)₂ | Zn(OH)₂ | 15,78 | 1,66 × 10⁻¹⁶ | 5 × 10⁻¹⁷ | Factor 3 |
| Cu(OH)₂ | Cu(OH)₂ | 19,34 | 4,57 × 10⁻²⁰ | 2 × 10⁻¹⁹ | Factor 4 |
| Mg(OH)₂ | Mg(OH)₂ | — | — | 1,8 × 10⁻¹¹ | — |
| Al(OH)₃ amorfo | Al(OH)₃ | 31,17 | 6,76 × 10⁻³² | — | — |
| Gibbsita | Al(OH)₃ | 33,86 | 1,38 × 10⁻³⁴ | — | — |

**Fuente A** [MED]: recopilación aqion a partir de las bases termodinámicas de PHREEQC — **WATEQ4F** (yeso, anhidrita, calcita, hidroxiapatita, Fe(OH)₃ am., Mn(OH)₂, Zn(OH)₂, Cu(OH)₂, Al(OH)₃), **MINTEQ** (brushita) y **LLNL** (Fe(OH)₂). Temperatura: **25 °C**. — https://www.aqion.de/site/16

**Fuente B** [MED]: tabla derivada de **Lange's Handbook of Chemistry**, pp. 8-6 a 8-11, y de **Sillén, L.G. & Martell, A.E. (1964)**, *Stability Constants of Metal-Ion Complexes*, The Chemical Society, London, Special Publication No. 17. Temperatura: **25 °C**. — https://www.wiredchemist.com/chemistry/data/solubility-product-constants

#### ⚠ Declaración obligatoria sobre fuerza iónica

El pedido exigía "cada Ksp con temperatura y fuerza iónica". **La temperatura sí está declarada (25 °C en ambas fuentes). La fuerza iónica NO está declarada en ninguna de las dos compilaciones accesibles.** Esto es en sí mismo un hallazgo y debe decirse:

- Las bases de la familia PHREEQC (WATEQ4F, MINTEQ, LLNL) tabulan **log K a dilución infinita (I = 0)** por convención del formato, y aplican el modelo de actividad en tiempo de cálculo. **La página consultada no lo declara explícitamente** — es inferencia por convención de la base, no una cita. **[NV parcial]**
- Sillén & Martell publican **tanto** constantes termodinámicas (I = 0) **como** constantes condicionales en medio iónico declarado. **La tabla secundaria consultada no indica cuál de las dos usó.** **[NV parcial]**

**Consecuencia práctica:** todos los cálculos del §1.4 en adelante se hacen con **γ = 1 (I = 0)**, y por lo tanto **erran del lado conservador** — ver §1.5 para la magnitud y el signo del error.

#### 1.2.1 Estruvita — el caso con mejor documentación de fuerza iónica

La estruvita es la única sal de esta tabla para la que sí se recuperó una determinación con **tratamiento explícito de fuerza iónica**:

- **pKsp = 13,36 ± 0,07 a 25 °C** [MED] — Bhuiyan et al., *"Exploring the determination of struvite solubility product from analytical results"*, PubMed PMID **17067121**. https://pubmed.ncbi.nlm.nih.gov/17067121/
- Serie térmica **10–60 °C**: pKsp varía de **14,36 ± 0,05** a **14,01 ± 0,03**, con **mínimo de 13,17 ± 0,05 a 30 °C** [MED]. Los productos de solubilidad termodinámicos se determinaron **variando la fuerza iónica de la solución y extrapolando a fuerza iónica cero**, con un modelo de coeficiente de actividad apropiado. — *Chemical Engineering Journal*, "Temperature impact assessment on struvite solubility product: a thermodynamic modeling approach". https://www.sciencedirect.com/science/article/abs/pii/S1385894710012027
- **Dispersión de la literatura: Ksp reportado entre 4,37 × 10⁻¹⁴ y 3,89 × 10⁻¹⁰** [MED] — casi **4 órdenes de magnitud**. Las causas declaradas: equilibrios aproximados, **fuerza iónica frecuentemente ignorada**, y balances de masa y electroneutralidad no siempre aplicados.

> **Lección transferible:** si la constante mejor estudiada de la lista tiene 4 órdenes de dispersión por no declarar fuerza iónica, **cualquier umbral absoluto de compatibilidad copiado de una tabla sin su contexto es sospechoso.** Use el Ksp para entender el mecanismo y ordenar los riesgos; use la prueba de jarra (§5) para decidir.

### 1.3 Por qué el Ksp no alcanza: las tres reservas

1. **Cinética.** El SI dice si *puede* precipitar, no *cuándo*. La hidroxiapatita (pKsp 54,45) está termodinámicamente sobresaturada en casi cualquier caldo con Ca y P, pero **no nuclea rápido**. Quien precipita en minutos, en el rango ácido-neutro, es la **brushita (DCPD)**. Confirmado: *"HAP is the least soluble and is preferentially formed under neutral or basic conditions, while DCPD (brushite) and OCP are often found in more acidic solutions"* **[MED]** — https://pmc.ncbi.nlm.nih.gov/articles/PMC5178315/
   → **Por eso el §2.2 se calcula contra brushita y no contra hidroxiapatita.**
2. **Pares iónicos.** El Ksp puro **subestima** la solubilidad aparente. En el sistema CaSO₄ una fracción importante del Ca y del SO₄ disueltos viaja como par neutro **CaSO₄°(aq)**, que no cuenta en el producto iónico pero sí en el análisis químico.
3. **Complejación competitiva.** Fosfato, carbonato, quelatos sintéticos y polifosfatos (§6) secuestran el catión y bajan su actividad libre. El Ksp no lo ve.

### 1.4 Supuestos declarados de todos los cálculos [CALC]

| Supuesto | Valor |
|---|---|
| Temperatura | 25 °C |
| Coeficientes de actividad | γ = 1 (solución ideal, I = 0) |
| Complejos hidroxo, pares iónicos, quelatos | **no considerados** |
| pKa₂ del ácido fosfórico (H₂PO₄⁻/HPO₄²⁻) | 7,20 |
| pKa₃ del ácido fosfórico (HPO₄²⁻/PO₄³⁻) | 12,35 |
| pKa del NH₄⁺/NH₃ | 9,25 |
| Masas molares | Ca 40,08 · Mg 24,305 · SO₄ 96,06 · P 30,97 · N 14,007 · Fe 55,85 · Mn 54,94 · Zn 65,38 · Cu 63,55 |

### 1.5 Magnitud y signo del error por ignorar la fuerza iónica [CALC]

Estimación con la **ecuación de Davies** (A = 0,509 a 25 °C) a una fuerza iónica realista de caldo, **I = 0,05 M**:

$$\log \gamma = -A z^2\left(\frac{\sqrt{I}}{1+\sqrt{I}} - 0{,}3\,I\right)$$

| Carga | γ a I = 0,05 M |
|---|---|
| ±1 | 0,822 |
| ±2 | 0,455 |
| ±3 | 0,170 |

**Corrección resultante sobre el umbral de precipitación:**

| Sistema | Factor γ combinado | Concentración umbral real vs. calculada | Corrección de pH |
|---|---|---|---|
| CaSO₄ (2:2) | 0,207 | **2,2× más alta** | — |
| M(OH)₂ | 0,302 | 3,3× más alta | **pH + 0,26** |
| Fe(OH)₃ | 0,0882 | 11,3× más alta | **pH + 0,35** |

> **Dirección del error: los umbrales calculados en este dossier son CONSERVADORES.** En una solución real, la precipitación arranca a concentraciones ~2–11× más altas y a un pH ~0,3 unidades más alto de lo que dicen las tablas §2 y §3. Se avisa antes de tiempo, nunca tarde. Para diseño operativo esto es lo correcto; para litigar un caso concreto, no alcanza — hay que medir.

---

## 2. MATRIZ DE COMPATIBILIDAD FERTILIZANTE × FERTILIZANTE

### 2.1 Ca²⁺ + SO₄²⁻ → YESO. El caso testigo.

**Mecanismo** [MED]: *"Mixing a fertilizer containing calcium with a fertilizer containing sulfate can cause gypsum to precipitate. While both fertilizers are highly water soluble, mixing them together into irrigation water will cause calcium sulfate (gypsum) to form."* El resultado es un **precipitado blanco espeso que tapa filtros, válvulas y emisores de goteo**. Par típico: **nitrato de calcio + sulfato de potasio**. — Haifa Group, https://www.haifa-group.com/haifa-blog/mastering-tank-mixes · Cropaia, https://cropaia.com/blog/fertilizer-compatibility-chart-guide/ · Purdue Vegetable Crops Hotline, https://vegcropshotline.org/article/fertilizer-compatibility/

**Cuantificación** [CALC] — Ksp(yeso) = 2,63 × 10⁻⁵:

Saturación en agua pura, solo por Ksp (sin par iónico):
- [Ca²⁺] = [SO₄²⁻] = √(2,63 × 10⁻⁵) = **5,13 × 10⁻³ M**
- = **206 mg/L de Ca** · **493 mg/L de SO₄** · ≈ **0,88 g/L expresado como yeso**

*(La solubilidad medida del yeso es mayor que esto por el par iónico CaSO₄°(aq) — ver §1.3.2 y §10.)*

**Ejemplo trabajado — por qué A/B no es opcional** [CALC]:

Receta de fertirriego con objetivo en gotero de **Ca 150 mg/L** y **S-SO₄ 48 mg/L de S** (= 144 mg/L de SO₄), inyectada al **1:100**.

| | [Ca²⁺] | [SO₄²⁻] | PI | SI | Veredicto |
|---|---|---|---|---|---|
| **Caldo final (en gotero)** | 3,74 × 10⁻³ M | 1,50 × 10⁻³ M | 5,61 × 10⁻⁶ | **−0,67** | Subsaturado. **Estable.** |
| **Solución madre (100×)** | 0,374 M | 0,150 M | 5,61 × 10⁻² | **+3,33** | **2 133× sobresaturado. Precipita.** |

> **El mismo par de fertilizantes: estable en el gotero, catastrófico en el bidón.** La separación A/B no separa productos incompatibles — separa **concentraciones** incompatibles. Es la aplicación directa del escalado cuadrático del §1.1.

### 2.2 Ca²⁺ + HPO₄²⁻ / PO₄³⁻ → FOSFATOS DE CALCIO. El caso que también rompe el caldo diluido.

**Mecanismo** [MED]: *"The most common and problematic reaction occurs between calcium ions and phosphates or sulfates. When these elements are combined in a concentrated solution, they tend to form insoluble compounds such as calcium phosphate or gypsum."* — Haifa Group (misma URL).

**Cuantificación contra brushita** [CALC] — Ksp(CaHPO₄·2H₂O) = 2,45 × 10⁻⁷, fase que efectivamente nuclea en el rango ácido-neutro (§1.3.1).

Caldo final con **Ca 150 mg/L** (3,74 × 10⁻³ M) y **P 30 mg/L** (9,69 × 10⁻⁴ M de P total):

| pH | α(HPO₄²⁻) | [HPO₄²⁻] | PI | **SI** | Veredicto |
|---|---|---|---|---|---|
| 5,5 | 0,0196 | 1,90 × 10⁻⁵ | 7,09 × 10⁻⁸ | **−0,54** | Subsaturado ✓ |
| 6,0 | 0,0594 | 5,75 × 10⁻⁵ | 2,15 × 10⁻⁷ | **−0,06** | Al filo del equilibrio |
| 6,5 | 0,166 | 1,61 × 10⁻⁴ | 6,03 × 10⁻⁷ | **+0,39** | 2,5× sobresaturado ✗ |
| 7,0 | 0,387 | 3,75 × 10⁻⁴ | 1,40 × 10⁻⁶ | **+0,76** | 5,7× sobresaturado ✗ |

> **Resultado operativo de primer orden: el par Ca + P no se arregla solo con diluir.** A concentración de campo ya está sobresaturado por encima de **pH 6,0**. A diferencia del yeso, **necesita además control de pH**. En la solución madre a 100× el SI sube +4 en toda la fila: **no hay pH que lo salve**, por eso Ca y P **nunca** comparten bidón. **[CALC]**

**Regla derivada:** si el caldo lleva calcio y fósforo juntos, **acidificar a pH ≤ 6,0** no es un refinamiento — es la condición de existencia de la mezcla.

### 2.3 Mg²⁺ + fosfato + amonio a pH alto → ESTRUVITA

La estruvita **exige los tres iones simultáneamente**: Mg²⁺, NH₄⁺ y PO₄³⁻. **Sin amonio no hay estruvita** — ésa es la palanca de control.

**Cuantificación** [CALC] — Ksp = 6,76 × 10⁻¹⁴ (pKsp 13,17). Caldo con **Mg 40 mg/L** (1,646 × 10⁻³ M), **N-NH₄ 20 mg/L de N** (1,428 × 10⁻³ M) y **P 30 mg/L** (9,69 × 10⁻⁴ M). Se incluye la especiación del NH₄⁺/NH₃ (pKa 9,25):

| pH | [NH₄⁺] | [PO₄³⁻] | PI | **SI** | Veredicto |
|---|---|---|---|---|---|
| 7,0 | 1,420 × 10⁻³ | 1,675 × 10⁻⁹ | 3,92 × 10⁻¹⁵ | **−1,24** | Subsaturado ✓ |
| 8,0 | 1,352 × 10⁻³ | 3,74 × 10⁻⁸ | 8,31 × 10⁻¹⁴ | **+0,09** | **Umbral. Empieza.** |
| 8,5 | 1,212 × 10⁻³ | 1,303 × 10⁻⁷ | 2,60 × 10⁻¹³ | **+0,59** | Precipita ✗ |
| 9,0 | 9,14 × 10⁻⁴ | 4,26 × 10⁻⁷ | 6,41 × 10⁻¹³ | **+0,98** | Precipita ✗ |

**Lectura:**
- El umbral cae en **pH ≈ 8,0**. Por debajo de 7,5 la estruvita no es un problema, porque la fracción PO₄³⁻ del fosfato total es despreciablemente pequeña (a pH 7 es ~4,5 × 10⁻⁶ del HPO₄²⁻).
- Por encima de pH 9,25 la conversión NH₄⁺ → NH₃ **frena parcialmente** el proceso (el SI a pH 9,0 baja de +1,17 a +0,98 al aplicar la corrección). **Frena, no lo cancela.**
- **Palanca de control:** en un caldo con Mg y P, **usar nitrato en lugar de amonio elimina la estruvita por completo**, sin tocar el pH. **[CALC]**

### 2.4 Sulfato + Ca del agua dura

Este es el caso que la matriz clásica no cubre, porque **el calcio no lo aportó usted: lo aportó el agua**.

Con la solubilidad del yeso calculada en §2.1 (**206 mg/L de Ca en saturación**) y la clasificación de dureza de Purdue **[MED]** — soft 0–114, moderately hard 114–342, hard 342–800, extremely hard > 800 ppm (clasificación OMS) — la conclusión es directa:

> Un agua clasificada como **"hard"** (342–800 ppm CaCO₃, equivalente a ~137–320 mg/L de Ca²⁺) puede estar **ya cerca o por encima de la mitad de la saturación de yeso antes de que usted agregue nada**. Todo el sulfato que cargue después se descuenta de un margen que ya está comprometido. **[CALC]** sobre clasificación **[MED]** de https://ag.purdue.edu/department/extension/ppp/resources/ppp-publications/mobile/ppp-86/the-impact-of-water-quality-on-pesticide-performance.html

**Corolario operativo:** la matriz de compatibilidad **no se puede escribir sin el análisis del agua**. Es la misma mezcla, con distinto veredicto, en dos pozos separados por 5 km.

### 2.5 MATRIZ RESUMEN — fertilizante × fertilizante

Escala de veredictos:
**✓** compatible · **◐** compatible **solo diluido** (nunca en solución madre) · **✗** incompatible siempre · **pH** compatible **solo con control de pH**

| | Nitrato de Ca | Nitrato de K / NH₄ | Sulfato de K | Sulfato de Mg | Fosfato mono-K / MAP | Ácido fosfórico | Micros quelatados | Micros sulfato |
|---|---|---|---|---|---|---|---|---|
| **Nitrato de Ca** | — | ✓ | **✗** yeso | **✗** yeso | **✗** fosfato de Ca | **pH** | ◐ | ◐ |
| **Nitrato de K / NH₄** | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Sulfato de K** | **✗** yeso | ✓ | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Sulfato de Mg** | **✗** yeso | ✓ | ✓ | — | **pH** estruvita si hay NH₄⁺ | ✓ | ✓ | ✓ |
| **Fosfato mono-K / MAP** | **✗** fosfato de Ca | ✓ | ✓ | **pH** estruvita | — | ✓ | **pH** | **pH** fosfatos de micro |
| **Ácido fosfórico** | **pH** | ✓ | ✓ | ✓ | ✓ | — | **pH** | ✓ |
| **Micros quelatados** | ◐ | ✓ | ✓ | ✓ | **pH** | **pH** | — | ✓ |
| **Micros sulfato** | ◐ | ✓ | ✓ | ✓ | **pH** | ✓ | ✓ | — |

**Precipitado formado en cada casilla ✗:**

| Par | Producto | Ksp (25 °C) | pH al que aparece |
|---|---|---|---|
| Ca²⁺ + SO₄²⁻ | **Yeso**, CaSO₄·2H₂O | 2,63 × 10⁻⁵ | **Independiente del pH** — sólo concentración |
| Ca²⁺ + HPO₄²⁻ | **Brushita**, CaHPO₄·2H₂O | 2,45 × 10⁻⁷ | **> 6,0** en caldo diluido; siempre en madre |
| Ca²⁺ + PO₄³⁻ (envejecido) | **Hidroxiapatita**, Ca₅(PO₄)₃OH | 3,55 × 10⁻⁵⁵ | Termodinámico siempre; **cinéticamente lento** |
| Mg²⁺ + NH₄⁺ + PO₄³⁻ | **Estruvita**, MgNH₄PO₄·6H₂O | 6,76 × 10⁻¹⁴ | **> 8,0** |
| Ca²⁺ + CO₃²⁻ (agua alcalina) | **Calcita**, CaCO₃ | 3,31 × 10⁻⁹ | **> 7,5** aprox. |

### 2.6 La regla de tanques A/B — enunciado y justificación

**Enunciado** [MED / PRAC]: *"Calcium-based fertilizers, such as calcium nitrate, are placed in one tank together with nitrates, while phosphates, potassium fertilizers, magnesium, and sulfates are prepared in a separate tank."* — Haifa Group · Cropaia · Rivulis.

| Tanque | Contenido | Ion prohibido enfrente |
|---|---|---|
| **A** | Nitrato de calcio · nitrato de amonio · nitrato de potasio · **quelatos de Fe** | — |
| **B** | Fosfatos (MAP/MKP/H₃PO₄) · **sulfatos** (K₂SO₄, MgSO₄) · **micros sulfato** (Zn, Mn, Cu, B) | Nunca calcio |
| **C** (opcional) | Ácido para control de pH | Nunca en contacto directo con A concentrado |

**Por qué NO es opcional — los tres argumentos, en orden de fuerza:**

1. **Argumento termodinámico [CALC].** SI = **+3,33** para el par Ca/SO₄ en madre a 100× (§2.1) y **SI > +4** para Ca/P. No es un riesgo probabilístico: **es una condición de sobresaturación de tres órdenes de magnitud.** No existe agitación, orden de carga ni adyuvante que revierta un SI de +3,3 — la agitación resuspende, no disuelve.
2. **Argumento de consecuencia física [MED].** El precipitado es *"a thick, white precipitate that will rapidly clog filters, valves and drip emitters"*. En riego por goteo el fallo no es "menor eficacia": es **pérdida del sistema de distribución**, y la limpieza es ácida y cara.
3. **Argumento de asimetría de costo.** La dilución en el punto de inyección **sí** salva la mezcla: *"the solutions are highly diluted, and the concentration of reactive ions is significantly lower"* [MED]. Es decir, **A/B no cuesta nada agronómicamente** — el cultivo recibe exactamente la misma solución. Es una separación **gratuita** que evita un fallo **catastrófico e irreversible**. Ninguna decisión de manejo tiene un perfil riesgo/beneficio tan asimétrico.

> **La versión corta que va al operario:** *"El calcio va solo. Todo lo que tenga sulfato o fosfato va en el otro bidón. Se juntan recién en el agua de riego, nunca antes."*

---

## 3. PRECIPITACIÓN DE MICRONUTRIENTES POR pH

### 3.1 El cálculo

Para un hidróxido M(OH)ₙ, el pH al que **arranca** la precipitación de una concentración dada de metal:

$$[OH^-] = \left(\frac{K_{sp}}{[M^{n+}]}\right)^{1/n} \qquad ; \qquad pH = 14 - pOH$$

Se calcula a **dos concentraciones de referencia** deliberadamente distintas, porque el veredicto cambia:
- **1 mg/L** — orden de magnitud de un micronutriente en **solución de fertirriego**.
- **100 mg/L** — orden de magnitud de un micronutriente en **caldo foliar concentrado**.

### 3.2 Tabla de pH de inicio de precipitación (no quelatado, 25 °C) [CALC]

| Catión | Sólido | pH inicio @ **1 mg/L** (Ksp A / Ksp B) | pH inicio @ **100 mg/L** (Ksp A / Ksp B) | Fragilidad |
|---|---|---|---|---|
| **Fe³⁺** | Fe(OH)₃ am. | **3,22 / 3,18** | **2,56 / 2,51** | 🔴 Extrema |
| **Cu²⁺** | Cu(OH)₂ | **6,73 / 7,05** | **5,73 / 6,05** | 🟠 Alta |
| **Zn²⁺** | Zn(OH)₂ | **8,52 / 8,26** | **7,52 / 7,26** | 🟡 Media |
| **Fe²⁺** | Fe(OH)₂ | **9,33 / 9,02** | **8,33 / 8,02** | 🟢 Baja *(pero ver §3.3)* |
| **Mn²⁺** | Mn(OH)₂ | **9,98 / 10,02** | **8,98 / 9,02** | 🟢 Baja |

**Ordenamiento de fragilidad — el resultado robusto:**

$$\mathbf{Fe^{3+} \lll Cu^{2+} < Zn^{2+} < Fe^{2+} < Mn^{2+}}$$

> **Las dos compilaciones de Ksp coinciden dentro de ±0,3 unidades de pH y dan exactamente el mismo ordenamiento.** El *orden* es un resultado sólido. El *valor absoluto* tiene ±0,3 de incertidumbre **sólo por la elección de tabla**, más +0,26 a +0,35 de corrección por fuerza iónica (§1.5), más la incertidumbre de fase amorfa/cristalina. **Trate estos números como umbrales de diseño con ±0,5 unidades, no como constantes.**

### 3.3 Los tres hallazgos que importan

**(a) El Fe³⁺ no quelatado es químicamente inviable en agricultura.**
Precipita a **pH 2,5–3,2**. No existe caldo agronómico a ese pH (destruiría la hoja y muchas formulaciones). **Conclusión dura: todo hierro que se aplique en solución por encima de pH 3 y que no esté quelatado, ya precipitó** — esté visible o no. El sulfato ferroso en un caldo a pH 6 no es un fertilizante de hierro: es una suspensión de óxido férrico. **[CALC]**

**(b) La trampa del Fe²⁺: es soluble, y por eso engaña.**
El Fe²⁺ aguanta hasta **pH 8,0–9,3** — parece la solución al problema (a). No lo es. En agua **aireada** el Fe²⁺ se oxida a Fe³⁺, y el Fe³⁺ precipita a pH 3 (hallazgo *a*). El caldo se prepara transparente y a la hora tiene lodo ocre en el fondo.
- La velocidad de esa oxidación **crece con el cuadrado de [OH⁻]** (es decir, ~100× por cada unidad de pH) — **[NV]**, ver §10. El mecanismo cualitativo es estándar; la ley de velocidad no se pudo verificar en esta sesión.
- **Operativamente:** el Fe²⁺ no es un depósito estable de hierro en un tanque abierto y agitado. La agitación es exactamente lo que lo oxida.

**(c) El cobre es el que fija la ventana operativa por arriba.**
Con **5,73–6,05** a concentración foliar, el Cu²⁺ no quelatado es el primer micronutriente que se pierde al subir el pH dentro del rango agronómico normal. Es el techo real, no el Zn ni el Mn.

**Límites declarados de este modelo** [CALC]:
- No incluye **complejos hidroxo** (FeOH²⁺, Zn(OH)₃⁻, Cu(OH)₄²⁻), que **aumentan** la solubilidad total por encima de lo calculado.
- No incluye **anfoterismo**: Zn y Cu se **redisuelven** a pH muy alto (> 11–12). Irrelevante en agronomía, pero el modelo no lo captura.
- No incluye competencia con **fosfato y carbonato**, que forman sus propios sólidos y pueden precipitar el micro **antes** que el hidróxido.
- No incluye **quelatos** — que es precisamente lo que cambia todo el cuadro (§3.5, §6).

### 3.4 Ventana de pH operativa del caldo

La ventana no la fija un solo criterio, sino la **intersección** de cinco restricciones. Ésta es la síntesis:

| Restricción | Límite | Fuente |
|---|---|---|
| Precipitación de Cu²⁺ no quelatado (foliar) | pH **≤ 6,0** | §3.2 **[CALC]** |
| Precipitación de brushita (Ca + P) | pH **≤ 6,0** | §2.2 **[CALC]** |
| Precipitación de estruvita (Mg + NH₄ + P) | pH **≤ 7,5** | §2.3 **[CALC]** |
| Hidrólisis alcalina de plaguicidas | pH **4,0 – 6,5** | Purdue PPP-86 **[MED]** |
| Hidrólisis alcalina de plaguicidas | pH **4 – 6,5** óptimo | Virginia Tech BSE-350P **[MED]** |
| Almacenamiento corto en tanque | pH **3,5 – 6** satisfactorio | Purdue PPP-86 **[MED]** |
| Rango aceptable general en tanque | pH **6 – 8** | Sprayers101 / Storrie **[PRAC]** |
| Rango aceptable general en tanque | pH **4 – 7** | Sprayers101 / Wolf **[PRAC]** |
| **Excepción — sulfonilureas** | pH **7 – 8** (¡al revés!) | Purdue PPP-86 **[MED]** |

> ### VENTANA RECOMENDADA: **pH 5,0 – 6,5**
> Con **dos excepciones que la invierten**:
> 1. **Sulfonilureas**: requieren **pH 7–8**. Su eficacia *empeora* con agua ácida. *"The efficacy of weak-acid herbicides such as glyphosate, glufosinate, clethodim, sethoxydim, bentazon, and 2,4-D is improved with acidic water pH; however, the efficacy of sulfonylurea herbicides is negatively impacted."* **[MED]** — Weed Technology 36(6):758–767, DOI 10.1017/wet.2022.97
> 2. **Mezcla dicamba + glifosato**: el glifosato **baja el pH del tanque de 8 a menos de 4**, y esa caída **aumenta la volatilización de dicamba**. En Australia la recomendación es **no agregar glifosato a la mezcla con dicamba**. **[MED/PRAC]** — Storrie, Sprayers101, 28-07-2026, https://sprayers101.com/ph-hardness/

**Dato operativo crítico y poco conocido** [MED]: **el pH del tanque no es el pH del agua.** El glifosato lo derrumba de 8 a < 4; las formulaciones de dicamba lo llevan a 6,5–6,9 (Storrie, misma fuente). **Medir el pH del agua antes de cargar y decidir sobre ese número es un error metodológico** — hay que medirlo sobre el caldo terminado.

### 3.5 Quelatos — lo que se pudo y lo que no

**[MED]** El polifosfato sí funciona como secuestrante y está cuantificado — ver **§6**.

**[NV]** Las constantes de estabilidad y los rangos de pH útiles de **EDTA, DTPA, EDDHA, EDDHSA y HEDTA**, y la razón cuantitativa por la que el Fe-EDTA falla por encima de pH ~6,5, **no se pudieron verificar en esta sesión** (presupuesto de búsqueda agotado). Ver §10. Es una laguna consciente de este dossier y, dado el hallazgo (a) del §3.3, es la **laguna más importante que queda por cerrar**.

---

## 4. ORDEN DE CARGA DEL TANQUE

### 4.1 Los estándares publicados

**W.A.L.E.S.** es el estándar histórico. **BASF lo extendió a W.A.M.L.E.G.S.** **[MED]**

**Motivo declarado del cambio** [MED]: *"With the development of new pesticide formulations with different mixing characteristics, the WALES mixing acronym has become outdated. Microencapsulated suspensions and glyphosate with new high-load inert packages have moved the industry to use a new acronym, WAMLEGS."*

| Letra | Contenido | Fuente |
|---|---|---|
| **W** | Water soluble packets, wettable powders, dry flowables | BASF / Exacto / Grainews |
| **A** | Agitation and buffers (antiespumantes, acondicionadores) | ídem |
| **M** | Microcapsule suspension (CS) | ídem |
| **L** | Liquids and solubles (SC, SL) | ídem |
| **E** | Emulsifiable concentrates (EC) | ídem |
| **G** | High-load glyphosate products | ídem |
| **S** | Surfactants | ídem |

**Fuentes** [MED]: https://www.exactoinc.com/blog/2021/11/09/pesticide-tank-mix-incompatibility/ · https://www.grainews.ca/crops/good-to-be-mixed-up-in-the-right-order/ · https://ag.fmc.com/ca/en/fmc-news/everything-order-tips-mixing-herbicides-right-order

**Nota Exacto** [MED]: después de la secuencia WAMLEGS *"add micronutrients and fertilizers"* — los fertilizantes van **al final**.

### 4.2 Variante Sprayers101 (por tipo de formulación, más granular)

**[MED]** — https://sprayers101.com/loading-jartest/

1. **WSB** — Water-Soluble Bags (dejar disolver por completo)
2. **WP** — Wettable Powders
3. **WDG / WG / SG** — Water Dispersible Granules
4. **F / FL / SC / SE / CS / DC / EW** — Liquid flowables
5. **EC / MEC / OD** — Emulsifiable concentrates
6. **SN / SL / fertilizantes líquidos** — Solutions

**Adyuvantes, fuera de la secuencia principal:**
- **Acondicionadores de agua → PRIMERO** (antes que todo)
- **Surfactantes activadores → después de los plaguicidas**
- **Antideriva → ÚLTIMO**

**Espera entre adiciones**: *"Allow 3–5 minutes between additions — especially for dry products — to ensure full dispersion."*

Acrónimos reconocidos: **W.W.W.W.A.L.E.S.**, **W.A.M.L.E.G.S.**, **A.P.P.L.E.S.** — descritos como *"reliable guides 95 % of the time"*, pero **"always defer to the pesticide label for specific instructions."**

### 4.3 Variante Embrapa (referencia institucional en portugués)

**Manual técnico para subsidiar a mistura em tanque de agrotóxicos e afins** — **Embrapa Soja, Série Documentos nº 437**, en conjunto con la **UENP** (Universidade Estadual do Norte do Paraná) y **Bayer CropScience**. Anuncio: 26-08-2021. **[MED, referencia]**
PDF: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1132371/1/DOCUMENTOS-437-1.pdf

**Lo verificado del contenido** (vía resumen secundario — **el texto del PDF no se pudo extraer en este entorno**):
- Los **fertilizantes foliares entran en el paso 10**, seguidos del **resto del agua en el paso 11**. La secuencia completa tiene al menos 11 pasos numerados.
- Prueba de compatibilidad: **recipiente transparente con tapa, 2/3 de agua**, productos añadidos **en el mismo orden recomendado para el tanque**.
- Declara que **pH, concentración de cationes, dureza y turbidez** influyen directamente en la calidad y seguridad de la mezcla en tanque.

> ⚠ **Los pasos 1 a 9 del orden Embrapa no se pudieron leer directamente.** Se recomienda descargar el PDF y verificarlos antes de adoptarlo como estándar interno. Ver §10.

### 4.4 POR QUÉ cada posición — la lógica física

Aquí está la parte que los acrónimos no explican. **Todo el orden de carga se deduce de dos principios:**

> **P1 — Lo que necesita tiempo y agua libre para dispersarse, entra primero.**
> **P2 — Lo que altera las propiedades del solvente (tensión superficial, viscosidad, fuerza iónica), entra al final.**

| Posición | Formulación | Razón física |
|---|---|---|
| **0** | **Tanque a media carga + agitación** | Un sólido cargado sobre poca agua forma pasta en el fondo, fuera del alcance del agitador. **[PRAC]** |
| **0.5** | **Acondicionadores de agua (AMS, secuestrantes)** | **Deben secuestrar Ca²⁺/Mg²⁺ ANTES de que aparezca el activo que los teme.** Si el glifosato entra primero, la sal cálcica ya se formó y el AMS llega tarde. Esto es cinética, no equilibrio. **[MED]** (mecanismo, §7.1) |
| **1** | **WSB / WP / WDG / SG (sólidos)** | Necesitan **agua libre** y tiempo para humectarse y dispersarse. Si entran después de un EC, el aceite recubre el gránulo y **nunca se moja**. Requieren los 3–5 min de espera. **[MED]** |
| **2** | **A — buffers, antiespumantes** | Fijan el pH **antes** de que entren los activos hidrolizables (§8.2). **[PRAC]** |
| **3** | **CS — microcápsulas** | La cápsula polimérica es frágil frente a solventes; entra antes que los EC para minimizar su tiempo de contacto con solventes orgánicos. **[PRAC]** |
| **4** | **SC / SL — suspensiones y solubles** | Ya están dispersos; poca demanda de agua libre. **[PRAC]** |
| **5** | **EC / OD — emulsionables y aceites** | **Aportan fase orgánica.** Una vez presentes, la dispersión de cualquier sólido posterior queda comprometida. **[PRAC]** |
| **6** | **G — glifosato de alta carga** | Su paquete de inertes de alta carga **altera fuertemente la fuerza iónica**; puede desestabilizar emulsiones ya formadas. **[MED]** (motivo declarado del cambio WALES→WAMLEGS) |
| **7** | **S — surfactantes** | Bajan la tensión superficial. Si entran antes, **generan espuma masiva** durante toda la carga y falsean el volumen. **[PRAC]** |
| **8** | **Fertilizantes foliares / micronutrientes** | Aportan **cationes divalentes y trivalentes** — la fuente exacta de todo el §2 y §3. Entran cuando el resto ya está estabilizado, y **nunca antes de un plaguicida sensible a cationes**. **[MED]** Exacto + Embrapa paso 10 |
| **9** | **Antideriva** | Polímeros de cadena larga; el cizallamiento de la bomba durante una carga larga los **degrada**. Último = menos cizallamiento. **[PRAC]** |
| **10** | **Completar agua** | Embrapa paso 11. **[MED]** |

**Excepción documentada y contraintuitiva — ATS**
**[MED]** El **tiosulfato de amonio (ATS) debe entrar DESPUÉS del herbicida**, no antes: *"adding stabilizer will not reverse a tank mix error arising from adding ATS prior to the herbicide."* Cuando UAN y ATS se **premezclan** antes de agregar el herbicida, **hay incompatibilidad sin importar qué estabilizante se agregue después**. — Deveau (OMAFA) sobre trabajo de M. Schryver (BASF), Sprayers101, https://sprayers101.com/nitrogen_stabilizers/

> **Esto es lo más importante del §4:** el orden de carga **no es una preferencia de prolijidad. Es irreversible.** Un error de orden **no se corrige agitando más, ni agregando adyuvante después.** El ATS es el caso probado experimentalmente.

---

## 5. PROTOCOLO ESTÁNDAR DE PRUEBA DE JARRA (JAR TEST)

### 5.1 Los tres protocolos publicados, lado a lado

| Parámetro | **UNL G2350** (Nebraska, 2023) | **Sprayers101** (Deveau/Wolf) | **Embrapa Doc. 437** |
|---|---|---|---|
| Recipiente | Frasco de vidrio transparente de **1 cuarto (≈946 mL)** | Frasco de vidrio de **1 litro** | Recipiente transparente **con tapa** |
| Volumen de agua | **1 pinta (473 mL)** | **250 mL** (**375 mL** si el vehículo es aceite o fertilizante) | **2/3** del recipiente |
| Volumen final | — | **500 mL** | — |
| Orden | Plan **D-A-L-E-S** | WSB→WP→WDG→flowables→EC→soluciones | **El mismo orden del tanque** |
| Dosis: sólidos (DF/WP) | **1 cucharada sopera** por cada **libra/100 galones** del caldo final | proporción real de tanque | proporción real de tanque |
| Dosis: líquidos (SC/EC/SL) | **1 cucharadita** por cada **pinta/100 galones** del caldo final | proporción real de tanque | proporción real de tanque |
| Entre adiciones | **Agitar** entre cada adición | **Esperar 3–5 min** (sobre todo sólidos) | — |
| Reposo | **10–15 min** | **15 min** + observación **toda la noche** | — |
| Señales de fallo | Separación en capas, grumos, espuma, **calor**, precipitado | **Calor**, gel, nata (*scum*), sólidos asentados | — |

**Fuentes** [MED]:
- UNL G2350: https://extensionpubs.unl.edu/publication/g2350/2023/pdf/view/g2350-2023.pdf
- Sprayers101: https://sprayers101.com/loading-jartest/
- Embrapa Documentos 437: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1132371/1/DOCUMENTOS-437-1.pdf
- Adicional (protocolo con tamizado): Sprayers101 / OMAFA, https://sprayers101.com/nitrogen_stabilizers/
- Adicional: UF/IFAS PI301 · Montana State · UADA FSA-2166 — **referencias localizadas, texto no recuperado** (§10)

### 5.2 PROTOCOLO OPERATIVO REPRODUCIBLE

Protocolo armonizado a partir de las tres fuentes anteriores más el método de laboratorio de BASF/OMAFA. **Los pasos marcados [MED] provienen literalmente de una fuente; los marcados [PRAC] son integración de este dossier.**

---

#### **PASO 0 — Antes de tocar nada**

**0.1 EPP** **[MED]** — *"be sure to wear the appropriate PPE as directed by the label. If no specific PPE is listed for doing a jar test (usually there is not), then follow the PPE guidance as if you were mixing and loading."* (Sprayers101)

**0.2 Use el agua REAL** **[MED]** — *"It is important to use the source water you use to fill your tank."* No agua destilada, no agua de la canilla del galpón si va a cargar del pozo. **Todo el §7 depende de esto.**

**0.3 Registre las condiciones de partida** **[PRAC]** — antes de cargar, mida y anote:

| Variable | Instrumento | Por qué |
|---|---|---|
| **pH del agua** | pHmetro | Línea de base (§3.4) |
| **Dureza (mg/L CaCO₃)** | kit o análisis | §7.1 |
| **Bicarbonatos (mg/L)** | análisis | §7.2 |
| **Temperatura del agua (°C)** | termómetro | §8 — **es una variable, no un detalle** |
| **Turbidez** | prueba del balde (§7.4) | §7.4 |

---

#### **PASO 1 — Definir la escala y calcular las alícuotas**

> ### ⚠ EL PRINCIPIO NO NEGOCIABLE DE LA PRUEBA DE JARRA
>
> **La jarra debe reproducir la DILUCIÓN REAL del caldo, no una dilución cómoda.**
>
> **Por qué, cuantitativamente:** por el §1.1, el índice de saturación de un par 2:2 **escala con el cuadrado de la concentración**. Una jarra preparada al doble de dilución que el tanque tiene un **producto iónico 4 veces menor** — es decir, un **SI 0,6 unidades más bajo**. Una jarra al 10× de dilución tiene un **SI 2 unidades más bajo**.
>
> **Consecuencia:** una jarra mal diluida **pasa limpia una mezcla que precipitará en el tanque.** No es un error de precisión: es un **falso negativo estructural**, y es el modo de fallo más común de esta prueba. Igual que un control nulo mal construido, **una jarra que no puede reprobar no es una prueba.**
>
> Esto se aplica con el mismo rigor a la relación **volumen de caldo por hectárea**: la misma dosis de producto en 50 L/ha vs. 200 L/ha son dos caldos con **4× de diferencia** en concentración y, por lo tanto, **16× de diferencia** en producto iónico para un par 2:2. **[CALC]**

**Regla de cálculo general** **[PRAC]**:

$$V_{producto\ en\ jarra} = \frac{\text{Dosis por hectárea}}{\text{Volumen de caldo por hectárea}} \times V_{jarra}$$

**Método rápido UNL (sistema imperial)** **[MED]** — para una jarra de **1 pinta (473 mL)** de agua:
- **Sólidos (DF, WP):** **1 cucharada sopera** por cada **libra por 100 galones** del caldo planificado.
- **Líquidos (SL, EC, SC):** **1 cucharadita** por cada **pinta por 100 galones** del caldo planificado.

**Método métrico (recomendado, escala 1:1000)** **[PRAC]** — jarra de **500 mL** que representa **500 L de caldo**:
- Multiplique cada dosis, en unidades de caldo, por **0,001**.
- Ejemplo: 2,0 L/ha de producto en 200 L/ha de caldo → concentración 1 % v/v → **5,0 mL en la jarra de 500 mL**.
- **Verificación obligatoria:** la suma de todos los productos + agua debe dar exactamente 500 mL.

---

#### **PASO 2 — Cargar (replicando el orden del tanque)**

2.1 Cargue **la mitad del volumen final de agua**: **250 mL** para jarra de 500 mL. Si el vehículo es aceite o fertilizante líquido, cargue **375 mL**. **[MED]**

2.2 Agregue los productos **en el orden exacto de la etiqueta**, o en su defecto **WAMLEGS** (§4.1). **[MED]**

2.3 **Entre cada adición: agitar y esperar.** **[MED]**
- **Sólidos (WSB, WP, WDG): 3–5 minutos.** No negociable.
- Líquidos: agitar hasta homogeneizar.
- *(Método de laboratorio BASF/OMAFA: adiciones a intervalos de 1 minuto con **barra magnética de agitación**.)* **[MED]**

2.4 Complete a **500 mL** con el agua restante. Tape y **invierta 10 veces** (no sacuda violentamente: la espuma enmascara la observación). **[PRAC]**

---

#### **PASO 3 — Reposo**

| Ventana | Duración | Qué detecta |
|---|---|---|
| **Inmediata** | 0–2 min | **Exotermia**, efervescencia, gel instantáneo |
| **Corta** | **15 min** **[MED]** | Separación de fases, floculación, crema |
| **Estándar** | **1 hora** **[MED]** | Precipitación lenta, sedimentación |
| **Extendida** | **Toda la noche** **[MED]** | *"you can see if products separate or solidify over time"* |

**Temperatura durante el reposo** **[PRAC]**: mantenga la jarra a la **temperatura a la que realmente se aplicará el caldo**. Una jarra que reposa a 22 °C en el galpón no predice un tanque a 8 °C en la madrugada de aplicación (§8.1).

---

#### **PASO 4 — Observar. Los seis modos de fallo**

| # | Modo | Qué se ve | Qué significa |
|---|---|---|---|
| 1 | **Precipitado** | Sólido en el fondo, cristalino o amorfo | **Sobresaturación** — §2, §3. Irreversible. |
| 2 | **Floculación** | Grumos, copos, "leche cortada" | Desestabilización coloidal de una SC. |
| 3 | **Separación de fases** | Dos capas, crema arriba o aceite abajo | **Ruptura de emulsión** — típico EC en fertilizante líquido (§7.5, §8.3). |
| 4 | **Gel / aumento de viscosidad** | Se espesa, no fluye | Fallo grave: **tapa filtros y bomba**. |
| 5 | **Exotermia** | **La jarra se calienta al tacto** | ⚠ **REACCIÓN QUÍMICA EN CURSO.** El modo más grave: no es incompatibilidad física, es **química**. **Aborte inmediatamente.** |
| 6 | **Nata / espuma persistente** (*scum*) | Película en superficie que no reintegra | Incompatibilidad de tensioactivos. |

**Fuentes de los modos** **[MED]**: UNL G2350 (*"separate into layers, create clumping or foam, give off heat, or precipitate"*); Sprayers101 (*"heat generation, gel formation, scum development, or settling solids"*).

---

#### **PASO 5 — Prueba de reversibilidad (la que separa un susto de un fallo)**

**[MED]** — *"If mixture appears compatible, allow it to stand for 1 hour, stir well, and check it again. Any persistent signs of precipitation, gelling, layering, or difficulty in re-suspending settled material indicate incompatibility."* (UF/IFAS PI301, vía resumen)

**Criterio de decisión:**

| Observación | Veredicto |
|---|---|
| Sedimenta, pero **reintegra completamente** al agitar | **PASA** — compatible con agitación continua en tanque. |
| Sedimenta y **NO reintegra**, o cuesta reintegrarlo | **REPRUEBA** — incompatible. |
| **Exotermia** en cualquier momento | **REPRUEBA** sin más análisis. |

**Prueba de tamiz (nivel laboratorio)** **[MED]**: el método BASF/OMAFA agrega un paso final — tras el reposo, **agitar y verter a través de un tamiz de malla 100**. Simula el filtro de la pulverizadora. *"Components separated during rest periods but readily reintegrated with agitation and passed filtration screening."*
**Recomendación de este dossier [PRAC]: incorpore el tamiz.** Es el único paso que verifica el criterio que realmente importa a campo — **si pasa el filtro de la máquina**.

---

#### **PASO 6 — Escenario de peor caso**

**[MED]** El método BASF/OMAFA ensaya deliberadamente contra el peor caso:
- **UAN enfriado a ≈ −5 °C**
- Herbicidas al **doble (2×) de la dosis de etiqueta**
- Simulando **10 galones por acre** (volumen de caldo bajo = concentración alta)

**Recomendación [PRAC]:** si la mezcla es nueva o cara, corra **dos jarras**: una a condición nominal y otra a **peor caso** (dosis alta + volumen de caldo mínimo + agua fría). Si la nominal pasa y la de peor caso reprueba, la mezcla es viable **pero con ventana operativa estrecha** — y eso hay que escribirlo en la recomendación, no descubrirlo en el lote.

---

### 5.3 LA LIMITACIÓN QUE HAY QUE DECLARAR SIEMPRE

> **[MED]** *"It is important to note that a jar test only tests physical incompatibilities, not chemical incompatibilities."* — resumen de fuentes de extensión (UF/IFAS, UNL, Montana State, MSU)

**Qué NO ve la prueba de jarra:**

| Invisible en la jarra | Se manifiesta como |
|---|---|
| **Hidrólisis alcalina** del activo (§8.2) | Caldo perfectamente transparente, **eficacia nula a campo**. |
| **Antagonismo de absorción** (glifosato-Ca, §7.1) | Caldo limpio y estable, **la maleza no muere**. |
| **Adsorción a arcilla** en agua turbia (§7.4) | Caldo turbio pero homogéneo, **el activo ya no está disponible**. |
| **Fitotoxicidad** de la combinación | Aparece en la hoja **días después**. |
| **Degradación lenta** durante la jornada (§8.4) | La primera carga funciona, la última no. |

**Corolario metodológico:** *pasar la jarra* es **condición necesaria y no suficiente**. Una mezcla que pasa la jarra puede fracasar por completo. La jarra descarta un modo de fallo — el físico — y **no dice absolutamente nada sobre los otros cinco.** Declararlo en el informe al cliente no es cautela: es exactitud.

---

## 6. POLIFOSFATOS COMO SECUESTRANTES

### 6.1 Composición del APP 10-34-0

**[MED]** El 10-34-0 contiene **~30–40 % de ortofosfato** (absorción inmediata) y **~60–70 % de polifosfato** (liberación sostenida). — https://www.agvise.com/phosphorus-fertilizer-forms-orthophosphate-or-polyphosphate-ortho-p-or-poly-p/ (vía resumen de búsqueda)

### 6.2 El mecanismo de secuestro

**[MED]** *"A unique property of ammonium polyphosphate (APP, 10-34-0) is the ability to chelate or sequester metal cations, such as micronutrients like zinc, in the polyphosphate molecule."* APP secuestra **Fe²⁺/Fe³⁺, Zn²⁺, Ca²⁺ y Mg²⁺**.

**Físicamente:** la cadena polifosfato es un **ligando multidentado**. Los oxígenos de los grupos fosfato sucesivos envuelven al catión formando quelatos de varios anillos. El efecto sobre el §1 es directo: **baja la actividad del catión libre**, y por lo tanto **baja el producto iónico**, sin bajar la concentración analítica. Es la única forma de estar "por encima del Ksp" en el papel y no precipitar.

### 6.3 HASTA DÓNDE LLEGA — el número

> **[MED]** **El polifosfato amónico mantiene 2 % de Zn en solución. El ortofosfato puro sólo 0,05 %.**
>
> **Factor 40×.**

Ésta es la cuantificación que pedía el encargo, y es notable: no es una mejora marginal, es un cambio de régimen. Permite formular fertilizantes líquidos NP + micronutrientes que serían **termodinámicamente imposibles** con ortofosfato.

Fuentes **[MED]**: https://www.agvise.com/phosphorus-fertilizer-forms-orthophosphate-or-polyphosphate-ortho-p-or-poly-p/ · Mosaic Crop Nutrition, https://www.cropnutrition.com/resource-library/polyphosphate/ (vía resumen; fetch bloqueado)

### 6.4 Hidrólisis a ortofosfato — dónde termina la protección

**[MED]** *"Plant roots can only absorb waterborne orthophosphate, so APP does not provide any nutrient value to plants until it is hydrolysed to orthophosphate. Orthophosphate is released from APP by unzipping from the APP chain ends."*

**El hallazgo mecanístico clave — y es una paradoja operativa** **[MED]**:

> *"Zn²⁺ decreased the stability of the P–O–P bond by causing a conformational change in the polyphosphate due to chelation, which in turn promoted APP hydrolysis. APP hydrolysis switches from **unzipping** to **random chain scission** when catalysed by Zn²⁺, Fe²⁺ and/or Al³⁺, promoting hydrolysis by generating more end-groups."*
>
> — *Hydrolysis Mechanism of Water-Soluble Ammonium Polyphosphate Affected by Zinc Ions*, PMC10210202, https://pmc.ncbi.nlm.nih.gov/articles/PMC10210202/
> — Revisión: *Ammonium polyphosphates: correlating structure to application*, European Polymer Journal (2025), https://knowledge.lancashire.ac.uk/id/eprint/54201/2/Hansen-Bruhn_Hull_APP_applications_Eur_Polym_J_2025.pdf

**Lo que esto significa para el formulador:**

El catión que el APP está protegiendo (Zn²⁺, Fe²⁺, Al³⁺) es **el mismo catión que cataliza la destrucción del protector**. La quelación deforma la cadena, debilita el enlace P–O–P y cambia el mecanismo de hidrólisis de *unzipping* (lento, desde los extremos) a **escisión aleatoria de cadena** (rápida, en cualquier punto, generando más extremos y **autoacelerándose**).

> **Consecuencia: la protección del APP tiene fecha de vencimiento, y la carga de micronutriente ACELERA el reloj.** Cuanto más Zn cargue, más rápido se degrada la cadena que lo sostiene. Cuando el polifosfato se hidroliza a ortofosfato, se pierde el secuestro **y** aparece el ortofosfato que precipita al Zn y al Ca (§2.2). **La falla es doble y simultánea.**

**Límite operativo derivado [PRAC]:** un APP con micronutrientes cargados **no es un producto de almacenamiento indefinido.** Debe tratarse como una formulación con vida útil, y la vida útil es **más corta cuanto mayor la carga de micro**.

### 6.5 El pH de hidrólisis — laguna declarada

**[NV]** El encargo pedía específicamente **"a qué pH se hidroliza a ortofosfato"**. Se verificó:
- ✅ El mecanismo (unzipping vs. escisión aleatoria)
- ✅ La catálisis por Zn²⁺/Fe²⁺/Al³⁺
- ✅ Que la hidrólisis es requisito para la disponibilidad para la planta
- ❌ **NO se pudo recuperar el umbral de pH ni la ley de velocidad cuantitativa** (t½ vs. pH y temperatura)

Se sabe cualitativamente que la hidrólisis de polifosfatos se acelera en **medio ácido** y con **temperatura**, pero **no se cita un número sin verificarlo**. Ver §10.

---

## 7. CALIDAD DEL AGUA

### 7.1 Dureza (Ca²⁺ / Mg²⁺)

#### Clasificaciones publicadas — nótese que NO coinciden

| Clase | **Purdue PPP-86** (clasif. OMS) | **Virginia Tech BSE-350P** |
|---|---|---|
| Blanda | 0–114 ppm | < 75 ppm |
| Moderadamente dura | 114–342 ppm | 75–150 ppm |
| Dura | 342–800 ppm | 150–300 ppm |
| Muy / extremadamente dura | > 800 ppm | > 300 ppm |

**[MED]** — Purdue: https://ag.purdue.edu/department/extension/ppp/resources/ppp-publications/mobile/ppp-86/the-impact-of-water-quality-on-pesticide-performance.html · Virginia Tech: Ling, E., Parson, R., Frank, D., Mohamed, D., Kline, K., Spiller, A. & Horn, D. (2024). *Spray water quality and pesticide characteristics*, VCE **BSE-350P**. https://www.pubs.ext.vt.edu/BSE/bse-350/bse-350.html

> ⚠ **Las dos escalas difieren por un factor de ~2,7.** Lo que Virginia Tech llama "muy dura" (> 300 ppm), Purdue todavía lo llama "dura". **Nunca transfiera un umbral de dureza sin declarar la escala de origen.**

#### Umbrales de acción — cuánto degrada cada uno

| Umbral | Efecto | Fuente |
|---|---|---|
| **> 120 ppm** | Amerita considerar tratamiento | Virginia Tech BSE-350P **[MED]** |
| **> 250–350 ppm CaCO₃** | Requiere tratamiento antes de aplicar herbicidas de ácido débil (glifosato, 2,4-D amina) | Storrie, Sprayers101 **[MED]** |
| **< 350 ppm** | Suficiente para la **dosis baja** de glifosato (equiv. ½ L/ac) | Wolf, Sprayers101 **[MED]** |
| **< 700 ppm** | Suficiente para las **dosis altas** de glifosato | Wolf, Sprayers101 **[MED]** |
| **> 350 ppm** | La eficacia del glifosato **puede verse afectada** | Virginia Tech BSE-350P **[MED]** |
| **500 ppm** | El **2,4-D puede quedar completamente desactivado** | Virginia Tech BSE-350P **[MED]** |
| **Fe > 25 ppm** y **dureza + Fe > 400** | Se aconseja acondicionar el agua | Purdue PPP-86 **[MED]** |

**Herbicidas sensibles a dureza** **[MED]**: **glifosato, 2,4-D, imazetapir, glufosinato** — los *"weak-acid, salt-based pesticides"*. (Virginia Tech BSE-350P)

#### El mecanismo — y por qué es un problema de ABSORCIÓN, no de precipitación

**[MED]** *"Calcium associates with both the carboxyl and phosphonate groups on the glyphosate molecule. Initially, a random association of the compounds occurs; however, the reaction progresses to yield a more structured, chelate type complex over time."* — *The Basis for the Hard-Water Antagonism of Glyphosate Activity*, **Weed Science**, https://www.cambridge.org/core/journals/weed-science/article/abs/basis-for-the-hardwater-antagonism-of-glyphosate-activity/1B115821F1CAFEB89F926BBB1CE66810 *(autores/año/DOI **no verificados** en esta sesión — §10)*

> **Éste es el punto que hay que entender:** la sal cálcica de glifosato **es soluble**. El caldo se ve **perfectamente limpio**. **La prueba de jarra la pasa sin ninguna señal.** El fallo no es físico: la molécula Ca-glifosato **no atraviesa la cutícula**. Se pulveriza la dosis completa de un activo que **no puede entrar en la planta**.
>
> Y hay un agravante temporal: *"the reaction progresses to yield a more structured, chelate type complex **over time**"*. **El daño aumenta cuanto más tiempo el caldo permanece en el tanque** (§8.4).

#### La corrección — sulfato de amonio (AMS)

**Mecanismo en dos pasos** **[MED]**:
1. **El sulfato secuestra el calcio.** SO₄²⁻ + Ca²⁺ → CaSO₄, impidiendo la formación de la sal cálcica de glifosato, que se absorbe mal por la hoja. *(Nota: esto es el §2.1 usado deliberadamente **a favor** — se provoca la precipitación de yeso para proteger al activo.)*
2. **El amonio compite por el sitio.** *"NH₄⁺ effectively competed with calcium for complexation sites on the glyphosate molecule. When glyphosate binds to ammonium, the resultant molecule is much more easily absorbed through the leaf cuticle, through the cell wall, or across the plasma membrane."*

**Dosis publicadas:**

| Dosis | Contexto | Fuente |
|---|---|---|
| **1–3 % w/v** de 21-0-0-24, **antes** del herbicida | Glifosato, dureza | Wolf, Sprayers101 **[MED]** |
| **20 g/L (2 % w/v)** | Revierte el antagonismo del **2,4-D DMA** | Weed Technology **[MED]** |
| **1,6 L/ac** (líquido 490 g/L) o **0,8 kg/ac** (seco 99 %) | Restaura el control con **cletodim** en agua bicarbonatada | Saskatchewan Agriculture **[MED]** |
| **0,5 L/ac de 28-0-0**, agregado **antes** del cletodim | Alternativa a AMS | Saskatchewan Agriculture **[MED]** |

**[MED]** Saskatchewan: https://www.saskatchewan.ca/business/agriculture-natural-resources-and-industry/agribusiness-farmers-and-ranchers/crops-and-irrigation/weeds/water-quality-and-herbicides (vía resumen de búsqueda)

> **El orden es parte de la dosis.** Todas las fuentes coinciden en **"antes del herbicida"**. Es cinética: el AMS debe ocupar el calcio **antes** de que el activo lo encuentre. Agregado después, llega a una reacción ya ocurrida. Ver §4.4, posición 0.5.

### 7.2 Bicarbonatos

| Umbral | Efecto | Fuente |
|---|---|---|
| **400–500 ppm HCO₃⁻** | Afecta el desempeño de **sethoxydim (Poast), cletodim (Select), tralkoxydim (Achieve) y 2,4-D amina** | Saskatchewan **[MED]** |
| **≥ 500 ppm** | **Reduce la actividad del cletodim** | Saskatchewan **[MED]** |
| **> 500 ppm** | Inhibe herbicidas del **Grupo 1 ('dims')** y **2,4-D amina** | Storrie, Sprayers101 **[MED]** |
| **Hasta 1000 ppm** | **Poast (sethoxydim) generalmente se ha desempeñado satisfactoriamente** | Saskatchewan **[MED]** |

> **El bicarbonato es un problema distinto de la dureza y hay que medirlo aparte.** Un agua puede ser blanda y muy bicarbonatada (aguas sódicas). Los herbicidas afectados son **específicamente los "dim" (Grupo 1) y el 2,4-D amina** — no es un efecto general.

**Nota de calibración honesta:** el propio corpus tiene una inconsistencia interna — Saskatchewan dice que **≥ 500 ppm reduce el cletodim** y en la misma fuente que **Poast tolera hasta 1000 ppm**. Ambos son "dims". La respuesta **es específica de la molécula**, no de la familia química. No extrapole entre principios activos del mismo grupo.

### 7.3 pH

Ver la ventana operativa completa en **§3.4**. Los datos duros de hidrólisis están en **§8.2**.

**Los dos datos que más cambian la práctica** **[MED]**:
1. **La degradación aumenta ~10× por cada unidad de pH.** (Virginia Tech BSE-350P)
2. **El pH del agua NO es el pH del caldo.** El glifosato lo lleva de 8 a **< 4**; el dicamba a 6,5–6,9. (Storrie, Sprayers101) → **mida sobre el caldo terminado.**

**Conductividad eléctrica** **[MED]**: valores **< 500 µS/cm se consideran seguros**. (Wolf, Sprayers101, https://sprayers101.com/water-quality/)

### 7.4 Turbidez

**Mecanismo** **[MED]**: *"The negative effect of spray water turbidity on herbicide efficacy has been attributed to the binding of sediment or negatively charged clay particles to the highly polar and positive-charged herbicide molecule, which resulted in a reduction in plant uptake."*

**Efectos medidos** **[MED]**:
- **Diquat**: eficacia reducida por adsorción a **montmorillonita y caolinita** en la solución de pulverización.
- **Glifosato y nicosulfurón**: eficacia reducida sobre *Echinochloa crus-galli* (capín) y *Abutilon theophrasti* con partículas de suelo en el agua de pulverización.
- **Paraquat y diquat** (cationes): se adsorben fuertemente a partículas suspendidas con carga negativa.
- Fuentes: Weed Technology 36(6):758–767, DOI 10.1017/wet.2022.97 · https://pubs.acs.org/doi/10.1021/jf00076a013 · https://pmc.ncbi.nlm.nih.gov/articles/PMC6822125/

**Prueba de campo — el balde** **[MED]**: si **no se puede ver una moneda en el fondo de un balde de 5 galones (≈19 L)**, el agua está demasiado turbia. (Virginia Tech BSE-350P)

**Corrección** **[MED]**: **sulfato de aluminio a 10–60 mg/L**, logrando **80–95 % de remoción en 24–48 horas**. (Wolf, Sprayers101)

> ⚠ **Nótese la escala temporal: 24–48 HORAS.** Ésta no es una corrección de tanque — es una **corrección de reservorio**, que hay que planificar con dos días de anticipación. En la práctica operativa esto significa que **la turbidez no se corrige el día de la aplicación.** Ver §11.

### 7.5 Resumen — cuánto degrada cada variable

| Variable | Umbral de acción | Magnitud del daño | Corrección | ¿Funciona? |
|---|---|---|---|---|
| **Dureza** | > 250–350 ppm CaCO₃ | 2,4-D **completamente desactivado** a 500 ppm | AMS 1–3 % w/v **antes** del herbicida | ✅ Sí, bien documentada |
| **Bicarbonatos** | > 400–500 ppm | Reduce Grupo 1 y 2,4-D amina | AMS o 28-0-0 antes del herbicida | ✅ Sí |
| **pH alto** | > 7 | **~10× más degradación por unidad de pH** | Buffer/acidificante **antes** de los activos | ✅ Sí, salvo sulfonilureas |
| **Turbidez** | Moneda invisible en balde de 19 L | Reduce absorción de glifosato, diquat, nicosulfurón | Sulfato de Al 10–60 mg/L, **24–48 h antes** | ⚠ Sí, pero **no el mismo día** |
| **Hierro** | > 25 ppm (y dureza+Fe > 400) | Acondicionamiento aconsejado | AMS / secuestrante | ⚠ Parcial |
| **CE** | > 500 µS/cm | Indicador de carga iónica total | — | — |

---

## 8. EFECTOS DE LA TEMPERATURA

### 8.1 Temperatura del agua sobre la dispersión y la mezcla

**[MED]** *"Carrier and product temperature affect mixing"* — las **formulaciones secas tardan más en dispersarse en frío**. (Sprayers101, https://sprayers101.com/loading-jartest/)

**[MED]** El método de laboratorio BASF/OMAFA usa **UAN enfriado a ≈ −5 °C** como **escenario de peor caso** deliberado, precisamente porque el frío es la condición crítica para la compatibilidad. Bajo esa condición, EC y SC se mantuvieron compatibles con UAN + estabilizantes; los componentes **se separaron durante el reposo pero se reintegraron con agitación** y pasaron el tamiz de malla 100.

**Implicación operativa** **[PRAC]**: el tiempo de espera de **3–5 min entre sólidos** del §5.2 es un valor para condiciones templadas. **En agua fría hay que extenderlo**, y la prueba de jarra debe correrse a la temperatura real de aplicación (§5.2, Paso 3).

### 8.2 Temperatura + pH sobre la hidrólisis del activo

La hidrólisis alcalina es una **reacción química**, y como toda reacción química **se acelera con la temperatura**. La combinación **agua alcalina + agua caliente + caldo que espera** es el peor escenario posible.

**Vidas medias medidas** **[MED]** — Virginia Tech BSE-350P (Ling et al., 2024), Tabla 2:

| Plaguicida | t½ a **pH 6** | t½ a **pH 9** | Factor de pérdida |
|---|---|---|---|
| **Dimetoato** | 12 horas | **48 minutos** | 15× |
| **Carbaril** | 125 días | **1 día** | 125× |
| **Malatión** | 8 días | **~19 horas** | ~10× |

**Vidas medias por tipo** **[MED]** — Purdue PPP-86. ⚠ **La publicación presenta estos valores con nombres genéricos ("Brand X"), no con principios activos identificados.** Se reproduce tal cual, con esa reserva declarada:

| Tipo de producto | pH 9 | pH 7 | pH 5 |
|---|---|---|---|
| "Brand X" Herbicida | **10 minutos** | 17 horas | 16 días |
| "Brand X" Fungicida | **2 minutos** | 3 horas | 10 horas |
| "Brand X" Insecticida | 24 horas | 10 días | Estable |

**Casos específicos** **[MED, verificación parcial]** — vía resumen de fuente Purdue:
- **Captan**: t½ **32 horas a pH 5**; **10 minutos a pH 8**.
- **Mancozeb**: t½ **20 días a pH 5**; **< 17 horas a pH 7**.

> **La cifra que hay que llevar a campo:** un fungicida en agua a pH 9 tiene **2 minutos de vida media**. El tiempo que el operario tarda en terminar de cargar el tanque **es más largo que la vida del producto**. No hay orden de mezcla que arregle eso — hay que corregir el pH **antes** (§4.4, posición 2).

**Efecto cuantitativo del pH** **[MED]**: la degradación *"increas[es] tenfold with every one unit of increase in pH"*. (Virginia Tech BSE-350P)

### 8.3 Temperatura sobre la estabilidad de emulsiones y la solubilidad

**[MED]** *"Liquid nitrogen fertilizers (28 %–32 % UAN) present challenges since they're **close to saturation already**, potentially hindering ingredient solubilization."* — https://www.exactoinc.com/blog/2021/11/09/pesticide-tank-mix-incompatibility/

Éste es el punto central del §8.3 y merece desarrollarse:

> **El UAN ya está cerca de la saturación a temperatura ambiente.** La disolución de la mayoría de las sales fertilizantes es **endotérmica** — al disolverse, **enfrían la solución**. Y la solubilidad **cae con la temperatura**. Es un lazo de realimentación positiva hacia el fallo:
>
> **más sal → solución más fría → menor solubilidad → cristaliza → menos volumen de solvente efectivo → más concentrado el resto.**
>
> Por eso el UAN frío es el peor caso del §8.1, y por eso **la "sal fuera" (*salting out*) de emulsiones EC en fertilizante líquido** es un modo de fallo específico: la altísima fuerza iónica del UAN desestabiliza la emulsión, expulsando la fase orgánica.
> El componente **[CALC]/[PRAC]** de este razonamiento (endotermicidad, realimentación) es deducción de este dossier; los valores de calor de disolución y las curvas de solubilidad vs. temperatura **no se pudieron verificar** — §10.

### 8.4 Estabilidad del caldo durante la jornada

**[MED, evidencia directa]** El antagonismo del calcio con glifosato **empeora con el tiempo en el tanque**: *"the reaction progresses to yield a more structured, chelate type complex **over time**"*. (Weed Science, §7.1) → **el caldo que espera pierde eficacia aunque se vea idéntico.**

**[MED, evidencia en contra para otro caso]** No es universal: un trabajo de Weed Technology encontró que el control de malezas con **2,4-D DMA** *"depends on mixture water hardness and adjuvant inclusion **but not spray solution storage time**"*. — https://www.cambridge.org/core/journals/weed-technology/article/abs/weed-control-by-24d-dimethylamine-depends-on-mixture-water-hardness-and-adjuvant-inclusion-but-not-spray-solution-storage-time/70A8F26EA62C96E9536941B55C8DCE21

> **Hallazgo honesto y útil: la evidencia sobre el tiempo en tanque va en direcciones opuestas según la molécula.** Para el glifosato, el tiempo empeora el antagonismo (mecanismo publicado). Para el 2,4-D DMA, el tiempo de almacenamiento **no** resultó significativo (ensayo publicado). **No se puede enunciar una regla general de "no dejar el caldo de un día para otro" apoyada en datos** — lo que sí se puede enunciar es que **el efecto es específico del activo y hay que verificarlo por producto.**

**[MED, indirecto]** La observación **"toda la noche"** de la prueba de jarra (§5.2) es la herramienta correcta para responder esta pregunta **en el caso físico** (separación, solidificación). Para el caso químico, la jarra no sirve (§5.3).

**[PRAC]** La recomendación general de la industria de no almacenar caldo preparado y de vaciar el tanque al final de la jornada **es práctica recomendada sin ensayo publicado general** que la sostenga transversalmente. Ver §10.

---

## 9. INCOMPATIBILIDADES FERTILIZANTE × AGROQUÍMICO

### 9.1 UAN + ATS (tiosulfato de amonio) — el caso mejor medido

**[MED]** Trabajo de **Mike Schryver (BASF Technical Service Specialist)**, difundido por **Jason Deveau (OMAFA Application Technology Specialist)**, Sprayers101, 14-04-2026 (trabajo de 2023). https://sprayers101.com/nitrogen_stabilizers/

**Método:** frascos de **300 mL** con **barra magnética de agitación**, simulando **10 galones/acre**; **UAN enfriado a ≈ −5 °C**; herbicidas al **2× de la dosis de etiqueta** (peor caso); productos introducidos a **intervalos de 1 minuto**; reposo **≥ 1 hora**; agitación y **vertido a través de tamiz de malla 100**.

**Resultados:**

| Relación **UAN : ATS** | Resultado |
|---|---|
| 3 : 1 | ensayada |
| **5 : 1** | **FALLA** |
| **8 : 1** | **PASA** |
| **Umbral estimado por los autores: ~7 : 1** | |

**Los dos hallazgos de orden — y son irreversibles** **[MED]**:
1. **El ATS debe agregarse DESPUÉS del herbicida (EC o SC).** Preferiblemente **último** en el tanque.
2. Si UAN y ATS se **premezclan antes** del herbicida, hay incompatibilidad **sin importar el estabilizante**: *"adding stabilizer will not reverse a tank mix error arising from adding ATS prior to the herbicide."*

**Resultado tranquilizador:** tanto herbicidas **EC como SC** resultaron compatibles con UAN + estabilizantes cuando se respetó el orden. Los componentes se separaron durante el reposo pero **se reintegraron con agitación y pasaron el tamiz**.

> **Este es el único caso de todo el dossier con umbral numérico medido, método declarado y criterio de fallo reproducible.** Úselo como modelo de lo que debería exigirse a cualquier afirmación de compatibilidad.

### 9.2 UAN / fertilizantes líquidos como vehículo con formulaciones EC

**[MED]** UAN 28–32 % está *"close to saturation already"*, lo que **dificulta la solubilización** de los demás ingredientes. (Exacto)

**[MED]** Cuando el vehículo es **aceite o fertilizante líquido**, la prueba de jarra cambia: se cargan **375 mL** en lugar de 250 mL en la jarra de 1 L (Sprayers101, §5.1) — reconocimiento explícito de que el vehículo fertilizante es un caso distinto.

**[MED]** Riesgo fitotóxico: *"Severe crop burn is possible with 32-0-0 applied by broadcast spray on growing crops."* (vía resumen, Mississippi State Extension / Fluid Fertilizers)

### 9.3 Glifosato + agua dura (Ca²⁺)

Tratado íntegramente en **§7.1**. Resumen del veredicto:

| | |
|---|---|
| **Qué pasa** | Ca²⁺ forma un complejo quelato con los grupos carboxilo y fosfonato del glifosato. **[MED]** |
| **Es visible en la jarra** | **NO.** El caldo queda limpio. **[MED]** |
| **Qué lo corrige** | **AMS 1–3 % w/v, agregado ANTES del glifosato.** Doble mecanismo (§7.1). **[MED]** |
| **Qué NO lo corrige** | AMS agregado **después** del herbicida. Más agitación. Aumentar la dosis de glifosato (compensa el síntoma, no el mecanismo, y es caro). **[MED/CALC]** |
| **Umbral** | < 350 ppm para dosis baja; < 700 ppm para dosis alta. **[MED]** |

### 9.4 2,4-D sal amina con cationes no-amina

**[MED]** *"2,4-D is a weak acid with a water-soluble amine formulation that is prone to dissociate and be antagonized by divalent cations when mixed in hard water, including calcium (Ca²⁺), magnesium (Mg²⁺), and iron (Fe²⁺, Fe³⁺)."*

**Química:** la formulación amina existe como **par iónico [2,4-D⁻][amina-H⁺]**. En presencia de cationes divalentes o trivalentes, el anión 2,4-D⁻ **cambia de contraión**: forma sales de Ca, Mg o Fe. Estas sales **se absorben mal** — y en el extremo pueden precipitar.

**Magnitud** **[MED]**: el **2,4-D puede quedar completamente desactivado a 500 ppm de dureza**. (Virginia Tech BSE-350P). **Es el activo más sensible a la dureza de los documentados en este dossier.**

**Corrección** **[MED]**: **AMS a 20 g/L (2 % w/v)** revierte el antagonismo de agua dura del 2,4-D DMA.

> ### ⚠ LA TRAMPA — la corrección crea un problema nuevo
>
> **[MED]** *"Where ammonium sulfate is present in the tank-mix composition to counteract effects of hard water, compatibility of a glyphosate potassium salt formulation and a 2,4-D dimethylammonium salt formulation can be **further compromised**, especially at **low spray volumes** and/or relatively **high 2,4-D rates**."*
>
> Es decir: la mezcla **glifosato-K + 2,4-D DMA + AMS** — que es exactamente la mezcla de barbecho más común del Cono Sur — tiene una **incompatibilidad física propia** que **el AMS agrava**, y que empeora justamente en las condiciones de aplicación moderna (**bajo volumen de caldo**).
>
> Por el §5.2, bajar de 200 a 50 L/ha **cuadruplica todas las concentraciones** y **multiplica por 16 el producto iónico**. La tendencia a bajar volumen de caldo está empujando esta mezcla hacia su límite de compatibilidad.
>
> **Recomendación [PRAC]: esta mezcla específica exige prueba de jarra al volumen de caldo real, cada vez que se baje el volumen.**

**Referencias adicionales localizadas** **[MED, referencia]**:
- *Mixing the correct nitrogen source and rate with 2,4-D increases efficacy in hard and soft water*, **Crop Protection**, https://www.sciencedirect.com/science/article/abs/pii/S0261219421002283
- *Tank-mixing 2,4-D amine and sulfosulfuron can help alleviate the adverse effects of water hardness on controlling flixweed*, **Crop Protection**, https://www.sciencedirect.com/science/article/abs/pii/S0261219423002004
- *Weed control by 2,4-D dimethylamine depends on mixture water hardness and adjuvant inclusion but not spray solution storage time*, **Weed Technology**, https://www.cambridge.org/core/journals/weed-technology/article/abs/weed-control-by-24d-dimethylamine-depends-on-mixture-water-hardness-and-adjuvant-inclusion-but-not-spray-solution-storage-time/70A8F26EA62C96E9536941B55C8DCE21

### 9.5 Fertilizantes con azufre y aceites

**[MED, parcial]** Lo verificado sobre azufre en mezcla: la incompatibilidad **ATS × UAN** con el umbral 7:1 (§9.1) y la regla de orden (ATS después del herbicida).

**[NV]** La incompatibilidad clásica **azufre elemental / polisulfuro de calcio × aceites**, con su intervalo de seguridad en días entre aplicaciones, **no se pudo verificar** en esta sesión (presupuesto de búsqueda agotado antes de alcanzar las guías de fruticultura). Es una incompatibilidad **fitotóxica** bien establecida en el manejo de frutales, pero **no se cita un intervalo sin fuente**. Ver §10.

### 9.6 Calcio foliar + fosfitos / sulfatos

**[CALC]** Predicción directa del §2: un fertilizante foliar de **nitrato de calcio o cloruro de calcio** mezclado con un producto **fosfitado o sulfatado** reproduce exactamente los pares de §2.1 y §2.2, **a la concentración de caldo foliar** — que es mucho más alta que la de fertirriego. Con Ca a nivel de caldo foliar, el par Ca/P está sobresaturado en todo el rango de pH útil.

**[NV]** No se recuperaron ensayos publicados específicos de esta mezcla. La predicción termodinámica es sólida; **la confirmación experimental falta**. Ver §10.

### 9.7 Micronutrientes foliares + glifosato

**[NV]** El antagonismo de **Mn, Zn, Fe y Cu** sobre el glifosato es un caso ampliamente discutido en la literatura de malezas. El **mecanismo es idéntico al del calcio** (§7.1): cationes divalentes que forman sales de glifosato poco absorbibles — y de hecho la fuente de Weed Science menciona que los cationes problemáticos incluyen **aluminio, hierro, magnesio y calcio** **[MED]**.

Sin embargo, **los ensayos cuantitativos específicos con Mn y Zn (p. ej. el trabajo de Bernards et al. en Weed Science) no se pudieron recuperar** en esta sesión. Ver §10.

**[CALC/PRAC]** Predicción defendible desde el mecanismo verificado: **cualquier micronutriente catiónico agregado al mismo caldo que el glifosato es un antagonista potencial, y el AMS es la mitigación de primera línea por el mismo mecanismo de competencia por el sitio.** Esto es **extrapolación mecanística, no un resultado medido** — y así debe declararse ante un cliente.

---

## 10. TABLA "NO VERIFICADO"

Todo lo siguiente es **conocido o probable pero SIN fuente primaria recuperada en esta sesión**. **No se usó para sostener ninguna conclusión operativa de este dossier.**

| # | Afirmación pendiente | Sección | Por qué no se verificó | Cómo cerrarla |
|---|---|---|---|---|
| 1 | **Fuerza iónica** de los Ksp de las dos compilaciones usadas | §1.2 | Ninguna de las dos páginas la declara | Consultar la base WATEQ4F original y Sillén & Martell (1964) en papel |
| 2 | Solubilidad **medida** del yeso (≈ 2,0–2,5 g/L a 25 °C) y la contribución del par iónico CaSO₄°(aq) | §1.3, §2.1 | No se recuperó tabla primaria | Manual de química física / base PHREEQC |
| 3 | **Ley de velocidad de oxidación de Fe²⁺** (dependencia con [OH⁻]²) | §3.3(b) | Presupuesto agotado | Stumm & Morgan, *Aquatic Chemistry*; Singer & Stumm (1970) *Science* |
| 4 | **Constantes de estabilidad y rangos de pH** de EDTA, DTPA, EDDHA, EDDHSA, HEDTA; por qué falla Fe-EDTA sobre pH 6,5 | §3.5 | Presupuesto agotado | Norvell (1991) en *Micronutrients in Agriculture* (SSSA); trabajos de J.J. Lucena en *J. Plant Nutrition* |
| 5 | **Pasos 1 a 9** del orden de mezcla Embrapa Documentos 437 | §4.3 | Texto del PDF no extraíble en este entorno | Descargar el PDF y leerlo con un extractor de texto |
| 6 | Texto completo de **UF/IFAS PI301**, **Montana State**, **UADA FSA-2166**, **UGA Tank Mixing** | §5.1 | Dominios bloqueados o PDF no extraíble | Reintentar fetch / OCR |
| 7 | **pH y ley de velocidad de hidrólisis del APP** a ortofosfato (t½ vs. pH y T) | §6.5 | Presupuesto agotado | *European Polymer Journal* (2025) revisión APP, texto completo |
| 8 | **Autores, año y DOI** de *The Basis for the Hard-Water Antagonism of Glyphosate Activity* (Weed Science) | §7.1 | Fetch de Cambridge falló (ECONNRESET) | Reintentar Cambridge Core o Crossref |
| 9 | **Autores** de *Spray water quality and herbicide performance: a review* (el DOI 10.1017/wet.2022.97 y las páginas 758–767 **sí** están verificados) | §3.4, §7.4 | Fetch falló | Crossref por DOI |
| 10 | **Calores de disolución y curvas de solubilidad vs. temperatura** de KNO₃, urea, NH₄NO₃, KCl | §8.3 | Presupuesto agotado | Manual de química / literatura de fertilizantes |
| 11 | **Temperatura mínima de agua** recomendada por fabricantes para mezclar WG/WP/SG | §8.1 | Presupuesto agotado | Etiquetas y hojas técnicas de fabricantes |
| 12 | Intervalo de seguridad **azufre elemental / polisulfuro de calcio × aceites** (días entre aplicaciones) | §9.5 | Presupuesto agotado | Guías de pulverización de frutales (Penn State, Michigan State, Cornell) |
| 13 | Ensayos publicados de **Ca foliar × fosfito / sulfato** | §9.6 | No localizados | Búsqueda dirigida en literatura de nutrición foliar |
| 14 | Ensayos cuantitativos de **antagonismo Mn/Zn × glifosato** (Bernards et al. y afines) | §9.7 | Presupuesto agotado | Weed Science / Weed Technology vía Crossref |
| 15 | Regla general **"no almacenar caldo de un día para otro"** con ensayo publicado transversal | §8.4 | No existe evidencia general recuperada; la existente es contradictoria por molécula | Revisión sistemática por activo |
| 16 | Vidas medias de **captan** y **mancozeb** (fuente Purdue vía resumen secundario, no del documento primario) | §8.2 | Fetch parcial | Purdue *Facts for Fancy Fruit* / PPP-86 texto completo |

---

## 11. LO QUE NO SE PUEDE

> Esta sección es el contrapeso del dossier. Todo lo anterior describe problemas que **tienen** solución. Aquí están los que **no la tienen** — y confundirlos es el error más caro, porque lleva a gastar en adyuvantes que no pueden funcionar y a culpar al producto de un fallo del agua.

### 11.1 Ningún adyuvante ni orden de mezcla arregla esto

#### ① Agua turbia / arcillosa el día de la aplicación
El activo **ya está adsorbido** a la arcilla. La adsorción de glifosato, paraquat, diquat y nicosulfurón a montmorillonita y caolinita es **rápida y de alta afinidad** **[MED]**. Ni el surfactante, ni el AMS, ni la agitación lo despegan.
- La corrección existe — sulfato de aluminio 10–60 mg/L — pero **tarda 24–48 horas** **[MED]**.
- **No es una corrección de tanque. Es una corrección de reservorio.** Si el agua está turbia esta mañana, **hoy no se aplica** con esos activos. No hay atajo.

#### ② Incompatibilidad química real (exotermia)
Si la jarra **libera calor**, hay una reacción química en curso: el activo **se está destruyendo o transformando**. Un agente de compatibilidad es un **tensioactivo o dispersante** — actúa sobre la estabilidad **física** de la suspensión. **No tiene ningún mecanismo por el cual detener una reacción química.** Confirmado **[MED]**: los agentes de compatibilidad *"cannot resolve all compatibility problems"*.

#### ③ Un error de orden de carga, una vez cometido
**[MED, probado experimentalmente]** *"adding stabilizer will not reverse a tank mix error arising from adding ATS prior to the herbicide."*
El orden de carga es **irreversible**. Un producto agregado en el momento equivocado no se "des-agrega". La única corrección es **vaciar, limpiar y volver a cargar**.

#### ④ Sobresaturación en solución madre
**[CALC]** Un SI de **+3,33** (§2.1) significa **2 133 veces por encima del equilibrio**. Ninguna agitación disuelve eso — la agitación **resuspende**, no disuelve. Ningún secuestrante alcanza a esa escala: el polifosfato llega a **2 % de Zn** (§6.3), no a tres órdenes de magnitud de Ca.
**La única solución es la separación A/B, y por eso no es opcional.**

#### ⑤ Antagonismo de absorción — el fallo invisible
La sal Ca-glifosato **es soluble**. El caldo se ve **perfecto**. **La jarra la aprueba.** Y el activo **no entra en la planta** **[MED]**.
Corregible **sólo preventivamente** con AMS **antes** del herbicida. Una vez formado el complejo quelato — y **empeora con el tiempo en el tanque** **[MED]** — no hay recuperación en el tanque. **Un caldo que se ve bien no es evidencia de nada.**

#### ⑥ Hidrólisis alcalina ya consumada
Un fungicida en agua a pH 9 tiene **2 minutos de vida media** **[MED]**. Para cuando el operario termina de cargar, el producto ya no está. **Acidificar después no re-sintetiza la molécula.** El buffer va **antes** (§4.4, posición 2) o no sirve.

#### ⑦ Fe³⁺ no quelatado por encima de pH 3
**[CALC]** Precipita a **pH 2,5–3,2**. No existe caldo agronómico viable a ese pH. **Ningún adyuvante, orden ni acidificante compatible con el cultivo lo mantiene en solución.** La única vía es **quelatar** — es decir, cambiar de producto, no de manejo.

#### ⑧ Ca + P en solución madre
**[CALC]** SI > +4 en toda la ventana de pH. **No hay pH que lo salve** a concentración de madre. En caldo diluido sí se salva con pH ≤ 6,0 — en madre, no.

#### ⑨ El vencimiento del propio secuestrante
**[MED]** El Zn²⁺, Fe²⁺ y Al³⁺ que el APP protege son **los mismos cationes que catalizan la escisión de su cadena**. La protección **se autodestruye, y más rápido cuanto mayor la carga**. No es un problema de manejo: es una propiedad de la molécula. Un APP con micros cargados **no es almacenable indefinidamente.**

### 11.2 Lo que ninguna prueba de jarra puede decirle

Repetido aquí porque es la limitación más ignorada del dossier (§5.3):

**La prueba de jarra sólo detecta incompatibilidad FÍSICA.** No ve hidrólisis alcalina, no ve antagonismo de absorción, no ve adsorción a arcilla, no ve fitotoxicidad, no ve degradación lenta durante la jornada.

> **Pasar la jarra es condición necesaria y no suficiente.** Presentarla al cliente como certificado de compatibilidad es un error de método. Descarta **un** modo de fallo de **seis**.

### 11.3 Lo que este dossier no puede decirle

Honestidad sobre el propio alcance:

1. **Los umbrales de pH del §3.2 son de diseño, no constantes.** Incertidumbre real: **±0,5 unidades** (±0,3 por elección de tabla de Ksp + 0,26–0,35 por fuerza iónica + fase amorfa/cristalina).
2. **Las escalas de dureza publicadas difieren por un factor de 2,7** (§7.1). Nunca transfiera un umbral sin su escala.
3. **La respuesta al bicarbonato es específica de la molécula, no del grupo** — cletodim y sethoxydim, ambos Grupo 1, difieren por un factor de 2 en tolerancia (§7.2).
4. **Buena parte del corpus de orden de mezcla es [PRAC], no [MED].** Funciona, es criterio acumulado de la industria, y **no está publicado como ensayo**. La excepción notable es el caso ATS/UAN (§9.1), que sí tiene método y umbral medidos — y que debería ser el estándar exigido al resto.
5. **Quedan 16 ítems sin verificar** (§10). Los más importantes: los **quelatos** (§3.5, ítem 4) — que es justamente lo que resuelve el problema del Fe³⁺ — y el **pH de hidrólisis del APP** (ítem 7).

---

## 12. BIBLIOGRAFÍA

### 12.1 Literatura revisada por pares

| Referencia | Identificador | Estado |
|---|---|---|
| *Spray water quality and herbicide performance: a review*. **Weed Technology 36(6):758–767 (2022)** | **DOI 10.1017/wet.2022.97** | DOI, volumen y páginas **verificados**; **autores NO verificados** |
| Mirzaei et al. (2023). *Effects and mitigation of poor water quality on herbicide performance: A review*. **Weed Research** | **DOI 10.1111/wre.12573** | DOI **verificado** |
| *The Basis for the Hard-Water Antagonism of Glyphosate Activity*. **Weed Science** | Cambridge Core ID `1B115821F1CAFEB89F926BBB1CE66810` | **Autores/año/DOI NO verificados** |
| *Weed control by 2,4-D dimethylamine depends on mixture water hardness and adjuvant inclusion but not spray solution storage time*. **Weed Technology** | Cambridge ID `70A8F26EA62C96E9536941B55C8DCE21` | Referencia localizada |
| *Glyphosate Response to Calcium, Ethoxylated Amine Surfactant, and Ammonium Sulfate*. **Weed Technology** | Cambridge ID `D8373D100EFAECF1CAEF880C63C6850C` | Referencia localizada |
| *Mixing the correct nitrogen source and rate with 2,4-D increases efficacy in hard and soft water*. **Crop Protection** | `S0261219421002283` | Referencia localizada |
| *Tank-mixing 2,4-D amine and sulfosulfuron... water hardness... flixweed*. **Crop Protection** | `S0261219423002004` | Referencia localizada |
| Bhuiyan et al. *Exploring the determination of struvite solubility product from analytical results* | **PMID 17067121** | **Verificado** |
| *Temperature impact assessment on struvite solubility product: a thermodynamic modeling approach*. **Chemical Engineering Journal** | `S1385894710012027` | **Verificado** |
| *Octacalcium Phosphate Solubility Product from 4 to 37 °C* | **PMC5178315** | **Verificado** |
| *Hydrolysis Mechanism of Water-Soluble Ammonium Polyphosphate Affected by Zinc Ions* | **PMC10210202** | **Verificado** |
| *Ammonium polyphosphates: correlating structure to application*. **European Polymer Journal (2025)** | Hansen-Bruhn & Hull | Referencia localizada |
| *Adsorption of glyphosate by soils and clay minerals*. **J. Agric. Food Chem.** | `10.1021/jf00076a013` | **Verificado** |
| *Montmorillonites Can Tightly Bind Glyphosate and Paraquat* | **PMC6822125** | **Verificado** |

### 12.2 Publicaciones institucionales

| Publicación | Institución | URL |
|---|---|---|
| **PPP-86** — *The Impact of Water Quality on Pesticide Performance*. Whitford, F. (coord.), Penner, D., Johnson, B., Bledsoe, L., Wagoner, N., Garr, J., Wise, K., Obermeyer, J., Blessing, A. | **Purdue Pesticide Programs** | https://ag.purdue.edu/department/extension/ppp/resources/ppp-publications/mobile/ppp-86/the-impact-of-water-quality-on-pesticide-performance.html |
| **BSE-350P** — Ling, E., Parson, R., Frank, D., Mohamed, D., Kline, K., Spiller, A. & Horn, D. (2024). *Spray water quality and pesticide characteristics* | **Virginia Cooperative Extension** | https://www.pubs.ext.vt.edu/BSE/bse-350/bse-350.html |
| **G2350** (2023) — *Testing Pesticide Mixtures for Compatibility* | **University of Nebraska-Lincoln Extension** | https://extensionpubs.unl.edu/publication/g2350/2023/pdf/view/g2350-2023.pdf |
| **Documentos 437** (2021) — *Manual técnico para subsidiar a mistura em tanque de agrotóxicos e afins* | **Embrapa Soja** + UENP + Bayer CropScience | https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1132371/1/DOCUMENTOS-437-1.pdf |
| *Water Quality and Herbicides* | **Saskatchewan Agriculture** | https://www.saskatchewan.ca/business/agriculture-natural-resources-and-industry/agribusiness-farmers-and-ranchers/crops-and-irrigation/weeds/water-quality-and-herbicides |
| **PI301** — *Ensuring Pesticide Compatibility in Tank Mixes* | **UF/IFAS EDIS** | https://edis.ifas.ufl.edu/publication/PI301 |
| **FSA-2166** — *Assessing Pesticide-Fertilizer Compatibility (Jar Test)* | **University of Arkansas Division of Agriculture** | https://www.uaex.uada.edu/publications/PDF/FSA-2166.pdf |
| *Compatibility Test for Pesticide Mixtures* | **Montana State University PSEP** | https://www.montana.edu/extension/pesticides/reference/compatibility.html |
| *Fertilizer Compatibility* | **Purdue Vegetable Crops Hotline** | https://vegcropshotline.org/article/fertilizer-compatibility/ |
| *Tank Mixing* | **University of Georgia Turf** | https://turf.caes.uga.edu/content/dam/caes-subsite/georgiaturf/docs/pcrp2020/Tank_Mixing.pdf |

### 12.3 Fuentes técnicas de industria y divulgación especializada

| Fuente | Autor / Institución | URL |
|---|---|---|
| *Sprayer Loading and the Jar Test* | **Sprayers101** | https://sprayers101.com/loading-jartest/ |
| *Water Quality and Spray Application* — Tom Wolf, 09-04-2026 | **Sprayers101** | https://sprayers101.com/water-quality/ |
| *The Real Story behind pH and Water Hardness* — Andrew Storrie, 28-07-2026 | **Sprayers101** | https://sprayers101.com/ph-hardness/ |
| *Tank mixing Urease and Nitrification Inhibitors* — Jason Deveau (**OMAFA**), sobre trabajo de Mike Schryver (**BASF**), 14-04-2026 | **Sprayers101** | https://sprayers101.com/nitrogen_stabilizers/ |
| *Pesticide Tank Mix Incompatibility* (WAMLEGS) | **Exacto Inc.** | https://www.exactoinc.com/blog/2021/11/09/pesticide-tank-mix-incompatibility/ |
| *Herbicide Mixing Order Matters* | **Grainews** | https://www.grainews.ca/crops/good-to-be-mixed-up-in-the-right-order/ |
| *Everything in Order* | **FMC Ag Canada** | https://ag.fmc.com/ca/en/fmc-news/everything-order-tips-mixing-herbicides-right-order |
| *Tank Mixing 101* | **Corteva Agriscience** | https://www.corteva.com/ca-en/resources/agronomy-hub/tank-mixing-101-principles-optimal-application.html |
| *Mastering Tank Mixes* · *Interaction among Fertilizers* | **Haifa Group** | https://www.haifa-group.com/haifa-blog/mastering-tank-mixes |
| *Fertilizer Compatibility Chart Guide* | **Cropaia** | https://cropaia.com/blog/fertilizer-compatibility-chart-guide/ |
| *Correct Fertigation Regimes* | **Rivulis Knowledge Hub** | https://www.rivulis.com/knowledge-hub/maintenance/number-7-correct-fertigation-regimes/some-specific-considerations-to-keep-in-mind/ |
| *Phosphorus Fertilizer Forms: Ortho-P or Poly-P* | **Agvise Laboratories** | https://www.agvise.com/phosphorus-fertilizer-forms-orthophosphate-or-polyphosphate-ortho-p-or-poly-p/ |
| *Polyphosphate* | **Mosaic Crop Nutrition** | https://www.cropnutrition.com/resource-library/polyphosphate/ |

### 12.4 Datos termodinámicos

| Fuente | Contenido | URL |
|---|---|---|
| **aqion** — bases PHREEQC: WATEQ4F, MINTEQ, LLNL | pKsp a 25 °C (Fuente A del §1.2) | https://www.aqion.de/site/16 |
| **Lange's Handbook of Chemistry**, pp. 8-6 a 8-11 · **Sillén, L.G. & Martell, A.E. (1964)**, *Stability Constants of Metal-Ion Complexes*, The Chemical Society, London, Special Publ. No. 17 | Ksp a 25 °C (Fuente B del §1.2) | https://www.wiredchemist.com/chemistry/data/solubility-product-constants |

---

## APÉNDICE A — TARJETA DE CAMPO

> Una página. Para el que carga el tanque.

**ANTES DE CARGAR**
1. ¿Análisis del agua? → **dureza, bicarbonatos, pH, turbidez**
2. ¿Se ve una moneda en el fondo de un balde de 19 L? Si **no** → **no aplique hoy** con glifosato/paraquat/diquat/nicosulfurón. La corrección tarda 24–48 h.
3. ¿Dureza > 350 ppm? → **AMS 1–3 % w/v, PRIMERO, antes que nada.**
4. ¿pH > 7? → **buffer, ANTES de los activos.** Excepción: **sulfonilureas quieren pH 7–8.**

**ORDEN DE CARGA — WAMLEGS**
```
0.  Tanque a MEDIA carga + agitación en marcha
0.5 ACONDICIONADORES DE AGUA (AMS)      ← siempre primero
1.  W  Sólidos: WSB, WP, WDG, SG        ← esperar 3–5 min cada uno
2.  A  Buffers, antiespumantes
3.  M  Microcápsulas (CS)
4.  L  Líquidos: SC, SL
5.  E  Emulsionables: EC, OD
6.  G  Glifosato de alta carga
7.  S  Surfactantes
8.  FERTILIZANTES FOLIARES / MICROS     ← ATS va AQUÍ, nunca antes
9.  Antideriva
10. Completar agua
```
> ⚠ **El orden es IRREVERSIBLE. Un error no se corrige agitando ni agregando adyuvante.**

**PRUEBA DE JARRA — 500 mL**
1. **250 mL** de agua **del pozo real** (375 mL si el vehículo es aceite/fertilizante)
2. Productos en **el mismo orden del tanque**, a la **dilución REAL del caldo** (×0,001 si la jarra representa 500 L)
3. **3–5 min** entre sólidos
4. Completar a 500 mL, invertir 10×
5. Reposo: **15 min** → **1 h** → **toda la noche**
6. **Agitar y pasar por tamiz malla 100**

**REPRUEBA SI:** precipita · flocula · se separa · gelifica · **se calienta** · hace nata
**REPRUEBA SI:** sedimenta y **NO reintegra** al agitar
**PASA SI:** sedimenta y **reintegra completo** + pasa el tamiz

> ⚠ **Pasar la jarra NO garantiza que funcione.** La jarra no ve hidrólisis, ni antagonismo de absorción, ni arcilla, ni fitotoxicidad.

**FERTIRRIEGO — REGLA A/B**
```
TANQUE A: Calcio + nitratos + quelatos de Fe
TANQUE B: Fosfatos + sulfatos + micros sulfato
                 NUNCA se tocan concentrados.
```
> **Por qué:** en madre a 100× el par Ca/SO₄ está **2 133 veces sobresaturado.** En el gotero, no. **A/B no separa productos: separa concentraciones.**

**pH DEL CALDO — VENTANA 5,0 – 6,5**
| Si el caldo lleva… | pH máximo |
|---|---|
| Ca + P | **≤ 6,0** |
| Cu no quelatado (foliar) | **≤ 6,0** |
| Mg + amonio + P | **≤ 7,5** |
| **Sulfonilureas** | **7 – 8 (al revés)** |

> **Mida el pH del CALDO TERMINADO, no del agua.** El glifosato baja el tanque de 8 a menos de 4.

---

*Fin del dossier R3.*
*16 afirmaciones pendientes de verificación catalogadas en §10. Ninguna sostiene una conclusión operativa.*
