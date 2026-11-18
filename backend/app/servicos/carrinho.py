"""Montagem do carrinho com valores sempre recalculados (UC29 passos 1–3, RF-13).

Cada vez que o carrinho é devolvido ao cliente:
1. tenta atualizar o cardápio da unidade no SGL; se falhar, usa o último salvo
   e informa o horário dele (UC29 E3, RNF-03);
2. retira itens que saíram do cardápio e avisa (UC29 E2);
3. recalcula cada item com o preço e o desconto vigentes (RF-02, RF-11, RF-13);
"""

import sqlite3

from .. import relogio
from . import cardapio, precos


def obter(conn: sqlite3.Connection, cliente_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM carrinho WHERE cliente_id = ?", (cliente_id,)).fetchone()


def tocar(conn: sqlite3.Connection, carrinho_id: int) -> None:
    conn.execute("UPDATE carrinho SET atualizado_em = ? WHERE id = ?",
                 (relogio.para_texto(relogio.agora()), carrinho_id))


def contar_itens(conn: sqlite3.Connection, carrinho_id: int) -> int:
    return conn.execute("SELECT COUNT(*) FROM item WHERE carrinho_id = ?", (carrinho_id,)).fetchone()[0]


def _vazio() -> dict:
    return {"unidade": None, "itens": [], "subtotal_centavos": 0, "avisos": [],
            "cardapio_atualizado_em": None, "sgl_indisponivel": False}


def montar(conn: sqlite3.Connection, cliente_id: int) -> dict:
    car = obter(conn, cliente_id)
    if car is None:
        return _vazio()  # UC29 E1: o front-end mostra "carrinho vazio"

    unidade = cardapio.obter_unidade(conn, car["unidade_id"])
    sgl_ok = cardapio.atualizar_cardapio(conn, unidade)
    unidade = cardapio.obter_unidade(conn, car["unidade_id"])

    linhas = conn.execute("SELECT * FROM item WHERE carrinho_id = ? ORDER BY id", (car["id"],)).fetchall()
    prods = cardapio.produtos(conn, unidade["id"], [l["produto_id"] for l in linhas])
    avisos, itens, subtotal = [], [], 0
    for l in linhas:
        p = prods[l["produto_id"]]
        if not p["vigente"]:  # UC29 E2
            conn.execute("DELETE FROM item WHERE id = ?", (l["id"],))
            avisos.append(f"{p['nome']} não está mais no cardápio e foi retirado do carrinho.")
            continue
        valor = precos.valor_final(l["quantidade"], p["preco_centavos"], p["desconto_centavos"])
        subtotal += valor
        itens.append({
            "id": l["id"], "produto_id": p["id"], "nome": p["nome"], "tipo": p["tipo"],
            "quantidade": l["quantidade"], "observacao": l["observacao"],
            "preco_unitario_centavos": p["preco_centavos"],
            "desconto_unitario_centavos": p["desconto_centavos"],
            "valor_final_centavos": valor,
            "componentes": p["componentes"],  # UC29 passo 3: itens do combo
        })

    return {
        "unidade": {"id": unidade["id"], "nome": unidade["nome"]},
        "itens": itens,
        "subtotal_centavos": subtotal,
        "avisos": avisos,
        "cardapio_atualizado_em": unidade["cardapio_atualizado_em"],
        "sgl_indisponivel": not sgl_ok,
    }
