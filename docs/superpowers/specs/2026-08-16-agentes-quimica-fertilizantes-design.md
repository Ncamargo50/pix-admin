# Familia de agentes: química de fertilizantes, fisiología y nutrición

Fecha: 2026-08-16
Estado: diseño aprobado por el usuario (2026-08-16), pendiente de implementación.

## Problema

Pixadvisor formula, audita y recomienda fertilizantes líquidos y granulados —propios y de
terceros— sin una base de criterio química escrita. Hoy ese conocimiento vive en la cabeza
del usuario y en skills genéricas de marzo 2026 (`recomendacion-fertilizacion`,
`interpretacion-suelos`, `metabolitos-bioactivos`, `biotech-microbianos`) que calculan dosis
pero no responden las preguntas de formulación: qué sal entra, a qué pH, cuánto aguanta sin
precipitar, si el quelato es real, y si la etiqueta puede hacer lo que promete.

## Objetivo

Seis agentes de dominio más un auditor adversarial, disponibles globalmente, capaces de:

1. **Formular** producto propio líquido y granulado, con criterio de **costo por kg de
   nutriente**, no por litro de producto.
2. **Auditar** formulaciones de terceros a partir de su etiqueta o ficha técnica.
3. **Recomendar** la aplicación a campo: fertirriego, inyección al suelo, foliar y mezcla de
   tanque.

Restricción de diseño declarada por el usuario: las soluciones deben ser **prácticas y de bajo
costo** para el productor.

## No objetivos

- No se recalcula dosis por meta de rendimiento: eso ya lo hace la skill
  `recomendacion-fertilizacion`.
- No se interpreta análisis de suelo: eso lo hace `interpretacion-suelos`.
- No se cubren microorganismos vivos: eso lo hace `biotech-microbianos`.
- No se cargan precios de proveedores. Ver "Política de costos".

## Arquitectura

Siete archivos markdown con frontmatter de agente en `C:\Users\Usuario\.claude\agents\`,
junto a los cinco agentes de teledetección ya existentes. Cada uno es invocable solo; se
componen cuando el trabajo lo pide.

| Agente | Dueño de | Frontera |
|---|---|---|
| `formulador-fertilizantes-liquidos` | Catálogo de materias primas, solubilidad, calor de disolución, fuerza iónica, Ksp, ventanas de pH, quelatos **sintéticos** (EDTA/DTPA/EDDHA/HEDTA/IDHA/EDDS), orden de carga, temperatura de cristalización, estabilidad en estante | No dice qué necesita el cultivo ni cuánto aplicar |
| `quimica-fertilizantes-granulados` | Rutas de producción, complejo vs blend vs compactado, SGN/UI y segregación, CRH de mezclas, incompatibilidad física, inhibidores (NBPT/DCD/DMPP), liberación controlada, índice salino y colocación, organominerales | Termina donde el gránulo se disuelve |
| `fisiologo-nutricion-vegetal` | Flujo masal/difusión/intercepción, cinética de absorción, NH₄⁺:NO₃⁻ y pH de rizósfera, movilidad floemática, penetración cuticular y punto de delicuescencia, antagonismos, ventana fenológica por cultivo | No calcula dosis por meta de rendimiento |
| `bioestimulantes-organicos` | Hidrolizados proteicos (ácida vs enzimática, libres vs totales, L vs D), húmicos/fúlvicos, algas, betaína, ALA, quitosano, Si, y la **aminoquelación / complejos orgánicos** | No toca microorganismos vivos |
| `fertirriego-solucion-nutritiva` | Análisis de agua y acidulación, balance meq/L, CE objetivo, tanques A/B/C, sistemas de inyección, goteo y taponamiento, fraccionamiento, inyección al suelo | No formula el concentrado |
| `auditor-formulaciones` | Adversarial. Intenta reprobar una fórmula, propia o ajena | No propone la alternativa |

### El corte de la quelación

Es el punto donde dos agentes podrían contradecirse sobre la misma molécula, así que queda
fijado:

- **Quelato sintético** (EDTA, DTPA, EDDHA, HEDTA, IDHA, EDDS) → `formulador`. Es química de
  tanque: constante de estabilidad, ventana de pH, desplazamiento por Ca²⁺.
- **Aminoquelato, complejo orgánico, lignosulfonato, glucoheptonato, citrato, húmico** →
  `bioestimulantes-organicos`, como estudio propio. Es el terreno donde "complejo" y "quelato"
  se usan como sinónimos comerciales sin serlo.

## El auditor

Replica el patrón de `validador-ciego`: su producto es un veredicto **APROBADO / RECHAZADO /
NO CONCLUYENTE**, y NO CONCLUYENTE es un resultado legítimo. Chequeos obligatorios:

1. **Aritmética de etiqueta y balance iónico** — ¿los % declarados salen de las sales
   nombradas? ¿cationes = aniones en meq?
2. **Saturación a 5 °C, no a 20 °C** — la fórmula que se disolvió en el laboratorio y precipitó
   de noche en el camión. KNO₃ y urea disuelven endotérmicamente: el tanque se enfría solo.
3. **Incompatibles duros** — Ca²⁺ con sulfato y con fosfato, con su Ksp. De ahí sale la regla de
   tanques A/B, que no es opcional.
4. **¿El quelato es quelato?** — sin agente quelante nombrado y fracción quelatada declarada no
   hay reclamo de quelato. Y el agente debe corresponder al pH del suelo: Fe-EDTA a pH 7 ya no
   existe.
5. **Aritmética de dosis** — 1 L/ha de un producto al 5 % de Zn son 50 g Zn/ha. ¿Alcanza para lo
   que promete?
6. **Cuánto se paga por agua** — costo por kg de nutriente contra la sal commodity equivalente.
7. **¿La evidencia citada existe?** — misma regla que en teledetección.

Chequeos propios del granulado: **segregación** (SGN/UI de los componentes del blend) y **CRH
de la mezcla**, que es más baja que la de cualquier componente.

## Reglas transversales (van en los siete)

- Ningún número de solubilidad, Ksp o constante de estabilidad sale sin **temperatura y pH**
  (y fuerza iónica cuando aplique). Sin eso no es un número.
- **Umbral absoluto no transfiere** sin declarar método y extractante. Regla ya establecida en
  `feedback_umbrales_absolutos_no_transferibles`.
- Distinguir siempre **ensayo de campo con testigo** de **ensayo en maceta** de **afirmación de
  folleto**.
- Cada agente cierra con **"LO QUE NO SE PUEDE"**, con el número que lo demuestra.
- "No lo sé" es una salida válida y preferible a inventar. Regla ya establecida en
  `feedback_evidencia_citada_debe_existir`.
- Español; "soya" en documentos de Bolivia (`feedback_bolivia_soya_terminology`).

## Política de costos

Decisión del usuario: **catálogo genérico + preguntar**. Cada agente lleva el catálogo técnico
completo y el costo **relativo** típico por kg de nutriente, y se **niega** a afirmar "esta es
la más barata" sin los precios reales del usuario. Cuando no los tiene, lo declara en vez de
estimar. Si más adelante el usuario quiere un CSV de precios editable, se agrega sin cambiar
los agentes.

## Fuente del contenido

Los agentes no se escriben de memoria. Siete dossiers de investigación con fuente verificable
se generan primero en `_agentes_quimica\investigacion\`:

| Dossier | Alimenta a |
|---|---|
| `R1_sales_solubilidad.md` | formulador |
| `R2_quelatos_sinteticos.md` | formulador, auditor |
| `R3_compatibilidad_mezclas.md` | formulador, fertirriego, auditor |
| `R4_fisiologia_nutricion.md` | fisiólogo |
| `R5_bioestimulantes_aminoacidos.md` | bioestimulantes, auditor |
| `R6_fertirriego_solucion_nutritiva.md` | fertirriego |
| `R7_granulados.md` | granulados, auditor |

Cada dossier exige: fuente por afirmación (autor/año + DOI verificable o publicación
institucional con URL), tabla separada de **NO VERIFICADO** declarando qué se buscó, y sección
de **LO QUE NO SE PUEDE**. Lo que no se pueda verificar sale marcado como no verificado o no
sale.

## Criterio de aceptación

1. Los siete archivos existen en `~/.claude/agents/` y cargan (frontmatter válido: `name`,
   `description`, `tools`, `model`).
2. Cada `description` permite decidir cuándo invocarlo sin leer el cuerpo.
3. Ninguna afirmación numérica sin fuente ni sin sus condiciones (T, pH, fuerza iónica).
4. Cada agente tiene su sección "LO QUE NO SE PUEDE".
5. Sin solapamiento: la misma pregunta no cae en dos agentes con respuestas distintas. En
   particular, la quelación respeta el corte de arriba.
6. Los dossiers de investigación quedan comiteados en el repositorio: el agente cita evidencia
   que existe y se puede abrir.
7. Prueba funcional: el auditor recibe una etiqueta comercial real y produce un veredicto con
   al menos un defecto medible o un NO CONCLUYENTE justificado.

## Riesgos

- **Alucinación de DOIs y constantes.** Es el riesgo principal y el motivo de la fase de
  investigación separada con tabla de NO VERIFICADO.
- **Solapamiento con las skills de marzo.** Mitigado con las fronteras declaradas; cada agente
  deriva explícitamente a la skill correspondiente en lugar de rehacer su trabajo.
- **Números sin condiciones.** Una solubilidad sin temperatura o un log K sin fuerza iónica es
  el defecto que hace inútil una tabla. Va como regla transversal y como criterio de aceptación.
