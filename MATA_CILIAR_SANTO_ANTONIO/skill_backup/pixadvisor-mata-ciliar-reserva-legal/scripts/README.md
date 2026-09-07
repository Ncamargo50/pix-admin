# Scripts de referência (copiados de `PIXADVISOR_AGENT_WORKSPACE/MATA_CILIAR_SANTO_ANTONIO/`, 2026-09-07)

Não rodam "de caixa": dependem de `comun.py` / `dron_00_comun.py` (rotas do projeto: PROYECTO,
PROPIEDAD_GEOJSON, DRONE, SALIDA_RAIZ), de `pix_branding.py` (skill `pixadvisor-propuesta-ejecutiva`)
e de dados externos (`datos_externos/`, ortofoto ODM). Para um projeto novo:

1. Copiar a pasta, ajustar `dron_00_comun.py` (rotas, IMOVEIS, AREA_INFORMADA_CLIENTE, ALQUEIRE).
2. Baixar governo: `gobierno/hp_gov_descarga.py` (IAT CAR/outorga/FBDS, ANA, IBGE) — hosts `*.pr.gov.br`
   usam cadeia ICP-Brasil: passar `verify=<bundle>`; não desativar TLS; SICAR direto tem captcha.
3. Cadeia drone: `dron_01_recorte.py` → `dron_02_agua.py` → `dron_03_vegetacao.py` → `dron_04_legal.py`
   → `dron_05_mapas_v5.py` → `dron_06_informe_v5.py` (textos em `textos_v5.py`).
4. Sem drone: `satelite_gee/gee_01..03` + `an_01..03` (S2 + FBDS + DEM 30 m + RF consenso).
5. Ortofoto extra: `ortofoto/ortho_0*` (CHM, secções, nascentes, cauce M1–M5).
6. Informes alternativos: `informes/` (resumo produtor 9 pág.; v3 técnico bilíngue).

Ordem de verificação obrigatória: rangos por camada (min/max/nodata) → somas fecham por imóvel
(±0,02 ha) → PDF: render de cada página + fitz (KPIs, glifos, acentos, jargão).
