"""Transformações do ETL: leitura dos CSVs da ANP e consolidação estatística."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

COLUNAS_ANP = {
    "Estado - Sigla": "uf",
    "Municipio": "municipio",
    "Produto": "produto_raw",
    "Data da Coleta": "data_coleta",
    "Valor de Venda": "valor_venda",
    "Bandeira": "bandeira",
}

COLUNAS_FATO = ["data_coleta", "ano", "mes", "uf", "municipio", "produto_raw", "bandeira", "valor_venda"]

# Agregação base sobre o fato: soma e soma dos quadrados permitem recompor média e
# desvio padrão em qualquer nível de agrupamento sem reler os 2,6 milhões de linhas.
SQL_BASE_AGREGADA = """
    SELECT ano, mes, uf, produto_raw, bandeira,
           COUNT(*) AS n,
           SUM(valor_venda) AS soma,
           SUM(valor_venda * valor_venda) AS soma_quadrados,
           MIN(valor_venda) AS minimo,
           MAX(valor_venda) AS maximo
    FROM fato_preco
    GROUP BY ano, mes, uf, produto_raw, bandeira
"""


def ler_csv(caminho: Path | str) -> pd.DataFrame:
    """Lê um CSV mensal da ANP (BOM, ';', vírgula decimal) e devolve só as colunas do fato."""
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        decimal=",",
        usecols=list(COLUNAS_ANP),
        dtype={"Estado - Sigla": "string", "Municipio": "string", "Produto": "string", "Bandeira": "string"},
    ).rename(columns=COLUNAS_ANP)

    df["data_coleta"] = pd.to_datetime(df["data_coleta"], format="%d/%m/%Y", errors="coerce")
    df["valor_venda"] = pd.to_numeric(df["valor_venda"], errors="coerce")
    df["produto_raw"] = df["produto_raw"].str.strip().str.upper()
    df["uf"] = df["uf"].str.strip().str.upper()
    df = df.dropna(subset=["data_coleta", "valor_venda", "uf", "produto_raw"])
    df = df[df["valor_venda"] > 0]
    df["ano"] = df["data_coleta"].dt.year.astype(int)
    df["mes"] = df["data_coleta"].dt.month.astype(int)
    return df[COLUNAS_FATO].reset_index(drop=True)


def consolidar(base: pd.DataFrame, chaves: list[str]) -> pd.DataFrame:
    """Recompõe média, mínimo, máximo, desvio padrão amostral e n a partir da base agregada."""
    g = base.groupby(chaves, as_index=False, observed=True).agg(
        n=("n", "sum"),
        soma=("soma", "sum"),
        soma_quadrados=("soma_quadrados", "sum"),
        minimo=("minimo", "min"),
        maximo=("maximo", "max"),
    )
    variancia = (g["soma_quadrados"] - g["soma"] ** 2 / g["n"]) / (g["n"] - 1)
    variancia = variancia.where(g["n"] > 1, 0.0).clip(lower=0.0)
    return g[chaves].assign(
        preco_medio=g["soma"] / g["n"],
        preco_min=g["minimo"],
        preco_max=g["maximo"],
        desvio_postos=np.sqrt(variancia),
        n_amostras=g["n"].astype(int),
    )
