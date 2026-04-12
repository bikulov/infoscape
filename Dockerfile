FROM ghcr.io/astral-sh/uv:python3.14-alpine

COPY app /app
COPY entrypoint.sh config.yaml /app/

WORKDIR /app
ENV UV_CACHE_DIR=.uv-cache
RUN uv sync --frozen --no-dev

CMD ["sh", "entrypoint.sh"]
