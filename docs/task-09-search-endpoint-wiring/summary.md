## What was implemented

- **`dependencies.py` (new file, not in the original repo skeleton listing):** a `get_es_client` provider plus an `ESClientDep` type alias, reading the `AsyncElasticsearch` client off `app.state`. Added as a small separate module so `routes/search.py` doesn't need to import `main.py` (which mounts the router) to get the client — avoids a circular import while still following the "DI via `Depends`, no globals in route handlers" convention.
- **`routes/search.py`:** `GET /search` accepting `q`, `job_title`, `skill` (all optional strings) and `page`/`page_size` (`Query(..., ge=1)`, `page_size` also capped `le=100`) as Pydantic-validated query params. Pulls the ES client via `ESClientDep` and `Settings` via `Depends(get_settings)`, then delegates entirely to `search_service.search_profiles`. No query-building logic in the route.
- **`main.py`:**
  - A `lifespan` context manager creates the single `AsyncElasticsearch` client at startup (stored on `app.state.es_client`) and closes it at shutdown, instead of instantiating at import time.
  - `CORSMiddleware` restricted to `settings.CORS_ORIGINS` (the frontend dev origin, `http://localhost:5173` by default), `GET`-only.
  - An `@app.exception_handler(SearchQueryError)` handler returning `{"detail": "..."}` with HTTP 502, so ES failures never leak the library's native error shape to the client.
  - The search router is mounted via `include_router`.

## Verification (manual, per the task's checkpoint)

With `docker compose` Elasticsearch up (283 already-indexed profiles) and `uv run uvicorn searcher.main:app` running:

- `GET /search?q=engineer` — returns scored, relevant results.
- `GET /search?job_title=recruiting+manager` — returns only matching profiles.
- `GET /search?skill=leadership` — returns only matching profiles.
- `GET /search?job_title=recruiting+manager&skill=leadership` — combined filter narrows correctly.
- `GET /search?q=zzzznotarealtermxyz` — `{"results": [], "total": 0, "page": 1, "page_size": 20}`, not an error.
- CORS: response to a request with `Origin: http://localhost:5173` carries `access-control-allow-origin: http://localhost:5173`.
- Exception handler: stopped the ES container mid-request — `GET /search?q=engineer` returned HTTP 502 with `{"detail": "Search query failed"}` instead of an ES traceback or native error body.

`uv run ruff check src/`, `uv run ruff format --check src/`, and `uv run mypy src/` all pass clean.

## Deviations from the description

- Added `dependencies.py`, which isn't in CLAUDE.md's repo-structure listing. That listing is illustrative ("e.g.") rather than exhaustive, and the alternative — defining the ES-client dependency function inside `main.py` and importing it from `routes/search.py` — would have created a circular import (`main.py` imports the router, the router would import back from `main.py`). No other deviations.
