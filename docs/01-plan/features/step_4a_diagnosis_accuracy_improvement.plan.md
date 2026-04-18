---
feature: step_4a_diagnosis_accuracy_improvement
phase: plan
version: v1.0
created: 2026-04-18
updated: 2026-04-18
status: active
---

# STEP 4A 섹션 진단 정확도 향상 계획 (Harness Engineering 고도화)

## Executive Summary

| 관점 | 내용 |
|------|------|
| **문제** | Harness Engineering의 자동 품질 평가(hallucination, persuasiveness, completeness, clarity)에서 False Negative/Positive 발생, 처리 시간 초과, 사용자 피드백 미반영 |
| **해결책** | 진단 정확도 메트릭 정의 → 검증 강화(Confidence Thresholding, Multi-Model Voting) → 알고리즘 개선(Weight Tuning, Feedback Integration) → 모니터링 시스템 구축 |
| **기능/경험** | 섹션당 평가 정확도 90%→97%로 향상, 진단 신뢰도 시각화, 사용자 반박 학습 루프 |
| **핵심 가치** | 제안서 품질 신뢰도 ⬆️, AI 진단 오류 ⬇️, 사용자 만족도 ⬆️ |

## Context Anchor

| Context | 설명 |
|---------|------|
| **WHY** | Harness Engineering의 평가 정확도 향상은 제안서 최종 품질 신뢰도와 직결. False Negative(놓친 결점)는 제출 후 오류 발생, False Positive(과도한 지적)는 사용자 피로도 증대 |
| **WHO** | tenopa 내부 인력: 제안서 작성자(평가 신뢰도 개선 원함), PM(품질 지표 필요), 기술 팀(Harness 고도화 담당) |
| **RISK** | 모델 재학습 비용 증가, 평가 시간 증가로 UX 저하 가능, 평가 메트릭 정의 오류 시 신뢰도 악화 |
| **SUCCESS** | 평가 정확도 90%→97%, False Negative/Positive 50% 감소, Latency 20% 개선, 사용자 피드백 반영율 100% |
| **SCOPE** | Harness Engineering 기존 4-step(Generator/Evaluator/Selector/FeedbackLoop) 위에 정확도 강화 계층 추가. Phase별 구현. |

---

## 1. 요구사항 정의

### 1.1 현재 상태 분석

**Harness Engineering 현황**:
- ✅ 완료: 3-variant 병렬 생성, 5가지 메트릭 평가(hallucination 35%, persuasiveness 25%, completeness 25%, clarity 15%), 피드백 루프(max 3회)
- ❌ 미흡: 평가 정확도 메트릭 부재, False Negative/Positive 추적 불가, 평가 신뢰도 점수 없음, 사용자 피드백 학습 안 됨

**사용자 피드백** (4가지 문제점):
1. **False Negative** (빈틈 미탐지): 실제 결점을 놓치는 경우
2. **False Positive** (오탐지): 사소한 것을 과도하게 지적하는 경우
3. **Latency** (처리 시간): 평가 단계가 너무 오래 걸림
4. **피드백 반영 부족**: 사용자의 승인/거부 데이터를 다음 평가에 활용 못함

### 1.2 목표 설정

#### Primary Goal
**진단 정확도 메트릭 개선**
- 평가 정확도: 90% → 97% (±7%)
- False Negative 감소: 현재 미측정 → 목표 <5%
- False Positive 감소: 현재 미측정 → 목표 <8%
- Latency: 현재 ~26초 → 목표 ~21초 (20% 개선)

#### Secondary Goals
1. 평가 신뢰도 점수 시각화 (사용자가 AI 판단의 확신도 파악)
2. 사용자 피드백 학습 루프 (승인/반박 데이터 → 모델 가중치 튜닝)
3. 섹션별 특화 검증 로직 (Executive Summary ≠ Technical Details)

### 1.3 성공 기준

| # | 기준 | 측정 방법 | 목표값 |
|----|------|---------|-------|
| SC-1 | 평가 정확도 | Test 섹션 50개 검증 후 정확도 계산 | ≥97% |
| SC-2 | False Negative Rate | 실제 결점 기준 미탐지율 | <5% |
| SC-3 | False Positive Rate | 오탐지율 | <8% |
| SC-4 | 처리 시간 | 평가 node 평균 소요 시간 | <21초 |
| SC-5 | 신뢰도 점수 추적 | 평가 결과에 confidence 필드 포함 | 100% |
| SC-6 | 피드백 데이터 수집 | 사용자 피드백 DB 저장 | 100% 저장 |
| SC-7 | 코드 품질 | 타입 힌트 + 단위테스트 커버리지 | ≥90% |

---

## 2. 범위 및 제약

### 2.1 포함 범위 (In Scope)

**Phase 1: 메트릭 정의 & 검증 (Day 1-2)**
- 진단 정확도 메트릭 정의 (Precision, Recall, F1-Score)
- Test Dataset 구성 (50개 섹션 + Ground Truth)
- 현재 Harness 성능 기준선 측정
- Baseline 평가 코드 작성

**Phase 2: 검증 강화 (Day 3-4)**
- Confidence Thresholding: 저신뢰도 평가 필터링
- Multi-Model Voting: 여러 모델로 투표형 평가
- Cross-Validation: Train/Test split으로 과적합 방지
- Latency 프로파일링 및 최적화

**Phase 3: 알고리즘 개선 (Day 5-7)**
- 가중치 튜닝 (hallucination 35% → 40% 등)
- 섹션별 특화 검증 (Executive Summary 전용 규칙)
- 사용자 피드백 통합 (Feedback DB → Model retraining)
- Fallback 메커니즘 (평가 실패 시 대응)

**Phase 4: 모니터링 & 배포 (Day 8)**
- 메트릭 대시보드 구축 (정확도 실시간 모니터링)
- 프로덕션 배포 체크리스트
- E2E 테스트 (전체 워크플로우 검증)

### 2.2 제외 범위 (Out of Scope)

- 새로운 평가 메트릭 추가 (현재 5개 고정)
- 3-variant 생성 로직 변경
- UI 대시보드 개발 (메트릭 API만 제공)
- 다국어 모델 지원

### 2.3 제약 사항

- **시간**: 8일 개발 주기
- **비용**: Claude API 호출 제어 (평가당 최대 $0.02)
- **의존성**: 기존 Harness Engineering 구조 유지
- **호환성**: 기존 graph.py 통합 유지

---

## 3. 주요 기능

### 3.1 Phase 1: 메트릭 정의 & 검증

**메트릭 정의**
```
Precision = True Positives / (True Positives + False Positives)
Recall = True Positives / (True Positives + False Negatives)
F1-Score = 2 * (Precision * Recall) / (Precision + Recall)

Baseline Target: Precision ≥95%, Recall ≥97%, F1 ≥96%
```

**Test Dataset 구성**
- 50개 제안 섹션 (Executive Summary, Technical Details, etc.)
- 각 섹션마다 Ground Truth 라벨링
  - hallucination_severity (none/low/medium/high)
  - persuasiveness_level (1-5)
  - completeness_score (0-100%)
  - clarity_rating (1-5)
- 현재 Harness 평가값과 비교

**Baseline 측정 코드**
```python
# app/services/harness_accuracy_validator.py
class DiagnosisAccuracyValidator:
    async def evaluate_baseline(self, test_dataset) -> AccuracyMetrics:
        """Harness 현재 성능 측정"""
        results = []
        for section in test_dataset:
            predicted = await self.evaluator.evaluate(section.content)
            actual = section.ground_truth
            results.append({
                "section_id": section.id,
                "predicted": predicted,
                "actual": actual,
                "match": self._compare(predicted, actual)
            })
        return self._calculate_metrics(results)

    def _calculate_metrics(self, results):
        """Precision, Recall, F1 계산"""
        tp = sum(1 for r in results if r["match"] == "true_positive")
        fp = sum(1 for r in results if r["match"] == "false_positive")
        fn = sum(1 for r in results if r["match"] == "false_negative")
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return AccuracyMetrics(
            precision=precision,
            recall=recall,
            f1=f1,
            false_negative_count=fn,
            false_positive_count=fp
        )
```

### 3.2 Phase 2: 검증 강화

**Confidence Thresholding**
```python
# 저신뢰도 평가 필터링
if evaluation.confidence < 0.75:
    # 다시 평가하거나 사용자에게 확인 요청
    return {
        "status": "low_confidence",
        "suggested_action": "manual_review",
        "confidence_score": evaluation.confidence
    }
```

**Multi-Model Voting**
```python
# 여러 온도에서 평가
evaluations = []
for temp in [0.1, 0.3, 0.5]:  # Conservative, Balanced, Creative
    eval_result = await evaluator.evaluate(section, temperature=temp)
    evaluations.append(eval_result)

# Voting: 3개 중 2개 이상 동의하면 확정
consensus = self._determine_consensus(evaluations)
```

**Cross-Validation**
```python
# Train/Test split (80/20)
train_set, test_set = split_dataset(test_dataset, ratio=0.8)

# Train: 평가 가중치 최적화
trained_weights = await self._train_weights(train_set)

# Test: 독립적 검증
metrics = await self._validate_on_test_set(test_set, trained_weights)
```

### 3.3 Phase 3: 알고리즘 개선

**가중치 튜닝**
```python
# 현재: hallucination 35%, persuasiveness 25%, completeness 25%, clarity 15%
# 개선: 데이터 기반 최적화

# Approach: Grid Search
weights_candidates = [
    {hallucination: 0.40, persuasiveness: 0.25, completeness: 0.20, clarity: 0.15},
    {hallucination: 0.38, persuasiveness: 0.27, completeness: 0.22, clarity: 0.13},
    {hallucination: 0.42, persuasiveness: 0.23, completeness: 0.20, clarity: 0.15},
]

best_weights = max(weights_candidates, key=lambda w: calculate_f1(w, train_set))
```

**섹션별 특화 검증**
```python
# Executive Summary 전용 규칙
executive_rules = {
    "min_completion": 90,  # 완성도 최소 90%
    "max_hallucination": 0.1,  # 허위 최대 10%
    "persuasiveness_weight": 0.3,  # 설득력 가중치 증가
}

# Technical Details 전용 규칙
technical_rules = {
    "min_completion": 95,  # 더 높은 완성도 요구
    "max_hallucination": 0.05,  # 더 엄격
    "clarity_weight": 0.2,  # 명확성 강조
}

evaluation = await evaluator.evaluate(section, rules=section_specific_rules[section.type])
```

**사용자 피드백 통합**
```python
# 사용자가 평가를 승인/거부하면 DB에 저장
@app.post("/api/artifacts/evaluate-feedback")
async def save_evaluation_feedback(feedback: EvaluationFeedback):
    """
    feedback = {
        "evaluation_id": "...",
        "user_decision": "approved" | "rejected",
        "reason": "사용자 지적사항",
        "corrected_scores": {
            "hallucination": 0.1,  # 사용자가 수정한 점수
            "persuasiveness": 0.8,
        }
    }
    """
    # 피드백 저장
    await db.save_feedback(feedback)
    
    # 주기적으로 피드백 데이터로 모델 재학습
    if await db.count_new_feedback() > 100:  # 100개 누적되면
        await retrain_model_with_feedback()
```

### 3.4 Phase 4: 모니터링 & 배포

**메트릭 대시보드 API**
```python
@app.get("/api/metrics/harness-accuracy")
async def get_harness_accuracy_metrics():
    """
    Response:
    {
        "current_metrics": {
            "precision": 0.97,
            "recall": 0.97,
            "f1_score": 0.97,
            "false_negative_rate": 0.03,
            "false_positive_rate": 0.05,
            "avg_latency_seconds": 21.5,
            "confidence_distribution": {
                "high": 0.85,   # >=0.9
                "medium": 0.10,  # 0.75-0.9
                "low": 0.05     # <0.75
            }
        },
        "trend": {
            "precision_7d": [0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.97],
            "recall_7d": [0.92, 0.93, 0.94, 0.96, 0.97, 0.97, 0.97]
        },
        "recommendations": [
            "hallucination 메트릭 가중치 3% 증가 권장",
            "섹션별 평가 규칙 미세조정 필요"
        ]
    }
    """
```

---

## 4. 설계 접근법

### 4.1 아키텍처

```
┌─────────────────────────────────────────────┐
│  Harness Engineering (기존 4-Step)          │
│  Generator → Evaluator → Selector → Feedback│
└────────────┬────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────┐
│  Accuracy Enhancement Layer (신규)          │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ 1. Confidence Thresholding            │  │
│  │    (저신뢰도 평가 필터링)              │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ 2. Multi-Model Voting                │  │
│  │    (여러 온도에서 투표형 평가)        │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ 3. Weight Tuning Engine               │  │
│  │    (데이터 기반 메트릭 가중치 조정)  │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ 4. Feedback Integration Loop          │  │
│  │    (사용자 피드백 → 모델 재학습)      │  │
│  └──────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────┐  │
│  │ 5. Metrics Monitoring & Dashboard     │  │
│  │    (실시간 정확도 모니터링)           │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────┐
│  LangGraph Integration                       │
│  (proposal_nodes.py → harness + accuracy)   │
└─────────────────────────────────────────────┘
```

### 4.2 데이터 모델

```python
# 새로운 데이터 구조
class AccuracyMetrics(BaseModel):
    precision: float  # True Positives / (TP + FP)
    recall: float     # True Positives / (TP + FN)
    f1_score: float   # 2 * (Precision * Recall) / (P + R)
    false_negative_count: int
    false_positive_count: int
    avg_latency_seconds: float
    confidence_distribution: dict  # {high: %, medium: %, low: %}
    timestamp: datetime

class EvaluationFeedback(BaseModel):
    evaluation_id: str
    user_decision: Literal["approved", "rejected"]
    reason: Optional[str]
    corrected_scores: Optional[Dict[str, float]]
    section_type: str
    timestamp: datetime

class WeightConfig(BaseModel):
    hallucination_weight: float
    persuasiveness_weight: float
    completeness_weight: float
    clarity_weight: float
    section_type: Optional[str]  # null = default, "executive_summary" = specific
```

---

## 5. 구현 계획

### 5.1 Phase 별 마일스톤

| Phase | 목표 | 파일 | 기간 | 검증 |
|-------|------|------|------|------|
| **Phase 1** | 메트릭 정의 & Baseline | `harness_accuracy_validator.py`, test_dataset.json | D1-2 | Baseline 측정 완료 |
| **Phase 2** | 검증 강화 (Confidence + Voting + CV) | `harness_accuracy_enhancement.py` | D3-4 | Latency 프로파일링 완료 |
| **Phase 3** | 알고리즘 개선 (Weight Tuning + Feedback) | `harness_weight_tuner.py`, DB schema 확장 | D5-7 | F1-Score ≥96% 달성 |
| **Phase 4** | 모니터링 & 배포 | `routes_metrics.py`, E2E 테스트 | D8 | 프로덕션 준비 완료 |

### 5.2 핵심 파일 (생성/수정)

**신규 생성**:
1. `app/services/harness_accuracy_validator.py` (400줄)
   - DiagnosisAccuracyValidator 클래스
   - Baseline 측정, Precision/Recall/F1 계산
   
2. `app/services/harness_accuracy_enhancement.py` (350줄)
   - Confidence Thresholding
   - Multi-Model Voting
   - Cross-Validation
   
3. `app/services/harness_weight_tuner.py` (300줄)
   - Weight Grid Search
   - Section-Specific Rules
   - Feedback Integration
   
4. `tests/test_harness_accuracy.py` (250줄)
   - Validator 단위 테스트 (5개)
   - Enhancement 통합 테스트 (4개)
   - Weight Tuner 테스트 (3개)
   
5. `data/test_datasets/harness_test_50_sections.json` (500줄)
   - 50개 섹션 + Ground Truth 라벨

6. `app/api/routes_metrics.py` (150줄)
   - GET /api/metrics/harness-accuracy
   - GET /api/metrics/harness-accuracy-trend
   - POST /api/artifacts/evaluate-feedback

**기존 수정**:
1. `app/services/harness_evaluator.py` (+50줄)
   - confidence 필드 추가
   
2. `app/graph/nodes/proposal_nodes.py` (+30줄)
   - accuracy enhancement layer 통합
   
3. Database schema (+2개 테이블)
   - evaluation_feedback (사용자 피드백)
   - harness_metrics_log (메트릭 이력)

---

## 6. 성공 기준 및 검증 전략

### 6.1 테스트 전략

**Unit Tests** (95개 케이스):
- Validator: Baseline 측정, 메트릭 계산 (15개)
- Enhancement: Confidence 필터링, Voting 로직 (20개)
- Weight Tuner: Grid Search, 섹션별 규칙 (15개)
- Metrics API: 응답 형식, 데이터 무결성 (10개)

**Integration Tests** (8개):
- E2E 평가 → 피드백 → 모델 재학습 (1개)
- 전체 워크플로우 Latency 측정 (1개)
- DB 피드백 저장 & 조회 (1개)

**Acceptance Tests**:
- Test Dataset 50개 섹션에서 F1 ≥96% (1개)
- False Negative < 5%, False Positive < 8% (1개)
- Latency < 21초 (1개)

### 6.2 검증 기준

| 기준 | 현재 | 목표 | 검증 방법 |
|------|------|------|---------|
| F1-Score | ?[Baseline 측정] | ≥0.96 | Test 50개 섹션 |
| Precision | ? | ≥0.95 | TP/(TP+FP) |
| Recall | ? | ≥0.97 | TP/(TP+FN) |
| FN Rate | ? | <5% | 50개 중 미탐지 수 |
| FP Rate | ? | <8% | 50개 중 오탐지 수 |
| Avg Latency | ~26초 | <21초 | 100회 평가 평균 |
| Confidence Score | 없음 | 100% 포함 | 모든 평가에 confidence 필드 |
| Test Coverage | - | ≥90% | pytest --cov |

---

## 7. 위험 관리

| 위험 | 영향 | 확률 | 대응책 |
|------|------|------|-------|
| Ground Truth 라벨링 오류 | Baseline 신뢰도 저하 | 중간 | 인간 검토 2회, 리뷰자 합의 |
| Weight Tuning 과적합 | Test Set에서만 높은 성능 | 중간 | K-Fold Cross-Validation (5-fold) |
| Multi-Model Voting 비용 증가 | Claude API 비용 3배 증가 | 중간 | 선택적 Voting (저신뢰도만 적용) |
| Latency 악화 | UX 저하 | 낮음 | 검증 캐싱, 비동기 처리 |
| 피드백 데이터 부족 | 모델 재학습 지연 | 낮음 | 초기 3개월은 수동 피드백 수집 |

---

## 8. 의존성 및 전제 조건

### 8.1 기술 의존성
- ✅ Harness Engineering 기존 4-Step 완료
- ✅ Claude API (평가 모델)
- ✅ Supabase DB (피드백 저장)
- ✅ FastAPI (메트릭 API)

### 8.2 전제 조건
- Test Dataset 구성 (인간 라벨링)
- 현재 Harness 성능 Baseline 측정 완료
- 팀 리뷰어 2명 (Ground Truth 라벨링)

---

## 9. 다음 단계

1. **Plan 승인 후**: 
   - Design 문서 생성 (아키텍처 상세, API 스펙, 데이터 모델)
   - Test Dataset 구성 시작

2. **Design 완료 후**:
   - Do 단계: Phase 1-4 순차 구현
   - 각 Phase마다 Check & Act

3. **최종 목표**:
   - STEP 4A 진단 정확도 97% 달성
   - 프로덕션 배포 (2026-04-26 예정)

---

**Plan Document Version**: v1.0  
**Last Updated**: 2026-04-18  
**Next Phase**: Design (아키텍처 상세 설계)
