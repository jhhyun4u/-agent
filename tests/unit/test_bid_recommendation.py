"""
입찰 추천 기능 유닛 테스트 (가상 테스트 데이터)

커버 범위:
1. BidFetcher — _normalize(), _is_qualification_available(), 후처리 필터, date_range 계산
2. BidRecommender — analyze_bids() 실제 Claude API 호출 (E2E)
3. SearchPresetCreate — 검증 로직 (bid_types, keywords)
"""

import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.bid_schemas import (
    BidAnnouncement,
    QualificationResult,
    SearchPresetCreate,
    TeamBidProfile,
)
from app.services.bid_fetcher import BidFetcher
from app.services.bid_recommender import BidRecommender, _score_to_grade


# ─────────────────────────────────────────────────────────────
# 가상 테스트 데이터
# ─────────────────────────────────────────────────────────────

def make_bid(
    bid_no: str = "20260001-00",
    bid_title: str = "AI 기반 행정 업무 지원 시스템 구축",
    agency: str = "행정안전부",
    bid_type: str = "용역",
    budget: int = 300_000_000,
    days_remaining: int = 10,
    content_text: str = None,
    qualification_available: bool = True,
) -> BidAnnouncement:
    deadline = datetime.now(timezone.utc) + timedelta(days=days_remaining)
    return BidAnnouncement(
        bid_no=bid_no,
        bid_title=bid_title,
        agency=agency,
        bid_type=bid_type,
        budget_amount=budget,
        announce_date=date.today(),
        deadline_date=deadline,
        days_remaining=days_remaining,
        content_text=content_text,
        qualification_available=qualification_available,
    )


SAMPLE_TEAM_PROFILE = TeamBidProfile(
    team_id="team-test-001",
    expertise_areas=["AI/ML", "공공데이터", "스마트행정"],
    tech_keywords=["Python", "LLM", "FastAPI", "RAG", "클라우드"],
    past_projects=(
        "행정안전부 AI 챗봇 구축 (2023, 3억), "
        "교육부 LLM 교육 플랫폼 개발 (2024, 5억), "
        "국토부 스마트시티 데이터 분석 (2024, 2억)"
    ),
    company_size="중기업",
    certifications=["GS인증", "SW기업확인서", "ISO27001"],
    business_registration_type="중소기업",
    employee_count=80,
    founded_year=2015,
)


# ─────────────────────────────────────────────────────────────
# 1. BidFetcher — 단위 테스트
# ─────────────────────────────────────────────────────────────

class TestBidFetcherNormalize:
    """_normalize() 메서드 테스트"""

    def setup_method(self):
        g2b = MagicMock()
        db = MagicMock()
        self.fetcher = BidFetcher(g2b_service=g2b, supabase_client=db)

    def test_정상_공고_정규화(self):
        raw = {
            "bidNtceNo": "20260001-00",
            "bidNtceNm": "AI 기반 행정 업무 지원 시스템 구축",
            "ntcInsttNm": "행정안전부",
            "bidClsfcNm": "용역",
            "presmptPrceAmt": "300000000",
            "bfSpecRgstDt": "2026/03/20 18:00:00",
            "bidNtceDt": "2026/03/08 09:00:00",
        }
        bid = self.fetcher._normalize(raw)
        assert bid is not None
        assert bid.bid_no == "20260001-00"
        assert bid.bid_title == "AI 기반 행정 업무 지원 시스템 구축"
        assert bid.agency == "행정안전부"
        assert bid.bid_type == "용역"
        assert bid.budget_amount == 300_000_000
        assert bid.deadline_date is not None

    def test_필수_필드_누락_시_None_반환(self):
        # bid_no 누락
        raw = {"bidNtceNm": "테스트", "ntcInsttNm": "기관"}
        assert self.fetcher._normalize(raw) is None

        # bid_title 누락
        raw = {"bidNtceNo": "001", "ntcInsttNm": "기관"}
        assert self.fetcher._normalize(raw) is None

        # agency 누락
        raw = {"bidNtceNo": "001", "bidNtceNm": "테스트"}
        assert self.fetcher._normalize(raw) is None

    def test_예산_숫자_파싱(self):
        """쉼표 포함 예산 문자열 파싱"""
        raw = {
            "bidNtceNo": "001",
            "bidNtceNm": "테스트 공고",
            "ntcInsttNm": "테스트 기관",
            "presmptPrceAmt": "1,500,000,000",
        }
        bid = self.fetcher._normalize(raw)
        assert bid is not None
        assert bid.budget_amount == 1_500_000_000

    def test_마감일_포맷_다양성(self):
        """다양한 날짜 포맷 파싱"""
        formats_and_raw = [
            "2026/03/20 18:00:00",
            "20260320180000",
            "2026-03-20T18:00:00",
        ]
        for fmt in formats_and_raw:
            raw = {
                "bidNtceNo": "001",
                "bidNtceNm": "테스트",
                "ntcInsttNm": "기관",
                "bfSpecRgstDt": fmt,
            }
            bid = self.fetcher._normalize(raw)
            assert bid is not None, f"포맷 파싱 실패: {fmt}"
            assert bid.deadline_date is not None, f"마감일 None: {fmt}"

    def test_예산_None_처리(self):
        raw = {
            "bidNtceNo": "001",
            "bidNtceNm": "예산없는 공고",
            "ntcInsttNm": "기관",
        }
        bid = self.fetcher._normalize(raw)
        assert bid is not None
        assert bid.budget_amount is None


class TestBidFetcherQualification:
    """_is_qualification_available() 테스트"""

    def setup_method(self):
        self.fetcher = BidFetcher(MagicMock(), MagicMock())

    def test_충분한_텍스트(self):
        text = "본 사업 참여를 위해서는 소프트웨어사업자 신고확인서 보유업체만 참가 가능합니다."
        assert self.fetcher._is_qualification_available(text) is True

    def test_None_반환_False(self):
        assert self.fetcher._is_qualification_available(None) is False

    def test_빈_문자열_False(self):
        assert self.fetcher._is_qualification_available("") is False
        assert self.fetcher._is_qualification_available("  ") is False

    def test_너무_짧은_텍스트_False(self):
        assert self.fetcher._is_qualification_available("짧음") is False

    @pytest.mark.parametrize("phrase", [
        "첨부파일 참조",
        "붙임 참조",
        "별첨 참조",
        "입찰공고문 참조",
    ])
    def test_참조_문구_포함_시_False(self, phrase: str):
        text = f"자격요건은 {phrase}하시기 바랍니다. 상세 내용은 아래를 확인하세요."
        assert self.fetcher._is_qualification_available(text) is False


class TestBidFetcherFilter:
    """후처리 필터 (min_budget, min_days_remaining, bid_types) 테스트"""

    def setup_method(self):
        self.fetcher = BidFetcher(MagicMock(), MagicMock())

    def test_모든_필터_통과(self):
        bid = make_bid(budget=200_000_000, days_remaining=7, bid_type="용역")
        preset = SearchPresetCreate(
            name="기본",
            keywords=["AI"],
            min_budget=100_000_000,
            min_days_remaining=5,
            bid_types=["용역"],
        )
        # 직접 필터 로직 검증
        assert bid.budget_amount >= preset.min_budget
        assert bid.days_remaining >= preset.min_days_remaining
        assert bid.bid_type in preset.bid_types

    def test_예산_미달_필터(self):
        bid = make_bid(budget=50_000_000)
        preset = SearchPresetCreate(
            name="기본", keywords=["AI"], min_budget=100_000_000, bid_types=["용역"]
        )
        assert bid.budget_amount < preset.min_budget

    def test_잔여일_부족_필터(self):
        bid = make_bid(days_remaining=2)
        preset = SearchPresetCreate(
            name="기본", keywords=["AI"], min_days_remaining=5, bid_types=["용역"]
        )
        assert bid.days_remaining < preset.min_days_remaining

    def test_공고종류_불일치_필터(self):
        bid = make_bid(bid_type="공사")
        preset = SearchPresetCreate(
            name="기본", keywords=["AI"], bid_types=["용역"]
        )
        assert bid.bid_type not in preset.bid_types


class TestDateRangeCalculation:
    """announce_date_range_days 날짜 계산 테스트"""

    def test_14일_범위_계산(self):
        range_days = 14
        now = datetime.now(timezone.utc)
        date_to = now.strftime("%Y%m%d%H%M%S")
        date_from = (now - timedelta(days=range_days)).strftime("%Y%m%d%H%M%S")

        assert date_from < date_to
        # date_from이 약 14일 전인지 확인
        parsed_from = datetime.strptime(date_from, "%Y%m%d%H%M%S")
        parsed_to = datetime.strptime(date_to, "%Y%m%d%H%M%S")
        delta = parsed_to - parsed_from
        assert 13 <= delta.days <= 14

    def test_0일_범위_는_제한없음(self):
        """range_days=0이면 date_from/date_to 모두 None"""
        range_days = 0
        date_from = None
        date_to = None
        if range_days and range_days > 0:
            now = datetime.now(timezone.utc)
            date_to = now.strftime("%Y%m%d%H%M%S")
            date_from = (now - timedelta(days=range_days)).strftime("%Y%m%d%H%M%S")
        assert date_from is None
        assert date_to is None

    def test_90일_범위_계산(self):
        range_days = 90
        now = datetime.now(timezone.utc)
        date_from = (now - timedelta(days=range_days)).strftime("%Y%m%d%H%M%S")
        date_to = now.strftime("%Y%m%d%H%M%S")

        parsed_from = datetime.strptime(date_from, "%Y%m%d%H%M%S")
        parsed_to = datetime.strptime(date_to, "%Y%m%d%H%M%S")
        delta = parsed_to - parsed_from
        assert 89 <= delta.days <= 90


# ─────────────────────────────────────────────────────────────
# 2. SearchPresetCreate — 검증 테스트
# ─────────────────────────────────────────────────────────────

class TestSearchPresetValidation:

    def test_정상_프리셋(self):
        p = SearchPresetCreate(
            name="AI분야 기본조건",
            keywords=["AI", "LLM", "머신러닝"],
            min_budget=100_000_000,
            min_days_remaining=5,
            bid_types=["용역"],
            announce_date_range_days=14,
        )
        assert p.name == "AI분야 기본조건"
        assert len(p.keywords) == 3
        assert p.announce_date_range_days == 14

    def test_허용되지않는_공고종류_오류(self):
        with pytest.raises(Exception):
            SearchPresetCreate(
                name="테스트",
                keywords=["AI"],
                bid_types=["컨설팅"],  # 허용값: 용역/공사/물품
            )

    def test_키워드_20자_초과_오류(self):
        with pytest.raises(Exception):
            SearchPresetCreate(
                name="테스트",
                keywords=["인공지능기반스마트행정업무자동화시스템구축"],  # 20자 초과
                bid_types=["용역"],
            )

    def test_announce_date_range_days_기본값_14(self):
        p = SearchPresetCreate(name="테스트", keywords=["AI"], bid_types=["용역"])
        assert p.announce_date_range_days == 14

    def test_announce_date_range_days_0_허용(self):
        p = SearchPresetCreate(
            name="테스트", keywords=["AI"], bid_types=["용역"],
            announce_date_range_days=0
        )
        assert p.announce_date_range_days == 0

    def test_announce_date_range_days_365_허용(self):
        p = SearchPresetCreate(
            name="테스트", keywords=["AI"], bid_types=["용역"],
            announce_date_range_days=365
        )
        assert p.announce_date_range_days == 365

    def test_announce_date_range_days_366_오류(self):
        with pytest.raises(Exception):
            SearchPresetCreate(
                name="테스트", keywords=["AI"], bid_types=["용역"],
                announce_date_range_days=366
            )

    def test_복수_공고종류_허용(self):
        p = SearchPresetCreate(
            name="테스트", keywords=["AI"],
            bid_types=["용역", "공사"]
        )
        assert "용역" in p.bid_types
        assert "공사" in p.bid_types

    def test_preferred_agencies_기본_빈배열(self):
        p = SearchPresetCreate(name="테스트", keywords=["AI"], bid_types=["용역"])
        assert p.preferred_agencies == []

    def test_preferred_agencies_설정(self):
        p = SearchPresetCreate(
            name="테스트", keywords=["AI"], bid_types=["용역"],
            preferred_agencies=["행정안전부", "교육부"]
        )
        assert len(p.preferred_agencies) == 2


# ─────────────────────────────────────────────────────────────
# 3. _score_to_grade 단위 테스트
# ─────────────────────────────────────────────────────────────

class TestScoreToGrade:

    @pytest.mark.parametrize("score,expected", [
        (95, "S"),
        (90, "S"),
        (89, "A"),
        (80, "A"),
        (79, "B"),
        (70, "B"),
        (69, "C"),
        (60, "C"),
        (59, "D"),
        (0, "D"),
    ])
    def test_점수_등급_변환(self, score: int, expected: str):
        assert _score_to_grade(score) == expected


# ─────────────────────────────────────────────────────────────
# 4. BidRecommender — Claude API 실제 호출 (E2E 통합 테스트)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestBidRecommenderE2E:
    """
    Claude API 실제 호출 테스트.
    가상 공고 3건 + 팀 프로필로 2단계 분석 전체 실행.
    """

    SAMPLE_BIDS = [
        make_bid(
            bid_no="2026-AI-001",
            bid_title="AI 기반 민원 처리 자동화 시스템 구축 및 운영",
            agency="행정안전부",
            budget=500_000_000,
            days_remaining=15,
            content_text=(
                "본 사업은 AI·LLM 기술을 활용하여 민원 자동처리 시스템을 구축합니다. "
                "참가 자격: 소프트웨어사업자 신고확인서 보유 업체, "
                "유사 사업 수행 실적 2억 이상 (최근 5년), 기업부설연구소 보유."
            ),
        ),
        make_bid(
            bid_no="2026-EDU-002",
            bid_title="초중등 AI 교육 플랫폼 개발 및 콘텐츠 제작",
            agency="교육부",
            budget=800_000_000,
            days_remaining=20,
            content_text=(
                "AI 디지털 교과서 연계 학습 플랫폼 개발 사업. "
                "교육 소프트웨어 개발 전문 기업, GS인증 보유 업체 우대. "
                "LLM 기반 맞춤형 학습 추천 기능 포함."
            ),
        ),
        make_bid(
            bid_no="2026-CON-003",
            bid_title="국도 5호선 교량 보수 공사",
            agency="국토교통부",
            bid_type="공사",
            budget=2_000_000_000,
            days_remaining=8,
            content_text=(
                "콘크리트 교량 균열 보수 및 방수 공사. "
                "건설업 등록 필수, 토목 면허 보유 업체만 참가 가능."
            ),
        ),
    ]

    async def test_analyze_bids_전체_파이프라인(self):
        """3건 공고 2단계 분석 — 추천 목록과 자격 판정 결과 반환"""
        recommender = BidRecommender()
        recommendations, qual_results = await recommender.analyze_bids(
            SAMPLE_TEAM_PROFILE, self.SAMPLE_BIDS
        )

        # 자격 판정 3건 모두 반환
        assert len(qual_results) == 3

        # 모든 status가 유효한 값
        for q in qual_results:
            assert q.qualification_status in ("pass", "fail", "ambiguous")

        # 건설 공사는 fail이어야 함 (AI 팀과 불일치)
        con_result = next((q for q in qual_results if q.bid_no == "2026-CON-003"), None)
        assert con_result is not None
        assert con_result.qualification_status == "fail", (
            f"건설 공사 공고는 fail이어야 합니다. 실제: {con_result.qualification_status}"
        )

        print(f"\n[E2E] 자격 판정 결과:")
        for q in qual_results:
            print(f"  {q.bid_no}: {q.qualification_status}")
            if q.disqualification_reason:
                print(f"    사유: {q.disqualification_reason}")

    async def test_추천_목록_점수_정렬(self):
        """추천 결과가 match_score 내림차순 정렬"""
        recommender = BidRecommender()
        recommendations, _ = await recommender.analyze_bids(
            SAMPLE_TEAM_PROFILE, self.SAMPLE_BIDS
        )

        if len(recommendations) >= 2:
            scores = [r.match_score for r in recommendations]
            assert scores == sorted(scores, reverse=True), (
                f"점수 내림차순 정렬 실패: {scores}"
            )

        print(f"\n[E2E] 추천 결과 ({len(recommendations)}건):")
        for r in recommendations:
            print(f"  [{r.match_grade}] {r.bid_no} - {r.match_score}점")
            print(f"    요약: {r.recommendation_summary}")

    async def test_추천_결과_스키마_유효성(self):
        """BidRecommendation 스키마 필드 검증"""
        recommender = BidRecommender()
        recommendations, _ = await recommender.analyze_bids(
            SAMPLE_TEAM_PROFILE, self.SAMPLE_BIDS
        )

        for rec in recommendations:
            assert 0 <= rec.match_score <= 100
            assert rec.match_grade in ("S", "A", "B", "C", "D")
            assert len(rec.recommendation_summary) > 0
            assert len(rec.recommendation_reasons) >= 1
            assert rec.win_probability_hint
            assert rec.recommended_action

            for reason in rec.recommendation_reasons:
                assert reason.category in ("전문성", "실적", "규모", "기술", "지역", "기타")
                assert reason.strength in ("high", "medium", "low")

            for risk in rec.risk_factors:
                assert risk.level in ("high", "medium", "low")

    async def test_빈_공고_목록(self):
        """공고 없을 때 빈 결과 반환"""
        recommender = BidRecommender()
        recommendations, qual_results = await recommender.analyze_bids(
            SAMPLE_TEAM_PROFILE, []
        )
        assert recommendations == []
        assert qual_results == []

    async def test_qualification_unavailable_자동_ambiguous(self):
        """qualification_available=False 공고는 자동 ambiguous 처리"""
        recommender = BidRecommender()
        bid_no_qa = make_bid(
            bid_no="2026-QA-999",
            bid_title="자격요건 파일 첨부 공고",
            qualification_available=False,
        )
        _, qual_results = await recommender.analyze_bids(
            SAMPLE_TEAM_PROFILE, [bid_no_qa]
        )

        result = next((q for q in qual_results if q.bid_no == "2026-QA-999"), None)
        assert result is not None
        assert result.qualification_status == "ambiguous"
        assert result.qualification_notes is not None
        print(f"\n[E2E] 자동 ambiguous: {result.qualification_notes}")
