# -*- coding: utf-8 -*-
"""textos_produtor.py — textos do RESUMO PARA O PRODUTOR (pt-BR, linguagem simples).

Regras: uma ideia por frase; termos legais explicados em uma frase; nada de RF/CHM/MNDWI/envolvente/consenso;
"laudo" só em "não é laudo"; nunca "dispensa"; largura dos arroios = "até 10 m, provável, sem medição".
Todos os números entram por {chaves} preenchidas em an_19 a partir dos JSON (nenhum número digitado aqui).
"""

TXT = {
    'footer': 'Resumo para o produtor · Santo Antônio · 09/2026',
    'cover_title': 'Mata ciliar e Reserva Legal',
    'cover_sub': 'Fazenda Santo Antônio · resumo para o produtor · 06/09/2026',
    'h1': 'Mata ciliar e Reserva Legal da Fazenda Santo Antônio — resumo para o produtor',
    'h1_sub': 'Com base em satélite, drone e dados do governo · 06/09/2026',

    'ficha': [
        ('Fazenda', 'Fazenda Santo Antônio — Sonia Maria Bigati'),
        ('Área', '{area} ha ({mf} módulos fiscais de {mf_ha} ha)'),
        ('Glebas', 'Gleba 1: {g1} ha · Gleba 2 ("os 6 alqueires"): {g2} ha = {g2_alq} alqueires'),
        ('Município', 'São Sebastião da Amoreira – PR (o CAR está registrado em Santo Antônio do Paraíso: conferir)'),
        ('Imagem de satélite', 'Sentinel-2 de 29/08/2026 (10 m por pixel)'),
        ('Voo de drone', '22/05/2026, foto a 5 cm por pixel (cobriu {cob_pct}% da fazenda)'),
    ],
    'em_uma_frase': 'A fazenda ainda não está em dia com a lei da mata: falta plantar {app_rec} ha de mata na beira dos rios, '
                    'faltam {rl_def} ha de Reserva Legal e o CAR precisa ser corrigido. A lei dá caminhos e prazos para regularizar. '
                    'Este resumo mostra o que existe, o que falta e por onde começar.',

    # ---------------------------------------------------------------- 1 resposta curta
    's1': 'A resposta curta',
    's1_intro': 'Quatro perguntas, quatro respostas. Os números vêm da foto de drone de 22/05/2026 e dos mapas do governo. '
                'São números preliminares: o técnico de campo e o IAT (órgão ambiental do Paraná) confirmam.',
    'kpi': [('{app_rec}', 'ha de mata a plantar<br/>na beira dos rios'), ('{rl_def}', 'ha de Reserva Legal<br/>que faltam'),
            ('{car_rl}', 'ha de Reserva Legal<br/>que o CAR declara hoje'), ('{represa}', 'ha de água na represa<br/>em 22/05/2026')],
    'tab_hdr': ['O que a lei pede', 'O que a fazenda tem', 'O que falta'],
    'itens': [
        ('a) Mata na beira dos rios e da nascente (APP)', 'NÃO ESTÁ EM DIA',
         '{app_exig} ha de mata: 30 m de cada lado dos 3 arroios e 50 m em volta da nascente.',
         '{app_veg} ha com mata e {app_agua} ha de água.',
         'Plantar {app_rec} ha ({app_pra} ha se entrar no PRA do Paraná).'),
        ('b) Reserva Legal (20% da fazenda com mata)', 'NÃO ESTÁ EM DIA',
         '{rl_exig} ha (20% de {area} ha).',
         '{rl_veg} ha de mata que conta.',
         '{rl_def} ha ({rl_def_cons} ha no cenário mais rigoroso).'),
        ('c) CAR (cadastro ambiental da fazenda no governo)', 'PRECISA CORRIGIR',
         'Declarar toda a mata, a Reserva Legal exigida e as duas glebas juntas.',
         'Declara só {car_rl} ha de Reserva Legal e {car_veg} ha de mata. A Gleba 2 está fora.',
         'Retificar o CAR e incluir a Gleba 2.'),
        ('d) Represa', 'PRECISA REGULARIZAR',
         'Outorga (licença de uso da água) válida e faixa de mata definida pelo IAT.',
         '{represa} ha de água (maior que 1 ha). Outorga vencida em {outorga_venc}.',
         'Renovar a outorga e medir a represa em campo.'),
    ],

    # ---------------------------------------------------------------- 2 inventário
    's2': 'O que tem dentro da fazenda',
    's2_intro': 'A foto de drone mostrou, metro a metro, o que existe dentro do perímetro. O mapa P1 está na página seguinte.',
    'inv_hdr': ['O que existe', 'Quanto'],
    'inv': [
        ('3 arroios (córregos)', 'Arroio 1: {a1} m · Arroio 2: {a2} m · Arroio 3: {a3} m dentro da fazenda'),
        ('Largura dos arroios', 'Até 10 m, provável. Ainda sem medição: as árvores escondem o leito.'),
        ('1 nascente', 'Provável, na cabeceira do Arroio 2 (água a {nasc_dist} m do ponto do mapa oficial).'),
        ('1 represa', '{represa} ha de água no Arroio 3, em 22/05/2026.'),
        ('1 açude pequeno', '{acude} ha, na cabeceira do Arroio 2, ao lado da nascente.'),
        ('Mata nativa que conta', '{rl_veg} ha (dentro e fora da beira dos rios).'),
        ('Lavoura', 'Cerca de {lavoura} ha.'),
        ('Pasto', 'Cerca de {pasto} ha.'),
    ],
    'p1_cap': 'Mapa P1 — A fazenda vista de cima: 2 glebas, 3 arroios, nascente, represa e açude.',

    # ---------------------------------------------------------------- 3 APP
    's3': 'Mata na beira dos rios (APP)',
    's3_txt': [
        'APP quer dizer "área de preservação permanente". É a faixa de mata que a lei exige ao longo de rios e nascentes: '
        'aqui, 30 m de cada lado de cada arroio e 50 m em volta da nascente. Isso dá {app_exig} ha.',
        'Hoje {app_veg} ha dessa faixa já têm mata e {app_agua} ha são água. Faltam {app_rec} ha. '
        'No mapa P2 é o vermelho: a maior parte fica ao longo do Arroio 2 e perto da represa.',
        'PRA é o programa do Paraná para quem regulariza. Ele reduz a faixa a plantar para 20 m: nesse caso faltariam {app_pra} ha. '
        'Depende da data em que o CAR foi feito (conferir no recibo).',
    ],
    'app_hdr': ['Faixa de mata na beira dos rios (APP)', 'ha'],
    'app_tab': [('A lei pede', '{app_exig}'), ('Já tem mata', '{app_veg}'), ('É água', '{app_agua}'), ('Falta plantar', '{app_rec}'),
                ('Falta plantar, se entrar no PRA', '{app_pra}')],
    's3_represa': 'Represa: mediu {represa} ha no dia do voo, maior que 1 ha. A faixa de mata em volta dela quem define é o IAT, na licença. '
                  'A outorga (licença de uso da água) venceu em {outorga_venc}: precisa renovar.',
    'p2_cap': 'Mapa P2 — Verde: já tem mata. Vermelho: falta plantar. Azul: água. Linha tracejada: a faixa que a lei pede.',

    # ---------------------------------------------------------------- 4 RL
    's4': 'Reserva Legal (20% da fazenda)',
    's4_txt': [
        'Reserva Legal é a parte da fazenda que a lei manda deixar com mata nativa. Aqui é 20%: 20% de {area} ha dá {rl_exig} ha.',
        'A mata da beira dos rios também conta. Somando tudo, hoje contam {rl_veg} ha. Faltam {rl_def} ha. '
        'Se a mata nova da beira do Arroio 2 não for aceita como mata nativa, faltam {rl_def_cons} ha.',
        'Três caminhos, que podem ser combinados: deixar a mata regenerar sozinha, plantar, ou compensar em outra área com mata no mesmo bioma. '
        'Prazo: a lei dá até 20 anos, fazendo 1/10 a cada 2 anos.',
    ],
    'rl_hdr': ['Reserva Legal', 'ha'],
    'rl_tab': [('A lei pede (20%)', '{rl_exig}'), ('Mata que conta hoje', '{rl_veg}'), ('Falta', '{rl_def}'),
               ('Falta, se a mata nova não contar', '{rl_def_cons}'), ('O CAR declara hoje', '{car_rl}')],
    'p3_cap': 'Mapa P3 — Verde: mata que conta. Laranja: onde plantar ou deixar regenerar. Riscado branco: mata nova a confirmar em campo.',

    # ---------------------------------------------------------------- 5 Gleba 2
    's5': 'Os 6 alqueires (Gleba 2)',
    's5_txt': [
        'A Gleba 2 tem {g2} ha ({g2_alq} alqueires) e foi comprada como terra limpa, sem mata.',
        'As duas glebas são da mesma dona e ficam coladas. Pela regra, é uma fazenda só e um CAR só.',
        'Por isso os 6 alqueires não têm conta própria. Eles somam {g2_rl} ha à Reserva Legal da fazenda inteira ({g1_rl} + {g2_rl} = {rl_exig} ha). '
        'Essa Reserva pode ficar toda na Gleba 1.',
        'Atenção à ponta norte: o desenho da Gleba 2 avança sobre {ponta} ha de mata que talvez seja do vizinho. '
        'Conferir na escritura. Se a mata for da fazenda, a Reserva Legal que falta cai para {rl_def_ponta} ha.',
    ],
    'p4_cap': 'Mapa P4 — Gleba 2: lavoura em quase tudo; a mata da ponta norte (riscado vermelho) precisa ser conferida na escritura.',

    # ---------------------------------------------------------------- 6 CAR
    's6': 'O CAR da fazenda precisa ser corrigido',
    's6_txt': [
        'CAR é o cadastro ambiental da fazenda no governo. O CAR existente ({car_cod}) foi feito com números muito diferentes do que existe.',
        'Ele declara menos mata do que há e uma Reserva Legal muito menor que a exigida. E deixa a Gleba 2 de fora.',
    ],
    'car_hdr': ['Tema', 'O CAR declara', 'O que existe'],
    'car_tab': [
        ('Área da fazenda', '{car_area} ha', '{area} ha (com a Gleba 2)'),
        ('Reserva Legal', '{car_rl} ha', '{rl_exig} ha exigidos; {rl_veg} ha de mata que conta'),
        ('Mata nativa', '{car_veg} ha', '{rl_veg} ha'),
        ('Represa', '{car_represa} ha', '{represa} ha em 22/05/2026'),
        ('Açude na nascente', '{car_acude} ha', '{acude} ha'),
        ('Gleba 2', 'Fora deste CAR', 'Incluir no mesmo CAR'),
    ],
    's6_fim': 'O que fazer: retificar o CAR com a mata real, a Reserva Legal exigida, a represa medida em campo e a Gleba 2 incluída. '
              'Quem faz é o técnico responsável pelo cadastro, com a escritura em mãos.',

    # ---------------------------------------------------------------- 7 drone
    's7': 'O que o drone mostrou de perto',
    's7_txt': [
        'Represa: {represa} ha de água no dia do voo, maior que 1 ha. A faixa de mata em volta é definida pelo IAT na licença. '
        'A outorga (licença de uso da água) venceu em {outorga_venc}: renovar.',
        'Toda a fazenda fica dentro da área de manancial do Rio Congonhas (água que abastece cidades). '
        'Por isso o IAT olha com mais cuidado qualquer obra em rio, nascente ou represa.',
        'Açude e nascente: existe um açude pequeno ({acude} ha) na cabeceira do Arroio 2, a {nasc_dist} m do ponto da nascente do mapa oficial. '
        'O olho d\'água exato fica escondido no brejo: marcar com GPS em campo.',
        'Largura dos arroios: não deu para medir pela foto, porque as árvores cobrem o leito. Provável até 10 m. '
        'Medir com trena e GPS: se algum arroio passar de 10 m, a faixa de mata dele sobe de 30 m para 50 m.',
        'Mata nova: na beira do Arroio 2 há {f13} ha de mata jovem, com árvores de {f13_h50} a {f13_h90} m, em regeneração. Precisa de vistoria em campo para contar.',
    ],
    'p5_cap': 'Mapa P5 — Foto de drone a 5 cm: (a) represa; (b) açude e ponto da nascente.',

    # ---------------------------------------------------------------- 8 próximos passos
    's8': 'Próximos passos, em ordem',
    's8_intro': 'Seis passos, na ordem em que valem mais. Cada um destrava o seguinte.',
    'passos_hdr': ['Passo', 'Quem faz', 'Para quê'],
    'passos': [
        ('1. Conferir a escritura da Gleba 2 e a matrícula de origem', 'A dona, com o cartório ou advogado',
         'Saber se a ponta norte é da fazenda e fechar a conta da Reserva Legal.'),
        ('2. Medir em campo com trena e GPS: largura dos 3 arroios, olho d\'água da nascente, contorno da represa e do açude',
         'Técnico de campo (Pixadvisor + topógrafo)', 'Fixar a faixa de mata com valor legal. Confirmar que os arroios têm até 10 m.'),
        ('3. Renovar a outorga da represa e pedir a do açude', 'A dona, com o técnico, no IAT',
         'Represa em regra. O IAT define a faixa de mata em volta dela.'),
        ('4. Corrigir o CAR e incluir a Gleba 2', 'Técnico responsável pelo cadastro',
         'Cadastro certo: Reserva Legal de {car_rl} para {rl_exig} ha; mata de {car_veg} para {rl_veg} ha. Ver se cabe o PRA ({app_pra} ha em vez de {app_rec} ha).'),
        ('5. Vistoria da mata nova na beira do Arroio 2 ({f13} ha)', 'Engenheiro florestal',
         'Confirmar que ela conta para a Reserva Legal. Decide se faltam {rl_def} ou {rl_def_cons} ha.'),
        ('6. Plano de plantio e regeneração: {app_rec} ha na beira dos rios + {rl_def} ha de Reserva Legal (ou compensar)', 'Pixadvisor + IAT',
         'Cronograma de até 20 anos, 1/10 a cada 2 anos. Com o plano aprovado, a fazenda entra em regularização.'),
    ],
    'nao_e': 'Este resumo não é laudo. É um diagnóstico preliminar feito com satélite, drone e dados do governo. '
             'O IAT valida. O técnico de campo confirma as medidas. Os números podem mudar um pouco depois da medição em campo.',
    'contato': 'Dúvidas: Eng. Agr. Nilton Camargo · nilton.camargo@pixadvisor.network · +591 721 49171',
}
