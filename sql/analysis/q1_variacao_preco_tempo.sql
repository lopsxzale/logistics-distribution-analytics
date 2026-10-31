-- Pergunta 1: como o preço médio de combustíveis varia por estado/região ao longo do tempo?
SELECT
    a.ano,
    a.mes,
    e.regiao_nome,
    a.uf,
    a.categoria,
    a.preco_medio
FROM agg_preco_mensal_uf a
JOIN dim_estado e ON e.uf = a.uf
ORDER BY a.ano, a.mes, e.regiao_nome, a.uf;
