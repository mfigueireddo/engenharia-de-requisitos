"""Base de testes compartilhada (infra mínima — sem UC na ERS; só desenvolvimento).

Apaga o banco local e o recria sempre com os mesmos dados, para que todo o grupo
teste a partir da mesma base. O que fica no git é este script, não o arquivo
.db: um banco commitado ficaria velho a cada mudança do schema.sql (o app recusa
banco de esquema antigo) e daria conflito binário no merge.

    cd backend && python -m scripts.base_compartilhada
    (ou: bash scripts/rodar.sh --resetar-banco)

Os dados entram pela própria API (cadastro, carrinho, prévia e confirmação do
pedido), então passam pelas mesmas regras de negócio do app. Só os endereços
são gravados direto no banco, porque o cadastro de endereços pela API é o UC33.

Clientes (todos com a senha demo1234):
- demo@burguerja.com  — o cliente de scripts/dados_demo.py (endereços da PUC e do Jardim Botânico).
- ana@burguerja.com   — sacola pronta na Gávea, para testar o UC29 e o UC28 direto.
- bruno@burguerja.com — dois pedidos já feitos (entrega na Gávea e retirada na
                        Botafogo) e um endereço perto da Botafogo.
- carla@burguerja.com — conta nova: sem endereço, sem sacola, sem pedido.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import db
from app.routers import auth, carrinho, enderecos, pedidos, unidades

from . import dados_demo

SENHA = dados_demo.SENHA

CLIENTES = [
    {"nome": "Ana Souza", "email": "ana@burguerja.com"},
    {"nome": "Bruno Lima", "email": "bruno@burguerja.com"},
    {"nome": "Carla Dias", "email": "carla@burguerja.com"},
]

# CEPs presentes em app/integracoes/geocodificacao.py (CEPS_SIMULADOS).
ENDERECOS = {
    "ana@burguerja.com": [
        {"logradouro": "Rua Marquês de São Vicente", "numero": "225", "complemento": "PUC-Rio, prédio Kennedy",
         "bairro": "Gávea", "cidade": "Rio de Janeiro", "estado": "RJ", "cep": "22451-900"},
    ],
    "bruno@burguerja.com": [
        {"logradouro": "Rua Jardim Botânico", "numero": "500", "complemento": "apto 101",
         "bairro": "Jardim Botânico", "cidade": "Rio de Janeiro", "estado": "RJ", "cep": "22470-050"},
        {"logradouro": "Praia de Botafogo", "numero": "300", "complemento": None,
         "bairro": "Botafogo", "cidade": "Rio de Janeiro", "estado": "RJ", "cep": "22250-040"},
    ],
}

# (e-mail, unidade, [(produto, quantidade, observação)])
SACOLAS = [
    ("ana@burguerja.com", "BurguerJá Gávea", [
        ("Burguer Clássico", 2, "sem cebola"),
        ("Batata frita média", 1, None),
        ("Combo Clássico", 1, None),
    ]),
]

# (e-mail, unidade, itens, atendimento, CEP do endereço de entrega ou None)
PEDIDOS = [
    ("bruno@burguerja.com", "BurguerJá Gávea",
     [("Combo Clássico", 2, None), ("Refrigerante lata", 1, "bem gelado")], "ENTREGA", "22470-050"),
    ("bruno@burguerja.com", "BurguerJá Botafogo",
     [("Duplo Cheddar", 1, "sem cebola caramelizada")], "RETIRADA", None),
]


def _api() -> FastAPI:
    """A API com as rotas usadas aqui, montada sem depender de app/main.py."""
    api = FastAPI()
    for modulo in (auth, unidades, carrinho, enderecos, pedidos):
        api.include_router(modulo.router)
    return api


def _ok(resposta, esperado: int = 200):
    if resposta.status_code != esperado:
        raise RuntimeError(f"{resposta.request.method} {resposta.request.url.path}: "
                           f"{resposta.status_code} {resposta.text}")
    return resposta.json() if resposta.content else None


def _apagar_banco() -> None:
    caminho = db.caminho_banco()
    for arquivo in (caminho, caminho.with_name(caminho.name + "-wal"), caminho.with_name(caminho.name + "-shm")):
        arquivo.unlink(missing_ok=True)


def _entrar(c: TestClient, email: str) -> dict:
    token = _ok(c.post("/api/auth/login", json={"email": email, "senha": SENHA}))["token"]
    return {"Authorization": f"Bearer {token}"}


def _encher_sacola(c: TestClient, cabecalho: dict, unidades_por_nome: dict, unidade: str, itens) -> None:
    unidade_id = unidades_por_nome[unidade]
    cardapio = _ok(c.get(f"/api/unidades/{unidade_id}/cardapio"))
    produtos = {p["nome"]: p["id"] for p in cardapio["produtos"]}
    for nome, quantidade, observacao in itens:
        _ok(c.post("/api/carrinho/itens", headers=cabecalho, json={
            "unidade_id": unidade_id, "produto_id": produtos[nome],
            "quantidade": quantidade, "observacao": observacao}), 201)


def recriar() -> None:
    _apagar_banco()
    db.inicializar()
    dados_demo.criar()

    with TestClient(_api()) as c:
        for cliente in CLIENTES:
            _ok(c.post("/api/auth/cadastro", json={**cliente, "senha": SENHA, "aceite_termos": True}), 201)

        with db.conectar() as conn:
            for email, lista in ENDERECOS.items():
                cliente_id = conn.execute("SELECT id FROM cliente WHERE email = ?", (email,)).fetchone()["id"]
                for e in lista:
                    conn.execute(
                        "INSERT INTO endereco_cliente (cliente_id, logradouro, numero, complemento, bairro, "
                        "cidade, estado, cep) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (cliente_id, e["logradouro"], e["numero"], e["complemento"], e["bairro"],
                         e["cidade"], e["estado"], e["cep"]))

        unidades_por_nome = {u["nome"]: u["id"] for u in _ok(c.get("/api/unidades"))}

        for email, unidade, itens, atendimento, cep in PEDIDOS:
            cabecalho = _entrar(c, email)
            _encher_sacola(c, cabecalho, unidades_por_nome, unidade, itens)
            escolha = {"tipo_atendimento": atendimento, "endereco_id": None}
            if cep:
                escolha["endereco_id"] = next(e["id"] for e in _ok(c.get("/api/enderecos", headers=cabecalho))
                                              if e["cep"] == cep)
            previa = _ok(c.post("/api/pedidos/previa", headers=cabecalho, json=escolha))
            _ok(c.post("/api/pedidos", headers=cabecalho,
                       json={**escolha, "total_centavos": previa["total_centavos"]}), 201)

        for email, unidade, itens in SACOLAS:
            _encher_sacola(c, _entrar(c, email), unidades_por_nome, unidade, itens)

    with db.conectar() as conn:
        conn.execute("DELETE FROM sessao")  # a base começa sem ninguém logado

    print(f"Base compartilhada recriada em {db.caminho_banco()}")
    print(f"Clientes (senha {SENHA}): {dados_demo.EMAIL}, " + ", ".join(c["email"] for c in CLIENTES))


if __name__ == "__main__":
    recriar()
