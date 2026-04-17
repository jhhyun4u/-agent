# Phase 1 성능 기준선 (Baseline) 보고서

**측정 일시:** 2026-04-17  
**측정 기간:** Day 1-2 (2026-04-17 ~ 2026-04-18)  
**상태:** 📊 **기준선 수집 중** (현재 진행 중)

---

## 📊 측정 개요

### 측정 대상 (Hot Paths)
- **API 응답시간:** 10개 주요 경로
- **메모리 사용량:** 실시간 추적 (X-Memory-* 헤더)
- **데이터베이스 성능:** 슬로우 쿼리 로깅
- **캐시 성능:** 현재 캐시 히트율 측정

### 측정 방법
```bash
# 실행 명령어
bash scripts/measure_performance.sh http://localhost:8000

# 또는 프로덕션 서버 대상
bash scripts/measure_performance.sh https://api.tenopa.co.kr
```

### 반복 횟수
- **API 응답시간:** 각 경로당 100회 반복 측정
- **메모리:** 매 요청마다 자동 기록
- **목표 시간:** 약 30분 (네트워크 포함)

---

## 📈 현재 상태 (측정 진행 중)

### 1. API 응답시간 (P95)

| 경로 | 설명 | Min | Avg | Max | P95 | 목표 | 상태 |
|------|------|-----|-----|-----|-----|------|------|
| `/api/proposals` | 제안 목록 | TBD | TBD | TBD | TBD | <3s | 📊 |
| `/api/proposals/count` | 제안 개수 | TBD | TBD | TBD | TBD | <1s | 📊 |
| `/api/workflow/proposals` | 워크플로우 목록 | TBD | TBD | TBD | TBD | <3s | 📊 |
| `/api/vault/search?q=test` | Vault 검색 | TBD | TBD | TBD | TBD | <2s | 📊 |
| `/api/kb/search?q=IoT` | KB 검색 | TBD | TBD | TBD | TBD | <2s | 📊 |
| `/api/analytics` | 분석 데이터 | TBD | TBD | TBD | TBD | <3s | 📊 |
| `/api/performance/trends` | 성능 추이 | TBD | TBD | TBD | TBD | <2s | 📊 |
| `/api/users/me` | 현재 사용자 | TBD | TBD | TBD | TBD | <1s | 📊 |
| `/api/teams` | 팀 목록 | TBD | TBD | TBD | TBD | <1s | 📊 |

**요약:**
- **평균 응답시간:** TBD 초
- **최대 응답시간:** TBD 초
- **P95 응답시간:** TBD 초 (목표: <3s)
- **성공률:** TBD%

### 2. 메모리 사용량

| 메트릭 | 현재 | 목표 | 상태 |
|--------|------|------|------|
| **현재 메모리** | TBD MB | <500MB | 📊 |
| **피크 메모리** | TBD MB | <800MB | 📊 |
| **평균 요청당 증가** | TBD MB | <10MB | 📊 |
| **메모리 누수 여부** | TBD | 없음 | 📊 |

**분석:**
```
메모리 증가 패턴:
- 요청 처리 후 메모리 해제: ✓ 확인 필요
- 메모리 누수 신호: ⚠️ 모니터링 중
- GC 효율성: TBD
```

### 3. 데이터베이스 성능 (슬로우 로그)

| 쿼리 | 평균 시간 | 최대 시간 | 호출 횟수 | 개선 기회 |
|------|---------|---------|---------|---------|
| `SELECT * FROM proposals` | TBD ms | TBD ms | TBD | JOIN 최적화 |
| 검색 쿼리 | TBD ms | TBD ms | TBD | 인덱스 추가 |
| 분석 쿼리 | TBD ms | TBD ms | TBD | 집계 최적화 |

**상위 5개 슬로우 쿼리:**
```
(측정 후 업데이트)
```

### 4. 캐시 성능 (현재)

| 항목 | 상태 | 히트율 | 개선 기회 |
|------|------|--------|---------|
| 검색 결과 캐시 | 없음 | 0% | 메모리 캐시 추가 |
| API 응답 캐시 | 없음 | 0% | 캐시 서비스 구현 |
| DB 쿼리 캐시 | 없음 | 0% | 쿼리 결과 캐싱 |

---

## 🔍 상세 분석 (측정 후 작성)

### 응답시간 분포

```
(측정 후 히스토그램 추가)

예상 분포:
- <500ms:  ░░░ 10%
- 500-1000ms: ░░░░░░ 30%
- 1-2s:  ░░░░░░░░░ 40%
- 2-3s:  ░░░░░ 15%
- >3s:   ░░ 5%
```

### 병목 지점 (Bottleneck Analysis)

```
(측정 후 분석)

1. 가장 느린 경로: ___________
2. 가장 많이 호출되는 경로: ___________
3. 메모리 가장 많이 사용: ___________
4. DB 쿼리 가장 느린 부분: ___________
```

---

## ✅ 체크리스트

### Day 1 (2026-04-17)

- [ ] API 응답시간 측정 (100회 반복)
  - [ ] `/api/proposals` 측정
  - [ ] `/api/workflow/proposals` 측정
  - [ ] `/api/vault/search` 측정
  - [ ] 기타 6개 경로 측정

- [ ] 메모리 모니터링 미들웨어 활성화
  - [ ] app/middleware/memory_monitor.py 등록
  - [ ] X-Memory-* 헤더 응답 확인

- [ ] DB 슬로우 로그 활성화
  - [ ] ALTER SYSTEM SET log_min_duration_statement = 1000
  - [ ] pg_reload_conf()
  - [ ] 느린 쿼리 로깅 확인

- [ ] 성능 메트릭 수집
  - [ ] Prometheus 메트릭 확인
  - [ ] 헬스체크 엔드포인트 동작 확인

### Day 2 (2026-04-18)

- [ ] 측정 데이터 수집 완료
  - [ ] PHASE1_PERFORMANCE_BASELINE.md 업데이트
  - [ ] P95 응답시간 계산
  - [ ] 메모리 통계 분석

- [ ] 병목 지점 식별
  - [ ] 느린 쿼리 상위 10개 추출
  - [ ] N+1 쿼리 패턴 확인
  - [ ] 메모리 누수 신호 검출

- [ ] 기준선 최종 승인
  - [ ] 데이터 검증 완료
  - [ ] 이상값(Outlier) 제거
  - [ ] Task #2 시작 준비

---

## 📊 수집 방법

### API 응답시간 (curl)

```bash
# 1회 테스트
curl -w "%{time_total}\n" -o /dev/null -s \
  http://localhost:8000/api/proposals?skip=0&limit=10

# 100회 반복 + 통계 계산
bash scripts/measure_performance.sh http://localhost:8000
```

### 메모리 사용량 (응답 헤더)

```bash
# 요청 후 헤더 확인
curl -i http://localhost:8000/api/proposals \
  | grep "X-Memory"

# 예상 출력:
# X-Memory-Before: 450.25MB
# X-Memory-After: 455.30MB
# X-Memory-Delta: +5.05MB
# X-Memory-Peak: 520.15MB
```

### 느린 쿼리 (PostgreSQL)

```sql
-- Supabase SQL Editor에서 실행
SELECT 
    query,
    mean_exec_time,
    max_exec_time,
    calls
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY total_exec_time DESC
LIMIT 10;
```

---

## 📈 기대 결과

### 최적화 전 (현재)

| 메트릭 | 예상 | 근거 |
|--------|------|------|
| P95 응답시간 | ~5s | 100+ SELECT, N+1 패턴 |
| 메모리 피크 | ~1000MB | 캐싱 없음 |
| 캐시 히트율 | 0% | 캐시 구현 전 |

### 최적화 후 (목표)

| 메트릭 | 목표 | 개선율 |
|--------|------|--------|
| P95 응답시간 | <3s | -40% (쿼리) + -60% (캐시) |
| 메모리 피크 | <800MB | -20% |
| 캐시 히트율 | >50% | 신규 구현 |

---

## 🚀 다음 단계

### Day 3-5: 데이터베이스 쿼리 최적화 (Task #2)
- JOIN 추가로 쿼리 수 감소
- 인덱스 생성
- N+1 쿼리 제거

### Day 5-6: 메모리 캐시 구현 (Task #3)
- CacheService 개발
- 검색 결과 캐싱
- 캐시 무효화 로직

### Day 7-10: 검증 & 최적화 완료 (Task #4)
- 최종 성능 측정
- 비교 보고서 작성
- 개발 가이드 문서화

---

## 📝 참고 자료

- **성능 측정 스크립트:** `scripts/measure_performance.sh`
- **메모리 모니터링:** `app/middleware/memory_monitor.py`
- **DB 슬로우 로그:** `database/migrations/037_enable_slowlog.sql`
- **최적화 계획:** `PHASE1_PERFORMANCE_OPTIMIZATION.md`

---

**최종 업데이트:** 2026-04-17  
**담당자:** Backend Performance Team  
**검토:** 2026-04-18 (기준선 수집 완료)  
**다음 검토:** 2026-04-24 (중간 점검)
