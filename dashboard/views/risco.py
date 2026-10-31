import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
df = data.aplicar(data.painel_uf(), f)

ui.cabecalho(
    "Risco & volatilidade",
    "Preço alto é um problema; preço **imprevisível** é outro. Aqui separamos as duas coisas para apoiar o "
    "planejamento de rotas, estoque de segurança e orçamento.",
)
if df.empty or df["data"].nunique() < 3:
    ui.vazio("Selecione ao menos 3 meses no período para medir volatilidade.")
    st.stop()

nomes = df.drop_duplicates("uf").set_index("uf")[["nome_estado", "regiao"]]
vol = metrics.volatilidade_temporal(df).join(nomes, on="uf")
disp = metrics.dispersao_postos(df).join(nomes, on="uf")
cor = ui.COR_CATEGORIA[f.categoria]

# 1. Matriz de risco
mx, my = vol["preco_medio"].median(), vol["volatilidade"].median()
fig = px.scatter(
    vol,
    x="preco_medio",
    y="volatilidade",
    color="regiao",
    text="uf",
    color_discrete_map=ui.COR_REGIAO,
    category_orders={"regiao": list(data.REGIOES)},
    custom_data=["nome_estado", "preco_medio", "volatilidade"],
)
fig.update_traces(
    marker=dict(size=13, line=dict(color="#0d0d0d", width=2)),
    textposition="top center",
    textfont=dict(size=11, color=ui.TINTA_SECUNDARIA),
    hovertemplate="<b>%{customdata[0]}</b><br>preço médio R$ %{customdata[1]:.2f}"
    "<br>volatilidade ±%{customdata[2]:.2f}%/mês<extra></extra>",
)
fig.add_vline(x=mx, line_dash="dot", line_color="#5c5b57", line_width=1)
fig.add_hline(y=my, line_dash="dot", line_color="#5c5b57", line_width=1)
for texto, xa, ya, xan, yan in [
    ("CARO E INSTÁVEL", 0.99, 0.99, "right", "top"),
    ("BARATO E INSTÁVEL", 0.01, 0.99, "left", "top"),
    ("CARO E ESTÁVEL", 0.99, 0.01, "right", "bottom"),
    ("BARATO E ESTÁVEL", 0.01, 0.01, "left", "bottom"),
]:
    fig.add_annotation(
        text=texto,
        xref="paper",
        yref="paper",
        x=xa,
        y=ya,
        xanchor=xan,
        yanchor=yan,
        showarrow=False,
        font=dict(size=10, color="#6b6a65"),
    )
span_x = vol["preco_medio"].max() - vol["preco_medio"].min()
span_y = vol["volatilidade"].max() - vol["volatilidade"].min()
fig.update_xaxes(
    tickprefix="R$ ",
    tickformat=".2f",
    title_text="Preço médio no período",
    showgrid=True,
    gridcolor=ui.GRID,
    range=[vol["preco_medio"].min() - 0.06 * span_x, vol["preco_medio"].max() + 0.06 * span_x],
)
fig.update_yaxes(
    ticksuffix="%",
    title_text="Volatilidade mensal",
    range=[vol["volatilidade"].min() - 0.12 * span_y, vol["volatilidade"].max() + 0.2 * span_y],
)
criticos = vol[(vol["preco_medio"] > mx) & (vol["volatilidade"] > my)].sort_values("volatilidade", ascending=False)
lista = ", ".join(criticos["nome_estado"].head(4)) if not criticos.empty else "nenhum estado"
ui.chart_card(
    "matriz_risco",
    "Matriz de risco: nível de preço × instabilidade",
    ui.estilizar(fig, altura=520),
    "Cada ponto é um estado: no eixo horizontal, o preço médio; no vertical, o quanto o preço oscila de um mês para o outro.",
    "As linhas pontilhadas são as medianas e dividem quatro quadrantes. Canto superior direito = caro **e** imprevisível.",
    f"No quadrante crítico estão **{lista}**. Rotas que dependem desses estados pedem estoque de segurança, "
    "contratos com preço fixo ou orçamento com folga maior.",
)

col1, col2 = st.columns(2, gap="medium")

with col1:
    v = vol.sort_values("volatilidade")
    fig = go.Figure(
        go.Bar(
            x=v["volatilidade"],
            y=v["nome_estado"],
            orientation="h",
            marker=dict(color=cor, cornerradius=4),
            text=[f"±{ui.num(x, 2)}%" for x in v["volatilidade"]],
            textposition="outside",
            textfont=dict(color=ui.TINTA_SECUNDARIA, size=11),
            cliponaxis=False,
            hovertemplate="%{y}: ±%{x:.2f}% ao mês<extra></extra>",
        )
    )
    fig.update_xaxes(ticksuffix="%", range=[0, v["volatilidade"].max() * 1.25])
    fig.update_yaxes(tickfont_size=11)
    topo = vol.iloc[0]
    ui.chart_card(
        "volatilidade",
        f"{topo['nome_estado']} tem o preço mais instável",
        ui.estilizar(fig, altura=max(300, 21 * len(v) + 40), legenda=False),
        "Volatilidade temporal: desvio padrão da variação % do preço médio de um mês para o outro.",
        "Barra maior = preço que 'balança' mais. ±2% significa que, em um mês típico, o preço sobe ou cai cerca de 2%.",
        f"Em **{topo['nome_estado']}** a oscilação típica é de **±{ui.num(topo['volatilidade'], 2)}% ao mês**, "
        f"contra ±{ui.num(my, 2)}% na mediana: o custo por km é mais difícil de prever.",
    )

with col2:
    d = disp.sort_values("dispersao")
    fig = go.Figure(
        go.Bar(
            x=d["dispersao"],
            y=d["nome_estado"],
            orientation="h",
            marker=dict(color="#9085e9", cornerradius=4),
            text=[f"{ui.num(x, 1)}%" for x in d["dispersao"]],
            textposition="outside",
            textfont=dict(color=ui.TINTA_SECUNDARIA, size=11),
            cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f}% de variação entre postos<extra></extra>",
        )
    )
    fig.update_xaxes(ticksuffix="%", range=[0, d["dispersao"].max() * 1.2])
    fig.update_yaxes(tickfont_size=11)
    topo_d = disp.iloc[0]
    ui.chart_card(
        "dispersao",
        f"Em {topo_d['nome_estado']}, escolher o posto faz mais diferença",
        ui.estilizar(fig, altura=max(300, 21 * len(d) + 40), legenda=False),
        "Dispersão entre postos: coeficiente de variação dos preços coletados no mesmo estado e no mesmo mês.",
        "Barra maior = preços muito diferentes entre postos vizinhos no mesmo mês.",
        f"Onde a dispersão é alta (**{topo_d['nome_estado']}**: {ui.num(topo_d['dispersao'], 1)}%), "
        "credenciar postos parceiros ou usar cartão-frota com rede negociada gera economia direta.",
    )

var = metrics.variacoes_mensais(df, "uf").dropna(subset=["var_pct"])
media_var = var["var_pct"].mean()
caudas = (var["var_pct"].abs() > 5).mean() * 100
fig = go.Figure(
    go.Histogram(
        x=var["var_pct"],
        nbinsx=50,
        marker=dict(color=cor, line=dict(color="#0d0d0d", width=1)),
        hovertemplate="%{x}%: %{y} ocorrências<extra></extra>",
    )
)
fig.add_vline(x=0, line_color="#5c5b57", line_width=1)
fig.add_vline(
    x=media_var,
    line_dash="dot",
    line_color="#f0efec",
    line_width=1,
    annotation_text=f"média {ui.pct(media_var, 2, sinal=True)}",
    annotation_font_color=ui.TINTA_SECUNDARIA,
)
fig.update_xaxes(ticksuffix="%", title_text="Variação em relação ao mês anterior")
fig.update_yaxes(title_text="Estado × mês")
ui.chart_card(
    "histograma",
    "Como os reajustes mensais se distribuem",
    ui.estilizar(fig, altura=340, legenda=False),
    "Todas as variações mensais de preço (cada estado em cada mês) agrupadas em faixas.",
    "Picos perto de 0 = meses estáveis. As caudas mostram os choques: reajustes grandes para cima ou para baixo.",
    f"**{ui.num(caudas, 1)}%** das observações tiveram variação acima de 5% (para mais ou para menos) em um único mês: "
    "é a frequência de choques que o planejamento precisa absorver.",
)
