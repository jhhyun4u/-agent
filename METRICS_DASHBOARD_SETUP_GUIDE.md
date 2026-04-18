# 임시 메트릭 대시보드 설정 가이드

**목적:** Google Sheets를 이용한 STEP 4A 메트릭 모니터링  
**대상:** AI Engineering, Product, QA Teams  
**구성:** Metrics Dashboard + Latency Dashboard  
**업데이트:** 주간 (매주 금요일)

---

## 1단계: Google Sheets 생성 (1분)

### 새 시트 만들기
1. Google Sheets 이동: https://sheets.google.com
2. "새로운 스프레드시트" 클릭
3. 이름 지정: `STEP4A Metrics Dashboard - [Date]`
   - 예: `STEP4A Metrics Dashboard - 2026-04-26`

### 폴더 정리
- Google Drive에서 "tenopa-internal" 폴더 생성
- 그 아래 "Step4A" 폴더 생성
- 시트 파일을 "Step4A" 폴더에 저장
- 공유 설정: `view` 권한으로 AI Engineering + Product 팀과 공유

---

## 2단계: 데이터 다운로드 (2분)

### CSV 파일 다운로드

```bash
# 스크립트: 메트릭 CSV 다운로드
#!/bin/bash
TIMESTAMP=$(date +%Y-%m-%d-%H%M%S)

# Metrics CSV 다운로드
curl -s http://localhost:8000/api/metrics/export/metrics.csv \
  -o metrics_export_${TIMESTAMP}.csv

# Latency CSV 다운로드
curl -s http://localhost:8000/api/metrics/export/latency.csv \
  -o latency_export_${TIMESTAMP}.csv

echo "Downloaded at: ${TIMESTAMP}"
```

### API 엔드포인트

**Production URL:**
```
GET http://tenopa.co.kr/api/metrics/export/metrics.csv
GET http://tenopa.co.kr/api/metrics/export/latency.csv
GET http://tenopa.co.kr/api/metrics/export/info
```

**Staging URL:**
```
GET http://staging.tenopa.co.kr/api/metrics/export/metrics.csv
GET http://staging.tenopa.co.kr/api/metrics/export/latency.csv
```

**Local Development:**
```
GET http://localhost:8000/api/metrics/export/metrics.csv
GET http://localhost:8000/api/metrics/export/latency.csv
```

---

## 3단계: Google Sheets에 CSV 임포트 (5분)

### Tab 1: Metrics Data

1. Google Sheets 열기
2. "파일" → "가져오기" → "CSV 파일 업로드"
3. `metrics_export_[timestamp].csv` 선택
4. 임포트 옵션:
   - [ ] 새 스프레드시트 선택
   - [ ] 빈 셀 다루기: "선택 항목으로 대체" (기본값)
   - [ ] 변환: 기본값 유지

5. 임포트 완료 후:
   - Tab 이름을 "Metrics" 로 변경
   - 첫 행 고정 (행 1)

### Tab 2: Latency Data

1. 같은 시트에 새 탭 추가
2. Tab 이름: "Latency"
3. CSV 임포트:
   - "파일" → "가져오기" → "CSV 파일 업로드"
   - `latency_export_[timestamp].csv` 선택
   - 새 탭에 추가

4. 첫 행 고정

---

## 4단계: 피벗 테이블 생성 (10분)

### Pivot Table 1: 섹션별 신뢰도 분포

**소스:** Metrics 탭

**위치:** 새 탭 "Confidence Analysis"

**구성:**

1. "Metrics" 탭 선택
2. "데이터" → "피벗 테이블"
3. 새 탭에 생성

**피벗 테이블 설정:**

| 항목 | 설정 |
|------|------|
| **행** | Section ID |
| **열** | (없음) |
| **값** | Confidence (평균) |
| **필터** | Proposal ID (선택사항) |

**결과:** 각 섹션의 평균 신뢰도 → 낮은 신뢰도 섹션 식별

### Pivot Table 2: 앙상블 적용 통계

**소스:** Metrics 탭

**위치:** 새 탭 "Ensemble Analysis"

**구성:**

| 항목 | 설정 |
|------|------|
| **행** | Section ID |
| **열** | Ensemble Applied (TRUE/FALSE) |
| **값** | Score (개수) |

**결과:**
- 앙상블 적용된 섹션 vs 미적용 섹션 비교
- 적용 비율 계산

### Pivot Table 3: 레이턴시 분석

**소스:** Latency 탭

**위치:** 새 탭 "Latency Analysis"

**구성:**

| 항목 | 설정 |
|------|------|
| **행** | Section ID |
| **열** | (없음) |
| **값** | Total Section (ms) (평균, 최소, 최대, 표준편차) |
| **필터** | (필요시) |

**추가 계산:**
```
= PERCENTILE(Latency!H:H, 0.95)  // P95 계산
= PERCENTILE(Latency!H:H, 0.99)  // P99 계산
= COUNTIF(Latency!H:H, ">21000") // 21초 초과 건수
```

---

## 5단계: 차트 생성 (15분)

### Chart 1: 신뢰도 분포

**유형:** 막대 차트

**데이터:** Confidence Analysis 피벗 테이블

**축:**
- X축: Section ID
- Y축: 평균 신뢰도 (0.0 ~ 1.0)

**옵션:**
- [ ] 데이터 라벨 표시
- [ ] 목표선 추가 (0.75 = 신뢰도 기준)

**해석:**
- 0.75 이상: 높은 신뢰도 (녹색)
- 0.65 ~ 0.75: 중간 신뢰도 (노랑색)
- 0.65 미만: 낮은 신뢰도 (빨강색) → 개선 필요

### Chart 2: 레이턴시 추이

**유형:** 꺾은선 차트

**데이터:** Latency 탭

**축:**
- X축: Timestamp
- Y축: Total Section (ms)

**옵션:**
- [ ] 평균선 추가 (8-10초 범위)
- [ ] 목표선 추가 (21초 = 임계값)
- [ ] P95/P99 선 추가 (고급)

**해석:**
- 21초 이상: 경고 (SLA 위반)
- 21초 이하: 정상

### Chart 3: 앙상블 효과

**유형:** 원형 차트

**데이터:** Ensemble Analysis 피벗 테이블

**계산:**
```
앙상블 적용률 = 앙상블 사용 / 전체 × 100%
```

**옵션:**
- [ ] 퍼센트 표시
- [ ] 범례 표시

---

## 6단계: 대시보드 레이아웃 (5분)

### 전체 구조

```
┌─────────────────────────────────────────────────────┐
│   STEP4A METRICS DASHBOARD - 2026-04-26             │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📊 SUMMARY METRICS                                 │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │ Total        │ Avg Confidence │ P95 Latency │    │
│  │ Sections: 45 │ 0.82           │ 20.5s       │    │
│  └──────────────┴──────────────┴──────────────┘    │
│                                                      │
│  📈 TRENDS                                          │
│  ┌────────────────────────┐  ┌──────────────────┐  │
│  │ Latency Trend          │  │ Confidence Dist. │  │
│  │ [꺾은선 차트]           │  │ [막대 차트]       │  │
│  └────────────────────────┘  └──────────────────┘  │
│                                                      │
│  🎯 ANALYSIS                                        │
│  ┌────────────────────────┐  ┌──────────────────┐  │
│  │ Ensemble Application   │  │ P50/P95/P99      │  │
│  │ [원형 차트]             │  │ [통계 표]        │  │
│  └────────────────────────┘  └──────────────────┘  │
│                                                      │
│  📋 KEY METRICS                                     │
│  • Sections under 21s: 43/45 (95.6%) ✓             │
│  • Low confidence sections: 2 (4.4%) ⚠️            │
│  • Ensemble applied: 28/45 (62.2%)                 │
│  • Last updated: 2026-04-26 10:15 KST              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 추가 정보 섹션

하단에 추가 정보:

```
📌 NOTES
- P95 Latency: 20.5초 < 21초 (목표 달성) ✓
- 신뢰도 낮은 섹션: [exec_summary_005, tech_detail_012]
- 다음 리뷰: 2026-05-03
- 가중치 버전: v1.0 (2026-04-18 적용)

⚠️ ALERTS
- None currently

🔄 UPDATE SCHEDULE
- Daily: 자동 (API 기반)
- Weekly Review: 매주 금요일 14:00 KST
- Next Update: 2026-04-27 (Latency 재평가)
```

---

## 7단계: 정기 업데이트 자동화 (10분)

### Google Apps Script로 자동 갱신

```javascript
function updateMetricsDashboard() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const metricsSheet = spreadsheet.getSheetByName("Metrics");
  
  // CSV 다운로드 URL
  const metricsUrl = "http://tenopa.co.kr/api/metrics/export/metrics.csv";
  const latencyUrl = "http://tenopa.co.kr/api/metrics/export/latency.csv";
  
  // 기존 데이터 삭제 후 새 데이터 추가
  // (Google Sheets → CSV Import 자동화는 제한적)
  
  // 대안: 매주 수동 업데이트 알림 설정
  const emailAddress = "ai-team@tenopa.co.kr";
  const subject = "[STEP4A] Weekly Metrics Update Required";
  const message = `
    이번 주 메트릭 대시보드를 업데이트해주세요.
    
    1. 다음 링크에서 CSV 다운로드:
       - Metrics: http://tenopa.co.kr/api/metrics/export/metrics.csv
       - Latency: http://tenopa.co.kr/api/metrics/export/latency.csv
    
    2. Google Sheets에 임포트
    3. 피벗 테이블 새로 고침
    
    대시보드: https://docs.google.com/spreadsheets/d/[ID]/edit
  `;
  
  GmailApp.sendEmail(emailAddress, subject, message);
}

// 매주 금요일 14:30 실행
function createWeeklyTrigger() {
  ScriptApp.newTrigger("updateMetricsDashboard")
    .timeBased()
    .onWeeksDay(ScriptApp.WeekDay.FRIDAY)
    .atHour(14)
    .minute(30)
    .create();
}
```

### 대안: 수동 업데이트 프로세스

**주간 갱신 체크리스트 (매주 금요일 13:45):**

- [ ] Metrics CSV 다운로드
  ```bash
  curl http://tenopa.co.kr/api/metrics/export/metrics.csv -o metrics.csv
  ```

- [ ] Latency CSV 다운로드
  ```bash
  curl http://tenopa.co.kr/api/metrics/export/latency.csv -o latency.csv
  ```

- [ ] Google Sheets에서:
  - [ ] "Metrics" 탭의 기존 데이터 삭제
  - [ ] 새 metrics.csv 임포트
  - [ ] "Latency" 탭의 기존 데이터 삭제
  - [ ] 새 latency.csv 임포트
  - [ ] 피벗 테이블 새로 고침 (데이터 → 새로 고침)
  - [ ] 차트 업데이트 확인

- [ ] 요약 통계 업데이트:
  - [ ] 총 섹션 수
  - [ ] 평균 신뢰도
  - [ ] P95 레이턴시
  - [ ] 21초 초과 건수

**소요시간:** 약 5분

---

## 8단계: 공유 & 접근 제어 (3분)

### 공유 설정

1. Google Sheets "공유" 버튼 클릭
2. 사용자/그룹 추가:
   - [ ] AI Engineering Team (편집 권한)
   - [ ] Product Team (보기 권한)
   - [ ] QA Team (편집 권한)
   - [ ] CTO (보기 권한)

3. 댓글 권한 활성화 (피드백용)

### 접근 URL

```
Dashboard Link: https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit#gid=0
Shared Folder: https://drive.google.com/drive/folders/[FOLDER_ID]
```

---

## 정기 모니터링 프로세스

### 일일 확인 (선택)

**시간:** 매일 09:00 KST

**확인 항목:**
- P95 레이턴시 < 22초?
- 신뢰도 이상 섹션 없음?
- 에러 없음?

### 주간 리뷰

**시간:** 매주 금요일 14:00 KST (피드백 리뷰 세션)

**검토 내용:**
- 주간 추이 분석
- 가중치 조정 효과
- 다음 주 개선 계획

### 월간 분석

**시간:** 매달 마지막 주 금요일

**내용:**
- 월간 성능 보고서 생성
- 추세 분석 및 예측
- Phase 2 자동화 준비도 검토

---

## 문제 해결

### CSV 임포트 실패

**증상:** "데이터를 임포트할 수 없습니다" 오류

**해결:**
1. CSV 파일을 직접 열어 인코딩 확인 (UTF-8-sig)
2. 특수 문자 확인 (쉼표, 따옴표 등)
3. 파일 크기 확인 (<100MB)
4. 다시 다운로드 후 재시도

### 피벗 테이블 오류

**증상:** 피벗 테이블이 비어있거나 값이 0

**해결:**
1. "데이터" → "피벗 테이블" → "기존 피벗 테이블 수정"
2. 범위 확인 (A1:H100 등)
3. 열 이름 재확인
4. 필터 설정 확인

### 차트 표시 문제

**증상:** 차트가 비어있거나 오류 표시

**해결:**
1. 차트 편집 ("차트 옵션")
2. 데이터 범위 재설정
3. 축 라벨 확인
4. 범례 설정 확인

---

## 다음 단계: Phase 2 (2026-05)

프로덕션 대시보드 개발:
- React 기반 실시간 대시보드
- WebSocket 기반 실시간 메트릭
- 고급 필터링 및 드릴다운
- 자동 경고 알림

---

**Document Version:** 1.0  
**Created:** 2026-04-19  
**First Deployment:** 2026-04-26  
**Update Frequency:** Weekly (Friday 14:30 KST)
