# R2 — QUELATOS SINTÉTICOS PARA FERTILIZANTES
## Dossier de investigación verificado

**Fecha:** 2026-08-16
**Alcance:** agentes quelantes sintéticos para micronutrientes (Fe, Zn, Mn, Cu) en fertilización de suelo, fertirriego y foliar.
**Estándar de evidencia:** cada constante con fuerza iónica, temperatura y fuente. Lo que no pude leer en la fuente primaria está declarado en la sección [NO VERIFICADO](#no-verificado). No se inventó ningún DOI ni ninguna constante.

---

## ÍNDICE

| § | Sección | Estado de la evidencia |
|---|---|---|
| — | [Advertencia de método](#advertencia-de-método--leer-antes-de-usar-cualquier-número) | — |
| 1 | [Constantes de estabilidad (log K)](#1-constantes-de-estabilidad-log-k) | ⚠️ **Parcial** — tabla incompleta, huecos declarados |
| 2 | [Ventana de pH real en suelo](#2-ventana-de-ph-real-de-cada-quelato-en-suelo-) ⭐ | ✅ Buena para Fe · ⚠️ sin curvas numéricas |
| 3 | [Desplazamiento por Ca²⁺ y Mg²⁺](#3-desplazamiento-por-ca-y-mg) | ⚠️ Mecanismo sólido, cuantificación débil |
| 4 | [Isómeros EDDHA o,o vs o,p](#4-isómeros-de-eddha-oo-vs-op--el-vector-de-fraude-) ⭐ | ✅ **Fuerte** |
| 5 | [Marco regulatorio](#5-marco-regulatorio) | ✅ **Fuerte (UE)** · ⚠️ Brasil vía espejos |
| 6 | [Biodegradabilidad y persistencia](#6-biodegradabilidad-y-persistencia-ambiental) | ✅ Buena · ⚠️ sin t½ de EDTA/DTPA |
| 7 | [Quelato vs complejo vs mezcla](#7-quelato-vs-complejo-vs-mezcla) | ✅ Definiciones + criterio operativo |
| 8 | [Costo relativo](#8-costo-relativo-por-kg-de-metal) | ✅ Orden relativo + estequiometría propia |
| — | [**LO QUE NO SE PUEDE**](#lo-que-no-se-puede) | ✅ 8 puntos con evidencia · ⚠️ L9 foliar sin verificar |
| — | [**NO VERIFICADO**](#no-verificado) | Registro completo de lagunas |

### Los cinco hallazgos que más cambian una decisión de compra

1. **Fe-EDTA es inestable a pH 7,3 en suelo** (Norvell & Lindsay 1969). En calcáreo no rinde menos: **se pierde entero**. → §2.2
2. **El Reglamento (UE) 2019/1009 eliminó la lista positiva de quelantes.** Ahora rige un criterio funcional (anillo de 5-6 miembros + estabilidad 3 días en el pH declarado). Ya no basta preguntar "¿está en la lista?". → §5.1
3. **El %o,o del EDDHA es una variable de proceso**: cambiando solo la relación de solventes en el reactor, un mismo esquema produce **0,2 % a 2,7 % de o,o** (Cascone et al. 2015). Es exactamente lo que se recorta para abaratar. → §4.5
4. **El 98,8 % de los Fe-EDDHA/EDDHMA analizados incumplía la ley** y **ninguno** alcanzaba el 6 % declarado (Álvarez-Fernández 2000, n=80). ⚠️ Dato de 1998-2000. → §4.4
5. **Brasil no obliga a declarar el % quelado ni el intervalo de pH** (IN 39/2018); la UE sí. En Brasil hay que **exigirlo por contrato**. → §5.4

---

## ADVERTENCIA DE MÉTODO — leer antes de usar cualquier número

Este dossier se construyó con acceso restringido: **NIST SRD 46 (Martell & Smith) es una base de datos descargable, no una página web consultable**, y buena parte de la literatura primaria (ACS, ScienceDirect, Wiley, PMC) devolvió 403 o bloqueo de red en este entorno.

Consecuencia práctica y honesta: **la tabla de log K de la Sección 1 está incompleta**. Las celdas que pude verificar llevan su fuente y sus condiciones. Las que no, están vacías y listadas en NO VERIFICADO. Preferí una tabla con huecos declarados antes que una tabla completa con números de procedencia desconocida — que es exactamente el defecto que este dossier existe para no cometer.

**Regla de uso:** un log K sin fuerza iónica y temperatura declaradas no es un dato, es una cifra. No lo transcriba a una propuesta comercial.

---

## 1. CONSTANTES DE ESTABILIDAD (log K)

### 1.1 Qué es el número y qué convención usa NIST

Para la reacción M + L ⇌ ML, la constante de formación es K_ML = [ML] / ([M][L]).
Se reporta como **log K** (o log β₁ para el primer complejo).

La referencia crítica es **NIST Standard Reference Database 46 — "Critically Selected Stability Constants of Metal Complexes"**, de **Robert M. Smith y Arthur E. Martell**, digitalización de seis volúmenes publicados entre **1974 y 1989**, con literatura cubierta hasta 1985. Contiene ~6.166 ligandos y 112.559 entradas. Versión final: **8.0**, actualmente discontinuada en su forma original.

Convención declarada por la propia base, y este punto es decisivo:

> "For a given system, values at the published temperature and ionic strength are given."

Es decir: **NIST NO normaliza a una condición única**. Cada constante viene con la T y la I del experimento original. Por eso comparar dos log K de fuentes distintas sin verificar T e I es un error de método, no un detalle.

Criterios de selección de NIST: control y descripción adecuados del método experimental (temperatura, fuerza iónica, naturaleza del electrolito soporte, pureza del ligando, calibración, definición del cociente de equilibrio) y fiabilidad del investigador.

**Fuente:** NIST SRD 46, Smith & Martell. Descripción y convención verificadas en la guía de Equilibrium Data (https://equilibriumdata.github.io/guide/NIST.html) y en la ficha NIST PDR (https://data.nist.gov/od/id/mds2-2154). Interfaz alternativa de consulta desarrollada por Naoyuki Hatada (Universidad de Kioto).

### 1.2 Tabla de constantes verificadas

Celda vacía = **no verificada en fuente identificable**, no "no existe". Ver NO VERIFICADO §A.

| Ligando | Fe³⁺ | Fe²⁺ | Zn²⁺ | Mn²⁺ | Cu²⁺ | Ca²⁺ | Mg²⁺ | I | T | Fuente |
|---|---|---|---|---|---|---|---|---|---|---|
| **o,o-EDDHA** | **35,09** | — | **20,46** | **19,89** | — | — | — | n.d. | n.d. | Yunta et al. 2003; López-Rayo et al. 2012 — vía López-Rayo, Nadal & Lucena 2015 |
| **EDTA** | **25,7** | — | — | — | — | — | — | n.d. | 25 °C | Almubarak & Ng 2024, Tabla 1 |
| **DTPA** | **28,0** | — | — | — | — | — | — | n.d. | 25 °C | Almubarak & Ng 2024, Tabla 1 |
| **HEDTA** (HEEDTA) | **19,8** | — | — | — | — | — | — | n.d. | 25 °C | Almubarak & Ng 2024, Tabla 1 |
| **S,S-EDDS** | — | — | **13,6** | **8,97** | **18,7** | — | — | **0,1** | n.d. | Orama et al. 2002 — vía López-Rayo, Nadal & Lucena 2015 |
| **IDHA** (IDS) | **12,9** | — | **10,2** | **7,26** | — | — | — | n.d. | n.d. | Hyvönen et al. 2003 — vía López-Rayo, Nadal & Lucena 2015 |
| **NTA** (ref. baja) | **15,8** | — | — | — | — | — | — | n.d. | 25 °C | Almubarak & Ng 2024, Tabla 1 |
| **GLDA** | **15,2** | — | — | — | — | — | — | n.d. | 25 °C | Almubarak & Ng 2024, Tabla 1 |
| **Citrato** (ref. baja) | — | — | — | — | — | — | — | — | — | **no verificado** |

**Fuentes de la tabla:**
- **Yunta F., García-Marco S., Lucena J.J. et al. (2003).** *Chelating Agents Related to Ethylenediamine Bis(2-hydroxyphenyl)acetic Acid (EDDHA): Synthesis, Characterization, and Equilibrium Studies of the Free Ligands and Their Mg²⁺, Ca²⁺, Cu²⁺, and Fe³⁺ Chelates.* **Inorganic Chemistry 42** (2003). **DOI 10.1021/ic034333j** (DOI leído en la URL de ACS, no en el PDF). Determinó Ca²⁺ y Mg²⁺ por valoración potenciométrica y Fe³⁺/Cu²⁺ por un método espectrofotométrico nuevo. **Este es el trabajo de referencia para EDDHA y sus isómeros, y contiene los valores de Ca²⁺ y Mg²⁺ que faltan arriba** — no pude acceder al texto completo.
- **López-Rayo S., Nadal P. & Lucena J.J. (2015).** *Reactivity and effectiveness of traditional and novel ligands for multi-micronutrient fertilization in a calcareous soil.* **Frontiers in Plant Science 6: 752.** **DOI 10.3389/fpls.2015.00752**. Texto completo leído.
- **Almubarak T. & Ng C. (2024).** *Chelating Agents in the Oilfield*, IntechOpen. Tabla 1, caption verbatim: **"Stability constants at 77°F (25°C)"**. ⚠️ **La tabla NO declara fuerza iónica** — por la regla de arriba, estos valores son de menor calidad probatoria que los de NIST/Martell y deben verificarse antes de uso comercial.
- **Orama M. et al. (2002)** para EDDS; **Hyvönen H. et al. (2003)** para IDHA — citados en López-Rayo 2015; no leídos en original.

### 1.3 Lo que la tabla ya permite afirmar

Aun incompleta, el orden de magnitud es inequívoco y es lo que importa agronómicamente:

**Fe³⁺: o,o-EDDHA (35,1) ≫ DTPA (28,0) > EDTA (25,7) > HEDTA (19,8) > NTA (15,8) ≈ GLDA (15,2) > IDHA (12,9)**

Diez órdenes de magnitud separan al EDDHA del IDHA frente al Fe³⁺. Ese salto es el que decide si el producto sirve en suelo calcáreo.

**Inversión de selectividad, dato comercialmente relevante:** IDHA y EDDS tienen constantes **bajas** con Fe³⁺ pero razonables con Zn²⁺ y Cu²⁺. Por eso López-Rayo et al. (2015) concluyen que los ligandos nuevos son buenas alternativas **principalmente para fertilizantes de Zn** — no para Fe. Un IDHA-Fe vendido para clorosis férrica en suelo calcáreo es, por termodinámica, un producto mal aplicado.

**Discrepancia a declarar:** el log K de GLDA-Fe³⁺ = 15,2 de Almubarak & Ng convive en la literatura con valores notablemente menores. No pude resolver la discrepancia. Ver NO VERIFICADO §A.4.

### 1.4 Por qué el log K solo no alcanza

El log K es la constante **con el ligando totalmente desprotonado (L^n⁻)**. En suelo real, el ligando compite con:
- **H⁺** (protonación del ligando, dominante a pH bajo),
- **Ca²⁺ y Mg²⁺** (masivos en suelo calcáreo),
- **Fe³⁺** (que en cualquier suelo está tamponado por óxidos férricos).

Lo que gobierna el resultado agronómico es la **constante condicional** a un pH y una composición iónica dados, no el log K de tabla. Esta es exactamente la construcción de Lindsay & Norvell — Sección 2.

---

## 2. VENTANA DE pH REAL DE CADA QUELATO EN SUELO ⭐

**Esta es la sección central del dossier.**

### 2.1 El marco: Lindsay & Norvell

El método por el cual se predice qué queda de un quelato en un suelo es el de Lindsay y Norvell: a partir de las constantes de formación se construyen **diagramas de fracción molar** del ligando repartido entre los cationes competidores (Fe³⁺, Ca²⁺, H⁺, Zn²⁺), asumiendo que **la concentración de Fe³⁺ en solución está controlada por la solubilidad de los óxidos férricos amorfos** del propio suelo.

Ese supuesto es la clave conceptual completa: **el suelo tiene un tampón de Fe³⁺ propio e inagotable**. El quelato no compite contra "nada", compite contra un reservorio.

**Fuentes primarias:**
- **Lindsay W.L. & Norvell W.A. (1969).** *Equilibrium Relationships of Zn²⁺, Fe³⁺, Ca²⁺, and H⁺ with EDTA and DTPA in Soils.* **Soil Science Society of America Journal 33(1).** **DOI 10.2136/sssaj1969.03615995003300010020x**
- **Norvell W.A. & Lindsay W.L. (1969).** *Reactions of EDTA Complexes of Fe, Zn, Mn, and Cu with Soils.* **Soil Science Society of America Journal 33(1).** **DOI 10.2136/sssaj1969.03615995003300010024x**
- **Norvell W.A. (1991).** *Reactions of Metal Chelates in Soils and Nutrient Solutions.* En: **Mortvedt J.J. et al. (eds.), Micronutrients in Agriculture, 2ª ed., SSSA Book Series 4**, cap. 7. **DOI 10.2136/sssabookser4.2ed.c7**
- **Lindsay W.L. (1991).** *Inorganic Equilibria Affecting Micronutrients in Soils.* Mismo volumen, cap. 4. **DOI 10.2136/sssabookser4.2ed.c4**
- **Norvell W.A. (1984).** *Comparison of Chelating Agents as Extractants for Metals in Diverse Soil Materials.* **SSSAJ 48(6).** **DOI 10.2136/sssaj1984.03615995004800060017x**

⚠️ Los DOI anteriores fueron leídos en las URLs de Wiley/SSSA. **Los textos completos devolvieron 403**; el contenido citado abajo proviene de resúmenes y de la literatura que los cita. Ver NO VERIFICADO §B.

### 2.2 El dato duro: Fe-EDTA en suelo

De **Norvell & Lindsay (1969)**, ensayos en suspensión de suelo:

| pH del suelo | Estado del Fe-EDTA |
|---|---|
| 5,7 | **Estable** |
| 6,1 | **Estable** |
| 6,75 | **Moderadamente estable** |
| 7,3 | **Inestable** |
| 7,85 | **Inestable** |

> **"Fe-EDTA a pH 7 ya no existe" — el número con el que respaldarlo:**
> A **pH 7,3 el Fe-EDTA es inestable** en suelo (Norvell & Lindsay 1969). La transición ocurre entre **pH 6,1 (estable) y pH 7,3 (inestable)**, con el punto de quiebre en **pH 6,75**.
> Complementariamente, la extensión de la Universidad de Florida (**UF/IFAS HS1208**, *Understanding and Applying Chelated Fertilizers Effectively Based on Soil pH*) reporta que a **pH 7,5 la estabilidad del Fe quelado con EDTA es 0,025** en una escala 0–1 — es decir, **queda ~2,5 % del Fe quelado; se perdió ~97,5 %**.
> ⚠️ El valor 0,025 proviene de extracto de buscador; **no pude abrir HS1208** (dominio bloqueado). Verificar antes de publicarlo. Ver NO VERIFICADO §B.2.

**Corolario comercial:** en un suelo calcáreo típico (pH 7,4–8,5), **un Fe-EDTA es dinero tirado**. No es que rinda menos: es que la termodinámica lo desarma. El Fe³⁺ del EDTA se sustituye por Ca²⁺ y precipita como óxido férrico.

### 2.3 Fe-DTPA

- Mantuvo Fe soluble efectivamente en **cuatro suelos de pH 5,8 a 7,3**.
- A **pH 7,9**, **más del 13 % del Fe añadido seguía soluble tras 30 días** de reacción en suelo calcáreo.
- Ventana operativa citada de forma recurrente: **hasta pH ~7,5**.

⚠️ Estos valores provienen de resúmenes de búsqueda que los atribuyen a la línea Norvell/Lindsay y a *Reactions of iron chelates in calcareous soil and their relative efficiency in iron nutrition of corn*, **Plant and Soil**, **DOI 10.1007/BF00693111**. **No leí ninguno de los dos originales.** Ver NO VERIFICADO §B.3.

### 2.4 Fe-EDDHA

- Efectivo en un rango de **pH 4 a 9** (atribuido a Norvell 1991).
- En ausencia de iones competidores, **Fe-EDDHA no se afecta hasta pH 9**, frente a **Fe-EDTA que aguanta hasta pH 6**.
- Es el quelato **más estable a pH > 7** y el único recomendable en suelo calcáreo.

### 2.5 Tabla resumen de ventanas de pH (Fe)

| Quelato | pH máximo operativo (Fe) | Calidad de la evidencia |
|---|---|---|
| **Fe-EDTA** | **≈ 6,0–6,5** | **Alta** — Norvell & Lindsay 1969, datos por pH |
| **Fe-HEDTA** | menor que EDTA (log K Fe³⁺ 19,8) | **Baja** — inferido del log K, sin dato de suelo |
| **Fe-DTPA** | **≈ 7,0–7,5** | **Media** — 13 % soluble a pH 7,9 a 30 d, no leído en original |
| **Fe-EDDHA (o,o)** | **≈ 9,0** | **Media-alta** — consenso de múltiples fuentes secundarias |
| **Fe-IDHA / Fe-EDDS** | bajo; **no aptos para calcáreo** | **Media** — inferido de log K Fe³⁺ 12,9 y de López-Rayo 2015 |
| **Fe-citrato / gluconato** | muy bajo | **No verificado** |

**Confirmación agronómica independiente** — ensayo en *Calibrachoa* en sustrato de pH alto: los tres quelatos (EDTA, DTPA, EDDHA) previnieron la clorosis **hasta pH 6,5**; **por encima de pH 7,2 solo el Fe-EDDHA fue efectivo**. Fuente: *Fertigation with Fe-EDTA, Fe-DTPA, and Fe-EDDHA Chelates to Prevent Iron Chlorosis of Sensitive Species in High-pH Soilless Media* (indexado en DOAJ; **no leí el texto completo**).

### 2.6 Zn, Mn y Cu: la ventana es distinta

**Advertencia:** las ventanas de arriba son **para Fe**. No son transferibles a los otros micronutrientes, porque compiten con distintos cationes y su química redox difiere.

- **Zn-EDTA y Cu-EDTA**: en suelos calcáreos **fueron desplazados por Ca²⁺ a medida que subió el pH** (Norvell & Lindsay 1969). Pero a diferencia del Fe, **el Zn²⁺ y el Cu²⁺ no tienen que competir contra un óxido férrico**, por lo que su ventana útil es **más ancha** que la del Fe con el mismo ligando.
- **Mn**: caso aparte. **La estabilidad de los quelatos de Mn depende fuertemente de las condiciones redox** (López-Rayo et al. 2015), porque el Mn²⁺ se oxida a Mn(III/IV) insoluble. Para Mn, EDDS, EDTA, HEEDTA y DTPA dieron mejores resultados que los demás ligandos ensayados. En el ensayo en suelo calcáreo de pH 7,70 (H₂O) / 7,10 (KCl): *"EDTA y HEEDTA mantuvieron la cantidad inicial total de Mn introducida como quelato, mientras que DTPA fue capaz de quelar más Mn del suelo"*.
- **Nota metodológica de ese mismo trabajo:** las formulaciones con ligandos tradicionales **mantuvieron más Mn pero menos Zn** en solución que las de ligandos nuevos. No hay un ganador único — depende del metal.

---

## 3. DESPLAZAMIENTO POR Ca²⁺ Y Mg²⁺

### 3.1 El mecanismo

En suelo calcáreo o con agua dura, el quelante **no encuentra un solo metal, encuentra un mercado**. El Ca²⁺ está en concentraciones de 10⁻³ a 10⁻² M mientras el micronutriente añadido está en 10⁻⁵–10⁻⁶ M. Aunque el log K con Ca²⁺ sea mucho menor que con Fe³⁺ o Zn²⁺, **la ley de acción de masas compensa la diferencia de constante con la diferencia de concentración**.

Evidencia directa (**Norvell & Lindsay 1969**): en suelos calcáreos, **Cu y Zn fueron desplazados por Ca a medida que aumentó el pH**. El comportamiento se predijo satisfactoriamente usando las constantes de formación del EDTA con Fe³⁺, Ca²⁺ y H⁺, bajo el supuesto de que el Fe³⁺ estaba controlado por la solubilidad de los óxidos férricos amorfos.

### 3.2 La doble competencia

En suelo calcáreo el micronutriente pierde por dos frentes a la vez:

1. **Ca²⁺ ataca por concentración** — desplaza al micronutriente del ligando.
2. **Fe³⁺ ataca por constante** — el Fe³⁺ del suelo (tamponado por óxidos) tiene log K altísimo con casi cualquier aminopolicarboxilato y **roba el ligando al Zn, Mn o Cu**.

Por eso un **Zn-EDTA aplicado a suelo calcáreo se convierte parcialmente en Fe-EDTA + Zn²⁺ libre**, y el Zn²⁺ liberado precipita o se adsorbe. El ligando sigue trabajando; el metal que uno pagó, no.

Confirmación indirecta en el mismo sentido: **DTPA "fue capaz de quelar más Mn del suelo"** (López-Rayo et al. 2015) — el ligando intercambia metal con la matriz activamente. Un quelato aplicado al suelo **no es un paquete cerrado**.

### 3.3 La consecuencia de biodegradación (dato no obvio)

De Bucheli-Witschel & Egli (2001): la biodegradabilidad del EDTA **depende del metal complejado**. Complejos con constante **< 10¹²** (Ca, Mg, Mn) se degradan bajo condiciones especiales; con **> 10¹²** (Cu, Fe) son recalcitrantes.

Combinado con lo anterior: en suelo calcáreo, el EDTA que fue desplazado a Ca-EDTA **es el más biodegradable**, mientras que el que terminó como Fe-EDTA **es el más persistente**. La competencia por Ca no solo arruina la eficacia agronómica — **también determina el destino ambiental del ligando**.

### 3.4 Agua dura en el tanque

⚠️ **No pude verificar en literatura primaria un dato cuantificado de pérdida de quelato por dureza del agua de caldo.** Es un punto que la industria afirma rutinariamente y que la termodinámica de §3.1 respalda cualitativamente, pero **no tengo el número**. Ver NO VERIFICADO §C.

---

## 4. ISÓMEROS DE EDDHA: o,o vs o,p — EL VECTOR DE FRAUDE ⭐

### 4.1 La química: un OH movido de sitio cuesta un enlace

El EDDHA es el análogo fenólico del EDTA: etilendiamina-N,N'-bis(2-hidroxifenilacetato). El grupo **OH fenólico** puede estar en posición *orto* o *para* en cada uno de los dos anillos aromáticos. De ahí tres isómeros posicionales:

| Isómero | Enlaces al Fe³⁺ | Denticidad | Grupos donadores |
|---|---|---|---|
| **o,o-EDDHA** | **6** | **Hexadentado** | 2 N amino + 2 O carboxilato + **2 O fenolato** |
| **o,p-EDDHA** | **5** | Pentadentado | 2 N + 2 O carboxilato + **1 O fenolato** |
| **p,p-EDDHA** | **4** | Tetradentado | 2 N + 2 O carboxilato + **0 fenolato** |

**Fuente:** Cascone S., Apicella P., Caccavo D., Lamberti G., Barba A.A. (2015), *Chemical Engineering Transactions* **44**, AIDIC, ISSN 2283-9216 — texto literal: los tres isómeros «establish respectively six, five and four bonds with the metallic ion», citando a Gómez-Gallego et al. (2002).

**El porqué geométrico.** El OH en posición *orto* respecto al carbono α queda a distancia de quelación del mismo Fe³⁺ que ya está unido por el N amino y el O carboxilato de ese brazo: cierra un anillo de 6 miembros. En posición *para*, el OH está en el extremo opuesto del anillo aromático — **físicamente inalcanzable** para el centro metálico. Ese brazo aporta solo N + carboxilato, y el sexto sitio de coordinación del octaedro queda ocupado por **agua o hidroxilo: lábil, hidrolizable y desplazable**.

La estructura cristalina del Fe-o,o-EDDHA muestra coordinación octaédrica casi perfecta, con el Fe *"nearly completely concealed by coordinating oxygens and nitrogens"* — lo que **impide la entrada de agua o hidroxilo**. El enlace fenolato–Fe(III) da el color rojo-púrpura característico y es más fuerte que el de agentes puramente carboxílicos como EDTA.
**Fuente:** Virtual Museum of Molecules and Minerals, Dept. of Soil Science, University of Wisconsin–Madison, ficha "EDDHA", que remite a **Bailey et al. (1981), *Inorganica Chimica Acta* 50:111–120**.

**Esto explica el log K de 35,09 de la Sección 1**: los dos fenolatos son bases duras que casan con el ácido duro Fe³⁺ mucho mejor que un carboxilato. Quitar uno no resta "un sexto" de la estabilidad — la desploma.

**No confundir con la estereoisomería.** El o,o-EDDHA tiene dos carbonos asimétricos → **par de enantiómeros (racémico) + forma meso**. Ambos son hexadentados, ambos legales, ambos activos, pero difieren en comportamiento en suelo. La HPLC los resuelve como **dos picos separados** (Cascone et al. 2015).

### 4.2 Constantes

| Ligando | log K (Fe³⁺) | Estado |
|---|---|---|
| **o,o-EDDHA** | **35,09** | Verificado vía López-Rayo et al. 2015, atribuido a Yunta et al. 2003 |
| **o,p-EDDHA** | **—** | ⚠️ **NO VERIFICADO.** Circula el valor 28,7 en resúmenes de buscador; **no lo use** — no se pudo abrir la fuente |

**Referencia primaria (confirmada en catálogo, tabla no leída):** Yunta F. et al. (2003), *Inorganic Chemistry* **42**, 5412–5421, **DOI 10.1021/ic034333j**, PMID 12924915. Desarrolla un método espectrofotométrico nuevo para las constantes de Fe(III) y Cu(II) y reporta valores **pM**. Pureza de ligando obtenida > 87 %.
Trabajo hermano: Yunta et al. (2004), *Dalton Transactions*, *"Effect of the tether on the Mg(II), Ca(II), Cu(II) and Fe(III) stability constants and pM values of chelating agents related to EDDHA"* — DOI 10.1039/b408730e ⚠️ *derivado de la URL de RSC, no visto impreso*.

### 4.3 Eficacia agronómica: el resultado contraintuitivo

**No simplificar: el o,p NO es inútil — es inútil EN SUELO.**

| Sistema | Isómero más eficaz | Fuente |
|---|---|---|
| **Hidroponía / solución nutritiva** | **o,p-EDDHA** | García-Marco et al. 2006 |
| **Suelo calcáreo** | **o,o-EDDHA** | López-Rayo et al. 2015; Schenkeveld |

**García-Marco S., Martínez N., Yunta F. et al. (2006)**, *"Effectiveness of Ethylenediamine-N(o-hydroxyphenylacetic)-N′(p-hydroxyphenylacetic) acid (o,p-EDDHA) to Supply Iron to Plants"*, **Plant and Soil 279, 31–40**, **DOI 10.1007/s11104-005-8218-5** *(abstract a nivel snippet)*: la Fe-quelato reductasa (FC-R) de raíz de pepino redujo el o,p-EDDHA/Fe³⁺ **más rápido** que el o,o, el EDTA y una fuente comercial de EDDHA; y el o,p fue **más eficaz que el o,o** en soja hidropónica.

**En suelo se invierte.** López-Rayo et al. 2015 (texto leído): el o,o presenta *"the most suitable properties as Fe fertilizer, due to their low reactivity in calcareous soil and high efficiency"*, mientras el o,p tiene *"lower efficacy in calcareous soil mainly due to its high reactivity with soil components"*.

**La lectura correcta:** el o,p **entrega el Fe más fácil — y precisamente por eso lo pierde contra el suelo antes de que llegue a la raíz**. Su virtud en hidroponía es su defecto en campo. Lo que hace valioso al o,o no es solo que agarre fuerte, sino que **agarre más fuerte que el suelo** (Sección 2: el suelo es el competidor).

Y esto también explica por qué el legislador europeo autorizó el o,p-EDDHA (Sección 5.2, CAS 475475-49-1): **no es un fraude en sí mismo** — es un quelante legítimo para fertirriego e hidroponía. **El fraude es venderlo como si fuera o,o para suelo calcáreo.**

**Escuela de Wageningen (Schenkeveld).** Los FeEDDHA comerciales se descomponen en **cuatro fracciones**: o,o-FeEDDHA racémico, o,o-FeEDDHA meso, o,p-FeEDDHA y **rest-EDDHA** (fracción policondensada/polimérica no identificada). Referencias localizadas, contenido no accesible:
- Schenkeveld W.D.C. et al., *"The effectiveness of soil-applied FeEDDHA treatments in preventing iron chlorosis in soybean as a function of the o,o-FeEDDHA content"*, **Plant and Soil**, **DOI 10.1007/s11104-007-9496-x**
- Schenkeveld W.D.C. (2010), tesis doctoral Wageningen, **DOI 10.18174/155619** *(snippet)*
- Schenkeveld et al. (2015), *European Journal of Soil Science*, **DOI 10.1111/ejss.12226** (competencia de Cu)
- *"The behaviour of EDDHA isomers in soils as influenced by soil properties"*, **Plant and Soil**, **DOI 10.1007/s11104-006-9135-y**

Dato de Wageningen (snippet): en agua de poro, el o,o-FeEDDHA racémico y meso muestran un **descenso gradual no atribuible a absorción vegetal ni a biodegradación** — hay pérdida química/de sorción propia del suelo. Concuerda con Schenkeveld et al. 2011/2012 (*Geoderma*), citado en Sección 6: el declive del EDDHA en suelo calcáreo **no es biodegradación, es desplazamiento catiónico por Cu**.

### 4.4 EL FRAUDE, CUANTIFICADO

**Fuente:** Lucena J.J. (Dpto. Química Agrícola, Universidad Autónoma de Madrid), *La calidad de los quelatos de hierro en el mercado nacional, 2ª parte*, Infoagro — basado en la tesis doctoral de **Álvarez-Fernández A. (2000)**, UAM, campaña 1998-1999.

| Hallazgo | Valor |
|---|---|
| Productos comerciales analizados | **80** |
| Productos que **no contenían el agente quelante declarado en la etiqueta** | **25 %** |
| Fe-EDDHA y Fe-EDDHMA que **no alcanzan los valores exigidos por la legislación** | **98,8 %** |
| Fe-EDDHA con solo 2–3 % de Fe quelado | 64,3 % |
| Fe-EDDHA con 3–4 % de Fe quelado | 23,8 % |
| Fe-EDDHMA con 2–3 % de Fe quelado | 50 % |
| Fe-EDDHMA con 3–4 % de Fe quelado | 37,5 % |
| Productos que alcanzaron el **6 % de Fe quelado declarado** | **NINGUNO** |

Faltaba además sistemáticamente en las etiquetas el **intervalo de pH de estabilidad** y el **porcentaje de Fe soluble** — exactamente los dos datos que hoy la UE obliga a declarar (Sección 5.1, Anexo III puntos 2 y 2 bis). **La norma europea actual está escrita contra este fraude.**

Contexto de mercado: España representaba **dos tercios del consumo europeo de quelatos**, con gasto del agricultor superior a **7.500 millones de pesetas**.

⚠️ **Advertencia de vigencia:** este estudio es de **1998-2000**. Es el más completo que se pudo verificar, pero **no refleja necesariamente el mercado actual**, posterior al endurecimiento regulatorio. Ver NO VERIFICADO §D.

**El hallazgo del isómero fraudulento.** Hernández-Apaolaza L. et al. (2002), *"Synthesis of o,p-EDDHA and Its Detection as the Main Impurity in o,o-EDDHA Commercial Iron Chelates"*, **J. Agric. Food Chem. 50, 6395–6399**, **DOI 10.1021/jf025727g**, PMID 12381123 *(abstract a nivel snippet)*: sintetizaron por primera vez el o,p-EDDHA y demostraron **inequívocamente por HPLC** que es la **impureza principal** de los quelatos EDDHA comerciales.

Referencias adicionales del bloque de control de calidad (DOI vistos en URL, contenido no leído):
- *"Chromatographic Determination of Fe Chelated by o,p-EDDHA in Commercial EDDHA/Fe³⁺ Fertilizers"*, **JAFC 54(4), 1380–1386 (2006)**, **DOI 10.1021/jf051745x**
- *"Characterization of Commercial Iron Chelates and Their Behavior in an Alkaline and Calcareous Soil"*, **JAFC**, **DOI 10.1021/jf025745y**
- *"Structure and Fertilizer Properties of Byproducts Formed in the Synthesis of EDDHA"*, **JAFC**, **DOI 10.1021/jf0605749**, PMID 16756367 — la fracción **policondensada / rest-EDDHA**

### 4.5 Por qué el fraude es rentable: el dato de síntesis

**Este es el hallazgo más revelador del dossier.** Cascone et al. (2015) variaron la relación fenol/tolueno en la alimentación del reactor (reacción de Petree: fenol + etilendiamina + ácido glioxílico + NaOH, 75 °C, 2 h; quelación a pH 7,5) y midieron por HPLC el **%o,o-EDDHA/Fe³⁺ del producto seco**:

| Proceso | Fracción molar de fenol | Rendimiento | **% o,o-EDDHA/Fe³⁺** |
|---|---|---|---|
| Feed 1 | 1,000 | 26 % | **2,7 %** |
| Feed 2 | 0,700 | 23 % | **2,0 %** |
| Feed 5 | 0,078 | 2,5 % | **0,2 %** |

**Un mismo esquema de reacción, cambiando solo la relación de solventes, produce entre 0,2 % y 2,7 % de o,o — un factor de 13×.** El fenol en gran exceso es lo que maximiza el orto-orto, y el fenol es el reactivo caro y tóxico. Además, para que predomine el o,o *"the pH 7,5 has to be reached as soon as possible"* durante la quelación.

**Conclusión:** el %o,o es **exactamente la variable de proceso que el fabricante puede recortar para abaratar**, sin que cambie el aspecto del producto (mismo polvo rojo), sin que cambie el "6 % Fe" de la etiqueta, y sin que el comprador pueda notarlo sin un HPLC. Esa es la definición estructural de un vector de fraude.

### 4.6 Cómo se mide: HPLC

**La norma correcta es EN 13368-2** (no la 15451, que es para EDDHSA):

| Norma | Alcance |
|---|---|
| **EN 13368-1** | EDTA, HEEDTA y DTPA por **cromatografía iónica** |
| **EN 13368-2** (BS EN 13368-2:2017) | **Fe quelado por [o,o]-EDDHA, [o,o]-EDDHMA y HBED**, por **cromatografía de par iónico** |
| **EN 15451** | Fe quelado por **EDDHSA** (suma meso/rac + fracción oligomérica) |
| **EN 15452** | **o,p-EDDHA** |

Título completo de la vigente: *"Fertilizers — Determination of chelating agents in fertilizers by chromatography — Part 2: Determination of Fe chelated by [o,o] EDDHA, [o,o] EDDHMA and HBED, or the amount of chelating agents, by ion pair chromatography"*.

✅ **Nota de validación cruzada:** la existencia de **EN 15452 para o,p-EDDHA** no pudo confirmarse en la búsqueda de normas, pero **sí fue verificada de forma independiente en el texto consolidado del Reglamento (CE) 2003/2003 en EUR-Lex** (Sección 5.2). Dos rutas independientes coinciden — se da por buena.

**Condiciones cromatográficas reales**, aplicadas por Cascone et al. (2015) invocando EN 13368-2:2007:

| Parámetro | Valor |
|---|---|
| Columna | **C18** (Agilent Zorbax Eclipse Plus), 3,9 mm d.i. × 150 mm |
| Fase móvil | acetonitrilo + **TBA (tetrabutilamonio) 0,5 % v/v** + agua hasta 1 L |
| Reactivo de par iónico | **TBA** |
| Flujo | 1 mL/min |
| Detección | **UV 280 nm** |
| Preparación | muestra en NaOH diluido (60 mg/50 mL), filtrada a 45 µm |
| Resolución | **dos picos**: racémico-o,o-EDDHA/Fe³⁺ y meso-o,o-EDDHA/Fe³⁺ |

El método HPLC de par iónico de **Lucena, Barak & Hernández-Apaolaza (1996), *J. Chromatogr. A* 727, 253–264** resuelve los diastereoisómeros y distingue isómeros posicionales en **menos de 15 min**, con mayor selectividad que la cromatografía iónica del CEN, que **no distingue isómeros geométricos ni variantes metiladas posicionales**.

Bibliografía analítica adicional: Hernández-Apaolaza, Barak & Lucena, *J. Chromatogr. A* **789**, 453–460; Deacon, Smyth & Tuinstra (1994), *J. Chromatogr. A* **659**, 349–357; Barak & Chen (1987), *SSSAJ* **51**, 893–896; Hernández-Apaolaza L. (1997), tesis doctoral UAM.

⚠️ **No existe método AOAC** para %o,o-EDDHA que se haya podido localizar. El método operativo es el **CEN/EN 13368-2**.

### 4.7 Regla de compra

> **Un Fe-EDDHA sin certificado HPLC de %o,o es un producto sin especificar.**
>
> Dos productos etiquetados "6 % Fe" pueden tener **1,8 % o,o** y **4,8 % o,o**: mismo polvo rojo, misma etiqueta, **~2,7× de diferencia en ingrediente activo real** en suelo calcáreo.
>
> **Comparar precio por kg de producto en lugar de precio por kg de Fe-o,o-EDDHA es el error económico central de este mercado.**

⚠️ El rango 2–6 % de o,o citado habitualmente **no se pudo confirmar con un estudio de mercado reciente**. Puntos verificados sueltos: 5,2 % o,o en listados comerciales (snippet); 0,2–2,7 % en producto de laboratorio (Cascone 2015). Ver NO VERIFICADO §D.

---

## 5. MARCO REGULATORIO

> ### ⚠️ TRES CORRECCIONES DE PREMISA
> El encargo de este dossier contenía tres supuestos que resultaron **falsos** al verificarlos contra los textos consolidados de EUR-Lex y del MAPA. Se documentan porque circulan ampliamente en la literatura comercial:
>
> | Supuesto habitual | Verificado |
> |---|---|
> | "Micronutrientes = **PFC/CFP 1(C)(I)**" | **Falso.** 1(C)(I) es **macronutrientes**. Micronutrientes es **CFP 1(C)(II)** |
> | "CMC 1 **puntos 3 y 4**" tratan quelantes | **Parcial.** Solo el **punto 3**. El punto 4 son inhibidores de nitrificación/ureasa |
> | "**IDHA** añadido por Reg. (CE) **1020/2009**" | **Falso.** Fue el **Reglamento (UE) nº 137/2011** (probado comparando consolidados, ver §5.2) |
> | "Brasil: **IN 61/2020** regula quelatos en fertilizantes minerales" | **Falso.** La IN 61/2020 regula **fertilizantes orgánicos y biofertilizantes**. Los **minerales** están en la **IN MAPA nº 39, de 8 de agosto de 2018** |

### 5.1 Reglamento (UE) 2019/1009 — régimen vigente

Consolidado (ES): https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:02019R1009-20251230

**Aplicación:** art. 53 — *"Se aplicará a partir del 16 de julio de 2022"*. Art. 52 — *"El Reglamento (CE) nº 2003/2003 queda derogado con efecto a partir del 16 de julio de 2022"*, con salvaguarda para "abonos CE" ya comercializados antes de esa fecha.

#### HALLAZGO CRÍTICO: no hay lista positiva de quelantes

Búsqueda de "EDTA", "EDDHA" y "lignosulfon" en todo el reglamento consolidado: **0 ocurrencias**.

El 2019/1009 **abandonó la lista cerrada** del 2003/2003 y la sustituyó por un **criterio funcional** (Anexo II, Parte II, **CMC 1, punto 3**). Un quelante nuevo entra si cumple la definición estructural + estabilidad + registro REACH. Esto es un cambio de fondo: **ya no basta preguntar "¿está en la lista?"; hay que preguntar "¿cumple el criterio?"**.

**Definición de agente quelante** — CMC 1, punto 3.a): *"El agente quelante será una sustancia orgánica compuesta de una molécula que:"*
- i) *"tenga dos o más sitios que donan pares de electrones a un catión de metal de transición central"* — Zn, Cu, Fe, Mn, **Mg, Ca**, Co
- ii) *"sea lo bastante grande como para constituir una estructura cíclica de cinco o seis anillos"*
- Estabilidad (texto vigente): *"permanecerá estable al cabo de 3 días como mínimo en una solución con cualquier pH que se sitúe dentro del intervalo declarado"*

📌 Nótese que **la definición legal europea reproduce exactamente la definición química de la Sección 7**: denticidad ≥ 2 + anillo de 5 o 6 miembros. No es casualidad — es la química la que manda.

📌 **Cambio 2021:** el texto original de 2019 exigía estabilidad *"in standard Hoagland solution at pH 7 and 8 for at least 3 days"*. El **Delegado (UE) 2021/1768** lo sustituyó por el criterio de "intervalo de pH declarado" — es decir, **el fabricante declara su ventana y debe cumplirla ahí**, en lugar de un ensayo único a pH 7-8.

**Definición de agente complejante** — punto 3.b): *"sustancia orgánica que forme una estructura plana o estérica con un catión de metal de transición divalente o trivalente"* — Zn, Cu, Fe, Mn, Co (**sin Mg ni Ca**). Estabilidad: *"al cabo de 1 día como mínimo en una disolución acuosa a pH 6-7"*.

#### Anexo I — CFP 1(C)(II): abono inorgánico a base de micronutrientes

Concentraciones mínimas, CFP 1(C)(II)(a) simple:

| Tipología | Requisito |
|---|---|
| Micronutriente en sal | 10 % en masa |
| Óxido o hidróxido | 10 % |
| **Quelado** | **5 % soluble en agua, ≥ 80 % quelado** |
| **Quelatos UVCB** | 5 %, ≥ 80 % quelado y **≥ 50 % por quelantes específicos** |
| **Complejado** | 5 %, **≥ 80 % complejado** |

Contenidos mínimos para poder **declarar** un micronutriente (CFP 1(C)(II)(b), % masa) — nótese que **el umbral quelado es mucho más bajo**, reconociendo su mayor eficacia:

| Micronutriente | No quelado | **Quelado/complejado** |
|---|---|---|
| B | 0,2 | n. a. |
| Co | 0,02 | 0,02 |
| Cu | 0,5 | **0,1** |
| **Fe** | **2** | **0,3** |
| Mn | 0,5 | **0,1** |
| Mo | 0,02 | n. a. |
| Zn | 0,5 | **0,1** |

Tolerancia analítica (Anexo III, Parte III): *"± 5 % de desviación relativa del valor declarado"*.

#### Anexo III — QUÉ OBLIGA A DECLARAR LA ETIQUETA

**Punto 2** — umbral y forma exacta. Si los micronutrientes *"son quelados por agentes quelantes y cada agente quelante puede ser identificado y cuantificado y **quela al menos un 1 % del micronutriente soluble en agua**"*, se añade tras el nombre y símbolo:

> *"«quelado por [nombre o abreviatura del agente quelante]» / «complejado por [nombre o abreviatura del agente complejante]»"*

y además **la cantidad de micronutriente quelado/complejado como % en masa**.

**Punto 2 bis** (insertado por el Delegado 2021/1768):
> *"si los micronutrientes declarados son quelados por agentes quelantes, se indicará el intervalo de pH que garantice una estabilidad aceptable"*

**Punto 4** — advertencia obligatoria: *"Utilícese solamente en caso de reconocida necesidad. No debe sobrepasarse la dosis de aplicación"*.

**Resumen operativo — la etiqueta UE conforme debe llevar los cuatro:**
1. Nombre o sigla de **cada** quelante que quele ≥ 1 % del micronutriente soluble
2. **% en masa** de micronutriente quelado (distinto del total)
3. **Intervalo de pH** de estabilidad garantizada
4. La advertencia de "reconocida necesidad"

Esto valida punto por punto el criterio operativo de la Sección 7.2.

**Actos delegados relevantes:**

| Acto | Referencia | Qué cambió |
|---|---|---|
| **Delegado (UE) 2021/1768** | 23-jun-2021, DO L 356, 8.10.2021, p. 8; rectificación DO L 35, 17.2.2022, p. 30 | Estabilidad CMC 1.3.a (Hoagland → intervalo declarado); insertó Anexo III **2 bis / c bis** (pH); reformuló tipologías incluyendo **UVCB** |
| **Delegado (UE) 2022/1519** | — | Sustituyó CMC 1 **punto 4** (inhibidores). **No afecta quelantes** |

### 5.2 Reglamento (CE) 2003/2003 — derogado, pero sigue siendo la mejor lista técnica

Consolidado (ES): https://eur-lex.europa.eu/legal-content/ES/TXT/HTML/?uri=CELEX:02003R2003-20210620

Aunque derogado, su **Anexo I, E.3.1** es la lista de referencia técnica más útil que existe, con CAS. Encabezado: *"Ácidos o sales de sodio, potasio o amonio de:"*

| Nº | Sigla | Denominación | CAS |
|---|---|---|---|
| 1 | **EDTA** | Ácido etilendiaminotetraacético | 60-00-4 |
| 2 | **HEEDTA** | Ácido 2-hidroxietiletilendiaminotriacético | 150-39-0 |
| 3 | **DTPA** | Ácido dietilentriaminopentaacético | 67-43-6 |
| 4 | **[o,o] EDDHA** | etilendiamino-N,N'-di[(orto-hidroxifenil)acético] | **1170-02-1** |
| 5 | **[o,p] EDDHA** | orto-/para-hidroxifenil | **475475-49-1** |
| 6 | [o,o] EDDHMA | orto-hidroximetilfenil | 641632-90-8 |
| 7 | [o,p] EDDHMA | orto-/para-hidroximetilfenil | 641633-41-2 |
| 8 | EDDCHA | 5-carboxi-2-hidroxifenil | 85120-53-2 |
| 9 | EDDHSA | 2-hidroxi-5-sulfofenil + condensados | 57368-07-7 / 642045-40-7 |
| 10 | **IDHA** | Ácido iminodisuccínico | 131669-35-7 |
| 11 | HBED | etilendiamino-N,N'-di(2-hidroxibencil)-N,N'-diacético | 35998-29-9 |
| 12 | **[S,S]-EDDS** | Ácido [S,S]-etilendiaminodisuccínico | **20846-91-7** |

📌 **Dato decisivo para la Sección 4:** el legislador europeo **listó o,o-EDDHA y o,p-EDDHA como sustancias distintas, con CAS distintos**. No son variantes del mismo producto: son dos quelantes diferentes.

📌 **[S,S]-EDDS está listado con su estereoquímica explícita** — coherente con la Sección 6: el racémico no es el mismo producto.

📌 Nota de nomenclatura: la sigla oficial del nº 2 es **HEEDTA**, no "HEDTA" (que aparece en el Anexo IV, método 11.1). Ambas circulan.

**Agentes complejantes (E.3.2):** solo lignosulfonato (LS, CAS 8062-15-5) y ácido heptaglucónico (HGA, CAS 23351-51-1). *"solo se permiten en productos para fertirrigación y/o aplicación foliar, excepto... lignosulfonato de zinc, hierro, cobre y manganeso"*.

**Etiquetado que ya exigía:**
- Art. 2: *"micronutriente quelado: micronutriente ligado a una de las moléculas orgánicas que figuran en la lista del punto E.3.1"*
- Art. 6: se declara *"inmediatamente a continuación del contenido soluble en agua, en porcentaje en masa del producto, seguido por las expresiones «quelado por» o «complejado por»"*
- Anexo I, Parte E, **Nota 3**: *"Si un micronutriente está presente en forma quelada, habrá que indicar en qué intervalo de pH se garantiza una buena estabilidad de la fracción quelada"*
- Tipo 4(b) "Quelato de hierro": *"5 % de hierro soluble en agua, del cual la fracción quelada es, como mínimo, del 80 %"*, declarando el *"Nombre de cada agente quelante autorizado que quele al menos un 1 % del hierro soluble en agua"*

**Normas EN de referencia** (siguen siendo los métodos de ensayo):

| Norma | Objeto |
|---|---|
| **EN 13366** | Fracción quelada (general) |
| **EN 13368-1** | EDTA / HEDTA / DTPA por HPLC |
| **EN 13368-2** | EDDHA, EDDHMA, EDDCHA, EDDHSA |
| **EN 15451** | EDDHSA |
| **EN 15452** | **o,p-EDDHA** |
| **EN 15950** | IDHA |
| **EN 16109** | Lignosulfonatos |

**Trazabilidad del origen de IDHA (verificación hecha, no asumida):** comparando el consolidado **02003R2003-20091118** (posterior a la entrada en vigor del Reg. 1020/2009) — donde **IDHA no aparece** — con el **02003R2003-20110309** — donde aparece marcado *"32011R0137: INSERTED"* — queda probado que **IDHA fue añadido por el Reglamento (UE) nº 137/2011**. HBED y la ampliación de complejantes vienen del **223/2012**; [S,S]-EDDS y HGA del **1618/2016**; la tabla E.3.2 fue sustituida por el **463/2013**. El **1107/2008** introdujo la sección F (inhibidores), **no** quelantes.

### 5.3 Brasil — MAPA

⚠️ **Leído en espejos jurídicos (LegisWeb/NormasBrasil); in.gov.br y gov.br bloquearon el acceso directo.** Tratar con reserva y verificar en el DOU antes de uso legal.

**La norma aplicable a fertilizantes minerales es la IN MAPA nº 39, de 8 de agosto de 2018** — no la IN 61/2020 (que es de orgánicos y biofertilizantes) ni es la de métodos analíticos.

- **Definición (art. 2º):** agente quelante/complexante = *"compostos químicos que formam moléculas complexas com íons metálicos, adicionados intencionalmente ao produto"*
  📌 Nótese: la definición brasileña es **mucho más laxa que la europea** — no exige anillo de 5-6 miembros ni ensayo de estabilidad. Un producto rechazable en la UE puede ser conforme en Brasil.
- **Art. 8º, III:** *"podem ser adicionados agentes quelantes ou complexantes ou aditivos autorizados, conforme os anexos II e III"*
- **Rotulagem, art. 17 §2º, XXII:** *"quando utilizado agente quelante ou complexante, o seu nome ou o do grupo ao qual pertença"*
  📌 **Brasil obliga el NOMBRE del quelante, pero no se localizó inciso que exija declarar el % de micronutriente quelatado ni el intervalo de pH.** Esta es la diferencia práctica más importante frente a la UE, y **la puerta por la que entra el fraude de %o,o** (Sección 4). La expresión *"ou o do grupo ao qual pertença"* permite además declarar solo el grupo, no la molécula.
- **Solubilidad (art. 6º):** facultativa vía suelo; obligatoria (*"teor solúvel em água, para todos os nutrientes"*) vía foliar/fertirriego/hidroponía
- **Garantías mínimas (art. 9º, III, b), % masa:** B 0,01 · Co 0,005 · Cu 0,02 · **Fe 0,02** · Mn 0,02 · Mo 0,005 · Ni 0,005 · Zn 0,1
- **Anexo II = "Agentes quelantes e complexantes autorizados"** — ⚠️ **contenido no leído**
- Modificada por **IN nº 32, de 13/10/2025** (solubilidad de P₂O₅ en complejos)
- **Decreto 4.954/2004** y **Lei 6.894/1980** existen; el Decreto **no define quelato** y fue parcialmente revocado por el **Decreto 12.502/2025**

### 5.4 Comparación UE vs Brasil — lo que cambia en la práctica

| Exigencia | UE 2019/1009 | Brasil IN 39/2018 |
|---|---|---|
| Nombre del quelante en etiqueta | **Sí** (si quela ≥ 1 %) | **Sí** (o el grupo) |
| **% de micronutriente quelado** | **Sí, obligatorio** | **No localizado** |
| **Intervalo de pH de estabilidad** | **Sí, obligatorio** | **No localizado** |
| Definición con anillo 5-6 miembros | **Sí** | No |
| Ensayo de estabilidad exigido | **Sí (3 días)** | No localizado |
| % mínimo quelado del total | **≥ 80 %** | No localizado |
| Lista positiva cerrada | **No** (criterio funcional) | Sí (Anexo II, no leído) |

**Conclusión comercial:** una etiqueta conforme a la UE trae la información necesaria para decidir. **Una etiqueta conforme a Brasil puede no traerla.** Para compra en Brasil hay que **exigir contractualmente** el % quelado, el intervalo de pH y —en EDDHA— el %o,o con certificado HPLC, porque la norma no los obliga.

---

## 6. BIODEGRADABILIDAD Y PERSISTENCIA AMBIENTAL

### 6.1 Tabla comparativa

Criterio OECD: *readily biodegradable* = **60 %** (301B, C, D, F) o **70 %** (301A, E) en 28 días, con ventana de 10 días.

| Agente | Vida media suelo | Vida media agua | OECD 301 | Fuente |
|---|---|---|---|---|
| **EDTA** | no medida; **detectable en zona radicular 19 meses** | no degrada biológicamente; única ruta real = **fotólisis del Fe(III)-EDTA** | **NO** (ni readily ni inherently); ~10 % en cribado | EU RAR EDTA/Na₄EDTA (2004, ECHA); Sýkora et al. 2001 |
| **DTPA** | ⚠️ no verificada | recalcitrante | **NO** | *Water Sci Technol*, PII S0273122396009110 |
| **NTA** | días | **horas a pocos días** | **SÍ** >90 % (301B) | Bucheli-Witschel & Egli 2001 ⚠️ snippet |
| **HEDTA** | no verificada | recalcitrante | **NO** — estable aun con lodo aclimatado 30 d | Sýkora et al. 2001 |
| **EDDHA (o,o)** | declive en solución de suelo calcáreo en 4 semanas **pero NO por biodegradación** (desplazamiento catiónico por Cu) | no verificada | no verificado | Schenkeveld et al., *Geoderma*, PII S0016706111003557 |
| **EDDS [S,S]** | **t½ 4,18–5,60 d** (tras fase lag 7–11 d) | rápida | **SÍ** — 96 % en simulación de PTAR | Tandy, Ammann, Schulin & Nowack 2006, *Environ Pollut* 142:191– |
| **EDDS [R,R]** | — | **NO degrada** | **NO** | *Chemosphere* 1997, PII S0045653597000829, PMID 9192467 |
| **IDHA (IDS)** | no verificada | — | **SÍ** — ready para **todos** los estereoisómeros (301F); >70–72 % (301E) | Cokesa et al. 2004, *Appl Environ Microbiol* 70(7):3941-3947, **DOI 10.1128/aem.70.7.3941-3947.2004** |
| **GLDA** | no verificada | — | **SÍ** ~80 % (301D) | Dossier ECHA / Nouryon ⚠️ dato industrial |
| **MGDA** | no verificada | — | **SÍ** 90–100 % (301B) | Dossier ECHA ⚠️ dato regulatorio, no revisado por pares |

### 6.2 Por qué persiste el EDTA — y el vínculo con la Sección 3

**Revisión canónica:** **Bucheli-Witschel M. & Egli T. (2001).** *Environmental fate and microbial degradation of aminopolycarboxylic acids.* **FEMS Microbiology Reviews 25(1): 69–106.** **DOI 10.1111/j.1574-6976.2001.tb00572.x** (PMID 11152941). Verificada por título, volumen, páginas y DOI.

**El mecanismo, y es el dato de mayor valor de esta sección:** la biodegradabilidad del EDTA **depende del metal que lleva puesto**. Complejos con constante **< 10¹²** (Ca, Mg, Mn) se degradan bajo condiciones especiales; con **> 10¹²** (Cu, Fe) son **recalcitrantes**. En un río real, el EDTA está mayoritariamente como Fe(III)-EDTA o Ca/Zn-EDTA — es decir, en la forma que no se degrada.

📌 **Consecuencia cruzada con la Sección 3.3:** en suelo calcáreo, el EDTA desplazado a **Ca-EDTA es el más biodegradable**; el que terminó como **Fe-EDTA es el más persistente**. La competencia por Ca no solo arruina la eficacia agronómica — **determina también el destino ambiental del ligando**. El producto que falla agronómicamente es el que menos contamina, y viceversa.

**Explicación estructural** (Sýkora et al. 2001, *Water Res* 35:2010-2016, **DOI 10.1016/S0043-1354(00)00455-3**): las moléculas con **dos o más grupos amino terciarios** (EDTA, DTPA, PDTA, HEDTA) no se biodegradan ni con lodo aclimatado 30 días; las de **un solo nitrógeno** (NTA) sí.

**Otras revisiones verificadas:** Oviedo & Rodríguez (2003), *Química Nova* 26(6):901–905; Knepper (2003), *TrAC* 22(10):708–724; Schmidt et al. (2004), *Environmental Toxicology* 19, **DOI 10.1002/tox.20071**.

### 6.3 La PTAR no lo destruye

**Kari F.G. & Giger W. (1996).** *Speciation and fate of EDTA in municipal wastewater treatment.* **Water Research 30(1): 122–134**, **DOI 10.1016/0043-1354(95)00125-5**.

Balances de masa de varios días mostraron **ninguna eliminación significativa** de EDTA por procesos biológicos o químicos. La fracción de Fe-EDTA varió de **10–55 % en afluente** a **20–90 % en efluente**. La planta no destruye EDTA: **solo cambia su especiación** — y de esa especiación depende todo lo que pase después en el río.

### 6.4 Fotodegradación: la única ruta real

- **Kari, Hilger & Canonica (1995).** *Determination of the reaction quantum yield for the photochemical degradation of Fe(III)-EDTA.* **Environ. Sci. Technol. 29(4): 1008–1017**, **DOI 10.1021/es00004a022**. Rendimientos cuánticos **0,034 → 0,018** entre 366 y 405 nm.
- **Kari & Giger (1995).** *Modeling the photochemical degradation of EDTA in the River Glatt.* **ES&T**, **DOI 10.1021/es00011a018**.

El **Fe(III)-EDTA es la única especie de EDTA que sufre fotólisis directa** en el ambiente. Productos: ED3A, EDDA, EDMA, IMDA, glicina — **fotólisis parcial, no mineralización**. ⚠️ No se verificó ningún t½ fotolítico numérico.

### 6.5 Concentraciones ambientales

⚠️ Todas de extractos de buscador del documento de fondo de la OMS *Edetic acid (EDTA) in Drinking-water* (WHO/SDE/WSH/03.04/58), **no descargado completo**:
- Alemania 1993: **45 puntos en 29 ríos**; medias anuales **5–15 µg/L**, máximo ~**50 µg/L** (río Lippe en Wesel)
- **Rin y Mosa**: máximo **40 µg/L**
- Aguas superficiales dulces ~**26 µg/L** (Coastal Wiki, citando Oviedo & Rodríguez 2003 y EU RAR 2004)

❌ **No se localizaron series con nombre y valor para Elba ni Danubio**, pese a ser citadas habitualmente.

### 6.6 Movilización de metales pesados — el argumento agrícola sólido

- **Nowack B., Schulin R. & Robinson B.H. (2006).** *Critical Assessment of Chelant-Enhanced Metal Phytoextraction.* **Environ. Sci. Technol. 40(17): 5225–5232**, **DOI 10.1021/es0604919**. Conclusión: la fitoextracción asistida por quelantes **debe evitarse salvo que la lixiviación sea irrelevante**. ⚠️ El dato "la planta extrajo ~5 % del Cu solubilizado y el 95 % lixivió" se leyó en fuente secundaria.
- **Tandy S. et al. (2004).** *Extraction of Heavy Metals from Soils Using Biodegradable Chelating Agents.* **ES&T 38(3): 937–944**, **DOI 10.1021/es0348750**.
- Remobilización desde sedimento fluvial: **Aquatic Geochemistry**, **DOI 10.1023/A:1009620513655**.
- Columna de suelo con dosis graduadas: **Bloem et al. (2018)**, *J. Plant Nutr. Soil Sci.*, **DOI 10.1002/jpln.201700353**.
- Lixiviación de Cd y Pb en columna: **ES&T**, **DOI 10.1021/es970708m**.

**El mecanismo es el mismo que hace útil al quelante:** el complejo metal-EDTA es **soluble y con carga negativa**, no se adsorbe al intercambiador catiónico del suelo, y **viaja con el agua de percolación**. No se puede tener una cosa sin la otra.

### 6.7 EDDS: solo el isómero [S,S] — trampa comercial

*Chemosphere* (1997), PII S0045653597000829, **PMID 9192467**:

| Isómero | Comportamiento |
|---|---|
| **[S,S]** | mineralizado rápida y completamente; **96 %** de remoción en simulación de PTAR |
| **[R,R]** | **sin degradar** en Sturm (301B); biotransformación muy lenta al metabolito recalcitrante **AEAA** |
| **[S,R]/[R,S]** | biotransformación a AEAA |

📌 **Implicación comercial directa:** un **EDDS racémico** (mezcla de los tres isómeros, más barato de sintetizar) **NO es un quelante biodegradable** — solo un tercio lo es, y el resto genera un metabolito persistente. Hay que exigir especificación **[S,S]** y ensayo de pureza isomérica.

📌 Esto es **la misma estructura de fraude que el %o,o del EDDHA** (Sección 4): un isómero caro que es el único que funciona, mezclado con isómeros baratos que no, bajo una etiqueta que no los distingue. Nótese que el legislador europeo **listó [S,S]-EDDS con su estereoquímica explícita** (Sección 5.2, CAS 20846-91-7) — igual que separó o,o de o,p.

Contraste: **IDHA** — Cokesa et al. (2004) demostraron biodegradabilidad rápida de **todos** los estereoisómeros (epimerasa + C-N liasa en *Agrobacterium tumefaciens* BY6). **IDHA no tiene el problema isomérico.**

### 6.8 Estado regulatorio y ecotoxicidad

- **EU Risk Assessment Report** (relator Alemania, 2003–2004) para Na₄EDTA: toxicidad baja para salud humana; riesgo ambiental **limitado a casos locales extremos**. No readily ni inherently biodegradable. No se estableció PNEC terrestre por falta de datos.
- Umbral de toxicidad aguda peces y algas **> 50 mg/L** — ~1.000× las concentraciones de río.
  📌 **El problema del EDTA no es la ecotoxicidad directa: es la persistencia y la movilización de metales.**
- ❌ **No hay evidencia de que EDTA esté en la Candidate List de SVHC de ECHA.** Tampoco se pudo confirmar negativamente. La sustitución por MGDA/GLDA en detergentes europeos es **de mercado**, no por prohibición.
- Proyecto LIFE04-ENV-SE-000765 (reducción biológica de EDTA en industria papelera) confirma acción regulatoria sobre ese sector.

### 6.9 Contra-argumento honesto: ¿pesa el EDTA agrícola?

**Un dossier que solo diera munición comercial sería propaganda. Los datos no cierran del todo a favor.**

**Reparto sectorial en Europa Occidental** ⚠️ *(snippet, atribuible a Knepper & Werner / Oviedo & Rodríguez)*: detergentes industriales **30 %**, **agricultura 18 %**, pulpa y papel **11 %**, fotoquímica **10 %**. Consumo europeo ~**35.000 t/año (1999)**.

| Lectura | Argumento |
|---|---|
| **A favor** | 18 % es el segundo sector. Y a diferencia del detergente —que va a PTAR y a un río donde se diluye— el EDTA agrícola **se aplica directamente al suelo**, donde su función es precisamente mantener metales en solución |
| **En contra** | La masa dominante es industrial/doméstica. La vía crítica (5–50 µg/L en aguas superficiales) está dominada por efluentes de PTAR y papeleras, **no por fertirriego** |
| **Evidencia que contradice la ortodoxia** | **Fine et al. (2024)**, *J. Environ. Manage.* **353: 120133** (PMID 38308985): en 4 años de lagunas construidas de 70 m³ selladas, el EDTA en solución de suelo **se biodegradó rápido** al cesar las aplicaciones, y la lixiviación espontánea en tres inviernos fue **< 0,02 % del EDTA aplicado**. Los autores concluyen que en suelo aclimatado con población degradadora establecida **el retiro del EDTA puede no estar justificado**, y que los quelantes biodegradables son **demasiado efímeros para ser efectivos ahí** |

> **Síntesis defendible:** el EDTA agrícola **no** es el contribuyente mayoritario a la carga ambiental total. Si se busca argumento comercial para IDHA/EDDS frente a EDTA, el respaldo sólido **no es** "el EDTA contamina los ríos" (eso es sobre todo detergente y papelera), sino **la movilización de metales en el perfil de suelo** (Nowack 2006; Bloem 2018) y **la persistencia isomérica documentada**.
>
> Y hay que decir el reverso: **Fine et al. (2024) sugiere que un quelante biodegradable puede degradarse antes de hacer su trabajo.** Biodegradable no es gratis: se paga en persistencia útil.

---

## 7. QUELATO vs COMPLEJO vs MEZCLA

### 7.1 Definición química estricta

**QUELATO** (del griego *chēlē*, "pinza"). Requiere las tres condiciones **simultáneamente**:

1. **Ligando polidentado** — dona electrones desde **dos o más átomos donores** (N, O, S) al mismo ion metálico.
2. **Anillo de coordinación cerrado** — los átomos donores y el metal forman un **ciclo**. Los anillos de **5 y 6 miembros** son los estables; de ahí que los aminopolicarboxilatos (que forman glicinatos de 5 miembros) dominen el mercado.
3. **Constante de estabilidad definida y medible** — existe un log K determinado para una estequiometría M:L conocida.

El **efecto quelato** —la razón de que esto importe— es que un ligando polidentado forma un complejo mucho más estable que varios ligandos monodentados equivalentes. El origen es **entrópico**: un ligando hexadentado desplaza seis moléculas de agua y libera cinco partículas netas a la solución.

**Denticidad de los ligandos del dossier:**

| Ligando | Denticidad | Átomos donores | Anillos con Fe³⁺ |
|---|---|---|---|
| **EDTA** | **hexadentado** | 2 N + 4 O(carboxilato) | 5 |
| **DTPA** | **octadentado** (potencial) | 3 N + 5 O | hasta 7 |
| **o,o-EDDHA** | **hexadentado** | 2 N + 2 O(carboxilato) + **2 O(fenolato)** | 5 |
| **o,p-EDDHA** | **pentadentado** | pierde un fenolato orto | 4 |
| **HEDTA** | pentadentado | 2 N + 3 O | 4 |
| **NTA** | tetradentado | 1 N + 3 O | 3 |
| **Citrato** | tridentado | 3 O | 2 |

Los **fenolatos** del o,o-EDDHA son la clave de su log K de 35: son bases duras que casan con el ácido duro Fe³⁺ mucho mejor que un carboxilato. Ver Sección 4.

**COMPLEJO (o agente complejante):** hay enlace de coordinación **pero no anillo cerrado**, o la denticidad y la estequiometría no están definidas. Ejemplos comerciales: **lignosulfonato, gluconato, heptagluconato, ácidos húmicos/fúlvicos, aminoácidos**. Pueden funcionar agronómicamente —López-Rayo et al. (2015) los ensayaron en serio— pero **no tienen una constante de estabilidad única** porque no son una molécula única. Un lignosulfonato es una población polidispersa.

**MEZCLA:** sal metálica + un ácido orgánico cualquiera, revueltos. **Sin evidencia de coordinación**. Es el caso de un "sulfato de zinc con ácido cítrico" vendido como "Zn quelatado". El citrato **sí** es un quelante tridentado real, pero a la relación molar y al pH del producto puede haber poco o nada de metal efectivamente quelatado.

### 7.2 Criterio operativo — ¿este producto puede llamarse quelato?

Aplicar en orden. **Si falla cualquiera de los tres primeros, no es un quelato.**

| # | Pregunta | Criterio de aprobación |
|---|---|---|
| **1** | ¿El agente quelante está **nombrado** en la etiqueta con su sigla o nombre químico? | Debe decir "EDTA", "DTPA", "o,o-EDDHA", "IDHA"… **"quelato orgánico", "quelato natural" o "aminoquelato" no identifican nada** |
| **2** | ¿Está **declarado el % de metal efectivamente quelatado**, distinto del % de metal total? | Son dos números diferentes. Si solo hay uno, falta información |
| **3** | ¿El agente está en la **lista de quelantes autorizados** de la jurisdicción? | Ver Sección 5 |
| **4** | ¿Se declara el **rango de pH de estabilidad**? | Exigencia regulatoria en la UE |
| **5** | Para Fe-EDDHA: ¿se declara el **% de isómero o,o**? | **Sin este número el producto es incomprable.** Ver Sección 4 |
| **6** | ¿La **relación molar ligando:metal** es ≥ 1:1? | Con menos ligando que metal, el excedente de metal **no está quelatado** por definición estequiométrica |
| **7** | ¿Existe **método analítico** para verificarlo? | HPLC para EDDHA; los complejos orgánicos indefinidos **no son verificables analíticamente** — su cumplimiento no se puede auditar |

**La prueba del punto 6 es la más subestimada y la más fácil de aplicar en campo:** si un producto declara 6 % de Fe y la cantidad de agente quelante presente no alcanza estequiométricamente para 6 % de Fe, la diferencia es **sulfato disfrazado**. Se detecta con un cálculo de masa molar, sin laboratorio.

---

## 8. COSTO RELATIVO POR kg DE METAL

⚠️ **No se dan precios absolutos.** Varían por país, volumen, momento y proveedor. Solo el **orden relativo**, que es estructural y estable.

### 8.1 El orden

**Sulfato ≪ EDTA < HEDTA < DTPA ≪ EDDHA**

El EDDHA es el extremo caro por tres razones acumulativas: síntesis más compleja (condensación de fenol + glioxilato + etilendiamina, con mezcla de isómeros), rendimiento de la fracción útil (solo el o,o sirve), y purificación.

### 8.2 El multiplicador oculto: contenido de metal

El precio por kg de **producto** engaña. Lo que se compra es **metal**. Y el quelato, por ser una molécula grande, **diluye el metal**.

Contenido de metal, **calculado estequiométricamente por mí** a partir de masas atómicas IUPAC (aritmética verificable, no dato de literatura):

| Fuente | Fórmula | MM (g/mol) | % metal |
|---|---|---|---|
| **Sulfato ferroso heptahidrato** | FeSO₄·7H₂O | 278,01 | **20,1 % Fe** |
| **Fe-EDTA sódico trihidrato** | NaFe(C₁₀H₁₂N₂O₈)·3H₂O | 421,09 | **13,3 % Fe** |
| **Fe-DTPA disódico** | Na₂Fe(C₁₄H₁₈N₃O₁₀) | 490,13 | **11,4 % Fe** |
| **Fe-EDDHA sódico (quelato puro)** | NaFe(C₁₈H₁₆N₂O₆) | 435,17 | **12,8 % Fe** |
| **Sulfato de zinc heptahidrato** | ZnSO₄·7H₂O | 287,54 | **22,7 % Zn** |
| **Sulfato de manganeso monohidrato** | MnSO₄·H₂O | 169,01 | **32,5 % Mn** |

**El dato que hay que entender del Fe-EDDHA:** el quelato **puro** tiene 12,8 % de Fe, pero **el producto comercial estándar declara 6 % de Fe**. La diferencia son sales de formulación, subproductos de síntesis e isómeros inactivos. Y de ese 6 %, **solo la fracción quelatada como o,o es agronómicamente útil en suelo calcáreo** — típicamente 3–4,8 puntos porcentuales. Ver Sección 4.

Es decir: **el costo real por kg de Fe efectivo en un EDDHA hay que calcularlo sobre el %o,o, no sobre el % de Fe total.** Dos productos ambos "6 % Fe" pueden diferir al doble en Fe útil.

### 8.3 Cuándo el caro es el barato

El orden de costo **no es el orden de decisión**. La decisión la fija el pH (Sección 2):

| Situación | Elección racional | Razón |
|---|---|---|
| Suelo ácido a neutro (**pH < 6,5**), deficiencia confirmada | **Sulfato** | El quelato no aporta nada que el sulfato no haga; se paga la molécula por nada |
| pH 6,5–7,2 | **EDTA / HEDTA / DTPA** según metal | Ventana de estabilidad adecuada |
| pH 7,2–7,5 | **DTPA** | EDTA ya perdió |
| **Suelo calcáreo (pH > 7,5)**, clorosis férrica | **o,o-EDDHA**, sin alternativa | Es el único que sobrevive. Acá el EDDHA es el **único producto que funciona**, y un EDTA barato es un **gasto del 100 %**, no un ahorro |
| Fertirriego, agua de buena calidad | El más barato que aguante el pH del agua | |
| Foliar | Ver "LO QUE NO SE PUEDE" §L1 | El quelato **no es automáticamente superior** por vía foliar |

**La frase para el productor:** en suelo ácido, pagar EDDHA es tirar plata. En suelo calcáreo, ahorrar con EDTA es tirar *toda* la plata. El costo del quelato solo se evalúa contra el pH.

---

## LO QUE NO SE PUEDE

**Qué NO arregla un quelato.** Cada punto con la evidencia de este mismo dossier.

### L1. No aumenta la dosis de metal — la reduce

Un quelato es una molécula grande. **Diluye el metal.** Cálculo estequiométrico propio (§8.2):

| Fuente | % metal |
|---|---|
| FeSO₄·7H₂O | **20,1 % Fe** |
| Fe-EDTA·3H₂O | 13,3 % Fe |
| Fe-DTPA | 11,4 % Fe |
| **Fe-EDDHA comercial** | **6 % Fe** (12,8 % el quelato puro) |

Comprar quelato **por más metal es un error aritmético**: se compra *menos* metal por kg, a mayor precio. Lo que se compra es **disponibilidad**, no cantidad. Si la disponibilidad no es el problema, el quelato no resuelve nada.

### L2. No compensa un pH de suelo equivocado — y el pH decide cuál sirve

Un quelato **no cambia el pH**. Y el pH determina si el quelato sobrevive: **Fe-EDTA es inestable a pH 7,3** (Norvell & Lindsay 1969, §2.2). Aplicar Fe-EDTA a suelo calcáreo no es "menos eficaz": es **pérdida del 100 %** — el Ca²⁺ desplaza al Fe³⁺ y este precipita.

El problema de fondo en suelo calcáreo **no es la falta de Fe**. El método de Lindsay & Norvell (§2.1) asume explícitamente que **el Fe³⁺ en solución está controlado por la solubilidad de los óxidos férricos amorfos del propio suelo** — es decir, **el suelo tiene un reservorio de Fe propio e inagotable**. Lo que falta es Fe *disponible*, y eso lo gobierna el pH y el bicarbonato, no el contenido total.

> **Corolario:** si el pH es el problema, la herramienta que corresponde es **acidificación / manejo del bicarbonato / portainjerto tolerante**, y el quelato es un paliativo caro y recurrente.

### L3. El quelato aplicado al suelo no es un paquete cerrado

Se compra "Zn-EDTA" y se aplica al suelo. Lo que pasa después:
- **Ca²⁺ ataca por concentración** (está 100–1.000× más concentrado)
- **Fe³⁺ ataca por constante** (log K altísimo con casi cualquier aminopolicarboxilato)

**El ligando sigue trabajando; el metal que se pagó, no.** Evidencia directa: *"DTPA fue capaz de quelar más Mn del suelo"* (López-Rayo et al. 2015) — el ligando **intercambia metal con la matriz activamente**. Un Zn-EDTA en suelo calcáreo se convierte parcialmente en **Fe-EDTA + Zn²⁺ libre**, y el Zn liberado precipita o se adsorbe (§3.2).

### L4. El quelante equivocado para el metal equivocado

**IDHA-Fe³⁺ tiene log K 12,9. o,o-EDDHA-Fe³⁺ tiene 35,09.** Son **22 órdenes de magnitud**. Un "IDHA-Fe biodegradable" para clorosis férrica en suelo calcáreo está **termodinámicamente mal aplicado**, por muy verde que sea su etiqueta.

López-Rayo et al. (2015) son explícitos: los ligandos nuevos (IDHA, EDDS, o,p-EDDHA) son buenas alternativas **"principalmente para fertilizantes de Zn"** — **no para Fe**.

### L5. "Biodegradable" no es gratis: se paga en persistencia útil

**Fine et al. (2024)**, *J. Environ. Manage.* **353: 120133** (PMID 38308985): en suelo aclimatado el EDTA se biodegradó rápido al cesar las aplicaciones y la lixiviación fue **< 0,02 % de lo aplicado**; los autores concluyen que **los quelantes biodegradables pueden ser "demasiado efímeros para ser efectivos"** ahí.

Un quelante que desaparece en **4–5 días** (EDDS [S,S], §6.1) puede degradarse **antes de haber hecho su trabajo**. La biodegradabilidad es una virtud ambiental, **no una virtud agronómica**.

### L6. Un quelato no vuelve honesto a un isómero

**Dos veces en este dossier aparece la misma trampa**: un isómero caro que es el único que funciona, mezclado con isómeros baratos que no, bajo una etiqueta que no los distingue.

| Producto | Isómero útil | Trampa |
|---|---|---|
| **Fe-EDDHA** | **o,o** (hexadentado) | o,p (pentadentado) y rest-EDDHA policondensado. **98,8 % de los productos incumplían** (§4.4) |
| **EDDS** | **[S,S]** | [R,R] no degrada; racémico ⅓ útil (§6.7) |

**Un producto "quelatado" cuyo isómero activo no está declarado y certificado no está especificado.** Y en Brasil la norma **no obliga a declararlo** (§5.4).

### L7. El quelato no justifica la aplicación

**El propio Reglamento (UE) 2019/1009 obliga a imprimir en la etiqueta** (Anexo III, punto 4):

> *"Utilícese solamente en caso de reconocida necesidad. No debe sobrepasarse la dosis de aplicación"*

Es decir: **el legislador europeo exige advertir que un micronutriente sin deficiencia reconocida no debe aplicarse.** Sin diagnóstico (análisis de suelo, foliar o síntoma), un micronutriente quelatado es un costo sin hipótesis agronómica. El quelato mejora la *entrega*; **no crea la necesidad**.

### L8. El ligando sobrevive al metal — y eso tiene un costo ambiental

Cuando el quelato entrega o pierde su micronutriente, **el ligando sigue activo** y puede tomar lo que encuentre: Cu, Pb, Cd, Ni. El complejo metal-EDTA es **soluble y aniónico**, no se adsorbe al intercambiador catiónico y **viaja con el agua de percolación** (§6.6; Nowack et al. 2006, **DOI 10.1021/es0604919**).

**No se puede tener una cosa sin la otra:** el mecanismo que mantiene el micronutriente en solución es el mismo que moviliza metales pesados hacia la napa.

### L9. ⚠️ Aplicación foliar: NO VERIFICADO en este dossier

El encargo pedía documentar que **el quelato foliar no siempre penetra mejor que la sal**. La hipótesis es plausible —el quelato tiene mayor masa molecular y menor penetración cuticular que un ion pequeño, y la humedad relativa / punto de delicuescencia domina la absorción— y las referencias habituales son **Fernández & Eichert (2009)**, *Critical Reviews in Plant Sciences*, y **Fernández & Brown (2013)**, *Frontiers in Plant Science*.

**Pero NO se verificó ninguna de estas fuentes ni ningún dato en esta investigación** (presupuesto de búsqueda agotado; agente de investigación no concluyó). **No use este argumento sin verificarlo.** Se deja consignado como hipótesis a comprobar, no como hallazgo.

Igualmente **sin verificar**: la baja movilidad floemática del Fe (que haría transitoria la corrección foliar), la interacción de quelatos con fosfatos y glifosato en tanque, y los metaanálisis de "no respuesta" al micronutriente sin deficiencia diagnosticada.

### Resumen: las tres preguntas antes de comprar un quelato

1. **¿Hay deficiencia diagnosticada?** Si no → no compre nada. (L7)
2. **¿Cuál es el pH del suelo?** Él decide *cuál* quelato, y si hace falta alguno. Bajo pH 6,5 → sulfato. (L2, §8.3)
3. **¿Está especificado el isómero activo y el % quelado, con método y certificado?** Si no → el producto no está especificado. (L6, §7.2)

---

## NO VERIFICADO

Todo lo de esta sección **se buscó y no se pudo confirmar en fuente primaria accesible**. No debe usarse como afirmación firme. Se declara qué se buscó y por qué falló.

### A. Constantes de estabilidad (Sección 1)

| # | Qué falta | Qué se buscó | Estado |
|---|---|---|---|
| A.1 | **La mayoría de la tabla log K**: Fe²⁺ de todos los ligandos; Zn/Mn/Cu/Ca/Mg de EDTA, DTPA, HEDTA, NTA, GLDA; Ca/Mg de o,o-EDDHA, EDDS, IDHA | NIST SRD 46 (es base descargable, no web); Martell & Smith; Anderegg *Sci Total Environ* 1987 (PII 0048969787901276); tablas en revisiones | **No obtenido.** Paywall/403 en ACS, Wiley, ScienceDirect, PMC, NIST |
| A.2 | **Citrato**: ninguna constante | mismas fuentes | **No obtenido** |
| A.3 | **Fuerza iónica de EDTA/DTPA/HEDTA/NTA/GLDA-Fe³⁺** (25,7 / 28,0 / 19,8 / 15,8 / 15,2) | Tabla 1 de Almubarak & Ng 2024 declara T=25 °C pero **no declara I** | **Incompleto por origen.** Por la regla del §1.1, estos valores son de **menor calidad probatoria** |
| A.4 | **Discrepancia GLDA-Fe³⁺** | Almubarak & Ng dan **15,2**; en la literatura circulan valores notablemente menores | **Sin resolver.** Ambos declarados, ninguno adoptado |
| A.5 | **Yunta et al. 2003 (10.1021/ic034333j)**: tabla completa y valores pM | pubs.acs.org | **403.** Es la fuente que resolvería Ca²⁺/Mg²⁺ de EDDHA |
| A.6 | Orama 2002, Hyvönen 2003 | leídos **solo vía cita** en López-Rayo 2015 | Constantes tomadas de segunda mano |

### B. Ventanas de pH (Sección 2)

| # | Qué falta | Estado |
|---|---|---|
| B.1 | **Textos completos de Lindsay & Norvell 1969, Norvell & Lindsay 1969, Norvell 1991, Lindsay 1991.** Los DOI **sí** fueron leídos en las URL de Wiley/SSSA; el **contenido** proviene de resúmenes y de literatura citante | **403 en Wiley.** Es la laguna metodológica principal |
| B.2 | **El valor "0,025 de estabilidad a pH 7,5" del Fe-EDTA** (UF/IFAS HS1208) | **Extracto de buscador.** ask.ifas.ufl.edu y edis.ifas.ufl.edu bloqueados/ECONNRESET. **Verificar antes de publicar** |
| B.3 | **"13 % del Fe soluble a pH 7,9 a 30 d" del Fe-DTPA** y "efectivo en 4 suelos pH 5,8–7,3" | Atribuido a la línea Norvell/Lindsay y a *Plant and Soil* **DOI 10.1007/BF00693111**. **Ninguno leído en original** |
| B.4 | **Curvas cuantitativas "% quelato remanente vs pH"** para cada quelato/metal — lo que el encargo pedía explícitamente | **NO OBTENIDAS.** No se localizó ninguna tabla ni figura numérica en fuente accesible. Lo que hay son **umbrales cualitativos por pH**, que es menos de lo pedido |
| B.5 | Ventanas de pH para **Zn, Mn y Cu** por separado (solo hay Fe bien documentado) | **Parcial.** Solo evidencia cualitativa de desplazamiento por Ca |
| B.6 | Ensayo *Calibrachoa* (pH 6,5 / 7,2) | Indexado en DOAJ, **texto completo no leído** |

### C. Desplazamiento por Ca/Mg (Sección 3)

| # | Qué falta | Estado |
|---|---|---|
| C.1 | **Cuantificación del desplazamiento por dureza del agua de caldo** (mg/L de Ca vs % de quelato perdido) | **NO ENCONTRADO** en literatura primaria. La termodinámica lo respalda cualitativamente; **no hay número** |
| C.2 | **Diagramas de fracción molar** de Lindsay & Norvell con valores numéricos por pH | No accesibles (ver B.1) |
| C.3 | Constantes Ca²⁺/Mg²⁺ de cada ligando, necesarias para calcular la competencia | Ver A.1 |

### D. Isómeros de EDDHA (Sección 4)

| # | Qué falta | Estado |
|---|---|---|
| D.1 | **log K de Fe(III)–o,p-EDDHA** | Circula **28,7** en resúmenes de buscador. **Fuente no abierta. NO USAR** |
| D.2 | **Datos numéricos de estabilidad vs pH** de o,o y o,p. La cifra corriente "o,o estable hasta pH 9–10" **no está respaldada aquí** | No se pudo acceder a Hernández-Apaolaza et al., *"Effect of pH on the stability of the chelates FeEDDHA, FeEDDHMA and their isomers"* |
| D.3 | **Vigencia del estudio de fraude**: los datos de Álvarez-Fernández son de **1998-2000** | **No se encontró estudio de mercado reciente.** El endurecimiento regulatorio posterior pudo cambiar el panorama. **No extrapolar al mercado 2026 sin verificación** |
| D.4 | **Rango típico 2–6 % de o,o en el mercado actual** | Solo puntos sueltos: 5,2 % (listados comerciales, snippet); 0,2–2,7 % (Cascone 2015, laboratorio). **Sin distribución de mercado** |
| D.5 | Resultados numéricos de **García-Marco et al. 2006** (10.1021/jf051745x): cuántos productos, con qué %o,p | ACS bloqueado. Solo el hecho cualitativo |
| D.6 | Cifras de **Schenkeveld** sobre eficacia vs %o,o (10.1007/s11104-007-9496-x) y tesis (10.18174/155619) | Springer y research.wur.nl bloqueados. El DOI de la tesis es de snippet |
| D.7 | **Método AOAC** para %o,o | **No existe uno localizable.** El operativo es CEN/EN 13368-2 |
| D.8 | **DOI de Bailey et al. 1981** (*Inorg. Chim. Acta* 50:111–120) | No visible en la ficha de Wisconsin |
| D.9 | **DOI Yunta 2004 Dalton** `10.1039/b408730e` | **Reconstruido desde la URL de RSC, no visto impreso** |
| D.10 | Álvarez-Fernández et al., *Eur. J. Agronomy* (PII S1161030104000164) | Artículo localizado, **DOI no visto**. No se inventa |
| D.11 | **Diferencial de precio por punto de %o,o** | **Ningún dato publicado.** La inferencia económica del §4.5 es razonamiento propio apoyado en rendimientos medidos, no un dato de mercado |

### E. Regulatorio (Sección 5)

| # | Qué falta | Estado |
|---|---|---|
| E.1 | **AAPFCO / EE. UU.**: definición oficial de "chelate", lista aceptada, etiquetado estatal, método AOAC | aapfco.org **bloqueado**. **Nada afirmado** |
| E.2 | **Anexo II de la IN 39/2018 (Brasil)**: qué quelantes están efectivamente autorizados | **No leído.** Laguna importante para operar en Brasil |
| E.3 | Todo lo brasileño proviene de **espejos jurídicos** (LegisWeb/NormasBrasil), **no del DOU ni gov.br** (bloqueados) | **Verificar en DOU antes de uso legal** |
| E.4 | Cuál IN fija los **métodos analíticos** brasileños (pista: IN 37/2017) | Sin confirmar |
| E.5 | Carácter **opcional del marcado CE** y articulación con Reg. (UE) 2019/515 de reconocimiento mutuo | Solo verificados art. 3 y art. 52 |
| E.6 | Si existe delegado posterior a 2021/1768 que toque CMC 1 punto 3 | Revisado el consolidado a 30.12.2025; no se auditó acto por acto |

### F. Biodegradabilidad (Sección 6)

| # | Qué falta | Estado |
|---|---|---|
| F.1 | **Vida media t½ de EDTA en suelo y agua**: no hay valor primario citable. El "19 meses en zona radicular" es de snippet sin fuente identificada | **Laguna** |
| F.2 | **Datos de DTPA en suelo/agua**: prácticamente ausentes | **La laguna más grande de la sección** |
| F.3 | **t½ fotolítico numérico** de Fe(III)-EDTA | Solo rendimientos cuánticos verificados |
| F.4 | **Concentraciones en Elba y Danubio** | No localizadas con nombre y valor |
| F.5 | **MGDA y GLDA**: datos de dossiers ECHA y literatura de fabricante (BASF Trilon M, Nouryon Dissolvine), **no de literatura revisada por pares** | Calidad probatoria menor |
| F.6 | **NTA >90 % Sturm / >80 % Closed Bottle** | Snippet atribuido a fuente regulatoria |
| F.7 | **Reparto sectorial 30/18/11/10 %** | Snippet; capítulo fuente no leído |
| F.8 | **"95 % del Cu lixivió"** (Nowack 2006) | Fuente secundaria |
| F.9 | **Autores y DOI** de *Chemosphere* 1997 sobre isómeros de EDDS (se atribuye a Schowanek et al.; sin confirmar) | Solo PII y PMID |
| F.10 | **DOI y año exacto** del artículo de EDDHA en *Geoderma* (Schenkeveld): un resultado indica 2011, otro 2012 | Discrepancia sin resolver |
| F.11 | **Estado SVHC de EDTA**: no hay evidencia de inclusión; **tampoco se pudo confirmar negativamente** | Ambiguo — no afirmar en ninguna dirección |

### G. Nota sobre las cifras calculadas

Los porcentajes de contenido de metal del §8.2 son **cálculo estequiométrico propio** a partir de masas atómicas IUPAC, no dato de literatura. Son aritmética verificable y reproducible, pero **corresponden al compuesto puro**: un producto comercial contiene sales de formulación, agua e impurezas, por lo que su contenido real es **menor**. El caso del Fe-EDDHA (12,8 % teórico vs 6 % comercial) lo ilustra.

⚠️ La verificación cruzada de estos cálculos con `python` y `bc` **falló por indisponibilidad de ambos runtimes** en este entorno. La aritmética se hizo a mano.

---


