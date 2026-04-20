# 주간 피드백 분석 및 리뷰 가이드 (Feedback Review Guide)

**작성일**: 2026-04-18  
**페이즈**: STEP 4A Gap 3 (피드백 자동화 - Phase 1: 수동 프로세스)  
**상태**: ✅ 운영 중

---

## 개요

이 가이드는 제안서 워크플로 실행에 따른 사용자 피드백을 수집하고, 주간 분석을 통해 모델의 가중치를 조정하는 프로세스를 정의합니다.
사용자의 승인/재작업 피드백 → 주간 팀 리뷰 → 가중치 의사결정 → 검증 후 배포의 사이클을 운영합니다.

### Process Flow

```
User Reviews Proposal Section
        ↓
Provides Feedback (APPROVE/REJECT)
        ↓
Feedback Stored in Database
        ↓
Weekly Team Review Meeting
        ↓
Analyze Patterns & Metrics
        ↓
Recommend Weight Adjustments
        ↓
Test New Weights
        ↓
Deploy If Validation Passes
```

---

## 주간 피드백 리뷰 회의

**일정**: 매주 목요일 (2026-04-19, 2026-04-26, ...)  
**시간**: 14:00-14:45 KST  
**참석자**: AI 엔지니어링팀, PM, QA 담당자  
**위치**: Zoom / 회의실 A

### 회의 안건

1. **피드백 요약** (5분)
   - 이번 주 수집된 총 피드백 수
   - 섹션별 승인/재작업 비율
   - 승인률이 낮은 섹션 식별

2. **분석 단계** (15분)
   - 재작업 요청 섹션 검토
   - 공통 패턴 식별
   - 이슈 분류:
     * 정확도 이슈 (부정확한 사실)
     * 스타일 이슈 (포맷, 톤)
     * 완성도 이슈 (내용 누락)
     * 명확성 이슈 (이해하기 어려움)

3. **의사결정 단계** (15분)
   - 가중치 조정 권장사항
   - 영향받을 섹션 유형
   - 예상 효과

4. **검증 및 배포** (10분)
   - 샘플 데이터셋에서 새 가중치 테스트
   - 성공 기준 검증
   - 배포 일정 결정

---

## Step 1: 데이터 수집 (매주 목요일 09:00)

```bash
# 명령어: 지난 7일 피드백 수집
python -m app.services.feedback_analyzer --week --format=json --output=reports/week_16.json
```

**수집 항목:**
```json
{
  "period": "2026-04-14 ~ 2026-04-20",
  "total_proposals": 12,
  "feedback_count": 45,
  "approval_rate": 0.82,
  "rework_rate": 0.15,
  "skip_rate": 0.03
}
```

## Step 2: 섹션별 성능 분석 (09:30)

```bash
python -m app.services.feedback_analyzer --by-section --format=csv
```

| 섹션명 | 피드백 수 | 승인률 | 재작업률 | 평균 감정도 |
|--------|----------|--------|---------|-----------|
| Executive Summary | 15 | 93% | 7% | 0.89 |
| Technical Approach | 12 | 75% | 25% | 0.71 |
| Project Schedule | 10 | 80% | 20% | 0.75 |
| Risk Management | 8 | 88% | 12% | 0.82 |

**분석 기준:**
- **높은 승인률 (>85%)**: 양호 섹션, 모니터링만
- **중간 승인률 (70-85%)**: 개선 필요, 재작업 사유 분석
- **낮은 승인률 (<70%)**: 긴급 대응, 프롬프트 재작성

## Step 3: 재작업 사유 분석 (10:00)

```bash
python -m app.services.feedback_analyzer --rework-reasons --format=json
```

| 사유 | 빈도 | 비율 | 대응 방안 |
|------|------|------|---------|
| 내용 부족 | 4회 | 33% | 최소 단어 수 지정 |
| 표현 불명확 | 2회 | 17% | 예시 추가 |
| 기술적 오류 | 1회 | 8% | 검증 로직 추가 |
| 필수 요소 누락 | 2회 | 17% | 체크리스트 명시 |
| 기타 | 2회 | 17% | 사례 별도 분석 |

## Step 4: 감정 분석 (Sentiment Analysis)

```bash
python -m app.services.feedback_analyzer --sentiment --format=json
```

| 감정 | 수 | 비율 | 해석 |
|------|-----|------|------|
| 긍정 | 32 | 71% | 만족 |
| 중립 | 10 | 22% | 보통 |
| 부정 | 3 | 7% | 불만 |

**감정 임계값:**
- **긍정 > 70%**: 정상
- **중립 20-30%**: 주의, 개선 검토
- **부정 > 10%**: 경고, 즉시 개선

---

## 주간 리뷰 미팅 체크리스트

**회의 시작 전 준비 (10분):**

- [ ] 피드백 데이터 수집 완료
- [ ] 대시보드 미리보기 (slack에 공유)
- [ ] 지난주 의사결정 사항 검토
- [ ] 회의실/Zoom 준비

**회의 중 분석 양식:**

**섹션명**: [executive_summary / technical_approach / project_schedule / risk_management]

**이번 주 피드백**: [X건 승인, Y건 재작업]

**승인률**: X / (X+Y) = ___%

**재작업 사유별:**
- [ ] 부정확한 사실 (\_\_\_%)
- [ ] 스타일/포맷 (\_\_\_%)
- [ ] 불완전한 내용 (\_\_\_%)
- [ ] 명확성 문제 (\_\_\_%)
- [ ] 기타 (\_\_\_%)

**주요 이슈:**
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

**권장 가중치 조정:**

| 항목 | 현재 | 권장 | 사유 |
|------|------|------|------|
| Sonnet 가중치 | 0.X | 0.X | 성능 ___ |
| Haiku 가중치 | 0.X | 0.X | 성능 ___ |
| 규칙 기반 가중치 | 0.X | 0.X | 성능 ___ |
| 사용자 선호도 | 0.X | 0.X | 성능 ___ |

**예상 효과**: F1-Score ±__%

---

## 승인률 기준 및 해석

### 목표 승인률

| 환경 | 목표 | 경고 | 심각 |
|------|------|------|------|
| Staging | 85-95% | < 80% | < 70% |
| Production | 80-90% | < 75% | < 60% |

### 섹션별 기대 승인률

| 섹션 | 난도 | 목표 | 해석 |
|------|------|------|------|
| Executive Summary | 낮음 | > 90% | 높은 수준의 임팩트 표현 |
| Technical Approach | 높음 | > 75% | 기술 깊이 표현 어려움 |
| Project Schedule | 중간 | > 85% | 일정 합리성 중요 |
| Risk Management | 중간 | > 80% | 리스크 식별 및 대응 전략 |
| Cost & Pricing | 높음 | > 70% | 가격 정당성 설명 어려움 |

---

## Database Structure for Feedback

### feedback_entry Table

```sql
CREATE TABLE feedback_entries (
    id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL,
    section_id TEXT NOT NULL,
    section_type TEXT NOT NULL,  -- executive_summary, technical_details, etc.
    user_decision TEXT NOT NULL,  -- APPROVE, REJECT
    reason TEXT,                  -- User explanation
    rating_hallucination INT,     -- 1-5 (1=high hallucination, 5=factual)
    rating_persuasiveness INT,    -- 1-5
    rating_completeness INT,      -- 1-5
    rating_clarity INT,           -- 1-5
    created_at TIMESTAMP,
    reviewed_at TIMESTAMP NULL,
    weight_version INT            -- Which weight version created this section
);
```

### Sample Query for Weekly Review

```python
# Get this week's feedback summary
SELECT 
    section_type,
    COUNT(*) as total_feedback,
    SUM(CASE WHEN user_decision='APPROVE' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN user_decision='REJECT' THEN 1 ELSE 0 END) as rejected,
    AVG(rating_hallucination) as avg_hallucination,
    AVG(rating_persuasiveness) as avg_persuasiveness,
    AVG(rating_completeness) as avg_completeness,
    AVG(rating_clarity) as avg_clarity
FROM feedback_entries
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
  AND reviewed_at IS NULL  -- Not yet analyzed
GROUP BY section_type
ORDER BY total_feedback DESC;
```

---

## Weight Adjustment Decision Criteria

### When to Adjust Weights

**Increase Hallucination Filter** (lower weight tolerance):
- Rejection rate > 30% for factual issues
- Multiple feedback entries mentioning "wrong facts"
- F1-Score degradation in test evaluation

**Increase Persuasiveness Weight**:
- Rejection rate for "weak argument" feedback
- Customer feedback indicating weak positioning
- Low engagement in proposal content

**Increase Completeness Weight**:
- Rejection for "missing sections" or "incomplete"
- Feedback indicating insufficient detail
- Compliance matrix gaps

**Increase Clarity Weight**:
- Rejection for "confusing" or "hard to understand"
- Grammar/style issues
- Structure/flow problems

### Success Criteria for New Weights

- [ ] F1-Score >= 0.96
- [ ] False Negative < 5%
- [ ] False Positive < 8%
- [ ] Latency < 21s (unchanged)
- [ ] Sample test passes (10 random sections)

---

## Monthly Performance Report

Generate monthly report to track improvement over time.

### Report Contents

1. **Feedback Metrics**
   - Total feedback collected
   - Approval rate trend
   - Feedback per section type

2. **Weight History**
   - Weight versions deployed
   - Effectiveness of each version
   - Improvement/degradation

3. **Quality Metrics**
   - F1-Score trend
   - False rate trends
   - Latency trends

4. **Recommendations for Next Month**
   - Sections needing attention
   - Potential optimizations
   - Phase 2 automation readiness

---

## 가중치 조정 의사결정 프로세스

### LangGraph 앙상블 가중치 구조

```python
# app/graph/nodes/proposal_nodes.py

weights = {
    "model_sonnet": 0.50,           # Claude Sonnet (기본)
    "model_haiku": 0.20,            # Claude Haiku (가벼운 평가)
    "rule_based": 0.15,             # 규칙 기반 평가
    "user_history": 0.15            # 사용자 선호도 학습
}

# 최종 점수 = Σ(모델_점수 × 가중치)
final_score = sonnet_score * 0.50 + haiku_score * 0.20 + rule_score * 0.15 + user_score * 0.15
```

### 가중치 조정 트리거

```python
# 주간 리뷰에서 다음 조건 발생 시 가중치 재조정:

if approval_rate < 0.75 or section_approval_rate < 0.65:
    trigger_weight_review()
    run_ab_test(old_weights, new_weights, sample_size=100)
    if new_weights.approval_rate > old_weights.approval_rate + 0.05:
        deploy_weights(new_weights)
```

### 가중치 조정 제한사항

**조정 규칙:**
- 주 최대 1회만 조정 (과도한 진동 방지)
- 한 모델의 가중치 변화: 최대 ±15%
- 모든 가중치 합계: 반드시 1.0 유지
- 조정 전후 A/B 테스트 필수 (100 샘플 최소)

---

## 가중치 조정 실행 예시

**상황**: Technical Approach 섹션 승인률 75% → 60% 급락

```python
# Step 1: 현재 가중치 분석
# sonnet_score=0.85, haiku_score=0.60, rule_score=0.75
# 현재 최종_점수 = 0.85*0.50 + 0.60*0.20 + 0.75*0.15 + 0.70*0.15 = 0.72 (낮음)

# Step 2: Sonnet 가중치 증가 (0.50 → 0.60)
# Haiku 가중치 감소 (0.20 → 0.10)
# 새 점수 = 0.85*0.60 + 0.60*0.10 + 0.75*0.15 + 0.70*0.15 = 0.76 (개선)

# Step 3: Staging에서 10개 샘플로 검증
# 개선된 가중치 테스트 → 승인률 76% 확인

# Step 4: Production 배포
new_weights = {
    "model_sonnet": 0.60,       # 증가
    "model_haiku": 0.10,        # 감소
    "rule_based": 0.15,         # 유지
    "user_history": 0.15        # 유지
}
```

---

## Phase 2: 자동화된 재학습 (2026년 5월 예정)

자동화 준비 완료 시 (추정: 2026년 5월):

1. **일일 배치 작업** (매일 23:00 KST)
   - 지난 24시간 피드백 수집
   - 가중치 튜닝 그리드 검색 실행
   - 테스트 데이터셋에서 검증

2. **자동 배포**
   - 메트릭 개선 + 기준 충족 시
   - 버전 기록 생성
   - 새 가중치 배포
   - Slack 알림 발송

3. **모니터링**
   - 프로덕션 정확도 추적
   - 성능 저하 시 알림
   - 필요 시 자동 롤백

---

## 월간 종합 분석 (매월 첫 주 금요일)

```bash
# 월간 리포트 생성
python -m app.services.feedback_analyzer --monthly-report \
  --month=2026-04 \
  --output-dir=reports/ \
  --include-trends=true
```

**출력 항목:**
- 4주 동향 분석
- 개선 추이 그래프
- 모델 성능 비교
- 다음 월 개선 제안

---

## 보고서 공유

### 주간 리포트 생성 (매주 목요일 11:00)

**배포 대상:**

1. **Slack**: #proposal-feedback 채널
   - HTML 버전 (대시보드용 스크린샷)
   - 핵심 지표만 메시지로 요약

2. **이메일**: ops@tenopa.co.kr
   - CSV 파일 첨부 (상세 데이터)
   - 개선 제안 및 액션 아이템 포함

3. **Confluence**: Operations > Weekly Reports
   - 역사 관리 및 트렌드 추적

### 보고서 샘플

```
Subject: [Weekly Report] TenopA Feedback Analysis (Week 16, 2026-04-14~20)

안녕하세요,

이번 주 제안서 피드백 분석 결과를 공유드립니다.

📊 핵심 지표:
- 전체 승인률: 82% ↑ (+3pp vs 전주)
- 평균 감정 점수: 0.78 (만족도 양호)
- Technical Approach 승인률: 75% ⚠️ (목표 85%)

📋 이번 주 조치:
[ ] Technical Approach 섹션 프롬프트 재작성
[ ] Staging에서 A/B 테스트 (10개 샘플)
[ ] 목요일 회의에서 가중치 조정 논의

📎 첨부: week_16_report.csv

더 자세한 내용은 첨부 파일을 참고해주세요.

---
TenopA Operations Team
```

---

## Feedback Collection API 빠른 참조

### 사용자 피드백 제공

```python
POST /api/proposal/{proposal_id}/feedback
{
    "section_id": "executive_summary",
    "decision": "REJECT",
    "reason": "회사 규모에 대한 부정확한 정보",
    "ratings": {
        "hallucination": 2,      # 1=환각, 5=정확
        "persuasiveness": 4,
        "completeness": 4,
        "clarity": 5
    }
}
```

### 팀 주간 분석

```python
GET /api/metrics/feedback/weekly-summary
# 이번 주 집계된 피드백 반환

GET /api/metrics/feedback/by-section-type
# 섹션별로 그룹화된 피드백 반환
```

### 가중치 조정 구현

```python
POST /api/weights/update
{
    "section_type": "technical_approach",
    "weights": {
        "model_sonnet": 0.60,
        "model_haiku": 0.10,
        "rule_based": 0.15,
        "user_history": 0.15
    },
    "notes": "2026-04-18 주 피드백 분석 기반"
}
```

---

---

## 트러블슈팅

### 낮은 피드백 수집률
- **문제**: 사용자가 피드백을 제공하지 않음
- **해결**: 피드백 UI 강화, 알림 발송, 인센티브 제공

### 불일치한 피드백
- **문제**: 같은 섹션이 승인과 재작업을 모두 받음
- **해결**: 문맥 제공, 피드백 UI 설명 개선

### 가중치 개선 실패
- **문제**: 가중치 조정이 F1-Score 개선 못함
- **해결**: 피드백 품질 확인, 샘플 크기 검토, 다른 요인 분석

### 성능 저하
- **문제**: 새 가중치가 F1-Score 하락시킴
- **해결**: 이전 버전으로 롤백, 이슈 분석, 재시도

---

## 담당자

| 역할 | 담당자 | 연락처 | 담당 항목 |
|------|--------|---------|----------|
| 피드백 분석 담당 | (지정 예정) | Slack: #ops | 주간 리포트 생성 |
| PM | (지정 예정) | Slack: #proposal | 가중치 의사결정 |
| 개발 팀장 | (지정 예정) | Slack: #backend | 프롬프트 개선 |
| AI 엔지니어링팀 | (지정 예정) | Slack: #ai | 모델 평가 |

---

## 관련 문서

- `deployment-guide.md` - 배포 프로세스
- `monitoring-guide.md` - 모니터링 및 알림
- `rollback-recovery-guide.md` - 장애 대응 및 복구

---

## 문서 버전

- **버전**: 1.0
- **마지막 업데이트**: 2026-04-18
- **다음 검토**: 2026-05-18
