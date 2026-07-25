# La campaña de validación

Cómo se mide si dirigir el scouting con el mapa sirve. **Hay que dejarlo armado antes de
que se siembre**: una vez que la campaña arranca, elegir a dónde va el técnico en función
de lo que ya se vio sesga el resultado.

Cubre las Puertas 4.1, 4.2 y 4.4 de [`PLAN_A_PRODUCCION.md`](PLAN_A_PRODUCCION.md).

---

## El problema que resuelve

**Sesgo de verificación** (Begg & Greenes 1983, `10.2307/2530820`): si el técnico sólo va
a los lotes que el sistema marcó en rojo, el sistema **siempre** parece excelente y nunca
se sabe cuántos focos se escaparon. La precisión sale alta por construcción.

La solución de diseño (Olofsson et al. 2014, `10.1016/j.rse.2014.02.015`): sortear también
en el **verde**, sobremuestrear el rojo porque ahí está la señal, y **guardar las
probabilidades de inclusión** para corregir después. Sin esas probabilidades, el
sobremuestreo del rojo contamina toda estimación poblacional.

Ninguno de los 15 competidores revisados publica validación. Este es el número propio.

---

## Cómo se corre

**1. Ranking completo, SIN cortar por K.** El corte por K deja fuera el estrato verde.

```bash
python -m pix_alerta.main --sitio HDS --hasta 2026-10-15 --salida salida/HDS
```

**2. Dimensionar y sortear.**

```bash
python -m pix_alerta.disenar_muestra --ranking salida/HDS/ranking_HDS_2026-10-15.csv --sitio HDS --prevalencia 0.30 --semiancho 0.10 --K 10 --rondas 20
```

Emite la muestra (CSV con probabilidad de inclusión y peso), el **GeoJSON ciego** para la
APK, y el dimensionamiento en texto para que quede auditable.

Si el ranking no tiene estrato verde, **el comando falla y explica por qué**. No emite una
muestra sesgada.

**3. Encender `MODO_CIEGO` en la APK** antes de repartir la muestra. Si el técnico sabe que
va a un rojo, encuentra algo.

**4. Al cierre, evaluar.**

```python
from pix_alerta import validacion as vl
res = vl.evaluar(validaciones)      # muestra + lo que encontró el técnico
print(vl.informe(res))
```

---

## Dimensionamiento real de HDS (medido, 2026-07-25)

Sobre el ranking real del 2026-04-30: 126 lotes evaluados, 4 en ATENCIÓN, 2 en VIGILANCIA,
115 sin señal, 5 sin dato.

| Estrato | N | n a visitar |
|---|---|---|
| ATENCIÓN | 4 | 4 |
| VIGILANCIA | 2 | 2 |
| SIN SEÑAL | 115 | 48 |
| **total** | | **54 visitas** |

Con K=10 y 20 rondas la capacidad es 200: **alcanza de sobra**.

### ⚠️ Pero el estrato alertado es demasiado chico

Ése es el hallazgo que importa. Con 6 lotes alertados a una fecha, el intervalo de
confianza de la precisión es de **±44 puntos** — no distingue nada:

| Alertados visitados | IC de la precisión |
|---|---|
| 6 | ±44 pp |
| 20 | ±22 pp |
| 40 | ±16 pp |
| 60 | ±13 pp |

**Consecuencia operativa: la muestra hay que sortearla en CADA RONDA y acumular los
alertados a lo largo de la campaña**, no sortear una vez en octubre. Con ~20 rondas y unos
pocos alertados por ronda se llega a 40–60 acumulados, que es donde el número empieza a
significar algo.

El módulo sortea por ronda; **acumular entre rondas es trabajo del operador y todavía no
está automatizado**. Es lo primero que hay que construir cuando arranque la campaña.

---

## Las métricas, y la que no se calcula

**Nunca exactitud global.** Con prevalencia baja, "no pasa nada en ningún lote" da 95% de
exactitud y es un sistema inútil. `validacion.py` no la implementa: no es un olvido.

Lo que sí se reporta, siempre junto:

- **Precisión en lotes alertados**, con IC95.
- **Prevalencia del campo**, con IC95 — una precisión sin la prevalencia al lado no se
  puede interpretar.
- **Mejora sobre ir al azar** (precisión ÷ prevalencia). Si es ≤ 1, dirigir el scouting con
  el mapa no rindió más que ir al azar, y **eso se reporta como tal**.
- **Recall aproximado** y **PR-AUC ponderada** por el diseño.

Todas las estimaciones poblacionales usan el estimador estratificado con corrección por
población finita. Sin pesos, la prevalencia estimada sería la del rojo, no la del campo.

El informe marca el resultado como **no concluyente** si no se visitó ningún lote verde, o
si algún estrato tiene menos de 5 observaciones.

---

## Lo que falta

- **Acumulación entre rondas** (ver arriba). Es el hueco más importante.
- **Puerta 4.3 — ciego auditable.** Exige que el registro se cierre con timestamp anterior
  a cualquier consulta del mapa por ese técnico. La APK guarda `created` en cada
  validación, pero **no registra cuándo el técnico abrió el mapa**, así que hoy el ciego no
  es auditable a posteriori: se confía en el procedimiento. Hace falta un evento
  `mapa_consultado` en PIX Scout.
- La prevalencia esperada de 0,30 es un **supuesto**, no un dato: no hay ni una observación
  de plaga georreferenciada en la cartera. Al cierre de la primera campaña se reemplaza por
  el valor medido y se re-dimensiona la segunda.
