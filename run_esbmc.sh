#!/usr/bin/env bash
set -euo pipefail


if ! command -v esbmc >/dev/null 2>&1; then
  echo "ESBMC não encontrado no PATH. Instale o ESBMC ou ajuste o PATH."
  exit 127
fi


# Define o arquivo alvo: pega o argumento 1, ou usa o padrão gerado
TARGET_FILE=${1:-build/generated_toggle.c}


if [ ! -f "$TARGET_FILE" ]; then
    echo "Erro: Arquivo $TARGET_FILE não encontrado. Rode o tradutor Python primeiro."
    exit 1
fi


echo "[1/1] Verificando $TARGET_FILE ..."
esbmc "$TARGET_FILE" --unwind 1
