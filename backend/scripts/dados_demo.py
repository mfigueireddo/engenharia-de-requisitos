"""Dados de demonstração para usar o front-end (infra mínima — sem UC na ERS).

Cria um cliente de teste com endereços nos CEPs da geocodificação simulada
(decisão Q8), para o checkout com entrega (UC28) funcionar antes do UC33
(Gerenciar Endereços Salvos), que é quem vai cadastrar endereços pela API.

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
    print(f"Cliente de demonstração pronto: {EMAIL} / senha {SENHA} ({len(ENDERECOS)} endereços).")


if __name__ == "__main__":
    criar()
