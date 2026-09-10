## What was implemented

- `backend/tests/conftest.py` — session-scoped fixtures that stand up a real,
  disposable Elasticsearch index (`linkedin_profiles_test_<random>`), built
  from the same `PROFILE_INDEX_MAPPING`/`PROFILE_INDEX_SETTINGS` the real
  ingestion script uses, seeded with four fixed fixture profiles chosen so
  each test scenario has an exact, non-overlapping expected result. A
  function-scoped `client` fixture wires an `httpx.AsyncClient` (via
  `ASGITransport`) to the FastAPI app with `get_es_client`/`get_settings`
  overridden to point at the test index — the app's own `lifespan` startup is
  bypassed since it would otherwise open a client against the real
  `ES_INDEX_NAME`. The index is dropped and the ES client closed in a
  `finally` block after the session.
- `backend/tests/test_search.py` — five tests against `GET /search`:
  keyword-only search, `job_title` filter alone, `skill` filter alone, both
  filters combined, and a query with no matches. Each asserts on the exact
  set of profile names returned (not just a count), so a test would catch a
  filter behaving as `OR` instead of `AND`, or a keyword match bleeding into
  the wrong field.

## Deviations from the description

- The description didn't specify a fixture strategy. Went with a small,
  fixed, in-memory document set indexed directly via `client.index()` (not
  `parse.py`/the real dataset) so each test's expected result is exact and
  the tests don't depend on `data/300_user_linkedin.txt` staying unchanged.
- Had to add `asyncio_default_fixture_loop_scope = "session"` and
  `asyncio_default_test_loop_scope = "session"` to `pyproject.toml`'s pytest
  config. Without it, pytest-asyncio 1.x runs each test in its own event
  loop while the session-scoped ES client fixture is bound to the first
  loop, which surfaces as `RuntimeError: Timeout context manager should be
  used inside a task` from `aiohttp` on the second test onward.

## Files created/changed

- `backend/tests/conftest.py` (new)
- `backend/tests/test_search.py` (new)
- `backend/pyproject.toml` (added session-scoped asyncio loop config)
