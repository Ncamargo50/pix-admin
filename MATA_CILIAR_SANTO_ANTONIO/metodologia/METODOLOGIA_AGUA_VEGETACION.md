# Metodología verificada: cuerpos de agua, red de drenaje, nascentes y vegetación nativa para APP hídrica (Lei 12.651/2012)

**Propiedad:** 157,75 ha · centroide lat -23,4858 / lon -50,6586 · bbox de trabajo lon -50,70/-50,62, lat -23,52/-23,45
**Municipio (verificado por punto-en-polígono con la malla IBGE):** São Sebastião da Amoreira – PR (IBGE 4126009). El bbox también toca Santo Antônio do Paraíso (4124301) y Nova Fátima (4117008).
**Bioma:** Mata Atlântica, Floresta Estacional Semidecidual (submontana), norte de Paraná.
**Fecha de verificación de fuentes:** 2026-09-06. Todo lo marcado **[VERIFICADO]** fue comprobado en esta fecha por HTTP (Crossref API, catálogo GEE, `ee.getInfo()`, ArcGIS REST, WFS). Lo marcado **[NO VERIFICADO]** no pudo confirmarse y no debe citarse como hecho.

---

## 0. Resumen ejecutivo (lo que importa)

1. **La imagen Sentinel-2 a 10 m NO es la fuente del "curso d'água" legal.** Los cursos de 1-5 m bajo dosel no son resolubles a 10 m (ver §1). El leito regular se toma de la **hidrografía oficial** y se verifica en campo.
2. **La referencia oficial más fina que existe para el bbox es la base FBDS (RapidEye 5 m, año base 2013, escala nominal 1:25.000), publicada por el IAT-PR** en `geopr.iat.pr.gov.br` (ríos ≤10 m como línea, ríos >10 m como polígono, nascentes como punto, masas de agua y APP ya delimitadas). **Se descargó para el bbox** (231 tramos ≤10 m = 69,4 km; 38 nascentes; 33 masas de agua; 3 ríos >10 m). Complementan: red ottocodificada IAT 2020 (90 tramos, 73,9 km), ANA BHO 2017 5k (10 tramos, 31,5 km), IBGE BC250 2025 (16 tramos) y la hidrografía **declarada en el CAR** por los 54 inmuebles vecinos (WFS `geoserver.pr.gov.br`).
3. **Sentinel-2 sirve para lo que sí resuelve:** masas de agua abiertas ≥ 1-2 píxeles, vegetación arbórea vs no arbórea dentro del buffer, y refinamiento de bordes a 10 m del mapa MapBiomas (30 m). No sirve para el estágio sucessional (CONAMA 02/1994 exige DAP, altura, área basal, estratos: campo obligatorio).
4. **Nascentes:** se generan candidatos (cabeceras de red + HAND + FBDS) pero **cada nascente se confirma en campo**; la ley las define por perenidad, que ningún sensor óptico mide.
5. **Incertidumbre a comunicar:** ±1 píxel (10 m) en bordes S2; ±1 píxel DEM (30 m) en la posición del talweg derivado de DEM global; el buffer de 30 m tiene por lo tanto incertidumbre del orden de su propio ancho si se traza desde DEM. Con la base FBDS (5 m) la incertidumbre cae a ~5-15 m, pero sigue siendo diagnóstico preliminar: **el CAR es declaratorio (Art. 29) y el IAT analiza contra sus propias bases (IN IAT 05/2023, Art. 5 § único)**.

---

## 1. Límites físicos: qué ancho de curso de agua se detecta con S2 y qué puede hacer un DEM

### 1.1 Detección de agua con índices ópticos

| Referencia [VERIFICADO Crossref] | Qué aporta a este trabajo |
|---|---|
| McFeeters, S.K. (1996). *Int. J. Remote Sensing* 17(7). DOI 10.1080/01431169608948714 | Define NDWI = (Green − NIR)/(Green + NIR). Con S2: (B3 − B8)/(B3 + B8), ambas a 10 m nativos. Confunde agua con sombra y con suelo/edificación oscura. |
| Xu, H. (2006). *Int. J. Remote Sensing* 27(14). DOI 10.1080/01431160600589179 | MNDWI = (Green − SWIR1)/(Green + SWIR1) reduce la confusión con edificaciones. Con S2 exige B11 (20 m): el mapa resultante es a 20 m salvo que se afile (Du et al. 2016). |
| Feyisa, G.L. et al. (2014). *Remote Sens. Environ.* 140. DOI 10.1016/j.rse.2013.08.029 | AWEI_nsh y AWEI_sh: combinaciones lineales de B, G, NIR, SWIR1, SWIR2 pensadas para separar agua de sombra y superficies oscuras. Requiere SWIR (20 m en S2). |
| Pekel, J.-F. et al. (2016). *Nature* 540. DOI 10.1038/nature20584 | Global Surface Water (Landsat 30 m, 1984-hoy): sirve como **prior de ocurrencia/estacionalidad** de agua abierta, no para cursos de 1-5 m. |
| Du, Y. et al. (2016). *Remote Sensing* 8(4). DOI 10.3390/rs8040354 | Afilado de MNDWI a 10 m en S2 (pan-sharpening de B11 con bandas de 10 m). Es la forma correcta de obtener MNDWI a 10 m. |
| Yang, X. et al. (2017). *Remote Sensing* 9(6). DOI 10.3390/rs9060596 | Mapa de cuerpos de agua urbanos a 10 m vía afilado basado en NDWI. Mismo principio, entorno urbano. |
| Radoux, J. et al. (2016). *Remote Sensing* 8(6). DOI 10.3390/rs8060488 | **Límite sub-píxel de S2**: detecta objetos lineales de agua desde ~5 m de ancho *solo* cuando están centrados en el píxel y sobre fondo homogéneo (pastizal). Bajo dosel o con fondo mixto, no. |
| Lu, D., Yang, X. et al. (2020). *J. Hydrology* 584. DOI 10.1016/j.jhydrol.2020.124689 | Mapeo automatizado de ríos árticos "tan estrechos como 10 m" con NDWI + filtros morfológicos + DEM: el ancho mínimo operativo confiable es **~1 píxel (10 m)** y con apoyo del DEM. |
| Kirby, Ferguson, Rennie (2024). *Remote Sens. Appl.: Soc. Environ.* DOI 10.1016/j.rsase.2024.101367 | Comparación de métodos en S2: todos producen polígonos de agua **discontinuos donde el ancho < ~40 m**; NDWI es el que mejor rescata tramos estrechos. |
| Liang et al. (2022). *Remote Sensing* 14(19). DOI 10.3390/rs14194693 | ASRM: ríos pequeños con S2 + MERIT DEM; confirma que sin DEM la red se fragmenta. |
| Li et al. (2020, 2021). *Remote Sensing* 12(17) y 13(14). DOI 10.3390/rs12172737 y 10.3390/rs13142650 | Extracción de ríos con S2 + DEM en condiciones de "bankfull" (leito regular análogo). |
| Cavallo, Papa et al. (2022). *Sci. Reports* 12. DOI 10.1038/s41598-022-26034-z | Uso de la serie S2 para **intermitencia de flujo** en ríos no perennes: sólo funciona en cauces anchos y abiertos. |
| Allen & Pavelsky (2018). *Science* 361. DOI 10.1126/science.aat0636 | GRWL: la cartografía global de ancho de ríos desde Landsat se limita a ríos ≥ 30 m. Contexto: los cursos del bbox (1-5 m) están un orden de magnitud por debajo. |

**Conclusión física (§1.1):** con S2 L2A el ancho mínimo *operativo* de un curso de agua es ~10 m (1 píxel) a cielo abierto; en condiciones ideales (centrado, fondo homogéneo) puede llegar a ~5 m como señal sub-píxel, pero **bajo mata ciliar el cauce es invisible al sensor óptico**: se ve dosel, no agua. Por tanto, para cursos de 1-5 m la imagen sólo aporta (a) la posición de la franja arbórea ciliar, (b) masas de agua abiertas (represas, lagos) ≥ 2 píxeles y (c) humedad superficial (NDMI, B8-B11) como indicio de zona ripária.

### 1.2 Red de drenaje por DEM

| Referencia [VERIFICADO Crossref] | Qué aporta |
|---|---|
| O'Callaghan & Mark (1984). *Computer Vision, Graphics, and Image Processing* 28. DOI 10.1016/S0734-189X(84)80011-0 | Algoritmo D8 y extracción de red por umbral de acumulación de flujo. Base de todo lo demás. |
| Tarboton (1997). *Water Resour. Res.* 33(2). DOI 10.1029/96WR03137 | D-infinity: direcciones continuas; mejor en laderas suaves y divergentes que D8. |
| Rennó et al. (2008). *Remote Sens. Environ.* 112. DOI 10.1016/j.rse.2008.03.018 | **HAND** (altura sobre el drenaje más cercano) con SRTM: normaliza el terreno respecto a la red; separa fondo de valle de terra firme. |
| Nobre et al. (2011). *J. Hydrology* 404. DOI 10.1016/j.jhydrol.2011.03.051 | HAND como modelo de terreno hidrológicamente relevante; umbrales de HAND para zonas ripárias/saturables. |
| Wang & Yin (1998). *J. Hydrology* 210. DOI 10.1016/S0022-1694(98)00189-9 | La red derivada de DEM depende fuertemente de la escala/resolución del DEM; redes a dos escalas difieren en cabeceras. |
| Bortolini, Taborda da Silveira, Siame (2025). *RAEGA* 62(1). DOI 10.5380/raega.v62i1.98168 | Comparación **en Brasil** de redes extraídas de DEMs globales con flujo simple (D8) y múltiple: las discrepancias se concentran en cabeceras y terreno suave (justo el caso de este bbox). |
| Yamazaki et al. (2017, 2019). *GRL* 44 y *WRR* 55. DOI 10.1002/2017GL072874 y 10.1029/2019WR024873 | MERIT DEM y MERIT Hydro (90 m): red, acumulación y HAND globales ya calculados; útiles como control de coherencia, no para trazar el leito a escala de propiedad. |
| Lehner, Verdin, Jarvis (2008). *Eos* 89(10). DOI 10.1029/2008EO100001 · Grill et al. (2019). *Nature* 569. DOI 10.1038/s41586-019-1111-9 | HydroSHEDS (90 m) y Free-Flowing Rivers: contexto de cuenca, inútiles a escala de 157 ha. |

### 1.3 Precisión de los DEM globales de 30 m para drenaje en terreno suave

| Referencia [VERIFICADO Crossref] | Hallazgo relevante |
|---|---|
| Guth & Geoffroy (2021). *Transactions in GIS* 25(5). DOI 10.1111/tgis.12825 | Evaluación con LiDAR e ICESat-2 de DEMs de 1 arc-s: **Copernicus GLO-30 es el más preciso**, seguido de ALOS AW3D30; SRTM y NASADEM detrás. |
| Bielski, López-Vázquez, Grohmann et al. (2024). *IEEE TGRS* 62. DOI 10.1109/TGRS.2024.3368015 | Ranking multi-criterio (DEMIX): Copernicus DEM mejora la topografía abierta de 1 arc-s; confirma GLO-30 como primera opción. |
| Uuemaa et al. (2020). *Remote Sensing* 12(21). DOI 10.3390/rs12213482 | Precisión vertical de ASTER, AW3D30, MERIT, TanDEM-X, SRTM, NASADEM: los errores crecen con pendiente y con **cobertura forestal** (todos son DSM). |
| Hawker et al. (2022). *Environ. Res. Lett.* 17. DOI 10.1088/1748-9326/ac4d4f | **FABDEM**: GLO-30 con bosques y edificios removidos por ML; en zonas con mata ciliar reduce el sesgo de dosel que "levanta" el fondo de valle. **Licencia CC BY-NC-SA 4.0: no comercial** (ver §3). |

**Conclusión (§1.2-1.3):** en relieve suave del norte de Paraná, un DEM de 30 m posiciona el talweg con error del orden de **1 píxel (≈30 m)**, con errores mayores en cabeceras (donde se definen las nascentes) y donde el dosel ciliar infla el DSM. El DEM sirve para: (a) proponer *dónde debería* haber un curso (candidatos), (b) HAND para acotar la zona ripária, (c) verificar la coherencia topológica de la hidrografía oficial. **No sirve para fijar la borda del leito regular.**

---

## 2. Fuentes oficiales de hidrografía en Brasil / Paraná (con verificación de URLs)

Marco legal: Lei 12.651/2012 Art. 3º XIX define **leito regular** como "a calha por onde correm regularmente as águas do curso d'água durante o ano"; Art. 4º I fija la APP "desde a borda da calha do leito regular" con mínimo de **30 m para cursos de menos de 10 m de largura** (perennes e intermitentes, excluidos los efímeros); Art. 4º IV, **radio mínimo de 50 m** alrededor de nascentes y olhos d'água **perenes**; Art. 3º XVII nascente = "afloramento natural do lençol freático que apresenta perenidade e dá início a um curso d'água" [VERIFICADO: texto obtenido de planalto.gov.br el 2026-09-06].

### 2.1 Tabla de fuentes

| Fuente | Escala / origen | Formato y acceso | ¿Cubre el bbox? | Estado 2026-09-06 |
|---|---|---|---|---|
| **FBDS – Mapeamento APP hídricas (via IAT-PR)** | RapidEye 5 m, año base 2013; escala nominal 1:25.000; ríos medidos en tramos de 100 m con ancho por intervalos de 10 m (según descripción del servicio IAT). Capas: `fbds_rio_ate10m_larg` (línea), `Cursos_D_água_Largura_acima_de_10_metros_FBDS` (polígono), `fbds_nascentes` (punto), `fbds_massas_dagua`, `fbds_app`, `fbds_app_uso`, `fbds_uso_cobertura_2013` | ArcGIS REST FeatureServer: `https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/<capa>/FeatureServer/0/query` (GeoJSON, filtro por envelope). Descarga completa .gdb: `https://geopr.iat.pr.gov.br/webgis/download/<capa>.gdb.rar` | **Sí** | **[VERIFICADO] Responde; descargado.** Sitio original `geo.fbds.org.br` **[NO RESPONDE: DNS no resuelve]** |
| **IAT – Rede Hidrográfica Ottocodificada 2020** (`rede_otto_trech_drena_2020_iat`, `rede_otto_areas_drena_2020_iat`) | Derivada de la base 1:50.000 estatal (COPEL/ÁguasParaná 2011) con metodología ANA 2010; "corrigidos uma série de pequenos erros" y toponimia. Campos ANA (cotrecho, cobacia, nustrahler, nuareamont…). | Mismo REST del IAT; .gdb: `https://geopr.iat.pr.gov.br/webgis/download/rede_otto_trech_drena_2020_iat.gdb.rar` | Sí | **[VERIFICADO] Responde; descargado** (áreas de drenaje dieron timeout 503 en el conteo pero la consulta GeoJSON funcionó). |
| **IAT – Massas d'água 1:50.000 PARANACIDADE/COPEL 2000** (`hidro_50k_massa_dagua_prcidade`) | 1:50.000, con campo `regime` (Permanente/Temporário) | Mismo REST | Sí | **[VERIFICADO] Responde; descargado.** |
| **IAT – ZEE-PR Cursos d'água detalhados** (`zee_rios`) | 2011, campos `tipo`, `rio`, `ordem` | Mismo REST | Sí | **[VERIFICADO] Responde; descargado.** |
| **IAT – Hidrografia 1:10.000 por radar** (`bc_hid_trecho_drenagem_l_10k`) | 1:10.000, SEMA 2016 | Mismo REST | **No** (sólo litoral paranaense; 0 features en el bbox) | [VERIFICADO] Responde, sin cobertura aquí. |
| **Hidrografía declarada en el CAR (WFS estatal)** capa `car:hidrografia_pol_p4674` | Lo que cada propietario declaró en SICAR (temas `RIO_ATE_10`, `RIO_10_A_50`, `LAGO_NATURAL`, `RESERVATORIO_ARTIFICIAL…`), con `cod_imovel` y `des_condic` | WFS GeoServer: `https://geoserver.pr.gov.br/geoserver/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=car:hidrografia_pol_p4674&bbox=…&outputFormat=application/json` (cadena TLS ICP-Brasil no incluida en `certifi`: usar `verify=<bundle con la CA ICP-Brasil>`, no desactivar la verificación) | Sí | **[VERIFICADO] Responde; descargado** (73 polígonos de 54 inmuebles). No es "oficial" como referencia: es lo declarado. |
| **ANA – BHO 2017 5k** (trechos con área ≥ 5 km² + trechos federales) | Derivada del Mapeamento Sistemático (cartas 1:50.000/1:100.000/1:250.000 según región) | ArcGIS REST: `https://www.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_TRECHODRENAGEM/FeatureServer/0/query` y `…/BHO2017_5K_AREADRENAGEM/…`. Metadatos: `https://metadados.snirh.gov.br/geonetwork/srv/api/records/0c698205-6b59-48dc-8b5e-a58a5dfcc989`; portal `https://dadosabertos.ana.gov.br/datasets/5b97dc790ebc4307938d8a5b089c1aab_0/about` | Sí | **[VERIFICADO] Responde; descargado** (10 trechos). `portal1.snirh.gov.br/ana/rest` devuelve HTTP 500; `geoservicos.ana.gov.br` no resuelve DNS. |
| **ANA – BHO 2017 50k** | Igual, umbral 50 km² | `…/SPR/BHO2017_50K_TRECHODRENAGEM/FeatureServer/0` y `…_AREADRENAGEM` | Sí | **[VERIFICADO] Responde; descargado** (2 trechos). |
| **IBGE – BC250 versión 2025** | 1:250.000 (nacional); campos `regime`, `larguramedia`, `tipotrechodrenagem` | WFS: `https://geoservicos.ibge.gov.br/geoserver/wfs` capa `CCAR:BC250_2025_hid_trecho_drenagem_l` (y `…hid_massa_dagua_a`). Descarga completa: `https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc250/versao2025/geopackage/bc250_gpkg_2026-03-03.zip` (864 MB) | Sí | **[VERIFICADO] Responde; descargado** (16 trechos, todos `Permanente`). |
| **IBGE – BC25 (1:25.000)** | Sólo estados con cobertura | `https://geoftp.ibge.gov.br/cartas_e_mapas/bases_cartograficas_continuas/bc25/` | **No** (sólo `rj/` y `sc/`) | [VERIFICADO] Responde; Paraná no existe. |
| **IBGE – BC100** | 1:100.000 por estado | WFS IBGE capas `CCAR:BC100_<UF>_…` | No hay capa `_PR_` en el GetCapabilities | [VERIFICADO] Sin Paraná. |
| **DSG/Exército – BDGEx (cartas 1:50.000 vetoriais)** | 1:50.000 | WMS raster `https://bdgex.eb.mil.br/mapcache?service=WMS` (capas `ctm50`, `Multiescala_Hidrografia`, `curva_nivel50`); índice `http://bdgex.eb.mil.br/cgi-bin/mapaindice` (capas `F50_WGS84_VETORIAL`). Vectores sólo con login en `https://bdgex.eb.mil.br/bdgexapp` | Sí (cobertura por hoja, verificar `F50_WGS84_VETORIAL`) | WMS **[VERIFICADO] responde**; WFS `ms_ogc/wfs_geo` **[NO RESPONDE]** (error "Unable to access file multiscale.map"). Descarga vectorial: **[NO VERIFICADO]** (requiere cuenta). |
| **MapBiomas Água (Coleção 4)** | Landsat 30 m, 1985-2024, superficie de agua mensual/anual | GEE `projects/mapbiomas-public/assets/brazil/water/collection4/mapbiomas_brazil_collection4_water_v3` | Sí | **[VERIFICADO con ee.getInfo]**. Sólo agua abierta ≥ 30 m: represas y lagos, no cursos de 1-5 m. |
| **SICAR – descarga pública de shapefiles por estado** | Declarado | `https://consultapublica.car.gov.br/publico/imoveis/index` | Sí | **[NO VERIFICADO]** en esta sesión (el WFS estatal ya entregó lo mismo para el bbox). |

### 2.2 ¿Qué base usa el IAT-PR para analizar el CAR?

- **IN IAT nº 05/2023** (Art. 5): la análisis se hace en el **Módulo de Análise del SICAR** (Serviço Florestal Brasileiro); "§ único: O IAT poderá efetuar a inserção de bases cartográficas no Módulo de Análise visando subsidiar a análise e validação dos cadastros". Art. 9 remite a los *roteiros* de análisis (≤ 4 MF y > 4 MF) y a la Orientação Técnica IAT 03/2023. Art. 10: la finalidad es "conferir as informações declaradas, apurando se correspondem à realidade existente no imóvel". Art. 15 § 1º: tolerancia de 5 % entre área declarada y vectorizada. **[VERIFICADO: PDF oficial leído].** La IN **no nombra** una base hidrográfica específica.
- Lo que sí está verificado es que el IAT **publica como capa institucional** la hidrografía y las nascentes FBDS, con la leyenda "Mapeamento de Áreas de Preservação Permanentes Hídricas, conforme previsto nos Artigos 4º e 5º da Lei 12.651/2012", y el programa CAR-Paraná (Fundo Amazônia) declara haber compatibilizado 15 bases temáticas y creado bases nuevas "para melhorar a identificação de drenagens e nascentes nos imóveis". Que la FBDS sea *la* base cargada en el Módulo de Análise es **probable pero [NO VERIFICADO]**: confirmarlo con el escritório regional del IAT (Cornélio Procópio) antes de presentar el laudo.
- El módulo de cadastro del SICAR usa imágenes RapidEye (~5 m, 2011-2013) como fondo de referencia para el dibujo del propietario [fuente: manual del Módulo de Cadastro SFB alojado en iat.pr.gov.br; contenido de detalle NO VERIFICADO línea a línea].

### 2.3 Consulta programática (Python)

```python
import requests, geopandas as gpd
BBOX = "-50.70,-23.52,-50.62,-23.45"          # xmin,ymin,xmax,ymax (EPSG:4326)
# Los hosts *.pr.gov.br usan cadena ICP-Brasil, ausente en certifi. NO desactivar TLS:
# descargar la cadena (https://www.gov.br/iti/pt-br/assuntos/repositorio) y concatenarla
# al bundle de certifi en un archivo propio, p.ej. C:/certs/certifi_icpbrasil.pem
CA = "C:/certs/certifi_icpbrasil.pem"

# (a) IAT / FBDS – ArcGIS REST FeatureServer
def iat(layer, out):
    u = f"https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/{layer}/FeatureServer/0/query"
    p = dict(geometry=BBOX, geometryType="esriGeometryEnvelope", inSR=4326,
             spatialRel="esriSpatialRelIntersects", outFields="*", outSR=4326, f="geojson")
    r = requests.get(u, params=p, timeout=180, verify=CA); r.raise_for_status()
    open(out, "w", encoding="utf-8").write(r.text); return gpd.read_file(out)
rios   = iat("fbds_rio_ate10m_larg", "IAT_FBDS_rios_ate10m.geojson")
nasc   = iat("fbds_nascentes",       "IAT_FBDS_nascentes.geojson")
otto   = iat("rede_otto_trech_drena_2020_iat", "IAT_otto_trecho_drenagem_2020.geojson")

# (b) ANA BHO 2017 5k – mismo protocolo, otro host
u = "https://www.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_TRECHODRENAGEM/FeatureServer/0/query"
bho = gpd.read_file(requests.get(u, params=p, timeout=180).text)

# (c) IBGE BC250 2025 – WFS
u = "https://geoservicos.ibge.gov.br/geoserver/wfs"
p = dict(service="WFS", version="1.0.0", request="GetFeature",
         typeName="CCAR:BC250_2025_hid_trecho_drenagem_l", bbox=BBOX,
         outputFormat="application/json", srsName="EPSG:4326")
bc250 = gpd.read_file(requests.get(u, params=p, timeout=240).text)

# (d) CAR declarado (vecinos) – WFS estatal
u = "https://geoserver.pr.gov.br/geoserver/ows"
p.update(typeName="car:hidrografia_pol_p4674")
car = gpd.read_file(requests.get(u, params=p, timeout=180, verify=CA).text)
```

---

## 3. Datasets en Google Earth Engine (IDs verificados)

Verificación: **[EE]** = `ee.Image/ImageCollection(id).getInfo()` ejecutado con éxito el 2026-09-06 desde la cuenta local; **[CAT]** = página del catálogo responde HTTP 200 con el título esperado.

| Dataset | ID exacto | Tipo | Resolución | Vigencia / versión | Bandas relevantes | Verif. |
|---|---|---|---|---|---|---|
| Sentinel-2 L2A armonizado | `COPERNICUS/S2_SR_HARMONIZED` | ImageCollection | 10/20/60 m | 2017-03-28 → hoy | B2,B3,B4,B8 (10 m); B5,B6,B7,B8A,B11,B12 (20 m); SCL | [EE][CAT] |
| Cloud Score+ | `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` | ImageCollection | 10 m | 2015-06-27 → hoy | `cs`, `cs_cdf` (usar `cs_cdf ≥ 0,6-0,7`) | [EE][CAT] |
| Sentinel-1 GRD | `COPERNICUS/S1_GRD` | ImageCollection | 10 m | 2014-10 → hoy | VV, VH (agua abierta = retrodispersión baja) | [CAT] |
| Copernicus DEM GLO-30 (vigente) | `COPERNICUS/DEM/GLO30_2024_1` | ImageCollection (mosaicar) | 30 m | Edición 2024_1; adquisiciones 2010-2020 | `DEM` (DSM), `WBM`, `HEM`, `EDM`, `FLM` | [EE][CAT] |
| Copernicus DEM GLO-30 (antiguo) | `COPERNICUS/DEM/GLO30` | — | 30 m | **[deprecated]** en catálogo | — | [CAT] |
| FABDEM v1-2 | `projects/sat-io/open-datasets/FABDEM` | ImageCollection (mosaicar) | 30 m | Community catalog (sat-io) | `b1` | [EE] — **licencia CC BY-NC-SA 4.0: no usar en entregable comercial sin licencia Fathom** |
| NASADEM | `NASA/NASADEM_HGT/001` | Image | 30 m | 2000 (SRTM reprocesado) | `elevation`, `swb` | [EE][CAT] |
| SRTM 1 arc-s | `USGS/SRTMGL1_003` | Image | 30 m | 2000 | `elevation` | [CAT] |
| ALOS AW3D30 (vigente) | `JAXA/ALOS/AW3D30/V4_1` | ImageCollection | 30 m | v4.1 (abr-2024) | `DSM`, `MSK`, `STK` | [EE][CAT] |
| ALOS AW3D30 (antiguo) | `JAXA/ALOS/AW3D30/V3_2` | — | 30 m | **[deprecated]** | — | [CAT] |
| MERIT DEM | `MERIT/DEM/v1_0_3` | Image | 90 m | v1.0.3 | `dem` | [CAT] |
| MERIT Hydro | `MERIT/Hydro/v1_0_1` | Image | 90 m | v1.0.1 | `elv`, `dir`, `upa` (área aguas arriba), `upg`, `hnd` (HAND), `wth`, `wat` | [EE][CAT] |
| JRC Global Surface Water | `JRC/GSW1_4/GlobalSurfaceWater` | Image | 30 m | v1.4 (1984-2021) | `occurrence`, `seasonality`, `max_extent`, `transition` | [EE][CAT] |
| JRC Monthly History | `JRC/GSW1_4/MonthlyHistory` | ImageCollection | 30 m | v1.4 | `water` | [CAT] |
| HydroSHEDS | `WWF/HydroSHEDS/03CONDEM`, `WWF/HydroSHEDS/03DIR` | Image | 90 m | v1 | `b1` | [CAT] |
| HydroSHEDS Free-Flowing Rivers | `WWF/HydroSHEDS/v1/FreeFlowingRivers` | FeatureCollection | vector | v1 | `RIV_ORD`, `BB_LEN_KM`… | [EE][CAT] |
| HydroATLAS nivel 12 | `WWF/HydroATLAS/v1/Basins_level12` | FeatureCollection | vector | v1 | atributos de cuenca | [CAT] |
| MapBiomas Brasil (catálogo oficial GEE) | `projects/mapbiomas-public/assets/brazil/lulc/v1` | ImageCollection (1 imagen/año) | 30 m | 1985-2024; filtrar `collection_id == 10` | `classification` | [EE][CAT] |
| MapBiomas Coleção 10 (asset directo) | `projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_coverage_v2` | Image multibanda | 30 m | 1985-**2024** | `classification_1985 … classification_2024` | [EE] (`…coverage_v1` **no existe**) |
| MapBiomas Coleção 9 | `projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1` | Image multibanda | 30 m | 1985-2023 | `classification_1985 … classification_2023` | [EE] |
| MapBiomas Água Coleção 4 | `projects/mapbiomas-public/assets/brazil/water/collection4/mapbiomas_brazil_collection4_water_v3` | Image multibanda | 30 m | 1985-2024 | `classification_<año>` | [EE] |
| MapBiomas Água Coleção 3 | `projects/mapbiomas-public/assets/brazil/water/collection3/mapbiomas_water_annual_water_coverage_v1` | Image multibanda | 30 m | 1985-2023 | `annual_water_coverage_<año>` | [EE] |
| Global Forest Change (vigente) | `UMD/hansen/global_forest_change_2025_v1_13` | Image | 30 m | 2000-2025, v1.13 | `treecover2000`, `loss`, `lossyear`, `gain`, `datamask` | [EE][CAT] |
| Global Forest Change (antiguo) | `UMD/hansen/global_forest_change_2024_v1_12` | — | — | **[deprecated]** | — | [CAT] |
| ESA WorldCover | `ESA/WorldCover/v200` | ImageCollection | 10 m | 2021 (v200) | `Map` (10 árbol, 20 arbusto, 30 pasto, 40 cultivo, 50 urbano, 80 agua, 90 humedal…) | [EE][CAT] |
| Dynamic World | `GOOGLE/DYNAMICWORLD/V1` | ImageCollection | 10 m | 2015-06 → hoy | `label`, `trees`, `water`, `crops`, `grass`… | [EE][CAT] |

**Leyenda MapBiomas Coleção 10 (del catálogo GEE, verificada):** 1 Floresta · **3 Formação Florestal** · 4 Formação Savânica · 5 Mangue · 6 Floresta Alagável · **9 Silvicultura** · 10 Veg. Herbácea/Arbustiva · 11 Campo Alagado/Área Pantanosa · 12 Formação Campestre · 14 Agropecuária · **15 Pastagem** · 18 Agricultura · 19 Lavoura Temporária · 20 Cana · **21 Mosaico de Usos** · 22 Área não vegetada · 23 Praia/Duna · **24 Área Urbanizada** · 25 Outras áreas não vegetadas · 26 Água · 29 Afloramento Rochoso · 30 Mineração · 31 Aquicultura · 32 Apicum · **33 Rio/Lago/Oceano** · 35 Dendê · 36 Lavoura Perene · **39 Soja** · 40 Arroz · **41 Outras Lavouras Temporárias** · 46 Café · 47 Citrus · 48 Outras Perenes · 49/50 Restinga · 62 Algodão (beta) · 75 Usina fotovoltaica (beta).

Referencias GEE [VERIFICADO Crossref]: Gorelick et al. (2017) *RSE* 202, DOI 10.1016/j.rse.2017.06.031 · Hansen et al. (2013) *Science* 342, DOI 10.1126/science.1244693 · Brown et al. (2022) *Sci. Data* 9, DOI 10.1038/s41597-022-01307-4 · Zanaga et al. (2022) WorldCover v200, DOI 10.5281/zenodo.7254221 (DataCite; resuelve en doi.org) · Souza et al. (2020) *Remote Sensing* 12(17), DOI 10.3390/rs12172735 · Mullissa et al. (2021) *Remote Sensing* 13(10), DOI 10.3390/rs13101954 (preprocesado S1 en GEE).

---

## 4. Metodología recomendada para vegetación nativa a 10 m

### 4.1 Arquitectura (a)+(b)+(c)

**(a) Referencia temática: MapBiomas Coleção 10, año 2024, 30 m.** Souza et al. (2020) documentan el método (Random Forest por bioma sobre Landsat, filtros temporales). Es la referencia que los órganos ambientales reconocen como "mapa de contexto", pero su borde tiene 30 m de píxel y un filtro temporal que **suaviza cambios recientes**: nunca usarlo como borde del fragmento.

**(b) Clasificación supervisada en GEE (Random Forest) de S2 a 10 m, con MapBiomas como semilla de etiquetas.**
1. Compuesto S2 L2A: mediana estacional **seca** (jun-ago) y **húmeda** (dic-feb), `cs_cdf ≥ 0,65`, SCL ∉ {3,8,9,10,11}, dilatación de la máscara de nube 2 píxeles (memoria: `unmask` infla cobertura; usar `unmask(0, False)` sólo para conteo, nunca para clasificar).
2. Predictores: B2-B4, B8 (10 m); B5, B6, B7, B8A, B11, B12 remuestreadas a 10 m (bilinear); NDVI, NDMI = (B8−B11)/(B8+B11), NDRE = (B8A−B5)/(B8A+B5), MNDWI afilado; **texturas GLCM** (Haralick et al. 1973, DOI 10.1109/TSMC.1973.4309314) sobre NIR: contraste, entropía, homogeneidad, ventana 5×5 (50 m) — `ee.Image.glcmTexture`; diferencia seca-húmeda de NDVI (la mata semidecidual pierde hoja parcialmente; el eucalipto no; la soja/maíz oscila al máximo).
3. Etiquetas: muestrear MapBiomas 2024 **sólo en píxeles "núcleo"** (a > 45 m del borde de su propia clase, es decir, erosionar cada clase 1,5 píxeles de 30 m) para no enseñar mezclas. Clases: 3 Formação Florestal, 9 Silvicultura, 15 Pastagem, 39/41 Lavoura, 33/26 Agua, 24/22 Suelo/edificado. Mínimo 200 puntos por clase, estratificados, sobre un radio de 10-15 km (misma fisonomía).
4. RF (Breiman 2001, DOI 10.1023/A:1010933404324; revisión: Belgiu & Drăguţ 2016, DOI 10.1016/j.isprsjprs.2016.01.011): 300 árboles, `variablesPerSplit` = √p, validación por bloques espaciales (no aleatoria) y matriz de confusión reportada.
5. Post-clasificación: filtro de moda 3×3, eliminación de parches < 4 píxeles (0,04 ha) salvo dentro del buffer, y **vectorización a 10 m**.

**(c) Discriminación bosque nativo / silvicultura / cultivo / pastura.**
- Nativo vs eucalipto: el eucalipto tiene NDVI alto y **muy homogéneo** (baja entropía GLCM), copas en hileras a veces visibles a 10 m, NDRE estable entre estaciones y **fecha de corte** detectable en la serie temporal (Hansen `lossyear`, Zhou et al. 2024 *Forests* 15(11), DOI 10.3390/f15111866 con CCDC+RF; Xiao et al. 2024 *J. Remote Sensing*, DOI 10.34133/remotesensing.0204, mapa global natural/plantado a 30 m). La textura y la historia son las variables que separan; la reflectancia instantánea sola **no** (correlación entre índices 0,97-0,998 en variabilidad espacial — memoria del proyecto).
- Nativo vs pastura arbolada / mosaico: altura. Perez, Bourscheidt & Lopes (2022) *Ecological Informatics* 70, DOI 10.1016/j.ecoinf.2022.101680 estiman altura de vegetación en fragmentos de Mata Atlântica con S2, con error suficiente para separar arbóreo (> 5 m) de herbáceo, no para clases finas.
- Cultivo vs pastura: amplitud temporal NDVI (cultivo anual: ciclo con suelo desnudo; pastura: NDVI medio sin caída a suelo).

### 4.2 Estágio sucessional: qué se puede y qué NO se puede afirmar desde satélite

**CONAMA nº 2/1994** (Paraná; DOU 28-mar-1994) define, para Floresta Estacional Semidecidual, los estágios con muestreo de "indivíduos arbóreos com DAP igual ou maior que 20 cm" [VERIFICADO: texto leído]:
- **Inicial:** fisionomía herbáceo-arbustiva, 1 estrato, 1-10 especies leñosas, dosel hasta 10 m, **área basal 8-20 m²/ha**, distribución diamétrica 5-15 cm, DAP medio 10 cm; indicadoras: bracatinga, vassourão, aroeira, embaúba, taquara.
- **Médio:** arbustivo/arbóreo, 1-2 estratos, 5-30 especies, dosel **8-17 m**, **área basal 15-35 m²/ha**, distribución 10-40 cm, DAP medio 25 cm; indicadoras: congonha, canela-guaicá, palmito, guapuruvu, cedro.
- **Avançado:** arbóreo dominante, dosel cerrado y uniforme, **> 2 estratos**, especies predominantemente esciófilas, epífitas abundantes, etc.

**Lo que S2 puede afirmar:** existencia de cobertura arbórea continua vs discontinua; **edad mínima** del fragmento vía serie Landsat/MapBiomas (si el píxel es "Formação Florestal" desde 1985, tiene ≥ 40 años: consistente con médio/avançado, no prueba); pérdida reciente (Hansen `lossyear`); homogeneidad de dosel (textura) como indicio de plantación.
**Lo que S2 NO puede afirmar:** DAP, área basal, número de estratos, composición de especies, epífitas. Rosa et al. (2021) *Science Advances* 7(4), DOI 10.1126/sciadv.abc4547, muestran además que gran parte de la "ganancia" de bosque en Mata Atlântica es regeneración joven que se vuelve a perder: la edad satelital sobreestima madurez. Sothe et al. (2017) *Remote Sensing* 9(8), DOI 10.3390/rs9080838, obtuvieron con S2 + RF/SVM separación **parcial** de estágios en Floresta Ombrófila (SC) usando dos estaciones y texturas — nivel "indicio", no laudo. **Por tanto: el estágio sucessional se informa como "indicio satelital, a confirmar por inventario florístico/estructural en campo (CONAMA 02/1994)".**

---

## 5. Nascentes: localización de candidatos y por qué la validación de campo es obligatoria

**Definición legal (Art. 3º XVII):** afloramiento natural del freático **con perenidad** que da inicio a un curso de agua; olho d'água (XVIII) = afloramiento "mesmo que intermitente". La APP de 50 m (Art. 4º IV) aplica a nascentes y olhos d'água **perenes**. La perenidad es una propiedad **temporal e hidrogeológica**: ningún sensor óptico la mide; la serie S2 tampoco ve un afloramiento de 1-2 m bajo dosel.

**Cadena de candidatos (ranking, no detección):**
1. **Base FBDS `fbds_nascentes`** (38 puntos en el bbox: 21 en Santo Antônio do Paraíso, 17 en São Sebastião da Amoreira): nascente = "representação pontual aproximada das cabeceiras dos cursos d'água" digitalizada sobre RapidEye 5 m, 2013. Es el **candidato oficial de partida** (el IAT la publica con la leyenda de la Lei 12.651). Precisión posicional esperada: 5-25 m (escala 1:25.000 → 0,2 mm × 25.000 = 5 m de trazo; en la práctica 1-3 píxeles RapidEye).
2. **Cabeceras de la red ottocodificada IAT 2020** (48 tramos Strahler 1 en el bbox): extremo aguas arriba de cada tramo de orden 1 = nascente cartográfica 1:50.000; peor posición (± 25-50 m) pero con topología y `nuareamont`.
3. **Cabeceras por DEM**: acumulación de flujo (D8/D-inf sobre GLO-30 o FABDEM, relleno de depresiones) con umbral de área de contribución calibrado **contra las nascentes FBDS** (ajustar el umbral hasta que la longitud total de red DEM ≈ longitud FBDS en la cuenca; típicamente 2-10 ha en este relieve — cifra a calibrar, no a copiar). Punto de inicio de cada cauce = candidato.
4. **HAND** (Rennó 2008; Nobre 2011): candidatos con HAND ≤ 3-5 m y pendiente local baja son coherentes con afloramiento freático; HAND alto en ladera = probable error del DEM (dosel).
5. **Humedad S2**: NDMI y MNDWI en compuesto de **estación seca** (jul-sep). Un candidato cuyo entorno de 50 m mantiene NDMI alto en seca frente al vecindario (z-score local, MAD por fecha — memoria del proyecto) gana puntos; en cultivos irrigados o represas pierde validez.
6. **Coherencia cruzada**: candidato confirmado si ≥ 2 fuentes independientes coinciden dentro de 30 m. Listar todos con su rango, distancia entre fuentes y clase de cobertura.

**Bases de nascentes en Paraná:** (i) FBDS vía IAT [VERIFICADO, descargada]; (ii) IAT `Nascentes/Formulario_Cadastro_Nascentes_2025` — formulario de cadastro ciudadano/técnico, no una base cartográfica validada [VERIFICADO que existe, contenido no evaluado]; (iii) nascentes declaradas en el CAR de cada inmueble (SICAR; el WFS estatal expone hidrografía poligonal declarada, no vimos capa puntual de nascentes en `geoserver.pr.gov.br`) [parcialmente verificado]; (iv) PronaSolos-PR registró sólo ríos perennes y nascentes para la base del Paraná III (oeste del estado, fuera del bbox).

**Validación de campo obligatoria** (no negociable): visita en **estación seca** (agosto-septiembre) a cada candidato con GPS (RTK o al menos L1/L5 con < 1 m), registro de: agua aflorante sí/no, caudal aproximado, sustrato, presencia de cauce definido aguas abajo, fotos georreferenciadas. Sólo lo perenne confirmado recibe buffer de 50 m; lo intermitente se reporta como olho d'água (sin APP de 50 m según redacción de la Lei 12.727/2012, pero se recomienda protección).

---

## 6. Precisión e incertidumbre: cómo reportarla al cliente

| Componente | Fuente | Incertidumbre planimétrica a declarar | Consecuencia sobre el buffer |
|---|---|---|---|
| Borde de vegetación arbórea | S2 10 m, clasificación RF | **± 1 píxel = ± 10 m** (más en bordes diagonales) | Área de vegetación dentro del buffer con error relativo ≈ (perímetro × 10 m)/área. En una franja de 30 m, un error de 10 m es 33 % del ancho. |
| Borde de vegetación (referencia) | MapBiomas 30 m | ± 30 m | Sólo para contexto; jamás para medir buffer. |
| Eje del curso (leito) | FBDS (RapidEye 5 m, 1:25.000) | ± 5-15 m (estimación a partir de la escala; **no hay RMSE publicado por FBDS que hayamos podido verificar** — el metadato oficial en geo.fbds.org.br no respondió) | Buffer de 30 m con ± 5-15 m: usable como diagnóstico. |
| Eje del curso | IAT otto 2020 / cartas 1:50.000 | ± 25-50 m (0,5-1 mm a 1:50.000) | Buffer de 30 m queda dentro del error: sólo para topología. |
| Eje del curso | DEM 30 m (GLO-30/FABDEM) | ± 1 píxel = ± 30 m; mayor en cabeceras y bajo dosel (DSM) | El buffer de 30 m tiene incertidumbre del orden de su propio ancho. |
| Nascente | FBDS punto / cabecera DEM | ± 15-30 m / ± 30-60 m | El radio de 50 m se desplaza hasta la mitad de su tamaño. |
| Ancho del curso (< 10 m vs 10-50 m) | FBDS por tramos de 100 m; S2 no lo mide | Clase FBDS; en campo con cinta | Cambia el buffer de 30 a 50 m: verificar en campo todo tramo clasificado FBDS como "10-50 m" (hay 3 polígonos en el bbox). |

**Recomendaciones de verificación (de mayor a menor valor):**
1. **Levantamiento GPS RTK de la borda del leito regular** de cada curso dentro y en el límite de la propiedad (caminata por el cauce en estación seca, puntos cada 20-30 m y en cada quiebre), más los nascentes confirmados. Es lo único que fija el leito con precisión de decímetros y tiene valor probatorio.
2. **Vuelo de dron** (Mavic 3M/Lito X1 — memoria: GSD = h/36,7) con ortomosaico < 5 cm: ve el cauce donde el dosel es discontinuo, delimita el borde arbóreo con ± 0,5 m, y documenta el uso dentro del buffer. No ve el leito bajo dosel cerrado.
3. **Hidrografía FBDS/IAT** como referencia administrativa: adjuntar en el informe la comparación "FBDS vs RTK" con desplazamiento medio y máximo, porque es la base con la que el órgano probablemente compare.

**Frase de alcance que debe ir en el informe:** "El presente diagnóstico satelital es **preliminar**; delimita cobertura vegetal con precisión de ±10 m y utiliza la hidrografía oficial FBDS/IAT (2013, 1:25.000) como referencia del leito regular. No constituye laudo con validez legal: el CAR es declaratorio (Lei 12.651/2012 Art. 29) y su validación por el IAT-PR sigue la IN IAT 05/2023; la posición del leito regular y la perenidad de nascentes deben confirmarse en campo (GPS RTK) antes de cualquier uso administrativo."

**Nota sobre áreas consolidadas (Art. 61-A):** si hay uso agropecuario en APP anterior a 22-jul-2008, la recomposición exigida depende de los módulos fiscales del inmueble (5, 8, 15 o 20-100 m para cursos < 10 m; 15 m de radio en nascentes) — el módulo fiscal de São Sebastião da Amoreira / Santo Antônio do Paraíso **[NO VERIFICADO]** en esta sesión; determinarlo (tabla INCRA) antes de calcular pasivos.

---

## 7. Lista de DOIs verificados (Crossref API, 2026-09-06)

Formato: autor(es), año, revista, DOI — aporte.

1. McFeeters, 1996, *Int. J. Remote Sensing*, 10.1080/01431169608948714 — NDWI original.
2. Xu, 2006, *Int. J. Remote Sensing*, 10.1080/01431160600589179 — MNDWI (Green/SWIR).
3. Feyisa, Meilby, Fensholt, 2014, *Remote Sens. Environ.*, 10.1016/j.rse.2013.08.029 — AWEI.
4. Pekel, Cottam, Gorelick, Belward, 2016, *Nature*, 10.1038/nature20584 — Global Surface Water.
5. Du, Zhang, Ling et al., 2016, *Remote Sensing*, 10.3390/rs8040354 — MNDWI a 10 m en S2 por afilado.
6. Yang, Zhao, Qin et al., 2017, *Remote Sensing*, 10.3390/rs9060596 — agua urbana a 10 m con NDWI afilado.
7. Radoux, Chomé, Jacques et al., 2016, *Remote Sensing*, 10.3390/rs8060488 — límite sub-píxel de S2 (agua lineal desde ~5 m en condiciones ideales).
8. Lu, Yang, Lu, 2020, *J. Hydrology*, 10.1016/j.jhydrol.2020.124689 — ríos pequeños (≥10 m) con S2 + DEM.
9. Kirby, Ferguson, Rennie, 2024, *Remote Sens. Appl. Soc. Environ.*, 10.1016/j.rsase.2024.101367 — comparación de métodos S2; discontinuidad < 40 m.
10. Liang, Mao, Yang et al., 2022, *Remote Sensing*, 10.3390/rs14194693 — ASRM ríos pequeños S2 + MERIT.
11. Li, Wu, Chen et al., 2020, *Remote Sensing*, 10.3390/rs12172737 — extracción de ríos S2 + DEM.
12. Li, Wang, Qin et al., 2021, *Remote Sensing*, 10.3390/rs13142650 — ríos en bankfull con S2 + DEM.
13. Cavallo, Papa, Negro et al., 2022, *Sci. Reports*, 10.1038/s41598-022-26034-z — intermitencia con serie S2.
14. Allen & Pavelsky, 2018, *Science*, 10.1126/science.aat0636 — GRWL, ríos ≥ 30 m.
15. O'Callaghan & Mark, 1984, *CVGIP*, 10.1016/S0734-189X(84)80011-0 — D8 y acumulación.
16. Tarboton, 1997, *Water Resour. Res.*, 10.1029/96WR03137 — D-infinity.
17. Rennó, Nobre, Cuartas et al., 2008, *Remote Sens. Environ.*, 10.1016/j.rse.2008.03.018 — HAND.
18. Nobre, Cuartas, Hodnett et al., 2011, *J. Hydrology*, 10.1016/j.jhydrol.2011.03.051 — HAND hidrológico.
19. Wang & Yin, 1998, *J. Hydrology*, 10.1016/S0022-1694(98)00189-9 — redes de DEM a dos escalas.
20. Bortolini, Taborda da Silveira, Siame, 2025, *RAEGA*, 10.5380/raega.v62i1.98168 — redes de DEM globales en Brasil, flujo simple vs múltiple.
21. Yamazaki et al., 2017, *GRL*, 10.1002/2017GL072874 — MERIT DEM.
22. Yamazaki et al., 2019, *WRR*, 10.1029/2019WR024873 — MERIT Hydro.
23. Lehner, Verdin, Jarvis, 2008, *Eos*, 10.1029/2008EO100001 — HydroSHEDS.
24. Grill, Lehner, Thieme et al., 2019, *Nature*, 10.1038/s41586-019-1111-9 — Free-Flowing Rivers.
25. Guth & Geoffroy, 2021, *Transactions in GIS*, 10.1111/tgis.12825 — "Copernicus wins" (precisión DEMs 1 arc-s).
26. Bielski, López-Vázquez, Grohmann et al., 2024, *IEEE TGRS*, 10.1109/TGRS.2024.3368015 — ranking DEMIX.
27. Uuemaa et al., 2020, *Remote Sensing*, 10.3390/rs12213482 — precisión vertical de DEMs globales.
28. Hawker et al., 2022, *Environ. Res. Lett.*, 10.1088/1748-9326/ac4d4f — FABDEM.
29. Souza et al., 2020, *Remote Sensing*, 10.3390/rs12172735 — MapBiomas método.
30. Rosa, Brancalion, Crouzeilles et al., 2021, *Science Advances*, 10.1126/sciadv.abc4547 — destrucción oculta de bosques maduros en Mata Atlântica.
31. Sothe, Almeida, Liesenberg, Schimalski, 2017, *Remote Sensing*, 10.3390/rs9080838 — S2/L8 para estágios sucessionais (SC).
32. Perez, Bourscheidt, Lopes, 2022, *Ecological Informatics*, 10.1016/j.ecoinf.2022.101680 — altura de vegetación en Mata Atlântica con S2.
33. Xiao, Wang, Zhang et al., 2024, *J. Remote Sensing*, 10.34133/remotesensing.0204 — bosque natural vs plantado a 30 m.
34. Zhou, Han, Wang et al., 2024, *Forests*, 10.3390/f15111866 — eucalipto con CCDC + RF.
35. Breiman, 2001, *Machine Learning*, 10.1023/A:1010933404324 — Random Forest.
36. Belgiu & Drăguţ, 2016, *ISPRS J. Photogramm.*, 10.1016/j.isprsjprs.2016.01.011 — RF en teledetección.
37. Haralick, Shanmugam, Dinstein, 1973, *IEEE TSMC*, 10.1109/TSMC.1973.4309314 — GLCM.
38. Gorelick et al., 2017, *Remote Sens. Environ.*, 10.1016/j.rse.2017.06.031 — GEE.
39. Hansen et al., 2013, *Science*, 10.1126/science.1244693 — Global Forest Change.
40. Brown et al., 2022, *Sci. Data*, 10.1038/s41597-022-01307-4 — Dynamic World.
41. Mullissa et al., 2021, *Remote Sensing*, 10.3390/rs13101954 — S1 ARD en GEE.
42. Zanaga et al., 2022, Zenodo, 10.5281/zenodo.7254221 — WorldCover v200 (DataCite, resuelve vía doi.org).
43. Oliveira, Cassol, Ganem et al., 2020, *Rev. Bras. Cartografia* 72 (esp. 50 anos), 10.14393/rbcv72nespecial50anos-56591 — **revisión** de iniciativas de mapeo del Cerrado que describe el proyecto FBDS (RapidEye 5 m, 2013, 1:25.000). *No es el paper metodológico de FBDS*; ese no se pudo verificar.

**No verificados / descartados:** metadato oficial FBDS (`geo.fbds.org.br/Metadados Mapeamento FBDS.pdf`) — DNS no resuelve; el DOI 10.1002/joc.3370080202 que circula como "Jenson & Domingue 1988" corresponde a otro artículo (Hamilton et al.) — no citar; 10.1126/sciadv.abc6667 no existe (el correcto de Rosa 2021 es abc4547).

---

## 8. Pipeline paso a paso (GEE + Python local)

**Entradas:** polígono de la propiedad (157,75 ha) en EPSG:4326 y EPSG:31982 (SIRGAS 2000 / UTM 22S). Todas las áreas se calculan en 31982.

1. **Descargar hidrografía oficial** para el bbox con el código de §2.3 (ya hecho: ver §9). Reproyectar todo a EPSG:31982. Cortar por la propiedad + 100 m.
2. **Armonizar fuentes hidrográficas**: en un GeoPackage `hidro_ref.gpkg` con capas `fbds_rios_l`, `fbds_rios_pol`, `fbds_nascentes`, `fbds_massas`, `otto2020`, `bho5k`, `bc250`, `car_vecinos`. Calcular por tramo FBDS la distancia al tramo otto/BHO más cercano (Hausdorff por segmento) → tabla de discrepancias.
3. **DEM**: en GEE, `ee.ImageCollection('COPERNICUS/DEM/GLO30_2024_1').select('DEM').mosaic()` recortado al bbox + 2 km, exportar a GeoTIFF (EPSG:31982, 30 m). Repetir con `NASA/NASADEM_HGT/001` para control. FABDEM sólo si el cliente acepta uso no comercial o se licencia.
4. **Red de drenaje local** (Python: `pysheds` o WhiteboxTools): rellenar depresiones (`fill_depressions`/`breach`), dirección D8 y D-inf (Tarboton 1997), acumulación, umbral calibrado contra longitud FBDS por subcuenca (paso 2), `stream_link`, vectorizar; **HAND** con `whitebox.elevation_above_stream`. Guardar `dem_streams.gpkg`, `hand.tif`.
5. **Compuestos S2** en GEE: `COPERNICUS/S2_SR_HARMONIZED` unido a `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` (`cs_cdf ≥ 0,65`), máscara SCL ∉ {3,8,9,10,11} dilatada 2 px, mediana de estación seca (jun-ago 2026) y húmeda (dic-2025–feb-2026). Bandas 10 m nativas; 20 m remuestreadas a 10 m. Imprimir min/max/media de cada banda e índice sobre la propiedad (regla del proyecto: verificar rangos por capa).
6. **Índices**: NDVI, NDMI, NDRE, NDWI (B3/B8), MNDWI afilado (Du 2016), AWEI_sh; GLCM 5×5 sobre B8 (contraste, entropía, homogeneidad); ΔNDVI seca-húmeda.
7. **Agua abierta**: umbral local sobre MNDWI/NDWI (Otsu por propiedad + vecindario 2 km) restringido a HAND ≤ 10 m; cruzar con `JRC/GSW1_4` `occurrence ≥ 50` y MapBiomas Água 2024. Salida: `agua_abierta_s2.gpkg` (represas, lagos ≥ 2 px). Todo cuerpo < 2 px se reporta como "no evaluable a 10 m" (regla: no evaluable ≠ sin novedad).
8. **Etiquetas**: MapBiomas Coleção 10 (`…collection10_coverage_v2`, banda `classification_2024`) erosionada 1,5 px de 30 m; muestreo estratificado 200-400 puntos/clase en radio 15 km; separar 30 % en bloques espaciales para validación.
9. **RF en GEE** (`ee.Classifier.smileRandomForest(300)`) sobre las 20-25 variables del paso 6; matriz de confusión, exactitud global, F1 por clase; exportar `cobertura_10m.tif` y vectorizar (`reduceToVectors`, escala 10 m) → `cobertura_10m.gpkg`.
10. **Buffers legales** (Python/GeoPandas, EPSG:31982): (a) 30 m desde el eje FBDS de cursos ≤ 10 m — **ojo**: el eje no es la borda; sumar ½ ancho estimado (tramo FBDS de "0-10 m": asumir 2,5 m y declararlo); (b) 50 m desde el borde del polígono FBDS para cursos 10-50 m; (c) radio 50 m en nascentes FBDS + candidatos confirmados; (d) borde de masas de agua naturales (30 m rural) y reservatórios artificiales según el Art. 4º III / 5º. Disolver; cortar por la propiedad.
11. **Cobertura dentro del buffer**: intersección `buffers × cobertura_10m`: ha y % de Formação Florestal (arbórea nativa), Silvicultura, Pastagem, Lavoura, Agua, Suelo. Reportar también el mismo cruce con **FBDS `fbds_app_uso`** (2013) para mostrar la evolución 2013→2026 y con MapBiomas 2024 (30 m) como referencia.
12. **Historia**: Hansen `lossyear` (2001-2025) y MapBiomas 1985-2024 por píxel del buffer: año de primera y última condición forestal → tabla "consolidado antes de 22-jul-2008 sí/no" (indicio, no prueba).
13. **Nascentes**: aplicar §5 (ranking 6 criterios); tabla de candidatos con coordenadas, fuentes que coinciden, HAND, NDMI-z, cobertura, y columna "verificar en campo".
14. **Incertidumbre**: para cada cifra de área, calcular el intervalo con buffer ± 10 m del borde (área mínima/máxima) y reportar ambos. Para la posición del leito, reportar desplazamiento medio FBDS–otto–DEM.
15. **Entregables**: GeoPackage con todas las capas, mapa PDF (marca Pixadvisor) con la frase de alcance de §6, tabla de superficies con intervalos, lista de puntos de campo (GPX) para RTK, y este documento como anexo metodológico.

---

## 9. Datos descargados en esta sesión (`..\MATA_CILIAR_SANTO_ANTONIO\datos_externos\`)

Todos en GeoJSON EPSG:4326, consultados por envelope lon -50,70/-50,62, lat -23,52/-23,45; conteos y longitudes calculados tras recorte al bbox y proyección a EPSG:31982.

| Archivo | URL usada | Resultado |
|---|---|---|
| `IAT_FBDS_rios_ate10m.geojson` | `https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/fbds_rio_ate10m_larg/FeatureServer/0/query` | **231 tramos, 69,37 km** (municipios Nova Fátima, Santo Antônio do Paraíso, São Sebastião da Amoreira) |
| `IAT_FBDS_rios_acima10m_pol.geojson` | `…/Cursos_D_água_Largura_acima_de_10_metros_FBDS/FeatureServer/0/query` | 3 polígonos, 4,16 ha (Rio Congonhas y afluentes >10 m) |
| `IAT_FBDS_nascentes.geojson` | `…/fbds_nascentes/FeatureServer/0/query` | **38 nascentes** (21 S.A. do Paraíso, 17 S.S. da Amoreira) |
| `IAT_FBDS_massas_dagua.geojson` | `…/fbds_massas_dagua/FeatureServer/0/query` | 33 polígonos, 91,78 ha (natural/artificial, rural/urbano) |
| `IAT_FBDS_app_hidrica.geojson` | `…/fbds_app/FeatureServer/0/query` | 9 multipolígonos, 440,17 ha de APP (curso 0-10 m → 30 m; 10-50 m → 50 m; nascente → 50 m; massa → 30 m) |
| `IAT_FBDS_app_uso.geojson` | `…/fbds_app_uso/FeatureServer/0/query` | Uso 2013 dentro de APP: formação florestal, área antropizada, silvicultura, área edificada |
| `IAT_FBDS_uso_cobertura_2013.geojson` | `…/fbds_uso_cobertura_2013/FeatureServer/0/query` | 12 multipolígonos, cubre el bbox (6 clases) |
| `IAT_otto_trecho_drenagem_2020.geojson` | `…/rede_otto_trech_drena_2020_iat/FeatureServer/0/query` | **90 tramos, 73,89 km**; Strahler 1: 48, 2: 22, 3: 12, 4: 3, 6: 5; nombres: Rio Congonhas, Ribeirão do Dez, do Pari, do Salto |
| `IAT_otto_areas_drenagem_2020.geojson` | `…/rede_otto_areas_drena_2020_iat/FeatureServer/0/query` | 116 ottobacias (nivel 9-10) |
| `IAT_hidro50k_massa_dagua_paranacidade.geojson` | `…/hidro_50k_massa_dagua_prcidade/FeatureServer/0/query` | 15 polígonos, 74,16 ha, campo `regime` |
| `IAT_ZEE_rios_detalhados.geojson` | `…/zee_rios/FeatureServer/0/query` | 15 tramos, 9,34 km (sólo ríos nombrados, orden ≥ 4) |
| `ANA_BHO2017_5k_trecho_drenagem.geojson` | `https://www.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_TRECHODRENAGEM/FeatureServer/0/query` | **10 tramos, 31,49 km** (Rio Congonhas, Ribeirão do Salto, da Porteira, do Dez, Água do Chapadão) |
| `ANA_BHO2017_5k_area_drenagem.geojson` | `…/SPR/BHO2017_5K_AREADRENAGEM/FeatureServer/0/query` | 15 ottobacias |
| `ANA_BHO2017_50k_trecho_drenagem.geojson` / `…_area_drenagem.geojson` | `…/SPR/BHO2017_50K_TRECHODRENAGEM/…` y `…_AREADRENAGEM/…` | 2 tramos, 3,84 km / 4 áreas |
| `IBGE_BC250_trecho_drenagem.geojson` | `https://geoservicos.ibge.gov.br/geoserver/wfs` · `CCAR:BC250_2025_hid_trecho_drenagem_l` | 16 tramos (13 tras recorte), 34,20 km, todos `regime = Permanente` |
| `PR_geoserver_car_hidrografia_pol.geojson` | `https://geoserver.pr.gov.br/geoserver/ows` · `car:hidrografia_pol_p4674` | 73 polígonos declarados por 54 inmuebles CAR (49 RIO_ATE_10, 11 reservatórios, 7 RIO_10_A_50, 6 lagos naturales). Una geometría tiene topología inválida (aplicar `make_valid`). |
| `IBGE_municipio_4126009.geojson` | `https://servicodados.ibge.gov.br/api/v3/malhas/municipios/4126009` | Polígono municipal São Sebastião da Amoreira (contiene el centroide) |

**No se pudo descargar:** FBDS directo (`geo.fbds.org.br`, DNS); BDGEx vectorial 1:50.000 (WFS roto, descarga requiere login); IBGE BC25/BC100 (no existen para PR); IAT hidrografía 1:10.000 por radar (sólo litoral). Archivos auxiliares de verificación: `metodologia\_dois_check.json`, `metodologia\_gee_check.json`, `datos_externos\_geopr_meta.json`, `_download_log_*.json`, `_stats_bbox.json`, listas de capas WFS (`_geoserver_pr_layers.txt`, `_ibge_wfs_layers.txt`).

**Lectura de la comparación entre fuentes:** en el mismo bbox la densidad de red va de 31,5 km (ANA 5k, sólo cuencas ≥ 5 km²) → 34,2 km (BC250) → 73,9 km (IAT otto 1:50k) → **69,4 km + 3 polígonos (FBDS 1:25k)**. La FBDS y la otto 2020 tienen longitud similar pero geometría distinta (RapidEye vs carta 1:50.000): la discrepancia posicional entre ambas es el primer número de incertidumbre que hay que calcular en el paso 2 del pipeline y mostrar al cliente.
