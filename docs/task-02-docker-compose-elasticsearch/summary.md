## What was implemented

`docker-compose.yml` at the repo root defines a single `elasticsearch` service (`docker.elastic.co/elasticsearch/elasticsearch:8.13.0`) configured for local development:

- `discovery.type=single-node` — no peer discovery/quorum needed for a one-node dev cluster.
- `xpack.security.enabled=false` and `xpack.security.http.ssl.enabled=false` — auth/TLS disabled for local convenience.
- `ES_JAVA_OPTS=-Xms512m -Xmx512m` — small fixed heap appropriate for a laptop dev instance.
- `ulimits.memlock` unlocked, as recommended by Elastic's Docker docs.
- Named volume `es_data` mounted at `/usr/share/elasticsearch/data` so indexed documents survive `docker compose down`/restarts.
- Port `9200` (default HTTP) published to the host.
- A `healthcheck` hitting `/_cluster/health` so `docker compose ps` / dependent services can tell when ES is actually ready, not just started.

Each dev-only setting has an inline comment explaining what the production equivalent would be (this went beyond the original task prompt, which the user explicitly asked for): keep security/TLS enabled and set `ELASTIC_PASSWORD`, size the heap to ~50% of available RAM (capped near 31-32GB for compressed oops) and pin container memory limits to match, and run a real multi-node cluster with dedicated master/data roles instead of `discovery.type=single-node`.

## Deviations from the description

- The task description didn't specify an ES version. Initially pinned to `8.15.3`, but `docker.elastic.co` (the registry Elastic images are published from) turned out to be unreachable from this network — pulls and auth-token requests both hit TLS handshake timeouts, while Docker Hub itself pulled fine (`hello-world` succeeded). The host already had `docker.elastic.co/elasticsearch/elasticsearch:8.13.0` cached locally from prior work, so the compose file was repinned to that version to unblock verification. Repin to a newer 8.x tag once the registry is reachable, if desired.
- Added a `healthcheck` block, which wasn't explicitly requested, since it's low-cost and makes "is ES actually up" checkable via `docker compose ps` instead of guessing.

## Verification status

Fully verified end-to-end:
- Docker Desktop was started and its engine confirmed ready (`docker info` succeeded).
- `docker compose up -d` created the network, named volume, and container cleanly.
- The container reached `healthy` per the compose healthcheck within ~40s.
- `curl localhost:9200` returned a valid cluster info JSON response (cluster name `docker-cluster`, version `8.13.0`).

## Files changed

- `docker-compose.yml` (created/populated at repo root)
