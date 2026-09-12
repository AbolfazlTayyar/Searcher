"""Elasticsearch query building and execution for the search API.

Kept separate from `routes/search.py` per CLAUDE.md's backend conventions --
route handlers stay thin (parse request, call this module, return the
response model) while every detail of how a keyword + two filters becomes an
ES query lives here in one place.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from elasticsearch import ApiError, AsyncElasticsearch, TransportError

from searcher.models import ProfileResult, SearchResponse

logger = logging.getLogger(__name__)

# Free-text fields searched by `q`, matching the `.keyword`-backed text
# fields declared in `ingest/mapping.py`. Weighted so a hit on the name
# ranks above the same keyword merely appearing in the free-text summary.
_SEARCH_FIELDS = ["full_name^3", "summary", "skills"]

# Maps the public `/suggest` field name to the `.keyword` sub-field it
# aggregates over -- kept separate from the filter field names in
# `_build_query` since `skill` (singular, user-facing) maps to `skills`
# (plural, the indexed field).
_SUGGEST_FIELD_PATHS: dict[str, str] = {
    "job_title": "job_title.keyword",
    "skill": "skills.keyword",
}

# Comfortably above this dataset's real distinct-value count (~336 profiles
# total), so the aggregation captures every value before Python filters it.
_SUGGEST_AGG_SIZE = 1000

# Elasticsearch's default `index.max_result_window` -- a `from`/`size` search
# rejects any request where `from + size` exceeds this. A page number far
# past the real result set (e.g. a client guessing at `page`) would otherwise
# surface as a raw ES `search_phase_execution_exception` instead of the
# empty-but-valid page it actually is.
_MAX_RESULT_WINDOW = 10_000


class SearchQueryError(Exception):
    """Raised when the search query cannot be built or executed against Elasticsearch.

    Route handlers catch this (via a FastAPI exception handler in `main.py`)
    instead of letting `elasticsearch` package exceptions -- which carry ES's
    native error shape -- leak into the HTTP response.
    """


def _build_query(q: str | None, job_title: str | None, skill: str | None) -> dict[str, Any]:
    """Build the single `bool` query combining keyword search and filters.

    The free-text keyword goes in `must` as a `multi_match` so it
    contributes to relevance scoring; `job_title`/`skill` go in `filter`
    clauses against their `.keyword` sub-fields so they narrow the result
    set without affecting score (per CLAUDE.md's ES conventions). An absent
    `q` degrades to `match_all` rather than an empty/invalid query, since
    plenty of searches are filter-only.
    """
    must: list[dict[str, Any]] = []
    if q:
        # `bool_prefix` treats the last (or only) term as a prefix match --
        # without it, a plain `multi_match` requires whole-token matches, so
        # typing "jose" would never surface "Joseph Holland" until the full
        # name was typed.
        must.append({"multi_match": {"query": q, "fields": _SEARCH_FIELDS, "type": "bool_prefix"}})
    else:
        must.append({"match_all": {}})

    # `case_insensitive` keeps the filter an exact match on the whole field
    # value (unlike a `match`, which would tokenize and allow partial hits)
    # while not requiring callers to match the indexed casing -- the `q`
    # free-text search is already case-insensitive via the standard
    # analyzer, so filters should behave the same way.
    filters: list[dict[str, Any]] = []
    if job_title:
        filters.append(
            {"term": {"job_title.keyword": {"value": job_title, "case_insensitive": True}}}
        )
    if skill:
        filters.append({"term": {"skills.keyword": {"value": skill, "case_insensitive": True}}})

    return {"bool": {"must": must, "filter": filters}}


def _hit_to_profile_result(hit: dict[str, Any]) -> ProfileResult:
    """Map a single ES hit's `_source` into the API's `ProfileResult` shape.

    `_source` is a raw dict straight from Elasticsearch, never handed to
    callers directly -- this is the one place that boundary gets crossed.
    """
    source = hit.get("_source", {})
    return ProfileResult(
        name=source.get("full_name"),
        job_title=source.get("job_title"),
        industry=source.get("industry"),
        skills=source.get("skills") or [],
        summary=source.get("summary"),
        location=source.get("location_name"),
    )


async def search_profiles(
    client: AsyncElasticsearch,
    index_name: str,
    *,
    q: str | None,
    job_title: str | None,
    skill: str | None,
    page: int,
    page_size: int,
) -> SearchResponse:
    """Run a keyword + filter search against `index_name` and return a page of results.

    Pagination is offset-based (`from`/`size`) rather than `search_after`:
    with ~336 documents total, deep pagination's cost never becomes a
    concern, and offset pagination is simpler for the frontend to drive from
    a page number.

    A `page`/`page_size` combination past Elasticsearch's `from + size`
    result-window limit is treated as a valid page with no results, rather
    than surfacing ES's rejection to the caller -- `total` still reflects the
    real count via a separate `count` call, since that request has no window
    limit of its own.
    """
    query = _build_query(q, job_title, skill)
    from_ = (page - 1) * page_size

    try:
        if from_ + page_size > _MAX_RESULT_WINDOW:
            count_response = await client.count(index=index_name, query=query)
            return SearchResponse(
                results=[], total=count_response["count"], page=page, page_size=page_size
            )

        response = await client.search(
            index=index_name,
            query=query,
            from_=from_,
            size=page_size,
        )
    except (ApiError, TransportError) as exc:
        logger.error("Elasticsearch search failed: %s", exc)
        raise SearchQueryError("Search query failed") from exc

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    return SearchResponse(
        results=[_hit_to_profile_result(hit) for hit in hits],
        total=total,
        page=page,
        page_size=page_size,
    )


async def suggest_values(
    client: AsyncElasticsearch,
    index_name: str,
    *,
    field: Literal["job_title", "skill"],
    prefix: str,
    limit: int,
) -> list[str]:
    """Return up to `limit` exact `.keyword` values for `field` starting with `prefix`.

    Exists so a UI can steer a user toward a value that will actually match
    `job_title`/`skill`'s exact-match `term` filters in `_build_query` --
    typing "manager" alone returns 0 results against a title like "recruiting
    manager" by design, and this endpoint is the discovery path for that.

    A `terms` aggregation pulls every distinct value (bounded by
    `_SUGGEST_AGG_SIZE`, comfortably above this dataset's real cardinality),
    filtered in Python against any *word* in the value starting with
    `prefix` (case-insensitive) -- e.g. prefix "manager" must surface
    "recruiting manager", not just values whose first word is "manager", or
    the suggester wouldn't actually solve the UX gap it exists for. This
    also sidesteps Elasticsearch 8.x's `include` regex, which only accepts a
    plain (case-sensitive) pattern and can't express "case-insensitive,
    matches any word" directly. A `completion` suggester was skipped as
    overkill -- the mapping has no dedicated suggester field, and at ~336
    documents this aggregate-then-filter approach is simple and fast enough.
    """
    field_path = _SUGGEST_FIELD_PATHS[field]
    prefix_lower = prefix.lower()

    try:
        response = await client.search(
            index=index_name,
            size=0,
            aggs={
                "values": {
                    "terms": {
                        "field": field_path,
                        "order": {"_count": "desc"},
                        "size": _SUGGEST_AGG_SIZE,
                    }
                }
            },
        )
    except (ApiError, TransportError) as exc:
        logger.error("Elasticsearch suggest aggregation failed: %s", exc)
        raise SearchQueryError("Suggest query failed") from exc

    buckets = response["aggregations"]["values"]["buckets"]
    matches = [
        bucket["key"]
        for bucket in buckets
        if any(word.startswith(prefix_lower) for word in bucket["key"].lower().split())
    ]
    return matches[:limit]
