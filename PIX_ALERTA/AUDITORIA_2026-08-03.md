# Auditoría del 2026-08-03 — qué de la investigación aguanta y qué no

Auditoría de la investigación `../INVESTIGACION_TELEDETECCION_CULTIVOS_2026.md` y de lo que se
implementó a partir de ella. **Todo lo que sigue está medido**; lo que no se pudo medir está
marcado como tal.

Método: para cada hallazgo de la investigación, dos preguntas separadas —
**(a) ¿es verdad?** y **(b) ¿aplica a ESTE motor?** — porque son independientes, y la segunda es
la que falla más seguido.

---

## Resumen: 6 hallazgos, 2 contra el propio trabajo de la investigación

| # | Hallazgo | Veredicto |
|---|---|---|
| **H1** | kNDVI **no aplica** a este motor, y usarlo en la compuerta sería un cambio no calibrado | ⛔ Se descarta como mejora |
| **H2** | La textura GLCM **dilata el foco 2,5-4,2x** | ⚠️ Sirve para detectar, **no** para delimitar |
| **H3** | **Sentinel-1D NO mejoró la revisita** sobre SA/SF | ⛔ La premisa del plan era falsa |
| **H4** | El radar **no puede correr** en TRIGO: exige cohorte ≥8, hay 2 lotes | ⛔ No implementable hoy |
| **H5** | **Tercera fuga del ciego**: la forma del polígono delataba la clase | ✅ Corregida y verificada |
| **H6** | El **hueco máximo** de S1 subió de 12 a 18 días | 📄 Corrige el dato del contrato |

---

## H1 — kNDVI no aplica a este motor

**¿Es verdad la ciencia?** Sí. Camps-Valls et al. 2021 (*Science Advances*,
doi:10.1126/sciadv.abc7447) es sólido: kNDVI resiste mejor la saturación y correlaciona mejor con
GPP y SIF que NDVI y NIRv.

**¿Aplica acá?** **No**, por tres razones en orden de peso:

1. **NDVI no es un eje del criterio.** Los ejes son NDMI y NDRE. El NDVI solo alimenta la
   compuerta de dosel. Cambiar el NDVI no toca la detección.
2. **La saturación no le pega a este motor.** El criterio nunca usa valores absolutos: compara
   cada píxel contra su propia trayectoria y contra su cohorte. La saturación arruina *umbrales
   absolutos*, y acá no hay ninguno.
3. **Usarlo en la compuerta sería un cambio no calibrado.** MEDIDO sobre 20.000 píxeles
   sintéticos de trigo:

   | | resultado |
   |---|---|
   | Correlación de **rangos** NDVI ↔ kNDVI | **1,000000** (orden idéntico) |
   | Píxeles que **cambian de lado** de la compuerta | **1,29%** |
   | NDVI equivalente al corte | pasa de **0,6465 a 0,6510** |

   FVC normaliza entre percentiles y después **corta en un valor**: no es invariante a
   transformaciones monótonas **no lineales**. Mover el umbral 1,29% sin razón positiva es
   exactamente lo que `config.py` prohíbe.

**Qué se hizo:** kNDVI queda como banda de archivo en la serie, con la afirmación falsa corregida
en `series.py` y fijada por `tests/test_textura_y_kndvi.py::test_kndvi_NO_es_invariante_en_la_compuerta_de_dosel`.

> **Error de la investigación original:** el informe presentaba kNDVI como "reemplazo directo,
> gratis, de una línea de código". Es cierto en general y **falso para este motor**. La
> investigación no separó "es verdad" de "aplica".

---

## H2 — La textura dilata el foco

**¿Es verdad?** Sí: VIs + textura llegan a R² 0,78-0,84 en biomasa, y la textura es ortogonal por
física a la reflectancia. Sigue siendo el mejor candidato a segundo eje independiente.

**¿Aplica?** **Con una restricción medida que la investigación no anticipó.** Toda medida de
ventana contamina a los vecinos: un píxel anómalo altera la textura de los 8 que lo rodean.

MEDIDO con la MMU real del motor (`test_la_textura_dilata_el_foco_y_por_eso_no_puede_delimitar`):

| foco real | píxeles afectados por GLCM 3×3 | factor |
|---|---|---|
| 5 px = **0,20 ha** (la MMU exacta) | 21 px = **0,84 ha** | **×4,2** |
| 12 px = 0,48 ha | 30 px = 1,20 ha | ×2,5 |

**La consecuencia hay que separarla en dos:**
- **Detectar** ("¿hay algo raro acá?") — la dilatación no invalida nada; el foco sigue dentro de
  la mancha.
- **Delimitar** ("¿de cuántas hectáreas?") — **no sirve**. El área que se le informa al cliente y
  la MMU de 0,20 ha tienen que seguir saliendo de los ejes espectrales.

**Qué se hizo:** documentado como límite 5 de `series._textura`, con test. La textura sigue
**apagada en producción** y solo se calcula cuando un arnés la declara como eje.

---

## H3 — Sentinel-1D no mejoró la revisita ⛔

Esta es la refutación más importante de la auditoría, y va contra lo que este mismo asistente
escribió en el plan.

MEDIDO con `medicion/disponibilidad_s1d.py` sobre los dos sitios, corte 1-may-2026:

| | antes de S1D | después de S1D |
|---|---|---|
| Pasadas | 4 en 25 días (1 c/6,2 d) | 10 en 79 días (1 c/**7,9** d) |
| Órbitas | **1** (24, descendente) | **1** (24, descendente) |
| Hueco **mediano** | 12 d | **11 d** |
| Hueco **máximo** | 12 d | **18 d** |

**La revisita de 6 días de la constelación no existe sobre estos lotes.** Sigue habiendo una sola
órbita relativa, descendente. Es exactamente lo que `radar.py` ya había medido sobre HDS
(oct-2025 a ene-2026) — y que se suponía superado.

> **Error del plan:** `PROYECTO_2026_2027.md` presentaba S1D como "la palanca de ~5x" y ponía
> re-medirlo como Fase 1. La medición se hizo y **la palanca no está ahí**. El plan de trabajo
> derivado de esa premisa queda sin base.

**Lo que sí es cierto y quedó medido:** el radar (S1 en general, no S1D en particular) aportaría
**+15,4 puntos** en Santo Antonio y **+23,1 puntos** en São Francisco de dékadas con alguna
observación (S2∪S1 = 92,3% contra 76,9% y 69,2% de S2 solo). Eso es real, y es el argumento para
seguir intentándolo — por otra vía.

---

## H4 — El radar no puede correr en TRIGO ⛔

MEDIDO corriendo `radar.cambio_estructural` sobre São Francisco:

```
[S1] órbita 24 DESCENDING: 12 escenas → 24 filas | 2 lotes | 12 fechas
MIN_LOTES_COHORTE_RADAR = 8  |  lotes disponibles = 2
   SAO_FRANCISCO-01   ('SIN DATO RADAR', 9)
   SAO_FRANCISCO-02   ('SIN DATO RADAR', 9)
```

**El radar extrae datos correctamente pero no puede concluir nada**, y la guarda funciona como
debe: con menos de 8 lotes el residuo contra la mediana de la cohorte es ~0 por construcción, el
z se va al piso y saldría **SIN CAMBIO garantizado pase lo que pase en el campo**. Reportar eso
sería la falsa tranquilidad que todo el paquete existe para evitar.

**¿Y sin cohorte, contra su propia trayectoria?** No sirve: sin cohorte no hay corrección por
efectos comunes, y **una lluvia que moja todos los lotes por igual se confunde con un evento del
lote**. La cohorte es justamente lo que separa las dos cosas.

**¿Y con cohorte regional?** Es la vía correcta, y ya está medida — pero
`COHORTE_REGIONAL_2026-07-29.md` §5 declara explícitamente que **no se implementó**, y enumera
tres requisitos previos: alineación fenológica, verificación de plausibilidad temporal, y tasa de
falsa alarma propia. Ninguno existe todavía.

**Decisión: el radar NO se conecta a `solo_focos` en esta versión.** Hacerlo produciría
`SIN DATO RADAR` en el 100% de los casos (inútil) o exigiría una capa que está medida y
declarada como no implementable todavía (deshonesto).

---

## H5 — Tercera fuga del ciego ✅ corregida

MEDIDO sobre la salida real `validacion_SAO_FRANCISCO_2026-08-03.geojson`:

| | vértices | forma |
|---|---|---|
| Foco | **15** | polígono vectorizado del ráster, irregular |
| Controles (×4) | **25** | círculo generado de 24 lados |

Y `PIX_SCOUT/app/js/map.js` (`ringFor`) **dibuja ese anillo** cuando el punto lo trae. El técnico
veía círculos perfectos para los controles y una mancha irregular para el foco: después de una
ronda sabe cuál es cuál sin la clave, y a partir de ahí registra distinto — el sesgo de
verificación que la campaña entera existe para evitar.

Las dos fugas anteriores fueron de **propiedades** y se taparon con la lista blanca
`CAMPOS_DEL_PUNTO`. Esta es de **geometría**, que viajaba tal cual.

**Corregido en el DATO, no en la app** (`controles._geometria_uniforme`): todos los puntos del
paquete ciego salen como el mismo tipo de círculo, con el radio derivado de su área declarada. Si
el ciego dependiera de que la app no dibuje la forma, cualquiera que abra el GeoJSON en QGIS
volvería a verla.

**Verificado sobre salida real:**

```
ANTES     focos: [15]  controles: [25]   -> DELATA
DESPUÉS   focos: [25]  controles: [25]   -> INDISTINGUIBLE
```

Fijado por 4 tests nuevos en `tests/test_controles.py`, incluidos dos que verifican que el punto
uniforme sigue cayendo sobre el foco original y que el radio respeta el área declarada.

> **Por qué ningún test lo detectaba:** los fixtures usaban el **mismo triángulo** para foco y
> control. Un fixture que no se parece a la salida real no prueba la salida real.

---

## H6 — El hueco máximo de S1 subió a 18 días 📄

`PLAN_A_PRODUCCION.md` puerta 5.1 pide declarar el hueco máximo en el contrato. El número de
radar que estaba documentado era **12 días** (mediano y máximo, medido sobre HDS).

MEDIDO ahora sobre SA/SF post-S1D: mediano **11 d**, **máximo 18 d**.

Un contrato que prometa continuidad radar cada 12 días **incumple**. El número a declarar es 18.

---

## Qué de la investigación sigue en pie

No todo se cayó. Lo que la auditoría **no** refutó y sigue siendo aplicable:

| Hallazgo | Estado |
|---|---|
| Los umbrales absolutos no transfieren | ✅ Ya es doctrina de la casa, reforzado |
| La fenología satelital tiene RMSE 8-13 días en trigo | ✅ Justifica cohorte en vez de estadio |
| La textura es el único candidato ortogonal por física | ✅ Con la restricción de H2 |
| Los foundation models se degradan al cambiar de región | ✅ Sin refutar; refuerza el valor de las verdades de campo |
| SIF es inviable a escala de lote | ✅ Sin refutar |
| Declarar exactitud y latencia como producto (patrón CDL/OpenET) | ✅ Sin refutar; es la estrategia |
| El radar aporta +15 a +23 puntos de cobertura | ✅ **Medido acá**, pero no cosechable todavía |

---

## Lección de método

Dos de los seis hallazgos son errores de la propia investigación, y los dos tienen la misma
causa: **confundir "es verdad" con "aplica"**. kNDVI y S1D son ciencia correcta y noticias reales;
ninguno de los dos sirve en este motor, sobre estos lotes, hoy.

La investigación bibliográfica dice qué es posible. Solo la medición sobre el dato propio dice qué
es aplicable. **Ninguna de las dos reemplaza a la otra, y el orden importa: medir antes de
implementar, no después.**
