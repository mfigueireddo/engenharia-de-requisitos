"""UC30 — Aplicar Cupom ao Pedido.

Rotas:
- `GET /api/cupons`: lista os cupons do cliente logado (para a tela 07).
- `POST /api/cupons/aplicar`: valida o código do cupom contra o subtotal atual
  do carrinho do cliente (UC30 passos 2–5, E1, E2) e devolve o desconto
  calculado, sem gravar uso (o uso só é registrado quando o pedido é confirmado,
  em `POST /api/pedidos`, RF-17).

Exige login (RN-01, RNF-09) e só acessa cupons do próprio cliente (RN-02,
RNF-13, RF-15).
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .. import seguranca
from ..servicos import carrinho, cupons

router = APIRouter(prefix="/api/cupons", tags=["aplicar cupom (UC30)"])


class AplicarCupomEntrada(BaseModel):
    codigo: str


@router.get("")
def meus_cupons(
    cliente=Depends(seguranca.cliente_atual),
    conn: sqlite3.Connection = Depends(seguranca.conexao),
):
    return cupons.listar(conn, cliente["id"])


@router.post("/aplicar")
def aplicar_cupom(
    entrada: AplicarCupomEntrada,
    cliente=Depends(seguranca.cliente_atual),
    conn: sqlite3.Connection = Depends(seguranca.conexao),
):
    resumo = carrinho.montar(conn, cliente["id"])
    if not resumo["itens"]:
        raise HTTPException(
            409,
            {"motivo": "carrinho_vazio", "mensagem": "Seu carrinho está vazio."},
        )
    try:
        resultado = cupons.validar_e_calcular(
            conn, cliente["id"], entrada.codigo, resumo["subtotal_centavos"]
        )
    except cupons.ErroCupom as e:
        raise HTTPException(e.status, {"motivo": e.motivo, "mensagem": e.mensagem}) from None
    return {
        **resultado,
        "subtotal_centavos": resumo["subtotal_centavos"],
    }
