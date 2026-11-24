"""Script de dados de demonstração (infra mínima — sem UC na ERS)."""

from scripts import dados_demo


def test_dados_demo_permite_login_e_lista_enderecos(client):
    dados_demo.criar()
    dados_demo.criar()  # idempotente
    r = client.post("/api/auth/login", json={"email": dados_demo.EMAIL, "senha": dados_demo.SENHA})
    assert r.status_code == 200
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    enderecos = client.get("/api/enderecos", headers=headers).json()
    assert len(enderecos) == len(dados_demo.ENDERECOS)
    cupons = client.get("/api/cupons", headers=headers).json()
    assert len(cupons) == len(dados_demo.CUPONS)
