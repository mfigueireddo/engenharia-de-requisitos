"""Cadastro, login, logout e dados do cliente logado.

Infra mínima — sem UC na ERS (decisão Q1): a ERS exige conta e login
(2.2, RN-01, RNF-09) mas não descreve esses fluxos. Só as regras escritas na ERS
foram implementadas: hash bcrypt (RNF-09), bloqueio de 15 min após 5 erros
(RNF-10), aceite dos termos (RNF-08, RNF-25) e a mensagem "E-mail ou senha
inválidos" (Seção 3.1). "Esqueci minha senha" está fora do escopo (decisão Q7).
"""

import sqlite3
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator

from .. import relogio, seguranca

router = APIRouter(tags=["autenticação (infra mínima)"])

MAX_TENTATIVAS = 5                      # RNF-10
TEMPO_BLOQUEIO = timedelta(minutes=15)  # RNF-10
MSG_LOGIN_INVALIDO = "E-mail ou senha inválidos"  # ERS 3.1


class CadastroEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    senha: str = Field(min_length=1, max_length=72)  # bcrypt usa no máximo 72 bytes
    aceite_termos: bool  # RNF-08, RNF-25

    @field_validator("nome")
    @classmethod
    def _nome(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("informe o nome")
        return v.strip()

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        usuario, arroba, dominio = v.partition("@")
        if not arroba or not usuario or "." not in dominio or " " in v:
            raise ValueError("e-mail inválido")
        return v


class LoginEntrada(BaseModel):
    email: str
    senha: str


class Cliente(BaseModel):
    id: int
    nome: str
    email: str


class Sessao(BaseModel):
    token: str
    expira_em: str
    cliente: Cliente


@router.post("/api/auth/cadastro", response_model=Cliente, status_code=201)
def cadastrar(entrada: CadastroEntrada, conn: sqlite3.Connection = Depends(seguranca.conexao)):
    if not entrada.aceite_termos:
        raise HTTPException(422, "É preciso aceitar os termos de uso e a política de privacidade (RNF-25).")
    if conn.execute("SELECT 1 FROM cliente WHERE email = ?", (entrada.email,)).fetchone():
        raise HTTPException(409, "Já existe uma conta com este e-mail.")
    cur = conn.execute(
        "INSERT INTO cliente (nome, email, senha_hash, termos_aceitos_em) VALUES (?, ?, ?, ?)",
        (entrada.nome, entrada.email, seguranca.gerar_hash_senha(entrada.senha),
         relogio.para_texto(relogio.agora())),
    )
    return {"id": cur.lastrowid, "nome": entrada.nome, "email": entrada.email}


@router.post("/api/auth/login", response_model=Sessao)
def entrar(entrada: LoginEntrada, conn: sqlite3.Connection = Depends(seguranca.conexao)):
    cliente = conn.execute(
        "SELECT id, nome, email, senha_hash, tentativas_login_falhas, bloqueado_ate "
        "FROM cliente WHERE email = ?",
        (entrada.email.strip().lower(),),
    ).fetchone()
    if cliente is None:
        raise HTTPException(401, MSG_LOGIN_INVALIDO)

    agora = relogio.agora()
    if cliente["bloqueado_ate"] and relogio.de_texto(cliente["bloqueado_ate"]) > agora:
        raise HTTPException(429, "Muitas tentativas erradas. Tente de novo em 15 minutos (RNF-10).")

    if not seguranca.senha_confere(entrada.senha, cliente["senha_hash"]):
        tentativas = cliente["tentativas_login_falhas"] + 1
        if tentativas >= MAX_TENTATIVAS:  # RNF-10: 5ª tentativa errada bloqueia por 15 min
            conn.execute(
                "UPDATE cliente SET tentativas_login_falhas = 0, bloqueado_ate = ? WHERE id = ?",
                (relogio.para_texto(agora + TEMPO_BLOQUEIO), cliente["id"]),
            )
        else:
            conn.execute("UPDATE cliente SET tentativas_login_falhas = ? WHERE id = ?",
                         (tentativas, cliente["id"]))
        conn.commit()  # a exceção abaixo faria rollback da contagem
        raise HTTPException(401, MSG_LOGIN_INVALIDO)

    conn.execute("UPDATE cliente SET tentativas_login_falhas = 0, bloqueado_ate = NULL WHERE id = ?",
                 (cliente["id"],))
    token, expira_em = seguranca.criar_sessao(conn, cliente["id"])
    return {"token": token, "expira_em": expira_em,
            "cliente": {"id": cliente["id"], "nome": cliente["nome"], "email": cliente["email"]}}


@router.post("/api/auth/logout", status_code=204)
def sair(
    _cliente=Depends(seguranca.cliente_atual),
    token: str = Depends(seguranca.token_atual),
    conn: sqlite3.Connection = Depends(seguranca.conexao),
):
    seguranca.encerrar_sessao(conn, token)
    return Response(status_code=204)


@router.get("/api/clientes/me", response_model=Cliente)
def meus_dados(cliente=Depends(seguranca.cliente_atual)):
    return {"id": cliente["id"], "nome": cliente["nome"], "email": cliente["email"]}
