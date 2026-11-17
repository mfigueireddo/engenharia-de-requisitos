# BurguerJá

Requisitos: **Python 3.11+** e **Node.js 20+**. Use dois terminais.

**1. API** (http://localhost:8000/docs)

```bash
cd backend
python -m venv .venv
# Linux/Mac:  source .venv/bin/activate
# Windows:    .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**2. Front-end** (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Testes da API: `cd backend && python -m pytest`

Contribuição: um branch por tarefa e merge na `main` só por pull request (ver [AGENTS.md](AGENTS.md), seção 6).

Estrutura do projeto: [ESTRUTURA.md](ESTRUTURA.md) · Requisitos: [docs/srs/srs-pt.md](docs/srs/srs-pt.md) · Uso de IA: [docs/ia/](docs/ia/README.md)
