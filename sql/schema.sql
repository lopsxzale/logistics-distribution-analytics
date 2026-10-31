-- Schema canônico (DDL de referência). A criação efetiva das tabelas é feita
-- por src/load.py via SQLAlchemy Core, usando o mesmo desenho abaixo, para
-- funcionar de forma idêntica em SQLite (padrão) e Postgres (opcional).

-- Dimensão estática de estados/regiões (seed de 27 linhas).
CREATE TABLE IF NOT EXISTS dim_estado (
    uf              TEXT PRIMARY KEY,      -- 'SP', 'AL', ...
    nome_estado     TEXT NOT NULL,
    regiao_sigla    TEXT NOT NULL,         -- 'NE', 'SE', 'S', 'N', 'CO'
    regiao_nome     TEXT NOT NULL
);

-- Dimensão de produto normalizado (agrupa variantes da ANP em categorias).
CREATE TABLE IF NOT EXISTS dim_produto (
    produto_raw     TEXT PRIMARY KEY,      -- valor original da coluna "Produto" da ANP
    categoria       TEXT NOT NULL          -- 'GASOLINA' | 'ETANOL' | 'DIESEL'
);

-- Fato: um registro por coleta de preço (granularidade de posto), com colunas
-- irrelevantes às perguntas de negócio já descartadas no ETL.
CREATE TABLE IF NOT EXISTS fato_preco (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data_coleta     DATE NOT NULL,
    ano             INTEGER NOT NULL,
    mes             INTEGER NOT NULL,
    uf              TEXT NOT NULL REFERENCES dim_estado(uf),
    municipio       TEXT NOT NULL,
    produto_raw     TEXT NOT NULL REFERENCES dim_produto(produto_raw),
    bandeira        TEXT,
    valor_venda     NUMERIC NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fato_preco_uf_data ON fato_preco(uf, data_coleta);
CREATE INDEX IF NOT EXISTS idx_fato_preco_produto ON fato_preco(produto_raw);
CREATE INDEX IF NOT EXISTS idx_fato_preco_ano_mes ON fato_preco(ano, mes);

-- Agregado materializado mensal por UF/produto. É isso que o dashboard
-- consulta (poucos milhares de linhas em vez de milhões), garantindo fluidez.
CREATE TABLE IF NOT EXISTS agg_preco_mensal_uf (
    ano             INTEGER NOT NULL,
    mes             INTEGER NOT NULL,
    uf              TEXT NOT NULL REFERENCES dim_estado(uf),
    categoria       TEXT NOT NULL,
    preco_medio     NUMERIC NOT NULL,
    preco_min       NUMERIC NOT NULL,
    preco_max       NUMERIC NOT NULL,
    desvio_padrao   NUMERIC NOT NULL,
    n_amostras      INTEGER NOT NULL,
    PRIMARY KEY (ano, mes, uf, categoria)
);

-- Metadados de carga (usado no rodapé do dashboard).
CREATE TABLE IF NOT EXISTS meta_carga (
    chave               TEXT PRIMARY KEY,
    ultima_atualizacao  TEXT NOT NULL
);
