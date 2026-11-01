"""Carga dos CSVs brutos da ANP (data/raw/) no banco e geração dos dados do site.

1. Cria o schema (SQLAlchemy Core — funciona em SQLite e Postgres).
2. Popula as dimensões e carrega o fato arquivo a arquivo. É idempotente:
   reprocessar um arquivo substitui só os meses/produtos daquele arquivo.
3. Recalcula o agregado mensal por UF/categoria (só combustíveis em R$/litro).
4. Exporta os Parquet versionados em data/app/ (ver src/export.py) e, a partir deles,
   os JSONs do site em web/src/data/ (ver src/export_web.py).

Uso: python src/load.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    MetaData,
    Table,
    Text,
    delete,
    select,
    text,
)

import export
import export_web
from db import get_engine
from referencias import CATEGORIAS_ANALISE, ESTADOS, MAPA_PRODUTO, categoria_de
from transform import SQL_BASE_AGREGADA, consolidar, ler_csv

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"

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
    Column("ano", Integer, nullable=False, index=True),
    Column("mes", Integer, nullable=False, index=True),
    Column("uf", Text, nullable=False, index=True),
    Column("municipio", Text, nullable=False),
    Column("produto_raw", Text, nullable=False, index=True),
    Column("bandeira", Text),
    Column("valor_venda", Float, nullable=False),
)

agg_preco_mensal_uf = Table(
    "agg_preco_mensal_uf",
    metadata,
    Column("ano", Integer, primary_key=True),
    Column("mes", Integer, primary_key=True),
    Column("uf", Text, primary_key=True),
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


def seed_dimensoes(conn) -> None:
    conn.execute(delete(dim_estado))
    conn.execute(
        dim_estado.insert(),
        [
            {"uf": uf, "nome_estado": nome, "regiao_sigla": sigla, "regiao_nome": regiao}
            for uf, (nome, sigla, regiao) in ESTADOS.items()
        ],
    )


def registrar_produtos(conn, produtos: set[str]) -> None:
    existentes = set(conn.execute(select(dim_produto.c.produto_raw)).scalars())
    novos = sorted(produtos - existentes)
    if novos:
        conn.execute(dim_produto.insert(), [{"produto_raw": p, "categoria": categoria_de(p)} for p in novos])


def carregar_arquivo(conn, df: pd.DataFrame) -> None:
    """Substitui no fato os meses × produtos presentes neste arquivo."""
    produtos = sorted(df["produto_raw"].unique())
    for (ano, mes), grupo in df.groupby(["ano", "mes"]):
        conn.execute(
            delete(fato_preco).where(
                fato_preco.c.ano == int(ano),
                fato_preco.c.mes == int(mes),
                fato_preco.c.produto_raw.in_(produtos),
            )
        )
        registros = grupo.assign(data_coleta=grupo["data_coleta"].dt.date)
        conn.execute(fato_preco.insert(), registros.to_dict(orient="records"))


def ler_base_agregada(conn) -> pd.DataFrame:
    base = pd.read_sql(text(SQL_BASE_AGREGADA), conn)
    base["categoria"] = base["produto_raw"].map(categoria_de)
    return base


def recalcular_agregado(conn, base: pd.DataFrame) -> int:
    analise = base[base["categoria"].isin(CATEGORIAS_ANALISE)]
    agg = consolidar(analise, ["ano", "mes", "uf", "categoria"]).rename(columns={"desvio_postos": "desvio_padrao"})
    conn.execute(delete(agg_preco_mensal_uf))
    conn.execute(agg_preco_mensal_uf.insert(), agg.to_dict(orient="records"))
    return len(agg)


def atualizar_meta(conn) -> str:
    agora = datetime.now(UTC).isoformat(timespec="seconds")
    conn.execute(delete(meta_carga).where(meta_carga.c.chave == "ultima_atualizacao"))
    conn.execute(meta_carga.insert(), [{"chave": "ultima_atualizacao", "ultima_atualizacao": agora}])
    return agora


def main() -> int:
    csvs = sorted(RAW_DIR.glob("*/*.csv"))
    if not csvs:
        print("Nenhum CSV encontrado em data/raw/. Rode `python src/extract.py` primeiro.")
        return 1

    engine = get_engine()
    metadata.create_all(engine)

    with engine.begin() as conn:
        seed_dimensoes(conn)
        registrar_produtos(conn, set(MAPA_PRODUTO))

    print(f"Carregando {len(csvs)} arquivo(s) de data/raw/...")
    for caminho in csvs:
        df = ler_csv(caminho)
        with engine.begin() as conn:
            registrar_produtos(conn, set(df["produto_raw"].unique()))
            carregar_arquivo(conn, df)
        print(f"  {caminho.relative_to(ROOT_DIR)}: {len(df):,} linhas")

    with engine.begin() as conn:
        base = ler_base_agregada(conn)
        n_agg = recalcular_agregado(conn, base)
        ultima_carga = atualizar_meta(conn)
        resumo = conn.execute(
            text(
                "SELECT COUNT(*), MIN(data_coleta), MAX(data_coleta), "
                "COUNT(DISTINCT uf), COUNT(DISTINCT municipio) FROM fato_preco"
            )
        ).one()

    total, inicio, fim, n_ufs, n_municipios = resumo
    print(f"\nFato: {total:,} registros | agregado: {n_agg:,} linhas")
    print(f"Período: {inicio} a {fim} | UFs: {n_ufs} | municípios: {n_municipios}")

    arquivos = export.exportar(
        base,
        meta={
            "ultima_carga": ultima_carga,
            "periodo_inicio": str(inicio),
            "periodo_fim": str(fim),
            "registros": int(total),
            "ufs": int(n_ufs),
            "municipios": int(n_municipios),
        },
    )
    arquivos += export_web.export()
    print("Export (Parquet + JSONs do site):")
    for caminho in arquivos:
        print(f"  {caminho.relative_to(ROOT_DIR)} ({caminho.stat().st_size / 1024:,.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
