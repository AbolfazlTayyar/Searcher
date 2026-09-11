### Task 19 — Full containerization
**Do:** Add backend/Dockerfile and frontend/Dockerfile (both multi-stage), update docker-compose.yml to run Elasticsearch + backend + frontend together, and wire the ingestion step per the "Infra & containerization" section of CLAUDE.md, so the whole app runs via Docker with no local uv/npm commands required.

**Prompt:**
> Implement the "Infra & containerization" section of CLAUDE.md: create a multi-stage backend/Dockerfile (uv-based) and a multi-stage frontend/Dockerfile (Vite build, served via nginx), update docker-compose.yml to run all three services together with correct env vars (ES host as the service name, not localhost) and depends_on/healthchecks so the backend waits for Elasticsearch to be ready. Set up the ingestion step as either an automated one-off compose service or a clearly documented single command. Update the "How to run" section of CLAUDE.md and the README if it already exists.

**Checkpoint:** From a clean state (docker compose down -v), running docker compose up --build -d plus the documented ingestion command brings up the entire app with no local Python/Node tooling used — frontend reachable in the browser, search and filters working end-to-end against the containerized backend and ES.
