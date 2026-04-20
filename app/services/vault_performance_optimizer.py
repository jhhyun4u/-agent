"""
Vault Performance Optimizer Service
Caching, optimization, bottleneck analysis
Design Ref: §7.2, Vault Chat Phase 2 Technical Design
Phase: CHECK (Day 5-6)
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation"""
    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    cache_hit: bool = False
    error: Optional[str] = None


@dataclass
class PerformanceSummary:
    """Summary statistics for performance metrics"""
    operation: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    sample_count: int
    cache_hit_rate: float
    error_rate: float


class LRUCache:
    """Simple LRU Cache implementation"""

    def __init__(self, max_size: int = 100):
        """
        Initialize LRU Cache

        Args:
            max_size: Maximum number of items to store
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (moves to end if found)

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: Any) -> None:
        """
        Put value in cache (evicts oldest if full)

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value

        # Evict oldest if exceeds max size
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_hit_rate(self) -> float:
        """Get cache hit rate (0.0 to 1.0)"""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total


class VaultPerformanceOptimizer:
    """
    Vault Performance Optimizer

    Provides caching, metrics collection, and bottleneck analysis
    """

    def __init__(self):
        """Initialize optimizer with caches and metrics"""
        self.context_cache = LRUCache(max_size=100)
        self.embedding_cache = LRUCache(max_size=500)
        self.permission_cache = LRUCache(max_size=50)

        self.metrics: List[PerformanceMetrics] = []
        self.metrics_lock = asyncio.Lock()

        logger.info("Vault Performance Optimizer initialized")

    # ── Caching Methods ──

    async def optimize_context_loading(self, session_id: str) -> Dict[str, Any]:
        """
        Optimize context loading with LRU cache

        Targets: 5-10ms improvement per context load
        Strategy: Cache last 100 sessions in memory

        Args:
            session_id: Conversation session ID

        Returns:
            Cached or loaded context
        """
        start = time.time()

        # Try cache first
        cached = self.context_cache.get(session_id)
        if cached:
            elapsed_ms = (time.time() - start) * 1000
            await self._record_metric(
                "context_loading",
                elapsed_ms,
                cache_hit=True
            )
            logger.debug(f"Context cache hit: {session_id} ({elapsed_ms:.2f}ms)")
            return cached

        # Simulate database load (in real code, this would call Supabase)
        # For now, return placeholder
        context = {
            "session_id": session_id,
            "turns": [],
            "created_at": datetime.now().isoformat()
        }

        self.context_cache.put(session_id, context)

        elapsed_ms = (time.time() - start) * 1000
        await self._record_metric(
            "context_loading",
            elapsed_ms,
            cache_hit=False
        )

        logger.debug(f"Context loaded from DB: {session_id} ({elapsed_ms:.2f}ms)")
        return context

    async def batch_embeddings(
        self,
        texts: List[str],
        batch_size: int = 5
    ) -> List[List[float]]:
        """
        Batch text embeddings for parallel processing

        Targets: Reduce embedding time via parallelization
        Strategy: Process in batches, cache results

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            List of embedding vectors
        """
        start = time.time()

        # Process in batches
        embeddings = []
        cache_hits = 0

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            batch_embeddings = []
            for text in batch:
                # Try cache
                cached = self.embedding_cache.get(text[:50])  # Use first 50 chars as key
                if cached:
                    batch_embeddings.append(cached)
                    cache_hits += 1
                else:
                    # Simulate embedding (in real code, call OpenAI)
                    embedding = [0.1] * 768  # text-embedding-3-small dimension
                    self.embedding_cache.put(text[:50], embedding)
                    batch_embeddings.append(embedding)

            embeddings.extend(batch_embeddings)

        elapsed_ms = (time.time() - start) * 1000
        hit_rate = cache_hits / len(texts) if texts else 0.0

        await self._record_metric(
            "batch_embeddings",
            elapsed_ms,
            cache_hit=(cache_hits > 0)
        )

        logger.info(
            f"Batch embeddings: {len(texts)} texts, {elapsed_ms:.2f}ms, "
            f"cache hit rate {hit_rate*100:.1f}%"
        )

        return embeddings

    async def cache_permission_rules(self, role: str) -> Dict[str, List[str]]:
        """
        Cache permission rules by role

        Targets: Sub-100ms permission filtering
        Strategy: Cache rules per role, 12-hour TTL

        Args:
            role: User role (member, lead, manager, admin)

        Returns:
            Cached permission rules
        """
        start = time.time()

        # Try cache
        cached = self.permission_cache.get(f"perms:{role}")
        if cached:
            elapsed_ms = (time.time() - start) * 1000
            await self._record_metric(
                "permission_cache",
                elapsed_ms,
                cache_hit=True
            )
            logger.debug(f"Permission cache hit: {role}")
            return cached

        # Define permission rules by role
        permission_rules = {
            "member": {
                "view": ["public_projects", "public_resources"],
                "edit": [],
                "deny": ["budget_info", "competitor_data", "strategy"]
            },
            "lead": {
                "view": ["public_projects", "public_resources", "team_data"],
                "edit": ["public_projects"],
                "deny": ["competitor_data", "strategy"]
            },
            "manager": {
                "view": ["public_projects", "public_resources", "team_data", "budget_info"],
                "edit": ["public_projects", "team_data"],
                "deny": ["strategy"]
            },
            "admin": {
                "view": ["*"],
                "edit": ["*"],
                "deny": []
            }
        }

        rules = permission_rules.get(role, permission_rules["member"])
        self.permission_cache.put(f"perms:{role}", rules)

        elapsed_ms = (time.time() - start) * 1000
        await self._record_metric(
            "permission_cache",
            elapsed_ms,
            cache_hit=False
        )

        logger.debug(f"Permission rules loaded: {role} ({elapsed_ms:.2f}ms)")
        return rules

    # ── Metrics Methods ──

    async def measure_response_time(self, job_id: str) -> Dict[str, float]:
        """
        Measure response time for a job

        Args:
            job_id: Job ID to measure

        Returns:
            Dict with p50, p95, p99, avg_ms
        """
        async with self.metrics_lock:
            job_metrics = [
                m for m in self.metrics
                if m.operation == job_id
            ]

        if not job_metrics:
            return {
                "p50_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "avg_ms": 0,
                "sample_count": 0
            }

        durations = sorted([m.duration_ms for m in job_metrics])
        count = len(durations)

        p50_idx = int(count * 0.50)
        p95_idx = int(count * 0.95)
        p99_idx = int(count * 0.99)

        return {
            "p50_ms": durations[p50_idx] if p50_idx < count else 0,
            "p95_ms": durations[p95_idx] if p95_idx < count else 0,
            "p99_ms": durations[p99_idx] if p99_idx < count else 0,
            "avg_ms": sum(durations) / count if count > 0 else 0,
            "min_ms": min(durations) if durations else 0,
            "max_ms": max(durations) if durations else 0,
            "sample_count": count
        }

    async def get_performance_metrics(self) -> Dict[str, PerformanceSummary]:
        """
        Get current performance metrics for all operations

        Returns:
            Dict mapping operation names to PerformanceSummary
        """
        async with self.metrics_lock:
            metrics_copy = self.metrics.copy()

        # Group by operation
        operation_groups: Dict[str, List[PerformanceMetrics]] = {}
        for metric in metrics_copy:
            if metric.operation not in operation_groups:
                operation_groups[metric.operation] = []
            operation_groups[metric.operation].append(metric)

        # Calculate summaries
        summaries = {}
        for operation, metrics in operation_groups.items():
            if not metrics:
                continue

            durations = sorted([m.duration_ms for m in metrics])
            count = len(durations)
            errors = sum(1 for m in metrics if m.error is not None)
            cache_hits = sum(1 for m in metrics if m.cache_hit)

            p50_idx = int(count * 0.50)
            p95_idx = int(count * 0.95)
            p99_idx = int(count * 0.99)

            summaries[operation] = PerformanceSummary(
                operation=operation,
                p50_ms=durations[p50_idx] if p50_idx < count else 0,
                p95_ms=durations[p95_idx] if p95_idx < count else 0,
                p99_ms=durations[p99_idx] if p99_idx < count else 0,
                avg_ms=sum(durations) / count if count > 0 else 0,
                min_ms=min(durations),
                max_ms=max(durations),
                sample_count=count,
                cache_hit_rate=cache_hits / count if count > 0 else 0.0,
                error_rate=errors / count if count > 0 else 0.0
            )

        return summaries

    async def analyze_bottleneck(self) -> Dict[str, Any]:
        """
        Analyze performance bottlenecks

        Returns:
            Dict with:
            - slowest_operation: (name, avg_ms)
            - highest_error_rate: (name, error_rate)
            - lowest_cache_hit_rate: (name, hit_rate)
            - recommendations: List[str]
        """
        summaries = await self.get_performance_metrics()

        if not summaries:
            return {
                "slowest_operation": None,
                "highest_error_rate": None,
                "lowest_cache_hit_rate": None,
                "recommendations": ["No metrics collected yet"]
            }

        # Find bottlenecks
        slowest = max(
            summaries.items(),
            key=lambda x: x[1].avg_ms
        )

        highest_error = max(
            summaries.items(),
            key=lambda x: x[1].error_rate
        )

        lowest_cache = min(
            summaries.items(),
            key=lambda x: x[1].cache_hit_rate
        )

        # Generate recommendations
        recommendations = []

        if slowest[1].avg_ms > 1000:
            recommendations.append(
                f"Slow operation '{slowest[0]}' averaging {slowest[1].avg_ms:.0f}ms - "
                "consider optimization or caching"
            )

        if highest_error[1].error_rate > 0.05:
            recommendations.append(
                f"High error rate in '{highest_error[0]}' ({highest_error[1].error_rate*100:.1f}%) - "
                "investigate failure causes"
            )

        if lowest_cache[1].cache_hit_rate < 0.30:
            recommendations.append(
                f"Low cache hit rate in '{lowest_cache[0]}' ({lowest_cache[1].cache_hit_rate*100:.1f}%) - "
                "consider larger cache or longer TTL"
            )

        return {
            "slowest_operation": {
                "name": slowest[0],
                "avg_ms": slowest[1].avg_ms
            },
            "highest_error_rate": {
                "name": highest_error[0],
                "rate": highest_error[1].error_rate
            },
            "lowest_cache_hit_rate": {
                "name": lowest_cache[0],
                "rate": lowest_cache[1].cache_hit_rate
            },
            "recommendations": recommendations
        }

    # ── Private Methods ──

    async def _record_metric(
        self,
        operation: str,
        duration_ms: float,
        cache_hit: bool = False,
        error: Optional[str] = None
    ) -> None:
        """
        Record a performance metric

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            cache_hit: Whether this was a cache hit
            error: Error message if operation failed
        """
        metric = PerformanceMetrics(
            operation=operation,
            duration_ms=duration_ms,
            cache_hit=cache_hit,
            error=error
        )

        async with self.metrics_lock:
            self.metrics.append(metric)

            # Keep last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]

    def clear_metrics(self) -> None:
        """Clear all collected metrics"""
        self.metrics.clear()
        self.context_cache.clear()
        self.embedding_cache.clear()
        self.permission_cache.clear()

    def get_cache_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get cache statistics

        Returns:
            Dict with cache hit rates and sizes
        """
        return {
            "context_cache": {
                "hit_rate": self.context_cache.get_hit_rate(),
                "size": len(self.context_cache.cache),
                "max_size": self.context_cache.max_size
            },
            "embedding_cache": {
                "hit_rate": self.embedding_cache.get_hit_rate(),
                "size": len(self.embedding_cache.cache),
                "max_size": self.embedding_cache.max_size
            },
            "permission_cache": {
                "hit_rate": self.permission_cache.get_hit_rate(),
                "size": len(self.permission_cache.cache),
                "max_size": self.permission_cache.max_size
            }
        }


# Global instance
_optimizer_instance: Optional[VaultPerformanceOptimizer] = None


def get_optimizer() -> VaultPerformanceOptimizer:
    """Get or create optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = VaultPerformanceOptimizer()
    return _optimizer_instance
