"""Dados de demonstração para usar o front-end (infra mínima — sem UC na ERS).

Cria um cliente de teste com endereços nos CEPs da geocodificação simulada
(decisão Q8), para o checkout com entrega (UC28) funcionar antes do UC33
(Gerenciar Endereços Salvos), e com os cupons do wireframe 07 (UC30).

Não é rota da API: roda direto no banco local, só em desenvolvimento.
    cd backend && python -m scripts.dados_demo

É idempotente: rodar de novo não duplica nada.
"""

from app import db, relogio, seguranca

EMAIL = "demo@burguerja.com"
SENHA = "demo1234"
NOME = "Cliente Demo"

# CEPs presentes em app/integracoes/geocodificacao.py (CEPS_SIMULADOS).
ENDERECOS = [
    # Perto da unidade Gávea; fora do raio de 4 km da unidade Botafogo (UC28 E2).
    {"logradouro": "Rua Marquês de São Vicente", "numero": "225", "complemento": "PUC-Rio",
     "bairro": "Gávea", "cidade": "Rio de Janeiro", "estado": "RJ", "cep": "22451-900"},
    {"logradouro": "Rua Jardim Botânico", "numero": "1008", "complemento": None,
     "bairro": "Jardim Botânico", "cidade": "Rio de Janeiro", "estado": "RJ", "cep": "22470-050"},
]

# Cupons do wireframe 07 e do projeto relacional (UC30).
CUPONS = [
    {"codigo": "BEMVINDO10", "descricao": "10% off até R$ 10",
     "percentual_desconto_centesimos": 1000, "valor_maximo_desconto_centavos": 1000,
     "isenta_taxa_entrega": 0, "valor_minimo_pedido_centavos": 0,
     "validade_inicio": "2026-01-01", "validade_fim": "2027-12-31", "limite_usos": 1},
    {"codigo": "FRETEGRATIS", "descricao": "Entrega grátis em pedidos acima de R$ 50",
     "percentual_desconto_centesimos": 0, "valor_maximo_desconto_centavos": None,
     "isenta_taxa_entrega": 1, "valor_minimo_pedido_centavos": 5000,
     "validade_inicio": "2026-01-01", "validade_fim": "2027-12-31", "limite_usos": 3},
    {"codigo": "PROMO5", "descricao": "5% off em qualquer pedido",
     "percentual_desconto_centesimos": 500, "valor_maximo_desconto_centavos": None,
     "isenta_taxa_entrega": 0, "valor_minimo_pedido_centavos": 0,
     "validade_inicio": "2026-01-01", "validade_fim": "2026-09-15", "limite_usos": 1},
]


def criar() -> None:
    db.inicializar()
    with db.conectar() as conn:
        linha = conn.execute("SELECT id FROM cliente WHERE email = ?", (EMAIL,)).fetchone()
        if linha is None:
            cur = conn.execute(
                "INSERT INTO cliente (nome, email, senha_hash, termos_aceitos_em) VALUES (?, ?, ?, ?)",
                (NOME, EMAIL, seguranca.gerar_hash_senha(SENHA), relogio.para_texto(relogio.agora())),
            )
            cliente_id = cur.lastrowid
        else:
            cliente_id = linha["id"]
        for e in ENDERECOS:
            existe = conn.execute("SELECT 1 FROM endereco_cliente WHERE cliente_id = ? AND cep = ? AND numero = ?",
                                  (cliente_id, e["cep"], e["numero"])).fetchone()
            if not existe:
                conn.execute(
                    "INSERT INTO endereco_cliente (cliente_id, logradouro, numero, complemento, bairro, cidade, estado, cep) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (cliente_id, e["logradouro"], e["numero"], e["complemento"], e["bairro"],
                     e["cidade"], e["estado"], e["cep"]),
                )
        for c in CUPONS:
            existe = conn.execute("SELECT 1 FROM cupom_promocional WHERE cliente_id = ? AND codigo = ?",
                                  (cliente_id, c["codigo"])).fetchone()
            if not existe:
                conn.execute(
                    """INSERT INTO cupom_promocional (
                           cliente_id, codigo, descricao, percentual_desconto_centesimos,
                           valor_maximo_desconto_centavos, isenta_taxa_entrega,
                           valor_minimo_pedido_centavos, validade_inicio, validade_fim, limite_usos
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (cliente_id, c["codigo"], c["descricao"], c["percentual_desconto_centesimos"],
                     c["valor_maximo_desconto_centavos"], c["isenta_taxa_entrega"],
                     c["valor_minimo_pedido_centavos"], c["validade_inicio"], c["validade_fim"],
                     c["limite_usos"]),
                )
    print(f"Cliente de demonstração pronto: {EMAIL} / senha {SENHA} ({len(ENDERECOS)} endereços, {len(CUPONS)} cupons).")


if __name__ == "__main__":
    criar()
