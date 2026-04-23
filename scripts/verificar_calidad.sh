#!/usr/bin/env bash
set -euo pipefail

directorio_raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$directorio_raiz"

if [[ -x "$directorio_raiz/.venv/bin/python" ]]; then
  interprete="$directorio_raiz/.venv/bin/python"
else
  interprete="${PYTHON:-python3}"
fi

"$interprete" -m ruff format --check .
"$interprete" -m ruff check .
"$interprete" -m mypy src
"$interprete" -m pytest
