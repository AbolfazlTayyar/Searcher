# Searcher

Search/filter application over a LinkedIn profile dataset, backed by Elasticsearch.

## How to run

```bash
docker compose up --build -d                                        # starts Elasticsearch, backend, frontend
docker compose run --rm backend python -m searcher.ingest.ingest     # one-time: index the dataset
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Elasticsearch: http://localhost:9200

Re-run the ingestion command any time to refresh the index. No local `uv`/`npm` installation is required.

(Architecture, search/filter logic, and data-quality handling are documented in a later pass.)
