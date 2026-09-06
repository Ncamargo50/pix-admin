# AUDITORIA RESUMEN PRO — estado de todos los hallazgos en la VERSION 3

Fecha: 2026-09-06. Consolida `AUDITORIA_ANALISIS.md` (tecnica, an_00..an_03), `AUDITORIA_LEGAL_PRO.md` (juridica, PDF v2), `AUDITORIA_INFORME_V2.md` (informe v2) y `COMPARACION_FUENTES_GOBIERNO.md` (hidrologia PRO, an_11).
Entregables v3: `Diagnostico_APP_RL_Fazenda_Santo_Antonio_v3_PT.pdf` (21 pag.) y `_v3_ES.pdf` (22 pag.), `03_MAPAS_V3/W01..W07` (PT + ES), `04_VETORES_ENTREGA_V3/`, `02_ANALISIS/resultados_v3.json`.
Codigo v3: `an_12_glebas_v3.py` (cifras), `an_13_mapas_v3.py` (mapas), `textos_v3.py` + `an_14_informe_v3.py` (PDF + verificacion fitz), `an_15_exportar_v3.py` (vectores).

Estados: **CORREGIDO** = resuelto en la v3 · **ACEPTADO CON NOTA** = no se puede resolver por satelite/escritorio, el PDF lo declara · **PENDIENTE DE CAMPO** = exige campo, escritura u organo.
"PDF" = seccion y pagina de la version PT (la ES tiene una pagina mas por longitud del texto: p. +1 a partir de la seccion 2).

## 1. Hipotesis juridica principal (cambia el veredicto)

| Id | Origen | Hallazgo | Estado | Donde quedo en la v3 |
|---|---|---|---|---|
| L-H1 | Legal | Hipotesis "glebas separadas" invierte el defecto legal: areas contiguas del mismo dueno = un CAR (IN MMA 2/2014 art. 32; Lei 8.629 art. 4 I; Manual INCRA 1.1) | **CORREGIDO** | Ficha p.1 ("Cenario principal: IMOVEL UNICO"); Resposta direta p.3-4; sec. 1 p.4; sec. 6 p.15; W04/W07. `resultados_v3.json._meta.hipotese_principal` |
| L-H2 / I-B1 | Legal + Informe | G2 aislada seria 0,68 MF (art. 67, 61-A §1, 61-B) y el PDF v2 aplicaba 20 % sin decirlo | **CORREGIDO** (reformulado) | Tabla de 3 escenarios p.4 y sec. 6 p.15: (A) imovel unico principal; (B) desmembrada de imovel > 4 MF → art. 12 §1 (CAR de origen 94,13 ha = 4,78 MF); (C) art. 67 solo como excepcion a probar con la matricula de origen. Ficha: MF 7,89 / 7,21 (2008) / 0,68 (G2 aislada) |
| L-H3 | Legal | "Se nao pertencer, os 2,71 ha ficam integralmente a recompor" era falso en ambos escenarios | **CORREGIDO** | Sustituido por la tabla de escenarios con aritmetica (p.4): A → deficit del imovel 13,85; B → 2,71 propios via art. 66; C → 0 |
| G2-TL | Cliente | G2 comprada como terra limpa, sem monte: tomar como hecho | **CORREGIDO** | Vegetacao computavel = solo G1 (17,70); G2 aporta 0; `gleba2_cenarios.A_imovel_unico_principal.aporte_vegetacao_g2_ha = 0` |
| I-M1 | Informe | "NAO CONFORME por 0,03 ha" en G2: 0,03 ha = 3 pixeles, indistinguible | **CORREGIDO** | Ya no hay cuota de RL por gleba; la floresta de la ponta norte no se computa; APP G2 con envolvente [0,14; 0,22] (p.4 nota, sec. 4 tabla p.10) |
| I-M2 | Informe | "mata do vizinho, floresta desde 1985" afirmado como hecho | **CORREGIDO** | Frase eliminada del PDF y mapas (verificador falla si aparece). Redaccion: "continua com o fragmento 2 (IAT prioridade A); MapBiomas: floresta em 1985/2008 (indicio a 30 m)" (sec. 3 tabla vegetacao p.8; W01) |
| G2-LIM | Informe/legal | La ponta norte del poligono cae sobre 2,68 ha de floresta que el cliente dice no haber comprado | **PENDIENTE DE CAMPO/ESCRITURA** (declarado) | Callout "Limite da Gleba 2 a conferir com a escritura/SIGEF" p.15 con coordenadas N 7.403.860-7.404.071; W07 hachurado; paso 1 de sec. 9; capa `v3_G2_ponta_norte` |

## 2. CAR existente (hallazgo de hidrologia PRO)

| Id | Origen | Hallazgo | Estado | Donde quedo |
|---|---|---|---|---|
| HP-1 | Hidro PRO | El "vecino con reservatorio de 2,28 ha dentro" (T-#6, L-H16, I-m5) era el CAR PROPIO PR-4124301-F127CD1E... (143,34 ha, "Aguardando analise", matricula 8.334) | **CORREGIDO** | Aviso corregido explicitamente en sec. 2 p.5; ficha p.1; tabla declarado vs medido p.5; W06 p.6; capa `v3_CAR_existente` |
| HP-1b | Hidro PRO | CAR declara APP 12,44 / RL averbada 2,45 / veg. nativa 3,80 / consolidada 125,13 / reservatorio 2,12 + 0,15 | **CORREGIDO** (subsidio a retificacao) | Tabla p.5 (10 filas) + lista "Retificacao proposta" p.6; KPI "2,45 RL averbada" p.3 |
| HP-1c | Hidro PRO | G2 esta dentro del CAR de origen PR-4124301-5223911747... (94,13 ha = 4,78 MF, notificado; matricula 1168) → desmembramento | **CORREGIDO** | Ficha p.1; escenario B p.4; sec. 6 p.15; W07 (contorno magenta) |
| HP-1d | Hidro PRO | Municipio del CAR = Santo Antonio do Paraiso (4124301) vs centroide en Sao Sebastiao da Amoreira (4126009); MF declarado 7,29 | **ACEPTADO CON NOTA** | Ficha p.1 (fila Municipio y Modulo fiscal); tabla p.5; sec. 8 incertezas p.19: banda 4-10 MF no cambia; conferir matricula/CCIR |
| L-H7 / I-m5 | Legal + Informe | El escenario PRA-PR (1,63 ha) depende de CAR hasta 31/12/2023 y adesao en 1 ano (art. 59 §2); plazos vencidos sin prorroga localizada; fecha de inscripcion desconocida | **ACEPTADO CON NOTA** (dato no publicado en la replica IAT) | Ficha p.1; sec. 1 p.4 (art. 29 §4, 59 §2, "ambos os prazos ja venceram; nao se localizou prorrogacao"); tabla p.5 fila "Data de inscricao"; paso 4 de sec. 9 |
| L-H16 | Legal | Sobreposicion entre CAR deja la inscripcion "pendente" (Boletim IAT 09/2024) | **CORREGIDO** | Sec. 2 p.6 ultimo item de retificacao; solape 1,89 ha entre los dos CAR en p.5 |

## 3. Reserva Legal

| Id | Origen | Hallazgo | Estado | Donde quedo |
|---|---|---|---|---|
| I-B2 / T-#4 | Informe + Tecnica | Variante conservadora de RL ausente: 10,46 ha del fragmento 13 sin historial 2008/2013 y fuera del consenso del RF (9,94 de 20,42 ha sin exactitud medida) | **CORREGIDO** | Principal 17,70 → deficit 13,85; conservadora 7,24 [5,53; 8,95] → deficit 24,31, en KPI p.3, tabla p.4, sec. 5 tabla p.12-13, W04 leyenda. `reserva_legal.variante_conservadora` |
| I-M6 | Informe | "RL existente" → debe ser "vegetacao nativa computavel" (arts. 14, 18) | **CORREGIDO** | Termino sustituido en todo el PDF, mapas y capas (`v3_vegetacao_computavel`); sec. 5 p.12 lo define; verificador falla si aparece "RL existente" |
| L-H6 | Legal | APP a recompor incluida en la RL proposta solo computa despues de "em processo de recuperacao" (art. 15 II) | **CORREGIDO** | Sec. 5 p.13 (localizacao proposta); W04 nota; capa `v3_RL_proposta.status` |
| L-3.7 | Legal | La RL depende en 10,46 ha del fragmento 13; declararlo como RL/regeneracao lo consolida como intocable; si es plantio no computa | **CORREGIDO** | Sec. 5 nota p.13 |
| RL-LOC | v3 | RL proposta recortada a G1 = 28,57 ha; faltan 2,98 para 31,55; fragmento IAT prioridade A 163756 (7,07 ha dentro, 23 anos) como ancla | **CORREGIDO** | Sec. 5 p.13; W04 (linea punteada magenta); capa `v3_IAT_fragmento_prioritario` |
| T-#2 | Tecnica | RL proposta v1 no contigua, con eucalipto, 17 partes | **CORREGIDO en v2** (5 blocos, sin silvicultura ni agua) y mantenido | Sec. 5 p.13; `an_03` (blocos [23,63; 3,17; 3,02; 1,05; 0,72]) |
| L-H15 | Legal | Compensacion en el mismo bioma (STF ED: no "identidade ecologica") | **CORREGIDO** | Sec. 1 p.4 y sec. 5 p.13 (art. 66 III, IN IAT 53/2025); Anexo A |

## 4. APP / hidrografia

| Id | Origen | Hallazgo | Estado | Donde quedo |
|---|---|---|---|---|
| I-M5 | Informe | Envolvente [min; max] solo en p.13 del v2 y solo para el imovel; frase de alcance completa ausente en la ficha | **CORREGIDO** | Envolventes en KPI p.3, tabla p.3, sec. 4 tabla p.10 (fila "Envolvente [min; max]"), sec. 5 tabla p.12; frase de alcance completa en la ficha p.1 y en sec. 8 |
| HP-2 | Hidro PRO | Ensamble de 5 DEM: Arroio 1 con desvio sistematico de 29 m (p90 55) → APP G1 [11,96; 14,00]; referencia sigue siendo FBDS | **CORREGIDO** | Sec. 4 intro p.10; W02/W03 (linea cian); `app.G1.por_arroio`; capa `v3_APP_envolvente` y `v3_arroio1_ensamble_DEM` |
| GNSS | Hidro PRO | Levantar el eje del Arroio 1 con GNSS antes de retificar | **PENDIENTE DE CAMPO** (declarado) | Paso 2 de sec. 9 p.19-20 |
| L-H4 / I-m4 | Legal + Informe | Faixa del reservatorio: no hay faixa por defecto; IN IAT 64/2025 no aplica; "+1,44" era delta de recompor, "+1,66" de exigida | **CORREGIDO** | Sec. 4 nota p.11 ("sem faixa legal por defeito (art. 4 III)... sensibilidade 30 m segue o criterio FBDS: +1,66 exigiveis, +1,44 a recompor"); IN IAT 64 eliminada del PDF y del Anexo A (verificador) |
| HP-3 | Hidro PRO | Represa: espejo actual 0,83-1,23 ha vs historico 1,95 (FBDS) / 1,93 (WV2) / 2,12 (CAR): >= 1 ha INDETERMINADO | **ACEPTADO CON NOTA** + **PENDIENTE DE CAMPO** (perimetro GNSS / cota vertedero) | Tabla por fuente sec. 3 p.8 (12 fuentes); texto "sem presumir a dispensa"; W02; capa `v3_represa_espelhos`; paso 2 de sec. 9 |
| T-#3 / T-#8 | Tecnica | Dispensa art. 4 §4 afirmada en v1 | **CORREGIDO en v2** y mantenido ("nao se presume") | Sec. 1 p.4; sec. 3 p.8; verificador exige que "dispensa" aparezca solo negada |
| HP-6i | Hidro PRO | Outorga SIGARH de la barragem: previa, IRREGULAR, vencida 08/11/2025 | **CORREGIDO** (contexto) + **PENDIENTE DE ORGANO** | Tabla p.3 ("REGULARIZAR"); sec. 3 p.8; paso 3 de sec. 9; W02 (estrella); capa `v3_outorga_sigarh` |
| HP-6ii | Hidro PRO | 100 % del imovel en el manancial Rio Congonhas (Portaria 233/2018, impeditivo) | **CORREGIDO** (contexto) | Ficha p.1; sec. 1 p.4; paso 3 de sec. 9 |
| HP-4 | Hidro PRO | Nascente FBDS 306158 PROBABLE; dem_1 misma cabecera; dem_2 POCO PROBABLE (0 agua en 338 S2 + 43 S1, NDMI z -3,55) | **CORREGIDO** | Tabla de nascentes sec. 3 p.7 con coordenadas UTM; dem_2 sale de los avisos de riesgo (nota topografica); W02; capa `v3_nascentes` |
| T-#5 | Tecnica | dem_2 no es nascente; talvegue de 700 m como riesgo | **CORREGIDO** (rebajado con evidencia negativa) | Sec. 3 p.7 ("ate 3,89 ha SO se houver curso em campo") |
| HP-1e | Hidro PRO | 2.o reservatorio declarado en el CAR (0,15 ha) en la cabecera del Arroio 2, sin agua 2024-26 | **PENDIENTE DE CAMPO** (declarado) | Tabla p.5; W02/W06; paso 2 de sec. 9 |
| I-M4 / T-#12 | Informe + Tecnica | "Perene" del SICAR y "Permanente" del BC250 no son evidencia de perenidad | **CORREGIDO** | Sec. 3 tabla de cursos p.7 ("atributo que nao discrimina regime"); sec. 7 intro p.16 y W05 nota ("perene = nomenclatura SICAR obrigatoria; perenidade NAO verificada") |
| HP-5 | Hidro PRO | Longitudes por fuente (FBDS 2,038 / otto 2,043 / ANA 1,070 / BC250 1,153 / DEM 2,188 km); ancho <= 10 m confirmado | **CORREGIDO** | Sec. 3 tabla p.7 (523 / 951 / 564 m + 33 m en G2); nombre "Ribeirao do Salto" |
| L-H5 | Legal | "Supressao pos-2008 confirmada... cabe no art. 61-A" sobreafirmado | **CORREGIDO** | Sec. 4 nota p.11: "indicio de 0,04 ha (MapBiomas 30 m; Hansen 0), a validar; o restante e ELEGIVEL ao regime de area consolidada, sujeito a comprovacao e a validacao do IAT" |
| I-M3 / T-#7 | Informe + Tecnica | 0,05 era cifra del imovel; APP G1 = 0,04; G2 tiene 0,53 de indicio | **CORREGIDO** | Sec. 3 tabla vegetacao p.8 (0,04 APP G1 / 0,53 G2); sec. 6 p.15 |
| L-H14 / I-m10 | Legal + Informe | STF ADI 4903: formula exacta ("interpretacao conforme") y ED con transito em julgado 21/02/2025 | **CORREGIDO** | Sec. 1 p.4; Anexo A |
| L-H11 | Legal | FBDS es base privada "disponibilizada pelo IAT", no determinacion oficial | **CORREGIDO** | Ficha p.1, sec. 4 p.10, sec. 8 p.18, notas de los mapas |

## 5. Vegetacion / clasificacion

| Id | Origen | Hallazgo | Estado | Donde quedo |
|---|---|---|---|---|
| T-#1 | Tecnica | Aviso con "194,53 ha" para el fragmento 13 | **CORREGIDO en v2** y verificado en v3 (la cadena "194,53" no puede aparecer) | Verificador an_14 |
| T-#9 | Tecnica | Fragmento 13: arboreo por SWIR + DW, no solo por la serie NDVI; nucleo/borda; 1,22 ha con p < 0,5 | **CORREGIDO** | Sec. 3 tabla p.8 ("indicio por serie NDVI, SWIR B11 0,161 vs pastagem 0,250 e textura; sem historico 2008/2013; estagio e idade a confirmar (CONAMA 2/1994)"); W01 hachurado |
| I-m9 | Informe | Fragmento 30 no mencionado | **CORREGIDO** | Sec. 3 tabla p.8 (0,73 ha, sem historico); W01 |
| T-#4 | Tecnica | OA 0,976 medida solo sobre consenso; 9,94 ha sin exactitud | **CORREGIDO** | Sec. 3 intro p.7; sec. 8 p.18; incertezas p.19 |
| EST | Todas | Estagio sucessional no se determina por satelite | **PENDIENTE DE CAMPO** (declarado) | Paso 5 de sec. 9 (inventario CONAMA 2/1994) |
| I-B2 env | Informe | Envolvente +-1 px de la floresta por gleba | **CORREGIDO** | 17,70 [14,48; 20,92] y conservadora [5,53; 8,95] (perimetro x 10 m / 2, incluye la borda con el limite: conservador) en sec. 5 tabla p.12 |

## 6. Redaccion, terminologia, mapas, exportacion

| Id | Origen | Hallazgo | Estado | Donde quedo |
|---|---|---|---|---|
| L-H9 / I-m1 | Legal + Informe | "Dictame", "Director" en PT; tagline | **CORREGIDO** | "Parecer tecnico preliminar", "Diretor Tecnico"; el verificador rechaza "Dictame" (tambien "dictamen" en ES). La tagline del pie ("Agricultura de Precision") se mantiene como marca (pix_branding) |
| I-m2 | Informe | Lusismos en ES (leito, floresta, nascente, laudo) | **CORREGIDO** | ES: cauce, bosque, naciente, informe pericial; "nascente" solo entre comillas como termino legal y en la nomenclatura SICAR (nota en sec. 7); verificador de lusismos e hispanismos (PT sin "sesgo/ensamble") |
| L-H13 | Legal | "Conforme" es resultado de la analise del IAT | **CORREGIDO** | Definido en Resposta direta p.3 y `app.conforme_definicao`: "APP com vegetacao nativa segundo a classificacao RF 10 m... nao e a conformidade da analise do IAT" |
| L-H12 | Legal | "Pronta para o SICAR" y "classes da IN" | **CORREGIDO** | Sec. 7 p.16: "nomenclatura do Modulo de Cadastro do SICAR (Manual SFB)... camada preparada no formato do SICAR, a ser conferida pelo responsavel pela inscricao" |
| I-m3 | Informe | Sumas de redondeos (144,20 / 157,74 / 12,27 vs 12,28) | **CORREGIDO** | Sumas sobre 3 decimales (`_verificacao` de an_12: 14 items OK); nota en sec. 7 p.16 y W05; tabla p.17 cierra en 144,21 / 13,54 / 157,75 |
| I-m5 | Informe | Coordenadas de nascente y candidatos; matricula/CAR | **CORREGIDO** | Sec. 3 tabla p.7 (UTM 22S); ficha p.1 |
| I-m6 | Informe | V04 verdes iguales (corredor vs APP vegetada); rotulo APP fuera de G2 en V06 | **CORREGIDO** | W04: corredor naranja hachurado, APP vegetada verde medio, fragmento 13 hachurado blanco, IAT magenta punteado; W07: rotulos con linea guia dentro de G2 |
| I-m7 | Informe | Proximos pasos sin orden | **CORREGIDO** | Sec. 9 p.19-20: 1 escritura/matriculas, 2 GNSS (arroio 1, represa, nascente), 3 outorga, 4 retificar CAR/PRA, 5 inventario florestal, 6 plano de recomposicao/compensacao |
| I-m8 | Informe | "CONFORME" de G2 con 22 pixeles | **CORREGIDO** | Sec. 4 tabla p.10: "CONFORME (na cena; limite a conferir)" + envolvente [0,14; 0,22] |
| L-H8 / L-H10 / L-H17 | Legal | Citar IN MMA 2/2014 art. 32 y art. 67 en anexo; clase MF correcta; MF por tabla INCRA/CCIR | **CORREGIDO** | Sec. 1 p.4; ficha p.1 ("media propriedade (4-15 MF)... banda 4-10 MF"; "conferir no CCIR"); Anexo A p.20 |
| T-#10 | Tecnica | Log no correspondia a la corrida | **ACEPTADO CON NOTA** | an_12 imprime la verificacion en la misma corrida que escribe el JSON (`_verificacao`); los logs de an_11 (`hidrologia_pro/log_hidrologia_pro.txt`) y de an_12 (stdout) son de la misma fecha |
| T-#11 | Tecnica | Brecha de 2,2 m entre poligonos | **ACEPTADO CON NOTA** + **PENDIENTE** (snap antes de inscribir) | Ficha p.1 y sec. 8 p.18 ("estrada de 2,2 m"; IN MMA 2/2014 art. 32: no rompe la continuidad) |
| T-#13 / T-#14 / T-#15 | Tecnica | Logica de `dispensa_ambigua`; frases internas; nombre de `app_a_recompor_incluida` | **ACEPTADO CON NOTA** (v2/v3 usan banda +- incertidumbre y "nao se presume"; documentos internos, no llegan al cliente) | `resultados_analisis.json` (an_03 v2); an_12 recalcula `app_a_recompor_incluida_g1_ha` desde la geometria |
| DOI | Informe | Referencias verificadas | **CORREGIDO** | Anexo A p.20-21: 15 DOIs de la lista Crossref de METODOLOGIA §7 |

## 7. Lo que sigue PENDIENTE (no resoluble desde escritorio)

1. Escritura/SIGEF de la Gleba 2 (limite de la ponta norte) y matricula de origen 1168 con la situacion en 22/07/2008 (decide A/B/C); CCIR (MF) y recibo del CAR (fecha de inscripcion → PRA-PR).
2. GNSS: eje/borda de la calha del Arroio 1 (desvio 29 m; APP entre 11,96 y 14,00 ha), Arroios 2 y 3, perimetro del espejo de la represa en estacion lluviosa (criterio de 1 ha) y nascente 306158 (perenidad; 2.o reservatorio de 0,15 ha).
3. Outorga de la barragem (26039/2023/OP-GOUT, previa, irregular, vencida) ante IAT/SIGARH, regimen del manancial Rio Congonhas.
4. Retificacion del CAR PR-4124301-F127CD1E... (RL 2,45 → 31,55; vegetacao 3,80 → 17,70; APP; inclusion de G2; sobreposicion con el CAR de origen).
5. Inventario forestal de los fragmentos 13 y 2 (CONAMA 2/1994): fija el deficit entre 13,85 y 24,31 ha.
6. PRADA de la APP (2,92 / 1,63 / +1,44 ha) y plan de RL (corredor 8,55 + 2,98 ha a localizar o compensacion).

## 8. Verificacion automatica (an_14, PyMuPDF)

- KPIs presentes en ambos PDF: 12,18 · 11,96 · 14,00 · 2,92 · 1,63 · 31,55 · 17,70 · 7,24 · 13,85 · 24,31 · 2,71 · 2,45 · 143,34 · 0,83 · 1,23 · 157,75 · 2,04 · 523 · 951 · 564 · 0,976 (+ envolventes, RL proposta, espejos, outorga).
- Ausentes: "Dictame"/"dictame", "RL existente", "mata do vizinho"/"monte del vecino", "194,53", "+1,00 ha", "IN IAT 64"; "dispensa" solo negada.
- Sin glifos fuera de WinAnsi; PT sin "-cao" sin tilde ni "sesgo/ensamble/Director"; ES sin "-cion/-sion" sin tilde ni "leito/floresta/laudo/nascente/talvegue" (salvo nomenclatura oficial y "Floresta Estacional").
- Paginas: PT 21, ES 22 (rango 16-22). Resultado: **OK** en ambos.
- Sumas (an_12 `_verificacao`, 14 items, tolerancia 0,011 ha): todas OK (144,212 + 13,538 = 157,750; 28,842 + 2,708 = 31,550; 31,55 − 17,70 = 13,85; 17,70 − 10,46 = 7,24; 31,55 − 7,24 = 24,31; 11,96 + 0,22 = 12,18; 7,887 + 1,157 + 2,916 = 11,960; 28,57 + 2,98 = 31,55; 11,96 + 1,66 = 13,62).
