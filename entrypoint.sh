#!/usr/bin/env bash
set -euo pipefail

mkdir -p data

uv run python app/main.py fetch &
fetch_pid=$!

cleanup() {
    kill "$fetch_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

uv run python app/main.py serve
