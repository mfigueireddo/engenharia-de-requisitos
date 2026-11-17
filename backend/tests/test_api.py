# ESBOÇO-PROVISÓRIO: teste de recados; substituir por testes reais (AGENTS.md, seção 7).


def test_recados(client):
    assert client.post("/api/recados", json={"texto": "oi"}).status_code == 201
    assert client.get("/api/recados").json()[0]["texto"] == "oi"
    assert client.post("/api/recados", json={"texto": ""}).status_code == 422


def test_recados_cada_teste_comeca_com_banco_vazio(client):
    assert client.get("/api/recados").json() == []
