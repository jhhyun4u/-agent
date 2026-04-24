"""
Vault Bidding Service — 입찰 분석 (Bidding Analysis and Price Recommendation)
Handles bidding data management, price analysis, and recommendations based on historical data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from decimal import Decimal
from statistics import mean, stdev

from pydantic import BaseModel

from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)


class SimilarProject(BaseModel):
    """Similar historical project for comparison"""
    project_id: str
    title: str
    budget: int
    winning_bid: int
    bid_ratio: Decimal
    bidders_count: int
    completion_date: str


class BiddingAnalysisResult(BaseModel):
    """AI bidding analysis result"""
    avg_bid_ratio: Decimal
    avg_bid_amount: int
    recommended_bid: int
    confidence_score: Decimal
    reasoning: str
    pricing_strategy: str  # aggressive, moderate, conservative
    risk_level: str  # low, medium, high
    comparable_projects: int
    market_competitiveness: str  # intense, moderate, weak
    recommendation: str


class VaultBiddingService:
    """Service for managing vault bidding analysis"""

    INDUSTRIES = [
        "건설",
        "IT",
        "방위사업",
        "용역",
        "기타"
    ]

    BUDGET_RANGES = {
        "<100M": (0, 100_000_000),
        "100M-500M": (100_000_000, 500_000_000),
        "500M-1B": (500_000_000, 1_000_000_000),
        "1B+": (1_000_000_000, float('inf'))
    }

    @staticmethod
    def _get_budget_range(budget: int) -> str:
        """Determine budget range category"""
        for range_name, (min_val, max_val) in VaultBiddingService.BUDGET_RANGES.items():
            if min_val <= budget < max_val:
                return range_name
        return "1B+"

    @staticmethod
    async def create_bidding_analysis(
        proposal_id: UUID,
        industry: str,
        budget: int,
        analyzed_by: Optional[UUID] = None,
        g2b_entry_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create bidding analysis for a proposal.

        Args:
            proposal_id: Proposal ID
            industry: Project industry
            budget: Estimated budget (예정가)
            analyzed_by: User ID who initiated analysis
            g2b_entry_id: G2B public entry ID if available

        Returns:
            Created analysis record
        """
        try:
            budget_range = VaultBiddingService._get_budget_range(budget)

            # Fetch similar projects
            similar_projects = await VaultBiddingService._fetch_similar_projects(
                industry=industry,
                budget=budget,
                limit=10
            )

            # Perform AI analysis
            analysis = await VaultBiddingService._analyze_pricing(
                industry=industry,
                budget=budget,
                similar_projects=similar_projects
            )

            # Create analysis record
            analysis_data = {
                "proposal_id": str(proposal_id),
                "industry": industry,
                "budget": budget,
                "budget_range": budget_range,
                "similar_projects": similar_projects,
                "analysis_result": analysis,
                "analyzed_by": str(analyzed_by) if analyzed_by else None,
                "analyzed_at": datetime.now().isoformat(),
                "metadata": {
                    "data_sources": ["similar_projects", "historical"],
                    "analysis_timestamp": datetime.now().isoformat(),
                    "model_version": "v1.0"
                }
            }

            response = supabase.table("vault_bidding_analysis").insert(analysis_data).execute()
            result = response.data[0] if response.data else None

            if not result:
                raise Exception("Failed to create analysis record")

            logger.info(f"Created bidding analysis: {result['id']} for proposal {proposal_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to create bidding analysis: {str(e)}")
            raise

    @staticmethod
    async def _fetch_similar_projects(
        industry: str,
        budget: int,
        limit: int = 10,
        time_window_days: int = 365
    ) -> List[Dict[str, Any]]:
        """
        Fetch similar completed projects within same industry/budget range.

        Args:
            industry: Project industry
            budget: Budget amount
            limit: Number of similar projects to fetch
            time_window_days: Look back this many days for historical data

        Returns:
            List of similar projects with bid information
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=time_window_days)).date()

            # Query proposals in same industry and budget range
            response = supabase.table("proposals")\
                .select("id,title,budget,client_name,updated_at")\
                .eq("industry", industry)\
                .gte("budget", int(budget * 0.7))\
                .lte("budget", int(budget * 1.3))\
                .eq("status", "won")\
                .gte("updated_at", cutoff_date.isoformat())\
                .order("updated_at", desc=True)\
                .limit(limit)\
                .execute()

            similar = []
            for project in (response.data or []):
                try:
                    # Calculate bid ratio (assuming final_bid is stored in metadata)
                    final_bid = project.get("budget", 0)  # Placeholder
                    bid_ratio = Decimal(str(final_bid)) / Decimal(str(project.get("budget", 1)))

                    similar.append({
                        "project_id": project["id"],
                        "title": project.get("title", "Unnamed Project"),
                        "budget": project.get("budget", 0),
                        "winning_bid": final_bid,
                        "bid_ratio": float(bid_ratio),
                        "bidders_count": 1,  # Placeholder - would need to fetch from G2B
                        "completion_date": project.get("updated_at", "")
                    })
                except Exception as e:
                    logger.warning(f"Failed to process similar project: {str(e)}")
                    continue

            logger.info(f"Fetched {len(similar)} similar projects for {industry} budget {budget}")
            return similar

        except Exception as e:
            logger.error(f"Failed to fetch similar projects: {str(e)}")
            return []

    @staticmethod
    async def _analyze_pricing(
        industry: str,
        budget: int,
        similar_projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze pricing based on similar projects and recommend bid.

        Args:
            industry: Project industry
            budget: Estimated budget
            similar_projects: List of comparable projects

        Returns:
            Analysis result with recommendation
        """
        try:
            if not similar_projects:
                # No historical data - conservative recommendation
                return {
                    "avg_bid_ratio": 1.0,
                    "avg_bid_amount": budget,
                    "recommended_bid": int(budget * 0.95),
                    "confidence_score": 0.5,
                    "reasoning": "제출 이력이 없어 보수적으로 예정가 기준으로 입찰가를 추천합니다.",
                    "pricing_strategy": "conservative",
                    "risk_level": "high",
                    "comparable_projects": 0,
                    "market_competitiveness": "unknown",
                    "recommendation": "충분한 입찰 데이터가 없으므로 추가 시장조사가 필요합니다."
                }

            # Calculate statistics from similar projects
            bid_ratios = [p["bid_ratio"] for p in similar_projects]
            bid_amounts = [p["winning_bid"] for p in similar_projects]

            avg_bid_ratio = Decimal(str(mean(bid_ratios)))
            avg_bid_amount = int(mean(bid_amounts))

            # Calculate confidence based on data quality
            num_projects = len(similar_projects)
            confidence_base = min(Decimal(str(num_projects)) / Decimal("10"), Decimal("1.0"))

            # Recommended bid: average ratio * current budget with strategy adjustment
            recommended_bid = int(budget * float(avg_bid_ratio))

            # Determine strategy and risk
            bid_ratio_std = stdev(bid_ratios) if len(bid_ratios) > 1 else 0
            avg_bidders = mean([p.get("bidders_count", 1) for p in similar_projects])

            if avg_bidders > 5:
                market_competitiveness = "intense"
                pricing_strategy = "aggressive"
                risk_level = "high"
                confidence_score = confidence_base * Decimal("0.8")
                recommended_bid = int(recommended_bid * 0.95)  # Be more aggressive
            elif avg_bidders > 3:
                market_competitiveness = "moderate"
                pricing_strategy = "moderate"
                risk_level = "medium"
                confidence_score = confidence_base * Decimal("0.9")
            else:
                market_competitiveness = "weak"
                pricing_strategy = "conservative"
                risk_level = "low"
                confidence_score = confidence_base * Decimal("0.95")
                recommended_bid = int(recommended_bid * 1.05)  # Less pressure to cut price

            # Generate reasoning
            reasoning = VaultBiddingService._generate_reasoning(
                industry=industry,
                budget=budget,
                avg_bid_ratio=avg_bid_ratio,
                num_projects=num_projects,
                market_competitiveness=market_competitiveness,
                bid_ratio_std=bid_ratio_std
            )

            # Generate recommendation
            recommendation = VaultBiddingService._generate_recommendation(
                pricing_strategy=pricing_strategy,
                risk_level=risk_level,
                confidence_score=confidence_score,
                market_competitiveness=market_competitiveness
            )

            return {
                "avg_bid_ratio": float(avg_bid_ratio),
                "avg_bid_amount": avg_bid_amount,
                "recommended_bid": recommended_bid,
                "confidence_score": float(confidence_score),
                "reasoning": reasoning,
                "pricing_strategy": pricing_strategy,
                "risk_level": risk_level,
                "comparable_projects": num_projects,
                "market_competitiveness": market_competitiveness,
                "recommendation": recommendation
            }

        except Exception as e:
            logger.error(f"Failed to analyze pricing: {str(e)}")
            # Return safe default on analysis failure
            return {
                "avg_bid_ratio": 1.0,
                "avg_bid_amount": budget,
                "recommended_bid": int(budget * 0.95),
                "confidence_score": 0.3,
                "reasoning": "분석 중 오류가 발생했습니다. 보수적으로 입찰가를 추천합니다.",
                "pricing_strategy": "conservative",
                "risk_level": "high",
                "comparable_projects": 0,
                "market_competitiveness": "unknown",
                "recommendation": "분석을 다시 시도하거나 수동으로 입찰가를 결정하세요."
            }

    @staticmethod
    def _generate_reasoning(
        industry: str,
        budget: int,
        avg_bid_ratio: Decimal,
        num_projects: int,
        market_competitiveness: str,
        bid_ratio_std: float
    ) -> str:
        """Generate human-readable reasoning for bid recommendation"""
        reasoning_parts = []

        reasoning_parts.append(f"과거 {num_projects}개의 유사 {industry} 프로젝트를 분석했습니다.")

        reasoning_parts.append(f"평균 낙찰가 비율은 {float(avg_bid_ratio):.2%}입니다.")

        if market_competitiveness == "intense":
            reasoning_parts.append("시장 경쟁이 심해서 적극적인 가격 전략을 추천합니다.")
        elif market_competitiveness == "moderate":
            reasoning_parts.append("보통 수준의 시장 경쟁이 예상되므로 적절한 가격 책정을 권장합니다.")
        else:
            reasoning_parts.append("시장 경쟁이 약해서 적절한 마진을 유지할 수 있습니다.")

        if bid_ratio_std > 0.15:
            reasoning_parts.append("과거 낙찰가 변동성이 크므로 주의가 필요합니다.")

        return " ".join(reasoning_parts)

    @staticmethod
    def _generate_recommendation(
        pricing_strategy: str,
        risk_level: str,
        confidence_score: Decimal,
        market_competitiveness: str
    ) -> str:
        """Generate recommendation text"""
        if confidence_score < 0.5:
            return "데이터가 충분하지 않아 추가 시장조사를 권장합니다."

        if risk_level == "high":
            if pricing_strategy == "aggressive":
                return "경쟁이 심한 시장이므로 적극적 가격책정이 필요합니다. 원가 분석을 철저히 하세요."
            else:
                return "높은 위험도가 감지되었습니다. 신중한 검토 후 입찰을 결정하세요."
        elif risk_level == "medium":
            if pricing_strategy == "moderate":
                return "현재 시장 환경에서 균형잡힌 가격 책정을 권장합니다."
            else:
                return "추가적인 리스크 분석을 통해 입찰 여부를 결정하세요."
        else:
            return "유리한 시장 환경입니다. 적절한 마진을 유지하며 입찰을 진행하세요."

    @staticmethod
    async def get_analysis(analysis_id: UUID) -> Dict[str, Any]:
        """Retrieve bidding analysis"""
        try:
            response = supabase.table("vault_bidding_analysis")\
                .select("*")\
                .eq("id", str(analysis_id))\
                .execute()

            result = response.data[0] if response.data else None
            if not result:
                raise ValueError(f"Analysis not found: {analysis_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to get analysis: {str(e)}")
            raise

    @staticmethod
    async def get_industry_statistics(industry: str) -> Dict[str, Any]:
        """
        Get aggregated bidding statistics for an industry.

        Returns:
            Industry-wide statistics including bid ratios, risks, competitiveness
        """
        try:
            response = supabase.table("vault_bidding_by_industry")\
                .select("*")\
                .eq("industry", industry)\
                .execute()

            if not response.data:
                return {
                    "industry": industry,
                    "total_projects": 0,
                    "message": "이 업종에 대한 분석 데이터가 없습니다."
                }

            return response.data[0]

        except Exception as e:
            logger.error(f"Failed to get industry statistics: {str(e)}")
            raise

    @staticmethod
    async def get_budget_range_statistics(budget_range: str) -> Dict[str, Any]:
        """Get aggregated statistics for a budget range"""
        try:
            response = supabase.table("vault_bidding_by_budget_range")\
                .select("*")\
                .eq("budget_range", budget_range)\
                .execute()

            if not response.data:
                return {
                    "budget_range": budget_range,
                    "total_projects": 0,
                    "message": "이 규모의 프로젝트에 대한 분석 데이터가 없습니다."
                }

            return response.data[0]

        except Exception as e:
            logger.error(f"Failed to get budget range statistics: {str(e)}")
            raise

    @staticmethod
    async def get_high_risk_opportunities(limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get high-risk bidding opportunities requiring special attention.

        Returns:
            List of high-risk opportunities
        """
        try:
            response = supabase.table("vault_bidding_high_risk_opportunities")\
                .select("*")\
                .limit(limit)\
                .execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Failed to get high-risk opportunities: {str(e)}")
            raise

    @staticmethod
    async def get_project_comparison(analysis_id: UUID) -> Dict[str, Any]:
        """
        Get detailed comparison of current project with similar historical projects.

        Returns:
            Comparison data with similar projects
        """
        try:
            response = supabase.table("vault_bidding_project_comparison")\
                .select("*")\
                .eq("analysis_id", str(analysis_id))\
                .execute()

            result = response.data[0] if response.data else None
            if not result:
                raise ValueError(f"Comparison not found: {analysis_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to get project comparison: {str(e)}")
            raise

    @staticmethod
    async def update_g2b_data(
        analysis_id: UUID,
        g2b_entry_id: str,
        g2b_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update analysis with G2B data.

        Args:
            analysis_id: Analysis to update
            g2b_entry_id: G2B public entry ID
            g2b_data: G2B data including bidders and winning bid

        Returns:
            Updated analysis record
        """
        try:
            update_data = {
                "g2b_entry_id": g2b_entry_id,
                "g2b_data": g2b_data,
                "updated_at": datetime.now().isoformat()
            }

            response = supabase.table("vault_bidding_analysis")\
                .update(update_data)\
                .eq("id", str(analysis_id))\
                .execute()

            result = response.data[0] if response.data else None
            logger.info(f"Updated G2B data for analysis: {analysis_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to update G2B data: {str(e)}")
            raise

    @staticmethod
    async def delete_analysis(analysis_id: UUID) -> Dict[str, Any]:
        """Soft-delete analysis record"""
        try:
            update_data = {"deleted_at": datetime.now().isoformat()}
            response = supabase.table("vault_bidding_analysis")\
                .update(update_data)\
                .eq("id", str(analysis_id))\
                .execute()

            result = response.data[0] if response.data else None
            logger.info(f"Deleted analysis: {analysis_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to delete analysis: {str(e)}")
            raise
