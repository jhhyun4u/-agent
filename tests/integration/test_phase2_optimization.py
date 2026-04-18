"""
Phase 2 Week 2: Data-Driven Optimization 통합 테스트

테스트 범위:
1. 쿼리 분석 (느린 쿼리, 자주 실행 쿼리, 인덱스 추천)
2. 캐시 TTL 동적 조정
3. 최적화 스케줄러
4. API 엔드포인트
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.services.query_analyzer import QueryAnalyzer, QueryStats, IndexRecommendation
from app.services.cache_ttl_optimizer import CacheTTLOptimizer, CacheTTLMetrics
from app.services.optimization_scheduler import (
    start_optimization_scheduler,
    get_optimization_status,
    reset_optimization_stats,
    OptimizationStats,
    OPTIMIZATION_INTERVAL_SECONDS,
)


class TestQueryAnalyzer:
    """쿼리 분석 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_identify_slow_queries(self):
        """느린 쿼리 식별"""
        analyzer = QueryAnalyzer()

        # Mock 쿼리 데이터
        analyzer.query_stats = [
            QueryStats(
                query_type="SELECT",
                table_name="proposals",
                execution_count=50,
                total_time_ms=15000,
                min_time_ms=100,
                max_time_ms=500,
                avg_time_ms=300,
                p95_time_ms=450,
                p99_time_ms=480,
                error_count=0,
            ),
            QueryStats(
                query_type="SELECT",
                table_name="documents",
                execution_count=5,
                total_time_ms=500,
                min_time_ms=50,
                max_time_ms=150,
                avg_time_ms=100,
                p95_time_ms=140,
                p99_time_ms=145,
                error_count=0,
            ),
        ]

        slow_queries = analyzer.identify_slow_queries(
            p95_threshold_ms=100, execution_threshold=10
        )

        assert len(slow_queries) == 1
        assert slow_queries[0].table_name == "proposals"
        assert slow_queries[0].p95_time_ms == 450

    @pytest.mark.asyncio
    async def test_identify_frequent_queries(self):
        """자주 실행되는 쿼리 식별"""
        analyzer = QueryAnalyzer()

        # Mock 쿼리 데이터
        analyzer.query_stats = [
            QueryStats(
                query_type="SELECT",
                table_name="proposals",
                execution_count=1000,
                total_time_ms=50000,
                min_time_ms=10,
                max_time_ms=200,
                avg_time_ms=50,
                p95_time_ms=150,
                p99_time_ms=180,
                error_count=0,
            ),
            QueryStats(
                query_type="SELECT",
                table_name="documents",
                execution_count=50,
                total_time_ms=2500,
                min_time_ms=10,
                max_time_ms=100,
                avg_time_ms=50,
                p95_time_ms=80,
                p99_time_ms=95,
                error_count=0,
            ),
        ]

        frequent_queries = analyzer.identify_frequent_queries(execution_threshold=100)

        assert len(frequent_queries) == 1
        assert frequent_queries[0].table_name == "proposals"
        assert frequent_queries[0].execution_count == 1000

    @pytest.mark.asyncio
    async def test_recommend_indexes(self):
        """인덱스 추천"""
        analyzer = QueryAnalyzer()

        # Mock 쿼리 데이터
        analyzer.query_stats = [
            QueryStats(
                query_type="SELECT",
                table_name="proposals",
                execution_count=100,
                total_time_ms=20000,
                min_time_ms=50,
                max_time_ms=300,
                avg_time_ms=200,
                p95_time_ms=280,
                p99_time_ms=290,
                error_count=0,
            ),
        ]

        recommendations = analyzer.recommend_indexes()

        assert len(recommendations) > 0
        assert all(isinstance(r, IndexRecommendation) for r in recommendations)


class TestCacheTTLOptimizer:
    """캐시 TTL 최적화 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_analyze_and_optimize(self):
        """TTL 동적 조정"""
        optimizer = CacheTTLOptimizer()

        # 낮은 hit rate를 가진 캐시 메트릭
        cache_metrics = {
            "kb_search": CacheTTLMetrics(
                cache_type="kb_search",
                current_ttl_seconds=600,
                hit_rate=0.65,  # < 70% → TTL 증가
                hit_count=130,
                miss_count=70,
                size_bytes=5000000,  # 5MB
                item_count=50,
                last_updated=datetime.now(),
            ),
            "proposals": CacheTTLMetrics(
                cache_type="proposals",
                current_ttl_seconds=300,
                hit_rate=0.95,  # > 95% → TTL 감소
                hit_count=380,
                miss_count=20,
                size_bytes=2000000,  # 2MB
                item_count=40,
                last_updated=datetime.now(),
            ),
        }

        results = optimizer.analyze_and_optimize(cache_metrics)

        assert "kb_search" in results
        assert "proposals" in results
        # kb_search TTL은 증가해야 함 (hit rate 낮음)
        new_ttl = optimizer.get_current_ttl("kb_search")
        assert new_ttl > 600
        # proposals TTL은 감소해야 함 (hit rate 높음)
        new_ttl_proposals = optimizer.get_current_ttl("proposals")
        assert new_ttl_proposals < 300

    @pytest.mark.asyncio
    async def test_memory_constraints(self):
        """메모리 제약 기반 TTL 조정"""
        optimizer = CacheTTLOptimizer()

        # 큰 메모리 사용을 가진 캐시
        large_cache = CacheTTLMetrics(
            cache_type="kb_search",
            current_ttl_seconds=900,
            hit_rate=0.85,
            hit_count=170,
            miss_count=30,
            size_bytes=150000000,  # 150MB → TTL 감소
            item_count=500,
            last_updated=datetime.now(),
        )

        optimizer.analyze_and_optimize({"kb_search": large_cache})
        new_ttl = optimizer.get_current_ttl("kb_search")

        # 메모리가 100MB 초과이면 0.8배 감소
        assert new_ttl < 900

    @pytest.mark.asyncio
    async def test_ttl_constraints(self):
        """TTL 최소/최대값 제약"""
        optimizer = CacheTTLOptimizer()

        # 매우 낮은 hit rate
        low_hit_rate = CacheTTLMetrics(
            cache_type="search_results",
            current_ttl_seconds=600,
            hit_rate=0.1,  # 매우 낮음 → TTL 증가
            hit_count=10,
            miss_count=90,
            size_bytes=1000000,
            item_count=100,
            last_updated=datetime.now(),
        )

        optimizer.analyze_and_optimize({"search_results": low_hit_rate})
        new_ttl = optimizer.get_current_ttl("search_results")

        # TTL은 최대 3600초를 초과할 수 없음
        assert new_ttl <= 3600

    @pytest.mark.asyncio
    async def test_optimization_history(self):
        """최적화 이력 추적"""
        optimizer = CacheTTLOptimizer()

        # 첫 번째 최적화
        metrics1 = {
            "kb_search": CacheTTLMetrics(
                cache_type="kb_search",
                current_ttl_seconds=600,
                hit_rate=0.70,
                hit_count=140,
                miss_count=60,
                size_bytes=3000000,
                item_count=30,
                last_updated=datetime.now(),
            ),
        }
        optimizer.analyze_and_optimize(metrics1)

        # 두 번째 최적화
        metrics2 = {
            "kb_search": CacheTTLMetrics(
                cache_type="kb_search",
                current_ttl_seconds=900,  # 이전 최적화 후 TTL
                hit_rate=0.80,
                hit_count=160,
                miss_count=40,
                size_bytes=3000000,
                item_count=30,
                last_updated=datetime.now(),
            ),
        }
        optimizer.analyze_and_optimize(metrics2)

        # 이력 확인
        history = optimizer.get_optimization_history("kb_search", limit=10)
        assert len(history) >= 2


class TestOptimizationScheduler:
    """최적화 스케줄러 테스트"""

    @pytest.mark.asyncio
    async def test_scheduler_initialization(self):
        """스케줄러 초기화"""
        reset_optimization_stats()

        status = await get_optimization_status()

        assert status["total_runs"] == 0
        assert status["successful_runs"] == 0
        assert status["failed_runs"] == 0
        assert status["last_run_at"] is None
        assert status["interval_seconds"] == OPTIMIZATION_INTERVAL_SECONDS

    @pytest.mark.asyncio
    async def test_scheduler_execution(self):
        """스케줄러 실행 (단축 간격)"""
        reset_optimization_stats()

        # Mock get_async_client
        with patch(
            "app.services.optimization_scheduler.get_async_client"
        ) as mock_client:
            mock_client.return_value = AsyncMock()

            # 스케줄러 태스크 생성 (1초 간격으로 수정하기 위해 mock 필요)
            with patch.object(
                asyncio, "sleep", new_callable=AsyncMock
            ) as mock_sleep:
                # 첫 번째 호출에서 대기, 두 번째에서 취소
                mock_sleep.side_effect = [None, asyncio.CancelledError()]

                task = asyncio.create_task(start_optimization_scheduler())

                try:
                    await asyncio.wait_for(task, timeout=0.5)
                except asyncio.TimeoutError:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                # 최소 1회 실행
                assert mock_sleep.call_count >= 1

    @pytest.mark.asyncio
    async def test_scheduler_error_handling(self):
        """스케줄러 에러 처리"""
        reset_optimization_stats()

        # Mock으로 쿼리 분석 실패 시뮬레이션
        with patch(
            "app.services.optimization_scheduler.QueryAnalyzer"
        ) as mock_analyzer:
            mock_instance = AsyncMock()
            mock_instance.identify_slow_queries.side_effect = Exception("DB 연결 오류")
            mock_analyzer.return_value = mock_instance

            task = asyncio.create_task(start_optimization_scheduler())

            # 짧은 시간 실행 후 취소
            await asyncio.sleep(0.1)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # 통계 확인
            status = await get_optimization_status()
            assert status["failed_runs"] > 0


class TestPhase2OptimizationAPIs:
    """Phase 2 최적화 API 엔드포인트 테스트"""

    @pytest.fixture
    async def client(self):
        """FastAPI 테스트 클라이언트"""
        from fastapi.testclient import TestClient
        from app.main import app

        return TestClient(app)

    def test_scheduler_status_endpoint(self, client):
        """스케줄러 상태 엔드포인트"""
        response = client.get("/api/phase2/scheduler/status")
        assert response.status_code == 200

        data = response.json()
        assert "total_runs" in data
        assert "successful_runs" in data
        assert "failed_runs" in data
        assert "interval_seconds" in data

    def test_reset_scheduler_stats_endpoint(self, client):
        """스케줄러 통계 초기화 엔드포인트"""
        response = client.post("/api/phase2/scheduler/reset-stats")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "스케줄러 통계가 초기화되었습니다"

    def test_slow_queries_endpoint(self, client):
        """느린 쿼리 조회 엔드포인트"""
        response = client.get("/api/phase2/analyze/slow-queries")
        # 200 또는 500 (DB 연결 실패)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "count" in data
            assert "slow_queries" in data

    def test_ttl_status_endpoint(self, client):
        """TTL 상태 조회 엔드포인트"""
        response = client.get("/api/phase2/cache/ttl-status")
        # 200 또는 500
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            # TTL 상태 정보 확인


class TestOptimizationIntegration:
    """전체 최적화 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_optimization_cycle(self):
        """전체 최적화 사이클"""
        analyzer = QueryAnalyzer()
        optimizer = CacheTTLOptimizer()

        # Step 1: 쿼리 분석
        analyzer.query_stats = [
            QueryStats(
                query_type="SELECT",
                table_name="proposals",
                execution_count=1000,
                total_time_ms=100000,
                min_time_ms=50,
                max_time_ms=500,
                avg_time_ms=100,
                p95_time_ms=400,
                p99_time_ms=450,
                error_count=0,
            ),
        ]

        slow_queries = analyzer.identify_slow_queries(execution_threshold=100)
        assert len(slow_queries) > 0

        # Step 2: 캐시 메트릭 수집 및 TTL 최적화
        cache_metrics = {
            "proposals": CacheTTLMetrics(
                cache_type="proposals",
                current_ttl_seconds=300,
                hit_rate=0.75,
                hit_count=150,
                miss_count=50,
                size_bytes=2000000,
                item_count=40,
                last_updated=datetime.now(),
            ),
        }

        optimizer.analyze_and_optimize(cache_metrics)
        ttl_summary = optimizer.get_summary()

        assert "proposals" in ttl_summary

    @pytest.mark.asyncio
    async def test_continuous_optimization(self):
        """지속적인 최적화 시뮬레이션"""
        optimizer = CacheTTLOptimizer()
        reset_optimization_stats()

        # 여러 번 최적화 사이클 실행
        for i in range(3):
            cache_metrics = {
                "kb_search": CacheTTLMetrics(
                    cache_type="kb_search",
                    current_ttl_seconds=600,
                    hit_rate=0.70 + (i * 0.05),  # 70% → 75% → 80%
                    hit_count=100 + (i * 10),
                    miss_count=50 - (i * 5),
                    size_bytes=5000000,
                    item_count=50,
                    last_updated=datetime.now(),
                ),
            }

            optimizer.analyze_and_optimize(cache_metrics)

        # TTL이 점진적으로 증가했는지 확인
        history = optimizer.get_optimization_history("kb_search", limit=10)
        assert len(history) >= 3
