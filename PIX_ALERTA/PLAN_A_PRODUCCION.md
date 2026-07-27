# PIX ALERTA — Plan para dejar la herramienta fiable y aplicable a campo

Fecha: 2026-07-24. Complementa a `METODOLOGIA_RECOMENDADA.md` (el *qué* y el *orden*).
Este documento define **qué significa "listo"** para cada pieza, con una prueba que se pasa o no se
pasa, y el calendario que las ata.

---

## 0. Qué se puede prometer y qué no

**"100% fiable" no es alcanzable, y perseguirlo es el modo de fallo que este proyecto entero está
diseñado para evitar.** El eslabón "mapa satelital → mejor scouting" no tiene ni un solo ensayo
publicado que lo compare contra scouting sistemático (`ESPECIFICACION.md` §0). Nadie —ni Syngenta,
ni xarvio, ni EOSDA— ha demostrado ese eslabón. Prometer fiabilidad total sería inventar el número
que la competencia tampoco tiene.

Lo que sí es alcanzable, y lo que hay que construir, son dos cosas distintas:

**FIABLE** = todo número que la herramienta emite está medido o está declarado como no medido.
Ninguna afirmación sin respaldo, ningún parámetro sin barrido de sensibilidad, ninguna alerta sin α
declarado, ninguna entrega sin su etiqueta de calidad. Es auditable por un tercero hostil.

**APLICABLE A CAMPO** = el técnico puede salir mañana con la lista, encuentra el punto, registra lo
que ve sin saber qué esperaba el satélite, y ese registro vuelve y recalibra el sistema.

La segunda se consigue en semanas. La primera necesita **una campaña completa**, y esa es la
restricción que manda sobre todo el plan.

---

## 1. La restricción real es el calendario agrícola, no el código

Hoy es **24-jul-2026**. La campaña de verano de Santa Cruz —soya, la que importa— se siembra a
partir de **octubre**. La validación honesta de `ESPECIFICACION.md` §4 dura una campaña entera y
**solo se puede empezar una vez al año**.

| | Ventana | Qué pasa si se pierde |
|---|---|---|
| Preparar todo | **jul → sep 2026 (≈10 semanas)** | — |
| Campaña de validación | **oct 2026 → abr 2027** | Se espera a **octubre de 2027** |
| Número propio, medido | **may 2027** | may 2028 |

**Corolario que cambia las prioridades:** todo lo que tiene que estar listo *antes* de octubre está
en el camino crítico; todo lo demás puede esperar. El lazo de retorno y la planilla de siembra están
en el camino crítico. Afinar el detector, no.

### Aprovechar lo que queda de invierno como ensayo general

La estación seca de Santa Cruz tiene ~3× mejor disponibilidad óptica que el verano
(`DISPONIBILIDAD_MULTISITIO.md` §4), y el trigo de SA/SF ya está siendo monitoreado en producción.
Quedan unas 4-6 semanas hasta cosecha.

**Usar esa ventana para ensayar el LAZO, no el detector.** El objetivo no es medir precisión —no da
el tiempo ni el n— sino descubrir en agosto, con imágenes fáciles, todo lo que se rompe cuando un
técnico real sale a campo con la app: que el punto no aparece, que el GPS no ancla, que la ficha no
tiene la especie, que el registro no sube. Descubrir eso en enero, con 33% de dekadas con imagen y
la campaña corriendo, cuesta la campaña entera.

---

## 2. Las puertas

Cada puerta es una prueba que se pasa o no se pasa. No se avanza a la siguiente sin pasarla.
El esfuerzo es de construcción; el calendario manda sobre el total.

### Puerta 0 — Insumos que no son software · *días de gestión*

| # | Qué | Prueba de aceptación |
|---|---|---|
| 0.1 | **Planilla de siembra** por lote: cultivo, variedad, fecha de siembra | ≥90% de los lotes del piloto con fecha no nula. Hoy: **0%** |
| 0.2 | **K declarado por el cliente**: a cuántos lotes puede ir por semana con los técnicos que tiene | Un número por escrito. Sin él, precisión@K no tiene K |
| 0.3 | **Hacienda piloto elegida** | Geometrías con ID único: `n_ids_únicos == n_lotes`. Solo **HDS** lo cumple hoy (220/220) y es la única con 14 meses de historia |

Sin 0.1 el Paso 2 de la especificación no es implementable y la cohorte hay que estimarla por quiebre
de NDVI, rotulada como estimada. Sin 0.2 no hay métrica. **Es la puerta más barata y la única que
está 100% bloqueada por un tercero: pedirla hoy.**

### Puerta 1 — La tabla de series por lote · *3-5 días*

| # | Qué | Prueba de aceptación |
|---|---|---|
| 1.1 | Una fila por (lote, fecha, índice, calidad, cobertura válida), retrollenada ≥3 campañas | La tabla existe y `lote_id` cruza 100% contra el maestro |
| 1.2 | **Control contra la disponibilidad medida** | La fracción de dekadas con calidad "pleno" cae en **48% ± 5** (`AUDITORIA` §1). Si da mucho más, la máscara está dejando pasar nube |
| 1.3 | **Máscara con sombra** | Sobre una escena con nube conocida, los píxeles SCL=3 quedan fuera. Hoy el motor de producción **no excluye sombra** |
| 1.4 | **Dos ejes, no siete** | La correlación entre el eje de humedad y el de senescencia es \|r\| < 0,8. Si no, es un eje disfrazado de dos |

### Puerta 2 — El criterio, con la nula temporal · *1-2 semanas*

Esta es la puerta que separa este motor del de Syngenta, y la que hoy no se pasa.

| # | Qué | Prueba de aceptación |
|---|---|---|
| 2.1 | **Control nulo** — correr el criterio sobre un mundo donde la hipótesis nula es CIERTA POR CONSTRUCCIÓN: cada lote sigue la trayectoria de su cohorte + ruido AR(1) con la escala, la autocorrelación temporal y la correlación entre ejes medidas en el dato real | Tasa de alarma **≈ α declarado**. **MEDIDO 2026-07-26: 0,16%-0,28%** según el par de ejes, coherente con una carta a L=3σ. Referencia: Gi* espacial sobre el índice crudo marca ~30% |
| 2.1b | ⚠️ **NO usar permutación ni rotación como nula.** Medido: rotar la serie de cada lote (a) no movía la etiqueta de calidad, así que la nula se evaluaba sobre 3 lotes y el dato real sobre 96; (b) aplanaba la trayectoria de cohorte (desvío del NDMI mediano de 0,1338 → 0,1022), inflando el residuo; (c) **conserva los episodios sostenidos**, que es justo lo que el EWMA detecta. El número **"0,7%-1,8%"** que circulaba salió de ese método y **no es una tasa de falsa alarma** | Verificar siempre que la nula evalúe la MISMA población que el dato real |
| 2.2 | **No es una cuota** | La fracción marcada **varía entre fechas**. Si es constante en ~30% campaña tras campaña, es un cuantil con otra cara |
| 2.3 | **Puede decir "no pasa nada"** | Existe al menos una fecha del histórico en la que el sistema entrega **cero lotes** sobre el umbral de atención |
| 2.4 | **Estabilidad de parámetros** | Mover cualquier parámetro ±50% conserva **≥70% del top-K**. Precedente propio: en el motor de caña, df=7 vs df=2 movía la superficie roja de 113 a 772 ha el mismo día |
| 2.5 | **Reproducibilidad** | Misma entrada → misma salida, bit a bit. Ya se cumple (semillas fijas) |
| 2.6 | **Tests del motor** | Existe una suite con fixture sintético. Hoy: **cero tests** en 1.209 líneas |

### Puerta 3 — El lazo de retorno cerrado · *2-3 semanas, la mayor parte curaduría*

Sobre PIX_SCOUT, que ya está al ~65%. **En el camino crítico: tiene que estar en la mano del técnico
antes de octubre.**

| # | Qué | Prueba de aceptación |
|---|---|---|
| 3.1 | **`punto_id` estable** emitido desde el pipeline | 0 colisiones sobre el GeoJSON emitido, verificado por test. Hoy: **50 de 101 colisionan** |
| 3.2 | **`supera_umbral` calculado por el sistema** | Para las especies con umbral de fuente citable, el valor lo calcula el código a partir del conteo, no lo aprieta el técnico. Requiere convertir 26 umbrales de prosa a objetos computables y agregar el campo `conteo` |
| 3.3 | **Modo ciego** | El técnico no ve estrato ni severidad antes de guardar. `estrato_asignado` se guarda y **no se renderiza**. Hoy la app hace lo contrario por diseño |
| 3.4 | **Registro negativo** | Se puede guardar "nada encontrado" y llega al servidor. Sin esto §4 es inejecutable |
| 3.5 | **Ida y vuelta real** | Emitir 20 puntos → un técnico los visita → los 20 vuelven con el mismo `punto_id`, con foto y con hora. **Prueba de campo, no de laboratorio** |
| 3.6 | **Backend** | Tabla creada y `config.js` relleno. La cola cliente ya está escrita y probada |

### Puerta 4 — La campaña de validación · *oct 2026 → abr 2027*

Protocolo de `ESPECIFICACION.md` §4, que es correcto y no hay que tocar.

| # | Qué | Prueba de aceptación |
|---|---|---|
| 4.1 | **Estratos con verde** | Sorteo aleatorio dentro de rojo, amarillo **y verde**, con probabilidades de inclusión guardadas por punto |
| 4.2 | **n suficiente** | Calculado, no adivinado, a partir de la prevalencia esperada y del ancho de IC aceptable. Con prevalencia baja el n se dispara: hay que dimensionarlo **antes** de octubre y confrontarlo con el K real del cliente |
| 4.3 | **Ciego auditable** | El registro se cierra con timestamp anterior a cualquier consulta del mapa por ese técnico |
| 4.4 | **Métricas correctas** | precisión@K con IC + PR-AUC + prevalencia declarada. **Nunca exactitud global** |

### Puerta 5 — Operación y contrato · *1 semana*

| # | Qué | Prueba de aceptación |
|---|---|---|
| 5.1 | **Hueco máximo en el contrato** | Declarado por escrito: **66 días** en Santa Cruz, 147 en Mato Grosso. Un contrato que no lo contemple incumple en 1 de cada 5 temporadas |
| 5.2 | **Calidad dentro del dato** | Cada fila lleva su etiqueta. Sin esto, en un año no se distingue un falso negativo real de una dekada nublada |
| 5.3 | **Bootstrap de hacienda nueva** | Un script del repo produce las máscaras desde un vector de borde. Hoy vienen de otro proyecto como binarios opacos: **el repo no puede arrancar una hacienda solo** |
| 5.4 | **Sin silencios** | Los tres casos que hoy reportan "sin anomalías" cuando en realidad el motor no pudo correr (`n<200`, Mahalanobis degenerado, `cire_ref` ausente) pasan a error explícito |

---

## 3. Arreglos del sistema vivo, independientes de todo esto

Conviene hacerlos igual, porque afectan al informe que el cliente recibe hoy:

1. `history.json` quedó inconsistente con el baseline re-sembrado. El primer informe óptico completo
   va a dibujar una caída de −1,5 ha en SA y −2,9 ha en SF que es **cambio de método, no agronomía**.
   Arreglo: 10 minutos.
2. `check_new` toma solo la escena más reciente: si el cron se cae y aparecen una limpia y una
   nublada, **la limpia se pierde para siempre**. Falta `--force` / `--date`.
3. El PDF del cliente describe *"estrato de siembra"* y *"P95 de la cohorte"* — método que el motor
   no usa desde el 22-jul.

---

## 4. Lo que nunca va a ser fiable, y hay que declararlo por escrito

Esto no es una lista de pendientes: es el perímetro del producto. Va en el contrato y en la primera
reunión, no en la letra chica.

- **Chinches / percevejos.** Evidencia negativa publicada: ni el hiperespectral de proximidad detecta
  su daño. Y es la plaga que más importa en soya reproductiva.
- **Roya asiática de la soya.** Sin respaldo satelital a escala de lote comercial. Es la enfermedad
  número uno de la zona.
- **La causa.** El índice detecta estrés, no qué lo produce.
- **Detección pre-visual.** Cuando el foco es detectable ya mide 100-400 m² y se ve desde la
  camioneta.
- **La bordadura.** Embrapa documenta un gradiente de 67 → 43 → 18 → 5 → 0 chinches por metro hacia
  adentro. Un píxel de 10 m promediando 50 ha no lo ve. Hay que tratarla como estrato propio y aun
  así declarar que el satélite no la resuelve.
- **Cadencia fija con óptico.** 48% de las dekadas. Lo prometible es *"mapa óptico en cuanto haya
  escena utilizable"*: realistamente 4-13 mapas por temporada de verano en Santa Cruz.

Declarar esto no debilita la venta: **es la venta.** Ninguno de los 15 competidores publica su
criterio de alerta ni su validación. El argumento sigue siendo el de la especificación —*"hago que el
MIP sea aplicable en tus 200 lotes, y el MIP ahorra R$ 270/ha según Embrapa"*— y ese argumento no
necesita que el satélite vea la roya.

---

## 5. El orden de las próximas dos semanas

1. **Pedir la planilla de siembra y el K.** Hoy. Es lo único bloqueado por un tercero.
2. **Arreglar `history.json`.** 10 minutos, y evita un gráfico falso en el próximo informe.
3. **Construir la tabla de series de HDS** (Puerta 1). Es la única hacienda con base histórica.
4. **`punto_id` estable + salida "nada encontrado" en PIX_SCOUT** (3.1 y 3.4). Son los dos cambios
   más chicos del lazo y sin ellos el ensayo de invierno no mide nada.
5. **Sacar a un técnico a campo con lo que queda de trigo**, aunque el criterio todavía sea el viejo.
   El objetivo es que se rompa ahora.
