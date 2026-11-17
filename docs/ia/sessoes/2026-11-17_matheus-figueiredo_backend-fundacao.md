# Sessão: fundação do back-end (passo 1)

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | Matheus Figueiredo (no container de nuvem o `git config user.name` era "Claude") |
| Data | 2026-11-17 |
| Duração aproximada | <preencher no fim> |
| Ferramenta (harness) e versão | Claude Code 2.1.326 (sessão na nuvem, claude.ai/code) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | matheus-figueiredo/backend-fundacao |
| Commits | <preenchidos no fim> |
| Transcript | <preenchido no fim> |
| Sessão anterior | [ordem-casos-de-uso](2026-11-17_matheus-figueiredo_ordem-casos-de-uso.md) (no branch `claude/practical-cray-xmz3kd`, PR #1) |

## Objetivo

Passo 1 do plano `docs/planejamento/backend-base-carrinho.md` (seção 8): fundação
do back-end, sem funcionalidade de negócio — rotas em `app/routers/`, fixture do
pytest com banco temporário, utilitário de dinheiro em centavos, esqueleto dos
mocks do SGL e da geocodificação com tempo limite e tratamento de erro.

**Requisitos da ERS relacionados:** RNF-19, RNF-23; decisão do grupo Q8 (geocodificação simulada)

## Interações

### 1

**Prompt (literal):**

```text
Sessão nova para o **passo 1 (fundação do back-end)** do BurguerJá. Antes de tudo, siga o AGENTS.md e o CLAUDE.md: crie o registro desta sessão em docs/ia/sessoes/ (autor: matheus-figueiredo; no container de nuvem o git user.name é "Claude") e registre cada prompt. Sessão anterior: docs/ia/sessoes/2026-11-17_matheus-figueiredo_ordem-casos-de-uso.md.

Contexto: o plano está em `docs/planejamento/backend-base-carrinho.md`, que ainda está só no branch `claude/practical-cray-xmz3kd` (PR #1, ainda não mergeado). Leia com `git fetch origin claude/practical-cray-xmz3kd && git show FETCH_HEAD:docs/planejamento/backend-base-carrinho.md` (e o registro da sessão anterior do mesmo jeito). Leia as seções 6, 7 (decisões do grupo) e 8 (próximos passos).

Escopo do passo 1 (só back-end, sem funcionalidade de negócio ainda):
- Separar as rotas em `backend/app/routers/` (mantendo `/api/health`; o esboço `recado` FICA, pois só sai no primeiro PR de front-end — AGENTS.md §7).
- Fixture do pytest com banco SQLite temporário (variável `BURGUERJA_DB`).
- Utilitário de dinheiro em centavos inteiros, sem float (RNF-23), com testes.
- Esqueleto dos mocks em `backend/app/integracoes/`: `sgl.py` (cardápio) e `geocodificacao.py` (CEP → latitude/longitude por tabela fixa — decisão Q8), ambos com tempo limite e tratamento de erro (RNF-19), com testes de falha simulada.
- Atualizar ESTRUTURA.md com as pastas novas.

Regras: não invente requisitos; se algo for ambíguo, pergunte. Cite os IDs da ERS nos commits e testes. Rode `cd backend && python -m pytest` antes de terminar. Não abra PR nem faça merge sem o humano pedir. Comece apresentando um plano curto e esperando o OK do humano antes de codar.
```

**Saída (resumo):** a IA leu AGENTS.md, CLAUDE.md, ESTRUTURA.md, o template, o
código atual do back-end, o plano (seções 6–8) e o registro anterior via
`git show FETCH_HEAD:...`, e conferiu RNF-19 e RNF-23 na ERS. Criou o branch
`matheus-figueiredo/backend-fundacao` a partir da `main` e este registro.
Apresentou um plano curto e perguntas sobre pontos não definidos na ERS
(valor do tempo limite, escopo do utilitário de dinheiro, RNF-19 não citar a
geocodificação). Não codou nada; aguardando OK.

**Arquivos alterados:** `docs/ia/sessoes/2026-11-17_matheus-figueiredo_backend-fundacao.md` (novo)

**Decisão humana:** <pendente>
