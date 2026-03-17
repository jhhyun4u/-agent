"""
나라장터 Open API 연동 서비스

4단계 경쟁사 분석:
1. getBidPblancListInfoServc  — 유사 입찰공고 검색
2. getBidResultListInfo       — 낙찰결과 조회 (낙찰업체명, 낙찰금액)
3. getCmpnyBidInfoServc       — 업체별 수주이력
4. CompetitorProfile 생성    — Phase 2 LLM 전달

Rate Limit: 공공 API 초당 10건 → asyncio.sleep(0.1) + exponential backoff
캐싱: Supabase g2b_cache 테이블 (SHA256 해시 키, 24h TTL)
"""

import asyncio
import hashlib
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/1230000"

# 서비스별 경로 prefix (공고=/ad, 낙찰=/as)
SERVICE_PREFIX = {
    "BidPublicInfoService": "ad",
    "ScsbidInfoService": "as",
    "ContractInfoService": "ac",
}


# ─────────────────────────────────────────────
# 데이터 클래스
# ─────────────────────────────────────────────

@dataclass
class G2BContract:
    """나라장터 계약 정보"""
    contract_id: str
    title: str
    agency: str
    contractor: str
    contract_date: str
    contract_amount: int
    category: str
    description: str
    similarity_score: float = 0.0


@dataclass
class CompetitorProfile:
    """경쟁사 프로필"""
    company_name: str
    contract_history: List[G2BContract]
    specialization_areas: List[str]
    avg_contract_amount: int
    success_rate: float
    market_share: float
    strength_score: float
    weakness_score: float


# ─────────────────────────────────────────────
# 캐시 헬퍼
# ─────────────────────────────────────────────

def _cache_key(api_type: str, params: dict) -> str:
    raw = api_type + json.dumps(sorted(params.items()))
    return hashlib.sha256(raw.encode()).hexdigest()


async def _get_cache(key: str) -> Optional[List]:
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("g2b_cache")
            .select("response")
            .eq("query_hash", key)
            .gt("expires_at", datetime.now(timezone.utc).isoformat())
            .single()
            .execute()
        )
        if result.data:
            return result.data.get("response")
    except Exception:
        pass
    return None


async def _set_cache(key: str, endpoint: str, params: dict, data: List) -> None:
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        await (
            client.table("g2b_cache")
            .upsert({
                "query_hash": key,
                "endpoint": endpoint,
                "response": data,
                "expires_at": expires,
            })
            .execute()
        )
    except Exception as e:
        logger.warning(f"캐시 저장 실패 (무시): {e}")


# ─────────────────────────────────────────────
# G2BService
# ─────────────────────────────────────────────

class G2BService:
    """나라장터 Open API 연동 서비스"""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = BASE_URL

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

    # ── 공통 API 호출 ──────────────────────────────

    async def _call_api(self, endpoint: str, params: dict) -> List[Dict]:
        """나라장터 API 호출 (Rate Limit + Retry + 캐시)"""
        cache_key = _cache_key(endpoint, params)
        cached = await _get_cache(cache_key)
        if cached is not None:
            logger.debug(f"G2B 캐시 HIT: {endpoint}")
            return cached

        api_key = settings.g2b_api_key
        if not api_key:
            raise RuntimeError("G2B_API_KEY가 설정되지 않았습니다.")

        # serviceKey를 URL에 직접 삽입 (인코딩 불필요한 hex 키)
        # endpoint에서 서비스명 추출 → prefix 결정
        svc_name = endpoint.split("/")[0]
        prefix = SERVICE_PREFIX.get(svc_name, "ad")
        url = f"{self.base_url}/{prefix}/{endpoint}?serviceKey={api_key}"
        # type=json을 params에 포함
        params = {**params, "type": "json"}

        for attempt in range(3):
            await asyncio.sleep(0.1)  # 기본 Rate Limit 간격
            try:
                async with self.session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 429:
                        wait = 2 ** attempt
                        logger.warning(f"G2B Rate Limit — {wait}초 대기")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json(content_type=None)
                    # 응답 구조: {"response": ...} 또는 {"nkoneps...": ...}
                    result = data.get("response", {})
                    if not result:
                        for k, v in data.items():
                            if isinstance(v, dict) and "header" in v:
                                result = v
                                break
                    header = result.get("header", {})
                    if header.get("resultCode") != "00":
                        raise RuntimeError(f"G2B API 오류: {header.get('resultMsg')}")
                    items = result.get("body", {}).get("items") or []
                    # items가 list일 수도, dict일 수도 있음
                    if isinstance(items, list):
                        rows = items
                    else:
                        raw = items.get("item", [])
                        rows = raw if isinstance(raw, list) else [raw]
                    await _set_cache(cache_key, endpoint, params, rows)
                    return rows
            except RuntimeError:
                raise
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"G2B API 호출 실패: {endpoint}")

    # ── 1단계: 입찰공고 검색 ─────────────────────────

    async def search_bid_announcements(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict]:
        """
        입찰공고 목록 검색 (getBidPblancListInfoServc)

        Args:
            keyword: 검색 키워드 (클라이언트 측 제목 필터링)
            date_from: 조회시작일시 (YYYYMMDDHHMM). 미지정 시 최근 14일
            date_to: 조회종료일시 (YYYYMMDDHHMM). 미지정 시 현재

        Returns:
            나라장터 입찰공고 raw 목록 (keyword로 제목 필터링 적용)
        """
        # 기본 날짜 범위: 최근 14일 (API 최대 21일)
        if not date_to:
            date_to = datetime.now().strftime("%Y%m%d") + "2359"
        if not date_from:
            date_from = (datetime.now() - timedelta(days=14)).strftime("%Y%m%d") + "0000"

        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": "1",
            "inqryBgnDt": date_from,
            "inqryEndDt": date_to,
        }

        results = await self._call_api(
            "BidPublicInfoService/getBidPblancListInfoServc",
            params,
        )

        # 서버 측 키워드 필터가 미작동 → 클라이언트 측 제목 필터링
        if keyword:
            kw_lower = keyword.lower()
            results = [r for r in results if kw_lower in r.get("bidNtceNm", "").lower()]

        return results

    async def get_bid_detail(self, bid_no: str) -> Dict:
        """
        입찰공고 상세 조회

        자격요건 포함 공고 규격 내용(ntceSpecCn)을 확보하기 위해 사용.

        Returns:
            상세 정보 dict (없으면 빈 dict)
        """
        # 상세 조회: bidNtceNo로 검색 (날짜 범위 최대 14일)
        results = await self._call_api(
            "BidPublicInfoService/getBidPblancListInfoServc",
            {"bidNtceNo": bid_no, "inqryDiv": "2",
             "inqryBgnDt": (datetime.now() - timedelta(days=14)).strftime("%Y%m%d") + "0000",
             "inqryEndDt": datetime.now().strftime("%Y%m%d") + "2359",
             "numOfRows": "10", "pageNo": "1"},
        )
        return results[0] if results else {}

    # ── 2단계: 낙찰결과 조회 ─────────────────────────

    async def get_bid_results(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1,
        date_range_days: int = 30,
    ) -> List[Dict]:
        """
        낙찰결과 목록 조회 (ScsbidInfoService/getScsbidListSttusServc)
        낙찰업체명(bidwinnrNm), 참여업체수(prtcptCnum) 포함

        Returns:
            낙찰결과 raw 목록
        """
        end_dt = datetime.now()
        bgn_dt = end_dt - timedelta(days=date_range_days)
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": "1",
            "inqryBgnDt": bgn_dt.strftime("%Y%m%d") + "0000",
            "inqryEndDt": end_dt.strftime("%Y%m%d") + "2359",
            "bidNtceNm": keyword,
        }
        return await self._call_api(
            "ScsbidInfoService/getScsbidListSttusServc",
            params,
        )

    # ── 3단계: 계약결과 조회 ─────────────────────────

    async def get_contract_results(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1,
        date_range_days: int = 30,
    ) -> List[Dict]:
        """
        계약결과 목록 조회 (ContractInfoService)

        Returns:
            계약결과 raw 목록
        """
        end_dt = datetime.now()
        bgn_dt = end_dt - timedelta(days=date_range_days)
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": "1",
            "inqryBgnDt": bgn_dt.strftime("%Y%m%d") + "0000",
            "inqryEndDt": end_dt.strftime("%Y%m%d") + "2359",
            "cntrctNm": keyword,
        }
        return await self._call_api(
            "ContractInfoService/getContractResultListInfo",
            params,
        )

    # ── 4단계: 업체 입찰이력 조회 ───────────────────────

    async def get_company_bid_history(
        self,
        company_name: str,
        num_of_rows: int = 20,
        page_no: int = 1,
        date_range_days: int = 7,
    ) -> List[Dict]:
        """
        업체별 입찰이력 조회 — 낙찰정보에서 업체명 검색

        Args:
            company_name: 업체명

        Returns:
            업체 입찰이력 raw 목록
        """
        end_dt = datetime.now()
        bgn_dt = end_dt - timedelta(days=date_range_days)
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "inqryDiv": "1",
            "inqryBgnDt": bgn_dt.strftime("%Y%m%d") + "0000",
            "inqryEndDt": end_dt.strftime("%Y%m%d") + "2359",
            "bidwinnrNm": company_name,
        }
        return await self._call_api(
            "ScsbidInfoService/getScsbidListSttusServc",
            params,
        )

    # ── 통합: 경쟁사 분석 ────────────────────────────

    async def search_competitors(
        self,
        rfp_title: str,
        date_range_months: int = 24,
        max_competitors: int = 10,
    ) -> Dict[str, Any]:
        """
        경쟁사 통합 분석 (4단계 파이프라인)

        1. 유사 입찰공고 검색
        2. 낙찰결과에서 낙찰업체 추출
        3. 주요 업체 수주이력 조회
        4. CompetitorProfile 생성

        Returns:
            경쟁사 분석 결과 dict
        """
        # 날짜 범위 (YYYYMMDDHHMM 포맷)
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=date_range_months * 30)
        date_from = start_dt.strftime("%Y%m%d") + "0000"
        date_to = end_dt.strftime("%Y%m%d") + "2359"

        keyword = self._extract_main_keyword(rfp_title)
        logger.info(f"G2B 경쟁사 분석 시작: keyword={keyword}")

        # Step 1: 유사 입찰공고 검색 (최근 14일, API 날짜 범위 제한)
        try:
            bid_list = await self.search_bid_announcements(
                keyword, num_of_rows=50
            )
        except Exception as e:
            logger.warning(f"입찰공고 검색 실패: {e}")
            bid_list = []

        # Step 2: 낙찰결과에서 업체명 추출 (최근 7일)
        try:
            bid_results = await self.get_bid_results(
                keyword, num_of_rows=50, date_range_days=7
            )
        except Exception as e:
            logger.warning(f"낙찰결과 조회 실패: {e}")
            bid_results = []

        # 낙찰업체 빈도 집계
        winner_counter: Counter = Counter()
        winner_amounts: Dict[str, List[int]] = {}
        for row in bid_results:
            company = (row.get("bidwinnrNm") or row.get("sucsfBidderNm")
                       or row.get("cmpnyNm", ""))
            amount_str = (row.get("sucsfBidAmt") or row.get("bidAmt")
                         or row.get("presmptPrce", "0"))
            if company:
                winner_counter[company] += 1
                try:
                    amt = int(str(amount_str).replace(",", "").strip() or 0)
                except (ValueError, TypeError):
                    amt = 0
                winner_amounts.setdefault(company, []).append(amt)

        # 상위 업체 선정
        top_companies = [c for c, _ in winner_counter.most_common(max_competitors)]

        # Step 3: 주요 업체 수주이력 조회 (상위 5개만)
        company_histories: Dict[str, List[Dict]] = {}
        for company in top_companies[:5]:
            try:
                history = await self.get_company_bid_history(company, num_of_rows=10)
                company_histories[company] = history
            except Exception as e:
                logger.warning(f"업체이력 조회 실패({company}): {e}")
                company_histories[company] = []

        # Step 4: CompetitorProfile 생성
        profiles = []
        total_market = sum(
            sum(amts) for amts in winner_amounts.values()
        ) or 1

        for company in top_companies:
            amts = winner_amounts.get(company, [0])
            avg_amt = int(sum(amts) / len(amts)) if amts else 0
            market_share = round(sum(amts) / total_market, 4)
            win_count = winner_counter[company]
            strength = min(0.5 + win_count * 0.08 + min(avg_amt / 5e8 * 0.1, 0.1), 0.95)

            profiles.append({
                "company_name": company,
                "win_count": win_count,
                "avg_contract_amount": avg_amt,
                "market_share": market_share,
                "strength_score": round(strength, 3),
                "weakness_score": round(1 - strength, 3),
                "bid_history_count": len(company_histories.get(company, [])),
            })

        return {
            "keyword": keyword,
            "rfp_title": rfp_title,
            "bid_announcements_found": len(bid_list),
            "bid_results_found": len(bid_results),
            "competitors": profiles,
            "total_competitors": len(profiles),
            "date_range": {"from": start_dt.date().isoformat(), "to": end_dt.date().isoformat()},
        }

    # ── 다중 키워드 검색 ──────────────────────────────

    async def search_multi_keyword(
        self,
        keywords: list[str],
        num_of_rows: int = 999,
        date_range_days: int = 14,
    ) -> list[dict]:
        """
        다중 키워드로 공고 검색 후 OR 매칭 + 중복 제거.

        전체 공고를 조회한 뒤 클라이언트 측에서 키워드 매칭.
        각 공고에 matched_keywords, match_count 필드를 추가.

        Args:
            keywords: 매칭할 키워드 목록
            num_of_rows: 조회 건수 (기본 999)
            date_range_days: 조회 기간 일수 (기본 14)

        Returns:
            매칭된 공고 목록 (match_count 내림차순)
        """
        all_bids = await self.search_bid_announcements(
            keyword="",
            num_of_rows=num_of_rows,
            date_from=(datetime.now() - timedelta(days=date_range_days)).strftime("%Y%m%d") + "0000",
        )

        # 중복 제거 (공고번호 기준)
        seen = set()
        unique_bids = []
        for bid in all_bids:
            bid_no = bid.get("bidNtceNo", "")
            if bid_no and bid_no not in seen:
                seen.add(bid_no)
                unique_bids.append(bid)
            elif not bid_no:
                unique_bids.append(bid)

        # 키워드 OR 매칭
        kw_lower = [kw.lower() for kw in keywords]
        matched = []
        for bid in unique_bids:
            title = bid.get("bidNtceNm", "").lower()
            hits = [kw for kw, kw_l in zip(keywords, kw_lower) if kw_l in title]
            if hits:
                bid["matched_keywords"] = hits
                bid["match_count"] = len(hits)
                matched.append(bid)

        matched.sort(key=lambda x: x["match_count"], reverse=True)
        return matched

    # ── 내부 헬퍼 ────────────────────────────────

    def _extract_main_keyword(self, title: str) -> str:
        """제목에서 핵심 키워드 추출 (불용어 제거)"""
        stopwords = {'및', '등', '의', '을', '를', '이', '가', '은', '는', '에', '에서',
                     '으로', '로', '과', '와', '구축', '개발', '서비스', '시스템', '사업'}
        words = re.findall(r'[가-힣A-Za-z0-9]+', title)
        keywords = [w for w in words if len(w) > 1 and w not in stopwords]
        return keywords[0] if keywords else title[:10]


# ─────────────────────────────────────────────
# 하위 호환: search_similar_contracts (phase_executor에서 사용)
# ─────────────────────────────────────────────

    async def search_similar_contracts(
        self,
        rfp_title: str,
        rfp_description: str,
        keywords: List[str],
        budget_range: Optional[tuple] = None,
        date_range_months: int = 24,
    ) -> List[G2BContract]:
        """하위 호환 메서드 — search_competitors 결과를 G2BContract 목록으로 변환"""
        result = await self.search_competitors(rfp_title, date_range_months)
        contracts = []
        for i, comp in enumerate(result.get("competitors", [])):
            contracts.append(G2BContract(
                contract_id=f"g2b_{i:04d}",
                title=rfp_title,
                agency="나라장터",
                contractor=comp["company_name"],
                contract_date=datetime.now().strftime("%Y-%m-%d"),
                contract_amount=comp["avg_contract_amount"],
                category="정보통신",
                description="",
                similarity_score=comp["strength_score"],
            ))
        return contracts

    async def identify_competitors(
        self,
        contracts: List[G2BContract],
        min_contracts: int = 1,
    ) -> List[CompetitorProfile]:
        """하위 호환 메서드"""
        company_map: Dict[str, List[G2BContract]] = {}
        for c in contracts:
            company_map.setdefault(c.contractor, []).append(c)

        profiles = []
        for company, clist in company_map.items():
            if len(clist) < min_contracts:
                continue
            avg = int(sum(c.contract_amount for c in clist) / len(clist))
            strength = min(0.5 + len(clist) * 0.1, 0.95)
            profiles.append(CompetitorProfile(
                company_name=company,
                contract_history=clist,
                specialization_areas=["정보통신"],
                avg_contract_amount=avg,
                success_rate=0.8,
                market_share=0.05,
                strength_score=strength,
                weakness_score=1 - strength,
            ))
        return sorted(profiles, key=lambda x: x.strength_score, reverse=True)


# ─────────────────────────────────────────────
# 스탠드얼론 래퍼 (LangGraph 노드에서 사용)
# ─────────────────────────────────────────────

async def search_bids(
    keywords: str,
    budget_min: Optional[int] = None,
    region: Optional[str] = None,
) -> List[Dict]:
    """공고 검색 — rfp_search 노드에서 사용."""
    async with G2BService() as svc:
        try:
            results = await svc.search_bid_announcements(keywords, num_of_rows=500)
            # 간이 필터
            filtered = []
            for r in results:
                bid = {
                    "bid_no": r.get("bidNtceNo", ""),
                    "project_name": r.get("bidNtceNm", ""),
                    "client": r.get("ntceInsttNm", r.get("dminsttNm", "")),
                    "budget": r.get("presmptPrce", r.get("asignBdgtAmt", "")),
                    "deadline": r.get("bidClseDt", ""),
                }
                if budget_min:
                    try:
                        amt = int(str(bid["budget"]).replace(",", "").strip() or "0")
                        if amt < budget_min:
                            continue
                    except (ValueError, TypeError):
                        pass
                filtered.append(bid)
            return filtered
        except Exception as e:
            logger.warning(f"G2B 공고 검색 실패: {e}")
            return []


async def get_bid_detail(bid_no: str) -> Dict:
    """공고 상세 조회 — rfp_fetch 노드에서 사용."""
    async with G2BService() as svc:
        try:
            raw = await svc.get_bid_detail(bid_no)
            return {
                "project_name": raw.get("bidNtceNm", ""),
                "client": raw.get("ntceInsttNm", raw.get("dminsttNm", "")),
                "budget": raw.get("presmptPrce", raw.get("asignBdgtAmt", "")),
                "deadline": raw.get("bidClseDt", ""),
                "description": raw.get("ntceSpecDocUrl1", raw.get("bidNtceDtlUrl", "")),
                "requirements_summary": raw.get("ntceSpecCn", ""),
                "attachments": _extract_attachments(raw),
            }
        except Exception as e:
            logger.warning(f"G2B 상세 조회 실패: {e}")
            return {
                "project_name": bid_no,
                "client": "", "budget": "", "deadline": "",
                "description": "", "requirements_summary": "",
                "attachments": [],
            }


async def get_bid_result_info(bid_no: str) -> Dict:
    """낙찰 정보 조회 — Phase 4 성과 추적에서 사용."""
    async with G2BService() as svc:
        try:
            results = await svc.get_bid_results(bid_no, num_of_rows=5)
            if results:
                r = results[0]
                return {
                    "winner": r.get("bidwinnrNm", r.get("sucsfBidderNm", "")),
                    "amount": r.get("sucsfBidAmt", r.get("presmptPrce", "")),
                    "bid_count": r.get("prtcptCnum", r.get("bidprcPrtcptCnt", "")),
                    "bid_date": r.get("opengDt", ""),
                }
            return {}
        except Exception:
            return {}


async def fetch_and_store_bid_result(bid_notice_id: str, domain: str = "SI/SW개발") -> Dict:
    """
    낙찰정보 수집 + market_price_data 적재 (Phase 4-1).

    공고번호로 낙찰결과를 조회하여 market_price_data 테이블에 저장.
    """
    async with G2BService() as svc:
        results = await svc.get_bid_results(bid_notice_id, num_of_rows=5)
        if not results:
            return {"status": "not_found", "bid_notice_id": bid_notice_id}

        r = results[0]
        winner = r.get("bidwinnrNm", r.get("sucsfBidderNm", ""))
        amount_str = r.get("sucsfBidAmt", r.get("presmptPrce", "0"))
        budget_str = r.get("presmptPrce", r.get("asignBdgtAmt", "0"))
        bid_count_str = r.get("prtcptCnum", r.get("bidprcPrtcptCnt", "0"))

        try:
            winning_price = int(str(amount_str).replace(",", "").strip() or "0")
        except (ValueError, TypeError):
            winning_price = 0
        try:
            budget = int(str(budget_str).replace(",", "").strip() or "0")
        except (ValueError, TypeError):
            budget = 0
        try:
            num_bidders = int(str(bid_count_str).strip() or "0")
        except (ValueError, TypeError):
            num_bidders = 0

        bid_ratio = round(winning_price / budget, 4) if budget > 0 else None
        project_title = r.get("bidNtceNm", "")
        client_org = r.get("ntceInsttNm", r.get("dminsttNm", ""))
        bid_date = r.get("opengDt", "")
        year = int(bid_date[:4]) if bid_date and len(bid_date) >= 4 else datetime.now().year

        # market_price_data 적재
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        row = {
            "project_title": project_title,
            "client_org": client_org,
            "domain": domain,
            "budget": budget,
            "winning_price": winning_price,
            "bid_ratio": bid_ratio,
            "num_bidders": num_bidders,
            "year": year,
            "source": f"G2B:{bid_notice_id}",
        }

        await client.table("market_price_data").upsert(
            row, on_conflict="source"
        ).execute()

        return {
            "status": "stored",
            "bid_notice_id": bid_notice_id,
            "winner": winner,
            "winning_price": winning_price,
            "budget": budget,
            "bid_ratio": bid_ratio,
            "num_bidders": num_bidders,
        }


async def bulk_sync_bid_results(proposal_ids: Optional[List[str]] = None) -> Dict:
    """
    진행 중인 프로젝트의 낙찰정보 일괄 동기화 (Phase 4-1).

    proposal_ids 미지정 시 status='submitted'인 프로젝트 대상.
    """
    from app.utils.supabase_client import get_async_client
    client = await get_async_client()

    if proposal_ids:
        proposals = await client.table("proposals").select(
            "id, picked_bid_no"
        ).in_("id", proposal_ids).not_.is_("picked_bid_no", "null").execute()
    else:
        proposals = await client.table("proposals").select(
            "id, picked_bid_no"
        ).eq("status", "submitted").not_.is_("picked_bid_no", "null").execute()

    results = {"synced": 0, "not_found": 0, "errors": 0, "details": []}
    for p in (proposals.data or []):
        bid_no = p.get("picked_bid_no", "")
        if not bid_no:
            continue
        try:
            r = await fetch_and_store_bid_result(bid_no)
            if r["status"] == "stored":
                results["synced"] += 1
            else:
                results["not_found"] += 1
            results["details"].append(r)
        except Exception as e:
            results["errors"] += 1
            results["details"].append({"bid_notice_id": bid_no, "error": str(e)})

    return results


def _extract_attachments(raw: Dict) -> List[Dict]:
    """G2B 공고 상세에서 첨부파일 추출."""
    attachments = []
    for i in range(1, 6):
        url = raw.get(f"ntceSpecDocUrl{i}", "")
        if url:
            ext = "pdf" if "pdf" in url.lower() else "hwp" if "hwp" in url.lower() else "unknown"
            attachments.append({"url": url, "type": ext, "name": f"첨부파일{i}"})
    return attachments
