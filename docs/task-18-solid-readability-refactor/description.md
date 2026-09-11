### Task 18 — SOLID / readability refactor pass
**Do:** Review backend modules and frontend components against the SOLID-related bullet in CLAUDE.md's Backend conventions — single responsibility, clear naming, small functions — and refactor where needed.

**Prompt:**
> Review backend/src/searcher and frontend/src against the SOLID/readability conventions in CLAUDE.md. Refactor anything that violates single responsibility (a function or module doing more than one job), has unclear naming, or is harder to follow than it needs to be. Keep behavior identical — this is a structural/readability refactor, not a feature change.

**Checkpoint:** All existing backend tests (uv run pytest) and frontend tests (npm run test) still pass after the refactor. Manually skim each touched file — each has one clear responsibility and reads easily top to bottom.
