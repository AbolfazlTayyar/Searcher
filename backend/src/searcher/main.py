"""FastAPI app entrypoint: wiring only -- no query logic lives here.

Creates the single `AsyncElasticsearch` client at startup (not at import
time) and tears it down at shutdown via a lifespan context manager, mounts
the search router, configures CORS for the frontend dev origin, and
registers a handler that turns `SearchQueryError` into a consistent JSON
error shape instead of leaking ES's native error format to the client.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from searcher.config import get_settings
from searcher.routes.search import router as search_router
from searcher.search_service import SearchQueryError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.es_client = AsyncElasticsearch(settings.ES_HOST)
    try:
        yield
    finally:
        await app.state.es_client.close()


app = FastAPI(title="Searcher API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(SearchQueryError)
async def search_query_error_handler(request: Request, exc: SearchQueryError) -> JSONResponse:
    logger.error("Search query error: %s", exc)
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(search_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
