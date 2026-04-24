"""
Phase 2 Week 2: Performance Optimization - 정기 최적화 스케줄러

5분마다 실행:
1. 데이터베이스 쿼리 성능 분석 (pg_stat_statements)
2. 캐시 TTL 최적화 (hit rate + memory usage 기반)
3. 인덱스 추천 생성 (slow queries 분석)
4. 메트릭 수집 및 경고 확인

이 스케줄러는 app/main.py의 lifespan에서 시작되며, 백그라운드에서 지속적으로 실행된다.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.services.core.query_analyzer import QueryAnalyzer
from app.services.core.cache_ttl_optimizer import CacheTTLOptimizer
from app.services.core.memory_cache_service import get_memory_cache
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

# Phase 2 최적화 간격 (초)
OPTIMIZATION_INTERVAL_SECONDS = 300  # 5분


class OptimizationStats:
    """스케줄러 실행 통계"""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_run_at: Optional[datetime] = None
    last_error: Optional[str] = None

    @classmethod
    def reset(cls):
        cls.total_runs = 0
        cls.successful_runs = 0
        cls.failed_runs = 0
        cls.last_run_at = None
        cls.last_error = None


async def start_optimization_scheduler():
    """
    주기적 성능 최적화 스케줄러 (5분 간격)

    실행 순서:
    1. 쿼리 성능 분석 (slow queries, frequent queries, index recommendations)
    2. 캐시 메트릭 수집 (cache hit rate, size, item count)
    3. TTL 최적화 (hit rate + memory usage 기반 조정)
    4. 최적화 결과 로깅 (성공/실패 통계)

    이 함수는 application lifespan에서 asyncio.create_task()로 호출되며,
    yield 후 유지되다가 종료 시 cancel() 호출로 정리된다.
    """
    logger.info("[Phase 2] 성능 최적화 스케줄러 시작 (5분 간격)")

    query_analyzer = QueryAnalyzer()
    ttl_optimizer = CacheTTLOptimizer()

    try:
        while True:
            try:
                # 5분 대기
                await asyncio.sleep(OPTIMIZATION_INTERVAL_SECONDS)

                OptimizationStats.total_runs += 1
                logger.info(f"[Phase 2] 최적화 사이클 #{OptimizationStats.total_runs} 시작")

                client = await get_async_client()

                # 1단계: 쿼리 분석 (slow queries, recommendations)
                logger.debug("[Phase 2] 쿼리 성능 분석 중...")
                slow_queries = query_analyzer.identify_slow_queries(
                    p95_threshold_ms=100,
                    execution_threshold=10
                )
                logger.debug(f"[Phase 2] 느린 쿼리 식별: {len(slow_queries)}개")

                # 2단계: 캐시 메트릭 수집
                logger.debug("[Phase 2] 캐시 메트릭 수집 중...")
                memory_cache = await get_memory_cache()
                cache_metrics = {}
                for cache_type in ["kb_search", "proposals", "analytics", "search_results"]:
                    try:
                        stats = await memory_cache.get_stats(cache_type)
                        if stats and "size" in stats:
                            cache_metrics[cache_type] = {
                                "hit_rate": stats.get("total_hits", 0) / max(1, stats.get("size", 1)),
                                "hit_count": stats.get("total_hits", 0),
                                "miss_count": stats.get("size", 0),
                                "size_bytes": stats.get("size", 0) * 100,  # Rough estimate
                                "item_count": stats.get("size", 0),
                            }
                    except Exception as e:
                        logger.warning(f"[Phase 2] 캐시 메트릭 수집 실패 ({cache_type}): {e}")

                logger.debug(f"[Phase 2] 캐시 메트릭 수집 완료: {len(cache_metrics)}개 캐시")

                # 3단계: TTL 최적화
                logger.debug("[Phase 2] 캐시 TTL 최적화 중...")
                optimization_results = ttl_optimizer.analyze_and_optimize(cache_metrics)

                logger.info(
                    f"[Phase 2] 최적화 완료 | "
                    f"TTL 조정: {optimization_results.get('adjustments_made', 0)}개 | "
                    f"쿼리 이슈: {len(slow_queries)}개 | "
                    f"캐시: {len(cache_metrics)}개"
                )

                # 4단계: 통계 업데이트
                OptimizationStats.successful_runs += 1
                OptimizationStats.last_run_at = datetime.utcnow()
                OptimizationStats.last_error = None

            except asyncio.CancelledError:
                logger.info("[Phase 2] 최적화 스케줄러 취소됨")
                raise
            except Exception as e:
                OptimizationStats.failed_runs += 1
                OptimizationStats.last_error = str(e)
                logger.error(
                    f"[Phase 2] 최적화 사이클 실패 "
                    f"(#{OptimizationStats.total_runs}): {e}",
                    exc_info=True
                )
                # 실패해도 계속 진행 (다음 사이클 대기)
    except asyncio.CancelledError:
        # 정상 종료
        logger.info(
            f"[Phase 2] 최적화 스케줄러 종료 | "
            f"총 실행: {OptimizationStats.total_runs}, "
            f"성공: {OptimizationStats.successful_runs}, "
            f"실패: {OptimizationStats.failed_runs}"
        )
        raise


async def get_optimization_status() -> dict:
    """현재 최적화 스케줄러 상태 조회"""
    return {
        "total_runs": OptimizationStats.total_runs,
        "successful_runs": OptimizationStats.successful_runs,
        "failed_runs": OptimizationStats.failed_runs,
        "last_run_at": OptimizationStats.last_run_at.isoformat() if OptimizationStats.last_run_at else None,
        "last_error": OptimizationStats.last_error,
        "interval_seconds": OPTIMIZATION_INTERVAL_SECONDS,
    }


async def reset_optimization_stats():
    """최적화 통계 초기화 (테스트용)"""
    OptimizationStats.reset()
    logger.info("[Phase 2] 최적화 통계 초기화 완료")
