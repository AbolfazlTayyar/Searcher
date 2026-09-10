## What was implemented

Added Vitest + React Testing Library coverage for the three presentational components:

- `src/components/SearchBar.test.tsx` — types into the input via `user-event`, asserts the debounced `onQueryChange` callback has *not* fired immediately, then `waitFor`s it to fire exactly once with the final typed value (covers the debounce behavior, not just the raw `onChange`).
- `src/components/Filters.test.tsx` — three cases: typing in the job title input calls `onJobTitleChange` (and leaves `onSkillChange` untouched), typing in the skill input calls `onSkillChange` (and leaves `onJobTitleChange` untouched), and the inputs reflect controlled `jobTitle`/`skill` prop values.
- `src/components/ResultsList.test.tsx` — four cases: loading state, error state (`role="alert"`), empty-results state, and a populated list that renders name/job title/industry/location/summary/skills for a sample profile.

Test infra additions (none of this existed yet — task 11 scaffolded the app but not a test runner config):

- `vite.config.ts` — added a `test` block (`environment: 'jsdom'`, `setupFiles`) via the `vitest/config` triple-slash reference, so `vite.config.ts` stays the single Vite/Vitest config file rather than adding a separate `vitest.config.ts`.
- `src/test/setup.ts` — imports `@testing-library/jest-dom/vitest` for the extended matchers (`toHaveValue`, `toBeInTheDocument`, etc.) and registers an `afterEach(cleanup)`. RTL's implicit auto-cleanup depends on Vitest's `globals: true`, which this project doesn't enable (keeping `describe`/`it`/`expect` as explicit imports, consistent with not using implicit globals elsewhere); without the explicit `cleanup()` call, `Filters.test.tsx`'s three renders leaked into each other and `getByLabelText` failed with "multiple elements found."
- Added `@testing-library/user-event` as a devDependency (present in the ecosystem but missing from `package.json`) — used instead of firing raw `fireEvent.change` calls, since it more accurately simulates real per-keystroke typing, which matters for the `SearchBar` debounce test.

## Deviations from the description

- The description says "selecting a value" for `Filters`, but `Filters` uses plain text `<input>`s, not `<select>`s (per task 13) — the tests type into the text inputs instead.
- Vitest/JSDOM test infrastructure (config + setup file) wasn't part of task 11's scaffold, so it was added here as a prerequisite rather than a separate task.

## Files created/changed

- `frontend/vite.config.ts` — added `test` config
- `frontend/src/test/setup.ts` — new, jest-dom matchers + RTL cleanup
- `frontend/src/components/SearchBar.test.tsx` — new
- `frontend/src/components/Filters.test.tsx` — new
- `frontend/src/components/ResultsList.test.tsx` — new
- `frontend/package.json` — added `@testing-library/user-event` devDependency
- `frontend/package-lock.json` — lockfile update from the install
