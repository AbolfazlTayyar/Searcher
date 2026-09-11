FROM python:3.11-slim AS builder

RUN pip install --no-cache-dir uv

WORKDIR /app/backend

# Dependencies are synced before the rest of the source is copied so this
# layer is cache-hit as long as pyproject.toml/uv.lock haven't changed.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev


FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY --from=builder /app/backend/.venv .venv
COPY --from=builder /app/backend/src src
COPY --from=builder /app/backend/pyproject.toml .

ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONPATH="/app/backend/src"

EXPOSE 8000

CMD ["uvicorn", "searcher.main:app", "--host", "0.0.0.0", "--port", "8000"]
