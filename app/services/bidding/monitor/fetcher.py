"""
입찰 공고 수집 서비스

G2BService 래퍼 + 후처리 필터 + Supabase upsert.
새 API 연동 코드를 작성하지 않고 G2BService를 내부적으로 사용한다.
"""

import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Optional

import aiohttp

from app.models.bid_schemas import BidAnnouncement, SearchPreset
from app.services.g2b_service import G2BService

logger = logging.getLogger(__name__)

# ── 보안 및 성능 설정 ────────────────────────────────
_QUALIFICATION_UNAVAILABLE_PHRASES = ("첨부파일 참조", "붙임 참조", "별첨 참조", "입찰공고문 참조")

# 문서 다운로드 제한
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50MB
MAX_TEXT_LENGTH = 100_000  # 100KB (content_text 저장)
MAX_CONTENT_TEXT = 100_000  # 100KB 전체 제한

# SSRF 차단 - 내부 IP 패턴
BLOCKED_IP_PATTERNS = ['localhost', '127.', '192.168.', '10.', '169.254.']

# 타임아웃 설정
DOCUMENT_DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(
    total=15,      # 전체 15초
    connect=5,     # 연결 5초
    sock_read=10,  # 읽기 10초
)

# 병렬 처리 설정
ENRICH_SEMAPHORE_COUNT = 5  # 동시 최대 5개


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
        3소스 전수 수집 + 적합도 스코어링 파이프라인 (v4: 중복 제거).

        1. 기존 bid_no 조회 (중복 방지)
        2. 입찰공고 + 사전규격 + 발주계획 병렬 수집
        3. 신규 공고만 필터링
        4. 정규화 → 공통 형식으로 합산
        5. bid_scorer.score_and_rank_bids() 스코어링
        6. 후처리 필터 + sources 집계

        Returns:
            {"total_fetched": int, "new_fetched": int, "sources": {...}, "data": [...]}
        """
        from app.services.bidding.monitor.scorer import (
            normalize_plan_for_scoring,
            normalize_pre_spec_for_scoring,
            score_and_rank_bids,
        )

        today = date.today()
        if not date_to:
            date_to = today.strftime("%Y%m%d") + "2359"
        if not date_from:
            date_from = today.strftime("%Y%m%d") + "0000"

        # NEW: 기존 bid_no 조회
        existing_bid_nos = await self._get_existing_bid_nos()
        logger.info(f"스코어링: 기존 {len(existing_bid_nos)}건 제외")

        # 1) 3소스 병렬 수집 (개별 실패 허용)
        all_bids, all_pre, all_plans = await asyncio.gather(
            self.g2b.fetch_all_bids(date_from, date_to),
            self.g2b.fetch_all_pre_specs(date_from, date_to),
            self.g2b.fetch_all_procurement_plans(date_from, date_to),
            return_exceptions=True,
        )

        if isinstance(all_bids, BaseException):
            logger.warning(f"입찰공고 수집 실패 ({type(all_bids).__name__}): {all_bids}")
            all_bids = []
        if isinstance(all_pre, BaseException):
            logger.warning(f"사전규격 수집 실패 ({type(all_pre).__name__}): {all_pre}")
            all_pre = []
        if isinstance(all_plans, BaseException):
            logger.warning(f"발주계획 수집 실패 ({type(all_plans).__name__}): {all_plans}")
            all_plans = []

        # NEW: 기존 공고 필터링
        all_bids = [b for b in all_bids if b.get("bidNtceNo", "").strip() not in existing_bid_nos]
        all_pre = [b for b in all_pre if (b.get("bfSpecRgstNo") or b.get("prcSpcfNo") or "").strip() not in existing_bid_nos]
        all_plans = [b for b in all_plans if (b.get("orderPlanNo") or b.get("bidNtceNo") or "").strip() not in existing_bid_nos]

        total_fetched = len(all_bids) + len(all_pre) + len(all_plans)

        # 2) 정규화 + 합산
        combined = list(all_bids)
        combined.extend(normalize_pre_spec_for_scoring(r) for r in all_pre)
        combined.extend(normalize_plan_for_scoring(r) for r in all_plans)

        logger.info(
            f"전수 수집: 공고 {len(all_bids)} + 사전규격 {len(all_pre)} + "
            f"발주계획 {len(all_plans)} = {total_fetched}건 신규 ({date_from}~{date_to})"
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
            f"스코어링 완료: {total_fetched}건 신규 → 통과 {len(scored)}건 → "
            f"최종 {len(results)}건 (공고:{sources['입찰공고']} 사전:{sources['사전규격']} 계획:{sources['발주계획']})"
        )
        return {
            "total_fetched": total_fetched,
            "new_fetched": total_fetched,
            "sources": sources,
            "data": results
        }

    async def fetch_bids_by_preset(self, preset: SearchPreset) -> list[BidAnnouncement]:
        """
        프리셋 기반 공고 수집 (v4: 중복 제거 + 첨부파일 + 병렬 처리).

        1. 기존 bid_no 목록 조회 (중복 방지)
        2. fetch_all_bids() — 당일 전체 공고 수집
        3. 새로운 공고만 필터링 (deduplication)
        4. bid_scorer 적합도 스코어링
        5. 프리셋 필터 (min_budget, min_days_remaining, bid_types) 적용
        6. 첨부파일 다운로드 및 내용 추출 — 병렬 처리 (SEMAPHORE 활용)
        7. BidAnnouncement 정규화 + DB upsert
        """
        from app.services.bidding.monitor.scorer import score_and_rank_bids

        today = date.today()
        date_from = today.strftime("%Y%m%d") + "0000"
        date_to = today.strftime("%Y%m%d") + "2359"

        # Step 1: 기존 bid_no 목록 조회 (중복 방지)
        existing_bid_nos = await self._get_existing_bid_nos()
        logger.info(f"기존 공고 {len(existing_bid_nos)}건 로드 (중복 제거 준비)")

        logger.info(f"당일 전수 수집: {date_from} ~ {date_to}")

        # Step 2: 전수 수집
        all_raw = await self.g2b.fetch_all_bids(date_from, date_to)

        # Step 3: 기존 공고 필터링 (새로운 것만 선택)
        new_raw = [bid for bid in all_raw if bid.get("bidNtceNo", "").strip() not in existing_bid_nos]
        logger.info(
            f"Dedup: 전체 {len(all_raw)}건 → 신규 {len(new_raw)}건 "
            f"(기존 {len(all_raw) - len(new_raw)}건 스킵)"
        )

        if not new_raw:
            logger.info("신규 공고가 없습니다 (모두 기존 공고)")
            return []

        # Step 4: 스코어링 (신규 공고만)
        scored = score_and_rank_bids(
            new_raw,
            reference_date=today,
            min_score=0,
            exclude_expired=True,
            max_results=200,
        )

        # Step 5: 프리셋 필터 + 정규화
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

        # Step 6: 공고 상세(자격요건) + 첨부파일 수집 — 병렬 처리
        logger.info(f"병렬 처리 시작: {len(filtered)}건 공고 상세 및 첨부파일 수집")

        # Semaphore로 동시 요청 제한 (G2B 서버 부하 방지)
        semaphore = asyncio.Semaphore(ENRICH_SEMAPHORE_COUNT)

        async def enrich_and_download(bid: BidAnnouncement) -> BidAnnouncement:
            """공고 상세 수집 + 첨부파일 다운로드 (Semaphore 제한)"""
            async with semaphore:
                try:
                    # 상세내용 수집
                    bid = await self._enrich_detail(bid)

                    # 신규 공고에 대해서만 첨부파일 다운로드
                    if bid.bid_no not in existing_bid_nos:
                        try:
                            detail = await self.g2b.get_bid_detail(bid.bid_no)
                            attachments = await self._download_bid_attachments(bid.bid_no, detail)

                            # 첨부파일 내용을 content_text에 추가 (길이 제한)
                            if attachments:
                                doc_content = bid.content_text or ""

                                if attachments.get("rfp_content"):
                                    rfp_text = attachments["rfp_content"][:5000]
                                    doc_content += f"\n\n=== [RFP 분석] ({len(rfp_text)}자) ===\n{rfp_text}"

                                if attachments.get("notice_content"):
                                    notice_text = attachments["notice_content"][:3000]
                                    doc_content += f"\n\n=== [공고문] ({len(notice_text)}자) ===\n{notice_text}"

                                if attachments.get("instruction_content"):
                                    instruction_text = attachments["instruction_content"][:3000]
                                    doc_content += f"\n\n=== [과업지시서] ({len(instruction_text)}자) ===\n{instruction_text}"

                                # HIGH #5: DB 컬럼 오버플로우 방지
                                bid.content_text = doc_content[:MAX_CONTENT_TEXT]
                                logger.info(f"[{bid.bid_no}] 첨부파일 다운로드 완료 ({len(bid.content_text)}자)")
                        except Exception as e:
                            logger.warning(f"[{bid.bid_no}] 첨부파일 수집 실패 (계속 진행): {e}")

                    return bid

                except Exception as e:
                    logger.error(f"[{bid.bid_no}] 상세 수집 실패: {e}")
                    return bid

        # 모든 공고를 병렬로 처리
        enriched_bids = await asyncio.gather(
            *[enrich_and_download(bid) for bid in filtered],
            return_exceptions=False
        )

        # 실패한 항목 필터링
        enriched_bids = [bid for bid in enriched_bids if isinstance(bid, BidAnnouncement)]

        logger.info(f"병렬 처리 완료: {len(enriched_bids)}건 완료")

        # Step 7: Supabase upsert
        await self._upsert_announcements(enriched_bids)

        logger.info(
            f"공고 수집 완료: {len(all_raw)}건 전수 → {len(new_raw)}건 신규 → "
            f"{len(scored)}건 스코어 → {len(enriched_bids)}건 최종"
        )
        return enriched_bids

    async def fetch_pre_bids_by_preset(self, preset: SearchPreset) -> list[BidAnnouncement]:
        """
        사전규격 공개 수집 (v2: 중복 제거).

        G2B 사전규격 API를 호출하여 입찰 전 단계의 공고를 수집한다.
        bid_announcements 테이블에 bid_stage='사전공고'로 저장.
        기존 공고는 스킵 (deduplication).
        """
        # Step 1: 기존 bid_no 목록 조회
        existing_bid_nos = await self._get_existing_bid_nos()
        logger.info(f"사전규격 수집: 기존 {len(existing_bid_nos)}건 제외")

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

                    # NEW: 기존 bid_no는 스킵
                    if bid_no and bid_no not in existing_bid_nos and bid_no not in raw_bids:
                        raw_bids[bid_no] = item
            except Exception as e:
                logger.warning(f"사전규격 '{keyword}' 수집 실패 ({type(e).__name__}), 계속 진행: {e}")

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
        logger.info(
            f"사전규격 수집 완료: {len(raw_bids)}건 신규 → {len(filtered)}건 최종 "
            f"(키워드: {preset.keywords})"
        )
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
            # dminsttNm(수요기관=실제 발주처)을 우선 사용.
            # ntceInsttNm(공고기관)은 조달청 등 대행기관인 경우가 많아 발주처와 다름.
            agency = (raw.get("dminsttNm") or raw.get("ntceInsttNm") or "").strip()
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
            logger.warning(f"상세 수집 실패 ({type(e).__name__}): bid_no={bid.bid_no} | {e}")
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

    async def _get_existing_bid_nos(self) -> set[str]:
        """
        Supabase bid_announcements 테이블에서 이미 수집된 bid_no 목록 조회.
        
        Returns:
            기존 bid_no 집합 (중복 방지용)
        """
        try:
            result = await self.db.table("bid_announcements")\
                .select("bid_no")\
                .execute()
            return {row["bid_no"] for row in (result.data or [])}
        except Exception as e:
            logger.warning(f"기존 bid_no 조회 실패 ({type(e).__name__}), 계속 진행: {e}")
            return set()

    async def _download_bid_attachments(self, bid_no: str, detail: dict) -> dict[str, str]:
        """
        G2B 공고 상세에서 첨부파일(RFP, 공고문, 과업지시서) 다운로드.
        
        파일명 분류 개선:
        - Content-Disposition 헤더 우선 사용
        - URL percent-encoding 디코딩
        - 한글/영문 키워드 모두 매칭
        
        Args:
            bid_no: 공고번호
            detail: G2B get_bid_detail() 응답
            
        Returns:
            {
                "rfp_content": "...",  # RFP 파일 내용
                "notice_content": "...", # 공고문 내용
                "instruction_content": "..." # 과업지시서 내용
            }
        """

        attachments = {}

        try:
            # G2B API 응답에서 첨부파일 URL 추출
            # ntceSpecDocUrl1-5: 규격서, 공고문 등
            for i in range(1, 6):
                url = detail.get(f"ntceSpecDocUrl{i}", "")
                if not url:
                    continue

                try:
                    # 파일명 추출 및 분류
                    filename = self._extract_and_classify_filename(url)

                    if not filename or not filename.get("type"):
                        logger.debug(f"[{bid_no}] 파일 {i} 분류 실패: {url[:50]}")
                        continue

                    content = await self._fetch_document_content(url)

                    if not content:
                        logger.debug(f"[{bid_no}] 파일 {i} 다운로드 실패: {url[:50]}")
                        continue

                    # 파일 타입별로 저장 (중복 방지)
                    file_type = filename["type"]
                    if file_type not in attachments:
                        attachments[file_type] = content
                        logger.debug(f"[{bid_no}] 파일 다운로드 완료: {filename['name']} ({file_type})")
                    else:
                        logger.debug(f"[{bid_no}] {file_type} 이미 존재, 스킵: {filename['name']}")

                except Exception as e:
                    logger.debug(f"[{bid_no}] 첨부파일 {i} 처리 실패: {e}")
                    continue

        except Exception as e:
            logger.warning(f"[{bid_no}] 첨부파일 수집 실패 ({type(e).__name__}): {e}")

        return attachments

    def _extract_and_classify_filename(self, url: str) -> Optional[dict]:
        """
        파일명을 추출하고 분류 (RFP/공고문/과업지시서).
        
        Priority:
        1. Content-Disposition 헤더 (응답 수신 시 확인, 현재는 URL만 사용)
        2. URL percent-decoding
        3. 파일명 키워드 매칭 (한글/영문)
        
        Returns:
            {"name": "파일명", "type": "rfp_content|notice_content|instruction_content"}
            또는 None (분류 불가)
        """
        from urllib.parse import unquote

        try:
            # URL에서 파일명 추출 및 디코딩
            encoded_filename = url.split("/")[-1]
            filename = unquote(encoded_filename).lower()

            if not filename:
                return None

            # RFP 문서 분류
            rfp_keywords = ["rfp", "제안", "입찰", "요청서", "공동", "proposal"]
            if any(kw in filename for kw in rfp_keywords):
                return {"name": filename, "type": "rfp_content"}

            # 공고문 분류
            notice_keywords = ["공고", "notice", "announcement", "bid"]
            if any(kw in filename for kw in notice_keywords):
                return {"name": filename, "type": "notice_content"}

            # 과업지시서 분류
            instruction_keywords = ["지시", "instruction", "task", "job", "과업", "업무"]
            if any(kw in filename for kw in instruction_keywords):
                return {"name": filename, "type": "instruction_content"}

            # 기본값: 첫 파일은 RFP로 간주 (대부분의 경우)
            logger.debug(f"파일명 분류 불확실, RFP로 간주: {filename}")
            return {"name": filename, "type": "rfp_content"}

        except Exception as e:
            logger.debug(f"파일명 분류 실패: {e}")
            return None

    async def _fetch_document_content(self, url: str) -> Optional[str]:
        """
        문서 URL에서 내용 다운로드 (PDF/텍스트 지원).
        
        보안 및 성능 대책:
        - SSRF 방지: URL 검증, 내부 IP 차단
        - DoS 방지: 파일 크기 제한, 청크 단위 읽기
        - 메모리 효율: 텍스트 길이 제한
        
        Args:
            url: 문서 URL
            
        Returns:
            문서 텍스트 내용 또는 None
        """
        from urllib.parse import urlparse

        try:
            # Step 1: URL 검증 (SSRF 방지)
            parsed = urlparse(url)

            # 프로토콜 검증
            if parsed.scheme not in ('http', 'https'):
                logger.warning(f"유효하지 않은 URL 스키마: {parsed.scheme} | {url}")
                return None

            # 호스트명 검증
            hostname = parsed.hostname
            if not hostname:
                logger.warning(f"호스트명 추출 실패: {url}")
                return None

            # 내부 IP 차단
            if any(hostname.startswith(pattern) for pattern in BLOCKED_IP_PATTERNS):
                logger.warning(f"내부 IP 접근 차단: {hostname} | {url}")
                return None

            # Step 2: 문서 다운로드 (타임아웃 + 크기 제한)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=DOCUMENT_DOWNLOAD_TIMEOUT) as resp:
                    if resp.status != 200:
                        logger.warning(f"문서 다운로드 실패: {url} (상태: {resp.status})")
                        return None

                    # Content-Length 확인 (DoS 방지)
                    content_length = int(resp.headers.get('content-length', 0))
                    if content_length > MAX_DOCUMENT_SIZE:
                        logger.warning(f"파일 크기 초과: {content_length} bytes > {MAX_DOCUMENT_SIZE} | {url}")
                        return None

                    # 청크 단위 읽기 (메모리 효율)
                    chunks = []
                    total_size = 0
                    chunk_size = 1024 * 1024  # 1MB

                    async for chunk in resp.content.iter_chunked(chunk_size):
                        total_size += len(chunk)
                        if total_size > MAX_DOCUMENT_SIZE:
                            logger.warning(f"파일 크기 초과 중단: {total_size} bytes > {MAX_DOCUMENT_SIZE}")
                            return None
                        chunks.append(chunk)

                    content = b''.join(chunks)

                    # Step 3: PDF 또는 텍스트 파일 처리
                    if content.startswith(b"%PDF"):
                        # PDF → 텍스트 추출
                        try:
                            import PyPDF2
                            from io import BytesIO

                            pdf = PyPDF2.PdfReader(BytesIO(content))
                            text = ""

                            # 메모리 누수 방지: 텍스트 길이 제한
                            for page in pdf.pages:
                                if len(text) >= MAX_TEXT_LENGTH:
                                    logger.info(f"PDF 텍스트 길이 초과: {len(text)} chars에서 중단 | {url}")
                                    break

                                try:
                                    page_text = page.extract_text()
                                    if page_text:
                                        text += page_text + "\n"
                                except Exception as e:
                                    logger.debug(f"PDF 페이지 추출 실패: {e}")
                                    continue

                            return text[:MAX_TEXT_LENGTH] if text.strip() else None

                        except ImportError:
                            logger.warning(f"PyPDF2 미설치 - PDF 파싱 불가: {url}")
                            return None
                        except Exception as e:
                            logger.debug(f"PDF 파싱 실패: {e}")
                            return None
                    else:
                        # 텍스트 파일 직접 반환 (길이 제한)
                        try:
                            text = content.decode("utf-8", errors="ignore")
                            return text[:MAX_TEXT_LENGTH] if text.strip() else None
                        except Exception as e:
                            logger.debug(f"텍스트 디코딩 실패: {e}")
                            return None

        except asyncio.TimeoutError:
            logger.warning(f"문서 다운로드 타임아웃: {url}")
            return None
        except Exception as e:
            logger.warning(f"문서 다운로드 오류 ({type(e).__name__}): {url} | {e}")
            return None

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
