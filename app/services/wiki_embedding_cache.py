"""Wiki 임베딩 캐시 — 인메모리 TTL 캐시."""
import time
from typing import Any, Dict, Optional, Tuple

_store: Dict[str, Tuple[Any, float]] = {}
_instance: Optional["WikiEmbeddingCache"] = None


class WikiEmbeddingCache:
    async def get(self, key: str) -> Optional[Any]:
        entry = _store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del _store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        _store[key] = (value, time.time() + ttl_seconds)


async def get_wiki_cache() -> WikiEmbeddingCache:
    global _instance
    if _instance is None:
        _instance = WikiEmbeddingCache()
    return _instance
