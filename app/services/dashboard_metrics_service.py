"""
Dashboard KPI 메트릭 서비스 (설계: 3.3)

팀/본부/경영진 대시보드용 KPI 계산 및 조회.
- 개인: 개인의 제안 진행률, 경과일수
- 팀: 수주율, 수주금액, 기술점수
- 본부: 팀별 비교, 경쟁사 분석
- 경영진: 전사 KPI, 분기/월별 추이

설계 문서: docs/02-design/features/dashboard-kpi.design.md (섹션 3, 4)
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from app.utils.supabase_client import get_async_client
from app.exceptions import TenopAPIError

logger = logging.getLogger(__name__)


class DashboardMetricsService:
    """대시보드 메트릭 서비스"""

    def __init__(self, client=None):
        self.client = client

    async def _get_client(self):
        """Supabase 클라이언트 획득 (캐시 또는 신규)"""
        if not hasattr(self, '_initialized_client'):
            self._initialized_client = await get_async_client()
            return self._initialized_client
        if self.client is None:
            self.client = self._initialized_client
        return self.client

    # ========================================
    # 개인 대시보드 (Individual)
    # ========================================

    async def get_individual_metrics(self, user_id: str) -> dict:
        """
        개인 대시보드 메트릭 조회

        Args:
            user_id: 사용자 ID

        Returns:
            {
                "in_progress_proposals": int,
                "completed_this_month": int,
                "recent_won": int,
                "recent_lost": int,
                "total_amount_won": int (원),
                "avg_days_to_complete": float
            }
        """
        try:
            client = await self._get_client()

            # mv_dashboard_individual에서 조회
            res = await client.table("mv_dashboard_individual") \
                .select("*") \
                .eq("owner_id", user_id) \
                .execute()

            proposals = res.data if res.data else []

            # 메트릭 계산
            now = datetime.utcnow()
            this_month = now.replace(day=1)

            in_progress = sum(
                1 for p in proposals
                if p["status"] not in ("won", "lost", "cancelled", "completed")
            )
            completed_this_month = sum(
                1 for p in proposals
                if p["status"] in ("won", "lost", "completed")
                and datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00")).date() >= this_month.date()
            )
            recent_won = sum(
                1 for p in proposals
                if p["result_type"] == "won"
                and datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00")).date() >= this_month.date()
            )
            recent_lost = sum(
                1 for p in proposals
                if p["result_type"] == "lost"
                and datetime.fromisoformat(p["updated_at"].replace("Z", "+00:00")).date() >= this_month.date()
            )

            total_amount_won = sum(
                (p["final_price"] or 0)
                for p in proposals
                if p["result_type"] == "won"
            )

            # 완료된 제안의 평균 소요 일수
            completed_proposals = [p for p in proposals if p["days_elapsed"] is not None and p["status"] in ("won", "lost", "completed")]
            avg_days = sum(p["days_elapsed"] for p in completed_proposals) / len(completed_proposals) if completed_proposals else 0

            return {
                "in_progress_proposals": in_progress,
                "completed_this_month": completed_this_month,
                "recent_won": recent_won,
                "recent_lost": recent_lost,
                "total_amount_won": int(total_amount_won),
                "avg_days_to_complete": round(avg_days, 1),
                "total_proposals_count": len(proposals)
            }

        except Exception as e:
            logger.error(f"Error getting individual metrics for user {user_id}: {e}")
            raise TenopAPIError("GEN_001", "개인 대시보드 메트릭 조회 실패", status_code=500)

    # ========================================
    # 팀 대시보드 (Team)
    # ========================================

    async def get_team_metrics(self, team_id: str) -> dict:
        """
        팀 대시보드 메트릭 조회

        Args:
            team_id: 팀 ID

        Returns:
            {
                "team_id": str,
                "team_name": str,
                "division_name": str,
                "win_rate_ytd": float (%),
                "win_rate_mtd": float (%),
                "total_proposals": int,
                "won_count": int,
                "total_won_amount": int (원),
                "avg_deal_size": int (원),
                "avg_tech_score": float,
                "in_progress_count": int,
                "positioning_breakdown": [
                    {"positioning": str, "win_rate": float, "total": int, "won": int}
                ]
            }
        """
        try:
            client = await self._get_client()

            # 팀 메트릭 조회
            res = await client.table("mv_dashboard_team") \
                .select("*") \
                .eq("team_id", team_id) \
                .order("year", desc=True) \
                .limit(1) \
                .execute()

            if not res.data or len(res.data) == 0:
                raise TenopAPIError("GEN_005", "팀을 찾을 수 없음", status_code=404)

            team_metrics = res.data[0]

            # 포지셔닝별 성공률 (세부 분석)
            pos_res = await client.table("mv_positioning_accuracy") \
                .select("*") \
                .execute()

            positioning_breakdown = [
                {
                    "positioning": p.get("positioning", "Unknown"),
                    "win_rate": float(p.get("win_rate", 0)) if p.get("win_rate") else 0,
                    "total": int(p.get("total", 0)) if p.get("total") else 0,
                    "won": int(p.get("won", 0)) if p.get("won") else 0
                }
                for p in (pos_res.data or [])
            ]

            return {
                "team_id": str(team_metrics["team_id"]),
                "team_name": team_metrics.get("team_name", ""),
                "division_name": team_metrics.get("division_name", ""),
                "win_rate_ytd": float(team_metrics.get("win_rate_ytd", 0)) if team_metrics.get("win_rate_ytd") else 0,
                "win_rate_mtd": float(team_metrics.get("win_rate_mtd", 0)) if team_metrics.get("win_rate_mtd") else 0,
                "total_proposals": int(team_metrics.get("total_proposals", 0)) if team_metrics.get("total_proposals") else 0,
                "won_count": int(team_metrics.get("won_count", 0)) if team_metrics.get("won_count") else 0,
                "total_won_amount": int(team_metrics.get("total_won_amount", 0)) if team_metrics.get("total_won_amount") else 0,
                "avg_deal_size": int(team_metrics.get("avg_deal_size", 0)) if team_metrics.get("avg_deal_size") else 0,
                "avg_tech_score": float(team_metrics.get("avg_tech_score", 0)) if team_metrics.get("avg_tech_score") else 0,
                "in_progress_count": int(team_metrics.get("in_progress_count", 0)) if team_metrics.get("in_progress_count") else 0,
                "positioning_breakdown": positioning_breakdown
            }

        except TenopAPIError:
            raise
        except Exception as e:
            logger.error(f"Error getting team metrics for team {team_id}: {e}")
            raise TenopAPIError("GEN_002", "팀 대시보드 메트릭 조회 실패", status_code=500)

    # ========================================
    # 본부 대시보드 (Department)
    # ========================================

    async def get_department_metrics(self, division_id: str) -> dict:
        """
        본부 대시보드 메트릭 조회 (팀별 비교 포함)

        Args:
            division_id: 부서 ID

        Returns:
            {
                "division_id": str,
                "division_name": str,
                "win_rate": float (%),
                "target_win_rate": float (%),
                "variance": float (%), # 실적 - 목표
                "status": str, # "below_target" | "on_target" | "above_target"
                "total_proposals": int,
                "total_won_amount": int (원),
                "team_comparison": [
                    {
                        "team_id": str,
                        "team_name": str,
                        "win_rate": float,
                        "won_count": int,
                        "total_proposals": int,
                        "total_won_amount": int,
                        "rank": int
                    }
                ]
            }
        """
        try:
            client = await self._get_client()

            # 팀 메트릭 목록 조회 (해당 부서)
            res = await client.table("mv_dashboard_team") \
                .select("*") \
                .eq("division_id", division_id) \
                .execute()

            teams_data = res.data if res.data else []

            if not teams_data:
                raise TenopAPIError("GEN_006", "부서를 찾을 수 없음", status_code=404)

            # 부서명 (첫 팀의 division_name 사용)
            division_name = teams_data[0].get("division_name", "")

            # 부서별 집계 메트릭
            total_proposals = sum(int(t.get("total_proposals", 0)) for t in teams_data if t.get("total_proposals"))
            total_won = sum(int(t.get("won_count", 0)) for t in teams_data if t.get("won_count"))
            total_amount = sum(int(t.get("total_won_amount", 0)) for t in teams_data if t.get("total_won_amount"))

            # 부서 수주율
            division_win_rate = (total_won / total_proposals * 100) if total_proposals > 0 else 0
            target_win_rate = 45.0  # 기본 목표 45%
            variance = division_win_rate - target_win_rate

            # 상태 판정
            if variance >= 0:
                status = "above_target" if variance > 2 else "on_target"
            else:
                status = "below_target"

            # 팀별 비교 (수주율 기준 정렬)
            team_comparison = []
            for idx, t in enumerate(sorted(teams_data, key=lambda x: float(x.get("win_rate_ytd", 0)) or 0, reverse=True)):
                team_comparison.append({
                    "team_id": str(t["team_id"]),
                    "team_name": t.get("team_name", ""),
                    "win_rate": float(t.get("win_rate_ytd", 0)) if t.get("win_rate_ytd") else 0,
                    "won_count": int(t.get("won_count", 0)) if t.get("won_count") else 0,
                    "total_proposals": int(t.get("total_proposals", 0)) if t.get("total_proposals") else 0,
                    "total_won_amount": int(t.get("total_won_amount", 0)) if t.get("total_won_amount") else 0,
                    "rank": idx + 1
                })

            return {
                "division_id": str(division_id),
                "division_name": division_name,
                "win_rate": round(division_win_rate, 1),
                "target_win_rate": target_win_rate,
                "variance": round(variance, 1),
                "status": status,
                "total_proposals": total_proposals,
                "total_won_amount": int(total_amount),
                "team_comparison": team_comparison
            }

        except TenopAPIError:
            raise
        except Exception as e:
            logger.error(f"Error getting department metrics for division {division_id}: {e}")
            raise TenopAPIError("GEN_003", "본부 대시보드 메트릭 조회 실패", status_code=500)

    # ========================================
    # 경영진 대시보드 (Executive)
    # ========================================

    async def get_executive_metrics(self, org_id: str) -> dict:
        """
        경영진 대시보드 메트릭 조회 (전사 KPI)

        Args:
            org_id: 조직 ID

        Returns:
            {
                "org_id": str,
                "org_name": str,
                "period": str, # "YTD"
                "metrics": {
                    "overall_win_rate": float (%),
                    "total_won_amount": int (원),
                    "total_proposal_count": int,
                    "avg_proposal_value": int (원)
                },
                "division_comparison": [
                    {
                        "division_id": str,
                        "division_name": str,
                        "win_rate": float,
                        "target_win_rate": float,
                        "total_proposals": int,
                        "total_won_amount": int,
                        "status": str
                    }
                ]
            }
        """
        try:
            client = await self._get_client()

            # 최신 분기 경영진 메트릭 조회
            res = await client.table("mv_dashboard_executive") \
                .select("*") \
                .eq("org_id", org_id) \
                .order("quarter", desc=True) \
                .limit(1) \
                .execute()

            if not res.data or len(res.data) == 0:
                raise TenopAPIError("GEN_007", "조직을 찾을 수 없음", status_code=404)

            exec_metrics = res.data[0]

            # 본부별 메트릭 (팀 데이터 활용)
            team_res = await client.table("mv_dashboard_team") \
                .select("*") \
                .eq("org_id", org_id) \
                .execute()

            teams_by_division: dict = {}
            for team in (team_res.data or []):
                div_id = team.get("division_id")
                div_name = team.get("division_name", "Unknown")
                if div_id not in teams_by_division:
                    teams_by_division[div_id] = {
                        "division_id": div_id,
                        "division_name": div_name,
                        "teams": []
                    }
                teams_by_division[div_id]["teams"].append(team)

            # 본부별 집계
            division_comparison = []
            for div_id, div_data in teams_by_division.items():
                teams = div_data["teams"]
                total_props = sum(int(t.get("total_proposals", 0)) for t in teams if t.get("total_proposals"))
                total_won = sum(int(t.get("won_count", 0)) for t in teams if t.get("won_count"))
                total_amt = sum(int(t.get("total_won_amount", 0)) for t in teams if t.get("total_won_amount"))

                div_win_rate = (total_won / total_props * 100) if total_props > 0 else 0
                target_wr = 45.0
                variance = div_win_rate - target_wr
                div_status = "above_target" if variance > 2 else ("below_target" if variance < -2 else "on_target")

                division_comparison.append({
                    "division_id": str(div_id),
                    "division_name": div_data["division_name"],
                    "win_rate": round(div_win_rate, 1),
                    "target_win_rate": target_wr,
                    "total_proposals": total_props,
                    "total_won_amount": int(total_amt),
                    "status": div_status
                })

            # 전사 메트릭
            org_total_props = int(exec_metrics.get("total_proposals", 0)) if exec_metrics.get("total_proposals") else 0
            org_total_won = int(exec_metrics.get("won_count", 0)) if exec_metrics.get("won_count") else 0
            org_total_amt = int(exec_metrics.get("total_won_amount", 0)) if exec_metrics.get("total_won_amount") else 0
            org_avg_val = int(exec_metrics.get("avg_proposal_value", 0)) if exec_metrics.get("avg_proposal_value") else 0

            org_win_rate = (org_total_won / org_total_props * 100) if org_total_props > 0 else 0

            return {
                "org_id": str(org_id),
                "org_name": exec_metrics.get("org_name", ""),
                "period": "YTD",
                "metrics": {
                    "overall_win_rate": round(org_win_rate, 1),
                    "total_won_amount": org_total_amt,
                    "total_proposal_count": org_total_props,
                    "avg_proposal_value": org_avg_val
                },
                "division_comparison": division_comparison
            }

        except TenopAPIError:
            raise
        except Exception as e:
            logger.error(f"Error getting executive metrics for org {org_id}: {e}")
            raise TenopAPIError("GEN_004", "경영진 대시보드 메트릭 조회 실패", status_code=500)

    # ========================================
    # 유틸리티
    # ========================================

    async def refresh_materialized_views(self) -> dict:
        """
        Materialized View 수동 갱신 (admin only)

        Returns:
            {"status": "success", "message": str}
        """
        try:
            client = await get_async_client()

            # SQL 함수 호출
            await client.rpc("refresh_dashboard_views").execute()

            logger.info("Dashboard views refreshed successfully")
            return {
                "status": "success",
                "message": "대시보드 뷰가 갱신되었습니다"
            }

        except Exception as e:
            logger.error(f"Error refreshing dashboard views: {e}")
            raise TenopAPIError("GEN_008", "뷰 갱신 실패", status_code=500)

    async def populate_metrics_history(self) -> dict:
        """
        월별 메트릭 이력 자동 기록 (월 1회, 자동 스케줄러 호출)

        Returns:
            {"status": "success", "records_created": int}
        """
        try:
            client = await get_async_client()

            # SQL 함수 호출
            await client.rpc("populate_dashboard_metrics_history").execute()

            logger.info("Dashboard metrics history populated")
            return {
                "status": "success",
                "message": "월별 메트릭 이력이 기록되었습니다"
            }

        except Exception as e:
            logger.error(f"Error populating metrics history: {e}")
            raise TenopAPIError("GEN_009", "이력 기록 실패", status_code=500)
