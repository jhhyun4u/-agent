"""
Master Projects API - Unified interface for historical projects and proposals

통합 마스터 프로젝트 API:
- 과거 프로젝트 (intranet_projects)
- 진행 중 제안 (active_proposal)
- 완료된 제안 (completed_proposal)
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser
from app.utils.supabase_client import get_async_client
from app.services.domains.vault.master_projects_chat_service import MasterProjectsChatService

router = APIRouter(prefix="/api/master-projects", tags=["master-projects"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Schemas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MasterProjectResponse(BaseModel):
    """마스터 프로젝트 응답"""
    id: UUID
    project_name: str
    project_year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    client_name: Optional[str] = None
    summary: Optional[str] = None
    budget_krw: Optional[int] = None
    project_type: str
    proposal_status: Optional[str] = None
    result_status: Optional[str] = None
    execution_status: Optional[str] = None
    keywords: Optional[List[str]] = None
    actual_teams: Optional[list] = None
    actual_participants: Optional[list] = None
    proposal_teams: Optional[list] = None
    proposal_participants: Optional[list] = None
    document_count: int = 0
    archive_count: int = 0
    created_at: str
    updated_at: str


class MasterProjectDetailResponse(MasterProjectResponse):
    """마스터 프로젝트 상세 응답"""
    pass


class ProjectStatsResponse(BaseModel):
    """프로젝트 통계 응답"""
    project_id: str
    project_name: str
    project_type: str
    document_count: int
    archive_count: int
    proposal_status: Optional[str]
    result_status: Optional[str]
    execution_status: Optional[str]


class ChatSearchRequest(BaseModel):
    """Chat 검색 요청"""
    query: str = None  # 사용자 질문
    limit: int = 5  # 검색할 최대 프로젝트 수

    class Config:
        json_schema_extra = {
            "example": {
                "query": "우리가 IoT 프로젝트 한 적 있어?",
                "limit": 5
            }
        }


class ChatSearchResponse(BaseModel):
    """Chat 검색 응답"""
    answer: str  # AI가 생성한 답변
    sources: List[MasterProjectResponse]  # 관련 프로젝트들
    message: str  # 처리 메시지


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/test/all", response_model=List[MasterProjectResponse])
async def test_all_projects(
    limit: int = Query(20, ge=1, le=100),
):
    """
    Test endpoint: Get all master_projects without org filter
    """
    client = await get_async_client()
    response = await client.table("master_projects").select("*").limit(limit).execute()
    projects = response.data or []
    return [MasterProjectResponse(**p) for p in projects]


@router.get("", response_model=List[MasterProjectResponse])
async def search_projects(
    current_user: CurrentUser = Depends(get_current_user),
    # 검색 파라미터
    keyword: Optional[str] = Query(None, description="검색어 (프로젝트명, 발주처, 요약)"),
    year: Optional[int] = Query(None, description="프로젝트 연도"),
    client: Optional[str] = Query(None, description="발주처명"),
    project_type: Optional[str] = Query(None, description="프로젝트 타입"),
    proposal_status: Optional[str] = Query(None, description="제안 상태"),
    result_status: Optional[str] = Query(None, description="수주 결과"),
    # 페이지네이션
    skip: int = Query(0, ge=0, description="건너뛸 건수"),
    limit: int = Query(20, ge=1, le=100, description="조회 건수"),
):
    """
    마스터 프로젝트 검색 (통합 검색)

    - 키워드: 프로젝트명, 발주처, 요약에서 검색
    - 필터: 연도, 발주처, 타입, 상태
    - 정렬: 종료일 역순 (최근순)
    """
    client = await get_async_client()

    # 기본 쿼리
    query = client.table("master_projects").select("*")

    # RLS 적용: 현재 조직만
    query = query.eq("org_id", str(current_user.org_id))

    # 키워드 검색
    if keyword:
        keyword_lower = keyword.lower()
        query = query.or_(f"project_name.ilike.%{keyword_lower}%,client_name.ilike.%{keyword_lower}%")

    # 필터
    if year:
        query = query.eq("project_year", year)
    if client:
        query = query.ilike("client_name", f"%{client}%")
    if project_type:
        query = query.eq("project_type", project_type)
    if proposal_status:
        query = query.eq("proposal_status", proposal_status)
    if result_status:
        query = query.eq("result_status", result_status)

    # 정렬 및 페이지네이션
    query = query.order("end_date", desc=True)
    query = query.range(skip, skip + limit - 1)

    response = await query.execute()
    projects = response.data or []

    return [MasterProjectResponse(**p) for p in projects]


@router.get("/{project_id}", response_model=MasterProjectDetailResponse)
async def get_project_detail(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    마스터 프로젝트 상세 조회

    - 기본 정보: 프로젝트명, 발주처, 예산, 상태
    - 참여자: 수행팀/인원 + 제안팀/참여자
    """
    client = await get_async_client()

    response = await (
        client.table("master_projects")
        .select("*")
        .eq("id", project_id)
        .eq("org_id", str(current_user.org_id))
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")

    return MasterProjectResponse(**response.data)


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    프로젝트 통계 조회
    """
    client = await get_async_client()

    response = await (
        client.table("master_projects")
        .select("id,project_name,project_type,document_count,archive_count,proposal_status,result_status,execution_status")
        .eq("id", project_id)
        .eq("org_id", str(current_user.org_id))
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Project not found")

    project = response.data
    return ProjectStatsResponse(
        project_id=str(project["id"]),
        project_name=project["project_name"],
        project_type=project["project_type"],
        document_count=project.get("document_count", 0),
        archive_count=project.get("archive_count", 0),
        proposal_status=project.get("proposal_status"),
        result_status=project.get("result_status"),
        execution_status=project.get("execution_status"),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Chat 검색 (자연어 기반)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post("/chat/search", response_model=ChatSearchResponse)
async def chat_search_projects(
    request: ChatSearchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    자연어 기반 과거 프로젝트 Chat 검색

    RAG (Retrieval-Augmented Generation) 패턴:
    1. 사용자 질문을 벡터로 변환
    2. pgvector로 유사 프로젝트 검색
    3. Claude API로 자연어 답변 생성

    예시:
    - "우리가 IoT 프로젝트 한 적 있어?"
    - "서울시와 계약한 비슷한 규모 프로젝트는?"
    - "에너지 관리 시스템 관련 과제 찾아줘"
    - "2023년에 진행했던 공공사업은?"
    """
    if not request.query:
        raise HTTPException(status_code=400, detail="query는 필수입니다")

    service = MasterProjectsChatService()
    result = await service.search_and_answer(
        query=request.query,
        org_id=current_user.org_id,
        limit=request.limit
    )

    return ChatSearchResponse(
        answer=result["answer"],
        sources=[MasterProjectResponse(**p) for p in result.get("sources", [])],
        message=result["message"]
    )

