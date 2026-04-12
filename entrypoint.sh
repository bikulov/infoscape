#!/usr/bin/env bash
set -euo pipefail

mkdir -p data

uv run python main.py fetch &
uv run python main.py serve
