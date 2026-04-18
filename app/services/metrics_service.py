"""
Prometheus 메트릭 서비스

캐시, API, 데이터베이스 성능 메트릭 수집 및 추적
"""

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    CollectorRegistry,
    REGISTRY,
)
import time
from typing import Optional, Callable
import functools


# =====================================================
# Registry 설정
# =====================================================
metrics_registry = REGISTRY


# =====================================================
# 캐시 메트릭
# =====================================================

# 캐시 히트/미스 카운터
cache_hits = Counter(
    name="cache_hits_total",
    documentation="캐시 히트 총 횟수",
    labelnames=["cache_type"],
    registry=metrics_registry,
)

cache_misses = Counter(
    name="cache_misses_total",
    documentation="캐시 미스 총 횟수",
    labelnames=["cache_type"],
    registry=metrics_registry,
)

cache_evictions = Counter(
    name="cache_evictions_total",
    documentation="캐시 퇴출(LRU) 총 횟수",
    labelnames=["cache_type"],
    registry=metrics_registry,
)

# 캐시 사이즈
cache_size = Gauge(
    name="cache_size_bytes",
    documentation="캐시 메모리 사용량 (바이트)",
    labelnames=["cache_type"],
    registry=metrics_registry,
)

cache_items = Gauge(
    name="cache_items_count",
    documentation="캐시 항목 개수",
    labelnames=["cache_type"],
    registry=metrics_registry,
)

# 캐시 히트율
cache_hit_rate = Gauge(
    name="cache_hit_rate",
    documentation="캐시 히트율 (0.0 ~ 1.0)",
    labelnames=["cache_type"],
    registry=metrics_registry,
)

# 캐시 TTL 만료
cache_expirations = Counter(
    name="cache_expirations_total",
    documentation="캐시 TTL 만료 총 횟수",
    labelnames=["cache_type"],
    registry=metrics_registry,
)


# =====================================================
# API 메트릭
# =====================================================

# API 응답 시간 (히스토그램)
http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP 요청 처리 시간 (초)",
    labelnames=["method", "endpoint", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=metrics_registry,
)

# API 요청 카운터
http_requests_total = Counter(
    name="http_requests_total",
    documentation="HTTP 요청 총 횟수",
    labelnames=["method", "endpoint", "status"],
    registry=metrics_registry,
)

# 현재 활성 요청
http_requests_in_progress = Gauge(
    name="http_requests_in_progress",
    documentation="현재 진행 중인 HTTP 요청 개수",
    labelnames=["method", "endpoint"],
    registry=metrics_registry,
)


# =====================================================
# 데이터베이스 메트릭
# =====================================================

# DB 쿼리 응답 시간
db_query_duration_seconds = Histogram(
    name="db_query_duration_seconds",
    documentation="데이터베이스 쿼리 처리 시간 (초)",
    labelnames=["query_type", "table"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=metrics_registry,
)

# DB 쿼리 카운터
db_queries_total = Counter(
    name="db_queries_total",
    documentation="데이터베이스 쿼리 총 횟수",
    labelnames=["query_type", "table", "status"],
    registry=metrics_registry,
)

# 현재 활성 DB 연결
db_connections_active = Gauge(
    name="db_connections_active",
    documentation="현재 활성 데이터베이스 연결 개수",
    registry=metrics_registry,
)


# =====================================================
# AI API 메트릭
# =====================================================

# Claude API 호출 시간
ai_request_duration_seconds = Histogram(
    name="ai_request_duration_seconds",
    documentation="AI API 요청 처리 시간 (초)",
    labelnames=["model", "operation"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 60.0),
    registry=metrics_registry,
)

# Claude API 토큰 사용량
ai_tokens_used = Counter(
    name="ai_tokens_used_total",
    documentation="AI API 총 토큰 사용량",
    labelnames=["model", "token_type"],
    registry=metrics_registry,
)

# Claude API 에러율
ai_errors_total = Counter(
    name="ai_errors_total",
    documentation="AI API 에러 총 횟수",
    labelnames=["model", "error_type"],
    registry=metrics_registry,
)


# =====================================================
# 메트릭 유틸 함수
# =====================================================

def record_cache_metric(
    cache_type: str,
    hit: bool,
    response_time_ms: float = 0,
):
    """캐시 메트릭 기록"""
    if hit:
        cache_hits.labels(cache_type=cache_type).inc()
    else:
        cache_misses.labels(cache_type=cache_type).inc()


def record_http_metric(
    method: str,
    endpoint: str,
    status: int,
    duration_seconds: float,
):
    """HTTP 요청 메트릭 기록"""
    http_requests_total.labels(
        method=method, endpoint=endpoint, status=status
    ).inc()
    http_request_duration_seconds.labels(
        method=method, endpoint=endpoint, status=status
    ).observe(duration_seconds)


def record_db_metric(
    query_type: str,
    table: str,
    status: str,
    duration_seconds: float,
):
    """DB 쿼리 메트릭 기록"""
    db_queries_total.labels(
        query_type=query_type, table=table, status=status
    ).inc()
    db_query_duration_seconds.labels(
        query_type=query_type, table=table
    ).observe(duration_seconds)


def record_ai_metric(
    model: str,
    operation: str,
    duration_seconds: float,
    tokens_used: Optional[dict] = None,
    error: bool = False,
    error_type: str = "unknown",
):
    """AI API 메트릭 기록"""
    ai_request_duration_seconds.labels(
        model=model, operation=operation
    ).observe(duration_seconds)
    
    if tokens_used:
        for token_type, count in tokens_used.items():
            ai_tokens_used.labels(
                model=model, token_type=token_type
            ).inc(count)
    
    if error:
        ai_errors_total.labels(
            model=model, error_type=error_type
        ).inc()


def update_cache_stats(
    cache_type: str,
    size_bytes: int,
    item_count: int,
    hit_count: int,
    miss_count: int,
):
    """캐시 통계 업데이트"""
    cache_size.labels(cache_type=cache_type).set(size_bytes)
    cache_items.labels(cache_type=cache_type).set(item_count)
    
    total = hit_count + miss_count
    hit_rate = hit_count / total if total > 0 else 0
    cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)


# =====================================================
# 데코레이터
# =====================================================

def track_http_metric(method: str, endpoint: str):
    """HTTP 요청 메트릭 추적 데코레이터"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                status = getattr(result, "status_code", 200)
                record_http_metric(method, endpoint, status, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_http_metric(method, endpoint, 500, duration)
                raise
        
        return wrapper
    return decorator


def track_db_metric(query_type: str, table: str):
    """DB 쿼리 메트릭 추적 데코레이터"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                record_db_metric(query_type, table, "success", duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_db_metric(query_type, table, "error", duration)
                raise
        
        return wrapper
    return decorator


def track_ai_metric(model: str, operation: str):
    """AI API 메트릭 추적 데코레이터"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # 토큰 정보가 있으면 추가 기록
                tokens = None
                if isinstance(result, dict) and "usage" in result:
                    tokens = {
                        "input": result["usage"].get("input_tokens", 0),
                        "output": result["usage"].get("output_tokens", 0),
                    }
                
                record_ai_metric(model, operation, duration, tokens, False)
                return result
            except Exception as e:
                duration = time.time() - start_time
                record_ai_metric(
                    model, operation, duration,
                    error=True, error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator
