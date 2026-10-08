FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so code changes do not reinstall them.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY src ./src
RUN uv sync --frozen --no-dev

RUN useradd --system --no-create-home hourtime
USER hourtime

EXPOSE 8000

# The API is reachable only through the web container, so its forwarded headers are trusted.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn hourtime.presentation.api.app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips '*'"]
