## What was implemented

`backend/src/searcher/models.py` now defines the two Pydantic models the search API's routes/service will use:

- **`ProfileResult`** — the display shape for one profile: `name`, `job_title`, `industry`, `summary`, `location` (all `str | None`) and `skills` (`list[str]`, defaults to `[]`). Field names match the mapping in `ingest/mapping.py` (`full_name` → `name`, `location_name` → `location`) at the API boundary, so the frontend gets clean names without leaking ES's internal field naming. All scalar fields are optional because the dataset legitimately leaves many of them blank (per CLAUDE.md's data-quality notes) — that's not an error condition the API should reject or hide.
- **`SearchResponse`** — the envelope returned by `GET /search`: `results: list[ProfileResult]`, `total` (matching count, `ge=0`), `page` and `page_size` (both `ge=1`) for pagination info.

Only the fields `ResultsList.tsx` needs to render are exposed — nested `experience`/`education`/`certifications`/etc. from the index are intentionally left out of this response shape.

## Deviations

None. Implemented as described; no search-request query-param model was added here since that belongs to the route layer (Task 8/9), and the task description only asked for the response envelope and result item shape.

## Verification

- `uv run python -c "from searcher.models import ProfileResult, SearchResponse; ..."` constructs and prints a `SearchResponse` correctly.
- `uv run ruff check` / `ruff format --check` / `mypy` all pass on the new file.
