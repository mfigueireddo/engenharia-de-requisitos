"""UC28 — Finalizar Pedido.

Regras testadas: RF-01, RF-03 a RF-07, RF-09, RF-21, RF-22, RN-01, RN-04, RN-05,
RN-06, RNF-13, RNF-14, RNF-19, RNF-22, RNF-23, RNF-26 e os fluxos A1, E1, E2.
Fórmulas de taxa e tempo: decisão do humano (ver app/servicos/checkout.py).
"""

import sqlite3

import pytest

from app.integracoes.base import IntegracaoIndisponivel
from app.servicos import checkout
from conftest import produtos, unidade_id

CEP_PUC = "22451-900"            # ~0,2 km da unidade Gávea; ~5,5 km da Botafogo
CEP_JARDIM_BOTANICO = "22470-050"
CEP_DESCONHECIDO = "01000-000"


@pytest.fixture
def gavea(client, sgl):
    return produtos(client)


def _add(client, headers, produto_id, quantidade=1, unidade="BurguerJá Gávea"):
    corpo = {"unidade_id": unidade_id(client, unidade), "produto_id": produto_id, "quantidade": quantidade}
    r = client.post("/api/carrinho/itens", json=corpo, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _endereco(client, banco, headers, cep=CEP_PUC, rua="Rua Marquês de São Vicente"):
    """Os endereços são do UC33 (outro integrante); aqui entram direto no banco."""
    cliente_id = client.get("/api/clientes/me", headers=headers).json()["id"]
    cur = banco.execute(
        """INSERT INTO endereco_cliente (cliente_id, logradouro, numero, complemento, bairro, cidade, estado, cep)
           VALUES (?, ?, '225', NULL, 'Gávea', 'Rio de Janeiro', 'RJ', ?)""",
        (cliente_id, rua, cep))
    banco.commit()
    return cur.lastrowid


def _previa(client, headers, tipo="RETIRADA", endereco_id=None):
    return client.post("/api/pedidos/previa", json={"tipo_atendimento": tipo, "endereco_id": endereco_id},
                       headers=headers)


def _confirmar(client, headers, total, tipo="RETIRADA", endereco_id=None):
    return client.post("/api/pedidos", json={"tipo_atendimento": tipo, "endereco_id": endereco_id,
                                             "total_centavos": total}, headers=headers)


# --- Fórmulas (decisão do humano; RN-05, RNF-06, RNF-23) -----------------------

def test_rn05_taxa_km_vezes_fator_arredondada_ao_centavo():
    assert checkout.taxa_entrega(2300, 150) == 345   # 2,3 km × R$ 1,50
    assert checkout.taxa_entrega(1234, 150) == 185   # 185,1 → 185
    assert checkout.taxa_entrega(1237, 150) == 186   # 185,55 → 186
    assert checkout.taxa_entrega(0, 150) == 0


def test_rnf06_tempo_estimado_preparo_mais_minutos_por_km_iniciado():
    assert checkout.tempo_estimado_min(0) == 30
    assert checkout.tempo_estimado_min(1000) == 33
    assert checkout.tempo_estimado_min(1001) == 36
    assert checkout.tempo_estimado_min(2300) == 39


def test_rf06_distancia_em_linha_reta():
    # Gávea → Botafogo (unidades do SGL simulado): cerca de 6 km.
    assert 5500 < checkout.distancia_m(-22.9789, -43.2311, -22.9475, -43.1823) < 6500


# --- Fluxo pela API --------------------------------------------------------------

def test_rn01_checkout_exige_login(client):
    assert _previa(client, {}).status_code == 401
    assert _confirmar(client, {}, 0).status_code == 401


def test_e1_rf07_carrinho_vazio_nao_inicia_checkout(client, ana):
    r = _previa(client, ana)
    assert r.status_code == 409 and r.json()["detail"]["motivo"] == "carrinho_vazio"
    assert _confirmar(client, ana, 0).status_code == 409


def test_passo3_rn04_drive_thru_so_na_unidade_que_tem(client, ana, gavea):
    _add(client, ana, gavea["Burguer Clássico"])
    r = _previa(client, ana)
    assert r.json()["tipos_atendimento_disponiveis"] == ["ENTREGA", "RETIRADA"]
    assert _previa(client, ana, "DRIVE_THRU").status_code == 422

    client.delete("/api/carrinho", headers=ana)
    _add(client, ana, produtos(client, "BurguerJá Botafogo")["Duplo Cheddar"], unidade="BurguerJá Botafogo")
    r = _previa(client, ana, "DRIVE_THRU")
    assert r.status_code == 200 and "DRIVE_THRU" in r.json()["tipos_atendimento_disponiveis"]


def test_a1_rn05_retirada_sem_endereco_e_sem_taxa(client, ana, gavea):
    _add(client, ana, gavea["Batata frita média"], quantidade=2)
    r = _previa(client, ana, "RETIRADA").json()
    assert r["entrega"] is None
    assert r["taxa_entrega_centavos"] == 0
    assert r["subtotal_centavos"] == r["total_centavos"] == 2 * (1190 - 200)


def test_passos_5_a_8_entrega_calcula_distancia_taxa_tempo_e_total(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    end = _endereco(client, banco, ana, CEP_JARDIM_BOTANICO)
    r = _previa(client, ana, "ENTREGA", end)
    assert r.status_code == 200, r.text
    r = r.json()
    dist = r["entrega"]["distancia_m"]
    assert 1000 < dist < 2500
    assert r["taxa_entrega_centavos"] == checkout.taxa_entrega(dist, 150)  # fator da unidade Gávea
    assert r["entrega"]["tempo_estimado_min"] == checkout.tempo_estimado_min(dist)
    assert r["total_centavos"] == 2490 + r["taxa_entrega_centavos"]  # passo 8 (sem cupom)
    assert r["desconto_cupom_centavos"] == 0


def test_entrega_exige_endereco(client, ana, gavea):
    _add(client, ana, gavea["Burguer Clássico"])
    assert _previa(client, ana, "ENTREGA").status_code == 422


def test_e2_rf06_endereco_fora_do_raio_nao_pode_ser_usado(client, ana, banco):
    _add(client, ana, produtos(client, "BurguerJá Botafogo")["Duplo Cheddar"], unidade="BurguerJá Botafogo")
    end = _endereco(client, banco, ana, CEP_PUC)
    r = _previa(client, ana, "ENTREGA", end)
    assert r.status_code == 422 and r.json()["detail"]["motivo"] == "fora_do_raio"
    assert _confirmar(client, ana, 99999, "ENTREGA", end).status_code == 422
    # O cliente pode trocar o tipo de atendimento (volta ao passo 3).
    assert _previa(client, ana, "RETIRADA").status_code == 200


def test_cep_desconhecido_nao_serve_para_entrega(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    end = _endereco(client, banco, ana, CEP_DESCONHECIDO)
    r = _previa(client, ana, "ENTREGA", end)
    assert r.status_code == 422 and r.json()["detail"]["motivo"] == "cep_desconhecido"


def test_rnf19_geocodificacao_fora_do_ar(client, ana, gavea, banco, monkeypatch):
    def fora(_cep):
        raise IntegracaoIndisponivel("Geocodificação", "simulada fora do ar")
    monkeypatch.setattr("app.servicos.checkout.buscar_coordenadas", fora)
    _add(client, ana, gavea["Burguer Clássico"])
    end = _endereco(client, banco, ana)
    assert _previa(client, ana, "ENTREGA", end).status_code == 503
    assert _previa(client, ana, "RETIRADA").status_code == 200


def test_rnf13_endereco_de_outro_cliente(client, ana, novo_cliente, gavea, banco):
    bia = novo_cliente(email="bia@exemplo.com", nome="Bia")
    end_bia = _endereco(client, banco, bia)
    _add(client, ana, gavea["Burguer Clássico"])
    assert _previa(client, ana, "ENTREGA", end_bia).status_code == 404
    assert client.get("/api/enderecos", headers=ana).json() == []
    assert [e["id"] for e in client.get("/api/enderecos", headers=bia).json()] == [end_bia]


def test_passos_9_a_11_confirmar_cria_pedido_recebido(client, ana, gavea, banco):
    carrinho = _add(client, ana, gavea["Combo Clássico"], quantidade=2)
    end = _endereco(client, banco, ana)
    total = _previa(client, ana, "ENTREGA", end).json()["total_centavos"]
    r = _confirmar(client, ana, total, "ENTREGA", end)
    assert r.status_code == 201, r.text
    pedido = r.json()
    assert pedido["status"] == "RECEBIDO"                                   # passo 10, RF-21
    assert pedido["unidade_id"] == carrinho["unidade"]["id"]                # RF-01
    assert pedido["total_centavos"] == total
    assert pedido["itens"][0]["valor_final_centavos"] == 2 * 4170           # RF-02
    assert pedido["entrega"]["endereco"]["cep"] == CEP_PUC                  # RF-04, RF-05
    assert [n["status"] for n in pedido["notificacoes"]] == ["RECEBIDO"]    # passo 11, RF-22
    assert client.get("/api/carrinho", headers=ana).json()["itens"] == []   # itens saíram do carrinho


def test_rf09_itens_passam_do_carrinho_para_o_pedido(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    pedido = _confirmar(client, ana, 2490).json()
    linhas = banco.execute("SELECT carrinho_id, pedido_id FROM item_pedido").fetchall()
    assert [tuple(l) for l in linhas] == [(None, pedido["id"])]


def test_rf03_rn06_preco_congelado_no_pedido(client, ana, gavea, sgl, banco):
    _add(client, ana, gavea["Burguer Clássico"], quantidade=2)
    _confirmar(client, ana, 2 * 2490)
    sgl.item("UN-GAVEA", "LAN-01")["preco_centavos"] = 9990
    produtos(client)  # o cardápio novo é carregado
    item = banco.execute("SELECT * FROM item_pedido WHERE pedido_id IS NOT NULL").fetchone()
    assert (item["preco_unitario_centavos"], item["desconto_unitario_centavos"], item["valor_final_centavos"]) \
        == (2490, 0, 4980)
    with pytest.raises(sqlite3.IntegrityError):  # trigger item_pedido_congelado
        banco.execute("UPDATE item_pedido SET quantidade = 3 WHERE pedido_id IS NOT NULL")


def test_rf05_rf31_pedido_guarda_copia_do_endereco(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    end = _endereco(client, banco, ana)
    total = _previa(client, ana, "ENTREGA", end).json()["total_centavos"]
    pedido_id = _confirmar(client, ana, total, "ENTREGA", end).json()["id"]
    banco.execute("UPDATE endereco_cliente SET logradouro = 'Outra Rua' WHERE id = ?", (end,))
    banco.execute("DELETE FROM endereco_cliente WHERE id = ?", (end,))
    banco.commit()
    assert banco.execute("SELECT logradouro FROM endereco_pedido WHERE pedido_id = ?", (pedido_id,)).fetchone()[0] \
        == "Rua Marquês de São Vicente"


def test_rnf26_total_diferente_do_mostrado_nao_cria_pedido(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    r = _confirmar(client, ana, 1)  # o navegador não define o valor (RNF-14)
    assert r.status_code == 409 and r.json()["detail"]["motivo"] == "valores_mudaram"
    assert banco.execute("SELECT COUNT(*) FROM pedido").fetchone()[0] == 0
    assert len(client.get("/api/carrinho", headers=ana).json()["itens"]) == 1


def test_rf13_rnf26_preco_mudou_entre_a_previa_e_a_confirmacao(client, ana, gavea, sgl):
    _add(client, ana, gavea["Burguer Clássico"])
    total = _previa(client, ana).json()["total_centavos"]
    sgl.item("UN-GAVEA", "LAN-01")["preco_centavos"] = 2690
    assert _confirmar(client, ana, total).status_code == 409
    assert _confirmar(client, ana, 2690).status_code == 201


def test_confirmar_duas_vezes_nao_duplica_o_pedido(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    assert _confirmar(client, ana, 2490).status_code == 201
    assert _confirmar(client, ana, 2490).status_code == 409  # carrinho já está vazio
    assert banco.execute("SELECT COUNT(*) FROM pedido").fetchone()[0] == 1


# --- Restrições no banco ------------------------------------------------------------

def _inserir_pedido(banco, **campos):
    base = {"cliente_id": 1, "unidade_id": 1, "data_hora": "2026-11-19T12:00:00+00:00",
            "status": "RECEBIDO", "modalidade": "RETIRADA", "taxa_entrega_centavos": 0}
    base.update(campos)
    cols = ", ".join(base)
    return banco.execute(f"INSERT INTO pedido ({cols}) VALUES ({', '.join('?' for _ in base)})",
                         list(base.values())).lastrowid


def test_rf04_rn05_rf21_restricoes_do_pedido_no_banco(client, ana, gavea, banco):
    _inserir_pedido(banco)  # retirada válida
    with pytest.raises(sqlite3.IntegrityError):  # RF-04: retirada com previsão de entrega
        _inserir_pedido(banco, previsao_entrega="2026-11-19T12:40:00+00:00")
    with pytest.raises(sqlite3.IntegrityError):  # RF-04: entrega sem previsão
        _inserir_pedido(banco, modalidade="ENTREGA")
    with pytest.raises(sqlite3.IntegrityError):  # RN-05: retirada com taxa
        _inserir_pedido(banco, taxa_entrega_centavos=500)
    with pytest.raises(sqlite3.IntegrityError):  # RF-21: o nome da ERS é SAIU_PARA_ENTREGA
        _inserir_pedido(banco, status="EM_ROTA")


def test_rf04_endereco_do_pedido_so_em_entrega(client, ana, gavea, banco):
    """Trigger do projeto relacional: ENDERECO_PEDIDO só existe em pedido de ENTREGA."""
    retirada = _inserir_pedido(banco)
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("""INSERT INTO endereco_pedido (pedido_id, logradouro, numero, bairro, cidade, estado, cep)
                         VALUES (?, 'Rua X', '1', 'Gávea', 'Rio de Janeiro', 'RJ', '22451-900')""", (retirada,))


def test_rf22_status_do_pedido_segue_a_ultima_notificacao(client, ana, gavea, banco):
    """Trigger do projeto relacional: PEDIDO.status = status da notificação mais recente."""
    _add(client, ana, gavea["Burguer Clássico"])
    pedido_id = _confirmar(client, ana, 2490).json()["id"]
    banco.execute("""INSERT INTO notificacao (pedido_id, status, data_hora, titulo, mensagem)
                     VALUES (?, 'PAGO', '2026-11-19T12:05:00+00:00', 'Pago', 'Pagamento aprovado')""", (pedido_id,))
    assert banco.execute("SELECT status FROM pedido WHERE id = ?", (pedido_id,)).fetchone()[0] == "PAGO"


def test_rnf22_pedido_e_notificacao_nunca_apagados(client, ana, gavea, banco):
    _add(client, ana, gavea["Burguer Clássico"])
    _confirmar(client, ana, 2490)
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("DELETE FROM notificacao")
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("DELETE FROM pedido")
