"""
나라장터 API 프록시 라우터 (/api/g2b/*)

엔드포인트:
  GET /api/g2b/bid-search        입찰공고 검색
  GET /api/g2b/bid-results       낙찰결과 조회
  GET /api/g2b/contract-results  계약결과 조회
  GET /api/g2b/company-history   업체 입찰이력
  GET /api/g2b/competitors       경쟁사 통합 분석 (4단계)

모두 JWT 인증 필요 (Depends(get_current_user))
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.middleware.auth import get_current_user
from app.services.g2b_service import G2BService

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
