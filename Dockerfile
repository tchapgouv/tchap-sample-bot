ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-bookworm AS builder

ENV POETRY_VERSION=1.8.3

RUN pip install poetry==$POETRY_VERSION

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY scripts ./scripts

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --compile

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

COPY --from=builder /app /app

WORKDIR /data
ENTRYPOINT ["/app/.venv/bin/bot-entry-point"]
