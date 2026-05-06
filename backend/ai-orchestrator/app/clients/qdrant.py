from functools import lru_cache

from qdrant_client import AsyncQdrantClient

from app.core.config import get_settings


@lru_cache
def get_qdrant() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=get_settings().qdrant_url)


# Collection names — kept stable across the codebase. Spec §6.2.
COLLECTION_POIS = "pois"
COLLECTION_POSTS = "posts"
COLLECTION_USER_TASTE = "user_taste"
