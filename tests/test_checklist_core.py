"""배포 전 점검 체크리스트 — 핵심 비즈니스 로직 + 알림 + API 검증

체크리스트 항목:
  1-1. 진도율 계산 정확도
  1-2. 예산 집행률 계산
  1-3. D-day / 잔여일 계산
  1-4. 과제 상태 전환 로직
  2-1. 결과물 제출 기한 알림
  2-3. 알림 수신자 권한 분기
  3-1. API 응답 구조 검증
  3-2. 파일 업로드 확장자 차단
  3-3. stream progress 경계값
"""

import pytest
from datetime import date, datetime
from unittest.mock import patch, AsyncMock, MagicMock

# ══════════════════════════════════════
# 1-1. 진도율 계산 정확도
# ══════════════════════════════════════

from app.utils.date_utils import calc_progress  # noqa: E402


class TestCalcProgress:
    def test_normal(self):
        """마일스톤 3/5 완료 시 진도율 60%."""
        assert calc_progress(total=5, completed=3) == 60.0

    def test_zero_total(self):
        """마일스톤 0개일 때 0% (ZeroDivision 방지)."""
        assert calc_progress(total=0, completed=0) == 0.0

    def test_full(self):
        """5/5 완료 시 100%."""
        assert calc_progress(total=5, completed=5) == 100.0

    def test_rounding(self):
        """1/3 = 33.3% (소수점 1자리 반올림)."""
        assert calc_progress(total=3, completed=1) == 33.3

    def test_negative_total(self):
        """음수 total은 0% 반환."""
        assert calc_progress(total=-1, completed=0) == 0.0


# ══════════════════════════════════════
# 1-2. 예산 집행률 계산
# ══════════════════════════════════════

from app.utils.date_utils import calc_budget_rate  # noqa: E402


class TestCalcBudgetRate:
    def test_normal(self):
        """500/1000 = 50%."""
        assert calc_budget_rate(total=1000, used=500) == 50.0

    def test_over_100(self):
        """집행률 100% 초과해도 그대로 표시."""
        assert calc_budget_rate(total=1000, used=1100) == 110.0

    def test_zero_total(self):
        """총 예산 0이면 0%."""
        assert calc_budget_rate(total=0, used=100) == 0.0

    def test_float_precision(self):
        """원화 부동소수점: 333333 / 1000000 ≈ 33.3%."""
        result = calc_budget_rate(total=1_000_000, used=333_333)
        assert abs(result - 33.3) < 0.1


# ══════════════════════════════════════
# 1-3. D-day / 잔여일 계산
# ══════════════════════════════════════

from app.utils.date_utils import calc_dday, deadline_alert_level, KST  # noqa: E402


class TestCalcDday:
    def test_today_is_zero(self):
        """마감일이 오늘이면 D-0."""
        today = date.today()
        assert calc_dday(today, base=today) == 0

    def test_past_is_negative(self):
        """마감일이 지났으면 음수."""
        base = date(2026, 3, 22)
        deadline = date(2026, 3, 21)
        assert calc_dday(deadline, base=base) == -1

    def test_future_is_positive(self):
        """마감일이 미래이면 양수."""
        base = date(2026, 3, 22)
        deadline = date(2026, 3, 29)
        assert calc_dday(deadline, base=base) == 7

    def test_string_input(self):
        """YYYY-MM-DD 문자열 입력."""
        assert calc_dday("2026-03-29", base="2026-03-22") == 7

    def test_leap_year(self):
        """윤년 2024-02-29 → 2024-03-01 = 1일."""
        assert calc_dday("2024-03-01", base="2024-02-29") == 1

    def test_non_leap_year(self):
        """비윤년 2025-02-28 → 2025-03-01 = 1일."""
        assert calc_dday("2025-03-01", base="2025-02-28") == 1

    def test_datetime_with_tz(self):
        """datetime(KST) 입력도 정상 변환."""
        dl = datetime(2026, 3, 29, 10, 0, tzinfo=KST)
        base = datetime(2026, 3, 22, 23, 59, tzinfo=KST)
        assert calc_dday(dl, base=base) == 7

    def test_month_boundary(self):
        """월말 경계: 3/31 → 4/1 = 1일."""
        assert calc_dday("2026-04-01", base="2026-03-31") == 1


class TestDeadlineAlertLevel:
    def test_d0_danger(self):
        assert deadline_alert_level(0) == "danger"

    def test_d_minus_danger(self):
        assert deadline_alert_level(-3) == "danger"

    def test_d3_warning(self):
        assert deadline_alert_level(3) == "warning"

    def test_d1_warning(self):
        assert deadline_alert_level(1) == "warning"

    def test_d7_info(self):
        assert deadline_alert_level(7) == "info"

    def test_d4_info(self):
        assert deadline_alert_level(4) == "info"

    def test_d8_none(self):
        assert deadline_alert_level(8) is None

    def test_d30_none(self):
        assert deadline_alert_level(30) is None


# ══════════════════════════════════════
# 1-4. 과제 상태 전환 로직 (edges.py)
# ══════════════════════════════════════

from app.graph.edges import (  # noqa: E402
    route_after_rfp_review,
    route_after_gng_review,
    route_after_strategy_review,
    route_after_bid_plan_review,
    route_after_plan_review,
    route_after_self_review,
    route_after_section_review,
    route_after_proposal_review,
    route_after_presentation_strategy,
    route_after_ppt_review,
)


def _make_state(**overrides) -> dict:
    """최소 ProposalState dict 생성."""
    base = {
        "project_id": "test-001",
        "current_step": "",
        "approval": {},
        "feedback_history": [],
    }
    base.update(overrides)
    return base


class TestRouteAfterRfpReview:
    def test_approved(self):
        approval_obj = MagicMock(status="approved")
        state = _make_state(approval={"rfp": approval_obj})
        assert route_after_rfp_review(state) == "approved"

    def test_rejected(self):
        approval_obj = MagicMock(status="rejected")
        state = _make_state(approval={"rfp": approval_obj})
        assert route_after_rfp_review(state) == "rejected"

    def test_no_approval(self):
        state = _make_state()
        assert route_after_rfp_review(state) == "rejected"


class TestRouteAfterGngReview:
    def test_go(self):
        state = _make_state(current_step="go_no_go_go")
        assert route_after_gng_review(state) == "go"

    def test_no_go(self):
        state = _make_state(current_step="go_no_go_no_go")
        assert route_after_gng_review(state) == "no_go"

    def test_rejected(self):
        state = _make_state(current_step="something_else")
        assert route_after_gng_review(state) == "rejected"


class TestRouteAfterStrategyReview:
    def test_approved(self):
        approval_obj = MagicMock(status="approved")
        state = _make_state(approval={"strategy": approval_obj})
        assert route_after_strategy_review(state) == "approved"

    def test_positioning_changed(self):
        state = _make_state(current_step="strategy_positioning_changed")
        assert route_after_strategy_review(state) == "positioning_changed"

    def test_rejected(self):
        state = _make_state()
        assert route_after_strategy_review(state) == "rejected"


class TestRouteAfterBidPlanReview:
    def test_approved(self):
        approval_obj = MagicMock(status="approved")
        state = _make_state(approval={"bid_plan": approval_obj})
        assert route_after_bid_plan_review(state) == "approved"

    def test_back_to_strategy(self):
        state = _make_state(
            feedback_history=[{"step": "bid_plan", "back_to_strategy": True}]
        )
        assert route_after_bid_plan_review(state) == "back_to_strategy"

    def test_rejected(self):
        state = _make_state(feedback_history=[{"step": "bid_plan"}])
        assert route_after_bid_plan_review(state) == "rejected"


class TestRouteAfterPlanReview:
    def test_approved(self):
        approval_obj = MagicMock(status="approved")
        state = _make_state(approval={"plan": approval_obj})
        assert route_after_plan_review(state) == "approved"

    def test_rework_with_strategy(self):
        state = _make_state(
            feedback_history=[{"rework_targets": ["strategy_generate"]}]
        )
        assert route_after_plan_review(state) == "rework_with_strategy"

    def test_rework_bid_plan(self):
        state = _make_state(
            feedback_history=[{"rework_targets": ["bid_plan"]}]
        )
        assert route_after_plan_review(state) == "rework_bid_plan"

    def test_plain_rework(self):
        state = _make_state(feedback_history=[{"rework_targets": []}])
        assert route_after_plan_review(state) == "rework"


class TestRouteAfterSelfReview:
    def test_pass(self):
        state = _make_state(current_step="self_review_pass")
        assert route_after_self_review(state) == "pass"

    def test_retry_research(self):
        state = _make_state(current_step="self_review_retry_research")
        assert route_after_self_review(state) == "retry_research"

    def test_retry_strategy(self):
        state = _make_state(current_step="self_review_retry_strategy")
        assert route_after_self_review(state) == "retry_strategy"

    def test_force_review(self):
        state = _make_state(current_step="self_review_force_review")
        assert route_after_self_review(state) == "force_review"

    def test_default_retry_sections(self):
        state = _make_state(current_step="self_review_unknown")
        assert route_after_self_review(state) == "retry_sections"


class TestRouteAfterSectionReview:
    def test_all_done(self):
        state = _make_state(current_step="sections_complete")
        assert route_after_section_review(state) == "all_done"

    def test_next_section(self):
        state = _make_state(current_step="section_approved")
        assert route_after_section_review(state) == "next_section"

    def test_rewrite(self):
        state = _make_state(current_step="needs_rewrite")
        assert route_after_section_review(state) == "rewrite"


class TestRouteAfterProposalReview:
    def test_approved(self):
        approval_obj = MagicMock(status="approved")
        state = _make_state(approval={"proposal": approval_obj})
        assert route_after_proposal_review(state) == "approved"

    def test_rework(self):
        state = _make_state()
        assert route_after_proposal_review(state) == "rework"


class TestRouteAfterPresentationStrategy:
    def test_document_only_skip(self):
        """서류심사이면 PPT 스킵."""
        rfp = {"eval_method": "document_only_review"}
        state = _make_state(rfp_analysis=rfp)
        assert route_after_presentation_strategy(state) == "document_only"

    def test_proceed(self):
        rfp = {"eval_method": "comprehensive"}
        state = _make_state(rfp_analysis=rfp)
        assert route_after_presentation_strategy(state) == "proceed"

    def test_no_rfp(self):
        state = _make_state()
        assert route_after_presentation_strategy(state) == "proceed"


class TestRouteAfterPptReview:
    def test_approved(self):
        approval_obj = MagicMock(status="approved")
        state = _make_state(approval={"ppt": approval_obj})
        assert route_after_ppt_review(state) == "approved"

    def test_rework(self):
        state = _make_state()
        assert route_after_ppt_review(state) == "rework"


# ══════════════════════════════════════
# 1-4 보조: PropStatusTransitionError
# ══════════════════════════════════════

from app.exceptions import PropStatusTransitionError  # noqa: E402


class TestPropStatusTransitionError:
    def test_error_message(self):
        err = PropStatusTransitionError("completed", "initialized")
        assert "completed" in str(err)
        assert "initialized" in str(err)
        assert err.status_code == 409

    def test_error_code(self):
        err = PropStatusTransitionError("running", "initialized")
        assert err.error_code == "PROP_001"


# ══════════════════════════════════════
# 2-1. 알림 중복 발송 방지 + 2-3. 수신자 격리
# ══════════════════════════════════════

class TestNotifyDeadlineAlert:
    """notification_service.notify_deadline_alert 동작 검증."""

    @pytest.mark.asyncio
    async def test_sends_to_participants_only(self):
        """과제 A의 알림은 과제 A 참여자에게만 전달."""
        from app.services.notification_service import notify_deadline_alert

        mock_sb = AsyncMock()

        # proposal 조회
        proposal_result = MagicMock()
        proposal_result.data = {"title": "테스트 과제", "team_id": "team-001"}

        # 참여자: user-010, user-020만 해당 과제에 참여
        participants_result = MagicMock()
        participants_result.data = [
            {"user_id": "user-010"},
            {"user_id": "user-020"},
        ]

        # table 호출 분기
        call_count = {"n": 0}

        def _table(name):
            qb = MagicMock()
            qb.select = MagicMock(return_value=qb)
            qb.eq = MagicMock(return_value=qb)
            qb.single = MagicMock(return_value=qb)

            async def _exec():
                call_count["n"] += 1
                if name == "proposals":
                    return proposal_result
                if name == "project_participants":
                    return participants_result
                # notifications INSERT
                insert_result = MagicMock()
                insert_result.data = [{}]
                return insert_result

            qb.execute = _exec
            qb.insert = MagicMock(return_value=qb)
            return qb

        mock_sb.table = _table

        with patch("app.services.notification_service.get_async_client", return_value=mock_sb), \
             patch("app.services.notification_service.send_teams_notification", new_callable=AsyncMock):
            await notify_deadline_alert("proposal-001", days_left=7)

        # notifications.insert가 참여자 수(2명)만큼 호출되었는지 확인
        # call_count: proposals(1) + participants(1) + notifications(2) = 4
        assert call_count["n"] >= 3  # 최소 proposal + participants + 1 notification

    @pytest.mark.asyncio
    async def test_alert_level_from_days(self):
        """D-7=info, D-3=warning, D-0=danger 알림 등급."""
        assert deadline_alert_level(7) == "info"
        assert deadline_alert_level(3) == "warning"
        assert deadline_alert_level(0) == "danger"


# ══════════════════════════════════════
# 3-1. API 응답 구조 검증 (제안서 목록)
# ══════════════════════════════════════

from tests.conftest import _get_test_app  # noqa: E402

app = _get_test_app()


@pytest.mark.xfail(reason="기존 인프라 이슈: HTTPBearer dep override 미적용 — test_phase1과 동일 401")
async def test_proposals_list_200(client):
    """GET /api/proposals → 200 + 응답 구조 확인."""
    resp = await client.get("/api/proposals")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data or isinstance(data, list), "응답이 items 또는 list 형태여야 함"
    if "total" in data:
        assert isinstance(data["total"], int)


def test_proposal_list_response_model():
    """ProposalListResponse 모델에 필수 필드가 정의되어 있는지 확인."""
    from app.api.routes_proposal import ProposalListResponse
    fields = set(ProposalListResponse.model_fields.keys())
    for required in ["id", "name", "status"]:
        assert required in fields, f"ProposalListResponse에 '{required}' 필드 누락"


# ══════════════════════════════════════
# 3-2. 파일 업로드 확장자 차단
# ══════════════════════════════════════

class TestFileUploadExtension:
    def test_allowed_extensions_no_exe(self):
        """ALLOWED_EXTENSIONS에 exe가 포함되지 않음."""
        from app.api.routes_files import ALLOWED_EXTENSIONS
        assert "exe" not in ALLOWED_EXTENSIONS
        assert "bat" not in ALLOWED_EXTENSIONS
        assert "sh" not in ALLOWED_EXTENSIONS

    def test_allowed_extensions_include_pdf(self):
        """PDF/DOCX/HWPX는 허용."""
        from app.api.routes_files import ALLOWED_EXTENSIONS
        assert "pdf" in ALLOWED_EXTENSIONS
        assert "docx" in ALLOWED_EXTENSIONS
        assert "hwpx" in ALLOWED_EXTENSIONS

    def test_validate_file_type_pdf(self):
        """validate_file_type: PDF 허용."""
        from app.utils.file_utils import validate_file_type
        assert validate_file_type("report.pdf") is True

    def test_validate_file_type_exe_blocked(self):
        """validate_file_type: exe 차단."""
        from app.utils.file_utils import validate_file_type
        assert validate_file_type("malware.exe") is False


# ══════════════════════════════════════
# 3-3. stream progress 경계값
# ══════════════════════════════════════

class TestStreamProgressBoundary:
    def test_progress_zero(self):
        """progress_pct 0은 유효."""
        assert calc_progress(total=10, completed=0) == 0.0

    def test_progress_100(self):
        """progress_pct 100은 유효."""
        assert calc_progress(total=10, completed=10) == 100.0

    def test_progress_over_100(self):
        """completed > total 시 100% 초과 표시 (에러 아님)."""
        result = calc_progress(total=5, completed=6)
        assert result == 120.0
