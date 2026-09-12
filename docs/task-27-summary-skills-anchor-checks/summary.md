# Task 27 summary — Anchor checks for `summary`/`skills` column-shift leaks

## What was implemented

Extended the per-field "anchor" validation in `backend/src/searcher/ingest/parse.py` (added in the earlier browser-QA ingestion fix) to cover two more shift symptoms that were still slipping through:

- **`summary`**: added `_BARE_NUMBER_RE` (matches a bare int/float like `"1646.0"`) and `_is_plausible_summary`, which rejects a `summary` value that is either a stray Python-literal repr or a bare number — a symptom of a numeric field (e.g. `linkedin_connections`, `inferred_years_experience`) landing in `summary` after a same-length column shift. A genuine free-text summary is never just a number.
- **`skills`**: added `_is_plausible_skills`, which `ast.literal_eval`s the `skills` value and, if it parses as a list, rejects it when any element looks like a phone number (via the existing `_PHONE_LIKE_RE`). This catches the case where a shifted row lands `phone_numbers` in the `skills` column — `phone_numbers` is itself a list-of-strings, so it parses as a syntactically valid `skills` literal and the pre-existing type check alone can't tell it apart from real skills.

Both predicates are wired into `_ANCHOR_CHECKS` alongside the existing `job_title`/`industry`/URL/`gender` checks, so a row failing either is skipped in full (same treatment as a column-count mismatch), not partially trusted. The module docstring was updated to describe the two new checks.

## Stats updated to match

`.claude/CLAUDE.md` (data handling conventions, item 2) and the Persian `README.md` data-quality section were updated from the previous measured breakdown to the new one after adding these two checks:

| | Before this task | After this task |
|---|---|---|
| Malformed rows | ~82% (276/336) | ~81% (271/336) |
| — length-mismatch | 53 | 53 (unchanged) |
| — same-length shift | ~66% (223) | ~65% (218) |
| — exact duplicates | ~10% (34) | ~10% (34, unchanged) |
| Clean rows | ~18% (60/336) | ~9% (31/336) |

The drop from 60 to 31 clean rows reflects rows that previously passed all anchor checks (because nothing checked `summary`/`skills` shape) but are now correctly caught as shifted.

## Verification

- Added two regression tests to `backend/tests/test_parse.py`: `test_row_with_bare_number_in_summary_is_skipped` (a numeric value shifted into `summary`) and `test_row_with_phone_numbers_shifted_into_skills_is_skipped` (`phone_numbers` shifted into `skills`) — closing the coverage gap noted when this task was first documented.
- `uv run pytest` — 17/17 tests pass (15 existing + 2 new). `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy .` all clean.
- The updated 271/31 figures in `CLAUDE.md`/`README.md` were carried over as given in the diff, not re-derived by re-running ingestion in this session — re-running `docker compose run --rm backend python -m searcher.ingest.ingest` against a live Elasticsearch would be the way to re-confirm them if that's wanted.

## Files changed

- `backend/src/searcher/ingest/parse.py` — `_BARE_NUMBER_RE`, `_is_plausible_summary`, `_is_plausible_skills`, two new `_ANCHOR_CHECKS` entries, updated module docstring.
- `backend/tests/test_parse.py` — two new regression tests for the `summary`/`skills` anchor checks.
- `.claude/CLAUDE.md` — data handling conventions, item 2, updated malformed/clean-row statistics.
- `README.md` — Persian data-quality section, same statistics update plus a description of the new checks.
- `docs/TASKS.md` — added this task.
