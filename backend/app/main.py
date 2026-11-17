"""Ponto de entrada da API do BurguerJá (FastAPI).

Aqui só se cria o app e se registram os routers; as rotas ficam em app/routers/.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .routers import recados, saude


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.inicializar()
    yield


app = FastAPI(title="BurguerJá API", lifespan=lifespan)

app.include_router(saude.router)
app.include_router(recados.router)  # ESBOÇO-PROVISÓRIO (AGENTS.md, seção 7)
