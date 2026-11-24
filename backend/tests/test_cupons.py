"""UC30 — Aplicar Cupom ao Pedido.

Regras testadas: UC30 (fluxo principal passos 1–6, A1, E1, E2), UC28 (A3),
RF-14, RF-15, RF-16, RF-17, RF-18, RN-01, RN-02, RN-07, RNF-13, RNF-22, RNF-23,
RNF-26.
"""

import sqlite3

import pytest

from app.servicos import cupons
from conftest import produtos, unidade_id

CEP_JARDIM_BOTANICO = "22470-050"


@pytest.fixture
def gavea(client, sgl):
    return produtos(client)


def _add(client, headers, produto_id, quantidade=1, unidade="BurguerJá Gávea"):
    corpo = {"unidade_id": unidade_id(client, unidade), "produto_id": produto_id, "quantidade": quantidade}
    r = client.post("/api/carrinho/itens", json=corpo, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _endereco(client, banco, headers, cep=CEP_JARDIM_BOTANICO):
    cliente_id = client.get("/api/clientes/me", headers=headers).json()["id"]
    cur = banco.execute(
        """INSERT INTO endereco_cliente (cliente_id, logradouro, numero, complemento, bairro, cidade, estado, cep)
           VALUES (?, 'Rua Jardim Botânico', '1008', NULL, 'Jardim Botânico', 'Rio de Janeiro', 'RJ', ?)""",
        (cliente_id, cep),
    )
    banco.commit()
    return cur.lastrowid


def _cupom(
    client,
    banco,
    headers,
    codigo="BEMVINDO10",
    descricao="10% off até R$ 10",
    percentual_centesimos=1000,
    teto_centavos=1000,
    isenta_taxa=0,
    minimo_centavos=0,
    inicio="2026-01-01",
    fim="2026-12-31",
    limite_usos=1,
):
    cliente_id = client.get("/api/clientes/me", headers=headers).json()["id"]
    cur = banco.execute(
        """INSERT INTO cupom_promocional (
               cliente_id, codigo, descricao, percentual_desconto_centesimos,
               valor_maximo_desconto_centavos, isenta_taxa_entrega,
               valor_minimo_pedido_centavos, validade_inicio, validade_fim, limite_usos
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            cliente_id,
            codigo,
            descricao,
            percentual_centesimos,
            teto_centavos,
            isenta_taxa,
            minimo_centavos,
            inicio,
            fim,
            limite_usos,
        ),
    )
    banco.commit()
    return cur.lastrowid


def _previa(client, headers, tipo="RETIRADA", endereco_id=None, codigo_cupom=None):
    return client.post(
        "/api/pedidos/previa",
        json={"tipo_atendimento": tipo, "endereco_id": endereco_id, "codigo_cupom": codigo_cupom},
        headers=headers,
    )


def _confirmar(client, headers, total, tipo="RETIRADA", endereco_id=None, codigo_cupom=None):
    return client.post(
        "/api/pedidos",
        json={
            "tipo_atendimento": tipo,
            "endereco_id": endereco_id,
            "codigo_cupom": codigo_cupom,
            "total_centavos": total,
        },
        headers=headers,
    )


# --- Cálculo inteiro do desconto (RNF-23) ------------------------------------


def test_rnf23_calculo_desconto_percentual_inteiro_e_teto():
    # 10% de R$ 24,90 = R$ 2,49 (249 centavos)
    assert cupons.calcular_desconto_percentual(2490, 1000, None) == 249
    # Com teto de R$ 10,00 (1000 centavos): 10% de R$ 150,00 = R$ 15,00 -> limitado a 1000
    assert cupons.calcular_desconto_percentual(15000, 1000, 1000) == 1000
    # Arredondamento ao centavo mais próximo: 15% de 99 = 14,85 -> 15
    assert cupons.calcular_desconto_percentual(99, 1500, None) == 15
    # Cupom só de frete (0%): desconto nos itens é zero
    assert cupons.calcular_desconto_percentual(5000, 0, None) == 0


# --- Autenticação e isolamento por cliente (RN-01, RN-02, RNF-13, RF-15) -----


def test_rn01_cupons_exige_login(client):
    assert client.get("/api/cupons").status_code == 401
    assert client.post("/api/cupons/aplicar", json={"codigo": "BEMVINDO10"}).status_code == 401


def test_rf15_rnf13_cupom_pertence_a_um_unico_cliente(client, ana, novo_cliente, gavea, banco, relogio):
    bia = novo_cliente(email="bia@exemplo.com", nome="Bia")
    _cupom(client, banco, bia, codigo="SO_DA_BIA")
    _add(client, ana, gavea["Burguer Clássico"])

    # Ana não vê nem consegue aplicar o cupom da Bia (E1: cupom não encontrado)
    assert client.get("/api/cupons", headers=ana).json() == []
    r = client.post("/api/cupons/aplicar", json={"codigo": "SO_DA_BIA"}, headers=ana)
    assert r.status_code == 404 and r.json()["detail"]["motivo"] == "cupom_nao_encontrado"
    assert _previa(client, ana, codigo_cupom="SO_DA_BIA").status_code == 404


# --- Fluxo principal (passos 1–6) e A1 (trocar ou remover cupom) --------------


def test_uc30_fluxo_principal_desconto_percentual_e_confirmacao(client, ana, gavea, banco, relogio):
    _cupom(client, banco, ana, codigo="BEMVINDO10", percentual_centesimos=1000, teto_centavos=1000)
    _add(client, ana, gavea["Burguer Clássico"], quantidade=2)  # subtotal = 4980

    # Endpoint de validação na tela 07
    ap = client.post("/api/cupons/aplicar", json={"codigo": "bemvindo10"}, headers=ana)
    assert ap.status_code == 200, ap.text
    assert ap.json()["desconto_cupom_centavos"] == 498

    # Passo 5: prévia no checkout mostra o desconto e o novo total (4980 - 498 = 4482)
    prev = _previa(client, ana, "RETIRADA", codigo_cupom="BEMVINDO10")
    assert prev.status_code == 200, prev.text
    dados_prev = prev.json()
    assert dados_prev["desconto_cupom_centavos"] == 498
    assert dados_prev["total_centavos"] == 4980 - 498
    assert dados_prev["cupom"]["codigo"] == "BEMVINDO10"

    # RF-17: antes da confirmação do pedido, o uso ainda não foi contado
    assert client.get("/api/cupons", headers=ana).json()[0]["usos_realizados"] == 0

    # Passo 6: confirmar o pedido registra o uso do cupom com o valor descontado
    conf = _confirmar(client, ana, dados_prev["total_centavos"], "RETIRADA", codigo_cupom="BEMVINDO10")
    assert conf.status_code == 201, conf.text
    pedido = conf.json()
    assert pedido["desconto_cupom_centavos"] == 498
    assert pedido["total_centavos"] == 4482
    assert pedido["cupom"]["codigo"] == "BEMVINDO10"

    uso = banco.execute("SELECT * FROM uso_cupom WHERE pedido_id = ?", (pedido["id"],)).fetchone()
    assert uso is not None and uso["valor_descontado_centavos"] == 498
    assert client.get("/api/cupons", headers=ana).json()[0]["usos_realizados"] == 1


def test_uc30_passo4_isenta_taxa_entrega(client, ana, gavea, banco, relogio):
    _cupom(
        client,
        banco,
        ana,
        codigo="FRETEGRATIS",
        percentual_centesimos=0,
        teto_centavos=None,
        isenta_taxa=1,
        minimo_centavos=4000,
        limite_usos=3,
    )
    _add(client, ana, gavea["Burguer Clássico"], quantidade=2)  # subtotal = 4980
    end = _endereco(client, banco, ana)

    sem_cupom = _previa(client, ana, "ENTREGA", end).json()
    assert sem_cupom["taxa_entrega_centavos"] > 0

    com_cupom = _previa(client, ana, "ENTREGA", end, codigo_cupom="FRETEGRATIS").json()
    assert com_cupom["taxa_entrega_centavos"] == 0  # passo 4: a taxa passa a ser zero
    assert com_cupom["desconto_cupom_centavos"] == 0
    assert com_cupom["total_centavos"] == 4980
    assert com_cupom["cupom"]["isenta_taxa_entrega"] is True

    conf = _confirmar(client, ana, 4980, "ENTREGA", end, codigo_cupom="FRETEGRATIS")
    assert conf.status_code == 201
    assert conf.json()["taxa_entrega_centavos"] == 0


def test_a1_trocar_ou_remover_cupom_desfaz_desconto_anterior(client, ana, gavea, banco, relogio):
    _cupom(client, banco, ana, codigo="CUPOM10", percentual_centesimos=1000, teto_centavos=None)
    _cupom(client, banco, ana, codigo="CUPOM20", percentual_centesimos=2000, teto_centavos=None)
    _add(client, ana, gavea["Burguer Clássico"], quantidade=2)  # subtotal = 4980

    p10 = _previa(client, ana, codigo_cupom="CUPOM10").json()
    assert p10["desconto_cupom_centavos"] == 498 and p10["total_centavos"] == 4482

    # Troca para CUPOM20
    p20 = _previa(client, ana, codigo_cupom="CUPOM20").json()
    assert p20["desconto_cupom_centavos"] == 996 and p20["total_centavos"] == 3984

    # Remove o cupom
    sem = _previa(client, ana, codigo_cupom=None).json()
    assert sem["desconto_cupom_centavos"] == 0 and sem["total_centavos"] == 4980 and sem["cupom"] is None


# --- Exceções E1 e E2 e Requisitos RF-14 a RF-18 ------------------------------


def test_e1_cupom_nao_encontrado(client, ana, gavea, relogio):
    _add(client, ana, gavea["Burguer Clássico"])
    r = _previa(client, ana, codigo_cupom="NAOEXISTE")
    assert r.status_code == 404 and r.json()["detail"]["motivo"] == "cupom_nao_encontrado"


def test_e2_cupom_expirado_e_fora_da_validade(client, ana, gavea, banco, relogio):
    # Relógio de teste está em 2026-11-18
    _cupom(client, banco, ana, codigo="PROMO5", inicio="2026-01-01", fim="2026-09-15")
    _cupom(client, banco, ana, codigo="FUTURO10", inicio="2026-12-01", fim="2026-12-31")
    _add(client, ana, gavea["Burguer Clássico"])

    r = _previa(client, ana, codigo_cupom="PROMO5")
    assert r.status_code == 422
    assert r.json()["detail"]["motivo"] == "cupom_expirado"
    assert "15/09/2026" in r.json()["detail"]["mensagem"]

    r2 = _previa(client, ana, codigo_cupom="FUTURO10")
    assert r2.status_code == 422 and r2.json()["detail"]["motivo"] == "cupom_fora_da_validade"


def test_e2_rf18_valor_minimo_comparado_com_subtotal_sem_taxa(client, ana, gavea, banco, relogio):
    # Subtotal = 2490 (< 2600), mas com a taxa de entrega (~270) passaria de 2600.
    # RF-18: o valor mínimo deve ser comparado apenas com o subtotal dos itens, sem a taxa.
    _cupom(client, banco, ana, codigo="MIN26", minimo_centavos=2600)
    _add(client, ana, gavea["Burguer Clássico"], quantidade=1)  # 2490
    end = _endereco(client, banco, ana)

    sem_cupom = _previa(client, ana, "ENTREGA", end).json()
    assert sem_cupom["subtotal_centavos"] == 2490
    assert sem_cupom["total_centavos"] > 2600

    r = _previa(client, ana, "ENTREGA", end, codigo_cupom="MIN26")
    assert r.status_code == 422 and r.json()["detail"]["motivo"] == "cupom_valor_minimo"


def test_e2_rf16_rf17_limite_de_usos_por_cliente_e_pedido_cancelado(client, ana, gavea, banco, relogio):
    _cupom(client, banco, ana, codigo="UNICO10", percentual_centesimos=1000, limite_usos=1)
    _add(client, ana, gavea["Burguer Clássico"])
    prev = _previa(client, ana, codigo_cupom="UNICO10").json()
    p1 = _confirmar(client, ana, prev["total_centavos"], codigo_cupom="UNICO10").json()

    # Tentar usar de novo em outro pedido deve falhar com limite atingido (E2, RF-16)
    _add(client, ana, gavea["Burguer Clássico"])
    r = _previa(client, ana, codigo_cupom="UNICO10")
    assert r.status_code == 422 and r.json()["detail"]["motivo"] == "cupom_limite_atingido"

    # Se o pedido anterior for CANCELADO, o uso não conta contra o limite (diagrama)
    banco.execute(
        """INSERT INTO notificacao (pedido_id, status, data_hora, titulo, mensagem)
           VALUES (?, 'CANCELADO', '2026-11-18T16:00:00+00:00', 'Cancelado', 'Pedido cancelado')""",
        (p1["id"],),
    )
    banco.commit()
    assert _previa(client, ana, codigo_cupom="UNICO10").status_code == 200


# --- Restrições no banco (RF-14, RF-15, RF-16, RNF-22) -----------------------


def test_rf14_rf15_rnf22_restricoes_de_cupom_no_banco(client, ana, novo_cliente, gavea, banco, relogio):
    cid = _cupom(client, banco, ana, codigo="BEMVINDO10", limite_usos=1)

    # RF-15: o mesmo cliente não pode ter dois cupons com o mesmo código
    with pytest.raises(sqlite3.IntegrityError):
        _cupom(client, banco, ana, codigo="BEMVINDO10")
    banco.rollback()

    # Outro cliente pode ter um cupom com o mesmo código (RF-15)
    bia = novo_cliente(email="bia@exemplo.com", nome="Bia")
    cid_bia = _cupom(client, banco, bia, codigo="BEMVINDO10")

    _add(client, ana, gavea["Burguer Clássico"])
    prev = _previa(client, ana, codigo_cupom="BEMVINDO10").json()
    pedido = _confirmar(client, ana, prev["total_centavos"], codigo_cupom="BEMVINDO10").json()

    # RF-14: no máximo um cupom por pedido (pedido_id UNIQUE em uso_cupom)
    cid2 = _cupom(client, banco, ana, codigo="OUTRO5", percentual_centesimos=500, limite_usos=5)
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute(
            "INSERT INTO uso_cupom (pedido_id, cupom_id, valor_descontado_centavos) VALUES (?, ?, 100)",
            (pedido["id"], cid2),
        )
    banco.rollback()

    # Trigger uso_cupom_valido: não permite registrar mais usos que limite_usos
    _add(client, ana, gavea["Burguer Clássico"])
    pedido2 = _confirmar(client, ana, 2490).json()
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute(
            "INSERT INTO uso_cupom (pedido_id, cupom_id, valor_descontado_centavos) VALUES (?, ?, 100)",
            (pedido2["id"], cid),
        )
    banco.rollback()

    # Trigger uso_cupom_valido: não permite usar cupom de outro cliente no pedido
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute(
            "INSERT INTO uso_cupom (pedido_id, cupom_id, valor_descontado_centavos) VALUES (?, ?, 100)",
            (pedido2["id"], cid_bia),
        )
    banco.rollback()

    # RNF-22: uso_cupom nunca é apagado fisicamente
    with pytest.raises(sqlite3.IntegrityError):
        banco.execute("DELETE FROM uso_cupom WHERE pedido_id = ?", (pedido["id"],))
    banco.rollback()
