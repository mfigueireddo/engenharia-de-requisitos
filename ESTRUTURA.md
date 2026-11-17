# Estrutura do projeto

Mapa das pastas e arquivos e as regras de organização. **Mantenha este arquivo
atualizado**: toda pasta nova, arquivo importante ou regra de organização nova
entra aqui no mesmo commit.

## Árvore

```
.
├── AGENTS.md                 Regras para agentes de IA (fonte única)
├── CLAUDE.md                 Importa AGENTS.md + regras só do Claude Code
├── ESTRUTURA.md              Este arquivo
├── README.md                 Como rodar (mínimo)
├── srs-pt.docx               ERS original (fonte de verdade)
├── .github/
│   └── pull_request_template.md  Modelo de descrição de PR
├── backend/                  API — Python + FastAPI + SQLite
│   ├── requirements.txt      Dependências Python (versões fixas)
│   ├── app/
│   │   ├── main.py           Cria o app FastAPI e declara as rotas
│   │   ├── db.py             Conexão com o SQLite e inicialização do esquema
│   │   └── schema.sql        DDL do banco (CREATE TABLE ...)
│   └── tests/
│       └── test_api.py       Testes da API (pytest + TestClient)
├── frontend/                 Interface — TypeScript + React (Vite)
│   ├── package.json
│   ├── vite.config.ts        Porta 5173 e proxy de /api para a API (porta 8000)
│   ├── index.html
│   └── src/
│       ├── main.tsx          Monta o React
│       ├── App.tsx           Página atual (teste de integração)
│       ├── api.ts            Cliente da API REST (todo fetch passa por aqui)
│       └── index.css         Estilos globais
├── docs/
│   ├── srs/                  ERS em Markdown (srs-pt.md) + figuras (media/)
│   ├── apresentacoes/        Resumos para o professor (AAAA-MM-DD_<tema>.md)
│   └── ia/                   Registro do uso de IA (ver docs/ia/README.md)
├── scripts/ia/autor.sh       Nome do git → identificador usado em docs/ia/
└── .claude/                  Configuração e hooks do Claude Code
```

## Regras de organização

1. **Back-end só em `backend/`, front-end só em `frontend/`.** O front-end nunca
   acessa o banco; tudo passa pela API REST (ERS 2.5, 3.3).
2. **Rotas da API começam com `/api/`.** O proxy do Vite depende disso.
3. **Esquema do banco em `backend/app/schema.sql`.** Tabelas, restrições e
   triggers ficam nesse arquivo (ou em arquivos `.sql` ao lado, se crescer).
4. **Chamadas HTTP do front-end só em `frontend/src/api.ts`** (ou em `src/api/`
   quando crescer). Componentes não chamam `fetch` diretamente.
5. **Todo endpoint novo ganha teste** em `backend/tests/`.
6. **Arquivos gerados não entram no git:** `.venv/`, `node_modules/`, `dist/`, `*.db`.
7. **A tabela `recado`, as rotas `/api/recados` e a página de `App.tsx` são só
   um teste de integração** (marcados com `ESBOÇO-PROVISÓRIO`). Remova-os no PR
   da primeira funcionalidade real; a lista completa está no `AGENTS.md`, seção 7.
8. **Nada vai direto para a `main`.** Cada tarefa num branch `<autor>/<tema>` e
   merge por pull request revisado por outro integrante (`AGENTS.md`, seção 6).

## Crescimento previsto (sugestão, não obrigatório)

Quando o código crescer, a ideia é separar por funcionalidade da ERS:
`backend/app/routers/<funcionalidade>.py` (ex.: `carrinho.py`, `pedidos.py`) e
`frontend/src/pages/<Tela>.tsx` + `frontend/src/components/`. Ao fazer isso,
atualize a árvore e as regras acima.
