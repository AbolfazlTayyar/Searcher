### Task 13 — SearchBar and Filters components
**Do:** `SearchBar.tsx` (debounced text input), `Filters.tsx` (job_title + skill selectors).

**Prompt:**
> Implement `SearchBar.tsx` (a debounced text input using `use-debounce`, emitting the keyword upward via props) and `Filters.tsx` (two filter controls for job_title and skill, emitting selected values upward via props). Keep both presentational — no data fetching inside them.

**Checkpoint:** Render both in isolation (temporarily in `App.tsx`) — typing debounces visibly, filter selections update local state.
