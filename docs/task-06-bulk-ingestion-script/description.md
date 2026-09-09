### Task 6 — Bulk ingestion script
**Do:** `ingest/ingest.py` — creates the index with the mapping, bulk-indexes the parsed records via the ES bulk API.

**Prompt:**
> Implement `backend/src/searcher/ingest/ingest.py` as a runnable script: create the `linkedin_profiles` index using the mapping from Task 5 (recreate if it already exists), then bulk-index the clean records from `parse.py` using the Elasticsearch bulk API. Print a summary at the end (indexed count, skipped count).
