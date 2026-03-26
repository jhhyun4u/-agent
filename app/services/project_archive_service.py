"""
프로젝트 아카이브 서비스 — 중간 산출물 파일화 + Storage 저장 + manifest 관리.

LangGraph state에서 중간 산출물을 추출하여 Markdown/텍스트 파일로 변환,
Supabase Storage에 업로드하고 project_archive 테이블에 등록.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

BUCKET = settings.storage_bucket_proposals

# ═══════════════════════════════════════════
# 산출물 정의 레지스트리
# ═══════════════════════════════════════════

ARCHIVE_DEFS: list[dict] = [
    # ── RFP ──
    {
        "doc_type": "rfp_raw_text",
        "category": "rfp",
        "title": "RFP 원문 텍스트",
        "file_format": "txt",
        "state_key": "rfp_raw",
        "graph_step": "rfp_fetch",
        "storage_subpath": "rfp/rfp_raw.txt",
    },
    # ── 분석 ──
    {
        "doc_type": "rfp_analysis",
        "category": "analysis",
        "title": "RFP 분석 결과",
        "file_format": "md",
        "state_key": "rfp_analysis",
        "graph_step": "rfp_analyze",
        "storage_subpath": "analysis/rfp_analysis.md",
        "renderer": "_render_rfp_analysis",
    },
    {
        "doc_type": "compliance_matrix",
        "category": "analysis",
        "title": "Compliance Matrix",
        "file_format": "md",
        "state_key": "compliance_matrix",
        "graph_step": "rfp_analyze",
        "storage_subpath": "analysis/compliance_matrix.md",
        "renderer": "_render_compliance_matrix",
    },
    {
        "doc_type": "go_no_go",
        "category": "analysis",
        "title": "Go/No-Go 의사결정",
        "file_format": "md",
        "state_key": "go_no_go",
        "graph_step": "go_no_go",
        "storage_subpath": "analysis/go_no_go.md",
        "renderer": "_render_go_no_go",
    },
    {
        "doc_type": "research_brief",
        "category": "analysis",
        "title": "리서치 브리프",
        "file_format": "md",
        "state_key": "research_brief",
        "graph_step": "research_gather",
        "storage_subpath": "analysis/research_brief.md",
        "renderer": "_render_json_as_md",
    },
    # ── 전략 ──
    {
        "doc_type": "strategy",
        "category": "strategy",
        "title": "제안전략",
        "file_format": "md",
        "state_key": "strategy",
        "graph_step": "strategy_generate",
        "storage_subpath": "strategy/strategy.md",
        "renderer": "_render_strategy",
    },
    {
        "doc_type": "bid_plan",
        "category": "strategy",
        "title": "입찰가격계획",
        "file_format": "md",
        "state_key": "bid_plan",
        "graph_step": "bid_plan",
        "storage_subpath": "strategy/bid_plan.md",
        "renderer": "_render_bid_plan",
    },
    {
        "doc_type": "evaluation_simulation",
        "category": "strategy",
        "title": "모의평가 시뮬레이션",
        "file_format": "md",
        "state_key": "evaluation_simulation",
        "graph_step": "self_review",
        "storage_subpath": "strategy/evaluation_simulation.md",
        "renderer": "_render_json_as_md",
    },
    # ── 계획 ──
    {
        "doc_type": "team_plan",
        "category": "plan",
        "title": "투입인력 계획",
        "file_format": "md",
        "state_key": "plan",
        "sub_key": "team",
        "graph_step": "plan_team",
        "storage_subpath": "plan/team_plan.md",
        "renderer": "_render_plan_section",
    },
    {
        "doc_type": "schedule",
        "category": "plan",
        "title": "일정 계획",
        "file_format": "md",
        "state_key": "plan",
        "sub_key": "schedule",
        "graph_step": "plan_schedule",
        "storage_subpath": "plan/schedule.md",
        "renderer": "_render_plan_section",
    },
    {
        "doc_type": "storyline",
        "category": "plan",
        "title": "스토리라인",
        "file_format": "md",
        "state_key": "plan",
        "sub_key": "storylines",
        "graph_step": "plan_story",
        "storage_subpath": "plan/storyline.md",
        "renderer": "_render_storyline",
    },
    {
        "doc_type": "price_plan",
        "category": "plan",
        "title": "가격 계획",
        "file_format": "md",
        "state_key": "plan",
        "sub_key": "bid_price",
        "graph_step": "plan_price",
        "storage_subpath": "plan/price_plan.md",
        "renderer": "_render_plan_section",
    },
    # ── 제안서 ──
    {
        "doc_type": "proposal_full_md",
        "category": "proposal",
        "title": "제안서 (Markdown 원본)",
        "file_format": "md",
        "state_key": "proposal_sections",
        "graph_step": "proposal_write",
        "storage_subpath": "proposal/proposal_full.md",
        "renderer": "_render_proposal_sections",
    },
    # ── 발표 ──
    {
        "doc_type": "ppt_slides_md",
        "category": "presentation",
        "title": "PPT 슬라이드 (Markdown 원본)",
        "file_format": "md",
        "state_key": "ppt_slides",
        "graph_step": "ppt_slide",
        "storage_subpath": "presentation/ppt_slides.md",
        "renderer": "_render_ppt_slides",
    },
    {
        "doc_type": "presentation_strategy",
        "category": "presentation",
        "title": "발표전략",
        "file_format": "md",
        "state_key": "presentation_strategy",
        "graph_step": "presentation_strategy",
        "storage_subpath": "presentation/presentation_strategy.md",
        "renderer": "_render_json_as_md",
    },
    # ── 리뷰 ──
    {
        "doc_type": "feedback_history",
        "category": "review",
        "title": "리뷰 피드백 이력",
        "file_format": "md",
        "state_key": "feedback_history",
        "graph_step": "review",
        "storage_subpath": "review/feedback_history.md",
        "renderer": "_render_feedback_history",
    },
]

# doc_type → def 매핑
_DEF_MAP = {d["doc_type"]: d for d in ARCHIVE_DEFS}


# ═══════════════════════════════════════════
# Markdown 렌더러들
# ═══════════════════════════════════════════

def _to_dict(obj: Any) -> Any:
    """Pydantic 모델 또는 dict를 dict로 변환."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def _render_rfp_analysis(data: Any) -> str:
    """RFP 분석 결과 → 제안전략 수립 기초자료 MD 보고서."""
    d = _to_dict(data)
    lines: list[str] = ["# RFP 분석 보고서 — 제안전략 수립 기초자료", ""]

    # ── 1. 사업 개요 ──
    lines.append("## 1. 사업 개요\n")
    lines.append("| 항목 | 내용 |")
    lines.append("|------|------|")
    overview = [
        ("사업명", d.get("project_name", "")),
        ("발주기관", d.get("client", "")),
        ("사업 분류", d.get("domain", "") or "(미분류)"),
        ("예산", d.get("budget", "") or "(미명시)"),
        ("수행 기간", d.get("duration", "") or "(미명시)"),
        ("마감일", d.get("deadline", "")),
        ("계약 유형", d.get("contract_type", "") or "(미명시)"),
        ("케이스 유형", f"{d.get('case_type', 'A')} ({'자유양식' if d.get('case_type') == 'A' else '지정서식'})"),
        ("평가 방식", d.get("eval_method", "") or "(미명시)"),
    ]
    for label, value in overview:
        lines.append(f"| {label} | {value} |")

    # ── 2. 사업 범위 ──
    lines.append("\n## 2. 사업 범위\n")
    scope = d.get("project_scope", "")
    lines.append(scope if scope else "(RFP에 미명시)")

    # ── 3. 평가 구조 ──
    lines.append("\n## 3. 평가 구조\n")
    tpr = d.get("tech_price_ratio", {})
    if tpr:
        lines.append(f"- **기술 : 가격 = {tpr.get('tech', '?')} : {tpr.get('price', '?')}**\n")
    eval_items = d.get("eval_items", [])
    if eval_items:
        lines.append("| 평가항목 | 배점 | 세부항목 |")
        lines.append("|----------|------|----------|")
        for item in eval_items:
            name = item.get("item", "") if isinstance(item, dict) else str(item)
            weight = item.get("weight", "") if isinstance(item, dict) else ""
            subs = ", ".join(item.get("sub_items", [])) if isinstance(item, dict) else ""
            lines.append(f"| {name} | {weight} | {subs} |")
    else:
        lines.append("(평가항목 미추출)")

    # ── 4. 가격평가 산식 ──
    lines.append("\n## 4. 가격평가 산식\n")
    ps = d.get("price_scoring")
    if ps and isinstance(ps, dict) and ps.get("formula_type"):
        lines.append(f"- 산식 유형: **{ps.get('formula_type', '')}**")
        lines.append(f"- 설명: {ps.get('description', '')}")
        lines.append(f"- 가격 배점: {ps.get('price_weight', 0)}점")
        params = ps.get("parameters", {})
        if params:
            lines.append(f"- 파라미터: {json.dumps(params, ensure_ascii=False)}")
    else:
        lines.append("(RFP에 가격평가 산식 미명시 — 표준 공식 적용)")

    # ── 5. 핫버튼 ──
    lines.append("\n## 5. 핫버튼 (발주처 핵심 관심사)\n")
    for hb in d.get("hot_buttons", []):
        lines.append(f"- {hb}")
    if not d.get("hot_buttons"):
        lines.append("(미추출)")

    # ── 6. 필수 요구사항 ──
    lines.append("\n## 6. 필수 요구사항 (미충족 시 탈락)\n")
    for req in d.get("mandatory_reqs", []):
        lines.append(f"- {req}")
    if not d.get("mandatory_reqs"):
        lines.append("(미추출)")

    # ── 7. 업체 자격 요건 ──
    lines.append("\n## 7. 업체 자격 요건\n")
    quals = d.get("qualification_requirements", [])
    if quals:
        for q in quals:
            lines.append(f"- {q}")
    else:
        lines.append("(RFP에 미명시)")

    # ── 8. 유사 수행실적 요건 ──
    lines.append("\n## 8. 유사 수행실적 요건\n")
    similar = d.get("similar_project_requirements", [])
    if similar:
        for s in similar:
            lines.append(f"- {s}")
    else:
        lines.append("(RFP에 미명시)")

    # ── 9. 핵심인력 요건 ──
    lines.append("\n## 9. 핵심인력 요건\n")
    personnel = d.get("key_personnel_requirements", [])
    if personnel:
        lines.append("| 역할 | 등급 | 자격/인증 |")
        lines.append("|------|------|-----------|")
        for p in personnel:
            if isinstance(p, dict):
                role = p.get("role", "")
                grade = p.get("grade", "")
                certs = ", ".join(p.get("certifications", [])) if isinstance(p.get("certifications"), list) else str(p.get("certifications", ""))
                lines.append(f"| {role} | {grade} | {certs} |")
            else:
                lines.append(f"| {p} | | |")
    else:
        lines.append("(RFP에 미명시)")

    # ── 10. 수행 단계 및 마일스톤 ──
    lines.append("\n## 10. 수행 단계 및 마일스톤\n")
    phases = d.get("delivery_phases", [])
    if phases:
        lines.append("| 단계 | 기간 | 산출물 |")
        lines.append("|------|------|--------|")
        for ph in phases:
            if isinstance(ph, dict):
                name = ph.get("phase", "")
                period = ph.get("period", "")
                delivs = ", ".join(ph.get("deliverables", [])) if isinstance(ph.get("deliverables"), list) else str(ph.get("deliverables", ""))
                lines.append(f"| {name} | {period} | {delivs} |")
    else:
        lines.append("(RFP에 미명시)")

    # ── 11. 서식 템플릿 ──
    lines.append("\n## 11. 서식 템플릿\n")
    ft = d.get("format_template", {})
    if ft and ft.get("exists"):
        lines.append("- **지정 서식 있음** (케이스 B)")
        structure = ft.get("structure")
        if structure and isinstance(structure, dict):
            for k, v in structure.items():
                lines.append(f"  - {k}: {v}")
    else:
        lines.append("- 자유양식 (케이스 A)")

    # ── 12. 분량 규격 ──
    lines.append("\n## 12. 분량 규격\n")
    vs = d.get("volume_spec", {})
    if vs:
        for k, v in (vs.items() if isinstance(vs, dict) else []):
            lines.append(f"- {k}: {v}")
    else:
        lines.append("(미명시)")

    # ── 13. 하도급 조건 ──
    lines.append("\n## 13. 하도급 조건\n")
    subs = d.get("subcontracting_conditions", [])
    if subs:
        for s in subs:
            lines.append(f"- {s}")
    else:
        lines.append("(RFP에 미명시)")

    # ── 14. 특수 조건 ──
    lines.append("\n## 14. 특수 조건\n")
    for sc in d.get("special_conditions", []):
        lines.append(f"- {sc}")
    if not d.get("special_conditions"):
        lines.append("(없음)")

    return "\n".join(lines)


def _render_compliance_matrix(data: Any) -> str:
    items = data if isinstance(data, list) else []
    lines = [
        "# Compliance Matrix",
        "",
        "| 요구사항 ID | 내용 | 출처 | 상태 | 제안서 섹션 |",
        "|------------|------|------|------|------------|",
    ]
    for item in items:
        d = _to_dict(item)
        lines.append(
            f"| {d.get('req_id', '')} | {d.get('content', '')[:60]} | "
            f"{d.get('source_step', '')} | {d.get('status', '')} | {d.get('proposal_section', '')} |"
        )
    return "\n".join(lines)


def _render_go_no_go(data: Any) -> str:
    d = _to_dict(data)
    lines = [
        "# Go/No-Go 의사결정",
        f"\n## 판정: **{d.get('recommendation', '').upper()}**",
        f"- 포지셔닝: {d.get('positioning', '')}",
        f"- 포지셔닝 근거: {d.get('positioning_rationale', '')}",
        f"- 타당성 점수: {d.get('feasibility_score', 0)}점",
        f"- 의사결정: {d.get('decision', '')}",
    ]
    if d.get("fatal_flaw"):
        lines.append(f"- **치명적 결함**: {d['fatal_flaw']}")
    lines.append("\n## 점수 내역")
    for k, v in d.get("score_breakdown", {}).items():
        lines.append(f"- {k}: {v}")
    lines.append("\n## 장점")
    for p in d.get("pros", []):
        lines.append(f"- {p}")
    lines.append("\n## 리스크")
    for r in d.get("risks", []):
        lines.append(f"- {r}")
    return "\n".join(lines)


def _render_strategy(data: Any) -> str:
    d = _to_dict(data)
    lines = [
        "# 제안전략",
        f"\n## 포지셔닝: {d.get('positioning', '')}",
        f"- 근거: {d.get('positioning_rationale', '')}",
        f"- Win Theme: {d.get('win_theme', '')}",
        f"- Ghost Theme: {d.get('ghost_theme', '')}",
        f"- Action Forcing Event: {d.get('action_forcing_event', '')}",
        "\n## 핵심 메시지",
    ]
    for msg in d.get("key_messages", []):
        lines.append(f"- {msg}")
    lines.append("\n## 가격전략")
    lines.append(f"```json\n{json.dumps(d.get('price_strategy', {}), ensure_ascii=False, indent=2)}\n```")
    lines.append("\n## 경쟁사 분석")
    lines.append(f"```json\n{json.dumps(d.get('competitor_analysis', {}), ensure_ascii=False, indent=2)}\n```")
    lines.append("\n## 리스크")
    for r in d.get("risks", []):
        lines.append(f"- {json.dumps(r, ensure_ascii=False)}")
    lines.append("\n## 전략 대안")
    for alt in d.get("alternatives", []):
        a = _to_dict(alt) if hasattr(alt, "model_dump") else alt
        lines.append(f"\n### 대안 {a.get('alt_id', '')}")
        lines.append(f"- Win Theme: {a.get('win_theme', '')}")
        lines.append(f"- Ghost Theme: {a.get('ghost_theme', '')}")
    return "\n".join(lines)


def _render_bid_plan(data: Any) -> str:
    d = _to_dict(data)
    lines = [
        "# 입찰가격계획",
        f"\n- 추천 입찰가: {d.get('recommended_bid', 0):,}원",
        f"- 추천 비율: {d.get('recommended_ratio', 0):.1%}",
        f"- 낙찰 확률: {d.get('win_probability', 0):.1%}",
        f"- 데이터 품질: {d.get('data_quality', '')}",
    ]
    if d.get("user_override_price"):
        lines.append(f"- **사용자 지정가**: {d['user_override_price']:,}원 ({d.get('user_override_reason', '')})")
    lines.append("\n## 시나리오")
    for s in d.get("scenarios", []):
        lines.append(f"- {json.dumps(s, ensure_ascii=False)}")
    lines.append("\n## 원가 내역")
    lines.append(f"```json\n{json.dumps(d.get('cost_breakdown', {}), ensure_ascii=False, indent=2)}\n```")
    lines.append("\n## 시장 컨텍스트")
    lines.append(f"```json\n{json.dumps(d.get('market_context', {}), ensure_ascii=False, indent=2)}\n```")
    return "\n".join(lines)


def _render_plan_section(data: Any, sub_key: str = "") -> str:
    d = _to_dict(data)
    section_data = d.get(sub_key, d) if sub_key else d
    title_map = {
        "team": "투입인력 계획", "schedule": "일정 계획",
        "bid_price": "가격 계획", "deliverables": "산출물 계획",
    }
    title = title_map.get(sub_key, sub_key or "계획")
    if isinstance(section_data, (dict, list)):
        return f"# {title}\n\n```json\n{json.dumps(section_data, ensure_ascii=False, indent=2)}\n```"
    return f"# {title}\n\n{section_data}"


def _render_storyline(data: Any, sub_key: str = "") -> str:
    d = _to_dict(data)
    sl = d.get("storylines", d) if isinstance(d, dict) else d
    if isinstance(sl, dict):
        lines = ["# 스토리라인"]
        for sec_key, sec_val in sl.items():
            if isinstance(sec_val, dict):
                lines.append(f"\n## {sec_key}")
                for field, value in sec_val.items():
                    if isinstance(value, list):
                        lines.append(f"- **{field}**:")
                        for item in value:
                            lines.append(f"  - {item}")
                    else:
                        lines.append(f"- **{field}**: {value}")
            else:
                lines.append(f"\n## {sec_key}: {sec_val}")
        return "\n".join(lines)
    return f"# 스토리라인\n\n```json\n{json.dumps(sl, ensure_ascii=False, indent=2)}\n```"


def _render_proposal_sections(data: Any) -> str:
    if not data:
        return "# 제안서\n\n(섹션 없음)"
    lines = ["# 제안서 (전문)"]
    sections = data if isinstance(data, list) else [data]
    for sec in sections:
        d = _to_dict(sec)
        lines.append(f"\n---\n## {d.get('title', '제목 없음')}")
        lines.append(f"<!-- section_id: {d.get('section_id', '')} | case: {d.get('case_type', '')} | v{d.get('version', 1)} -->")
        lines.append(d.get("content", ""))
    return "\n".join(lines)


def _render_ppt_slides(data: Any) -> str:
    if not data:
        return "# PPT 슬라이드\n\n(슬라이드 없음)"
    lines = ["# PPT 슬라이드"]
    slides = data if isinstance(data, list) else [data]
    for slide in slides:
        d = _to_dict(slide)
        lines.append(f"\n---\n## 슬라이드: {d.get('title', '')}")
        lines.append(d.get("content", ""))
        if d.get("notes"):
            lines.append(f"\n> 발표자 노트: {d['notes']}")
    return "\n".join(lines)


def _render_feedback_history(data: Any) -> str:
    if not data:
        return "# 리뷰 피드백 이력\n\n(피드백 없음)"
    lines = ["# 리뷰 피드백 이력"]
    for i, fb in enumerate(data, 1):
        d = _to_dict(fb)
        lines.append(f"\n## 피드백 #{i}")
        for k, v in d.items():
            lines.append(f"- **{k}**: {v}")
    return "\n".join(lines)


def _render_json_as_md(data: Any) -> str:
    d = _to_dict(data)
    return f"```json\n{json.dumps(d, ensure_ascii=False, indent=2)}\n```"


# 렌더러 매핑
_RENDERERS = {
    "_render_rfp_analysis": _render_rfp_analysis,
    "_render_compliance_matrix": _render_compliance_matrix,
    "_render_go_no_go": _render_go_no_go,
    "_render_strategy": _render_strategy,
    "_render_bid_plan": _render_bid_plan,
    "_render_plan_section": _render_plan_section,
    "_render_storyline": _render_storyline,
    "_render_proposal_sections": _render_proposal_sections,
    "_render_ppt_slides": _render_ppt_slides,
    "_render_feedback_history": _render_feedback_history,
    "_render_json_as_md": _render_json_as_md,
}


# ═══════════════════════════════════════════
# 핵심 서비스 함수
# ═══════════════════════════════════════════

def render_artifact(definition: dict, state: dict) -> str | None:
    """State에서 산출물을 추출하여 텍스트로 렌더링.

    Returns: 렌더링된 텍스트 또는 None (데이터 없음).
    """
    state_key = definition["state_key"]
    raw = state.get(state_key)
    if raw is None:
        return None

    # sub_key 처리 (plan.team, plan.schedule 등)
    sub_key = definition.get("sub_key")
    if sub_key:
        d = _to_dict(raw)
        if isinstance(d, dict) and sub_key not in d:
            return None

    renderer_name = definition.get("renderer")
    if renderer_name and renderer_name in _RENDERERS:
        renderer = _RENDERERS[renderer_name]
        if sub_key:
            return renderer(raw, sub_key=sub_key)
        return renderer(raw)

    # 기본: 문자열 또는 JSON
    if isinstance(raw, str):
        return raw
    return json.dumps(_to_dict(raw), ensure_ascii=False, indent=2)


async def archive_artifact(
    proposal_id: str,
    doc_type: str,
    content: str | bytes,
    *,
    created_by: str | None = None,
    source: str = "ai",
) -> dict:
    """단일 산출물을 Storage에 업로드하고 project_archive에 등록.

    Returns: 등록된 archive 레코드.
    """
    definition = _DEF_MAP.get(doc_type)
    if not definition:
        raise ValueError(f"알 수 없는 doc_type: {doc_type}")

    client = await get_async_client()
    storage_path = f"{proposal_id}/{definition['storage_subpath']}"

    # 바이트 변환
    if isinstance(content, str):
        file_bytes = content.encode("utf-8")
    else:
        file_bytes = content

    content_type_map = {
        "md": "text/markdown; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
        "json": "application/json; charset=utf-8",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hwpx": "application/hwp+zip",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    ct = content_type_map.get(definition["file_format"], "application/octet-stream")

    # Storage 업로드
    try:
        await client.storage.from_(BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": ct, "upsert": "true"},
        )
    except Exception as e:
        logger.warning(f"[{proposal_id}] archive upload 실패 ({doc_type}): {e}")
        storage_path = None  # 업로드 실패해도 DB 기록은 남김

    # 기존 latest 해제
    await client.table("project_archive").update(
        {"is_latest": False}
    ).eq("proposal_id", proposal_id).eq("doc_type", doc_type).eq("is_latest", True).execute()

    # 버전 조회
    ver_res = await client.table("project_archive").select("version").eq(
        "proposal_id", proposal_id
    ).eq("doc_type", doc_type).order("version", desc=True).limit(1).execute()
    next_version = ((ver_res.data or [{}])[0].get("version") or 0) + 1

    # 신규 레코드 삽입
    row = {
        "proposal_id": proposal_id,
        "category": definition["category"],
        "doc_type": doc_type,
        "title": definition["title"],
        "file_format": definition["file_format"],
        "storage_path": storage_path,
        "file_size": len(file_bytes),
        "version": next_version,
        "is_latest": True,
        "source": source,
        "graph_step": definition.get("graph_step"),
        "created_by": created_by,
    }
    result = await client.table("project_archive").insert(row).execute()
    record = (result.data or [{}])[0]
    logger.info(f"[{proposal_id}] archived {doc_type} v{next_version} ({len(file_bytes)} bytes)")
    return record


async def archive_binary_artifact(
    proposal_id: str,
    doc_type: str,
    category: str,
    title: str,
    file_format: str,
    file_bytes: bytes,
    storage_subpath: str,
    *,
    graph_step: str = "",
    created_by: str | None = None,
    source: str = "ai",
) -> dict:
    """바이너리 산출물(DOCX, PPTX, HWPX 등)을 아카이브에 등록."""
    client = await get_async_client()
    storage_path = f"{proposal_id}/{storage_subpath}"

    content_type_map = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hwpx": "application/hwp+zip",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    ct = content_type_map.get(file_format, "application/octet-stream")

    try:
        await client.storage.from_(BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": ct, "upsert": "true"},
        )
    except Exception as e:
        logger.warning(f"[{proposal_id}] binary archive upload 실패 ({doc_type}): {e}")
        storage_path = None

    # 기존 latest 해제
    await client.table("project_archive").update(
        {"is_latest": False}
    ).eq("proposal_id", proposal_id).eq("doc_type", doc_type).eq("is_latest", True).execute()

    ver_res = await client.table("project_archive").select("version").eq(
        "proposal_id", proposal_id
    ).eq("doc_type", doc_type).order("version", desc=True).limit(1).execute()
    next_version = ((ver_res.data or [{}])[0].get("version") or 0) + 1

    row = {
        "proposal_id": proposal_id,
        "category": category,
        "doc_type": doc_type,
        "title": title,
        "file_format": file_format,
        "storage_path": storage_path,
        "file_size": len(file_bytes),
        "version": next_version,
        "is_latest": True,
        "source": source,
        "graph_step": graph_step,
        "created_by": created_by,
    }
    result = await client.table("project_archive").insert(row).execute()
    record = (result.data or [{}])[0]
    logger.info(f"[{proposal_id}] archived binary {doc_type} v{next_version} ({len(file_bytes)} bytes)")
    return record


async def snapshot_from_state(
    proposal_id: str,
    state: dict,
    *,
    created_by: str | None = None,
) -> list[dict]:
    """현재 LangGraph state에서 모든 중간 산출물을 파일화하여 아카이브.

    Returns: 아카이브된 레코드 목록.
    """
    archived = []
    for defn in ARCHIVE_DEFS:
        try:
            content = render_artifact(defn, state)
            if content is None:
                continue
            record = await archive_artifact(
                proposal_id,
                defn["doc_type"],
                content,
                created_by=created_by,
                source="ai",
            )
            archived.append(record)
        except Exception as e:
            logger.warning(f"[{proposal_id}] snapshot 실패 ({defn['doc_type']}): {e}")

    # snapshot 타임스탬프 기록
    if archived:
        try:
            client = await get_async_client()
            await client.table("proposals").update({
                "archive_snapshot_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", proposal_id).execute()
        except Exception as e:
            logger.warning(f"[{proposal_id}] snapshot timestamp 갱신 실패: {e}")

    logger.info(f"[{proposal_id}] snapshot 완료: {len(archived)}개 산출물 아카이브됨")
    return archived


async def get_project_manifest(proposal_id: str) -> dict:
    """프로젝트 마스터 파일 일람 (모든 카테고리 통합).

    Returns: {categories, files, total_count, total_size}
    """
    client = await get_async_client()

    # project_archive (최신 버전만)
    archive_res = await client.table("project_archive").select(
        "id, category, doc_type, title, file_format, storage_path, "
        "file_size, version, source, graph_step, created_by, created_at"
    ).eq("proposal_id", proposal_id).eq("is_latest", True).order("category").execute()
    archive_files = archive_res.data or []

    # proposal_files (참고자료 등)
    pf_res = await client.table("proposal_files").select(
        "id, category, filename, storage_path, file_type, file_size, "
        "uploaded_by, description, created_at"
    ).eq("proposal_id", proposal_id).order("created_at", desc=True).execute()
    ref_files = pf_res.data or []

    # submission_documents (제출서류)
    sd_res = await client.table("submission_documents").select(
        "id, doc_type, doc_category, file_path, file_name, file_size, "
        "file_format, status, created_at"
    ).eq("proposal_id", proposal_id).order("sort_order").execute()
    sub_docs = sd_res.data or []

    # 카테고리별 그룹화
    categories: dict[str, list] = {}
    total_size = 0

    for f in archive_files:
        cat = f.get("category", "etc")
        categories.setdefault(cat, []).append({
            **f, "_source_table": "project_archive",
        })
        total_size += f.get("file_size") or 0

    for f in ref_files:
        categories.setdefault("reference", []).append({
            "id": f["id"],
            "doc_type": f["category"],
            "title": f["filename"],
            "file_format": f.get("file_type", ""),
            "storage_path": f["storage_path"],
            "file_size": f.get("file_size"),
            "description": f.get("description"),
            "created_at": f.get("created_at"),
            "_source_table": "proposal_files",
        })
        total_size += f.get("file_size") or 0

    for f in sub_docs:
        if f.get("file_path"):
            categories.setdefault("submission", []).append({
                "id": f["id"],
                "doc_type": f["doc_type"],
                "title": f.get("file_name") or f["doc_type"],
                "file_format": f.get("file_format", ""),
                "storage_path": f["file_path"],
                "file_size": f.get("file_size"),
                "status": f.get("status"),
                "created_at": f.get("created_at"),
                "_source_table": "submission_documents",
            })
            total_size += f.get("file_size") or 0

    all_files = archive_files + ref_files + [d for d in sub_docs if d.get("file_path")]
    return {
        "proposal_id": proposal_id,
        "categories": categories,
        "total_count": len(all_files),
        "total_size": total_size,
    }
