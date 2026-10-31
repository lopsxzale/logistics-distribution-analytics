-- Pergunta 3: quais estados têm maior volatilidade de preço?
-- Volatilidade temporal = desvio padrão da variação % mês a mês do preço médio.
-- (A dispersão entre postos no mesmo mês é outra métrica: ver desvio_padrao em agg_preco_mensal_uf.)
-- Requer SQLite >= 3.35 (funções matemáticas) ou PostgreSQL.
WITH serie AS (
    SELECT
        uf,
        categoria,
        ano,
        mes,
        preco_medio,
        LAG(preco_medio) OVER (PARTITION BY uf, categoria ORDER BY ano, mes) AS preco_anterior
    FROM agg_preco_mensal_uf
),
variacoes AS (
    SELECT uf, categoria, preco_medio, (preco_medio / preco_anterior - 1) * 100 AS var_pct
    FROM serie
    WHERE preco_anterior IS NOT NULL
)
SELECT
    v.uf,
    e.nome_estado,
    v.categoria,
    AVG(v.preco_medio) AS preco_medio,
    SQRT(SUM((v.var_pct - m.media) * (v.var_pct - m.media)) / (COUNT(*) - 1)) AS volatilidade_pct
FROM variacoes v
JOIN (SELECT uf, categoria, AVG(var_pct) AS media FROM variacoes GROUP BY uf, categoria) m
    ON m.uf = v.uf AND m.categoria = v.categoria
JOIN dim_estado e ON e.uf = v.uf
GROUP BY v.uf, e.nome_estado, v.categoria
HAVING COUNT(*) > 1
ORDER BY v.categoria, volatilidade_pct DESC;
