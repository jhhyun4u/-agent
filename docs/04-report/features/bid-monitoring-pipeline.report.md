# bid-monitoring-pipeline — PDCA 완료 보고서

| 항목 | 내용 |
|------|------|
| 피처명 | 공고 모니터링 백그라운드 파이프라인 |
| PDCA 완료일 | 2026-03-25 |
| Match Rate | **97%** (BUG-1 수정 후) |
| 신규 파일 | 2개 |
| 수정 파일 | 3개 |
| 총 코드량 | ~450줄 (Python 350 + TypeScript 100) |

---

## 1. 요약

공고 모니터링 시스템의 **클릭 시 실시간 처리(30초+)** 병목을 해결하기 위해, scored/crawl 결과를 **백그라운드에서 사전 처리**하는 파이프라인을 구축했다.

### Before → After

| 지표 | Before | After |
|------|--------|-------|
| 제안 검토 로딩 | 30초+ (실시간 Claude 2회) | < 2초 (캐시 히트) |
| 분석 실패율 | ~60% (Supabase cold start) | < 5% (백그라운드 재시도) |
| scored 공고 DB 커버리지 | 수동 4건 | 자동 상위 50건 |
| 첨부파일 | 매번 G2B 재다운로드 | 로컬 캐시 영구 보관 |

---

## 2. 구현 내역

### 신규 파일

| 파일 | 줄수 | 역할 |
|------|:----:|------|
| `app/services/bid_pipeline.py` | ~250 | 4-Step 파이프라인 오케스트레이터 |
| `app/services/bid_attachment_store.py` | ~95 | G2B 첨부파일 다운로드 + 로컬 캐시 + 텍스트 추출 |

### 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/api/routes_bids.py` | `POST /bids/crawl` 파이프라인 자동 트리거 + `GET /bids/pipeline/status` + `POST /bids/pipeline/trigger` |
| `app/services/scheduled_monitor.py` | score >= 100 공고 파이프라인 자동 트리거 |
| `frontend/.../review/page.tsx` | 파이프라인 진행 중 5초 폴링 + 완료 시 자동 표시 |

---

## 3. 파이프라인 흐름

```
Trigger (crawl/monitor/manual)
  │
  ▼
Step 1: ensure_bid_in_db()
  │ DB 존재 확인 → 없으면 G2B API 조회 → upsert
  ▼
Step 2: download_and_extract()
  │ raw_data에서 첨부파일 URL 추출
  │ → 우선순위: 제안요청서 > 과업지시서 > 공고문 (최대 3파일)
  │ → 로컬 캐시: data/bid_attachments/{bid_no}/
  │ → 텍스트 추출 → content_text DB 저장
  ▼
Step 3: run_analysis_if_needed()
  │ data/bid_analyses/{bid_no}.json 캐시 확인
  │ → 없으면 Claude Stage 1 (전처리) + Stage 2 (적합성)
  │ → 결과 파일 캐시 저장
  ▼
Done → 사용자 클릭 시 즉시 표시
```

### 트리거 시점

| 트리거 | 대상 | 조건 |
|--------|------|------|
| `POST /bids/crawl` (수동 새로고침) | 상위 50건 | score >= 80 |
| `scheduled_monitor` (08:00/15:00) | 당일 공고 | score >= 100 |
| `POST /bids/pipeline/trigger` (수동) | content_text null 공고 | 최대 20건 |

---

## 4. 갭 분석 결과

| 항목 | 건수 | 조치 |
|------|:----:|------|
| HIGH (BUG) | 1 | `scheduled_monitor.py` dict→dataclass 접근 수정 **완료** |
| MEDIUM (ADD) | 1 | `/bids/pipeline/trigger` 엔드포인트 — 설계 보완 가능 |
| LOW | 7 | 의도적 변경/코드 품질 개선 — 조치 불필요 |

---

## 5. 기술 결정

| 결정 | 근거 |
|------|------|
| 로컬 파일 캐시 (Supabase Storage 대신) | Supabase 불안정 → 로컬이 더 신뢰성 높음 |
| Semaphore(5) 동시성 제한 | G2B rate limit + Claude API 보호 |
| score >= 80/100 임계값 | Claude API 비용 관리 (100회/일 이내) |
| 인메모리 파이프라인 상태 | 30분 TTL, 서버 재시작 시 초기화 (충분) |

---

## 6. 잔여 작업 / 향후 개선

| 항목 | 우선순위 | 설명 |
|------|:--------:|------|
| Supabase Storage 연동 | L | 로컬 캐시 → 클라우드 이관 (다중 서버 배포 시) |
| 90일 자동 삭제 | L | `data/bid_attachments/` 오래된 파일 정리 |
| 파이프라인 대시보드 UI | M | 관리자용 진행 현황 페이지 |
| 에러 재시도 큐 | L | 실패 건 자동 재시도 (현재는 다음 트리거 시 재시도) |

---

## 7. PDCA 사이클 요약

```
[Plan] ✅ → [Design] ✅ → [Do] ✅ → [Check] ✅ (97%) → [Report] ✅
```

| Phase | 산출물 |
|-------|--------|
| Plan | `docs/01-plan/features/bid-monitoring-pipeline.plan.md` |
| Design | `docs/02-design/features/bid-monitoring-pipeline.design.md` |
| Analysis | `docs/03-analysis/features/bid-monitoring-pipeline.analysis.md` |
| Report | `docs/04-report/features/bid-monitoring-pipeline.report.md` |
