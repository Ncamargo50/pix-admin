# PIX Scout — Banco de Conocimiento (esquema de datos)

Banco de fichas **enfermedad / plaga / carencia por cultivo** que consume la APK offline
para asistir el diagnóstico diferencial a campo. Diseñado para conectar con:
- el **GeoJSON de focos** que emite la skill `deteccion-anomalias-cultivos-satelital`
  (cada foco trae un `patron_espacial` que la clave usa como primer filtro), y
- las skills de manejo (`biocontrol-plagas`, `biotech-microbianos`, `interpretacion-suelos`,
  `recomendacion-fertilizacion`) vía el campo `manejo_ref`.

## Principio de rigor (regla dura del proyecto)
- Nombres científicos y descripciones de síntoma = **hechos establecidos** → van cargados.
- **Umbrales de acción, dosis y citas** = NO se inventan. Van con valor `null` o
  `"VERIFICAR_LOCAL"` hasta curar con fuente verificable (ref: `feedback_umbrales_absolutos_no_transferibles`,
  `ref_estandar_optimo_trigo_no_existe`, "nunca inventar refs" del caso Canata 2024).
- **Fotos** = placeholders `PENDIENTE_CURAR/...` hasta cargar imágenes con derechos/propias de campo.

## Archivos
- `clave_dicotomica.json` — árbol de decisión que guía al técnico en el punto.
- `soya.json`, `trigo.json`, `maiz.json`, `sorgo.json`, `girasol.json`, `cana.json`, `pastura.json` — 7 cultivos de interés.

## Esquema de una ficha

```jsonc
{
  "id": "soya-roya-asiatica",           // slug único cultivo-nombre
  "cultivo": "soya",
  "categoria": "enfermedad",            // enfermedad | plaga | carencia
  "subtipo": "fungica_foliar",          // libre, para agrupar/filtrar
  "nombre_comun": "Roya asiática",
  "nombre_pt": "Ferrugem asiática",     // nombre en portugués (Brasil)
  "nombre_cientifico": "Phakopsora pachyrhizi",
  "severidad_potencial": "muy_alta",    // baja|media|alta|muy_alta (impacto potencial rinde)
  "organo": ["hoja"],                   // hoja|tallo|raiz|vaina|espiga|grano|planta_entera
  "estadio_cultivo": ["R1-R6"],         // ventana fenológica de mayor riesgo
  "signo": "…",                          // presencia FÍSICA del organismo (pústula, micelio, insecto, huevo)
  "sintoma": "…",                        // reacción de la planta (clorosis, necrosis, marchitez)
  "confirmacion_campo": "…",             // maniobra concreta para confirmar in-situ
  "confusiones": [                       // diagnóstico diferencial explícito
    { "con": "…", "como_diferenciar": "…" }
  ],
  "dd_tags": {                           // etiquetas que la clave dicotómica cruza (ver abajo)
    "patron_espacial": ["foco"],
    "signo_visible": true,
    "tipo_signo": "estructura_fungica",  // estructura_fungica|insecto|larva|huevo|ninguno
    "gradiente_hoja": "vieja_a_nueva",   // para carencias: vieja|nueva|generalizado|null
    "distribucion_planta": "ascendente"  // ascendente|descendente|localizado|null
  },
  "manejo_ref": "skill:biocontrol-plagas | skill:recomendacion-fertilizacion | …",
  "umbral_accion": "…",                  // umbral MIP con cifra citada, o "VERIFICAR_LOCAL" — NUNCA inventado
  "fuente_umbral": "Institucion + publicacion + URL",  // null si no hay umbral con fuente
  "fotos": [                             // objetos con licencia (para uso legal), o "PENDIENTE_CURAR/..."
    { "url": "https://commons.wikimedia.org/wiki/File:...", "muestra": "…", "licencia": "CC BY 3.0 US", "autor": "Autor, institucion, Bugwood.org" }
  ],
  "fuentes": ["URL fuente agronomica de la ficha"]
}
```

### Reglas de los campos curados (fotos + umbrales)
- **`fotos`**: sólo URLs de **licencia abierta verificada archivo por archivo** (Wikimedia Commons CC/CC0, USDA dominio público, Bugwood CC-BY). Cada objeto lleva `licencia` y `autor` para citar al mostrarla en la APK. Lo no verificado queda como string `"PENDIENTE_CURAR/..."`.
- **`umbral_accion` + `fuente_umbral`**: umbral MIP con **cifra y fuente citable** (Embrapa, INTA, AAPRESID, UGA…). Todos los umbrales publicados están calibrados en Brasil/Argentina/EEUU → llevan la coletilla `-> VERIFICAR_LOCAL` para no mostrarse como definitivos en Bolivia. Sin fuente → `"VERIFICAR_LOCAL"` y `fuente_umbral: null`.

## Cómo la clave usa `dd_tags`
La `clave_dicotomica.json` hace 3 preguntas al técnico (patrón espacial → signo → gradiente de hoja).
Cada respuesta filtra el set de fichas por sus `dd_tags`. El resultado es una lista corta de
**candidatos ordenados por coincidencia**, con las fotos al lado. La app **asiste, no diagnostica**:
el técnico confirma y el dato validado vuelve al satélite (ground-truth para calibrar el motor).

## Estado de curaduría (7 cultivos — 123 fichas)
| Cultivo | Fichas | enf / plaga / carencia | Fotos c/licencia | Umbrales c/fuente |
|---------|:------:|:----------------------:|:----------------:|:-----------------:|
| soya    | 21 | 8 / 6 / 7 | 0 (pendiente) | 3 (Embrapa MIP-Soja) |
| trigo   | 20 | 8 / 4 / 8 | 0 (pendiente) | 2 (Embrapa Trigo) |
| maiz    | 21 | 9 / 7 / 5 | 5 | 4 (Embrapa/Epagri/IRAC) |
| sorgo   | 16 | 7 / 5 / 4 | 5 | 5 (Embrapa/UGA) |
| girasol | 16 | 8 / 5 / 3 | 2 | 4 (AAPRESID/INTA) |
| cana    | 15 | 7 / 5 / 3 | 4 | 3 (Gebio/Coopercitrus) |
| pastura | 14 | 5 / 6 / 3 | 4 | 5 (Embrapa/SEMADESC/Frontiers) |
| **TOTAL** | **123** | | **20** | **26** |

Todas las fichas tienen síntoma/signo/confusiones completos (contenido agronómico sólido).
Cada cultivo lleva `stubs_por_curar` con las fichas pendientes nombradas.

### Umbrales MIP con cifra dura ya cargados
- **Soja** (Embrapa MIP-Soja): defoliadores 30% veg / 15% reprod, o 20 lagartas grandes >1,5cm/m; percevejos 2/paño (grano), 1/paño (semilla).
- **Trigo** (Embrapa): pulgones 10% plantas / 10 por afijo / 10 por espiga; barriga-verde Dichelops 4/m² veg, 2/m² reprod.
- **Maíz**: cogollero 20% plantas nota≥3 (Davis); barriga-verde 0,5/m² o 1 c/10 plantas.
- **Sorgo**: cogollero 20% nota≥3; midge 1 adulto/panícula en 20-30% floración; pulgón amarillo ~40-50/hoja (EEUU).
- **Girasol**: Rachiplusia nu 8-10 larvas/planta o 15% defoliación; cortadoras 3-5% plántulas cortadas.
- **Caña**: broca Diatraea III 1-2%; salivazo Mahanarva 3-5 ninfas/m.
- **Pastura**: salivazo/cigarrinha 6-25 ninfas/m² o 20-30 adultos/m² (Embrapa/Metarhizium).

Trabajo de curaduría restante: fotos con licencia para soja/trigo y para las especies marcadas "sin foto verificada"; umbrales `VERIFICAR_LOCAL` (calibración local Bolivia) para las plagas sin cifra publicada.
