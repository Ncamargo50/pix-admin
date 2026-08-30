# -*- coding: utf-8 -*-
"""Resumo SIMPLES em pt-BR (linguagem de produtor) que acompanha o relatorio
tecnico de maturacao. Sem jargao: nada de NDMI/CIre/intervalos — o que esta
pronto, o que falta, o que fazer. 2 paginas: resumo + mapa de zonas.

Uso: python resumo_simples.py   (le os numeros do resultados_SA_SF_2026-08-29.json)
"""
import os, sys, json
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = r"C:/Users/Usuario/.claude/skills/pixadvisor-propuesta-ejecutiva"
sys.path.insert(0, f"{SKILL}/scripts")
from pix_branding import Brand
from reportlab.platypus import PageBreak, Image, KeepTogether
from reportlab.lib.units import cm

B = Brand(logo=f"{SKILL}/assets/logo_pix_azulnegro_trim.png",
          footer_center="Trigo Santo Antônio + São Francisco · Resumo do produtor · ago/2026")

st = []
st += B.cover_filler()
st += [B.P("O que o satélite mostrou — 29 de agosto", "H1"), B.hr()]
st += [B.P("Este é o resumo simples do relatório técnico. Aqui está só o que importa "
           "para decidir a colheita.", "Body")]

st += [B.sec(1, "O que está pronto AGORA")]
tab = [["Talhão", "Situação", "O que fazer"],
       ["SA-01 (18 ha)", "Seco como a referência", "Medir umidade e colher"],
       ["SF-01 (50 ha)", "Seco como a referência", "Medir umidade e colher"],
       ["SF-02 parte de cima (~25 ha)", "Seco como a referência", "Medir umidade e colher"],
       ["SF-02 parte de baixo (~15 ha)", "Ainda úmido (deu 23 %)", "Esperar 3 a 6 dias"],
       ["SA-02 Setor A (70 ha)", "Secando rápido", "Medir umidade até 04/set"],
       ["SA-02 Setor B (49 ha)", "Ainda verde", "Esperar 1-2 semanas"]]
st += [B.tbl(tab, [5.6 * cm, 5.4 * cm, 4.8 * cm])]
st += [B.P("No total: uns 98 ha prontos para conferir e colher agora, e mais ~40 ha "
           "entrando nesta semana.", "Body")]

st += [B.sec(2, "O que já foi conferido no campo")]
st += [B.P("A parte seca colhida em São Francisco deu 18 % de umidade — exatamente o "
           "ponto de começar a trilha — e PH 78 (qualidade boa). A parte mais verde deu "
           "23 % — ainda cedo. Ou seja: onde o mapa mostrou marrom, o grão estava no "
           "ponto; onde mostrou verde, ainda não. O satélite e o medidor de umidade "
           "contaram a mesma história.", "Body")]

st += [B.sec(3, "As 3 regras simples")]
st += [B.P("1. O satélite diz POR ONDE começar. O medidor de umidade diz QUANDO colher. "
           "Sempre medir antes de entrar com a máquina.", "Body")]
st += [B.P("2. Chuva molha a palha e atrasa tudo alguns dias. Depois de chuva, esperar "
           "o próximo mapa antes de decidir.", "Body")]
st += [B.P("3. A cada 3-5 dias sai um mapa novo. As datas podem se ajustar um pouco — "
           "é normal, o trigo seca conforme o tempo que faz.", "Body")]

st += [B.callout("Esta semana", "Começar pela parte marrom do mapa (SA-01, SF-01 e a parte "
                 "de cima do SF-02). Medir umidade no Setor A de Santo Antônio até 04/set. "
                 "Deixar o Setor B quieto por enquanto. Dúvidas: nilton.camargo@pixadvisor.network "
                 "· +591 721 49171.")]
st += [B.sec(4, "O mapa: cada cor é uma decisão")]
st += [KeepTogether([
    B.P("Marrom = pronto para medir e colher · Laranja = questão de dias · Amarelo = "
        "perto, ainda úmido · Verde = falta 1-2 semanas · Azul = longe ainda. A barra "
        "embaixo de cada talhão mostra quantos hectares tem de cada cor.", "Body"),
    Image(os.path.join(RAIZ, "medicion", "zonas_proximidad_SA_SF_pt.png"),
          width=15 * cm, height=15 * cm * 1710 / 2081)])]

out = os.path.join(RAIZ, "salida", "Resumo_Simples_Produtor_SA_SF_29ago.pdf")
B.build(out, st, cover_title="Trigo — o que colher e quando",
        cover_subtitle="Santo Antônio + São Francisco · Resumo simples do produtor · 29/ago/2026")
print("PDF ->", out)
