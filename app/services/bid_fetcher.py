"""
입찰 공고 수집 서비스

G2BService 래퍼 + 후처리 필터 + Supabase upsert.
새 API 연동 코드를 작성하지 않고 G2BService를 내부적으로 사용한다.
"""

import asyncio
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

    async def fetch_bids_scored(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_budget: int = 0,
        min_days_remaining: int = 3,
        min_score: float = 0,
        max_results: int = 50,
    ) -> dict:
        """
        3소스 전수 수집 + 적합도 스코어링 파이프라인 (v3).

        1. 입찰공고 + 사전규격 + 발주계획 병렬 수집
        2. 정규화 → 공통 형식으로 합산
        3. bid_scorer.score_and_rank_bids() 스코어링
        4. 후처리 필터 + sources 집계

        Returns:
            {"total_fetched": int, "sources": {...}, "data": [...]}
        """
        from app.services.bid_scorer import (
            normalize_plan_for_scoring,
            normalize_pre_spec_for_scoring,
            score_and_rank_bids,
        )

        today = date.today()
        if not date_to:
            date_to = today.strftime("%Y%m%d") + "2359"
        if not date_from:
            date_from = today.strftime("%Y%m%d") + "0000"

        # 1) 3소스 병렬 수집 (개별 실패 허용)
        all_bids, all_pre, all_plans = await asyncio.gather(
            self.g2b.fetch_all_bids(date_from, date_to),
            self.g2b.fetch_all_pre_specs(date_from, date_to),
            self.g2b.fetch_all_procurement_plans(date_from, date_to),
            return_exceptions=True,
        )

        if isinstance(all_bids, BaseException):
            logger.warning(f"입찰공고 수집 실패: {all_bids}")
            all_bids = []
        if isinstance(all_pre, BaseException):
            logger.warning(f"사전규격 수집 실패: {all_pre}")
            all_pre = []
        if isinstance(all_plans, BaseException):
            logger.warning(f"발주계획 수집 실패: {all_plans}")
            all_plans = []

        # 2) 정규화 + 합산
        combined = list(all_bids)
        combined.extend(normalize_pre_spec_for_scoring(r) for r in all_pre)
        combined.extend(normalize_plan_for_scoring(r) for r in all_plans)

        total_fetched = len(all_bids) + len(all_pre) + len(all_plans)
        logger.info(
            f"전수 수집: 공고 {len(all_bids)} + 사전규격 {len(all_pre)} + "
            f"발주계획 {len(all_plans)} = {total_fetched}건 ({date_from}~{date_to})"
        )

        # 3) 스코어링
        scored = score_and_rank_bids(
            combined,
            reference_date=today,
            min_score=min_score,
            exclude_expired=True,
            max_results=max_results * 2,
        )

        # 4) 후처리 필터 + sources 집계
        sources = {"입찰공고": 0, "사전규격": 0, "발주계획": 0}
        results = []
        for bs in scored:
            if bs.budget < min_budget:
                continue
            if bs.d_day is not None and bs.d_day < min_days_remaining:
                continue
            sources[bs.bid_stage] = sources.get(bs.bid_stage, 0) + 1
            results.append({
                "bid_no": bs.bid_no,
                "title": bs.title,
                "agency": bs.agency,
                "budget": bs.budget,
                "deadline": bs.deadline,
                "d_day": bs.d_day,
                "score": bs.score,
                "role_keywords": bs.role_keywords_matched,
                "domain_keywords": bs.domain_keywords_matched,
                "classification": bs.classification,
                "classification_large": bs.classification_large,
                "bid_stage": bs.bid_stage,
            })
            if len(results) >= max_results:
                break

        logger.info(
            f"스코어링 완료: {total_fetched}건 → 통과 {len(scored)}건 → "
            f"최종 {len(results)}건 (공고:{sources['입찰공고']} 사전:{sources['사전규격']} 계획:{sources['발주계획']})"
        )
        return {"total_fetched": total_fetched, "sources": sources, "data": results}

    async def fetch_bids_by_preset(self, preset: SearchPreset) -> list[BidAnnouncement]:
        """
        프리셋 기반 공고 수집 (v2: 전수 수집 + 스코어링).

        1. fetch_all_bids() — 당일 전체 공고 수집
        2. bid_scorer 적합도 스코어링
        3. 프리셋 필터 (min_budget, min_days_remaining, bid_types) 적용
        4. BidAnnouncement 정규화 + DB upsert
        """
        from app.services.bid_scorer import score_and_rank_bids

        today = date.today()
        date_from = today.strftime("%Y%m%d") + "0000"
        date_to = today.strftime("%Y%m%d") + "2359"
        logger.info(f"당일 전수 수집: {date_from} ~ {date_to}")

        # 1) 전수 수집
        all_raw = await self.g2b.fetch_all_bids(date_from, date_to)

        # 2) 스코어링 (역할 키워드 필수 매칭)
        scored = score_and_rank_bids(
            all_raw,
            reference_date=today,
            min_score=0,
            exclude_expired=True,
            max_results=200,
        )

        # 3) 프리셋 필터 + 정규화
        filtered: list[BidAnnouncement] = []
        for bs in scored:
            bid = self._normalize(bs.raw)
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
            logger.info("스코어링 후 프리셋 필터 통과 공고 없음")
            return []

        # 공고 상세(자격요건) 수집
        for bid in filtered:
            bid = await self._enrich_detail(bid)

        # Supabase upsert
        await self._upsert_announcements(filtered)

        logger.info(
            f"공고 수집 완료: {len(all_raw)}건 전수 → {len(scored)}건 스코어 → {len(filtered)}건 최종"
        )
        return filtered

    async def fetch_pre_bids_by_preset(self, preset: SearchPreset) -> list[BidAnnouncement]:
        """
        사전규격 공개 수집.

        G2B 사전규격 API를 호출하여 입찰 전 단계의 공고를 수집한다.
        bid_announcements 테이블에 bid_stage='사전공고'로 저장.
        """
        raw_bids: dict[str, dict] = {}

        for keyword in preset.keywords:
            try:
                results = await self.g2b.search_pre_bid_specifications(
                    keyword, num_of_rows=self.NUM_OF_ROWS,
                )
                for item in results:
                    bid_no = (
                        item.get("bfSpecRgstNo")
                        or item.get("prcSpcfNo")
                        or ""
                    ).strip()
                    if bid_no and bid_no not in raw_bids:
                        raw_bids[bid_no] = item
            except Exception as e:
                logger.warning(f"사전규격 '{keyword}' 수집 실패 (계속 진행): {e}")

        filtered: list[BidAnnouncement] = []
        today = date.today()

        for raw in raw_bids.values():
            bid = self._normalize_pre_spec(raw)
            if bid is None:
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
            logger.info("사전규격 수집 후 필터 통과 없음")
            return []

        await self._upsert_announcements(filtered)
        logger.info(f"사전규격 수집 완료: {len(filtered)}건 (키워드: {preset.keywords})")
        return filtered

    def _normalize_pre_spec(self, raw: dict) -> Optional[BidAnnouncement]:
        """사전규격 API 응답 → BidAnnouncement 변환

        BfSpecRgstInfoService 응답 필드:
        - bfSpecRgstNo: 사전규격 등록번호
        - bfSpecRgstNm: 사전규격 등록명
        - orderInsttNm / rlDminsttNm: 발주기관
        - asignBdgtAmt: 배정예산액
        - opninRgstClseDt / bfSpecRgstClseDt: 의견등록 마감일
        - rgstDt: 등록일
        """
        try:
            bid_no = (raw.get("bfSpecRgstNo") or raw.get("prcSpcfNo") or "").strip()
            bid_title = (raw.get("bfSpecRgstNm") or raw.get("prcSpcfNm") or "").strip()
            agency = (raw.get("orderInsttNm") or raw.get("rlDminsttNm") or "").strip()
            if not bid_no or not bid_title:
                return None

            budget_amount: Optional[int] = None
            raw_budget = raw.get("asignBdgtAmt") or raw.get("presmptPrce")
            if raw_budget:
                try:
                    budget_amount = int(float(str(raw_budget).replace(",", "")))
                except (ValueError, TypeError):
                    pass

            # 사전규격 의견등록 마감일 (bfSpecRgstClseDt)
            deadline_date: Optional[datetime] = None
            raw_deadline = raw.get("bfSpecRgstClseDt") or raw.get("opninRgstClseDt")
            if raw_deadline:
                for fmt in ("%Y/%m/%d %H:%M:%S", "%Y%m%d%H%M%S", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        deadline_date = datetime.strptime(str(raw_deadline).strip(), fmt)
                        deadline_date = deadline_date.replace(tzinfo=timezone.utc)
                        break
                    except ValueError:
                        continue

            days_remaining: Optional[int] = None
            if deadline_date:
                days_remaining = (deadline_date.date() - date.today()).days

            announce_date = None
            raw_announce = raw.get("rgstDt") or raw.get("prcSpcfRgstDt")
            if raw_announce and len(str(raw_announce)) >= 8:
                try:
                    announce_date = date.fromisoformat(str(raw_announce)[:10].replace("/", "-"))
                except ValueError:
                    pass

            return BidAnnouncement(
                bid_no=f"PRE-{bid_no}",
                bid_title=f"[사전규격] {bid_title}",
                agency=agency,
                bid_type="용역",
                budget_amount=budget_amount,
                announce_date=announce_date,
                deadline_date=deadline_date,
                days_remaining=days_remaining,
                content_text=raw.get("prcSpcfCn"),
                qualification_available=False,
            )
        except Exception as e:
            logger.warning(f"사전규격 정규화 실패: {e} | raw={raw.get('prcSpcfNo')}")
            return None

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
