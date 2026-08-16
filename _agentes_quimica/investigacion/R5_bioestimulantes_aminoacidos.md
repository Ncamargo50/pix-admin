# R5 — Bioestimulantes: aminoácidos y sustancias orgánicas

**Dossier de investigación verificado**
Fecha: 2026-08-16 · Autor: agente de investigación química (Pixadvisor)
Alcance: hidrolizados proteicos, moléculas bioactivas individuales, extractos de algas, sustancias húmicas, aminoquelatos, quitosano y silicio. Marco regulatorio y tamaño de efecto real.

---

## 0. Cómo leer este dossier

Este es el rubro más contaminado de marketing del negocio de insumos. El valor de este documento no está en listar productos: está en **separar lo que tiene evidencia de lo que no**, y en dejar por escrito qué NO se pudo verificar.

### 0.1 Niveles de evidencia usados

| Nivel | Etiqueta | Qué significa |
|---|---|---|
| **A** | Meta-análisis / revisión sistemática | Síntesis cuantitativa de múltiples ensayos, con IC y heterogeneidad reportadas |
| **B** | Ensayo de CAMPO con repeticiones y testigo | Parcelas replicadas, testigo sin tratar, análisis estadístico, condiciones productivas reales |
| **C** | Ensayo en MACETA / cámara / hidroponía / laboratorio | Mecanismo demostrado, pero NO transferible directamente a dosis y condiciones de campo |
| **D** | Mecanismo bioquímico documentado sin ensayo agronómico | Se conoce la ruta; no se demostró efecto en rendimiento |
| **E** | Afirmación de folleto comercial sin ensayo publicado | No es evidencia. Se cita solo para nombrarla y marcarla |

### 0.2 Regla de oro aplicada

Todo DOI que aparece en este documento fue **resuelto contra Crossref** (`api.crossref.org`) durante la elaboración, salvo los explícitamente marcados. Lo que no se pudo verificar está en la **§9 — TABLA NO VERIFICADO**, con constancia de qué se buscó. No hay DOIs inventados, ni tamaños de efecto inventados, ni constantes de estabilidad inventadas.

> **Advertencia de sesión.** La elaboración de este dossier agotó el presupuesto de búsqueda web (200/200) y sufrió fallas de red repetidas (`ECONNRESET`, `socket hang up`, bloqueo de verificación de dominio) contra MDPI, ScienceDirect, Tandfonline, PMC, Wikipedia y parte de Frontiers. Además, dos de las tres investigaciones paralelas planificadas **no pudieron ejecutarse** por límite de concurrencia de agentes, y la tercera no devolvió resultados antes del cierre. Varios ítems quedaron sin verificar **por esas razones, no porque no existan**. Están todos en §9.
>
> **Las tres lagunas materiales del documento, en orden de gravedad:**
>
> 1. **§5 — constantes de estabilidad de aminoquelatos (NV-23).** No se verificó **ningún** valor de log K. La sección se escribió **deliberadamente sin tabla de constantes**. Es la laguna más grave.
> 2. **§7 — marco regulatorio completo (NV-26 a NV-30).** Estructura correcta, **cero citas verificadas contra fuente oficial**.
> 3. **§4.3 — magnitud numérica de la divergencia entre métodos analíticos de ácidos húmicos (NV-16).** El argumento cualitativo se sostiene; **el número no está**.
>
> El resto del documento — §1 a §4, §6, §8 y §10 — está sostenido por **25 referencias con DOI resuelto contra Crossref**.

---

## 1. Hidrolizados proteicos: cómo se hacen y por qué importa

La etiqueta dice "aminoácidos libres 10%". El proceso de fabricación decide si eso vale algo o no. Es la parte del rubro donde el proceso importa **más** que el número de la etiqueta.

### 1.1 Las tres vías de hidrólisis

| | **Ácida (química)** | **Enzimática** | **Alcalina** |
|---|---|---|---|
| Reactivo | HCl o H₂SO₄ concentrado | Proteasas (vegetales, microbianas, animales) | NaOH / Ba(OH)₂ / KOH |
| Temperatura | **> 121 °C** | **< 60 °C** | Alta |
| Presión | **> 220,6 kPa** | Atmosférica | Variable |
| Racemización L→D | **Sí, extensa** | **Nula** | **Sí, extensa** |
| Aminoácidos destruidos | **Trp (total), Cys, Ser, Thr (parcial o total)** | Ninguno | Cys, Ser, Thr, Arg |
| Producto | Predominan aminoácidos libres | Mayor relación **péptidos : aminoácidos libres** | Mezcla degradada |
| Sal residual | Alta (neutralización → NaCl / Na₂SO₄) | Baja | Alta |
| Costo | Bajo | Alto | Bajo |

**Fuente primaria:** Colla, Hoagland, Ruzzi, Cardarelli, Bonini, Canaguier & Rouphael (2017), *Biostimulant Action of Protein Hydrolysates: Unraveling Their Effects on Plant Physiology and Microbiome*, **Frontiers in Plant Science 8: 2202**. DOI **10.3389/fpls.2017.02202** ✅ verificado. *Nivel A (revisión).*

De esa revisión, textualmente el punto que la etiqueta no dice: los hidrolizados de **origen animal** se producen habitualmente por hidrólisis química con ácidos a >121 °C y >220,6 kPa; durante ese proceso **Trp, Cys, Ser y Thr se destruyen parcial o totalmente y muchos aminoácidos pasan de forma L a forma D, perdiendo actividad biológica**. Los de **origen vegetal** se producen por hidrólisis enzimática a <60 °C, lo que da mayor relación péptidos:aminoácidos libres y mayor proporción de **L**-aminoácidos.

**Ensayo de referencia (nivel B/C):** Colla, Rouphael, Canaguier, Svecova & Cardarelli (2014), *Biostimulant action of a plant-derived protein hydrolysate produced through enzymatic hydrolysis*, **Frontiers in Plant Science 5**. DOI **10.3389/fpls.2014.00448** ✅ verificado.

> **🔎 Pista a seguir — un riesgo del que nadie habla.** Existe un trabajo dedicado a las **propiedades FOTOSENSIBILIZANTES de los fertilizantes basados en hidrolizados proteicos**: Cavani, L. et al. (2006), *Photosensitizing Properties of Protein Hydrolysate-Based Fertilizers*, **Journal of Agricultural and Food Chemistry 54: 9160–9167**, DOI **10.1021/jf0624953** — ✅ existencia verificada vía Crossref, **contenido NO leído en esta sesión**. Si el hallazgo es el que el título sugiere, implica un **riesgo de fitotoxicidad foliar por interacción con la radiación solar** que condicionaría el horario de aplicación. **Leer antes de recomendar aplicación foliar de hidrolizados a pleno sol.** → §9, NV-31.

### 1.2 Por qué la forma L y no la D

Los aminoácidos proteinogénicos son **L** (configuración S, salvo cisteína por prioridad CIP). Toda la maquinaria enzimática vegetal — aminoacil-tRNA sintetasas, transaminasas, transportadores LHT/AAP de membrana — es **estereoespecífica para L**.

Consecuencia práctica en tres niveles:

1. **La forma D no entra por la misma puerta o entra peor.** Los transportadores de aminoácidos de la membrana plasmática vegetal fueron caracterizados sobre sustratos L.
2. **La forma D no se incorpora a proteína.** No hay ruta canónica de incorporación de D-aminoácidos al ribosoma vegetal.
3. **La forma D puede ser antagonista.** Compite por el sitio del transportador sin producir el efecto, es decir, actúa como inhibidor competitivo del ingreso del L homólogo.

> ⚠️ El punto 3 es el más citado por el marketing del hidrolizado enzimático y es **el que peor documentado está con números**. La afirmación de que la D es "inerte" está bien sostenida; la de que es **activamente antagonista y en qué magnitud** quedó **NO VERIFICADA** en esta sesión (ver §9, ítem NV-02).

**Un problema analítico real que casi nadie menciona:** medir la relación D/L de un producto es difícil porque **el propio análisis racemiza**. La hidrólisis ácida necesaria para liberar los aminoácidos del péptido genera D adicional. El método correcto usa **hidrólisis en ácido deuterado (DCl/D₂O) + LC-MS/MS**: los D generados durante el análisis quedan marcados con deuterio y se pueden **restar** de los D nativos. Fuente: Danielsen, M. et al. (2020), *Simultaneous Determination of L- and D-Amino Acids in Proteins: A Sensitive Method Using Hydrolysis in Deuterated Acid and Liquid Chromatography–Tandem Mass Spectrometry Analysis*, **Foods 9: 309**, DOI **10.3390/foods9030309** ✅ verificado vía Crossref. *Nivel D (método analítico).*

**Consecuencia para el comprador:** un certificado de D/L que **no declare corrección por racemización inducida durante el análisis** está midiendo, en parte, su propio artefacto. Preguntar por el método es tan importante como pedir el número.

**Implicancia comercial:** si un proveedor declara "100% L-aminoácidos" sin especificar el método, y el producto es de hidrólisis ácida, la declaración es **improbable por construcción del proceso**. Pedir el cromatograma quiral y el método.

### 1.3 Aminoácidos LIBRES vs TOTALES: la diferencia que la etiqueta esconde

Esta es la asimetría de información más rentable del rubro.

| | **Aminoácidos libres** | **Aminoácidos totales** |
|---|---|---|
| Qué es | Moléculas monoméricas, ya disponibles | Libres **+** los que están todavía unidos en péptidos y proteínas |
| Cómo se mide | Analizador de aminoácidos **sin** paso de hidrólisis | Analizador **con** hidrólisis ácida previa |
| Método de referencia | **AOAC 994.12** aplicado **omitiendo la hidrólisis** | **AOAC 994.12** / **AOAC 985.28** (hidrólisis ácida + intercambio iónico + derivatización post-columna con **ninhidrina**) |
| Método moderno | — | **AOAC Final Action 2018.06** — aminoácidos totales por UHPLC-UV, con validación interlaboratorio |
| Valor típico en etiqueta | El número chico | El número grande |

Referencia del método moderno: *Determination of Total Amino Acids in Infant Formulas, Adult Nutritionals, Dairy, and Cereal Matrixes by UHPLC–UV: Interlaboratory Validation Study, Final Action 2018.06*, **Journal of AOAC International 105(6): 1625**. *Nivel D (norma analítica).* DOI no verificado en esta sesión → §9, NV-04.

**La maniobra:** un producto de hidrólisis parcial puede declarar "**aminoácidos totales 40%**" cuando sus **libres** son 5%. El comprador lee 40 y compara contra un producto enzimático que declara honestamente "libres 12%". El segundo es mejor producto y parece peor.

**Criterio de compra operativo — pedir SIEMPRE las dos cifras en el mismo certificado:**

- Si **totales ≈ libres** → hidrólisis completa. El producto es lo que dice.
- Si **totales >> libres** → hay péptidos sin hidrolizar. No es necesariamente malo (hay evidencia de que ciertos péptidos cortos son la fracción bioactiva), pero **no es lo que la etiqueta de "aminoácidos" insinúa**, y el precio por kg de libre real es otro.
- Corolario documentado: si totales son significativamente mayores que libres, la muestra contiene **péptidos no hidrolizados de peso molecular < 3000 Da**.

**Tercera cifra que hay que pedir: cloruros y sodio.** La hidrólisis con HCl se neutraliza con NaOH → el producto arrastra **NaCl**. Un hidrolizado ácido barato puede llevar una fracción importante de su peso en sal, con el riesgo fitotóxico foliar que eso implica. Un certificado de análisis serio de un hidrolizado incluye: libres, totales, N total, N orgánico, **cloruros**, sodio, metales pesados, y para origen animal, **cromo**.

### 1.4 Origen de la materia prima

| Origen | Materias primas | Perfil de aminoácidos | Costo relativo | Riesgo específico |
|---|---|---|---|---|
| **Animal — colágeno** | Cuero (*chrome shavings*), gelatina, descarne | Dominado por **Gly, Pro, Hyp (hidroxiprolina)**. Muy desbalanceado. Pobre en aromáticos y azufrados | **Muy bajo** | **CROMO** (§1.5); hidroxiprolina como marcador delator |
| **Animal — plumas** | Queratina hidrolizada | Muy rico en **Cys, Ser, Gly**; alto S | Bajo | Requiere hidrólisis dura → racemización |
| **Animal — sangre** | Hemoglobina, plasma | Perfil más equilibrado, rico en **His, Lys, Leu** | Medio | Restricciones sanitarias (subproductos animales) |
| **Vegetal — soja** | Torta/harina desgrasada | Equilibrado; rico en **Glu, Asp, Arg** | Medio-alto | — |
| **Vegetal — gluten de maíz / trigo** | Gluten meal | Muy rico en **Glu/Gln** y **Pro**; pobre en Lys | Medio | Desbalance en Lys |
| **Vegetal — agua de maceración de maíz** (*corn steep liquor*) | Subproducto de molienda húmeda | Rico en aminoácidos libres y ácido láctico | Bajo | Alta variabilidad de lote |
| **Fermentación microbiana** | *Corynebacterium glutamicum*, levaduras | **Molécula única y pura** (Glu, Lys, Trp) o extracto de levadura | Alto (molécula pura) | Ninguno relevante |

**El marcador delator del origen animal-colágeno: la HIDROXIPROLINA.** La Hyp prácticamente no existe en proteína vegetal en cantidad relevante y es abundante en colágeno. Un perfil de aminoácidos con Hyp significativa y Gly dominante **es colágeno**, diga lo que diga la etiqueta. Es la prueba más barata de trazabilidad de origen que existe. *Nivel D — razonamiento bioquímico establecido; no se localizó en esta sesión un paper que lo proponga formalmente como método de autenticación de fertilizantes → §9, NV-05.*

### 1.5 CROMO en hidrolizados de cuero: el problema real

Este es un problema **documentado, no teórico**.

**El mecanismo:** el curtido al cromo usa sales de **Cr(III)**. Los residuos sólidos de la industria (*chrome shavings*, virutas de rebajado) son proteína (colágeno) con Cr(III) unido. Convertirlos en "fertilizante de aminoácidos" es económicamente atractivo: la materia prima tiene costo negativo — el curtidor **paga** por deshacerse de ella.

**Los dos riesgos:**

1. **Cr(III) → Cr(VI).** En las virutas el cromo está como **Cr(III), que no es tóxico**, pero **puede oxidarse a Cr(VI)**, que es cancerígeno de categoría 1A por inhalación y genotóxico. La oxidación se ve favorecida por temperatura alta, pH alcalino y presencia de oxidantes — exactamente las condiciones de la hidrólisis alcalina.
2. **Carga total de Cr al suelo**, acumulativa por aplicación repetida.

**Referencia primaria verificada:** Zhao et al. (2022), *Toxicity evaluation of collagen hydrolysates from chrome shavings and their potential use in the preparation of amino acid fertilizer for crop growth*, **Journal of Leather Science and Engineering 4**. DOI **10.1186/s42825-021-00072-1** ✅ verificado. Se producen hidrolizados de colágeno de distinto peso molecular a partir de virutas al cromo por tres métodos de **descromado**: hidrólisis alcalina, enzimática, y alcalino-enzimática sinérgica. *Nivel C (ensayo de plántulas).*

Lectura escéptica de ese trabajo: **existe porque el descromado es necesario**. Que sea técnicamente posible producir un hidrolizado de cuero descromado no significa que el producto que llega al mercado boliviano o brasileño **lo esté**.

**Límite regulatorio localizado:** la legislación de Brasil y de la UE establece **2 mg/kg como límite máximo de Cr(VI) en fertilizantes orgánicos**. Fuente: trabajo sobre especiación de cromo en fertilizante orgánico por extracción en punto de nube (*Microchemical Journal*, ScienceDirect S0026265X2033006X). ⚠️ El valor 2 mg/kg es consistente con lo que fija el Reg. UE 2019/1009, pero la cita exacta del artículo y anexo debe tomarse de §7. DOI del trabajo de especiación no verificado → §9, NV-06.

**Detalle técnico incómodo y relevante:** existe literatura específica sobre **el fracaso de los métodos oficiales** para determinar Cr(VI) en matrices ricas en Cr(III) — *On the Determination of Cr(VI) in Cr(III)-Rich Particulates: From the Failure of Official Methods to the Development of an Alternative Protocol* (PMC9564694). Es decir: **el análisis de Cr(VI) que presenta el proveedor puede dar bajo por artefacto del método**, en la matriz que justamente importa. *Nivel D.* DOI → §9, NV-07.

**Criterio operativo:** ante un hidrolizado de origen animal barato, exigir (a) certificado de **Cr total** y **Cr(VI)** por laboratorio independiente, (b) declaración del método usado para Cr(VI), (c) perfil de aminoácidos completo para detectar **hidroxiprolina**. Si el proveedor no puede dar las tres, el producto no entra.

---

## 2. Moléculas específicas con mecanismo real

Distinción clave de esta sección: hay moléculas con **mecanismo bioquímico conocido y específico** (columna "mecanismo") y hay moléculas cuyo mecanismo se cita pero cuya **eficacia agronómica a dosis de campo** no está establecida. No son lo mismo.

### 2.1 Glicina betaína (N,N,N-trimetilglicina)

- **Mecanismo (nivel D, sólido):** osmolito compatible. Se acumula en el citosol y el cloroplasto sin interferir con la maquinaria enzimática; estabiliza el **complejo evolutor de oxígeno del PSII** y la Rubisco, protege membranas, contribuye al ajuste osmótico. Es de los mecanismos mejor establecidos de todo el rubro: no es un "estimulante" difuso, es una molécula con función fisicoquímica definida.
- **Especies acumuladoras naturales:** remolacha, espinaca, cebada, sorgo. **No acumuladoras:** arroz, tomate, tabaco, *Arabidopsis*. La lógica de aplicación exógena es más fuerte en las **no acumuladoras**.
- **Evidencia agronómica:** dosis foliares habituales en literatura **500–2.500 ppm**. Ensayo con dos campañas consecutivas (2021–2022) en arroz bajo salinidad: 30 mM GB y 30 mM Pro dieron **4,22 y 4,30 t/ha** de grano vs testigo. Fuente: PeerJ (PMC11913015). *Nivel B, pero bajo estrés salino impuesto.*
- **Lo honesto:** la evidencia se concentra abrumadoramente **bajo estrés** (salinidad, sequía, calor, metales pesados). **No se localizó en esta sesión un meta-análisis de glicina betaína con efecto medio e IC** → §9, NV-08.
- Revisión: *Deciphering the role of glycine betaine in enhancing plant performance and defense mechanisms against environmental stresses*, Frontiers in Plant Science (2025). *Nivel A (revisión narrativa, no meta-análisis).* DOI → §9, NV-09.

### 2.2 Triptófano (precursor de auxina)

Acá hay que ser preciso, porque el marketing dice "auxina natural" y la evidencia dice otra cosa.

- **Mecanismo (nivel D):** el Trp es precursor de **IAA (ácido indol-3-acético)** por dos rutas distintas:
  - **En la planta:** Trp → indol-3-piruvato (**TAA1/TAR**, triptófano aminotransferasa) → IAA (**YUCCA**, flavín-monooxigenasas). Es la ruta canónica.
  - **En la rizósfera:** microorganismos convierten Trp en IAA por rutas propias — indol-3-acetamida (*Pseudomonas syringae*), indol-3-piruvato (*Agrobacterium tumefaciens*). **Confirmado por HPLC que el IAA es un metabolito microbiano mayoritario derivado de L-Trp en suelo.**
- **EL DATO QUE IMPORTA — vía de aplicación:** en un experimento con rabanito comparando aplicación foliar vs al suelo, **la aplicación al suelo promovió el crecimiento y la foliar NO tuvo efecto en un rango de dosis de 10⁻² a 10⁻¹⁰ M**. En soja, en cambio, tanto el *drench* como el foliar (1,9 y 3,8 mg/planta) promovieron crecimiento radicular de forma similar (MDPI *Plants* 12(1):186, PMC9823744). *Nivel C (rizotrón / maceta).*
- **Conclusión escéptica:** el Trp funciona en buena medida como **sustrato para la microbiota del suelo**, no como pro-hormona de acción directa foliar. Esto tiene tres consecuencias prácticas que el folleto nunca dice:
  1. El efecto **depende de la población microbiana del suelo**, que varía por lote.
  2. Depende de **glucosa, N disponible, pH, temperatura, aireación y tiempo de incubación** — todos factores documentados como moduladores de la producción de IAA por la microbiota.
  3. Un Trp aplicado por vía foliar tiene un caso mucho más débil que el mismo Trp al suelo.
- **Y el problema de fabricación:** el Trp es **exactamente el aminoácido que la hidrólisis ácida destruye por completo** (§1.1). Un hidrolizado ácido que promete "triptófano precursor de auxinas" es una contradicción de proceso.

### 2.3 Ácido glutámico / glutamato

- **Mecanismo (nivel D, sólido):** es el **nudo central del metabolismo del nitrógeno vegetal**. Producto de la GS/GOGAT, donante de amino en prácticamente todas las transaminaciones, precursor de **prolina, arginina, ornitina, poliaminas, clorofila (vía ALA) y glutatión**. Es el aminoácido con más justificación bioquímica para ser el mayoritario de un hidrolizado.
- **Mecanismo de señalización (nivel C/D):** las plantas tienen **receptores tipo glutamato (GLR)**, canales iónicos homólogos a los iGluR animales, implicados en señalización de Ca²⁺, respuesta a herida y arquitectura radicular. Existe evidencia de que la señalización por glutamato induce cambios en la arquitectura radicular por una vía dependiente de **MEKK1** (PMC3739925). Es un mecanismo **real y específico**, no un "efecto nutricional".
- **La honestidad requerida:** que el glutamato sea un nudo metabólico central **no implica** que aportarlo exógenamente a dosis de campo sea limitante. La planta lo fabrica. Ver §10 (aritmética).

### 2.4 Prolina — mecanismo discutido, se declara como tal

**Este ítem se declara explícitamente como CONTROVERTIDO.**

- **Mecanismo propuesto:** osmolito compatible; mantiene turgencia y balance osmótico, estabiliza membranas evitando fuga de electrolitos, reduce ROS, actúa como chaperona química y reserva de C/N.
- **La discusión real:** la prolina **se acumula** bajo estrés — eso no está en duda. Lo que está en duda es **si la acumulación es causa de tolerancia o solo síntoma de daño**. La literatura de contaminación de suelos plantea el problema explícitamente (*Accumulation of Proline in Plants under Contaminated Soils—Are We on the Same Page?*, PMC10045403).
- **Evidencia contradictoria documentada** (Hosseinifard et al. 2022, *Contribution of Exogenous Proline to Abiotic Stresses Tolerance in Plants: A Review*, **Int. J. Mol. Sci. 23(9): 5186**, DOI **10.3390/ijms23095186** ✅ verificado. *Nivel A, revisión*):
  - Hay **efectos tóxicos de la prolina exógena a concentraciones altas**.
  - **Un número considerable de estudios no encontró resultados óptimos** usando prolina como mitigador de estrés, y algunos reportaron toxicidad.
  - Caso concreto de efecto **contrario según el estrés**: la prolina **redujo el daño por deficiencia de boro pero AUMENTÓ la toxicidad por aluminio** en plántulas de tomate — considerado perjudicial.
- **Conclusión operativa:** la prolina exógena es **dosis-dependiente con ventana estrecha y signo variable según el estrés**. Es el ejemplo más claro del dossier de que "acumula bajo estrés" ≠ "aplicarla mejora la tolerancia". No recomendarla como componente activo sin ensayo local en el estrés específico.

### 2.5 ALA (ácido 5-aminolevulínico)

- **Mecanismo (nivel D, muy sólido y específico):** el ALA es **el precursor común de todos los tetrapirroles** — clorofila, hemo, sirohemo. Es el punto de control de la ruta. Aplicarlo exógenamente aumenta los intermediarios de la rama de clorofila: **protoporfirina IX, Mg-protoporfirina IX, protoclorofilida y clorofila**. Ese encadenamiento está medido, no supuesto (PMC5962685, pepino bajo salinidad).
- **Efectos reportados:** regula fotosíntesis, absorción de nutrientes, metabolismo antioxidante y síntesis proteica; mejora la estabilidad de la clorofila y del PSII; tolerancia a salinidad, sequía, calor, frío, UV-B, sombra, Cd y Cr(VI).
- **Revisiones (ambas ✅ verificadas vía Crossref):** Akram, M. et al. (2013), *Regulation in Plant Stress Tolerance by a Potential Plant Growth Regulator, 5-Aminolevulinic Acid*, **Journal of Plant Growth Regulation 32: 663–679**, DOI **10.1007/s00344-013-9325-9**; y Wu, Y. et al. (2018), *5-Aminolevulinic acid (ALA) biosynthetic and metabolic pathways and its role in higher plants: a review*, **Plant Growth Regulation 87: 357–374**, DOI **10.1007/s10725-018-0463-8**.
- **Lo que hay que decir:** el ALA es la molécula del dossier con **mejor relación mecanismo/evidencia**, pero la casi totalidad de los ensayos son **nivel C (plántulas, maceta, cámara)** — pepino, repollo chino, poroto, tejo, festuca, tomate, álamo. **No se localizó meta-análisis ni cuerpo de ensayos de campo con rendimiento** → §9, NV-11. Además es una molécula **cara**, lo que empuja las dosis comerciales hacia abajo.

### 2.6 Poliaminas (putrescina, espermidina, espermina)

- **Mecanismo (nivel D):** policationes a pH fisiológico. Se unen electrostáticamente a ácidos nucleicos, fosfolípidos y proteínas de pared; **modulan el transporte iónico a través de membranas** (bloqueo de canales catiónicos no selectivos, control de fugas de K⁺ bajo estrés salino). Interactúan con ABA, etileno, giberelinas y jasmonatos. Su **catabolismo genera H₂O₂**, que actúa como molécula señal — mecanismo de doble filo.
- **Conexión con §2.3:** el glutamato es el precursor común de prolina, arginina, ornitina y por lo tanto de las poliaminas. Es la misma ruta.
- **Evidencia:** mayoritariamente **nivel C** (trébol blanco bajo sequía, zoysia bajo salinidad, *Anoectochilus* bajo déficit hídrico). El área con evidencia más aplicada es **poscosecha** (*Modulatory Effects of Exogenously Applied Polyamines on Postharvest Physiology, Antioxidant System and Shelf Life of Fruits*, PMC5578177) — allí sí hay uso práctico con respaldo.
- **Honestidad sobre el mecanismo de moda:** la idea de que las poliaminas actúan sobre **receptores de glutamato y canales CNG** en plantas está explícitamente descrita en la literatura como **"plausible pero inexplorada"**. No usarla como argumento de venta.

---

## 3. Extractos de algas (*Ascophyllum nodosum*)

### 3.1 Composición real

*A. nodosum* (alga parda, Atlántico norte) es la especie dominante del rubro. Composición del alga, con rangos publicados:

| Componente | Contenido | Función propuesta |
|---|---|---|
| **Ácido algínico / alginatos** | **15–30 %** | Polisacárido de pared; acondicionador de suelo, agente formador de gel |
| **Fucoidanos** (sulfatados) | **4–10 %** | Elicitor de defensa, actividad inmunoestimulante |
| **Manitol** | **5–10 %** | Poliol; osmolito; **agente complejante de micronutrientes** |
| **Laminarina** | **0–10 %** | β-1,3-glucano; **elicitor de defensa reconocido** |
| **Betaínas** | Presentes | Osmoprotección (misma lógica que §2.1) |
| **Florotaninos** | Presentes, variables | Antioxidantes, polifenoles característicos de pardas |
| **"Citoquininas, auxinas, giberelinas"** | Trazas | ⚠️ Ver advertencia abajo |
| Minerales (K, P, Ca, B, Mg, Zn) | **Concentración baja** | Marginal a dosis de uso |

**Referencia principal:** Shukla, Mantin, Adil, Bajpai, Critchley & Prithiviraj (2019), *Ascophyllum nodosum-Based Biostimulants: Sustainable Applications in Agriculture for the Stimulation of Plant Growth, Stress Tolerance, and Disease Management*, **Frontiers in Plant Science 10: 655**. DOI **10.3389/fpls.2019.00655** ✅ verificado. *Nivel A (revisión).*

**Revisión sobre estrés abiótico:** Deolu-Ajayi et al. (2022), *The power of seaweeds as plant biostimulants to boost crop production under abiotic stress*, **Plant, Cell & Environment 45: 2537–2553**. DOI **10.1111/pce.14391** ✅ verificado. *Nivel A.*

> ⚠️ **Advertencia sobre "hormonas del alga".** La literatura habla consistentemente de actividad **"tipo citoquinina" y "tipo auxina"** (*cytokinin-like*, *auxin-like*) — es decir, **bioensayos que responden como si hubiera hormona**, no necesariamente cuantificación de la hormona en concentración fisiológicamente activa a la dosis aplicada. La distinción entre "el extracto produce el efecto que produciría una citoquinina" y "el extracto contiene citoquinina suficiente para causar ese efecto" **no está resuelta** y el marketing la colapsa sistemáticamente. Tratar como **nivel D con reserva**.

### 3.2 La variación por método de extracción — el punto que decide el producto

**No existe "extracto de *Ascophyllum*" como categoría homogénea.** El método de extracción cambia la composición, y por lo tanto cambia el producto.

Métodos en uso industrial: acuoso, agua:etanol (90:10), **hidrólisis ácida**, **hidrólisis alcalina**, asistida por microondas, asistida por ultrasonido, microondas+ultrasonido, asistida por enzimas, fluidos supercríticos, líquido presurizado.

Datos concretos localizados:

- **Ácido seguido de álcali** fue el método más eficiente de todos los investigados: **59 % de recuperación de proteína**. Le sigue **álcali en un paso asistido con ultrasonido: 57 %**.
- El pretratamiento con **H₂SO₄ o HCl a 40–50 °C por 30 min** remueve compuestos fenólicos complejos y aumenta la despolimerización de polisacáridos. Es decir: **la extracción ácida destruye los florotaninos**, que son parte de lo que se vende como principio activo.
- Productos comerciales de referencia con extracción declarada: **PSI-494** (alta temperatura, condiciones alcalinas) y **Acadian®** (extracto alcalino comercial), este último con evidencia en soja bajo sequía severa regulando temperatura foliar, turgencia y genes de respuesta a estrés.
- La extracción **en base agua** es la más aceptable según principios de química verde en escala industrial.

**Consecuencia comercial directa:** dos productos etiquetados "extracto de *Ascophyllum nodosum* 20%" pueden tener composiciones **incomparables**. La única pregunta útil al proveedor es **"¿cuál es el método de extracción?"**, y la segunda es "¿el ensayo de eficacia que me muestra fue hecho con ESTE extracto o con otro?".

### 3.3 Qué muestran los ensayos

- **Meta-análisis (nivel A, ver §8):** extractos de algas → **+17,1 % de rendimiento (IC 95 %: 14,4–19,8)**, sobre 180 estudios de campo (Li et al. 2022).
- **Meta-análisis específico de algas:** Pérez-Oñate et al. (2026), *Crop yield responses to seaweed extract-based biostimulants depend on application strategy, formulation, and extraction methods: a meta-analysis*, **Frontiers in Plant Science 17**, DOI **10.3389/fpls.2026.1803269** ✅ verificado vía Crossref. Reporta incremento de rendimiento del **~16 %**, con *A. nodosum* mostrando **los efectos más estables entre especies**, mientras que *Laminaria*, *Gracilaria* y *Kappaphycus* fueron **más variables**. **El propio título del trabajo confirma la tesis de §3.2: la respuesta DEPENDE de la estrategia de aplicación, la formulación y el método de extracción.** ⚠️ Números internos (IC, I², sesgo, desglose por método de extracción) **no se pudieron extraer** por falla de red repetida contra Frontiers → §9, NV-12.
- **Meta-análisis en cereales bajo salinidad:** Nuruzzaman, Md. et al. (2025), *Seaweed Extracts Improve Salinity Tolerance in Cereal Crops—A Meta-Analysis*, **Plant-Environment Interactions 6**, DOI **10.1002/pei3.70094** ✅ verificado vía Crossref. Los extractos acuosos mejoraron biomasa aérea y radicular **tanto en condiciones normales como bajo salinidad**; eficaces en el rango 34,2–100 mM y 101–400 mM NaCl equivalente; **concentraciones ≤ 25 % de extracto acuoso fueron las más efectivas**. *Nivel A.* ⚠️ Los efectos medios con IC no se pudieron extraer del texto completo → §9, NV-13.
- **Ensayos individuales:** hasta **+65 % de rendimiento de fruta** en tomate cherry con tratamiento de semilla, bajo sequía; **+3,08 Mg/ha de caña** bajo sequía (PMC9096543). ⚠️ Estos son los números que usa el marketing. Son **extremos de la distribución**, no la esperanza. El valor esperado es el del meta-análisis: **~16–17 %**, y en condiciones óptimas, menos.

---

## 4. Ácidos húmicos y fúlvicos

> Sección parcialmente cubierta por investigación paralela que no pudo completarse por límite de concurrencia de agentes. Lo que sigue está verificado; los faltantes están en §9.

### 4.1 Materias primas

| Fuente | Origen | Comentario |
|---|---|---|
| **Leonardita** | Lignito oxidado naturalmente (aflorante) | **La fuente preferida del rubro.** Ya está oxidada → alto contenido de grupos funcionales carboxílicos y fenólicos → mayor extractabilidad y mayor capacidad de intercambio/quelación |
| **Lignito / carbón subbituminoso** | Carbón de bajo rango | Menos oxidado; requiere oxidación previa |
| **Turba (*peat*)** | Materia vegetal parcialmente descompuesta | Menor contenido de húmicos; extracción de recurso no renovable con costo ambiental |
| **Suelo, compost, vermicompost, residuos orgánicos** | Materia orgánica en humificación | Contenido bajo y muy variable |

Rose et al. (2014) definen el objeto exactamente así: las sustancias húmicas son los productos de degradación de restos vegetales y animales **extraídos en solución alcalina** a partir de carbones subbituminosos, lignitos, turba, suelo, compost y residuos orgánicos crudos.

⚠️ **Contenidos porcentuales típicos de AH por fuente: NO VERIFICADOS numéricamente en esta sesión** → §9, NV-14.

### 4.2 Extracción y la definición OPERACIONAL

El punto crítico conceptual: **ácido húmico y ácido fúlvico no son moléculas. Son fracciones definidas por un procedimiento.**

| Fracción | Definición operacional |
|---|---|
| **Ácido húmico (AH)** | Soluble en álcali (NaOH/KOH), **insoluble al acidificar a pH < 2** → precipita |
| **Ácido fúlvico (AF)** | Soluble en álcali **y soluble a todo pH**, incluido pH < 2 → queda en el sobrenadante |
| **Humina** | **Insoluble en álcali** |

Consecuencias inmediatas y poco cómodas:

1. **Si cambia el procedimiento, cambia el resultado.** No hay un "verdadero % de ácidos húmicos" independiente del método.
2. La extracción alcalina en presencia de O₂ puede **oxidar y condensar** material, generando artefactos (condensaciones tipo Maillard entre azúcares y aminas). Parte de lo que se extrae puede haberse **formado durante la extracción**.
3. La fracción "fúlvica" comercial arrastra rutinariamente material no húmico soluble en ácido (azúcares, aminoácidos, sales).

### 4.3 EL PUNTO CENTRAL: el "% de ácidos húmicos" de la etiqueta NO es comparable entre productos

Esto hay que documentarlo bien porque es la trampa estructural de la categoría.

**El problema:** distintos métodos analíticos dan distintos números **para el mismo producto**. Como el número no viene acompañado del método, comparar dos etiquetas es comparar nada.

**Los métodos en circulación:**

| Método | Principio | Sesgo conocido |
|---|---|---|
| **Gravimétrico "casero"** | Precipitar a pH<2, secar, pesar | **Sobreestima**: co-precipitan cenizas, arcillas, minerales y materia orgánica no húmica. No corrige por contenido de cenizas |
| **Colorimétrico** | Absorbancia del extracto alcalino | **Depende enteramente del estándar de calibración elegido**. Sin estándar universal, el número es arbitrario |
| **Mehlich / AOAC** | Colorimétrico normalizado | Limitaciones de matriz |
| **IHSS** | Protocolo de la *International Humic Substances Society*: extracción + purificación exhaustiva (desceniza con HF/HCl, diálisis, liofilización) | Riguroso pero **laborioso**; pensado para caracterización científica, no para control de calidad de rutina |
| **Lamar et al. (el estandarizado)** | Método diseñado específicamente para **menas húmicas y productos comerciales** | El intento serio de resolver el problema |

**La referencia que hay que citar — verificada:**

> Lamar, R.T., Olk, D.C., Mayhew, L. & Bloom, P.R. (2014). *A New Standardized Method for Quantification of Humic and Fulvic Acids in Humic Ores and Commercial Products*. **Journal of AOAC International 97(3): 721–730**. DOI **10.5740/jaoacint.13-393** ✅ verificado vía Crossref.

Antecedente de validación: Lamar, Olk, Mayhew & Bloom (2012), *Evaluation of a Proposed Standardized Analytical Method for the Determination of Humic and Fulvic Acids in Commercial Products*, en **Functions of Natural Organic Matter in Changing Environment**, pp. 1071–1073. DOI **10.1007/978-94-007-5634-2_198** ✅ verificado.

Protocolo en video (2022): Lamar & Monda, **Journal of Visualized Experiments**, DOI **10.3791/61233** ✅ verificado vía Crossref.

⚠️ **Lo que NO se pudo verificar y es importante:** el **número de método oficial AOAC** que corresponde (si el método de Lamar fue adoptado como *Official Method* y con qué número), el estado *First Action* vs *Final Action*, y sobre todo **la magnitud numérica de la divergencia entre métodos** (el factor de sobreestimación del gravimétrico frente al estandarizado). Ver §9, NV-15 y NV-16. **Esa cifra es la que más falta hace y es la que no se debe inventar.**

### 4.4 El debate de fondo: ¿existen las "sustancias húmicas"?

No es una discusión académica ociosa: golpea directamente la etiqueta.

**La crítica.** Lehmann, J. & Kleber, M. (2015), *The contentious nature of soil organic matter*, **Nature 528: 60–68**. DOI **10.1038/nature16069** ✅ verificado. Sostiene que las macromoléculas húmicas grandes y persistentes son en buena medida **un artefacto de la extracción alcalina**, y que la materia orgánica del suelo se entiende mejor como un continuo de moléculas pequeñas en descomposición progresiva, estabilizadas por interacción con minerales y por accesibilidad física, no por una recalcitrancia química intrínseca.

**La respuesta.** Olk, D.C., Bloom, P.R., Perdue, E.M., McKnight, D.M., Chen, Y., Farenhorst, A., Senesi, N., Chin, Y.-P., Schmitt-Kopplin, P., Hertkorn, N. & Harir, M. (2019), *Environmental and Agricultural Relevance of Humic Fractions Extracted by Alkali from Soils and Natural Waters*, **Journal of Environmental Quality 48: 217–232**. DOI **10.2134/jeq2019.02.0041** ✅ verificado (existe además una fe de erratas, DOI 10.2134/jeq2019.02.0041er, JEQ 48: 1126). Argumenta que, artefacto o no, **las fracciones extraídas por álcali tienen relevancia ambiental y agronómica demostrable** y que descartarlas por objeciones nomenclaturales es tirar el dato con la definición.

**Qué implica para un producto comercial:**

1. El "% de ácidos húmicos" es una cifra **definida por procedimiento**, no una propiedad intrínseca del producto. Aun con el debate resuelto a favor de Olk, sigue siendo operacional.
2. Un producto puede tener 12 % por un método y otro número por otro método, y **ambos ser correctos dentro de su definición**.
3. Por lo tanto: **especificar el método en el pliego de compra, o no especificar nada útil.** Es el único blindaje.

### 4.5 Mecanismos con evidencia

**Estimulación de la H⁺-ATPasa de la membrana plasmática radicular.** Es el mecanismo mejor sostenido de toda la categoría, y a diferencia de casi todo lo demás en este dossier **tiene una cadena causal medida, no supuesta**. La bomba de protones acidifica el apoplasto → la acidificación activa expansinas → la pared cede → hay elongación celular y emisión de raíces laterales. Es la "teoría del crecimiento ácido", el mismo mecanismo por el que actúa la auxina — y de ahí viene la etiqueta de "actividad tipo auxina" de las fracciones húmicas de bajo peso molecular.

Las tres referencias que sostienen la cadena, **todas ✅ verificadas vía Crossref**:

1. **Canellas, L.P. et al. (2002)**, *Humic Acids Isolated from Earthworm Compost Enhance Root Elongation, Lateral Root Emergence, and Plasma Membrane H⁺-ATPase Activity in Maize Roots*, **Plant Physiology 130: 1951–1957**. DOI **10.1104/pp.007088**. — El trabajo fundacional. *Nivel C.*
2. **Zandonadi, D.B. et al. (2006)**, *Indolacetic and humic acids induce lateral root development through a concerted plasmalemma and tonoplast H⁺ pumps activation*, **Planta 225: 1583–1595**. DOI **10.1007/s00425-006-0454-2**. — Muestra que ácido húmico y **AIA (auxina) actúan por la misma vía**, activando de forma concertada las bombas de protones de plasmalema y tonoplasto. Es la evidencia dura detrás de "actividad tipo auxina". *Nivel C.*
3. **Zandonadi, D.B. et al. (2010)**, *Nitric oxide mediates humic acids-induced root development and plasma membrane H⁺-ATPase activation*, **Planta 231: 1025–1036**. DOI **10.1007/s00425-010-1106-0**. — Identifica el **óxido nítrico** como mediador de la señal. *Nivel C.*

Otros mecanismos propuestos:

- **Quelación de micronutrientes** por los grupos carboxílicos y fenólicos, aumentando disponibilidad de Fe, Zn, Mn en suelos calcáreos.

> ⚠️ **La reserva que corresponde hacer, y es grande.** Las tres referencias son **nivel C**: raíces de maíz, sistemas controlados, dosis de laboratorio. El mecanismo está demostrado; **lo que NO está demostrado es que ese mecanismo sea el que produce el +16,5 % de rendimiento a campo** (§8.2), ni que a las dosis comerciales de §10.1 la concentración de ácido húmico que llega a la rizósfera alcance el umbral que activa la bomba. **Tener un mecanismo elegante no es tener una explicación del efecto de campo.** Los DOIs de Nardi y Piccolo no se localizaron por esta vía → §9, NV-17.

### 4.6 Evidencia cuantitativa

- **Rose et al. (2014)**, *A Meta-Analysis and Review of Plant-Growth Response to Humic Substances*, **Advances in Agronomy 124: 37–89**. DOI **10.1016/B978-0-12-800138-7.00002-4** ✅ verificado vía Crossref (nota: el registro Crossref **no incluye** el subtítulo "Practical Implications for Agriculture" que sí aparece en muchas citas). Conclusión verificada del propio texto: aunque la aplicación de HS tiene potencial de mejorar el crecimiento vegetal, **la magnitud de la promoción es inconsistente y relativamente impredecible en comparación con los fertilizantes inorgánicos**. ⚠️ Los valores numéricos (% de aumento de biomasa aérea y radicular, IC, n de estudios, factores explicativos) **no se pudieron extraer**: Crossref no expone abstract y ScienceDirect/Monash fallaron por red → §9, NV-18.
- **Ma, Cheng & Zhang (2024)**, *The Impact of Humic Acid Fertilizers on Crop Yield and Nitrogen Use Efficiency: A Meta-Analysis*, **Agronomy 14: 2763**. DOI **10.3390/agronomy14122763** ✅ verificado. Resultados del abstract:
  - Rendimiento: **+12 %**
  - **Eficiencia de uso de nitrógeno: +27 %**
  - Absorción de nitrógeno: **+17 %**
  - Mejores resultados con **precipitación anual > 300 mm**, **temperatura media > 10 °C**, **suelos de pH moderado (6 < pH ≤ 8)** y **bajo nivel de nitrógeno**.
  - **Efectividad REDUCIDA en suelos alcalinos y en condiciones de alto nitrógeno.**
  - Cultivos de renta y cereales de secano respondieron mejor que arroz inundado, con N de 100–200 kg/ha.
  - ⚠️ IC 95 %, I² y pruebas de sesgo de publicación **no extraídos** (falla de red contra MDPI) → §9, NV-19.
- **Li et al. (2022), campo:** húmicos + fúlvicos → **+16,5 % (IC 95 %: 13,7–19,3)**. Ver §8.

**Lectura conjunta:** los tres coinciden en un efecto **positivo, moderado (12–17 %) y fuertemente condicional**. El hallazgo más accionable es el de Ma et al.: **el beneficio se concentra donde el N es bajo y desaparece donde el N es alto.** Es el patrón de estrés de §8, expresado en nutrición.

---

## 5. Aminoquelatos y complejos orgánicos

> **Sección con el mayor déficit de verificación del dossier.** La investigación paralela asignada a este punto no pudo ejecutarse (límite de concurrencia de agentes) y el presupuesto de búsqueda se agotó. **Deliberadamente NO se reportan constantes de estabilidad numéricas que no se pudieron verificar** (ver §9, **NV-23**, la laguna más grave del documento). Se reporta el marco conceptual, lo poco verificado, y una lista explícita de lo que falta medir.

### 5.1 ¿Un "aminoquelato" cumple la definición química de quelato?

**Respuesta corta: formalmente sí, funcionalmente casi nunca al nivel que implica el nombre.**

**Definición.** Un quelato requiere un **ligando polidentado** que se una al metal por **dos o más átomos donores**, formando un **anillo**. La estabilidad extra frente a ligandos monodentados equivalentes es el **efecto quelato**, de origen mayoritariamente entrópico.

**El caso de la glicina.** La glicina tiene un grupo **amino (N donor)** y un **carboxilato (O donor)**. Al coordinarse a un metal por ambos forma un **anillo de 5 miembros** — la geometría más favorable. Por lo tanto **la glicina ES un ligando bidentado y el glicinato metálico ES formalmente un quelato**. Ese es el argumento honesto del rubro, y es correcto.

**Dónde se cae el argumento — tres puntos:**

1. **Denticidad.** La glicina es **bidentada**. El EDTA es **hexadentado**. El número de anillos formados no es comparable, y la estabilidad tampoco.
2. **Competencia iónica en el suelo.** El suelo tiene **Ca²⁺ y Mg²⁺ en concentración milimolar** — tres a seis órdenes de magnitud por encima del micronutriente aplicado. Un ligando de constante de estabilidad baja **cede el metal por acción de masas** y el Zn liberado precipita o se adsorbe. Un ligando de constante alta lo retiene.
3. **pH.** El grupo amino de la glicina debe estar **desprotonado** para coordinar. A pH ácido está protonado (–NH₃⁺) y no coordina. La quelación por aminoácidos es fuertemente pH-dependiente en el rango agronómico.

**El punto donde el marketing miente por omisión:** la afirmación "es un quelato" es verdadera y **completamente insuficiente**. La pregunta correcta no es *si* quela, sino **con qué constante y a qué pH**, y si esa constante alcanza para sobrevivir a la competencia del Ca²⁺ del suelo hasta la raíz o hasta la cutícula.

Esto es un caso textual de la regla ya establecida en este proyecto: **"es verdad" no es lo mismo que "aplica"**.

### 5.2 Criterio operativo para distinguir quelato real / complejo débil / mera mezcla

Este es el entregable útil de la sección, y no depende de tener las constantes a mano.

| Nivel | Qué es | Cómo se detecta |
|---|---|---|
| **Quelato real** | Ligando polidentado, log K alto, el metal permanece coordinado en el rango de pH de uso | **Sobrevive la prueba de precipitación alcalina**; cuantificable por norma **EN 13366** (retención en resina de intercambio catiónico) y **EN 13368** (cromatografía, identifica el quelante por nombre e isómero) |
| **Complejo débil** | Coordinación real pero log K bajo (aminoácidos, gluconato, citrato, lignosulfonato) | Precipita al subir el pH; **la fracción retenida en resina cae con el pH** |
| **Mera mezcla física** | Sal metálica + aminoácidos en el mismo envase, sin coordinación | **Precipita inmediatamente** al alcalinizar; comportamiento indistinguible de la sal sola |

**Las tres pruebas que se le piden al proveedor, en orden de costo:**

1. **Prueba de precipitación (barata, hacer en casa).** Diluir el producto y llevar a **pH 9** con NaOH, o agregar fosfato monoamónico. Un **Zn realmente quelado permanece en solución**; un Zn en mezcla física precipita como hidróxido u ortofosfato de zinc, visible a simple vista. Es un test cualitativo pero **discrimina el fraude grosero en cinco minutos**.
2. **Fracción quelada por EN 13366** (resina de intercambio catiónico): da el **porcentaje del micronutriente soluble en agua que está efectivamente acomplejado**.
3. **Identificación del agente por EN 13368** (cromatografía): confirma **qué** quelante es y en qué isómero (relevante especialmente en EDDHA, donde el isómero *orto-orto* es el efectivo).

⚠️ El **alcance exacto** de EN 13366 y de cada parte de EN 13368, y los **umbrales porcentuales** que exige el Reg. UE 2019/1009 para poder declarar un micronutriente como "quelado", **quedaron sin verificar** → §9, NV-20 y NV-21.

### 5.3 Lignosulfonato — la advertencia que corresponde hacer

El lignosulfonato es un **polímero polidisperso**, subproducto de la pulpa al sulfito, de composición variable según la madera y el proceso. **Hablar de "la constante de estabilidad del lignosulfonato" es una impropiedad química**: no es una especie molecular definida, es una población de macromoléculas. Cualquier valor de log K citado para lignosulfonato debe entenderse como una **constante condicional operativa** para un lote y unas condiciones dadas, no como una constante termodinámica. Los complejos metal-lignosulfonato están descritos como **complejos débiles**, útiles principalmente para aplicación **foliar** y de bajo costo, no para corrección de deficiencias en suelo calcáreo.

*Nivel D — razonamiento químico establecido. Sin cita verificada en esta sesión → §9, NV-22.*

### 5.4 Fe: el caso donde el criterio sí está zanjado

En hierro, el mercado y la literatura coinciden y no hay ambigüedad:

- **Fe-EDDHA** (y análogos EDDHMA, EDDHSA) es **el tratamiento estándar** para corregir clorosis férrica en suelo calcáreo. Es el único que mantiene el Fe soluble a pH alto.
- **Fe-EDTA y Fe-DTPA** son soluciones satisfactorias para **otros micronutrientes como Zn**, pero **no** para Fe en suelo calcáreo: el EDTA pierde el Fe³⁺ frente al Ca²⁺ y al OH⁻ a pH elevado.
- Referencias verificadas: Álvarez-Fernández, Hernández-Apaolaza, Lucena et al. (2005), *Evaluation of synthetic iron(III)-chelates (EDDHA/Fe³⁺, EDDHMA/Fe³⁺ and the novel EDDHSA/Fe³⁺) to correct iron chlorosis*, **European Journal of Agronomy 22: 119–130**, DOI **10.1016/j.eja.2004.02.001** ✅ verificado. Y Hernández-Apaolaza, Lucena et al. (1995), *Efficacy of commercial Fe(III)-EDDHA and Fe(III)-EDDHMA chelates to supply iron to sunflower and corn seedlings*, **Journal of Plant Nutrition 18: 1209–1223**, DOI **10.1080/01904169509364973** ✅ verificado.

**El corolario que interesa:** si en **hierro** — donde el problema es más severo — la industria y la academia convergen en que hace falta un quelante **hexadentado y fenólico** como el EDDHA, la pretensión de que un **aminoácido bidentado** cumpla la misma función en suelo calcáreo **no tiene sustento**. Para uso foliar el argumento es distinto y más favorable (ver 5.5).

### 5.5 Eficacia comparada aminoquelato vs EDTA vs sulfato

**Este es el punto que quedó SIN VERIFICAR y es central.** Lo que corresponde declarar:

- La hipótesis que se quería contrastar es que, **en aplicación FOLIAR**, el **ZnSO₄ rinde igual o mejor que el Zn-EDTA**, porque la absorción cuticular favorece moléculas **pequeñas, de bajo peso molecular y con punto de delicuescencia adecuado**, y el quelato es una molécula **grande y cargada** que penetra peor. La línea de trabajo relevante es la de **Victoria Fernández y Patrick Brown** sobre absorción foliar y propiedades fisicoquímicas.
- **No se pudo verificar ni un solo ensayo comparativo con repeticiones para esta hipótesis en esta sesión.** Ver §9, NV-24.
- **Por lo tanto: este dossier NO afirma que el sulfato foliar sea equivalente al quelato, ni lo contrario.** Es una pregunta abierta que este documento deja explícitamente pendiente, y es probablemente la que más plata decide en el rubro de micronutrientes.

> **🔎 DÓNDE BUSCAR PARA CERRAR ESTA LAGUNA.** La revisión que responde exactamente esta pregunta y que debe leerse antes de cualquier decisión de compra de micronutrientes:
>
> **Montalvo, D. et al. (2016).** *Agronomic Effectiveness of Zinc Sources as Micronutrient Fertilizer*. **Advances in Agronomy**. DOI **10.1016/bs.agron.2016.05.004** ✅ existencia verificada vía Crossref; **contenido no leído en esta sesión**.
>
> Es una revisión en la misma serie (*Advances in Agronomy*) y del mismo tipo que la de Rose et al. usada en §4.6, dedicada específicamente a comparar la eficacia agronómica de las **fuentes de zinc** — sulfato, óxido, quelatos sintéticos y complejos orgánicos. Es el documento único de mayor valor para cerrar NV-23 y NV-24.

**Lo que sí se puede decir con lo verificado:** el problema del quelante es **de suelo, no de hoja**. En suelo el quelante existe para impedir que el metal precipite o se adsorba antes de llegar a la raíz; ahí la constante de estabilidad manda y el aminoquelato es débil. En hoja, el metal atraviesa la cutícula en centímetros de recorrido y minutos de exposición: la función del quelante es mucho menos crítica, y el argumento del aminoquelato es **más defendible ahí que en suelo** — que es exactamente al revés de como se vende.

---

## 6. Quitosano y silicio

### 6.1 Quitosano

- **Qué es:** derivado **parcialmente desacetilado** de la quitina (de exoesqueletos de crustáceos o de pared fúngica). El **grado de desacetilación** y el **peso molecular** son las dos variables que definen el producto — y las dos que la etiqueta suele omitir.
- **Mecanismo (nivel D, bien establecido):** es un **elicitor de defensa**. La quitina es un **PAMP** clásico; su percepción en *Arabidopsis* ocurre por el receptor **CERK1** (*Chitin Elicitor Receptor Kinase 1*), una quinasa tipo receptor con motivo LysM. La quitina, los quito-oligómeros y el quitosano inducen **fosforilación de CERK1 in vivo** en múltiples residuos del dominio yuxtamembrana y del dominio quinasa. CERK1 es esencial para la señalización por elicitor de quitina y para la resistencia a hongos.
  - Referencias: *CERK1, a LysM receptor kinase, is essential for chitin elicitor signaling in Arabidopsis* (PubMed 18042724); *The LysM Motif Receptor-like Kinase CERK1 Is a Major Chitin-binding Protein in Arabidopsis thaliana and Subject to Chitin-induced Phosphorylation* (PMC2937917). Un preprint indica que **la percepción de quitosano en *Arabidopsis* también requiere AtCERK1**, lo que sugiere un modelo unificado de receptor (bioRxiv 170092). DOIs → §9, NV-25.
  - Confirmación de conservación del mecanismo: CERK1 es requerido para la generación de ROS disparada por quitina en melón y está ampliamente conservado en cucurbitáceas (PMC12645901).
- **La consecuencia regulatoria que casi nadie ve:** si el quitosano **funciona por activar defensa contra patógenos**, entonces reclamar protección de cultivo lo convierte en **producto fitosanitario**, no en bioestimulante (ver §7). El mismo producto cambia de categoría según lo que diga la etiqueta. Es la frontera más ambigua del marco legal.
- **Evidencia agronómica (nivel A):** quitosano → **+14,8 % de rendimiento (IC 95 %: 11,8–17,8)** en el meta-análisis de campo de Li et al. 2022. Es el más bajo de los orgánicos evaluados, por encima solo del fosfito.
- **Lo que hay que exigir:** peso molecular, grado de desacetilación, y **el pH de la formulación** — el quitosano solo es soluble en medio ácido y precipita al neutralizar, lo que crea problemas reales de compatibilidad en tanque.

### 6.2 Silicio

Acá hay que ir contra la corriente del marketing, porque la literatura crítica es contundente.

- **Estatus:** el Si **no es un elemento esencial** para la mayoría de las plantas. Es un **elemento benéfico**. Acumuladores fuertes: arroz, caña de azúcar, trigo, gramíneas en general.
- **La revisión crítica de referencia — verificada:** Coskun, D. et al. (2019), *The controversies of silicon's role in plant biology*, **New Phytologist 221: 67–85**. DOI **10.1111/nph.15343** ✅ verificado (registro Crossref con fecha de emisión 2018, número de volumen 221 de 2019).
  - Su conclusión es dura y hay que citarla como es: **la evidencia empírica, en particular la derivada de genómica funcional reciente, está en contradicción con muchas de las afirmaciones mecanísticas que rodean al silicio, y esos datos NO sostienen los reportes de que el silicio afecta un rango amplio de procesos molecular-genéticos, bioquímicos y fisiológicos.**
- **El mecanismo que Coskun et al. proponen en reemplazo — la "hipótesis de obstrucción apoplástica":** el Si precipitado como sílice amorfa **fortifica el apoplasto radicular y la pared celular** alrededor de la vasculatura. Al depositarse en pared, **adsorbe y bloquea la difusión de cationes metálicos**, reduciendo su transferencia al interior celular, e interfiere con la señalización y el reconocimiento durante la infestación por patógenos y la alimentación de insectos. Es decir: un mecanismo **físico y apoplástico**, no una cascada de señalización activa.
- **Evidencia a favor de esa hipótesis:** en arroz y pepino, agregar Si al medio causó **mayor formación de placa de hierro**, disminuyendo la absorción de Fe y **activando respuestas de deficiencia de Fe incluso con suministro óptimo de Fe** — consistente con obstrucción apoplástica.
- **Evidencia de que el Si también puede perjudicar:** el Si **debilita la barrera apoplástica externa en raíces de arroz y retrasa su formación, resultando en MAYORES flujos de Na⁺ y Cl⁻ hacia la parte aérea** (ScienceDirect S0098847224002995). Es decir, hay contexto en que el Si empeora el problema salino. Registrarlo.
- **Evidencia agronómica (nivel A):** silicio → **~+15 %** de rendimiento en Li et al. 2022, pero explícitamente señalado como **la categoría de MAYOR variabilidad** de todas las evaluadas.
- **Traducción práctica:** el Si tiene el mejor caso en **gramíneas acumuladoras** (arroz, caña, trigo) y para **fortalecimiento estructural / defensa mecánica**. La narrativa de "el silicio activa las defensas y regula el estrés" está explícitamente cuestionada por la revisión más citada del tema. Vender Si como modulador fisiológico general es ir contra la evidencia disponible.

---

## 7. Marco regulatorio

> ⚠️ **SECCIÓN NO VERIFICADA CONTRA FUENTE PRIMARIA.** La investigación paralela asignada a esta sección **no devolvió resultados antes del cierre**, y el presupuesto de búsqueda web estaba agotado. Lo que sigue es el **esqueleto estructural** del marco regulatorio — correcto en su arquitectura, pero **sin una sola cita verificada contra EUR-Lex, el Diário Oficial da União ni SENASAG**.
>
> **NO usar esta sección para un pliego de compra, un registro de producto ni una comunicación a cliente sin verificar cada dato en la fuente oficial.** Los ítems NV-26 a NV-30 de §9 listan exactamente qué falta.

### 7.1 Unión Europea — Reglamento (UE) 2019/1009

El **Reglamento (UE) 2019/1009** sobre productos fertilizantes con marcado CE es la primera norma que da **estatus legal explícito** al bioestimulante vegetal. Aplicable desde **16 de julio de 2022**, sustituyendo al Reg. (CE) 2003/2003.

**La arquitectura:** los productos se clasifican por **PFC** (*Product Function Category* — qué hace el producto) y por **CMC** (*Component Material Category* — de qué está hecho). Un producto debe cumplir **ambas**.

**PFC 6 — Bioestimulante vegetal**, con dos subcategorías:
- **PFC 6(A)** — bioestimulante microbiano
- **PFC 6(B)** — bioestimulante no microbiano ← *acá caen los hidrolizados proteicos, húmicos/fúlvicos, extractos de algas, quitosano*

**Los CUATRO reclamos permitidos.** Un bioestimulante es un producto que estimula procesos de nutrición de la planta con independencia del contenido de nutrientes del producto, con el único objetivo de mejorar una o más de estas características de la planta o de su rizosfera:

1. **Eficiencia en el uso de nutrientes**
2. **Tolerancia al estrés abiótico**
3. **Características de calidad**
4. **Disponibilidad de nutrientes confinados en el suelo o la rizosfera**

⚠️ La **redacción textual exacta** debe tomarse de EUR-Lex antes de reproducirla en un documento comercial → §9, NV-26.

**Lo que NO se puede reclamar — y es la frontera decisiva.** La definición dice **estrés ABIÓTICO**. En el momento en que un producto reclama efecto sobre **plagas o enfermedades** (estrés **biótico**), sale del Reg. 2019/1009 y entra en el **Reglamento (CE) 1107/2009 de productos fitosanitarios**, cuyo régimen de registro es incomparablemente más caro y exigente.

**Consecuencia directa para §6.1:** el quitosano, cuyo mecanismo demostrado es **elicitación de defensa antifúngica vía CERK1**, es un producto cuyo mecanismo real lo empuja hacia fitosanitario mientras su etiqueta lo mantiene en bioestimulante. Es una tensión estructural, no un detalle.

⚠️ Pendientes de verificación: lista taxonómica exacta de microorganismos admitidos en PFC 6(A); **valores límite numéricos de contaminantes** (Cd, Cr VI, Cr total, Pb, Hg, Ni, As inorgánico, Cu, Zn, biuret, perclorato, *Salmonella*, *E. coli*) para PFC 6; módulos de evaluación de la conformidad; normas CEN/TC 455. → §9, NV-27.

### 7.2 Brasil — MAPA

Marco: **Lei 6.894/1980**, **Decreto 4.954/2004**, e **Instrução Normativa nº 61/2020** del MAPA, que consolidó las reglas sobre fertilizantes, correctivos, inoculantes y **biofertilizantes**.

Categorías del sistema brasileño: fertilizante mineral, organomineral, orgânico, condicionador de solo, substrato para plantas, **biofertilizante**, remineralizador.

**El punto que hay que verificar y que decide todo el registro:** en Brasil los productos de **aminoácidos** y de **ácidos húmicos** históricamente **no se registran como "bioestimulante"** sino como **fertilizante orgánico** o **condicionador de solo**, con **garantías mínimas** exigidas (% de carbono orgánico, % de ácidos húmicos, % de aminoácidos libres) y **tolerancias** definidas.

**Lo crítico y no verificado:** el **método analítico oficial** que MAPA acepta para ácidos húmicos y fúlvicos (Manual de Métodos Analíticos Oficiais para Fertilizantes e Corretivos). **Esto se conecta directamente con §4.3:** si MAPA prescribe un método y la UE otro, el mismo producto declara **cifras distintas y ambas legales** en los dos mercados. Es la prueba práctica de la no comparabilidad. → §9, NV-28.

⚠️ Pendiente: si IN 61/2020 sigue vigente o fue modificada; garantías mínimas numéricas; si MAPA exige ensayos de eficacia agronómica para registro. → §9, NV-28.

### 7.3 Bolivia — SENASAG

El **SENASAG** (Servicio Nacional de Sanidad Agropecuaria e Inocuidad Alimentaria) registra insumos agrícolas. Los bioestimulantes se encuadran en el registro de **fertilizantes y enmiendas** o de **coadyuvantes**.

⚠️ **No se pudo verificar en esta sesión** si existe normativa boliviana **específica de bioestimulantes** (distinta del registro genérico de fertilizantes), ni el número de resolución administrativa aplicable, ni los requisitos documentales y analíticos. **Se deja constancia de que NO se verificó y NO se inventa un número de resolución.** → §9, NV-29.

**Nota práctica que sí se puede sostener:** en ausencia de una categoría legal específica, el registro boliviano de un bioestimulante depende de bajo qué figura se lo presente. Esto significa que **la etiqueta boliviana puede reclamar cosas que la etiqueta europea del mismo producto no puede**. Al evaluar un producto importado, **pedir la ficha técnica del país de origen**, no la traducción local.

### 7.4 Estados Unidos

**No existe categoría federal de bioestimulante.** El registro es **estado por estado**, vía **AAPFCO** (*Association of American Plant Food Control Officials*). La **Farm Bill 2018** introdujo una definición de bioestimulante y encomendó un informe federal, pero **no creó un régimen de registro federal**. La consecuencia es que un producto puede estar registrado en un estado y no en otro, con etiquetas distintas. ⚠️ Texto exacto de la definición y estado actual del proceso EPA/USDA → §9, NV-30.

### 7.5 Cómo se registra realmente un bioestimulante — lectura transversal

De lo verificado, el patrón es claro y vale como criterio de compra:

1. **En ningún régimen conocido el registro exige demostrar el efecto biológico reclamado con ensayos de campo independientes** con el rigor que exige un fitosanitario. La UE exige cumplir criterios de **seguridad** (contaminantes, patógenos) y de **conformidad de composición**; la eficacia se demuestra ante el mercado, no ante el regulador, salvo requisitos puntuales.
2. Por lo tanto: **"producto registrado" NO significa "producto que funciona".** Significa "producto que no supera los límites de contaminantes y declara lo que contiene".
3. El único filtro real de eficacia es **el ensayo propio con testigo y repeticiones**.

---

## 8. TAMAÑO DE EFECTO REAL

Esta es la sección que decide si el rubro entero merece plata o no.

### 8.1 El meta-análisis de referencia

> **Li, J., Van Gerrewey, T. & Geelen, D. (2022).** *A Meta-Analysis of Biostimulant Yield Effectiveness in Field Trials*. **Frontiers in Plant Science 13: 836702**. DOI **10.3389/fpls.2022.836702** ✅ verificado.
>
> **180 estudios · 1.087 observaciones pareadas** (de 1.108 originales, 21 removidas por outliers). **Solo ENSAYOS DE CAMPO** — no maceta, no hidroponía. Esto lo hace el meta-análisis más relevante del dossier.

### 8.2 Efecto medio por categoría

| Categoría | Efecto medio sobre rendimiento | IC 95 % |
|---|---|---|
| Extractos vegetales (PE) | **+26,6 %** | 23,1 – 30,1 |
| Extracto de hoja de moringa (MLE) | **+30,8 %** | 26,1 – 35,6 |
| **Extractos de algas (SWE)** | **+17,1 %** | 14,4 – 19,8 |
| **Húmicos y fúlvicos (HFA)** | **+16,5 %** | 13,7 – 19,3 |
| **Hidrolizados proteicos (PH)** | **+16,0 %** | 13,4 – 18,6 |
| **Quitosano (Chi)** | **+14,8 %** | 11,8 – 17,8 |
| Silicio (Si) | **~+15 %** | *la mayor variabilidad de todas* |
| Fosfito (Phi) | **+8,6 %** | 4,6 – 12,5 |
| **PROMEDIO GENERAL** | **+17,9 %** | **16,7 – 19,0** |

### 8.3 Heterogeneidad — el número que hay que mirar antes que la media

**En todos los modelos evaluados: prueba de heterogeneidad significativa (p < 0,001) e I² ≥ 75 %**, lo que por convención implica **heterogeneidad sustancial**.

**Cómo se lee esto, sin adornos:** un I² ≥ 75 % significa que **la mayor parte de la variación entre estudios NO es error de muestreo, es variación real de efecto**. La media de +17,9 % **no es lo que va a pasar en el lote del cliente**. Es el centro de una distribución ancha que incluye ensayos con efecto nulo y con efecto negativo. **Citar la media sin citar el I² es el error metodológico más frecuente del marketing técnico de este rubro.**

### 8.4 Sesgo de publicación

Reportado por los autores: **la prueba de asimetría no fue significativa (p > 0,05)**, por lo que **no identificaron problemas de sesgo de publicación** en su conjunto de datos.

⚠️ **Reserva escéptica, que corresponde declarar:** la ausencia de asimetría en el funnel plot es **evidencia débil de ausencia de sesgo**, especialmente con I² ≥ 75 %, porque la heterogeneidad alta reduce el poder de las pruebas de asimetría. No es una absolución.

**Y hay un dato interno del propio trabajo que apunta en la dirección contraria y que es el hallazgo más incómodo de todo el dossier:**

> **Productos NO comercializados: +21,8 % (IC 20,0–23,5)**
> **Productos comprados comercialmente: +14,4 % (IC 12,7–16,0)**

Los productos **experimentales, no vendidos**, rindieron **más de 7 puntos porcentuales por encima** de los productos que efectivamente se compran en el mercado, **con intervalos de confianza que no se solapan**. La interpretación más sobria: hay un componente de **efecto del experimentador / entusiasmo del desarrollador** en la literatura, y **el producto que el productor realmente compra rinde menos que el promedio del rubro**. El número que corresponde usar para un cliente que va a comprar un producto comercial es **+14,4 %, no +17,9 %**.

### 8.5 LA OBSERVACIÓN CLAVE: ¿el efecto aparece bajo estrés y desaparece en condiciones óptimas?

**SÍ. Está confirmado y cuantificado.** Este es el hallazgo más importante del dossier, y sobrevive a todas las objeciones metodológicas anteriores porque es un patrón **interno y consistente** de los subgrupos.

Conclusión textual del trabajo: **los bioestimulantes son más eficientes en suelos con bajo contenido de materia orgánica, no neutros, salinos, deficientes en nutrientes y arenosos.**

Desglose verificado:

| Factor | Hallazgo |
|---|---|
| **Clima** | El efecto fue **máximo en climas con disponibilidad de agua seriamente limitada (árido y desértico)**; el clima **totalmente húmedo fue el MENOS favorable** para la eficiencia del bioestimulante |
| **Materia orgánica del suelo** | **Tendencia negativa robusta** entre MO y respuesta al bioestimulante → **cuanto más pobre el suelo, mayor el efecto** |
| **Salinidad** | **Fuertemente correlacionada en positivo** con la efectividad |
| **Estado nutricional** | Funcionan **mejor en suelos pobres, deficientes en P y K**, y con **bajo N disponible** |
| **pH del suelo** | Acidez o alcalinidad **moderadas** fueron mejores que pH neutro o que extremos. **Alcalino moderado = máxima respuesta potencial** |
| **Textura** | Arcilla pura: **+13,5 %** · Franco arcillo-limoso: **+26,3 %** |
| **Vía de aplicación** | **Suelo: +28,8 % (IC 24,0–33,6)** ≫ foliar ~+17,0 % ≈ semilla ~+17,0 % |
| **Cultivo** | **Hortalizas +22,8 %** (máximo) · leguminosas > cereales y frutales · **raíces y tubérculos +10,6 %** (mínimo) |
| **Frecuencia** | Una sola aplicación: **+14,9 % (IC 12,3–17,6)**; **rendimientos decrecientes más allá de 4 aplicaciones (11,3–14,3 %)** |

**Confirmación independiente en húmicos:** Ma et al. (2024), DOI 10.3390/agronomy14122763, encontraron el mismo patrón en su dominio: mejor respuesta con **bajo nivel de nitrógeno**, y **efectividad REDUCIDA en condiciones de alto nitrógeno y suelos alcalinos**.

**Confirmación independiente en algas:** el cuerpo de meta-análisis de algas (§3.3) muestra efectos consistentes específicamente **bajo salinidad y sequía**.

**Las cinco consecuencias comerciales de esto — que es lo que hay que llevarse:**

1. **El bioestimulante compite con la corrección del limitante, no lo complementa.** En un suelo con MO baja, P y K deficientes y pH desviado, lo que hay que corregir es el suelo. El bioestimulante rinde mucho **precisamente ahí**, es decir, **donde hay una solución agronómica mejor y más barata disponible**.
2. **En el lote bien manejado — buena MO, nutrición adecuada, riego, pH neutro — el efecto esperado es el más bajo del rango.** Es exactamente el cliente que más paga.
3. **Aplicar al SUELO rinde casi el doble que foliar (+28,8 % vs +17,0 %)**, y sin embargo casi todo el rubro de aminoácidos se vende como foliar. Vale la pena revisar el modo de aplicación antes que el producto.
4. **Más aplicaciones NO es mejor.** El rendimiento decrece pasadas 4 aplicaciones. Los programas de 6–8 aplicaciones por campaña no tienen respaldo en estos datos.
5. **El número honesto para un producto comercial comprado es +14,4 %, con I² ≥ 75 %** — es decir, con una probabilidad no despreciable de efecto nulo en un lote individual. **Todo esto debe ir contra el costo del producto en la misma planilla.**

---

## 9. TABLA "NO VERIFICADO"

Ítems que se buscaron y NO se pudieron verificar en esta sesión. **No se inventó ninguno de estos datos.** Causas dominantes: agotamiento del presupuesto de búsqueda web (200/200) y fallas de red repetidas (`ECONNRESET`, `socket hang up`) contra MDPI, ScienceDirect, Tandfonline, PMC y parte de Frontiers.

| ID | Qué se buscaba | Qué se buscó | Estado |
|---|---|---|---|
| NV-01 | Porcentaje cuantitativo de racemización L→D en hidrólisis ácida de hidrolizados fertilizantes | Búsqueda de racemización en hidrolizados proteicos; trabajos de Cavani & Ciavatta | Confirmado **cualitativamente** por Colla 2017 ("muchos aminoácidos convertidos de L a D"). **Sin porcentaje verificado.** No se reporta cifra |
| NV-02 | Evidencia de que la forma D es **antagonista** (no solo inerte) y su magnitud | Búsqueda de D-aminoácidos como inhibidores competitivos de transportadores vegetales | Sin cita verificada. Reportado como hipótesis, no como hecho |
| ~~NV-03~~ | ~~DOI del método LC-MS/MS con hidrólisis en ácido deuterado para D/L~~ | Crossref | ✅ **RESUELTO**: Danielsen, M. et al. (2020), Foods 9: 309, **10.3390/foods9030309** |
| NV-04 | DOI de AOAC Final Action 2018.06 y confirmación de AOAC 994.12 / 985.28 / 988.15 | Búsqueda de métodos AOAC de aminoácidos libres y totales | Métodos identificados por número vía fuentes secundarias; **DOIs y textos oficiales no verificados**. AOAC 988.15 (Trp por hidrólisis alcalina) **mencionado de memoria, NO verificado — no usar sin confirmar** |
| NV-05 | Paper que proponga formalmente la **hidroxiprolina** como marcador de autenticación de origen colágeno en fertilizantes | Búsqueda de marcadores de origen en hidrolizados | Sin cita. Se presenta como razonamiento bioquímico, no como método publicado |
| NV-06 | Cita exacta del límite de **2 mg/kg de Cr(VI)** en fertilizante orgánico (UE y Brasil) | Localizado en Microchemical Journal (S0026265X2033006X) | Valor localizado, **DOI y artículo/anexo legal exactos sin verificar** |
| NV-07 | DOI de *On the Determination of Cr(VI) in Cr(III)-Rich Particulates* (PMC9564694) | Localizado por PMC ID | DOI pendiente |
| NV-08 | **Meta-análisis de glicina betaína** con efecto medio e IC | Búsqueda específica de meta-análisis de GB foliar y rendimiento | **No se localizó ninguno.** Solo ensayos individuales y revisiones narrativas |
| NV-09 | DOI de la revisión Frontiers 2025 sobre glicina betaína | Localizada por URL | Pendiente |
| ~~NV-10~~ | ~~DOIs de las dos revisiones de ALA~~ | Crossref | ✅ **RESUELTO**: Akram 2013, J Plant Growth Regul 32:663–679; Wu 2018, Plant Growth Regul 87:357–374 |
| NV-11 | Ensayos de **campo** con rendimiento para ALA; meta-análisis de ALA | Búsqueda de ALA en agricultura | **No se localizó ninguno.** Toda la evidencia hallada es nivel C |
| NV-12 | Meta-análisis de algas Pérez-Oñate 2026: IC 95 %, I², sesgo, desglose por método de extracción y por condición de estrés | 3 intentos de fetch a Frontiers | **DOI, autores, revista y volumen ✅ VERIFICADOS vía Crossref.** Los **números internos** no se pudieron extraer por falla de red repetida. Solo se dispone del ~16 % y de la mayor estabilidad de *A. nodosum* |
| NV-13 | Efectos medios con IC del meta-análisis de algas y salinidad en cereales | Crossref | ✅ **DOI RESUELTO**: Nuruzzaman et al. 2025, Plant-Environment Interactions 6, **10.1002/pei3.70094**. **Efectos medios e IC del texto completo NO extraídos** |
| NV-14 | Contenido porcentual típico de ácidos húmicos por materia prima (leonardita / turba / lignito) | Investigación paralela bloqueada por límite de concurrencia | **No verificado. No se reportan porcentajes** |
| NV-15 | **Número de método oficial AOAC** correspondiente al método de Lamar, y estado First/Final Action | Crossref (paper verificado); número de método no localizado | Pendiente |
| NV-16 | **MAGNITUD NUMÉRICA de la divergencia entre métodos analíticos de AH** (factor de sobreestimación del gravimétrico) | Búsqueda de estudios comparativos, rondas AOAC, HPTA | **NO VERIFICADO. Es el dato más importante que falta en §4.3.** El argumento cualitativo se sostiene; el número no existe en este documento porque no se pudo verificar |
| NV-17 | DOIs de Canellas / Nardi / Piccolo sobre H⁺-ATPasa y actividad auxínica de húmicos | Crossref | ✅ **RESUELTO PARCIALMENTE**: Canellas 2002 (10.1104/pp.007088), Zandonadi 2006 (10.1007/s00425-006-0454-2) y Zandonadi 2010 (10.1007/s00425-010-1106-0) verificados. **Nardi y Piccolo NO localizados** por esta vía |
| NV-18 | **Valores numéricos de Rose et al. 2014**: % de aumento de biomasa aérea y radicular, IC, n | Crossref (sin abstract), ScienceDirect (ECONNRESET), Monash (ECONNRESET), ouci.dntb.gov.ua (dominio bloqueado) | **DOI y conclusión cualitativa verificados; números NO** |
| NV-19 | IC 95 %, I² y sesgo de publicación de Ma et al. 2024 | 2 intentos de fetch a MDPI | **Falla de red.** Solo se recuperaron los valores puntuales del abstract vía Crossref |
| NV-20 | Alcance exacto de **EN 13366** y de cada parte de **EN 13368** | Investigación paralela bloqueada; presupuesto de búsqueda agotado | Pendiente |
| NV-21 | **Umbrales porcentuales** del Reg. UE 2019/1009 para declarar un micronutriente como quelado; lista de quelantes autorizados por nombre | Ídem | Pendiente |
| NV-22 | Cita para la afirmación de que el lignosulfonato no tiene constante termodinámica definida | Búsqueda de constantes de lignosulfonato | Sin cita. Presentado como razonamiento químico |
| NV-23 | **CONSTANTES DE ESTABILIDAD (log K) de glicina, glutámico, aspártico, citrato, gluconato/glucoheptonato, lignosulfonato, EDTA, DTPA, EDDHA con Zn²⁺/Fe³⁺/Fe²⁺/Mn²⁺/Cu²⁺/Ca²⁺** | NIST SRD 46, IUPAC SC-Database, Martell & Smith; intento de fetch a Tandfonline (ECONNRESET) y a PMC6259637 (socket hang up); presupuesto de búsqueda agotado | **NO VERIFICADO — NINGÚN VALOR.** Único dato relacionado recuperado, de fuente secundaria y por lo tanto **no citable**: citrato con Fe³⁺ ~11,85, con Ca²⁺ ~3,5, con Fe²⁺ ~3,2; EDTA con Ca²⁺ 10,65, Co²⁺ 16,45, Cd²⁺ 16,5, Al³⁺ 16,4. **§5 se escribió deliberadamente SIN tabla de constantes.** Es la laguna más grave del dossier y debe cerrarse antes de usarlo en una discusión técnica |
| NV-24 | Evidencia comparativa con repeticiones **aminoquelato vs EDTA vs sulfato** (Zn y Fe, foliar y suelo); trabajos de Fernández & Brown sobre absorción foliar | Presupuesto de búsqueda agotado | **NO VERIFICADO.** §5.5 declara la pregunta como abierta. **Vía identificada para cerrarla:** Montalvo, D. et al. (2016), *Agronomic Effectiveness of Zinc Sources as Micronutrient Fertilizer*, Advances in Agronomy, DOI **10.1016/bs.agron.2016.05.004** — existencia verificada vía Crossref, contenido no leído. Pistas adicionales para el mecanismo de penetración cuticular (existencia verificada, contenido no leído): Baker, E.A. (1992), *Physicochemical properties of agrochemicals: Their effects on foliar penetration*, Pesticide Science, DOI 10.1002/ps.2780340212; Chamel, A. (1980), *Foliar penetration of micronutrients: study with isolated pear leaf cuticles*, DOI 10.1016/b978-0-408-10662-7.50058-2. **No se localizaron los trabajos de Fernández & Brown por esta vía** |
| NV-25 | DOIs de CERK1 (PubMed 18042724, PMC2937917, bioRxiv 170092, PMC12645901) | Localizados por PMID/PMC ID | Pendientes |
| NV-26 | Texto TEXTUAL de los cuatro reclamos del Reg. UE 2019/1009 (EUR-Lex) | Investigación paralela en curso al cierre | Pendiente |
| NV-27 | UE: lista taxonómica de PFC 6(A); **límites numéricos de contaminantes** para PFC 6; módulos de conformidad; normas CEN/TC 455 | Ídem | Pendiente |
| NV-28 | Brasil: vigencia de IN 61/2020; garantías mínimas numéricas; **método analítico oficial de MAPA para AH y AF**; exigencia de ensayos de eficacia | Ídem | Pendiente. **El método oficial de MAPA es clave para §4.3** |
| NV-29 | **Bolivia/SENASAG:** existencia de normativa específica de bioestimulantes, número de resolución, requisitos | Ídem | **NO VERIFICADO. No se inventa ningún número de resolución** |
| NV-30 | EE.UU.: texto de la definición de la Farm Bill 2018; estado del proceso EPA/USDA | Ídem | Pendiente |
| **NV-31** | **Contenido de Cavani et al. 2006, *Photosensitizing Properties of Protein Hydrolysate-Based Fertilizers*, JAFC 54: 9160–9167, DOI 10.1021/jf0624953** | Crossref | **Existencia ✅ verificada, CONTENIDO NO LEÍDO.** Riesgo potencial de fitotoxicidad foliar por fotosensibilización. **Prioridad alta**: afecta la recomendación de horario de aplicación foliar |

---

## 10. LO QUE NO SE PUEDE

El cierre del dossier. Cada punto con su número.

### 10.1 NO aporta nutrición significativa a las dosis de uso — la aritmética

Este es el argumento que termina la discusión, y se hace con una calculadora.

**Caso 1 — Aminoácidos, aporte de nitrógeno.**

Producto típico: **10 % p/v de aminoácidos libres**. Dosis alta y generosa: **5 L/ha**.

- Aminoácidos aportados: 5 L/ha × 100 g/L = **500 g/ha**
- Contenido de N de una mezcla de aminoácidos: **~15 %** (glicina 18,7 % N; ácido glutámico 9,5 % N; promedio proteico ~16 %)
- **N aportado: 500 × 0,15 = 75 g N/ha = 0,075 kg N/ha**

Contra la demanda de un cultivo de trigo de rendimiento medio: **~150 kg N/ha**.

> **0,075 / 150 = 0,05 %.**
> **El bioestimulante de aminoácidos cubre CINCO CENTÉSIMAS DE UNO POR CIENTO de la demanda de nitrógeno del cultivo.**

Dicho al revés: para reemplazar **1 kg de N de urea** con ese producto harían falta **≈ 67 litros por hectárea**.

**Caso 2 — Aminoácidos, aporte de carbono al suelo.**

- Carbono aportado: 500 g/ha × ~45 % C = **225 g C/ha = 0,225 kg C/ha**
- Stock de carbono orgánico en los primeros 20 cm de un suelo con 2 % de MO: ~2.400 t de suelo/ha × 2 % = 48 t MO/ha ≈ **28 t C/ha = 28.000 kg C/ha**

> **0,225 / 28.000 = 0,0008 %.** Es decir, **8 partes por millón del stock de carbono del suelo.**
> Cualquier reclamo de "mejora la materia orgánica del suelo" a estas dosis es **aritméticamente imposible**.

**Caso 3 — Ácidos húmicos.**

Producto de **15 % de ácidos húmicos**, dosis **5 L/ha** → **750 g AH/ha = 0,75 kg/ha**.

> Contra 48.000 kg de MO/ha: **0,0016 %.** Del mismo orden que el caso 2.

**Caso 4 — Extracto de algas, aporte de potasio.**

Producto con **5 % K₂O**, dosis **2 L/ha** → **100 g K₂O/ha**. Contra una demanda de 100–200 kg K₂O/ha:

> **0,05 – 0,1 %.**

**Conclusión de la aritmética:** si un bioestimulante funciona, **NO funciona por lo que aporta**. Funciona — cuando funciona — por **señalización a dosis sub-nutricionales**. Cualquier proveedor que justifique el precio por el contenido de N, C, K o micronutrientes está vendiendo el fertilizante más caro del mercado por varios órdenes de magnitud.

**Corolario de compra:** el precio de un bioestimulante hay que juzgarlo **contra el aumento de rendimiento esperado (§8.4: +14,4 % para producto comercial, con I² ≥ 75 %)**, nunca contra su composición.

### 10.2 NO sustituye la fertilización

Se sigue de 10.1 con la misma aritmética: **0,05 %** de la demanda de N. Pero además hay evidencia directa en la otra dirección:

- Ma et al. 2024: la respuesta a húmicos es **mayor con bajo N** y **REDUCIDA en condiciones de alto N**. El bioestimulante actúa sobre la **eficiencia de uso** del nutriente (**NUE +27 %**), no sobre su **provisión**.
- Li et al. 2022: los bioestimulantes funcionan mejor en suelos **deficientes en P y K y con bajo N disponible**.

**La lectura correcta de ese patrón es la contraria a la que hace el marketing.** El marketing dice: "responde bien en suelos pobres, entonces sirve para suelos pobres". Lo que dice el dato es: **el bioestimulante rinde donde hay un limitante nutricional sin corregir** — es decir, **donde existe una solución más barata, más predecible y más grande, que es corregir el limitante**. El bioestimulante captura una fracción del *gap*; la fertilización lo cierra.

### 10.3 El efecto es VARIABLE y DEPENDIENTE DE ESTRÉS — con números

- **I² ≥ 75 %, p < 0,001** en todos los modelos de Li et al. 2022 → **heterogeneidad sustancial**. La mayor parte de la variación entre ensayos es **variación real de efecto**, no ruido de muestreo. **La media no predice el lote.**
- Rango documentado por textura: **+13,5 % (arcilla pura) a +26,3 % (franco arcillo-limoso)** — casi el doble, solo por textura.
- Rango por cultivo: **+10,6 % (raíces y tubérculos) a +22,8 % (hortalizas)**.
- Clima: **máximo en árido y desértico, MÍNIMO en clima totalmente húmedo.**
- MO del suelo: **tendencia negativa robusta** — a más MO, menos efecto.
- Rose et al. 2014 lo dice para húmicos en una frase que vale para toda la categoría: la magnitud de la promoción del crecimiento es **inconsistente y relativamente impredecible en comparación con los fertilizantes inorgánicos**.

**Traducción para un cliente:** *"En un lote bien manejado, con buena materia orgánica, nutrición completa y sin estrés hídrico ni salino, el efecto esperado de este producto está en el extremo bajo del rango publicado, y la probabilidad de no medir diferencia contra el testigo no es despreciable."* Eso es lo que dicen los datos, y es lo que hay que decir.

### 10.4 NO protege contra plagas y enfermedades (legalmente y en la mayoría de los casos, materialmente)

La definición legal de bioestimulante de la UE dice **estrés ABIÓTICO**. Reclamar efecto sobre estrés **biótico** convierte al producto en **fitosanitario** bajo Reg. (CE) 1107/2009.

Caso incómodo documentado: el **quitosano** tiene un mecanismo de **elicitación de defensa antifúngica vía CERK1** experimentalmente demostrado. Es decir, **el producto cuyo mecanismo mejor documentado es de defensa es el que legalmente no puede reclamarlo**. Cuando un vendedor insinúa efecto sanitario de un bioestimulante, está (a) fuera de la ley del régimen europeo, y (b) sin el paquete de eficacia y residuos que ese reclamo exigiría.

### 10.5 NO es comparable entre productos por la etiqueta

Cuatro fallas de comparabilidad **estructurales**, no accidentales:

1. **Aminoácidos:** "libres" vs "totales" son cifras distintas por un factor que puede ser grande, y la etiqueta rara vez dice cuál declara (§1.3).
2. **Aminoácidos:** el proceso (ácido vs enzimático) determina la relación L/D y la presencia de Trp/Cys, y **no se declara** (§1.1).
3. **Ácidos húmicos:** el "%" **depende del método analítico** y no hay un método universal. Dos etiquetas con el mismo número pueden no medir lo mismo, y dos números distintos pueden corresponder al mismo producto (§4.3).
4. **Extractos de algas:** el método de extracción cambia la composición del extracto, y **no se declara** (§3.2).

**Consecuencia:** comparar dos etiquetas de bioestimulantes es, en el estado actual del mercado, **una operación sin significado**. Lo único comparable es **el ensayo propio con testigo**.

### 10.6 "Registrado" NO significa "eficaz"

El registro verifica **seguridad** (contaminantes, patógenos) y **conformidad de composición**. **No verifica el efecto agronómico reclamado** con el estándar que se le exige a un fitosanitario (§7.5). Un número de registro no es evidencia de eficacia.

### 10.7 Y una advertencia sobre la literatura misma

En el meta-análisis de campo más grande disponible, los productos **no comercializados** rindieron **+21,8 % (IC 20,0–23,5)** y los **comprados comercialmente** **+14,4 % (IC 12,7–16,0)** — **intervalos que no se solapan**. La literatura del rubro es, en promedio, **más optimista que el producto que el productor efectivamente compra**. Ese descuento hay que aplicarlo antes de leer cualquier número de este dossier.

---

## Referencias con DOI verificado contra Crossref

1. Colla, G., Hoagland, L., Ruzzi, M., Cardarelli, M., Bonini, P., Canaguier, R. & Rouphael, Y. (2017). *Biostimulant Action of Protein Hydrolysates: Unraveling Their Effects on Plant Physiology and Microbiome*. Frontiers in Plant Science 8: 2202. **10.3389/fpls.2017.02202**
2. Colla, G., Rouphael, Y., Canaguier, R., Svecova, E. & Cardarelli, M. (2014). *Biostimulant action of a plant-derived protein hydrolysate produced through enzymatic hydrolysis*. Frontiers in Plant Science 5. **10.3389/fpls.2014.00448**
3. Zhao et al. (2022). *Toxicity evaluation of collagen hydrolysates from chrome shavings and their potential use in the preparation of amino acid fertilizer for crop growth*. Journal of Leather Science and Engineering 4. **10.1186/s42825-021-00072-1**
4. Hosseinifard, M. et al. (2022). *Contribution of Exogenous Proline to Abiotic Stresses Tolerance in Plants: A Review*. Int. J. Mol. Sci. 23(9): 5186. **10.3390/ijms23095186**
5. Shukla, P.S. et al. (2019). *Ascophyllum nodosum-Based Biostimulants...*. Frontiers in Plant Science 10: 655. **10.3389/fpls.2019.00655**
6. Deolu-Ajayi, A.O. et al. (2022). *The power of seaweeds as plant biostimulants to boost crop production under abiotic stress*. Plant, Cell & Environment 45: 2537–2553. **10.1111/pce.14391**
7. Lamar, R.T., Olk, D.C., Mayhew, L. & Bloom, P.R. (2014). *A New Standardized Method for Quantification of Humic and Fulvic Acids in Humic Ores and Commercial Products*. J. AOAC Int. 97(3): 721–730. **10.5740/jaoacint.13-393**
8. Lamar, R., Olk, D.C., Mayhew, L. & Bloom, P.R. (2012). *Evaluation of a Proposed Standardized Analytical Method...*. En: Functions of Natural Organic Matter in Changing Environment, 1071–1073. **10.1007/978-94-007-5634-2_198**
9. Lamar, R.T. & Monda, H. (2022). Protocolo en video. Journal of Visualized Experiments. **10.3791/61233**
10. Olk, D.C. et al. (2019). *Environmental and Agricultural Relevance of Humic Fractions Extracted by Alkali from Soils and Natural Waters*. J. Environ. Qual. 48: 217–232. **10.2134/jeq2019.02.0041** (erratum: 10.2134/jeq2019.02.0041er)
11. Lehmann, J. & Kleber, M. (2015). *The contentious nature of soil organic matter*. Nature 528: 60–68. **10.1038/nature16069**
12. Rose, M.T., Patti, A.F., Little, K.R., Brown, A.L., Jackson, W.R. & Cavagnaro, T.R. (2014). *A Meta-Analysis and Review of Plant-Growth Response to Humic Substances*. Advances in Agronomy 124: 37–89. **10.1016/B978-0-12-800138-7.00002-4**
13. Ma, Y., Cheng, X. & Zhang, Y. (2024). *The Impact of Humic Acid Fertilizers on Crop Yield and Nitrogen Use Efficiency: A Meta-Analysis*. Agronomy 14: 2763. **10.3390/agronomy14122763**
14. Li, J., Van Gerrewey, T. & Geelen, D. (2022). *A Meta-Analysis of Biostimulant Yield Effectiveness in Field Trials*. Frontiers in Plant Science 13: 836702. **10.3389/fpls.2022.836702**
15. Coskun, D. et al. (2019). *The controversies of silicon's role in plant biology*. New Phytologist 221: 67–85. **10.1111/nph.15343**
16. Álvarez-Fernández, A., Hernández-Apaolaza, L., Lucena, J.J. et al. (2005). *Evaluation of synthetic iron(III)-chelates (EDDHA/Fe³⁺, EDDHMA/Fe³⁺ and the novel EDDHSA/Fe³⁺) to correct iron chlorosis*. European Journal of Agronomy 22: 119–130. **10.1016/j.eja.2004.02.001**
17. Hernández-Apaolaza, L., Lucena, J.J. et al. (1995). *Efficacy of commercial Fe(III)-EDDHA and Fe(III)-EDDHMA chelates to supply iron to sunflower and corn seedlings*. Journal of Plant Nutrition 18: 1209–1223. **10.1080/01904169509364973**
18. Akram, M. et al. (2013). *Regulation in Plant Stress Tolerance by a Potential Plant Growth Regulator, 5-Aminolevulinic Acid*. Journal of Plant Growth Regulation 32: 663–679. **10.1007/s00344-013-9325-9**
19. Wu, Y. et al. (2018). *5-Aminolevulinic acid (ALA) biosynthetic and metabolic pathways and its role in higher plants: a review*. Plant Growth Regulation 87: 357–374. **10.1007/s10725-018-0463-8**
20. Pérez-Oñate et al. (2026). *Crop yield responses to seaweed extract-based biostimulants depend on application strategy, formulation, and extraction methods: a meta-analysis*. Frontiers in Plant Science 17. **10.3389/fpls.2026.1803269**
21. Canellas, L.P. et al. (2002). *Humic Acids Isolated from Earthworm Compost Enhance Root Elongation, Lateral Root Emergence, and Plasma Membrane H⁺-ATPase Activity in Maize Roots*. Plant Physiology 130: 1951–1957. **10.1104/pp.007088**
22. Zandonadi, D.B. et al. (2006). *Indolacetic and humic acids induce lateral root development through a concerted plasmalemma and tonoplast H⁺ pumps activation*. Planta 225: 1583–1595. **10.1007/s00425-006-0454-2**
23. Zandonadi, D.B. et al. (2010). *Nitric oxide mediates humic acids-induced root development and plasma membrane H⁺-ATPase activation*. Planta 231: 1025–1036. **10.1007/s00425-010-1106-0**
24. Nuruzzaman, Md. et al. (2025). *Seaweed Extracts Improve Salinity Tolerance in Cereal Crops—A Meta-Analysis*. Plant-Environment Interactions 6. **10.1002/pei3.70094**
25. Danielsen, M. et al. (2020). *Simultaneous Determination of L- and D-Amino Acids in Proteins: A Sensitive Method Using Hydrolysis in Deuterated Acid and Liquid Chromatography–Tandem Mass Spectrometry Analysis*. Foods 9: 309. **10.3390/foods9030309**

**Existencia verificada vía Crossref pero CONTENIDO NO LEÍDO** (leads para cerrar §5, no citables como evidencia todavía): Montalvo, D. et al. (2016), *Agronomic Effectiveness of Zinc Sources as Micronutrient Fertilizer*, Advances in Agronomy, **10.1016/bs.agron.2016.05.004**; Baker, E.A. (1992), *Physicochemical properties of agrochemicals: Their effects on foliar penetration*, Pesticide Science, **10.1002/ps.2780340212**; Chamel, A. (1980), *Foliar penetration of micronutrients: study with isolated pear leaf cuticles*, **10.1016/b978-0-408-10662-7.50058-2**.

**Fuentes citadas por identificador PMC/PubMed con DOI pendiente de verificación:** PMC7143715, PMC9823744, PMC3739925, PMC5962685, PMC5578177, PMC10045403, PMC11913015, PMC12560104, PMC9096543, PMC9564694, PMC2937917, PMC12645901, PubMed 18042724, bioRxiv 170092, ScienceDirect S0026265X2033006X y S0098847224002995. Todas están listadas en §9.
