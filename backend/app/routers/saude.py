"""Verificação de que a API está no ar (infraestrutura, sem UC na ERS)."""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["saúde"])


@router.get("/health")
def health():
    return {"status": "ok"}
