import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

f = data.filtros()
df = data.aplicar(data.painel_uf(), f)
m = data.meta()

ui.cabecalho(
    "Quanto custa abastecer o Brasil?",
    f"**{ui.num(m['registros'] / 1e6, 1)} milhões** de preços coletados pela ANP em {m['municipios']} municípios, "
    "analisados sob a ótica de quem planeja rotas, frota e estoque em uma operação de distribuição.",
    chips=[f.rotulo, f"{ui.mes_ano(f.inicio)} → {ui.mes_ano(f.fim)}", f"{len(f.regioes)} de 5 regiões", "Fonte: ANP"],
)

if df.empty:
    ui.vazio()
    st.stop()

nac = metrics.serie_nacional(df)
ultimo_mes = nac["data"].iloc[-1]
atual = nac["preco_medio"].iloc[-1]
anterior = nac["preco_medio"].iloc[-2] if len(nac) > 1 else atual
inicial = nac["preco_medio"].iloc[0]

uf_atual = metrics.media_ponderada(df[df["data"] == ultimo_mes], ["uf", "nome_estado", "regiao"])
uf_atual["dif_pct"] = (uf_atual["preco_medio"] / atual - 1) * 100
uf_atual = uf_atual.sort_values("preco_medio")
mais_cara, mais_barata = uf_atual.iloc[-1], uf_atual.iloc[0]
gap = metrics.gap_regional(df)

serie_cara = metrics.media_ponderada(df[df["uf"] == mais_cara["uf"]], ["data"]).sort_values("data")
variacao_mensal = (nac["preco_medio"].pct_change() * 100).dropna().round(2).tolist()

c1, c2, c3, c4 = st.columns(4)
ui.kpi(
    c1,
    f"{f.rotulo} · média {ui.mes_ano(ultimo_mes)}",
    ui.brl(atual),
    f"{ui.pct(metrics.variacao_pct(atual, anterior), sinal=True)} no mês",
    delta_color="inverse",
    chart_data=nac["preco_medio"].round(3).tolist(),
    chart_type="area",
)
ui.kpi(
    c2,
    "Variação no período",
    ui.pct(metrics.variacao_pct(atual, inicial), sinal=True),
    f"{ui.brl(inicial)} → {ui.brl(atual)}",
    # O delta é texto (sem sinal), então o Streamlit o trata como positivo: queda de preço = verde.
    delta_color="inverse" if atual >= inicial else "normal",
    delta_arrow="up" if atual >= inicial else "down",
    chart_data=variacao_mensal or [0.0],
    chart_type="bar",
)
ui.kpi(
    c3,
    "Estado mais caro",
    mais_cara["nome_estado"],
    f"{ui.brl(mais_cara['preco_medio'])} · {ui.pct(mais_cara['dif_pct'], sinal=True)} vs média",
    delta_color="inverse",
    chart_data=serie_cara["preco_medio"].round(3).tolist(),
    chart_type="area",
)
ui.kpi(
    c4,
    "Gap entre regiões",
    ui.pct(gap["gap_pct"].iloc[-1]),
    f"{ui.num(gap['gap_pct'].iloc[-1] - gap['gap_pct'].iloc[0], 1)} p.p. no período",
    delta_color="inverse",
    chart_data=gap["gap_pct"].round(2).tolist(),
    chart_type="line",
)

col_mapa, col_rank = st.columns([3, 2], gap="medium")

with col_mapa:
    # Satura a cor no percentil 90 para que um outlier (ex.: Acre) não deixe os demais estados todos cinza.
    limite = max(float(uf_atual["dif_pct"].abs().quantile(0.9)), 1.0)
    uf_atual["hover"] = [
        f"<b>{n}</b><br>{ui.brl(p)}/L<br>{ui.pct(d, sinal=True)} vs média"
        for n, p, d in zip(uf_atual["nome_estado"], uf_atual["preco_medio"], uf_atual["dif_pct"], strict=True)
    ]
    fig = ui.mapa_coropletico(
        uf_atual, data.contornos_estados(), "dif_pct", "hover", ui.ESCALA_DIVERGENTE, (-limite, limite)
    )
    ui.chart_card(
        "mapa",
        f"Onde o {f.rotulo.lower()} pesa mais no caixa — {ui.mes_ano(ultimo_mes)}",
        ui.estilizar(fig, altura=470, legenda=False),
        f"O preço médio de cada estado comparado à média nacional de **{ui.brl(atual)}** no último mês do filtro.",
        f"Vermelho = acima da média, azul = abaixo; a cor satura em ±{ui.num(limite, 0)}%. "
        "Passe o mouse sobre um estado para ver o valor exato.",
        f"**{mais_cara['nome_estado']}** paga {ui.pct(mais_cara['dif_pct'], sinal=True)} e "
        f"**{mais_barata['nome_estado']}** {ui.pct(mais_barata['dif_pct'], sinal=True)} em relação à média: "
        "rotas que cruzam estados permitem planejar onde abastecer.",
    )

with col_rank:
    todos = len(uf_atual) <= 12
    extremos = uf_atual if todos else pd.concat([uf_atual.head(6), uf_atual.tail(6)])
    cores = [ui.COR_RUIM if v > 0 else ui.COR_DESTAQUE for v in extremos["dif_pct"]]
    fig = go.Figure(
        go.Bar(
            x=extremos["dif_pct"],
            y=extremos["nome_estado"],
            orientation="h",
            marker=dict(color=cores, cornerradius=4),
            text=[ui.pct(v, sinal=True) for v in extremos["dif_pct"]],
            textposition="outside",
            textfont=dict(color=ui.TINTA_SECUNDARIA, size=12),
            customdata=extremos["preco_medio"],
            hovertemplate="<b>%{y}</b><br>%{customdata:.2f} R$/L<extra></extra>",
            cliponaxis=False,
        )
    )
    folga = extremos["dif_pct"].abs().max() * 0.35
    fig.update_xaxes(
        ticksuffix="%",
        zeroline=True,
        zerolinecolor="#45443f",
        range=[min(extremos["dif_pct"].min(), 0) - folga, max(extremos["dif_pct"].max(), 0) + folga],
    )
    ui.chart_card(
        "ranking",
        "Estados selecionados vs média" if todos else "Os 6 mais caros e os 6 mais baratos",
        ui.estilizar(fig, altura=470, legenda=False),
        "Distância de cada estado em relação à média nacional" + ("." if todos else ", só nos extremos do ranking."),
        "Barras à direita (vermelho) = mais caro que a média; à esquerda (azul) = mais barato.",
        f"Entre o mais caro e o mais barato há **{ui.brl(mais_cara['preco_medio'] - mais_barata['preco_medio'])} "
        "por litro**: em uma carreta que roda 10 mil km/mês, isso muda o custo em milhares de reais.",
    )

ui.secao("Principais achados", "Calculados ao vivo para o combustível, período e regiões selecionados.")
a1, a2, a3, a4 = st.columns(4)

regioes = metrics.media_ponderada(df, ["regiao"]).sort_values("preco_medio")
with a1:
    cara, barata = regioes.iloc[-1], regioes.iloc[0]
    ui.achado(
        ui.pct(metrics.variacao_pct(cara["preco_medio"], barata["preco_medio"]), sinal=True),
        f"{cara['regiao']} é a região mais cara",
        f"Média de {ui.brl(cara['preco_medio'])} contra {ui.brl(barata['preco_medio'])} no {barata['regiao']}.",
        ui.COR_REGIAO.get(cara["regiao"], ui.COR_DESTAQUE),
    )

sazonal = metrics.indice_sazonal(df)
with a2:
    if len(sazonal) >= 6:
        pico = sazonal.loc[sazonal["indice_medio"].idxmax()]
        vale = sazonal.loc[sazonal["indice_medio"].idxmin()]
        ui.achado(
            ui.pct(pico["indice_medio"] - vale["indice_medio"]),
            f"de diferença entre {ui.MESES[int(pico['mes']) - 1]} e {ui.MESES[int(vale['mes']) - 1]}",
            f"**{ui.MESES[int(vale['mes']) - 1].capitalize()}** costuma ser o mês mais barato: "
            "janela para negociar contratos e reforçar estoque.",
            ui.COR_BOM,
        )
    else:
        ui.achado("—", "Sazonalidade", "Selecione ao menos 6 meses para estimar o padrão sazonal.", ui.COR_NEUTRA)

vol = metrics.volatilidade_temporal(df)
with a3:
    if not vol.empty:
        topo = vol.iloc[0]
        nome = data.painel_uf().drop_duplicates("uf").set_index("uf").loc[topo["uf"], "nome_estado"]
        mediana = vol["volatilidade"].median()
        ui.achado(
            f"±{ui.pct(topo['volatilidade'])}",
            f"{nome}: o preço mais instável",
            f"Variação típica de um mês para o outro, **{ui.num(topo['volatilidade'] / mediana, 1)}×** a mediana "
            "dos estados: exige margem de segurança no orçamento.",
            ui.COR_RUIM,
        )
    else:
        ui.achado("—", "Volatilidade", "Selecione ao menos 3 meses para medir a volatilidade.", ui.COR_NEUTRA)

with a4:
    gap_ano = gap.assign(ano=gap["data"].dt.year).groupby("ano")["gap_pct"].mean()
    inicio_gap, fim_gap = gap_ano.iloc[0], gap_ano.iloc[-1]
    subiu = fim_gap > inicio_gap
    ui.achado(
        f"{ui.num(inicio_gap, 1)}% → {ui.num(fim_gap, 1)}%",
        "Gap regional " + ("em alta" if subiu else "em queda"),
        f"Diferença média entre a região mais cara e a mais barata de {gap_ano.index[0]} a {gap_ano.index[-1]}"
        + (": a desigualdade regional de preço está aumentando." if subiu else ": as regiões estão convergindo."),
        ui.COR_RUIM if subiu else ui.COR_BOM,
    )
