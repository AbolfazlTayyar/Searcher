# Task 23 summary

`docker compose up --build -d` failed on Windows with a bind error on `0.0.0.0:5173`. Checked `netsh interface ipv4 show excludedportrange protocol=tcp` and confirmed 5173 falls inside a Windows-reserved TCP range (`5161–5260`), almost certainly from Hyper-V/WSL's dynamic port allocator. This isn't caused by another process holding the port — Docker can never bind anywhere in that range on this machine, so the fix is to stop using that port rather than to free it up.

Remapped the frontend's published host port from `5173` to `4173` (the container still serves on port 80 internally via nginx; only the host-side mapping changed) and updated every place that referenced the old port for consistency:

- `docker-compose.yml` — frontend `ports` mapping and the backend's `CORS_ORIGINS` env var
- `.env.example` — `CORS_ORIGINS` default
- `backend/src/searcher/config.py` — `CORS_ORIGINS` default in `Settings`
- `README.md` — documented frontend URL
- `.claude/CLAUDE.md` — "How to run" section's documented frontend URL

Then ran `docker compose up --build -d` (all three services started healthy), followed by the one-off ingestion command (`docker compose run --rm backend python -m searcher.ingest.ingest`), which reported 283 indexed / 53 skipped rows — matching the ~16% malformed-row rate documented in CLAUDE.md's data handling conventions.

Verified end-to-end in a browser at `http://localhost:4173`: the page loads with the styled search UI and all 283 results by default; typing "engineer" into the search bar correctly debounced and narrowed results to 2 matches. Backend `/search` endpoint also spot-checked directly via curl.

No application logic changed — this was purely a local dev-environment port conflict and its downstream documentation/config references.
