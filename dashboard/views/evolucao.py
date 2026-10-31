import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
painel = data.painel_uf()
df = data.aplicar(painel, f)

ui.cabecalho(
    "Evolução de preços",
    f"Como o preço do **{f.rotulo.lower()}** se moveu entre {ui.mes_ano(f.inicio)} e {ui.mes_ano(f.fim)}, "
    "por região e por estado.",
)
if df.empty:
    ui.vazio()
    st.stop()

# 1. Linhas por região
reg = metrics.media_ponderada(df, ["data", "regiao"])
fig = px.line(
    reg,
    x="data",
    y="preco_medio",
    color="regiao",
    color_discrete_map=ui.COR_REGIAO,
    category_orders={"regiao": list(data.REGIOES)},
    custom_data=["regiao"],
)
fig.update_traces(line_width=2.2, hovertemplate="%{customdata[0]}: R$ %{y:.2f}<extra></extra>")
fig.update_xaxes(tickformat="%m/%y")
fig.update_yaxes(tickprefix="R$ ", tickformat=".2f")
ultimo = reg[reg["data"] == reg["data"].max()].sort_values("preco_medio")
ui.chart_card(
    "regioes",
    f"{ultimo.iloc[-1]['regiao']} lidera o preço do {f.rotulo.lower()} no fim do período",
    ui.estilizar(fig, altura=400, hover_unificado=True),
    "Preço médio mensal de cada região, ponderado pelo número de coletas de cada estado.",
    "Cada linha é uma região; a distância vertical entre elas é a diferença de preço em R$/litro naquele mês.",
    f"No último mês, **{ultimo.iloc[-1]['regiao']}** ({ui.brl(ultimo.iloc[-1]['preco_medio'])}) e "
    f"**{ultimo.iloc[0]['regiao']}** ({ui.brl(ultimo.iloc[0]['preco_medio'])}) estão nos extremos. "
    "Linhas que andam juntas indicam choques nacionais (refinaria, impostos); separações indicam custo logístico local.",
)

col1, col2 = st.columns(2, gap="medium")

# 2. Índice base 100 comparando os combustíveis
with col1:
    todos = data.aplicar(painel, f, por_categoria=False)
    idx = metrics.indice_base_100(todos, "categoria")
    idx["combustivel"] = idx["categoria"].map(data.ROTULO)
    fig = px.line(
        idx,
        x="data",
        y="indice",
        color="combustivel",
        color_discrete_map={data.ROTULO[k]: v for k, v in ui.COR_CATEGORIA.items()},
        category_orders={"combustivel": [data.ROTULO[c] for c in data.CATEGORIAS]},
        custom_data=["combustivel", "preco_medio"],
    )
    fig.update_traces(
        line_width=2.2, hovertemplate="%{customdata[0]}: %{y:.1f} (R$ %{customdata[1]:.2f})<extra></extra>"
    )
    fig.add_hline(y=100, line_dash="dot", line_color="#5c5b57", line_width=1)
    fig.update_xaxes(tickformat="%m/%y")
    finais = idx.sort_values("data").groupby("combustivel").tail(1).sort_values("indice")
    ui.chart_card(
        "base100",
        "Qual combustível subiu (ou caiu) mais?",
        ui.estilizar(fig, altura=380, hover_unificado=True),
        f"Preço de cada combustível relativo ao seu valor em {ui.mes_ano(f.inicio)} (=100).",
        "Acima de 100 = mais caro que no início; abaixo = mais barato. Ex.: 105 significa alta de 5%.",
        f"**{finais.iloc[-1]['combustivel']}** terminou em {ui.num(finais.iloc[-1]['indice'], 1)} e "
        f"**{finais.iloc[0]['combustivel']}** em {ui.num(finais.iloc[0]['indice'], 1)}: trajetórias diferentes "
        "mudam a atratividade de frota flex ou a diesel.",
    )

# 3. Dumbbell início vs fim por UF
with col2:
    serie_uf = metrics.media_ponderada(df, ["uf", "nome_estado", "data"])
    pontas = (
        serie_uf.sort_values("data")
        .groupby("uf", observed=True)
        .agg(nome=("nome_estado", "first"), inicio=("preco_medio", "first"), fim=("preco_medio", "last"))
    )
    pontas["var"] = (pontas["fim"] / pontas["inicio"] - 1) * 100
    pontas = pontas.sort_values("var").reset_index()
    cor_fim = ui.COR_CATEGORIA[f.categoria]
    xs, ys = [], []
    for uf, ini, fim in zip(pontas["uf"], pontas["inicio"], pontas["fim"], strict=True):
        xs += [ini, fim, None]
        ys += [uf, uf, None]
    fig = go.Figure(
        go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#45443f", width=2), hoverinfo="skip", showlegend=False)
    )
    fig.add_trace(
        go.Scatter(
            x=pontas["inicio"],
            y=pontas["uf"],
            mode="markers",
            name=ui.mes_ano(f.inicio),
            marker=dict(color=ui.COR_NEUTRA, size=9),
            hovertemplate="%{y}: R$ %{x:.2f}<extra>início</extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=pontas["fim"],
            y=pontas["uf"],
            mode="markers",
            name=ui.mes_ano(f.fim),
            marker=dict(color=cor_fim, size=10, line=dict(color="#0d0d0d", width=2)),
            customdata=pontas["var"],
            hovertemplate="%{y}: R$ %{x:.2f} (%{customdata:+.1f}%)<extra>fim</extra>",
        )
    )
    fig.update_xaxes(tickprefix="R$ ", tickformat=".2f", showgrid=True, gridcolor=ui.GRID)
    fig.update_yaxes(showgrid=False, tickfont_size=11)
    caiu = int((pontas["var"] < 0).sum())
    ui.chart_card(
        "dumbbell",
        f"{caiu} de {len(pontas)} estados terminaram o período mais baratos",
        ui.estilizar(fig, altura=380 if len(pontas) < 14 else 560),
        "Preço de cada estado no primeiro e no último mês do filtro, ligados por uma linha.",
        "Ponto cinza = início, ponto colorido = fim. Linha longa = grande variação. Maior alta no topo, maior queda na base.",
        f"Maior queda: **{pontas.iloc[0]['nome']}** ({ui.pct(pontas.iloc[0]['var'], sinal=True)}); "
        f"maior alta: **{pontas.iloc[-1]['nome']}** ({ui.pct(pontas.iloc[-1]['var'], sinal=True)}). "
        "Bom ponto de partida para revisar custos de rotas por estado.",
    )

# 4. Heatmap UF x mês
ordem = (
    metrics.media_ponderada(df, ["uf", "regiao"])
    .assign(ordem_regiao=lambda d: d["regiao"].astype(str).map({r: i for i, r in enumerate(data.REGIOES)}))
    .sort_values(["ordem_regiao", "preco_medio"], ascending=[True, False])["uf"]
    .tolist()
)
matriz = serie_uf.pivot_table(index="uf", columns="data", values="preco_medio", observed=True).reindex(ordem)
fig = go.Figure(
    go.Heatmap(
        z=matriz.values,
        x=matriz.columns,
        y=matriz.index,
        colorscale=ui.ESCALA_SEQUENCIAL,
        xgap=1,
        ygap=1,
        colorbar=dict(thickness=10, tickprefix="R$ ", tickformat=".2f", tickfont_color="#898781"),
        hovertemplate="%{y} · %{x|%m/%Y}<br>R$ %{z:.2f}<extra></extra>",
    )
)
fig.update_xaxes(tickformat="%m/%y", showgrid=False)
fig.update_yaxes(autorange="reversed", showgrid=False, tickfont_size=11)
ui.chart_card(
    "heatmap_uf",
    "Mapa de calor: todos os estados, todos os meses",
    ui.estilizar(fig, altura=max(320, 22 * len(ordem) + 60), legenda=False),
    "Preço médio de cada estado (linhas) em cada mês (colunas).",
    "Cor mais clara = mais caro. Estados agrupados por região (Norte no topo) e, dentro dela, do mais caro ao mais barato. "
    "Faixas verticais indicam movimentos nacionais; linhas que destoam indicam fatores locais.",
    "Permite achar de relance **quando** e **onde** o preço fugiu do padrão, sem precisar abrir 27 gráficos.",
)
