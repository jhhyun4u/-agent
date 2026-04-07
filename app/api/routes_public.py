"""랜딩페이지 공개 통계 API

GET /api/public/stats — 인증 없이 접근 가능한 플랫폼 통계.
실제 DB 데이터를 기반으로 일일 모니터링 수, 스크리닝 정확도,
제안서 작성 시간 단축, 레퍼런스 과제 수를 반환한다.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.response import ok
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public"])


class LandingStats(BaseModel):
    """랜딩페이지 통계 응답"""
    daily_bids_monitored: int          # 일일 모니터링 공고 수
    screening_accuracy_pct: float      # AI 스크리닝 정확도 (%)
    hours_saved: int                   # 제안서 초안 작성 시간 단축
    reference_projects: int            # 학습 레퍼런스 과제 수
    today_new_bids: int                # 오늘 신규 공고
    today_recommended: int             # 오늘 AI 추천 공고
    deadline_urgent: int               # 마감 임박 D-3 이내
    monthly_proposals: int             # 이번달 진행 제안


@router.get("/stats")
async def get_landing_stats():
    """랜딩페이지 실시간 통계 (인증 불필요)"""
    try:
        client = await get_async_client()
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        d3_deadline = now + timedelta(days=3)

        # 1) 일일 모니터링 공고 수: g2b_bids 전체 건수
        bids_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .limit(0)
            .execute()
        )
        daily_bids_monitored = bids_res.count or 0

        # 2) AI 스크리닝 정확도: go_no_go 결과 대비 실제 수주 결과 일치율
        #    go_no_go_score >= 70 AND win_result='won' + go_no_go_score < 70 AND win_result='lost'
        accuracy_res = await (
            client.table("proposals")
            .select("go_no_go_score, win_result")
            .in_("win_result", ["won", "lost"])
            .not_.is_("go_no_go_score", "null")
            .execute()
        )
        accuracy_records = accuracy_res.data or []
        if accuracy_records:
            correct = sum(
                1 for r in accuracy_records
                if (r["go_no_go_score"] >= 70 and r["win_result"] == "won")
                or (r["go_no_go_score"] < 70 and r["win_result"] == "lost")
            )
            screening_accuracy_pct = round(correct / len(accuracy_records) * 100, 1)
        else:
            screening_accuracy_pct = 0.0

        # 3) 제안서 작성 시간 단축: 완료된 제안서의 평균 작업 시간 기반 추정
        #    AI 없이 평균 16시간 → AI 활용 시 실제 소요 시간 차이
        completed_res = await (
            client.table("proposals")
            .select("created_at, updated_at")
            .in_("status", ["submitted", "presented", "won", "lost"])
            .limit(100)
            .order("created_at", desc=True)
            .execute()
        )
        completed = completed_res.data or []
        if completed:
            total_hours = 0.0
            count = 0
            for r in completed:
                try:
                    created = datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                    updated = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
                    diff_hours = (updated - created).total_seconds() / 3600
                    if 0 < diff_hours < 72:  # 합리적 범위
                        total_hours += diff_hours
                        count += 1
                except (ValueError, TypeError):
                    continue
            avg_ai_hours = total_hours / count if count > 0 else 8
            baseline_hours = 16  # 수동 작성 기준
            hours_saved = max(1, round(baseline_hours - avg_ai_hours))
        else:
            hours_saved = 8

        # 4) 레퍼런스 과제 수: content_library 건수
        ref_res = await (
            client.table("content_library")
            .select("id", count="exact")
            .limit(0)
            .execute()
        )
        reference_projects = ref_res.count or 0

        # 5) 오늘 신규 공고
        today_bids_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .gte("fetched_at", today_start.isoformat())
            .limit(0)
            .execute()
        )
        today_new_bids = today_bids_res.count or 0

        # 6) AI 추천 공고 (적합도 70점 이상)
        recommended_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .gte("fetched_at", today_start.isoformat())
            .gte("relevance_score", 70)
            .limit(0)
            .execute()
        )
        today_recommended = recommended_res.count or 0

        # 7) 마감 임박 D-3 이내
        urgent_res = await (
            client.table("g2b_bids")
            .select("id", count="exact")
            .gte("deadline", now.isoformat())
            .lte("deadline", d3_deadline.isoformat())
            .eq("status", "active")
            .limit(0)
            .execute()
        )
        deadline_urgent = urgent_res.count or 0

        # 8) 이번달 진행 제안
        monthly_res = await (
            client.table("proposals")
            .select("id", count="exact")
            .gte("created_at", month_start.isoformat())
            .limit(0)
            .execute()
        )
        monthly_proposals = monthly_res.count or 0

        stats = LandingStats(
            daily_bids_monitored=daily_bids_monitored,
            screening_accuracy_pct=screening_accuracy_pct,
            hours_saved=hours_saved,
            reference_projects=reference_projects,
            today_new_bids=today_new_bids,
            today_recommended=today_recommended,
            deadline_urgent=deadline_urgent,
            monthly_proposals=monthly_proposals,
        )
        return ok(stats.model_dump())

    except Exception as e:
        logger.error(f"랜딩 통계 조회 실패: {e}", exc_info=True)
        # 에러 시 기본값 반환 (랜딩 페이지가 깨지지 않도록)
        return ok(LandingStats(
            daily_bids_monitored=0,
            screening_accuracy_pct=0.0,
            hours_saved=0,
            reference_projects=0,
            today_new_bids=0,
            today_recommended=0,
            deadline_urgent=0,
            monthly_proposals=0,
        ).model_dump())
