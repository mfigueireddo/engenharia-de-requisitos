"""UC30 — Aplicar Cupom ao Pedido: listagem, validação, cálculo do desconto e registro de uso.

Regras da ERS (Seção 4.3 e Seção 5.5):
- RF-14: no máximo um cupom por pedido (USO_CUPOM.pedido_id UNIQUE).
- RF-15: cada cupom pertence a um único cliente; um cliente não pode ter dois
  cupons com o mesmo código (UNIQUE(cliente_id, codigo)).
- RF-16: o limite de usos é contado por cliente.
- RF-17: o uso só conta para o limite depois que o pedido é confirmado
  (pedidos cancelados não contam, conforme o projeto relacional).
- RF-18: o valor mínimo do cupom é comparado com o subtotal dos itens, sem a
  taxa de entrega.
- RN-07: cada pedido aceita no máximo um cupom, dentro da validade, com o valor
  mínimo atingido e com usos abaixo do limite.
- Passo 4: aplica o percentual de desconto sobre o subtotal dos itens
  (limitado por `valor_maximo_desconto_centavos`, se definido no modelo
  relacional / wireframe 07); se o cupom isenta a taxa de entrega, a taxa
  passa a ser zero.
- RNF-23: valores monetários em centavos inteiros; percentual em centésimos
  de ponto percentual (1000 = 10,00%), arredondado ao centavo mais próximo
  apenas com aritmética inteira.
"""

from datetime import date
import sqlite3

from .. import dinheiro, relogio


class ErroCupom(Exception):
    def __init__(self, status: int, motivo: str, mensagem: str):
        super().__init__(mensagem)
        self.status, self.motivo, self.mensagem = status, motivo, mensagem


def _data_br(iso: str) -> str:
    """Converte 'AAAA-MM-DD' para 'dd/mm/aaaa' (RNF-24)."""
    d = date.fromisoformat(iso)
    return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"


def usos_confirmados(conn: sqlite3.Connection, cupom_id: int) -> int:
    """RF-16, RF-17: quantidade de usos em pedidos confirmados (não cancelados)."""
    linha = conn.execute(
        """SELECT COUNT(*)
             FROM uso_cupom u
             JOIN pedido p ON p.id = u.pedido_id
            WHERE u.cupom_id = ?
              AND p.status <> 'CANCELADO'""",
        (cupom_id,),
    ).fetchone()
    return int(linha[0])


def cupom_publico(conn: sqlite3.Connection, c: sqlite3.Row) -> dict:
    """Representação pública de um cupom do cliente (para a tela 07)."""
    usos = usos_confirmados(conn, c["id"])
    hoje_str = relogio.hoje().isoformat()
    expirado = hoje_str > c["validade_fim"]
    agendado = hoje_str < c["validade_inicio"]
    esgotado = usos >= c["limite_usos"]
    return {
        "id": c["id"],
        "codigo": c["codigo"],
        "descricao": c["descricao"],
        "percentual_desconto_centesimos": c["percentual_desconto_centesimos"],
        "valor_maximo_desconto_centavos": c["valor_maximo_desconto_centavos"],
        "isenta_taxa_entrega": bool(c["isenta_taxa_entrega"]),
        "valor_minimo_pedido_centavos": c["valor_minimo_pedido_centavos"],
        "validade_inicio": c["validade_inicio"],
        "validade_fim": c["validade_fim"],
        "limite_usos": c["limite_usos"],
        "usos_realizados": usos,
        "disponivel": not (expirado or agendado or esgotado),
    }


def listar(conn: sqlite3.Connection, cliente_id: int) -> list[dict]:
    """Lista todos os cupons do cliente (RN-02, RNF-13, RF-15)."""
    linhas = conn.execute(
        "SELECT * FROM cupom_promocional WHERE cliente_id = ? ORDER BY id",
        (cliente_id,),
    ).fetchall()
    return [cupom_publico(conn, c) for c in linhas]


def calcular_desconto_percentual(
    subtotal_centavos: int,
    percentual_centesimos: int,
    valor_maximo_centavos: int | None = None,
) -> int:
    """Calcula o desconto percentual sobre o subtotal, só com inteiros (RNF-23).

    percentual_centesimos: 1000 = 10,00% (divisão por 10_000, arredondada ao
    centavo mais próximo). Respeita o teto `valor_maximo_centavos` e nunca
    ultrapassa o próprio `subtotal_centavos`.
    """
    if percentual_centesimos <= 0 or subtotal_centavos <= 0:
        return 0
    desconto = (subtotal_centavos * percentual_centesimos + 5_000) // 10_000
    if valor_maximo_centavos is not None and desconto > valor_maximo_centavos:
        desconto = valor_maximo_centavos
    if desconto > subtotal_centavos:
        desconto = subtotal_centavos
    return desconto


def validar_e_calcular(
    conn: sqlite3.Connection,
    cliente_id: int,
    codigo: str,
    subtotal_centavos: int,
) -> dict:
    """UC30 passos 2–4: busca o cupom do cliente, valida e calcula o desconto.

    Lança `ErroCupom` para E1 (cupom não encontrado) e E2 (cupom expirado,
    fora da validade, valor mínimo não atingido ou limite de usos atingido).
    """
    codigo_limpo = (codigo or "").strip().upper()
    if not codigo_limpo:
        raise ErroCupom(404, "cupom_nao_encontrado", "Informe o código do cupom.")

    # Passo 2: busca pelo código entre os cupons do cliente (RF-15, RNF-13).
    c = conn.execute(
        "SELECT * FROM cupom_promocional WHERE cliente_id = ? AND codigo = ?",
        (cliente_id, codigo_limpo),
    ).fetchone()
    if c is None:  # E1
        raise ErroCupom(
            404,
            "cupom_nao_encontrado",
            f"O código {codigo_limpo} não corresponde a nenhum cupom da sua conta.",
        )

    # Passo 3: validações (validade, limite de usos, valor mínimo sobre subtotal).
    hoje_str = relogio.hoje().isoformat()
    if hoje_str > c["validade_fim"]:  # E2: expirado (estilo wireframe 07)
        raise ErroCupom(
            422,
            "cupom_expirado",
            f"Cupom {c['codigo']} expirado em {_data_br(c['validade_fim'])}.",
        )
    if hoje_str < c["validade_inicio"]:  # E2: ainda não iniciou a validade
        raise ErroCupom(
            422,
            "cupom_fora_da_validade",
            f"Cupom {c['codigo']} só é válido a partir de {_data_br(c['validade_inicio'])}.",
        )

    usos = usos_confirmados(conn, c["id"])
    if usos >= c["limite_usos"]:  # E2, RF-16, RF-17
        raise ErroCupom(
            422,
            "cupom_limite_atingido",
            f"O limite de usos do cupom {c['codigo']} já foi atingido.",
        )

    if subtotal_centavos < c["valor_minimo_pedido_centavos"]:  # E2, RF-18
        minimo_txt = dinheiro.formatar(c["valor_minimo_pedido_centavos"])
        raise ErroCupom(
            422,
            "cupom_valor_minimo",
            f"O cupom {c['codigo']} exige subtotal mínimo de {minimo_txt} em itens.",
        )

    # Passo 4: calcula o desconto percentual e informa se isenta a taxa de entrega.
    desconto = calcular_desconto_percentual(
        subtotal_centavos,
        c["percentual_desconto_centesimos"],
        c["valor_maximo_desconto_centavos"],
    )
    return {
        "cupom_id": c["id"],
        "codigo": c["codigo"],
        "descricao": c["descricao"],
        "percentual_desconto_centesimos": c["percentual_desconto_centesimos"],
        "valor_maximo_desconto_centavos": c["valor_maximo_desconto_centavos"],
        "isenta_taxa_entrega": bool(c["isenta_taxa_entrega"]),
        "desconto_cupom_centavos": desconto,
    }


def registrar_uso(
    conn: sqlite3.Connection,
    pedido_id: int,
    cupom_id: int,
    valor_descontado_centavos: int,
) -> None:
    """UC30 passo 6 / RF-17: grava o uso do cupom quando o pedido é confirmado."""
    conn.execute(
        "INSERT INTO uso_cupom (pedido_id, cupom_id, valor_descontado_centavos) VALUES (?, ?, ?)",
        (pedido_id, cupom_id, valor_descontado_centavos),
    )


def uso_do_pedido(conn: sqlite3.Connection, pedido_id: int) -> dict | None:
    """Devolve o cupom usado num pedido confirmado, ou None se não houve cupom."""
    linha = conn.execute(
        """SELECT u.cupom_id, u.valor_descontado_centavos,
                  c.codigo, c.descricao, c.percentual_desconto_centesimos,
                  c.valor_maximo_desconto_centavos, c.isenta_taxa_entrega
             FROM uso_cupom u
             JOIN cupom_promocional c ON c.id = u.cupom_id
            WHERE u.pedido_id = ?""",
        (pedido_id,),
    ).fetchone()
    if linha is None:
        return None
    return {
        "cupom_id": linha["cupom_id"],
        "codigo": linha["codigo"],
        "descricao": linha["descricao"],
        "percentual_desconto_centesimos": linha["percentual_desconto_centesimos"],
        "valor_maximo_desconto_centavos": linha["valor_maximo_desconto_centavos"],
        "isenta_taxa_entrega": bool(linha["isenta_taxa_entrega"]),
        "desconto_cupom_centavos": linha["valor_descontado_centavos"],
    }
