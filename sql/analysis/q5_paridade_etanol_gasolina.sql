-- Pergunta 5 (frota flex): em quais estados o etanol compensa?
-- Regra de mercado: etanol vale a pena quando custa até 70% do preço da gasolina.
-- Usa os últimos 3 meses disponíveis, com média ponderada pelo nº de coletas.
WITH recorte AS (
    SELECT *
    FROM agg_preco_mensal_uf
    WHERE ano * 12 + mes > (SELECT MAX(ano * 12 + mes) - 3 FROM agg_preco_mensal_uf)
),
precos AS (
    SELECT
        uf,
        SUM(CASE WHEN categoria = 'ETANOL' THEN preco_medio * n_amostras END)
            / SUM(CASE WHEN categoria = 'ETANOL' THEN n_amostras END) AS preco_etanol,
        SUM(CASE WHEN categoria = 'GASOLINA' THEN preco_medio * n_amostras END)
            / SUM(CASE WHEN categoria = 'GASOLINA' THEN n_amostras END) AS preco_gasolina
    FROM recorte
    GROUP BY uf
)
SELECT
    p.uf,
    e.nome_estado,
    p.preco_etanol,
    p.preco_gasolina,
    p.preco_etanol / p.preco_gasolina * 100 AS razao_pct,
    CASE WHEN p.preco_etanol / p.preco_gasolina <= 0.70 THEN 'etanol' ELSE 'gasolina' END AS compensa
FROM precos p
JOIN dim_estado e ON e.uf = p.uf
ORDER BY razao_pct;
