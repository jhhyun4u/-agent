# STEP 8A: 고객 관점 섹션 검토 구현 가이드

> **작성일**: 2026-03-29
> **목표**: 고객(발주기관) 관점에서 섹션별 검토 루프 구현
> **예상 구현 기간**: 3-4일 (Phase, Node 개발)

---

## 🎯 구현 전략

### 3가지 주요 작업

1. **STEP 1: 고객 요구사항 분석** (`proposal_customer_analysis` 노드)
   - RFP → 고객 pain points, success criteria, 니즈 매핑
   - 1회만 실행 (모든 섹션의 지침)

2. **STEP 2: 섹션별 작성 & 검증** (기존 `proposal_write_next` 강화)
   - 고객 관점 프롬프트로 작성
   - AI 자체 검증 (구체성, 차별성, 고객니즈 충족)
   - Human Review Interrupt

3. **STEP 3: 통합 검증** (`proposal_sections_consolidation` 노드)
   - 모든 섹션 완성 후 전체 일관성 검증
   - 미흡 섹션 자동 추출

---

## 📝 Phase 1: proposal_customer_analysis (새 노드)

### 파일: `app/graph/nodes/proposal_customer_analysis.py` (새로 생성)

```python
"""
STEP 8A-0: 고객 요구사항 분석 (proposal_customer_analysis)

RFP와 전략을 바탕으로 발주기관의 pain point, success criteria,
평가항목-고객니즈 매핑을 한 번에 분석합니다.

이 정보는 이후 모든 섹션 작성의 기초가 됩니다.
"""

import asyncio
import json
import logging
from typing import Any

from app.graph.state import ProposalState
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


async def proposal_customer_analysis(state: ProposalState) -> dict:
    """고객 요구사항 분석 (1회, 모든 섹션 공통)"""

    rfp = state.get("rfp_analysis")
    rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    strategy = state.get("strategy")
    strategy_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    # RFP 정보 추출
    project_name = rfp_dict.get("project_name", "")
    client_name = rfp_dict.get("client", "")
    hot_buttons = rfp_dict.get("hot_buttons", [])
    mandatory_reqs = rfp_dict.get("mandatory_reqs", [])
    eval_items = rfp_dict.get("eval_items", [])

    prompt = f"""
당신은 발주기관 '{client_name}'의 사업 담당자 입장에서 분석하는 컨설턴트입니다.

## 프로젝트 정보

프로젝트명: {project_name}
발주기관: {client_name}

### RFP의 핵심 신호

핫버튼 (발주기관이 가장 중시하는 것):
{', '.join(hot_buttons) if hot_buttons else '정보 없음'}

필수 요구사항:
{chr(10).join([f"- {req}" for req in mandatory_reqs]) if mandatory_reqs else '정보 없음'}

### 우리의 포지셔닝

포지셔닝: {strategy_dict.get('positioning', '')}
Win Theme: {strategy_dict.get('win_theme', '')}

---

## 분석 과제

### 1️⃣ Pain Points (발주기관이 해결하려는 문제, 3-5개)

RFP를 읽은 발주기관의 입장에서:
- 현 상황의 핵심 문제는 무엇인가? (기술, 비용, 리스크 등)
- 이 문제가 발생하는 근본 원인은?
- 문제를 방치했을 때의 영향?
- 평가위원 관점: 이 문제를 "가장 잘 이해하고 해결하는 업체"는?

응답 형식:
{{
  "pain_points": [
    {{
      "rank": 1,
      "point": "현재 시스템의 성능 저하로 인한 업무 지연",
      "root_cause": "...",
      "impact": "...",
      "why_critical": "...",
      "related_hot_buttons": ["XX", "YY"],
      "evaluator_perspective": "이 업체가 이 문제를 가장 잘 이해하고 해결할 수 있는가?"
    }},
    ...
  ]
}}

### 2️⃣ Success Criteria (성공의 정의, 3-5개)

발주기관 입장에서 "성공한 프로젝트"는?
- 정량 목표 (성능, 일정, 비용, 품질)
- 정성 목표 (만족도, 안정성, 혁신도)
- 단기 vs 장기 성공
- 평가위원 관점: "이 업체가 발주기관의 성공을 가장 잘 보장할 수 있는가?"

응답 형식:
{{
  "success_criteria": [
    {{
      "dimension": "성능",
      "type": "quantitative",
      "metric": "처리 성능 300% 향상",
      "target": "응답시간 3초 이내",
      "why_matters": "...",
      "evaluator_perspective": "..."
    }},
    ...
  ]
}}

### 3️⃣ Evaluation Item ↔ Customer Need Mapping

RFP의 각 평가항목이 발주기관의 어떤 니즈를 충족하는가?

응답 형식:
{{
  "item_to_customer_need": {{
    "T1_기술혁신성": {{
      "eval_item": "기술혁신성 (20점)",
      "eval_criteria": [...],
      "customer_needs": [
        "신규 기술을 통한 성능 개선",
        "향후 5년 이후 확장성 확보"
      ],
      "key_success": "신기술 도입으로 성능 300% 향상",
      "our_unique_value": "우리가 보유한 AI 기술로 경쟁사 대비 2배 성능",
      "section_focus": ["기술적 수행방안", "기술혁신"]
    }},
    ...
  ]}},
}}

### 4️⃣ Our Unique Value (우리만 제공할 수 있는 가치, 3-5개)

기술, 경험, 맞춤화 관점에서 우리의 차별화:
- 기술 우월성 (vs 일반적 솔루션)
- 경험 우월성 (vs 경쟁사)
- 고객 맞춤 우월성 (vs 기존 제안)

응답 형식:
{{
  "our_unique_value": [
    {{
      "dimension": "기술",
      "what": "AI 기반 자동 최적화",
      "why_unique": "경쟁사는 수동 튜닝만 제공",
      "impact": "성능 300% 향상, 운영 인력 50% 감소",
      "evidence": "A기관 사례: 8초 → 2초"
    }},
    ...
  ]
}}

### 5️⃣ Messaging Framework (통합 메시지)

제안서 전체의 설득 논리:

응답 형식:
{{
  "messaging_framework": {{
    "opening": "발주기관의 pain point 직시",
    "main": "우리 솔루션이 어떻게 해결하는가",
    "closing": "따라서 발주기관의 성공을 가장 잘 보장할 수 있는 이유"
  }}
}}

---

## 최종 산출물

{{
  "analysis_timestamp": "...",
  "pain_points": [...],
  "success_criteria": [...],
  "item_to_customer_need": {{...}},
  "our_unique_value": [...],
  "messaging_framework": {{...}},
  "analysis_quality": "high|medium|low"  // 신뢰도
}}
"""

    try:
        result = await claude_generate(
            prompt=prompt,
            response_format="json",
            temperature=0.3,
        )

        # 결과 검증
        if not isinstance(result, dict):
            result = json.loads(result) if isinstance(result, str) else {}

        return {
            "customer_context": result,
            "current_phase": "customer_analysis_complete",
        }

    except Exception as e:
        logger.error(f"proposal_customer_analysis 실패: {e}", exc_info=True)
        return {
            "customer_context": {
                "error": str(e),
                "analysis_quality": "low"
            },
            "current_phase": "customer_analysis_error",
        }


# ── 헬퍼 함수 ──

def _validate_customer_context(context: dict) -> bool:
    """customer_context가 필수 필드를 가지고 있는지 검증"""
    required = [
        "pain_points",
        "success_criteria",
        "item_to_customer_need",
        "our_unique_value",
        "messaging_framework"
    ]
    return all(field in context for field in required)
```

### 그래프 연결 (graph.py)

```python
# STEP 8A 시작
g.add_node(
    "proposal_customer_analysis",
    track_tokens("proposal_customer_analysis")(proposal_customer_analysis)
)

# 가장 앞: proposal_write_next 직전
g.add_edge("plan_merge", "proposal_customer_analysis")
g.add_edge("proposal_customer_analysis", "proposal_start_gate")
```

---

## 📝 Phase 2: proposal_write_next 강화

### 변경 (기존 파일 수정)

파일: `app/graph/nodes/proposal_nodes.py`

#### 2-1) _analyze_section_requirement 함수 추가

```python
async def _analyze_section_requirement(
    section_id: str,
    section_title: str,
    customer_context: dict,
    eval_items: list
) -> dict:
    """이 섹션이 충족해야 할 고객 니즈를 정리"""

    related_items = []
    for item in eval_items:
        item_title = item.get("title", "").lower()
        section_title_lower = section_title.lower()

        # 간단한 문자열 매칭 (추후 LLM 기반 개선 가능)
        if any(kw in section_title_lower for kw in [
            "기술", "아키텍처", "설계", "구현", "개발"
        ]):
            if "기술" in item_title or "설계" in item_title:
                related_items.append(item)

    section_requirement = {
        "section_id": section_id,
        "section_title": section_title,
        "related_eval_items": related_items,
        "customer_needs": [],
        "key_messages": [],
        "section_focus": []
    }

    # 각 eval_item의 고객니즈 추출
    item_to_need = customer_context.get("item_to_customer_need", {})
    for item in related_items:
        item_id = item.get("item_id", item.get("id", ""))
        need_info = item_to_need.get(item_id, {})

        if need_info:
            section_requirement["customer_needs"].extend(
                need_info.get("customer_needs", [])
            )
            section_requirement["key_messages"].append(
                need_info.get("key_success", "")
            )
            section_requirement["section_focus"].extend(
                need_info.get("section_focus", [])
            )

    return section_requirement
```

#### 2-2) 고객 관점 프롬프트 강화

```python
async def proposal_write_next(state: ProposalState) -> dict:
    """섹션 순차 작성 (고객 관점 강화)"""

    # ... 기존 코드 ...

    # 신규: 고객 요구사항 분석 결과 활용
    customer_context = state.get("customer_context", {})

    # 신규: 섹션 요구사항 분석
    section_requirement = await _analyze_section_requirement(
        section_id,
        section_title,
        customer_context,
        rfp_dict.get("eval_items", [])
    )

    # 신규: 고객 관점 프롬프트 생성
    customer_prompt_section = f"""
## 발주기관의 관점

발주기관이 해결하려는 핵심 문제:
{customer_context.get('messaging_framework', {}).get('opening', '')}

이 섹션에서 충족해야 할 고객 니즈:
{chr(10).join([f"- {need}" for need in section_requirement['customer_needs']])}

## 핵심 메시지 (평가위원이 "최고점"이라 할 내용)
{chr(10).join([f"- {msg}" for msg in section_requirement['key_messages']])}

## 작성 구조

[도입부] 발주기관의 현 상황과 요구를 **재해석** (단순 복사 X)
  ↓ "발주기관은 현재 XX 문제를 겪고 있습니다"

[전개부] 우리의 차별화된 접근 방법
  ↓ "우리는 YY 기술/경험으로 이를 해결합니다"

[근거부] 구체적 사례, 수치, 도표 (최소 3개)
  ↓ "A기관 사례에서 ZZ% 개선 달성"

[결론부] 발주기관의 성공을 보장하는 이유
  ↓ "따라서 우리를 선택하면 발주기관의 성공을 가장 잘 보장할 수 있습니다"
"""

    # 기존 프롬프트 + 고객 관점 섹션 결합
    prompt = base_prompt + customer_prompt_section + prompt_tail

    # ... 이후 동일 ...
```

---

## 🔍 Phase 3: 섹션 검증 노드 (새 노드)

파일: `app/graph/nodes/proposal_section_validator.py` (새로 생성)

```python
"""
섹션 완성 후 AI 자체 검증 노드
(validate_section_customer_focus)

고객 관점에서 각 섹션을 검증하고 개선 제안을 생성합니다.
"""

async def validate_section_customer_focus(state: ProposalState) -> dict:
    """섹션 완성 후 자체 검증"""

    section = state.get("current_section")  # ProposalSection
    section_id = section.get("section_id", "")
    section_content = section.get("content", "")

    customer_context = state.get("customer_context", {})
    section_requirement = state.get("current_section_customer_focus", {})

    # 1. 고객니즈 대응 정도
    check1 = await _check_customer_need_coverage(
        section_content,
        section_requirement.get("customer_needs", [])
    )

    # 2. 구체성 (사례/수치 최소 3개)
    check2 = await _check_specificity(section_content)

    # 3. 차별성
    check3 = await _check_differentiation(
        section_content,
        customer_context.get("our_unique_value", [])
    )

    # 4. 평가항목 명시적 대응
    check4 = await _check_eval_item_mapping(
        section_content,
        section_requirement.get("related_eval_items", [])
    )

    # 5. 논리성
    check5 = await _check_logic_flow(section_content)

    validation = {
        "section_id": section_id,
        "checks": {
            "customer_need_coverage": check1["percentage"],  # 0-100
            "specificity_count": check2["count"],  # 사례/수치 개수
            "differentiation_count": check3["count"],
            "eval_item_coverage": check4["percentage"],  # 0-100
            "logic_score": check5["score"],  # 0-100
        },
        "improvement_suggestions": await _generate_improvement_suggestions(
            {
                "check1": check1,
                "check2": check2,
                "check3": check3,
                "check4": check4,
                "check5": check5,
            },
            section_content,
            section_requirement
        ),
        "overall_status": "ready" if check1["percentage"] >= 70 else "needs_improvement"
    }

    return {
        "section_validation_result": validation,
    }
```

---

## 🔄 Phase 4: 통합 검증 노드 (새 노드)

파일: `app/graph/nodes/proposal_sections_consolidation.py` (새로 생성)

```python
"""
모든 섹션 완성 후 통합 검증 (proposal_sections_consolidation)

- 고객니즈 전체 커버 여부
- 평가항목별 충족도
- 섹션 간 일관성
"""

async def proposal_sections_consolidation(state: ProposalState) -> dict:
    """모든 섹션 완성 후 통합 검증"""

    all_sections = state.get("proposal_sections", [])
    customer_context = state.get("customer_context", {})
    eval_items = state.get("rfp_analysis", {}).get("eval_items", [])

    # 1. 고객니즈 전체 커버
    check1 = await _check_all_customer_needs_covered(
        all_sections,
        customer_context
    )

    # 2. 평가항목별 충족도
    check2 = await _check_all_eval_items_covered(
        all_sections,
        eval_items
    )

    # 3. 섹션 간 일관성
    check3 = await _check_sections_coherence(
        all_sections,
        customer_context
    )

    # 4. 우리 강점 강조도
    check4 = await _check_unique_value_emphasis(
        all_sections,
        customer_context.get("our_unique_value", [])
    )

    consolidation = {
        "total_sections": len(all_sections),
        "coverage": {
            "customer_needs_percentage": check1["percentage"],
            "eval_items_percentage": check2["percentage"],
            "unique_value_mentions": check4["count"],
        },
        "issues": check1.get("missing", []) + check3.get("issues", []),
        "overall_status": _determine_consolidation_status(
            check1, check2, check3, check4
        ),
    }

    if consolidation["overall_status"] == "needs_improvement":
        consolidation["sections_to_improve"] = [
            section["section_id"]
            for section in all_sections
            if _section_needs_improvement(section, customer_context)
        ]

    return {
        "sections_consolidation_result": consolidation,
        "current_phase": "sections_consolidation_complete",
    }
```

---

## 📊 상태 필드 추가 (state.py)

```python
# STEP 8A 신규 필드
customer_context: Annotated[Optional[dict], _replace]  # 고객 요구사항 분석
current_section_customer_focus: Annotated[Optional[dict], _replace]  # 현재 섹션 고객 니즈
section_validation_results: Annotated[list[dict], _append_list]  # 섹션별 검증 결과
sections_consolidation_result: Annotated[Optional[dict], _replace]  # 통합 검증 결과
```

---

## 🔗 라우팅 강화 (edges.py)

```python
def route_after_section_review(state: ProposalState) -> str:
    """섹션 리뷰 후 라우팅 (강화)"""

    current_step = state.get("current_step", "")

    if current_step == "section_approved":
        idx = state.get("current_section_index", 0)
        total = len(state.get("dynamic_sections", []))
        return "next_section" if idx + 1 < total else "all_done"

    elif current_step == "section_rework_customer_focus":
        # 신규: 고객 니즈 재분석 후 재작성
        return "rework_customer_focus"

    elif current_step == "section_rewrite":
        return "rewrite"

    return "rewrite"


def route_after_section_consolidation(state: ProposalState) -> str:
    """통합 검증 후 라우팅"""

    consolidation = state.get("sections_consolidation_result", {})
    status = consolidation.get("overall_status", "")

    if status == "ready_for_self_review":
        return "proceed_to_self_review"  # STEP 9
    elif status == "needs_section_improvement":
        return "rework_sections"  # 부분 개선
    else:
        return "restart_step8a"  # 전체 재검토
```

---

## ✅ 구현 체크리스트

### Phase 1: Customer Analysis (1일)
- [ ] `proposal_customer_analysis.py` 작성
- [ ] 프롬프트 개발 및 테스트
- [ ] 그래프 노드 등록
- [ ] State 필드 추가

### Phase 2: Section Writing 강화 (1일)
- [ ] `_analyze_section_requirement` 함수
- [ ] 고객 관점 프롬프트 통합
- [ ] `proposal_write_next` 수정
- [ ] 테스트

### Phase 3: Section Validation (1일)
- [ ] `proposal_section_validator.py` 작성
- [ ] 5가지 검증 함수 개발
- [ ] 개선 제안 생성
- [ ] 그래프 노드 등록

### Phase 4: Consolidation (1일)
- [ ] `proposal_sections_consolidation.py` 작성
- [ ] 통합 검증 함수들
- [ ] 라우팅 로직
- [ ] 테스트

### Phase 5: Integration & Testing (1일)
- [ ] 모든 노드 통합
- [ ] End-to-End 테스트
- [ ] Human Review UI 검증
- [ ] 성능 최적화

---

**설계**: ✅ Complete
**구현**: ⏳ Ready to Start
**예상 기간**: 5일

