# Barrido de GitHub — qué sirve para PIX_ALERTA

**4 de agosto de 2026.** Búsqueda dirigida en GitHub de herramientas de teledetección,
sensoriamiento remoto y agricultura de precisión, evaluadas contra los problemas concretos del
motor.

Criterio de evaluación, aprendido en la auditoría del 3-ago: **"existe" y "aplica" son dos
preguntas distintas**, y la segunda es la que falla más seguido. Cada entrada lleva veredicto
explícito.

---

## 🟢 LO QUE APLICA YA — y lo usé para auditar el motor

### awesome-spectral-indices — el catálogo con DOI de cada fórmula

**Repo:** `awesome-spectral-indices/awesome-spectral-indices` · **1.154★** · activo ago-2026
**Paper:** Montero et al., *Scientific Data* (2023). DOI 10.1038/s41597-023-02096-0
**Licencia:** MIT · **280 índices** con fórmula, bandas y referencia bibliográfica

Es un JSON descargable (`output/spectral-indices-dict.json`) más un mapeo de bandas por
plataforma (`output/bands.json`). No es una librería que haya que adoptar: **es una fuente de
verdad contra la cual verificar.**

**Por qué importa acá:** este repositorio tiene documentado un historial de fórmulas mal citadas
—el NDWI de Gao que Sentinel-2 no puede calcular, el PSRI con B2 y no B3, el REIP con 700+40 en
vez de 705+35. Un catálogo con DOI por índice es exactamente el antídoto.

#### ✅ AUDITORÍA HECHA: las fórmulas del motor contra el catálogo

| Índice | Motor | Catálogo (→ S2) | Veredicto |
|---|---|---|---|
| **NDVI** | (B8−B4)/(B8+B4) | (B8−B4)/(B8+B4) | ✅ **IDÉNTICO** |
| **PSRI** | (B4−B2)/B6 | (B4−B2)/B6 | ✅ **IDÉNTICO** |
| **NDMI** | (B8A−B11)/(B8A+B11) | (B8−B11)/(B8+B11) | ⚠️ difiere solo B8A vs B8 |
| **NDRE** | (B8A−B5)/(B8A+B5) | (B8−B5)/(B8+B5) | ⚠️ difiere solo B8A vs B8 |
| **CIRE** | (B7/B5)−1 | (B8/B5)−1 | ⚠️ **DIFIERE** (B7 vs B8) |

**Las dos diferencias de B8A vs B8 NO son errores del motor — son mejoras deliberadas y
documentadas.** El catálogo usa B8 (NIR ancho) por convención genérica; el motor usa B8A porque:

- B8 tiene **FWHM de 118 nm** e integra media meseta NIR; **B8A tiene 20 nm** y contiene
  exactamente los 850-865 nm que pide Hardisky para el NDII/NDMI.
- **B8A es nativo de 20 m**, igual que B11 y B5. Usar B8 (10 m) obliga a remuestrear una de las
  dos y mete mezcla espectral en los bordes de lote.

En los dos casos, **la elección del motor está mejor fundamentada que la del catálogo**.

**La discrepancia de CIRE sí es real** (B7=782,8 nm contra B8=832,8 nm), pero CIRE **no está en
producción** — los ejes son NDMI y NDRE. Vale anotarla: la formulación original de Gitelson usa
NIR de ~770-800 nm, así que **B7 es más fiel al paper original que B8**. Si algún día CIRE entra,
esta decisión ya está razonada.

**Confirmaciones útiles que trae el catálogo:**
- **NDMI** referencia DOI 10.1016/S0034-4257(01)00318-2 → Wilson & Sader 2002, **la cita que ya
  estaba documentada acá**.
- **NDWI** es (G−N)/(G+N), McFeeters — **no** es NDMI. Confirma la distinción que ya estaba hecha.
- **PSRI** usa B (azul), Merzlyak 1999. Confirma el uso de B2.

**Acción concreta:** agregar un test que valide las fórmulas del motor contra el JSON del
catálogo, con las dos excepciones documentadas. Convierte una auditoría manual en una regresión
permanente. **Costo: bajo. Valor: alto.**

---

## 🟡 LO QUE VALE MIRAR, CON RESERVAS

### eemont — extensión de Google Earth Engine para Python

**Repo:** `davemlz/eemont` · **449★** · activo ago-2026 · MIT
**Paper:** JOSS, DOI 10.21105/joss.03168

Agrega métodos a los objetos de GEE: escalado automático, enmascarado de nubes, cálculo de
índices espectrales (usa awesome-spectral-indices por debajo), cierre de nubes, etc.

**Veredicto: NO adoptar como dependencia, SÍ usar como referencia cruzada.**

El motor ya tiene implementado y **auditado** todo lo que eemont ofrece: máscara híbrida SCL
dilatada + CloudScore+, escalado por 10000, índices verificados banda por banda. Cambiar código
auditado por una dependencia externa reintroduciría el riesgo que ya se cerró.

Lo que sí vale: **contrastar el resultado del motor contra eemont en una escena**, como control
independiente. Si dan distinto, uno de los dos tiene un bug.

### BFAST — detección de quiebres en series temporales

**Repos:** `bfast2/bfast` (53★, R, mar-2026) · `diku-dk/bfast` (43★, Python GPU, 2023) ·
`bfast2/geeBfastMonitor` (75★, JavaScript sobre GEE, 2020)

**Veredicto: mirar el método, no adoptar el código.**

La investigación del 3-ago ya midió por qué: sobre 151.200 series simuladas con verdad conocida,
**BFAST Monitor mejora cuando le sacan datos** (Awty-Carroll et al. 2019) — propiedad valiosa
para el régimen de 48% de dékadas útiles. Pero contra verdad-terreno real, EWMACD y la familia dan
**omisión del 65-70%** en disturbios sutiles.

Y hay un problema de encaje: BFAST trabaja sobre **regresión armónica** de series largas
(años), mientras el motor ajusta una **recta sobre ~120 días** dentro de una campaña. No son
intercambiables. El aporte sería conceptual —la idea de monitorear contra un modelo estacional
ajustado en un período de referencia— y eso ya está resuelto de otra forma.

### openEO — cliente Python

**Repo:** `Open-EO/openeo-python-client` · **210★** · activo ago-2026

**Veredicto: es LA ruta de salida cuando GEE deje de servir, no un cambio de hoy.**

Sigue vigente lo que ya está anotado: GEE gratuito **prohíbe cobrar**, y el disparador comercial
llega con el primer cliente que pague. openEO + Copernicus Data Space es la alternativa, y ESA
WorldCereal demostró que un sistema global completo corre ahí.

No es trabajo para ahora, pero el cliente Python está maduro y activo — cuando toque migrar, la
herramienta existe.

### spyndex — awesome-spectral-indices en Python

**Repo:** `awesome-spectral-indices/spyndex` · **250★** · activo ago-2026

Calcula cualquiera de los 280 índices sobre numpy, pandas, xarray o GEE. **Útil para el arnés de
medición**, donde probar un índice candidato hoy exige escribirlo a mano. No para producción.

---

## 🔴 LO QUE NO APLICA, Y POR QUÉ

| Repo / familia | Por qué no |
|---|---|
| **Detección de enfermedad con deep learning** (`Wheat-Disease-Detection` y similares, 6-18★) | Todos operan sobre **fotos de hojas**, no sobre píxeles satelitales de 10-20 m. Es el mismo error que el paper de roya asiática medido en laboratorio |
| **`px39n/Awesome-Precision-Agriculture`** (139★) | Última actualización **2020**. Lista de papers de UAV y deep learning, sin código aplicable |
| **`sacridini/Awesome-Geospatial`** (5.235★) | Catálogo general de herramientas. Útil para descubrir, nada específico al problema |
| **`torchgeo`** (4.131★), **`geoai`** (3.257★) | Requieren GPU y datasets etiquetados grandes. El motor no tiene ninguna de las dos cosas, y la investigación ya midió que los foundation models se degradan al cambiar de región |
| **Delineación de bordes de lote** (`agribound` 82★, otros) | Los lotes ya vienen del cliente con ID estable. Problema resuelto |
| **`sits`** (Python, 3★) | El paquete serio es el de R (CRAN); el port Python está incipiente |

---

## Lo que NO encontré, y es un hallazgo

Busqué específicamente y **no existe repositorio público** de:

1. **Corrección del escalón instrumental entre S2A/S2B/S2C.** Ni una herramienta, ni un script.
   El problema que se corrigió ayer —B5 en 707,1 nm contra 703,8-704,1, escalón de 0,052 en
   NDRE— no tiene solución publicada en GitHub. La búsqueda "band adjustment landsat sentinel"
   devolvió **cero resultados**.
2. **Detección de anomalías intra-lote contra la trayectoria del propio píxel**, con control de
   tasa de falsa alarma. Coincide con lo que la revisión bibliográfica ya había encontrado: nadie
   valida ese paquete completo.
3. **Herramientas de muestreo estratificado y evaluación de exactitud** para teledetección
   agrícola (tipo Olofsson et al.). Las búsquedas de "accuracy assessment sampling" y "area
   estimation stratified" devolvieron **vacío**.

Los tres refuerzan la misma conclusión: **el nicho del motor sigue sin competencia publicada,
tampoco en código.**

---

## Acciones, por relación valor/esfuerzo

| # | Acción | Esfuerzo | Valor |
|---|---|---|---|
| **1** | **Test de regresión de fórmulas** contra el JSON de awesome-spectral-indices, con las dos excepciones de B8A documentadas | Bajo | Alto — convierte la auditoría de hoy en permanente |
| **2** | Contrastar una escena del motor contra **eemont** como control independiente | Bajo | Medio — si difieren, uno tiene un bug |
| 3 | Usar **spyndex** en `medicion/` para probar índices candidatos sin escribirlos a mano | Bajo | Medio |
| 4 | Anotar la discrepancia de **CIRE** (B7 vs B8) en el código, con el razonamiento | Trivial | Bajo, pero evita rediscutirlo |
| — | ~~Adoptar eemont / BFAST / torchgeo en producción~~ | — | **Descartado**: reintroduce riesgo en código ya auditado |

**Nota sobre el punto 1:** el JSON del catálogo se puede versionar en el repo o bajar en el test.
Bajarlo en el test lo hace dependiente de red, que es mal patrón para una suite que corre en cada
push. **Conviene congelar una copia y actualizarla a mano**, igual que se hace con cualquier
referencia externa.
