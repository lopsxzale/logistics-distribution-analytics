-- Pergunta 2: existe sazonalidade (meses/períodos com maior variação de preço)?
-- Agrega todos os anos por mês-calendário para revelar padrão sazonal por categoria.
SELECT
    mes,
    categoria,
    AVG(preco_medio) AS preco_medio_mes,
    MAX(preco_medio) - MIN(preco_medio) AS amplitude
FROM agg_preco_mensal_uf
GROUP BY mes, categoria
ORDER BY categoria, mes;
