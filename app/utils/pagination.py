"""
페이지네이션 유틸리티

Supabase .range() 기반 오프셋 페이지네이션 공통 로직.
routes_bids, routes_team, routes_resources, routes_users 등에서 공유.
"""

from fastapi import Query


class PageParams:
    """FastAPI Depends()로 주입 가능한 페이지네이션 파라미터.

    사용법:
        async def list_items(pg: PageParams = Depends()):
            query = query.range(pg.offset, pg.end)
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="페이지 번호"),
        page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def end(self) -> int:
        """Supabase .range(offset, end) 의 end 값."""
        return self.offset + self.page_size - 1

    def apply(self, query):
        """Supabase 쿼리에 .range() 적용. 쿼리 빌더 반환."""
        return query.range(self.offset, self.end)
