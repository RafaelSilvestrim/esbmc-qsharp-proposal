#!/usr/bin/env bash
# Convenience wrapper: verify a generated C harness with the flags matching
# its amplitude encoding.
#
# Usage:
#   ./run_esbmc.sh <harness.c> [float|exact]
#
# Defaults to the 'float' encoding (IEEE 754, --floatbv). The full pipeline
# (transpile + verify + signed evidence) is governance/vbe_gate.py.
set -euo pipefail

ESBMC_BIN="${ESBMC:-esbmc}"

if ! command -v "$ESBMC_BIN" >/dev/null 2>&1; then
  echo "error: ESBMC not found on PATH (or set the ESBMC env var)." >&2
  echo "Releases: https://github.com/esbmc/esbmc/releases" >&2
  exit 127
fi

TARGET_FILE=${1:?usage: ./run_esbmc.sh <harness.c> [float|exact]}
ENCODING=${2:-float}

if [ ! -f "$TARGET_FILE" ]; then
  echo "error: $TARGET_FILE not found. Generate it first, e.g.:" >&2
  echo "  python3 translator/qsharp2c.py qsharp/TestHHIdentity.qs $TARGET_FILE" >&2
  exit 1
fi

case "$ENCODING" in
  float) FLAGS="--unwind 1 --z3 --floatbv" ;;
  exact) FLAGS="--unwind 16 --z3" ;;
  *) echo "error: unknown encoding '$ENCODING' (use float or exact)" >&2; exit 2 ;;
esac

echo "[verify] $ESBMC_BIN $TARGET_FILE $FLAGS"
# shellcheck disable=SC2086
exec "$ESBMC_BIN" "$TARGET_FILE" $FLAGS
