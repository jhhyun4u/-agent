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
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://apis.data.go.kr/1230000"


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
            .select("data")
            .eq("query_hash", key)
            .gt("expires_at", datetime.utcnow().isoformat())
            .single()
            .execute()
        )
        if result.data:
            return result.data.get("data")
    except Exception:
        pass
    return None


async def _set_cache(key: str, api_type: str, params: dict, data: List) -> None:
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        await (
            client.table("g2b_cache")
            .upsert({
                "query_hash": key,
                "api_type": api_type,
                "params": params,
                "data": data,
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

        encoded_key = quote(api_key, safe="")
        url = f"{self.base_url}/{endpoint}?serviceKey={encoded_key}&_type=json"

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
                    result = data.get("response", {})
                    header = result.get("header", {})
                    if header.get("resultCode") != "00":
                        raise RuntimeError(f"G2B API 오류: {header.get('resultMsg')}")
                    items = result.get("body", {}).get("items") or {}
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

        Returns:
            나라장터 입찰공고 raw 목록
        """
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "bidNtceNm": keyword,
        }
        if date_from:
            params["bidNtceBgnDt"] = date_from  # 예: 20230101
        if date_to:
            params["bidNtceEndDt"] = date_to

        return await self._call_api(
            "BidPublicInfoService04/getBidPblancListInfoServc",
            params,
        )

    # ── 2단계: 낙찰결과 조회 ─────────────────────────

    async def get_bid_results(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1,
    ) -> List[Dict]:
        """
        낙찰결과 목록 조회 (getBidResultListInfo)
        낙찰업체명, 낙찰금액 포함

        Returns:
            낙찰결과 raw 목록
        """
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "bidNtceNm": keyword,
        }
        return await self._call_api(
            "BidPublicInfoService04/getBidResultListInfo",
            params,
        )

    # ── 3단계: 계약결과 조회 ─────────────────────────

    async def get_contract_results(
        self,
        keyword: str,
        num_of_rows: int = 20,
        page_no: int = 1,
    ) -> List[Dict]:
        """
        계약결과 목록 조회 (getContractResultListInfo)

        Returns:
            계약결과 raw 목록
        """
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
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
    ) -> List[Dict]:
        """
        업체별 입찰이력 조회 (getCmpnyBidInfoServc)

        Args:
            company_name: 업체명

        Returns:
            업체 입찰이력 raw 목록
        """
        params: Dict[str, Any] = {
            "numOfRows": num_of_rows,
            "pageNo": page_no,
            "cmpnyNm": company_name,
        }
        return await self._call_api(
            "BidPublicInfoService04/getCmpnyBidInfoServc",
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
        # 날짜 범위
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=date_range_months * 30)
        date_from = start_dt.strftime("%Y%m%d%H%M%S")
        date_to = end_dt.strftime("%Y%m%d%H%M%S")

        keyword = self._extract_main_keyword(rfp_title)
        logger.info(f"G2B 경쟁사 분석 시작: keyword={keyword}")

        # Step 1: 유사 입찰공고 검색
        try:
            bid_list = await self.search_bid_announcements(
                keyword, num_of_rows=20, date_from=date_from, date_to=date_to
            )
        except Exception as e:
            logger.warning(f"입찰공고 검색 실패: {e}")
            bid_list = []

        # Step 2: 낙찰결과에서 업체명 추출
        try:
            bid_results = await self.get_bid_results(keyword, num_of_rows=30)
        except Exception as e:
            logger.warning(f"낙찰결과 조회 실패: {e}")
            bid_results = []

        # 낙찰업체 빈도 집계
        winner_counter: Counter = Counter()
        winner_amounts: Dict[str, List[int]] = {}
        for row in bid_results:
            company = row.get("sucsfBidderNm") or row.get("cmpnyNm", "")
            amount_str = row.get("sucsfBidAmt") or row.get("bidAmt", "0")
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
