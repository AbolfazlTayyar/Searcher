# Task 3 — Summary

Initialized the backend as a `uv`-managed project and got a minimal FastAPI app running.

## What was done

- **`backend/pyproject.toml`**: filled in project metadata, runtime deps (`fastapi`, `uvicorn[standard]`, `elasticsearch[async]`, `pydantic-settings`), and a `dev` dependency group (`pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`). Configured `ruff` (line length 100, `E/F/I/UP/B` rules), `mypy` (`strict = true`), and `pytest` (`asyncio_mode = "auto"`) in the same file. Uses `hatchling` as the build backend with the package rooted at `src/searcher`.
- **`backend/src/searcher/config.py`**: `Settings(BaseSettings)` covering `ES_HOST`, `ES_INDEX_NAME`, `CORS_ORIGINS` (reads a `.env` file if present), plus a `get_settings()` cached factory intended for use as a FastAPI `Depends` in later tasks.
- **`backend/src/searcher/main.py`**: minimal `FastAPI()` app with just `GET /health` returning `{"status": "ok"}` — no CORS/exception-handler wiring yet since that's Task 9's job once there's real business logic.
- **`.env.example`** (repo root): documents `ES_HOST`, `ES_INDEX_NAME`, `CORS_ORIGINS` (as a JSON array, matching how `pydantic-settings` parses list-typed env vars).
- **`backend/README.md`**: added — `hatchling` requires the file referenced by `readme` in `pyproject.toml` to exist to build the package; this wasn't called out in the task description but was necessary for `uv sync` to succeed. Kept it to a one-line pointer at the root README.
- Removed the empty stub `backend/uv.lock` that scaffolding had left behind (an empty file isn't valid TOML), letting `uv sync` generate a real lockfile.

## Deviations from the description

- Added `pytest-asyncio` alongside `pytest`/`httpx` (not explicitly listed) since async endpoint tests in Task 10 will need it, and set `asyncio_mode = "auto"` now while touching `pyproject.toml`.
- Added `backend/README.md`, which wasn't requested, purely to satisfy `hatchling`'s build requirement (see above).

## Verification

- `uv sync` — succeeds, resolves and installs 50 packages.
- `uv run uvicorn searcher.main:app --port 8123` — starts; `curl http://127.0.0.1:8123/health` → `200 {"status":"ok"}`.
- `uv run ruff check .` — all checks passed.
- `uv run mypy src` — no issues found in 10 source files.
