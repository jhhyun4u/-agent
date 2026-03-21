"""
보안 헤더 미들웨어 (L-1, L-2)

OWASP 권장 보안 헤더를 모든 응답에 자동 추가.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """HSTS + X-Content-Type-Options + X-Frame-Options 등 보안 헤더 추가."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # L-1: HSTS (HTTPS 강제, 1년)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # L-2: 콘텐츠 보안 헤더
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response
