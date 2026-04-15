"""
Vault Cache Service - DB-based caching for search results and routing decisions
Phase 1 implementation following g2b_cache pattern
"""

import hashlib
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.vault_schemas import SearchResult, VaultSection
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class VaultCacheService:
    """Database-backed cache service for Vault queries"""

    # Cache TTLs (in seconds)
    SEARCH_TTL = 1800      # 30 minutes for search results
    ROUTING_TTL = 3600     # 1 hour for routing decisions

    @staticmethod
    def _make_cache_key(
        query: str,
        sections: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate SHA256 cache key from query, sections, and filters.

        Ensures consistent keys for identical searches across invocations.
        """
        filter_str = json.dumps(filters or {}, sort_keys=True)
        sections_str = ",".join(sorted(sections))
        raw_key = f"{query.lower().strip()}|{sections_str}|{filter_str}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @staticmethod
    async def get_search(
        cache_key: str,
        sections: List[str]
    ) -> Optional[List[SearchResult]]:
        """
        Retrieve cached search results by key.

        Args:
            cache_key: SHA256 hash from _make_cache_key()
            sections: Section names to verify cache relevance

        Returns:
            List[SearchResult] if cache hit, None if miss or expired
        """
        try:
            client = await get_async_client()
            result = await client.table("vault_query_cache") \
                .select("response_json, hit_count") \
                .eq("cache_key", cache_key) \
                .gt("expires_at", datetime.utcnow().isoformat()) \
                .single() \
                .execute()

            if not result.data:
                return None

            # Update hit count (fire-and-forget)
            hit_count = result.data.get("hit_count", 0) + 1
            await client.table("vault_query_cache") \
                .update({"hit_count": hit_count}) \
                .eq("cache_key", cache_key) \
                .execute()

            # Parse cached response
            cached_json = result.data.get("response_json", [])
            return [SearchResult(**item) for item in cached_json]

        except Exception as e:
            logger.warning(f"Cache get error: {str(e)}")
            return None

    @staticmethod
    async def set_search(
        cache_key: str,
        results: List[SearchResult],
        sections: List[str],
        ttl: int = SEARCH_TTL
    ) -> bool:
        """
        Cache search results.

        Args:
            cache_key: SHA256 hash from _make_cache_key()
            results: SearchResult objects to cache
            sections: Section names for cache metadata
            ttl: Time-to-live in seconds (default: 30 min)

        Returns:
            True if cached successfully, False on error
        """
        try:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
            response_json = [r.model_dump(mode="json") for r in results]

            client = await get_async_client()
            await client.table("vault_query_cache").insert({
                "cache_key": cache_key,
                "response_json": response_json,
                "sections": sections,
                "expires_at": expires_at,
                "hit_count": 0,
            }).execute()

            return True

        except Exception as e:
            logger.warning(f"Cache set error: {str(e)}")
            return False

    @staticmethod
    async def get_routing(routing_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached routing decision.

        Args:
            routing_hash: Query hash for routing cache

        Returns:
            Cached routing decision dict, or None if miss/expired
        """
        try:
            client = await get_async_client()
            result = await client.table("vault_query_cache") \
                .select("response_json") \
                .eq("cache_key", routing_hash) \
                .gt("expires_at", datetime.utcnow().isoformat()) \
                .single() \
                .execute()

            return result.data.get("response_json") if result.data else None

        except Exception as e:
            logger.warning(f"Routing cache get error: {str(e)}")
            return None

    @staticmethod
    async def set_routing(
        routing_hash: str,
        decision: Dict[str, Any],
        ttl: int = ROUTING_TTL
    ) -> bool:
        """
        Cache routing decision.

        Args:
            routing_hash: Query hash
            decision: Routing decision dict with sections, filters, confidence
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if cached, False on error
        """
        try:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

            client = await get_async_client()
            await client.table("vault_query_cache").insert({
                "cache_key": routing_hash,
                "response_json": decision,
                "sections": decision.get("sections", []),
                "expires_at": expires_at,
                "hit_count": 0,
            }).execute()

            return True

        except Exception as e:
            logger.warning(f"Routing cache set error: {str(e)}")
            return False

    @staticmethod
    async def invalidate_section(section: str) -> bool:
        """
        Invalidate all cache entries for a given section.

        Useful when source data is updated.

        Args:
            section: Section name to invalidate (e.g., "completed_projects")

        Returns:
            True if invalidation succeeded, False on error
        """
        try:
            client = await get_async_client()
            await client.table("vault_query_cache") \
                .delete() \
                .contains("sections", [section]) \
                .execute()

            logger.info(f"Invalidated cache for section: {section}")
            return True

        except Exception as e:
            logger.warning(f"Cache invalidation error: {str(e)}")
            return False

    @staticmethod
    async def clear_expired() -> int:
        """
        Manually clean up expired cache entries.

        Typically called by background job, but can be triggered manually.

        Returns:
            Number of entries deleted
        """
        try:
            client = await get_async_client()
            response = await client.table("vault_query_cache") \
                .delete() \
                .lt("expires_at", datetime.utcnow().isoformat()) \
                .execute()

            deleted_count = len(response.data) if response.data else 0
            logger.info(f"Cleared {deleted_count} expired cache entries")
            return deleted_count

        except Exception as e:
            logger.warning(f"Cache cleanup error: {str(e)}")
            return 0

    @staticmethod
    async def get_stats() -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with cache_size, avg_hit_count, total_hits, expired_count
        """
        try:
            client = await get_async_client()

            # Get active cache stats
            active_stats = await client.table("vault_query_cache") \
                .select("count") \
                .gt("expires_at", datetime.utcnow().isoformat()) \
                .execute()

            active_count = active_stats.count if active_stats.count else 0

            # Get total hits
            total_result = await client.table("vault_query_cache") \
                .select("hit_count") \
                .gt("expires_at", datetime.utcnow().isoformat()) \
                .execute()

            total_hits = sum(
                item.get("hit_count", 0) for item in (total_result.data or [])
            )

            return {
                "active_entries": active_count,
                "total_hits": total_hits,
                "avg_hits_per_entry": total_hits / active_count if active_count > 0 else 0,
                "ttl_search_seconds": VaultCacheService.SEARCH_TTL,
                "ttl_routing_seconds": VaultCacheService.ROUTING_TTL,
            }

        except Exception as e:
            logger.warning(f"Cache stats error: {str(e)}")
            return {}
