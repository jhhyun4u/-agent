"""
Rate Limiting 미들웨어 — SlowAPI 기반

배포 점검 항목: API 엔드포인트 속도 제한
- 일반 API: 60 req/min per user
- AI 워크플로: 10 req/min per user
- 인증: 20 req/min per IP
"""

import hashlib

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def _key_func(request: Request) -> str:
    """인증된 사용자는 토큰 해시, 미인증은 IP 기준."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer ") and len(auth) > 20:
        token_hash = hashlib.sha256(auth.encode()).hexdigest()[:16]
        return f"user:{token_hash}"
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """429 Too Many Requests 응답."""
    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
            "detail": str(exc.detail),
        },
    )
