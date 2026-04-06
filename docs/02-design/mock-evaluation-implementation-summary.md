# 모의평가 구현 완료 보고서

> **구현일**: 2026-03-29
> **상태**: ✅ 완료 (v6.0 설계 기반 구현)
> **코드**: `app/graph/nodes/evaluation_nodes.py` (v6.0)

---

## 📋 구현 개요

### 목표
RFP 평가항목 기반의 현실적인 모의평가 시뮬레이션 구현:
- ✅ 6명 평가위원 (산업계 2명, 학계 2명, 연구계/공공 2명)
- ✅ 평가항목별 독립적 점수 산출
- ✅ 평가위원 성향 반영 (보수/중도/낙관)
- ✅ 분포 분석 및 합의도 평가
- ✅ Human Review 루프 (수정보완 지원)

---

## 🎯 구현 내용

### 1. 평가위원 프로필 정의 (`_create_evaluator_profiles`)

**6명 평가위원 (산학연 2명씩)**

```
산업계 (2명):
├─ evaluator_1: 이산업 (발주유사 - 실현가능성/비용효율성 중심, 보수적)
└─ evaluator_2: 박경쟁 (경쟁 - 차별화/경쟁우위 중심, 중도)

학계 (2명):
├─ evaluator_3: 최교수 (혁신성 - 기술혁신/이론적근거 중심, 낙관적)
└─ evaluator_4: 정소장 (실현가능성 - 기술완성도/리스크 중심, 중도)

연구계/공공 (2명):
├─ evaluator_5: 홍정책 (정책 - 정책부합/법규준수 중심, 보수적)
└─ evaluator_6: 강협회 (표준 - 산업표준/확산가능성 중심, 중도)
```

**프로필 구조**
```python
{
    "id": "evaluator_1",
    "name": "이산업",
    "title": "OOO 회사 개발이사",
    "type": "산업계",
    "experience_years": 15,
    "perspective": ["사업 실현가능성", "비용 효율성", ...],
    "evaluation_bias": {
        "tendency": "보수적",
        "scoring_range": (0, 90),  # 점수 범위 제한
        "weight": 1.0
    }
}
```

### 2. 평가항목별 점수 산출 (`_score_evaluation_item`)

**프로세스**
1. RFP의 eval_items에서 평가항목 추출
2. 각 평가위원이 독립적으로 해당 항목 평가
3. AI(Claude)가 평가위원 관점 시뮬레이션
4. 점수 범위 제한 (evaluator bias 반영)
5. 배점 기준으로 정규화

**산출 결과**
```python
{
    "evaluator_id": "evaluator_1",
    "score": 18.5,  # 0 ~ max_score 범위
    "max_score": 20,
    "reasoning": "요구사항 충족도 우수하나 혁신성 부족",
    "strengths": ["항목1", "항목2"],
    "weaknesses": ["항목A"],
}
```

### 3. 분포 분석 (`_calculate_distribution`)

**6명 평가위원의 점수 분포**
```python
{
    "mean": 72.5,          # 평균
    "median": 75.0,        # 중앙값
    "stdev": 8.3,          # 표준편차 (합의도 지표)
    "variance": 68.9,      # 분산
    "min": 62.0,
    "max": 85.0,
    "range": (62.0, 85.0),
    "scores": [68, 75, 78, 62, 80, 85]
}
```

### 4. 합의도 평가 (`_assess_consensus`)

**평가위원 의견 일치도 판정**
- `stdev < 3`: "높음 (강한 합의)"
- `3 ≤ stdev < 6`: "중간 (약한 합의)"
- `stdev ≥ 6`: "낮음 (의견 분분)" → 🚩 논쟁 여지 있는 항목

### 5. 최종 평가 보고서 구조

```python
mock_evaluation_report = {
    "evaluation_metadata": {
        "total_evaluators": 6,
        "evaluators_by_type": {"산업계": 2, "학계": 2, "연구계/공공": 2},
        "total_evaluation_items": N,
        "final_score": 72.5,
        "percentage": 72.5,
    },
    "evaluators": [
        {
            "id": "evaluator_1",
            "name": "이산업",
            "title": "OOO 회사 개발이사",
            "type": "산업계",
            "experience_years": 15,
        },
        ...
    ],
    "evaluation_items": {
        "T1": {
            "item_id": "T1",
            "item_title": "기술혁신성",
            "max_score": 20,
            "scores_by_evaluator": {...},
            "average_score": 18.3,
            "distribution": {...},
            "consensus": {...},
        },
        ...
    },
    "evaluator_scores": {
        "evaluator_1": {
            "evaluator_id": "evaluator_1",
            "name": "이산업",
            "title": "OOO 회사 개발이사",
            "type": "산업계",
            "total_score": 68.5,
            "rank": 4,
        },
        ...
    },
    "category_scores": {
        "기술": 72.5,
        "가격": 65.0,
        "관리": 75.0,
        ...
    },
    "final_score": 72.5,
    "win_probability": "보통 (70-84점)",
    "strengths": ["강점 1", "강점 2", ...],
    "weaknesses": ["약점 1", "약점 2", ...],
    "high_consensus_items": [...],
    "low_consensus_items": [...],
}
```

---

## 🔄 워크플로우 통합

### 현재 그래프 구조 (v4.0)

**STEP 10A: mock_evaluation** (AI 실행)
```
↓
6A 모의평가 실행
  ├─ RFP eval_items 추출
  ├─ 6명 평가위원 프로필 로드
  ├─ 평가항목별 독립 점수 산출
  ├─ 분포 분석 및 합의도 평가
  └─ 최종 보고서 생성
↓
```

**STEP 11A: review_mock_eval** (Human Review)
```
↓
Human이 모의평가 결과 검토
  ├─ [approved] → 수주 가능성 높음 → convergence (발표 준비)
  ├─ [rework_sections] → 특정 섹션 개선 → proposal_start_gate (재작성)
  ├─ [rework_strategy] → 전략 재검토 → strategy_generate
  └─ [rejected] → 모의평가 재실행 → mock_evaluation
↓
```

### 라우팅 함수 (edges.py)

```python
def route_after_mock_eval_review(state: ProposalState) -> str:
    """모의평가 리뷰 라우팅 (4방향)"""
    approval = state.get("approval", {}).get("mock_evaluation")
    if approval and approval.status == "approved":
        return "approved"

    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}
    rework_targets = latest.get("rework_targets", [])

    if "strategy_generate" in rework_targets:
        return "rework_strategy"
    if rework_targets:
        return "rework_sections"

    return "rejected"
```

### 그래프 엣지 (graph.py)

```python
g.add_edge("mock_evaluation", "review_mock_eval")
g.add_conditional_edges("review_mock_eval", route_after_mock_eval_review, {
    "approved": "convergence_gate",       # → 발표 준비
    "rework_sections": "proposal_start_gate",  # → 섹션 재작성
    "rework_strategy": "strategy_generate",    # → 전략 재검토
    "rejected": "mock_evaluation",        # → 모의평가 재실행
})
```

---

## 📊 구현 세부사항

### 핸들러 함수 목록

| 함수명 | 역할 | 토큰 효율성 |
|--------|------|-----------|
| `mock_evaluation` | 메인 평가 오케스트레이션 | 높음 (섹션 요약) |
| `_score_evaluation_item` | 평가위원 개별 점수 산출 | 중간 (AI 호출 1회/항목) |
| `_calculate_distribution` | 분포 통계 계산 | 낮음 (파이썬 계산) |
| `_assess_consensus` | 합의도 판정 | 낮음 (파이썬 계산) |
| `_summarize_strengths` | 강점 종합 | 낮음 (집계) |
| `_summarize_weaknesses` | 약점 종합 | 낮음 (집계) |
| `_find_high_consensus_items` | 높은 합의 항목 | 낮음 (필터링) |
| `_find_low_consensus_items` | 논쟁 여지 항목 | 낮음 (필터링) |
| `_assess_win_probability` | 수주 가능성 판정 | 낮음 (규칙 기반) |

### AI 호출 전략

**효율성 최적화**
- 섹션은 상위 12개만 요약 (토큰 절약)
- 평가항목당 1회 AI 호출 (평가위원 성향 시뮬레이션)
- JSON 응답 포맷 지정 (파싱 안정성)
- 온도 낮음 (0.3) → 일관성 확보

**폴백 전략**
- AI 호출 실패 시 배점의 50% 중간값 할당
- 분포 계산 시 스코어 누락 → 스킵
- 평가항목 누락 → 경고 로그

---

## ✅ 완료 항목

### 코드 변경사항

| 파일 | 변경사항 | 라인 수 |
|-----|---------|--------|
| `app/graph/nodes/evaluation_nodes.py` | 모의평가 전면 재구현 | +400줄 |
| `app/graph/edges.py` | route_after_mock_eval_review 강화 | +20줄 |
| `app/graph/graph.py` | 4방향 라우팅 추가 | +3줄 |

### 신규 헬퍼 함수

- `_create_evaluator_profiles()`: 6명 평가위원 프로필
- `_score_evaluation_item()`: 항목별 점수 산출
- `_calculate_distribution()`: 분포 통계
- `_assess_consensus()`: 합의도 판정
- `_summarize_strengths()`: 강점 종합
- `_summarize_weaknesses()`: 약점 종합
- `_find_high_consensus_items()`: 높은 합의 항목
- `_find_low_consensus_items()`: 논쟁 항목
- `_assess_win_probability()`: 수주 가능성

### 상태 필드

| 필드 | 타입 | 설명 |
|-----|------|------|
| `mock_evaluation_result` | Optional[dict] | 6A 모의평가 결과 (이미 정의됨) |
| `current_phase` | str | "mock_evaluation_complete" |

---

## 🧪 검증

### 컴파일 확인
```
✅ Python syntax check: PASS
✅ Import validation: PASS
✅ Type annotations: PASS
✅ Function signatures: PASS
```

### 런타임 검증
```
✅ Evaluator profiles: 6명 생성 확인
✅ Profile types: 산업계, 학계, 연구계/공공 확인
✅ Graph edges: 4방향 라우팅 설정 확인
✅ State fields: mock_evaluation_result 필드 존재 확인
```

---

## 🚀 사용 방법

### 워크플로우 실행

1. **PPT 완료 후** → 자동으로 `mock_evaluation` 노드 진입
2. **AI 실행**: RFP eval_items 기반 6명 평가 → 최종 보고서 생성
3. **Human Review**: `review_mock_eval` 노드에서 결과 검토
4. **라우팅 선택**:
   - ✅ **승인**: 발표 준비 진행
   - 🔄 **섹션 개선**: 특정 섹션 재작성
   - 🔄 **전략 재검토**: 전략부터 재시작
   - ❌ **재평가**: 모의평가 다시 실행

### API 응답 예시

```json
{
  "mock_evaluation_result": {
    "evaluation_metadata": {
      "total_evaluators": 6,
      "final_score": 72.5,
      "win_probability": "보통 (70-84점)"
    },
    "evaluation_items": {
      "T1": {
        "item_title": "기술혁신성",
        "average_score": 18.3,
        "consensus": {
          "consensus_level": "높음",
          "stdev": 2.1
        }
      }
    },
    "strengths": ["강점1", "강점2"],
    "weaknesses": ["약점1"],
    "high_consensus_items": [...],
    "low_consensus_items": [...]
  },
  "current_phase": "mock_evaluation_complete"
}
```

---

## 📝 다음 단계

### 1. 프론트엔드 연동 (선택사항)
- MockEvaluationPanel 컴포넌트 개발
- 평가항목별/평가위원별 결과 시각화
- 합의도 시각화 (표준편차 표시)

### 2. 인터럽트 개선 (선택사항)
- review_mock_eval에서 상세 피드백 입력 지원
- rework_targets 선택 UI
- 평가 코멘트 기반 개선 제안

### 3. 테스트 케이스
- 다양한 eval_items 구조 테스트
- AI 오류 폴백 검증
- 분포 통계 정확성 검증

---

## 📚 참고 문서

- 설계 상세: `mock-evaluation-detailed-design.md`
- 그래프 설계: `langgraph-optimized-v6.0-revised.md`
- 상태 정의: `app/graph/state.py` (ProposalState.mock_evaluation_result)
- 라우팅: `app/graph/edges.py` (route_after_mock_eval_review)

---

**구현 완료**: ✅ 2026-03-29
**검증 상태**: ✅ PASS
**배포 준비**: ⏳ 테스트 완료 후 배포
