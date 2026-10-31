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

Série histórica de preços de combustíveis da **ANP** (Agência Nacional do Petróleo, Gás Natural e Biocombustíveis) — dados abertos em [gov.br/anp](https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/levantamento-de-precos) ou via portal [dados.gov.br](https://dados.gov.br/). **Fallback:** caso a fonte da ANP esteja indisponível ou mal estruturada para ingestão programática no momento da implementação, usar um dataset público equivalente de supply chain/distribuição (ex. DataCo Smart Supply Chain, no Kaggle) e documentar a troca aqui.

## Stack

- **Banco de dados:** PostgreSQL
- **ETL/Análise:** Python (pandas, requests, SQLAlchemy, psycopg2)
- **Visualização:** Streamlit + Plotly
- **Notebook exploratório:** Jupyter

## Roadmap

- [ ] Validar a fonte de dados (ANP vs. fallback) e documentar o formato/endpoint em `src/extract.py`
- [ ] Baixar/coletar os dados brutos para `data/raw/`
- [ ] Criar schema em `sql/schema.sql` e carregar os dados (`src/load.py`)
- [ ] Queries analíticas em `sql/analysis/` (uma por pergunta de negócio)
- [ ] Notebook de EDA em `notebooks/01_exploracao.ipynb`
- [ ] Dashboard Streamlit em `dashboard/app.py`
- [ ] Publicar o dashboard e colar o link abaixo
- [ ] Escrever a seção "Insights e Recomendações" com os achados finais

## Como rodar localmente

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python src/extract.py
python src/load.py
streamlit run dashboard/app.py
```

## Dashboard ao vivo

_(link a publicar após a implementação)_

## Insights e recomendações

_(a preencher depois da análise)_
