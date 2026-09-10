## What was implemented

`backend/src/searcher/search_service.py` (previously an empty stub):

- `SearchQueryError` — domain-specific exception raised on ES failure, per CLAUDE.md's centralized-error-handling convention. Wraps `elasticsearch.ApiError`/`TransportError` so raw ES exceptions never propagate past this module (a future FastAPI exception handler in `main.py`, out of scope for this task, is expected to catch it and return `{"detail": "..."}`).
- `_build_query(q, job_title, skill)` — builds the single `bool` query: `q` becomes a `multi_match` in `must` (weighted `full_name^3`, `summary`, `skills`) so relevance scoring applies, or `match_all` when `q` is absent (filter-only searches are valid). `job_title`/`skill` each become a `term` clause on their `.keyword` sub-field in `filter`, per the mapping in `ingest/mapping.py`, so they narrow results without affecting score.
- `_hit_to_profile_result(hit)` — maps a raw ES hit's `_source` into `ProfileResult` (from `models.py`), the one place `_source` dicts get crossed into the typed API boundary. Field name translation: `full_name` → `name`, `location_name` → `location`; everything else maps 1:1.
- `search_profiles(client, index_name, *, q, job_title, skill, page, page_size)` — the public entry point. Takes an already-constructed `AsyncElasticsearch` client (dependency-injected by the route layer in a later task, not instantiated here), runs the query with offset pagination (`from`/`size`), and returns a `SearchResponse`.

## Deviations from the description

- Pagination parameters (`page`, `page_size`) were added to the function signature beyond what the task described, since `SearchResponse` (from Task 7) already requires `page`/`page_size`/`total` and the ES `search` call needs `from`/`size` to produce them. Offset-based pagination was chosen over `search_after` — with ~336 total documents, deep-pagination cost is never a concern, and offset pagination is simpler for the frontend (route/`Filters.tsx` wiring) to drive from a page number.
- Used `term` (not `match`) queries on the `.keyword` filter fields, matching the CLAUDE.md instruction to filter on `.keyword` sub-fields for exact match.
- The ES client and index name are passed as parameters rather than pulled from a module-level global, consistent with CLAUDE.md's "don't reach for globals inside route handlers" — `Depends`-based wiring in `routes/search.py` and the exception handler in `main.py` are separate, not-yet-implemented tasks.

## Verification

- `uv run ruff check` / `ruff format --check` / `mypy` all pass on the new file.
- Live sanity check against a real Elasticsearch instance: started `docker compose up -d`, ran `uv run python -m searcher.ingest.ingest` (283 indexed, 53 skipped, matching the ~16% malformed-row rate CLAUDE.md documents), then called `search_profiles` directly (bypassing the not-yet-implemented route layer) with a temporary script in the scratchpad dir. Confirmed: keyword search via `multi_match` returns scored hits; `job_title` filter and `skill` filter each narrow results via `.keyword` term match; combining both filters intersects correctly; a query with no matches returns `total=0, results=[]` without error; and querying a nonexistent index raises `SearchQueryError` (wrapping the underlying `NotFoundError`) instead of leaking the raw ES exception. Script was deleted after verification.

## Files changed

- `backend/src/searcher/search_service.py` — implemented (was an empty placeholder).
