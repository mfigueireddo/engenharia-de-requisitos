"""Unidades e cardápio: cópia local (cache) do que vem do SGL (decisão Q2).

Infra mínima — sem UC na ERS (decisão Q1) para listar unidades e consultar o
cardápio. Regras da ERS aplicadas aqui:
- RF-10: 0 ≤ desconto ≤ preço (também garantido por CHECK no banco).
- RF-11: combo sem preço próprio; preço e desconto = soma dos componentes.
- RF-13: quem monta o carrinho chama `atualizar_cardapio` antes de calcular.
- UC29 E3 / RNF-03: se o SGL falhar, fica o último cardápio salvo e o horário
  `cardapio_atualizado_em` não muda.
- RNF-22: item que sai do cardápio perde a ligação em `cardapio_item`, mas
  continua em `item_cardapio` (pedidos antigos apontam para ele).

Tabelas (projeto relacional, docs/srs/Projeto_Relacional_de_Tabelas.drawio):
unidade + endereco_unidade; cardapio + cardapio_item; item_cardapio com herança
item_simples / combo; item_no_combo.
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

_CAMPOS_UNIDADE = ("id_sgl", "nome", "latitude", "longitude", "distancia_maxima_km",
                   "fator_taxa_entrega_centavos", "aceita_drive_thru")
_CAMPOS_ENDERECO = ("logradouro", "numero", "complemento", "bairro", "cidade", "estado", "cep")
_OPCIONAIS_UNIDADE = ("telefone_contato", "horario_funcionamento")


def _int(valor: object, nome: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"{nome} deve ser inteiro em centavos (RNF-23)")
    return valor


def sincronizar_unidades(conn: sqlite3.Connection) -> bool:
    """Atualiza `unidade` e `endereco_unidade` com o SGL. Devolve False se o SGL falhou."""
    try:
        unidades = []
        for u in buscar_unidades():
            dados = {c: u[c] for c in _CAMPOS_UNIDADE}
            dados.update({c: u.get(c) for c in _OPCIONAIS_UNIDADE})
            dados["aceita_drive_thru"] = 1 if dados["aceita_drive_thru"] else 0
            endereco = {c: u["endereco"].get(c) for c in _CAMPOS_ENDERECO}
            unidades.append((dados, endereco))
    except (IntegracaoIndisponivel, KeyError, TypeError, AttributeError) as exc:
        log.warning("unidades do SGL não atualizadas: %s", exc)
        return False
    for dados, endereco in unidades:
        colunas = list(dados)
        atualiza = ", ".join(f"{c} = excluded.{c}" for c in colunas if c != "id_sgl")
        unidade_id = conn.execute(
            f"INSERT INTO unidade ({', '.join(colunas)}) VALUES ({', '.join('?' for _ in colunas)}) "
            f"ON CONFLICT(id_sgl) DO UPDATE SET {atualiza} RETURNING id",
            [dados[c] for c in colunas],
        ).fetchone()["id"]
        atualiza = ", ".join(f"{c} = excluded.{c}" for c in _CAMPOS_ENDERECO)
        conn.execute(
            f"INSERT INTO endereco_unidade (unidade_id, {', '.join(_CAMPOS_ENDERECO)}) "
            f"VALUES (?, {', '.join('?' for _ in _CAMPOS_ENDERECO)}) "
            f"ON CONFLICT(unidade_id) DO UPDATE SET {atualiza}",
            [unidade_id, *(endereco[c] for c in _CAMPOS_ENDERECO)],
        )
        conn.execute("INSERT OR IGNORE INTO cardapio (unidade_id) VALUES (?)", (unidade_id,))
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


def _gravar_cardapio(conn: sqlite3.Connection, unidade_id: int,
                     simples: list[dict], combos: list[dict]) -> None:
    def item_cardapio(it: dict) -> int:
        return conn.execute(
            """INSERT INTO item_cardapio (id_sgl, nome, descricao, categoria) VALUES (?, ?, ?, ?)
               ON CONFLICT(id_sgl) DO UPDATE SET nome = excluded.nome,
                   descricao = excluded.descricao, categoria = excluded.categoria
               RETURNING id""",
            (it["id_sgl"], it["nome"], it["descricao"], it["categoria"]),
        ).fetchone()["id"]

    ofertados, ids = [], {}
    for p in simples:
        ids[p["id_sgl"]] = item_id = item_cardapio(p)
        conn.execute(
            """INSERT INTO item_simples (item_cardapio_id, preco_centavos, desconto_item_centavos)
               VALUES (?, ?, ?)
               ON CONFLICT(item_cardapio_id) DO UPDATE SET preco_centavos = excluded.preco_centavos,
                   desconto_item_centavos = excluded.desconto_item_centavos""",
            (item_id, p["preco"], p["desconto"]),
        )
        ofertados.append(item_id)
    for c in combos:
        item_id = item_cardapio(c)
        conn.execute("INSERT OR IGNORE INTO combo (item_cardapio_id) VALUES (?)", (item_id,))
        # Combo só é oferecido se todos os componentes estiverem no cardápio atual
        # e se tiver 2 ou mais itens (regra do diagrama).
        if all(id_sgl in ids for id_sgl, _ in c["componentes"]) and len(c["componentes"]) >= 2:
            conn.execute("DELETE FROM item_no_combo WHERE combo_id = ?", (item_id,))
            conn.executemany(
                "INSERT INTO item_no_combo (combo_id, item_simples_id, quantidade) VALUES (?, ?, ?)",
                [(item_id, ids[id_sgl], qtd) for id_sgl, qtd in c["componentes"]],
            )
            ofertados.append(item_id)
        else:
            log.warning("combo %s fora do cardápio da unidade %s: componentes incompletos",
                        c["id_sgl"], unidade_id)

    # O cardápio passa a ter só o que veio do SGL. O que saiu perde a ligação,
    # mas o item continua em item_cardapio (RNF-22).
    conn.execute("INSERT OR IGNORE INTO cardapio (unidade_id) VALUES (?)", (unidade_id,))
    cardapio_id = conn.execute("SELECT id FROM cardapio WHERE unidade_id = ?", (unidade_id,)).fetchone()["id"]
    conn.execute("DELETE FROM cardapio_item WHERE cardapio_id = ?", (cardapio_id,))
    conn.executemany("INSERT INTO cardapio_item (cardapio_id, item_cardapio_id) VALUES (?, ?)",
                     [(cardapio_id, i) for i in dict.fromkeys(ofertados)])
    conn.execute("UPDATE unidade SET cardapio_atualizado_em = ? WHERE id = ?",
                 (relogio.para_texto(relogio.agora()), unidade_id))


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
    # SAVEPOINT: se o banco recusar algo (ex.: item que era simples e virou combo),
    # nada do cardápio novo fica gravado e vale o último salvo.
    conn.execute("SAVEPOINT cardapio")
    try:
        _gravar_cardapio(conn, unidade["id"], simples, combos)
    except sqlite3.IntegrityError as exc:
        conn.execute("ROLLBACK TO cardapio")
        conn.execute("RELEASE cardapio")
        log.warning("cardápio da unidade %s recusado pelo banco: %s", unidade["id_sgl"], exc)
        return False
    conn.execute("RELEASE cardapio")
    return True


def obter_unidade(conn: sqlite3.Connection, unidade_id: int) -> sqlite3.Row | None:
    """Unidade com o endereço (endereco_unidade) na mesma linha."""
    return conn.execute(
        """SELECT u.*, e.logradouro, e.numero, e.complemento, e.bairro, e.cidade, e.estado, e.cep
             FROM unidade u LEFT JOIN endereco_unidade e ON e.unidade_id = u.id
            WHERE u.id = ?""",
        (unidade_id,),
    ).fetchone()


_SELECT_ITEM = """
    SELECT ic.*, s.preco_centavos, s.desconto_item_centavos,
           CASE WHEN s.item_cardapio_id IS NOT NULL THEN 'SIMPLES' ELSE 'COMBO' END AS tipo,
           EXISTS (SELECT 1 FROM cardapio_item ci JOIN cardapio ca ON ca.id = ci.cardapio_id
                    WHERE ci.item_cardapio_id = ic.id AND ca.unidade_id = :unidade) AS vigente
      FROM item_cardapio ic LEFT JOIN item_simples s ON s.item_cardapio_id = ic.id
"""


def produtos(conn: sqlite3.Connection, unidade_id: int, ids: list[int] | None = None) -> dict[int, dict]:
    """Itens do cardápio da unidade com preço e desconto vigentes já calculados (RF-11).

    Sem `ids`, devolve só os que estão no cardápio da unidade; com `ids`, devolve
    esses (estejam ou não), cada um com a chave `vigente`.
    """
    if ids is None:
        linhas = conn.execute(
            f"SELECT * FROM ({_SELECT_ITEM}) WHERE vigente ORDER BY categoria, nome",
            {"unidade": unidade_id}).fetchall()
    else:
        marcas = ", ".join(f":i{n}" for n in range(len(ids))) or "NULL"
        linhas = conn.execute(f"SELECT * FROM ({_SELECT_ITEM}) WHERE id IN ({marcas})",
                              {"unidade": unidade_id, **{f"i{n}": i for n, i in enumerate(ids)}}).fetchall()
    resultado = {}
    for p in linhas:
        info = {"id": p["id"], "nome": p["nome"], "descricao": p["descricao"],
                "categoria": p["categoria"], "tipo": p["tipo"], "vigente": bool(p["vigente"]),
                "componentes": []}
        if p["tipo"] == "SIMPLES":
            info["preco_centavos"], info["desconto_centavos"] = p["preco_centavos"], p["desconto_item_centavos"]
        else:
            comps = conn.execute(
                """SELECT ic.id, ic.nome, s.preco_centavos, s.desconto_item_centavos, nc.quantidade
                     FROM item_no_combo nc
                     JOIN item_simples s ON s.item_cardapio_id = nc.item_simples_id
                     JOIN item_cardapio ic ON ic.id = s.item_cardapio_id
                    WHERE nc.combo_id = ? ORDER BY ic.nome""",
                (p["id"],),
            ).fetchall()
            info["componentes"] = [
                {"produto_id": c["id"], "nome": c["nome"], "quantidade": c["quantidade"],
                 "preco_unitario_centavos": c["preco_centavos"],
                 "desconto_unitario_centavos": c["desconto_item_centavos"]}
                for c in comps
            ]
            info["preco_centavos"], info["desconto_centavos"] = precos.preco_combo(
                [(c["preco_centavos"], c["desconto_item_centavos"], c["quantidade"]) for c in comps])
        resultado[p["id"]] = info
    return resultado
