"""
BidFetcher 유닛 테스트 — fetch_bids_by_preset (v2), _upsert, _enrich_detail

외부 의존성(G2BService, Supabase, bid_scorer)은 모두 Mock 처리.
v2: fetch_all_bids 전수 수집 + score_and_rank_bids 스코어링 파이프라인.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.bid_schemas import BidAnnouncement, SearchPreset
from app.services.bid_fetcher import BidFetcher


# ─────────────────────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────────────────────

def make_preset(
    keywords=None,
    min_budget=100_000_000,
    min_days_remaining=5,
    bid_types=None,
    announce_date_range_days=14,
) -> SearchPreset:
    return SearchPreset(
        id="preset-001",
        team_id="team-001",
        name="테스트 프리셋",
        keywords=keywords or ["AI", "LLM"],
        min_budget=min_budget,
        min_days_remaining=min_days_remaining,
        bid_types=bid_types or ["용역"],
        announce_date_range_days=announce_date_range_days,
    )


def make_raw(
    bid_no="20260001-00",
    bid_title="AI 전략 수립 시스템",
    agency="행정안전부",
    bid_type="용역",
    budget="300000000",
    deadline_offset_days=10,
):
    deadline = (datetime.now(timezone.utc) + timedelta(days=deadline_offset_days)).strftime(
        "%Y/%m/%d %H:%M:%S"
    )
    return {
        "bidNtceNo": bid_no,
        "bidNtceNm": bid_title,
        "ntceInsttNm": agency,
        "bidClsfcNm": bid_type,
        "presmptPrce": budget,
        "bidClseDt": deadline,
        "bidNtceDt": datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S"),
    }


def make_fetcher(g2b=None, db=None) -> BidFetcher:
    g2b = g2b or MagicMock()
    db = db or MagicMock()
    return BidFetcher(g2b_service=g2b, supabase_client=db)


def _make_bid_score(raw, score=50.0, passed=True):
    """bid_scorer.BidScore를 모방하는 간단한 객체 생성."""
    from app.services.bid_scorer import BidScore
    deadline_str = raw.get("bidClseDt", "")
    return BidScore(
        bid_no=raw.get("bidNtceNo", ""),
        title=raw.get("bidNtceNm", ""),
        agency=raw.get("ntceInsttNm", ""),
        budget=int(str(raw.get("presmptPrce", "0")).replace(",", "") or "0"),
        deadline=deadline_str,
        d_day=10,
        classification="",
        classification_large="",
        score=score,
        passed=passed,
        role_keywords_matched=["전략"],
        raw=raw,
    )


def _make_db_mock():
    """upsert 가능한 DB mock 생성."""
    upsert_mock = MagicMock(return_value=MagicMock(execute=AsyncMock(return_value=MagicMock())))
    table_mock = MagicMock(upsert=upsert_mock)
    db = MagicMock()
    db.table = MagicMock(return_value=table_mock)
    return db, upsert_mock


# ─────────────────────────────────────────────────────────────
# fetch_bids_by_preset — v2 통합 흐름
# (fetch_all_bids 전수 수집 + score_and_rank_bids 스코어링)
# ─────────────────────────────────────────────────────────────

class TestFetchBidsByPreset:

    @pytest.mark.asyncio
    async def test_전수수집_1회_호출(self):
        """v2: fetch_all_bids 1회 호출로 전수 수집"""
        raw = make_raw(bid_no="001")
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(return_value=[raw])
        g2b.get_bid_detail = AsyncMock(return_value={"ntceSpecCn": "자격요건 명세가 있습니다."})

        db, _ = _make_db_mock()
        fetcher = make_fetcher(g2b=g2b, db=db)
        preset = make_preset(keywords=["AI", "LLM"])

        bid_score = _make_bid_score(raw)
        with patch("app.services.bid_scorer.score_and_rank_bids", return_value=[bid_score]):
            result = await fetcher.fetch_bids_by_preset(preset)

        # v2: fetch_all_bids 1회 호출 (키워드별이 아님)
        assert g2b.fetch_all_bids.call_count == 1
        assert len(result) == 1
        assert result[0].bid_no == "001"

    @pytest.mark.asyncio
    async def test_전수수집_실패_시_빈_결과(self):
        """fetch_all_bids 실패 시 예외 전파"""
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(side_effect=RuntimeError("API 오류"))

        fetcher = make_fetcher(g2b=g2b)
        preset = make_preset()

        with pytest.raises(RuntimeError, match="API 오류"):
            await fetcher.fetch_bids_by_preset(preset)

    @pytest.mark.asyncio
    async def test_당일_날짜범위_전달(self):
        """v2: 항상 당일 date_from/date_to로 fetch_all_bids 호출"""
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(return_value=[])

        fetcher = make_fetcher(g2b=g2b)
        preset = make_preset(announce_date_range_days=0)

        with patch("app.services.bid_scorer.score_and_rank_bids", return_value=[]):
            await fetcher.fetch_bids_by_preset(preset)

        today_str = date.today().strftime("%Y%m%d")
        g2b.fetch_all_bids.assert_called_once_with(
            today_str + "0000", today_str + "2359"
        )

    @pytest.mark.asyncio
    async def test_프리셋_무관_당일수집(self):
        """v2: announce_date_range_days 값과 무관하게 항상 당일 수집"""
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(return_value=[])

        fetcher = make_fetcher(g2b=g2b)
        preset = make_preset(announce_date_range_days=14)

        with patch("app.services.bid_scorer.score_and_rank_bids", return_value=[]):
            await fetcher.fetch_bids_by_preset(preset)

        today_str = date.today().strftime("%Y%m%d")
        call_args = g2b.fetch_all_bids.call_args[0]
        assert call_args[0] == today_str + "0000"
        assert call_args[1] == today_str + "2359"

    @pytest.mark.asyncio
    async def test_예산_미달_필터_빈_목록(self):
        """스코어링 통과했지만 min_budget 미달이면 빈 목록"""
        raw = make_raw(bid_no="003", budget="50000000")  # 5천만 < 1억
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(return_value=[raw])

        bid_score = _make_bid_score(raw)
        fetcher = make_fetcher(g2b=g2b)
        preset = make_preset(min_budget=100_000_000)

        with patch("app.services.bid_scorer.score_and_rank_bids", return_value=[bid_score]):
            result = await fetcher.fetch_bids_by_preset(preset)

        assert result == []

    @pytest.mark.asyncio
    async def test_bid_type_불일치_제외(self):
        """bid_types에 없는 공고는 프리셋 필터에서 제외"""
        raw = make_raw(bid_no="004", bid_type="공사")
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(return_value=[raw])

        bid_score = _make_bid_score(raw)
        fetcher = make_fetcher(g2b=g2b)
        preset = make_preset(bid_types=["용역"])  # 공사는 제외

        with patch("app.services.bid_scorer.score_and_rank_bids", return_value=[bid_score]):
            result = await fetcher.fetch_bids_by_preset(preset)

        assert result == []

    @pytest.mark.asyncio
    async def test_필터_통과_시_upsert_호출(self):
        """필터 통과 공고가 있으면 DB upsert 호출"""
        raw = make_raw(bid_no="005")
        g2b = MagicMock()
        g2b.fetch_all_bids = AsyncMock(return_value=[raw])
        g2b.get_bid_detail = AsyncMock(return_value={"ntceSpecCn": "자격요건 명세 텍스트."})

        db, upsert_mock = _make_db_mock()
        fetcher = make_fetcher(g2b=g2b, db=db)
        preset = make_preset()

        bid_score = _make_bid_score(raw)
        with patch("app.services.bid_scorer.score_and_rank_bids", return_value=[bid_score]):
            await fetcher.fetch_bids_by_preset(preset)

        db.table.assert_called_with("bid_announcements")
        upsert_mock.assert_called_once()


# ─────────────────────────────────────────────────────────────
# fetch_bid_detail — 공개 메서드
# ─────────────────────────────────────────────────────────────

class TestFetchBidDetail:

    @pytest.mark.asyncio
    async def test_정상_반환(self):
        g2b = MagicMock()
        g2b.get_bid_detail = AsyncMock(return_value={"ntceSpecCn": "자격요건 내용"})
        fetcher = make_fetcher(g2b=g2b)

        result = await fetcher.fetch_bid_detail("20260001-00")

        assert result == "자격요건 내용"

    @pytest.mark.asyncio
    async def test_API_실패시_None_반환(self):
        g2b = MagicMock()
        g2b.get_bid_detail = AsyncMock(side_effect=RuntimeError("연결 실패"))
        fetcher = make_fetcher(g2b=g2b)

        result = await fetcher.fetch_bid_detail("20260001-00")

        assert result is None


# ─────────────────────────────────────────────────────────────
# _normalize — 예외 처리 경로
# ─────────────────────────────────────────────────────────────

class TestNormalizeEdgeCases:

    def setup_method(self):
        self.fetcher = make_fetcher()

    def test_예산_파싱_실패시_None(self):
        """예산이 숫자로 변환 불가면 budget_amount=None"""
        raw = {
            "bidNtceNo": "001", "bidNtceNm": "테스트", "ntceInsttNm": "기관",
            "presmptPrce": "금액미정(협의)",
        }
        bid = self.fetcher._normalize(raw)
        assert bid is not None
        assert bid.budget_amount is None

    def test_공고일_파싱_실패시_announce_date_None(self):
        """bidNtceDt가 파싱 불가 형식이면 announce_date=None"""
        raw = {
            "bidNtceNo": "001", "bidNtceNm": "테스트", "ntceInsttNm": "기관",
            "bidNtceDt": "invalid-date",
        }
        bid = self.fetcher._normalize(raw)
        assert bid is not None
        assert bid.announce_date is None

    def test_normalize_pydantic_유효성_실패시_None_반환(self):
        """BidAnnouncement 생성 실패 시 None 반환"""
        fetcher = make_fetcher()
        # bid_no가 빈 문자열 → 필수 필드 누락 → None 반환
        raw = {"bidNtceNo": "", "bidNtceNm": "테스트", "ntceInsttNm": "기관"}
        result = fetcher._normalize(raw)
        assert result is None


# ─────────────────────────────────────────────────────────────
# _upsert_announcements — 예외 처리
# ─────────────────────────────────────────────────────────────

class TestUpsertAnnouncements:

    @pytest.mark.asyncio
    async def test_upsert_실패시_예외_재발생(self):
        """DB upsert 실패 시 예외를 caller에게 전달"""
        upsert_mock = MagicMock(return_value=MagicMock(
            execute=AsyncMock(side_effect=RuntimeError("DB 오류"))
        ))
        table_mock = MagicMock(upsert=upsert_mock)
        db = MagicMock()
        db.table = MagicMock(return_value=table_mock)

        fetcher = make_fetcher(db=db)
        bids = [BidAnnouncement(bid_no="001", bid_title="테스트", agency="기관")]

        with pytest.raises(RuntimeError, match="DB 오류"):
            await fetcher._upsert_announcements(bids)


# ─────────────────────────────────────────────────────────────
# _enrich_detail
# ─────────────────────────────────────────────────────────────

class TestEnrichDetail:

    @pytest.mark.asyncio
    async def test_상세_수집_성공(self):
        g2b = MagicMock()
        g2b.get_bid_detail = AsyncMock(
            return_value={"ntceSpecCn": "소프트웨어사업자 신고확인서 보유 업체 참가 가능합니다."}
        )
        fetcher = make_fetcher(g2b=g2b)

        bid = BidAnnouncement(bid_no="001", bid_title="테스트", agency="기관")
        result = await fetcher._enrich_detail(bid)

        assert result.content_text is not None
        assert result.qualification_available is True

    @pytest.mark.asyncio
    async def test_상세_수집_실패시_qualification_available_False(self):
        g2b = MagicMock()
        g2b.get_bid_detail = AsyncMock(side_effect=RuntimeError("연결 실패"))
        fetcher = make_fetcher(g2b=g2b)

        bid = BidAnnouncement(bid_no="001", bid_title="테스트", agency="기관")
        result = await fetcher._enrich_detail(bid)

        assert result.qualification_available is False

    @pytest.mark.asyncio
    async def test_첨부파일_참조_문구_qualification_unavailable(self):
        g2b = MagicMock()
        g2b.get_bid_detail = AsyncMock(
            return_value={"ntceSpecCn": "자격요건은 첨부파일 참조하시기 바랍니다. 상세 내용은 공고문 확인."}
        )
        fetcher = make_fetcher(g2b=g2b)

        bid = BidAnnouncement(bid_no="001", bid_title="테스트", agency="기관")
        result = await fetcher._enrich_detail(bid)

        assert result.qualification_available is False


# ─────────────────────────────────────────────────────────────
# _extract_content_text
# ─────────────────────────────────────────────────────────────

class TestExtractContentText:

    def test_ntceSpecCn_우선(self):
        fetcher = make_fetcher()
        detail = {"ntceSpecCn": "규격서 내용", "bidNtceDtlCn": "공고 상세"}
        assert fetcher._extract_content_text(detail) == "규격서 내용"

    def test_ntceSpecCn_없으면_bidNtceDtlCn(self):
        fetcher = make_fetcher()
        detail = {"bidNtceDtlCn": "공고 상세 내용"}
        assert fetcher._extract_content_text(detail) == "공고 상세 내용"

    def test_모두_없으면_None(self):
        fetcher = make_fetcher()
        assert fetcher._extract_content_text({}) is None

    def test_specDocCn_폴백(self):
        fetcher = make_fetcher()
        detail = {"specDocCn": "스펙 문서 내용"}
        assert fetcher._extract_content_text(detail) == "스펙 문서 내용"
