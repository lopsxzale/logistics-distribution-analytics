import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
df = data.aplicar(data.painel_uf(), f)

ui.cabecalho(
    "Gap regional",
    "Quanto mais caro é abastecer na região mais cara do que na mais barata — e se essa distância está "
    "**aumentando** ou **diminuindo**.",
)
if df.empty or len(f.regioes) < 2:
    ui.vazio("Selecione ao menos duas regiões para comparar.")
    st.stop()

gap = metrics.gap_regional(df)
cor = ui.COR_CATEGORIA[f.categoria]
gap_ano = gap.assign(ano=gap["data"].dt.year).groupby("ano")["gap_pct"].mean()

# 1. Evolução do gap
fig = go.Figure(
    go.Scatter(
        x=gap["data"],
        y=gap["gap_pct"],
        mode="lines",
        line=dict(color=cor, width=2.2, shape="spline", smoothing=0.6),
        fill="tozeroy",
        fillcolor=ui.rgba(cor, 0.12),
        customdata=gap[["regiao_mais_cara", "preco_max", "regiao_mais_barata", "preco_min"]],
        hovertemplate="<b>%{x|%m/%Y}: gap %{y:.1f}%</b><br>mais cara: %{customdata[0]} (R$ %{customdata[1]:.2f})"
        "<br>mais barata: %{customdata[2]} (R$ %{customdata[3]:.2f})<extra></extra>",
    )
)
topo = gap["gap_pct"].max()
for ano, valor in gap_ano.items():
    fig.add_annotation(
        x=f"{ano}-07-01",
        y=topo * 1.14,
        text=f"média {ano}: <b>{ui.num(valor, 1)}%</b>",
        showarrow=False,
        font=dict(size=12, color=ui.TINTA_SECUNDARIA),
    )
fig.update_xaxes(tickformat="%m/%y")
fig.update_yaxes(ticksuffix="%", range=[0, topo * 1.22])
tendencia = "aumentou" if gap_ano.iloc[-1] > gap_ano.iloc[0] else "diminuiu"
ui.chart_card(
    "gap_tempo",
    f"O gap entre regiões {tendencia}: {ui.num(gap_ano.iloc[0], 1)}% → {ui.num(gap_ano.iloc[-1], 1)}%",
    ui.estilizar(fig, altura=380, legenda=False),
    "Diferença % entre o preço médio da região mais cara e o da mais barata, mês a mês.",
    "Área mais alta = regiões mais distantes entre si. Passe o mouse para ver quais regiões estão nos extremos em cada mês.",
    f"Com gap de {ui.num(gap['gap_pct'].iloc[-1], 1)}% no último mês, usar **um custo nacional único** em orçamentos de "
    "frete subestima as rotas das regiões mais caras. Precificar por região evita margem negativa.",
)

col1, col2 = st.columns(2, gap="medium")

# 2. Faixa de preços regionais por ano
with col1:
    anual = metrics.media_ponderada(df.assign(ano=df["data"].dt.year.astype(str)), ["ano", "regiao"])
    faixa = anual.groupby("ano")["preco_medio"].agg(["min", "max"]).reset_index()
    fig = go.Figure()
    xs, ys = [], []
    for ano, lo, hi in zip(faixa["ano"], faixa["min"], faixa["max"], strict=True):
        xs += [lo, hi, None]
        ys += [ano, ano, None]
    fig.add_trace(
        go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#45443f", width=6), hoverinfo="skip", showlegend=False)
    )
    for regiao in data.REGIOES:
        r = anual[anual["regiao"] == regiao]
        if r.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=r["preco_medio"],
                y=r["ano"],
                mode="markers",
                name=regiao,
                marker=dict(color=ui.COR_REGIAO[regiao], size=13, line=dict(color="#0d0d0d", width=2)),
                hovertemplate=f"{regiao} %{{y}}: R$ %{{x:.2f}}<extra></extra>",
            )
        )
    fig.update_yaxes(type="category", autorange="reversed", showgrid=False)
    fig.update_xaxes(tickprefix="R$ ", tickformat=".2f", showgrid=True, gridcolor=ui.GRID)
    ultimo_ano = anual[anual["ano"] == anual["ano"].max()].sort_values("preco_medio")
    ui.chart_card(
        "faixa_anual",
        "Onde cada região fica na régua de preço, ano a ano",
        ui.estilizar(fig, altura=320),
        "Preço médio anual de cada região, posicionado sobre a faixa entre a mais barata e a mais cara.",
        "Cada linha é um ano; cada ponto, uma região. Barra cinza mais longa = regiões mais distantes entre si.",
        f"Em {ultimo_ano['ano'].iloc[0]}, **{ultimo_ano.iloc[-1]['regiao']}** ficou no topo e "
        f"**{ultimo_ano.iloc[0]['regiao']}** na base da régua.",
    )

# 3. Spread entre UFs extremas (R$/litro)
with col2:
    uf_mes = metrics.media_ponderada(df, ["data", "uf", "nome_estado"])
    idx_max = uf_mes.groupby("data")["preco_medio"].idxmax()
    idx_min = uf_mes.groupby("data")["preco_medio"].idxmin()
    spread = uf_mes.loc[idx_max, ["data", "nome_estado", "preco_medio"]].merge(
        uf_mes.loc[idx_min, ["data", "nome_estado", "preco_medio"]], on="data", suffixes=("_max", "_min")
    )
    spread["diferenca"] = spread["preco_medio_max"] - spread["preco_medio_min"]
    fig = go.Figure(
        go.Bar(
            x=spread["data"],
            y=spread["diferenca"],
            marker=dict(color=cor, cornerradius=3),
            customdata=spread[["nome_estado_max", "nome_estado_min"]],
            hovertemplate="<b>%{x|%m/%Y}: R$ %{y:.2f}/L</b><br>%{customdata[0]} vs %{customdata[1]}<extra></extra>",
        )
    )
    fig.update_xaxes(tickformat="%m/%y")
    fig.update_yaxes(tickprefix="R$ ", tickformat=".2f")
    medio = spread["diferenca"].mean()
    ui.chart_card(
        "spread_ufs",
        f"Até {ui.brl(spread['diferenca'].max())} por litro entre o estado mais caro e o mais barato",
        ui.estilizar(fig, altura=320, legenda=False),
        "Diferença em R$/litro entre o estado mais caro e o mais barato em cada mês.",
        "Cada barra é um mês. Passe o mouse para ver quais estados estavam nos extremos.",
        f"Na média, **{ui.brl(medio)} por litro**. Para um caminhão que consome 3 mil litros/mês, são "
        f"**{ui.brl(medio * 3000, 0)}/mês** de diferença só pelo estado onde abastece.",
    )
