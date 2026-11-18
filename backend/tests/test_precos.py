"""Cálculos de preço (RF-02, RF-10, RF-11), em centavos (RNF-23)."""

import pytest

from app.servicos import precos


def test_rf02_valor_final_quantidade_vezes_preco_menos_desconto():
    assert precos.valor_final(3, 1190, 200) == 3 * (1190 - 200)


def test_rf10_desconto_fora_do_intervalo_recusado():
    with pytest.raises(ValueError):
        precos.valor_final(1, 1000, 1001)
    with pytest.raises(ValueError):
        precos.valor_final(1, 1000, -1)


def test_rf11_combo_soma_precos_e_descontos_de_cada_componente():
    assert precos.preco_combo([(2490, 0, 1), (1190, 200, 1), (690, 0, 2)]) == (2490 + 1190 + 1380, 200)


def test_rnf23_calculos_recusam_float():
    with pytest.raises(TypeError):
        precos.valor_final(1, 10.5, 0)
