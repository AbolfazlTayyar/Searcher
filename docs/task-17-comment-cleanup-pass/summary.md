Audited every file in `backend/src` and `frontend/src` against the "Comment density" rule in CLAUDE.md (keep only comments that explain non-obvious *why*; remove anything that restates the next line).

Went through all `#` comments in the backend (grepped every occurrence across `backend/src`), and all `//` and `/** ... */` comments in the frontend (grepped every occurrence across `frontend/src`, including `.tsx`/`.ts` and test files), plus the module/function docstrings in the backend.

Result: no changes were needed. Every existing comment already explains a non-obvious tradeoff or data quirk rather than restating code, for example:

- `ingest/parse.py`, `ingest/mapping.py`, `ingest/ingest.py`: comments cover the CSV column-mismatch handling, why `ast.literal_eval` is used instead of `json.loads`, why ES dynamic date/numeric detection is disabled, and why `certifications`/`profiles` are stored with `enabled: false` rather than typed.
- `search_service.py`: explains the `must`/`filter` split for relevance vs. exact-match, and why offset pagination is fine at this dataset size.
- Frontend JSDoc blocks (`SearchBar.tsx`, `Filters.tsx`, `ResultsList.tsx`, `api/search.ts`, `api/types.ts`) explain debounce/presentational-component boundaries, why empty params are omitted from the query string rather than sent as `""`, and the Pydantic-to-TS type mirroring convention — none restate the code beneath them.

No logic, docstrings serving the CLAUDE.md-mandated "docstrings on public functions" convention, or any other file content was touched. This was a read-only verification pass; `git status` shows no diff.
