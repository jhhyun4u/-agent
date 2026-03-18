"""
입찰 공고 수집 서비스

G2BService 래퍼 + 후처리 필터 + Supabase upsert.
새 API 연동 코드를 작성하지 않고 G2BService를 내부적으로 사용한다.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.models.bid_schemas import BidAnnouncement, SearchPreset
from app.services.g2b_service import G2BService

logger = logging.getLogger(__name__)

_QUALIFICATION_UNAVAILABLE_PHRASES = ("첨부파일 참조", "붙임 참조", "별첨 참조", "입찰공고문 참조")


class BidFetcher:
    """나라장터 공고 수집 + 후처리 필터 + DB upsert"""

    # 키워드당 최대 수집 건수 (API 기본값 20에서 상향)
    NUM_OF_ROWS = 100

    def __init__(self, g2b_service: G2BService, supabase_client):
        self.g2b = g2b_service
        self.db = supabase_client

    # ── 공개 API ────────────────────────────────────────────

    async def fetch_bids_by_preset(self, preset: SearchPreset) -> list[BidAnnouncement]:
        """
        프리셋 기반 공고 수집 통합 실행.

        1. 키워드별 search_bid_announcements() 호출 후 합산 (중복 제거)
        2. 후처리 필터: min_budget / min_days_remaining / bid_types
        3. BidAnnouncement 스키마로 정규화
        4. bid_announcements 테이블에 upsert
        5. 각 공고별 fetch_bid_detail() 호출하여 content_text 확보
        """
        raw_bids: dict[str, dict] = {}  # bid_no → raw dict (중복 제거)

        # 당일 신규 공고만 검색
        today = date.today()
        date_from = today.strftime("%Y%m%d") + "0000"
        date_to = today.strftime("%Y%m%d") + "2359"
        logger.info(f"당일 신규 공고 검색: {date_from} ~ {date_to}")

        for keyword in preset.keywords:
            try:
                results = await self.g2b.search_bid_announcements(
                    keyword, num_of_rows=self.NUM_OF_ROWS,
                    date_from=date_from, date_to=date_to,
                )
                for item in results:
                    bid_no = item.get("bidNtceNo")
                    if bid_no and bid_no not in raw_bids:
                        raw_bids[bid_no] = item
            except Exception as e:
                logger.warning(f"키워드 '{keyword}' 수집 실패 (계속 진행): {e}")

        # 후처리 필터 적용
        filtered: list[BidAnnouncement] = []
        today = date.today()

        for raw in raw_bids.values():
            bid = self._normalize(raw)
            if bid is None:
                continue

            # bid_types 필터
            if bid.bid_type and bid.bid_type not in preset.bid_types:
                continue

            # min_budget 필터
            if bid.budget_amount is not None and bid.budget_amount < preset.min_budget:
                continue

            # min_days_remaining 필터
            if bid.deadline_date is not None:
                days = (bid.deadline_date.date() - today).days
                if days < preset.min_days_remaining:
                    continue

            filtered.append(bid)

        if not filtered:
            logger.info("수집 후 필터 통과 공고 없음")
            return []

        # 공고 상세(자격요건) 수집
        for bid in filtered:
            bid = await self._enrich_detail(bid)

        # Supabase upsert
        await self._upsert_announcements(filtered)

        logger.info(f"공고 수집 완료: {len(filtered)}건 (키워드: {preset.keywords})")
        return filtered

    async def fetch_bid_detail(self, bid_no: str) -> Optional[str]:
        """
        단일 공고 상세내용 수집.

        Returns:
            content_text (규격서 내용). 확보 불가면 None.
        """
        try:
            detail = await self.g2b.get_bid_detail(bid_no)
            return self._extract_content_text(detail)
        except Exception as e:
            logger.warning(f"공고 상세 수집 실패 bid_no={bid_no}: {e}")
            return None

    # ── 내부 헬퍼 ────────────────────────────────────────────

    def _normalize(self, raw: dict) -> Optional[BidAnnouncement]:
        """나라장터 API 응답 dict → BidAnnouncement 스키마 변환"""
        try:
            bid_no = raw.get("bidNtceNo", "").strip()
            bid_title = raw.get("bidNtceNm", "").strip()
            agency = (raw.get("ntceInsttNm") or raw.get("dminsttNm") or "").strip()
            if not bid_no or not bid_title or not agency:
                return None

            budget_amount: Optional[int] = None
            raw_budget = raw.get("presmptPrce") or raw.get("asignBdgtAmt") or raw.get("presmptPrceAmt")
            if raw_budget:
                try:
                    budget_amount = int(float(str(raw_budget).replace(",", "")))
                except (ValueError, TypeError):
                    pass

            deadline_date: Optional[datetime] = None
            raw_deadline = raw.get("bidClseDt") or raw.get("bfSpecRgstDt") or raw.get("bidNtceDt")
            if raw_deadline:
                try:
                    # 포맷 예: "2026/03/20 18:00:00" 또는 "20260320180000"
                    for fmt in ("%Y/%m/%d %H:%M:%S", "%Y%m%d%H%M%S", "%Y-%m-%dT%H:%M:%S"):
                        try:
                            deadline_date = datetime.strptime(str(raw_deadline).strip(), fmt)
                            deadline_date = deadline_date.replace(tzinfo=timezone.utc)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

            days_remaining: Optional[int] = None
            if deadline_date:
                days_remaining = (deadline_date.date() - date.today()).days

            announce_date = None
            raw_announce = raw.get("bidNtceDt")
            if raw_announce and len(str(raw_announce)) >= 8:
                try:
                    announce_date = date.fromisoformat(str(raw_announce)[:10].replace("/", "-"))
                except ValueError:
                    pass

            return BidAnnouncement(
                bid_no=bid_no,
                bid_title=bid_title,
                agency=agency,
                bid_type=raw.get("bidClsfcNm"),
                budget_amount=budget_amount,
                announce_date=announce_date,
                deadline_date=deadline_date,
                days_remaining=days_remaining,
                content_text=None,
                qualification_available=True,
            )
        except Exception as e:
            logger.warning(f"공고 정규화 실패: {e} | raw={raw.get('bidNtceNo')}")
            return None

    async def _enrich_detail(self, bid: BidAnnouncement) -> BidAnnouncement:
        """공고 상세 API로 content_text 보강"""
        try:
            detail = await self.g2b.get_bid_detail(bid.bid_no)
            content = self._extract_content_text(detail)
            bid.content_text = content
            bid.qualification_available = self._is_qualification_available(content)
        except Exception as e:
            logger.warning(f"상세 수집 실패 bid_no={bid.bid_no}: {e}")
            bid.qualification_available = False
        return bid

    def _extract_content_text(self, detail: dict) -> Optional[str]:
        """상세 API 응답에서 규격서 내용 추출"""
        return (
            detail.get("ntceSpecCn")
            or detail.get("bidNtceDtlCn")
            or detail.get("specDocCn")
        )

    def _is_qualification_available(self, content: Optional[str]) -> bool:
        """자격요건 텍스트 확보 가능 여부 판단"""
        if not content or len(content.strip()) < 20:
            return False
        for phrase in _QUALIFICATION_UNAVAILABLE_PHRASES:
            if phrase in content:
                return False
        return True

    async def _upsert_announcements(self, bids: list[BidAnnouncement]) -> None:
        """bid_announcements 테이블에 upsert (bid_no 기준)"""
        rows = []
        for bid in bids:
            row = {
                "bid_no": bid.bid_no,
                "bid_title": bid.bid_title,
                "agency": bid.agency,
                "bid_type": bid.bid_type,
                "budget_amount": bid.budget_amount,
                "deadline_date": bid.deadline_date.isoformat() if bid.deadline_date else None,
                "days_remaining": bid.days_remaining,
                "content_text": bid.content_text,
                "qualification_available": bid.qualification_available,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
            if bid.announce_date:
                row["announce_date"] = bid.announce_date.isoformat()
            rows.append(row)

        try:
            await (
                self.db.table("bid_announcements")
                .upsert(rows, on_conflict="bid_no")
                .execute()
            )
        except Exception as e:
            logger.error(f"bid_announcements upsert 실패: {e}")
            raise
