"""Extração dos dados abertos da ANP (Série Histórica de Preços de Combustíveis).

Baixa os CSVs mensais publicados pela ANP para a janela de tempo configurada
e grava em data/raw/{produto}/{ano}-{mes}.csv, junto com um manifesto
(data/raw/_manifest.json) resumindo sucessos, arquivos já existentes, meses
ainda não publicados (404) e falhas reais.

Uso: python src/extract.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"

BASE_URL = "https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/arquivos/shpc/dsan"

# produto (slug da URL da ANP) -> nome amigável, usado só para log/pastas
PRODUTOS: dict[str, str] = {
    "gasolina-etanol": "Gasolina + Etanol",
    "diesel-gnv": "Diesel + GNV",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
    "logistics-distribution-analytics/1.0 (+portfolio project)"
)

HOJE = date.today()
ANO_INICIO = int(os.getenv("ANP_ANO_INICIO", "2023"))
ANO_FIM = int(os.getenv("ANP_ANO_FIM", str(HOJE.year)))


def montar_urls() -> list[tuple[str, str, int, int]]:
    """Gera (produto, url, ano, mes) para toda a janela configurada, sem passar do mês atual."""
    tarefas: list[tuple[str, str, int, int]] = []
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        for mes in range(1, 13):
            if ano == HOJE.year and mes > HOJE.month:
                continue
            for produto in PRODUTOS:
                mm = f"{mes:02d}"
                url = f"{BASE_URL}/{ano}/precos-{produto}-{mm}.csv"
                tarefas.append((produto, url, ano, mes))
    return tarefas


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    sessao.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    sessao.mount("https://", adapter)
    sessao.mount("http://", adapter)
    return sessao


def baixar_arquivo(sessao: requests.Session, url: str, destino: Path) -> str:
    """Baixa um arquivo e retorna o status: 'sucesso' | 'ja_existia' | 'nao_publicado_404' | 'falha'."""
    if destino.exists() and destino.stat().st_size > 0:
        return "ja_existia"

    try:
        resposta = sessao.get(url, timeout=30)
    except requests.RequestException as exc:
        print(f"  [falha] {url} -> {exc}")
        return "falha"

    if resposta.status_code == 404:
        return "nao_publicado_404"

    if resposta.status_code != 200:
        print(f"  [falha] {url} -> HTTP {resposta.status_code}")
        return "falha"

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resposta.content)
    return "sucesso"


def main() -> int:
    tarefas = montar_urls()
    sessao = criar_sessao()

    resultado: dict[str, list[str]] = {
        "sucesso": [],
        "ja_existia": [],
        "nao_publicado_404": [],
        "falha": [],
    }

    print(f"Janela: {ANO_INICIO}-{ANO_FIM} | {len(tarefas)} arquivos a verificar\n")

    for produto, url, ano, mes in tarefas:
        destino = RAW_DIR / produto / f"{ano}-{mes:02d}.csv"
        status = baixar_arquivo(sessao, url, destino)
        rotulo = f"{produto} {ano}-{mes:02d}"
        resultado[status].append(rotulo)
        if status in ("sucesso", "ja_existia"):
            print(f"  [{status}] {rotulo}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifesto_path = RAW_DIR / "_manifest.json"
    manifesto_path.write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")

    total_ok = len(resultado["sucesso"]) + len(resultado["ja_existia"])
    print(
        f"\nResumo: {total_ok} arquivos disponíveis localmente, "
        f"{len(resultado['nao_publicado_404'])} ainda não publicados, "
        f"{len(resultado['falha'])} falhas."
    )
    print(f"Manifesto: {manifesto_path}")

    if len(resultado["falha"]) > 0:
        print("\nAtenção: houve falhas de download. Veja o manifesto para detalhes.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
