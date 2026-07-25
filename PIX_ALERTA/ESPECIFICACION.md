# PIX ALERTA — Especificación de construcción

**Motor de alerta multicultivo para dirigir el scouting de campo.**
Estado: especificado, sin construir. Fecha: 2026-07-24.

Documento de propuesta (el *por qué*, con toda la evidencia):
https://claude.ai/code/artifact/8c0dcb41-2448-48ab-a28d-744a93a0030e

Este archivo es el *qué construir*. Está pensado para retomarse en frío.

---

## 0. Qué es y qué NO es

**Es** un sistema que cada ~10 días ordena N lotes por prioridad de visita y, dentro de los
priorizados, demarca focos, para que el productor mande sus técnicos a donde conviene mirar primero.

**NO es** un diagnosticador. No dice qué plaga ni qué enfermedad hay. No detecta antes que el ojo
humano. No estima severidad absoluta.

**La frase que define el producto:** *"hago que el MIP sea aplicable en tus 200 lotes"*. No
*"detecto la plaga por satélite"*.

### Por qué esa frase vende y la otra no

| Eslabón | Evidencia |
|---|---|
| Decidir por umbral vs por calendario | −44% aplicaciones de insecticida, −40% costos, sin perder control ni rendimiento. Meta-análisis 126 estudios / 466 ensayos / 34 cultivos. DOI 10.1038/s43247-025-02643-0 |
| Sistemas de apoyo a la decisión | ≥50% menos fungicida sin aumentar enfermedad, 80 experimentos. DOI 10.1038/s43247-021-00291-8 |
| **MIP en soya, efecto medido por Embrapa** | **1,02 aplicaciones con MIP vs 3,36 sin MIP = R$ 270,16/ha de ahorro, sin pérdida de productividad** (n=119 URTs, campaña 2024/25) |
| **Adopción real del MIP en soya** | **23,5% → 27,7% → 31,4% → 32,9%** (campañas 2021/22 a 2024/25). 76% lo conoce, 25% lo usa |
| Dirigir el scouting con mapa satelital | **Sin ensayo publicado.** Nadie lo comparó contra scouting sistemático |

Embrapa reconoce por escrito que *"o MIP-Soja tem sido abandonado"* y que se aplica *"com base em
critérios subjetivos, muitas vezes programadas com base em calendários"* (Doc 143, 2018).
El manual SP-17 dice que en áreas extensas el registro por talhão permite *"priorizar a realização
do controle nas áreas com maior nível populacional da praga"* — que es literalmente el producto.

En caña, el sector lo pide por escrito: STAB describe *"amostragens abaixo dos níveis mínimos
recomendados… redução das equipes de campo"*, y una presentación en evento Embrapa pide
*"novos métodos mais rápidos e precisos"*. Daño potencial estimado ~R$ 9.400 M/año; aun con 70% de
control quedan ~R$ 2.800 M/año.

---

## 1. Decisiones ya tomadas (no reabrir sin motivo)

1. **Dos ejes de dosel, no cuatro.** Sobre datos reales de 131 lotes, los 4 índices del motor viejo
   daban PC1 = 92,5% y número efectivo de índices independientes = 1,17. Se conservan un eje de
   humedad y uno de senescencia.
2. **Cero umbrales absolutos.** No transfieren entre sitios, campañas ni cultivares.
3. **Cero cuantiles.** Son una cuota: siempre pintan un % fijo de rojo aunque el campo esté sano.
4. **Alfa declarado en todo.** El nivel de alerta tiene que ser auditable.
5. **El satélite prioriza; el umbral del MIP decide.** La herramienta se acopla al protocolo MIP
   existente, no lo reemplaza.
6. **Cadencia de ENTREGA, no de óptica.** Se entrega cada 10 días siempre; si no hubo escena limpia
   se entrega producto degradado y declarado como tal.

---

## 2. Arquitectura — los 8 pasos

### Paso 1 · Máscara
- Nube **y sombra de nube**. `s2cloudless` **NO produce clase de sombra** — usarlo solo deja el
  sistema ciego al artefacto que más se parece a un foco. Sumar Fmask 4.0 (DOI 10.1016/j.rse.2019.05.024)
  o equivalente con clase de sombra. Dilatar la máscara.
- Compuerta por **cobertura vegetal fraccional (FVC)**, no por NDVI absoluto. Asumir incertidumbre
  real RMSE ≈ 0,17 (DOI 10.3390/rs12060912), no el 0,04 teórico.
- **Buffer negativo de 5 m** y descartar lotes que queden con **< 8 píxeles limpios** o que pierdan
  **> 60%** de su superficie. Criterio numérico publicado por el JRC: DOI 10.3390/rs12142195.
- ✅ **BSI: CORREGIDO 2026-07-24 — la cita NO está rota.** Se decía que "no se puede citar".
  Es falso: el paper se recuperó del Wayback Machine y **se leyó**. Es **Rikimaru, Roy &
  Miyatake (2002), "Tropical forest cover density mapping", Tropical Ecology 43(1):39-47,
  ISSN 0564-3295**, fórmula en la página 43. PDF archivado en `referencias_primarias/`
  porque tropecol.com es hoy un dominio parqueado. Cuatro precisiones para citarlo bien:
  **(1)** no tiene DOI y no hay que inventarle uno; **(2)** en el paper se llama **BI**, no BSI;
  **(3)** la fórmula original termina en `x100+100` sobre DN de 8 bits (rango 0-200) — la forma
  normalizada (−1,+1) sobre reflectancia es una **adaptación** y hay que decirlo así;
  **(4)** la primogenitura es **Rikimaru & Miyatake 1997** (ACRS Kuala Lumpur), misma fórmula
  verbatim; *"Roy et al."* como fuente separada **no existe**.
  ⚠️ Lo que sí es folclore son las fuentes de terceros: `awesome-spectral-indices` cita un
  link muerto de CiteSeerX con un ID interno **disfrazado de DOI**, y Sentinel Hub distribuye
  esta fórmula citando a Nguyen 2021, que es el paper del **MBI** (otro índice).
  Sigue siendo cierto que **no distingue rastrojo seco**, y que Rikimaru **nunca validó BI**
  contra suelo desnudo medido (es una de 4 entradas de un PCA). Alternativas verificadas:
  MBI (DOI 10.3390/land10030231), composites GEOS3/SYSI (DOI 10.1016/j.rse.2018.04.047).

- ⚠️ **"NDSIsw" era un MISNOMER y se retiró del criterio.** La fórmula (B11−B12)/(B11+B12)
  **no es un NDSI**: el NDSI real (Hall, Riggs & Salomonson 1995, DOI
  10.1016/0034-4257(95)00137-P) es de **nieve** y usa verde/SWIR1. La fórmula que se usaba es
  el **NDTI — Normalized Difference *Tillage* Index** (van Deventer, Ward, Gowda & Lyon 1997,
  PE&RS 63(1):87-93, **sin DOI**; PDF archivado). Idéntico a NBR2 (USGS) y NSDSI3
  (10.1016/j.isprsjprs.2019.06.012). El nombre equivocado viene de Index DataBase id=57, que
  es *Normalized Difference **Salinity** Index*, marcado "derived" y apoyado en una tesis de
  maestría sobre ASTER.
  **Y no sirve para estrés de cultivo:** su uso publicado es residuo, labranza, humedad de
  suelo desnudo, quema y salinidad. Hively et al. 2021 (10.3390/rs13183718) documenta que la
  **vegetación verde lo degrada**. Se conserva como capa de suelo/residuo y se sacó de las
  features de enfermedad.

### Paso 2 · Estratificación
Dos ejes, ambos obligatorios:
- **Zona de suelo / productividad.** Sin esto, terrazas y subsuelo erosionado se marcan como
  anomalía (ya pasó en trigo SA/SF, documentado en la v7).
- **Cohorte de siembra.** Con 200 lotes escalonados, sin cohorte lo que se mide es la fecha de
  siembra, no la plaga.

### Paso 3 · Magnitud
Índice de suficiencia contra el percentil alto **de la propia cohorte**, no contra tabla.
DOI 10.1007/s11119-012-9301-6 (único enfoque de referencia interna con despliegue comercial validado).

### Paso 4 · Agrupamiento espacial
- Getis-Ord Gi* con **permutación condicional**, no la aproximación gaussiana analítica.
- **Agregar a 20–30 m antes de testear.** Un test por píxel de 10 m infla la corrección y viola el
  supuesto.
- FDR de Benjamini-Hochberg como default (DOI 10.1111/j.0016-7363.2006.00682.x aplica FDR
  explícitamente a Gi*/LISA). Benjamini-Yekutieli si se quiere ser defensivo ante cliente.
- ⚠️ **El FDR nominal no es el FDR real bajo autocorrelación.** Se puede controlar en promedio y
  aun así tener una campaña llena de rojos falsos (DOI 10.1198/016214506000001211). Si los p-valores
  salen sesgados, estimar nulo empírico.

### Paso 5 · Persistencia temporal
Carta EWMA sobre los residuos respecto de la trayectoria fenológica esperada de la cohorte,
**en tiempo térmico, no en fecha calendario**. Referencia satelital: DOI 10.1109/TGRS.2013.2272545.
Precedente intra-campaña más cercano: DOI 10.1016/j.compag.2022.106983.

⚠️ **BFAST / CCDC / COLD no sirven tal cual**: todos exigen un histórico estable plurianual por
píxel, que dentro de una campaña de 4-5 meses no existe. Y sus latencias publicadas (96–240 días)
son para disturbio forestal — un cultivo anual no da ese margen.

### Paso 6 · Prior meteorológico (opcional, fase tardía)
Solo donde exista modelo validado **y recalibrado localmente**. Mejor candidato: brusone de trigo,
única cadena completa modelo → validación → despliegue en Brasil (DOI 10.1016/j.cliser.2025.100589).
⚠️ Que combinar clima y satélite reduzca falsos positivos es **hipótesis razonable sin respaldo
empírico publicado**. Declararlo como componente no validado. Si se valida, es publicable.

### Paso 7 · Salida
**Probabilidad posterior** que incorpore la prevalencia del año (DOI 10.1046/j.1365-3059.2002.00741.x),
no un corte fijo. El mismo detector produce muchos más falsos positivos en año de baja presión.

### Paso 8 · Validación
Ver sección 4. Es lo que separa producto de piloto.

---

## 3. El lazo de retorno — construir esto PRIMERO

Hoy nada captura qué encontró el técnico. Sin eso no hay precisión medible, no hay calibración y no
hay nada que demostrarle al cliente. **Ninguno de los 15 competidores revisados lo tiene documentado.**

Va en la APK de campo. Esquema mínimo por visita:

```
punto_id            # estable, sobrevive el viaje de ida y vuelta
lote_id
fecha_visita
estrato_asignado    # rojo | amarillo | verde  ← NO se le muestra al técnico
hallazgo            # nada | plaga | enfermedad | deficiencia | daño mecánico | otro
especie             # vocabulario controlado por cultivo
severidad           # escala del protocolo MIP del cultivo
conteo              # nº por metro / % plantas atacadas, según protocolo
supera_umbral       # booleano, calculado contra el umbral MIP
foto
observacion
```

**Regla no negociable: el técnico no ve el nivel de alerta antes de registrar.** Si sabe que va a un
rojo, encuentra algo.

---

## 4. Protocolo de validación

El error que arruina toda medición se llama **sesgo de verificación** (DOI 10.2307/2530820): si solo
se verifica donde el sistema marcó rojo, la sensibilidad se sobreestima siempre.

Solución de diseño, la misma que usan los sistemas de alerta de deforestación
(DOI 10.1016/j.rse.2014.02.015):

1. El mapa de cada fecha define estratos rojo / amarillo / **verde**.
2. Sorteo aleatorio dentro de cada estrato, **incluido el verde**. Sin muestras en verde no hay
   falsos negativos y no se puede calcular nada.
3. Sobremuestrear rojo (es raro) pero **guardar las probabilidades de inclusión** y estimar con pesos.
4. Técnico a ciegas del nivel de alerta.
5. Ficha cerrada, completada antes de ver el mapa.

**Métrica:** precisión en el top-K (de los K lotes a los que se mandó al técnico, cuántos tenían
problema confirmado), donde K = capacidad real de scouting. Reportar junto con **PR-AUC** y la
**prevalencia de la campaña**. Nunca exactitud global: con prevalencia baja, decir "no hay nada" da
95% de exactitud y cero valor (DOI 10.1371/journal.pone.0118432).

⚠️ No existe literatura agronómica que valide con precisión@K. Es la métrica correcta pero hay que
definirla y defenderla; no hay antecedente en el que apoyarse.

---

## 5. Orden de construcción

**Paso 0 — YA RESUELTO, ver `AUDITORIA_2026-07-24.md` §1 y `DISPONIBILIDAD_MULTISITIO.md`.**
Medido: **48% de las dekadas tienen escena útil a escala de lote** en Santa Cruz (febrero 33%).
**La promesa de 5–10 días solo con óptico no se sostiene.** El orden de construcción vigente es el
de `METODOLOGIA_RECOMENDADA.md`, que corrige este documento: medición primero, detector después.

**Paso 1 — el lazo de retorno en la APK.** Sin esto todo lo demás es opinión.

**Paso 2 — generalizar el motor.** Sacar haciendas del código a configuración, estratificar por
cohorte, y producir el **ranking de los N lotes** además del mapa intra-lote. El ranking es el
entregable que el cliente consume: la lista de a dónde ir hoy.

**Paso 3 — una campaña de validación honesta.** Con el protocolo de la sección 4. Al final se tiene
un número propio, medido, sobre la zona y los cultivos reales — que ninguno de los 15 competidores
tiene.

**Paso 4 — persistencia temporal (EWMA) y prior meteorológico.**

---

## 6. Lo que hay que reutilizar

> ⚠️ **Actualizado 2026-07-24.** Esta tabla decía tres cosas que no eran ciertas: que el
> motor v7 estaba en la skill (la skill despacha **v6**), que la compuerta absoluta era
> parte de la base sólida (fue **retirada** por no transferir entre sitios), y no listaba
> PIX SCOUT, que es el activo de campo real. Ver `AUDITORIA_2026-07-24.md` y
> `CAMBIO_DE_CULTIVO.md`.

| Activo | Dónde | Estado |
|---|---|---|
| Motor de raster en producción | `PIXADVISOR_Sync/repo/scripts/` | Gi* sobre **residuo temporal** + FDR, Mahalanobis de 2 ejes, zona de suelo, compuerta **FVC**. Corre en la nube |
| Motor de ranking de lotes | `PIX_ALERTA/pix_alerta/` | EWMA sobre residuo vs cohorte, 13 puertas de aceptación. Corre a mano |
| ~~Motor de anomalías v7 en la skill~~ | skill `deteccion-anomalias-cultivos-satelital` | **La skill describe v6/v7 y quedó desactualizada**: instruye a usar BSI, Gi* sobre CIre crudo, `CIre_ref` de media de temporada y `NDVI>0.5`. Los cuatro fueron retirados por medición. No usarla como referencia hasta reescribirla |
| **PIX SCOUT** | `PIX_SCOUT/` | APK firmada, 123 fichas / 7 cultivos, foto obligatoria, cola offline, registro negativo. **El lazo de retorno real** |
| Revisión de literatura (trigo) | misma skill, `references/revision_literatura_2026-07-22.md` | 22 fuentes. Solo trigo — falta el resto de cultivos |
| Pipeline en nube funcionando | repo `Ncamargo50/pixadvisor-monitoreo-trigo` | GitHub Actions cron, cuenta de servicio GEE, PDF + GeoJSON + aviso WhatsApp. Corre solo |
| APK de campo | `pix-muestreo-apk` | GPS promediado, offline, cola de sync. Falta el esquema de formulario genérico |
| Patrón de automatización | skill `automatizacion-nube-github-actions` | `ee_init.py` + orquestador con exit codes 0/10/≠0 |

---

## 7. Protocolos MIP verificados (para acoplar la herramienta)

- **Soya**: 6 puntos (1-9 ha) / 8 (10-29) / 10 (30-99) / dividir >100 ha. Semanal hasta R7, paño de
  batida de 1 m de fila. Umbrales reproductivo: *Helicoverpa* 2 lagartas/m, *Spodoptera* 10/m,
  chinches 2/m (1/m si es semilla), 15% defoliación. Repetir a los 3-4 días cerca del nivel.
- **Trigo** (ed. 2026): mínimo 10 puntos por talhão. Pulgones 10% plantas infestadas o 10/espiga;
  *D. furcatus* 4/m² vegetativo, 2/m² reproductivo; corós 5/m².
- **Maíz**: *S. frugiperda* 10% de plantas con hojas raspadas. ⚠️ Hay **discrepancia entre documentos
  Embrapa** (otros dan 20% hasta 30 días, 10% de 40-60 días). Puntos/ha: no encontrado.
- **Sorgo**: mosca 1 hembra/panícula (cada 3 días en floración); *Helicoverpa*/*Spodoptera* 2/panícula.
- **Girasol**: ⚠️ **NO existen umbrales oficiales.** Embrapa lo admite; la norma 2026 obliga a
  monitorear sin fijar números. Declararlo diferencia, no debilita.
- **Caña**: broca 2 puntos/ha + I.I. sobre 20 cañas/ha; cigarrinha ⚠️ **dos NDE incompatibles**
  (IAC experimental 3-5/m vs sector 12/m — declarar cuál se usa); *Telchin licus* **no tiene NDE**,
  Embrapa lo declara explícitamente.

### Bolivia — el hueco es total, y es una oportunidad

**No existe protocolo oficial boliviano de monitoreo MIP con densidad de muestreo por hectárea.**
Verificado contra ANAPO, CIAT Santa Cruz, INIAF y SENASAG. Lo único institucional con umbrales
accesible es la cartilla ANAPO Nº5 de 2011 y la Hoja Divulgativa 38 de 2024.

- **Soya (ANAPO)**: paño de 1 m para gusanos y chinches; 10 m lineales para picudo; 100 plantas para
  barrenador de brotes; visual con lupa para mosca blanca, ácaros y trips. Semanal.
  Umbrales: chinches **2 por paño** (grano) / **1 por paño** (semilla); picudo negro 1 adulto/m
  hasta V3 y 2/m de V3 a V6; barrenador 25-30% de plantas atacadas; gusanos comedores de vainas
  10% de vainas atacadas; ácaros 10-20 por trifolio. Trips y mosca blanca: **sin umbral**.
  ⚠️ La cartilla de 2011 imprime *"40 gusanos de hasta 15 cm"* — es errata evidente del original
  (la fila siguiente dice 1,5 cm). No usar sin contrastar contra el manual 2024.
- **Densidad de puntos por lote o por hectárea: NO EXISTE en ninguna fuente boliviana.**
- **Maíz y sorgo en Bolivia: NO EXISTE protocolo oficial.**
- Los manuales grandes de ANAPO (soya 2024, trigo 2022, girasol 2020) sí tienen capítulos de niveles
  críticos, pero **son de pago y su contenido no es accesible en línea**. Hay que comprarlos.
- ⚠️ El INSA publica densidades por superficie (3-5 puntos hasta 20 ha, 7-9 de 21 a 50, 11 de 51 a
  100) pero es para **ajuste de siniestros de seguro, NO para scouting MIP**. No citarlo como tal.

### Argentina — la mejor referencia de densidad disponible para la región

- **AAPRESID**: *"una estación de muestreo cada 10-15 ha dentro de la unidad de manejo, con un
  mínimo de 4-5 para lotes menores a 40-50 hectáreas"*, **estaciones fijas georreferenciadas**,
  frecuencia mínima semanal, cada 3-4 días si se está cerca del umbral. Es la referencia práctica
  más útil que se encontró para calibrar el K del producto.
- **INTA Marcos Juárez** publica un boletín mensual con umbrales vigentes (ISSN 2953-3953). Es una
  **fuente viva** que conviene seguir. Cogollera en maíz: 20% de plantas con daño *y presencia de
  orugas*, con la advertencia de que ya hay fallas en eventos Bt con Vip3Aa20.
- **INTA Reconquista tiene tabla completa de umbrales para trigo** y guía de girasol con densidad.

### ⚠️ Respaldo institucional para la regla de que los umbrales no transfieren

INTA Reconquista publicó que los umbrales de defoliación de soja vigentes en Argentina fueron
establecidos en la zona núcleo, y que en el norte de Santa Fe **"con 33% de defoliación en R1 el
rendimiento se vio afectado en un 18%"** mientras que en la zona de origen el efecto aparecía recién
**a partir del 67%**. Conclusión textual: *"los umbrales actualmente vigentes subestiman la reducción
de rendimiento"* en esas condiciones agroecológicas.

Es decir: **una institución oficial documentó que un umbral absoluto falló al cambiar de región
dentro del mismo país.** Es el respaldo citable para la regla del proyecto de no usar umbrales
absolutos transferidos.

---

## 8. Lo que NUNCA hay que prometer

1. "Detectamos la roya antes de que la veas." No demostrado con Sentinel-2. El paper de referencia
   descarta como sano todo lo que esté bajo 20% de índice de enfermedad porque el píxel de 10 m no
   lo registra.
2. "Te decimos qué tiene el lote." El índice detecta estrés, no causa.
3. "Detectamos el foco inicial." Cuando es detectable ya mide 100-400 m² y se ve desde la camioneta.
4. "Sirve para chinches." **Evidencia negativa publicada**: ni el hiperespectral de proximidad
   detecta su daño (DOI 10.3390/agronomy12071516).
5. "Sirve para nematodos, mosca blanca, plagas de caña, sorgo, girasol o pastura." Sin respaldo.
6. "El radar detecta la enfermedad." Ve a través de las nubes; detectar enfermedad, no demostrado.
7. Exactitudes de otros países aplicadas a la zona propia. Lo validado es trigo (China), arroz
   (China/España), maíz (Bangladesh).

**Un límite agronómico que hay que tener presente:** las plagas se concentran en la **bordadura**.
Embrapa documenta un gradiente de 67 → 43 → 18 → 5 → 0 chinches por metro hacia el interior. Un
píxel de 10 m promediando 50 ha no lo ve. La franja de borde debe tratarse como **estrato propio**,
no solo como ruido a erosionar.

---

## 9. Lo que sí está validado y sirve de cimiento

- **El eje temporal es la única vía demostrada de especificidad** con bandas anchas: oídio de trigo
  84,6% multitemporal vs 76,9% monoescena, validado en región distinta (DOI 10.3390/s18103290).
- **Cogollero en maíz con S2 temporal: 72-82% en test independiente**, 6.998 observaciones en 579
  lotes, AUC 0,83-0,95 (DOI 10.1016/j.jag.2025.104516). Mejor antecedente disponible.
- Roya vs deficiencia de N con serie temporal: 91% (DOI 10.3389/fpls.2023.1250844).
- Brusone de arroz con S2 + Random Forest: hasta 94% (DOI 10.3390/agriculture15242560).

---

## 10. Competencia — el hueco

15 productos revisados. **Ninguno publica su criterio de alerta. Ninguno publica validación
independiente de su motor.** El líder explícito del segmento (Cropwise Easy Scout, Syngenta)
clasifica prioridad con el **Δ del NDVI promedio del lote** — sin control de error espacial, sin
cohorte, sin separar suelo. El motor v7 ya es técnicamente superior.

Único con paper independiente: xarvio (BASF), pero es trigo en el norte de Alemania y valida el
*timing* de fungicida, no las zonas (DOI 10.3390/su142315599).

Precios de plataforma: EOSDA ~USD 1,25-1,40/ha/año, Auravant Pro ~R$ 3,95/ha/año. **Competir por
precio de plataforma no tiene sentido**; el margen está en criterio declarado y validación local,
que nadie tiene para Brasil/Bolivia.

Taranis cerró Brasil en julio 2025 (causa comercial documentada; causa técnica no encontrada).
El VP para LatAm de Farmers Edge: *"o B2C no Brasil, para a agricultura digital, não é um negócio
que gera valor"* — pasaron a vender a través de canales.

---

## 11. Preguntas abiertas

1. **¿Cuántas ventanas de 10 días tienen escena limpia en Santa Cruz?** Sin responder esto no se
   puede prometer cadencia. Se resuelve con GEE sobre datos propios.
2. **¿Qué K real tiene el cliente?** ¿A cuántos lotes puede ir por semana con los técnicos que
   tiene? Ese número define la métrica y el diseño del entregable.
3. **¿Qué cultivos primero?** La evidencia es más fuerte en maíz (cogollero) y trigo. Soya es el
   cultivo principal pero es donde la roya no tiene respaldo satelital.
4. **¿Zona de suelo desde qué fuente?** ¿Barbecho histórico, mapas existentes, muestreo?
5. **¿El prior meteorológico con qué datos?** ERA5 es de 11 km — para una hacienda es un solo píxel.
   ¿Estación propia?

---

## Referencias verificadas

Todos los DOI de este documento fueron resueltos contra Crossref o el editor. Los que no se pudieron
verificar están marcados como tales en el cuerpo y **no deben citarse ante un cliente**.

Memoria del proyecto: `project_motor_alerta_scouting.md`
