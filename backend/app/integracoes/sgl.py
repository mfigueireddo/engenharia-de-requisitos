"""Cliente do SGL (Sistema de Gestão da Loja), simulado.

O SGL é sistema externo (ERS 2.5, 3.3); o BurguerJá só consulta o cardápio de
cada unidade. Aqui a "chamada" lê um JSON fixo de exemplo
(dados_simulados/cardapios_sgl.json). A carga desse cardápio no banco e as
rotas de cardápio ficam para o passo 3 do plano. No exemplo, o combo não tem
preço próprio: vale a soma dos componentes, com o desconto de cada um (RF-11).

Toda chamada tem tempo limite e tratamento de erro (RNF-19). Em caso de falha,
quem chama deve usar o último cardápio salvo (UC29 E3, RNF-03).
"""

import json
from pathlib import Path
from typing import Callable

from .base import IntegracaoIndisponivel, chamar_com_tempo_limite

SISTEMA = "SGL"
ARQUIVO_SIMULADO = Path(__file__).resolve().parent / "dados_simulados" / "cardapios_sgl.json"

Transporte = Callable[[str], object]
"""Função que faz a chamada ao SGL e devolve a resposta bruta (JSON decodificado)."""


def _transporte_simulado(id_sgl_unidade: str) -> object:
    cardapios = json.loads(ARQUIVO_SIMULADO.read_text(encoding="utf-8"))
    if id_sgl_unidade not in cardapios:
        raise LookupError(f"unidade {id_sgl_unidade!r} não existe no SGL simulado")
    return cardapios[id_sgl_unidade]


def _validar(resposta: object) -> dict:
    if not isinstance(resposta, dict) or not isinstance(resposta.get("itens"), list):
        raise IntegracaoIndisponivel(SISTEMA, "resposta em formato inesperado")
    return resposta


def obter_cardapio(
    id_sgl_unidade: str,
    *,
    transporte: Transporte = _transporte_simulado,
    tempo_limite: float | None = None,
) -> dict:
    """Cardápio de uma unidade, como o SGL devolve (preços em centavos, RNF-23).

    Levanta IntegracaoIndisponivel se o SGL demorar além do tempo limite, der
    erro ou responder em formato inesperado (RNF-19). `transporte` existe para
    os testes simularem falhas.
    """
    resposta = chamar_com_tempo_limite(SISTEMA, transporte, id_sgl_unidade, tempo_limite=tempo_limite)
    return _validar(resposta)
