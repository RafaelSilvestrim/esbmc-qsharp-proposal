#!/usr/bin/env bash
set -euo pipefail

if ! command -v esbmc >/dev/null 2>&1; then
  echo "ESBMC não encontrado no PATH. Instale o ESBMC ou ajuste o PATH."
  exit 127
fi

echo "[1/1] Verificando toggle_twice.c ..."
esbmc classical/toggle_twice.c --unwind 1 --floatbv --incremental --no-div-by-zero-check
