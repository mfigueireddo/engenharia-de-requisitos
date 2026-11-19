"""UC29 — Gerenciar Itens do Carrinho (e UC27/esvaziar como infra mínima).

Regras testadas: RF-02, RF-08, RF-09, RF-11, RF-12, RF-13, RN-01, RN-02, RN-03,
RNF-13, RNF-14 e as exceções E1, E2, E3 do UC29.
"""

import sqlite3

import pytest

from conftest import produtos, unidade_id


def _add(client, headers, produto_id, quantidade=1, observacao=None, unidade="BurguerJá Gávea", **extra):
    corpo = {"unidade_id": unidade_id(client, unidade), "produto_id": produto_id, "quantidade": quantidade, **extra}
    if observacao is not None:
        corpo["observacao"] = observacao
    return client.post("/api/carrinho/itens", json=corpo, headers=headers)


@pytest.fixture
def ids(client, sgl):
    return produtos(client)


def test_rn01_carrinho_exige_login(client, ids):
    assert client.get("/api/carrinho").status_code == 401
    assert _add(client, {}, ids["Burguer Clássico"]).status_code == 401


def test_uc29_e1_carrinho_vazio(client, ana):
    r = client.get("/api/carrinho", headers=ana)
    assert r.status_code == 200
    assert r.json()["itens"] == [] and r.json()["subtotal_centavos"] == 0


def test_uc27_rf02_adicionar_item_calcula_valor_final(client, ana, ids):
    r = _add(client, ana, ids["Batata frita média"], quantidade=3, observacao="sem sal")
    assert r.status_code == 201
    item = r.json()["itens"][0]
    assert item["valor_final_centavos"] == 3 * (1190 - 200)
    assert item["observacao"] == "sem sal"
    assert r.json()["subtotal_centavos"] == 2970
    assert r.json()["unidade"]["nome"] == "BurguerJá Gávea"


def test_rnf14_preco_enviado_pelo_navegador_e_ignorado(client, ana, ids):
    r = _add(client, ana, ids["Burguer Clássico"], preco_centavos=1, valor_final_centavos=1)
    assert r.json()["itens"][0]["valor_final_centavos"] == 2490


def test_rf12_nao_adiciona_quantidade_menor_que_1(client, ana, ids):
    assert _add(client, ana, ids["Burguer Clássico"], quantidade=0).status_code == 422


def test_uc29_passo3_rf11_combo_mostra_componentes(client, ana, ids):
    item = _add(client, ana, ids["Combo Clássico"], quantidade=2).json()["itens"][0]
    assert item["valor_final_centavos"] == 2 * 4170
    assert len(item["componentes"]) == 3


def test_uc29_passo4_alterar_quantidade_recalcula(client, ana, ids):
    item = _add(client, ana, ids["Burguer Clássico"]).json()["itens"][0]
    r = client.patch(f"/api/carrinho/itens/{item['id']}", json={"quantidade": 4}, headers=ana)
    assert r.status_code == 200
    assert r.json()["itens"][0]["valor_final_centavos"] == 4 * 2490
    assert r.json()["subtotal_centavos"] == 4 * 2490


def test_rf12_uc29_a1_quantidade_zero_remove_o_item(client, ana, ids):
    item = _add(client, ana, ids["Burguer Clássico"]).json()["itens"][0]
    r = client.patch(f"/api/carrinho/itens/{item['id']}", json={"quantidade": 0}, headers=ana)
    assert r.json()["itens"] == []


def test_rf12_quantidade_negativa_recusada(client, ana, ids):
    item = _add(client, ana, ids["Burguer Clássico"]).json()["itens"][0]
    assert client.patch(f"/api/carrinho/itens/{item['id']}", json={"quantidade": -1}, headers=ana).status_code == 422
    assert client.patch(f"/api/carrinho/itens/{item['id']}", json={}, headers=ana).status_code == 422


def test_uc29_a1_remover_item(client, ana, ids):
    a = _add(client, ana, ids["Burguer Clássico"]).json()["itens"][0]
    _add(client, ana, ids["Refrigerante lata"])
    r = client.delete(f"/api/carrinho/itens/{a['id']}", headers=ana)
    assert [i["nome"] for i in r.json()["itens"]] == ["Refrigerante lata"]
    assert r.json()["subtotal_centavos"] == 690


def test_uc29_a2_editar_observacao_nao_altera_valor(client, ana, ids):
    item = _add(client, ana, ids["Burguer Clássico"], quantidade=2).json()["itens"][0]
    r = client.patch(f"/api/carrinho/itens/{item['id']}", json={"observacao": "sem cebola"}, headers=ana)
    novo = r.json()["itens"][0]
    assert novo["observacao"] == "sem cebola"
    assert novo["valor_final_centavos"] == item["valor_final_centavos"]
    assert novo["quantidade"] == 2
    r = client.patch(f"/api/carrinho/itens/{item['id']}", json={"observacao": None}, headers=ana)
    assert r.json()["itens"][0]["observacao"] is None


def test_rf13_carrinho_usa_preco_e_desconto_vigentes(client, ana, ids, sgl):
    _add(client, ana, ids["Burguer Clássico"], quantidade=2)
    sgl.item("UN-GAVEA", "LAN-01")["preco_centavos"] = 2690
    sgl.item("UN-GAVEA", "LAN-01")["desconto_centavos"] = 300
    item = client.get("/api/carrinho", headers=ana).json()["itens"][0]
    assert item["preco_unitario_centavos"] == 2690
    assert item["valor_final_centavos"] == 2 * (2690 - 300)


def test_rf13_rf11_combo_no_carrinho_acompanha_preco_dos_componentes(client, ana, ids, sgl):
    _add(client, ana, ids["Combo Clássico"])
    sgl.item("UN-GAVEA", "BEB-01")["desconto_centavos"] = 100
    assert client.get("/api/carrinho", headers=ana).json()["subtotal_centavos"] == 4170 - 100


def test_uc29_e2_item_fora_do_cardapio_sai_do_carrinho_com_aviso(client, ana, ids, sgl):
    _add(client, ana, ids["Burguer Clássico"])
    _add(client, ana, ids["Batata frita média"])
    sgl.remover("UN-GAVEA", "ACO-01")
    r = client.get("/api/carrinho", headers=ana).json()
    assert [i["nome"] for i in r["itens"]] == ["Burguer Clássico"]
    assert any("Batata frita média" in a for a in r["avisos"])
    assert client.get("/api/carrinho", headers=ana).json()["avisos"] == []  # avisa uma vez


def test_uc29_e3_sgl_fora_do_ar_usa_ultimo_cardapio(client, ana, ids, sgl, relogio):
    antes = _add(client, ana, ids["Burguer Clássico"]).json()
    relogio.avancar(hours=2)
    sgl.fora_do_ar = True
    r = client.get("/api/carrinho", headers=ana).json()
    assert r["sgl_indisponivel"] is True
    assert r["subtotal_centavos"] == 2490
    assert r["cardapio_atualizado_em"] == antes["cardapio_atualizado_em"]


def test_adicionar_produto_fora_do_cardapio(client, ana, ids, sgl):
    sgl.remover("UN-GAVEA", "LAN-01")
    assert _add(client, ana, ids["Burguer Clássico"]).status_code == 409
    assert _add(client, ana, 999999).status_code == 404


def test_rn03_rf08_carrinho_de_uma_unidade_so(client, ana, ids):
    botafogo = produtos(client, "BurguerJá Botafogo")
    _add(client, ana, ids["Burguer Clássico"])
    r = _add(client, ana, botafogo["Duplo Cheddar"], unidade="BurguerJá Botafogo")
    assert r.status_code == 409
    # Esvaziar libera a outra unidade.
    assert client.delete("/api/carrinho", headers=ana).json()["itens"] == []
    r = _add(client, ana, botafogo["Duplo Cheddar"], unidade="BurguerJá Botafogo")
    assert r.status_code == 201 and r.json()["unidade"]["nome"] == "BurguerJá Botafogo"


def test_rn03_carrinho_sem_itens_pode_trocar_de_unidade(client, ana, ids):
    item = _add(client, ana, ids["Burguer Clássico"]).json()["itens"][0]
    client.delete(f"/api/carrinho/itens/{item['id']}", headers=ana)
    botafogo = produtos(client, "BurguerJá Botafogo")
    assert _add(client, ana, botafogo["Duplo Cheddar"], unidade="BurguerJá Botafogo").status_code == 201


def test_rn02_rnf13_cliente_nao_mexe_no_carrinho_de_outro(client, ana, novo_cliente, ids):
    bia = novo_cliente(email="bia@exemplo.com", nome="Bia")
    item = _add(client, ana, ids["Burguer Clássico"]).json()["itens"][0]
    assert client.patch(f"/api/carrinho/itens/{item['id']}", json={"quantidade": 9}, headers=bia).status_code == 404
    assert client.delete(f"/api/carrinho/itens/{item['id']}", headers=bia).status_code == 404
    assert client.get("/api/carrinho", headers=bia).json()["itens"] == []
    assert client.get("/api/carrinho", headers=ana).json()["itens"][0]["quantidade"] == 1


def test_rf08_banco_permite_um_carrinho_por_cliente(client, ana, ids, banco):
    _add(client, ana, ids["Burguer Clássico"])
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("INSERT INTO carrinho (cliente_id, unidade_id) SELECT cliente_id, unidade_id FROM carrinho")


def test_rf09_item_no_carrinho_ou_no_pedido_nunca_nos_dois(client, ana, ids, banco):
    _add(client, ana, ids["Burguer Clássico"])
    car = banco.execute("SELECT * FROM carrinho").fetchone()
    pedido = banco.execute(
        """INSERT INTO pedido (cliente_id, unidade_id, data_hora, status, modalidade)
           VALUES (?, ?, '2026-11-19T12:00:00+00:00', 'RECEBIDO', 'RETIRADA')""",
        (car["cliente_id"], car["unidade_id"])).lastrowid
    produto = ids["Burguer Clássico"]

    def inserir(carrinho_id, pedido_id, quantidade=1, preco=1, desconto=0, valor=1):
        banco.execute("""INSERT INTO item_pedido (carrinho_id, pedido_id, item_cardapio_id, quantidade,
                             preco_unitario_centavos, desconto_unitario_centavos, valor_final_centavos)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (carrinho_id, pedido_id, produto, quantidade, preco, desconto, valor))

    inserir(car["id"], None)  # válido
    with pytest.raises(sqlite3.IntegrityError):  # nos dois
        inserir(car["id"], pedido)
    with pytest.raises(sqlite3.IntegrityError):  # em nenhum
        inserir(None, None)
    with pytest.raises(sqlite3.IntegrityError):  # RF-12 no banco
        inserir(car["id"], None, quantidade=0, valor=0)


def test_rf02_rf10_valores_do_item_conferidos_no_banco(client, ana, ids, banco):
    """Projeto relacional: 0 ≤ desconto ≤ preço e valor final = qtd × (preço − desconto)."""
    _add(client, ana, ids["Burguer Clássico"], quantidade=2)
    with pytest.raises(sqlite3.IntegrityError):  # RF-02
        banco.execute("UPDATE item_pedido SET valor_final_centavos = valor_final_centavos + 1")
    with pytest.raises(sqlite3.IntegrityError):  # RF-10
        banco.execute("UPDATE item_pedido SET desconto_unitario_centavos = preco_unitario_centavos + 1")


def test_rf13_carrinho_grava_valores_recalculados(client, ana, ids, sgl, banco):
    """No carrinho, preço/desconto/valor da linha acompanham o cardápio vigente."""
    _add(client, ana, ids["Burguer Clássico"], quantidade=2)
    sgl.item("UN-GAVEA", "LAN-01")["preco_centavos"] = 2690
    client.get("/api/carrinho", headers=ana)
    linha = banco.execute("SELECT preco_unitario_centavos, valor_final_centavos FROM item_pedido").fetchone()
    assert tuple(linha) == (2690, 5380)
