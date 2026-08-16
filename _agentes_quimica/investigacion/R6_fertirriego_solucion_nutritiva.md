# R6 — FERTIRRIEGO E INYECCIÓN DE SOLUCIONES NUTRITIVAS AL SUELO
### Dossier de investigación verificado
**Fecha:** 2026-08-16 · **Ámbito:** riego localizado (goteo/microaspersión) + aplicación líquida localizada en extensivo
**Regla de la casa:** un umbral sin método declarado no se transfiere de una región a otra.

---

## 0. CÓMO LEER ESTE DOSSIER

Tres marcas aparecen a lo largo del texto:

| Marca | Significado |
|---|---|
| **[V]** | Valor tomado literal de la fuente citada, con DOI verificado en Crossref o URL institucional que se abrió y se leyó. |
| **[C]** | Cálculo propio a partir de constantes fisicoquímicas tabuladas (pesos equivalentes, densidades, pKa). La aritmética se muestra para que se pueda auditar. |
| **[NV]** | No verificado. Va en la tabla del §9 y **no se usa para decidir**. |

Y una advertencia estructural que condiciona todo el §1:

> **Las guías de calidad de agua de FAO 29 NO fueron escritas para goteo.** El propio documento declara sus supuestos: textura franco-arenosa a franco-arcillosa con buen drenaje interno, clima semiárido a árido, lluvia que no cubre la demanda ni el lavado, riego **superficial o por aspersión** aplicado con poca frecuencia, y **fracción de lavado ≥ 15 %**. Y dice textualmente que las guías *"son demasiado restrictivas para métodos de riego especializados, como el goteo localizado, que resulta en riegos casi diarios o frecuentes"*. **[V]** — Ayers & Westcot (1985/1994), FAO Irrigation and Drainage Paper 29 Rev.1, Cap. 1, "Assumptions in the Guidelines". https://www.fao.org/4/t0234e/t0234e01.htm
>
> Consecuencia operativa: en goteo, el umbral de CE de FAO se puede relajar (la alta frecuencia mantiene el bulbo húmedo y baja la succión matricial), pero el umbral de **obstrucción** —que FAO 29 no trata— se vuelve el limitante. Son dos criterios distintos sobre la misma agua.

---

## 1. EL ANÁLISIS DE AGUA VA PRIMERO

### 1.1 Qué se le pide al laboratorio

FAO 29 Rev.1, Tabla 2 ("Laboratory determinations needed to evaluate common irrigation water quality problems"), rangos normales en aguas de riego **[V]**:

| Determinación | Símbolo | Unidad | Rango normal |
|---|---|---|---|
| Bicarbonato | HCO₃⁻ | me/L | 0 – 10 |
| Cloruro | Cl⁻ | me/L | 0 – 30 |
| Boro | B | mg/L | 0 – 2 |
| Relación de adsorción de sodio | SAR | (me/L)^½ | 0 – 15 |

Conversión que usa FAO: `me/L = mg/L ÷ peso equivalente`; y `1 me/L = 1 mmol/L ajustado por la carga del ion` **[V]** (FAO 29 Cap. 1, notas de la Tabla 2).

Pesos equivalentes de uso corriente **[C]**: HCO₃⁻ 61,0 · CO₃²⁻ 30,0 · Cl⁻ 35,45 · SO₄²⁻ 48,03 · NO₃⁻ 62,0 · Ca²⁺ 20,04 · Mg²⁺ 12,15 · Na⁺ 22,99 · K⁺ 39,10 · CaCO₃ 50,04.

### 1.2 FAO 29 Tabla 1 — el marco de referencia, con sus tres columnas

Reproducida literal **[V]** (https://www.fao.org/4/t0234e/t0234e01.htm; adaptada por FAO de *University of California Committee of Consultants 1974*):

| Problema potencial | Unidad | Ninguna | Ligera a moderada | Severa |
|---|---|---|---|---|
| **Salinidad** — CEw | dS/m | < 0,7 | 0,7 – 3,0 | > 3,0 |
| (o) SDT | mg/L | < 450 | 450 – 2 000 | > 2 000 |
| **Infiltración** (evaluar CEw y SAR juntos) | | | | |
|  SAR 0 – 3 y CEw = | dS/m | > 0,7 | 0,7 – 0,2 | < 0,2 |
|  SAR 3 – 6 | dS/m | > 1,2 | 1,2 – 0,3 | < 0,3 |
|  SAR 6 – 12 | dS/m | > 1,9 | 1,9 – 0,5 | < 0,5 |
|  SAR 12 – 20 | dS/m | > 2,9 | 2,9 – 1,3 | < 1,3 |
|  SAR 20 – 40 | dS/m | > 5,0 | 5,0 – 2,9 | < 2,9 |
| **Toxicidad — Sodio**, riego superficial | SAR | < 3 | 3 – 9 | > 9 |
|  Sodio, aspersión | me/L | < 3 | > 3 | — |
| **Cloruro**, riego superficial | me/L | < 4 | 4 – 10 | > 10 |
|  Cloruro, aspersión | me/L | < 3 | > 3 | — |
| **Boro** | mg/L | < 0,7 | 0,7 – 3,0 | > 3,0 |
| **NO₃-N** | mg/L | < 5 | 5 – 30 | > 30 |
| **Bicarbonato (HCO₃)** *sólo aspersión por encima del follaje* | me/L | < 1,5 | 1,5 – 8,5 | > 8,5 |
| **pH** | — | Rango normal 6,5 – 8,4 | | |

**Método de la fila de infiltración** (nota 3 de FAO): *"A un SAR dado, la tasa de infiltración aumenta al aumentar la salinidad del agua. Evalúe el problema potencial de infiltración por el SAR modificado por la CEw. Adaptado de Rhoades 1977 y Oster & Schroer 1979."* **[V]** Es decir: **el SAR no se lee solo**. Un SAR de 8 con CEw 2,0 no restringe; el mismo SAR 8 con CEw 0,4 es severo. Un informe que reporte SAR sin CEw es inutilizable.

**Método de la fila de bicarbonato:** el corte 1,5 / 8,5 me/L es **exclusivamente para aspersión por encima del follaje** (manchas blancas de carbonato sobre hoja y fruto). **No es** el umbral de obstrucción de goteros ni el disparador de acidulación agronómica. Confundir estos dos usos es el error más común del rubro.

### 1.3 Bicarbonatos y carbonatos: qué problema causan realmente

Tres problemas distintos, con tres umbrales distintos y tres métodos distintos:

| Problema | Umbral | Método / fuente |
|---|---|---|
| Manchas foliares por aspersión | HCO₃ > 1,5 me/L (ligero), > 8,5 me/L (severo) | FAO 29 Tabla 1 **[V]** |
| **Precipitación de CaCO₃ en goteros** | HCO₃ > ~2 meq/L **y** pH > 7,5 | UC ANR, *Maintenance of Microirrigation Systems* — "Chemical precipitation" **[V]** https://ucanr.edu/site/maintenance-microirrigation-systems/chemical-precipitation |
| Alcalinización progresiva del bulbo húmedo | cualquier HCO₃ apreciable, acumulativo | UF/IFAS SL142: en arena, con agua de **2,1 me/L de bases**, el pH del suelo a 0–1 pulgada del gotero subió a **7,6 en un año**, mientras a 24–48 pulgadas seguía en 5,0 (pH nativo) **[V]** |

Ese último dato es el que justifica acidular aunque el gotero no se tape: el problema no es el emisor, es el suelo bajo el emisor.

**Alcalinidad y alcalinidad residual.** La alcalinidad total en meq/L es `HCO₃⁻(meq/L) + CO₃²⁻(meq/L)`, o equivalentemente `alcalinidad como mg/L CaCO₃ ÷ 50,04` **[C]**.

El **carbonato de sodio residual (RSC / alcalinidad residual)** mide cuánto bicarbonato queda *después* de que precipite todo el Ca y Mg disponibles:

```
RSC (meq/L) = (CO₃²⁻ + HCO₃⁻) − (Ca²⁺ + Mg²⁺)        [todo en meq/L]
```

| RSC (meq/L) | Interpretación |
|---|---|
| ≤ 1,25 | Segura |
| 1,25 – 2,5 | Marginal |
| > 2,5 | Excesiva / no apta sin corrección |

**[V]** Penn State Extension, *Irrigation Water Quality Guidelines for Turfgrass Sites* (P. Landschoot; act. 23-sep-2025), citando a Duncan, Carrow & Huck (2000), *USGA Green Section Record* sep–oct: 14–24. https://extension.psu.edu/irrigation-water-quality-guidelines-for-turfgrass-sites
*Método declarado:* umbrales de origen turf/USGA, no de cultivo extensivo. **Transferirlos a soya o caña exige verificación local.**

Un RSC positivo dice algo operativo: el agua **destruye su propio calcio** al concentrarse en el suelo, y el Na queda dominando el complejo de cambio aunque el SAR de entrada parezca aceptable.

### 1.4 EL CÁLCULO EXACTO DE ACIDULACIÓN

#### Paso 1 — Alcalinidad a neutralizar
```
Alc_total (meq/L) = HCO₃⁻(mg/L)/61,0 + CO₃²⁻(mg/L)/30,0
Ácido requerido (meq/L) = Alc_total − Alc_residual_objetivo
```

#### Paso 2 — Fijar la alcalinidad residual objetivo (NO neutralizar el 100 %)

UF/IFAS SL142 es explícito: neutralizar **80–90 %**, nunca 100 %, por tres razones textuales **[V]**:
1. No hace falta neutralizar todo: con 80–90 % neutralizado, un agua que hubiera dado problema en 6 meses tarda 5 años al mismo régimen.
2. Deja margen para el error de dosificación y la variabilidad del agua.
3. El riesgo de sobreacidificar no compensa neutralizar el último 10–20 %.

Y lo respalda con medición: sobre 7 aguas reales, con **80 % de neutralización** el pH inmediato quedó entre 4,1 y 5,2 (y a los 2 días subió a 4,1–6,1); con **100 %** el pH cayó a 3,2–3,6 y **ahí se quedó** a los dos días **[V]** (SL142, Tabla 5).

> Objetivo práctico: dejar **0,5 – 1,0 meq/L de alcalinidad residual**, y verificar con pH de campo **4,5 – 5,0 medido inmediatamente después de la inyección** (SL142, pregunta 18) **[V]**.

#### Paso 3 — Convertir meq/L a litros de ácido comercial por m³

```
eq a neutralizar por m³ = (Alc_total − Alc_res) [meq/L] × 1000 L/m³ ÷ 1000 = (Alc_total − Alc_res)  [eq/m³]

L de ácido comercial por m³ = (Alc_total − Alc_res) [eq/m³] ÷ N [eq/L]
```

donde la normalidad del ácido comercial es **[C]**:
```
N (eq/L) = 1000 × ρ(kg/L) × (%p/p ÷ 100) ÷ PM(g/mol) × n_eq
```

**Validación del método:** aplicado a H₂SO₄ 93 % (ρ 1,83; PM 98,08; n_eq 2) da `1000×1,83×0,93/98,08×2 = 34,7 N`, **idéntico** al valor publicado por UF/IFAS SL142 (34,7 N) **[V]**. Aplicado a HCl 32 % (ρ 1,16; PM 36,46; n_eq 1) da 10,2 N, **idéntico** al publicado (10,2 N) **[V]**. El método reproduce la fuente; se puede usar con confianza para ácidos que la fuente no lista.

#### Paso 4 — Ejemplo trabajado (auditable línea por línea)

Agua de pozo: HCO₃⁻ = 274 mg/L; CO₃²⁻ = 0; Ca = 3,2 meq/L; Mg = 1,1 meq/L; Na = 2,4 meq/L; CEw = 0,85 dS/m.

- Alcalinidad = 274 / 61,0 = **4,49 meq/L**
- RSC = (0 + 4,49) − (3,2 + 1,1) = **+0,19 meq/L** → *segura* según el criterio de §1.3, pero el HCO₃ ya está por encima del corte de precipitación de CaCO₃ (2 meq/L) de UC ANR.
- SAR = 2,4 / √((3,2+1,1)/2) = 2,4 / √2,15 = **1,64** → con CEw 0,85: fila "SAR 0–3 y CEw > 0,7" = **sin restricción de infiltración** (FAO 29 Tabla 1).
- Objetivo: dejar 0,8 meq/L residual → **neutralizar 3,69 meq/L = 3,69 eq/m³**.

| Ácido | Concentración comercial | N (eq/L) | L de ácido por m³ | mL/m³ | Nutriente aportado |
|---|---|---|---|---|---|
| Sulfúrico | 93 % (66° Bé) | 34,7 **[V]** | 0,106 | **106** | 59 g S/m³ **[C]** |
| Sulfúrico | 98 % | 36,8 **[C]** | 0,100 | **100** | 59 g S/m³ |
| Nítrico | 60 % (ρ 1,37) | 13,1 **[C]** | 0,283 | **283** | 51,7 g N/m³ **[C]** |
| Nítrico | 65 % (ρ 1,39) | 14,3 **[C]** | 0,258 | **258** | 51,7 g N/m³ |
| Fosfórico | 85 %, contado a **1 eq/mol** (ver aviso) | 14,6 **[C]** | 0,253 | **253** | 114 g P/m³ **[C]** |
| Fosfórico | 85 %, contado a 3 eq/mol | 44,1 **[V]** | 0,084 | **84** | 38 g P/m³ |
| Clorhídrico | 32 % (20° Bé) | 10,2 **[V]** | 0,362 | **362** | ninguno; **+131 g Cl/m³** |

> **AVISO TÉCNICO — el fosfórico no vale 3 equivalentes en esta aplicación.** UF/IFAS SL142 tabula el H₃PO₄ 85 % como 44,1 N, que corresponde a los **tres** protones. Pero las constantes de disociación del ácido fosfórico son pK₁ = 2,15, pK₂ = 7,20, pK₃ = 12,35: **al pH objetivo de 4,5–5,0 sólo el primer protón está entregado**. El segundo protón no se disocia apreciablemente hasta pH ≈ 7. Neutralizar contra bicarbonato hasta pH 5 consume, en la práctica, **~1 equivalente por mol**, no 3 — es decir, hace falta **~3 veces más fosfórico** del que sugiere el factor 6,8 de la Tabla 4 de SL142.
> Esto es **análisis propio [C]**, no una corrección publicada de esa hoja de extensión. La salvaguarda operativa es la misma que recomienda SL142: **dosificar contra el pH medido, no contra la tabla**. Y el aviso práctico real es el de la línea siguiente: aun a 1 eq/mol, el fosfórico aporta 114 g P/m³, que en 400 m³/ha son **45 kg P/ha en un solo riego** — imposible de encajar en ninguna receta.

**El corolario que decide la elección del ácido:** el anión del ácido **no desaparece**, entra en la receta.
Con 400 m³/ha de lámina (40 mm):
- Nítrico: 51,7 g N/m³ × 400 = **20,7 kg N/ha por riego** **[C]**. Si el plan de N del ciclo son 200 kg/ha y se riega 30 veces, el ácido solo ya aporta 620 kg N/ha. **Imposible.** El nítrico sólo cubre una fracción de la alcalinidad, o se usa en aguas de alcalinidad baja.
- Sulfúrico: 59 g S/m³ × 400 = **23,6 kg S/ha por riego** **[C]**. El S se tolera mucho mejor que el N o el P, y por eso el sulfúrico es el ácido por defecto en aguas alcalinas duras.

Esta restricción está explícitamente enunciada en la literatura de solución nutritiva: *"estas cantidades no deben exceder las concentraciones deseadas para la solución nutritiva. Como estas concentraciones de aniones limitan la cantidad de ácido que se puede agregar, la cantidad de HCO₃⁻ que se puede neutralizar es limitada. En consecuencia, la concentración inicial de HCO₃⁻ del agua de riego es una cuestión de calidad de primer orden."* **[V]** — Eurofins Agro / AkzoNobel / NMI / SQM / Yara (2016), *Nutrient Solutions for Greenhouse Crops*, sección "pH, CaCO₃, Hardness of water". https://cdnmedia.eurofins.com/corporate-eurofins/media/12142795/160825_manual_nutrient_solutions_digital_en.pdf

**Reacción y consecuencia física** **[V]** (misma fuente):
```
Ca²⁺ + 2 HCO₃⁻ + 2 HNO₃  →  Ca²⁺ + 2 CO₂↑ + 2 H₂O + 2 NO₃⁻
```
El CO₂ **tiene que poder escapar**. Si no, el pH no baja y fluctúa. Por eso la reacción ácido–bicarbonato debe ocurrir en **sistema abierto** (tanque de mezcla abierto), no en línea presurizada cerrada. Es un error de diseño frecuente: inyectar ácido directo en la tubería y no entender por qué el pH medido "no obedece".

### 1.5 Comparación de ácidos

| | Sulfúrico H₂SO₄ | Nítrico HNO₃ | Fosfórico H₃PO₄ | Cítrico C₆H₈O₇ | Clorhídrico HCl |
|---|---|---|---|---|---|
| Concentración comercial típica | 93–98 % | 60–65 % | 75–85 % | sólido monohidratado | 32–35 % |
| **Normalidad útil** (eq/L) | 34,7 (93 %) **[V]** / 36,8 (98 %) **[C]** | 13,1 (60 %) / 14,3 (65 %) **[C]** | **14,6** al pH objetivo **[C]** (44,1 si se cuentan 3 H⁺ **[V]**) | ~9–10 eq/kg al pH objetivo **[C]**, ver nota | 10,2 (32 %) **[V]** |
| **mL (o g) por m³ para neutralizar 1 meq/L** | 28,8 mL **[C]** | 76,6 mL (60 %) **[C]** | 68,5 mL **[C]** | ~105 g **[C]** | 98,0 mL **[C]** |
| **Nutriente por meq neutralizado** | 16,03 mg S/L **[C]** | 14,01 mg N/L **[C]** | 30,97 mg P/L **[C]** (= 70,9 mg P₂O₅/L) | ninguno | ninguno |
| Anión indeseable | — | NO₃⁻ (lixiviable, cuenta en el plan de N) | H₂PO₄⁻ (satura la receta) | **carbono orgánico → alimenta biopelícula** | **Cl⁻: 35,45 mg/L por meq** |
| **Costo relativo por meq neutralizado** | **1,0 ×** (referencia) | [NV] | **3,2 ×** | [NV] | **2,2 ×** (a granel) / 6,8 × (bidón) |
| Riesgo de manejo | El peor: reacción exotérmica violenta con agua, quemadura profunda, ataca acero al carbono, hormigón y aluminio | Oxidante fuerte + humos nitrosos (NO₂, rojizos, edema pulmonar diferido); incompatible con orgánicos | El más benigno de los tres minerales; corrosivo moderado | El más seguro para el operario; **el peor para la biopelícula** | Humos de HCl; **produce gas cloro si toca hipoclorito** |
| Uso preferente | Agua muy alcalina y dura; cuando el S es útil o neutro | Alcalinidad baja–media donde el N cabe en la receta | Sólo para la fracción de alcalinidad que quepa como P de la receta; o como preventivo contra precipitados | Limpiezas puntuales de emisores en pequeña escala; agricultura orgánica certificada | Cuando el Cl no es limitante (nunca en cultivos sensibles al Cl) |

**Base de la comparación de costo** **[V]**: UF/IFAS SL142, Tabla 3, "costo aproximado de tratar 1000 galones de agua conteniendo 4 me base/L": sulfúrico 93 % en tambor **US$ 0,13**; clorhídrico 20° Bé a granel **US$ 0,29** y en bidón **US$ 0,88**; fosfórico 85 % **US$ 0,42**; ácido de batería (1,265 sp.gr.) **US$ 1,04**.
> **Método y caducidad del dato:** son precios de Florida de la edición original de la hoja (años 1990), presentados por la propia fuente como *ilustrativos*. **Los valores absolutos no se usan.** Lo que sí transfiere razonablemente es el **orden**: sulfúrico a granel ≪ clorhídrico a granel < fosfórico ≪ presentaciones minoristas. Nítrico y cítrico **no figuran** en esa tabla → **[NV]** en costo.

**Nota sobre el ácido cítrico** **[C]**: monohidratado, PM 210,14 g/mol, tres grupos carboxilo con pK₁ 3,13 · pK₂ 4,76 · pK₃ 6,40. Al pH objetivo de 4,5–5,0 entrega aproximadamente **2 de los 3 protones**, es decir ~2 eq/mol → ~9,5 eq/kg. Neutraliza, pero: (a) hace falta **~105 g por m³ y por meq/L** a neutralizar — en el ejemplo del §1.4 (3,69 eq/m³ ÷ 9,5 eq/kg) son **388 g/m³ de cítrico sólido** contra **106 mL de sulfúrico**; (b) es **sustrato de carbono biodisponible**: bajar el pH con cítrico y después pelear la biopelícula con cloro es trabajar contra uno mismo. Uso justificado en limpieza puntual, no en acidulación continua de un sistema comercial.

**Incompatibilidad que mata gente:** *"No mezcle cloro y ácidos, porque eso puede causar la formación de gas cloro, altamente tóxico. Use tanques de almacenamiento y puertos de inyección distintos para el ácido y para el cloro."* **[V]** UC ANR, *Chlorination for biological clogging problems*. Virginia Cooperative Extension agrega la distancia: los puntos de inyección de ácido y de cloro deben estar **separados 2 a 3 pies (0,6–0,9 m)** **[V]** (Shortridge & Benham 2023, VCE 442-757 / BSE-222P).

### 1.6 Dureza, Na, Cl, B, SAR y SAR ajustado

**SAR** (FAO 29, Fig. 1) **[V]**:
```
SAR = Na / √( (Ca + Mg) / 2 )        [todos en me/L]
```

**SAR ajustado — adj R_Na** (FAO 29 Rev.1, ec. 14, adaptado de Suarez 1981) **[V]**:
```
adj R_Na = Na / √( (Ca_x + Mg) / 2 )
```
donde **Ca_x** es un valor de calcio modificado, leído de la Tabla 11 de FAO 29 en función de:
- la relación **HCO₃/Ca** del agua (ambos en me/L),
- la **CEw** (dS/m),
- y una presión parcial de CO₂ en los primeros milímetros de suelo de **P_CO₂ = 0,0007 atm** (supuesto del procedimiento).

*Método declarado por FAO:* el procedimiento asume una **fuente de calcio del suelo** (caliza CaCO₃ u otros minerales silicatados) y **ninguna precipitación de magnesio**. FAO advierte además que, para la mayoría de las aguas, el SAR simple queda **dentro de ±10 % del adj R_Na** **[V]**. Es decir: **el adj R_Na sólo cambia la decisión en aguas bicarbonatadas extremas.** Calcularlo de rutina es teatro; calcularlo cuando HCO₃/Ca es alto es criterio.

FAO 29 Rev.1 abandonó el "adj SAR" de la edición 1976 (Bower/Rhoades) y adoptó el de Suarez 1981, declarando que **ambos son aceptables** pero prefiriendo el nuevo **[V]**.

**Dureza.** No es un parámetro de FAO 29. Se usa en la práctica de riego localizado como proxy del riesgo de incrustación:

| Dureza (mg/L CaCO₃) | Riesgo de obstrucción |
|---|---|
| < 150 | Ligero |
| 150 – 300 | Moderado |
| > 300 | Severo |

**[V]** Shortridge & Benham (2023), Virginia Cooperative Extension **442-757 (BSE-222P)**, Tabla 1b. https://www.pubs.ext.vt.edu/content/pubs_ext_vt_edu/en/442/442-757/442-757.html
*Método:* clasificación de riesgo de obstrucción de emisores, **no** de aptitud agronómica. Un agua dura puede ser excelente para la planta y letal para el gotero.

**Boro — toxicidad por cultivo.** FAO 29 Rev.1, Tabla 16, tomada de Maas (1984) **[V]**:

| Clase | Rango (mg/L) | Cultivos representativos |
|---|---|---|
| Muy sensible | < 0,5 | limón, zarzamora |
| Sensible | 0,5 – 0,75 | palta, pomelo, naranjo, damasco, durazno, cerezo, ciruelo, caqui, higuera, **vid**, nogal, pecán, caupí, cebolla |
| Sensible | 0,75 – 1,0 | ajo, batata, **trigo**, **cebada**, **girasol**, poroto mungo, sésamo, frutilla, poroto, maní |
| Moderadamente sensible | 1,0 – 2,0 | pimiento, arveja, zanahoria, rabanito, **papa**, pepino |
| Moderadamente tolerante | 2,0 – 4,0 | lechuga, repollo, apio, nabo, avena, **maíz**, alcaucil, tabaco, mostaza, zapallo, melón |
| Tolerante | 4,0 – 6,0 | **sorgo**, **tomate**, **alfalfa**, perejil, remolacha, remolacha azucarera |
| Muy tolerante | 6,0 – 15,0 | **algodón**, espárrago |

> **Método declarado, y es crítico:** *"Concentraciones máximas toleradas en el agua del suelo o en el extracto de saturación sin reducción de rendimiento o de crecimiento vegetativo. Las tolerancias al boro varían según clima, condiciones de suelo y variedades. Las concentraciones máximas en el agua de riego son aproximadamente iguales a estos valores o algo menores."* **[V]** (FAO 29 Rev.1, notas de la Tabla 16).
> Traducción: **estos números son del agua del suelo, no del agua de riego**, y sólo se igualan "aproximadamente". Cualquier tabla comercial que los presente como límites del análisis de agua está sobre-simplificando la fuente. La **soya no figura** en la tabla de Maas.

**Sodio y cloruro — el matiz que FAO 29 declara y casi nadie lee** **[V]** (nota 4 de la Tabla 1): los cortes de Na (SAR < 3 / 3–9 / > 9) y Cl (< 4 / 4–10 / > 10 me/L) para riego superficial aplican a **frutales y leñosas**, que son sensibles. *"La mayoría de los cultivos anuales no son sensibles; use las tablas de tolerancia a la salinidad (Tablas 4 y 5)."* Aplicar el corte de Cl de 4 me/L a un maíz o a una soya es importar un umbral de un método que no corresponde.

Con **aspersión sobre el follaje y humedad relativa < 30 %**, Na y Cl se absorben **por la hoja** y los umbrales bajan a 3 me/L para ambos **[V]**.

**Límites de Na para sistemas cerrados / hidroponía** (marco distinto, declarado) **[V]** — Eurofins Agro et al. (2016), Tablas 1 y 2:

| Nivel de calidad | CE (mS/cm) | Na o Cl (mmol/L) | Aptitud |
|---|---|---|---|
| 1 | < 0,5 | < 1,5 | Apta para todos los cultivos |
| 2 | 0,5 – 1,0 | 1,5 – 2,5 | No apta si se requiere recirculación |
| 3 | 1,0 – 1,5 | 2,5 – 4,0 | No usar en cultivos sensibles a sales |

Na máximo aceptable **en zona radicular**: tomate 8 mmol/L (184 ppm) · pimiento, berenjena, pepino 6 (138) · melón 4 (92) · **rosa 1 mmol/L (23 ppm)** · gerbera 4 · orquídeas 4. El Cl máximo aceptable en zona radicular es **0,2–0,5 mmol/L por encima** del máximo de Na. **[V]**

### 1.7 Hierro, manganeso y bacterias del hierro

**Mecanismo** **[V]** (Eurofins Agro et al. 2016): el hierro de un pozo anaeróbico viene como **Fe²⁺ disuelto e invisible**. En cuanto toca oxígeno se oxida a **Fe³⁺** y precipita rápido como hidróxidos/óxidos insolubles. *"Esto siempre va a ocurrir en el momento en que el agua pasa por una boquilla de aspersión o un gotero, porque ahí el agua entra en contacto súbito con el aire."* Consecuencia doble: (a) el gotero se tapa, (b) **ese hierro nunca queda disponible para la planta** — no cuenta como fertilización.

**Umbrales de riesgo de obstrucción** **[V]** (Shortridge & Benham 2023, VCE 442-757, Tablas 1a–1c; criterios derivados del sistema de clasificación de Bucks, Nakayama & Gilbert 1979):

| Parámetro | Ligero | Moderado | Severo |
|---|---|---|---|
| Sólidos suspendidos (ppm) | < 50 | 50 – 100 | > 100 |
| pH | < 7,0 | 7,0 – 7,5 | > 7,5 |
| Sólidos disueltos (ppm) | < 500 | 500 – 2 000 | > 2 000 |
| **Manganeso (ppm)** | < 0,1 | 0,1 – 1,5 | > 1,5 |
| **Hierro (ppm)** | < 0,1 | 0,1 – 1,5 | > 1,5 |
| **Sulfuro de hidrógeno (ppm)** | < 0,2 | 0,2 – 2,0 | > 2,0 |
| Dureza (ppm CaCO₃) | < 150 | 150 – 300 | > 300 |
| **Bacterias (UFC/100 mL)** | < 10 000 | 10 000 – 50 000 | > 50 000 |

Fuente primaria del sistema de clasificación, con DOI verificado en Crossref:
- **Bucks, D.A., Nakayama, F.S. & Gilbert, R.G. (1979).** *Trickle irrigation water quality and preventive maintenance.* **Agricultural Water Management 2(2): 149–162.** **DOI: 10.1016/0378-3774(79)90028-3** ✔ verificado
- **Nakayama, F.S. & Bucks, D.A. (1991).** *Water quality in drip/trickle irrigation: A review.* **Irrigation Science 12(4).** **DOI: 10.1007/BF00190522** ✔ verificado

> **Advertencia de trazabilidad:** los cortes numéricos de la tabla de arriba se leyeron en la publicación de extensión de Virginia Tech (2023), que es la fuente que se pudo abrir y verificar. La tabla original de Bucks et al. 1979 **no se leyó en el original** (paywall Elsevier). Las versiones que circulan difieren en detalles — por ejemplo, el corte de pH aparece a veces como 7,0–8,0 en lugar de 7,0–7,5, y el H₂S como 0,5–2,0 en lugar de 0,2–2,0. **Si el número va a decidir una inversión en filtración, hay que abrir el original.**

**Dosis de cloro para oxidar Fe y Mn** **[V]** — Jatana & Sanders (2024), Clemson Land-Grant Press **LGP 1190**:
- Hierro: inyectar cloro a **0,64 × la concentración de hierro ferroso**, manteniendo 1 ppm de cloro libre residual al final de la línea.
- Manganeso: inyectar cloro a **1,3 × la concentración de manganeso soluble**.
- Rango de pH óptimo para la oxidación: **6,5 – 7,5**.

> **La trampa del hierro:** clorar **aguas arriba del filtro** convierte el Fe²⁺ disuelto en un precipitado que el filtro retiene. Clorar **aguas abajo** del filtro con hierro presente fabrica el precipitado dentro de la lateral. Regla: con Fe o Mn, el oxidante va **antes** del filtro, y el filtro tiene que ser de medios (arena), no de malla.

**Bacterias del hierro y del azufre.** Géneros que oxidan Fe²⁺ y depositan ocre (*Gallionella*, *Leptothrix*, *Crenothrix*) y que oxidan sulfuro (*Thiothrix*, *Beggiatoa*, *Thiobacillus*) forman limos filamentosos que taponan emisores. Los mecanismos y géneros están descritos en la literatura de riego localizado, pero **no se pudo abrir una fuente institucional con umbrales cuantitativos por género** → los géneros van como referencia cualitativa; el criterio operativo cuantitativo es la fila de "bacterias (UFC/100 mL)" y la de H₂S de la tabla de arriba. Ver §9.

### 1.8 CE del agua base y cuánto margen deja

La relación operativa que cierra el §1 con el §2 **[V]** (Eurofins Agro et al. 2016, Fórmula 4):

```
CE (mS/cm) ≈ ( Σ eq_cationes + Σ eq_aniones ) / 20        [mmol/L × carga]
```

De ahí, la regla de bolsillo **[C]**: **1 mS/cm ≈ 10 meq/L de cationes (y 10 meq/L de aniones)**.

Y la corrección por sodio, para saber cuánta CE es *nutriente* y cuánta es *lastre* **[V]**:
```
CE_nutrientes = CE_medida − 0,1 × Na (mmol/L)
```

**Cómo se lee el margen.** Si el cultivo admite una CE de solución en zona radicular de 2,5 mS/cm y el agua base trae 0,85 mS/cm (de los cuales 0,1 × 2,4 mmol Na = 0,24 son sodio inútil), quedan **1,65 mS/cm de margen ≈ 16,5 meq/L de cationes** para la receta. Eso es aproximadamente 8 mmol/L de NO₃ + 5 de K + 3 de Ca + 1 de Mg — una receta completa, ajustada. Con un agua de 1,8 mS/cm el margen es de 0,7 mS/cm ≈ 7 meq/L: **no entra una receta completa**, y hay que decidir qué nutriente sale del agua y qué nutriente se aplica al suelo por fuera del riego.

**Este es el cálculo que define si un servicio de fertirriego es vendible en un campo dado, y se hace antes de cotizar.**

**Conversión CE → SDT** (declarar siempre el factor): FAO 29 Tabla 1 implica **SDT (mg/L) ≈ CE (dS/m) × 640** (0,7 dS/m ↔ 450 mg/L) **[V]**; Penn State usa el mismo factor 640 explícitamente **[V]**. El factor real varía entre 550 y 800 según la composición iónica: **un SDT calculado no reemplaza un SDT medido.**

---

## 2. DISEÑO DE LA SOLUCIÓN NUTRITIVA

### 2.1 Balance en meq/L: cationes = aniones

Una solución nutritiva **no tiene carga eléctrica neta**. Por lo tanto la suma de equivalentes positivos debe igualar la de negativos. Método **[V]** (Eurofins Agro / AkzoNobel / Geerten van der Lugt / NMI / SQM / Yara, 2016, *Nutrient Solutions for Greenhouse Crops*, Fórmulas 1–4; base metodológica: *Bemestingsadviesbasis Substraten*, Proefstation Naaldwijk, 1999):

**Paso 1 — Equivalentes de cationes** (concentraciones en mmol/L):
```
Eq_cationes = NH₄⁺ + K⁺ + Na⁺ + 2·Ca²⁺ + 2·Mg²⁺
```

**Paso 2 — Equivalentes de aniones**:
```
Eq_aniones = NO₃⁻ + Cl⁻ + 2·SO₄²⁻ + HCO₃⁻ + H₂PO₄⁻
```

**Paso 3 — Verificar el balance**:
```
Eq_cationes ≟ Eq_aniones
```
*"En la práctica una diferencia pequeña (menor al 10 %) es aceptable, porque puede resultar de la variación analítica."* **[V]**

**Paso 4 — Derivar la CE**:
```
CE (mS/cm) = ( Eq_cationes + Eq_aniones ) / 20
```
La propia fuente aclara el alcance del método: *"Las Fórmulas 1 a 4 son sólo para uso práctico… En la realidad la conductividad eléctrica es más compleja. Los laboratorios usan fórmulas químicas más complejas."* **[V]** — o sea: sirve para **verificar** una receta, no para certificar un valor de CE. La CE se mide.

**Paso 5 — CE de referencia, para poder comparar** **[V]**: para contrastar un análisis contra los valores objetivo hay que llevarlos a la misma CE.
```
CE_nutrientes = CE_analizada − 0,1 × Na (mmol/L)
Nutriente_referencia (mmol/L) = Nutriente_analizado (mmol/L) × ( CE_referencia / CE_nutrientes )
```
La CE de referencia se toma **0,3 mS/cm por debajo** de la CE de los valores objetivo (esos 0,3 representan el Na promedio de las soluciones). Na y HCO₃ **no se convierten** porque nunca están en los valores objetivo; el Cl se convierte sólo si figura (p. ej. en tomate). **[V]**

**Paso 6 — Umbrales de corrección** **[V]**: se corrige cuando el análisis (ya llevado a CE de referencia) se desvía **25 %** del objetivo (corrección de primer nivel: ±10–15 % de nutrientes) y **50 %** (segundo nivel: ±15–25 %).

**Paso 7 — Ajuste por etapa** **[V]**: *"Temprano en la temporada los cultivos consumen relativamente más Ca que K. Al comienzo de floración y desarrollo de fruto consumen relativamente más K que Ca."*

> **Dónde entra el agua base.** El balance se hace sobre la **solución final en el gotero**, no sobre los fertilizantes. El Ca, Mg, SO₄, Na, Cl y HCO₃ que ya trae el agua **se descuentan** de la receta. Este es el error de cálculo más frecuente: sumar la receta de catálogo sobre un agua que ya trae 3,2 meq/L de Ca, y terminar con Ca en exceso, K bloqueado y un balance de cargas que sólo cierra porque sobran aniones de cloruro.

### 2.2 CE objetivo por cultivo y etapa — con dos recetas completas y su verificación

Todos los valores de este apartado son **[V]** de Eurofins Agro et al. (2016), Sección B, "Nutrient Solutions", sustrato inerte. Dos columnas distintas y no intercambiables: **"valores objetivo"** = lo que se busca **en la zona radicular** (drenaje); **"solución nutritiva"** = lo que se prepara **en el gotero**.

#### TOMATE (*Solanum lycopersicum*) — sustrato inerte

| Parámetro | Objetivo en zona radicular | Solución nutritiva (gotero) | Objetivo (ppm) | Solución (ppm) |
|---|---|---|---|---|
| pH | 5,5 – 6,0 | **5,3** | | |
| **CE (mS/cm)** | **4,0** | **2,6** | | |
| Na (mmol/L) | < 8 | — | < 184 | — |
| Cl | < 8 | 1 | < 284 | 35 |
| HCO₃ | < 0,05 | — | < 6 | — |
| **N-NH₄** | < 0,05 | **1,2** | < 2 | **17** |
| **K** | 8 | **9,5** | 313 | 371 |
| **Ca** | 10 | **5,4** | 400 | 216 |
| **Mg** | 4,5 | **2,4** | 109 | 58 |
| **N-NO₃** | 22 | **15** | 308 | 210 |
| **S** | 6,8 | **4,4** | 218 | 141 |
| **P** | 1,0 | **1,5** | 31 | 47 |
| Fe (µmol/L) | 35 | 15 | 1960 ppb | 840 ppb |
| Mn | 5 | 10 | 275 | 550 |
| Zn | 7 | 5 | 458 | 327 |
| B | 50 | 30 | 540 | 324 |
| Cu | 0,7 | 0,75 | 44 | 48 |
| Mo | 0,5 | 0,5 | 48 | 48 |

**Ajustes por etapa** (sobre la solución, mmol/L) **[V]**:

| Etapa | K | Ca | Mg | N-NH₄ | Notas de la fuente |
|---|---|---|---|---|---|
| Inicio (*Start*) | −1,0 (−39 ppm) | +0,5 (+20) | +0,5 (+12) | — | Más Ca relativo |
| Cuajado (*Fruit set*) | **+1,5 (+59)** | **−0,5 (−20)** | −0,25 (−6) | — | *"puede variar de 0,25 a 2 mmol/L para K y de 0,2 a 0,75 mmol/L para Ca"* |
| Alta demanda hídrica | −1,0 (−39) | +0,5 (+20) | — | — | *"recomendado cuando el aporte de agua supera 5 L/m²/día"* |
| Fin de temporada | −1,0 (−14 y −31 según ion) | | | −1 (−14) | |

> **Aquí está toda la respuesta a "relación K:Ca:Mg por etapa", y es una inversión, no un ajuste fino:** de inicio a cuajado el K sube 2,5 mmol/L y el Ca baja 1,0. En equivalentes, la relación K:Ca:Mg pasa de **8,5 : 11,8 : 5,8 meq/L** (inicio) a **11,0 : 9,8 : 4,3 meq/L** (cuajado). El orden de dominancia entre K y Ca **se da vuelta**.

#### PEPINO (*Cucumis sativus*) — sustrato inerte **[V]**

| Parámetro | Objetivo zona radicular | Solución nutritiva |
|---|---|---|
| pH | 5,2 – 6,0 | 5,3 |
| **CE (mS/cm)** | **3,0** | **2,2** |
| Na (mmol/L) | < 6 | — |
| HCO₃ | < 0,5 | — |
| N-NH₄ | < 0,5 | 1,25 |
| K | 8 | 8 |
| Ca | 6,5 | 4 |
| Mg | 3 | 1,375 |
| N-NO₃ | 18 | 16 |
| S | 3,5 | 1,375 |
| P | 0,9 | 1,25 |

Ajustes: inicio K −1 / Ca +0,5 / Mg +0,25 / NH₄ −0,5; cuajado K +1 / NO₃ +1; alta demanda hídrica K −1 / Ca +0,5; fin de temporada NH₄ −1, P −1. **[V]**

#### Verificación del método del §2.1 contra estas recetas — **la auditoría cierra al decimal**

Aplicando las Fórmulas 1, 2 y 4 a la solución de **tomate** **[C]**:

```
Eq_cationes = NH₄ 1,2 + K 9,5 + Ca 5,4×2 + Mg 2,4×2
            = 1,2 + 9,5 + 10,8 + 4,8                    = 26,3 meq/L

Eq_aniones  = NO₃ 15 + Cl 1 + SO₄ 4,4×2 + H₂PO₄ 1,5 + HCO₃ ~0
            = 15 + 1 + 8,8 + 1,5                        = 26,3 meq/L   ← BALANCE EXACTO

CE          = (26,3 + 26,3) / 20 = 2,63 mS/cm     vs.  2,6 publicado    ← COINCIDE
```

Y para **pepino** **[C]**: cationes = 1,25 + 8 + 8 + 2,75 = **20,0**; aniones = 16 + 2,75 + 1,25 = **20,0**; CE = 40/20 = **2,0** frente a **2,2** publicado — diferencia del 9 %, dentro del margen del 10 % que la propia fuente declara aceptable (el Cl no está tabulado en la solución de pepino y explicaría la diferencia).

> **Esto es lo que hace utilizable el método:** una receta publicada que no cierre el balance de cargas, o cuya CE calculada se aparte más del 10 % de la declarada, **está mal transcrita o le falta un ion**. Es una prueba de 30 segundos que descarta la mitad de las "recetas" que circulan.

**% de N amoniacal en estas recetas** **[C]**: tomate 1,2 / (1,2 + 15) = **7,4 %**; pepino 1,25 / (1,25 + 16) = **7,2 %**. Ambas dentro del 5–15 % del §2.3.

**Lo que estas tablas NO son:** son de **cultivo en sustrato inerte bajo invernadero, en Países Bajos**. No son recetas para fertirriego de campo abierto en suelo, ni para clima tropical. Lo que **sí** transfiere es la **metodología** (balance de cargas, CE de referencia, dirección del ajuste K↔Ca por etapa, % de NH₄). Los valores absolutos, no.

Lo que además puede afirmarse con fuente:

- **La CE es el agregado, no el diagnóstico.** *"La salinidad (Na, Cl + todos los nutrientes) causa pérdida de potencial productivo"* **[V]** (Eurofins 2016, Fig. 1, según Sonneveld & Voogt 2009, *Plant Nutrition of Greenhouse Crops*, cap. "Nutrient management in substrate systems", pp. 277–312). Dos aguas de CE 2,0 pueden estar una llena de nutrientes y la otra llena de NaCl: **la misma CE, resultados opuestos.** Por eso existe la corrección `CE_nutrientes = CE − 0,1·Na`.
- **El techo lo pone la tolerancia del cultivo a la salinidad del extracto de saturación (CEe), no la CE del gotero.** FAO 29 Rev.1 Tablas 4 y 5 (Maas & Hoffman) dan CEe por cultivo y por porcentaje de rendimiento; la traducción de CEe a CE del agua depende de la **fracción de lavado** (§6.2), no es una constante.
- Referencia de libro para receta y fisiología: **Sonneveld, C. & Voogt, W. (2009).** *Plant Nutrition of Greenhouse Crops.* Springer, Dordrecht. ISBN 978-90-481-2531-9. (DOI del libro no verificado en esta sesión → §9.)

### 2.3 Relaciones K : Ca : Mg y % máximo de N amoniacal

**% de N amoniacal — el número y el mecanismo.**

Límite operativo en sistemas hidropónicos **[V]** (Eurofins Agro et al. 2016):
- **NH₄⁺ = 5–15 % del N total** de la solución.
- Máximo **1,0–1,5 mmol/L de NH₄⁺** (= **14–21 ppm de N**) en la solución nutritiva.
- Si el pH de la zona radicular está **bajo**: reducir NH₄ a **0–0,5 mmol/L (0–7 ppm N)**.
- Si el pH está **alto**: subir NH₄ hasta el máximo de **1,5 mmol/L (21 ppm N)**.
- **Verificar el pH a diario.**

Mecanismo del uso del amonio como regulador de pH **[V]** (misma fuente): la raíz que absorbe NH₄⁺ libera H⁺ al medio → acidifica la rizosfera. Es la segunda vía de control de pH, alternativa a inyectar ácido.

**Por qué el límite depende de la temperatura de raíz — evidencia experimental** **[V]**:
Ganmore-Neumann & Kafkafi (1983, 1985), citados en Kafkafi & Tarchitzky (2011/2012): frutilla en solución nutritiva con distintas relaciones NH₄:NO₃ pero **igual N total**. Las plantas crecieron **muy bien con fuente amoniacal mientras la raíz se mantuvo por debajo de 17 °C**, y **murieron a las cuatro semanas cuando la temperatura de raíz subió a 32 °C**.
Mecanismo medido: al subir la temperatura de raíz cae el contenido de azúcares de la raíz (más respiración); el metabolismo del NH₄⁺ en la raíz **consume azúcar**; cuando el azúcar ya no alcanza, **se acumula amoníaco libre**, que es tóxico para la respiración celular, y la raíz muere.
Consecuencia por grupo botánico **[V]** (Moritsugu et al. 1983, misma cita): las **monocotiledóneas son menos sensibles** a la concentración de N amoniacal que las **dicotiledóneas de hoja ancha, que son muy sensibles**.

> **Regla derivada, y es una regla de campo, no de catálogo:** el % de N amoniacal admisible **baja cuando sube la temperatura del suelo/sustrato y cuando el volumen radicular está restringido** (macetas, contenedores, sustratos poco profundos). En verano cálido, con raíz confinada, **nitrato**. En campo abierto el riesgo es menor porque no todo el volumen radicular está a la misma temperatura ni a la misma concentración de amonio **[V]**.

Fuente: **Kafkafi, U. & Tarchitzky, J. (2011).** *Fertigation: A Tool for Efficient Fertilizer and Water Management.* IFA / IPI, París. Edición en español: *Fertirrigación. Una herramienta para una eficiente fertilización y manejo del agua* (2012). https://www.fertilizer.org/wp-content/uploads/2023/01/2012_ifa_fertigation_spanish.pdf

**Un efecto colateral del amonio que se puede aprovechar** **[V]** (misma fuente, §5.3): colocar el fertilizante fosfatado **en banda junto con sulfato de amonio** resultó en **más de cinco veces** más P absorbido por maíz que colocarlo con una fuente nítrica (Black 1968; Duncan & Ohlrogge 1957; confirmado por Imas et al. 1997a,b). El mecanismo es la acidificación de la rizosfera por absorción de NH₄⁺, que aumenta la disponibilidad del P. **Esto es un argumento a favor de la banda arrancadora amoniacal + P, no a favor del fertirriego.**

**Relaciones K : Ca : Mg — valores verificados, en equivalentes** **[C, sobre datos [V] de Eurofins Agro et al. 2016, §2.2]**:

| Cultivo / etapa | K (meq/L) | Ca (meq/L) | Mg (meq/L) | K : Ca : Mg (normalizado a K=1) | % de la carga catiónica (sin NH₄) |
|---|---|---|---|---|---|
| Tomate, solución base | 9,5 | 10,8 | 4,8 | 1 : 1,14 : 0,51 | K 38 % · Ca 43 % · Mg 19 % |
| Tomate, inicio | 8,5 | 11,8 | 5,8 | 1 : 1,39 : 0,68 | K 33 % · Ca 45 % · Mg 22 % |
| **Tomate, cuajado** | **11,0** | **9,8** | **4,3** | **1 : 0,89 : 0,39** | **K 44 % · Ca 39 % · Mg 17 %** |
| Pepino, solución base | 8,0 | 8,0 | 2,75 | 1 : 1,00 : 0,34 | K 43 % · Ca 43 % · Mg 15 % |

*(Advertencia de dominio: sustrato inerte, invernadero, Países Bajos. Ver el cierre del §2.2.)*

Y el resto de lo verificado:
- El **antagonismo K–Mg** en solución: exceso de K²⁺ compite con la absorción de Mg²⁺ y puede inducir deficiencia de Mg **[V]** (Kafkafi et al. 1971, citado en Kafkafi & Tarchitzky 2011, §6).
- La **deficiencia de Ca inducida** durante el desarrollo del fruto: el Ca se mueve por xilema (flujo transpiratorio) y los frutos transpiran poco; por eso el suministro de Ca a fruto es crítico y no se resuelve subiendo la dosis **[V]** (misma fuente, §7).
- El **cambio de relación por etapa**: más Ca relativo en fase vegetativa, más K relativo desde floración/fructificación **[V]** (Eurofins 2016).

---

## 3. TANQUES CONCENTRADOS A / B / C

### 3.1 Qué va en cada uno y por qué

| Tanque | Contenido | Razón química |
|---|---|---|
| **A** | Todas las fuentes de **calcio** (nitrato de calcio, nitrato de calcio amoniacal) + **quelato de hierro** + nitrato de potasio/amonio si hace falta | El Ca²⁺ debe estar aislado de todo lo que precipite con él |
| **B** | **Sulfatos** (sulfato de potasio, de magnesio, de amonio) + **fosfatos** (MAP, MKP, fosfato de urea) + micronutrientes (excepto Fe si el pH lo requiere) | SO₄²⁻ y H₂PO₄⁻/HPO₄²⁻ juntos no reaccionan entre sí |
| **C** | **Ácido** (sulfúrico / nítrico / fosfórico) — **solo** | Un ácido concentrado sobre un nitrato de calcio o sobre un hipoclorito produce reacciones violentas y/o gases tóxicos |

Las tres reacciones que fundan la regla:

1. **Ca²⁺ + fosfato → fosfato de calcio.** *"La mezcla entre el nitrato de calcio con fosfatos provoca la formación de precipitados de fosfato de calcio."* En solución concentrada, el Ca³(PO₄)₂ / CaHPO₄ es insoluble y precipita como un lodo blanco que pasa el filtro como partícula fina y sella el laberinto del gotero.
2. **Ca²⁺ + sulfato → yeso (CaSO₄·2H₂O).** *"Estas se combinan formando precipitados de sulfato de calcio, conocido comúnmente como yeso; un compuesto de muy baja solubilidad."* El yeso tiene una solubilidad de ~2,4 g/L: en un tanque madre concentrado 100 veces, cualquier combinación Ca + SO₄ la supera de sobra.
3. **Ácido concentrado + nitrato de calcio / hipoclorito.** Exotérmica y, con hipoclorito, liberación de **gas cloro**.

**[V]** Intagri, *La Compatibilidad de los Fertilizantes en Fertirrigación*. https://www.intagri.com/articulos/nutricion-vegetal/la-compatibilidad-de-los-fertilizantes-en-fertirrigacion
*(Fuente técnica divulgativa, no revisada por pares. La química subyacente —producto de solubilidad del CaSO₄ y del Ca₃(PO₄)₂— es de manual y no está en discusión.)*

### 3.2 Ejemplo verificado de carga A/B — y el factor de concentración real

Receta de tanques para la solución de tomate del §2.2, **[V]** literal de Eurofins Agro et al. (2016):

> *"Las cantidades de fertilizante están calculadas para un volumen de 1000 L, y darán una **solución nutritiva concentrada 100×**."*

| **TANQUE A** (1000 L) | Cantidad | **TANQUE B** (1000 L) | Cantidad |
|---|---|---|---|
| Nitrato de calcio sólido | **106 kg** | Nitrato de potasio | **20 kg** |
| Nitrato de potasio | **23 kg** | Sulfato de potasio | **35 kg** |
| Cloruro de calcio anhidro | **6 kg** | Fosfato monopotásico (MKP) | **17 kg** |
| Fe-DTPA 6 % (o EDDHA 6 % o HBED 6 %) | **1 396 g** | Sulfato de magnesio 16 % MgO | **59 kg** |
| Mn-EDTA 12,8 % | **429 g** | Fosfato monoamónico (MAP) | **3 kg** |
| Zn-EDTA 14,8 % | **221 g** | Bórax 11,3 % B | **287 g** |
| Cu-EDTA 14,8 % | **32 g** | Molibdato de sodio 39,6 % | **12 g** |

**La receta se puede auditar, y cierra** **[C]** (dilución 100× ⇒ 1000 L de concentrado → 100 000 L de solución final):

| Ion | Aporte de los tanques | Calculado (mmol/L) | Publicado (mmol/L) |
|---|---|---|---|
| **K** | KNO₃ 43 kg (A+B) = 425 mol → 4,25 · K₂SO₄ 35 kg = 201 mol ×2 = 402 mol → 4,02 · MKP 17 kg = 125 mol → 1,25 | **9,52** | **9,5** ✔ |
| **P** | MKP 125 mol + MAP 26 mol | **1,51** | **1,5** ✔ |
| **S** | K₂SO₄ 201 mol + MgSO₄ 234 mol | **4,35** | **4,4** ✔ |
| **Mg** | MgSO₄ 59 kg × 16 % MgO ÷ 40,3 = 234 mol | **2,34** | **2,4** ✔ |
| **Cl** | CaCl₂ 6 kg = 54 mol × 2 | **1,08** | **1** ✔ |
| **NH₄** | Nitrato de calcio cálcico [5Ca(NO₃)₂·NH₄NO₃·10H₂O] 106 kg ≈ 98 mol → 0,98 + MAP 0,26 | **1,24** | **1,2** ✔ |
| **Ca** | Nitrato de calcio ≈ 19 % Ca → 5,03 + CaCl₂ 0,54 | **5,57** | **5,4** ✔ |

Los siete iones reproducen la receta publicada. **Este es el estándar de verificación que debería exigirse a cualquier plan de fertirriego antes de mandar el camión de fertilizante.**

**Y se ve la regla A/B funcionando:**
- Tanque A: **todo el calcio** (nitrato de calcio + cloruro de calcio) y **todo el hierro quelatado**. Ningún sulfato, ningún fosfato.
- Tanque B: **todos los sulfatos** (K₂SO₄, MgSO₄) y **todos los fosfatos** (MKP, MAP). Ningún calcio.
- El **nitrato de potasio aparece en los dos tanques** (23 kg en A, 20 kg en B): es compatible con ambos y se usa para equilibrar volúmenes y masas entre tanques.
- El **Fe va en A** porque, en las condiciones de este concentrado, es el fosfato del tanque B el que lo precipitaría.

**Factor de concentración: 100× es el valor verificado para esta receta.** No es un techo universal — es el resultado de que ninguna sal de esta lista supere su solubilidad a 100× a la temperatura de trabajo. Cambiar una fuente cambia el techo.

### 3.3 Factor de concentración máximo: qué lo limita

- **La incompatibilidad es un fenómeno de concentración, no una propiedad absoluta.** *"Cuando nos referimos al término compatibilidad hablamos de fertilizantes que pueden mezclarse en altas concentraciones (por altas concentraciones nos referimos a más de 10 veces concentrado)."* **[V]** (Intagri). Dos sales que conviven perfectamente en el gotero a 1× precipitan a 100× en el tanque madre.
- **El techo real lo pone la solubilidad de la sal menos soluble a la temperatura mínima nocturna, no a 20 °C.** Datos **[V]** de Kafkafi & Tarchitzky (2011), Tabla 1.3 (g de producto por 100 g de agua):

| Temperatura | KNO₃ | KCl | K₂SO₄ | NH₄NO₃ | Urea |
|---|---|---|---|---|---|
| 10 °C | 21 | 31 | **9** | 158 | 84 |
| 20 °C | 31 | 34 | **11** | 195 | 105 |
| 40 °C | 46 | 37 | **13** | 242 | 133 |

El **sulfato de potasio es el cuello de botella**: 9 g/100 g a 10 °C. Un tanque B con K₂SO₄ formulado a 20 °C **cristaliza durante la noche**.

*Verificación sobre el tanque B del §3.2* **[C]**: 35 kg de K₂SO₄ en 1000 L = **35 g/L**, contra un límite de ~110 g/L a 20 °C y ~90 g/L a 10 °C. Hay margen de 2,6× incluso en la noche fría — **por eso esa receta tolera 100×**. Con 3× más K₂SO₄, o con un factor de 300×, el margen desaparece. La regla no es "100× siempre": es **"calcular la sal más limitante a la temperatura mínima"**.

- **Reacción endotérmica: el tanque se congela solo.** *"Algunos fertilizantes solos o en combinación pueden bajar la temperatura de la solución a niveles de congelamiento (por ejemplo, KNO₃, Ca(NO₃)₂, urea, NH₄NO₃, KCl y 5Ca(NO₃)₂·NH₄NO₃·10H₂O)."* **[V]** Y en la Tabla 1.2, la nota al pie: para urea y nitrato de amonio *"la temperatura de la solución cae a 0 °C; por eso toma más tiempo para que se disuelva todo el material"* **[V]**. Un tanque cargado de madrugada en invierno puede congelar parte de la solución y **cambiar la concentración real sin que nadie lo note**.
- Cantidad máxima disuelta en 100 L a 20 °C **[V]** (Tabla 1.2, Kafkafi & Tarchitzky 2011, adaptada de *Primary Industries: Agriculture*, 2000): urea 105 kg (20 min) · NH₄NO₃ 195 kg (20 min) · (NH₄)₂SO₄ 43 kg (15 min) · KCl 34 kg (5 min) · K₂SO₄ 11 kg (5 min) · KNO₃ 31 kg (3 min) · MKP 213 kg · MAP 40 kg (20 min) · DAP 60 kg (20 min).

### 3.4 Qué pasa cuando se viola la regla

Cadena de consecuencias, en orden de aparición:
1. **Lodo en el fondo del tanque.** El nutriente sale del balance: se aplicó menos Ca (o menos P) del calculado, y el balance de cargas del §2.1 deja de cerrar en el campo aunque cierre en la planilla.
2. **Partícula fina que atraviesa el filtro.** Los precipitados de fosfato de calcio se forman *aguas abajo* del filtro si la mezcla ocurre en el cabezal, y **la filtración no los ve**.
3. **Sellado del laberinto del emisor.** Es el modo de falla más caro porque es progresivo y no uniforme: baja la uniformidad de emisión antes de que se note un gotero tapado.
4. **El diagnóstico se corrompe.** Un análisis foliar que muestra Ca bajo lleva a subir la dosis de Ca — que precipita otra vez. Se sube la dosis del nutriente que está precipitando.

**Prueba de jarra obligatoria** **[V]**: *"Antes de inyectar cualquier químico, o antes de mezclar cualquier químico, siempre se debe hacer una 'prueba de jarra' para evaluar los peligros potenciales de taponamiento."* — Shortridge & Benham (2023), VCE 442-757. Se prepara la mezcla **a la concentración real del tanque madre**, se deja 12–24 h a la temperatura mínima esperada, y se mira el fondo.

---

## 4. SISTEMAS DE INYECCIÓN

Clasificación por el medio con que vencen la presión de la red **[V]** (Kafkafi & Tarchitzky 2011, §2.2.2):

### 4.1 Venturi

Principio: una contracción cónica acelera el flujo y baja la presión localmente hasta un valor muy bajo, lo que **succiona** la solución fertilizante desde el tanque (a través de un filtro de malla) hacia la red. Se regula con una válvula que fija la diferencia de velocidades entre los dos extremos. **[V]**

| Atributo | Estado |
|---|---|
| Costo y simplicidad | El más bajo; sin partes móviles ni energía externa |
| **Pérdida de carga requerida** | **[NV]** — no se pudo verificar en fuente institucional abierta el % exacto de diferencial requerido. Ver §9. |
| Proporcionalidad al caudal | Depende de la presión y el caudal de la línea: **si la presión de red cambia, la tasa de inyección cambia**. No es proporcional por sí solo. |
| Uso recomendado | Superficies chicas y medianas, sistemas con presión estable, cuando no hay electricidad |

> La debilidad real del venturi no es la pérdida de carga sino la **dependencia hidráulica**: la dosis inyectada es función del estado de la red. Una válvula de sector que abre en otro lado del campo cambia la fertilización del sector que se está regando. Con venturi hay que **medir la tasa de inyección en condiciones de operación**, no confiar en la curva del fabricante.

### 4.2 Bomba dosificadora (inyección por presión positiva)

Principio: la bomba eleva la presión de la solución madre por encima de la de la red y establece **una relación predeterminada entre volumen de solución fertilizante y volumen de agua de riego**, logrando distribución proporcional. **[V]**

Ventajas declaradas por la fuente **[V]**: (a) mantiene la presión de la línea **sin pérdidas**, (b) **exactitud** en la dosificación, (c) capacidad de proveer **una concentración determinada a lo largo de todo el ciclo de riego**.

Dos tipos: **pistón** y **diafragma**. Dos fuentes de energía **[V]**:
- **Hidráulica** (tipo Dosatron/Amiad): usa la presión del propio riego; el agua motriz —**aproximadamente tres veces el volumen de solución inyectada**— se descarga. Adecuada para áreas **sin electricidad**.
- **Eléctrica**: común en invernaderos y donde hay electricidad confiable.

| Atributo | Valor |
|---|---|
| Pérdida de carga en la línea | Ninguna (es la ventaja frente al venturi) |
| Consumo de agua motriz (bomba hidráulica) | ≈ **3 × el volumen inyectado**, descartado **[V]** |
| Precisión numérica (% de error) | **[NV]** — no verificada en fuente abierta. §9 |
| Uso recomendado | Cuando la dosis tiene que ser reproducible y auditable: ensayos, alta gama, superficies grandes con sectorización |

### 4.3 Tanque de derivación (presión diferencial / by-pass)

Principio: tanque metálico presurizado, hermético, con protección interna antiácida; una **válvula mariposa** en la línea crea un diferencial que desvía parte del agua de riego hacia el tanque. **[V]**

**Es el único sistema que admite fertilizante sólido y líquido.** **[V]**

**Y es el que no permite controlar la concentración.** Textual **[V]**:
> *"La concentración en el emisor al final de la línea se mantiene constante en tanto haya fertilizante sólido presente en el tanque y que el fertilizante se diluya rápidamente. Una vez que la fracción sólida se disuelve completamente, la concentración del fertilizante se reduce a una tasa exponencial. En la práctica, cuando haya pasado a través del tanque un volumen equivalente a cuatro tanques, sólo quedan cantidades ínfimas dentro de éste."*

Es decir: la curva de concentración es **exponencial decreciente** y la **regla de los 4 volúmenes de tanque** marca el agotamiento práctico. Consecuencias:
- No se puede fertilizar **proporcionalmente**: el primer cuarto del riego recibe mucho más que el último.
- El área regable por vez está limitada por el volumen del tanque.
- Riesgo de **congelamiento** del contenido al cargar sales endotérmicas (KNO₃, Ca(NO₃)₂, urea, NH₄NO₃, KCl) en la madrugada fría, *"lo que genera cambios inesperados en la concentración de nutrientes"* **[V]**.
- La propia fuente lo ubica históricamente: *"Este equipo se utilizó en los primeros estadios del desarrollo de la fertirrigación."* **[V]**

### 4.4 Criterio de selección

| Situación | Equipo |
|---|---|
| Sin electricidad, superficie chica, presión estable, dosis no crítica | Venturi |
| Sin electricidad, dosis reproducible | Bomba dosificadora **hidráulica** (aceptando el 300 % de agua motriz) |
| Con electricidad, dosis crítica, receta multi-tanque A/B/C | Bomba dosificadora **eléctrica**, una por tanque, con control por CE y pH |
| Fertilizante sólido, sin infraestructura, aplicación cuantitativa (no proporcional) | Tanque de derivación — aceptando que la concentración no es controlable |

**Dosificación: dos patrones, y no son intercambiables** **[V]** (Kafkafi & Tarchitzky 2011, §2.3, según Sne 2006):
- **Cuantitativa:** se inyecta una **cantidad determinada** de fertilizante en cada riego. Compatible con tanque de derivación.
- **Proporcional:** se mantiene una **relación constante** entre volumen de agua y volumen de solución → concentración constante. Requiere bomba (o venturi bien regulado con presión estable).

### 4.5 Seguridad de inyección — no es opcional

Requisitos de la instalación **[V]** (Shortridge & Benham 2023, VCE 442-757):
- Válvula de retención (check valve) **aguas arriba** del punto de inyección
- Válvula de drenaje de baja presión
- Válvula de alivio de vacío
- Válvula de retención **en la línea de inyección química**
- **Enclavamiento eléctrico** entre la bomba de riego y la bomba de inyección
- Dispositivo antirretorno conforme a norma **ASAE**

Y del lado de la fuente de agua **[V]** (Kafkafi & Tarchitzky 2011, §2.1): la presión de inyección debe superar la presión interna; debe haber un **filtro** que impida que partículas de la solución lleguen al emisor; y **una válvula que prevenga el retroflujo**.
UF/IFAS SL142 es tajante **[V]**: no se debe inyectar ácido en sistemas sin dispositivos de seguridad que **impidan automáticamente el retroflujo**, para proteger el acuífero.

---

## 5. GOTEO Y TAPONAMIENTO

### 5.1 Clasificación de riesgo de obstrucción

Ver la tabla completa en **§1.7** (Bucks/Nakayama vía VCE 442-757), con su advertencia de trazabilidad.

Los tres mecanismos, y son independientes:
1. **Físico** — sólidos suspendidos, arena, limo, restos de biopelícula desprendida.
2. **Químico** — precipitación de CaCO₃ (HCO₃ > 2 meq/L **y** pH > 7,5), de Fe³⁺, de Mn, de fosfato de calcio inducido por la propia fertirrigación.
3. **Biológico** — algas, bacterias filamentosas, biopelícula, bacterias del hierro y del azufre.

Cada uno tiene su tratamiento y **ninguno resuelve el de los otros**: filtrar no evita la precipitación química; acidular no mata la biopelícula; clorar no quita la arena, y con hierro presente **la empeora** si se hace en el lugar equivocado.

### 5.2 Filtración requerida

**Criterio de dimensionamiento** **[V]** (VCE 442-757): *remover las partículas mayores a **un décimo del diámetro de la abertura del emisor***, para prevenir el puenteo (*bridging*) de varias partículas en el paso de agua.
> *(La regla de 1/7 a 1/10 aparece en la literatura del rubro; el valor que se pudo verificar en fuente institucional abierta es **1/10**. El 1/7 queda como **[NV]**, §9.)*

**Equivalencia malla ↔ micras ↔ tamaño de partícula** **[V]** (VCE 442-757, Tabla 2):

| Clase | Tamaño (mm) | Micras | Malla (mesh) |
|---|---|---|---|
| Arena muy gruesa | 1,00 – 2,00 | 1000 – 2000 | 18 – 10 |
| Arena gruesa | 0,50 – 1,00 | 500 – 1000 | 35 – 18 |
| Arena media | 0,25 – 0,50 | 250 – 500 | 60 – 35 |
| Arena fina | 0,10 – 0,25 | 100 – 250 | 160 – 60 |
| Arena muy fina | 0,05 – 0,10 | 50 – 100 | 270 – 160 |
| Limo | 0,002 – 0,05 | 2 – 50 | 400 – 270 |

Referencia práctica **[V]**: *"Una malla 200 con abertura de 0,003 pulgadas removerá partículas del tamaño de arena fina y mayores, y usualmente es adecuada para sistemas de microrriego que usan agua subterránea."*

**Selección y operación por tipo de filtro** **[V]** (VCE 442-757):

| Tipo | Caudal admisible | Disparo de retrolavado | Cuándo usarlo / limitación |
|---|---|---|---|
| **Malla (screen)** | 200 gpm por pie² de área efectiva | Aumento de **3–5 psi** en la caída de presión | Agua subterránea, carga de sólidos baja. Se ciega rápido con materia orgánica |
| **Medios / arena** | ≈ 25 gpm por pie² de superficie | ≈ **10 psi** de caída de presión | **Agua superficial con algas y materia orgánica.** Requiere **3 o más unidades** para poder retrolavar sin cortar el riego |
| **Anillas (disc)** | 50 gpm por pie² (equivalente a malla 200) | Retrolavado hasta **50 psi** | **No recomendado donde la arena es preocupación importante** |
| **Hidrociclón** | — | — | Separador de arena; va **antes** del filtro principal. Datos numéricos **[NV]**, §9 |

Regla operativa derivada de la tabla: un filtro de medios necesita **8 veces más superficie** que uno de malla para el mismo caudal (25 vs 200 gpm/pie²). Cotizar un filtro de arena con la superficie de uno de malla es el error de dimensionamiento típico.

**Lavado de líneas (flushing)** **[V]** (VCE 442-757 y Clemson LGP 1190):
- Velocidad mínima de lavado: **1 pie/s (0,3 m/s)** — equivalente a ~1 gpm en lateral de 5/8" y ~2 gpm en lateral de 7/8".
- Duración: *"hasta que salga agua limpia de la línea lavada durante al menos dos minutos"*.
- Secuencia: **primero las principales, después las secundarias, por último las laterales**. Lavar la lateral primero solo empuja hacia ella la suciedad de la principal.

### 5.3 Mantenimiento con cloro — protocolos

**Química que manda: el pH.** **[V]** (UC ANR, *Chlorination for biological clogging problems*):
> *"El ácido hipocloroso es el agente más efectivo para controlar crecimientos biológicos. Su concentración depende del pH del agua. Mantener un pH de 7 o menos significa que al menos el **75 % del cloro** en el agua es ácido hipocloroso, mientras que a un pH de 8 solo alrededor del **25 %** lo es. A un pH menor de 3 predomina el gas cloro."*

Y el corolario operativo **[V]** (VCE 442-757): *"La cloración es relativamente inefectiva para el control bacteriano si el pH del agua está por encima de 7,5."*

> **Consecuencia de diseño:** en agua alcalina hay que **acidular primero y clorar después**, en ese orden, con **puntos de inyección separados**. Un programa de cloración a pH 8,2 está gastando 3 de cada 4 pesos de cloro.

**Protocolos con concentración y tiempo:**

| Modalidad | Concentración | Duración / frecuencia | Punto de medición | Fuente |
|---|---|---|---|---|
| **Continua** | **1 – 2 ppm de cloro libre** | Permanente, mientras riega | **Al final de la lateral más alejada** del punto de inyección | UC ANR **[V]**; VCE 442-757 **[V]** |
| **Periódica / de choque** | **10 – 20 ppm** | **≥ 2 horas**, ~1 vez por mes | Idem | UC ANR **[V]** |
| **De choque (variante)** | **10 – 30 ppm** | Semestral en sistemas con agua subterránea | Idem | VCE 442-757 **[V]** |
| **Recuperación de sistema tapado** | **50 ppm** | Inyectar ~2 h, **dejar el agua clorada en las tuberías ~24 h**, luego lavar | — | Clemson LGP 1190 **[V]** |
| **Superclorado** | Alta (no especificada) | Sólo para recuperar sistemas tapados por algas y limos bacterianos; *"requiere cuidado especial para evitar daño a plantas y equipo"* | — | UC ANR **[V]** |
| **Limpieza del filtro** | ~2 L (½ galón) de lavandina en la unidad de filtración | Remojo **6 horas** | — | Clemson LGP 1190 **[V]** |

**Por qué se mide al final de la lateral y no en el cabezal** **[V]**: *"Es importante verificar la concentración al final de la línea lateral, ya que el cloro se consume al reaccionar con los constituyentes orgánicos y con cualquier hierro y manganeso del agua."* Un residual de 2 ppm en el cabezal puede ser **cero** en el extremo del sector.
Medición: kit **DPD** (N,N-dietil-p-fenilendiamina) para cloro libre residual **[V]** (VCE 442-757), o test de cloro de piscina de buena calidad **[V]** (UC ANR).

**Cálculo de la tasa de inyección** **[V]** (UC ANR):
```
Hipoclorito de sodio:   IR (gal/h) = (0,006 × Q × C) ÷ S
Gas cloro:              IR (lb/día) = Q × C × 0,012
```
`Q` = caudal del sistema (gpm) · `C` = concentración deseada (ppm) · `S` = % de cloro disponible en la fuente.
Ejemplo de la fuente: lavandina doméstica al 5,25 %, sistema de 500 gpm, objetivo 5 ppm → `IR = (0,006 × 500 × 5) ÷ 5,25 = 2,9 gal/h`. **[V]**
Hipoclorito de calcio: **12,8 lb en 100 galones de agua = solución al 1 %**; 25,6 lb = 2 % **[V]**. *Precaución: al disolver hipoclorito de calcio puede formarse gas cloro.*

**El hipoclorito de sodio sube el pH** **[V]**: *"Agregar hipoclorito de sodio al agua produce iones hidroxilo, que elevan el pH del agua y con ello pueden disminuir la efectividad de la cloración. Puede ser necesaria la inyección de ácido para reducir el pH y aumentar la efectividad del cloro."* Es decir: el cloro se sabotea a sí mismo, y por eso la acidulación es parte del programa de cloración, no un programa aparte.

**Tolerancia del cultivo al cloro** **[V]** (Clemson LGP 1190): plántulas de hortalizas **< 1 ppm**; pimiento y tomate **> 8 ppm**; pimiento dulce **> 50 ppm**; brócoli **> 37 ppm**. *(Método no declarado en la fuente consultada; usar como orden de magnitud.)*

**Incompatibilidades del cloro:**
- **Cloro + ácido concentrado → gas cloro.** Tanques y puertos separados, 0,6–0,9 m de distancia **[V]**.
- **Cloro + fertilizantes fosfatados y amoniacales:** el cloro reacciona con el amonio formando cloraminas, de menor poder oxidante; y con fosfatos puede precipitar. La práctica de extensión es **no coinyectar** cloro con la fertilización. *(La incompatibilidad cloro–amonio/fosfato es de manual químico; no se citó fuente institucional específica en esta sesión → tratar el detalle como **[NV]**, §9; la separación de puertos sí está verificada.)*
- **Cloro + hierro/manganeso:** ver §1.7 — clorar **antes** del filtro, nunca después.

### 5.4 Mantenimiento con ácido — protocolos

| Objetivo | pH objetivo | Tiempo | Fuente |
|---|---|---|---|
| **Prevención** (evitar que precipite CaCO₃) | **< 7,0** | Continuo o por riego | VCE 442-757 **[V]**; Clemson LGP 1190 **[V]** |
| **Disolución activa** de precipitados existentes | **pH ≈ 5** | Mantener **24 h**, luego lavar con agua limpia | Clemson LGP 1190 **[V]** |
| **Remoción de incrustación establecida** | **pH tan bajo como 2,0** | Inyectar un "slug" concentrado y **dejarlo varias horas** antes de lavar | VCE 442-757 **[V]** |
| **Protocolo de fabricante** | **pH 2 – 3** durante **12–15 minutos**, con **0,6 % de ácido** en el agua de riego | Inyectar los 15 min recién con el sistema a presión máxima de operación; **limpiar los filtros inmediatamente después**; luego lavar principales → secundarias → laterales (de a ~10 líneas, ~1 min cada tanda) | Netafim USA, *Recommendations for the Treatment of Drip Irrigation Systems with Acid* **[V]** — literatura de fabricante |

**Límite inferior** **[V]** (Clemson LGP 1190): *evitar pH por debajo de 4 para no dañar los emisores.*
> **Nota de conflicto entre fuentes, declarada:** Clemson pone el piso en pH 4; VCE y Netafim admiten pH 2–3 en tratamiento de choque corto. La diferencia es **duración**: pH 2 por 15 minutos con lavado inmediato no es lo mismo que pH 4 sostenido 24 h. **Un protocolo que copie el pH sin copiar el tiempo destruye emisores.**

**Después de acidular, hay que lavar** **[V]** (Netafim): restablecer el flujo normal de agua **al menos una hora** para arrastrar el ácido remanente; crítico en instalaciones con tubería de acero, aluminio, fibrocemento u hormigón, que sí se corroen (el PE y el PVC resisten).

**Por qué también hay que enjuagar después de fertirrigar** **[V]** (Kafkafi & Tarchitzky 2011, §7): los emisores se tapan por **precipitación de CaCO₃ si los residuos no son enjuagados al final** del ciclo. Y para desatascar y restaurar la emisión, la fuente menciona el enjuague de las líneas con **ácido nítrico** **[V]** (§ *ibid.*).

### 5.5 Intrusión radicular (riego subsuperficial, SDI)

Tres vías conocidas: (a) emisores impregnados con **trifluralina** de liberación lenta, (b) inyección periódica de **ácido**, (c) aplicación de herbicida a través del sistema.

Existe literatura revisada por pares específica sobre el tema, incluyendo trabajo sobre **goteros enterrados bajo caña de azúcar** con trifluralina. En esta sesión **no se pudo abrir el texto completo ni verificar concentraciones, dosis y frecuencias** → los protocolos numéricos de intrusión radicular quedan **[NV]**, §9.
Lo que sí es criterio firme y no requiere cita: en SDI, el ácido cumple **doble función** (disuelve carbonatos y desalienta la raíz), y por eso la acidulación periódica es la práctica de base antes de recurrir a herbicida.

---

## 6. MANEJO DE LA FERTIRRIGACIÓN

### 6.1 Pulsos vs continuo, y en qué fracción del riego inyectar

**El protocolo verificado, para fertilizantes nítricos** **[V]** (Zhang et al. 2004, citado en Kafkafi & Tarchitzky 2011, §4.5.1):

| Fracción del tiempo de riego | Qué se aplica |
|---|---|
| **Primer cuarto** | **Sólo agua** |
| **Mitad central** | **Solución con nitratos** |
| **Último cuarto** | **Sólo agua** |

*"Este procedimiento mantuvo la mayor parte del nitrato cerca del gotero emisor."* **[V]**

**Por qué se empieza con agua limpia:** hay que humedecer el bulbo antes de meter el nutriente. Si se inyecta sobre suelo seco, el frente de mojado —que es el que más lejos llega— arrastra el nitrato al borde del bulbo, fuera de la zona de raíces.

**Por qué se termina con agua limpia — y son dos razones distintas:**
1. **Razón agronómica:** empujar el nutriente que quedó en la tubería hacia el suelo, y reposicionar el nitrato del borde hacia el centro del bulbo.
2. **Razón de mantenimiento:** dejar la lateral con agua, no con solución fertilizante. Solución concentrada estancada en la lateral entre riegos = precipitación de CaCO₃ y **alimento para la biopelícula** durante todas las horas que el sistema está parado. *"Los emisores [se tapan] por precipitación de CaCO₃ si los residuos no son enjuagados al final"* **[V]**.

**Pero el enjuague no puede ser largo** — y aquí hay un matiz medido **[V]** (Kafkafi & Tarchitzky 2011, §4.5.1): en un ensayo donde la solución emitida tenía **igual concentración de amonio y de nitrato**, justo debajo del emisor se midió **amonio extremadamente alto** (adsorbido a la arcilla) mientras **los nitratos se movieron al borde del bulbo**.
> *"Esta observación sugiere que en la práctica de campo el enjuague del remanente de la solución fertilizante en el sistema de líneas de goteros debería ser lo más corto posible luego de que haya terminado la inyección de nitratos, para evitar las pérdidas potenciales de nitratos desde la zona de raíces."* **[V]**

Es decir: **el último cuarto se usa para limpiar la línea, no para seguir regando.** Un enjuague generoso lixivia el nitrato que se acaba de aplicar.

**Caso especial de la urea** **[V]** (misma fuente, §4.5.2): la urea es neutra y se mueve con el agua.
- Urea inyectada en el **primer cuarto** → sigue moviéndose con el agua posterior → **empujada al extremo del bulbo húmedo**.
- Urea inyectada en el **último cuarto** → **queda cerca del gotero**.
> Y la advertencia asociada **[V]**: la urea fertirrigada que llega al **borde del bulbo** queda expuesta a **volatilización**, porque la evaporación desde la superficie concentra la urea cerca de la superficie del suelo. Con urea, la regla del "tercer cuarto seguido de enjuague" **es contraproducente**.

**Pulsos.** Kafkafi & Tarchitzky mencionan la aplicación por *"pulsos de fertilizantes con concentraciones más altas o más bajas que la concentración [objetivo]"* **[V]** como estrategia de manejo. No se verificó en esta sesión una comparación cuantitativa pulsos vs continuo con rendimiento → **[NV]**, §9.

### 6.2 Fracción de lavado y su cálculo

**Definición** **[V]** (FAO 29 Rev.1, §3, nota al pie): *"En muchos textos, los términos 'fracción de lavado (LF)' y 'requerimiento de lavado (LR)' se usan indistintamente. Ambos se refieren a la porción del riego que debe pasar a través de la zona radicular para controlar las sales a un nivel específico. LF indica que el valor se expresa como fracción; LR puede expresarse como fracción o como porcentaje."*

**Ecuación (9) de FAO 29 Rev.1** — atribuida a **Rhoades (1974)** y **Rhoades & Merrill (1976)** **[V]**:

```
        CEw
LR = ─────────────
      5·CEe − CEw
```

- `CEw` = salinidad del agua de riego aplicada, dS/m
- `CEe` = salinidad media del suelo tolerada por el cultivo, medida en **extracto de saturación**, tomada de la Tabla 4 de FAO 29 para el porcentaje de rendimiento aceptado.

> **La ecuación se muestra como imagen en la versión HTML de FAO y no se pudo leer píxel a píxel.** La forma `LR = CEw / (5·CEe − CEw)` es la que reproduce universalmente la literatura de salinidad para la ecuación (9) de FAO 29 (Rhoades 1974). Se marca como **[V] en la atribución** (Rhoades 1974; FAO 29 ec. 9) y **[NV] en la transcripción literal del símbolo**. Si se va a programar, **verificar contra el PDF original de FAO 29** antes de codificar.

**Criterio de qué CEe usar** **[V]** (FAO 29, texto que acompaña a la ecuación): *"Se recomienda usar el valor de CEe que pueda esperarse que resulte en al menos 90 % de rendimiento. Para agua en el rango de salinidad moderada a alta (> 1,5 dS/m), podría ser mejor usar el valor de CEe para el potencial de rendimiento máximo (100 %), ya que el control de la salinidad es crítico para obtener buenos rendimientos."*

**Lámina total a aplicar — ecuación (7) de FAO 29** **[V]**:
```
AW = ET / (1 − LR)
```
`AW` = lámina anual aplicada (mm/año) · `ET` = demanda hídrica anual del cultivo (mm/año) · `LR` = fracción de lavado.

**Y el supuesto que se olvida** **[V]**: *"La lluvia debe considerarse al estimar el requerimiento de lavado… La lluvia que infiltra… reduce proporcionalmente"* la fracción que hay que aportar con riego. En clima monzónico o con estación lluviosa marcada, **el LR calculado sobre CEw sin descontar lluvia sobreestima la lámina**.

Nota de coherencia con el §0: la propia Tabla 1 de FAO asume **LF ≥ 15 %**. Es decir, los umbrales de la Tabla 1 **ya incorporan** un lavado del 15 %. Usar la Tabla 1 en un sistema que riega con LF del 5 % es usarla fuera de su dominio.

### 6.3 Fraccionamiento a lo largo del ciclo

Principio verificado **[V]** (Kafkafi & Tarchitzky 2011, Introducción): la ventaja del fertirriego es aplicar el nutriente *"para alcanzar la máxima eficiencia del fertilizante aplicado"* sincronizando con la demanda, en la zona de raíces activas, *"de tal modo que se maximiza la eficiencia de uso de los nutrientes y se minimiza"* la contaminación.

Base cuantitativa disponible **[V]**: la Tabla 6.1 de Kafkafi & Tarchitzky (según Kafkafi & Kant 2004) reporta la **absorción de K por quintiles del ciclo** (0–20, 20–40, 40–60, 60–80, 80–100 % del tiempo entre siembra y cosecha) para algodón, maíz, caña, tomate y pimiento, en g/planta. El patrón medido en algodón, por ejemplo, es 0,60 → 2,00 → **3,60** → 0,60 → 0,20 g/planta: **más de la mitad de la absorción de K ocurre en el tercer quintil**.
> Esa es la forma correcta de fraccionar: **según la curva de absorción medida del cultivo**, no en dosis iguales por riego. La extracción de la tabla completa por cultivo no se completó en esta sesión → §9.

Y una advertencia estructural que la propia fuente pone **[V]** (§ sobre suministro periódico): la fertirrigación a intervalos periódicos *"asegura que no habrá deficiencia de ningún"* nutriente — el fraccionamiento fino sólo tiene sentido si el sistema puede sostener la frecuencia. Fraccionar en 30 aplicaciones un sistema que sólo puede operar 6 veces por ciclo es un plan de papel.

### 6.4 Movimiento del bulbo húmedo y colocación según movilidad

**Nitrato (NO₃⁻) — anión, móvil.** No se adsorbe al complejo de cambio (cargado negativamente). Se mueve con el agua **hasta el borde del bulbo húmedo** **[V]**. Es el ion que define el riesgo de lixiviación y el que impone la regla del §6.1.

**Amonio (NH₄⁺) — catión, se frena.** *"El amonio lleva carga eléctrica positiva y se adsorbe a los sitios cargados negativamente de las arcillas, pudiendo también reemplazar a otros cationes adsorbidos… Como resultado, **el amonio se concentra cerca de los goteros desplazando al Ca** y en menor medida al Mg, que se mueven con el frente de mojado. En pocos días, el amonio normalmente se oxida por las bacterias del suelo para formar nitrato, que se dispersa en el suelo con los siguientes ciclos de riego."* **[V]**
> Dos consecuencias operativas que casi nunca se mencionan: (1) el amonio **desplaza calcio** del complejo justo bajo el gotero; (2) la inmovilidad del amonio **dura días, no meses** — la nitrificación lo convierte en nitrato móvil.

**Fósforo (P) — el que no se mueve, aunque vaya disuelto.** **[V]**:
*"Las rápidas reacciones de los fosfatos con el Ca (suelos enriquecidos con carbonatos) en suelos básicos, y con el Fe y Al en suelos ácidos, restringen las distancias de movimiento del P aplicado al suelo. **Cuanto más alto sea el contenido de arcilla o la fracción de CaCO₃ en el suelo, más corta será la distancia de movimiento del P desde el gotero.** Aun en suelos arenosos (Ben Gal y Dudley, 2003), la distancia desplazada del P es bastante limitada en comparación con la del agua."*
Y: *"La difusión del P en el suelo es más bien lenta en comparación con la tasa de elongación de las raíces, a menos que haya una enorme concentración local de P o el P sea agregado"* (Lewis y Quirk, 1965) **[V]**.
**Excepción medida** **[V]**: cuando el P se acompleja con materia orgánica (p. ej. estiércol de pollo), *"puede moverse a distancias considerables desde el punto de aplicación"*, por flujo en **macroporos**. Es decir: el P orgánico complejado **sí lixivia** — que es exactamente el problema ambiental de los sistemas con estiércol (Kleinman et al. 2005).

**Potasio (K⁺) — intermedio.** **[V]**: *"Cuando el suelo no adsorbe potasio debido a que hay bajos contenidos de arcilla, **la distribución de K es normalmente mayor que la del P, pero menor que la del N**."* Demostrado en tomate fertirrigado sobre un suelo con **95 % de carbonato de calcio y baja CIC** (Kafkafi & Bar-Yosef 1980).
Y el criterio que desdramatiza **[V]**: *"En la práctica, la distribución exacta del K en el suelo desde el punto de emisión es poco importante, dado que las raíces pueden crecer y encontrar el K en la zona húmeda del bulbo. La eficiencia de las raíces de las plantas para absorber K es tan alta que donde las raíces encuentren una fuente de K, ésta es fácilmente absorbida."*
La excepción: *"En suelos muy arenosos y con muy bajo contenido de K, es necesaria la fertirrigación con un suministro diario de K y de N"*, particularmente con volumen radicular restringido **[V]**.

**Orden de movilidad, consolidado:**
```
NO₃⁻  >  urea (mientras no se hidrolice)  >  K⁺  >  NH₄⁺  >  H₂PO₄⁻
móvil ────────────────────────────────────────────────────► inmóvil
```

**Distancias de desplazamiento en centímetros, por textura.**
No se encontró **ningún dato medido a campo** de desplazamiento de NO₃⁻, NH₄⁺, P y K desde el gotero, por textura, en fuente abierta → **[NV]**, §9. Es el hueco más serio del dossier.

Lo único disponible es **simulación**, y hay que decirlo así **[V, pero SIMULACIÓN]** — **El-Nesr, M.N., Alazba, A.A. & Šimůnek, J. (2014).** *HYDRUS simulations of the effects of dual-drip subsurface irrigation and a physical barrier on water movement and solute transport in soils.* **Irrigation Science 32(2): 111–125.** Modelo HYDRUS-2D, gotero superficial y subsuperficial:

| Suelo | Alcance radial del agua | Alcance en profundidad |
|---|---|---|
| **Franco** (Ks = 0,01733 cm/min) | **nunca alcanzó 35 cm** (salvo con barrera física) | **no bajó de 60 cm** |
| **Arenoso** (Ks = 0,495 cm/min) | alcanzó 35 cm (poca cantidad) a los 1 440–2 880 min | **60 – 90 cm** |

Y coincide en orden de magnitud con la **medición de campo** del pH bajo el emisor (tabla siguiente): bulbo alterado de ~20–25 cm de radio en arena.

> **La regla física que sale de combinar §6.4 con §7.2, y que hay que decirle al cliente:** el P se mueve poco **y** el bulbo húmedo en suelo franco no pasa de ~30 cm radiales. Por lo tanto, **aplicar P por goteo no lo lleva más lejos que el frente de agua.** La ganancia del fertirriego con P no es "distribuirlo mejor en el lote": es **mantenerlo en solución y sincronizarlo con la demanda dentro de ese volumen chico**. Cualquier folleto que prometa distribución uniforme de P en el lote por goteo **contradice la física del bulbo**.

Referencias primarias para traer el dato medido (DOI verificado en Crossref, texto no accesible):
- **Mmolawa, K. & Or, D. (2000).** *Root zone solute dynamics under drip irrigation: A review.* **Plant and Soil 222: 163–190.** **DOI: 10.1023/A:1004756832038** ✔
- **Hanson, B.R., Šimůnek, J. & Hopmans, J.W. (2006).** *Evaluation of urea–ammonium–nitrate fertigation with drip irrigation using numerical modeling.* **Agricultural Water Management 86: 102–113.** **DOI: 10.1016/j.agwat.2006.06.013** ✔ — es **la** referencia para distribución de NO₃⁻/NH₄⁺ en el bulbo.

**Una medición de campo que sí está y que ordena la escala** **[V]** (UF/IFAS SL142, Tabla 1, datos de L.A. Halsey, Jefferson County Extension): en **arena**, regando por goteo con agua de 2,1 me/L de bases, el pH del suelo (0–15 cm de profundidad) medido según distancia al emisor fue:

| Distancia al emisor | pH del suelo |
|---|---|
| 0 – 1 pulgada (0 – 2,5 cm) | **7,6** |
| 8 – 10 pulgadas (20 – 25 cm) | **5,5** |
| 24 – 48 pulgadas (60 – 120 cm) | 5,0 (pH nativo) |
| 60 pulgadas (150 cm) | 5,0 (pH nativo) |

El bulbo químicamente alterado, en arena, tiene el orden de **20–25 cm de radio**. Todo lo que se aplique por el gotero y sea poco móvil vive dentro de ese círculo.

---

## 7. EFICIENCIA COMPARADA — EL NÚMERO QUE SOSTIENE LA VENTA

> **Marca adicional de esta sección.** Además de **[V]** / **[C]** / **[NV]**, aquí aparece **[V-res]**: *DOI verificado en Crossref y cifra tomada del resumen indexado, pero **el texto completo no se pudo abrir*** (paywall). Es evidencia utilizable **con la salvedad declarada**: no se pudo auditar el método ni los intervalos de confianza. **No se llenó ningún hueco con cifras de folleto.**

### 7.1 Nitrógeno — el meta-análisis que sostiene el argumento

**Li, H., Mei, X., Wang, J., Huang, F., Hao, W. & Li, B. (2021).** *Drip fertigation significantly increased crop yield, water productivity and nitrogen use efficiency with respect to traditional irrigation and fertilization practices: A meta-analysis in China.* **Agricultural Water Management 244: 106534.** **DOI: 10.1016/j.agwat.2020.106534** ✔ verificado en Crossref.

| Efecto del fertirriego por goteo vs. riego + fertilización tradicional | Valor | Marca |
|---|---|---|
| **Rendimiento** | **+12,0 %** | **[V-res]** |
| **Eficiencia de uso de N (NUE)** | **+34,3 %** | **[V-res]** |
| **Productividad del agua** | **+26,4 %** | **[V-res]** |
| Evapotranspiración del cultivo | **−11,3 %** | **[V-res]** |
| Rango de aumento de rendimiento según cultivo | **+6,0 % a +40,3 %** | **[V-res]** |
| Dosis de N de máxima respuesta | **100 – 200 kg N/ha** | **[V-res]** |

**Este es el número que sostiene la venta: +34,3 % de eficiencia de uso de N y +12,0 % de rendimiento**, de un meta-análisis publicado en una revista de primera línea. Con tres salvedades que hay que decir en la misma frase:
1. **Es de China.** El sesgo geográfico es real y estructural (clima, suelo, práctica de referencia, dosis de partida). No hay dato equivalente para Bolivia, Brasil ni el Cono Sur → §9.
2. La comparación es contra *"práctica tradicional de riego y fertilización"*. **Cuanto peor sea la práctica de referencia, mayor el efecto.** En un campo que ya fracciona y ya riega bien, la ganancia es menor.
3. El efecto sobre NUE (+34,3 %) es **casi tres veces** el efecto sobre rendimiento (+12,0 %). Es decir: **la mayor parte del beneficio es fertilizante que no se pierde, no grano que aparece.** El argumento comercial correcto es de costo de insumo y de ambiente, no de techo de rendimiento.

Meta-análisis de respaldo, con DOI verificado pero **sin cifras obtenidas** (texto cerrado) → **[NV]** en magnitud:
- **Zhu, Zhang, Li, Zhu & Kang (2023).** *Nutrient Cycling in Agroecosystems* 127(3): 359–373. **DOI: 10.1007/s10705-023-10318-5** — 2 546 pares de tratamiento de 139 publicaciones de campo; efecto positivo sobre rendimiento, mayor con microirrigación y aspersión.
- **Zheng, Zhou & Zhu (2023).** *Science of the Total Environment* 886: 163804. **DOI: 10.1016/j.scitotenv.2023.163804** — fertirriego por goteo sostiene productividad y mitiga pérdidas reactivas de N.
- **Yang, X., Zhang, L. & Liu, X. (2024).** *Scientia Horticulturae* 338: 113653. **DOI: 10.1016/j.scienta.2024.113653**

**Lo que NO se encontró y hay que decirlo:** ningún estudio con **¹⁵N** que compare directamente fertirriego por goteo contra voleo o incorporado **en cultivos extensivos**, con recuperación aparente medida. Es un hueco de esta búsqueda, no una prueba de que no exista.

### 7.2 Fósforo — el dato que corrige el argumento de venta más usado

Aquí sí hay una fuente institucional abierta y leída, y **desmiente el argumento comercial habitual**:

> *"La conclusión principal de este informe es que **la eficiencia del uso del P de fertilizante es a menudo alta (hasta 90 por ciento)** cuando se evalúa en una escala de tiempo adecuada usando el **método de balance**."* **[V]**

> *"El hecho de que los cultivos puedan recuperar P de fertilizante aplicado previamente durante períodos bastante largos demuestra que **el P no está fijado irreversiblemente en formas no disponibles en los suelos**."* **[V]**

**Syers, J.K., Johnston, A.E. & Curtin, D. (2008).** *Efficiency of soil and fertilizer phosphorus use: Reconciling changing concepts of soil phosphorus behaviour with agronomic information.* **FAO Fertilizer and Plant Nutrition Bulletin 18**, FAO, Roma. https://www.fao.org/4/a1595e/a1595e00.pdf

**Método, y es la clave de todo:** el informe distingue dos formas de medir y **prefiere explícitamente el método de balance** **[V]**:
- **Método de la diferencia:** absorción de P con fertilizante menos absorción sin fertilizante, sobre P aplicado. Es el que da los famosos "10–25 % de eficiencia del P".
- **Método de balance:** absorción total de P del cultivo como porcentaje del P aplicado, **contabilizando el P residual del suelo a lo largo de años**. Es el que da hasta 90 %.

**El mismo P, medido de las dos maneras — datos del boletín, leídos en el texto completo** **[V]**:

| Ensayo / contexto | Método diferencia | Método balance |
|---|---|---|
| Broadbalk (Rothamsted), trigo de invierno, **sin N** | **2 – 5 %** (sin cambio en 150 años) | — |
| Broadbalk, trigo de invierno, **con 96 kg N/ha** | **14 % (1852–71) → 33 % (1985–2000)** | **34 % → 50–52 %** |
| Saxmundham, rotación 4 años, suelo **Olsen P = 4 mg/kg** | 43 % → 24 % (cae al subir la dosis) | **85 % → 39 %** |
| Saxmundham, mismo ensayo, suelo **Olsen P = 33 mg/kg** | **3 – 4 %** | **140 % → 50 %** |
| Agdell, Olsen P 6 mg/kg | cebada 16 %, papa 8 %, remolacha 27 % | — |
| Agdell, Olsen P 59 mg/kg | cebada 6 %, papa **0 %**, remolacha **0 %** | — |
| Invernadero, ryegrass, 10 suelos (Johnston & Richards 2003) | **34 – 44 %** | — |
| ³²P directo, cereales y raíces, RU 1952–54 (Mattingly & Widdowson) | **5 – 25 %** | — |

Tres lecturas que salen de esta tabla y que cambian la conversación con el cliente:
1. **El "2–5 % de eficiencia del P" del Broadbalk sin N no es un problema de P: es un problema de N.** Con N, la misma parcela sube a 33 %. **Un P que no rinde puede ser un N que falta.**
2. **En suelo con P alto (Olsen 59), la recuperación por diferencia es 0 %** en papa y remolacha. No porque el P se pierda: porque **no hacía falta**. Vender "mejora de eficiencia del P" en un suelo por encima del valor crítico es vender la corrección de un problema que no existe.
3. **Los valores de balance por encima de 100 %** (Saxmundham, 140 %) son el cultivo **extrayendo P residual acumulado**. Eso es minería de suelo, y aparece como "eficiencia altísima".

> **Implicancia para la venta del servicio, y es incómoda:** si el argumento es *"el fertirriego mejora la eficiencia del P porque lo aplica disuelto"*, ese argumento **compara contra un número (10–25 %) que la FAO considera un artefacto del método de medición**. El P aplicado al voleo no se pierde: se acumula como P residual y se recupera en años siguientes. Lo que el fertirriego puede legítimamente ofrecer en P es **sincronía y posicionamiento en el año de aplicación**, no "recuperar P que se perdía".

Y el propio informe advierte el costo de la transición **[V]**: *"Para llevar el P del suelo al valor crítico, puede ser necesario aceptar una recuperación más baja del P agregado por algunos años."*

### 7.3 Nitrógeno — el dato de volatilización que sí está medido

Éste es el terreno donde la ganancia de eficiencia es real y medible, y viene de **evitar la volatilización**, no del goteo en sí.

**[V]** Terman & Hunt (1964), citados en Kafkafi & Tarchitzky (2011), §4.2.1:

| Manejo de la urea | Pérdida de N |
|---|---|
| Urea **en superficie**, suelo a **pH 5,2** | hasta **70 %** de la urea aplicada |
| Urea **en superficie**, mismo suelo **encalado a pH 7,5** | **82 %** |
| Urea **mezclada con el suelo** al pH original 5,2 | **25 %** |

> **Método:** valores citados de segunda mano (a través del manual IFA/IPI); no se leyó el trabajo original de Terman & Hunt 1964. Son de un ensayo específico, no un promedio — pérdidas de 70–82 % son del extremo alto del rango que reporta la literatura. **Marcar como orden de magnitud, no como coeficiente de cálculo.**

Lo que el número sí soporta: **incorporar o inyectar la urea reduce la pérdida por volatilización en un factor de ~3** en ese suelo. Y explica por qué el §8 (inyección subsuperficial en extensivo) tiene un caso económico propio, independiente del goteo.

> **El cuerpo de evidencia cuantitativo de volatilización —síntesis global de 824 observaciones, ensayos brasileños de siembra directa con cuatro campañas, y el efecto del orden riego/fertilización— está en el §8.2**, porque el beneficio pertenece a la colocación, no al fertirriego. Aquí sólo interesa la contracara:

Y la contracara que la misma fuente pone **[V]**: en fertirriego, la urea que llega al **borde del bulbo** y se concentra por evaporación superficial **también se volatiliza**. *"Tales pérdidas son difíciles de monitorear en condiciones de campo, pero muchos trabajos que han medido la recuperación del N por el cultivo sugieren que ésta es una vía directa para perder N"* (Haynes 1985). También se reportan pérdidas significativas de **N₂O y NO** con amonio o urea en fertirriego (Hoffman & Van Cleemput 2004) **[V]**.
**El fertirriego no elimina la volatilización de la urea. La reubica.**

### 7.4 Potasio

**No se encontró un solo dato defendible** de eficiencia de recuperación de K comparando fertirriego contra voleo. Búsqueda por Crossref y OpenAlex con filtro de acceso abierto: los resultados son trabajos de nutrición general en cítricos, arándano, cereza y lechuga, ninguno con la comparación pedida. **Sección vacía a propósito** → §9.

Lo único que se puede afirmar sobre K, y es de mecanismo, no de eficiencia **[V]** (Kafkafi & Tarchitzky 2011, §6.5): *"La eficiencia de las raíces de las plantas para absorber K es tan alta que donde las raíces encuentren una fuente de K, ésta es fácilmente absorbida."* Es decir: **es el nutriente donde menos cabe esperar una ganancia por fertirriego**, salvo en suelo muy arenoso con K bajo y volumen radicular restringido.

### 7.5 Lo que falta y hay que traer

| Dato | Estado |
|---|---|
| Recuperación aparente de N con **¹⁵N** en fertirriego vs. voleo, extensivo | **[NV]** — no encontrado |
| % de ahorro de N a igual rendimiento, con primario leído | **[NV]** |
| **Eficiencia de K** en fertirriego vs. voleo | **[NV]** — sección vacía |
| Datos de ensayo en **Bolivia / Brasil / Cono Sur** para fertirriego | **[NV]** — lo verificado es de China, RU, EE.UU., Israel y Países Bajos. *(Sí hay dato brasileño de volatilización: §8.2.)* |
| Cifras de Zhu et al. 2023 y Zheng et al. 2023 | **[NV]** — DOI verificado, texto cerrado |

---

## 8. INYECCIÓN SUBSUPERFICIAL Y APLICACIÓN LOCALIZADA AL SUELO EN EXTENSIVO

> Es la sección con **mejor evidencia de campo de todo el dossier**, y con un dato brasileño en siembra directa que sí transfiere razonablemente al Cono Sur.

### 8.1 Las modalidades

| Modalidad | Descripción | Qué gana frente al voleo |
|---|---|---|
| **Banda superficial / chorro dirigido** (*dribble, streaming, surface band*) | Solución depositada en una banda estrecha sobre el suelo, entre líneas o al costado | Concentra el nutriente (menor superficie de contacto suelo–fertilizante → menor fijación de P); reduce el contacto con rastrojo (menos ureasa) |
| **Inyección líquida subsuperficial** (*knife / coulter injection*) | Solución colocada 5–15 cm bajo la superficie con cuchilla o disco | **Elimina la volatilización de NH₃** al no dejar el N en superficie; ubica el nutriente en suelo húmedo |
| **Banda arrancadora con el sembrador** (*starter*) | Fertilizante al costado y debajo de la semilla | Sincroniza con la demanda inicial; ver el efecto amonio–P de abajo |

### 8.2 Volatilización de NH₃: el número que justifica la inyección

**Síntesis global** **[V-res]** — **Pan, B., Lam, S.K., Mosier, A., Luo, Y. & Chen, D. (2016).** *Ammonia volatilization from synthetic fertilizers and its mitigation strategies: A global synthesis.* **Agriculture, Ecosystems & Environment 232: 283–289.** **DOI: 10.1016/j.agee.2016.08.019** ✔ — 824 observaciones:

| Dato | Valor |
|---|---|
| Pérdida global de N como NH₃ desde fertilizantes sintéticos | media **18 %**, hasta **64 %** |
| **Reducción de la volatilización por colocación profunda del fertilizante** | **−55 %** |

**Ensayo de campo brasileño, siembra directa — el dato más transferible al Cono Sur** **[V]**:
**Fontoura, S.M.V. & Bayer, C. (2010).** *Volatilização de amônia e eficiência agronômica de fontes nitrogenadas em milho sob plantio direto.* **Revista Brasileira de Ciência do Solo 34(5): 1677–1684.** **DOI: 10.1590/s0100-06832010000500020** ✔
Maíz en siembra directa, Latossolo Bruno arcilloso (640 g arcilla/kg), 150 kg N/ha en V5, Guarapuava (PR), 4 campañas 2004/05–2007/08:

| Manejo | Pérdida de NH₃ (% del N aplicado) |
|---|---|
| **Urea superficial** — media de 4 años | **12,5 %** **[V]** |
| **Urea incorporada** | **1,1 %** — *valor leído citado por Cancellier et al. 2016 atribuido a este trabajo; no aislado en la tabla del original* → **[V-secundaria]** |
| Urea superficial, **variabilidad interanual** | **1,3 % / 25,4 % / 20,1 % / 3,0 %** **[V]** |
| Tasa de pérdida al 3.er día en años secos | ≈ **8 kg N/ha/día** **[V]** |

> **La variabilidad interanual es el dato más importante de la tabla, y no es ruido: es el hallazgo.** El mismo fertilizante, la misma dosis, el mismo cultivo, el mismo lote, y la pérdida va de **1,3 % a 25,4 %** según el año. **Ningún coeficiente de volatilización se puede usar como constante de cálculo.** Lo que se puede usar es la **dirección** (incorporar reduce ~10×) y la **distribución** (el riesgo se concentra en pocos días).

**Cuándo ocurre la pérdida — y cómo se la puede anular con riego** **[V]**:
**Viero, F., Bayer, C., Vieira, R.C.B. & Carniel, E. (2015).** RBCS 39(6): 1737–1743. **DOI: 10.1590/01000683rbcs20150132** ✔ — maíz en siembra directa de 28 años, Argissolo Vermelho, 180 kg N/ha al voleo, Depressão Central (RS):

| Dato | Valor |
|---|---|
| **> 90 % de la pérdida ocurre en los primeros 3 días** | picos hasta **15,4 kg N/ha/día** |
| **Regar DESPUÉS de fertilizar** | urea **−67 %** · urea+NBPT **−50 %** · liberación lenta **−40 %** |
| **Regar ANTES de fertilizar** | **no redujo las pérdidas** |

> **Este es el puente entre el §6 y el §8, y es directamente accionable en un campo con pivote:** aplicar urea al voleo y **regar inmediatamente después** recupera dos tercios de la pérdida. Regar antes no sirve. Y la ventana de decisión son **72 horas**.

**Inhibidores y recubrimientos, misma región** **[V]** — **Cancellier, E.L. et al. (2016).** *Ciência e Agrotecnologia* 40(2): 133–144. **DOI: 10.1590/1413-70542016402031115** ✔ — maíz siembra directa, Latossolo Vermelho, Lavras (MG), banda superficial:
urea+**NBPT −18,6 %** · urea+Cu+B −17,9 % · **urea recubierta con S+polímeros −37,2 %** (todas respecto de urea común).

**Rango de contexto, para no transferir a ciegas** (todas **[V-secundaria]**, citadas dentro de los trabajos leídos):

| Contexto | Pérdida por urea superficial |
|---|---|
| Regiones **tropicales irrigadas de Brasil** | **38 – 78 %** (Lara-Cabezas et al. 2000) |
| Suelo arenoso, RS Brasil (1 769 mm, 19,3 °C) | 17 % (Da Ros et al. 2005) |
| **Balcarce, Argentina** (870 mm, 13,7 °C) | **13,6 %** (Rozas et al. 1999) |
| Maíz irrigado, semiárido EE.UU. | **0,1 – 4,0 %** (Jantalia et al. 2012) |

**De 0,1 % a 78 % según el sitio.** Cualquier número de volatilización que se le presente a un cliente sin decir el sitio, el clima y el año **es publicidad**.

**Urea vs. UAN** **[V]** (Manitoba Agriculture, *Volatilization of Surface Applied Urea/UAN*, jun. 2023, https://www.gov.mb.ca/agriculture/crops/seasonal-reports/pubs/volatilization-surface-applied-urea.pdf — documento de extensión leído; **la tabla no cita el paper primario** → cifras con reserva):
Jerarquía por riesgo: **urea > solución UAN > nitrato de amonio**. Pérdida a 7 días: mayo (20–25 °C) urea 40 %, UAN 7 %; julio (30 °C) urea 88 %, UAN 50 %. *Cifras extremas; tratar como orden de magnitud.* El mismo documento afirma que **UAN en banda superficial o chorro dirigido está "mucho menos sujeto a volatilización" que en aspersión total** — pero **sin cifra** → **[NV]**.

### 8.3 Los tres mecanismos verificados

**(a) La volatilización se evita colocando el N bajo la superficie.** Cuantificado arriba: **−55 %** por colocación profunda en la síntesis global de 824 observaciones **[V-res]**, y **12,5 % → 1,1 %** en el ensayo brasileño de siembra directa **[V / V-secundaria]**. Ésta es la ganancia de la inyección subsuperficial de UAN o urea líquida frente a la superficial, y **no tiene nada que ver con el goteo**.

**(b) El P en banda con fuente amoniacal absorbe hasta 5 veces más.** **[V]** (Kafkafi & Tarchitzky 2011, §5.3, citando Black 1968; Duncan & Ohlrogge 1957; Imas et al. 1997a,b):
> Colocar el fertilizante fosfatado **en banda junto con sulfato de amonio** resultó en **más de cinco veces** más P absorbido por maíz que colocarlo con una fuente **nítrica**.

Mecanismo medido: la absorción de NH₄⁺ **acidifica la rizosfera**; la absorción de NO₃⁻ la **alcaliniza**. Con nitrato, el pH cerca de la raíz de maíz sube a 6,5; el P se fija. Con amonio, baja, y el P se libera. **[V]**
> Esto **no es un argumento a favor del fertirriego**. Es un argumento a favor de la **banda arrancadora amoniacal con P** — que es aplicación localizada al suelo, con sembradora, en extensivo. La escala en la que se puede sostener este mecanismo con goteo es otra.

**(c) El P inmóvil premia la colocación, no la disolución.** El P se mueve poco desde el punto de aplicación **cualquiera sea la forma en que se aplique** (§6.4) **[V]**. Aplicarlo disuelto no lo hace móvil. Lo que cambia el resultado es **dónde se lo deja respecto de la raíz**, y ese es exactamente el argumento de la banda.

### 8.4 Cuánto gana la banda — y la profundidad óptima

**Meta-análisis de colocación de fertilizante** **[V-res]** — **Nkebiwe, P.M., Weinmann, M., Bar-Tal, A. & Müller, T. (2016).** *Fertilizer placement to improve crop nutrient acquisition and yield: A review and meta-analysis.* **Field Crops Research 196: 389–401.** **DOI: 10.1016/j.fcr.2016.07.018** ✔

| Hallazgo | Valor |
|---|---|
| Colocación **subsuperficial profunda (> 10 cm)** vs. voleo | **+14 % a +27 %** en rendimiento y absorción |
| Combinación de mejor efecto | **NH₄⁺ + P**, o **urea + P**, colocados a **10 – 20 cm** |
| Condición que potencia el efecto | **P junto con N** en la misma banda |

> Nótese que esto confirma con meta-análisis el mecanismo del §8.3(b): **el efecto máximo es amonio + P juntos**, no P solo. Es la misma química de acidificación de rizosfera, medida a escala de literatura.

**Arrancador subsuperficial en maíz — dato de EE.UU.** **[V-res]** — **Quinn, D., Lee, C. & Poffenbarger, H. (2020).** *Field Crops Research* 254: 107834. **DOI: 10.1016/j.fcr.2020.107834** ✔ — 474 observaciones, 23 estudios:

| Colocación | Efecto sobre rendimiento |
|---|---|
| Arrancador subsuperficial (promedio) | **+5,2 %** |
| **2×2** cuando el grueso del N se retrasa a *sidedress* | **+8,9 %** |
| **In-furrow** en el mismo escenario | **sin efecto significativo** |

**³²P colocado vs. al voleo, mismo año** **[V]** (leído en FAO Bulletin 18 p.32, citando Mattingly & Widdowson 1959, *Plant and Soil* 10:161–175; **primario no abierto**): cebada de primavera, dos suelos (pH 7,4 y 5,3), RU 1953–54 → **colocado 10–15 %** vs. **voleo 5–12 %**.

### 8.5 El factor de equivalencia banda:voleo — hallazgo NEGATIVO, y hay que declararlo

**No existe, en la literatura que se pudo verificar, un factor de equivalencia agronómica publicado del tipo "2 kg de P₂O₅ al voleo = 1 kg en banda".**

Y no es sólo un límite de esta búsqueda. El propio FAO Bulletin 18, tras revisar la literatura mundial de P, declara explícitamente que **hace falta una revisión exhaustiva y más investigación sobre la efectividad agronómica y económica del P colocado frente al P al voleo** (p. 52) **[V]**. En 2008, la autoridad de referencia en eficiencia de P dijo que esa comparación sistemática **todavía no estaba hecha**.

Y advierte de un artificio contable en el propio concepto **[V]**: una absorción proporcionalmente mayor desde una **dosis menor colocada** puede representar **la misma eficiencia de uso de P** que una dosis mayor al voleo en un suelo que está en el valor crítico — y la dosis menor **deja menos P residual**, con lo cual las reservas de P disponible del suelo se acumulan más lentamente.

> **Traducción comercial, y es incómoda:** el "ahorro" que promete la banda puede ser, en parte, **minería de suelo diferida** y no eficiencia. El factor 2:1 debe tratarse como **folclore de extensión** hasta que alguien lo respalde con un ensayo citable. La evidencia real de que la banda gana es la de **Nkebiwe 2016 (+14–27 %)** y **Quinn 2020 (+5,2 %; 2×2 > in-furrow)** — que son ganancias de **rendimiento**, no factores de conversión de dosis.

### 8.6 Lo que falta verificar

| Dato | Estado |
|---|---|
| Factor de equivalencia agronómica banda ↔ voleo para P | **[NV]** — probablemente **no exista publicado**; ver §8.5 |
| Separación entre bandas y distancia banda–semilla, con fuente institucional | **[NV]** |
| Límites de seguridad salina (N + K₂O máximo) en la línea de siembra | **[NV]** |
| UAN inyectado vs. superficial con cifra de primario | **[NV]** — Woodley et al. 2020, SSSAJ, **DOI 10.1002/saj2.20079** dio HTTP 403 |
| Chorro dirigido / *dribble* vs. aspersión total de UAN, cuantificado | **[NV]** — sólo el cualitativo de extensión de Manitoba |
| K en banda vs. voleo en extensivo | **[NV]** |

---

## 9. TABLA "NO VERIFICADO"

Todo lo de esta tabla **no se usa para decidir ni para cotizar** hasta que se abra la fuente primaria.

| # | Afirmación / dato faltante | Por qué quedó sin verificar | Dónde buscarlo |
|---|---|---|---|
| 1 | Costo por meq neutralizado de **ácido nítrico** y **ácido cítrico** | No figuran en la Tabla 3 de UF/IFAS SL142, única tabla de costos abierta | Cotización local; los precios de SL142 son de Florida años 1990 y no transfieren |
| 2 | Transcripción literal de la ecuación (9) de FAO 29 (fracción de lavado) | En la versión HTML de FAO la ecuación es una imagen (`T0234E21.gif`) | PDF original de FAO 29 Rev.1 |
| 3 | ~~Tablas de CE objetivo y receta por cultivo~~ | **RESUELTO** — tomate y pepino en §2.2 | — |
| 4 | ~~Relaciones K : Ca : Mg~~ | **RESUELTO** — §2.3, calculadas sobre las recetas verificadas | — |
| 5 | ~~DOI del libro Sonneveld & Voogt (2009)~~ | **RESUELTO** — `10.1007/978-90-481-2532-6` ✔ Crossref | — |
| 5b | Recetas y CE objetivo para **cultivos extensivos en suelo** y clima tropical/subtropical | Todo lo verificado es sustrato inerte, invernadero, Países Bajos | Embrapa; INTA; literatura de fertirriego de caña/algodón |
| 6 | **Pérdida de carga del venturi** (% del diferencial de presión requerido) | No verificada en fuente institucional abierta | ASABE; catálogos de fabricante con curva; Irrigation Science |
| 7 | **Precisión (% de error) de bombas dosificadoras** | Sólo afirmación cualitativa ("exactitud") en IFA/IPI | Ensayos ASABE; ISO 15873 |
| 8 | Datos numéricos de **hidrociclón** (eficiencia, caída de presión) | No buscada en fuente abierta | VCE/UC ANR/fabricantes |
| 9 | Regla de filtración **1/7** del diámetro del emisor | Sólo se verificó **1/10** (VCE 442-757) | Nakayama & Bucks (1986) *Trickle Irrigation for Crop Production* |
| 10 | Tabla original de **Bucks, Nakayama & Gilbert (1979)** con sus cortes exactos | Paywall Elsevier; se usaron los cortes de VCE 442-757 (2023) | DOI 10.1016/0378-3774(79)90028-3 |
| 11 | Umbrales por **género de bacteria del hierro/azufre** (*Gallionella, Leptothrix, Thiobacillus*) | No se abrió fuente institucional con umbrales | Nakayama & Bucks (1991), DOI 10.1007/BF00190522 |
| 12 | Incompatibilidad cuantitativa **cloro + fosfatos/amoniacales** | Sólo verificada la separación física de puertos, no la química con números | Extensión (Nebraska, UC ANR) |
| 13 | Protocolos numéricos de **intrusión radicular** (trifluralina: dosis, frecuencia) | No se abrió texto completo | Literatura de SDI; ensayo publicado sobre goteros enterrados en caña |
| 14 | Comparación cuantitativa **pulsos vs continuo** con rendimiento | Sólo mención cualitativa en IFA/IPI | Agricultural Water Management |
| 15 | **Distancias MEDIDAS en cm** de NO₃, NH₄, P, K desde el gotero por textura | Sólo se consiguió **simulación** HYDRUS de movimiento de **agua** (El-Nesr 2014). Ningún dato medido de nutrientes | Hanson, Šimůnek & Hopmans 2006 (10.1016/j.agwat.2006.06.013); Mmolawa & Or 2000 (10.1023/A:1004756832038) |
| 16 | ~~% de aumento de NUE en fertirriego vs convencional~~ | **RESUELTO parcialmente** — §7.1, Li et al. 2021: NUE **+34,3 %**, rendimiento **+12,0 %**, marcado **[V-res]** (texto completo no leído) | Conseguir el PDF para auditar método e IC |
| 16b | Cifras de **Zhu et al. 2023** (10.1007/s10705-023-10318-5) y **Zheng et al. 2023** (10.1016/j.scitotenv.2023.163804) | DOI verificado, texto cerrado | Biblioteca |
| 17 | Eficiencia de **K** en fertirriego vs voleo | Búsqueda en Crossref y OpenAlex con filtro de acceso abierto: **cero resultados pertinentes** | — |
| 18 | Recuperación aparente de N con **¹⁵N** en fertirriego vs voleo, **extensivo** | No encontrado ningún estudio con esa comparación directa | — |
| 18b | Cifras de ¹⁵N vistas pero **NO citables** (fuente inaccesible): 77–82 % vs 58–66 % en pimiento (*Agronomy* 10:741); trigo 19,79 % / 47,64 % | Dominio MDPI bloqueado / revista china no accesible | **No usar** |
| 19 | ~~Equivalencia agronómica banda ↔ voleo para P~~ | **HALLAZGO NEGATIVO** — §8.5: probablemente **no exista publicado**; FAO Bull. 18 p.52 declara que la comparación sistemática no está hecha | — |
| 20 | ~~Reducción de volatilización de NH₃ por colocación profunda~~ | **RESUELTO** — §8.2: **−55 %** (Pan et al. 2016, 824 obs.); 12,5 % → 1,1 % (Fontoura & Bayer 2010) | — |
| 20b | **Curva** de reducción de NH₃ **en función de la profundidad** (no un valor único) | No verificada | Woodley et al. 2020 (10.1002/saj2.20079) — dio HTTP 403 |
| 21 | Eficiencia de **fertirriego** en Bolivia / Brasil / Cono Sur | No encontrada. *(Sí hay dato de volatilización brasileño y argentino: §8.2)* | Embrapa; INTA; UNESP *Irriga* |
| 22 | Tabla completa de **absorción de K por quintil del ciclo** por cultivo | Identificada (Kafkafi & Kant 2004, Tabla 6.1) pero no extraída íntegra | Kafkafi & Tarchitzky (2011), Tabla 6.1 |
| 23 | Método declarado de los umbrales de **tolerancia al cloro por cultivo** (Clemson) | La fuente no declara el método | Clemson LGP 1190 y sus referencias |
| 24 | Revisión específica de **fertirriego de P en el Mediterráneo** | DOI verificado, PDF dio 403 | `10.1016/j.heliyon.2024.e25543` |
| 25 | **Chorro dirigido / *dribble* de UAN vs. aspersión total**, cuantificado | Sólo afirmación cualitativa de extensión de Manitoba | — |
| 26 | Cifras de folleto vistas y **descartadas**: "reducción de pérdidas de N 25–50 % en fertirriego"; "N parcial productivo +48,9 % hortalizas / +63,1 % frutales"; "inyección de UAN hasta 99 % menos NH₃" | Fuente primaria inaccesible o inexistente | **No usar bajo ningún concepto** |

> **Nota de método sobre esta tabla.** Durante la investigación se conjeturó por patrón el DOI `10.1016/j.fcr.2016.05.010` para Nkebiwe et al. 2016. Crossref devolvió **un trabajo distinto** (soja, Kaschuk et al.). El DOI correcto es `10.1016/j.fcr.2016.07.018`. Se deja constancia porque **la conjetura de DOIs por patrón es exactamente el mecanismo por el que se cuelan citas inventadas** en un informe.

---

## 10. LO QUE NO SE PUEDE

Cada punto con su número y su fuente. Esto es lo que hay que decirle al cliente **antes** de firmar, no después.

**1. El fertirriego no corrige un suelo compactado — y con goteo el problema empeora.**
El agua entra donde puede. FAO 29 asume explícitamente *"buen drenaje interno"* y *"drenaje bueno, sin capa freática somera no controlada dentro de los 2 metros de la superficie"* como condición para que sus guías apliquen **[V]**. Fuera de ese supuesto, el bulbo húmedo se deforma: se ensancha en superficie y no baja. El nutriente queda arriba, la raíz no baja, y la sal se acumula en el borde lateral del bulbo. **Ningún ajuste de receta compensa una capa compactada.** Se rompe primero.

**2. El P sigue siendo poco móvil aunque se lo aplique disuelto — y el techo se lo pone el bulbo, no la solubilidad.**
*"Cuanto más alto sea el contenido de arcilla o la fracción de CaCO₃ en el suelo, más corta será la distancia de movimiento del P desde el gotero. Aun en suelos arenosos, la distancia desplazada del P es bastante limitada en comparación con la del agua."* **[V]** (Kafkafi & Tarchitzky 2011, §5.4, citando Ben Gal & Dudley 2003).
La difusión del P es lenta *"en comparación con la tasa de elongación de las raíces"* (Lewis & Quirk 1965) **[V]**: **la raíz llega al P antes de que el P llegue a la raíz.**
Y el límite duro: en **suelo franco el frente de agua no alcanza los 35 cm radiales ni baja de 60 cm** (simulación HYDRUS-2D, El-Nesr et al. 2014) **[V, simulación]**. **El P no puede ir más lejos que el agua, y el agua no va lejos.** Vender "P disuelto = P disponible en todo el lote" es falso por partida doble.

**3. El agua salina no se compensa con más fertilizante — se compensa con más agua, o no se compensa.**
La CE es un agregado: `CE ≈ (Σeq cationes + Σeq aniones)/20` **[V]**. Agregar fertilizante **sube** la CE. Si el agua base ya trae 1,8 dS/m y el cultivo tolera 2,5 en zona radicular, quedan **0,7 dS/m ≈ 7 meq/L** de margen total **[C]** — menos de la mitad de una receta completa. La única herramienta contra la sal es la **fracción de lavado** (§6.2), que cuesta agua: con `LR = CEw/(5·CEe − CEw)`, un agua de CEw 3,0 sobre un cultivo de CEe 4,0 exige `3,0/(20−3,0) = 0,18`, o sea **18 % más lámina, todos los riegos, todo el ciclo** **[C, sobre la ec. 9 de FAO 29]**. Ese 18 % es un costo operativo permanente, no un ajuste.

**4. El Fe²⁺ del agua nunca fue fertilizante.**
*"Esto siempre va a ocurrir en el momento en que el agua pasa por una boquilla de aspersión o un gotero… Esto significa que **nada de este hierro puede estar disponible para las plantas**, porque va a haber [precipitado]."* **[V]** (Eurofins Agro et al. 2016). Un análisis de agua que reporta 1,2 mg/L de Fe no está reportando 1,2 mg/L de nutriente: está reportando **riesgo de obstrucción severo** (> 1,5 = severo; 0,1–1,5 = moderado, VCE 442-757 **[V]**). El Fe se aporta quelatado por la receta, no por el pozo.

**5. La acidulación no se puede llevar al 100 %, y el ácido "gratis" no existe.**
Neutralizar el 100 % de la alcalinidad deja el agua a **pH 3,2–3,6 de forma estable** (medido en 7 aguas, UF/IFAS SL142 Tabla 5) **[V]**. El objetivo es 80–90 %, pH 4,5–5,0. Y el anión del ácido entra en la receta: con nítrico al 60 %, neutralizar 3,7 meq/L aporta **51,7 g N/m³ = 20,7 kg N/ha en un riego de 40 mm** **[C]**. Con fosfórico, **114 g P/m³ = 45 kg P/ha** **[C]**: la receta explota. **El ácido no es un aditivo neutro; es un fertilizante que se está aplicando sin haberlo planeado.**

**6. Bajar el pH no mata la biopelícula, y clorar en agua alcalina es tirar plata.**
Son dos tratamientos distintos para dos problemas distintos (§5.1). Y están acoplados en un solo sentido: a **pH 8 solo el 25 %** del cloro es ácido hipocloroso, contra **≥ 75 % a pH 7** **[V]** (UC ANR). *"La cloración es relativamente inefectiva para el control bacteriano si el pH del agua está por encima de 7,5"* **[V]** (VCE 442-757). Pero al revés no vale: acidular a pH 5 **no desinfecta**. Y **mezclar los dos en el mismo tanque produce gas cloro** **[V]**.

**7. El tanque de derivación no puede dosificar proporcionalmente. Nunca.**
*"Una vez que la fracción sólida se disuelve completamente, la concentración del fertilizante se reduce a una tasa exponencial. En la práctica, cuando haya pasado a través del tanque un volumen equivalente a cuatro tanques, sólo quedan cantidades ínfimas dentro de éste."* **[V]** (Kafkafi & Tarchitzky 2011). No es un problema de calibración: es la física del equipo. Si el requisito es concentración constante, el equipo es otro.

**8. El fertirriego no elimina la volatilización de la urea; la reubica al borde del bulbo.**
*"La urea fertirrigada que alcanza los bordes del bulbo húmedo se vuelve susceptible a la volatilización. La evaporación de la superficie del suelo resulta en un aumento de la concentración de urea cerca de la superficie."* **[V]** (Kafkafi & Tarchitzky 2011, §4.2.1). La única forma segura de no volatilizar urea es **ponerla debajo de la superficie**: colocación profunda **−55 %** sobre 824 observaciones globales (Pan et al. 2016) **[V-res]**; **12,5 % → 1,1 %** en maíz de siembra directa en Paraná (Fontoura & Bayer 2010) **[V]**. Eso es el §8, no el §6.

**8b. Ningún coeficiente de volatilización es una constante — y quien lo use como tal se va a equivocar por un factor de 20.**
Mismo lote, mismo fertilizante, misma dosis, mismo cultivo, cuatro campañas seguidas: **1,3 % · 25,4 % · 20,1 % · 3,0 %** de pérdida por urea superficial (Fontoura & Bayer 2010) **[V]**. Entre sitios el rango va de **0,1–4,0 %** (maíz irrigado, semiárido EE.UU.) a **38–78 %** (tropical irrigado, Brasil) **[V-secundaria]**. Lo que sí transfiere: la **dirección** (incorporar reduce ~10×) y la **ventana** (**> 90 % de la pérdida en los primeros 3 días**, Viero et al. 2015 **[V]**).

**8c. Regar antes de fertilizar no sirve. Regar después, sí.**
Medido en maíz de siembra directa de 28 años, RS Brasil: **regar después de aplicar redujo la pérdida 67 %** con urea; **regar antes no la redujo** (Viero et al. 2015) **[V]**. Es gratis y casi nadie lo hace en el orden correcto.

**9. Un enjuague largo después de inyectar nitrato lixivia lo que se acaba de aplicar.**
El nitrato viaja al borde del bulbo mientras el amonio se queda pegado bajo el gotero **[V]**; por eso el enjuague *"debería ser lo más corto posible luego de que haya terminado la inyección de nitratos, para evitar las pérdidas potenciales de nitratos desde la zona de raíces"* **[V]**. "Terminar con agua limpia" **no significa** "regar mucho al final".

**10. La eficiencia del P al voleo no es del 10–25 %. Ese número es un artefacto del método de medición.**
*"La eficiencia del uso del P de fertilizante es a menudo alta (hasta 90 por ciento) cuando se evalúa en una escala de tiempo adecuada usando el método de balance."* **[V]** (Syers, Johnston & Curtin 2008, FAO Bulletin 18). El mismo ensayo de Broadbalk da **2–5 %** por diferencia sin N y **50–52 %** por balance con N **[V]**. Vender fertirriego contra el 10–25 % del método de la diferencia es **vender contra un número que la FAO considera mal calculado**. El argumento honesto en P es sincronía y colocación en el año, no recuperación de P perdido.

**10b. En un suelo por encima del valor crítico de P, la eficiencia del P aplicado es cero — y no hay manejo que la suba.**
Agdell, Olsen P 59 mg/kg: recuperación por diferencia de **0 % en papa y 0 % en remolacha** **[V]** (FAO Bull. 18, Tabla 6). No es que el P se pierda: **no hacía falta**. Antes de vender un servicio de eficiencia de P hay que mirar el análisis de suelo; si está sobre el valor crítico, el servicio correcto es *no aplicar*.

**10c. El "ahorro" de la banda puede ser minería de suelo, no eficiencia.**
FAO Bull. 18 (p. 52) advierte que una dosis menor colocada puede dar **la misma eficiencia de uso** que una dosis mayor al voleo, pero **deja menos P residual**, con lo que las reservas de P disponible se acumulan más lentamente **[V]**. Y declara que la comparación sistemática banda vs. voleo **todavía no está hecha** **[V]**. **El factor "2:1 voleo:banda" no tiene respaldo publicado verificable** (§8.5). Lo que sí está medido es la ganancia de rendimiento: **+14 a +27 %** con colocación > 10 cm (Nkebiwe et al. 2016) **[V-res]** y **+5,2 %** con arrancador subsuperficial en maíz (Quinn et al. 2020) **[V-res]**.

**11b. El grueso del beneficio del fertirriego es fertilizante que no se pierde, no grano que aparece.**
En el meta-análisis de referencia, la NUE sube **+34,3 %** pero el rendimiento sólo **+12,0 %** (Li et al. 2021) **[V-res]**. Prometer un salto de rendimiento proporcional a la mejora de eficiencia es prometer casi el triple de lo que la evidencia sostiene. Y todo ese meta-análisis es **de China**, contra una *"práctica tradicional"* cuya calidad no es la del campo del cliente: **cuanto mejor sea la referencia, menor la ganancia.**

**11. Los umbrales de FAO 29 no aplican al goteo tal como están escritos.**
Textual: las guías *"son demasiado restrictivas para métodos de riego especializados, como el goteo localizado"* **[V]**, y asumen LF ≥ 15 %, clima semiárido y riego infrecuente. Un informe que aplique la Tabla 1 de FAO 29 a un sistema de goteo diario sin declarar esta salvedad está usando la fuente fuera de su dominio declarado. **Y los umbrales de boro son del agua del suelo, no del agua de riego** **[V]**.

**12. Un análisis de agua sin CE no permite leer el SAR, y un SAR sin CE no dice nada sobre infiltración.**
*"A un SAR dado, la tasa de infiltración aumenta al aumentar la salinidad del agua"* **[V]** (FAO 29, nota 3, según Rhoades 1977 y Oster & Schroer 1979). SAR 8 con CEw 2,0 = sin restricción; SAR 8 con CEw 0,4 = severo. **Es la misma agua en la planilla y dos suelos distintos en el campo.**

**13. El diseño de la receta no sobrevive a un tanque mal armado.**
El balance de cargas se cumple en la planilla y se rompe en el fondo del tanque: Ca + fosfato precipita, Ca + sulfato da yeso **[V]**, y la incompatibilidad aparece recién **por encima de ~10× de concentración** **[V]**. El K₂SO₄ satura a **9 g/100 g a 10 °C** **[V]**: un tanque formulado a 20 °C cristaliza de noche. La prueba de jarra a concentración y temperatura reales **no es opcional** **[V]**.

---

## FUENTES PRIMARIAS CONSULTADAS Y ABIERTAS

**Institucionales / normativas**
1. **Ayers, R.S. & Westcot, D.W. (1985; Rev.1 1994).** *Water Quality for Agriculture.* FAO Irrigation and Drainage Paper 29 Rev.1. FAO, Roma. — https://www.fao.org/4/t0234e/t0234e00.htm — *(Caps. 1, 3, 4, 5 leídos: Tabla 1, Tabla 2, supuestos, ec. 7 y 9, adj R_Na, Tablas 16 y 17)*
2. **Syers, J.K., Johnston, A.E. & Curtin, D. (2008).** *Efficiency of soil and fertilizer phosphorus use.* FAO Fertilizer and Plant Nutrition Bulletin 18. FAO, Roma. — https://www.fao.org/4/a1595e/a1595e00.pdf
3. **Kafkafi, U. & Tarchitzky, J. (2011/2012).** *Fertirrigación. Una herramienta para una eficiente fertilización y manejo del agua.* IFA / IPI, París. — https://www.fertilizer.org/wp-content/uploads/2023/01/2012_ifa_fertigation_spanish.pdf
4. **Eurofins Agro, AkzoNobel, Geerten van der Lugt, NMI, SQM & Yara (2016).** *Nutrient Solutions for Greenhouse Crops.* — https://cdnmedia.eurofins.com/corporate-eurofins/media/12142795/160825_manual_nutrient_solutions_digital_en.pdf — *(base metodológica: Bemestingsadviesbasis Substraten, Proefstation Naaldwijk, 1999)*

**Extensión universitaria**
5. **UF/IFAS EDIS SL142** — *Neutralizing Excess Bicarbonates from Irrigation Water.* — mirror leído: https://irrigationtoolbox.com/ReferenceDocuments/Extension/Florida/SS16500.pdf
6. **Shortridge, J. & Benham, B. (2023).** *[Micro-irrigation filtration and treatment].* Virginia Cooperative Extension **442-757 (BSE-222P)**. — https://www.pubs.ext.vt.edu/content/pubs_ext_vt_edu/en/442/442-757/442-757.html
7. **Jatana, B.S. & Sanders, T.G. III (2024).** *Micro-Irrigation System Maintenance to Prevent Clogging.* Clemson Land-Grant Press **LGP 1190**. — https://lgpress.clemson.edu/publication/micro-irrigation-system-maintenance-to-prevent-clogging/
8. **UC ANR** — *Maintenance of Microirrigation Systems*: "Chlorination for biological clogging problems" y "Chemical precipitation". — https://ucanr.edu/site/maintenance-microirrigation-systems
9. **Landschoot, P. (act. 2025).** *Irrigation Water Quality Guidelines for Turfgrass Sites.* Penn State Extension. — https://extension.psu.edu/irrigation-water-quality-guidelines-for-turfgrass-sites — *(citando Duncan, Carrow & Huck 2000, USGA Green Section Record sep–oct: 14–24)*

**Revisadas por pares — DOI verificado en Crossref / OpenAlex**

*Taponamiento y calidad de agua*
10. **Bucks, D.A., Nakayama, F.S. & Gilbert, R.G. (1979).** *Trickle irrigation water quality and preventive maintenance.* Agricultural Water Management 2(2): 149–162. **DOI: 10.1016/0378-3774(79)90028-3** ✔
11. **Nakayama, F.S. & Bucks, D.A. (1991).** *Water quality in drip/trickle irrigation: A review.* Irrigation Science 12(4). **DOI: 10.1007/BF00190522** ✔
12. **Suarez, D.L. (1981).** *Relation Between pHc and Sodium Adsorption Ratio (SAR) and an Alternative Method of Estimating SAR of Soil or Drainage Waters.* Soil Science Society of America Journal 45: 469–475. **DOI: 10.2136/sssaj1981.03615995004500030005x** ✔ — *base del adj R_Na de FAO 29 Rev.1*

*Eficiencia y meta-análisis de fertirriego* — **[V-res]**, texto completo no accesible
13. **Li, H., Mei, X., Wang, J., Huang, F., Hao, W. & Li, B. (2021).** Agricultural Water Management 244: 106534. **DOI: 10.1016/j.agwat.2020.106534** ✔
14. **Zhu, Zhang, Li, Zhu & Kang (2023).** Nutrient Cycling in Agroecosystems 127(3): 359–373. **DOI: 10.1007/s10705-023-10318-5** ✔
15. **Zheng, Zhou & Zhu (2023).** Science of the Total Environment 886: 163804. **DOI: 10.1016/j.scitotenv.2023.163804** ✔
16. **Yang, X., Zhang, L. & Liu, X. (2024).** Scientia Horticulturae 338: 113653. **DOI: 10.1016/j.scienta.2024.113653** ✔

*Volatilización de NH₃ y colocación*
17. **Pan, B., Lam, S.K., Mosier, A., Luo, Y. & Chen, D. (2016).** *Ammonia volatilization from synthetic fertilizers and its mitigation strategies: A global synthesis.* Agriculture, Ecosystems & Environment 232: 283–289. **DOI: 10.1016/j.agee.2016.08.019** ✔ **[V-res]**
18. **Fontoura, S.M.V. & Bayer, C. (2010).** Revista Brasileira de Ciência do Solo 34(5): 1677–1684. **DOI: 10.1590/s0100-06832010000500020** ✔ **[V, texto completo]**
19. **Viero, F., Bayer, C., Vieira, R.C.B. & Carniel, E. (2015).** Revista Brasileira de Ciência do Solo 39(6): 1737–1743. **DOI: 10.1590/01000683rbcs20150132** ✔ **[V, texto completo]**
20. **Cancellier, E.L. et al. (2016).** Ciência e Agrotecnologia 40(2): 133–144. **DOI: 10.1590/1413-70542016402031115** ✔ **[V, texto completo]**
21. **Nkebiwe, P.M., Weinmann, M., Bar-Tal, A. & Müller, T. (2016).** *Fertilizer placement to improve crop nutrient acquisition and yield: A review and meta-analysis.* Field Crops Research 196: 389–401. **DOI: 10.1016/j.fcr.2016.07.018** ✔ **[V-res]**
22. **Quinn, D., Lee, C. & Poffenbarger, H. (2020).** Field Crops Research 254: 107834. **DOI: 10.1016/j.fcr.2020.107834** ✔ **[V-res]**
23. **Barber, S.A. (1958).** Agronomy Journal 50: 535–539. **DOI: 10.2134/agronj1958.00021962005000090011x** ✔ *(clásico de P en línea; contenido no leído)*
24. **Barber, S.A. (1959).** Agronomy Journal 51: 97–99. **DOI: 10.2134/agronj1959.00021962005100020011x** ✔ *(clásico de K en línea; contenido no leído)*
25. **Welch, L.F. et al. (1966).** *Relative Efficiency of Broadcast Versus Banded Phosphorus for Corn.* Agronomy Journal 58: 283–287. **DOI: 10.2134/agronj1966.00021962005800030011x** ✔ *(contenido no leído)*
26. **Buah, S.S.J., Polito, T.A. & Killorn, R. (2000).** Agronomy Journal 92: 657–662. **DOI: 10.2134/agronj2000.924657x** ✔ *(contenido no leído)*
27. **Howard, D.D., Essington, M.E. & Logan, J. (2002).** Agronomy Journal 94: 51. **DOI: 10.2134/agronj2002.0051** ✔ *(contenido no leído)*

*Bulbo húmedo y transporte de solutos*
28. **El-Nesr, M.N., Alazba, A.A. & Šimůnek, J. (2014).** Irrigation Science 32(2): 111–125. **[V, texto completo — pero es SIMULACIÓN HYDRUS-2D]**
29. **Mmolawa, K. & Or, D. (2000).** *Root zone solute dynamics under drip irrigation: A review.* Plant and Soil 222: 163–190. **DOI: 10.1023/A:1004756832038** ✔ *(contenido no accesible)*
30. **Hanson, B.R., Šimůnek, J. & Hopmans, J.W. (2006).** Agricultural Water Management 86: 102–113. **DOI: 10.1016/j.agwat.2006.06.013** ✔ *(contenido no accesible — referencia clave pendiente)*

**Libros y fuentes clásicas (citados, no abiertos en esta sesión)**
31. **Sonneveld, C. & Voogt, W. (2009).** *Plant Nutrition of Greenhouse Crops.* Springer, Dordrecht. **DOI: 10.1007/978-90-481-2532-6** ✔ · ISBN 978-90-481-2531-9.
32. **Rhoades, J.D. (1974); Rhoades & Merrill (1976).** Ecuación de requerimiento de lavado, FAO 29 ec. (9).
33. **Maas, E.V. (1984).** Base de la Tabla 16 de tolerancia al boro de FAO 29.
34. **Mattingly, G.E.G. & Widdowson, F.V. (1958, 1959).** *Plant and Soil* 9:286–304 y 10:161–175. Recuperación de ³²P, colocado vs. voleo. *(Leídos a través de FAO Bulletin 18; primarios no abiertos.)*

**Extensión adicional**
35. **Manitoba Agriculture (jun. 2023).** *Volatilization of Surface Applied Urea/UAN.* — https://www.gov.mb.ca/agriculture/crops/seasonal-reports/pubs/volatilization-surface-applied-urea.pdf — *PDF leído; la tabla de cifras no cita el trabajo primario.*

**Literatura de fabricante (identificada como tal)**
36. **Netafim USA.** *Recommendations for the Treatment of Drip Irrigation Systems with Acid.* — https://www.netafimusa.com/globalassets/treatment-with-acid.pdf

**Técnica divulgativa (no revisada por pares)**
37. **Intagri.** *La Compatibilidad de los Fertilizantes en Fertirrigación.* — https://www.intagri.com/articulos/nutricion-vegetal/la-compatibilidad-de-los-fertilizantes-en-fertirrigacion

---

### Nota final sobre el alcance de esta investigación

Se agotó el presupuesto de búsqueda web de la sesión (200/200 consultas); el resto del trabajo se hizo con las **APIs de Crossref y OpenAlex** para verificación de DOI y con **descarga directa de PDF**. Quedaron inaccesibles: ScienceDirect, MDPI, PMC (CAPTCHA — no se resolvió), Springer y Nature (redirigen a autenticación). Eso sesgó la cobertura hacia **FAO, extensión universitaria de EE.UU. y acceso abierto latinoamericano (SciELO)** — que es exactamente por qué los §1, §3, §5, §7.2 y §8.2 quedaron sólidos, y por qué el §7.4 (potasio) y las distancias medidas del §6.4 quedaron vacíos.

**Ningún hueco se rellenó con estimaciones.** Los 26 renglones del §9 son el trabajo pendiente, no una formalidad.
