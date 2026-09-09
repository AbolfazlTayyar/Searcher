Added `backend/src/searcher/ingest/mapping.py`, defining the explicit Elasticsearch mapping for the `linkedin_profiles` index so the (still-empty) ingestion script has something concrete to import when creating the index.

## What was implemented

- `PROFILE_INDEX_MAPPING`: a `properties` dict covering the fields the search API actually touches:
  - Free-text search fields (`full_name`, `summary`, `skills`, `job_title`, `job_company_name`) as `text` with a `.keyword` sub-field, so they work both for `multi_match` relevance search and exact-match/sort via `.keyword`.
  - Pure filter/categorical fields (`industry`, `job_title_role`, `job_title_levels`, `location_name`, `certifications`, `languages`, `interests`) as plain `keyword`.
  - `experience` and `education` as `nested` objects (not plain `object`), each with their own title/school name as `text` + `.keyword`. Nested was chosen over object because both are lists per profile — with plain object mapping, Elasticsearch flattens list-of-object fields into parallel arrays, which would let a query match a title from one job against a company from a different job in the same profile.
- `PROFILE_INDEX_SETTINGS`: `number_of_shards: 1`, `number_of_replicas: 0` — appropriate for a single-node dev cluster holding ~336 documents.
- All keyword fields use `ignore_above: 256` to avoid unbounded doc-value storage on stray long values.

## Deviations from the literal task description

The dataset's actual header has no `name` or `headline` field (CLAUDE.md's example names) — the real columns are `full_name` and `summary`. The mapping uses the actual dataset column names throughout, confirmed by inspecting `data/300_user_linkedin.txt`'s header and a sample parsed row (via `ast.literal_eval` on `experience`/`education`) rather than the illustrative names in CLAUDE.md.

The task only asked for name/summary/skills + job_title/skill filtering fields, but `experience` and `education` are explicitly called out elsewhere in CLAUDE.md as fields whose "titles" need text+keyword treatment, so their nested mappings were included as well rather than left to dynamic mapping.

## Files changed

- `backend/src/searcher/ingest/mapping.py` (new)
- `docs/task-05-elasticsearch-index-mapping/description.md` (new)
- `docs/task-05-elasticsearch-index-mapping/summary.md` (new)
