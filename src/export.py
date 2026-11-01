"""Exporta os painéis mensais consolidados (data/app/, versionados no git).

O banco completo (~170 MB) não cabe no GitHub nem é necessário para o site: as
análises só precisam de painéis mensais por UF, que somam poucas centenas de KB
em Parquet. src/export_web.py lê esses Parquets e gera os JSONs do site.

Uso isolado (com o banco já carregado): python src/export.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine
from referencias import CATEGORIAS_ANALISE, ESTADOS, categoria_de, normalizar_bandeira
from transform import SQL_BASE_AGREGADA, consolidar

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / "data" / "app"


def _dim_estados() -> pd.DataFrame:
    return pd.DataFrame(
        [(uf, nome, regiao) for uf, (nome, _, regiao) in ESTADOS.items()],
        columns=["uf", "nome_estado", "regiao"],
    )


def _finalizar(df: pd.DataFrame, categoricas: list[str]) -> pd.DataFrame:
    df = df.merge(_dim_estados(), on="uf", how="left")
    df.insert(0, "data", pd.to_datetime({"year": df["ano"], "month": df["mes"], "day": 1}))
    for col in ["uf", "nome_estado", "regiao", *categoricas]:
        df[col] = df[col].astype("category")
    for col in ["preco_medio", "preco_min", "preco_max", "desvio_postos"]:
        df[col] = df[col].round(4)
    return df.sort_values(["data", "uf", *categoricas]).reset_index(drop=True)


def montar_tabelas(base: pd.DataFrame) -> dict[str, pd.DataFrame]:
    base = base.copy()
    if "categoria" not in base:
        base["categoria"] = base["produto_raw"].map(categoria_de)
    base = base[base["categoria"].isin(CATEGORIAS_ANALISE)]
    base["bandeira_grupo"] = (
        base["bandeira"].map({b: normalizar_bandeira(b) for b in base["bandeira"].dropna().unique()}).fillna("OUTRAS")
    )

    uf_mensal = consolidar(base, ["ano", "mes", "uf", "categoria"])
    produto = consolidar(base, ["ano", "mes", "uf", "produto_raw"]).rename(columns={"produto_raw": "produto"})
    produto["categoria"] = produto["produto"].map(categoria_de)
    bandeira = consolidar(base, ["ano", "mes", "uf", "categoria", "bandeira_grupo"]).rename(
        columns={"bandeira_grupo": "bandeira"}
    )

    return {
        "precos_uf_mensal": _finalizar(uf_mensal, ["categoria"]),
        "precos_produto_mensal": _finalizar(produto, ["produto", "categoria"]),
        "precos_bandeira_mensal": _finalizar(bandeira, ["categoria", "bandeira"]),
    }


def exportar(base: pd.DataFrame, meta: dict) -> list[Path]:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    escritos = []
    for nome, df in montar_tabelas(base).items():
        caminho = APP_DIR / f"{nome}.parquet"
        df.to_parquet(caminho, index=False, compression="zstd")
        escritos.append(caminho)
    caminho_meta = APP_DIR / "meta.json"
    caminho_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    escritos.append(caminho_meta)
    return escritos


def main() -> int:
    engine = get_engine()
    with engine.connect() as conn:
        base = pd.read_sql(text(SQL_BASE_AGREGADA), conn)
        total, inicio, fim, n_ufs, n_municipios = conn.execute(
            text(
                "SELECT COUNT(*), MIN(data_coleta), MAX(data_coleta), "
                "COUNT(DISTINCT uf), COUNT(DISTINCT municipio) FROM fato_preco"
            )
        ).one()
        ultima = conn.execute(
            text("SELECT ultima_atualizacao FROM meta_carga WHERE chave = 'ultima_atualizacao'")
        ).scalar_one_or_none()
    meta = {
        "ultima_carga": ultima,
        "periodo_inicio": str(inicio),
        "periodo_fim": str(fim),
        "registros": int(total),
        "ufs": int(n_ufs),
        "municipios": int(n_municipios),
    }
    for caminho in exportar(base, meta):
        print(f"{caminho.relative_to(ROOT_DIR)} ({caminho.stat().st_size / 1024:,.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
