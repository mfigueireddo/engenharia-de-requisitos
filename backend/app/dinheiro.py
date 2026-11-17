"""Valores monetários em centavos inteiros (RNF-23).

A ERS exige dinheiro com duas casas decimais e sem ponto flutuante. Por isso
todo valor em dinheiro do back-end é um `int` em centavos (R$ 12,34 → 1234), e
estas funções recusam `float` em vez de convertê-lo em silêncio.

Divisão e arredondamento (ex.: taxa de entrega por distância, RN-05) ficam para
quando o UC28 for implementado.
"""

import re

Centavos = int
"""Valor em dinheiro, em centavos inteiros (RNF-23)."""

_REAIS = re.compile(r"^(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{1,2}))?$")


def _exigir_inteiro(valor: object, nome: str) -> int:
    # bool é subclasse de int em Python; não é um valor monetário válido.
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TypeError(f"{nome} deve ser int (centavos), não {type(valor).__name__} (RNF-23)")
    return valor


def de_reais(texto: str) -> Centavos:
    """Converte um texto em reais no formato brasileiro para centavos.

    Aceita "12", "12,3", "12,34" e "1.234,56". Recusa valores negativos, mais de
    duas casas decimais e qualquer coisa que não seja `str` (inclusive `float`).
    """
    if not isinstance(texto, str):
        raise TypeError(f"esperado texto em reais, não {type(texto).__name__} (RNF-23)")
    limpo = texto.strip()
    m = _REAIS.match(limpo)
    if not m:
        raise ValueError(f"valor em reais inválido: {texto!r}")
    inteiro, _, decimais = limpo.partition(",")
    return int(inteiro.replace(".", "")) * 100 + int(decimais.ljust(2, "0") or "0")


def formatar(valor: Centavos) -> str:
    """Formata centavos como texto em reais: 123456 → "R$ 1.234,56"."""
    _exigir_inteiro(valor, "valor")
    sinal = "-" if valor < 0 else ""
    reais, centavos = divmod(abs(valor), 100)
    return f"{sinal}R$ {reais:,}".replace(",", ".") + f",{centavos:02d}"


def multiplicar(valor: Centavos, quantidade: int) -> Centavos:
    """Valor unitário × quantidade, sem arredondamento (resultado exato em centavos)."""
    return _exigir_inteiro(valor, "valor") * _exigir_inteiro(quantidade, "quantidade")
