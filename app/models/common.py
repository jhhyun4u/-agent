"""공통 재사용 응답 모델."""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class StatusResponse(BaseModel):
    """단순 상태 응답. return {"status": "ok"} 대체."""

    status: Literal["ok", "error"] = "ok"
    message: str = ""


class ItemsResponse(BaseModel, Generic[T]):
    """목록 응답 (페이지네이션 없음). return {"items": [...], "total": N} 대체."""

    items: list[T]
    total: int


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션 목록 응답."""

    items: list[T]
    total: int
    page: int = 1
    per_page: int = 20


class DeleteResponse(BaseModel):
    """삭제 확인 응답."""

    status: Literal["ok"] = "ok"
    deleted_id: str
