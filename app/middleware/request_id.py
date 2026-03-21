"""
Request ID 미들웨어 — Zero Script QA 핵심 인프라

모든 HTTP 요청에 고유 request_id를 부여하고:
1. 요청 헤더 X-Request-ID가 있으면 재사용, 없으면 생성
2. ContextVar로 비동기 체인 전체에 전파
3. 응답 헤더 X-Request-ID에 반환
4. 구조화 로그에 자동 포함
"""

import uuid
import time
import logging
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ── ContextVar: 비동기 체인 전파용 ──
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_request_start_var: ContextVar[float] = ContextVar("request_start", default=0.0)


def get_request_id() -> str:
    """현재 요청의 request_id 반환. 미들웨어 밖에서도 호출 가능."""
    return _request_id_var.get("")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """X-Request-ID 생성·전파·로깅 미들웨어."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. request_id 확보 (클라이언트 제공 or 신규 생성)
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        start_time = time.time()

        # 2. ContextVar에 저장 (비동기 전파)
        _request_id_var.set(request_id)
        _request_start_var.set(start_time)

        # 3. request.state에도 저장 (라우터에서 접근용)
        request.state.request_id = request_id

        # 4. 요청 시작 로그
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "data": {
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.query_params) if request.query_params else "",
                },
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "data": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "error": str(exc)[:200],
                    },
                },
            )
            raise

        # 5. 응답 완료 로그
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "data": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            },
        )

        # 6. 응답 헤더에 request_id 반환
        response.headers["X-Request-ID"] = request_id

        # 7. 느린 응답 경고 (1초 초과)
        if duration_ms > 1000:
            logger.warning(
                "Slow response detected",
                extra={
                    "request_id": request_id,
                    "data": {
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                    },
                },
            )

        return response
