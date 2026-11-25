# BurguerJá — o que Matheus e Paulo fizeram até agora (17 a 19/11/2026)

Fonte: registros em `docs/ia/sessoes/` (9 sessões, todas com Claude Code / `claude-opus-5-5`) e PRs #1 a #4.

## Matheus Figueiredo — processo, planejamento, front-end e banco

**Processo e base (17/11)**
- Estrutura de registro do uso de IA: `AGENTS.md`/`CLAUDE.md`, template, índice, hook que salva o transcript.
- ERS convertida para Markdown (`docs/srs/srs-pt.md`) para os agentes lerem.
- Esqueleto SQLite + FastAPI + React conversando (esboço "recado"), `README` e `ESTRUTURA.md`.
- Fluxo de branch + PR (sem CI) e modelo de PR.

**Planejamento (17/11, PR #1)**
- Escolheu o **UC29 (carrinho)** como primeiro caso de uso; ordem UC29 → UC33 → UC28 → UC30 → UC31 → UC32.
- Levantamento do back-end (`docs/planejamento/backend-base-carrinho.md`): dependências ocultas, modelo de dados, rotas, decisões Q1–Q8 do grupo.
- Fundação do back-end (passo 1): routers, banco temporário nos testes, dinheiro em centavos (RNF-23), mocks do SGL e geocodificação com tempo limite (RNF-19).

**Front-end do UC28/UC29 (19/11, PR #3)**
- Telas pelos wireframes: Entrar, Cadastro, Início, Cardápio, Detalhe, Sacola, Finalizar pedido, Pedido recebido.
- Tema único (`tema.css`), 18 componentes reutilizáveis; esboço "recado" removido.
- Corrigiu bug de concorrência do back-end ("database is locked") achado testando no navegador.

**Banco alinhado ao projeto relacional (19/11, PR #4)**
- `schema.sql` reescrito seguindo o `.drawio` do grupo (cardápio Table-Per-Type, endereços em tabelas próprias, triggers).
- Divergências diagrama × ERS resolvidas a favor da ERS (`SAIU_PARA_ENTREGA`, pontos em ENTREGUE).

## Paulo Henrique Monção — back-end do carrinho e checkout (18/11, PR #2)

- **Autenticação:** cadastro, login, logout, `/clientes/me`, bcrypt, bloqueio após 5 erros (RNF-09, RNF-10).
- **Unidades e cardápio** com cache do SGL simulado (RF-10, RF-11, RNF-03).
- **UC29 completo:** adicionar, alterar quantidade, remover, esvaziar, recalcular (RF-08 a RF-13).
- **UC28:** prévia e confirmação do pedido, taxa por km, tempo estimado, raio de entrega, preço congelado, notificação "RECEBIDO" (RF-01 a RF-07).
- Começou o UC30 (cupom), mas o escopo mudou e o código foi apagado.
- 69 testes novos (124 no total ao fim da sessão).

## Números

- **2 casos de uso prontos** (UC28 sem pagamento/cupom, UC29) + infra mínima (login, cardápio, endereços só listagem).
- **131 testes** no back-end passando; build do front-end ok.
- **4 PRs** mergeados na `main`.

## Lições do uso de IA

- Perguntar antes de codar (fórmulas omissas, divergências ERS × wireframe) evitou retrabalho.
- Prompt ambíguo ("o C de cupom") custou código apagado.
- Testar no navegador revelou um bug que os testes unitários não pegavam.
