#!/usr/bin/env bash

set -euo pipefail

export AUTH_SECRET="${AUTH_SECRET:-0123456789abcdef0123456789abcdef}"
export TG_TOKEN="${TG_TOKEN:-na_for_test}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"
export FLAKE8_EXCLUDE="${FLAKE8_EXCLUDE:-.venv,app/.venv,__pycache__}"

uv run mypy app
uv run pytest -vvv
uv run flake8 --exclude="$FLAKE8_EXCLUDE" --count --select=E9,F63,F7,F82 --show-source --statistics app
uv run flake8 --exclude="$FLAKE8_EXCLUDE" --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics app
