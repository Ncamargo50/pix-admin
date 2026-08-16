# R4 — Fisiología de la absorción y transporte de nutrientes

**Dossier de investigación verificado**
Propósito: decidir si un fertilizante puede hacer lo que promete.
Fecha: 2026-08-16 · Agente: fisiología vegetal / nutrición mineral

---

## Cómo leer este documento

Cada afirmación cuantitativa lleva su fuente. La verificación está graduada en tres niveles y el nivel está declarado:

| Marca | Significado |
|---|---|
| **[TP]** | **Texto primario leído.** Abrí el documento y el número está en él. |
| **[MD]** | **Metadato verificado.** DOI/cita confirmados en Crossref o Europe PMC, pero **no** pude abrir el texto completo. El número, si lo doy, viene de una fuente secundaria. |
| **[NV]** | **No verificado.** Listado en la sección final. **No usar frente a un cliente.** |

Regla operativa del dossier: **donde el mecanismo está en disputa en la literatura, digo que está en disputa.** No cierro lo que la literatura no cerró.

> **Dossiers hermanos.** `R2b_quelato_foliar_limites.md` cubre penetración cuticular, POD y el límite del foliar de Fe. **Lo crucé con este dossier**: no hay contradicción de fondo, este cierra parcialmente uno de sus puntos abiertos, y el cruce detectó un DOI equivocado. Ver §5.7 (*Concordancia y diferencia con R2b*) y §9.2.
>
> **Cobertura de la §7:** 6 cultivos con ventana fenológica verificada, 1 parcial, **2 sin dato (café sin ventana, papa sin nada)**. Declarado en §9.1b.
>
> **Nota de método.** La sesión agotó su presupuesto de búsqueda web a mitad del trabajo. La segunda mitad se hizo con WebFetch directo, la API de Crossref y la API REST de Europe PMC. Varios dominios (Springer, Taylor & Francis, ScienceDirect, ASHS, Wiley) devolvieron 403 o redirección a portal de identidad. Eso, y no otra cosa, explica cada hueco marcado [MD] o [NV].

---

# 1. Llegada del nutriente a la raíz

La raíz no "busca" el nutriente. El nutriente llega por tres vías, y **cuál domina define si el fertilizante responde a la colocación o no.**

| Vía | Motor físico | De qué depende |
|---|---|---|
| **Flujo masal** (*mass flow*) | Transpiración: el agua se mueve a la raíz y arrastra el soluto disuelto | Concentración en la solución del suelo × volumen transpirado |
| **Difusión** | Gradiente de concentración creado por la propia absorción, que vacía la zona junto a la raíz | Coeficiente de difusión efectivo, tortuosidad, contenido de agua |
| **Intercepción radicular** | La raíz crece y físicamente encuentra el nutriente | Volumen de suelo explorado (≈ 1 % del total) |

## 1.1 La tabla de Barber para maíz

Fuente original del concepto: **Barber, S.A. (1966).** *The role of root interception, mass-flow and diffusion in regulating the uptake of ions by plants from soil.* En: *Limiting steps in ion uptake by plants from soil*, Technical Reports Series No. 65, pp. 39–45. IAEA, Viena. **[TP — registro IAEA/INIS abierto y leído]**
Registro: https://inis.iaea.org/records/25hvn-hyj66
El estudio usó ⁸⁶Rb como trazador, maíz y soya, y varios tipos de suelo; contiene 4 figuras y 3 tablas.

La tabla numérica que circula universalmente proviene de la obra posterior: **Barber, S.A. (1984/1995).** *Soil Nutrient Bioavailability: A Mechanistic Approach.* John Wiley & Sons, Nueva York. **[MD — cita confirmada; no pude abrir la tabla primaria]**

Valores tal como se reproducen en fuentes secundarias, maíz, **kg/ha**:

| Nutriente | Absorción total | Intercepción | Flujo masal | Difusión |
|---|---|---|---|---|
| Calcio | 23 | 66 | 175 | — |
| Magnesio | 28 | 16 | 105 | — |
| Potasio | 135 | 4 | 35 | 96 |
| Fósforo | 39 | 1 | 2 | 36 |

⚠️ **Advertencia de precisión.** Estos valores **cambian entre ediciones y entre rendimientos supuestos**. No pude abrir la tabla primaria (spectrumanalytic 404; UF/IFAS bloqueado por política de red; Pioneer publica la tabla como imagen). **No cites estos números exactos a un cliente.** Ver [NV].

**Lo que sí es robusto** y no depende de la edición — es la conclusión que importa:

| Nutriente | Vía dominante | Magnitud aproximada |
|---|---|---|
| **N (nitrato)** | **Flujo masal** | La gran mayoría |
| **P** | **Difusión** | >90 % |
| **K** | **Difusión** | ~70–80 % |
| **Ca, Mg** | **Flujo masal** | El flujo masal **excede** la demanda |
| **S (sulfato)** | Flujo masal | Mayoría |

## 1.2 Por qué el P y el K responden a la colocación y el N no

Ésta es la consecuencia de decisión, y se lee directo de la tabla:

**Fósforo — difusión pura.** El flujo masal aporta ~2 de 39 kg/ha. El resto tiene que difundir. La difusión del fosfato en suelo es **lentísima** (coeficiente de difusión efectivo del orden de 10⁻¹²–10⁻¹³ m² s⁻¹ **[NV]** — orden de magnitud citado sin fuente primaria abierta) porque el fosfato se adsorbe a óxidos de Fe/Al y arcillas. La distancia que recorre un ion fosfato en una estación de crecimiento es de **milímetros**. Consecuencia: **el fosfato tiene que estar puesto donde la raíz va a estar.** De ahí que el P responda a la localización en banda, al arrancador, y a la proximidad a la semilla.

**Potasio — difusión también**, aunque menos extrema que el P, y con la complicación de que el K se intercambia con la fase sólida. Distancia de difusión: del orden de centímetros. Responde a la colocación, pero menos que el P.

**Nitrógeno (nitrato) — flujo masal.** El nitrato no se adsorbe (el suelo agrícola tiene carga neta negativa; el NO₃⁻ es un anión). Viaja con el agua. Consecuencia doble:
- **No responde a la colocación**: al voleo llega igual, porque el agua lo lleva.
- **Se lixivia**: la misma propiedad que lo hace disponible lo hace perdible. La colocación no lo protege; el **momento** sí.

**Calcio y magnesio — el flujo masal aporta más de lo que la planta necesita** (175 vs 23 para Ca; 105 vs 28 para Mg en la tabla de arriba). Consecuencia contraintuitiva pero central:

> **Si el flujo masal ya entrega 4–7× la demanda de Ca, una deficiencia de Ca en un órgano NO es un problema de suministro del suelo.** Es un problema de *transporte dentro de la planta* (ver §4 y §5.7). Agregar Ca al suelo no lo arregla. Este es el error de formulación más caro que existe en nutrición de Ca.

---

# 2. Absorción radicular: cinética y transportadores

## 2.1 El modelo de doble mecanismo

**Epstein, E. (1953).** Mechanism of ion absorption by roots. *Nature* 171:83–84. DOI **10.1038/171083a0** **[MD]**

**Epstein, E., Rains, D.W. & Elzam, O.E. (1963).** Resolution of dual mechanisms of potassium absorption by barley roots. *PNAS* 49(3):684–692. DOI **10.1073/pnas.49.5.684** **[MD]**

El hallazgo, que sigue siendo el marco vigente: la absorción de un ion por la raíz **no es una sola curva de saturación**, sino **dos sistemas superpuestos**:

- **Mecanismo 1 / HATS (High-Affinity Transport System)** — opera en el rango **micromolar**, satura, tiene Km baja. Es un transportador activo, acoplado a protones.
- **Mecanismo 2 / LATS (Low-Affinity Transport System)** — opera en el rango **milimolar**, Km alta, a menudo casi lineal (no saturante en el rango fisiológico). Frecuentemente son canales.

La ecuación es Michaelis-Menten:

```
v = Vmax · [S] / (Km + [S])
```

donde `v` = velocidad de influjo, `[S]` = concentración externa, `Km` = concentración a la que `v = Vmax/2` (**menor Km = mayor afinidad**), `Vmax` = velocidad máxima.

## 2.2 Valores de Km por nutriente

⚠️ **Lo que pude verificar es poco, y lo digo.**

| Nutriente | Sistema | Km verificada | Fuente / nivel |
|---|---|---|---|
| **NH₄⁺** | HATS (AMT1.5, Arabidopsis) | **~5 µM** | Rivero-Marcos 2025 **[TP]** |
| **NO₃⁻** | HATS (familia NRT2) | *"concentraciones micromolares"* — **sin valor numérico en la fuente** | Rivero-Marcos 2025 **[TP]** |
| **NO₃⁻** | LATS (NRT1.1/NPF6.3) | *"concentraciones milimolares"* — **sin valor numérico** | Rivero-Marcos 2025 **[TP]** |
| **K⁺** | Mec. 1 (µM) vs Mec. 2 (mM) | Dualidad verificada; **valores de Km no leídos del primario** | Epstein et al. 1963 **[MD]** |
| **H₂PO₄⁻** | HATS (PHT1) | — | **[NV]** |
| **Ca²⁺, Mg²⁺, SO₄²⁻, micros** | — | — | **[NV]** |

**Fuente:** Rivero-Marcos, M. (2025). Functional crosstalk between nitrate and ammonium transporters in N acquisition and pH homeostasis. *Frontiers in Plant Science* 16:1634119. DOI **10.3389/fpls.2025.1634119** **[TP]**

Dato de contexto de esa misma fuente **[TP]**: *"las concentraciones de NH₄⁺ en la mayoría de los suelos de cultivo van típicamente de 20 a 200 µM."*

> **Aritmética que importa:** si la Km del HATS de amonio es ~5 µM y el suelo tiene 20–200 µM, **el HATS está saturado en campo**. En condiciones agrícolas normales quien manda es el LATS, no el HATS. La afinidad alta importa en suelos pobres, no en un lote fertilizado. Un producto que promete "mejorar la afinidad de absorción" está prometiendo algo irrelevante en el rango de concentración donde opera un cultivo fertilizado.

⚠️ **Los valores de Km que circulan en literatura comercial** (K⁺ HATS ≈ 20–30 µM, NO₃⁻ HATS ≈ 10–100 µM, fosfato ≈ 3–10 µM) **no los pude respaldar contra texto primario en esta sesión.** Ver [NV]. Son plausibles y ampliamente citados, pero *plausible y ampliamente citado* no es *verificado*.

## 2.3 Activa vs pasiva

| Modo | Cuándo | Ejemplos |
|---|---|---|
| **Activa (secundaria)** | El ion entra **contra** su gradiente electroquímico. Cotransporte con H⁺, financiado por la H⁺-ATPasa de membrana plasmática (AHA), que consume ATP para bombear H⁺ afuera y crear el gradiente | NO₃⁻/H⁺, H₂PO₄⁻/H⁺, SO₄²⁻/H⁺, K⁺ vía HAK5 |
| **Pasiva (canales)** | A favor del gradiente electroquímico. El interior celular es electronegativo (−120 a −200 mV), así que **los cationes entran pasivamente** aunque su concentración interna sea mayor | K⁺ vía AKT1, Ca²⁺ vía canales, NH₄⁺ vía AMT |

**Punto en discusión — y relevante.** La suposición clásica de que la absorción de NH₄⁺ es cara en energía **está siendo cuestionada**. Xie et al. 2025 **[TP]** recogen hallazgos recientes de que *"el NH₄⁺ que entra a las células… es una vía de transporte pasivo, que no consume energía"*, lo que contradice el argumento tradicional del "ciclado fútil" como causa de la toxicidad amoniacal.

> **Consecuencia comercial:** el argumento de venta "el amonio ahorra energía a la planta porque no hay que reducir el nitrato" es **parcialmente cierto** (la reducción de NO₃⁻ a NH₄⁺ sí cuesta poder reductor) pero la contabilidad completa está en disputa. No es una base sólida para prometer rendimiento.

---

# 3. NH₄⁺ vs NO₃⁻ — la palanca real de formulación

Ésta **sí** es una palanca de formulación con mecanismo físico duro. Y tiene un techo.

## 3.1 El mecanismo: balance de cargas

La raíz debe mantener neutralidad eléctrica. Si absorbe más cationes que aniones, **expulsa H⁺**. Si absorbe más aniones que cationes, **expulsa OH⁻/HCO₃⁻**.

| Fuente de N | Qué absorbe | Qué expulsa | Efecto en rizósfera |
|---|---|---|---|
| **NH₄⁺** | Catión | **H⁺** | **ACIDIFICA** |
| **NO₃⁻** | Anión | **OH⁻ / HCO₃⁻** | **ALCALINIZA** |

Como el N es, por lejos, el nutriente absorbido en mayor cantidad, **la forma de N domina el balance catión/anión de toda la planta.** Por eso es una palanca y no un detalle.

Mecanismo molecular **[TP, Rivero-Marcos 2025]**:
> *"El exceso de absorción de NH₄⁺ mediado por AMTs conduce a una acidificación considerable del pH apoplástico, lo que causa desequilibrios iónicos."* La absorción de NH₄⁺ **despolariza el potencial de membrana**, lo que a su vez **aumenta el eflujo neto de H⁺**, mediado principalmente por la H⁺-ATPasa **AHA2**.

En el otro sentido: *"el consumo de H⁺ durante la reducción de NO₃⁻ a nitrito y NH₄⁺ aumenta el pH citosólico."*

**Referencia canónica del fenómeno en suelo:** Hinsinger, P., Plassard, C., Tang, C. & Jaillard, B. (2003). Origins of root-mediated pH changes in the rhizosphere and their responses to environmental constraints: A review. *Plant and Soil* 248:43–59. DOI **10.1023/A:1022371130939** **[MD — DOI verificado en Crossref; Springer devolvió 303 al portal de identidad, texto no leído]**

## 3.2 Magnitud del cambio de pH

| Contexto | Magnitud medida | Fuente / nivel |
|---|---|---|
| Arándano *highbush*, NH₄⁺ vs basal | **−0,75 unidades de pH** | ASHS *HortScience* 54(5):955 **[NV — el sitio devolvió 403; magnitud vista solo en extracto de buscador]** |
| Arroz en solución, 2 días con NH₄⁺ | pH 4,5 → 3,5 (**−1,0 unidad**) | **[NV — extracto de buscador]** |
| Desviación rizósfera vs suelo masal, caso general | **hasta ~2 unidades** | Hinsinger et al. 2003 **[MD]** |

⚠️ **Ninguna de las tres magnitudes está en nivel [TP].** Lo que **sí** está verificado en texto primario es la **dirección** del efecto y su **mecanismo**. Si necesitás un número defendible para un cliente, hay que conseguir el texto de Hinsinger.

## 3.3 Consecuencias sobre disponibilidad de P y micronutrientes

La acidificación de rizósfera es el mecanismo por el cual el N amoniacal **moviliza P y micros**, y es la base física del "efecto arrancador" del fosfato de amonio:

| Elemento | Efecto de bajar el pH de rizósfera |
|---|---|
| **P** | En suelos alcalinos/calcáreos, disuelve fosfatos de Ca. **Gana disponibilidad.** En suelos muy ácidos, el efecto se invierte: más Al/Fe solubles → **más fijación de P.** |
| **Fe, Mn, Zn, Cu** | Solubilidad de los cationes metálicos **sube fuertemente** al bajar el pH (aprox. 100× por unidad de pH para metales divalentes; 1000× para Fe³⁺ **[NV]**). Es la razón por la que el amonio ayuda contra la clorosis férrica en suelo calcáreo. |
| **Mo** | **Se mueve al revés**: el molibdato gana disponibilidad al **subir** el pH. El amonio lo **empeora**. |
| **Ca, Mg** | Se desplazan del complejo de intercambio → más en solución, más lixiviables. |

Efecto colateral documentado **[MD]**: la acidificación por NH₄⁺ **reduce la acumulación de Mn en arroz** por regulación a la baja del transportador *OsNramp5* — evidencia de que el efecto sobre micros no es solo químico de suelo, sino también de expresión de transportadores. (PMC6785973)

## 3.4 El límite práctico: cuánto N amoniacal antes de toxicidad

**Fuente principal:** Xie, L.-B., Sun, L.-N., Zhang, Z.-W., Chen, Y.-E., Yuan, M. & Yuan, S. (2025). Phenotype Assessment and Putative Mechanisms of Ammonium Toxicity to Plants. *International Journal of Molecular Sciences* 26(6):2606. DOI **10.3390/ijms26062606** **[TP]**

### Umbrales por concentración (no por porcentaje)

| Órgano / efecto | Rango de NH₄⁺ que lo produce |
|---|---|
| Inhibición de elongación de raíz primaria | **5–30 mM** |
| Alteración de raíces laterales, caída de relación raíz/tallo | **5–80 mM** |
| Inhibición de crecimiento de tallo | **10–50 mM** |
| Clorosis foliar | **20–60 mM** |
| Caída de biomasa y rendimiento (flores/semillas) | **5–20 mM** |
| Muerte de la planta en especies sensibles | **>1 mM** |

Y el dato de rescate **[TP]**: *"tan poco como 0,1 mM"* de nitrato contrarresta la toxicidad de *"5–10 mM NH₄⁺"*. **Una traza de nitrato compra mucha tolerancia.**

### Umbrales por porcentaje de N amoniacal

⚠️ **Xie et al. 2025 NO dan porcentajes.** Textualmente: *el documento no provee porcentajes explícitos de amonio como fracción del N total que distingan seguro de tóxico.* Trabajan en concentraciones, no en ratios.

La regla de porcentajes que usa la industria tiene **una sola fuente primaria trazable**, y conviene saber cuál es:

**Saloner, A. & Bernstein, N. (2022).** Nitrogen source matters: High NH₄/NO₃ ratio reduces cannabinoids, terpenoids, and yield in medical cannabis. *Frontiers in Plant Science* 13:830224. DOI **10.3389/fpls.2022.830224** **[TP]**

Diseño: cinco niveles — **0 %, 10 %, 30 %, 50 % y 100 % de N-NH₄⁺**, con el resto como NO₃⁻ y **N total constante en 200 mg L⁻¹**.

| Nivel de NH₄ | Resultado medido | Nivel |
|---|---|---|
| **10–30 %** | *"Niveles moderados de 10–30 % NH₄ son adecuados para el cultivo de cannabis medicinal, ya que no dañan la función de la planta y muestran solo poca influencia adversa sobre el rendimiento"* | **[TP]** |
| **50 %** | Aparecen síntomas adversos, con **≈40 % de mortalidad de plantas** al final del experimento | **[TP]** |
| **100 %** | *"indujo daño sustancial a la planta, resultando en muerte de la planta"* | **[TP]** |

Y la confirmación del mecanismo de §3.1 en el mismo ensayo **[TP]**: *"el pH de la solución de lixiviado fue significativamente MÁS ALTO que el pH de la solución de riego bajo 0 % NH₄, y MÁS BAJO que el pH de la solución de riego bajo 100 % NH₄"* — acidificación con amonio, alcalinización con nitrato, medido.

> ⚠️ **La advertencia que la industria omite: la regla "10–30 %" está enunciada por sus autores PARA CANNABIS MEDICINAL EN SUSTRATO, no como regla universal de cultivo.** Se la cita rutinariamente como si fuera un umbral general. **No lo es.** Es un dato sólido de una especie, en maceta, con N total fijo en 200 mg/L. Extrapolarla a un maíz a campo, a un arroz inundado (que tolera NH₄⁺ como forma principal) o a un arándano (que lo prefiere) **no está respaldado por esta fuente ni por ninguna otra que haya podido abrir**.
>
> **Lo que sí se puede afirmar con base [TP]:** que la respuesta al % de NH₄ es **fuertemente no lineal** — entre 30 % y 50 % se pasa de "poco efecto adverso" a **40 % de mortalidad**. El acantilado es real y está cerca. Ver también §3.4 *Sensibilidad por especie*: la cebada es explícitamente sensible, el arroz inundado y las ericáceas tolerantes. **El umbral es específico de especie y el diseño de la formulación tiene que declarar para cuál.**

### Sensibilidad por especie

| Grupo | Comportamiento | Nivel |
|---|---|---|
| **Tolerantes** | Arroz inundado (absorbe NH₄⁺ como forma principal; el suelo anegado no nitrifica), arándano y ericáceas (adaptadas a suelos ácidos, prefieren NH₄⁺) | **[TP parcial — arándano en ASHS 2019; arroz en Xie 2025]** |
| **Sensibles** | **Cebada** — explícitamente señalada, con *"eflujo significativo de NH₄⁺"* y *"ciclado fútil"* | Xie 2025 **[TP]** |
| **Variables, sin ranking cuantificado** | Lechuga, tomate, pepino, trigo, colza | Xie 2025 **[TP]** |
| **Diferencias intraespecíficas** | Cultivares de arroz Kas vs Kos difieren, ligado a biosíntesis de auxinas | Xie 2025 **[TP]** |

### Efecto de la temperatura

⚠️ **Xie et al. 2025 no lo tratan.** Verbatim del análisis: *el documento no discute cómo la temperatura influye en la severidad o los mecanismos de la toxicidad amoniacal.*

La regla práctica de que **el amonio es más riesgoso en frío** — porque la nitrificación se frena por debajo de ~10 °C y el NH₄⁺ se acumula, y porque la asimilación de NH₄⁺ a glutamina es enzimática y se enlentece — **es mecanísticamente coherente pero NO la pude verificar contra texto primario.** Ver [NV]. **No la presentes como dato.**

### El mecanismo de la toxicidad está ABIERTO

Éste es un punto donde la honestidad importa, porque hay mucho producto vendido sobre mecanismos supuestos. Xie et al. 2025 **[TP]** son explícitos:

> *"Ninguno de éstos [estallido de ROS, acidificación de rizósfera, desequilibrio iónico, alteración de fitohormonas] son las razones directas de la toxicidad amoniacal."*

Y desglosan qué está sin resolver:

1. **Acidificación**: amortiguar con MES o inhibir la H⁺-ATPasa *"mitiga efectivamente"* los síntomas **pero no restaura el crecimiento por completo** → la acidificación contribuye pero **no es la causa única**.
2. **Desequilibrio C-N**: los autores lo proponen como *"una de las razones principales"* pero admiten que **el NO₃⁻ alto también** desequilibra el C-N, y que aportar C extra *"no puede mitigar la toxicidad amoniacal completamente"*.
3. **SnRK1**: *"aún falta evidencia experimental directa"*.
4. **Fitohormonas**: *"puede ser resultado del estrés oxidativo, más que una razón directa"* — o sea, consecuencia, no causa.
5. **Microorganismos de rizósfera**: *"no podemos concluir que las alteraciones en PGPMs sean una de las razones"*.
6. **Gasto energético**: **contradicho** por evidencia de transporte pasivo (ver §2.3).

> **Qué se puede prometer con la palanca NH₄/NO₃:** un cambio de pH de rizósfera en la dirección deseada, con efecto real y documentado sobre disponibilidad de P y de micronutrientes catiónicos. **Qué NO se puede prometer:** un porcentaje óptimo universal de N amoniacal, ni una explicación cerrada de por qué el exceso hace daño.

---

# 4. Movilidad en floema

El xilema mueve agua y solutos **hacia arriba**, empujado por la transpiración: llega a las hojas viejas, muy transpirantes. El floema mueve fotoasimilados **hacia los sumideros**: hojas nuevas, ápices, frutos, granos, raíces. **Que un nutriente pueda o no viajar por floema decide dos cosas: dónde aparece el síntoma, y si un aporte foliar puede llegar al órgano que lo necesita.**

Referencia general: **Marschner, H.** *Mineral Nutrition of Higher Plants.* (Marschner's Mineral Nutrition of Higher Plants, 3ª ed., ed. P. Marschner, Academic Press, 2012). **[NV — no consultado en ninguna edición en esta sesión.** Ninguna cifra de este dossier se atribuye a Marschner.**]**

## 4.1 Clasificación

| Clase | Elementos | Consecuencia diagnóstica |
|---|---|---|
| **Móviles** | **N, P, K, Mg, S, Cl** | La planta los **retira de la hoja vieja** para alimentar el crecimiento nuevo → **SÍNTOMA EN HOJA VIEJA (basal)** |
| **Parcialmente móviles** | **Zn, Cu, Mo, Fe, Mn**, y **B en algunas especies** | Síntoma intermedio o ambiguo. Depende de especie y de severidad. |
| **Inmóviles** | **Ca**, y **B** en la mayoría de las especies | No se pueden retirar de donde ya están → **SÍNTOMA EN HOJA NUEVA (apical), meristema, fruto** |

## 4.2 La regla diagnóstica

> **Síntoma en hoja vieja → nutriente móvil (N, P, K, Mg, S).**
> **Síntoma en hoja nueva o punto de crecimiento → nutriente inmóvil (Ca, B, Fe, Zn, Mn, Cu).**
> **Muerte del meristema apical → Ca o B, casi siempre.**

Es la herramienta de diagnóstico visual más confiable que existe, y es gratis.

## 4.3 El caso del boro: la movilidad depende de la ESPECIE

Éste es el matiz que rompe la tabla, y está bien documentado **[TP, IFA cap. 5]**:

> *"El boro es móvil en floema en almendro y las aplicaciones hechas en agosto se translocan rápidamente desde las hojas a las yemas en desarrollo para su utilización en primavera. En contraste, el B es inmóvil en pistacho y las aplicaciones foliares en agosto aportaron poco o nada de B a las yemas florales en desarrollo."* (Brown & Hu 1996, citado en Fernández et al. 2013 cap. 5)

**Mecanismo:** las especies que transportan polioles (sorbitol, manitol) —rosáceas como almendro, manzano, duraznero— forman complejos B-poliol que **sí** viajan por floema. Las que transportan sacarosa pura, no.

> **Consecuencia de formulación directa:** un B foliar postcosecha es una inversión razonable en almendro y una pérdida de dinero en pistacho. **El mismo producto, la misma dosis, el mismo momento — y resultados opuestos por fisiología de especie.** Cualquier etiqueta que prometa "B foliar translocable" sin decir en qué especie está vendiendo humo la mitad de las veces.

## 4.4 Calcio: por qué es el caso más difícil

**Torres, E., Kalcsits, L. & Nieto, L.G. (2024).** Is calcium deficiency the real cause of bitter pit? A review. *Frontiers in Plant Science* 15:1383645. DOI **10.3389/fpls.2024.1383645** **[TP]**

Dato duro **[TP]**: *"El Ca²⁺ tiene baja movilidad en floema, y sus niveles son bajos en el citosol"*, y debe mantenerse en **rango micromolar (10–3.000 µM)** en los tubos cribosos, **lo que hace el transporte por floema insuficiente para la demanda de los tejidos.**

Y la razón fisiológica es inescapable: el Ca²⁺ citosólico **es una señal**. Toda la señalización celular por Ca depende de mantener el citosol en ~100 nM en reposo. Una planta **no puede** cargar Ca en el floema a concentración alta sin destruir su propio sistema de señalización. **La inmovilidad del Ca no es un defecto: es el precio de usarlo como mensajero.**

Consecuencia: los órganos que **no transpiran** —frutos carnosos, hojas envueltas, tubérculos, meristemas— **no reciben Ca**, porque el Ca solo viaja por xilema y el xilema solo llega donde hay transpiración.

Esto explica, con un solo mecanismo:
- Bitter pit en manzana
- Podredumbre apical (*blossom-end rot*) en tomate y pimiento
- *Tipburn* en lechuga y repollo
- Corazón negro en apio
- Necrosis del ápice en papa

**Y el mecanismo está EN DISCUSIÓN.** Torres et al. 2024 **[TP]** dicen explícitamente que hay incertidumbre sobre *si la deficiencia de calcio es causa directa o síntoma secundario*, sobre las relaciones entre fracciones específicas de calcio y el bitter pit, sobre el rol de las auxinas, y sobre las interacciones entre factores de estrés abiótico. Concluyen: *"los mecanismos involucrados en su desarrollo aún no se conocen claramente."*

> **Traducción:** vender un producto de Ca contra bitter pit prometiendo corregir "la deficiencia de Ca" está prometiendo corregir algo que la literatura de 2024 no ha confirmado que sea la causa.

## 4.5 Consecuencia para movilidad de aplicaciones foliares

**[TP, IFA cap. 5]:**
> *"Las ventajas asociadas con la aplicación foliar de nutrientes durante el período de poscosecha son mayores con los nutrientes móviles en floema (N, K, así como B en especies que transportan B fácilmente)… Para los nutrientes inmóviles en floema, particularmente Ca, Fe, Mn y Zn, no parece haber ventaja alguna en suministrar estos elementos."*

Y un efecto perverso documentado **[TP, IFA cap. 5]**: en ciruelo y pecán, la **remobilización rápida de K desde la hoja hacia el fruto** bajó tanto el K foliar que **produjo quemado de borde (síntoma de deficiencia de K) y muerte de brotes** — *"incluso en suelos con K disponible abundante"*. El nutriente móvil se mueve tan bien que **desnuda la hoja**.

---

# 5. Absorción foliar

**La sección que decide qué se puede prometer.**

Fuentes centrales de esta sección, todas leídas en texto primario:

- **Fernández, V. & Eichert, T. (2009).** Uptake of Hydrophilic Solutes Through Plant Leaves: Current State of Knowledge and Perspectives of Foliar Fertilization. *Critical Reviews in Plant Sciences* 28(1-2):36–68. DOI **10.1080/07352680902743069** **[MD]**
- **Fernández, V. & Brown, P.H. (2013).** From plant surface to plant metabolism: the uncertain fate of foliar-applied nutrients. *Frontiers in Plant Science* 4:289. DOI **10.3389/fpls.2013.00289** **[TP]**
- **Fernández, V., Sotiropoulos, T. & Brown, P.H. (2013).** *Foliar Fertilization: Scientific Principles and Field Practices.* International Fertilizer Industry Association (IFA), París. **[TP — capítulos 2, 3, 4, 5 y 6 extraídos y leídos]**
- **Schönherr, J. (2002).** Foliar nutrition using inorganic salts: laws of cuticular penetration. *Acta Horticulturae* 594:77–84. DOI **10.17660/ActaHortic.2002.594.5** **[MD]**
- **Schönherr, J. (2001).** Cuticular penetration of calcium salts: effects of humidity, anions, and adjuvants. *Journal of Plant Nutrition and Soil Science* 164(2):225–231. DOI **10.1002/1522-2624(200104)164:2<225::AID-JPLN225>3.0.CO;2-N** **[MD]**

## 5.1 La cutícula: qué barrera es realmente

**[TP, Fernández & Brown 2013]** La cutícula es *"una matriz biopolimérica de cutina y/o cutano, con ceras depositadas sobre ella e intruidas en ella"*, más polisacáridos y fenólicos variables. Y la advertencia clave del mismo trabajo: **su composición varía con las condiciones ambientales y fisiológicas, lo que limita la aplicabilidad general de cualquier estudio individual.**

> Eso ya es un límite a lo que se puede prometer: **no hay una "cutícula" — hay la cutícula de esta especie, de esta hoja, de esta edad, crecida en este ambiente.** Un dato de penetración medido en manzano en cámara de crecimiento no transfiere a soya en campo.

Hay **dos modelos de transporte**, y solo uno está resuelto:

| Vía | Para qué solutos | Estado del conocimiento |
|---|---|---|
| **Disolución-difusión** en la matriz lipídica | Lipofílicos, apolares | **Bien entendido.** Gobernado por partición; permeancia P = D·K/l (Fick) |
| **Vía polar acuosa** (poros acuosos / continuo acuoso) | **Iones, sales, nutrientes** | **NO resuelto.** *"Los mecanismos de penetración de solutos hidrofílicos y polares a través de la cutícula actualmente no se comprenden completamente"* **[TP]** |

**El fertilizante foliar de nutrientes viaja por la vía que la ciencia NO tiene resuelta.** Es honesto decirlo.

## 5.2 Tamaño de poro y límite de tamaño molecular

**[TP, IFA cap. 3]:**

| Estructura | Radio de poro acuoso estimado |
|---|---|
| **Hojas** (varias especies) | **0,3 – 0,5 nm** |
| **Frutos** (varias especies) | **0,7 – 1,2 nm** |
| **Hojas de café y álamo** | **2,0 – 2,4 nm** (Eichert & Goldbach) |

Fuentes citadas en el capítulo: Beyer et al. 2005; Luque et al. 1995; Popp et al. 2005; Schönherr 2006; Eichert & Goldbach.

Referencia primaria de los radios de poro, **DOI verificado en Crossref [MD]**: **Eichert, T. & Goldbach, H.E. (2007).** Equivalent pore radii of hydrophilic foliar uptake routes in stomatous and astomatous leaf surfaces – further evidence for a stomatal pathway. *Physiologia Plantarum* 132(4):491–502. DOI **10.1111/j.1399-3054.2007.01023.x**

Y el principio **[TP]**: *"el proceso de permeabilidad cuticular es selectivo por tamaño, discriminándose los compuestos de alto peso molecular (más grandes) frente a las moléculas de bajo peso molecular"* (Schreiber & Schönherr 2009).

**Lo que esto significa en la práctica:**
- Un poro de **0,3–0,5 nm de radio** es del orden de **unas pocas moléculas de agua**. Un ion hidratado de K⁺ o Ca²⁺ ya está en ese orden de magnitud.
- **Todo lo grande queda afuera.** Complejos orgánicos voluminosos, quelatos grandes, polímeros, "nanopartículas" de decenas de nm: **no pasan por vía cuticular.**
- **No hay un número de corte de peso molecular publicado.** Fernández & Brown 2013 **[TP]** son explícitos: *no cuantificado en esta revisión… los valores umbral específicos están ausentes.* Cualquier etiqueta que cite un "límite de 500 Da" o similar está citando algo que no está establecido. Ver [NV].

## 5.3 Estomas: el papel real, y por qué está en discusión

Éste es el punto donde más se exagera comercialmente. La literatura **no** está cerrada.

**[TP, Fernández & Brown 2013]:** hay evidencia confirmada de entrada de agua y solutos por estomas sin presión externa en ciertas especies. Pero:

> *"La contribución global de los estomas al proceso de absorción foliar… permanece poco clara, pero puede ser altamente significativa"* — y varía por especie, estadio de la hoja y condiciones ambientales.

**Datos duros de selectividad por tamaño en la vía estomática [TP, IFA cap. 3]**, de **Eichert, T., Kurtz, A., Steiner, U. & Goldbach, H.E. (2008).** Size exclusion limits and lateral heterogeneity of the stomatal foliar uptake pathway for aqueous solutes and water-suspended nanoparticles. *Physiologia Plantarum* 134(1):151–160. DOI **10.1111/j.1399-3054.2008.01135.x** **[MD — DOI verificado en Crossref]**:
- Partículas de **43 nm de diámetro SÍ** penetraron en los estomas.
- Partículas de **1 µm NO** entraron en el poro estomático.
- La vía estomática *"parece ser menos selectiva por tamaño que la cuticular"* — pero **sigue siendo selectiva**.

**Por qué la vía estomática no es la autopista que se vende:** el poro estomático está diseñado para **no** dejar entrar agua líquida. La tensión superficial de una gota acuosa sobre un poro hidrofóbico impide la entrada masiva. Lo que ocurre es difusión a lo largo de las paredes del poro, no un flujo. Además, un estoma abierto es un estoma en un día de alta transpiración — es decir, **el día en que la gota se seca más rápido** (§5.5).

> **Qué se puede decir:** los estomas contribuyen, la magnitud es específica de especie y condición, y la literatura no la tiene resuelta. **Qué NO se puede decir:** que un adyuvante "abre la vía estomática" y multiplica la absorción por un factor determinado.

## 5.4 Punto de delicuescencia (POD)

**El concepto más accionable de toda esta sección.**

**Definición [TP, IFA cap. 3 y 4]:** el POD es *"el valor de humedad relativa al cual la sal se convierte en soluto"*. Es la HR sobre una solución saturada que contiene sal sólida.

**La ley [TP, IFA cap. 4]:**
> *"Cuando la humedad está por encima del POD, el residuo de sal sobre la cutícula se disuelve, mientras que la penetración CESA cuando la humedad cae por debajo del POD."*

Y: *"Por encima del POD hay a menudo un incremento lineal de la penetración a medida que aumenta la humedad, aunque la naturaleza exacta de esta relación es específica de la sal mineral y de la especie"* (Schönherr 2001; Schönherr & Luber 2001).

**Un nutriente solo entra si está disuelto. Si la gota se seca y la sal cristaliza, la entrada se detiene — no se ralentiza, se detiene.**

### Tabla de POD por sal

**Fuente: Tabla 4.2 de Fernández et al. 2013 (IFA), según Schönherr 2002. [TP — tabla extraída completa del PDF]**

| Compuesto | POD (% HR) | Lectura operativa |
|---|---|---|
| **CaCl₂ · 6H₂O** | **33** | Funciona casi siempre |
| **MgCl₂ · 6H₂O** | **33** | Funciona casi siempre |
| **Zn(NO₃)₂ · 6H₂O** | **42** | Muy bueno |
| **Mn(NO₃)₂ · 4H₂O** | **42** | Muy bueno |
| **K₂CO₃ · 2H₂O** | **44** | Muy bueno |
| **FeCl₃ · 6H₂O** | **44** | Muy bueno |
| **Fe(NO₃)₃ · 9H₂O** | **54** | Bueno |
| **Ca(NO₃)₂ · 4H₂O** | **56** | Bueno |
| **Mg(NO₃)₂ · 6H₂O** | **56** | Bueno |
| **MnCl₂ · 4H₂O** | **60** | Aceptable |
| **NH₄NO₃** | **63** | Aceptable |
| **KCl** | **86** | Marginal |
| **MgSO₄** | **90** | **Malo** |
| **ZnSO₄** | **90** | **Malo** |
| **K₂HPO₄** | **92** | **Malo** |
| **KNO₃** | **95** | **Malo** |
| **KH₂PO₄** | **95** | **Malo** |
| **Ca-propionato · H₂O** | **95** | **Malo** |
| **Ca-lactato · 5H₂O** | **97** | **Muy malo** |
| **K₂SO₄** | **98** | **Muy malo** |
| **Ca-acetato** | **100** | **Inútil sin humectante** |

### Lo que esta tabla dice de la práctica real

**Las sales que más se usan en foliares de macronutrientes son las que peor POD tienen.**

- **Potasio**: K₂SO₄ (98), KNO₃ (95), K₂HPO₄ (92), KH₂PO₄ (95). **Todo el catálogo de K foliar necesita HR >90 % para entrar.** Solo KCl (86) y K₂CO₃ (44) escapan, y el KCl trae cloruro.
- **Sulfatos**: MgSO₄ y ZnSO₄, ambos 90. Son las sales más baratas y más vendidas, y son de las peores por POD.
- **Cloruros y nitratos**: los mejores casi sin excepción.
- **Sales orgánicas de Ca** (acetato, lactato, propionato: 95–100) — que se venden como "más asimilables" — son, por POD, **las peores de la tabla**.

Confirmación en el propio texto **[TP, extracto de búsqueda del Schönherr 2002]**: los tiempos de penetración fueron **141 h para KNO₃** y **115 h para KH₂PO₄** — sales que *"no son adecuadas para nutrición foliar, ya que penetran solo a humedad cercana al 100 %"*.

Ejemplo de campo coherente **[TP, IFA cap. 5]**: el Mg aplicado como **MgCl₂ fue absorbido por hojas de manzano incluso a 30 % de HR**, mientras que **MgSO₄ requirió 80 % de HR** para mostrar aumento de absorción (Neilsen & Hoyt 1984). *"La respuesta probablemente refleja la mayor delicuescencia del MgCl₂ comparado con el MgSO₄."*

### Pero el POD no alcanza por sí solo — advertencia de los propios autores

**[TP, IFA cap. 4]**, y es importante para no sobrevender la tabla:

> *"Si bien está claro que el POD… tiene un efecto importante sobre la penetración, el conocimiento del POD solo es a menudo insuficiente para predecir la eficacia de una sal mineral como fertilizante foliar. Por ejemplo, la aparente facilidad de penetración de Ca(NO₃)₂ o CaCl₂ … no explica la gran dificultad que muchos productores han encontrado para corregir deficiencias de Ca a campo."*

Y: *"Un POD menor que la humedad ambiente es requerido para que ocurra la absorción, pero no siempre es garantía."*

Además, hay una contrapartida **[TP]**: *"las sales con POD bajo pueden actuar como desecantes… en consecuencia, las sales con POD bajo pueden ser más efectivas pero más propensas a causar fitotoxicidad."* **El POD bajo compra penetración y vende riesgo de quemado.**

> **Uso correcto de la tabla POD: es un filtro de descarte, no un predictor de eficacia.** Sirve para decir "esta sal NO va a entrar con esta HR". No sirve para prometer cuánto va a entrar.

## 5.5 Secado de la gota y ventana horaria

**Principio [TP, IFA cap. 3]:** *"Cuando se aplica una solución acuosa a una hoja, inicialmente hay una alta tasa de penetración que decrece con el tiempo como resultado del secado de la solución aplicada"* (Sargent & Blackman 1962).

Y **[TP, IFA cap. 3]**: las altas temperaturas *"acelerarán la tasa de evaporación de las soluciones de pulverización depositadas sobre el follaje, reduciendo el tiempo hasta que ocurre la sequedad de la solución, cuando la penetración ya no puede ocurrir."*

El experimento clásico **[TP, IFA cap. 4]**: Wittwer & Bukovac (1959) mostraron que la **absorción de P por hojas de poroto se DUPLICÓ** cuando la superficie tratada se mantuvo húmeda, comparado con tratamientos donde se dejó secar. **Factor 2, solo por mantener la gota líquida.**

⚠️ **Tiempos de secado en minutos: NO PUBLICADOS en las fuentes que abrí.** El capítulo trata el secado cualitativamente. Los "20–30 minutos de gota húmeda" que circulan en literatura comercial **no los pude verificar.** Ver [NV].

### Ventana horaria — derivada, no citada

La recomendación de aplicar **al atardecer/noche o muy temprano** se deduce de tres hechos verificados, no de una recomendación horaria publicada que yo haya leído:

1. La HR nocturna es la más alta del día → más sales superan su POD (§5.4).
2. La temperatura es más baja → evaporación más lenta → gota líquida más tiempo (§5.5).
3. La penetración sigue **cinética de primer orden** **[TP, IFA cap. 4]** → más tiempo húmedo = más absorbido, con rendimientos decrecientes.

⚠️ Hay un **contraejemplo publicado** que impide dar la regla como absoluta **[TP, IFA cap. 4]**: Van Goor (1973) mostró que la penetración de Ca²⁺ en cutícula de fruto de manzana **correlacionó con humedad DECRECIENTE** justo después de la aplicación, porque el secado **concentra** la gota y aumenta el gradiente de difusión. El efecto neto se invierte solo cuando la HR cae por debajo del POD y la sal cristaliza (Wojcik 2004).

> **O sea: secar un poco concentra y ayuda; secar del todo detiene. El óptimo no es "lo más húmedo posible" sino "que no cristalice".** Esto es más fino de lo que se suele contar.

## 5.6 Cuánto se puede entregar realmente por pase foliar

**Éste es el número que define qué se puede prometer.**

### El marco aritmético

```
kg nutriente/ha por pase = (concentración % p/v) × (volumen L/ha) × (fracción de nutriente en la sal) / 100
```

El techo lo pone la **fitotoxicidad**, no la química: se puede disolver mucho más de lo que la hoja tolera.

### Techos de concentración verificados

| Cultivo / situación | Sal | Techo de fitotoxicidad | Fuente |
|---|---|---|---|
| **Duraznero**, en plena estación | Urea | **0,5 – 1,0 %** | Johnson et al. 2001, en IFA cap. 5 **[TP]** |
| **Duraznero**, previo a caída natural de hoja | Urea | **5 – 10 %** | idem **[TP]** |
| **Trigo/arroz/maíz**, biofortificación | ZnSO₄·7H₂O | **0,2 – 0,5 % p/v** en 500–1000 L/ha | Domingos et al. 2026 **[TP]** |

Cita textual sobre el duraznero **[TP]**: *"En duraznero, el umbral de fitotoxicidad durante la mayor parte de la estación de crecimiento se alcanza con concentraciones de urea aplicada al follaje entre 0,5 y 1,0 % y, en consecuencia, **se requieren múltiples pulverizaciones para satisfacer la demanda del árbol**."* — la propia fuente reconoce el límite.

### Dosis foliares óptimas medidas a campo

| Nutriente | Cultivo | Dosis óptima | Fuente |
|---|---|---|---|
| **P** (como KH₂PO₄) | **Trigo**, antesis tardía | **2,2 kg P/ha** (probado 0 / 2,2 / 4,4 / 6,6) | Benbella & Paulsen 1998, en IFA cap. 5 **[TP]** |
| **P** (como KH₂PO₄) | **Trigo**, floración Zadoks 65 | **2,0 kg P/ha** | Mosali et al. 2006, en IFA cap. 5 **[TP]** |
| **P** | **Maíz** | **2,0 kg P/ha** | en IFA cap. 5 **[TP]** |
| **Zn** (ZnSO₄·7H₂O) | Trigo | **0,5 – 0,7 kg Zn/ha** | Bhardwaj et al. 2022 **[TP]** |

Nótese que **el óptimo de P foliar en trigo NO fue la dosis más alta probada**: 4,4 y 6,6 kg P/ha no superaron a 2,2. **La curva de respuesta foliar tiene techo, y el techo se alcanza rápido.**

### TABLA CENTRAL — Entrega foliar por pase vs demanda del cultivo

Cálculo propio a partir de los techos verificados arriba. Supuesto de volumen: **400 L/ha** (típico de barral en cultivo extensivo). **La aritmética es mía; los techos de concentración y las demandas están citados.**

| Nutriente | Sal | Conc. máx. | Sal aplicada | % nutriente en la sal | **Entrega por pase** | Demanda típica del cultivo | **% de la demanda cubierta** |
|---|---|---|---|---|---|---|---|
| **N** | Urea | 1,0 % | 4,00 kg/ha | 46,0 % N | **1,84 kg N/ha** | **Maíz 14,4 t/ha: 287 kg N/ha** ‡ | **0,64 %** |
| **N** | Urea | 3,0 %* | 12,00 kg/ha | 46,0 % N | **5,52 kg N/ha** | **Maíz 14,4 t/ha: 287 kg N/ha** ‡ | **1,92 %** |
| **P** | KH₂PO₄ | — (dosis medida a campo) | — | — | **2,0–2,2 kg P/ha** | **Trigo 5 t/ha: 25 kg P/ha** ‡ | **8,8 %** |
| **K** | KNO₃ | 3,0 % | 12,00 kg/ha | 38,7 % K | **4,64 kg K/ha** | **Soya 3,48 t/ha: 142 kg K/ha** ‡ | **3,3 %** |
| **Zn** | ZnSO₄·7H₂O | 0,5 % | 2,00 kg/ha | 22,7 % Zn | **0,45 kg Zn/ha** | Cereal: ~0,3 kg Zn/ha † | **152 % — CUBRE TODO** |
| **B** | Ácido bórico | 0,3 %* | 1,20 kg/ha | 17,5 % B | **0,21 kg B/ha** | Cereal: ~0,1 kg B/ha † | **210 % — CUBRE TODO** |

**‡ Demandas VERIFICADAS**, tomadas de §7: maíz **Bender et al. 2013** (287 kg N/ha a 14,4 Mg/ha); soya **Bender et al. 2015** (142 kg K/ha a 3.480 kg/ha); trigo **IPNI Cono Sur** (5 kg P/t × 5 t/ha).

> ⚠️ **Nota de corrección.** Una versión previa de esta tabla usaba demandas estimadas de consenso (200 kg N/ha, 65 kg K/ha, 22 kg P/ha). Al reemplazarlas por las cifras verificadas de §7, **las tres resultaron MÁS ALTAS que mi estimación**, y por lo tanto **el foliar cubre todavía menos de lo que yo había calculado**: N pasó de 0,9 % a **0,64 %**, K de 7,1 % a **3,3 %**, P de 10,0 % a **8,8 %**. La conclusión no cambia de signo — **se refuerza**.

† Las demandas de Zn y B **siguen siendo estimaciones de orden de magnitud [NV]** — la tabla IPNI de §7.1 cubre macronutrientes y secundarios, no micros.

\* Los techos de 3 % para urea y 0,3 % para ácido bórico en cultivos extensivos **[NV]**; el único techo de urea verificado es el de duraznero (0,5–1,0 %).

### La conclusión que sale de la tabla

> **Hay una asimetría de dos órdenes de magnitud entre macro y micronutrientes.**
>
> - **Micronutrientes: el foliar es un método completo de fertilización.** Un solo pase entrega el 100–200 % de la demanda estacional de Zn o B. Tiene todo el sentido: la demanda es de cientos de gramos por hectárea, y eso cabe en una gota.
> - **Macronutrientes: el foliar es un complemento marginal.** Un pase entrega el 1 % de la demanda de N, el 7 % de la de K, el 10 % de la de P. **Es matemáticamente imposible reemplazar el fertilizante de suelo.**

### Confirmación empírica en biofortificación

**Domingos, I.F.N., Baranski, M., Rengel, Z., Bilsborrow, P. & Stewart, G. (2026).** Agronomic Biofortification Strategies to Increase Grain Zinc Concentrations of Wheat, Rice and Maize: A Systematic Review and Network-Meta-Analysis. *Campbell Systematic Reviews* 22(2):18911803261435900. DOI **10.1177/18911803261435900** **[TP]**

| Cultivo | Aumento de Zn en grano, foliar vs control | Ventaja sobre aplicación al suelo | n |
|---|---|---|---|
| **Trigo** | **+18,0 mg/kg** | +14,8 mg/kg | 12 estudios |
| **Arroz** | **+6,6 mg/kg** | +4,4 mg/kg | 8 estudios |
| **Maíz** | **+8,5 mg/kg** | — | 1 estudio |

Tratamientos: *"0,2 %, 0,3 %, 0,4 % y 0,5 % p/v de ZnSO₄·7H₂O a una tasa de aplicación de 500–1000 L/ha"*, con múltiples aplicaciones.

**Para micros, el foliar es superior al suelo.** Esto es coherente con toda la física anterior: el micronutriente aplicado al suelo se fija; aplicado a la hoja, entra.

### ⚠️ Corrección importante: dosis suficiente ≠ respuesta en rendimiento

La tabla de arriba dice que **la dosis alcanza** para micros. **No dice que vaya a haber respuesta.** El dossier hermano `R2b_quelato_foliar_limites.md` §5 trae la evidencia que corrige esto, y es determinante:

**Stewart, Z.P., Paparozzi, E.T., Wortmann, C.S., Jha, P.K. & Shapiro, C.A. (2021).** *Plants* 10:528. DOI **10.3390/plants10030528** — 5 experimentos en maíz, Nebraska:

- *"Solo el sitio de Fe tuvo respuesta consistente de rendimiento en grano, y fue el único experimento que tenía signos visuales de deficiencia de micronutrientes."* Allí: **+13,5–14,6 % con 0,22 kg Fe/ha.**
- En el resto (B, Mn, Zn, Fe/Zn): **sin efecto.**
- **El Zn fraccionado a 0,84 kg/ha BAJÓ el rendimiento 4,5 % por fitotoxicidad foliar.**
- Recuperación aparente del nutriente (ANR): Mn 9,5 %, Zn 16,9 %, **B solo 2,5 %**; la mezcla Fe/Zn dio **ANR negativa** (−9,1 % Fe; −1,3 % Zn) = **supresión mutua**.
- Conclusión textual de los autores: *"resaltan la importancia de confirmar una deficiencia de micronutriente ANTES de la aplicación foliar."*

Y en Iowa (Mallarino, 56 campos, productos EDTA comerciales): *"Ningún aumento de rendimiento en ningún ensayo"*, con una **caída** en soya por Cu, Zn y la mezcla.

> **La afirmación correcta, entonces, es de dos partes y hay que decir las dos:**
>
> 1. **Aritméticamente, el foliar SÍ puede cubrir la demanda de un micronutriente** (152 % de la de Zn en un pase). Para macros no puede, y por dos órdenes de magnitud.
> 2. **Pero cubrir la demanda solo se traduce en rendimiento si la deficiencia existe y está diagnosticada.** Sin deficiencia confirmada, el resultado esperado es **cero, y puede ser negativo** (−4,5 % por toxicidad de Zn; caídas en soya con EDTA).
>
> Nótese además que **0,84 kg Zn/ha fue fitotóxico** en el ensayo de Stewart — es decir, el techo real de seguridad está **por debajo** del doble de los 0,45 kg Zn/ha que calculé como entrega por pase. **El margen entre dosis útil y dosis que quema es estrecho, y esto no se lee en la tabla de POD.**

### Nota sobre eficiencia de penetración real

Aun cuando la dosis alcance, **una fracción se pierde**. **[TP, IFA cap. 5]**: *"El Zn aplicado al follaje generalmente exhibe un bajo grado de penetración foliar (1 a 5 %)"*. Y en aguacate, **<1 %** del Zn aplicado como ZnSO₄ o Zn-metalosato fue realmente absorbido por el tejido foliar.

> Esto no invalida la tabla anterior — la biofortificación funciona porque incluso el 1–5 % de 450 g Zn/ha son 4,5–22 g Zn/ha, y el grano de trigo necesita muy poco Zn adicional para subir 18 mg/kg. **Pero sí significa que "aplicado" no es "absorbido", y la diferencia puede ser de 20 a 100 veces.**

## 5.7 Por qué un quelato no siempre penetra mejor que la sal

La creencia comercial es que el quelato protege al metal y facilita la entrada. **La evidencia es que muchas veces es al revés.** Cuatro razones, todas documentadas.

### Razón 1 — El quelato es más grande

Los poros acuosos cuticulares tienen radio de **0,3–0,5 nm** en hoja (§5.2), y la permeabilidad **es selectiva por tamaño** contra las moléculas grandes **[TP]**. Un complejo Zn-EDTA es sustancialmente más voluminoso que un ion Zn²⁺ hidratado. **La quelación agranda justo lo que tiene que pasar por el poro más chico.**

### Razón 2 — Evidencia directa: la sal simple gana

**[TP, IFA cap. 5]**, naranjo:

| Fuente de Zn | Absorción (% de lo aplicado, 120 días) |
|---|---|
| **ZnSO₄** | **6 %** |
| **ZnCl₂** | **92 %** |

*"Cuando se usaron productos comercialmente disponibles de Zn quelatado en naranjos, las tasas de absorción y translocación **no fueron mayores** que las del sulfato y el cloruro de Zn inorgánicos"* (Caetano 1982; Santos et al. 1999).

Y con ⁶⁵Zn en arveja o poroto, comparando sulfato, cloruro, EDTA y lignosulfonato: **menos del 7 % del Zn aplicado se translocó fuera de la hoja tratada, sin importar la fuente** (Ferrandon & Chamel 1988; Sartori et al. 2008).

**Nótese que la diferencia ZnSO₄ (6 %) vs ZnCl₂ (92 %) —un factor 15— NO es un efecto de quelación: es POD.** ZnSO₄ tiene POD 90 %; los cloruros están en 33–44 %. **La química que explica el resultado es la delicuescencia, no la forma "orgánica".**

### Razón 3 — Confirmación en Ca, con números limpios

**Santos, E., Montanha, G.S., Agostinho, L.F., Polezi, S., Marques, J.P.R. & de Carvalho, H.W.P. (2023).** Foliar Calcium Absorption by Tomato Plants: Comparing the Effects of Calcium Sources and Adjuvant Usage. *Plants* 12(14):2587. DOI **10.3390/plants12142587** **[TP]**

Tres fuentes, todas a 0,1 M de Ca, medidas por XRF a 100 horas:

| Fuente de Ca | POD | **% absorbido (100 h)** |
|---|---|---|
| **CaCl₂** (sal simple) | **33 %** | **90 %** |
| **Ca-citrato** (complejo orgánico) | alto | **18 %** |
| **Ca₃(PO₄)₂** (nanopartícula) | insoluble | **4 %** |

**La sal inorgánica simple absorbió 5 veces más que el complejo orgánico y 22 veces más que la nanopartícula.** Y el orden sigue exactamente el POD.

Efecto del adyuvante (1 % aceite mineral): subió el Ca-citrato de 18 % a 28 %, **bajó el CaCl₂ de 90 % a 77 %**, y no hizo nada al fosfato. **El adyuvante ayudó al peor y perjudicó al mejor.**

Cinética: el CaCl₂ mostró decaimiento exponencial con **vida media de 15 h sin adyuvante y 5 h con adyuvante**. Ca-citrato y Ca₃(PO₄)₂ fueron lineales — o sea, **más lentos y sin saturar**, lo que confirma que estaban limitados por disolución, no por transporte.

### Razón 4 — La forma neutra y pequeña es la que gana

**[TP, IFA cap. 5]**, sobre por qué el boro es el nutriente foliar más eficaz:
> el rendimiento *"probablemente resulta del pequeño tamaño y la naturaleza no cargada del ácido bórico no disociado, que es el estado químico predominante a valores de pH menores a 8,2. El ácido bórico no disociado, similar a la urea y al glicerol, **debería pasar fácilmente a través de las membranas cuticulares**."*

**Pequeño + sin carga = pasa.** Es la misma razón por la que la urea es el mejor vehículo de N foliar: es una molécula pequeña y neutra, no un ion.

### Cuándo el quelato SÍ sirve

Para no caer en el extremo opuesto — hay casos documentados a favor **[TP, IFA cap. 5]**:
- En arroz, la deficiencia de Zn se corrige con ZnSO₄, *"pero la aplicación en formas quelatadas, como Zn-EDTA, resultó más eficiente"* (Correia et al. 2008; Karak et al. 2006).
- En manzano, orden de eficacia: Zn-fosfato < Zn-óxido = Zn-oxisulfato < **Zn quelatado/complejado orgánicamente** < **Zn-nitrato** (Peryea 2006, 2007).
- Fe: *"algunos autores reportan ventajas de usar quelatos de Fe sobre sales inorgánicas de Fe, otros no observaron beneficio del primero sobre las últimas, que son más baratas."*
- Los quelatos de Fe sin carga o con carga electrónica *"pueden penetrar la hoja más fácilmente que las sustancias con Fe positivamente cargadas o iónicas"* **[TP, Fernández & Brown 2013]** — la **carga**, no la quelación en sí, es la variable.

Y el veredicto económico del propio capítulo **[TP]**:
> *"Dado que los productos inorgánicos basados en Zn suelen ser menos costosos por unidad de Zn, puede ser menos costoso e igual de efectivo usar una tasa más alta de un producto inorgánico que usar una tasa menor de un producto complejado orgánicamente, más caro."*

### 🔗 Concordancia y diferencia con `R2b_quelato_foliar_limites.md`

El dossier hermano **R2b** cubre el mismo terreno (penetración cuticular, POD, límite del foliar de Fe). **Lo verifiqué y no hay contradicción de fondo — hay una diferencia de alcance que conviene dejar explícita.**

**En qué coincidimos plenamente:**
- El factor dominante medido es **HR vs POD**, no la quelatación. R2b: *"Vender 'penetra más porque es quelatado' no tiene respaldo… si la HR está por debajo del POD, no penetra nada, sea quelato o sulfato."* **Idéntico a mi §5.4 y §5.7.**
- Los mecanismos de penetración de solutos polares no están resueltos (§5.1).
- La selectividad por tamaño de poro está publicada (Schönherr 2004/2006).

**En qué este dossier CIERRA un punto que R2b dejó abierto — parcialmente:**
R2b lista en su NO VERIFICADO #1: *"Peso molecular del quelato ⇒ menor penetración foliar en campo… no se leyó un ensayo que mida penetración Fe-EDTA vs FeSO₄ en la misma hoja y HR. Evidencia mixta: no afirmarlo como cerrado."*

> **Aporte de este dossier:** el ensayo pedido **existe para Ca, no para Fe**. Santos et al. 2023 **[TP]** midió, **en la misma hoja de tomate, a la misma molaridad (0,1 M) y en las mismas condiciones**, sal simple vs complejo orgánico vs nanopartícula: **CaCl₂ 90 % / Ca-citrato 18 % / Ca₃(PO₄)₂ 4 %**. Es exactamente el diseño que R2b reclamaba.
>
> **Pero atención al alcance:** eso **cierra el punto para Ca y confirma el mecanismo POD** (CaCl₂ tiene POD 33; el citrato y el fosfato no se disuelven). **NO lo cierra para Fe** — el caso del Fe sigue siendo mixto, y ahí R2b tiene razón: Fernández & Brown 2013 sugieren que los quelatos de Fe **sin carga** penetran *mejor* que las formas iónicas. **La variable que manda es la carga y la disolución, no el tamaño por sí solo.**
>
> **Conclusión conjunta defendible:** *el quelato no penetra mejor por ser quelato; en Ca penetra claramente peor que el cloruro; en Fe la evidencia es mixta y depende de la carga del complejo.*

**Diferencia de énfasis a registrar:** R2b concluye que el Fe foliar *"no puede considerarse todavía una estrategia confiable"* (Abadía et al. 2011) y que reverdece solo la superficie mojada sin translocarse (El-Jendoubi et al. 2014). **Eso es plenamente coherente con mi §4.5 y §8.2**: el Fe es inmóvil en floema, igual que el Ca. **Los dos dossiers dicen lo mismo por dos caminos distintos** — R2b por la vía del Fe, éste por la vía del Ca.

> **Regla:** el quelato no es intrínsecamente mejor ni peor. **Lo que predice la penetración es tamaño, carga y POD — no la etiqueta "quelatado" ni "orgánico".** Un CaCl₂ barato le gana a un Ca-citrato caro por 5 a 1 en tomate. Un ZnCl₂ le gana a un ZnSO₄ por 15 a 1 en naranjo. **Exigí el dato de absorción, no el adjetivo.**

### Un efecto contraintuitivo que rompe la lógica de "más concentrado, mejor"

**[TP, IFA cap. 3]:** existe una *"correlación negativa entre concentraciones crecientes de Fe-quelato y la tasa de penetración a través de cutículas aisladas y hojas intactas, expresada como porcentaje de la cantidad aplicada"* (Schlegel et al. 2006; Schönherr et al. 2005). Lo mismo para K (Ferrandon & Chamel 1988) y otros elementos (Tukey et al. 1961).

Dos hipótesis, **ninguna resuelta** **[TP]**: saturación progresiva de los sitios de absorción (Chamel 1988), o que las sales y quelatos de Fe *"pueden reducir el tamaño de la vía hidrofílica induciendo la deshidratación parcial de los poros en la cutícula"* (Schönherr et al. 2005; Weichert & Knoche 2006).

> **Subir la concentración baja la eficiencia porcentual de penetración.** Doblar la dosis no dobla lo absorbido.

---

# 6. Antagonismos e interacciones, con evidencia cuantificada

## 6.0 Advertencia metodológica — la trampa de la dilución

La literatura mezcla **tres cosas distintas** bajo la palabra "antagonismo". Antes de cualquier número hay que declarar cuál se está midiendo:

| Nivel | Qué se mide | Qué significa una caída |
|---|---|---|
| **A. Sitio de absorción** | Flujo del ion en raíz (hidroponía, influjo con isótopo, electrofisiología) | Competencia verdadera por transportador/canal |
| **B. Concentración en tejido** | mg/kg de materia seca | **Ambiguo**: puede ser menor absorción *o* más biomasa sobre la misma absorción |
| **C. Rendimiento** | kg/ha | Único criterio agronómico |

Rietra et al. definen antagonismo **solo en el nivel C**, con criterio multiplicativo (Wallace 1990): antagonismo si `y_ab/y_0 < (y_a/y_0 × y_b/y_0)`. Y los propios autores marcan que esa expectativa *"es una definición operativa y no está basada en un proceso fisiológico vegetal"* (VFRC 2015, nota al pie 2, p. 4).

### Prueba aritmética de la trampa

Tres casos de P→Zn con la misma dirección aparente y tres mecanismos distintos (datos de la Tabla 13, VFRC 2015; **las columnas de absorción total e interpretación son cálculo propio sobre los valores publicados**):

| Estudio | Dosis P | Rendimiento | Zn tejido | Absorción total Zn | Interpretación |
|---|---|---|---|---|---|
| Zhang et al. 2012 — trigo, grano | 0→400 kg/ha | 3,5→6,5 t/ha | 29→13 mg/kg (**−55 %**) | 101,5→84,5 g/ha (**−17 %**) | **Dilución explica ~84 %** de la caída |
| Izsáki 2014 — maíz, hoja | 0→72 kg/ha | 7,4→7,9 t/ha | 23→17 mg/kg (**−26 %**) | — | Rendimiento subió 6,8 %: **antagonismo real** |
| Fageria et al. 2012 — poroto, maceta | 25→200 mg/kg | 1,7→7,6 g/pl (**4,5×**) | 27→24 mg/kg (−11 %) | **subió ~4×** | **Cero antagonismo** |

Aritmética del caso 1: si la absorción se hubiera mantenido en 101,5 g/ha con 6,5 t/ha, la concentración sería 15,6 mg/kg. Observado: 13. De los 16 mg/kg de caída, **13,4 son dilución y 2,6 son menor absorción real**.

> **Regla operativa: nunca reportar un antagonismo desde concentración foliar sin publicar también el rendimiento.**

## 6.1 Marco cuantitativo global

**Rietra, R.P.J.J., Heinen, M., Dimkpa, C.O. & Bindraban, P.S. (2017).** Effects of nutrient antagonism and synergism on yield and fertilizer use efficiency. *Communications in Soil Science and Plant Analysis* 48(16):1895–1920. DOI **10.1080/00103624.2017.1407429** **[MD — texto completo 403]**
Versión abierta y precursora, **leída íntegra [TP]**: VFRC Report 2015/5, 42 pp., 229 referencias.

Búsqueda en Scopus → 349 publicaciones; **116 interacciones en 96 publicaciones**:

| Categoría | n | Magnitud (cociente real/esperado) |
|---|---|---|
| Sinergismo | 21 | 1 a 3 |
| Liebig-sinergismo | 21 | **1,5 a 35** |
| Interacción cero (aditiva) | 34 | ≈ 1 |
| **Antagonismo** | **17** | **0,3 a 0,9** |
| Efecto negativo | 7 | — |
| Sin efecto detectable | 16 | — |

Conclusión de los autores **[TP]**: *"En la mayoría de los casos el antagonismo ocurre entre, o involucra, uno de los cationes Ca, Mg, Fe, Mn, Zn o Cu"* y *"con excepción de un número limitado de estudios para N × S y Mg × K, las interacciones entre macronutrientes son sinérgicas o de interacción cero."*

> **Tres lecturas para decisión:**
> 1. El antagonismo es **minoría** (17/116 ≈ 15 %) y **acotado** (nunca peor que 0,3). Los sinergismos por corrección de deficiencia son **hasta 35×** más grandes. **Buscar deficiencias limitantes rinde mucho más que evitar antagonismos.**
> 2. Los antagonismos que importan son **entre cationes divalentes**, no entre macronutrientes.
> 3. La estrategia "aplicar uno por suelo y otro por hoja" para esquivar antagonismos: *"La ruta más prometedora, suministrar nutrientes antagónicos por vías diferentes (suelo o follaje), aún no ha sido demostrada."* Y donde se probó, **falló** (§6.3).

## 6.2 K–Mg–Ca

### El efecto sobre el contenido es sólido y ASIMÉTRICO

**[TP, VFRC 2015 p. 17-18]**, revisando Bolton & Penny 1968, Bedi & Sekhon 1977, Ologunde & Sorensen 1982, Ohno & Grunes 1985:
> *"El suministro de K tiene un efecto negativo sobre el contenido de Mg de los cultivos, mientras que el contenido de K de los cultivos no es afectado… o incluso aumentado."*

**K baja el Mg; Mg no baja el K.** La asimetría descarta una competencia simétrica simple.

### La magnitud que importa: el desacople planta/animal

| Parámetro | Valor | Fuente (vía VFRC 2015) |
|---|---|---|
| Mg para crecimiento **óptimo del raigrás** | **1,0 g/kg MS** | Smith et al. 1985 |
| Mg requerido por **vaca en lactancia** | **1,6–2,4 g/kg MS** | Suttle & Underwood 2010 |
| Mg alcanzable con fertilización K+Mg balanceada | 2,5 g/kg MS | Reijneveld et al. 2014 |

> **Existe una ventana de 1,0 a 1,6 g/kg donde la pastura está perfecta y la vaca se cae.** El antagonismo K–Mg es un problema de **calidad de forraje**, no de rendimiento de forraje. Usar rendimiento como indicador de riesgo de tetania es medir la variable equivocada.

### Sobre rendimiento: casi ausente

De las **7 interacciones K×Mg** halladas en toda la literatura revisada, **solo 1 clasificó como antagonismo** (caupí, en hidroponía — Narwal et al. 1985). El único caso de campo con daño medible: maíz, 22 mg K/kg → **−16 % de rendimiento** con descenso de Mg (Bedi & Sekhon 1977).

### Umbrales de tetania (fuentes institucionales abiertas)

| Umbral | Valor | Fuente |
|---|---|---|
| **K/(Ca+Mg) forraje, base meq** | **> 2,2 → riesgo creciente de hipomagnesemia** | Van Saun, Penn State Extension **[TP]** |
| Requerimiento Mg rumiante gestación/lactancia | 0,12–0,15 % MS | idem |
| Forraje de riesgo | < 0,2 % Mg, > 3 % K, 4 % N (25 % PB) | Allison, NMSU Guide B-809 **[TP]** |

https://extension.psu.edu/grass-tetany-a-disease-of-many-challenges · https://pubs.nmsu.edu/_b/B809/index.html

### El mecanismo NO está cerrado

**[TP, VFRC 2015, Tabla 17]**, textual:
> *"El mecanismo molecular de la absorción de Mg²⁺ es pobremente entendido y, por lo tanto, no se listan transportadores de membrana plasmática para Mg en la Tabla 17."*

> **La explicación estándar "compiten por transportadores no selectivos" NO se puede sostener para Mg, porque el transportador de Mg no está caracterizado.**

Los transportadores efectivamente promiscuos que sí listan son otros: P3A-H-ATPasas (Na⁺, K⁺, Ca²⁺, Zn²⁺), P1B-Zn-ATPasas (Zn²⁺, Co²⁺, Cu²⁺), NRAMP (Mn²⁺, Fe²⁺, Co²⁺), ZIP (Zn²⁺, Cu²⁺, Fe²⁺). Su conclusión es prudente: *"La competencia entre cationes divalentes por varios transportadores de membrana plasmática es **probablemente** importante."*

### Las relaciones Ca/Mg del SUELO están refutadas

**Kopittke, P.M. & Menzies, N.W. (2007).** A review of the use of the basic cation saturation ratio and the "ideal" soil. *Soil Science Society of America Journal* 71(2):259–265. DOI **10.2136/sssaj2006.0186** **[MD]**

> *"Dentro de los rangos comúnmente hallados en suelos, la fertilidad química, física y biológica de un suelo generalmente NO es influida por las relaciones de Ca, Mg y K"* — y *"la promoción continuada del BCSR resultará en el uso ineficiente de recursos en agricultura."*

> **Esto invalida el sistema de saturación de bases "ideal" (65 % Ca / 10 % Mg / 5 % K) como base de recomendación.** El antagonismo K–Mg es real en el tejido; la relación Ca/Mg **del suelo** como criterio de manejo **no está respaldada**.

## 6.3 P–Zn inducido

### El mecanismo clásico ESTÁ EN DISCUSIÓN, y la disputa está publicada

**[TP, VFRC 2015, nota al pie 5, p. 15]**, textual:
> *"Si bien el mecanismo de la interacción P × Zn ha sido a menudo sujeto de investigación, la relevancia de la interacción también es debatida. Alloway (2008) afirmó: 'Los altos niveles de fosfato en el suelo son una de las causas más comunes de deficiencia de zinc en cultivos en todo el mundo', mientras que Pan (2012) afirmó que 'La evidencia directa de esta interacción es escasa' y 'Las respuestas a Zn en suelos con alto P no han mostrado deficiencias de Zn'."*

Y sus propios datos apoyan a Pan: **de las 11 interacciones P×Zn sobre rendimiento, ninguna clasificó como antagonismo.** Los dos casos con daño real fueron ambos **sobre fondo ya deficiente en Zn**: poroto enano, 200 kg P/ha → **−10 %**; maíz hidroponía, 80 mg P/L → **−28 %**.

> **El P no induce deficiencia de Zn; desnuda una deficiencia de Zn preexistente.**

### El experimento que separa los mecanismos

**Ova, E.A., Kutman, U.B., Ozturk, L. & Cakmak, I. (2015).** High phosphorus supply reduced zinc concentration of wheat in native soil but not in autoclaved soil or nutrient solution. *Plant and Soil* 393:147–162. DOI **10.1007/s11104-015-2483-8** **[MD]**

El título es el resultado. Mismo P, tres medios: el efecto **desaparece al autoclavar el suelo y desaparece en solución nutritiva**. Eso **descarta competencia iónica directa en la membrana** y descarta química de suelo pura → **el efecto requiere la biota del suelo**.

### Cuantificación del mecanismo micorrícico

**Yu, B.-G., Chen, X.-X., Cao, W.-Q., Liu, Y.-M. & Zou, C.-Q. (2020).** *Frontiers in Plant Science* 11:606472. DOI **10.3389/fpls.2020.606472** **[TP]**

| Cultivo | Micorrícico | Δ Zn parte aérea | Δ acumulación total Zn (600 mg P/kg) | Qué lo explica |
|---|---|---|---|---|
| **Maíz** | Sí (AMF) | **−43 a −63 %** | **−55 %** | Colonización AMF explica **89 %** |
| **Soya** | Sí (AMF) | **−29 a −60 %** | **−54 %** | Colonización AMF explica **64–69 %** |
| **Colza** | **No** (no AMF) | −19 a −31 % | −31 % | Peso y Zn radicular explican **90–92 %** |

> **La caída es ~2× mayor en cultivos micorrícicos, y en ellos la supresión de micorrizas por P explica la mayoría del efecto.** En soya y maíz, el "antagonismo P–Zn" es en buena medida **un efecto sobre el simbionte, no sobre la planta.**

### Los cinco mecanismos coexistentes

**Chen, X.P. et al., incl. Cakmak, I. & Zou, C.Q. (2017).** *Scientific Reports* 7. DOI **10.1038/s41598-017-07484-2** **[TP]**. Los autores no eligen un mecanismo — listan cinco:
> *"reducida disponibilidad de Zn en la rizósfera, reducción en la absorción de Zn por unidad de peso radicular, disminución de la colonización micorrícica, menor translocación raíz-a-parte-aérea de Zn, y **efecto de dilución inducido por rendimiento**."*

Datos del mismo trabajo: Zn en grano de trigo a escala global **20,4–30,5 mg/kg** (meta de biofortificación 40 mg/kg); el Olsen-P de suelos agrícolas de China subió de **7,4 a 24,7 mg/kg en tres décadas**; el Zn foliar aportó **+10,5 mg/kg** promedio sobre 320 pares de parcelas.

### La dirección inversa, poco citada

**[TP, VFRC 2015 p. 15]**, citando Huang et al. 2000 y Bouain et al. 2014:
> *"el control de la absorción de P por la planta se pierde bajo deficiencia de Zn, ya que la expresión de proteínas transportadoras de P de alta afinidad está ligada al estado de Zn de la planta."*

**La deficiencia de Zn causa sobreabsorción de P**, no solo al revés. Muchos casos de campo pueden estar leyendo el bucle al revés.

### Umbral P/Zn en tejido: NO EXISTE VERIFICADO

Los valores que circulan (P/Zn > 150, > 200) **no aparecen con respaldo primario en ninguna fuente abierta**. Ver [NV].

## 6.4 Fe–Mn

A diferencia de K–Mg, este antagonismo **sí aparece en rendimiento**. De las 7 interacciones Fe×Mn del VFRC 2015: maíz **antagonismo (0,8)** (Bansal et al. 1999); soya **antagonismo (0,76)** (Kobraee & Shamsi 2011); garbanzo, trigo y soya negativos; poroto sin efecto.

Casos de daño documentados:
- **Garbanzo**, 2 mg Fe/kg → **−19 % rendimiento**, con descenso de Mn
- **Lupino blanco**, 8 mg Fe/kg → **−18 % rendimiento**, con descenso de Mn
- **Rábano**, 28 mg Fe/kg → **−41 % rendimiento**, con descenso de Mg

**Mecanismo — dos vías, ambas plausibles:**
1. **Transportador compartido**: NRAMP transporta Mn²⁺, Fe²⁺, Co²⁺; ZIP transporta Zn²⁺, Cu²⁺, Fe²⁺ (Tabla 17, VFRC 2015). **Aquí sí hay competencia documentada a nivel molecular**, a diferencia de Mg.
2. **Inhibición de la ferric-chelate reductasa** (Estrategia I) por alta disponibilidad de metales — alfalfa, remolacha, pepino, caupí, poroto.

### Y el dato más importante para formulación

**[TP, VFRC 2015]**: Moosavi & Ronaghi 2010 probaron corregir la deficiencia de Mn inducida por Fe en poroto **por suelo y por vía foliar**, y *"ambas no fueron efectivas."* Lo mismo en garbanzo y trigo: la aplicación de Mn no mejoró rendimiento y el Fe por cualquier vía dio efecto nulo o negativo.

> **Cambiar la vía de aplicación NO resuelve este antagonismo.** Ver "LO QUE NO SE PUEDE" §8.3.

**Relación Fe/Mn crítica en tejido: NO EXISTE UMBRAL ESTABLECIDO.** Los trabajos que la usan la reportan cualitativamente. Ver [NV].

## 6.5 Cu–Mo–S

### En la PLANTA: competencia molecular real, cero consecuencia agronómica

Molibdato y sulfato **sí comparten transportador** (MOT/SULTR). Sin embargo, de los 3 estudios Mo×S sobre rendimiento **[TP, VFRC 2015]**:
> *"Ninguno de los estudios mostró antagonismo para Mo × S… Estos efectos sugieren que la competencia en la membrana plasmática probablemente no sea una interacción mayor entre Mo × S determinando el rendimiento."*

**Ejemplo perfecto de la disociación nivel A / nivel C.**

### En el RUMIANTE: acá sí, y con números duros

**López-Alonso, M. & Miranda, M. (2020).** Copper Supplementation, A Challenge in Cattle. *Animals* 10(10):1890. DOI **10.3390/ani10101890** **[TP]**
Revisión canónica anterior: **Suttle, N.F. (1991).** *Annual Review of Nutrition* 11:121–140. DOI **10.1146/annurev.nu.11.070191.001005** **[MD]**

**Mecanismo [TP]:** *"Los compuestos de azufre inorgánicos y orgánicos son metabolizados por microbios en el rumen, produciendo sulfuro. Además, el azufre y el molibdeno reaccionan para formar tiomolibdatos… Estos compuestos se unen fuertemente al cobre (tri- y tetratiomolibdatos unen cobre irreversiblemente)… El cobre unido es insoluble y, por lo tanto, no se absorbe en el intestino."*

| Parámetro | Valor (textual) |
|---|---|
| **Relación Cu:Mo** | *"relaciones <1 indican alto riesgo de deficiencia de cobre y relaciones >3 se consideran seguras"* |
| Efecto del Mo solo | absorción real de Cu baja *"cerca de 1 %"* al pasar Mo de 1 a 5 mg/kg MS |
| **Efecto del S — el grande** | *"Con 0,2 % de azufre en la dieta, cerca del 5,5 % del cobre estaba disponible; con 0,4 % de azufre, el cobre absorbible se redujo a cerca de 1,5 %"* → **−73 % al duplicar el S** |
| Umbral de arranque / MTL S | MTL 4 g S/kg MS para novillos, *"aunque la depresión de la absorción de cobre comienza a 1 g S/kg MS"* |
| Cu hepático vs S | de 230 a 140 o 96 mg Cu/kg MS al subir S de 0,12 a 0,31 o 0,46 % MS |

> **El S es el driver dominante, NO el Mo.** Un Cu:Mo "seguro" con S alto sigue siendo peligroso. **La relación Cu:Mo sola es un indicador incompleto.**

## 6.6 Exceso de N y B

**Koohkan, H. & Maftoun, M. (2016).** Effect of nitrogen–boron interaction on plant growth and tissue nutrient concentration of canola. *Journal of Plant Nutrition* 39(7):922–931. DOI **10.1080/01904167.2016.1143492** **[MD — T&F 403; magnitudes no verificadas]**. Dirección confirmada: el B en parte aérea **desciende al subir N**.

**Aquí la dilución es la hipótesis principal, no el antagonismo.** No hay sitio compartido: el B se absorbe como ácido bórico/borato vía transportadores BOR y canales NIP — vía completamente distinta a NO₃⁻ (NRT) o NH₄⁺ (AMT). **No existe un transportador común que sostenga un antagonismo verdadero.**

**Mecanismo EN DISCUSIÓN. Long, Y. & Peng, J. (2023).** Interaction between Boron and Other Elements in Plants. *Genes* 14(1):130. DOI **10.3390/genes14010130** **[TP]**. Los autores identifican cambios en expresión de *NRT2* y *PAM2*, y notan que en tabaco bajo deficiencia de B las concentraciones de nitrato en hoja y raíz son bajas — **el efecto también corre en sentido B→N**. Y cierran:

> *"se han obtenido algunos resultados inconsistentes en distintas plantas o distintos experimentos, incluso bajo la influencia del B sobre el mismo elemento. Esto podría relacionarse con las diferencias en condiciones y métodos experimentales."*

Efecto colateral confirmado: **el N alivia la toxicidad de B** (colza, cebada, trigo) — coherente con dilución.

## 6.7 NH₄⁺–K⁺ y Ca–B

### NH₄⁺ / K⁺ — antagonismo verdadero, molecular y asimétrico

**ten Hoopen, F., Cuin, T.A., Pedas, P., Hegelund, J.N., Shabala, S., Schjoerring, J.K. & Jahn, T.P. (2010).** Competition between uptake of ammonium and potassium in barley and Arabidopsis roots. *Journal of Experimental Botany* 61(9):2303–2315. DOI **10.1093/jxb/erq057** **[MD]**

- Correlaciones **negativas** entre flujos de K⁺ y NH₄⁺ → absorción competitiva
- Inhibidores del transporte de K⁺ **redujeron el influjo de NH₄⁺ y aliviaron la depresión de crecimiento por amonio** — evidencia causal directa
- Transportador de cebada **HvHKT2;1**: *"los transportadores y canales de K⁺ de plantas son capaces de transportar NH₄⁺"*
- La toxicidad por NH₄⁺ **se agrava con K⁺ bajo y se mitiga con K⁺ alto**

**Asimetría:** el NH₄⁺ deprime la absorción de K⁺ vía canales de K; **el K⁺ NO deprime la absorción de NH₄⁺** vía AMT.

**Pero en rendimiento no aparece.** La interacción N×K es abrumadoramente **sinérgica** (canola 1,6; trigo 1,3; arroz 1,0; piña 1,1). Conclusión de Rietra **[TP]**: *"la interacción N × K no puede explicarse simplemente por competencia a nivel de membrana plasmática."*

> **El ejemplo más limpio de por qué no se puede extrapolar del nivel A al nivel C.**
> **Corolario de formulación útil:** si vas a usar N amoniacal alto, **subí el K**. La evidencia causal (inhibidores de K alivian la toxicidad amoniacal) lo respalda.

### Ca–B

3 interacciones: arveja/poroto en hidroponía **antagonismo (0,4)**; maní en campo **Liebig-sinergismo (7,2)**; zanahoria aditivo. El maní pasó de 0,25 g/pl (control) a **4,50 g/pl** con Ca+B combinados, contra 0,63 con Ca solo y 0,25 con B solo — **deficiencia doble resuelta, no antagonismo.**

**Mecanismo CONTESTADO [TP, Long & Peng 2023]:** *"Una mayor concentración de Ca en el medio de cultivo puede agravar los síntomas de deficiencia de B en las plantas, pero aliviar la toxicidad del estrés por B de alta concentración"* — **efecto de doble signo según el nivel de B**. Y sobre la relación crítica: *"la relación Ca/B óptima para el crecimiento de varias plantas es diversa"* — **sin dar número**.

Sobre B×K y B×Mg los mismos autores son categóricos: *"Las interacciones de B con K, Mg y S en plantas no han sido muy investigadas."*

---

# 7. Ventana fenológica de demanda por cultivo

**Cobertura honesta de esta sección: 6 cultivos con ventana fenológica verificada** (maíz, soya, girasol, trigo, caña parcial, sorgo parcial), **1 parcial** (tomate, solo N), **2 sin ventana** (café, papa). Lo faltante está declarado en §9.

## 7.0 Distinción que hay que hacer antes de cualquier número

| Término | Qué mide | Para qué sirve |
|---|---|---|
| **Absorción / extracción total** | Planta entera, todo el ciclo | Dimensionar la **demanda** que hay que satisfacer |
| **Exportación** | Solo el órgano cosechado que sale del lote | Calcular la **reposición** de un balance |
| **Índice de cosecha del nutriente (IC)** | Exportación / absorción | Cuánto vuelve al suelo con el rastrojo |

> **Confundir ambos es el error más común de las tablas que circulan.** Un balance de reposición basado en exportación **subestima gravemente la demanda**: en soya el IC del Ca es **9 %** — el 91 % del Ca absorbido queda en el rastrojo, pero la planta igual tuvo que absorberlo.

## 7.1 Tabla transversal (kg de nutriente por tonelada de producto)

**Ciampitti, I.A. & García, F.O.** *Requerimientos nutricionales. Absorción y extracción de macronutrientes y nutrientes secundarios. I. Cereales, oleaginosos e industriales.* IPNI Cono Sur, Archivo Agronómico #11, pp. 13–16. **[TP]**
https://www.profertil.com.ar/wp-content/uploads/2020/08/requerimientos-de-cultivos-ipni.pdf

| Cultivo | Base | N | P | K | Ca | Mg | S |
|---|---|---|---|---|---|---|---|
| **Trigo** | Absorción total | 30 | 5 | 19 | 3 | 4 | 5 |
| Trigo | Extracción en grano | 21 | 4 | 4 | 0,4 | 3 | 2 |
| **Maíz** | Absorción total | 22 | 4 | 19 | 3 | 3 | 4 |
| Maíz | Extracción en grano | 15 | 3 | 4 | 0,2 | 2 | 1 |
| **Sorgo granífero** | Absorción total | 30 | 4 | 21 | – | 5 | 4 |
| Sorgo | Extracción en grano | 20 | 4 | 4 | 0,9 | 1 | 2 |
| **Soya** | Absorción total | 75 | 7 | 39 | 16 | 9 | 4 |
| Soya | Extracción en grano | 55 | 6 | 19 | 3 | 4 | 3 |
| **Girasol** | Absorción total | 40 | 11 | 29 | 18 | 11 | 5 |
| Girasol | Extracción en grano | 24 | 7 | 6 | 1 | 3 | 2 |
| **Caña de azúcar** | Absorción total (incl. raíces) | 5 | 1,3 | 6 | – | 0,9 | 0,4 |
| Caña | Extracción (parte aérea) | 3,4 | 0,6 | 3 | 0,5 | 0,5 | 0,2 |
| **Café** | Absorción total (fruto) | 24 | 2 | 19 | 2 | 1 | 1 |
| Café | Extracción en fruto | 5 | 0,5 | 6 | – | – | – |

⚠️ Los valores de caña están **en base a materia seca**, NO por tonelada de caña fresca — no son comparables con las cifras por TCH de §7.5. Mezclarlos es un error frecuente.

## 7.2 Maíz

**Bender, R.R., Haegele, J.W., Ruffo, M.L. & Below, F.E. (2013).** Nutrient uptake, partitioning, and remobilization in modern, transgenic insect-protected maize hybrids. *Agronomy Journal* 105(1):161–170. DOI **10.2134/agronj2012.0352** **[MD — DOI verificado en Crossref]**
Tabla del propio laboratorio autor (Crop Physiology Lab, Univ. of Illinois), a 230 bu/ac ≈ **14,4 Mg/ha** **[TP]**:

| Nutriente | Absorción total (kg/ha) | Exportado en grano (kg/ha) | **IC** |
|---|---|---|---|
| **N** | **287** | 166 | 58 % |
| P₂O₅ | 113 | 90 | **79 %** |
| K₂O | 202 | 66 | **32 %** |
| S | 26 | 15 | 57 % |
| Mg | 58 | 17 | 29 % |

*(Conversión lb/ac → kg/ha ×1,121, aritmética propia. El resumen del paper confirma la magnitud: 286 kg N, 114 kg P₂O₅, 202 kg K₂O para 23,0 Mg/ha de biomasa total.)*

| Nutriente | Ventana de máxima tasa | Dato |
|---|---|---|
| **N** | **V10–V14** | Pico de **7,8 lb N/día**; hasta **⅔ del total en fase vegetativa** |
| **K, Mg** | **Vegetativa** — ⅔ del total antes de floración | **La más temprana.** El K termina en floración |
| **P, S** | Repartido vegetativo / reproductivo | **La más tardía.** Siguen entrando durante todo el llenado |

> **Decisión:** el **K en maíz no admite corrección tardía** — para floración ya está definido. **El P y el S sí.**

## 7.3 Soya

**Bender, R.R., Haegele, J.W. & Below, F.E. (2015).** Nutrient uptake, partitioning, and remobilization in modern soybean varieties. *Agronomy Journal* 107(2):563–573. DOI **10.2134/agronj14.0435** **[MD — DOI verificado; PDF completo leído por el agente de investigación]**
Rendimiento medio **3.480 kg/ha** de grano, biomasa total 9.524 kg/ha, base 0 % humedad. Tabla 4:

| Nutriente | Absorción total (kg/ha) | Exportado (kg/ha) | **IC** |
|---|---|---|---|
| N | 275 ± 18 | 201 ± 11 | 73 % |
| P | 21 ± 1,8 | 17 ± 1,3 | **81 %** |
| **K** | **142 ± 15** | 64 ± 3,2 | 46 % |
| **Ca** | 113 ± 17 | 10 ± 0,6 | **9 %** |
| Mg | 50 ± 6,7 | 9 ± 0,5 | 18 % |
| S | 19 ± 1,5 | 11 ± 0,6 | 61 % |

Ventanas (Tabla 5, función beta de Yin et al. 2003):

| Nutriente | Máxima **tasa** diaria | Tasa (kg/ha/día) | Acumulación máxima | **% que entra después de R4** |
|---|---|---|---|---|
| **K** | **R3** | 2,8 | **R6** (el más temprano) | **28 %** |
| N | R4 | 4,6 | R6.5 | 46 % |
| P | R4 | 0,34 | R6.5 | 45 % |
| Ca | R4 | 1,9 | R7 | 45 % |
| **Mg** | R4 | 0,69 | **R8** (el más tardío) | 49 % |
| S | R4 | 0,29 | R7 | — |

Del resumen **[TP]**: *"K y Fe se adquirieron principalmente durante el crecimiento vegetativo tardío, mientras que N, P, Ca, Mg, S, Zn, Mn, B y Cu se distribuyeron más equitativamente entre las fases vegetativa y de llenado."*

> **Corrección a la creencia común:** el pico de K en soya es **R3, no R5**. Y solo el 28 % del K entra después de R4. **Una corrección de K en R5 llega tarde.**
> **IC del Ca = 9 %:** el 91 % vuelve con el rastrojo. Un balance por exportación subestima gravemente el Ca del sistema.

## 7.4 Girasol

**Zobiole, L.H.S., Castro, C., Oliveira, F.A. & Oliveira Junior, A. (2010).** Marcha de absorção de macronutrientes na cultura do girassol. *Revista Brasileira de Ciência do Solo* 34:425–433. **[TP — PDF completo leído]**
Híbrido BRS-191, Embrapa Soja, Londrina/PR. Para **>3.000 kg/ha de aquenios** (3.334 kg/ha; 9.498 kg/ha MS total):

| Nutriente | Extracción total (kg/ha) | % exportado en aquenios |
|---|---|---|
| **K** | **286** (= 346 kg K₂O/ha) | **4,7 %** |
| N | 150 | 42 % |
| Ca | 116 | 1,0 % |
| Mg | 42 | 9,6 % |
| P | 24 (= 55 kg P₂O₅/ha) | 64 % |
| S | 24 | 11,5 % |

Orden de extracción: **K > N > Ca > Mg > P = S**. Entre R1 (42 DAE) y R8 (89 DAE) se acumuló el **89 % de la MS total**.

| Nutriente | Inflexión (máxima tasa) | Máxima acumulación |
|---|---|---|
| **K** | **R3 (52–53 DAE)** | **R7 (74 DAE)** — el más temprano |
| N | R3 (57 DAE) | R8 (85 DAE) |
| **P** | R4 (62 DAE) | **R8 (85 DAE)** — el más tardío |
| Ca, Mg, S | R4 (58–59 DAE) | R7 (80–82 DAE) |

Recomendación textual de los autores **[TP]**: fertilización de cobertura con N y K a los **30–35 DAE**.

> **Dato notable:** el girasol extrae 286 kg K/ha y exporta **4,7 %**. El K se redistribuye al **capítulo** (39,4 g/kg en R9), no al aquenio (5,2 g/kg). **Es un cultivo reciclador de K, no un extractor neto.**

## 7.5 Caña de azúcar

**Oliveira, E.C.A., Freire, F.J., Oliveira, R.I., Freire, M.B.G.S., Simões Neto, D.E. & Silva, S.A.M. (2010).** Extração e exportação de nutrientes por variedades de cana-de-açúcar cultivadas sob irrigação plena. *Revista Brasileira de Ciência do Solo* 34(4):1143–1152. DOI **10.1590/S0100-06832010000400031** **[MD]**
Rendimiento medio **195 t/ha**, riego pleno, Pernambuco:

| Nutriente | Extracción planta entera (kg/ha) | Exportación en colmos (kg/ha) | % exportado | **kg/TCH** |
|---|---|---|---|---|
| N | 179 | 92 | 51 % | 0,91 |
| P | 25 | 15 | 60 % | 0,13 |
| **K** | **325** | 188 | 58 % | **1,71** |
| Ca | 226 | 187 | 83 % | 1,18 |
| Mg | 87 | 66 | 76 % | 0,44 |

Valores clásicos de contraste, **citados dentro de Oliveira et al. 2010** (originales no abiertos):
- **Orlando Filho (1993)**, por 100 t de colmos: N 143, P 19, K 174, Ca 87, Mg 49, **S 44 kg**.
- **Orlando Filho et al. (1980)**, CB41-76, secano, por TCH: N 0,92–1,80; P 0,09–0,17; **K 0,63–3,2**; Ca 0,11–0,56; Mg 0,13–0,48; S 0,15–0,28.
- **Coleti et al. (2006)**, RB835486 y SP81-3250: rangos similares.

**Convergencia entre fuentes independientes: el K es el nutriente de mayor extracción en caña, ~1,7 kg K/TCH.**

⚠️ **Ventanas fenológicas de caña: NO VERIFICADAS.** Solo hay extracción, no cronología. Ver §9.

## 7.6 Trigo

Extracción: tabla IPNI de §7.1 — **absorción total 30 N / 5 P / 19 K** kg/t de grano; extracción en grano 21 N / 4 P / 4 K. El trigo tiene **la mayor extracción de N y P por tonelada de grano** entre arroz, maíz, trigo y cebada **[TP, IPNI]**.

Ventanas — proyecto *Winter Wheat Nutrient Uptake, Partitioning and Removal*, **Peter Johnson**, Middlesex Soil and Crop Improvement Association / Grain Farmers of Ontario, 2018–2022 **[TP]**
https://gfo.ca/research-projects/w2018ag01/

| Nutriente | Absorción total | Ventana / partición |
|---|---|---|
| **N** | 143 lb N/ac | Absorción más rápida en **encañado**; **83 % del N total completado en ANTESIS** — solo 17 % durante el llenado. 83 % removido en grano |
| **K** | 132 lb K/ac | Solo **27 %** removido en grano |
| Mg | ~13 lb/ac | ~8 lb/ac en grano |
| Cu | 20,6 g/ac | 75 % en grano a madurez |
| B | 13 g/ac | — |

> **Decisión:** con **83 % del N ya absorbido en antesis**, la ventana operativa del N en trigo es el **encañado**. Una aplicación en llenado solo puede tocar el 17 % restante.

⚠️ El mapeo de *"stem elongation"* a Zadoks 30–39 / Feekes 6–10 es **interpretación**, no está en la fuente. La ventana tardía de Mg/B/Mn/Cu **no está verificada** (ver §9).

## 7.7 Sorgo granífero

Extracción, tabla IPNI de §7.1: absorción total 30 N / 4 P / 21 K / 5 Mg / 4 S kg/t.

Dato brasileño convergente, **cita secundaria** dentro de Albuquerque, C.J.B., Camargo, R. & Souza, R.M. (2013), *Revista Brasileira de Milho e Sorgo* 12(1):10–20 **[TP — PDF Embrapa abierto]**:
- **Cantarella et al. (1996)**, por tonelada de grano: **planta entera** 30 N, 6 P, 23 K, 2,7 S; **exportado en grano** 17 N, 4 P, 5 K, 1,2 S.
- **Santi et al. (2006)**: orden de acumulación **N > K > Ca > Mg > P > S**.
- **Pitta et al. (2001)**: las extracciones aumentan **linealmente** con la productividad.

> **Coincidencia notable entre fuentes independientes:** IPNI (30 N / 21 K por t, planta entera) y Cantarella (30 N / 23 K por t). Cuando dos compilaciones independientes convergen, la cifra es utilizable.

⚠️ **Ventanas fenológicas (GS1/GS2/GS3 de Vanderlip): NO VERIFICADAS.**

## 7.8 Tomate (industria, a campo) — parcial

**California Fertilization Guidelines – Processing Tomatoes.** Daniel Geisseler (UCCE Nutrient Management), rev. Timothy K. Hartz y Gene Miyao, UC Davis, act. dic. 2020. **[TP]**
http://geisseler.ucdavis.edu/Guidelines/Tomato.html

| Parámetro | Valor |
|---|---|
| N en fruto | **3 lb N/ton** de fruto fresco; ≈ **⅔ del N total** de la biomasa aérea |
| K removido en fruto | **4–6 lb K/ton**; a 45 ton/ac = **180–270 lb K/ac** |
| N antes del cuaje | **< 30 % del N total** |

Ventana de N **[TP]**: *"La mayor parte del crecimiento estacional y de la absorción de N ocurre entre el cuaje temprano de frutos y el estado de primeros frutos rojos."* El N de preplantación es poco eficiente (máx. 30 lb/ac); arranque comercial 5–15 lb N/ac.

⚠️ Solo tengo la ventana de **N**. Ventanas de los demás nutrientes y todo el tomate de invernadero/indeterminado: **NO VERIFICADO**.

## 7.9 Café — solo extracción, evidencia débil

Único dato: tabla IPNI de §7.1 (Tabla 3, órgano cosechable = fruto): absorción total **24 N / 2 P / 19 K / 2 Ca / 1 Mg / 1 S** kg/t de fruto; extracción en fruto 5 N / 0,5 P / 6 K.

> ⚠️ **Es la evidencia más débil de todo el dossier.** Proviene de una tabla de compilación (fuentes citadas: Bertsch 2003; IFA World Fertilizer Use Manual 1992), **no de un ensayo de marcha de absorción**. **No usar para una recomendación de campo sin corroborar.** Ventanas fenológicas: **NO VERIFICADAS**.

## 7.10 Papa — SIN DATO

**No hay un solo número de papa que pueda respaldar.** Ver §9.

## 7.11 Síntesis: qué nutriente cierra su ventana primero

| Cultivo | Ventana más TEMPRANA (no admite corrección tardía) | Ventana más TARDÍA (sí admite) |
|---|---|---|
| **Maíz** | **K, Mg** (⅔ en vegetativo; K cierra en floración) | **P, S** (siguen en llenado) |
| **Soya** | **K** (pico R3; solo 28 % después de R4) | **Mg** (máximo en R8) |
| **Girasol** | **K** (inflexión R3, máximo R7) | **P** (máximo R8) |
| **Trigo** | **N** (83 % en antesis) | Mg/B/Mn/Cu **[NV]** |
| **Tomate** | — | **N** (cuaje → primeros frutos rojos) |

> **El patrón se repite en los tres cultivos extensivos verificados: el K es SIEMPRE el que cierra primero, y el P o el Mg el que cierra último.**
>
> **Consecuencia directa para evaluar una promesa comercial:** un producto foliar de **K** ofrecido en estado reproductivo avanzado (R5 de soya, llenado de maíz, R8 de girasol) **llega después de que la ventana se cerró** — con independencia de que penetre o no. Y ya vimos en §5.4 que el K foliar además tiene el peor POD del catálogo (KNO₃ 95, K₂SO₄ 98) y en §8.1 que un pase cubre el **3,3 %** de la demanda. **Tres razones independientes contra el mismo producto.**

---

# 8. LO QUE NO SE PUEDE

Cada afirmación con su aritmética explícita.

## 8.1 El foliar NO reemplaza al fertilizante de suelo para macronutrientes

**La aritmética (§5.6):**

**Nitrógeno.** Techo de fitotoxicidad verificado para urea en plena estación: **1,0 %** (duraznero, Johnson et al. 2001 **[TP]**). A 400 L/ha:

```
4 kg urea/ha × 0,46 kg N/kg urea = 1,84 kg N/ha por pase
Demanda VERIFICADA de un maíz de 14,4 t/ha = 287 kg N/ha (Bender et al. 2013, §7.2)
287 / 1,84 = 156 pases
```

**Se necesitarían 156 aplicaciones foliares para cubrir el N de un maíz.** Aun tomando un techo optimista de 3 % **[NV]**, que entrega 5,52 kg N/ha: **52 pases**. Con un ciclo de ~140 días, eso es **una aplicación cada 2,7 días, sin fallar una sola**.

La propia fuente lo admite **[TP]**: *"se requieren múltiples pulverizaciones para satisfacer la demanda del árbol."*

**Potasio.** Peor, porque la limitación es doble: fitotoxicidad **y POD**.

```
KNO₃ al 3 % en 400 L/ha = 12 kg/ha × 0,387 = 4,64 kg K/ha por pase
Demanda VERIFICADA de una soya de 3,48 t/ha = 142 kg K/ha (Bender et al. 2015, §7.3)
142 / 4,64 = 31 pases
```

**Y esos 31 pases solo funcionan si la HR supera 95 %**, porque el POD del KNO₃ es 95 **[TP, Tabla 4.2]**. Con K₂SO₄ (POD 98) el número de pases es irrelevante: **la sal no se disuelve y no entra**. Tiempo de penetración medido para KNO₃: **141 horas** — o sea que 31 pases exigirían **4.371 horas de hoja mojada por encima de 95 % de HR**, unos 182 días continuos. El ciclo de la soya no dura eso.

**Y hay un tercer golpe, independiente de los dos anteriores:** el pico de absorción de K en soya es **R3**, y solo el **28 %** del K entra después de R4 (§7.3). **Aunque la dosis alcanzara y la humedad acompañara, el grueso de los pases caería después de que la ventana se cerró.**

**Fósforo.** El mejor caso de los tres, y aun así:

```
Óptimo foliar medido en trigo: 2,2 kg P/ha (Benbella & Paulsen 1998) [TP]
Demanda VERIFICADA de un trigo de 5 t/ha = 25 kg P/ha (IPNI Cono Sur, §7.1)
2,2 / 25 = 8,8 % de la demanda en un pase
```

Y la curva tiene techo: **4,4 y 6,6 kg P/ha no superaron a 2,2** en el mismo ensayo.

> **Veredicto:** un fertilizante foliar de macronutrientes puede ser un **corrector de deficiencia puntual** o un **suplemento en un momento crítico**. **No puede ser un programa de fertilización.** Cualquier etiqueta que sugiera reemplazo de la fertilización de suelo con NPK foliar está contradicha por aritmética elemental, no por opinión.
>
> **La excepción, y es real:** para **micronutrientes la relación se invierte.** Un pase de ZnSO₄ al 0,5 % en 400 L/ha entrega 0,45 kg Zn/ha, contra una demanda de cereal de ~0,3 kg Zn/ha — **150 % de la demanda estacional en una sola aplicación**. Y el meta-análisis lo confirma en resultado, no solo en dosis: **+18,0 mg Zn/kg en grano de trigo, con ventaja de +14,8 mg/kg sobre la aplicación al suelo** (Domingos et al. 2026 **[TP]**). Para micros, el foliar no solo alcanza: **le gana al suelo.**

## 8.2 El Ca foliar casi no se mueve al órgano que lo necesita

**El problema no es la penetración. Es el transporte posterior.**

**Paso 1 — el Ca SÍ entra a la hoja.** CaCl₂ al 0,1 M: **90 % absorbido en 100 h**, con vida media de 15 h (Santos et al. 2023 **[TP]**). La barrera cuticular no es el cuello de botella.

**Paso 2 — y ahí se queda.** El Ca²⁺ debe mantenerse en **rango micromolar (10–3.000 µM)** en los tubos cribosos, *"lo que hace el transporte por floema insuficiente para la demanda de los tejidos"* (Torres et al. 2024 **[TP]**).

**Paso 3 — el órgano que lo necesita no transpira.** El Ca solo viaja por xilema, y el xilema sigue a la transpiración. Un fruto carnoso, un tubérculo, una hoja envuelta de lechuga o un meristema **casi no transpiran**. No hay flujo que lleve el Ca allí.

> **La aritmética del absurdo:** un producto puede tener un **90 % de absorción foliar demostrada** y una **eficacia de ~0 %** sobre bitter pit, blossom-end rot o tipburn. **Las dos cosas son ciertas al mismo tiempo.** El 90 % es real; el Ca queda en la hoja.

**Confirmación independiente [TP, IFA cap. 5]:** *"Para los nutrientes inmóviles en floema, particularmente Ca, Fe, Mn y Zn, no parece haber ventaja alguna en suministrar estos elementos"* por vía foliar en poscosecha.

**Y la advertencia que cierra el caso [TP, IFA cap. 4]** — los autores señalan explícitamente que la facilidad de penetración del Ca(NO₃)₂ y el CaCl₂ *"no explica la gran dificultad que muchos productores han encontrado para corregir deficiencias de Ca a campo."* **La literatura ya notó la contradicción entre el dato de laboratorio y el resultado de campo.**

**Y aún peor — puede que ni siquiera sea deficiencia de Ca.** Torres et al. 2024 **[TP]** no confirman que la deficiencia de calcio sea la causa del bitter pit: dejan abierto si es *causa directa o síntoma secundario*, y concluyen que *"los mecanismos involucrados en su desarrollo aún no se conocen claramente."*

> **Lo único que un Ca foliar puede prometer honestamente:** un efecto **local, de superficie**, sobre el tejido que recibió la gota — estabilización de membranas y pared celular donde mojó. Por eso los programas de Ca en manzana son de **muchas aplicaciones dirigidas al fruto**, no de aplicaciones al follaje. **Es un tratamiento de contacto sobre el órgano diana, no una nutrición.**

## 8.3 Corregir un antagonismo agregando más del nutriente antagonizado NO siempre funciona

**El caso Fe–Mn, probado y fallido por ambas vías [TP, VFRC 2015]:**

Moosavi & Ronaghi 2010 intentaron corregir la deficiencia de Mn inducida por Fe en poroto aplicando Mn **al suelo** y **al follaje**. Resultado textual: **"ambas no fueron efectivas."** Confirmado en garbanzo (Ghasemi-Fasaei et al. 2005) y trigo (Ghasemi-Fasaei & Ronaghi 2008): la aplicación de Mn **no mejoró el rendimiento** y el Fe por cualquier vía dio efecto **nulo o negativo**.

Y la propia revisión desmiente la estrategia general que se suele proponer **[TP]**:
> *"La ruta más prometedora, suministrar nutrientes antagónicos por vías diferentes (suelo o follaje), **aún no ha sido demostrada**."*

**Por qué falla, con tres mecanismos distintos y tres números:**

**(a) Porque el problema no está en el sitio de absorción.** En P–Zn de maíz y soya, la **colonización micorrícica explica el 89 % y el 64–69 %** de la caída de Zn (Yu et al. 2020 **[TP]**). El P suprimió al **simbionte**. Agregar Zn no restaura la micorriza. Estás dosificando el síntoma.

**(b) Porque muchas veces no hay antagonismo — hay dilución.** En trigo con 400 kg P/ha, el Zn foliar cayó 55 %, pero **13,4 de los 16 mg/kg de caída son dilución por mayor rendimiento** y solo 2,6 son menor absorción. Agregar Zn para "corregir" un 55 % cuando el déficit real es 16 % es sobredosificar por un factor de 3,4. **Y la absorción total de Zn por hectárea solo bajó 17 %, con 86 % más de grano cosechado.**

**(c) Porque el antagonista real puede ser otro elemento.** En el complejo Cu–Mo–S, la relación Cu:Mo se usa como criterio, pero **el driver dominante es el S**: pasar de 0,2 % a 0,4 % de S en la dieta baja el Cu absorbible de **5,5 % a 1,5 % — una caída del 73 %** (López-Alonso & Miranda 2020 **[TP]**). El Mo solo, de 1 a 5 mg/kg, baja la absorción **~1 %**. **Corregir vigilando el Mo cuando el problema es el S es corregir la variable equivocada por un factor de 70.**

**Y la escala del problema está mal calibrada en la industria.** De 116 interacciones documentadas, **solo 17 (15 %) son antagonismos**, y ninguno peor que un cociente de 0,3. En cambio, los **Liebig-sinergismos —corregir una deficiencia que estaba limitando— llegan a 35×** (VFRC 2015 **[TP]**). El maní pasó de 0,25 a 4,50 g/planta corrigiendo Ca y B juntos.

> **Buscar la deficiencia limitante rinde hasta 35×. Evitar un antagonismo rinde, en el mejor caso, evitar una pérdida del 70 % en el peor caso documentado, y típicamente del 10–25 %.** Un programa nutricional construido sobre "equilibrar antagonismos" está optimizando el término chico de la ecuación.

## 8.4 Otras cosas que no se pueden prometer

| Promesa | Por qué no |
|---|---|
| **"Mejora la afinidad de absorción radicular"** | Con Km del HATS de NH₄⁺ ≈ 5 µM y suelos de cultivo a 20–200 µM **[TP]**, el sistema de alta afinidad ya está saturado. La afinidad no es limitante en un lote fertilizado. |
| **"Penetra por los estomas"** | La contribución estomática *"permanece poco clara"* **[TP, Fernández & Brown 2013]**. Se puede decir que contribuye; no se puede cuantificar ni garantizar. |
| **"Quelatado = mejor absorción"** | CaCl₂ 90 % vs Ca-citrato 18 % en tomate **[TP]**. ZnCl₂ 92 % vs ZnSO₄ 6 % en naranjo **[TP]** — y esa diferencia es **POD**, no quelación. Los quelatos comerciales de Zn en naranjo *"no fueron mayores"* que las sales inorgánicas **[TP]**. |
| **"Molécula portadora de bajo peso molecular que atraviesa la cutícula"** | **No existe un umbral de peso molecular publicado.** Fernández & Brown 2013 son explícitos en que los valores umbral *"están ausentes"* **[TP]**. Cualquier cifra concreta es inventada. |
| **"Más concentrado, más absorción"** | Correlación **negativa** documentada entre concentración y penetración porcentual, para Fe-quelato, K y otros **[TP, IFA cap. 3]**. Doblar la dosis no dobla lo absorbido. |
| **"El 10–30 % de N amoniacal es el óptimo para tu cultivo"** | El dato existe y está verificado **[TP]** — pero es de **cannabis medicinal en sustrato** (Saloner & Bernstein 2022). Xie et al. 2025 **[TP]**, que sí es una revisión general, **no da porcentajes**: trabaja en concentraciones. **No hay umbral porcentual universal publicado.** Y entre 30 % y 50 % se pasa de daño leve a **40 % de mortalidad**: la curva es no lineal y el margen es angosto. |
| **"Corrige la deficiencia de Ca que causa el bitter pit"** | La literatura de 2024 **no ha confirmado** que la deficiencia de Ca sea la causa **[TP, Torres et al.]**. |
| **"Relación Ca:Mg ideal del suelo de 5:1"** | **Activamente refutada** por Kopittke & Menzies 2007 **[MD]**: la fertilidad *"generalmente NO es influida por las relaciones de Ca, Mg y K"*. |
| **"Aplicá el antagonista por la otra vía"** | *"Aún no ha sido demostrada"* **[TP]**, y donde se probó (Fe/Mn en poroto, garbanzo, trigo) **falló por ambas vías**. |

---

# 9. NO VERIFICADO

**Nada de esta sección debe usarse frente a un cliente sin verificación adicional.**

## 9.1 Números que circulan y NO pude respaldar

| Ítem | Valor que circula | Estado |
|---|---|---|
| **Tabla de Barber, valores exactos en kg/ha** | Ca 23/66/175; Mg 28/16/105; K 135/4/35/96; P 39/1/2/36 | Obtenidos de extracto de buscador de una fuente secundaria. **La tabla primaria no pudo abrirse** (spectrumanalytic 404, UF/IFAS bloqueado, Pioneer publica imagen). **Los valores varían entre ediciones y rendimientos supuestos.** La conclusión cualitativa (P y K por difusión, N por flujo masal, Ca/Mg con flujo masal excedente) **sí es robusta**. |
| Coeficiente de difusión efectivo del fosfato en suelo | 10⁻¹²–10⁻¹³ m² s⁻¹ | Orden de magnitud citado sin fuente primaria abierta |
| **Km del HATS de K⁺** | ~20–30 µM | Epstein et al. 1963: **DOI verificado, valores no leídos del primario** |
| **Km del HATS de NO₃⁻** | ~10–100 µM | Rivero-Marcos 2025 dice *"micromolares"* sin dar número |
| **Km del HATS de fosfato** | ~3–10 µM | Sin fuente abierta |
| Km/Vmax de Ca, Mg, SO₄, micros | — | No hallados |
| **Generalización de los umbrales de % de N amoniacal a otros cultivos** | "10–30 % de NH₄ es seguro para cualquier cultivo" | Los valores **sí** están verificados **[TP]** en Saloner & Bernstein 2022 — pero **enunciados para CANNABIS MEDICINAL en sustrato, con N total 200 mg/L**. **La extrapolación a otras especies es lo no verificado**, y contradice la sensibilidad conocida de la cebada y la tolerancia del arroz inundado y las ericáceas. Ver §3.4. |
| **Efecto de la temperatura sobre toxicidad amoniacal** | "El amonio es más riesgoso en frío" | **Xie et al. 2025 NO tratan la temperatura.** Mecanísticamente coherente (la nitrificación se frena <10 °C; la asimilación es enzimática) pero **sin respaldo primario**. No presentar como dato. |
| Acidificación de rizósfera, magnitud | −0,75 unidades (arándano); −1,0 unidad (arroz) | Ambos de extracto de buscador. ASHS devolvió 403. **Dirección y mecanismo sí verificados; magnitud no.** |
| Desviación rizósfera vs suelo masal | hasta 2 unidades de pH | Hinsinger et al. 2003, **DOI verificado, texto no leído** (Springer 303→IdP) |
| Solubilidad de metales vs pH | ~100× por unidad de pH (divalentes); ~1000× (Fe³⁺) | Química de consenso, sin fuente primaria abierta |
| **Límite de peso molecular para penetración cuticular** | "500 Da" y similares | **NO EXISTE valor publicado.** Fernández & Brown 2013 **[TP]**: los valores umbral *"están ausentes"*. Cualquier cifra concreta es inventada. |
| **Tiempo de secado de gota en minutos** | "20–30 minutos" | El capítulo IFA trata el secado **cualitativamente**. No hay tiempos publicados en las fuentes abiertas. |
| **Ventana horaria de aplicación** | "Atardecer/noche" | **Derivada** de tres hechos verificados (HR nocturna, temperatura, cinética de 1er orden), **no de una recomendación horaria publicada leída**. Y existe contraejemplo (Van Goor 1973). |
| Techo de urea foliar en cultivos extensivos | 3 % | Solo verificado el de duraznero (0,5–1,0 % en estación; 5–10 % pre-abscisión) |
| Techo de ácido bórico foliar | 0,3 % | Sin fuente abierta |
| **Umbral de relación P/Zn en tejido** | >150, >200 | Ninguna fuente abierta lo sostiene con dato primario |
| **Relación crítica Fe/Mn en tejido** | 1,5–2,5 | Los papers que usan Fe/Mn la reportan **cualitativamente, sin umbral** |
| **Relación Ca/Mg "ideal" del suelo** | 5:1, 6:1 | No verificada y **activamente refutada** (Kopittke & Menzies 2007) |
| Relación K:Mg 1:2 | — | Fuente verificada (Vašíček et al. 2026, DOI 10.3390/plants15050801) pero el enunciado es *"believed to be"* — opinión de revisión, no umbral medido |
| Relación Ca/B óptima | — | Long & Peng 2023 **[TP]** dicen que es diversa entre especies y **no dan número** |

## 9.1b Huecos de la §7 (ventanas fenológicas)

| Ítem | Qué falta | Qué se buscó y por qué falló |
|---|---|---|
| **PAPA — TODO** | Extracción N/P/K/Ca/Mg/S y ventanas (tuberización, *bulking*) | Se identificó vía Crossref **Gómez, Magnitskiy & Rodríguez (2019), *Nutrient Cycling in Agroecosystems* 113:349–363, DOI 10.1007/s10705-019-09986-z** — **DOI verificado**, pero Springer redirigió a portal de autenticación y no se pudo leer ni el resumen. No se abrió ninguna fuente de extensión (Idaho, Minnesota) ni Embrapa Hortaliças. **No hay un solo número de papa respaldable en este dossier.** |
| **CAFÉ — ventanas fenológicas** | Curva de acumulación por semanas/meses post-floración | Se localizó la referencia **Sadeghian, Mejía & González (2012), *Revista Cenicafé* 63(1):7–18, "Acumulación de nitrógeno, fósforo y potasio en los frutos de café"** en resultados de búsqueda, pero **el PDF no abrió** (404 en el patrón de URL de Cenicafé). Un capítulo del Manual del Cafetero que sí se descargó resultó ser sobre subproductos. Laviola no se llegó a leer. |
| **CAFÉ — extracción** | Corroboración con un ensayo real | El único dato (§7.9) es de una **tabla de compilación** (Bertsch 2003; IFA Manual 1992), no de un ensayo de marcha de absorción. **Evidencia más débil del dossier.** |
| **CAÑA — ventanas fenológicas** | Reparto entre *perfilhamento* / gran crecimiento / maduración; caña planta vs soca | No se abrió ninguna fuente con marcha temporal. La página de Embrapa está bloqueada por política de red. **Solo hay extracción, no cronología.** |
| **SORGO — ventanas fenológicas** | GS1/GS2/GS3 de Vanderlip por nutriente | No se halló el equivalente de Bender para sorgo. Albuquerque 2013 mide arreglo de plantas, no marcha temporal. |
| **TRIGO — ventana tardía** | Confirmar que Mg, B, Mn y Cu siguen entrando en llenado | **Malhi et al., DOI 10.4141/P05-116** — DOI y título vistos, pero cdnsciencepub.com falló 3 veces (ECONNRESET / socket hang up). El fragmento visto en buscador **no se cuenta como verificado**. |
| **TRIGO — códigos Zadoks/Feekes** | La fuente de Ontario dice *"stem elongation"* y *"anthesis"* sin códigos | El mapeo a Zadoks 30–39 / Feekes 6–10 es **interpretación propia**, no está en la fuente |
| **MAÍZ — Ca** | La tabla de Illinois no publica Ca | El paper original sí lo trae, pero Wiley está bloqueado y no se obtuvo el PDF completo (a diferencia de soya, donde sí) |
| **Orlando Filho 1980/1993; Coleti 2006** | Originales | **Cita secundaria** dentro de Oliveira et al. 2010. No abiertos. |
| **Cantarella 1996; Santi 2006; Pitta 2001** | Originales | **Cita secundaria** dentro de Albuquerque et al. 2013. No abiertos. |
| **IPNI Archivo Agronómico #11 — cita exacta** | Número de ejemplar y año de *Informaciones Agronómicas del Cono Sur* | El PDF trae autores, título, nº de archivo (#11) y páginas 13–16, **pero no el número de revista ni el año**. Por la bibliografía (última consulta 25/01/2007) sería **2007**, pero es **inferencia**. **Citar con el URL, no con un número de ejemplar inventado.** |
| **TOMATE** | Ventanas de todos los nutrientes salvo N; y todo el tomate de invernadero/indeterminado | Solo se cubrió tomate de industria a campo (California). Los números de invernadero difieren mucho. |
| **Demandas de Zn y B por hectárea** | Valores citables | La tabla IPNI cubre macros y secundarios, **no micros**. Los ~0,3 kg Zn/ha y ~0,1 kg B/ha de la tabla de §5.6 son **estimaciones de orden de magnitud**. |

## 9.2 Fuentes con metadatos verificados pero texto no accesible [MD]

Barber 1984/1995 (libro) · Fernández & Eichert 2009 (T&F) · Schönherr 2001 y 2002 · **Eichert & Goldbach 2007 y Eichert et al. 2008** (Wiley) · Epstein 1953 y Epstein et al. 1963 · Hinsinger et al. 2003 (Springer 303) · Rietra et al. 2017 (T&F 403 — **se usó el informe VFRC 2015, leído íntegro**) · Ova et al. 2015 (Springer 303) · Kopittke & Menzies 2007 · Suttle 1991 · ten Hoopen et al. 2010 · Koohkan & Maftoun 2016 (T&F 403) · Fageria 2001 (10.1081/PLN-100106981) · **Fernández, V., Gil-Pelegrín, E. & Eichert, T. (2020).** Foliar water and solute absorption: an update. *The Plant Journal* 105(4):870–883. DOI **10.1111/tpj.15090** (Wiley 403 — **no consultado**; DOI verificado en Crossref).

> ⚠️ **Corrección de DOI.** Una versión previa de este dossier citó esta revisión con el DOI `10.1111/tpj.14964`. **Es incorrecto**: ese DOI corresponde a Stratilová et al. 2020, *Plant J.* 104(3):752–767, sobre xiloglucano de cebada — un trabajo sin relación. El DOI correcto es **10.1111/tpj.15090**, verificado contra Crossref y coincidente con el que ya figuraba en `R2b_quelato_foliar_limites.md`. El error se detectó al cruzar ambos dossiers.

## 9.3 Fuentes citadas DENTRO de otras, no abiertas por mí

Todas las referencias internas de Rietra/VFRC 2015 y de los capítulos IFA: Bedi & Sekhon 1977 · Bolton & Penny 1968 · Ohno & Grunes 1985 · Ologunde & Sorensen 1982 · Narwal et al. 1985 · Smith et al. 1985 · Suttle & Underwood 2010 · Reijneveld et al. 2014 · Bansal et al. 1999 · Kobraee & Shamsi 2011 · Ghasemi-Fasaei et al. 2005, 2008 · Moosavi & Ronaghi 2010 · Moraghan 1992 · Zhang et al. 2012 · Izsáki 2014 · Fageria et al. 2012 · Gianquinto et al. 2000 · Soltangheisi et al. 2014 · Redondo-Nieto et al. 2003 · Keeratikasikorn et al. 1991 · Alloway 2008 · Pan 2012 · Wallace 1990 · Huang et al. 2000 · Bouain et al. 2014 · **Benbella & Paulsen 1998 · Mosali et al. 2006 · Johnson et al. 2001 · Brown & Hu 1996 · Ferrandon & Chamel 1988 · Neilsen & Hoyt 1984 · Wittwer & Bukovac 1959 · Van Goor 1973 · Wojcik 2004 · Beyer et al. 2005 · Luque et al. 1995 · Popp et al. 2005 · Schreiber & Schönherr 2009 · Caetano 1982 · Santos et al. 1999 · Peryea 2006, 2007 · Correia et al. 2008 · Karak et al. 2006 · Schlegel et al. 2006 · Schönherr et al. 2005 · Chamel 1988 · Tukey et al. 1961 · Weichert & Knoche 2006.**

Los datos que les atribuyo provienen de la cita textual dentro de la fuente que sí leí, no del original.

## 9.4 No consultado en absoluto

**Marschner, *Mineral Nutrition of Higher Plants*, en ninguna edición.** Es la referencia canónica pedida para §4 y **no pude acceder a ella**. La clasificación de movilidad en floema de §4.1 es conocimiento de consenso ampliamente reproducido, pero **en este dossier no está respaldada por lectura de Marschner**. Ninguna cifra se le atribuye.

---

# 10. Referencias verificadas

| # | Cita | DOI / URL | Nivel |
|---|---|---|---|
| 1 | Barber, S.A. (1966). *The role of root interception, mass-flow and diffusion…* IAEA Tech. Rep. Series 65:39–45 | https://inis.iaea.org/records/25hvn-hyj66 | [TP] registro |
| 2 | Barber, S.A. (1984/1995). *Soil Nutrient Bioavailability: A Mechanistic Approach.* Wiley | — | [MD] |
| 3 | Epstein, E. (1953). *Nature* 171:83–84 | 10.1038/171083a0 | [MD] |
| 4 | Epstein, E., Rains, D.W. & Elzam, O.E. (1963). *PNAS* 49:684–692 | 10.1073/pnas.49.5.684 | [MD] |
| 5 | Rivero-Marcos, M. (2025). *Front. Plant Sci.* 16:1634119 | 10.3389/fpls.2025.1634119 | **[TP]** |
| 6 | Xie, L.-B. et al. (2025). *Int. J. Mol. Sci.* 26(6):2606 | 10.3390/ijms26062606 | **[TP]** |
| 7 | Hinsinger, P. et al. (2003). *Plant and Soil* 248:43–59 | 10.1023/A:1022371130939 | [MD] |
| 8 | Fernández, V. & Eichert, T. (2009). *Crit. Rev. Plant Sci.* 28(1-2):36–68 | 10.1080/07352680902743069 | [MD] |
| 9 | Fernández, V. & Brown, P.H. (2013). *Front. Plant Sci.* 4:289 | 10.3389/fpls.2013.00289 | **[TP]** |
| 10 | **Fernández, V., Sotiropoulos, T. & Brown, P.H. (2013).** *Foliar Fertilization: Scientific Principles and Field Practices.* IFA, París. Caps. 2, 3, 4, 5, 6 | avocadosource.com/books/fernandezv2013/ | **[TP]** |
| 11 | Schönherr, J. (2002). *Acta Hortic.* 594:77–84 | 10.17660/ActaHortic.2002.594.5 | [MD] |
| 12 | Schönherr, J. (2001). *J. Plant Nutr. Soil Sci.* 164(2):225–231 | 10.1002/1522-2624(200104)164:2<225::AID-JPLN225>3.0.CO;2-N | [MD] |
| 13 | Torres, E., Kalcsits, L. & Nieto, L.G. (2024). *Front. Plant Sci.* 15:1383645 | 10.3389/fpls.2024.1383645 | **[TP]** |
| 14 | Santos, E. et al. (2023). *Plants* 12(14):2587 | 10.3390/plants12142587 | **[TP]** |
| 15 | Domingos, I.F.N. et al. (2026). *Campbell Syst. Rev.* 22(2) | 10.1177/18911803261435900 | **[TP]** |
| 16 | Bhardwaj, A.K. et al. (2022). *Front. Plant Sci.* 13:1055278 | 10.3389/fpls.2022.1055278 | **[TP]** |
| 17 | Rietra, R.P.J.J. et al. (2017). *Commun. Soil Sci. Plant Anal.* 48(16):1895–1920 | 10.1080/00103624.2017.1407429 | [MD] |
| 17b | Rietra et al. (2015). **VFRC Report 2015/5**, 42 pp. | api.hub.ifdc.org | **[TP]** |
| 18 | Ova, E.A., Kutman, U.B., Ozturk, L. & Cakmak, I. (2015). *Plant and Soil* 393:147–162 | 10.1007/s11104-015-2483-8 | [MD] |
| 19 | Yu, B.-G. et al. (2020). *Front. Plant Sci.* 11:606472 | 10.3389/fpls.2020.606472 | **[TP]** |
| 20 | Chen, X.P. et al. (2017). *Sci. Rep.* 7 | 10.1038/s41598-017-07484-2 | **[TP]** |
| 21 | Kopittke, P.M. & Menzies, N.W. (2007). *SSSAJ* 71(2):259–265 | 10.2136/sssaj2006.0186 | [MD] |
| 22 | López-Alonso, M. & Miranda, M. (2020). *Animals* 10(10):1890 | 10.3390/ani10101890 | **[TP]** |
| 23 | Suttle, N.F. (1991). *Annu. Rev. Nutr.* 11:121–140 | 10.1146/annurev.nu.11.070191.001005 | [MD] |
| 24 | ten Hoopen, F. et al. (2010). *J. Exp. Bot.* 61(9):2303–2315 | 10.1093/jxb/erq057 | [MD] |
| 25 | Long, Y. & Peng, J. (2023). *Genes* 14(1):130 | 10.3390/genes14010130 | **[TP]** |
| 26 | Koohkan, H. & Maftoun, M. (2016). *J. Plant Nutr.* 39(7):922–931 | 10.1080/01904167.2016.1143492 | [MD] |
| 27 | Vašíček, J. et al. (2026). *Plants* 15:801 | 10.3390/plants15050801 | **[TP]** |
| 28 | Van Saun, R.J. *Grass Tetany: A Disease of Many Challenges.* Penn State Extension | https://extension.psu.edu/grass-tetany-a-disease-of-many-challenges | **[TP]** |
| 29 | Allison, C. *Controlling Grass Tetany in Livestock.* NMSU Guide B-809, rev. 2003 | https://pubs.nmsu.edu/_b/B809/index.html | **[TP]** |
| 29b | Saloner, A. & Bernstein, N. (2022). *Front. Plant Sci.* 13:830224 | 10.3389/fpls.2022.830224 | **[TP]** |
| 29c | Eichert, T. & Goldbach, H.E. (2007). *Physiol. Plant.* 132(4):491–502 | 10.1111/j.1399-3054.2007.01023.x | [MD] |
| 29d | Eichert, T., Kurtz, A., Steiner, U. & Goldbach, H.E. (2008). *Physiol. Plant.* 134(1):151–160 | 10.1111/j.1399-3054.2008.01135.x | [MD] |
| 30 | Marschner, H. *Mineral Nutrition of Higher Plants* (3ª ed., 2012, ed. P. Marschner) | — | **[NV — no consultado]** |
| 31 | **Ciampitti, I.A. & García, F.O.** *Requerimientos nutricionales…* IPNI Cono Sur, Archivo Agronómico #11:13–16 | profertil.com.ar/wp-content/uploads/2020/08/requerimientos-de-cultivos-ipni.pdf | **[TP]** |
| 32 | Bender, R.R., Haegele, J.W., Ruffo, M.L. & Below, F.E. (2013). *Agron. J.* 105(1):161–170 | 10.2134/agronj2012.0352 | [MD] + tabla del lab autor **[TP]** |
| 33 | Bender, R.R., Haegele, J.W. & Below, F.E. (2015). *Agron. J.* 107(2):563–573 | 10.2134/agronj14.0435 | [MD] + PDF completo **[TP]** |
| 34 | Zobiole, L.H.S., Castro, C., Oliveira, F.A. & Oliveira Junior, A. (2010). *Rev. Bras. Ciênc. Solo* 34:425–433 | — | **[TP — PDF completo]** |
| 35 | Oliveira, E.C.A. et al. (2010). *Rev. Bras. Ciênc. Solo* 34(4):1143–1152 | 10.1590/S0100-06832010000400031 | [MD] |
| 36 | Albuquerque, C.J.B., Camargo, R. & Souza, R.M. (2013). *Rev. Bras. Milho e Sorgo* 12(1):10–20 | ainfo.cnptia.embrapa.br | **[TP]** |
| 37 | Johnson, P. *Winter Wheat Nutrient Uptake, Partitioning and Removal.* Grain Farmers of Ontario, 2018–2022 | https://gfo.ca/research-projects/w2018ag01/ | **[TP]** |
| 38 | Geisseler, D. (rev. Hartz, T.K. & Miyao, G.). *California Fertilization Guidelines – Processing Tomatoes.* UC Davis, 2020 | http://geisseler.ucdavis.edu/Guidelines/Tomato.html | **[TP]** |
| 39 | Stewart, Z.P., Paparozzi, E.T., Wortmann, C.S., Jha, P.K. & Shapiro, C.A. (2021). *Plants* 10:528 | 10.3390/plants10030528 | vía `R2b` |
| 40 | Fernández, V., Gil-Pelegrín, E. & Eichert, T. (2020). *Plant J.* 105(4):870–883 | 10.1111/tpj.15090 | [MD] |
