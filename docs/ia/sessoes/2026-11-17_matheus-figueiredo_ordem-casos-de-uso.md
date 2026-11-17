# Sessão: ordem de implementação dos casos de uso

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | Matheus Figueiredo (no container de nuvem o `git config user.name` era "Claude") |
| Data | 2026-11-17 |
| Duração aproximada | <preencher no fim> |
| Ferramenta (harness) e versão | Claude Code 2.1.326 (sessão na nuvem, claude.ai/code) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | claude/practical-cray-xmz3kd |
| Commits | <preencher no fim> |
| Transcript | <preencher no fim> |
| Sessão anterior | — |

## Objetivo

Analisar os casos de uso da ERS e definir qual deve ser implementado primeiro
por ser pré-requisito dos demais.

**Requisitos da ERS relacionados:** UC28, UC29, UC30, UC31, UC32, UC33 (Seção 4); UC27 citado na 4.2

## Interações

### 1

**Prompt (literal):**

```text
veja os casos de uso no arquivo de srs

qual dos casos vc considera que deve ser primeiro que os outros pq é necessário pra confecção do resto?
```

**Saída (resumo):** Leitura das Seções 2.2, 4 e 7.1 de `docs/srs/srs-pt.md`.
Montado o grafo de dependências: UC28 (checkout) consome o carrinho (UC29) e,
na entrega, os endereços (UC33); UC30 estende UC28; UC31 precisa de pedidos
criados por UC28; UC32 é independente (só gateway mock). Recomendação: **UC29
(Gerenciar Itens do Carrinho)** primeiro, junto com a base mínima que ele exige
(cliente, unidade, cardápio do SGL simulado). Ordem sugerida:
UC29 → UC33 → UC28 → UC30 → UC31 → UC32. Divergência apontada: a ERS não
especifica UC27 (Adicionar ao Carrinho), login/cadastro nem consulta ao cardápio
como casos de uso detalhados, mas UC29 depende deles — perguntado ao humano
como tratar.

**Arquivos alterados:** este registro

**Decisão humana:** aceito (implícito) — o humano seguiu com o UC29 como tarefa e pediu o levantamento do back-end; a pergunta sobre UC27/cadastro ficou em aberto.

### 2

**Prompt (literal):**

```text
pode ser que tenha mais alguma dependencia de use case que nao tenhamos documentado

quero que voce faca um levantamento de tudo que precisamos estruturado (apenas em backend por enquanto) para conseguirmos fazer essa tarefa
```

**Saída (resumo):** Leitura das Seções 2–7 e Apêndices da ERS, dos wireframes
01–06 e do back-end atual. Criado `docs/planejamento/backend-base-carrinho.md`
com: 10 dependências ocultas do UC29 (cadastro, login, autorização, unidades,
cardápio do SGL e cache, UC27, esvaziar carrinho, esqueleto de `pedido` para o
XOR, mock do SGL); modelo de dados proposto (cliente, sessao, unidade, produto,
combo_componente, carrinho, pedido, item com CHECK XOR, valores em centavos);
rotas REST; integração SGL com timeout/fallback; tabela regra→teste; 8 perguntas
ao grupo (Q1–Q8) e divisão em 4 PRs. Divergências encontradas: wireframe 06
mostra cupom e pontos na sacola (conflita com RN-12/UC30); wireframe 02 mostra
horário de funcionamento (omisso na ERS); combos com escolhas (wireframe 06) não
especificados; Seção 3.3 não lista cardápio/unidades como dados do banco.
Nenhum código alterado.

**Arquivos alterados:** `docs/planejamento/backend-base-carrinho.md` (novo),
`ESTRUTURA.md` (pasta `docs/planejamento/`), este registro

**Decisão humana:** aceito — o humano respondeu às perguntas na interação 3.

### 3

**Prompt (literal):**

```text
1. nao vamos mudar nada na ers. deixamos do jeito atual e seguimos com o resto como infra minima
2. sim
3. sim
4. pedir o endereco do cliente tb
```

**Saída (resumo):** Decisões registradas na seção 7 de
`docs/planejamento/backend-base-carrinho.md`: ERS não muda; cadastro, login,
unidades, cardápio, UC27 e esvaziar carrinho entram como infraestrutura mínima;
cardápio e unidades guardados como cópia do SGL; cupom/pontos na sacola, horário
de funcionamento e escolhas de combo ignorados; Q6 (token opaco) e Q7 (sem
"esqueci a senha") assumidos pelas recomendações, já que o humano não se opôs.
A resposta 4 ficou ambígua (pedir o endereço no cadastro? pedir as coordenadas?)
— a IA pediu esclarecimento em vez de supor.

**Arquivos alterados:** `docs/planejamento/backend-base-carrinho.md`, este registro

**Decisão humana:** aceito — o humano esclareceu o item 4 na interação 4.

### 4

**Prompt (literal):**

```text
c
```

**Saída (resumo):** Escolhida a opção (c) para o RF-06: geocodificação simulada
(CEP → latitude/longitude por tabela fixa, mock como o do SGL), sem mudar o
formulário do UC33. Registrado como Q8 em `docs/planejamento/backend-base-carrinho.md`.

**Arquivos alterados:** `docs/planejamento/backend-base-carrinho.md`, este registro

**Decisão humana:** <pendente>

## Resultado

- **Entregue:** <preencher no fim>
- **Testes:** não se aplica (análise)
- **Problemas da IA:** <preencher no fim>
- **Pendências:** decidir como tratar UC27/cadastro/cardápio, que não estão detalhados na ERS.

## Reflexão

<preencher no fim>
