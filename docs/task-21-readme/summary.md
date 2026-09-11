## What was done

Replaced the placeholder root `README.md` (which had a "documented in a later pass" stub for architecture/search/data-quality) with a full write-up, sourced by reading the actual implementation rather than restating CLAUDE.md:

- **How to run** — kept the existing Docker Compose + one-off ingestion commands, added a note that `.env.example` documents overridable config and that re-running ingestion is a safe full drop-and-recreate.
- **Architecture** — described the three services (Elasticsearch, FastAPI backend, React/TS frontend) and explicitly justified the no-separate-database decision: the dataset is read-only/write-once, so there's no transactional write path calling for a relational store, and Elasticsearch already natively provides every capability the app needs (relevance search, exact filtering, pagination) — a second datastore would only add a sync problem.
- **Search/filter logic** — walked through `search_service.py`'s single `bool` query: `multi_match` over `full_name^3`/`summary`/`skills` in `must` (or `match_all` when `q` is absent), `job_title`/`skill` as `term` queries against their `.keyword` sub-fields in `filter` (no score contribution), and why the mapping declares `.keyword` sub-fields explicitly instead of relying on dynamic mapping. Also noted the offset-based pagination choice given the dataset's small size.
- **Data quality** — summarized the three real issues from `ingest/parse.py`/`mapping.py`: Python-literal nested fields parsed via `ast.literal_eval` with a type check as a secondary guard against quote-shifted columns, the ~16% column-count-mismatch rows skipped and logged to `backend/ingest.log`, and legitimately empty fields normalized to `None` with every `ProfileResult` field optional.
- **Testing** — added a short section pointing at `uv run pytest` (backend) and `npm test` (frontend) as local-only commands, verified against `frontend/package.json`'s actual `test` script (there is no `backend/README.md`/`frontend/README.md` test-command doc to defer to, so the commands are stated directly).

## Deviations from the description

None in scope — the description didn't ask for a testing section, but one was added briefly since CLAUDE.md's own conventions mention `pytest`/Vitest coverage and a reviewer would otherwise have no pointer to it. Kept to one short paragraph rather than a full testing guide.

## Files changed

- `README.md` (root) — rewritten in full.
- `docs/task-21-readme/description.md`, `docs/task-21-readme/summary.md` — this task's docs folder.

## Checkpoint verification

Mentally stepped through the README's run instructions against the actual `docker-compose.yml` and ingestion entrypoint (`searcher.ingest.ingest`) — service names, ports (5173/8000/9200), and the ingestion command all match what's in the repo. No steps missing or out of order.
