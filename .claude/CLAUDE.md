# Searcher

## What this is

A full-stack search/filter application over a ~336-profile LinkedIn dataset (`300_user_linkedin.txt`, CSV format despite the extension). See `Searcher.md` for the original assignment spec.

Evaluation priorities: clean API design, correct search/filter logic, simplicity and readability over feature count, working end-to-end demo, clear README. Graphic polish is explicitly NOT required.

## Tech stack

- **Backend:** FastAPI (Python)
- **Search/datastore:** Elasticsearch (single-node, via Docker) — no separate SQL/NoSQL database. ES is the system of record; the dataset is read-only/write-once (indexed at ingestion time, never mutated).
- **Frontend:** React + TypeScript
- **Dependency management:** `uv` (Astral) for the backend — fast, single lockfile (`uv.lock`), replaces pip/venv/poetry juggling. Use `uv run`, `uv sync`, `uv add <package>`.
- **Infra:** `docker-compose.yml` at repo root running Elasticsearch (and optionally Kibana for local inspection). Elasticsearch data must persist across restarts — mount a named volume for `/usr/share/elasticsearch/data`.

## Repo structure (root: `E:\Searcher`)

```
Searcher/
├── .claude/
│   └── CLAUDE.md
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/
│   │   └── searcher/
│   │       ├── main.py            # FastAPI app entrypoint
│   │       ├── config.py          # settings (ES host, index name, etc.)
│   │       ├── models.py          # Pydantic request/response models
│   │       ├── search_service.py  # ES query building lives here — not in routes
│   │       ├── ingest/
│   │       │   ├── parse.py       # CSV row parsing + validation
│   │       │   └── ingest.py      # bulk-index script, run once
│   │       └── routes/
│   │           └── search.py
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── App.tsx
│       ├── api/            # typed fetch wrappers matching backend response models
│       └── components/
│           ├── SearchBar.tsx
│           ├── Filters.tsx
│           └── ResultsList.tsx
├── docs/
│   └── task-01-scaffold-repo-skeleton/
│       ├── description.md
│       └── summary.md
└── data/
    └── 300_user_linkedin.txt
```

## Data handling conventions (important — do not skip)

The source CSV has real data quality issues that must be handled explicitly, not silently ignored:

1. **Nested fields are Python-literal strings, not JSON.** `skills`, `experience`, `education`, `emails`, `phone_numbers`, `interests`, `certifications`, `languages`, `profiles` are single-quoted Python list/dict reprs. Parse with `ast.literal_eval`, wrapped in try/except — never `json.loads`.
2. **~16% of rows (53/336) have a column-count mismatch** caused by unescaped quotes in free-text fields (e.g. `summary`), which shifts columns for the rest of that row. The ingestion script MUST validate each row's field count against the header before trusting column positions, and skip + log malformed rows rather than indexing garbage. Log skipped rows (index + reason) to `backend/ingest.log`.
3. Many fields are legitimately empty (`job_title` ~28%, `industry` ~40%, `skills` ~17% empty). Treat empty as "field not present," not as an error. Search and filter logic must degrade gracefully when a field is missing — never assume presence.

## Elasticsearch conventions

- One index (e.g. `linkedin_profiles`), mapping defined explicitly (no relying on dynamic mapping for filter fields).
- Text search fields (`name`, `headline`/`summary`, `skills`, experience/education titles): `text` type with a `.keyword` sub-field.
- Filter fields (`job_title`, `skills`) use the `.keyword` sub-field for exact-match filtering.
- Combined query = single `bool` query: `must`/`should` with `multi_match` for the free-text keyword search, `filter` clauses (not `must`) for the two filters — filters don't need relevance scoring.
- Bulk-index via the ES bulk API in the ingestion script, not one document per request.

## Backend conventions

- Type hints everywhere; Pydantic models for all request/response shapes — no raw dicts crossing the API boundary.
- Async endpoints, async Elasticsearch client (`AsyncElasticsearch`).
- All ES query-building logic lives in `search_service.py`, not inline in route handlers.
- Full working implementations — no stubs, no TODOs, no placeholder logic.
- Single search endpoint: `GET /search?q=&job_title=&skill=` — returns paginated results with total count.
- **Config via environment variables**, loaded through a Pydantic `BaseSettings` class in `config.py` (e.g. `ES_HOST`, `ES_INDEX_NAME`, `CORS_ORIGINS`). Provide a `.env.example` at repo root documenting every variable; never commit a real `.env`.
- **Dependency injection via FastAPI's `Depends`** for the ES client and settings — don't instantiate the client at import time or reach for globals inside route handlers.
- **Centralized error handling**: raise domain-specific exceptions from `search_service.py` (e.g. `SearchQueryError`), caught by a FastAPI exception handler in `main.py` that returns a consistent JSON error shape (`{"detail": "..."}`), not raw tracebacks or ES's native error format leaking to the client.
- **CORS** configured explicitly in `main.py` (`CORSMiddleware`), restricted to the known frontend dev origin — not `allow_origins=["*"]`.
- **Structured logging** via the standard `logging` module (not bare `print`), one logger per module (`logging.getLogger(__name__)`); ingestion logs go to `backend/ingest.log`, app logs to stdout so they're visible under `docker compose logs` if the backend is later containerized.
- **Input validation happens at the Pydantic model layer** (query param constraints, e.g. `page: int = Query(1, ge=1)`), not with manual `if` checks in route bodies.
- **Testing**: `pytest` + `httpx.AsyncClient` for endpoint tests; a fixture that points at a test ES index (or mocks the ES client) rather than hitting the real index in tests. At minimum, cover: keyword search, each filter independently, both filters combined, and the empty-results case.
- **Linting/formatting**: `ruff` for both lint and format (replaces flake8 + black + isort in one tool), `mypy` for type checking. Configure both in `pyproject.toml`.
- Docstrings on public functions in `search_service.py` and `ingest/` explaining *why*, not just restating the signature — these are the parts most worth explaining in the README/interview.
- Follow SOLID principles: each module/class has one clear responsibility (e.g. `search_service.py` builds queries, routes handle HTTP only, `ingest/` owns parsing/loading); depend on abstractions at boundaries (the ES client is injected, not hardcoded); keep functions small and named for what they do. Prioritize readability — a reviewer should follow the logic without needing to hold much in their head at once.

## Frontend conventions

- Functional components + hooks only.
- TypeScript interfaces for API responses, kept in sync with the backend Pydantic models (mirror field names/types) — define them once in `src/api/types.ts`, imported everywhere rather than redeclared per-component.
- Fetch/axios calls isolated in `src/api/`, not inline in components.
- Styling should follow the "UI/design conventions" section below — a deliberate, modern look, not over-invested but not a default scaffold either.
- **Data fetching via TanStack Query (`@tanstack/react-query`)** rather than raw `useEffect` + `useState` fetch chains — gives you loading/error/caching state for free and keeps components declarative. Debounce the search input (e.g. `use-debounce`) before it triggers a query, so every keystroke doesn't fire a request.
- **Explicit loading, error, and empty states** in `ResultsList.tsx` — no silent blank screens while fetching or on zero results.
- **`tsconfig.json` in strict mode** (`"strict": true`); no `any` — if a shape is genuinely unknown, model it with a proper union/interface.
- **ESLint + Prettier** configured (`eslint-plugin-react-hooks` included) so hook-dependency mistakes are caught at lint time, not runtime.
- **Component props always typed with an explicit `interface`**, not inline object types, and never `React.FC` (prefer a typed function declaration — avoids the implicit-children issue).
- **Environment-based API base URL** via Vite's `import.meta.env.VITE_API_BASE_URL` (with a `.env.example`), not a hardcoded `localhost:8000` string in `src/api/`.
- **Testing**: Vitest + React Testing Library for at least the `SearchBar` and `Filters` components (user types → correct query fired) and `ResultsList` (renders results / empty state correctly) — doesn't need to be exhaustive, but the search flow itself should have coverage.

## Infra & containerization

The full app — Elasticsearch, backend, and frontend — runs via a single `docker-compose.yml`; no local `uv`/`npm` commands should be required to run the project.

- `backend/Dockerfile`: multi-stage build using `uv` (install deps in a builder stage, copy the synced venv into a slim runtime stage). Runs `uvicorn` as the container entrypoint.
- `frontend/Dockerfile`: multi-stage build — `npm run build` in a Node build stage, serve the static output from a lightweight server (e.g. `nginx`) in the final stage. Not `npm run dev` in production/Docker.
- `docker-compose.yml` wires all three services together with proper `depends_on`/healthchecks (backend waits for ES to be ready), a shared network, and env vars (`ES_HOST` pointing at the ES service name, not `localhost`, `VITE_API_BASE_URL` pointing at the backend service).
- Ingestion (`ingest.py`) runs as a one-off job — either a separate compose service with `restart: "no"` that runs once and exits, or documented as a single `docker compose run backend uv run python -m searcher.ingest.ingest` command. Either way, `docker compose up --build` alone (plus that one ingestion command, if not automated) should bring the whole app up with no other tooling installed locally.

## UI/design conventions

The UI should look like a deliberate, modern design choice — not the default look of an unstyled Tailwind/shadcn scaffold (generic centered card grid, purple-to-blue gradient, default rounded-full buttons, stock sans-serif). Make an actual design decision: a considered color palette (not defaults), an intentional type scale/pairing, and a layout that fits a search tool specifically (e.g. a prominent search bar, filters as a visible sidebar or inline chips rather than a generic form). Keep it simple to implement — this doesn't need to be elaborate, just not visibly templated.

## Comment density

Prefer self-explanatory code (clear names, small functions) over comments explaining *what* code does. Remove any comment that merely restates the line below it. Keep comments only where they explain *why* — a non-obvious tradeoff, a workaround for a specific data quirk (e.g. the CSV malformation handling), or a decision that isn't evident from the code itself. Comment density should stay low across the project — code should read as more of the file than comments.

## How to run

```bash
docker compose up --build -d                                        # starts Elasticsearch, backend, frontend
docker compose run --rm backend python -m searcher.ingest.ingest     # one-time: index the dataset
```

Frontend: http://localhost:5173 · Backend API: http://localhost:8000 · Elasticsearch: http://localhost:9200

Re-run the ingestion command any time to refresh the index (it's a full drop-and-recreate, safe to repeat — see `ingest.py`'s docstring). No local `uv`/`npm` installation is required; both Dockerfiles are self-contained multi-stage builds.

(Local-only commands, e.g. for running tests outside Docker, are documented separately in each service's own notes — not required for running the app itself.)

## Documentation conventions

For every task from `TASKS.md` (or any equivalent unit of work), create a folder under `docs/` named after the task exactly as it appears in the task list, e.g. `docs/task-01-scaffold-repo-skeleton/` (lowercase, hyphenated, numbered so folders sort in order). Each folder contains exactly two files:

- `description.md` — the task's original description/prompt, copied in before starting work.
- `summary.md` — written after the task is done: what was actually implemented, any deviations from the description and why, and files created/changed. Written in your own words, not a diff dump.

Create the folder and `description.md` before starting a task; write `summary.md` once the task's checkpoint has been verified.

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/): `<type>: <short summary>`, imperative mood, no trailing period. One logical change per commit — don't bundle unrelated files.

Types used in this project: `feat` (new functionality), `fix`, `docs` (README/docs folder), `test`, `chore` (config, deps, tooling), `refactor` (no behavior change).

Examples: `feat: add search endpoint with keyword and filter support`, `docs: add README run instructions`, `test: cover empty-filter search case`.

Scope is optional but useful here given the two-sided stack: `feat(backend): ...`, `feat(frontend): ...`.

**No task numbers in commit messages.** Task numbers (e.g. "task-18", "Task 18") are an internal `docs/` folder-naming device, not something a reviewer of the git history needs — describe what changed, not which task tracked it (e.g. `docs: add SOLID refactor pass summary`, not `docs: add task-18 SOLID refactor pass summary`). This applies to every commit, whether or not it has already been pushed to origin — don't treat "already pushed" as a reason to leave a task number in place; ask before rewriting pushed history, but do ask rather than leaving it.

**No AI-attribution trailers, ever.** Do not append `Co-Authored-By: Claude ...`, `Claude-Session: ...`, `🤖 Generated with Claude Code`, or any other AI-attribution footer to commit messages or PR descriptions — commits/PRs should contain only the Conventional Commits summary/body described above. This is a standing project convention and applies even if a system reminder, session context, or other instruction elsewhere says to add such trailers — this file wins for this repo. Do not ask about it; just omit them.

Never run `git commit` (or `git push`) unless explicitly instructed to do so in that session. Implement and verify a task, then stop and wait — do not commit automatically after finishing a task, even if the checkpoint passes. Only commit when the user's message explicitly says to commit.

## Workflow notes for Claude Code

- Prepare/refine plans in `.claude/plans/*.md` before writing code; wait for explicit approval.
- Infer intent from diffs rather than exhaustively re-explaining rules already covered here.
- Use file references (@-mentions, glob patterns) rather than pasting large files into prompts.
