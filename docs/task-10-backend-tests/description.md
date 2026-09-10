### Task 10 — Backend tests

**Do:** `pytest` + `httpx.AsyncClient` tests covering keyword search, each filter alone, both combined, and empty results.

**Prompt:**
> Write pytest tests in `backend/tests/` using `httpx.AsyncClient` against the FastAPI app, covering: keyword-only search, job_title filter alone, skill filter alone, both filters combined, and a query with no matches. Use a real or test ES index — don't mock ES itself, since query correctness is what's being tested.
