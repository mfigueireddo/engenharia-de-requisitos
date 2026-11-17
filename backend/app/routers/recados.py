"""ESBOÇO-PROVISÓRIO: exemplo de integração banco → API → front-end.

Não faz parte do produto. Remover este arquivo (e o include_router em main.py)
no PR da primeira funcionalidade real que chegue ao front-end (AGENTS.md, seção 7).
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import db

router = APIRouter(prefix="/api/recados", tags=["esboço provisório"])


class RecadoEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=200)


class Recado(BaseModel):
    id: int
    texto: str
    criado_em: str


@router.get("", response_model=list[Recado])
def listar_recados():
    with db.conectar() as conn:
        linhas = conn.execute("SELECT id, texto, criado_em FROM recado ORDER BY id DESC").fetchall()
    return [dict(l) for l in linhas]


@router.post("", response_model=Recado, status_code=201)
def criar_recado(entrada: RecadoEntrada):
    with db.conectar() as conn:
        cur = conn.execute("INSERT INTO recado (texto) VALUES (?)", (entrada.texto,))
        linha = conn.execute("SELECT id, texto, criado_em FROM recado WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(linha)
