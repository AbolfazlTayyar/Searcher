# Task 23 — Fix dev port conflict on Windows

**Do:** Diagnose why `docker compose up --build -d` failed to bind host port 5173, remap the frontend's published port in `docker-compose.yml`, and update every doc/config reference to the old port. Then run ingestion and verify the full stack end-to-end.

**Prompt:**
> Running `docker compose up --build -d` fails with `ports are not available: exposing port TCP 0.0.0.0:5173 -> 127.0.0.1:0: listen tcp 0.0.0.0:5173: bind: An attempt was made to access a socket in a way forbidden by its access permissions`. Diagnose the root cause (check `netsh interface ipv4 show excludedportrange protocol=tcp` for a Windows-reserved port range covering 5173), remap the frontend's host-side port in `docker-compose.yml` to a free port, and update every place that documents or configures port 5173 (`README.md`, `.claude/CLAUDE.md`, `.env.example`, backend `CORS_ORIGINS` default) to match. Bring the stack up, run the one-off ingestion command, and verify the frontend loads and the search flow works end-to-end in a browser.

**Checkpoint:** `docker compose up --build -d` starts all three services cleanly; ingestion reports the expected ~283 indexed / ~53 skipped rows; the frontend loads at the new port with default results, and typing a keyword narrows results correctly after the debounce.
