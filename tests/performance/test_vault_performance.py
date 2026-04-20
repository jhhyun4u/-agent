"""
Performance Benchmark Tests for Vault Chat Phase 2
Measures: Response time, context loading, permission filtering, embedding speed, digest generation
Design Ref: §7.3, Vault Chat Phase 2 Technical Design
Phase: CHECK (Day 5-6)
"""

import pytest
import asyncio
import time
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from statistics import mean, median, stdev

from app.services.vault_performance_optimizer import (
    VaultPerformanceOptimizer,
    get_optimizer
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def optimizer():
    """Get performance optimizer instance"""
    opt = get_optimizer()
    opt.clear_metrics()
    return opt


@pytest.fixture
def benchmark_results_dir():
    """Create benchmark results directory"""
    results_dir = Path(__file__).parent / "benchmark_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


# ============================================================================
# Performance Test 1: Adaptive Response Time
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
class TestAdaptiveResponseTime:
    """Benchmark: Adaptive mode response time (target P95 < 2s)"""

    async def test_adaptive_response_time_p95(self, optimizer, benchmark_results_dir):
        """
        Benchmark: P95 response time for adaptive queries

        Target: < 2 seconds (P95)
        Method: Execute 20 queries, measure response times
        """
        # Arrange
        num_iterations = 20
        response_times = []

        # Act
        for i in range(num_iterations):
            start = time.time()

            # Simulate adaptive query processing
            _ = await optimizer.optimize_context_loading(f"session_{i}")

            elapsed = (time.time() - start) * 1000  # Convert to ms
            response_times.append(elapsed)

        # Calculate percentiles
        response_times_sorted = sorted(response_times)
        p50_idx = int(len(response_times) * 0.50)
        p95_idx = int(len(response_times) * 0.95)
        p99_idx = int(len(response_times) * 0.99)

        p50 = response_times_sorted[p50_idx]
        p95 = response_times_sorted[p95_idx]
        p99 = response_times_sorted[p99_idx]
        avg = mean(response_times)

        # Assert
        assert p95 < 2000, f"P95 response time {p95:.0f}ms exceeds 2000ms target"
        assert p99 < 5000, f"P99 response time {p99:.0f}ms exceeds 5000ms target"

        # Log results
        print(f"\nAdaptive Response Time Benchmark:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms (target: < 2000ms) ✓")
        print(f"  P99: {p99:.2f}ms")
        print(f"  AVG: {avg:.2f}ms")
        print(f"  Samples: {num_iterations}")

        # Save to CSV
        _save_benchmark_results(
            benchmark_results_dir,
            "adaptive_response_time",
            response_times
        )

    async def test_adaptive_response_time_distribution(self, optimizer):
        """
        Benchmark: Response time distribution analysis

        Shows whether response times are consistent or have outliers
        """
        # Arrange
        num_iterations = 30
        response_times = []

        # Act
        for i in range(num_iterations):
            start = time.time()
            _ = await optimizer.optimize_context_loading(f"session_{i}")
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)

        # Calculate statistics
        response_times_sorted = sorted(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        avg_time = mean(response_times)
        median_time = median(response_times)

        # Calculate standard deviation
        if len(response_times) > 1:
            std_dev = stdev(response_times)
        else:
            std_dev = 0

        # Assert - Variance should be reasonable
        assert std_dev < avg_time, "Response time variance is too high"

        print(f"\nAdaptive Response Time Distribution:")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Avg: {avg_time:.2f}ms")
        print(f"  Median: {median_time:.2f}ms")
        print(f"  Std Dev: {std_dev:.2f}ms")


# ============================================================================
# Performance Test 2: Context Loading Speed
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
class TestContextLoadingSpeed:
    """Benchmark: Context loading speed with 8 turns (target P95 < 500ms)"""

    async def test_context_loading_speed_p95(self, optimizer, benchmark_results_dir):
        """
        Benchmark: P95 context loading time for 8-turn conversations

        Target: < 500ms (P95)
        Simulates loading context from database
        """
        # Arrange
        num_iterations = 20
        load_times = []

        # Act
        for i in range(num_iterations):
            start = time.time()

            # Simulate loading context with multiple turns
            for turn in range(8):
                _ = await optimizer.optimize_context_loading(f"session_{i}_turn_{turn}")

            elapsed = (time.time() - start) * 1000  # Convert to ms
            load_times.append(elapsed)

        # Calculate percentiles
        load_times_sorted = sorted(load_times)
        p50_idx = int(len(load_times) * 0.50)
        p95_idx = int(len(load_times) * 0.95)
        p99_idx = int(len(load_times) * 0.99)

        p50 = load_times_sorted[p50_idx]
        p95 = load_times_sorted[p95_idx]
        p99 = load_times_sorted[p99_idx]
        avg = mean(load_times)

        # Assert
        assert p95 < 500, f"P95 context loading {p95:.0f}ms exceeds 500ms target"

        print(f"\nContext Loading Speed Benchmark (8 turns):")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms (target: < 500ms) ✓")
        print(f"  P99: {p99:.2f}ms")
        print(f"  AVG: {avg:.2f}ms")
        print(f"  Samples: {num_iterations}")

        # Save to CSV
        _save_benchmark_results(
            benchmark_results_dir,
            "context_loading_speed",
            load_times
        )

    async def test_context_loading_with_cache(self, optimizer):
        """
        Benchmark: Context loading with cache hits vs misses

        Shows cache effectiveness (target: >60% hit rate)
        """
        # Arrange
        num_iterations = 30
        load_times_cache_miss = []
        load_times_cache_hit = []

        # Act
        for i in range(num_iterations):
            # First load: cache miss
            start = time.time()
            _ = await optimizer.optimize_context_loading(f"session_cache_{i}")
            elapsed = (time.time() - start) * 1000
            load_times_cache_miss.append(elapsed)

            # Second load: cache hit (same session)
            start = time.time()
            _ = await optimizer.optimize_context_loading(f"session_cache_{i}")
            elapsed = (time.time() - start) * 1000
            load_times_cache_hit.append(elapsed)

        # Calculate cache benefit
        avg_miss = mean(load_times_cache_miss)
        avg_hit = mean(load_times_cache_hit)
        speedup = avg_miss / avg_hit if avg_hit > 0 else 1.0

        # Get cache stats
        cache_stats = optimizer.get_cache_stats()
        context_hit_rate = cache_stats["context_cache"]["hit_rate"]

        # Assert
        assert context_hit_rate > 0.6, f"Cache hit rate {context_hit_rate*100:.1f}% < 60%"

        print(f"\nContext Loading Cache Performance:")
        print(f"  Cache miss avg: {avg_miss:.2f}ms")
        print(f"  Cache hit avg: {avg_hit:.2f}ms")
        print(f"  Speedup: {speedup:.1f}x")
        print(f"  Hit rate: {context_hit_rate*100:.1f}% (target: > 60%) ✓")


# ============================================================================
# Performance Test 3: Permission Filtering Speed
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
class TestPermissionFilteringSpeed:
    """Benchmark: Permission filtering speed (target P95 < 100ms)"""

    async def test_permission_filtering_speed_p95(self, optimizer, benchmark_results_dir):
        """
        Benchmark: P95 permission rule lookup and filtering

        Target: < 100ms (P95)
        Includes role-based permission caching
        """
        # Arrange
        roles = ["member", "lead", "manager", "admin"]
        num_iterations = 20
        filter_times = []

        # Act
        for i in range(num_iterations):
            role = roles[i % len(roles)]
            start = time.time()

            # Simulate permission filtering
            _ = await optimizer.cache_permission_rules(role)

            elapsed = (time.time() - start) * 1000  # Convert to ms
            filter_times.append(elapsed)

        # Calculate percentiles
        filter_times_sorted = sorted(filter_times)
        p50_idx = int(len(filter_times) * 0.50)
        p95_idx = int(len(filter_times) * 0.95)
        p99_idx = int(len(filter_times) * 0.99)

        p50 = filter_times_sorted[p50_idx]
        p95 = filter_times_sorted[p95_idx]
        p99 = filter_times_sorted[p99_idx]
        avg = mean(filter_times)

        # Assert
        assert p95 < 100, f"P95 permission filtering {p95:.0f}ms exceeds 100ms target"

        print(f"\nPermission Filtering Speed Benchmark:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms (target: < 100ms) ✓")
        print(f"  P99: {p99:.2f}ms")
        print(f"  AVG: {avg:.2f}ms")
        print(f"  Samples: {num_iterations}")

        # Save to CSV
        _save_benchmark_results(
            benchmark_results_dir,
            "permission_filtering_speed",
            filter_times
        )


# ============================================================================
# Performance Test 4: Embedding Batch Speed
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
class TestEmbeddingBatchSpeed:
    """Benchmark: Batch embedding speed (target P95 < 1s for 10 texts)"""

    async def test_embedding_batch_speed_p95(self, optimizer, benchmark_results_dir):
        """
        Benchmark: P95 batch embedding time for 10 texts

        Target: < 1 second (P95)
        Tests vectorization efficiency
        """
        # Arrange
        num_iterations = 20
        texts_per_batch = 10
        batch_times = []

        # Create sample texts
        sample_texts = [
            f"Sample text {i} for embedding test with meaningful content"
            for i in range(texts_per_batch)
        ]

        # Act
        for _ in range(num_iterations):
            start = time.time()

            # Simulate batch embedding
            _ = await optimizer.batch_embeddings(sample_texts, batch_size=5)

            elapsed = (time.time() - start) * 1000  # Convert to ms
            batch_times.append(elapsed)

        # Calculate percentiles
        batch_times_sorted = sorted(batch_times)
        p50_idx = int(len(batch_times) * 0.50)
        p95_idx = int(len(batch_times) * 0.95)
        p99_idx = int(len(batch_times) * 0.99)

        p50 = batch_times_sorted[p50_idx]
        p95 = batch_times_sorted[p95_idx]
        p99 = batch_times_sorted[p99_idx]
        avg = mean(batch_times)

        # Assert
        assert p95 < 1000, f"P95 embedding time {p95:.0f}ms exceeds 1000ms target"

        print(f"\nEmbedding Batch Speed Benchmark (10 texts):")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms (target: < 1000ms) ✓")
        print(f"  P99: {p99:.2f}ms")
        print(f"  AVG: {avg:.2f}ms")
        print(f"  Samples: {num_iterations}")

        # Save to CSV
        _save_benchmark_results(
            benchmark_results_dir,
            "embedding_batch_speed",
            batch_times
        )

    async def test_embedding_cache_effectiveness(self, optimizer):
        """
        Benchmark: Embedding cache hit rate and speedup

        Shows cache effectiveness for repeated texts
        """
        # Arrange
        num_iterations = 20
        texts = ["Repeated text for caching test"] * 10
        embed_times_miss = []
        embed_times_hit = []

        # Act
        for _ in range(num_iterations):
            # First batch: cache miss
            start = time.time()
            _ = await optimizer.batch_embeddings(texts[:5])
            elapsed = (time.time() - start) * 1000
            embed_times_miss.append(elapsed)

            # Second batch: cache hit
            start = time.time()
            _ = await optimizer.batch_embeddings(texts[:5])
            elapsed = (time.time() - start) * 1000
            embed_times_hit.append(elapsed)

        # Calculate cache benefit
        avg_miss = mean(embed_times_miss)
        avg_hit = mean(embed_times_hit)
        speedup = avg_miss / avg_hit if avg_hit > 0 else 1.0

        # Get cache stats
        cache_stats = optimizer.get_cache_stats()
        embed_hit_rate = cache_stats["embedding_cache"]["hit_rate"]

        print(f"\nEmbedding Cache Effectiveness:")
        print(f"  Cache miss avg: {avg_miss:.2f}ms")
        print(f"  Cache hit avg: {avg_hit:.2f}ms")
        print(f"  Speedup: {speedup:.1f}x")
        print(f"  Hit rate: {embed_hit_rate*100:.1f}%")


# ============================================================================
# Performance Test 5: Digest Generation Speed
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
class TestDigestGenerationSpeed:
    """Benchmark: Digest generation speed (target < 5s)"""

    async def test_digest_generation_speed(self, optimizer, benchmark_results_dir):
        """
        Benchmark: Time to generate daily digest

        Target: < 5 seconds
        Includes context loading + keyword search + formatting
        """
        # Arrange
        num_iterations = 10
        digest_times = []

        # Act
        for i in range(num_iterations):
            start = time.time()

            # Simulate digest generation:
            # 1. Load team config
            _ = await optimizer.cache_permission_rules("admin")

            # 2. Load context for keywords
            for _ in range(3):
                _ = await optimizer.optimize_context_loading(f"digest_{i}")

            # 3. Generate embeddings for keyword matching
            keywords = ["G2B:스마트팩토리", "competitor:OOO사", "tech:AI"]
            _ = await optimizer.batch_embeddings(keywords)

            elapsed = (time.time() - start) * 1000  # Convert to ms
            digest_times.append(elapsed)

        # Calculate statistics
        digest_times_sorted = sorted(digest_times)
        p50_idx = int(len(digest_times) * 0.50)
        p95_idx = int(len(digest_times) * 0.95)

        p50 = digest_times_sorted[p50_idx]
        p95 = digest_times_sorted[p95_idx]
        avg = mean(digest_times)

        # Assert
        assert p95 < 5000, f"P95 digest generation {p95:.0f}ms exceeds 5000ms target"

        print(f"\nDigest Generation Speed Benchmark:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms (target: < 5000ms) ✓")
        print(f"  AVG: {avg:.2f}ms")
        print(f"  Samples: {num_iterations}")

        # Save to CSV
        _save_benchmark_results(
            benchmark_results_dir,
            "digest_generation_speed",
            digest_times
        )


# ============================================================================
# Performance Test 6: Bottleneck Analysis
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
class TestBottleneckAnalysis:
    """Analyze performance bottlenecks and cache effectiveness"""

    async def test_bottleneck_detection(self, optimizer):
        """
        Benchmark: Identify slowest operations and cache hit rates

        Helps prioritize optimization efforts
        """
        # Arrange - Run various operations
        num_iterations = 15

        # Simulate operations
        for i in range(num_iterations):
            # Context loading
            await optimizer.optimize_context_loading(f"bench_context_{i}")

            # Permission filtering
            await optimizer.cache_permission_rules(["member", "lead", "admin"][i % 3])

            # Embeddings
            await optimizer.batch_embeddings([f"text_{i}"] * 5)

        # Act - Analyze bottlenecks
        bottleneck_analysis = await optimizer.analyze_bottleneck()

        # Assert
        assert bottleneck_analysis is not None
        assert "slowest_operation" in bottleneck_analysis
        assert "recommendations" in bottleneck_analysis

        # Log bottleneck analysis
        print(f"\nBottleneck Analysis:")
        print(f"  Slowest operation: {bottleneck_analysis['slowest_operation']['name']}")
        print(f"    Avg time: {bottleneck_analysis['slowest_operation']['avg_ms']:.2f}ms")

        if bottleneck_analysis["recommendations"]:
            print(f"  Recommendations:")
            for rec in bottleneck_analysis["recommendations"]:
                print(f"    - {rec}")

    async def test_cache_statistics(self, optimizer):
        """
        Benchmark: Overall cache effectiveness

        Shows hit rates for all cache types
        """
        # Arrange - Run operations to populate caches
        for i in range(30):
            # Context cache
            await optimizer.optimize_context_loading(f"cache_test_{i}")

            # Permission cache
            await optimizer.cache_permission_rules(["member", "lead"][i % 2])

            # Embedding cache
            await optimizer.batch_embeddings([f"text_{i % 5}"] * 3)

        # Act - Get cache stats
        cache_stats = optimizer.get_cache_stats()

        # Assert
        print(f"\nCache Statistics:")
        for cache_name, stats in cache_stats.items():
            print(f"  {cache_name}:")
            print(f"    Hit rate: {stats['hit_rate']*100:.1f}%")
            print(f"    Size: {stats['size']} / {stats['max_size']}")


# ============================================================================
# Helper Functions
# ============================================================================

def _save_benchmark_results(
    results_dir: Path,
    benchmark_name: str,
    measurements: List[float]
) -> None:
    """
    Save benchmark results to CSV

    Args:
        results_dir: Directory to save results
        benchmark_name: Name of benchmark
        measurements: List of measurements (ms)
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = results_dir / f"{benchmark_name}_{timestamp}.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Iteration", "Time (ms)"])
        for i, measurement in enumerate(measurements, 1):
            writer.writerow([i, f"{measurement:.2f}"])

    print(f"  Saved to: {filename}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])
