"""
Memory Cache Service Integration Tests (Task #3)

Verifies:
1. KB search caching and cache invalidation
2. Proposals list caching and cache invalidation
3. Cache statistics and monitoring
4. Cache hit/miss behavior
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from app.services.memory_cache_service import get_memory_cache, MemoryCacheService


class TestMemoryCacheIntegration:
    """Test memory cache integration with KB and proposals endpoints"""

    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation from query and filters"""
        service = MemoryCacheService()
        
        # Same query and filters should produce same key
        key1 = MemoryCacheService._make_key(
            query="test_query",
            filters={"area": "content", "top_k": 5}
        )
        key2 = MemoryCacheService._make_key(
            query="test_query",
            filters={"area": "content", "top_k": 5}
        )
        assert key1 == key2
        
        # Different filters should produce different key
        key3 = MemoryCacheService._make_key(
            query="test_query",
            filters={"area": "client", "top_k": 5}
        )
        assert key1 != key3
        
        # Order of filters should not matter
        key4 = MemoryCacheService._make_key(
            query="test_query",
            filters={"top_k": 5, "area": "content"}
        )
        assert key1 == key4

    @pytest.mark.asyncio
    async def test_kb_search_cache_workflow(self):
        """Test KB search cache get/set workflow"""
        cache = MemoryCacheService()
        await cache.init_cache("kb_search", max_size=200, default_ttl_seconds=600)
        
        # Generate cache key
        cache_key = MemoryCacheService._make_key(
            query="proposal strategy",
            filters={"area": "content"}
        )
        
        # Cache miss: should return None
        result = await cache.get("kb_search", cache_key)
        assert result is None
        
        # Set cache value
        test_result = {"content": [{"id": "1", "title": "Strategy"}]}
        success = await cache.set("kb_search", cache_key, test_result)
        assert success is True
        
        # Cache hit: should return value
        cached = await cache.get("kb_search", cache_key)
        assert cached == test_result
        
        # Stats should show hit count
        stats = await cache.get_stats("kb_search")
        assert stats["total_hits"] == 1

    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        """Test LRU eviction when cache exceeds max_size"""
        cache = MemoryCacheService()
        await cache.init_cache("test_cache", max_size=3, default_ttl_seconds=600)
        
        # Add 3 entries (at capacity)
        keys = []
        for i in range(3):
            key = MemoryCacheService._make_key(f"query_{i}", None)
            await cache.set("test_cache", key, f"value_{i}")
            keys.append(key)
        
        # Cache is full
        stats = await cache.get_stats("test_cache")
        assert stats["size"] == 3
        
        # Add 4th entry: should evict least recently used (oldest)
        key4 = MemoryCacheService._make_key("query_3", None)
        await cache.set("test_cache", key4, "value_3")
        
        # Still at max capacity
        stats = await cache.get_stats("test_cache")
        assert stats["size"] == 3
        
        # Oldest key should be evicted (keys[0])
        result = await cache.get("test_cache", keys[0])
        assert result is None
        
        # Newer keys should exist
        result = await cache.get("test_cache", keys[1])
        assert result == "value_1"

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test TTL expiration"""
        cache = MemoryCacheService()
        await cache.init_cache("test_cache", max_size=100, default_ttl_seconds=1)
        
        # Set value
        key = MemoryCacheService._make_key("expiring_query", None)
        await cache.set("test_cache", key, "will_expire")
        
        # Should exist immediately
        result = await cache.get("test_cache", key)
        assert result == "will_expire"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        result = await cache.get("test_cache", key)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_invalidation(self):
        """Test cache clearing for invalidation"""
        cache = MemoryCacheService()
        await cache.init_cache("kb_search", max_size=100, default_ttl_seconds=600)
        await cache.init_cache("proposals", max_size=100, default_ttl_seconds=300)
        
        # Add items to both caches
        key1 = MemoryCacheService._make_key("search1", None)
        key2 = MemoryCacheService._make_key("proposal_list", None)
        
        await cache.set("kb_search", key1, "result1")
        await cache.set("proposals", key2, "result2")
        
        # Both should have items
        stats = await cache.get_stats()
        assert stats["kb_search"]["size"] == 1
        assert stats["proposals"]["size"] == 1
        
        # Clear KB search cache (simulating content update)
        count = await cache.clear("kb_search")
        assert count == 1
        
        # KB search should be empty, proposals should remain
        stats = await cache.get_stats()
        assert stats["kb_search"]["size"] == 0
        assert stats["proposals"]["size"] == 1

    @pytest.mark.asyncio
    async def test_global_singleton_cache(self):
        """Test global singleton instance"""
        cache1 = await get_memory_cache()
        cache2 = await get_memory_cache()
        
        # Should be same instance
        assert cache1 is cache2
        
        # Should have standard caches initialized
        stats = await cache1.get_all_stats()
        assert "kb_search" in stats["caches"]
        assert "proposals" in stats["caches"]
        assert "analytics" in stats["caches"]
        assert "search_results" in stats["caches"]

    @pytest.mark.asyncio
    async def test_cache_statistics(self):
        """Test cache statistics collection"""
        cache = MemoryCacheService()
        await cache.init_cache("test_cache", max_size=100, default_ttl_seconds=600)
        
        # Add entries and simulate hits
        key1 = MemoryCacheService._make_key("query1", None)
        key2 = MemoryCacheService._make_key("query2", None)
        
        await cache.set("test_cache", key1, "result1")
        await cache.set("test_cache", key2, "result2")
        
        # Generate hits
        await cache.get("test_cache", key1)  # hit 1
        await cache.get("test_cache", key1)  # hit 2
        await cache.get("test_cache", key2)  # hit 1
        
        # Check stats
        stats = await cache.get_stats("test_cache")
        assert stats["size"] == 2
        assert stats["max_size"] == 100
        assert stats["total_hits"] == 3
        assert stats["avg_hits_per_entry"] == 1.5

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Test thread-safe concurrent operations"""
        cache = MemoryCacheService()
        await cache.init_cache("concurrent_test", max_size=100, default_ttl_seconds=600)
        
        # Simulate concurrent operations
        keys = [MemoryCacheService._make_key(f"query_{i}", None) for i in range(10)]
        
        # Set operations
        tasks = [cache.set("concurrent_test", key, f"result_{i}") for i, key in enumerate(keys)]
        results = await asyncio.gather(*tasks)
        assert all(results)
        
        # Get operations
        tasks = [cache.get("concurrent_test", key) for key in keys]
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries"""
        cache = MemoryCacheService()
        await cache.init_cache("cleanup_test", max_size=100, default_ttl_seconds=1)
        
        # Add entries
        keys = []
        for i in range(5):
            key = MemoryCacheService._make_key(f"query_{i}", None)
            await cache.set("cleanup_test", key, f"result_{i}")
            keys.append(key)
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Cleanup expired
        count = await cache.cleanup_expired("cleanup_test")
        assert count == 5
        
        # Cache should be empty
        stats = await cache.get_stats("cleanup_test")
        assert stats["size"] == 0


@pytest.mark.asyncio
async def test_kb_search_cache_usage():
    """Integration test: KB search with caching"""
    # This would be used with actual routes in an integration test
    cache = await get_memory_cache()
    
    # Simulate KB search with cache
    query = "proposal strategy"
    filters = {"area": "content", "top_k": 5}
    cache_key = MemoryCacheService._make_key(query=query, filters=filters)
    
    # First call: cache miss
    cached = await cache.get("kb_search", cache_key)
    assert cached is None
    
    # Store search result
    search_result = {
        "content": [{"id": "1", "title": "Strategy Document"}],
        "client": [],
        "competitor": [],
    }
    await cache.set("kb_search", cache_key, search_result)
    
    # Second call: cache hit
    cached = await cache.get("kb_search", cache_key)
    assert cached == search_result
    
    # Clear cache (simulating content update)
    await cache.clear("kb_search")
    
    # Third call: cache miss again
    cached = await cache.get("kb_search", cache_key)
    assert cached is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
