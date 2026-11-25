# Estrutura do projeto

Mapa das pastas e arquivos e as regras de organização. **Mantenha este arquivo
atualizado**: toda pasta nova, arquivo importante ou regra de organização nova
entra aqui no mesmo commit.

## Árvore

```
.
├── AGENTS.md                 Regras para agentes de IA (fonte única)
├── CLAUDE.md                 Importa AGENTS.md + regras só do Claude Code
├── ESTRUTURA.md              Este arquivo
├── README.md                 Como rodar (mínimo)
├── srs-pt.docx               ERS original (fonte de verdade)
├── .github/
│   └── pull_request_template.md  Modelo de descrição de PR
├── backend/                  API — Python + FastAPI + SQLite
│   ├── requirements.txt      Dependências Python (versões fixas)
│   ├── app/
│   │   ├── main.py           Cria o app FastAPI e registra os routers
│   │   ├── db.py             Conexão com o SQLite (arquivo em BURGUERJA_DB) e esquema
│   │   ├── schema.sql        DDL do banco, segue docs/srs/Projeto_Relacional_de_Tabelas.drawio
│   │   ├── dinheiro.py       Valores em centavos inteiros, sem float (RNF-23)
│   │   ├── relogio.py        Data/hora atual (os testes trocam por monkeypatch)
│   │   ├── seguranca.py      bcrypt, token de sessão, conexão por requisição e cliente_atual (RNF-09, RNF-13)
│   │   ├── routers/          Rotas da API, um arquivo por funcionalidade
│   │   │   ├── saude.py      /api/health
│   │   │   ├── auth.py       /api/auth/*, /api/clientes/me — infra mínima (Q1)
│   │   │   ├── unidades.py   /api/unidades e cardápio — públicas, infra mínima (Q1, Q2)
│   │   │   ├── carrinho.py   /api/carrinho — UC29 (+ adicionar/esvaziar, infra mínima)
│   │   │   ├── cupons.py     /api/cupons e /api/cupons/aplicar — UC30
│   │   │   ├── enderecos.py  GET /api/enderecos — só listagem, usada pelo UC28 (CRUD = UC33)
│   │   │   ├── pedidos.py    /api/pedidos/previa e /api/pedidos — UC28 (+ A3 / UC30)
│   │   │   └── acompanhamento.py  /api/pedidos, webhook SGL e WebSocket — UC31
│   │   ├── servicos/         Regras de negócio (cálculos e validações), sem HTTP
│   │   │   ├── precos.py     RF-02, RF-11
│   │   │   ├── cardapio.py   Cache do cardápio do SGL (RF-10, RF-13, RNF-03, RNF-22)
│   │   │   ├── carrinho.py   Carrinho recalculado (UC29, E1–E3)
│   │   │   ├── cupons.py     UC30: listagem, validação, desconto percentual/isento e uso
│   │   │   ├── checkout.py   UC28: distância, taxa, tempo, cupom (A3), total e confirmação
│   │   │   └── acompanhamento.py UC31: histórico, detalhe, notificações e conexões em tempo real
│   │   └── integracoes/      Clientes dos sistemas externos, simulados (RNF-19)
│   │       ├── base.py       Tempo limite + IntegracaoIndisponivel
│   │       ├── sgl.py        Cardápio das unidades (SGL)
│   │       ├── geocodificacao.py  CEP → latitude/longitude por tabela fixa (decisão Q8)
│   │       └── dados_simulados/   Respostas fixas dos mocks (JSON)
│   ├── scripts/
│   │   ├── dados_demo.py     Cliente de demonstração com endereços e cupons (só desenvolvimento; não é rota)
│   │   └── base_compartilhada.py  Recria o banco local com a base de testes do grupo (usa dados_demo)
│   └── tests/
│       ├── conftest.py       Fixtures: banco SQLite temporário + TestClient
│       ├── test_saude.py     /api/health e isolamento do banco
│       ├── test_auth.py      Cadastro, login, bloqueio, sessão (RNF-09, RNF-10, RNF-25)
│       ├── test_cardapio.py  Unidades e cardápio (RF-10, RF-11, RNF-03)
│       ├── test_precos.py    RF-02, RF-10, RF-11
│       ├── test_carrinho.py  UC29
│       ├── test_checkout.py  UC28
│       ├── test_acompanhamento.py UC31 (RF-19 a RF-23, RNF-13, RNF-15, WebSocket)
│       ├── test_cupons.py    UC30 (RF-14 a RF-18, RN-07)
│       ├── test_dinheiro.py  RNF-23
│       ├── test_integracoes.py  RNF-19 com falhas simuladas
│       ├── test_concorrencia.py Conexão usada em outra thread (evita "database is locked")
│       ├── test_dados_demo.py   Script de dados de demonstração
│       └── test_base_compartilhada.py  Base compartilhada: sempre igual, cenários e logins
├── frontend/                 Interface — TypeScript + React (Vite)
│   ├── package.json
│   ├── vite.config.ts        Porta 5173 e proxy de /api para a API (porta 8000)
│   ├── index.html
│   └── src/
│       ├── main.tsx          Monta o React e importa os estilos
│       ├── App.tsx           Escolhe a tela pela rota e protege as que exigem login (RN-01)
│       ├── navegacao.ts      Rotas pelo "#" da URL (#/cardapio, #/item/3 ...), sem dependência extra
│       ├── api.ts            Cliente da API REST e tipos das respostas (todo fetch passa por aqui)
│       ├── formatar.ts       Moeda, data, distância e nomes em pt-BR
│       ├── useCarregar.ts    Hook de carregamento (dados / erro / carregando)
│       ├── estilos/
│       │   ├── tema.css      ÚNICO lugar com cores, fontes, tamanhos, raios e sombras
│       │   └── global.css    Base e moldura do app (coluna de celular, tela, utilitários)
│       ├── contextos/        Estado compartilhado: Sessao.tsx (cliente, unidade) e Carrinho.tsx
│       ├── componentes/      Componentes reutilizáveis (Botao, Campo, Cartao, Tela, Folha...) + componentes.css
│       └── paginas/          Uma tela por arquivo (Entrar, Inicio, Cardapio, DetalheItem, Sacola,
│                             Cupons, Checkout, PedidoRecebido, Pedidos, AcompanharPedido, EmBreve) + paginas.css
├── docs/
│   ├── srs/                  ERS em Markdown (srs-pt.md) + figuras (media/)
│   │   └── Projeto_Relacional_de_Tabelas.drawio  Modelo relacional do grupo (ERS, Ap. B.3); abrir em app.diagrams.net
│   ├── apresentacoes/        Resumos e slides para o professor (AAAA-MM-DD_<tema>.md ou .pdf)
│   ├── planejamento/         Levantamentos e planos de implementação (o que falta, ordem dos PRs)
│   └── ia/                   Registro do uso de IA (ver docs/ia/README.md)
├── scripts/
│   ├── rodar.sh              Sobe tudo com um comando: instala, dados demo, API + front-end
│   └── ia/autor.sh           Nome do git → identificador usado em docs/ia/
└── .claude/                  Configuração e hooks do Claude Code
```

## Regras de organização

1. **Back-end só em `backend/`, front-end só em `frontend/`.** O front-end nunca
   acessa o banco; tudo passa pela API REST (ERS 2.5, 3.3).
2. **Rotas da API começam com `/api/`.** O proxy do Vite depende disso.
3. **Esquema do banco em `backend/app/schema.sql`.** Tabelas, restrições e
   triggers ficam nesse arquivo (ou em arquivos `.sql` ao lado, se crescer).
   Ele segue o projeto relacional `docs/srs/Projeto_Relacional_de_Tabelas.drawio`
   (nomes de tabelas e colunas, FKs, ON DELETE, CHECKs e triggers). Toda
   diferença em relação ao diagrama fica explicada no cabeçalho do `schema.sql`;
   quem mudar uma tabela atualiza os dois no mesmo PR. Se o diagrama contradisser
   a ERS, vale a ERS (ex.: status `SAIU_PARA_ENTREGA`, RF-21). Não há migração:
   mudou o esquema, apague o `burguerja.db` local (o app recusa banco antigo).
4. **Chamadas HTTP do front-end só em `frontend/src/api.ts`** (ou em `src/api/`
   quando crescer). Componentes não chamam `fetch` diretamente.
5. **Todo endpoint novo ganha teste** em `backend/tests/`.
6. **Arquivos gerados não entram no git:** `.venv/`, `node_modules/`, `dist/`, `*.db`.
7. **Nada vai direto para a `main`.** Cada tarefa num branch `<autor>/<tema>` e
   merge por pull request revisado por outro integrante (`AGENTS.md`, seção 6).
8. **Rotas em `backend/app/routers/<funcionalidade>.py`**, cada uma com seu
   `APIRouter`; `main.py` só registra os routers.
9. **Dinheiro é sempre `int` em centavos** (RNF-23). Use `app/dinheiro.py`;
    nunca `float` nem `REAL` no banco para dinheiro. Onde o diagrama diz
    `DECIMAL(10,2)`, a coluna é `INTEGER` com sufixo `_centavos`.
10. **Sistemas externos só em `backend/app/integracoes/`**, e toda chamada passa
    por `base.chamar_com_tempo_limite` (RNF-19). Os mocks aceitam um
    `transporte` para os testes simularem falhas. Tempo limite padrão: 3 s,
    configurável em `BURGUERJA_TIMEOUT_INTEGRACOES`.
11. **Testes usam a fixture `client`** (`tests/conftest.py`), que cria um banco
    temporário via `BURGUERJA_DB`; nunca o `burguerja.db` real. Outras fixtures:
    `sgl` (SGL simulado que o teste altera), `relogio` (hora controlada),
    `novo_cliente`/`ana` (cliente logado) e `banco` (acesso direto para testar
    restrições do esquema).
12. **Regras de negócio em `backend/app/servicos/`**; os routers só validam a
    entrada, chamam o serviço e devolvem a resposta.
13. **Rotas protegidas usam `Depends(seguranca.cliente_atual)`** e filtram tudo
    pelo id do cliente (RN-02, RNF-13). Recurso de outro cliente responde 404.
14. **Hora atual só por `app/relogio.py`** (nunca `datetime.now()` direto), para
    os testes controlarem o tempo.
15. **Funcionalidade sem caso de uso na ERS** (cadastro, login, unidades,
    cardápio, adicionar ao carrinho, esvaziar) é marcada como "infra mínima —
    sem UC na ERS" no código (decisão Q1).
16. **Cores, fontes e medidas só em `frontend/src/estilos/tema.css`**, como
    variáveis CSS (`var(--cor-primaria)`). Os outros `.css` não têm cor nem fonte
    "solta". Valores tirados dos wireframes da ERS (seção 3.1).
17. **Telas em `frontend/src/paginas/`, uma por arquivo**, montadas com os
    componentes de `frontend/src/componentes/` (importe de `../componentes`). Antes
    de criar um elemento visual novo, veja se já existe um componente; se for
    reutilizável, crie-o lá. Toda tela usa `<Tela>` (cabeçalho, rodapé fixo, abas).
18. **Toda a interface em português do Brasil** (ERS 2.4), com erros junto ao
    campo e confirmação para ações que não podem ser desfeitas (`<Folha>`, ERS 3.1).
19. **Dados de demonstração só por `backend/scripts/`**, nunca por rota da API.
20. **Base de testes do grupo = `backend/scripts/base_compartilhada.py`, nunca um
    `.db` no git.** O script apaga o banco local e o recria sempre igual, pela
    própria API (`bash scripts/rodar.sh --resetar-banco`). Cenário novo para todos
    testarem entra no script (e em `tests/test_base_compartilhada.py`) no mesmo PR
    que precisar dele; CEP novo de endereço entra em `integracoes/geocodificacao.py`.

21. **Atualizações do SGL no UC31** entram por `POST /api/webhooks/sgl/pedidos/{id}/status`,
    assinado com HMAC-SHA256 no header `X-SGL-Signature` e segredo da variável
    `BURGUERJA_SGL_WEBHOOK_SECRET`; o front-end acompanha por `GET /api/pedidos/{id}`
    e WebSocket `/api/ws/pedidos/{id}?token=...`.

## Crescimento previsto (sugestão, não obrigatório)

Os próximos casos de uso (UC31, UC32, UC33) entram como novos arquivos
em `routers/` e `servicos/`, criando no `schema.sql` as tabelas do diagrama que
ainda faltam: PAGAMENTO com
PAGAMENTO_PIX/CARTAO/PONTOS e CARTAO_SALVO (Table-Per-Type, ERS 2.5) e
PROGRAMA_FIDELIDADE, PONTOS_FIDELIDADE e CONSUMO_PONTOS (triggers de fidelidade;
crédito quando o pedido chega a ENTREGUE, RN-11; valores do diagrama como
provisórios do TBD-2, decisão de 2026-11-19). No front-end:
o pagamento substitui a tela `PedidoRecebido` (telas 08–10), e o UC31 e a
fidelidade substituem `EmBreve` (telas 11–14). O UC33 (tela 03) deve ligar o
"novo endereço" do `Checkout` (UC28 A2). Ao fazer isso, atualize a árvore e as regras acima.
