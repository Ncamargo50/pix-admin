# Cómo pasar el sistema de TRIGO a soja, caña o maíz

Fecha: 2026-07-24. Auditado sobre el código real. Incorpora `ESPECIFICACION.md` §7
(protocolos MIP verificados, incluidos Bolivia y Argentina).

---

## Antes que nada: son DOS sistemas, no uno

No comparten una línea de código. Cambiar de cultivo hay que hacerlo dos veces.

| | Pipeline de producción | PIX ALERTA |
|---|---|---|
| Dónde | `PIXADVISOR_Sync/repo/scripts/` | `PIX_ALERTA/pix_alerta/` |
| Qué opera | polígono de hacienda, ráster | lotes con ID, tabla |
| Gatillo | Gi\* sobre residuo temporal de CIre | EWMA sobre residuo vs cohorte |
| Severidad | Mahalanobis (NDMI, TCARI/OSAVI) | los 2 ejes en señal |
| Corre | GitHub Actions, 2×/día | a mano |

Ningún documento declara cuál reemplaza a cuál. **Esa decisión hay que tomarla antes
de tocar el cultivo**, o se paga el trabajo dos veces.

---

## Lo que cuesta, en una tabla

| Bloque | Trabajo | Quién |
|---|---|---|
| Sacar `CULTIVO` a configuración y limpiar duplicados | ~1 día | programación |
| Bootstrap de `ambientes.tif` / `strata.tif` | 2-3 días | programación |
| Re-anclar umbrales sobre el cultivo nuevo | **1-2 semanas de campaña, por cultivo** | agronomía |
| Fecha de siembra / corte por lote | **hoy no existe** | gestión con la hacienda |

**El cuello de botella no es el código.** Hoy hay que tocar ~13 archivos de código,
4 de estado y 2 binarios que ningún script genera — pero sólo 8 de esas ediciones son
strings. El resto exige medir sobre una campaña del cultivo objetivo.

---

## Inventario: qué es específico de trigo

### Sólo cambiar un texto (8 lugares)
`p5_report.py:2,43` · `p5b_interim.py:20` · `monitor_run.py` (los dos nombres de PDF) ·
`monitor.yml:1,48,75` (nombre, commit, mensaje de WhatsApp) · `README.md` ·
`p6_geojson.py:23` (`PREFIJO`).

### Cambiar un valor que exige criterio agronómico
| Dónde | Valor | Por qué cambia |
|---|---|---|
| `cfg.py` `VENTANA_BARBECHO` | mar-may | depende del ciclo y de si hay barbecho |
| `cfg.py` `VENTANA_REFERENCIA` | 46 días | en soja son ~⅓ del ciclo |
| `p2_engine.py` `FVC_MIN` 0,35 | compuerta | la skill pide canopy ~0,6 en soja/caña |
| `p2_engine.py` `NDVI_SUELO` 0,18 | ancla de suelo | sobre palhada de caña no es 0,18 |
| `p2_engine.py` `win` 150 m | ventana local | en maíz hay que subirla (sombra de surco) |
| `p1b_s1.py` baseline 36 días | radar | en soja son dos estadios |

### Rehacer o medir
`TEMP_DECL = 0.93` — decide Prioritario vs Vigilancia y está anclado a una escena de
trigo. Los índices del gatillo y de la severidad. El orden de zonas de `build_zones.py`
(en caña ordenaría por edad de soca, no por suelo).

---

## Los supuestos que se rompen

**El factor fenológico es un escalar por hacienda.** `p2_engine` calcula
`fac = mediana(CIre_hoy / CIre_ref)` — "cuánto avanzó el campo" — y todo el criterio
cuelga de que el campo avance junto.

- **Soja escalonada (oct–dic):** un lote en R6 y otro en V6 el mismo día tienen
  trayectorias opuestas. Y la estratificación es un `if/else`: hoy usa zona de suelo,
  así que **la cohorte de siembra no se aplica en producción**.
- **Caña:** un lote cortado hace 2 meses (rebrote, CIre subiendo) convive con uno de 12
  meses (madurando). El recién cortado entra con `rel ≈ 0` y **sale prioritario por
  haber sido cosechado**. La compuerta FVC lo salva mientras el suelo está desnudo, pero
  en el rebrote intermedio entra y se marca.
- **Maíz safrinha:** ciclo comprimido, senescencia forzada. Igual que soja, peor.

**La fase I de la carta EWMA.** Con 48% de dekadas útiles, 4 observaciones plenas son
~80 días. En soja (110-130 días de ciclo) eso se come dos tercios. **Es un bloqueo
estructural para soja**, no un parámetro. Salidas: sembrar la línea base con el histórico
de campañas anteriores del mismo lote, o declarar que el sistema no ve nada antes de R3.

**El barbecho no existe en caña ni en safrinha.** En caña queda *palhada* (10-20 t/ha de
paja), que no es suelo desnudo — y el BSI, además de tener la cita rota, no distingue
rastrojo seco. En safrinha se siembra sobre rastrojo de soja. Alternativas, en orden de
defendibilidad: composite multianual de suelo expuesto (GEOS3/SYSI `10.1016/j.rse.2018.04.047`,
MBI `10.3390/land10030231`), quitar la feature de suelo, o zona de suelo desde muestreo.

---

## Los índices: ¿sirven en cada cultivo?

Según `references/cultivo_fenologia.md` de la skill, con su regla explícita —
*"no transferir un índice validado de un cultivo-enfermedad a otro sin verificar"*:

| Cultivo | Veredicto |
|---|---|
| **Soja** | El set actual es el más transferible. CIre y TCARI/OSAVI figuran como robustos. Cambiar la compuerta (canopy 0,6) y **medir la dimensionalidad efectiva en soja** antes de fijar el df del χ² |
| **Maíz** | Los índices sirven; lo que no sirve es la geometría. Subir `win` y testear a 20-30 m por la sombra entre surcos. **Mejor antecedente publicado**: cogollero 72-82% en test independiente, AUC 0,83-0,95 |
| **Caña** | **Hay que cambiarlos.** La skill lista NDRE, GNDVI y radar RVI; no lista CIre ni TCARI/OSAVI. Techo medido de S2 en caña: LAI R²=0,42, clorofila 0,27, N foliar 0,12. El radar pasa de complemento a primera línea |

---

## Los umbrales MIP, que es donde el proyecto tiene un hueco y una oportunidad

Esto cambia con la §7 nueva de la especificación.

### Bolivia: no existe protocolo oficial de densidad

Verificado contra ANAPO, CIAT, INIAF y SENASAG: **no hay densidad de muestreo por
hectárea publicada**. Lo único institucional accesible con umbrales es la cartilla ANAPO
Nº5 (2011) y la Hoja Divulgativa 38 (2024).

Para **soja** sí hay números citables: paño de 1 m para gusanos y chinches, 10 m lineales
para picudo, 100 plantas para barrenador. Chinches 2 por paño (grano) / 1 (semilla);
picudo 1 adulto/m hasta V3 y 2/m de V3 a V6; barrenador 25-30% de plantas; gusanos de
vainas 10% de vainas; ácaros 10-20 por trifolio. Trips y mosca blanca **sin umbral**.

⚠️ La cartilla de 2011 imprime *"40 gusanos de hasta 15 cm"* — errata evidente del
original. No usar sin contrastar contra el manual 2024.

**Maíz y sorgo en Bolivia: no existe protocolo oficial.** Y las densidades del INSA
(3-5 puntos hasta 20 ha, 7-9 de 21 a 50, 11 de 51 a 100) son para **ajuste de siniestros
de seguro, no para scouting** — no citarlas como tal.

### Argentina da la mejor referencia de densidad para calibrar el K

**AAPRESID**: *una estación cada 10-15 ha dentro de la unidad de manejo, mínimo 4-5 para
lotes menores a 40-50 ha*, **estaciones fijas georreferenciadas**, semanal, cada 3-4 días
cerca del umbral.

Esto responde parcialmente la pregunta abierta nº2 (¿qué K tiene el cliente?): da un piso
defendible para dimensionar la capacidad de scouting, y **"estaciones fijas
georreferenciadas" es exactamente el `punto_id` estable que el lazo de retorno necesita**.

### El respaldo institucional para la regla del proyecto

INTA Reconquista publicó que los umbrales de defoliación de soja de Argentina se
establecieron en la zona núcleo, y que en el norte de Santa Fe **con 33% de defoliación en
R1 el rendimiento cayó 18%**, mientras que en la zona de origen el efecto aparecía recién
a partir del 67%. Textual: *"los umbrales actualmente vigentes subestiman la reducción de
rendimiento"*.

Es una institución oficial documentando que **un umbral absoluto falló al cambiar de
región dentro del mismo país**. Es la cita que respalda la regla de no transferir umbrales
— y aplica igual al `TEMP_DECL = 0.93` del propio motor.

### Consecuencia práctica

En PIX SCOUT las 123 fichas están completas, pero de los 26 umbrales con fuente **sólo 19
traen una cifra y ninguno es computable**: son prosa. En trigo, soja y maíz el 100% lleva
el flag `VERIFICAR_LOCAL`. O sea que `supera_umbral` —el eslabón que convierte esto en
*"hago que el MIP sea aplicable"*— **no es calculable para ninguno de los tres cultivos
objetivo**. Con los números de ANAPO y AAPRESID ahora hay con qué llenarlo para soja en
Bolivia; para maíz y sorgo hay que elegir un juego extranjero y declararlo.

**Que Bolivia no tenga protocolo no es un obstáculo: es el diferencial.** El producto
puede ser el primero en fijar una densidad defendible, citando AAPRESID para la densidad
y ANAPO para los umbrales, y declarando ambas procedencias.

---

## PIX SCOUT: no es sólo elegir otro JSON

Los 7 cultivos ya están (123 fichas, empaquetadas en `data.js`, la clave dicotómica es
agnóstica). Pero el cultivo del recorrido está cableado:

- `app.js:54` — `cultivo:'trigo'` en la carga del GeoJSON
- `geojson.js:91` — `cultivo: def.cultivo || 'trigo'`, **nunca mira `props.cultivo`**
- `app.js:416` — fallback duro a `'soya'` al guardar
- `config.js:15` — `DEFAULT_FOCOS`

**Asimetría peligrosa:** si el GeoJSON trae `properties.cultivo:"Soja"`, cambia sólo la
etiqueta en pantalla; el banco de fichas que se abre sigue siendo el de trigo. El técnico
vería "Soja" en el mapa y una lista de royas de trigo.

**Trampa de nombres:** la clave interna de caña es `cana_de_azucar`, no `cana`. Escribir
`'cana'` produce un `TypeError` sin guard.

Y el pipeline **no emite `cultivo`** en el GeoJSON. Hay que agregarlo.

---

## Procedimiento

### Común, antes de elegir cultivo

1. Decidir cuál de los dos motores es el sistema.
2. Sacar `CULTIVO` a `cfg.py` y consumirlo en los 8 textos.
3. Deduplicar `HAC` (3 copias) y `EPSG` (3 copias).
4. **Escribir el bootstrap de `ambientes.tif`/`strata.tif`.** Sin esto no hay hacienda
   nueva posible, sea cual sea el cultivo.
5. Emitir `cultivo` en el GeoJSON y que la app lo lea normalizado, con guard.
6. Poblar `cohorte` en `series.py` y consumir `Sitio.campanas` (declarado y no leído).
7. **Pedir la planilla de siembra.** No es software.
8. Estructurar los umbrales MIP en objetos computables, con la fuente declarada por
   número (ANAPO / AAPRESID / Embrapa / INTA).

### Soja
Lo anterior, más: ventana de barbecho a jul-sep **verificando que el lote no lleve cultivo
de invierno**; ventana de referencia a ≤3-4 semanas; `FVC_MIN` equivalente a canopy 0,6;
**cruzar zona de suelo × cohorte** en vez del `if/else`; re-anclar `TEMP_DECL`; medir la
dimensionalidad efectiva en soja; resolver la fase I (histórico o declarar la ceguera
hasta R3); umbrales ANAPO para Bolivia.

**Es el más portable en índices y el más caro en fenología.**

### Caña
Lo común, más: **reemplazar el concepto de campaña por edad de soca** (cambio de modelo de
datos, no de valor); resolver el barbecho inexistente; arreglar el orden de zonas;
eliminar o cohortizar el factor fenológico escalar; **cambiar los índices**; subir el radar
a primera línea. Declarar por escrito que `ESPECIFICACION.md` §8 prohíbe prometer que
sirve para plagas de caña — el producto defendible es priorizar dónde muestrear.

**Es el más lejano.** Contrapartida: la fase I no es problema en un ciclo de 12-18 meses,
y HDS es la única hacienda con 220 lotes con ID y 14 meses de historia.

### Maíz
Lo común, más: **declarar zafra y safrinha como cultivos distintos**; resolver el barbecho
en safrinha; subir `win` y testear a 20-30 m; agregar MSAVI2; misma fase I que soja.
Umbrales: elegir entre Embrapa (10% raspadas, con discrepancia interna documentada) e INTA
Marcos Juárez (20% + presencia de orugas, con aviso de fallas en Bt Vip3Aa20) y declararlo.

**Portabilidad intermedia, mejor respaldo bibliográfico, peor definición de umbral.**

---

## Lo que no se puede determinar del código

1. La fecha de siembra o de corte de ningún lote. No existe.
2. Cómo se generaron `ambientes.tif` y `strata.tif`, ni qué significa cada clase.
3. Si `TEMP_DECL=0.93`, `DET=-0.03` y los cortes de riesgo 5%/2% tienen algún respaldo.
4. Cuál de los dos motores es "el sistema".
