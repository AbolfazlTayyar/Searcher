## What was implemented

`backend/src/searcher/ingest/ingest.py` is a runnable script (`uv run python -m searcher.ingest.ingest`) that:

1. Connects to Elasticsearch via `Elasticsearch(settings.ES_HOST)`, reusing the same `Settings` (`config.py`) used by the app.
2. Parses the dataset with `parse_profiles` (Task 4) and counts total data rows in the source CSV for the final summary.
3. Drops and recreates the `linkedin_profiles` index from the mapping/settings in `mapping.py` (Task 5) — recreate-on-run keeps this idempotent since the dataset is write-once.
4. Bulk-indexes every clean record via `elasticsearch.helpers.bulk`, one bulk request rather than per-document calls. Documents get ES-assigned ids (no explicit `_id`) — idempotency on re-run comes from dropping and recreating the index (step 3), not from a stable id, so a handful of source rows that happen to share a `linkedin_id` value still each get their own document rather than being collapsed into one.
5. Logs both parse-level skips (from `parse.py`, e.g. column-count mismatches) and any bulk-level errors to `backend/ingest.log`, and prints a final `Indexed: N` / `Skipped: N` summary (skipped = total source rows − indexed documents).

## Deviations from the description and why

The description assumed `parse.py`'s existing row-count validation was sufficient to guarantee "clean" records. In practice it wasn't: running the script surfaced two additional problems that had to be fixed to get a working end-to-end ingest, both scoped narrowly to what was needed:

1. **Dependency version drift.** `pyproject.toml` pinned `elasticsearch[async]>=8.17` with no upper bound, which resolved to client `9.5.1` — not wire-compatible with the `elasticsearch:8.13.0` server pinned in `docker-compose.yml`, causing every request to fail with `BadRequestError(400, 'None')`. Pinned to `elasticsearch[async]>=8.17,<9` and re-ran `uv sync`.

2. **Dynamic-mapping and shape-mismatch failures at the ES layer.** The Task 5 mapping only declares fields the search API touches, leaving other source columns (e.g. `job_last_updated`) to dynamic mapping; ES's date auto-detection guessed `date` from an early well-formed row and then rejected every later row where that column held plain text. Fixed by disabling `date_detection`/`numeric_detection` on the mapping, and by explicitly mapping `emails`, `phone_numbers`, `profiles` as `{"type": "object", "enabled": false}` (unused by search, and inherently shape-inconsistent across rows).

   A further ~17% of the "clean" (correct column-count) rows still had data shifted into the wrong field — an address `dict` landing under `skills`, for example — because some unescaped-quote shifts happen to preserve the row's total column count even though they misalign individual fields. This surfaced as ES `document_parsing_exception`s that killed the whole document. Rather than let a single corrupted field drop the entire profile, `parse.py` now validates each nested field's parsed type (and, for list fields, its element type) against what the field is expected to hold; a mismatch logs a warning and treats just that field as absent, consistent with the project's existing "degrade gracefully on missing fields" convention. This took indexed documents from 117/336 to the full 283/336 parse-clean rows, with zero remaining bulk errors.

None of this changes the ingestion script's documented interface or output shape — the fixes were necessary for the script to actually do what the task asked ("bulk-index the clean records... print a summary") rather than fail or silently drop most of the dataset.

## Follow-up fixes from the checkpoint

The checkpoint ("`_count` matches the clean-record count from Task 4") caught two further problems in the first pass:

1. **Duplicate `linkedin_id` values collapsing distinct records.** The original `_to_bulk_actions` set `_id` to `record["linkedin_id"]` when present, intending to make re-running the script idempotent. But the index is already dropped and recreated on every run (step 3 above), so a stable `_id` bought nothing — it only caused harm: 35 source rows share a `linkedin_id` with another row, so keying on it silently collapsed those pairs into single documents, taking the final count from 283 to 248 and breaking the checkpoint. Removed the explicit `_id` entirely; each clean record now gets its own ES-assigned id and its own document.

2. **Wrong assumed shape for `certifications`/`languages`.** The per-field shape validation added in `parse.py` (see above) originally assumed both fields were lists of plain strings, matching the mapping in `mapping.py`. Checking the actual data showed both are always lists of structured records instead — `certifications`: `{"organization": ..., "name": ..., "start_date": ..., "end_date": ...}`, `languages`: `{"name": ..., "proficiency": ...}` (a `dict` value for these fields is *only* ever corruption for `skills`/`interests`, not for these two). The wrong assumption meant the validation was treating the field as "wrong type" and silently discarding it as absent on nearly every well-formed row. Fixed `_EXPECTED_LIST_ELEMENT_TYPE` in `parse.py` to expect `dict` for both, and replaced their `mapping.py` entries from flat `_KEYWORD` with `object` mappings carrying the real sub-fields, so the data is now actually retained and indexed instead of dropped.

After both fixes, `_count` on `linkedin_profiles` is **283**, matching Task 4's clean-record count exactly.

## Result

- 336 total rows in the source file.
- 53 skipped at the parse layer (column-count mismatch — matches the ~16% documented in `CLAUDE.md`).
- 283 clean records bulk-indexed with zero ES errors, and `_count` on the index is 283 — matching Task 4's clean-record count exactly (verified per the checkpoint).

## Files created/changed

- `backend/src/searcher/ingest/ingest.py` — the ingestion script (was an empty stub).
- `backend/src/searcher/ingest/mapping.py` — added `date_detection`/`numeric_detection: false`, explicit (disabled) mappings for `emails`/`phone_numbers`/`profiles`, and corrected `certifications`/`languages` from flat keyword lists to `object` mappings matching their real structured shape.
- `backend/src/searcher/ingest/parse.py` — added per-field type/shape validation for nested fields (with `certifications`/`languages` expecting `dict` elements, matching the corrected mapping), falling back to "absent" on a genuine mismatch instead of passing corrupted data through.
- `backend/pyproject.toml` — pinned `elasticsearch[async]` to `<9` to match the ES 8.x server.
