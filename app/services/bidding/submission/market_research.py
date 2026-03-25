"""
입찰 시장 조사 서비스

bid_plan 실행 전, 유사과제 낙찰정보가 충분한지 확인하고
부족하면 G2B에서 크롤링하여 market_price_data를 보강한다.

2단계 전략:
1. 기존 market_price_data에서 유사 사례 검색 (domain + eval_method + budget_tier)
2. 30건 미만이면 G2B 낙찰결과 API로 유사과제 낙찰정보 수집 → 저장
"""

import logging
from datetime import datetime, timedelta

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

# 통계 모델 전환 임계값 (WinProbabilityModel.MIN_CASES_FOR_STATS와 동일)
MIN_CASES_FOR_STATS = 30


async def ensure_market_data(
    domain: str,
    evaluation_method: str,
    budget: int,
    project_name: str = "",
    client_name: str = "",
    hot_buttons: list[str] | None = None,
) -> dict:
    """
    유사과제 낙찰정보가 충분한지 확인하고, 부족하면 G2B 크롤링으로 보강.

    Returns:
        {
            "existing_count": 기존 데이터 건수,
            "crawled_count": 신규 크롤링 건수,
            "total_count": 보강 후 총 건수,
            "data_quality": "sufficient" | "enriched" | "sparse",
            "search_keywords": 사용된 검색 키워드,
        }
    """
    budget_tier = _compute_budget_tier(budget)

    # 1단계: 기존 데이터 확인
    existing = await _count_comparable(domain, evaluation_method, budget_tier)

    if existing >= MIN_CASES_FOR_STATS:
        logger.info(
            f"시장 데이터 충분: {existing}건 (domain={domain}, "
            f"eval={evaluation_method}, tier={budget_tier})"
        )
        return {
            "existing_count": existing,
            "crawled_count": 0,
            "total_count": existing,
            "data_quality": "sufficient",
            "search_keywords": [],
        }

    # 2단계: 부족 → G2B 크롤링으로 보강
    logger.info(
        f"시장 데이터 부족 ({existing}건 < {MIN_CASES_FOR_STATS}건). "
        f"G2B 크롤링 시작: domain={domain}"
    )

    keywords = _build_search_keywords(domain, project_name, hot_buttons)
    crawled = 0

    for kw in keywords:
        try:
            count = await _crawl_bid_results(kw, domain, evaluation_method)
            crawled += count
        except Exception as e:
            logger.warning(f"G2B 크롤링 실패 (keyword={kw}): {e}")

        # 목표 달성 확인
        total = await _count_comparable(domain, evaluation_method, budget_tier)
        if total >= MIN_CASES_FOR_STATS:
            break

    final_count = await _count_comparable(domain, evaluation_method, budget_tier)
    quality = (
        "sufficient" if final_count >= MIN_CASES_FOR_STATS
        else "enriched" if crawled > 0
        else "sparse"
    )

    logger.info(
        f"시장 조사 완료: 기존 {existing}건 + 크롤링 {crawled}건 = 총 {final_count}건 ({quality})"
    )

    return {
        "existing_count": existing,
        "crawled_count": crawled,
        "total_count": final_count,
        "data_quality": quality,
        "search_keywords": keywords,
    }


def _build_search_keywords(
    domain: str,
    project_name: str = "",
    hot_buttons: list[str] | None = None,
) -> list[str]:
    """
    G2B 검색 키워드 생성.

    우선순위:
    1. 과제명에서 핵심 키워드 추출 (가장 구체적)
    2. RFP hot_buttons (평가위원 관심사항)
    3. 도메인 기반 일반 키워드 (가장 넓음)
    """
    keywords = []

    # 1. 과제명에서 핵심 단어 추출 (2~4글자 명사)
    if project_name:
        # 불용어 제거 후 의미 있는 단어 추출
        stopwords = {
            "구축", "사업", "용역", "운영", "개발", "시스템", "정보", "관리",
            "서비스", "플랫폼", "고도화", "ISP", "BPR", "연구", "조사",
        }
        words = [
            w for w in project_name.replace("(", " ").replace(")", " ").split()
            if len(w) >= 2 and w not in stopwords
        ]
        # 가장 구체적인 2~3개 키워드 조합
        if words:
            keywords.append(" ".join(words[:3]))
            if len(words) > 1:
                keywords.append(words[0])  # 첫 번째 핵심 단어 단독

    # 2. hot_buttons에서 키워드 (평가위원이 중시하는 분야)
    if hot_buttons:
        for hb in hot_buttons[:2]:
            kw = hb.strip()
            if len(kw) >= 2 and kw not in keywords:
                keywords.append(kw)

    # 3. 도메인 기반 일반 키워드 (가장 넓은 범위)
    domain_keywords = {
        "SI/SW개발": ["정보시스템", "소프트웨어"],
        "정책연구": ["정책연구", "정책수립"],
        "성과분석": ["성과분석", "성과평가"],
        "컨설팅": ["컨설팅", "ISP"],
        "엔지니어링": ["엔지니어링", "설계"],
        "감리": ["감리", "정보화감리"],
    }
    for key, kws in domain_keywords.items():
        if key in domain:
            for kw in kws:
                if kw not in keywords:
                    keywords.append(kw)
            break

    # 도메인 자체도 fallback
    if not keywords:
        keywords.append(domain)

    return keywords[:5]  # 최대 5개 키워드


async def _count_comparable(
    domain: str,
    evaluation_method: str,
    budget_tier: str,
) -> int:
    """market_price_data에서 유사 사례 건수 조회."""
    try:
        client = await get_async_client()
        query = (
            client.table("market_price_data")
            .select("id", count="exact")
            .eq("domain", domain)
            .not_.is_("bid_ratio", "null")
        )
        if evaluation_method:
            query = query.eq("evaluation_method", evaluation_method)
        if budget_tier:
            query = query.eq("budget_tier", budget_tier)

        result = await query.execute()
        return result.count or 0
    except Exception as e:
        logger.debug(f"유사 사례 카운트 실패: {e}")
        return 0


async def _crawl_bid_results(
    keyword: str,
    domain: str,
    evaluation_method: str,
    date_range_days: int = 365,
) -> int:
    """G2B 낙찰결과 검색 → market_price_data 저장. 저장된 건수 반환."""
    from app.services.g2b_service import G2BService, _map_evaluation_method

    stored = 0
    client = await get_async_client()

    async with G2BService() as svc:
        # 최근 1년치 낙찰결과 검색
        results = await svc.get_bid_results(
            keyword=keyword,
            num_of_rows=50,
            date_range_days=date_range_days,
        )

        for r in results:
            try:
                # 낙찰금액, 예정가격 파싱
                winning_str = r.get("sucsfBidAmt", r.get("bidprc", "0"))
                budget_str = r.get("presmptPrce", r.get("asignBdgtAmt", "0"))
                bidders_str = r.get("prtcptCnum", r.get("bidprcPrtcptCnt", "0"))

                winning_price = int(str(winning_str).replace(",", "").strip() or "0")
                budget_val = int(str(budget_str).replace(",", "").strip() or "0")
                num_bidders = int(str(bidders_str).strip() or "0")

                if winning_price <= 0 or budget_val <= 0:
                    continue

                bid_ratio = round(winning_price / budget_val, 4)
                project_title = r.get("bidNtceNm", "")
                client_org = r.get("ntceInsttNm", r.get("dminsttNm", ""))
                bid_date = r.get("opengDt", "")
                year = int(bid_date[:4]) if bid_date and len(bid_date) >= 4 else datetime.now().year

                eval_raw = r.get("evlMthd", r.get("bidMethdNm", ""))
                mapped_eval = _map_evaluation_method(eval_raw)

                # 평가방식 필터: 요청과 다르면 스킵 (선택적)
                if evaluation_method and mapped_eval and mapped_eval != evaluation_method:
                    continue

                budget_tier = _compute_budget_tier(budget_val)

                source = f"G2B:market_research:{r.get('bidNtceNo', keyword)}"

                await client.table("market_price_data").upsert(
                    {
                        "project_title": project_title,
                        "client_org": client_org,
                        "domain": domain,
                        "budget": budget_val,
                        "winning_price": winning_price,
                        "bid_ratio": bid_ratio,
                        "num_bidders": num_bidders,
                        "year": year,
                        "evaluation_method": mapped_eval or None,
                        "budget_tier": budget_tier,
                        "source": source,
                    },
                    on_conflict="source",
                ).execute()
                stored += 1

            except Exception as e:
                logger.debug(f"낙찰정보 파싱/저장 실패: {e}")
                continue

    return stored


def _compute_budget_tier(budget: int) -> str:
    """예산 규모 구간."""
    if budget < 500_000_000:
        return "<500M"
    elif budget < 1_000_000_000:
        return "500M-1B"
    return ">1B"
