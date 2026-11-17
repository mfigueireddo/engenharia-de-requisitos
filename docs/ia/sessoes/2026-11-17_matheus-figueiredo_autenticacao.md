# Sessão: autenticação do back-end (passo 2)

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | Matheus Figueiredo (no container de nuvem o `git config user.name` era "Claude") |
| Data | 2026-11-17 |
| Duração aproximada | <preencher no fim> |
| Ferramenta (harness) e versão | Claude Code 2.1.326 (sessão na nuvem, claude.ai/code) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | matheus-figueiredo/autenticacao (criado a partir de `matheus-figueiredo/backend-fundacao`; PRs empilhados) |
| Commits | <preenchidos no fim> |
| Transcript | <preenchido no fim> |
| Sessão anterior | [backend-fundacao](2026-11-17_matheus-figueiredo_backend-fundacao.md) |

## Objetivo

Passo 2 do plano `docs/planejamento/backend-base-carrinho.md` (seção 8, no branch
`claude/practical-cray-xmz3kd`, PR #1): tabelas `cliente` e `sessao`; rotas de
cadastro, login, logout e `/api/clientes/me`; senha com bcrypt; bloqueio após 5
tentativas erradas; dependência `cliente_atual()` para as próximas rotas
protegidas. Cadastro e login são "infra mínima — sem UC na ERS" (decisão Q1).

**Requisitos da ERS relacionados:** RNF-08, RNF-09, RNF-10, RNF-13, RNF-25, RN-01, Seção 3.1 (mensagem "E-mail ou senha inválidos"); decisões do grupo Q1, Q6, Q7

## Interações

### 1

**Prompt (literal):**

```text
Sessão nova para o **passo 2 (autenticação)** do back-end do BurguerJá. Siga o AGENTS.md e o CLAUDE.md: crie o registro desta sessão em docs/ia/sessoes/ (autor: matheus-figueiredo; no container de nuvem o git user.name é "Claude") e registre cada prompt. Sessão anterior: docs/ia/sessoes/2026-11-17_matheus-figueiredo_backend-fundacao.md.

**Branch:** crie `matheus-figueiredo/autenticacao` a partir de `matheus-figueiredo/backend-fundacao` (passo 1, ainda não mergeado na `main`; os PRs ficarão empilhados). Leia o ESTRUTURA.md desse branch (regras 9–12 novas: routers, centavos, integrações, fixture `client`).

**Plano:** `docs/planejamento/backend-base-carrinho.md`, que está só no branch `claude/practical-cray-xmz3kd` (PR #1). Leia com `git fetch origin claude/practical-cray-xmz3kd && git show FETCH_HEAD:docs/planejamento/backend-base-carrinho.md` — seções 2.1, 2.2, 3.1, 7 (decisões: Q1 infra mínima sem UC na ERS, Q6 token opaco na tabela `sessao`, Q7 sem "esqueci a senha") e 8.

**Escopo do passo 2:**
- Tabelas `cliente` e `sessao` em `schema.sql`.
- Rotas: `POST /api/auth/cadastro`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/clientes/me`.
- Senha com bcrypt (RNF-09); bloqueio de 15 min após 5 tentativas erradas na mesma conta (RNF-10); aceite dos termos no cadastro (RNF-08, RNF-25); mensagem "E-mail ou senha inválidos" (Seção 3.1).
- Dependência `cliente_atual()` reutilizável para as próximas rotas protegidas (RNF-09, RNF-13, RN-01).
- Marcar no código/testes que cadastro e login são "infra mínima — sem UC na ERS" (decisão Q1).
- Testes citando os IDs; atualizar ESTRUTURA.md e requirements.txt.

Regras: não invente requisitos; se algo for ambíguo, pergunte. O esboço `recado` continua. Rode `cd backend && python -m pytest` antes de terminar. Não abra PR nem faça merge sem o humano pedir. Comece apresentando um plano curto e esperando o OK do humano antes de codar.
```

**Saída (resumo):** Criou o branch `matheus-figueiredo/autenticacao` a partir de
`matheus-figueiredo/backend-fundacao`. Leu `ESTRUTURA.md`, o plano (seções 2.1,
2.2, 3.1, 6, 7, 8; o comando com `FETCH_HEAD` falhou porque o `git fetch` de dois
branches deixou o outro branch no `FETCH_HEAD`, então leu por
`origin/claude/practical-cray-xmz3kd`), os trechos da ERS (3.1, RNF-08 a RNF-13,
RNF-16, RNF-25, RN-01, RN-02) e o código atual do back-end. Criou este registro.
Apresentou um plano curto e listou pontos que a ERS não define (expiração da
sessão, regras de senha/e-mail, detalhes do bloqueio, resposta do cadastro) para
o humano decidir antes de codar.

**Arquivos alterados:** `docs/ia/sessoes/2026-11-17_matheus-figueiredo_autenticacao.md` (novo)

**Decisão humana:** <pendente>
