# Task 25 summary — Case-insensitive filter search fix

## What was found

Tested case sensitivity against the live, running Docker stack (real ES index, ~60 documents) rather than just reasoning about the mapping:

- **`q` keyword search**: already case-insensitive. `q=training`, `q=Training`, and `q=TRAINING` all returned the identical single result. This works because `multi_match` targets `text`-typed fields (`full_name`, `summary`, `skills`), which go through the standard analyzer — it lowercases both the indexed tokens and the query string.
- **`job_title` / `skill` filters**: case-sensitive. `job_title=recruiting manager` matched, but `job_title=Recruiting Manager` and `job_title=RECRUITING MANAGER` returned zero results. These filters run as `term` queries against `.keyword` sub-fields, which are unanalyzed — ES compares the raw bytes, so casing must match exactly.

## Fix

`backend/src/searcher/search_service.py`: added ES's `case_insensitive: true` option (available since 7.10, no reindex needed) to both filter clauses:

```python
{"term": {"job_title.keyword": {"value": job_title, "case_insensitive": True}}}
{"term": {"skills.keyword": {"value": skill, "case_insensitive": True}}}
```

This keeps the filters exact-match on the whole field value (unlike switching to `match`, which would tokenize and allow partial/substring hits) while no longer requiring callers to match the indexed casing.

## Verification

- Rebuilt and restarted the `backend` container (`docker compose up -d --build backend`).
- Re-tested live: `job_title=Recruiting Manager`, `RECRUITING MANAGER`, and `recruiting manager` all now return the same match; `skill=Leadership` now matches the lowercase-indexed `"leadership"` skill; a genuinely non-matching filter value (`nonexistent title xyz`) still correctly returns zero results (case-insensitivity didn't loosen the match into a partial/fuzzy one).
- Added 3 regression tests to `backend/tests/test_search.py`: `test_keyword_search_is_case_insensitive`, `test_job_title_filter_is_case_insensitive`, `test_skill_filter_is_case_insensitive`.
- Full backend suite: `uv run pytest` — 15/15 passed. `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy src` all clean (one line-length fix needed after the initial edit).

## Files changed

- `backend/src/searcher/search_service.py` — case-insensitive `term` filters.
- `backend/tests/test_search.py` — 3 new tests.
- `.claude/CLAUDE.md` — not changed; no documented convention contradicted this fix.

## Deviations

None — this was investigate-and-fix work triggered by a one-line prompt, with no separate plan needed given the small, well-scoped change.
