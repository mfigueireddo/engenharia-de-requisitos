"""UC28 — Finalizar Pedido: cálculo do resumo (passos 2–8) e confirmação (9–11).

Fórmulas que a ERS deixa em aberto, decididas pelo humano na sessão
2026-11-18_henriqueecoa_carrinho-e-cupom:
- Distância (RF-06): linha reta (Haversine) entre a unidade e as coordenadas do
  CEP do endereço, obtidas pela geocodificação simulada (decisão Q8).
- Taxa de entrega (RN-05): distância em km × fator da unidade (centavos por km),
  arredondada ao centavo mais próximo, só com inteiros (RNF-23).
- Tempo estimado (passo 7, RNF-06): 30 min + 3 min por km iniciado. É sempre uma
  estimativa; o front-end deve apresentá-lo assim.

Cupom (A3): o UC30 é de outro integrante. O total já prevê o desconto
(`desconto_cupom_centavos`), hoje sempre zero; o UC30 deve preenchê-lo aqui.
"""

import math
import sqlite3
from dataclasses import dataclass

from .. import relogio
from ..integracoes import geocodificacao
from ..integracoes.base import IntegracaoIndisponivel
from . import carrinho, cardapio

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
    return [t for t in TIPOS if t != "DRIVE_THRU" or unidade["tem_drive_thru"]]


def _endereco_publico(e) -> dict:
    return {"id": e["id"], "rua": e["rua"], "numero": e["numero"], "complemento": e["complemento"],
            "bairro": e["bairro"], "cidade": e["cidade"], "estado": e["estado"], "cep": e["cep"]}


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
        end = conn.execute("SELECT * FROM endereco WHERE id = ? AND cliente_id = ?",
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
        if dist > unidade["raio_max_entrega_m"]:  # E2, RF-06, RN-04
            raise ErroCheckout(422, "fora_do_raio",
                               "Este endereço está fora da área de entrega da unidade. "
                               "Escolha outro endereço ou outro tipo de atendimento.")
        taxa = taxa_entrega(dist, unidade["fator_taxa_entrega_centavos"])  # passo 7
        entrega = {"endereco": _endereco_publico(end), "distancia_m": dist,
                   "tempo_estimado_min": tempo_estimado_min(dist)}

    desconto_cupom = 0  # A3 / UC30: a cargo de outro integrante
    return {
        "carrinho": resumo,
        "tipos_atendimento_disponiveis": tipos,
        "tipo_atendimento": escolha.tipo_atendimento,
        "entrega": entrega,
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
    agora = relogio.para_texto(relogio.agora())
    e = (calc["entrega"] or {}).get("endereco") or {}
    cur = conn.execute(
        """INSERT INTO pedido (cliente_id, unidade_id, status, tipo_atendimento,
               entrega_rua, entrega_numero, entrega_complemento, entrega_bairro, entrega_cidade,
               entrega_estado, entrega_cep, distancia_m, tempo_estimado_min, subtotal_centavos,
               taxa_entrega_centavos, desconto_cupom_centavos, total_centavos, criado_em)
           VALUES (?, ?, 'RECEBIDO', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (cliente_id, car["unidade_id"], escolha.tipo_atendimento,  # RF-01
         e.get("rua"), e.get("numero"), e.get("complemento"), e.get("bairro"), e.get("cidade"),
         e.get("estado"), e.get("cep"),  # RF-05: cópia do endereço
         (calc["entrega"] or {}).get("distancia_m"), (calc["entrega"] or {}).get("tempo_estimado_min"),
         calc["subtotal_centavos"], calc["taxa_entrega_centavos"], calc["desconto_cupom_centavos"],
         calc["total_centavos"], agora),
    )
    pedido_id = cur.lastrowid
    # Passo 10: os itens saem do carrinho e entram no pedido (RF-09) com preço,
    # desconto e valor final congelados (RF-03, RN-06).
    for item in calc["carrinho"]["itens"]:
        conn.execute(
            """UPDATE item SET carrinho_id = NULL, pedido_id = ?, preco_unitario_centavos = ?,
                   desconto_unitario_centavos = ?, valor_final_centavos = ?
               WHERE id = ? AND carrinho_id = ?""",
            (pedido_id, item["preco_unitario_centavos"], item["desconto_unitario_centavos"],
             item["valor_final_centavos"], item["id"], car["id"]),
        )
    conn.execute("DELETE FROM carrinho WHERE id = ?", (car["id"],))  # carrinho já está vazio
    conn.execute(  # passo 11, RF-22
        "INSERT INTO notificacao (pedido_id, status, titulo, mensagem, criado_em) VALUES (?, 'RECEBIDO', ?, ?, ?)",
        (pedido_id, "Pedido recebido", "Recebemos seu pedido. Agora é só concluir o pagamento.", agora),
    )
    return pedido_id


def pedido_publico(conn: sqlite3.Connection, pedido_id: int) -> dict:
    p = conn.execute("SELECT * FROM pedido WHERE id = ?", (pedido_id,)).fetchone()
    itens = conn.execute(
        """SELECT i.id, pr.nome, i.quantidade, i.observacao, i.preco_unitario_centavos,
                  i.desconto_unitario_centavos, i.valor_final_centavos
             FROM item i JOIN produto pr ON pr.id = i.produto_id
            WHERE i.pedido_id = ? ORDER BY i.id""",
        (pedido_id,),
    ).fetchall()
    notificacoes = conn.execute(
        "SELECT status, titulo, mensagem, criado_em FROM notificacao WHERE pedido_id = ? ORDER BY id",
        (pedido_id,),
    ).fetchall()
    entrega = None
    if p["tipo_atendimento"] == "ENTREGA":
        entrega = {"endereco": {k: p[f"entrega_{k}"] for k in
                                ("rua", "numero", "complemento", "bairro", "cidade", "estado", "cep")},
                   "distancia_m": p["distancia_m"], "tempo_estimado_min": p["tempo_estimado_min"]}
    return {
        "id": p["id"], "status": p["status"], "unidade_id": p["unidade_id"],
        "tipo_atendimento": p["tipo_atendimento"], "entrega": entrega,
        "itens": [dict(i) for i in itens],
        "subtotal_centavos": p["subtotal_centavos"],
        "desconto_cupom_centavos": p["desconto_cupom_centavos"],
        "taxa_entrega_centavos": p["taxa_entrega_centavos"],
        "total_centavos": p["total_centavos"], "criado_em": p["criado_em"],
        "notificacoes": [dict(n) for n in notificacoes],
    }
