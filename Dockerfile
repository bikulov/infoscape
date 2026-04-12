FROM ghcr.io/astral-sh/uv:python3.14-alpine

COPY pyproject.toml uv.lock README.md entrypoint.sh config.yaml /app/
COPY app /app/app

WORKDIR /app
ENV UV_CACHE_DIR=.uv-cache
RUN uv sync --frozen --no-dev

CMD ["sh", "entrypoint.sh"]
