# PIX ALERTA

Ranking de lotes por prioridad de scouting. Dice **a qué lotes ir hoy**, no qué plaga hay.

```bash
python -m pix_alerta.correr_todos --hasta 2026-04-30      # todos los clientes activos
python -m pix_alerta.main --sitio HDS --hasta 2026-04-30 --K 10 --control-nulo
python -m pytest tests/ -q          # las puertas de aceptacion
```

Salida: `<salida>/<cliente>/ranking_<sitio>_<fecha>.csv` y `lotes_<sitio>_<fecha>.geojson`
para la app de campo.
Exit codes: `0` nada que entregar · `10` entregable generado · otro = fallo real.

**Alta de cliente = un archivo JSON en `clientes/`, cero código.** Ver [clientes/README.md](clientes/README.md).

---

## Qué hace, en una frase

Mide cuánto se aparta cada lote de **su propia trayectoria** —no de la de sus vecinos— y acumula
ese apartamiento con una carta EWMA. Los lotes que salen de control son los que valen una visita.

## Por qué no Gi\* sobre el índice crudo

Medido sobre escena real de Santa Cruz (`medicion/gi_nulo_y_estratos.py`):

| | Superficie marcada |
|---|---|
| Gi\*+FDR sobre el índice, campo real | 33,3% |
| ídem, estratificando por zona de suelo | 30,3% |
| ídem, con los valores barajados en el espacio | **0,0%** |

La implementación era correcta; la pregunta no. Gi\* contrasta contra aleatoriedad espacial, que es
falsa por construcción en cualquier lote agrícola: siempre hay suelo, topografía y gradiente de
siembra. Rechazarla no informa, y el resultado es **una cuota del 30%** — lo mismo que hacen los
cuantiles, con más matemática encima.

La nula temporal sí puede ser verdadera: un lote sano sigue su curva.

## Resultados medidos

Campaña completa de HDS (2025-10 a 2026-04, 20.700 filas, 207 lotes de cultivo, NDMI de B8A).
Porcentajes **sobre lotes con observación reciente**, no sobre el total: incluir los `SIN DATO`
en el denominador infla la variación y hace parecer que el criterio responde cuando lo que
cambió fue la nubosidad.

### La cohorte no es un refinamiento: sin ella el criterio está ciego

| Configuración | Marcado real (media / máx) | Control nulo | ¿Discrimina? |
|---|---|---|---|
| Cohorte única | 1,3% / 4,3% | 2,0% | **No** — el marcado queda *por debajo* del nulo |
| **Cohorte estimada por fenología** | **4,7% / 9,9%** | 3,1% | **Sí** — 1,5× el nulo en media, 3,2× en el pico |

Con lotes en estadios distintos, la trayectoria mediana no describe a ninguno: los residuos
quedan grandes y ruidosos, la escala por fecha se infla y todo parece normal. Es exactamente
lo que advierte `ESPECIFICACION.md` Paso 2, medido.

No hay fecha de siembra declarada en ningún archivo del proyecto, así que la cohorte se
**estima** por mitad de amplitud propia de la curva de NDVI (half-max de la rama ascendente,
el estimador estándar de *greenup*) y se rotula `EST-<fecha>` para que en el entregable quede
explícito. Es relativo a cada lote: no usa ningún umbral absoluto de NDVI. Los lotes sin ciclo
interpretable quedan en `EST-SIN-CICLO`, como cohorte aparte.

Sobre HDS: **10 cohortes estimadas** (bin de 15 días) y 86 lotes sin ciclo interpretable.

### Calidad estadística

| | |
|---|---|
| SD del z bajo la nula (objetivo ≈1) | 1,38 (NDMI) · 1,34 (PSRI) |
| Lotes con serie suficiente | 126 de 207 |

**Sigue sin haber validación agronómica.** El criterio pasa sus puertas estadísticas y ahora
discrimina; su precisión contra campo es desconocida y lo será hasta la campaña de validación.

### Historia del estimador de escala, que es lo que gobierna la tasa de falsa alarma

Cuatro versiones, todas medidas sobre el dato real. Objetivo: SD(z) ≈ 1.

1. **MAD del propio lote** — sesgado a la baja con pocos puntos; el denominador elegía el
   ranking (defecto del motor de caña: 49 de 131 lotes con SD < 0,03).
2. **Rango móvil** (MAD de diferencias sucesivas ÷ √2) — supone independencia temporal. Con
   el ρ real (0,6–0,7) devuelve σ·√(1−ρ): denominador ~2,7× chico. **SD(z) = 2,9.**
3. **Dispersión marginal de fase I** — la heterogeneidad entre lotes **crece** durante la
   campaña, así que una escala fija se calibra bien al principio y mal después. **SD(z) = 2,9.**
4. **MAD transversal entre lotes, por fecha** (actual) — no supone nada sobre dependencia
   temporal y sigue la heterogeneidad real.

Riesgo conocido de la versión 4: un evento **generalizado** infla la escala de esa fecha y se
enmascara. Se usa MAD (haría falta que afectara a más de la mitad de los lotes) y hay un piso.

El **control nulo** también estaba ciego: permutar identidades dentro de cada fecha dejaba
cada serie iid, o sea destruía la autocorrelación a la que el estimador es sensible, y
reportaba ~0% pasara lo que pasara. Ahora usa rotación circular, que preserva la estructura
temporal intra-lote.

## Cómo funciona el criterio

Tres pasos, en `ranking.residuos()`:

1. **Quitar la trayectoria fenológica** — `resid = valor − mediana(cohorte, fecha)`. Lo que baja
   porque la campaña avanza, baja para todos. Se usa la mediana y no la media para que media docena
   de lotes afectados no arrastren la referencia.
2. **Quitar el desnivel propio del lote** — con la línea base de las primeras `N_BASE` observaciones
   (fase I de la carta). Sin este paso, un lote que siempre está más seco que el resto (otra
   variedad, otro suelo) queda marcado para siempre: sería volver a preguntar "¿este lote es distinto
   de sus vecinos?".
   La base sale de una ventana **anterior**, no de la serie entera: si se usa toda la serie, un
   episodio largo entra en su propia referencia y se anula solo. Es el defecto que tiene el eje
   temporal del motor v7, cuya ventana de `cire_ref` incluye la fecha que analiza.
3. **Estandarizar por rango móvil agrupado** — MAD de las diferencias sucesivas dentro de cada lote,
   agrupadas entre lotes. No el MAD de cada lote por separado: con pocas observaciones ese estimador
   está sesgado a la baja y **el denominador termina eligiendo el ranking** (defecto medido en el
   motor de caña: 49 de 131 lotes con SD < 0,03, mínimo 0,0016).

Después, `ranking.ewma()` acumula: un apartamiento chico y sostenido pesa más que un pico de una
fecha. El límite de control incorpora la **incertidumbre de la línea base** (`1/N_BASE` dentro de la
raíz); sin ese término cada lote arrastra un desvío persistente —medido: 0,78 σ con `N_BASE=4`— y la
carta dispara sola.

Un lote entra en ATENCIÓN si **los dos ejes** salen de control en el sentido fisiológico del
deterioro (NDMI bajo = dosel más seco; PSRI alto = más senescente). Uno solo = VIGILANCIA.

### Dos ejes, no siete

Dimensionalidad efectiva medida de los 7 índices que usa el motor v7: **1,87–2,40**
(`medicion/dimensionalidad_indices.py`; PC1 69,7%, PC1+PC2 90,4%; CIre–NDRE r=0,97). Un índice más
agrega columnas, no información.

---

## Las puertas de aceptación

`tests/test_criterio.py` — cada test es una puerta de `PLAN_A_PRODUCCION.md` §2. Corren sin GEE.

| Test | Qué garantiza |
|---|---|
| `test_control_nulo_cerca_de_alfa` | Sobre campo sano marca poco, no un 30% fijo |
| `test_desnivel_propio_no_se_marca` | Un lote constantemente distinto no es una alerta |
| `test_no_es_una_cuota` | La fracción marcada responde a lo que pasa |
| `test_puede_decir_que_no_pasa_nada` | El sistema puede no mandar a nadie |
| `test_detecta_un_deterioro_real` | Sensibilidad: si no detecta, tampoco sirve |
| `test_signo_fisiologico` | Un dosel más húmedo no es alerta de plaga |
| `test_estabilidad_de_parametros` | λ ±50% conserva ≥70% del top-10 |
| `test_reproducible` | Misma entrada, misma salida |
| `test_la_alerta_se_resuelve` | Un lote que se recupera deja de estar marcado |
| `test_dato_viejo_no_es_alerta` | No se arrastra un estado sin observación reciente |
| `test_serie_corta_no_produce_ranking` | Sin serie no se inventa un resultado |
| `test_cohorte_chica_se_descarta` | Sin cohorte la referencia no significa nada |
| `test_cohorte_estimada_no_se_rotula_declarada` | El entregable no afirma fechas de siembra que no existen |

`tests/test_clientes.py` — puertas de la capa multi-cliente:

| Test | Qué garantiza |
|---|---|
| `test_alta_de_cliente_es_un_archivo` | Dar de alta un cliente no requiere editar `.py` |
| `test_rutas_relativas_al_archivo_del_cliente` | Un cliente es una carpeta portable |
| `test_cada_cliente_escribe_en_su_carpeta` | Aislamiento por construcción |
| `test_clave_de_cliente_repetida_es_error` | Dos clientes no comparten carpeta de salida |
| `test_clave_de_sitio_con_guion_bajo_se_lee_bien` | El chequeo de aislamiento no da falsas alarmas |
| `test_detecta_entregable_de_otro_cliente` | Se verifica leyendo las carpetas, no por confianza |
| `test_cliente_ilegible_no_se_saltea_en_silencio` | Un cliente roto no queda sin informe calladamente |
| `test_un_sitio_que_falla_no_frena_a_los_demas` | Un GeoJSON roto no deja a todos sin entrega |
| `test_typo_en_campo_de_sitio_es_error` | `epsg` en vez de `epsg_metrico` no pasa callado |
| `test_sitios_ref_inexistente_es_error` | No se referencia un sitio que no existe |
| `test_cliente_sin_sitios_es_error` | — |
| `test_K_invalido_es_error` | K es la capacidad real de scouting |
| `test_inactivo_no_corre` | Se puede desactivar un cliente sin borrarlo |
| `test_sitio_de_cliente_no_pisa_uno_ya_definido` | No se resuelve por orden de lectura |
| `test_cliente_HDS_del_repo_carga` | El cliente real declarado carga y reusa su sitio |

---

## Límites, declarados

- **La cohorte hoy es una sola.** No existe fecha de siembra en ningún archivo del proyecto. Sin
  cohorte, la trayectoria de referencia mezcla lotes en estadios distintos. Es la degradación más
  grande que tiene el sistema hoy y **no se arregla con código**: es una planilla.
- **Un deterioro que empiece dentro de la fase I no se detecta.** La línea base hay que sembrarla
  temprano en campaña.
- **48% de las dekadas tienen escena óptica útil** a escala de lote (`AUDITORIA_2026-07-24.md` §1).
  Cada fila lleva su etiqueta de calidad; el producto pleno no es la mayoría de las entregas.
- **No dice qué plaga hay.** No detecta antes que el ojo humano. No sirve para chinches ni para roya
  de soya. Ver `ESPECIFICACION.md` §8.
- **Nada de esto está validado contra campo**, porque no existe ni una observación de plaga
  georreferenciada en la cartera. El criterio pasa sus puertas estadísticas; su precisión agronómica
  es desconocida hasta la campaña de validación.

---

## Archivos

| | |
|---|---|
| `pix_alerta/config.py` | Sitios y parámetros. Agregar una hacienda = una entrada |
| `pix_alerta/clientes.py` | Capa de clientes: alta por archivo, validación, aislamiento |
| `pix_alerta/correr_todos.py` | Corrida multi-cliente (lo que va en el cron) |
| `clientes/` | Un JSON por cliente. Ver su README |
| `pix_alerta/series.py` | Extracción a tabla por lote y fecha (`reduceRegions`, sin ráster) |
| `pix_alerta/ranking.py` | El criterio: residuos, EWMA, ranking, control nulo |
| `pix_alerta/main.py` | Orquestador con contrato de exit codes |
| `tests/` | Las puertas |
| `medicion/` | Scripts de la auditoría (disponibilidad, dimensionalidad, Gi\*) |
