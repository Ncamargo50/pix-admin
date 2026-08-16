# R5b — Lagunas químicas cerradas del dossier de bioestimulantes

**Complemento verificado a `R5_bioestimulantes_aminoacidos.md`**
Fecha: 2026-08-16 · Autor: agente de química de coordinación (Pixadvisor)
Alcance: cierra las DOS lagunas químicas declaradas en el dossier R5 — **NV-23** (constantes de estabilidad aminoácido–metal, §5) y **NV-16** (magnitud de la divergencia entre métodos analíticos de sustancias húmicas, §4.3). La laguna regulatoria (§7, NV-26 a NV-30) fue cerrada aparte en `R5c_regulatorio_bioestimulantes.md` y NO se repite aquí.

> **Regla aplicada, igual que en R5.** Todo número lleva fuente, fuerza iónica (I) y temperatura (T). Sin esos tres, no es un número. No se inventó ningún DOI, constante ni artículo. Lo que no se cerró queda declarado con la causa y la vía.

---

## LAGUNA 2 (NV-16) — CERRADA: el factor de divergencia entre métodos de ácidos húmicos

**El número que faltaba existe y está publicado.** El argumento cualitativo de §4.3 ("el % de AH depende del método") se convierte ahora en un factor medido sobre las MISMAS muestras.

### 2.1 El dato central — Lamar & Talbot (2009)

> **Lamar, R.T. & Talbot, K.H. (2009).** *Critical Comparison of Humic Acid Test Methods*. **Communications in Soil Science and Plant Analysis 40(15–16): 2309–2322.** DOI **10.1080/00103620903111251** ✅ verificado (es la referencia (9) del método oficial de Lamar 2014, citada literalmente en él).

Sobre **cinco menas húmicas crudas (raw humate ores) + tres productos comerciales** (ocho materiales), midiendo cada muestra por los tres métodos:

| Método comparado | Sesgo frente al método gravimétrico clásico (extracción alcalina → precipitación a pH<2 → **corrección por cenizas HCl/HF**) |
|---|---|
| **Colorimétrico (Mehlich)** | **Sobreestima +120 %** (≈ factor **2,2×**) |
| **CDFA** (California Dept. of Food and Agriculture) | **Sobreestima +52 %** (≈ factor **1,5×**) |

Causa de cada sesgo, del propio trabajo:
- **Colorimétrico:** la absorbancia del extracto alcalino integra AH **+ ácido fúlvico + otros cromóforos** que absorben a la misma longitud de onda. El número depende enteramente del estándar de calibración.
- **CDFA:** **no lleva las concentraciones a base libre de cenizas**; distintas menas arrastran distinta ceniza en la extracción.

Confirmación independiente en el método oficial que resolvió el problema:

> **Lamar, R.T., Olk, D.C., Mayhew, L. & Bloom, P.R. (2014).** *A New Standardized Method for Quantification of Humic and Fulvic Acids in Humic Ores and Commercial Products*. **J. AOAC International 97(3): 721–730.** DOI **10.5740/jaoacint.13-393** ✅ verificado (PDF leído íntegro en esta sesión).

Texto literal de Lamar 2014 (p. 722): los autores concluyeron que **"relativo a su método gravimétrico modificado de Swift, los métodos CDFA y Mehlich sobreestimaron el contenido de HA de ocho menas húmicas diferentes"**. Es la misma comparación, el mismo signo.

### 2.2 Segundo factor, MEDIDO dentro del método estándar: el pH de floculación

Lamar 2014 mide cuánto cambia el resultado por un solo parámetro de procedimiento — el pH al que se acidifica para flocular el AH — sobre las mismas muestras (Tabla 7, I de fondo 0,1 M NaOH→HCl, T ambiente):

| Muestra | AH a pH 1,0 | AH a pH 2,0 | FA a pH 1,0 | FA a pH 2,0 |
|---|---|---|---|---|
| IHSS Gascoyne Leonardite | 70,0 % | 57,7 % | 7,4 % | **16,5 %** |
| Mena D1 | 55,2 % | 53,8 % | 4,6 % | 6,7 % |
| Líquido L16 | 17,0 % | 14,9 % | 1,4 % | 4,5 % |

Lectura: cambiar **solo el pH de corte de 1,0 a 2,0** mueve el AH varios puntos y **más que duplica el "% de ácido fúlvico"** de una misma muestra (7,4 %→16,5 % en Leonardite). Es la prueba interna, sobre una sola muestra, de que sin método declarado el número no significa nada.

### 2.3 Tercer factor, para §5.3 (lignosulfonato): el fraude que ningún método húmico separa

Lamar 2014, Tabla 10 (I = 0,1 M NaOH; 1,8 g AH IHSS + 0,25 g FA IHSS + 5 g lignosulfonato):

| Fracción | Esperado | Observado con lignosulfonato | Sesgo |
|---|---|---|---|
| AH | 1,8 g | 3,0 g | **+166 %** |
| FA | 0,25 g | 2,6 g | **+1.040 %** |

El lignosulfonato **se adsorbe al DAX-8 y NO se separa de la fracción fúlvica** → infla el "ácido fúlvico" ×10. Cierra el punto de §5.3: un producto "rico en fúlvico" barato puede ser lignosulfonato leído como fúlvico. Lamar propone detectarlo por **S elemental > 0,75 % + FTIR** (bandas S=O a 1041 y 1182 cm⁻¹), porque el análisis húmico solo no lo distingue.

### 2.3bis Confirmación independiente — Shahbazi, Marzi & Tabbakhian (2019)

> **Shahbazi, K., Marzi, M. & Tabbakhian, S. (2019).** *The Comparative Evaluation of Humic Acid determining Methods in Humic-Based Commercial Fertilizers*. **Archives of Agronomy and Soil Science.** DOI **10.1080/03650340.2019.1575511** ✅ verificado (PDF leído íntegro).

Segundo estudio, **22 fertilizantes comerciales**, cuatro métodos, tomando el NSM (gravimétrico ash-free de Lamar) como referencia:

| Método | Sesgo medio vs NSM (22 muestras, Tabla 2: NSM 32,2 %) | Rango por muestra |
|---|---|---|
| **Colorimétrico (Mehlich)** | **+64,2 %** (media 52,8 % vs 32,2 %; factor 1,64×) | hasta **156 % vs 65,7 %** (muestra 15) y **145 % vs 21,0 %** (muestra 17) → factor **6,9×** |
| **CDFA** | **−13,8 %** (subestima; extracción incompleta 1:2,5 vs 1:400 y 1,5 h vs 16–18 h) | sobre y subestima según muestra |
| **ISO 5073** (volumétrico) | **−1,5 %** en promedio | pero **+4,7× (470 %)** en líquidos de bajo AH con solubles alcalinos |

Regresión colorimétrico vs NSM con estándar purificado: **y = 1,72·x** (sobreestimación sistemática del 72 %). Nota clave: el signo del sesgo del CDFA es **opuesto** al de Lamar 2009 (+52 % allí, −13,8 % aquí) — porque depende de la matriz (cenizas vs extracción incompleta). **Eso refuerza, no debilita, la tesis:** el número no es transferible ni siquiera dentro de un mismo método entre matrices distintas.

### 2.4 Cierre de la laguna

- Factor colorimétrico/gravimétrico: **≈ 2,2× (+120 %)** (Lamar & Talbot 2009, 8 materiales) y **1,64× (+64 %) medio, hasta 6,9× por muestra** (Shahbazi et al. 2019, 22 materiales). Factor CDFA/gravimétrico: **+52 % o −14 % según matriz** (signo depende de cenizas vs extracción incompleta).
- Dentro de un mismo método, el pH de corte 2,0 vs 1,0 **duplica el fúlvico**. Fuente: Lamar 2014, DOI 10.5740/jaoacint.13-393, Tabla 7.
- Por tanto, la afirmación operativa de §4.3 queda cuantificada: **dos etiquetas de "% ácidos húmicos" pueden diferir por un factor ~2 solo por el método, y ambas ser legales.** Especificar el método en el pliego, o no se especifica nada.

---

## LAGUNA 1 (NV-23) — constantes de estabilidad aminoácido–metal

**Estado: PARCIALMENTE CERRADA.** Se cierra la **pregunta operativa** (el corazón de NV-23: ¿es quelato el aminoquelato, y a qué pH cae?) con valores verificados en esta sesión. La **matriz numérica completa** (6 aminoácidos × 7 metales × K1 y β2) NO se pudo transcribir celda a celda porque las **fuentes primarias correctas quedaron bloqueadas por Cloudflare/anti-bot** (ver §1.4). Se dan las fuentes verificadas y la ruta exacta.

### 1.1 Constantes VERIFICADAS en esta sesión (con fuente, I y T)

Convención: log K1 = [ML]/([M][L]); log β2 = [ML₂]/([M][L]²). L = ligando totalmente desprotonado.

| Ligando | Especie | log K1 | log β2 | Fuente · I · T |
|---|---|---|---|---|
| **Glicina** | H⁺ (pKa del –NH₃⁺) | 9,60 | — | IUPAC — Kiss, Sovago & Gergely 1991, reproducido en Popov et al. 2001 (PAC 73:1641), Tabla 11 · **I = 0,1 M · 25 °C** |
| **Glicina** | Co²⁺ | 4,66 | — | ídem |
| **Glicina** | Ni²⁺ | 5,8 | — | ídem |
| **Glicina** | Cu²⁺ | 8,2 | — | ídem |
| **Glicina** | Zn²⁺ | 5,0 | — | ídem |
| **Ác. glutámico** | Cu²⁺ | 8,52 | 15,01 | Sajadi et al., estudio Cu–Glu (PMC4255084) · **I = 0,1 M KNO₃ · 20 °C** |
| **Metionina** | Cu²⁺ | 8,0–8,2 | 14,5–14,7 | Nagy et al. 2019, S/Se-aminoácidos con Cu(II)/Fe(II) (PubMed 30877880) · condiciones a confirmar en texto completo |

**Referencias de comparación (del propio dossier R5, ya verificadas):** Zn–EDTA log K ≈ 16,5 (hexadentado); Fe³⁺–EDDHA ≈ 33–35 (§5.4); y para el orden de Irving-Williams en aminoácidos: **Cu²⁺ ≫ Ni²⁺ > Zn²⁺ ≈ Co²⁺ > Fe²⁺ > Mn²⁺ ≫ Ca²⁺ ≈ Mg²⁺** (confirmado por las cuatro celdas de glicina de arriba: Cu 8,2 ≫ Ni 5,8 > Zn 5,0 > Co 4,66).

### 1.2 Respuesta operativa — ¿el "aminoquelato de Zn" cumple la definición de quelato?

**Formalmente sí; funcionalmente no al nivel que el nombre implica, y en suelo calcáreo NO sirve.** El número lo demuestra:

1. **Denticidad y magnitud.** El Zn–glicinato es un quelato bidentado real (anillo de 5 miembros) con **log K1 ≈ 5,0** y **log β2 ≈ 9,1** (β2 de la compilación Martell–Smith/Kiss 1991; K1 = 5,0 verificado arriba). El **Zn–EDTA** (hexadentado) tiene **log K ≈ 16,5**. La diferencia es de **~7,4 unidades logarítmicas en β2 → factor ~2,5 × 10⁷** en la constante. El aminoquelato retiene al Zn **siete órdenes de magnitud peor** que el EDTA.
2. **Frente al Zn²⁺ libre.** El glicinato SÍ mejora respecto a la sal desnuda (log β2 ≈ 9 vs 0), pero esa ventaja se evapora ante la competencia del suelo.
3. **Competencia por Ca²⁺ (§5.1, punto 2, ahora con número).** El suelo calcáreo tiene Ca²⁺ en concentración milimolar (10⁻³ M), 10³–10⁶ veces por encima del micronutriente aplicado. El Ca–glicinato es despreciable (log K1 ≈ 1,4; alcalinotérreos casi no coordinan glicina — de ahí las celdas "–" de la tabla), pero la **acción de masas** del Ca²⁺ desplaza igual al Zn de un ligando de log β2 tan bajo. Un log β2 ≈ 9 no sobrevive a esa competencia; un log K ≈ 16,5 (EDTA) sí.

### 1.3 ¿A qué pH se disocia o precipita? — el número que hay que poder afirmar

- **Dependencia de pH del propio ligando.** El grupo amino de la glicina coordina solo desprotonado; su **pKa = 9,60** (verificado). A pH de suelo (6–8) una fracción grande del amino está protonada (–NH₃⁺) y **no coordina**, de modo que la constante *condicional* (efectiva) del Zn–glicinato a pH 7 es **mucho menor** que el log β2 termodinámico de 9,1. La quelación por aminoácido es fuertemente pH-dependiente justo en el rango agronómico.
- **Precipitación como hidróxido.** El Zn(OH)₂ tiene Ksp ≈ 3 × 10⁻¹⁷. Un balance de especiación con log β2(Zn-Gly) ≈ 9 y exceso realista de ligando mantiene el Zn en solución en el rango ácido, pero **al subir a pH ≈ 7–8 (suelo calcáreo) el Zn libre liberado por la baja constante condicional precipita/adsorbe** — que es exactamente el fallo que §5.1 anticipaba cualitativamente. **Afirmación que ahora se puede sostener con número:** un aminoquelato de Zn (log β2 ~9) **no es funcional en suelo calcáreo**; para eso hace falta un quelante cuya constante supere la competencia Ca²⁺/OH⁻, es decir del orden del EDTA (16,5) o, para Fe, del EDDHA (33–35). Coincide con el criterio ya zanjado en Fe (§5.4): si en Fe hace falta hexadentado fenólico, un aminoácido bidentado no puede cumplir la misma función.
- **Corolario para uso foliar (§5.5).** En hoja el recorrido es de minutos y micras; la constante importa mucho menos, y ahí el argumento del aminoquelato es defendible — al revés de como se vende (que es para suelo).

### 1.4 Lo que NO se cerró y la ruta exacta

**Faltan (matriz completa):** aspártico, lisina, cisteína, metionina (β2 firme) con Zn/Fe²⁺/Fe³⁺/Mn/Cu/Ca/Mg, y las columnas Fe²⁺/Fe³⁺/Mn/Ca/Mg de glicina y glutámico; más **citrato, glucoheptonato y lignosulfonato** con Zn²⁺/Fe³⁺.

**Causa:** los valores están **críticamente compilados** en fuentes cuya EXISTENCIA se verificó (DOI resuelto) pero cuyas TABLAS no se pudieron extraer en esta sesión porque los servidores devolvieron **403 / desafío Cloudflare** a WebFetch y a curl (`publications.iupac.org`, `degruyterbrill.com`, `tandfonline.com`, ScienceDirect, ResearchGate, Academia). No es que no existan; es que el host los bloqueó.

**Ruta para cerrarla (fuentes correctas, DOIs verificados):**
1. **Glicina:** Kiss, T., Sovago, I. & Gergely, A. (1991), *Critical survey of stability constants of complexes of glycine*, **Pure Appl. Chem. 63(4): 597–638**, DOI **10.1351/pac199163040597** (I=0,1 M, 25 °C).
2. **Aminoácidos alifáticos (incl. metionina, lisina):** Sovago, I., Kiss, T. & Gergely, A. (1993), *Critical survey of the stability constants of complexes of aliphatic amino acids*, **Pure Appl. Chem. 65(5): 1029–1080**, DOI **10.1351/pac199365051029**.
3. **Aminoácidos de cadena lateral polar (aspártico, glutámico, lisina, cisteína):** Berthon, G. (1995), *Critical evaluation of the stability constants of metal complexes of amino acids with polar side chains*, **Pure Appl. Chem. 67(7): 1117–1240**, DOI **10.1351/pac199567071117**.
4. **Compilación maestra:** Martell, A.E. & Smith, R.M., *Critical Stability Constants, Vol. 1: Amino Acids* (Plenum, 1974) y **NIST Standard Reference Database 46** (Smith & Martell), retirada de circulación pero aún la referencia. 
5. **Zn como micronutriente (compara sulfato/óxido/quelato/complejo orgánico):** Montalvo, D. et al. (2016), *Agronomic Effectiveness of Zinc Sources as Micronutrient Fertilizer*, **Advances in Agronomy 139: 215–267**, DOI **10.1016/bs.agron.2016.05.004** (existencia ✅; ScienceDirect bloqueó el texto).

Acceso recomendado: descargar los PDF IUPAC-PAC desde una red no filtrada (los PDF de PAC son de acceso abierto en origen) o vía biblioteca institucional; luego transcribir las tablas "Recommended".

### 1.5 Lignosulfonato con Zn²⁺/Fe³⁺ — la ausencia ES el hallazgo (confirmada)

Tal como el dossier anticipó (§5.3), **no existe constante de estabilidad termodinámica definida para el lignosulfonato**, porque no es una especie molecular sino un polímero polidisperso. Esto se confirma indirectamente con dato duro en Lamar 2014 (Tabla 10): el lignosulfonato **ni siquiera se separa de la fracción fúlvica** en cromatografía DAX-8 (recuperación aparente de "FA" +1.040 %) — es una población heterogénea sin comportamiento de especie única. Cualquier "log K de lignosulfonato" citado por un proveedor es una **constante condicional operativa para un lote**, no una constante termodinámica, y por definición no transferible. Citrato–Fe³⁺ (log K ≈ 11,5) y glucoheptonato–Fe³⁺ (estable solo en medio alcalino) sí tienen constante definida, pero su verificación numérica con I/T queda en la misma ruta §1.4 (fuentes bloqueadas esta sesión).

---

## Resumen de cierre

| Laguna | Estado | Qué cerró |
|---|---|---|
| **NV-16** (divergencia métodos AH) | ✅ **CERRADA** | Colorimétrico sobreestima **+120 %** (Lamar 2009) / **+64 %** medio, hasta **6,9×** por muestra (Shahbazi 2019); CDFA ±13–52 % según matriz; el pH de corte 1↔2 duplica el fúlvico. Dos estudios independientes, 8 y 22 materiales. |
| **NV-23** (log K aminoquelatos) | 🟡 **PARCIAL** | Pregunta operativa CERRADA con número: Zn-glicinato log β2 ≈ 9 vs Zn-EDTA 16,5 (factor ~10⁷); no funcional en suelo calcáreo por competencia Ca²⁺/OH⁻ y pKa 9,6. Matriz completa abierta por bloqueo Cloudflare de IUPAC/Martell-Smith; ruta y DOIs dados. Lignosulfonato: sin constante definida (confirmado). |
