import streamlit as st

import components as ui
import data

m = data.meta()

ui.cabecalho(
    "Sobre o projeto",
    "Projeto de portfólio que conecta a experiência prática em logística de distribuição a dados públicos reais: "
    "do download automatizado na ANP até um painel de decisão.",
    chips=["Python", "pandas", "SQL", "SQLite/PostgreSQL", "Streamlit", "Plotly", "pytest", "GitHub Actions"],
)

ui.secao("Pipeline de dados")
ui.pipeline(
    [
        ("ANP", "72 CSVs mensais (gov.br)"),
        ("extract.py", "download com retry, idempotente"),
        ("load.py", "parsing, limpeza, carga incremental"),
        ("SQLite / PostgreSQL", f"{ui.num(m['registros'] / 1e6, 1)} mi de linhas + 6 queries SQL"),
        ("export.py", "agregados em Parquet (~300 KB)"),
        ("Streamlit", "9 páginas, 25+ gráficos"),
    ]
)

col1, col2 = st.columns(2, gap="large")
with col1:
    ui.secao("Os dados")
    st.markdown(
        f"""
- **Fonte:** Série Histórica de Preços de Combustíveis da ANP (dados abertos, CSV mensal por produto).
- **Volume:** {ui.num(m["registros"], 0)} coletas de preço, {m["municipios"]} municípios, 27 UFs.
- **Período:** {m["periodo_inicio"]} a {m["periodo_fim"]}.
- **Combustíveis:** gasolina (comum e aditivada), etanol e diesel (comum e S10).
  O **GNV fica fora** das comparações porque é cotado em R\\$/m³, não em R\\$/litro.
- **Mapa:** contornos estaduais do projeto *click_that_hood* (Code for America), simplificados para carregar rápido.
"""
    )
    ui.secao("Decisões técnicas")
    st.markdown(
        """
- **Banco relacional + Parquet:** o banco completo (~170 MB) fica local; o app lê só os agregados mensais
  em Parquet, que somam ~300 KB, ficam versionados e carregam em milissegundos.
- **Média ponderada pelo nº de coletas** em toda agregação, para estados com poucas coletas não distorcerem a média nacional.
- **Desvio padrão sem reler o fato:** a carga guarda soma e soma dos quadrados por grupo, e o desvio é recomposto em
  qualquer nível de agregação.
- **Carga idempotente:** reprocessar um arquivo substitui apenas os meses e produtos daquele arquivo.
- **Testes automatizados** (pytest) para parsing, consolidação e todas as métricas, rodando no GitHub Actions.
"""
    )
with col2:
    ui.secao("Como as métricas são calculadas")
    st.markdown(
        """
- **Volatilidade temporal:** desvio padrão da variação % do preço médio mensal de um mês para o outro.
  Responde *"quão imprevisível é o preço aqui?"*.
- **Dispersão entre postos:** coeficiente de variação (desvio ÷ média) dos preços no mesmo estado e mês.
  Responde *"quanto vale escolher bem o posto?"*.
- **Gap regional:** (região mais cara − mais barata) ÷ mais barata, mês a mês.
- **Índice sazonal:** preço do mês ÷ média do próprio ano × 100, calculado só com anos completos.
- **Paridade etanol/gasolina:** preço do etanol ÷ preço da gasolina; abaixo de 70% o etanol compensa.
- **Custo de frota:** km ÷ consumo (km/L) × preço × nº de veículos.
"""
    )
    ui.secao("Autor")
    links = f"[Código no GitHub]({ui.GITHUB_URL})"
    if ui.LINKEDIN_URL:
        links += f" · [LinkedIn]({ui.LINKEDIN_URL})"
    st.markdown(
        "Desenvolvido por **Alexandre Lopes**, a partir da rotina como aprendiz de logística em distribuição: "
        "as perguntas deste painel são as que aparecem no dia a dia de quem planeja rotas e custos.\n\n" + links
    )
