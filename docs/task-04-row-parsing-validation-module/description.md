# Task 4 — Row parsing & validation module

**Do:** `ingest/parse.py` — CSV row reading, field-count validation against the header, `ast.literal_eval` parsing for nested fields (wrapped in try/except), returns clean structured records + logs skipped/malformed rows.

**Prompt:**
> Implement `backend/src/searcher/ingest/parse.py` per the "Data handling conventions" section of CLAUDE.md: read `data/300_user_linkedin.txt` as CSV, validate each row's field count against the header and skip+log malformed rows (don't trust column position blindly), parse the nested Python-literal-string fields (skills, experience, education, etc.) with `ast.literal_eval` in a try/except, and treat empty fields as absent rather than erroring. Return a list of clean structured profile records. Write skipped-row details to `backend/ingest.log`.

**Checkpoint:** Run the parser standalone against the real dataset; confirm ~283 clean records and ~53 logged skips, with `ingest.log` showing row index + reason for each skip.
