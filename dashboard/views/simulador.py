import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import components as ui
import data
import metrics

CONSUMO_PADRAO = {"DIESEL": 2.8, "GASOLINA": 11.0, "ETANOL": 7.7}
KM_PADRAO = {"DIESEL": 10_000, "GASOLINA": 3_000, "ETANOL": 3_000}
# Corredor típico de distribuição (Sul–Sudeste–Centro-Oeste–Nordeste) como ponto de partida editável.
CORREDOR_PADRAO = [
    "Paraná",
    "São Paulo",
    "Rio de Janeiro",
    "Minas Gerais",
    "Goiás",
    "Mato Grosso",
    "Bahia",
    "Pernambuco",
]

f = data.filtros()
df = data.aplicar(data.painel_uf(), f)

ui.cabecalho(
    "Simulador de custo de frota",
    "Quanto a sua frota gasta de combustível em cada estado, quanto dá para economizar escolhendo onde abastecer "
    "e como o custo deve se comportar nos próximos 12 meses.",
    chips=[f.rotulo, "Preços: média dos últimos 3 meses do período", "Projeção: padrão sazonal histórico"],
)
if df.empty:
    ui.vazio()
    st.stop()


@st.fragment
def simulador() -> None:
    recente = df[df["data"] > f.fim - pd.DateOffset(months=3)]
    precos = metrics.media_ponderada(recente, ["uf", "nome_estado"]).sort_values("preco_medio")

    with st.container(border=True, key="card-sim-entradas"):
        c1, c2, c3 = st.columns(3)
        km = c1.number_input(
            "Km por veículo / mês",
            min_value=100,
            max_value=50_000,
            step=500,
            value=KM_PADRAO[f.categoria],
            key=f"sim_km_{f.categoria}",
        )
        consumo = c2.number_input(
            "Consumo (km/litro)",
            min_value=0.5,
            max_value=30.0,
            step=0.1,
            format="%.1f",
            value=CONSUMO_PADRAO[f.categoria],
            key=f"sim_consumo_{f.categoria}",
            help="Referências: carreta ~2,5–3 km/L; caminhão toco ~4–5 km/L; utilitário leve ~10–12 km/L.",
        )
        veiculos = c3.number_input("Veículos na frota", min_value=1, max_value=5_000, step=1, value=10, key="sim_veic")
        nomes = precos["nome_estado"].tolist()
        padrao = [n for n in CORREDOR_PADRAO if n in nomes] or nomes
        escolhidos = st.multiselect(
            "Estados onde a frota abastece",
            options=nomes,
            default=padrao,
            key=f"sim_ufs_{'-'.join(f.regioes)}",
            placeholder="Escolha os estados da operação",
        )

    sel = precos[precos["nome_estado"].isin(escolhidos)].copy()
    if sel.empty:
        ui.vazio("Escolha ao menos um estado para simular.")
        return
    sel["custo"] = metrics.custo_frota(sel["preco_medio"], km, consumo, veiculos)
    litros = km / consumo * veiculos
    barata, cara = sel.iloc[0], sel.iloc[-1]
    custo_medio = sel["custo"].mean()

    k1, k2, k3, k4 = st.columns(4)
    ui.kpi(k1, "Litros por mês", ui.num(litros, 0))
    ui.kpi(k2, "Custo mensal médio", ui.brl(custo_medio, 0))
    ui.kpi(k3, "Custo anual estimado", ui.brl(custo_medio * 12, 0))
    ui.kpi(
        k4,
        "Economia possível / mês",
        ui.brl(cara["custo"] - barata["custo"], 0),
        f"abastecendo em {barata['nome_estado']} vs {cara['nome_estado']}",
        delta_color="off",
        delta_arrow="off",
    )

    cores = [
        ui.COR_BOM if n == barata["nome_estado"] else ui.COR_RUIM if n == cara["nome_estado"] else ui.COR_NEUTRA
        for n in sel["nome_estado"]
    ]
    fig = go.Figure(
        go.Bar(
            x=sel["custo"],
            y=sel["nome_estado"],
            orientation="h",
            marker=dict(color=cores, cornerradius=4),
            text=[ui.brl(v, 0) for v in sel["custo"]],
            textposition="outside",
            cliponaxis=False,
            textfont=dict(color=ui.TINTA_SECUNDARIA, size=11),
            customdata=sel["preco_medio"],
            hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}/mês<br>litro a R$ %{customdata:.2f}<extra></extra>",
        )
    )
    fig.update_xaxes(tickprefix="R$ ", tickformat=",.0f", range=[0, sel["custo"].max() * 1.2])
    fig.update_yaxes(autorange="reversed", tickfont_size=11)
    ui.chart_card(
        "sim_ufs",
        f"Mesma frota, mesma rodagem: de {ui.brl(barata['custo'], 0)} a {ui.brl(cara['custo'], 0)} por mês",
        ui.estilizar(fig, altura=max(260, 24 * len(sel) + 40), legenda=False),
        "Custo mensal de combustível da frota configurada acima, se ela abastecesse integralmente em cada estado.",
        "Verde = estado mais barato, vermelho = mais caro entre os escolhidos. Custo = km ÷ consumo × preço × veículos.",
        f"A diferença de **{ui.brl(cara['custo'] - barata['custo'], 0)}/mês** "
        f"(**{ui.brl((cara['custo'] - barata['custo']) * 12, 0)}/ano**) mostra o valor de planejar pontos de "
        "abastecimento ao longo da rota.",
    )

    sazonal = metrics.indice_sazonal(df)
    if len(sazonal) == 12:
        meses = pd.date_range(f.fim + pd.DateOffset(months=1), periods=12, freq="MS")
        proj = pd.DataFrame({"data": meses, "mes": meses.month}).merge(sazonal, on="mes")
        custo_base = litros * sel["preco_medio"].mean() / 100
        for col in ("indice_medio", "indice_min", "indice_max"):
            proj[col.replace("indice", "custo")] = custo_base * proj[col]
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=pd.concat([proj["data"], proj["data"][::-1]]),
                y=pd.concat([proj["custo_max"], proj["custo_min"][::-1]]),
                fill="toself",
                fillcolor=ui.rgba(ui.COR_CATEGORIA[f.categoria], 0.15),
                line=dict(width=0),
                hoverinfo="skip",
                name="faixa histórica",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=proj["data"],
                y=proj["custo_medio"],
                mode="lines+markers",
                name="projeção",
                line=dict(color=ui.COR_CATEGORIA[f.categoria], width=2.4),
                marker=dict(size=6),
                hovertemplate="%{x|%m/%Y}: R$ %{y:,.0f}<extra></extra>",
            )
        )
        fig.update_xaxes(tickformat="%m/%y")
        fig.update_yaxes(tickprefix="R$ ", tickformat=",.0f")
        pico = proj.loc[proj["indice_medio"].idxmax()]
        ui.chart_card(
            "sim_projecao",
            "Projeção do custo nos próximos 12 meses",
            ui.estilizar(fig, altura=340, hover_unificado=True),
            "Custo mensal estimado da frota (preço médio dos estados escolhidos) ajustado pelo padrão sazonal histórico.",
            "A linha é a projeção central; a faixa sombreada vai do ano mais favorável ao menos favorável já observado "
            "para cada mês. Não considera tendência nem choques — é um cenário de planejamento, não uma previsão.",
            f"O mês de maior custo esperado é **{ui.mes_ano(pico['data'])}**: bom momento para negociar preço fixo "
            "ou antecipar compra.",
        )


simulador()
