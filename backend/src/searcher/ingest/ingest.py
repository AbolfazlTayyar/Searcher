"""One-time bulk-indexing script for the `linkedin_profiles` dataset.

Recreates the index from the explicit mapping in `mapping.py` (dropping any
existing index of the same name, since the dataset is read-only/write-once
and re-running this script is the intended way to refresh it), then bulk
loads every clean record produced by `parse.py` via the Elasticsearch bulk
API rather than one request per document.

Run with: `uv run python -m searcher.ingest.ingest`
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterator
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from searcher.config import get_settings
from searcher.ingest.mapping import PROFILE_INDEX_MAPPING, PROFILE_INDEX_SETTINGS
from searcher.ingest.parse import ProfileRecord, parse_profiles

logger = logging.getLogger(__name__)

# Same file parse.py logs to, so parse-level and bulk-level skips both land
# in one place (backend/ingest.log -- three levels up: ingest/ -> searcher/ -> src/ -> backend/).
_LOG_PATH = Path(__file__).resolve().parents[3] / "ingest.log"
_DATASET_PATH = Path(__file__).resolve().parents[4] / "data" / "300_user_linkedin.txt"


def _configure_file_logging() -> None:
    """Attach a file handler pointed at backend/ingest.log, once per process."""
    already_attached = any(
        isinstance(handler, logging.FileHandler) and Path(handler.baseFilename) == _LOG_PATH
        for handler in logger.handlers
    )
    if already_attached:
        return

    handler = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _count_data_rows(path: Path) -> int:
    """Count data rows (excluding the header) in the source CSV."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        return sum(1 for _ in reader)


def _recreate_index(client: Elasticsearch, index_name: str) -> None:
    """Drop and recreate `index_name` from the explicit mapping.

    The dataset is indexed once and never mutated in place, so a clean
    recreate on every run is simpler and safer than trying to reconcile
    mapping drift on an existing index.
    """
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        logger.info("Deleted existing index %r", index_name)

    client.indices.create(
        index=index_name,
        mappings=PROFILE_INDEX_MAPPING,
        settings=PROFILE_INDEX_SETTINGS,
    )
    logger.info("Created index %r", index_name)


def _to_bulk_actions(records: list[ProfileRecord], index_name: str) -> Iterator[dict[str, object]]:
    """Yield bulk-API index actions, one per clean record.

    No explicit `_id` -- the index is dropped and recreated on every run
    (see `_recreate_index`), so idempotency doesn't depend on a stable id,
    and a handful of source rows share a `linkedin_id` value (likely
    genuine duplicate profiles), so keying on it would silently collapse
    distinct clean records into one document.
    """
    for record in records:
        yield {"_index": index_name, "_source": record}


def run_ingestion() -> None:
    """Recreate the index and bulk-index every clean record from the dataset.

    Skips happen at two layers: `parse.py` drops rows whose column count
    doesn't match the header (logged there), and a residual set of rows
    that pass that check still carry content shifted into the wrong field
    by unescaped quotes elsewhere in the row (e.g. an address dict landing
    in `skills`) -- those surface here as Elasticsearch bulk errors, since
    the explicit mapping rejects a value of the wrong shape rather than
    silently indexing it. Both are logged to `backend/ingest.log` and
    rolled into the final skipped count so nothing is indexed under the
    wrong field silently.
    """
    _configure_file_logging()

    settings = get_settings()
    client = Elasticsearch(settings.ES_HOST)

    total_rows = _count_data_rows(_DATASET_PATH)
    records = parse_profiles(_DATASET_PATH)
    _recreate_index(client, settings.ES_INDEX_NAME)

    indexed_count, errors = bulk(
        client,
        _to_bulk_actions(records, settings.ES_INDEX_NAME),
        stats_only=False,
        raise_on_error=False,
    )
    if isinstance(errors, list):
        for error in errors:
            logger.warning("Skipping document, bulk index error: %s", error)

    client.indices.refresh(index=settings.ES_INDEX_NAME)
    client.close()

    skipped_count = total_rows - indexed_count
    logger.info(
        "Ingestion complete: %d indexed, %d skipped (of %d total rows)",
        indexed_count,
        skipped_count,
        total_rows,
    )
    print(f"Indexed: {indexed_count}")
    print(f"Skipped: {skipped_count}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_ingestion()
