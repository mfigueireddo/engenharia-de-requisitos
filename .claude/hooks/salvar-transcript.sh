#!/usr/bin/env bash
# Hook do Claude Code (Stop e SessionEnd): copia o transcript bruto da sessão
# para docs/ia/transcripts/, mascarando e-mails e tokens. Roda após cada
# resposta, então o arquivo está sempre atualizado; quem commita é o agente
# (ou a pessoa) junto com o registro da sessão.
set -u
entrada=$(cat)

campo() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$entrada" | jq -r ".$1 // empty"
  else
    printf '%s' "$entrada" | sed -nE "s/.*\"$1\" *: *\"([^\"]*)\".*/\1/p" | sed 's/\\\\/\\/g'
  fi
}

sessao=$(campo session_id)
origem=$(campo transcript_path)
[ -z "$sessao" ] || [ -z "$origem" ] || [ ! -f "$origem" ] && exit 0

raiz="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
destdir="$raiz/docs/ia/transcripts"
mkdir -p "$destdir"

# Reaproveita o arquivo se a sessão já tiver um (sessões que viram o dia).
destino=$(ls "$destdir"/*_"$sessao".jsonl 2>/dev/null | head -1)
if [ -z "$destino" ]; then
  autor=$(cd "$raiz" && bash scripts/ia/autor.sh)
  destino="$destdir/$(date +%Y-%m-%d)_${autor}_${sessao}.jsonl"
fi

sed -E \
  -e 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/[email-removido]/g' \
  -e 's/(sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,})/[token-removido]/g' \
  "$origem" > "$destino.tmp" && mv "$destino.tmp" "$destino"
exit 0
