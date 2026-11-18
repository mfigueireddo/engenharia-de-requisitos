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
│   │   ├── main.py           Cria o app FastAPI e registra os routers
│   │   ├── db.py             Conexão com o SQLite (arquivo em BURGUERJA_DB) e esquema
│   │   ├── schema.sql        DDL do banco (CREATE TABLE ...)
│   │   ├── dinheiro.py       Valores em centavos inteiros, sem float (RNF-23)
│   │   ├── relogio.py        Data/hora atual (os testes trocam por monkeypatch)
│   │   ├── seguranca.py      bcrypt, token de sessão, conexão por requisição e cliente_atual (RNF-09, RNF-13)
│   │   ├── routers/          Rotas da API, um arquivo por funcionalidade
│   │   │   ├── saude.py      /api/health
│   │   │   ├── auth.py       /api/auth/*, /api/clientes/me — infra mínima (Q1)
│   │   │   ├── unidades.py   /api/unidades e cardápio — públicas, infra mínima (Q1, Q2)
│   │   │   ├── carrinho.py   /api/carrinho — UC29 (+ adicionar/esvaziar, infra mínima)
│   │   │   ├── enderecos.py  GET /api/enderecos — só listagem, usada pelo UC28 (CRUD = UC33)
│   │   │   ├── pedidos.py    /api/pedidos/previa e /api/pedidos — UC28
│   │   │   └── recados.py    ESBOÇO-PROVISÓRIO (/api/recados)
│   │   ├── servicos/         Regras de negócio (cálculos e validações), sem HTTP
│   │   │   ├── precos.py     RF-02, RF-11
│   │   │   ├── cardapio.py   Cache do cardápio do SGL (RF-10, RF-13, RNF-03, RNF-22)
│   │   │   ├── carrinho.py   Carrinho recalculado (UC29, E1–E3)
│   │   │   └── checkout.py   UC28: distância, taxa, tempo, total e confirmação
│   │   └── integracoes/      Clientes dos sistemas externos, simulados (RNF-19)
│   │       ├── base.py       Tempo limite + IntegracaoIndisponivel
│   │       ├── sgl.py        Cardápio das unidades (SGL)
│   │       ├── geocodificacao.py  CEP → latitude/longitude por tabela fixa (decisão Q8)
│   │       └── dados_simulados/   Respostas fixas dos mocks (JSON)
│   └── tests/
│       ├── conftest.py       Fixtures: banco SQLite temporário + TestClient
│       ├── test_saude.py     /api/health e isolamento do banco
│       ├── test_auth.py      Cadastro, login, bloqueio, sessão (RNF-09, RNF-10, RNF-25)
│       ├── test_cardapio.py  Unidades e cardápio (RF-10, RF-11, RNF-03)
│       ├── test_precos.py    RF-02, RF-10, RF-11
│       ├── test_carrinho.py  UC29
│       ├── test_checkout.py  UC28
│       ├── test_dinheiro.py  RNF-23
│       ├── test_integracoes.py  RNF-19 com falhas simuladas
│       └── test_api.py       ESBOÇO-PROVISÓRIO (recados)
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
│   ├── planejamento/         Levantamentos e planos de implementação (o que falta, ordem dos PRs)
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
9. **Rotas em `backend/app/routers/<funcionalidade>.py`**, cada uma com seu
   `APIRouter`; `main.py` só registra os routers.
10. **Dinheiro é sempre `int` em centavos** (RNF-23). Use `app/dinheiro.py`;
    nunca `float` nem `REAL` no banco.
11. **Sistemas externos só em `backend/app/integracoes/`**, e toda chamada passa
    por `base.chamar_com_tempo_limite` (RNF-19). Os mocks aceitam um
    `transporte` para os testes simularem falhas. Tempo limite padrão: 3 s,
    configurável em `BURGUERJA_TIMEOUT_INTEGRACOES`.
12. **Testes usam a fixture `client`** (`tests/conftest.py`), que cria um banco
    temporário via `BURGUERJA_DB`; nunca o `burguerja.db` real. Outras fixtures:
    `sgl` (SGL simulado que o teste altera), `relogio` (hora controlada),
    `novo_cliente`/`ana` (cliente logado) e `banco` (acesso direto para testar
    restrições do esquema).
13. **Regras de negócio em `backend/app/servicos/`**; os routers só validam a
    entrada, chamam o serviço e devolvem a resposta.
14. **Rotas protegidas usam `Depends(seguranca.cliente_atual)`** e filtram tudo
    pelo id do cliente (RN-02, RNF-13). Recurso de outro cliente responde 404.
15. **Hora atual só por `app/relogio.py`** (nunca `datetime.now()` direto), para
    os testes controlarem o tempo.
16. **Funcionalidade sem caso de uso na ERS** (cadastro, login, unidades,
    cardápio, adicionar ao carrinho, esvaziar) é marcada como "infra mínima —
    sem UC na ERS" no código (decisão Q1).

## Crescimento previsto (sugestão, não obrigatório)

No back-end, os routers e serviços já estão separados (regras 9 e 13). Os
próximos casos de uso (UC30 cupom, UC31, UC32, UC33) entram como novos arquivos
em `routers/` e `servicos/`; o UC30 deve preencher `desconto_cupom_centavos` em
`servicos/checkout.py`. No front-end, a ideia é
`frontend/src/pages/<Tela>.tsx` + `frontend/src/components/`. Ao fazer isso,
atualize a árvore e as regras acima.
