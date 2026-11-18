"""Cálculos de preço, todos em centavos inteiros (RNF-23) e feitos no servidor (RNF-14)."""

from ..dinheiro import Centavos, multiplicar


def valor_final(quantidade: int, preco: Centavos, desconto: Centavos) -> Centavos:
    """RF-02: valor final = quantidade × (preço unitário − desconto unitário)."""
    if not 0 <= desconto <= preco:
        raise ValueError("desconto fora do intervalo [0, preço] (RF-10)")
    return multiplicar(preco - desconto, quantidade)


def preco_combo(componentes: list[tuple[Centavos, Centavos, int]]) -> tuple[Centavos, Centavos]:
    """RF-11: preço do combo = soma dos preços dos componentes; o desconto também
    é a soma dos descontos de cada componente (aplicado item a item).

    `componentes` = [(preço, desconto, quantidade), ...]. Devolve (preço, desconto).
    """
    preco = sum(multiplicar(p, q) for p, _, q in componentes)
    desconto = sum(multiplicar(d, q) for _, d, q in componentes)
    return preco, desconto

