# 예산 필터링 테스트 보고서

## 1. 단위 테스트 결과 ✓

### 테스트 파일
- `tests/test_budget_filtering.py`

### 테스트 항목

#### 1.1 BidFetcher 예산 필터링
```
✓ min_budget=0원: 3건 (모든 공고)
✓ min_budget=50,000,000원: 3건 (50M, 150M, 300M)
✓ min_budget=100,000,000원: 2건 (150M, 300M)
✓ min_budget=200,000,000원: 1건 (300M)
✓ min_budget=400,000,000원: 0건 (없음)
```

**로직 검증:**
- `BidFetcher.fetch_bids_scored()` (fetcher.py:140-141)
  ```python
  if bs.budget < min_budget:
      continue
  ```

#### 1.2 API 응답 필터링
```
✓ min_budget=0원: 3건 (모든 공고)
✓ min_budget=100,000,000원: 2건 필터
✓ min_budget=200,000,000원: 1건 필터
```

**로직 검증:**
- `get_scored_bids()` 엔드포인트 (routes_bids.py:511-512)
  ```python
  filtered_data = [bid for bid in payload.get("data", [])
                   if bid.get("budget", 0) >= min_budget]
  ```

#### 1.3 엔드포인트 파라미터 전달
```
✓ /bids/crawl에서 min_budget 파라미터 전달
✓ /bids/scored에서 min_budget 파라미터 수신
✓ 파라미터는 0 이상의 정수
```

---

## 2. 코드 변경 사항

### 2.1 routes_bids.py - GET /bids/scored

**Line 457:** min_budget 파라미터 추가
```python
min_budget: int = Query(0, ge=0, description="최소 예산 (원)"),
```

**Line 511-512:** 필터링 로직 추가
```python
# ✅ min_budget 필터링: 예산이 min_budget 이상인 공고만 반환
filtered_data = [bid for bid in payload.get("data", [])
               if bid.get("budget", 0) >= min_budget]
```

**Line 529:** 로깅 추가
```python
logger.info(f"min_budget={min_budget}원 필터링: {len(payload.get('data', []))}건 → {len(filtered_data)}건")
```

### 2.2 routes_bids.py - POST /bids/crawl

**Line 553:** min_budget 파라미터 추가
```python
min_budget: int = Query(0, ge=0, description="최소 예산 (원)"),
```

**Line 575:** 파라미터 전달
```python
results = await fetcher.fetch_bids_scored(
    ...
    min_budget=min_budget,
    ...
)
```

### 2.3 fetcher.py - fetch_bids_scored()

**Line 58:** 파라미터 이미 정의됨
```python
min_budget: int = 0,
```

**Line 140-141:** 필터링 로직 이미 구현됨
```python
if bs.budget < min_budget:
    continue
```

---

## 3. 통합 테스트 가이드

### 3.1 테스트 환경 준비

1. **서버 실행**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **데이터 수집** (선택사항)
   ```bash
   curl -X POST "http://localhost:8000/api/bids/crawl?days=1"
   ```

### 3.2 테스트 케이스

#### Test 1: 기본 조회 (모든 공고)
```bash
curl "http://localhost:8000/api/bids/scored"
```

**기대 결과:**
- 응답 상태: 200
- 데이터: 전체 공고

#### Test 2: 1억원 이상 필터링
```bash
curl "http://localhost:8000/api/bids/scored?min_budget=100000000"
```

**기대 결과:**
- 응답 상태: 200
- 데이터: 1억원 이상의 공고만
- 반환 건수 < Test 1의 반환 건수

#### Test 3: 2억원 이상 필터링
```bash
curl "http://localhost:8000/api/bids/scored?min_budget=200000000"
```

**기대 결과:**
- 응답 상태: 200
- 데이터: 2억원 이상의 공고만
- 반환 건수 < Test 2의 반환 건수

#### Test 4: 3억원 이상 필터링
```bash
curl "http://localhost:8000/api/bids/scored?min_budget=300000000"
```

**기대 결과:**
- 응답 상태: 200
- 데이터 감소 (있으면)

#### Test 5: 수동 크롤링 + 필터링
```bash
curl -X POST "http://localhost:8000/api/bids/crawl?min_budget=150000000"
```

**기대 결과:**
- 응답 상태: 200
- 캐시 저장됨
- GET /bids/scored에서 1억5천만원 이상만 반환

### 3.3 검증 항목

```
[VALIDATION] 예산 필터링
□ 1. min_budget=0: 최대 건수 반환
□ 2. min_budget 증가시 반환 건수 감소
□ 3. 모든 반환 공고: budget >= min_budget 만족
□ 4. 로그 메시지: "min_budget=XXX원 필터링: N건 → M건"
□ 5. 필터 값이 없는 경우 기본값 0 적용
□ 6. 음수 값 거부 (Query validation)
```

---

## 4. 실제 데이터 예시

### 필터링 전
```json
{
  "total_count": 3,
  "data": [
    {"bid_no": "001", "title": "공고1", "budget": 50000000},
    {"bid_no": "002", "title": "공고2", "budget": 150000000},
    {"bid_no": "003", "title": "공고3", "budget": 300000000}
  ]
}
```

### 필터링 후 (min_budget=100000000)
```json
{
  "total_count": 3,
  "data": [
    {"bid_no": "002", "title": "공고2", "budget": 150000000},
    {"bid_no": "003", "title": "공고3", "budget": 300000000}
  ]
}
```

**로그 출력:**
```
min_budget=100000000원 필터링: 3건 → 2건
```

---

## 5. 백그라운드 분석 연동

### Line 514-525: 분석 자동 트리거

```python
# ✅ 분석이 없는 공고들의 백그라운드 분석 큐 추가
# analysis_status가 pending 또는 suitability_score가 없는 공고만 분석 시작
try:
    for bid in filtered_data:  # <- 필터링된 데이터에서만 실행
        bid_no = bid.get("bid_no")
        has_score = bid.get("suitability_score") is not None
        # 분석 점수가 없으면 백그라운드 분석 트리거
        if bid_no and not has_score:
            await _queue_bid_analysis(bid_no, background_tasks)
            logger.info(f"[scored] {bid_no} 백그라운드 분석 큐 추가")
except Exception as e:
    logger.warning(f"[scored] 분석 큐 추가 중 오류: {e}")
```

**효과:**
- 필터링된 공고들만 자동 분석
- 적합도 점수 실시간 업데이트
- 공고 모니터링과 제안 검토 점수 일치

---

## 6. 로그 분석

### 성공 시 로그 예시

```
2026-04-13 14:00:00 INFO min_budget=100000000원 필터링: 120건 → 85건
2026-04-13 14:00:01 INFO [scored] 001 백그라운드 분석 큐 추가
2026-04-13 14:00:01 INFO [scored] 002 백그라운드 분석 큐 추가
```

### 문제 시 로그 예시

```
2026-04-13 14:00:00 WARNING [scored] 분석 큐 추가 중 오류: ...
```

---

## 7. 확인 목록

```
✓ 단위 테스트 (test_budget_filtering.py)
  ✓ BidFetcher 필터링 로직
  ✓ API 응답 필터링 로직
  ✓ 엔드포인트 파라미터 전달

□ 통합 테스트 (실제 API)
  □ /api/bids/scored 엔드포인트
    □ min_budget=0 (기본)
    □ min_budget=100000000
    □ min_budget=200000000
  □ /api/bids/crawl 엔드포인트
    □ min_budget 파라미터 전달
    □ 캐시 필터링 적용
  □ 로그 메시지 확인
  □ 배경 분석 자동 트리거

□ 성능 테스트
  □ 대량 데이터 필터링 (1000+건)
  □ 응답 시간 측정
```

---

## 8. 참고: 지난 세션 수정 사항

### 문제 1: 제안 프로젝트 목록 표시 안 됨
- **원인:** frontend 필터링에서 `bid_tracked: false` 제외
- **해결:** `frontend/app/(app)/proposals/page.tsx` 라인 826 필터 제거

### 문제 2: 가용도 점수 불일치
- **원인:** `/bids/scored` 엔드포인트가 백그라운드 분석 트리거 안 함
- **해결:** routes_bids.py에 분석 큐 로직 추가

### 문제 3: 예산 필터링 작동 안 함
- **원인:** `/bids/crawl`에서 `min_budget` 하드코딩
- **해결:** `min_budget` 파라미터 추가 및 전달

---

**테스트 완료 일시:** 2026-04-13
**상태:** 모든 단위 테스트 ✓ | 통합 테스트 대기 (서버 실행 필요)
