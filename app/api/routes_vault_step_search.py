"""
Vault Step Search API — Step별 최적화 검색 및 데이터 라우팅
각 PDCA 단계에서 필요한 Vault 데이터를 빠르게 조회하는 엔드포인트
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_current_user_team
from app.models.user_schemas import UserInDB
from app.services.domains.vault.vault_step_search import VaultStepSearch

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault/step-search", tags=["vault-step-search"])


# ============================================
# Request/Response Models
# ============================================

class StepSearchRequest(BaseModel):
    """Step 검색 요청"""
    proposal_id: str = Field(..., description="Proposal UUID")
    industry: str = Field(..., description="산업 분류")
    budget: int = Field(..., ge=1, description="예정가")
    client_name: Optional[str] = Field(None, description="발주처명")
    step: int = Field(..., ge=1, le=5, description="PDCA 단계 (1-5)")


class Step1Response(BaseModel):
    """Step 1 Go/No-Go 응답"""
    proposal_id: str
    step: int
    client_info: Dict[str, Any]
    similar_projects: List[Dict[str, Any]]
    team_capability: Dict[str, Any]
    risk_assessment: Dict[str, Any]


class Step2Response(BaseModel):
    """Step 2 Strategy 응답"""
    proposal_id: str
    step: int
    bidding_recommendation: Dict[str, Any]
    competitive_analysis: Dict[str, Any]
    client_preferences: Dict[str, Any]
    team_lead_expertise: Dict[str, Any]


class Step3Response(BaseModel):
    """Step 3 Planning 응답"""
    proposal_id: str
    step: int
    available_personnel: List[Dict[str, Any]]
    recommended_team: List[Dict[str, Any]]
    capacity_analysis: Dict[str, Any]
    schedule_recommendations: Dict[str, Any]


class Step4Response(BaseModel):
    """Step 4 Proposal Writing 응답"""
    proposal_id: str
    step: int
    credibility_evidence: List[Dict[str, Any]]
    pricing_guidance: Dict[str, Any]
    client_customization: Dict[str, Any]
    content_references: Dict[str, Any]


class Step5Response(BaseModel):
    """Step 5 Presentation 응답"""
    proposal_id: str
    step: int
    client_strategy: Dict[str, Any]
    team_composition: Dict[str, Any]
    presentation_structure: Dict[str, Any]
    audience_analysis: Dict[str, Any]


# ============================================
# Endpoints
# ============================================

@router.post("/step1/go-no-go", response_model=Step1Response)
async def search_step1_go_no_go(
    proposal_id: str = Query(..., description="Proposal UUID"),
    industry: str = Query(..., description="산업 분류"),
    budget: int = Query(..., ge=1, description="예정가"),
    client_name: Optional[str] = Query(None, description="발주처명"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Step 1: Go/No-Go 의사결정 데이터 조회

    조회 항목:
    - 고객 정보 및 이력 (낙찰률, 관계)
    - 유사 프로젝트 (같은 산업, 예산 범위)
    - 팀 역량 평가
    - 위험도 평가 (경쟁 강도)

    Args:
        proposal_id: Proposal UUID
        industry: 산업 분류 (건설, IT, 방위사업 등)
        budget: 예정가
        client_name: 발주처명 (optional)

    Returns:
        Step 1 데이터: 고객정보, 유사사례, 팀역량, 위험도
    """
    try:
        result = await VaultStepSearch.search_for_step1_go_no_go(
            UUID(proposal_id),
            industry,
            budget,
            client_name
        )

        return Step1Response(**result)

    except Exception as e:
        logger.error(f"Failed to search Step 1: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search Step 1 data")


@router.post("/step2/strategy", response_model=Step2Response)
async def search_step2_strategy(
    proposal_id: str = Query(..., description="Proposal UUID"),
    industry: str = Query(..., description="산업 분류"),
    budget: int = Query(..., ge=1, description="예정가"),
    client_name: Optional[str] = Query(None, description="발주처명"),
    team_lead_id: Optional[str] = Query(None, description="팀 리더 Personnel ID"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Step 2: 제안전략 수립 데이터 조회

    조회 항목:
    - 경쟁 분석 (산업별 경쟁 강도)
    - 입찰 가격 추천 (낙찰률 기반)
    - 고객 선호도 및 과거 교훈
    - 팀 리더 전문성

    Args:
        proposal_id: Proposal UUID
        industry: 산업 분류
        budget: 예정가
        client_name: 발주처명 (optional)
        team_lead_id: 팀 리더 Personnel ID (optional)

    Returns:
        Step 2 데이터: 입찰추천, 경쟁분석, 고객선호도, 리더역량
    """
    try:
        team_lead_uuid = UUID(team_lead_id) if team_lead_id else None

        result = await VaultStepSearch.search_for_step2_strategy(
            UUID(proposal_id),
            industry,
            budget,
            client_name,
            team_lead_uuid
        )

        return Step2Response(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to search Step 2: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search Step 2 data")


@router.post("/step3/planning", response_model=Step3Response)
async def search_step3_planning(
    proposal_id: str = Query(..., description="Proposal UUID"),
    team_size: int = Query(3, ge=1, le=10, description="필요한 팀 규모"),
    required_expertise: Optional[List[str]] = Query(None, description="필요한 기술 목록"),
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    Step 3: 제안 계획 & 팀 구성 데이터 조회

    조회 항목:
    - 가용 인력 (역량 기반, 활용률 기반)
    - 최적 팀 구성 추천 (낙찰률 순)
    - 조직 역량 분석
    - 일정 계획 권장사항

    Args:
        proposal_id: Proposal UUID
        team_size: 필요한 팀 규모 (default 3)
        required_expertise: 필요한 기술 목록 (optional)

    Returns:
        Step 3 데이터: 가용인력, 추천팀, 용량분석, 일정권장
    """
    try:
        result = await VaultStepSearch.search_for_step3_planning(
            UUID(proposal_id),
            team_size,
            required_expertise,
            UUID(current_user.org_id)
        )

        return Step3Response(**result)

    except Exception as e:
        logger.error(f"Failed to search Step 3: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search Step 3 data")


@router.post("/step4/proposal-writing", response_model=Step4Response)
async def search_step4_proposal_writing(
    proposal_id: str = Query(..., description="Proposal UUID"),
    industry: Optional[str] = Query(None, description="산업 분류"),
    budget: Optional[int] = Query(None, ge=1, description="예정가"),
    client_name: Optional[str] = Query(None, description="발주처명"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Step 4: 제안서 작성 지원 데이터 조회

    조회 항목:
    - 신뢰성 있는 사례 (인증서, 성공 사례)
    - 가격 결정 가이드 (입찰 분석)
    - 고객 맞춤 정보
    - 섹션별 콘텐츠 참고

    Args:
        proposal_id: Proposal UUID
        industry: 산업 분류 (optional)
        budget: 예정가 (optional)
        client_name: 발주처명 (optional)

    Returns:
        Step 4 데이터: 사례, 가격가이드, 고객맞춤, 콘텐츠참고
    """
    try:
        result = await VaultStepSearch.search_for_step4_proposal_writing(
            UUID(proposal_id),
            client_name,
            industry,
            budget
        )

        return Step4Response(**result)

    except Exception as e:
        logger.error(f"Failed to search Step 4: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search Step 4 data")


@router.post("/step5/presentation", response_model=Step5Response)
async def search_step5_presentation(
    proposal_id: str = Query(..., description="Proposal UUID"),
    client_name: Optional[str] = Query(None, description="발주처명"),
    team_lead_id: Optional[str] = Query(None, description="팀 리더 Personnel ID"),
    presentation_minutes: int = Query(20, ge=5, le=60, description="발표 시간 (분)"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Step 5: 발표 전략 수립 데이터 조회

    조회 항목:
    - 고객 맞춤화 전략
    - 팀 구성 및 역할 배정
    - 발표 구성 (시간 배분, 슬라이드)
    - 청중 분석 및 설득 전략

    Args:
        proposal_id: Proposal UUID
        client_name: 발주처명 (optional)
        team_lead_id: 팀 리더 Personnel ID (optional)
        presentation_minutes: 발표 시간 (default 20분)

    Returns:
        Step 5 데이터: 고객전략, 팀구성, 발표구조, 청중분석
    """
    try:
        team_lead_uuid = UUID(team_lead_id) if team_lead_id else None

        result = await VaultStepSearch.search_for_step5_presentation(
            UUID(proposal_id),
            client_name,
            team_lead_uuid,
            presentation_minutes
        )

        return Step5Response(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to search Step 5: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search Step 5 data")


@router.post("/integrated", response_model=Dict[str, Any])
async def search_integrated_vault_data(
    proposal_id: str = Query(..., description="Proposal UUID"),
    industry: str = Query(..., description="산업 분류"),
    budget: int = Query(..., ge=1, description="예정가"),
    current_step: int = Query(..., ge=1, le=5, description="현재 단계 (1-5)"),
    client_name: Optional[str] = Query(None, description="발주처명"),
    team_lead_id: Optional[str] = Query(None, description="팀 리더 Personnel ID"),
    current_user: UserInDB = Depends(get_current_user),
    current_team = Depends(get_current_user_team)
):
    """
    통합 Vault 데이터 조회 (현재 Step별)

    현재 단계에 맞는 모든 필요한 Vault 데이터를 한 번에 조회합니다.

    Args:
        proposal_id: Proposal UUID
        industry: 산업 분류
        budget: 예정가
        current_step: 현재 PDCA 단계 (1-5)
        client_name: 발주처명 (optional)
        team_lead_id: 팀 리더 Personnel ID (optional)

    Returns:
        Step-specific integrated vault data
    """
    try:
        team_lead_uuid = UUID(team_lead_id) if team_lead_id else None

        result = await VaultStepSearch.search_integrated_vault_data(
            UUID(proposal_id),
            industry,
            budget,
            client_name,
            UUID(current_user.org_id),
            team_lead_uuid,
            current_step
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed integrated search: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search integrated data")
