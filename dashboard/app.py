"""Combustível & Logística — dashboard de preços da ANP sob a ótica de uma distribuidora.

Uso: streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path[:0] = [str(RAIZ), str(RAIZ.parent / "src")]

import components as ui  # noqa: E402
import data  # noqa: E402

st.set_page_config(
    page_title="Combustível & Logística | Analytics ANP",
    page_icon=":material/local_gas_station:",
    layout="wide",
    initial_sidebar_state="auto",
)
ui.aplicar_css()

if not data.dados_disponiveis():
    st.error(
        "Dados do dashboard não encontrados em `data/app/`. Rode `python src/extract.py` e `python src/load.py`.",
        icon=":material/database_off:",
    )
    st.stop()

paginas = {
    "Panorama": [
        st.Page("views/visao_geral.py", title="Visão geral", icon=":material/space_dashboard:", default=True),
    ],
    "Análises": [
        st.Page("views/evolucao.py", title="Evolução de preços", icon=":material/trending_up:"),
        st.Page("views/sazonalidade.py", title="Sazonalidade", icon=":material/calendar_month:"),
        st.Page("views/risco.py", title="Risco & volatilidade", icon=":material/monitoring:"),
        st.Page("views/gap_regional.py", title="Gap regional", icon=":material/compare_arrows:"),
        st.Page("views/etanol_gasolina.py", title="Etanol vs gasolina", icon=":material/eco:"),
        st.Page("views/bandeiras_produtos.py", title="Bandeiras & produtos", icon=":material/storefront:"),
    ],
    "Ferramentas": [
        st.Page("views/simulador.py", title="Simulador de frota", icon=":material/local_shipping:"),
        st.Page("views/sobre.py", title="Sobre o projeto", icon=":material/info:"),
    ],
}
pagina = st.navigation(paginas)

meses = data.meses_disponiveis()
with st.sidebar:
    st.segmented_control(
        "Combustível",
        options=data.CATEGORIAS,
        format_func=data.ROTULO.get,
        default="DIESEL",
        required=True,
        key="f_categoria",
        width="stretch",
    )
    st.select_slider(
        "Período",
        options=meses,
        value=(meses[0], meses[-1]),
        format_func=ui.mes_ano,
        key="f_periodo",
    )
    st.pills(
        "Regiões",
        options=data.REGIOES,
        selection_mode="multi",
        default=list(data.REGIOES),
        key="f_regioes",
    )
    if not st.session_state.get("f_regioes"):
        st.caption("Nenhuma região marcada: mostrando todas.")
    m = data.meta()
    st.markdown(
        f"""<div class="rodape">Fonte: ANP — Série Histórica de Preços de Combustíveis.<br>
        {ui.num(m["registros"] / 1e6, 1)} mi de coletas · {m["municipios"]} municípios · 27 UFs<br>
        <a href="{ui.GITHUB_URL}" target="_blank">Código no GitHub</a></div>""",
        unsafe_allow_html=True,
    )

pagina.run()
