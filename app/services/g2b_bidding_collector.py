"""
G2B 낙찰가 데이터 수집 및 분석 자동화
나라장터 API에서 유사 과제의 낙찰 정보를 수집하고 분석
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.services.g2b_service import G2BAPIClient
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


class G2BBiddingCollector:
    """나라장터 입찰/낙찰 데이터 수집"""

    def __init__(self):
        self.g2b_client = G2BAPIClient()
        self.batch_size = 10  # 유사 과제 수집 개수

    @staticmethod
    def _industry_to_g2b_category(industry: str) -> str:
        """산업 분류를 나라장터 카테고리로 매핑"""
        mapping = {
            "IT": "정보통신",
            "AI": "정보통신",
            "클라우드": "정보통신",
            "건설": "건설/시설",
            "인프라": "건설/시설",
            "방위사업": "방위사업",
            "바이오": "보건/의료",
            "의료": "보건/의료",
        }
        return mapping.get(industry, industry)

    async def collect_similar_projects(
        self,
        industry: str,
        budget: int,
        agency: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        유사 과제 수집

        Args:
            industry: 산업 분류 (IT, 건설 등)
            budget: 예정가
            agency: 발주기관 (optional)
            limit: 수집할 과제 수

        Returns:
            유사 과제 목록 with 낙찰정보
            [
                {
                    "project_id": "...",
                    "project_name": "...",
                    "budget": 150000000,
                    "winner": "ABC업체",
                    "winner_bid": 148500000,
                    "win_percentage": 99.0,
                    "announcement_date": "2026-01-15",
                    "category": "정보통신",
                    "agency": "과기부"
                }
            ]
        """
        try:
            category = self._industry_to_g2b_category(industry)

            # G2B API를 통해 유사 공고 검색
            search_params = {
                "category": category,
                "budget_min": int(budget * 0.7),  # 예정가 70%~130%
                "budget_max": int(budget * 1.3),
                "limit": limit,
            }

            if agency:
                search_params["agency"] = agency

            # 공고 목록 조회
            bid_notices = await self.g2b_client.search_bid_notices(
                **search_params
            )

            if not bid_notices:
                logger.info(f"No similar projects found for {industry}")
                return []

            # 각 공고의 낙찰 결과 조회
            projects_with_results = []
            for notice in bid_notices[:limit]:
                try:
                    # 낙찰 정보 조회
                    bid_result = await self.g2b_client.get_bid_result(
                        notice.get("notice_id") or notice.get("id")
                    )

                    if bid_result:
                        # 낙찰률 계산
                        budget = notice.get("budget", 0)
                        winner_bid = bid_result.get("bid_amount", 0)
                        win_percentage = (winner_bid / budget * 100) if budget > 0 else 0

                        project = {
                            "project_id": notice.get("notice_id") or notice.get("id"),
                            "project_name": notice.get("title") or notice.get("name"),
                            "budget": budget,
                            "winner": bid_result.get("contractor_name"),
                            "winner_bid": winner_bid,
                            "win_percentage": round(win_percentage, 2),
                            "announcement_date": notice.get(
                                "announcement_date"
                            ) or notice.get("date"),
                            "category": category,
                            "agency": notice.get("agency"),
                            "collected_at": datetime.utcnow().isoformat(),
                        }
                        projects_with_results.append(project)
                except Exception as e:
                    logger.warning(f"Failed to get bid result for {notice}: {e}")
                    # Continue with next project
                    continue

            logger.info(
                f"Collected {len(projects_with_results)} projects with bid results"
            )
            return projects_with_results

        except Exception as e:
            logger.error(f"Error collecting similar projects: {e}")
            return []

    async def save_to_vault(
        self,
        proposal_id: UUID,
        industry: str,
        budget: int,
        projects: List[Dict[str, Any]],
        org_id: Optional[UUID] = None,
    ) -> bool:
        """
        수집한 데이터를 vault_bidding_analysis에 저장

        Args:
            proposal_id: 제안 ID
            industry: 산업 분류
            budget: 예정가
            projects: 수집한 유사 과제
            org_id: 조직 ID

        Returns:
            저장 성공 여부
        """
        try:
            client = await get_async_client()

            # 분석 데이터 계산
            if not projects:
                logger.warning("No projects to save")
                return False

            win_percentages = [p.get("win_percentage", 0) for p in projects]
            winner_bids = [p.get("winner_bid", 0) for p in projects]

            avg_win_percentage = sum(win_percentages) / len(win_percentages)
            avg_winner_bid = sum(winner_bids) / len(winner_bids)

            # 권장 제안가: 평균 낙찰률 - 0.5%
            recommended_win_percentage = avg_win_percentage - 0.5
            recommended_bid = int(budget * (recommended_win_percentage / 100))

            # Confidence 점수 (표본 수, 데이터 신선도)
            # 신선도: 최근 3개월 내 데이터
            recent_projects = [
                p for p in projects
                if datetime.fromisoformat(p.get("announcement_date", "1900-01-01"))
                   > datetime.utcnow().replace(month=(datetime.utcnow().month - 3) % 12)
            ]
            freshness_score = len(recent_projects) / len(projects) if projects else 0
            sample_score = min(len(projects) / 10, 1.0)  # Max score at 10+ samples
            confidence = (freshness_score * 0.4 + sample_score * 0.6)

            analysis_data = {
                "industry": industry,
                "budget": budget,
                "sample_size": len(projects),
                "avg_win_percentage": round(avg_win_percentage, 2),
                "recommended_win_percentage": round(recommended_win_percentage, 2),
                "recommended_bid": recommended_bid,
                "avg_winner_bid": round(avg_winner_bid, 2),
                "confidence": round(confidence, 3),
                "data_source": "G2B",
                "collected_at": datetime.utcnow().isoformat(),
                "projects": projects,  # 상세 데이터
            }

            # vault_bidding_analysis에 저장
            result = await client.table("vault_bidding_analysis").insert({
                "proposal_id": str(proposal_id),
                "industry": industry,
                "budget": budget,
                "org_id": str(org_id) if org_id else None,
                "analysis_data": analysis_data,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()

            logger.info(f"Saved bidding analysis for proposal {proposal_id}")
            return bool(result.data)

        except Exception as e:
            logger.error(f"Error saving to vault: {e}")
            return False

    async def analyze_and_save(
        self,
        proposal_id: UUID,
        industry: str,
        budget: int,
        agency: Optional[str] = None,
        org_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        통합 분석: 수집 → 분석 → 저장

        Args:
            proposal_id: 제안 ID
            industry: 산업 분류
            budget: 예정가
            agency: 발주기관 (optional)
            org_id: 조직 ID

        Returns:
            분석 결과
            {
                "success": True,
                "sample_size": 10,
                "avg_win_percentage": 87.5,
                "recommended_bid": 185250000,
                "confidence": 0.85
            }
        """
        try:
            # Step 1: 데이터 수집
            projects = await self.collect_similar_projects(
                industry=industry,
                budget=budget,
                agency=agency,
                limit=self.batch_size,
            )

            if not projects:
                return {
                    "success": False,
                    "error": "No similar projects found",
                    "sample_size": 0,
                }

            # Step 2: 분석 데이터 저장
            saved = await self.save_to_vault(
                proposal_id=proposal_id,
                industry=industry,
                budget=budget,
                projects=projects,
                org_id=org_id,
            )

            if not saved:
                return {
                    "success": False,
                    "error": "Failed to save analysis data",
                    "sample_size": len(projects),
                }

            # Step 3: 결과 반환
            win_percentages = [p.get("win_percentage", 0) for p in projects]
            avg_win_percentage = sum(win_percentages) / len(win_percentages)
            recommended_win_percentage = avg_win_percentage - 0.5
            recommended_bid = int(budget * (recommended_win_percentage / 100))

            sample_score = min(len(projects) / 10, 1.0)
            confidence = sample_score  # Simplified for now

            return {
                "success": True,
                "sample_size": len(projects),
                "avg_win_percentage": round(avg_win_percentage, 2),
                "recommended_bid": recommended_bid,
                "recommended_win_percentage": round(recommended_win_percentage, 2),
                "confidence": round(confidence, 3),
            }

        except Exception as e:
            logger.error(f"Error in analyze_and_save: {e}")
            return {
                "success": False,
                "error": str(e),
            }


class G2BBiddingAnalyzer:
    """G2B 데이터 기반 입찰 분석"""

    @staticmethod
    async def get_bidding_analysis(
        proposal_id: UUID,
        org_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        제안서의 낙찰가 분석 결과 조회

        Args:
            proposal_id: 제안 ID
            org_id: 조직 ID

        Returns:
            분석 결과
        """
        try:
            client = await get_async_client()

            query = client.table("vault_bidding_analysis").select("*").eq(
                "proposal_id", str(proposal_id)
            )

            if org_id:
                query = query.eq("org_id", str(org_id))

            # 가장 최근의 분석 데이터 조회
            result = await query.order("created_at", desc=True).limit(1).execute()

            if not result.data:
                return None

            return result.data[0]

        except Exception as e:
            logger.error(f"Error getting bidding analysis: {e}")
            return None

    @staticmethod
    async def get_recommendation(
        proposal_id: UUID,
        proposed_bid: Optional[int] = None,
        org_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        제안가에 대한 낙찰 가능성 예측

        Args:
            proposal_id: 제안 ID
            proposed_bid: 제안하려는 입찰가 (optional)
            org_id: 조직 ID

        Returns:
            추천사항
            {
                "recommended_bid": 185250000,
                "win_probability": 0.92,
                "price_position": "competitive",
                "recommendation": "제안가 185M은 경쟁력 있는 가격입니다"
            }
        """
        try:
            analysis = await G2BBiddingAnalyzer.get_bidding_analysis(
                proposal_id=proposal_id,
                org_id=org_id,
            )

            if not analysis:
                return {
                    "success": False,
                    "error": "No bidding analysis available",
                }

            analysis_data = analysis.get("analysis_data", {})
            recommended_bid = analysis_data.get("recommended_bid", 0)
            budget = analysis_data.get("budget", 0)
            confidence = analysis_data.get("confidence", 0.5)

            # proposed_bid가 제공된 경우
            if proposed_bid:
                # 낙찰률 계산
                win_percentage = (proposed_bid / budget * 100) if budget > 0 else 0

                # 평균 낙찰률과 비교
                avg_win_percentage = analysis_data.get("avg_win_percentage", 0)
                win_probability = max(0, min(1, 1 - (win_percentage - avg_win_percentage) / 10))

                # 가격 포지셔닝
                if win_percentage < avg_win_percentage - 2:
                    price_position = "very_competitive"
                    recommendation = f"제안가 {proposed_bid:,}은(는) 매우 경쟁력 있는 가격입니다 (낙찰률 {win_percentage:.1f}%)"
                elif win_percentage < avg_win_percentage:
                    price_position = "competitive"
                    recommendation = f"제안가 {proposed_bid:,}은(는) 경쟁력 있는 가격입니다 (낙찰률 {win_percentage:.1f}%)"
                elif win_percentage < avg_win_percentage + 2:
                    price_position = "neutral"
                    recommendation = f"제안가 {proposed_bid:,}은(는) 평균 가격입니다 (낙찰률 {win_percentage:.1f}%)"
                else:
                    price_position = "premium"
                    recommendation = f"제안가 {proposed_bid:,}은(는) 높은 가격입니다 (낙찰률 {win_percentage:.1f}%)"

                return {
                    "success": True,
                    "proposed_bid": proposed_bid,
                    "recommended_bid": recommended_bid,
                    "win_probability": round(win_probability, 2),
                    "price_position": price_position,
                    "recommendation": recommendation,
                    "confidence": confidence,
                }
            else:
                # 추천 제안가 반환
                return {
                    "success": True,
                    "recommended_bid": recommended_bid,
                    "avg_win_percentage": analysis_data.get("avg_win_percentage", 0),
                    "sample_size": analysis_data.get("sample_size", 0),
                    "confidence": confidence,
                }

        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    async def get_historical_analysis(
        industry: str,
        budget_range: tuple = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        산업별/예산별 최근 분석 데이터 조회

        Args:
            industry: 산업 분류
            budget_range: (min, max) 튜플
            limit: 조회할 분석 건수

        Returns:
            분석 데이터 목록
        """
        try:
            client = await get_async_client()

            query = client.table("vault_bidding_analysis").select(
                "analysis_data, created_at"
            ).eq("industry", industry)

            if budget_range:
                min_budget, max_budget = budget_range
                query = query.gte("budget", min_budget).lte("budget", max_budget)

            result = await (
                query.order("created_at", desc=True)
                .limit(limit)
                .execute()
            )

            return [r.get("analysis_data") for r in result.data] if result.data else []

        except Exception as e:
            logger.error(f"Error getting historical analysis: {e}")
            return []
