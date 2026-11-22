from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app import enderecos as repo

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

class EnderecoIn(BaseModel):
    cep: str = ""
    rua: str = ""
    numero: str = ""
    complemento: Optional[str] = ""
    bairro: str = ""
    cidade: str = ""

@app.get("/enderecos")
def listar_enderecos(): return repo.listar()

@app.post("/enderecos", status_code=201)
def criar_endereco(dados: EnderecoIn):
    try: return repo.criar(dados.model_dump())
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))

@app.put("/enderecos/{endereco_id}")
def editar_endereco(endereco_id: int, dados: EnderecoIn):
    try: return repo.editar(endereco_id, dados.model_dump())
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))
    except LookupError as e: raise HTTPException(status_code=404, detail=str(e))

@app.delete("/enderecos/{endereco_id}", status_code=204)
def remover_endereco(endereco_id: int):
    try: repo.remover(endereco_id)
    except LookupError as e: raise HTTPException(status_code=404, detail=str(e))
    return None
