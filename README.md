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
AUTH_SECRET=dev-secret-change-me-please-1234 TG_TOKEN=na_for_test UV_CACHE_DIR=.uv-cache uv run python app/main.py serve
```

`TG_TOKEN=na_for_test` keeps the bot disabled for local runs while the site still serves pages.

## Checks

```bash
./test.sh
```

## Endpoints

- `GET /healthz` for a lightweight container health check

## Docker

`docker-compose.yml` now leaves `AUTH_SECRET` empty and `TG_TOKEN` at `na_for_test` unless you set real env vars, so the web app can start without a configured Telegram bot.

Todo:
- [x] several tabs with different topics
- [x] CI + linters
- [ ] support polls
- [ ] support video?
