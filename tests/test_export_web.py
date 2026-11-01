"""Contrato dos JSONs do site: estrutura, cobertura e consistência com src/metrics.py.

Os testes leem os JSONs versionados em web/src/data/ (o que o site publica) e
recalculam os números-chave direto dos Parquets, para que site e análise nunca divirjam.
"""

import json
import math

import pandas as pd
import pytest

import export_web
import metrics

UFS = 27


@pytest.fixture(scope="module")
def site():
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in export_web.WEB_DATA_DIR.glob("*.json")}


@pytest.fixture(scope="module")
def painel_uf():
    return export_web.load_panels()[0]


def _sem_nan(valor):
    if isinstance(valor, dict):
        return all(_sem_nan(v) for v in valor.values())
    if isinstance(valor, list):
        return all(_sem_nan(v) for v in valor)
    return not (isinstance(valor, float) and math.isnan(valor))


def test_todos_os_arquivos_que_o_site_importa_existem(site):
    esperados = {
        "meta",
        "states",
        "evolution",
        "seasonality",
        "risk",
        "gap",
        "ethanol",
        "brands",
        "simulator",
        "findings",
        "ufs",
        "sql",
    }
    assert esperados <= set(site)


def test_json_valido_sem_nan(site):
    for nome, payload in site.items():
        assert _sem_nan(payload), nome


def test_cobertura_de_estados_e_combustiveis(site):
    assert len(site["ufs"]) == UFS
    for fuel in export_web.FUELS:
        assert len([s for s in site["states"]["states"] if s["fuel"] == fuel]) == UFS
        assert len([s for s in site["simulator"]["prices"] if s["fuel"] == fuel]) == UFS
        assert len([s for s in site["seasonality"]["index"] if s["fuel"] == fuel]) == 12
    assert len(site["ethanol"]["states"]) == UFS


def test_sql_de_cada_pergunta_esta_disponivel(site):
    assert {f"q{i}" for i in range(1, 7)} <= {k.split("_")[0] for k in site["sql"]}


def test_variacao_do_periodo_bate_com_metrics(site, painel_uf):
    for fuel in export_web.FUELS:
        serie = metrics.serie_nacional(painel_uf[painel_uf["categoria"] == fuel])
        esperado = metrics.variacao_pct(serie["preco_medio"].iloc[-1], serie["preco_medio"].iloc[0])
        assert site["findings"]["change_pct"][fuel] == pytest.approx(esperado, abs=1e-3)


def test_gap_regional_anual_bate_com_metrics(site, painel_uf):
    gap = metrics.gap_regional(painel_uf[painel_uf["categoria"] == "DIESEL"])
    por_ano = gap.groupby(gap["data"].dt.year)["gap_pct"].mean()
    for ano, valor in por_ano.items():
        assert site["findings"]["gap_by_year"][str(ano)] == pytest.approx(valor, abs=1e-3)


def test_paridade_do_etanol_coerente_com_o_limiar(site):
    eth = site["ethanol"]
    for s in eth["states"]:
        assert s["worth"] == (s["ratio"] <= eth["threshold"])
    assert site["findings"]["ethanol_worth_count"] == sum(s["worth"] for s in eth["states"])


def test_diferenca_vs_media_nacional_e_consistente(site):
    nacional = site["states"]["national"]
    for s in site["states"]["states"]:
        esperado = (s["price"] / nacional[s["fuel"]]["last"] - 1) * 100
        assert s["diff_pct"] == pytest.approx(esperado, abs=0.01)


def test_normalize_converte_tipos_do_pandas():
    payload = {"d": pd.Timestamp("2025-12-01"), "x": float("nan"), "y": 1.234567, "lista": (1, 2)}
    assert export_web._normalize(payload) == {"d": "2025-12", "x": None, "y": 1.2346, "lista": [1, 2]}
