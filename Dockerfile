FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# RUN --mount=type=cache,target=/root/.cache/uv \
#     --mount=type=bind,source=uv.lock,target=uv.lock \
#     --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
#     uv sync --frozen --no-install-project \
COPY pyproject.toml /app/

RUN uv lock && uv sync --frozen --no-cache

COPY . /app

# RUN --mount=type=cache,target=/root/.cache/uv \
#     uv sync --frozen \

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Health check natif Docker (compatible avec urllib.request)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
