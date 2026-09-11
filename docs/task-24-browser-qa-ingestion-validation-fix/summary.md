# Task 24 summary — Browser QA pass and ingestion validation fix

## What was done

Ran the 7 requested QA scenarios against the live stack (Elasticsearch + backend + frontend, all via `docker compose`) using Claude in Chrome, verifying each one both in the browser UI and against the backend API directly for precision.

**Results of the initial pass:**

| # | Scenario | Result |
|---|----------|--------|
| 1 | `+1` keyword search should return 0 results | **Failed** — 3 hits, including a row with an entire raw `experience` structure dumped into `location` and fragments leaked into `industry`/`summary` |
| 2 | Case-insensitive keyword search | Passed |
| 3 | Job-title filter exact-match (keyword, not partial) | Passed |
| 4 | Multi-word skill filter exact-match | Passed |
| 5 | Combined keyword + both filters intersect properly | Passed |
| 6 | No-match query renders a clean empty state | Passed |
| 7 | Missing-field profile renders without layout breakage | Passed the layout check, but surfaced the same leak live: a profile showed `MILITARY · +19104675531` — a phone number in the `industry` slot |

Investigating #1/#7 led to querying Elasticsearch directly, which turned up a much bigger problem than the failing test alone suggested:

- 27 profiles had a raw phone number in `industry`.
- ~49 profiles had `job_title` holding a stringified Python list (`"['manager']"`, `"[]"`, etc.).
- The index had 283 documents but only 248 unique `full_name` values — 35 duplicate documents, traced to byte-identical duplicate rows in the source CSV.
- Manually decoding a few "clean-looking" rows column-by-column (via `csv.reader`, not naive comma-splitting) showed some rows keep the *correct total field count* but have every field from partway through the row assigned to the wrong header — e.g. `facebook_url` holding an industry name, `twitter_url` holding a birth date or a first name, one row's `full_name`/`job_title`/`industry` literally reading back the CSV header itself as data.

## Root cause and fix

`backend/src/searcher/ingest/parse.py` only validated a row's *column count* against the header. That catches rows where an unescaped quote adds or removes columns, but not rows where the shift's net effect leaves the column count unchanged while scrambling field assignment from the shift point onward — a category found to affect the majority of the "clean" 283 rows.

Fix implemented in `parse.py`:

- Added `_ANCHOR_CHECKS`: per-column shape predicates for `linkedin_url`/`facebook_url`/`twitter_url`/`github_url` (must contain their own platform domain, or be blank), `gender` (must be `male`/`female`, or blank), and `job_title`/`industry` (must not look like a Python-literal repr or a bare phone number, or be blank). A row failing any anchor check is skipped in full and logged — the same treatment as a column-count mismatch — rather than trusting the row's other fields.
- Added exact-duplicate-row detection (`seen_rows` set keyed on the full parsed row tuple) to catch the byte-identical repeated CSV rows.

`backend/src/searcher/ingest/ingest.py`'s docstring on `_to_bulk_actions` was updated to reflect that exact duplicates are now caught upstream in `parse.py`, while still explaining why bulk-indexing doesn't key documents on `linkedin_id`.

Added three new tests to `backend/tests/test_parse.py` covering the shifted-scalar case, the phone-like-value case, and duplicate-row dedup; all pass alongside the existing suite (12/12), plus `ruff check`, `ruff format --check`, and `mypy` clean.

## Verification

- Rebuilt the backend Docker image (source isn't bind-mounted; the running container was serving stale code until rebuilt) and re-ran `docker compose run --rm backend python -m searcher.ingest.ingest`.
- Indexed count dropped from 283 to **60** clean, verified-unique profiles (276 skipped: 53 column-count mismatches, 189 anchor-check failures, 34 exact duplicates).
- Confirmed via direct Elasticsearch queries: zero remaining phone-number-shaped `industry` values, zero remaining Python-literal-shaped `job_title` values.
- Re-ran the `+1` search: one residual hit remains (`hava avraham`, summary contains "HIV-1") — this is expected ES analyzer tokenization (`+1` → `1`, matching the `1` in `HIV-1`), not a data-corruption leak, and was called out explicitly rather than treated as a further bug.
- Confirmed the rest of the original 7 scenarios still pass against the corrected index.

## Deviation from the original ask

The user's test #1 only asked to confirm phone-number leakage was gone; investigating it uncovered a much larger, previously undocumented class of malformed rows (same field-count, scrambled content) than `CLAUDE.md` described. Given the scale (a majority of the "clean" 283 rows were actually affected), this was surfaced to the user directly with the before/after numbers and an explicit tradeoff question (keep the stricter anchor set at 60 rows, or relax it to keep more rows with looser guarantees) rather than silently fixing it and moving on. The user chose to keep the stricter set.

## Files changed

- `backend/src/searcher/ingest/parse.py` — anchor-field validation + exact-duplicate-row detection; updated module docstring.
- `backend/src/searcher/ingest/ingest.py` — updated `_to_bulk_actions` docstring.
- `backend/tests/test_parse.py` — three new tests.
- `.claude/CLAUDE.md` — data handling conventions section (item 2) updated with the real, measured skip breakdown (53 column-count / 223 anchor-shift / 34 duplicate / 60 clean, out of 336) in place of the original column-count-only ~16% estimate.
- `docs/TASKS.md` — added Task 24 documenting this session's work.
- Elasticsearch index `linkedin_profiles` — re-ingested from the fixed pipeline (283 → 60 documents).
