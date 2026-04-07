"""
공고 적합도 스코어링 유닛 테스트 (app.services.bidding.monitor.scorer)

score_bid() 4단계 파이프라인, score_and_rank_bids() 배치 처리,
정규화 어댑터(normalize_pre_spec/plan)를 검증한다.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.services.bidding.monitor.scorer import (
    BidScore,
    _normalize_title,
    normalize_plan_for_scoring,
    normalize_pre_spec_for_scoring,
    score_and_rank_bids,
    score_bid,
)


# ─────────────────────────────────────────────────────────────
# 픽스처 헬퍼
# ─────────────────────────────────────────────────────────────

REF_DATE = date(2026, 3, 29)  # 고정 기준일


def make_raw(
    title: str = "AI 기술 전략 수립 용역",
    agency: str = "과학기술정보통신부",
    classification: str = "전략계획서비스",
    classification_large: str = "컨설팅",
    budget: str = "300000000",
    deadline_days: int = 10,
    bid_method: str = "",
    bid_no: str = "20260001-00",
) -> dict:
    """테스트용 공고 raw dict 생성."""
    dl = (date.today() + timedelta(days=deadline_days)).strftime("%Y/%m/%d 18:00:00")
    return {
        "bidNtceNo": bid_no,
        "bidNtceNm": title,
        "ntceInsttNm": agency,
        "pubPrcrmntClsfcNm": classification,
        "pubPrcrmntLrgClsfcNm": classification_large,
        "presmptPrce": budget,
        "bidClseDt": dl,
        "bidMethdNm": bid_method,
    }


# ─────────────────────────────────────────────────────────────
# score_bid — 1단계: 역할 키워드 필수 매칭
# ─────────────────────────────────────────────────────────────

class TestScoreBidRoleKeywords:

    def test_역할_키워드_없으면_탈락(self):
        raw = make_raw(title="공장 신축 공사", classification="건설시공")
        result = score_bid(raw, REF_DATE)
        assert result.passed is False
        assert result.score == -1

    def test_전략_키워드_포함시_통과(self):
        raw = make_raw(title="기술 전략 수립 컨설팅")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        assert "전략" in result.role_keywords_matched

    def test_기획_키워드_포함시_통과(self):
        raw = make_raw(title="AI 정책 기획 연구")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        assert "기획" in result.role_keywords_matched

    def test_복수_역할_키워드_모두_기록(self):
        raw = make_raw(title="디지털 전략 기획 평가 연구")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        matched = result.role_keywords_matched
        assert "전략" in matched
        assert "기획" in matched
        assert "평가" in matched

    def test_ISP_키워드_영문_통과(self):
        raw = make_raw(title="행정정보화 ISP 수립 용역")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        assert "ISP" in result.role_keywords_matched

    def test_타당성_키워드_통과(self):
        raw = make_raw(title="R&D 기술 타당성 조사")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        assert "타당성" in result.role_keywords_matched

    def test_진단_키워드_통과(self):
        raw = make_raw(title="IT 시스템 진단 및 개선 방안")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        assert "진단" in result.role_keywords_matched

    def test_기본계획_키워드_통과(self):
        raw = make_raw(title="스마트시티 기본계획 수립")
        result = score_bid(raw, REF_DATE)
        assert result.passed is True
        assert "기본계획" in result.role_keywords_matched


# ─────────────────────────────────────────────────────────────
# score_bid — 2단계: 분류 가중치
# ─────────────────────────────────────────────────────────────

class TestScoreBidClassification:

    def test_전략계획서비스_가산(self):
        raw_high = make_raw(classification="전략계획서비스")
        raw_none = make_raw(classification="")
        high = score_bid(raw_high, REF_DATE)
        none_ = score_bid(raw_none, REF_DATE)
        assert high.score > none_.score
        assert high.classification_score >= 30

    def test_컨설팅_분류_가산(self):
        raw = make_raw(classification="컨설팅용역서비스", classification_large="컨설팅")
        result = score_bid(raw, REF_DATE)
        assert result.classification_score > 0

    def test_폐기물_분류_감점(self):
        # classification_large를 빈 값으로 설정해야 컨설팅 가산이 상쇄하지 않음
        raw = make_raw(title="환경 전략 수립", classification="폐기물처리용역", classification_large="")
        result = score_bid(raw, REF_DATE)
        assert result.classification_score < 0

    def test_청소_분류_감점(self):
        raw = make_raw(title="청소 기획 관리", classification="청소용역", classification_large="")
        result = score_bid(raw, REF_DATE)
        assert result.classification_score < 0


# ─────────────────────────────────────────────────────────────
# score_bid — 3단계: 도메인 키워드 가산
# ─────────────────────────────────────────────────────────────

class TestScoreBidDomainKeywords:

    def test_AI_도메인_가산(self):
        raw_with = make_raw(title="AI 기술 전략 수립")
        raw_without = make_raw(title="농업 전략 수립")
        with_ = score_bid(raw_with, REF_DATE)
        without_ = score_bid(raw_without, REF_DATE)
        assert with_.score > without_.score
        assert "AI" in with_.domain_keywords_matched

    def test_핵심_도메인_is_core_domain_True(self):
        raw = make_raw(title="디지털 전략 수립 컨설팅")
        result = score_bid(raw, REF_DATE)
        assert result.is_core_domain is True

    def test_비핵심_도메인_is_core_domain_False(self):
        raw = make_raw(title="농업 전략 수립")
        result = score_bid(raw, REF_DATE)
        assert result.is_core_domain is False

    def test_복수_도메인_키워드_누적_가산(self):
        raw = make_raw(title="AI 데이터 디지털 혁신 전략")
        result = score_bid(raw, REF_DATE)
        assert len(result.domain_keywords_matched) >= 3


# ─────────────────────────────────────────────────────────────
# score_bid — 4단계: 컨텍스트 감점
# ─────────────────────────────────────────────────────────────

class TestScoreBidContextPenalty:

    def test_건립_감점(self):
        raw = make_raw(title="도서관 건립 타당성 조사")
        result = score_bid(raw, REF_DATE)
        # "타당성"으로 통과하지만 "건립" 감점 — 단, PENALTY_EXEMPT_KEYWORDS 없으면 감점
        # "타당성"은 PENALTY_EXEMPT_KEYWORDS에 없으므로 감점 적용
        assert result.context_penalty < 0

    def test_전략_포함시_감점_면제(self):
        raw_exempt = make_raw(title="물류센터 건립 물류 전략 수립")
        raw_penalty = make_raw(title="물류센터 건립 타당성 조사")
        exempt = score_bid(raw_exempt, REF_DATE)
        penalty = score_bid(raw_penalty, REF_DATE)
        # 면제 키워드(전략) 있으면 컨텍스트 감점 0
        assert exempt.context_penalty == 0
        assert penalty.context_penalty < 0

    def test_기획_포함시_감점_면제(self):
        raw = make_raw(title="신축 시설 기획 연구")
        result = score_bid(raw, REF_DATE)
        assert result.context_penalty == 0

    def test_보수공사_감점(self):
        raw = make_raw(title="도로 보수공사 타당성 검토")
        result = score_bid(raw, REF_DATE)
        assert result.context_penalty < 0


# ─────────────────────────────────────────────────────────────
# score_bid — 마감일 파싱 및 마감 임박 가산/감점
# ─────────────────────────────────────────────────────────────

class TestScoreBidDeadline:

    def test_마감_임박_3일내_D3_가산(self):
        dl = (date.today() + timedelta(days=3)).strftime("%Y/%m/%d 18:00:00")
        raw = make_raw(title="AI 전략", deadline_days=3)
        raw["bidClseDt"] = dl
        result = score_bid(raw, date.today())
        assert result.d_day in (3, 4)
        # 3~7일: +10
        assert result.score > 0

    def test_이미_마감된_공고_감점(self):
        raw = make_raw(title="AI 전략", deadline_days=-1)
        result = score_bid(raw, date.today())
        assert result.d_day is not None and result.d_day < 0

    def test_마감일_없으면_d_day_None(self):
        raw = make_raw(title="AI 전략")
        raw["bidClseDt"] = ""
        result = score_bid(raw, REF_DATE)
        assert result.d_day is None

    def test_날짜형식_yyyymmddHHMMSS_파싱(self):
        dl = (date.today() + timedelta(days=10)).strftime("%Y%m%d180000")
        raw = make_raw(title="AI 전략")
        raw["bidClseDt"] = dl
        result = score_bid(raw, date.today())
        assert result.d_day is not None
        assert 9 <= result.d_day <= 11

    def test_날짜형식_ISO_파싱(self):
        dl = (date.today() + timedelta(days=10)).strftime("%Y-%m-%dT18:00:00")
        raw = make_raw(title="AI 전략")
        raw["bidClseDt"] = dl
        result = score_bid(raw, date.today())
        assert result.d_day is not None


# ─────────────────────────────────────────────────────────────
# score_bid — 예산 가산
# ─────────────────────────────────────────────────────────────

class TestScoreBidBudget:

    def test_예산_0원_가산없음(self):
        raw_zero = make_raw(title="AI 전략", budget="0")
        raw_large = make_raw(title="AI 전략", budget="1000000000")
        zero = score_bid(raw_zero, REF_DATE)
        large = score_bid(raw_large, REF_DATE)
        assert large.score > zero.score

    def test_예산_10억_최대_가산30점(self):
        raw = make_raw(title="AI 전략", budget="1000000000")
        result = score_bid(raw, REF_DATE)
        # 10억 / 1억 * 2 = 20점, max 30점 이하
        budget_score = min(10 * 2, 30)
        assert budget_score == 20

    def test_예산_파싱_실패시_0처리(self):
        raw = make_raw(title="AI 전략")
        raw["presmptPrce"] = "금액미정"
        result = score_bid(raw, REF_DATE)
        assert result.passed is True  # 예산 파싱 실패해도 통과
        assert result.budget == 0

    def test_쉼표포함_예산_파싱(self):
        raw = make_raw(title="AI 전략")
        raw["presmptPrce"] = "500,000,000"
        result = score_bid(raw, REF_DATE)
        assert result.budget == 500_000_000


# ─────────────────────────────────────────────────────────────
# score_and_rank_bids — 배치 처리
# ─────────────────────────────────────────────────────────────

class TestScoreAndRankBids:

    def _make_batch(self, titles: list[str]) -> list[dict]:
        return [
            make_raw(title=t, bid_no=f"{i:05d}-00")
            for i, t in enumerate(titles, 1)
        ]

    def test_역할_키워드_없는_공고_탈락(self):
        bids = [
            make_raw(title="AI 전략 수립", bid_no="001"),
            make_raw(title="건물 청소 용역", bid_no="002"),
        ]
        result = score_and_rank_bids(bids, REF_DATE)
        assert len(result) == 1
        assert result[0].bid_no == "001"

    def test_점수_내림차순_정렬(self):
        # 전략계획서비스(높은 분류) vs 기타(낮은 분류)
        bids = [
            make_raw(title="AI 전략 수립", classification="기타기술용역", bid_no="low"),
            make_raw(title="디지털 혁신 전략", classification="전략계획서비스", bid_no="high"),
        ]
        result = score_and_rank_bids(bids, REF_DATE)
        assert result[0].bid_no == "high"

    def test_수의시담_제외(self):
        bids = [
            make_raw(title="AI 전략 수립", bid_method="수의시담", bid_no="001"),
            make_raw(title="R&D 기획 용역", bid_method="일반경쟁", bid_no="002"),
        ]
        result = score_and_rank_bids(bids, REF_DATE)
        assert len(result) == 1
        assert result[0].bid_no == "002"

    def test_수의계약_제외(self):
        bids = [make_raw(title="AI 기획", bid_method="수의계약", bid_no="001")]
        result = score_and_rank_bids(bids, REF_DATE)
        assert result == []

    def test_min_score_필터(self):
        bids = [
            make_raw(title="AI 전략", bid_no="001", budget="0", classification=""),
        ]
        # min_score 높게 설정 → 통과 불가
        result = score_and_rank_bids(bids, REF_DATE, min_score=999)
        assert result == []

    def test_exclude_expired_기본_마감_제외(self):
        bids = [
            make_raw(title="AI 전략", deadline_days=-5, bid_no="001"),
            make_raw(title="R&D 기획", deadline_days=10, bid_no="002"),
        ]
        result = score_and_rank_bids(bids, date.today(), exclude_expired=True)
        nos = [b.bid_no for b in result]
        assert "001" not in nos
        assert "002" in nos

    def test_exclude_expired_False_마감_포함(self):
        bids = [make_raw(title="AI 전략", deadline_days=-5, bid_no="001")]
        result = score_and_rank_bids(bids, date.today(), exclude_expired=False)
        assert len(result) == 1

    def test_max_results_제한(self):
        bids = [
            make_raw(title=f"AI 전략 수립 용역 {i}", bid_no=f"{i:05d}")
            for i in range(10)
        ]
        result = score_and_rank_bids(bids, REF_DATE, max_results=3)
        assert len(result) <= 3

    def test_bid_no_중복_제거(self):
        bids = [
            make_raw(title="AI 전략 수립", bid_no="DUP-001"),
            make_raw(title="AI 전략 수립 재공고", bid_no="DUP-001"),
        ]
        result = score_and_rank_bids(bids, REF_DATE)
        assert len(result) == 1

    def test_제목_정규화_중복_제거(self):
        """재공고 접두사만 다른 동일 공고는 중복 제거."""
        bids = [
            make_raw(title="AI 기술전략 수립 용역", bid_no="A001"),
            make_raw(title="[재공고] AI 기술전략 수립 용역", bid_no="A002"),
        ]
        result = score_and_rank_bids(bids, REF_DATE)
        assert len(result) == 1

    def test_빈_목록_빈_결과(self):
        result = score_and_rank_bids([], REF_DATE)
        assert result == []


# ─────────────────────────────────────────────────────────────
# 고가치 역할 조합 보너스
# ─────────────────────────────────────────────────────────────

class TestHighValueRoleCombos:

    def test_전략_기획_조합_보너스(self):
        raw_combo = make_raw(title="디지털 전략 기획 수립")
        raw_single = make_raw(title="디지털 전략 수립")
        combo = score_bid(raw_combo, REF_DATE)
        single = score_bid(raw_single, REF_DATE)
        assert combo.score > single.score

    def test_타당성_조사_조합_보너스(self):
        raw = make_raw(title="R&D 타당성 조사 연구")
        result = score_bid(raw, REF_DATE)
        # "타당성" + "조사" 조합 → 보너스
        assert "타당성" in result.role_keywords_matched
        assert "조사" in result.role_keywords_matched


# ─────────────────────────────────────────────────────────────
# 정규화 어댑터
# ─────────────────────────────────────────────────────────────

class TestNormalizePreSpec:

    def test_bfSpecRgstNo_bid_no_변환(self):
        raw = {"bfSpecRgstNo": "2026-01", "bfSpecRgstNm": "AI 전략 기획", "orderInsttNm": "과기부"}
        result = normalize_pre_spec_for_scoring(raw)
        assert result["bidNtceNo"] == "PRE-2026-01"
        assert result["bidNtceNm"] == "AI 전략 기획"
        assert result["_bid_stage"] == "사전규격"

    def test_prcSpcfNo_폴백(self):
        raw = {"prcSpcfNo": "SPEC-99", "prcSpcfNm": "ISP 수립"}
        result = normalize_pre_spec_for_scoring(raw)
        assert result["bidNtceNo"] == "PRE-SPEC-99"
        assert result["bidNtceNm"] == "ISP 수립"

    def test_빈_입력(self):
        result = normalize_pre_spec_for_scoring({})
        assert result["bidNtceNo"] == "PRE-"
        assert result["bidNtceNm"] == ""
        assert result["_bid_stage"] == "사전규격"


class TestNormalizePlan:

    def test_orderPlanNo_bid_no_변환(self):
        raw = {"orderPlanNo": "PLN-2026", "orderPlanNm": "디지털 전략 기획", "orderInsttNm": "과기부"}
        result = normalize_plan_for_scoring(raw)
        assert result["bidNtceNo"] == "PLN-PLN-2026"
        assert result["bidNtceNm"] == "디지털 전략 기획"
        assert result["_bid_stage"] == "발주계획"

    def test_cntrctMthdNm_bid_method_매핑(self):
        raw = {"cntrctMthdNm": "수의시담"}
        result = normalize_plan_for_scoring(raw)
        assert result["bidMethdNm"] == "수의시담"

    def test_빈_입력(self):
        result = normalize_plan_for_scoring({})
        assert result["bidNtceNo"] == "PLN-"
        assert result["_bid_stage"] == "발주계획"


# ─────────────────────────────────────────────────────────────
# _normalize_title
# ─────────────────────────────────────────────────────────────

class TestNormalizeTitle:

    def test_재공고_접두사_제거(self):
        assert _normalize_title("[재공고] AI 전략 수립") == _normalize_title("AI 전략 수립")

    def test_긴급_접두사_제거(self):
        assert _normalize_title("[긴급] AI 전략 수립") == _normalize_title("AI 전략 수립")

    def test_50자_이후_잘림(self):
        long_title = "A" * 100
        result = _normalize_title(long_title)
        assert len(result) == 50

    def test_공백_정규화(self):
        result = _normalize_title("AI   기술  전략")
        assert "  " not in result

    def test_사전규격_접두사_제거(self):
        assert _normalize_title("[사전규격] AI 전략") == _normalize_title("AI 전략")
