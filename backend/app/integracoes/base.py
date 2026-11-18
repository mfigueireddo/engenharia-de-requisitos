"""Tempo limite e tratamento de erro comuns às integrações externas (RNF-19).

A RNF-19 exige que toda chamada ao Gateway de Pagamento e ao SGL tenha tempo
limite e tratamento de erro. Por decisão do grupo (Q8), a geocodificação
simulada segue a mesma regra.

Qualquer falha (demora acima do limite, exceção, resposta inválida) vira
`IntegracaoIndisponivel`, e quem chama decide o que fazer. Exemplo: no UC29 E3
o carrinho usa o último cardápio salvo.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as _Timeout
from typing import Callable, TypeVar

T = TypeVar("T")

TEMPO_LIMITE_PADRAO_S = 3.0
VARIAVEL_TEMPO_LIMITE = "BURGUERJA_TIMEOUT_INTEGRACOES"


class IntegracaoIndisponivel(Exception):
    """O sistema externo não respondeu a tempo ou respondeu com erro (RNF-19)."""

    def __init__(self, sistema: str, motivo: str):
        super().__init__(f"{sistema} indisponível: {motivo}")
        self.sistema = sistema
        self.motivo = motivo


def tempo_limite_padrao() -> float:
    """Tempo limite em segundos; configurável por BURGUERJA_TIMEOUT_INTEGRACOES."""
    bruto = os.environ.get(VARIAVEL_TEMPO_LIMITE)
    if bruto is None:
        return TEMPO_LIMITE_PADRAO_S
    try:
        valor = float(bruto)
    except ValueError:
        raise ValueError(f"{VARIAVEL_TEMPO_LIMITE} inválido: {bruto!r}") from None
    if valor <= 0:
        raise ValueError(f"{VARIAVEL_TEMPO_LIMITE} deve ser positivo: {bruto!r}")
    return valor


def chamar_com_tempo_limite(
    sistema: str,
    funcao: Callable[..., T],
    *args,
    tempo_limite: float | None = None,
) -> T:
    """Executa `funcao(*args)` com tempo limite; falhas viram IntegracaoIndisponivel."""
    limite = tempo_limite_padrao() if tempo_limite is None else tempo_limite
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        futuro = executor.submit(funcao, *args)
        try:
            return futuro.result(timeout=limite)
        except _Timeout:
            raise IntegracaoIndisponivel(sistema, f"sem resposta em {limite:g} s") from None
        except Exception as exc:
            raise IntegracaoIndisponivel(sistema, f"erro na chamada ({type(exc).__name__}: {exc})") from exc
    finally:
        # Não espera a thread que estourou o tempo; ela termina sozinha.
        executor.shutdown(wait=False, cancel_futures=True)
