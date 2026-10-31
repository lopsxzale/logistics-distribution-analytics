"""Carregamento (em cache) dos dados exportados em data/app/ e estado dos filtros globais."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent.parent / "data" / "app"

CATEGORIAS = ("DIESEL", "GASOLINA", "ETANOL")
ROTULO = {"DIESEL": "Diesel", "GASOLINA": "Gasolina", "ETANOL": "Etanol"}
REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")


@st.cache_data(show_spinner=False)
def painel_uf() -> pd.DataFrame:
    return pd.read_parquet(APP_DIR / "precos_uf_mensal.parquet")


@st.cache_data(show_spinner=False)
def painel_produto() -> pd.DataFrame:
    return pd.read_parquet(APP_DIR / "precos_produto_mensal.parquet")


@st.cache_data(show_spinner=False)
def painel_bandeira() -> pd.DataFrame:
    return pd.read_parquet(APP_DIR / "precos_bandeira_mensal.parquet")


@st.cache_data(show_spinner=False)
def meta() -> dict:
    return json.loads((APP_DIR / "meta.json").read_text(encoding="utf-8"))


@st.cache_resource(show_spinner=False)
def contornos_estados() -> dict[str, tuple[list, list]]:
    """uf -> (xs, ys) dos anéis externos, separados por None — pronto para Scatter(fill='toself').

    Desenhar o mapa como polígonos cartesianos evita o download do mapa-múndi base que o
    Plotly geo faz da CDN a cada carga, então o mapa aparece junto com os outros gráficos.
    """
    gj = json.loads((APP_DIR / "br_estados.geojson").read_text(encoding="utf-8"))
    contornos = {}
    for feat in gj["features"]:
        geom = feat["geometry"]
        poligonos = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        xs, ys = [], []
        for poligono in poligonos:
            externo = poligono[0]
            xs += [p[0] for p in externo] + [None]
            ys += [p[1] for p in externo] + [None]
        contornos[feat["properties"]["sigla"]] = (xs, ys)
    return contornos


@st.cache_data(show_spinner=False)
def meses_disponiveis() -> list[pd.Timestamp]:
    return sorted(painel_uf()["data"].unique())


def dados_disponiveis() -> bool:
    return (APP_DIR / "precos_uf_mensal.parquet").exists()


@dataclass(frozen=True)
class Filtros:
    categoria: str
    inicio: pd.Timestamp
    fim: pd.Timestamp
    regioes: tuple[str, ...]

    @property
    def rotulo(self) -> str:
        return ROTULO[self.categoria]


def filtros() -> Filtros:
    meses = meses_disponiveis()
    inicio, fim = st.session_state.get("f_periodo", (meses[0], meses[-1]))
    regioes = tuple(st.session_state.get("f_regioes") or REGIOES)
    return Filtros(
        categoria=st.session_state.get("f_categoria") or "DIESEL",
        inicio=pd.Timestamp(inicio),
        fim=pd.Timestamp(fim),
        regioes=regioes,
    )


def aplicar(df: pd.DataFrame, f: Filtros, por_categoria: bool = True) -> pd.DataFrame:
    mascara = df["data"].between(f.inicio, f.fim) & df["regiao"].isin(f.regioes)
    if por_categoria:
        mascara &= df["categoria"] == f.categoria
    return df[mascara]
