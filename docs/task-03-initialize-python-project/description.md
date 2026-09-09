# Task 3 — Initialize the Python project

**Do:** `pyproject.toml` via `uv`, core dependencies (fastapi, uvicorn, elasticsearch, pydantic-settings, pytest, httpx, ruff, mypy), `config.py` with `BaseSettings`, `.env.example`.

**Prompt:**
> Initialize the backend as a uv-managed Python project per CLAUDE.md's dependency management and repo structure sections. Add dependencies: fastapi, uvicorn, elasticsearch (async client), pydantic-settings, and dev dependencies pytest, httpx, ruff, mypy. Create `config.py` with a Pydantic `BaseSettings` class covering `ES_HOST`, `ES_INDEX_NAME`, and `CORS_ORIGINS`. Create `.env.example` documenting these variables. Create a minimal `main.py` with a FastAPI app and a `/health` endpoint only — no business logic yet.

**Checkpoint:** `uv sync` succeeds; `uv run uvicorn searcher.main:app --reload` starts; `GET /health` returns 200.
