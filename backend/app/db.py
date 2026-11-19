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
    # check_same_thread=False: o FastAPI abre a conexão (dependência `conexao`)
    # numa thread e roda a rota em outra. Com o padrão (True), a rota falhava com
    # ProgrammingError, o rollback também falhava, a transação ficava aberta e as
    # requisições seguintes recebiam "database is locked" (erro 500). Cada
    # conexão continua sendo usada por uma requisição só.
    conn = sqlite3.connect(caminho_banco(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Tabelas do esquema anterior ao projeto relacional (antes de 2026-11-19).
_TABELAS_ANTIGAS = ("produto", "combo_componente", "item", "endereco")


def inicializar() -> None:
    """Cria as tabelas que ainda não existem, a partir de schema.sql.

    Não há migração: um banco de desenvolvimento criado com o esquema antigo
    precisa ser apagado (ele é recriado vazio; ver README)."""
    with conectar() as conn:
        antigas = [n for (n,) in conn.execute(
            f"SELECT name FROM sqlite_master WHERE type = 'table' AND name IN "
            f"({', '.join('?' for _ in _TABELAS_ANTIGAS)})", _TABELAS_ANTIGAS)]
        if antigas:
            raise RuntimeError(
                f"O banco {caminho_banco()} usa o esquema antigo (tabelas {', '.join(antigas)}). "
                "Apague o arquivo para recriá-lo com o esquema atual.")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
