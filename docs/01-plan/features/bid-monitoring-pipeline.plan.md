# 공고 모니터링 백그라운드 파이프라인

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-03-25 |
| 상태 | 초안 |
| 선행 | Phase 0~6 완료, 공고 모니터링 UI 구현 완료 |

---

## 1. 목적

현재 공고 모니터링 시스템은 **공고 목록 수집(scored/monitor)**까지는 자동화되어 있으나, 개별 공고의 **첨부파일 다운로드 → 텍스트 추출 → AI 분석**이 **클릭 시 실시간 수행**되어 30초+ 소요되거나 Supabase 불안정 시 완전히 실패한다.

### 핵심 가치
- **즉시 열람**: 제안 검토 클릭 시 RFP 주요내용 + 적합성 분석이 **이미 준비**되어 있음
- **안정성**: Supabase/Claude API 장애 시에도 캐시된 분석 결과 표시 가능
- **업무 효율**: 스크리닝 담당자가 판단에 집중 (대기 시간 제거)

---

## 2. 현재 상태 (AS-IS)

```
[G2B API] ──→ [scored/monitor 목록] ──→ [화면 표시]
                                              │
                                         사용자 클릭
                                              │
                                              ▼
                                    [실시간] GET /bids/{id}
                                        │ DB 조회 (불안정)
                                        │ G2B fallback
                                        ▼
                                    [실시간] GET /bids/{id}/analysis
                                        │ DB 조회 → 첨부파일 다운로드
                                        │ → 텍스트 추출 → Claude x2
                                        │ → 캐시 저장
                                        ▼
                                    [30초+ 후] 화면 표시
```

### 문제점

| # | 문제 | 영향 |
|---|------|------|
| 1 | scored 공고가 DB에 저장 안 됨 | `/bids/{id}` API 500 에러 |
| 2 | 첨부파일이 영구 저장 안 됨 | 매번 G2B에서 재다운로드 (30초+) |
| 3 | AI 분석이 클릭 시 실시간 | 사용자 대기 30초, 타임아웃 빈번 |
| 4 | Supabase cold start | DB 쿼리 10~20초, 간헐적 실패 |

---

## 3. 목표 상태 (TO-BE)

```
[G2B API] ──→ [scored/monitor 목록]
                     │
                     ▼ (백그라운드)
              ┌──────────────────────────────┐
              │  Pipeline Worker              │
              │                              │
              │  Step 1: DB 저장              │
              │    scored 상위 N건 → bid_announcements │
              │                              │
              │  Step 2: 첨부파일 다운로드      │
              │    과업지시서, 제안요청서 등     │
              │    → Supabase Storage 저장     │
              │    → content_text 추출/저장     │
              │                              │
              │  Step 3: AI 분석              │
              │    Stage 1: 전처리 (Claude)    │
              │    Stage 2: 적합성 (Claude)    │
              │    → 파일 캐시 저장            │
              └──────────────────────────────┘
                     │
                     ▼
              사용자 클릭 → 즉시 표시 (캐시 히트)
```

---

## 4. 범위 (Scope)

### In-Scope

| # | 기능 | 설명 | 우선순위 |
|---|------|------|:--------:|
| P-1 | scored 결과 DB 자동 저장 | 상위 50건 → bid_announcements upsert | H |
| P-2 | 첨부파일 자동 다운로드 | 과업지시서/제안요청서 우선 → Storage 저장 | H |
| P-3 | content_text 자동 추출 | PDF/HWP/HWPX → 텍스트 파싱 → DB 저장 | H |
| P-4 | AI 분석 백그라운드 실행 | 전처리 + 적합성 → 파일 캐시 저장 | H |
| P-5 | 파이프라인 트리거 | scored API 호출 후 자동 / 수동 트리거 | M |
| P-6 | 진행 상태 표시 | 프론트엔드에서 분석 진행률 표시 | M |
| P-7 | 에러 재시도 | 실패 건 자동 재시도 (최대 3회) | L |

### Out-of-Scope

| 항목 | 사유 |
|------|------|
| 공고 자동 분류/태깅 | 별도 피처로 분리 |
| 첨부파일 전체 보관 (영구) | Storage 비용 관리 별도 검토 |
| scored 알고리즘 개선 | 별도 피처 |

---

## 5. 기술 설계 방향

### 5-1. 트리거 시점

| 트리거 | 설명 |
|--------|------|
| **scored API 호출 후** | `/bids/scored` 응답 반환 후 백그라운드 태스크 시작 |
| **스케줄 모니터링 후** | `scheduled_monitor.py` 08:00/15:00 실행 후 |
| **수동** | 관리자가 `/api/bids/pipeline/trigger` 호출 |

### 5-2. 파이프라인 Worker

```python
async def run_bid_pipeline(bid_nos: list[str]):
    """백그라운드 파이프라인 — scored/monitor 결과 후처리"""
    for bid_no in bid_nos:
        try:
            # Step 1: DB 확인/저장 (G2B fallback)
            await ensure_bid_in_db(bid_no)

            # Step 2: 첨부파일 다운로드 + 텍스트 추출
            await download_and_extract_attachments(bid_no)

            # Step 3: AI 분석 (캐시 없는 경우만)
            await run_analysis_if_needed(bid_no)

        except Exception as e:
            logger.warning(f"[{bid_no}] 파이프라인 실패: {e}")
            await record_pipeline_error(bid_no, str(e))
```

### 5-3. 첨부파일 저장 전략

| 항목 | 방식 |
|------|------|
| 저장소 | Supabase Storage `bid-attachments` 버킷 |
| 경로 | `{bid_no}/{파일명}` |
| 우선순위 | 제안요청서 > 과업지시서 > 공고문 (최대 3파일) |
| 텍스트 | 추출 후 `bid_announcements.content_text`에 저장 |
| 보존기간 | 90일 (마감일 기준 자동 삭제) |

### 5-4. 파일 구조

```
app/services/
  bid_pipeline.py          ← NEW: 파이프라인 오케스트레이터
  bid_attachment_store.py   ← NEW: 첨부파일 다운로드/저장
app/api/
  routes_bids.py           ← 수정: scored 후 파이프라인 트리거
```

---

## 6. 구현 순서

| 단계 | 작업 | 예상 파일 | 의존성 |
|------|------|----------|--------|
| 1 | `bid_pipeline.py` 스켈레톤 | 신규 | - |
| 2 | `ensure_bid_in_db()` — scored 결과 DB 저장 | bid_pipeline.py | G2BService |
| 3 | `bid_attachment_store.py` — 첨부파일 다운로드/Storage 저장 | 신규 | Supabase Storage |
| 4 | `download_and_extract_attachments()` — 텍스트 추출 → content_text | bid_pipeline.py | rfp_parser.py |
| 5 | `run_analysis_if_needed()` — AI 분석 + 캐시 | bid_pipeline.py | bid_preprocessor, bid_recommender |
| 6 | scored API 트리거 연동 | routes_bids.py 수정 | bid_pipeline.py |
| 7 | scheduled_monitor 트리거 연동 | scheduled_monitor.py 수정 | bid_pipeline.py |
| 8 | 프론트엔드 진행 상태 표시 | review/page.tsx 수정 | routes 수정 |

---

## 7. 성공 기준

| 지표 | 현재 | 목표 |
|------|------|------|
| 제안 검토 로딩 시간 | 30초+ (실시간 분석) | < 2초 (캐시 히트) |
| 분석 실패율 | ~60% (Supabase 불안정) | < 5% (백그라운드 재시도) |
| 첨부파일 접근 | G2B URL 직접 다운로드 | Storage 캐시 서빙 |
| scored 공고 DB 커버리지 | 4건 (수동) | 상위 50건 자동 |

---

## 8. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Claude API 비용 증가 | 상위 50건 x 2회 호출 = 100회/일 | scored 임계점(score >= 100) 이상만 분석 |
| Supabase Storage 용량 | HWP/PDF 파일 누적 | 90일 자동 삭제 정책 |
| G2B 첨부파일 다운로드 차단 | rate limit / IP 차단 | 0.5초 간격 + retry 3회 |
| 파이프라인 장시간 실행 | 50건 x 60초 = 50분 | 병렬 5건 동시 처리 → ~10분 |
