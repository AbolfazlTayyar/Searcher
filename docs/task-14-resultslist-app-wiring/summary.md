## What was implemented

- **`ResultsList.tsx`**: takes `data` (`SearchResponse | undefined`), `isLoading`, and `isError` as props (mirroring the shape TanStack Query's `useQuery` returns) and renders one of three explicit states — a loading message, an error message (`role="alert"`), or an empty-results message — before falling through to the actual list. Each profile renders via a small internal `ProfileCard` component showing name, job title, industry, location, summary, and skills, all guarded with optional chaining/conditionals since every field except `skills` can be `null` per the backend's data-quality conventions.
- **`App.tsx`**: now owns `query`, `jobTitle`, and `skill` as local `useState`, passes them into `useSearch` from `src/api/search.ts` (the Task 12 hook), and renders `SearchBar`, `Filters`, and `ResultsList` wired to that shared state — `SearchBar` and `Filters` only ever see setters, `ResultsList` only ever sees the query result.

## Deviations from the description

None. `useSearch` already existed in `src/api/search.ts` from Task 12 exactly as expected, so no new data-fetching logic was needed here — this task was purely presentation + wiring.

## Files changed

- `frontend/src/components/ResultsList.tsx` (was empty — implemented)
- `frontend/src/App.tsx` (replaced placeholder with real page composition)

## Verification

- `npm run build` (tsc -b && vite build) passes with no type errors.
- `npm run lint` passes with no warnings/errors.
- Full manual end-to-end checkpoint against the real backend + Elasticsearch, driven through the browser:
  - Keyword search debounces and updates results (e.g. "engineer" narrowed from the 283-result default set to 2 matches).
  - Job title filter alone narrows correctly; job title + skill combined applies AND logic (returns empty when the two don't co-occur on any profile, non-empty when they do).
  - Clearing keyword and both filters returns to the full default result set.
  - A nonsense keyword renders the "No profiles match your search." empty state, not a blank screen.
  - Found along the way: `frontend/.env` didn't exist locally, so `VITE_API_BASE_URL` was `undefined` and requests silently hit Vite's SPA fallback instead of the backend (200 status but not JSON), which looked like a false empty state on first load. This was a local dev-environment gap, not a code defect — fixed by creating `frontend/.env` from `.env.example` (gitignored, nothing to commit) and restarting the dev server.
