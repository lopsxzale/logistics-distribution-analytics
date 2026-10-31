import pandas as pd
import pytest

import metrics


def painel(linhas):
    """linhas: (data 'AAAA-MM', uf, regiao, categoria, preco, n)."""
    df = pd.DataFrame(linhas, columns=["data", "uf", "regiao", "categoria", "preco_medio", "n_amostras"])
    df["data"] = pd.to_datetime(df["data"])
    df["desvio_postos"] = df["preco_medio"] * 0.05
    return df


def test_media_ponderada_respeita_numero_de_coletas():
    df = painel([("2024-01", "SP", "Sudeste", "DIESEL", 6.0, 300), ("2024-01", "AC", "Norte", "DIESEL", 8.0, 100)])
    r = metrics.media_ponderada(df, ["data"]).iloc[0]
    assert r["preco_medio"] == pytest.approx(6.5)
    assert r["n_amostras"] == 400


def test_volatilidade_temporal_ordena_mais_instavel_primeiro():
    df = painel(
        [
            ("2024-01", "SP", "Sudeste", "DIESEL", 6.0, 10),
            ("2024-02", "SP", "Sudeste", "DIESEL", 6.0, 10),
            ("2024-03", "SP", "Sudeste", "DIESEL", 6.0, 10),
            ("2024-01", "AM", "Norte", "DIESEL", 6.0, 10),
            ("2024-02", "AM", "Norte", "DIESEL", 6.6, 10),
            ("2024-03", "AM", "Norte", "DIESEL", 6.0, 10),
        ]
    )
    v = metrics.volatilidade_temporal(df)
    assert v["uf"].tolist() == ["AM", "SP"]
    assert v.loc[v["uf"] == "SP", "volatilidade"].iloc[0] == pytest.approx(0.0)


def test_dispersao_postos_e_cv_ponderado():
    df = painel([("2024-01", "SP", "Sudeste", "DIESEL", 6.0, 10)])
    assert metrics.dispersao_postos(df).iloc[0]["dispersao"] == pytest.approx(5.0)


def test_gap_regional_identifica_extremos():
    df = painel(
        [
            ("2024-01", "AM", "Norte", "DIESEL", 7.0, 10),
            ("2024-01", "SP", "Sudeste", "DIESEL", 5.0, 10),
            ("2024-01", "RS", "Sul", "DIESEL", 6.0, 10),
        ]
    )
    g = metrics.gap_regional(df).iloc[0]
    assert g["regiao_mais_cara"] == "Norte" and g["regiao_mais_barata"] == "Sudeste"
    assert g["gap_pct"] == pytest.approx(40.0)


def test_indice_sazonal_media_anual_igual_a_100():
    linhas = [(f"2024-{m:02d}", "SP", "Sudeste", "DIESEL", 5.0 + m / 10, 10) for m in range(1, 13)]
    s = metrics.indice_sazonal(painel(linhas))
    assert len(s) == 12
    assert s["indice_medio"].mean() == pytest.approx(100.0)
    assert s.loc[s["mes"] == 12, "indice_medio"].iloc[0] > s.loc[s["mes"] == 1, "indice_medio"].iloc[0]


def test_indice_sazonal_ignora_ano_parcial_quando_ha_ano_completo():
    linhas = [(f"2024-{m:02d}", "SP", "Sudeste", "DIESEL", 5.0, 10) for m in range(1, 13)]
    linhas.append(("2025-01", "SP", "Sudeste", "DIESEL", 50.0, 10))
    s = metrics.indice_sazonal(painel(linhas))
    assert s["n_anos"].max() == 1
    assert s["indice_medio"].tolist() == pytest.approx([100.0] * 12)


def test_indice_base_100_comeca_em_100():
    df = painel([("2024-01", "SP", "Sudeste", "ETANOL", 4.0, 10), ("2024-02", "SP", "Sudeste", "ETANOL", 4.4, 10)])
    i = metrics.indice_base_100(df)
    assert i["indice"].tolist() == pytest.approx([100.0, 110.0])


def test_paridade_etanol_gasolina_aplica_regra_dos_70():
    df = painel(
        [
            ("2024-01", "SP", "Sudeste", "ETANOL", 3.5, 10),
            ("2024-01", "SP", "Sudeste", "GASOLINA", 5.5, 10),
            ("2024-01", "AM", "Norte", "ETANOL", 5.0, 10),
            ("2024-01", "AM", "Norte", "GASOLINA", 6.0, 10),
        ]
    )
    p = metrics.paridade_etanol_gasolina(df).set_index("uf")
    assert bool(p.loc["SP", "etanol_compensa"]) is True
    assert bool(p.loc["AM", "etanol_compensa"]) is False
    assert p.loc["AM", "razao"] == pytest.approx(5 / 6)


def test_premio_produto():
    df = pd.DataFrame(
        {
            "data": pd.to_datetime(["2024-01-01", "2024-01-01"]),
            "produto": ["DIESEL S10", "DIESEL"],
            "preco_medio": [6.3, 6.0],
            "n_amostras": [10, 10],
        }
    )
    df["produto"] = df["produto"].astype(pd.CategoricalDtype(["DIESEL", "DIESEL S10", "GASOLINA"]))
    p = metrics.premio_produto(df, premium="DIESEL S10", base="DIESEL").iloc[0]
    assert p["premio_rs"] == pytest.approx(0.3)
    assert p["premio_pct"] == pytest.approx(5.0)


def test_premio_produto_sem_dados_retorna_vazio():
    df = pd.DataFrame(
        {"data": pd.to_datetime(["2024-01-01"]), "produto": ["DIESEL"], "preco_medio": [6.0], "n_amostras": [10]}
    )
    assert metrics.premio_produto(df, premium="DIESEL S10", base="DIESEL").empty


def test_custo_frota():
    assert metrics.custo_frota(6.0, km_mes=3000, consumo_km_l=3.0, veiculos=2) == pytest.approx(12000.0)
    with pytest.raises(ValueError):
        metrics.custo_frota(6.0, km_mes=1000, consumo_km_l=0)
