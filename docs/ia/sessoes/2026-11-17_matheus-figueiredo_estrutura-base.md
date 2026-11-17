# Sessão: estrutura base (banco + API + front-end)

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | Matheus Figueiredo (no container de nuvem o `git config user.name` era "Claude"; autor definido com `IA_AUTOR`) |
| Data | 2026-11-17 |
| Duração aproximada | 20 min |
| Ferramenta (harness) e versão | Claude Code 2.1.x (sessão na nuvem, claude.ai/code) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | main |
| Commits | commit "Cria estrutura base: SQLite + FastAPI + React" |
| Transcript | `docs/ia/transcripts/2026-11-17_matheus-figueiredo_aef3e293-c8dd-5fc7-9fb8-fed79cb995fb.jsonl` (mesma conversa da sessão anterior) |
| Sessão anterior | [setup-registro-ia](2026-11-17_matheus-figueiredo_setup-registro-ia.md) |

## Objetivo

Criar o esqueleto mínimo do sistema com banco, API e front-end conversando,
sem começar as funcionalidades da ERS. Documentar a estrutura de pastas e
como rodar.

**Requisitos da ERS relacionados:** stack da seção 2.5; RNF-20 (SQLite acessado
só pelo back-end); seção 3.4 (HTTP + JSON). Nenhum RF implementado.

## Interações

### 1

**Prompt (literal):**

```text
agora quero q vc crie uma estrutura básica pra implementação 

o mínimo para que tenhamos pelo menos um banco de dados, api e frontend conversando

não comece o trabalho do projeto de fato, quero apenas fazer a base pra quem quiser começar ter algo estruturado

siga as instruções dos arquivos para levantar as tecnologias utilizadas

crie uma página web que se comunica com o backend, armazena/pega uma informação trivial só pra testar se tá tudo integrado

cria um README MUITO CURTO com o mínimo pra rodar. integrantes do grupo tem linux, mac e windows

cria um arquivo markdown pra registrar a estrutura de pasta e arquivos do sistema

adiciona no agents.md que ele deve seguir essa estrutura e, sempre que tiver alguma regra nova, registrar no .md

dá commit e push na main

roda o programa e me dá um print do que aparece na tela atualmente
```

**Saída (resumo):**
- `backend/`: FastAPI com `sqlite3` da biblioteca padrão (sem ORM, para não
  impor essa decisão ao grupo); `schema.sql` com a tabela de teste `recado`;
  rotas `GET /api/health`, `GET` e `POST /api/recados`; teste em pytest.
- `frontend/`: Vite + React + TypeScript; proxy `/api` → porta 8000 (evita CORS);
  `api.ts` concentra as chamadas; página de teste que salva e lista recados.
- `README.md` curto (comandos para Linux/Mac/Windows), `ESTRUTURA.md` (árvore +
  regras de organização), `.gitignore`, nova seção 4 no `AGENTS.md` (seguir
  `ESTRUTURA.md` e registrar regras novas nele); a seção de registro de IA virou a 5.
- Verificação: `pytest` passou (1 teste), `npm run build` passou, API e Vite
  rodando; Playwright (390x844) salvou um recado, recarregou a página e o recado
  continuou lá. O print foi enviado no chat.

**Arquivos alterados:** `backend/**`, `frontend/**`, `README.md`, `ESTRUTURA.md`,
`.gitignore`, `AGENTS.md`, `docs/ia/README.md`, `docs/ia/INDICE.md`, este registro.

**Decisão humana:** pendente de revisão.

## Resultado

- **Entregue:** base com banco, API e front-end integrados, documentação de execução e de estrutura.
- **Testes:** `python -m pytest` (1 passou); `npm run build` ok; teste manual via Playwright ok.
- **Problemas da IA:** nenhum relevante.
- **Pendências:** o grupo decidir se adota ORM (ex.: SQLAlchemy) e migrações; remover a tabela `recado` quando as funcionalidades reais começarem; testar o README no Windows.

## Reflexão

Manter o mínimo (sem ORM, sem roteamento, sem biblioteca de UI) deixa as
decisões de arquitetura para o grupo, mas já fixa as convenções de pasta e o
caminho front-end → API → banco.
