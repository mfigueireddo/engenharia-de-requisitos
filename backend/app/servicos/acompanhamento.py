"""Regras de negócio do Acompanhar Pedido (UC31).

O SGL grava cada mudança como uma nova notificação (RF-22). O trigger do
schema mantém ``pedido.status`` igual à notificação mais recente (RF-20), e
este serviço filtra todos os pedidos pelo cliente autenticado (RF-19/RNF-13).
"""

import sqlite3
from typing import Any

from .. import relogio
from . import checkout

STATUS_PEDIDO = (
    "RECEBIDO",
    "PAGO",
    "EM_PREPARO",
    "PRONTO",
    "SAIU_PARA_ENTREGA",
    "ENTREGUE",
    "CANCELADO",
)


class ConexoesPedido:
    """Conexões WebSocket agrupadas por pedido para atualização em tempo real."""

    def __init__(self):
        self._por_pedido: dict[int, set[Any]] = {}

    async def adicionar(self, pedido_id: int, websocket: Any) -> None:
        self._por_pedido.setdefault(pedido_id, set()).add(websocket)

    def remover(self, pedido_id: int, websocket: Any) -> None:
        conexoes = self._por_pedido.get(pedido_id)
        if not conexoes:
            return
        conexoes.discard(websocket)
        if not conexoes:
            self._por_pedido.pop(pedido_id, None)

    async def publicar(self, pedido_id: int, evento: dict) -> None:
        """Envia uma notificação aos clientes conectados ao pedido.

        Uma aba fechada não pode impedir a entrega para as outras abas; ela é
        removida quando o WebSocket rejeita a mensagem.
        """
        for websocket in tuple(self._por_pedido.get(pedido_id, ())):
            try:
                await websocket.send_json(evento)
            except Exception:
                self.remover(pedido_id, websocket)


conexoes = ConexoesPedido()


def listar(conn: sqlite3.Connection, cliente_id: int) -> list[dict]:
    """Lista os pedidos do cliente, do mais recente para o mais antigo (passo 2)."""
    linhas = conn.execute(
        """SELECT p.id, p.status, p.modalidade, p.data_hora AS criado_em,
                  p.unidade_id, u.nome AS unidade_nome,
                  COALESCE(MAX(n.data_hora), p.data_hora) AS atualizado_em
             FROM pedido p
             JOIN unidade u ON u.id = p.unidade_id
             LEFT JOIN notificacao n ON n.pedido_id = p.id
            WHERE p.cliente_id = ?
            GROUP BY p.id
            ORDER BY p.data_hora DESC, p.id DESC""",
        (cliente_id,),
    ).fetchall()
    return [
        {
            "id": p["id"],
            "status": p["status"],
            "tipo_atendimento": p["modalidade"],
            "criado_em": p["criado_em"],
            "atualizado_em": p["atualizado_em"],
            "unidade": {"id": p["unidade_id"], "nome": p["unidade_nome"]},
        }
        for p in linhas
    ]


def obter(conn: sqlite3.Connection, cliente_id: int, pedido_id: int) -> dict | None:
    """Retorna o detalhe somente se o pedido pertencer ao cliente (RF-19)."""
    existe = conn.execute(
        "SELECT id FROM pedido WHERE id = ? AND cliente_id = ?", (pedido_id, cliente_id)
    ).fetchone()
    if existe is None:
        return None

    pedido = checkout.pedido_publico(conn, pedido_id)
    unidade = conn.execute(
        "SELECT id, nome FROM unidade WHERE id = (SELECT unidade_id FROM pedido WHERE id = ?)",
        (pedido_id,),
    ).fetchone()
    atualizado = conn.execute(
        "SELECT MAX(data_hora) AS data_hora FROM notificacao WHERE pedido_id = ?", (pedido_id,)
    ).fetchone()["data_hora"]
    pedido["unidade"] = {"id": unidade["id"], "nome": unidade["nome"]}
    pedido["atualizado_em"] = atualizado or pedido["criado_em"]
    return pedido


def registrar_notificacao(
    conn: sqlite3.Connection,
    pedido_id: int,
    status: str,
    titulo: str,
    mensagem: str,
    data_hora: str | None,
) -> tuple[dict, bool]:
    """Registra um webhook do SGL e devolve (notificação, avisar_cliente).

    A decisão de avisar é separada do registro: RF-22 exige guardar toda
    mudança mesmo quando o cliente desativou os avisos (RF-23).
    """
    pedido = conn.execute(
        "SELECT cliente_id FROM pedido WHERE id = ?", (pedido_id,)
    ).fetchone()
    if pedido is None:
        raise LookupError(pedido_id)

    momento = data_hora or relogio.para_texto(relogio.agora())
    cur = conn.execute(
        """INSERT INTO notificacao (pedido_id, status, data_hora, titulo, mensagem)
           VALUES (?, ?, ?, ?, ?)""",
        (pedido_id, status, momento, titulo, mensagem),
    )
    notificacao_id = cur.lastrowid
    avisar = conn.execute(
        "SELECT COALESCE(notificacoes_habilitadas, 0) FROM cliente WHERE id = ?",
        (pedido["cliente_id"],),
    ).fetchone()[0] == 1
    return (
        {
            "id": notificacao_id,
            "pedido_id": pedido_id,
            "status": status,
            "titulo": titulo,
            "mensagem": mensagem,
            "criado_em": momento,
        },
        avisar,
    )
