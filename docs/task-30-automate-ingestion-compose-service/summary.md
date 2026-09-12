## What was implemented

Added a dedicated `ingest` service to `docker-compose.yml`, built from the same `backend/Dockerfile` image, that:

- mounts `./data:/app/data:ro` (same as `backend`) so it can read the dataset,
- overrides the container command to `python -m searcher.ingest.ingest`,
- depends on `elasticsearch: condition: service_healthy` before running,
- has `restart: "no"` since it's a one-shot job, not a long-running process.

`backend` now additionally depends on `ingest: condition: service_completed_successfully`, so it only starts once ingestion has finished indexing. This required no changes to `ingest.py` itself — it already drops and recreates the index on every run, so running it as part of every `docker compose up --build` is safe and idempotent.

## Why a separate service instead of folding it into backend startup

Considered three options: keep the manual command, add a FastAPI startup-event that ingests lazily, or add a dedicated one-off compose service. Chose the dedicated service because it keeps ingestion's responsibility out of the API process (matches the existing `ingest/` module boundary and the project's SOLID conventions), avoids any race condition if the backend were ever scaled to multiple replicas, and is the standard Compose idiom for one-off jobs (`depends_on` + `service_completed_successfully` + `restart: "no"`).

## Deviations from the original CLAUDE.md wording

CLAUDE.md's "Infra & containerization" section originally presented the one-off-service and manual-command approaches as equally acceptable alternatives. Updated that section (and the "How to run" section) to reflect that the service is now the actual, automated approach — plus `README.md`'s Farsi run instructions — so `docker compose up --build` alone is documented as sufficient, with `docker compose up --build ingest` (or `docker compose run --rm ingest`) documented as the way to re-index later.

## Files changed

- `docker-compose.yml` — added the `ingest` service; added `ingest: condition: service_completed_successfully` to `backend`'s `depends_on`; removed the now-inaccurate comment on `backend`'s data volume referencing the manual `docker compose run` command.
- `.claude/CLAUDE.md` — updated the ingestion bullet under "Infra & containerization" and the "How to run" section.
- `README.md` — updated the Farsi "نحوه اجرا" (how to run) section to match.

## Verification

Ran `docker compose up --build -d` from a clean state: `searcher-ingest` started only after `searcher-elasticsearch` reported healthy, exited 0 after logging "Ingestion complete: 31 indexed, 305 skipped (of 336 total rows)", and `searcher-backend` started only after that. Confirmed `curl localhost:9200/linkedin_profiles/_count` returned 31, and `GET /health` and `GET /search` against the backend worked end-to-end with no separate ingestion command run.
