-- Pergunta 4: qual o gap % entre a região mais cara e a mais barata, e como evoluiu?
WITH preco_regiao AS (
    SELECT
        a.ano,
        a.mes,
        e.regiao_sigla,
        a.categoria,
        AVG(a.preco_medio) AS preco_medio
    FROM agg_preco_mensal_uf a
    JOIN dim_estado e ON e.uf = a.uf
    GROUP BY a.ano, a.mes, e.regiao_sigla, a.categoria
)
SELECT
    ano,
    mes,
    categoria,
    MAX(preco_medio) AS preco_max_regiao,
    MIN(preco_medio) AS preco_min_regiao,
    (MAX(preco_medio) - MIN(preco_medio)) / MIN(preco_medio) * 100 AS gap_percentual
FROM preco_regiao
GROUP BY ano, mes, categoria
ORDER BY categoria, ano, mes;
