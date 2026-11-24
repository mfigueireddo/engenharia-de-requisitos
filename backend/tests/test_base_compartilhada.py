"""Base de testes compartilhada (infra mínima — sem UC na ERS)."""

import sqlite3

from fastapi.testclient import TestClient

from scripts import base_compartilhada as base


def _foto(caminho) -> dict:
    """O que precisa ser igual em toda máquina: ids, clientes, sacolas e pedidos."""
    conn = sqlite3.connect(caminho)
    try:
        return {
            "clientes": conn.execute("SELECT id, email FROM cliente ORDER BY id").fetchall(),
            "enderecos": conn.execute("SELECT id, cliente_id, cep FROM endereco_cliente ORDER BY id").fetchall(),
            "itens": conn.execute(
                "SELECT id, carrinho_id, pedido_id, quantidade, observacao, valor_final_centavos "
                "FROM item_pedido ORDER BY id").fetchall(),
            "pedidos": conn.execute(
                "SELECT id, cliente_id, unidade_id, modalidade, taxa_entrega_centavos FROM pedido "
                "ORDER BY id").fetchall(),
            "cupons": conn.execute(
                "SELECT id, cliente_id, codigo FROM cupom_promocional ORDER BY id").fetchall(),
        }
    finally:
        conn.close()


def test_base_e_igual_toda_vez_que_e_recriada(banco_temporario):
    base.recriar()
    primeira = _foto(banco_temporario)
    base.recriar()
    assert _foto(banco_temporario) == primeira


def test_base_tem_os_cenarios_prometidos(banco_temporario):
    base.recriar()
    conn = sqlite3.connect(banco_temporario)
    conn.row_factory = sqlite3.Row

    def cliente(email):
        return conn.execute("SELECT id FROM cliente WHERE email = ?", (email,)).fetchone()["id"]

    # Ana: sacola com 3 itens na Gávea e cupons do wireframe 07; nenhum pedido.
    ana = cliente("ana@burguerja.com")
    sacola = conn.execute(
        "SELECT COUNT(*) FROM item_pedido i JOIN carrinho c ON c.id = i.carrinho_id WHERE c.cliente_id = ?",
        (ana,)).fetchone()[0]
    assert sacola == 3
    assert conn.execute("SELECT COUNT(*) FROM pedido WHERE cliente_id = ?", (ana,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM cupom_promocional WHERE cliente_id = ?", (ana,)).fetchone()[0] == 3

    # Bruno: um pedido com entrega (endereço copiado, RF-05) e um de retirada sem taxa (RN-05).
    bruno = cliente("bruno@burguerja.com")
    pedidos = conn.execute("SELECT * FROM pedido WHERE cliente_id = ? ORDER BY id", (bruno,)).fetchall()
    assert [p["modalidade"] for p in pedidos] == ["ENTREGA", "RETIRADA"]
    assert pedidos[1]["taxa_entrega_centavos"] == 0
    assert conn.execute("SELECT COUNT(*) FROM endereco_pedido WHERE pedido_id = ?",
                        (pedidos[0]["id"],)).fetchone()[0] == 1

    # Carla: conta vazia.
    carla = cliente("carla@burguerja.com")
    assert conn.execute("SELECT COUNT(*) FROM endereco_cliente WHERE cliente_id = ?", (carla,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM carrinho WHERE cliente_id = ?", (carla,)).fetchone()[0] == 0

    # Ninguém começa logado.
    assert conn.execute("SELECT COUNT(*) FROM sessao").fetchone()[0] == 0
    conn.close()


def test_todos_os_clientes_da_base_entram_com_a_senha_documentada(banco_temporario):
    base.recriar()
    emails = [base.dados_demo.EMAIL] + [c["email"] for c in base.CLIENTES]
    with TestClient(base._api()) as c:
        for email in emails:
            r = c.post("/api/auth/login", json={"email": email, "senha": base.SENHA})
            assert r.status_code == 200, email
