#!/usr/bin/env bash
set -euo pipefail

directorio_raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
interprete_base="${PYTHON:-python3}"
cd "$directorio_raiz"

"$interprete_base" -m venv .venv
"$directorio_raiz/.venv/bin/python" -m pip install --upgrade pip
"$directorio_raiz/.venv/bin/python" -m pip install -e ".[dev,analisis]"
