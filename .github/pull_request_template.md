## O que muda

<!-- 1 a 3 frases. O que este PR faz e por quê. -->

## Requisitos da ERS

<!-- IDs atendidos ou afetados. Ex.: UC29, RF-08, RF-12, RNF-17. "Nenhum" se for infraestrutura. -->

## Registro de IA

<!-- Links para os registros em docs/ia/sessoes/ desta tarefa. "Sem uso de IA" se for o caso. -->

- 

## Como testar

<!-- Passos para o revisor ver funcionando (telas, endpoints, dados de exemplo). -->

1. 

## Resultado dos testes locais (não há CI)

<!-- Cole o final da saída de cada comando. -->

- `cd backend && python -m pytest`: 
- `cd frontend && npm run build`: 

## Checklist

- [ ] Branch criado a partir da `main` e atualizado com ela antes do merge
- [ ] Testes do back-end e build do front-end passam localmente
- [ ] Endpoints novos têm teste em `backend/tests/`
- [ ] Nada contradiz a ERS (divergências discutidas e registradas)
- [ ] `ESTRUTURA.md` atualizado se houve pasta, arquivo importante ou regra nova
- [ ] Registro de IA da sessão commitado e linha adicionada em `docs/ia/INDICE.md`
- [ ] Sem segredos, `.env`, banco (`*.db`), `node_modules/` ou `.venv/` no diff
- [ ] Pelo menos um outro integrante revisou e aprovou
