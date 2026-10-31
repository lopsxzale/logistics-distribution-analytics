"""Dashboard Streamlit — Logistics & Distribution Pricing Analytics.

Visualiza os preços de combustíveis (ANP) por estado/região, com foco em
fluidez: cache agressivo, filtros aplicados via formulário (um único rerun
por aplicação, não um por clique) e transições suaves nos gráficos Plotly.

Uso: streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db import get_engine  # noqa: E402

# Paleta categórica (validada para CVD — ver skill dataviz, references/palette.md).
# Slots 1-3, nessa ordem fixa: azul, laranja, água.
COR_CATEGORIA = {
    "GASOLINA": "#2a78d6",
    "ETANOL": "#eb6834",
    "DIESEL": "#1baf7a",
}
COR_SEQUENCIAL = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

# Mapeamento fixo (ordem categórica validada) para as 5 regiões — a cor de uma
# região nunca muda quando o filtro altera quais outras regiões aparecem.
COR_REGIAO = {
    "Sudeste": "#2a78d6",
    "Nordeste": "#eb6834",
    "Sul": "#1baf7a",
    "Centro-Oeste": "#eda100",
    "Norte": "#e87ba4",
}

NOMES_MES = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]

st.set_page_config(
    page_title="Logistics & Distribution Pricing Analytics",
    page_icon="⛽",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def css() -> str:
    return """
    <style>
    #MainMenu, footer, header {visibility: hidden;}

    .block-container {
        padding-top: 1.5rem;
        max-width: 1400px;
    }

    [data-testid="stMetric"] {
        background: #fcfcfb;
        border: 1px solid rgba(11,11,11,0.10);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        transition: transform .25s ease, box-shadow .25s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(11,11,11,0.08);
    }

    [data-testid="stTabs"] button {
        transition: color .2s ease, border-color .2s ease;
    }

    .stPlotlyChart {
        transition: opacity .25s ease;
    }

    @media (max-width: 768px) {
        [data-testid="stMetric"] { padding: 0.6rem 0.75rem; }
        .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
    }
    </style>
    """


@st.cache_resource(show_spinner=False)
def carregar_opcoes_filtro() -> tuple[pd.DataFrame, list[str], int, int]:
    engine = get_engine()
    estados = pd.read_sql(
        "SELECT uf, nome_estado, regiao_sigla, regiao_nome FROM dim_estado ORDER BY regiao_nome, nome_estado",
        engine,
    )
    categorias_df = pd.read_sql(
        "SELECT DISTINCT categoria FROM agg_preco_mensal_uf ORDER BY categoria", engine
    )
    anos_df = pd.read_sql(
        "SELECT MIN(ano) AS ano_min, MAX(ano) AS ano_max FROM agg_preco_mensal_uf", engine
    )
    categorias = categorias_df["categoria"].tolist()
    ano_min = int(anos_df["ano_min"].iloc[0]) if not anos_df["ano_min"].isna().iloc[0] else datetime.now().year
    ano_max = int(anos_df["ano_max"].iloc[0]) if not anos_df["ano_max"].isna().iloc[0] else datetime.now().year
    return estados, categorias, ano_min, ano_max


@st.cache_data(show_spinner=False)
def carregar_agregado(ufs: tuple[str, ...], categoria: str, ano_ini: int, ano_fim: int) -> pd.DataFrame:
    engine = get_engine()
    placeholders = ",".join(f"'{uf}'" for uf in ufs) if ufs else "''"
    query = f"""
        SELECT a.ano, a.mes, a.uf, e.nome_estado, e.regiao_sigla, e.regiao_nome,
               a.categoria, a.preco_medio, a.preco_min, a.preco_max, a.desvio_padrao, a.n_amostras
        FROM agg_preco_mensal_uf a
        JOIN dim_estado e ON e.uf = a.uf
        WHERE a.categoria = '{categoria}'
          AND a.ano BETWEEN {ano_ini} AND {ano_fim}
          AND a.uf IN ({placeholders})
        ORDER BY a.ano, a.mes
    """
    return pd.read_sql(query, engine)


@st.cache_data(show_spinner=False)
def carregar_meta() -> str | None:
    engine = get_engine()
    try:
        df = pd.read_sql(
            "SELECT ultima_atualizacao FROM meta_carga WHERE chave = 'ultima_atualizacao'", engine
        )
    except Exception:
        return None
    if df.empty:
        return None
    return df["ultima_atualizacao"].iloc[0]


def banco_disponivel() -> bool:
    try:
        _, categorias, _, _ = carregar_opcoes_filtro()
        return len(categorias) > 0
    except Exception:
        return False


def layout_base(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        transition_duration=400,
        transition_easing="cubic-in-out",
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif"),
    )
    fig.update_xaxes(gridcolor="#e1e0d9", zeroline=False)
    fig.update_yaxes(gridcolor="#e1e0d9", zeroline=False)
    return fig


def main() -> None:
    st.markdown(css(), unsafe_allow_html=True)
    st.title("⛽ Logistics & Distribution Pricing Analytics")
    st.caption(
        "Preços de combustíveis por estado/região no Brasil — dados abertos da ANP, "
        "sob a ótica de uma operação de distribuição."
    )

    if not banco_disponivel():
        st.warning(
            "Nenhum dado carregado ainda. Rode no terminal, na raiz do projeto:\n\n"
            "```bash\npython src/extract.py\npython src/load.py\n```\n\n"
            "Depois recarregue esta página.",
            icon="⚠️",
        )
        return

    estados, categorias, ano_min, ano_max = carregar_opcoes_filtro()

    with st.sidebar:
        st.header("Filtros")
        with st.form("filtros", border=False):
            regioes_sel = st.multiselect(
                "Região",
                options=sorted(estados["regiao_nome"].unique()),
                default=sorted(estados["regiao_nome"].unique()),
                key="filtro_regiao",
            )
            categoria_sel = st.selectbox(
                "Combustível", options=categorias, index=0, key="filtro_categoria"
            )
            periodo_sel = st.slider(
                "Período (ano)",
                min_value=ano_min,
                max_value=ano_max,
                value=(ano_min, ano_max),
                key="filtro_periodo",
            )
            aplicar = st.form_submit_button("Aplicar filtros", width="stretch")

    if "estado_filtros" not in st.session_state or aplicar:
        st.session_state["estado_filtros"] = {
            "regioes": tuple(regioes_sel) or tuple(sorted(estados["regiao_nome"].unique())),
            "categoria": categoria_sel,
            "ano_ini": periodo_sel[0],
            "ano_fim": periodo_sel[1],
        }

    filtros = st.session_state["estado_filtros"]
    ufs_filtradas = tuple(estados.loc[estados["regiao_nome"].isin(filtros["regioes"]), "uf"])

    df = carregar_agregado(ufs_filtradas, filtros["categoria"], filtros["ano_ini"], filtros["ano_fim"])

    if df.empty:
        st.info("Nenhum dado para a combinação de filtros selecionada.")
        return

    df_mensal_brasil = (
        df.groupby(["ano", "mes"])
        .apply(lambda g: pd.Series({"preco_medio": (g["preco_medio"] * g["n_amostras"]).sum() / g["n_amostras"].sum()}))
        .reset_index()
        .sort_values(["ano", "mes"])
    )

    preco_atual = df_mensal_brasil["preco_medio"].iloc[-1]
    preco_anterior = df_mensal_brasil["preco_medio"].iloc[-2] if len(df_mensal_brasil) > 1 else preco_atual
    variacao_pct = (preco_atual - preco_anterior) / preco_anterior * 100 if preco_anterior else 0.0

    por_uf = df.groupby(["uf", "nome_estado"])["preco_medio"].mean().reset_index()
    uf_mais_cara = por_uf.loc[por_uf["preco_medio"].idxmax()]
    uf_mais_barata = por_uf.loc[por_uf["preco_medio"].idxmin()]
    gap_pct = (uf_mais_cara["preco_medio"] - uf_mais_barata["preco_medio"]) / uf_mais_barata["preco_medio"] * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        f"Preço médio — {filtros['categoria'].title()}",
        f"R$ {preco_atual:.2f}",
        f"{variacao_pct:+.1f}% vs mês anterior",
        delta_color="inverse",
    )
    col2.metric("Estado mais caro", f"{uf_mais_cara['nome_estado']}", f"R$ {uf_mais_cara['preco_medio']:.2f}")
    col3.metric("Estado mais barato", f"{uf_mais_barata['nome_estado']}", f"R$ {uf_mais_barata['preco_medio']:.2f}")
    col4.metric("Gap mais caro vs. mais barato", f"{gap_pct:.1f}%")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Evolução por região",
        "🗓️ Sazonalidade",
        "📊 Volatilidade por estado",
        "↕️ Gap regional",
    ])

    cor_categoria_atual = COR_CATEGORIA.get(filtros["categoria"], COR_SEQUENCIAL[2])

    with tab1:
        df["data"] = pd.to_datetime(dict(year=df["ano"], month=df["mes"], day=1))
        df_regiao = df.groupby(["data", "regiao_nome"])["preco_medio"].mean().reset_index()
        fig = px.line(
            df_regiao,
            x="data",
            y="preco_medio",
            color="regiao_nome",
            markers=True,
            labels={"data": "", "preco_medio": "Preço médio (R$)", "regiao_nome": "Região"},
            color_discrete_map=COR_REGIAO,
        )
        fig.update_traces(line_width=2, marker=dict(size=6))
        fig = layout_base(fig)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="chart_evolucao")

    with tab2:
        df_sazonal = df.groupby("mes")["preco_medio"].mean().reindex(range(1, 13))
        fig = go.Figure(
            go.Bar(
                x=NOMES_MES,
                y=df_sazonal.values,
                marker=dict(
                    color=df_sazonal.values,
                    colorscale=[[0, COR_SEQUENCIAL[0]], [1, COR_SEQUENCIAL[-1]]],
                ),
            )
        )
        fig.update_layout(yaxis_title="Preço médio (R$)")
        fig = layout_base(fig)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="chart_sazonalidade")
        st.caption("Preço médio por mês-calendário, agregando todos os anos do período selecionado.")

    with tab3:
        volat = (
            df.groupby(["uf", "nome_estado"])
            .agg(preco_medio=("preco_medio", "mean"), desvio_medio=("desvio_padrao", "mean"))
            .reset_index()
        )
        volat["coef_variacao"] = (volat["desvio_medio"] / volat["preco_medio"]) * 100
        volat = volat.sort_values("coef_variacao", ascending=True)
        fig = go.Figure(
            go.Bar(
                x=volat["coef_variacao"],
                y=volat["nome_estado"],
                orientation="h",
                marker=dict(color=cor_categoria_atual),
            )
        )
        fig.update_layout(
            xaxis_title="Coeficiente de variação (%)",
            height=max(400, 22 * len(volat)),
        )
        fig = layout_base(fig)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="chart_volatilidade")

    with tab4:
        preco_regiao_tempo = df.groupby(["ano", "mes", "regiao_sigla"])["preco_medio"].mean().reset_index()
        gap = (
            preco_regiao_tempo.groupby(["ano", "mes"])["preco_medio"]
            .agg(preco_max="max", preco_min="min")
            .reset_index()
        )
        gap["gap_percentual"] = (gap["preco_max"] - gap["preco_min"]) / gap["preco_min"] * 100
        gap["data"] = pd.to_datetime(dict(year=gap["ano"], month=gap["mes"], day=1))
        fig = px.area(
            gap.sort_values("data"),
            x="data",
            y="gap_percentual",
            labels={"data": "", "gap_percentual": "Gap (%)"},
        )
        fig.update_traces(line_color=cor_categoria_atual, fillcolor=cor_categoria_atual, opacity=0.35)
        fig = layout_base(fig)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="chart_gap")
        st.caption("Gap % entre a região mais cara e a mais barata, mês a mês.")

    meta = carregar_meta()
    st.divider()
    rodape = "Fonte: ANP — Série Histórica de Preços de Combustíveis (dados.gov.br)."
    if meta:
        try:
            dt = datetime.fromisoformat(meta)
            rodape += f" Última carga: {dt.astimezone().strftime('%d/%m/%Y %H:%M')}."
        except ValueError:
            pass
    st.caption(rodape)


if __name__ == "__main__":
    main()
