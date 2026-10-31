"""Carga dos CSVs brutos da ANP (data/raw/) no banco (SQLite por padrão).

Cria o schema (se não existir), popula as dimensões, carrega o fato de preços
por mês (idempotente: reprocessar um mês substitui os dados daquele mês) e
recalcula o agregado mensal por UF/categoria usado pelo dashboard.

Uso: python src/load.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    Text,
    delete,
    text,
)

from db import get_engine
from estados import ESTADOS, categoria_de

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"

COLUNAS_USADAS = [
    "Regiao - Sigla",
    "Estado - Sigla",
    "Municipio",
    "Produto",
    "Data da Coleta",
    "Valor de Venda",
    "Bandeira",
]

metadata = MetaData()

dim_estado = Table(
    "dim_estado",
    metadata,
    Column("uf", Text, primary_key=True),
    Column("nome_estado", Text, nullable=False),
    Column("regiao_sigla", Text, nullable=False),
    Column("regiao_nome", Text, nullable=False),
)

dim_produto = Table(
    "dim_produto",
    metadata,
    Column("produto_raw", Text, primary_key=True),
    Column("categoria", Text, nullable=False),
)

fato_preco = Table(
    "fato_preco",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("data_coleta", Date, nullable=False),
    Column("ano", Integer, nullable=False),
    Column("mes", Integer, nullable=False),
    Column("uf", Text, ForeignKey("dim_estado.uf"), nullable=False),
    Column("municipio", Text, nullable=False),
    Column("produto_raw", Text, ForeignKey("dim_produto.produto_raw"), nullable=False),
    Column("bandeira", Text),
    Column("valor_venda", Float, nullable=False),
)

agg_preco_mensal_uf = Table(
    "agg_preco_mensal_uf",
    metadata,
    Column("ano", Integer, primary_key=True),
    Column("mes", Integer, primary_key=True),
    Column("uf", Text, ForeignKey("dim_estado.uf"), primary_key=True),
    Column("categoria", Text, primary_key=True),
    Column("preco_medio", Float, nullable=False),
    Column("preco_min", Float, nullable=False),
    Column("preco_max", Float, nullable=False),
    Column("desvio_padrao", Float, nullable=False),
    Column("n_amostras", Integer, nullable=False),
)

meta_carga = Table(
    "meta_carga",
    metadata,
    Column("chave", Text, primary_key=True),
    Column("ultima_atualizacao", Text, nullable=False),
)


def listar_csvs() -> list[Path]:
    return sorted(RAW_DIR.glob("*/*.csv"))


def ler_csv(caminho: Path) -> pd.DataFrame:
    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        decimal=",",
        usecols=COLUNAS_USADAS,
    )
    df = df.rename(
        columns={
            "Regiao - Sigla": "regiao_sigla",
            "Estado - Sigla": "uf",
            "Municipio": "municipio",
            "Produto": "produto_raw",
            "Data da Coleta": "data_coleta",
            "Valor de Venda": "valor_venda",
            "Bandeira": "bandeira",
        }
    )
    df["data_coleta"] = pd.to_datetime(df["data_coleta"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["data_coleta", "valor_venda", "uf", "produto_raw"])
    df = df[df["valor_venda"] > 0]
    df["ano"] = df["data_coleta"].dt.year
    df["mes"] = df["data_coleta"].dt.month
    return df[["data_coleta", "ano", "mes", "uf", "municipio", "produto_raw", "bandeira", "valor_venda"]]


def seed_dimensoes(conn, produtos_encontrados: set[str]) -> None:
    linhas_estado = [
        {"uf": uf, "nome_estado": nome, "regiao_sigla": regiao_sigla, "regiao_nome": regiao_nome}
        for uf, (nome, regiao_sigla, regiao_nome) in ESTADOS.items()
    ]
    conn.execute(delete(dim_estado))
    conn.execute(dim_estado.insert(), linhas_estado)

    linhas_produto = [
        {"produto_raw": produto_raw, "categoria": categoria_de(produto_raw)}
        for produto_raw in sorted(produtos_encontrados)
    ]
    conn.execute(delete(dim_produto))
    if linhas_produto:
        conn.execute(dim_produto.insert(), linhas_produto)


def carregar_fato(conn, df: pd.DataFrame) -> None:
    for (ano, mes), grupo in df.groupby(["ano", "mes"]):
        conn.execute(delete(fato_preco).where(fato_preco.c.ano == int(ano), fato_preco.c.mes == int(mes)))
        registros = grupo.drop(columns=["ano", "mes"]).assign(ano=int(ano), mes=int(mes))
        registros["data_coleta"] = registros["data_coleta"].dt.date
        conn.execute(fato_preco.insert(), registros.to_dict(orient="records"))


def recalcular_agregado(conn) -> None:
    fato_df = pd.read_sql(
        "SELECT ano, mes, uf, produto_raw, valor_venda FROM fato_preco",
        conn,
    )
    if fato_df.empty:
        return
    produto_para_categoria = {p: categoria_de(p) for p in fato_df["produto_raw"].unique()}
    fato_df["categoria"] = fato_df["produto_raw"].map(produto_para_categoria)

    agg = (
        fato_df.groupby(["ano", "mes", "uf", "categoria"])["valor_venda"]
        .agg(preco_medio="mean", preco_min="min", preco_max="max", n_amostras="count")
        .reset_index()
    )
    desvio = (
        fato_df.groupby(["ano", "mes", "uf", "categoria"])["valor_venda"]
        .apply(lambda s: float(np.std(s, ddof=1)) if len(s) > 1 else 0.0)
        .reset_index(name="desvio_padrao")
    )
    agg = agg.merge(desvio, on=["ano", "mes", "uf", "categoria"])

    conn.execute(delete(agg_preco_mensal_uf))
    conn.execute(agg_preco_mensal_uf.insert(), agg.to_dict(orient="records"))


def atualizar_meta(conn) -> None:
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conn.execute(delete(meta_carga).where(meta_carga.c.chave == "ultima_atualizacao"))
    conn.execute(meta_carga.insert(), [{"chave": "ultima_atualizacao", "ultima_atualizacao": agora}])


def main() -> int:
    csvs = listar_csvs()
    if not csvs:
        print("Nenhum CSV encontrado em data/raw/. Rode `python src/extract.py` primeiro.")
        return 1

    engine = get_engine()
    metadata.create_all(engine)

    print(f"Lendo {len(csvs)} arquivo(s) de data/raw/...")
    partes = []
    for caminho in csvs:
        df = ler_csv(caminho)
        partes.append(df)
        print(f"  {caminho.relative_to(ROOT_DIR)}: {len(df):,} linhas válidas")

    df_total = pd.concat(partes, ignore_index=True)
    produtos_encontrados = set(df_total["produto_raw"].unique())

    with engine.begin() as conn:
        seed_dimensoes(conn, produtos_encontrados)
        carregar_fato(conn, df_total)
        recalcular_agregado(conn)
        atualizar_meta(conn)

    with engine.connect() as conn:
        total_fato = conn.execute(text("SELECT COUNT(*) FROM fato_preco")).scalar_one()
        total_agg = conn.execute(text("SELECT COUNT(*) FROM agg_preco_mensal_uf")).scalar_one()
        range_datas = conn.execute(
            text("SELECT MIN(data_coleta), MAX(data_coleta) FROM fato_preco")
        ).one()
        n_ufs = conn.execute(text("SELECT COUNT(DISTINCT uf) FROM fato_preco")).scalar_one()

    print(f"\nCarga concluída: {total_fato:,} registros em fato_preco, {total_agg:,} em agg_preco_mensal_uf.")
    print(f"Período coberto: {range_datas[0]} a {range_datas[1]} | UFs presentes: {n_ufs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
