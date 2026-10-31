-- Pergunta 3: quais estados têm maior volatilidade de preço?
-- (relevante para planejamento de rotas/estoque: estados mais voláteis exigem
-- margem de segurança maior no planejamento de custo de combustível)
SELECT
    uf,
    categoria,
    AVG(desvio_padrao) AS desvio_medio,
    AVG(preco_medio) AS preco_medio,
    AVG(desvio_padrao) / AVG(preco_medio) AS coef_variacao
FROM agg_preco_mensal_uf
GROUP BY uf, categoria
ORDER BY coef_variacao DESC;
