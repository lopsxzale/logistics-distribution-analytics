import numpy as np
import pandas as pd
import pytest

from referencias import categoria_de, normalizar_bandeira
from transform import consolidar, ler_csv

CABECALHO = (
    "Regiao - Sigla;Estado - Sigla;Municipio;Revenda;CNPJ da Revenda;Nome da Rua;Numero Rua;"
    "Complemento;Bairro;Cep;Produto;Data da Coleta;Valor de Venda;Valor de Compra;Unidade de Medida;Bandeira"
)


def _linha(uf, produto, data, valor, bandeira="BRANCA"):
    return f"NE;{uf};CIDADE;POSTO;00.000.000/0001-00;RUA;1;;BAIRRO;00000-000;{produto};{data};{valor};;R$ / litro;{bandeira}"


@pytest.fixture
def csv_anp(tmp_path):
    linhas = [
        CABECALHO,
        _linha("AL", "GASOLINA", "02/01/2024", "5,68"),
        _linha("AL", "ETANOL", "15/01/2024", "4,10", "VIBRA ENERGIA"),
        _linha("PE", "DIESEL S10", "31/01/2024", "6,05"),
        _linha("PE", "GASOLINA", "31/01/2024", "0"),
        _linha("PE", "GASOLINA", "data-invalida", "5,00"),
    ]
    caminho = tmp_path / "precos.csv"
    caminho.write_bytes(("\n".join(linhas) + "\n").encode("utf-8-sig"))
    return caminho


def test_ler_csv_trata_bom_separador_e_decimal(csv_anp):
    df = ler_csv(csv_anp)
    assert list(df.columns) == [
        "data_coleta",
        "ano",
        "mes",
        "uf",
        "municipio",
        "produto_raw",
        "bandeira",
        "valor_venda",
    ]
    assert len(df) == 3, "preço zero e data inválida devem ser descartados"
    assert df["valor_venda"].tolist() == pytest.approx([5.68, 4.10, 6.05])
    assert set(df["ano"]) == {2024} and set(df["mes"]) == {1}


def test_consolidar_recupera_media_e_desvio_amostral():
    rng = np.random.default_rng(0)
    valores = rng.normal(6.0, 0.3, size=500)
    lotes = np.array_split(valores, 7)
    base = pd.DataFrame(
        {
            "uf": "SP",
            "n": [len(lote) for lote in lotes],
            "soma": [lote.sum() for lote in lotes],
            "soma_quadrados": [(lote**2).sum() for lote in lotes],
            "minimo": [lote.min() for lote in lotes],
            "maximo": [lote.max() for lote in lotes],
        }
    )
    r = consolidar(base, ["uf"]).iloc[0]
    assert r["n_amostras"] == 500
    assert r["preco_medio"] == pytest.approx(valores.mean())
    assert r["desvio_postos"] == pytest.approx(valores.std(ddof=1))
    assert r["preco_min"] == valores.min() and r["preco_max"] == valores.max()


def test_consolidar_com_uma_amostra_tem_desvio_zero():
    base = pd.DataFrame(
        {"uf": ["AC"], "n": [1], "soma": [7.0], "soma_quadrados": [49.0], "minimo": [7.0], "maximo": [7.0]}
    )
    assert consolidar(base, ["uf"]).iloc[0]["desvio_postos"] == 0.0


@pytest.mark.parametrize(
    ("produto", "esperado"),
    [("GASOLINA ADITIVADA", "GASOLINA"), ("diesel s10", "DIESEL"), ("ETANOL", "ETANOL"), ("GNV", "GNV")],
)
def test_categoria_de(produto, esperado):
    assert categoria_de(produto) == esperado


@pytest.mark.parametrize(
    ("bandeira", "esperado"),
    [("VIBRA ENERGIA", "VIBRA"), ("ALE", "ALESAT"), (" ipiranga ", "IPIRANGA"), ("RODOIL", "OUTRAS"), (None, "OUTRAS")],
)
def test_normalizar_bandeira(bandeira, esperado):
    assert normalizar_bandeira(bandeira) == esperado
