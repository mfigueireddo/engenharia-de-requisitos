#!/usr/bin/env bash
# Imprime o identificador do autor usado nos nomes de arquivo de docs/ia/.
# Vem de `git config user.name` (ou da variável IA_AUTOR, se definida),
# em minúsculas, sem acentos e com hífens. Ex.: "João Marcelo" -> joao-marcelo
nome="${IA_AUTOR:-$(git config user.name 2>/dev/null)}"
[ -z "$nome" ] && nome="desconhecido"
printf '%s' "$nome" | sed -E \
  -e 's/(á|à|â|ã|ä|Á|À|Â|Ã|Ä)/a/g' -e 's/(é|è|ê|ë|É|È|Ê|Ë)/e/g' \
  -e 's/(í|ì|î|ï|Í|Ì|Î|Ï)/i/g' -e 's/(ó|ò|ô|õ|ö|Ó|Ò|Ô|Õ|Ö)/o/g' \
  -e 's/(ú|ù|û|ü|Ú|Ù|Û|Ü)/u/g' -e 's/(ç|Ç)/c/g' -e 's/(ñ|Ñ)/n/g' \
  | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
echo
