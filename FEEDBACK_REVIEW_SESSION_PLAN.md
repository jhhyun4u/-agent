# 주간 피드백 리뷰 세션 계획

**첫 세션:** 2026-04-26 (금요일)  
**정기 일정:** 매주 금요일 14:00 KST  
**예상 소요시간:** 45분  
**참석자:** AI Engineering, Product, QA Teams

---

## 세션 1: 2026-04-26 (14:00 ~ 14:45 KST)

### 사전 준비 (2026-04-23 ~ 2026-04-25)

#### 1. 피드백 수집 완료 여부 확인
```bash
# Database에서 이번 주 피드백 조회
SELECT 
    section_type,
    COUNT(*) as total,
    SUM(CASE WHEN user_decision='APPROVE' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN user_decision='REJECT' THEN 1 ELSE 0 END) as rejected,
    AVG(rating_hallucination) as avg_hallucination,
    AVG(rating_persuasiveness) as avg_persuasiveness,
    AVG(rating_completeness) as avg_completeness,
    AVG(rating_clarity) as avg_clarity
FROM feedback_entries
WHERE created_at >= '2026-04-19'::date
GROUP BY section_type
ORDER BY total DESC;
```

- [ ] 피드백 데이터 추출
- [ ] 분석 도구 실행 (FeedbackAnalyzer)
- [ ] 주간 분석 리포트 생성

#### 2. 분석 리포트 준비
```bash
python << 'SCRIPT'
from app.services.feedback_analyzer import FeedbackAnalyzer
import json

# Database에서 피드백 로드
feedback_data = [...]  # DB 쿼리 결과

# 분석 실행
analyzer = FeedbackAnalyzer()
analysis = analyzer.analyze_weekly_feedback(feedback_data)
report_text = analyzer.get_feedback_analysis_report(feedback_data)

# 리포트 저장
with open('/tmp/feedback_analysis_2026-04-26.txt', 'w') as f:
    f.write(report_text)

# JSON 저장 (추가 분석용)
with open('/tmp/feedback_analysis_2026-04-26.json', 'w') as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)

print("분석 완료")
SCRIPT
```

- [ ] FeedbackAnalyzer 실행
- [ ] 텍스트 리포트 생성
- [ ] JSON 분석 결과 저장

#### 3. 프레젠테이션 자료 준비
- [ ] 피드백 요약 슬라이드 (총 개수, 승인률)
- [ ] 섹션별 분석 그래프
- [ ] 가중치 조정 권장사항
- [ ] 영향도 분석

---

## 세션 진행 절차

### 1단계: 개회 (14:00 ~ 14:05, 5분)

**진행자:** PM Lead

- 세션 목표 설명
- 참석자 소개
- 제약 사항 및 결정권자 확인

**안건:**
- 정기 세션 시간 확정 (매주 금요일 14:00)
- 피드백 리뷰 프로세스 설명

---

### 2단계: 피드백 요약 (14:05 ~ 14:10, 5분)

**발표자:** Data Analyst (or PM)

**내용:**
- 총 피드백 수: __개
- 승인 건: __개 (__%)
- 거절 건: __개 (__%)
- 주요 섹션: ________
- 주목할 패턴: ________

**Q&A:** (2분)

---

### 3단계: 섹션별 분석 (14:10 ~ 14:25, 15분)

**발표자:** QA/AI Engineering

**분석 대상:**
1. **Executive Summary**
   - 총 피드백: __개
   - 승인률: __%
   - 평균 점수 (1-5 스케일):
     * 할루시네이션: 3.2 (낮음 ⚠️)
     * 설득력: 4.1 (양호)
     * 완성도: 3.8 (보통)
     * 명확성: 4.3 (양호)
   - **주요 이슈:** 사실 정확성 부족
   - **거절 사유:** 
     - "부정확한 수치" × 3
     - "뒷받침 부족" × 2
   
2. **Technical Details**
   - 총 피드백: __개
   - 승인률: __%
   - 평균 점수:
     * 할루시네이션: 4.0
     * 설득력: 3.5 (낮음 ⚠️)
     * 완성도: 3.2 (낮음 ⚠️)
     * 명확성: 3.7
   - **주요 이슈:** 기술 깊이 부족, 복잡성 전달 미흡
   - **거절 사유:**
     - "너무 단순함" × 4
     - "중요 세부사항 누락" × 2

3. **Team Section**
   - 총 피드백: __개
   - 승인률: __%
   - 평균 점수: 양호 (4.1 이상)
   - **주요 이슈:** 없음 (진행 중)

4. **Strategy Section**
   - (필요한 경우)

**각 섹션당 Q&A:** (1분)

---

### 4단계: 가중치 조정 권장사항 (14:25 ~ 14:35, 10분)

**발표자:** AI Engineering + FeedbackAnalyzer 결과

**권장 조정 사항:**

#### Executive Summary (사실 정확성 개선 필요)
| 가중치 | 현재 | 권장 | 변경 | 이유 |
|--------|------|------|------|------|
| **할루시네이션** | 0.40 | **0.50** | ⬆️ | 평가점수 3.2 → 엄격한 필터 필요 |
| **설득력** | 0.30 | 0.30 | — | 평가점수 4.1 양호 |
| **완성도** | 0.20 | 0.15 | — | 상대적으로 낮은 우선순위 |
| **명확성** | 0.10 | 0.05 | — | 조정 |

**기대 효과:** F1-Score 개선 예상 ±2%

#### Technical Details (깊이 강화)
| 가중치 | 현재 | 권장 | 변경 | 이유 |
|--------|------|------|------|------|
| **할루시네이션** | 0.40 | 0.40 | — | 정확성 양호 |
| **설득력** | 0.30 | **0.40** | ⬆️ | 평가점수 3.5 → 주장력 강화 필요 |
| **완성도** | 0.20 | **0.15** | ↓ | 평가점수 3.2 낮음, 재설계 검토 |
| **명확성** | 0.10 | 0.05 | — | 조정 |

**기대 효과:** F1-Score 개선 예상 ±3%

#### Team Section
- **권장:** 현재 가중치 유지 (승인률 85% 이상 양호)

**결정:**
- [ ] 권장 가중치 승인
- [ ] 추가 검토 필요 (_____)
- [ ] 추가 데이터 수집 필요

---

### 5단계: 테스트 & 배포 계획 (14:35 ~ 14:40, 5분)

**발표자:** QA Lead

**테스트 계획:**
1. **새 가중치로 샘플 10개 섹션 재평가**
   - 대상: 이번 주 거절된 상위 10개 섹션
   - 예상 결과: 개선율 ≥50%
   - 테스트 기간: 2026-04-26 ~ 2026-04-27 (주말)

2. **검증 기준:**
   - [ ] F1-Score 변화 추적 (개선/악화)
   - [ ] False Negative Rate 변화 확인
   - [ ] 기존 승인된 섹션 재평가 (회귀 테스트)
   - [ ] 성능 메트릭 변화 없음

**배포 타이밍:**
- 결정 기한: 2026-04-28 (월요일)
- 배포 예정: 2026-04-28 또는 2026-04-29

**롤백 계획:**
- 이전 가중치 버전 준비 완료
- 롤백 실행 조건: F1-Score 0.96 미만

---

### 6단계: 다음 주 계획 & 마무리 (14:40 ~ 14:45, 5분)

**발표자:** PM Lead

**다음 주 예정:**
- [ ] 가중치 테스트 완료
- [ ] 테스트 결과 분석
- [ ] 배포 의사결정 회의 (2026-04-28)
- [ ] 피드백 수집 계속 (새 가중치 또는 기존)

**피드백:**
- 프로세스 개선 사항?
- 다음 주 집중할 영역?

**마무리:**
- 회의록 작성
- 결정사항 문서화
- Slack 채널에 공지

---

## 회의록 템플릿 (세션별)

```markdown
# 주간 피드백 리뷰 회의록

**날짜:** 2026-04-26 (금)  
**시간:** 14:00 ~ 14:45  
**참석:** [이름], [이름], [이름]

## 주간 피드백 요약
- 총 피드백: __개
- 승인률: __%
- 주요 섹션: ________

## 섹션별 분석 결과
### Executive Summary
- 현황: ________
- 주요 이슈: ________
- 권장: ________

### Technical Details
- 현황: ________
- 주요 이슈: ________
- 권장: ________

## 가중치 조정 결정
| 섹션 | 할루 | 설득 | 완성 | 명확 | 상태 |
|------|------|------|------|------|------|
| Exec | 0.50 | 0.30 | 0.15 | 0.05 | 승인 |
| Tech | 0.40 | 0.40 | 0.15 | 0.05 | 승인 |
| Team | - | - | - | - | 유지 |

## 테스트 계획
- 샘플 검증: 10개 섹션
- 기간: 2026-04-26 ~ 2026-04-27
- 배포 결정: 2026-04-28

## 액션 아이템
- [ ] 새 가중치로 샘플 테스트 (QA, 2026-04-27)
- [ ] 테스트 결과 분석 (AI Eng, 2026-04-27)
- [ ] 배포 의사결정 회의 (모두, 2026-04-28)

## 다음 회의
**날짜:** 2026-05-03 (금)  
**시간:** 14:00 KST
```

---

## 정기 세션 스케줄 (Go-Forward)

| 주차 | 날짜 | 주제 | 담당 |
|------|------|------|------|
| 1 | 2026-04-26 | Phase 1: 초기 피드백 분석 | PM |
| 2 | 2026-05-03 | Phase 2: 가중치 조정 효과 검증 | QA |
| 3 | 2026-05-10 | Phase 3: 2주차 누적 분석 | AI Eng |
| 4+ | 매주 금 | 정기 리뷰 & 조정 | Rotating |

---

## 도구 & 자료

### 필요한 도구
- [ ] FeedbackAnalyzer (Python 스크립트)
- [ ] Google Sheets (대시보드)
- [ ] 회의실 또는 Zoom 링크
- [ ] 데이터 추출 쿼리

### 공유 자료 위치
- Design: `docs/operations/feedback-review-guide.md`
- Tool: `app/services/feedback_analyzer.py`
- Reports: `/reports/feedback-analysis-*.json`

### 슬랙 채널
- `#step4a-feedback-review` (공지)
- `#step4a-qa` (관련 이슈)

---

**Document Version:** 1.0  
**Created:** 2026-04-19  
**First Session:** 2026-04-26  
**Review Cycle:** Weekly (Every Friday 14:00 KST)
