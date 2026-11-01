"""Gera as imagens do README (docs/img/) a partir do site estático.

Pré-requisitos: `cd web && npm run build`, `pip install playwright` e `playwright install chromium`.
Uso: python scripts/screenshots.py
"""

from __future__ import annotations

import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "web" / "out"
DESTINO = ROOT / "docs" / "img"
# (arquivo, seletor, largura da janela, tema)
CAPTURAS = [
    ("hero.jpg", "#top", 1440, "dark"),
    ("mapa.jpg", "#prices", 1440, "dark"),
    ("risco.jpg", "#risk", 1440, "dark"),
    ("simulador.jpg", "#simulator", 1440, "dark"),
    ("sazonalidade_claro.jpg", "#seasonality", 1440, "light"),
    ("mobile.jpg", "#top", 390, "dark"),
]


class _Silencioso(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


def servir(porta: int) -> http.server.ThreadingHTTPServer:
    handler = functools.partial(_Silencioso, directory=str(SITE))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    servidor = servir(4174)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        for arquivo, seletor, largura, tema in CAPTURAS:
            pagina = navegador.new_page(viewport={"width": largura, "height": 900}, device_scale_factor=2)
            pagina.add_init_script(f"localStorage.setItem('theme', '{tema}')")
            pagina.goto("http://127.0.0.1:4174/pt/", wait_until="networkidle")
            # Rola a página inteira para disparar as animações de entrada dos gráficos.
            altura = pagina.evaluate("document.body.scrollHeight")
            for y in range(0, altura, 500):
                pagina.evaluate(f"window.scrollTo(0, {y})")
                pagina.wait_for_timeout(80)
            alvo = pagina.locator(seletor)
            alvo.scroll_into_view_if_needed()
            # O cabeçalho fixo sairia por cima da seção na captura.
            pagina.add_style_tag(content="header { display: none !important; }")
            pagina.wait_for_timeout(2500)
            alvo.screenshot(path=str(DESTINO / arquivo), type="jpeg", quality=82)
            print(f"docs/img/{arquivo}")
            pagina.close()
        navegador.close()
    servidor.shutdown()


if __name__ == "__main__":
    main()
