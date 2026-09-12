# Task 27 — Anchor checks for `summary`/`skills` column-shift leaks

## Original prompt

No session transcript was captured for this task — the change was made directly to the working tree before this documentation pass. The prompt below is inferred from the diff (new `_BARE_NUMBER_RE`/`_is_plausible_summary`/`_is_plausible_skills` predicates in `parse.py`, plus the updated malformed-row stats in `CLAUDE.md` and `README.md`), not copied verbatim from the original request:

> The anchor checks from the earlier ingestion fix caught shifted `job_title`/`industry`/URL/`gender` values, but two more leaks are getting through: a numeric field (connections count or years-of-experience) landing in `summary` as a bare number, and `phone_numbers` landing in `skills` — which still parses as a valid list-of-strings, so the existing type check doesn't reject it. Add anchor checks for `summary` and `skills` to catch these, and update the malformed-row statistics in CLAUDE.md and the README to match the corrected counts.
