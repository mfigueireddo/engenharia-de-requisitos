"""HTTP/WebSocket do Acompanhar Pedido (UC31)."""

import hashlib
import hmac
import json
import logging
import os
import sqlite3
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError

from .. import db, relogio, seguranca
from ..servicos import acompanhamento

logger = logging.getLogger(__name__)
router = APIRouter()

StatusPedido = Literal[
    "RECEBIDO",
    "PAGO",
    "EM_PREPARO",
    "PRONTO",
    "SAIU_PARA_ENTREGA",
    "ENTREGUE",
    "CANCELADO",
]


class AtualizacaoSGL(BaseModel):
    status: StatusPedido
    titulo: str = Field(min_length=1)
    mensagem: str = Field(min_length=1)
    data_hora: str | None = None


@router.get("/api/pedidos", tags=["acompanhar pedido (UC31)"])
def listar_pedidos(cliente=Depends(seguranca.cliente_atual), conn: sqlite3.Connection = Depends(seguranca.conexao)):
    return acompanhamento.listar(conn, cliente["id"])


@router.get("/api/pedidos/{pedido_id}", tags=["acompanhar pedido (UC31)"])
def obter_pedido(pedido_id: int, cliente=Depends(seguranca.cliente_atual),
                 conn: sqlite3.Connection = Depends(seguranca.conexao)):
    pedido = acompanhamento.obter(conn, cliente["id"], pedido_id)
    if pedido is None:  # E1/RF-19: não revela se o pedido existe para outro cliente
        raise HTTPException(404, "Pedido não encontrado.")
    return pedido


def _assinatura_valida(corpo: bytes, assinatura: str | None) -> bool:
    segredo = os.environ.get("BURGUERJA_SGL_WEBHOOK_SECRET", "")
    if not segredo or not assinatura:
        return False
    esperada = hmac.new(segredo.encode("utf-8"), corpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(assinatura, f"sha256={esperada}")


@router.post("/api/webhooks/sgl/pedidos/{pedido_id}/status", status_code=201,
             tags=["acompanhar pedido (UC31)"])
async def webhook_status(pedido_id: int, request: Request,
                         x_sgl_signature: str | None = Header(default=None)):
    corpo = await request.body()
    if not _assinatura_valida(corpo, x_sgl_signature):  # RNF-15
        logger.warning("Webhook SGL recusado: assinatura inválida (pedido=%s)", pedido_id)
        raise HTTPException(401, "Assinatura do SGL inválida.")
    try:
        atualizacao = AtualizacaoSGL(**json.loads(corpo))
    except (json.JSONDecodeError, TypeError, ValidationError):
        raise HTTPException(422, "Payload de atualização inválido.") from None

    conn = db.conectar()
    try:
        try:
            notificacao, avisar = acompanhamento.registrar_notificacao(
                conn, pedido_id, atualizacao.status, atualizacao.titulo,
                atualizacao.mensagem, atualizacao.data_hora,
            )
        except LookupError:
            raise HTTPException(404, "Pedido não encontrado.") from None
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    evento = {"tipo": "status_atualizado", "avisar": avisar, "notificacao": notificacao}
    await acompanhamento.conexoes.publicar(pedido_id, evento)
    return evento


@router.websocket("/api/ws/pedidos/{pedido_id}")
async def acompanhar_por_websocket(websocket: WebSocket, pedido_id: int):
    """Canal autenticado para as atualizações sem recarregar a página."""
    token = websocket.query_params.get("token")
    conn = db.conectar()
    try:
        cliente = seguranca.cliente_por_token(conn, token)
        pedido = acompanhamento.obter(conn, cliente["id"], pedido_id) if cliente else None
        if pedido is None:  # RNF-13: nem o WebSocket revela pedido de terceiro
            await websocket.close(code=1008)
            return
        await websocket.accept()
        await acompanhamento.conexoes.adicionar(pedido_id, websocket)
        await websocket.send_json({"tipo": "conectado", "pedido": pedido})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        acompanhamento.conexoes.remover(pedido_id, websocket)
        conn.close()
