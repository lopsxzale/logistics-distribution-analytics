"""Métricas analíticas sobre o painel mensal de preços (uma linha por mês × UF × categoria).

Todas as funções são puras: recebem DataFrames com as colunas exportadas por
src/export.py (data, uf, regiao, categoria, preco_medio, desvio_postos,
n_amostras, ...) e não dependem de banco, Streamlit ou arquivos.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

LIMIAR_PARIDADE = 0.70  # etanol compensa quando custa até 70% da gasolina (rendimento ~30% menor)


def media_ponderada(df: pd.DataFrame, por: Sequence[str]) -> pd.DataFrame:
    """Preço médio ponderado pelo nº de coletas — evita que UFs com poucas coletas distorçam a média."""
    por = list(por)
    g = (
        df.assign(_soma=df["preco_medio"] * df["n_amostras"])
        .groupby(por, as_index=False, observed=True)
        .agg(_soma=("_soma", "sum"), n_amostras=("n_amostras", "sum"))
    )
    g["preco_medio"] = g["_soma"] / g["n_amostras"]
    return g.drop(columns="_soma")


def serie_nacional(df: pd.DataFrame) -> pd.DataFrame:
    return media_ponderada(df, ["data"]).sort_values("data").reset_index(drop=True)


def variacao_pct(atual: float, anterior: float) -> float:
    return (atual - anterior) / anterior * 100 if anterior else 0.0


def variacoes_mensais(df: pd.DataFrame, por: str = "uf") -> pd.DataFrame:
    """Variação % mês contra mês do preço médio, dentro de cada grupo."""
    s = media_ponderada(df, [por, "data"]).sort_values([por, "data"])
    s["var_pct"] = s.groupby(por, observed=True)["preco_medio"].pct_change() * 100
    return s.reset_index(drop=True)


def volatilidade_temporal(df: pd.DataFrame, por: str = "uf") -> pd.DataFrame:
    """Desvio padrão das variações % mensais: quanto o preço 'balança' de um mês para o outro."""
    v = variacoes_mensais(df, por)
    out = (
        v.groupby(por, observed=True)
        .agg(
            preco_medio=("preco_medio", "mean"),
            volatilidade=("var_pct", "std"),
            n_meses=("data", "nunique"),
        )
        .reset_index()
    )
    return out.dropna(subset=["volatilidade"]).sort_values("volatilidade", ascending=False, ignore_index=True)


def dispersao_postos(df: pd.DataFrame, por: str = "uf") -> pd.DataFrame:
    """Coeficiente de variação entre postos no mesmo mês (%): quanto vale pesquisar preço na mesma UF."""
    cv = df["desvio_postos"] / df["preco_medio"] * 100
    out = (
        df.assign(_cv_peso=cv * df["n_amostras"])
        .groupby(por, as_index=False, observed=True)
        .agg(_cv_peso=("_cv_peso", "sum"), n_amostras=("n_amostras", "sum"))
    )
    out["dispersao"] = out["_cv_peso"] / out["n_amostras"]
    return out.drop(columns="_cv_peso").sort_values("dispersao", ascending=False, ignore_index=True)


def gap_regional(df: pd.DataFrame) -> pd.DataFrame:
    """Por mês: região mais cara, mais barata e o gap % entre elas."""
    r = media_ponderada(df, ["data", "regiao"])
    mais_cara = r.loc[r.groupby("data")["preco_medio"].idxmax(), ["data", "regiao", "preco_medio"]]
    mais_barata = r.loc[r.groupby("data")["preco_medio"].idxmin(), ["data", "regiao", "preco_medio"]]
    out = mais_cara.merge(mais_barata, on="data", suffixes=("_max", "_min"))
    out = out.rename(
        columns={
            "regiao_max": "regiao_mais_cara",
            "regiao_min": "regiao_mais_barata",
            "preco_medio_max": "preco_max",
            "preco_medio_min": "preco_min",
        }
    )
    out["gap_pct"] = (out["preco_max"] - out["preco_min"]) / out["preco_min"] * 100
    return out.sort_values("data").reset_index(drop=True)


def indice_sazonal(df: pd.DataFrame) -> pd.DataFrame:
    """Preço de cada mês relativo à média do próprio ano (=100), resumido por mês-calendário.

    Normalizar pelo ano remove a tendência de longo prazo; usa só anos completos
    quando há ao menos um, para que anos parciais não enviesem o índice.
    """
    s = serie_nacional(df)
    s["ano"] = s["data"].dt.year
    s["mes"] = s["data"].dt.month
    meses_por_ano = s.groupby("ano")["mes"].transform("nunique")
    if (meses_por_ano == 12).any():
        s = s[meses_por_ano == 12]
    s["indice"] = s["preco_medio"] / s.groupby("ano")["preco_medio"].transform("mean") * 100
    return (
        s.groupby("mes")
        .agg(
            indice_medio=("indice", "mean"),
            indice_min=("indice", "min"),
            indice_max=("indice", "max"),
            n_anos=("ano", "nunique"),
        )
        .reset_index()
    )


def indice_base_100(df: pd.DataFrame, por: str = "categoria") -> pd.DataFrame:
    """Preço relativo ao primeiro mês do período (=100), para comparar trajetórias de níveis diferentes."""
    s = media_ponderada(df, [por, "data"]).sort_values([por, "data"])
    base = s.groupby(por, observed=True)["preco_medio"].transform("first")
    s["indice"] = s["preco_medio"] / base * 100
    return s.reset_index(drop=True)


def paridade_etanol_gasolina(df: pd.DataFrame, por: Sequence[str] = ("uf",)) -> pd.DataFrame:
    """Razão preço etanol / preço gasolina. Abaixo de 0,70 o etanol compensa."""
    por = list(por)
    base = df[df["categoria"].isin(["ETANOL", "GASOLINA"])]
    m = media_ponderada(base, [*por, "categoria"])
    tabela = m.pivot_table(index=por, columns="categoria", values="preco_medio", observed=True).reset_index()
    tabela = tabela.dropna(subset=["ETANOL", "GASOLINA"])
    tabela.columns.name = None
    tabela = tabela.rename(columns={"ETANOL": "preco_etanol", "GASOLINA": "preco_gasolina"})
    tabela["razao"] = tabela["preco_etanol"] / tabela["preco_gasolina"]
    tabela["etanol_compensa"] = tabela["razao"] <= LIMIAR_PARIDADE
    return tabela


def premio_produto(df_produto: pd.DataFrame, premium: str, base: str, por: str = "data") -> pd.DataFrame:
    """Quanto o produto premium (ex.: DIESEL S10) custa a mais que o básico, em R$ e em %."""
    m = media_ponderada(df_produto[df_produto["produto"].isin([premium, base])], [por, "produto"])
    t = m.pivot_table(index=por, columns="produto", values="preco_medio", observed=True)
    if premium not in t or base not in t:
        return pd.DataFrame(columns=[por, premium, base, "premio_rs", "premio_pct"])
    t = t[[premium, base]].dropna().reset_index()
    t.columns.name = None
    t["premio_rs"] = t[premium] - t[base]
    t["premio_pct"] = t["premio_rs"] / t[base] * 100
    return t


def custo_frota(preco_litro, km_mes: float, consumo_km_l: float, veiculos: int = 1):
    """Custo mensal de combustível: litros consumidos × preço. Aceita escalar ou Series de preços."""
    if consumo_km_l <= 0:
        raise ValueError("consumo_km_l deve ser positivo")
    return preco_litro * (km_mes / consumo_km_l) * veiculos
