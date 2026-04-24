"""
Memory Cache Service - High-speed in-memory caching with TTL and LRU eviction

Task #3: Performance optimization (Day 5-6, 2026-04-18)
- In-memory caching for KB search results, proposals, analytics
- Configurable TTL per cache type
- LRU eviction policy with configurable max size
- Cache statistics and monitoring
- Thread-safe dictionary-based storage
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.services.domains.vault.metrics_service import (
    cache_hits,
    cache_misses,
    cache_evictions,
    cache_expirations,
    cache_size,
    cache_items,
    cache_hit_rate,
    update_cache_stats,
)

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    ttl_seconds: int
    hit_count: int = 0

    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds

    def touch(self) -> None:
        """Update access time for LRU tracking"""
        self.accessed_at = time.time()
        self.hit_count += 1


class MemoryCacheService:
    """
    High-performance in-memory cache with TTL, LRU eviction, and statistics.
    
    Features:
    - Configurable TTL per cache type
    - LRU (Least Recently Used) eviction when max size exceeded
    - Hit/miss statistics for monitoring
    - Multiple named caches (kb_search, proposals, analytics, etc.)
    """

    def __init__(self):
        self._caches: Dict[str, Dict[str, CacheEntry]] = {}
        self._max_sizes: Dict[str, int] = {}
        self._default_ttls: Dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def init_cache(
        self,
        cache_name: str,
        max_size: int = 100,
        default_ttl_seconds: int = 300,
    ) -> None:
        """
        Initialize a named cache.
        
        Args:
            cache_name: Name of cache (e.g., "kb_search", "proposals")
            max_size: Maximum entries before LRU eviction
            default_ttl_seconds: Default time-to-live in seconds
        """
        async with self._lock:
            self._caches[cache_name] = {}
            self._max_sizes[cache_name] = max_size
            self._default_ttls[cache_name] = default_ttl_seconds
            logger.info(
                f"Cache '{cache_name}' initialized: max_size={max_size}, ttl={default_ttl_seconds}s"
            )

    @staticmethod
    def _make_key(query: str, filters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate cache key from query and filters.
        
        Args:
            query: Search query or operation identifier
            filters: Optional filter dictionary
            
        Returns:
            SHA256 hash of normalized query+filters
        """
        filter_str = json.dumps(filters or {}, sort_keys=True)
        raw_key = f"{query.lower().strip()}|{filter_str}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    async def get(
        self,
        cache_name: str,
        key: str,
    ) -> Optional[Any]:
        """
        Retrieve value from cache.
        
        Args:
            cache_name: Name of cache to query
            key: Cache key (from _make_key or custom)
            
        Returns:
            Cached value if hit and not expired, None otherwise
        """
        if cache_name not in self._caches:
            cache_misses.labels(cache_type=cache_name).inc()
            return None

        async with self._lock:
            cache = self._caches[cache_name]
            if key not in cache:
                cache_misses.labels(cache_type=cache_name).inc()
                return None

            entry = cache[key]
            
            # Check expiration
            if entry.is_expired():
                del cache[key]
                cache_expirations.labels(cache_type=cache_name).inc()
                cache_misses.labels(cache_type=cache_name).inc()
                logger.debug(f"Cache miss (expired): {cache_name}/{key[:8]}...")
                return None

            # Update access time for LRU
            entry.touch()
            cache_hits.labels(cache_type=cache_name).inc()
            logger.debug(
                f"Cache hit: {cache_name}/{key[:8]}... (hits: {entry.hit_count})"
            )
            return entry.value

    async def set(
        self,
        cache_name: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """
        Store value in cache with optional TTL override.
        
        Args:
            cache_name: Name of cache
            key: Cache key
            value: Value to cache
            ttl_seconds: Override default TTL (None = use default)
            
        Returns:
            True if cached successfully, False if cache not initialized
        """
        if cache_name not in self._caches:
            logger.warning(f"Cache '{cache_name}' not initialized")
            return False

        ttl = ttl_seconds or self._default_ttls.get(cache_name, 300)
        max_size = self._max_sizes.get(cache_name, 100)

        async with self._lock:
            cache = self._caches[cache_name]

            # LRU eviction: remove least recently used entry if at capacity
            if len(cache) >= max_size and key not in cache:
                lru_key = min(
                    cache.keys(),
                    key=lambda k: cache[k].accessed_at,
                )
                del cache[lru_key]
                cache_evictions.labels(cache_type=cache_name).inc()
                logger.debug(f"LRU eviction in '{cache_name}': removed {lru_key[:8]}...")

            # Store entry
            cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                ttl_seconds=ttl,
            )
            
            # Update cache size metrics
            _update_cache_metrics(cache_name, cache)
            logger.debug(f"Cache set: {cache_name}/{key[:8]}... (ttl: {ttl}s)")
            return True

    async def delete(self, cache_name: str, key: str) -> bool:
        """
        Delete specific cache entry.
        
        Args:
            cache_name: Name of cache
            key: Key to delete
            
        Returns:
            True if deleted, False if not found
        """
        if cache_name not in self._caches:
            return False

        async with self._lock:
            cache = self._caches[cache_name]
            if key in cache:
                del cache[key]
                logger.debug(f"Cache deleted: {cache_name}/{key[:8]}...")
                return True
            return False

    async def clear(self, cache_name: str) -> int:
        """
        Clear all entries in a cache.
        
        Args:
            cache_name: Name of cache to clear
            
        Returns:
            Number of entries cleared
        """
        if cache_name not in self._caches:
            return 0

        async with self._lock:
            count = len(self._caches[cache_name])
            self._caches[cache_name].clear()
            logger.info(f"Cache cleared: {cache_name} ({count} entries)")
            return count

    async def cleanup_expired(self, cache_name: str) -> int:
        """
        Remove expired entries from cache.
        
        Useful for periodic maintenance or on-demand cleanup.
        
        Args:
            cache_name: Name of cache to clean
            
        Returns:
            Number of entries removed
        """
        if cache_name not in self._caches:
            return 0

        async with self._lock:
            cache = self._caches[cache_name]
            expired_keys = [k for k, v in cache.items() if v.is_expired()]
            
            for key in expired_keys:
                del cache[key]
            
            if expired_keys:
                logger.debug(
                    f"Cleaned {len(expired_keys)} expired entries from '{cache_name}'"
                )
            return len(expired_keys)

    async def get_stats(self, cache_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.
        
        Args:
            cache_name: Specific cache to analyze, or None for all
            
        Returns:
            Dict with size, max_size, ttl, hit_count, avg_hits, etc.
        """
        async with self._lock:
            if cache_name:
                # Stats for specific cache
                if cache_name not in self._caches:
                    return {"error": f"Cache '{cache_name}' not found"}

                cache = self._caches[cache_name]
                entries = list(cache.values())
                
                total_hits = sum(e.hit_count for e in entries)
                avg_hits = total_hits / len(entries) if entries else 0
                
                return {
                    "cache_name": cache_name,
                    "size": len(cache),
                    "max_size": self._max_sizes.get(cache_name, 0),
                    "default_ttl_seconds": self._default_ttls.get(cache_name, 0),
                    "total_hits": total_hits,
                    "avg_hits_per_entry": round(avg_hits, 2),
                    "oldest_entry_age_seconds": round(
                        time.time() - min((e.created_at for e in entries), default=0), 1
                    ),
                }
            else:
                # Stats for all caches
                stats = {}
                for name in self._caches.keys():
                    cache = self._caches[name]
                    entries = list(cache.values())
                    total_hits = sum(e.hit_count for e in entries)
                    stats[name] = {
                        "size": len(cache),
                        "max_size": self._max_sizes.get(name, 0),
                        "total_hits": total_hits,
                    }
                return stats

    async def get_all_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all caches."""
        stats = await self.get_stats(cache_name=None)
        
        # Calculate totals
        total_size = sum(s.get("size", 0) for s in stats.values())
        total_hits = sum(s.get("total_hits", 0) for s in stats.values())
        
        return {
            "timestamp": datetime.now().isoformat(),
            "caches": stats,
            "total_entries": total_size,
            "total_hits": total_hits,
            "avg_entries_per_cache": round(
                total_size / len(stats) if stats else 0, 1
            ),
        }


def _update_cache_metrics(cache_name: str, cache: Dict[str, CacheEntry]) -> None:
    """Update Prometheus metrics for cache statistics"""
    entries = list(cache.values())
    
    # Calculate cache size in bytes (rough estimate)
    cache_size_bytes = sum(
        len(str(e.value).encode()) + len(e.key.encode())
        for e in entries
    )
    
    # Calculate hit/miss ratio
    total_hits = sum(e.hit_count for e in entries)
    hit_rate = total_hits / max(1, len(entries))  # Per-entry hit count average
    
    # Update metrics
    cache_size.labels(cache_type=cache_name).set(cache_size_bytes)
    cache_items.labels(cache_type=cache_name).set(len(entries))
    cache_hit_rate.labels(cache_type=cache_name).set(min(hit_rate, 1.0))


# Global singleton instance
_memory_cache: Optional[MemoryCacheService] = None


async def get_memory_cache() -> MemoryCacheService:
    """Get or create global memory cache instance"""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCacheService()
        
        # Initialize standard caches
        await _memory_cache.init_cache(
            "kb_search",
            max_size=200,
            default_ttl_seconds=600,  # 10 minutes
        )
        await _memory_cache.init_cache(
            "proposals",
            max_size=100,
            default_ttl_seconds=300,  # 5 minutes
        )
        await _memory_cache.init_cache(
            "analytics",
            max_size=50,
            default_ttl_seconds=900,  # 15 minutes
        )
        await _memory_cache.init_cache(
            "search_results",
            max_size=150,
            default_ttl_seconds=600,  # 10 minutes
        )
    
    return _memory_cache
