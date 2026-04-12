#!/usr/bin/env bash

set -euo pipefail

export AUTH_SECRET="${AUTH_SECRET:-0123456789abcdef0123456789abcdef}"
export TG_TOKEN="${TG_TOKEN:-na_for_test}"
export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"

uv run mypy app
uv run pytest -vvv
uv run flake8 --count --select=E9,F63,F7,F82 --show-source --statistics app
uv run flake8 --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics app
