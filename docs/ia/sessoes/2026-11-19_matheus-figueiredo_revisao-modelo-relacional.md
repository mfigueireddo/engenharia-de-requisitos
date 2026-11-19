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
fidelidade, Table-Per-Type de pagamento), RF-09, RF-21, RNF-21, RNF-22, RNF-23, B.3, TBD-2.

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

**Decisão humana:** (pendente)
