"""Elasticsearch query building and execution for the search API.

Kept separate from `routes/search.py` per CLAUDE.md's backend conventions --
route handlers stay thin (parse request, call this module, return the
response model) while every detail of how a keyword + two filters becomes an
ES query lives here in one place.
"""

from __future__ import annotations

import logging
from typing import Any

from elasticsearch import ApiError, AsyncElasticsearch, TransportError

from searcher.models import ProfileResult, SearchResponse

logger = logging.getLogger(__name__)

# Free-text fields searched by `q`, matching the `.keyword`-backed text
# fields declared in `ingest/mapping.py`. Weighted so a hit on the name
# ranks above the same keyword merely appearing in the free-text summary.
_SEARCH_FIELDS = ["full_name^3", "summary", "skills"]


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
        must.append({"multi_match": {"query": q, "fields": _SEARCH_FIELDS}})
    else:
        must.append({"match_all": {}})

    filters: list[dict[str, Any]] = []
    if job_title:
        filters.append({"term": {"job_title.keyword": job_title}})
    if skill:
        filters.append({"term": {"skills.keyword": skill}})

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
    """
    query = _build_query(q, job_title, skill)

    try:
        response = await client.search(
            index=index_name,
            query=query,
            from_=(page - 1) * page_size,
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
