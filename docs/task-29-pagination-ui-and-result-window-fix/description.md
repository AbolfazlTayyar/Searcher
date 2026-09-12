# Task 29 — Pagination UI and result-window edge case fix

**Do:** QA pagination behavior against the live stack. Found two gaps: (1) the frontend never exposed a way to reach page 2+ despite the backend already supporting `page`/`page_size` — a query with more than `page_size` results silently truncated to the first page with no way to see the rest; (2) a page number whose `from + size` exceeds Elasticsearch's default `index.max_result_window` (10,000) surfaced as a raw 502 instead of a graceful empty page. Fixed both: added a `Pagination.tsx` Previous/Next control wired through `App.tsx`/`ResultsList.tsx` (resetting to page 1 on any filter/keyword change), and guarded `search_profiles` in `search_service.py` to fall back to a `count`-only query when the ES window limit would be exceeded, returning an empty results page with the real `total` instead of erroring.

**Prompt:**
> check pagination edge cases too
>
> [after the audit surfaced the missing pagination UI and the ES result-window bug] yes, fix both

**Checkpoint:** `uv run pytest` — 10/10 backend search tests pass (1 new: `test_page_past_es_result_window_returns_empty_results_not_an_error`), `ruff check`/`ruff format --check`/`mypy` all clean. `npx vitest run` — 15/15 frontend tests pass (3 new for `Pagination.tsx`, 2 updated in `ResultsList.test.tsx`), `tsc --noEmit`/`eslint` clean. Live-tested against the rebuilt Docker stack: `GET /search?page=999` and `GET /search?page=501&page_size=20` now return `200` with empty results and the correct `total` instead of `502`; in the browser, Next/Previous correctly page through the 31-result unfiltered set, and changing the skill filter while on page 2 resets to page 1.
