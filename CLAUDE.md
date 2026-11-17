@AGENTS.md

# Específico do Claude Code

- O identificador do modelo que você está usando aparece no seu próprio contexto
  de sistema e em `/status`; use-o no registro. Se houver dúvida (ex.: fallback
  de modelo), pergunte ao humano.
- Versão da ferramenta: `claude --version`.
- O hook `.claude/hooks/salvar-transcript.sh` roda a cada resposta (`Stop`) e no
  fim da sessão (`SessionEnd`), mantendo `docs/ia/transcripts/<data>_<autor>_<session_id>.jsonl`
  atualizado. No commit final da sessão, inclua esse arquivo
  (`git add docs/ia/transcripts/`). Cite o nome dele no campo "Transcript" do registro.
- Se a sessão for compactada, consulte o próprio arquivo de registro (e não a
  memória) para saber o que já foi registrado.
