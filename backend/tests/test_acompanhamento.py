"""UC31 — Acompanhar Pedido.

Regras cobertas: RF-19 a RF-23, RN-02, RN-09, RNF-04, RNF-13 e RNF-15.
"""
import hashlib
import hmac
import json

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import produtos, unidade_id


def _criar_pedido(client, headers, unidade="BurguerJá Gávea"):
    uid = unidade_id(client, unidade)
    produto_id = next(iter(produtos(client, unidade).values()))
    r = client.post("/api/carrinho/itens", headers=headers, json={
        "unidade_id": uid, "produto_id": produto_id, "quantidade": 1,
    })
    assert r.status_code == 201, r.text
    previa = client.post("/api/pedidos/previa", headers=headers, json={
        "tipo_atendimento": "RETIRADA", "endereco_id": None,
    })
    assert previa.status_code == 200, previa.text
    pedido = client.post("/api/pedidos", headers=headers, json={
        "tipo_atendimento": "RETIRADA", "endereco_id": None,
        "total_centavos": previa.json()["total_centavos"],
    })
    assert pedido.status_code == 201, pedido.text
    return pedido.json()


def _webhook(client, pedido_id, payload, segredo="segredo-de-teste"):
    corpo = json.dumps(payload, separators=(",", ":")).encode()
    assinatura = hmac.new(segredo.encode(), corpo, hashlib.sha256).hexdigest()
    return client.post(
        f"/api/webhooks/sgl/pedidos/{pedido_id}/status",
        content=corpo,
        headers={"Content-Type": "application/json", "X-SGL-Signature": f"sha256={assinatura}"},
    )


def test_uc31_lista_sem_pedidos_e_exige_login(client):
    assert client.get("/api/pedidos").status_code == 401


def test_uc31_a1_cliente_sem_pedidos_recebe_lista_vazia(client, ana):
    assert client.get("/api/pedidos", headers=ana).json() == []


def test_rf19_detalhe_e_lista_so_mostram_pedidos_do_cliente(client, ana, novo_cliente, sgl):
    pedido = _criar_pedido(client, ana)
    assert client.get("/api/pedidos", headers=ana).json()[0]["id"] == pedido["id"]
    detalhe = client.get(f"/api/pedidos/{pedido['id']}", headers=ana)
    assert detalhe.status_code == 200
    assert detalhe.json()["unidade"]["nome"] == "BurguerJá Gávea"
    outro = novo_cliente(email="bia@exemplo.com", nome="Bia")
    assert client.get(f"/api/pedidos/{pedido['id']}", headers=outro).status_code == 404


def test_uc31_passo_4_a_6_exibe_valores_congelados_timeline_e_entrega(client, ana, sgl, banco):
    pedido = _criar_pedido(client, ana)
    resposta = client.get(f"/api/pedidos/{pedido['id']}", headers=ana)
    dados = resposta.json()
    assert dados["itens"][0]["valor_final_centavos"] > 0
    assert dados["subtotal_centavos"] == dados["total_centavos"]
    assert dados["notificacoes"][0]["status"] == "RECEBIDO"
    assert dados["atualizado_em"] == dados["notificacoes"][-1]["criado_em"]


def test_rnf15_webhook_sem_assinatura_nao_grava_notificacao(client, ana, sgl, banco, monkeypatch):
    monkeypatch.setenv("BURGUERJA_SGL_WEBHOOK_SECRET", "segredo-de-teste")
    pedido = _criar_pedido(client, ana)
    resposta = client.post(
        f"/api/webhooks/sgl/pedidos/{pedido['id']}/status",
        json={"status": "EM_PREPARO", "titulo": "Em preparo", "mensagem": "A loja começou o preparo."},
    )
    assert resposta.status_code == 401
    assert banco.execute("SELECT COUNT(*) FROM notificacao WHERE pedido_id = ?", (pedido["id"],)).fetchone()[0] == 1


def test_rf20_rf22_webhook_assinado_atualiza_status_e_timeline(client, ana, sgl, banco, monkeypatch):
    segredo = "segredo-de-teste"
    monkeypatch.setenv("BURGUERJA_SGL_WEBHOOK_SECRET", segredo)
    pedido = _criar_pedido(client, ana)
    resposta = _webhook(client, pedido["id"], {
        "status": "EM_PREPARO",
        "titulo": "Pedido em preparo",
        "mensagem": "A loja começou a preparar seu pedido.",
        "data_hora": "2026-11-18T15:10:00+00:00",
    }, segredo)
    assert resposta.status_code == 201, resposta.text
    assert banco.execute("SELECT status FROM pedido WHERE id = ?", (pedido["id"],)).fetchone()[0] == "EM_PREPARO"
    notificacoes = client.get(f"/api/pedidos/{pedido['id']}", headers=ana).json()["notificacoes"]
    assert [n["status"] for n in notificacoes] == ["RECEBIDO", "EM_PREPARO"]


def test_uc31_websocket_entrega_atualizacao_sem_recarregar(client, ana, sgl, monkeypatch):
    segredo = "segredo-de-teste"
    monkeypatch.setenv("BURGUERJA_SGL_WEBHOOK_SECRET", segredo)
    pedido = _criar_pedido(client, ana)
    token = ana["Authorization"].split(" ", 1)[1]
    with client.websocket_connect(f"/api/ws/pedidos/{pedido['id']}?token={token}") as websocket:
        inicial = websocket.receive_json()
        assert inicial["tipo"] == "conectado"
        resposta = _webhook(client, pedido["id"], {
            "status": "PRONTO",
            "titulo": "Pedido pronto",
            "mensagem": "Seu pedido está pronto para retirada.",
        }, segredo)
        assert resposta.status_code == 201
        evento = websocket.receive_json()
        assert evento["tipo"] == "status_atualizado"
        assert evento["notificacao"]["status"] == "PRONTO"


def test_rnf13_websocket_de_outro_cliente_e_recusado(client, ana, novo_cliente, sgl):
    pedido = _criar_pedido(client, ana)
    outro = novo_cliente(email="bia@exemplo.com", nome="Bia")
    token = outro["Authorization"].split(" ", 1)[1]
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/api/ws/pedidos/{pedido['id']}?token={token}"):
            pass
