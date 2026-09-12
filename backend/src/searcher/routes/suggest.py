"""`GET /suggest` route.

Mirrors `routes/search.py`'s shape: parse/validate query params, delegate to
`search_service.py`, return its response model as-is. No ES query-building
logic lives here.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from searcher.config import Settings, get_settings
from searcher.dependencies import ESClientDep
from searcher.models import SuggestResponse
from searcher.search_service import suggest_values

router = APIRouter()


@router.get("/suggest", response_model=SuggestResponse)
async def suggest(
    client: ESClientDep,
    settings: Annotated[Settings, Depends(get_settings)],
    field: Literal["job_title", "skill"] = Query(description="Filter field to suggest values for"),
    prefix: str = Query(min_length=1, description="Prefix to match values against"),
    limit: int = Query(default=10, ge=1, le=25, description="Maximum number of suggestions"),
) -> SuggestResponse:
    """Exact `job_title`/`skill` values starting with `prefix`, for filter autocomplete."""
    values = await suggest_values(
        client,
        settings.ES_INDEX_NAME,
        field=field,
        prefix=prefix,
        limit=limit,
    )
    return SuggestResponse(values=values)
