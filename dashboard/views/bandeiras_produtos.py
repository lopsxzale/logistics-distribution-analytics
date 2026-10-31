import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
dfb = data.aplicar(data.painel_bandeira(), f)
dfp = data.aplicar(data.painel_produto(), f, por_categoria=False)

ui.cabecalho(
    "Bandeiras & produtos",
    "Vale pagar pela bandeira? E pelo diesel S10 ou pela gasolina aditivada? O prêmio cobrado em cada caso, "
    "medido nas coletas da ANP.",
)
if dfb.empty:
    ui.vazio()
    st.stop()

COR_BANDEIRA = {
    "VIBRA": "#3987e5",
    "IPIRANGA": "#d95926",
    "RAIZEN": "#199e70",
    "ALESAT": "#c98500",
    "OUTRAS": "#d55181",
    "BRANCA": "#898781",
}
ROTULO_BANDEIRA = {
    "VIBRA": "Vibra (BR)",
    "IPIRANGA": "Ipiranga",
    "RAIZEN": "Raízen (Shell)",
    "ALESAT": "Alesat",
    "OUTRAS": "Outras",
    "BRANCA": "Bandeira branca",
}

col1, col2 = st.columns(2, gap="medium")

ranking = metrics.media_ponderada(dfb, ["bandeira"])
preco_branca = ranking.loc[ranking["bandeira"] == "BRANCA", "preco_medio"]
ref = float(preco_branca.iloc[0]) if not preco_branca.empty else ranking["preco_medio"].mean()
ranking["dif_pct"] = (ranking["preco_medio"] / ref - 1) * 100
ranking["share"] = ranking["n_amostras"] / ranking["n_amostras"].sum() * 100
ranking = ranking.sort_values("preco_medio")
ranking["rotulo"] = ranking["bandeira"].map(ROTULO_BANDEIRA)

with col1:
    fig = go.Figure(
        go.Bar(
            x=ranking["dif_pct"],
            y=ranking["rotulo"],
            orientation="h",
            marker=dict(color=[COR_BANDEIRA[b] for b in ranking["bandeira"]], cornerradius=4),
            text=[
                f"{ui.pct(d, sinal=True)} · {ui.brl(p)}"
                for p, d in zip(ranking["preco_medio"], ranking["dif_pct"], strict=True)
            ],
            textposition="outside",
            textfont=dict(color=ui.TINTA_SECUNDARIA, size=11),
            cliponaxis=False,
            customdata=ranking[["preco_medio", "share"]],
            hovertemplate="<b>%{y}</b><br>R$ %{customdata[0]:.3f}/L<br>%{customdata[1]:.1f}% das coletas"
            "<extra></extra>",
        )
    )
    alcance = max(ranking["dif_pct"].abs().max(), 0.5)
    fig.update_xaxes(
        ticksuffix="%",
        zeroline=True,
        zerolinecolor="#45443f",
        range=[min(ranking["dif_pct"].min(), 0) - alcance * 0.1, ranking["dif_pct"].max() + alcance * 0.7],
    )
    cara = ranking.iloc[-1]
    ui.chart_card(
        "bandeiras",
        f"{cara['rotulo']} cobra {ui.pct(cara['dif_pct'], sinal=True)} sobre os postos de bandeira branca",
        ui.estilizar(fig, altura=340, legenda=False),
        f"Quanto o {f.rotulo.lower()} custa a mais em cada bandeira, comparado aos postos sem bandeira (bandeira branca).",
        "Barra = diferença % sobre a bandeira branca (que fica em 0%). Ao lado, o preço médio em R$/litro.",
        "Postos de bandeira branca costumam ser os mais baratos. Para frota própria, credenciar postos independentes "
        "confiáveis reduz custo sem mudar a rota.",
    )

with col2:
    serie = metrics.media_ponderada(dfb, ["data", "bandeira"])
    branca = serie[serie["bandeira"] == "BRANCA"].set_index("data")["preco_medio"]
    serie = serie[~serie["bandeira"].isin(["BRANCA", "OUTRAS"])].copy()
    serie["premio"] = (serie["preco_medio"] / serie["data"].map(branca) - 1) * 100
    serie["rotulo"] = serie["bandeira"].map(ROTULO_BANDEIRA)
    fig = px.line(
        serie.dropna(subset=["premio"]),
        x="data",
        y="premio",
        color="rotulo",
        color_discrete_map={ROTULO_BANDEIRA[b]: c for b, c in COR_BANDEIRA.items()},
        custom_data=["rotulo"],
    )
    fig.update_traces(line_width=2, hovertemplate="%{customdata[0]}: %{y:+.1f}%<extra></extra>")
    fig.add_hline(y=0, line_color="#5c5b57", line_width=1)
    fig.update_xaxes(tickformat="%m/%y")
    fig.update_yaxes(ticksuffix="%")
    ui.chart_card(
        "premio_bandeiras",
        "O prêmio das grandes bandeiras ao longo do tempo",
        ui.estilizar(fig, altura=340, hover_unificado=True),
        "Quanto cada grande bandeira cobrou acima (ou abaixo) dos postos de bandeira branca, mês a mês.",
        "Linha em 0 = mesmo preço da bandeira branca. Acima = mais caro.",
        "Um prêmio estável indica estratégia de preço; picos isolados indicam repasses mais rápidos de reajustes.",
    )

ui.secao(
    "Produtos premium", "Diesel S10 vs diesel comum e gasolina aditivada vs comum (independe do filtro de combustível)."
)
c3, c4 = st.columns(2, gap="medium")

for coluna, chave, premium, base, nome, nome_base, cor, contexto in [
    (
        c3,
        "s10",
        "DIESEL S10",
        "DIESEL",
        "o diesel S10",
        "o diesel comum",
        ui.COR_CATEGORIA["DIESEL"],
        "O S10 é obrigatório para caminhões a partir da fase P7 do Proconve (2012+): para a maioria da frota moderna, "
        "não é opcional — é custo fixo a orçar.",
    ),
    (
        c4,
        "aditivada",
        "GASOLINA ADITIVADA",
        "GASOLINA",
        "a gasolina aditivada",
        "a gasolina comum",
        ui.COR_CATEGORIA["GASOLINA"],
        "Para frota leve, a aditivada raramente se paga no consumo: o prêmio é custo extra a justificar.",
    ),
]:
    with coluna:
        p = metrics.premio_produto(dfp, premium=premium, base=base)
        if p.empty:
            ui.vazio()
            continue
        fig = go.Figure(
            go.Scatter(
                x=p["data"],
                y=p["premio_pct"],
                mode="lines",
                line=dict(color=cor, width=2.2),
                fill="tozeroy",
                fillcolor=ui.rgba(cor, 0.12),
                customdata=p["premio_rs"],
                hovertemplate="%{x|%m/%Y}: %{y:+.2f}% (R$ %{customdata:.3f}/L)<extra></extra>",
            )
        )
        fig.update_xaxes(tickformat="%m/%y")
        fig.update_yaxes(ticksuffix="%", rangemode="tozero")
        ui.chart_card(
            f"premio_{chave}",
            f"{nome[2:].capitalize()} custa em média {ui.pct(p['premio_pct'].mean(), 2, sinal=True)} a mais",
            ui.estilizar(fig, altura=300, legenda=False),
            f"Diferença % entre o preço médio d{nome} e d{nome_base}, mês a mês.",
            f"Área mais alta = prêmio maior. Passe o mouse para ver o valor em R$/litro "
            f"(média {ui.brl(p['premio_rs'].mean(), 3)}).",
            contexto,
        )
