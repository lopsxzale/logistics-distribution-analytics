"""Smoke tests do dashboard: cada página renderiza sem exceções, com filtros padrão e alterados."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "dashboard" / "app.py")
PAGINAS = [
    "views/visao_geral.py",
    "views/evolucao.py",
    "views/sazonalidade.py",
    "views/risco.py",
    "views/gap_regional.py",
    "views/etanol_gasolina.py",
    "views/bandeiras_produtos.py",
    "views/simulador.py",
    "views/sobre.py",
]


def abrir(pagina: str, **estado) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=90)
    for chave, valor in estado.items():
        at.session_state[chave] = valor
    at.run()
    at.switch_page(pagina)
    at.run()
    return at


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_renderiza_com_filtros_padrao(pagina):
    at = abrir(pagina)
    assert not at.exception, at.exception


@pytest.mark.parametrize("pagina", PAGINAS)
@pytest.mark.parametrize(
    "estado",
    [
        {"f_categoria": "ETANOL", "f_regioes": ["Sul", "Sudeste"]},
        {"f_categoria": "GASOLINA", "f_regioes": ["Norte"]},
    ],
    ids=["etanol-sul-sudeste", "gasolina-norte"],
)
def test_pagina_renderiza_com_filtros_alterados(pagina, estado):
    at = abrir(pagina, **estado)
    assert not at.exception, at.exception


def test_visao_geral_mostra_kpis_e_graficos():
    at = abrir("views/visao_geral.py")
    assert len(at.metric) == 4
    assert len(at.get("plotly_chart")) == 2
