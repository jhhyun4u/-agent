---
feature: step_4a_diagnosis_accuracy_improvement
phase: design
version: v1.0
architecture: Option B - Clean Architecture
created: 2026-04-18
updated: 2026-04-18
status: active
---

# STEP 4A 섹션 진단 정확도 향상 설계 (Option B: Clean Architecture)

## Overview

**선택 아키텍처**: Clean Architecture with Modular Accuracy Enhancement Layer
- 별도의 4개 서비스 모듈로 정확도 강화 계층 구현
- DB 스키마 확장 (evaluation_feedback, harness_metrics_log)
- 각 Phase마다 명확한 마일스톤

## Context Anchor

| Context | 설명 |
|---------|------|
| **WHY** | Harness Engineering의 평가 정확도가 제안서 최종 품질 신뢰도를 결정함. False Negative는 놓친 결점 → 제출 후 오류, False Positive는 과도한 지적 → 사용자 피로도 증대. 정확도 97% 달성이 핵심 목표 |
| **WHO** | tenopa 제안서 작성자 (정확한 평가 원함), PM (품질 지표 필요), 기술 팀 (Harness 고도화) |
| **RISK** | Multi-Model Voting 비용 3배 증가 가능 (완화: 선택적 적용), Weight Tuning 과적합 위험 (완화: K-Fold CV), Latency 악화 (완화: 캐싱) |
| **SUCCESS** | ① Precision ≥95%, Recall ≥97%, F1 ≥96% ② False Negative <5%, False Positive <8% ③ Latency <21초 ④ Confidence 점수 100% 포함 ⑤ 사용자 피드백 100% 수집 |
| **SCOPE** | Harness 기존 4-step 위에 Accuracy Enhancement Layer 추가. Phase 1-2 (메트릭/검증), Phase 3-4 (알고리즘/배포). 총 ~1,200줄 신규 코드 + DB 확장 |

---

## 1. 아키텍처 개요

### 1.1 시스템 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│                  Harness Engineering (기존)                   │
│  Generator (3-variant) → Evaluator → Selector → FeedbackLoop  │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ↓ (평가 결과)
┌──────────────────────────────────────────────────────────────┐
│         Accuracy Enhancement Layer (신규 - Clean Arch)        │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 1. DiagnosisAccuracyValidator (Phase 1)                │  │
│  │    - Baseline 측정: Precision, Recall, F1-Score        │  │
│  │    - Test Dataset (50개 섹션 + Ground Truth)           │  │
│  │    - 현재 성능 기준선                                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 2. AccuracyEnhancementEngine (Phase 2)                │  │
│  │    - Confidence Thresholding                           │  │
│  │    - Multi-Model Voting (3개 온도)                    │  │
│  │    - Cross-Validation (Train/Test split)              │  │
│  │    - Latency 최적화                                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 3. WeightTuningEngine (Phase 3)                        │  │
│  │    - Grid Search (가중치 최적화)                       │  │
│  │    - Section-Specific Rules                           │  │
│  │    - Feedback Integration                             │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4. MetricsMonitoringService (Phase 4)                 │  │
│  │    - 실시간 정확도 모니터링                             │  │
│  │    - 대시보드 API                                       │  │
│  │    - 프로덕션 배포 체크리스트                           │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                     │
                     ↓ (강화된 평가 결과 + 신뢰도)
┌──────────────────────────────────────────────────────────────┐
│                  LangGraph Integration                        │
│     proposal_nodes.py → Harness + Accuracy Enhancement       │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 데이터 흐름

```
User Section Input
       │
       ↓
[Harness Generator]
  3-variant 병렬 생성 (conservative/balanced/creative)
       │
       ↓
[Harness Evaluator]
  각 variant 평가 (hallucination, persuasiveness, completeness, clarity)
       │
       ↓
[AccuracyEnhancementEngine]
  ├─ Confidence Threshold Check
  │  └─ confidence < 0.75? → Re-evaluate with Multi-Model Voting
  │
  ├─ Multi-Model Voting (낮은 신뢰도만)
  │  ├─ Model A (temperature=0.1)
  │  ├─ Model B (temperature=0.3)
  │  └─ Model C (temperature=0.7)
  │  └─ Consensus: 3개 중 2개 이상 동의
  │
  └─ Cross-Validation
     ├─ Train Set (80%): Weight Tuning
     └─ Test Set (20%): Performance Validation
       │
       ↓
[WeightTuningEngine]
  ├─ Grid Search (가중치 조합 최적화)
  ├─ Section-Specific Rules 적용
  └─ Feedback Loop: 사용자 피드백 → 모델 재학습
       │
       ↓
[MetricsMonitoringService]
  ├─ 실시간 정확도 계산 (Precision/Recall/F1)
  ├─ False Negative/Positive 추적
  ├─ Latency 모니터링
  └─ 대시보드 업데이트
       │
       ↓
Enhanced Evaluation Result (+ confidence + metrics)
```

---

## 2. 모듈 설계

### 2.1 Module 1: DiagnosisAccuracyValidator

**파일**: `app/services/harness_accuracy_validator.py` (400줄)

**책임**:
- Baseline 성능 측정
- Precision, Recall, F1-Score 계산
- Test Dataset 관리

**핵심 클래스**:
```python
class DiagnosisAccuracyValidator:
    """Harness 평가 정확도 검증 및 메트릭 계산"""
    
    def __init__(self, test_dataset_path: str):
        """
        Args:
            test_dataset_path: 50개 섹션 + Ground Truth JSON 파일
        """
        self.test_dataset = load_dataset(test_dataset_path)  # 50개 섹션
        self.metrics_history = []
    
    async def measure_baseline(self) -> AccuracyMetrics:
        """
        현재 Harness 성능 측정 (Baseline)
        
        Returns:
            AccuracyMetrics = {
                precision: float (0-1),
                recall: float (0-1),
                f1_score: float (0-1),
                false_negative_count: int,
                false_positive_count: int,
                avg_latency_seconds: float,
                timestamp: datetime
            }
        """
        results = []
        for section in self.test_dataset:
            # 1. Harness로 평가
            predicted = await self._evaluate_with_harness(section)
            
            # 2. Ground Truth와 비교
            actual = section.ground_truth
            
            # 3. 결과 기록
            results.append({
                "section_id": section.id,
                "predicted": predicted,
                "actual": actual,
                "match_type": self._classify_match(predicted, actual),
                "latency": predicted.evaluation_time_ms / 1000
            })
        
        # 4. 메트릭 계산
        metrics = self._calculate_metrics(results)
        self.metrics_history.append(metrics)
        return metrics
    
    def _calculate_metrics(self, results: List[Dict]) -> AccuracyMetrics:
        """Precision, Recall, F1-Score 계산"""
        tp = sum(1 for r in results if r["match_type"] == "true_positive")
        fp = sum(1 for r in results if r["match_type"] == "false_positive")
        fn = sum(1 for r in results if r["match_type"] == "false_negative")
        tn = sum(1 for r in results if r["match_type"] == "true_negative")
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        avg_latency = sum(r["latency"] for r in results) / len(results)
        
        return AccuracyMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            false_negative_count=fn,
            false_positive_count=fp,
            avg_latency_seconds=avg_latency,
            timestamp=datetime.now()
        )
    
    def _classify_match(self, predicted, actual) -> str:
        """TP/FP/FN/TN 분류"""
        # hallucination 메트릭 기준 (>= 0.3 = 문제 있음)
        pred_is_issue = predicted.hallucination >= 0.3
        actual_is_issue = actual.hallucination >= 0.3
        
        if pred_is_issue and actual_is_issue:
            return "true_positive"
        elif pred_is_issue and not actual_is_issue:
            return "false_positive"
        elif not pred_is_issue and actual_is_issue:
            return "false_negative"
        else:
            return "true_negative"
```

**데이터 모델**:
```python
class AccuracyMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    false_negative_count: int
    false_positive_count: int
    avg_latency_seconds: float
    timestamp: datetime
```

---

### 2.2 Module 2: AccuracyEnhancementEngine

**파일**: `app/services/harness_accuracy_enhancement.py` (350줄)

**책임**:
- Confidence Thresholding
- Multi-Model Voting
- Cross-Validation

**핵심 클래스**:
```python
class AccuracyEnhancementEngine:
    """검증 강화 엔진"""
    
    CONFIDENCE_THRESHOLD = 0.75  # 신뢰도 기준선
    
    async def enhance_evaluation(
        self, 
        section_content: str,
        harness_result: EvaluationScore
    ) -> EnhancedEvaluationResult:
        """
        Harness 평가 결과에 검증 강화 적용
        
        Args:
            section_content: 섹션 본문
            harness_result: Harness 평가 결과 (5가지 메트릭)
        
        Returns:
            EnhancedEvaluationResult = {
                original_score: EvaluationScore,
                confidence: float,
                needs_voting: bool,
                voting_result: Optional[EvaluationScore],  # Multi-Model Voting 결과
                final_score: EvaluationScore,  # 최종 점수
                enhancement_reason: str
            }
        """
        
        # 1. Confidence Thresholding
        confidence = self._calculate_confidence(harness_result)
        
        if confidence >= self.CONFIDENCE_THRESHOLD:
            # 신뢰도 높음 → 그대로 사용
            return EnhancedEvaluationResult(
                original_score=harness_result,
                confidence=confidence,
                needs_voting=False,
                final_score=harness_result,
                enhancement_reason="High confidence, no enhancement needed"
            )
        else:
            # 신뢰도 낮음 → Multi-Model Voting
            voting_result = await self._multi_model_voting(
                section_content, 
                harness_result
            )
            
            final_score = self._select_best_score(
                harness_result, 
                voting_result
            )
            
            return EnhancedEvaluationResult(
                original_score=harness_result,
                confidence=confidence,
                needs_voting=True,
                voting_result=voting_result,
                final_score=final_score,
                enhancement_reason="Low confidence, Multi-Model Voting applied"
            )
    
    def _calculate_confidence(self, result: EvaluationScore) -> float:
        """
        신뢰도 점수 계산
        
        신뢰도 = 각 메트릭 스코어의 표준편차의 역함수
        → 메트릭들이 비슷한 점수면 신뢰도 높음
        → 메트릭들이 다르면 신뢰도 낮음
        """
        scores = [
            result.hallucination,
            result.persuasiveness,
            result.completeness,
            result.clarity
        ]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # std_dev이 작을수록 신뢰도 높음
        confidence = 1 / (1 + std_dev)  # Sigmoid-like 변환
        return min(confidence, 1.0)
    
    async def _multi_model_voting(
        self, 
        section_content: str,
        original_result: EvaluationScore
    ) -> EvaluationScore:
        """
        3개 온도에서 평가 후 투표
        
        - Conservative (temp=0.1): 신중한 평가
        - Balanced (temp=0.3): 중간 평가
        - Creative (temp=0.7): 관대한 평가
        
        투표 규칙: 3개 중 2개 이상 동의하면 채택
        """
        
        # 1. 3개 모델로 병렬 평가
        evaluations = await asyncio.gather(
            self._evaluate_with_temperature(section_content, 0.1),
            self._evaluate_with_temperature(section_content, 0.3),
            self._evaluate_with_temperature(section_content, 0.7),
        )
        
        # 2. Voting (평균 스코어)
        consensus_score = EvaluationScore(
            hallucination=sum(e.hallucination for e in evaluations) / 3,
            persuasiveness=sum(e.persuasiveness for e in evaluations) / 3,
            completeness=sum(e.completeness for e in evaluations) / 3,
            clarity=sum(e.clarity for e in evaluations) / 3,
            overall=sum(e.overall for e in evaluations) / 3
        )
        
        return consensus_score
    
    async def cross_validate(
        self,
        test_dataset: List[TestSection]
    ) -> CrossValidationResult:
        """
        K-Fold Cross-Validation (K=5)
        
        Returns:
            CrossValidationResult = {
                fold_scores: List[AccuracyMetrics],  # 5개 fold 점수
                mean_f1_score: float,
                std_dev: float,
                best_fold: int,
                worst_fold: int
            }
        """
        k = 5
        fold_size = len(test_dataset) // k
        fold_scores = []
        
        for fold_idx in range(k):
            # Train/Test split
            test_start = fold_idx * fold_size
            test_end = test_start + fold_size
            
            test_fold = test_dataset[test_start:test_end]
            train_fold = test_dataset[:test_start] + test_dataset[test_end:]
            
            # Fold별 평가
            metrics = await self._evaluate_fold(train_fold, test_fold)
            fold_scores.append(metrics)
        
        # 평균 및 표준편차
        mean_f1 = sum(m.f1_score for m in fold_scores) / k
        std_dev = (sum((m.f1_score - mean_f1) ** 2 for m in fold_scores) / k) ** 0.5
        
        return CrossValidationResult(
            fold_scores=fold_scores,
            mean_f1_score=mean_f1,
            std_dev=std_dev,
            best_fold=fold_scores.index(max(fold_scores, key=lambda m: m.f1_score)),
            worst_fold=fold_scores.index(min(fold_scores, key=lambda m: m.f1_score))
        )
```

---

### 2.3 Module 3: WeightTuningEngine

**파일**: `app/services/harness_weight_tuner.py` (300줄)

**책임**:
- Grid Search로 가중치 최적화
- Section-Specific Rules
- Feedback Integration

**핵심 클래스**:
```python
class WeightTuningEngine:
    """가중치 튜닝 엔진"""
    
    # 기본 가중치
    DEFAULT_WEIGHTS = {
        "hallucination": 0.35,
        "persuasiveness": 0.25,
        "completeness": 0.25,
        "clarity": 0.15
    }
    
    # 섹션별 특화 가중치
    SECTION_SPECIFIC_WEIGHTS = {
        "executive_summary": {
            "hallucination": 0.40,  # 더 엄격
            "persuasiveness": 0.30,  # 설득력 강조
            "completeness": 0.20,
            "clarity": 0.10
        },
        "technical_details": {
            "hallucination": 0.40,  # 엄격
            "persuasiveness": 0.20,
            "completeness": 0.25,
            "clarity": 0.15
        }
    }
    
    async def grid_search_optimal_weights(
        self,
        train_dataset: List[TestSection]
    ) -> WeightConfig:
        """
        Grid Search로 최적 가중치 찾기
        
        기본 가중치를 기준으로 ±5% 범위에서 탐색
        """
        
        # 1. 가중치 후보 생성
        candidates = self._generate_weight_candidates()  # ~100개 조합
        
        # 2. 각 조합별 F1-Score 계산
        results = []
        for weights in candidates:
            f1_score = await self._evaluate_weights(weights, train_dataset)
            results.append({
                "weights": weights,
                "f1_score": f1_score
            })
        
        # 3. 최적 가중치 선택
        best = max(results, key=lambda r: r["f1_score"])
        
        return WeightConfig(
            hallucination=best["weights"]["hallucination"],
            persuasiveness=best["weights"]["persuasiveness"],
            completeness=best["weights"]["completeness"],
            clarity=best["weights"]["clarity"],
            f1_score=best["f1_score"]
        )
    
    def _generate_weight_candidates(self) -> List[Dict]:
        """기본 가중치 ±5% 범위에서 조합 생성"""
        base = self.DEFAULT_WEIGHTS
        candidates = []
        
        adjustments = [-0.05, -0.025, 0, 0.025, 0.05]
        
        for hal_adj in adjustments:
            for per_adj in adjustments:
                for com_adj in adjustments:
                    for cla_adj in adjustments:
                        weights = {
                            "hallucination": base["hallucination"] + hal_adj,
                            "persuasiveness": base["persuasiveness"] + per_adj,
                            "completeness": base["completeness"] + com_adj,
                            "clarity": base["clarity"] + cla_adj
                        }
                        
                        # 합이 1.0이 되도록 정규화
                        total = sum(weights.values())
                        weights = {k: v/total for k, v in weights.items()}
                        
                        candidates.append(weights)
        
        return candidates[:100]  # 상위 100개
    
    async def integrate_user_feedback(
        self,
        feedback_list: List[EvaluationFeedback],
        current_weights: WeightConfig
    ) -> WeightConfig:
        """
        사용자 피드백을 기반으로 가중치 조정
        
        피드백 = {
            evaluation_id: "...",
            user_decision: "approved" | "rejected",
            reason: "...",
            corrected_scores: {hallucination: 0.1, ...}
        }
        """
        
        if len(feedback_list) < 50:
            return current_weights  # 피드백 충분하지 않으면 유지
        
        # 1. 피드백 분석
        false_positives = [f for f in feedback_list if f.user_decision == "rejected"]
        false_negatives = [f for f in feedback_list if f.user_decision == "approved"]
        
        # 2. 문제 메트릭 식별
        issue_metrics = self._identify_issue_metrics(
            false_positives, 
            false_negatives
        )
        
        # 3. 가중치 조정
        adjusted_weights = current_weights.copy()
        
        for metric, impact in issue_metrics.items():
            if impact < 0:  # 과도하게 높음 (FP)
                adjusted_weights[metric] *= 0.95  # 5% 감소
            else:  # 낮음 (FN)
                adjusted_weights[metric] *= 1.05  # 5% 증가
        
        # 4. 정규화
        total = sum(adjusted_weights.values())
        adjusted_weights = {k: v/total for k, v in adjusted_weights.items()}
        
        return adjusted_weights
    
    def apply_section_specific_rules(
        self,
        section_type: str,
        general_weights: WeightConfig
    ) -> WeightConfig:
        """섹션별 특화 가중치 적용"""
        if section_type in self.SECTION_SPECIFIC_WEIGHTS:
            return self.SECTION_SPECIFIC_WEIGHTS[section_type]
        return general_weights
```

---

### 2.4 Module 4: MetricsMonitoringService

**파일**: `app/api/routes_metrics.py` (150줄)

**책임**:
- 정확도 메트릭 API
- 대시보드 조회
- 프로덕션 배포 준비

**API Endpoints**:
```python
@app.get("/api/metrics/harness-accuracy")
async def get_harness_accuracy_metrics():
    """
    현재 정확도 메트릭 조회
    
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
                "high": 0.85,
                "medium": 0.10,
                "low": 0.05
            }
        },
        "trend": {
            "precision_7d": [0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.97],
            "recall_7d": [0.92, 0.93, 0.94, 0.96, 0.97, 0.97, 0.97]
        },
        "success_criteria_status": {
            "sc_1": {criterion: "F1 ≥ 0.96", actual: 0.97, status: "✅ PASS"},
            "sc_2": {criterion: "FN < 5%", actual: 3.2, status: "✅ PASS"},
            "sc_3": {criterion: "FP < 8%", actual: 5.1, status: "✅ PASS"},
            "sc_4": {criterion: "Latency < 21s", actual: 21.5, status: "⚠️ CLOSE"},
            "sc_5": {criterion: "Confidence 100%", actual: 100, status: "✅ PASS"},
            "sc_6": {criterion: "Feedback 100%", actual: 100, status: "✅ PASS"},
            "sc_7": {criterion: "Coverage ≥ 90%", actual: 92, status: "✅ PASS"}
        }
    }
    """

@app.post("/api/artifacts/evaluate-feedback")
async def save_evaluation_feedback(feedback: EvaluationFeedback):
    """
    사용자 평가 피드백 저장
    
    Request:
    {
        "evaluation_id": "eval-123",
        "user_decision": "approved" | "rejected",
        "reason": "이 부분은 너무 과하게 지적되었습니다",
        "corrected_scores": {
            "hallucination": 0.1,
            "persuasiveness": 0.8,
            "completeness": 0.9,
            "clarity": 0.85
        },
        "section_type": "executive_summary"
    }
    
    Response:
    {
        "status": "saved",
        "feedback_id": "fb-456",
        "learning_status": {
            "total_feedback_collected": 245,
            "feedback_needed_for_retraining": 250,
            "days_until_retraining": 3
        }
    }
    """

@app.get("/api/metrics/harness-accuracy-trend")
async def get_accuracy_trend(days: int = 7):
    """7일 또는 30일 정확도 추이 조회"""

@app.get("/api/metrics/deployment-readiness")
async def check_deployment_readiness():
    """
    배포 준비 상태 점검
    
    Response:
    {
        "ready": true,
        "checklist": [
            {item: "F1-Score ≥ 96%", status: "✅", deadline: "2026-04-25"},
            {item: "False Negative < 5%", status: "✅", deadline: "2026-04-25"},
            {item: "E2E Test 통과", status: "✅", deadline: "2026-04-25"},
            {item: "Code Coverage ≥ 90%", status: "✅", deadline: "2026-04-25"}
        ]
    }
    """
```

---

## 3. 데이터 모델

### 3.1 신규 DB 스키마

```sql
-- 1. evaluation_feedback 테이블
CREATE TABLE evaluation_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    user_decision VARCHAR(20) NOT NULL,  -- 'approved' | 'rejected'
    reason TEXT,
    corrected_hallucination DECIMAL(3,2),
    corrected_persuasiveness DECIMAL(3,2),
    corrected_completeness DECIMAL(3,2),
    corrected_clarity DECIMAL(3,2),
    section_type VARCHAR(50),  -- 'executive_summary', 'technical_details', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_section_type (section_type)
);

-- 2. harness_metrics_log 테이블
CREATE TABLE harness_metrics_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id VARCHAR(255),
    precision DECIMAL(4,3),
    recall DECIMAL(4,3),
    f1_score DECIMAL(4,3),
    false_negative_count INT,
    false_positive_count INT,
    avg_latency_ms INT,
    confidence_score DECIMAL(4,3),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp)
);

-- 3. weight_configs 테이블
CREATE TABLE weight_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100),  -- 'default', 'optimized_v1', etc.
    hallucination_weight DECIMAL(4,3),
    persuasiveness_weight DECIMAL(4,3),
    completeness_weight DECIMAL(4,3),
    clarity_weight DECIMAL(4,3),
    section_type VARCHAR(50),  -- NULL = default, 'executive_summary' = specific
    f1_score DECIMAL(4,3),  -- 이 가중치의 성능
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);
```

### 3.2 Pydantic 모델

```python
class AccuracyMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    false_negative_count: int
    false_positive_count: int
    avg_latency_seconds: float
    timestamp: datetime

class EvaluationFeedback(BaseModel):
    evaluation_id: str
    user_decision: Literal["approved", "rejected"]
    reason: Optional[str] = None
    corrected_hallucination: Optional[float] = None
    corrected_persuasiveness: Optional[float] = None
    corrected_completeness: Optional[float] = None
    corrected_clarity: Optional[float] = None
    section_type: str

class WeightConfig(BaseModel):
    hallucination_weight: float
    persuasiveness_weight: float
    completeness_weight: float
    clarity_weight: float
    section_type: Optional[str] = None
    f1_score: Optional[float] = None

class EnhancedEvaluationResult(BaseModel):
    original_score: Dict[str, float]
    confidence: float
    needs_voting: bool
    voting_result: Optional[Dict[str, float]] = None
    final_score: Dict[str, float]
    enhancement_reason: str

class CrossValidationResult(BaseModel):
    fold_scores: List[AccuracyMetrics]
    mean_f1_score: float
    std_dev: float
    best_fold: int
    worst_fold: int
```

---

## 4. 알고리즘 의사코드

### 4.1 Confidence Calculation

```
함수: calculate_confidence(evaluation_result)
입력: EvaluationScore {hallucination, persuasiveness, completeness, clarity}
출력: confidence ∈ [0, 1]

알고리즘:
1. scores = [hallucination, persuasiveness, completeness, clarity]
2. mean = sum(scores) / 4
3. variance = sum((score - mean)^2) / 4
4. std_dev = sqrt(variance)
5. confidence = 1 / (1 + std_dev)  // Sigmoid-like
6. return min(confidence, 1.0)

직관: 메트릭들이 비슷한 점수 → std_dev 작음 → confidence 높음
     메트릭들이 다른 점수 → std_dev 큼 → confidence 낮음
```

### 4.2 Multi-Model Voting

```
함수: multi_model_voting(section_content)
입력: 섹션 본문
출력: consensus_score (3개 평가의 평균)

알고리즘:
1. 병렬 평가 (asyncio.gather)
   - evaluate_with_temperature(content, 0.1)  // Conservative
   - evaluate_with_temperature(content, 0.3)  // Balanced
   - evaluate_with_temperature(content, 0.7)  // Creative

2. 평균 계산
   consensus.hallucination = (eval1.hal + eval2.hal + eval3.hal) / 3
   consensus.persuasiveness = (eval1.per + eval2.per + eval3.per) / 3
   ... (completeness, clarity도 동일)

3. 최종 점수
   consensus.overall = weighted_average(hal, per, com, cla, weights)

직관: 온도(temperature)를 변경하면 다양한 관점의 평가 가능
     이 3개를 투표하면 더 안정적인 결과 얻음
```

### 4.3 Grid Search Weight Optimization

```
함수: grid_search_optimal_weights(train_dataset)
입력: 트레이닝 데이터 (섹션 + Ground Truth)
출력: 최적 가중치

알고리즘:
1. 후보 생성 (각 가중치 ±5% 범위)
   기본: {hal: 0.35, per: 0.25, com: 0.25, cla: 0.15}
   
   for hal in [0.30, 0.325, 0.35, 0.375, 0.40]:
     for per in [0.20, 0.225, 0.25, 0.275, 0.30]:
       ...
   → ~100개 조합 생성

2. 각 조합별 F1-Score 계산
   for weights in candidates:
     f1 = evaluate_weights(weights, train_dataset)
     results.append({weights, f1})

3. 최적 선택
   best = max(results, key=lambda r: r.f1)
   return best.weights

직관: 데이터 기반으로 각 메트릭의 중요도 찾기
     hallucination이 더 중요하면 가중치 증가
     persuasiveness 과도하면 가중치 감소
```

---

## 5. 구현 가이드

### 5.1 Phase별 구현 순서

**Phase 1: Metrics Definition (Day 1-2)**
1. `harness_accuracy_validator.py` 구현
   - `DiagnosisAccuracyValidator` 클래스
   - `measure_baseline()` 메서드
   - Precision/Recall/F1 계산
   
2. Test Dataset 구성
   - `data/test_datasets/harness_test_50_sections.json` 생성
   - 50개 섹션 + Ground Truth 라벨링
   - Baseline 측정 실행
   
3. Unit Tests
   - `test_harness_accuracy_validator.py` (15개 테스트)

**Phase 2: Validation Enhancement (Day 3-4)**
1. `harness_accuracy_enhancement.py` 구현
   - `AccuracyEnhancementEngine` 클래스
   - Confidence Thresholding
   - Multi-Model Voting
   - Cross-Validation
   
2. Latency 최적화
   - Profiling: `cProfile` 사용
   - Bottleneck 식별
   - 캐싱, 비동기 처리 적용
   
3. Unit & Integration Tests
   - `test_harness_accuracy_enhancement.py` (20개 테스트)

**Phase 3: Algorithm Improvement (Day 5-7)**
1. `harness_weight_tuner.py` 구현
   - `WeightTuningEngine` 클래스
   - Grid Search
   - Section-Specific Rules
   - Feedback Integration
   
2. DB 확장
   - Supabase 테이블 생성 (3개)
   - Migration script 작성
   
3. Unit & Integration Tests
   - `test_harness_weight_tuner.py` (15개 테스트)

**Phase 4: Monitoring & Deployment (Day 8)**
1. `routes_metrics.py` 구현
   - 4개 API 엔드포인트
   - 메트릭 조회, 피드백 저장, 배포 준비 확인
   
2. E2E Tests
   - `tests/e2e_harness_accuracy_e2e.py` (12개 테스트)
   - 전체 워크플로우 검증
   
3. 배포 체크리스트
   - 모든 Success Criteria 확인
   - 성능 벤치마크
   - 프로덕션 배포

### 5.2 Session Guide (Multi-Session 구현)

```
╔════════════════════════════════════════════════╗
║  STEP 4A Diagnosis Accuracy Improvement        ║
║  Session Guide (Option B: Clean Architecture)  ║
╚════════════════════════════════════════════════╝

Session 1: Metrics Definition & Baseline
  📌 목표: Baseline 성능 측정 및 메트릭 정의
  ⏱️  시간: ~4시간
  📁 산출물:
     - harness_accuracy_validator.py (400줄)
     - test_dataset.json (50개 섹션)
     - baseline_metrics.json (측정 결과)
  ✅ 완료 조건:
     - Baseline Precision/Recall/F1 측정 완료
     - Test Dataset 50개 섹션 준비
     - Unit Tests 10/15 통과

─────────────────────────────────────────────────

Session 2: Validation Enhancement
  📌 목표: Confidence Thresholding, Voting, CV 구현
  ⏱️  시간: ~4시간
  📁 산출물:
     - harness_accuracy_enhancement.py (350줄)
     - latency_profile.json (Profiling 결과)
  ✅ 완료 조건:
     - Multi-Model Voting 구현 완료
     - Cross-Validation 5-Fold 완료
     - Latency 20% 개선 달성
     - Integration Tests 8/8 통과

─────────────────────────────────────────────────

Session 3: Algorithm Improvement & Feedback Loop
  📌 목표: Weight Tuning, Section Rules, Feedback 통합
  ⏱️  시간: ~5시간
  📁 산출물:
     - harness_weight_tuner.py (300줄)
     - weight_optimization_report.json (Grid Search 결과)
     - DB 마이그레이션 스크립트
  ✅ 완료 조건:
     - Grid Search 최적 가중치 찾기 완료
     - Section-Specific Rules 적용 완료
     - evaluation_feedback 테이블 생성
     - Unit Tests 12/15 통과

─────────────────────────────────────────────────

Session 4: Monitoring API & E2E Testing
  📌 목표: 메트릭 대시보드 API, E2E 테스트, 배포 준비
  ⏱️  시간: ~3시간
  📁 산출물:
     - routes_metrics.py (150줄)
     - E2E 테스트 (12개 케이스)
     - deployment_checklist.md
  ✅ 완료 조건:
     - 4개 API 엔드포인트 완성
     - E2E Tests 12/12 통과
     - 모든 Success Criteria 달성 (SC-1~7)
     - Code Coverage ≥90%
```

---

## 6. 테스트 전략

### 6.1 단위 테스트 (45개)

**DiagnosisAccuracyValidator** (15개):
- test_baseline_measurement (5)
- test_precision_recall_calculation (5)
- test_false_positive_negative_counting (5)

**AccuracyEnhancementEngine** (20개):
- test_confidence_calculation (5)
- test_multi_model_voting (8)
- test_cross_validation (7)

**WeightTuningEngine** (10개):
- test_grid_search (5)
- test_section_specific_rules (5)

### 6.2 통합 테스트 (8개)
- test_enhancement_workflow (3)
- test_feedback_integration (2)
- test_end_to_end_pipeline (3)

### 6.3 수용 테스트 (3개)
- test_acceptance_f1_score (F1 ≥ 96%)
- test_acceptance_false_rates (FN <5%, FP <8%)
- test_acceptance_latency (Latency <21s)

---

## 7. 리스크 관리

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|---------|
| Ground Truth 라벨링 오류 | 중간 | 높음 | 인간 검토 2회, 합의 프로세스 |
| Weight Tuning 과적합 | 중간 | 중간 | 5-Fold Cross-Validation |
| Multi-Model Voting 비용 | 중간 | 중간 | 선택적 적용 (confidence <0.75만) |
| Latency 악화 | 낮음 | 중간 | 캐싱, 비동기 처리 |
| Feedback 데이터 부족 | 낮음 | 낮음 | 초기 수동 피드백 수집 |

---

## 8. 성공 메트릭

| 메트릭 | 목표 | 측정 시점 |
|--------|------|---------|
| F1-Score | ≥0.96 | Phase 1 완료 후 |
| Precision | ≥0.95 | Phase 1 완료 후 |
| Recall | ≥0.97 | Phase 1 완료 후 |
| False Negative Rate | <5% | Phase 2 완료 후 |
| False Positive Rate | <8% | Phase 2 완료 후 |
| Latency | <21초 | Phase 2 완료 후 |
| Confidence 필드 | 100% | Phase 3 완료 후 |
| Feedback 수집 | 100% | Phase 4 배포 시 |
| Code Coverage | ≥90% | Phase 4 완료 후 |
| E2E Tests Pass | 100% | Phase 4 완료 후 |

---

**Design Document Version**: v1.0  
**Architecture**: Option B - Clean Architecture  
**Status**: Ready for Implementation  
**Next Phase**: Do (Phase 1: Metrics Definition)
