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


# ---------------------------------------------------------------------------
# Fixtures das funcionalidades (autenticação, cardápio, carrinho, checkout).
# ---------------------------------------------------------------------------
import copy
import json
import sqlite3
from datetime import datetime, timedelta, timezone

from app.integracoes import sgl as _sgl
from app.integracoes.base import IntegracaoIndisponivel


class SGLFalso:
    """SGL simulado que os testes podem alterar: mudar preço, tirar item, cair."""

    def __init__(self):
        self.cardapios = copy.deepcopy(json.loads(_sgl.ARQUIVO_SIMULADO.read_text(encoding="utf-8")))
        self.fora_do_ar = False

    def obter_cardapio(self, id_sgl_unidade):
        if self.fora_do_ar:
            raise IntegracaoIndisponivel("SGL", "simulado fora do ar")
        return copy.deepcopy(self.cardapios[id_sgl_unidade])

    def item(self, unidade, id_sgl):
        return next(i for i in self.cardapios[unidade]["itens"] if i["id_sgl"] == id_sgl)

    def remover(self, unidade, id_sgl):
        self.cardapios[unidade]["itens"].remove(self.item(unidade, id_sgl))


@pytest.fixture(autouse=True)
def _bcrypt_rapido(monkeypatch):
    monkeypatch.setattr("app.seguranca.RODADAS_BCRYPT", 4)


@pytest.fixture
def sgl(monkeypatch):
    falso = SGLFalso()
    monkeypatch.setattr("app.servicos.cardapio.buscar_cardapio", falso.obter_cardapio)
    return falso


class Relogio:
    """Relógio controlável: `relogio.avancar(minutes=15)`."""

    def __init__(self, monkeypatch):
        self.momento = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
        monkeypatch.setattr("app.relogio.agora", lambda: self.momento)

    def avancar(self, **delta):
        self.momento += timedelta(**delta)


@pytest.fixture
def relogio(monkeypatch):
    return Relogio(monkeypatch)


@pytest.fixture
def novo_cliente(client):
    """Fábrica: cadastra e entra; devolve os cabeçalhos com o token."""

    def _novo(email="ana@exemplo.com", senha="segredo123", nome="Ana"):
        r = client.post("/api/auth/cadastro",
                        json={"nome": nome, "email": email, "senha": senha, "aceite_termos": True})
        assert r.status_code == 201, r.text
        r = client.post("/api/auth/login", json={"email": email, "senha": senha})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['token']}"}

    return _novo


@pytest.fixture
def ana(novo_cliente):
    return novo_cliente()


@pytest.fixture
def banco(banco_temporario):
    """Conexão direta ao banco temporário, para testar restrições do esquema."""
    conn = sqlite3.connect(banco_temporario)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


def unidade_id(client, nome="BurguerJá Gávea"):
    return next(u["id"] for u in client.get("/api/unidades").json() if u["nome"] == nome)


def produtos(client, nome_unidade="BurguerJá Gávea"):
    """{nome do produto: id} do cardápio da unidade (também carrega o cache)."""
    uid = unidade_id(client, nome_unidade)
    return {p["nome"]: p["id"] for p in client.get(f"/api/unidades/{uid}/cardapio").json()["produtos"]}
