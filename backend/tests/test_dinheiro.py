"""RNF-23: valores monetários em centavos inteiros, sem ponto flutuante."""

import pytest

from app.dinheiro import de_reais, formatar, multiplicar


@pytest.mark.parametrize(
    "texto, centavos",
    [("0", 0), ("12", 1200), ("12,3", 1230), ("12,34", 1234), ("0,05", 5),
     ("1.234,56", 123456), (" 7,90 ", 790), ("1000000,00", 100000000)],
)
def test_rnf23_de_reais_converte_para_centavos(texto, centavos):
    assert de_reais(texto) == centavos


@pytest.mark.parametrize("texto", ["", "abc", "12,345", "-1,00", "12.34", "1.23,00", "1,", "R$ 5,00"])
def test_rnf23_de_reais_recusa_texto_invalido(texto):
    with pytest.raises(ValueError):
        de_reais(texto)


def test_rnf23_de_reais_recusa_float():
    with pytest.raises(TypeError):
        de_reais(12.34)


@pytest.mark.parametrize(
    "centavos, texto",
    [(0, "R$ 0,00"), (5, "R$ 0,05"), (1234, "R$ 12,34"), (123456, "R$ 1.234,56"),
     (100000000, "R$ 1.000.000,00"), (-500, "-R$ 5,00")],
)
def test_rnf23_formatar(centavos, texto):
    assert formatar(centavos) == texto


def test_rnf23_multiplicar_e_exato():
    # 0,10 + 0,20 em float dá 0,30000000000000004; em centavos é exato.
    assert multiplicar(10, 3) + multiplicar(20, 3) == 90
    assert multiplicar(2490, 2) == 4980


@pytest.mark.parametrize("args", [(12.34, 1), (1234, 1.0), (1234, True), ("1234", 1)])
def test_rnf23_recusa_tipos_nao_inteiros(args):
    with pytest.raises(TypeError):
        multiplicar(*args)


def test_rnf23_formatar_recusa_float():
    with pytest.raises(TypeError):
        formatar(12.34)
