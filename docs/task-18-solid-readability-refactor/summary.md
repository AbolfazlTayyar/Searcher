## What was done

Reviewed every module in `backend/src/searcher` and every file in `frontend/src` against the SOLID/readability conventions in CLAUDE.md: single responsibility per function/module, clear naming, small functions, no unnecessary indirection.

Both sides of the codebase were already in good shape — a result of the prior comment-cleanup and UI-redesign passes (tasks 16–17) having kept things tidy along the way. Route handlers stay thin and delegate to `search_service.py`; query-building, response-shaping, and ES execution are each their own function; `ingest/parse.py` and `ingest/ingest.py` cleanly separate "parse a row" from "recreate the index and bulk-load it"; dependency injection for the ES client and settings is already in place; frontend components are small, typed, and presentational, with API calls isolated in `src/api/`.

The one genuine SOLID violation found: **`_configure_file_logging` was duplicated verbatim** in both `backend/src/searcher/ingest/parse.py` and `backend/src/searcher/ingest/ingest.py` — the same "attach a file handler to `backend/ingest.log`, once per process" responsibility implemented twice, including a duplicated `_LOG_PATH` constant. This violates single responsibility at the module level (each module owned a copy of a concern that belongs to neither of them specifically) and risked the two copies drifting apart.

## Change made

- Added `backend/src/searcher/ingest/logging_setup.py`, exporting `LOG_PATH` and `configure_file_logging(logger)`.
- `parse.py` and `ingest.py` now both import and call `configure_file_logging(logger)` instead of each defining their own `_configure_file_logging()`/`_LOG_PATH`.

No other files were changed — everything else already met the bar.

## Deviations from the description

None. The description anticipated the refactor might touch multiple files across both backend and frontend; in practice only the logging duplication warranted a change.

## Verification

- `uv run ruff check src/` — all checks passed.
- `uv run mypy src/` — no issues found.
- `uv run pytest` — 4/9 tests pass (the same 4 that passed before the change); the other 5 require a live Elasticsearch instance and fail with a connection error both before and after this refactor, unrelated to it.
- Manually ran `parse_profiles` against the dataset directly: still parses 283 clean records, skips 53 malformed rows, and logs to `backend/ingest.log` exactly as before.
- `npm run test -- --run` (frontend) — 8/8 tests pass; frontend code was unchanged.

## Files changed

- `backend/src/searcher/ingest/logging_setup.py` (new)
- `backend/src/searcher/ingest/parse.py`
- `backend/src/searcher/ingest/ingest.py`
