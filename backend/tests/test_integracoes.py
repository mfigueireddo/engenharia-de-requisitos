"""RNF-19: chamadas aos sistemas externos (simulados) têm tempo limite e
tratamento de erro, testados com falhas simuladas.

A geocodificação segue a mesma regra por decisão do grupo (Q8).
"""

import threading

import pytest

from app.integracoes import base, geocodificacao, sgl
from app.integracoes.base import IntegracaoIndisponivel
from app.integracoes.geocodificacao import Coordenadas


@pytest.fixture
def lento():
    """Transporte que só responde quando o teste libera, simulando um sistema travado."""
    liberar = threading.Event()

    def transporte(_):
        liberar.wait(5)
        return {"itens": []}

    yield transporte
    liberar.set()  # solta a thread presa para não sobrar nada rodando


def _quebrado(_):
    raise ConnectionError("conexão recusada")


# --- base -------------------------------------------------------------------

def test_rnf19_tempo_limite_padrao_e_configuravel(monkeypatch):
    monkeypatch.delenv(base.VARIAVEL_TEMPO_LIMITE, raising=False)
    assert base.tempo_limite_padrao() == 3.0
    monkeypatch.setenv(base.VARIAVEL_TEMPO_LIMITE, "0.5")
    assert base.tempo_limite_padrao() == 0.5


@pytest.mark.parametrize("valor", ["abc", "0", "-1"])
def test_rnf19_tempo_limite_invalido_e_recusado(monkeypatch, valor):
    monkeypatch.setenv(base.VARIAVEL_TEMPO_LIMITE, valor)
    with pytest.raises(ValueError):
        base.tempo_limite_padrao()


# --- SGL --------------------------------------------------------------------

def test_sgl_obter_cardapio_simulado():
    cardapio = sgl.obter_cardapio("UN-GAVEA")
    assert {i["id_sgl"] for i in cardapio["itens"]} >= {"LAN-01", "COM-01"}
    for item in cardapio["itens"]:
        if item["tipo"] == "SIMPLES":  # RNF-23: preços em centavos inteiros
            assert isinstance(item["preco_centavos"], int)
            assert 0 <= item["desconto_centavos"] <= item["preco_centavos"]  # RF-10


def test_rnf19_sgl_tempo_limite_estourado(lento):
    with pytest.raises(IntegracaoIndisponivel, match="sem resposta") as erro:
        sgl.obter_cardapio("UN-GAVEA", transporte=lento, tempo_limite=0.05)
    assert erro.value.sistema == "SGL"


def test_rnf19_sgl_erro_de_conexao():
    with pytest.raises(IntegracaoIndisponivel, match="ConnectionError"):
        sgl.obter_cardapio("UN-GAVEA", transporte=_quebrado)


@pytest.mark.parametrize("resposta", [None, [], {"sem": "itens"}, {"itens": "x"}])
def test_rnf19_sgl_resposta_invalida(resposta):
    with pytest.raises(IntegracaoIndisponivel, match="formato inesperado"):
        sgl.obter_cardapio("UN-GAVEA", transporte=lambda _: resposta)


def test_rnf19_sgl_unidade_desconhecida_vira_erro_tratado():
    with pytest.raises(IntegracaoIndisponivel):
        sgl.obter_cardapio("UN-INEXISTENTE")


# --- Geocodificação (decisão Q8) --------------------------------------------

def test_q8_geocodificar_cep_conhecido_com_ou_sem_hifen():
    esperado = geocodificacao.CEPS_SIMULADOS["22451900"]
    assert geocodificacao.geocodificar("22451-900") == esperado
    assert geocodificacao.geocodificar("22451900") == esperado


def test_q8_cep_desconhecido_nao_serve_para_entrega():
    assert geocodificacao.geocodificar("01001-000") is None


@pytest.mark.parametrize("cep", ["", "1234", "22451-90a", "224519000"])
def test_q8_cep_mal_formado(cep):
    with pytest.raises(ValueError):
        geocodificacao.geocodificar(cep)


def test_rnf19_q8_geocodificacao_tempo_limite_estourado(lento):
    with pytest.raises(IntegracaoIndisponivel, match="sem resposta") as erro:
        geocodificacao.geocodificar("22451-900", transporte=lento, tempo_limite=0.05)
    assert erro.value.sistema == "Geocodificação"


def test_rnf19_q8_geocodificacao_erro_de_conexao():
    with pytest.raises(IntegracaoIndisponivel):
        geocodificacao.geocodificar("22451-900", transporte=_quebrado)


def test_rnf19_q8_geocodificacao_resposta_invalida():
    with pytest.raises(IntegracaoIndisponivel, match="formato inesperado"):
        geocodificacao.geocodificar("22451-900", transporte=lambda _: (-22.9, -43.2))


def test_q8_coordenadas_simuladas_validas():
    for c in geocodificacao.CEPS_SIMULADOS.values():
        assert isinstance(c, Coordenadas)
        assert -90 <= c.latitude <= 90 and -180 <= c.longitude <= 180
