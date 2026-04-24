"""
STEP 1-①: RFP 분석 + Compliance Matrix 초안 (§6)

RFP 텍스트를 분석하여 구조화된 분석 결과 생성.
"""

import logging
import re

from app.graph.state import ComplianceItem, PriceScoringFormula, ProposalState, RFPAnalysis
from app.services.core.claude_client import claude_generate
from app.services import prompt_tracker

logger = logging.getLogger(__name__)

# 대형 RFP 처리 설정
_RFP_HARD_LIMIT = 30_000
_RFP_EXTRACTION_KEYWORDS = {
    "평가기준", "평가항목", "심사항목",
    "과업범위", "사업범위", "업무범위",
    "자격요건", "필수요건", "참여자격",
    "기술요건", "기술기준",
    "제안서양식", "제안서형식",
    "가격평가", "가격기준",
}


async def _prepare_rfp_text(rfp_raw: str) -> str:
    """대형 RFP 전처리: 30,000자 초과 시 핵심 섹션 우선 추출.

    2-pass 처리:
    1. Pass 1: 첫 8,000자로 목차/구조 파악
    2. Pass 2: 키워드 기반 핵심 섹션 추출 및 재조합
    """
    if len(rfp_raw) <= _RFP_HARD_LIMIT:
        return rfp_raw

    logger.info(f"대형 RFP 감지 ({len(rfp_raw):,}자). 핵심 섹션 추출 시작...")

    # ── Pass 1: 구조 파악 (첫 8,000자) ──
    initial_text = rfp_raw[:8000]
    lines = rfp_raw.split("\n")

    # ── Pass 2: 핵심 키워드 기반 섹션 추출 ──
    sections = []
    current_section = []
    current_section_length = 0
    target_length = _RFP_HARD_LIMIT - len(initial_text) - 500  # 헤더, 마진 예약

    for i, line in enumerate(lines):
        # 키워드 라인 감지
        is_keyword_match = any(kw in line for kw in _RFP_EXTRACTION_KEYWORDS)

        if is_keyword_match and current_section:
            # 현재 섹션 저장
            section_text = "\n".join(current_section)
            if len(section_text) > 100:
                sections.append(section_text)
            current_section = [line]
            current_section_length = len(line)
        else:
            current_section.append(line)
            current_section_length += len(line) + 1

        # 섹션 크기 제한 (3000자)
        if current_section_length > 3000:
            section_text = "\n".join(current_section)
            if len(section_text) > 100:
                sections.append(section_text)
            current_section = []
            current_section_length = 0

        # 목표 길이 도달 확인
        if sum(len(s) for s in sections) >= target_length:
            break

    # 마지막 섹션
    if current_section:
        section_text = "\n".join(current_section)
        if len(section_text) > 100:
            sections.append(section_text)

    # 재조합
    combined = initial_text + "\n\n" + "\n\n".join(sections)
    result = combined[:_RFP_HARD_LIMIT]

    logger.info(f"대형 RFP 추출 완료: {len(result):,}자 (원본 {len(rfp_raw):,}자에서 {len(result)/len(rfp_raw)*100:.1f}%)")
    return result


async def rfp_analyze(state: ProposalState) -> dict:
    """STEP 1-①: RFP 분석 + Compliance Matrix 초안 생성."""

    rfp_raw = state.get("rfp_raw", "")
    if not rfp_raw:
        return {
            "current_step": "rfp_analyze_error",
            "node_errors": {
                **state.get("node_errors", {}),
                "rfp_analyze": {
                    "error": "rfp_raw가 비어 있어 RFP 분석 수행 불가",
                    "step": "rfp_analyze",
                    "hint": "RFP 문서가 정상적으로 파싱되었는지 확인하세요.",
                },
            },
        }

    bid_detail = state.get("bid_detail")
    bid_context = ""
    if bid_detail:
        bid_context = f"""
## 공고 기본 정보
- 공고번호: {bid_detail.bid_no}
- 사업명: {bid_detail.project_name}
- 발주기관: {bid_detail.client}
- 예산: {bid_detail.budget}
- 마감일: {bid_detail.deadline}
"""

    # 대형 RFP 전처리 (30,000자 초과 시 핵심 섹션 우선 추출)
    rfp_processed = await _prepare_rfp_text(rfp_raw)

    prompt = f"""다음 RFP 문서를 분석하여 제안전략 수립에 필요한 기초자료를 빠짐없이 추출하세요.

{bid_context}

## RFP 원문
{rfp_processed}

## 분석 요구사항
1. 사업 유형 판단: 케이스 A (자유양식) vs 케이스 B (지정 서식)
2. 평가 항목 + 배점 역설계 (세부항목까지)
3. 기술:가격 비중
4. Hot Buttons (발주처 핵심 관심사)
5. 필수 요건 (불충족 시 탈락하는 제안서 수준 요건)
6. 서식 템플릿 존재 여부 + 구조
7. 분량 규격
8. 특수 조건
9. 평가방식 (종합심사, 적격심사, 최저가, 수의계약 등)
10. **가격점수 산정 방식** — RFP에 가격평가 산식이 명시되어 있으면 반드시 추출할 것
    - formula_type: "lowest_ratio" | "fixed_rate" | "budget_ratio" | "custom"
    - description: RFP 원문 발췌
    - price_weight: 가격 배점
    - parameters: 산식 추가 값
    - RFP에 가격점수 산식이 없으면 null
11. **사업 분류(domain)**: SI/SW개발, 컨설팅, 감리, 인프라구축, 운영유지보수, 기타
12. **사업 범위 요약**: 과업 내용을 3~5문장으로 요약
13. **예산**: RFP에 명시된 사업 예산 (원문 발췌, 없으면 "미명시")
14. **수행 기간**: 전체 사업 기간 (예: "12개월", "2026.07~2027.06")
15. **계약 유형**: 정액, 실비정산, T&M 등
16. **수행 단계 + 마일스톤**: 단계별 기간, 산출물, 검수 포인트
17. **업체 자격 요건**: 입찰 참가 자격 (업체 등록, 인증, 매출 기준 등)
18. **유사 수행실적 요건**: 과거 유사 사업 수행 실적 요구사항
19. **핵심인력 요건**: 역할별 필수 등급, 자격증, 경력 조건
20. **하도급 조건**: 하도급 허용 여부, 비율 제한, 특수 조건

## 출력 형식 (JSON)
{{
  "project_name": "사업명",
  "client": "발주기관",
  "deadline": "마감일",
  "case_type": "A 또는 B",
  "eval_method": "종합심사 | 적격심사 | 최저가 | 수의계약",
  "eval_items": [{{"item": "항목명", "weight": 30, "sub_items": ["세부항목"]}}],
  "tech_price_ratio": {{"tech": 90, "price": 10}},
  "hot_buttons": ["핫버튼 키워드"],
  "mandatory_reqs": ["필수 요건"],
  "format_template": {{"exists": false, "structure": null}},
  "volume_spec": {{"max_pages": 100, "font_size": "11pt"}},
  "special_conditions": ["특수 조건"],
  "price_scoring": {{
    "formula_type": "lowest_ratio",
    "description": "가격점수 = 가격배점 × (최저입찰가격/입찰가격)",
    "price_weight": 10,
    "parameters": {{}}
  }},
  "domain": "SI/SW개발",
  "project_scope": "사업 범위 요약 (3~5문장)",
  "budget": "예산 금액 원문 발췌",
  "duration": "수행기간",
  "contract_type": "정액 | 실비정산 | T&M | 기타",
  "delivery_phases": [{{"phase": "단계명", "period": "기간", "deliverables": ["산출물"]}}],
  "qualification_requirements": ["업체 자격 요건"],
  "similar_project_requirements": ["유사 실적 요건"],
  "key_personnel_requirements": [{{"role": "역할", "grade": "등급", "certifications": ["자격"]}}],
  "subcontracting_conditions": ["하도급 조건"],
  "compliance_items": [
    {{"req_id": "RFP-001", "content": "요건 내용", "source_step": "rfp_analyze"}}
  ]
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
                artifact_step="rfp_analyze",
                section_id=None,
                prompt_id="_inline.rfp_analyze",
                prompt_version=0,
                prompt_hash=hashlib.sha256(prompt[:500].encode()).hexdigest(),
            )
        except Exception as e:
            logger.debug(f"프롬프트 트래커 기록 실패 (무시): {e}")

    # RFP 분석 결과 구성
    rfp_analysis = RFPAnalysis(
        project_name=result.get("project_name", state.get("project_name", "")),
        client=result.get("client", ""),
        deadline=result.get("deadline", ""),
        case_type=result.get("case_type", "A"),
        eval_method=result.get("eval_method", ""),
        eval_items=result.get("eval_items", []),
        tech_price_ratio=result.get("tech_price_ratio", {"tech": 90, "price": 10}),
        hot_buttons=result.get("hot_buttons", []),
        mandatory_reqs=result.get("mandatory_reqs", []),
        format_template=result.get("format_template", {"exists": False, "structure": None}),
        volume_spec=result.get("volume_spec", {}),
        special_conditions=result.get("special_conditions", []),
        price_scoring=PriceScoringFormula(**result["price_scoring"]) if result.get("price_scoring") else None,
        # v3.9 확장 필드
        domain=result.get("domain", ""),
        project_scope=result.get("project_scope", ""),
        budget=result.get("budget", bid_detail.budget if bid_detail else ""),
        duration=result.get("duration", ""),
        contract_type=result.get("contract_type", ""),
        delivery_phases=result.get("delivery_phases", []),
        qualification_requirements=result.get("qualification_requirements", []),
        similar_project_requirements=result.get("similar_project_requirements", []),
        key_personnel_requirements=result.get("key_personnel_requirements", []),
        subcontracting_conditions=result.get("subcontracting_conditions", []),
    )

    # Compliance Matrix 초안
    compliance_items = [
        ComplianceItem(
            req_id=item.get("req_id", f"RFP-{i:03d}"),
            content=item.get("content", ""),
            source_step="rfp_analyze",
        )
        for i, item in enumerate(result.get("compliance_items", []), 1)
    ]

    # 동적 섹션 목록 생성 (케이스 A: 평가항목 기반, 케이스 B: 서식 구조 기반)
    if rfp_analysis.case_type == "B" and rfp_analysis.format_template.get("structure"):
        structure = rfp_analysis.format_template["structure"]
        if isinstance(structure, dict):
            sections = list(structure.keys())
        elif isinstance(structure, list):
            sections = [item if isinstance(item, str) else list(item.keys())[0]
                        for item in structure if item]
        else:
            sections = [item.get("item", f"section_{i}")
                        for i, item in enumerate(rfp_analysis.eval_items, 1)]
    else:
        sections = [item.get("item", f"section_{i}") for i, item in enumerate(rfp_analysis.eval_items, 1)]

    # v3.5: 섹션 유형 자동 분류 (section_title 전달로 분류 정확도 향상)
    from app.prompts.section_prompts import classify_section_type
    section_type_map = {}
    for section_id in sections:
        section_type_map[section_id] = classify_section_type(section_id, section_id)

    # 즉시 MD 보고서 생성 + 아카이브 (review_rfp 전 사용자에게 제공)
    if proposal_id:
        try:
            import asyncio
            from app.services.project_archive_service import archive_artifact, render_artifact, _DEF_MAP
            defn = _DEF_MAP.get("rfp_analysis")
            if defn:
                content = render_artifact(defn, {"rfp_analysis": rfp_analysis})
                if content:
                    asyncio.get_running_loop().create_task(
                        archive_artifact(proposal_id, "rfp_analysis", content, source="ai")
                    )
        except Exception as e:
            logger.warning(f"RFP 분석 즉시 아카이브 실패 (무시): {e}")

    return {
        "rfp_analysis": rfp_analysis,
        "compliance_matrix": compliance_items,
        "dynamic_sections": sections,
        "parallel_results": {"_section_type_map": section_type_map},
        "current_step": "rfp_analyze_complete",
        "project_name": rfp_analysis.project_name or state.get("project_name", ""),
    }
