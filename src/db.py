"""Conexão com o banco de dados (SQLite por padrão, Postgres opcional via DATABASE_URL)."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "data" / "processed" / "anp_combustiveis.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"

load_dotenv(ROOT_DIR / ".env")

_engine: Engine | None = None


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = get_database_url()
        if url.startswith("sqlite"):
            DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(url, future=True)
    return _engine
