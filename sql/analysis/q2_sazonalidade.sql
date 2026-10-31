-- Pergunta 2: existe sazonalidade (meses com preço sistematicamente maior ou menor)?
-- Índice sazonal = preço nacional do mês / média do próprio ano * 100, resumido por mês-calendário.
-- Normalizar pelo ano remove a tendência de longo prazo (mesma regra do dashboard).
WITH nacional AS (
    SELECT ano, mes, categoria, SUM(preco_medio * n_amostras) / SUM(n_amostras) AS preco_medio
    FROM agg_preco_mensal_uf
    GROUP BY ano, mes, categoria
),
indice AS (
    SELECT
        ano,
        mes,
        categoria,
        preco_medio / AVG(preco_medio) OVER (PARTITION BY ano, categoria) * 100 AS indice
    FROM nacional
)
SELECT
    categoria,
    mes,
    AVG(indice) AS indice_medio,
    MIN(indice) AS indice_min,
    MAX(indice) AS indice_max
FROM indice
GROUP BY categoria, mes
ORDER BY categoria, mes;
