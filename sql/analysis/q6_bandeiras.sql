-- Pergunta 6: quanto as grandes bandeiras cobram a mais que os postos de bandeira branca?
-- Consulta direto o fato; rebrandings unificados (VIBRA ENERGIA -> VIBRA, ALE -> ALESAT).
WITH fato AS (
    SELECT
        CASE
            WHEN p.produto_raw IN ('DIESEL', 'DIESEL S10') THEN 'DIESEL'
            WHEN p.produto_raw IN ('GASOLINA', 'GASOLINA ADITIVADA') THEN 'GASOLINA'
            ELSE p.produto_raw
        END AS categoria,
        CASE
            WHEN UPPER(TRIM(p.bandeira)) = 'VIBRA ENERGIA' THEN 'VIBRA'
            WHEN UPPER(TRIM(p.bandeira)) = 'ALE' THEN 'ALESAT'
            WHEN UPPER(TRIM(p.bandeira)) IN ('BRANCA', 'IPIRANGA', 'VIBRA', 'RAIZEN', 'ALESAT') THEN UPPER(TRIM(p.bandeira))
            ELSE 'OUTRAS'
        END AS bandeira,
        p.valor_venda
    FROM fato_preco p
    WHERE p.produto_raw <> 'GNV'
),
por_bandeira AS (
    SELECT categoria, bandeira, AVG(valor_venda) AS preco_medio, COUNT(*) AS coletas
    FROM fato
    GROUP BY categoria, bandeira
)
SELECT
    b.categoria,
    b.bandeira,
    b.preco_medio,
    b.coletas,
    (b.preco_medio / branca.preco_medio - 1) * 100 AS premio_sobre_branca_pct
FROM por_bandeira b
JOIN por_bandeira branca ON branca.categoria = b.categoria AND branca.bandeira = 'BRANCA'
ORDER BY b.categoria, premio_sobre_branca_pct DESC;
