News aggregator (currently from telegram channels only)

![tests](https://github.com/bikulov/infoscape/actions/workflows/tests.yaml/badge.svg)

## Setup

```bash
UV_CACHE_DIR=.uv-cache uv venv
UV_CACHE_DIR=.uv-cache uv sync --dev
```

## Run

```bash
mkdir -p data
AUTH_SECRET=secret TG_TOKEN=na_for_test UV_CACHE_DIR=.uv-cache uv run python app/main.py serve
```

## Checks

```bash
./test.sh
```

Todo:
- [x] several tabs with different topics
- [x] CI + linters
- [ ] support polls
- [ ] support video?
