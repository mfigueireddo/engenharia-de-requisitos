"""Unidades e cardápio — rotas públicas (RN-01: visitante pode ver o cardápio).

Infra mínima — sem UC na ERS (decisão Q1). Dados vindos do SGL e guardados como
cache (decisão Q2); se o SGL falhar, usa o último cardápio salvo (RNF-03).
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from .. import seguranca
from ..servicos import cardapio

router = APIRouter(prefix="/api/unidades", tags=["unidades e cardápio (infra mínima)"])


def _unidade_publica(u: sqlite3.Row) -> dict:
    # Nomes da API mantidos (contrato com o front-end); no banco: endereco_unidade.logradouro
    # e unidade.aceita_drive_thru.
    return {"id": u["id"], "nome": u["nome"], "rua": u["logradouro"], "numero": u["numero"],
            "bairro": u["bairro"], "cidade": u["cidade"], "estado": u["estado"], "cep": u["cep"],
            "tem_drive_thru": bool(u["aceita_drive_thru"])}


@router.get("")
def listar_unidades(conn: sqlite3.Connection = Depends(seguranca.conexao)):
    cardapio.sincronizar_unidades(conn)
    ids = [u["id"] for u in conn.execute("SELECT id FROM unidade ORDER BY nome")]
    return [_unidade_publica(cardapio.obter_unidade(conn, i)) for i in ids]


@router.get("/{unidade_id}/cardapio")
def ver_cardapio(unidade_id: int, conn: sqlite3.Connection = Depends(seguranca.conexao)):
    unidade = cardapio.obter_unidade(conn, unidade_id)
    if unidade is None:
        raise HTTPException(404, "Unidade não encontrada.")
    sgl_ok = cardapio.atualizar_cardapio(conn, unidade)
    unidade = cardapio.obter_unidade(conn, unidade_id)
    produtos = []
    for p in cardapio.produtos(conn, unidade_id).values():
        p = {k: v for k, v in p.items() if k != "vigente"}
        p["preco_final_centavos"] = p["preco_centavos"] - p["desconto_centavos"]  # RF-02, qtd 1
        produtos.append(p)
    return {
        "unidade": _unidade_publica(unidade),
        "produtos": produtos,
        "cardapio_atualizado_em": unidade["cardapio_atualizado_em"],  # RNF-03
        "sgl_indisponivel": not sgl_ok,
    }
