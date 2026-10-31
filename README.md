# Logistics & Distribution Pricing Analytics

Análise de dados públicos de preços e distribuição de combustíveis no Brasil, ligando dados reais a perguntas de negócio típicas de uma operação de logística/distribuição.

## Contexto

Projeto de portfólio que conecta a experiência real do autor como Aprendiz de Logística (distribuição) a um caso de análise de dados: em vez de um CSV estático de Kaggle, o projeto consome dados públicos via API/download oficial, trata séries temporais regionais e responde perguntas que uma distribuidora realmente faria sobre custo e variação de preços.

## Perguntas de negócio

1. Como varia o preço médio dos combustíveis entre estados/regiões ao longo do tempo?
2. Existe sazonalidade (meses/períodos do ano com maior variação de preço)?
3. Quais estados têm maior volatilidade de preço — relevante para planejamento de rotas/estoque?
4. Qual a diferença percentual entre a região mais cara e a mais barata, e como isso evoluiu nos últimos anos?

## Fonte de dados

Série histórica de preços de combustíveis da **ANP** (Agência Nacional do Petróleo, Gás Natural e Biocombustíveis) — dados abertos em [gov.br/anp](https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/levantamento-de-precos), com download direto em CSV mensal por produto (`.../shpc/dsan/{ano}/precos-{produto}-{mm}.csv`). Fonte validada e usada diretamente — o fallback (DataCo Smart Supply Chain, no Kaggle) não foi necessário.

Janela carregada: **janeiro/2023 a dezembro/2025** (a série mensal unificada da ANP começa em 2023; antes disso só existe uma série semestral com formato diferente, não usada aqui), cobrindo Gasolina, Etanol e Diesel nas 27 UFs.

## Stack

- **Banco de dados:** SQLite por padrão (zero dependência externa — `data/processed/anp_combustiveis.db`), com suporte a PostgreSQL via `DATABASE_URL` no `.env` para quem preferir
- **ETL/Análise:** Python (pandas, requests, SQLAlchemy, psycopg2)
- **Visualização:** Streamlit + Plotly
- **Notebook exploratório:** Jupyter

## Roadmap

- [x] Validar a fonte de dados (ANP vs. fallback) e documentar o formato/endpoint em `src/extract.py`
- [x] Baixar/coletar os dados brutos para `data/raw/`
- [x] Criar schema em `sql/schema.sql` e carregar os dados (`src/load.py`)
- [x] Queries analíticas em `sql/analysis/` (uma por pergunta de negócio)
- [x] Notebook de EDA em `notebooks/01_exploracao.ipynb`
- [x] Dashboard Streamlit em `dashboard/app.py`
- [ ] Publicar o dashboard e colar o link abaixo
- [x] Escrever a seção "Insights e Recomendações" com os achados finais

## Como rodar localmente

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/extract.py
python src/load.py
streamlit run dashboard/app.py
```

Por padrão usa SQLite (sem configuração extra). Para customizar a janela de anos ou usar Postgres, copie `.env.example` para `.env` e ajuste.

## Dashboard ao vivo

_(link a publicar)_

## Insights e recomendações

Análise sobre 2.6 milhões de registros de preço (2023-01 a 2025-12, 27 UFs). Foco em **diesel**, o combustível mais relevante para uma operação de distribuição:

1. **Variação por estado/região:** o preço médio de diesel caiu em todas as regiões entre jan/2023 e dez/2025 (ex.: Nordeste R$ 6,51 → R$ 6,03). O **Norte é consistentemente a região mais cara** (R$ 6,84 → R$ 6,60), refletindo o custo logístico de abastecer áreas remotas.
2. **Sazonalidade:** existe um padrão sazonal claro — **junho/julho são os meses mais baratos** (~R$ 5,81) e **fevereiro o mais caro** (~R$ 6,33), uma amplitude de ~R$ 0,52 (~8,5%) entre os extremos do ano. Vale considerar antecipar reabastecimento/contratos antes de fevereiro.
3. **Volatilidade por estado:** **AM (8,1%), PA (7,7%) e AL (6,9%)** de coeficiente de variação lideram a volatilidade de preço — estados do Norte/Nordeste exigem margem de segurança maior no planejamento de custo de combustível e nas rotas que passam por eles.
4. **Gap regional:** o gap % entre a região mais cara e a mais barata está **aumentando**, não encolhendo: 9,1% (2023) → 9,5% (2024) → 10,5% (2025) — a disparidade regional de preço vem se ampliando ano a ano, o que reforça a importância de revisar a malha logística/fornecedores por região periodicamente, em vez de assumir um custo nacional único.
