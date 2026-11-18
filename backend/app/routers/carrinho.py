"""Carrinho: UC29 (Gerenciar Itens do Carrinho).

Também tem "adicionar ao carrinho" (UC27, citado na ERS mas não especificado) e
"esvaziar carrinho" (RN-03): infra mínima — sem UC na ERS (decisão Q1).

Todas as rotas exigem cliente logado (RN-01, RNF-09) e só mexem no carrinho do
próprio cliente (RN-02, RNF-13). Toda resposta devolve o carrinho recalculado
no servidor (RF-13, RNF-14); preços enviados pelo navegador são ignorados.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from .. import seguranca
from ..servicos import cardapio, carrinho

router = APIRouter(prefix="/api/carrinho", tags=["carrinho (UC29)"])

MAX_OBSERVACAO = 200


def _limpar_observacao(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    return v or None


class ItemEntrada(BaseModel):
    produto_id: int
    quantidade: int = Field(default=1, ge=1)  # RF-12
    observacao: str | None = Field(default=None, max_length=MAX_OBSERVACAO)

    _obs = field_validator("observacao")(lambda cls, v: _limpar_observacao(v))


class ItemAlteracao(BaseModel):
    quantidade: int | None = Field(default=None, ge=0)  # 0 remove o item (RF-12, UC29 A1)
    observacao: str | None = Field(default=None, max_length=MAX_OBSERVACAO)

    _obs = field_validator("observacao")(lambda cls, v: _limpar_observacao(v))


def _item_do_cliente(conn: sqlite3.Connection, item_id: int, cliente_id: int) -> sqlite3.Row:
    """RNF-13: item de outro cliente responde 404, sem revelar que existe."""
    item = conn.execute(
        """SELECT i.*, c.id AS car_id FROM item i JOIN carrinho c ON c.id = i.carrinho_id
            WHERE i.id = ? AND c.cliente_id = ?""",
        (item_id, cliente_id),
    ).fetchone()
    if item is None:
        raise HTTPException(404, "Item não encontrado no seu carrinho.")
    return item


@router.get("")
def ver_carrinho(cliente=Depends(seguranca.cliente_atual),
                 conn: sqlite3.Connection = Depends(seguranca.conexao)):
    """UC29 passos 1–3 (e E1, E2, E3)."""
    return carrinho.montar(conn, cliente["id"])


@router.post("/itens", status_code=201)
def adicionar_item(entrada: ItemEntrada, cliente=Depends(seguranca.cliente_atual),
                   conn: sqlite3.Connection = Depends(seguranca.conexao)):
    """UC27 (infra mínima — sem UC na ERS): põe um produto vigente no carrinho."""
    produto = conn.execute("SELECT id, unidade_id FROM produto WHERE id = ?",
                           (entrada.produto_id,)).fetchone()
    if produto is None:
        raise HTTPException(404, "Produto não encontrado.")
    unidade = cardapio.obter_unidade(conn, produto["unidade_id"])
    cardapio.atualizar_cardapio(conn, unidade)  # RF-13: confere no cardápio vigente
    if not cardapio.produtos(conn, unidade["id"], [produto["id"]])[produto["id"]]["vigente"]:
        raise HTTPException(409, "Este item não está mais no cardápio da unidade.")

    car = carrinho.obter(conn, cliente["id"])
    if car is None:
        cur = conn.execute("INSERT INTO carrinho (cliente_id, unidade_id) VALUES (?, ?)",
                           (cliente["id"], unidade["id"]))
        car_id = cur.lastrowid
    else:
        car_id = car["id"]
        if car["unidade_id"] != unidade["id"]:
            if carrinho.contar_itens(conn, car_id):  # RN-03, RF-08
                raise HTTPException(409, "Seu carrinho tem itens de outra unidade. "
                                         "Esvazie o carrinho para pedir nesta unidade (RN-03).")
            conn.execute("UPDATE carrinho SET unidade_id = ? WHERE id = ?", (unidade["id"], car_id))
    conn.execute("INSERT INTO item (carrinho_id, produto_id, quantidade, observacao) VALUES (?, ?, ?, ?)",
                 (car_id, produto["id"], entrada.quantidade, entrada.observacao))
    carrinho.tocar(conn, car_id)
    return carrinho.montar(conn, cliente["id"])


@router.patch("/itens/{item_id}")
def alterar_item(item_id: int, entrada: ItemAlteracao, cliente=Depends(seguranca.cliente_atual),
                 conn: sqlite3.Connection = Depends(seguranca.conexao)):
    """UC29 passo 4 (quantidade), A1 (quantidade zero remove) e A2 (observação)."""
    if not entrada.model_fields_set & {"quantidade", "observacao"}:
        raise HTTPException(422, "Informe a quantidade e/ou a observação.")
    if "quantidade" in entrada.model_fields_set and entrada.quantidade is None:
        raise HTTPException(422, "Quantidade inválida.")
    item = _item_do_cliente(conn, item_id, cliente["id"])
    if entrada.quantidade == 0:  # RF-12, UC29 A1
        conn.execute("DELETE FROM item WHERE id = ?", (item_id,))
    else:
        if entrada.quantidade is not None:
            conn.execute("UPDATE item SET quantidade = ? WHERE id = ?", (entrada.quantidade, item_id))
        if "observacao" in entrada.model_fields_set:  # A2: não altera o valor do item
            conn.execute("UPDATE item SET observacao = ? WHERE id = ?", (entrada.observacao, item_id))
    carrinho.tocar(conn, item["car_id"])
    return carrinho.montar(conn, cliente["id"])


@router.delete("/itens/{item_id}")
def remover_item(item_id: int, cliente=Depends(seguranca.cliente_atual),
                 conn: sqlite3.Connection = Depends(seguranca.conexao)):
    """UC29 A1."""
    item = _item_do_cliente(conn, item_id, cliente["id"])
    conn.execute("DELETE FROM item WHERE id = ?", (item_id,))
    carrinho.tocar(conn, item["car_id"])
    return carrinho.montar(conn, cliente["id"])


@router.delete("")
def esvaziar(cliente=Depends(seguranca.cliente_atual),
             conn: sqlite3.Connection = Depends(seguranca.conexao)):
    """Esvaziar o carrinho (RN-03; infra mínima — sem UC na ERS). Libera a troca de unidade."""
    conn.execute("DELETE FROM carrinho WHERE cliente_id = ?", (cliente["id"],))  # itens: ON DELETE CASCADE
    return carrinho.montar(conn, cliente["id"])
