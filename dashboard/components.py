"""Componentes visuais compartilhados: paleta, formatação pt-BR, cards de gráfico e CSS."""

from __future__ import annotations

import html
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.colors import sample_colorscale

GITHUB_URL = "https://github.com/lopsxzale/logistics-distribution-analytics"
LINKEDIN_URL = "www.linkedin.com/in/alexandrelopes0"

# Paleta validada para o tema escuro (skill dataviz). A cor segue a entidade, nunca a posição.
COR_CATEGORIA = {"GASOLINA": "#3987e5", "ETANOL": "#d95926", "DIESEL": "#199e70"}
COR_REGIAO = {
    "Sudeste": "#3987e5",
    "Nordeste": "#d95926",
    "Sul": "#199e70",
    "Centro-Oeste": "#c98500",
    "Norte": "#d55181",
}
COR_NEUTRA = "#5c5b57"
COR_DESTAQUE = "#3987e5"
COR_BOM = "#199e70"
COR_RUIM = "#e66767"
ESCALA_SEQUENCIAL = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#b7d3f6"]
ESCALA_DIVERGENTE = [[0.0, "#2a78d6"], [0.25, "#6da7ec"], [0.5, "#4a4945"], [0.75, "#ec8a8a"], [1.0, "#d03b3b"]]

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
GRID = "#2c2c2a"
TINTA_SECUNDARIA = "#c3c2b7"

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True, "scrollZoom": False}


def brl(valor: float, casas: int = 2) -> str:
    texto = f"{valor:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {texto}"


def num(valor: float, casas: int = 1) -> str:
    return f"{valor:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def pct(valor: float, casas: int = 1, sinal: bool = False) -> str:
    prefixo = "+" if sinal and valor > 0 else ""
    return f"{prefixo}{num(valor, casas)}%"


def rgba(cor_hex: str, alfa: float) -> str:
    r, g, b = (int(cor_hex[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alfa})"


def mes_ano(data: pd.Timestamp) -> str:
    return f"{MESES[data.month - 1]}/{data:%y}"


def _rich(texto: str) -> str:
    """Escapa HTML e converte **negrito**. O '$' vira entidade para o Markdown não abrir modo LaTeX em 'R$ ... R$'."""
    seguro = html.escape(texto).replace("$", "&#36;")
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", seguro)


def kpi(coluna, rotulo: str, valor: str, delta: str | None = None, **kwargs) -> None:
    """st.metric com '$' escapado (rótulos e deltas passam por Markdown) e borda padrão."""

    def esc(t):
        return t.replace("$", r"\$") if t else t

    coluna.metric(esc(rotulo), esc(valor), esc(delta), border=True, **kwargs)


def mapa_coropletico(
    df: pd.DataFrame,
    contornos: dict[str, tuple[list, list]],
    valor: str,
    hover: str,
    escala: list,
    faixa: tuple[float, float],
    sufixo: str = "%",
) -> go.Figure:
    """Coroplético do Brasil desenhado com polígonos cartesianos (sem tiles nem topojson externos)."""
    cmin, cmax = faixa
    fig = go.Figure()
    # DF fica dentro de GO: desenhado por último para ficar por cima.
    for linha in sorted(df.to_dict("records"), key=lambda r: r["uf"] == "DF"):
        xs, ys = contornos[linha["uf"]]
        t = min(max((linha[valor] - cmin) / (cmax - cmin), 0.0), 1.0) if cmax > cmin else 0.5
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                fill="toself",
                fillcolor=sample_colorscale(escala, [t])[0],
                line=dict(color="#0d0d0d", width=0.8),
                hoveron="fills",
                hoverinfo="text",
                text=linha[hover],
                showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            hoverinfo="skip",
            showlegend=False,
            marker=dict(
                colorscale=escala,
                cmin=cmin,
                cmax=cmax,
                color=[cmin],
                showscale=True,
                colorbar=dict(thickness=10, len=0.6, ticksuffix=sufixo, tickfont_color="#898781", outlinewidth=0),
            ),
        )
    )
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    return fig


def estilizar(
    fig: go.Figure,
    altura: int = 380,
    legenda: bool = True,
    hover_unificado: bool = False,
    eixo_y: str | None = None,
    eixo_x: str | None = None,
) -> go.Figure:
    fig.update_layout(
        height=altura,
        margin=dict(l=4, r=12, t=8 if not legenda else 36, b=4),
        separators=",.",
        font=dict(family="'Source Sans 3', 'Source Sans Pro', system-ui, sans-serif", size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text="", font_size=12),
        hovermode="x unified" if hover_unificado else "closest",
        hoverlabel=dict(bgcolor="#1a1a19", bordercolor="#383835", font_size=13, font_color="#f0efec"),
        transition=dict(duration=350, easing="cubic-in-out"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=GRID, title_text=eixo_x or "", tickfont_color="#898781")
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title_text=eixo_y or "", tickfont_color="#898781")
    return fig


def cabecalho(titulo: str, subtitulo: str, chips: list[str] | None = None) -> None:
    chips_html = "".join(f"<span>{html.escape(c)}</span>" for c in (chips or []))
    st.markdown(
        f"""<div class="hero"><h1>{html.escape(titulo)}</h1><p>{_rich(subtitulo)}</p>
        <div class="chips">{chips_html}</div></div>""",
        unsafe_allow_html=True,
    )


def secao(titulo: str, texto: str | None = None) -> None:
    corpo = f"<p>{_rich(texto)}</p>" if texto else ""
    st.markdown(f'<div class="secao"><h3>{html.escape(titulo)}</h3>{corpo}</div>', unsafe_allow_html=True)


def chart_card(
    key: str,
    titulo: str,
    fig: go.Figure,
    o_que: str,
    como_ler: str,
    por_que: str,
) -> None:
    """Gráfico com título-afirmação e a explicação: o que mostra, como ler e por que importa."""
    with st.container(border=True, key=f"card-{key}"):
        st.markdown(f'<div class="card-titulo">{_rich(titulo)}</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, key=f"fig-{key}", config=PLOTLY_CONFIG, theme="streamlit", width="stretch")
        st.markdown(
            f"""<div class="explica">
            <div><span class="rotulo">O que mostra</span><span>{_rich(o_que)}</span></div>
            <div><span class="rotulo">Como ler</span><span>{_rich(como_ler)}</span></div>
            <div class="destaque"><span class="rotulo">Por que importa</span><span>{_rich(por_que)}</span></div>
            </div>""",
            unsafe_allow_html=True,
        )


def achado(numero: str, titulo: str, texto: str, cor: str = COR_DESTAQUE) -> None:
    st.markdown(
        f"""<div class="achado" style="--cor:{cor}"><div class="achado-num">{html.escape(numero)}</div>
        <div class="achado-titulo">{_rich(titulo)}</div><div class="achado-texto">{_rich(texto)}</div></div>""",
        unsafe_allow_html=True,
    )


def pipeline(etapas: list[tuple[str, str]]) -> None:
    """Fluxo horizontal de etapas (quebra em linhas no celular)."""
    blocos = [
        f'<div class="etapa"><b>{html.escape(titulo)}</b><span>{html.escape(sub)}</span></div>'
        for titulo, sub in etapas
    ]
    st.markdown(f'<div class="pipeline">{"<i>→</i>".join(blocos)}</div>', unsafe_allow_html=True)


def vazio(mensagem: str = "Nenhum dado para os filtros selecionados. Amplie o período ou as regiões.") -> None:
    st.info(mensagem, icon=":material/filter_alt_off:")


CSS = """
<style>
:root { --superficie:#1a1a19; --hair:#2c2c2a; --tinta2:#c3c2b7; --muted:#898781; --acento:#3987e5; }

[data-testid="stMainBlockContainer"] { max-width: 1320px; padding-top: 2.2rem; padding-bottom: 4rem; }

@keyframes surgir { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }

[class*="st-key-card-"], [data-testid="stMetric"], .achado {
  background: var(--superficie);
  animation: surgir .45s cubic-bezier(.2,.7,.2,1) both;
  transition: border-color .25s ease, box-shadow .25s ease;
}
[class*="st-key-card-"]:hover, [data-testid="stMetric"]:hover, .achado:hover {
  border-color: #45443f !important;
  box-shadow: 0 10px 30px rgba(0,0,0,.35);
}
[data-testid="stMetricValue"] { font-weight: 650; letter-spacing: -.01em; }
[data-testid="stMetricLabel"] p { color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .05em; }

.hero { margin-bottom: 1.4rem; animation: surgir .5s cubic-bezier(.2,.7,.2,1) both; }
.hero h1 {
  font-size: clamp(1.9rem, 2.4vw + 1rem, 3rem); font-weight: 800; letter-spacing: -.025em; line-height: 1.1;
  padding: 0; margin: 0 0 .5rem 0;
  background: linear-gradient(92deg, #f0efec 30%, #86b6ef 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero p { color: var(--tinta2); font-size: 1.05rem; max-width: 70ch; margin: 0; }
.chips { margin-top: .8rem; display: flex; flex-wrap: wrap; gap: .4rem; }
.chips span {
  padding: .22rem .7rem; border: 1px solid var(--hair); border-radius: 999px;
  font-size: .78rem; color: var(--tinta2); background: rgba(255,255,255,.02);
}

.secao { margin: 1.6rem 0 .6rem 0; }
.secao h3 { font-size: 1.15rem; font-weight: 700; margin: 0; padding: 0; }
.secao p { color: var(--muted); font-size: .92rem; margin: .2rem 0 0 0; }

.card-titulo { font-size: 1.02rem; font-weight: 650; line-height: 1.3; margin: .1rem 0 .2rem 0; }
.explica {
  display: grid; gap: .4rem; margin-top: .15rem; padding-top: .7rem;
  border-top: 1px solid var(--hair); font-size: .87rem; color: var(--tinta2); line-height: 1.45;
}
.explica > div { display: grid; grid-template-columns: 8.2rem 1fr; gap: .6rem; }
.explica .rotulo {
  color: var(--muted); font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; padding-top: .18rem;
}
.explica .destaque span:last-child { color: #f0efec; }
.explica strong, .achado strong { color: #f0efec; font-weight: 650; }

.achado { border: 1px solid var(--hair); border-radius: .75rem; padding: 1rem 1.1rem; min-height: 11.5rem;
  border-left: 3px solid var(--cor); }
.achado-num { font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; color: #f0efec; }
.achado-titulo { font-size: .92rem; font-weight: 650; margin-top: .1rem; }
.achado-texto { font-size: .85rem; color: var(--tinta2); margin-top: .35rem; line-height: 1.45; }

.pipeline { display: flex; flex-wrap: wrap; align-items: stretch; gap: .45rem; margin: .4rem 0 1rem 0; }
.pipeline > i { align-self: center; color: var(--muted); font-style: normal; font-size: 1.1rem; }
.pipeline .etapa {
  flex: 1 1 6.5rem; min-width: 0; display: flex; flex-direction: column; gap: .2rem; padding: .75rem .9rem;
  background: var(--superficie); border: 1px solid var(--hair); border-radius: .75rem;
  animation: surgir .45s cubic-bezier(.2,.7,.2,1) both;
}
.pipeline .etapa:first-child { border-color: #3987e5; }
.pipeline .etapa:last-child { border-color: #199e70; }
.pipeline .etapa b { font-size: .95rem; color: #f0efec; }
.pipeline .etapa span { font-size: .8rem; color: var(--tinta2); line-height: 1.35; }

[data-testid="stSidebar"] .rodape { font-size: .75rem; color: var(--muted); line-height: 1.5; }

@media (max-width: 640px) {
  [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }
  .explica > div { grid-template-columns: 1fr; gap: .1rem; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
"""


def aplicar_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
