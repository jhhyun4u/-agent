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

    # ========================================
    # Timeline & Details (설계: 5.2, 5.3)
    # ========================================

    async def fetch_timeline(
        self,
        dashboard_type: str,
        constraint_id: str,
        months: int = 12,
        metric: str = "win_rate"
    ) -> dict:
        """
        월별 이력 조회 (최근 N개월 + 추이)

        Args:
            dashboard_type: "team" | "department" | "executive"
            constraint_id: 팀ID / 본부ID / 조직ID
            months: 조회 개월 수 (1-36, 기본값 12)
            metric: "win_rate" | "total_amount" | "proposal_count"

        Returns:
            {
                "dashboard_type": str,
                "metric": str,
                "data": [{month, period_label, win_rate, proposal_count, won_count, total_amount}],
                "summary": {trend, avg_win_rate, best_month, best_month_value}
            }
        """
        try:
            client = await self._get_client()

            # 기준 날짜 계산 (최근 N개월)
            now = datetime.utcnow()
            start_date = now - timedelta(days=30 * months)

            # dashboard_metrics_history 조회
            query = client.table("dashboard_metrics_history").select("*")

            if dashboard_type == "team":
                query = query.eq("team_id", constraint_id)
            elif dashboard_type == "department":
                query = query.eq("division_id", constraint_id)
            elif dashboard_type == "executive":
                query = query.eq("org_id", constraint_id)
            else:
                raise TenopAPIError("VAL_001", "Invalid dashboard_type", status_code=400)

            query = query.gte("period", start_date.date().isoformat())
            query = query.order("period", desc=False)

            res = await query.execute()
            history_data = res.data if res.data else []

            if not history_data:
                # 이력이 없으면 현재 메트릭으로 응답
                if dashboard_type == "team":
                    current = await self.get_team_metrics(constraint_id)
                    current_wr = current.get("win_rate_ytd", 0)
                elif dashboard_type == "department":
                    current = await self.get_department_metrics(constraint_id)
                    current_wr = current.get("win_rate", 0)
                else:  # executive
                    current = await self.get_executive_metrics(constraint_id)
                    current_wr = current.get("metrics", {}).get("overall_win_rate", 0)

                return {
                    "dashboard_type": dashboard_type,
                    "metric": metric,
                    "data": [],
                    "summary": {
                        "trend": "flat",
                        "avg_win_rate": current_wr,
                        "best_month": None,
                        "best_month_value": current_wr
                    }
                }

            # 응답 데이터 구성
            timeline_data = []
            win_rates = []

            for record in history_data:
                month = record.get("period", "").replace("-01", "")  # YYYY-MM-01 → YYYY-MM
                win_rate = float(record.get("win_rate", 0)) if record.get("win_rate") else 0
                proposal_count = int(record.get("total_proposals", 0)) if record.get("total_proposals") else 0
                won_count = int(record.get("won_count", 0)) if record.get("won_count") else 0
                total_amount = int(record.get("total_won_amount", 0)) if record.get("total_won_amount") else 0

                timeline_data.append({
                    "month": month,
                    "period_label": datetime.fromisoformat(record.get("period", "")).strftime("%b %Y"),
                    "win_rate": round(win_rate, 1),
                    "proposal_count": proposal_count,
                    "won_count": won_count,
                    "total_amount": total_amount
                })

                win_rates.append(win_rate)

            # 추이 분석
            if len(win_rates) > 1:
                recent_avg = sum(win_rates[-3:]) / 3 if len(win_rates) >= 3 else sum(win_rates[-1:]) / 1
                older_avg = sum(win_rates[:-3]) / (len(win_rates) - 3) if len(win_rates) > 3 else sum(win_rates[:-1]) / 1
                if recent_avg > older_avg:
                    trend = "up"
                elif recent_avg < older_avg:
                    trend = "down"
                else:
                    trend = "flat"
            else:
                trend = "flat"

            best_month_idx = win_rates.index(max(win_rates)) if win_rates else 0
            best_month = timeline_data[best_month_idx]["month"] if timeline_data else None
            best_month_value = max(win_rates) if win_rates else 0

            return {
                "dashboard_type": dashboard_type,
                "metric": metric,
                "data": timeline_data,
                "summary": {
                    "trend": trend,
                    "avg_win_rate": round(sum(win_rates) / len(win_rates), 1) if win_rates else 0,
                    "best_month": best_month,
                    "best_month_value": round(best_month_value, 1)
                }
            }

        except TenopAPIError:
            raise
        except Exception as e:
            logger.error(f"Error fetching timeline for {dashboard_type}/{constraint_id}: {e}")
            raise TenopAPIError("GEN_010", "타임라인 조회 실패", status_code=500)

    async def fetch_details(
        self,
        dashboard_type: str,
        constraint_id: str,
        filter_type: str = "team",
        filter_value: Optional[str] = None,
        sort_by: str = "win_rate",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        상세 데이터 드릴다운 (필터/정렬)

        Args:
            dashboard_type: "team" | "department" | "executive"
            constraint_id: 팀ID / 본부ID / 조직ID
            filter_type: "team" | "region" | "client" | "positioning"
            filter_value: 필터 값 (선택)
            sort_by: "win_rate" | "amount" | "date"
            sort_order: "asc" | "desc"
            limit: 페이지 크기
            offset: 페이지 오프셋

        Returns:
            {
                "dashboard_type": str,
                "filter_type": str,
                "total_count": int,
                "data": [{team_id, team_name, team_lead, win_rate, total_proposals, won_count, total_won_amount, recent_projects}]
            }
        """
        try:
            client = await self._get_client()

            # 팀별 상세 데이터 조회 (filter_type이 "team"인 경우만 지원)
            if filter_type != "team":
                # 다른 필터 타입은 향후 구현
                return {
                    "dashboard_type": dashboard_type,
                    "filter_type": filter_type,
                    "total_count": 0,
                    "data": []
                }

            # 팀 메트릭 조회
            if dashboard_type == "department":
                res = await client.table("mv_dashboard_team") \
                    .select("*") \
                    .eq("division_id", constraint_id) \
                    .execute()
            elif dashboard_type == "executive":
                res = await client.table("mv_dashboard_team") \
                    .select("*") \
                    .eq("org_id", constraint_id) \
                    .execute()
            else:
                raise TenopAPIError("VAL_002", "Invalid dashboard_type", status_code=400)

            teams_data = res.data if res.data else []

            # 정렬
            sort_key_map = {
                "win_rate": "win_rate_ytd",
                "amount": "total_won_amount",
                "date": "updated_at"
            }
            sort_key = sort_key_map.get(sort_by, "win_rate_ytd")
            reverse_sort = sort_order == "desc"

            sorted_teams = sorted(
                teams_data,
                key=lambda x: float(x.get(sort_key, 0)) if x.get(sort_key) else 0,
                reverse=reverse_sort
            )

            # 페이징
            paginated_teams = sorted_teams[offset:offset+limit]

            # 응답 데이터 구성
            details_data = []
            for team in paginated_teams:
                team_id = str(team.get("team_id", ""))

                # 최근 프로젝트 조회 (최대 5개)
                projects_res = await client.table("proposals") \
                    .select("id, title, status, result_amount, result_date") \
                    .eq("team_id", team_id) \
                    .in_("status", ["won", "lost"]) \
                    .order("result_date", desc=True) \
                    .limit(5) \
                    .execute()

                recent_projects = [
                    {
                        "proposal_id": str(p.get("id", "")),
                        "title": p.get("title", ""),
                        "result": "won" if p.get("status") == "won" else "lost",
                        "amount": int(p.get("result_amount", 0)) if p.get("result_amount") else 0,
                        "result_date": p.get("result_date", "")
                    }
                    for p in (projects_res.data or [])
                ]

                details_data.append({
                    "team_id": team_id,
                    "team_name": team.get("team_name", ""),
                    "team_lead": team.get("team_lead", ""),
                    "team_size": int(team.get("team_size", 0)) if team.get("team_size") else 0,
                    "win_rate": float(team.get("win_rate_ytd", 0)) if team.get("win_rate_ytd") else 0,
                    "total_proposals": int(team.get("total_proposals", 0)) if team.get("total_proposals") else 0,
                    "won_count": int(team.get("won_count", 0)) if team.get("won_count") else 0,
                    "total_won_amount": int(team.get("total_won_amount", 0)) if team.get("total_won_amount") else 0,
                    "recent_projects": recent_projects
                })

            return {
                "dashboard_type": dashboard_type,
                "filter_type": filter_type,
                "total_count": len(sorted_teams),
                "data": details_data
            }

        except TenopAPIError:
            raise
        except Exception as e:
            logger.error(f"Error fetching details for {dashboard_type}/{constraint_id}: {e}")
            raise TenopAPIError("GEN_011", "상세 데이터 조회 실패", status_code=500)
