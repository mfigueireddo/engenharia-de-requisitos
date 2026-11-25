# BurguerJá — o que o grupo fez até agora (17 a 25/11/2026)

Fonte: registros em `docs/ia/sessoes/` e PRs #1 a #7, além da implementação do UC31 no branch `joao-marcelo-onofre/uc31-implementacao`.

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

## Hugo Freires — aplicar cupom (23/11, PR #6)

- **UC30 completo:** cupons do cliente, validação de validade/limite/subtotal,
  desconto percentual e isenção da taxa de entrega (RF-14 a RF-18, RN-07).
- Integração do cupom ao checkout (UC28 A3), registro de uso no pedido e triggers
  de titularidade, limite e histórico (RF-15 a RF-17, RNF-22).
- Tela de cupons integrada à sacola, checkout e pedido recebido; base compartilhada
  passou a incluir cupons para os cenários de demonstração.

## João Marcelo Onofre — acompanhar pedido (25/11, branch do UC31)

- **UC31 implementado:** histórico de pedidos e detalhe com itens, preços
  congelados, taxa, desconto, total, endereço e tempo estimado (RF-19 a RF-23).
- Webhook assinado do SGL (`X-SGL-Signature` com HMAC-SHA256) grava cada mudança
  como notificação e mantém o status conforme a última notificação (RF-20/RF-22,
  RNF-15).
- WebSocket autenticado por pedido atualiza a tela sem recarregar; o front-end
  mostra o último status, reconecta e busca as notificações perdidas após a volta
  da conexão (RNF-04). Pedidos de outro cliente retornam 404/fecham o canal
  (RNF-13).
- Tela de histórico (wf 13) e tela de acompanhamento (wf 11), com interface em
  português e estado de cliente sem pedidos (A1).
- 8 testes novos cobrindo login, isolamento, webhook, timeline e WebSocket.

## Números

- **3 casos de uso prontos na `main`** (UC28 sem pagamento, UC29 e UC30) +
  **UC31 implementado em branch**, além da infraestrutura mínima (login,
  cardápio, endereços só listagem).
- **145 testes** no back-end passando na `main`; **153 no branch do UC31**;
  build do front-end ok nos dois estados.
- **7 PRs** mergeados na `main`; o PR do UC31 ainda aguarda abertura/revisão.

## Lições do uso de IA

- Perguntar antes de codar (fórmulas omissas, divergências ERS × wireframe) evitou retrabalho.
- Prompt ambíguo ("o C de cupom") custou código apagado.
- Testar no navegador revelou um bug que os testes unitários não pegavam.
- No UC31, testar o fluxo real de atualização exigiu combinar REST, webhook e
  WebSocket; os testes garantem o isolamento entre clientes e a reconexão busca
  novamente o estado persistido em vez de confiar apenas no evento perdido.
