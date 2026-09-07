# Largura da calha do leito regular — métodos alternativos (Fazenda Santo Antônio, PR)

Script: `MATA_CILIAR_SANTO_ANTONIO/ortho_07_cauce_alternativo.py` · Saídas: `05_ORTOFOTO/cauce/` (`cauce_medicoes.geojson`, `cauce_resumo.json`, `cauce_recortes/*.png`, `_check_ortho_07.png`, `log_ortho_07.txt`). Data do voo: 22-mai-2026 (ortofoto 5 cm, DSM/DTM 5 cm ODM). CRS: EPSG:31982 (≡ 32722, dx = 0,0 m).

**Pergunta legal.** Lei 12.651/2012, art. 4º I: APP de 30 m para curso d'água com **menos de 10 m de largura**, medida **da borda da calha do leito regular** (art. 3º XIX: leito regular = calha por onde correm regularmente as águas do curso durante o ano). Não é a lâmina do dia nem a planície de cheia.

**Por que métodos alternativos.** Sob dossel fechado o "DTM" fotogramétrico do drone é a envolvente inferior da copa (ortho_01: `dtm_fonte = 2`). As seções sobre o DTM (ortho_03) falharam: Arroio 1 = 3 de 26 seções com solo, Arroio 2 = 0 de 56, Arroio 3 sem DSM/DTM (o modelo termina em N 7401711).

## Resultado consolidado (2026-09-06)

| Arroio | M1 claros (n / espelho / calha) | M2 solo visível DSM−DTM (n bosque) | M3 estimativa W na saída [intervalo] | M4 oficial | Faixa consolidada | Conclusão |
|---|---|---|---|---|---|---|
| 1 (norte), talweg 513 m | **0** componentes (dossel contínuo) | **0** (7 seções válidas, todas na borda campo-floresta, 26-35 % arbóreo: excluídas; 39 estações a < 20 m da borda da huella: descartadas) | A = 6,8 (local) a 9,2 km² (otto ajustada) → **5,9 m [3,1-10,2]** | FBDS 0-10 m; BC250 `larguramedia` = None, regime Permanente | 3,1-10,2 m | ≤ 10 m **provável, não confirmado por medição** → M5 |
| 2 (central), talweg 1110 m | **0** (dossel 100 %) | **0** candidatas | A = 0,21 (nascente) a 0,76 km² → **2,5 m [1,4-4,3]** | FBDS 0-10 m; BC250 None, Permanente | 1,4-4,3 m | ≤ 10 m **provável** (M3 suporta com folga) → M5 |
| 3 (sul), eixo FBDS 564 m | 3 componentes, **todos no vertedouro/saída da represa** (artificial, excluídos) | sem DTM | A = 8,3 a 12,3 km² → **6,5 m [3,4-11,3]** | FBDS 0-10 m; BC250 "Ribeirão do Salto", `larguramedia` None, Permanente | 3,4-11,3 m | ≤ 10 m **provável, não confirmado** → M5 |

Nenhuma medição direta válida deu ≥ 10 m. Pontos ≥ 10 m **excluídos** (não são o arroio): Arroio 1, seções M2 em x 534950-534954 / y 7403964-7403969 (11-18 m, artefato de borda da huella do DTM, a < 20 m do limite, corrida 1); Arroio 3, `calha_veg` 10-20 m em x ≈ 535126 / y 7401692-7401756 (trilhas em estrada de terra roxa, corrida 1, eliminadas com `ExG_min`/`BR_min`).

**Que método trouxe dado e qual não.** M1 e M2 **não** trouxeram medição da calha natural em nenhum arroio: o dossel ripário é contínuo nos três, e os únicos claros com água/solo são artificiais (vertedouro da represa) ou de borda (terraço campo-floresta). M3 e M4 trouxeram os números; ambos são **estimativa/classe**, não medição. O número administrativo fecha só com **M5**.

## M1 — claros do dossel na ortofoto 5 cm

Estações a cada 2 m ao longo do eixo (talweg DTM de ortho_03 nos arroios 1-2; eixo FBDS no 3, corredor ±50 m porque a distância FBDS-talweg tem p90 = 44 m). Leitura por janelas do `odm_orthophoto.tif` (blocos de 25 estações, corredor ±40/50 m + 4 m; nunca `read()` completo). Feições de ortho_02 a 5 cm: L, ExG, S, BR = (B−R)/(B+R), TEX = desvio-padrão local de L em 21 px (1,05 m).

Máscara água/leito úmido: `L < 150 & −25 < ExG < 8 & TEX < 5 & −0,20 < BR < 0,06 & S < 0,5`, abertura/fechamento 2 it., área ≥ 0,5 m², componente com eixo maior ≥ 3 m. Largura do espelho = 2 × EDT sobre o esqueleto (mediana, p90, máx). Calha por vegetação (`calha_veg`): perfil perpendicular ao componente, do bordo da água para fora até ExG(1 m) > 20 ou TEX > 12 (vegetação), máx. 20 m. Qualidade: alta = alinhado ao eixo (|cos| ≥ 0,7), ≥ 5 m, DSM plano (σ < 0,15 m em 2 m); média = ≥ 3 m; baixa (descartada) = DSM rugoso. Componentes a < 60 m da represa = vertedouro (artificial, excluídos).

Calibração medida nesta obra: água real (represa/reservatório/poça do vertedouro) tem L 70-130, ExG −2 a −8, BR −0,10 a +0,02; sombra é azulada (BR > 0); **solo vermelho exposto (Terra Roxa) tem ExG −40 a −57 e BR −0,26 a −0,29** e passou como "água" nas trilhas de uma estrada na 1ª corrida (16 componentes, calha_veg 6-20 m) — por isso `ExG_min = −25` e `BR_min = −0,20`.

Limites: só mede onde há claro; a lâmina do dia (22-mai, fim do outono) é cota inferior da calha; `calha_veg` é o limite herbáceo/arbustivo, não necessariamente a ruptura de declive; um espelho de 0,5 m sob dossel a 5 cm é invisível. Resultado: 0 medições naturais em 2.187 m de eixo (1.096 estações).

## M2 — solo visível segundo DSM−DTM

Nas estações onde `dtm_fonte = 1` (solo) em ±3 m e CHM híbrido 0,25 m < 0,5 m, perfil ±15 m a 5 cm lido por janela do `dtm.tif` original (filtro de mediana 5 px). Regra de ortho_03: fundo = mínimo em ±8 m; margem a fundo + h (h = 0,5 e 1,0 m: primeiro cruzamento caminhando do fundo para fora); ruptura de declive (subiu ≥ 20 % e caiu < 10 % em 1 m com ≥ 0,3 m acima do fundo). Exigências novas, aprendidas na 1ª corrida: **mínimo local transversal** (ambos os lados sobem ≥ 0,30 m em 8 m), **≥ 20 m da borda da huella do DTM/ortofoto** (as "seções válidas" de 11-18 m no Arroio 1 eram artefato de borda em x ≈ 534950) e **classe de cobertura do perfil**: ≥ 50 % arbóreo = bosque (conta); 20-50 % = borda campo-floresta (o talweg de ortho_03 sob dossel desvia-se para o campo cosechado e a seção mede o terraço, não o arroio); < 20 % = campo. Só bosque entra na estatística legal.

Resultado: Arroio 1 = 7 seções válidas (s 86-96 e 142 m, x 534641-534688), todas borda (h0,5 mediana 5,6 m, excluídas); Arroio 2 = 0 candidatas; Arroio 3 = sem DTM. O DTM original está sem a correção vertical de ortho_01 (z 603-610 m vs 629-728 m no produto corrigido): larguras são relativas ao fundo, independentes do datum.

## M3 — geometria hidráulica regional (ESTIMATIVA, não medição)

W_bankfull = a·A^b, A em km². Cinco pontos por arroio (cabeceira/entrada, ¼, ½, ¾, saída do imóvel). A: máximo da `ACUMULACION_ha_30m` (ensamble 5 DEM, AOI = imóvel + 3 km, portanto **truncada** para bacias maiores) em raio de 45 m; na saída, conservador = max(local, otto IAT 2020 `nuareamont` do trecho descontada pro-rata a contribuição própria `nuareacont` a jusante da saída). Medido: no Arroio 2 a janela de 45 m capturou o Arroio 1 na confluência (5,7 vs 0,87 km²) — descartada quando local > 1,5 × otto. Áreas: A1 6,4-9,2 km² (otto 10,2 no fim do trecho a 1,16 km; ANA 5k 17,6 a 1,8 km); A2 0,21-0,76 km² (otto 0,867, cabeceira Strahler 1); A3 8,3-12,3 km² (otto/ANA 13,1 a 0,76 km).

Curvas usadas (VERIFICADAS):
- **Bieger, K.; Rathjens, H.; Allen, P.M.; Arnold, J.G. (2015).** Development and evaluation of bankfull hydraulic geometry relationships for the physiographic regions of the United States. *JAWRA* 51(3): 842-858. DOI 10.1111/jawr.12282. Tabela 3, modelo nacional (n = 1.279): **W = 2,70·A^0,352** (R² 0,66, SEE 0,24 log10 → fator 1,74 ≈ −43 % / +74 %); D = 0,30·A^0,213; Appalachian Highlands (úmido, florestal, n = 377): W = 3,12·A^0,415 (R² 0,87, SEE 0,12), dado como analogia climática superior.
- **Fernandez, O.V.Q. (2004).** Relações da geometria hidráulica em nível de margens plenas nos córregos de Marechal Cândido Rondon, oeste do Paraná. *Geosul* 19(37). Sem DOI (PDF verificado em periodicos.ufsc.br). 8 seções em córregos de 2ª ordem, **A 1,1-9,7 km² → W_mp medida 3,06-8,48 m** (R² W×A = 0,11: não é curva, é **envolvente regional empírica**; mesmo domínio basalto/Latossolo do norte-oeste do PR). Todas < 10 m para áreas comparáveis às dos arroios 1 e 3.

Referências verificadas mas NÃO aplicadas (motivo no `cauce_resumo.json → parametros.M3_no_aplicadas`): Moody & Troutman 2002 (DOI 10.1002/esp.403; W = 7,2·Q^0,5 exige vazão); Grison & Kobiyama 2011 (DOI 10.21168/rbrh.v16n2.p111-131; Q de margens plenas Tr 1,58 a vs área para 448 estações do PR, sem equação de largura no resumo); Wilkerson et al. 2014 (DOI 10.1002/2013WR013916; expoente 0,22-0,38 por ecorregião, coeficientes não extraídos); Andrews 1984 (DOI 10.1130/0016-7606(1984)95<371:BEAHGO>2.0.CO;2; rios de cascalho do Colorado). "Curvas de la geometría hidráulica regional para ríos del estado de Paraná" (Fernandez, ResearchGate): A 969-12.124 km², fora de faixa e texto não acessível → **NÃO VERIFICADO**.

Leitura: o valor central fica em 2,5-6,5 m nos três arroios; o teto do intervalo (fator 1,74) toca 10,2 m (A1) e 11,3 m (A3) → M3 é **compatível** com ≤ 10 m, não o **demonstra**; para o Arroio 2 (≤ 0,8 km²) o teto é 4,3 m e M3 **suporta**. Categoria por arroio no JSON (`M3.categoria`).

## M4 — atributos oficiais

- IBGE BC250 (2025) `trecho_drenagem`: os 3 trechos que cruzam o imóvel têm `larguramedia = None` ("não informado"), `regime = Permanente`, `tipotrechodrenagem = Curso d'água`, `encoberto = Não`; o do Arroio 3 chama-se "Ribeirão do Salto". Sem número de largura.
- IAT/FBDS `rios_ate10m` (1:25.000, RapidEye 5 m, 2013): ids 647524 (A1), 647525 (A2), 617192 + 647547 (A3), classe **"curso d'água (0-10 m)"** — é a base que o próprio IAT usa para APP; classe, não medição.
- ANA BHO 2017 5k e otto IAT 2020: **nenhum atributo de largura** (só `nuareamont`, `nucomptrec`, Strahler); usados em M3.
- CAR (réplica IAT): tema `hidro_RIO_ATE_10` declarado (0,35 ha em G1) → o próprio cadastro declara ≤ 10 m.

## M5 — protocolo de campo (o que fecha o número)

Detalhe em `cauce_resumo.json → M5`. Resumo: 8 seções no Arroio 1, 10 no Arroio 2, 8 no Arroio 3 (2 a montante e 2 a jusante da represa, nunca no vaso), incluindo entrada/saída do imóvel e o trecho mais largo sugerido por qualquer método; em cada seção medir com trena/laser a **largura da calha do leito regular** (borda a borda da ruptura de declive), lâmina e profundidade do dia, altura de barranco em cada margem, coordenadas GNSS (erro ≤ 0,5 m) das **duas** bordas, presença de água corrente, marcas de cheia, fotos a montante/jusante com escala; época de águas médias (não após chuva > 30 mm/48 h); planilha + shapefile anexados ao laudo com ART/TRT. Regra de decisão: a largura legal por curso é a **maior** largura de calha em seção válida dentro do imóvel; se alguma ≥ 10 m, repetir com 2 medições independentes e ampliar a APP a 50 m naquele curso.

## Verificação de camadas (`cauce_resumo.json → verificacion_capas`)

CHM híbrido 0,25 m: 0-21,6 m, média 0,27, 30,5 % nodata (fora da huella do DSM). `dtm_fonte`: 0/1/2, média 0,77. DSM 0,25 m: 629,3-728,6 m. Arbóreo RF 0,5 m: 8,6 % do grid. Ortofoto 5 cm (amostra de 1 em 6 blocos): L 0-255 (média 108), ExG −72 a 160, BR −1 a 1, TEX 0-72 (média 21,8), alpha válido 99,5 %. DTM 5 cm (7 janelas): 603,3-610,0 m (datum bruto do ODM). `ACUMULACION_ha_30m`: 0,09-4.080 ha, sem nodata.
