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

from fastapi import APIRouter, Depends, Query, Body, BackgroundTasks

from app.api.deps import get_current_user
from app.exceptions import G2BExternalError, G2BServiceError, InternalServiceError, TenopAPIError
from app.services.g2b_service import G2BService, fetch_and_store_bid_result, bulk_sync_bid_results
from app.services.bid_analysis_service import generate_bid_analysis_documents
from app.utils.supabase_client import get_async_client


def _classify_g2b_error(e: RuntimeError) -> TenopAPIError:
    """RuntimeError 메시지 기반 G2B 에러 분류."""
    msg = str(e)
    if "타임아웃" in msg or "시간 초과" in msg:
        return G2BExternalError("나라장터 API 응답 시간 초과")
    if "클라이언트 오류" in msg:
        return G2BExternalError(msg)
    if "연결 실패" in msg:
        return G2BExternalError("나라장터 API 서버 연결 실패")
    if "API_KEY" in msg:
        return G2BServiceError("G2B API 키가 설정되지 않았습니다.")
    return G2BExternalError(msg)

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
    - 결과를 bid_announcements 테이블에 저장 (분석 대기)
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

        # 각 검색 결과를 bid_announcements 테이블에 저장
        client = await get_async_client()
        saved_count = 0

        for item in items:
            bid_no = item.get("bid_no") or item.get("bidNo")
            if not bid_no:
                continue

            try:
                # 기존 기록 확인 (upsert를 위해)
                result = await client.table("bid_announcements").select("id").eq(
                    "org_id", current_user.org_id
                ).eq("bid_no", bid_no).execute()

                is_update = len(result.data) > 0

                # 저장할 데이터
                data = {
                    "org_id": str(current_user.org_id),
                    "bid_no": bid_no,
                    "bid_title": item.get("bid_title") or item.get("bidTitle") or "제목 미정",
                    "agency": item.get("agency") or item.get("agencyName"),
                    "budget_amount": item.get("budget_amount") or item.get("budgetAmount"),
                    "deadline_date": item.get("deadline_date") or item.get("deadlineDate"),
                    "content_text": item.get("content_text", ""),
                    "raw_data": item,  # 원본 데이터 저장
                    "analysis_status": "pending",
                    "decision": "pending",
                    "created_by": str(current_user.id) if not is_update else None,
                }

                if is_update:
                    # 업데이트: id 필요
                    bid_id = result.data[0]["id"]
                    data.pop("created_by")  # created_by는 업데이트시 제외
                    await client.table("bid_announcements").update(data).eq(
                        "id", bid_id
                    ).execute()
                else:
                    # 새로 생성
                    await client.table("bid_announcements").insert(data).execute()

                saved_count += 1
                logger.info(f"✓ bid_announcements 저장: {bid_no}")

            except Exception as e:
                logger.warning(f"! bid_announcements 저장 실패 [{bid_no}]: {str(e)}")
                # 개별 저장 실패는 계속 진행

        logger.info(f"[bid-search] {saved_count}개 공고 저장됨 (total: {len(items)})")

        return {
            "keyword": keyword,
            "page_no": page_no,
            "num_of_rows": num_of_rows,
            "total_count": len(items),
            "saved_count": saved_count,
            "items": items,
        }
    except RuntimeError as e:
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"bid-search 오류: {e}")
        raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")


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
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"bid-results 오류: {e}")
        raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 공고 분석 (RFP分析, 공고문, 과업지시서 생성)
# ─────────────────────────────────────────────

@router.post("/bid/{bid_no}/analyze")
async def analyze_bid(
    bid_no: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """
    공고 상세 분석 — 3가지 마크다운 문서 생성 (백그라운드)

    - RFP分析: 사업개요, 평가항목, 기술요구사항, 가격평가, 강점/약점, 경쟁강도, 제안전략
    - 공고문: 공고 요약
    - 과업지시서: 과업 범위, 요구사항, 일정

    모든 문서는 Supabase Storage에 저장됨.
    """
    try:
        client = await get_async_client()

        # bid_announcements에서 해당 공고 조회 (RLS: org_id 필터링 필수)
        result = await client.table("bid_announcements").select("id, bid_no, bid_title, agency, budget_amount, deadline_date, raw_data").eq(
            "org_id", str(current_user.org_id)
        ).eq("bid_no", bid_no).maybe_single().execute()

        if not result.data:
            raise G2BServiceError("공고를 찾을 수 없습니다")

        bid = result.data
        logger.info("[analyze] 공고 조회 완료")

        # 분석 문서 생성은 백그라운드에서 처리
        async def _analyze_documents():
            try:
                doc_paths = await generate_bid_analysis_documents(
                    bid_no=bid["bid_no"],
                    bid_title=bid["bid_title"],
                    agency=bid.get("agency", ""),
                    budget_amount=bid.get("budget_amount"),
                    deadline_date=bid.get("deadline_date", ""),
                    raw_data=bid.get("raw_data", {}),
                )

                # bid_announcements 업데이트: 문서 경로 및 상태 저장
                await client.table("bid_announcements").update({
                    "md_rfp_analysis_path": doc_paths["md_rfp_analysis_path"],
                    "md_notice_path": doc_paths["md_notice_path"],
                    "md_instruction_path": doc_paths["md_instruction_path"],
                    "analysis_status": "analyzed",
                }).eq("id", bid["id"]).execute()

                logger.info("✓ 공고 분석 문서 생성 완료")
            except Exception as e:
                logger.error(f"✗ 공고 분석 문서 생성 실패: {type(e).__name__}: {str(e)[:100]}")

        background_tasks.add_task(_analyze_documents)

        logger.info("[analyze] ✓ 공고 분석 시작됨 (백그라운드)")

        return {
            "bid_no": bid_no,
            "status": "pending",
            "message": "공고 분석이 백그라운드에서 처리 중입니다",
        }

    except Exception as e:
        logger.error(f"공고 분석 오류: {type(e).__name__}")
        raise G2BServiceError(f"공고 분석 중 오류가 발생했습니다: {str(e)}")


# ─────────────────────────────────────────────
# 공고 의사결정 (Go/No-Go)
# ─────────────────────────────────────────────

@router.post("/bid/{bid_no}/decision")
async def decide_bid(
    bid_no: str,
    decision: str = Body(..., description="Go 또는 No-Go"),
    decision_comment: Optional[str] = Body(None, description="의사결정 사유"),
    current_user=Depends(get_current_user),
):
    """
    공고 의사결정 기록 (Go/No-Go) — 로깅 전용

    실제 proposal_status 업데이트는 /api/bids/{bid_no}/status 엔드포인트에서 처리
    """
    try:
        if decision not in ["Go", "No-Go"]:
            raise G2BServiceError("의사결정은 'Go' 또는 'No-Go'만 가능합니다.")

        logger.info(
            f"✓ 공고 의사결정 기록: {decision}"
        )

        # 의사결정 로깅만 수행 (DB 업데이트는 /api/bids/{bid_no}/status에서 처리)
        return {
            "bid_no": bid_no,
            "decision": decision,
            "decision_comment": decision_comment,
            "message": "의사결정이 기록되었습니다",
        }

    except Exception as e:
        logger.error(f"공고 의사결정 오류 [{bid_no}]: {str(e)}")
        raise G2BServiceError(f"의사결정 기록 중 오류가 발생했습니다: {str(e)}")


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
                "winner": primary.get("bidwinnrNm", primary.get("sucsfBidderNm", "")),
                "amount": _parse_amount(primary.get("sucsfBidAmt", primary.get("presmptPrce"))),
                "bid_count": _parse_int(primary.get("prtcptCnum", primary.get("bidprcPrtcptCnt"))),
                "open_date": primary.get("opengDt", ""),
                "bid_date": primary.get("bidClseDt", primary.get("opengDt", "")),
            },
            "bid_detail": _normalize_bid_detail(detail) if detail else None,
            "all_results": [
                {
                    "winner": r.get("bidwinnrNm", r.get("sucsfBidderNm", "")),
                    "amount": _parse_amount(r.get("sucsfBidAmt", r.get("presmptPrce"))),
                    "bid_count": _parse_int(r.get("prtcptCnum", r.get("bidprcPrtcptCnt"))),
                    "open_date": r.get("opengDt", ""),
                }
                for r in results
            ],
        }
    except RuntimeError as e:
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"bid-award-info 오류: {e}")
        raise G2BServiceError("낙찰정보 조회 중 오류가 발생했습니다.")


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
            amt = _parse_amount(r.get("sucsfBidAmt", r.get("presmptPrce")))
            if amt and amt > 0:
                amounts.append(amt)

            cnt = _parse_int(r.get("prtcptCnum", r.get("bidprcPrtcptCnt")))
            if cnt and cnt > 0:
                bid_counts.append(cnt)

            winner = (r.get("bidwinnrNm") or r.get("sucsfBidderNm", "")).strip()
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
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"bid-stats 오류: {e}")
        raise G2BServiceError("낙찰 통계 조회 중 오류가 발생했습니다.")


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
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"contract-results 오류: {e}")
        raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")


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
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"company-history 오류: {e}")
        raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")


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
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"competitors 분석 오류: {e}")
        raise G2BServiceError("경쟁사 분석 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# Phase 4-1: 낙찰정보 수집 + market_price_data 적재
# ─────────────────────────────────────────────

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
        raise InternalServiceError("일괄 동기화 중 오류가 발생했습니다.")


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
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"낙찰정보 수집 오류: {e}")
        raise G2BServiceError("낙찰정보 수집 중 오류가 발생했습니다.")


# ─────────────────────────────────────────────
# 모니터링 진단 + 수동 트리거
# ─────────────────────────────────────────────

@router.get("/monitor/diagnostics")
async def monitor_diagnostics(current_user=Depends(get_current_user)):
    """모니터링 시스템 상태 진단."""
    from app.config import settings
    from app.utils.supabase_client import get_async_client

    diag: dict = {"scheduler": "unknown", "g2b_api_key": False, "teams_count": 0,
                  "teams_with_keywords": 0, "g2b_api_reachable": False, "errors": []}

    # 1) APScheduler
    import importlib.util
    if importlib.util.find_spec("apscheduler") is not None:
        diag["scheduler"] = "installed"
    else:
        diag["scheduler"] = "NOT_INSTALLED"
        diag["errors"].append("apscheduler 미설치 — 스케줄러 비활성 상태")

    # 2) G2B API 키
    diag["g2b_api_key"] = bool(settings.g2b_api_key)
    if not settings.g2b_api_key:
        diag["errors"].append("G2B_API_KEY 미설정")

    # 3) 팀 + 키워드
    try:
        client = await get_async_client()
        teams_res = await client.table("teams").select("id, name, monitor_keywords").execute()
        teams = teams_res.data or []
        diag["teams_count"] = len(teams)
        diag["teams_with_keywords"] = sum(
            1 for t in teams if t.get("monitor_keywords") and len(t["monitor_keywords"]) > 0
        )
        if diag["teams_with_keywords"] == 0:
            diag["errors"].append("monitor_keywords가 설정된 팀이 없음")
    except Exception as e:
        diag["errors"].append(f"teams 테이블 조회 실패: {e}")

    # 4) G2B API 연결 테스트 (1건만)
    if settings.g2b_api_key:
        try:
            async with G2BService() as g2b:
                test = await g2b.search_bid_announcements("테스트", num_of_rows=1)
                diag["g2b_api_reachable"] = True
                diag["g2b_test_result_count"] = len(test)
        except Exception as e:
            diag["errors"].append(f"G2B API 호출 실패: {e}")

    diag["status"] = "ok" if not diag["errors"] else "issues_found"
    return diag


@router.post("/monitor/trigger")
async def trigger_monitor(current_user=Depends(get_current_user)):
    """모니터링 수동 실행 (디버깅용)."""
    from app.services.scheduled_monitor import daily_g2b_monitor
    try:
        result = await daily_g2b_monitor()
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"수동 모니터링 실행 오류: {e}", exc_info=True)
        raise InternalServiceError(f"모니터링 실행 실패: {e}")
