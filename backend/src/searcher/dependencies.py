"""FastAPI dependency providers.

Kept separate from `main.py` so route modules can depend on `get_es_client`
without importing the app module itself (which would create a circular
import, since `main.py` mounts the routers). The client is created once at
app startup (see `main.py`'s lifespan) and handed out per-request here
rather than instantiated at import time or reached for as a global.
"""

from __future__ import annotations

from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import Depends, Request


def get_es_client(request: Request) -> AsyncElasticsearch:
    """Return the app-wide `AsyncElasticsearch` client stored on app state."""
    client: AsyncElasticsearch = request.app.state.es_client
    return client


ESClientDep = Annotated[AsyncElasticsearch, Depends(get_es_client)]
