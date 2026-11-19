# Sessão: revisão do esquema contra o modelo relacional

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | matheus-figueiredo |
| Data | 2026-11-19 |
| Duração aproximada | (preencher no fim) |
| Ferramenta (harness) e versão | Claude Code 2.1.328 (web) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | claude/awesome-turing-3m0yie |
| Commits | (preenchidos no fim) |
| Transcript | docs/ia/transcripts/2026-11-19_claude_dcce4748-9e5c-5235-84e3-4589104d6039.jsonl |
| Sessão anterior | — |

## Objetivo

Comparar o esquema do banco na `main` (`backend/app/schema.sql`) com o projeto
relacional de tabelas do grupo (`Projeto_Relacional_de_Tabelas.drawio`, enviado
pelo humano; é o diagrama previsto no Apêndice B.3 da ERS).

**Requisitos da ERS relacionados:** Seção 2.5 (modelo relacional, triggers de
fidelidade, Table-Per-Type de pagamento), RF-02, RF-03, RF-04, RF-05, RF-09, RF-10, RF-11, RF-13, RF-21, RN-05, RN-11, RNF-21, RNF-22, RNF-23, B.3, TBD-2.

## Interações

### 1

**Prompt (literal):**

```text
@"/root/.claude/uploads/dcce4748-9e5c-5235-84e3-4589104d6039/0a4645eb-Projeto_Relacional_de_Tabelas.drawio" revisa a main e ve se a nossa estrutura de tabelas ta seguindo esse planejado
```

**Saída (resumo):** a IA extraiu as 25 tabelas, colunas, FKs e quadros de
restrições do `.drawio` (script Python no scratchpad) e comparou com as 10
tabelas de `backend/app/schema.sql` na `main` (c0c2ed3). Conclusão: segue
**parcialmente**. Alinhados: carrinho (1 por cliente + unidade), XOR
item carrinho/pedido (RF-09), endereço do cliente, notificação. Divergências
estruturais: cardápio (diagrama tem CARDAPIO + CARDAPIO_ITEM + ITEM_CARDAPIO
com herança TPT ITEM_SIMPLES/COMBO; código tem `produto` por unidade com coluna
`tipo`), endereço da unidade e do pedido embutidos nas tabelas (diagrama usa
ENDERECO_UNIDADE e ENDERECO_PEDIDO), nomes diferentes, dinheiro em centavos
(RNF-23) em vez de DECIMAL, PEDIDO com totais/distância/tempo em minutos.
O diagrama diverge da ERS em `EM_ROTA` (ERS RF-21: `SAIU_PARA_ENTREGA`) e fixa
valores de fidelidade que a ERS deixa como TBD-2. Faltam 15 tabelas (pagamento
TPT, cartão salvo, cupom, fidelidade), ligadas a UCs ainda não implementados.

**Arquivos alterados:** este registro.

**Decisão humana:** aceito — o humano escolheu alinhar o código ao diagrama e incluir o `.drawio` em `docs/srs/` (ver interação 2).

### 2

**Prompt (literal):**

```text
alinha o codigo ao diagrama
pode colocar no srs sim
```

**Saída (resumo):** antes de refatorar, a IA listou ao humano (AGENTS.md §2)
os pontos em que o diagrama contradiz a ERS ou cria campos sem requisito e
perguntou como seguir. Respostas: status `SAIU_PARA_ENTREGA` (ERS, RF-21) e
corrigir o `.drawio`; fidelidade com crédito em ENTREGUE (RN-11) usando os
valores do diagrama como provisórios do TBD-2; colunas sem requisito
(telefone, notificações, telefone/horário da unidade) **opcionais**; **não**
criar agora as tabelas de pagamento, cartão, cupom e fidelidade (só refatorar
as existentes).

Feito em seguida:
- `backend/app/schema.sql` reescrito com os nomes e a estrutura do diagrama:
  `endereco_unidade`, `cardapio`, `cardapio_item`, `item_cardapio` (item da
  rede, não da unidade) com herança `item_simples`/`combo` e `item_no_combo`;
  `endereco_cliente` (`logradouro`); `item_pedido` (antes `item`) com preços
  NOT NULL e CHECKs de RF-02/RF-10; `pedido` com `modalidade`, `data_hora`,
  `previsao_entrega` e sem totais (vêm da soma dos itens); `endereco_pedido`.
  Triggers do diagrama: subtipo único do item, combo com 2 ou mais itens,
  endereço do pedido só em ENTREGA, item de pedido congelado, status do pedido
  = última notificação. Mantidos: centavos (RNF-23), `sessao`, cache do SGL,
  RNF-22. Diferenças explicadas no cabeçalho do `schema.sql`.
- Serviços e rotas adaptados (`cardapio.py` grava em SAVEPOINT; carrinho grava
  os valores recalculados na linha; checkout grava `endereco_pedido`). A API
  manteve os nomes públicos (`rua`, `tipo_atendimento`...); única mudança:
  `POST /api/carrinho/itens` passa a exigir `unidade_id`, porque o item agora é
  da rede (front-end ajustado em `api.ts` e `DetalheItem.tsx`). O pedido não
  devolve mais `distancia_m` (não é coluna do diagrama), e sim `previsao_entrega`.
- Mock do SGL de unidades com os nomes do diagrama; `db.inicializar` recusa
  banco no esquema antigo com mensagem clara (sem migração).
- Diagrama copiado para `docs/srs/Projeto_Relacional_de_Tabelas.drawio` com
  `EM_ROTA` → `SAIU_PARA_ENTREGA` e "pedido PAGO" → "pedido ENTREGUE (RN-11)".
- `ESTRUTURA.md` (regras 3 e 9, árvore, crescimento previsto) e `README.md`.
- Testes: `python -m pytest` → **131 passed** (antes 124; novos testes de
  CHECKs/triggers do diagrama e do banco antigo). `npm run build` → ok.
  Teste manual com uvicorn + `dados_demo`: carrinho, prévia e pedido de
  entrega funcionando.

**Arquivos alterados:** `backend/app/schema.sql`, `backend/app/db.py`,
`backend/app/servicos/{cardapio,carrinho,checkout}.py`,
`backend/app/routers/{carrinho,unidades,enderecos}.py`,
`backend/app/integracoes/dados_simulados/unidades_sgl.json`,
`backend/scripts/dados_demo.py`, `backend/tests/test_{cardapio,carrinho,checkout,saude}.py`,
`frontend/src/api.ts`, `frontend/src/paginas/DetalheItem.tsx`,
`docs/srs/Projeto_Relacional_de_Tabelas.drawio`, `ESTRUTURA.md`, `README.md`, este registro.

**Decisão humana:** (pendente)
