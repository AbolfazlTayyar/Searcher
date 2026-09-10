### Task 9 — Search endpoint + wiring
**Do:** `routes/search.py`, dependency injection for the ES client, CORS middleware, exception handler, wire everything into `main.py`.

**Prompt:**
> Implement `GET /search` in `routes/search.py` accepting `q`, `job_title`, `skill`, and pagination params, using FastAPI `Depends` for the ES client, calling `search_service.py`, and returning the paginated response model. Add CORS middleware in `main.py` restricted to the frontend dev origin, and a global exception handler that catches `SearchQueryError` and returns a consistent JSON error shape.
