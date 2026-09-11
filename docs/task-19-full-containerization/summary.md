## What was implemented

- **`backend/Dockerfile`** — multi-stage, `python:3.11-slim` in both stages. Builder stage installs `uv` via `pip`, syncs dependencies in a cache-friendly two-step (`--no-install-project` first so the lockfile layer is reusable, then a second `uv sync` after copying source to install the project itself). Runtime stage copies only `.venv` and `src` from the builder (no compiler toolchain, no `uv`, no lockfile), installs `curl` for the compose healthcheck, and runs `uvicorn` directly via `CMD`.
- **`frontend/Dockerfile`** — multi-stage, `node:20-slim` build stage (`npm ci` + `npm run build`) producing a static `dist/`, served by `nginx:1.27-alpine` in the runtime stage. `frontend/nginx.conf` adds an SPA fallback (`try_files ... /index.html`) so client-side routes and hard refreshes don't 404. `VITE_API_BASE_URL` is a build `ARG` (Vite inlines `VITE_*` vars at build time, not runtime), defaulted to `http://localhost:8000` and set explicitly via `docker-compose.yml`'s `build.args`.
- **`docker-compose.yml`** — added `backend` and `frontend` services alongside the existing `elasticsearch` service:
  - `backend` gets `ES_HOST=http://elasticsearch:9200` (service name, not `localhost`), mounts `./data` read-only at `/app/data`, depends on `elasticsearch` via `condition: service_healthy`, and has its own healthcheck against `/health`.
  - `frontend` depends on `backend` and is built with `VITE_API_BASE_URL=http://localhost:8000` — the browser calls the backend via its published host port, not the compose-internal service name, since the browser runs outside the compose network.
  - No dedicated `ingest` service — ingestion is documented as a single `docker compose run --rm backend python -m searcher.ingest.ingest` command (per the "clearly documented single command" option in CLAUDE.md), reusing the backend image/network rather than duplicating a service definition.
- Added `backend/.dockerignore` and `frontend/.dockerignore` to keep `.venv`/`node_modules`/build caches out of build contexts.
- Updated the "How to run" section in `.claude/CLAUDE.md` and wrote a minimal "How to run" section into the previously-empty root `README.md` (full README content is deferred to the README task).

## Deviations from the description

- **Dockerfile `# syntax=docker/dockerfile:1` directive was dropped.** BuildKit re-resolves that pinned frontend image on every build, and in this environment that lookup (plus several base-image pulls) hit repeated `TLS handshake timeout` errors against Docker Hub/ghcr.io. Since neither Dockerfile uses any syntax feature beyond the default frontend, dropping the line removed one extra flaky network round-trip without changing behavior.
- **`uv` is installed via `pip install uv` in the builder stage instead of `COPY --from=ghcr.io/astral-sh/uv:0.5`.** The ghcr.io image pull was the most persistently flaky fetch in this environment (multiple full retry passes failed). Installing `uv` from PyPI (already a required registry for the dependency install anyway) removes a third external registry dependency from the build.
- Root `README.md` got only a minimal "How to run" section, not the full architecture/design writeup — that's explicitly scoped to Task 20 in `docs/TASKS.md`, and CLAUDE.md's instruction here is just to update it "if it already exists" (it existed as an empty file).

## Verification performed

Built both images and ran the full stack locally (`docker compose build backend`, `docker compose build frontend`, then `docker compose up -d`):

- `elasticsearch` reached `healthy`.
- `backend` reached `healthy` (`curl http://localhost:8000/health` → `{"status":"ok"}`).
- Ran `docker compose run --rm backend python -m searcher.ingest.ingest` from a clean index — logged the same malformed-row pattern as local runs (283 indexed, 53 skipped of 336 rows) and wrote to `ingest.log` inside the container.
- `curl "http://localhost:8000/search?q=engineer&page_size=1" -H "Origin: http://localhost:5173"` returned real indexed results with `access-control-allow-origin: http://localhost:5173`, confirming CORS is scoped correctly for the frontend's published origin.
- Verified the frontend image serves the built SPA (`nginx` returns `200` with the built `index.html`) via a one-off `docker run` on an alternate host port.
- `docker compose down` (without `-v`) left the `searcher_es_data` volume intact.

One local-environment wrinkle: this Windows host has TCP port `5173` inside a Hyper-V/WSL dynamic-port exclusion range, so `docker compose up -d frontend`'s `5173:80` publish failed to bind *on this machine specifically* (confirmed via `netsh interface ipv4 show excludedportrange`, and reproduced independently with a plain `docker run -p 5173:80 ...`, unrelated to this project's config). `docker-compose.yml` keeps the conventional `5173:80` mapping since it matches the documented Vite dev port and is very likely free on a normal machine; anyone hitting the same collision just needs to change the left-hand side of that port mapping.
