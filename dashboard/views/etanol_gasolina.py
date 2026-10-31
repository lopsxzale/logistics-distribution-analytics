import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
todos = data.aplicar(data.painel_uf(), f, por_categoria=False)

ui.cabecalho(
    "Etanol vs gasolina",
    "Para veículos flex, o etanol só compensa quando custa **até 70% do preço da gasolina** (rende cerca de 30% "
    "menos por litro). Onde vale abastecer a frota leve com etanol?",
    chips=["Ignora o filtro de combustível", "Últimos 3 meses do período para a decisão atual"],
)
if todos.empty:
    ui.vazio()
    st.stop()

recente = todos[todos["data"] > f.fim - pd.DateOffset(months=3)]
par = metrics.paridade_etanol_gasolina(recente, por=["uf", "nome_estado"]).sort_values("razao")
par["razao_pct"] = par["razao"] * 100
n_comp = int(par["etanol_compensa"].sum())
limiar = metrics.LIMIAR_PARIDADE * 100

col1, col2 = st.columns([3, 2], gap="medium")

with col1:
    amplitude = max(float((par["razao_pct"] - limiar).abs().quantile(0.9)), 2.0)
    par["hover"] = [
        f"<b>{n}</b><br>etanol = {ui.pct(r)} da gasolina<br>etanol {ui.brl(e)} · gasolina {ui.brl(g)}"
        for n, r, e, g in zip(
            par["nome_estado"], par["razao_pct"], par["preco_etanol"], par["preco_gasolina"], strict=True
        )
    ]
    fig = ui.mapa_coropletico(
        par,
        data.contornos_estados(),
        "razao_pct",
        "hover",
        ui.ESCALA_DIVERGENTE,
        (limiar - amplitude, limiar + amplitude),
    )
    ui.chart_card(
        "mapa_paridade",
        f"Etanol compensa em {n_comp} de {len(par)} estados",
        ui.estilizar(fig, altura=470, legenda=False),
        "Preço do etanol como % do preço da gasolina em cada estado, na média dos últimos 3 meses do período.",
        "Azul = abaixo de 70% (etanol compensa); vermelho = acima (gasolina compensa). Cinza = perto do empate.",
        "Para frotas leves flex, a regra vira **política de abastecimento por estado**, configurável no cartão-frota.",
    )

with col2:
    cores = [ui.COR_BOM if c else ui.COR_NEUTRA for c in par["etanol_compensa"]]
    fig = go.Figure(
        go.Bar(
            x=par["razao_pct"] - limiar,
            base=limiar,
            y=par["uf"],
            orientation="h",
            marker=dict(color=cores, cornerradius=3),
            customdata=par[["nome_estado", "razao_pct"]],
            hovertemplate="<b>%{customdata[0]}</b>: %{customdata[1]:.1f}%<extra></extra>",
        )
    )
    fig.add_vline(x=limiar, line_color="#f0efec", line_width=1.2)
    fig.update_xaxes(ticksuffix="%")
    fig.update_yaxes(tickfont_size=10, autorange="reversed")
    melhor = par.iloc[0]
    ui.chart_card(
        "barras_paridade",
        "Ranking da paridade",
        ui.estilizar(fig, altura=470, legenda=False),
        "Mesma razão do mapa, ordenada do estado onde o etanol é mais vantajoso para o menos vantajoso.",
        "Cada barra parte da linha de 70%. Verde, para a esquerda = etanol compensa; cinza, para a direita = gasolina "
        "compensa. Barra longa = vantagem clara.",
        f"Em **{melhor['nome_estado']}** o etanol custa só {ui.num(melhor['razao_pct'], 1)}% da gasolina: "
        "a economia por km é a maior do país.",
    )

c3, c4 = st.columns(2, gap="medium")

serie = metrics.paridade_etanol_gasolina(todos, por=["data"])
with c3:
    fig = go.Figure(
        go.Scatter(
            x=serie["data"],
            y=serie["razao"] * 100,
            mode="lines+markers",
            line=dict(color=ui.COR_CATEGORIA["ETANOL"], width=2.2),
            marker=dict(size=5),
            hovertemplate="%{x|%m/%Y}: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(y=limiar, line_dash="dot", line_color="#f0efec", line_width=1)
    fig.update_xaxes(tickformat="%m/%y")
    fig.update_yaxes(ticksuffix="%")
    abaixo = (serie["razao"] <= metrics.LIMIAR_PARIDADE).mean() * 100
    ui.chart_card(
        "paridade_tempo",
        "A paridade nacional ao longo do tempo",
        ui.estilizar(fig, altura=320, legenda=False),
        "Preço médio nacional do etanol dividido pelo da gasolina, mês a mês.",
        "Abaixo da linha pontilhada (70%) o etanol compensa na média do país.",
        f"Na média nacional, o etanol compensou em **{ui.num(abaixo, 0)}%** dos meses do período: a decisão muda com o "
        "tempo e deve ser revista periodicamente.",
    )

with c4:
    por_uf_mes = metrics.paridade_etanol_gasolina(todos, por=["data", "uf"])
    share = por_uf_mes.groupby("data")["etanol_compensa"].mean().reset_index()
    share["pct"] = share["etanol_compensa"] * 100
    fig = go.Figure(
        go.Bar(
            x=share["data"],
            y=share["pct"],
            marker=dict(color=ui.COR_BOM, cornerradius=3),
            hovertemplate="%{x|%m/%Y}: etanol compensa em %{y:.0f}% dos estados<extra></extra>",
        )
    )
    fig.update_xaxes(tickformat="%m/%y")
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    ui.chart_card(
        "share_paridade",
        "Em quantos estados o etanol compensa, mês a mês",
        ui.estilizar(fig, altura=320, legenda=False),
        "Percentual dos estados selecionados em que o etanol custava até 70% da gasolina em cada mês.",
        "Barra alta = etanol vantajoso em boa parte do país naquele mês.",
        f"No último mês, **{ui.num(share['pct'].iloc[-1], 0)}%** dos estados: a vantagem do etanol é regional, "
        "não nacional.",
    )
