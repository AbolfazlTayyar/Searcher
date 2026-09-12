# Task 26 — Prefix search / partial name match fix

## What was wrong

Searching `q=jose` returned zero results even though "joseph holland" exists
in the index. `search_service.py`'s `_build_query` sent the keyword through a
`multi_match` query with the default `type: best_fields`, which requires a
whole-token match against the standard analyzer's tokens. "Joseph" indexes as
the single token `joseph`; `jose` is a prefix of that token, not the token
itself, so `best_fields` never matched it. The same gap applied to `summary`
and `skills` — any partial word typed against `q` failed to match unless it
happened to equal a full token.

## Fix

Changed the `multi_match` query in `_build_query` (`search_service.py`) to
`type: "bool_prefix"`, which matches the last (or only) term in the query as
a prefix against tokens in each of `_SEARCH_FIELDS` (`full_name^3`,
`summary`, `skills`), combined via `should` across fields. No mapping change
was needed — `bool_prefix` works against plain `text` fields, just less
efficiently than a dedicated `search_as_you_type` field type would for a much
larger dataset (irrelevant at this dataset's ~60-doc scale).

## Verification

- `uv run pytest tests/test_search.py` — all 8 existing tests still pass
  unchanged (no regression to exact/whole-word search behavior).
- Rebuilt the backend Docker image (`docker compose up --build -d backend`)
  and hit the live containerized API: `GET /search?q=jose` now returns
  "joseph holland" and other "joseph"-named profiles, confirmed via
  `curl http://localhost:8000/search?q=jose`.
- Cross-checked directly against Elasticsearch
  (`GET /linkedin_profiles/_search?q=full_name:Joseph`) to confirm the
  underlying data was present all along — this was a query-construction bug,
  not a missing/malformed ingestion row.

## Deviations from a typical task write-up

This was a reactive bug-fix task, not one pre-planned in `TASKS.md` before
the session — it's recorded here after the fact per the project's
documentation convention, with `description.md` holding the user's original
report verbatim rather than a scripted prompt.
