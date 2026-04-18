"""
메모리 모니터링 미들웨어 (M-1)

FastAPI 요청마다 메모리 사용량을 추적하여:
- 메모리 증가량 (Delta)
- 최대 메모리 사용량 (Peak)
- 메모리 누수 여부 감지

사용처:
- X-Memory-Delta 헤더로 응답 시간 메모리 변화 반환
- 메모리 로그에 기록 (app_logs 테이블)
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable

import psutil
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# 전역 메모리 통계
class MemoryStats:
    def __init__(self):
        self.peak_mb = 0.0
        self.total_requests = 0
        self.high_memory_requests = []  # 메모리 > 800MB 요청 추적

    def record(self, current_mb: float):
        """현재 메모리 기록"""
        if current_mb > self.peak_mb:
            self.peak_mb = current_mb

        self.total_requests += 1

        if current_mb > 800:  # 경고 기준
            self.high_memory_requests.append({
                "timestamp": datetime.now(),
                "memory_mb": current_mb
            })

memory_stats = MemoryStats()


class MemoryMonitorMiddleware(BaseHTTPMiddleware):
    """메모리 사용량 모니터링 미들웨어"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 메모리 측정 (Before)
        process = psutil.Process()
        mem_before_bytes = process.memory_info().rss
        mem_before_mb = mem_before_bytes / 1024 / 1024

        # 요청 처리
        response = None
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"요청 처리 오류: {e}")
            raise
        finally:
            # 메모리 측정 (After) — 예외 발생 시에도 기록
            mem_after_bytes = process.memory_info().rss
            mem_after_mb = mem_after_bytes / 1024 / 1024
            mem_delta_mb = mem_after_mb - mem_before_mb

            # 통계 기록
            memory_stats.record(mem_after_mb)

            # 응답 헤더에 추가 (응답이 있는 경우만)
            if response is not None:
                response.headers["X-Memory-Before"] = f"{mem_before_mb:.2f}MB"
                response.headers["X-Memory-After"] = f"{mem_after_mb:.2f}MB"
                response.headers["X-Memory-Delta"] = f"{mem_delta_mb:+.2f}MB"
                response.headers["X-Memory-Peak"] = f"{memory_stats.peak_mb:.2f}MB"

            # 경고 로그 (메모리 > 800MB 또는 증가량 > 100MB)
            if mem_after_mb > 800 or mem_delta_mb > 100:
                logger.warning(
                    f"⚠️ 높은 메모리 사용: "
                    f"경로={request.url.path} "
                    f"이전={mem_before_mb:.2f}MB "
                    f"현재={mem_after_mb:.2f}MB "
                    f"증가={mem_delta_mb:+.2f}MB"
                )

            # DEBUG 로그
            logger.debug(
                f"[Memory] {request.method} {request.url.path} | "
                f"Before: {mem_before_mb:.2f}MB | "
                f"After: {mem_after_mb:.2f}MB | "
                f"Delta: {mem_delta_mb:+.2f}MB"
            )

        return response


async def get_memory_stats() -> dict:
    """현재 메모리 통계 반환"""
    process = psutil.Process()
    current_mb = process.memory_info().rss / 1024 / 1024

    return {
        "current_mb": round(current_mb, 2),
        "peak_mb": round(memory_stats.peak_mb, 2),
        "total_requests": memory_stats.total_requests,
        "high_memory_count": len(memory_stats.high_memory_requests),
        "status": "normal" if current_mb < 800 else "warning"
    }


# 헬스체크 엔드포인트에 추가할 메모리 정보
def get_memory_health() -> dict:
    """헬스체크용 메모리 정보"""
    stats = asyncio.run(get_memory_stats())
    return {
        "memory": {
            "current_mb": stats["current_mb"],
            "peak_mb": stats["peak_mb"],
            "threshold_mb": 800,
            "status": "ok" if stats["current_mb"] < 800 else "warning"
        }
    }
