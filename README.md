# BurguerJá

Requisitos: **Python 3.11+** e **Node.js 20+**.

## Jeito rápido

```bash
bash scripts/rodar.sh
```

Instala o que faltar e sobe a API (http://localhost:8000/docs) e o app
(http://localhost:5173) no mesmo terminal. Ctrl+C para os dois. No Windows, use o Git Bash.

Opções: `--resetar-banco` (volta para a base compartilhada), `--banco-vazio`,
`--testes` (roda `pytest` e o build e sai), `--ajuda`.

## Base de testes compartilhada

Na primeira vez (ou com `--resetar-banco`) o banco local é recriado com a mesma
base para todo o grupo ([backend/scripts/base_compartilhada.py](backend/scripts/base_compartilhada.py)).
Senha de todos: `demo1234`.

| Login | Para testar |
|---|---|
| `demo@burguerja.com` | Cliente básico com 2 endereços (PUC e Jardim Botânico) e 3 cupons |
| `ana@burguerja.com` | Sacola pronta na Gávea e cupons (UC29, UC30 e UC28 direto) |
| `bruno@burguerja.com` | 2 pedidos já feitos, endereço perto da Botafogo e cupons |
| `carla@burguerja.com` | Conta nova: sem endereço, sacola, pedido ou cupom |

## Passo a passo (dois terminais)

**1. API** (http://localhost:8000/docs)

```bash
cd backend
python -m venv .venv
# Linux/Mac:  source .venv/bin/activate
# Windows:    .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Dados de demonstração (opcional): `cd backend && python -m scripts.dados_demo` cria o
cliente `demo@burguerja.com` / senha `demo1234`, com endereços para testar a entrega
(o cadastro de endereços pelo app vem com o UC33).

**2. Front-end** (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Se a API recusar o banco por ser de um esquema antigo, apague `backend/burguerja.db` (ele é recriado vazio).

Testes da API: `cd backend && python -m pytest`

Contribuição: um branch por tarefa e merge na `main` só por pull request (ver [AGENTS.md](AGENTS.md), seção 6).

Estrutura do projeto: [ESTRUTURA.md](ESTRUTURA.md) · Requisitos: [docs/srs/srs-pt.md](docs/srs/srs-pt.md) · Uso de IA: [docs/ia/](docs/ia/README.md)
