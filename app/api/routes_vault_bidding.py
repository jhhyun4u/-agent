"""
Vault Bidding API — 입찰 분석 (Bidding Analysis and Price Recommendation) Routes
Endpoints for bidding analysis, market statistics, and AI price recommendations.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.models.user_schemas import UserInDB
from app.services.vault_bidding_service import VaultBiddingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault/bidding", tags=["vault-bidding"])


# ============================================
# Request/Response Models
# ============================================

class CreateAnalysisRequest(BaseModel):
    """Create bidding analysis request"""
    proposal_id: str = Field(..., description="Proposal UUID")
    industry: str = Field(..., description="Industry type")
    budget: int = Field(..., ge=1, description="Estimated budget amount")
    g2b_entry_id: Optional[str] = None


class SimilarProjectResponse(BaseModel):
    """Similar project for comparison"""
    project_id: str
    title: str
    budget: int
    winning_bid: int
    bid_ratio: Decimal
    bidders_count: int
    completion_date: str


class AnalysisResultResponse(BaseModel):
    """Bidding analysis result"""
    avg_bid_ratio: Decimal
    avg_bid_amount: int
    recommended_bid: int
    confidence_score: Decimal
    reasoning: str
    pricing_strategy: str
    risk_level: str
    comparable_projects: int
    market_competitiveness: str
    recommendation: str


class BiddingAnalysisResponse(BaseModel):
    """Bidding analysis record"""
    id: str
    proposal_id: str
    industry: str
    budget: int
    budget_range: str
    similar_projects: list[Dict[str, Any]]
    analysis_result: AnalysisResultResponse
    g2b_entry_id: Optional[str]
    g2b_data: Optional[Dict[str, Any]]
    analyzed_at: str
    created_at: str
    updated_at: str


class IndustryStatisticsResponse(BaseModel):
    """Industry statistics"""
    industry: str
    total_projects: int
    avg_budget: Optional[int]
    avg_bid_ratio: Optional[Decimal]
    avg_recommended_bid: Optional[int]
    avg_confidence: Optional[Decimal]
    high_risk_count: Optional[int]
    medium_risk_count: Optional[int]
    low_risk_count: Optional[int]


class BudgetRangeStatisticsResponse(BaseModel):
    """Budget range statistics"""
    budget_range: str
    total_projects: int
    avg_budget: Optional[int]
    avg_bid_ratio: Optional[Decimal]
    avg_recommended_bid: Optional[int]
    avg_confidence: Optional[Decimal]
    ratio_to_budget: Optional[Decimal]


class ProjectComparisonResponse(BaseModel):
    """Project comparison with similar projects"""
    analysis_id: str
    proposal_id: str
    industry: str
    current_budget: int
    recommended_bid: int
    historical_avg_ratio: Decimal
    similar_projects_count: int
    data_quality: str
    confidence_score: Decimal


class UpdateG2BDataRequest(BaseModel):
    """Update analysis with G2B data"""
    g2b_entry_id: str
    g2b_data: Dict[str, Any] = Field(..., description="G2B data including bidders and winning bid")


# ============================================
# Endpoints
# ============================================

@router.post("/analyze", response_model=BiddingAnalysisResponse)
async def create_bidding_analysis(
    request: CreateAnalysisRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Create bidding analysis for a proposal.

    Analyzes historical similar projects and recommends bidding strategy.
    Returns:
    - Recommended bid amount
    - Confidence score (0-1)
    - Pricing strategy (aggressive, moderate, conservative)
    - Risk level (low, medium, high)
    - Market competitiveness assessment

    Args:
        request: Proposal and budget information

    Returns:
        Bidding analysis with AI recommendation
    """
    try:
        analysis = await VaultBiddingService.create_bidding_analysis(
            proposal_id=UUID(request.proposal_id),
            industry=request.industry,
            budget=request.budget,
            analyzed_by=UUID(current_user.id),
            g2b_entry_id=request.g2b_entry_id
        )

        return BiddingAnalysisResponse(**analysis)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create analysis")


@router.get("/{analysis_id}", response_model=BiddingAnalysisResponse)
async def get_bidding_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retrieve detailed bidding analysis.

    Returns complete analysis with similar projects and AI recommendation.

    Args:
        analysis_id: Analysis UUID

    Returns:
        Detailed bidding analysis record
    """
    try:
        analysis = await VaultBiddingService.get_analysis(UUID(analysis_id))
        return BiddingAnalysisResponse(**analysis)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get analysis")


@router.get("/industry/{industry}/statistics", response_model=IndustryStatisticsResponse)
async def get_industry_statistics(
    industry: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get aggregated bidding statistics for an industry.

    Shows:
    - Number of past projects
    - Average bid ratio
    - Average recommended bid
    - Risk distribution (high/medium/low)
    - Confidence levels

    Useful for understanding market patterns for a specific industry.

    Args:
        industry: Industry type (건설, IT, 방위사업, 용역, 기타)

    Returns:
        Industry-wide statistics
    """
    try:
        stats = await VaultBiddingService.get_industry_statistics(industry)
        return IndustryStatisticsResponse(**stats) if stats.get("total_projects", 0) > 0 else stats

    except Exception as e:
        logger.error(f"Failed to get industry statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get industry statistics")


@router.get("/budget-range/{budget_range}/statistics", response_model=BudgetRangeStatisticsResponse)
async def get_budget_range_statistics(
    budget_range: str = Query(..., regex="^(<100M|100M-500M|500M-1B|1B\\+)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get bidding statistics for a budget range.

    Helps understand pricing patterns for different project sizes.

    Args:
        budget_range: Budget category (<100M, 100M-500M, 500M-1B, 1B+)

    Returns:
        Budget range statistics
    """
    try:
        stats = await VaultBiddingService.get_budget_range_statistics(budget_range)
        return BudgetRangeStatisticsResponse(**stats) if stats.get("total_projects", 0) > 0 else stats

    except Exception as e:
        logger.error(f"Failed to get budget statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get budget statistics")


@router.get("/{analysis_id}/comparison", response_model=ProjectComparisonResponse)
async def get_project_comparison(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get detailed comparison of current project with similar historical projects.

    Shows:
    - How current project compares to similar past projects
    - Data quality and confidence level
    - Historical bid patterns

    Args:
        analysis_id: Analysis UUID

    Returns:
        Comparison with similar projects
    """
    try:
        comparison = await VaultBiddingService.get_project_comparison(UUID(analysis_id))
        return ProjectComparisonResponse(**comparison)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get comparison: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get comparison")


@router.get("/opportunities/high-risk", response_model=list[Dict[str, Any]])
async def get_high_risk_opportunities(
    limit: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get high-risk bidding opportunities that require special attention.

    These are bids with:
    - High risk level
    - Medium+ confidence (not speculative)
    - Intense market competition
    - Uncertain market conditions

    Useful for identifying proposals that need more careful analysis
    before committing to a bid.

    Args:
        limit: Number of opportunities to return

    Returns:
        List of high-risk opportunities
    """
    try:
        opportunities = await VaultBiddingService.get_high_risk_opportunities(limit=limit)
        return opportunities

    except Exception as e:
        logger.error(f"Failed to get high-risk opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get opportunities")


@router.patch("/{analysis_id}/g2b-data", response_model=BiddingAnalysisResponse)
async def update_g2b_data(
    analysis_id: str,
    request: UpdateG2BDataRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update analysis with G2B (나라장터) data.

    Enriches the analysis with actual G2B bidding data including:
    - List of actual bidders
    - Winning bid amount
    - Number of competing bidders
    - Tender status and timeline

    This helps calibrate AI recommendations with real market data.

    Args:
        analysis_id: Analysis to update
        request: G2B data to incorporate

    Returns:
        Updated analysis record
    """
    try:
        analysis = await VaultBiddingService.update_g2b_data(
            UUID(analysis_id),
            request.g2b_entry_id,
            request.g2b_data
        )

        return BiddingAnalysisResponse(**analysis)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update G2B data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update G2B data")


@router.delete("/{analysis_id}")
async def delete_bidding_analysis(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Soft-delete a bidding analysis record.

    Note: Records are soft-deleted to preserve audit trail.

    Args:
        analysis_id: Analysis to delete

    Returns:
        Deletion confirmation
    """
    try:
        result = await VaultBiddingService.delete_analysis(UUID(analysis_id))

        if not result:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return {"status": "deleted", "id": analysis_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")


@router.get("/industries", response_model=list[str])
async def get_industries():
    """
    Get list of supported industries.

    Returns:
        Valid industry values
    """
    return VaultBiddingService.INDUSTRIES
