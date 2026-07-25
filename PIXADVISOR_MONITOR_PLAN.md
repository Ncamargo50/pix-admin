# Pixadvisor Monitor — Plan de implementación

**Fecha:** 2026-07-24 · **Estado:** propuesto, pendiente de luz verde
**Versión presentable:** https://claude.ai/code/artifact/eb7fdd95-76f3-4524-aebb-802a6b1a0694
**Supersede:** `PLAN_ESTRATEGICO_RENTA_IA_2026.md` (borrador con supuesto técnico erróneo)

---

## 0. Resumen

Ranking semanal de lotes para dirigir el scouting, entregado automáticamente, con criterio auditable
y retorno del técnico cerrando el lazo. **Lo que se vende no es el píxel: es que el MIP se vuelva
aplicable en 200 lotes** (ahorro Embrapa R$ 270,16/ha).

**Restricción dura:** ~10 semanas hasta la siembra de octubre 2026. La validación dura una campaña y
solo se puede empezar una vez al año. Perder octubre corre el primer número propio de may-2027 a may-2028.

---

## 1. CORRECCIÓN CENTRAL respecto del borrador anterior

**El motor de Pixadvisor Monitor NO es el pipeline de rásteres de la nube. Es PIX_ALERTA.**

Verificado en disco (2026-07-24). El camino "generalizar el pipeline de monitoreo a multi-cliente"
está cerrado:

| Criterio para vender a cliente nuevo | Pipeline nube v7 (rásteres) | PIX_ALERTA |
|---|---|---|
| Alta de hacienda | Editar 6+ archivos + binarios a mano | 1 entrada en `config.py:47` |
| Unidad de análisis | Píxel (`grep -i lote` = solo comentarios) | **Lote** (fila por lote×fecha) |
| Insumo mínimo | Perímetro + `ambientes.tif` + `strata.tif` + baseline sembrado | GeoJSON de lotes |
| Zona UTM | Fija 22S, re-hardcodeada en `p1_extract.py:11` y `p1b_s1.py:17` | Parámetro por sitio |
| ¿Puede decir "no pasa nada"? | Marca ~30% siempre (cuota disfrazada) | Control nulo 0,7–1,8% |
| Tests | 1 verificador de fórmula | 13 pruebas de aceptación, en verde |

**Bloqueo duro del pipeline v7:** `build_zones.py:65` abre `ambientes.tif` para sacar la grilla y la
máscara de área útil. **Ningún script del repo escribe `ambientes.tif` ni `strata.tif`** — vienen de
otro proyecto como binarios opacos. Sin ese archivo no arranca ni la zonificación.
Además `monitor_run.py:114-115` copia `strata.tif` sin chequear existencia: una hacienda nueva corre
p1→p6 entera y revienta con `FileNotFoundError` en la promoción, después de gastar toda la descarga.

**Decisión:** el pipeline de rásteres no se tira, **baja de categoría** → capa de acercamiento opcional
sobre los lotes del top-K (Fase 4 de `PIX_ALERTA/METODOLOGIA_RECOMENDADA.md`). Sigue corriendo tal cual
para SA + SF, que es donde funciona.

---

## 2. Las tres piezas

| Pieza | Función | Estado real verificado |
|---|---|---|
| **PIX_ALERTA** (motor) | Serie por lote S2 → cohorte estimada → residuo → EWMA → ranking | **Operativo.** 20.700 filas, 207 lotes, 100 escenas, campaña completa HDS (oct-25→abr-26). 13 tests verdes. Salida real: 6 lotes (4 ATENCION, 2 VIGILANCIA), 0 colisiones de id |
| **PIX Scout** (lazo) | APK offline: navega al lote, diagnóstico diferencial, foto obligatoria, registro negativo | **A medias.** v1.0.6 firmada y funcional 100% offline, **backend desconectado** (`config.js:16-17` vacíos) |
| **Entrega** (operación) | Corrida programada, informe, aviso, cobro | **Por construir.** Mono-cliente; no existe el concepto de segundo cliente |

---

## 3. Argumento de venta (y lo NO prometido)

**Vender:** "hago que el MIP sea aplicable en tus 200 lotes". Lo respalda Embrapa, no Pixadvisor.
- R$ 270,16/ha de ahorro decidiendo por umbral (n=119 URT, Embrapa Soja + IDR-PR, 2024/25)
- 1,02 vs 3,36 aplicaciones/campaña, sin perder productividad
- Adopción real del MIP: 32,9% (76% lo conoce, 25% lo usa)
- −44% aplicaciones de insecticida por umbral vs calendario (metaanálisis 126 estudios / 34 cultivos)

**NO prometer (va por escrito en el contrato):**
- Chinches/percevejos: **evidencia negativa publicada** (`10.3390/agronomy12071516`)
- Roya asiática de soya a escala de lote comercial: NO ENCONTRADO (y es la enfermedad #1 de la zona)
- Detección pre-visual con S2: no existe (`10.3389/fpls.2023.1250844`)
- La causa del estrés: el satélite no la dice
- Cadencia fija con óptico: se rompe sola en enero

Declararlo es lo único que hace defendible el resto. **Ninguno de los 15 competidores revisados
publica su criterio ni su validación.**

---

## 4. Los 8 bloqueantes, con arreglo

**Estado al 2026-07-25: 7 de 8 cerrados. El único abierto depende de un tercero.**

| # | Bloqueante | Qué se hizo | Estado |
|---|---|---|---|
| 1 | **Planilla de siembra no existe.** 0 lotes con fecha en toda la cartera | Hay que pedírsela al cliente. No es software. Mientras tanto la cohorte se estima por fenología y se rotula como estimada | ⛔ **abierto — depende del cliente** |
| 2 | **Backend PIX Scout apagado** (credenciales vacías); validaciones encoladas para siempre | Esquema `backend/001_scout_validaciones.sql` (37 columnas = las 37 claves que manda la app, verificado). **RLS append-only**: `anon` solo INSERT, porque la clave viaja dentro del APK. `store.js` a `ignore-duplicates` (un merge exigiría UPDATE → 403 en todo reintento). Probado contra un PostgREST simulado | ✅ **falta pegar credenciales** |
| 3 | ~~Colisión de `punto_id`: 20 de 41~~ | **NO SE REPRODUCE.** Medido: la app carga 20 focos con 20 ids únicos. Los duplicados son features Point y el cargador solo procesa polígonos. Los puntos de visita se descartan, pero el desvío es 6,9 m de mediana (máx 23,8) — dentro del ruido de GPS | ✅ **descartado, no era un bug** |
| 4 | **`supera_umbral` es opinión, no cálculo.** Los 26 umbrales son prosa libre | `data/umbrales.json`: **14 computables + 12 declarados no computables** con motivo. Ningún número inventado. `js/umbral.js` calcula; la unidad se elige de lista y aparece selector de estadio/destino. **Con punto elegido por el satélite el veredicto dice "referencia", nunca "supera el umbral MIP"** | ✅ |
| 5 | **El ranking miente:** rotula cohortes `EST-*` como `declarada` | Decide por el prefijo del estimador, no por descarte. Columna → `cohorte_origen`. Test dedicado. Verificado en datos reales: las 6 filas dicen `ESTIMADA-FENOLOGIA` | ✅ |
| 6 | **3 silencios:** el informe decía "sin anomalías" cuando el motor no pudo correr | El motor ya los registraba; el silencio estaba en `p5_report.py`, que no los mencionaba. Bloque **"Cobertura del análisis"** en la portada. Verificado renderizando caso peor y caso limpio | ✅ **desplegado** (commit `ff7b569`) |
| 7 | **`FOCOS_ENDPOINT` declarado pero nunca leído** | Red primero → caché offline → empaquetado, con la fecha de escena y el origen a la vista. Agregado a `KEEP` del service worker (si no, cada actualización borraba lo descargado) | ✅ |
| 8 | **No existe el 2º cliente** | Alta = **1 archivo JSON en `PIX_ALERTA/clientes/`, cero Python**. `clientes.py` + `correr_todos.py`. Aislamiento **verificado leyendo las carpetas**, no por confianza; un cliente que falla no frena a los demás | ✅ |

**29 pruebas en verde** (14 del criterio + 15 de la capa multi-cliente). APK **v1.0.8 firmada**
con el mismo certificado que 1.0.6.

---

## 5. Calendario

### Sem. 1–2 (jul–ago) — Cerrar el lazo con el trigo que queda
El trigo de invierno da 4-6 semanas de óptica ~3× mejor. **Ensayo del LAZO, no del detector**: que se
rompa en agosto con imágenes fáciles y no en enero con la campaña corriendo.
- Bloqueantes 2, 3, 5, 6
- Ida y vuelta real: 20 puntos, 1 técnico, ficha cerrada antes de ver el mapa
- **Vos:** conseguir el técnico + media jornada de campo

### Sem. 3–5 (agosto) — Primer cliente que PAGA
Cerro Alto, HDS y consultores que ya te conocen. CAC cero, ingreso en semanas.
- Propuesta de 1 página: ahorro Embrapa adelante, no-prometidos por escrito
- Alta Asaas + Pix Automático (R$ 1,99 fijo, sin recargo por recurrencia)
- ⚠️ **Al primer cobro: registrar licencia comercial GEE** (plan Limited, sin cuota mínima)
- **Vos:** las conversaciones

### Sem. 6–8 (ago–sep) — Multi-cliente y entrega desatendida
Bloqueantes 4, 7, 8. Al cierre: cliente nuevo entra con su GeoJSON + fecha de siembra.
- **Vos:** nada

### Sem. 9–10 (septiembre) — Armar la validación ANTES de sembrar
Una vez que la campaña arranca ya no se puede diseñar el muestreo sin sesgar.
- Estratos **con verde incluido**, sorteo aleatorio, guardar probabilidades de inclusión
- Técnico **a ciegas** del nivel de alerta (la app ya tiene el modo, está apagado: `MODO_CIEGO:false`)
- n calculado, no adivinado
- Métrica: **precisión@K con IC + PR-AUC + prevalencia declarada. NUNCA exactitud global**
- **Vos:** acordar el K con el cliente por escrito

### Oct 2026 → Abr 2027 — Campaña de validación
Entrega cada 10 días, el técnico devuelve. Al cierre: **un número propio** que hoy no tiene nadie en el rubro.

### May 2027 — El número propio se vuelve el argumento
Recién ahí tiene sentido escalar a marca blanca con consultores y buscar el cambio de pagador
(banco / seguro / certificación).

---

## 6. Precio

**Corregido:** el borrador anterior proponía ticket bajo por lote. Error.

Cobrar por hectárea es pelea perdida: EOSDA USD 1,25–1,40/ha/año, Auravant R$ 3,95, Aegro ~R$ 5.
Eso es precio de plataforma, sin margen. El **servicio** de AP se paga R$ 30–80/ha/ciclo.

**El ticket bajo mata:** con ARPA < USD 10/mes solo el 5,3% logra GRR > 85% (ChartMogul, n>2.100).
10 clientes a USD 500 > 200 a USD 25 — y con diálisis 3×/semana la segunda cartera es inatendible.

| Plan | A quién | Precio | Incluye |
|---|---|---|---|
| **Hacienda** | Productor con administración propia, 1.000–5.000 ha | R$ 1.500–2.500/mes (por campaña) | Ranking c/10 días, APK, informe, aviso |
| **Consultor** | Agrónomo con cartera | R$ 900/mes + R$ 400 por hacienda extra | Lo anterior con su marca + datos crudos |
| **Acercamiento** | Complemento | R$ 300/lote | Pipeline de rásteres sobre 1 lote del top-K |

Ancla internacional: **FarmQA USD 800/asiento agrónomo/año + USD 199/productor**.
**Cobro:** Asaas + Pix Automático (BR, R$ 1,99 fijo) · Paddle (USD, única verificada que paga a
Bolivia **y** Brasil — Wise NO opera con Bolivia).

---

## 7. Expectativa honesta y riesgos

Con 6–10 cuentas pagando: **USD 1.500–4.000/mes en año 1.** No es proyección optimista — de ~937
productos con revenue verificado por Stripe, **54% factura cero** y solo ~5% supera USD 100k/año; el
caso mejor documentado de servicio productizado tardó **3 años** en llegar a USD 10k/mes.
**Presupuestar 2-3 años, no 6 meses.** El límite es la adquisición (tu tiempo y tu salud), no la entrega.

| Riesgo | Prob. | Contención |
|---|---|---|
| El cliente no entrega la planilla de siembra | Alta | Cohorte estimada por fenología, rotulada como estimada. Degrada, no bloquea |
| Nubes: hueco peor caso **66 días** Santa Cruz, **147** Mato Grosso | Cierta | Va en el contrato como número. Entregar c/10 días SIEMPRE; sin imagen → producto degradado declarado |
| La validación sale en contra | Real | Nadie lo demostró, ni la competencia. Se sabe en may-2027 con plata de clientes, no con una ronda |
| Sesgo de verificación (el técnico solo va a los rojos) | Alta si no se diseña | Estrato verde obligatorio + técnico ciego. Por eso la Fase 4 va ANTES de octubre |
| Mapa mal normalizado con logo bonito llega al cliente | Media | QA humano de cada entregable el 1er trimestre. Ver `feedback_verify_layer_ranges` |

---

## 8. Primer paso

Arrancar por los 4 arreglos que no dependen de nadie y hacen falta para el ensayo con el trigo:
**bloqueantes 2, 3, 5 y 6.** Semana 1, sin decisiones tuyas pendientes.

En paralelo, lo único tuyo: **pedir la planilla de siembra.** Es el bloqueante más largo del plan y
el único que no puedo destrabar.
