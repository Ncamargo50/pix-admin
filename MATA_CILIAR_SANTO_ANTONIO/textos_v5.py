# -*- coding: utf-8 -*-
"""textos_v5.py — textos do RELATÓRIO FINAL v5 (pt-BR, linguagem simples, nível produtor rural).

Dois imóveis SEPARADOS (nada se soma): Fazenda Santo Antônio e Área dos 6 alqueires.
Regras: uma ideia por frase; termos legais explicados em uma frase; nada de jargão técnico
(sem RF/CHM/MNDWI/FBDS/DTM/DSM: "mapa oficial do governo", "foto de drone"); "laudo" só em "não é laudo";
nunca "dispensa" afirmada; sem palavras em espanhol; só glifos WinAnsi (sem setas, sem "maior ou igual").
TODOS os números entram por {chaves} preenchidas em dron_06_informe_v5.py a partir de resultados_v5.json.
"""

TXT = {
    'footer': 'Mata ciliar e Reserva Legal · relatório final · 09/2026',
    'cover_title': 'Mata ciliar e Reserva Legal',
    'cover_sub': 'Fazenda Santo Antônio e Área dos 6 alqueires · relatório final · 07/09/2026',
    'h1': 'Mata ciliar e Reserva Legal: Fazenda Santo Antônio e Área dos 6 alqueires',
    'h1_sub': 'Relatório final, feito só com a foto de drone de cada imóvel e com a consulta aos serviços do governo de 06/09/2026.',

    'ficha': [
        ('Proprietária', 'Sonia Maria Bigati'),
        ('Imóvel 1', 'Fazenda Santo Antônio: {sa_area} ha ({sa_alq} alqueires; {sa_mf} módulos fiscais de {mf_ha} ha)'),
        ('Imóvel 2', 'Área dos 6 alqueires: polígono de {al_area} ha ({al_alq} alqueires paulistas), comprada como terra limpa'),
        ('Município', 'Santo Antônio do Paraíso - PR (município do CAR)'),
        ('Voo de drone', '22/05/2026, foto a 5 cm por pixel, recortada pelo contorno de cada imóvel'),
        ('Consulta ao governo', '06/09/2026: situação do CAR (cadastro ambiental) e da outorga da represa'),
        ('Data deste relatório', '07/09/2026'),
    ],
    'em_uma_frase': 'São dois imóveis e duas contas separadas. Na Fazenda Santo Antônio falta plantar {app_rec} ha de mata na beira dos rios e '
                    'faltam {rl_def} ha de Reserva Legal; o CAR precisa ser corrigido e a outorga da represa venceu. '
                    'Nos 6 alqueires a terra é limpa mesmo: não há rio nem nascente, mas falta toda a Reserva Legal, {al_rl} ha. '
                    'A lei dá caminhos e prazos para regularizar os dois.',

    # ---------------------------------------------------------------- resposta curta
    's_resp': 'A resposta curta',
    's_resp_intro': 'Quatro perguntas para cada imóvel. Os números vêm da foto de drone de 22/05/2026 (só a parte dentro de cada contorno) '
                    'e das linhas de rio e nascente do mapa oficial do governo. São números preliminares: o IAT (órgão ambiental do Paraná) valida.',
    'kpi_sa_titulo': 'Fazenda Santo Antônio ({sa_area} ha)',
    'kpi_sa': [('{app_rec}', 'ha de mata a plantar<br/>na beira dos rios'), ('{rl_def}', 'ha de Reserva Legal<br/>que faltam'),
               ('{car_rl}', 'ha de Reserva Legal<br/>que o CAR declara'), ('{represa}', 'ha de água na represa<br/>(outorga vencida)')],
    'kpi_al_titulo': 'Área dos 6 alqueires ({al_area} ha)',
    'kpi_al': [('0', 'ha de beira de rio<br/>a plantar (não há rio)'), ('{al_rl}', 'ha de Reserva Legal<br/>que faltam (toda)'),
               ('100%', 'coberto pelo drone:<br/>terra limpa confirmada')],
    'resp_hdr': ['Pergunta', 'Fazenda Santo Antônio', 'Área dos 6 alqueires'],
    'resp': [
        ('Mata na beira dos rios e da nascente (APP)',
         'NÃO ESTÁ EM DIA|A lei pede {app_exig} ha. Tem {app_veg} ha de mata e {app_agua} ha de água. Falta plantar {app_rec} ha ({app_pra} ha se entrar no PRA).',
         'NÃO SE APLICA|Não há arroio, nascente nem água dentro do polígono. Nada a plantar na beira de rio.'),
        ('Reserva Legal (20% com mata nativa)',
         'NÃO ESTÁ EM DIA|A lei pede {rl_exig} ha. Conta {rl_veg} ha de mata ({rl_pct}%). Faltam {rl_def} ha.',
         'NÃO ESTÁ EM DIA|A lei pede {al_rl} ha (20% de {al_area} ha). Há 0 ha de mata. Falta tudo: {al_rl} ha.'),
        ('CAR (cadastro ambiental no governo)',
         'PRECISA CORRIGIR|Situação em 06/09/2026: "{car_status}". Declara só {car_rl} ha de Reserva Legal e {car_veg} ha de mata; o drone vê {med_veg} ha de mata.',
         'PRECISA DE CAR PRÓPRIO|A área ainda está dentro do CAR de origem (imóvel de {al_car_area} ha), situação "{al_car_status}". Ali ela consta como área de uso, sem Reserva Legal.'),
        ('Represa e outorga (licença de uso da água)',
         'PRECISA REGULARIZAR|Represa de {represa} ha (mais de 1 ha). Outorga {outorga_n}: situação "irregular", vencida em {outorga_venc}.',
         'NÃO SE APLICA|Não há represa nem outorga dentro do polígono.'),
    ],

    # ================================================================ CAPÍTULO 1: SANTO ANTÔNIO
    'cap1': 'Fazenda Santo Antônio ({sa_area} ha)',
    's1': 'O que tem dentro da fazenda',
    's1_txt': [
        'O drone fotografou {cob} ha dos {sa_area} ha (uma faixa de {sem_cob} ha no norte ficou sem foto e fica "não avaliada": nada foi preenchido com satélite). '
        'Tudo o que está fora do contorno da fazenda foi apagado do mapa: só conta o que está dentro.',
    ],
    'inv_hdr': ['O que existe', 'Quanto'],
    'inv': [
        ('3 arroios (córregos)', 'Arroio 1: {a1} m · Arroio 2: {a2} m · Arroio 3 (Ribeirão do Salto): {a3} m dentro da fazenda, pela linha do mapa oficial'),
        ('Largura dos arroios', 'Até 10 m, provável. Sem medição: as árvores escondem o leito. Medir com trena e GPS.'),
        ('1 nascente', 'Na cabeceira do Arroio 2 (ponto do mapa oficial), a {nasc_dist} m da água do açude. Marcar o olho d\'água com GPS.'),
        ('1 represa', '{represa} ha de água no Arroio 3 em 22/05/2026 (mais de 1 ha).'),
        ('1 açude e 2 lagoas', 'Açude de {acude} ha na cabeceira do Arroio 2 (o CAR declara {car_acude} ha); 2 lagoas pequenas com {lagoas} ha.'),
        ('Mata, pasto e lavoura', '{arborea} ha de mata (mais {arbustiva} ha de arbustos em regeneração), {pasto} ha de pasto e {lavoura} ha de lavoura e solo.'),
    ],
    'sa1_cap': 'Mapa SA1 — A fazenda vista pelo drone: 3 arroios com os metros dentro da fazenda, nascente, represa, açude e a faixa sem foto (hachurada).',

    's2': 'Mata na beira dos rios (APP)',
    's2_txt': [
        'APP quer dizer "área de preservação permanente": a faixa de mata que a lei exige ao longo dos rios e das nascentes. '
        'Aqui são 30 m de cada lado dos 3 arroios e 50 m em volta da nascente: {app_exig} ha.',
        'Hoje {app_veg} ha dessa faixa têm mata e {app_agua} ha são água. Faltam {app_rec} ha: {app_rec_lav} ha hoje em lavoura e {app_rec_pasto} ha em pasto. '
        'Outros {app_sem} ha ficaram sem foto do drone: não avaliados.',
        'PRA é o programa do Paraná para quem regulariza. Nele a faixa a plantar cai para 20 m nos arroios e 15 m na nascente: faltariam {app_pra} ha. Depende da data do CAR (conferir no recibo).',
        'Represa: {represa} ha de água, mais de 1 ha. A faixa de mata em volta dela quem define é o IAT, na licença da represa. '
        'Se o IAT pedir 30 m, a faixa exigida sobe para {rz_exig} ha e o que falta plantar, para {rz_rec} ha.',
    ],
    'app_hdr': ['Faixa de mata na beira dos rios (APP)', 'ha'],
    'app_tab': [('A lei pede (30 m nos arroios + 50 m na nascente)', '{app_exig}'), ('Já tem mata', '{app_veg}'), ('É água', '{app_agua}'),
                ('Sem foto do drone: não avaliado', '{app_sem}'), ('Falta plantar', '{app_rec}'), ('Falta plantar, se entrar no PRA (20 m + 15 m)', '{app_pra}')],
    'sa2_cap': 'Mapa SA2 — Verde: já tem mata. Vermelho: falta plantar. Azul: água. Cinza: sem foto. Linha preta: faixa da lei. Linha rosa: faixa de 20 m do PRA.',

    's3': 'Reserva Legal (20% da fazenda)',
    's3_txt': [
        'Reserva Legal é a parte do imóvel que a lei manda manter com mata nativa. Aqui é 20%: 20% de {sa_area} ha dá {rl_exig} ha.',
        'A mata da beira dos rios também conta. Somando tudo, hoje contam {rl_veg} ha ({rl_pct}% do exigido). Faltam {rl_def} ha. '
        'Árvores isoladas menores que 0,05 ha ({rl_isol} ha) não contam; a faixa sem foto não soma nem desconta.',
        'Os {app_rec} ha que serão plantados na beira dos rios também contam para a Reserva Legal. Sobram {rl_resto} ha, e a sugestão do mapa SA3 é uma faixa sobre o pasto, junto à mata que já existe.',
        'Três caminhos, que podem ser combinados: plantar mudas nativas, deixar a mata regenerar sozinha (com vistoria que comprove que ela volta), '
        'ou compensar em outra área com mata no mesmo bioma. Prazo da lei: até 20 anos, pelo menos 1/10 a cada 2 anos ({rl_etapa} ha nos primeiros 2 anos).',
    ],
    'rl_hdr': ['Reserva Legal', 'ha'],
    'rl_tab': [('A lei pede (20% de {sa_area} ha)', '{rl_exig}'), ('Mata que conta hoje (fora e dentro da beira dos rios)', '{rl_veg}'), ('Falta', '{rl_def}'),
               ('Beira dos rios a plantar, que também vai contar', '{app_rec}'), ('O CAR declara hoje', '{car_rl}')],
    'sa3_cap': 'Mapa SA3 — Verde: mata que conta. Vermelho: beira dos rios a plantar (também conta). Laranja: sugestão de onde plantar o resto, junto à mata.',

    's4': 'CAR e outorga: a situação hoje (06/09/2026)',
    's4_txt': [
        'CAR é o cadastro ambiental do imóvel no governo. O CAR da fazenda ({car_cod}) está com a situação "{car_status}" '
        '(dados publicados pelo governo: SICAR de {sicar_data}). Ele foi feito com números muito diferentes do que o drone mostra.',
    ],
    'car_hdr': ['Tema', 'O CAR declara', 'O drone mede'],
    'car_tab': [
        ('Área do imóvel', '{car_area} ha', '{sa_area} ha (contorno)'),
        ('Reserva Legal', '{car_rl} ha', '{rl_exig} ha exigidos; {rl_veg} ha de mata que conta'),
        ('Mata nativa', '{car_veg} ha', '{med_veg} ha'),
        ('Beira dos rios (APP)', '{car_app} ha', '{app_exig} ha exigidos; {app_veg} ha com mata'),
        ('Represa e lagoas', '{car_res} ha', '{med_agua} ha de água (represa: {represa} ha)'),
        ('Área de uso (consolidada)', '{car_cons} ha', '{med_cons} ha (lavoura, pasto e sede)'),
    ],
    's4_fim': [
        'O que fazer com o CAR: retificar, com a mata real ({med_veg} ha), a Reserva Legal exigida ({rl_exig} ha) e a represa medida em campo. Quem faz é o técnico responsável pelo cadastro.',
        'Outorga é a licença de uso da água. A da represa ({outorga_n}) é uma outorga prévia da barragem no Ribeirão do Salto, em nome de Sonia Maria Bigati, publicada em {outorga_pub}. '
        'Em 06/09/2026 o governo a mostra "IRREGULAR" e vencida em {outorga_venc}. O que fazer: renovar (ou pedir a outorga definitiva) no IAT, com a represa medida em campo.',
    ],
    'sa4_cap': 'Mapa SA4 — Sobre a foto do drone: mata e água vistas pelo drone (verde claro e azul) e os polígonos que o CAR declara (roxo: Reserva Legal; riscados: mata e represa).',

    's5': 'De perto, a 5 cm: represa, açude e nascente',
    's5_txt': [
        'Represa: {represa_3} ha de água no dia do voo (fim do outono). O espelho que vale para a lei é o do nível máximo normal, medido em campo no vertedouro.',
        'Açude e nascente: o açude da cabeceira do Arroio 2 tem {acude} ha (o CAR declara {car_acude} ha). O ponto da nascente do mapa oficial fica a {nasc_dist} m dele, '
        'escondido no brejo: marcar com GPS em campo.',
    ],
    'sa5_cap': 'Mapa SA5 — Foto de drone a 5 cm: (a) represa de {represa} ha; (b) açude de {acude} ha e ponto da nascente.',

    # ================================================================ CAPÍTULO 2: 6 ALQUEIRES
    'cap2': 'Área dos 6 alqueires ({al_area} ha)',
    's6': 'O que o drone mostra',
    's6_txt': [
        'O polígono da área comprada tem {al_area} ha, o que dá {al_alq} alqueires paulistas. '
        'O drone cobriu 100% do polígono.',
        'Dentro do contorno há {al_lav} ha de lavoura e solo, {al_pasto} ha de pasto e {al_mata} ha de árvores (uma mancha pequena, que não conta). '
        'Não há arroio, nascente, represa nem água. Terra limpa confirmada, como foi comprada.',
        'Por isso não há faixa de beira de rio (APP) a plantar aqui: 0 ha.',
    ],
    'al1_cap': 'Mapa AL1 — Os 6 alqueires vistos pelo drone: lavoura em tudo, sem arroio, sem nascente e sem água.',

    's7': 'Reserva Legal que falta: {al_rl} ha',
    's7_txt': [
        'A Reserva Legal é 20% do imóvel com mata nativa: 20% de {al_area} ha dá {al_rl} ha. '
        'Como não há mata dentro do polígono, falta toda a Reserva Legal: {al_rl} ha.',
        'Por que 20% mesmo sendo uma área pequena: ela veio de um imóvel maior, de {al_car_area} ha ({al_car_mf} módulos fiscais). '
        'A lei da mata (Código Florestal, artigo 12) diz que, quando se desmembra um imóvel maior que 4 módulos, a parte desmembrada continua devendo os 20%. '
        'A regra que reduz a Reserva Legal para imóveis pequenos (artigo 67) só valeria se o imóvel de origem tivesse até 4 módulos em 22/07/2008, e não é o caso.',
        'Onde pode ficar: dentro do próprio polígono (qualquer parte, escolhida com o IAT), ou compensada em outra área com mata no mesmo bioma. '
        'Prazo: até 20 anos, pelo menos 1/10 a cada 2 anos ({al_etapa} ha nos primeiros 2 anos).',
        'Se os 6 alqueires entrarem no mesmo CAR da fazenda, a Reserva Legal do cadastro vira a soma das duas: {rl_exig} ha + {al_rl} ha = {rl_soma} ha. '
        'Isso não muda o que cada imóvel deve. Neste relatório os dois seguem separados.',
    ],
    'al_rl_hdr': ['Reserva Legal dos 6 alqueires', 'ha'],
    'al_rl_tab': [('A lei pede (20% de {al_area} ha)', '{al_rl}'), ('Mata que conta hoje', '{al_veg}'),
                  ('Falta', '{al_rl}'), ('Beira de rio (APP) a plantar', '0')],
    'al2_cap': 'Mapa AL2 — Reserva Legal que falta nos 6 alqueires: {al_rl} ha, a definir dentro do polígono ou compensar.',

    's8': 'O CAR de origem',
    's8_txt': [
        'Os 6 alqueires ainda não têm CAR próprio. O polígono está dentro do CAR de origem ({al_car_cod}), do imóvel de {al_car_area} ha de onde a área foi desmembrada. '
        'Situação desse CAR em 06/09/2026: "{al_car_status}".',
        'Dentro do polígono, esse CAR declara: Reserva Legal 0 ha, beira de rio (APP) 0 ha, mata 0 ha e área de uso (consolidada) {al_area} ha. '
        'Isso bate com o que o drone vê, mas deixa a Reserva Legal de {al_rl} ha sem lugar. O desmembramento exige CAR próprio (ou a retificação do CAR de origem) com essa Reserva Legal.',
        'A mata que fica logo ao norte deste polígono não faz parte desta compra e não entra nesta conta.',
    ],

    # ================================================================ CAPÍTULO 3
    'cap3': 'Próximos passos, em ordem',
    's9_intro': 'Passos separados por imóvel, na ordem em que valem mais. Cada um destrava o seguinte.',
    'passos_hdr': ['Passo', 'Quem faz', 'Para quê'],
    'passos_sa': [
        ('1. Medir em campo com trena e GPS: largura dos 3 arroios, olho d\'água da nascente, contorno da represa (no nível do vertedouro) e do açude',
         'Técnico de campo (Pixadvisor + topógrafo)', 'Fixar a faixa de mata com valor legal e confirmar que os arroios têm até 10 m.'),
        ('2. Renovar a outorga da represa ({outorga_n}, vencida em {outorga_venc})', 'A proprietária, com o técnico, no IAT',
         'Represa em regra. O IAT define a faixa de mata em volta dela.'),
        ('3. Retificar o CAR da fazenda', 'Técnico responsável pelo cadastro',
         'Reserva Legal de {car_rl} para {rl_exig} ha; mata de {car_veg} para {med_veg} ha; represa medida. Ver se cabe o PRA ({app_pra} ha em vez de {app_rec} ha).'),
        ('4. Plano de plantio e regeneração: {app_rec} ha na beira dos rios + {rl_def} ha de Reserva Legal (ou compensar parte)', 'Pixadvisor + IAT',
         'Cronograma de até 20 anos, 1/10 a cada 2 anos. Com o plano aprovado, a fazenda entra em regularização.'),
    ],
    'passos_al': [
        ('1. Conferir na escritura a área total do imóvel', 'A proprietária, com o cartório ou advogado',
         'Fechar a área ({al_area} ha) e a Reserva Legal exigida ({al_rl} ha).'),
        ('2. Fazer o CAR próprio dos 6 alqueires (ou retificar o CAR de origem)', 'Técnico responsável pelo cadastro',
         'Declarar a área desmembrada e a Reserva Legal de {al_rl} ha, hoje sem lugar.'),
        ('3. Escolher onde fica a Reserva Legal: dentro do polígono ou compensação', 'A proprietária, com Pixadvisor e IAT',
         'Plano de {al_rl} ha em até 20 anos, ou compensação em área com mata no mesmo bioma.'),
    ],
    's10': 'Como foi feito e o que este relatório não é',
    's10_txt': [
        'Só a foto de drone de 22/05/2026 (5 cm por pixel) entrou nas medições, recortada pelo contorno de cada imóvel: nada fora do contorno foi medido e nada foi preenchido com satélite. '
        'Onde o drone não fotografou ({sem_cob} ha no norte da fazenda), a área ficou "não avaliada".',
        'As linhas dos arroios e o ponto da nascente vêm do mapa oficial do governo (escala 1:25.000). Debaixo das árvores o drone não vê o leito: a largura dos arroios não foi medida; '
        'a faixa de 30 m foi contada a partir da linha oficial. A medição com trena e GPS pode mudar um pouco os números.',
        'A situação do CAR e da outorga é a publicada pelos serviços do governo em 06/09/2026 (os dados do CAR publicados ali são do SICAR de {sicar_data}). Pode haver processos em andamento que ainda não aparecem.',
        'Este relatório não é laudo. É um diagnóstico preliminar para orientar a proprietária. O IAT valida; o técnico de campo confirma as medidas.',
    ],
    'nao_e': 'Este relatório não é laudo. É um diagnóstico preliminar feito com a foto de drone de cada imóvel e com os dados do governo. '
             'Os dois imóveis são tratados separados: nada se soma. O IAT valida.',
    'contato': 'Dúvidas: Eng. Agr. Nilton Camargo · nilton.camargo@pixadvisor.network · +591 721 49171',
}
