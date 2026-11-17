# Sessão: estrutura de registro do uso de IA

## Metadados

| Campo | Valor |
|---|---|
| Autor (humano) | Matheus Figueiredo (no container de nuvem o `git config user.name` era "Claude"; o autor foi definido com `IA_AUTOR`) |
| Data | 2026-11-17 |
| Duração aproximada | 30 min |
| Ferramenta (harness) e versão | Claude Code 2.1.326 (sessão na nuvem, claude.ai/code) |
| Modelo (ID exato) | claude-opus-5-5 |
| Modo de uso | agente |
| Branch | main |
| Commits | ver `git log` do commit "Adiciona estrutura de registro do uso de IA" |
| Transcript | `docs/ia/transcripts/2026-11-17_matheus-figueiredo_aef3e293-c8dd-5fc7-9fb8-fed79cb995fb.jsonl` |
| Sessão anterior | — |

## Objetivo

Planejar e criar a estrutura para documentar o uso de IA na implementação da ERS
(pedido do professor): instruções para os agentes (`AGENTS.md`, `CLAUDE.md`),
template de registro por sessão, índice e captura automática de transcripts.

**Requisitos da ERS relacionados:** nenhum (infraestrutura do processo).

## Interações

### 1

**Prompt (literal):**

```text
Nesse repositório, a gente tem um documento que deve ser utilizado como verdade. Lá tem muitas informações sobre o nosso projeto. O que eu quero fazer é... A disciplina ela tem a intenção de implementar o que está descrito no documento com o uso de IA. Só que o professor, ele quer que a gente documente o uso da IA. Ele quer que a gente coloque, por exemplo, os prompts utilizados, qual modelo utilizou, quer que a gente distribua isso. O que eu quero fazer contigo é que você me faça umas perguntas, a gente pode analisar junto um agents.md e um cloud.md para que o agente, cada pessoa, tenha instruções específicas para fazer as coisas. O que eu estou pensando é, por exemplo, para a sessão de cada uma das pessoas, ao final dela sempre registrar tudo num arquivo de texto, onde lá ou no Markdown, onde nesse arquivo a gente teria, por exemplo, qual modelo foi utilizado, qual a harness utilizada, também qual foi os prompts utilizados, coisas de entrada e saída de resultado de cada prompt, pra gente ter uma noção disso e conseguir mandar pro professor. Me ajuda a planejar isso aí.
```

**Saída (resumo):** a IA leu o `srs-pt.docx` e fez 4 perguntas de múltipla escolha.
Respostas: o grupo usa todas as ferramentas (Claude Code, Codex/Cursor/Copilot,
chat web, Gemini CLI); prompt literal + resumo da saída; um arquivo por sessão;
hook do Claude Code para salvar o transcript bruto. Depois a IA propôs o plano:
`AGENTS.md` como fonte única das regras, `CLAUDE.md` importando-o, ERS convertida
para Markdown, registro incremental (para não perder prompts na compactação de
contexto), campos do registro, índice e pontos de atenção.

**Arquivos alterados:** nenhum.

**Decisão humana:** aceito. Transcripts brutos entram no repositório; nomes de
arquivo usam o nome do git.

### 2

**Prompt (literal):**

```text
Transcriptos brutos entram no repositório os nomes dos arquivos vão usar o nome do Git.

Dá commit e push na main
```

**Saída (resumo):** a IA converteu a ERS com pandoc (`docs/srs/srs-pt.md` +
figuras), criou `AGENTS.md`, `CLAUDE.md`, `docs/ia/` (README, template, índice,
este registro), `scripts/ia/autor.sh` (nome do git → slug sem acentos) e o hook
`.claude/hooks/salvar-transcript.sh` (eventos Stop e SessionEnd, mascarando
e-mails e tokens). Testou o slug com nomes acentuados e o hook com o transcript
real. Bug encontrado e corrigido: `iconv` sem locale UTF-8 trocava acentos por
`?`; foi substituído por `sed`.

**Arquivos alterados:** `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`,
`.claude/hooks/salvar-transcript.sh`, `scripts/ia/autor.sh`, `docs/srs/*`, `docs/ia/*`.

**Decisão humana:** pendente de revisão.

## Resultado

- **Entregue:** estrutura de registro completa, commitada na `main`.
- **Testes:** `autor.sh` com "João Marcelo Onofre" → `joao-marcelo-onofre` e "Paulo Henrique Monção" com `LC_ALL=C` → `paulo-henrique-moncao`; hook executado manualmente com o transcript desta sessão.
- **Problemas da IA:** primeira versão do slug quebrava acentos (corrigido).
- **Pendências:** cada integrante conferir o `git config user.name`; testar o hook no Windows (Git Bash).

## Reflexão

Fazer as perguntas antes de escrever evitou retrabalho nas decisões de formato.
O hook só passa a valer em sessões novas (o desta sessão foi rodado à mão).
