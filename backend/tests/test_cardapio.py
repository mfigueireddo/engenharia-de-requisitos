"""Unidades e cardápio (infra mínima — sem UC na ERS, decisões Q1 e Q2).

Regras testadas: RF-10, RF-11, RNF-03, RNF-19 (falha simulada do SGL), RNF-22, RN-01.
"""

import sqlite3

import pytest

from conftest import unidade_id


def _cardapio(client, nome="BurguerJá Gávea"):
    return client.get(f"/api/unidades/{unidade_id(client, nome)}/cardapio").json()


def test_rn01_visitante_ve_unidades_e_cardapio_sem_login(client, sgl):
    unidades = client.get("/api/unidades").json()
    assert {u["nome"] for u in unidades} == {"BurguerJá Gávea", "BurguerJá Botafogo"}
    assert _cardapio(client)["produtos"]


def test_unidade_inexistente(client):
    assert client.get("/api/unidades/999/cardapio").status_code == 404


def test_rf11_combo_vale_a_soma_dos_componentes_com_desconto_por_componente(client, sgl):
    combo = next(p for p in _cardapio(client)["produtos"] if p["tipo"] == "COMBO")
    # Burguer Clássico 24,90 + Batata 11,90 (−2,00) + Refrigerante 6,90
    assert combo["preco_centavos"] == 2490 + 1190 + 690
    assert combo["desconto_centavos"] == 200
    assert combo["preco_final_centavos"] == 4170
    assert {c["nome"] for c in combo["componentes"]} == {"Burguer Clássico", "Batata frita média", "Refrigerante lata"}


def test_rnf03_rnf19_sgl_fora_do_ar_usa_ultimo_cardapio_e_horario(client, sgl, relogio):
    primeiro = _cardapio(client)
    relogio.avancar(hours=1)
    sgl.fora_do_ar = True
    depois = _cardapio(client)
    assert depois["sgl_indisponivel"] is True
    assert depois["produtos"] == primeiro["produtos"]
    assert depois["cardapio_atualizado_em"] == primeiro["cardapio_atualizado_em"]


def test_rf10_cardapio_do_sgl_com_desconto_maior_que_o_preco_e_recusado(client, sgl):
    antes = _cardapio(client)
    sgl.item("UN-GAVEA", "BEB-01")["desconto_centavos"] = 9999
    depois = _cardapio(client)
    assert depois["sgl_indisponivel"] is True
    assert depois["produtos"] == antes["produtos"]


def test_rf10_banco_recusa_desconto_fora_do_intervalo(client, sgl, banco):
    _cardapio(client)
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("UPDATE item_simples SET desconto_item_centavos = preco_centavos + 1")
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("UPDATE item_simples SET desconto_item_centavos = -1")


def test_rnf22_item_que_sai_do_sgl_sai_do_cardapio_e_nao_e_apagado(client, sgl, banco):
    _cardapio(client)
    sgl.remover("UN-GAVEA", "ACO-01")
    nomes = {p["nome"] for p in _cardapio(client)["produtos"]}
    assert "Batata frita média" not in nomes
    assert "Combo Clássico" not in nomes  # combo sem um componente sai junto
    item = banco.execute("SELECT id FROM item_cardapio WHERE id_sgl = 'ACO-01'").fetchone()
    assert item is not None  # continua em item_cardapio
    assert banco.execute("SELECT COUNT(*) FROM cardapio_item WHERE item_cardapio_id = ?",
                         (item[0],)).fetchone()[0] == 0  # mas não está em nenhum cardápio


def test_item_que_volta_ao_sgl_volta_ao_cardapio(client, sgl):
    _cardapio(client)
    item = sgl.item("UN-GAVEA", "ACO-01")
    sgl.remover("UN-GAVEA", "ACO-01")
    _cardapio(client)
    sgl.cardapios["UN-GAVEA"]["itens"].append(item)
    assert "Combo Clássico" in {p["nome"] for p in _cardapio(client)["produtos"]}


def test_projeto_relacional_heranca_do_item_do_cardapio(client, sgl, banco):
    """Cada ITEM_CARDAPIO está em exatamente uma subtabela; combo tem 2 ou mais itens."""
    _cardapio(client)
    combo = banco.execute("SELECT item_cardapio_id FROM combo").fetchone()[0]
    simples = banco.execute("SELECT item_cardapio_id FROM item_simples").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("INSERT INTO item_simples (item_cardapio_id, preco_centavos) VALUES (?, 100)", (combo,))
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("INSERT INTO combo (item_cardapio_id) VALUES (?)", (simples,))
    novo = banco.execute("INSERT INTO item_cardapio (id_sgl, nome, categoria) VALUES ('X', 'X', 'X')").lastrowid
    banco.execute("INSERT INTO combo (item_cardapio_id) VALUES (?)", (novo,))
    banco.execute("INSERT INTO item_no_combo (combo_id, item_simples_id, quantidade) VALUES (?, ?, 1)",
                  (novo, simples))
    with pytest.raises(sqlite3.IntegrityError):  # só 1 item no combo
        banco.execute("INSERT INTO cardapio_item (cardapio_id, item_cardapio_id) VALUES (1, ?)", (novo,))


def test_mesmo_item_e_compartilhado_entre_unidades(client, sgl, banco):
    """ITEM_CARDAPIO é da rede; CARDAPIO_ITEM liga cada unidade aos itens dela."""
    sgl.cardapios["UN-BOTAFOGO"]["itens"].append(sgl.item("UN-GAVEA", "LAN-01"))
    gavea, botafogo = _cardapio(client), _cardapio(client, "BurguerJá Botafogo")
    id_gavea = next(p["id"] for p in gavea["produtos"] if p["nome"] == "Burguer Clássico")
    id_botafogo = next(p["id"] for p in botafogo["produtos"] if p["nome"] == "Burguer Clássico")
    assert id_gavea == id_botafogo
    assert banco.execute("SELECT COUNT(*) FROM item_cardapio WHERE id_sgl = 'LAN-01'").fetchone()[0] == 1
