"""Infraestrutura: rota de saúde e isolamento do banco nos testes (sem UC na ERS)."""

from app import db


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_banco_dos_testes_e_temporario(client, banco_temporario):
    assert db.caminho_banco() == banco_temporario
    assert banco_temporario.exists()
    assert banco_temporario != db.CAMINHO_PADRAO
