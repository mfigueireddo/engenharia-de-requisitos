"""Acesso ao banco SQLite. Só o back-end acessa o banco (ERS 2.5, RNF-20)."""

import os
import sqlite3
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "burguerja.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def caminho_banco() -> Path:
    """Arquivo do banco. Lido a cada conexão para que os testes troquem o banco
    pela variável de ambiente BURGUERJA_DB (ver tests/conftest.py)."""
    return Path(os.environ.get("BURGUERJA_DB", CAMINHO_PADRAO))


def conectar() -> sqlite3.Connection:
    conn = sqlite3.connect(caminho_banco())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar() -> None:
    """Cria as tabelas que ainda não existem, a partir de schema.sql."""
    with conectar() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
