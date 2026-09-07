# COMPARACION FUENTES DE GOBIERNO — Hidrologia PRO, Fazenda Santo Antonio (G1 144.21 ha + G2 13.54 ha)

Generado por `an_11_hidrologia_pro.py` el 2026-09-06 18:36. CRS EPSG:31982. Solo cuenta lo que cae DENTRO de las glebas; lo exterior se uso para derivar (cuencas, correspondencia).

JSON de cifras: `02_ANALISIS/hidrologia_pro/resultados_hidrologia_pro.json`. Capas nuevas de gobierno: `datos_externos/gov_pro/` (log `_download_log_gov_pro.json`).


## 1. Tabla fuente por fuente

| Institucion | Capa | Escala | Fecha | URL | Respondio | Que aporta | Discrepancia con nuestro resultado |
|---|---|---|---|---|---|---|---|
| IAT-PR (replica SICAR) | Base_Geo_Cadastro_Ambiental_rural (9 capas CAR) | declaratorio (SICAR) | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/Base_Geo_Cadastro_Ambiental_rural/FeatureServer/8 | si | CAR PROPIO PR-4124301-F127CD1E73FA4B9DB4FA0CC2B3FC1E14 (143.3 ha) y CAR de G2 PR-4124301-5223911747FD4B878118F1823D609DD6; APP, RL, veg. nativa, consolidada, hidrografia, reservatorio declarados | APP CAR 12.44 vs medida 11.96 ha (G1); RL averbada 2.45 vs exigida 28.84 ha; reservatorio 2.27 vs FBDS 1.95 ha |
| INCRA via IAT | imoveis_certificados_sigef_incra / snci | certificacao georreferenciada | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/imoveis_certificados_sigef_incra/FeatureServer/0 | si | parcelas SIGEF que cubren las glebas: FAZENDA SANTO ANTÔNIO - FAZENDA SANTO ANTÕNIO REGISTRADA 143.34 ha (matr. 8.334, mun. 4124301); FAZENDA SANTO ANTONIO - FAZENDA SANTO ANTONIO CERTIFICADA 95.90 ha (matr. 1168, mun. 4124301); FAZENDA CACHOEIRA - Gleba 12 REGISTRADA 705.74 ha (matr. 8325, mun. 4126009) | perimetro SIGEF vs poligono del cliente: 142.89 ha de G1 dentro del SIGEF principal |
| SICAR (SFB) directo | consultapublica.car.gov.br downloads/exportShapeFile | declaratorio | 2026-09-06 | https://consultapublica.car.gov.br/publico/estados/downloads | parcial | pagina responde solo con TLS legacy; descarga exige reCAPTCHA (no se salto) | n/a |
| Paraná geoserver (CELEPAR) | car:hidrografia_pol_p4674 (WFS) | declaratorio | 2026-09-06 | https://geoserver.pr.gov.br/geoserver/ows (WFS) | si | hidrografia CAR (misma fuente, version WFS): reservatorio propio 2.278 ha | vs replica IAT 2.266 ha (dif. 0.012 ha) |
| Copernicus/NASA/USGS/JAXA/Bristol via GEE | GLO30_2024_1, NASADEM_HGT/001, SRTMGL1_003, AW3D30 V4_1, FABDEM V1-2 | 30 m (1 arc-sec) | 2000-2024 | GEE (IDs verificados con getInfo 2026-09-06) | si | ensamble de 5 DEM: red D8 con umbral calibrado y dispersion por arroio | ver tabla por arroio (dispersion entre DEM y vs FBDS) |
| INPE | TOPODATA (SRTM refinado 30 m) | 30 m | 2008 | http://www.dsr.inpe.br/topodata/ | no | DNS no resuelve el 2026-09-06 (espejo webmapit 404); reemplazado por SRTMGL1 1 arc-sec real | n/a |
| IAT-PR | curvas_de_nivel_1_50000_20m | 1:50.000 (eq. 20 m) / 1:25.000 (10 m) | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/curvas_de_nivel_1_50000_20m/FeatureServer/0 | si | 9 curvas en la zona (cotas 620-720 m): relieve oficial para contrastar el DEM | ver seccion DEM vs curvas |
| ESA/Google via GEE | S2_SR_HARMONIZED + Cloud Score+ (338 escenas, 73 utiles en la represa) | 10 m | 2024-09..2026-09 | GEE | si | frecuencia de agua por pixel, espejo por escena, NDMI seco | espejo represa mediana lluviosa 0.831 ha vs FBDS 1.95 / CAR 2.12 |
| ESA via GEE | S1_GRD IW VV (43 escenas, orbita ['24']) | 10 m | 2024-09..2026-09 | GEE | si | frecuencia de agua a traves de nubes; Otsu -11.47 dB | espejo S1(-16 dB) freq>=0.5: 1.16 ha |
| JRC via GEE | GSW1_4 MonthlyHistory 2015-2021 + GlobalSurfaceWater | 30 m | 1984-2021 | GEE | si | max_extent 1.71 ha; freq mensual>=0.5 0.45 ha | GSW1_4 termina en 2021-12 (no cubre 2022-24) |
| MapBiomas via GEE | Agua colecao 4 (water_v3) 1985-2024 | 30 m | 2020-2024 | GEE | si | agua 2024 1.08 ha; freq 2020-24>=0.5 1.17 ha | vs FBDS 1.95 ha |
| ANA/SNIRH | SPR/Massa_dagua, Armazena_Reservatorio_UGRH | 1:50k-1:250k | 2026-09-06 | https://www.snirh.gov.br/arcgis/rest/services/SPR/Massa_dagua/FeatureServer/0 | si | 2 masas ANA en zona; 1.95 ha en la represa | coincide |
| IAT-PR / PARANACIDADE | hidro_50k_massa_dagua_prcidade | 1:50.000 | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/hidro_50k_massa_dagua_prcidade/FeatureServer/0 | si | 1.78 ha en la represa | coincide |
| IAT-PR | map_uso_cobertura_terra_2012 (WorldView-2 2012-13) | 1:10.000 aprox. | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/map_uso_cobertura_terra_2012/FeatureServer/0 | si | corpos d'agua 1.93 ha en la represa; clases en zona {'Agricultura Anual': 2.098, 'Agricultura Perene': 0.0, 'Corpos d’Água': 1.933, 'Floresta Nativa': 0.011, 'Pastagem/Campo': 2.982, 'Plantios Florestais': 0.0, 'Várzea': 0.0} | vs FBDS 1.95 ha |
| IAT-PR | outorgas_sigarh / out_captacao_crh / mananciais_2023 | puntual | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/outorgas_sigarh/FeatureServer/0 | si | 1 outorgas SIGARH + 0 CRH en PROP+500 m; 1 en la propiedad | hay outorga en la propiedad |
| IAT-PR | mananciais_2023_iat / Mananciais_Superficiais_IAT_2026 | poligono de cuenca | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/mananciais_2023_iat/FeatureServer/0 | si | areas de manancial de abastecimento publico que contienen la propiedad | n/a (contexto) |
| IAT-PR | fragmentos_florestais_prioritarios_iatpr | poligono (MapBiomas/IAT) | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/fragmentos_florestais_prioritarios_iatpr/FeatureServer/0 | si | 3 fragmentos prioritarios tocan la propiedad | coincide con el fragmento 2 (mata vecina) del an_02 |
| IAT-PR/FBDS | fbds_nascentes (re-descarga de control) | 1:25.000 (RapidEye 5 m, 2013) | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/fbds_nascentes/FeatureServer/0 | si | 38 nascentes en bbox (identicas a la descarga previa: True) | 1 nascente FBDS dentro de G1 (306158); ninguna en los candidatos DEM |
| IAT-PR | rede_otto_trech_drena_2020_iat | 1:50.000 | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/rede_otto_trech_drena_2020_iat/FeatureServer/0/query | si | trazado/longitud de cursos en G1: 2.043 km asignados a arroios FBDS | vs FBDS 2.038 km en G1; desplazamiento mediano respecto del eje FBDS [26.2, 11.8, 24.7] m por arroio |
| ANA/SNIRH | BHO2017_5K_TRECHODRENAGEM | 1:5k (cuencas >=5 km2) | 2026-09-06 | https://www.snirh.gov.br/arcgis/rest/services/SPR/BHO2017_5K_TRECHODRENAGEM/FeatureServer/0 | si | trazado/longitud de cursos en G1: 1.070 km asignados a arroios FBDS | vs FBDS 2.038 km en G1; desplazamiento mediano respecto del eje FBDS [9.5, 24.4] m por arroio |
| IBGE | BC250_2025_hid_trecho_drenagem_l | 1:250.000 | 2026-09-06 | https://geoservicos.ibge.gov.br/geoserver/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName=CCAR%3ABC250_2025_hid_trecho_drenagem_l&bbox=-50.70%2C-23.52%2C-50.62%2C-23.45&outputFormat=application%2Fjson&srsName=EPSG%3A4326 | si | trazado/longitud de cursos en G1: 1.153 km asignados a arroios FBDS | vs FBDS 2.038 km en G1; desplazamiento mediano respecto del eje FBDS [34.4, 39.6] m por arroio |
| IAT-PR / CBH | enquadramento_base_hidrografica | 1:50.000 (otto) | 2026-09-06 | https://geopr.iat.pr.gov.br/server/rest/services/00_PUBLICACOES/enquadramento_base_hidrografica/FeatureServer/0 | si | trazado/longitud de cursos en G1: 2.043 km asignados a arroios FBDS | vs FBDS 2.038 km en G1; desplazamiento mediano respecto del eje FBDS [26.2, 11.8, 24.7] m por arroio |


No respondieron / no usables: INPE TOPODATA (DNS), SICAR directo (reCAPTCHA; no se salto), IAT `pbnp_*` Norte Pioneiro (exige token), Sudersha 1:20.000 (0 feats en el bbox: solo litoral/RMC), BDGEx vectorial (login).


## 2. CAR del inmueble: existe, y es el "vecino" que declaraba la represa

El poligono `PR-4124301-F127CD1E73FA4B9DB4FA0CC2B3FC1E14` cubre el 99.1% de G1 (142.89 de 144.21 ha) y coincide con la parcela SIGEF/INCRA "FAZENDA SANTO ANTÔNIO - FAZENDA SANTO ANTÕNIO" (143.34 ha, matricula 8.334, REGISTRADA). Es el CAR del propio inmueble (status AT, condicao "Aguardando analise"), no de un vecino. G2 (los 6 alqueires) esta dentro del CAR `PR-4124301-5223911747FD4B878118F1823D609DD6` (94.13 ha declaradas, condicao "Analisado, aguardando atendimento a notificacao"), que a su vez coincide con la parcela SIGEF "FAZENDA SANTO ANTONIO - FAZENDA SANTO ANTONIO" (95.90 ha, matricula 1168): G2 es parte de un inmueble mayor ya certificado.

| Gleba | Tema | Declarado en CAR (ha) | Medido por nosotros (ha) | Dif. CAR - medido |
|---|---|---|---|---|
| G1 | Area do imovel | 143.3442 | 144.21 | -0.87 |
| G1 | APP (geometria CAR en la gleba / num_area) | 12.44 / 10.45 | 11.96 (30 m) / 13.62 (cenario FBDS) | 0.48 |
| G1 | Reserva Legal (reserva_legal) | 2.45 en gleba / 2.45 decl. | exigida 20%: 28.84; remanescente fuera APP: 9.81 | -26.39 |
| G1 | Vegetacao nativa / remanescente | 3.80 en gleba / 3.80 decl. | 17.7 | -13.9 |
| G1 | Area consolidada | 125.127 | - | - |
| G1 | Hidrografia rio ate 10 m (poligono CAR, ha) | 0.284 | 2.038 km FBDS | - |
| G1 | Reservatorio artificial (ha) | 2.266 | FBDS 1.95 / S2 ref 0.831 | 0.32 |
| G2 | Area do imovel (CAR mayor que la gleba: G2 es parte de el) | 94.1313 | 13.54 | 80.59 |
| G2 | APP (geometria CAR en la gleba / num_area) | 0.00 / 2.41 | 0.22 (30 m) / 0.22 (cenario FBDS) | -0.22 |
| G2 | Reserva Legal (reserva_legal) | 1.85 en gleba / 9.74 decl. | exigida 20%: 2.71; remanescente fuera APP: 2.46 | -0.85 |
| G2 | Vegetacao nativa / remanescente | 1.85 en gleba / 9.74 decl. | 2.68 | -0.83 |
| G2 | Area consolidada | 11.683 | - | - |
| G2 | Hidrografia rio ate 10 m (poligono CAR, ha) | 0.0 | 0.033 km FBDS | - |
| G2 | Reservatorio artificial (ha) | 0.0 | - | 0.0 |


Notas: (a) los CAR se solapan entre si dentro de la propiedad (B3FC1E14-3D609DD6 1.89 ha); (b) la replica IAT del CAR no publica nascentes (temas de hidrografia en el bbox: ['LAGO_NATURAL', 'RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO', 'RIO_10_A_50', 'RIO_ATE_10']); (c) el reservatorio declarado en el CAR propio mide 2.266 ha (IAT) / 2.278 ha (WFS geoserver), contra 1.95 ha FBDS 2013.


## 3. Ensamble de 5 DEM vs FBDS: dispersion posicional del lecho

| DEM | Umbral (ha) | Red en PROP+500 (km) | FBDS->DEM med/p90 (m) | DEM->FBDS med/p90 (m) | vs curvas IAT 1:50k sesgo/MAD/RMSE (m) |
|---|---|---|---|---|---|
| GLO30 | 20 | 8.2 | 23.0 / 67.3 | 25.9 / 102.1 | 5.54 / 4.22 / 9.09 |
| NASADEM | 20 | 7.8 | 29.4 / 89.5 | 31.1 / 161.0 | 7.0 / 4.0 / 10.42 |
| SRTMGL1 | 10 | 9.8 | 27.5 / 86.8 | 39.7 / 250.3 | 7.0 / 4.0 / 11.08 |
| AW3D30 | 20 | 7.9 | 35.6 / 82.7 | 38.5 / 118.8 | 7.0 / 5.0 / 10.22 |
| FABDEM | 20 | 7.8 | 25.4 / 73.3 | 26.8 / 97.2 | 5.38 / 4.1 / 8.57 |


### Por arroio (dentro de cada gleba + 60 m)

| Gleba | Arroio | Long. FBDS en gleba (m) | Dist. FBDS->cada DEM med/p90 (m) | Dispersion ENTRE DEM med/p90 (m) | Mediana ensamble vs FBDS med/p90 (m) | APP30 FBDS (ha) | APP30 ensamble (ha) | Envolvente APP30 (ha) | Dif. simetrica (ha) |
|---|---|---|---|---|---|---|---|---|---|
| G1 | Arroio 1 (norte) | 522.8 | GLO30 27.5/60.2 NASADEM 37.1/60.4 SRTMGL1 37.1/55.4 AW3D30 49.4/77.6 FABDEM 22.2/57.9 | 38.4 / 48.0 | 29.4 / 55.4 | 2.435 | 3.731 | [2.435; 3.743] | 2.541 |
| G1 | Arroio 2 (central) | 950.7 | GLO30 9.7/27.3 NASADEM 17.9/55.4 SRTMGL1 15.4/35.4 AW3D30 32.5/47.9 FABDEM 17.2/55.8 | 48.4 / 94.7 | 7.9 / 19.5 | 5.783 | 5.563 | [5.326; 6.096] | 2.054 |
| G1 | Arroio 3 (sul) | 564.1 | GLO30 24.8/42.1 NASADEM 33.2/51.3 SRTMGL1 26.5/50.1 AW3D30 30.6/56.7 FABDEM 30.7/50.3 | 32.2 / 59.2 | 26.3 / 38.4 | 3.391 | 3.664 | [3.333; 3.681] | 2.749 |
| G2 | Arroio 1 (norte) | 32.7 | GLO30 4.9/13.7 NASADEM 13.5/21.7 SRTMGL1 11.8/21.7 AW3D30 12.9/23.2 FABDEM 4.9/13.7 | 11.8 / 26.5 | 7.9 / 19.6 | 0.216 | 0.168 | [0.144; 0.216] | 0.052 |


## 4. Represa: espejo por fuente y referencia

| Fuente / metrica | ha |
|---|---|
| fbds_2013_ha | 1.95 |
| car_declarado_iat_ha | 2.119 |
| car_declarado_geoserver_ha | 2.119 |
| car_declarado_total_incl_cabecera_ha | 2.266 |
| s2_freq_total_ge50_ha | 0.84 |
| s2_freq_chuva_ge50_ha | 0.83 |
| s2_freq_seca_ge50_ha | 0.88 |
| s2_freq_total_ge10_ha_extension_maxima | 1.12 |
| s2_freq_total_ge90_ha_nucleo_permanente | 0.0 |
| s1_freq16_ge50_ha | 1.16 |
| s1_freq18_ge50_ha | 0.95 |
| s1_freq20_ge50_ha | 0.76 |
| s1_otsu_vv_p50_db | -11.47 |
| s1_otsu_nota | Otsu sobre VV p50 en PROP+500 m cae en -11.5 dB con 58% del area por debajo: separa cultivo/bosque, NO agua (el agua es <1% del area y no forma modo). Se usan umbrales fijos -16/-18/-20 dB; -18 dB es el mas cercano al espejo S2/MapBiomas. |
| jrc_max_extent_1984_2021_ha | 1.71 |
| jrc_freq_mensual_2015_2021_ge50_ha | 0.45 |
| jrc_occurrence_media_pct | 39.1 |
| mapbiomas_agua_2024_ha | 1.08 |
| mapbiomas_freq_2020_2024_ge50_ha | 1.17 |
| mapbiomas_freq_1985_2024_ge50_ha | 1.35 |
| iat_massa_50k_paranacidade_ha | 1.785 |
| ana_massa_dagua_ha | 1.95 |
| iat_uso2012_wv2_corpos_dagua_ha | 1.933 |
| escena_2026_08_29_mndwi_ha | 0.91 |
| escena_2026_08_29_rf_ha | 1.98 |


Serie S2 por escena (zona de la represa 7.02 ha; 73 escenas utiles de 338): todas {'n': 73, 'min': 0.0, 'p25': 0.61, 'mediana': 0.861, 'p75': 0.971, 'p90': 1.049, 'max': 2.233}; lluviosa {'n': 29, 'min': 0.0, 'p25': 0.33, 'mediana': 0.831, 'p75': 0.891, 'p90': 0.997, 'max': 2.233}; seca {'n': 44, 'min': 0.0, 'p25': 0.708, 'mediana': 0.906, 'p75': 0.981, 'p90': 1.075, 'max': 1.241}.

Serie S1 (VV<-16 dB): todas {'n': 43, 'min': 0.0, 'p25': 1.166, 'mediana': 1.232, 'p75': 1.395, 'p90': 1.604, 'max': 2.167}; lluviosa med 1.181; seca med 1.341. Otsu local sobre VV p50: -11.47 dB.

**Espejo de referencia: 0.831 ha** (mediana del espejo S2 en estacion lluviosa (Oct-Mar) 2024-2026, escenas con >=90% de la zona valida). Espejo actual por sensor: {'S2 mediana lluviosa': 0.831, 'S2 freq_total>=0.5': 0.84, 'S1 -16 dB mediana': 1.232, 'S1 -18 dB mediana': 0.981, 'MapBiomas 2024': 1.08, 'MapBiomas freq 2020-24>=0.5': 1.17} -> envolvente [0.83; 1.23] ha. >= 1 ha: **INDETERMINADO: el espejo ACTUAL (2024-26) va de 0.83 (S2, 10 m, MNDWI>0) a 1.23 ha (S1 -16 dB / MapBiomas) segun sensor y umbral; el historico (FBDS 2013 1.95, WV2 2012 1.93, JRC max 1.71, CAR 2.12) es >= 1 ha**. Lei 12.651 art. 4 III + par. 4: el reservatorio artificial decorrente de barramento de curso natural tiene APP en la faixa de la licencia y queda DISPENSADO de esa faixa si el espejo es < 1 ha (vedada nova supressao). El espejo actual esta en la frontera de 1 ha: mientras no se mida en campo (perimetro GNSS del espejo en estacion lluviosa o cota del vertedero), la lectura conservadora es la de las bases oficiales (FBDS/CAR >= 1 ha): sin dispensa. Los 30 m del curso natural bajo el espejo (arroio 3) no dependen de esta cuestion.


## 5. Nascentes: veredicto por candidato

| Candidato | Gleba | HAND (m) | Nasc. FBDS (m) | Inicio otto (m) | Inicio ANA (m) | DEM con cabecera <=100 m | S2 freq lluviosa max | S1 f(-20dB) max | NDMI seco z | Uso IAT 2012 | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FBDS 306158 | G1 | 1.9 | 0.0 | 20.3 | 1186.2 | 3/5 | 0.0 | 0.023 | 1.03 | Pastagem/Campo; Várzea | PROBABLE |
| DEM_GLO30_cabeceira dem_1 | G1 | 0.0 | 96.7 | 76.7 | 1090.2 | 4/5 | 0.0 | 0.0 | 1.2 | Várzea | PROBABLE (MISMA CABECERA QUE LA NASCENTE FBDS, NO ES UNA NASCENTE ADICIONAL) |
| DEM_GLO30_cabeceira dem_2 | G1 | 0.0 | 727.0 | 732.9 | 951.0 | 3/5 | 0.0 | 0.0 | -3.55 | Agricultura Anual | POCO PROBABLE (EVIDENCIA NEGATIVA: SIN AGUA NI HUMEDAD, MAS SECO QUE EL ENTORNO EN LA SECA) |


**Dato nuevo del CAR propio:** ademas de la represa, declara un segundo `RESERVATORIO_ARTIFICIAL_DECORRENTE_BARRAMENTO` de 0.147 ha en la cabecera del Arroio 2 (a 45.0 m de la nascente FBDS 306158 y 7 m de dem_1), SIN agua detectable en 2024-26 (S2 freq max 0.0, S1 f16 max 0.047, MNDWI max -0.259): coherente con un acude en la nascente hoy seco, colmatado o bajo vegetacion. Es un punto obligatorio de la visita de campo: si existe barramento sobre la nascente, la APP es el radio de 50 m de la nascente (art. 4 IV) y el barramento requiere outorga/regularizacion.



Criterio: probable = base oficial (nascente FBDS<=60 m o inicio de trecho otto<=100 m) + (relieve: >=3 de 5 DEM con cabecera a <=100 m, o humedad: S2 freq lluviosa>=0.10 / S1 VV<-20 freq>=0.20 / NDMI p10 seco z>=1.5 vs entorno 100-300 m / uso IAT 2012 varzea-agua); probable tambien si relieve Y humedad sin base oficial; una sola linea = sin evidencia concluyente; ninguna = poco probable. NINGUN veredicto sustituye la verificacion en campo en estacion seca (Lei 12.651 art. 3 XVII: perenidad).


## 6. Cursos por fuente dentro de cada gleba

| Gleba | Arroio | FBDS (m) | otto 2020 (m) | ANA 5k (m) | IBGE BC250 (m) | Ensamble DEM (m) | CAR rio<=10 (m aprox.) | Nombre otto | Regime IBGE | Ancho agua persistente S2 (m) | S2 freq seca/lluv. (eje 15 m) | S1 f16 | JRC occ % | NDMI seco eje vs entorno |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | Arroio 1 (norte) | 522.8 | 496 | 509 | 601 | 646 | 309.5 | [] | ['Permanente'] | [] | 0.00 / 0.00 | 0.001 | - (JRC nunca vio agua en el eje) | 0.101 vs -0.176 |
| G1 | Arroio 2 (central) | 950.7 | 985 | 0 | 0 | 910 | 874.3 | [] | [] | [] | 0.00 / 0.00 | 0.006 | - (JRC nunca vio agua en el eje) | -0.008 vs -0.173 |
| G1 | Arroio 3 (sul) | 564.1 | 562 | 561 | 552 | 632 | 303.9 | ['Ribeirão', 'Ribeirão do Salto'] | ['Permanente'] | [] | 0.00 / 0.00 | 0.0 | - (JRC nunca vio agua en el eje) | -0.015 vs -0.117 |
| G2 | Arroio 1 (norte) | 32.7 | 2 | 8 | 155 | 10 | None | [] | ['Permanente'] | [] | 0.00 / 0.00 | 0.0 | - (JRC nunca vio agua en el eje) | 0.186 vs -0.102 |


Perenidad: la frecuencia de agua en el eje es un INDICIO (arroios de 1-3 m no resuelven en 10 m); la prueba es de campo en estacion seca. Ancho: ningun tramo fuera de la represa muestra agua abierta persistente > 10 m -> faixa de 30 m se mantiene.


## 7. Que cambia en el diagnostico (antes -> despues)

| Gleba | Item | Antes (resultados_glebas.json) | Despues (an_11) |
|---|---|---|---|
| G1 | APP exigible (30 m + nascente 50 m) | 11.96 | 11.96 (FBDS) / ensamble 13.58 / envolvente [11.96; 14.00] / CAR 12.44 |
| G2 | APP exigible (30 m + nascente 50 m) | 0.22 | 0.22 (FBDS) / ensamble 0.17 / envolvente [0.14; 0.22] / CAR 0.00 |
| G1 | Represa: espejo | 1.95 (FBDS) / 0.91 (MNDWI 29-ago) / 1.71 (JRC max) | 0.831 (mediana S2 lluviosa 2024-26); rango [0.0, 1.049]; CAR declara 2.12 |
| G1 | Nascentes | 1 FBDS + 2 candidatos DEM | FBDS 306158: probable; DEM_ dem_1: probable (misma cabecera que la nascente FBDS, no es una nascente adicional); DEM_ dem_2: poco probable (evidencia negativa: sin agua ni humedad, mas seco que el entorno en la seca) |
| G1 | Cursos (km dentro) | 2.038 | FBDS 2.038 / otto 2.043 / ANA 1.070 / ensamble 2.188 km |
| G1 | CAR | sin CAR propio identificado (vecino F127CD1E) | CAR PROPIO B3FC1E14: APP 12.44, RL averbada 2.45 (exigida 28.84), veg. nativa 3.80, consolidada 125.13 ha |


**Referencia recomendada para el informe: FBDS/IAT (RapidEye 5 m, 1:25.000).** La mediana del ensamble de 5 DEM de 30 m queda a 17 m (mediana) / 55 m (p90) del eje FBDS: la dispersion es del orden del pixel del DEM y menor que la incertidumbre que el propio buffer de 30 m absorbe; ningun DEM global mejora a una base trazada sobre imagen de 5 m, y el IAT publica FBDS como su capa institucional de APP hidrica. El ensamble sirve para la ENVOLVENTE de incertidumbre, no para reemplazar el eje. DEM mas cercano a FBDS: GLO30 (17 m).



Serie S1: Otsu sobre VV p50 en PROP+500 m cae en -11.5 dB con 58% del area por debajo: separa cultivo/bosque, NO agua (el agua es <1% del area y no forma modo). Se usan umbrales fijos -16/-18/-20 dB; -18 dB es el mas cercano al espejo S2/MapBiomas.


## 7b. Contexto regulatorio que aportan las capas de gobierno

- **Outorga SIGARH dentro de la propiedad**: empreendimento "Fazenda Santo Antônio", interferencia **Barragem/soleira** en Córrego Ribeirão do Salto (cuenca Tibagi, otto 864227451), portaria 26039/2023/OP-GOUT (Portaria de outorga prévia, Outorga prévia), finalidades "Regularização de nível,Acumulação", publicada 2023-11-09, vencimiento 2025-11-08 (**vencida: True**), **status IRREGULAR**; el punto esta a 15 m del espejo FBDS y a 26 m del arroio mas cercano. Es la outorga previa del barramento de la represa (Ribeirao do Salto = arroio 3): confirma que el reservatorio decorre de barramento de curso natural (art. 4 III) y que la regularizacion hidrica esta pendiente.
- **Manancial de abastecimento publico** (IAT mananciais 2023): "Rio Congonhas 2", tipo Ativo, impeditivo **Sim**, portaria 233/2018, abastece None, ICMS ecologico Sim -> 100% de la propiedad dentro.
- **Manancial de abastecimento publico** (IAT mananciais 2023): "Rio Congonhas 1", tipo Ativo, impeditivo **Analisar**, portaria 472/2018, abastece None, ICMS ecologico Sim -> 100% de la propiedad dentro.
- **Manancial de abastecimento publico** (IAT mananciais superficiais 2026): "Rio Congonhas (Uraí)", tipo Ativo, impeditivo **None**, portaria 233/2018, abastece Uraí, ICMS ecologico Sim -> 100% de la propiedad dentro.
- **Manancial de abastecimento publico** (IAT mananciais superficiais 2026): "Rio Congonhas (Cornélio Procópio)", tipo Ativo, impeditivo **None**, portaria 472/2018, abastece Cornélio Procópio, ICMS ecologico Sim -> 100% de la propiedad dentro.
- **Fragmento florestal prioritario IAT** 163519: 0.6 ha totales, idade 4 anos, prioridade A, tamanho A -> 0.09 ha dentro de la propiedad.
- **Fragmento florestal prioritario IAT** 163519: 3.8 ha totales, idade 4 anos, prioridade A, tamanho A -> 0.29 ha dentro de la propiedad.
- **Fragmento florestal prioritario IAT** 163756: 260.2 ha totales, idade 23 anos, prioridade A, tamanho A -> 7.07 ha dentro de la propiedad.

## 8. Lectura y recomendaciones para el informe

1. **El inmueble YA tiene CAR** (`PR-4124301-F127CD1E73FA4B9DB4FA0CC2B3FC1E14`, 143.34 ha, "Aguardando analise"): no es un vecino. Declara APP 12.44 ha (num_area 10.45), **Reserva Legal averbada de solo 2.45 ha contra 28.84 ha exigidas (20%)**, vegetacion nativa 3.80 ha contra 17.7 ha de floresta medida, area consolidada 125.13 ha y un reservatorio de 2.12 ha. El diagnostico debe pasar de "propuesta de CAR" a **retificacao del CAR existente** (RL insuficiente y vegetacion nativa subdeclarada), y G2 debe tratarse como desmembramento del CAR `PR-4124301-5223911747FD4B878118F1823D609DD6` (94 ha, ya notificado por el IAT).
2. **La referencia del leito sigue siendo FBDS/IAT**: los 5 DEM coinciden entre si a 38.4 m (mediana) y con FBDS a 8-29 m por arroio; ninguna base de gobierno (otto 1:50k, ANA 5k, BC250, CAR) mejora esa precision. La unica discrepancia sistematica esta en el **Arroio 1 (norte)**: la mediana del ensamble queda a 29.4 m (p90 55.4 m) del eje FBDS y todos los DEM la desplazan hacia el mismo lado, lo que sube la APP de ese arroio de 2.44 a 3.73 ha (G1 total 11.96 -> 13.58 ha). Recomendacion: levantar el eje del Arroio 1 con GNSS (RTK o L1/L5) antes de la retificacao del CAR; hasta entonces reportar APP G1 = 11.96 ha con envolvente [11.96; 14.00].
3. **Represa**: el espejo actual (2024-26) es de 0.83-1.23 ha segun sensor (S2 mediana lluviosa 0.83; S1 -18 dB 0.98; MapBiomas 2024 1.08), es decir la mitad del historico (FBDS 2013 1.95, WorldView-2 2012 1.93, CAR 2.12). Esta en la frontera de 1 ha: no se puede afirmar la dispensa del art. 4 par. 4. Recomendacion: medir el perimetro del espejo en campo (GNSS, estacion lluviosa, o cota del vertedero) y, mientras tanto, mantener el criterio conservador (>= 1 ha, sin dispensa) y la faixa de 30 m del arroio 3 bajo el espejo.
4. **Nascentes**: la nascente FBDS 306158 se confirma como probable (inicio de trecho otto a 20 m, 3/5 DEM, varzea en el mapeo IAT 2012, NDMI seco por encima del entorno); dem_1 es la misma cabecera 97 m aguas arriba (no suma APP nueva; el circulo de 50 m debe centrarse donde aflore el agua en campo); dem_2 (en soja) queda como POCO PROBABLE: sin agua en 338 escenas S2 ni 43 S1, sin base oficial, y mas seco que su entorno en la seca (z = -3.55). El riesgo de 3.89 ha del talvegue se mantiene solo como aviso topografico para la visita en estacion lluviosa.
5. **Cursos**: longitudes por fuente dentro de G1 coinciden con FBDS (otto 2.043 km, enquadramento igual; ANA 5k y BC250 solo cubren los arroios 1 y 3, que BC250 clasifica como Permanente; el arroio 3 es el Ribeirao do Salto, clase 2). Ningun tramo muestra agua abierta persistente > 10 m fuera de la represa: la faixa de 30 m se mantiene. La frecuencia de agua en los ejes es ~0 en S2/S1 (cauces de 1-3 m bajo dosel no resuelven a 10 m): la perenidad NO se puede probar por satelite; el unico indicio positivo es el NDMI seco mas alto en el eje que en el entorno ({'Arroio 1 (norte)': '0.101 vs -0.176', 'Arroio 2 (central)': '-0.008 vs -0.173', 'Arroio 3 (sul)': '-0.015 vs -0.117'}).
6. **Contexto regulatorio nuevo** (seccion 7b): (i) la represa tiene una outorga PREVIA de barragem en SIGARH con status IRREGULAR y vencida (2025-11-08): el informe debe recomendar regularizar la outorga (o su renovacion) junto con el CAR; (ii) el 100% de la propiedad esta dentro del manancial de abastecimento publico "Rio Congonhas" (impeditivo Sim, portaria 233/2018): toda intervencion en APP/RL y el propio barramento se licencian bajo ese regimen; (iii) el fragmento IAT 163756 (prioridade A, 23 anos) toca la propiedad en 7.07 ha: es el corredor natural para la RL. Curvas de nivel 1:50k: sesgo vertical de los DEM +5 a +7 m, MAD 4-5 m, sin consecuencia para el trazado.