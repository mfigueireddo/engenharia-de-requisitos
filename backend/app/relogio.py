"""Data e hora atuais, num só lugar para os testes poderem trocar (monkeypatch).

Datas/horas são guardadas no banco como texto ISO 8601 em UTC. `hoje()` dá a
data no horário de Brasília (UTC−3; o Brasil não tem horário de verão desde 2019).
"""

from datetime import date, datetime, timedelta, timezone

BRASILIA = timezone(timedelta(hours=-3))


def agora() -> datetime:
    """Agora, em UTC."""
    return datetime.now(timezone.utc)


def hoje() -> date:
    """Data atual no horário de Brasília."""
    return agora().astimezone(BRASILIA).date()


def para_texto(momento: datetime) -> str:
    return momento.astimezone(timezone.utc).isoformat(timespec="seconds")


def de_texto(texto: str) -> datetime:
    return datetime.fromisoformat(texto)
