"""
Vault Personnel API — 인사 데이터 관리 엔드포인트
Personnel search, expertise management, availability tracking, performance analytics
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_current_user_team
from app.models.user_schemas import UserInDB
from app.services.domains.vault.vault_personnel_service import VaultPersonnelService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault/personnel", tags=["vault-personnel"])


# ============================================
# Request/Response Models
# ============================================

class SkillRequest(BaseModel):
    """Skill/expertise entry"""
    skill: str = Field(..., description="기술/역량명")
    proficiency: str = Field(..., description="숙련도: beginner, intermediate, advanced, expert")
    years: Optional[int] = Field(None, description="경력년수")


class PersonnelResponse(BaseModel):
    """Personnel record"""
    id: str
    name: str
    email: str
    role: str
    department: Optional[str]
    position: Optional[str]
    primary_expertise: Optional[str]
    total_proposals: int
    won_proposals: int
    win_rate: float
    years_in_company: Optional[int]
    current_project_count: int
    max_concurrent_projects: int
    is_active: bool
    employment_status: str
    skills: List[Dict[str, Any]]
    created_at: str


class PersonnelSearchResponse(BaseModel):
    """Simplified personnel for search results"""
    id: str
    name: str
    email: str
    role: str
    department: Optional[str]
    primary_expertise: Optional[str]
    total_proposals: int
    win_rate: float


class PersonnelPerformanceResponse(BaseModel):
    """Personnel performance summary"""
    personnel_id: str
    period_days: int
    total_proposals: int
    won_proposals: int
    lost_proposals: int
    pending_proposals: int
    win_rate: float
    lifetime_stats: Dict[str, Any]


class AvailablePersonnelResponse(BaseModel):
    """Available personnel with utilization"""
    id: str
    name: str
    email: str
    role: str
    primary_expertise: Optional[str]
    win_rate: float
    utilization_percent: float
    capacity_status: str


class DepartmentStatsResponse(BaseModel):
    """Department statistics"""
    department: Optional[str]
    total_count: int
    active_count: int
    avg_win_rate: float
    avg_tenure: float
    key_skills: Optional[str]


class ExpertiseInventoryResponse(BaseModel):
    """Organization expertise inventory"""
    org_id: str
    all_skills: List[Dict[str, Any]]
    expert_count: int
    advanced_count: int


class UtilizationResponse(BaseModel):
    """Personnel utilization status"""
    id: str
    name: str
    email: str
    role: str
    max_concurrent_projects: int
    current_project_count: int
    utilization_percent: float
    capacity_status: str


# ============================================
# Endpoints
# ============================================

@router.get("/{personnel_id}", response_model=PersonnelResponse)
async def get_personnel(
    personnel_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    인력 상세 조회

    Args:
        personnel_id: Personnel UUID

    Returns:
        Complete personnel record
    """
    try:
        personnel = await VaultPersonnelService.get_personnel(UUID(personnel_id))
        return PersonnelResponse(**personnel)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get personnel: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get personnel")


@router.get("/user/{user_id}", response_model=PersonnelResponse)
async def get_personnel_by_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    사용자 ID로 인력 조회

    Args:
        user_id: Supabase auth user ID

    Returns:
        Personnel record for user
    """
    try:
        personnel = await VaultPersonnelService.get_personnel_by_user_id(UUID(user_id))
        return PersonnelResponse(**personnel)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get personnel by user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get personnel")


@router.post("/search", response_model=List[PersonnelSearchResponse])
async def search_personnel(
    query: Optional[str] = Query(None, description="이름/이메일 검색"),
    department: Optional[str] = Query(None, description="부서 필터"),
    role: Optional[str] = Query(None, description="직급 필터"),
    skill: Optional[str] = Query(None, description="보유 기술 필터"),
    is_active: bool = Query(True, description="활성 여부"),
    limit: int = Query(50, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    인력 검색 (다중 필터)

    검색 조건:
    - 이름/이메일 포함 검색
    - 부서별 필터
    - 직급별 필터
    - 특정 기술 보유자 필터
    - 활성/비활성 필터

    Args:
        query: Search by name or email
        department: Filter by department
        role: Filter by role
        skill: Filter by skill
        is_active: Active status filter
        limit: Result limit

    Returns:
        List of matching personnel
    """
    try:
        results = await VaultPersonnelService.search_personnel(
            org_id=UUID(current_user.org_id),
            query=query,
            department=department,
            role=role,
            skill=skill,
            is_active=is_active,
            limit=limit
        )

        return [PersonnelSearchResponse(**r) for r in results]

    except Exception as e:
        logger.error(f"Failed to search personnel: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search personnel")


@router.post("/sync-from-auth", response_model=Dict[str, Any])
async def sync_personnel_from_auth(
    current_user: UserInDB = Depends(get_current_user),
):
    """
    Supabase auth.users에서 인력 데이터 동기화

    새로운 사용자는 자동으로 vault_personnel에 추가됩니다.
    기존 사용자는 last_synced_at이 업데이트됩니다.

    권한: admin, hr_manager

    Returns:
        Sync result with counts
    """
    try:
        if current_user.role not in ["admin", "hr_manager"]:
            raise HTTPException(status_code=403, detail="HR access required")

        result = await VaultPersonnelService.sync_from_supabase_auth(
            UUID(current_user.org_id)
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync personnel: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to sync personnel")


@router.get("/{personnel_id}/performance", response_model=PersonnelPerformanceResponse)
async def get_personnel_performance(
    personnel_id: str,
    days: int = Query(90, ge=1, le=365, description="조회 기간 (일)"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    개인 성과 요약

    최근 기간 내 제안서 참여 현황, 낙찰/낙찰실패 건수, 낙찰률 조회

    Args:
        personnel_id: Personnel UUID
        days: Period in days (default 90)

    Returns:
        Performance summary
    """
    try:
        performance = await VaultPersonnelService.get_personnel_performance(
            UUID(personnel_id),
            days=days
        )

        return PersonnelPerformanceResponse(**performance)

    except Exception as e:
        logger.error(f"Failed to get personnel performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get performance")


@router.get("/available", response_model=List[AvailablePersonnelResponse])
async def get_available_personnel(
    skill: Optional[str] = Query(None, description="필요한 기술"),
    limit: int = Query(10, ge=1, le=50),
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    가용한 인력 조회

    조건:
    - 활성 상태 (is_active = true)
    - 근무중 (employment_status = 'employed')
    - 역량 활용 가능 (<100% utilization)
    - 특정 기술 보유 (optional)

    Args:
        skill: Required skill (optional)
        limit: Result limit

    Returns:
        List of available personnel with utilization info
    """
    try:
        available = await VaultPersonnelService.get_available_personnel(
            org_id=UUID(current_user.org_id),
            required_skill=skill,
            limit=limit
        )

        return [AvailablePersonnelResponse(**p) for p in available]

    except Exception as e:
        logger.error(f"Failed to get available personnel: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get available personnel")


@router.get("/top/contributors", response_model=List[PersonnelSearchResponse])
async def get_top_contributors(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    상위 기여자 조회 (낙찰률 & 제안 수 기준)

    낙찰률이 높고 제안서 참여 경험이 많은 인력을 우선 조회

    Args:
        limit: Result limit

    Returns:
        Top contributors
    """
    try:
        contributors = await VaultPersonnelService.get_top_contributors(
            org_id=UUID(current_user.org_id),
            limit=limit
        )

        return [PersonnelSearchResponse(**c) for c in contributors]

    except Exception as e:
        logger.error(f"Failed to get top contributors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get contributors")


@router.get("/department/stats", response_model=List[DepartmentStatsResponse])
async def get_department_statistics(
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    부서별 인력 통계

    각 부서의:
    - 인력 수 (전체, 활성)
    - 평균 낙찰률
    - 평균 근속년수
    - 주력 기술

    Returns:
        Department-level statistics
    """
    try:
        stats = await VaultPersonnelService.get_department_stats(
            org_id=UUID(current_user.org_id)
        )

        return [DepartmentStatsResponse(**s) for s in stats]

    except Exception as e:
        logger.error(f"Failed to get department stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.get("/expertise/inventory", response_model=ExpertiseInventoryResponse)
async def get_expertise_inventory(
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    조직의 역량 인벤토리 조회

    전체 기술 분포, 전문가 수, 등급별 인력 수

    Returns:
        Expertise inventory
    """
    try:
        inventory = await VaultPersonnelService.get_expertise_inventory(
            org_id=UUID(current_user.org_id)
        )

        return ExpertiseInventoryResponse(**inventory)

    except Exception as e:
        logger.error(f"Failed to get expertise inventory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get inventory")


@router.get("/utilization/report", response_model=List[UtilizationResponse])
async def get_utilization_report(
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    조직 전체 인력 활용률 보고서

    각 인력의:
    - 최대 동시 프로젝트 수
    - 현재 프로젝트 수
    - 활용률 (%)
    - 역량 상태 (free, available, high-utilization, at-capacity)

    Returns:
        Utilization report sorted by utilization %
    """
    try:
        report = await VaultPersonnelService.get_utilization_report(
            org_id=UUID(current_user.org_id)
        )

        return [UtilizationResponse(**r) for r in report]

    except Exception as e:
        logger.error(f"Failed to get utilization report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get report")


@router.patch("/{personnel_id}/skills", response_model=PersonnelResponse)
async def update_skills(
    personnel_id: str,
    skills: List[SkillRequest],
    current_user: UserInDB = Depends(get_current_user)
):
    """
    인력의 기술/역량 업데이트

    Args:
        personnel_id: Personnel UUID
        skills: List of skills with proficiency levels

    Returns:
        Updated personnel record
    """
    try:
        skills_data = [s.dict() for s in skills]

        updated = await VaultPersonnelService.update_skills(
            UUID(personnel_id),
            skills_data
        )

        return PersonnelResponse(**updated)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update skills")


@router.patch("/{personnel_id}/expertise", response_model=PersonnelResponse)
async def set_primary_expertise(
    personnel_id: str,
    primary_expertise: str = Query(..., description="주력 기술 영역"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    주력 기술 영역 설정

    Args:
        personnel_id: Personnel UUID
        primary_expertise: Primary expertise area

    Returns:
        Updated personnel record
    """
    try:
        updated = await VaultPersonnelService.set_primary_expertise(
            UUID(personnel_id),
            primary_expertise
        )

        return PersonnelResponse(**updated)

    except Exception as e:
        logger.error(f"Failed to set expertise: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to set expertise")


@router.patch("/{personnel_id}/availability", response_model=PersonnelResponse)
async def update_availability(
    personnel_id: str,
    available_from: Optional[str] = Query(None, description="가용 시작일 (ISO 8601)"),
    available_until: Optional[str] = Query(None, description="가용 종료일 (ISO 8601)"),
    max_concurrent_projects: Optional[int] = Query(None, ge=1),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    인력의 가용성 업데이트

    Args:
        personnel_id: Personnel UUID
        available_from: Availability start date
        available_until: Availability end date
        max_concurrent_projects: Max concurrent projects

    Returns:
        Updated personnel record
    """
    try:
        from_dt = datetime.fromisoformat(available_from) if available_from else None
        until_dt = datetime.fromisoformat(available_until) if available_until else None

        updated = await VaultPersonnelService.update_availability(
            UUID(personnel_id),
            available_from=from_dt,
            available_until=until_dt,
            max_concurrent_projects=max_concurrent_projects
        )

        return PersonnelResponse(**updated)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update availability: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update availability")


@router.patch("/{personnel_id}/hr-info", response_model=PersonnelResponse)
async def update_hr_info(
    personnel_id: str,
    department: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    position: Optional[str] = Query(None),
    manager_id: Optional[str] = Query(None),
    hr_notes: Optional[str] = Query(None),
    employment_status: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    HR 정보 업데이트 (부서, 직급, 관리자 등)

    권한: admin, hr_manager

    Args:
        personnel_id: Personnel UUID
        department: Department name
        role: Job title
        position: Position
        manager_id: Manager's personnel ID
        hr_notes: HR notes
        employment_status: Employment status (employed, leave, retired, terminated)

    Returns:
        Updated personnel record
    """
    try:
        if current_user.role not in ["admin", "hr_manager"]:
            raise HTTPException(status_code=403, detail="HR access required")

        mgr_id = UUID(manager_id) if manager_id else None

        updated = await VaultPersonnelService.update_hr_info(
            UUID(personnel_id),
            department=department,
            role=role,
            position=position,
            manager_id=mgr_id,
            hr_notes=hr_notes,
            employment_status=employment_status
        )

        return PersonnelResponse(**updated)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update HR info: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update HR info")


@router.delete("/{personnel_id}")
async def delete_personnel(
    personnel_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    인력 기록 soft delete

    권한: admin, hr_manager

    Args:
        personnel_id: Personnel UUID

    Returns:
        Deletion confirmation
    """
    try:
        if current_user.role not in ["admin", "hr_manager"]:
            raise HTTPException(status_code=403, detail="HR access required")

        result = await VaultPersonnelService.delete_personnel(UUID(personnel_id))

        return {"status": "deleted", **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete personnel: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete personnel")
