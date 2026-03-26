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
    """RFP dict에서 표준 요약 텍스트 생성 (전략·Go/No-Go 등 주요 노드용)."""
    if not rfp_dict:
        return "(RFP 분석 없음)"
    parts = [
        f"사업명: {rfp_dict.get('project_name', '')}",
        f"발주기관: {rfp_dict.get('client', '')}",
        f"사업유형: {rfp_dict.get('domain', '')}" if rfp_dict.get("domain") else None,
        f"예산: {rfp_dict.get('budget', '')}" if rfp_dict.get("budget") else None,
        f"마감일: {rfp_dict.get('deadline', '')}" if rfp_dict.get("deadline") else None,
        f"수행기간: {rfp_dict.get('duration', '')}" if rfp_dict.get("duration") else None,
        f"계약유형: {rfp_dict.get('contract_type', '')}" if rfp_dict.get("contract_type") else None,
        f"케이스: {rfp_dict.get('case_type', '')}",
        f"평가방식: {rfp_dict.get('eval_method', '')}" if rfp_dict.get("eval_method") else None,
        f"핫버튼: {rfp_dict.get('hot_buttons', [])}",
        f"평가항목: {rfp_dict.get('eval_items', [])}",
        f"기술:가격 비중: {rfp_dict.get('tech_price_ratio', {})}",
        f"필수요건: {rfp_dict.get('mandatory_reqs', [])}",
        f"업체자격요건: {rfp_dict.get('qualification_requirements', [])}" if rfp_dict.get("qualification_requirements") else None,
        f"유사실적요건: {rfp_dict.get('similar_project_requirements', [])}" if rfp_dict.get("similar_project_requirements") else None,
        f"특수조건: {rfp_dict.get('special_conditions', [])}",
    ]
    return "\n".join(p for p in parts if p is not None)


def get_rfp_summary_compact(rfp_dict: dict) -> str:
    """RFP dict에서 간결한 요약 (plan_nodes 등에서 사용)."""
    if not rfp_dict:
        return "(RFP 분석 없음)"
    parts = [
        f"사업명: {rfp_dict.get('project_name', '')}",
        f"발주기관: {rfp_dict.get('client', '')}",
        f"사업유형: {rfp_dict.get('domain', '')}" if rfp_dict.get("domain") else None,
        f"예산: {rfp_dict.get('budget', '')}" if rfp_dict.get("budget") else None,
        f"마감일: {rfp_dict.get('deadline', '')}" if rfp_dict.get("deadline") else None,
        f"평가방식: {rfp_dict.get('eval_method', '')}" if rfp_dict.get("eval_method") else None,
        f"핫버튼: {rfp_dict.get('hot_buttons', [])}",
        f"평가항목: {rfp_dict.get('eval_items', [])}",
        f"필수요건: {rfp_dict.get('mandatory_reqs', [])}",
    ]
    return "\n".join(p for p in parts if p is not None)


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


# ── 유사 사례 검색 (C-1) ──


async def find_similar_cases(
    project_name: str,
    client_name: str,
    org_id: str,
    top_k: int = 3,
) -> str:
    """RFP 사업명 기반 유사 과거 사례 시맨틱 검색 → 텍스트 반환."""
    try:
        from app.services.knowledge_search import unified_search
        results = await unified_search(
            query=f"{project_name} {client_name}",
            org_id=org_id,
            filters={"areas": ["lesson"]},
            top_k=top_k,
        )
        lessons = results.get("lesson", [])
        if not lessons:
            return ""

        parts = []
        for ls in lessons:
            r = "수주" if ls.get("result") == "won" else "패찰"
            title = ls.get("title", ls.get("strategy_summary", ""))
            if title and len(title) > 60:
                title = title[:60] + "..."
            parts.append(
                f"- [{r}] {title}"
                f" (포지셔닝: {ls.get('positioning', '-')})"
                f" — 강점: {(ls.get('effective_points') or '-')[:80]},"
                f" 약점: {(ls.get('weak_points') or '-')[:80]}"
            )
        return f"\n\n## 유사 과거 사례 (시맨틱 매칭 top {top_k})\n" + "\n".join(parts)
    except Exception as e:
        logger.debug(f"유사 사례 검색 실패: {e}")
        return ""


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


# ── Go/No-Go 4축 정량 스코어링 (v4.0) ──


def _match_qualification(req_keywords: list[str], capabilities: list[dict]) -> dict | None:
    """자격 요건 키워드 ↔ capabilities 매칭. 가장 유사한 1건 반환."""
    for cap in capabilities:
        cap_text = f"{cap.get('title', '')} {cap.get('detail', '')}".lower()
        cap_kws = [k.lower() for k in (cap.get("keywords") or [])]
        for kw in req_keywords:
            kw_lower = kw.lower()
            if kw_lower in cap_text or kw_lower in cap_kws:
                return cap
    return None


async def score_similar_performance(
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """축①: RFP 유사실적 요건 ↔ 자사 수주 이력 정량 매칭 (30점 만점)."""
    result: dict[str, Any] = {
        "score": 0,
        "required_items": [],
        "coverage_rate": 0.0,
        "same_client_wins": 0,
        "same_domain_win_rate": None,
        "is_fatal": False,
        "fatal_reason": None,
    }

    similar_reqs: list[str] = rfp_dict.get("similar_project_requirements") or []
    client_name: str = rfp_dict.get("client", "")
    domain: str = rfp_dict.get("domain", "")

    try:
        from app.utils.supabase_client import get_async_client
        db = await get_async_client()
    except Exception as e:
        logger.warning(f"score_similar_performance DB 연결 실패: {e}")
        result["score"] = 15  # fallback
        return result

    # ── 유사실적 요건이 없으면 기본 20점 ──
    if not similar_reqs:
        result["score"] = 20
        return result

    # ── Step 1: AI 파싱으로 요건 구조화 ──
    parsed_reqs: list[dict] = []
    try:
        from app.services.claude_client import claude_generate
        parse_prompt = (
            "다음 유사실적 요건을 JSON 배열로 구조화하세요.\n"
            "각 요건: {\"raw_text\": str, \"period_years\": int, "
            "\"min_amount\": int(원 단위), \"min_count\": int, "
            "\"domain_keywords\": [str]}\n"
            "금액은 원 단위 정수로 변환 (예: 10억→1000000000).\n"
            "기간이 명시 안 되면 period_years=5.\n"
            "건수가 명시 안 되면 min_count=1.\n\n"
            "요건 목록:\n" + "\n".join(f"- {r}" for r in similar_reqs)
        )
        parsed_reqs = await claude_generate(parse_prompt)
        if not isinstance(parsed_reqs, list):
            parsed_reqs = [parsed_reqs] if isinstance(parsed_reqs, dict) else []
    except Exception as e:
        logger.debug(f"유사실적 AI 파싱 실패 (fallback): {e}")

    if not parsed_reqs:
        # AI 파싱 실패 시 기본 구조
        parsed_reqs = [
            {"raw_text": r, "period_years": 5, "min_amount": 0, "min_count": 1, "domain_keywords": []}
            for r in similar_reqs
        ]

    # ── Step 2: DB 정량 매칭 (각 요건별) ──
    met_count = 0
    for req in parsed_reqs:
        period = req.get("period_years", 5)
        min_amount = req.get("min_amount", 0)
        min_count = req.get("min_count", 1)
        kws = req.get("domain_keywords", [])

        try:
            query = (
                db.table("proposal_results")
                .select("proposals!inner(title, bid_amount, created_at, client_name)")
                .eq("result", "won")
                .eq("proposals.org_id", org_id)
            )
            rows = await query.limit(50).execute()

            matched = []
            from datetime import datetime, timedelta, timezone
            cutoff = datetime.now(timezone.utc) - timedelta(days=period * 365)
            for row in rows.data or []:
                p = row.get("proposals", {})
                # 기간 필터
                created = p.get("created_at", "")
                if created and created < cutoff.isoformat():
                    continue
                # 금액 필터
                amt = p.get("bid_amount") or 0
                if min_amount and amt < min_amount:
                    continue
                # 키워드 필터 (OR)
                if kws:
                    title = (p.get("title") or "").lower()
                    if not any(kw.lower() in title for kw in kws):
                        continue
                matched.append({
                    "title": p.get("title", ""),
                    "amount": amt,
                    "year": created[:4] if created else "",
                    "client": p.get("client_name", ""),
                })

            is_met = len(matched) >= min_count
            if is_met:
                met_count += 1

            req["matched_count"] = len(matched)
            req["matched_projects"] = matched[:5]
            req["is_met"] = is_met
        except Exception as e:
            logger.debug(f"유사실적 DB 매칭 실패: {e}")
            req["matched_count"] = 0
            req["matched_projects"] = []
            req["is_met"] = False

    result["required_items"] = parsed_reqs
    total_reqs = len(parsed_reqs)
    result["coverage_rate"] = met_count / total_reqs if total_reqs else 0.0

    # ── Step 3: 동일 발주기관 수주 보너스 ──
    try:
        if client_name:
            client_wins = await (
                db.table("proposal_results")
                .select("proposals!inner(client_name)", count="exact")
                .eq("result", "won")
                .eq("proposals.org_id", org_id)
                .ilike("proposals.client_name", f"%{client_name}%")
                .execute()
            )
            result["same_client_wins"] = client_wins.count or 0
    except Exception as e:
        logger.debug(f"동일 발주기관 수주 조회 실패: {e}")

    # ── Step 4: 동일 사업유형 승률 ──
    try:
        if domain:
            domain_lessons = await (
                db.table("lessons_learned")
                .select("result")
                .eq("org_id", org_id)
                .ilike("industry", f"%{domain}%")
                .execute()
            )
            if domain_lessons.data:
                won = sum(1 for dl in domain_lessons.data if dl.get("result") == "won")
                total = sum(1 for dl in domain_lessons.data if dl.get("result") in ("won", "lost"))
                result["same_domain_win_rate"] = won / total if total else None
    except Exception as e:
        logger.debug(f"사업유형 승률 조회 실패: {e}")

    # ── Step 5: 점수 산정 ──
    coverage = result["coverage_rate"]
    if coverage >= 1.0:
        base = 25
    elif coverage > 0:
        base = round(coverage * 25)
    else:
        base = 0
        if total_reqs > 0:
            result["is_fatal"] = True
            result["fatal_reason"] = (
                f"필수 유사실적 요건 {total_reqs}건 중 0건 충족 — 참가자격 미달 가능"
            )

    bonus = 0
    if result["same_client_wins"] >= 1:
        bonus += 3
    if result.get("same_domain_win_rate") is not None and result["same_domain_win_rate"] >= 0.6:
        bonus += 2

    result["score"] = min(base + bonus, 30)
    return result


async def score_qualification(
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """축②: RFP 자격 요건 ↔ 자사 보유 자격(capabilities) 자동 대조 (30점 만점)."""
    result: dict[str, Any] = {
        "score": 0,
        "mandatory": [],
        "preferred": [],
        "is_fatal": False,
        "fatal_reason": None,
        "summary": "",
    }

    qual_reqs: list[str] = rfp_dict.get("qualification_requirements") or []

    # 요건 없으면 25점 (요건 자체가 없는 공고 → 자격 통과)
    if not qual_reqs:
        result["score"] = 25
        result["summary"] = "자격 요건 없음 (기본 통과)"
        return result

    try:
        from app.utils.supabase_client import get_async_client
        db = await get_async_client()
    except Exception as e:
        logger.warning(f"score_qualification DB 연결 실패: {e}")
        result["score"] = 15  # fallback
        return result

    # ── Step 1: AI 파싱으로 mandatory/preferred 분류 ──
    classified: dict = {"mandatory": [], "preferred": []}
    try:
        from app.services.claude_client import claude_generate
        classify_prompt = (
            "다음 자격 요건을 mandatory(필수 참가자격)와 preferred(가점/우대)로 분류하세요.\n"
            "mandatory 판단 기준: '필수', '참가자격', '등록 업체', '보유 업체', '면허' 포함\n"
            "preferred 판단 기준: '가점', '우대', '우선' 포함\n"
            "애매하면 mandatory로 분류하세요.\n\n"
            "출력 JSON: {\"mandatory\": [{\"requirement\": str, \"keywords\": [str]}], "
            "\"preferred\": [{\"requirement\": str, \"keywords\": [str]}]}\n\n"
            "요건 목록:\n" + "\n".join(f"- {r}" for r in qual_reqs)
        )
        classified = await claude_generate(classify_prompt)
        if not isinstance(classified, dict):
            classified = {"mandatory": [], "preferred": []}
    except Exception as e:
        logger.debug(f"자격 분류 AI 파싱 실패: {e}")
        # fallback: 전체 mandatory
        classified = {
            "mandatory": [{"requirement": r, "keywords": [r]} for r in qual_reqs],
            "preferred": [],
        }

    # ── Step 2: 자사 보유 자격 조회 ──
    capabilities: list[dict] = []
    if org_id:
        try:
            caps = await (
                db.table("capabilities")
                .select("id, title, type, detail, keywords")
                .eq("org_id", org_id)
                .in_("type", ["certification", "license", "registration", "track_record"])
                .execute()
            )
            capabilities = caps.data or []
        except Exception as e:
            logger.debug(f"자격 DB 조회 실패: {e}")

    # ── Step 3: 매칭 ──
    mandatory_results = []
    for m in classified.get("mandatory", []):
        kws = m.get("keywords", [m.get("requirement", "")])
        matched = _match_qualification(kws, capabilities)
        mandatory_results.append({
            "requirement": m.get("requirement", ""),
            "status": "met" if matched else "unmet",
            "matched_capability": matched["title"] if matched else None,
            "note": f"매칭: {matched['title']}" if matched else "미보유",
        })

    preferred_results = []
    for p in classified.get("preferred", []):
        kws = p.get("keywords", [p.get("requirement", "")])
        matched = _match_qualification(kws, capabilities)
        preferred_results.append({
            "requirement": p.get("requirement", ""),
            "status": "met" if matched else "unmet",
        })

    result["mandatory"] = mandatory_results
    result["preferred"] = preferred_results

    # ── Step 4: 점수 산정 ──
    total_mandatory = len(mandatory_results)
    met_mandatory = sum(1 for m in mandatory_results if m["status"] == "met")
    met_preferred = sum(1 for p in preferred_results if p["status"] == "met")
    total_preferred = len(preferred_results)

    if total_mandatory == 0:
        base = 25
    elif met_mandatory == total_mandatory:
        base = 25
    elif met_mandatory == 0:
        base = 0
        result["is_fatal"] = True
        unmet = [m["requirement"] for m in mandatory_results if m["status"] == "unmet"]
        result["fatal_reason"] = f"필수 자격 미충족: {', '.join(unmet[:3])}"
    else:
        # 부분 충족
        base = round((met_mandatory / total_mandatory) * 25)
        unmet = [m["requirement"] for m in mandatory_results if m["status"] == "unmet"]
        if any("필수" in m["requirement"] for m in mandatory_results if m["status"] == "unmet"):
            result["is_fatal"] = True
            result["fatal_reason"] = f"필수 자격 미충족: {', '.join(unmet[:3])}"

    # 가점 보너스 (최대 5점)
    pref_bonus = min(met_preferred * 2, 5) if total_preferred > 0 else 0
    result["score"] = min(base + pref_bonus, 30)
    result["summary"] = f"필수 {met_mandatory}/{total_mandatory} 충족, 가점 {met_preferred}/{total_preferred} 보유"

    return result


async def score_competition(
    rfp_dict: dict,
    org_id: str,
) -> dict:
    """축③: 경쟁 강도 분석 — 발주기관 낙찰이력 + 자사 대전 기록 (20점 만점)."""
    result: dict[str, Any] = {
        "score": 10,
        "intensity_level": "medium",
        "estimated_competitors": 5,
        "avg_competitors_same_client": None,
        "top_competitors": [],
        "our_win_rate_at_client": None,
        "our_market_share": None,
        "rationale": "",
    }

    client_name: str = rfp_dict.get("client", "")

    try:
        from app.utils.supabase_client import get_async_client
        db = await get_async_client()
    except Exception as e:
        logger.warning(f"score_competition DB 연결 실패: {e}")
        return result

    # ── Step 1: 동일 발주기관 입찰 이력 ──
    our_wins_at_client = 0
    our_total_at_client = 0
    if client_name and org_id:
        try:
            ci = await (
                db.table("client_intelligence")
                .select("id")
                .eq("org_id", org_id)
                .ilike("client_name", f"%{client_name}%")
                .limit(1)
                .execute()
            )
            if ci.data:
                client_id = ci.data[0]["id"]
                history = await (
                    db.table("client_bid_history")
                    .select("positioning, result, bid_year")
                    .eq("client_id", client_id)
                    .order("bid_year", desc=True)
                    .execute()
                )
                for h in history.data or []:
                    if h.get("result") in ("won", "lost"):
                        our_total_at_client += 1
                        if h["result"] == "won":
                            our_wins_at_client += 1

                if our_total_at_client > 0:
                    result["our_win_rate_at_client"] = our_wins_at_client / our_total_at_client
        except Exception as e:
            logger.debug(f"발주기관 이력 조회 실패: {e}")

    # ── Step 2: 예상 참여업체 수 ──
    try:
        if client_name and org_id:
            avg_q = await (
                db.table("proposal_results")
                .select("competitor_count, proposals!inner(client_name)")
                .eq("proposals.org_id", org_id)
                .ilike("proposals.client_name", f"%{client_name}%")
                .not_.is_("competitor_count", "null")
                .execute()
            )
            counts = [r["competitor_count"] for r in (avg_q.data or []) if r.get("competitor_count")]
            if counts:
                avg_comp = sum(counts) / len(counts)
                result["avg_competitors_same_client"] = round(avg_comp, 1)
                result["estimated_competitors"] = round(avg_comp)
    except Exception as e:
        logger.debug(f"평균 참여수 조회 실패: {e}")

    # ── Step 3: 경쟁사 대전 기록 ──
    try:
        if org_id:
            ch = await (
                db.table("competitor_history")
                .select("competitors!inner(company_name), our_result")
                .eq("competitors.org_id", org_id)
                .execute()
            )
            comp_stats: dict[str, dict] = {}
            for row in ch.data or []:
                name = row.get("competitors", {}).get("company_name", "")
                if not name:
                    continue
                if name not in comp_stats:
                    comp_stats[name] = {"wins": 0, "losses": 0}
                if row.get("our_result") == "won":
                    comp_stats[name]["wins"] += 1
                elif row.get("our_result") == "lost":
                    comp_stats[name]["losses"] += 1

            top = sorted(comp_stats.items(), key=lambda x: x[1]["wins"] + x[1]["losses"], reverse=True)[:5]
            result["top_competitors"] = [
                {
                    "name": name,
                    "wins_at_client": stats["wins"],
                    "head_to_head": f"{stats['wins']}승 {stats['losses']}패",
                }
                for name, stats in top
            ]
    except Exception as e:
        logger.debug(f"경쟁사 대전 기록 조회 실패: {e}")

    # ── Step 4: 점수 산정 ──
    est = result["estimated_competitors"]
    if est <= 3:
        base = 18
        result["intensity_level"] = "low"
    elif est <= 7:
        base = 12
        result["intensity_level"] = "medium"
    else:
        base = 8
        result["intensity_level"] = "high"

    adj = 0
    win_rate = result["our_win_rate_at_client"]
    if win_rate is not None:
        if win_rate >= 0.5:
            adj += 2
        elif win_rate < 0.3:
            adj -= 2

    # 점유율 (간이): 해당 기관 수주 건수 / 전체 이력 건수
    if our_total_at_client >= 3 and our_wins_at_client / our_total_at_client >= 0.3:
        result["our_market_share"] = our_wins_at_client / our_total_at_client
        adj += 2

    result["score"] = max(0, min(base + adj, 20))
    result["rationale"] = (
        f"예상 {est}개사 참여 ({result['intensity_level']}), "
        f"자사 기관 내 {our_wins_at_client}승/{our_total_at_client}전"
    )
    return result
