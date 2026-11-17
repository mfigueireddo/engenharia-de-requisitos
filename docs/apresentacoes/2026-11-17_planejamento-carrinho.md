# BurguerJá: planejamento do primeiro caso de uso

**Matheus Figueiredo · 17/11/2026 · Claude Code (claude-opus-5-5)**

## Objetivo

- Escolher o caso de uso que deve ser implementado primeiro
- Levantar tudo o que o back-end precisa para implementá-lo

## 1. Ordem dos casos de uso

- Grafo de dependências montado a partir da Seção 4 da ERS:
  - UC28 (checkout) consome o carrinho (UC29) e os endereços (UC33)
  - UC30 (cupom) estende o UC28; UC31 (acompanhar) precisa de pedidos do UC28
  - UC32 (cartões) e UC33 (endereços) são independentes
- Escolhido o **UC29 – Gerenciar Itens do Carrinho** como primeiro
- Ordem definida: UC29 → UC33 → UC28 → UC30 → UC31 → UC32

## 2. Dependências que a ERS não detalha

- O UC29 pressupõe funções sem caso de uso escrito:
  - cadastro, login e autorização (RNF-09, RNF-13, RN-01)
  - unidades e cardápio vindos do SGL (RF-08, RF-13)
  - UC27 – Adicionar ao Carrinho (citado, mas não especificado)
  - esvaziar o carrinho para trocar de unidade (RN-03)
- Decisão do grupo: **a ERS não muda**; essas funções entram como infraestrutura mínima, sem regras novas

## 3. Divergências encontradas

- Wireframe da sacola mostra cupom e pontos abatendo o total: conflita com RN-12 e UC30
- Horário de funcionamento e escolhas dentro do combo aparecem nos wireframes, mas não na ERS
- Decisão: ignorados no UC29
- RF-06 exige distância, mas o endereço só tem CEP: decidido usar conversão de CEP simulada

## 4. Plano do back-end

- Modelo de dados com valores em centavos (RNF-23) e restrição XOR item-carrinho/item-pedido (RF-09)
- Rotas REST, mocks do SGL com tempo limite (RNF-19) e tabela regra → teste
- 4 PRs: fundação → autenticação ∥ unidades e cardápio → carrinho
- Documento completo: `docs/planejamento/backend-base-carrinho.md`

## Uso de IA nesta sessão

- 1 sessão, 7 prompts, registrada em `docs/ia/sessoes/`
- A IA leu a ERS e os wireframes, apontou lacunas e perguntou antes de decidir
- Uma resposta ambígua do humano foi esclarecida com opções, em vez de suposta
- Nenhum código alterado: sessão só de análise e planejamento

## Próximos passos

- Passo 1: fundação do back-end
- Passos 2 e 3 em paralelo: autenticação; unidades e cardápio
