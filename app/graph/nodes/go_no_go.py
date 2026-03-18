"""
STEP 1-②: Go/No-Go 판정 노드 (§7)

RFP 분석 + 역량 DB + 리서치 브리프 → 포지셔닝 추천 + 수주 가능성 점수.
Full/Lite 모드 분기. v3.2: research_brief + 발주기관 인텔리전스 5단계.
"""

import logging

from app.graph.state import GoNoGoResult, ProposalState
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


async def go_no_go(state: ProposalState) -> dict:
    """STEP 1-②: Go/No-Go 평가 (Full: 역량+리서치 기반, Lite: RFP만)."""

    rfp = state.get("rfp_analysis")
    if not rfp:
        return {"current_step": "go_no_go_error"}

    mode = state.get("mode", "full")
    research_brief = state.get("research_brief", {})

    # RFP 요약 구성
    if hasattr(rfp, "model_dump"):
        rfp_dict = rfp.model_dump()
    elif isinstance(rfp, dict):
        rfp_dict = rfp
    else:
        rfp_dict = {}

    rfp_summary = f"""
사업명: {rfp_dict.get('project_name', '')}
발주기관: {rfp_dict.get('client', '')}
핫버튼: {rfp_dict.get('hot_buttons', [])}
평가항목: {rfp_dict.get('eval_items', [])}
기술:가격 비중: {rfp_dict.get('tech_price_ratio', {})}
필수요건: {rfp_dict.get('mandatory_reqs', [])}
"""

    # 역량 DB + KB 조회 (Full 모드)
    capabilities_text = ""
    client_intel_text = ""
    competitor_text = ""

    if mode == "full":
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        org_id = state.get("org_id", "")

        # 역량 DB
        if org_id:
            try:
                caps = await client.table("capabilities").select("type, title, detail, keywords").eq("org_id", org_id).execute()
                capabilities_text = "\n".join(
                    f"- [{c['type']}] {c['title']}: {c['detail']}" for c in (caps.data or [])
                )
            except Exception as e:
                logger.warning(f"역량 DB 조회 실패: {e}")

        # 발주기관 인텔리전스 (v3.0)
        client_name = rfp_dict.get("client", "")
        if client_name:
            try:
                intel = await client.table("client_intelligence").select("*").ilike("client_name", f"%{client_name}%").limit(5).execute()
                if intel.data:
                    client_intel_text = "\n".join(
                        f"- {r['aspect']}: {r['detail']}" for r in intel.data
                    )
            except Exception:
                pass

        # 경쟁사 DB (v3.0)
        try:
            comp = await client.table("competitors").select("*").limit(10).execute()
            if comp.data:
                competitor_text = "\n".join(
                    f"- {c['company_name']}: {c.get('strengths', '')} / {c.get('weaknesses', '')}"
                    for c in comp.data
                )
        except Exception:
            pass

    # 리서치 브리프 요약 (v3.2) + credibility 필터링 (v3.7)
    research_text = ""
    if research_brief:
        if isinstance(research_brief, dict):
            # 종합 요약
            research_text = research_brief.get("summary", "")

            # 고신뢰 데이터만 추출 (credibility: high/medium만 포함)
            topics = research_brief.get("research_topics", [])
            credible_evidence = []
            for topic in topics:
                if not isinstance(topic, dict):
                    continue
                for dp in topic.get("data_points", []):
                    if isinstance(dp, dict):
                        cred = dp.get("credibility", "low")
                        if cred in ("high", "medium"):
                            source = dp.get("source", "")
                            credible_evidence.append(
                                f"- {dp.get('content', '')} [{source}] ({cred})"
                            )
                    elif isinstance(dp, str):
                        # 레거시 문자열 형식 호환
                        credible_evidence.append(f"- {dp}")

            if credible_evidence:
                research_text += "\n\n검증된 근거 데이터:\n" + "\n".join(credible_evidence[:15])

            # 차별화 포인트 + 리스크
            diff_pts = research_brief.get("differentiation_points", [])
            risk_pts = research_brief.get("risk_factors", [])
            if diff_pts:
                research_text += "\n\n차별화 포인트:\n" + "\n".join(f"- {d}" for d in diff_pts)
            if risk_pts:
                research_text += "\n\n리스크 요인:\n" + "\n".join(f"- {r}" for r in risk_pts)

            if not research_text:
                research_text = str(research_brief)
        else:
            research_text = str(research_brief)

    prompt = f"""다음 RFP에 대한 Go/No-Go 판정을 수행하세요.

## RFP 분석 요약
{rfp_summary}

## 자사 역량
{capabilities_text or "(역량 DB 없음 — Lite 모드)"}

## 발주기관 인텔리전스 (v3.2: 5단계 프레임워크)
{client_intel_text or "(발주기관 정보 없음)"}
분석 관점: 1) 기관 미션·전략 방향, 2) 조직 구조·의사결정 체계,
3) 과거 발주 패턴·선호 특성, 4) 평가위원 성향 추정, 5) 관계 이력·접점

## 경쟁 환경
{competitor_text or "(경쟁사 정보 없음)"}

## 사전조사 리서치 브리프 (v3.2)
{research_text or "(리서치 미수행)"}

## 지시사항
1. 포지셔닝 판정: defensive(수성) / offensive(공격) / adjacent(인접)
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
