#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
venv="${UV_PROJECT_ENVIRONMENT:-.venv}"
if [[ ! -x "$venv/bin/python" ]]; then
    echo "Run bash scripts/codex-setup.sh first." >&2
    exit 1
fi
exec "$venv/bin/python" -m pytest "$@"
