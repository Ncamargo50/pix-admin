# PIX ALERTA — Metodología recomendada de construcción

Fecha: 2026-07-24. Se apoya en `AUDITORIA_2026-07-24.md` (evidencia medida) y sustituye al
orden de construcción de `ESPECIFICACION.md` §5.

---

## La decisión de fondo

`ESPECIFICACION.md` describe la arquitectura de un **detector** cada vez más fino: mejor máscara,
mejor estratificación, mejor test espacial, persistencia temporal, prior meteorológico. Es una buena
descripción de un detector. El problema es que la auditoría muestra que **el cuello de botella no
está en el detector**:

- El gatillo espacial actual marca ~30% del campo hagas lo que hagas con él (medido).
- No hay una sola observación de campo contra la cual saber si eso está bien o mal.
- No hay fecha de siembra, así que el Paso 2 no se puede implementar.
- El entregable que el cliente consume —la lista de lotes— no existe en el código.

Afinar el detector antes de tener con qué medirlo produce un motor más sofisticado y exactamente
igual de indemostrable. **La metodología correcta es invertir el orden: construir primero el sistema
de medición, y mantener el detector en lo más simple que sea defendible hasta que el dato mande.**

Esto no contradice la especificación, la reordena. Todo lo de §2 sigue siendo el destino; lo que
cambia es qué se construye primero y con qué criterio se acepta cada pieza.

---

## Principio 1 — La unidad es el LOTE, y la columna vertebral es una tabla, no un ráster

Hoy el motor opera sobre el polígono de la hacienda entera y produce rásters y focos. El producto
que se vende es *"a qué 10 lotes voy esta semana"*. Son cosas distintas y la segunda no existe.

**La pieza a construir primero es una tabla de serie temporal por lote y por fecha.** Una fila por
(lote, fecha, índice). Nada más.

Por qué esto primero, y no como subproducto:

- Es lo único que hace posible el eje temporal, que es **la única vía de especificidad demostrada**
  con bandas anchas (spec §9: 84,6% multitemporal vs 76,9% monoescena).
- Es lo único que permite EWMA, tendencias, y comparar un lote contra sí mismo.
- Es lo que hace baratísima la parte cara: `reduceRegions` sobre 220 polígonos devuelve un CSV, no
  requiere bajar un solo ráster, no toca el límite de 48 MB, y corre en segundos.
- HDS ya tiene 3.094 filas de exactamente esta forma (221 lotes × 14 meses) con `lote_id` que cruza
  220/221 contra el maestro. **La prueba de concepto ya está hecha sin querer.**
- Es lo que se le muestra al cliente y lo que se archiva para la validación.

El ráster y los focos intra-lote pasan a ser un **segundo nivel, calculado solo para los top-K
lotes** a los que el técnico realmente va. Es donde el costo computacional se justifica.

Reutilizar el esquema de `pixadvisor_lots.db` (POC_FIELD_BOUNDARY) en vez de inventar otro: ya tiene
versionado y `lot_history`.

---

## Principio 2 — Cambiar la hipótesis nula: del vecino al propio pasado

Este es el cambio técnico central.

Gi\* pregunta *"¿este píxel es más bajo que sus vecinos?"*. En un lote agrícola la respuesta es
siempre sí en algún lado, porque la nula de aleatoriedad espacial es falsa por construcción. Medido:
33,3% del campo marcado; estratificando por suelo, 30,3%; con los valores barajados, 0,0%. El test
funciona perfecto y responde una pregunta que no sirve. El resultado es una **cuota del 30%**, que es
lo mismo que hacen los cuantiles que la Decisión 3 prohíbe, solo que con más matemática encima.

La nula que sí es informativa es **temporal**: *"¿este lote se está apartando de su propia
trayectoria, comparado con lo que hicieron los lotes de su misma cohorte?"* Esa nula puede ser
verdadera —un lote sano sigue su curva— y por lo tanto rechazarla significa algo.

En la práctica:

- **Nivel 1 (ranking de lotes):** residuo del lote respecto de la trayectoria esperada de su cohorte,
  acumulado con EWMA. El estadístico es el residuo estandarizado, no el rank. Un lote puede no estar
  en el top si nadie está mal.
- **Nivel 2 (foco intra-lote, solo en los priorizados):** ahí sí Gi\*, pero sobre el **campo de
  residuos temporales**, no sobre el índice crudo. Un coldspot de residuo sí tiene nula plausible:
  la anomalía no tiene por qué estar espacialmente agrupada si no hay nada.

Conservar de la implementación actual todo lo que ya está bien: permutación condicional, FDR
adaptativo, α declarado, barrido de sensibilidad, semillas fijas. Lo que cambia es **sobre qué
variable se aplica**.

Corolario: bajar el Mahalanobis de 7 features a 2 ejes, como manda la Decisión 1 y confirma la
medición (dimensionalidad efectiva 1,87–2,40). Hoy df=7 contra df=2 mueve la superficie roja de 113
a 772 ha sobre el mismo campo el mismo día.

---

## Principio 3 — El sistema tiene que poder decir "no pasa nada"

Tres lugares donde hoy no puede, y los tres hay que arreglarlos antes que cualquier índice nuevo:

1. **El motor**: el gatillo del 30% nunca devuelve campo limpio. Con la nula temporal, sí.
2. **La app de campo**: PIX_SCOUT no tiene salida "nada encontrado". Sin registro negativo no hay
   falsos negativos y §4 es inejecutable.
3. **El ranking**: un rank siempre tiene un primero. El anclaje absoluto de `prioridad_muestreo.py`
   —que ya está escrito y nadie llama— es lo que permite entregar "los 10 primeros, pero ninguno
   supera el umbral de atención".

Un informe que dice "no vi nada" conserva la confianza. Es la misma lógica que la spec ya aplica a
la cadencia, extendida al criterio.

---

## Principio 4 — Prometer entrega, con la calidad rotulada en el propio entregable

Medido: 48,2% de las dekadas tienen escena óptica útil a escala de lote. Febrero, 33%.

La escalera de tres estados del pipeline actual es correcta y hay que conservarla, pero el rótulo
tiene que viajar **dentro del dato**, no solo en el PDF: cada fila de la tabla lleva su calidad
(pleno / parcial / radar / sin observación) y el ranking declara con qué se construyó. Con S2 ∪ S1
se cubre el 87,3% de las dekadas; el 13% restante es "sin observación válida" y hay que decirlo.

Esto además protege la validación: sin la etiqueta de calidad en la fila, en un año no se va a poder
distinguir un falso negativo real de una dekada nublada.

---

## Orden de construcción

Reemplaza a `ESPECIFICACION.md` §5. Cada fase cierra con algo utilizable.

### Fase 1 — Pedir la planilla de siembra (no es software)

La fecha de siembra no existe en ningún archivo, y la plantilla para capturarla lleva meses vacía. Es
el único insumo del Paso 2 y la hacienda ya lo tiene. Mientras tanto, derivar cohorte estimada por
quiebre de la serie NDVI y rotularla como estimada — nunca presentarla como declarada.

Sin esto, el Paso 2 de la especificación no es implementable y la cohorte del Paso 3 tampoco.

### Fase 2 — La tabla de series por lote

`reduceRegions` sobre los polígonos que ya existen, persistiendo (lote_id, fecha, índice, calidad,
cobertura válida). Empezar por HDS, que es la única hacienda con ID estable, zonificación y 14 meses
de historia.

Dos ejes de dosel, no siete: uno de humedad y uno de senescencia (Decisión 1, confirmada por
medición). Retrollenar con el histórico disponible.

Entregable: el ranking de lotes por residuo EWMA. **Este ya es el producto vendible**, sin un solo
ráster.

### Fase 3 — Cerrar el lazo de retorno en PIX_SCOUT

Es el activo más avanzado y la spec ni lo lista. Está al ~65%. Falta, en orden de dificultad:

1. **Estructurar los 26 umbrales MIP** — convertir prosa en objetos computables (valor, unidad,
   operador, condición fenológica) y agregar el campo `conteo`. Es curaduría agronómica, no código, y
   es lo que hace que `supera_umbral` pase de opinión a cálculo. Los otros 97 quedan
   `VERIFICAR_LOCAL` por diseño y hay que decirlo.
2. **Modo ciego de captura** — es el conflicto de fondo: la app entera está construida para mostrar la
   priorización satelital. Se necesita un modo distinto, no ocultar un campo.
3. **Salida "nada encontrado"** — sin esto §4 no se puede ejecutar.
4. `punto_id` estable emitido desde el pipeline (hoy 50 de 101 colisionan), `lote_id`, `observacion`,
   `estrato_asignado` guardado y no mostrado.
5. Crear la tabla en Supabase y rellenar `config.js` — la cola cliente ya está escrita y probada.

### Fase 4 — Focos intra-lote solo para el top-K, con la nula temporal

Gi\* + FDR sobre el campo de residuos, agregado a 20 m, Mahalanobis de 2 ejes. Aquí sí hace falta
ráster, y solo para los lotes a los que el técnico va.

Requisito previo del pipeline: escribir el bootstrap de máscaras que hoy no existe (`ambientes.tif`
/ `strata.tif` vienen de otro proyecto como binarios opacos). Sin eso no hay hacienda nueva posible.

### Fase 5 — Una campaña de validación honesta

Con el protocolo de `ESPECIFICACION.md` §4, que es correcto y no hay que tocar: estratos rojo /
amarillo / **verde**, sorteo aleatorio dentro de cada uno, técnico a ciegas, probabilidades de
inclusión guardadas, precisión@K + PR-AUC + prevalencia declarada.

Solo después de esto tiene sentido el Paso 6 (prior meteorológico) y cualquier índice nuevo.

---

## Qué NO construir todavía

- **Prior meteorológico.** La spec ya lo marca como hipótesis sin respaldo empírico. Y el precedente
  propio es malo: en el motor de caña, ERA5 a 11 km degeneró a 8 valores únicos en 131 lotes y aun
  así pesaba 0,20 en el composite.
- **Más índices.** La dimensionalidad efectiva es ~2. Un índice nuevo agrega columnas, no información.
- **Multicultivo simultáneo.** Los umbrales de dosel están anclados a una escena de trigo de dos
  haciendas y no transfieren. Re-anclar cuesta 1-2 semanas de campaña **por cultivo**, y es tiempo
  agronómico. Empezar por el cultivo con más evidencia y más historia propia.
- **Sao Francisco, Campo Verde y Santo Antonio como pilotos.** No tienen geometrías de lote. Las dos
  haciendas que hoy corren en producción no tienen lotes.

---

## Arreglos del pipeline actual que convienen igual

Independientes de PIX ALERTA, sobre el sistema que ya corre:

1. `history.json` quedó inconsistente con el baseline re-sembrado. El primer informe óptico completo
   va a mostrar una caída de −1,5 ha en SA y −2,9 ha en SF que es cambio de método, no agronomía.
2. `check_new` toma solo la escena más reciente: si el cron se cae, una escena limpia se pierde para
   siempre. Falta `--force`/`--date`.
3. El PDF del cliente describe *"estrato de siembra"* y *"P95 de la cohorte"*, método que el motor no
   usa desde el 22-jul.
4. Los tres silencios del motor (`n<200`, Mahalanobis degenerado, `cire_ref` ausente) reportan "sin
   anomalías", que es indistinguible de "el motor no pudo correr".

---

## El argumento de venta no cambia

Sigue siendo el de la especificación: **"hago que el MIP sea aplicable en tus 200 lotes"**, con el
ahorro de R$ 270/ha respaldado por Embrapa y no por Pixadvisor.

Lo que esta metodología agrega es que el ranking de lotes —la parte que ese argumento realmente
necesita— se puede entregar en la Fase 2, antes y más barato que el mapa de focos, que es la parte
cara y la que menos respaldo tiene.
