"""Senhas, tokens de sessão e a dependência `cliente_atual` (infra mínima — sem UC na ERS).

- RNF-09: senha guardada só como hash bcrypt (com salt); toda rota da Seção 4
  exige cliente logado.
- Decisão Q6: sessão por token opaco. O cliente recebe o token; o banco guarda
  só o hash SHA-256 dele, com data de expiração.
- RNF-13 / RN-02: `cliente_atual` devolve o cliente dono do token; cada rota usa
  o id dele para filtrar os dados.
"""

import hashlib
import secrets
import sqlite3
from datetime import timedelta

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import db, relogio

RODADAS_BCRYPT = 12  # custo padrão do bcrypt; os testes baixam para ficarem rápidos
DURACAO_SESSAO = timedelta(days=7)  # a ERS não define; decisão técnica registrada no log

_bearer = HTTPBearer(auto_error=False)


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(RODADAS_BCRYPT)).decode("ascii")


def senha_confere(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("ascii"))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def criar_sessao(conn: sqlite3.Connection, cliente_id: int) -> tuple[str, str]:
    """Cria uma sessão e devolve (token, expira_em). O token só existe nesta resposta."""
    token = secrets.token_urlsafe(32)
    agora = relogio.agora()
    expira_em = relogio.para_texto(agora + DURACAO_SESSAO)
    conn.execute(
        "INSERT INTO sessao (token_hash, cliente_id, criado_em, expira_em) VALUES (?, ?, ?, ?)",
        (_hash_token(token), cliente_id, relogio.para_texto(agora), expira_em),
    )
    return token, expira_em


def encerrar_sessao(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessao WHERE token_hash = ?", (_hash_token(token),))


def cliente_por_token(conn: sqlite3.Connection, token: str | None) -> sqlite3.Row | None:
    """Resolve um token para o cliente; usado pelo handshake do WebSocket."""
    if not token:
        return None
    linha = conn.execute(
        """SELECT c.id, c.nome, c.email, s.expira_em
             FROM sessao s JOIN cliente c ON c.id = s.cliente_id
            WHERE s.token_hash = ?""",
        (_hash_token(token),),
    ).fetchone()
    if linha is None or relogio.de_texto(linha["expira_em"]) <= relogio.agora():
        return None
    return linha


def conexao():
    """Dependência FastAPI: uma conexão por requisição, com commit no fim."""
    conn = db.conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def token_atual(credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> str:
    if credenciais is None:
        raise HTTPException(401, "É preciso entrar na conta (RNF-09, RN-01).",
                            headers={"WWW-Authenticate": "Bearer"})
    return credenciais.credentials


def cliente_atual(
    token: str = Depends(token_atual),
    conn: sqlite3.Connection = Depends(conexao),
) -> sqlite3.Row:
    """Cliente logado (RNF-09, RNF-13, RN-01). 401 se o token não vale ou expirou."""
    linha = cliente_por_token(conn, token)
    if linha is None:
        raise HTTPException(401, "Sessão inválida ou expirada. Entre novamente.",
                            headers={"WWW-Authenticate": "Bearer"})
    return linha
