# BurguerJá — João Marcelo e o UC31: acompanhar pedido

**João Marcelo Onofre · 25/11/2026 · Codex via VS Code (gpt-5-codex)**

## Objetivo

Implementar o **UC31 — Acompanhar Pedido** do BurguerJá, mantendo a arquitetura existente e a rastreabilidade com a ERS.

**Requisitos relacionados:** UC31, RF-19 a RF-23, RN-02, RN-09, RNF-04, RNF-13, RNF-15 e interface WebSocket da Seção 3.4.

## O que foi implementado

- **Histórico de pedidos:** o cliente autenticado consulta apenas os próprios pedidos, com unidade, tipo de atendimento, status, data de criação e última atualização (RF-19, RN-02, RNF-13).
- **Detalhe do pedido:** itens com preços congelados, subtotal, taxa, desconto de cupom, total, endereço de entrega e tempo estimado.
- **Linha do tempo:** cada notificação mostra status, título, mensagem e data/hora. O status atual continua sendo o da notificação mais recente (RF-20 e RF-22).
- **Webhook do SGL:** atualizações assinadas com HMAC-SHA256 no header `X-SGL-Signature`; o segredo fica somente em `BURGUERJA_SGL_WEBHOOK_SECRET` (RNF-15).
- **Atualização em tempo real:** WebSocket autenticado por pedido, sem necessidade de recarregar a tela.
- **Reconexão:** quando a conexão cai, a interface mostra o último status persistido, tenta reconectar e busca novamente o pedido quando a conexão volta (RNF-04).
- **Avisos:** a notificação só solicita aviso ao cliente quando os avisos estão habilitados (RF-23).

## Arquivos principais

- `backend/app/routers/acompanhamento.py`: rotas REST, webhook e WebSocket.
- `backend/app/servicos/acompanhamento.py`: regras de negócio, histórico, notificações e conexões.
- `backend/app/seguranca.py`: validação do token usado no WebSocket.
- `backend/tests/test_acompanhamento.py`: testes do UC31.
- `frontend/src/paginas/Pedidos.tsx`: histórico de pedidos, tela 13.
- `frontend/src/paginas/AcompanharPedido.tsx`: detalhe e linha do tempo, tela 11.
- `frontend/src/api.ts`, `App.tsx` e `navegacao.ts`: integração da API e das rotas.

O banco já possuía as tabelas `pedido` e `notificacao`, além do trigger que atualiza o status do pedido. Por isso o UC31 não precisou criar novas tabelas.

## Verificação

- Backend: **153 testes aprovados** no branch.
- Front-end: `npm run build` concluído sem erros.
- Testes específicos: isolamento entre clientes, cliente sem pedidos, webhook sem assinatura, webhook válido, timeline, WebSocket e acesso indevido ao pedido de outro cliente.

## Como testar

1. Subir o projeto com `bash scripts/rodar.sh`.
2. Entrar com um cliente que tenha pedidos na base compartilhada, como `bruno@burguerja.com`.
3. Abrir a aba **Pedidos** e selecionar um pedido.
4. Para simular uma atualização do SGL, configurar `BURGUERJA_SGL_WEBHOOK_SECRET` e enviar um webhook assinado para o pedido.
5. Observar a mudança do status e o novo item na linha do tempo sem recarregar a página.

## Situação

A implementação está no branch `joao-marcelo-onofre/uc31-implementacao`, com os commits da implementação e da documentação. O próximo passo é abrir o PR, obter a revisão de outro integrante e somente então fazer o merge na `main`.
