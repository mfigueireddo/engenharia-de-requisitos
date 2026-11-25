# Estado atual do BurguerJá × ERS e projeto relacional (19/11/2026, `main` em `5595695`)

Verificação: `cd backend && python -m pytest` → **131 passed**; `cd frontend && npm run build` → ok.

## 1. Casos de uso (ERS, Seção 4)

| UC | Back-end | Front-end | Situação |
|---|---|---|---|
| UC29 Gerenciar itens do carrinho (RF-08 a RF-13) | Completo: listar, adicionar (UC27, infra mínima), alterar qtd., remover, esvaziar, recálculo e E1–E3 | Sacola (wf 06), Cardápio (wf 04), Detalhe (wf 05) | **Pronto** |
| UC28 Finalizar pedido (RF-01 a RF-07) | Prévia + confirmação, taxa por km, tempo estimado, raio (RF-06), cópia do endereço (RF-05), preço congelado (RF-03), RNF-26 | Finalizar pedido + Pedido recebido | **Pronto sem pagamento e sem cupom** |
| UC30 Aplicar cupom (RF-14 a RF-18) | — (tentativa apagada) | — | Não começado |
| UC31 Acompanhar pedido (RF-19 a RF-23) | Só a notificação "RECEBIDO" e o trigger status = última notificação (RF-20); sem rota "ver pedido", sem WebSocket | Aba "Em breve" | Não começado |
| UC32 Cadastrar/remover cartão (RF-24 a RF-28) | — | — | Não começado |
| UC33 Endereços salvos (RF-29 a RF-32) | Tabela + `GET /api/enderecos` (listagem usada no UC28) | Escolha de endereço no checkout | Parcial (falta criar/editar/remover) |

**Infra mínima sem UC na ERS (decisão Q1):** cadastro, login, logout, sessão por token (RNF-09, RNF-10, RNF-13, RNF-25), unidades e cardápio com cache do SGL simulado (RF-10, RF-11, RNF-03, RNF-19).

**Pagamento (wf 08–09):** não existe. O pedido para em RECEBIDO; nada chega a PAGO.

## 2. Banco × projeto relacional (`docs/srs/Projeto_Relacional_de_Tabelas.drawio`)

- **15 de 25 tabelas do diagrama implementadas**, com os mesmos nomes: `cliente`, `unidade`, `endereco_unidade`, `cardapio`, `cardapio_item`, `item_cardapio`, `item_simples`, `combo`, `item_no_combo`, `endereco_cliente`, `carrinho`, `pedido`, `endereco_pedido`, `item_pedido`, `notificacao`.
- **XOR item carrinho/pedido (RF-09):** implementado em `item_pedido` com CHECK.
- **Triggers do diagrama:** subtipo único do item (TPT), combo com ≥ 2 itens, endereço do pedido só em ENTREGA, item de pedido congelado, status = última notificação; pedido e notificação nunca apagados (RNF-22).
- **Faltam 10 tabelas**, todas de UCs não começados:
  - Pagamento Table-Per-Type (ERS 2.5): `pagamento`, `pagamento_cartao`, `pagamento_pix`, `pagamento_pontos`.
  - Cartão (UC32): `cartao_salvo`.
  - Cupom (UC30): `cupom_promocional`, `uso_cupom`.
  - Fidelidade (ERS 2.5, RN-11): `programa_fidelidade`, `pontos_fidelidade`, `consumo_pontos` — **os triggers de pontos exigidos pela ERS ainda não existem**.
- **Diferenças intencionais (documentadas no cabeçalho do `schema.sql`):** dinheiro em centavos inteiros (RNF-23) em vez de DECIMAL; `SAIU_PARA_ENTREGA` (RF-21) em vez de `EM_ROTA` (o `.drawio` foi corrigido); tabela extra `sessao` e colunas extras de bloqueio de login/cache do SGL; colunas do diagrama sem requisito (telefone, notificações) ficaram opcionais.

## 3. Restrições da ERS (Seção 2.5 / AGENTS.md)

| Restrição | Situação |
|---|---|
| React + TypeScript, mobile 390x844, pt-BR | Ok |
| FastAPI + REST JSON | Ok |
| WebSocket para acompanhar pedido | **Falta** (vem com UC31) |
| SQLite só pelo back-end (RNF-20) | Ok |
| Gateway e SGL simulados | SGL e geocodificação simulados; **gateway ainda não** |
| Triggers de fidelidade, TPT de pagamento | **Falta** |

## 4. Decisões tomadas onde a ERS é omissa (levar ao grupo / Apêndice C)

- Taxa de entrega = km em linha reta × fator da unidade; tempo estimado = 30 min + 3 min/km.
- Sessão expira em 7 dias; resposta 429 durante o bloqueio de login.
- Valores de fidelidade do diagrama como provisórios do TBD-2.
- Divergências ERS × wireframes registradas: teto "até R$ 10" no cupom (wf 07), cupom/pontos na sacola (wf 06), horário de funcionamento e distância por unidade (wf 02), "Esqueci a senha" (wf 01, fora por decisão Q7).

## 5. Próximos passos sugeridos

1. **UC33** completo (rotas de criar/editar/remover; tela do wf 03).
2. **Pagamento + gateway simulado** (tabelas TPT, wf 08–09), que leva o pedido a PAGO.
3. **UC30** cupom (preencher o desconto em `servicos/checkout.py`).
4. **UC31** com WebSocket e histórico (wf 11–13); **UC32** cartões.
5. Fidelidade e seus triggers (wf 14).
6. Rodar o README e o hook no Windows; definir estratégia de migração (hoje é preciso apagar o `burguerja.db` local quando o esquema muda).
