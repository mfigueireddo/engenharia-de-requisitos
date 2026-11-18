"""UC28 — Finalizar Pedido (checkout).

Fluxo na API:
1. `POST /api/pedidos/previa` (passos 2–8): resumo, opções de atendimento,
   distância, taxa, tempo estimado e total. Não grava nada.
2. `POST /api/pedidos` (passos 9–11): confirma. Recalcula tudo no servidor
   (RNF-14) e exige o total que o cliente viu na prévia (RNF-26).

Pagamento (passo 11, "leva à tela de pagamento"), envio ao SGL e acompanhamento
são de outros casos de uso. Exige login (RN-01) e só usa dados do próprio
cliente (RN-02, RNF-13).
"""

import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import seguranca
from ..servicos import checkout

router = APIRouter(prefix="/api/pedidos", tags=["finalizar pedido (UC28)"])


class EscolhaEntrada(BaseModel):
    tipo_atendimento: Literal["ENTREGA", "RETIRADA", "DRIVE_THRU"]
    endereco_id: int | None = None


class ConfirmacaoEntrada(EscolhaEntrada):
    total_centavos: int = Field(ge=0)  # o total mostrado na prévia (RNF-26)


def _executar(funcao, *args):
    try:
        return funcao(*args)
    except checkout.ErroCheckout as e:
        raise HTTPException(e.status, {"motivo": e.motivo, "mensagem": e.mensagem}) from None


@router.post("/previa")
def previa(entrada: EscolhaEntrada, cliente=Depends(seguranca.cliente_atual),
           conn: sqlite3.Connection = Depends(seguranca.conexao)):
    escolha = checkout.Escolha(entrada.tipo_atendimento, entrada.endereco_id)
    return _executar(checkout.calcular, conn, cliente["id"], escolha)


@router.post("", status_code=201)
def confirmar(entrada: ConfirmacaoEntrada, cliente=Depends(seguranca.cliente_atual),
              conn: sqlite3.Connection = Depends(seguranca.conexao)):
    escolha = checkout.Escolha(entrada.tipo_atendimento, entrada.endereco_id)
    pedido_id = _executar(checkout.confirmar, conn, cliente["id"], escolha, entrada.total_centavos)
    return checkout.pedido_publico(conn, pedido_id)
