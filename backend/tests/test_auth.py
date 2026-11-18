"""Cadastro, login e sessão — infra mínima, sem UC na ERS (decisão Q1).

Regras testadas: RNF-09, RNF-10, RNF-13, RNF-25, RN-01 e a mensagem da Seção 3.1.
"""

CADASTRO = {"nome": "Ana", "email": "ana@exemplo.com", "senha": "segredo123", "aceite_termos": True}


def _login(client, senha="segredo123", email="ana@exemplo.com"):
    return client.post("/api/auth/login", json={"email": email, "senha": senha})


def test_cadastro_cria_conta(client):
    r = client.post("/api/auth/cadastro", json=CADASTRO)
    assert r.status_code == 201
    assert r.json()["email"] == "ana@exemplo.com"
    assert "senha" not in r.json() and "senha_hash" not in r.json()


def test_rnf25_cadastro_exige_aceite_dos_termos(client):
    r = client.post("/api/auth/cadastro", json={**CADASTRO, "aceite_termos": False})
    assert r.status_code == 422
    assert client.post("/api/auth/cadastro", json={k: v for k, v in CADASTRO.items() if k != "aceite_termos"}).status_code == 422


def test_rnf25_aceite_dos_termos_fica_registrado(client, banco):
    client.post("/api/auth/cadastro", json=CADASTRO)
    assert banco.execute("SELECT termos_aceitos_em FROM cliente").fetchone()[0]


def test_cadastro_recusa_email_repetido_mesmo_com_maiusculas(client):
    client.post("/api/auth/cadastro", json=CADASTRO)
    assert client.post("/api/auth/cadastro", json={**CADASTRO, "email": "ANA@exemplo.com"}).status_code == 409


def test_cadastro_valida_campos(client):
    assert client.post("/api/auth/cadastro", json={**CADASTRO, "email": "sem-arroba"}).status_code == 422
    assert client.post("/api/auth/cadastro", json={**CADASTRO, "nome": "   "}).status_code == 422
    assert client.post("/api/auth/cadastro", json={**CADASTRO, "senha": ""}).status_code == 422


def test_rnf09_senha_guardada_so_como_hash_bcrypt(client, banco):
    client.post("/api/auth/cadastro", json=CADASTRO)
    senha_hash = banco.execute("SELECT senha_hash FROM cliente").fetchone()[0]
    assert senha_hash != "segredo123" and senha_hash.startswith("$2")


def test_login_e_dados_do_cliente(client):
    client.post("/api/auth/cadastro", json=CADASTRO)
    r = _login(client)
    assert r.status_code == 200
    me = client.get("/api/clientes/me", headers={"Authorization": f"Bearer {r.json()['token']}"})
    assert me.status_code == 200 and me.json()["nome"] == "Ana"


def test_rnf09_token_nao_fica_em_texto_puro_no_banco(client, banco):
    client.post("/api/auth/cadastro", json=CADASTRO)
    token = _login(client).json()["token"]
    assert banco.execute("SELECT COUNT(*) FROM sessao WHERE token_hash = ?", (token,)).fetchone()[0] == 0


def test_secao_3_1_mensagem_unica_para_senha_errada_e_email_inexistente(client):
    client.post("/api/auth/cadastro", json=CADASTRO)
    errada = _login(client, senha="errada")
    inexistente = _login(client, email="ninguem@exemplo.com")
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json()["detail"] == inexistente.json()["detail"] == "E-mail ou senha inválidos"


def test_rnf10_bloqueio_de_15_minutos_apos_5_tentativas_erradas(client, relogio):
    client.post("/api/auth/cadastro", json=CADASTRO)
    for _ in range(5):
        assert _login(client, senha="errada").status_code == 401
    assert _login(client).status_code == 429  # bloqueada, mesmo com a senha certa
    relogio.avancar(minutes=14, seconds=59)
    assert _login(client).status_code == 429
    relogio.avancar(seconds=1)
    assert _login(client).status_code == 200


def test_rnf10_login_certo_zera_a_contagem_de_erros(client):
    client.post("/api/auth/cadastro", json=CADASTRO)
    for _ in range(4):
        _login(client, senha="errada")
    assert _login(client).status_code == 200
    for _ in range(4):
        _login(client, senha="errada")
    assert _login(client).status_code == 200


def test_rn01_rotas_protegidas_exigem_login(client):
    assert client.get("/api/clientes/me").status_code == 401
    assert client.get("/api/clientes/me", headers={"Authorization": "Bearer inventado"}).status_code == 401
    assert client.get("/api/carrinho").status_code == 401


def test_logout_invalida_o_token(client, ana):
    assert client.post("/api/auth/logout", headers=ana).status_code == 204
    assert client.get("/api/clientes/me", headers=ana).status_code == 401


def test_sessao_expira(client, relogio, ana):
    relogio.avancar(days=7)
    assert client.get("/api/clientes/me", headers=ana).status_code == 401
