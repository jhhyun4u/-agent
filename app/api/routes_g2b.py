"""
나라장터 API 프록시 라우터 (/api/g2b/*)

엔드포인트:
  GET /api/g2b/bid-search        입찰공고 검색
  GET /api/g2b/bid-results       낙찰결과 조회
  GET /api/g2b/bid/{bid_no}      특정 공고 낙찰정보 (§12-4)
  GET /api/g2b/stats             유사 공고 낙찰 통계 (§12-4)
  GET /api/g2b/contract-results  계약결과 조회
  GET /api/g2b/company-history   업체 입찰이력
  GET /api/g2b/competitors       경쟁사 통합 분석 (4단계)

모두 JWT 인증 필요 (Depends(get_current_user))
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.middleware.auth import get_current_user
from app.services.g2b_service import G2BService, fetch_and_store_bid_result, bulk_sync_bid_results

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/g2b", tags=["g2b"])


# ─────────────────────────────────────────────
# 입찰공고 검색
# ─────────────────────────────────────────────

@router.get("/bid-search")
async def bid_search(
    keyword: str = Query(..., description="검색 키워드 (예: AI 시스템 구축)"),
    num_of_rows: int = Query(20, ge=1, le=100, description="한 페이지 결과 수"),
    page_no: int = Query(1, ge=1, description="페이지 번호"),
    date_from: Optional[str] = Query(None, description="공고 시작일 (YYYYMMDDHHMMSS)"),
    date_to: Optional[str] = Query(None, description="공고 종료일 (YYYYMMDDHHMMSS)"),
    current_user=Depends(get_current_user),
):
    """
    나라장터 입찰공고 검색

    - 키워드로 유사 공고 조회
    - 캐시 TTL: 24시간
    """
    try:
        async with G2BService() as g2b:
            items = await g2b.search_bid_announcements(
                keyword=keyword,
                num_of_rows=num_of_rows,
                page_no=page_no,
                date_from=date_from,
                date_to=date_to,
            )
        return {
            "keyword": keyword,
            "page_no": page_no,
            "num_of_rows": num_of_rows,
            "total_count": len(items),
            "items": items,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"bid-search 오류: {e}")
        raise HTTPException(status_code=500, detail="나라장터 API 호출 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 낙찰결과 조회
# ─────────────────────────────────────────────

@router.get("/bid-results")
async def bid_results(
    keyword: str = Query(..., description="검색 키워드"),
    num_of_rows: int = Query(20, ge=1, le=100),
    page_no: int = Query(1, ge=1),
    current_user=Depends(get_current_user),
):
    """
    낙찰결과 조회 — 낙찰업체명, 낙찰금액 포함
    """
    try:
        async with G2BService() as g2b:
            items = await g2b.get_bid_results(
                keyword=keyword,
                num_of_rows=num_of_rows,
                page_no=page_no,
            )
        return {
            "keyword": keyword,
            "page_no": page_no,
            "total_count": len(items),
            "items": items,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"bid-results 오류: {e}")
        raise HTTPException(status_code=500, detail="나라장터 API 호출 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 특정 공고 낙찰정보 (§12-4)
# ─────────────────────────────────────────────

@router.get("/bid/{bid_no}")
async def bid_award_info(
    bid_no: str,
    current_user=Depends(get_current_user),
):
    """
    특정 공고의 낙찰정보 조회

    - 낙찰업체명, 낙찰금액, 투찰 업체수, 개찰일 등
    - 공고 상세 정보도 함께 반환
    """
    try:
        async with G2BService() as g2b:
            # 낙찰결과 조회 (공고번호 기준)
            results = await g2b.get_bid_results(bid_no, num_of_rows=10)

            # 공고 상세 조회 (예정가격, 발주기관 등 보충)
            detail = await g2b.get_bid_detail(bid_no)

        if not results:
            return {
                "bid_no": bid_no,
                "status": "not_found",
                "message": "낙찰결과가 아직 공개되지 않았거나 해당 공고번호가 없습니다.",
                "bid_detail": _normalize_bid_detail(detail) if detail else None,
            }

        primary = results[0]
        return {
            "bid_no": bid_no,
            "status": "found",
            "award": {
                "winner": primary.get("sucsfBidderNm", ""),
                "amount": _parse_amount(primary.get("sucsfBidAmt")),
                "bid_count": _parse_int(primary.get("bidprcPrtcptCnt")),
                "open_date": primary.get("opengDt", ""),
                "bid_date": primary.get("bidClseDt", primary.get("opengDt", "")),
            },
            "bid_detail": _normalize_bid_detail(detail) if detail else None,
            "all_results": [
                {
                    "winner": r.get("sucsfBidderNm", ""),
                    "amount": _parse_amount(r.get("sucsfBidAmt")),
                    "bid_count": _parse_int(r.get("bidprcPrtcptCnt")),
                    "open_date": r.get("opengDt", ""),
                }
                for r in results
            ],
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"bid-award-info 오류: {e}")
        raise HTTPException(status_code=500, detail="낙찰정보 조회 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 유사 공고 낙찰 통계 (§12-4)
# ─────────────────────────────────────────────

@router.get("/stats")
async def bid_stats(
    keyword: str = Query(..., description="검색 키워드 (유사 공고 기준)"),
    num_of_rows: int = Query(50, ge=10, le=100, description="분석 대상 건수"),
    date_range_months: int = Query(24, ge=1, le=60, description="검색 기간 (개월)"),
    current_user=Depends(get_current_user),
):
    """
    유사 공고 낙찰 통계 — 평균 낙찰금액, 낙찰률, 경쟁강도 등

    - 키워드로 유사 낙찰결과를 조회한 뒤 통계 집계
    - plan_price 노드의 벤치마크 데이터로 활용
    """
    try:
        async with G2BService() as g2b:
            results = await g2b.get_bid_results(
                keyword=keyword,
                num_of_rows=num_of_rows,
            )

        if not results:
            return {
                "keyword": keyword,
                "status": "no_data",
                "message": "해당 키워드의 낙찰결과가 없습니다.",
                "stats": None,
            }

        # 통계 집계
        amounts = []
        bid_counts = []
        winners: dict[str, int] = {}

        for r in results:
            amt = _parse_amount(r.get("sucsfBidAmt"))
            if amt and amt > 0:
                amounts.append(amt)

            cnt = _parse_int(r.get("bidprcPrtcptCnt"))
            if cnt and cnt > 0:
                bid_counts.append(cnt)

            winner = r.get("sucsfBidderNm", "").strip()
            if winner:
                winners[winner] = winners.get(winner, 0) + 1

        avg_amount = int(sum(amounts) / len(amounts)) if amounts else 0
        min_amount = min(amounts) if amounts else 0
        max_amount = max(amounts) if amounts else 0
        avg_bid_count = round(sum(bid_counts) / len(bid_counts), 1) if bid_counts else 0

        # 상위 낙찰업체 (빈도순)
        top_winners = sorted(winners.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "keyword": keyword,
            "status": "ok",
            "analyzed_count": len(results),
            "stats": {
                "avg_amount": avg_amount,
                "min_amount": min_amount,
                "max_amount": max_amount,
                "amount_count": len(amounts),
                "avg_bid_count": avg_bid_count,
                "bid_count_range": {
                    "min": min(bid_counts) if bid_counts else 0,
                    "max": max(bid_counts) if bid_counts else 0,
                },
                "unique_winners": len(winners),
                "top_winners": [
                    {"company": name, "win_count": count}
                    for name, count in top_winners
                ],
            },
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"bid-stats 오류: {e}")
        raise HTTPException(status_code=500, detail="낙찰 통계 조회 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────

def _parse_amount(val) -> int | None:
    """금액 문자열을 int로 변환."""
    if val is None:
        return None
    try:
        return int(str(val).replace(",", "").strip() or "0")
    except (ValueError, TypeError):
        return None


def _parse_int(val) -> int | None:
    """정수 문자열을 int로 변환."""
    if val is None:
        return None
    try:
        return int(str(val).replace(",", "").strip() or "0")
    except (ValueError, TypeError):
        return None


def _normalize_bid_detail(raw: dict) -> dict:
    """공고 상세 raw 데이터를 정규화."""
    return {
        "project_name": raw.get("bidNtceNm", ""),
        "client": raw.get("ntceInsttNm", raw.get("dminsttNm", "")),
        "budget": _parse_amount(raw.get("presmptPrce", raw.get("asignBdgtAmt"))),
        "deadline": raw.get("bidClseDt", ""),
        "bid_method": raw.get("bidMethdNm", ""),
        "contract_method": raw.get("cntrctCnclsMthdNm", ""),
    }


# ─────────────────────────────────────────────
# 계약결과 조회
# ─────────────────────────────────────────────

@router.get("/contract-results")
async def contract_results(
    keyword: str = Query(..., description="계약명 키워드"),
    num_of_rows: int = Query(20, ge=1, le=100),
    page_no: int = Query(1, ge=1),
    current_user=Depends(get_current_user),
):
    """
    계약결과 목록 조회
    """
    try:
        async with G2BService() as g2b:
            items = await g2b.get_contract_results(
                keyword=keyword,
                num_of_rows=num_of_rows,
                page_no=page_no,
            )
        return {
            "keyword": keyword,
            "page_no": page_no,
            "total_count": len(items),
            "items": items,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"contract-results 오류: {e}")
        raise HTTPException(status_code=500, detail="나라장터 API 호출 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 업체 입찰이력
# ─────────────────────────────────────────────

@router.get("/company-history")
async def company_history(
    company_name: str = Query(..., description="업체명"),
    num_of_rows: int = Query(20, ge=1, le=100),
    page_no: int = Query(1, ge=1),
    current_user=Depends(get_current_user),
):
    """
    업체별 입찰이력 조회
    """
    try:
        async with G2BService() as g2b:
            items = await g2b.get_company_bid_history(
                company_name=company_name,
                num_of_rows=num_of_rows,
                page_no=page_no,
            )
        return {
            "company_name": company_name,
            "page_no": page_no,
            "total_count": len(items),
            "items": items,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"company-history 오류: {e}")
        raise HTTPException(status_code=500, detail="나라장터 API 호출 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 경쟁사 통합 분석 (4단계 파이프라인)
# ─────────────────────────────────────────────

@router.get("/competitors")
async def competitors(
    rfp_title: str = Query(..., description="RFP 제목 (경쟁사 분석 기준)"),
    date_range_months: int = Query(24, ge=1, le=60, description="검색 기간 (개월)"),
    max_competitors: int = Query(10, ge=1, le=30, description="최대 경쟁사 수"),
    current_user=Depends(get_current_user),
):
    """
    경쟁사 통합 분석 — 4단계 파이프라인

    1. 유사 입찰공고 검색
    2. 낙찰결과에서 낙찰업체 추출
    3. 주요 업체 수주이력 조회
    4. CompetitorProfile 생성

    결과는 Phase 2 LLM 분석에 활용됩니다.
    """
    try:
        async with G2BService() as g2b:
            result = await g2b.search_competitors(
                rfp_title=rfp_title,
                date_range_months=date_range_months,
                max_competitors=max_competitors,
            )
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"competitors 분석 오류: {e}")
        raise HTTPException(status_code=500, detail="경쟁사 분석 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# Phase 4-1: 낙찰정보 수집 + market_price_data 적재
# ─────────────────────────────────────────────

@router.post("/bid-results/{bid_notice_id}")
async def collect_bid_result(
    bid_notice_id: str,
    domain: str = Query("SI/SW개발", description="도메인 분류"),
    current_user=Depends(get_current_user),
):
    """특정 공고 낙찰정보를 수집하여 market_price_data에 저장."""
    try:
        result = await fetch_and_store_bid_result(bid_notice_id, domain)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"낙찰정보 수집 오류: {e}")
        raise HTTPException(status_code=500, detail="낙찰정보 수집 중 오류가 발생했습니다.")


@router.post("/bid-results/bulk-sync")
async def bulk_sync(
    current_user=Depends(get_current_user),
):
    """진행 중인 프로젝트의 낙찰정보 일괄 동기화."""
    try:
        result = await bulk_sync_bid_results()
        return result
    except Exception as e:
        logger.error(f"낙찰정보 일괄 동기화 오류: {e}")
        raise HTTPException(status_code=500, detail="일괄 동기화 중 오류가 발생했습니다.")
