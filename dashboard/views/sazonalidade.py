import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
df = data.aplicar(data.painel_uf(), f)

ui.cabecalho(
    "Sazonalidade",
    f"Existe época certa para comprar **{f.rotulo.lower()}**? Padrões que se repetem ao longo do ano ajudam a "
    "programar compras, contratos e estoques.",
)
if df.empty or df["data"].nunique() < 6:
    ui.vazio("Selecione ao menos 6 meses no período para analisar sazonalidade.")
    st.stop()

nac = metrics.serie_nacional(df)
nac["ano"] = nac["data"].dt.year
nac["mes"] = nac["data"].dt.month
idx = metrics.indice_sazonal(df)
pico = idx.loc[idx["indice_medio"].idxmax()]
vale = idx.loc[idx["indice_medio"].idxmin()]
mes_pico, mes_vale = ui.MESES[int(pico["mes"]) - 1], ui.MESES[int(vale["mes"]) - 1]

# 1. Índice sazonal com destaque no pico e no vale
cores = [ui.COR_RUIM if m == pico["mes"] else ui.COR_BOM if m == vale["mes"] else ui.COR_NEUTRA for m in idx["mes"]]
fig = go.Figure(
    go.Bar(
        x=[ui.MESES[m - 1] for m in idx["mes"]],
        y=idx["indice_medio"] - 100,
        base=100,
        marker=dict(color=cores, cornerradius=4),
        error_y=dict(
            type="data",
            symmetric=False,
            array=idx["indice_max"] - idx["indice_medio"],
            arrayminus=idx["indice_medio"] - idx["indice_min"],
            color="#898781",
            thickness=1.2,
            width=4,
        ),
        customdata=idx[["indice_min", "indice_max", "n_anos"]],
        hovertemplate="<b>%{x}</b><br>índice médio %{y:.1f}<br>faixa %{customdata[0]:.1f}–%{customdata[1]:.1f}"
        " (%{customdata[2]} anos)<extra></extra>",
    )
)
fig.add_hline(y=100, line_color="#5c5b57", line_width=1)
fig.update_yaxes(title_text="Índice (média do ano = 100)")
n_anos = int(idx["n_anos"].max())
consistente = vale["indice_max"] < 100 and pico["indice_min"] > 100
ressalva = (
    f"Em todos os {n_anos} anos, {mes_vale} ficou abaixo e {mes_pico} acima da média: padrão consistente."
    if consistente
    else f"Atenção: com {n_anos} ano(s) de dados, o traço de {mes_vale} ou {mes_pico} cruza a linha de 100 — "
    "um evento pontual pesa na média. Trate como indicativo, não como regra."
)
ui.chart_card(
    "indice_sazonal",
    f"{mes_vale.capitalize()} é o mês mais barato; {mes_pico}, o mais caro",
    ui.estilizar(fig, altura=380, legenda=False),
    "Preço de cada mês relativo à média do próprio ano (=100), na média dos anos completos do período.",
    "Barras acima de 100 = mês mais caro que a média do ano; abaixo = mais barato. "
    "O traço vai do menor ao maior valor observado entre os anos: traço curto = padrão que se repete. " + ressalva,
    f"A diferença média entre **{mes_pico}** e **{mes_vale}** é de "
    f"**{ui.num(pico['indice_medio'] - vale['indice_medio'], 1)}%**. Antecipar compras ou travar preço antes do pico "
    "protege a margem da operação.",
)

col1, col2 = st.columns(2, gap="medium")

# 2. Heatmap mês x ano
with col1:
    matriz = nac.pivot_table(index="ano", columns="mes", values="preco_medio")
    fig = go.Figure(
        go.Heatmap(
            z=matriz.values,
            x=[ui.MESES[m - 1] for m in matriz.columns],
            y=[str(a) for a in matriz.index],
            colorscale=ui.ESCALA_SEQUENCIAL,
            xgap=2,
            ygap=2,
            texttemplate="%{z:.2f}",
            textfont=dict(size=11),
            showscale=False,
            hovertemplate="%{x}/%{y}: R$ %{z:.2f}<extra></extra>",
        )
    )
    fig.update_yaxes(autorange="reversed", showgrid=False, type="category")
    fig.update_xaxes(showgrid=False, side="top")
    ui.chart_card(
        "heatmap_mes_ano",
        "Calendário de preços",
        ui.estilizar(fig, altura=max(220, 70 * len(matriz) + 60), legenda=False),
        "Preço médio nacional (R$/litro) em cada mês de cada ano.",
        "Cada linha é um ano. Cor mais clara = mais caro. Compare colunas para ver se o mesmo mês se repete caro ou barato.",
        "Mostra ao mesmo tempo a **tendência** (anos mais claros ou escuros) e a **sazonalidade** (colunas que se destacam).",
    )

# 3. Distribuição das variações mensais por mês-calendário
with col2:
    var = metrics.variacoes_mensais(df, "uf").dropna(subset=["var_pct"])
    var["mes"] = var["data"].dt.month
    medianas = var.groupby("mes")["var_pct"].median()
    mes_alta = ui.MESES[int(medianas.idxmax()) - 1]
    fig = go.Figure(
        go.Box(
            x=[ui.MESES[m - 1] for m in var["mes"]],
            y=var["var_pct"],
            marker=dict(color=ui.COR_CATEGORIA[f.categoria], size=3, opacity=0.5),
            line=dict(width=1.5),
            fillcolor="rgba(0,0,0,0)",
            boxpoints="outliers",
            hovertemplate="%{x}: %{y:+.1f}%<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_color="#5c5b57", line_width=1)
    fig.update_xaxes(categoryorder="array", categoryarray=ui.MESES)
    fig.update_yaxes(ticksuffix="%")
    ui.chart_card(
        "box_variacoes",
        f"Em {mes_alta} os reajustes costumam ser maiores",
        ui.estilizar(fig, altura=max(220, 70 * len(matriz) + 60), legenda=False),
        "Distribuição da variação % do preço de um mês para o outro, em todos os estados selecionados.",
        "A caixa concentra metade dos estados; a linha do meio é a mediana. Acima de 0 = aumento em relação ao mês anterior.",
        f"**{mes_alta.capitalize()}** tem a maior variação mediana ({ui.pct(medianas.max(), sinal=True)}): "
        "é o mês para revisar tabelas de frete e reajustes de contrato.",
    )
