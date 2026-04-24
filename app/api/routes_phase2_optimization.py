"""
Phase 2 Week 2: Data-Driven Optimization API

쿼리 성능 분석, 인덱스 추천, 캐시 TTL 최적화 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.services.core.query_analyzer import get_query_analyzer, QueryAnalyzer
from app.services.core.cache_ttl_optimizer import get_cache_ttl_optimizer, CacheTTLOptimizer, CacheTTLMetrics
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/phase2", tags=["phase2-optimization"])


# ════════════════════════════════════════════════════════════════════════════
# 쿼리 성능 분석 엔드포인트
# ════════════════════════════════════════════════════════════════════════════

@router.get("/analyze/slow-queries")
async def get_slow_queries(
    p95_threshold_ms: float = 100.0,
    execution_threshold: int = 10,
):
    """
    느린 쿼리 식별
    
    P95 응답 시간이 임계값을 초과하는 쿼리 목록 반환
    
    Args:
        p95_threshold_ms: P95 응답 시간 임계값 (기본: 100ms)
        execution_threshold: 최소 실행 횟수 (기본: 10회)
    """
    analyzer = await get_query_analyzer()
    slow_queries = analyzer.identify_slow_queries(
        p95_threshold_ms=p95_threshold_ms,
        execution_threshold=execution_threshold,
    )
    
    return {
        "count": len(slow_queries),
        "slow_queries": [
            {
                "table": q.table_name,
                "type": q.query_type,
                "execution_count": q.execution_count,
                "avg_time_ms": round(q.avg_time_ms, 2),
                "p95_time_ms": round(q.p95_time_ms, 2),
                "p99_time_ms": round(q.p99_time_ms, 2),
                "error_rate": round(q.error_rate * 100, 2),
            }
            for q in slow_queries[:20]  # 상위 20개
        ],
    }


@router.get("/analyze/frequent-queries")
async def get_frequent_queries(execution_threshold: int = 100):
    """
    자주 실행되는 쿼리 식별
    
    실행 횟수가 임계값을 초과하는 쿼리 목록 반환
    
    Args:
        execution_threshold: 최소 실행 횟수 (기본: 100회)
    """
    analyzer = await get_query_analyzer()
    frequent_queries = analyzer.identify_frequent_queries(
        execution_threshold=execution_threshold,
    )
    
    return {
        "count": len(frequent_queries),
        "frequent_queries": [
            {
                "table": q.table_name,
                "type": q.query_type,
                "execution_count": q.execution_count,
                "avg_time_ms": round(q.avg_time_ms, 2),
                "throughput_per_sec": round(q.throughput_per_sec, 2),
            }
            for q in frequent_queries[:20]
        ],
    }


@router.get("/analyze/index-recommendations")
async def get_index_recommendations():
    """
    인덱스 추천
    
    느린 쿼리와 자주 실행되는 쿼리 분석을 통해
    생성 시 효과가 클 인덱스 추천
    """
    analyzer = await get_query_analyzer()
    recommendations = analyzer.recommend_indexes()
    
    return {
        "count": len(recommendations),
        "recommendations": [
            {
                "table": r.table_name,
                "columns": r.columns,
                "reason": r.reason,
                "estimated_improvement_percent": r.estimated_improvement_percent,
                "priority": r.priority,
                "frequency_score": round(r.frequency_score, 3),
            }
            for r in recommendations
        ],
    }


@router.get("/analyze/optimization-report")
async def get_optimization_report():
    """
    전체 최적화 분석 보고서
    
    느린 쿼리, 자주 실행되는 쿼리, 인덱스 추천을 포함한
    종합 분석 보고서 반환
    """
    analyzer = await get_query_analyzer()
    report = analyzer.generate_optimization_report()
    return report


# ════════════════════════════════════════════════════════════════════════════
# 캐시 TTL 동적 조정 엔드포인트
# ════════════════════════════════════════════════════════════════════════════

@router.post("/cache/optimize-ttl")
async def optimize_cache_ttl():
    """
    캐시 TTL 자동 최적화 실행
    
    현재 캐시 메트릭을 분석하여 최적의 TTL 값으로 조정
    """
    try:
        optimizer = await get_cache_ttl_optimizer()
        
        # 캐시 메트릭 수집 (Memory Cache Service에서)
        from app.services.core.memory_cache_service import get_memory_cache
        cache_service = await get_memory_cache()
        
        # 각 캐시별 메트릭 구성
        cache_metrics = {}
        for cache_name in ['kb_search', 'proposals', 'analytics', 'search_results']:
            stats = await cache_service.get_stats(cache_name)
            if stats:
                # 통계 데이터로부터 메트릭 객체 생성
                cache_metrics[cache_name] = CacheTTLMetrics(
                    cache_type=cache_name,
                    current_ttl_seconds=optimizer.get_current_ttl(cache_name),
                    hit_rate=stats.get('hit_rate', 0),
                    hit_count=stats.get('total_hits', 0),
                    miss_count=stats.get('total_misses', 0),
                    size_bytes=int(stats.get('size_bytes', 0)),
                    item_count=stats.get('item_count', 0),
                    last_updated=datetime.now(),
                )
        
        # TTL 최적화 실행
        optimizations = await optimizer.analyze_and_optimize(cache_metrics)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "optimizations": optimizations,
            "message": "캐시 TTL 최적화 완료",
        }
    
    except Exception as e:
        logger.error(f"캐시 TTL 최적화 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"TTL 최적화 실패: {str(e)}",
        )


@router.get("/cache/ttl-status")
async def get_ttl_status():
    """
    캐시 TTL 현재 상태 조회
    
    모든 캐시의 현재 TTL, 기본 TTL, 최적화 이력을 반환
    """
    optimizer = await get_cache_ttl_optimizer()
    return optimizer.get_summary()


@router.get("/cache/ttl-history/{cache_type}")
async def get_ttl_history(cache_type: str, limit: int = 20):
    """
    캐시 TTL 조정 이력 조회
    
    Args:
        cache_type: 캐시 타입 (kb_search, proposals, analytics, search_results)
        limit: 반환할 이력 개수 (기본: 20개)
    """
    optimizer = await get_cache_ttl_optimizer()
    history = optimizer.get_optimization_history(cache_type, limit)
    
    if not history:
        return {
            "cache_type": cache_type,
            "message": "조정 이력 없음",
            "history": [],
        }
    
    return {
        "cache_type": cache_type,
        "count": len(history),
        "history": history,
    }


@router.post("/cache/reset-ttl")
async def reset_ttl():
    """
    캐시 TTL을 기본값으로 리셋
    
    모든 캐시의 TTL을 초기값으로 되돌림
    """
    optimizer = await get_cache_ttl_optimizer()
    optimizer.reset_to_defaults()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "message": "캐시 TTL을 기본값으로 리셋했습니다",
        "status": optimizer.get_summary(),
    }


# ════════════════════════════════════════════════════════════════════════════
# 통합 분석 엔드포인트
# ════════════════════════════════════════════════════════════════════════════

@router.get("/analyze/full-report")
async def get_full_optimization_report():
    """
    전체 데이터 기반 최적화 분석 보고서
    
    쿼리 성능, 인덱스 추천, 캐시 TTL 상태를 모두 포함한
    종합 분석 보고서 반환
    """
    analyzer = await get_query_analyzer()
    optimizer = await get_cache_ttl_optimizer()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "query_analysis": analyzer.generate_optimization_report(),
        "cache_ttl_status": optimizer.get_summary(),
        "summary": {
            "recommendation_count": len(analyzer.index_recommendations),
            "ttl_optimization_history": len(analyzer.query_stats),
        },
    }


@router.post("/optimize/full-cycle")
async def run_full_optimization_cycle():
    """
    전체 최적화 사이클 실행
    
    1. 쿼리 성능 분석
    2. 인덱스 추천 생성
    3. 캐시 TTL 최적화
    
    모든 최적화를 한 번에 실행
    """
    try:
        client = await get_async_client()
        
        # 1. 쿼리 메트릭 수집
        analyzer = await get_query_analyzer()
        await analyzer.collect_query_metrics(client)
        
        # 2. 캐시 TTL 최적화
        optimizer = await get_cache_ttl_optimizer()
        
        from app.services.core.memory_cache_service import get_memory_cache
        cache_service = await get_memory_cache()
        
        # 캐시 메트릭 구성
        cache_metrics = {}
        for cache_name in ['kb_search', 'proposals', 'analytics', 'search_results']:
            stats = await cache_service.get_stats(cache_name)
            if stats:
                cache_metrics[cache_name] = CacheTTLMetrics(
                    cache_type=cache_name,
                    current_ttl_seconds=optimizer.get_current_ttl(cache_name),
                    hit_rate=stats.get('hit_rate', 0),
                    hit_count=stats.get('total_hits', 0),
                    miss_count=stats.get('total_misses', 0),
                    size_bytes=int(stats.get('size_bytes', 0)),
                    item_count=stats.get('item_count', 0),
                    last_updated=datetime.now(),
                )
        
        optimizations = await optimizer.analyze_and_optimize(cache_metrics)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "message": "전체 최적화 사이클 완료",
            "query_analysis": analyzer.generate_optimization_report(),
            "cache_optimizations": optimizations,
            "cache_status": optimizer.get_summary(),
        }
    
    except Exception as e:
        logger.error(f"전체 최적화 사이클 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"최적화 사이클 실패: {str(e)}",
        )


# ════════════════════════════════════════════════════════════════════════════
# 최적화 스케줄러 상태 모니터링
# ════════════════════════════════════════════════════════════════════════════

@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    최적화 스케줄러 현재 상태 조회
    
    - 총 실행 횟수
    - 성공/실패 통계
    - 마지막 실행 시간
    - 최근 에러
    """
    from app.services.domains.operations.optimization_scheduler import get_optimization_status
    return await get_optimization_status()


@router.post("/scheduler/reset-stats")
async def reset_scheduler_stats():
    """
    최적화 스케줄러 통계 초기화
    
    테스트 목적으로 실행 통계를 초기화함
    """
    from app.services.domains.operations.optimization_scheduler import reset_optimization_stats
    await reset_optimization_stats()
    return {
        "timestamp": datetime.now().isoformat(),
        "message": "스케줄러 통계가 초기화되었습니다",
    }
