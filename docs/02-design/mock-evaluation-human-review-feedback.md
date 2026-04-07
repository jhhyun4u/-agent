# Mock Evaluation → Human Review → Feedback 루프 설계

> **설계일**: 2026-03-29
> **목표**: 평가위원 평가의견 정리 → Human 피드백 → 수정 지시
> **핵심**: "평가위원이 왜 낮은 점수를 줬는가?" 를 Human이 명확히 이해

---

## 📋 설계 개요

### 현재 상태

```
✅ STEP 10A: mock_evaluation
   └─ 6명 평가위원 점수 + 의견 생성
      (평가항목별, 평가위원별, 분포 분석)

❌ STEP 11A: review_mock_eval
   └─ Human이 대략적 점수만 확인
   └─ 평가근거 상세 분석 안 됨
   └─ Feedback/수정 지시 체계 불명확
```

### 개선 목표

```
✅ STEP 10A: mock_evaluation (현재 그대로)
   └─ 6명 평가위원 점수 + 의견 생성

✨ STEP 10A-분석: mock_evaluation_analysis (신규)
   └─ 6명의 평가의견을 체계적으로 정리
   └─ 항목별/평가위원별 정렬
   └─ 공통 우려사항 추출
   └─ 개선 우선순위 도출

✨ STEP 11A: review_mock_eval (강화)
   └─ 정렬된 평가의견을 Human에게 명확히 전달
   └─ Human이 이해하기 쉬운 형식 (정렬표, 요약)
   └─ Feedback 입력 폼 (어디를 개선할 것인가)

✨ STEP 11A-피드백: process_mock_eval_feedback (신규)
   └─ Human 피드백 → 수정 지시 (rework_targets)
   └─ 라우팅 결정 (섹션 개선/전략 재검토/재평가)
```

---

## 🔍 STEP 10A-분석: mock_evaluation_analysis (신규 노드)

### 목적

mock_evaluation에서 생성된 **6명의 점수와 의견을 정렬, 분석, 요약**하여
Human이 "평가위원들이 왜 낮은 점수를 줬는가"를 **한눈에 파악**하도록 합니다.

### 입력

```python
mock_evaluation_result = {
    "evaluation_items": {
        "T1": {
            "item_title": "기술혁신성",
            "max_score": 20,
            "scores_by_evaluator": {
                "evaluator_1": {
                    "evaluator_id": "evaluator_1",
                    "evaluator_name": "이산업",
                    "score": 16,
                    "reasoning": "신기술 적용도 우수하나 실현가능성 검증 부족",
                    "strengths": ["AI 기술 수준 높음"],
                    "weaknesses": ["파일럿 경험 미흡"]
                },
                "evaluator_2": {...},
                ...
            },
            "average_score": 17.5,
            "distribution": {...},
            "consensus": {...}
        },
        ...
    },
    "evaluator_scores": {
        "evaluator_1": {
            "name": "이산업",
            "title": "개발이사",
            "type": "산업계",
            "total_score": 68,
            "rank": 4
        },
        ...
    }
}
```

### AI 분석 프롬프트

```python
async def mock_evaluation_analysis(state: ProposalState) -> dict:
    """평가위원 평가의견 정렬 & 분석"""

    mock_result = state.get("mock_evaluation_result", {})

    prompt = f"""
당신은 6명 평가위원의 평가 의견을 분석하는 평가 컨설턴트입니다.

## 평가 결과

### 전체 점수 분포
- 평가위원 총점: {[r['total_score'] for r in mock_result.get('evaluator_scores', {}).values()]}
- 평균: {sum([r['total_score'] for r in mock_result.get('evaluator_scores', {}).values()]) / 6:.1f}점
- 범위: {mock_result.get('final_score', 0):.1f}점

## 분석 과제

### 1️⃣ 항목별 평가의견 정렬

각 평가항목마다:
- 6명의 점수 (순서대로)
- 점수 편차 (표준편차)
- 공통으로 지적된 강점 (2-3개)
- 공통으로 지적된 약점 (2-3개)
- 평가위원별 우려사항 (한 줄씩)

응답 형식:
{{
  "items_analysis": [
    {{
      "item_id": "T1",
      "item_title": "기술혁신성",
      "scores_by_evaluator": [
        {{"rank": 1, "name": "이산업", "score": 16, "reason_short": "..."}},
        ...
      ],
      "score_variance": 3.2,  # 표준편차
      "average_score": 17.5,
      "consensus_assessment": "높음",  # 높음/중간/낮음
      "common_strengths": [
        "AI 기술 수준 높음",
        "..."
      ],
      "common_weaknesses": [
        "파일럿 경험 미흡",
        "..."
      ],
      "individual_concerns": [
        {{"name": "이산업", "concern": "실현가능성 검증 부족"}},
        ...
      ]
    }},
    ...
  ]
}}

### 2️⃣ 평가위원별 평가 성향 분석

각 평가위원마다:
- 총점 & 순위
- 엄격한가 / 평균적인가 / 관대한가 (성향)
- 어느 항목에서 낮은 점수를 줬는가 (약점 지적 항목)
- 어느 항목에서 높은 점수를 줬는가 (강점 인정 항목)
- 주요 우려사항 (한 줄 요약)

응답 형식:
{{
  "evaluators_analysis": [
    {{
      "evaluator_id": "evaluator_1",
      "name": "이산업",
      "title": "개발이사",
      "type": "산업계",
      "total_score": 68,
      "rank": 4,
      "scoring_tendency": "보수적",  # 보수적/평균/관대
      "lowest_items": [
        {{"item_id": "M1", "item_title": "관리능력", "score": 14, "reason": "위험관리 미흡"}}
      ],
      "highest_items": [
        {{"item_id": "T1", "item_title": "기술혁신성", "score": 16}}
      ],
      "key_concern": "조직의 변화관리 능력에 대한 우려"
    }},
    ...
  ]
}}

### 3️⃣ 평가위원 의견 불일치 항목 (논쟁 여지)

점수 편차가 큰 항목들 (std > 5):
- 어느 평가위원이 높게 줬는가
- 어느 평가위원이 낮게 줬는가
- 왜 의견이 갈렸는가 (서로 다른 관점)

응답 형식:
{{
  "divergent_items": [
    {{
      "item_id": "T1",
      "item_title": "기술혁신성",
      "variance": 5.2,
      "high_scorers": [
        {{"name": "최교수", "score": 19, "reason": "신기술 도입 적극 평가"}},
        ...
      ],
      "low_scorers": [
        {{"name": "이산업", "score": 14, "reason": "현장 적용성 의심"}},
        ...
      ],
      "key_disagreement": "신기술 혁신성 vs 현장 적용성"
    }},
    ...
  ]
}}

### 4️⃣ 공통 우려사항 추출

모든 평가위원이 또는 여러 평가위원이 지적한 공통 문제점:
- 발생 빈도 (5명/4명/3명이 언급)
- 어느 항목과 관련 있는가
- 해결책은 무엇인가 (우리 제안)

응답 형식:
{{
  "common_concerns": [
    {{
      "concern": "기존 시스템과의 연계 방안 미흡",
      "frequency": 4,  # 4명의 평가위원이 언급
      "related_items": ["T1", "M1"],
      "impact": "HIGH",  # HIGH/MEDIUM/LOW
      "our_proposal_to_address": "기존 시스템 연계 아키텍처 추가 제시, 마이그레이션 계획 상세화"
    }},
    ...
  ]
}}

### 5️⃣ 개선 우선순위 추천

Human이 "어디를 먼저 개선할 것인가"를 결정하도록 도움:
1. 영향도 높은 항목 (큰 점수 배점)
2. 의견 불일치 항목 (명확하지 않은 부분)
3. 공통 우려사항 (모두가 우려하는 부분)

응답 형식:
{{
  "improvement_priorities": [
    {{
      "rank": 1,
      "item_id": "T1",
      "item_title": "기술혁신성",
      "reason": "배점 20점(높음) + 평가위원 4명이 실현가능성 우려",
      "target_score_improvement": "17.5 → 19 (+1.5점, +3%)",
      "suggested_actions": [
        "기존 시스템 연계 아키텍처 추가 제시",
        "파일럿 프로젝트 사례 2-3개 추가",
        "리스크 관리 계획 강화"
      ]
    }},
    {{
      "rank": 2,
      "item_id": "M1",
      "item_title": "관리능력",
      ...
    }},
    ...
  ]
}}

### 6️⃣ 최종 요약 (1페이지 Executive Summary)

- 현재 점수: XX점 (70-84점 범위 = 보통)
- 강점: 기술혁신성은 높이 평가 (평균 17.5/20)
- 약점: 관리/실현가능성 우려 (평균 14/20)
- 개선 시 예상 점수: YY점 (5-10점 상향 가능)
- 우선 개선 항목: 3개 (T1, M1, OB1)

응답 형식:
{{
  "executive_summary": {{
    "current_score": 72.5,
    "score_range": "보통 (70-84점)",
    "win_probability": "보통",
    "key_strength": "기술혁신성 평가 높음",
    "key_weakness": "관리/실현가능성 우려",
    "improvement_potential": "+5-10점",
    "top_3_actions": [
      "기술 실현가능성 검증 (파일럿 사례)",
      "리스크/변화관리 계획 강화",
      "기존 시스템 연계 방안 상세화"
    ]
  }}
}}

---

최종 응답:
{{
  "items_analysis": [...],
  "evaluators_analysis": [...],
  "divergent_items": [...],
  "common_concerns": [...],
  "improvement_priorities": [...],
  "executive_summary": {{...}}
}}
"""

    try:
        analysis = await claude_generate(
            prompt=prompt,
            response_format="json",
            temperature=0.3,
        )

        return {
            "mock_evaluation_analysis": analysis,
            "current_phase": "mock_evaluation_analysis_complete",
        }

    except Exception as e:
        logger.error(f"mock_evaluation_analysis 실패: {e}")
        return {
            "mock_evaluation_analysis": {"error": str(e)},
            "current_phase": "mock_evaluation_analysis_error",
        }
```

---

## 👤 STEP 11A (강화): review_mock_eval Human Review

### 목적

Human이 **정렬된 평가의견을 보면서** feedback을 입력하고,
수정 지시를 내릴 수 있도록 합니다.

### Human Review Panel 구조

```
┌─────────────────────────────────────────────────────────┐
│        STEP 11A: 모의평가 결과 검토 & 피드백              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [Executive Summary]                                     │
│ ┌───────────────────────────────────────────────────┐  │
│ │ 현재 점수: 72.5점 (보통)                           │  │
│ │ 강점: 기술혁신성 평가 높음 (17.5/20)              │  │
│ │ 약점: 관리능력 우려 (14/20)                        │  │
│ │ 개선 시 예상 점수: 78-82점                        │  │
│ │ 우선 개선 항목: ① 기술 실현가능성 ② 리스크 관리  │  │
│ └───────────────────────────────────────────────────┘  │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│ [평가항목별 분석]                                       │
│                                                         │
│ 📊 기술혁신성 (T1) — 20점                               │
│ ├─ 평균 점수: 17.5점 (높음) ✅                         │
│ ├─ 점수 분포: [16, 18, 19, 17, 16, 18]               │
│ ├─ 평가위원 의견:                                     │
│ │  최교수: "신기술 도입 적극 평가" (19점)             │
│ │  이산업: "신기술이나 현장 적용성 의심" (16점)       │
│ │  정소장: "기술 완성도 높지만 검증 부족" (17점)      │
│ │  (나머지 3명)                                       │
│ ├─ 공통 의견:                                         │
│ │  ✅ 강점: AI 기술 수준 높음, 혁신성 인정            │
│ │  ⚠️ 약점: 파일럿 경험 부족, 적용성 검증 미흡       │
│ └─ 개선 제안: 파일럿 사례 2-3개 추가                   │
│                                                         │
│ 📊 관리능력 (M1) — 20점                                 │
│ ├─ 평균 점수: 14점 (낮음) ⚠️                          │
│ ├─ 점수 분포: [14, 13, 15, 14, 13, 15]               │
│ ├─ 평가위원 의견:                                     │
│ │  이산업: "위험관리 계획 미흡" (14점)                │
│ │  홍정책: "변화관리 능력 의심" (13점)                │
│ │  (나머지)                                           │
│ ├─ 공통 의견:                                         │
│ │  ⚠️ 약점: 리스크 대응, 변화관리 계획 부족          │
│ └─ 개선 제안: 위험관리 계획 상세화, 비상 대응 추가    │
│                                                         │
│ (나머지 평가항목들...)                                 │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│ [평가위원별 관점]                                       │
│                                                         │
│ 👤 이산업 (산업계-개발이사) — 68점 (4위/6명)           │
│ └─ 성향: 보수적 (기술보다 실현가능성 중시)             │
│    ✅ 인정한 강점: 기술 수준                           │
│    ⚠️ 지적한 약점: 현장 적용성, 위험관리             │
│                                                         │
│ 👤 최교수 (학계-교수) — 76점 (1위/6명)                │
│ └─ 성향: 낙관적 (신기술 중시)                          │
│    ✅ 인정한 강점: AI 혁신, 이론적 근거               │
│    ⚠️ 우려: 단기 완성도                               │
│                                                         │
│ (나머지 평가위원들...)                                 │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│ [의견 불일치 항목 (논쟁 여지)]                         │
│                                                         │
│ 🔴 기술혁신성 (T1): 점수 편차 = 3.2 (큰 편차)        │
│    높게 평가: 최교수 (19) — "신기술 혁신성 높음"       │
│    낮게 평가: 이산업 (16) — "현장 적용성 의심"        │
│    → 해결책: 실제 파일럿 사례로 입증                  │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│ [공통 우려사항 (모두가 언급)]                          │
│                                                         │
│ 🔴 기존 시스템 연계 방안 미흡 (5명 언급)              │
│    └─ 영향도: HIGH | 해결책: 아키텍처 상세화          │
│                                                         │
│ 🟡 변화관리 계획 부족 (4명 언급)                       │
│    └─ 영향도: MEDIUM | 해결책: 변화관리 계획 추가     │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│ [개선 우선순위 추천]                                   │
│                                                         │
│ ① 우선순위 1: 기술혁신성 강화                          │
│    대상 점수: 17.5 → 19 (+1.5점)                     │
│    방법: 파일럿 사례 2-3개 추가                       │
│    예상 효과: 전체 점수 +1.5점                        │
│                                                         │
│ ② 우선순위 2: 관리능력 강화                            │
│    대상 점수: 14 → 16 (+2점)                         │
│    방법: 리스크/변화관리 계획 상세화                  │
│    예상 효과: 전체 점수 +2점                          │
│                                                         │
│ ③ 우선순위 3: 기존 시스템 연계                         │
│    대상 점수: 15 → 17 (+2점)                         │
│    방법: 기술 아키텍처 보강                           │
│    예상 효과: 전체 점수 +2점                          │
│                                                         │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│ [Human Feedback 입력]                                  │
│                                                         │
│ ☐ Approved (점수 만족, 다음 단계)                     │
│                                                         │
│ ☐ Rework (수정 지시)                                  │
│                                                         │
│    개선 대상 항목 선택 (복수 선택 가능):               │
│    ☐ T1 기술혁신성 (파일럿 사례 추가)                │
│    ☐ M1 관리능력 (리스크 관리 강화)                  │
│    ☐ OB1 기존시스템연계 (아키텍처 보강)             │
│                                                         │
│    우선순위 선택:                                       │
│    (O) 자동 우선순위 (AI 추천)                        │
│    ( ) 직접 입력:                                      │
│           1순위: [▼ T1], 2순위: [▼ M1], ...          │
│                                                         │
│    피드백 입력 (선택사항):                             │
│    ┌──────────────────────────────────────────────┐  │
│    │ 특히 기술 실현가능성에 대한 우려가 높으니,   │  │
│    │ 파일럿 프로젝트 사례를 더 구체적으로 제시해 │  │
│    │ 달라. 기간, 규모, 성과 지표 등...            │  │
│    └──────────────────────────────────────────────┘  │
│                                                         │
│ [Submit]                                               │
│                                                         │
│ ☐ Re-evaluate (재평가)                                │
│                                                         │
│    이유 (선택사항):                                     │
│    ┌──────────────────────────────────────────────┐  │
│    │ 평가위원별 성향이 너무 갈려있어서, 제안       │  │
│    │ 내용을 더 명확히 한 후 재평가 요청            │  │
│    └──────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### State 필드 추가

```python
class ProposalState(TypedDict):
    # ... 기존 필드들 ...

    # STEP 11A 피드백
    mock_evaluation_analysis: Optional[dict]  # 분석 결과
    mock_eval_feedback: Optional[dict]  # Human 피드백
    mock_eval_rework_targets: Annotated[list[str], _replace]  # 수정 대상 (e.g., ["T1", "M1"])
    mock_eval_feedback_text: Annotated[str, _replace]  # 추가 피드백
```

---

## 🔄 STEP 11A-피드백: process_mock_eval_feedback (신규 노드)

### 목적

Human의 피드백 입력을 받아서 **실제 수정 지시로 변환**합니다.

```python
async def process_mock_eval_feedback(state: ProposalState) -> dict:
    """Human 피드백 → 수정 지시 변환"""

    feedback = state.get("mock_eval_feedback", {})
    action = feedback.get("action", "approved")  # approved | rework | re_evaluate
    rework_targets = feedback.get("rework_targets", [])  # ["T1", "M1"]
    feedback_text = feedback.get("feedback_text", "")

    if action == "approved":
        return {
            "current_phase": "mock_evaluation_approved",
            "next_step": "convergence_gate",  # 발표 준비
        }

    elif action == "rework":
        # 각 rework_target을 분석항목 ID로 변환
        rework_sections = _map_eval_items_to_sections(
            rework_targets,
            state.get("rfp_analysis", {}).get("eval_items", [])
        )

        # 각 섹션에 대한 수정 지시 생성
        rework_instructions = await _generate_rework_instructions(
            rework_targets,
            state.get("mock_evaluation_analysis", {}),
            feedback_text,
            state.get("proposal_sections", [])
        )

        return {
            "current_phase": "mock_eval_rework_initiated",
            "rework_targets": rework_sections,
            "rework_instructions": rework_instructions,
            "next_step": "proposal_start_gate",  # 섹션 재작성
        }

    elif action == "re_evaluate":
        return {
            "current_phase": "mock_eval_re_evaluation_requested",
            "re_eval_reason": feedback_text,
            "next_step": "mock_evaluation",  # 모의평가 재실행
        }

    return {
        "current_phase": "mock_eval_feedback_error",
    }


def _map_eval_items_to_sections(eval_item_ids: list[str], eval_items: list) -> list[str]:
    """평가항목 ID → 섹션 ID로 매핑

    예: T1_기술혁신성 → 기술적수행방안 섹션
    """
    mapping = {
        "T1": ["기술적수행방안"],
        "T2": ["기술적수행방안"],
        "M1": ["사업관리", "리스크관리"],
        "OB1": ["기존시스템연계", "아키텍처"],
    }

    rework_sections = []
    for item_id in eval_item_ids:
        if item_id in mapping:
            rework_sections.extend(mapping[item_id])

    return list(set(rework_sections))  # 중복 제거


async def _generate_rework_instructions(
    rework_targets: list[str],
    analysis: dict,
    feedback_text: str,
    proposal_sections: list
) -> dict:
    """각 섹션별 수정 지시 생성"""

    instructions = {}

    improvement_priorities = analysis.get("improvement_priorities", [])

    for priority in improvement_priorities:
        item_id = priority.get("item_id")
        if item_id not in rework_targets:
            continue

        # 해당 평가항목의 상세 분석
        item_analysis = next(
            (item for item in analysis.get("items_analysis", [])
             if item["item_id"] == item_id),
            None
        )

        if not item_analysis:
            continue

        instruction = {
            "eval_item_id": item_id,
            "eval_item_title": priority.get("item_title"),
            "current_score": item_analysis.get("average_score"),
            "target_score": priority.get("target_score_improvement", "").split("→")[-1].strip().split()[0],
            "key_concern": item_analysis.get("common_weaknesses"),
            "suggested_actions": priority.get("suggested_actions", []),
            "evaluator_feedback": [
                {
                    "evaluator_name": concern.get("name"),
                    "concern": concern.get("concern")
                }
                for concern in item_analysis.get("individual_concerns", [])
            ],
            "additional_feedback": feedback_text if item_id == rework_targets[0] else ""
        }

        instructions[item_id] = instruction

    return instructions
```

### 라우팅

```python
def route_after_mock_eval_review(state: ProposalState) -> str:
    """모의평가 검토 후 라우팅 (강화)"""

    action = state.get("mock_eval_feedback", {}).get("action", "")

    if action == "approved":
        return "approved"  # convergence_gate 진행

    elif action == "rework":
        return "rework"  # proposal_start_gate (섹션 재작성)

    elif action == "re_evaluate":
        return "re_evaluate"  # mock_evaluation 재실행

    return "rejected"  # 기본
```

---

## 📊 수정 지시 구조 (Human이 받는 정보)

```python
rework_instructions = {
    "T1": {
        "eval_item_id": "T1",
        "eval_item_title": "기술혁신성",
        "current_score": 17.5,
        "target_score": "19",
        "key_concern": [
            "파일럿 경험 부족",
            "적용성 검증 미흡"
        ],
        "suggested_actions": [
            "파일럿 프로젝트 사례 2-3개 추가",
            "각 사례마다: 프로젝트명, 기간, 규모, 성과 지표",
            "리스크 관리 계획 강화"
        ],
        "evaluator_feedback": [
            {
                "evaluator_name": "이산업",
                "concern": "현장 적용성 의심"
            },
            {
                "evaluator_name": "정소장",
                "concern": "검증 프로세스 부족"
            }
        ],
        "additional_feedback": "파일럿 사례에서 실제 성과 수치를 강조해주세요"
    },
    "M1": {
        "eval_item_id": "M1",
        "eval_item_title": "관리능력",
        "current_score": 14,
        "target_score": "16",
        "key_concern": [
            "위험관리 계획 미흡",
            "변화관리 능력 의심"
        ],
        "suggested_actions": [
            "리스크 매트릭스 (Risk × Impact) 추가",
            "위험별 대응 계획 구체화",
            "변화관리 프로세스 (교육, 의사소통) 추가"
        ],
        "evaluator_feedback": [...]
    }
}
```

---

## 🎯 Human의 의사결정 흐름

### Case 1: 점수 만족 → Approved

```
평가의견 확인
  ↓
"기술혁신성 17.5점, 관리능력 14점이구나"
"이 정도면 충분하다" 또는 "더 개선할 시간이 없다"
  ↓
[Approved] 선택
  ↓
STEP 12: 발표 준비 진행
```

### Case 2: 특정 항목만 개선 → Rework

```
평가의견 확인
  ↓
"관리능력(14점)이 너무 낮다"
"기술혁신성은 괜찮은데 현장 적용성이 우려네"
  ↓
[Rework] 선택
  ↓
개선 대상 선택:
☑ T1 기술혁신성 (파일럿 사례 추가)
☑ M1 관리능력 (리스크 관리 강화)
☐ OB1 기존시스템연계
  ↓
피드백 입력:
"T1에서는 실제 수치 강조, M1에서는 변화관리 프로세스 추가"
  ↓
[Submit]
  ↓
STEP 8A: 해당 섹션만 재작성
      (T1 관련 기술 섹션 + M1 관련 관리 섹션)
  ↓
다시 AI 자체 검증 → Human Review
  ↓
만족하면 다음 단계
```

### Case 3: 의견이 너무 갈려서 → Re-evaluate

```
평가의견 확인
  ↓
"최교수는 19점, 이산업은 16점?"
"평가위원 의견이 너무 갈려있다"
  ↓
[Re-evaluate] 선택
  ↓
이유 입력:
"제안 내용의 명확성을 높인 후 다시 평가해달라"
  ↓
[Submit]
  ↓
STEP 10A: 모의평가 재실행
      (6명이 다시 평가)
  ↓
STEP 11A: 다시 검토
```

---

## 🔗 그래프 통합

### 기존 (v6.0)

```
... → ppt_review → mock_evaluation → review_mock_eval → convergence
```

### 신규 (v6.1)

```
... → ppt_review
      → mock_evaluation (6명 평가 + 점수)
      → mock_evaluation_analysis (정렬 & 분석) ← NEW
      → review_mock_eval (Human Review + 피드백)
      → process_mock_eval_feedback (피드백 처리) ← NEW
      → (라우팅: approved/rework/re_evaluate)
          ├─ approved → convergence
          ├─ rework → proposal_start_gate
          └─ re_evaluate → mock_evaluation
```

---

## ✅ 구현 체크리스트

### Phase A: Analysis 노드 (1일)
- [ ] `mock_evaluation_analysis` 함수
- [ ] AI 분석 프롬프트
- [ ] 그래프 노드 등록

### Phase B: Human Review UI (1일)
- [ ] Panel 설계 및 구현
- [ ] Feedback 입력 폼
- [ ] 항목별/평가위원별 정렬 표시

### Phase C: Feedback Processing 노드 (1일)
- [ ] `process_mock_eval_feedback` 함수
- [ ] 수정 지시 생성
- [ ] 라우팅 구현

### Phase D: Integration & Testing (1일)
- [ ] End-to-End 테스트
- [ ] 각 라우팅 경로 검증
- [ ] 성능 최적화

---

**설계 완료**: ✅ 2026-03-29
**예상 구현**: 4일
**상태**: Ready for Implementation
