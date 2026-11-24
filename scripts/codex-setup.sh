#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python_bin="${CODEX_PYTHON:-python3}"
if ! "$python_bin" -c 'import sys; sys.exit(sys.version_info < (3, 11))'; then
    echo "Select Python 3.11+ or set CODEX_PYTHON to its executable." >&2
    exit 1
fi

if command -v uv >/dev/null 2>&1; then
    uv_bin="$(command -v uv)"
else
    uv_bin="$PWD/.codex-tools/uv/bin/uv"
    if [[ ! -x "$uv_bin" ]]; then
        "$python_bin" -m venv .codex-tools/uv
        .codex-tools/uv/bin/python -m pip install --disable-pip-version-check uv==0.12.10
    fi
fi

"$uv_bin" sync --locked --dev --no-python-downloads --system-certs --python "$python_bin"
