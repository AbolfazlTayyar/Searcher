# Task 12 — API types + client
**Do:** `src/api/types.ts` mirroring the backend Pydantic models, `src/api/search.ts` with a typed fetch function + a TanStack Query hook.

**Prompt:**
> Implement `src/api/types.ts` with TypeScript interfaces mirroring the backend's search response and profile result models exactly (check `backend/src/searcher/models.py` for field names/types). Implement `src/api/search.ts` with a typed fetch function calling `GET /search` and a `useSearch` hook wrapping it in TanStack Query, accepting keyword + both filter values as arguments.

**Checkpoint:** No implementation to visually check yet — types compile cleanly (`npx tsc --noEmit`).
