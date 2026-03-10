"""
BidRecommender 유닛 테스트 — 파싱/포맷 메서드 (Claude API 호출 없음)

_parse_qualification_response, _parse_scoring_response,
_format_profile, _format_bids_for_qualification, _format_bids_for_scoring
"""

import json
import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.bid_schemas import BidAnnouncement, TeamBidProfile
from app.services.bid_recommender import BidRecommender, _score_to_grade


# ─────────────────────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────────────────────

def make_recommender() -> BidRecommender:
    with patch("app.services.bid_recommender.AsyncAnthropic"):
        return BidRecommender()


def make_bid(bid_no="001", bid_title="AI 시스템 구축", agency="행정안전부", content="자격요건 명세") -> BidAnnouncement:
    deadline = datetime.now(timezone.utc) + timedelta(days=10)
    return BidAnnouncement(
        bid_no=bid_no,
        bid_title=bid_title,
        agency=agency,
        bid_type="용역",
        budget_amount=300_000_000,
        announce_date=date.today(),
        deadline_date=deadline,
        days_remaining=10,
        content_text=content,
        qualification_available=True,
    )


SAMPLE_PROFILE = TeamBidProfile(
    team_id="team-001",
    expertise_areas=["AI/ML", "공공데이터"],
    tech_keywords=["Python", "LLM"],
    past_projects="행정안전부 AI 챗봇 구축 (2023, 3억)",
    company_size="중기업",
    certifications=["GS인증", "SW기업확인서"],
    business_registration_type="중소기업",
    employee_count=80,
    founded_year=2015,
)


# ─────────────────────────────────────────────────────────────
# _parse_qualification_response
# ─────────────────────────────────────────────────────────────

class TestParseQualificationResponse:

    def setup_method(self):
        self.rec = make_recommender()

    def test_정상_파싱(self):
        bids = [make_bid("001"), make_bid("002")]
        response = json.dumps([
            {"bid_no": "001", "qualification_status": "pass"},
            {"bid_no": "002", "qualification_status": "fail", "disqualification_reason": "건설업 면허 필요"},
        ])
        results = self.rec._parse_qualification_response(response, bids)

        assert len(results) == 2
        r1 = next(r for r in results if r.bid_no == "001")
        r2 = next(r for r in results if r.bid_no == "002")
        assert r1.qualification_status == "pass"
        assert r2.qualification_status == "fail"
        assert r2.disqualification_reason == "건설업 면허 필요"

    def test_JSON_앞뒤_텍스트_무시(self):
        """응답에 JSON 외 텍스트가 있어도 추출 성공"""
        bids = [make_bid("001")]
        response = "네, 분석 결과입니다:\n" + json.dumps([
            {"bid_no": "001", "qualification_status": "pass"}
        ]) + "\n이상입니다."
        results = self.rec._parse_qualification_response(response, bids)
        assert results[0].qualification_status == "pass"

    def test_누락된_bid_no_ambiguous_처리(self):
        """응답에서 특정 bid_no 누락 시 ambiguous 자동 추가"""
        bids = [make_bid("001"), make_bid("002")]
        response = json.dumps([
            {"bid_no": "001", "qualification_status": "pass"},
            # "002"가 누락됨
        ])
        results = self.rec._parse_qualification_response(response, bids)
        assert len(results) == 2
        r2 = next(r for r in results if r.bid_no == "002")
        assert r2.qualification_status == "ambiguous"

    def test_잘못된_status_ambiguous_대체(self):
        """pass/fail/ambiguous 외 값은 ambiguous로 처리"""
        bids = [make_bid("001")]
        response = json.dumps([
            {"bid_no": "001", "qualification_status": "unknown_value"}
        ])
        results = self.rec._parse_qualification_response(response, bids)
        assert results[0].qualification_status == "ambiguous"

    def test_완전히_깨진_JSON_전체_ambiguous(self):
        """JSON 파싱 자체 실패 시 전체 ambiguous"""
        bids = [make_bid("001"), make_bid("002")]
        response = "이건 JSON이 아닙니다."
        results = self.rec._parse_qualification_response(response, bids)
        assert len(results) == 2
        for r in results:
            assert r.qualification_status == "ambiguous"

    def test_알_수_없는_bid_no_무시(self):
        """요청에 없는 bid_no는 결과에서 제외"""
        bids = [make_bid("001")]
        response = json.dumps([
            {"bid_no": "001", "qualification_status": "pass"},
            {"bid_no": "999", "qualification_status": "pass"},  # 요청에 없음
        ])
        results = self.rec._parse_qualification_response(response, bids)
        assert all(r.bid_no == "001" for r in results)


# ─────────────────────────────────────────────────────────────
# _parse_scoring_response
# ─────────────────────────────────────────────────────────────

class TestParseScoringResponse:

    def setup_method(self):
        self.rec = make_recommender()

    def test_정상_파싱(self):
        bids = [make_bid("001")]
        response = json.dumps([{
            "bid_no": "001",
            "match_score": 85,
            "match_grade": "A",
            "recommendation_summary": "AI 전문성과 부합",
            "recommendation_reasons": [
                {"category": "전문성", "reason": "LLM 경험 보유", "strength": "high"}
            ],
            "risk_factors": [{"risk": "경쟁사 다수", "level": "medium"}],
            "win_probability_hint": "중상",
            "recommended_action": "적극 검토",
        }])
        results = self.rec._parse_scoring_response(response, bids)
        assert len(results) == 1
        assert results[0].match_score == 85
        assert results[0].match_grade == "A"
        assert len(results[0].recommendation_reasons) == 1
        assert results[0].recommendation_reasons[0].strength == "high"

    def test_score_100_초과_클램핑(self):
        bids = [make_bid("001")]
        response = json.dumps([{
            "bid_no": "001",
            "match_score": 150,
            "match_grade": "S",
            "recommendation_summary": "요약",
            "recommendation_reasons": [
                {"category": "기타", "reason": "부합", "strength": "high"}
            ],
            "win_probability_hint": "상",
            "recommended_action": "검토",
        }])
        results = self.rec._parse_scoring_response(response, bids)
        assert results[0].match_score == 100

    def test_score_음수_클램핑(self):
        bids = [make_bid("001")]
        response = json.dumps([{
            "bid_no": "001",
            "match_score": -10,
            "match_grade": "D",
            "recommendation_summary": "요약",
            "recommendation_reasons": [
                {"category": "기타", "reason": "부합", "strength": "low"}
            ],
            "win_probability_hint": "하",
            "recommended_action": "보류",
        }])
        results = self.rec._parse_scoring_response(response, bids)
        assert results[0].match_score == 0

    def test_recommendation_reasons_없으면_기본값_삽입(self):
        bids = [make_bid("001")]
        response = json.dumps([{
            "bid_no": "001",
            "match_score": 70,
            "match_grade": "B",
            "recommendation_summary": "요약",
            "recommendation_reasons": [],  # 빈 배열
            "win_probability_hint": "중",
            "recommended_action": "검토",
        }])
        results = self.rec._parse_scoring_response(response, bids)
        assert len(results[0].recommendation_reasons) >= 1

    def test_깨진_JSON_빈_목록_반환(self):
        bids = [make_bid("001")]
        results = self.rec._parse_scoring_response("이건 JSON이 아님", bids)
        assert results == []

    def test_match_grade_없으면_score로_계산(self):
        bids = [make_bid("001")]
        response = json.dumps([{
            "bid_no": "001",
            "match_score": 92,
            "recommendation_summary": "요약",
            "recommendation_reasons": [
                {"category": "기술", "reason": "부합", "strength": "high"}
            ],
            "win_probability_hint": "상",
            "recommended_action": "추천",
        }])
        results = self.rec._parse_scoring_response(response, bids)
        assert results[0].match_grade == "S"  # score 92 → S


# ─────────────────────────────────────────────────────────────
# _format_profile
# ─────────────────────────────────────────────────────────────

class TestFormatProfile:

    def setup_method(self):
        self.rec = make_recommender()

    def test_모든_필드_포함(self):
        text = self.rec._format_profile(SAMPLE_PROFILE)
        assert "AI/ML" in text
        assert "Python" in text
        assert "행정안전부 AI 챗봇" in text
        assert "GS인증" in text
        assert "80명" in text
        assert "2015년" in text

    def test_빈_리스트_필드_미지정_표시(self):
        profile = TeamBidProfile(
            team_id="t1",
            expertise_areas=[],
            tech_keywords=[],
            certifications=[],
        )
        text = self.rec._format_profile(profile)
        assert "미지정" in text or "없음" in text


# ─────────────────────────────────────────────────────────────
# _format_bids_for_qualification / _format_bids_for_scoring
# ─────────────────────────────────────────────────────────────

class TestFormatBids:

    def setup_method(self):
        self.rec = make_recommender()

    def test_qualification_포맷_필드_포함(self):
        bids = [make_bid("001", content="자격요건 상세 내용")]
        text = self.rec._format_bids_for_qualification(bids)
        assert "001" in text
        assert "AI 시스템 구축" in text
        assert "행정안전부" in text
        assert "자격요건 상세 내용" in text

    def test_scoring_포맷_예산_마감일_포함(self):
        bids = [make_bid("001")]
        text = self.rec._format_bids_for_scoring(bids)
        assert "001" in text
        assert "300,000,000원" in text
        assert "D-" in text

    def test_content_500자_자르기(self):
        long_content = "자" * 600
        bids = [make_bid("001", content=long_content)]
        text = self.rec._format_bids_for_qualification(bids)
        # 500자 제한 확인 (정확히 500 또는 그 이하)
        assert long_content not in text  # 600자 전체는 없어야 함

    def test_content_None_내용없음_표시(self):
        bids = [make_bid("001", content=None)]
        text = self.rec._format_bids_for_qualification(bids)
        assert "내용 없음" in text

    def test_예산_None_미기재_표시(self):
        bid = BidAnnouncement(
            bid_no="001", bid_title="예산없는 공고", agency="기관",
            budget_amount=None, days_remaining=5,
        )
        text = self.rec._format_bids_for_scoring([bid])
        assert "미기재" in text


# ─────────────────────────────────────────────────────────────
# analyze_bids / check_qualifications / score_bids — Mock 기반
# ─────────────────────────────────────────────────────────────

def _make_claude_response(text: str):
    """Claude API 응답 형태 Mock 생성"""
    content = MagicMock()
    content.text = text
    response = MagicMock()
    response.content = [content]
    return response


@pytest.mark.asyncio
class TestAnalyzeBidsMocked:
    """analyze_bids / check_qualifications / score_bids — Claude API Mock"""

    def _make_rec(self):
        with patch("app.services.bid_recommender.AsyncAnthropic"):
            rec = BidRecommender()
        return rec

    async def test_analyze_bids_pass_공고_2단계까지_실행(self):
        """pass 판정 공고는 score_bids까지 호출"""
        rec = self._make_rec()
        bids = [make_bid("001"), make_bid("002")]

        qual_response = json.dumps([
            {"bid_no": "001", "qualification_status": "pass"},
            {"bid_no": "002", "qualification_status": "fail", "disqualification_reason": "인증 없음"},
        ])
        score_response = json.dumps([{
            "bid_no": "001", "match_score": 80, "match_grade": "A",
            "recommendation_summary": "적합",
            "recommendation_reasons": [{"category": "기술", "reason": "LLM 경험", "strength": "high"}],
            "risk_factors": [], "win_probability_hint": "중상", "recommended_action": "검토",
        }])

        rec.client.messages.create = AsyncMock(
            side_effect=[
                _make_claude_response(qual_response),
                _make_claude_response(score_response),
            ]
        )

        recommendations, qual_results = await rec.analyze_bids(SAMPLE_PROFILE, bids)

        assert len(qual_results) == 2
        assert len(recommendations) == 1
        assert recommendations[0].bid_no == "001"
        assert recommendations[0].match_score == 80
        # fail 공고는 추천 목록에 없어야 함
        assert all(r.bid_no != "002" for r in recommendations)

    async def test_analyze_bids_전원_fail_score_호출_없음(self):
        """모두 fail이면 2단계 score_bids 호출하지 않음"""
        rec = self._make_rec()
        bids = [make_bid("001")]

        qual_response = json.dumps([
            {"bid_no": "001", "qualification_status": "fail", "disqualification_reason": "건설업"},
        ])
        rec.client.messages.create = AsyncMock(
            return_value=_make_claude_response(qual_response)
        )

        recommendations, qual_results = await rec.analyze_bids(SAMPLE_PROFILE, bids)

        assert rec.client.messages.create.call_count == 1  # 1단계만 호출
        assert recommendations == []
        assert qual_results[0].qualification_status == "fail"

    async def test_check_qualifications_배치_실패시_ambiguous_처리(self):
        """Claude API 오류 시 해당 배치 전체 ambiguous 처리"""
        rec = self._make_rec()
        bids = [make_bid("001"), make_bid("002")]

        rec.client.messages.create = AsyncMock(side_effect=RuntimeError("API 타임아웃"))

        results = await rec.check_qualifications(SAMPLE_PROFILE, bids)

        assert len(results) == 2
        for r in results:
            assert r.qualification_status == "ambiguous"
            assert "오류" in (r.qualification_notes or "")

    async def test_score_bids_배치_실패시_건너뜀(self):
        """score_bids 배치 실패 시 결과 없이 계속 진행"""
        rec = self._make_rec()
        bids = [make_bid("001")]

        rec.client.messages.create = AsyncMock(side_effect=RuntimeError("API 오류"))

        results = await rec.score_bids(SAMPLE_PROFILE, bids)

        assert results == []  # 실패한 배치는 건너뜀

    async def test_call_qualification_claude_호출_파라미터(self):
        """_call_qualification 이 올바른 파라미터로 Claude 호출"""
        rec = self._make_rec()
        bids = [make_bid("001")]

        qual_json = json.dumps([{"bid_no": "001", "qualification_status": "pass"}])
        rec.client.messages.create = AsyncMock(
            return_value=_make_claude_response(qual_json)
        )

        results = await rec._call_qualification(SAMPLE_PROFILE, bids)

        call_kwargs = rec.client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == rec.model
        assert call_kwargs["max_tokens"] == 2000
        assert len(results) == 1

    async def test_call_scoring_claude_호출_파라미터(self):
        """_call_scoring 이 올바른 파라미터로 Claude 호출"""
        rec = self._make_rec()
        bids = [make_bid("001")]

        score_json = json.dumps([{
            "bid_no": "001", "match_score": 75, "match_grade": "B",
            "recommendation_summary": "적합",
            "recommendation_reasons": [{"category": "기술", "reason": "부합", "strength": "medium"}],
            "risk_factors": [], "win_probability_hint": "중", "recommended_action": "검토",
        }])
        rec.client.messages.create = AsyncMock(
            return_value=_make_claude_response(score_json)
        )

        results = await rec._call_scoring(SAMPLE_PROFILE, bids)

        call_kwargs = rec.client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 4000
        assert len(results) == 1
        assert results[0].match_score == 75

    async def test_analyze_bids_top_n_제한(self):
        """top_n 초과 공고는 2단계 분석 제외"""
        rec = self._make_rec()
        # 5건 생성, top_n=2
        bids = [make_bid(f"00{i}") for i in range(5)]

        qual_json = json.dumps([
            {"bid_no": f"00{i}", "qualification_status": "pass"} for i in range(5)
        ])
        score_json = json.dumps([{
            "bid_no": f"00{i}", "match_score": 70, "match_grade": "B",
            "recommendation_summary": "요약",
            "recommendation_reasons": [{"category": "기술", "reason": "부합", "strength": "medium"}],
            "risk_factors": [], "win_probability_hint": "중", "recommended_action": "검토",
        } for i in range(2)])  # 2건만 반환

        rec.client.messages.create = AsyncMock(
            side_effect=[
                _make_claude_response(qual_json),
                _make_claude_response(score_json),
            ]
        )

        recommendations, _ = await rec.analyze_bids(SAMPLE_PROFILE, bids, top_n=2)

        # 2단계에 전달된 bids가 2건인지 확인
        scoring_call_args = rec.client.messages.create.call_args_list[1]
        user_content = scoring_call_args.kwargs["messages"][0]["content"]
        # 2건만 포함 (bid 000, 001)
        assert user_content.count("bid_no:") == 2
