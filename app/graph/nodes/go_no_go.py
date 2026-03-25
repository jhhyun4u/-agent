"""
STEP 1-②: Go/No-Go 판정 노드 (§7)

RFP 분석 + 역량 DB + 리서치 브리프 → 포지셔닝 추천 + 수주 가능성 점수.
Full/Lite 모드 분기. v3.2: research_brief + 발주기관 인텔리전스 5단계.
"""

import logging

from app.graph.state import GoNoGoResult, ProposalState
from app.graph.context_helpers import (
    extract_credible_research,
    get_rfp_summary,
    query_kb_context,
    rfp_to_dict,
)
from app.services.claude_client import claude_generate
from app.services import prompt_tracker

logger = logging.getLogger(__name__)


async def go_no_go(state: ProposalState) -> dict:
    """STEP 1-②: Go/No-Go 평가 (Full: 역량+리서치 기반, Lite: RFP만)."""

    rfp = state.get("rfp_analysis")
    if not rfp:
        return {"current_step": "go_no_go_error"}

    mode = state.get("mode", "full")
    rfp_dict = rfp_to_dict(rfp)
    rfp_summary = get_rfp_summary(rfp_dict)

    # KB 조회 (Full 모드)
    kb: dict[str, str] = {}
    if mode == "full":
        kb = await query_kb_context(
            org_id=state.get("org_id", ""),
            client_name=rfp_dict.get("client", ""),
            include_capabilities=True,
            include_client_intel=True,
            include_competitors=True,
            include_lessons=True,
            include_competitor_history=False,
            include_past_performance=True,
            include_positioning_overrides=True,
        )

    # 유사 과거 사례 시맨틱 매칭 (C-1)
    similar_cases_text = ""
    if mode == "full":
        try:
            from app.graph.context_helpers import find_similar_cases
            similar_cases_text = await find_similar_cases(
                project_name=rfp_dict.get("project_name", ""),
                client_name=rfp_dict.get("client", ""),
                org_id=state.get("org_id", ""),
            )
        except Exception:
            pass

    # 리서치 브리프 (v3.2) + credibility 필터링 (v3.7)
    research_text = extract_credible_research(
        state.get("research_brief"), max_evidence=15
    )

    # 가격경쟁력 시장 분석 (PricingEngine 연동)
    pricing_context = ""
    try:
        from app.services.bid_calculator import parse_budget_string
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
                f"\n## 시장 기반 가격 분석 (알고리즘)\n"
                f"- 추천 낙찰률: {qe.recommended_ratio}%\n"
                f"- 수주확률: {qe.win_probability:.0%} (신뢰도: {qe.win_probability_confidence})\n"
                f"- 분석 기반: {qe.data_quality} (유사 사례 {qe.comparable_cases}건)\n"
            )
            if qe.market_avg_ratio:
                pricing_context += f"- 시장 평균 낙찰률: {qe.market_avg_ratio * 100:.1f}%\n"
            if qe.positioning_adjustment:
                pricing_context += f"- 포지셔닝 조정: {qe.positioning_adjustment}\n"
    except Exception as e:
        logger.debug(f"PricingEngine quick_estimate 실패 (무시): {e}")

    prompt = f"""다음 RFP에 대한 Go/No-Go 판정을 수행하세요.

## RFP 분석 요약
{rfp_summary}

## 자사 역량
{kb.get("capabilities", "(역량 DB 없음 — Lite 모드)")}

## 발주기관 인텔리전스 (v3.2: 5단계 프레임워크)
{kb.get("client_intel", "(발주기관 정보 없음)")}
분석 관점: 1) 기관 미션·전략 방향, 2) 조직 구조·의사결정 체계,
3) 과거 발주 패턴·선호 특성, 4) 평가위원 성향 추정, 5) 관계 이력·접점

## 경쟁 환경
{kb.get("competitors", "(경쟁사 정보 없음)")}

## 사전조사 리서치 브리프 (v3.2)
{research_text or "(리서치 미수행)"}

## 과거 교훈 (동일 발주기관에서의 수주/패찰 경험)
{kb.get("lessons", "(이 발주기관 대상 과거 교훈 없음)")}

## 포지셔닝별 과거 성과 (조직 전체)
{kb.get("past_performance", "(과거 입찰 성과 데이터 없음)")}

## 포지셔닝 오버라이드 이력 (사람이 AI 판정을 변경한 선례)
{kb.get("positioning_overrides", "(오버라이드 이력 없음)")}
{pricing_context}
{similar_cases_text}
## 지시사항
1. 포지셔닝 판정: defensive(수성) / offensive(공격) / adjacent(인접)
   - **과거 포지셔닝별 성과 데이터가 있으면 반드시 참고하세요**
   - 예: defensive 승률 80%이면 defensive 우선 고려, 승률 20%이면 다른 포지셔닝 검토
   - 과거 교훈에서 동일 발주기관의 패찰 사유가 있으면 같은 실수를 반복하지 않도록 전략 조정
2. 수주 가능성 점수 (0~100)와 항목별 분석
3. 강점(pros) 3~5개, 리스크 3~5개
4. Go/No-Go 추천 및 근거

## 출력 형식 (JSON)
{{
  "positioning": "defensive|offensive|adjacent",
  "positioning_rationale": "포지셔닝 판단 근거",
  "feasibility_score": 75,
  "score_breakdown": {{
    "기술역량": 80,
    "수행실적": 70,
    "가격경쟁력": 75,
    "발주처관계": 60,
    "경쟁환경": 65
  }},
  "pros": ["강점1", "강점2", "강점3"],
  "risks": ["리스크1", "리스크2", "리스크3"],
  "recommendation": "go 또는 no-go",
  "recommendation_rationale": "추천 근거",
  "fatal_flaw": "no-go 판정 시 가장 치명적인 결격 사유 1줄. go일 경우 null",
  "strategic_focus": "go 판정 시 제안서에서 가장 뾰족하게 강조할 승부수(Winning Theme) 1줄. no-go일 경우 null"
}}
"""

    result = await claude_generate(prompt)

    # 프롬프트 사용 기록 (인라인 프롬프트)
    proposal_id = state.get("project_id", "")
    if proposal_id:
        try:
            import hashlib
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="go_no_go",
                section_id=None,
                prompt_id="_inline.go_no_go",
                prompt_version=0,
                prompt_hash=hashlib.sha256(prompt[:500].encode()).hexdigest(),
            )
        except Exception:
            pass

    gng = GoNoGoResult(
        rfp_analysis_ref=f"rfp_{state.get('project_id', '')}",
        positioning=result.get("positioning", "defensive"),
        positioning_rationale=result.get("positioning_rationale", ""),
        feasibility_score=result.get("feasibility_score", 0) if mode == "full" else 0,
        score_breakdown=result.get("score_breakdown", {}) if mode == "full" else {},
        pros=result.get("pros", []),
        risks=result.get("risks", []),
        recommendation=result.get("recommendation", "go"),
        fatal_flaw=result.get("fatal_flaw"),
        strategic_focus=result.get("strategic_focus"),
    )

    return {
        "go_no_go": gng,
        "positioning": gng.positioning,
        "current_step": "go_no_go_complete",
    }
