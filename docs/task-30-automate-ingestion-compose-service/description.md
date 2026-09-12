# Task 30 — Automate ingestion as a compose service

**Do:** Replace the manual `docker compose run --rm backend python -m searcher.ingest.ingest` step with a dedicated `ingest` compose service that runs automatically as part of `docker compose up --build`, so no separate command is required to get a working, populated stack.

**Prompt:**
> shouldnt this docker compose run --rm backend python -m searcher.ingest.ingest handle in code automaticaly? whats the best practice here
>
> [after discussing the manual-command vs. startup-hook vs. dedicated-service tradeoffs] automate it as a separate compose service
