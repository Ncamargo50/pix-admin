# Disponibilidad de imagen — medición multisitio y estado de constelaciones

Medición independiente contra el **catálogo oficial de Copernicus (OData API)**, 24-jul-2026.
5 temporadas de verano (nov–mar, 2021/22 a 2025/26).

**Complementa a `AUDITORIA_2026-07-24.md` §1, no lo reemplaza.** Aquella medición es mejor para
decidir (escala de lote, descarta nube **y sombra** por SCL, criterio ≥80% de píxeles válidos).
Esta agrega tres cosas que aquella no tiene: **comparación entre sitios**, **tamaño de los huecos**
y **estado real de las constelaciones**.

---

## 1. Las dos mediciones coinciden

| Medición | Escala | Criterio | Resultado Santa Cruz |
|---|---|---|---|
| `AUDITORIA` §1 (la buena para decidir) | **Lote** | ≥80% píxeles válidos, descarta nube + sombra SCL | **48% de dekadas con escena útil** → 52% de fallo |
| Esta (catálogo Copernicus) | **Escena** (~110×110 km) | `cloudCover` del metadato | 76,2% de fallo con cc≤20% · 37,5% con cc≤60% |

El `cloudCover` de escena es un proxy **pesimista** para un lote (el lote puede estar despejado con
el tile 60% nublado) y a la vez **optimista** frente a cirros no detectados. Por eso se reporta como
banda. **El 52% de fallo medido a escala de lote cae dentro de la banda 37,5%–76,2%.**
Dos métodos independientes, resultado consistente.

---

## 2. Comparación entre sitios — dato nuevo

Ventanas de **10 días** sin escena utilizable, temporada húmeda:

| Sitio | cc≤20% (estricto) | cc≤60% (laxo) | Mediana de nube de escena |
|---|---|---|---|
| **Sorriso, MT** | **85,0%** | 55,0% | **86,4%** |
| **Santa Cruz Norte, BO** | **76,2%** | 37,5% | **69,7%** |
| Maracaju, MS | 51,2% | 17,5% | 43,1% |
| Rio Verde, GO¹ | 42,5% | 11,3% | 57,1% |
| Cascavel, PR | 32,5% | 15,0% | 34,2% |

¹ Rio Verde cae en solape de órbitas → doble cobertura. No representativo de Goiás.

**Implicación comercial:** la promesa óptica es mucho más defendible en **Paraná** (falla 1 de cada 3
ciclos) que en **Mato Grosso** (falla 9 de cada 10). Si alguna vez se vende fuera de Santa Cruz,
el sitio cambia el producto.

---

## 3. Tamaño de los huecos — el dato que va al contrato

Hueco máximo sin escena cc≤35%, por temporada:

| Sitio | Medio | **Peor caso medido** |
|---|---|---|
| Santa Cruz, BO | 50,4 días | **66 días** |
| Sorriso, MT | 78,8 días | **147 días** |
| Maracaju, MS | 36,8 días | 70 días |
| Cascavel, PR | 23,0 días | 35 días |

Casos reales: **Sorriso 2024/25 tuvo CERO escenas con cc≤20% en toda la temporada.**
Santa Cruz 2023/24: 3 escenas en toda la temporada; hueco de 80 días.

**Un contrato que no contemple un hueco de 66 días genera incumplimiento en al menos una de cada
cinco temporadas.** Hay que declararlo por escrito.

---

## 4. La estación seca es otro producto

| Sitio | Mediana de nube húmeda | Mediana seca | Escenas cc≤20% húmeda → seca |
|---|---|---|---|
| Sorriso, MT | 86,4% | **3,6%** | 2,6 → **26,2** |
| Rio Verde, GO | 57,1% | 1,8% | 12,4 → 45,2 |
| Santa Cruz, BO | 69,7% | **31,0%** | 4,4 → **13,8** |
| Cascavel, PR | 34,2% | 34,5% | 12,2 → 14,0 |

En Santa Cruz el monitoreo óptico es **~3× mejor en invierno** (trigo, soya de invierno). En Mato
Grosso, **~10× mejor en la safrinha**. La cadencia de 10 días **sí es prometible en seca**.
Paraná no tiene estación seca útil, pero tampoco colapsa.

---

## 5. ⚠️ Sentinel-1: la revisita real medida es 12,6 días, no 6

Esto **hay que contrastar con el 87,3% de cobertura que reporta `METODOLOGIA_RECOMENDADA.md`**,
porque si ese cálculo asumió 6 días, la cobertura real sería menor.

Fechas únicas de producto GRD sobre el punto, por temporada:

| Temporada | Santa Cruz | Sorriso |
|---|---|---|
| Nov21–Abr22 | 9 fechas · 16,8 d · **hueco 100 d** (caída de S1B) | 12 fechas · 12,6 d |
| Nov22–Abr23 | 12 fechas · 12,6 d | 13 fechas · 11,6 d |
| Nov23–Abr24 | 11 fechas · 13,8 d | 12 fechas · 12,7 d |
| Nov24–Abr25 | 12 fechas · 12,6 d | 12 fechas · 12,6 d |
| Nov25–Abr26 | 12 fechas · 12,6 d (S1C) | 12 fechas · 12,6 d |
| 25-jun a 24-jul 2026 (post-reconfiguración) | 3 fechas en 29 d | 3 fechas en 29 d |

**Una sola órbita cubre el punto** → ~12,6 días reales en las cinco temporadas. La muestra
post-reconfiguración (29 días) es corta y **provisional**; todavía no muestra el 6-día nominal.
**Planificar con 12 días de SAR y tratar el 6 como upside.**

---

## 6. Estado de constelaciones (verificado en ESA/Copernicus, jul-2026)

- **Sentinel-2**: la nominal es **2B + 2C**, revisita 5 días. **Sentinel-2A fue el reemplazado**
  (cedió su posición a 2C el 21-ene-2025) y opera en **campaña de extensión prorrogada hasta el
  31-dic-2026**, a 36° de 2B. Sentinel-2D sucederá a 2B (fecha: no encontrada).
  ⚠️ Más pasadas **no dieron más escenas limpias**: Sorriso 2025/26 tuvo 38 pasadas y mediana de
  nube 92,7%.
- **Sentinel-1**: configuración final **S1C + S1D**, nominal 6 días. S1D operativo 1-may-2026,
  datos abiertos desde 17-abr-2026. **S1A terminado el 29-jun-2026.** Ver §5 sobre la revisita real.
- **Landsat 8+9**: 8 días combinados. **HLS v2.0** armoniza Landsat + S2 a 30 m, 1,6 días de
  revisita de pasada — pero es revisita de pasada, **no de píxel despejado**. En Sorriso suma ~30%
  más de intentos sobre un pool 86% nublado: mejora marginal, no rescata la promesa.
- **PlanetScope**: ~30 intentos/mes vs ~6. La mejor apuesta óptica. Planet reconoce que **~95% de
  sus fallos de ground-lock son por nube**. Precio público para LatAm: **NO ENCONTRADO**.
  No elimina rachas de 10+ días cubiertos: compra más intentos, no cielo despejado.

---

## 7. Literatura verificada que respalda esto

- **Nazarova, Martin & Giuliani (2020)**, *Remote Sensing* 12(11):1829, DOI `10.3390/rs12111829`.
  Rondônia: de 72 escenas anuales, **solo 10 completamente libres de nube (13,9%)**, y la nube alta
  *"follows a seasonal distribution (October to May)"* — exactamente la ventana de la soya de verano.
- **Simonetti et al. (2021)**, *Data in Brief*, DOI `10.1016/j.dib.2021.107488`. En zonas tropicales
  *"the annual average cloud percentage computed over the MGRS tile can be greater than 80%"*.
- **Flores-Anderson et al. (2023)**, *Scientific Data*, DOI `10.1038/s41597-023-02439-x`.
  Landsat+S2 sobre 59,4 M km² de trópicos 2017-2021. En Sudamérica los datos libres de nube son más
  probables en **octubre y noviembre**, más escasos **entre marzo y mayo**.

---

## 8. Qué prometer, en una línea

1. **No prometer cadencia fija con óptico.** Prometer *"mapa óptico en cuanto haya escena utilizable,
   best-effort"*. En Santa Cruz eso son realistamente **4–13 mapas ópticos por temporada de 5 meses**.
2. **La cadencia fija se promete con SAR**: 12 días, no 6.
3. **Declarar el hueco máximo en el contrato**: 66 días en Santa Cruz, 147 en Mato Grosso.
4. **Vender la estación seca aparte**: ahí la cadencia de 10 días sí es prometible.

---

*Método: catálogo Copernicus OData, productos `SENTINEL-2 MSIL2A` que intersectan un punto de campo,
tile MGRS dominante, una observación por fecha. Los porcentajes de fallo son cálculo propio sobre
datos oficiales medidos, no cifra publicada. Scripts de esta medición: temporales, no versionados —
los reproducibles del proyecto están en `medicion/`.*
