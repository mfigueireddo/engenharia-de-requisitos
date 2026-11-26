"""Ponto de entrada da API do BurguerJá (FastAPI).

Aqui só se cria o app e se registram os routers; as rotas ficam em app/routers/.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .routers import acompanhamento, auth, carrinho, cupons, enderecos, pedidos, saude, unidades


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.inicializar()
    yield


app = FastAPI(title="BurguerJá API", lifespan=lifespan)

app.include_router(saude.router)
app.include_router(auth.router)
app.include_router(unidades.router)
app.include_router(carrinho.router)
app.include_router(cupons.router)
app.include_router(enderecos.router)
app.include_router(pedidos.router)
app.include_router(acompanhamento.router)
