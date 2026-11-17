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

**Decisão humana:** <pendente>

## Resultado

- **Entregue:** <preencher no fim>
- **Testes:** não se aplica (análise)
- **Problemas da IA:** <preencher no fim>
- **Pendências:** decidir como tratar UC27/cadastro/cardápio, que não estão detalhados na ERS.

## Reflexão

<preencher no fim>
