"""
STEP 1-②: Go/No-Go 판정 노드 (§7)

v4.0: 3축 정량 분석(유사실적·자격·경쟁) + AI 전략가산 = 100점 합산.
70점 게이트: ≥85 적극참여 / ≥70 일반참여 / <70 No-Go 추천.
Fatal: 필수 자격 미충족 또는 필수 유사실적 0건 → 점수 무관 No-Go.
"""

import hashlib
import logging

from app.graph.state import GoNoGoResult, ProposalState
from app.graph.context_helpers import (
    extract_credible_research,
    get_rfp_summary,
    query_kb_context,
    rfp_to_dict,
    score_competition,
    score_qualification,
    score_similar_performance,
)
from app.services.core.claude_client import claude_generate
from app.services import prompt_tracker

logger = logging.getLogger(__name__)


async def go_no_go(state: ProposalState) -> dict:
    """STEP 1-②: Go/No-Go 4축 정량 스코어링."""

    rfp = state.get("rfp_analysis")
    if not rfp:
        return {
            "current_step": "go_no_go_error",
            "node_errors": {
                **state.get("node_errors", {}),
                "go_no_go": {
                    "error": "rfp_analysis가 없어 Go/No-Go 수행 불가",
                    "step": "go_no_go",
                },
            },
        }

    mode = state.get("mode", "full")
    rfp_dict = rfp_to_dict(rfp)
    org_id = state.get("org_id", "")

    # ── 축 1~3: 정량 스코어링 (DB 기반, Full 모드) ──
    if mode == "full" and org_id:
        perf = await score_similar_performance(rfp_dict, org_id)
        qual = await score_qualification(rfp_dict, org_id)
        comp = await score_competition(rfp_dict, org_id)
    else:
        perf = {"score": 15, "is_fatal": False, "required_items": [], "coverage_rate": 0.0,
                "same_client_wins": 0, "same_domain_win_rate": None, "fatal_reason": None}
        qual = {"score": 15, "is_fatal": False, "mandatory": [], "preferred": [],
                "fatal_reason": None, "summary": "Lite 모드 — 자격 검증 스킵 (15점 기본 부여)"}
        comp = {"score": 10, "intensity_level": "medium", "estimated_competitors": 5,
                "top_competitors": [], "our_win_rate_at_client": None, "rationale": "Lite 모드"}

    # ── 축 4: AI 전략 가산 (20점) ──
    strategic = await _ai_strategic_assessment(state, rfp_dict, org_id, mode)

    # ── 합산 + 게이트 판정 ──
    total = perf["score"] + qual["score"] + comp["score"] + strategic["score"]

    if qual.get("is_fatal") or perf.get("is_fatal"):
        recommendation = "no-go"
        score_tag = "disqualified"
        fatal_flaw = qual.get("fatal_reason") or perf.get("fatal_reason")
    elif total >= 85:
        recommendation = "go"
        score_tag = "priority"
        fatal_flaw = None
    elif total >= 70:
        recommendation = "go"
        score_tag = "standard"
        fatal_flaw = None
    else:
        recommendation = "no-go"
        score_tag = "below_threshold"
        fatal_flaw = f"합산 {total}점 (기준: 70점)"

    # Lite 모드 disclaimer 추가
    score_breakdown = {
        "similar_performance": perf["score"],
        "qualification": qual["score"],
        "competition": comp["score"],
        "strategic": strategic["score"],
    }
    if mode != "full":
        score_breakdown["lite_mode_disclaimer"] = (
            "Lite 모드: 축①②③은 실제 DB 조회 없이 중간값(15/15/10) 부여. Full 모드 재검토 권장."
        )

    gng = GoNoGoResult(
        rfp_analysis_ref=f"rfp_{state.get('project_id', '')}",
        positioning=strategic.get("positioning", "defensive"),
        positioning_rationale=strategic.get("positioning_rationale", ""),
        feasibility_score=total,
        score_breakdown=score_breakdown,
        pros=strategic.get("pros", []),
        risks=strategic.get("risks", []),
        recommendation=recommendation,
        fatal_flaw=fatal_flaw,
        strategic_focus=strategic.get("strategic_focus"),
        score_tag=score_tag,
        performance_detail=perf,
        qualification_detail=qual,
        competition_detail=comp,
    )

    return {
        "go_no_go": gng,
        "positioning": gng.positioning,
        "current_step": "go_no_go_complete",
    }


async def _ai_strategic_assessment(
    state: ProposalState,
    rfp_dict: dict,
    org_id: str,
    mode: str,
) -> dict:
    """AI 기반 전략 평가 (20점 만점).

    기술 적합도(8) + 발주처 관계(6) + 가격 경쟁력(6)
    + 포지셔닝 추천 + 강점/리스크 + 핵심 승부수.
    """
    rfp_summary = get_rfp_summary(rfp_dict)

    # KB 조회 (축소: capabilities + client_intel + lessons)
    kb: dict[str, str] = {}
    if mode == "full" and org_id:
        kb = await query_kb_context(
            org_id=org_id,
            client_name=rfp_dict.get("client", ""),
            include_capabilities=True,
            include_client_intel=True,
            include_competitors=False,
            include_lessons=True,
            include_competitor_history=False,
            include_past_performance=False,
            include_positioning_overrides=False,
        )

    # 리서치 브리프
    research_text = extract_credible_research(
        state.get("research_brief"), max_evidence=10
    )

    # 가격경쟁력 시장 분석
    pricing_context = ""
    try:
        from app.services.domains.bidding.bid_calculator import parse_budget_string
        from app.services.pricing import PricingEngine, QuickEstimateRequest

        budget_str = rfp_dict.get("budget", "")
        budget_val = parse_budget_string(budget_str) if budget_str else None
        if budget_val and budget_val > 0:
            engine = PricingEngine()
            qe = await engine.quick_estimate(QuickEstimateRequest(
                budget=budget_val,
                evaluation_method=rfp_dict.get("eval_method", "종합심사"),
                domain=rfp_dict.get("domain", "SI/SW개발"),
                positioning=state.get("positioning", "defensive"),
                competitor_count=5,
            ))
            pricing_context = (
                f"\n## 시장 기반 가격 분석\n"
                f"- 추천 낙찰률: {qe.recommended_ratio}%\n"
                f"- 수주확률: {qe.win_probability:.0%} (신뢰도: {qe.win_probability_confidence})\n"
            )
    except Exception as e:
        logger.debug(f"PricingEngine 실패 (무시): {e}")

    prompt = f"""다음 RFP에 대한 전략적 평가를 수행하세요. (20점 만점)

## RFP 분석 요약
{rfp_summary}

## 자사 역량
{kb.get("capabilities", "(역량 DB 없음)")}

## 발주기관 인텔리전스
{kb.get("client_intel", "(발주기관 정보 없음)")}

## 과거 교훈
{kb.get("lessons", "(교훈 없음)")}

## 리서치 브리프
{research_text or "(리서치 미수행)"}
{pricing_context}
## 지시사항
1. 기술 적합도 (0~8점): RFP 핫버튼·평가항목 ↔ 자사 역량 부합도
2. 발주처 관계 (0~6점): 기관 인텔리전스 기반 관계 수준 + 접점 이력
3. 가격 경쟁력 (0~6점): 예산 대비 시장 분석 + 낙찰률 추정
4. 포지셔닝: defensive | offensive | adjacent (근거 포함)
5. 강점(pros) 3개, 리스크(risks) 3개
6. 핵심 승부수(strategic_focus) 1줄

## 출력 형식 (JSON)
{{
  "score": 15,
  "tech_fit": 7,
  "client_relationship": 4,
  "price_competitiveness": 4,
  "positioning": "defensive",
  "positioning_rationale": "근거",
  "pros": ["강점1", "강점2", "강점3"],
  "risks": ["리스크1", "리스크2", "리스크3"],
  "strategic_focus": "핵심 승부수 1줄"
}}
"""

    result = await claude_generate(prompt)

    # 프롬프트 사용 기록
    proposal_id = state.get("project_id", "")
    if proposal_id:
        try:
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="go_no_go",
                section_id=None,
                prompt_id="_inline.go_no_go_strategic_v4",
                prompt_version=0,
                prompt_hash=hashlib.sha256(prompt[:500].encode()).hexdigest(),
            )
        except Exception as e:
            logger.debug(f"프롬프트 트래커 기록 실패 (무시): {e}")

    # score 범위 보정
    raw_score = result.get("score", 10)
    score = max(0, min(int(raw_score) if isinstance(raw_score, (int, float)) else 10, 20))

    return {
        "score": score,
        "tech_fit": result.get("tech_fit", 0),
        "client_relationship": result.get("client_relationship", 0),
        "price_competitiveness": result.get("price_competitiveness", 0),
        "positioning": result.get("positioning", "defensive"),
        "positioning_rationale": result.get("positioning_rationale", ""),
        "pros": result.get("pros", []),
        "risks": result.get("risks", []),
        "strategic_focus": result.get("strategic_focus"),
    }
