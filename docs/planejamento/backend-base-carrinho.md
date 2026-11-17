# Levantamento: o que o back-end precisa para o UC29 (Gerenciar Itens do Carrinho)

Data: 2026-11-17 · Escopo: **apenas back-end** · Base: `docs/srs/srs-pt.md` + wireframes 01–06.

O UC29 foi escolhido como primeiro caso de uso porque UC28 (checkout), UC30
(cupom) e UC31 (acompanhar) dependem dele. Este documento lista **tudo** que
precisa existir no back-end para implementá-lo, inclusive as dependências que
**não estão escritas como caso de uso** na ERS.

Legenda: ✅ especificado na ERS · ⚠️ citado na ERS mas sem caso de uso/detalhe · ❓ omisso/ambíguo (decisão do grupo)

---

## 1. Dependências ocultas (o que o UC29 pressupõe e a ERS não detalha)

| # | Dependência | Onde a ERS exige | Situação |
|---|---|---|---|
| D1 | **Cadastro de cliente** (criar conta, aceitar termos) | 2.2 ("Criar uma conta"), RN-01, RNF-08, RNF-25 | ⚠️ sem UC |
| D2 | **Login / sessão autenticada** | RNF-09 ("todos os casos de uso da Seção 4 exigem cliente logado"), RNF-10, wireframe 01 | ⚠️ sem UC |
| D3 | **Autorização por dono do recurso** | RNF-13, RN-02 | ✅ |
| D4 | **Unidades** (listar e escolher a loja) | RF-08 (carrinho vinculado a uma unidade), RN-03, wireframe 02 | ⚠️ sem UC |
| D5 | **Cardápio da unidade obtido do SGL** (preços, descontos, combos) | 2.2, 3.3, RF-10, RF-11, RF-13, wireframe 04 | ⚠️ sem UC |
| D6 | **Cache do último cardápio + horário da atualização** | UC29 E3, RNF-03 | ✅ (mas ver ❓Q2) |
| D7 | **Adicionar ao carrinho (UC27)** | 4.2.1 ("Complementa o UC27"), wireframe 05 | ⚠️ citado, não especificado |
| D8 | **Esvaziar carrinho / trocar de unidade** | RN-03 | ⚠️ regra sem fluxo |
| D9 | **Tabela de pedido (ao menos o esqueleto)** | RF-09 (XOR item-carrinho/item-pedido) | ✅ — necessária já para a restrição XOR |
| D10 | **Mock do SGL** com timeout e tratamento de erro | 2.5, RNF-19 | ✅ |

Sem D1, D2, D4, D5 e D7 **não há como colocar um item no carrinho**, então eles
são pré-requisitos de fato do UC29.

---

## 2. Modelo de dados (SQLite — `backend/app/schema.sql`)

Regra geral: **dinheiro em centavos (`INTEGER`)**, nunca `REAL` (RNF-23).
Nada de histórico apagado fisicamente (RNF-22) → produtos que saem do cardápio
são desativados, não excluídos.

### 2.1 `cliente` (D1, D2)
| Coluna | Tipo / restrição | Origem |
|---|---|---|
| id | INTEGER PK | |
| nome | TEXT NOT NULL | wireframe 02 ("Olá, Paulo!") |
| email | TEXT NOT NULL UNIQUE | wireframe 01 |
| senha_hash | TEXT NOT NULL (bcrypt) | RNF-09 |
| termos_aceitos_em | TEXT NOT NULL | RNF-08, RNF-25 |
| tentativas_login_falhas | INTEGER NOT NULL DEFAULT 0 | RNF-10 |
| bloqueado_ate | TEXT NULL | RNF-10 (15 min após 5 erros) |
| avisos_ativos | INTEGER NOT NULL DEFAULT 0 | RF-23 (usado só no UC31; pode ficar para depois) |
| criado_em | TEXT NOT NULL | |

### 2.2 `sessao` (D2) — se a opção for token opaco (ver Q6)
`token_hash` PK, `cliente_id` FK → cliente ON DELETE CASCADE, `criado_em`, `expira_em`.

### 2.3 `unidade` (D4)
| Coluna | Tipo / restrição | Origem |
|---|---|---|
| id | INTEGER PK | |
| id_sgl | TEXT NOT NULL UNIQUE | identificador no sistema externo |
| nome | TEXT NOT NULL | wireframe 02 |
| endereço (rua, número, bairro, cidade, estado, CEP) | TEXT | RF-06 (distância) |
| latitude, longitude | REAL | RF-06 — **só usado no UC28** (ver Q8) |
| raio_max_entrega_m | INTEGER | RF-06, RN-04 — UC28 |
| fator_taxa_entrega_centavos | INTEGER | RN-05 — UC28 |
| tem_drive_thru | INTEGER (0/1) | RN-04 — UC28 |
| cardapio_atualizado_em | TEXT NULL | UC29 E3, RNF-03 |

Os campos marcados "UC28" podem entrar já (custa pouco e evita migração) ou só no PR do checkout.

### 2.4 `produto` — item do cardápio de uma unidade (D5)
| Coluna | Tipo / restrição | Origem |
|---|---|---|
| id | INTEGER PK | |
| unidade_id | FK → unidade | RF-08, RN-03 |
| id_sgl | TEXT NOT NULL; UNIQUE(unidade_id, id_sgl) | |
| nome, descricao, categoria | TEXT | wireframes 04–05 (Lanches, Acompanhamentos, Bebidas…) |
| tipo | TEXT CHECK IN ('SIMPLES','COMBO') | RF-11 |
| preco_centavos | INTEGER CHECK ≥ 0 | RF-02 (NULL ou derivado para combo — ver abaixo) |
| desconto_centavos | INTEGER CHECK 0 ≤ desconto ≤ preco | **RF-10** |
| vigente | INTEGER (0/1) | UC29 E2 — item fora do cardápio |

### 2.5 `combo_componente` (RF-11)
`combo_id` FK → produto (tipo COMBO), `produto_id` FK → produto (tipo SIMPLES),
`quantidade` INTEGER ≥ 1. PK (combo_id, produto_id).
Preço do combo = Σ preços dos componentes; desconto aplicado **em cada componente** (RF-11).
Melhor calcular por consulta/serviço do que guardar o preço do combo duplicado.

### 2.6 `carrinho` (RF-08)
`id` PK, `cliente_id` FK **UNIQUE** (um carrinho por cliente), `unidade_id` FK
(RN-03), `atualizado_em`.

### 2.7 `pedido` — esqueleto mínimo (D9)
Só o necessário para a FK do item: `id`, `cliente_id`, `unidade_id`, `status`
(CHECK nos 7 valores do RF-21), `criado_em`. O UC28 completa as demais colunas
(tipo de atendimento, endereço copiado, taxa, total…). Criar agora evita ter de
recriar a tabela `item` depois (SQLite não adiciona FK com `ALTER TABLE`).

### 2.8 `item` — item de carrinho **ou** de pedido (RF-09, RNF-21)
| Coluna | Tipo / restrição | Origem |
|---|---|---|
| id | INTEGER PK | |
| carrinho_id | FK → carrinho, NULL | RF-09 |
| pedido_id | FK → pedido, NULL | RF-09 |
| **CHECK ((carrinho_id IS NULL) <> (pedido_id IS NULL))** | | **RF-09 — XOR** |
| produto_id | FK → produto | |
| quantidade | INTEGER CHECK ≥ 1 | **RF-12** |
| observacao | TEXT NULL | UC29 A2 |
| preco_unitario_centavos, desconto_unitario_centavos, valor_final_centavos | INTEGER NULL | RF-02/RF-03 — **preenchidos só no pedido** (no carrinho o valor é sempre recalculado, RF-13) |

Triggers de fidelidade e herança TPT de pagamento (RNF-21) **não** são necessários para o UC29.

---

## 3. API REST (todas em `/api/…`)

### 3.1 Autenticação e cliente (D1, D2)
| Método | Rota | Observações |
|---|---|---|
| POST | `/api/auth/cadastro` | nome, e-mail, senha, aceite dos termos (RNF-25); senha com bcrypt (RNF-09) |
| POST | `/api/auth/login` | 401 "E-mail ou senha inválidos"; bloqueio 15 min após 5 erros (RNF-10) |
| POST | `/api/auth/logout` | |
| GET | `/api/clientes/me` | dados do cliente logado |

Dependência FastAPI `cliente_atual()` usada por todas as rotas protegidas (RNF-09, RNF-13).

### 3.2 Unidades e cardápio (D4, D5, D6) — públicas (RN-01: visitante pode ver o cardápio)
| Método | Rota | Observações |
|---|---|---|
| GET | `/api/unidades` | lista de unidades |
| GET | `/api/unidades/{id}/cardapio` | produtos vigentes + combos com componentes + `atualizado_em` (RNF-03) |

### 3.3 Carrinho (UC27 + UC29) — exigem login
| Método | Rota | Fluxo ERS |
|---|---|---|
| GET | `/api/carrinho` | UC29 passos 1–3: recalcula com cardápio vigente (RF-13), remove itens não vigentes e devolve `avisos` (E2), devolve `cardapio_atualizado_em` (E3), carrinho vazio (E1) |
| POST | `/api/carrinho/itens` | UC27 (D7): produto, quantidade, observação. Se o carrinho for de outra unidade → **409** (RN-03) |
| PATCH | `/api/carrinho/itens/{id}` | UC29 passo 4 (quantidade) e A2 (observação). Quantidade 0 → remove (RF-12, A1) |
| DELETE | `/api/carrinho/itens/{id}` | UC29 A1 |
| DELETE | `/api/carrinho` | esvaziar (D8, RN-03) |

Resposta do carrinho (exemplo de forma): `unidade`, `itens[]` (nome, quantidade,
observação, preço/desconto unitário, `valor_final`, `componentes[]` se combo),
`subtotal`, `avisos[]`, `cardapio_atualizado_em`. **Todos os valores calculados
no servidor** (RNF-14) — o back-end ignora preços vindos do cliente.

---

## 4. Integração com o SGL (mock)

- `backend/app/integracoes/sgl.py`: interface `obter_cardapio(id_sgl_unidade)`.
- Implementação simulada lendo um JSON de exemplo (`backend/app/integracoes/dados_sgl/…`).
- **Timeout + tratamento de erro** em toda chamada (RNF-19); se falhar, usa o
  cardápio já salvo e mantém `cardapio_atualizado_em` antigo (RNF-03, UC29 E3).
- Sincronização: ao consultar o cardápio/carrinho (se o cache estiver velho) ou
  por um comando de carga inicial. Itens que sumirem do SGL → `vigente = 0`.
- Testes com falha simulada do SGL (RNF-19).

---

## 5. Regras de negócio que viram código/teste no UC29

| ID | Regra | Onde garantir |
|---|---|---|
| RF-02 | valor final = qtd × (preço − desconto) | serviço de cálculo + teste |
| RF-08 | 1 carrinho por cliente, 1 unidade | `UNIQUE(cliente_id)` + teste |
| RF-09 | XOR carrinho/pedido | `CHECK` no banco + teste |
| RF-10 | 0 ≤ desconto ≤ preço | `CHECK` no banco + teste |
| RF-11 | combo = Σ componentes, desconto por componente | serviço de cálculo + teste |
| RF-12 | qtd ≥ 1; zero remove | `CHECK` + regra na rota PATCH + teste |
| RF-13 | carrinho sempre com preços vigentes | recálculo no GET + teste (mudar preço no "SGL" e reler) |
| RN-01 | só logado monta carrinho | dependência de auth + teste 401 |
| RN-02 / RNF-13 | cliente só mexe no próprio carrinho | teste com dois clientes (404/403) |
| RN-03 | trocar unidade exige esvaziar | 409 + teste |
| RNF-14 | cálculos no servidor | payload não aceita preço |
| RNF-23 | centavos inteiros | tipos `INTEGER` + teste de arredondamento |
| UC29 E2/E3 | item fora do cardápio; SGL fora do ar | testes com mock |

---

## 6. Infraestrutura do back-end

- **Organização** (já prevista no ESTRUTURA.md): `app/routers/{auth,unidades,carrinho}.py`,
  `app/servicos/` (cálculo de preços), `app/integracoes/sgl.py`, `app/seguranca.py`.
- **Dependências novas:** `bcrypt` (RNF-09); `pyjwt` só se a opção for JWT (Q6).
- **Banco nos testes:** fixture do pytest com banco temporário (`BURGUERJA_DB`) e dados de exemplo.
- **Dados de exemplo (seed):** 2–3 unidades e um cardápio com lanche, bebida, acompanhamento e um combo.
- **Esboço provisório:** só sai quando a funcionalidade chegar ao front-end (AGENTS.md §7). Se o PR for só de back-end, mantém.

---

## 7. Perguntas para o grupo (não decidir sem resposta)

| # | Pergunta | Por quê |
|---|---|---|
| Q1 | Cadastro, login, escolha de unidade, consulta ao cardápio e **UC27** entram como "infraestrutura mínima" ou o grupo escreve esses casos na ERS antes? | ⚠️ citados mas sem fluxo; AGENTS.md proíbe inventar requisitos |
| Q2 | O cardápio e as unidades são **guardados no nosso banco** (cache do SGL)? | A Seção 3.3 lista o que fica no banco e **não** cita cardápio/unidades, mas o UC29 E3 exige "último cardápio recebido" e as FKs precisam deles |
| Q3 | Combos com escolhas (wireframe 06: "Batata + Refri — Refri: guaraná") | A ERS só diz que combo = soma de itens (RF-11); não há variações/opções |
| Q4 | Wireframe 06 mostra **cupom e pontos** na sacola, com o total abatido por pontos (– R$ 5,00) | Conflita com RN-12 (sem dividir pontos + outro meio) e com UC30 (cupom é no checkout). Para o UC29, proponho ignorar cupom/pontos |
| Q5 | Wireframe 02 mostra unidade "Aberta/Fechada · abre às 11h" | Horário de funcionamento não existe na ERS. Proponho ignorar por enquanto |
| Q6 | Sessão: **token opaco em tabela** (recomendado: simples, permite logout real) ou JWT? | Decisão técnica, não de requisito |
| Q7 | "Esqueci minha senha" (wireframe 01) | Não especificado; proponho fora do escopo |
| Q8 | Distância do RF-06: como obter latitude/longitude do endereço do cliente (só há CEP)? | Não afeta o UC29, mas bloqueia o UC28 — bom decidir cedo |

---

### Decisões do grupo (2026-11-17)

| # | Decisão |
|---|---|
| Q1 | **A ERS não será alterada.** Cadastro, login, unidades, consulta ao cardápio, UC27 e esvaziar carrinho entram como **infraestrutura mínima**, sem inventar regras além das já escritas na ERS. Cada uma deve ser marcada no código/testes como "infra mínima — sem UC na ERS". |
| Q2 | **Sim:** unidades e cardápio ficam no banco do BurguerJá como cópia (cache) do que vem do SGL. |
| Q3 | **Sim, ignorar no UC29:** cupom e pontos na sacola, horário de funcionamento e escolhas dentro do combo. Combo = lista fixa de componentes (RF-11). |
| Q4 | Mesma linha do Q3 (ignorados: cupom/pontos na sacola, horário, escolhas no combo). |
| Q5 | Idem: horário de funcionamento fora do escopo. |
| Q6 | Sem objeção à recomendação: **token opaco guardado na tabela `sessao`**. |
| Q7 | Sem objeção à proposta: "Esqueci minha senha" fica **fora do escopo**. |
| Q8 | **Geocodificação simulada (opção c):** o formulário de endereço continua igual ao UC33; um serviço mock (`app/integracoes/geocodificacao.py`, como o do SGL) converte o CEP em latitude/longitude a partir de uma tabela fixa de CEPs de exemplo. CEP desconhecido → endereço não pode ser usado para entrega. Só é necessário no UC28 (RF-06). |

## 8. Próximos passos (revisado em 2026-11-17)

Cada passo é **um branch `<autor>/<tema>` a partir da `main` atualizada e um PR**
revisado por outro integrante (AGENTS.md §6). Antes de cada PR:
`cd backend && python -m pytest`.

| Passo | Branch sugerido | Entrega | Requisitos | Depende de |
|---|---|---|---|---|
| 0 | (este branch) | PR só de documentação: este levantamento + registro da sessão | — | — |
| 1 | `<autor>/backend-fundacao` | `app/routers/`, fixture pytest com banco temporário, utilitário de centavos, esqueleto dos mocks `integracoes/sgl.py` e `integracoes/geocodificacao.py` com timeout | RNF-19, RNF-23 | 0 |
| 2 | `<autor>/autenticacao` | `cliente`, `sessao`; cadastro, login, logout, `/clientes/me`; bcrypt; bloqueio após 5 erros; dependência `cliente_atual()` | RNF-09, RNF-10, RNF-13, RNF-25, RN-01 | 1 |
| 3 | `<autor>/unidades-cardapio` | `unidade` (já com lat/long, raio, fator de taxa, drive-thru), `produto`, `combo_componente`; carga do mock do SGL; rotas públicas; `cardapio_atualizado_em` | RF-10, RF-11, RNF-03, RNF-19 | 1 |
| 4 | `<autor>/carrinho-backend` | `carrinho`, `pedido` (esqueleto), `item` com CHECK XOR; UC27 (adicionar) + UC29 (listar/recalcular, alterar, remover, esvaziar) | RF-02, RF-08 a RF-13, RN-02, RN-03, RNF-14 | 2 e 3 |

**Paralelismo:** 2 e 3 podem ser feitos por pessoas diferentes ao mesmo tempo.
Depois do passo 2, o **UC33 (endereços)** também pode começar em paralelo (só depende do cliente logado).

**Depois do back-end do UC29** (fora deste levantamento):
- Front-end de login + cardápio + sacola → esse PR é o que **remove o esboço provisório** (`recado`, AGENTS.md §7), pois é o primeiro a ir do banco ao front-end.
- UC33 → UC28 (usa a geocodificação simulada, RF-06) → UC30 → UC31 → UC32.

**Critério de pronto de cada passo:** todos os IDs da coluna "Requisitos" com teste
citando o ID no nome/descrição; `ESTRUTURA.md` atualizado com pastas novas;
registro de IA da sessão commitado junto.
