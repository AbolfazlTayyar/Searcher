> Create `docker-compose.yml` at repo root running a single-node Elasticsearch instance suitable for local development (security disabled, discovery.type=single-node). Mount a named volume for the data directory so indexed data survives restarts. Expose the default HTTP port.

**Checkpoint:** `docker compose up -d` starts cleanly; `curl localhost:9200` returns a cluster info JSON response.
