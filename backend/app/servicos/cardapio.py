"""Unidades e cardápio: cópia local (cache) do que vem do SGL (decisão Q2).

Infra mínima — sem UC na ERS (decisão Q1) para listar unidades e consultar o
cardápio. Regras da ERS aplicadas aqui:
- RF-10: 0 ≤ desconto ≤ preço (também garantido por CHECK no banco).
- RF-11: combo sem preço próprio; preço e desconto = soma dos componentes.
- RF-13: quem monta o carrinho chama `atualizar_cardapio` antes de calcular.
- UC29 E3 / RNF-03: se o SGL falhar, fica o último cardápio salvo e o horário
  `cardapio_atualizado_em` não muda.
- RNF-22: produto que sai do cardápio vira `vigente = 0`, não é apagado.
"""

import logging
import sqlite3

from .. import relogio
from ..integracoes import sgl
from ..integracoes.base import IntegracaoIndisponivel
from . import precos

log = logging.getLogger(__name__)

# Pontos de troca para os testes simularem o SGL (monkeypatch).
buscar_unidades = sgl.obter_unidades
buscar_cardapio = sgl.obter_cardapio

_CAMPOS_UNIDADE = ("id_sgl", "nome", "rua", "numero", "bairro", "cidade", "estado", "cep",
                   "latitude", "longitude", "raio_max_entrega_m", "fator_taxa_entrega_centavos",
                   "tem_drive_thru")


def _int(valor: object, nome: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{nome} deve ser inteiro em centavos (RNF-23)")
    return valor


def sincronizar_unidades(conn: sqlite3.Connection) -> bool:
    """Atualiza a tabela `unidade` com o SGL. Devolve False se o SGL falhou."""
    try:
        unidades = [{c: u[c] for c in _CAMPOS_UNIDADE} for u in buscar_unidades()]
    except (IntegracaoIndisponivel, KeyError, TypeError) as exc:
        log.warning("unidades do SGL não atualizadas: %s", exc)
        return False
    for u in unidades:
        u["tem_drive_thru"] = 1 if u["tem_drive_thru"] else 0
        colunas = ", ".join(_CAMPOS_UNIDADE)
        marcas = ", ".join("?" for _ in _CAMPOS_UNIDADE)
        atualiza = ", ".join(f"{c} = excluded.{c}" for c in _CAMPOS_UNIDADE if c != "id_sgl")
        conn.execute(
            f"INSERT INTO unidade ({colunas}) VALUES ({marcas}) "
            f"ON CONFLICT(id_sgl) DO UPDATE SET {atualiza}",
            [u[c] for c in _CAMPOS_UNIDADE],
        )
    return True


def _normalizar_itens(itens: list) -> tuple[list[dict], list[dict]]:
    """Valida a resposta do SGL antes de gravar. ValueError se algo estiver errado."""
    simples, combos = [], []
    for it in itens:
        if not isinstance(it, dict):
            raise ValueError("item do cardápio em formato inesperado")
        base = {"id_sgl": str(it["id_sgl"]), "nome": str(it["nome"]),
                "descricao": str(it.get("descricao", "")), "categoria": str(it["categoria"])}
        if it["tipo"] == "SIMPLES":
            preco = _int(it["preco_centavos"], "preco_centavos")
            desconto = _int(it.get("desconto_centavos", 0), "desconto_centavos")
            if not 0 <= desconto <= preco:  # RF-10
                raise ValueError(f"desconto inválido no item {base['id_sgl']} (RF-10)")
            simples.append({**base, "preco": preco, "desconto": desconto})
        elif it["tipo"] == "COMBO":
            componentes = [(str(c["id_sgl"]), _int(c["quantidade"], "quantidade"))
                           for c in it["componentes"]]
            if not componentes or any(q < 1 for _, q in componentes):
                raise ValueError(f"combo {base['id_sgl']} sem componentes válidos")
            combos.append({**base, "componentes": componentes})
        else:
            raise ValueError(f"tipo de item desconhecido: {it['tipo']!r}")
    return simples, combos


def atualizar_cardapio(conn: sqlite3.Connection, unidade: sqlite3.Row) -> bool:
    """Busca o cardápio da unidade no SGL e grava no cache.

    Devolve False (e não mexe no cache) se o SGL estiver fora do ar ou responder
    algo inválido (RNF-19, UC29 E3).
    """
    try:
        simples, combos = _normalizar_itens(buscar_cardapio(unidade["id_sgl"])["itens"])
    except (IntegracaoIndisponivel, KeyError, TypeError, ValueError) as exc:
        log.warning("cardápio da unidade %s não atualizado: %s", unidade["id_sgl"], exc)
        return False

    uid = unidade["id"]
    for p in simples:
        conn.execute(
            """INSERT INTO produto (unidade_id, id_sgl, nome, descricao, categoria, tipo,
                                    preco_centavos, desconto_centavos, vigente)
               VALUES (?, ?, ?, ?, ?, 'SIMPLES', ?, ?, 1)
               ON CONFLICT(unidade_id, id_sgl) DO UPDATE SET
                   nome = excluded.nome, descricao = excluded.descricao,
                   categoria = excluded.categoria, tipo = 'SIMPLES',
                   preco_centavos = excluded.preco_centavos,
                   desconto_centavos = excluded.desconto_centavos, vigente = 1""",
            (uid, p["id_sgl"], p["nome"], p["descricao"], p["categoria"], p["preco"], p["desconto"]),
        )
    ids_simples = {p["id_sgl"] for p in simples}
    vigentes = set(ids_simples)
    for c in combos:
        # Combo só vale se todos os componentes estiverem no cardápio atual.
        completo = all(id_sgl in ids_simples for id_sgl, _ in c["componentes"])
        cur = conn.execute(
            """INSERT INTO produto (unidade_id, id_sgl, nome, descricao, categoria, tipo,
                                    preco_centavos, desconto_centavos, vigente)
               VALUES (?, ?, ?, ?, ?, 'COMBO', NULL, NULL, ?)
               ON CONFLICT(unidade_id, id_sgl) DO UPDATE SET
                   nome = excluded.nome, descricao = excluded.descricao,
                   categoria = excluded.categoria, tipo = 'COMBO',
                   preco_centavos = NULL, desconto_centavos = NULL, vigente = excluded.vigente
               RETURNING id""",
            (uid, c["id_sgl"], c["nome"], c["descricao"], c["categoria"], int(completo)),
        )
        combo_id = cur.fetchone()["id"]
        conn.execute("DELETE FROM combo_componente WHERE combo_id = ?", (combo_id,))
        if completo:
            vigentes.add(c["id_sgl"])
            for id_sgl, qtd in c["componentes"]:
                conn.execute(
                    """INSERT INTO combo_componente (combo_id, produto_id, quantidade)
                       SELECT ?, id, ? FROM produto WHERE unidade_id = ? AND id_sgl = ?""",
                    (combo_id, qtd, uid, id_sgl),
                )
    # O que não veio do SGL saiu do cardápio (RNF-22: desativa, não apaga).
    marcas = ", ".join("?" for _ in vigentes) or "''"
    conn.execute(f"UPDATE produto SET vigente = 0 WHERE unidade_id = ? AND id_sgl NOT IN ({marcas})",
                 (uid, *vigentes))
    conn.execute("UPDATE unidade SET cardapio_atualizado_em = ? WHERE id = ?",
                 (relogio.para_texto(relogio.agora()), uid))
    return True


def obter_unidade(conn: sqlite3.Connection, unidade_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM unidade WHERE id = ?", (unidade_id,)).fetchone()


def produtos(conn: sqlite3.Connection, unidade_id: int, ids: list[int] | None = None) -> dict[int, dict]:
    """Produtos da unidade com preço e desconto vigentes já calculados (RF-11).

    Sem `ids`, devolve só os vigentes; com `ids`, devolve esses (vigentes ou não),
    cada um com a chave `vigente`.
    """
    if ids is None:
        linhas = conn.execute("SELECT * FROM produto WHERE unidade_id = ? AND vigente = 1 "
                              "ORDER BY categoria, nome", (unidade_id,)).fetchall()
    else:
        marcas = ", ".join("?" for _ in ids) or "NULL"
        linhas = conn.execute(f"SELECT * FROM produto WHERE unidade_id = ? AND id IN ({marcas})",
                              (unidade_id, *ids)).fetchall()
    resultado = {}
    for p in linhas:
        info = {"id": p["id"], "nome": p["nome"], "descricao": p["descricao"],
                "categoria": p["categoria"], "tipo": p["tipo"], "vigente": bool(p["vigente"]),
                "componentes": []}
        if p["tipo"] == "SIMPLES":
            info["preco_centavos"], info["desconto_centavos"] = p["preco_centavos"], p["desconto_centavos"]
        else:
            comps = conn.execute(
                """SELECT p.id, p.nome, p.preco_centavos, p.desconto_centavos, p.vigente, cc.quantidade
                     FROM combo_componente cc JOIN produto p ON p.id = cc.produto_id
                    WHERE cc.combo_id = ? ORDER BY p.nome""",
                (p["id"],),
            ).fetchall()
            info["vigente"] = info["vigente"] and bool(comps) and all(c["vigente"] for c in comps)
            info["componentes"] = [
                {"produto_id": c["id"], "nome": c["nome"], "quantidade": c["quantidade"],
                 "preco_unitario_centavos": c["preco_centavos"],
                 "desconto_unitario_centavos": c["desconto_centavos"]}
                for c in comps
            ]
            info["preco_centavos"], info["desconto_centavos"] = precos.preco_combo(
                [(c["preco_centavos"], c["desconto_centavos"], c["quantidade"]) for c in comps])
        if ids is None and not info["vigente"]:
            continue
        resultado[p["id"]] = info
    return resultado
