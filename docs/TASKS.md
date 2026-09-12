# Searcher — Build Task List

Sequential, local-dev only. Each task = one Claude Code session. Do them in order — each builds on the previous task's verified output. The prompt text under each task is meant to be handed to Claude Code roughly as-is (adjust wording as you like); it assumes `.claude/CLAUDE.md` and `Searcher.md` already exist at repo root and are readable context.

Per CLAUDE.md's "Documentation conventions," every task below gets a `docs/task-NN-<slug>/` folder with `description.md` and `summary.md` — this is a standing rule, not repeated in each task's prompt below.

---

## Phase 0 — Repo & folder structure

### Task 1 — Scaffold the repo skeleton
**Do:** Create the folder structure exactly as defined in `CLAUDE.md` — empty folders + placeholder `__init__.py`/`.gitkeep` where needed, `.gitignore` (Python + Node + `.env` + `data/*.log`), and copy `Searcher.md`, `CLAUDE.md`, and `300_user_linkedin.txt` into place (`data/300_user_linkedin.txt`).

**Prompt:**
> Read `.claude/CLAUDE.md` and `Searcher.md`. Create the full repo folder structure exactly as specified in the "Repo structure" section of CLAUDE.md, with empty placeholder files where needed (`.gitkeep`, empty `__init__.py`). Also create a `.gitignore` covering Python, Node, `.env`, and `backend/ingest.log`. Do not write any implementation code yet.

**Checkpoint:** `tree` (or equivalent) matches the structure in CLAUDE.md exactly. No stray files.

---

## Phase 1 — Infrastructure

### Task 2 — Docker Compose for Elasticsearch
**Do:** Write `docker-compose.yml` — single-node ES, security disabled for local dev, named volume for data persistence, exposed on the default port.

**Prompt:**
> Create `docker-compose.yml` at repo root running a single-node Elasticsearch instance suitable for local development (security disabled, discovery.type=single-node). Mount a named volume for the data directory so indexed data survives restarts. Expose the default HTTP port.

**Checkpoint:** `docker compose up -d` starts cleanly; `curl localhost:9200` returns a cluster info JSON response.

---

## Phase 2 — Backend foundation

### Task 3 — Initialize the Python project
**Do:** `pyproject.toml` via `uv`, core dependencies (fastapi, uvicorn, elasticsearch, pydantic-settings, pytest, httpx, ruff, mypy), `config.py` with `BaseSettings`, `.env.example`.

**Prompt:**
> Initialize the backend as a uv-managed Python project per CLAUDE.md's dependency management and repo structure sections. Add dependencies: fastapi, uvicorn, elasticsearch (async client), pydantic-settings, and dev dependencies pytest, httpx, ruff, mypy. Create `config.py` with a Pydantic `BaseSettings` class covering `ES_HOST`, `ES_INDEX_NAME`, and `CORS_ORIGINS`. Create `.env.example` documenting these variables. Create a minimal `main.py` with a FastAPI app and a `/health` endpoint only — no business logic yet.

**Checkpoint:** `uv sync` succeeds; `uv run uvicorn searcher.main:app --reload` starts; `GET /health` returns 200.

---

## Phase 3 — Data ingestion

### Task 4 — Row parsing & validation module
**Do:** `ingest/parse.py` — CSV row reading, field-count validation against the header, `ast.literal_eval` parsing for nested fields (wrapped in try/except), returns clean structured records + logs skipped/malformed rows.

**Prompt:**
> Implement `backend/src/searcher/ingest/parse.py` per the "Data handling conventions" section of CLAUDE.md: read `data/300_user_linkedin.txt` as CSV, validate each row's field count against the header and skip+log malformed rows (don't trust column position blindly), parse the nested Python-literal-string fields (skills, experience, education, etc.) with `ast.literal_eval` in a try/except, and treat empty fields as absent rather than erroring. Return a list of clean structured profile records. Write skipped-row details to `backend/ingest.log`.

**Checkpoint:** Run the parser standalone against the real dataset; confirm ~283 clean records and ~53 logged skips, with `ingest.log` showing row index + reason for each skip.

### Task 5 — Elasticsearch index mapping
**Do:** Explicit index mapping (not dynamic) per CLAUDE.md's ES conventions — `text`+`.keyword` for search/filter fields.

**Prompt:**
> Add an ES index mapping definition for `linkedin_profiles` per the "Elasticsearch conventions" section of CLAUDE.md — text fields with keyword sub-fields for name/summary/skills, keyword fields for job_title and skill filtering. Put this in a dedicated module the ingestion script can import (e.g. `ingest/mapping.py`).

**Checkpoint:** Review the mapping file yourself — confirm `job_title` and the skill filter field are `keyword`-typed and match the field names the frontend filters will send.

### Task 6 — Bulk ingestion script
**Do:** `ingest/ingest.py` — creates the index with the mapping, bulk-indexes the parsed records via the ES bulk API.

**Prompt:**
> Implement `backend/src/searcher/ingest/ingest.py` as a runnable script: create the `linkedin_profiles` index using the mapping from Task 5 (recreate if it already exists), then bulk-index the clean records from `parse.py` using the Elasticsearch bulk API. Print a summary at the end (indexed count, skipped count).

**Checkpoint:** `uv run python -m searcher.ingest.ingest` completes without errors; `curl localhost:9200/linkedin_profiles/_count` matches the clean-record count from Task 4.

---

## Phase 4 — Backend API

### Task 7 — Pydantic request/response models
**Do:** `models.py` — search request params, result item shape, paginated response envelope.

**Prompt:**
> Implement `models.py` with Pydantic models for: the search response envelope (results list, total count, page info), and an individual profile result item (only the fields the frontend actually needs to display — name, job_title, industry, skills, summary, location). Use proper types, not raw dicts.

**Checkpoint:** Models import cleanly; review field names match what you'll want to display in `ResultsList.tsx`.

### Task 8 — Search service (ES query building)
**Do:** `search_service.py` — builds the combined `bool` query (multi_match + filter clauses), executes against ES, maps hits to response models.

**Prompt:**
> Implement `search_service.py` per CLAUDE.md's Elasticsearch conventions: a function taking the search keyword and the two filter values, building a single `bool` query (multi_match in `must`/`should` for the keyword, `filter` clauses for job_title/skill), executing it against the async ES client, and mapping hits into the response models from Task 7. Raise a domain-specific `SearchQueryError` on failure — don't let raw ES exceptions propagate.

**Checkpoint:** Not yet testable via HTTP — proceed to Task 9 for that.

### Task 9 — Search endpoint + wiring
**Do:** `routes/search.py`, dependency injection for the ES client, CORS middleware, exception handler, wire everything into `main.py`.

**Prompt:**
> Implement `GET /search` in `routes/search.py` accepting `q`, `job_title`, `skill`, and pagination params, using FastAPI `Depends` for the ES client, calling `search_service.py`, and returning the paginated response model. Add CORS middleware in `main.py` restricted to the frontend dev origin, and a global exception handler that catches `SearchQueryError` and returns a consistent JSON error shape.

**Checkpoint:** With the backend running, manually hit `GET /search?q=engineer`, `GET /search?job_title=...`, and `GET /search?skill=...` (via curl or the FastAPI `/docs` page) — each returns sensible, correctly filtered results.

### Task 10 — Backend tests
**Do:** `pytest` + `httpx.AsyncClient` tests covering keyword search, each filter alone, both combined, and empty results.

**Prompt:**
> Write pytest tests in `backend/tests/` using `httpx.AsyncClient` against the FastAPI app, covering: keyword-only search, job_title filter alone, skill filter alone, both filters combined, and a query with no matches. Use a real or test ES index — don't mock ES itself, since query correctness is what's being tested.

**Checkpoint:** `uv run pytest` — all tests pass. Also run `uv run ruff check .` and `uv run mypy .` clean.

---

## Phase 5 — Frontend

### Task 11 — Scaffold the React + TypeScript app
**Do:** Vite + React + TS init, strict `tsconfig.json`, ESLint + Prettier, TanStack Query provider, `.env.example` for `VITE_API_BASE_URL`.

**Prompt:**
> Scaffold the frontend in `frontend/` with Vite + React + TypeScript per CLAUDE.md's frontend conventions: strict tsconfig, ESLint + Prettier + eslint-plugin-react-hooks configured, TanStack Query installed and its provider wired into the app root, and `.env.example` documenting `VITE_API_BASE_URL`. Leave `App.tsx` minimal — no feature components yet.

**Checkpoint:** `npm install && npm run dev` starts cleanly; blank app loads in the browser with no console errors.

### Task 12 — API types + client
**Do:** `src/api/types.ts` mirroring the backend Pydantic models, `src/api/search.ts` with a typed fetch function + a TanStack Query hook.

**Prompt:**
> Implement `src/api/types.ts` with TypeScript interfaces mirroring the backend's search response and profile result models exactly (check `backend/src/searcher/models.py` for field names/types). Implement `src/api/search.ts` with a typed fetch function calling `GET /search` and a `useSearch` hook wrapping it in TanStack Query, accepting keyword + both filter values as arguments.

**Checkpoint:** No implementation to visually check yet — types compile cleanly (`npx tsc --noEmit`).

### Task 13 — SearchBar and Filters components
**Do:** `SearchBar.tsx` (debounced text input), `Filters.tsx` (job_title + skill selectors).

**Prompt:**
> Implement `SearchBar.tsx` (a debounced text input using `use-debounce`, emitting the keyword upward via props) and `Filters.tsx` (two filter controls for job_title and skill, emitting selected values upward via props). Keep both presentational — no data fetching inside them.

**Checkpoint:** Render both in isolation (temporarily in `App.tsx`) — typing debounces visibly, filter selections update local state.

### Task 14 — ResultsList and App wiring
**Do:** `ResultsList.tsx` with explicit loading/error/empty states, `App.tsx` wiring state from SearchBar/Filters into the `useSearch` hook and passing results down.

**Prompt:**
> Implement `ResultsList.tsx` rendering the profile results with explicit loading, error, and empty states. Wire `App.tsx` to hold the current keyword and filter state, pass it to the `useSearch` hook from Task 12, and render `SearchBar`, `Filters`, and `ResultsList` together as a working page.

**Checkpoint:** Full manual end-to-end test in the browser: type a keyword → results update after debounce; apply each filter alone and combined → results narrow correctly; clear everything → full/default result set returns; search a nonsense term → empty state displays correctly.

### Task 15 — Frontend tests
**Do:** Vitest + React Testing Library for `SearchBar`, `Filters`, `ResultsList`.

**Prompt:**
> Write Vitest + React Testing Library tests for `SearchBar` (typing triggers the debounced callback with correct value), `Filters` (selecting a value calls the callback with correct value), and `ResultsList` (renders results correctly, and renders the empty state when given an empty list).

**Checkpoint:** `npm run test` — all tests pass. `npm run lint` clean.

---

## Phase 6 — Polish & containerization

### Task 16 — Modern, distinctive UI pass
**Do:** Replace default/scaffold styling with an intentional design — real color palette, type scale, and a layout suited to a search tool — per the "UI/design conventions" section of CLAUDE.md. No functional changes.

**Prompt:**
> Redesign the frontend's visual styling per the "UI/design conventions" section of CLAUDE.md: pick a deliberate color palette and typography, and a layout suited specifically to a search tool (not a generic centered card grid or default Tailwind/shadcn look). This is a styling pass only — don't change any component logic, data flow, or the API layer. All existing functionality (search, filters, loading/error/empty states) must keep working exactly as before.

**Checkpoint:** Visually compare against an unstyled scaffold — the app should look like a deliberate design choice, not a default template. Re-run the full manual flow from Task 14's checkpoint — nothing functional broke.

### Task 17 — Comment cleanup pass
**Do:** Audit comments across backend and frontend per the "Comment density" section of CLAUDE.md — remove noise, keep only comments that explain non-obvious why.

**Prompt:**
> Go through every file in backend/src and frontend/src and clean up comments per the "Comment density" section of CLAUDE.md: remove any comment that just restates what the next line of code already says, and keep only comments explaining non-obvious reasoning (e.g. the CSV malformation handling, any tradeoffs). Do not change any logic — comments only.

**Checkpoint:** Spot-check a handful of files — remaining comments all pass the "why, not what" test. No behavior changed (existing tests from Tasks 10 and 15 still pass).

### Task 18 — SOLID / readability refactor pass
**Do:** Review backend modules and frontend components against the SOLID-related bullet in CLAUDE.md's Backend conventions — single responsibility, clear naming, small functions — and refactor where needed.

**Prompt:**
> Review backend/src/searcher and frontend/src against the SOLID/readability conventions in CLAUDE.md. Refactor anything that violates single responsibility (a function or module doing more than one job), has unclear naming, or is harder to follow than it needs to be. Keep behavior identical — this is a structural/readability refactor, not a feature change.

**Checkpoint:** All existing backend tests (uv run pytest) and frontend tests (npm run test) still pass after the refactor. Manually skim each touched file — each has one clear responsibility and reads easily top to bottom.

### Task 19 — Full containerization
**Do:** Add backend/Dockerfile and frontend/Dockerfile (both multi-stage), update docker-compose.yml to run Elasticsearch + backend + frontend together, and wire the ingestion step per the "Infra & containerization" section of CLAUDE.md, so the whole app runs via Docker with no local uv/npm commands required.

**Prompt:**
> Implement the "Infra & containerization" section of CLAUDE.md: create a multi-stage backend/Dockerfile (uv-based) and a multi-stage frontend/Dockerfile (Vite build, served via nginx), update docker-compose.yml to run all three services together with correct env vars (ES host as the service name, not localhost) and depends_on/healthchecks so the backend waits for Elasticsearch to be ready. Set up the ingestion step as either an automated one-off compose service or a clearly documented single command. Update the "How to run" section of CLAUDE.md and the README if it already exists.

**Checkpoint:** From a clean state (docker compose down -v), running docker compose up --build -d plus the documented ingestion command brings up the entire app with no local Python/Node tooling used — frontend reachable in the browser, search and filters working end-to-end against the containerized backend and ES.

---

## Phase 7 — Documentation & final pass

### Task 20 — Remove CDN usage, vendor everything locally
**Do:** Audit the frontend (and backend, if applicable) for any CDN-loaded resources — script/link tags pointing at services like unpkg, jsdelivr, cdnjs, Google Fonts, etc. — and replace each with a locally installed/bundled equivalent, so the app has no runtime dependency on external CDNs.

**Prompt:**
> Search the project for any CDN usage — `<script>`/`<link>` tags in `index.html` or elsewhere pointing to external CDNs (unpkg, jsdelivr, cdnjs, Google Fonts, etc.), or any library loaded via CDN instead of a package import. Replace each with a locally installed npm package (or self-hosted asset, e.g. downloaded font files served from `public/`), bundled through Vite like the rest of the app. Remove the CDN references entirely. Don't change any functionality — this is a delivery-mechanism change only.

**Checkpoint:** Disconnect from the internet (or block outbound requests) and run the app — it loads and functions identically, with no failed network requests to any external CDN domain in the browser's network tab.

### Task 21 — README
**Do:** How to run (Docker-based), architecture explanation (including the ES-only, no-separate-DB decision and why), search/filter logic explanation, note on data quality handling.

**Prompt:**
> Write `README.md` at repo root covering: how to run the project end-to-end via Docker (per the updated "How to run" section of CLAUDE.md), a general architecture explanation (FastAPI + Elasticsearch, no separate database and why that's sufficient here), an explanation of the search and filter logic (multi_match + bool/filter query), and a short note on the dataset's data quality issues and how ingestion handles them.

**Checkpoint:** Follow the README's own run instructions on a clean checkout (or mentally step through them) — confirm nothing is missing or out of order.

### Task 22 — Final review against the spec
**Do:** Re-check the implementation against every bullet in `Searcher.md`.

**Prompt:**
> Read `Searcher.md` again in full. Go through every requirement (backend search, at least 2 filters, frontend search input + 2 filters + results display, data storage/indexing design, README with run instructions/architecture/search explanation) and confirm the current implementation satisfies each one. Flag anything missing or partially done — don't fix silently, just report.

**Checkpoint:** Every bullet in the original spec is confirmably satisfied. Project is demo-ready.

---

## Phase 8 — Local environment fixes

### Task 23 — Fix dev port conflict on Windows
**Do:** Diagnose why `docker compose up --build -d` failed to bind host port 5173, remap the frontend's published port in `docker-compose.yml`, and update every doc/config reference to the old port. Then run ingestion and verify the full stack end-to-end.

**Prompt:**
> Running `docker compose up --build -d` fails with `ports are not available: exposing port TCP 0.0.0.0:5173 -> 127.0.0.1:0: listen tcp 0.0.0.0:5173: bind: An attempt was made to access a socket in a way forbidden by its access permissions`. Diagnose the root cause (check `netsh interface ipv4 show excludedportrange protocol=tcp` for a Windows-reserved port range covering 5173), remap the frontend's host-side port in `docker-compose.yml` to a free port, and update every place that documents or configures port 5173 (`README.md`, `.claude/CLAUDE.md`, `.env.example`, backend `CORS_ORIGINS` default) to match. Bring the stack up, run the one-off ingestion command, and verify the frontend loads and the search flow works end-to-end in a browser.

**Checkpoint:** `docker compose up --build -d` starts all three services cleanly; ingestion reports the expected ~283 indexed / ~53 skipped rows; the frontend loads at the new port with default results, and typing a keyword narrows results correctly after the debounce.

---

## Phase 9 — QA & data-integrity fixes

### Task 24 — Browser QA pass and ingestion validation fix
**Do:** Run a set of manual QA scenarios against the live, running stack via browser automation (malformed-row exclusion, keyword case sensitivity, exact-match job-title/skill filtering, combined keyword+filter intersection, empty-result state, missing-field rendering). Investigate any failures down to root cause in `parse.py`/`ingest.py`, fix the underlying validation gap, and update `CLAUDE.md`'s documented malformed-row statistics to match the corrected, verified behavior.

**Prompt:**
> test these using claude in chrome:
> 1. Confirm the malformed rows really got excluded — search `+1`, expect 0 results.
> 2. Case sensitivity on keyword search — `RECRUITING` vs `recruiting`, expect same count.
> 3. Job title filter exact vs partial — `manager` vs `recruiting manager`.
> 4. Multi-word skill filter — `team building` vs `team`.
> 5. Combined keyword + both filters at once — proper intersection.
> 6. Genuinely no-match query — empty-state UI renders correctly.
> 7. Field that's frequently empty — profile with blank industry still renders gracefully.
>
> [after the QA pass surfaced real leaks] yes, dig into parse.py and ingest.py to fix it.
>
> [after the fix was verified] update CLAUDE.md's malformed-row percentage to match.

**Checkpoint:** All 7 QA scenarios pass against the rebuilt backend image and re-ingested index; direct Elasticsearch queries confirm zero remaining phone-number-in-`industry` or Python-literal-in-`job_title` leaks; `uv run pytest`/`ruff`/`mypy` all clean; `.claude/CLAUDE.md`'s data handling section reflects the real, measured skip breakdown (column-count mismatch / same-length shift / exact duplicate) instead of the original column-count-only estimate.

### Task 25 — Case-insensitive filter search fix
**Do:** Verify keyword search (`q`) and both filters (`job_title`, `skill`) behave the same regardless of input casing. `q` already worked (standard analyzer lowercases both sides); `job_title`/`skill` filters didn't (`term` queries against unanalyzed `.keyword` sub-fields require exact-case matches). Fix the filters in `search_service.py` and add regression tests.

**Prompt:**
> test the search based on case sensibity or insensivity ity should work both ways i think

**Checkpoint:** Live-tested against the running Docker stack: `q=training`/`Training`/`TRAINING` all return identical results (confirms `q` was already case-insensitive). `job_title=recruiting manager` vs `Recruiting Manager` vs `RECRUITING MANAGER` all returned the same match after the fix (previously only the exact-cased value matched); non-matching filter values still correctly return zero results. Added `case_insensitive: true` to both `term` filter clauses in `search_service.py`. Added 3 regression tests (`test_keyword_search_is_case_insensitive`, `test_job_title_filter_is_case_insensitive`, `test_skill_filter_is_case_insensitive`) to `backend/tests/test_search.py`; full suite (15 tests), `ruff check`, `ruff format --check`, and `mypy` all pass.

### Task 26 — Prefix search / partial name match fix
**Do:** Fix `q` keyword search so a partial word (e.g. "jose") matches profiles whose full-name/summary/skills token starts with it (e.g. "joseph holland"), instead of requiring a whole-token match.

**Prompt:**
> when i saerch "jose" shouldnt "joseph holland" come as result? right now nothing comes

**Checkpoint:** Root cause confirmed: `multi_match`'s default `best_fields` type requires whole-token matches against the standard analyzer, so `jose` never matched the token `joseph`. Fixed by switching to `multi_match` `type: "bool_prefix"` in `search_service.py`. `uv run pytest tests/test_search.py` — all 8 existing tests still pass. Rebuilt the backend Docker image and verified live: `GET /search?q=jose` returns "joseph holland" and other "joseph"-named profiles against the real containerized stack.
