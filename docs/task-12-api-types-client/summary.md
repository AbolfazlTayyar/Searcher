## What was implemented

- `frontend/src/api/types.ts` — `ProfileResult` and `SearchResponse` interfaces mirroring `backend/src/searcher/models.py` field-for-field. Optional backend fields (`name`, `job_title`, `industry`, `summary`, `location`) are typed `string | null` rather than `string | undefined`, since FastAPI serializes Pydantic's `None` to JSON `null` and the fetched response is parsed as-is with no transformation layer.
- `frontend/src/api/search.ts`:
  - `SearchParams` — camelCase param interface (`q`, `jobTitle`, `skill`, `page`, `pageSize`) for the client-facing API.
  - `fetchSearch(params)` — builds the query string (mapping `jobTitle`/`pageSize` to the backend's `job_title`/`page_size`), calls `GET {VITE_API_BASE_URL}/search`, throws on a non-OK response, and returns the typed `SearchResponse`.
  - `useSearch(params)` — thin TanStack Query wrapper around `fetchSearch`, keyed on `['search', params]` so each distinct keyword/filter/page combination is cached and changes trigger a refetch.

## Deviations

- Empty/undefined param values are omitted from the query string entirely rather than sent as `q=`, `job_title=`, etc. — keeps the backend's "field not present" handling (per CLAUDE.md's data-handling conventions) uniform instead of the route needing to treat a blank string differently from an absent param.
- Not otherwise deviated from the task description.

## Verification

- `npx tsc --noEmit` — clean.
- `npx eslint src/api/types.ts src/api/search.ts` — clean.

No UI to check yet — `SearchBar`/`Filters`/`ResultsList` wiring is Tasks 13–14.
