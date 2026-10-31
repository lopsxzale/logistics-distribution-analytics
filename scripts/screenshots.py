"""Captura screenshots de todas as páginas do dashboard (para o README e revisão visual).

Pré-requisito: o app rodando (streamlit run dashboard/app.py) e `playwright install chromium`.
Uso: python scripts/screenshots.py [--url http://localhost:8501] [--mobile]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "img"
PAGINAS = {
    "visao_geral": "",
    "evolucao": "evolucao",
    "sazonalidade": "sazonalidade",
    "risco": "risco",
    "gap_regional": "gap_regional",
    "etanol_gasolina": "etanol_gasolina",
    "bandeiras_produtos": "bandeiras_produtos",
    "simulador": "simulador",
    "sobre": "sobre",
}


def capturar(url_base: str, mobile: bool, paginas: list[str]) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    viewport = {"width": 390, "height": 844} if mobile else {"width": 1440, "height": 900}
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport=viewport, device_scale_factor=2 if mobile else 1)
        for nome in paginas:
            pagina.goto(f"{url_base.rstrip('/')}/{PAGINAS[nome]}", wait_until="networkidle")
            pagina.wait_for_selector('[data-testid="stMainBlockContainer"]', timeout=60_000)
            if nome != "sobre":
                pagina.wait_for_selector(".js-plotly-plot", timeout=60_000)
            pagina.wait_for_timeout(1500)
            # O Streamlit rola dentro de [data-testid=stMain], não no body: amplia a janela até caber tudo.
            altura = pagina.evaluate("document.querySelector('[data-testid=\"stMain\"]').scrollHeight")
            pagina.set_viewport_size({"width": viewport["width"], "height": max(altura, viewport["height"])})
            pagina.wait_for_timeout(1500)
            destino = SAIDA / f"{'mobile_' if mobile else ''}{nome}.png"
            pagina.screenshot(path=str(destino), full_page=True)
            pagina.set_viewport_size(viewport)
            print(destino.relative_to(SAIDA.parent.parent))
        navegador.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8501")
    parser.add_argument("--mobile", action="store_true")
    parser.add_argument("paginas", nargs="*", default=list(PAGINAS))
    args = parser.parse_args()
    capturar(args.url, args.mobile, args.paginas)
