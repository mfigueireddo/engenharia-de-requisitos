# BurguerJá: preparação do projeto com IA

**Matheus Figueiredo · 17/11/2026 · Claude Code (claude-opus-5-5)**

## Objetivo

- Preparar o repositório para o grupo implementar a ERS com IA
- Documentar o uso de IA desde o primeiro dia

## 1. Registro do uso de IA

- Um registro por sessão em `docs/ia/sessoes/`, com:
  - ferramenta e modelo
  - prompts na íntegra
  - resumo das saídas
  - decisões humanas
- Registro feito a cada prompt, para que nada se perca em sessões longas
- Transcript bruto salvo automaticamente no Claude Code, com e-mails e tokens mascarados
- Índice geral em `docs/ia/INDICE.md`

## 2. Instruções para os agentes

- `AGENTS.md`: uma única fonte de regras para Claude, Codex, Cursor, Copilot e Gemini
- A ERS é a fonte de verdade. Se houver dúvida ou conflito, o agente pergunta
- Rastreabilidade: os commits e os testes citam RF, RNF, RN e UC
- ERS convertida para Markdown (`docs/srs/`), para os agentes conseguirem ler

## 3. Estrutura base do sistema

- Stack da seção 2.5 da ERS: **React + TypeScript**, **FastAPI** e **SQLite**
- Página de teste que salva e lê um dado: front-end → API → banco ✅
- README de execução para Linux, Mac e Windows
- `ESTRUTURA.md`: mapa de pastas e regras de organização

## 4. Fluxo de trabalho do grupo

- Um branch por tarefa, e merge na `main` só por pull request
- Sem CI: os testes rodam localmente e o resultado vai na descrição do PR
- Modelo de PR com checklist (ERS, registro de IA, testes)
- Lembrete para remover o esboço de teste quando a primeira funcionalidade real for entregue

## Uso de IA nesta sessão

- 3 sessões registradas, cerca de 8 prompts
- A IA fez perguntas antes de agir e as decisões de formato ficaram com o humano
- 1 erro da IA, encontrado nos testes e corrigido: o nome do autor perdia os acentos

## Próximos passos

- O grupo começa as funcionalidades da ERS (UC28 a UC33)
- Decidir sobre ORM e migrações do banco
