"""표준 API 응답 래퍼.

모든 엔드포인트는 이 모듈의 함수를 통해 응답을 반환한다.

단건:  return ok(data)
리스트: return ok_list(items, total=count, offset=offset, limit=limit)
작업:  return ok(None, message="삭제되었습니다.")
"""

from datetime import datetime, timezone
from typing import Any


def ok(data: Any = None, *, message: str | None = None) -> dict:
    """단건 성공 응답."""
    meta: dict[str, Any] = {"timestamp": _now()}
    if message:
        meta["message"] = message
    return {"data": data, "meta": meta}


def ok_list(
    items: list | None,
    *,
    total: int,
    offset: int = 0,
    limit: int = 20,
) -> dict:
    """리스트 성공 응답 (페이지네이션 포함)."""
    return {
        "data": items or [],
        "meta": {
            "total": total,
            "offset": offset,
            "limit": limit,
            "timestamp": _now(),
        },
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
