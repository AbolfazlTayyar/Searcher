### Task 7 — Pydantic request/response models
**Do:** `models.py` — search request params, result item shape, paginated response envelope.

**Prompt:**
> Implement `models.py` with Pydantic models for: the search response envelope (results list, total count, page info), and an individual profile result item (only the fields the frontend actually needs to display — name, job_title, industry, skills, summary, location). Use proper types, not raw dicts.

**Checkpoint:** Models import cleanly; review field names match what you'll want to display in `ResultsList.tsx`.
