"""Ponto de entrada da API do BurguerJá (FastAPI)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from . import db


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.inicializar()
    yield


app = FastAPI(title="BurguerJá API", lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# --- ESBOÇO-PROVISÓRIO: exemplo de integração; remover na 1ª funcionalidade real (AGENTS.md, seção 7) ---

class RecadoEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=200)


class Recado(BaseModel):
    id: int
    texto: str
    criado_em: str


@app.get("/api/recados", response_model=list[Recado])
def listar_recados():
    with db.conectar() as conn:
        linhas = conn.execute("SELECT id, texto, criado_em FROM recado ORDER BY id DESC").fetchall()
    return [dict(l) for l in linhas]


@app.post("/api/recados", response_model=Recado, status_code=201)
def criar_recado(entrada: RecadoEntrada):
    with db.conectar() as conn:
        cur = conn.execute("INSERT INTO recado (texto) VALUES (?)", (entrada.texto,))
        linha = conn.execute("SELECT id, texto, criado_em FROM recado WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(linha)
