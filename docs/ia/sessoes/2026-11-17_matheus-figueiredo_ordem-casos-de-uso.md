# Sessão: ordem de implementação dos casos de uso

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | Matheus Figueiredo (no container de nuvem o `git config user.name` era "Claude") |
| Data | 2026-11-17 |
| Duração aproximada | ~1h |
| Ferramenta (harness) e versão | Claude Code 2.1.326 (sessão na nuvem, claude.ai/code) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | claude/practical-cray-xmz3kd |
| Commits | 742aed0, ddfc2fd, 4cd010f, eb36faf, bbf163a + commit final |
| Transcript | `docs/ia/transcripts/2026-11-17_claude_86fc6792-9474-5eff-9e62-d21db14c1d30.jsonl` |
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

**Decisão humana:** aceito.

### 5

**Prompt (literal):**

```text
revise quais serao nossos proximos passos
```

**Saída (resumo):** Seção 8 de `docs/planejamento/backend-base-carrinho.md`
reescrita como plano de próximos passos: passo 0 (PR desta documentação),
1 fundação, 2 autenticação, 3 unidades e cardápio (unidade já com campos do
UC28), 4 carrinho (UC27 + UC29); 2 e 3 em paralelo; UC33 pode começar após o 2;
remoção do esboço provisório fica para o primeiro PR de front-end; critério de
pronto por passo.

**Arquivos alterados:** `docs/planejamento/backend-base-carrinho.md`, este registro

**Decisão humana:** aceito — o humano pediu para abrir o PR do passo 0.

### 6

**Prompt (literal):**

```text
abre o pr do passo 0 e já dá merge com a main
[Request interrupted by user]
antes, faz um arquivo .md para apresentar o que foi feito no passo 1 pro professor
máximo de uma página, tudo em bullet poinst
```

**Saída (resumo):** Interpretado "passo 1" como o trabalho desta sessão (o passo 1
do plano, fundação, ainda não foi feito). Criado
`docs/apresentacoes/2026-11-17_planejamento-carrinho.md` (uma página, só
tópicos, no formato da apresentação anterior). Registro finalizado, linha no
`INDICE.md`, transcript salvo. PR do passo 0 aberto. Merge **não** feito sem
confirmação: AGENTS.md §6 diz que agentes nunca fazem merge e que outro
integrante precisa aprovar — conflito levado ao humano.

**Arquivos alterados:** `docs/apresentacoes/2026-11-17_planejamento-carrinho.md`,
`docs/ia/INDICE.md`, `docs/ia/transcripts/`, este registro

**Decisão humana:** aceito o resumo; sobre o merge, o humano não respondeu e pediu para seguir ao passo 1 (PR #1 continua aberto).

### 7

**Prompt (literal):**

```text
cria uma outra sessao pra gent efazer o passo 1 fundação
```

**Saída (resumo):** Criada uma nova sessão do Claude Code na nuvem
(`session_01RBrzSdWNGSMGCAZyEKsnb1`, "BurguerJá — passo 1: fundação do back-end")
com instruções: seguir AGENTS.md, criar o próprio registro citando este como
sessão anterior, ler o plano no branch do PR #1 (ainda não mergeado), escopo do
passo 1 (routers, fixture de banco temporário, centavos RNF-23, mocks SGL e
geocodificação com timeout RNF-19, ESTRUTURA.md), manter o esboço `recado`,
não abrir PR nem fazer merge sem pedido, e apresentar um plano antes de codar.

**Arquivos alterados:** este registro

**Decisão humana:** <pendente>

## Resultado

- **Entregue:** escolha do UC29 como primeiro caso de uso; levantamento do back-end
  (`docs/planejamento/backend-base-carrinho.md`) com dependências ocultas, modelo de
  dados, rotas, regras→testes, decisões do grupo e plano de 4 PRs; resumo para o
  professor (`docs/apresentacoes/2026-11-17_planejamento-carrinho.md`).
- **Testes:** não se aplica (só documentação).
- **Problemas da IA:** a primeira análise não tinha visto as dependências ocultas
  (cadastro, unidades, cardápio, UC27) — o humano pediu para procurar e elas foram
  encontradas; a resposta "4" do humano foi ambígua e precisou de esclarecimento.
- **Pendências:** merge do PR do passo 0 (aguarda revisão/decisão); passos 1 a 4.

## Reflexão

Ler a ERS inteira (não só a Seção 4) e os wireframes revelou dependências e
conflitos que a lista de casos de uso escondia. Perguntar com opções concretas
resolveu ambiguidades rápido. Faria o levantamento completo já na primeira resposta.
