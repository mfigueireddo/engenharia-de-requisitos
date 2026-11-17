from fastapi.testclient import TestClient


def test_health_e_recados(tmp_path, monkeypatch):
    from app import db
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "teste.db")
    from app.main import app

    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        assert client.post("/api/recados", json={"texto": "oi"}).status_code == 201
        assert client.get("/api/recados").json()[0]["texto"] == "oi"
        assert client.post("/api/recados", json={"texto": ""}).status_code == 422
