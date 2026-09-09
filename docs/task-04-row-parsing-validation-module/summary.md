# Task 4 — Summary

Implemented `backend/src/searcher/ingest/parse.py` as a standalone parsing module (importable by the future ingestion script, and runnable directly via `uv run python -m searcher.ingest.parse`).

## What it does

- Reads `data/300_user_linkedin.txt` with the stdlib `csv` module (its default quoting handles the well-formed rows fine — the row-shifting problem in this dataset comes from unescaped quotes inside free-text fields, not from anything `csv` mishandles on its own).
- For every data row, compares `len(row)` against the header's field count. A mismatch means unescaped quotes upstream have shifted that row's columns, so the row is skipped entirely and logged — never trusted at a guessed column offset.
- For rows that pass the count check, builds a `dict[str, Any]` record by zipping header names to values:
  - Scalar fields are whitespace-stripped; a blank result becomes `None` (absent), not an error.
  - The nine nested fields (`skills`, `experience`, `education`, `emails`, `phone_numbers`, `interests`, `certifications`, `languages`, `profiles`) are parsed with `ast.literal_eval` inside a try/except. A blank value or a literal that fails to parse becomes `None` for that field only — the rest of the row is still kept.
- Every skip (row-count mismatch) and every individual nested-field parse failure is logged with the row index and reason to `backend/ingest.log` (already gitignored), via a `FileHandler` attached to the module logger the first time `parse_profiles` runs. Running the module standalone also echoes basic progress to stdout.

## Verification against the real dataset

```
uv run python -m searcher.ingest.parse
```

produced **283 clean records** and **53 skipped rows**, matching the checkpoint's expected ~283/~53 split exactly. `ingest.log` shows one `WARNING` line per skipped row (index + expected/actual field counts) plus `WARNING` lines for individual nested-field parse failures on rows that were otherwise kept, ending with an `INFO` summary line.

## Deviations from the description

None in behavior. Two additions beyond the literal prompt, both consistent with existing CLAUDE.md conventions:

- Added `backend/tests/test_parse.py` (4 cases: clean row with a nested field, empty-field-as-absent, row-count mismatch causing a skip, unparseable nested literal keeping the row with that field set to `None`) — the testing conventions call for coverage of the data-handling logic, and this module is the riskiest piece of it.
- `parse_profiles` returns `list[dict[str, Any]]` (aliased as `ProfileRecord`) rather than a dataclass/Pydantic model, since `models.py` is reserved for API request/response shapes per the repo structure and the ingestion pipeline (mapping definition, bulk indexing) is still a later task — a typed dict alias was the lightest structure that wouldn't need reworking once Task 5/6 land.

## Files changed

- `backend/src/searcher/ingest/parse.py` — implementation (was an empty placeholder).
- `backend/tests/test_parse.py` — new, unit tests for the parser.
- `docs/task-04-row-parsing-validation-module/` — this folder.
