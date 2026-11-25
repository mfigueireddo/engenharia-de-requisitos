# Estado atual do BurguerJá × ERS e projeto relacional (25/11/2026, `main` em `fa16452`; UC31 no branch `joao-marcelo-onofre/uc31-implementacao`)

Verificação: `main` tinha 145 testes e build ok; o branch do UC31 tem `cd backend && python -m pytest` → **153 passed**; `cd frontend && npm run build` → ok.

## 1. Casos de uso (ERS, Seção 4)

| UC | Back-end | Front-end | Situação |
|---|---|---|---|
| UC29 Gerenciar itens do carrinho (RF-08 a RF-13) | Completo: listar, adicionar (UC27, infra mínima), alterar qtd., remover, esvaziar, recálculo e E1–E3 | Sacola (wf 06), Cardápio (wf 04), Detalhe (wf 05) | **Pronto** |
| UC28 Finalizar pedido (RF-01 a RF-07) | Prévia + confirmação, taxa por km, tempo estimado, raio (RF-06), cópia do endereço (RF-05), preço congelado (RF-03), RNF-26 | Finalizar pedido + Pedido recebido | **Pronto sem pagamento e sem cupom** |
| UC30 Aplicar cupom (RF-14 a RF-18) | Completo: cupons do cliente, validação, cálculo, uso no checkout e triggers | Tela de cupons integrada à sacola, checkout e pedido recebido | **Pronto na main** |
| UC31 Acompanhar pedido (RF-19 a RF-23) | Histórico e detalhe filtrados por cliente; webhook HMAC do SGL; notificações persistidas; WebSocket por pedido | Histórico, detalhe, linha do tempo, reconexão e aviso de indisponibilidade | **Implementado no branch; aguardando PR** |
| UC32 Cadastrar/remover cartão (RF-24 a RF-28) | — | — | Não começado |
| UC33 Endereços salvos (RF-29 a RF-32) | Tabela + `GET /api/enderecos` (listagem usada no UC28) | Escolha de endereço no checkout | Parcial (falta criar/editar/remover) |

**Infra mínima sem UC na ERS (decisão Q1):** cadastro, login, logout, sessão por token (RNF-09, RNF-10, RNF-13, RNF-25), unidades e cardápio com cache do SGL simulado (RF-10, RF-11, RNF-03, RNF-19).

**Pagamento (wf 08–09):** ainda não existe. O pedido para em RECEBIDO; nada chega a PAGO.

## 2. Banco × projeto relacional (`docs/srs/Projeto_Relacional_de_Tabelas.drawio`)

- **17 de 25 tabelas do diagrama implementadas**, com os mesmos nomes: as 15 tabelas anteriores mais `cupom_promocional` e `uso_cupom` (UC30).
- **XOR item carrinho/pedido (RF-09):** implementado em `item_pedido` com CHECK.
- **Triggers do diagrama:** subtipo único do item (TPT), combo com ≥ 2 itens, endereço do pedido só em ENTREGA, item de pedido congelado, status = última notificação, titularidade/limite de cupom; pedido, notificação e uso de cupom nunca apagados (RNF-22).
- **Faltam 8 tabelas**, todas de UCs ainda não concluídos:
  - Pagamento Table-Per-Type (ERS 2.5): `pagamento`, `pagamento_cartao`, `pagamento_pix`, `pagamento_pontos`.
  - Cartão (UC32): `cartao_salvo`.
  - Fidelidade (ERS 2.5, RN-11): `programa_fidelidade`, `pontos_fidelidade`, `consumo_pontos` — **os triggers de pontos exigidos pela ERS ainda não existem**.
- **Diferenças intencionais (documentadas no cabeçalho do `schema.sql`):** dinheiro em centavos inteiros (RNF-23) em vez de DECIMAL; `SAIU_PARA_ENTREGA` (RF-21) em vez de `EM_ROTA` (o `.drawio` foi corrigido); tabela extra `sessao` e colunas extras de bloqueio de login/cache do SGL; colunas do diagrama sem requisito (telefone, notificações) ficaram opcionais.

## 3. Restrições da ERS (Seção 2.5 / AGENTS.md)

| Restrição | Situação |
|---|---|
| React + TypeScript, mobile 390x844, pt-BR | Ok |
| FastAPI + REST JSON | Ok |
| WebSocket para acompanhar pedido | Implementado no branch do UC31; aguardando PR |
| SQLite só pelo back-end (RNF-20) | Ok |
| Gateway e SGL simulados | SGL e geocodificação simulados; **gateway ainda não**; webhook do SGL validado com HMAC (RNF-15) |
| Triggers de fidelidade, TPT de pagamento | **Falta** |

## 4. Decisões tomadas onde a ERS é omissa (levar ao grupo / Apêndice C)

- Taxa de entrega = km em linha reta × fator da unidade; tempo estimado = 30 min + 3 min/km.
- Sessão expira em 7 dias; resposta 429 durante o bloqueio de login.
- Valores de fidelidade do diagrama como provisórios do TBD-2.
- Contrato técnico do UC31: webhook `POST /api/webhooks/sgl/pedidos/{id}/status`
  com HMAC-SHA256 no header `X-SGL-Signature`; acompanhamento por
  `GET /api/pedidos/{id}` e WebSocket autenticado em `/api/ws/pedidos/{id}`.
- Em caso de perda de conexão, o front-end mostra o último status persistido,
  tenta reconectar e busca novamente o pedido quando a conexão volta (RNF-04).
- Divergências ERS × wireframes registradas: teto "até R$ 10" no cupom (wf 07), cupom/pontos na sacola (wf 06), horário de funcionamento e distância por unidade (wf 02), "Esqueci a senha" (wf 01, fora por decisão Q7).

## 5. Próximos passos sugeridos

1. Revisar, abrir e fazer merge do PR do **UC31**; depois atualizar este documento
   para registrar a implementação na `main`.
2. **UC33** completo (rotas de criar/editar/remover; tela do wf 03).
3. **Pagamento + gateway simulado** (tabelas TPT, wf 08–09), que leva o pedido a PAGO.
4. **UC32** cartões.
5. Fidelidade e seus triggers (wf 14).
6. Rodar o README e o hook no Windows; definir estratégia de migração (hoje é preciso apagar o `burguerja.db` local quando o esquema muda).
