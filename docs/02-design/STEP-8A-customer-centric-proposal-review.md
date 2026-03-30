# STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계

> **설계일**: 2026-03-29
> **목표**: 섹션별 작성 & Human 검토 → 고객 니즈 기반 개선 루프
> **핵심 원칙**: "발주기관을 설득한다" = "발주기관의 pain point를 해결한다"

---

## 📋 설계 개요

### 현재 문제점

기존 제안서 작성은:
- ❌ 평가항목 충족 중심 (체크리스트)
- ❌ 기술 스펙 나열
- ❌ 일반적/추상적 서술
- ❌ 발주기관의 관점 부족

### 개선 목표

STEP 8A는:
- ✅ **고객(발주기관) pain point → 우리 솔루션**의 구조
- ✅ 각 섹션이 "발주기관이 왜 우리를 선택해야 하는가"를 설득
- ✅ 평가위원도 "이 업체가 우리 기관을 가장 잘 이해한다"고 확신
- ✅ 섹션별 Human Review → 고객 관점 검증 → 피드백 반영

---

## 🎯 STEP 8A 구조 (섹션별 검토 루프)

```
┌──────────────────────────────────────────┐
│ STEP 8A: 목차별 제안 작업 & Human Review │
└──────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 1️⃣ 고객 요구사항 분석 (1회, 모든 섹션 공통)       │
│                                                     │
│  RFP 분석 → 발주기관 pain points 추출              │
│          → 발주기관 success criteria 정의          │
│          → 평가항목 ↔ 고객니즈 매핑               │
│                                                     │
│  산출: customer_context = {                        │
│    "pain_points": [...],                           │
│    "success_criteria": [...],                      │
│    "item_to_customer_need": {...},                 │
│    "our_unique_value": [...]                       │
│  }                                                  │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 2️⃣ 섹션별 루프 (동적 섹션 수만큼 반복)            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  for each section in dynamic_sections:             │
│                                                     │
│    a) 섹션 작성 전 분석                            │
│       ├─ 평가항목 세부 배점 추출                   │
│       ├─ 이 섹션이 충족할 고객니즈 식별            │
│       └─ 우리의 차별화된 접근 정의                 │
│                                                     │
│    b) 고객 관점 프롬프트로 섹션 작성               │
│       ├─ 발주기관 pain point로 도입               │
│       ├─ 우리 솔루션이 어떻게 해결하는지           │
│       ├─ 구체적 사례/수치/근거 포함               │
│       └─ 평가위원이 점수를 쉽게 매길 구조         │
│                                                     │
│    c) 섹션 완성 후 AI 자체 검증                   │
│       ├─ 고객니즈 대응 정도 (0-100%)             │
│       ├─ 구체성/차별성 검증                       │
│       └─ 개선 제안 3-5개 자동 생성                │
│                                                     │
│    d) Human Review (Interrupt)                     │
│       ├─ 섹션 내용 검토 (+AI 자체 검증 결과)      │
│       ├─ 고객 니즈 충족 여부 확인                 │
│       ├─ 피드백 입력 (선택: 수정/승인/재작성)     │
│       └─ 다음 섹션 진행                           │
│                                                     │
│    라우팅:                                         │
│    ├─ approved → 다음 섹션                       │
│    ├─ rework_customer_focus → 고객 니즈 재분석   │
│    └─ rewrite → 섹션 재작성                      │
│                                                     │
│  end for                                            │
│                                                     │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ 3️⃣ 모든 섹션 완성 후 통합 검증                     │
│                                                     │
│  ├─ 섹션 간 일관성 (스토리라인 흐름)              │
│  ├─ 고객니즈 전체 커버 여부                        │
│  ├─ 평가항목별 충족도 종합                        │
│  └─ 시정 필요 항목 자동 추출                      │
│                                                     │
│  라우팅:                                           │
│  ├─ 전체 OK → STEP 9 (자가진단)                  │
│  ├─ 부분 개선 필요 → 해당 섹션 루프 재진입       │
│  └─ 대규모 개선 필요 → STEP 8A 처음부터           │
└─────────────────────────────────────────────────────┘
```

---

## 🔍 1️⃣ 고객 요구사항 분석 (proposal_customer_analysis)

### 목적
모든 섹션 작성 전에 **발주기관의 관점을 한 번에 정리**하고, 이를 각 섹션의 작성 지침으로 사용합니다.

### 입력
```python
{
    "rfp_analysis": RFPAnalysis,  # eval_items, hot_buttons, mandatory_reqs
    "strategy": Strategy,          # positioning, win_theme
}
```

### AI 분석 프롬프트

```
당신은 발주기관의 사업 담당자입니다.

RFP 분석 기반으로 다음을 도출하세요:

1️⃣ Pain Points (발주기관이 해결하려는 핵심 문제, 3-5개)
   - 현 상황의 문제점
   - 의도 (TO-BE)
   - 평가위원 관점: 이 문제를 "우리가 해결한다"면 최고점

2️⃣ Success Criteria (성공의 정의, 3-5개)
   - 정량 목표 (성능, 일정, 비용, 품질)
   - 정성 목표 (만족도, 안정성, 혁신도)
   - 평가위원 관점: "이 업체가 우리 기관의 성공을 가장 잘 이해한다"

3️⃣ Evaluation Item → Customer Need Mapping
   for each eval_item in RFP:
      {
        "eval_item": "기술혁신성 (20점)",
        "customer_needs": [
          "현 시스템의 XX 문제를 신기술로 해결",
          "향후 5년 이후 확장성 확보",
        ],
        "key_success": "신기술 도입으로 XX% 성능 향상",
        "why_we_are_best": "우리가 보유한 OO 기술로 경쟁사 대비 XX% 우월"
      }

4️⃣ Our Unique Value (우리만 제공할 수 있는 것, 3-5개)
   - 기술 우월성 (vs 일반적 솔루션)
   - 경험 우월성 (vs 경쟁사)
   - 고객 맞춤 우월성 (vs 기존 제안)

5️⃣ Messaging Framework
   {
      "opening": "발주기관의 pain point 직시",
      "main": "우리 솔루션이 어떻게 해결하는가",
      "closing": "발주기관의 성공을 보장하는 이유"
   }

응답 형식:
{
  "pain_points": [
    {
      "point": "...",
      "impact": "...",
      "why_critical": "..."
    }
  ],
  "success_criteria": [...],
  "item_to_customer_need": {...},
  "our_unique_value": [...],
  "messaging_framework": {...}
}
```

### 산출물

```python
customer_context = {
    "analysis_timestamp": "2026-03-29T10:00:00Z",
    "pain_points": [
        {
            "point": "현 시스템의 성능 저하로 인한 업무 지연",
            "impact": "월 XX시간의 업무 손실, YY% 만족도 저하",
            "why_critical": "향후 처리량 증가 시 시스템 마비 가능성",
            "related_eval_items": ["기술혁신성", "성능"],
        },
        ...
    ],
    "success_criteria": [
        {
            "type": "quantitative",
            "metric": "처리 성능 300% 향상",
            "target": "응답시간 3초 이내",
            "why_matters": "사용자 만족도 90% 이상 달성",
        },
        ...
    ],
    "item_to_customer_need": {
        "T1_기술혁신성": {
            "eval_item": "기술혁신성 (20점)",
            "customer_needs": [
                "신규 기술을 통한 성능 개선",
                "향후 5년 이후 확장성"
            ],
            "key_success": "신기술 도입으로 성능 300% 향상",
            "our_unique_value": "우리가 보유한 AI 기술로 경쟁사 대비 2배 성능",
            "section_focus": ["기술적 수행방안", "기술혁신"]
        },
        ...
    },
    "our_unique_value": [
        {
            "dimension": "기술",
            "what": "AI 기반 자동 최적화",
            "why_unique": "경쟁사는 수동 튜닝만 제공",
            "impact": "성능 300% 향상, 운영 인력 50% 감소"
        },
        ...
    ],
    "messaging_framework": {
        "opening": "발주기관은 현 시스템의 성능 저하로 ...",
        "main": "우리는 AI 기술을 통해 ...",
        "closing": "따라서 발주기관의 성공을 가장 잘 보장할 수 있는 것은 우리입니다"
    }
}
```

---

## ✍️ 2️⃣ 섹션별 작성 (proposal_write_customer_centric)

### 변경사항

기존: `proposal_write_next(state, context)` → 단순 섹션 작성
신규: 3단계 프로세스

#### 2-1) 섹션 작성 전 분석 (_analyze_section_requirement)

```python
async def _analyze_section_requirement(
    section_id: str,
    section_title: str,
    customer_context: dict,
    eval_items: list
) -> dict:
    """이 섹션이 충족해야 할 고객 니즈를 정리"""

    # 1. 이 섹션이 대응하는 eval_items 추출
    related_items = [
        item for item in eval_items
        if _is_section_related_to_item(section_title, item)
    ]

    # 2. 각 eval_item마다 고객니즈 추출
    section_requirement = {
        "section_id": section_id,
        "section_title": section_title,
        "related_eval_items": related_items,
        "customer_needs": [],
        "key_messages": [],
        "section_focus": []
    }

    for item in related_items:
        # customer_context.item_to_customer_need에서 lookup
        need = customer_context["item_to_customer_need"].get(item.get("item_id"))
        if need:
            section_requirement["customer_needs"].extend(need["customer_needs"])
            section_requirement["key_messages"].append(need["key_success"])
            section_requirement["section_focus"].extend(need.get("section_focus", []))

    return section_requirement
```

#### 2-2) 고객 관점 섹션 프롬프트 (get_customer_centric_section_prompt)

```python
def get_customer_centric_section_prompt(
    section_id: str,
    section_type: str,
    section_requirement: dict,
    customer_context: dict,
    eval_items: list,
    prev_sections_context: str,
    strategy: dict
) -> str:
    """고객 관점 중심의 섹션 작성 프롬프트"""

    prompt = f"""
당신은 발주기관의 성공을 가장 잘 이해하는 제안 컨설턴트입니다.

## 발주기관의 관점

발주기관이 이 사업으로 해결하려는 핵심 문제:
{customer_context['messaging_framework']['opening']}

발주기관의 성공 정의:
{', '.join([c['metric'] for c in customer_context['success_criteria']])}

## 이 섹션의 역할

이 섹션 '{section_title}'에서는 다음 고객 니즈를 충족해야 합니다:

{chr(10).join([f"- {need}" for need in section_requirement['customer_needs']])}

## 핵심 메시지 (평가위원이 "이 부분이 최고"라고 평가할 내용)

각 메시지마다:
1. 발주기관의 pain point를 구체적으로 명시
2. 우리의 솔루션이 어떻게 해결하는지 (차별화 강조)
3. 구체적 근거 (수치, 사례, 도표)

메시지 예:
- {section_requirement['key_messages'][0] if section_requirement['key_messages'] else '(분석 필요)'}

## 평가항목 매핑

이 섹션이 충족하는 평가항목:
{chr(10).join([f"- {item.get('title')} ({item.get('score')}점): {item.get('criteria')}" for item in section_requirement['related_eval_items']])}

각 평가항목 세부 배점에 **명시적으로 대응**하세요.
평가위원이 "이 부분은 OO점"이라고 바로 체크할 수 있는 구조로 작성하세요.

## 작성 구조

[도입부] 발주기관의 현 상황과 요구를 재해석 (단순 복사 X)
    ↓
[전개부] 우리의 차별화된 접근 방법
    ↓
[근거부] 구체적 사례, 수치, 도표 (최소 3개)
    ↓
[결론부] 발주기관의 성공을 보장하는 이유

## 이전 섹션 컨텍스트 (일관성 유지)

{prev_sections_context}

제안 작성을 시작하세요. 마크다운 형식으로 분명하고 구체적으로 작성하세요.
"""

    return prompt
```

#### 2-3) 섹션 산출물 예시

```markdown
# 기술적 수행방안

## 현 시황 진단 (발주기관 관점 재해석)

발주기관은 현 시스템의 응답시간이 평균 8초에 달해 업무 지연이 매달 200시간에 이르고 있습니다.
특히 향후 2년간 처리량이 50% 증가할 예정인 상황에서, 현 시스템으로는 마비 가능성이 높습니다.

## 우리의 차별화된 솔루션

기존 솔루션: 수동 튜닝 → 3-6개월 최적화 필요, 비용 XX억
**우리의 솔루션: AI 기반 자동 최적화 → 1개월, 비용 XX억, 성능 3배 향상**

### 차별화 포인트 1: AI 자동 최적화
- 우리는 XX 기술을 보유하고 있어 자동으로 최적값을 찾습니다
- A기관 사례: 응답시간 8초 → 2초 (75% 개선)
- 비용 절감: 수동 튜닝 인력 50명 → 2명

### 차별화 포인트 2: 5년 후 확장성 확보
- ...

(이런 식으로 각 평가항목별 명시적 대응)
```

---

## 🔍 2️⃣-2 섹션 완성 후 AI 자체 검증 (validate_section_customer_focus)

### 목적
Human Review 전에 AI가 먼저 검증하여 명백한 개선 사항을 제시

### 검증 항목

```python
async def validate_section_customer_focus(
    section_content: str,
    section_requirement: dict,
    customer_context: dict
) -> dict:
    """고객 관점에서 섹션 검증"""

    validation = {
        "section_id": section_requirement["section_id"],
        "checks": []
    }

    # 1. 고객니즈 대응 정도 (0-100%)
    check1 = await _check_customer_need_coverage(
        section_content,
        section_requirement["customer_needs"]
    )
    validation["checks"].append({
        "type": "customer_need_coverage",
        "score": check1["percentage"],  # 0-100
        "details": check1["missing_needs"],
        "severity": "HIGH" if check1["percentage"] < 70 else "LOW"
    })

    # 2. 구체성 검증 (추상적 표현 vs 구체적 근거)
    check2 = await _check_specificity(
        section_content,
        required_min=3  # 구체적 사례/수치 최소 3개
    )
    validation["checks"].append({
        "type": "specificity",
        "score": check2["specificity_score"],
        "examples_found": check2["count"],
        "abstract_phrases": check2["abstract_phrases"],
        "severity": "MEDIUM" if check2["count"] < 3 else "LOW"
    })

    # 3. 차별성 검증
    check3 = await _check_differentiation(
        section_content,
        customer_context["our_unique_value"]
    )
    validation["checks"].append({
        "type": "differentiation",
        "score": check3["differentiation_score"],
        "unique_value_mentioned": check3["count"],
        "severity": "MEDIUM" if check3["count"] == 0 else "LOW"
    })

    # 4. 평가항목 명시적 대응 (§평가항목 하나하나)
    check4 = await _check_eval_item_mapping(
        section_content,
        section_requirement["related_eval_items"]
    )
    validation["checks"].append({
        "type": "eval_item_mapping",
        "items_covered": check4["items_covered"],
        "items_missing": check4["items_missing"],
        "severity": "HIGH" if len(check4["items_missing"]) > 0 else "LOW"
    })

    # 5. 논리성/일관성
    check5 = await _check_logic_flow(section_content)
    validation["checks"].append({
        "type": "logic_flow",
        "score": check5["logic_score"],
        "issues": check5["issues"]
    })

    # 자동 개선 제안 (3-5개)
    validation["improvement_suggestions"] = await _generate_improvement_suggestions(
        validation["checks"],
        section_content,
        section_requirement
    )

    # 종합 평가
    validation["overall_status"] = _determine_status(validation["checks"])
    # "ready_for_human_review" | "needs_improvement" | "rewrite_recommended"

    return validation
```

---

## 👤 2️⃣-3 Human Review (Interrupt)

### 화면 UI 정보 (참고용)

```
┌─────────────────────────────────────────┐
│  STEP 8A: 섹션별 검토                    │
├─────────────────────────────────────────┤
│                                         │
│  섹션: 기술적 수행방안  (3/10)            │
│                                         │
│  [AI 자체 검증 결과]                     │
│  ├─ 고객니즈 대응: 85% ✅                │
│  ├─ 구체성: 4개 사례/수치 ✅              │
│  ├─ 차별성: 2개 포인트 ⚠️ (목표: 3개)    │
│  ├─ 평가항목 대응: 5/5 항목 ✅            │
│  └─ 논리성: 좋음 ✅                     │
│                                         │
│  [AI 개선 제안]                         │
│  1. "기존 기술은 XX하지만..."라는         │
│     비교 표현 추가 (차별성)             │
│  2. B기관 사례도 추가 (구체성)           │
│  3. 5년 후 확장성 언급 추가              │
│                                         │
│  ───────────────────────────────────────  │
│                                         │
│  [섹션 본문]                            │
│  (제안서 내용...)                        │
│                                         │
│  ───────────────────────────────────────  │
│                                         │
│  [Human Review]                         │
│                                         │
│  ☐ Approved (승인, 다음 섹션 진행)       │
│                                         │
│  ☐ Rework Customer Focus               │
│    (고객 니즈 재분석 후 재작성)           │
│                                         │
│  ☐ Rewrite (처음부터 재작성)            │
│                                         │
│  [피드백 입력] (선택사항)                │
│  ┌──────────────────────────────────┐  │
│  │ 특정 고객니즈가 잘 안 드러난다...  │  │
│  │ CC 사례도 추가해달라...          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  [Submit]                               │
│                                         │
└─────────────────────────────────────────┘
```

### 라우팅 로직

```python
def route_after_section_review(state: ProposalState) -> str:
    """섹션 리뷰 후 라우팅"""

    current_step = state.get("current_step", "")

    if current_step == "section_approved":
        # 다음 섹션 인덱스 증가
        idx = state.get("current_section_index", 0)
        next_idx = idx + 1
        total = len(state.get("dynamic_sections", []))

        if next_idx < total:
            return "next_section"  # 다음 섹션 작성
        else:
            return "all_done"  # 모든 섹션 완성 → STEP 9 (자가진단)

    elif current_step == "section_rework_customer_focus":
        # 고객 니즈 재분석 후 재작성
        return "rework_customer_focus"

    elif current_step == "section_rewrite":
        # 섹션 재작성
        return "rewrite"

    return "rewrite"  # 기본: 재작성
```

---

## ✅ 3️⃣ 모든 섹션 완성 후 통합 검증 (proposal_sections_consolidation)

### 목적
모든 섹션이 일관되게 고객 니즈를 충족하고, 강점이 명확히 드러나는지 종합 검증

### 검증 항목

```python
async def validate_all_sections_integration(
    all_sections: list[ProposalSection],
    customer_context: dict,
    eval_items: list
) -> dict:
    """전체 섹션 통합 검증"""

    consolidation = {
        "total_sections": len(all_sections),
        "checks": []
    }

    # 1. 고객니즈 전체 커버 (모든 customer_need이 어딘가에 명시되었나)
    check1 = await _check_all_customer_needs_covered(
        all_sections,
        customer_context["pain_points"],
        customer_context["success_criteria"]
    )
    consolidation["checks"].append({
        "type": "customer_needs_coverage",
        "covered": check1["covered_percentage"],  # 0-100%
        "uncovered": check1["uncovered_needs"],
        "severity": "HIGH" if check1["covered_percentage"] < 90 else "LOW"
    })

    # 2. 평가항목별 충족도 (각 eval_item이 명확히 대응되었나)
    check2 = await _check_all_eval_items_covered(
        all_sections,
        eval_items
    )
    consolidation["checks"].append({
        "type": "eval_items_coverage",
        "items_details": check2["items"],  # 각 항목별 충족도
        "overall_score": check2["overall_percentage"],
        "severity": "HIGH" if check2["overall_percentage"] < 80 else "LOW"
    })

    # 3. 섹션 간 일관성 (스토리라인 흐름, 메시징 일관성)
    check3 = await _check_sections_coherence(
        all_sections,
        customer_context["messaging_framework"]
    )
    consolidation["checks"].append({
        "type": "sections_coherence",
        "consistency_score": check3["score"],
        "messaging_consistency": check3["messaging_consistency"],
        "flow_issues": check3["flow_issues"],
        "severity": "MEDIUM" if len(check3["flow_issues"]) > 2 else "LOW"
    })

    # 4. 우리 강점 강조도 (우리의 unique value가 충분히 드러나나)
    check4 = await _check_unique_value_emphasis(
        all_sections,
        customer_context["our_unique_value"]
    )
    consolidation["checks"].append({
        "type": "unique_value_emphasis",
        "value_mentions": check4["count"],
        "emphasis_percentage": check4["percentage"],  # 전체 내용 중 %
        "severity": "MEDIUM" if check4["percentage"] < 15 else "LOW"
    })

    # 5. 발주기관 성공과의 연결고리 (마지막 섹션이 "따라서 우리를 선택해야"로 끝나나)
    check5 = await _check_customer_success_connection(
        all_sections[-1],  # 마지막 섹션
        customer_context["success_criteria"]
    )
    consolidation["checks"].append({
        "type": "success_connection",
        "connection_score": check5["score"],
        "details": check5["details"]
    })

    # 종합 판정
    consolidation["overall_status"] = _determine_consolidation_status(consolidation["checks"])
    # "ready_for_self_review" | "needs_section_improvement" | "restart_step8a"

    if consolidation["overall_status"] == "needs_section_improvement":
        # 개선 필요 섹션 자동 추출
        consolidation["sections_to_improve"] = [
            s["section_id"] for s in all_sections
            if _needs_improvement(s, customer_context)
        ]

    return consolidation
```

### 라우팅

```python
def route_after_section_consolidation(state: ProposalState) -> str:
    """모든 섹션 완성 후 라우팅"""

    consolidation = state.get("sections_consolidation_result", {})
    status = consolidation.get("overall_status", "")

    if status == "ready_for_self_review":
        return "proceed_to_self_review"  # STEP 9 (자가진단)

    elif status == "needs_section_improvement":
        # 부분 개선: 문제 섹션 재입력
        sections_to_improve = consolidation.get("sections_to_improve", [])
        return "rework_sections"  # 해당 섹션만 루프

    elif status == "restart_step8a":
        # 전체 재검토
        return "restart_step8a"  # 처음부터

    return "proceed_to_self_review"  # 기본
```

---

## 📊 상태 필드 확장 (state.py)

```python
class ProposalState(TypedDict):
    # ... 기존 필드들 ...

    # STEP 8A 신규 필드
    customer_context: Optional[dict]  # 고객 요구사항 분석 (1회)
    current_section_customer_focus: Optional[dict]  # 현재 섹션의 고객 니즈

    # 섹션별 검증 결과
    section_validation_results: list[dict]  # 각 섹션의 검증 결과 누적

    # 통합 검증 결과
    sections_consolidation_result: Optional[dict]  # 모든 섹션 완성 후 검증
```

---

## 🔧 구현 로드맵

### Phase 1: 고객 분석 (proposal_customer_analysis)
- [ ] AI 분석 프롬프트 작성
- [ ] customer_context 생성
- [ ] RFP eval_items ↔ 고객니즈 매핑

### Phase 2: 섹션 작성 강화 (proposal_write_customer_centric)
- [ ] _analyze_section_requirement 함수
- [ ] get_customer_centric_section_prompt 함수
- [ ] 기존 proposal_write_next 수정

### Phase 3: AI 자체 검증 (validate_section_customer_focus)
- [ ] _check_customer_need_coverage
- [ ] _check_specificity
- [ ] _check_differentiation
- [ ] _check_eval_item_mapping
- [ ] _generate_improvement_suggestions

### Phase 4: Human Review 및 라우팅
- [ ] route_after_section_review 함수 강화
- [ ] 섹션별 Human Interrupt UI
- [ ] 피드백 수집 및 저장

### Phase 5: 통합 검증 (proposal_sections_consolidation)
- [ ] validate_all_sections_integration
- [ ] 고객니즈 전체 커버 검증
- [ ] 평가항목별 충족도 검증
- [ ] route_after_section_consolidation

---

## 📝 프롬프트 패턴

### 현재 (기술 중심)
```
이 섹션의 평가항목: 기술혁신성 (20점)
세부항목: 신규 기술 적용도, 차별화된 해결방안, 기술 완성도

↓ 기술 스펙 나열
```

### 신규 (고객 관점 중심)
```
발주기관의 pain point: "현 시스템 응답시간 8초 → 업무 지연"
발주기관의 success: "응답시간 3초 이내 + 50% 비용 절감"
이 섹션이 충족할 고객니즈: "신기술로 성능 3배 향상"

↓ 고객 관점에서:
  1. "발주기관은 현재 XX 문제를 겪고 있습니다"
  2. "우리의 해결방안: XX 기술로 YY% 개선"
  3. "사례: A기관에서 8초 → 2초 달성"
```

---

## ✅ 효과

| 항목 | 기존 | 신규 |
|-----|-----|-----|
| 평가위원 관점 | 평가항목 체크리스트 | 발주기관 성공을 보장하는지 판단 |
| 제안서 느낌 | 일반적/기술적 | 발주기관 맞춤/설득력 있음 |
| 차별성 | 평가항목 충족 | 왜 우리를 선택해야 하는가? |
| 섹션 개수 | 고정 10-12개 | 고객니즈에 따라 7-15개 최적화 |
| 점수 기댓값 | 65-75점 | 75-85점 |

---

**설계 완료**: ✅ 2026-03-29
**다음 단계**: Phase 2 (섹션 작성 강화)
