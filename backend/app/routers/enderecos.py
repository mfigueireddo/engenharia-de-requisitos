"""Listagem dos endereços salvos do cliente — usada pelo UC28 (passo 5).

Só leitura. Cadastrar, editar e remover endereços é o UC33, a cargo de outro
integrante. Cada cliente vê apenas os próprios endereços (RN-02, RNF-13).
"""

import sqlite3

from fastapi import APIRouter, Depends

from .. import seguranca

router = APIRouter(prefix="/api/enderecos", tags=["endereços (listagem para o UC28)"])


@router.get("")
def meus_enderecos(cliente=Depends(seguranca.cliente_atual),
                   conn: sqlite3.Connection = Depends(seguranca.conexao)):
    linhas = conn.execute(
        "SELECT id, logradouro AS rua, numero, complemento, bairro, cidade, estado, cep "
        "FROM endereco_cliente "
        "WHERE cliente_id = ? ORDER BY id", (cliente["id"],)).fetchall()
    return [dict(l) for l in linhas]
