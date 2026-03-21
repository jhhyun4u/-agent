"""
노드 간 공유 컨텍스트 유틸리티.

중복 제거 대상:
- RFP dict 변환 + 요약 생성 (4개 노드에서 반복)
- 리서치 브리프 credibility 필터링 (2개 노드에서 반복)
- KB 조회 (capabilities, client_intel, competitors, lessons, competitor_history)
- 이전 섹션 컨텍스트 윈도우 제한
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 이전 섹션 컨텍스트 윈도우 크기
PREV_SECTIONS_FULL_WINDOW = 3  # content 포함
PREV_SECTIONS_CONTENT_CHARS = 300  # content 잘림 기준


# ── RFP 변환 ──


def rfp_to_dict(rfp: Any) -> dict:
    """RFP 객체 → dict 변환 (Pydantic / dict / None 모두 처리)."""
    if rfp is None:
        return {}
    if hasattr(rfp, "model_dump"):
        return rfp.model_dump()
    if isinstance(rfp, dict):
        return rfp
    return {}


def get_rfp_summary(rfp_dict: dict) -> str:
    """RFP dict에서 표준 요약 텍스트 생성."""
    if not rfp_dict:
        return "(RFP 분석 없음)"
    return f"""사업명: {rfp_dict.get('project_name', '')}
발주기관: {rfp_dict.get('client', '')}
핫버튼: {rfp_dict.get('hot_buttons', [])}
평가항목: {rfp_dict.get('eval_items', [])}
기술:가격 비중: {rfp_dict.get('tech_price_ratio', {})}
필수요건: {rfp_dict.get('mandatory_reqs', [])}
특수조건: {rfp_dict.get('special_conditions', [])}"""


def get_rfp_summary_compact(rfp_dict: dict) -> str:
    """RFP dict에서 간결한 요약 (plan_nodes 등에서 사용)."""
    if not rfp_dict:
        return "(RFP 분석 없음)"
    return f"""사업명: {rfp_dict.get('project_name', '')}
발주기관: {rfp_dict.get('client', '')}
핫버튼: {rfp_dict.get('hot_buttons', [])}
평가항목: {rfp_dict.get('eval_items', [])}
필수요건: {rfp_dict.get('mandatory_reqs', [])}"""


# ── 리서치 브리프 ──


def extract_credible_research(research_brief: dict | None, max_evidence: int = 20) -> str:
    """리서치 브리프에서 고신뢰(high/medium) 데이터만 추출하여 텍스트로 반환."""
    if not research_brief or not isinstance(research_brief, dict):
        return ""

    parts = []

    # 종합 요약
    summary = research_brief.get("summary", "")
    if summary:
        parts.append(summary)

    # 고신뢰 데이터만 추출
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
                credible_evidence.append(f"- {dp}")

    if credible_evidence:
        parts.append("검증된 근거 데이터:\n" + "\n".join(credible_evidence[:max_evidence]))

    # 차별화 포인트 + 리스크
    diff_pts = research_brief.get("differentiation_points", [])
    risk_pts = research_brief.get("risk_factors", [])
    if diff_pts:
        parts.append("차별화 포인트:\n" + "\n".join(f"- {d}" for d in diff_pts))
    if risk_pts:
        parts.append("리스크 요인:\n" + "\n".join(f"- {r}" for r in risk_pts))

    return "\n\n".join(parts) if parts else str(research_brief) if research_brief else ""


def extract_evidence_candidates(research_brief: dict | None, max_items: int = 20) -> str:
    """리서치 브리프에서 evidence 후보 추출 (plan_story용)."""
    if not research_brief or not isinstance(research_brief, dict):
        return "(리서치 근거 없음)"

    candidates = []
    for topic in research_brief.get("research_topics", []):
        if not isinstance(topic, dict):
            continue
        rfp_align = topic.get("rfp_alignment", topic.get("relevance", ""))
        for dp in topic.get("data_points", []):
            if isinstance(dp, dict) and dp.get("credibility") in ("high", "medium"):
                candidates.append(
                    f"- {dp.get('content', '')} [{dp.get('source', '')}] (연관: {rfp_align})"
                )
            elif isinstance(dp, str):
                candidates.append(f"- {dp}")

    return "\n".join(candidates[:max_items]) if candidates else "(리서치 근거 없음)"


# ── KB 조회 ──


async def query_kb_context(
    org_id: str = "",
    client_name: str = "",
    *,
    include_capabilities: bool = True,
    include_client_intel: bool = True,
    include_competitors: bool = True,
    include_lessons: bool = True,
    include_competitor_history: bool = False,
    include_past_performance: bool = False,
    include_positioning_overrides: bool = False,
) -> dict[str, str]:
    """KB 테이블들을 한 번에 조회하여 텍스트 dict로 반환.

    Returns:
        {"capabilities": str, "client_intel": str, "competitors": str,
         "lessons": str, "competitor_history": str, "past_performance": str,
         "positioning_overrides": str}
    """
    result: dict[str, str] = {}
    try:
        # lazy import: supabase_client → config → settings 순환 방지
        from app.utils.supabase_client import get_async_client
        db = await get_async_client()
    except Exception as e:
        logger.warning(f"KB DB 연결 실패: {e}")
        return result

    # 역량 DB
    if include_capabilities and org_id:
        try:
            caps = await db.table("capabilities").select("type, title, detail").eq("org_id", org_id).execute()
            if caps.data:
                result["capabilities"] = "\n".join(
                    f"- [{c['type']}] {c['title']}: {c['detail']}" for c in caps.data
                )
        except Exception as e:
            logger.debug(f"역량 DB 조회 실패: {e}")

    # 발주기관 인텔리전스
    if include_client_intel and client_name:
        try:
            intel = await db.table("client_intelligence").select("*").ilike("client_name", f"%{client_name}%").limit(5).execute()
            if intel.data:
                result["client_intel"] = "\n".join(
                    f"- {r['aspect']}: {r['detail']}" for r in intel.data
                )
        except Exception as e:
            logger.debug(f"발주기관 인텔 조회 실패: {e}")

    # 경쟁사 DB
    if include_competitors:
        try:
            comp = await db.table("competitors").select("*").limit(10).execute()
            if comp.data:
                result["competitors"] = "\n".join(
                    f"- {c['company_name']}: 강점={c.get('strengths', '')} / 약점={c.get('weaknesses', '')}"
                    for c in comp.data
                )
        except Exception as e:
            logger.debug(f"경쟁사 DB 조회 실패: {e}")

    # 과거 교훈
    if include_lessons:
        try:
            lessons_query = db.table("lessons_learned").select(
                "title, result, positioning, failure_category, effective_points, weak_points, improvements"
            ).order("created_at", desc=True).limit(10)
            if client_name:
                lessons_query = lessons_query.ilike("client_name", f"%{client_name}%")
            lessons_result = await lessons_query.execute()

            # 발주기관 매칭 없으면 조직 전체에서 최근 교훈
            if not lessons_result.data and org_id:
                lessons_result = await db.table("lessons_learned").select(
                    "title, result, positioning, failure_category, effective_points, weak_points, improvements"
                ).eq("org_id", org_id).order("created_at", desc=True).limit(5).execute()

            if lessons_result.data:
                parts = []
                for ls in lessons_result.data:
                    r_label = "수주" if ls.get("result") == "won" else "패찰"
                    parts.append(
                        f"- [{r_label}] {ls.get('title', '')}"
                        f" (포지셔닝: {ls.get('positioning', '-')})"
                        f" — 강점: {ls.get('effective_points', '-')},"
                        f" 약점: {ls.get('weak_points', '-')},"
                        f" 개선: {ls.get('improvements', '-')}"
                    )
                result["lessons"] = "\n".join(parts)
        except Exception as e:
            logger.debug(f"교훈 조회 실패: {e}")

    # 경쟁사 대전 기록
    if include_competitor_history and org_id:
        try:
            history = await db.table("competitor_history").select(
                "competitor_name, result, positioning, client_name, created_at"
            ).eq("org_id", org_id).order("created_at", desc=True).limit(20).execute()

            if history.data:
                records: dict = {}
                for h in history.data:
                    name = h.get("competitor_name", "")
                    if not name:
                        continue
                    if name not in records:
                        records[name] = {"won": 0, "lost": 0, "positions": []}
                    if h.get("result") == "won":
                        records[name]["won"] += 1
                    else:
                        records[name]["lost"] += 1
                    if h.get("positioning"):
                        records[name]["positions"].append(h["positioning"])

                parts = []
                for name, r in sorted(records.items(), key=lambda x: x[1]["won"] + x[1]["lost"], reverse=True):
                    total = r["won"] + r["lost"]
                    win_rate = round(r["won"] / total * 100) if total else 0
                    freq_pos = max(set(r["positions"]), key=r["positions"].count) if r["positions"] else "-"
                    parts.append(f"- {name}: {r['won']}승 {r['lost']}패 (승률 {win_rate}%), 주요 포지셔닝: {freq_pos}")
                result["competitor_history"] = "\n".join(parts)
        except Exception as e:
            logger.debug(f"경쟁 전적 조회 실패: {e}")

    # 포지셔닝별 과거 성과
    if include_past_performance and org_id:
        try:
            perf = await db.table("proposal_results").select(
                "result, proposals!inner(positioning, client)"
            ).eq("proposals.org_id", org_id).limit(50).execute()

            if perf.data:
                pos_stats: dict = {}
                for p in perf.data:
                    prop = p.get("proposals", {})
                    pos = prop.get("positioning", "unknown")
                    if pos not in pos_stats:
                        pos_stats[pos] = {"won": 0, "lost": 0}
                    if p.get("result") == "won":
                        pos_stats[pos]["won"] += 1
                    elif p.get("result") == "lost":
                        pos_stats[pos]["lost"] += 1

                parts = []
                for pos, s in pos_stats.items():
                    total = s["won"] + s["lost"]
                    rate = round(s["won"] / total * 100) if total else 0
                    parts.append(f"- {pos}: {s['won']}승 {s['lost']}패 (승률 {rate}%)")
                result["past_performance"] = "\n".join(parts)
        except Exception as e:
            logger.debug(f"과거 성과 조회 실패: {e}")

    # 포지셔닝 오버라이드 이력
    if include_positioning_overrides:
        try:
            overrides = await db.table("feedbacks").select(
                "feedback, comments, created_at"
            ).eq("step", "go_no_go").ilike("feedback", "%오버라이드%").order("created_at", desc=True).limit(5).execute()

            if not overrides.data:
                overrides = await db.table("feedbacks").select(
                    "feedback, comments, created_at"
                ).eq("step", "strategy").ilike("feedback", "%포지셔닝 변경%").order("created_at", desc=True).limit(5).execute()

            if overrides.data:
                parts = []
                for o in overrides.data:
                    parts.append(f"- {o.get('feedback', '')}")
                    if isinstance(o.get("comments"), dict) and o["comments"].get("override_reason"):
                        parts.append(f"  이유: {o['comments']['override_reason']}")
                result["positioning_overrides"] = "\n".join(parts)
        except Exception as e:
            logger.debug(f"오버라이드 이력 조회 실패: {e}")

    return result


# ── 전략 필드 추출 ──


def get_strategy_dict(strategy: Any) -> dict:
    """Strategy 객체 → dict 변환."""
    if strategy is None:
        return {}
    if hasattr(strategy, "model_dump"):
        return strategy.model_dump()
    if isinstance(strategy, dict):
        return strategy
    return {}


# ── 이전 섹션 컨텍스트 ──


def build_prev_sections_context(
    existing_sections: list,
    full_window: int = PREV_SECTIONS_FULL_WINDOW,
    content_chars: int = PREV_SECTIONS_CONTENT_CHARS,
) -> str:
    """이전 섹션 컨텍스트를 윈도우 제한하여 생성.

    - 최근 full_window개: section_id + title + content[:content_chars]
    - 그 이전: section_id + title만 (목록)
    """
    if not existing_sections:
        return ""

    def _to_dict(s) -> dict:
        if hasattr(s, "model_dump"):
            return s.model_dump()
        if isinstance(s, dict):
            return s
        return {}

    total = len(existing_sections)
    older = existing_sections[:max(0, total - full_window)]
    recent = existing_sections[max(0, total - full_window):]

    parts = []

    # 오래된 섹션: title만
    if older:
        titles = []
        for s in older:
            d = _to_dict(s)
            titles.append(f"  - {d.get('section_id', '')}: {d.get('title', '')}")
        parts.append("이전 섹션 목록:\n" + "\n".join(titles))

    # 최근 섹션: content 포함
    if recent:
        for s in recent:
            sd = _to_dict(s)
            content = sd.get("content", "")
            preview = content[:content_chars] + "..." if len(content) > content_chars else content
            parts.append(f"### {sd.get('section_id', '')}: {sd.get('title', '')}\n{preview}")

    return "\n\n## 이전에 작성된 섹션 (참고하여 일관성 유지)\n" + "\n\n".join(parts)
