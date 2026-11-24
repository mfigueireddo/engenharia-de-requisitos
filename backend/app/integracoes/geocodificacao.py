"""Geocodificação simulada: CEP → latitude/longitude (decisão do grupo Q8).

A ERS não diz como obter as coordenadas do endereço do cliente, necessárias para
a distância do RF-06 (raio de entrega, UC28). O grupo decidiu (Q8) usar um
serviço simulado com uma tabela fixa de CEPs de exemplo. Um CEP fora da tabela
significa que o endereço não pode ser usado para entrega.

Por decisão do grupo, a chamada segue a mesma regra da RNF-19 (tempo limite e
tratamento de erro), como se fosse um serviço externo. Essa é uma extensão:
a RNF-19 cita só o SGL e o Gateway de Pagamento.
"""

import re
from dataclasses import dataclass
from typing import Callable

from .base import IntegracaoIndisponivel, chamar_com_tempo_limite

SISTEMA = "Geocodificação"


@dataclass(frozen=True)
class Coordenadas:
    latitude: float
    longitude: float


# CEPs de exemplo na região da Gávea (Rio de Janeiro), com coordenadas
# aproximadas. Servem só para testes e demonstração.
CEPS_SIMULADOS: dict[str, Coordenadas] = {
    "22451900": Coordenadas(-22.9790, -43.2330),  # PUC-Rio, R. Marquês de São Vicente
    "22451040": Coordenadas(-22.9764, -43.2290),  # Gávea, R. Marquês de São Vicente (início)
    "22470050": Coordenadas(-22.9681, -43.2210),  # Jardim Botânico
    "22250040": Coordenadas(-22.9460, -43.1800),  # Botafogo, Praia de Botafogo (dentro do raio da unidade Botafogo)
}

Transporte = Callable[[str], Coordenadas | None]


def normalizar_cep(cep: str) -> str:
    """'22451-900' → '22451900'. Levanta ValueError se não tiver 8 dígitos."""
    digitos = re.sub(r"[\s-]", "", cep or "")
    if not re.fullmatch(r"\d{8}", digitos):
        raise ValueError(f"CEP inválido: {cep!r}")
    return digitos


def _transporte_simulado(cep: str) -> Coordenadas | None:
    return CEPS_SIMULADOS.get(cep)


def geocodificar(
    cep: str,
    *,
    transporte: Transporte = _transporte_simulado,
    tempo_limite: float | None = None,
) -> Coordenadas | None:
    """Coordenadas do CEP, ou None se o CEP não for conhecido (não serve para entrega).

    Levanta ValueError para CEP mal formado e IntegracaoIndisponivel se o serviço
    demorar além do tempo limite, der erro ou responder algo inesperado.
    """
    normalizado = normalizar_cep(cep)
    resposta = chamar_com_tempo_limite(SISTEMA, transporte, normalizado, tempo_limite=tempo_limite)
    if resposta is not None and not isinstance(resposta, Coordenadas):
        raise IntegracaoIndisponivel(SISTEMA, "resposta em formato inesperado")
    return resposta
