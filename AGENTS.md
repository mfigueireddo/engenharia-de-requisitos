# AGENTS.md — Instruções para agentes de IA

Este arquivo vale para **qualquer** agente de IA que trabalhe neste repositório
(Claude Code, Codex, Cursor, Copilot, Gemini CLI etc.). O `CLAUDE.md` importa
este arquivo; regras novas entram **aqui**, não lá.

## 1. O projeto

**BurguerJá** — aplicativo web de pedidos para uma rede de fast-food, projeto da
disciplina de Engenharia de Requisitos (PUC-Rio, 2026.2). A disciplina avalia a
implementação da ERS **com uso de IA**, e o uso da IA precisa ser documentado
(seção 5 deste arquivo).

## 2. Fonte de verdade: a ERS

- A Especificação de Requisitos de Software é a **fonte de verdade** do projeto.
  - Original: `srs-pt.docx` (raiz do repositório).
  - Versão legível por agentes: `docs/srs/srs-pt.md` (figuras em `docs/srs/media/`).
    **Leia esta versão** antes de implementar qualquer coisa.
- Se o `.docx` mudar, regenere o Markdown:
  `pandoc srs-pt.docx -t gfm --extract-media=docs/srs -o docs/srs/srs-pt.md`
  (depois troque `src="docs/srs/media/` por `src="media/` no arquivo gerado).
- **Não invente requisitos.** Se o pedido do humano contradiz a ERS, ou a ERS é
  ambígua/omissa (itens TBD no Apêndice C), **pare e pergunte** antes de seguir.
  Registre a divergência no log da sessão.
- **Rastreabilidade:** cite os IDs da ERS (`RF-xx`, `RNF-xx`, `RN-xx`, `UCxx`)
  nas mensagens de commit, nos nomes/descrições de testes e em comentários
  quando uma regra não for óbvia. Ex.: `feat(carrinho): remover item ao zerar quantidade (RF-12)`.

## 3. Stack e restrições (ERS, seção 2.5 e seção 6)

- Front-end: **TypeScript + React**, layout responsivo, prioridade mobile (390x844),
  interface em **português do Brasil**.
- Back-end: **Python + FastAPI**, API REST em JSON; WebSocket para acompanhamento
  de pedidos em tempo real.
- Banco: **SQLite**, acessado **somente** pelo back-end. Respeitar o modelo
  relacional da ERS: XOR item-carrinho/item-pedido (RF-09), triggers de pontos de
  fidelidade, herança Table-Per-Type para formas de pagamento.
- Funções administrativas e de cozinha **não** entram: pertencem ao SGL externo.
  Gateway de Pagamento e SGL são sistemas externos (simule-os com mocks/stubs).
- Nunca commitar segredos (chaves, tokens, senhas, `.env`).

## 4. Estrutura de pastas e arquivos

- Siga a estrutura e as regras de organização de [`ESTRUTURA.md`](ESTRUTURA.md).
  Antes de criar arquivos, leia esse documento.
- Sempre que surgir uma regra nova (de organização, de código ou de processo),
  ou quando você criar/mover/remover pastas ou arquivos importantes,
  **registre em `ESTRUTURA.md` no mesmo commit**.
- Como rodar o projeto: [`README.md`](README.md). Mantenha-o curto.

## 5. Registro obrigatório do uso de IA

Toda sessão de trabalho com IA gera **um arquivo de registro**. O professor
avalia esses registros, então eles fazem parte da entrega.

### 5.1 Onde e com que nome

```
docs/ia/sessoes/AAAA-MM-DD_<autor>_<tema>.md
```

- `<autor>` = saída de `bash scripts/ia/autor.sh` (deriva do `git config user.name`).
- `<tema>` = 2 a 4 palavras em kebab-case (ex.: `carrinho-backend`).
- Modelo do arquivo: `docs/ia/TEMPLATE_SESSAO.md`. Siga **todas** as seções.

### 5.2 Protocolo

1. **Início da sessão** (primeira resposta): crie o arquivo de registro a partir
   do template. Preencha os metadados. Pergunte ao humano o objetivo e os
   requisitos envolvidos, se não estiverem claros.
2. **Depois de cada prompt do humano**: acrescente uma entrada em "Interações"
   **na hora**, não no fim. Sessões longas sofrem compactação de contexto e os
   primeiros prompts se perdem; registrar incrementalmente evita isso.
   - **Prompt: copie literalmente**, sem corrigir nem resumir. Se houver
     segredo ou dado pessoal, substitua só esse trecho por `[removido]`.
   - **Saída: resuma** em poucas linhas o que a IA fez/respondeu, os arquivos
     alterados e comandos relevantes (incluindo testes e seus resultados).
   - **Decisão humana:** aceito / aceito com ajustes / rejeitado, e por quê.
     Se o humano não disser, pergunte no fim da sessão.
3. **Fim da sessão** (quando o humano disser "encerrar sessão", pedir o commit
   final, ou se despedir): complete "Resultado" e "Reflexão", adicione uma linha
   no fim de `docs/ia/INDICE.md` e **commite o registro junto com o código**
   (e o transcript bruto, se existir — ver 5.4).
4. Uma sessão = um arquivo. Se o mesmo humano retomar outro dia, crie outro
   arquivo e cite o anterior em "Sessão anterior".

### 5.3 Modelo e ferramenta

- Informe o **identificador exato do modelo** (ex.: `claude-opus-5-5`,
  `gpt-5-codex`), não só o nome comercial. Se você não souber com certeza qual
  modelo está respondendo, **pergunte ao humano** — não chute.
- Informe a ferramenta (*harness*) e a versão quando possível
  (ex.: `claude --version`, `codex --version`, versão do Cursor).
- Se o modelo mudar durante a sessão, registre na interação em que mudou.

### 5.4 Transcript bruto

- **Claude Code:** o hook em `.claude/settings.json` salva o transcript em
  `docs/ia/transcripts/` automaticamente (com e-mails e tokens mascarados).
  Basta commitá-lo no fim da sessão.
- **Outras ferramentas:** se ela permitir exportar a conversa (Codex: arquivos em
  `~/.codex/sessions/`; ChatGPT/Claude.ai: link de compartilhamento ou export),
  salve em `docs/ia/transcripts/` com o mesmo prefixo do registro, ou cole o
  link no campo "Transcript" do registro. Revise antes de commitar: nada de
  segredos ou dados pessoais.

### 5.5 Ferramentas sem acesso ao repositório (chat web, autocomplete)

O **humano** preenche o registro copiando `docs/ia/TEMPLATE_SESSAO.md`. Para
autocomplete (Copilot inline etc.), um registro por dia de trabalho basta,
descrevendo onde foi usado e o que foi aceito.
