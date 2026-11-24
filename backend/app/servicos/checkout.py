"""UC28 — Finalizar Pedido: cálculo do resumo (passos 2–8) e confirmação (9–11).

Fórmulas que a ERS deixa em aberto, decididas pelo humano na sessão
2026-11-18_henriqueecoa_carrinho-e-cupom:
- Distância (RF-06): linha reta (Haversine) entre a unidade e as coordenadas do
  CEP do endereço, obtidas pela geocodificação simulada (decisão Q8).
- Taxa de entrega (RN-05): distância em km × fator da unidade (centavos por km),
  arredondada ao centavo mais próximo, só com inteiros (RNF-23).
- Tempo estimado (passo 7, RNF-06): 30 min + 3 min por km iniciado. É sempre uma
  estimativa; o front-end deve apresentá-lo assim.

Cupom (A3 / UC30): `Escolha.codigo_cupom` (opcional) aplica um cupom do cliente
via `servicos.cupons.validar_e_calcular`. O desconto percentual entra em
`desconto_cupom_centavos` (e em `uso_cupom.valor_descontado_centavos` na
confirmação, RF-17); se o cupom isenta a taxa de entrega, `taxa_entrega_centavos`
passa a ser zero (UC30 passo 4).

Tabelas (projeto relacional): `pedido` (modalidade, taxa, previsao_entrega),
`endereco_pedido` (cópia do endereço, só em ENTREGA) e `item_pedido`. Subtotal
e total não são colunas: saem da soma dos itens (passo 8).
"""

from datetime import timedelta

import math
import sqlite3
from dataclasses import dataclass

from .. import relogio
from ..integracoes import geocodificacao
from ..integracoes.base import IntegracaoIndisponivel
from . import carrinho, cardapio, cupons

TEMPO_PREPARO_MIN = 30
MINUTOS_POR_KM = 3
RAIO_TERRA_M = 6_371_000

TIPOS = ("ENTREGA", "RETIRADA", "DRIVE_THRU")

# Ponto de troca para os testes simularem a geocodificação (monkeypatch).
buscar_coordenadas = geocodificacao.geocodificar


class ErroCheckout(Exception):
    def __init__(self, status: int, motivo: str, mensagem: str):
        super().__init__(mensagem)
        self.status, self.motivo, self.mensagem = status, motivo, mensagem


@dataclass
class Escolha:
    tipo_atendimento: str
    endereco_id: int | None = None
    codigo_cupom: str | None = None


def distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Distância em linha reta (Haversine), em metros inteiros."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df, dl = f2 - f1, math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return round(2 * RAIO_TERRA_M * math.asin(math.sqrt(a)))


def taxa_entrega(distancia: int, fator_centavos_por_km: int) -> int:
    """RN-05: km × fator, arredondado ao centavo mais próximo (só inteiros, RNF-23)."""
    return (distancia * fator_centavos_por_km + 500) // 1000


def tempo_estimado_min(distancia: int) -> int:
    """Estimativa (RNF-06): preparo + minutos por km iniciado."""
    km_iniciados = -(-distancia // 1000)
    return TEMPO_PREPARO_MIN + MINUTOS_POR_KM * km_iniciados


def tipos_disponiveis(unidade: sqlite3.Row) -> list[str]:
    """Passo 3 / RN-04: drive-thru só na unidade que tem. A entrega aparece como
    opção, mas só vale para endereço dentro do raio (verificado no passo 6)."""
    return [t for t in TIPOS if t != "DRIVE_THRU" or unidade["aceita_drive_thru"]]


_CAMPOS_ENDERECO = ("logradouro", "numero", "complemento", "bairro", "cidade", "estado", "cep")


def _endereco_publico(e) -> dict:
    # A API mantém "rua"; no banco a coluna é "logradouro" (projeto relacional).
    return {"id": e["id"], "rua": e["logradouro"], **{k: e[k] for k in _CAMPOS_ENDERECO[1:]}}


def calcular(conn: sqlite3.Connection, cliente_id: int, escolha: Escolha) -> dict:
    """Passos 2 a 8: resumo do carrinho, atendimento, distância, taxa e total."""
    resumo = carrinho.montar(conn, cliente_id)  # passo 2, com preços vigentes (RF-13)
    if not resumo["itens"]:  # E1, RF-07
        raise ErroCheckout(409, "carrinho_vazio", "Seu carrinho está vazio.")
    unidade = cardapio.obter_unidade(conn, resumo["unidade"]["id"])  # RF-01
    tipos = tipos_disponiveis(unidade)
    if escolha.tipo_atendimento not in tipos:  # RN-04
        raise ErroCheckout(422, "atendimento_indisponivel", "Esta unidade não oferece esse tipo de atendimento.")

    entrega = None
    taxa = 0  # RN-05: retirada e drive-thru não têm taxa (A1)
    if escolha.tipo_atendimento == "ENTREGA":
        if escolha.endereco_id is None:
            raise ErroCheckout(422, "endereco_obrigatorio", "Escolha um endereço para a entrega.")
        end = conn.execute("SELECT * FROM endereco_cliente WHERE id = ? AND cliente_id = ?",
                           (escolha.endereco_id, cliente_id)).fetchone()
        if end is None:  # RNF-13: endereço de outro cliente = não encontrado
            raise ErroCheckout(404, "endereco_nao_encontrado", "Endereço não encontrado.")
        try:
            coord = buscar_coordenadas(end["cep"])
        except ValueError:
            coord = None
        except IntegracaoIndisponivel:  # RNF-19
            raise ErroCheckout(503, "geocodificacao_indisponivel",
                               "Não foi possível verificar o endereço agora. Tente mais tarde "
                               "ou escolha outro tipo de atendimento.") from None
        if coord is None:  # decisão Q8: CEP desconhecido não serve para entrega
            raise ErroCheckout(422, "cep_desconhecido",
                               "Não conseguimos localizar este CEP; o endereço não pode ser usado para entrega.")
        dist = distancia_m(unidade["latitude"], unidade["longitude"], coord.latitude, coord.longitude)
        if dist > unidade["distancia_maxima_km"] * 1000:  # E2, RF-06, RN-04
            raise ErroCheckout(422, "fora_do_raio",
                               "Este endereço está fora da área de entrega da unidade. "
                               "Escolha outro endereço ou outro tipo de atendimento.")
        taxa = taxa_entrega(dist, unidade["fator_taxa_entrega_centavos"])  # passo 7
        entrega = {"endereco": _endereco_publico(end), "distancia_m": dist,
                   "tempo_estimado_min": tempo_estimado_min(dist)}

    desconto_cupom = 0
    cupom_aplicado = None
    if escolha.codigo_cupom and escolha.codigo_cupom.strip():  # A3 / UC30
        try:
            cupom_aplicado = cupons.validar_e_calcular(
                conn, cliente_id, escolha.codigo_cupom, resumo["subtotal_centavos"]
            )
        except cupons.ErroCupom as e:
            raise ErroCheckout(e.status, e.motivo, e.mensagem) from None
        desconto_cupom = cupom_aplicado["desconto_cupom_centavos"]
        if cupom_aplicado["isenta_taxa_entrega"]:  # UC30 passo 4: a taxa passa a ser zero
            taxa = 0

    return {
        "carrinho": resumo,
        "tipos_atendimento_disponiveis": tipos,
        "tipo_atendimento": escolha.tipo_atendimento,
        "entrega": entrega,
        "cupom": cupom_aplicado,
        "subtotal_centavos": resumo["subtotal_centavos"],
        "desconto_cupom_centavos": desconto_cupom,
        "taxa_entrega_centavos": taxa,
        "total_centavos": resumo["subtotal_centavos"] - desconto_cupom + taxa,  # passo 8
    }


def confirmar(conn: sqlite3.Connection, cliente_id: int, escolha: Escolha, total_mostrado: int) -> int:
    """Passos 9–11. Recalcula tudo no servidor (RNF-14) e só cria o pedido se o
    total for o mesmo que o cliente viu (RNF-26: valor cobrado = valor mostrado).
    Devolve o id do pedido."""
    calc = calcular(conn, cliente_id, escolha)
    if calc["total_centavos"] != total_mostrado:
        raise ErroCheckout(409, "valores_mudaram",
                           "Os valores do pedido mudaram. Revise o resumo antes de confirmar.")
    car = carrinho.obter(conn, cliente_id)
    momento = relogio.agora()
    agora = relogio.para_texto(momento)
    entrega = calc["entrega"]
    previsao = (relogio.para_texto(momento + timedelta(minutes=entrega["tempo_estimado_min"]))
                if entrega else None)
    # O status inicial vem da notificação RECEBIDO (trigger pedido_status_da_notificacao);
    # o INSERT já usa o mesmo valor porque a coluna é NOT NULL.
    cur = conn.execute(
        """INSERT INTO pedido (cliente_id, unidade_id, data_hora, modalidade, status,
               taxa_entrega_centavos, previsao_entrega)
           VALUES (?, ?, ?, ?, 'RECEBIDO', ?, ?)""",
        (cliente_id, car["unidade_id"], agora, escolha.tipo_atendimento,  # RF-01
         calc["taxa_entrega_centavos"], previsao),
    )
    pedido_id = cur.lastrowid
    if entrega:  # RF-05, RF-31: cópia do endereço, na mesma transação do pedido
        e = entrega["endereco"]
        conn.execute(
            f"INSERT INTO endereco_pedido (pedido_id, {', '.join(_CAMPOS_ENDERECO)}) "
            f"VALUES (?, {', '.join('?' for _ in _CAMPOS_ENDERECO)})",
            (pedido_id, e["rua"], *(e[k] for k in _CAMPOS_ENDERECO[1:])),
        )
    # Passo 10: os itens saem do carrinho e entram no pedido (RF-09). Os valores
    # já foram recalculados e gravados pelo carrinho.montar (RF-13) e, com
    # pedido_id preenchido, ficam congelados (RF-03, RN-06; trigger item_pedido_congelado).
    for item in calc["carrinho"]["itens"]:
        conn.execute(
            "UPDATE item_pedido SET carrinho_id = NULL, pedido_id = ? WHERE id = ? AND carrinho_id = ?",
            (pedido_id, item["id"], car["id"]),
        )
    conn.execute("DELETE FROM carrinho WHERE id = ?", (car["id"],))  # carrinho já está vazio
    if calc["cupom"]:  # UC30 passo 6, RF-14, RF-17: registra uso do cupom na confirmação
        cupons.registrar_uso(
            conn, pedido_id, calc["cupom"]["cupom_id"], calc["desconto_cupom_centavos"]
        )
    conn.execute(  # passo 11, RF-22
        "INSERT INTO notificacao (pedido_id, status, titulo, mensagem, data_hora) VALUES (?, 'RECEBIDO', ?, ?, ?)",
        (pedido_id, "Pedido recebido", "Recebemos seu pedido. Agora é só concluir o pagamento.", agora),
    )
    return pedido_id


def pedido_publico(conn: sqlite3.Connection, pedido_id: int) -> dict:
    p = conn.execute("SELECT * FROM pedido WHERE id = ?", (pedido_id,)).fetchone()
    itens = conn.execute(
        """SELECT i.id, ic.nome, i.quantidade, i.observacao, i.preco_unitario_centavos,
                  i.desconto_unitario_centavos, i.valor_final_centavos
             FROM item_pedido i JOIN item_cardapio ic ON ic.id = i.item_cardapio_id
            WHERE i.pedido_id = ? ORDER BY i.id""",
        (pedido_id,),
    ).fetchall()
    notificacoes = conn.execute(
        "SELECT status, titulo, mensagem, data_hora AS criado_em FROM notificacao WHERE pedido_id = ? ORDER BY id",
        (pedido_id,),
    ).fetchall()
    entrega = None
    if p["modalidade"] == "ENTREGA":
        end = conn.execute("SELECT * FROM endereco_pedido WHERE pedido_id = ?", (pedido_id,)).fetchone()
        minutos = (relogio.de_texto(p["previsao_entrega"]) - relogio.de_texto(p["data_hora"])) // timedelta(minutes=1)
        entrega = {"endereco": {k: v for k, v in _endereco_publico(end).items() if k != "id"},
                   "previsao_entrega": p["previsao_entrega"], "tempo_estimado_min": minutos}
    subtotal = sum(i["valor_final_centavos"] for i in itens)
    uso_cupom = cupons.uso_do_pedido(conn, pedido_id)
    desconto_cupom = uso_cupom["desconto_cupom_centavos"] if uso_cupom else 0
    return {
        "id": p["id"], "status": p["status"], "unidade_id": p["unidade_id"],
        "tipo_atendimento": p["modalidade"], "entrega": entrega,
        "cupom": uso_cupom,
        "itens": [dict(i) for i in itens],
        "subtotal_centavos": subtotal,
        "desconto_cupom_centavos": desconto_cupom,
        "taxa_entrega_centavos": p["taxa_entrega_centavos"],
        "total_centavos": subtotal - desconto_cupom + p["taxa_entrega_centavos"],  # UC28 passo 8
        "criado_em": p["data_hora"],
        "notificacoes": [dict(n) for n in notificacoes],
    }
