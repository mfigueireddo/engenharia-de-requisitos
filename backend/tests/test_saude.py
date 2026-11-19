"""Infraestrutura: rota de saúde e isolamento do banco nos testes (sem UC na ERS)."""

from app import db


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_banco_dos_testes_e_temporario(client, banco_temporario):
    assert db.caminho_banco() == banco_temporario
    assert banco_temporario.exists()
    assert banco_temporario != db.CAMINHO_PADRAO


def test_banco_com_esquema_antigo_e_recusado_com_mensagem_clara(banco_temporario):
    """Sem migração: banco criado antes do projeto relacional precisa ser apagado."""
    import sqlite3

    import pytest

    from app import db

    sqlite3.connect(banco_temporario).execute("CREATE TABLE produto (id INTEGER)").connection.close()
    with pytest.raises(RuntimeError, match="esquema antigo"):
        db.inicializar()
