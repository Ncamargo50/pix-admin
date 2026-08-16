# R1 — Sales fertilizantes: solubilidad, termoquímica y límites de la formulación LÍQUIDA

**Dossier de investigación verificado**
Fecha: 2026-08-16 · Ámbito: química de sales para formulación líquida (fertirriego, foliar, soluciones madre)

---

## 0. Reglas de lectura de este documento

Cada número de este dossier lleva una **etiqueta de evidencia**. No hay números sin etiqueta.

| Etiqueta | Significado |
|---|---|
| **[M]** | **Medido / tabulado** en una fuente primaria o handbook. Se cita la fuente y la temperatura. |
| **[M2]** | Medido y **confirmado por dos fuentes independientes** que coinciden. |
| **[C]** | **Calculado** por estequiometría o por una fórmula explícita que se muestra en el texto. No es una medición. |
| **[I]** | **Interpolado linealmente** entre dos valores medidos. No es una medición. |
| **[?]** | **Discrepancia entre fuentes**: se dan las dos y se arbitra. |
| **[NV]** | **No verificado.** Va a la tabla del §9. |

> **Regla dura aplicada:** un valor de solubilidad sin temperatura declarada **no es un valor**. Cuando una fuente lo publica así, este dossier lo registra como defecto de la fuente, no como dato.

### 0.1 Dos advertencias de método que cambian los números

**(a) Base de agua: LIBRE vs TOTAL.** Para las sales hidratadas hay dos convenciones y las fuentes las mezclan sin avisar:

- **Base anhidra**: g de sal *anhidra* por 100 g de H₂O. Es la base de las tablas clásicas (Seidell → CRC).
- **Base hidrato / agua libre**: g del *hidrato comercial* por 100 g del agua que usted **echa al tanque**. El agua de cristalización se suma al solvente y por eso este número es **mucho mayor**.
- **Base hidrato / agua total**: g de hidrato por 100 g de agua contando el agua de cristalización como solvente.

Conversión usada en este dossier (base agua libre), con `n = S_anh / M_anh`:

```
S_hidrato = [ n · M_hidrato · 100 ] / [ 100 − n · x · 18,015 ]        (x = moles de H2O de cristalización)
```

**Validación de la fórmula:** para MgSO₄·7H₂O a 20 °C, con S_anh = 35,1 g/100 g H₂O, la fórmula da **113,7**. Wikipedia/CRC publica de forma independiente **113 g/100 mL a 20 °C** para el heptahidrato. Coinciden. La fórmula queda validada. **[M2]**

**(b) Defecto detectado en la tabla de solubilidad de Wikipedia.** La tabla `Solubility table` de Wikipedia tiene columnas 0/10/**15**/20/30/40…/100 °C, pero **muchas filas traen sólo 11 celdas y omiten la de 15 °C sin dejarla vacía**, de modo que la tabla *renderizada* corre los valores una columna a la izquierda. Verificado: la fila de KNO₃ leída como 0/10/**15**/20 daría 31,6 g a 15 °C, pero la serie clásica y una segunda fuente independiente (BOC Sciences, columnas 0/20/40/60/80/100) dan **31,66 g a 20 °C**. Lo mismo con Ca(NO₃)₂ (129 g a 20 °C, confirmado por el chembox de Wikipedia que da 1290 g/L a 20 °C).
**Consecuencia práctica: en este dossier los valores de esa tabla se reasignaron a la serie 0/10/20/30/40… y cada uno se cruzó contra una segunda fuente.** Quien copie la tabla renderizada de Wikipedia sin este control se lleva los valores corridos una columna.

---

## 1. Solubilidad en agua

### 1.1 Fuentes de la tabla

| Clave | Fuente | Columnas de T | Unidad declarada | URL |
|---|---|---|---|---|
| **WST** | Wikipedia, *Solubility table* (wikitext crudo, no la tabla renderizada) | 0/10/15/20/30/40/50/60/70/80/90/100 °C | g/100 mL H₂O | https://en.wikipedia.org/wiki/Solubility_table |
| **BOC** | BOC Sciences, *Water Solubility Table at Temperatures* | 0/20/40/60/80/100 °C | **g/100 g H₂O** | https://www.bocsci.com/support-documents/water-solubility-table-at-temperatures.html |
| **CB-x** | Chembox de Wikipedia del compuesto (cita CRC Handbook 97ª ed., Patnaik *Handbook of Inorganic Chemicals*, o PubChem según el caso) | variable | g/100 mL o g/L | — |
| **CBK** | ChemicalBook, ficha del producto | variable | g/100 mL | https://www.chemicalbook.com/ |

> **Nota de unidad:** WST declara g/100 mL de agua; BOC declara g/100 g H₂O. A 20 °C, 100 mL de agua = 99,82 g, así que la diferencia es del **0,2 %** — por debajo de la dispersión entre fuentes. Este dossier reporta todo como **g/100 g H₂O** y asume la equivalencia, que queda declarada aquí y no se repite.

### 1.2 MACRONUTRIENTES — base anhidra (g de sal anhidra / 100 g H₂O)

| Sal | Fórmula | 0 °C | 10 °C | 20 °C | 25 °C | 30 °C | Ev. | Notas y control cruzado |
|---|---|---|---|---|---|---|---|---|
| Urea | CO(NH₂)₂ | 66,7 | s/d | 108 | **120** | ~137 | [M]/[I] | 25 °C **[M]** de CRC 97ª ed. vía CB-Urea: *1200 g/L a 25 °C*. 30 °C **[I]** entre 108 (20 °C) y 167 (40 °C). CRC además da 790 g/L a **5 °C**. |
| Nitrato de amonio | NH₄NO₃ | 118 | 150 | **192** [?] | ~213 | 242 | [M]/[?] | **Discrepancia:** WST y CB-AN (Patnaik 2002) dan **192** a 20 °C; BOC da **187,7**. Diferencia 2,3 %. Se prefiere **192** (dos fuentes coinciden contra una). 25 °C **[I]**. |
| Sulfato de amonio | (NH₄)₂SO₄ | 70,6 | 73,0 | 75,4 | ~76,7 | 78,1 | **[M2]** | BOC confirma: 70,4 / 75,44 / 81,2 a 0/20/40 °C. Coincidencia < 0,3 %. 25 °C **[I]**. |
| Nitrato de calcio | Ca(NO₃)₂ | 102 | 115 | **129** [?] | ~140 | 152 | [M]/[?] | **Discrepancia:** CB-CaNO3 da **1212 g/L (121,2) a 20 °C para el anhidro** y **1290 g/L (129) a 20 °C rotulado tetrahidrato**. Ambos parecen ser base anhidra; difieren 6,4 %. Ver §1.5 — es el peor dato de la tabla. |
| Nitrato de potasio | KNO₃ | 13,3 | 20,9 | 31,6 | **38,3** | 45,8 | **[M2]** | BOC: 13,25 / 31,66 / 63,9. 25 °C **[M]** de CB-KNO3: *383 g/L a 25 °C*. Es la sal de mayor pendiente dS/dT de la tabla — ver §2. |
| Cloruro de potasio | KCl | 28,0 | 31,2 | 34,2 | ~35,7 | 37,2 | **[M2]** | BOC: 28,15 / 34,24 / 40,3. CB-KCl: 27,77 (0 °C), 33,97 (20 °C). Tres fuentes dentro del 0,8 %. |
| Sulfato de potasio | K₂SO₄ | 7,4 | 9,3 | 11,1 | **12,0** | 13,0 | **[M2]** | BOC: 7,33 / 11,11 / 14,79. 25 °C **[M]** de CB-K2SO4: *120 g/L a 25 °C*. **La sal menos soluble de todo el catálogo NPK.** |
| MAP | NH₄H₂PO₄ | 22,7 | 29,5 | 37,4 [?] | ~41,9 | 46,4 | [M2]/[?] | BOC: 22,7 / **36,8** / 56,7. Diferencia 1,6 % a 20 °C, dentro del ruido. 25 °C **[I]**. |
| DAP | (NH₄)₂HPO₄ | 42,9 | **62,9 [?]** | 68,9 | ~72,0 | 75,1 | [?] | **Discrepancia grande:** WST da **62,9 a 10 °C**; CB-DAP (que cita CRC) da **57,5 a 10 °C**. Diferencia 9,4 %. Ver §1.5. |
| MKP | KH₂PO₄ | 14,8 [?] | 18,3 | 22,6 | ~25,3 | 28,0 | [M2]/[?] | BOC: **14,3** / 22,7 / 33,9. CB-MKP: *22,6 g/100 mL a 20 °C* — confirma el valor de 20 °C con **tres** fuentes. 25 °C **[I]**. |
| Sulfato de magnesio | MgSO₄ | 25,5 [?] | 30,4 | 35,1 | ~37,4 | 39,7 | [M2]/[?] | CB-MgSO4 confirma **35,1 a 20 °C**, pero da **26,9 a 0 °C** contra 25,5 de WST (5,5 %). Ver base hidrato en §1.4. |
| Nitrato de magnesio | Mg(NO₃)₂ | 62,1 | 66,0 | 69,5 | ~71,6 | 73,6 | [M] | Sólo WST. Sin segunda fuente independiente. Serie internamente muy regular (+3,7/+3,5/+4,1 por década de T). |

### 1.3 MICRONUTRIENTES, AZUFRE Y BORO

| Sal | Fórmula | 0 °C | 10 °C | 20 °C | 25 °C | 30 °C | Ev. | Notas |
|---|---|---|---|---|---|---|---|---|
| Sulfato de zinc | ZnSO₄ (anhidro) | 41,6 | 47,2 | 53,8 | ~57,6 | 61,3 | [M] | WST. Base anhidra. Para el hepta y el mono ver §1.4. |
| Sulfato de manganeso | MnSO₄ (anhidro) | 52,9 | 59,7 | **62,9** | **62,9** | **62,9** | [M] | **Solubilidad retrógrada:** el máximo está en ~27 °C y luego **BAJA** (60,0 a 40 °C; 35,3 a 100 °C). Calentar el tanque *precipita* MnSO₄. Es la excepción de todo el catálogo. CB-MnSO4 publica «52 g/100 mL (5 °C), 70 g/100 mL (70 °C)» — **el 70 a 70 °C contradice frontalmente la serie retrógrada de WST.** Ver §1.5. |
| Sulfato de cobre | CuSO₄·5H₂O | 23,1 | 27,5 | 32,0 | ~34,9 | 37,8 | [M] | WST rotula la fila como **pentahidrato**. Equivalente anhidro a 20 °C = 20,5 g **[C]**. |
| Sulfato ferroso | FeSO₄ (anhidro) | s/d | s/d | **28,8** | s/d | s/d | [M]/[?] | Sólo un punto con temperatura declarada. CB-FeSO4, citando CRC 97ª ed., publica «**29,5 g/100 g** (anhidro, monohidrato, heptahidrato)» **SIN TEMPERATURA** → por la regla del §0, **no es un valor**. Los dos números son compatibles pero el de CRC no es citable. |
| Ácido bórico | H₃BO₃ | **2,52–2,59** [?] | 3,62 | **4,72–4,95** [?] | **5,7** | 6,64 | [M]/[?] | **Discrepancia sistemática ~5 %:** CB-H3BO3 da 2,52 / 4,72 / **5,7 (25 °C)** / 19,10 (80 °C); WST da 2,59 / 3,62 / 4,95 / 6,64. El **25 °C = 5,7 [M]** sólo lo tiene CB. Ver §1.5. |
| Octaborato de sodio (Solubor®) | Na₂B₈O₁₃·4H₂O | — | — | — | — | — | **[NV]** | **No verificado.** Ver §9. |
| Molibdato de sodio | Na₂MoO₄ (anhidro) | 44,1 | 64,7 | 65,3 | ~65,7 | 66,9 | [M] | WST. Salto anómalo 0→10 °C (+47 %) y luego meseta: patrón típico de **cambio de hidrato estable**. Sin segunda fuente. |
| Molibdato de amonio | (NH₄)₆Mo₇O₂₄·4H₂O | — | — | — | — | — | **[NV]** | CB-AHM publica «65,3 g/100 mL (tetrahidrato)» **SIN TEMPERATURA** → no es un valor. Además **65,3 es exactamente el valor de Na₂MoO₄ a 20 °C** en WST: hay sospecha fundada de copia cruzada entre artículos. **No usar.** Ver §9. |
| Tiosulfato de amonio (ATS) | (NH₄)₂S₂O₃ | s/d | s/d | **173** | s/d | s/d | **[M]** | CB-ATS: *173 g/100 mL a 20 °C*, con temperatura declarada. WST coincide. La sal más soluble del catálogo. |
| Tiosulfato de potasio (KTS) | K₂S₂O₃ | 96 | s/d | 155 | ~165 | 175 | [M] | WST. Sin segunda fuente. 25 °C **[I]**. |
| **Yeso** (referencia crítica) | CaSO₄·2H₂O | 0,223 | 0,244 | **0,255** | ~0,26 | 0,264 | [M] | **No es un fertilizante líquido: es el límite que mata las mezclas Ca+SO₄.** Máximo ~0,265 g/100 g a 40 °C, luego retrógrado. Ver §4. |
| **APP 10-34-0** | polifosfatos de amonio | — | — | — | — | — | n/a | **No tiene «solubilidad»: es una SOLUCIÓN, no un sólido.** Ver §6. |

### 1.4 Base HIDRATO — lo que usted realmente pesa **[C]**

Calculado con la fórmula del §0.1(a), a partir de la base anhidra del §1.2–1.3. **Son valores calculados, no medidos**, salvo donde se indica confirmación.

| Producto comercial | M (g/mol) | 20 °C, g/100 g **agua libre** [C] | 20 °C, g/100 g **agua total** [C] | Confirmación independiente |
|---|---|---|---|---|
| MgSO₄·7H₂O (sal de Epsom) | 246,47 | **113,7** | 71,9 | **CB-MgSO4: 113 g/100 mL a 20 °C** → confirma la base *agua libre*. **[M2]** |
| ZnSO₄·7H₂O | 287,54 | **165,3** | 95,8 | CBK publica **96,5 g/100 mL a 20 °C** → esa cifra está en base *agua total*. **Dos fuentes, dos convenciones distintas para la misma sal.** |
| ZnSO₄·H₂O | 179,45 | **63,6** | 59,8 | — |
| MnSO₄·H₂O | 169,01 | **76,1** | 70,4 | — |
| FeSO₄·7H₂O | 278,01 | **69,3** | 52,7 | — |
| CuSO₄·5H₂O | 249,68 | **32,0 [M]** | ~28,7 | WST ya reporta base pentahidrato. |
| Mg(NO₃)₂·6H₂O | 256,40 | **243,5** | 120,2 | — |
| Ca(NO₃)₂·4H₂O | 236,15 | **428** | 185,7 | Ver §1.5: la base de partida está en disputa. |
| Na₂MoO₄·2H₂O | 241,95 | **86,6** | 76,7 | — |

> **Por qué importa.** Si usted diseña un tanque madre de MgSO₄·7H₂O usando el 35,1 «de tabla» va a pesar **tres veces menos** producto del que el agua admite; si usa el 113 sobre agua total en vez de libre, se pasa un 57 %. La convención de la fuente **cambia el diseño del tanque**. Declárela siempre.

### 1.5 Arbitraje de discrepancias

| Caso | Valores en conflicto | Arbitraje |
|---|---|---|
| **Ca(NO₃)₂ a 20 °C** | 121,2 (chembox «anhidro») vs 129 (chembox «tetrahidrato» y WST) | **Ninguno de los dos es citable con confianza.** El 129 no puede ser el tetrahidrato en base hidrato: 129 g de tetrahidrato equivalen a sólo 89,6 g de anhidro **[C]**, lo que contradiría el 121,2 de la misma página. Lo más probable es que **ambas cifras sean base anhidra y provengan de series distintas**. La serie WST (102/115/129/152) es la clásica de Seidell y es internamente coherente. **Uso recomendado: 129 base anhidra a 20 °C, con la incertidumbre de ±6 % declarada.** |
| **DAP a 10 °C** | 62,9 (WST) vs 57,5 (CRC vía chembox) | **Se prefiere 57,5** (CRC es handbook primario; WST no cita fuente por fila). Pero note que la serie WST 42,9→62,9 (0→10 °C) tiene un salto de +47 % seguido de +9,5 % (10→20 °C), que es un perfil físicamente sospechoso; con 57,5 el perfil sería +34 %/+20 %, más plausible. **La sospecha refuerza el arbitraje.** |
| **MnSO₄ a alta T** | serie retrógrada de WST (62,9 máx, 35,3 a 100 °C) vs «70 g/100 mL a 70 °C» del chembox | **Se prefiere la serie retrógrada de WST**, porque la retrogradación del MnSO₄ por transición de hidrato es un hecho establecido y la serie es internamente coherente y monótona en cada tramo. El dato del chembox es un par suelto sin serie. Aun así, **el rango 0–30 °C —el único que importa en un tanque— no está en disputa.** |
| **H₃BO₃, sesgo ~5 %** | CB 2,52/4,72/5,7 vs WST 2,59/3,62/4,95/6,64 | **Se prefiere la serie CB** para 0/20/25 °C (procede del chembox con referencia a handbook y **es la única que tiene el punto de 25 °C medido**). Para 10 y 30 °C sólo existe WST. La discrepancia del 5 % es **irrelevante para el uso real**: el boro foliar se aplica muy por debajo de saturación. |
| **NH₄NO₃ a 20 °C** | 192 (WST + Patnaik) vs 187,7 (BOC) | **192.** Dos fuentes independientes contra una, y una de ellas es un handbook citado nominalmente (Patnaik 2002). |
| **MgSO₄ a 0 °C** | 25,5 (WST) vs 26,9 (chembox) | Sin árbitro. Diferencia 5,5 %. **Use 25,5 como valor conservador de diseño** (si diseña con el número más bajo, no precipita). |

---

## 2. Calor de disolución — por qué el tanque se enfría y la fórmula precipita

### 2.1 El mecanismo, primero

Una fórmula que «se disolvió en el laboratorio» y precipita en el campo casi nunca falla por química: falla por **temperatura**. Tres efectos se suman y **todos empujan en el mismo sentido**:

1. **La disolución endotérmica enfría el propio tanque.** Al disolver la sal, el sistema absorbe calor de la solución. El operador ve el agua enfriarse mientras revuelve.
2. **La solubilidad cae con la temperatura**, y en algunas sales cae muy rápido (§2.2).
3. **La noche del campo no es la noche del laboratorio.** Un tanque preparado a 25 °C en un galpón a 30 °C amanece a 8–12 °C.

El resultado: la fórmula se preparó cerca de saturación **a la temperatura equivocada**. La sal cristaliza durante la noche, en el fondo del tanque y dentro de los filtros.

### 2.2 La sensibilidad térmica es lo que decide, no la solubilidad absoluta

Este es el número que hay que mirar antes de formular. **Calculado [C] a partir de la tabla del §1.2:**

| Sal | S(30 °C) | S(0 °C) | **Razón S₃₀/S₀** | ΔS por cada −10 °C (20→10 °C) | Riesgo de cristalización nocturna |
|---|---|---|---|---|---|
| **KNO₃** | 45,8 | 13,3 | **3,44×** | **−34 %** | **EXTREMO** |
| Urea | ~137 | 66,7 | 2,05× | — (sin dato a 10 °C) | Alto en absoluto, moderado en relativo |
| NH₄NO₃ | 242 | 118 | 2,05× | −22 % | Alto |
| MKP | 28,0 | 14,8 | 1,89× | −19 % | Alto |
| MAP | 46,4 | 22,7 | 2,04× | −21 % | Alto |
| K₂SO₄ | 13,0 | 7,4 | 1,76× | −16 % | Alto **y sobre una base ínfima** |
| ZnSO₄ | 61,3 | 41,6 | 1,47× | −12 % | Medio |
| MgSO₄ | 39,7 | 25,5 | 1,56× | −13 % | Medio |
| KCl | 37,2 | 28,0 | **1,33×** | **−9 %** | **BAJO** |
| (NH₄)₂SO₄ | 78,1 | 70,6 | **1,11×** | **−3 %** | **MUY BAJO** |
| MnSO₄ | 62,9 | 52,9 | 1,19× | −5 % | Bajo (pero retrógrado al calentar) |

> **La lectura operativa:** el KNO₃ pierde **un tercio de su solubilidad** al bajar de 20 a 10 °C. Una solución de KNO₃ preparada al 90 % de saturación a 20 °C está **sobresaturada al 137 %** a 10 °C. El sulfato de amonio, en el otro extremo, casi no se entera del frío. **Formular con KNO₃ y formular con (NH₄)₂SO₄ son dos problemas físicos distintos**, aunque las dos sean «muy solubles».

### 2.3 La fórmula del descenso de temperatura

El enfriamiento del tanque al disolver una masa `m` (kg) de una sal de masa molar `M` (g/mol) y entalpía de disolución `ΔH_sol` (kJ/mol, **positivo = endotérmico**) en `V` litros de agua:

```
             (m · 1000 / M) · ΔH_sol
   ΔT  =  −  ─────────────────────────          [°C]
                 (V + m) · c_p
```

con `c_p ≈ 4,18 kJ·kg⁻¹·K⁻¹` (agua; la solución real tiene c_p algo menor, lo que hace el enfriamiento **peor** que el calculado — el cálculo es conservador).

### 2.4 Valores de ΔH_sol — verificados

**Convención de signo, declarada explícitamente** (es la trampa clásica de esta tabla):

| Signo | Significado | Efecto en el tanque |
|---|---|---|
| **ΔH_sol > 0** | **endotérmico**, absorbe calor | **ENFRÍA el agua** |
| ΔH_sol < 0 | exotérmico, libera calor | calienta el agua |

**Fuente primaria:** *CRC Handbook of Chemistry and Physics*, sección 5, «Enthalpy of Solution of Electrolytes», que a su vez cita **Parker, V. B., *Thermal Properties of Uni-Univalent Electrolytes*, NSRDS-NBS 2, National Bureau of Standards, 1965**. Encabezado textual de la tabla: entalpía molar de disolución **a dilución infinita**, **1 mol de soluto en agua infinita**, **kJ/mol a 25 °C**.
URL de la reproducción leída: https://www.purdue.edu/science/archive/docs/science-express/labs/Enthalpy%20of%20Solution_Reference.pdf

> **Control anti-trampa aplicado sobre la propia tabla:** HCl(g) −74,84 · NaOH(c) −44,51 · KOH(c) −57,61 salen **negativos** (son notoriamente exotérmicos), y KNO₃ +34,89 y NH₄NO₃ +25,69 —los dos clásicos de las *cold packs*— salen **positivos**. La convención queda confirmada por dentro, no por el encabezado.
>
> ⚠️ *Perry's Chemical Engineers' Handbook* y varias tablas industriales publican «heat of solution» como **calor desprendido**, con el signo invertido. **No mezclar tablas sin leer el encabezado.**

#### Las ENDOTÉRMICAS — las que enfrían el tanque

| Compuesto | ΔH_sol (kJ/mol) | ΔH_sol (kJ/kg) [C] | Fuente | Ev. |
|---|---|---|---|---|
| **KNO₃** | **+34,89** | +345,1 | CRC / Parker 1965 | **[M]** |
| **NH₄NO₃** | **+25,69** | +321,0 | CRC / Parker 1965 | **[M]** |
| NaNO₃ | +20,50 | +241,2 | CRC / Parker 1965 | [M] |
| **KCl** | **+17,22** | +231,0 | CRC / Parker 1965 | **[M]** |
| **Urea** | **+15,29** ± 0,4 % | +254,6 | Kustov & Smirnova (2010), *J. Chem. Eng. Data* 55(9):3055–3058, **DOI 10.1021/je9010689** | **[M]** * |
| NH₄Cl | +14,78 | +276,3 | CRC / Parker 1965 | [M] |
| NaCl (referencia) | +3,88 | +66,4 | CRC / Parker 1965 | [M] |

\* El valor de urea proviene del **resumen indexado** del artículo (pubs.acs.org y trc.nist.gov cortaron la conexión). El DOI aparece en dos hosts independientes, por lo que es real. Cita textual del resumen: las entalpías estándar de disolución de urea y tetrametilurea en agua bidestilada a 298,15 K fueron **15,29** y −24,80 kJ/mol, con incertidumbre estimada del 0,4 %.

**Confirmación independiente para el NH₄NO₃:** el chembox de Wikipedia (citando Patnaik, *Handbook of Inorganic Chemicals*, McGraw-Hill 2002) rotula literalmente la entrada como **«Solubility in water (endothermic)»**. **[M2]**

#### Las EXOTÉRMICAS — las que calientan

| Compuesto | ΔH_sol (kJ/mol) | Relevancia en formulación |
|---|---|---|
| KOH (c) | **−57,61** | Base de los «0-0-x líquidos sin cloro». Calienta fuerte. |
| NaOH (c) | −44,51 | Ajuste de pH |
| HNO₃ (l) | −33,28 | Acidificación |
| NH₃ (g) | −30,50 | — |

> **Las cuatro sales fertilizantes principales del catálogo son ENDOTÉRMICAS. Ninguna calienta el tanque.** Lo exotérmico en una planta de formulación es la **acidificación y la neutralización**, no la disolución de la sal.

#### La trampa del hidrato — principio confirmado, número ausente

Es un patrón termoquímico establecido: el **anhidro** libera calor al hidratarse *y luego* disolverse (exotérmico neto), mientras que el **hidrato** ya «gastó» esa energía y sólo puede absorber calor (endotérmico). La misma tabla CRC/Parker lo demuestra con ~10 pares medidos:

| Par | Anhidro | Hidratado | Δ |
|---|---|---|---|
| LiClO₄ / LiClO₄·3H₂O | **−26,55** (exo) | **+32,61** (endo) | **cambia de signo, +59,2** |
| KF / KF·2H₂O | **−17,73** (exo) | **+6,97** (endo) | **cambia de signo** |
| NaC₂H₃O₂ / ·3H₂O | **−17,32** (exo) | **+19,66** (endo) | **cambia de signo** |
| NaOH / NaOH·H₂O | −44,51 | −21,41 | +23,1 |
| LiCl / LiCl·H₂O | −37,03 | −19,08 | +17,9 |
| NaI / NaI·2H₂O | −7,53 | +16,13 | +23,7 |

> **Comprar «nitrato de calcio» o «sulfato de magnesio» sin saber si es anhidro o hidratado puede cambiar el SIGNO del efecto térmico en el tanque.** El principio está verificado; **los números concretos de Ca(NO₃)₂ y MgSO₄ NO** — ver §9.
>
> **Hallazgo estructural que explica el hueco:** la tabla del CRC procede de Parker (1965), que **por título y alcance cubre sólo electrolitos uni-univalentes (1:1)**. Por eso no puede contener (NH₄)₂SO₄, K₂SO₄, Ca(NO₃)₂ ni MgSO₄ — son 2:1, 1:2 y 2:2. **No es que falten: están fuera del alcance de la fuente.** Para esos hace falta Wagman et al. (NBS Tables, 1982) o el cálculo `ΔH_sol = ΣΔfH°(iones, aq) − ΔfH°(sólido)`.

### 2.5 Cuánto baja realmente la temperatura del tanque **[C]**

Desarrollo completo y auditable para el KNO₃, 100 kg en 1000 L:

```
n  = 100 000 g ÷ 101,103 g/mol        =    989,09 mol
Q  = 989,09 mol × 34,89 kJ/mol        = 34 509,4 kJ absorbidos del líquido
m_total = 1000 kg agua + 100 kg sal   =   1100 kg
ΔT = −34 509,4 ÷ (1100 × 4,18)        =   −7,51 K
```

| Producto | M (g/mol) | ΔH_sol | n (mol) | Q (kJ) | **ΔT** | Desde 25 °C llega a | Desde 15 °C llega a |
|---|---|---|---|---|---|---|---|
| **KNO₃** | 101,103 | +34,89 | 989,1 | 34 509 | **−7,5 °C** | 17,5 °C | **7,5 °C** |
| **NH₄NO₃** | 80,043 | +25,69 | 1249,3 | 32 095 | **−7,0 °C** | 18,0 °C | 8,0 °C |
| **Urea** | 60,056 | +15,29 | 1665,1 | 25 460 | **−5,5 °C** | 19,5 °C | 9,5 °C |
| **KCl** | 74,551 | +17,22 | 1341,4 | 23 098 | **−5,0 °C** | 20,0 °C | 10,0 °C |

**ΔT no depende del tamaño del tanque, sólo de la razón `w` = kg sal / kg agua:**

```
ΔT  =  − ( w · 1000/M · ΔH_sol ) / ( (1 + w) · c_p )
```

| Dosis de KNO₃ | w | **ΔT** |
|---|---|---|
| 100 g/L | 0,10 | −7,5 °C |
| 200 g/L | 0,20 | −13,9 °C |
| **300 g/L** | 0,30 | **−19,1 °C** |

**Salvedades del cálculo, declaradas:**
1. ΔH_sol es **a dilución infinita**; a ~1 mol/kg el valor real difiere por el calor de dilución. Tratar los ΔT como estimación de **±5–10 %**.
2. Es un cálculo **adiabático**: ignora el intercambio con las paredes y el ambiente. Con agitación (disolución en minutos) la caída se manifiesta casi completa; sin agitación, el ambiente la amortigua.
3. El c_p real de la solución es **menor** que 4,18 kJ/kg·K, de modo que **la caída real es MAYOR que la calculada**. El cálculo es conservador: con c_p = 3,80 el KNO₃ da −8,3 °C en vez de −7,5 °C.

### 2.6 Por qué la fórmula del laboratorio precipita en el campo — el caso cerrado

Junte §2.2 con §2.5. El KNO₃ a 300 g/L:

| Paso | Número | Fuente |
|---|---|---|
| El operador prepara el tanque a | **25 °C** | — |
| La disolución endotérmica lo enfría | **−19,1 °C** → **5,9 °C** | §2.5 **[C]** |
| Solubilidad del KNO₃ a ~6 °C (interpolada 0–10 °C) | **≈ 17 g/100 g H₂O = 170 g/L** | §1.2 **[I]** |
| Concentración que se quiso preparar | **300 g/L** | — |
| **Estado** | **SOBRESATURADO al 176 %** | — |

> **El tanque no «se enfrió un poco»: se pasó al otro lado de la curva de solubilidad por su propia disolución, antes de que caiga la noche.** El laboratorio no lo vio porque allí se disuelven 30 g en 100 mL — una masa térmica despreciable frente al vidrio y la mesada, con el termostato del edificio devolviendo el calor. **El error no está en la receta; está en que el ensayo se hizo a una escala donde el efecto térmico no existe.**
>
> Y después, encima, viene la noche.
>
> **Corolario operativo:** disolver el KNO₃ **primero, en agua tibia, con agitación, y esperar la recuperación térmica** antes de añadir la sal siguiente. Un dato de fabricante que respalda la agitación: 83 lb de KNO₃ por 100 gal de agua disuelven en **1 minuto con agitación** frente a **24 horas sin agitación** (instrucciones de preparación de Haifa Multi-K Greenhouse Grade publicadas por MORR Inc., 29-mar-2024 — https://morr.com/news/how-to-prepare-haifa-multi-k-greenhouse-grade-potassium-nitrate-fertilizer-in-solution/). Esa misma página advierte textualmente que *la temperatura del agua descenderá por la reacción endotérmica* entre el KNO₃ y el agua, **pero no publica ninguna cifra en °C** — la cuantificación de §2.5 es propia.

---

## 3. Índice salino (salt index)

### 3.1 La fuente original — y la corrección al título que circula

| Campo | Valor verificado |
|---|---|
| Título **real** | *The salt index — a measure of the effect of fertilizers on the concentration of the soil solution* |
| Autores | L. F. Rader Jr., Lawrence M. White, Colin W. Whittaker (Bureau of Plant Industry, USDA) |
| Publicación | *Soil Science*, **55**(3), 201–218 (1943) |
| **DOI** | **10.1097/00010694-194303000-00001** |

> El título *«The salt index of fertilizers and its relation to the growth of plants»* que circula ampliamente **no existe**.
>
> **Cómo se verificó el DOI:** el editor (LWW/Ovid) devuelve HTTP 402 y no se pudo leer la página. El DOI se confirmó en **OpenAlex W2079401058** (https://api.openalex.org/works/W2079401058), que devuelve DOI, volumen, número y páginas coincidentes con el *article-id* de Ovid `00010694-194303000-00001`. **No inventado; verificado indirectamente por dos identificadores concordantes.**

### 3.2 Definición y — el punto crítico — las condiciones de medición

```
                Presión osmótica producida por el fertilizante
   IS  =  ───────────────────────────────────────────────────────  × 100
          Presión osmótica producida por el MISMO PESO de NaNO3
```

**Las condiciones del método original de 1943 NO se pudieron verificar** (paper tras paywall). Lo que sí está documentado es que Rader et al. **declararon ellos mismos** que el resultado depende de la humedad del suelo, el intercambio de bases, **la temperatura** y el tipo de coloide. Es decir: la fuente original ya advertía que su propio número es condicional.

**El «20 °C» que se ve citado pertenece a otro método** — el moderno de conductividad de Jackson (1958), *Soil Chemical Analysis*, p. 245:

| Parámetro | Valor |
|---|---|
| Masa | 1,0 g de material (y 1,0 g de NaNO₃ patrón) |
| Volumen | 400 mL de agua desionizada |
| **Temperatura** | **20 °C** |
| Medición | **Conductividad eléctrica**, no presión osmótica |

> **Confundir los dos métodos es exactamente el error que denuncia la literatura moderna (§3.5).**

### 3.3 Tabla de índice salino — N, S

*Fuente real: Mortvedt, J.J. (2001), «Calculating Salt Index», Fluid Journal 9(2):8–11, a partir de Rader et al. (1943). Reproducida en The Andersons Technical Bulletin 09 (https://assets.andersonsplantnutrient.com/pdf/TechnicalBulletin09_CalculatingSaltIndex.pdf) y A&L Canada Fact Sheet 141 (https://alcanada.com/Tech_Bulletins/Compost_Fertilizer_Manure/Levels/141-Salt_Index.pdf).*

| Material | Análisis | **IS total** | **IS parcial** (por unidad de nutriente) |
|---|---|---|---|
| Nitrato de sodio (patrón) | 16,5 % N | 100,0 | 6,080 |
| Nitrato de amonio | 34 % N | 104,0 | 3,059 |
| Sulfato de amonio | 21 % N, 24 % S | **68,3** [?] | 3,252 |
| **Urea** | 46 % N | **74,4** | **1,618** |
| Urea (base Rader) | 46,6 % N | 75,4 | 1,618 |
| UAN 28 | 28 % N | 63,0 | 2,250 |
| **UAN 32** | 32 % N | **71,1** | 2,221 |
| Nitrato de calcio | 15,5 % N | 65,0 | 4,194 |
| Amoníaco anhidro | 82 % N | 47,1 | 0,572 |
| **ATS** | 12 % N, 26 % S | **90,4** | **7,533** |
| Polisulfuro de amonio | 20 % N, 40 % S | 59,2 | 2,960 |

### 3.4 Tabla de índice salino — P, K, Mg, Ca

| Material | Análisis | **IS total** | **IS parcial** |
|---|---|---|---|
| Superfosfato simple | 0-20-0 | 7,8 | 0,390 |
| Superfosfato triple | 0-45-0 | 10,1 | 0,224 |
| **MAP** | 11-52-0 | **26,7** | 0,405 [?] |
| **DAP** | 18-46-0 | **29,2** | 0,456 |
| **APP** | 10-34-0 | **20,0** | 0,455 |
| Ácido fosfórico | 54 % P₂O₅ | — | 1,613 * |
| **KCl (MOP)** | 60 % K₂O | **116,2** | 1,936 |
| KCl (MOP) | 62 % K₂O | 120,1 | 1,936 |
| **K₂SO₄ (SOP)** | 50 % K₂O, 18 % S | **42,6** | 0,852 |
| **KNO₃** | 13 % N, 44 % K₂O | **69,5** | 1,219 |
| **MKP** | 0-52-34 | **8,4** | **0,097** ← el más bajo del catálogo |
| Sulfato de K-Mg (SOPM) | 22 % K₂O, 11 % Mg, 22 % S | 43,4 | 1,971 |
| KTS | 25 % K₂O, 17 % S | 68,0 | 2,720 |
| Hidróxido de potasio | 83,6 % K₂O | — | 1,015 |
| Sulfato de magnesio | 10 % Mg, 14 % S | 44,0 | 2,687 |
| Óxido de magnesio | 60 % Mg | 1,7 | 0,002 |
| Yeso | 23 % Ca, 17 % S | 8,1 | 0,247 |
| Carbonato de calcio | 35 % Ca | 4,7 | 0,083 |
| Dolomita | 21,5 % Ca, 11,5 % Mg | 0,8 | 0,042 |

\* Por 100 lb de H₃PO₄, no por unidad de 20 lb.

**Regla aritmética que permite auditar cualquier fila:** `IS parcial = IS total ÷ % del nutriente`. Se usó para detectar los errores del §3.6.

**Umbral operativo (Mortvedt):** IS ≤ 20 → aplicable en surco junto a la semilla; IS > 20 → no recomendado en contacto con semilla.

### 3.5 Actualizaciones modernas — y por qué la tabla de arriba es menos firme de lo que parece

**Murray, T.P. & Clapp, J.G. (2004). «Current Fertilizer Salt Index Tables are Misleading». *Communications in Soil Science and Plant Analysis*, 35(19–20), 2867–2873. DOI: 10.1081/CSS-200036474** (verificado en OpenAlex; existe un duplicado registrado como `10.1081/LCSS-200036474`).

Argumento: las tablas en circulación **mezclan dos metodologías incompatibles** — presión osmótica en suelo (1940s) con conductividad eléctrica en solución (1950s). Al remedir cinco fuentes potásicas por CE encontraron valores **entre +28,6 % (KCl) y +141,2 % (K₂SO₄)** por encima de los originales.

**Barbier, M. et al. (2017). DOI: 10.19080/ARTOAJ.2017.06.555690** (open access, PDF leído).

| Fuente K | Rader 1943 (osmótica) | Murray & Clapp (CE) | Barbier 2017 (CE) | Berry et al. 2014 |
|---|---|---|---|---|
| MOP (KCl) | 116,3 | 149,6 | 127,8 ± 6,0 | 116 |
| SOP (K₂SO₄) | 46,1 | **111,2** | 102,8 ± 2,2 | 46 |
| SOPM | 43,2 | 64,8 | 49,1 ± 3,1 | 43 |
| Polihalita | — | — | 68,5 ± 10,8 | 87 |

> La Tabla 3 de Barbier imprime **11,2** para SOP/Murray&Clapp. Es un **error tipográfico**: el abstract de Murray & Clapp dice +141,2 % sobre el original, y 46,1 × 2,412 = **111,2**. (El MOP cuadra: 116,3 × 1,286 = 149,6.) **Use 111,2.**

**El hallazgo más incómodo de Barbier:** midieron **el mismo fertilizante en 6 laboratorios con el mismo método**. K₂SO₄: de **41,5 a 114** (media 96 ± 25). KCl: de 110 a 140,8 (media 130 ± 11).

> **La incertidumbre entre laboratorios del índice salino del K₂SO₄ es de ±25 % — mayor que muchas de las diferencias entre productos que la tabla pretende discriminar.** El índice salino **ordena** productos; **no predice daño**. Y no captura en absoluto el mecanismo **no osmótico** de toxicidad (liberación de NH₃ libre por urea, UAN, DAP y ATS).

### 3.6 Errores detectados en las tablas comerciales publicadas

| Producto | Conflicto | Arbitraje |
|---|---|---|
| **Sulfato de amonio 21 % N** | 88,3 (A&L) vs **68,3** (Andersons/Mortvedt) | **68,3.** Las tres fuentes dan el mismo IS parcial 3,252; y 3,252 × 21 = 68,3. **El 88,3 es inconsistente con la propia columna parcial de A&L** → erratum. |
| KCl 116,2 vs 120,1 | 60 % vs 62 % K₂O | Ambos correctos, distinta base de grado. Parcial idéntico. |
| Urea 74,4 vs 75,4 | 46 % vs 46,6 % N | Ambos correctos, distinta base. Parcial idéntico (1,618). |
| MAP 11-52-0, parcial 0,405 | 26,7 ÷ 63 = 0,424 | El 0,405 es del **MAP 10-50-0**. Arrastre de copia, no medición. |
| Superfosfato: IS total 7,8 para 0-16-0, 0-18-0 y 0-20-0 | — | **Artefacto de la definición** (IS total es por peso igual de material). No son tres mediciones. |

---

## 4. Ion común y salting-out en MEZCLAS: por qué la solubilidad de una mezcla no es la suma

### 4.1 El principio

La solubilidad tabulada de una sal es la de esa sal **sola en agua pura**. En una mezcla eso deja de valer por tres razones simultáneas:

**(a) Efecto de ion común.** Toda sal poco soluble obedece un producto de solubilidad `Ksp = [catión]·[anión]`. Si otra sal aporta uno de esos dos iones, el otro tiene que **bajar** para que el producto se mantenga. La solubilidad del compuesto poco soluble cae.

Ejemplo cuantificado de la literatura general (Wikipedia, *Common-ion effect*, citando Skoog et al., *Fundamentals of Analytical Chemistry*, 9ª ed., 2014): el yodato de bario pasa de **7,32 × 10⁻⁴ M** en agua pura a **1,40 × 10⁻⁴ M** al añadir 0,0200 M de nitrato de bario — **cinco veces menos**, sin haber añadido nada de yodato.
URL: https://en.wikipedia.org/wiki/Common-ion_effect

**(b) Salting-out / competencia por el agua de hidratación.** A alta fuerza iónica el agua libre escasea: cada ion se lleva su esfera de hidratación y ya no queda solvente disponible. Es el mecanismo que hace que en un tanque **muy cargado** precipite algo que en agua pura sería solubilísimo.

**(c) Salting-in (efecto sal / «uncommon-ion effect»).** El efecto contrario, también real: la misma fuente reconoce que a alta concentración iónica la atracción inter-iónica reduce las **actividades**, y la solubilidad puede **subir**. Por eso el saldo neto de una mezcla **no se puede predecir con la aritmética de la suma**: hay dos efectos de signo opuesto.

> **Conclusión dura:** la solubilidad de una mezcla no es la suma de las individuales, y tampoco es «la suma menos algo». Se determina **experimentalmente** para cada fórmula, a la temperatura más baja de la operación.

### 4.2 El caso cuantificado que decide todo: Ca²⁺ + SO₄²⁻

Este no requiere ninguna fuente exótica. Está en la tabla del §1.3:

**CaSO₄·2H₂O (yeso): 0,255 g / 100 g H₂O a 20 °C = 2,55 g/L.**
Eso equivale a **594 mg Ca/L** **[C]** (0,255 × 10 × 40,078 / 172,17 × 1000).

| Comparación | mg Ca/L |
|---|---|
| Techo impuesto por el yeso a 20 °C | **≈ 594** |
| Ca que aporta un fertirriego típico a 1 mmol/L | 40 |
| Ca en una solución madre de Ca(NO₃)₂ al 20 % p/p | **≈ 34 000** |

> Una solución madre de nitrato de calcio lleva **~57 veces** más calcio del que el sulfato tolera. **Cualquier gota de sulfato que entre en ese tanque precipita yeso**, y el yeso tiene además solubilidad **retrógrada** por encima de 40 °C: el sol del mediodía sobre el tanque lo empeora.

**El mismo razonamiento, peor todavía, con el fosfato.** Los fosfatos de calcio (di- y tricálcico) son órdenes de magnitud **menos** solubles que el yeso. Por eso la regla operativa universal del fertirriego es:

> **El calcio (y el magnesio) NUNCA comparten tanque madre con fosfatos ni con sulfatos.** Tanque A = Ca, Mg, micros quelatados. Tanque B = fosfatos, sulfatos. Se juntan sólo diluidos, en la línea.

### 4.3 KCl + KNO₃ — el caso de ion común clásico

Comparten el **K⁺**. Añadir KCl a una solución de KNO₃ deprime la solubilidad del KNO₃ y viceversa. La consecuencia práctica se lee directamente de la tabla del §1.2:

| A 20 °C | K₂O disponible en solución saturada de la sal SOLA [C] |
|---|---|
| KNO₃ solo (31,6 g/100 g H₂O) | ~11,2 % p/p K₂O |
| KCl solo (34,2 g/100 g H₂O) | ~15,2 % p/p K₂O |
| **Mezcla 50/50** | **NO es el promedio (13,2 %). Es menor, y hay que medirlo.** |

**[NV]** — No se localizó, dentro del presupuesto de esta sesión, el diagrama de fases cuantificado del sistema recíproco K⁺, NH₄⁺ // Cl⁻, NO₃⁻ – H₂O que daría el número exacto. Ver §9.

> **Pero la decisión de formulación no necesita ese número:** si va a poner K y ya tiene nitrato en la fórmula, el ion común entre KNO₃ y cualquier otra fuente de K o de NO₃⁻ juega en contra. La regla es **no acumular el mismo ion desde dos sales distintas** salvo que se haya hecho el ensayo de jarra a la temperatura mínima.

### 4.4 Urea + nitrato de amonio: la excepción que confirma el mecanismo

Es el único par de la lista donde la mezcla es **mejor** que las partes, y por eso existe el UAN como producto industrial.

Composición verificada (§6): **UAN 32 = 45 % NH₄NO₃ + 35 % urea + 20 % agua.**

| Verificación de coherencia **[C]** | UAN 28 | UAN 30 | UAN 32 |
|---|---|---|---|
| N desde NH₄NO₃ | 0,40 × 35,00 = 14,00 % | 0,42 × 35,00 = 14,70 % | 0,45 × 35,00 = 15,75 % |
| N desde urea | 0,30 × 46,65 = 14,00 % | 0,33 × 46,65 = 15,39 % | 0,35 × 46,65 = 16,33 % |
| **Total calculado** | **28,00 %** ✓ | **30,09 %** ✓ | **32,08 %** ✓ |
| Grado declarado | 28 % | 30 % | 32 % |

**Los tres grados cierran al segundo decimal.** Es la validación más limpia de todo el dossier.

Ahora el punto: para meter **80 g de sólidos en 20 g de agua** haría falta una solubilidad conjunta de **400 g/100 g H₂O**. A 20 °C, sueltas, la urea llega a 108 y el NH₄NO₃ a 192 — **la suma de las dos es 300, y la mezcla real alcanza 400**. La mezcla es un **33 % más soluble que la suma** de sus componentes.

> **Por qué:** urea y NH₄NO₃ no comparten ningún ion, y la urea es un **no electrolito** que altera la estructura del agua y las actividades iónicas favorablemente. Es *salting-in*, no *salting-out*. **Es la prueba directa de que «la mezcla no es la suma» puede fallar en los dos sentidos.**
>
> Y tiene su precio: ese 376 está tan cerca del techo que el UAN 32 **cristaliza («salts out») a temperatura ambiente baja** — ver §6.

### 4.5 Incompatibilidades duras: la tabla de lo que nunca va junto

| A | B | Qué precipita / pasa | Base |
|---|---|---|---|
| Ca²⁺ (nitrato de calcio) | SO₄²⁻ (sulfatos: MgSO₄, K₂SO₄, ZnSO₄, ATS…) | **Yeso, CaSO₄·2H₂O** | Techo 594 mg Ca/L a 20 °C **[C]** (§4.2) |
| Ca²⁺ | PO₄³⁻ / HPO₄²⁻ (MAP, DAP, MKP, APP) | **Fosfatos de calcio** | Mucho menos solubles que el yeso |
| Mg²⁺ | PO₄³⁻ + NH₄⁺ | **Estruvita, MgNH₄PO₄·6H₂O** | Cristaliza en goteros |
| **ATS / KTS** | **cualquier ácido** (H₃PO₄, ácido nítrico, fórmulas ácidas) | **AZUFRE ELEMENTAL** — el tiosulfato se descompone en medio ácido y deposita S° coloidal que tapa filtros de forma irreversible | ATS y KTS son productos **alcalinos** (§6). Nunca acidificar un tanque que los contenga. |
| DAP | medio ácido o calor | **Pierde NH₃**; se convierte en MAP. CB-DAP: «se descompone en amoníaco y fosfato monoamónico alrededor de 70 °C», y «pierde amoníaco gradualmente expuesto al aire a temperatura ambiente» | https://en.wikipedia.org/wiki/Diammonium_phosphate |
| Fe/Zn/Mn/Cu **no quelatados** | pH > ~6,5, o fosfatos | Hidróxidos y fosfatos metálicos insolubles | Por eso los micros van **quelatados (EDTA/DTPA/EDDHA)** en formulación líquida |
| Sulfatos de micros | agua dura (Ca alto) | Yeso, más co-precipitación de micros | §4.2 |

### 4.6 Orden de mezcla y ensayo de jarra

**[NV] parcial** — no se recuperó, dentro del presupuesto de esta sesión, un documento institucional de extensión que fije el orden canónico con URL. Ver §9. Lo que sí queda establecido por los datos de este dossier:

1. El tanque **nunca** se carga con dos sales incompatibles del §4.5, ni siquiera «un momento».
2. El **ensayo de jarra es obligatorio** y debe hacerse **a la temperatura mínima esperada en campo**, no a temperatura ambiente de laboratorio. Un jarro que queda claro a 25 °C y turbio a 8 °C **reprueba**.
3. El ensayo debe mantenerse **al menos 12–24 h**, porque la cristalización tiene cinética: la sobresaturación puede tardar horas en nuclear. Un jarro «claro a los 10 minutos» no prueba nada.

---

## 5. Concentración máxima práctica de solución madre (stock)

### 5.1 El criterio de diseño

La solubilidad de la tabla es un **techo termodinámico a esa temperatura**, no una concentración de trabajo. El criterio profesional:

```
C_stock  =  0,7  ×  S(T_mínima esperada en campo)
```

- **El factor 0,7** (70 % de saturación) cubre: descenso nocturno adicional, error de pesada, impurezas del fertilizante grado técnico, y el efecto de ion común con los demás componentes.
- **T_mínima, no T de preparación.** Es el error que produce la precipitación descrita en §2.1.

### 5.2 Tabla de diseño **[C]**, calculada sobre la tabla del §1.2

Dos escenarios: clima cálido (mínima 20 °C) y clima con noches frescas (mínima 10 °C).

| Sal | S(20 °C) | **Stock máx. si T_mín = 20 °C** (g/L de agua) | S(10 °C) | **Stock máx. si T_mín = 10 °C** (g/L de agua) | Pérdida por el frío |
|---|---|---|---|---|---|
| Urea | 108 | **756** | s/d | ~(600) [I] | — |
| NH₄NO₃ | 192 | **1 344** | 150 | **1 050** | −22 % |
| (NH₄)₂SO₄ | 75,4 | **528** | 73,0 | **511** | **−3 %** |
| **KNO₃** | 31,6 | **221** | 20,9 | **146** | **−34 %** ← el peor |
| KCl | 34,2 | **239** | 31,2 | **218** | −9 % |
| **K₂SO₄** | 11,1 | **78** | 9,3 | **65** | −16 % ← techo absoluto ínfimo |
| MAP | 37,4 | **262** | 29,5 | **207** | −21 % |
| DAP | 68,9 | **482** | 57,5 | **403** | −17 % |
| MKP | 22,6 | **158** | 18,3 | **128** | −19 % |
| MgSO₄·7H₂O (agua libre) | 113,7 [C] | **796** | 91,3 [C] | **639** | −20 % |
| Ca(NO₃)₂·4H₂O (agua libre) | 428 [C] | **≈3 000** | 334 [C] | **≈2 340** | −22 % |
| ATS (sol. comercial) | — | se usa **puro**, no se rediluye | — | — | — |

> **Los dos números que gobiernan el diseño de una línea de fertirriego:**
> **K₂SO₄ tope 78 g/L a 20 °C** y **KNO₃ tope 221 g/L a 20 °C**, que caen a 65 y 146 g/L si las noches bajan a 10 °C.
> Si su plan de nutrición pide más K que eso, **el K no cabe en ese tanque** y hay que abrir un segundo tanque o cambiar a KCl.

### 5.3 Regla de dilución de inyección

Con `R` = razón de inyección del inyector (p. ej. 1:100 → R = 100):

```
C_stock = C_riego · R                y  la restricción es      C_riego · R  ≤  0,7 · S(T_min)
```

**Dos límites independientes que hay que satisfacer a la vez:**

| Límite | Qué controla | Consecuencia si se viola |
|---|---|---|
| **Límite de solubilidad**, en el tanque madre: `C_stock ≤ 0,7 · S(T_mín)` | Precipitación en el tanque y en el filtro | Tanque tapado, dosis real desconocida |
| **Límite de CE**, en la línea de riego: `CE_final ≤` tolerancia del cultivo | Estrés salino en la raíz | Daño al cultivo, aunque el tanque esté perfecto |

> Un inyector a 1:200 exige un tanque madre **el doble de concentrado** que uno a 1:100 — y por eso **la razón de inyección, no la receta, es lo que suele hacer imposible una fórmula.** Bajar de 1:200 a 1:100 duplica la holgura de solubilidad sin cambiar un gramo de la nutrición entregada.

**Orden de carga del tanque madre (deriva de §2 y §4):**
1. Llenar el tanque a **~⅔ de agua**, a la temperatura más alta razonablemente disponible.
2. Disolver **primero las sales endotérmicas** (KNO₃ el primero) **con agitación**, y **esperar a que la temperatura se recupere** antes de añadir la siguiente.
3. Micros quelatados y ácidos **al final**.
4. Completar a volumen. **Nunca** cargar ATS/KTS junto a nada ácido (§4.5).

---

## 6. Densidad y pH de las soluciones comerciales concentradas

### 6.1 UAN — verificado, incluido el salt-out

Fuente: Wikipedia, *UAN* — https://en.wikipedia.org/wiki/UAN

| Grado | % N | % NH₄NO₃ | % urea | % H₂O | **Densidad relativa @ 16 °C** | **Salt-out (cristalización)** |
|---|---|---|---|---|---|---|
| **UAN 28** | 28 | 40 | 30 | 30 | **1,283** | **−18 °C** |
| **UAN 30** | 30 | 42 | 33 | 25 | **1,303** | **−10 °C** |
| **UAN 32** | 32 | 45 | 35 | 20 | **1,320** | **−2 °C** |

**Ev. [M2]** — la composición está **confirmada por cierre estequiométrico independiente**: los tres grados reproducen su N declarado al segundo decimal (§4.4).

> **Discrepancia menor:** A&L Canada FS-141 y The Andersons TB-09 dan **44 % NH₄NO₃ + 35 % urea** para el UAN 32 y **39 + 31** para el UAN 28. **Se prefiere la composición de arriba** porque es la única que cierra exactamente contra el grado declarado (32,08 y 28,00 vs 31,7 y 28,1). El arbitraje es aritmético, no de autoridad.

**El salt-out del UAN 32 a −2 °C es el dato operativo más importante de esta sección**, y la física detrás está en §4.4: el UAN 32 aloja 80 g de sólidos en 20 g de agua, lo que exige una solubilidad conjunta de **400 g/100 g H₂O** contra una suma individual de 300 a 20 °C. **Opera un 33 % por encima de la suma de sus partes y por lo tanto muy cerca de su techo.** Por eso el 32 cristaliza casi a 0 °C y el 28 —con 30 % de agua en vez de 20 %— aguanta hasta −18 °C. **Es exactamente la razón por la que el UAN 28 se usa en climas fríos y el 32 en cálidos.**

**pH del UAN: [NV]** — el artículo no lo publica. Sí advierte que las soluciones UAN son **corrosivas para el acero al carbono** y exigen inhibidores de corrosión en el almacenamiento.

### 6.2 ATS y KTS — concentración real derivada por cierre estequiométrico

| Producto | Dato | Ev. | Base del cálculo |
|---|---|---|---|
| **ATS 12-0-0-26S** | **≈ 60 % p/p de (NH₄)₂S₂O₃** | **[C]** | La sal pura es 18,90 % N y 43,27 % S (§7). 0,60 × 18,90 = **11,3 % N**; 0,60 × 43,27 = **26,0 % S**. **El azufre cierra exacto contra el grado 26S.** |
| **KTS 0-0-25-17S** | **≈ 50,5 % p/p de K₂S₂O₃** | **[C]** | La sal pura es 49,49 % K₂O y 33,69 % S (§7). 0,505 × 49,49 = **25,0 % K₂O**; 0,505 × 33,69 = **17,0 % S**. **Los dos cierran exactos.** |
| Coherencia con §1.3 | El ATS al 60 % p/p equivale a **150 g de sal por 100 g de agua**, contra una solubilidad medida de **173 g/100 g a 20 °C**. La solución comercial está al **87 % de saturación**. | **[C]** | Consistente: es un producto formulado cerca del techo, como el UAN. |
| ATS/KTS + ácido | Descomposición con depósito de **azufre elemental**; ambos son productos **alcalinos** | [M] | §4.5 |

**Densidad y pH de ATS y KTS: [NV].** Ver §9.

### 6.3 APP 10-34-0

Es una **solución de polifosfatos de amonio**, no una sal disuelta: no tiene «solubilidad». Su capacidad de **secuestrar micronutrientes** proviene de que la cadena de polifosfato actúa como agente quelante — de ahí que sea el vehículo habitual para llevar Zn en líquido. Índice salino **20,0** (§3.4), el más bajo de las fuentes de P líquidas de alto grado, y justo en el umbral de aplicación en surco.

**Densidad, pH, y relación orto/poli: [NV].** Ver §9.

### 6.4 Nitrato de calcio

| Forma | Análisis | Ev. |
|---|---|---|
| **Sal doble comercial** 5Ca(NO₃)₂·NH₄NO₃·10H₂O | **15,5-0-0 + 19 % Ca** | [M] — https://en.wikipedia.org/wiki/Calcium_nitrate |
| Verificación estequiométrica de la sal doble | M = 1080,6 g/mol → **15,55 % N, 18,54 % Ca** ✓ | **[C]** — cierra |
| Grado de invernadero, tetrahidrato Ca(NO₃)₂·4H₂O | **11,9-0-0 + 16,9 Ca** | [M2] — cierra contra el cálculo de §7 (11,86 / 16,97) |
| Anhidro | **17-0-0 + 23,6 Ca** | [M] |

> **El «nitrato de calcio» del mercado suele ser la sal doble, que TRAE AMONIO.** Eso importa dos veces: (a) el N no es todo nítrico, y (b) el amonio participa en la formación de **estruvita** con Mg y fosfato (§4.5). Pedir «nitrato de calcio» sin especificar la forma es pedir tres productos distintos.

**Densidad y pH del nitrato de calcio líquido: [NV].** Ver §9.

---

## 7. Aporte de nutriente: % garantizado y kg de nutriente por kg de producto

### 7.1 Composición estequiométrica exacta **[C]**

Calculada con pesos atómicos IUPAC 2021. `%P₂O₅ = %P × 2,2914`; `%K₂O = %K × 1,2046`.
**Estos son los máximos teóricos de una sal pura.** El grado comercial siempre es igual o menor.

| Materia prima | Fórmula | M (g/mol) | %N | %P₂O₅ | %K₂O | %Ca | %Mg | %S | Micro | Grado comercial típico | ✓ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Urea | CO(NH₂)₂ | 60,06 | **46,65** | — | — | — | — | — | — | 46-0-0 | ✓ |
| Nitrato de amonio | NH₄NO₃ | 80,04 | **35,00** | — | — | — | — | — | — | 34-0-0 | ✓ |
| Sulfato de amonio | (NH₄)₂SO₄ | 132,13 | **21,20** | — | — | — | — | **24,26** | — | 21-0-0-24S | ✓ |
| Nitrato de calcio tetrahidr. | Ca(NO₃)₂·4H₂O | 236,15 | **11,86** | — | — | **16,97** | — | — | — | 11,9-0-0 + 16,9 Ca | ✓ |
| — sal doble comercial | 5Ca(NO₃)₂·NH₄NO₃·10H₂O | 1080,6 | **15,55** | — | — | **18,54** | — | — | — | 15,5-0-0 + 19 Ca | ✓ |
| Nitrato de potasio | KNO₃ | 101,10 | **13,85** | — | **46,58** | — | — | — | — | 13-0-46 | ✓ |
| Cloruro de potasio | KCl | 74,55 | — | — | **63,18** | — | — | — | Cl 47,55 | 0-0-60 / 0-0-62 | ✓ |
| Sulfato de potasio | K₂SO₄ | 174,25 | — | — | **54,06** | — | — | **18,40** | — | 0-0-50 + 18S | ✓ |
| MAP | NH₄H₂PO₄ | 115,03 | **12,18** | **61,70** | — | — | — | — | — | 12-61-0 (téc.) / 11-52-0 | ✓ |
| DAP | (NH₄)₂HPO₄ | 132,06 | **21,21** | **53,74** | — | — | — | — | — | 18-46-0 | ✓ |
| MKP | KH₂PO₄ | 136,08 | — | **52,15** | **34,61** | — | — | — | — | 0-52-34 | ✓ |
| Sulfato de magnesio heptahidr. | MgSO₄·7H₂O | 246,47 | — | — | — | — | **9,86** | **13,01** | — | 9,8 Mg + 13 S (16 % MgO) | ✓ |
| Nitrato de magnesio hexahidr. | Mg(NO₃)₂·6H₂O | 256,40 | **10,93** | — | — | — | **9,48** | — | — | 11-0-0 + 9,5 Mg | ✓ |
| Sulfato de zinc heptahidr. | ZnSO₄·7H₂O | 287,54 | — | — | — | — | — | 11,15 | **Zn 22,74** | 21–22 % Zn | ✓ |
| Sulfato de zinc monohidr. | ZnSO₄·H₂O | 179,45 | — | — | — | — | — | 17,87 | **Zn 36,43** | 35–36 % Zn | ✓ |
| Sulfato de manganeso monohidr. | MnSO₄·H₂O | 169,01 | — | — | — | — | — | 18,97 | **Mn 32,51** | 31–32 % Mn | ✓ |
| Sulfato de cobre pentahidr. | CuSO₄·5H₂O | 249,68 | — | — | — | — | — | 12,84 | **Cu 25,45** | 25 % Cu | ✓ |
| Sulfato ferroso heptahidr. | FeSO₄·7H₂O | 278,01 | — | — | — | — | — | 11,53 | **Fe 20,09** | 19–20 % Fe | ✓ |
| Ácido bórico | H₃BO₃ | 61,83 | — | — | — | — | — | — | **B 17,48** | 17 % B | ✓ |
| Octaborato de sodio tetrahidr. | Na₂B₈O₁₃·4H₂O | 412,51 | — | — | — | — | — | — | **B 20,96** | Solubor® **20,5 % B** | ✓ |
| Molibdato de sodio dihidr. | Na₂MoO₄·2H₂O | 241,96 | — | — | — | — | — | — | **Mo 39,66** | 39 % Mo | ✓ |
| Heptamolibdato de amonio | (NH₄)₆Mo₇O₂₄·4H₂O | 1235,92 | 6,80 | — | — | — | — | — | **Mo 54,34** | 54 % Mo | ✓ |
| Tiosulfato de amonio (sal pura) | (NH₄)₂S₂O₃ | 148,19 | **18,90** | — | — | — | — | **43,27** | — | *(la solución es 12-0-0-26S)* | ✓ |
| Tiosulfato de potasio (sal pura) | K₂S₂O₃ | 190,31 | — | — | **49,49** | — | — | **33,69** | — | *(la solución es 0-0-25-17S)* | ✓ |

**Columna «✓»: cada fila fue contrastada contra el grado comercial declarado en la literatura.** Las 24 filas cierran. Esta es una **auditoría interna del dossier**: si un valor calculado no cerrara contra el grado de mercado, indicaría un error de fórmula o de peso molecular.

### 7.2 kg de nutriente por kg de producto

Es la misma tabla ÷ 100. Ejemplos de lectura:

| Para aportar… | …necesita | **[C]** |
|---|---|---|
| 1 kg de N | 2,14 kg de urea · 2,86 kg de NH₄NO₃ · 4,72 kg de (NH₄)₂SO₄ · 7,22 kg de KNO₃ | 1 ÷ %N × 100 |
| 1 kg de K₂O | 1,58 kg de KCl · 1,85 kg de K₂SO₄ · 2,15 kg de KNO₃ · 2,89 kg de MKP | 1 ÷ %K₂O × 100 |
| 1 kg de P₂O₅ | 1,62 kg de MAP(puro) · 1,86 kg de DAP(puro) · 1,92 kg de MKP | 1 ÷ %P₂O₅ × 100 |
| 1 kg de Ca | 5,89 kg de Ca(NO₃)₂·4H₂O · 5,39 kg de la sal doble 15,5-0-0 | 1 ÷ %Ca × 100 |
| 1 kg de Zn | 4,40 kg de ZnSO₄·7H₂O · **2,74 kg** de ZnSO₄·H₂O | El monohidrato ahorra **38 % de flete** |
| 1 kg de B | 5,72 kg de H₃BO₃ · **4,77 kg** de Solubor® | — |

> **Nota de coherencia entre §7 y §1:** el heptahidrato de zinc tiene **más del doble** de solubilidad aparente que el monohidrato en base agua libre (165 vs 64 g/100 g a 20 °C, §1.4) **pero aporta un 38 % menos de Zn por kg**. Ambos efectos se cancelan casi exactamente en términos de **g de Zn por litro de solución saturada**. La elección entre hepta y mono es de **flete y de manejo**, no de solubilidad efectiva.

---

## 8. LO QUE NO SE PUEDE — los límites físicos duros de la formulación líquida

### 8.1 No existe un 20-20-20 líquido claro y estable. Y el número que lo demuestra

Un 20-20-20 líquido exige **20 g de P₂O₅ por cada 100 g de solución final**.

La única fuente de P que da una solución **clara, neutra y compatible con K** es el **MKP (0-52-34)**. Calculemos su techo **[C]**:

A 20 °C, S(MKP) = 22,6 g/100 g H₂O → fracción másica en la solución **saturada** = 22,6/122,6 = **18,43 % p/p de MKP**.

```
   %P2O5 máximo  =  18,43 %  ×  52,15 / 100  =  9,61 %
   %K2O   que viene con él  =  18,43 %  ×  34,61 / 100  =  6,38 %
```

| A 20 °C, **saturación absoluta** de MKP | Valor **[C]** |
|---|---|
| % P₂O₅ máximo alcanzable | **9,61 %** |
| % K₂O que lo acompaña obligatoriamente | 6,38 % |
| **A la concentración de trabajo (70 % de saturación)** | **≈ 6,7 % P₂O₅** |

> ### El número:
> **El techo termodinámico de P₂O₅ en una solución acuosa clara de MKP a 20 °C es 9,61 %. Un 20-20-20 pide 20 %. Está a un factor de 2,1 de lo físicamente posible — y eso ya en saturación absoluta, sin margen, sin nitrógeno y sin el resto del potasio.**
>
> A 10 °C el techo cae a **8,07 %** **[C]**; a la concentración de trabajo (70 %), a **5,6 %**.

**Por eso el 20-20-20 sólo existe como POLVO SOLUBLE.** El polvo no tiene que llevar el agua a cuestas: el productor lo disuelve al 1–2 % en el momento, donde nada está cerca de saturación. **Un sólido soluble y un líquido claro no compiten en la misma categoría física.**

Los grados líquidos claros que sí existen en el mercado —3-18-18, 2-20-20, 6-24-6, 9-18-9 (§3.5)— **todos tienen la suma N+P+K muy por debajo de 60**, y los que llegan a 20 de P₂O₅ lo hacen bajando el N y el K a cambio.

### 8.2 El techo del K en solución clara **[C]**

| Fuente | S(20 °C) | % p/p en saturación | **% K₂O máximo** | Obstáculo |
|---|---|---|---|---|
| KCl | 34,2 | 25,5 % | **16,1 %** | Aporta **12,1 % de cloruro** — inaceptable en muchos cultivos |
| KNO₃ | 31,6 | 24,0 % | **11,2 %** | Cae a **8,05 %** a 10 °C (−28 %) |
| MKP | 22,6 | 18,4 % | **6,4 %** | Arrastra 9,6 % de P₂O₅ |
| **K₂SO₄** | 11,1 | 10,0 % | **5,4 %** | **El techo más bajo del catálogo** |

> **Ningún fertilizante potásico soluble permite superar ~16 % de K₂O en una solución acuosa clara a 20 °C, y el único que llega ahí es el cloruro.** El «0-0-30 líquido» sin cloro no existe con sales convencionales; requiere hidróxido/carbonato de potasio, que traen su propio problema de pH.

### 8.3 El techo del N — y por qué éste sí es alto

| Fuente | % N máximo en solución clara a 20 °C **[C]** |
|---|---|
| Urea sola (S = 108) | 51,9 % p/p urea → **24,2 % N** |
| NH₄NO₃ solo (S = 192) | 65,8 % p/p → **23,0 % N** |
| **UAN 32 (mezcla real)** | **32 % N** |

> **El N es el único macronutriente que rompe el techo de sus componentes individuales** (§4.4), y por eso el UAN existe como producto y el «UAP» o el «UAK» equivalentes no. **La ventaja del N no se puede trasladar al P ni al K: es específica de que la urea sea un no electrolito.**

### 8.4 Los cinco límites duros, en una tabla

| # | Límite | El número que lo demuestra | Consecuencia |
|---|---|---|---|
| **1** | **No hay NPK alto en una sola solución clara** | P₂O₅ máx = **9,61 %** a 20 °C (MKP saturado); un 20-20-20 pide 20 % | Los grados altos existen sólo como **polvo soluble** |
| **2** | **El calcio y el fósforo/azufre no coexisten concentrados** | Yeso: **594 mg Ca/L** de techo a 20 °C, contra ~34 000 mg/L en una madre de Ca(NO₃)₂ | Obliga a **dos tanques madre** siempre. No es una precaución: es aritmética |
| **3** | **El K₂SO₄ es la pared del potasio sin cloro** | **11,1 g/100 g H₂O a 20 °C** — 3× menos soluble que el KCl, 5× menos que el NH₄NO₃ | El azufre y el potasio juntos, sin cloro, **no caben** en un tanque concentrado |
| **4** | **La temperatura mínima manda, no la de preparación** | KNO₃ pierde **34 %** de solubilidad de 20 a 10 °C | Toda fórmula debe validarse **a T mínima de campo**, con jarra de 12–24 h |
| **5** | **El tanque se enfría solo, antes de que caiga la noche** | Disolver KNO₃ a 300 g/L baja la temperatura **−19,1 °C** por endotermia propia (ΔH_sol = +34,89 kJ/mol) | Una fórmula validada en vaso de precipitado **no está validada**: a escala de laboratorio el efecto térmico no existe |

### 8.5 La regla que resume el dossier

> **En formulación líquida no se formula contra una receta agronómica: se formula contra la sal menos soluble, a la noche más fría del año.**
>
> Todo lo demás —el índice salino, el pH, la densidad— es optimización dentro de ese margen. Ese margen lo fija, casi siempre, **el K₂SO₄ (11,1 g/100 g a 20 °C)** si hay que aportar S y K sin cloro, o el **techo del yeso (594 mg Ca/L)** si hay que aportar Ca junto a cualquier otra cosa.

---

## 9. NO VERIFICADO

Lo que sigue **no** se pudo verificar contra fuente primaria dentro de esta sesión. Se declara qué se buscó y por qué falló. **Ninguno de estos valores fue inventado ni estimado en el cuerpo del dossier.**

| # | Ítem | Qué se buscó | Por qué falló / estado |
|---|---|---|---|
| 1 | **ΔH_sol de las sales NO uni-univalentes: Ca(NO₃)₂ (anhidro y ·4H₂O), MgSO₄ (anhidro y ·7H₂O), (NH₄)₂SO₄, K₂SO₄, MAP, MKP, y la dilución de H₃PO₄ y H₂SO₄** | NIST NSRDS-NBS 2 (`srd.nist.gov`, `nvlpubs.nist.gov` — *socket closed*, 4 intentos) · NBS Tables Wagman 1982 (`srd.nist.gov/JPCRD/jpcrdS2Vol11.pdf` — *socket closed*) · NIST WebBook (3 intentos) · CRC completo (`dl.icdst.org`, `mathguy.us`) · LibreTexts, OpenStax, archive.org | **Causa raíz identificada:** la tabla del CRC procede de Parker (1965), **limitada por alcance a electrolitos 1:1**. Estas sales no están ausentes por descuido — están fuera del alcance de la fuente. **Ruta correcta para R2:** Wagman et al. 1982, o `ΔH_sol = ΣΔfH°(iones,aq) − ΔfH°(sólido)`. Las cuatro sales pedidas explícitamente (KNO₃, urea, NH₄NO₃, KCl) **SÍ quedaron verificadas** (§2.4). |
| 1b | **Único dato hallado para (NH₄)₂SO₄, descartado** | Página de proveedor comercial (Alfa Chemistry): «integral heat of solution 6,57 kJ/mol a 30 °C; diferencial en saturación 6,07 kJ/mol a 30 °C» | **Descartado:** proveedor comercial sin cita primaria, a **30 °C y no 25 °C**, y es entalpía **integral**, no a dilución infinita. No es comparable con la tabla del §2.4. |
| 1c | **Tabla de «heat of solution» de un documento técnico de IFA — TRAMPA DETECTADA Y DESCARTADA** | `fertilizer.org/.../2002_tech_laurent.pdf` (ECONNRESET ×2) | Aparece indexada con valores **en kJ/kg y con signo NEGATIVO para lo endotérmico** (KNO₃ +26, urea −81, UAN 32 % −55 kJ/kg). **Irreconciliable con el CRC en cualquier base** (urea CRC = +254,6 kJ/kg endotérmico). Casi con seguridad son calores por kg de **solución final** en el proceso de fabricación de UAN, no ΔH_sol del soluto. **No se reportó ninguno de esos números.** Si esta tabla reaparece, resolver primero su base y su convención. |
| 2 | **pH de UAN, ATS, KTS, APP y nitrato de calcio líquido; densidad de ATS, KTS, APP y nitrato de calcio líquido; relación orto/poli del APP** | Fichas técnicas de fabricante (Tessenderlo Kerley Thio-Sul®, Mosaic, Nutrien, Yara, ICL) y publicaciones de extensión | Investigación delegada **no concluida al cierre de la sesión**. **Lo que SÍ se cerró en §6:** composición, densidad relativa (@ 16 °C, temperatura declarada) y **punto de salt-out de los tres grados de UAN**, más las concentraciones reales de ATS y KTS derivadas por cierre estequiométrico. **Lo que falta es pH y densidad de los tiosulfatos, el APP y el nitrato de calcio líquido.** |
| 3 | **Solubilidad de Solubor® (octaborato de sodio) con temperatura** | Ficha técnica US Borax `agriculture.borax.com/.../solubor.pdf` (3 intentos: *socket hang up*, PDF binario no parseable, sin librería PDF en el entorno) y SDS de distribuidores | **Sin valor citable.** El %B (20,5) sí está verificado. La solubilidad, no. |
| 4 | **Solubilidad del molibdato de amonio** | Chembox de Wikipedia | Publica «65,3 g/100 mL» **sin temperatura** → por la regla del §0 no es un valor. Además coincide exactamente con el Na₂MoO₄ a 20 °C: **sospecha fundada de copia cruzada entre artículos.** No usar. |
| 5 | **Diagrama de fases cuantificado KCl + KNO₃** (sistema recíproco K⁺,NH₄⁺//Cl⁻,NO₃⁻–H₂O) (§4.3) | Literatura de equilibrio de sales recíprocas | No localizado. **El efecto de ion común queda establecido cualitativamente y con el ejemplo cuantificado del Ba(IO₃)₂ (5×), pero no hay número propio para el par KCl/KNO₃.** |
| 6 | **Documento institucional que fije el orden canónico de mezcla en tanque (§4.6)** | Publicación de servicio de extensión o fabricante con URL | No recuperado. Las tres reglas del §4.6 se derivan de los datos de este dossier, no de una fuente citable. |
| 7 | **Condiciones (concentración, temperatura) del método ORIGINAL de Rader et al. 1943** | Paper original en LWW/Ovid | **HTTP 402 Payment Required.** Sólo se verificó la definición y la advertencia de los propios autores. **El «20 °C» que circula pertenece al método de Jackson (1958), no a Rader.** |
| 8 | **DOI de Mortvedt (2001), Fluid Journal 9(2):8–11** | OpenAlex, búsqueda por título y autor | *Fluid Journal* es publicación gremial sin registro Crossref localizable. **No hay DOI.** El contenido está reproducido y atribuido en The Andersons TB-09 (leído). |
| 9 | **Valores de Murray & Clapp para KNO₃ y KTS** | Paper tras paywall (Taylor & Francis) | Sólo se recuperaron MOP, SOP y SOPM vía Barbier 2017. |
| 10 | **Clapp, J.G. (2007), Indiana CCA Proceedings, Purdue** | 5 variantes de URL → 404; archive.org y ResearchGate bloqueados | No leído. Su contenido está cubierto por la versión revisada por pares (Murray & Clapp 2004), que sí está verificada. |
| 11 | **Fuente por fila de la tabla WST de Wikipedia** | El artículo no cita fuente fila por fila | Motivo por el cual **todo valor de WST se cruzó contra una segunda fuente** en §1. Los que no tienen segunda fuente están marcados `[M]` sin `[M2]`: **Mg(NO₃)₂, Na₂MoO₄, KTS y la serie de MnSO₄.** |

### 9.1 Presupuesto de búsqueda

La sesión agotó su cuota de búsqueda web (200/200) antes del cierre. Los ítems 1, 2, 3 y 5 son los que quedaron cortados por ese límite y son **la continuación natural de este dossier (R2)**.

---

## 10. Fuentes efectivamente leídas

| Fuente | URL | Uso |
|---|---|---|
| Wikipedia, *Solubility table* (wikitext crudo) | https://en.wikipedia.org/wiki/Solubility_table | §1 — tabla base (con el defecto de columnas documentado en §0.1b) |
| BOC Sciences, *Water Solubility Table at Temperatures* | https://www.bocsci.com/support-documents/water-solubility-table-at-temperatures.html | §1 — **confirmación independiente** de la alineación de columnas y de 7 sales |
| Wikipedia chembox — Urea (cita CRC Handbook 97ª ed.) | https://en.wikipedia.org/wiki/Urea | §1 — 25 °C |
| Wikipedia chembox — Potassium nitrate | https://en.wikipedia.org/wiki/Potassium_nitrate | §1 — 25 °C |
| Wikipedia chembox — Potassium chloride / sulfate / Monopotassium phosphate | (respectivas) | §1 |
| Wikipedia chembox — Ammonium nitrate (cita Patnaik 2002) | https://en.wikipedia.org/wiki/Ammonium_nitrate | §1, §2.4 (endotérmico declarado) |
| Wikipedia chembox — Diammonium phosphate | https://en.wikipedia.org/wiki/Diammonium_phosphate | §1.5, §4.5 (pérdida de NH₃) |
| Wikipedia chembox — Calcium nitrate | https://en.wikipedia.org/wiki/Calcium_nitrate | §1.5, §6.4, §7 (sal doble) |
| Wikipedia — *UAN* | https://en.wikipedia.org/wiki/UAN | §6.1 — composición, densidad @16 °C y salt-out de UAN 28/30/32 |
| Wikipedia chembox — Magnesium sulfate | https://en.wikipedia.org/wiki/Magnesium_sulfate | §1.4 — **validación de la fórmula de conversión de hidrato (113 g/100 mL)** |
| Wikipedia chembox — Manganese(II) sulfate / Iron(II) sulfate / Boric acid / Sodium molybdate / Ammonium heptamolybdate / Ammonium thiosulfate | (respectivas) | §1.3, §1.5, §9 |
| ChemicalBook — Zinc sulphate | https://www.chemicalbook.com/ChemicalProductProperty_EN_CB2727299.htm | §1.4 |
| Wikipedia, *Common-ion effect* (cita Skoog et al. 2014) | https://en.wikipedia.org/wiki/Common-ion_effect | §4.1 |
| **CRC Handbook of Chemistry and Physics**, secc. 5, «Enthalpy of Solution of Electrolytes» (cita **Parker, V.B., NSRDS-NBS 2, 1965**) | https://www.purdue.edu/science/archive/docs/science-express/labs/Enthalpy%20of%20Solution_Reference.pdf | §2.4 — todos los ΔH_sol |
| **Kustov & Smirnova (2010)**, *J. Chem. Eng. Data* 55(9):3055–3058 | DOI **10.1021/je9010689** (resumen indexado; ACS y NIST cortaron conexión) | §2.4 — ΔH_sol de la urea |
| MORR Inc. — preparación de Haifa Multi-K Greenhouse Grade (KNO₃) | https://morr.com/news/how-to-prepare-haifa-multi-k-greenhouse-grade-potassium-nitrate-fertilizer-in-solution/ | §2.6 — advertencia de endotermia y dato de agitación |
| **Rader, White & Whittaker (1943)**, Soil Science 55(3):201–218 | DOI 10.1097/00010694-194303000-00001 (vía OpenAlex W2079401058) | §3.1 |
| **Murray & Clapp (2004)**, Commun. Soil Sci. Plant Anal. 35(19-20):2867-2873 | DOI 10.1081/CSS-200036474 | §3.5 |
| **Barbier et al. (2017)** | DOI 10.19080/ARTOAJ.2017.06.555690 · https://juniperpublishers.com/artoaj/pdf/ARTOAJ.MS.ID.555690.pdf | §3.5 |
| The Andersons Technical Bulletin 09 (Mortvedt) | https://assets.andersonsplantnutrient.com/pdf/TechnicalBulletin09_CalculatingSaltIndex.pdf | §3.3–3.4 |
| A&L Canada Laboratories, Fact Sheet 141 | https://alcanada.com/Tech_Bulletins/Compost_Fertilizer_Manure/Levels/141-Salt_Index.pdf | §3.3–3.4 |
| SEGES / Landbrugsinfo Pl_19_4578 | https://projekter.seges.dk/-/media/projectreport/projectdocuments/Promilleafgiftsfonden%20for%20landbrug/Promilleafgiftsfonden%20for%20landbrug%20-%202019/4578/Pl_19_4578_Calculating_fertilizer_salt_index.ashx | §3.3–3.4 |

**Fallaron (no leídas):** journals.lww.com y ovid.com (HTTP 402) · agriculture.borax.com (socket hang up ×3) · ipipotash.org (403) · haifa-group.com (socket hang up ×2) · sigmaaldrich.com (ECONNRESET) · agry.purdue.edu (404) · researchgate.net (403) · tandfonline.com · spectrumanalytic.com · web.archive.org · anz.ipni.net (TLS inválido) · grdc.com.au.
