---
name: pixadvisor-mata-ciliar-reserva-legal
description: Use when a client in Brazil (Paraná or any state) asks whether a rural property complies with the Código Florestal — mata ciliar / APP along streams, springs and reservoirs, Reserva Legal (20 %), CAR status, water-use outorga — or asks to map native vegetation, count and measure arroios, lagoas and represas, or compute how much forest a purchased parcel needs. Triggers - "mata ciliar", "APP", "reserva legal", "CAR", "SICAR", "outorga", "está dentro da norma / da lei", "Lei 12.651", "Código Florestal", "vegetação nativa", "nascente", "represa", "alqueires", drone orthophoto for environmental compliance, IAT Paraná.
---

# Pixadvisor — Mata ciliar (APP), Reserva Legal e CAR

## Overview
Diagnóstico ambiental preliminar (nunca laudo) de um imóvel rural brasileiro: mede vegetação nativa, água,
APP e Reserva Legal, cruza com o CAR e a outorga publicados pelo governo e entrega um relatório em
português simples para o produtor. Implementação de referência validada de ponta a ponta na Fazenda
Santo Antônio (PR, 2026-09-06/07): 5 versões, 3 auditorias adversariais, o cliente corrigiu 3 vezes o
enquadramento. As regras abaixo saem dessas correções.

## Regras que mandam (aprendidas por rejeição do cliente ou da auditoria)
1. **Um cálculo por imóvel, nada se soma.** Cada polígono do GeoJSON é um imóvel com sua RL de 20 % e sua
   APP. Contíguos do mesmo dono podem virar um CAR só (IN MMA 2/2014 art. 32): informar como variante,
   não como veredito. **O polígono do cliente manda**: se ele o edita, recalcular sobre o arquivo novo.
2. **Se há ortofoto de drone, só ela mede.** Recortar ortofoto/DSM/DTM com o polígono ANTES de calcular;
   onde o drone não cobre, "não avaliado" (nunca preencher com satélite). Satélite só quando não há drone.
3. **O leito dos arroios vem da hidrografia oficial (FBDS/IAT 1:25.000 via `geopr.iat.pr.gov.br`)**,
   não da imagem: sob dossel nem drone nem DTM fotogramétrico veem o canal (DTM ODM sob copa = a copa).
   Largura do canal: só trena+GNSS; por imagem reportar "≤10 m provável, sem medição" (métodos M1–M5 em
   `references/ancho_cauce_metodos.md`).
4. **Represa**: o crescimento por Mahalanobis RGB fica curto na orla rasa/turva. Usar k-means 8 grupos
   (R,G,B,S,ExG,log textura) a 10 cm + crescimento desde a semente + fechamento 0,5 m
   (`lamina_kmeans_10cm` em `scripts/drone_por_imovel/dron_02_agua.py`) e **conferir a olho por
   quadrantes**. Espelho ≥ 1 ha → sem dispensa (art. 4º §4); faixa "a definir pelo IAT" (art. 4º III).
   Nunca decidir a dispensa com imagem de seca.
5. **Parcela comprada "limpa"**: RL = 20 % mesmo assim (art. 12 §1º, se desmembrada de imóvel > 4 MF);
   art. 67 só se o imóvel de origem tinha ≤ 4 MF em 22/07/2008. Não mostrar mapas nem cifras da mata
   vizinha que o cliente diz não ter comprado: uma frase só.
6. **Cruzar sempre com o governo**: CAR do próprio imóvel (réplica SICAR no IAT, sem captcha:
   `scripts/gobierno/hp_gov_descarga.py`), CAR de origem da parcela, outorga SIGARH, manancial.
   O "vizinho com represa dentro" era o próprio CAR do cliente.
7. **Relatório**: PT-BR nível produtor, termos explicados em uma frase, perímetros finos e pretos,
   nada fora do perímetro, **cada página e cada mapa renderizados e olhados** antes de entregar;
   verificação fitz: números do JSON presentes, sem glifos fora de WinAnsi, sem espanhol, sem jargão.
   "Vegetação nativa computável", nunca "RL existente"; "não é laudo"; conforme = "com vegetação nativa".

## Fluxo (scripts em `scripts/`)
| Etapa | Script | Saída |
|---|---|---|
| Legislação verificada | `references/legislacion_app_reserva_legal_parana.md`, `parametros_legales.json` | faixas, MF, art. 61-A/Lei PR 18.295, STF, nomenclatura CAR |
| Governo: CAR, outorga, hidrografia, DEMs | `scripts/gobierno/hp_gov_descarga.py`, `an_11_hidrologia_pro.py` | GeoJSON oficiais, comparação declarado × medido |
| Drone por imóvel | `scripts/drone_por_imovel/dron_01..04` | água, vegetação (CHM ≥ 3 m arbórea, 1–3 m arbustiva), APP, RL, `resultados_v5.json` |
| Mapas e relatório produtor | `dron_05_mapas_v5.py`, `dron_06_informe_v5.py`, `textos_v5.py` | 7 mapas + PDF 13 pág. |
| Sem drone (satélite) | `scripts/satelite_gee/` (S2 + RF 10 m, consenso MapBiomas×DW×WC) | só diagnóstico grosso, ±10 m |
| Ortofoto extra (cauce, nascente, CHM) | `scripts/ortofoto/ortho_0*.py` | secções, veredito de nascentes |

Dependências: `comun.py`/`dron_00_comun.py` (rotas do projeto), `pix_branding.py` da skill
`pixadvisor-propuesta-ejecutiva`, geopandas, rasterio, pysheds, sklearn, fitz. Adaptar as rotas do
projeto em `dron_00_comun.py` (PROYECTO, PROPIEDAD_GEOJSON, DRONE).

## Números legais de bolso (Lei 12.651/2012; Paraná)
| Item | Regra |
|---|---|
| APP curso ≤ 10 m / nascente | 30 m da borda da calha / raio 50 m (intermitentes também: STF ADI 4903) |
| RL fora da Amazônia | 20 % do imóvel; APP vegetada computa (art. 15) |
| Área consolidada, imóvel 4–10 MF (PR) | recompor 20 m (cursos ≤ 10 m) e 15 m (nascente), Lei PR 18.295 art. 17 §2; exige CAR até 31/12/2023 |
| Reservatório por barramento | faixa da licença (art. 4º III); < 1 ha dispensada (§4) |
| Regularização RL | art. 66: recompor / regenerar / compensar; 20 anos, 1/10 a cada 2 anos |
| Módulo fiscal | tabela INCRA por município (Sto. Antônio do Paraíso e S. S. da Amoreira = 20 ha) |

## Erros já cometidos (não repetir)
- RL proposta com eucalipto e lascas de 1 pixel; aviso citando a área do fragmento errado (`lista[0]`).
- OA do RF só vale nos pixels de consenso: 10 das 20 ha de floresta ficavam fora.
- MapBiomas 30 m perde faixas ripárias < 30 m e inventa "supressão" (cruzar com Hansen e a imagem).
- Franja jovem sem histórico 2008/2013: defender com série NDVI 24 meses + SWIR + textura + CHM, nunca
  com uma data; estágio sucessional exige campo (CONAMA 2/1994).
- Texto encavalado em legendas e caixas de notas: colocar legenda fora do mapa e olhar o PNG.
- Arquivo GeoJSON bloqueado pelo QGIS: gravar cópia `_v2` e apontar a cadeia para ela.
- `SendMessage` pode estar desativado: relançar agente novo com todo o contexto.

## Ambiguidades já resolvidas (perguntas que o primeiro agente de teste fez)
- **Veredito principal**: o que o cliente pediu (por polígono). A regra legal de CAR único para contíguos
  do mesmo dono (IN MMA 2/2014 art. 32) vai como nota de 3 frases com a soma, nunca no veredito.
- **Art. 12 §1º na parcela desmembrada**: a obrigação é 20 % da própria parcela (14 ha → 2,8 ha); o
  imóvel de origem só decide a classe (> 4 MF → 20 %; ≤ 4 MF em 22/07/2008 → art. 67). Área do
  imóvel de origem = seu CAR na réplica IAT; MF = tabela INCRA do município (marcar NÃO VERIFICADO se
  a fonte não for INCRA/Embrapa).
- **Art. 68** (supressão anterior a 1989 legal à época): não aplicar por padrão; citar como possível
  redução só se o cliente tiver prova documental (Lei PR 18.295 art. 32).
- **Voo em época seca (jun–set) e espelho perto de 1 ha**: não decidir a dispensa; escrever "≥ 1 ha
  indeterminado, medir na cota do vertedouro"; satélite não entra na conta (só se o cliente autorizar
  e sempre rotulado como satélite).
- **Ortofoto ODM sem GCP**: antes de medir, conferir deslocamento horizontal contra 3 objetos fixos
  (dique, cercas, vértices SIGEF): ≤ 3 m aceitável e declarado; cotas absolutas sem valor legal.
- **Manancial de abastecimento "impeditivo"**: frase modelo — "A fazenda está dentro da área de
  manancial X (Portaria N): intervenções e novas outorgas passam por análise mais rigorosa do IAT."

## Auditoria antes de entregar
Três agentes em paralelo: técnico (código/números), legal (aplicação artigo por artigo, por imóvel),
informe (cada frase contra o JSON). Consolidar em `AUDITORIA_RESUMEN_PRO.md` (modelo em
`references/lecciones_auditoria.md`). Veredito "com correções" é o normal; entregar só depois.
