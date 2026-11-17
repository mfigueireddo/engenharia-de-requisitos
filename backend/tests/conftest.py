"""Fixtures do pytest.

Cada teste que usa `client` ganha um banco SQLite novo e vazio num diretório
temporário, apontado pela variável BURGUERJA_DB (o banco real não é tocado).
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    caminho = tmp_path / "teste.db"
    monkeypatch.setenv("BURGUERJA_DB", str(caminho))
    return caminho


@pytest.fixture
def client(banco_temporario):
    from app.main import app

    with TestClient(app) as c:  # o lifespan cria as tabelas no banco temporário
        yield c
