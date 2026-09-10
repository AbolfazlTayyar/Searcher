## What was implemented

- `src/components/SearchBar.tsx`: a controlled text input that keeps its own local `value` state (so typing feels instant) and calls `onQueryChange(query: string)` through a 300ms `useDebouncedCallback` from `use-debounce`. No fetching, no knowledge of the search API.
- `src/components/Filters.tsx`: two controlled text inputs, `job_title` and `skill`, driven entirely by props (`jobTitle`, `skill`, `onJobTitleChange`, `onSkillChange`) — no internal state, no debouncing (filters aren't free-typed search text, so immediate propagation is fine).

Both components use explicit `interface` prop types, are typed function declarations (no `React.FC`), and have no data-fetching or TanStack Query usage, per the task constraint.

## Deviations from the description

- The dataset's `job_title` and `skill` values are free text with no fixed vocabulary (confirmed against `search_service.py` / the ingestion mapping), so "selectors" were implemented as plain text inputs rather than `<select>` dropdowns. A dropdown would require pre-computing a list of distinct values, which is out of scope for a presentational component and not requested elsewhere in the task list.
- `SearchBar` debounces only the *callback* to the parent, not the input's own displayed value — the input stays fully responsive while the parent only sees updates every 300ms.

## Checkpoint verification

Since the task description explicitly allows temporary wiring into `App.tsx` for visual verification, both components were briefly wired in with local `useState` and a `<pre>` dump of the resulting state, then run via `npm run dev`. `npx tsc -b --noEmit` and `npx eslint` both passed with no errors/warnings. The Chrome browser extension was not connected in this session, so the debounce/typing behavior could not be visually screenshotted — verification relied on typecheck/lint passing and manual reasoning about the debounce wiring (`useDebouncedCallback` from `use-debounce`, the same package already used elsewhere in the project). The temporary `App.tsx` wiring was reverted afterward since real wiring is Task 14's responsibility.

## Files changed

- `frontend/src/components/SearchBar.tsx` (new content, was an empty placeholder)
- `frontend/src/components/Filters.tsx` (new content, was an empty placeholder)
