#!/usr/bin/env bash
# Sobe o BurguerJá inteiro com um comando: instala o que faltar, prepara o banco
# e roda a API (porta 8000) e o front-end (porta 5173) juntos. Ctrl+C para os dois.
# Sem banco local, cria a base compartilhada (backend/scripts/base_compartilhada.py),
# igual para todo o grupo; com banco, usa o que já existe.
#
# Uso: bash scripts/rodar.sh [opções]
#   --resetar-banco  apaga o banco local e recria a base compartilhada
#   --banco-vazio    apaga o banco local e sobe sem nenhum dado
#   --testes         só roda os testes da API e o build do front-end, e sai
#   --ajuda          mostra esta ajuda
#
# Funciona no Linux, no Mac e no Git Bash do Windows.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$RAIZ/backend"
FRONTEND="$RAIZ/frontend"
PORTA_API=8000   # o proxy do Vite (frontend/vite.config.ts) aponta para esta porta
PORTA_WEB=5173

BANCO=manter   # manter | base | vazio
SO_TESTES=0

for arg in "$@"; do
  case "$arg" in
    --resetar-banco) BANCO=base ;;
    --banco-vazio) BANCO=vazio ;;
    --testes) SO_TESTES=1 ;;
    -h|--ajuda|--help) sed -n '2,14p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Opção desconhecida: $arg (use --ajuda)" >&2; exit 2 ;;
  esac
done

passo() { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
erro() { printf '\033[1;31mErro: %s\033[0m\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- requisitos
passo "Conferindo Python 3.11+ e Node.js 20+"
PYTHON=""
for cand in python3 python py; do
  if command -v "$cand" >/dev/null 2>&1 \
     && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    PYTHON="$cand"; break
  fi
done
[ -n "$PYTHON" ] || erro "Python 3.11 ou mais novo não encontrado."
command -v node >/dev/null 2>&1 || erro "Node.js não encontrado."
command -v npm >/dev/null 2>&1 || erro "npm não encontrado."
NODE_MAIOR="$(node -p 'process.versions.node.split(".")[0]')"
[ "$NODE_MAIOR" -ge 20 ] || erro "Node.js 20+ necessário (encontrado $(node --version))."
echo "$("$PYTHON" --version) · Node $(node --version)"

# ---------------------------------------------------------------- back-end
passo "Back-end: ambiente virtual e dependências"
if [ ! -d "$BACKEND/.venv" ]; then
  "$PYTHON" -m venv "$BACKEND/.venv"
fi
if [ -x "$BACKEND/.venv/bin/python" ]; then
  PY="$BACKEND/.venv/bin/python"
else
  PY="$BACKEND/.venv/Scripts/python.exe"   # Windows
fi
[ -x "$PY" ] || erro "Ambiente virtual quebrado; apague backend/.venv e rode de novo."

# Só reinstala quando o requirements.txt mudou desde a última instalação.
MARCA="$BACKEND/.venv/.requirements-instalado"
if [ ! -f "$MARCA" ] || ! cmp -s "$BACKEND/requirements.txt" "$MARCA"; then
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet -r "$BACKEND/requirements.txt"
  cp "$BACKEND/requirements.txt" "$MARCA"
  echo "Dependências instaladas."
else
  echo "Dependências já instaladas."
fi

# ---------------------------------------------------------------- front-end
passo "Front-end: dependências"
# O npm grava node_modules/.package-lock.json; se o package-lock.json for mais
# novo que ele, alguém mudou as dependências.
if [ ! -f "$FRONTEND/node_modules/.package-lock.json" ] \
   || [ "$FRONTEND/package-lock.json" -nt "$FRONTEND/node_modules/.package-lock.json" ]; then
  (cd "$FRONTEND" && npm install --no-audit --no-fund)
else
  echo "Dependências já instaladas."
fi

# ---------------------------------------------------------------- só testes
if [ "$SO_TESTES" = 1 ]; then
  passo "Testes da API"
  (cd "$BACKEND" && "$PY" -m pytest -q)
  passo "Build do front-end"
  (cd "$FRONTEND" && npm run build)
  passo "Tudo certo"
  exit 0
fi

# ---------------------------------------------------------------- banco
BANCO_ARQUIVO="${BURGUERJA_DB:-$BACKEND/burguerja.db}"
if [ "$BANCO" = manter ] && [ ! -f "$BANCO_ARQUIVO" ]; then
  BANCO=base   # primeira vez: começa da base compartilhada
fi

case "$BANCO" in
  base)
    passo "Recriando a base compartilhada"
    (cd "$BACKEND" && "$PY" -m scripts.base_compartilhada) || erro "Não deu para criar a base compartilhada."
    ;;
  vazio)
    passo "Apagando o banco local (vai subir vazio)"
    rm -f -- "$BANCO_ARQUIVO"
    ;;
  manter)
    passo "Usando o banco local que já existe ($BANCO_ARQUIVO)"
    echo "Para voltar à base compartilhada: bash scripts/rodar.sh --resetar-banco"
    ;;
esac

# ---------------------------------------------------------------- subir
porta_ocupada() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
porta_ocupada "$PORTA_API" && erro "A porta $PORTA_API já está em uso (API rodando em outro terminal?)."
porta_ocupada "$PORTA_WEB" && erro "A porta $PORTA_WEB já está em uso (front-end rodando em outro terminal?)."

# Prefixa cada linha de log com o nome do serviço.
prefixo() { while IFS= read -r linha; do printf '%s %s\n' "$1" "$linha"; done; }

passo "Subindo a API e o front-end (Ctrl+C para parar)"
(cd "$BACKEND" && exec "$PY" -m uvicorn app.main:app --reload --port "$PORTA_API" \
  > >(prefixo "[api]") 2>&1) &
PID_API=$!
(cd "$FRONTEND" && exec node node_modules/vite/bin/vite.js --port "$PORTA_WEB" --strictPort \
  > >(prefixo "[web]") 2>&1) &
PID_WEB=$!

parar() {
  trap - INT TERM EXIT
  echo
  echo "Parando..."
  kill "$PID_API" "$PID_WEB" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap 'parar; exit 0' INT TERM   # Ctrl+C: para os dois e sai sem erro
trap parar EXIT                   # um serviço caiu: para o outro também

# Espera a API responder antes de mostrar os endereços.
for _ in $(seq 1 30); do
  if (exec 3<>"/dev/tcp/127.0.0.1/$PORTA_API") 2>/dev/null; then break; fi
  sleep 1
done

printf '\n\033[1;32mPronto!\033[0m\n'
echo "  App:      http://localhost:$PORTA_WEB"
echo "  API docs: http://localhost:$PORTA_API/docs"
[ "$BANCO" = vazio ] || echo "  Logins:   demo@, ana@, bruno@ ou carla@burguerja.com, senha demo1234"
echo

# Fica rodando até um dos dois cair ou o usuário apertar Ctrl+C.
while kill -0 "$PID_API" 2>/dev/null && kill -0 "$PID_WEB" 2>/dev/null; do
  sleep 1
done
echo "Um dos serviços parou; veja o log acima."
echo "Se a API reclamou de esquema antigo do banco, rode: bash scripts/rodar.sh --resetar-banco"
exit 1
