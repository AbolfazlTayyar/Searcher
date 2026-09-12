# Task 28 — Suggest endpoint for job_title/skill autocomplete

**Do:** `job_title`/`skill` are exact-match `.keyword` filters by design (confirmed live: `job_title=manager` → 0 results, `job_title=recruiting manager` → 1 result). Add a `GET /suggest?field=job_title|skill&prefix=&limit=` endpoint backed by a `terms` aggregation with a case-insensitive prefix regex on the `.keyword` sub-fields, and a typeahead dropdown on `Filters.tsx` so users are steered toward a value that actually matches, without changing `/search`'s exact-match semantics.

**Prompt:**
> Filter Job Title: manager (just the word, not the full title) then filter Job Title: recruiting manager (the full title, exact). Expect: if the filter field is a keyword type (as designed), manager alone should return 0 results and only the exact full string matches. This is the most likely place for a UX surprise — worth deciding if users should be told "type the exact title" or if you actually want partial matching here.
>
> [after confirming the 0-result/1-result behavior] Add autocomplete/suggest endpoint.

**Checkpoint:** `uv run pytest` — 25/25 backend tests pass (7 new for `/suggest`), `ruff check`/`ruff format --check`/`mypy` all clean. `npm run test` — 10/10 frontend tests pass (2 new for the typeahead), `npm run lint` and `npx tsc --noEmit` clean. Live-tested against the rebuilt Docker stack: `GET /suggest?field=job_title&prefix=manager` returns `["it business analysis manager","recruiting manager"]` (word-boundary, case-insensitive prefix match), and in the browser typing "manager" into the Job title filter now shows both as a dropdown; selecting "recruiting manager" fills the exact value and correctly narrows to 1 result.
