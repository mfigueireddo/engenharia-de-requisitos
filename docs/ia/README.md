# Registro do uso de IA

A implementação do BurguerJá é feita com apoio de IA, e todo uso é documentado
aqui. As regras que os agentes seguem estão em [`AGENTS.md`](../../AGENTS.md)
(seção 4).

## O que tem aqui

| Caminho | Conteúdo |
|---|---|
| [`INDICE.md`](INDICE.md) | Tabela com todas as sessões: data, autor, ferramenta, modelo, tema, requisitos |
| [`sessoes/`](sessoes/) | Um registro por sessão: metadados, prompts literais, resumo das saídas, decisões humanas, resultado e reflexão |
| [`transcripts/`](transcripts/) | Transcripts brutos das sessões (quando a ferramenta permite), como evidência |
| [`TEMPLATE_SESSAO.md`](TEMPLATE_SESSAO.md) | Modelo de registro |

## Como funciona, por ferramenta

| Ferramenta | Lê as regras de | Registro da sessão | Transcript bruto |
|---|---|---|---|
| Claude Code | `CLAUDE.md` (que importa `AGENTS.md`) | O agente escreve | Automático (hook) |
| Codex, Cursor, Copilot (agente), Gemini CLI | `AGENTS.md` | O agente escreve | Exportar manualmente, se possível |
| Chat web (ChatGPT, Claude.ai) | — | A pessoa preenche o template | Link de compartilhamento |
| Autocomplete (Copilot inline etc.) | — | A pessoa preenche, um por dia | — |

## Para cada integrante

1. Confira seu nome no git: `git config user.name` (ele vira o `<autor>` nos nomes de arquivo).
2. Ao abrir uma sessão com um agente, ele cria o registro sozinho. Se não criar, peça:
   *"Siga a seção 4 do AGENTS.md e crie o registro desta sessão."*
3. Para encerrar, diga **"encerrar sessão"**: o agente fecha o registro, atualiza o índice e commita.
4. **Gemini CLI:** ele lê `GEMINI.md` por padrão; configure `"contextFileName": "AGENTS.md"`
   em `.gemini/settings.json` ou peça para ele ler o `AGENTS.md` no começo.
5. Antes de dar push, revise o registro e o transcript: nada de senhas, tokens ou dados pessoais.
