# R1b — Fichas técnicas verificadas de fertilizantes líquidos comerciales

Anexo a `R1_sales_solubilidad.md`. Datos de **etiqueta y hoja técnica de fabricante**, no de
literatura. Sirve para el catálogo de materias primas del formulador y para los chequeos del
auditor.

Método: WebSearch agotado (200/200); el resto por WebFetch directo. Dominios de fabricante
bloqueados por política de red: cfindustries.com, products.nutrien.com, tessenderlokerley.com,
cropvitality.com, sds.simplot.com. Eso explica varios huecos del §9.

## Fuentes descargadas y leídas

| # | Documento |
|---|---|
| F1 | Simplot **UAN-32** Product Data Sheet (11040_GHS_R10-14-15) — fertizona.com |
| F2 | **Dyno Nobel** Technical Data Sheet UAN 32 % — dynonobel.com |
| F3 | Wikipedia **UAN** |
| F4 | Simplot página producto UAN-32 |
| F5 | **Nutrien** Product Data Sheet POLY10 **10-34-0** (17-mar-2022) |
| F6 | Fertizona **10-34-0** label / physical characteristics |
| F7 | MSDS **10-34-0** Fertilizer Company of Arizona (2011) |
| F8 | Plant Food Co. **10-34-0** (turf, +0,5 % Fe) |
| F9 | **Tessenderlo Kerley THIO-SUL MSDS** (secc. 9 y 10) |
| F10 | **Thio-Sul** etiqueta TKI rev. 6/10/2014 |
| F11 | **Thio-Sul Application Guide** (Agrian Label Center, product_id 9212) |
| F12 | **KTS 0-0-25+17S** etiqueta Tessenderlo Kerley |
| F13 | Plant Food Co. **KTS 0-0-25 17S** |
| F14 | **YaraLiva UCAN-17** etiqueta (nitrato de calcio-amonio líquido) |
| F15 | Simplot **AN 20-0-0** (solución nitrato de amonio) |
| F16 | Simplot **Ácido fosfórico 0-52-0** |
| F17 | Fertizona **Rizen 7-28-3** (derivado de KOH) |
| F18 | Loveland **15-0-0-16S** (urea-sulfúrico) |
| F19 | **UGA Extension** — Proper Order for Tank Mixing (Waltz & Martinez) |
| F20 | **Sprayers101** — Sprayer Loading and the Jar Test |
| F21–F24 | Wikipedia: ammonium polyphosphate, polyphosphate, ammonium thiosulfate, calcium nitrate |

---

## 1. UAN 32 (32-0-0)

| Parámetro | Valor | Temperatura declarada | Fuente |
|---|---|---|---|
| N total | 32,00 % | — | F1, F4 |
| N amoniacal / nítrico / ureico | 7,75 / 7,75 / 16,50 % | — | F1, F4 |
| **Gravedad específica** | **1,327** | **20 °C** ✔ | F1 |
| **Densidad** | **11,06 lb/gal = 1,325 kg/L** | **20 °C** ✔ | F1 |
| **pH** | **6,8** | no declarada ⚠ | F1 |
| **Salting-out** | **0 °C** | — | F1 |
| Salting-out (rango de fábrica) | **4,4 a 0 °C**; mínimo 0 °C solo con relación NA:urea = 1,30 | — | F2 |
| N por galón | 3,54 lb N/gal (0,424 kg N/L) | — | F1 |
| Amoníaco libre | 0,01 % | — | F1 |
| Materiales | Acero al carbono, inox, aluminio, ciertos FRP. **NO cobre ni latón** | — | F1 |
| Descomposición térmica | 114 °C → amoníaco, CO₂, ácido nítrico | — | F2 |

**Composición másica:** urea 40,9–31,2 %, nitrato de amonio 36,9–49,9 %, agua 22,1–18,8 %,
inhibidor de corrosión 0,03–0,05 % (F2). Relación NA:urea de fábrica 0,9 a 1,6.

### ⚠ CONFLICTO con el dossier R1 — salting-out del UAN 32

`R1_sales_solubilidad.md` reporta **−2 °C** para UAN 32 (y −18 / −10 °C para UAN 28 / 30).
Ese dato **viene de Wikipedia (F3)**, fuente terciaria sin cita primaria.

| Fuente | Salting-out UAN 32 | Autoridad |
|---|---|---|
| Simplot, etiqueta registrada (F1) | **0 °C** | Alta — fabricante |
| Dyno Nobel, TDS (F2) | **4,4 → 0 °C** | Alta — fabricante |
| Wikipedia (F3) | −2 °C | Baja — terciaria |

**Resolución: usar 0 a +4 °C.** Los dos fabricantes coinciden en que 0 °C es el piso, y solo con
la relación NA:urea óptima. Los valores de UAN 28 (−18 °C) y UAN 30 (−10 °C) **quedan sin
verificar contra fabricante** — los PDF de CF Industries y Nutrien con las tres columnas están
bloqueados por dominio.

Consecuencia operativa: un UAN 32 almacenado en una noche fría de invierno **cristaliza**, y el
margen es mucho menor de lo que dice la cifra que circula.

---

## 2. APP — Polifosfato de amonio 10-34-0

| Parámetro | Nutrien POLY10 (F5) | Fertizona (F6) | MSDS AZ (F7) | Plant Food Co. (F8) |
|---|---|---|---|---|
| N / P₂O₅ | 10,0 mín / 34,0 mín | 10,0 / 34,0 | — | 10,0 / 34,0 |
| **% poli del P₂O₅** | **70,2 %** | **65 % poli / 35 % orto** | — | — |
| **Densidad** | 11,68 lb/gal (1,400 kg/L) | 11,6 lb/gal (1,390 kg/L) | — | 12,0 lb/gal |
| **Temp. de la densidad** | **23,9 °C** ✔ | **20 °C** ✔ | — | no declarada ⚠ |
| Gravedad específica | 1,401 @ 24 °C ✔ | — | 1,40 @ "60°" ⚠ unidad no declarada | — |
| **pH** | 6,1 | 6,2 | 5,6–6,2 | 5,5–6,5 |
| **Salting-out** | **−17,7 °C** | **−2,2 °C** | — | "almacenar sobre 0 °C" |
| Viscosidad | 72 cP @4 °C · 45 cP @18 °C · 23 cP @38 °C | 48 cP @16 °C | — | — |
| Composición | — | — | APP 56 % + agua 44 % | — |
| Impurezas | Al₂O₃ 0,6 · CaO 0,02 · F 0,14 · Fe₂O₃ 0,5 · MgO 0,15 · SO₄ 1,6 % | — | — | — |

### 2.1 Vida útil y temperatura — el dato más duro (F5, Nutrien)

> Vida útil **≥ 9 meses** almacenado **por debajo de 21 °C**. Decae **rápidamente por encima de
> 32 °C**.

Causa: por encima de ~32 °C se acelera la **hidrólisis de polifosfato a ortofosfato**, que es lo
que precipita y lo que hace perder la capacidad secuestrante. En galpón de Santa Cruz o del
Chaco esto no es una nota al pie.

### 2.2 ⚠ El salting-out del 10-34-0 no es una constante del producto

**−17,7 °C (Nutrien, 70,2 % poli) vs −2,2 °C (Fertizona, 65 % poli).** 15,5 °C de diferencia,
y no es un error: **es función de la fracción polifosfato**. A mayor % poli, mayor solubilidad y
menor punto de cristalización.

**Regla operativa: no asumir el salting-out sin conocer la relación orto/poli del lote.**

### 2.3 Por qué el APP secuestra micronutrientes

- Fórmula H(NH₄PO₃)ₙOH — cadena de n monómeros (F21).
- El polifosfato actúa como **agente quelante** manteniendo iones metálicos en solución, según el
  grado de polimerización (F21).
- Mecanismo: un par de electrones libre de un oxígeno del polifosfato se dona al metal en una
  interacción ácido-base de Lewis, formando un **complejo quelato** (F22).
- Orden de magnitud de constante: ATP⁴⁻ + Mg²⁺ ⇌ MgATP²⁻, **log β ≈ 4** (F22). Es débil frente a
  un EDTA (log K ~16), y esa es la lectura correcta: secuestra, no blinda.
- El polifosfato **se hidroliza de vuelta a ortofosfato**; el agua rompe el enlace
  fosfoanhídrido (F22).

**Consecuencia para formular:** la capacidad de cargar Zn/Fe/Mn en un 10-34-0 **es la fracción
polifosfato, no el fertilizante**. Un lote de 65 % poli secuestra menos que uno de 70 %, y el
almacenamiento sobre 32 °C destruye esa capacidad además de subir el punto de cristalización.

---

## 3. ATS — Tiosulfato de amonio 12-0-0-26S (Thio-Sul®)

| Parámetro | Valor | Temperatura | Fuente |
|---|---|---|---|
| N total | 12 % (100 % amoniacal) | — | F10, F11 |
| S total | 26 % (100 % combinado) | — | F10, F11 |
| **Densidad** | **11,1 lb/gal = 1,330 kg/L** | **20 °C** ✔ | F10 |
| Gravedad específica | 1,32–1,35 | no declarada ⚠ | F9 |
| **pH del concentrado** | **7,0 – 8,5** | — | F9 secc. 9.9 |
| **Punto de congelación** | **≈ 1,1 °C** | — | F9 secc. 9.8 |
| Punto de ebullición | 98,9 – 104,4 °C | — | F9 |
| lb N / lb S por galón | 1,3 / 2,8 (0,156 / 0,336 kg/L) | — | F11 |
| Cloro | no más de 1 % | — | F10 |
| Dosis máx. anual | 18 gal/acre | — | F10 |
| Rainfastness | 4 horas | — | F11 |

**Composición (F9, MSDS secc. 2.1, % peso):** tiosulfato de amonio 55–60 %, sulfato de amonio
0–4 %, sulfitos de amonio 0,5–2,5 %, **agua 36–45 %**.

### 3.1 Incompatibilidades — texto del MSDS (F9, secc. 10.4)

| Incompatible con | Consecuencia declarada |
|---|---|
| **ÁCIDOS** | *"ACIDS will cause the release of sulfur dioxide, a severe respiratory hazard"* |
| Oxidantes fuertes (nitratos, nitritos, cloratos) | Mezclas explosivas si se calientan a sequedad |
| Álcalis | Aceleran el desprendimiento de amoníaco |
| **Cobre, zinc y aleaciones** (bronce, latón, galvanizado) | Prohibidos en tanques y líneas |
| Calentamiento a sequedad | Amoníaco, sulfato de amonio, **azufre** y óxidos de azufre |

### 3.2 Regla operativa de acidez (F11)

> **"Blends of Thio-Sul should not be acidified below a pH of 6.0."**

Compatible con soluciones nitrogenadas y mezclas N-P-K **neutras a ligeramente ácidas**; mezcla
con UAN y 10-34-0 u 11-37-0 verificando compatibilidad. Jar test recomendado. Agitadores en
marcha durante llenado y aplicación.

⚠ **Matiz de mecanismo:** el MSDS documenta **SO₂**. La reacción
S₂O₃²⁻ + 2H⁺ → S⁰↓ + SO₂ + H₂O **no aparece escrita** en ninguna fuente descargada. Ver §9.

---

## 4. KTS — Tiosulfato de potasio 0-0-25-17S

| Parámetro | Valor | Fuente |
|---|---|---|
| K₂O soluble / S total | 25 % / 17 % (0 % azufre libre) | F12 |
| **pH** | **"neutral to basic"** — *sin valor numérico* ⚠ | F12, F13 |
| **Densidad** | **NO DECLARADA** en las fuentes obtenidas ⚠ | — |
| Densidad derivada (no de fuente) | 12,0–12,4 lb/gal (1,44–1,48 kg/L) | derivado de F12 |
| lb K₂O / lb S por galón | 3,0 / 2,1 (0,360 / 0,252 kg/L) | F12, F13 |
| **Cristalización** | **No almacenar bajo −9,4 °C** | F12 |
| Materiales | Plástico, fibra de vidrio, **inox**. Evitar cobre y galvanizado | F12 |

**Sobre el pH:** ni 14 ni 11 están verificados. Las fuentes de fabricante descargadas solo dicen
*"neutral to basic"*. Un pH 14 sería químicamente implausible para la sal de un ácido débil, pero
no se afirma un número que no se leyó. El boletín técnico con el valor falló por bloqueo de
dominio y ECONNRESET.

### 4.1 Reglas de mezcla del KTS (F12, texto de etiqueta)

| Regla | Texto |
|---|---|
| **Secuencia** | *"water, pesticide, KTS and/or other fertilizer"* |
| Acidez | *"Do not mix KTS with acid or acidic fertilizers below a pH of 6.0. KTS will decompose."* |
| **Calcio** | *"Do Not mix KTS with Calcium Products"* (F13) — sin mecanismo declarado |
| Compatible | Urea y polifosfato de amonio **en cualquier proporción** |
| UAN | Jar test: *"Potassium reacts with nitrate to form KNO₃ crystals"*; se recupera con agua y/o calor |
| Cloración | No aplicar mientras se clora el riego: *"Thiosulfates will neutralize the chlorine"* |

---

## 5. Nitrato de calcio líquido — YaraLiva® UCAN-17 (F14)

| Parámetro | Valor | Temperatura |
|---|---|---|
| N total | 17,0 % (3,2 amoniacal + 8,4 nítrico + 5,4 ureico) | — |
| **Calcio** | **7,2 %** | — |
| Derivado de | Nitrato de calcio, nitrato de amonio y urea | — |
| **Densidad** | **11,8 lb/gal = 1,414 kg/L** | **20 °C** ✔ |
| lb N / lb Ca por galón | 2,01 / 0,85 | — |
| pH | **no declarado en la etiqueta** ⚠ | — |

Advertencia de seguridad de la etiqueta: no dejar que la bomba trabaje en seco o se sobrecaliente
(bloqueo o válvula cerrada) — puede vaporizar y **descomponer el producto, generar presión y
explotar**.

**Referencia química del nitrato de calcio (F24):** Ca(NO₃)₂; densidad anhidro 2,504 g/cm³,
tetrahidrato 1,896 g/cm³; solubilidad a 20 °C: anhidro 1212 g/L, tetrahidrato 1290 g/L; grado
fertilizante común 15,5-0-0 + 19 % Ca.

---

## 6. Otros líquidos con temperatura declarada

| Producto | Análisis | Densidad | Temp. | pH | Salting-out | Fuente |
|---|---|---|---|---|---|---|
| **Nitrato de amonio 20-0-0** | 20 % N (10 NH₄ + 10 NO₃) | 10,53 lb/gal (1,262 kg/L) | **20 °C** ✔ | **6,5** | **5,6 °C** | F15 |
| **Ácido fosfórico 0-52-0** | 52 % P₂O₅ | 14,2 lb/gal; SG 1,695 @24 °C | **20 / 24 °C** ✔ | **1,0** | — | F16 |
| **Rizen™ 7-28-3** (ejemplo de K derivado de KOH) | 7-28-3, de ácido fosfórico + APP + KOH | 11,3 lb/gal (1,354 kg/L) | **20 °C** ✔ | **< 5** | — | F17 |
| **Urea-sulfúrico 15-0-0-16S** | 15 % N ureico + 16 % S | 12,60 lb/gal (1,510 kg/L) | **20 °C** ✔ | corrosivo | — | F18 |

**"Urea líquida":** el enlace rotulado *Liquid Urea 20-0-0* resolvió en realidad al UCAN-17. **No
se obtuvo hoja técnica de solución de urea pura.** Lo más cercano verificado es el urea-sulfúrico
15-0-0-16S y la fracción ureica del UAN (16,50 % de N ureico).

---

## 7. Compatibilidad — lo verificado en fuente de fabricante

| Par | Consecuencia | Fuente | Estado |
|---|---|---|---|
| **ATS + ácido** | Libera **SO₂**; no acidificar bajo **pH 6,0** | F9, F11 | **VERIFICADO** |
| **KTS + ácido (< pH 6,0)** | *"KTS will decompose"* | F12 | **VERIFICADO** |
| **KTS + productos de calcio** | *"Do Not mix"* | F13 | **VERIFICADO** (prohibición); mecanismo no |
| **KTS + UAN (nitrato)** | K + nitrato → **cristales de KNO₃** | F12 | **VERIFICADO** |
| **Ácido fosfórico 0-52-0 + nitratos** | *"Do not mix with materials containing nitrates, such as UAN-32"* | F16 | **VERIFICADO** |
| **Ácido fosfórico + amoníaco** | Evitar mezcla directa salvo recipiente controlado | F16 | **VERIFICADO** |
| **10-34-0 + amoníaco acuoso o anhidro** | *"not compatible"* | F6 | **VERIFICADO** |
| **APP en recipiente abierto** | Sólido de polifosfato en las paredes | F7 | **VERIFICADO** |
| **ATS/KTS/APP/UAN + cobre, latón, bronce, zinc, galvanizado** | Prohibidos como material | F9, F12, F6, F1, F7 | **VERIFICADO** |
| **Tiosulfatos + cloro de riego** | Los tiosulfatos **neutralizan el cloro** | F12 | **VERIFICADO** |

### Compatibilidades positivas declaradas

- **UAN-32:** soluciones de fosfato de amonio (10-34-0, 11-37-0, 9-30-0), soluciones de potasa,
  muchos herbicidas (F1).
- **AN 20-0-0:** 8-24-0, 9-30-0, 10-34-0, solución de potasa (F15).
- **Thio-Sul:** soluciones N y mezclas N-P-K neutras a ligeramente ácidas; UAN; 10-34-0; 11-37-0;
  suspensiones (F11).
- **KTS:** urea y APP **en cualquier proporción** (F12).

### Jar test (F20, Sprayers101) — procedimiento reproducible

1. Leer todas las etiquetas: formulación, calidad de agua requerida (pH/dureza), orden de mezcla.
2. Frasco de vidrio de 1 L con **250 mL de agua** — o **375 mL si el portador es aceite o
   fertilizante**.
3. Añadir los productos en la secuencia estándar, **agitando constantemente**.
4. Esperar **3–5 minutos entre adiciones**, sobre todo con productos secos.
5. Completar a **500 mL** con el portador. **Verificar el pH.**
6. Dejar reposar **15 minutos**.

**Señales de incompatibilidad:** generación de calor, gel o nata, sólidos que sedimentan.

⚠ El jar test detecta incompatibilidad **física** únicamente — no la química ni la legal.

### Orden de mezcla — UGA Extension (F19), literal

> Polvos mojables (WP) • Gránulos dispersables (DG) • Suspensiones (flowables) • Concentrados
> emulsionables (EC) • Soluciones — agitando después de cada adición.

Reglas de tanque asociadas: llenar **la mitad del tanque con agua limpia** y **nunca añadir
concentrados a un tanque vacío**; **iniciar la agitación antes** de cualquier químico; conocer y
marcar el volumen exacto; sin conexión directa a la fuente de agua (retrosifonaje); enjuagar los
envases al tanque; mezclar solo lo que se usa ese día.

Los mnemotécnicos W.A.L.E.S., W.A.M.L.E.G.S. y A.P.P.L.E.S. se citan como guía general, pero
**siempre prevalece la etiqueta sobre el mnemotécnico** (F20).

---

## 9. NO VERIFICADO

| Ítem | Estado | Qué se buscó / por qué falló |
|---|---|---|
| **11-37-0** — análisis, densidad, pH, orto/poli | Sin ningún dato numérico | Solo se confirmó su existencia comercial por mención en F1 y F11. Ninguna hoja técnica obtenida. |
| **KTS — densidad y su temperatura** | No verificado | Bloqueo de dominio tessenderlokerley.com y ECONNRESET en el boletín técnico S3. Solo el valor **derivado** 12,0–12,4 lb/gal. |
| **KTS — pH numérico** | No verificado | Solo cualitativo "neutral to basic". Ni 14 ni 11 confirmados. |
| **KTS — punto de congelación real** | Parcial | Solo el límite de almacenamiento (−9,4 °C), que no es un punto de congelación medido. |
| **ATS — "salting out 6–7 °C"** | No verificado | Apareció en un snippet atribuido a hoja de venta TKI, **PDF nunca descargado**. El MSDS leído dice **1,1 °C** y **contradice** el snippet. **Usar 1,1 °C.** |
| **ATS + ácido → azufre elemental (S⁰)** | Mecanismo no verificado | El MSDS documenta **SO₂**, no S⁰. |
| **Ca + fosfato → fosfato dicálcico** | No verificado | Solo en snippet de nurserymag.com, página no descargada. Ningún documento de extensión o fabricante descargado lo enuncia. |
| **Ca + sulfato → yeso** | No verificado | Ídem. **Nota: este par sí está tratado en `R3_compatibilidad_mezclas.md`; cruzar ahí antes de darlo por abierto.** |
| **APP + Ca** | No verificado | Ninguna fuente descargada lo declara. Adyacente: Nutrien reporta CaO 0,02 % como impureza; KTS prohíbe mezclar con calcio. |
| **Nitrato de calcio líquido CN-9 / 9-0-0-11Ca** | No verificado | Sin hoja técnica; presupuesto agotado. **Sustituto verificado: UCAN-17.** |
| **Solución de urea pura** | No verificado | El enlace rotulado resolvió a UCAN-17. |
| **K líquido a base de KOH como producto** | Parcial | Verificado solo como ingrediente de origen en Rizen 7-28-3. |
| **pH del UCAN-17** | No verificado | No figura en la etiqueta. |
| **UAN 28 y 30 — datos de fabricante** | No verificado | Solo Wikipedia. PDF de CF Industries y Nutrien bloqueados por dominio. |

### Datos con temperatura NO declarada — marcar al usarlos

| Dato | Valor | Fuente |
|---|---|---|
| ATS gravedad específica | 1,32–1,35 | F9 |
| 10-34-0 SG 1,40 @ "60°" | unidad de temperatura no escrita | F7 |
| 10-34-0 turf | 12,0 lb/gal | F8 |
| UAN-32 pH 6,8 | sin temperatura | F1 |
| **Todos los pH reportados** | **ninguna fuente declara la temperatura de medición del pH** | todas |
